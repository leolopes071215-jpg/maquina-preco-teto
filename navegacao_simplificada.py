# navegacao_simplificada.py

from typing import Any, Dict, List

import streamlit as st


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v1.35 — Simplificação de Navegação
# ------------------------------------------------------------
# Esta tela cria um mapa central do produto.
# Objetivo:
# - reduzir confusão gerada por muitas abas
# - organizar a jornada por blocos
# - mostrar ao usuário o caminho ideal
# - preparar a futura separação entre Modo Usuário e Modo Fundador
# ============================================================


OBJETIVOS_NAVEGACAO = [
    "Quero entender o produto rapidamente",
    "Quero analisar um ativo",
    "Quero acompanhar ativos",
    "Quero gerar relatório",
    "Quero testar como usuário beta",
    "Quero validar o negócio",
    "Quero produzir conteúdo/marketing",
    "Quero preparar lançamento beta",
]


def _safe_get_dict(key: str) -> Dict[str, Any]:
    valor = st.session_state.get(key)

    if isinstance(valor, dict):
        return valor

    return {}


def _fmt_texto(valor: Any, padrao: str = "N/D") -> str:
    if valor is None or valor == "":
        return padrao

    return str(valor)


def _extrair_contexto_navegacao() -> Dict[str, Any]:
    valuation = _safe_get_dict("resultado_valuation")
    negocio = _safe_get_dict("resultado_dashboard_negocio")
    marketing = _safe_get_dict("resultado_marketing")
    lancamento = _safe_get_dict("resultado_lancamento_beta")
    onboarding = _safe_get_dict("resultado_onboarding")

    return {
        "empresa": valuation.get("empresa", "Nenhuma análise ativa"),
        "ticker": valuation.get("ticker", "N/D"),
        "status": valuation.get("status", valuation.get("status_valuation", "N/D")),
        "tipo_analise": valuation.get("tipo_analise", "N/D"),
        "preco_teto": valuation.get("preco_teto", 0),
        "preco_atual": valuation.get("preco_atual", 0),
        "score_tracao": negocio.get("score_tracao", 0),
        "score_lancamento": lancamento.get("score_lancamento", 0),
        "dor_dominante": marketing.get("dor_dominante", negocio.get("dor_mais_comum", "N/D")),
        "perfil_onboarding": onboarding.get("perfil", "N/D"),
        "objetivo_onboarding": onboarding.get("objetivo", "N/D"),
    }


def _gerar_blocos_navegacao() -> List[Dict[str, str]]:
    return [
        {
            "Bloco": "Começar",
            "Abas": "Produto, Navegação, Onboarding, Início",
            "Para que serve": "Entender a proposta, escolher caminho e começar sem se perder.",
            "Usuário ideal": "Todos os usuários, principalmente iniciantes e beta testers.",
            "Prioridade": "Muito alta",
        },
        {
            "Bloco": "Analisar Ativo",
            "Abas": "Valuation, Simulador, Tese & Convicção, Checklist, Resumo da Decisão, Premissas",
            "Para que serve": "Fazer uma análise estruturada de preço, tese, riscos e cenários.",
            "Usuário ideal": "Investidor iniciante, intermediário e avançado.",
            "Prioridade": "Muito alta",
        },
        {
            "Bloco": "Acompanhar",
            "Abas": "Watchlist, Multiativos, Ações Brasil, FIIs, Renda Fixa, Comparativo",
            "Para que serve": "Acompanhar oportunidades, classes de ativos e status de análise.",
            "Usuário ideal": "Quem quer criar rotina de acompanhamento.",
            "Prioridade": "Alta",
        },
        {
            "Bloco": "Relatórios",
            "Abas": "Relatórios, Histórico, Educação",
            "Para que serve": "Registrar análises, baixar documentos e revisar aprendizados.",
            "Usuário ideal": "Usuários que querem evoluir com registro e revisão.",
            "Prioridade": "Alta",
        },
        {
            "Bloco": "Beta e Feedback",
            "Abas": "Feedback Beta, Beta Fechado, Oferta Beta",
            "Para que serve": "Coletar opinião, medir valor percebido e formar lista de espera.",
            "Usuário ideal": "Usuários beta e interessados no produto.",
            "Prioridade": "Muito alta para validação",
        },
        {
            "Bloco": "Negócio/Fundador",
            "Abas": "Negócio, Marketing, Conteúdo, Landing Page, Lançamento",
            "Para que serve": "Gerenciar validação, aquisição, conteúdo, página e lançamento beta.",
            "Usuário ideal": "Fundador, gestor do produto e criador do negócio.",
            "Prioridade": "Alta para você, baixa para usuário comum",
        },
    ]


