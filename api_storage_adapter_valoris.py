# api_storage_adapter_valoris.py

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

from api_sqlite_bridge_valoris import calcular_saude_api_sqlite
from api_endpoint_tests_valoris import calcular_saude_api_endpoint_tests
from api_smoke_tests_valoris import PASTA_API_SCAFFOLD, testar_health_api


VERSAO_API_STORAGE_ADAPTER_VALORIS = "3.8.67"

CAMINHO_DECISOES_API_ADAPTER = Path("decisoes_api_adapter_valoris.csv")
CAMINHO_MANIFESTO_API_ADAPTER = Path("manifesto_api_adapter_valoris.json")

CAMINHO_STORAGE_CONFIG = Path("api_valoris/app/core/storage_config.py")
CAMINHO_REPOSITORY_BRIDGE = Path("api_valoris/app/services/repository_bridge.py")
CAMINHO_ROUTES_LEADS = Path("api_valoris/app/routes/leads.py")
CAMINHO_ROUTES_EVENTS = Path("api_valoris/app/routes/events.py")
CAMINHO_README_API = Path("api_valoris/README.md")
CAMINHO_SQLITE_API = Path("valoris_api_local.sqlite3")

ARQUIVOS_ADAPTER = [
    CAMINHO_STORAGE_CONFIG,
    CAMINHO_REPOSITORY_BRIDGE,
    CAMINHO_ROUTES_LEADS,
    CAMINHO_ROUTES_EVENTS,
]

MODOS_STORAGE = ["csv", "sqlite", "hybrid"]

CAMPOS_DECISAO_API_ADAPTER = [
    "id",
    "data_registro",
    "score_adapter",
    "storage_mode",
    "scaffold_existe",
    "arquivos_ok",
    "health_ok",
    "sqlite_existe",
    "decisao",
    "proximo_passo",
    "observacoes",
]

