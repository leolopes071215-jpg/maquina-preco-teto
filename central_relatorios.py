# central_relatorios.py

import streamlit as st
from typing import Any, Dict

from relatorio import gerar_relatorio_markdown, gerar_nome_arquivo_relatorio
from decisao import gerar_bloco_markdown_decisao
from relatorio_multiativos import (
    gerar_relatorio_multiativos_markdown,
    gerar_nome_arquivo_relatorio_multiativos,
)


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v1.23 — Central de Relatórios
# ------------------------------------------------------------
# Esta tela centraliza os relatórios da plataforma:
# 1. Relatório executivo simples
# 2. Relatório com decisão
# 3. Relatório premium multiativos
# Não é recomendação de investimento.
# ============================================================


def _safe_get_dict(key: str) -> Dict[str, Any]:
    valor = st.session_state.get(key)

    if isinstance(valor, dict):
        return valor

    return {}


def _fmt_texto(valor: Any, padrao: str = "N/D") -> str:
    if valor is None or valor == "":
        return padrao

    return str(valor)


def _fmt_score(valor: Any) -> str:
    if valor is None or valor == "":
        return "N/D"

    try:
        return f"{int(round(float(valor)))}/100"
    except (TypeError, ValueError):
        return "N/D"


def _fmt_moeda(valor: Any, simbolo: str = "R$") -> str:
    if valor is None or valor == "":
        return "N/D"

    try:
        numero = float(valor)
        return f"{simbolo} {numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return "N/D"


def _injetar_css_relatorios() -> None:
    st.markdown(
        """
        <style>
            .rel-hero {
                padding: 1.55rem 1.6rem;
                border-radius: 26px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    radial-gradient(circle at top left, rgba(214, 181, 109, 0.22), transparent 30%),
                    radial-gradient(circle at bottom right, rgba(74, 144, 226, 0.20), transparent 34%),
                    linear-gradient(135deg, rgba(8, 15, 27, 0.98), rgba(5, 9, 18, 0.98));
                box-shadow: 0 18px 55px rgba(0, 0, 0, 0.33);
                margin-bottom: 1.25rem;
            }

            .rel-eyebrow {
                color: #d6b56d;
                font-size: 0.78rem;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .rel-title {
                color: #f4f7fb;
                font-size: 1.95rem;
                font-weight: 850;
                margin-bottom: 0.45rem;
            }

            .rel-subtitle {
                color: rgba(244, 247, 251, 0.74);
                font-size: 0.98rem;
                line-height: 1.58;
                max-width: 1040px;
            }

            .rel-card {
                padding: 1.05rem 1.1rem;
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.035);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.18);
                height: 100%;
            }

            .rel-card-label {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .rel-card-value {
                color: #f4f7fb;
                font-size: 1.22rem;
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .rel-card-note {
                color: rgba(244, 247, 251, 0.66);
                font-size: 0.86rem;
                line-height: 1.45;
            }

            .rel-box {
                padding: 1.05rem 1.1rem;
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.028);
                margin-bottom: 1rem;
            }

            .rel-box-title {
                color: #f4f7fb;
                font-size: 1.08rem;
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .rel-box-text {
                color: rgba(244, 247, 251, 0.70);
                font-size: 0.90rem;
                line-height: 1.50;
                margin-bottom: 0.7rem;
            }

            .rel-badge {
                display: inline-block;
                padding: 0.18rem 0.55rem;
                border-radius: 999px;
                background: rgba(214, 181, 109, 0.10);
                border: 1px solid rgba(214, 181, 109, 0.20);
                color: #d6b56d;
                font-size: 0.72rem;
                font-weight: 750;
                margin-bottom: 0.5rem;
            }

            .rel-disclaimer {
                padding: 0.95rem 1rem;
                border-radius: 16px;
                background: rgba(74, 144, 226, 0.08);
                border: 1px solid rgba(74, 144, 226, 0.18);
                color: rgba(244, 247, 251, 0.78);
                font-size: 0.9rem;
                line-height: 1.55;
                margin-top: 1.1rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _card(label: str, value: str, note: str = "") -> None:
    st.markdown(
        f"""
        <div class="rel-card">
            <div class="rel-card-label">{label}</div>
            <div class="rel-card-value">{value}</div>
            <div class="rel-card-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _gerar_relatorio_executivo_simples(
    entradas: Any,
    resultado: Dict[str, Any],
    dados_empresa: Dict[str, Any],
    simbolo_moeda: str,
    formatar_moeda,
    formatar_percentual,
    formatar_numero,
) -> str:
    return gerar_relatorio_markdown(
        entradas=entradas,
        resultado=resultado,
        dados_empresa=dados_empresa,
        simbolo_moeda=simbolo_moeda,
        formatar_moeda=formatar_moeda,
        formatar_percentual=formatar_percentual,
        formatar_numero=formatar_numero,
    )