def _gerar_rota_por_objetivo(objetivo: str) -> List[Dict[str, str]]:
    if objetivo == "Quero entender o produto rapidamente":
        return [
            {
                "Ordem": "1",
                "Aba": "Produto",
                "Ação": "Leia a proposta de valor.",
                "Resultado": "Entender o que a plataforma faz.",
            },
            {
                "Ordem": "2",
                "Aba": "Navegação",
                "Ação": "Veja os blocos principais do produto.",
                "Resultado": "Saber onde está cada coisa.",
            },
            {
                "Ordem": "3",
                "Aba": "Onboarding",
                "Ação": "Escolha seu perfil e objetivo.",
                "Resultado": "Receber uma rota personalizada.",
            },
            {
                "Ordem": "4",
                "Aba": "Início",
                "Ação": "Siga a jornada guiada.",
                "Resultado": "Começar a usar sem travar.",
            },
        ]

    if objetivo == "Quero analisar um ativo":
        return [
            {
                "Ordem": "1",
                "Aba": "Premissas",
                "Ação": "Revise dados financeiros, múltiplos e margem de segurança.",
                "Resultado": "Garantir que o cálculo não está baseado em dados ruins.",
            },
            {
                "Ordem": "2",
                "Aba": "Valuation",
                "Ação": "Veja preço justo, preço-teto e status educacional.",
                "Resultado": "Entender a zona racional de preço.",
            },
            {
                "Ordem": "3",
                "Aba": "Simulador",
                "Ação": "Teste cenários conservador, base e otimista.",
                "Resultado": "Ver sensibilidade do valuation.",
            },
            {
                "Ordem": "4",
                "Aba": "Tese & Convicção",
                "Ação": "Avalie tese, riscos e fundamentos.",
                "Resultado": "Não decidir apenas por número.",
            },
            {
                "Ordem": "5",
                "Aba": "Checklist",
                "Ação": "Audite erros e vieses.",
                "Resultado": "Reduzir decisão impulsiva.",
            },
            {
                "Ordem": "6",
                "Aba": "Resumo da Decisão",
                "Ação": "Leia a decisão educacional consolidada.",
                "Resultado": "Ter uma visão final mais organizada.",
            },
        ]

    if objetivo == "Quero acompanhar ativos":
        return [
            {
                "Ordem": "1",
                "Aba": "Watchlist",
                "Ação": "Salve o ativo com prioridade, status e próxima ação.",
                "Resultado": "Criar rotina de acompanhamento.",
            },
            {
                "Ordem": "2",
                "Aba": "Multiativos",
                "Ação": "Entenda a classificação geral entre classes de ativos.",
                "Resultado": "Comparar ações, FIIs e renda fixa com mais método.",
            },
            {
                "Ordem": "3",
                "Aba": "Ações Brasil",
                "Ação": "Teste a estrutura para ações brasileiras.",
                "Resultado": "Adaptar análise ao mercado local.",
            },
            {
                "Ordem": "4",
                "Aba": "FIIs",
                "Ação": "Analise pontos específicos de fundos imobiliários.",
                "Resultado": "Evitar olhar apenas dividend yield.",
            },
            {
                "Ordem": "5",
                "Aba": "Renda Fixa",
                "Ação": "Compare prazo, liquidez, retorno e risco.",
                "Resultado": "Avaliar renda fixa com mais racionalidade.",
            },
        ]

    if objetivo == "Quero gerar relatório":
        return [
            {
                "Ordem": "1",
                "Aba": "Valuation",
                "Ação": "Confira os resultados principais.",
                "Resultado": "Ter os números centrais prontos.",
            },
            {
                "Ordem": "2",
                "Aba": "Tese & Convicção",
                "Ação": "Revise tese, riscos e fundamentos.",
                "Resultado": "Complementar a parte qualitativa.",
            },
            {
                "Ordem": "3",
                "Aba": "Checklist",
                "Ação": "Verifique pontos de risco.",
                "Resultado": "Evitar relatório superficial.",
            },
            {
                "Ordem": "4",
                "Aba": "Relatórios",
                "Ação": "Baixe o relatório em Markdown.",
                "Resultado": "Guardar a análise para revisão futura.",
            },
            {
                "Ordem": "5",
                "Aba": "Histórico",
                "Ação": "Consulte análises salvas.",
                "Resultado": "Comparar evolução das premissas.",
            },
        ]

    if objetivo == "Quero testar como usuário beta":
        return [
            {
                "Ordem": "1",
                "Aba": "Produto",
                "Ação": "Leia a proposta sem explicação externa.",
                "Resultado": "Ver se a mensagem é clara.",
            },
            {
                "Ordem": "2",
                "Aba": "Onboarding",
                "Ação": "Escolha perfil e objetivo.",
                "Resultado": "Testar a jornada guiada.",
            },
            {
                "Ordem": "3",
                "Aba": "Valuation",
                "Ação": "Observe se os números fazem sentido visualmente.",
                "Resultado": "Avaliar clareza do motor principal.",
            },
            {
                "Ordem": "4",
                "Aba": "Relatórios",
                "Ação": "Teste o download do relatório.",
                "Resultado": "Avaliar entrega final.",
            },
            {
                "Ordem": "5",
                "Aba": "Feedback Beta",
                "Ação": "Preencha o formulário de feedback.",
                "Resultado": "Gerar dado real para validação.",
            },
            {
                "Ordem": "6",
                "Aba": "Oferta Beta",
                "Ação": "Entre na lista de espera, caso tenha interesse.",
                "Resultado": "Medir intenção real de compra.",
            },
        ]

    if objetivo == "Quero validar o negócio":
        return [
            {
                "Ordem": "1",
                "Aba": "Feedback Beta",
                "Ação": "Veja clareza, utilidade, confiança e disposição de pagamento.",
                "Resultado": "Entender valor percebido.",
            },
            {
                "Ordem": "2",
                "Aba": "Oferta Beta",
                "Ação": "Analise lista de espera, dor e preço mais citado.",
                "Resultado": "Medir intenção de compra.",
            },
            {
                "Ordem": "3",
                "Aba": "Negócio",
                "Ação": "Veja score de tração e próximas ações.",
                "Resultado": "Decidir se avança ou ajusta.",
            },
            {
                "Ordem": "4",
                "Aba": "Beta Fechado",
                "Ação": "Revise roteiro de teste e critérios de prontidão.",
                "Resultado": "Organizar validação com usuários reais.",
            },
        ]

    if objetivo == "Quero produzir conteúdo/marketing":
        return [
            {
                "Ordem": "1",
                "Aba": "Marketing",
                "Ação": "Defina posicionamento, promessa e copy.",
                "Resultado": "Ter mensagem central clara.",
            },
            {
                "Ordem": "2",
                "Aba": "Conteúdo",
                "Ação": "Gere roteiros e registre posts no calendário.",
                "Resultado": "Transformar estratégia em produção.",
            },
            {
                "Ordem": "3",
                "Aba": "Landing Page",
                "Ação": "Use a copy para montar uma página externa.",
                "Resultado": "Criar destino para interessados.",
            },
            {
                "Ordem": "4",
                "Aba": "Oferta Beta",
                "Ação": "Direcione interessados para a lista de espera.",
                "Resultado": "Medir demanda real.",
            },
        ]

    if objetivo == "Quero preparar lançamento beta":
        return [
            {
                "Ordem": "1",
                "Aba": "Landing Page",
                "Ação": "Revise headline, promessa, benefícios e CTA.",
                "Resultado": "Ter página pronta para captar interessados.",
            },
            {
                "Ordem": "2",
                "Aba": "Conteúdo",
                "Ação": "Planeje conteúdos de pré-lançamento.",
                "Resultado": "Criar demanda antes do convite.",
            },
            {
                "Ordem": "3",
                "Aba": "Lançamento",
                "Ação": "Siga o checklist e plano de 14 dias.",
                "Resultado": "Executar lançamento controlado.",
            },
            {
                "Ordem": "4",
                "Aba": "Negócio",
                "Ação": "Acompanhe score de tração.",
                "Resultado": "Tomar decisão baseada em dados.",
            },
        ]

    return []


