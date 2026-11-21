#!/usr/bin/env python3
"""
Constrói o catálogo completo dos 1.061 serviços open-source / self-hosted:
- Extrai os nomes exatos da lista fornecida pelo usuário.
- Obtém categorias, descrições em pt-BR e recursos a partir dos metadados públicos.
- Cruza links oficiais, repositórios Git e URLs de demonstração em múltiplas bases abertas.
- Gera catalogo-servicos.json, data.js, CATALOGO.md e README.md.
"""

import json
import math
import os
import re
import tarfile
import urllib.request
from collections import defaultdict
from datetime import datetime
import yaml

REFERENCE_DATE = datetime.now()
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.environ.get("CATALOG_CACHE_DIR", "/tmp/catalog_cache")
METRICS_RESOLVED_PATH = os.path.join(CACHE_DIR, "repo_metrics_resolved.json")
RAW_PROMPT_PATH = os.path.join(ROOT_DIR, "raw_prompt.txt")
if not os.path.exists(RAW_PROMPT_PATH):
    RAW_PROMPT_PATH = os.path.join(ROOT_DIR, "scripts", "raw_prompt.txt")

CATEGORIES = {
    "aiml": {"label": "IA & Machine Learning", "order": 1},
    "automation": {"label": "Automação & Workflows", "order": 2},
    "developerTools": {"label": "Ferramentas para Desenvolvedores", "order": 3},
    "infrastructure": {"label": "Infraestrutura & Containers", "order": 4},
    "databases": {"label": "Bancos de Dados", "order": 5},
    "observability": {"label": "Observabilidade & Monitoramento", "order": 6},
    "security": {"label": "Segurança & Autenticação", "order": 7},
    "analytics": {"label": "Analytics & Dados", "order": 8},
    "cms": {"label": "CMS, Blogs & Portais", "order": 9},
    "eCommerce": {"label": "E-commerce & Lojas Virtuais", "order": 10},
    "communication": {"label": "Comunicação & Comunidades", "order": 11},
    "productivity": {"label": "Produtividade & Colaboração", "order": 12},
    "storageFiles": {"label": "Armazenamento & Arquivos", "order": 13},
    "media": {"label": "Mídia, Streaming & Entretenimento", "order": 14},
    "finance": {"label": "Finanças & Contabilidade", "order": 15},
    "homeLifestyle": {"label": "Casa Inteligente & Lifestyle", "order": 16},
    "utilities": {"label": "Utilitários & Ferramentas", "order": 17},
    "other": {"label": "Outros & Especializados", "order": 18},
}

