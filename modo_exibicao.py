# modo_exibicao.py

from typing import Dict, List

import streamlit as st


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v3.8.26 — Deploy Público no Modo Fundador
# ------------------------------------------------------------
# Este arquivo controla a experiência de navegação do app.
#
# Objetivo:
# - reduzir ruído para usuário beta
# - abrir o app por padrão em experiência simples
# - separar produto real de áreas internas do fundador
# - integrar a preparação para deploy público apenas no Modo Fundador
# - preparar o MVP para teste público com usuários reais
# ============================================================


MODO_USUARIO_BETA = "Usuário Beta"
MODO_INVESTIDOR_COMPLETO = "Investidor Completo"
MODO_FUNDADOR = "Fundador"

MODOS_EXIBICAO = [
    MODO_USUARIO_BETA,
    MODO_INVESTIDOR_COMPLETO,
    MODO_FUNDADOR,
]


# Experiência enxuta para teste real.
# O usuário beta precisa entender valor, analisar, revisar, baixar relatório e dar feedback.
ABAS_USUARIO_BETA = [
    "Início",
    "Valuation",
    "Checklist",
    "Relatórios",
    "Feedback Beta",
    "Oferta Beta",
]


ABAS_INVESTIDOR_COMPLETO = [
    "Produto",
    "Navegação",
    "Onboarding",
    "Início",
    "Painel Executivo",
    "Valuation",
    "Simulador",
    "Tese & Convicção",
    "Checklist",
    "Watchlist",
    "Relatórios",
    "Multiativos",
    "Ações Brasil",
    "FIIs",
    "Renda Fixa",
    "Resumo da Decisão",
    "Comparativo",
    "Tese qualitativa",
    "Premissas",
    "Histórico",
    "Educação",
    "Feedback Beta",
    "Oferta Beta",
]


ABAS_FUNDADOR = [
    "Produto",
    "Navegação",
    "Onboarding",
    "Início",
    "Painel Executivo",
    "Valuation",
    "Simulador",
    "Tese & Convicção",
    "Checklist",
    "Watchlist",
    "Relatórios",
    "Feedback Beta",
    "Beta Fechado",
    "Oferta Beta",
    "Negócio",
    "Marketing",
    "Conteúdo",
    "Landing Page",
    "Lançamento",
    "Convite Beta",
    "Release",
    "Aprendizado Beta",
    "Rodadas Beta",
    "Prioridades Beta",
    "Sprints Beta",
    "Pré-venda Beta",
    "Oferta Paga",
    "CRM Beta",
    "Painel Beta",
    "Fase 3",
    "Clientes Beta",
    "Suporte Beta",
    "Retenção Beta",
    "Painel Fase 3",
    "Métricas Fase 3",
    "Decisão Fase 3",
    "Plano Fase 4",
    "Arquitetura Fase 4",
    "Core Engine",
    "Compatibilidade Core",
    "Motor Adapter",
    "Motor Controlado",
    "Auditoria Motor Principal",
    "Fallback Motor",
    "Logs Motor",
    "Saúde Motor",
    "Decisão Core",
    "Promoção Core",
    "Estratégia Produto",
    "Deploy Público",
    "Dados",
    "UX",
    "Multiativos",
    "Ações Brasil",
    "FIIs",
    "Renda Fixa",
    "Resumo da Decisão",
    "Comparativo",
    "Tese qualitativa",
    "Premissas",
    "Histórico",
    "Educação",
]


DESCRICAO_MODOS = {
    MODO_USUARIO_BETA: {
        "titulo": "Modo Usuário Beta",
        "descricao": (
            "Experiência enxuta para teste real. Mostra apenas o essencial: análise, "
            "preço-teto, checklist, relatório, feedback e oferta."
        ),
        "ideal_para": "Usuários convidados, primeiros beta testers e pessoas sem contexto prévio.",
        "foco": "Clareza, valor rápido e feedback real.",
        "risco_reduzido": (
            "Oculta áreas internas de fundador, governança técnica, negócio, arquitetura, "
            "métricas, logs, motores e módulos avançados."
        ),
    },
    MODO_INVESTIDOR_COMPLETO: {
        "titulo": "Modo Investidor Completo",
        "descricao": (
            "Experiência completa para quem quer usar o app como ferramenta de estudo, "
            "análise, acompanhamento e registro."
        ),
        "ideal_para": (
            "Usuários mais avançados, investidores recorrentes e pessoas que querem explorar "
            "todos os módulos de análise."
        ),
        "foco": "Análise profunda, rotina e acompanhamento.",
        "risco_reduzido": "Mantém áreas estratégicas do fundador fora da experiência principal.",
    },
    MODO_FUNDADOR: {
        "titulo": "Modo Fundador",
        "descricao": (
            "Experiência total do produto, incluindo áreas de validação, negócio, marketing, "
            "conteúdo, landing page, lançamento, convite beta, release, aprendizado beta, "
            "rodadas beta, prioridades beta, sprints beta, pré-venda beta, oferta paga, "
            "CRM beta, painel beta, Fase 3, clientes beta pagos, suporte beta, retenção beta, "
            "painel mestre da Fase 3, métricas da Fase 3, decisão Go/No-Go, plano Fase 4, "
            "arquitetura Fase 4, Core Engine, compatibilidade Core vs Legacy, Motor Adapter, "
            "Motor Controlado, Auditoria Motor Principal, Fallback Motor, Logs Motor, Saúde Motor, "
            "Decisão Core, Promoção Core, Estratégia Produto, Deploy Público, dados e auditoria UX."
        ),
        "ideal_para": "Leo, gestor do produto, fundador e operadores do negócio.",
        "foco": (
            "Construção, validação, aquisição, lançamento, produto, beta real, oferta, "
            "arquitetura, governança técnica, deploy público, dados, UX, backups e monetização."
        ),
        "risco_reduzido": (
            "Nenhum filtro: mostra tudo que existe no MVP, na Fase 2, Fase 3, Fase 4, "
            "núcleo técnico, estratégia, deploy público, negócio, marketing e operação."
        ),
    },
}