def _gerar_abas_por_prioridade() -> List[Dict[str, str]]:
    return [
        {
            "Prioridade": "Essencial para usuário beta",
            "Abas": "Produto, Navegação, Onboarding, Início, Valuation, Tese & Convicção, Checklist, Relatórios, Feedback Beta",
            "Motivo": "São as abas que mostram valor rápido e coletam opinião.",
        },
        {
            "Prioridade": "Útil para investidor recorrente",
            "Abas": "Watchlist, Simulador, Premissas, Histórico, Multiativos, Ações Brasil, FIIs, Renda Fixa",
            "Motivo": "Ajudam a transformar o app em rotina de análise.",
        },
        {
            "Prioridade": "Interno do fundador",
            "Abas": "Negócio, Marketing, Conteúdo, Landing Page, Lançamento, Beta Fechado, Oferta Beta",
            "Motivo": "Servem para validar, vender e evoluir o negócio.",
        },
        {
            "Prioridade": "Complementar",
            "Abas": "Comparativo, Educação, Painel Executivo, Resumo da Decisão",
            "Motivo": "Aumentam valor, mas não precisam ser a primeira coisa que o usuário vê.",
        },
    ]


def _gerar_fluxo_minimo_beta() -> List[Dict[str, str]]:
    return [
        {
            "Passo": "1",
            "Aba": "Produto",
            "Tempo estimado": "1 minuto",
            "Objetivo": "Entender a proposta.",
        },
        {
            "Passo": "2",
            "Aba": "Onboarding",
            "Tempo estimado": "2 minutos",
            "Objetivo": "Escolher perfil e rota.",
        },
        {
            "Passo": "3",
            "Aba": "Valuation",
            "Tempo estimado": "4 minutos",
            "Objetivo": "Ver o motor principal.",
        },
        {
            "Passo": "4",
            "Aba": "Relatórios",
            "Tempo estimado": "3 minutos",
            "Objetivo": "Ver entrega final.",
        },
        {
            "Passo": "5",
            "Aba": "Feedback Beta",
            "Tempo estimado": "3 minutos",
            "Objetivo": "Registrar percepção.",
        },
        {
            "Passo": "6",
            "Aba": "Oferta Beta",
            "Tempo estimado": "2 minutos",
            "Objetivo": "Entrar na lista de espera, caso tenha interesse.",
        },
    ]