# Metadados curados para os 45 templates/stacks que não constam no array Docker O()
CURATED_NON_DOCKER = {
    "Anaconda": {
        "category": "aiml",
        "description": "Distribuição Python e R voltada para ciência de dados, aprendizado de máquina e gerenciamento de ambientes.",
        "official": "https://www.anaconda.com/",
        "git": "https://github.com/conda/conda",
    },
    "Apache Airflow": {
        "category": "automation",
        "description": "Plataforma open-source para criar, agendar e monitorar programaticamente fluxos de trabalho e pipelines de dados.",
        "official": "https://airflow.apache.org/",
        "git": "https://github.com/apache/airflow",
    },
    "Appwrite": {
        "category": "developerTools",
        "description": "Plataforma Backend-as-a-Service (BaaS) open-source completa com autenticação, banco de dados, storage e funções.",
        "official": "https://appwrite.io/",
        "git": "https://github.com/appwrite/appwrite",
    },
    "ASP.NET": {
        "category": "developerTools",
        "description": "Framework web open-source e multiplataforma da Microsoft para construir aplicações web e APIs modernas em .NET.",
        "official": "https://dotnet.microsoft.com/apps/aspnet",
        "git": "https://github.com/dotnet/aspnetcore",
    },
    "AzuraCast": {
        "category": "media",
        "description": "Suíte completa e auto-hospedada de gerenciamento de web rádio com AutoDJ, agendamento e transmissão ao vivo.",
        "official": "https://www.azuracast.com/",
        "git": "https://github.com/AzuraCast/AzuraCast",
        "demo": "https://demo.azuracast.com/",
    },
    "Chatwoot": {
        "category": "communication",
        "description": "Plataforma open-source de atendimento ao cliente omnichannel integrada a e-mail, chat ao vivo, WhatsApp e redes sociais.",
        "official": "https://www.chatwoot.com/",
        "git": "https://github.com/chatwoot/chatwoot",
    },
    "Claude Code": {
        "category": "aiml",
        "description": "Agente de programação em terminal da Anthropic que entende bases de código, edita arquivos e executa comandos.",
        "official": "https://docs.anthropic.com/en/docs/claude-code/overview",
        "git": "https://github.com/anthropics/claude-code",
    },
    "ClusterControl": {
        "category": "databases",
        "description": "Plataforma de automação e gerenciamento para implantar, monitorar e escalar clusters de bancos de dados open-source.",
        "official": "https://severalnines.com/clustercontrol/",
    },
    "DeepSeek Harness": {
        "category": "aiml",
        "description": "Ambiente modular open-source para execução de agentes de código de IA com suporte a plugins e múltiplos runtimes.",
        "official": "https://github.com/deepseek-ai/deepseek-harness",
        "git": "https://github.com/deepseek-ai/deepseek-harness",
    },
    "Discourse": {
        "category": "communication",
        "description": "Plataforma moderna e open-source de fóruns de discussão, listas de e-mail e comunidades de longo prazo.",
        "official": "https://www.discourse.org/",
        "git": "https://github.com/discourse/discourse",
        "demo": "https://try.discourse.org/",
    },
    "Docker": {
        "category": "infrastructure",
        "description": "Plataforma padrão da indústria para empacotar, distribuir e executar aplicações isoladas em contêineres.",
        "official": "https://www.docker.com/",
        "git": "https://github.com/moby/moby",
    },
    "Docker e Traefik": {
        "category": "infrastructure",
        "description": "Ambiente pré-configurado com Docker Engine e Traefik como proxy reverso automático com certificados SSL Let's Encrypt.",
        "official": "https://traefik.io/",
        "git": "https://github.com/traefik/traefik",
    },
    "Dokku": {
        "category": "infrastructure",
        "description": "Mini-PaaS open-source baseado em Docker que permite implantar aplicações via `git push`, no estilo Heroku.",
        "official": "https://dokku.com/",
        "git": "https://github.com/dokku/dokku",
    },
    "Gemini CLI": {
        "category": "aiml",
        "description": "Agente de linha de comando open-source do Google que traz o poder dos modelos Gemini diretamente para o terminal.",
        "official": "https://geminicli.com/",
        "git": "https://github.com/google-gemini/gemini-cli",
    },
    "Grok Build": {
        "category": "aiml",
        "description": "Framework e CLI de agente de codificação da xAI voltado para automação e fluxos de engenharia assistidos por IA.",
        "official": "https://github.com/xai-org/grok-build",
        "git": "https://github.com/xai-org/grok-build",
    },
    "Herdr": {
        "category": "developerTools",
        "description": "Multiplexador de terminal nativo em Rust projetado para orquestrar e monitorar múltiplos agentes de código simultâneos.",
        "official": "https://herdr.dev/",
        "git": "https://github.com/herdrdev/herdr",
    },
    "IceWarp": {
        "category": "communication",
        "description": "Suíte corporativa integrada de servidor de e-mail, calendário, chat em equipe, videoconferência e documentos colaborativos.",
        "official": "https://www.icewarp.com/",
    },
    "Jitsi": {
        "category": "communication",
        "description": "Conjunto de projetos open-source para videoconferências seguras, criptografadas e auto-hospedadas via WebRTC.",
        "official": "https://jitsi.org/",
        "git": "https://github.com/jitsi/jitsi-meet",
        "demo": "https://meet.jit.si/",
    },
    "LAMP Stack (Apache, MySQL, PHP)": {
        "category": "infrastructure",
        "description": "Pilha clássica de servidor web Linux com Apache, banco de dados MySQL/MariaDB e PHP prontos para aplicações web.",
        "official": "https://httpd.apache.org/",
        "git": "https://github.com/apache/httpd",
    },
    "Laravel": {
        "category": "developerTools",
        "description": "Framework PHP elegante e expressivo com ecossistema completo para desenvolvimento ágil de aplicações web.",
        "official": "https://laravel.com/",
        "git": "https://github.com/laravel/laravel",
    },
    "LEMP Stack (Nginx, MySQL, PHP)": {
        "category": "infrastructure",
        "description": "Pilha de servidor web de alto desempenho combinando Linux, Nginx, MySQL/MariaDB e PHP-FPM.",
        "official": "https://nginx.org/",
        "git": "https://github.com/nginx/nginx",
    },
    "Magento 2": {
        "category": "eCommerce",
        "description": "Plataforma robusta e escalável de comércio eletrônico open-source (Adobe Commerce / Magento Open Source) em PHP.",
        "official": "https://business.adobe.com/products/magento/open-source.html",
        "git": "https://github.com/magento/magento2",
    },
    "MCP Server": {
        "category": "aiml",
        "description": "Servidor baseado no Model Context Protocol (MCP) para expor ferramentas, recursos e contextos padronizados a modelos de IA.",
        "official": "https://modelcontextprotocol.io/",
        "git": "https://github.com/modelcontextprotocol/servers",
    },
    "MEAN Stack (MongoDB, ExpressJS, AngularJS, NodeJS)": {
        "category": "infrastructure",
        "description": "Pilha JavaScript/TypeScript full-stack pré-configurada com MongoDB, Express, Angular e Node.js.",
        "official": "https://nodejs.org/",
        "git": "https://github.com/linnovate/mean",
    },
    "MediaWIKI": {
        "category": "cms",
        "description": "Software wiki open-source altamente escalável em PHP que alimenta a Wikipédia e bases de conhecimento colaborativas.",
        "official": "https://www.mediawiki.org/",
        "git": "https://github.com/wikimedia/mediawiki",
    },
    "MERN Stack (MongoDB, ExpressJS, ReactJS, NodeJS)": {
        "category": "infrastructure",
        "description": "Pilha full-stack moderna em JavaScript reunindo MongoDB, Express.js, React e Node.js.",
        "official": "https://react.dev/",
        "git": "https://github.com/Hashnode/mern-starter",
    },
    "MEVN Stack (MongoDB, ExpressJS, VueJS, NodeJS)": {
        "category": "infrastructure",
        "description": "Pilha full-stack em JavaScript combinando MongoDB, Express.js, Vue.js e Node.js para aplicações reativas.",
        "official": "https://vuejs.org/",
        "git": "https://github.com/vuejs/core",
    },
    "n8n (+100 workflows)": {
        "category": "automation",
        "description": "Instância do n8n pré-carregada com mais de 100 modelos prontos de fluxos de trabalho de automação e IA.",
        "official": "https://n8n.io/",
        "git": "https://github.com/n8n-io/n8n",
    },
    "n8n (queue mode)": {
        "category": "automation",
        "description": "Implantação do n8n em modo de fila escalável utilizando Redis e workers dedicados para cargas intensas de automação.",
        "official": "https://docs.n8n.io/hosting/scaling/queue-mode/",
        "git": "https://github.com/n8n-io/n8n",
    },
    "NemoClaw": {
        "category": "aiml",
        "description": "Pilha de referência e runtime seguro da NVIDIA para isolar e executar agentes autônomos de IA em contêineres OpenShell.",
        "official": "https://github.com/NVIDIA/NemoClaw",
        "git": "https://github.com/NVIDIA/NemoClaw",
    },
    "NextCloud": {
        "category": "storageFiles",
        "description": "Template VPS otimizado da plataforma Nextcloud para armazenamento em nuvem privada, sincronização e colaboração.",
        "official": "https://nextcloud.com/",
        "git": "https://github.com/nextcloud/server",
        "demo": "https://try.nextcloud.com/",
    },
    "Nod": {
        "category": "aiml",
        "description": "Agente pessoal de IA sempre ativo criado pela equipe do n8n, com espaço Linux isolado e navegador headless para fluxos cotidianos.",
        "official": "https://n8n.io/",
        "git": "https://github.com/n8n-io/n8n",
    },
    "OpenAI Codex": {
        "category": "aiml",
        "description": "Agente de codificação leve em linha de comando (CLI) da OpenAI que lê, edita e executa código diretamente no terminal.",
        "official": "https://developers.openai.com/codex/cli/",
        "git": "https://github.com/openai/codex",
    },
    "OpenCart": {
        "category": "eCommerce",
        "description": "Sistema de e-commerce open-source leve e amigável em PHP para criação e gestão de lojas online multi-loja.",
        "official": "https://www.opencart.com/",
        "git": "https://github.com/opencart/opencart",
        "demo": "https://demo.opencart.com/",
    },
    "OpenLiteSpeed e Django": {
        "category": "infrastructure",
        "description": "Servidor web OpenLiteSpeed de alta velocidade pré-configurado com Python e o framework web Django.",
        "official": "https://openlitespeed.org/",
        "git": "https://github.com/litespeedtech/openlitespeed",
    },
    "OpenLiteSpeed e Drupal": {
        "category": "cms",
        "description": "Servidor web OpenLiteSpeed otimizado com LSCache para hospedar o CMS enterprise open-source Drupal.",
        "official": "https://openlitespeed.org/",
        "git": "https://github.com/litespeedtech/openlitespeed",
    },
    "OpenLiteSpeed e Joomla": {
        "category": "cms",
        "description": "Servidor web OpenLiteSpeed configurado com cache integrado para sites e portais em Joomla.",
        "official": "https://openlitespeed.org/",
        "git": "https://github.com/litespeedtech/openlitespeed",
    },
    "OpenLiteSpeed e Node.js": {
        "category": "infrastructure",
        "description": "Ambiente combinando o servidor OpenLiteSpeed com suporte nativo para executar aplicações JavaScript em Node.js.",
        "official": "https://openlitespeed.org/",
        "git": "https://github.com/litespeedtech/openlitespeed",
    },
    "OpenLiteSpeed e Rails": {
        "category": "infrastructure",
        "description": "Servidor OpenLiteSpeed pré-configurado para hospedar aplicações web escritas em Ruby on Rails com alto desempenho.",
        "official": "https://openlitespeed.org/",
        "git": "https://github.com/litespeedtech/openlitespeed",
    },
    "OpenLiteSpeed e WordPress": {
        "category": "cms",
        "description": "Stack WordPress acelerada pelo servidor OpenLiteSpeed e plugin LiteSpeed Cache prontos para produção.",
        "official": "https://openlitespeed.org/",
        "git": "https://github.com/litespeedtech/openlitespeed",
    },
    "Portainer": {
        "category": "infrastructure",
        "description": "Interface web visual e intuitiva para gerenciar ambientes Docker, Docker Swarm e Kubernetes com facilidade.",
        "official": "https://www.portainer.io/",
        "git": "https://github.com/portainer/portainer",
    },
    "PostHog": {
        "category": "analytics",
        "description": "Plataforma open-source completa de analytics de produto com gravação de sessões, feature flags e testes A/B.",
        "official": "https://posthog.com/",
        "git": "https://github.com/PostHog/posthog",
    },
    "TYPO3": {
        "category": "cms",
        "description": "CMS corporativo open-source altamente extensível em PHP, voltado para portais multi-idioma e grandes organizações.",
        "official": "https://typo3.org/",
        "git": "https://github.com/typo3/typo3",
    },
    "Ubuntu com XRDP": {
        "category": "infrastructure",
        "description": "Ambiente Ubuntu Linux com interface gráfica e servidor XRDP configurado para acesso via Área de Trabalho Remota (RDP).",
        "official": "https://ubuntu.com/",
        "git": "https://github.com/neutrinolabs/xrdp",
    },
    "WooCommerce": {
        "category": "eCommerce",
        "description": "Plugin open-source de e-commerce mais popular para WordPress, transformando sites em lojas virtuais completas.",
        "official": "https://woocommerce.com/",
        "git": "https://github.com/woocommerce/woocommerce",
    },
}

