import streamlit as st


def calcular_score_conviccao(
    previsibilidade_lucro: int,
    qualidade_fcf: int,
    vantagem_competitiva: int,
    qualidade_tese: int,
    risco_endividamento: int,
    ciclicidade: int,
    dependencia_premissas_otimistas: int,
    risco_valuation_esticado: int,
) -> int:
    score = 0

    score += previsibilidade_lucro * 1.5
    score += qualidade_fcf * 1.5
    score += vantagem_competitiva * 1.5
    score += qualidade_tese * 1.5

    score += (10 - risco_endividamento) * 1.0
    score += (10 - ciclicidade) * 1.0
    score += (10 - dependencia_premissas_otimistas) * 1.0
    score += (10 - risco_valuation_esticado) * 1.0

    return round(max(0, min(score, 100)))


def classificar_conviccao(score: int) -> str:
    if score >= 80:
        return "ALTA"
    if score >= 65:
        return "FORTE"
    if score >= 45:
        return "MODERADA"
    return "FRACA"


def gerar_leitura_conviccao(
    score: int,
    classificacao: str,
    status_valuation: str,
) -> str:
    if classificacao == "ALTA" and status_valuation == "COMPRA":
        return (
            "A tese parece forte e o preço está dentro da zona conservadora do modelo. "
            "Esse é o melhor alinhamento possível entre qualidade da tese e valuation, desde que as premissas estejam corretas."
        )

    if classificacao in ["ALTA", "FORTE"] and status_valuation in ["NEUTRO", "AGUARDE"]:
        return (
            "A tese parece boa, mas o preço ainda não oferece margem de segurança suficiente pelo modelo atual. "
            "Esse é um caso típico de boa empresa que exige paciência no preço."
        )

    if classificacao in ["FRACA", "MODERADA"] and status_valuation == "COMPRA":
        return (
            "O preço pode parecer atrativo, mas a tese não parece suficientemente robusta. "
            "Esse é um alerta clássico: valuation barato não compensa uma tese frágil sem análise profunda."
        )

    if classificacao == "FRACA" and status_valuation == "AGUARDE":
        return (
            "A tese parece frágil e o preço também não está atrativo pelo modelo. "
            "O melhor uso dessa análise é revisar premissas, entender riscos e evitar decisões apressadas."
        )

    return (
        "A convicção da tese está em zona intermediária. "
        "O ideal é aprofundar a análise qualitativa antes de depender do preço-teto como referência decisória."
    )


def gerar_alertas_conviccao(
    risco_endividamento: int,
    ciclicidade: int,
    dependencia_premissas_otimistas: int,
    risco_valuation_esticado: int,
    previsibilidade_lucro: int,
    qualidade_fcf: int,
) -> list[str]:
    alertas = []

    if risco_endividamento >= 7:
        alertas.append("Endividamento elevado pode reduzir a margem de segurança real da tese.")

    if ciclicidade >= 7:
        alertas.append("Alta ciclicidade pode distorcer lucro, FCF e múltiplos justos.")

    if dependencia_premissas_otimistas >= 7:
        alertas.append("A tese depende demais de premissas otimistas. Isso aumenta risco de erro no valuation.")

    if risco_valuation_esticado >= 7:
        alertas.append("O valuation parece esticado. Mesmo uma boa empresa pode ser ruim se comprada cara.")

    if previsibilidade_lucro <= 4:
        alertas.append("Baixa previsibilidade de lucro reduz a confiabilidade do preço-teto.")

    if qualidade_fcf <= 4:
        alertas.append("Fluxo de caixa fraco ou irregular pode tornar o lucro contábil pouco confiável.")

    if len(alertas) == 0:
        alertas.append("Nenhum alerta crítico foi identificado pelos critérios qualitativos selecionados.")

    return alertas


