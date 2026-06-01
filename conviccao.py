# conviccao.py

import streamlit as st
from typing import Any, Dict, List


# ============================================================
# MÁQUINA DE PREÇO-TETO
# Motor de Convicção da Tese
# ------------------------------------------------------------
# Este módulo avalia a qualidade qualitativa da tese.
# Não representa recomendação de investimento.
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


def _classificar_tese(score: int) -> str:
    if score >= 80:
        return "FORTE"
    if score >= 65:
        return "BOA"
    if score >= 50:
        return "MODERADA"
    if score >= 35:
        return "FRACA"
    return "RISCO ELEVADO"


def _gerar_leitura_executiva(
    score: int,
    classificacao: str,
    status_valuation: str,
) -> str:
    if classificacao == "FORTE" and status_valuation == "COMPRA":
        return (
            "A tese apresenta alta qualidade qualitativa e o valuation indica preço dentro da zona conservadora. "
            "Mesmo assim, a decisão final exige revisão das premissas, riscos e cenários."
        )

    if classificacao in ["FORTE", "BOA"] and status_valuation == "AGUARDE":
        return (
            "A tese parece qualitativamente interessante, mas o preço atual não parece oferecer margem de segurança suficiente. "
            "A ação educacional mais racional é acompanhar o ativo e esperar uma zona de preço mais favorável."
        )

    if classificacao in ["FORTE", "BOA"] and status_valuation == "NEUTRO":
        return (
            "A tese possui bons elementos qualitativos, mas o preço ainda exige cuidado. "
            "Acompanhe o ativo, revise o preço-teto e compare com outras oportunidades."
        )

    if classificacao == "MODERADA":
        return (
            "A tese ainda não é fraca, mas também não é suficientemente robusta. "
            "É necessário revisar vantagem competitiva, previsibilidade, caixa, dívida, gestão e riscos."
        )

    if classificacao == "FRACA":
        return (
            "A tese apresenta fragilidades relevantes. Antes de confiar no valuation, revise os fundamentos e busque dados mais confiáveis."
        )

    return (
        "A tese apresenta risco elevado. O ativo pode até parecer barato, mas a qualidade da análise ainda não sustenta uma conclusão forte."
    )


def _gerar_alertas(
    vantagem_competitiva: int,
    previsibilidade: int,
    qualidade_caixa: int,
    endividamento: int,
    gestao: int,
    crescimento: int,
    margens: int,
    riscos: int,
    alinhamento_preco: int,
    clareza_tese: int,
) -> List[str]:
    alertas = []

    if vantagem_competitiva <= 4:
        alertas.append(
            "Vantagem competitiva fraca: a empresa pode não ter proteção suficiente contra concorrência."
        )

    if previsibilidade <= 4:
        alertas.append(
            "Baixa previsibilidade: lucros e caixa podem oscilar mais do que o valuation assume."
        )

    if qualidade_caixa <= 4:
        alertas.append(
            "Qualidade do caixa fraca: o lucro pode não estar sendo bem convertido em fluxo de caixa livre."
        )

    if endividamento <= 4:
        alertas.append(
            "Endividamento preocupante: dívida elevada reduz margem de erro e pode pressionar o valor justo."
        )

    if gestao <= 4:
        alertas.append(
            "Gestão pouco confiável: má alocação de capital pode destruir valor no longo prazo."
        )

    if crescimento <= 4:
        alertas.append(
            "Crescimento fraco ou incerto: múltiplos mais altos podem não ser justificáveis."
        )

    if margens <= 4:
        alertas.append(
            "Margens frágeis: queda de rentabilidade pode comprometer lucro, FCF e preço justo."
        )

    if riscos <= 4:
        alertas.append(
            "Riscos relevantes: a tese pode estar ignorando ameaças importantes."
        )

    if alinhamento_preco <= 4:
        alertas.append(
            "Preço pouco alinhado à tese: empresa boa pode virar mau investimento se comprada cara."
        )

    if clareza_tese <= 4:
        alertas.append(
            "Tese pouco clara: se a lógica de investimento não é simples de explicar, ela precisa ser revisada."
        )

    return alertas


def _calcular_score_conviccao(
    vantagem_competitiva: int,
    previsibilidade: int,
    qualidade_caixa: int,
    endividamento: int,
    gestao: int,
    crescimento: int,
    margens: int,
    riscos: int,
    alinhamento_preco: int,
    clareza_tese: int,
) -> int:
    score = (
        vantagem_competitiva * 1.25
        + previsibilidade * 1.15
        + qualidade_caixa * 1.20
        + endividamento * 1.00
        + gestao * 1.10
        + crescimento * 0.95
        + margens * 0.95
        + riscos * 1.05
        + alinhamento_preco * 0.95
        + clareza_tese * 1.00
    )

    score_final = int(round(score))
    return max(0, min(100, score_final))