# Links verificados manualmente/via pesquisa web para itens que não constam ou divergem nas bases agregadas
VERIFIED_OVERRIDES = {
    "1Backend": {"official": "https://github.com/1backend/1backend", "git": "https://github.com/1backend/1backend"},
    "agentmemory": {"official": "https://agentmemory.tech/", "git": "https://github.com/rohitg00/agentmemory"},
    "AgentRun": {"official": "https://agentrun.ai/", "git": "https://github.com/Serverless-Devs/agentrun-cli"},
    "AiToEarn": {"official": "https://github.com/yikart/AiToEarn", "git": "https://github.com/yikart/AiToEarn"},
    "Anki Sync Server Enhanced": {"official": "https://github.com/chrislongros/anki-sync-server-enhanced", "git": "https://github.com/chrislongros/anki-sync-server-enhanced"},
    "Annif": {"official": "https://annif.org/", "git": "https://github.com/NatLibFi/Annif"},
    "Ant Media Server CE": {"official": "https://antmedia.io/", "git": "https://github.com/ant-media/Ant-Media-Server"},
    "Apollo": {"official": "https://www.apolloconfig.com/", "git": "https://github.com/apolloconfig/apollo"},
    "AstrBot": {"official": "https://astrbot.app/", "git": "https://github.com/AstrBotDevs/AstrBot"},
    "AureusERP": {"official": "https://aureuserp.com/", "git": "https://github.com/aureuserp/aureuserp"},
    "Auto Ontology": {"official": "https://github.com/NVIDIA/auto-ontology", "git": "https://github.com/NVIDIA/auto-ontology"},
    "Big-AGI": {"official": "https://big-agi.com/", "git": "https://github.com/enricoros/big-AGI"},
    "Bionic GPT": {"official": "https://bionic-gpt.com/", "git": "https://github.com/bionic-gpt/bionic-gpt"},
    "Bluesky Ozone": {"official": "https://github.com/bluesky-social/ozone", "git": "https://github.com/bluesky-social/ozone"},
    "Bookshelf": {"official": "https://github.com/pennydreadful/bookshelf", "git": "https://github.com/pennydreadful/bookshelf"},
    "ByteChef": {"official": "https://www.bytechef.io/", "git": "https://github.com/bytechefhq/bytechef"},
    "Casibase": {"official": "https://casibase.org/", "git": "https://github.com/casibase/casibase"},
    "Cassandra Reaper": {"official": "https://cassandra-reaper.io/", "git": "https://github.com/thelastpickle/cassandra-reaper"},
    "Checkrr": {"official": "https://github.com/aetaric/checkrr", "git": "https://github.com/aetaric/checkrr"},
    "CitrineOS": {"official": "https://citrineos.github.io/", "git": "https://github.com/citrineos/citrineos-core"},
    "CiviCRM": {"official": "https://civicrm.org/", "git": "https://github.com/civicrm/civicrm-core", "demo": "https://dmaster.demo.civicrm.org/"},
    "ClassQuiz": {"official": "https://classquiz.de/", "git": "https://github.com/mawoka-myblock/ClassQuiz"},
    "ClassroomIO": {"official": "https://www.classroomio.com/", "git": "https://github.com/classroomio/classroomio"},
    "Coai": {"official": "https://github.com/coaidev/coai", "git": "https://github.com/coaidev/coai"},
    "Cockpit CMS": {"official": "https://getcockpit.com/", "git": "https://github.com/Cockpit-HQ/Cockpit"},
    "Cognee": {"official": "https://www.cognee.ai/", "git": "https://github.com/topoteretes/cognee"},
    "Coral Talk": {"official": "https://coralproject.net/", "git": "https://github.com/coralproject/talk"},
    "CoreControl": {"official": "https://github.com/crocofied/CoreControl", "git": "https://github.com/crocofied/CoreControl"},
    "Crontab UI": {"official": "https://alseambusher.github.io/crontab-ui/", "git": "https://github.com/alseambusher/crontab-ui"},
    "Crucix": {"official": "https://github.com/calesthio/Crucix", "git": "https://github.com/calesthio/Crucix"},
    "CVAT": {"official": "https://www.cvat.ai/", "git": "https://github.com/cvat-ai/cvat", "demo": "https://app.cvat.ai/"},
    "Dasharr": {"official": "https://github.com/Arcadia-Solutions/Dasharr", "git": "https://github.com/Arcadia-Solutions/Dasharr"},
    "DB Browser for SQLite": {"official": "https://sqlitebrowser.org/", "git": "https://github.com/sqlitebrowser/sqlitebrowser"},
    "Decidim": {"official": "https://decidim.org/", "git": "https://github.com/decidim/decidim", "demo": "https://try.decidim.org/"},
    "DeepWiki Open": {"official": "https://github.com/AsyncFuncAI/deepwiki-open", "git": "https://github.com/AsyncFuncAI/deepwiki-open"},
    "Dependency-Track": {"official": "https://dependencytrack.org/", "git": "https://github.com/DependencyTrack/dependency-track"},
    "DeskRPG": {"official": "https://github.com/dandacompany/deskrpg", "git": "https://github.com/dandacompany/deskrpg"},
    "DHIS2": {"official": "https://dhis2.org/", "git": "https://github.com/dhis2/dhis2-core", "demo": "https://play.im.dhis2.org/"},
    "Dialoqbase": {"official": "https://github.com/n4ze3m/dialoqbase", "git": "https://github.com/n4ze3m/dialoqbase"},
    "Dkron": {"official": "https://dkron.io/", "git": "https://github.com/dkron-io/dkron"},
    "Dograh": {"official": "https://www.dograh.com/", "git": "https://github.com/dograh-hq/dograh"},
    "Eclipse Hawkbit": {"official": "https://eclipse.dev/hawkbit/", "git": "https://github.com/eclipse-hawkbit/hawkbit"},
    "Eclipse Kura": {"official": "https://eclipse.dev/kura/", "git": "https://github.com/eclipse-kura/kura"},
    "EdgeDB": {"official": "https://www.geldata.com/", "git": "https://github.com/geldata/gel"},
    "Errbit": {"official": "https://errbit.com/", "git": "https://github.com/errbit/errbit"},
    "Euro-Office DocumentServer": {"official": "https://github.com/Euro-Office/DocumentServer", "git": "https://github.com/Euro-Office/DocumentServer"},
    "eve": {"official": "https://github.com/vercel/eve", "git": "https://github.com/vercel/eve"},
    "eXeLearning": {"official": "https://exelearning.net/", "git": "https://github.com/exelearning/iteexe"},
    "Faktory": {"official": "https://contribsys.com/faktory/", "git": "https://github.com/contribsys/faktory"},
    "Fasten Health": {"official": "https://www.fastenhealth.com/", "git": "https://github.com/fastenhealth/fasten-onprem"},
    "fazer.ai agents": {"official": "https://fazer.ai/", "git": "https://github.com/fazer-ai/chatwoot"},
    "FeedCraft": {"official": "https://github.com/Colin-XKL/FeedCraft", "git": "https://github.com/Colin-XKL/FeedCraft"},
    "Fleetbase": {"official": "https://www.fleetbase.io/", "git": "https://github.com/fleetbase/fleetbase"},
    "FMD (Find My Device)": {"official": "https://fmd-foss.org/", "git": "https://gitlab.com/fmd-foss/fmd-server"},
    "Foxel": {"official": "https://github.com/DrizzleTime/Foxel", "git": "https://github.com/DrizzleTime/Foxel"},
    "FUXA": {"official": "https://github.com/frangoteam/FUXA", "git": "https://github.com/frangoteam/FUXA"},
    "Galaxy": {"official": "https://galaxyproject.org/", "git": "https://github.com/galaxyproject/galaxy"},
    "Geneac": {"official": "https://geneac.net/", "git": "https://github.com/mrysav/geneac"},
    "GeoNetwork": {"official": "https://geonetwork-opensource.org/", "git": "https://github.com/geonetwork/core-geonetwork"},
    "GrowthBook": {"official": "https://www.growthbook.io/", "git": "https://github.com/growthbook/growthbook"},
    "Hanko": {"official": "https://www.hanko.io/", "git": "https://github.com/teamhanko/hanko"},
    "Headroom": {"official": "https://github.com/headroomlabs-ai/headroom", "git": "https://github.com/headroomlabs-ai/headroom"},
    "Hermes WebUI": {"official": "https://github.com/nesquena/hermes-webui", "git": "https://github.com/nesquena/hermes-webui"},
    "Hermes Workspace": {"official": "https://github.com/outsourc-e/hermes-workspace", "git": "https://github.com/outsourc-e/hermes-workspace"},
    "HFS": {"official": "https://www.rejetto.com/hfs/", "git": "https://github.com/rejetto/hfs"},
    "Hollama": {"official": "https://hollama.fernando.is/", "git": "https://github.com/fmaclen/hollama"},
    "Hoop": {"official": "https://hoop.dev/", "git": "https://github.com/hoophq/hoop"},
    "Horilla": {"official": "https://www.horilla.com/", "git": "https://github.com/horilla-opensource/horilla"},
    "HuggingChat (Chat UI)": {"official": "https://huggingface.co/chat/", "git": "https://github.com/huggingface/chat-ui"},
    "Hugo": {"official": "https://gohugo.io/", "git": "https://github.com/gohugoio/hugo"},
    "ILLA Builder": {"official": "https://www.illacloud.com/", "git": "https://github.com/illacloud/illa-builder"},
    "Imaginary": {"official": "https://github.com/h2non/imaginary", "git": "https://github.com/h2non/imaginary"},
    "ImmuDB": {"official": "https://immudb.io/", "git": "https://github.com/codenotary/immudb"},
    "InsForge": {"official": "https://insforge.dev/", "git": "https://github.com/InsForge/InsForge"},
    "Jelly-Clipper": {"official": "https://github.com/arnolicious/jelly-clipper", "git": "https://github.com/arnolicious/jelly-clipper"},
    "jfa-go": {"official": "https://jfa-go.com/", "git": "https://github.com/hrfee/jfa-go"},
    "JobOps": {"official": "https://github.com/DaKheera47/job-ops", "git": "https://github.com/DaKheera47/job-ops"},
    "Jump": {"official": "https://github.com/daledavies/jump", "git": "https://github.com/daledavies/jump"},
    "Juxtapose": {"official": "https://github.com/jc21/juxtapose", "git": "https://github.com/jc21/juxtapose"},
    "Kafbat Kafka UI": {"official": "https://ui.docs.kafbat.io/", "git": "https://github.com/kafbat/kafka-ui"},
    "KasmVNC": {"official": "https://www.kasmweb.com/kasmvnc", "git": "https://github.com/kasmtech/KasmVNC"},
    "Kibana": {"official": "https://www.elastic.co/kibana", "git": "https://github.com/elastic/kibana"},
    "Komari": {"official": "https://github.com/komari-monitor/komari", "git": "https://github.com/komari-monitor/komari"},
    "Kotaemon": {"official": "https://github.com/Cinnamon/kotaemon", "git": "https://github.com/Cinnamon/kotaemon"},
    "Krayin CRM": {"official": "https://krayincrm.com/", "git": "https://github.com/krayin/laravel-crm", "demo": "https://demo.krayincrm.com/"},
    "LakeFS": {"official": "https://lakefs.io/", "git": "https://github.com/treeverse/lakeFS"},
    "LavinMQ": {"official": "https://lavinmq.com/", "git": "https://github.com/cloudamqp/lavinmq"},
    "LDAP Account Manager": {"official": "https://www.ldap-account-manager.org/", "git": "https://github.com/LDAPAccountManager/lam"},
    "LightRAG": {"official": "https://github.com/HKUDS/LightRAG", "git": "https://github.com/HKUDS/LightRAG"},
    "Littlelink-Server": {"official": "https://github.com/techno-tim/littlelink-server", "git": "https://github.com/techno-tim/littlelink-server"},
    "Locust": {"official": "https://locust.io/", "git": "https://github.com/locustio/locust"},
    "M3DB": {"official": "https://m3db.io/", "git": "https://github.com/m3db/m3"},
    "Mailtrain": {"official": "https://mailtrain.org/", "git": "https://github.com/Mailtrain-org/mailtrain"},
    "MapStore": {"official": "https://geosolutionsgroup.com/technologies/mapstore/", "git": "https://github.com/geosolutions-it/MapStore"},
    "Maputnik": {"official": "https://maputnik.github.io/", "git": "https://github.com/maputnik/editor", "demo": "https://maputnik.github.io/editor/"},
    "MaxKB": {"official": "https://maxkb.pro/", "git": "https://github.com/1Panel-dev/MaxKB"},
    "MediaGo": {"official": "https://downloader.caorushizi.cn/", "git": "https://github.com/caorushizi/mediago"},
    "Meteroid": {"official": "https://github.com/meteroid-oss/meteroid", "git": "https://github.com/meteroid-oss/meteroid"},
    "MicroRealEstate": {"official": "https://microrealestate.org/", "git": "https://github.com/microrealestate/microrealestate"},
    "Microweber": {"official": "https://microweber.org/", "git": "https://github.com/microweber/microweber"},
    "MiroFish": {"official": "https://github.com/666ghj/MiroFish", "git": "https://github.com/666ghj/MiroFish"},
    "MySQL": {"official": "https://www.mysql.com/", "git": "https://github.com/mysql/mysql-server"},
    "NextChat": {"official": "https://nextchat.dev/", "git": "https://github.com/ChatGPTNextWeb/NextChat"},
    "Nexus Repository Manager": {"official": "https://www.sonatype.com/products/sonatype-nexus-repository", "git": "https://github.com/sonatype/nexus-public"},
    "Nightlio": {"official": "https://github.com/shirsakm/nightlio", "git": "https://github.com/shirsakm/nightlio"},
    "nopCommerce": {"official": "https://www.nopcommerce.com/", "git": "https://github.com/nopSolutions/nopCommerce", "demo": "https://www.nopcommerce.com/demo"},
    "NSQ": {"official": "https://nsq.io/", "git": "https://github.com/nsqio/nsq"},
    "Nuclio": {"official": "https://nuclio.io/", "git": "https://github.com/nuclio/nuclio"},
    "OCS Inventory NG": {"official": "https://ocsinventory-ng.org/", "git": "https://github.com/OCSInventory-NG/OCSInventory-Server"},
    "October CMS": {"official": "https://octobercms.com/", "git": "https://github.com/octobercms/october"},
    "Odysseus": {"official": "https://github.com/odysseus-ai/odysseus", "git": "https://github.com/odysseus-ai/odysseus"},
    "OMERO": {"official": "https://www.openmicroscopy.org/omero/", "git": "https://github.com/ome/openmicroscopy"},
    "Onyx": {"official": "https://www.onyx.app/", "git": "https://github.com/onyx-dot-app/onyx"},
    "Open Monograph Press": {"official": "https://pkp.sfu.ca/software/omp/", "git": "https://github.com/pkp/omp"},
    "OpenFGA": {"official": "https://openfga.dev/", "git": "https://github.com/openfga/openfga"},
    "OpenHuman": {"official": "https://github.com/tinyhumansai/openhuman", "git": "https://github.com/tinyhumansai/openhuman"},
    "OpenLIT": {"official": "https://openlit.io/", "git": "https://github.com/openlit/openlit"},
    "OpenMausBot": {"official": "https://github.com/milind-soni/OpenMausBot", "git": "https://github.com/milind-soni/OpenMausBot"},
    "OpenVPN Access Server": {"official": "https://openvpn.net/access-server/"},
    "OSRM": {"official": "https://project-osrm.org/", "git": "https://github.com/Project-OSRM/osrm-backend", "demo": "https://map.project-osrm.org/"},
    "Pangolin Newt": {"official": "https://docs.digpangolin.com/", "git": "https://github.com/fosrl/newt"},
    "Parse Server": {"official": "https://parseplatform.org/", "git": "https://github.com/parse-community/parse-server"},
    "Percona PMM": {"official": "https://www.percona.com/software/database-tools/percona-monitoring-and-management", "git": "https://github.com/percona/pmm"},
    "Perplexica": {"official": "https://github.com/ItzCrazyKns/Perplexica", "git": "https://github.com/ItzCrazyKns/Perplexica"},
    "Posterr": {"official": "https://github.com/petersem/posterr", "git": "https://github.com/petersem/posterr"},
    "PostgreSQL": {"official": "https://www.postgresql.org/", "git": "https://github.com/postgres/postgres"},
    "pycsw": {"official": "https://pycsw.org/", "git": "https://github.com/geopython/pycsw"},
    "pygeoapi": {"official": "https://pygeoapi.io/", "git": "https://github.com/geopython/pygeoapi", "demo": "https://demo.pygeoapi.io/"},
    "Quasarr": {"official": "https://github.com/rix1337/Quasarr", "git": "https://github.com/rix1337/Quasarr"},
    "R2R": {"official": "https://r2r-docs.sciphi.ai/", "git": "https://github.com/SciPhi-AI/R2R"},
    "RAGflow": {"official": "https://ragflow.io/", "git": "https://github.com/infiniflow/ragflow", "demo": "https://demo.ragflow.io/"},
    "Readyset": {"official": "https://readyset.io/", "git": "https://github.com/readysettech/readyset"},
    "Redis": {"official": "https://redis.io/", "git": "https://github.com/redis/redis"},
    "Redis Commander": {"official": "https://joeferner.github.io/redis-commander/", "git": "https://github.com/joeferner/redis-commander"},
    "Redpanda Console": {"official": "https://www.redpanda.com/", "git": "https://github.com/redpanda-data/console"},
    "Scada-LTS": {"official": "https://scada-lts.org/", "git": "https://github.com/SCADA-LTS/Scada-LTS"},
    "SENAITE LIMS": {"official": "https://www.senaite.com/", "git": "https://github.com/senaite/senaite.lims"},
    "ServerStatus": {"official": "https://github.com/cppla/ServerStatus", "git": "https://github.com/cppla/ServerStatus"},
    "Shadowbroker": {"official": "https://github.com/BigBodyCobain/Shadowbroker", "git": "https://github.com/BigBodyCobain/Shadowbroker"},
    "Sherlock": {"official": "https://sherlockproject.xyz/", "git": "https://github.com/sherlock-project/sherlock"},
    "ShinyProxy": {"official": "https://www.shinyproxy.io/", "git": "https://github.com/openanalytics/shinyproxy"},
    "SillyTavern": {"official": "https://sillytavern.app/", "git": "https://github.com/SillyTavern/SillyTavern"},
    "Smocker": {"official": "https://smocker.dev/", "git": "https://github.com/Thiht/smocker"},
    "Songloft": {"official": "https://github.com/songloft-org/songloft", "git": "https://github.com/songloft-org/songloft"},
    "Speaches": {"official": "https://speaches.ai/", "git": "https://github.com/speaches-ai/speaches"},
    "Spice AI": {"official": "https://spice.ai/", "git": "https://github.com/spiceai/spiceai"},
    "Spree": {"official": "https://spreecommerce.org/", "git": "https://github.com/spree/spree"},
    "StarRocks": {"official": "https://www.starrocks.io/", "git": "https://github.com/StarRocks/starrocks"},
    "Statistics for Strava": {"official": "https://github.com/robiningelbrecht/statistics-for-strava", "git": "https://github.com/robiningelbrecht/statistics-for-strava", "demo": "https://statistics-for-strava.robiningelbrecht.be/"},
    "Steel Browser": {"official": "https://steel.dev/", "git": "https://github.com/steel-dev/steel-browser"},
    "Sun-Panel": {"official": "https://sun-panel.top/", "git": "https://github.com/hslr-s/sun-panel"},
    "SuperTokens": {"official": "https://supertokens.com/", "git": "https://github.com/supertokens/supertokens-core"},
    "TaxHacker": {"official": "https://github.com/vas3k/TaxHacker", "git": "https://github.com/vas3k/TaxHacker"},
    "Teedy": {"official": "https://teedy.io/", "git": "https://github.com/sismics/docs"},
    "TensorZero": {"official": "https://www.tensorzero.com/", "git": "https://github.com/tensorzero/tensorzero"},
    "Text Generation Web UI": {"official": "https://github.com/oobabooga/text-generation-webui", "git": "https://github.com/oobabooga/text-generation-webui"},
    "Thruk": {"official": "https://www.thruk.org/", "git": "https://github.com/sni/Thruk"},
    "Topola Genealogy Viewer": {"official": "https://pewu.github.io/topola-viewer/", "git": "https://github.com/PeWu/topola-viewer", "demo": "https://pewu.github.io/topola-viewer/"},
    "Trino": {"official": "https://trino.io/", "git": "https://github.com/trinodb/trino"},
    "Twingate Connector": {"official": "https://www.twingate.com/"},
    "Vince Analytics": {"official": "https://vinceanalytics.com/", "git": "https://github.com/vinceanalytics/vince"},
    "Visual Studio Code Server": {"official": "https://code.visualstudio.com/docs/remote/vscode-server", "git": "https://github.com/microsoft/vscode"},
    "Waline": {"official": "https://waline.js.org/", "git": "https://github.com/walinejs/waline"},
    "WeKnora": {"official": "https://github.com/Tencent/WeKnora", "git": "https://github.com/Tencent/WeKnora"},
    "Whishper": {"official": "https://github.com/pluja/whishper", "git": "https://github.com/pluja/whishper"},
    "WireMock": {"official": "https://wiremock.org/", "git": "https://github.com/wiremock/wiremock"},
    "withoutbg": {"official": "https://withoutbg.com/", "git": "https://github.com/withoutbg/withoutbg"},
    "Xibo CMS": {"official": "https://xibosignage.com/", "git": "https://github.com/xibosignage/xibo-cms"},
    "Yaade": {"official": "https://docs.yaade.io/", "git": "https://github.com/EsperoTech/yaade"},
    "Yarn": {"official": "https://yarnpkg.com/", "git": "https://github.com/yarnpkg/berry"},
    "Zenfeed": {"official": "https://github.com/glidea/zenfeed", "git": "https://github.com/glidea/zenfeed"},
    "Apache Amoro": {"official": "https://amoro.apache.org/", "git": "https://github.com/apache/amoro"},
    "Apache DevLake": {"official": "https://devlake.apache.org/", "git": "https://github.com/apache/devlake"},
    "Apache Gravitino": {"official": "https://gravitino.apache.org/", "git": "https://github.com/apache/gravitino"},
    "Apache Kvrocks": {"official": "https://kvrocks.apache.org/", "git": "https://github.com/apache/kvrocks"},
    "Apache ShenYu": {"official": "https://shenyu.apache.org/", "git": "https://github.com/apache/shenyu"},
    "Apache StreamPark": {"official": "https://streampark.apache.org/", "git": "https://github.com/apache/streampark"},
    "Blender": {"official": "https://www.blender.org/", "git": "https://projects.blender.org/blender/blender"},
    "Buildbot": {"official": "https://buildbot.net/", "git": "https://github.com/buildbot/buildbot"},
    "Collabora Online": {"official": "https://www.collaboraoffice.com/collabora-online/", "git": "https://github.com/CollaboraOnline/online"},
    "DenoKV": {"official": "https://deno.com/kv", "git": "https://github.com/denoland/denokv"},
    "Drizzle Gateway": {"official": "https://orm.drizzle.team/", "git": "https://github.com/drizzle-team/drizzle-orm"},
    "DuckDNS": {"official": "https://www.duckdns.org/", "git": "https://github.com/linuxserver/docker-duckdns"},
    "FileFlows": {"official": "https://fileflows.com/", "git": None},
    "Firefly": {"official": "https://www.firefly-iii.org/", "git": "https://github.com/firefly-iii/firefly-iii"},
    "Firefox": {"official": "https://www.mozilla.org/firefox/", "git": "https://github.com/linuxserver/docker-firefox"},
    "FlexGet": {"official": "https://flexget.com/", "git": "https://github.com/Flexget/Flexget"},
    "FreeCAD": {"official": "https://www.freecad.org/", "git": "https://github.com/FreeCAD/FreeCAD"},
    "FusionDirectory": {"official": "https://www.fusiondirectory.org/", "git": "https://gitlab.fusiondirectory.org/fusiondirectory/fd"},
    "GIMP": {"official": "https://www.gimp.org/", "git": "https://gitlab.gnome.org/GNOME/gimp"},
    "GNS3 Server": {"official": "https://www.gns3.com/", "git": "https://github.com/GNS3/gns3-server"},
    "HandBrake": {"official": "https://handbrake.fr/", "git": "https://github.com/HandBrake/HandBrake"},
    "Harness": {"official": "https://www.harness.io/", "git": "https://github.com/harness/harness"},
    "Inkscape": {"official": "https://inkscape.org/", "git": "https://gitlab.com/inkscape/inkscape"},
    "jsreport": {"official": "https://jsreport.net/", "git": "https://github.com/jsreport/jsreport"},
    "LibreNMS": {"official": "https://www.librenms.org/", "git": "https://github.com/librenms/librenms"},
    "NetBird Client": {"official": "https://netbird.io/", "git": "https://github.com/netbirdio/netbird"},
    "New API": {"official": "https://github.com/QuantumNous/new-api", "git": "https://github.com/QuantumNous/new-api"},
    "Pydio Cells": {"official": "https://pydio.com/", "git": "https://github.com/pydio/cells"},
    "Ralph": {"official": "https://ralph.allegro.tech/", "git": "https://github.com/allegro/ralph"},
    "Remmina": {"official": "https://remmina.org/", "git": "https://gitlab.com/Remmina/Remmina"},
    "Snapdrop": {"official": "https://snapdrop.net/", "git": "https://github.com/RobinLinus/snapdrop"},
    "WebCord": {"official": "https://github.com/SpacingBat3/WebCord", "git": "https://github.com/SpacingBat3/WebCord"},
    "WireGuard Easy": {"official": "https://github.com/wg-easy/wg-easy", "git": "https://github.com/wg-easy/wg-easy"},
    "WPS Office": {"official": "https://www.wps.com/", "git": "https://github.com/linuxserver/docker-wps-office"},
    "Yucca": {"official": "https://yucca.app/", "git": "https://github.com/yuccastream/yucca"},
    "Apache Doris": {"official": "https://doris.apache.org/", "git": "https://github.com/apache/doris"},
    "Apache JSPWiki": {"official": "https://jspwiki.apache.org/", "git": "https://github.com/apache/jspwiki"},
    "Apache Pinot": {"official": "https://pinot.apache.org/", "git": "https://github.com/apache/pinot"},
    "Apache Zeppelin": {"official": "https://zeppelin.apache.org/", "git": "https://github.com/apache/zeppelin"},
    "ClassicPress": {"official": "https://www.classicpress.net/", "git": "https://github.com/ClassicPress/ClassicPress"},
    "ClusterControl": {"official": "https://severalnines.com/clustercontrol/", "git": None},
    "Deluge": {"official": "https://deluge-torrent.org/", "git": "https://github.com/deluge-torrent/deluge"},
    "Drupal": {"official": "https://www.drupal.org/", "git": "https://github.com/drupal/drupal"},
    "Iceshrimp": {"official": "https://iceshrimp.dev/", "git": "https://iceshrimp.dev/iceshrimp/iceshrimp"},
    "Phoenix": {"official": "https://phoenix.arize.com/", "git": "https://github.com/Arize-ai/phoenix"},
    "PicoShare": {"official": "https://pico.rocks/", "git": "https://codefloe.com/mtlynch/picoshare"},
    "Plone": {"official": "https://plone.org/", "git": "https://github.com/plone/Products.CMFPlone"},
    "PocketBase": {"official": "https://pocketbase.io/", "git": "https://github.com/pocketbase/pocketbase"},
    "RabbitMQ": {"official": "https://www.rabbitmq.com/", "git": "https://github.com/rabbitmq/rabbitmq-server"},
    "Redmine": {"official": "https://www.redmine.org/", "git": "https://github.com/redmine/redmine"},
    "Resilio Sync": {"official": "https://www.resilio.com/", "git": None},
    "Rivet": {"official": "https://rivet.gg/", "git": "https://github.com/rivet-gg/rivet"},
    "Sharkey": {"official": "https://joinsharkey.org/", "git": "https://git.joinsharkey.org/Sharkey/Sharkey"},
    "Ubooquity": {"official": "https://vaemendis.net/ubooquity/", "git": None},
    "Anaconda": {"official": "https://www.anaconda.com/", "git": "https://github.com/conda/conda"},
    "Emby": {"official": "https://emby.media/", "git": None},
    "FusionAuth": {"official": "https://fusionauth.io/", "git": None},
    "Matrix Synapse": {"official": "https://element-hq.github.io/synapse/", "git": "https://github.com/element-hq/synapse"},
    "Open Journal Systems": {"official": "https://pkp.sfu.ca/software/ojs/", "git": "https://github.com/pkp/ojs"},
    "Plex": {"official": "https://www.plex.tv/", "git": None},
    "tinyMediaManager": {"official": "https://www.tinymediamanager.org/", "git": "https://gitlab.com/tinyMediaManager/tinyMediaManager"},
}


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def parse_js_template_json(s: str):
    s = s.replace("\\`", "`").replace('\\\\"', '\\"')
    return json.loads(s)