STORAGE_CONFIG_TEMPLATE = 'DEFAULT_STORAGE_MODE = "hybrid"\n\nALLOWED_STORAGE_MODES = ["csv", "sqlite", "hybrid"]\n'
REPOSITORY_BRIDGE_ADAPTER_PY = 'from __future__ import annotations\n\nimport csv\nimport os\nimport sqlite3\nfrom datetime import datetime\nfrom pathlib import Path\nfrom typing import Any\nfrom uuid import uuid4\n\ntry:\n    from app.core.storage_config import DEFAULT_STORAGE_MODE, ALLOWED_STORAGE_MODES\nexcept Exception:\n    DEFAULT_STORAGE_MODE = "hybrid"\n    ALLOWED_STORAGE_MODES = ["csv", "sqlite", "hybrid"]\n\n\nclass RepositoryBridge:\n    """\n    v3.8.67 — Adapter selecionável:\n    csv, sqlite ou hybrid.\n    """\n\n    def __init__(self, root_path: str | None = None, storage_mode: str | None = None):\n        self.root_path = Path(root_path).resolve() if root_path else Path(__file__).resolve().parents[3]\n        self.leads_csv = self.root_path / "lista_espera_beta.csv"\n        self.events_csv = self.root_path / "eventos_publicos_valoris.csv"\n        self.sqlite_db = self.root_path / "valoris_api_local.sqlite3"\n        self.storage_mode = self._normalize_storage_mode(\n            storage_mode or os.getenv("VALORIS_STORAGE_MODE", "") or DEFAULT_STORAGE_MODE\n        )\n\n        self.lead_fields = [\n            "id", "data_criacao", "nome", "contato", "perfil", "principal_dor",\n            "plano_interesse", "preco_aceitavel", "pagaria_agora", "comentario",\n        ]\n        self.event_fields = [\n            "id", "data_evento", "sessao_id", "evento", "origem", "contexto",\n            "perfil", "valor", "detalhe",\n        ]\n\n        if self.storage_mode in ["sqlite", "hybrid"]:\n            self._ensure_database()\n\n    def _normalize_storage_mode(self, mode: str) -> str:\n        mode = str(mode or "").strip().lower()\n        return mode if mode in ALLOWED_STORAGE_MODES else "hybrid"\n\n    def _clean(self, value: Any) -> str:\n        if value is None:\n            return ""\n        return str(value).strip()\n\n    def _payload_to_dict(self, payload: Any) -> dict:\n        if hasattr(payload, "model_dump"):\n            return payload.model_dump()\n        if hasattr(payload, "dict"):\n            return payload.dict()\n        return payload if isinstance(payload, dict) else {}\n\n    def _connect(self) -> sqlite3.Connection:\n        conn = sqlite3.connect(self.sqlite_db)\n        conn.row_factory = sqlite3.Row\n        return conn\n\n    def _ensure_database(self) -> None:\n        with self._connect() as conn:\n            conn.execute(\n                """\n                CREATE TABLE IF NOT EXISTS leads (\n                    id TEXT PRIMARY KEY,\n                    data_criacao TEXT NOT NULL,\n                    nome TEXT,\n                    contato TEXT,\n                    perfil TEXT,\n                    principal_dor TEXT,\n                    plano_interesse TEXT,\n                    preco_aceitavel TEXT,\n                    pagaria_agora TEXT,\n                    comentario TEXT\n                )\n                """\n            )\n            conn.execute(\n                """\n                CREATE TABLE IF NOT EXISTS events (\n                    id TEXT PRIMARY KEY,\n                    data_evento TEXT NOT NULL,\n                    sessao_id TEXT,\n                    evento TEXT,\n                    origem TEXT,\n                    contexto TEXT,\n                    perfil TEXT,\n                    valor TEXT,\n                    detalhe TEXT\n                )\n                """\n            )\n            conn.commit()\n\n    def _ensure_csv(self, path: Path, fields: list[str]) -> None:\n        if path.exists():\n            return\n        with path.open("w", newline="", encoding="utf-8") as file:\n            writer = csv.DictWriter(file, fieldnames=fields)\n            writer.writeheader()\n\n    def _append_csv(self, path: Path, fields: list[str], row: dict) -> dict:\n        self._ensure_csv(path, fields)\n        final_row = {field: self._clean(row.get(field, "")) for field in fields}\n        with path.open("a", newline="", encoding="utf-8") as file:\n            writer = csv.DictWriter(file, fieldnames=fields)\n            writer.writerow(final_row)\n        return final_row\n\n    def _read_csv(self, path: Path, fields: list[str], limit: int = 100) -> list[dict]:\n        self._ensure_csv(path, fields)\n        with path.open("r", newline="", encoding="utf-8") as file:\n            rows = list(csv.DictReader(file))\n        return rows[-limit:]\n\n    def _insert_sqlite(self, table: str, fields: list[str], row: dict) -> dict:\n        self._ensure_database()\n        final_row = {field: self._clean(row.get(field, "")) for field in fields}\n        columns = ", ".join(fields)\n        placeholders = ", ".join(["?"] * len(fields))\n        values = [final_row[field] for field in fields]\n\n        with self._connect() as conn:\n            conn.execute(\n                f"INSERT OR REPLACE INTO {table} ({columns}) VALUES ({placeholders})",\n                values,\n            )\n            conn.commit()\n\n        return final_row\n\n    def _read_sqlite(self, table: str, order_field: str, limit: int = 100) -> list[dict]:\n        self._ensure_database()\n        with self._connect() as conn:\n            rows = conn.execute(\n                f"SELECT * FROM {table} ORDER BY {order_field} DESC LIMIT ?",\n                (limit,),\n            ).fetchall()\n        return [dict(row) for row in rows]\n\n    def _read_source(self, source: str) -> str:\n        requested = str(source or "auto").strip().lower()\n        if requested in ["csv", "sqlite"]:\n            return requested\n        return "csv" if self.storage_mode == "csv" else "sqlite"\n\n    def create_lead(self, payload: Any) -> dict:\n        data = self._payload_to_dict(payload)\n        row = {\n            "id": str(uuid4())[:8],\n            "data_criacao": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),\n            "nome": data.get("nome", ""),\n            "contato": data.get("contato", ""),\n            "perfil": data.get("perfil", ""),\n            "principal_dor": data.get("principal_dor", ""),\n            "plano_interesse": data.get("plano_interesse", ""),\n            "preco_aceitavel": data.get("preco_aceitavel", ""),\n            "pagaria_agora": data.get("pagaria_agora", ""),\n            "comentario": data.get("comentario", ""),\n        }\n\n        csv_saved = self._append_csv(self.leads_csv, self.lead_fields, row) if self.storage_mode in ["csv", "hybrid"] else None\n        sqlite_saved = self._insert_sqlite("leads", self.lead_fields, row) if self.storage_mode in ["sqlite", "hybrid"] else None\n\n        return {\n            "ok": True,\n            "storage_mode": self.storage_mode,\n            "source": self.storage_mode,\n            "file": str(self.leads_csv),\n            "database": str(self.sqlite_db),\n            "lead": sqlite_saved or csv_saved or row,\n            "csv_backup": csv_saved,\n            "sqlite_record": sqlite_saved,\n        }\n\n    def list_leads(self, limit: int = 100, source: str = "auto") -> dict:\n        selected_source = self._read_source(source)\n        rows = (\n            self._read_csv(self.leads_csv, self.lead_fields, limit)\n            if selected_source == "csv"\n            else self._read_sqlite("leads", "data_criacao", limit)\n        )\n\n        return {\n            "ok": True,\n            "storage_mode": self.storage_mode,\n            "source": selected_source,\n            "file": str(self.leads_csv),\n            "database": str(self.sqlite_db),\n            "total": len(rows),\n            "leads": rows,\n        }\n\n    def create_event(self, payload: Any) -> dict:\n        data = self._payload_to_dict(payload)\n        row = {\n            "id": str(uuid4())[:8],\n            "data_evento": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),\n            "sessao_id": data.get("sessao_id", ""),\n            "evento": data.get("evento", ""),\n            "origem": data.get("origem", ""),\n            "contexto": data.get("contexto", ""),\n            "perfil": data.get("perfil", ""),\n            "valor": data.get("valor", ""),\n            "detalhe": data.get("detalhe", ""),\n        }\n\n        csv_saved = self._append_csv(self.events_csv, self.event_fields, row) if self.storage_mode in ["csv", "hybrid"] else None\n        sqlite_saved = self._insert_sqlite("events", self.event_fields, row) if self.storage_mode in ["sqlite", "hybrid"] else None\n\n        return {\n            "ok": True,\n            "storage_mode": self.storage_mode,\n            "source": self.storage_mode,\n            "file": str(self.events_csv),\n            "database": str(self.sqlite_db),\n            "event": sqlite_saved or csv_saved or row,\n            "csv_backup": csv_saved,\n            "sqlite_record": sqlite_saved,\n        }\n\n    def storage_health(self) -> dict:\n        if self.storage_mode in ["sqlite", "hybrid"]:\n            self._ensure_database()\n\n        tables = []\n        leads_count = 0\n        events_count = 0\n\n        if self.sqlite_db.exists():\n            with self._connect() as conn:\n                tables = [\n                    row["name"]\n                    for row in conn.execute(\n                        "SELECT name FROM sqlite_master WHERE type=\'table\' ORDER BY name"\n                    ).fetchall()\n                ]\n                if "leads" in tables:\n                    leads_count = conn.execute("SELECT COUNT(*) AS total FROM leads").fetchone()["total"]\n                if "events" in tables:\n                    events_count = conn.execute("SELECT COUNT(*) AS total FROM events").fetchone()["total"]\n\n        return {\n            "ok": True,\n            "storage_mode": self.storage_mode,\n            "allowed_storage_modes": ALLOWED_STORAGE_MODES,\n            "database": str(self.sqlite_db),\n            "database_exists": self.sqlite_db.exists(),\n            "tables": tables,\n            "leads": leads_count,\n            "events": events_count,\n            "csv_leads_exists": self.leads_csv.exists(),\n            "csv_events_exists": self.events_csv.exists(),\n        }'
ROUTES_LEADS_ADAPTER_PY = 'from fastapi import APIRouter, Query\n\nfrom app.schemas.lead import LeadCreate\nfrom app.services.repository_bridge import RepositoryBridge\n\n\nrouter = APIRouter()\nrepository = RepositoryBridge()\n\n\n@router.post("")\ndef create_lead(payload: LeadCreate):\n    result = repository.create_lead(payload)\n\n    return {\n        "ok": result["ok"],\n        "message": f"Lead salvo via storage_mode={result[\'storage_mode\']}.",\n        "storage_mode": result["storage_mode"],\n        "source": result["source"],\n        "file": result["file"],\n        "database": result["database"],\n        "lead": result["lead"],\n    }\n\n\n@router.get("")\ndef list_leads(\n    limit: int = Query(default=100, ge=1, le=500),\n    source: str = Query(default="auto"),\n):\n    return repository.list_leads(limit=limit, source=source)\n\n\n@router.get("/storage-health")\ndef storage_health():\n    return repository.storage_health()'
ROUTES_EVENTS_ADAPTER_PY = 'from fastapi import APIRouter\n\nfrom app.schemas.event import EventCreate\nfrom app.services.repository_bridge import RepositoryBridge\n\n\nrouter = APIRouter()\nrepository = RepositoryBridge()\n\n\n@router.post("")\ndef create_event(payload: EventCreate):\n    result = repository.create_event(payload)\n\n    return {\n        "ok": result["ok"],\n        "message": f"Evento salvo via storage_mode={result[\'storage_mode\']}.",\n        "storage_mode": result["storage_mode"],\n        "source": result["source"],\n        "file": result["file"],\n        "database": result["database"],\n        "event": result["event"],\n    }\n\n\n@router.get("/storage-health")\ndef storage_health():\n    return repository.storage_health()'
README_APPEND_ADAPTER = '## Adapter selecionável CSV/SQLite\n\nA partir da v3.8.67, a API usa um `storage_mode` local:\n\n- `csv`: grava apenas CSV.\n- `sqlite`: grava apenas SQLite.\n- `hybrid`: grava CSV + SQLite.\n\nO modo padrão fica em `api_valoris/app/core/storage_config.py`.\n\nA variável de ambiente `VALORIS_STORAGE_MODE` também pode sobrescrever o modo no futuro.\n\nEsta etapa prepara a troca controlada para PostgreSQL/Supabase sem quebrar as rotas públicas.'


