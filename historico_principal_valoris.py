# historico_principal_valoris.py
# Valoris — Histórico Principal com Backend Flexível v3.10.6
# ------------------------------------------------------------
# Objetivo:
# - Promover a experiência nova de Histórico Backend para uma página principal.
# - Manter a página legada intacta como rollback.
# - Entregar ao cliente uma tela mais clara, confiável e orientada à decisão.
# - Usar backend flexível sem forçar SQLite como padrão.

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import streamlit as st


VERSAO_HISTORICO_PRINCIPAL_VALORIS = "3.10.6"

CAMINHO_RELATORIO = Path("RELATORIO_HISTORICO_PRINCIPAL_VALORIS.md")
CAMINHO_MANIFESTO = Path("manifesto_historico_principal_valoris.json")


def _agora_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat(sep=" ")


def obter_metricas_historico_principal() -> Dict[str, Any]:
    try:
        from historico_backend_flexivel_valoris import (
            BACKEND_CSV,
            BACKEND_SQLITE,
            calcular_metricas_historico_backend,
        )

        metricas_csv = calcular_metricas_historico_backend(backend=BACKEND_CSV)
        metricas_sqlite = calcular_metricas_historico_backend(backend=BACKEND_SQLITE)

        return {
            "ok": True,
            "versao": VERSAO_HISTORICO_PRINCIPAL_VALORIS,
            "gerado_em": _agora_iso(),
            "csv": metricas_csv,
            "sqlite": metricas_sqlite,
            "backend_recomendado": "csv",
        }
    except Exception as erro:
        return {
            "ok": False,
            "versao": VERSAO_HISTORICO_PRINCIPAL_VALORIS,
            "gerado_em": _agora_iso(),
            "erro": str(erro),
            "backend_recomendado": "csv",
        }