def clean_url(url: str | None) -> str | None:
    if not url or not isinstance(url, str):
        return None
    u = url.strip()
    if not u.startswith(("http://", "https://")):
        return None
    u = re.sub(r"[?&]utm_source=[^&]+", "", u).rstrip("?&")
    return u


def is_git_url(url: str | None) -> bool:
    if not url:
        return False
    low = url.lower()
    return any(
        h in low
        for h in [
            "github.com/",
            "gitlab.com/",
            "codeberg.org/",
            "git.sr.ht/",
            "gitea.",
            "bitbucket.org/",
            "sourceforge.net/projects/",
        ]
    )


def ensure_cache():
    os.makedirs(CACHE_DIR, exist_ok=True)
    urls = {
        "df.js": "https://www.hostinger.com/br/_nuxt/DFqozLpe.js",
        "cw.js": "https://www.hostinger.com/br/_nuxt/CwgNgyPT.js",
        "awesome_data.tar.gz": "https://codeload.github.com/awesome-selfhosted/awesome-selfhosted-data/tar.gz/refs/heads/master",
        "awesome_readme.md": "https://raw.githubusercontent.com/awesome-selfhosted/awesome-selfhosted/master/README.md",
        "selfhst_software.json": "https://r2.selfh.st/directory/software.json",
        "dokploy.json": "https://templates.dokploy.com/meta.json",
        "coolify.json": "https://raw.githubusercontent.com/coollabsio/coolify/v4.x/templates/service-templates-latest.json",
        "runtipi.tar.gz": "https://codeload.github.com/runtipi/runtipi-appstore/tar.gz/refs/heads/master",
        "yunohost_json": "https://app.yunohost.org/default/v3/apps.json",
        "linuxserver": "https://api.linuxserver.io/api/v1/images?include_config=false&include_deprecated=true",
        "umbrel": "https://codeload.github.com/getumbrel/umbrel-apps/tar.gz/refs/heads/master",
        "apache_projects.json": "https://projects.apache.org/json/foundation/projects.json",
        "lfx_landscape.yml": "https://raw.githubusercontent.com/cncf/landscape/master/landscape.yml",
        "awesome_docker.md": "https://raw.githubusercontent.com/veggiemonk/awesome-docker/master/README.md",
        "awesome_sysadmin.md": "https://raw.githubusercontent.com/awesome-foss/awesome-sysadmin/master/README.md",
        "portainer_lissy.json": "https://raw.githubusercontent.com/Lissy93/portainer-templates/main/templates.json",
    }
    for name, url in urls.items():
        p = os.path.join(CACHE_DIR, name)
        if not os.path.exists(p):
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                with open(p, "wb") as f:
                    f.write(resp.read())


