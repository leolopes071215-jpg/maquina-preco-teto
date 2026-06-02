# painel_decisao_core.py

from pathlib import Path
from typing import Any, Dict, List

import streamlit as st

from decisao_core_engine import (
    VERSAO_DECISAO_CORE_ENGINE,
    DECISAO_SEM_DADOS,
    DECISAO_MANTER_LEGACY,
    DECISAO_CONTINUAR_TESTE_CONTROLADO,
    DECISAO_AUMENTAR_TESTES_CORE,
    DECISAO_CORE_PODE_SER_PROMOVIDO_COM_FALLBACK,
    DECISAO_NAO_PROMOVER_CORE,
    RISCO_BAIXO,
    RISCO_MODERADO,
    RISCO_ALTO,
    RISCO_CRITICO,
    RISCO_INDEFINIDO,
    analisar_decisao_core_engine_por_arquivo,
    executar_autoteste_decisao_core_engine,
    gerar_markdown_decisao_core_engine,
    gerar_tabela_resumo_decisao_core,
)
from logs_motor_valuation import (
    CAMINHO_LOGS_MOTOR,
    carregar_logs_motor,
)
from saude_motor_valuation import VERSAO_SAUDE_MOTOR


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v3.8.20 — Painel Visual de Decisão Controlada do Core Engine
# ------------------------------------------------------------
# Esta tela transforma logs + saúde técnica em decisão operacional.
#
# Objetivo:
# - decidir se o Core Engine pode avançar
# - manter Legacy como proteção quando houver risco
# - mostrar risco técnico da migração
# - listar condições para promoção do Core
# - gerar plano de ação objetivo
# - impedir promoção emocional e sem evidência
# ============================================================


