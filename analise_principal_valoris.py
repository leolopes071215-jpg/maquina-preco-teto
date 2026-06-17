# analise_principal_valoris.py
# Valoris — Análise Inteligente Principal v3.10.8
# ------------------------------------------------------------
# Objetivo:
# - Promover a nova Análise Backend para a experiência principal de decisão.
# - Manter a página antiga como rollback.
# - Usar CSV como backend seguro e SQLite como laboratório.
# - Transformar a tela principal em uma central clara, executiva e orientada à próxima ação.

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import streamlit as st


VERSAO_ANALISE_PRINCIPAL_VALORIS = "3.10.8"

CAMINHO_RELATORIO = Path("RELATORIO_ANALISE_PRINCIPAL_VALORIS.md")
CAMINHO_MANIFESTO = Path("manifesto_analise_principal_valoris.json")


def _agora_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat(sep=" ")


def obter_metricas_analise_principal() -> Dict[str, Any]:
    try:
        from analise_inteligente_backend_valoris import (
            BACKEND_CSV,
            BACKEND_SQLITE,
            calcular_metricas_analise_backend,
        )

        metricas_csv = calcular_metricas_analise_backend(backend=BACKEND_CSV)
        metricas_sqlite = calcular_metricas_analise_backend(backend=BACKEND_SQLITE)

        return {
            "ok": True,
            "versao": VERSAO_ANALISE_PRINCIPAL_VALORIS,
            "gerado_em": _agora_iso(),
            "csv": metricas_csv,
            "sqlite": metricas_sqlite,
            "backend_recomendado": "csv",
        }
    except Exception as erro:
        return {
            "ok": False,
            "versao": VERSAO_ANALISE_PRINCIPAL_VALORIS,
            "gerado_em": _agora_iso(),
            "erro": str(erro),
            "backend_recomendado": "csv",
        }


