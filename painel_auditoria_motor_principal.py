# painel_auditoria_motor_principal.py

from datetime import datetime
from typing import Any, Dict, List

import streamlit as st

from auditoria_motor_principal import (
    VERSAO_AUDITORIA_MOTOR_PRINCIPAL,
    executar_auditoria_motor_principal,
    executar_autoteste_auditoria_motor_principal,
    executar_bateria_auditoria_motor_principal,
    gerar_entradas_exemplo_auditoria_motor_principal,
    gerar_markdown_auditoria_motor_principal,
    gerar_markdown_bateria_motor_principal,
    gerar_tabela_bateria_motor_principal,
    gerar_tabela_detalhada_comparacao_motor_principal,
    gerar_tabela_resumo_auditoria_motor_principal,
)
from motor_valuation_controlado import (
    MOTOR_CORE,
    MOTOR_LEGACY,
    obter_motor_padrao,
    obter_motores_disponiveis,
)
from valuation import EntradasValuation


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v3.8.10 — Painel de Auditoria do Motor Principal
# ------------------------------------------------------------
# Esta tela visualiza a auditoria pós-integração do Motor Controlado
# ao fluxo principal do app.
#
# Objetivo:
# - auditar Legacy e Core Engine no fluxo principal
# - visualizar segurança da integração
# - rodar bateria de cenários
# - detectar diferenças críticas
# - preparar decisão futura sobre tornar Core Engine padrão
# ============================================================


