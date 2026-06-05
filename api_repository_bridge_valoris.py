# api_repository_bridge_valoris.py

from __future__ import annotations

import csv
import json
import py_compile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

import streamlit as st

from api_smoke_tests_valoris import (
    PASTA_API_SCAFFOLD,
    URL_HEALTH,
    testar_health_api,
)
from repositorios_valoris import calcular_saude_repositorios
from gateway_dados_valoris import CONTRATOS_TABELAS_VALORIS


# ============================================================
# VALORIS
# v3.8.64 — Ponte Real entre API e Repositórios
# ------------------------------------------------------------
# Esta etapa faz a API local deixar de funcionar apenas em
# memória e passar a gravar dados reais do MVP.
#
# Objetivo:
# - atualizar api_valoris/app/services/repository_bridge.py;
# - atualizar rotas /leads e /events;
# - POST /leads grava em lista_espera_beta.csv;
# - GET /leads lê lista_espera_beta.csv;
# - POST /events grava em eventos_publicos_valoris.csv;
# - manter tudo reversível e local.
# ============================================================


VERSAO_API_REPOSITORY_BRIDGE_VALORIS = "3.8.64"

CAMINHO_DECISOES_API_BRIDGE = Path("decisoes_api_bridge_valoris.csv")
CAMINHO_MANIFESTO_API_BRIDGE = Path("manifesto_api_bridge_valoris.json")

CAMINHO_REPOSITORY_BRIDGE = Path("api_valoris/app/services/repository_bridge.py")
CAMINHO_ROUTES_LEADS = Path("api_valoris/app/routes/leads.py")
CAMINHO_ROUTES_EVENTS = Path("api_valoris/app/routes/events.py")
CAMINHO_README_API = Path("api_valoris/README.md")

ARQUIVOS_BRIDGE_API = [
    CAMINHO_REPOSITORY_BRIDGE,
    CAMINHO_ROUTES_LEADS,
    CAMINHO_ROUTES_EVENTS,
]

CAMPOS_DECISAO_API_BRIDGE = [
    "id",
    "data_registro",
    "score_bridge",
    "scaffold_existe",
    "arquivos_bridge_ok",
    "health_ok",
    "repositorio_score",
    "decisao",
    "proximo_passo",
    "observacoes",
]