def _limpar_texto(valor: Any) -> str:
    if valor is None:
        return ""
    return str(valor).strip()


def _normalizar_modo(modo: str) -> str:
    modo_limpo = str(modo or "").strip().lower()
    return modo_limpo if modo_limpo in MODOS_STORAGE else "hybrid"


def _garantir_csv(caminho: Path, campos: List[str]) -> None:
    if caminho.exists():
        return

    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()


def carregar_decisoes_api_adapter() -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_DECISOES_API_ADAPTER, CAMPOS_DECISAO_API_ADAPTER)

    with CAMINHO_DECISOES_API_ADAPTER.open("r", newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def gerar_csv_decisoes_api_adapter() -> str:
    _garantir_csv(CAMINHO_DECISOES_API_ADAPTER, CAMPOS_DECISAO_API_ADAPTER)
    return CAMINHO_DECISOES_API_ADAPTER.read_text(encoding="utf-8")


def salvar_decisao_api_adapter(decisao: Dict[str, Any]) -> Dict[str, str]:
    _garantir_csv(CAMINHO_DECISOES_API_ADAPTER, CAMPOS_DECISAO_API_ADAPTER)

    registro = {
        "id": str(uuid4())[:8],
        "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score_adapter": str(decisao.get("score_adapter", "")),
        "storage_mode": _normalizar_modo(decisao.get("storage_mode", "")),
        "scaffold_existe": str(decisao.get("scaffold_existe", "")),
        "arquivos_ok": str(decisao.get("arquivos_ok", "")),
        "health_ok": str(decisao.get("health_ok", "")),
        "sqlite_existe": str(decisao.get("sqlite_existe", "")),
        "decisao": _limpar_texto(decisao.get("decisao", "")),
        "proximo_passo": _limpar_texto(decisao.get("proximo_passo", "")),
        "observacoes": _limpar_texto(decisao.get("observacoes", "")),
    }

    with CAMINHO_DECISOES_API_ADAPTER.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISAO_API_ADAPTER)
        escritor.writerow(registro)

    return registro