def _gerar_relatorio_com_decisao(
    entradas: Any,
    resultado: Dict[str, Any],
    dados_empresa: Dict[str, Any],
    simbolo_moeda: str,
    formatar_moeda,
    formatar_percentual,
    formatar_numero,
) -> str:
    relatorio_base = gerar_relatorio_markdown(
        entradas=entradas,
        resultado=resultado,
        dados_empresa=dados_empresa,
        simbolo_moeda=simbolo_moeda,
        formatar_moeda=formatar_moeda,
        formatar_percentual=formatar_percentual,
        formatar_numero=formatar_numero,
    )

    resumo_decisao = st.session_state.get("resultado_resumo_decisao")

    bloco_decisao = gerar_bloco_markdown_decisao(
        resumo_decisao=resumo_decisao,
        simbolo_moeda=simbolo_moeda,
    )

    return relatorio_base + bloco_decisao


def _nome_relatorio_simples(entradas: Any) -> str:
    return gerar_nome_arquivo_relatorio(
        empresa=entradas.empresa,
        ticker=entradas.ticker,
    )


def _nome_relatorio_decisao(entradas: Any) -> str:
    return gerar_nome_arquivo_relatorio(
        empresa=entradas.empresa,
        ticker=entradas.ticker,
    ).replace(".md", "_decisao.md")


def _renderizar_status_modulos() -> None:
    painel = _safe_get_dict("resultado_painel_multiativos")
    resumo = _safe_get_dict("resultado_resumo_decisao")
    conviccao = _safe_get_dict("resultado_conviccao_tese")
    checklist = _safe_get_dict("resultado_checklist_erros")
    watchlist = _safe_get_dict("resultado_watchlist")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        _card(
            "Painel",
            "OK" if painel else "Pendente",
            f"Score: {_fmt_score(painel.get('score_integrado'))}" if painel else "Abra o Painel Executivo.",
        )

    with col2:
        _card(
            "Decisão",
            "OK" if resumo else "Pendente",
            f"Score: {_fmt_score(resumo.get('score_final'))}" if resumo else "Abra Resumo da Decisão.",
        )

    with col3:
        _card(
            "Tese",
            "OK" if conviccao else "Pendente",
            f"Score: {_fmt_score(conviccao.get('score_conviccao'))}" if conviccao else "Abra Tese & Convicção.",
        )

    with col4:
        _card(
            "Checklist",
            "OK" if checklist else "Pendente",
            f"Risco: {_fmt_score(checklist.get('score_risco'))}" if checklist else "Rode o Checklist.",
        )

    with col5:
        _card(
            "Watchlist",
            "OK" if watchlist else "Pendente",
            f"Ativos: {_fmt_texto(watchlist.get('total'))}" if watchlist else "Salve um ativo.",
        )