def load_user_items() -> list[str]:
    with open(RAW_PROMPT_PATH, "r", encoding="utf-8") as f:
        text = f.read().replace("<USER_REQUEST>", "")
    instr_idx = text.find("Preciso que crie")
    if instr_idx != -1:
        text = text[:instr_idx]
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip() and line.strip().lower() != "image"
    ]
    return sorted(list(dict.fromkeys(lines)), key=lambda x: x.lower())


def load_hostinger_metadata():
    with open(os.path.join(CACHE_DIR, "df.js"), "r", encoding="utf-8") as f:
        df = f.read()
    end_idx = df.find("routes.dockerApplicationsZulip")
    end_bracket = df.find("]`)", end_idx)
    start_bracket = df.rfind("h(`[", 0, end_idx)
    apps = {
        a["name"]: a
        for a in parse_js_template_json(df[start_bracket + 3 : end_bracket + 1])
    }

    with open(os.path.join(CACHE_DIR, "cw.js"), "r", encoding="utf-8") as f:
        cw = f.read()
    t_start = cw.find("e(`{")
    t_end = cw.rfind("}`)")
    trans = parse_js_template_json(cw[t_start + 3 : t_end + 1])
    return apps, trans


def build_link_index():
    idx = {}

    def add(name, official=None, git=None, demo=None):
        if not name:
            return
        official = clean_url(official)
        git = clean_url(git)
        demo = clean_url(demo)
        if not (official or git or demo):
            return
        variants = {norm(name)}
        low = name.lower().strip()
        for prefix in ("apache ", "eclipse ", "grafana ", "percona "):
            if low.startswith(prefix):
                variants.add(norm(low[len(prefix) :]))
        for k in variants:
            if not k:
                continue
            cur = idx.setdefault(k, {})
            if official and not cur.get("official"):
                cur["official"] = official
            if git and not cur.get("git"):
                cur["git"] = git
            if demo and not cur.get("demo"):
                cur["demo"] = demo

    # 1. Awesome-Selfhosted Data (alta prioridade, possui website, source e demo)
    with tarfile.open(os.path.join(CACHE_DIR, "awesome_data.tar.gz"), "r:gz") as tf:
        for m in tf.getmembers():
            if "/software/" in m.name and m.name.endswith(".yml"):
                d = yaml.safe_load(tf.extractfile(m).read().decode("utf-8"))
                if isinstance(d, dict):
                    add(
                        d.get("name"),
                        d.get("website_url"),
                        d.get("source_code_url"),
                        d.get("demo_url"),
                    )

    # 2. Awesome-Selfhosted README
    with open(os.path.join(CACHE_DIR, "awesome_readme.md"), "r", encoding="utf-8") as f:
        rm = f.read()
    for m in re.finditer(r"^\s*-\s*\[([^\]]+)\]\((https?://[^)]+)\)\s*-\s*(.+)$", rm, re.M):
        name, url, rest = m.group(1), m.group(2), m.group(3)
        demo_m = re.search(r"\[Demo\]\((https?://[^)]+)\)", rest, re.I)
        src_m = re.search(r"\[Source Code\]\((https?://[^)]+)\)", rest, re.I)
        add(
            name,
            url,
            src_m.group(1) if src_m else (url if is_git_url(url) else None),
            demo_m.group(1) if demo_m else None,
        )

    # 3. selfh.st directory
    with open(os.path.join(CACHE_DIR, "selfhst_software.json"), "r", encoding="utf-8") as f:
        for e in json.load(f).get("entries", []):
            add(e.get("name"), e.get("website"), e.get("repository"))
            add(e.get("reference"), e.get("website"), e.get("repository"))

    # 4. Easypanel meta.yaml cache
    ep_dir = os.path.join(CACHE_DIR, "easypanel_meta")
    if os.path.isdir(ep_dir):
        for fn in os.listdir(ep_dir):
            try:
                with open(os.path.join(ep_dir, fn), "r", encoding="utf-8") as f:
                    d = yaml.safe_load(f)
                if isinstance(d, dict):
                    off, git, demo = None, None, None
                    for lnk in d.get("links") or []:
                        lbl = (lnk.get("label") or "").lower()
                        u = lnk.get("url") or ""
                        if not u:
                            continue
                        if "git" in lbl or "source" in lbl or is_git_url(u):
                            if not git:
                                git = u
                        if "demo" in lbl:
                            if not demo:
                                demo = u
                        elif any(w in lbl for w in ("website", "home", "docs", "documentation")):
                            if not off:
                                off = u
                    add(d.get("name") or fn[:-5], off or git, git, demo)
                    add(fn[:-5], off or git, git, demo)
            except Exception:
                pass

    # 5. Dokploy templates
    with open(os.path.join(CACHE_DIR, "dokploy.json"), "r", encoding="utf-8") as f:
        for d in json.load(f):
            links = d.get("links") or {}
            add(d.get("name"), links.get("website") or links.get("docs"), links.get("github"))
            add(d.get("id"), links.get("website") or links.get("docs"), links.get("github"))

    # 6. Coolify templates
    with open(os.path.join(CACHE_DIR, "coolify.json"), "r", encoding="utf-8") as f:
        for k, v in json.load(f).items():
            doc = clean_url(v.get("documentation"))
            add(k, doc, doc if is_git_url(doc) else None)

    # 7. Runtipi appstore
    with tarfile.open(os.path.join(CACHE_DIR, "runtipi.tar.gz"), "r:gz") as tf:
        for m in tf.getmembers():
            if m.name.endswith("/config.json"):
                d = json.loads(tf.extractfile(m).read().decode("utf-8"))
                add(d.get("name"), d.get("website"), d.get("source"))
                add(d.get("id"), d.get("website"), d.get("source"))

    # 8. YunoHost apps
    with open(os.path.join(CACHE_DIR, "yunohost_json"), "r", encoding="utf-8") as f:
        for k, v in json.load(f).get("apps", {}).items():
            up = v.get("manifest", {}).get("upstream", {}) or {}
            add(
                v.get("manifest", {}).get("name") or k,
                up.get("website") or up.get("code"),
                up.get("code"),
                up.get("demo"),
            )
            add(k, up.get("website") or up.get("code"), up.get("code"), up.get("demo"))

    # 9. LinuxServer.io
    with open(os.path.join(CACHE_DIR, "linuxserver"), "r", encoding="utf-8") as f:
        for img in json.load(f).get("data", {}).get("repositories", {}).get("linuxserver", []):
            pu = img.get("project_url") or ""
            add(img.get("name"), pu, pu if is_git_url(pu) else None)

    # 10. Umbrel
    with tarfile.open(os.path.join(CACHE_DIR, "umbrel"), "r:gz") as tf:
        for m in tf.getmembers():
            if m.name.endswith("umbrel-app.yml"):
                d = yaml.safe_load(tf.extractfile(m).read().decode("utf-8"))
                if isinstance(d, dict):
                    add(d.get("name"), d.get("website"), d.get("repo"))

    # 11. Apache Projects
    with open(os.path.join(CACHE_DIR, "apache_projects.json"), "r", encoding="utf-8") as f:
        for k, v in json.load(f).items():
            if isinstance(v, dict):
                hp = v.get("homepage") or (f"https://{k}.apache.org/" if v.get("name") else None)
                repo = (
                    (v.get("repository") or [None])[0]
                    if isinstance(v.get("repository"), list)
                    else v.get("repository")
                )
                if isinstance(repo, str) and not repo.startswith("http"):
                    repo = f"https://github.com/apache/{k}"
                add(v.get("name") or f"Apache {k}", hp, repo)
                add(k, hp, repo)

    # 12. CNCF Landscape
    with open(os.path.join(CACHE_DIR, "lfx_landscape.yml"), "r", encoding="utf-8") as f:
        lfx = yaml.safe_load(f)
    for cat in lfx.get("landscape") or []:
        for sub in cat.get("subcategories") or []:
            for it in sub.get("items") or []:
                add(it.get("name"), it.get("homepage_url"), it.get("repo_url"))

    # 13. Portainer templates (Lissy93)
    with open(os.path.join(CACHE_DIR, "portainer_lissy.json"), "r", encoding="utf-8") as f:
        for t in json.load(f).get("templates", []):
            desc = t.get("description") or ""
            src_m = re.search(r"Source:\s*(https?://\S+)", desc)
            if src_m:
                u = src_m.group(1).rstrip(").,")
                add(t.get("title") or t.get("name"), u, u if is_git_url(u) else None)

    # 14. Awesome Docker / Sysadmin / AI markdowns
    for md_name in ["awesome_docker.md", "awesome_sysadmin.md", "awesome_ai.md", "awesome_ai_agents2.md", "awesome_llm_apps.md"]:
        p = os.path.join(CACHE_DIR, md_name)
        if not os.path.exists(p):
            continue
        with open(p, "r", encoding="utf-8") as f:
            md = f.read()
        for m in re.finditer(r"\[([^\]]+)\]\((https?://[^)]+)\)", md):
            name, url = m.group(1), m.group(2)
            if len(name) < 55:
                add(name, url, url if is_git_url(url) else None)

    return idx