def ler_storage_mode_atual() -> str:
    if not CAMINHO_STORAGE_CONFIG.exists():
        return "hybrid"

    texto = CAMINHO_STORAGE_CONFIG.read_text(encoding="utf-8", errors="ignore")

    for modo in MODOS_STORAGE:
        if f'DEFAULT_STORAGE_MODE = "{modo}"' in texto or f"DEFAULT_STORAGE_MODE = '{modo}'" in texto:
            return modo

    return "hybrid"


def _gerar_storage_config(modo: str) -> str:
    modo_final = _normalizar_modo(modo)
    return (
        f'DEFAULT_STORAGE_MODE = "{modo_final}"\n\n'
        'ALLOWED_STORAGE_MODES = ["csv", "sqlite", "hybrid"]'
    )


def verificar_arquivos_adapter() -> Dict[str, Any]:
    itens = []

    for caminho in ARQUIVOS_ADAPTER:
        itens.append(
            {
                "arquivo": str(caminho),
                "existe": caminho.exists(),
                "tamanho_bytes": caminho.stat().st_size if caminho.exists() else 0,
            }
        )

    total = len(itens)
    existentes = len([item for item in itens if item["existe"]])

    return {
        "itens": itens,
        "total": total,
        "existentes": existentes,
        "ok": existentes == total,
    }


