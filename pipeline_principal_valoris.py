# pipeline_principal_valoris.py
# Valoris — Pipeline Principal v3.11.0

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import streamlit as st


VERSAO_PIPELINE_PRINCIPAL_VALORIS = "3.11.0"

CAMINHO_RELATORIO = Path("RELATORIO_PIPELINE_PRINCIPAL_VALORIS.md")
CAMINHO_MANIFESTO = Path("manifesto_pipeline_principal_valoris.json")


def _agora_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat(sep=" ")


def obter_metricas_pipeline_principal() -> Dict[str, Any]:
    try:
        from pipeline_backend_flexivel_valoris import (
            BACKEND_CSV,
            BACKEND_SQLITE,
            calcular_metricas_pipeline_backend,
        )

        metricas_csv = calcular_metricas_pipeline_backend(backend_leitura=BACKEND_CSV)
        metricas_sqlite = calcular_metricas_pipeline_backend(backend_leitura=BACKEND_SQLITE)

        return {
            "ok": True,
            "versao": VERSAO_PIPELINE_PRINCIPAL_VALORIS,
            "gerado_em": _agora_iso(),
            "csv": metricas_csv,
            "sqlite": metricas_sqlite,
            "backend_leitura_recomendado": "csv",
            "backend_escrita_recomendado": "csv",
        }
    except Exception as erro:
        return {
            "ok": False,
            "versao": VERSAO_PIPELINE_PRINCIPAL_VALORIS,
            "gerado_em": _agora_iso(),
            "erro": str(erro),
            "backend_leitura_recomendado": "csv",
            "backend_escrita_recomendado": "csv",
        }


