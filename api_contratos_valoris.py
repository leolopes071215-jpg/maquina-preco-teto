# api_contratos_valoris.py

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

import streamlit as st

from postgres_supabase_valoris import calcular_prontidao_postgres
from repositorios_valoris import calcular_saude_repositorios
from piloto_sqlite_valoris import calcular_saude_sqlite


# ============================================================
# VALORIS
# v3.8.61 — Blueprint FastAPI e Contratos de Endpoints
# ------------------------------------------------------------
# Esta etapa ainda não liga uma API real.
#
# Objetivo:
# - desenhar os contratos do backend futuro;
# - mapear endpoints, payloads e respostas;
# - preparar a separação entre Streamlit e motor;
# - gerar esqueleto FastAPI para a próxima fase;
# - evitar criar API antes de dados/repositórios estarem maduros.
# ============================================================


VERSAO_API_CONTRATOS_VALORIS = "3.8.61"

CAMINHO_DECISOES_API = Path("decisoes_api_valoris.csv")
CAMINHO_MANIFESTO_API = Path("manifesto_api_valoris.json")
CAMINHO_OPENAPI_RASCUNHO = Path("openapi_valoris_rascunho.json")
CAMINHO_FASTAPI_BLUEPRINT = Path("valoris_fastapi_blueprint.py")

CAMPOS_DECISAO_API = [
    "id",
    "data_registro",
    "score_api",
    "score_sqlite",
    "score_repositorio",
    "score_postgres",
    "endpoints_mapeados",
    "decisao",
    "proximo_passo",
    "observacoes",
]


SCHEMAS_API_VALORIS: Dict[str, Dict[str, Any]] = {
    "LeadCreate": {
        "descricao": "Payload para cadastro de lead/lista beta.",
        "campos": {
            "nome": "str",
            "contato": "str",
            "perfil": "str | None",
            "principal_dor": "str | None",
            "plano_interesse": "str | None",
            "preco_aceitavel": "str | None",
            "pagaria_agora": "str | None",
            "comentario": "str | None",
        },
    },
    "EventCreate": {
        "descricao": "Payload para registrar evento de uso.",
        "campos": {
            "sessao_id": "str | None",
            "evento": "str",
            "origem": "str | None",
            "contexto": "str | None",
            "perfil": "str | None",
            "valor": "str | None",
            "detalhe": "str | None",
        },
    },
    "ValuationRequest": {
        "descricao": "Payload futuro para executar valuation.",
        "campos": {
            "ticker": "str",
            "preco_atual": "float | None",
            "lpa": "float | None",
            "fcl_por_acao": "float | None",
            "dividendo_esperado": "float | None",
            "yield_alvo": "float | None",
            "margem_seguranca": "float | None",
            "premissas": "dict | None",
        },
    },
    "ReportRequest": {
        "descricao": "Payload para gerar relatório a partir de valuation.",
        "campos": {
            "valuation_id": "str | None",
            "ticker": "str",
            "tipo": "str",
            "linguagem": "str | None",
            "incluir_auditoria": "bool",
        },
    },
    "FounderUpdate": {
        "descricao": "Payload para atualizar usuário fundador.",
        "campos": {
            "nome": "str",
            "contato": "str",
            "plano": "str | None",
            "status_pagamento": "str | None",
            "status_acesso": "str | None",
            "etapa_onboarding": "str | None",
            "feedback": "str | None",
        },
    },
}


