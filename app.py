import csv
from io import StringIO

import streamlit as st

from valuation import EntradasValuation, calcular_valuation
from empresas import EMPRESAS
from historico import salvar_analise, carregar_historico, CAMINHO_HISTORICO
from style import aplicar_estilo
from educacional import renderizar_aba_educacional
from simulador import renderizar_simulador_cenarios
from comparativo import (
    gerar_comparativo,
    encontrar_empresa_mais_atrativa,
    gerar_ranking_empresas_reais,
)


OPCAO_ANALISE_MANUAL = "Análise Manual"


DADOS_ANALISE_MANUAL = {
    "empresa": "Empresa Manual",
    "ticker": "MANUAL",
    "perfil_empresa": "Empresa inserida manualmente pelo usuário.",
    "moeda": "Valores inseridos manualmente. Use sempre a mesma unidade para lucro, FCF e quantidade de ações.",
    "simbolo_moeda": "R$",
    "data_referencia": "Dados inseridos manualmente pelo usuário",
    "fonte_premissas": (
        "Análise manual. Os dados não foram puxados automaticamente. "
        "O usuário deve conferir lucro líquido sustentável, FCF, quantidade de ações, preço atual e múltiplos usados."
    ),

    "lucro_liquido_sustentavel": 1_000.0,
    "fluxo_caixa_livre": 800.0,
    "quantidade_acoes": 100.0,
    "preco_atual": 10.0,

    "multiplo_justo_eps": 15.0,
    "multiplo_justo_fcf": 14.0,
    "peso_eps": 50,
    "peso_fcf": 50,
    "margem_seguranca": 25,

    "tese": (
        "Descreva aqui a tese da empresa: o que ela faz, como ganha dinheiro, "
        "quais são suas vantagens competitivas e por que ela poderia gerar valor no longo prazo."
    ),

    "riscos": (
        "Descreva aqui os principais riscos: concorrência, endividamento, queda de margens, "
        "regulação, ciclicidade, dependência de poucos clientes ou risco de pagar caro demais."
    ),

    "fundamentos": (
        "Descreva aqui os fundamentos observados: crescimento de receita, margens, lucro, "
        "geração de caixa, retorno sobre capital, endividamento e qualidade da gestão."
    ),
}


st.set_page_config(
    page_title="Máquina de Preço-Teto",
    page_icon="📊",
    layout="wide",
)

aplicar_estilo()


def formatar_moeda(valor: float, simbolo: str = "R$") -> str:
    return f"{simbolo} {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def formatar_numero(valor: float) -> str:
    return f"{valor:,.0f}".replace(",", ".")


def formatar_percentual(valor: float) -> str:
    return f"{valor:.2f}%"


def preparar_tabela(tabela: list[dict]) -> list[dict]:
    return [
        {chave: str(valor) for chave, valor in linha.items()}
        for linha in tabela
    ]


def converter_tabela_para_csv(tabela: list[dict]) -> str:
    if len(tabela) == 0:
        return ""

    saida = StringIO()
    campos = tabela[0].keys()

    escritor = csv.DictWriter(saida, fieldnames=campos)
    escritor.writeheader()
    escritor.writerows(tabela)

    return saida.getvalue()


def renderizar_hero() -> None:
    st.markdown("# 📊 Máquina de Preço-Teto")

    st.markdown(
        """
        ### Valuation disciplinado com lucro, fluxo de caixa livre e margem de segurança.

        Plataforma educacional para organizar premissas, comparar empresas e estimar uma zona racional de preço.
        """
    )

    st.caption(
        "Modelo EPS + FCF • Radar de oportunidade • Simulador de cenários • Análise manual • Ranking de empresas reais"
    )

    col_home_1, col_home_2, col_home_3, col_home_4 = st.columns(4)

    with col_home_1:
        st.metric("Empresas", len(EMPRESAS))

    with col_home_2:
        st.metric("Motor", "EPS + FCF")

    with col_home_3:
        st.metric("Leitura", "3 status")

    with col_home_4:
        st.metric("Modo", "Manual + Base")

    st.warning(
        "Uso educacional. Não representa recomendação de compra, venda ou manutenção de investimentos. "
        "Os resultados dependem diretamente das premissas inseridas."
    )

    st.divider()


