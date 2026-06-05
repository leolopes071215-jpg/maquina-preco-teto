# api_scaffold_valoris.py

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

import streamlit as st

from api_contratos_valoris import (
    ENDPOINTS_API_VALORIS,
    SCHEMAS_API_VALORIS,
    calcular_prontidao_api,
    gerar_openapi_rascunho,
)
from postgres_supabase_valoris import calcular_prontidao_postgres
from repositorios_valoris import calcular_saude_repositorios


VERSAO_API_SCAFFOLD_VALORIS = "3.8.62"

PASTA_API_SCAFFOLD = Path("api_valoris")
CAMINHO_DECISOES_API_SCAFFOLD = Path("decisoes_api_scaffold_valoris.csv")
CAMINHO_MANIFESTO_API_SCAFFOLD = Path("manifesto_api_scaffold_valoris.json")

CAMPOS_DECISAO_API_SCAFFOLD = [
    "id",
    "data_registro",
    "score_scaffold",
    "score_api",
    "score_repositorio",
    "score_postgres",
    "arquivos_planejados",
    "decisao",
    "proximo_passo",
    "observacoes",
]

ARQUIVOS_SCAFFOLD = [
    "api_valoris/README.md",
    "api_valoris/requirements_api.txt",
    "api_valoris/.env.example",
    "api_valoris/app/__init__.py",
    "api_valoris/app/main.py",
    "api_valoris/app/core/__init__.py",
    "api_valoris/app/core/config.py",
    "api_valoris/app/schemas/__init__.py",
    "api_valoris/app/schemas/lead.py",
    "api_valoris/app/schemas/event.py",
    "api_valoris/app/schemas/health.py",
    "api_valoris/app/routes/__init__.py",
    "api_valoris/app/routes/health.py",
    "api_valoris/app/routes/events.py",
    "api_valoris/app/routes/leads.py",
    "api_valoris/app/services/__init__.py",
    "api_valoris/app/services/repository_bridge.py",
]