def calcular_score_promocao_historico() -> Dict[str, Any]:
    metricas = obter_metricas_historico_principal()

    if not metricas.get("ok"):
        return {
            "score_promocao": 35,
            "status": "Atenção",
            "decisao": "Histórico principal indisponível",
            "proximo_passo": metricas.get("erro", "Revisar módulo do histórico backend."),
        }

    csv = metricas.get("csv", {})
    sqlite = metricas.get("sqlite", {})

    analises_csv = int(csv.get("analises", 0) or 0)
    analises_sqlite = int(sqlite.get("analises", 0) or 0)
    score_csv = int(csv.get("score_experiencia", 0) or 0)
    comparacao = csv.get("comparacao_csv_sqlite", {})
    alinhado = comparacao.get("status") == "alinhado"

    score = 40
    score += min(score_csv // 2, 40)

    if analises_csv > 0:
        score += 10

    if alinhado:
        score += 10

    if analises_sqlite == analises_csv:
        score += 5

    score = max(0, min(100, int(score)))

    if score >= 85 and analises_csv > 0:
        status = "Pronto"
        decisao = "Histórico Backend pode ser usado como experiência principal"
        proximo = "Manter página legada como rollback e observar uso."
    elif analises_csv > 0:
        status = "Funcional"
        decisao = "Histórico principal funcional, ainda em validação controlada"
        proximo = "Usar como página principal e manter rollback visível."
    else:
        status = "Atenção"
        decisao = "Histórico principal sem dados reais suficientes"
        proximo = "Gerar mais análises reais antes de remover o histórico legado."

    return {
        "score_promocao": score,
        "status": status,
        "decisao": decisao,
        "proximo_passo": proximo,
        "analises_csv": analises_csv,
        "analises_sqlite": analises_sqlite,
        "score_csv": score_csv,
        "csv_sqlite_alinhado": alinhado,
    }


def gerar_relatorio_historico_principal_markdown() -> str:
    promocao = calcular_score_promocao_historico()
    metricas = obter_metricas_historico_principal()

    csv = metricas.get("csv", {}) if metricas.get("ok") else {}
    sqlite = metricas.get("sqlite", {}) if metricas.get("ok") else {}

    return f"""# Histórico Principal com Backend Flexível — Valoris

Versão: {VERSAO_HISTORICO_PRINCIPAL_VALORIS}  
Gerado em: {_agora_iso()}

## Diagnóstico

Score de promoção: {promocao['score_promocao']}/100  
Status: {promocao['status']}  
Decisão: {promocao['decisao']}  
Próximo passo: {promocao['proximo_passo']}

## Backend CSV

Análises: {csv.get('analises', 0)}  
Tickers: {csv.get('tickers', 0)}  
Score experiência: {csv.get('score_experiencia', 0)}/100  
Decisão: {csv.get('decisao', '')}

## Backend SQLite laboratório

Análises: {sqlite.get('analises', 0)}  
Tickers: {sqlite.get('tickers', 0)}  
Score experiência: {sqlite.get('score_experiencia', 0)}/100  
Decisão: {sqlite.get('decisao', '')}

## Estratégia

Esta versão promove o histórico flexível como experiência principal sem apagar a página legada. A troca é segura porque CSV permanece como backend recomendado e o histórico antigo continua disponível como rollback.
"""


def salvar_relatorio_historico_principal() -> Path:
    CAMINHO_RELATORIO.write_text(gerar_relatorio_historico_principal_markdown(), encoding="utf-8")
    return CAMINHO_RELATORIO


def gerar_manifesto_historico_principal() -> Dict[str, Any]:
    return {
        "produto": "Valoris",
        "versao": VERSAO_HISTORICO_PRINCIPAL_VALORIS,
        "modulo": "historico_principal_valoris",
        "data_hora": _agora_iso(),
        "promocao": calcular_score_promocao_historico(),
        "metricas": obter_metricas_historico_principal(),
        "principio": "promover a nova experiência sem perder rollback",
        "backend_recomendado": "csv",
        "rollback": "Histórico Backend e Histórico Análises legado continuam disponíveis.",
        "proxima_etapa": "migrar Análise Inteligente para backend flexível com leitura controlada",
    }


def salvar_manifesto_historico_principal() -> Path:
    CAMINHO_MANIFESTO.write_text(
        json.dumps(gerar_manifesto_historico_principal(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return CAMINHO_MANIFESTO


def renderizar_historico_principal_valoris() -> None:
    st.subheader("Histórico Principal")
    st.caption(
        "Experiência oficial de histórico com backend flexível. CSV segue como padrão seguro; SQLite permanece em laboratório."
    )

    promocao = calcular_score_promocao_historico()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Score promoção", f"{promocao['score_promocao']}/100")
    col2.metric("Status", promocao["status"])
    col3.metric("Análises CSV", promocao.get("analises_csv", 0))
    col4.metric("CSV x SQLite", "Alinhado" if promocao.get("csv_sqlite_alinhado") else "Atenção")

    if promocao["status"] == "Pronto":
        st.success(f"{promocao['decisao']} — {promocao['proximo_passo']}")
    elif promocao["status"] == "Funcional":
        st.info(f"{promocao['decisao']} — {promocao['proximo_passo']}")
    else:
        st.warning(f"{promocao['decisao']} — {promocao['proximo_passo']}")

    with st.expander("Estratégia de transição e rollback", expanded=False):
        st.markdown(
            """
            **Estratégia da versão v3.10.6**

            - Esta página é a experiência principal recomendada.
            - A página antiga de histórico não foi apagada.
            - O backend CSV continua sendo o modo seguro.
            - O SQLite pode ser testado sem afetar a experiência do cliente.
            - O próximo passo é migrar a Análise Inteligente com a mesma lógica de segurança.
            """
        )

    st.divider()

    try:
        from historico_backend_flexivel_valoris import renderizar_historico_backend_flexivel_valoris

        renderizar_historico_backend_flexivel_valoris()
    except Exception as erro:
        st.error("Não foi possível renderizar o Histórico Backend Flexível.")
        st.exception(erro)

    st.divider()

    st.markdown("### Governança da página principal")

    col_a, col_b = st.columns(2)

    if col_a.button("Salvar relatório do Histórico Principal"):
        caminho = salvar_relatorio_historico_principal()
        st.success(f"Relatório salvo em {caminho}")

    if col_b.button("Salvar manifesto do Histórico Principal"):
        caminho = salvar_manifesto_historico_principal()
        st.success(f"Manifesto salvo em {caminho}")

    st.download_button(
        "Baixar relatório do Histórico Principal (.md)",
        data=gerar_relatorio_historico_principal_markdown(),
        file_name="RELATORIO_HISTORICO_PRINCIPAL_VALORIS.md",
        mime="text/markdown",
    )


def executar_autoteste_historico_principal_valoris() -> Dict[str, Any]:
    promocao = calcular_score_promocao_historico()

    return {
        "ok": True,
        "versao": VERSAO_HISTORICO_PRINCIPAL_VALORIS,
        "metricas": promocao,
    }
