#!/usr/bin/env python3
"""
Coleta métricas reais de aceitação de mercado e saúde comunitária dos repositórios
para os 1.061 serviços do catálogo (estrelas, forks, último commit/push e trending).

Fontes utilizadas:
1. selfh.st metrics.json (1.444+ projetos pré-indexados)
2. ungh.cc (API pública de metadados GitHub sem rate-limit restrito)
3. APIs oficiais GitLab v4 e Codeberg/Gitea v1
4. Fallback via shields.io / GitHub HTML
"""

import json
import os
import re
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.environ.get("CATALOG_CACHE_DIR", "/tmp/catalog_cache")
CATALOG_PATH = os.path.join(ROOT_DIR, "catalogo-servicos.json")
METRICS_CACHE_PATH = os.path.join(CACHE_DIR, "selfhst_metrics.json")
SW_CACHE_PATH = os.path.join(CACHE_DIR, "selfhst_software.json")
OUTPUT_PATH = os.path.join(CACHE_DIR, "repo_metrics_resolved.json")


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def fetch_json(url: str, timeout: int = 12):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "OpenSourceCatalogMetrics/1.0 (+https://github.com)",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors="ignore"))


def fetch_text(url: str, timeout: int = 12) -> str:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def parse_shorthand_num(val: str) -> int:
    s = (val or "").strip().lower().replace(",", "")
    if not s:
        return 0
    mult = 1
    if s.endswith("k"):
        mult = 1000
        s = s[:-1]
    elif s.endswith("m"):
        mult = 1_000_000
        s = s[:-1]
    try:
        return int(float(s) * mult)
    except ValueError:
        return 0


def parse_repo_coords(git_url: str):
    if not git_url:
        return None
    u = git_url.strip().split("#")[0].split("?")[0].rstrip("/")
    if u.endswith(".git"):
        u = u[:-4]
    parsed = urllib.parse.urlparse(u)
    host = parsed.netloc.lower()
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) < 2:
        return None
    owner, repo = parts[0], parts[1]
    if "github.com" in host:
        return ("github", host, owner, repo)
    if "gitlab" in host:
        # GitLab suporta subgrupos no path completo antes de /-/
        if "-" in parts:
            parts = parts[: parts.index("-")]
        return ("gitlab", f"{parsed.scheme}://{host}", "/".join(parts), None)
    if any(h in host for h in ("codeberg.org", "projects.blender.org", "gitea.", "codefloe.com", "git.joinsharkey.org", "iceshrimp.dev")):
        return ("gitea", f"{parsed.scheme}://{host}", owner, repo)
    return None


def fetch_github_fallback(owner: str, repo: str):
    stars, forks, last_commit = None, 0, None
    try:
        s_json = fetch_json(f"https://img.shields.io/github/stars/{owner}/{repo}.json", timeout=10)
        if s_json and s_json.get("value"):
            stars = parse_shorthand_num(s_json["value"])
    except Exception:
        pass
    try:
        html = fetch_text(f"https://github.com/{owner}/{repo}", timeout=10)
        if stars is None:
            m = re.search(r'id="repo-stars-counter-star"[^>]*title="([0-9,]+)"', html)
            if m:
                stars = int(m.group(1).replace(",", ""))
        m_fork = re.search(r'id="repo-network-counter"[^>]*title="([0-9,]+)"', html)
        if m_fork:
            forks = int(m_fork.group(1).replace(",", ""))
        m_dt = re.search(r'<relative-time[^>]*datetime="([0-9T:\-]+Z)"', html)
        if m_dt:
            last_commit = m_dt.group(1)[:10]
    except Exception:
        pass
    if stars is not None:
        return {
            "stars": stars,
            "forks": forks,
            "last_commit": last_commit,
            "trending": 0,
            "archived": False,
            "source": "github_fallback",
        }
    return None