REQUIREMENTS_API = 'fastapi>=0.115.0\nuvicorn[standard]>=0.30.0\npydantic>=2.7.0\npython-dotenv>=1.0.1'
ENV_EXAMPLE_API = '# .env.example — API Valoris\n# Copie para .env se for rodar a API localmente.\n# Nunca suba .env real para o Git.\n\nVALORIS_API_ENV="local"\nVALORIS_API_TITLE="Valoris API"\nVALORIS_API_VERSION="0.1.0"\nVALORIS_DATABASE_URL=""\nSUPABASE_URL=""\nSUPABASE_SERVICE_ROLE_KEY=""'
README_API = '# Valoris API — Scaffold Local\n\nEste diretório é um laboratório inicial para separar o backend da Valoris da interface Streamlit.\n\n## Objetivo\n\nComeçar com endpoints simples:\n\n- `GET /health`\n- `POST /events`\n- `POST /leads`\n- `GET /leads`\n\nDepois evoluir para valuation, relatórios, autenticação, pagamentos e PostgreSQL/Supabase.\n\n## Instalação local\n\n```powershell\ncd api_valoris\npython -m venv .venv\n.\\.venv\\Scripts\\Activate.ps1\npip install -r requirements_api.txt\nuvicorn app.main:app --reload --port 8000\n```\n\n## Aviso\n\nEste scaffold não substitui o app Streamlit. Ele é um backend paralelo para testes controlados.'
MAIN_PY = 'from fastapi import FastAPI\n\nfrom app.routes.health import router as health_router\nfrom app.routes.events import router as events_router\nfrom app.routes.leads import router as leads_router\n\n\napp = FastAPI(\n    title="Valoris API",\n    version="0.1.0",\n    description="Backend experimental da Valoris. Não substitui o Streamlit ainda.",\n)\n\napp.include_router(health_router, tags=["system"])\napp.include_router(events_router, prefix="/events", tags=["events"])\napp.include_router(leads_router, prefix="/leads", tags=["leads"])\n\n\n@app.get("/")\ndef root():\n    return {\n        "service": "valoris-api",\n        "status": "online",\n        "message": "Backend experimental da Valoris.",\n    }'
CONFIG_PY = 'from pydantic import BaseModel\nimport os\n\n\nclass Settings(BaseModel):\n    api_env: str = os.getenv("VALORIS_API_ENV", "local")\n    api_title: str = os.getenv("VALORIS_API_TITLE", "Valoris API")\n    api_version: str = os.getenv("VALORIS_API_VERSION", "0.1.0")\n    database_url: str = os.getenv("VALORIS_DATABASE_URL", "")\n\n\nsettings = Settings()'
SCHEMA_HEALTH_PY = 'from pydantic import BaseModel\n\n\nclass HealthResponse(BaseModel):\n    status: str\n    service: str\n    version: str'
SCHEMA_EVENT_PY = 'from pydantic import BaseModel\nfrom typing import Optional\n\n\nclass EventCreate(BaseModel):\n    sessao_id: Optional[str] = None\n    evento: str\n    origem: Optional[str] = None\n    contexto: Optional[str] = None\n    perfil: Optional[str] = None\n    valor: Optional[str] = None\n    detalhe: Optional[str] = None\n\n\nclass EventResponse(BaseModel):\n    ok: bool\n    message: str\n    event: EventCreate'
SCHEMA_LEAD_PY = 'from pydantic import BaseModel\nfrom typing import Optional\n\n\nclass LeadCreate(BaseModel):\n    nome: str\n    contato: str\n    perfil: Optional[str] = None\n    principal_dor: Optional[str] = None\n    plano_interesse: Optional[str] = None\n    preco_aceitavel: Optional[str] = None\n    pagaria_agora: Optional[str] = None\n    comentario: Optional[str] = None\n\n\nclass LeadResponse(BaseModel):\n    ok: bool\n    message: str\n    lead: LeadCreate'
ROUTE_HEALTH_PY = 'from fastapi import APIRouter\n\nfrom app.schemas.health import HealthResponse\n\n\nrouter = APIRouter()\n\n\n@router.get("/health", response_model=HealthResponse)\ndef health():\n    return HealthResponse(\n        status="ok",\n        service="valoris-api",\n        version="0.1.0",\n    )'
ROUTE_EVENTS_PY = 'from fastapi import APIRouter\n\nfrom app.schemas.event import EventCreate, EventResponse\n\n\nrouter = APIRouter()\n\n\n@router.post("", response_model=EventResponse)\ndef create_event(payload: EventCreate):\n    return EventResponse(\n        ok=True,\n        message="Evento recebido no scaffold da API.",\n        event=payload,\n    )'
ROUTE_LEADS_PY = 'from fastapi import APIRouter\n\nfrom app.schemas.lead import LeadCreate, LeadResponse\n\n\nrouter = APIRouter()\n\n\n_LEADS_MEMORIA: list[LeadCreate] = []\n\n\n@router.post("", response_model=LeadResponse)\ndef create_lead(payload: LeadCreate):\n    _LEADS_MEMORIA.append(payload)\n\n    return LeadResponse(\n        ok=True,\n        message="Lead recebido no scaffold da API.",\n        lead=payload,\n    )\n\n\n@router.get("")\ndef list_leads():\n    return {\n        "ok": True,\n        "total": len(_LEADS_MEMORIA),\n        "leads": _LEADS_MEMORIA,\n    }'
REPOSITORY_BRIDGE_PY = 'class RepositoryBridge:\n    """Ponte futura entre FastAPI e a camada de repositórios da Valoris."""\n\n    def __init__(self, adapter: str = "sqlite"):\n        self.adapter = adapter\n\n    def create_event(self, payload: dict) -> dict:\n        return {\n            "ok": True,\n            "adapter": self.adapter,\n            "payload": payload,\n        }\n\n    def create_lead(self, payload: dict) -> dict:\n        return {\n            "ok": True,\n            "adapter": self.adapter,\n            "payload": payload,\n        }'

