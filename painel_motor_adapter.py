# painel_motor_adapter.py

from datetime import datetime
from typing import Any, Dict, List

import streamlit as st

from valuation import EntradasValuation
from valuation_core_adapter import (
    VERSAO_ADAPTER_CORE,
    calcular_valuation_por_motor,
    comparar_motores_por_entradas,
    executar_autoteste_adapter_core,
    gerar_entradas_exemplo_adapter,
    gerar_markdown_adapter_core,
    gerar_tabela_comparacao_adapter,
)


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v3.8.5 — Painel Interno do Motor Adapter
# ------------------------------------------------------------
# Esta tela audita o adaptador seguro entre:
#
# - valuation.py              -> motor legacy atual
# - core_valuation.py         -> novo Core Engine
# - valuation_core_adapter.py -> ponte segura entre os dois
#
# Objetivo:
# - comparar resultado legacy vs core via adapter
# - testar entradas reais/manualizadas
# - validar compatibilidade antes da troca definitiva do motor
# - permitir relatório técnico da comparação
# ============================================================


def _injetar_css_motor_adapter() -> None:
    st.markdown(
        """
        <style>
            .ma-hero {
                padding: 1.75rem 1.8rem;
                border-radius: 30px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    radial-gradient(circle at top left, rgba(214, 181, 109, 0.25), transparent 30%),
                    radial-gradient(circle at bottom right, rgba(74, 144, 226, 0.22), transparent 34%),
                    linear-gradient(135deg, rgba(8, 15, 27, 0.99), rgba(5, 9, 18, 0.99));
                box-shadow: 0 18px 55px rgba(0, 0, 0, 0.34);
                margin-bottom: 1.25rem;
            }

            .ma-eyebrow {
                color: #d6b56d;
                font-size: 0.78rem;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.35rem;
            }

            .ma-title {
                color: #f4f7fb;
                font-size: 2.1rem;
                font-weight: 900;
                margin-bottom: 0.45rem;
                line-height: 1.14;
            }

            .ma-subtitle {
                color: rgba(244, 247, 251, 0.76);
                font-size: 1rem;
                line-height: 1.62;
                max-width: 1080px;
            }

            .ma-card {
                padding: 1.1rem 1.15rem;
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.035);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.18);
                height: 100%;
            }

            .ma-card-label {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .ma-card-value {
                color: #f4f7fb;
                font-size: 1.22rem;
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .ma-card-note {
                color: rgba(244, 247, 251, 0.68);
                font-size: 0.87rem;
                line-height: 1.47;
            }

            .ma-highlight {
                padding: 0.95rem 1rem;
                border-radius: 16px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.92rem;
                line-height: 1.55;
                margin-bottom: 0.7rem;
            }

            .ma-disclaimer {
                padding: 0.95rem 1rem;
                border-radius: 16px;
                background: rgba(74, 144, 226, 0.08);
                border: 1px solid rgba(74, 144, 226, 0.18);
                color: rgba(244, 247, 251, 0.78);
                font-size: 0.9rem;
                line-height: 1.55;
                margin-top: 1.1rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _card(label: str, value: str, note: str = "") -> None:
    st.markdown(
        f"""
        <div class="ma-card">
            <div class="ma-card-label">{label}</div>
            <div class="ma-card-value">{value}</div>
            <div class="ma-card-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _formatar_moeda(valor: Any, moeda: str = "R$") -> str:
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        numero = 0.0

    return f"{moeda} {numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _formatar_percentual(valor: Any) -> str:
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        numero = 0.0

    return f"{numero:.2f}%"


def _todos_testes_ok(testes: List[Dict[str, str]]) -> bool:
    return all(teste.get("status") == "OK" for teste in testes)


def _resultado_para_tabela(resultado: Dict[str, Any], rotulo_motor: str, moeda: str) -> List[Dict[str, str]]:
    return [
        {
            "Motor": rotulo_motor,
            "Indicador": "EPS normalizado",
            "Valor": _formatar_moeda(resultado.get("eps_normalizado", 0), moeda),
        },
        {
            "Motor": rotulo_motor,
            "Indicador": "FCF por ação",
            "Valor": _formatar_moeda(resultado.get("fcf_por_acao", 0), moeda),
        },
        {
            "Motor": rotulo_motor,
            "Indicador": "Preço justo por EPS",
            "Valor": _formatar_moeda(resultado.get("preco_justo_eps", 0), moeda),
        },
        {
            "Motor": rotulo_motor,
            "Indicador": "Preço justo por FCF",
            "Valor": _formatar_moeda(resultado.get("preco_justo_fcf", 0), moeda),
        },
        {
            "Motor": rotulo_motor,
            "Indicador": "Preço justo combinado",
            "Valor": _formatar_moeda(resultado.get("preco_justo_combinado", 0), moeda),
        },
        {
            "Motor": rotulo_motor,
            "Indicador": "Preço-teto",
            "Valor": _formatar_moeda(resultado.get("preco_teto", 0), moeda),
        },
        {
            "Motor": rotulo_motor,
            "Indicador": "Margem até preço-teto",
            "Valor": _formatar_percentual(resultado.get("margem_ate_preco_teto", 0)),
        },
        {
            "Motor": rotulo_motor,
            "Indicador": "Potencial até preço justo",
            "Valor": _formatar_percentual(resultado.get("potencial_ate_preco_justo", 0)),
        },
        {
            "Motor": rotulo_motor,
            "Indicador": "Status",
            "Valor": str(resultado.get("status", "")),
        },
        {
            "Motor": rotulo_motor,
            "Indicador": "Motor",
            "Valor": str(resultado.get("motor", "")),
        },
    ]


def _gerar_entradas_por_formulario(
    empresa: str,
    ticker: str,
    lucro_liquido_sustentavel: float,
    fluxo_caixa_livre: float,
    quantidade_acoes: float,
    multiplo_justo_eps: float,
    multiplo_justo_fcf: float,
    peso_eps: float,
    peso_fcf: float,
    margem_seguranca: float,
    preco_atual: float,
) -> EntradasValuation:
    return EntradasValuation(
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


def _gerar_leitura_tecnica(comparacao: Dict[str, Any]) -> str:
    if comparacao.get("aprovado"):
        return (
            "O adaptador está aprovado para esta entrada. O motor legacy e o Core Engine "
            "entregam resultados compatíveis dentro da tolerância definida. Isso permite avançar "
            "para a próxima etapa: criar alternância controlada de motor no app principal."
        )

    return (
        "O adaptador encontrou diferenças críticas para esta entrada. A troca do motor principal "
        "ainda não deve ser feita. Revise os campos divergentes antes de avançar."
    )


def renderizar_painel_motor_adapter() -> None:
    """
    Renderiza o painel interno do Motor Adapter.
    """
    _injetar_css_motor_adapter()

    st.markdown(
        """
        <div class="ma-hero">
            <div class="ma-eyebrow">v3.8.5 — Motor Adapter</div>
            <div class="ma-title">Adaptador Seguro do Core Engine</div>
            <div class="ma-subtitle">
                Compare o motor Legacy com o novo Core Engine usando uma ponte segura.
                Este painel valida se o app pode começar a alternar entre motores sem quebrar a interface.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="ma-highlight">
            O adaptador é a ponte entre o produto atual e a arquitetura profissional.
            Ele permite testar o Core Engine sem destruir o motor antigo.
        </div>
        """,
        unsafe_allow_html=True,
    )

    testes = executar_autoteste_adapter_core()

    st.markdown("### Diagnóstico do adaptador")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Versão Adapter", VERSAO_ADAPTER_CORE)

    with col_2:
        st.metric("Autotestes", len(testes))

    with col_3:
        st.metric("Status geral", "OK" if _todos_testes_ok(testes) else "FALHA")

    with col_4:
        st.metric("Finalidade", "Ponte segura")

    if _todos_testes_ok(testes):
        st.success("Motor Adapter passou nos autotestes.")
    else:
        st.error("Motor Adapter apresentou falha nos autotestes.")

    st.divider()

    st.markdown("### Autotestes do Adapter")

    st.dataframe(
        testes,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    exemplo = gerar_entradas_exemplo_adapter()

    st.markdown("### Testar entrada manual")

    with st.form("form_motor_adapter"):
        col_a, col_b = st.columns(2)

        with col_a:
            empresa = st.text_input(
                "Empresa",
                value=exemplo.empresa,
                key="ma_empresa",
            )

            ticker = st.text_input(
                "Ticker",
                value=exemplo.ticker,
                key="ma_ticker",
            )

            lucro_liquido_sustentavel = st.number_input(
                "Lucro líquido sustentável",
                value=float(exemplo.lucro_liquido_sustentavel),
                step=100_000_000.0,
                key="ma_lucro_liquido",
            )

            fluxo_caixa_livre = st.number_input(
                "Fluxo de caixa livre",
                value=float(exemplo.fluxo_caixa_livre),
                step=100_000_000.0,
                key="ma_fcf",
            )

            quantidade_acoes = st.number_input(
                "Quantidade de ações",
                min_value=1.0,
                value=float(exemplo.quantidade_acoes),
                step=10_000_000.0,
                key="ma_quantidade_acoes",
            )

        with col_b:
            preco_atual = st.number_input(
                "Preço atual",
                min_value=0.01,
                value=float(exemplo.preco_atual),
                step=0.5,
                key="ma_preco_atual",
            )

            multiplo_justo_eps = st.number_input(
                "Múltiplo justo EPS",
                min_value=0.0,
                value=float(exemplo.multiplo_justo_eps),
                step=0.5,
                key="ma_multiplo_eps",
            )

            multiplo_justo_fcf = st.number_input(
                "Múltiplo justo FCF",
                min_value=0.0,
                value=float(exemplo.multiplo_justo_fcf),
                step=0.5,
                key="ma_multiplo_fcf",
            )

            peso_eps = st.slider(
                "Peso EPS",
                min_value=0,
                max_value=100,
                value=int(exemplo.peso_eps),
                key="ma_peso_eps",
            )

            peso_fcf = st.slider(
                "Peso FCF",
                min_value=0,
                max_value=100,
                value=int(exemplo.peso_fcf),
                key="ma_peso_fcf",
            )

            margem_seguranca = st.slider(
                "Margem de segurança",
                min_value=0,
                max_value=90,
                value=int(exemplo.margem_seguranca),
                key="ma_margem",
            )

        col_config_1, col_config_2 = st.columns(2)

        with col_config_1:
            moeda = st.selectbox(
                "Moeda visual",
                ["R$", "US$"],
                index=0,
                key="ma_moeda",
            )

        with col_config_2:
            tolerancia = st.number_input(
                "Tolerância da comparação",
                min_value=0.0,
                max_value=1.0,
                value=0.0001,
                step=0.0001,
                format="%.6f",
                key="ma_tolerancia",
            )

        calcular = st.form_submit_button("Comparar Legacy vs Core via Adapter")

        if calcular:
            entradas = _gerar_entradas_por_formulario(
                empresa=empresa,
                ticker=ticker,
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

            comparacao = comparar_motores_por_entradas(
                entradas=entradas,
                moeda=moeda,
                tolerancia=tolerancia,
            )

            st.session_state["resultado_motor_adapter"] = {
                "entradas": entradas,
                "comparacao": comparacao,
                "moeda": moeda,
                "tolerancia": tolerancia,
                "data": datetime.now().isoformat(timespec="seconds"),
            }

            if comparacao.get("aprovado"):
                st.success("Comparação aprovada para esta entrada.")
            else:
                st.error("Comparação encontrou diferenças críticas.")

    resultado_atual = st.session_state.get("resultado_motor_adapter")

    if resultado_atual is None:
        entradas_padrao = gerar_entradas_exemplo_adapter()

        comparacao_padrao = comparar_motores_por_entradas(
            entradas=entradas_padrao,
            moeda="R$",
            tolerancia=0.0001,
        )

        resultado_atual = {
            "entradas": entradas_padrao,
            "comparacao": comparacao_padrao,
            "moeda": "R$",
            "tolerancia": 0.0001,
            "data": datetime.now().isoformat(timespec="seconds"),
        }

        st.session_state["resultado_motor_adapter"] = resultado_atual

    comparacao_atual = resultado_atual["comparacao"]
    moeda_atual = resultado_atual["moeda"]

    st.divider()

    st.markdown("### Resultado comparativo")

    resultado_legacy = comparacao_atual.get("resultado_legacy", {})
    resultado_core = comparacao_atual.get("resultado_core", {})

    col_r1, col_r2, col_r3, col_r4 = st.columns(4)

    with col_r1:
        _card(
            "Status Legacy",
            str(resultado_legacy.get("status", "")),
            "Resultado do motor antigo.",
        )

    with col_r2:
        _card(
            "Status Core",
            str(resultado_core.get("status", "")),
            "Resultado do novo motor.",
        )

    with col_r3:
        _card(
            "Preço-teto Legacy",
            _formatar_moeda(resultado_legacy.get("preco_teto", 0), moeda_atual),
            "Motor atual do app.",
        )

    with col_r4:
        _card(
            "Preço-teto Core",
            _formatar_moeda(resultado_core.get("preco_teto", 0), moeda_atual),
            "Core Engine via adapter.",
        )

    if comparacao_atual.get("aprovado"):
        st.success("Adapter aprovado: os motores estão compatíveis para esta entrada.")
    else:
        st.error("Adapter reprovado: há diferenças críticas entre os motores.")

    st.info(_gerar_leitura_tecnica(comparacao_atual))

    st.divider()

    st.markdown("### Tabela lado a lado")

    tabela_lado_a_lado = []
    tabela_lado_a_lado.extend(
        _resultado_para_tabela(
            resultado=resultado_legacy,
            rotulo_motor="Legacy",
            moeda=moeda_atual,
        )
    )
    tabela_lado_a_lado.extend(
        _resultado_para_tabela(
            resultado=resultado_core,
            rotulo_motor="Core",
            moeda=moeda_atual,
        )
    )

    st.dataframe(
        tabela_lado_a_lado,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Comparação campo a campo")

    tabela_comparacao = gerar_tabela_comparacao_adapter(comparacao_atual)

    filtro = st.selectbox(
        "Filtrar campos",
        ["Todos", "Apenas diferenças críticas", "Apenas compatíveis"],
        key="ma_filtro_comparacao",
    )

    tabela_filtrada = tabela_comparacao

    if filtro == "Apenas diferenças críticas":
        tabela_filtrada = [
            linha for linha in tabela_comparacao
            if linha.get("Compatível") == "Não"
        ]
    elif filtro == "Apenas compatíveis":
        tabela_filtrada = [
            linha for linha in tabela_comparacao
            if linha.get("Compatível") == "Sim"
        ]

    st.dataframe(
        tabela_filtrada,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Diferenças críticas")

    campos_com_diferenca = comparacao_atual.get("campos_com_diferenca", [])

    if len(campos_com_diferenca) == 0:
        st.success("Nenhuma diferença crítica encontrada.")
    else:
        st.warning("Existem diferenças críticas. Não avance para troca do motor principal.")
        st.dataframe(
            campos_com_diferenca,
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    st.markdown("### Resultado bruto")

    col_json_1, col_json_2 = st.columns(2)

    with col_json_1:
        with st.expander("Ver resultado Legacy bruto"):
            st.json(resultado_legacy)

    with col_json_2:
        with st.expander("Ver resultado Core bruto"):
            st.json(resultado_core)

    st.divider()

    st.markdown("### Download técnico")

    st.download_button(
        label="Baixar relatório do Motor Adapter (.md)",
        data=gerar_markdown_adapter_core(comparacao_atual),
        file_name="relatorio_motor_adapter.md",
        mime="text/markdown",
        key="download_relatorio_motor_adapter",
    )

    st.markdown(
        """
        <div class="ma-disclaimer">
            <strong>Regra de segurança:</strong> este painel ainda não troca o motor principal.
            Ele apenas valida a ponte entre Legacy e Core Engine. A troca definitiva será feita
            depois com alternância controlada e possibilidade de retorno ao motor antigo.
        </div>
        """,
        unsafe_allow_html=True,
    )