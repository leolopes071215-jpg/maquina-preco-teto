# painel_promocao_core.py

from pathlib import Path
from typing import Any, Dict, List

import streamlit as st

from logs_motor_valuation import (
    CAMINHO_LOGS_MOTOR,
    carregar_logs_motor,
)
from promocao_core_engine import (
    VERSAO_PROMOCAO_CORE_ENGINE,
    ESTADO_PROMOCAO_SEM_DADOS,
    ESTADO_PROMOCAO_BLOQUEADA,
    ESTADO_PROMOCAO_OBSERVACAO,
    ESTADO_PROMOCAO_TESTE_INTERNO,
    ESTADO_PROMOCAO_APTA_COM_CONTROLES,
    MOTOR_LEGACY,
    MOTOR_CORE,
    EXPOSICAO_NENHUMA,
    EXPOSICAO_FUNDADOR,
    EXPOSICAO_CONTROLADA,
    analisar_promocao_core_engine_por_arquivo,
    executar_autoteste_promocao_core_engine,
    gerar_markdown_promocao_core_engine,
    gerar_plano_execucao_promocao_core,
    gerar_tabela_resumo_promocao_core,
)
from decisao_core_engine import VERSAO_DECISAO_CORE_ENGINE
from saude_motor_valuation import VERSAO_SAUDE_MOTOR


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v3.8.22 — Painel Visual de Promoção Controlada do Core Engine
# ------------------------------------------------------------
# Esta tela transforma decisão técnica em governança operacional.
#
# Objetivo:
# - mostrar se o Core Engine pode virar padrão
# - impedir promoção insegura
# - exigir fallback e rollback
# - mostrar bloqueios técnicos
# - orientar plano de execução
# - preparar uma migração profissional Legacy -> Core
# ============================================================