ARQUIVOS_CONTEUDO_SCAFFOLD = {
    "api_valoris/README.md": README_API,
    "api_valoris/requirements_api.txt": REQUIREMENTS_API,
    "api_valoris/.env.example": ENV_EXAMPLE_API,
    "api_valoris/app/__init__.py": "",
    "api_valoris/app/main.py": MAIN_PY,
    "api_valoris/app/core/__init__.py": "",
    "api_valoris/app/core/config.py": CONFIG_PY,
    "api_valoris/app/schemas/__init__.py": "",
    "api_valoris/app/schemas/lead.py": SCHEMA_LEAD_PY,
    "api_valoris/app/schemas/event.py": SCHEMA_EVENT_PY,
    "api_valoris/app/schemas/health.py": SCHEMA_HEALTH_PY,
    "api_valoris/app/routes/__init__.py": "",
    "api_valoris/app/routes/health.py": ROUTE_HEALTH_PY,
    "api_valoris/app/routes/events.py": ROUTE_EVENTS_PY,
    "api_valoris/app/routes/leads.py": ROUTE_LEADS_PY,
    "api_valoris/app/services/__init__.py": "",
    "api_valoris/app/services/repository_bridge.py": REPOSITORY_BRIDGE_PY,
}


def _limpar_texto(valor: Any) -> str:
    if valor is None:
        return ""
    return str(valor).strip()


def _garantir_csv(caminho: Path, campos: List[str]) -> None:
    if caminho.exists():
        return

    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()


def carregar_decisoes_api_scaffold() -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_DECISOES_API_SCAFFOLD, CAMPOS_DECISAO_API_SCAFFOLD)
    with CAMINHO_DECISOES_API_SCAFFOLD.open("r", newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def gerar_csv_decisoes_api_scaffold() -> str:
    _garantir_csv(CAMINHO_DECISOES_API_SCAFFOLD, CAMPOS_DECISAO_API_SCAFFOLD)
    return CAMINHO_DECISOES_API_SCAFFOLD.read_text(encoding="utf-8")


def salvar_decisao_api_scaffold(decisao: Dict[str, Any]) -> Dict[str, str]:
    _garantir_csv(CAMINHO_DECISOES_API_SCAFFOLD, CAMPOS_DECISAO_API_SCAFFOLD)

    registro = {
        "id": str(uuid4())[:8],
        "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score_scaffold": str(decisao.get("score_scaffold", "")),
        "score_api": str(decisao.get("score_api", "")),
        "score_repositorio": str(decisao.get("score_repositorio", "")),
        "score_postgres": str(decisao.get("score_postgres", "")),
        "arquivos_planejados": str(decisao.get("arquivos_planejados", "")),
        "decisao": _limpar_texto(decisao.get("decisao", "")),
        "proximo_passo": _limpar_texto(decisao.get("proximo_passo", "")),
        "observacoes": _limpar_texto(decisao.get("observacoes", "")),
    }

    with CAMINHO_DECISOES_API_SCAFFOLD.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISAO_API_SCAFFOLD)
        escritor.writerow(registro)

    return registro


