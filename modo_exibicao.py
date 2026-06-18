# modo_exibicao.py

from typing import Dict, List

import streamlit as st


# ============================================================
# VALORIS
# v3.8.91 — Estabilidade de Execução e Validação Leve
# ------------------------------------------------------------
# Este arquivo controla a experiência de navegação do app.
#
# Objetivo:
# - abrir o app público sempre em Usuário Beta
# - impedir que usuários comuns vejam áreas internas de Fundador
# - manter acesso de fundador por código simples
# - separar produto real da sala de máquinas do negócio
# ============================================================


MODO_USUARIO_BETA = "Usuário Beta"
MODO_INVESTIDOR_COMPLETO = "Investidor Completo"
MODO_FUNDADOR = "Fundador"

CODIGO_ACESSO_FUNDADOR = "valoris-fundador"

MODOS_EXIBICAO = [
    MODO_USUARIO_BETA,
    MODO_INVESTIDOR_COMPLETO,
    MODO_FUNDADOR,
]


ABAS_USUARIO_BETA = [
    "Landing Page",
    "Ativação",
    "Copiloto",
    "Jornada",
    "Demonstração",
    "Trilha Valoris",
    "Início",
    "Valuation",
    "Relatórios",
    "Conversão",
    "Convite Beta",
    "Oferta Beta",
    "Feedback Beta",
    "Educação",
]


