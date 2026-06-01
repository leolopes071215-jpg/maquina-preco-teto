# checklist.py

import streamlit as st
from typing import Any, Dict, List, Optional


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v1.14 — Checklist de Erros Multiativos
# ------------------------------------------------------------
# Este módulo audita o raciocínio do usuário.
# Ele não recomenda compra/venda.
# Ele ajuda a identificar fragilidades, vieses e premissas perigosas.
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


def _extrair_resultado_valuation(resultado_valuation: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    data = {}

    if isinstance(st.session_state.get("resultado_valuation"), dict):
        data.update(st.session_state.get("resultado_valuation"))

    if isinstance(resultado_valuation, dict):
        data.update(resultado_valuation)

    return {
        "empresa": data.get("empresa", "Empresa analisada"),
        "ticker": data.get("ticker", "N/D"),
        "status": _normalizar_status(data.get("status_valuation", data.get("status", "N/D"))),
        "preco_atual": data.get("preco_atual"),
        "preco_teto": data.get("preco_teto"),
        "preco_justo": data.get("preco_justo", data.get("preco_justo_combinado")),
        "margem_ate_preco_teto": data.get("margem_ate_preco_teto"),
        "potencial_ate_preco_justo": data.get("potencial_ate_preco_justo"),
    }


def _classificar_risco(score_risco: int) -> str:
    if score_risco <= 25:
        return "Análise sólida"
    if score_risco <= 50:
        return "Revisar com atenção"
    if score_risco <= 75:
        return "Risco elevado de premissas frágeis"
    return "Risco crítico de erro"


def _acao_educacional(classificacao: str, classe_ativo: str) -> str:
    if classificacao == "Análise sólida":
        return (
            f"A análise de {classe_ativo} parece bem estruturada. "
            "Mesmo assim, revise os dados, compare cenários e mantenha disciplina antes de qualquer decisão real."
        )

    if classificacao == "Revisar com atenção":
        return (
            f"A análise de {classe_ativo} tem pontos bons, mas existem fragilidades relevantes. "
            "Revise as premissas marcadas, confira os dados e aumente a margem de segurança."
        )

    if classificacao == "Risco elevado de premissas frágeis":
        return (
            f"A análise de {classe_ativo} pode estar vulnerável a erros importantes. "
            "Antes de avançar, revise dados, riscos, preço, liquidez, premissas e qualidade do ativo."
        )

    return (
        f"A análise de {classe_ativo} apresenta risco crítico de erro. "
        "A ação educacional mais prudente é parar, revisar a tese desde o início e buscar dados mais confiáveis."
    )


def _perguntas_acoes() -> List[Dict[str, Any]]:
    return [
        {
            "texto": "O lucro usado pode estar inflado por evento não recorrente?",
            "peso": 12,
            "explicacao": "Lucro extraordinário pode fazer a ação parecer barata quando não está.",
        },
        {
            "texto": "O fluxo de caixa livre não confirma a qualidade do lucro?",
            "peso": 14,
            "explicacao": "Lucro sem caixa reduz a confiabilidade do valuation.",
        },
        {
            "texto": "O múltiplo justo usado parece otimista demais?",
            "peso": 13,
            "explicacao": "Múltiplos altos exigem empresas excelentes, previsíveis e com vantagem competitiva.",
        },
        {
            "texto": "A margem de segurança está baixa para o risco da empresa?",
            "peso": 12,
            "explicacao": "Quanto maior a incerteza, maior deveria ser a margem de segurança.",
        },
        {
            "texto": "A tese depende demais de crescimento futuro agressivo?",
            "peso": 12,
            "explicacao": "Crescimento projetado demais pode transformar valuation em torcida.",
        },
        {
            "texto": "O endividamento ou risco financeiro foi pouco considerado?",
            "peso": 10,
            "explicacao": "Dívida elevada reduz margem de erro e pode destruir valor.",
        },
        {
            "texto": "A empresa é cíclica, mas foi analisada como se fosse previsível?",
            "peso": 10,
            "explicacao": "Empresas cíclicas exigem lucro normalizado e múltiplos mais prudentes.",
        },
        {
            "texto": "A ação parece boa apenas porque a narrativa da empresa é bonita?",
            "peso": 9,
            "explicacao": "Boa história sem bons números pode gerar uma análise ilusória.",
        },
        {
            "texto": "O preço atual está muito distante do preço-teto?",
            "peso": 8,
            "explicacao": "Empresa excelente pode continuar sendo um investimento ruim se o preço for exagerado.",
        },
    ]


def _perguntas_fiis() -> List[Dict[str, Any]]:
    return [
        {
            "texto": "O dividend yield atual pode estar inflado por rendimento não recorrente?",
            "peso": 14,
            "explicacao": "Rendimento extraordinário pode criar falsa sensação de renda sustentável.",
        },
        {
            "texto": "A vacância, inadimplência ou risco dos inquilinos foi pouco analisado?",
            "peso": 13,
            "explicacao": "FIIs dependem da qualidade dos imóveis, contratos e pagadores.",
        },
        {
            "texto": "O fundo tem concentração excessiva em poucos imóveis ou inquilinos?",
            "peso": 12,
            "explicacao": "Concentração aumenta o impacto de qualquer problema operacional.",
        },
        {
            "texto": "O preço foi analisado só pelo P/VP, sem olhar qualidade dos ativos?",
            "peso": 11,
            "explicacao": "P/VP baixo não significa necessariamente oportunidade.",
        },
        {
            "texto": "A gestão do fundo não foi avaliada com profundidade?",
            "peso": 10,
            "explicacao": "Gestão ruim pode destruir valor mesmo em bons imóveis.",
        },
        {
            "texto": "O risco de alavancagem ou obrigações futuras foi ignorado?",
            "peso": 11,
            "explicacao": "Dívida, obras, emissões e obrigações podem afetar dividendos futuros.",
        },
        {
            "texto": "O setor do FII está passando por pressão estrutural?",
            "peso": 10,
            "explicacao": "Lajes, shoppings, logística, recebíveis e híbridos têm riscos diferentes.",
        },
        {
            "texto": "A liquidez do fundo é baixa para o tamanho da posição desejada?",
            "peso": 9,
            "explicacao": "Baixa liquidez pode dificultar entrada e saída sem distorcer preço.",
        },
        {
            "texto": "A análise ignora inflação, juros e ciclo imobiliário?",
            "peso": 10,
            "explicacao": "FIIs são muito sensíveis a juros, inflação, crédito e ciclo econômico.",
        },
    ]


def _perguntas_renda_fixa() -> List[Dict[str, Any]]:
    return [
        {
            "texto": "O risco de crédito do emissor foi pouco analisado?",
            "peso": 15,
            "explicacao": "Rentabilidade maior pode esconder risco maior de calote ou estresse financeiro.",
        },
        {
            "texto": "A aplicação foi escolhida apenas pela taxa, sem olhar segurança?",
            "peso": 13,
            "explicacao": "Taxa alta sem análise de risco pode ser armadilha.",
        },
        {
            "texto": "O prazo do título não combina com o objetivo do dinheiro?",
            "peso": 12,
            "explicacao": "Prazo errado pode gerar necessidade de resgate em momento ruim.",
        },
        {
            "texto": "A liquidez é baixa ou inexistente antes do vencimento?",
            "peso": 12,
            "explicacao": "Liquidez importa muito para reserva, objetivos curtos e imprevistos.",
        },
        {
            "texto": "O risco de marcação a mercado foi ignorado?",
            "peso": 11,
            "explicacao": "Títulos prefixados e IPCA+ podem oscilar bastante antes do vencimento.",
        },
        {
            "texto": "A análise não considera imposto de renda, IOF ou custos?",
            "peso": 9,
            "explicacao": "Rentabilidade bruta não é rentabilidade líquida.",
        },
        {
            "texto": "O produto não tem proteção do FGC e isso foi ignorado?",
            "peso": 11,
            "explicacao": "Debêntures, CRIs e CRAs exigem análise de crédito mais rigorosa.",
        },
        {
            "texto": "A taxa não foi comparada com CDI, Tesouro Direto ou alternativas similares?",
            "peso": 9,
            "explicacao": "Sem comparação, é difícil saber se o prêmio de risco compensa.",
        },
        {
            "texto": "A alocação está concentrada demais em um emissor ou indexador?",
            "peso": 8,
            "explicacao": "Concentração reduz segurança e aumenta risco específico.",
        },
    ]


def _perguntas_por_classe(classe_ativo: str) -> List[Dict[str, Any]]:
    if classe_ativo == "Fundos Imobiliários":
        return _perguntas_fiis()

    if classe_ativo == "Renda Fixa":
        return _perguntas_renda_fixa()

    return _perguntas_acoes()


def _gerar_perguntas_criticas(classe_ativo: str) -> List[str]:
    if classe_ativo in ["Ações EUA", "Ações Brasil"]:
        return [
            "O lucro utilizado representa um ano normal da empresa?",
            "O FCF confirma a qualidade do lucro?",
            "A empresa merece o múltiplo justo escolhido?",
            "O preço atual oferece margem de segurança real?",
            "A tese continua fazendo sentido em um cenário conservador?",
        ]

    if classe_ativo == "Fundos Imobiliários":
        return [
            "O rendimento distribuído é recorrente ou extraordinário?",
            "A vacância e os contratos foram analisados?",
            "O FII depende demais de poucos imóveis ou inquilinos?",
            "A gestão tem histórico de boa alocação de capital?",
            "O preço compensa o risco do setor e dos ativos?",
        ]

    return [
        "O emissor é seguro o suficiente para o prêmio oferecido?",
        "A liquidez combina com o objetivo do dinheiro?",
        "O prazo é adequado?",
        "A rentabilidade líquida foi comparada com alternativas?",
        "O risco de marcação a mercado foi entendido?",
    ]


def renderizar_checklist_erros(
    resultado_valuation: Optional[Dict[str, Any]] = None,
) -> None:
    st.markdown("### Checklist de Erros Multiativos")

    st.caption(
        "Esta aba audita o raciocínio da análise. O objetivo é encontrar fragilidades antes que elas virem decisões ruins."
    )

    st.warning(
        "Uso educacional. Este checklist não recomenda compra, venda ou manutenção. "
        "Ele serve para reduzir erros, vieses e excesso de confiança."
    )

    resultado = _extrair_resultado_valuation(resultado_valuation)

    st.divider()

    col_topo_1, col_topo_2, col_topo_3 = st.columns(3)

    with col_topo_1:
        st.metric("Ativo analisado", f"{resultado['empresa']}")

    with col_topo_2:
        st.metric("Ticker", resultado["ticker"])

    with col_topo_3:
        st.metric("Status valuation", resultado["status"])

    st.divider()

    classe_ativo = st.selectbox(
        "Classe da análise",
        [
            "Ações EUA",
            "Ações Brasil",
            "Fundos Imobiliários",
            "Renda Fixa",
        ],
        help="Escolha a classe de ativo para o checklist usar a lógica correta.",
    )

    if classe_ativo in ["Fundos Imobiliários", "Renda Fixa"]:
        st.info(
            f"Você selecionou **{classe_ativo}**. Nesta fase, o app ainda não calcula valuation completo para essa classe, "
            "mas já audita os principais erros de raciocínio. Nas próximas versões, criaremos motores específicos."
        )

    perguntas = _perguntas_por_classe(classe_ativo)

    st.markdown("### Marque os riscos que aparecem na sua análise")

    st.caption(
        "Quanto mais itens marcados, maior o risco de a análise estar apoiada em premissas frágeis."
    )

    score_risco = 0
    erros_marcados = []

    for indice, pergunta in enumerate(perguntas, start=1):
        marcado = st.checkbox(
            pergunta["texto"],
            value=False,
            key=f"checklist_{classe_ativo}_{indice}",
            help=pergunta["explicacao"],
        )

        if marcado:
            score_risco += pergunta["peso"]
            erros_marcados.append(pergunta)

    score_risco = min(score_risco, 100)
    classificacao = _classificar_risco(score_risco)
    acao = _acao_educacional(classificacao, classe_ativo)

    st.divider()

    st.markdown("### Resultado do auditor")

    col_res_1, col_res_2, col_res_3 = st.columns(3)

    with col_res_1:
        st.metric("Score de risco", f"{score_risco}/100")

    with col_res_2:
        st.metric("Classificação", classificacao)

    with col_res_3:
        st.metric("Erros marcados", len(erros_marcados))

    st.progress(score_risco / 100)

    if classificacao == "Análise sólida":
        st.success("A análise parece bem estruturada. Ainda assim, mantenha revisão crítica.")
    elif classificacao == "Revisar com atenção":
        st.warning("A análise tem pontos de atenção. Revise antes de avançar.")
    elif classificacao == "Risco elevado de premissas frágeis":
        st.error("Há risco elevado de erro. A análise precisa de revisão profunda.")
    else:
        st.error("Risco crítico. A análise pode estar sustentada por premissas perigosas.")

    st.markdown("### Ação educacional sugerida")
    st.info(acao)

    st.markdown("### Erros identificados")

    if len(erros_marcados) == 0:
        st.success(
            "Nenhum erro foi marcado. Isso não garante que a análise está correta, mas indica que os principais riscos do checklist não foram identificados."
        )
    else:
        for erro in erros_marcados:
            with st.container(border=True):
                st.markdown(f"**Erro potencial:** {erro['texto']}")
                st.caption(erro["explicacao"])

    st.divider()

    st.markdown("### Perguntas críticas antes de concluir")

    perguntas_criticas = _gerar_perguntas_criticas(classe_ativo)

    for pergunta in perguntas_criticas:
        st.markdown(f"- {pergunta}")

    resultado_checklist = {
        "classe_ativo": classe_ativo,
        "score_risco": score_risco,
        "classificacao_risco": classificacao,
        "erros_marcados": [erro["texto"] for erro in erros_marcados],
        "perguntas_criticas": perguntas_criticas,
        "acao_educacional": acao,
    }

    st.session_state["resultado_checklist_erros"] = resultado_checklist

    st.divider()

    st.markdown("### Leitura estratégica")

    st.markdown(
        """
        O checklist é uma camada de proteção contra excesso de confiança.

        Em ações, ele evita pagar caro por uma tese bonita.  
        Em FIIs, ele evita confundir rendimento alto com qualidade.  
        Em renda fixa, ele evita olhar apenas para taxa e ignorar risco, prazo e liquidez.

        A lógica da plataforma é simples: antes de buscar retorno, reduza erros evitáveis.
        """
    )