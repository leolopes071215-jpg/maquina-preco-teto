import csv
from io import StringIO

import streamlit as st

from valuation import EntradasValuation, calcular_valuation
from empresas import EMPRESAS
from historico import salvar_analise, carregar_historico, CAMINHO_HISTORICO
from style import aplicar_estilo
from comparativo import (
    gerar_comparativo,
    encontrar_empresa_mais_atrativa,
    gerar_ranking_empresas_reais,
)


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


st.markdown(
    """
    # 📊 Máquina de Preço-Teto

    ### Valuation conservador para investidores que querem comprar ações com método, margem de segurança e clareza.

    A Máquina de Preço-Teto organiza premissas fundamentais de uma empresa e estima uma faixa racional de preço com base em:

    **lucro líquido sustentável**, **fluxo de caixa livre**, **múltiplos justos**, **pesos entre EPS e FCF** e **margem de segurança**.

    O objetivo não é prever o futuro com precisão absoluta.  
    O objetivo é evitar decisões emocionais, organizar premissas e comparar empresas de forma mais disciplinada.
    """
)

col_home_1, col_home_2, col_home_3, col_home_4 = st.columns(4)

with col_home_1:
    st.metric("Empresas", len(EMPRESAS))

with col_home_2:
    st.metric("Modelo", "EPS + FCF")

with col_home_3:
    st.metric("Decisão", "3 status")

with col_home_4:
    st.metric("Margem", "Ajustável")

st.warning(
    "Aviso importante: esta ferramenta é apenas educacional. "
    "Não representa recomendação de compra, venda ou manutenção de investimentos. "
    "Os resultados dependem diretamente das premissas inseridas."
)

st.divider()


with st.sidebar:
    st.header("Premissas do valuation")

    modelo_escolhido = st.selectbox(
        "Escolha uma empresa/modelo",
        list(EMPRESAS.keys()),
    )

    dados = EMPRESAS[modelo_escolhido]
    simbolo_moeda = dados.get("simbolo_moeda", "R$")

    st.caption("Os dados iniciais são didáticos e podem ser editados manualmente.")

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

    lucro_liquido_sustentavel = st.number_input(
        "Lucro líquido sustentável",
        min_value=-1_000_000_000_000.0,
        value=float(dados["lucro_liquido_sustentavel"]),
        step=100_000_000.0,
        help="Use um lucro normalizado, evitando anos extraordinários.",
        key=f"lucro_{modelo_escolhido}",
    )

    fluxo_caixa_livre = st.number_input(
        "Fluxo de caixa livre",
        min_value=-1_000_000_000_000.0,
        value=float(dados["fluxo_caixa_livre"]),
        step=100_000_000.0,
        help="Fluxo de caixa operacional menos investimentos necessários.",
        key=f"fcf_{modelo_escolhido}",
    )

    quantidade_acoes = st.number_input(
        "Quantidade de ações",
        min_value=1.0,
        value=float(dados["quantidade_acoes"]),
        step=10_000_000.0,
        help="Quantidade total de ações da empresa.",
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

    col1, col2, col3 = st.columns(3)

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
            st.success("Status: COMPRA")
        elif status == "NEUTRO":
            st.warning("Status: NEUTRO")
        else:
            st.error("Status: AGUARDE")

    st.markdown("### Leitura automática do status")
    st.info(resultado["explicacao_status"])

    st.divider()

    col_salvar, col_info = st.columns([1, 3])

    with col_salvar:
        if st.button("Salvar análise no histórico"):
            salvar_analise(entradas, resultado)
            st.success("Análise salva com sucesso.")

    with col_info:
        st.caption(
            "O histórico registra as premissas usadas no momento do cálculo. "
            "Isso ajuda a comparar mudanças de valuation ao longo do tempo."
        )

    st.divider()

    aba_resultado, aba_comparativo, aba_tese, aba_premissas, aba_historico, aba_educacional = st.tabs(
        [
            "Resultado",
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

    with aba_comparativo:
        st.markdown("### Comparativo das empresas cadastradas")

        st.caption(
            "Esta tabela compara todas as empresas cadastradas usando as premissas salvas no arquivo empresas.py."
        )

        melhor_empresa = encontrar_empresa_mais_atrativa(
            EMPRESAS,
            formatar_moeda,
            formatar_percentual,
        )

        st.markdown("#### Empresa mais atrativa pelo modelo")

        col_best_1, col_best_2, col_best_3, col_best_4 = st.columns(4)

        with col_best_1:
            st.metric("Empresa", melhor_empresa["ticker"])

        with col_best_2:
            st.metric("Preço atual", melhor_empresa["preco_atual"])

        with col_best_3:
            st.metric("Preço-teto", melhor_empresa["preco_teto"])

        with col_best_4:
            st.metric("Status", melhor_empresa["status"])

        st.info(
            f"""
            **{melhor_empresa["empresa"]}** é a empresa mais atrativa pelo critério de maior margem até o preço-teto entre as empresas reais cadastradas.  
            Margem até preço-teto: **{melhor_empresa["margem_ate_preco_teto"]}**.  
            Potencial até preço justo: **{melhor_empresa["potencial_ate_preco_justo"]}**.
            """
        )

        st.markdown("#### Ranking das empresas reais")

        ranking_empresas_reais = gerar_ranking_empresas_reais(
            EMPRESAS,
            formatar_moeda,
            formatar_percentual,
        )

        if len(ranking_empresas_reais) == 0:
            st.warning("Nenhuma empresa real cadastrada para gerar ranking.")
        else:
            st.caption(
                "Ranking ordenado pela maior margem até o preço-teto. "
                "A primeira posição não significa recomendação de compra; apenas indica a empresa menos distante do preço-teto dentro das premissas atuais."
            )

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

        st.markdown("#### Filtros")

        col_filtro_1, col_filtro_2 = st.columns(2)

        with col_filtro_1:
            filtro_tipo = st.selectbox(
                "Filtrar por tipo",
                ["Todos", "Real", "Didática"],
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

        st.markdown("#### Tabela comparativa")

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
        st.markdown(
            """
            ### Como a Máquina de Preço-Teto calcula o valor?

            O modelo usa duas bases principais:

            **1. Lucro por ação normalizado**

            EPS = lucro líquido sustentável / quantidade de ações

            Depois:

            Preço justo por EPS = EPS × múltiplo justo de EPS

            ---

            **2. Fluxo de caixa livre por ação**

            FCF por ação = fluxo de caixa livre / quantidade de ações

            Depois:

            Preço justo por FCF = FCF por ação × múltiplo justo de FCF

            ---

            **3. Preço justo combinado**

            O preço justo combinado é uma média ponderada entre o preço justo calculado pelo lucro
            e o preço justo calculado pelo fluxo de caixa livre.

            ---

            **4. Preço-teto**

            O preço-teto aplica uma margem de segurança sobre o preço justo combinado.

            Exemplo:

            Se o preço justo é R$ 100,00 e a margem de segurança é 25%,
            o preço-teto será R$ 75,00.

            ---

            ### Como interpretar o status?

            **COMPRA:** o preço atual está abaixo ou igual ao preço-teto.

            **NEUTRO:** o preço atual está acima do preço-teto, mas ainda abaixo do preço justo estimado.

            **AGUARDE:** o preço atual está acima do preço justo estimado.

            ---

            Esta ferramenta é educacional. Ela não substitui uma análise completa da empresa,
            do setor, da gestão, dos riscos, da estrutura de capital e da qualidade dos lucros.
            """
        )

except ValueError as erro:
    st.error(str(erro))