ENDPOINTS_API_VALORIS: List[Dict[str, Any]] = [
    {
        "metodo": "GET",
        "rota": "/health",
        "tag": "system",
        "descricao": "Verificar se a API está viva.",
        "request": None,
        "response": "HealthResponse",
        "prioridade": "Alta",
        "fase": "API inicial",
    },
    {
        "metodo": "POST",
        "rota": "/events",
        "tag": "analytics",
        "descricao": "Registrar evento de uso da Valoris.",
        "request": "EventCreate",
        "response": "EventResponse",
        "prioridade": "Alta",
        "fase": "API inicial",
    },
    {
        "metodo": "POST",
        "rota": "/leads",
        "tag": "growth",
        "descricao": "Cadastrar lead da lista beta.",
        "request": "LeadCreate",
        "response": "LeadResponse",
        "prioridade": "Alta",
        "fase": "API inicial",
    },
    {
        "metodo": "GET",
        "rota": "/leads",
        "tag": "growth",
        "descricao": "Listar leads para painel fundador.",
        "request": None,
        "response": "list[LeadResponse]",
        "prioridade": "Média",
        "fase": "API inicial",
    },
    {
        "metodo": "POST",
        "rota": "/valuation",
        "tag": "valuation",
        "descricao": "Executar valuation usando o motor da Valoris.",
        "request": "ValuationRequest",
        "response": "ValuationResponse",
        "prioridade": "Alta",
        "fase": "API núcleo",
    },
    {
        "metodo": "GET",
        "rota": "/valuation/{valuation_id}",
        "tag": "valuation",
        "descricao": "Buscar uma análise salva.",
        "request": None,
        "response": "ValuationResponse",
        "prioridade": "Média",
        "fase": "API núcleo",
    },
    {
        "metodo": "POST",
        "rota": "/reports",
        "tag": "reports",
        "descricao": "Gerar relatório a partir de valuation.",
        "request": "ReportRequest",
        "response": "ReportResponse",
        "prioridade": "Alta",
        "fase": "API núcleo",
    },
    {
        "metodo": "POST",
        "rota": "/founders",
        "tag": "founders",
        "descricao": "Registrar ou atualizar fundador beta.",
        "request": "FounderUpdate",
        "response": "FounderResponse",
        "prioridade": "Média",
        "fase": "API operação",
    },
    {
        "metodo": "GET",
        "rota": "/me",
        "tag": "auth",
        "descricao": "Buscar usuário autenticado no futuro.",
        "request": None,
        "response": "UserResponse",
        "prioridade": "Baixa",
        "fase": "API pós-auth",
    },
    {
        "metodo": "POST",
        "rota": "/payments/checkout",
        "tag": "payments",
        "descricao": "Criar checkout quando monetização estiver validada.",
        "request": "CheckoutRequest",
        "response": "CheckoutResponse",
        "prioridade": "Baixa",
        "fase": "API monetização",
    },
]


FASES_API_VALORIS = [
    {
        "fase": "1",
        "nome": "API de sistema e eventos",
        "objetivo": "Começar simples: healthcheck, eventos e leads.",
        "criterio": "Repositórios funcionando e dados sincronizados.",
    },
    {
        "fase": "2",
        "nome": "API do núcleo Valoris",
        "objetivo": "Expor valuation e relatório.",
        "criterio": "Motor de valuation estável e relatório útil.",
    },
    {
        "fase": "3",
        "nome": "API de operação",
        "objetivo": "Expor founders, validações e decisões internas.",
        "criterio": "Beta fundador com uso real.",
    },
    {
        "fase": "4",
        "nome": "API autenticada",
        "objetivo": "Adicionar usuários, planos e área logada.",
        "criterio": "Banco externo e autenticação definidos.",
    },
    {
        "fase": "5",
        "nome": "API monetizável",
        "objetivo": "Checkout, permissões, planos e histórico premium.",
        "criterio": "Pagamento manual validado.",
    },
]


FASTAPI_BLUEPRINT = """
# valoris_fastapi_blueprint.py
# Rascunho futuro. Não usar em produção ainda.

from fastapi import FastAPI

app = FastAPI(
    title="Valoris API",
    version="0.1.0",
    description="Backend futuro da Valoris."
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "valoris-api"}


@app.post("/events")
def create_event(payload: dict):
    # Futuro: chamar repositório de eventos.
    return {"ok": True, "event": payload}


@app.post("/leads")
def create_lead(payload: dict):
    # Futuro: chamar repositório de leads.
    return {"ok": True, "lead": payload}


@app.post("/valuation")
def create_valuation(payload: dict):
    # Futuro: chamar motor de valuation.
    return {"ok": True, "valuation": payload}


@app.post("/reports")
def create_report(payload: dict):
    # Futuro: chamar motor de relatórios.
    return {"ok": True, "report": payload}
""".strip()


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