REPOSITORY_BRIDGE_REAL_PY = 'from __future__ import annotations\n\nimport csv\nfrom datetime import datetime\nfrom pathlib import Path\nfrom typing import Any\nfrom uuid import uuid4\n\n\nclass RepositoryBridge:\n    """\n    Ponte local entre a FastAPI e os dados reais do MVP.\n\n    Nesta fase, a API grava em CSVs do projeto principal.\n    Futuro:\n    - trocar CSV por SQLite/PostgreSQL sem mudar as rotas;\n    - validar autenticação;\n    - separar permissões de usuários.\n    """\n\n    def __init__(self, root_path: str | None = None):\n        self.root_path = Path(root_path).resolve() if root_path else Path(__file__).resolve().parents[3]\n\n        self.leads_csv = self.root_path / "lista_espera_beta.csv"\n        self.events_csv = self.root_path / "eventos_publicos_valoris.csv"\n\n        self.lead_fields = [\n            "id",\n            "data_criacao",\n            "nome",\n            "contato",\n            "perfil",\n            "principal_dor",\n            "plano_interesse",\n            "preco_aceitavel",\n            "pagaria_agora",\n            "comentario",\n        ]\n\n        self.event_fields = [\n            "id",\n            "data_evento",\n            "sessao_id",\n            "evento",\n            "origem",\n            "contexto",\n            "perfil",\n            "valor",\n            "detalhe",\n        ]\n\n    def _clean(self, value: Any) -> str:\n        if value is None:\n            return ""\n        return str(value).strip()\n\n    def _payload_to_dict(self, payload: Any) -> dict:\n        if hasattr(payload, "model_dump"):\n            return payload.model_dump()\n        if hasattr(payload, "dict"):\n            return payload.dict()\n        if isinstance(payload, dict):\n            return payload\n        return {}\n\n    def _ensure_csv(self, path: Path, fields: list[str]) -> None:\n        if path.exists():\n            return\n\n        with path.open("w", newline="", encoding="utf-8") as file:\n            writer = csv.DictWriter(file, fieldnames=fields)\n            writer.writeheader()\n\n    def _append_csv(self, path: Path, fields: list[str], row: dict) -> dict:\n        self._ensure_csv(path, fields)\n\n        final_row = {field: self._clean(row.get(field, "")) for field in fields}\n\n        with path.open("a", newline="", encoding="utf-8") as file:\n            writer = csv.DictWriter(file, fieldnames=fields)\n            writer.writerow(final_row)\n\n        return final_row\n\n    def _read_csv(self, path: Path, fields: list[str], limit: int = 100) -> list[dict]:\n        self._ensure_csv(path, fields)\n\n        with path.open("r", newline="", encoding="utf-8") as file:\n            reader = csv.DictReader(file)\n            rows = list(reader)\n\n        return rows[-limit:]\n\n    def create_lead(self, payload: Any) -> dict:\n        data = self._payload_to_dict(payload)\n\n        row = {\n            "id": str(uuid4())[:8],\n            "data_criacao": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),\n            "nome": data.get("nome", ""),\n            "contato": data.get("contato", ""),\n            "perfil": data.get("perfil", ""),\n            "principal_dor": data.get("principal_dor", ""),\n            "plano_interesse": data.get("plano_interesse", ""),\n            "preco_aceitavel": data.get("preco_aceitavel", ""),\n            "pagaria_agora": data.get("pagaria_agora", ""),\n            "comentario": data.get("comentario", ""),\n        }\n\n        saved = self._append_csv(self.leads_csv, self.lead_fields, row)\n\n        return {\n            "ok": True,\n            "source": "csv",\n            "file": str(self.leads_csv),\n            "lead": saved,\n        }\n\n    def list_leads(self, limit: int = 100) -> dict:\n        rows = self._read_csv(self.leads_csv, self.lead_fields, limit=limit)\n\n        return {\n            "ok": True,\n            "source": "csv",\n            "file": str(self.leads_csv),\n            "total": len(rows),\n            "leads": rows,\n        }\n\n    def create_event(self, payload: Any) -> dict:\n        data = self._payload_to_dict(payload)\n\n        row = {\n            "id": str(uuid4())[:8],\n            "data_evento": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),\n            "sessao_id": data.get("sessao_id", ""),\n            "evento": data.get("evento", ""),\n            "origem": data.get("origem", ""),\n            "contexto": data.get("contexto", ""),\n            "perfil": data.get("perfil", ""),\n            "valor": data.get("valor", ""),\n            "detalhe": data.get("detalhe", ""),\n        }\n\n        saved = self._append_csv(self.events_csv, self.event_fields, row)\n\n        return {\n            "ok": True,\n            "source": "csv",\n            "file": str(self.events_csv),\n            "event": saved,\n        }'
ROUTES_LEADS_REAL_PY = 'from fastapi import APIRouter, Query\n\nfrom app.schemas.lead import LeadCreate\nfrom app.services.repository_bridge import RepositoryBridge\n\n\nrouter = APIRouter()\nrepository = RepositoryBridge()\n\n\n@router.post("")\ndef create_lead(payload: LeadCreate):\n    result = repository.create_lead(payload)\n\n    return {\n        "ok": result["ok"],\n        "message": "Lead salvo nos dados reais da Valoris.",\n        "source": result["source"],\n        "file": result["file"],\n        "lead": result["lead"],\n    }\n\n\n@router.get("")\ndef list_leads(limit: int = Query(default=100, ge=1, le=500)):\n    return repository.list_leads(limit=limit)'
ROUTES_EVENTS_REAL_PY = 'from fastapi import APIRouter\n\nfrom app.schemas.event import EventCreate\nfrom app.services.repository_bridge import RepositoryBridge\n\n\nrouter = APIRouter()\nrepository = RepositoryBridge()\n\n\n@router.post("")\ndef create_event(payload: EventCreate):\n    result = repository.create_event(payload)\n\n    return {\n        "ok": result["ok"],\n        "message": "Evento salvo nos dados reais da Valoris.",\n        "source": result["source"],\n        "file": result["file"],\n        "event": result["event"],\n    }'
README_APPEND_BRIDGE = '## Ponte real com dados do MVP\n\nA partir da v3.8.64, os endpoints iniciais deixam de responder apenas em memória:\n\n- `POST /leads` grava em `../lista_espera_beta.csv`\n- `GET /leads` lê `../lista_espera_beta.csv`\n- `POST /events` grava em `../eventos_publicos_valoris.csv`\n\nEssa ponte ainda é local e reversível. O próximo passo natural será trocar o CSV por SQLite/PostgreSQL mantendo as mesmas rotas.'


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


