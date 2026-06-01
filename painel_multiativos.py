# painel_multiativos.py

import streamlit as st
from typing import Any, Dict, Optional


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v1.19 — Painel Executivo Multiativos
# ------------------------------------------------------------
# Este módulo consolida os principais resultados da plataforma:
# valuation, decisão, convicção, checklist, Ações Brasil, FIIs
# e Renda Fixa.
# Não é recomendação de investimento.
# É uma sala de controle educacional da análise.
# ============================================================


def _normalizar_status(status: Any) -> str:
    if status is None:
        return "N/D"

    texto = str(status).upper().strip()

    if "COMPRA" in texto:
        return "COMPRA"
    if "NEUTRO" in texto:
        return "NEUTRO"
    if "AGUARDE" in texto:
        return "AGUARDE"

    return texto or "N/D"


def _safe_get_dict(key: str) -> Dict[str, Any]:
    valor = st.session_state.get(key)

    if isinstance(valor, dict):
        return valor

    return {}


def _fmt_score(valor: Optional[Any]) -> str:
    if valor is None:
        return "N/D"

    try:
        return f"{int(round(float(valor)))}/100"
    except (TypeError, ValueError):
        return "N/D"


def _fmt_texto(valor: Optional[Any], padrao: str = "N/D") -> str:
    if valor is None or valor == "":
        return padrao

    return str(valor)


def _extrair_contexto() -> Dict[str, Any]:
    valuation = _safe_get_dict("resultado_valuation")

    return {
        "empresa": valuation.get("empresa", "Empresa analisada"),
        "ticker": valuation.get("ticker", "N/D"),
        "status_valuation": _normalizar_status(
            valuation.get("status_valuation", valuation.get("status", "N/D"))
        ),
        "preco_atual": valuation.get("preco_atual"),
        "preco_teto": valuation.get("preco_teto"),
        "preco_justo": valuation.get("preco_justo", valuation.get("preco_justo_combinado")),
        "simbolo_moeda": valuation.get("simbolo_moeda", "R$"),
    }


def _fmt_moeda(valor: Optional[Any], simbolo: str = "R$") -> str:
    if valor is None:
        return "N/D"

    try:
        numero = float(valor)
        return f"{simbolo} {numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return "N/D"