ABAS_INVESTIDOR_COMPLETO = [
    "Produto",
    "Navegação",
    "Onboarding",
    "Ativação",
    "Copiloto",
    "Jornada",
    "Demonstração",
    "Trilha Valoris",
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
    "Landing Page",
    "Ativação",
    "Copiloto",
    "Jornada",
    "Demonstração",
    "Trilha Valoris",
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
    "Analytics Público",
    "Painel Trilha",
    "Painel Copiloto",
    "Painel Jornada",
    "Painel Ativação",
    "Painel Conversão",
    "Growth",
    "Validação Manual",
    "Fundadores",
    "Maturidade",
    "Arquitetura",
    "Camada Dados",
    "Gateway Dados",
    "SQLite Piloto",
    "Repositórios",
    "PostgreSQL",
    "API",
    "API Scaffold",
    "API Smoke",
    "API Bridge",
    "API Tests",
    "API SQLite",
    "API Adapter",
    "API Security",
    "API Security Panel",
    "API Database Cloud",
    "API Database Contracts",
    "API Database Providers",
    "API Provider Runtime",
    "API Provider Backend",
    "Launch Readiness",
    "Análise Premium",
    "Demo 2 Min",
    "Beta Feedback",
    "Beta Insights",
    "Onboarding Premium",
    "Beta Público",
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
            "Experiência pública de conversão. Começa pela landing page, passa por uma demonstração guiada, apresenta a proposta, "
            "conduz para demonstração, relatório, convite beta, oferta e feedback."
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
    return MODO_USUARIO_BETA


def usuario_tem_acesso_fundador() -> bool:
    return bool(st.session_state.get("acesso_fundador_liberado", False))


def liberar_acesso_fundador(codigo_digitado: str) -> bool:
    if codigo_digitado.strip() == CODIGO_ACESSO_FUNDADOR:
        st.session_state["acesso_fundador_liberado"] = True
        return True

    return False


def bloquear_acesso_fundador() -> None:
    st.session_state["acesso_fundador_liberado"] = False
    st.session_state["modo_exibicao_app"] = MODO_USUARIO_BETA


def obter_abas_por_modo(modo: str) -> List[str]:
    if modo == MODO_USUARIO_BETA:
        return ABAS_USUARIO_BETA

    if modo == MODO_INVESTIDOR_COMPLETO:
        return ABAS_INVESTIDOR_COMPLETO

    if modo == MODO_FUNDADOR and usuario_tem_acesso_fundador():
        return ABAS_FUNDADOR

    return ABAS_USUARIO_BETA


def obter_descricao_modo(modo: str) -> Dict[str, str]:
    if modo == MODO_FUNDADOR and not usuario_tem_acesso_fundador():
        return DESCRICAO_MODOS[MODO_USUARIO_BETA]

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
            "O que mostra": "Landing page, hub de ativação, copiloto diagnóstico, jornada personalizada, demonstração guiada, trilha educativa, início, valuation, relatórios, conversão ética, convite beta, oferta, feedback e educação.",
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


def renderizar_acesso_fundador() -> None:
    with st.expander("Acesso interno", expanded=False):
        if usuario_tem_acesso_fundador():
            st.success("Acesso fundador liberado.")

            if st.button("Bloquear modo fundador"):
                bloquear_acesso_fundador()
                st.rerun()

            return

        codigo_digitado = st.text_input(
            "Código de acesso",
            type="password",
            placeholder="Digite o código interno",
            key="codigo_acesso_fundador",
        )

        if st.button("Liberar acesso fundador"):
            if liberar_acesso_fundador(codigo_digitado):
                st.success("Acesso fundador liberado.")
                st.rerun()
            else:
                st.error("Código inválido.")


def renderizar_controle_modo_exibicao() -> str:
    """
    Renderiza o seletor de modo na sidebar e retorna o modo escolhido.
    """
    if "acesso_fundador_liberado" not in st.session_state:
        st.session_state["acesso_fundador_liberado"] = False

    if "modo_exibicao_app" not in st.session_state:
        st.session_state["modo_exibicao_app"] = obter_modo_exibicao_padrao()

    if not usuario_tem_acesso_fundador():
        st.session_state["modo_exibicao_app"] = MODO_USUARIO_BETA

    st.markdown("#### Experiência do app")

    if usuario_tem_acesso_fundador():
        opcoes_modo = MODOS_EXIBICAO
    else:
        opcoes_modo = [MODO_USUARIO_BETA]

    modo_atual = st.session_state.get("modo_exibicao_app", MODO_USUARIO_BETA)

    if modo_atual not in opcoes_modo:
        modo_atual = MODO_USUARIO_BETA
        st.session_state["modo_exibicao_app"] = MODO_USUARIO_BETA

    modo = st.radio(
        "Modo de exibição",
        opcoes_modo,
        index=opcoes_modo.index(modo_atual),
        help=(
            "Usuários públicos acessam a experiência beta. "
            "O modo fundador exige liberação interna."
        ),
        key="modo_exibicao_app",
    )

    descricao = obter_descricao_modo(modo)

    st.caption(descricao["descricao"])

    if modo == MODO_USUARIO_BETA:
        st.success("Porta de entrada pública: landing, demonstração, relatório, convite e oferta beta.")
    elif modo == MODO_INVESTIDOR_COMPLETO:
        st.info("Interface completa para análise e acompanhamento.")
    else:
        st.warning("Modo fundador: áreas internas de negócio visíveis.")

    st.divider()
    renderizar_acesso_fundador()

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
        return "Descubra quanto vale uma empresa antes de investir"

    if modo == MODO_INVESTIDOR_COMPLETO:
        return "Experiência completa para análise de investimentos"

    if modo == MODO_FUNDADOR and usuario_tem_acesso_fundador():
        return "Experiência completa do fundador"

    return "Descubra quanto vale uma empresa antes de investir"


def obter_rotulo_metrica_modo(modo: str) -> str:
    if modo == MODO_USUARIO_BETA:
        return "Beta"

    if modo == MODO_INVESTIDOR_COMPLETO:
        return "Investidor"

    if modo == MODO_FUNDADOR and usuario_tem_acesso_fundador():
        return "Fundador"

    return "Beta"

ABAS_MODO_FUNDADOR = [
    "Agenda Revisões",
    "Rotina Semanal",
    "Alertas Radar",
    'Cockpit Principal',
    'Radar Principal',
    'Pipeline Principal',
    'Pipeline Backend',
    'Análise Principal',
    'Análise Backend',
    'Histórico Principal',
    'Histórico Backend',
    'Migração Backend',
    'Health Check',
    'Repository Backend',
    'SQLite Local',
    'Simulador Migração',
    'Repository Único',
    'Mapa Dados',
    'Radar Revisões',
    'Pipeline Decisão',
    'Análise Inteligente',
    'Motor + Relatório',
    'Motor + Watchlist',
    'Histórico Análises',
    'Motor Análise Ativos',
    'Recuperação Páginas',
    'Navegação Segura',
    'Estabilidade',
    'Roadmap Premium',
    'Feedback Pacote',
    'Pacote Premium',
    'Relatório Premium v2',
    'Comparador Setorial',
    'Watchlist Fundadores',
    'Retenção Fundadores',
    'Checkout Fundadores',
    'Oferta Beta',
    'Beta Público',
    'Onboarding Premium',
    'Beta Insights',
    'Beta Feedback',
    'Lista de Espera',
    'Gateway Dados',
    'Repositórios',
]

