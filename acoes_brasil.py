# acoes_brasil.py

import streamlit as st
from typing import Any, Dict, Optional


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v1.16 — Motor Inicial de Ações Brasil
# ------------------------------------------------------------
# Este módulo adapta a leitura educacional para empresas da B3.
# Ele não recomenda compra/venda.
# Ele adiciona uma camada de risco Brasil, governança, dividendos,
# endividamento, setor regulado, commodities e qualidade da tese.
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


def _extrair_contexto_valuation(
    resultado_valuation: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    dados = {}

    if isinstance(st.session_state.get("resultado_valuation"), dict):
        dados.update(st.session_state["resultado_valuation"])

    if isinstance(resultado_valuation, dict):
        dados.update(resultado_valuation)

    return {
        "empresa": dados.get("empresa", "Empresa brasileira analisada"),
        "ticker": dados.get("ticker", "N/D"),
        "status": _normalizar_status(
            dados.get("status_valuation", dados.get("status", "N/D"))
        ),
        "preco_atual": dados.get("preco_atual"),
        "preco_teto": dados.get("preco_teto"),
        "preco_justo": dados.get("preco_justo", dados.get("preco_justo_combinado")),
        "margem_ate_preco_teto": dados.get("margem_ate_preco_teto"),
        "potencial_ate_preco_justo": dados.get("potencial_ate_preco_justo"),
    }


def _classificar_risco_brasil(score_risco: int) -> str:
    if score_risco <= 25:
        return "Risco Brasil controlado"
    if score_risco <= 50:
        return "Atenção moderada"
    if score_risco <= 75:
        return "Risco Brasil elevado"
    return "Risco crítico para a tese"


def _gerar_leitura_risco_brasil(score_risco: int, classificacao: str) -> str:
    if classificacao == "Risco Brasil controlado":
        return (
            "A análise indica uma estrutura relativamente controlada para uma empresa brasileira. "
            "Mesmo assim, revise juros, governança, endividamento, setor e dependência macroeconômica."
        )

    if classificacao == "Atenção moderada":
        return (
            "A empresa apresenta alguns pontos de atenção típicos do mercado brasileiro. "
            "A análise ainda pode ser válida, mas exige margem de segurança maior e premissas mais conservadoras."
        )

    if classificacao == "Risco Brasil elevado":
        return (
            "A tese está exposta a riscos relevantes de Brasil, governança, ciclo econômico, dívida, regulação ou commodities. "
            "Antes de confiar no preço-teto, revise as premissas e aumente o rigor da análise."
        )

    return (
        "O conjunto de riscos é crítico. A empresa pode até parecer barata no valuation, "
        "mas a tese pode estar frágil se os riscos estruturais não forem bem compensados pelo preço."
    )


def _injetar_css_acoes_brasil() -> None:
    st.markdown(
        """
        <style>
            .br-hero {
                padding: 1.45rem 1.5rem;
                border-radius: 24px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    radial-gradient(circle at top left, rgba(26, 188, 156, 0.18), transparent 30%),
                    radial-gradient(circle at bottom right, rgba(214, 181, 109, 0.16), transparent 34%),
                    linear-gradient(135deg, rgba(8, 15, 24, 0.98), rgba(5, 10, 18, 0.98));
                box-shadow: 0 18px 55px rgba(0, 0, 0, 0.30);
                margin-bottom: 1.25rem;
            }

            .br-eyebrow {
                color: #d6b56d;
                font-size: 0.78rem;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .br-title {
                color: #f4f7fb;
                font-size: 1.75rem;
                font-weight: 850;
                margin-bottom: 0.45rem;
            }

            .br-subtitle {
                color: rgba(244, 247, 251, 0.74);
                font-size: 0.96rem;
                line-height: 1.58;
                max-width: 980px;
            }

            .br-card {
                padding: 1.05rem 1.1rem;
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.035);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.18);
                height: 100%;
            }

            .br-card-label {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .br-card-value {
                color: #f4f7fb;
                font-size: 1.25rem;
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .br-card-note {
                color: rgba(244, 247, 251, 0.66);
                font-size: 0.86rem;
                line-height: 1.45;
            }

            .br-alert {
                padding: 0.82rem 1rem;
                border-radius: 14px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.84);
                margin-bottom: 0.6rem;
            }

            .br-disclaimer {
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
        <div class="br-card">
            <div class="br-card-label">{label}</div>
            <div class="br-card-value">{value}</div>
            <div class="br-card-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _calcular_score_risco_brasil(
    risco_governanca: int,
    risco_endividamento: int,
    risco_juros: int,
    risco_regulatorio: int,
    risco_estatal: int,
    risco_commodity: int,
    risco_cambial: int,
    qualidade_dividendos: int,
    qualidade_alocacao: int,
    previsibilidade: int,
) -> int:
    """
    Quanto maior o score, maior o risco da análise.
    As notas de entrada são notas de qualidade de 0 a 10.
    Para transformar em risco, usamos 10 - nota.
    """
    score = (
        (10 - risco_governanca) * 1.30
        + (10 - risco_endividamento) * 1.25
        + (10 - risco_juros) * 1.05
        + (10 - risco_regulatorio) * 1.10
        + (10 - risco_estatal) * 0.90
        + (10 - risco_commodity) * 0.85
        + (10 - risco_cambial) * 0.75
        + (10 - qualidade_dividendos) * 0.90
        + (10 - qualidade_alocacao) * 1.05
        + (10 - previsibilidade) * 0.85
    )

    score_final = int(round(score))
    return max(0, min(100, score_final))


def _gerar_alertas_brasil(
    risco_governanca: int,
    risco_endividamento: int,
    risco_juros: int,
    risco_regulatorio: int,
    risco_estatal: int,
    risco_commodity: int,
    risco_cambial: int,
    qualidade_dividendos: int,
    qualidade_alocacao: int,
    previsibilidade: int,
) -> list[str]:
    alertas = []

    if risco_governanca <= 4:
        alertas.append(
            "Governança frágil: empresas brasileiras com baixa governança exigem margem de segurança maior."
        )

    if risco_endividamento <= 4:
        alertas.append(
            "Endividamento preocupante: em ambiente de juros altos, dívida pode pressionar lucro, dividendos e valuation."
        )

    if risco_juros <= 4:
        alertas.append(
            "Alta sensibilidade aos juros: o custo de capital no Brasil pode mudar rapidamente a atratividade do ativo."
        )

    if risco_regulatorio <= 4:
        alertas.append(
            "Risco regulatório relevante: mudanças de regras podem afetar margens, crescimento e previsibilidade."
        )

    if risco_estatal <= 4:
        alertas.append(
            "Risco estatal/político: interferência pública pode reduzir racionalidade econômica da tese."
        )

    if risco_commodity <= 4:
        alertas.append(
            "Dependência de commodities: lucro pode estar mais ligado ao ciclo global do que à qualidade operacional."
        )

    if risco_cambial <= 4:
        alertas.append(
            "Risco cambial relevante: câmbio pode distorcer custos, receitas, dívida ou resultado financeiro."
        )

    if qualidade_dividendos <= 4:
        alertas.append(
            "Dividendos pouco confiáveis: payout alto ou dividendos extraordinários não devem ser tratados como renda permanente."
        )

    if qualidade_alocacao <= 4:
        alertas.append(
            "Alocação de capital fraca: recompras ruins, aquisições caras ou projetos de baixo retorno podem destruir valor."
        )

    if previsibilidade <= 4:
        alertas.append(
            "Baixa previsibilidade: a empresa pode exigir lucro normalizado e premissas mais conservadoras."
        )

    return alertas


def renderizar_motor_acoes_brasil(
    resultado_valuation: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Renderiza o Motor Inicial de Ações Brasil.
    """
    _injetar_css_acoes_brasil()

    contexto = _extrair_contexto_valuation(resultado_valuation)

    st.markdown(
        """
        <div class="br-hero">
            <div class="br-eyebrow">Motor educacional Brasil</div>
            <div class="br-title">Ações Brasil — Camada de Risco e Qualidade</div>
            <div class="br-subtitle">
                Empresas brasileiras podem ser avaliadas com lucro, fluxo de caixa e múltiplos, mas exigem filtros adicionais:
                governança, dívida, juros, regulação, risco estatal, commodities, câmbio, dividendos e alocação de capital.
                Este módulo não substitui o valuation: ele audita a qualidade da tese no contexto brasileiro.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_ctx_1, col_ctx_2, col_ctx_3 = st.columns(3)

    with col_ctx_1:
        st.metric("Empresa analisada", contexto["empresa"])

    with col_ctx_2:
        st.metric("Ticker", contexto["ticker"])

    with col_ctx_3:
        st.metric("Status valuation", contexto["status"])

    st.divider()

    st.markdown("### Diagnóstico Brasil")

    st.caption(
        "Dê notas de 0 a 10. Quanto maior a nota, melhor a qualidade ou menor o risco percebido naquele critério."
    )

    col1, col2 = st.columns(2)

    with col1:
        risco_governanca = st.slider(
            "Governança corporativa",
            min_value=0,
            max_value=10,
            value=7,
            help="Nota alta significa governança mais confiável, alinhamento com minoritários e menor risco de abuso.",
            key="br_governanca",
        )

        risco_endividamento = st.slider(
            "Saúde financeira / endividamento",
            min_value=0,
            max_value=10,
            value=7,
            help="Nota alta significa dívida mais controlada e menor pressão financeira.",
            key="br_endividamento",
        )

        risco_juros = st.slider(
            "Resistência a juros altos",
            min_value=0,
            max_value=10,
            value=6,
            help="Nota alta significa que a empresa sofre menos com juros elevados.",
            key="br_juros",
        )

        risco_regulatorio = st.slider(
            "Baixo risco regulatório",
            min_value=0,
            max_value=10,
            value=6,
            help="Nota alta significa menor dependência de regras, concessões, tarifas ou interferência regulatória.",
            key="br_regulatorio",
        )

        risco_estatal = st.slider(
            "Baixo risco estatal/político",
            min_value=0,
            max_value=10,
            value=7,
            help="Nota alta significa menor risco de interferência política ou controle estatal destrutivo.",
            key="br_estatal",
        )

    with col2:
        risco_commodity = st.slider(
            "Baixa dependência de commodities",
            min_value=0,
            max_value=10,
            value=6,
            help="Nota alta significa menor dependência de ciclos de minério, petróleo, papel e celulose, agro etc.",
            key="br_commodity",
        )

        risco_cambial = st.slider(
            "Baixo risco cambial",
            min_value=0,
            max_value=10,
            value=6,
            help="Nota alta significa menor distorção por dólar em custos, receitas ou dívida.",
            key="br_cambial",
        )

        qualidade_dividendos = st.slider(
            "Qualidade dos dividendos",
            min_value=0,
            max_value=10,
            value=6,
            help="Nota alta significa dividendos recorrentes, sustentáveis e compatíveis com geração de caixa.",
            key="br_dividendos",
        )

        qualidade_alocacao = st.slider(
            "Qualidade da alocação de capital",
            min_value=0,
            max_value=10,
            value=6,
            help="Nota alta significa boa gestão de reinvestimentos, dividendos, recompras e aquisições.",
            key="br_alocacao",
        )

        previsibilidade = st.slider(
            "Previsibilidade dos resultados",
            min_value=0,
            max_value=10,
            value=6,
            help="Nota alta significa menor ciclicidade e maior confiança no lucro normalizado.",
            key="br_previsibilidade",
        )

    score_risco = _calcular_score_risco_brasil(
        risco_governanca=risco_governanca,
        risco_endividamento=risco_endividamento,
        risco_juros=risco_juros,
        risco_regulatorio=risco_regulatorio,
        risco_estatal=risco_estatal,
        risco_commodity=risco_commodity,
        risco_cambial=risco_cambial,
        qualidade_dividendos=qualidade_dividendos,
        qualidade_alocacao=qualidade_alocacao,
        previsibilidade=previsibilidade,
    )

    classificacao = _classificar_risco_brasil(score_risco)
    leitura = _gerar_leitura_risco_brasil(score_risco, classificacao)

    alertas = _gerar_alertas_brasil(
        risco_governanca=risco_governanca,
        risco_endividamento=risco_endividamento,
        risco_juros=risco_juros,
        risco_regulatorio=risco_regulatorio,
        risco_estatal=risco_estatal,
        risco_commodity=risco_commodity,
        risco_cambial=risco_cambial,
        qualidade_dividendos=qualidade_dividendos,
        qualidade_alocacao=qualidade_alocacao,
        previsibilidade=previsibilidade,
    )

    st.divider()

    st.markdown("### Resultado da camada Brasil")

    col_res_1, col_res_2, col_res_3 = st.columns(3)

    with col_res_1:
        st.metric("Score de risco Brasil", f"{score_risco}/100")

    with col_res_2:
        st.metric("Classificação", classificacao)

    with col_res_3:
        st.metric("Alertas", len(alertas))

    st.progress(score_risco / 100)

    if score_risco <= 25:
        st.success("A camada Brasil parece controlada para as notas atuais.")
    elif score_risco <= 50:
        st.warning("Existem pontos de atenção relevantes na camada Brasil.")
    else:
        st.error("A camada Brasil mostra riscos importantes que podem comprometer a tese.")

    st.markdown("### Leitura educacional")
    st.info(leitura)

    st.markdown("### Alertas específicos")

    if len(alertas) == 0:
        st.success(
            "Nenhum alerta crítico foi identificado. Ainda assim, revise os dados, o setor e o contexto macroeconômico."
        )
    else:
        for alerta in alertas:
            st.markdown(
                f"""
                <div class="br-alert">
                    {alerta}
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.divider()

    st.markdown("### Como interpretar ações brasileiras")

    col_info_1, col_info_2, col_info_3 = st.columns(3)

    with col_info_1:
        _card(
            "Dividendos",
            "Sustentabilidade",
            "Dividend yield alto não basta. O dividendo precisa vir de lucro e caixa recorrentes.",
        )

    with col_info_2:
        _card(
            "Juros",
            "Custo de capital",
            "No Brasil, juros altos podem reduzir valuation, aumentar dívida e mudar a atratividade relativa.",
        )

    with col_info_3:
        _card(
            "Governança",
            "Risco invisível",
            "Governança fraca pode transformar empresa aparentemente barata em armadilha de valor.",
        )

    st.markdown("### Perguntas críticas antes de concluir")

    st.markdown(
        """
        - O lucro usado é realmente recorrente?
        - O fluxo de caixa confirma o lucro?
        - A dívida é administrável em cenário de juros altos?
        - Os dividendos são sustentáveis ou extraordinários?
        - A empresa depende demais de commodity, câmbio, governo ou regulação?
        - A governança protege ou prejudica o acionista minoritário?
        - O preço compensa os riscos específicos do Brasil?
        """
    )

    resultado_brasil = {
        "empresa": contexto["empresa"],
        "ticker": contexto["ticker"],
        "score_risco_brasil": score_risco,
        "classificacao_risco_brasil": classificacao,
        "leitura_risco_brasil": leitura,
        "alertas_brasil": alertas,
        "notas": {
            "governanca": risco_governanca,
            "endividamento": risco_endividamento,
            "juros": risco_juros,
            "regulatorio": risco_regulatorio,
            "estatal": risco_estatal,
            "commodity": risco_commodity,
            "cambial": risco_cambial,
            "dividendos": qualidade_dividendos,
            "alocacao": qualidade_alocacao,
            "previsibilidade": previsibilidade,
        },
    }

    st.session_state["resultado_acoes_brasil"] = resultado_brasil

    st.markdown(
        """
        <div class="br-disclaimer">
            <strong>Aviso educacional:</strong> esta leitura não representa recomendação de investimento.
            O módulo de Ações Brasil adiciona uma camada de análise de risco e qualidade ao valuation.
            Toda decisão real deve considerar objetivos pessoais, diversificação, horizonte de tempo,
            riscos específicos e responsabilidade individual.
        </div>
        """,
        unsafe_allow_html=True,
    )