def _injetar_css_painel() -> None:
    st.markdown(
        """
        <style>
            .painel-hero {
                padding: 1.5rem 1.55rem;
                border-radius: 24px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    radial-gradient(circle at top left, rgba(214, 181, 109, 0.19), transparent 30%),
                    radial-gradient(circle at bottom right, rgba(74, 144, 226, 0.19), transparent 34%),
                    linear-gradient(135deg, rgba(8, 15, 27, 0.98), rgba(5, 9, 18, 0.98));
                box-shadow: 0 18px 55px rgba(0, 0, 0, 0.32);
                margin-bottom: 1.25rem;
            }

            .painel-eyebrow {
                color: #d6b56d;
                font-size: 0.78rem;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .painel-title {
                color: #f4f7fb;
                font-size: 1.85rem;
                font-weight: 850;
                margin-bottom: 0.45rem;
            }

            .painel-subtitle {
                color: rgba(244, 247, 251, 0.74);
                font-size: 0.98rem;
                line-height: 1.58;
                max-width: 980px;
            }

            .painel-card {
                padding: 1.05rem 1.1rem;
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.035);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.18);
                height: 100%;
            }

            .painel-card-label {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .painel-card-value {
                color: #f4f7fb;
                font-size: 1.22rem;
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .painel-card-note {
                color: rgba(244, 247, 251, 0.66);
                font-size: 0.86rem;
                line-height: 1.45;
            }

            .painel-alert {
                padding: 0.82rem 1rem;
                border-radius: 14px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.84);
                margin-bottom: 0.6rem;
            }

            .painel-disclaimer {
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
        <div class="painel-card">
            <div class="painel-card-label">{label}</div>
            <div class="painel-card-value">{value}</div>
            <div class="painel-card-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _calcular_score_integrado(
    score_decisao: Optional[Any],
    score_conviccao: Optional[Any],
    score_checklist: Optional[Any],
    risco_brasil: Optional[Any],
    risco_fii: Optional[Any],
    risco_renda_fixa: Optional[Any],
) -> int:
    """
    Calcula um score integrado educacional.

    Importante:
    - Score de decisão e convicção são positivos.
    - Scores de risco são negativos. Quanto maior o risco, menor a nota final.
    """
    pontos = []
    pesos = []

    def adicionar(valor: Optional[Any], peso: float, inverter: bool = False) -> None:
        try:
            numero = float(valor)
        except (TypeError, ValueError):
            return

        numero = max(0, min(100, numero))

        if inverter:
            numero = 100 - numero

        pontos.append(numero * peso)
        pesos.append(peso)

    adicionar(score_decisao, 0.30, inverter=False)
    adicionar(score_conviccao, 0.22, inverter=False)
    adicionar(score_checklist, 0.16, inverter=True)
    adicionar(risco_brasil, 0.12, inverter=True)
    adicionar(risco_fii, 0.10, inverter=True)
    adicionar(risco_renda_fixa, 0.10, inverter=True)

    if not pontos or not pesos:
        return 50

    score = sum(pontos) / sum(pesos)
    return int(round(max(0, min(100, score))))


def _classificar_score_integrado(score: int) -> str:
    if score >= 80:
        return "Análise muito forte"
    if score >= 65:
        return "Análise promissora"
    if score >= 50:
        return "Análise em observação"
    if score >= 35:
        return "Análise frágil"
    return "Análise crítica"


def _gerar_leitura_integrada(score: int, classificacao: str) -> str:
    if classificacao == "Análise muito forte":
        return (
            "A análise está bem estruturada nos módulos disponíveis. Ainda assim, isso não significa recomendação: "
            "significa apenas que o raciocínio está mais organizado, com menos fragilidades aparentes."
        )

    if classificacao == "Análise promissora":
        return (
            "A análise possui bons sinais, mas ainda exige revisão. O ideal é validar premissas, riscos específicos, "
            "cenários e qualidade dos dados antes de qualquer decisão real."
        )

    if classificacao == "Análise em observação":
        return (
            "A leitura está intermediária. Existem pontos positivos, mas também incertezas suficientes para exigir "
            "mais estudo, comparação e revisão das premissas."
        )

    if classificacao == "Análise frágil":
        return (
            "A análise mostra fragilidades relevantes. Pode haver excesso de otimismo, risco ignorado ou dados insuficientes. "
            "A ação educacional mais prudente é revisar a tese desde a base."
        )

    return (
        "A análise parece crítica. Antes de avançar, revise dados, premissas, riscos, margem de segurança e adequação "
        "da classe de ativo. Não confie apenas em preço, yield ou taxa."
    )


def renderizar_painel_executivo_multiativos() -> None:
    """
    Renderiza o Painel Executivo Multiativos.
    """
    _injetar_css_painel()

    contexto = _extrair_contexto()

    resumo_decisao = _safe_get_dict("resultado_resumo_decisao")
    conviccao = _safe_get_dict("resultado_conviccao_tese")
    checklist = _safe_get_dict("resultado_checklist_erros")
    acoes_brasil = _safe_get_dict("resultado_acoes_brasil")
    fiis = _safe_get_dict("resultado_fiis")
    renda_fixa = _safe_get_dict("resultado_renda_fixa")

    score_decisao = resumo_decisao.get("score_final")
    classificacao_decisao = resumo_decisao.get("classificacao_decisao")

    score_conviccao = conviccao.get("score_conviccao", st.session_state.get("score_conviccao"))
    classificacao_conviccao = conviccao.get(
        "classificacao_tese",
        st.session_state.get("classificacao_tese"),
    )

    score_checklist = checklist.get("score_risco")
    classificacao_checklist = checklist.get("classificacao_risco")

    risco_brasil = acoes_brasil.get("score_risco_brasil")
    classificacao_brasil = acoes_brasil.get("classificacao_risco_brasil")

    risco_fii = fiis.get("score_risco_fii")
    classificacao_fii = fiis.get("classificacao_risco_fii")

    risco_renda_fixa = renda_fixa.get("score_risco_renda_fixa")
    classificacao_renda_fixa = renda_fixa.get("classificacao_renda_fixa")

    score_integrado = _calcular_score_integrado(
        score_decisao=score_decisao,
        score_conviccao=score_conviccao,
        score_checklist=score_checklist,
        risco_brasil=risco_brasil,
        risco_fii=risco_fii,
        risco_renda_fixa=risco_renda_fixa,
    )

    classificacao_integrada = _classificar_score_integrado(score_integrado)
    leitura_integrada = _gerar_leitura_integrada(score_integrado, classificacao_integrada)

    st.session_state["resultado_painel_multiativos"] = {
        "empresa": contexto["empresa"],
        "ticker": contexto["ticker"],
        "score_integrado": score_integrado,
        "classificacao_integrada": classificacao_integrada,
        "leitura_integrada": leitura_integrada,
        "score_decisao": score_decisao,
        "score_conviccao": score_conviccao,
        "score_checklist": score_checklist,
        "risco_brasil": risco_brasil,
        "risco_fii": risco_fii,
        "risco_renda_fixa": risco_renda_fixa,
    }

    st.markdown(
        """
        <div class="painel-hero">
            <div class="painel-eyebrow">Sala de controle educacional</div>
            <div class="painel-title">Painel Executivo Multiativos</div>
            <div class="painel-subtitle">
                Uma visão consolidada dos principais módulos da Máquina de Preço-Teto:
                valuation, convicção, resumo da decisão, checklist de erros, Ações Brasil, FIIs e Renda Fixa.
                O objetivo é mostrar a qualidade do raciocínio, não recomendar investimento.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Contexto da análise")

    col_ctx_1, col_ctx_2, col_ctx_3, col_ctx_4 = st.columns(4)

    with col_ctx_1:
        st.metric("Ativo", contexto["empresa"])

    with col_ctx_2:
        st.metric("Ticker", contexto["ticker"])

    with col_ctx_3:
        st.metric("Status valuation", contexto["status_valuation"])

    with col_ctx_4:
        st.metric("Preço atual", _fmt_moeda(contexto["preco_atual"], contexto["simbolo_moeda"]))

    st.divider()

    st.markdown("### Score integrado da análise")

    col_score_1, col_score_2, col_score_3 = st.columns(3)

    with col_score_1:
        st.metric("Score integrado", f"{score_integrado}/100")

    with col_score_2:
        st.metric("Classificação", classificacao_integrada)

    with col_score_3:
        st.metric("Preço-teto", _fmt_moeda(contexto["preco_teto"], contexto["simbolo_moeda"]))

    st.progress(score_integrado / 100)

    if score_integrado >= 65:
        st.success(leitura_integrada)
    elif score_integrado >= 50:
        st.warning(leitura_integrada)
    else:
        st.error(leitura_integrada)

    st.divider()

    st.markdown("### Módulos consolidados")

    col1, col2, col3 = st.columns(3)

    with col1:
        _card(
            "Resumo da Decisão",
            _fmt_score(score_decisao),
            f"Classificação: {_fmt_texto(classificacao_decisao)}",
        )

    with col2:
        _card(
            "Convicção da Tese",
            _fmt_score(score_conviccao),
            f"Classificação: {_fmt_texto(classificacao_conviccao)}",
        )

    with col3:
        _card(
            "Checklist de Erros",
            _fmt_score(score_checklist),
            f"Risco: {_fmt_texto(classificacao_checklist)}",
        )

    col4, col5, col6 = st.columns(3)

    with col4:
        _card(
            "Ações Brasil",
            _fmt_score(risco_brasil),
            f"Risco: {_fmt_texto(classificacao_brasil)}",
        )

    with col5:
        _card(
            "FIIs",
            _fmt_score(risco_fii),
            f"Risco: {_fmt_texto(classificacao_fii)}",
        )

    with col6:
        _card(
            "Renda Fixa",
            _fmt_score(risco_renda_fixa),
            f"Risco: {_fmt_texto(classificacao_renda_fixa)}",
        )

    st.divider()

    st.markdown("### Como ler este painel")

    st.markdown(
        """
        Este painel não substitui as abas específicas. Ele apenas consolida a leitura.

        - **Resumo da Decisão** mostra a leitura final do valuation e da tese.
        - **Convicção da Tese** mede qualidade qualitativa da empresa.
        - **Checklist de Erros** procura fragilidades no raciocínio.
        - **Ações Brasil** avalia riscos específicos da B3.
        - **FIIs** avalia renda, patrimônio e risco imobiliário.
        - **Renda Fixa** avalia emissor, prazo, liquidez, indexador e adequação.

        A lógica é: quanto mais módulos preenchidos, mais rica fica a leitura integrada.
        """
    )

    st.markdown("### Próximos passos educacionais")

    proximos_passos = []

    if not resumo_decisao:
        proximos_passos.append("Rodar o Resumo da Decisão para consolidar valuation, tese e cenários.")

    if not conviccao:
        proximos_passos.append("Preencher a Convicção da Tese para avaliar qualidade do negócio.")

    if not checklist:
        proximos_passos.append("Rodar o Checklist de Erros para identificar fragilidades no raciocínio.")

    if contexto["status_valuation"] == "AGUARDE":
        proximos_passos.append("Revisar preço atual, margem de segurança e premissas de valuation.")

    if score_integrado < 50:
        proximos_passos.append("Revisar a análise desde a base antes de confiar no resultado final.")

    if not proximos_passos:
        proximos_passos.append("Revisar os dados, comparar com outras oportunidades e acompanhar a tese ao longo do tempo.")

    for passo in proximos_passos:
        st.markdown(
            f"""
            <div class="painel-alert">
                {passo}
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="painel-disclaimer">
            <strong>Aviso educacional:</strong> este painel não recomenda compra, venda ou manutenção de ativos.
            Ele consolida informações para organizar raciocínio, reduzir erros e melhorar disciplina de análise.
            Toda decisão real deve considerar objetivos pessoais, riscos, diversificação, horizonte de tempo,
            tributação, liquidez e responsabilidade individual.
        </div>
        """,
        unsafe_allow_html=True,
    )