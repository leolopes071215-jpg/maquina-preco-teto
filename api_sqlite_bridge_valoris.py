# api_sqlite_bridge_valoris.py

from __future__ import annotations

import csv
import json
import py_compile
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

import streamlit as st

from api_endpoint_tests_valoris import calcular_saude_api_endpoint_tests
from api_repository_bridge_valoris import calcular_saude_api_bridge
from api_smoke_tests_valoris import PASTA_API_SCAFFOLD, testar_health_api


VERSAO_API_SQLITE_BRIDGE_VALORIS = "3.8.66"

CAMINHO_DECISOES_API_SQLITE = Path("decisoes_api_sqlite_valoris.csv")
CAMINHO_MANIFESTO_API_SQLITE = Path("manifesto_api_sqlite_valoris.json")
CAMINHO_SQLITE_API = Path("valoris_api_local.sqlite3")

CAMINHO_REPOSITORY_BRIDGE = Path("api_valoris/app/services/repository_bridge.py")
CAMINHO_ROUTES_LEADS = Path("api_valoris/app/routes/leads.py")
CAMINHO_ROUTES_EVENTS = Path("api_valoris/app/routes/events.py")
CAMINHO_README_API = Path("api_valoris/README.md")

ARQUIVOS_SQLITE_BRIDGE = [CAMINHO_REPOSITORY_BRIDGE, CAMINHO_ROUTES_LEADS, CAMINHO_ROUTES_EVENTS]

CAMPOS_DECISAO_API_SQLITE = [
    "id", "data_registro", "score_sqlite_api", "scaffold_existe", "arquivos_ok",
    "health_ok", "sqlite_existe", "leads_sqlite", "events_sqlite", "decisao",
    "proximo_passo", "observacoes",
]

