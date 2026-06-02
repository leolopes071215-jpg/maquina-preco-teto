# painel_motor_controlado.py

from datetime import datetime
from typing import Any, Dict, List

import streamlit as st

from valuation import EntradasValuation
from motor_valuation_controlado import (
    MOTOR_CORE,
    MOTOR_LEGACY,
    VERSAO_MOTOR_CONTROLADO,
    auditar_motor_selecionado,
    calcular_valuation_controlado,
    executar_autoteste_motor_controlado,
    gerar_entradas_exemplo_motor_controlado,
    gerar_markdown_motor_controlado,
    gerar_resumo_motor_controlado,
    gerar_tabela_auditoria_motor_controlado,
    obter_descricao_motor,
    obter_motor_padrao,
    obter_motores_disponiveis,
)


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v3.8.7 — Painel Interno do Motor Controlado
# ------------------------------------------------------------
# Esta tela audita o seletor controlado de motor.
#
# Objetivo:
# - permitir escolher entre motor Legacy e Core Engine
# - calcular valuation com o motor selecionado
# - auditar Legacy vs Core em paralelo
# - validar segurança antes de ligar o seletor no app principal
# - manter possibilidade de retorno ao motor antigo
# ============================================================


def _injetar_css_motor_controlado() -> None:
    st.markdown(
        """
        <style>
            .mc-hero {
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

            .mc-eyebrow {
                color: #d6b56d;
                font-size: 0.78rem;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.35rem;
            }

            .mc-title {
                color: #f4f7fb;
                font-size: 2.1rem;
                font-weight: 900;
                margin-bottom: 0.45rem;
                line-height: 1.14;
            }

            .mc-subtitle {
                color: rgba(244, 247, 251, 0.76);
                font-size: 1rem;
                line-height: 1.62;
                max-width: 1080px;
            }

            .mc-card {
                padding: 1.1rem 1.15rem;
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.035);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.18);
                height: 100%;
            }

            .mc-card-label {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .mc-card-value {
                color: #f4f7fb;
                font-size: 1.22rem;
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .mc-card-note {
                color: rgba(244, 247, 251, 0.68);
                font-size: 0.87rem;
                line-height: 1.47;
            }

            .mc-highlight {
                padding: 0.95rem 1rem;
                border-radius: 16px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.92rem;
                line-height: 1.55;
                margin-bottom: 0.7rem;
            }

            .mc-disclaimer {
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
        <div class="mc-card">
            <div class="mc-card-label">{label}</div>
            <div class="mc-card-value">{value}</div>
            <div class="mc-card-note">{note}</div>
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


def _resultado_para_tabela(resultado: Dict[str, Any], moeda: str) -> List[Dict[str, str]]:
    return [
        {
            "Indicador": "EPS normalizado",
            "Valor": _formatar_moeda(resultado.get("eps_normalizado", 0), moeda),
            "Leitura": "Lucro sustentável por ação.",
        },
        {
            "Indicador": "FCF por ação",
            "Valor": _formatar_moeda(resultado.get("fcf_por_acao", 0), moeda),
            "Leitura": "Fluxo de caixa livre por ação.",
        },
        {
            "Indicador": "Preço justo por EPS",
            "Valor": _formatar_moeda(resultado.get("preco_justo_eps", 0), moeda),
            "Leitura": "Valor estimado via lucro.",
        },
        {
            "Indicador": "Preço justo por FCF",
            "Valor": _formatar_moeda(resultado.get("preco_justo_fcf", 0), moeda),
            "Leitura": "Valor estimado via caixa.",
        },
        {
            "Indicador": "Preço justo combinado",
            "Valor": _formatar_moeda(resultado.get("preco_justo_combinado", 0), moeda),
            "Leitura": "Combinação entre EPS e FCF.",
        },
        {
            "Indicador": "Preço-teto",
            "Valor": _formatar_moeda(resultado.get("preco_teto", 0), moeda),
            "Leitura": "Preço com margem de segurança.",
        },
        {
            "Indicador": "Margem até preço-teto",
            "Valor": _formatar_percentual(resultado.get("margem_ate_preco_teto", 0)),
            "Leitura": "Distância entre preço atual e preço-teto.",
        },
        {
            "Indicador": "Potencial até preço justo",
            "Valor": _formatar_percentual(resultado.get("potencial_ate_preco_justo", 0)),
            "Leitura": "Distância até preço justo estimado.",
        },
        {
            "Indicador": "Status",
            "Valor": str(resultado.get("status", "")),
            "Leitura": "Classificação educacional.",
        },
        {
            "Indicador": "Motor selecionado",
            "Valor": str(resultado.get("motor_selecionado", "")),
            "Leitura": "Motor usado no cálculo.",
        },
    ]


def _gerar_leitura_motor(motor: str, auditoria: Dict[str, Any]) -> str:
    if motor == MOTOR_LEGACY:
        return (
            "O motor Legacy continua sendo o padrão seguro. Ele já é usado pelo app principal "
            "e serve como referência durante a migração."
        )

    if auditoria.get("aprovado"):
        return (
            "O Core Engine foi selecionado e a auditoria paralela está aprovada. "
            "Isso indica que o novo motor pode ser testado de forma controlada."
        )

    return (
        "O Core Engine foi selecionado, mas a auditoria encontrou diferenças críticas. "
        "Não é seguro torná-lo padrão ainda."
    )


def renderizar_painel_motor_controlado() -> None:
    """
    Renderiza o painel interno do Motor Controlado.
    """
    _injetar_css_motor_controlado()

    st.markdown(
        """
        <div class="mc-hero">
            <div class="mc-eyebrow">v3.8.7 — Seletor controlado</div>
            <div class="mc-title">Motor Controlado de Valuation</div>
            <div class="mc-subtitle">
                Escolha de forma segura entre o motor Legacy e o Core Engine.
                Esta tela prepara a troca controlada do motor principal sem destruir o funcionamento atual.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="mc-highlight">
            O objetivo não é trocar o motor no escuro. O objetivo é permitir alternância,
            auditoria paralela e retorno ao motor antigo se algo sair errado.
        </div>
        """,
        unsafe_allow_html=True,
    )

    testes = executar_autoteste_motor_controlado()

    st.markdown("### Diagnóstico do seletor controlado")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Versão", VERSAO_MOTOR_CONTROLADO)

    with col_2:
        st.metric("Autotestes", len(testes))

    with col_3:
        st.metric("Status geral", "OK" if _todos_testes_ok(testes) else "FALHA")

    with col_4:
        st.metric("Motor padrão", obter_motor_padrao())

    if _todos_testes_ok(testes):
        st.success("Motor Controlado passou nos autotestes.")
    else:
        st.error("Motor Controlado apresentou falha nos autotestes.")

    st.divider()

    st.markdown("### Autotestes")

    st.dataframe(
        testes,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    exemplo = gerar_entradas_exemplo_motor_controlado()

    st.markdown("### Simular cálculo com motor selecionado")

    with st.form("form_motor_controlado"):
        col_motor_1, col_motor_2, col_motor_3 = st.columns(3)

        with col_motor_1:
            motor_selecionado = st.selectbox(
                "Motor de valuation",
                obter_motores_disponiveis(),
                index=obter_motores_disponiveis().index(obter_motor_padrao()),
                help="Por segurança, o padrão continua sendo Legacy.",
                key="mc_motor_selecionado",
            )

        with col_motor_2:
            moeda = st.selectbox(
                "Moeda visual",
                ["R$", "US$"],
                index=0,
                key="mc_moeda",
            )

        with col_motor_3:
            tolerancia = st.number_input(
                "Tolerância da auditoria",
                min_value=0.0,
                max_value=1.0,
                value=0.0001,
                step=0.0001,
                format="%.6f",
                key="mc_tolerancia",
            )

        descricao_motor = obter_descricao_motor(motor_selecionado)

        st.info(
            f"""
            **Motor:** {descricao_motor["nome"]}  
            **Descrição:** {descricao_motor["descricao"]}  
            **Uso recomendado:** {descricao_motor["uso_recomendado"]}  
            **Risco:** {descricao_motor["risco"]}
            """
        )

        col_a, col_b = st.columns(2)

        with col_a:
            empresa = st.text_input(
                "Empresa",
                value=exemplo.empresa,
                key="mc_empresa",
            )

            ticker = st.text_input(
                "Ticker",
                value=exemplo.ticker,
                key="mc_ticker",
            )

            lucro_liquido_sustentavel = st.number_input(
                "Lucro líquido sustentável",
                value=float(exemplo.lucro_liquido_sustentavel),
                step=100_000_000.0,
                key="mc_lucro_liquido",
            )

            fluxo_caixa_livre = st.number_input(
                "Fluxo de caixa livre",
                value=float(exemplo.fluxo_caixa_livre),
                step=100_000_000.0,
                key="mc_fcf",
            )

            quantidade_acoes = st.number_input(
                "Quantidade de ações",
                min_value=1.0,
                value=float(exemplo.quantidade_acoes),
                step=10_000_000.0,
                key="mc_quantidade_acoes",
            )

        with col_b:
            preco_atual = st.number_input(
                "Preço atual",
                min_value=0.01,
                value=float(exemplo.preco_atual),
                step=0.5,
                key="mc_preco_atual",
            )

            multiplo_justo_eps = st.number_input(
                "Múltiplo justo EPS",
                min_value=0.0,
                value=float(exemplo.multiplo_justo_eps),
                step=0.5,
                key="mc_multiplo_eps",
            )

            multiplo_justo_fcf = st.number_input(
                "Múltiplo justo FCF",
                min_value=0.0,
                value=float(exemplo.multiplo_justo_fcf),
                step=0.5,
                key="mc_multiplo_fcf",
            )

            peso_eps = st.slider(
                "Peso EPS",
                min_value=0,
                max_value=100,
                value=int(exemplo.peso_eps),
                key="mc_peso_eps",
            )

            peso_fcf = st.slider(
                "Peso FCF",
                min_value=0,
                max_value=100,
                value=int(exemplo.peso_fcf),
                key="mc_peso_fcf",
            )

            margem_seguranca = st.slider(
                "Margem de segurança",
                min_value=0,
                max_value=90,
                value=int(exemplo.margem_seguranca),
                key="mc_margem",
            )

        calcular = st.form_submit_button("Calcular com motor selecionado")

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

            resultado = calcular_valuation_controlado(
                entradas=entradas,
                motor=motor_selecionado,
                moeda=moeda,
            )

            auditoria = auditar_motor_selecionado(
                entradas=entradas,
                moeda=moeda,
                tolerancia=tolerancia,
            )

            st.session_state["resultado_motor_controlado"] = {
                "entradas": entradas,
                "motor": motor_selecionado,
                "moeda": moeda,
                "tolerancia": tolerancia,
                "resultado": resultado,
                "auditoria": auditoria,
                "data": datetime.now().isoformat(timespec="seconds"),
            }

            st.success("Cálculo executado pelo Motor Controlado.")

    resultado_atual = st.session_state.get("resultado_motor_controlado")

    if resultado_atual is None:
        entradas_padrao = gerar_entradas_exemplo_motor_controlado()
        motor_padrao = obter_motor_padrao()

        resultado_padrao = calcular_valuation_controlado(
            entradas=entradas_padrao,
            motor=motor_padrao,
            moeda="R$",
        )

        auditoria_padrao = auditar_motor_selecionado(
            entradas=entradas_padrao,
            moeda="R$",
            tolerancia=0.0001,
        )

        resultado_atual = {
            "entradas": entradas_padrao,
            "motor": motor_padrao,
            "moeda": "R$",
            "tolerancia": 0.0001,
            "resultado": resultado_padrao,
            "auditoria": auditoria_padrao,
            "data": datetime.now().isoformat(timespec="seconds"),
        }

        st.session_state["resultado_motor_controlado"] = resultado_atual

    resultado = resultado_atual["resultado"]
    auditoria = resultado_atual["auditoria"]
    motor = resultado_atual["motor"]
    moeda = resultado_atual["moeda"]

    st.divider()

    st.markdown("### Resultado do motor selecionado")

    col_r1, col_r2, col_r3, col_r4 = st.columns(4)

    with col_r1:
        _card(
            "Motor usado",
            str(resultado.get("motor_selecionado", motor)),
            "Motor escolhido para o cálculo.",
        )

    with col_r2:
        _card(
            "Status",
            str(resultado.get("status", "")),
            "Classificação educacional.",
        )

    with col_r3:
        _card(
            "Preço-teto",
            _formatar_moeda(resultado.get("preco_teto", 0), moeda),
            "Preço com margem de segurança.",
        )

    with col_r4:
        _card(
            "Auditoria paralela",
            "APROVADA" if auditoria.get("aprovado") else "REPROVADA",
            "Comparação Legacy vs Core.",
        )

    if auditoria.get("aprovado"):
        st.success("Auditoria paralela aprovada: Legacy e Core estão compatíveis para esta entrada.")
    else:
        st.error("Auditoria paralela reprovada: existem diferenças críticas.")

    st.info(_gerar_leitura_motor(motor, auditoria))

    st.divider()

    st.markdown("### Resumo técnico do motor usado")

    resumo_motor = gerar_resumo_motor_controlado(
        motor=motor,
        resultado=resultado,
    )

    st.dataframe(
        [{"Campo": chave, "Valor": valor} for chave, valor in resumo_motor.items()],
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Resultado detalhado")

    st.dataframe(
        _resultado_para_tabela(resultado, moeda),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Auditoria paralela Legacy vs Core")

    tabela_auditoria = gerar_tabela_auditoria_motor_controlado(auditoria)

    filtro = st.selectbox(
        "Filtrar campos da auditoria",
        ["Todos", "Apenas diferenças críticas", "Apenas compatíveis"],
        key="mc_filtro_auditoria",
    )

    tabela_filtrada = tabela_auditoria

    if filtro == "Apenas diferenças críticas":
        tabela_filtrada = [
            linha for linha in tabela_auditoria
            if linha.get("Compatível") == "Não"
        ]
    elif filtro == "Apenas compatíveis":
        tabela_filtrada = [
            linha for linha in tabela_auditoria
            if linha.get("Compatível") == "Sim"
        ]

    st.dataframe(
        tabela_filtrada,
        use_container_width=True,
        hide_index=True,
    )

    campos_com_diferenca = auditoria.get("campos_com_diferenca", [])

    if len(campos_com_diferenca) == 0:
        st.success("Nenhuma diferença crítica encontrada.")
    else:
        st.warning("Existem diferenças críticas. Não avance para tornar o Core Engine padrão.")
        st.dataframe(
            campos_com_diferenca,
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    st.markdown("### Resultado bruto")

    col_json_1, col_json_2 = st.columns(2)

    with col_json_1:
        with st.expander("Ver resultado calculado"):
            st.json(resultado)

    with col_json_2:
        with st.expander("Ver auditoria paralela"):
            st.json(auditoria)

    st.divider()

    st.markdown("### Download técnico")

    st.download_button(
        label="Baixar relatório do Motor Controlado (.md)",
        data=gerar_markdown_motor_controlado(
            motor=motor,
            resultado=resultado,
            auditoria=auditoria,
        ),
        file_name="relatorio_motor_controlado.md",
        mime="text/markdown",
        key="download_relatorio_motor_controlado",
    )

    st.markdown(
        """
        <div class="mc-disclaimer">
            <strong>Regra de segurança:</strong> este painel ainda não altera o app principal.
            Ele valida que o seletor de motor funciona. A ligação no fluxo principal será feita
            na próxima etapa, mantendo o Legacy como padrão e o Core Engine como opção controlada.
        </div>
        """,
        unsafe_allow_html=True,
    )