def carregar_decisoes_api_bridge() -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_DECISOES_API_BRIDGE, CAMPOS_DECISAO_API_BRIDGE)

    with CAMINHO_DECISOES_API_BRIDGE.open("r", newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def gerar_csv_decisoes_api_bridge() -> str:
    _garantir_csv(CAMINHO_DECISOES_API_BRIDGE, CAMPOS_DECISAO_API_BRIDGE)
    return CAMINHO_DECISOES_API_BRIDGE.read_text(encoding="utf-8")


def salvar_decisao_api_bridge(decisao: Dict[str, Any]) -> Dict[str, str]:
    _garantir_csv(CAMINHO_DECISOES_API_BRIDGE, CAMPOS_DECISAO_API_BRIDGE)

    registro = {
        "id": str(uuid4())[:8],
        "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score_bridge": str(decisao.get("score_bridge", "")),
        "scaffold_existe": str(decisao.get("scaffold_existe", "")),
        "arquivos_bridge_ok": str(decisao.get("arquivos_bridge_ok", "")),
        "health_ok": str(decisao.get("health_ok", "")),
        "repositorio_score": str(decisao.get("repositorio_score", "")),
        "decisao": _limpar_texto(decisao.get("decisao", "")),
        "proximo_passo": _limpar_texto(decisao.get("proximo_passo", "")),
        "observacoes": _limpar_texto(decisao.get("observacoes", "")),
    }

    with CAMINHO_DECISOES_API_BRIDGE.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISAO_API_BRIDGE)
        escritor.writerow(registro)

    return registro


def verificar_arquivos_bridge() -> Dict[str, Any]:
    itens = []

    for caminho in ARQUIVOS_BRIDGE_API:
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


def compilar_arquivos_bridge() -> Dict[str, Any]:
    resultados = []

    for caminho in ARQUIVOS_BRIDGE_API:
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


def aplicar_ponte_api_repositorios() -> Dict[str, Any]:
    if not PASTA_API_SCAFFOLD.exists():
        return {
            "ok": False,
            "mensagem": "A pasta api_valoris não existe. Gere o scaffold antes.",
            "arquivos": [],
        }

    CAMINHO_REPOSITORY_BRIDGE.parent.mkdir(parents=True, exist_ok=True)
    CAMINHO_ROUTES_LEADS.parent.mkdir(parents=True, exist_ok=True)
    CAMINHO_ROUTES_EVENTS.parent.mkdir(parents=True, exist_ok=True)

    CAMINHO_REPOSITORY_BRIDGE.write_text(REPOSITORY_BRIDGE_REAL_PY + "\n", encoding="utf-8")
    CAMINHO_ROUTES_LEADS.write_text(ROUTES_LEADS_REAL_PY + "\n", encoding="utf-8")
    CAMINHO_ROUTES_EVENTS.write_text(ROUTES_EVENTS_REAL_PY + "\n", encoding="utf-8")

    if CAMINHO_README_API.exists():
        conteudo_readme = CAMINHO_README_API.read_text(encoding="utf-8")
        if "Ponte real com dados do MVP" not in conteudo_readme:
            CAMINHO_README_API.write_text(
                conteudo_readme.rstrip() + "\n\n" + README_APPEND_BRIDGE + "\n",
                encoding="utf-8",
            )

    compilacao = compilar_arquivos_bridge()
    manifesto = gerar_manifesto_api_bridge()

    return {
        "ok": compilacao["ok"],
        "mensagem": "Ponte API ↔ Repositórios aplicada.",
        "arquivos": [str(item) for item in ARQUIVOS_BRIDGE_API],
        "compilacao": compilacao,
        "manifesto": manifesto,
    }