def _injetar_css_conviccao() -> None:
    st.markdown(
        """
        <style>
            .conv-card {
                padding: 1rem 1.1rem;
                border-radius: 18px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.035);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.16);
                height: 100%;
            }

            .conv-label {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .conv-value {
                color: #f4f7fb;
                font-size: 1.25rem;
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .conv-note {
                color: rgba(244, 247, 251, 0.66);
                font-size: 0.86rem;
                line-height: 1.45;
            }

            .conv-alert {
                padding: 0.82rem 1rem;
                border-radius: 14px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.84);
                margin-bottom: 0.6rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _card(label: str, value: str, note: str = "") -> None:
    st.markdown(
        f"""
        <div class="conv-card">
            <div class="conv-label">{label}</div>
            <div class="conv-value">{value}</div>
            <div class="conv-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def renderizar_aba_conviccao(
    empresa: str,
    ticker: str,
    resultado: Dict[str, Any],
    preparar_tabela,
) -> None:
    """
    Renderiza a aba Convicção da Tese.

    Parâmetros esperados pelo app.py:
    - empresa
    - ticker
    - resultado
    - preparar_tabela
    """
    _injetar_css_conviccao()

    status_valuation = _normalizar_status(resultado.get("status"))

    st.markdown("### Convicção da Tese")

    st.caption(
        "Avalie a qualidade qualitativa da empresa. O objetivo é evitar que uma ação pareça barata apenas por premissas otimistas."
    )

    st.warning(
        "Uso educacional. Esta aba não recomenda compra, venda ou manutenção. "
        "Ela ajuda a organizar a força da tese e seus riscos."
    )

    st.divider()

    col_topo_1, col_topo_2, col_topo_3 = st.columns(3)

    with col_topo_1:
        st.metric("Empresa", empresa)

    with col_topo_2:
        st.metric("Ticker", ticker.upper())

    with col_topo_3:
        st.metric("Status valuation", status_valuation)

    st.divider()

    st.markdown("### Diagnóstico qualitativo")

    st.caption(
        "Dê notas de 0 a 10. Quanto maior a nota, melhor a qualidade percebida naquele critério."
    )

    col1, col2 = st.columns(2)

    with col1:
        vantagem_competitiva = st.slider(
            "Vantagem competitiva",
            min_value=0,
            max_value=10,
            value=7,
            help="A empresa possui marca forte, escala, rede, custo baixo, switching cost ou outro diferencial defensável?",
            key=f"conv_vantagem_{ticker}",
        )

        previsibilidade = st.slider(
            "Previsibilidade dos resultados",
            min_value=0,
            max_value=10,
            value=7,
            help="A receita, o lucro e o caixa são previsíveis ou muito cíclicos?",
            key=f"conv_previsibilidade_{ticker}",
        )

        qualidade_caixa = st.slider(
            "Qualidade do caixa",
            min_value=0,
            max_value=10,
            value=7,
            help="O lucro se transforma em fluxo de caixa livre de forma consistente?",
            key=f"conv_caixa_{ticker}",
        )

        endividamento = st.slider(
            "Saúde financeira / endividamento",
            min_value=0,
            max_value=10,
            value=7,
            help="A dívida é controlada e compatível com a geração de caixa?",
            key=f"conv_endividamento_{ticker}",
        )

        gestao = st.slider(
            "Qualidade da gestão",
            min_value=0,
            max_value=10,
            value=7,
            help="A gestão aloca bem o capital, comunica bem e protege o acionista?",
            key=f"conv_gestao_{ticker}",
        )

    with col2:
        crescimento = st.slider(
            "Crescimento sustentável",
            min_value=0,
            max_value=10,
            value=6,
            help="A empresa tem espaço realista para crescer sem depender de premissas agressivas?",
            key=f"conv_crescimento_{ticker}",
        )

        margens = st.slider(
            "Qualidade das margens",
            min_value=0,
            max_value=10,
            value=6,
            help="As margens são fortes, estáveis e defensáveis?",
            key=f"conv_margens_{ticker}",
        )

        riscos = st.slider(
            "Controle dos riscos",
            min_value=0,
            max_value=10,
            value=6,
            help="Quanto maior a nota, melhor a tese lida com riscos de concorrência, regulação, ciclo, dívida e tecnologia.",
            key=f"conv_riscos_{ticker}",
        )

        alinhamento_preco = st.slider(
            "Alinhamento entre preço e qualidade",
            min_value=0,
            max_value=10,
            value=6,
            help="O preço atual faz sentido em relação à qualidade do negócio?",
            key=f"conv_preco_{ticker}",
        )

        clareza_tese = st.slider(
            "Clareza da tese",
            min_value=0,
            max_value=10,
            value=7,
            help="A tese é clara, objetiva e fácil de explicar?",
            key=f"conv_clareza_{ticker}",
        )

    score_conviccao = _calcular_score_conviccao(
        vantagem_competitiva=vantagem_competitiva,
        previsibilidade=previsibilidade,
        qualidade_caixa=qualidade_caixa,
        endividamento=endividamento,
        gestao=gestao,
        crescimento=crescimento,
        margens=margens,
        riscos=riscos,
        alinhamento_preco=alinhamento_preco,
        clareza_tese=clareza_tese,
    )

    classificacao_tese = _classificar_tese(score_conviccao)

    leitura_executiva = _gerar_leitura_executiva(
        score=score_conviccao,
        classificacao=classificacao_tese,
        status_valuation=status_valuation,
    )

    alertas = _gerar_alertas(
        vantagem_competitiva=vantagem_competitiva,
        previsibilidade=previsibilidade,
        qualidade_caixa=qualidade_caixa,
        endividamento=endividamento,
        gestao=gestao,
        crescimento=crescimento,
        margens=margens,
        riscos=riscos,
        alinhamento_preco=alinhamento_preco,
        clareza_tese=clareza_tese,
    )

    matriz_qualitativa = {
        "Vantagem competitiva": vantagem_competitiva,
        "Previsibilidade": previsibilidade,
        "Qualidade do caixa": qualidade_caixa,
        "Endividamento": endividamento,
        "Gestão": gestao,
        "Crescimento": crescimento,
        "Margens": margens,
        "Riscos": riscos,
        "Alinhamento preço/qualidade": alinhamento_preco,
        "Clareza da tese": clareza_tese,
    }

    resultado_conviccao = {
        "empresa": empresa,
        "ticker": ticker.upper(),
        "status_valuation": status_valuation,
        "score_conviccao": score_conviccao,
        "classificacao_tese": classificacao_tese,
        "leitura_executiva": leitura_executiva,
        "alertas": alertas,
        "matriz_qualitativa": matriz_qualitativa,
    }

    st.session_state["resultado_conviccao_tese"] = resultado_conviccao
    st.session_state["score_conviccao"] = score_conviccao
    st.session_state["classificacao_tese"] = classificacao_tese
    st.session_state["alertas_conviccao"] = alertas

    st.divider()

    st.markdown("### Resultado da convicção")

    col_res_1, col_res_2, col_res_3 = st.columns(3)

    with col_res_1:
        st.metric("Score de convicção", f"{score_conviccao}/100")

    with col_res_2:
        st.metric("Classificação da tese", classificacao_tese)

    with col_res_3:
        st.metric("Alertas", len(alertas))

    st.progress(score_conviccao / 100)

    if score_conviccao >= 70:
        st.success("A tese apresenta bons sinais qualitativos para as premissas atuais.")
    elif score_conviccao >= 50:
        st.warning("A tese possui pontos positivos, mas ainda exige revisão.")
    else:
        st.error("A tese apresenta fragilidades relevantes.")

    st.markdown("### Leitura executiva")
    st.info(leitura_executiva)

    st.markdown("### Alertas qualitativos")

    if len(alertas) == 0:
        st.success(
            "Nenhum alerta crítico foi identificado. Ainda assim, revise dados, riscos e premissas."
        )
    else:
        for alerta in alertas:
            st.markdown(
                f"""
                <div class="conv-alert">
                    {alerta}
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.divider()

    st.markdown("### Matriz qualitativa")

    tabela_matriz = [
        {
            "Critério": criterio,
            "Nota": nota,
        }
        for criterio, nota in matriz_qualitativa.items()
    ]

    st.table(preparar_tabela(tabela_matriz))

    st.markdown("### Perguntas críticas")

    st.markdown(
        """
        - A empresa realmente possui vantagem competitiva defensável?
        - O lucro é previsível ou depende de ciclo favorável?
        - O fluxo de caixa confirma a qualidade do lucro?
        - A dívida permite atravessar cenários difíceis?
        - A gestão aloca capital com racionalidade?
        - O preço atual compensa os riscos da tese?
        - A tese continua válida em cenário conservador?
        """
    )