def lookup_links(name: str, idx: dict) -> dict:
    # Overrides manuais têm precedência quando completos ou preenchem lacunas
    ov = VERIFIED_OVERRIDES.get(name, {})
    keys = [norm(name)]
    low = name.lower().strip()
    for p in ("apache ", "eclipse ", "grafana ", "percona "):
        if low.startswith(p):
            keys.append(norm(low[len(p) :]))
    for s in (
        " ce",
        " server",
        " community",
        " open",
        " (chat ui)",
        " (+100 workflows)",
        " (queue mode)",
        " with ai assistant",
        " 2",
        " 4",
    ):
        if low.endswith(s):
            keys.append(norm(low[: -len(s)]))

    found = {}
    for k in keys:
        if k in idx:
            ent = idx[k]
            if ent.get("official") and not found.get("official"):
                found["official"] = ent["official"]
            if ent.get("git") and not found.get("git"):
                found["git"] = ent["git"]
            if ent.get("demo") and not found.get("demo"):
                found["demo"] = ent["demo"]

    official = ov.get("official") or found.get("official") or ov.get("git") or found.get("git")
    git = ov["git"] if "git" in ov else found.get("git")
    demo = ov.get("demo") or found.get("demo")

    # Se official aponta para um repo Git e também temos website distinto, manter como está;
    # Se git for None (e não foi explicitamente desabilitado em VERIFIED_OVERRIDES), mas official for um repo Git, refletir em git.
    if git is None and "git" not in ov and is_git_url(official):
        git = official

    return {"official": official, "git": git, "demo": demo}