REPOSITORY_BRIDGE_SQLITE_PY = 'from __future__ import annotations\n\nimport csv\nimport sqlite3\nfrom datetime import datetime\nfrom pathlib import Path\nfrom typing import Any\nfrom uuid import uuid4\n\n\nclass RepositoryBridge:\n    """Ponte local CSV + SQLite da API Valoris."""\n\n    def __init__(self, root_path: str | None = None):\n        self.root_path = Path(root_path).resolve() if root_path else Path(__file__).resolve().parents[3]\n        self.leads_csv = self.root_path / "lista_espera_beta.csv"\n        self.events_csv = self.root_path / "eventos_publicos_valoris.csv"\n        self.sqlite_db = self.root_path / "valoris_api_local.sqlite3"\n        self.lead_fields = ["id", "data_criacao", "nome", "contato", "perfil", "principal_dor", "plano_interesse", "preco_aceitavel", "pagaria_agora", "comentario"]\n        self.event_fields = ["id", "data_evento", "sessao_id", "evento", "origem", "contexto", "perfil", "valor", "detalhe"]\n        self._ensure_database()\n\n    def _clean(self, value: Any) -> str:\n        return "" if value is None else str(value).strip()\n\n    def _payload_to_dict(self, payload: Any) -> dict:\n        if hasattr(payload, "model_dump"):\n            return payload.model_dump()\n        if hasattr(payload, "dict"):\n            return payload.dict()\n        return payload if isinstance(payload, dict) else {}\n\n    def _connect(self) -> sqlite3.Connection:\n        conn = sqlite3.connect(self.sqlite_db)\n        conn.row_factory = sqlite3.Row\n        return conn\n\n    def _ensure_database(self) -> None:\n        with self._connect() as conn:\n            conn.execute("""\n                CREATE TABLE IF NOT EXISTS leads (\n                    id TEXT PRIMARY KEY,\n                    data_criacao TEXT NOT NULL,\n                    nome TEXT,\n                    contato TEXT,\n                    perfil TEXT,\n                    principal_dor TEXT,\n                    plano_interesse TEXT,\n                    preco_aceitavel TEXT,\n                    pagaria_agora TEXT,\n                    comentario TEXT\n                )\n            """)\n            conn.execute("""\n                CREATE TABLE IF NOT EXISTS events (\n                    id TEXT PRIMARY KEY,\n                    data_evento TEXT NOT NULL,\n                    sessao_id TEXT,\n                    evento TEXT,\n                    origem TEXT,\n                    contexto TEXT,\n                    perfil TEXT,\n                    valor TEXT,\n                    detalhe TEXT\n                )\n            """)\n            conn.commit()\n\n    def _ensure_csv(self, path: Path, fields: list[str]) -> None:\n        if not path.exists():\n            with path.open("w", newline="", encoding="utf-8") as file:\n                csv.DictWriter(file, fieldnames=fields).writeheader()\n\n    def _append_csv(self, path: Path, fields: list[str], row: dict) -> dict:\n        self._ensure_csv(path, fields)\n        final_row = {field: self._clean(row.get(field, "")) for field in fields}\n        with path.open("a", newline="", encoding="utf-8") as file:\n            csv.DictWriter(file, fieldnames=fields).writerow(final_row)\n        return final_row\n\n    def _read_csv(self, path: Path, fields: list[str], limit: int = 100) -> list[dict]:\n        self._ensure_csv(path, fields)\n        with path.open("r", newline="", encoding="utf-8") as file:\n            rows = list(csv.DictReader(file))\n        return rows[-limit:]\n\n    def _insert_sqlite(self, table: str, fields: list[str], row: dict) -> dict:\n        final_row = {field: self._clean(row.get(field, "")) for field in fields}\n        placeholders = ", ".join(["?"] * len(fields))\n        columns = ", ".join(fields)\n        values = [final_row[field] for field in fields]\n        with self._connect() as conn:\n            conn.execute(f"INSERT OR REPLACE INTO {table} ({columns}) VALUES ({placeholders})", values)\n            conn.commit()\n        return final_row\n\n    def _read_sqlite(self, table: str, order_field: str, limit: int = 100) -> list[dict]:\n        with self._connect() as conn:\n            rows = conn.execute(f"SELECT * FROM {table} ORDER BY {order_field} DESC LIMIT ?", (limit,)).fetchall()\n        return [dict(row) for row in rows]\n\n    def create_lead(self, payload: Any) -> dict:\n        data = self._payload_to_dict(payload)\n        row = {\n            "id": str(uuid4())[:8],\n            "data_criacao": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),\n            "nome": data.get("nome", ""),\n            "contato": data.get("contato", ""),\n            "perfil": data.get("perfil", ""),\n            "principal_dor": data.get("principal_dor", ""),\n            "plano_interesse": data.get("plano_interesse", ""),\n            "preco_aceitavel": data.get("preco_aceitavel", ""),\n            "pagaria_agora": data.get("pagaria_agora", ""),\n            "comentario": data.get("comentario", ""),\n        }\n        csv_saved = self._append_csv(self.leads_csv, self.lead_fields, row)\n        sqlite_saved = self._insert_sqlite("leads", self.lead_fields, row)\n        return {"ok": True, "source": "csv+sqlite", "file": str(self.leads_csv), "database": str(self.sqlite_db), "lead": sqlite_saved, "csv_backup": csv_saved}\n\n    def list_leads(self, limit: int = 100, source: str = "sqlite") -> dict:\n        if source == "csv":\n            rows = self._read_csv(self.leads_csv, self.lead_fields, limit=limit)\n            selected_source = "csv"\n        else:\n            rows = self._read_sqlite("leads", "data_criacao", limit=limit)\n            selected_source = "sqlite"\n        return {"ok": True, "source": selected_source, "file": str(self.leads_csv), "database": str(self.sqlite_db), "total": len(rows), "leads": rows}\n\n    def create_event(self, payload: Any) -> dict:\n        data = self._payload_to_dict(payload)\n        row = {\n            "id": str(uuid4())[:8],\n            "data_evento": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),\n            "sessao_id": data.get("sessao_id", ""),\n            "evento": data.get("evento", ""),\n            "origem": data.get("origem", ""),\n            "contexto": data.get("contexto", ""),\n            "perfil": data.get("perfil", ""),\n            "valor": data.get("valor", ""),\n            "detalhe": data.get("detalhe", ""),\n        }\n        csv_saved = self._append_csv(self.events_csv, self.event_fields, row)\n        sqlite_saved = self._insert_sqlite("events", self.event_fields, row)\n        return {"ok": True, "source": "csv+sqlite", "file": str(self.events_csv), "database": str(self.sqlite_db), "event": sqlite_saved, "csv_backup": csv_saved}\n\n    def storage_health(self) -> dict:\n        self._ensure_database()\n        with self._connect() as conn:\n            lead_count = conn.execute("SELECT COUNT(*) AS total FROM leads").fetchone()["total"]\n            event_count = conn.execute("SELECT COUNT(*) AS total FROM events").fetchone()["total"]\n        return {\n            "ok": True,\n            "database": str(self.sqlite_db),\n            "database_exists": self.sqlite_db.exists(),\n            "leads": lead_count,\n            "events": event_count,\n            "csv_leads_exists": self.leads_csv.exists(),\n            "csv_events_exists": self.events_csv.exists(),\n        }\n'
ROUTES_LEADS_SQLITE_PY = 'from fastapi import APIRouter, Query\n\nfrom app.schemas.lead import LeadCreate\nfrom app.services.repository_bridge import RepositoryBridge\n\n\nrouter = APIRouter()\nrepository = RepositoryBridge()\n\n\n@router.post("")\ndef create_lead(payload: LeadCreate):\n    result = repository.create_lead(payload)\n    return {\n        "ok": result["ok"],\n        "message": "Lead salvo nos dados reais da Valoris via CSV + SQLite.",\n        "source": result["source"],\n        "file": result["file"],\n        "database": result["database"],\n        "lead": result["lead"],\n    }\n\n\n@router.get("")\ndef list_leads(\n    limit: int = Query(default=100, ge=1, le=500),\n    source: str = Query(default="sqlite"),\n):\n    return repository.list_leads(limit=limit, source=source)\n\n\n@router.get("/storage-health")\ndef storage_health():\n    return repository.storage_health()\n'
ROUTES_EVENTS_SQLITE_PY = 'from fastapi import APIRouter\n\nfrom app.schemas.event import EventCreate\nfrom app.services.repository_bridge import RepositoryBridge\n\n\nrouter = APIRouter()\nrepository = RepositoryBridge()\n\n\n@router.post("")\ndef create_event(payload: EventCreate):\n    result = repository.create_event(payload)\n    return {\n        "ok": result["ok"],\n        "message": "Evento salvo nos dados reais da Valoris via CSV + SQLite.",\n        "source": result["source"],\n        "file": result["file"],\n        "database": result["database"],\n        "event": result["event"],\n    }\n\n\n@router.get("/storage-health")\ndef storage_health():\n    return repository.storage_health()\n'
README_APPEND_SQLITE = '## Ponte CSV + SQLite\n\nA partir da v3.8.66, a API local passa a gravar em duas camadas:\n\n- CSV: compatibilidade e inspeção rápida.\n- SQLite: camada estruturada para preparar PostgreSQL/Supabase.\n\nRotas impactadas:\n\n- `POST /leads` grava em `lista_espera_beta.csv` e `valoris_api_local.sqlite3`.\n- `GET /leads` lê SQLite por padrão.\n- `GET /leads?source=csv` lê CSV quando necessário.\n- `POST /events` grava em `eventos_publicos_valoris.csv` e `valoris_api_local.sqlite3`.\n- `GET /leads/storage-health` inspeciona a camada local.\n- `GET /events/storage-health` inspeciona a camada local.\n'


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