def calcular_saude_api_bridge() -> Dict[str, Any]:
    arquivos = verificar_arquivos_bridge()
    compilacao = compilar_arquivos_bridge()
    health = testar_health_api()

    try:
        saude_repositorios = calcular_saude_repositorios()
    except Exception:
        saude_repositorios = {"score_repositorio": 0}

    repositorio_score = int(saude_repositorios.get("score_repositorio", 0) or 0)

    contratos = {
        "leads": CONTRATOS_TABELAS_VALORIS.get("leads", {}),
        "events": CONTRATOS_TABELAS_VALORIS.get("events", {}),
    }

    score = 15
    score += 20 if PASTA_API_SCAFFOLD.exists() else 0
    score += min(arquivos["existentes"] * 12, 36)
    score += 18 if compilacao["ok"] else 0
    score += min(repositorio_score * 0.14, 14)
    score += 12 if health["health_ok"] else 0
    score = int(round(max(0, min(100, score))))

    if score >= 85 and health["health_ok"]:
        decisao = "Ponte API ↔ dados reais validada"
        proximo_passo = "Testar POST /leads e POST /events com a API rodando; depois criar testes automatizados dos endpoints."
    elif score >= 70:
        decisao = "Ponte aplicada, falta validar API rodando"
        proximo_passo = "Rode a API local, teste /health e envie POST /leads para confirmar gravação no CSV."
    elif score >= 50:
        decisao = "Ponte parcialmente preparada"
        proximo_passo = "Aplique a ponte pela aba e recompile os arquivos do scaffold."
    else:
        decisao = "Ponte ainda não preparada"
        proximo_passo = "Gere api_valoris/ pela aba API Scaffold antes de aplicar a ponte."

    return {
        "score_bridge": score,
        "scaffold_existe": PASTA_API_SCAFFOLD.exists(),
        "arquivos": arquivos,
        "compilacao": compilacao,
        "health": health,
        "health_ok": health["health_ok"],
        "repositorio_score": repositorio_score,
        "contratos": contratos,
        "decisao": decisao,
        "proximo_passo": proximo_passo,
    }


def gerar_manifesto_api_bridge() -> Dict[str, Any]:
    saude = calcular_saude_api_bridge()

    manifesto = {
        "versao": VERSAO_API_REPOSITORY_BRIDGE_VALORIS,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "saude": saude,
        "rotas_afetadas": [
            "POST /leads",
            "GET /leads",
            "POST /events",
        ],
        "arquivos_bridge": [str(item) for item in ARQUIVOS_BRIDGE_API],
        "dados_reais": {
            "leads": "lista_espera_beta.csv",
            "events": "eventos_publicos_valoris.csv",
        },
    }

    CAMINHO_MANIFESTO_API_BRIDGE.write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return manifesto


def _gerar_markdown_bridge(saude: Dict[str, Any]) -> str:
    arquivos = "\n".join(
        [
            f"- `{item['arquivo']}` — {'OK' if item['existe'] else 'Ausente'}"
            for item in saude["arquivos"]["itens"]
        ]
    )

    erros = "\n".join(
        [
            f"- `{item['arquivo']}` — {item['detalhe']}"
            for item in saude["compilacao"]["erros"]
        ]
    ) or "- Nenhum"

    return f"""# Ponte API ↔ Repositórios — Valoris

Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Diagnóstico

Score Bridge: {saude["score_bridge"]}/100  
Decisão: {saude["decisao"]}  
Próximo passo: {saude["proximo_passo"]}

Scaffold existe: {saude["scaffold_existe"]}  
Arquivos bridge OK: {saude["arquivos"]["ok"]}  
Compilação OK: {saude["compilacao"]["ok"]}  
Health OK: {saude["health_ok"]}  
Score Repositórios: {saude["repositorio_score"]}/100  

## Rotas conectadas

- `POST /leads` → `lista_espera_beta.csv`
- `GET /leads` → `lista_espera_beta.csv`
- `POST /events` → `eventos_publicos_valoris.csv`

## Arquivos alterados na API local

{arquivos}

## Erros de compilação

{erros}

## Teste manual

```powershell
.\\scripts_api_valoris\\rodar_api_valoris.ps1
```

Em outro terminal:

```powershell
.\\scripts_api_valoris\\testar_api_valoris.ps1
```

## Regra

Esta ponte ainda é local e reversível. Primeiro validamos CSV; depois trocamos por SQLite/PostgreSQL.
"""