def compute_market_score(svc: dict, repo_metric: dict | None) -> dict:
    has_demo = bool(svc.get("demo_url"))
    is_popular = bool(svc.get("popular"))
    off = svc.get("official_url") or ""
    git = svc.get("git_url") or ""
    has_own_site = bool(off and off != git and not is_git_url(off))

    ecosystem_score = (4 if has_demo else 0) + (4 if is_popular else 0) + (2 if has_own_site else 0)

    if not repo_metric or repo_metric.get("stars") is None:
        # Projeto proprietário/comercial ou sem métricas Git públicas
        is_prop = not git
        pop_score = 26 if is_popular else (20 if is_prop else 16)
        act_score = 24 if is_prop else 14
        comm_score = 8 if is_popular else 6
        total = max(5, min(100, pop_score + act_score + comm_score + ecosystem_score))
        rating = round(1.0 + (total / 100.0) * 4.0, 1)
        rec = "recommended" if total >= 68 else ("niche" if total >= 48 else "caution")
        rec_labels = {
            "leader": "Líder de Mercado",
            "recommended": "Recomendado",
            "niche": "Nicho / Emergente",
            "caution": "Obsoleto / Baixa Atividade",
        }
        return {
            "stars": None,
            "forks": None,
            "last_commit": None,
            "days_since_commit": None,
            "trending": 0,
            "archived": False,
            "activity_status": "proprietary" if is_prop else "moderate",
            "activity_label": "Código Fechado / Comercial" if is_prop else "Sem telemetria Git",
            "score": total,
            "rating": rating,
            "recommendation": rec,
            "recommendation_label": rec_labels[rec],
            "score_breakdown": {
                "popularity": pop_score,
                "activity": act_score,
                "community": comm_score,
                "ecosystem": ecosystem_score,
                "penalty": 0,
            },
            "score_summary": (
                "Solução comercial/proprietária sem repositório Git público; pontuação estimada pela presença de mercado e ecossistema."
                if is_prop
                else "Repositório sem telemetria pública direta; pontuação baseada em adoção e documentação."
            ),
        }

    stars = int(repo_metric.get("stars") or 0)
    forks = int(repo_metric.get("forks") or 0)
    trending = int(repo_metric.get("trending") or 0)
    archived = bool(repo_metric.get("archived", False))
    last_commit = repo_metric.get("last_commit")

    days_since = None
    if last_commit:
        try:
            dt = datetime.strptime(last_commit[:10], "%Y-%m-%d")
            days_since = max(0, (REFERENCE_DATE - dt).days)
        except ValueError:
            days_since = None

    popularity_score = min(40, round(8.5 * math.log10(stars + 1)))

    penalty = 0
    if archived:
        activity_score = 0
        penalty = 25
        activity_status = "stale"
        activity_label = "Arquivado / Obsoleto"
    elif days_since is None:
        activity_score = 18
        activity_status = "moderate"
        activity_label = "Sem data recente"
    elif days_since <= 14:
        activity_score = 35
        activity_status = "active"
        activity_label = "Muito Ativo"
    elif days_since <= 60:
        activity_score = 31
        activity_status = "active"
        activity_label = "Ativo"
    elif days_since <= 180:
        activity_score = 24
        activity_status = "active"
        activity_label = "Regular"
    elif days_since <= 365:
        activity_score = 14
        activity_status = "moderate"
        activity_label = "Baixa Atividade"
    elif days_since <= 730:
        activity_score = 5
        penalty = 10
        activity_status = "stale"
        activity_label = "Inativo (>1 ano)"
    else:
        activity_score = 0
        penalty = 20
        activity_status = "stale"
        activity_label = "Obsoleto (>2 anos)"

    trend_bonus = min(3, round(trending / 120)) if trending > 0 else 0
    community_score = min(15, min(12, round(3.5 * math.log10(forks + 1))) + trend_bonus)

    raw_score = popularity_score + activity_score + community_score + ecosystem_score - penalty
    total = max(5, min(100, raw_score))
    rating = round(1.0 + (total / 100.0) * 4.0, 1)

    if activity_status == "stale" or total < 48:
        rec = "caution"
    elif total >= 82 and activity_status == "active":
        rec = "leader"
    elif total >= 68:
        rec = "recommended"
    else:
        rec = "niche"

    rec_labels = {
        "leader": "Líder de Mercado",
        "recommended": "Recomendado",
        "niche": "Nicho / Emergente",
        "caution": "Obsoleto / Baixa Atividade",
    }

    if archived:
        summary = f"Repositório arquivado ({stars:,} ★). Projeto descontinuado; avalie alternativas ativas."
    elif activity_status == "stale":
        summary = f"Sem atualizações há {days_since} dias ({stars:,} ★). Atenção ao risco de obsolescência e falta de PRs recentes."
    elif rec == "leader":
        summary = f"Alta aceitação no mercado ({stars:,} ★, {forks:,} forks) e desenvolvimento muito ativo (último commit há {days_since if days_since is not None else '?'}d)."
    elif rec == "recommended":
        summary = f"Boa adoção comunitária ({stars:,} ★) com manutenção consistente e ecossistema confiável."
    else:
        summary = f"Projeto de nicho ou em crescimento ({stars:,} ★), com atividade recente ({activity_label.lower()})."

    return {
        "stars": stars,
        "forks": forks,
        "last_commit": last_commit,
        "days_since_commit": days_since,
        "trending": trending,
        "archived": archived,
        "activity_status": activity_status,
        "activity_label": activity_label,
        "score": total,
        "rating": rating,
        "recommendation": rec,
        "recommendation_label": rec_labels[rec],
        "score_breakdown": {
            "popularity": popularity_score,
            "activity": activity_score,
            "community": community_score,
            "ecosystem": ecosystem_score,
            "penalty": penalty,
        },
        "score_summary": summary,
    }