def obter_modo_exibicao_padrao() -> str:
    # Para teste público, o padrão precisa ser a experiência do usuário comum.
    return MODO_USUARIO_BETA


def obter_abas_por_modo(modo: str) -> List[str]:
    if modo == MODO_USUARIO_BETA:
        return ABAS_USUARIO_BETA

    if modo == MODO_INVESTIDOR_COMPLETO:
        return ABAS_INVESTIDOR_COMPLETO

    return ABAS_FUNDADOR


def obter_descricao_modo(modo: str) -> Dict[str, str]:
    return DESCRICAO_MODOS.get(modo, DESCRICAO_MODOS[MODO_USUARIO_BETA])


def aba_ativa(nome_aba: str, modo: str) -> bool:
    return nome_aba in obter_abas_por_modo(modo)


def contar_abas_por_modo(modo: str) -> int:
    return len(obter_abas_por_modo(modo))


def obter_resumo_modos() -> List[Dict[str, str]]:
    return [
        {
            "Modo": MODO_USUARIO_BETA,
            "Quantidade de abas": str(len(ABAS_USUARIO_BETA)),
            "Uso ideal": "Teste rápido com usuários reais.",
            "O que mostra": "Início, valuation, checklist, relatório, feedback e oferta.",
        },
        {
            "Modo": MODO_INVESTIDOR_COMPLETO,
            "Quantidade de abas": str(len(ABAS_INVESTIDOR_COMPLETO)),
            "Uso ideal": "Uso recorrente para análise e acompanhamento.",
            "O que mostra": "Todos os módulos de análise, acompanhamento, histórico e multiativos.",
        },
        {
            "Modo": MODO_FUNDADOR,
            "Quantidade de abas": str(len(ABAS_FUNDADOR)),
            "Uso ideal": "Gestão completa do produto, negócio e aprendizado do beta real.",
            "O que mostra": (
                "Tudo: produto, análise, beta, negócio, marketing, conteúdo, landing, "
                "lançamento, CRM, Fase 3, Fase 4, Core Engine, logs, saúde, decisão, "
                "promoção, estratégia, deploy público, dados e UX."
            ),
        },
    ]


def obter_abas_ocultas_no_modo(modo: str) -> List[str]:
    abas_modo = set(obter_abas_por_modo(modo))
    abas_fundador = set(ABAS_FUNDADOR)

    return sorted(list(abas_fundador - abas_modo))


def renderizar_controle_modo_exibicao() -> str:
    """
    Renderiza o seletor de modo na sidebar e retorna o modo escolhido.
    """
    if "modo_exibicao_app" not in st.session_state:
        st.session_state["modo_exibicao_app"] = obter_modo_exibicao_padrao()

    st.markdown("#### Experiência do app")

    modo = st.radio(
        "Modo de exibição",
        MODOS_EXIBICAO,
        index=MODOS_EXIBICAO.index(st.session_state["modo_exibicao_app"]),
        help=(
            "Escolha quais áreas do app devem aparecer. "
            "Use Usuário Beta para testes reais e Fundador para construção do negócio."
        ),
        key="modo_exibicao_app",
    )

    descricao = obter_descricao_modo(modo)

    st.caption(descricao["descricao"])

    if modo == MODO_USUARIO_BETA:
        st.success("Interface enxuta para teste beta.")
    elif modo == MODO_INVESTIDOR_COMPLETO:
        st.info("Interface completa para análise e acompanhamento.")
    else:
        st.warning("Modo fundador: áreas internas de negócio visíveis.")

    return modo


def renderizar_painel_modo_exibicao(modo: str) -> None:
    """
    Renderiza uma visão resumida do modo atual.
    """
    descricao = obter_descricao_modo(modo)
    abas_visiveis = obter_abas_por_modo(modo)
    abas_ocultas = obter_abas_ocultas_no_modo(modo)

    with st.container(border=True):
        st.markdown(f"### {descricao['titulo']}")

        col_1, col_2, col_3 = st.columns(3)

        with col_1:
            st.metric("Abas visíveis", len(abas_visiveis))

        with col_2:
            st.metric("Abas ocultas", len(abas_ocultas))

        with col_3:
            st.metric("Foco", descricao["foco"])

        st.info(descricao["descricao"])

        st.markdown("#### Ideal para")
        st.write(descricao["ideal_para"])

        st.markdown("#### Risco reduzido")
        st.write(descricao["risco_reduzido"])

        st.markdown("#### Abas visíveis neste modo")
        st.write(", ".join(abas_visiveis))

        if len(abas_ocultas) > 0:
            st.markdown("#### Abas ocultas neste modo")
            st.write(", ".join(abas_ocultas))


def obter_mensagem_modo_para_hero(modo: str) -> str:
    if modo == MODO_USUARIO_BETA:
        return "Descubra seu preço-teto antes de investir"

    if modo == MODO_INVESTIDOR_COMPLETO:
        return "Experiência completa para análise de investimentos"

    return "Experiência completa do fundador"


def obter_rotulo_metrica_modo(modo: str) -> str:
    if modo == MODO_USUARIO_BETA:
        return "Beta"

    if modo == MODO_INVESTIDOR_COMPLETO:
        return "Investidor"

    return "Fundador"