def _injetar_css_decisao_core() -> None:
    st.markdown(
        """
        <style>
            .dc-hero {
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

            .dc-eyebrow {
                color: #d6b56d;
                font-size: 0.78rem;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.35rem;
            }

            .dc-title {
                color: #f4f7fb;
                font-size: 2.1rem;
                font-weight: 900;
                margin-bottom: 0.45rem;
                line-height: 1.14;
            }

            .dc-subtitle {
                color: rgba(244, 247, 251, 0.76);
                font-size: 1rem;
                line-height: 1.62;
                max-width: 1080px;
            }

            .dc-card {
                padding: 1.1rem 1.15rem;
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.035);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.18);
                height: 100%;
            }

            .dc-card-label {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .dc-card-value {
                color: #f4f7fb;
                font-size: 1.18rem;
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .dc-card-note {
                color: rgba(244, 247, 251, 0.68);
                font-size: 0.87rem;
                line-height: 1.47;
            }

            .dc-highlight {
                padding: 0.95rem 1rem;
                border-radius: 16px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.92rem;
                line-height: 1.55;
                margin-bottom: 0.7rem;
            }

            .dc-disclaimer {
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
        <div class="dc-card">
            <div class="dc-card-label">{label}</div>
            <div class="dc-card-value">{value}</div>
            <div class="dc-card-note">{note}</div>
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


def _leitura_decisao(decisao: str) -> str:
    if decisao == DECISAO_SEM_DADOS:
        return "Ainda não há base técnica suficiente. Continue gerando logs reais."

    if decisao == DECISAO_MANTER_LEGACY:
        return "Legacy deve continuar como motor padrão. Core apenas em teste interno."

    if decisao == DECISAO_CONTINUAR_TESTE_CONTROLADO:
        return "Core pode continuar em teste controlado, sem virar padrão."

    if decisao == DECISAO_AUMENTAR_TESTES_CORE:
        return "Core pode ser usado com mais frequência no Modo Fundador."

    if decisao == DECISAO_CORE_PODE_SER_PROMOVIDO_COM_FALLBACK:
        return "Core pode ser preparado para promoção controlada, com fallback e rollback."

    if decisao == DECISAO_NAO_PROMOVER_CORE:
        return "Não promova o Core. Há risco técnico relevante."

    return "Decisão não classificada."


def _leitura_risco(risco: str) -> str:
    if risco == RISCO_BAIXO:
        return "Risco baixo, mas ainda exige fallback ativo."

    if risco == RISCO_MODERADO:
        return "Risco moderado. Avance apenas com testes controlados."

    if risco == RISCO_ALTO:
        return "Risco alto. Não torne o Core padrão."

    if risco == RISCO_CRITICO:
        return "Risco crítico. Investigue antes de qualquer avanço."

    if risco == RISCO_INDEFINIDO:
        return "Risco indefinido por falta de dados."

    return "Risco não classificado."


def _filtrar_condicoes(
    condicoes: List[Dict[str, str]],
    filtro_status: str,
) -> List[Dict[str, str]]:
    if filtro_status == "Todos":
        return condicoes

    return [
        item for item in condicoes
        if item.get("Status", "") == filtro_status
    ]


def _filtrar_plano(
    plano: List[Dict[str, str]],
    filtro_prioridade: str,
) -> List[Dict[str, str]]:
    if filtro_prioridade == "Todas":
        return plano

    return [
        item for item in plano
        if item.get("Prioridade", "") == filtro_prioridade
    ]


def _filtrar_logs_decisao(
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


def _renderizar_alerta_decisao(decisao: str, risco: str, promocao_segura: bool) -> None:
    if decisao == DECISAO_CORE_PODE_SER_PROMOVIDO_COM_FALLBACK and promocao_segura:
        st.success(
            "Decisão: o Core Engine está potencialmente pronto para uma promoção controlada. "
            "A promoção deve manter fallback ativo e plano de rollback."
        )
        return

    if decisao == DECISAO_AUMENTAR_TESTES_CORE:
        st.info(
            "Decisão: aumente os testes com Core Engine no Modo Fundador, mas ainda não torne padrão."
        )
        return

    if decisao == DECISAO_CONTINUAR_TESTE_CONTROLADO:
        st.warning(
            "Decisão: continue em teste controlado. Ainda não há evidência suficiente para promoção."
        )
        return

    if decisao in [DECISAO_MANTER_LEGACY, DECISAO_NAO_PROMOVER_CORE]:
        st.error(
            "Decisão: mantenha Legacy como padrão. O Core Engine não deve ser promovido agora."
        )
        return

    if decisao == DECISAO_SEM_DADOS:
        st.info(
            "Decisão: gere mais logs reais antes de qualquer mudança no motor padrão."
        )
        return

    st.warning(f"Decisão não classificada. Risco atual: {risco}.")


def renderizar_painel_decisao_core() -> None:
    """
    Renderiza o painel visual de decisão controlada do Core Engine.
    """
    _injetar_css_decisao_core()

    st.markdown(
        """
        <div class="dc-hero">
            <div class="dc-eyebrow">v3.8.20 — Decisão controlada</div>
            <div class="dc-title">Decisão do Core Engine</div>
            <div class="dc-subtitle">
                Transforme logs e saúde técnica em decisão operacional:
                manter Legacy, continuar testes, ampliar uso do Core ou preparar promoção controlada.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="dc-highlight">
            O Core Engine não deve virar padrão por empolgação. Ele só deve avançar quando os dados
            mostrarem estabilidade, zero erros, zero fallbacks relevantes e amostra suficiente.
        </div>
        """,
        unsafe_allow_html=True,
    )

    testes = executar_autoteste_decisao_core_engine()

    st.markdown("### Diagnóstico do módulo de decisão")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Versão decisão", VERSAO_DECISAO_CORE_ENGINE)

    with col_2:
        st.metric("Versão saúde", VERSAO_SAUDE_MOTOR)

    with col_3:
        st.metric("Autotestes", len(testes))

    with col_4:
        st.metric("Arquivo de logs", "Encontrado" if _arquivo_logs_existe() else "Ausente")

    if _todos_testes_ok(testes):
        st.success("Módulo de Decisão Core passou nos autotestes.")
    else:
        st.error("Módulo de Decisão Core encontrou falha nos autotestes.")

    with st.expander("Ver autotestes"):
        st.dataframe(
            testes,
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    st.markdown("### Configuração da decisão")

    col_cfg_1, col_cfg_2 = st.columns(2)

    with col_cfg_1:
        limite_logs = st.slider(
            "Quantidade de logs analisados",
            min_value=10,
            max_value=1000,
            value=300,
            step=10,
            help="A decisão considera os logs mais recentes.",
            key="dc_limite_logs",
        )

    with col_cfg_2:
        atualizar = st.button(
            "Atualizar decisão",
            key="dc_atualizar_decisao",
        )

    if atualizar:
        st.session_state["decisao_core_atualizada"] = True
        st.success("Decisão atualizada.")

    decisao_core = analisar_decisao_core_engine_por_arquivo(
        caminho_logs=CAMINHO_LOGS_MOTOR,
        limite=limite_logs,
    )

    analise_saude = decisao_core.get("analise_saude", {})
    metricas = analise_saude.get("metricas", {})

    decisao = str(decisao_core.get("decisao", ""))
    risco = str(decisao_core.get("risco", ""))
    promocao_segura = bool(decisao_core.get("promocao_core_segura", False))
    score = int(analise_saude.get("score_saude", 0))
    status_saude = str(analise_saude.get("status_saude", ""))
    prontidao_core = str(analise_saude.get("prontidao_core", ""))

    st.divider()

    st.markdown("### Decisão executiva")

    col_d1, col_d2, col_d3, col_d4 = st.columns(4)

    with col_d1:
        _card(
            "Decisão",
            decisao,
            _leitura_decisao(decisao),
        )

    with col_d2:
        _card(
            "Risco",
            risco,
            _leitura_risco(risco),
        )

    with col_d3:
        _card(
            "Promoção segura?",
            "SIM" if promocao_segura else "NÃO",
            "Todas as condições críticas precisam estar OK.",
        )

    with col_d4:
        _card(
            "Ação recomendada",
            str(decisao_core.get("acao_recomendada", "")),
            "Próximo passo operacional.",
        )

    _renderizar_alerta_decisao(
        decisao=decisao,
        risco=risco,
        promocao_segura=promocao_segura,
    )

    st.info(decisao_core.get("leitura", ""))

    st.divider()

    st.markdown("### Base técnica da decisão")

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)

    with col_m1:
        st.metric("Score saúde", f"{score}/100")

    with col_m2:
        st.metric("Status saúde", status_saude)

    with col_m3:
        st.metric("Prontidão Core", prontidao_core)

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

    st.markdown("#### Resumo técnico")

    st.dataframe(
        gerar_tabela_resumo_decisao_core(decisao_core),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Condições para promoção do Core")

    condicoes = decisao_core.get("condicoes_promocao", [])

    filtro_condicoes = st.selectbox(
        "Filtrar condições",
        ["Todos", "OK", "PENDENTE", "FALHA"],
        key="dc_filtro_condicoes",
    )

    condicoes_filtradas = _filtrar_condicoes(
        condicoes=condicoes,
        filtro_status=filtro_condicoes,
    )

    st.dataframe(
        condicoes_filtradas,
        use_container_width=True,
        hide_index=True,
    )

    condicoes_pendentes = [
        item for item in condicoes
        if item.get("Status") != "OK"
    ]

    if len(condicoes_pendentes) == 0 and len(condicoes) > 0:
        st.success("Todas as condições de promoção estão aprovadas.")
    else:
        st.warning(
            f"Condições pendentes ou falhas: {len(condicoes_pendentes)}. "
            "Não promova o Core antes de resolver os pontos críticos."
        )

    st.divider()

    st.markdown("### Plano de ação")

    plano = decisao_core.get("plano_acao", [])

    filtro_plano = st.selectbox(
        "Filtrar plano por prioridade",
        ["Todas", "Alta", "Média", "Baixa"],
        key="dc_filtro_plano",
    )

    plano_filtrado = _filtrar_plano(
        plano=plano,
        filtro_prioridade=filtro_plano,
    )

    st.dataframe(
        plano_filtrado,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Logs usados na decisão")

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
                key="dc_filtro_status_execucao",
            )

        with col_f2:
            filtro_fallback = st.selectbox(
                "Fallback",
                ["Todos", "Com fallback", "Sem fallback"],
                key="dc_filtro_fallback",
            )

        with col_f3:
            filtro_motor = st.selectbox(
                "Motor executado",
                ["Todos", "Legacy", "Core Engine"],
                key="dc_filtro_motor_executado",
            )

        logs_filtrados = _filtrar_logs_decisao(
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

    with st.expander("Ver JSON da decisão"):
        st.json(decisao_core)

    st.divider()

    st.markdown("### Download técnico")

    st.download_button(
        label="Baixar relatório de decisão do Core (.md)",
        data=gerar_markdown_decisao_core_engine(decisao_core),
        file_name="relatorio_decisao_core_engine.md",
        mime="text/markdown",
        key="download_relatorio_decisao_core",
    )

    st.markdown(
        """
        <div class="dc-disclaimer">
            <strong>Regra de governança:</strong> este painel não muda automaticamente o motor padrão.
            Ele apenas recomenda. A promoção real do Core Engine deve acontecer em uma versão separada,
            com fallback ativo, rollback possível e teste controlado no Modo Fundador.
        </div>
        """,
        unsafe_allow_html=True,
    )