def calcular_score_promocao_analise() -> Dict[str, Any]:
    metricas = obter_metricas_analise_principal()

    if not metricas.get("ok"):
        return {
            "score_promocao": 35,
            "status": "Atenção",
            "decisao": "Análise principal indisponível",
            "proximo_passo": metricas.get("erro", "Revisar módulo da Análise Backend."),
        }

    csv = metricas.get("csv", {})
    sqlite = metricas.get("sqlite", {})

    ativos_csv = int(csv.get("ativos_ranqueados", 0) or 0)
    ativos_sqlite = int(sqlite.get("ativos_ranqueados", 0) or 0)
    score_csv = int(csv.get("score_experiencia", 0) or 0)
    alta = int(csv.get("alta_prioridade", 0) or 0)
    boas = int(csv.get("boas_candidatas", 0) or 0)
    incompletas = int(csv.get("premissas_incompletas", 0) or 0)

    score = 40
    score += min(score_csv // 2, 40)

    if ativos_csv > 0:
        score += 8

    if boas > 0:
        score += 7

    if alta > 0:
        score += 7

    if ativos_sqlite == ativos_csv:
        score += 5

    if incompletas > 0:
        score -= min(incompletas * 6, 18)

    score = max(0, min(100, int(score)))

    if score >= 85 and ativos_csv > 0:
        status = "Pronto"
        decisao = "Análise Backend pode ser usada como experiência principal de decisão"
        proximo = "Manter página antiga como rollback e observar uso real."
    elif ativos_csv > 0:
        status = "Funcional"
        decisao = "Análise principal funcional, ainda em validação controlada"
        proximo = "Usar como página principal e alimentar mais ativos reais."
    else:
        status = "Atenção"
        decisao = "Análise principal sem ativos suficientes"
        proximo = "Criar mais análises no Motor antes de remover a experiência antiga."

    return {
        "score_promocao": score,
        "status": status,
        "decisao": decisao,
        "proximo_passo": proximo,
        "ativos_csv": ativos_csv,
        "ativos_sqlite": ativos_sqlite,
        "score_csv": score_csv,
        "alta_prioridade": alta,
        "boas_candidatas": boas,
        "premissas_incompletas": incompletas,
        "sqlite_alinhado": ativos_sqlite == ativos_csv,
    }


def gerar_relatorio_analise_principal_markdown() -> str:
    promocao = calcular_score_promocao_analise()
    metricas = obter_metricas_analise_principal()

    csv = metricas.get("csv", {}) if metricas.get("ok") else {}
    sqlite = metricas.get("sqlite", {}) if metricas.get("ok") else {}

    return f"""# Análise Inteligente Principal — Valoris

Versão: {VERSAO_ANALISE_PRINCIPAL_VALORIS}  
Gerado em: {_agora_iso()}

## Diagnóstico

Score de promoção: {promocao['score_promocao']}/100  
Status: {promocao['status']}  
Decisão: {promocao['decisao']}  
Próximo passo: {promocao['proximo_passo']}

## Backend CSV

Ativos ranqueados: {csv.get('ativos_ranqueados', 0)}  
Alta prioridade: {csv.get('alta_prioridade', 0)}  
Boas candidatas: {csv.get('boas_candidatas', 0)}  
Score experiência: {csv.get('score_experiencia', 0)}/100  
Decisão: {csv.get('decisao', '')}

## Backend SQLite laboratório

Ativos ranqueados: {sqlite.get('ativos_ranqueados', 0)}  
Alta prioridade: {sqlite.get('alta_prioridade', 0)}  
Boas candidatas: {sqlite.get('boas_candidatas', 0)}  
Score experiência: {sqlite.get('score_experiencia', 0)}/100  
Decisão: {sqlite.get('decisao', '')}

## Estratégia

Esta versão promove a nova Análise Backend como experiência principal de decisão, sem apagar a página antiga. A decisão do usuário fica mais clara: ranking, classificação, ação recomendada e governança de backend no mesmo fluxo.
"""


def salvar_relatorio_analise_principal() -> Path:
    CAMINHO_RELATORIO.write_text(gerar_relatorio_analise_principal_markdown(), encoding="utf-8")
    return CAMINHO_RELATORIO


def gerar_manifesto_analise_principal() -> Dict[str, Any]:
    return {
        "produto": "Valoris",
        "versao": VERSAO_ANALISE_PRINCIPAL_VALORIS,
        "modulo": "analise_principal_valoris",
        "data_hora": _agora_iso(),
        "promocao": calcular_score_promocao_analise(),
        "metricas": obter_metricas_analise_principal(),
        "principio": "a tela principal deve transformar dado em próxima ação com clareza e rollback",
        "backend_recomendado": "csv",
        "rollback": "A aba Análise Inteligente antiga e a aba Análise Backend continuam disponíveis.",
        "proxima_etapa": "migrar Pipeline Decisão para backend flexível com escrita controlada",
    }


def salvar_manifesto_analise_principal() -> Path:
    CAMINHO_MANIFESTO.write_text(
        json.dumps(gerar_manifesto_analise_principal(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return CAMINHO_MANIFESTO


def renderizar_analise_principal_valoris() -> None:
    st.subheader("Análise Principal")
    st.caption(
        "Experiência oficial de decisão inteligente. CSV segue como padrão seguro; SQLite permanece em laboratório."
    )

    promocao = calcular_score_promocao_analise()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Score promoção", f"{promocao['score_promocao']}/100")
    col2.metric("Status", promocao["status"])
    col3.metric("Ativos CSV", promocao.get("ativos_csv", 0))
    col4.metric("Boas candidatas", promocao.get("boas_candidatas", 0))
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
            **Estratégia da v3.10.8**

            - Esta página passa a ser a experiência principal recomendada para decisão.
            - A aba antiga **Análise Inteligente** permanece como rollback.
            - A aba **Análise Backend** permanece disponível para validação técnica.
            - CSV continua sendo o backend padrão seguro.
            - SQLite continua em laboratório.
            - O próximo avanço natural será o Pipeline Decisão com backend flexível.
            """
        )

    st.divider()

    try:
        from analise_inteligente_backend_valoris import renderizar_analise_inteligente_backend_valoris

        renderizar_analise_inteligente_backend_valoris()
    except Exception as erro:
        st.error("Não foi possível renderizar a Análise Backend.")
        st.exception(erro)

    st.divider()

    st.markdown("### Governança da Análise Principal")

    col_a, col_b = st.columns(2)

    if col_a.button("Salvar relatório da Análise Principal"):
        caminho = salvar_relatorio_analise_principal()
        st.success(f"Relatório salvo em {caminho}")

    if col_b.button("Salvar manifesto da Análise Principal"):
        caminho = salvar_manifesto_analise_principal()
        st.success(f"Manifesto salvo em {caminho}")

    st.download_button(
        "Baixar relatório da Análise Principal (.md)",
        data=gerar_relatorio_analise_principal_markdown(),
        file_name="RELATORIO_ANALISE_PRINCIPAL_VALORIS.md",
        mime="text/markdown",
    )


def executar_autoteste_analise_principal_valoris() -> Dict[str, Any]:
    promocao = calcular_score_promocao_analise()

    return {
        "ok": True,
        "versao": VERSAO_ANALISE_PRINCIPAL_VALORIS,
        "metricas": promocao,
    }