def _injetar_css_promocao_core() -> None:
    st.markdown(
        """
        <style>
            .pc-hero {
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

            .pc-eyebrow {
                color: #d6b56d;
                font-size: 0.78rem;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.35rem;
            }

            .pc-title {
                color: #f4f7fb;
                font-size: 2.1rem;
                font-weight: 900;
                margin-bottom: 0.45rem;
                line-height: 1.14;
            }

            .pc-subtitle {
                color: rgba(244, 247, 251, 0.76);
                font-size: 1rem;
                line-height: 1.62;
                max-width: 1080px;
            }

            .pc-card {
                padding: 1.1rem 1.15rem;
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.035);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.18);
                height: 100%;
            }

            .pc-card-label {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .pc-card-value {
                color: #f4f7fb;
                font-size: 1.18rem;
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .pc-card-note {
                color: rgba(244, 247, 251, 0.68);
                font-size: 0.87rem;
                line-height: 1.47;
            }

            .pc-highlight {
                padding: 0.95rem 1rem;
                border-radius: 16px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.92rem;
                line-height: 1.55;
                margin-bottom: 0.7rem;
            }

            .pc-disclaimer {
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
        <div class="pc-card">
            <div class="pc-card-label">{label}</div>
            <div class="pc-card-value">{value}</div>
            <div class="pc-card-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _todos_testes_ok(testes: List[Dict[str, str]]) -> bool:
    return all(teste.get("status") == "OK" for teste in testes)


def _arquivo_logs_existe() -> bool:
    return Path(CAMINHO_LOGS_MOTOR).exists()


def _safe_float(valor: Any, default: float = 0.0) -> float:
    try:
        return float(valor)
    except (TypeError, ValueError):
        return default


def _formatar_percentual(valor: Any) -> str:
    return f"{_safe_float(valor):.2f}%"


def _bool_texto(valor: Any) -> str:
    return "Sim" if bool(valor) else "Não"


def _leitura_estado_promocao(estado: str) -> str:
    if estado == ESTADO_PROMOCAO_SEM_DADOS:
        return "Ainda não há dados suficientes para promoção."

    if estado == ESTADO_PROMOCAO_BLOQUEADA:
        return "Promoção bloqueada. Legacy deve continuar como padrão."

    if estado == ESTADO_PROMOCAO_OBSERVACAO:
        return "Core em observação. Continue coletando logs."

    if estado == ESTADO_PROMOCAO_TESTE_INTERNO:
        return "Core pode ser mais usado no Modo Fundador."

    if estado == ESTADO_PROMOCAO_APTA_COM_CONTROLES:
        return "Core apto apenas com fallback, rollback e escopo controlado."

    return "Estado não classificado."


def _leitura_motor_recomendado(motor: str) -> str:
    if motor == MOTOR_CORE:
        return "Core pode ser preparado para virar padrão em versão controlada."

    if motor == MOTOR_LEGACY:
        return "Legacy deve permanecer como motor padrão seguro."

    return "Motor não classificado."


def _leitura_exposicao(exposicao: str) -> str:
    if exposicao == EXPOSICAO_NENHUMA:
        return "Core não deve ser exposto."

    if exposicao == EXPOSICAO_FUNDADOR:
        return "Core apenas para testes internos no Modo Fundador."

    if exposicao == EXPOSICAO_CONTROLADA:
        return "Core pode avançar em escopo limitado e monitorado."

    return "Exposição não classificada."


def _renderizar_alerta_promocao(configuracao: Dict[str, Any], bloqueios: List[Dict[str, str]]) -> None:
    estado = str(configuracao.get("estado_promocao", ""))
    pode_promover = bool(configuracao.get("pode_promover_core", False))
    motor_recomendado = str(configuracao.get("motor_padrao_recomendado", ""))

    if estado == ESTADO_PROMOCAO_APTA_COM_CONTROLES and pode_promover:
        st.success(
            "Promoção potencialmente possível: o Core Engine pode ser preparado para virar padrão "
            "em uma versão controlada, com fallback obrigatório para Legacy e rollback planejado."
        )
        return

    if estado == ESTADO_PROMOCAO_TESTE_INTERNO:
        st.info(
            "Core Engine pode ser testado com mais frequência no Modo Fundador, "
            "mas Legacy ainda deve continuar como padrão."
        )
        return

    if estado == ESTADO_PROMOCAO_OBSERVACAO:
        st.warning(
            "Core Engine ainda está em observação. Continue gerando logs reais antes de promover."
        )
        return

    if estado == ESTADO_PROMOCAO_SEM_DADOS:
        st.info(
            "Sem dados suficientes. Gere mais logs com Legacy e Core antes de qualquer decisão."
        )
        return

    if motor_recomendado == MOTOR_LEGACY:
        st.error(
            f"Promoção bloqueada. Bloqueios encontrados: {len(bloqueios)}. "
            "Legacy deve permanecer como padrão."
        )
        return

    st.warning("Estado de promoção não classificado. Revise o diagnóstico bruto.")


def _filtrar_bloqueios(
    bloqueios: List[Dict[str, str]],
    filtro: str,
) -> List[Dict[str, str]]:
    if filtro == "Todos":
        return bloqueios

    termo = filtro.lower()

    return [
        bloqueio for bloqueio in bloqueios
        if termo in bloqueio.get("Bloqueio", "").lower()
        or termo in bloqueio.get("Detalhe", "").lower()
    ]


def _filtrar_plano(
    plano: List[Dict[str, str]],
    filtro_acao: str,
) -> List[Dict[str, str]]:
    if filtro_acao == "Todas":
        return plano

    termo = filtro_acao.lower()

    return [
        item for item in plano
        if termo in item.get("Ação", "").lower()
        or termo in item.get("Detalhe", "").lower()
    ]


def _filtrar_logs_promocao(
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


def renderizar_painel_promocao_core() -> None:
    """
    Renderiza o painel visual de promoção controlada do Core Engine.
    """
    _injetar_css_promocao_core()

    st.markdown(
        """
        <div class="pc-hero">
            <div class="pc-eyebrow">v3.8.22 — Promoção controlada</div>
            <div class="pc-title">Promoção do Core Engine</div>
            <div class="pc-subtitle">
                Transforme decisão técnica em política operacional:
                Core como padrão, Legacy como proteção, fallback obrigatório,
                rollback planejado e exposição controlada.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="pc-highlight">
            Esta tela não promove o Core automaticamente. Ela responde se a promoção é segura,
            quais controles são obrigatórios e quais bloqueios precisam ser resolvidos antes da mudança.
        </div>
        """,
        unsafe_allow_html=True,
    )

    testes = executar_autoteste_promocao_core_engine()

    st.markdown("### Diagnóstico do módulo de promoção")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Versão promoção", VERSAO_PROMOCAO_CORE_ENGINE)

    with col_2:
        st.metric("Versão decisão", VERSAO_DECISAO_CORE_ENGINE)

    with col_3:
        st.metric("Versão saúde", VERSAO_SAUDE_MOTOR)

    with col_4:
        st.metric("Arquivo de logs", "Encontrado" if _arquivo_logs_existe() else "Ausente")

    if _todos_testes_ok(testes):
        st.success("Módulo de Promoção Core passou nos autotestes.")
    else:
        st.error("Módulo de Promoção Core encontrou falha nos autotestes.")

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
            help="A política de promoção considera os logs mais recentes.",
            key="pc_limite_logs",
        )

    with col_cfg_2:
        atualizar = st.button(
            "Atualizar promoção",
            key="pc_atualizar_promocao",
        )

    if atualizar:
        st.session_state["promocao_core_atualizada"] = True
        st.success("Análise de promoção atualizada.")

    promocao = analisar_promocao_core_engine_por_arquivo(
        caminho_logs=CAMINHO_LOGS_MOTOR,
        limite=limite_logs,
    )

    configuracao = promocao.get("configuracao", {})
    bloqueios = promocao.get("bloqueios", [])
    decisao_core = promocao.get("decisao_core", {})
    analise_saude = decisao_core.get("analise_saude", {})
    metricas = analise_saude.get("metricas", {})

    estado_promocao = str(configuracao.get("estado_promocao", ""))
    motor_recomendado = str(configuracao.get("motor_padrao_recomendado", ""))
    nivel_exposicao = str(configuracao.get("nivel_exposicao", ""))
    pode_promover = bool(configuracao.get("pode_promover_core", False))

    st.divider()

    st.markdown("### Decisão de promoção")

    col_p1, col_p2, col_p3, col_p4 = st.columns(4)

    with col_p1:
        _card(
            "Estado da promoção",
            estado_promocao,
            _leitura_estado_promocao(estado_promocao),
        )

    with col_p2:
        _card(
            "Motor recomendado",
            motor_recomendado,
            _leitura_motor_recomendado(motor_recomendado),
        )

    with col_p3:
        _card(
            "Pode promover Core?",
            "SIM" if pode_promover else "NÃO",
            "Decisão final com controles técnicos.",
        )

    with col_p4:
        _card(
            "Exposição",
            nivel_exposicao,
            _leitura_exposicao(nivel_exposicao),
        )

    _renderizar_alerta_promocao(
        configuracao=configuracao,
        bloqueios=bloqueios,
    )

    st.info(promocao.get("leitura", ""))

    st.divider()

    st.markdown("### Controles obrigatórios")

    col_c1, col_c2, col_c3, col_c4 = st.columns(4)

    with col_c1:
        st.metric(
            "Fallback obrigatório",
            _bool_texto(configuracao.get("fallback_obrigatorio", False)),
        )

    with col_c2:
        st.metric(
            "Rollback obrigatório",
            _bool_texto(configuracao.get("rollback_obrigatorio", False)),
        )

    with col_c3:
        st.metric(
            "Monitorar logs",
            _bool_texto(configuracao.get("exige_monitoramento_logs", False)),
        )

    with col_c4:
        st.metric(
            "Versão controlada",
            _bool_texto(configuracao.get("exige_versao_controlada", False)),
        )

    col_c5, col_c6, col_c7 = st.columns(3)

    with col_c5:
        st.metric(
            "Core no Fundador",
            _bool_texto(configuracao.get("core_liberado_modo_fundador", False)),
        )

    with col_c6:
        st.metric(
            "Core no Usuário Beta",
            _bool_texto(configuracao.get("core_liberado_usuario_beta", False)),
        )

    with col_c7:
        st.metric(
            "Core no Investidor Completo",
            _bool_texto(configuracao.get("core_liberado_investidor_completo", False)),
        )

    st.warning(configuracao.get("justificativa", ""))

    st.divider()

    st.markdown("### Base técnica da promoção")

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)

    with col_m1:
        st.metric("Decisão técnica", decisao_core.get("decisao", ""))

    with col_m2:
        st.metric("Risco técnico", decisao_core.get("risco", ""))

    with col_m3:
        st.metric("Score saúde", f"{analise_saude.get('score_saude', 0)}/100")

    with col_m4:
        st.metric("Logs analisados", metricas.get("total_logs", 0))

    col_m5, col_m6, col_m7, col_m8 = st.columns(4)

    with col_m5:
        st.metric("Erros", metricas.get("execucoes_erro", 0))

    with col_m6:
        st.metric("Fallbacks", metricas.get("fallbacks", 0))

    with col_m7:
        st.metric("Core executado", metricas.get("core_executado", 0))

    with col_m8:
        st.metric("Taxa Core executado", _formatar_percentual(metricas.get("taxa_core_executado", 0)))

    st.markdown("#### Resumo da política de promoção")

    st.dataframe(
        gerar_tabela_resumo_promocao_core(promocao),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Bloqueios da promoção")

    if len(bloqueios) == 0:
        st.success("Nenhum bloqueio crítico encontrado para promoção controlada.")
    else:
        filtro_bloqueios = st.selectbox(
            "Filtrar bloqueios",
            [
                "Todos",
                "amostra",
                "core",
                "erro",
                "fallback",
                "risco",
                "decisão",
                "condição",
            ],
            key="pc_filtro_bloqueios",
        )

        bloqueios_filtrados = _filtrar_bloqueios(
            bloqueios=bloqueios,
            filtro=filtro_bloqueios,
        )

        st.dataframe(
            bloqueios_filtrados,
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    st.markdown("### Plano de execução")

    plano = gerar_plano_execucao_promocao_core(promocao)

    filtro_plano = st.selectbox(
        "Filtrar plano",
        ["Todas", "core", "legacy", "logs", "rollback", "fallback", "bloqueios"],
        key="pc_filtro_plano",
    )

    plano_filtrado = _filtrar_plano(
        plano=plano,
        filtro_acao=filtro_plano,
    )

    st.dataframe(
        plano_filtrado,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Logs usados na promoção")

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
                key="pc_filtro_status_execucao",
            )

        with col_f2:
            filtro_fallback = st.selectbox(
                "Fallback",
                ["Todos", "Com fallback", "Sem fallback"],
                key="pc_filtro_fallback",
            )

        with col_f3:
            filtro_motor = st.selectbox(
                "Motor executado",
                ["Todos", "Legacy", "Core Engine"],
                key="pc_filtro_motor_executado",
            )

        logs_filtrados = _filtrar_logs_promocao(
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

    with st.expander("Ver JSON da promoção"):
        st.json(promocao)

    st.divider()

    st.markdown("### Download técnico")

    st.download_button(
        label="Baixar relatório de promoção do Core (.md)",
        data=gerar_markdown_promocao_core_engine(promocao),
        file_name="relatorio_promocao_core_engine.md",
        mime="text/markdown",
        key="download_relatorio_promocao_core",
    )

    st.markdown(
        """
        <div class="pc-disclaimer">
            <strong>Regra de governança:</strong> este painel ainda não altera automaticamente o motor padrão.
            Ele cria a política de promoção. A mudança real do padrão deve acontecer em uma versão separada,
            com fallback ativo, rollback possível, logs monitorados e escopo controlado.
        </div>
        """,
        unsafe_allow_html=True,
    )