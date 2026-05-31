import streamlit as st

from valuation import EntradasValuation, calcular_valuation


def criar_cenario(
    entradas_base: EntradasValuation,
    nome_cenario: str,
    ajuste_lucro: float,
    ajuste_fcf: float,
    ajuste_multiplos: float,
    ajuste_margem_pontos: float,
) -> dict:
    margem_ajustada = entradas_base.margem_seguranca + ajuste_margem_pontos

    margem_ajustada = max(0, min(margem_ajustada, 90))

    entradas_cenario = EntradasValuation(
        empresa=entradas_base.empresa,
        ticker=entradas_base.ticker,
        lucro_liquido_sustentavel=entradas_base.lucro_liquido_sustentavel * ajuste_lucro,
        fluxo_caixa_livre=entradas_base.fluxo_caixa_livre * ajuste_fcf,
        quantidade_acoes=entradas_base.quantidade_acoes,
        multiplo_justo_eps=entradas_base.multiplo_justo_eps * ajuste_multiplos,
        multiplo_justo_fcf=entradas_base.multiplo_justo_fcf * ajuste_multiplos,
        peso_eps=entradas_base.peso_eps,
        peso_fcf=entradas_base.peso_fcf,
        margem_seguranca=margem_ajustada,
        preco_atual=entradas_base.preco_atual,
    )

    resultado = calcular_valuation(entradas_cenario)

    return {
        "nome": nome_cenario,
        "entradas": entradas_cenario,
        "resultado": resultado,
    }


def gerar_cenarios(
    entradas_base: EntradasValuation,
    ajuste_conservador_lucro: float,
    ajuste_conservador_fcf: float,
    ajuste_conservador_multiplos: float,
    margem_extra_conservadora: float,
    ajuste_otimista_lucro: float,
    ajuste_otimista_fcf: float,
    ajuste_otimista_multiplos: float,
    reducao_margem_otimista: float,
) -> list[dict]:
    cenario_conservador = criar_cenario(
        entradas_base=entradas_base,
        nome_cenario="Conservador",
        ajuste_lucro=ajuste_conservador_lucro,
        ajuste_fcf=ajuste_conservador_fcf,
        ajuste_multiplos=ajuste_conservador_multiplos,
        ajuste_margem_pontos=margem_extra_conservadora,
    )

    cenario_base = criar_cenario(
        entradas_base=entradas_base,
        nome_cenario="Base",
        ajuste_lucro=1.00,
        ajuste_fcf=1.00,
        ajuste_multiplos=1.00,
        ajuste_margem_pontos=0,
    )

    cenario_otimista = criar_cenario(
        entradas_base=entradas_base,
        nome_cenario="Otimista",
        ajuste_lucro=ajuste_otimista_lucro,
        ajuste_fcf=ajuste_otimista_fcf,
        ajuste_multiplos=ajuste_otimista_multiplos,
        ajuste_margem_pontos=-reducao_margem_otimista,
    )

    return [
        cenario_conservador,
        cenario_base,
        cenario_otimista,
    ]


def criar_tabela_cenarios(
    cenarios: list[dict],
    simbolo_moeda: str,
    formatar_moeda,
    formatar_percentual,
) -> list[dict]:
    tabela = []

    for cenario in cenarios:
        entradas = cenario["entradas"]
        resultado = cenario["resultado"]

        tabela.append(
            {
                "Cenário": cenario["nome"],
                "Lucro usado": formatar_moeda(entradas.lucro_liquido_sustentavel, simbolo_moeda),
                "FCF usado": formatar_moeda(entradas.fluxo_caixa_livre, simbolo_moeda),
                "Múltiplo EPS": f"{entradas.multiplo_justo_eps:.1f}",
                "Múltiplo FCF": f"{entradas.multiplo_justo_fcf:.1f}",
                "Margem segurança": f"{entradas.margem_seguranca:.0f}%",
                "Preço justo": formatar_moeda(resultado["preco_justo_combinado"], simbolo_moeda),
                "Preço-teto": formatar_moeda(resultado["preco_teto"], simbolo_moeda),
                "Margem até teto": formatar_percentual(resultado["margem_ate_preco_teto"]),
                "Status": resultado["status"],
            }
        )

    return tabela


def renderizar_card_cenario(
    cenario: dict,
    simbolo_moeda: str,
    formatar_moeda,
    formatar_percentual,
) -> None:
    resultado = cenario["resultado"]

    with st.container(border=True):
        st.markdown(f"### {cenario['nome']}")

        st.metric(
            "Preço-teto",
            formatar_moeda(resultado["preco_teto"], simbolo_moeda),
            formatar_percentual(resultado["margem_ate_preco_teto"]),
        )

        st.metric(
            "Preço justo",
            formatar_moeda(resultado["preco_justo_combinado"], simbolo_moeda),
            formatar_percentual(resultado["potencial_ate_preco_justo"]),
        )

        status = resultado["status"]

        if status == "COMPRA":
            st.success("Status: COMPRA")
        elif status == "NEUTRO":
            st.warning("Status: NEUTRO")
        else:
            st.error("Status: AGUARDE")


