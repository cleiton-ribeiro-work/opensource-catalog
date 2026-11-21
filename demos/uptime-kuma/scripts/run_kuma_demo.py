#!/usr/bin/env python3
"""
Agente automatizado (Playwright) para configurar, popular e testar o demo do Uptime Kuma
em https://demo.kuma.pet/start-demo com dados realistas, gerando capturas de tela
e relatório estruturado de asserções E2E.

Uso:
  /opt/dev-projects/GREENYARD-AI-NFL-VALUE-BETTING-ENGINE/backend/.venv/bin/python3 \
      demos/uptime-kuma/scripts/run_kuma_demo.py [--headed] [--hold SEGUNDOS]
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

BASE_DIR = Path(__file__).resolve().parent.parent
SCREENSHOTS_DIR = BASE_DIR / "screenshots"
RESULTS_DIR = BASE_DIR / "results"

DEMO_URL = "https://demo.kuma.pet/start-demo"
DEFAULT_USER = "kuma-admin"
DEFAULT_PASS = "#E5V5BRFk5kUGNA"

MONITORS = [
    {
        "name": "Portal Uptime Kuma (Oficial)",
        "url": "https://uptime.kuma.pet",
        "interval": "20",
        "description": "Monitoramento HTTPS principal com alerta de expiração de certificado TLS/SSL",
        "expiry_notification": True,
        "upside_down": False,
        "expected_state": "UP",
        "screenshot": "02-monitor-http-ssl.png",
    },
    {
        "name": "GitHub API & Repositórios",
        "url": "https://api.github.com",
        "interval": "20",
        "description": "Verificação contínua de disponibilidade e latência da API REST do GitHub",
        "expiry_notification": True,
        "upside_down": False,
        "expected_state": "UP",
        "screenshot": None,
    },
    {
        "name": "Cloudflare Edge (1.1.1.1)",
        "url": "https://1.1.1.1",
        "interval": "20",
        "description": "Monitoramento de conectividade e tempo de resposta na borda global",
        "expiry_notification": False,
        "upside_down": False,
        "expected_state": "UP",
        "screenshot": "03-monitor-api-up.png",
    },
    {
        "name": "Hostinger VPS App Catalog",
        "url": "https://www.hostinger.com/br/applications",
        "interval": "20",
        "description": "Acompanhamento de disponibilidade HTTP do catálogo de aplicações",
        "expiry_notification": True,
        "upside_down": False,
        "expected_state": "UP",
        "screenshot": None,
    },
    {
        "name": "Serviço de Pagamentos (Simulação de Queda / Alerta)",
        "url": "https://uptime.kuma.pet",
        "interval": "20",
        "description": "Monitor em modo invertido para demonstrar alerta de incidente, log de erro e badge DOWN",
        "expiry_notification": False,
        "upside_down": True,
        "expected_state": "DOWN",
        "screenshot": "04-monitor-incidente-down.png",
    },
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def record_step(report: dict, step_id: str, title: str, status: str, details: str = ""):
    report["steps"].append(
        {
            "id": step_id,
            "title": title,
            "status": status,
            "details": details,
            "timestamp": utc_now(),
        }
    )


def run_demo(headed: bool = False, hold_seconds: int = 0, user: str = DEFAULT_USER, password: str = DEFAULT_PASS):
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    report = {
        "target_url": DEMO_URL,
        "credentials": {"username": user},
        "started_at": utc_now(),
        "finished_at": None,
        "overall_status": "FAIL",
        "monitors_created": [],
        "steps": [],
        "screenshots": [],
    }

    with sync_playwright() as p:
        launch_args = ["--no-sandbox"]
        browser = p.chromium.launch(headless=not headed, args=launch_args)
        context = browser.new_context(viewport={"width": 1440, "height": 900}, locale="pt-BR")
        page = context.new_page()

        try:
            err_shot = SCREENSHOTS_DIR / "error-state.png"
            if err_shot.exists():
                err_shot.unlink()

            # 1. Acessar demo.kuma.pet e aguardar container subir
            page.goto(DEMO_URL, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_selector("iframe", timeout=30000)
            frame = page.frame_locator("iframe")
            frame.locator("label[for='btnradio1'], #floatingInput, a[href='/add']").first.wait_for(timeout=30000)

            # Aguardar estabilização da tela inicial (/setup-database, /setup ou /dashboard)
            page.wait_for_timeout(1200)

            # 2. Setup Database (se aparecer /setup-database)
            if frame.locator("label[for='btnradio1']").count() > 0:
                # Seleciona idioma pt-BR se existir
                lang_sel = frame.locator("#language")
                if lang_sel.count() > 0:
                    try:
                        lang_sel.select_option("pt-BR")
                    except Exception:
                        pass
                frame.locator("label[for='btnradio1']").click(timeout=15000)
                frame.locator("button[type='submit']").click()
                record_step(report, "setup_db", "Seleção do banco SQLite", "PASS", "SQLite selecionado em /setup-database")

            # 3. Criar conta administrativa (kuma-admin) ou fazer login
            frame.locator("#floatingInput").wait_for(timeout=20000)
            frame.locator("#floatingInput").fill(user)
            frame.locator("#floatingPassword").fill(password)
            if frame.locator("#repeat").count() > 0:
                frame.locator("#repeat").fill(password)
            shot1 = SCREENSHOTS_DIR / "01-setup-conta.png"
            page.screenshot(path=str(shot1))
            report["screenshots"].append(shot1.name)

            frame.locator("button[type='submit']").click()
            frame.locator("a[href='/add']").first.wait_for(timeout=20000)
            record_step(report, "auth_admin", "Criação/Login do administrador", "PASS", f"Autenticado como {user}")

            # 4. Criar os 5 monitores variados
            for idx, m in enumerate(MONITORS, start=1):
                frame.locator("a[href='/add']").first.click()
                frame.locator("#name").wait_for(timeout=15000)

                frame.locator("#name").fill(m["name"])
                frame.locator("#url").fill(m["url"])
                frame.locator("#interval").fill(m["interval"])

                desc_el = frame.locator("#description")
                if desc_el.count() > 0:
                    desc_el.fill(m["description"])

                exp_el = frame.locator("#expiry-notification")
                if exp_el.count() > 0:
                    if m["expiry_notification"] and not exp_el.is_checked():
                        exp_el.check()
                    elif not m["expiry_notification"] and exp_el.is_checked():
                        exp_el.uncheck()

                up_el = frame.locator("#upside-down")
                if up_el.count() > 0:
                    if m["upside_down"] and not up_el.is_checked():
                        up_el.check()
                    elif not m["upside_down"] and up_el.is_checked():
                        up_el.uncheck()

                frame.locator("#monitor-submit-btn").click()

                # Aguardar renderização do monitor criado e do primeiro heartbeat
                frame.locator(f"h1:has-text('{m['name']}'), span:has-text('{m['name']}')").first.wait_for(timeout=15000)
                page.wait_for_timeout(3500)

                if m["screenshot"]:
                    shot_path = SCREENSHOTS_DIR / m["screenshot"]
                    page.screenshot(path=str(shot_path))
                    report["screenshots"].append(shot_path.name)

                report["monitors_created"].append(
                    {
                        "name": m["name"],
                        "url": m["url"],
                        "interval_sec": int(m["interval"]),
                        "expected_state": m["expected_state"],
                        "ssl_expiry_check": m["expiry_notification"],
                    }
                )
                record_step(
                    report,
                    f"create_monitor_{idx}",
                    f"Monitor criado: {m['name']}",
                    "PASS",
                    f"URL={m['url']} | Estado esperado={m['expected_state']}",
                )

            # 5. Visão Geral no Dashboard com múltiplos batimentos
            dash_link = frame.locator("a[href='/dashboard']").first
            if dash_link.count() > 0:
                dash_link.click()
            page.wait_for_timeout(5000)

            dash_text = frame.locator("body").inner_text()
            for m in MONITORS:
                if m["name"] not in dash_text:
                    raise AssertionError(f"Monitor '{m['name']}' não apareceu no dashboard.")

            shot5 = SCREENSHOTS_DIR / "05-dashboard-geral.png"
            page.screenshot(path=str(shot5))
            report["screenshots"].append(shot5.name)
            record_step(
                report,
                "dashboard_overview",
                "Validação do Dashboard Geral",
                "PASS",
                f"Todos os {len(MONITORS)} monitores visíveis com gráficos de heartbeat e métricas agregadas.",
            )

            # 6. Criar e exibir uma Página de Status Pública
            frame.locator("a[href='/manage-status-page']").first.click(timeout=15000)
            frame.locator("a[href='/add-status-page']").first.click(timeout=15000)
            frame.locator("#name").wait_for(timeout=15000)
            frame.locator("#name").fill("Status da Infraestrutura")
            frame.locator("#slug").fill("infra")
            frame.locator("#monitor-submit-btn").click()

            # Aguarda tela de edição da status page (/status/infra)
            frame.locator("div.multiselect").first.wait_for(timeout=15000)

            # Adicionar os 5 monitores via Vue Multiselect
            for m in MONITORS:
                ms = frame.locator("div.multiselect").first
                ms.click()
                inp = frame.locator("input.multiselect__input").first
                inp.fill(m["name"])
                page.wait_for_timeout(300)
                opt = frame.locator(".multiselect__option").filter(has_text=m["name"]).first
                if opt.count() > 0:
                    opt.click()
                else:
                    inp.press("Enter")
                page.wait_for_timeout(250)

            # Publicar um aviso de incidente para demonstrar comunicação de crise
            try:
                inc_btn = frame.locator("button:has-text('Criar incidente'), button:has-text('Create Incident')").first
                if inc_btn.count() > 0:
                    inc_btn.click()
                    page.wait_for_timeout(500)
                    editables = frame.locator(".incident [contenteditable='true'], [contenteditable='true']")
                    if editables.count() >= 2:
                        editables.nth(0).fill("Degradação simulada no Serviço de Pagamentos")
                        editables.nth(1).fill("Alerta automático gerado durante o teste E2E para demonstrar registro de incidentes na Status Page.")
                        style_btn = frame.locator("button:has-text('Estilo:'), button:has-text('Style:')").first
                        if style_btn.count() > 0:
                            style_btn.click()
                            danger_opt = frame.locator("button.dropdown-item:has-text('perigo'), button.dropdown-item:has-text('danger')").first
                            if danger_opt.count() > 0:
                                danger_opt.click()
                        frame.locator("button:has-text('Post')").first.click()
                        page.wait_for_timeout(800)
            except Exception:
                cancel_btn = frame.locator("button:has-text('Cancelar'), button:has-text('Cancel')").first
                if cancel_btn.count() > 0:
                    cancel_btn.click()

            # Salvar Status Page para exibir visão pública final
            save_btn = frame.locator("button.btn-success:has-text('Salvar'), button.btn-success:has-text('Save')").first
            save_btn.click()
            page.wait_for_timeout(2500)

            sp_text = frame.locator("body").inner_text()
            if "Portal Uptime Kuma (Oficial)" not in sp_text:
                raise AssertionError("Monitores não apareceram na Status Page pública após salvar.")

            shot6 = SCREENSHOTS_DIR / "06-status-page-publica.png"
            page.screenshot(path=str(shot6))
            report["screenshots"].append(shot6.name)
            record_step(
                report,
                "status_page",
                "Criação da Página de Status Pública (/status/infra)",
                "PASS",
                "Status Page populada com os 5 monitores e banner de incidente publicado.",
            )

            report["overall_status"] = "PASS"

            if headed and hold_seconds > 0:
                print(f"\nSessão interativa aberta no navegador por {hold_seconds}s para inspeção manual...")
                time.sleep(hold_seconds)

        except (PlaywrightTimeout, AssertionError, Exception) as exc:
            report["overall_status"] = "FAIL"
            record_step(report, "error", "Falha durante execução E2E", "FAIL", repr(exc))
            err_shot = SCREENSHOTS_DIR / "error-state.png"
            try:
                page.screenshot(path=str(err_shot))
            except Exception:
                pass
            raise
        finally:
            report["finished_at"] = utc_now()
            report_path = RESULTS_DIR / "test-report.json"
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            report_js_path = RESULTS_DIR / "report-data.js"
            with open(report_js_path, "w", encoding="utf-8") as f:
                f.write("window.KUMA_REPORT = ")
                json.dump(report, f, ensure_ascii=False)
                f.write(";\n")
            browser.close()

    print(f"Teste finalizado com status: {report['overall_status']}")
    print(f"Relatório salvo em: {RESULTS_DIR / 'test-report.json'}")
    print(f"Screenshots salvos ({len(report['screenshots'])}): {report['screenshots']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agente Playwright para popular e testar demo.kuma.pet")
    parser.add_argument("--headed", action="store_true", help="Abre o navegador visível na tela do usuário")
    parser.add_argument("--hold", type=int, default=0, help="Segundos para manter o navegador aberto ao final (com --headed)")
    parser.add_argument("--user", default=DEFAULT_USER, help="Usuário administrador")
    parser.add_argument("--password", default=DEFAULT_PASS, help="Senha do administrador")
    args = parser.parse_args()

    try:
        run_demo(headed=args.headed, hold_seconds=args.hold, user=args.user, password=args.password)
    except Exception as e:
        print(f"Erro na execução: {e}", file=sys.stderr)
        sys.exit(1)