def carregar_decisoes_api_sqlite() -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_DECISOES_API_SQLITE, CAMPOS_DECISAO_API_SQLITE)
    with CAMINHO_DECISOES_API_SQLITE.open("r", newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def gerar_csv_decisoes_api_sqlite() -> str:
    _garantir_csv(CAMINHO_DECISOES_API_SQLITE, CAMPOS_DECISAO_API_SQLITE)
    return CAMINHO_DECISOES_API_SQLITE.read_text(encoding="utf-8")


def salvar_decisao_api_sqlite(decisao: Dict[str, Any]) -> Dict[str, str]:
    _garantir_csv(CAMINHO_DECISOES_API_SQLITE, CAMPOS_DECISAO_API_SQLITE)
    registro = {
        "id": str(uuid4())[:8],
        "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score_sqlite_api": str(decisao.get("score_sqlite_api", "")),
        "scaffold_existe": str(decisao.get("scaffold_existe", "")),
        "arquivos_ok": str(decisao.get("arquivos_ok", "")),
        "health_ok": str(decisao.get("health_ok", "")),
        "sqlite_existe": str(decisao.get("sqlite_existe", "")),
        "leads_sqlite": str(decisao.get("leads_sqlite", "")),
        "events_sqlite": str(decisao.get("events_sqlite", "")),
        "decisao": _limpar_texto(decisao.get("decisao", "")),
        "proximo_passo": _limpar_texto(decisao.get("proximo_passo", "")),
        "observacoes": _limpar_texto(decisao.get("observacoes", "")),
    }
    with CAMINHO_DECISOES_API_SQLITE.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISAO_API_SQLITE)
        escritor.writerow(registro)
    return registro


