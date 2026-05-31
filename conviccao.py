import streamlit as st


def classificar_conviccao(score: float) -> str:
    if score >= 80:
        return "FORTE"
    if score >= 65:
        return "BOA"
    if score >= 50:
        return "MODERADA"
    if score >= 35:
        return "FRACA"
    return "RISCO ELEVADO"


def gerar_alertas_conviccao(
    previsibilidade: int,
    qualidade_caixa: int,
    endividamento: int,
    vantagem_competitiva: int,
    risco_negocio: int,
    dependencia_premissas: int,
    qualidade_dados: int,
) -> list[str]:
    alertas = []

    if previsibilidade <= 4:
        alertas.append(
            "A previsibilidade dos resultados parece baixa. Isso reduz a confiança nas projeções de lucro e fluxo de caixa."
        )

    if qualidade_caixa <= 4:
        alertas.append(
            "A qualidade da geração de caixa parece fraca. O valuation pode estar dependendo demais do lucro contábil."
        )

    if endividamento <= 4:
        alertas.append(
            "O nível de endividamento ou risco financeiro exige atenção antes de elevar a convicção."
        )

    if vantagem_competitiva <= 4:
        alertas.append(
            "A vantagem competitiva parece limitada. Empresas sem proteção clara podem merecer múltiplos mais conservadores."
        )

    if risco_negocio <= 4:
        alertas.append(
            "Os riscos do negócio parecem relevantes. Regulação, concorrência, ciclicidade ou perda de margem podem afetar a tese."
        )

    if dependencia_premissas <= 4:
        alertas.append(
            "A tese parece depender demais de premissas otimistas. Revise crescimento, margens, múltiplos e margem de segurança."
        )

    if qualidade_dados <= 4:
        alertas.append(
            "A qualidade dos dados usados na análise parece limitada. Dados ruins produzem valuation frágil."
        )

    return alertas


def gerar_leitura_executiva(
    score: float,
    classificacao: str,
    status_valuation: str,
    alertas: list[str],
) -> str:
    if classificacao == "FORTE" and status_valuation == "COMPRA":
        return (
            "A tese apresenta alta qualidade qualitativa e o valuation indica uma zona educacionalmente atrativa. "
            "Mesmo assim, a leitura deve ser validada com premissas conservadoras, comparação com pares e revisão dos riscos."
        )

    if classificacao in ["FORTE", "BOA"] and status_valuation == "AGUARDE":
        return (
            "A empresa pode ter uma tese interessante, mas o preço atual ainda não oferece margem de segurança suficiente. "
            "A ação mais disciplinada é acompanhar a empresa e aguardar uma assimetria melhor."
        )

    if classificacao in ["FORTE", "BOA"] and status_valuation == "NEUTRO":
        return (
            "A tese tem pontos positivos, mas o preço ainda não entrega uma oportunidade clara. "
            "O ideal é monitorar, revisar premissas e comparar com outras empresas de qualidade."
        )

    if classificacao == "MODERADA":
        return (
            "A tese ainda não é fraca, mas também não é suficientemente robusta. "
            "Antes de aumentar a convicção, revise dados, riscos, vantagem competitiva e qualidade da geração de caixa."
        )

    if classificacao in ["FRACA", "RISCO ELEVADO"]:
        return (
            "A análise qualitativa mostra fragilidades importantes. "
            "Neste momento, a prioridade educacional deve ser entender melhor o negócio, os riscos e a confiabilidade das premissas."
        )

    if len(alertas) >= 4:
        return (
            "A quantidade de alertas qualitativos é elevada. "
            "Isso sugere que o valuation deve ser tratado com bastante cautela."
        )

    return (
        "A leitura qualitativa está em zona intermediária. "
        "Use esta análise como apoio para pensar melhor, não como conclusão final."
    )


def renderizar_score_visual(score: float, classificacao: str) -> None:
    st.markdown("### Score de convicção da tese")

    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        st.metric("Score", f"{score:.0f}/100")

    with col2:
        st.metric("Classificação", classificacao)

    with col3:
        st.progress(score / 100)

    if classificacao == "FORTE":
        st.success(
            "Convicção forte: a tese parece bem sustentada qualitativamente, considerando os critérios preenchidos."
        )
    elif classificacao == "BOA":
        st.success(
            "Convicção boa: há elementos positivos, mas ainda vale revisar riscos e premissas."
        )
    elif classificacao == "MODERADA":
        st.warning(
            "Convicção moderada: a tese exige mais estudo antes de ser tratada como prioridade."
        )
    elif classificacao == "FRACA":
        st.warning(
            "Convicção fraca: há pontos relevantes que reduzem a confiança na análise."
        )
    else:
        st.error(
            "Risco elevado: a tese parece frágil ou dependente demais de premissas incertas."
        )