def renderizar_motor_conviccao(
    empresa: str,
    ticker: str,
    status_valuation: str,
    margem_ate_preco_teto: float,
    potencial_ate_preco_justo: float,
    formatar_percentual,
) -> dict:
    st.markdown("### Motor de Convicção da Tese")

    st.caption(
        "Esta camada avalia a força qualitativa da tese. "
        "O objetivo é evitar que o usuário dependa apenas do preço-teto sem analisar qualidade, riscos e robustez das premissas."
    )

    st.warning(
        "O score de convicção é educacional e subjetivo. Ele não representa recomendação de investimento."
    )

    st.divider()

    st.markdown(f"### Avaliação qualitativa: {empresa} ({ticker})")

    col_qualidade, col_risco = st.columns(2)

    with col_qualidade:
        with st.container(border=True):
            st.markdown("#### Força da tese")

            previsibilidade_lucro = st.slider(
                "Previsibilidade do lucro",
                min_value=0,
                max_value=10,
                value=7,
                help="Quanto maior, mais previsível e recorrente é o lucro da empresa.",
                key=f"conviccao_previsibilidade_{ticker}",
            )

            qualidade_fcf = st.slider(
                "Qualidade do fluxo de caixa livre",
                min_value=0,
                max_value=10,
                value=7,
                help="Quanto maior, mais consistente e confiável é a geração de caixa livre.",
                key=f"conviccao_fcf_{ticker}",
            )

            vantagem_competitiva = st.slider(
                "Vantagem competitiva",
                min_value=0,
                max_value=10,
                value=7,
                help="Avalia barreiras de entrada, marca, escala, rede, switching cost ou posição competitiva.",
                key=f"conviccao_vantagem_{ticker}",
            )

            qualidade_tese = st.slider(
                "Qualidade geral da tese",
                min_value=0,
                max_value=10,
                value=7,
                help="Avalia se a tese é clara, objetiva, sustentável e baseada em fundamentos reais.",
                key=f"conviccao_tese_{ticker}",
            )

    with col_risco:
        with st.container(border=True):
            st.markdown("#### Riscos da tese")

            risco_endividamento = st.slider(
                "Risco de endividamento",
                min_value=0,
                max_value=10,
                value=4,
                help="Quanto maior, mais o endividamento ameaça a tese.",
                key=f"conviccao_endividamento_{ticker}",
            )

            ciclicidade = st.slider(
                "Ciclicidade do negócio",
                min_value=0,
                max_value=10,
                value=4,
                help="Quanto maior, mais os resultados dependem de ciclos econômicos ou setoriais.",
                key=f"conviccao_ciclicidade_{ticker}",
            )

            dependencia_premissas_otimistas = st.slider(
                "Dependência de premissas otimistas",
                min_value=0,
                max_value=10,
                value=5,
                help="Quanto maior, mais a tese depende de um futuro muito favorável.",
                key=f"conviccao_premissas_{ticker}",
            )

            risco_valuation_esticado = st.slider(
                "Risco de valuation esticado",
                min_value=0,
                max_value=10,
                value=5,
                help="Quanto maior, maior o risco de pagar caro demais mesmo em uma boa empresa.",
                key=f"conviccao_valuation_{ticker}",
            )

    score = calcular_score_conviccao(
        previsibilidade_lucro=previsibilidade_lucro,
        qualidade_fcf=qualidade_fcf,
        vantagem_competitiva=vantagem_competitiva,
        qualidade_tese=qualidade_tese,
        risco_endividamento=risco_endividamento,
        ciclicidade=ciclicidade,
        dependencia_premissas_otimistas=dependencia_premissas_otimistas,
        risco_valuation_esticado=risco_valuation_esticado,
    )

    classificacao = classificar_conviccao(score)

    leitura = gerar_leitura_conviccao(
        score=score,
        classificacao=classificacao,
        status_valuation=status_valuation,
    )

    alertas = gerar_alertas_conviccao(
        risco_endividamento=risco_endividamento,
        ciclicidade=ciclicidade,
        dependencia_premissas_otimistas=dependencia_premissas_otimistas,
        risco_valuation_esticado=risco_valuation_esticado,
        previsibilidade_lucro=previsibilidade_lucro,
        qualidade_fcf=qualidade_fcf,
    )

    st.divider()

    st.markdown("### Resultado da convicção")

    col_score_1, col_score_2, col_score_3, col_score_4 = st.columns(4)

    with col_score_1:
        st.metric("Score de convicção", f"{score}/100")

    with col_score_2:
        st.metric("Classificação", classificacao)

    with col_score_3:
        st.metric("Status valuation", status_valuation)

    with col_score_4:
        st.metric("Margem até teto", formatar_percentual(margem_ate_preco_teto))

    st.progress(score / 100)

    if classificacao in ["ALTA", "FORTE"]:
        st.success(f"Convicção {classificacao}: a tese qualitativa parece robusta pelos critérios selecionados.")
    elif classificacao == "MODERADA":
        st.warning("Convicção MODERADA: a tese exige mais validação antes de sustentar uma decisão forte.")
    else:
        st.error("Convicção FRACA: o valuation não deve ser usado sem revisar profundamente a tese.")

    st.info(f"**Leitura executiva:** {leitura}")

    st.divider()

    st.markdown("### Alertas qualitativos")

    for alerta in alertas:
        st.warning(alerta)

    st.divider()

    st.markdown("### Matriz tese x preço")

    col_matriz_1, col_matriz_2 = st.columns(2)

    with col_matriz_1:
        st.markdown(
            f"""
            **Dados do valuation atual**

            - Status: **{status_valuation}**
            - Margem até preço-teto: **{formatar_percentual(margem_ate_preco_teto)}**
            - Potencial até preço justo: **{formatar_percentual(potencial_ate_preco_justo)}**
            """
        )

    with col_matriz_2:
        if classificacao in ["ALTA", "FORTE"] and status_valuation == "COMPRA":
            st.success("Tese forte + preço atrativo: melhor combinação do modelo.")
        elif classificacao in ["ALTA", "FORTE"] and status_valuation != "COMPRA":
            st.warning("Tese forte + preço ainda exigente: monitorar com disciplina.")
        elif classificacao in ["FRACA", "MODERADA"] and status_valuation == "COMPRA":
            st.warning("Preço atrativo + tese frágil: risco de armadilha de valor.")
        else:
            st.error("Tese frágil + preço exigente: baixa prioridade pelo modelo.")

    resultado_conviccao = {
        "score": score,
        "classificacao": classificacao,
        "leitura": leitura,
        "alertas": alertas,
        "previsibilidade_lucro": previsibilidade_lucro,
        "qualidade_fcf": qualidade_fcf,
        "vantagem_competitiva": vantagem_competitiva,
        "qualidade_tese": qualidade_tese,
        "risco_endividamento": risco_endividamento,
        "ciclicidade": ciclicidade,
        "dependencia_premissas_otimistas": dependencia_premissas_otimistas,
        "risco_valuation_esticado": risco_valuation_esticado,
    }

    st.session_state["conviccao_atual"] = resultado_conviccao

    return resultado_conviccao