def compilar_arquivos_adapter() -> Dict[str, Any]:
    resultados = []

    for caminho in ARQUIVOS_ADAPTER:
        if not caminho.exists():
            resultados.append(
                {
                    "arquivo": str(caminho),
                    "status": "ausente",
                    "detalhe": "Arquivo não encontrado.",
                }
            )
            continue

        try:
            py_compile.compile(str(caminho), doraise=True)
            resultados.append(
                {
                    "arquivo": str(caminho),
                    "status": "ok",
                    "detalhe": "Compilação OK.",
                }
            )
        except Exception as erro:
            resultados.append(
                {
                    "arquivo": str(caminho),
                    "status": "erro",
                    "detalhe": str(erro),
                }
            )

    erros = [item for item in resultados if item["status"] != "ok"]

    return {
        "resultados": resultados,
        "erros": erros,
        "ok": len(erros) == 0,
    }


def inspecionar_sqlite_adapter() -> Dict[str, Any]:
    if not CAMINHO_SQLITE_API.exists():
        return {
            "sqlite_existe": False,
            "database": str(CAMINHO_SQLITE_API),
            "leads": 0,
            "events": 0,
            "tabelas": [],
            "erro": "",
        }

    try:
        with sqlite3.connect(CAMINHO_SQLITE_API) as conn:
            conn.row_factory = sqlite3.Row
            tabelas = [
                row["name"]
                for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
            ]

            leads = 0
            events = 0

            if "leads" in tabelas:
                leads = int(conn.execute("SELECT COUNT(*) AS total FROM leads").fetchone()["total"])

            if "events" in tabelas:
                events = int(conn.execute("SELECT COUNT(*) AS total FROM events").fetchone()["total"])

        return {
            "sqlite_existe": True,
            "database": str(CAMINHO_SQLITE_API),
            "leads": leads,
            "events": events,
            "tabelas": tabelas,
            "erro": "",
        }

    except Exception as erro:
        return {
            "sqlite_existe": CAMINHO_SQLITE_API.exists(),
            "database": str(CAMINHO_SQLITE_API),
            "leads": 0,
            "events": 0,
            "tabelas": [],
            "erro": str(erro),
        }


def aplicar_storage_adapter(modo: str = "hybrid") -> Dict[str, Any]:
    modo_final = _normalizar_modo(modo)

    if not PASTA_API_SCAFFOLD.exists():
        return {
            "ok": False,
            "mensagem": "A pasta api_valoris não existe. Gere o scaffold antes.",
            "storage_mode": modo_final,
            "arquivos": [],
        }

    CAMINHO_STORAGE_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    CAMINHO_REPOSITORY_BRIDGE.parent.mkdir(parents=True, exist_ok=True)
    CAMINHO_ROUTES_LEADS.parent.mkdir(parents=True, exist_ok=True)
    CAMINHO_ROUTES_EVENTS.parent.mkdir(parents=True, exist_ok=True)

    CAMINHO_STORAGE_CONFIG.write_text(_gerar_storage_config(modo_final) + "\n", encoding="utf-8")
    CAMINHO_REPOSITORY_BRIDGE.write_text(REPOSITORY_BRIDGE_ADAPTER_PY + "\n", encoding="utf-8")
    CAMINHO_ROUTES_LEADS.write_text(ROUTES_LEADS_ADAPTER_PY + "\n", encoding="utf-8")
    CAMINHO_ROUTES_EVENTS.write_text(ROUTES_EVENTS_ADAPTER_PY + "\n", encoding="utf-8")

    if CAMINHO_README_API.exists():
        conteudo_readme = CAMINHO_README_API.read_text(encoding="utf-8")
        if "Adapter selecionável CSV/SQLite" not in conteudo_readme:
            CAMINHO_README_API.write_text(
                conteudo_readme.rstrip() + "\n\n" + README_APPEND_ADAPTER + "\n",
                encoding="utf-8",
            )

    compilacao = compilar_arquivos_adapter()
    manifesto = gerar_manifesto_api_adapter()

    return {
        "ok": compilacao["ok"],
        "mensagem": f"Adapter aplicado com storage_mode={modo_final}. Reinicie a API para carregar a configuração.",
        "storage_mode": modo_final,
        "arquivos": [str(item) for item in ARQUIVOS_ADAPTER],
        "compilacao": compilacao,
        "manifesto": manifesto,
    }