def carregar_decisoes_api() -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_DECISOES_API, CAMPOS_DECISAO_API)

    with CAMINHO_DECISOES_API.open("r", newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        return list(leitor)


def gerar_csv_decisoes_api() -> str:
    _garantir_csv(CAMINHO_DECISOES_API, CAMPOS_DECISAO_API)
    return CAMINHO_DECISOES_API.read_text(encoding="utf-8")


def salvar_decisao_api(decisao: Dict[str, Any]) -> Dict[str, str]:
    _garantir_csv(CAMINHO_DECISOES_API, CAMPOS_DECISAO_API)

    registro = {
        "id": str(uuid4())[:8],
        "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score_api": str(decisao.get("score_api", "")),
        "score_sqlite": str(decisao.get("score_sqlite", "")),
        "score_repositorio": str(decisao.get("score_repositorio", "")),
        "score_postgres": str(decisao.get("score_postgres", "")),
        "endpoints_mapeados": str(decisao.get("endpoints_mapeados", "")),
        "decisao": _limpar_texto(decisao.get("decisao", "")),
        "proximo_passo": _limpar_texto(decisao.get("proximo_passo", "")),
        "observacoes": _limpar_texto(decisao.get("observacoes", "")),
    }

    with CAMINHO_DECISOES_API.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISAO_API)
        escritor.writerow(registro)

    return registro