def renderizar_barra_valuation(
    rotulo: str,
    valor: float,
    valor_maximo: float,
    simbolo: str,
) -> None:
    if valor_maximo <= 0:
        proporcao = 0.0
    else:
        proporcao = min(max(valor / valor_maximo, 0), 1)

    col_label, col_valor = st.columns([3, 1])

    with col_label:
        st.caption(rotulo)

    with col_valor:
        st.markdown(f"**{formatar_moeda(valor, simbolo)}**")

    st.progress(proporcao)


def renderizar_mapa_valuation(
    preco_atual: float,
    preco_teto: float,
    preco_justo: float,
    simbolo: str,
) -> None:
    valor_maximo = max(preco_atual, preco_teto, preco_justo, 1)

    with st.container(border=True):
        st.markdown("### Mapa visual do valuation")

        st.caption(
            "Leitura visual entre preço atual, preço-teto conservador e preço justo estimado."
        )

        renderizar_barra_valuation(
            "Preço atual",
            preco_atual,
            valor_maximo,
            simbolo,
        )

        renderizar_barra_valuation(
            "Preço-teto com margem de segurança",
            preco_teto,
            valor_maximo,
            simbolo,
        )

        renderizar_barra_valuation(
            "Preço justo estimado",
            preco_justo,
            valor_maximo,
            simbolo,
        )

        if preco_atual <= preco_teto:
            st.success(
                "Leitura: o preço atual está abaixo ou igual ao preço-teto. "
                "Pelas premissas atuais, está dentro da zona conservadora do modelo."
            )
        elif preco_atual <= preco_justo:
            st.warning(
                "Leitura: o preço atual está acima do preço-teto, mas ainda abaixo ou próximo do preço justo. "
                "Não está barato o suficiente para uma entrada conservadora."
            )
        else:
            st.error(
                "Leitura: o preço atual está acima do preço justo estimado. "
                "Pelas premissas atuais, o modelo indica paciência."
            )


def renderizar_painel_decisao(
    preco_atual: float,
    resultado: dict,
    simbolo_moeda: str,
) -> None:
    with st.container(border=True):
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            st.metric(
                label="Preço atual",
                value=formatar_moeda(preco_atual, simbolo_moeda),
            )

        with col2:
            st.metric(
                label="Preço-teto",
                value=formatar_moeda(resultado["preco_teto"], simbolo_moeda),
                delta=formatar_percentual(resultado["margem_ate_preco_teto"]),
            )

        with col3:
            status = resultado["status"]

            if status == "COMPRA":
                st.success("Status educacional: COMPRA")
            elif status == "NEUTRO":
                st.warning("Status educacional: NEUTRO")
            else:
                st.error("Status educacional: AGUARDE")

        st.markdown("#### Leitura automática")
        st.info(resultado["explicacao_status"])


def renderizar_radar_oportunidade(melhor_empresa: dict) -> None:
    with st.container(border=True):
        st.markdown("#### Radar de oportunidade pelo modelo")

        st.caption(
            "Identifica a empresa real mais bem posicionada pelo score de proximidade ao preço-teto. "
            "Não representa recomendação de compra."
        )

        col_1, col_2, col_3, col_4 = st.columns(4)

        with col_1:
            st.metric("Empresa", melhor_empresa["ticker"])

        with col_2:
            st.metric("Score", melhor_empresa["score_formatado"])

        with col_3:
            st.metric("Status", melhor_empresa["status"])

        with col_4:
            st.metric("Margem até teto", melhor_empresa["margem_ate_preco_teto"])

        st.info(
            f"""
            **{melhor_empresa["empresa"]}** é a empresa real melhor posicionada pelo modelo neste momento.  
            Preço atual: **{melhor_empresa["preco_atual"]}**.  
            Preço-teto: **{melhor_empresa["preco_teto"]}**.  
            Preço justo estimado: **{melhor_empresa["preco_justo"]}**.

            **Leitura executiva:** {melhor_empresa["leitura"]}
            """
        )