def calcular_saude_api_adapter() -> Dict[str, Any]:
    arquivos = verificar_arquivos_adapter()
    compilacao = compilar_arquivos_adapter()
    health = testar_health_api()
    sqlite_info = inspecionar_sqlite_adapter()
    storage_mode = ler_storage_mode_atual()

    try:
        sqlite_health = calcular_saude_api_sqlite()
    except Exception:
        sqlite_health = {"score_sqlite_api": 0}

    try:
        endpoint_tests = calcular_saude_api_endpoint_tests()
    except Exception:
        endpoint_tests = {"score_tests": 0, "ultima_suite_ok": False}

    score_sqlite = int(sqlite_health.get("score_sqlite_api", 0) or 0)
    score_tests = int(endpoint_tests.get("score_tests", 0) or 0)

    score = 10
    score += 14 if PASTA_API_SCAFFOLD.exists() else 0
    score += min(arquivos["existentes"] * 8, 32)
    score += 12 if compilacao["ok"] else 0
    score += 10 if storage_mode in MODOS_STORAGE else 0
    score += 8 if health["health_ok"] else 0
    score += 8 if sqlite_info["sqlite_existe"] else 0
    score += min(score_sqlite * 0.06, 6)
    score += min(score_tests * 0.06, 6)
    score = int(round(max(0, min(100, score))))

    if score >= 85 and storage_mode == "hybrid":
        decisao = "Adapter CSV/SQLite pronto em modo seguro"
        proximo_passo = "Rodar suite de endpoints com storage_mode=hybrid; depois preparar API key local."
    elif score >= 75:
        decisao = "Adapter aplicado, validar modo escolhido"
        proximo_passo = "Reinicie a API e rode a suite de endpoints para confirmar o storage_mode atual."
    elif score >= 55:
        decisao = "Adapter parcialmente preparado"
        proximo_passo = "Aplique o adapter pela aba e mantenha hybrid até a suite passar."
    else:
        decisao = "Adapter ainda não preparado"
        proximo_passo = "Aplique a bridge SQLite antes de criar modos selecionáveis."

    return {
        "score_adapter": score,
        "storage_mode": storage_mode,
        "modos_disponiveis": MODOS_STORAGE,
        "scaffold_existe": PASTA_API_SCAFFOLD.exists(),
        "arquivos": arquivos,
        "compilacao": compilacao,
        "health": health,
        "health_ok": health["health_ok"],
        "sqlite": sqlite_info,
        "score_sqlite": score_sqlite,
        "score_tests": score_tests,
        "decisao": decisao,
        "proximo_passo": proximo_passo,
    }


def gerar_manifesto_api_adapter() -> Dict[str, Any]:
    saude = calcular_saude_api_adapter()

    manifesto = {
        "versao": VERSAO_API_STORAGE_ADAPTER_VALORIS,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "saude": saude,
        "storage_mode": saude["storage_mode"],
        "modos": MODOS_STORAGE,
        "arquivos": [str(item) for item in ARQUIVOS_ADAPTER],
        "estrategia": "Adapter local selecionável antes de PostgreSQL/Supabase",
    }

    CAMINHO_MANIFESTO_API_ADAPTER.write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return manifesto


