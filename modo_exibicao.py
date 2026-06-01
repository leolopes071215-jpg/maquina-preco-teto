# modo_exibicao.py

from typing import Dict, List

import streamlit as st


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v2.7 — Modo Usuário Beta / Investidor / Fundador
# ------------------------------------------------------------
# Este arquivo controla a experiência de navegação do app.
#
# Objetivo:
# - reduzir excesso de abas para usuário beta
# - separar áreas de uso real e áreas internas do fundador
# - preparar o produto para testes com usuários reais
# - estruturar aprendizado, rodadas, priorização, sprints,
#   pré-venda, oferta paga e CRM beta
# ============================================================


MODO_USUARIO_BETA = "Usuário Beta"
MODO_INVESTIDOR_COMPLETO = "Investidor Completo"
MODO_FUNDADOR = "Fundador"

MODOS_EXIBICAO = [
    MODO_USUARIO_BETA,
    MODO_INVESTIDOR_COMPLETO,
    MODO_FUNDADOR,
]


ABAS_USUARIO_BETA = [
    "Produto",
    "Navegação",
    "Onboarding",
    "Início",
    "Valuation",
    "Tese & Convicção",
    "Checklist",
    "Relatórios",
    "Feedback Beta",
    "Oferta Beta",
    "Educação",
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
            "Experiência simplificada para alguém testar o produto sem se perder. "
            "Mostra apenas as áreas essenciais para entender, analisar, baixar relatório e enviar feedback."
        ),
        "ideal_para": "Usuários convidados, primeiros beta testers e pessoas sem contexto prévio.",
        "foco": "Clareza, valor rápido e feedback.",
        "risco_reduzido": (
            "Evita expor áreas internas de negócio, marketing, lançamento, convite beta, "
            "release, aprendizado beta, rodadas beta, prioridades beta, sprints beta, "
            "pré-venda beta, oferta paga, CRM beta, dados e UX para usuários comuns."
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
            "CRM beta, dados e auditoria UX."
        ),
        "ideal_para": "Leo, gestor do produto, fundador e operadores do negócio.",
        "foco": (
            "Construção, validação, aquisição, lançamento, convite beta, release, "
            "aprendizado real, rodadas beta, prioridades, sprints, pré-venda, oferta paga, "
            "CRM, dados, UX, backups e monetização."
        ),
        "risco_reduzido": "Nenhum filtro: mostra tudo que existe no MVP e na Fase 2.",
    },
}


def obter_modo_exibicao_padrao() -> str:
    return MODO_FUNDADOR


def obter_abas_por_modo(modo: str) -> List[str]:
    if modo == MODO_USUARIO_BETA:
        return ABAS_USUARIO_BETA

    if modo == MODO_INVESTIDOR_COMPLETO:
        return ABAS_INVESTIDOR_COMPLETO

    return ABAS_FUNDADOR


def obter_descricao_modo(modo: str) -> Dict[str, str]:
    return DESCRICAO_MODOS.get(modo, DESCRICAO_MODOS[MODO_FUNDADOR])


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
            "O que mostra": "Produto, navegação, onboarding, valuation, relatório, feedback e oferta.",
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
                "lançamento, convite beta, release, aprendizado beta, rodadas beta, "
                "prioridades beta, sprints beta, pré-venda beta, oferta paga, CRM beta, dados e UX."
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
        st.success("Interface simplificada para teste beta.")
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
        return "Experiência simplificada para teste beta"

    if modo == MODO_INVESTIDOR_COMPLETO:
        return "Experiência completa para análise de investimentos"

    return "Experiência completa do fundador"


def obter_rotulo_metrica_modo(modo: str) -> str:
    if modo == MODO_USUARIO_BETA:
        return "Usuário Beta"

    if modo == MODO_INVESTIDOR_COMPLETO:
        return "Investidor"

    return "Fundador"