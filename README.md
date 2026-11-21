# OpenSource Catalog

Portal web HTML5 minimalista e base estruturada reunindo **1.061 serviços e stacks open-source / self-hosted** organizados em **18 categorias**, com descrições objetivas em português, links para páginas oficiais, repositórios Git, páginas de demonstração e um sistema de **Score de Mercado (`0–100`)** baseado em telemetria real dos repositórios.

---

## Principais Recursos

- **Catálogo Completo (1.061 Serviços · 18 Categorias):** cobertura abrangente de ferramentas de IA/ML, Automação, DevTools, Infraestrutura, Bancos de Dados, Observabilidade, Segurança, CMS, Mídia, Finanças e Produtividade.
- **Score de Mercado & Saúde Comunitária (`0–100` e Nota `1.0–5.0 ★`):**
  - Coleta automatizada de estrelas (`stars`), `forks` e data do último commit/PR em **1.049+ repositórios** via `selfh.st`, `ungh.cc`, GitLab API v4 e Codeberg/Gitea API v1.
  - Classificação por nível de aceitação: **Líder de Mercado**, **Recomendado**, **Nicho / Emergente** e **Obsoleto / Baixa Atividade** (penalizando projetos arquivados ou sem atualizações há mais de 1–2 anos).
  - Modal **Raio-X de Mercado** detalhando os 4 pilares de pontuação.
- **Interface HTML5 Minimalista & Offline-First:**
  - Funciona abrindo `index.html` diretamente no navegador (`file://`) ou via qualquer servidor HTTP estático.
  - Busca instantânea (`/` ou `Ctrl+K`), filtros por categoria, recomendação de mercado, `+10k estrelas`, projetos ativos, com Git e com Demo.
  - Visualizações em **Categorias**, **Grade** e **Tabela Compacta**, alternância de **Tema Escuro/Claro** e exportação dinâmica para **JSON**, **CSV** e **Markdown**.
- **Suíte E2E Demo (`demos/uptime-kuma/`):**
  - Agente Playwright pronto para configurar, popular com 5 monitores reais e capturar telas da instância efêmera do **Uptime Kuma** (`demo.kuma.pet`), acompanhado de página HTML5 explicativa.

---

## Metodologia do Score de Mercado (`0–100`)

| Pilar | Peso | Critério Avaliado |
| :--- | :---: | :--- |
| **Aceitação de Mercado** | `0–40 pts` | Escala logarítmica sobre o total de estrelas (`stars`) no repositório Git. |
| **Atividade & Manutenção** | `0–35 pts` | Recência de commits e PRs (`<=14d`: 35 pts, `<=60d`: 31 pts, `<=180d`: 24 pts, `181–365d`: 14 pts). Projetos parados há `>1 ano` sofrem penalidade de `-10 pts` e `>2 anos` ou arquivados `-20/-25 pts`. |
| **Comunidade & Contribuições** | `0–15 pts` | Volume de `forks` em escala logarítmica + bônus de crescimento (`trending`). |
| **Maturidade & Ecossistema** | `0–10 pts` | Site oficial próprio (`+2`), página de demonstração pública (`+4`) e destaque de implantação (`+4`). |

> Soluções comerciais ou de código fechado (`git_url` ausente) são identificadas como **`Código Fechado / Comercial`** sem atribuição artificial de estrelas Git.

---

## Estrutura do Repositório

```text
opensource-catalog/
├── index.html                  # Portal HTML5 principal (sem dependências de build)
├── styles.css                  # Design system minimalista (Dark & Light Mode)
├── app.js                      # Lógica de busca, filtros, ordenação, modal Raio-X e exportação
├── data.js                     # Bundle JS (window.CATALOG_DATA) para execução local sem CORS
├── catalogo-servicos.json      # Base estruturada completa em JSON
├── CATALOGO.md                 # Documento Markdown completo agrupado por categoria
├── .env.example                # Modelo de variáveis de ambiente
├── .gitignore                  # Regras de arquivos ignorados pelo Git
├── scripts/
│   ├── raw_prompt.txt          # Lista de entrada original dos serviços
│   ├── fetch_repo_metrics.py   # Coletor paralelo de métricas Git (estrelas, forks, último commit)
│   └── build_catalog.py        # Gerador do catálogo, cálculo de score e exportação JSON/JS/MD
└── demos/
    └── uptime-kuma/            # Subprojeto E2E Playwright + tour visual do Uptime Kuma
        ├── index.html
        ├── README.md
        ├── scripts/run_kuma_demo.py
        ├── results/
        └── screenshots/
```