def calcular_prontidao_scaffold_api() -> Dict[str, Any]:
    try:
        prontidao_api = calcular_prontidao_api()
    except Exception:
        prontidao_api = {"score_api": 0}

    try:
        saude_repositorios = calcular_saude_repositorios()
    except Exception:
        saude_repositorios = {"score_repositorio": 0}

    try:
        prontidao_postgres = calcular_prontidao_postgres()
    except Exception:
        prontidao_postgres = {"score_prontidao": 0}

    score_api = int(prontidao_api.get("score_api", 0) or 0)
    score_repositorio = int(saude_repositorios.get("score_repositorio", 0) or 0)
    score_postgres = int(prontidao_postgres.get("score_prontidao", 0) or 0)

    arquivos_existentes = len([caminho for caminho in ARQUIVOS_SCAFFOLD if Path(caminho).exists()])

    score = 15
    score += min(score_api * 0.30, 30)
    score += min(score_repositorio * 0.22, 22)
    score += min(score_postgres * 0.12, 12)
    score += min(len(ARQUIVOS_SCAFFOLD) * 1.2, 18)
    score += min(arquivos_existentes * 2, 18)
    score = int(round(max(0, min(100, score))))

    if score >= 82:
        decisao = "Scaffold pronto para execução local"
        proximo_passo = "Rodar a API localmente em porta 8000 e testar /health, /events e /leads."
    elif score >= 65:
        decisao = "Pode gerar scaffold com segurança"
        proximo_passo = "Gerar a pasta api_valoris e testar sem conectar ao app principal."
    elif score >= 45:
        decisao = "Scaffold útil, mas backend ainda prematuro"
        proximo_passo = "Gerar arquivos como laboratório, sem instalar dependências obrigatórias no projeto principal."
    else:
        decisao = "Ainda cedo para scaffold executável"
        proximo_passo = "Fortalecer contratos, repositórios e SQLite antes de executar API."

    return {
        "score_scaffold": score,
        "score_api": score_api,
        "score_repositorio": score_repositorio,
        "score_postgres": score_postgres,
        "arquivos_planejados": len(ARQUIVOS_SCAFFOLD),
        "arquivos_existentes": arquivos_existentes,
        "decisao": decisao,
        "proximo_passo": proximo_passo,
    }


def gerar_scaffold_fastapi() -> Dict[str, Any]:
    criados = []

    for caminho_texto, conteudo in ARQUIVOS_CONTEUDO_SCAFFOLD.items():
        caminho = Path(caminho_texto)
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_text(conteudo + ("\n" if conteudo else ""), encoding="utf-8")
        criados.append(caminho_texto)

    openapi = gerar_openapi_rascunho()

    manifesto = {
        "versao": VERSAO_API_SCAFFOLD_VALORIS,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "pasta": str(PASTA_API_SCAFFOLD),
        "arquivos": criados,
        "endpoints_contratados": [f"{item['metodo']} {item['rota']}" for item in ENDPOINTS_API_VALORIS],
        "schemas": list(SCHEMAS_API_VALORIS.keys()),
        "openapi_paths": list(openapi["paths"].keys()),
    }

    CAMINHO_MANIFESTO_API_SCAFFOLD.write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return manifesto


def gerar_manifesto_api_scaffold() -> Dict[str, Any]:
    prontidao = calcular_prontidao_scaffold_api()

    manifesto = {
        "versao": VERSAO_API_SCAFFOLD_VALORIS,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "prontidao": prontidao,
        "arquivos_planejados": ARQUIVOS_SCAFFOLD,
        "endpoints_prioritarios": [
            "GET /health",
            "POST /events",
            "POST /leads",
            "GET /leads",
        ],
    }

    CAMINHO_MANIFESTO_API_SCAFFOLD.write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return manifesto


def _gerar_markdown_scaffold(prontidao: Dict[str, Any]) -> str:
    arquivos = "\n".join([f"- `{item}`" for item in ARQUIVOS_SCAFFOLD])
    endpoints = "\n".join([f"- `{item['metodo']} {item['rota']}` — {item['descricao']}" for item in ENDPOINTS_API_VALORIS[:4]])

    return f"""# Scaffold FastAPI Local — Valoris

Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Diagnóstico

Score Scaffold: {prontidao["score_scaffold"]}/100  
Decisão: {prontidao["decisao"]}  
Próximo passo: {prontidao["proximo_passo"]}

Score API: {prontidao["score_api"]}/100  
Score Repositório: {prontidao["score_repositorio"]}/100  
Score PostgreSQL: {prontidao["score_postgres"]}/100  

Arquivos planejados: {prontidao["arquivos_planejados"]}  
Arquivos existentes: {prontidao["arquivos_existentes"]}  

## Endpoints iniciais

{endpoints}

## Arquivos do scaffold

{arquivos}

## Comandos locais

```powershell
cd api_valoris
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -r requirements_api.txt
uvicorn app.main:app --reload --port 8000
```

Depois abra:
`http://127.0.0.1:8000/health` e `http://127.0.0.1:8000/docs`

## Regra

O scaffold FastAPI é paralelo. Ele não substitui o Streamlit agora.
"""


