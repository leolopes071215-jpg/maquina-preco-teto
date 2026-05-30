from valuation import EntradasValuation, calcular_valuation


def criar_entradas_empresa(dados_empresa: dict) -> EntradasValuation:
    return EntradasValuation(
        empresa=dados_empresa["empresa"],
        ticker=dados_empresa["ticker"],
        lucro_liquido_sustentavel=float(dados_empresa["lucro_liquido_sustentavel"]),
        fluxo_caixa_livre=float(dados_empresa["fluxo_caixa_livre"]),
        quantidade_acoes=float(dados_empresa["quantidade_acoes"]),
        multiplo_justo_eps=float(dados_empresa["multiplo_justo_eps"]),
        multiplo_justo_fcf=float(dados_empresa["multiplo_justo_fcf"]),
        peso_eps=float(dados_empresa["peso_eps"]),
        peso_fcf=float(dados_empresa["peso_fcf"]),
        margem_seguranca=float(dados_empresa["margem_seguranca"]),
        preco_atual=float(dados_empresa["preco_atual"]),
    )


def gerar_comparativo(empresas: dict, formatar_moeda, formatar_percentual) -> list[dict]:
    comparativo = []

    for nome_modelo, dados_empresa in empresas.items():
        simbolo = dados_empresa.get("simbolo_moeda", "R$")

        entradas_empresa = criar_entradas_empresa(dados_empresa)
        resultado_empresa = calcular_valuation(entradas_empresa)

        comparativo.append(
            {
                "Empresa": dados_empresa["empresa"],
                "Ticker": dados_empresa["ticker"],
                "Preço atual": formatar_moeda(dados_empresa["preco_atual"], simbolo),
                "Preço justo": formatar_moeda(resultado_empresa["preco_justo_combinado"], simbolo),
                "Preço-teto": formatar_moeda(resultado_empresa["preco_teto"], simbolo),
                "Margem até preço-teto": formatar_percentual(resultado_empresa["margem_ate_preco_teto"]),
                "Potencial até preço justo": formatar_percentual(resultado_empresa["potencial_ate_preco_justo"]),
                "Status": resultado_empresa["status"],
            }
        )

    return comparativo


def encontrar_empresa_mais_atrativa(empresas: dict, formatar_moeda, formatar_percentual) -> dict:
    melhor_empresa = None
    melhor_resultado = None
    melhor_dados = None

    for nome_modelo, dados_empresa in empresas.items():
        entradas_empresa = criar_entradas_empresa(dados_empresa)
        resultado_empresa = calcular_valuation(entradas_empresa)

        if melhor_resultado is None:
            melhor_empresa = nome_modelo
            melhor_resultado = resultado_empresa
            melhor_dados = dados_empresa
            continue

        if resultado_empresa["margem_ate_preco_teto"] > melhor_resultado["margem_ate_preco_teto"]:
            melhor_empresa = nome_modelo
            melhor_resultado = resultado_empresa
            melhor_dados = dados_empresa

    simbolo = melhor_dados.get("simbolo_moeda", "R$")

    return {
        "modelo": melhor_empresa,
        "empresa": melhor_dados["empresa"],
        "ticker": melhor_dados["ticker"],
        "preco_atual": formatar_moeda(melhor_dados["preco_atual"], simbolo),
        "preco_teto": formatar_moeda(melhor_resultado["preco_teto"], simbolo),
        "preco_justo": formatar_moeda(melhor_resultado["preco_justo_combinado"], simbolo),
        "margem_ate_preco_teto": formatar_percentual(melhor_resultado["margem_ate_preco_teto"]),
        "potencial_ate_preco_justo": formatar_percentual(melhor_resultado["potencial_ate_preco_justo"]),
        "status": melhor_resultado["status"],
    }