def renderizar_aba_conviccao(
    empresa: str,
    ticker: str,
    resultado: dict,
    preparar_tabela,
) -> None:
    st.markdown("### Motor de Convicção da Tese")

    st.caption(
        "Esta aba transforma aspectos qualitativos da empresa em uma leitura estruturada. "
        "O objetivo é evitar que o investidor olhe apenas para o preço-teto e ignore a qualidade da tese."
    )

    st.warning(
        "Uso educacional. Este score não é recomendação de compra, venda ou manutenção. "
        "Ele serve para organizar pensamento crítico sobre a empresa."
    )

    status_valuation = resultado.get("status", "N/D")

    st.divider()

    st.markdown(f"#### Empresa analisada: {empresa} ({ticker.upper()})")

    col_status_1, col_status_2, col_status_3 = st.columns(3)

    with col_status_1:
        st.metric("Status do valuation", status_valuation)

    with col_status_2:
        st.metric(
            "Preço-teto",
            f"{resultado.get('preco_teto', 0):.2f}",
        )

    with col_status_3:
        st.metric(
            "Preço justo combinado",
            f"{resultado.get('preco_justo_combinado', 0):.2f}",
        )

    st.divider()

    st.markdown("### Matriz qualitativa")

    st.caption(
        "Dê notas de 0 a 10 para cada dimensão. Quanto maior a nota, maior a qualidade percebida naquele critério."
    )

    col1, col2 = st.columns(2)

    with col1:
        previsibilidade = st.slider(
            "Previsibilidade dos resultados",
            min_value=0,
            max_value=10,
            value=7,
            help="Empresas previsíveis costumam permitir valuation mais confiável.",
            key=f"conviccao_previsibilidade_{ticker}",
        )

        qualidade_caixa = st.slider(
            "Qualidade da geração de caixa",
            min_value=0,
            max_value=10,
            value=7,
            help="Avalia se a empresa converte lucro em fluxo de caixa livre de forma consistente.",
            key=f"conviccao_caixa_{ticker}",
        )

        endividamento = st.slider(
            "Saúde financeira / endividamento",
            min_value=0,
            max_value=10,
            value=7,
            help="Nota maior significa menor risco financeiro percebido.",
            key=f"conviccao_endividamento_{ticker}",
        )

        vantagem_competitiva = st.slider(
            "Vantagem competitiva",
            min_value=0,
            max_value=10,
            value=7,
            help="Marcas fortes, escala, rede, switching cost e poder de preço aumentam a nota.",
            key=f"conviccao_vantagem_{ticker}",
        )

    with col2:
        crescimento = st.slider(
            "Crescimento sustentável",
            min_value=0,
            max_value=10,
            value=6,
            help="Avalia se o crescimento parece sustentável sem depender de premissas agressivas.",
            key=f"conviccao_crescimento_{ticker}",
        )

        qualidade_gestao = st.slider(
            "Qualidade da gestão e alocação de capital",
            min_value=0,
            max_value=10,
            value=6,
            help="Avalia disciplina, recompra de ações, aquisições, retorno sobre capital e comunicação com acionistas.",
            key=f"conviccao_gestao_{ticker}",
        )

        risco_negocio = st.slider(
            "Controle dos riscos do negócio",
            min_value=0,
            max_value=10,
            value=6,
            help="Nota maior significa que os riscos parecem mais controlados.",
            key=f"conviccao_risco_{ticker}",
        )

        dependencia_premissas = st.slider(
            "Baixa dependência de premissas otimistas",
            min_value=0,
            max_value=10,
            value=6,
            help="Nota maior significa que a tese não depende tanto de cenário perfeito.",
            key=f"conviccao_premissas_{ticker}",
        )

    qualidade_dados = st.slider(
        "Qualidade e confiabilidade dos dados usados",
        min_value=0,
        max_value=10,
        value=7,
        help="Dados atualizados, normalizados e bem conferidos aumentam a confiabilidade da análise.",
        key=f"conviccao_dados_{ticker}",
    )

    st.divider()

    score = (
        previsibilidade * 0.14
        + qualidade_caixa * 0.16
        + endividamento * 0.10
        + vantagem_competitiva * 0.16
        + crescimento * 0.10
        + qualidade_gestao * 0.10
        + risco_negocio * 0.10
        + dependencia_premissas * 0.08
        + qualidade_dados * 0.06
    ) * 10

    score = max(0, min(100, score))

    classificacao = classificar_conviccao(score)

    alertas = gerar_alertas_conviccao(
        previsibilidade=previsibilidade,
        qualidade_caixa=qualidade_caixa,
        endividamento=endividamento,
        vantagem_competitiva=vantagem_competitiva,
        risco_negocio=risco_negocio,
        dependencia_premissas=dependencia_premissas,
        qualidade_dados=qualidade_dados,
    )

    leitura_executiva = gerar_leitura_executiva(
        score=score,
        classificacao=classificacao,
        status_valuation=status_valuation,
        alertas=alertas,
    )

    resultado_conviccao = {
        "empresa": empresa,
        "ticker": ticker.upper(),
        "score_conviccao": round(score, 0),
        "classificacao_tese": classificacao,
        "status_valuation": status_valuation,
        "alertas": alertas,
        "leitura_executiva": leitura_executiva,
        "matriz_qualitativa": {
            "previsibilidade": previsibilidade,
            "qualidade_caixa": qualidade_caixa,
            "endividamento": endividamento,
            "vantagem_competitiva": vantagem_competitiva,
            "crescimento": crescimento,
            "qualidade_gestao": qualidade_gestao,
            "risco_negocio": risco_negocio,
            "dependencia_premissas": dependencia_premissas,
            "qualidade_dados": qualidade_dados,
        },
    }

    st.session_state["resultado_conviccao_tese"] = resultado_conviccao
    st.session_state["score_conviccao"] = round(score, 0)
    st.session_state["classificacao_tese"] = classificacao
    st.session_state["alertas_conviccao"] = alertas

    renderizar_score_visual(score, classificacao)

    st.divider()

    st.markdown("### Leitura executiva da tese")

    st.info(leitura_executiva)

    st.markdown("### Alertas qualitativos")

    if len(alertas) == 0:
        st.success(
            "Nenhum alerta crítico foi identificado com as notas atuais. Ainda assim, revise as premissas antes de usar a análise."
        )
    else:
        for alerta in alertas:
            st.warning(alerta)

    st.divider()

    st.markdown("### Matriz da tese")

    tabela_matriz = [
        {
            "Critério": "Previsibilidade dos resultados",
            "Nota": previsibilidade,
            "Leitura": "Quanto mais previsível, mais confiável tende a ser o valuation.",
        },
        {
            "Critério": "Qualidade da geração de caixa",
            "Nota": qualidade_caixa,
            "Leitura": "Lucro sem caixa pode distorcer o preço justo.",
        },
        {
            "Critério": "Saúde financeira / endividamento",
            "Nota": endividamento,
            "Leitura": "Endividamento elevado reduz margem de erro.",
        },
        {
            "Critério": "Vantagem competitiva",
            "Nota": vantagem_competitiva,
            "Leitura": "Empresas com fosso competitivo tendem a sustentar retornos superiores.",
        },
        {
            "Critério": "Crescimento sustentável",
            "Nota": crescimento,
            "Leitura": "Crescimento bom é aquele que não exige premissas irreais.",
        },
        {
            "Critério": "Gestão e alocação de capital",
            "Nota": qualidade_gestao,
            "Leitura": "Boa gestão protege o capital do acionista no longo prazo.",
        },
        {
            "Critério": "Controle dos riscos",
            "Nota": risco_negocio,
            "Leitura": "Riscos altos exigem margem de segurança maior.",
        },
        {
            "Critério": "Baixa dependência de otimismo",
            "Nota": dependencia_premissas,
            "Leitura": "A melhor tese não precisa de cenário perfeito para fazer sentido.",
        },
        {
            "Critério": "Qualidade dos dados",
            "Nota": qualidade_dados,
            "Leitura": "Dados ruins geram conclusões ruins.",
        },
    ]

    st.table(preparar_tabela(tabela_matriz))

    st.divider()

    st.markdown("### Como usar essa leitura")

    st.markdown(
        """
        Use o score de convicção como um filtro de qualidade da tese.

        - Se o valuation parece barato, mas a convicção é fraca, o risco pode estar escondido.
        - Se a empresa é excelente, mas o valuation manda aguardar, talvez o problema seja preço.
        - Se a tese depende demais de premissas otimistas, revise o modelo.
        - Se os dados são ruins, o resultado final perde confiabilidade.
        """
    )