def _injetar_css_scaffold() -> None:
    st.markdown(
        """
        <style>
            .scaf-hero {
                padding: clamp(1.18rem, 3vw, 2rem);
                border-radius: 30px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    radial-gradient(circle at top left, rgba(214, 181, 109, 0.26), transparent 30%),
                    radial-gradient(circle at bottom right, rgba(36, 128, 91, 0.22), transparent 34%),
                    linear-gradient(135deg, rgba(8, 15, 27, 0.99), rgba(5, 9, 18, 0.99));
                box-shadow: 0 18px 58px rgba(0, 0, 0, 0.31);
                margin-bottom: 1rem;
            }

            .scaf-eyebrow {
                color: #d6b56d;
                font-size: 0.74rem;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                font-weight: 880;
                margin-bottom: 0.35rem;
            }

            .scaf-title {
                color: #f4f7fb;
                font-size: clamp(1.75rem, 5.4vw, 3.1rem);
                font-weight: 950;
                line-height: 1.02;
                letter-spacing: -0.058em;
                margin-bottom: 0.55rem;
            }

            .scaf-subtitle {
                color: rgba(244, 247, 251, 0.75);
                font-size: clamp(0.94rem, 2.2vw, 1.06rem);
                line-height: 1.56;
                max-width: 1020px;
            }

            .scaf-note {
                padding: 0.92rem 0.98rem;
                border-radius: 17px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.90rem;
                line-height: 1.55;
                margin: 0.85rem 0;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _renderizar_hero() -> None:
    st.markdown(
        f"""
        <div class="scaf-hero">
            <div class="scaf-eyebrow">Valoris • FastAPI Scaffold • v{VERSAO_API_SCAFFOLD_VALORIS}</div>
            <div class="scaf-title">Crie a API como laboratório paralelo.</div>
            <div class="scaf-subtitle">
                Esta etapa gera uma estrutura FastAPI inicial para health, events e leads,
                sem substituir o Streamlit nem conectar banco externo automaticamente.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _renderizar_metricas(prontidao: Dict[str, Any]) -> None:
    st.markdown("### Diagnóstico do scaffold")
    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Score Scaffold", f"{prontidao['score_scaffold']}/100")
    with col_2:
        st.metric("Arquivos planejados", prontidao["arquivos_planejados"])
    with col_3:
        st.metric("Arquivos existentes", prontidao["arquivos_existentes"])
    with col_4:
        st.metric("Score API", f"{prontidao['score_api']}/100")

    st.progress(prontidao["score_scaffold"] / 100)

    if prontidao["score_scaffold"] >= 70:
        st.success(f"**{prontidao['decisao']}** — {prontidao['proximo_passo']}")
    elif prontidao["score_scaffold"] >= 45:
        st.warning(f"**{prontidao['decisao']}** — {prontidao['proximo_passo']}")
    else:
        st.info(f"**{prontidao['decisao']}** — {prontidao['proximo_passo']}")


def _renderizar_arquivos() -> None:
    st.markdown("### Arquivos planejados")

    for caminho in ARQUIVOS_SCAFFOLD:
        existe = Path(caminho).exists()
        with st.container(border=True):
            st.markdown(f"**{caminho}**")
            st.caption("Criado" if existe else "Ainda não criado")


def _renderizar_comandos() -> None:
    st.markdown("### Comandos para rodar a API depois de gerar")
    st.code(
        """cd api_valoris
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -r requirements_api.txt
uvicorn app.main:app --reload --port 8000""",
        language="powershell",
    )
    st.info("Depois abra: http://127.0.0.1:8000/health e http://127.0.0.1:8000/docs")


def _renderizar_historico() -> None:
    historico = carregar_decisoes_api_scaffold()
    st.markdown("### Histórico de decisões Scaffold API")

    if not historico:
        st.info("Ainda não há decisões salvas.")
        return

    for item in reversed(historico[-10:]):
        with st.container(border=True):
            st.markdown(f"**{item.get('decisao', 'N/D')}**")
            st.caption(item.get("data_registro", "N/D"))
            st.markdown(f"Score: {item.get('score_scaffold', 'N/D')}/100")
            st.markdown(f"Próximo passo: {item.get('proximo_passo', 'N/D')}")


def renderizar_api_scaffold_valoris() -> None:
    _injetar_css_scaffold()
    _renderizar_hero()

    prontidao = calcular_prontidao_scaffold_api()
    _renderizar_metricas(prontidao)
    st.divider()

    col_1, col_2, col_3 = st.columns(3)

    with col_1:
        if st.button("Gerar scaffold FastAPI", key="gerar_scaffold_fastapi_valoris"):
            manifesto = gerar_scaffold_fastapi()
            st.success(f"Scaffold gerado em: {PASTA_API_SCAFFOLD}")
            st.json({"versao": manifesto["versao"], "arquivos": len(manifesto["arquivos"]), "pasta": manifesto["pasta"]})
            st.rerun()

    with col_2:
        if st.button("Gerar manifesto Scaffold", key="gerar_manifesto_scaffold_valoris"):
            manifesto = gerar_manifesto_api_scaffold()
            st.success(f"Manifesto gerado: {CAMINHO_MANIFESTO_API_SCAFFOLD}")
            st.json({"versao": manifesto["versao"], "score": manifesto["prontidao"]["score_scaffold"]})

    with col_3:
        if st.button("Salvar decisão Scaffold", key="salvar_decisao_scaffold_valoris"):
            registro = salvar_decisao_api_scaffold(
                {
                    "score_scaffold": prontidao["score_scaffold"],
                    "score_api": prontidao["score_api"],
                    "score_repositorio": prontidao["score_repositorio"],
                    "score_postgres": prontidao["score_postgres"],
                    "arquivos_planejados": prontidao["arquivos_planejados"],
                    "decisao": prontidao["decisao"],
                    "proximo_passo": prontidao["proximo_passo"],
                    "observacoes": "Decisão gerada pelo scaffold FastAPI.",
                }
            )
            st.success(f"Decisão salva: {registro['decisao']}")
            st.rerun()

    st.download_button(
        "Baixar diagnóstico Scaffold API (.md)",
        data=_gerar_markdown_scaffold(prontidao),
        file_name="api_scaffold_valoris.md",
        mime="text/markdown",
        key="download_api_scaffold_valoris",
    )

    st.download_button(
        "Baixar decisões Scaffold API (.csv)",
        data=gerar_csv_decisoes_api_scaffold(),
        file_name="decisoes_api_scaffold_valoris.csv",
        mime="text/csv",
        key="download_decisoes_api_scaffold_valoris",
    )

    st.divider()
    _renderizar_arquivos()
    st.divider()
    _renderizar_comandos()
    st.divider()
    _renderizar_historico()

    st.markdown(
        """
        <div class="scaf-note">
            <strong>Regra do scaffold:</strong> ele é laboratório de backend. Não troque a Valoris para API
            antes de health, events e leads funcionarem com segurança.
        </div>
        """,
        unsafe_allow_html=True,
    )


def executar_autoteste_api_scaffold_valoris() -> List[Dict[str, str]]:
    prontidao = calcular_prontidao_scaffold_api()

    return [
        {
            "teste": "versao_scaffold",
            "status": "OK" if VERSAO_API_SCAFFOLD_VALORIS == "3.8.62" else "FALHA",
            "detalhe": VERSAO_API_SCAFFOLD_VALORIS,
        },
        {
            "teste": "arquivos_planejados",
            "status": "OK" if len(ARQUIVOS_SCAFFOLD) >= 10 else "FALHA",
            "detalhe": str(len(ARQUIVOS_SCAFFOLD)),
        },
        {
            "teste": "score_scaffold",
            "status": "OK" if 0 <= prontidao["score_scaffold"] <= 100 else "FALHA",
            "detalhe": str(prontidao["score_scaffold"]),
        },
        {
            "teste": "main_py",
            "status": "OK" if "FastAPI" in MAIN_PY else "FALHA",
            "detalhe": "main.py planejado.",
        },
    ]