def renderizar_ranking_visual(ranking_empresas_reais: list[dict]) -> None:
    st.markdown("#### Ranking visual das empresas reais")

    st.caption(
        "Ordenado pelo score de atratividade. O score mede proximidade ao preço-teto e leitura do status, não qualidade absoluta da empresa."
    )

    if len(ranking_empresas_reais) == 0:
        st.warning("Nenhuma empresa real cadastrada para gerar ranking.")
        return

    top_empresas = ranking_empresas_reais[:3]
    colunas = st.columns(len(top_empresas))

    for coluna, empresa in zip(colunas, top_empresas):
        with coluna:
            with st.container(border=True):
                st.markdown(f"### #{empresa['Ranking']} — {empresa['Ticker']}")
                st.metric("Score", empresa["Score"])
                st.caption(empresa["Empresa"])
                st.markdown(f"**Status:** {empresa['Status']}")
                st.markdown(f"**Margem até teto:** {empresa['Margem até preço-teto']}")
                st.markdown(f"**Potencial até justo:** {empresa['Potencial até preço justo']}")


renderizar_hero()


with st.sidebar:
    st.header("Premissas do valuation")

    opcoes_modelo = [OPCAO_ANALISE_MANUAL] + list(EMPRESAS.keys())

    modelo_escolhido = st.selectbox(
        "Escolha uma empresa/modelo",
        opcoes_modelo,
    )

    modo_manual = modelo_escolhido == OPCAO_ANALISE_MANUAL

    if modo_manual:
        dados = DADOS_ANALISE_MANUAL.copy()

        simbolo_moeda = st.selectbox(
            "Moeda da análise",
            ["R$", "US$"],
            index=0,
            help="Escolha apenas o símbolo visual. Os números devem ser inseridos de forma consistente.",
        )

        dados["simbolo_moeda"] = simbolo_moeda

        st.info(
            "Modo manual ativado. Insira os números usando a mesma unidade. "
            "Exemplo: se lucro e FCF estão em milhões, quantidade de ações também deve estar em milhões."
        )
    else:
        dados = EMPRESAS[modelo_escolhido]
        simbolo_moeda = dados.get("simbolo_moeda", "R$")

    st.caption("Os dados iniciais são editáveis e podem ser ajustados manualmente.")

    st.markdown("#### Empresa")

    empresa = st.text_input(
        "Nome da empresa",
        value=dados["empresa"],
        key=f"empresa_{modelo_escolhido}",
    )

    ticker = st.text_input(
        "Ticker",
        value=dados["ticker"],
        key=f"ticker_{modelo_escolhido}",
    )

    st.divider()

    st.markdown("#### Dados financeiros")

    lucro_liquido_sustentavel = st.number_input(
        "Lucro líquido sustentável",
        min_value=-1_000_000_000_000.0,
        value=float(dados["lucro_liquido_sustentavel"]),
        step=100.0 if modo_manual else 100_000_000.0,
        help="Use um lucro normalizado, evitando anos extraordinários.",
        key=f"lucro_{modelo_escolhido}",
    )

    fluxo_caixa_livre = st.number_input(
        "Fluxo de caixa livre",
        min_value=-1_000_000_000_000.0,
        value=float(dados["fluxo_caixa_livre"]),
        step=100.0 if modo_manual else 100_000_000.0,
        help="Fluxo de caixa operacional menos investimentos necessários.",
        key=f"fcf_{modelo_escolhido}",
    )

    quantidade_acoes = st.number_input(
        "Quantidade de ações",
        min_value=1.0,
        value=float(dados["quantidade_acoes"]),
        step=10.0 if modo_manual else 10_000_000.0,
        help="Quantidade total de ações da empresa. Use a mesma escala dos outros dados.",
        key=f"acoes_{modelo_escolhido}",
    )

    preco_atual = st.number_input(
        "Preço atual da ação",
        min_value=0.01,
        value=float(dados["preco_atual"]),
        step=0.50,
        key=f"preco_{modelo_escolhido}",
    )

    st.divider()

    st.markdown("#### Premissas de valuation")

    multiplo_justo_eps = st.number_input(
        "Múltiplo justo de EPS",
        min_value=0.0,
        value=float(dados["multiplo_justo_eps"]),
        step=0.5,
        help="Exemplo: P/L justo que você aceita pagar pela empresa.",
        key=f"mult_eps_{modelo_escolhido}",
    )

    multiplo_justo_fcf = st.number_input(
        "Múltiplo justo de FCF",
        min_value=0.0,
        value=float(dados["multiplo_justo_fcf"]),
        step=0.5,
        help="Exemplo: P/FCF justo que você aceita pagar pela empresa.",
        key=f"mult_fcf_{modelo_escolhido}",
    )

    peso_eps = st.slider(
        "Peso do EPS no valuation",
        min_value=0,
        max_value=100,
        value=int(dados["peso_eps"]),
        key=f"peso_eps_{modelo_escolhido}",
    )

    peso_fcf = st.slider(
        "Peso do FCF no valuation",
        min_value=0,
        max_value=100,
        value=int(dados["peso_fcf"]),
        key=f"peso_fcf_{modelo_escolhido}",
    )

    margem_seguranca = st.slider(
        "Margem de segurança",
        min_value=0,
        max_value=90,
        value=int(dados["margem_seguranca"]),
        key=f"margem_{modelo_escolhido}",
    )