def verificar_arquivos_sqlite_bridge() -> Dict[str, Any]:
    itens = []
    for caminho in ARQUIVOS_SQLITE_BRIDGE:
        itens.append({
            "arquivo": str(caminho),
            "existe": caminho.exists(),
            "tamanho_bytes": caminho.stat().st_size if caminho.exists() else 0,
        })
    total = len(itens)
    existentes = len([item for item in itens if item["existe"]])
    return {"itens": itens, "total": total, "existentes": existentes, "ok": existentes == total}


def compilar_arquivos_sqlite_bridge() -> Dict[str, Any]:
    resultados = []
    for caminho in ARQUIVOS_SQLITE_BRIDGE:
        if not caminho.exists():
            resultados.append({"arquivo": str(caminho), "status": "ausente", "detalhe": "Arquivo não encontrado."})
            continue
        try:
            py_compile.compile(str(caminho), doraise=True)
            resultados.append({"arquivo": str(caminho), "status": "ok", "detalhe": "Compilação OK."})
        except Exception as erro:
            resultados.append({"arquivo": str(caminho), "status": "erro", "detalhe": str(erro)})
    erros = [item for item in resultados if item["status"] != "ok"]
    return {"resultados": resultados, "erros": erros, "ok": len(erros) == 0}


def inspecionar_sqlite_api() -> Dict[str, Any]:
    if not CAMINHO_SQLITE_API.exists():
        return {"sqlite_existe": False, "database": str(CAMINHO_SQLITE_API), "leads": 0, "events": 0, "tabelas": [], "erro": ""}
    try:
        with sqlite3.connect(CAMINHO_SQLITE_API) as conn:
            conn.row_factory = sqlite3.Row
            tabelas = [row["name"] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()]
            leads = int(conn.execute("SELECT COUNT(*) AS total FROM leads").fetchone()["total"]) if "leads" in tabelas else 0
            events = int(conn.execute("SELECT COUNT(*) AS total FROM events").fetchone()["total"]) if "events" in tabelas else 0
        return {"sqlite_existe": True, "database": str(CAMINHO_SQLITE_API), "leads": leads, "events": events, "tabelas": tabelas, "erro": ""}
    except Exception as erro:
        return {"sqlite_existe": CAMINHO_SQLITE_API.exists(), "database": str(CAMINHO_SQLITE_API), "leads": 0, "events": 0, "tabelas": [], "erro": str(erro)}


def aplicar_bridge_api_sqlite() -> Dict[str, Any]:
    if not PASTA_API_SCAFFOLD.exists():
        return {"ok": False, "mensagem": "A pasta api_valoris não existe. Gere o scaffold antes.", "arquivos": []}

    CAMINHO_REPOSITORY_BRIDGE.parent.mkdir(parents=True, exist_ok=True)
    CAMINHO_ROUTES_LEADS.parent.mkdir(parents=True, exist_ok=True)
    CAMINHO_ROUTES_EVENTS.parent.mkdir(parents=True, exist_ok=True)

    CAMINHO_REPOSITORY_BRIDGE.write_text(REPOSITORY_BRIDGE_SQLITE_PY + "\n", encoding="utf-8")
    CAMINHO_ROUTES_LEADS.write_text(ROUTES_LEADS_SQLITE_PY + "\n", encoding="utf-8")
    CAMINHO_ROUTES_EVENTS.write_text(ROUTES_EVENTS_SQLITE_PY + "\n", encoding="utf-8")

    if CAMINHO_README_API.exists():
        conteudo_readme = CAMINHO_README_API.read_text(encoding="utf-8")
        if "Ponte CSV + SQLite" not in conteudo_readme:
            CAMINHO_README_API.write_text(conteudo_readme.rstrip() + "\n\n" + README_APPEND_SQLITE + "\n", encoding="utf-8")

    compilacao = compilar_arquivos_sqlite_bridge()
    manifesto = gerar_manifesto_api_sqlite()

    return {
        "ok": compilacao["ok"],
        "mensagem": "Bridge API → SQLite aplicada com compatibilidade CSV.",
        "arquivos": [str(item) for item in ARQUIVOS_SQLITE_BRIDGE],
        "compilacao": compilacao,
        "manifesto": manifesto,
    }


