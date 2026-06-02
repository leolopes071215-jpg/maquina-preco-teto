# painel_fallback_motor.py

from datetime import datetime
from typing import Any, Dict, List

import streamlit as st

from fallback_motor_valuation import (
    VERSAO_FALLBACK_MOTOR,
    calcular_valuation_com_fallback,
    executar_autoteste_fallback_motor,
    gerar_entradas_exemplo_fallback,
    gerar_markdown_fallback_motor,
    gerar_tabela_resumo_fallback,
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
# v3.8.12 — Painel Visual do Fallback Motor
# ------------------------------------------------------------
# Esta tela audita o fallback seguro do motor principal.
#
# Objetivo:
# - testar cálculo com Legacy
# - testar cálculo com Core Engine
# - simular falha do Core Engine
# - validar fallback automático para Legacy
# - impedir quebra do app durante migração futura
# - gerar relatório técnico do mecanismo de fallback
# ============================================================


def _injetar_css_fallback_motor() -> None:
    st.markdown(
        """
        <style>
            .fm-hero {
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

            .fm-eyebrow {
                color: #d6b56d;
                font-size: 0.78rem;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.35rem;
            }

            .fm-title {
                color: #f4f7fb;
                font-size: 2.1rem;
                font-weight: 900;
                margin-bottom: 0.45rem;
                line-height: 1.14;
            }

            .fm-subtitle {
                color: rgba(244, 247, 251, 0.76);
                font-size: 1rem;
                line-height: 1.62;
                max-width: 1080px;
            }

            .fm-card {
                padding: 1.1rem 1.15rem;
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.035);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.18);
                height: 100%;
            }

            .fm-card-label {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .fm-card-value {
                color: #f4f7fb;
                font-size: 1.18rem;
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .fm-card-note {
                color: rgba(244, 247, 251, 0.68);
                font-size: 0.87rem;
                line-height: 1.47;
            }

            .fm-highlight {
                padding: 0.95rem 1rem;
                border-radius: 16px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.92rem;
                line-height: 1.55;
                margin-bottom: 0.7rem;
            }

            .fm-disclaimer {
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
        <div class="fm-card">
            <div class="fm-card-label">{label}</div>
            <div class="fm-card-value">{value}</div>
            <div class="fm-card-note">{note}</div>
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


def _resultado_para_tabela(resultado: Dict[str, Any], moeda: str) -> List[Dict[str, str]]:
    return [
        {
            "Indicador": "Status valuation",
            "Valor": str(resultado.get("status", "")),
            "Leitura": "Classificação educacional calculada.",
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
            "Leitura": "Distância até preço justo estimado.",
        },
        {
            "Indicador": "Motor preferido",
            "Valor": str(resultado.get("motor_preferido", "")),
            "Leitura": "Motor que o sistema tentou usar primeiro.",
        },
        {
            "Indicador": "Motor executado",
            "Valor": str(resultado.get("motor_executado", "")),
            "Leitura": "Motor que efetivamente calculou o valuation.",
        },
        {
            "Indicador": "Fallback ocorreu",
            "Valor": "Sim" if resultado.get("fallback_ocorreu") else "Não",
            "Leitura": "Indica se houve retorno automático para Legacy.",
        },
        {
            "Indicador": "Status fallback",
            "Valor": str(resultado.get("status_fallback", "")),
            "Leitura": "Estado técnico do fallback.",
        },
        {
            "Indicador": "Erro motor preferido",
            "Valor": str(resultado.get("erro_motor_preferido", "")),
            "Leitura": "Erro capturado no motor preferido, caso exista.",
        },
    ]


def _gerar_leitura_fallback(resultado: Dict[str, Any]) -> str:
    if resultado.get("fallback_ocorreu"):
        return (
            "O fallback funcionou corretamente: o motor preferido falhou e o sistema voltou "
            "automaticamente para Legacy, evitando quebra do app."
        )

    if resultado.get("motor_preferido") == MOTOR_CORE:
        return (
            "O Core Engine calculou normalmente. Nenhum fallback foi necessário nesta execução."
        )

    return (
        "O Legacy calculou normalmente. Nenhum fallback foi necessário, e o sistema permaneceu "
        "no motor padrão seguro."
    )


def renderizar_painel_fallback_motor() -> None:
    """
    Renderiza o painel visual do Fallback Motor.
    """
    _injetar_css_fallback_motor()

    st.markdown(
        """
        <div class="fm-hero">
            <div class="fm-eyebrow">v3.8.12 — Fallback seguro</div>
            <div class="fm-title">Fallback do Motor Principal</div>
            <div class="fm-subtitle">
                Teste a resiliência do valuation: se o Core Engine falhar,
                o sistema deve retornar automaticamente para o Legacy e manter o app funcionando.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="fm-highlight">
            O fallback é uma camada de proteção. Ele permite testar o Core Engine com mais segurança,
            porque uma falha inesperada não deve derrubar o produto.
        </div>
        """,
        unsafe_allow_html=True,
    )

    testes = executar_autoteste_fallback_motor()

    st.markdown("### Diagnóstico do fallback")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Versão fallback", VERSAO_FALLBACK_MOTOR)

    with col_2:
        st.metric("Autotestes", len(testes))

    with col_3:
        st.metric("Status geral", "OK" if _todos_testes_ok(testes) else "FALHA")

    with col_4:
        st.metric("Motor padrão", obter_motor_padrao())

    if _todos_testes_ok(testes):
        st.success("Fallback Motor passou nos autotestes.")
    else:
        st.error("Fallback Motor encontrou falha nos autotestes.")

    st.divider()

    st.markdown("### Autotestes")

    st.dataframe(
        testes,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    exemplo = gerar_entradas_exemplo_fallback()

    st.markdown("### Simular cálculo com fallback")

    with st.form("form_fallback_motor"):
        col_config_1, col_config_2, col_config_3 = st.columns(3)

        with col_config_1:
            motor_preferido = st.selectbox(
                "Motor preferido",
                obter_motores_disponiveis(),
                index=obter_motores_disponiveis().index(obter_motor_padrao()),
                help="Motor que o sistema tentará usar primeiro.",
                key="fm_motor_preferido",
            )

        with col_config_2:
            moeda = st.selectbox(
                "Moeda visual",
                ["R$", "US$"],
                index=0,
                key="fm_moeda",
            )

        with col_config_3:
            permitir_fallback = st.checkbox(
                "Permitir fallback automático",
                value=True,
                help="Quando ativo, se o Core Engine falhar, o sistema tenta Legacy.",
                key="fm_permitir_fallback",
            )

        simular_falha_core = st.checkbox(
            "Simular falha no Core Engine",
            value=False,
            help="Usado para testar se o retorno automático para Legacy funciona.",
            key="fm_simular_falha_core",
        )

        if simular_falha_core and motor_preferido != MOTOR_CORE:
            st.warning(
                "A simulação de falha só afeta o Core Engine. Para testar fallback real, selecione Core Engine como motor preferido."
            )

        col_a, col_b = st.columns(2)

        with col_a:
            empresa = st.text_input(
                "Empresa",
                value=exemplo.empresa,
                key="fm_empresa",
            )

            ticker = st.text_input(
                "Ticker",
                value=exemplo.ticker,
                key="fm_ticker",
            )

            lucro_liquido_sustentavel = st.number_input(
                "Lucro líquido sustentável",
                value=float(exemplo.lucro_liquido_sustentavel),
                step=100_000_000.0,
                key="fm_lucro_liquido",
            )

            fluxo_caixa_livre = st.number_input(
                "Fluxo de caixa livre",
                value=float(exemplo.fluxo_caixa_livre),
                step=100_000_000.0,
                key="fm_fcf",
            )

            quantidade_acoes = st.number_input(
                "Quantidade de ações",
                min_value=1.0,
                value=float(exemplo.quantidade_acoes),
                step=10_000_000.0,
                key="fm_quantidade_acoes",
            )

        with col_b:
            preco_atual = st.number_input(
                "Preço atual",
                min_value=0.01,
                value=float(exemplo.preco_atual),
                step=0.5,
                key="fm_preco_atual",
            )

            multiplo_justo_eps = st.number_input(
                "Múltiplo justo EPS",
                min_value=0.0,
                value=float(exemplo.multiplo_justo_eps),
                step=0.5,
                key="fm_multiplo_eps",
            )

            multiplo_justo_fcf = st.number_input(
                "Múltiplo justo FCF",
                min_value=0.0,
                value=float(exemplo.multiplo_justo_fcf),
                step=0.5,
                key="fm_multiplo_fcf",
            )

            peso_eps = st.slider(
                "Peso EPS",
                min_value=0,
                max_value=100,
                value=int(exemplo.peso_eps),
                key="fm_peso_eps",
            )

            peso_fcf = st.slider(
                "Peso FCF",
                min_value=0,
                max_value=100,
                value=int(exemplo.peso_fcf),
                key="fm_peso_fcf",
            )

            margem_seguranca = st.slider(
                "Margem de segurança",
                min_value=0,
                max_value=90,
                value=int(exemplo.margem_seguranca),
                key="fm_margem",
            )

        calcular = st.form_submit_button("Executar cálculo com fallback")

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

            try:
                resultado = calcular_valuation_com_fallback(
                    entradas=entradas,
                    motor_preferido=motor_preferido,
                    moeda=moeda,
                    permitir_fallback=permitir_fallback,
                    forcar_falha_core=simular_falha_core,
                )

                st.session_state["resultado_fallback_motor"] = {
                    "entradas": entradas,
                    "resultado": resultado,
                    "moeda": moeda,
                    "data": datetime.now().isoformat(timespec="seconds"),
                }

                if resultado.get("fallback_ocorreu"):
                    st.warning("Cálculo concluído com fallback automático para Legacy.")
                else:
                    st.success("Cálculo concluído sem necessidade de fallback.")

            except RuntimeError as erro:
                st.session_state["resultado_fallback_motor"] = {
                    "entradas": entradas,
                    "resultado": None,
                    "erro": str(erro),
                    "moeda": moeda,
                    "data": datetime.now().isoformat(timespec="seconds"),
                }
                st.error(str(erro))

    resultado_atual = st.session_state.get("resultado_fallback_motor")

    if resultado_atual is None:
        entradas_padrao = gerar_entradas_exemplo_fallback()

        resultado_padrao = calcular_valuation_com_fallback(
            entradas=entradas_padrao,
            motor_preferido=obter_motor_padrao(),
            moeda="R$",
            permitir_fallback=True,
            forcar_falha_core=False,
        )

        resultado_atual = {
            "entradas": entradas_padrao,
            "resultado": resultado_padrao,
            "moeda": "R$",
            "data": datetime.now().isoformat(timespec="seconds"),
        }

        st.session_state["resultado_fallback_motor"] = resultado_atual

    resultado = resultado_atual.get("resultado")
    erro = resultado_atual.get("erro", "")
    moeda_atual = resultado_atual.get("moeda", "R$")

    st.divider()

    st.markdown("### Resultado do fallback")

    if resultado is None:
        st.error("A última execução terminou com erro.")
        st.code(erro, language="text")
        return

    col_r1, col_r2, col_r3, col_r4 = st.columns(4)

    with col_r1:
        _card(
            "Motor preferido",
            str(resultado.get("motor_preferido", "")),
            "Primeira tentativa.",
        )

    with col_r2:
        _card(
            "Motor executado",
            str(resultado.get("motor_executado", "")),
            "Motor que calculou de fato.",
        )

    with col_r3:
        _card(
            "Fallback",
            "SIM" if resultado.get("fallback_ocorreu") else "NÃO",
            str(resultado.get("status_fallback", "")),
        )

    with col_r4:
        _card(
            "Preço-teto",
            _formatar_moeda(resultado.get("preco_teto", 0), moeda_atual),
            "Resultado final entregue.",
        )

    if resultado.get("fallback_ocorreu"):
        st.warning("Fallback executado: o sistema retornou para Legacy.")
    else:
        st.success("Nenhum fallback foi necessário.")

    st.info(_gerar_leitura_fallback(resultado))

    st.divider()

    st.markdown("### Resumo técnico")

    st.dataframe(
        gerar_tabela_resumo_fallback(resultado),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Resultado detalhado")

    st.dataframe(
        _resultado_para_tabela(resultado, moeda_atual),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Erro capturado")

    erro_motor = str(resultado.get("erro_motor_preferido", "")).strip()

    if erro_motor == "":
        st.success("Nenhum erro capturado no motor preferido.")
    else:
        st.warning("Erro capturado no motor preferido:")
        st.code(erro_motor, language="text")

    st.divider()

    st.markdown("### Resultado bruto")

    with st.expander("Ver JSON bruto do fallback"):
        st.json(resultado)

    st.divider()

    st.markdown("### Download técnico")

    st.download_button(
        label="Baixar relatório de fallback (.md)",
        data=gerar_markdown_fallback_motor(resultado),
        file_name="relatorio_fallback_motor.md",
        mime="text/markdown",
        key="download_relatorio_fallback_motor",
    )

    st.markdown(
        """
        <div class="fm-disclaimer">
            <strong>Regra de segurança:</strong> este painel ainda não liga o fallback no fluxo principal.
            Ele apenas valida o mecanismo. Na próxima etapa, o app principal poderá usar cálculo com fallback,
            mantendo Legacy como proteção caso o Core Engine falhe.
        </div>
        """,
        unsafe_allow_html=True,
    )