def _injetar_css_navegacao() -> None:
    st.markdown(
        """
        <style>
            .nav-hero {
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

            .nav-eyebrow {
                color: #d6b56d;
                font-size: 0.78rem;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.35rem;
            }

            .nav-title {
                color: #f4f7fb;
                font-size: 2.1rem;
                font-weight: 900;
                margin-bottom: 0.45rem;
                line-height: 1.14;
            }

            .nav-subtitle {
                color: rgba(244, 247, 251, 0.76);
                font-size: 1rem;
                line-height: 1.62;
                max-width: 1080px;
            }

            .nav-card {
                padding: 1.1rem 1.15rem;
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.035);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.18);
                height: 100%;
            }

            .nav-card-label {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .nav-card-value {
                color: #f4f7fb;
                font-size: 1.2rem;
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .nav-card-note {
                color: rgba(244, 247, 251, 0.68);
                font-size: 0.87rem;
                line-height: 1.47;
            }

            .nav-highlight {
                padding: 0.95rem 1rem;
                border-radius: 16px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.92rem;
                line-height: 1.55;
                margin-bottom: 0.7rem;
            }

            .nav-disclaimer {
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
        <div class="nav-card">
            <div class="nav-card-label">{label}</div>
            <div class="nav-card-value">{value}</div>
            <div class="nav-card-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def renderizar_navegacao_simplificada() -> None:
    """
    Renderiza a central de navegação simplificada.
    """
    _injetar_css_navegacao()

    contexto = _extrair_contexto_navegacao()

    st.markdown(
        """
        <div class="nav-hero">
            <div class="nav-eyebrow">Mapa central do produto</div>
            <div class="nav-title">Navegação Simplificada</div>
            <div class="nav-subtitle">
                A Máquina de Preço-Teto ficou poderosa, mas agora precisa ser fácil de usar.
                Esta central organiza as abas em blocos claros e mostra o caminho ideal para cada objetivo.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="nav-highlight">
            Regra de UX: o usuário não deve precisar entender todas as abas para perceber valor.
            Ele precisa saber qual caminho seguir agora.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Contexto atual")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        _card("Análise ativa", _fmt_texto(contexto["empresa"]), f"Ticker: {contexto['ticker']}")

    with col_2:
        _card("Status", _fmt_texto(contexto["status"]), "Leitura educacional do valuation.")

    with col_3:
        _card("Score de tração", f"{contexto['score_tracao']}/100", "Sinal de validação do negócio.")

    with col_4:
        _card("Score de lançamento", f"{contexto['score_lancamento']}/100", "Preparação para beta.")

    st.divider()

    st.markdown("### Escolha o que você quer fazer")

    objetivo = st.selectbox(
        "Objetivo de navegação",
        OBJETIVOS_NAVEGACAO,
        key="navegacao_objetivo",
    )

    rota = _gerar_rota_por_objetivo(objetivo)

    st.session_state["resultado_navegacao_simplificada"] = {
        "objetivo": objetivo,
        "rota": rota,
        **contexto,
    }

    st.markdown("### Rota recomendada")

    st.dataframe(
        rota,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Blocos principais do produto")

    st.dataframe(
        _gerar_blocos_navegacao(),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Abas por prioridade")

    st.dataframe(
        _gerar_abas_por_prioridade(),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Fluxo mínimo para usuário beta")

    st.caption(
        "Este é o caminho mais simples para alguém testar o produto sem se perder."
    )

    st.dataframe(
        _gerar_fluxo_minimo_beta(),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Diagnóstico de UX")

    st.markdown(
        """
        **O app já tem profundidade suficiente. Agora o risco principal é excesso de complexidade.**

        Para a Fase 2, a experiência ideal é:

        1. Usuário comum vê primeiro: Produto, Navegação, Onboarding, Valuation, Relatórios e Feedback.
        2. Fundador vê também: Negócio, Marketing, Conteúdo, Landing Page e Lançamento.
        3. Investidor recorrente usa: Watchlist, Multiativos, Histórico e módulos por classe de ativo.
        4. As áreas estratégicas não devem distrair o usuário beta comum.
        """
    )

    st.markdown(
        """
        <div class="nav-disclaimer">
            <strong>Nota estratégica:</strong> esta central ainda não remove abas.
            Ela organiza a experiência. Na próxima versão, criaremos Modo Usuário Beta e Modo Fundador,
            para controlar quais áreas aparecem conforme o tipo de uso.
        </div>
        """,
        unsafe_allow_html=True,
    )