def calcular_saude_api_sqlite() -> Dict[str, Any]:
    arquivos = verificar_arquivos_sqlite_bridge()
    compilacao = compilar_arquivos_sqlite_bridge()
    health = testar_health_api()
    sqlite_info = inspecionar_sqlite_api()

    try:
        bridge = calcular_saude_api_bridge()
    except Exception:
        bridge = {"score_bridge": 0}

    try:
        tests = calcular_saude_api_endpoint_tests()
    except Exception:
        tests = {"score_tests": 0}

    score_bridge = int(bridge.get("score_bridge", 0) or 0)
    score_tests = int(tests.get("score_tests", 0) or 0)

    score = 10
    score += 14 if PASTA_API_SCAFFOLD.exists() else 0
    score += min(arquivos["existentes"] * 10, 30)
    score += 14 if compilacao["ok"] else 0
    score += 12 if health["health_ok"] else 0
    score += 12 if sqlite_info["sqlite_existe"] else 0
    score += 8 if "leads" in sqlite_info["tabelas"] else 0
    score += 6 if "events" in sqlite_info["tabelas"] else 0
    score += min(score_tests * 0.04, 4)
    score += min(score_bridge * 0.04, 4)
    score = int(round(max(0, min(100, score))))

    if score >= 85 and sqlite_info["sqlite_existe"] and health["health_ok"]:
        decisao = "Bridge API → SQLite validada"
        proximo_passo = "Rodar a suite de endpoints e confirmar registros no SQLite antes de criar adapter selecionável."
    elif score >= 70:
        decisao = "Bridge SQLite aplicada, falta validação completa"
        proximo_passo = "Rode a API, execute testes de endpoints e inspecione valoris_api_local.sqlite3."
    elif score >= 50:
        decisao = "SQLite parcialmente preparado"
        proximo_passo = "Aplique a bridge pela aba e rode a API para criar o banco local."
    else:
        decisao = "SQLite ainda não preparado"
        proximo_passo = "Gere o scaffold/API Bridge antes de aplicar SQLite."

    return {
        "score_sqlite_api": score,
        "scaffold_existe": PASTA_API_SCAFFOLD.exists(),
        "arquivos": arquivos,
        "compilacao": compilacao,
        "health": health,
        "health_ok": health["health_ok"],
        "sqlite": sqlite_info,
        "score_bridge": score_bridge,
        "score_tests": score_tests,
        "decisao": decisao,
        "proximo_passo": proximo_passo,
    }