def _injetar_css_bridge() -> None:
    st.markdown(
        """
        <style>
            .bridge-hero {
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

            .bridge-eyebrow {
                color: #d6b56d;
                font-size: 0.74rem;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                font-weight: 880;
                margin-bottom: 0.35rem;
            }

            .bridge-title {
                color: #f4f7fb;
                font-size: clamp(1.75rem, 5.4vw, 3.1rem);
                font-weight: 950;
                line-height: 1.02;
                letter-spacing: -0.058em;
                margin-bottom: 0.55rem;
            }

            .bridge-subtitle {
                color: rgba(244, 247, 251, 0.75);
                font-size: clamp(0.94rem, 2.2vw, 1.06rem);
                line-height: 1.56;
                max-width: 1020px;
            }

            .bridge-note {
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
        <div class="bridge-hero">
            <div class="bridge-eyebrow">Valoris • API Bridge • v{VERSAO_API_REPOSITORY_BRIDGE_VALORIS}</div>
            <div class="bridge-title">Conecte a API aos dados reais.</div>
            <div class="bridge-subtitle">
                Esta etapa faz leads e eventos deixarem de viver apenas em memória e passarem a gravar
                nos CSVs reais do MVP, mantendo a ponte pronta para SQLite/PostgreSQL.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _renderizar_metricas(saude: Dict[str, Any]) -> None:
    st.markdown("### Diagnóstico da ponte")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Score Bridge", f"{saude['score_bridge']}/100")

    with col_2:
        st.metric("Scaffold", "OK" if saude["scaffold_existe"] else "Ausente")

    with col_3:
        st.metric("Arquivos", f"{saude['arquivos']['existentes']}/{saude['arquivos']['total']}")

    with col_4:
        st.metric("Health", "OK" if saude["health_ok"] else "Offline")

    st.progress(saude["score_bridge"] / 100)

    if saude["score_bridge"] >= 80:
        st.success(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    elif saude["score_bridge"] >= 50:
        st.warning(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    else:
        st.info(f"**{saude['decisao']}** — {saude['proximo_passo']}")


def _renderizar_arquivos(saude: Dict[str, Any]) -> None:
    st.markdown("### Arquivos da ponte")

    for item in saude["arquivos"]["itens"]:
        with st.container(border=True):
            st.markdown(f"**{item['arquivo']}**")
            st.caption("OK" if item["existe"] else "Ausente")
            st.markdown(f"Tamanho: **{item['tamanho_bytes']} bytes**")


def _renderizar_compilacao(saude: Dict[str, Any]) -> None:
    st.markdown("### Compilação da ponte")

    for item in saude["compilacao"]["resultados"]:
        with st.container(border=True):
            st.markdown(f"**{item['arquivo']}** — {item['status']}")
            st.caption(item["detalhe"])


def _renderizar_historico() -> None:
    historico = carregar_decisoes_api_bridge()

    st.markdown("### Histórico de decisões API Bridge")

    if not historico:
        st.info("Ainda não há decisões salvas.")
        return

    for item in reversed(historico[-10:]):
        with st.container(border=True):
            st.markdown(f"**{item.get('decisao', 'N/D')}**")
            st.caption(item.get("data_registro", "N/D"))
            st.markdown(f"Score: {item.get('score_bridge', 'N/D')}/100")
            st.markdown(f"Próximo passo: {item.get('proximo_passo', 'N/D')}")


def renderizar_api_repository_bridge_valoris() -> None:
    _injetar_css_bridge()
    _renderizar_hero()

    saude = calcular_saude_api_bridge()
    _renderizar_metricas(saude)

    st.divider()

    col_1, col_2, col_3 = st.columns(3)

    with col_1:
        if st.button("Aplicar ponte API ↔ dados reais", key="aplicar_ponte_api_repositorios"):
            resultado = aplicar_ponte_api_repositorios()
            if resultado["ok"]:
                st.success(resultado["mensagem"])
            else:
                st.warning(resultado["mensagem"])
            st.json(resultado)
            st.rerun()

    with col_2:
        if st.button("Gerar manifesto Bridge", key="gerar_manifesto_api_bridge"):
            manifesto = gerar_manifesto_api_bridge()
            st.success(f"Manifesto gerado: {CAMINHO_MANIFESTO_API_BRIDGE}")
            st.json(
                {
                    "versao": manifesto["versao"],
                    "score": manifesto["saude"]["score_bridge"],
                    "rotas": manifesto["rotas_afetadas"],
                }
            )

    with col_3:
        if st.button("Salvar decisão Bridge", key="salvar_decisao_api_bridge"):
            registro = salvar_decisao_api_bridge(
                {
                    "score_bridge": saude["score_bridge"],
                    "scaffold_existe": saude["scaffold_existe"],
                    "arquivos_bridge_ok": saude["arquivos"]["ok"],
                    "health_ok": saude["health_ok"],
                    "repositorio_score": saude["repositorio_score"],
                    "decisao": saude["decisao"],
                    "proximo_passo": saude["proximo_passo"],
                    "observacoes": "Decisão gerada pela ponte API ↔ Repositórios.",
                }
            )
            st.success(f"Decisão salva: {registro['decisao']}")
            st.rerun()

    st.download_button(
        "Baixar diagnóstico API Bridge (.md)",
        data=_gerar_markdown_bridge(saude),
        file_name="api_repository_bridge_valoris.md",
        mime="text/markdown",
        key="download_api_bridge_valoris",
    )

    st.download_button(
        "Baixar decisões API Bridge (.csv)",
        data=gerar_csv_decisoes_api_bridge(),
        file_name="decisoes_api_bridge_valoris.csv",
        mime="text/csv",
        key="download_decisoes_api_bridge",
    )

    st.divider()

    st.markdown("### Rotas conectadas")
    st.code(
        """POST /leads  -> lista_espera_beta.csv
GET  /leads  -> lista_espera_beta.csv
POST /events -> eventos_publicos_valoris.csv""",
        language="text",
    )

    st.divider()
    _renderizar_arquivos(saude)

    st.divider()
    _renderizar_compilacao(saude)

    st.divider()
    _renderizar_historico()

    st.markdown(
        """
        <div class="bridge-note">
            <strong>Regra Bridge:</strong> a API agora pode começar a conversar com dados reais,
            mas ainda de forma local e reversível. Primeiro validamos CSV; depois conectamos banco.
        </div>
        """,
        unsafe_allow_html=True,
    )


def executar_autoteste_api_repository_bridge_valoris() -> List[Dict[str, str]]:
    saude = calcular_saude_api_bridge()

    return [
        {
            "teste": "versao_bridge",
            "status": "OK" if VERSAO_API_REPOSITORY_BRIDGE_VALORIS == "3.8.64" else "FALHA",
            "detalhe": VERSAO_API_REPOSITORY_BRIDGE_VALORIS,
        },
        {
            "teste": "score_bridge",
            "status": "OK" if 0 <= saude["score_bridge"] <= 100 else "FALHA",
            "detalhe": str(saude["score_bridge"]),
        },
        {
            "teste": "renderizador",
            "status": "OK" if callable(renderizar_api_repository_bridge_valoris) else "FALHA",
            "detalhe": "renderizar_api_repository_bridge_valoris",
        },
    ]
