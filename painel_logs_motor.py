# painel_logs_motor.py

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st

from logs_motor_valuation import (
    CAMINHO_LOGS_MOTOR,
    VERSAO_LOGS_MOTOR,
    calcular_valuation_com_log,
    carregar_logs_motor,
    executar_autoteste_logs_motor,
    gerar_entradas_exemplo_logs_motor,
    gerar_markdown_logs_motor,
    gerar_resumo_logs_motor,
    gerar_tabela_resumo_logs_motor,
    inicializar_arquivo_logs_motor,
)
from motor_valuation_controlado import (
    MOTOR_CORE,
    obter_motor_padrao,
    obter_motores_disponiveis,
)
from valuation import EntradasValuation


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v3.8.15 — Painel Visual dos Logs do Motor
# ------------------------------------------------------------
# Esta tela visualiza os logs técnicos do motor de valuation.
#
# Objetivo:
# - acompanhar execuções do motor
# - identificar uso do Core Engine e Legacy
# - detectar fallback automático
# - detectar erros técnicos
# - preparar painel de saúde do motor
# - fortalecer a confiabilidade da migração para Fase 4
# ============================================================


def _injetar_css_logs_motor() -> None:
    st.markdown(
        """
        <style>
            .lm-hero {
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

            .lm-eyebrow {
                color: #d6b56d;
                font-size: 0.78rem;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.35rem;
            }

            .lm-title {
                color: #f4f7fb;
                font-size: 2.1rem;
                font-weight: 900;
                margin-bottom: 0.45rem;
                line-height: 1.14;
            }

            .lm-subtitle {
                color: rgba(244, 247, 251, 0.76);
                font-size: 1rem;
                line-height: 1.62;
                max-width: 1080px;
            }

            .lm-card {
                padding: 1.1rem 1.15rem;
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.035);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.18);
                height: 100%;
            }

            .lm-card-label {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .lm-card-value {
                color: #f4f7fb;
                font-size: 1.18rem;
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .lm-card-note {
                color: rgba(244, 247, 251, 0.68);
                font-size: 0.87rem;
                line-height: 1.47;
            }

            .lm-highlight {
                padding: 0.95rem 1rem;
                border-radius: 16px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.92rem;
                line-height: 1.55;
                margin-bottom: 0.7rem;
            }

            .lm-disclaimer {
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
        <div class="lm-card">
            <div class="lm-card-label">{label}</div>
            <div class="lm-card-value">{value}</div>
            <div class="lm-card-note">{note}</div>
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


def _obter_logs_filtrados(
    logs: List[Dict[str, str]],
    filtro_status: str,
    filtro_fallback: str,
    filtro_motor_executado: str,
) -> List[Dict[str, str]]:
    logs_filtrados = logs

    if filtro_status != "Todos":
        logs_filtrados = [
            log for log in logs_filtrados
            if log.get("status_execucao", "") == filtro_status
        ]

    if filtro_fallback != "Todos":
        valor_fallback = "Sim" if filtro_fallback == "Com fallback" else "Não"
        logs_filtrados = [
            log for log in logs_filtrados
            if log.get("fallback_ocorreu", "") == valor_fallback
        ]

    if filtro_motor_executado != "Todos":
        logs_filtrados = [
            log for log in logs_filtrados
            if log.get("motor_executado", "") == filtro_motor_executado
        ]

    return logs_filtrados


def _gerar_leitura_saude(resumo: Dict[str, Any]) -> str:
    saude = resumo.get("saude", "")

    if saude == "SEM_DADOS":
        return (
            "Ainda não há logs suficientes para avaliar a saúde do motor. "
            "Execute alguns cálculos para começar a construir histórico técnico."
        )

    if saude == "SAUDAVEL":
        return (
            "O motor está saudável: as execuções recentes não mostram erros nem fallbacks. "
            "Esse é o cenário ideal para manter a migração controlada."
        )

    if saude == "ATENCAO_FALLBACKS":
        return (
            "Atenção: houve fallback recente. O app continuou funcionando, mas isso indica que "
            "o Core Engine pode ter falhado em alguma execução e precisa ser observado."
        )

    if saude == "ATENCAO_ERROS":
        return (
            "Atenção crítica: existem execuções com erro. Revise os logs antes de avançar "
            "qualquer migração mais profunda."
        )

    return "Estado técnico não classificado. Revise os logs manualmente."


def _arquivo_logs_existe() -> bool:
    return Path(CAMINHO_LOGS_MOTOR).exists()


def renderizar_painel_logs_motor() -> None:
    """
    Renderiza o painel visual dos logs do motor.
    """
    _injetar_css_logs_motor()

    st.markdown(
        """
        <div class="lm-hero">
            <div class="lm-eyebrow">v3.8.15 — Observabilidade técnica</div>
            <div class="lm-title">Logs do Motor de Valuation</div>
            <div class="lm-subtitle">
                Acompanhe cada execução do motor: Legacy, Core Engine, fallback,
                erros, preço-teto calculado e saúde da migração técnica.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="lm-highlight">
            Produto sério precisa de rastreabilidade. Logs técnicos mostram se o motor está saudável,
            se o Core Engine está sendo usado com segurança e se o fallback está protegendo o app.
        </div>
        """,
        unsafe_allow_html=True,
    )

    testes = executar_autoteste_logs_motor()

    st.markdown("### Diagnóstico dos logs")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Versão logs", VERSAO_LOGS_MOTOR)

    with col_2:
        st.metric("Autotestes", len(testes))

    with col_3:
        st.metric("Status geral", "OK" if _todos_testes_ok(testes) else "FALHA")

    with col_4:
        st.metric("Arquivo", "Criado" if _arquivo_logs_existe() else "Ainda não criado")

    if _todos_testes_ok(testes):
        st.success("Sistema de logs passou nos autotestes.")
    else:
        st.error("Sistema de logs encontrou falha nos autotestes.")

    st.divider()

    st.markdown("### Autotestes")

    st.dataframe(
        testes,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    exemplo = gerar_entradas_exemplo_logs_motor()

    st.markdown("### Executar cálculo e registrar log")

    with st.form("form_logs_motor"):
        col_config_1, col_config_2, col_config_3 = st.columns(3)

        with col_config_1:
            motor_preferido = st.selectbox(
                "Motor preferido",
                obter_motores_disponiveis(),
                index=obter_motores_disponiveis().index(obter_motor_padrao()),
                help="Motor que será tentado primeiro.",
                key="lm_motor_preferido",
            )

        with col_config_2:
            moeda = st.selectbox(
                "Moeda visual",
                ["R$", "US$"],
                index=0,
                key="lm_moeda",
            )

        with col_config_3:
            permitir_fallback = st.checkbox(
                "Permitir fallback",
                value=True,
                help="Se o Core Engine falhar, tenta Legacy.",
                key="lm_permitir_fallback",
            )

        simular_falha_core = st.checkbox(
            "Simular falha no Core Engine",
            value=False,
            help="Útil para testar log de fallback ou erro.",
            key="lm_simular_falha_core",
        )

        if simular_falha_core and motor_preferido != MOTOR_CORE:
            st.warning(
                "A simulação de falha só afeta o Core Engine. Para testar fallback, selecione Core Engine."
            )

        col_a, col_b = st.columns(2)

        with col_a:
            empresa = st.text_input(
                "Empresa",
                value=exemplo.empresa,
                key="lm_empresa",
            )

            ticker = st.text_input(
                "Ticker",
                value=exemplo.ticker,
                key="lm_ticker",
            )

            lucro_liquido_sustentavel = st.number_input(
                "Lucro líquido sustentável",
                value=float(exemplo.lucro_liquido_sustentavel),
                step=100_000_000.0,
                key="lm_lucro_liquido",
            )

            fluxo_caixa_livre = st.number_input(
                "Fluxo de caixa livre",
                value=float(exemplo.fluxo_caixa_livre),
                step=100_000_000.0,
                key="lm_fcf",
            )

            quantidade_acoes = st.number_input(
                "Quantidade de ações",
                min_value=1.0,
                value=float(exemplo.quantidade_acoes),
                step=10_000_000.0,
                key="lm_quantidade_acoes",
            )

        with col_b:
            preco_atual = st.number_input(
                "Preço atual",
                min_value=0.01,
                value=float(exemplo.preco_atual),
                step=0.5,
                key="lm_preco_atual",
            )

            multiplo_justo_eps = st.number_input(
                "Múltiplo justo EPS",
                min_value=0.0,
                value=float(exemplo.multiplo_justo_eps),
                step=0.5,
                key="lm_multiplo_eps",
            )

            multiplo_justo_fcf = st.number_input(
                "Múltiplo justo FCF",
                min_value=0.0,
                value=float(exemplo.multiplo_justo_fcf),
                step=0.5,
                key="lm_multiplo_fcf",
            )

            peso_eps = st.slider(
                "Peso EPS",
                min_value=0,
                max_value=100,
                value=int(exemplo.peso_eps),
                key="lm_peso_eps",
            )

            peso_fcf = st.slider(
                "Peso FCF",
                min_value=0,
                max_value=100,
                value=int(exemplo.peso_fcf),
                key="lm_peso_fcf",
            )

            margem_seguranca = st.slider(
                "Margem de segurança",
                min_value=0,
                max_value=90,
                value=int(exemplo.margem_seguranca),
                key="lm_margem",
            )

        registrar = st.form_submit_button("Calcular e registrar log")

        if registrar:
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
                resultado = calcular_valuation_com_log(
                    entradas=entradas,
                    motor_preferido=motor_preferido,
                    moeda=moeda,
                    permitir_fallback=permitir_fallback,
                    origem="painel_logs_motor",
                    contexto="simulacao_manual",
                    caminho_log=CAMINHO_LOGS_MOTOR,
                    forcar_falha_core=simular_falha_core,
                )

                st.session_state["resultado_logs_motor"] = {
                    "resultado": resultado,
                    "moeda": moeda,
                    "data": datetime.now().isoformat(timespec="seconds"),
                }

                if resultado.get("fallback_ocorreu"):
                    st.warning("Cálculo registrado com fallback para Legacy.")
                else:
                    st.success("Cálculo registrado com sucesso.")

            except RuntimeError as erro:
                st.session_state["resultado_logs_motor"] = {
                    "resultado": None,
                    "erro": str(erro),
                    "moeda": moeda,
                    "data": datetime.now().isoformat(timespec="seconds"),
                }
                st.error(str(erro))

    st.divider()

    logs = carregar_logs_motor(
        caminho=CAMINHO_LOGS_MOTOR,
        limite=300,
    )

    resumo_logs = gerar_resumo_logs_motor(logs)

    st.markdown("### Saúde do motor")

    col_s1, col_s2, col_s3, col_s4 = st.columns(4)

    with col_s1:
        _card(
            "Total de logs",
            str(resumo_logs.get("total_logs", 0)),
            "Execuções recentes carregadas.",
        )

    with col_s2:
        _card(
            "Execuções OK",
            str(resumo_logs.get("execucoes_ok", 0)),
            "Cálculos concluídos.",
        )

    with col_s3:
        _card(
            "Fallbacks",
            str(resumo_logs.get("fallbacks", 0)),
            "Retornos automáticos para Legacy.",
        )

    with col_s4:
        _card(
            "Saúde",
            str(resumo_logs.get("saude", "")),
            "Diagnóstico técnico.",
        )

    st.info(_gerar_leitura_saude(resumo_logs))

    st.divider()

    st.markdown("### Resumo dos logs")

    st.dataframe(
        gerar_tabela_resumo_logs_motor(logs),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Último resultado registrado nesta tela")

    resultado_atual = st.session_state.get("resultado_logs_motor")

    if resultado_atual is None:
        st.info("Nenhum cálculo foi registrado nesta sessão ainda.")
    else:
        resultado = resultado_atual.get("resultado")
        erro = resultado_atual.get("erro", "")
        moeda_resultado = resultado_atual.get("moeda", "R$")

        if resultado is None:
            st.error("A última execução desta sessão terminou com erro.")
            st.code(erro, language="text")
        else:
            col_r1, col_r2, col_r3, col_r4 = st.columns(4)

            with col_r1:
                st.metric(
                    "Status",
                    str(resultado.get("status", "")),
                )

            with col_r2:
                st.metric(
                    "Preço-teto",
                    _formatar_moeda(resultado.get("preco_teto", 0), moeda_resultado),
                )

            with col_r3:
                st.metric(
                    "Motor executado",
                    str(resultado.get("motor_executado", "")),
                )

            with col_r4:
                st.metric(
                    "Fallback",
                    "Sim" if resultado.get("fallback_ocorreu") else "Não",
                )

            st.caption(f"ID do log: {resultado.get('id_log_motor', '')}")

    st.divider()

    st.markdown("### Logs recentes")

    if len(logs) == 0:
        st.info("Nenhum log registrado ainda.")
    else:
        col_f1, col_f2, col_f3 = st.columns(3)

        with col_f1:
            filtro_status = st.selectbox(
                "Filtrar por status de execução",
                ["Todos", "OK", "ERRO"],
                key="lm_filtro_status",
            )

        with col_f2:
            filtro_fallback = st.selectbox(
                "Filtrar por fallback",
                ["Todos", "Com fallback", "Sem fallback"],
                key="lm_filtro_fallback",
            )

        with col_f3:
            filtro_motor_executado = st.selectbox(
                "Filtrar por motor executado",
                ["Todos", "Legacy", "Core Engine"],
                key="lm_filtro_motor_executado",
            )

        logs_filtrados = _obter_logs_filtrados(
            logs=logs,
            filtro_status=filtro_status,
            filtro_fallback=filtro_fallback,
            filtro_motor_executado=filtro_motor_executado,
        )

        st.dataframe(
            logs_filtrados,
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    st.markdown("### Downloads técnicos")

    col_d1, col_d2 = st.columns(2)

    with col_d1:
        st.download_button(
            label="Baixar relatório dos logs (.md)",
            data=gerar_markdown_logs_motor(logs),
            file_name="relatorio_logs_motor.md",
            mime="text/markdown",
            key="download_relatorio_logs_motor",
        )

    with col_d2:
        if Path(CAMINHO_LOGS_MOTOR).exists():
            with Path(CAMINHO_LOGS_MOTOR).open("rb") as arquivo_logs:
                st.download_button(
                    label="Baixar logs brutos (.csv)",
                    data=arquivo_logs,
                    file_name="logs_motor_valuation.csv",
                    mime="text/csv",
                    key="download_logs_motor_csv",
                )
        else:
            st.button(
                "Baixar logs brutos (.csv)",
                disabled=True,
                key="download_logs_motor_csv_disabled",
            )

    st.markdown(
        """
        <div class="lm-disclaimer">
            <strong>Regra de segurança:</strong> este painel ainda não altera o fluxo principal.
            Ele apenas visualiza e testa logs. Na próxima etapa, o app principal passará a registrar
            automaticamente cada valuation real feito pelo usuário.
        </div>
        """,
        unsafe_allow_html=True,
    )