---

## Como Implementar e Executar em Outro Computador

### Pré-requisitos
- **Navegador moderno** (Chrome, Firefox, Edge ou Brave) — suficiente apenas para visualizar o portal.
- **Git** — para clonar o repositório.
- **Python 3.10+** — necessário apenas se você quiser servir via HTTP, atualizar as métricas Git ou executar o agente Playwright.

### Passo 1: Clonar o Repositório
```bash
git clone https://github.com/cleiton-ribeiro-work/opensource-catalog.git
cd opensource-catalog
```

### Passo 2: Configurar Variáveis de Ambiente
```bash
cp .env.example .env
# Edite o arquivo .env se quiser customizar porta, diretório de cache ou credenciais do demo
```

### Passo 3: Executar o Portal Web

**Opção A — Diretamente no navegador (Zero configuração):**
Abra o arquivo `index.html` diretamente no seu navegador (o arquivo `data.js` garante funcionamento completo mesmo via `file://`).

**Opção B — Servidor HTTP local com Python:**
```bash
python3 -m http.server 8080
# Acesse em: http://localhost:8080
```

**Opção C — Deploy estático via Docker (Nginx):**
```bash
docker run -d --name opensource-catalog -p 8080:80 \
  -v "$(pwd)":/usr/share/nginx/html:ro \
  nginx:alpine
```

### Passo 4 (Opcional): Atualizar Métricas Git e Reconstruir o Catálogo
Caso deseje atualizar o número de estrelas, último commit e recalcular os scores:

```bash
python3 -m venv .venv
source .venv/bin/activate        # No Windows: .venv\Scripts\activate
pip install pyyaml

# 1. Coleta métricas atualizadas de repositórios (salva cache em CATALOG_CACHE_DIR)
python3 scripts/fetch_repo_metrics.py

# 2. Recalcula os scores e regenera catalogo-servicos.json, data.js e CATALOGO.md
python3 scripts/build_catalog.py
```

### Passo 5 (Opcional): Executar o Agente de Demonstração Playwright (Uptime Kuma)
```bash
source .venv/bin/activate
pip install playwright
playwright install chromium

# Executa o agente com janela do navegador visível e mantém aberta por 120s para exploração
python3 demos/uptime-kuma/scripts/run_kuma_demo.py --headed --hold 120
```

---

## Como Contribuir e Abrir Novos Pull Requests (PRs)

Contribuições são muito bem-vindas — seja para adicionar novos serviços self-hosted, corrigir links oficiais/Git/demo, ajustar descrições ou aprimorar a interface!

### Fluxo para Novos PRs

1. **Faça um Fork** do repositório ou crie uma nova branch a partir da `main` atualizada:
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feat/adicionar-novo-servico
   ```
2. **Realize suas alterações**:
   - **Para corrigir links ou adicionar um novo serviço:** edite `scripts/build_catalog.py` (`CURATED_NON_DOCKER` / `VERIFIED_OVERRIDES`) e, se necessário, `scripts/raw_prompt.txt`.
   - **Para regenerar os dados e validar:**
     ```bash
     python3 scripts/fetch_repo_metrics.py
     python3 scripts/build_catalog.py
     ```
   - **Não edite manualmente** `data.js`, `catalogo-servicos.json` ou `CATALOGO.md` sem atualizar os scripts geradores, para manter a consistência entre fontes.
3. **Verifique antes do commit:**
   - Confirme que não há arquivos sensíveis (`.env`) na área de stage (`git status`).
   - Teste o carregamento de `index.html` no navegador garantindo 0 erros no console.
4. **Padronize suas mensagens de commit (Conventional Commits):**
   - `feat: adiciona serviço X na categoria Y`
   - `fix: corrige link Git e score do projeto Z`
   - `docs: atualiza instruções no README`
   - `chore: atualiza métricas de repositórios`
5. **Envie sua branch e abra o Pull Request:**
   ```bash
   git push -u origin feat/adicionar-novo-servico
   ```
   No GitHub, descreva claramente **o que foi alterado**, **por que** e inclua capturas de tela caso haja mudanças visuais na UI.

---

## Autor & Contato

- **Projeto:** OpenSource Catalog
- **GitHub:** [@cleiton-ribeiro-work](https://github.com/cleiton-ribeiro-work)
- **E-mail:** `cleiton.ribeiro.work@gmail.com`