def _gerar_markdown_adapter(saude: Dict[str, Any]) -> str:
    arquivos = "\n".join(
        [
            f"- `{item['arquivo']}` — {'OK' if item['existe'] else 'Ausente'}"
            for item in saude["arquivos"]["itens"]
        ]
    )

    return f"""# Adapter Selecionável CSV/SQLite — Valoris

Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Diagnóstico

Score Adapter: {saude["score_adapter"]}/100  
Decisão: {saude["decisao"]}  
Próximo passo: {saude["proximo_passo"]}

Storage mode atual: `{saude["storage_mode"]}`  
Modos disponíveis: `{', '.join(saude["modos_disponiveis"])}`  

Scaffold existe: {saude["scaffold_existe"]}  
Arquivos OK: {saude["arquivos"]["ok"]}  
Compilação OK: {saude["compilacao"]["ok"]}  
Health OK: {saude["health_ok"]}  

## SQLite

Banco existe: {saude["sqlite"]["sqlite_existe"]}  
Leads: {saude["sqlite"]["leads"]}  
Events: {saude["sqlite"]["events"]}  

## Arquivos do adapter

{arquivos}

## Como validar

1. Aplicar `hybrid`.
2. Reiniciar a API.
3. Rodar:

```powershell
.\\scripts_api_valoris\\testar_endpoints_api_valoris.ps1
```

## Regra

Manter `hybrid` como padrão seguro até criarmos API Key e Supabase/PostgreSQL.
"""


