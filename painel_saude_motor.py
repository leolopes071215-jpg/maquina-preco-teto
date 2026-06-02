# painel_saude_motor.py

from pathlib import Path
from typing import Any, Dict, List

import streamlit as st

from logs_motor_valuation import (
    CAMINHO_LOGS_MOTOR,
    carregar_logs_motor,
)
from saude_motor_valuation import (
    VERSAO_SAUDE_MOTOR,
    STATUS_SAUDE_SAUDAVEL,
    STATUS_SAUDE_OBSERVACAO,
    STATUS_SAUDE_ATENCAO,
    STATUS_SAUDE_CRITICO,
    STATUS_SAUDE_SEM_DADOS,
    PRONTIDAO_CORE_PADRAO,
    PRONTIDAO_TESTE_CONTROLADO,
    PRONTIDAO_EM_OBSERVACAO,
    PRONTIDAO_NAO_PRONTO,
    PRONTIDAO_SEM_DADOS,
    analisar_saude_motor_por_arquivo,
    executar_autoteste_saude_motor,
    gerar_markdown_saude_motor,
    gerar_tabela_metricas_saude_motor,
)


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v3.8.18 — Painel Visual de Saúde Técnica do Motor
# ------------------------------------------------------------
# Esta tela transforma logs técnicos em diagnóstico executivo.
#
# Objetivo:
# - mostrar score de saúde do motor
# - mostrar taxa de erro e fallback
# - acompanhar uso de Legacy e Core Engine
# - avaliar prontidão do Core Engine para virar padrão
# - gerar checklist técnico de decisão
# - preparar governança técnica da Fase 4
# ============================================================