def gerar_openapi_rascunho() -> Dict[str, Any]:
    paths: Dict[str, Any] = {}

    for endpoint in ENDPOINTS_API_VALORIS:
        metodo = endpoint["metodo"].lower()
        rota = endpoint["rota"]

        paths.setdefault(rota, {})
        paths[rota][metodo] = {
            "tags": [endpoint["tag"]],
            "summary": endpoint["descricao"],
            "x-prioridade": endpoint["prioridade"],
            "x-fase": endpoint["fase"],
            "responses": {
                "200": {
                    "description": endpoint["response"],
                }
            },
        }

        if endpoint["request"]:
            paths[rota][metodo]["requestBody"] = {
                "description": endpoint["request"],
                "required": True,
            }

    spec = {
        "openapi": "3.1.0",
        "info": {
            "title": "Valoris API",
            "version": "0.1.0",
            "description": "Rascunho de contratos da futura API da Valoris.",
        },
        "paths": paths,
        "x-schemas-valoris": SCHEMAS_API_VALORIS,
    }

    CAMINHO_OPENAPI_RASCUNHO.write_text(
        json.dumps(spec, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return spec


def gerar_fastapi_blueprint() -> str:
    CAMINHO_FASTAPI_BLUEPRINT.write_text(FASTAPI_BLUEPRINT + "\n", encoding="utf-8")
    return FASTAPI_BLUEPRINT


def calcular_prontidao_api() -> Dict[str, Any]:
    try:
        saude_sqlite = calcular_saude_sqlite()
    except Exception:
        saude_sqlite = {"score_sqlite": 0}

    try:
        saude_repositorios = calcular_saude_repositorios()
    except Exception:
        saude_repositorios = {"score_repositorio": 0}

    try:
        prontidao_postgres = calcular_prontidao_postgres()
    except Exception:
        prontidao_postgres = {"score_prontidao": 0}

    sqlite_score = int(saude_sqlite.get("score_sqlite", 0) or 0)
    repositorio_score = int(saude_repositorios.get("score_repositorio", 0) or 0)
    postgres_score = int(prontidao_postgres.get("score_prontidao", 0) or 0)

    endpoints_mapeados = len(ENDPOINTS_API_VALORIS)
    schemas_mapeados = len(SCHEMAS_API_VALORIS)

    score = 20
    score += min(sqlite_score * 0.18, 18)
    score += min(repositorio_score * 0.28, 28)
    score += min(postgres_score * 0.18, 18)
    score += min(endpoints_mapeados * 3, 24)
    score += min(schemas_mapeados * 2, 12)
    score = int(round(max(0, min(100, score))))

    if score >= 82 and repositorio_score >= 70:
        decisao = "Pronto para scaffold FastAPI"
        proximo_passo = "Criar pasta api/ com app FastAPI mínimo e healthcheck, ainda sem substituir Streamlit."
    elif score >= 65:
        decisao = "API bem desenhada, mas aguarde execução"
        proximo_passo = "Revisar contratos, sincronizar SQLite/Repositórios e preparar FastAPI em branch separada."
    elif score >= 45:
        decisao = "Contratos úteis, execução prematura"
        proximo_passo = "Use esta aba para amadurecer endpoints antes de instalar FastAPI."
    else:
        decisao = "Ainda cedo para API"
        proximo_passo = "Fortaleça dados, repositórios e produto antes de separar backend."

    return {
        "score_api": score,
        "score_sqlite": sqlite_score,
        "score_repositorio": repositorio_score,
        "score_postgres": postgres_score,
        "endpoints_mapeados": endpoints_mapeados,
        "schemas_mapeados": schemas_mapeados,
        "decisao": decisao,
        "proximo_passo": proximo_passo,
    }


def gerar_manifesto_api() -> Dict[str, Any]:
    prontidao = calcular_prontidao_api()
    openapi = gerar_openapi_rascunho()

    manifesto = {
        "versao": VERSAO_API_CONTRATOS_VALORIS,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "prontidao": prontidao,
        "fases": FASES_API_VALORIS,
        "endpoints": ENDPOINTS_API_VALORIS,
        "schemas": SCHEMAS_API_VALORIS,
        "openapi_paths": list(openapi["paths"].keys()),
    }

    CAMINHO_MANIFESTO_API.write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return manifesto


def _gerar_markdown_api(prontidao: Dict[str, Any]) -> str:
    endpoints = "\n".join(
        [
            f"| {item['metodo']} | `{item['rota']}` | {item['tag']} | {item['prioridade']} | {item['fase']} | {item['descricao']} |"
            for item in ENDPOINTS_API_VALORIS
        ]
    )

    schemas = "\n".join(
        [
            f"### {nome}\n{schema['descricao']}\n\nCampos: `{', '.join(schema['campos'].keys())}`\n"
            for nome, schema in SCHEMAS_API_VALORIS.items()
        ]
    )

    fases = "\n".join(
        [
            f"### Fase {item['fase']} — {item['nome']}\nObjetivo: {item['objetivo']}\nCritério: {item['criterio']}\n"
            for item in FASES_API_VALORIS
        ]
    )

    return f"""# Blueprint FastAPI — Valoris

Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Diagnóstico

Score API: {prontidao["score_api"]}/100  
Decisão: {prontidao["decisao"]}  
Próximo passo: {prontidao["proximo_passo"]}

Score SQLite: {prontidao["score_sqlite"]}/100  
Score Repositório: {prontidao["score_repositorio"]}/100  
Score PostgreSQL: {prontidao["score_postgres"]}/100  

Endpoints mapeados: {prontidao["endpoints_mapeados"]}  
Schemas mapeados: {prontidao["schemas_mapeados"]}  

## Endpoints

| Método | Rota | Tag | Prioridade | Fase | Descrição |
|---|---|---|---|---|---|
{endpoints}

## Schemas

{schemas}

## Fases

{fases}

## Blueprint FastAPI

```python
{FASTAPI_BLUEPRINT}
```

## Regra

A API não deve nascer para substituir o Streamlit imediatamente.  
Ela deve nascer como backend paralelo, começando por healthcheck, events e leads.
"""


def _injetar_css_api() -> None:
    st.markdown(
        """
        <style>
            .api-hero {
                padding: clamp(1.18rem, 3vw, 2rem);
                border-radius: 30px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    radial-gradient(circle at top left, rgba(214, 181, 109, 0.26), transparent 30%),
                    radial-gradient(circle at bottom right, rgba(74, 144, 226, 0.22), transparent 34%),
                    linear-gradient(135deg, rgba(8, 15, 27, 0.99), rgba(5, 9, 18, 0.99));
                box-shadow: 0 18px 58px rgba(0, 0, 0, 0.31);
                margin-bottom: 1rem;
            }

            .api-eyebrow {
                color: #d6b56d;
                font-size: 0.74rem;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                font-weight: 880;
                margin-bottom: 0.35rem;
            }

            .api-title {
                color: #f4f7fb;
                font-size: clamp(1.75rem, 5.4vw, 3.1rem);
                font-weight: 950;
                line-height: 1.02;
                letter-spacing: -0.058em;
                margin-bottom: 0.55rem;
            }

            .api-subtitle {
                color: rgba(244, 247, 251, 0.75);
                font-size: clamp(0.94rem, 2.2vw, 1.06rem);
                line-height: 1.56;
                max-width: 1020px;
            }

            .api-note {
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
        <div class="api-hero">
            <div class="api-eyebrow">Valoris • API • v{VERSAO_API_CONTRATOS_VALORIS}</div>
            <div class="api-title">Desenhe a API antes de programá-la.</div>
            <div class="api-subtitle">
                Esta etapa mapeia endpoints, schemas, fases e um blueprint FastAPI para separar
                o cérebro da Valoris da interface Streamlit na hora certa.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _renderizar_metricas(prontidao: Dict[str, Any]) -> None:
    st.markdown("### Diagnóstico da API")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Score API", f"{prontidao['score_api']}/100")

    with col_2:
        st.metric("Endpoints", prontidao["endpoints_mapeados"])

    with col_3:
        st.metric("Schemas", prontidao["schemas_mapeados"])

    with col_4:
        st.metric("Repo", f"{prontidao['score_repositorio']}/100")

    st.progress(prontidao["score_api"] / 100)

    if prontidao["score_api"] >= 70:
        st.success(f"**{prontidao['decisao']}** — {prontidao['proximo_passo']}")
    elif prontidao["score_api"] >= 45:
        st.warning(f"**{prontidao['decisao']}** — {prontidao['proximo_passo']}")
    else:
        st.info(f"**{prontidao['decisao']}** — {prontidao['proximo_passo']}")


def _renderizar_endpoints() -> None:
    st.markdown("### Endpoints planejados")

    for endpoint in ENDPOINTS_API_VALORIS:
        with st.container(border=True):
            st.markdown(f"**{endpoint['metodo']} {endpoint['rota']}**")
            st.caption(f"{endpoint['tag']} • {endpoint['prioridade']} • {endpoint['fase']}")
            st.markdown(endpoint["descricao"])
            st.code(
                f"request: {endpoint['request'] or 'None'}\nresponse: {endpoint['response']}",
                language="text",
            )


def _renderizar_schemas() -> None:
    st.markdown("### Schemas planejados")

    for nome, schema in SCHEMAS_API_VALORIS.items():
        with st.container(border=True):
            st.markdown(f"**{nome}**")
            st.caption(schema["descricao"])
            st.json(schema["campos"])


def _renderizar_fases() -> None:
    st.markdown("### Fases da API")

    for fase in FASES_API_VALORIS:
        with st.container(border=True):
            st.markdown(f"**Fase {fase['fase']} — {fase['nome']}**")
            st.caption(fase["objetivo"])
            st.markdown(f"Critério: {fase['criterio']}")


def _renderizar_blueprint() -> None:
    st.markdown("### Blueprint FastAPI")
    st.code(FASTAPI_BLUEPRINT, language="python")


def _renderizar_historico() -> None:
    historico = carregar_decisoes_api()

    st.markdown("### Histórico de decisões API")

    if not historico:
        st.info("Ainda não há decisões de API salvas.")
        return

    for item in reversed(historico[-10:]):
        with st.container(border=True):
            st.markdown(f"**{item.get('decisao', 'N/D')}**")
            st.caption(item.get("data_registro", "N/D"))
            st.markdown(
                f"Score: {item.get('score_api', 'N/D')}/100 • Endpoints: {item.get('endpoints_mapeados', 'N/D')}"
            )
            st.markdown(f"Próximo passo: {item.get('proximo_passo', 'N/D')}")


def renderizar_api_contratos_valoris() -> None:
    _injetar_css_api()
    _renderizar_hero()

    prontidao = calcular_prontidao_api()
    _renderizar_metricas(prontidao)

    st.divider()

    col_1, col_2, col_3 = st.columns(3)

    with col_1:
        if st.button("Gerar OpenAPI rascunho", key="gerar_openapi_valoris"):
            spec = gerar_openapi_rascunho()
            st.success(f"OpenAPI gerado: {CAMINHO_OPENAPI_RASCUNHO}")
            st.json({"paths": list(spec["paths"].keys())})

    with col_2:
        if st.button("Gerar blueprint FastAPI", key="gerar_fastapi_blueprint_valoris"):
            conteudo = gerar_fastapi_blueprint()
            st.success(f"Blueprint gerado: {CAMINHO_FASTAPI_BLUEPRINT}")
            st.code(conteudo, language="python")

    with col_3:
        if st.button("Salvar decisão API", key="salvar_decisao_api_valoris"):
            registro = salvar_decisao_api(
                {
                    "score_api": prontidao["score_api"],
                    "score_sqlite": prontidao["score_sqlite"],
                    "score_repositorio": prontidao["score_repositorio"],
                    "score_postgres": prontidao["score_postgres"],
                    "endpoints_mapeados": prontidao["endpoints_mapeados"],
                    "decisao": prontidao["decisao"],
                    "proximo_passo": prontidao["proximo_passo"],
                    "observacoes": "Decisão gerada pelo Blueprint FastAPI.",
                }
            )
            st.success(f"Decisão salva: {registro['decisao']}")
            st.rerun()

    if st.button("Gerar manifesto API", key="gerar_manifesto_api_valoris"):
        manifesto = gerar_manifesto_api()
        st.success(f"Manifesto gerado: {CAMINHO_MANIFESTO_API}")
        st.json(
            {
                "versao": manifesto["versao"],
                "score_api": manifesto["prontidao"]["score_api"],
                "endpoints": len(manifesto["endpoints"]),
            }
        )

    st.download_button(
        "Baixar diagnóstico API (.md)",
        data=_gerar_markdown_api(prontidao),
        file_name="api_contratos_valoris.md",
        mime="text/markdown",
        key="download_api_contratos_valoris",
    )

    st.download_button(
        "Baixar decisões API (.csv)",
        data=gerar_csv_decisoes_api(),
        file_name="decisoes_api_valoris.csv",
        mime="text/csv",
        key="download_decisoes_api_valoris",
    )

    st.divider()
    _renderizar_endpoints()

    st.divider()
    _renderizar_schemas()

    st.divider()
    _renderizar_fases()

    st.divider()
    _renderizar_blueprint()

    st.divider()
    _renderizar_historico()

    st.markdown(
        """
        <div class="api-note">
            <strong>Regra da API:</strong> não criar backend por ansiedade técnica.
            A API deve nascer como backend paralelo, começando por health, events e leads.
        </div>
        """,
        unsafe_allow_html=True,
    )


def executar_autoteste_api_contratos_valoris() -> List[Dict[str, str]]:
    prontidao = calcular_prontidao_api()
    openapi = gerar_openapi_rascunho()

    return [
        {
            "teste": "versao_api",
            "status": "OK" if VERSAO_API_CONTRATOS_VALORIS == "3.8.61" else "FALHA",
            "detalhe": VERSAO_API_CONTRATOS_VALORIS,
        },
        {
            "teste": "renderizador",
            "status": "OK" if callable(renderizar_api_contratos_valoris) else "FALHA",
            "detalhe": "renderizar_api_contratos_valoris",
        },
        {
            "teste": "score_api",
            "status": "OK" if 0 <= prontidao["score_api"] <= 100 else "FALHA",
            "detalhe": str(prontidao["score_api"]),
        },
        {
            "teste": "openapi",
            "status": "OK" if "/health" in openapi["paths"] else "FALHA",
            "detalhe": str(len(openapi["paths"])),
        },
    ]