def _injetar_css_adapter() -> None:
    st.markdown(
        """
        <style>
            .adapter-hero {
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

            .adapter-eyebrow {
                color: #d6b56d;
                font-size: 0.74rem;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                font-weight: 880;
                margin-bottom: 0.35rem;
            }

            .adapter-title {
                color: #f4f7fb;
                font-size: clamp(1.75rem, 5.4vw, 3.1rem);
                font-weight: 950;
                line-height: 1.02;
                letter-spacing: -0.058em;
                margin-bottom: 0.55rem;
            }

            .adapter-subtitle {
                color: rgba(244, 247, 251, 0.75);
                font-size: clamp(0.94rem, 2.2vw, 1.06rem);
                line-height: 1.56;
                max-width: 1020px;
            }

            .adapter-note {
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
        <div class="adapter-hero">
            <div class="adapter-eyebrow">Valoris • API Adapter • v{VERSAO_API_STORAGE_ADAPTER_VALORIS}</div>
            <div class="adapter-title">Escolha a camada de persistência sem quebrar a API.</div>
            <div class="adapter-subtitle">
                Esta etapa cria storage_mode csv, sqlite ou hybrid. O padrão seguro é hybrid,
                preparando o caminho para PostgreSQL/Supabase.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _renderizar_metricas(saude: Dict[str, Any]) -> None:
    st.markdown("### Diagnóstico Adapter")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Score Adapter", f"{saude['score_adapter']}/100")

    with col_2:
        st.metric("Storage Mode", saude["storage_mode"])

    with col_3:
        st.metric("SQLite", "OK" if saude["sqlite"]["sqlite_existe"] else "Ausente")

    with col_4:
        st.metric("Health", "OK" if saude["health_ok"] else "Offline")

    st.progress(saude["score_adapter"] / 100)

    if saude["score_adapter"] >= 85:
        st.success(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    elif saude["score_adapter"] >= 55:
        st.warning(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    else:
        st.info(f"**{saude['decisao']}** — {saude['proximo_passo']}")


def _renderizar_arquivos(saude: Dict[str, Any]) -> None:
    st.markdown("### Arquivos do adapter")

    for item in saude["arquivos"]["itens"]:
        with st.container(border=True):
            st.markdown(f"**{item['arquivo']}**")
            st.caption("OK" if item["existe"] else "Ausente")
            st.markdown(f"Tamanho: **{item['tamanho_bytes']} bytes**")


def _renderizar_compilacao(saude: Dict[str, Any]) -> None:
    st.markdown("### Compilação do adapter")

    for item in saude["compilacao"]["resultados"]:
        with st.container(border=True):
            st.markdown(f"**{item['arquivo']}** — {item['status']}")
            st.caption(item["detalhe"])


def _renderizar_historico() -> None:
    historico = carregar_decisoes_api_adapter()

    st.markdown("### Histórico de decisões API Adapter")

    if not historico:
        st.info("Ainda não há decisões salvas.")
        return

    for item in reversed(historico[-10:]):
        with st.container(border=True):
            st.markdown(f"**{item.get('decisao', 'N/D')}**")
            st.caption(item.get("data_registro", "N/D"))
            st.markdown(f"Score: {item.get('score_adapter', 'N/D')}/100")
            st.markdown(f"Storage mode: {item.get('storage_mode', 'N/D')}")
            st.markdown(f"Próximo passo: {item.get('proximo_passo', 'N/D')}")


def renderizar_api_storage_adapter_valoris() -> None:
    _injetar_css_adapter()
    _renderizar_hero()

    saude = calcular_saude_api_adapter()
    _renderizar_metricas(saude)

    st.divider()

    indice_atual = MODOS_STORAGE.index(saude["storage_mode"]) if saude["storage_mode"] in MODOS_STORAGE else 2
    modo_escolhido = st.radio(
        "Storage mode para aplicar",
        MODOS_STORAGE,
        index=indice_atual,
        horizontal=True,
        key="storage_mode_adapter_valoris",
    )

    if modo_escolhido != "hybrid":
        st.warning(
            "Para testes e evolução segura, mantenha hybrid como padrão. "
            "Use csv/sqlite isolado apenas para validações controladas."
        )
    else:
        st.success("Modo hybrid é o padrão recomendado agora: CSV como backup + SQLite como camada estruturada.")

    col_1, col_2, col_3 = st.columns(3)

    with col_1:
        if st.button("Aplicar storage mode", key="aplicar_storage_adapter"):
            resultado = aplicar_storage_adapter(modo_escolhido)
            if resultado["ok"]:
                st.success(resultado["mensagem"])
            else:
                st.warning(resultado["mensagem"])
            st.json(resultado)
            st.rerun()

    with col_2:
        if st.button("Gerar manifesto Adapter", key="gerar_manifesto_api_adapter"):
            manifesto = gerar_manifesto_api_adapter()
            st.success(f"Manifesto gerado: {CAMINHO_MANIFESTO_API_ADAPTER}")
            st.json(
                {
                    "versao": manifesto["versao"],
                    "score": manifesto["saude"]["score_adapter"],
                    "storage_mode": manifesto["storage_mode"],
                }
            )

    with col_3:
        if st.button("Salvar decisão Adapter", key="salvar_decisao_api_adapter"):
            registro = salvar_decisao_api_adapter(
                {
                    "score_adapter": saude["score_adapter"],
                    "storage_mode": saude["storage_mode"],
                    "scaffold_existe": saude["scaffold_existe"],
                    "arquivos_ok": saude["arquivos"]["ok"],
                    "health_ok": saude["health_ok"],
                    "sqlite_existe": saude["sqlite"]["sqlite_existe"],
                    "decisao": saude["decisao"],
                    "proximo_passo": saude["proximo_passo"],
                    "observacoes": "Decisão gerada pelo adapter CSV/SQLite.",
                }
            )
            st.success(f"Decisão salva: {registro['decisao']}")
            st.rerun()

    st.download_button(
        "Baixar diagnóstico API Adapter (.md)",
        data=_gerar_markdown_adapter(saude),
        file_name="api_storage_adapter_valoris.md",
        mime="text/markdown",
        key="download_api_storage_adapter",
    )

    st.download_button(
        "Baixar decisões API Adapter (.csv)",
        data=gerar_csv_decisoes_api_adapter(),
        file_name="decisoes_api_adapter_valoris.csv",
        mime="text/csv",
        key="download_decisoes_api_adapter",
    )

    st.divider()

    st.markdown("### Estado SQLite")
    st.json(saude["sqlite"])

    st.divider()
    _renderizar_arquivos(saude)

    st.divider()
    _renderizar_compilacao(saude)

    st.divider()
    _renderizar_historico()

    st.markdown(
        """
        <div class="adapter-note">
            <strong>Regra Adapter:</strong> mantenha hybrid como modo operacional seguro.
            CSV preserva inspeção simples; SQLite prepara o backend de verdade.
        </div>
        """,
        unsafe_allow_html=True,
    )


def executar_autoteste_api_storage_adapter_valoris() -> List[Dict[str, str]]:
    saude = calcular_saude_api_adapter()

    return [
        {
            "teste": "versao_storage_adapter",
            "status": "OK" if VERSAO_API_STORAGE_ADAPTER_VALORIS == "3.8.67" else "FALHA",
            "detalhe": VERSAO_API_STORAGE_ADAPTER_VALORIS,
        },
        {
            "teste": "score_adapter",
            "status": "OK" if 0 <= saude["score_adapter"] <= 100 else "FALHA",
            "detalhe": str(saude["score_adapter"]),
        },
        {
            "teste": "renderizador",
            "status": "OK" if callable(renderizar_api_storage_adapter_valoris) else "FALHA",
            "detalhe": "renderizar_api_storage_adapter_valoris",
        },
    ]
