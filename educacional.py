import streamlit as st


def renderizar_card_educacional(
    titulo: str,
    descricao: str,
    formula: str,
    leitura: str,
) -> None:
    with st.container(border=True):
        st.markdown(f"#### {titulo}")
        st.write(descricao)

        st.markdown("**Fórmula base:**")
        st.info(formula)

        st.markdown("**Como interpretar:**")
        st.caption(leitura)


def renderizar_aba_educacional() -> None:
    st.markdown("### Centro educacional de valuation")

    st.caption(
        "Esta área transforma os números do modelo em conhecimento prático. "
        "A ideia é ajudar o usuário a entender o que cada indicador significa antes de interpretar o preço-teto."
    )

    st.warning(
        "Esta ferramenta é educacional. Nenhum indicador isolado deve ser usado como recomendação de compra, venda ou manutenção de investimentos."
    )

    st.divider()

    st.markdown("### 1. Indicadores principais")

    col_1, col_2 = st.columns(2)

    with col_1:
        renderizar_card_educacional(
            titulo="EPS normalizado",
            descricao=(
                "O EPS normalizado mostra quanto lucro sustentável existe para cada ação da empresa. "
                "Ele tenta evitar distorções causadas por anos extraordinários, eventos não recorrentes ou resultados fora da curva."
            ),
            formula="EPS = lucro líquido sustentável ÷ quantidade de ações",
            leitura=(
                "Um EPS maior tende a indicar maior geração de lucro por ação. "
                "Mas isso só tem valor se o lucro for recorrente, de qualidade e sustentável."
            ),
        )

        renderizar_card_educacional(
            titulo="Preço justo por EPS",
            descricao=(
                "É uma estimativa de valor baseada no lucro por ação e em um múltiplo justo definido pelo analista."
            ),
            formula="Preço justo por EPS = EPS normalizado × múltiplo justo de EPS",
            leitura=(
                "Empresas excelentes podem justificar múltiplos maiores, mas pagar múltiplos altos demais reduz a margem de segurança."
            ),
        )

        renderizar_card_educacional(
            titulo="Preço justo combinado",
            descricao=(
                "É a média ponderada entre o preço justo calculado pelo lucro e o preço justo calculado pelo fluxo de caixa livre."
            ),
            formula="Preço justo combinado = preço por EPS ponderado + preço por FCF ponderado",
            leitura=(
                "Essa métrica equilibra duas visões: lucro contábil e geração real de caixa. "
                "Os pesos devem mudar conforme o tipo de empresa."
            ),
        )

    with col_2:
        renderizar_card_educacional(
            titulo="FCF por ação",
            descricao=(
                "O FCF por ação mostra quanto fluxo de caixa livre a empresa gera para cada ação existente."
            ),
            formula="FCF por ação = fluxo de caixa livre ÷ quantidade de ações",
            leitura=(
                "Fluxo de caixa livre é essencial porque mostra a capacidade real da empresa de gerar dinheiro depois dos investimentos necessários."
            ),
        )

        renderizar_card_educacional(
            titulo="Preço justo por FCF",
            descricao=(
                "É uma estimativa de valor baseada no fluxo de caixa livre por ação e em um múltiplo justo de FCF."
            ),
            formula="Preço justo por FCF = FCF por ação × múltiplo justo de FCF",
            leitura=(
                "Funciona melhor para empresas com geração de caixa previsível. "
                "Em empresas cíclicas, o FCF de um único ano pode enganar."
            ),
        )

        renderizar_card_educacional(
            titulo="Preço-teto",
            descricao=(
                "É o preço máximo que o modelo considera aceitável depois de aplicar uma margem de segurança sobre o preço justo."
            ),
            formula="Preço-teto = preço justo combinado × (1 - margem de segurança)",
            leitura=(
                "Quanto maior a incerteza sobre a empresa, maior deve ser a margem de segurança. "
                "O preço-teto protege contra erro de premissa."
            ),
        )

    st.divider()

    st.markdown("### 2. Como interpretar o status")

    col_status_1, col_status_2, col_status_3 = st.columns(3)

    with col_status_1:
        st.success(
            """
            **COMPRA**

            O preço atual está abaixo ou igual ao preço-teto.

            Pelas premissas inseridas, a ação está dentro da zona conservadora de entrada.
            """
        )

    with col_status_2:
        st.warning(
            """
            **NEUTRO**

            O preço atual está acima do preço-teto, mas ainda abaixo ou próximo do preço justo.

            A empresa pode ser boa, mas não está barata o suficiente para uma entrada conservadora.
            """
        )

    with col_status_3:
        st.error(
            """
            **AGUARDE**

            O preço atual está acima do preço justo estimado.

            Pelas premissas atuais, o modelo indica paciência, revisão das premissas ou queda de preço.
            """
        )

    st.divider()

    st.markdown("### 3. Como usar a ferramenta com maturidade")

    col_maturidade_1, col_maturidade_2 = st.columns(2)

    with col_maturidade_1:
        st.markdown(
            """
            Use a Máquina de Preço-Teto como um **organizador de raciocínio**, não como uma máquina de prever o futuro.

            Uma análise profissional deve considerar:

            - qualidade da empresa;
            - previsibilidade do lucro;
            - recorrência do fluxo de caixa;
            - endividamento;
            - vantagem competitiva;
            - setor;
            - gestão;
            - riscos regulatórios;
            - valuation relativo;
            - margem de segurança.
            """
        )

    with col_maturidade_2:
        st.info(
            """
            A pergunta central do modelo é:

            **“Pelas minhas premissas atuais, este preço oferece uma relação risco-retorno minimamente racional?”**

            A melhor análise não é a mais otimista.  
            É a que continua fazendo sentido mesmo quando algumas premissas estão erradas.
            """
        )

    st.divider()

    st.markdown("### 4. Erros comuns ao usar valuation")

    erro_1, erro_2, erro_3 = st.columns(3)

    with erro_1:
        st.warning(
            """
            **Erro 1: usar lucro de pico**

            Em empresas cíclicas, um ano excelente pode inflar o lucro e gerar um preço-teto falso.
            """
        )

    with erro_2:
        st.warning(
            """
            **Erro 2: múltiplo otimista demais**

            Um múltiplo alto demais transforma qualquer empresa em oportunidade no papel.
            """
        )

    with erro_3:
        st.warning(
            """
            **Erro 3: ignorar qualidade**

            Uma ação barata pode continuar barata por muitos anos se a empresa for ruim.
            """
        )