def gerar_manifesto_api_sqlite() -> Dict[str, Any]:
    saude = calcular_saude_api_sqlite()
    manifesto = {
        "versao": VERSAO_API_SQLITE_BRIDGE_VALORIS,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "saude": saude,
        "database": str(CAMINHO_SQLITE_API),
        "rotas_afetadas": ["POST /leads", "GET /leads", "GET /leads/storage-health", "POST /events", "GET /events/storage-health"],
        "estrategia": "CSV + SQLite local",
    }
    CAMINHO_MANIFESTO_API_SQLITE.write_text(json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifesto


def _gerar_markdown_sqlite(saude: Dict[str, Any]) -> str:
    arquivos = "\n".join([f"- `{item['arquivo']}` — {'OK' if item['existe'] else 'Ausente'}" for item in saude["arquivos"]["itens"]])
    tabelas = ", ".join(saude["sqlite"].get("tabelas", [])) or "Nenhuma"
    return f"""# Bridge API → SQLite — Valoris

Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Diagnóstico

Score SQLite API: {saude["score_sqlite_api"]}/100  
Decisão: {saude["decisao"]}  
Próximo passo: {saude["proximo_passo"]}

Scaffold existe: {saude["scaffold_existe"]}  
Arquivos OK: {saude["arquivos"]["ok"]}  
Compilação OK: {saude["compilacao"]["ok"]}  
Health OK: {saude["health_ok"]}  

## SQLite

Banco existe: {saude["sqlite"]["sqlite_existe"]}  
Arquivo: `{saude["sqlite"]["database"]}`  
Tabelas: {tabelas}  
Leads: {saude["sqlite"]["leads"]}  
Events: {saude["sqlite"]["events"]}  

## Rotas afetadas

- `POST /leads` → CSV + SQLite
- `GET /leads` → SQLite por padrão
- `GET /leads?source=csv` → CSV
- `POST /events` → CSV + SQLite
- `GET /leads/storage-health`
- `GET /events/storage-health`

## Arquivos alterados na API local

{arquivos}

## Teste manual

Com a API ligada:

```powershell
.\\scripts_api_valoris\\testar_endpoints_api_valoris.ps1
```

Inspecione o banco:

```powershell
python -c "import sqlite3; c=sqlite3.connect('valoris_api_local.sqlite3'); print(c.execute('select count(*) from leads').fetchone()); print(c.execute('select count(*) from events').fetchone())"
```

## Regra

SQLite ainda é camada local. O próximo passo será adapter selecionável antes de PostgreSQL/Supabase.
"""


def _injetar_css_sqlite() -> None:
    st.markdown(
        """
        <style>
            .sqlite-hero {
                padding: clamp(1.18rem, 3vw, 2rem);
                border-radius: 30px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    radial-gradient(circle at top left, rgba(214, 181, 109, 0.26), transparent 30%),
                    radial-gradient(circle at bottom right, rgba(36, 128, 91, 0.24), transparent 34%),
                    linear-gradient(135deg, rgba(8, 15, 27, 0.99), rgba(5, 9, 18, 0.99));
                box-shadow: 0 18px 58px rgba(0, 0, 0, 0.31);
                margin-bottom: 1rem;
            }

            .sqlite-eyebrow {
                color: #d6b56d;
                font-size: 0.74rem;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                font-weight: 880;
                margin-bottom: 0.35rem;
            }

            .sqlite-title {
                color: #f4f7fb;
                font-size: clamp(1.75rem, 5.4vw, 3.1rem);
                font-weight: 950;
                line-height: 1.02;
                letter-spacing: -0.058em;
                margin-bottom: 0.55rem;
            }

            .sqlite-subtitle {
                color: rgba(244, 247, 251, 0.75);
                font-size: clamp(0.94rem, 2.2vw, 1.06rem);
                line-height: 1.56;
                max-width: 1020px;
            }

            .sqlite-note {
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
        <div class="sqlite-hero">
            <div class="sqlite-eyebrow">Valoris • API SQLite • v{VERSAO_API_SQLITE_BRIDGE_VALORIS}</div>
            <div class="sqlite-title">Transforme CSV em camada de dados estruturada.</div>
            <div class="sqlite-subtitle">
                Esta etapa mantém os CSVs como compatibilidade, mas adiciona SQLite como primeira
                camada real de banco local para preparar PostgreSQL/Supabase.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _renderizar_metricas(saude: Dict[str, Any]) -> None:
    st.markdown("### Diagnóstico SQLite API")
    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Score SQLite API", f"{saude['score_sqlite_api']}/100")
    with col_2:
        st.metric("SQLite", "OK" if saude["sqlite"]["sqlite_existe"] else "Ausente")
    with col_3:
        st.metric("Leads", saude["sqlite"]["leads"])
    with col_4:
        st.metric("Events", saude["sqlite"]["events"])

    st.progress(saude["score_sqlite_api"] / 100)

    if saude["score_sqlite_api"] >= 85:
        st.success(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    elif saude["score_sqlite_api"] >= 50:
        st.warning(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    else:
        st.info(f"**{saude['decisao']}** — {saude['proximo_passo']}")


def _renderizar_arquivos(saude: Dict[str, Any]) -> None:
    st.markdown("### Arquivos da bridge SQLite")
    for item in saude["arquivos"]["itens"]:
        with st.container(border=True):
            st.markdown(f"**{item['arquivo']}**")
            st.caption("OK" if item["existe"] else "Ausente")
            st.markdown(f"Tamanho: **{item['tamanho_bytes']} bytes**")


def _renderizar_compilacao(saude: Dict[str, Any]) -> None:
    st.markdown("### Compilação da bridge SQLite")
    for item in saude["compilacao"]["resultados"]:
        with st.container(border=True):
            st.markdown(f"**{item['arquivo']}** — {item['status']}")
            st.caption(item["detalhe"])


def _renderizar_historico() -> None:
    historico = carregar_decisoes_api_sqlite()
    st.markdown("### Histórico de decisões API SQLite")

    if not historico:
        st.info("Ainda não há decisões salvas.")
        return

    for item in reversed(historico[-10:]):
        with st.container(border=True):
            st.markdown(f"**{item.get('decisao', 'N/D')}**")
            st.caption(item.get("data_registro", "N/D"))
            st.markdown(f"Score: {item.get('score_sqlite_api', 'N/D')}/100")
            st.markdown(f"SQLite existe: {item.get('sqlite_existe', 'N/D')}")
            st.markdown(f"Próximo passo: {item.get('proximo_passo', 'N/D')}")


def renderizar_api_sqlite_bridge_valoris() -> None:
    _injetar_css_sqlite()
    _renderizar_hero()

    saude = calcular_saude_api_sqlite()
    _renderizar_metricas(saude)

    st.divider()
    col_1, col_2, col_3 = st.columns(3)

    with col_1:
        if st.button("Aplicar bridge API → SQLite", key="aplicar_bridge_api_sqlite"):
            resultado = aplicar_bridge_api_sqlite()
            if resultado["ok"]:
                st.success(resultado["mensagem"])
            else:
                st.warning(resultado["mensagem"])
            st.json(resultado)
            st.rerun()

    with col_2:
        if st.button("Gerar manifesto SQLite", key="gerar_manifesto_api_sqlite"):
            manifesto = gerar_manifesto_api_sqlite()
            st.success(f"Manifesto gerado: {CAMINHO_MANIFESTO_API_SQLITE}")
            st.json({"versao": manifesto["versao"], "score": manifesto["saude"]["score_sqlite_api"], "database": manifesto["database"]})

    with col_3:
        if st.button("Salvar decisão SQLite", key="salvar_decisao_api_sqlite"):
            registro = salvar_decisao_api_sqlite(
                {
                    "score_sqlite_api": saude["score_sqlite_api"],
                    "scaffold_existe": saude["scaffold_existe"],
                    "arquivos_ok": saude["arquivos"]["ok"],
                    "health_ok": saude["health_ok"],
                    "sqlite_existe": saude["sqlite"]["sqlite_existe"],
                    "leads_sqlite": saude["sqlite"]["leads"],
                    "events_sqlite": saude["sqlite"]["events"],
                    "decisao": saude["decisao"],
                    "proximo_passo": saude["proximo_passo"],
                    "observacoes": "Decisão gerada pela bridge API → SQLite.",
                }
            )
            st.success(f"Decisão salva: {registro['decisao']}")
            st.rerun()

    st.download_button(
        "Baixar diagnóstico API SQLite (.md)",
        data=_gerar_markdown_sqlite(saude),
        file_name="api_sqlite_bridge_valoris.md",
        mime="text/markdown",
        key="download_api_sqlite_bridge",
    )

    st.download_button(
        "Baixar decisões API SQLite (.csv)",
        data=gerar_csv_decisoes_api_sqlite(),
        file_name="decisoes_api_sqlite_valoris.csv",
        mime="text/csv",
        key="download_decisoes_api_sqlite",
    )

    st.divider()
    st.markdown("### Banco SQLite")
    st.json(saude["sqlite"])

    st.divider()
    _renderizar_arquivos(saude)

    st.divider()
    _renderizar_compilacao(saude)

    st.divider()
    _renderizar_historico()

    st.markdown(
        """
        <div class="sqlite-note">
            <strong>Regra SQLite:</strong> manter CSV + SQLite por enquanto. Só depois criaremos
            adapter selecionável e, então, PostgreSQL/Supabase.
        </div>
        """,
        unsafe_allow_html=True,
    )


def executar_autoteste_api_sqlite_bridge_valoris() -> List[Dict[str, str]]:
    saude = calcular_saude_api_sqlite()
    return [
        {"teste": "versao_sqlite_bridge", "status": "OK" if VERSAO_API_SQLITE_BRIDGE_VALORIS == "3.8.66" else "FALHA", "detalhe": VERSAO_API_SQLITE_BRIDGE_VALORIS},
        {"teste": "score_sqlite_api", "status": "OK" if 0 <= saude["score_sqlite_api"] <= 100 else "FALHA", "detalhe": str(saude["score_sqlite_api"])},
        {"teste": "renderizador", "status": "OK" if callable(renderizar_api_sqlite_bridge_valoris) else "FALHA", "detalhe": "renderizar_api_sqlite_bridge_valoris"},
    ]