def renderizar_central_relatorios(
    entradas: Any,
    resultado: Dict[str, Any],
    dados_empresa: Dict[str, Any],
    simbolo_moeda: str,
    formatar_moeda,
    formatar_percentual,
    formatar_numero,
) -> None:
    """
    Renderiza a Central de Relatórios.
    """
    _injetar_css_relatorios()

    valuation = _safe_get_dict("resultado_valuation")
    painel = _safe_get_dict("resultado_painel_multiativos")

    relatorio_simples = _gerar_relatorio_executivo_simples(
        entradas=entradas,
        resultado=resultado,
        dados_empresa=dados_empresa,
        simbolo_moeda=simbolo_moeda,
        formatar_moeda=formatar_moeda,
        formatar_percentual=formatar_percentual,
        formatar_numero=formatar_numero,
    )

    relatorio_decisao = _gerar_relatorio_com_decisao(
        entradas=entradas,
        resultado=resultado,
        dados_empresa=dados_empresa,
        simbolo_moeda=simbolo_moeda,
        formatar_moeda=formatar_moeda,
        formatar_percentual=formatar_percentual,
        formatar_numero=formatar_numero,
    )

    relatorio_multiativos = gerar_relatorio_multiativos_markdown(
        entradas=entradas,
        resultado=resultado,
        dados_empresa=dados_empresa,
        simbolo_moeda=simbolo_moeda,
        formatar_moeda=formatar_moeda,
        formatar_percentual=formatar_percentual,
        formatar_numero=formatar_numero,
    )

    nome_simples = _nome_relatorio_simples(entradas)
    nome_decisao = _nome_relatorio_decisao(entradas)
    nome_multiativos = gerar_nome_arquivo_relatorio_multiativos(
        empresa=entradas.empresa,
        ticker=entradas.ticker,
    )

    st.markdown(
        """
        <div class="rel-hero">
            <div class="rel-eyebrow">Entrega premium da análise</div>
            <div class="rel-title">Central de Relatórios</div>
            <div class="rel-subtitle">
                Converta sua análise em documentos organizados. Escolha entre relatório executivo simples,
                relatório com decisão ou relatório premium multiativos. O objetivo é transformar dados,
                premissas e riscos em um material claro para revisão e acompanhamento.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Análise atual")

    col_ctx_1, col_ctx_2, col_ctx_3, col_ctx_4 = st.columns(4)

    with col_ctx_1:
        st.metric("Empresa", _fmt_texto(valuation.get("empresa", entradas.empresa)))

    with col_ctx_2:
        st.metric("Ticker", _fmt_texto(valuation.get("ticker", entradas.ticker)))

    with col_ctx_3:
        st.metric("Status", _fmt_texto(valuation.get("status_valuation", valuation.get("status"))))

    with col_ctx_4:
        st.metric(
            "Preço-teto",
            _fmt_moeda(valuation.get("preco_teto"), simbolo_moeda),
        )

    st.divider()

    st.markdown("### Status dos módulos para relatório")

    _renderizar_status_modulos()

    if not painel:
        st.warning(
            "Para gerar o relatório premium mais completo, abra primeiro o Painel Executivo. "
            "Ele consolida os principais módulos da análise."
        )

    st.divider()

    st.markdown("### Escolha o tipo de relatório")

    col_rel_1, col_rel_2, col_rel_3 = st.columns(3)

    with col_rel_1:
        st.markdown(
            """
            <div class="rel-box">
                <div class="rel-badge">Essencial</div>
                <div class="rel-box-title">Relatório Executivo</div>
                <div class="rel-box-text">
                    Melhor para uma visão rápida do valuation: premissas, preço justo, preço-teto,
                    status educacional, tese, riscos e fundamentos.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.download_button(
            label="Baixar relatório executivo (.md)",
            data=relatorio_simples,
            file_name=nome_simples,
            mime="text/markdown",
            key="central_download_relatorio_executivo",
        )

    with col_rel_2:
        st.markdown(
            """
            <div class="rel-box">
                <div class="rel-badge">Decisão</div>
                <div class="rel-box-title">Relatório com Decisão</div>
                <div class="rel-box-text">
                    Melhor para revisar a leitura final da decisão educacional, combinando valuation,
                    convicção da tese, cenários, alertas e ação sugerida.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.download_button(
            label="Baixar relatório com decisão (.md)",
            data=relatorio_decisao,
            file_name=nome_decisao,
            mime="text/markdown",
            key="central_download_relatorio_decisao",
        )

    with col_rel_3:
        st.markdown(
            """
            <div class="rel-box">
                <div class="rel-badge">Premium</div>
                <div class="rel-box-title">Relatório Multiativos</div>
                <div class="rel-box-text">
                    Melhor para uma análise completa, consolidando valuation, painel executivo,
                    decisão, tese, checklist, Ações Brasil, FIIs e Renda Fixa.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.download_button(
            label="Baixar relatório premium multiativos (.md)",
            data=relatorio_multiativos,
            file_name=nome_multiativos,
            mime="text/markdown",
            key="central_download_relatorio_multiativos",
        )

    st.divider()

    st.markdown("### Quando usar cada relatório")

    st.markdown(
        """
        - **Relatório Executivo:** use quando quiser registrar apenas o valuation e as premissas principais.
        - **Relatório com Decisão:** use quando já avaliou tese, cenários e quer uma leitura educacional de decisão.
        - **Relatório Premium Multiativos:** use quando preencheu vários módulos e quer consolidar tudo em um documento mais completo.

        Para melhor resultado, siga a jornada: **Valuation → Tese & Convicção → Checklist → Painel Executivo → Relatórios → Watchlist**.
        """
    )

    st.markdown(
        """
        <div class="rel-disclaimer">
            <strong>Aviso educacional:</strong> os relatórios não representam recomendação de compra, venda ou manutenção.
            Eles organizam dados, premissas, riscos e raciocínio para apoiar estudo e disciplina.
            Toda decisão real deve considerar objetivos pessoais, diversificação, liquidez, tributação,
            horizonte de tempo, qualidade dos dados e responsabilidade individual.
        </div>
        """,
        unsafe_allow_html=True,
    )