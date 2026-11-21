# Demonstração & Teste Automatizado — Uptime Kuma (`demo.kuma.pet`)

Este subprojeto cria um agente automatizado em **Playwright** para inicializar, configurar e popular a instância efêmera do **Uptime Kuma** (`https://demo.kuma.pet/start-demo`), que por padrão inicia vazia.

## Estrutura de Diretórios

```text
demos/uptime-kuma/
├── README.md                  # Este guia
├── index.html                 # Tour visual HTML5 com o que o Uptime Kuma entrega e relatório E2E
├── scripts/
│   └── run_kuma_demo.py       # Agente Playwright que configura conta, cria 5 monitores e Status Page
├── results/
│   └── test-report.json       # Relatório estruturado das etapas e asserções executadas
└── screenshots/               # Capturas reais do ambiente populado
```

## Credenciais Configuradas pelo Teste
- **Usuário:** `kuma-admin`
- **Senha:** `#E5V5BRFk5kUGNA`

## Como Executar o Agente no Seu Navegador (Modo Visível)

Para assistir o agente interagir em tempo real no navegador e manter a instância populada aberta por 2 minutos para você explorar:

```bash
/opt/dev-projects/GREENYARD-AI-NFL-VALUE-BETTING-ENGINE/backend/.venv/bin/python3 \
  /home/administrador/Documentos/dev/dev-projects/servicos-opensource-catalogo/demos/uptime-kuma/scripts/run_kuma_demo.py \
  --headed --hold 120
```
