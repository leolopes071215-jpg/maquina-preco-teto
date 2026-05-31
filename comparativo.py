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


def empresa_eh_didatica(dados_empresa: dict) -> bool:
    return dados_empresa.get("data_referencia") == "Dados didáticos"


def limitar_numero(valor: float, minimo: float, maximo: float) -> float:
    return max(minimo, min(valor, maximo))


def calcular_score_atratividade(resultado_empresa: dict) -> int:
    margem_ate_preco_teto = float(resultado_empresa["margem_ate_preco_teto"])
    potencial_ate_preco_justo = float(resultado_empresa["potencial_ate_preco_justo"])
    status = resultado_empresa["status"]

    score = 100 + (margem_ate_preco_teto * 2)

    if potencial_ate_preco_justo > 0:
        score += min(potencial_ate_preco_justo * 0.20, 8)

    if status == "COMPRA":
        score += 10
    elif status == "NEUTRO":
        score += 3
    else:
        score -= 5

    score = limitar_numero(score, 0, 100)

    return round(score)


def gerar_leitura_radar(resultado_empresa: dict) -> str:
    status = resultado_empresa["status"]
    margem = resultado_empresa["margem_ate_preco_teto"]
    potencial = resultado_empresa["potencial_ate_preco_justo"]

    if status == "COMPRA":
        return (
            "Pelas premissas atuais, esta empresa está dentro da zona conservadora do modelo. "
            "Ainda assim, isso não elimina a necessidade de analisar qualidade, riscos e fontes dos números."
        )

    if status == "NEUTRO":
        return (
            "Esta é a empresa real mais bem posicionada pelo modelo, mas ainda não está abaixo do preço-teto. "
            "Ela está menos distante da zona conservadora, porém exige disciplina na entrada."
        )

    if potencial > 0:
        return (
            "Apesar de ainda estar fora da zona conservadora, a empresa está próxima do preço justo estimado. "
            "O modelo indica paciência e monitoramento."
        )

    return (
        "Mesmo sendo a melhor posicionada entre as empresas reais cadastradas, ainda está distante do preço-teto. "
        "O modelo indica cautela, revisão de premissas ou espera por melhor preço."
    )


def gerar_comparativo(empresas: dict, formatar_moeda, formatar_percentual) -> list[dict]:
    comparativo = []

    for nome_modelo, dados_empresa in empresas.items():
        simbolo = dados_empresa.get("simbolo_moeda", "R$")

        entradas_empresa = criar_entradas_empresa(dados_empresa)
        resultado_empresa = calcular_valuation(entradas_empresa)

        tipo = "Didática" if empresa_eh_didatica(dados_empresa) else "Real"
        score = calcular_score_atratividade(resultado_empresa)

        comparativo.append(
            {
                "Empresa": dados_empresa["empresa"],
                "Ticker": dados_empresa["ticker"],
                "Tipo": tipo,
                "Score": f"{score}/100",
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
    melhor_score = None

    for nome_modelo, dados_empresa in empresas.items():
        if empresa_eh_didatica(dados_empresa):
            continue

        entradas_empresa = criar_entradas_empresa(dados_empresa)
        resultado_empresa = calcular_valuation(entradas_empresa)
        score = calcular_score_atratividade(resultado_empresa)

        if melhor_score is None:
            melhor_empresa = nome_modelo
            melhor_resultado = resultado_empresa
            melhor_dados = dados_empresa
            melhor_score = score
            continue

        if score > melhor_score:
            melhor_empresa = nome_modelo
            melhor_resultado = resultado_empresa
            melhor_dados = dados_empresa
            melhor_score = score

    if melhor_dados is None:
        return {
            "modelo": "Nenhuma empresa real cadastrada",
            "empresa": "Nenhuma empresa real cadastrada",
            "ticker": "-",
            "preco_atual": "-",
            "preco_teto": "-",
            "preco_justo": "-",
            "margem_ate_preco_teto": "-",
            "potencial_ate_preco_justo": "-",
            "status": "-",
            "score": 0,
            "score_formatado": "0/100",
            "leitura": "Nenhuma empresa real foi cadastrada para análise.",
        }

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
        "score": melhor_score,
        "score_formatado": f"{melhor_score}/100",
        "leitura": gerar_leitura_radar(melhor_resultado),
    }


def gerar_ranking_empresas_reais(empresas: dict, formatar_moeda, formatar_percentual) -> list[dict]:
    ranking_bruto = []

    for nome_modelo, dados_empresa in empresas.items():
        if empresa_eh_didatica(dados_empresa):
            continue

        simbolo = dados_empresa.get("simbolo_moeda", "R$")

        entradas_empresa = criar_entradas_empresa(dados_empresa)
        resultado_empresa = calcular_valuation(entradas_empresa)
        score = calcular_score_atratividade(resultado_empresa)

        ranking_bruto.append(
            {
                "empresa": dados_empresa["empresa"],
                "ticker": dados_empresa["ticker"],
                "score": score,
                "preco_atual": formatar_moeda(dados_empresa["preco_atual"], simbolo),
                "preco_teto": formatar_moeda(resultado_empresa["preco_teto"], simbolo),
                "preco_justo": formatar_moeda(resultado_empresa["preco_justo_combinado"], simbolo),
                "margem_ate_preco_teto": formatar_percentual(resultado_empresa["margem_ate_preco_teto"]),
                "potencial_ate_preco_justo": formatar_percentual(resultado_empresa["potencial_ate_preco_justo"]),
                "status": resultado_empresa["status"],
                "_margem_numerica": resultado_empresa["margem_ate_preco_teto"],
            }
        )

    ranking_ordenado = sorted(
        ranking_bruto,
        key=lambda empresa: (empresa["score"], empresa["_margem_numerica"]),
        reverse=True,
    )

    ranking_final = []

    for posicao, empresa in enumerate(ranking_ordenado, start=1):
        ranking_final.append(
            {
                "Ranking": posicao,
                "Empresa": empresa["empresa"],
                "Ticker": empresa["ticker"],
                "Score": f"{empresa['score']}/100",
                "Status": empresa["status"],
                "Margem até preço-teto": empresa["margem_ate_preco_teto"],
                "Potencial até preço justo": empresa["potencial_ate_preco_justo"],
                "Preço atual": empresa["preco_atual"],
                "Preço-teto": empresa["preco_teto"],
                "Preço justo": empresa["preco_justo"],
            }
        )

    return ranking_final