def _injetar_css_auditoria_motor() -> None:
    st.markdown(
        """
        <style>
            .amp-hero {
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

            .amp-eyebrow {
                color: #d6b56d;
                font-size: 0.78rem;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.35rem;
            }

            .amp-title {
                color: #f4f7fb;
                font-size: 2.1rem;
                font-weight: 900;
                margin-bottom: 0.45rem;
                line-height: 1.14;
            }

            .amp-subtitle {
                color: rgba(244, 247, 251, 0.76);
                font-size: 1rem;
                line-height: 1.62;
                max-width: 1080px;
            }

            .amp-card {
                padding: 1.1rem 1.15rem;
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.035);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.18);
                height: 100%;
            }

            .amp-card-label {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .amp-card-value {
                color: #f4f7fb;
                font-size: 1.18rem;
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .amp-card-note {
                color: rgba(244, 247, 251, 0.68);
                font-size: 0.87rem;
                line-height: 1.47;
            }

            .amp-highlight {
                padding: 0.95rem 1rem;
                border-radius: 16px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.92rem;
                line-height: 1.55;
                margin-bottom: 0.7rem;
            }

            .amp-disclaimer {
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
        <div class="amp-card">
            <div class="amp-card-label">{label}</div>
            <div class="amp-card-value">{value}</div>
            <div class="amp-card-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _safe_float(valor: Any, default: float = 0.0) -> float:
    try:
        return float(valor)
    except (TypeError, ValueError):
        return default


def _formatar_moeda(valor: Any, moeda: str = "R$") -> str:
    numero = _safe_float(valor)
    return f"{moeda} {numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _formatar_percentual(valor: Any) -> str:
    numero = _safe_float(valor)
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


def _gerar_leitura_decisao(auditoria: Dict[str, Any]) -> str:
    classificacao = auditoria.get("classificacao_seguranca", "")

    if classificacao == "SEGURO_LEGACY_CORE_COMPATIVEL":
        return (
            "Estado excelente para migração gradual: o fluxo principal está seguro com Legacy, "
            "e o Core Engine continua compatível na auditoria paralela."
        )

    if classificacao == "CORE_CONTROLADO_APROVADO":
        return (
            "Core Engine está ativo de forma controlada e aprovado. Pode continuar em testes internos, "
            "mas ainda não precisa ser tornado padrão para todos."
        )

    if classificacao == "CORE_NAO_SEGURO":
        return (
            "Alerta: Core Engine ativo com diferenças críticas. Volte para Legacy e investigue antes de avançar."
        )

    if classificacao == "SEGURO_LEGACY_COM_ALERTA_CORE":
        return (
            "O app segue seguro porque Legacy está ativo, mas o Core apresentou divergências. "
            "Não avance para Core como padrão."
        )

    return (
        "A classificação exige revisão técnica. Use Legacy como padrão até confirmar a integridade do fluxo."
    )


def _resultado_principal_para_tabela(auditoria: Dict[str, Any]) -> List[Dict[str, str]]:
    resultado = auditoria.get("resultado_principal", {})
    moeda = auditoria.get("moeda", "R$")

    return [
        {
            "Indicador": "Motor selecionado",
            "Valor": str(auditoria.get("motor_selecionado", "")),
            "Leitura": "Motor usado no cálculo principal.",
        },
        {
            "Indicador": "Status",
            "Valor": str(resultado.get("status", "")),
            "Leitura": "Classificação educacional calculada.",
        },
        {
            "Indicador": "Preço atual",
            "Valor": _formatar_moeda(resultado.get("preco_atual", 0), moeda),
            "Leitura": "Preço informado no cálculo.",
        },
        {
            "Indicador": "Preço-teto",
            "Valor": _formatar_moeda(resultado.get("preco_teto", 0), moeda),
            "Leitura": "Preço com margem de segurança.",
        },
        {
            "Indicador": "Preço justo combinado",
            "Valor": _formatar_moeda(resultado.get("preco_justo_combinado", 0), moeda),
            "Leitura": "Valor justo estimado pelo motor.",
        },
        {
            "Indicador": "Margem até preço-teto",
            "Valor": _formatar_percentual(resultado.get("margem_ate_preco_teto", 0)),
            "Leitura": "Distância entre preço atual e preço-teto.",
        },
        {
            "Indicador": "Potencial até preço justo",
            "Valor": _formatar_percentual(resultado.get("potencial_ate_preco_justo", 0)),
            "Leitura": "Distância até preço justo.",
        },
        {
            "Indicador": "Classificação de segurança",
            "Valor": str(auditoria.get("classificacao_seguranca", "")),
            "Leitura": "Diagnóstico técnico da integração.",
        },
    ]


def renderizar_painel_auditoria_motor_principal() -> None:
    """
    Renderiza o painel de auditoria pós-integração do motor principal.
    """
    _injetar_css_auditoria_motor()

    st.markdown(
        """
        <div class="amp-hero">
            <div class="amp-eyebrow">v3.8.10 — Auditoria pós-integração</div>
            <div class="amp-title">Auditoria do Motor Principal</div>
            <div class="amp-subtitle">
                Valide se o fluxo principal do app está seguro após a integração do Motor Controlado.
                Esta tela verifica Legacy, Core Engine, auditoria paralela e bateria de cenários.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="amp-highlight">
            Esta é uma camada de segurança antes de qualquer decisão maior.
            O Core Engine só deve virar padrão depois que a bateria de auditorias permanecer aprovada.
        </div>
        """,
        unsafe_allow_html=True,
    )

    testes = executar_autoteste_auditoria_motor_principal()

    st.markdown("### Diagnóstico da auditoria")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Versão auditoria", VERSAO_AUDITORIA_MOTOR_PRINCIPAL)

    with col_2:
        st.metric("Autotestes", len(testes))

    with col_3:
        st.metric("Status geral", "OK" if _todos_testes_ok(testes) else "FALHA")

    with col_4:
        st.metric("Motor padrão", obter_motor_padrao())

    if _todos_testes_ok(testes):
        st.success("Auditoria do Motor Principal passou nos autotestes.")
    else:
        st.error("Auditoria do Motor Principal encontrou falha nos autotestes.")

    st.divider()

    st.markdown("### Autotestes")

    st.dataframe(
        testes,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    exemplo = gerar_entradas_exemplo_auditoria_motor_principal()

    st.markdown("### Auditar entrada manual")

    with st.form("form_auditoria_motor_principal"):
        col_config_1, col_config_2, col_config_3 = st.columns(3)

        with col_config_1:
            motor_selecionado = st.selectbox(
                "Motor principal simulado",
                obter_motores_disponiveis(),
                index=obter_motores_disponiveis().index(obter_motor_padrao()),
                help="Simula qual motor será usado no fluxo principal.",
                key="amp_motor_selecionado",
            )

        with col_config_2:
            moeda = st.selectbox(
                "Moeda visual",
                ["R$", "US$"],
                index=0,
                key="amp_moeda",
            )

        with col_config_3:
            tolerancia = st.number_input(
                "Tolerância da auditoria",
                min_value=0.0,
                max_value=1.0,
                value=0.0001,
                step=0.0001,
                format="%.6f",
                key="amp_tolerancia",
            )

        col_a, col_b = st.columns(2)

        with col_a:
            empresa = st.text_input(
                "Empresa",
                value=exemplo.empresa,
                key="amp_empresa",
            )

            ticker = st.text_input(
                "Ticker",
                value=exemplo.ticker,
                key="amp_ticker",
            )

            lucro_liquido_sustentavel = st.number_input(
                "Lucro líquido sustentável",
                value=float(exemplo.lucro_liquido_sustentavel),
                step=100_000_000.0,
                key="amp_lucro_liquido",
            )

            fluxo_caixa_livre = st.number_input(
                "Fluxo de caixa livre",
                value=float(exemplo.fluxo_caixa_livre),
                step=100_000_000.0,
                key="amp_fcf",
            )

            quantidade_acoes = st.number_input(
                "Quantidade de ações",
                min_value=1.0,
                value=float(exemplo.quantidade_acoes),
                step=10_000_000.0,
                key="amp_quantidade_acoes",
            )

        with col_b:
            preco_atual = st.number_input(
                "Preço atual",
                min_value=0.01,
                value=float(exemplo.preco_atual),
                step=0.5,
                key="amp_preco_atual",
            )

            multiplo_justo_eps = st.number_input(
                "Múltiplo justo EPS",
                min_value=0.0,
                value=float(exemplo.multiplo_justo_eps),
                step=0.5,
                key="amp_multiplo_eps",
            )

            multiplo_justo_fcf = st.number_input(
                "Múltiplo justo FCF",
                min_value=0.0,
                value=float(exemplo.multiplo_justo_fcf),
                step=0.5,
                key="amp_multiplo_fcf",
            )

            peso_eps = st.slider(
                "Peso EPS",
                min_value=0,
                max_value=100,
                value=int(exemplo.peso_eps),
                key="amp_peso_eps",
            )

            peso_fcf = st.slider(
                "Peso FCF",
                min_value=0,
                max_value=100,
                value=int(exemplo.peso_fcf),
                key="amp_peso_fcf",
            )

            margem_seguranca = st.slider(
                "Margem de segurança",
                min_value=0,
                max_value=90,
                value=int(exemplo.margem_seguranca),
                key="amp_margem",
            )

        auditar = st.form_submit_button("Executar auditoria da entrada")

        if auditar:
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

            auditoria = executar_auditoria_motor_principal(
                entradas=entradas,
                motor_selecionado=motor_selecionado,
                moeda=moeda,
                tolerancia=tolerancia,
            )

            st.session_state["resultado_auditoria_motor_principal"] = {
                "entradas": entradas,
                "auditoria": auditoria,
                "moeda": moeda,
                "tolerancia": tolerancia,
                "data": datetime.now().isoformat(timespec="seconds"),
            }

            if auditoria.get("aprovado_para_teste_core"):
                st.success("Auditoria executada. Fluxo aprovado para teste controlado.")
            else:
                st.error("Auditoria executada. Existem restrições antes de avançar.")

    resultado_atual = st.session_state.get("resultado_auditoria_motor_principal")

    if resultado_atual is None:
        entradas_padrao = gerar_entradas_exemplo_auditoria_motor_principal()

        auditoria_padrao = executar_auditoria_motor_principal(
            entradas=entradas_padrao,
            motor_selecionado=obter_motor_padrao(),
            moeda="R$",
            tolerancia=0.0001,
        )

        resultado_atual = {
            "entradas": entradas_padrao,
            "auditoria": auditoria_padrao,
            "moeda": "R$",
            "tolerancia": 0.0001,
            "data": datetime.now().isoformat(timespec="seconds"),
        }

        st.session_state["resultado_auditoria_motor_principal"] = resultado_atual

    auditoria_atual = resultado_atual["auditoria"]
    resultado_principal = auditoria_atual.get("resultado_principal", {})
    auditoria_paralela = auditoria_atual.get("auditoria_paralela", {})
    moeda_atual = auditoria_atual.get("moeda", "R$")

    st.divider()

    st.markdown("### Resultado da auditoria atual")

    col_r1, col_r2, col_r3, col_r4 = st.columns(4)

    with col_r1:
        _card(
            "Motor simulado",
            str(auditoria_atual.get("motor_selecionado", "")),
            "Motor usado no fluxo principal.",
        )

    with col_r2:
        _card(
            "Status valuation",
            str(resultado_principal.get("status", "")),
            "Resultado educacional.",
        )

    with col_r3:
        _card(
            "Preço-teto",
            _formatar_moeda(resultado_principal.get("preco_teto", 0), moeda_atual),
            "Preço com margem de segurança.",
        )

    with col_r4:
        _card(
            "Auditoria paralela",
            "APROVADA" if auditoria_paralela.get("aprovado") else "REPROVADA",
            "Comparação Legacy vs Core.",
        )

    classificacao = str(auditoria_atual.get("classificacao_seguranca", ""))

    if auditoria_atual.get("aprovado_para_teste_core"):
        st.success(f"Classificação: {classificacao}")
    else:
        st.error(f"Classificação: {classificacao}")

    st.info(auditoria_atual.get("leitura_seguranca", ""))
    st.info(_gerar_leitura_decisao(auditoria_atual))

    st.divider()

    st.markdown("### Resumo da auditoria")

    st.dataframe(
        gerar_tabela_resumo_auditoria_motor_principal(auditoria_atual),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Resultado principal detalhado")

    st.dataframe(
        _resultado_principal_para_tabela(auditoria_atual),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Comparação Legacy vs Core")

    tabela_detalhada = gerar_tabela_detalhada_comparacao_motor_principal(auditoria_atual)

    filtro = st.selectbox(
        "Filtrar comparação",
        ["Todos", "Apenas diferenças críticas", "Apenas compatíveis"],
        key="amp_filtro_comparacao",
    )

    tabela_filtrada = tabela_detalhada

    if filtro == "Apenas diferenças críticas":
        tabela_filtrada = [
            linha for linha in tabela_detalhada
            if linha.get("Compatível") == "Não"
        ]
    elif filtro == "Apenas compatíveis":
        tabela_filtrada = [
            linha for linha in tabela_detalhada
            if linha.get("Compatível") == "Sim"
        ]

    st.dataframe(
        tabela_filtrada,
        use_container_width=True,
        hide_index=True,
    )

    campos_com_diferenca = auditoria_atual.get("campos_com_diferenca", [])

    if len(campos_com_diferenca) == 0:
        st.success("Nenhuma diferença crítica encontrada na entrada atual.")
    else:
        st.warning("Existem diferenças críticas na entrada atual.")
        st.dataframe(
            campos_com_diferenca,
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    st.markdown("### Bateria de cenários")

    bateria = executar_bateria_auditoria_motor_principal(
        moeda=moeda_atual,
        tolerancia=float(resultado_atual.get("tolerancia", 0.0001)),
    )

    col_b1, col_b2, col_b3, col_b4 = st.columns(4)

    with col_b1:
        st.metric("Execuções", bateria.get("total_execucoes", 0))

    with col_b2:
        st.metric("Aprovadas p/ teste Core", bateria.get("aprovados_para_teste_core", 0))

    with col_b3:
        st.metric("Aprovadas p/ Core padrão", bateria.get("aprovados_para_core_padrao", 0))

    with col_b4:
        st.metric("Diferenças críticas", bateria.get("execucoes_com_diferenca", 0))

    if bateria.get("bateria_aprovada"):
        st.success("Bateria aprovada: nenhum cenário apresentou diferença crítica.")
    else:
        st.error("Bateria reprovada: existem cenários com diferença crítica.")

    st.dataframe(
        gerar_tabela_bateria_motor_principal(bateria),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Resultado bruto")

    col_json_1, col_json_2 = st.columns(2)

    with col_json_1:
        with st.expander("Ver resultado principal bruto"):
            st.json(resultado_principal)

    with col_json_2:
        with st.expander("Ver auditoria paralela bruta"):
            st.json(auditoria_paralela)

    st.divider()

    st.markdown("### Downloads técnicos")

    col_d1, col_d2 = st.columns(2)

    with col_d1:
        st.download_button(
            label="Baixar auditoria da entrada (.md)",
            data=gerar_markdown_auditoria_motor_principal(auditoria_atual),
            file_name="auditoria_motor_principal.md",
            mime="text/markdown",
            key="download_auditoria_motor_principal",
        )

    with col_d2:
        st.download_button(
            label="Baixar bateria de cenários (.md)",
            data=gerar_markdown_bateria_motor_principal(bateria),
            file_name="bateria_motor_principal.md",
            mime="text/markdown",
            key="download_bateria_motor_principal",
        )

    st.markdown(
        """
        <div class="amp-disclaimer">
            <strong>Regra de segurança:</strong> esta auditoria não torna o Core Engine padrão.
            Ela apenas valida se a integração do Motor Controlado ao app principal está saudável.
            A decisão de tornar o Core padrão deve ser feita em uma versão futura e com fallback.
        </div>
        """,
        unsafe_allow_html=True,
    )