def build():
    ensure_cache()
    items = load_user_items()
    hostinger_apps, trans = load_hostinger_metadata()
    link_idx = build_link_index()

    repo_metrics = {}
    if os.path.exists(METRICS_RESOLVED_PATH):
        with open(METRICS_RESOLVED_PATH, "r", encoding="utf-8") as f:
            repo_metrics = json.load(f)

    services = []
    missing_official = []

    for name in items:
        h_app = hostinger_apps.get(name)
        curated = CURATED_NON_DOCKER.get(name)

        if h_app:
            cat_key = h_app.get("category", "other")
            if cat_key not in CATEGORIES:
                cat_key = "other"
            desc = (trans.get(h_app.get("shortDescription")) or "").strip()
            if desc and not desc.endswith("."):
                desc += "."
            links = lookup_links(name, link_idx)
            img_id = h_app.get("imageId") or ""
            icon_url = (
                f"https://www.hostinger.com/cdn-cgi/imagedelivery/LqiWLm-3MGbYHtFuUbcBtA/{img_id}/public"
                if img_id
                else None
            )
            features = [
                trans[f["title"]]
                for f in (h_app.get("lpFeatures") or [])
                if f.get("title") and trans.get(f["title"])
            ]
            popular = bool(h_app.get("isRecommended") or h_app.get("isLpPopular"))
        elif curated:
            cat_key = curated["category"]
            desc = curated["description"]
            # Também aproveitar demo ou git do índice se não definido no curado
            auto_links = lookup_links(name, link_idx)
            links = {
                "official": curated.get("official") or auto_links.get("official"),
                "git": curated.get("git") or auto_links.get("git"),
                "demo": curated.get("demo") or auto_links.get("demo"),
            }
            icon_url = None
            features = []
            popular = name in {
                "Docker",
                "Portainer",
                "PostHog",
                "Chatwoot",
                "Discourse",
                "WooCommerce",
                "Claude Code",
                "OpenAI Codex",
                "Gemini CLI",
            }
        else:
            raise ValueError(f"Item não mapeado nem em Docker nem em CURATED_NON_DOCKER: {name}")

        if not links["official"]:
            missing_official.append(name)

        cat_label = CATEGORIES[cat_key]["label"]
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        svc_base = {
            "id": slug,
            "name": name,
            "category": cat_key,
            "category_label": cat_label,
            "description": desc,
            "official_url": links["official"],
            "git_url": links["git"],
            "demo_url": links["demo"],
            "icon_url": icon_url,
            "features": features[:4],
            "popular": popular,
        }
        evaluation = compute_market_score(svc_base, repo_metrics.get(name) if svc_base["git_url"] else None)
        svc_base.update(evaluation)
        services.append(svc_base)

    if missing_official:
        print(f"AVISO: {len(missing_official)} serviços sem URL oficial:", missing_official)

    # Agrupar por categoria mantendo ordem curada e ordem alfabética dos serviços
    grouped = defaultdict(list)
    for svc in services:
        grouped[svc["category"]].append(svc)

    ordered_categories = []
    for cat_key, meta in sorted(CATEGORIES.items(), key=lambda kv: kv[1]["order"]):
        cat_services = sorted(grouped.get(cat_key, []), key=lambda s: s["name"].lower())
        if not cat_services:
            continue
        ordered_categories.append(
            {
                "id": cat_key,
                "label": meta["label"],
                "count": len(cat_services),
                "services": cat_services,
            }
        )

    stats = {
        "total_services": len(services),
        "total_categories": len(ordered_categories),
        "with_official_url": sum(1 for s in services if s["official_url"]),
        "with_git_url": sum(1 for s in services if s["git_url"]),
        "with_demo_url": sum(1 for s in services if s["demo_url"]),
        "popular_count": sum(1 for s in services if s["popular"]),
        "leader_count": sum(1 for s in services if s["recommendation"] == "leader"),
        "recommended_count": sum(1 for s in services if s["recommendation"] == "recommended"),
        "niche_count": sum(1 for s in services if s["recommendation"] == "niche"),
        "caution_count": sum(1 for s in services if s["recommendation"] == "caution"),
        "active_count": sum(1 for s in services if s["activity_status"] == "active"),
        "stale_count": sum(1 for s in services if s["activity_status"] == "stale"),
        "stars_10k_count": sum(1 for s in services if (s.get("stars") or 0) >= 10000),
        "with_repo_metrics": sum(1 for s in services if s.get("stars") is not None),
    }

    catalog = {
        "title": "Catálogo de Serviços Open-Source & Self-Hosted",
        "stats": stats,
        "categories": ordered_categories,
    }

    # 1. JSON
    json_path = os.path.join(ROOT_DIR, "catalogo-servicos.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

    # 2. JS bundle para funcionamento offline (file://) sem CORS
    js_path = os.path.join(ROOT_DIR, "data.js")
    with open(js_path, "w", encoding="utf-8") as f:
        f.write("window.CATALOG_DATA = ")
        json.dump(catalog, f, ensure_ascii=False)
        f.write(";\n")

    # 3. Markdown completo agrupado por categoria
    md_lines = [
        "# Catálogo Completo de Serviços Open-Source & Self-Hosted",
        "",
        f"Catálogo estruturado com **{stats['total_services']} serviços** distribuídos em **{stats['total_categories']} categorias**, com descrição breve em português, página oficial, repositório Git e link de demonstração (quando disponível).",
        "",
        "## Resumo",
        f"- **Total de serviços:** {stats['total_services']}",
        f"- **Categorias:** {stats['total_categories']}",
        f"- **Com Página Oficial:** {stats['with_official_url']}",
        f"- **Com Repositório Git:** {stats['with_git_url']}",
        f"- **Com Demonstração (Demo):** {stats['with_demo_url']}",
        "",
        "## Índice por Categoria",
        "",
    ]

    for cat in ordered_categories:
        anchor = re.sub(r"[^a-z0-9]+", "-", cat["label"].lower()).strip("-")
        md_lines.append(f"- [{cat['label']}](#{anchor}) ({cat['count']})")
    md_lines.append("")

    for cat in ordered_categories:
        md_lines.append(f"## {cat['label']}")
        md_lines.append("")
        md_lines.append("| Serviço | Score & Recomendação | Estrelas / Atividade | Descrição | Links |")
        md_lines.append("| :--- | :--- | :--- | :--- | :--- |")
        for svc in cat["services"]:
            safe_desc = svc["description"].replace("|", "\\|").replace("\n", " ")
            link_parts = []
            if svc["official_url"]:
                link_parts.append(f"[Site Oficial]({svc['official_url']})")
            if svc["git_url"]:
                link_parts.append(f"[Git]({svc['git_url']})")
            if svc["demo_url"]:
                link_parts.append(f"[Demo]({svc['demo_url']})")
            links_str = " · ".join(link_parts) if link_parts else "—"
            stars_str = f"★ {svc['stars']:,}" if svc.get("stars") is not None else "—"
            act_str = f"{stars_str} · {svc['activity_label']}"
            score_str = f"**{svc['score']}/100** ({svc['rating']}★) · {svc['recommendation_label']}"
            md_lines.append(f"| **{svc['name']}** | {score_str} | {act_str} | {safe_desc} | {links_str} |")
        md_lines.append("")

    md_content = "\n".join(md_lines)
    with open(os.path.join(ROOT_DIR, "CATALOGO.md"), "w", encoding="utf-8") as f:
        f.write(md_content)

    # 4. Preservar README.md personalizado caso já exista
    readme_path = os.path.join(ROOT_DIR, "README.md")
    if not os.path.exists(readme_path):
        readme_lines = [
            "# OpenSource Catalog",
            "",
            f"Catálogo com **{stats['total_services']} serviços e stacks open-source / self-hosted** agrupados em **{stats['total_categories']} categorias**.",
        ]
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write("\n".join(readme_lines) + "\n")

    print("Catálogo gerado com sucesso!")
    print("Estatísticas:", json.dumps(stats, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    build()