def calcular_score_promocao_pipeline() -> Dict[str, Any]:
    metricas = obter_metricas_pipeline_principal()

    if not metricas.get("ok"):
        return {
            "score_promocao": 35,
            "status": "Atenção",
            "decisao": "Pipeline principal indisponível",
            "proximo_passo": metricas.get("erro", "Revisar módulo Pipeline Backend."),
        }

    csv = metricas.get("csv", {})
    sqlite = metricas.get("sqlite", {})

    ranking_csv = int(csv.get("ativos_no_ranking", 0) or 0)
    sugestoes_csv = int(csv.get("sugestoes", 0) or 0)
    acoes_csv = int(csv.get("acoes_pipeline", 0) or 0)
    abertas_csv = int(csv.get("acoes_abertas", 0) or 0)
    score_csv = int(csv.get("score_controle", 0) or 0)
    ranking_sqlite = int(sqlite.get("ativos_no_ranking", 0) or 0)
    sqlite_alinhado = ranking_sqlite == ranking_csv

    score = 40
    score += min(score_csv // 2, 40)
    if ranking_csv > 0:
        score += 6
    if sugestoes_csv > 0:
        score += 6
    if acoes_csv > 0:
        score += 10
    if abertas_csv <= 20:
        score += 5
    if sqlite_alinhado:
        score += 5

    score = max(0, min(100, int(score)))

    if score >= 85 and acoes_csv > 0:
        status = "Pronto"
        decisao = "Pipeline Backend pode ser usado como experiência operacional principal"
        proximo = "Manter pipeline antigo como rollback e começar a usar o fluxo operacional novo."
    elif acoes_csv > 0:
        status = "Funcional"
        decisao = "Pipeline principal funcional, ainda em validação controlada"
        proximo = "Usar como página principal e validar novas ações reais."
    elif ranking_csv > 0:
        status = "Atenção"
        decisao = "Pipeline principal gera sugestões, mas ainda precisa de ações salvas"
        proximo = "Salvar pelo menos uma ação controlada antes de remover qualquer fallback."
    else:
        status = "Atenção"
        decisao = "Pipeline principal sem base operacional suficiente"
        proximo = "Validar Análise Principal e criar ações de pipeline."

    return {
        "score_promocao": score,
        "status": status,
        "decisao": decisao,
        "proximo_passo": proximo,
        "ranking_csv": ranking_csv,
        "sugestoes_csv": sugestoes_csv,
        "acoes_csv": acoes_csv,
        "abertas_csv": abertas_csv,
        "score_csv": score_csv,
        "sqlite_alinhado": sqlite_alinhado,
    }


def gerar_relatorio_pipeline_principal_markdown() -> str:
    promocao = calcular_score_promocao_pipeline()
    metricas = obter_metricas_pipeline_principal()
    csv = metricas.get("csv", {}) if metricas.get("ok") else {}
    sqlite = metricas.get("sqlite", {}) if metricas.get("ok") else {}

    return f"""# Pipeline Principal — Valoris

Versão: {VERSAO_PIPELINE_PRINCIPAL_VALORIS}  
Gerado em: {_agora_iso()}

## Diagnóstico

Score de promoção: {promocao['score_promocao']}/100  
Status: {promocao['status']}  
Decisão: {promocao['decisao']}  
Próximo passo: {promocao['proximo_passo']}

## Backend CSV

Ativos no ranking: {csv.get('ativos_no_ranking', 0)}  
Sugestões: {csv.get('sugestoes', 0)}  
Ações no pipeline: {csv.get('acoes_pipeline', 0)}  
Ações abertas: {csv.get('acoes_abertas', 0)}  
Score controle: {csv.get('score_controle', 0)}/100  
Decisão: {csv.get('decisao', '')}

## Backend SQLite laboratório

Ativos no ranking: {sqlite.get('ativos_no_ranking', 0)}  
Sugestões: {sqlite.get('sugestoes', 0)}  
Ações no pipeline: {sqlite.get('acoes_pipeline', 0)}  
Ações abertas: {sqlite.get('acoes_abertas', 0)}  
Score controle: {sqlite.get('score_controle', 0)}/100  
Decisão: {sqlite.get('decisao', '')}

## Estratégia

Esta versão promove o Pipeline Backend como experiência operacional principal. O cliente passa a enxergar a jornada completa: análise, priorização, ação, prazo e acompanhamento. A escrita permanece segura em CSV e SQLite continua em laboratório.
"""


def salvar_relatorio_pipeline_principal() -> Path:
    CAMINHO_RELATORIO.write_text(gerar_relatorio_pipeline_principal_markdown(), encoding="utf-8")
    return CAMINHO_RELATORIO


def gerar_manifesto_pipeline_principal() -> Dict[str, Any]:
    return {
        "produto": "Valoris",
        "versao": VERSAO_PIPELINE_PRINCIPAL_VALORIS,
        "modulo": "pipeline_principal_valoris",
        "data_hora": _agora_iso(),
        "promocao": calcular_score_promocao_pipeline(),
        "metricas": obter_metricas_pipeline_principal(),
        "principio": "o produto premium precisa transformar decisão em ação acompanhável",
        "backend_leitura_recomendado": "csv",
        "backend_escrita_recomendado": "csv",
        "rollback": "Pipeline Backend e Pipeline Decisão antigo continuam disponíveis.",
        "proxima_etapa": "Radar Principal conectado ao Pipeline Principal",
    }


def salvar_manifesto_pipeline_principal() -> Path:
    CAMINHO_MANIFESTO.write_text(
        json.dumps(gerar_manifesto_pipeline_principal(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return CAMINHO_MANIFESTO


def renderizar_pipeline_principal_valoris() -> None:
    st.subheader("Pipeline Principal")
    st.caption("Experiência operacional oficial: transforma ranking inteligente em ações, prazos e acompanhamento.")

    promocao = calcular_score_promocao_pipeline()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Score promoção", f"{promocao['score_promocao']}/100")
    col2.metric("Status", promocao["status"])
    col3.metric("Ranking CSV", promocao.get("ranking_csv", 0))
    col4.metric("Ações", promocao.get("acoes_csv", 0))
    col5.metric("SQLite", "Alinhado" if promocao.get("sqlite_alinhado") else "Atenção")

    if promocao["status"] == "Pronto":
        st.success(f"{promocao['decisao']} — {promocao['proximo_passo']}")
    elif promocao["status"] == "Funcional":
        st.info(f"{promocao['decisao']} — {promocao['proximo_passo']}")
    else:
        st.warning(f"{promocao['decisao']} — {promocao['proximo_passo']}")

    with st.expander("Estratégia de transição e rollback", expanded=False):
        st.markdown(
            """
            **Estratégia da v3.11.0**

            - Esta página passa a ser a experiência operacional principal.
            - A aba **Pipeline Backend** continua disponível para validação técnica.
            - O pipeline antigo permanece como rollback.
            - CSV continua sendo a base segura de escrita.
            - SQLite continua como laboratório de leitura.
            - O próximo avanço natural será um Radar Principal conectado ao novo Pipeline.
            """
        )

    st.divider()

    try:
        from pipeline_backend_flexivel_valoris import renderizar_pipeline_backend_flexivel_valoris
        renderizar_pipeline_backend_flexivel_valoris()
    except Exception as erro:
        st.error("Não foi possível renderizar o Pipeline Backend.")
        st.exception(erro)

    st.divider()
    st.markdown("### Governança do Pipeline Principal")

    col_a, col_b = st.columns(2)

    if col_a.button("Salvar relatório do Pipeline Principal"):
        caminho = salvar_relatorio_pipeline_principal()
        st.success(f"Relatório salvo em {caminho}")

    if col_b.button("Salvar manifesto do Pipeline Principal"):
        caminho = salvar_manifesto_pipeline_principal()
        st.success(f"Manifesto salvo em {caminho}")

    st.download_button(
        "Baixar relatório do Pipeline Principal (.md)",
        data=gerar_relatorio_pipeline_principal_markdown(),
        file_name="RELATORIO_PIPELINE_PRINCIPAL_VALORIS.md",
        mime="text/markdown",
    )


def executar_autoteste_pipeline_principal_valoris() -> Dict[str, Any]:
    promocao = calcular_score_promocao_pipeline()
    return {"ok": True, "versao": VERSAO_PIPELINE_PRINCIPAL_VALORIS, "metricas": promocao}