def _injetar_css_saude_motor() -> None:
    st.markdown(
        """
        <style>
            .sm-hero {
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

            .sm-eyebrow {
                color: #d6b56d;
                font-size: 0.78rem;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.35rem;
            }

            .sm-title {
                color: #f4f7fb;
                font-size: 2.1rem;
                font-weight: 900;
                margin-bottom: 0.45rem;
                line-height: 1.14;
            }

            .sm-subtitle {
                color: rgba(244, 247, 251, 0.76);
                font-size: 1rem;
                line-height: 1.62;
                max-width: 1080px;
            }

            .sm-card {
                padding: 1.1rem 1.15rem;
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.035);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.18);
                height: 100%;
            }

            .sm-card-label {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .sm-card-value {
                color: #f4f7fb;
                font-size: 1.18rem;
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .sm-card-note {
                color: rgba(244, 247, 251, 0.68);
                font-size: 0.87rem;
                line-height: 1.47;
            }

            .sm-highlight {
                padding: 0.95rem 1rem;
                border-radius: 16px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.92rem;
                line-height: 1.55;
                margin-bottom: 0.7rem;
            }

            .sm-disclaimer {
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
        <div class="sm-card">
            <div class="sm-card-label">{label}</div>
            <div class="sm-card-value">{value}</div>
            <div class="sm-card-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _todos_testes_ok(testes: List[Dict[str, str]]) -> bool:
    return all(teste.get("status") == "OK" for teste in testes)


def _safe_float(valor: Any, default: float = 0.0) -> float:
    try:
        return float(valor)
    except (TypeError, ValueError):
        return default


def _formatar_percentual(valor: Any) -> str:
    return f"{_safe_float(valor):.2f}%"


def _arquivo_logs_existe() -> bool:
    return Path(CAMINHO_LOGS_MOTOR).exists()


def _gerar_leitura_status(status_saude: str) -> str:
    if status_saude == STATUS_SAUDE_SEM_DADOS:
        return "Sem dados suficientes. O app ainda precisa registrar mais cálculos reais."

    if status_saude == STATUS_SAUDE_SAUDAVEL:
        return "Saudável. O motor está operando sem sinais relevantes de instabilidade."

    if status_saude == STATUS_SAUDE_OBSERVACAO:
        return "Em observação. O motor está funcionando, mas ainda precisa de mais histórico técnico."

    if status_saude == STATUS_SAUDE_ATENCAO:
        return "Atenção. Existem sinais que exigem cautela antes de avançar a migração."

    if status_saude == STATUS_SAUDE_CRITICO:
        return "Crítico. Não avance a migração do Core Engine antes de investigar os logs."

    return "Status não classificado. Revise as métricas manualmente."


def _gerar_leitura_prontidao(prontidao_core: str) -> str:
    if prontidao_core == PRONTIDAO_SEM_DADOS:
        return "Ainda não há dados suficientes para avaliar o Core Engine."

    if prontidao_core == PRONTIDAO_NAO_PRONTO:
        return "Core Engine ainda não está pronto para virar padrão."

    if prontidao_core == PRONTIDAO_EM_OBSERVACAO:
        return "Core Engine deve continuar em observação e teste controlado."

    if prontidao_core == PRONTIDAO_TESTE_CONTROLADO:
        return "Core Engine já pode ser testado com mais frequência no Modo Fundador."

    if prontidao_core == PRONTIDAO_CORE_PADRAO:
        return "Core Engine está potencialmente pronto para virar padrão, mas ainda exige decisão humana."

    return "Prontidão não classificada."


def _filtrar_checklist(
    checklist: List[Dict[str, str]],
    filtro_status: str,
) -> List[Dict[str, str]]:
    if filtro_status == "Todos":
        return checklist

    return [
        item for item in checklist
        if item.get("Status", "") == filtro_status
    ]


def _filtrar_logs_saude(
    logs: List[Dict[str, str]],
    filtro_status_execucao: str,
    filtro_fallback: str,
    filtro_motor: str,
) -> List[Dict[str, str]]:
    filtrados = logs

    if filtro_status_execucao != "Todos":
        filtrados = [
            log for log in filtrados
            if log.get("status_execucao", "") == filtro_status_execucao
        ]

    if filtro_fallback != "Todos":
        valor = "Sim" if filtro_fallback == "Com fallback" else "Não"
        filtrados = [
            log for log in filtrados
            if log.get("fallback_ocorreu", "") == valor
        ]

    if filtro_motor != "Todos":
        filtrados = [
            log for log in filtrados
            if log.get("motor_executado", "") == filtro_motor
        ]

    return filtrados


def renderizar_painel_saude_motor() -> None:
    """
    Renderiza o painel visual de saúde técnica do motor.
    """
    _injetar_css_saude_motor()

    st.markdown(
        """
        <div class="sm-hero">
            <div class="sm-eyebrow">v3.8.18 — Saúde técnica</div>
            <div class="sm-title">Saúde do Motor de Valuation</div>
            <div class="sm-subtitle">
                Transforme logs técnicos em decisão estratégica: estabilidade, taxa de erro,
                fallback, uso do Core Engine e prontidão para migração segura.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="sm-highlight">
            A migração do motor não deve ser feita por entusiasmo. Deve ser feita por evidência.
            Este painel mostra se o Core Engine está tecnicamente maduro para avançar.
        </div>
        """,
        unsafe_allow_html=True,
    )

    testes = executar_autoteste_saude_motor()

    st.markdown("### Diagnóstico do módulo de saúde")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Versão saúde", VERSAO_SAUDE_MOTOR)

    with col_2:
        st.metric("Autotestes", len(testes))

    with col_3:
        st.metric("Status geral", "OK" if _todos_testes_ok(testes) else "FALHA")

    with col_4:
        st.metric("Arquivo de logs", "Encontrado" if _arquivo_logs_existe() else "Ausente")

    if _todos_testes_ok(testes):
        st.success("Módulo de Saúde do Motor passou nos autotestes.")
    else:
        st.error("Módulo de Saúde do Motor encontrou falha nos autotestes.")

    st.divider()

    with st.expander("Ver autotestes"):
        st.dataframe(
            testes,
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    st.markdown("### Configuração da análise")

    col_cfg_1, col_cfg_2 = st.columns(2)

    with col_cfg_1:
        limite_logs = st.slider(
            "Quantidade de logs analisados",
            min_value=10,
            max_value=1000,
            value=300,
            step=10,
            help="A análise considera os logs mais recentes.",
            key="sm_limite_logs",
        )

    with col_cfg_2:
        atualizar = st.button(
            "Atualizar análise de saúde",
            key="sm_atualizar_analise",
        )

    if atualizar:
        st.session_state["saude_motor_atualizada"] = True
        st.success("Análise atualizada.")

    analise = analisar_saude_motor_por_arquivo(
        caminho_logs=CAMINHO_LOGS_MOTOR,
        limite=limite_logs,
    )

    metricas = analise.get("metricas", {})
    score = int(analise.get("score_saude", 0))
    status_saude = str(analise.get("status_saude", ""))
    prontidao_core = str(analise.get("prontidao_core", ""))

    st.divider()

    st.markdown("### Visão executiva")

    col_s1, col_s2, col_s3, col_s4 = st.columns(4)

    with col_s1:
        _card(
            "Score técnico",
            f"{score}/100",
            "Quanto maior, mais estável.",
        )

    with col_s2:
        _card(
            "Saúde geral",
            status_saude,
            _gerar_leitura_status(status_saude),
        )

    with col_s3:
        _card(
            "Prontidão Core",
            prontidao_core,
            _gerar_leitura_prontidao(prontidao_core),
        )

    with col_s4:
        _card(
            "Logs analisados",
            str(metricas.get("total_logs", 0)),
            "Amostra técnica recente.",
        )

    st.markdown("#### Barra de score")

    st.progress(score)

    if status_saude == STATUS_SAUDE_SAUDAVEL:
        st.success(analise.get("leitura", ""))
    elif status_saude in [STATUS_SAUDE_OBSERVACAO, STATUS_SAUDE_ATENCAO]:
        st.warning(analise.get("leitura", ""))
    elif status_saude == STATUS_SAUDE_CRITICO:
        st.error(analise.get("leitura", ""))
    else:
        st.info(analise.get("leitura", ""))

    st.divider()

    st.markdown("### Métricas principais")

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)

    with col_m1:
        st.metric("Execuções OK", metricas.get("execucoes_ok", 0))

    with col_m2:
        st.metric("Erros", metricas.get("execucoes_erro", 0))

    with col_m3:
        st.metric("Fallbacks", metricas.get("fallbacks", 0))

    with col_m4:
        st.metric("Core executado", metricas.get("core_executado", 0))

    col_m5, col_m6, col_m7, col_m8 = st.columns(4)

    with col_m5:
        st.metric("Taxa de erro", _formatar_percentual(metricas.get("taxa_erro", 0)))

    with col_m6:
        st.metric("Taxa de fallback", _formatar_percentual(metricas.get("taxa_fallback", 0)))

    with col_m7:
        st.metric("Taxa Core executado", _formatar_percentual(metricas.get("taxa_core_executado", 0)))

    with col_m8:
        st.metric("Legacy executado", metricas.get("legacy_executado", 0))

    st.dataframe(
        gerar_tabela_metricas_saude_motor(analise),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Checklist técnico de decisão")

    checklist = analise.get("checklist", [])

    filtro_checklist = st.selectbox(
        "Filtrar checklist",
        ["Todos", "OK", "OBSERVAR", "ATENÇÃO", "FALHA", "NÃO"],
        key="sm_filtro_checklist",
    )

    checklist_filtrado = _filtrar_checklist(
        checklist=checklist,
        filtro_status=filtro_checklist,
    )

    st.dataframe(
        checklist_filtrado,
        use_container_width=True,
        hide_index=True,
    )

    if prontidao_core == PRONTIDAO_CORE_PADRAO:
        st.success(
            "Leitura: o Core Engine está potencialmente pronto para virar padrão. "
            "Mesmo assim, faça a mudança em uma versão controlada e com fallback ativo."
        )
    elif prontidao_core == PRONTIDAO_TESTE_CONTROLADO:
        st.info(
            "Leitura: o Core Engine pode ser usado com mais frequência em testes internos, "
            "mas ainda não deve virar padrão para todos."
        )
    elif prontidao_core == PRONTIDAO_NAO_PRONTO:
        st.error(
            "Leitura: o Core Engine não deve virar padrão. Existem erros, fallbacks ou instabilidade."
        )
    else:
        st.warning(
            "Leitura: continue coletando logs e testando o Core Engine no Modo Fundador."
        )

    st.divider()

    st.markdown("### Logs usados na análise")

    logs = carregar_logs_motor(
        caminho=CAMINHO_LOGS_MOTOR,
        limite=limite_logs,
    )

    if len(logs) == 0:
        st.info("Nenhum log encontrado para exibir.")
    else:
        col_f1, col_f2, col_f3 = st.columns(3)

        with col_f1:
            filtro_status_execucao = st.selectbox(
                "Status execução",
                ["Todos", "OK", "ERRO"],
                key="sm_filtro_status_execucao",
            )

        with col_f2:
            filtro_fallback = st.selectbox(
                "Fallback",
                ["Todos", "Com fallback", "Sem fallback"],
                key="sm_filtro_fallback",
            )

        with col_f3:
            filtro_motor = st.selectbox(
                "Motor executado",
                ["Todos", "Legacy", "Core Engine"],
                key="sm_filtro_motor_executado",
            )

        logs_filtrados = _filtrar_logs_saude(
            logs=logs,
            filtro_status_execucao=filtro_status_execucao,
            filtro_fallback=filtro_fallback,
            filtro_motor=filtro_motor,
        )

        st.dataframe(
            logs_filtrados,
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    st.markdown("### Diagnóstico bruto")

    with st.expander("Ver JSON da análise de saúde"):
        st.json(analise)

    st.divider()

    st.markdown("### Download técnico")

    st.download_button(
        label="Baixar relatório de saúde do motor (.md)",
        data=gerar_markdown_saude_motor(analise),
        file_name="relatorio_saude_motor.md",
        mime="text/markdown",
        key="download_relatorio_saude_motor",
    )

    st.markdown(
        """
        <div class="sm-disclaimer">
            <strong>Regra de governança:</strong> este painel não muda automaticamente o motor padrão.
            Ele apenas fornece evidência. A decisão de tornar o Core Engine padrão deve ser feita
            em uma versão específica, com rollback e fallback ativo.
        </div>
        """,
        unsafe_allow_html=True,
    )