st.subheader(f"Análise de valuation: {empresa} ({ticker.upper()})")

try:
    entradas = EntradasValuation(
        empresa=empresa,
        ticker=ticker.upper(),
        lucro_liquido_sustentavel=lucro_liquido_sustentavel,
        fluxo_caixa_livre=fluxo_caixa_livre,
        quantidade_acoes=quantidade_acoes,
        multiplo_justo_eps=multiplo_justo_eps,
        multiplo_justo_fcf=multiplo_justo_fcf,
        peso_eps=peso_eps,
        peso_fcf=peso_fcf,
        margem_seguranca=margem_seguranca,
        preco_atual=preco_atual,
    )

    resultado = calcular_valuation(entradas)

    renderizar_painel_decisao(
        preco_atual=preco_atual,
        resultado=resultado,
        simbolo_moeda=simbolo_moeda,
    )

    st.divider()

    col_salvar, col_info = st.columns([1, 3])

    with col_salvar:
        if st.button("Salvar análise"):
            salvar_analise(entradas, resultado)
            st.success("Análise salva com sucesso.")

    with col_info:
        st.caption(
            "O histórico registra as premissas usadas no momento do cálculo. "
            "Isso ajuda a comparar mudanças de valuation ao longo do tempo."
        )

    st.divider()

    aba_resultado, aba_simulador, aba_comparativo, aba_tese, aba_premissas, aba_historico, aba_educacional = st.tabs(
        [
            "Resultado",
            "Simulador",
            "Comparativo",
            "Tese da empresa",
            "Premissas usadas",
            "Histórico",
            "Visão educacional",
        ]
    )

    with aba_resultado:
        st.markdown("### Resultado do valuation")

        col_a, col_b = st.columns(2)

        with col_a:
            st.metric(
                "EPS normalizado",
                formatar_moeda(resultado["eps_normalizado"], simbolo_moeda),
            )

        with col_b:
            st.metric(
                "FCF por ação",
                formatar_moeda(resultado["fcf_por_acao"], simbolo_moeda),
            )

        col_c, col_d = st.columns(2)

        with col_c:
            st.metric(
                "Preço justo por EPS",
                formatar_moeda(resultado["preco_justo_eps"], simbolo_moeda),
            )

        with col_d:
            st.metric(
                "Preço justo por FCF",
                formatar_moeda(resultado["preco_justo_fcf"], simbolo_moeda),
            )

        st.divider()

        col_e, col_f = st.columns(2)

        with col_e:
            st.metric(
                "Preço justo combinado",
                formatar_moeda(resultado["preco_justo_combinado"], simbolo_moeda),
                formatar_percentual(resultado["potencial_ate_preco_justo"]),
            )

        with col_f:
            st.metric(
                "Preço-teto com margem de segurança",
                formatar_moeda(resultado["preco_teto"], simbolo_moeda),
                formatar_percentual(resultado["margem_ate_preco_teto"]),
            )

        st.divider()

        renderizar_mapa_valuation(
            preco_atual=preco_atual,
            preco_teto=resultado["preco_teto"],
            preco_justo=resultado["preco_justo_combinado"],
            simbolo=simbolo_moeda,
        )

        st.divider()

        st.markdown("### Tabela-resumo")

        tabela_resultado = [
            {
                "Indicador": "EPS normalizado",
                "Valor": formatar_moeda(resultado["eps_normalizado"], simbolo_moeda),
            },
            {
                "Indicador": "FCF por ação",
                "Valor": formatar_moeda(resultado["fcf_por_acao"], simbolo_moeda),
            },
            {
                "Indicador": "Preço justo por EPS",
                "Valor": formatar_moeda(resultado["preco_justo_eps"], simbolo_moeda),
            },
            {
                "Indicador": "Preço justo por FCF",
                "Valor": formatar_moeda(resultado["preco_justo_fcf"], simbolo_moeda),
            },
            {
                "Indicador": "Preço justo combinado",
                "Valor": formatar_moeda(resultado["preco_justo_combinado"], simbolo_moeda),
            },
            {
                "Indicador": "Preço-teto",
                "Valor": formatar_moeda(resultado["preco_teto"], simbolo_moeda),
            },
            {
                "Indicador": "Preço atual",
                "Valor": formatar_moeda(preco_atual, simbolo_moeda),
            },
            {
                "Indicador": "Status",
                "Valor": resultado["status"],
            },
        ]

        st.table(preparar_tabela(tabela_resultado))

    with aba_simulador:
        renderizar_simulador_cenarios(
            entradas_base=entradas,
            simbolo_moeda=simbolo_moeda,
            formatar_moeda=formatar_moeda,
            formatar_percentual=formatar_percentual,
            preparar_tabela=preparar_tabela,
        )

    with aba_comparativo:
        st.markdown("### Central inteligente de comparação")

        st.caption(
            "Compare empresas pelo mesmo critério de valuation e identifique quais estão mais próximas de uma zona racional de entrada."
        )

        melhor_empresa = encontrar_empresa_mais_atrativa(
            EMPRESAS,
            formatar_moeda,
            formatar_percentual,
        )

        renderizar_radar_oportunidade(melhor_empresa)

        st.divider()

        ranking_empresas_reais = gerar_ranking_empresas_reais(
            EMPRESAS,
            formatar_moeda,
            formatar_percentual,
        )

        renderizar_ranking_visual(ranking_empresas_reais)

        st.markdown("#### Ranking técnico")

        if len(ranking_empresas_reais) == 0:
            st.warning("Nenhuma empresa real cadastrada para gerar ranking.")
        else:
            st.dataframe(
                preparar_tabela(ranking_empresas_reais),
                use_container_width=True,
                hide_index=True,
            )

        st.divider()

        tabela_comparativo = gerar_comparativo(
            EMPRESAS,
            formatar_moeda,
            formatar_percentual,
        )

        st.markdown("#### Filtros avançados")

        col_filtro_1, col_filtro_2 = st.columns(2)

        with col_filtro_1:
            filtro_tipo = st.selectbox(
                "Filtrar por tipo",
                ["Todos", "Real", "Didática"],
                index=1,
            )

        with col_filtro_2:
            filtro_status = st.selectbox(
                "Filtrar por status",
                ["Todos", "COMPRA", "NEUTRO", "AGUARDE"],
            )

        tabela_filtrada = tabela_comparativo

        if filtro_tipo != "Todos":
            tabela_filtrada = [
                linha for linha in tabela_filtrada
                if linha["Tipo"] == filtro_tipo
            ]

        if filtro_status != "Todos":
            tabela_filtrada = [
                linha for linha in tabela_filtrada
                if linha["Status"] == filtro_status
            ]

        st.markdown("#### Base completa de comparação")

        if len(tabela_filtrada) == 0:
            st.warning("Nenhuma empresa encontrada com os filtros selecionados.")
        else:
            tabela_preparada = preparar_tabela(tabela_filtrada)

            st.dataframe(
                tabela_preparada,
                use_container_width=True,
                hide_index=True,
            )

            csv_comparativo = converter_tabela_para_csv(tabela_preparada)

            st.download_button(
                label="Baixar comparativo em CSV",
                data=csv_comparativo,
                file_name="comparativo_preco_teto.csv",
                mime="text/csv",
            )

    with aba_tese:
        st.markdown("### Tese qualitativa da empresa")

        st.text_area(
            "Tese da empresa",
            value=dados["tese"],
            height=130,
            key=f"tese_{modelo_escolhido}",
        )

        st.text_area(
            "Principais riscos",
            value=dados["riscos"],
            height=130,
            key=f"riscos_{modelo_escolhido}",
        )

        st.text_area(
            "Fundamentos observados",
            value=dados["fundamentos"],
            height=130,
            key=f"fundamentos_{modelo_escolhido}",
        )

    with aba_premissas:
        st.markdown("### Premissas utilizadas")

        moeda_unidade = dados.get("moeda", "Não informado").replace("$", "\\$")

        st.info(
            f"""
            **Perfil da empresa:** {dados.get("perfil_empresa", "Não informado")}  
            **Moeda/unidade:** {moeda_unidade}  
            **Data de referência:** {dados.get("data_referencia", "Não informado")}  
            **Fonte das premissas:** {dados.get("fonte_premissas", "Não informado")}
            """
        )

        if modo_manual:
            st.warning(
                "Esta é uma análise manual. O app não verificou automaticamente os dados inseridos. "
                "A qualidade do resultado depende totalmente da qualidade das premissas."
            )

        tabela_premissas = [
            {
                "Premissa": "Lucro líquido sustentável",
                "Valor": formatar_moeda(lucro_liquido_sustentavel, simbolo_moeda),
            },
            {
                "Premissa": "Fluxo de caixa livre",
                "Valor": formatar_moeda(fluxo_caixa_livre, simbolo_moeda),
            },
            {
                "Premissa": "Quantidade de ações",
                "Valor": formatar_numero(quantidade_acoes),
            },
            {
                "Premissa": "Preço atual",
                "Valor": formatar_moeda(preco_atual, simbolo_moeda),
            },
            {
                "Premissa": "Múltiplo justo EPS",
                "Valor": multiplo_justo_eps,
            },
            {
                "Premissa": "Múltiplo justo FCF",
                "Valor": multiplo_justo_fcf,
            },
            {
                "Premissa": "Peso EPS",
                "Valor": f"{peso_eps}%",
            },
            {
                "Premissa": "Peso FCF",
                "Valor": f"{peso_fcf}%",
            },
            {
                "Premissa": "Margem de segurança",
                "Valor": f"{margem_seguranca}%",
            },
        ]

        st.table(preparar_tabela(tabela_premissas))

    with aba_historico:
        st.markdown("### Histórico de análises salvas")

        historico = carregar_historico()

        if len(historico) == 0:
            st.info("Nenhuma análise foi salva ainda.")
        else:
            historico_mais_recente_primeiro = list(reversed(historico))
            st.table(preparar_tabela(historico_mais_recente_primeiro))

            with open(CAMINHO_HISTORICO, "rb") as arquivo:
                st.download_button(
                    label="Baixar histórico em CSV",
                    data=arquivo,
                    file_name="historico_analises.csv",
                    mime="text/csv",
                )

    with aba_educacional:
        renderizar_aba_educacional()

except ValueError as erro:
    st.error(str(erro))