def renderizar_leitura_cenarios(cenarios: list[dict]) -> None:
    conservador = cenarios[0]["resultado"]
    base = cenarios[1]["resultado"]
    otimista = cenarios[2]["resultado"]

    st.markdown("### Leitura dos cenários")

    if conservador["status"] == "COMPRA":
        st.success(
            "Mesmo no cenário conservador, o preço atual fica dentro da zona de compra do modelo. "
            "Isso indica uma margem de segurança mais robusta, desde que as premissas sejam realistas."
        )
        return

    if base["status"] == "COMPRA":
        st.info(
            "O cenário base indica compra, mas o cenário conservador não confirma. "
            "Isso sugere que a tese depende de premissas razoavelmente favoráveis."
        )
        return

    if otimista["status"] == "COMPRA":
        st.warning(
            "Apenas o cenário otimista indica compra. "
            "Isso é um alerta: a oportunidade depende de premissas mais agressivas."
        )
        return

    if base["status"] == "NEUTRO":
        st.warning(
            "O cenário base está em zona neutra. A empresa pode ser boa, mas o preço ainda não oferece margem conservadora suficiente."
        )
        return

    st.error(
        "Nenhum cenário indica compra pelas premissas atuais. "
        "O modelo sugere paciência, revisão das premissas ou espera por preço melhor."
    )


def renderizar_simulador_cenarios(
    entradas_base: EntradasValuation,
    simbolo_moeda: str,
    formatar_moeda,
    formatar_percentual,
    preparar_tabela,
) -> None:
    st.markdown("### Simulador de cenários")

    st.caption(
        "Compare como o preço-teto muda quando lucro, fluxo de caixa, múltiplos e margem de segurança são ajustados."
    )

    st.warning(
        "O simulador não prevê o futuro. Ele mostra a sensibilidade do valuation às premissas escolhidas."
    )

    st.divider()

    st.markdown("### Ajustes dos cenários")

    col_conservador, col_otimista = st.columns(2)

    with col_conservador:
        with st.container(border=True):
            st.markdown("#### Cenário conservador")

            ajuste_conservador_lucro = st.slider(
                "Lucro sustentável usado",
                min_value=50,
                max_value=100,
                value=90,
                step=5,
                help="Percentual do lucro base usado no cenário conservador.",
            ) / 100

            ajuste_conservador_fcf = st.slider(
                "FCF usado",
                min_value=50,
                max_value=100,
                value=90,
                step=5,
                help="Percentual do FCF base usado no cenário conservador.",
            ) / 100

            ajuste_conservador_multiplos = st.slider(
                "Múltiplos usados",
                min_value=50,
                max_value=100,
                value=85,
                step=5,
                help="Percentual dos múltiplos base usado no cenário conservador.",
            ) / 100

            margem_extra_conservadora = st.slider(
                "Margem extra de segurança",
                min_value=0,
                max_value=30,
                value=10,
                step=5,
                help="Pontos percentuais adicionados à margem de segurança base.",
            )

    with col_otimista:
        with st.container(border=True):
            st.markdown("#### Cenário otimista")

            ajuste_otimista_lucro = st.slider(
                "Lucro sustentável usado ",
                min_value=100,
                max_value=150,
                value=110,
                step=5,
                help="Percentual do lucro base usado no cenário otimista.",
            ) / 100

            ajuste_otimista_fcf = st.slider(
                "FCF usado ",
                min_value=100,
                max_value=150,
                value=110,
                step=5,
                help="Percentual do FCF base usado no cenário otimista.",
            ) / 100

            ajuste_otimista_multiplos = st.slider(
                "Múltiplos usados ",
                min_value=100,
                max_value=150,
                value=115,
                step=5,
                help="Percentual dos múltiplos base usado no cenário otimista.",
            ) / 100

            reducao_margem_otimista = st.slider(
                "Redução da margem de segurança",
                min_value=0,
                max_value=30,
                value=5,
                step=5,
                help="Pontos percentuais retirados da margem de segurança base.",
            )

    cenarios = gerar_cenarios(
        entradas_base=entradas_base,
        ajuste_conservador_lucro=ajuste_conservador_lucro,
        ajuste_conservador_fcf=ajuste_conservador_fcf,
        ajuste_conservador_multiplos=ajuste_conservador_multiplos,
        margem_extra_conservadora=margem_extra_conservadora,
        ajuste_otimista_lucro=ajuste_otimista_lucro,
        ajuste_otimista_fcf=ajuste_otimista_fcf,
        ajuste_otimista_multiplos=ajuste_otimista_multiplos,
        reducao_margem_otimista=reducao_margem_otimista,
    )

    st.divider()

    st.markdown("### Resultado por cenário")

    col_1, col_2, col_3 = st.columns(3)

    with col_1:
        renderizar_card_cenario(
            cenarios[0],
            simbolo_moeda,
            formatar_moeda,
            formatar_percentual,
        )

    with col_2:
        renderizar_card_cenario(
            cenarios[1],
            simbolo_moeda,
            formatar_moeda,
            formatar_percentual,
        )

    with col_3:
        renderizar_card_cenario(
            cenarios[2],
            simbolo_moeda,
            formatar_moeda,
            formatar_percentual,
        )

    renderizar_leitura_cenarios(cenarios)

    st.divider()

    st.markdown("### Tabela de cenários")

    tabela_cenarios = criar_tabela_cenarios(
        cenarios,
        simbolo_moeda,
        formatar_moeda,
        formatar_percentual,
    )

    st.dataframe(
        preparar_tabela(tabela_cenarios),
        use_container_width=True,
        hide_index=True,
    )