def fetch_remote_metrics(svc: dict):
    git_url = svc.get("git_url")
    coords = parse_repo_coords(git_url)
    if not coords:
        return None
    kind = coords[0]

    if kind == "github":
        _, _, owner, repo = coords
        try:
            data = fetch_json(f"https://ungh.cc/repos/{owner}/{repo}", timeout=12)
            r = data.get("repo") or {}
            if r and "stars" in r:
                pushed = (r.get("pushedAt") or r.get("updatedAt") or "")[:10]
                return {
                    "stars": int(r.get("stars") or 0),
                    "forks": int(r.get("forks") or 0),
                    "last_commit": pushed or None,
                    "trending": 0,
                    "archived": False,
                    "source": "ungh",
                }
        except Exception:
            pass
        return fetch_github_fallback(owner, repo)

    if kind == "gitlab":
        _, base_url, project_path, _ = coords
        encoded = urllib.parse.quote(project_path, safe="")
        try:
            data = fetch_json(f"{base_url}/api/v4/projects/{encoded}", timeout=12)
            if "star_count" in data:
                last_act = (data.get("last_activity_at") or "")[:10]
                return {
                    "stars": int(data.get("star_count") or 0),
                    "forks": int(data.get("forks_count") or 0),
                    "last_commit": last_act or None,
                    "trending": 0,
                    "archived": bool(data.get("archived", False)),
                    "source": "gitlab_api",
                }
        except Exception:
            pass

    if kind == "gitea":
        _, base_url, owner, repo = coords
        try:
            data = fetch_json(f"{base_url}/api/v1/repos/{owner}/{repo}", timeout=12)
            if "stars_count" in data:
                upd = (data.get("updated_at") or "")[:10]
                return {
                    "stars": int(data.get("stars_count") or 0),
                    "forks": int(data.get("forks_count") or 0),
                    "last_commit": upd or None,
                    "trending": 0,
                    "archived": bool(data.get("archived", False)),
                    "source": "gitea_api",
                }
        except Exception:
            pass

    return None


def main():
    os.makedirs(CACHE_DIR, exist_ok=True)
    if not os.path.exists(METRICS_CACHE_PATH):
        print("Baixando selfh.st metrics.json...")
        data = fetch_json("https://r2.selfh.st/directory/metrics.json", timeout=20)
        with open(METRICS_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f)
    else:
        with open(METRICS_CACHE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

    if not os.path.exists(SW_CACHE_PATH):
        print("Baixando selfh.st software.json...")
        sw = fetch_json("https://r2.selfh.st/directory/software.json", timeout=20)
        with open(SW_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(sw, f)
    else:
        with open(SW_CACHE_PATH, "r", encoding="utf-8") as f:
            sw = json.load(f)

    # Indexar selfh.st por repositório normalizado e por nome
    m_by_id = {x["id"]: x for x in data.get("apps", [])}
    selfhst_by_repo = {}
    selfhst_by_name = {}
    for e in sw.get("entries", []):
        mid = e.get("id")
        if mid not in m_by_id:
            continue
        m = m_by_id[mid]
        rec = {
            "stars": int(m.get("stars") or 0),
            "forks": int(m.get("forks") or 0),
            "last_commit": m.get("commit") or None,
            "trending": int(m.get("trending") or 0),
            "archived": False,
            "source": "selfhst",
        }
        repo_u = (e.get("repository") or "").lower().split("#")[0].rstrip("/")
        if repo_u:
            selfhst_by_repo[repo_u] = rec
        if e.get("name"):
            selfhst_by_name[norm(e["name"])] = rec
        if e.get("reference"):
            selfhst_by_name[norm(e["reference"])] = rec

    # Carregar cache prévio se existir para evitar rechamadas desnecessárias
    resolved = {}
    if os.path.exists(OUTPUT_PATH):
        with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
            resolved = json.load(f)

    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    svcs = [s for c in catalog["categories"] for s in c["services"]]
    pending = []
    for s in svcs:
        name = s["name"]
        git_norm = (s.get("git_url") or "").lower().split("#")[0].rstrip("/")
        if git_norm in selfhst_by_repo:
            resolved[name] = selfhst_by_repo[git_norm]
        elif norm(name) in selfhst_by_name:
            resolved[name] = selfhst_by_name[norm(name)]
        elif name in resolved and resolved[name].get("stars") is not None:
            continue
        elif s.get("git_url"):
            pending.append(s)

    print(f"Já resolvidos via selfh.st/cache: {len(resolved)} | Pendentes para consulta remota: {len(pending)}")

    if pending:
        start = time.time()
        done_cnt = 0
        ok_cnt = 0
        with ThreadPoolExecutor(max_workers=20) as ex:
            fut_map = {ex.submit(fetch_remote_metrics, s): s for s in pending}
            for fut in as_completed(fut_map):
                s = fut_map[fut]
                done_cnt += 1
                try:
                    res = fut.result()
                    if res is not None:
                        resolved[s["name"]] = res
                        ok_cnt += 1
                except Exception:
                    pass
                if done_cnt % 100 == 0 or done_cnt == len(pending):
                    print(f"  Progresso: {done_cnt}/{len(pending)} ({ok_cnt} obtidos em {time.time()-start:.1f}s)")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(resolved, f, ensure_ascii=False, indent=2)

    missing = [s["name"] for s in svcs if s["name"] not in resolved]
    print(f"\nTotal resolvido: {len(resolved)} / {len(svcs)} | Sem métricas Git: {len(missing)}")
    if missing:
        print("Amostra sem métricas Git:", missing[:30])


if __name__ == "__main__":
    main()
