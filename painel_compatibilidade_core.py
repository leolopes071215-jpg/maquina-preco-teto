# painel_compatibilidade_core.py

from datetime import datetime
from typing import Any, Dict, List

import streamlit as st

from compatibilidade_core_legacy import (
    VERSAO_COMPATIBILIDADE,
    executar_auditoria_compatibilidade,
    executar_autoteste_compatibilidade,
    gerar_markdown_auditoria_compatibilidade,
    gerar_tabela_detalhada_compatibilidade,
    gerar_tabela_resumo_compatibilidade,
)


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v3.8.3 — Painel de Compatibilidade Core vs Legacy
# ------------------------------------------------------------
# Esta tela audita a compatibilidade entre:
#
# - valuation.py      -> motor antigo em uso no app
# - core_valuation.py -> novo Core Engine profissional
#
# Objetivo:
# - visualizar se os dois motores calculam igual
# - reduzir risco antes da troca definitiva
# - auditar cenários de valuation
# - baixar relatório de compatibilidade
# - preparar a migração segura do motor principal
# ============================================================


def _injetar_css_compatibilidade() -> None:
    st.markdown(
        """
        <style>
            .cc-hero {
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

            .cc-eyebrow {
                color: #d6b56d;
                font-size: 0.78rem;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.35rem;
            }

            .cc-title {
                color: #f4f7fb;
                font-size: 2.1rem;
                font-weight: 900;
                margin-bottom: 0.45rem;
                line-height: 1.14;
            }

            .cc-subtitle {
                color: rgba(244, 247, 251, 0.76);
                font-size: 1rem;
                line-height: 1.62;
                max-width: 1080px;
            }

            .cc-card {
                padding: 1.1rem 1.15rem;
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.035);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.18);
                height: 100%;
            }

            .cc-card-label {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .cc-card-value {
                color: #f4f7fb;
                font-size: 1.22rem;
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .cc-card-note {
                color: rgba(244, 247, 251, 0.68);
                font-size: 0.87rem;
                line-height: 1.47;
            }

            .cc-highlight {
                padding: 0.95rem 1rem;
                border-radius: 16px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.92rem;
                line-height: 1.55;
                margin-bottom: 0.7rem;
            }

            .cc-disclaimer {
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
        <div class="cc-card">
            <div class="cc-card-label">{label}</div>
            <div class="cc-card-value">{value}</div>
            <div class="cc-card-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _resumo_autotestes(testes: List[Dict[str, Any]]) -> str:
    if all(teste.get("status") == "OK" for teste in testes):
        return "OK"

    return "FALHA"


def _gerar_leitura_executiva(auditoria: Dict[str, Any]) -> str:
    if auditoria.get("aprovado"):
        return (
            "A auditoria indica que o Core Engine novo está compatível com o motor antigo "
            "nos cenários testados. Isso permite avançar para a próxima etapa: preparar a troca "
            "controlada do motor principal do app."
        )

    return (
        "A auditoria encontrou diferenças entre o motor antigo e o Core Engine. "
        "A troca do motor principal ainda não deve ser feita. Primeiro precisamos analisar os campos divergentes."
    )


def renderizar_painel_compatibilidade_core() -> None:
    """
    Renderiza o painel de compatibilidade entre o motor antigo e o Core Engine.
    """
    _injetar_css_compatibilidade()

    st.markdown(
        """
        <div class="cc-hero">
            <div class="cc-eyebrow">v3.8.3 — Auditoria de compatibilidade</div>
            <div class="cc-title">Core Engine vs Motor Legacy</div>
            <div class="cc-subtitle">
                Compare o motor antigo do app com o novo Core Engine profissional.
                Esta etapa reduz risco antes de substituir o cálculo principal da Máquina de Preço-Teto.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="cc-highlight">
            Antes de trocar o motor principal, precisamos provar que o novo núcleo calcula os mesmos resultados
            do motor antigo. Primeiro compatibilidade. Depois migração.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Configuração da auditoria")

    tolerancia = st.number_input(
        "Tolerância numérica",
        min_value=0.0,
        max_value=1.0,
        value=0.0001,
        step=0.0001,
        format="%.6f",
        help="Diferença máxima aceita entre valores numéricos dos dois motores.",
        key="compatibilidade_tolerancia",
    )

    auditoria = executar_auditoria_compatibilidade(tolerancia=tolerancia)
    autotestes = executar_autoteste_compatibilidade()

    st.session_state["resultado_compatibilidade_core"] = {
        "versao": VERSAO_COMPATIBILIDADE,
        "aprovado": auditoria.get("aprovado"),
        "total_cenarios": auditoria.get("total_cenarios"),
        "cenarios_compativeis": auditoria.get("cenarios_compativeis"),
        "cenarios_com_diferenca": auditoria.get("cenarios_com_diferenca"),
        "tolerancia": tolerancia,
    }

    st.divider()

    st.markdown("### Diagnóstico geral")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Versão auditoria", VERSAO_COMPATIBILIDADE)

    with col_2:
        st.metric("Status", "APROVADO" if auditoria.get("aprovado") else "REPROVADO")

    with col_3:
        st.metric("Cenários testados", auditoria.get("total_cenarios", 0))

    with col_4:
        st.metric("Diferenças", auditoria.get("cenarios_com_diferenca", 0))

    if auditoria.get("aprovado"):
        st.success("Compatibilidade aprovada: o Core Engine bateu com o motor antigo nos cenários testados.")
    else:
        st.error("Compatibilidade reprovada: existem diferenças entre o motor antigo e o Core Engine.")

    st.info(_gerar_leitura_executiva(auditoria))

    st.divider()

    st.markdown("### Indicadores da auditoria")

    col_a, col_b, col_c, col_d = st.columns(4)

    with col_a:
        _card(
            "Cenários compatíveis",
            str(auditoria.get("cenarios_compativeis", 0)),
            "Cenários sem diferença relevante.",
        )

    with col_b:
        _card(
            "Cenários com diferença",
            str(auditoria.get("cenarios_com_diferenca", 0)),
            "Devem ser investigados antes da migração.",
        )

    with col_c:
        _card(
            "Autotestes",
            _resumo_autotestes(autotestes),
            "Sanidade básica do comparador.",
        )

    with col_d:
        _card(
            "Tolerância",
            str(tolerancia),
            "Limite aceito para diferenças numéricas.",
        )

    st.divider()

    st.markdown("### Autotestes da compatibilidade")

    st.dataframe(
        autotestes,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Resumo por cenário")

    tabela_resumo = gerar_tabela_resumo_compatibilidade(auditoria)

    st.dataframe(
        tabela_resumo,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Comparação detalhada por campo")

    tabela_detalhada = gerar_tabela_detalhada_compatibilidade(auditoria)

    filtro = st.selectbox(
        "Filtrar comparação",
        ["Todos", "Apenas diferenças", "Apenas compatíveis"],
        key="compatibilidade_filtro",
    )

    tabela_filtrada = tabela_detalhada

    if filtro == "Apenas diferenças":
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

    st.divider()

    st.markdown("### Campos com diferença")

    campos_diferenca = auditoria.get("campos_com_diferenca", [])

    if len(campos_diferenca) == 0:
        st.success("Nenhum campo divergente encontrado.")
    else:
        st.warning("Existem campos divergentes. Revise antes de migrar o motor principal.")
        st.dataframe(
            campos_diferenca,
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    st.markdown("### Decisão técnica sugerida")

    if auditoria.get("aprovado"):
        st.success(
            "Próxima etapa recomendada: preparar a troca controlada do app principal para usar o Core Engine."
        )
        st.write(
            "Ainda não vamos apagar o motor antigo. Primeiro vamos integrar o novo motor em paralelo, "
            "comparar os resultados no app e só depois transformar o Core Engine no motor padrão."
        )
    else:
        st.error(
            "Próxima etapa recomendada: corrigir divergências antes de qualquer troca de motor."
        )
        st.write(
            "A substituição do motor principal só deve acontecer quando a auditoria ficar aprovada."
        )

    st.divider()

    st.markdown("### Download do relatório")

    st.download_button(
        label="Baixar auditoria de compatibilidade (.md)",
        data=gerar_markdown_auditoria_compatibilidade(auditoria),
        file_name="auditoria_compatibilidade_core_legacy.md",
        mime="text/markdown",
        key="download_auditoria_compatibilidade_core",
    )

    st.markdown(
        """
        <div class="cc-disclaimer">
            <strong>Regra de migração:</strong> o Core Engine só deve substituir o motor antigo
            depois que a compatibilidade estiver aprovada e a troca for feita de forma controlada.
        </div>
        """,
        unsafe_allow_html=True,
    )