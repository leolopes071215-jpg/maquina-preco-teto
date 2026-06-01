# onboarding_usuario.py

from typing import Any, Dict, List

import streamlit as st


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v1.34 — Onboarding Inteligente e Jornada do Usuário
# ------------------------------------------------------------
# Esta tela guia o usuário dentro do produto.
# Objetivo:
# - reduzir confusão causada por muitas abas
# - mostrar o caminho ideal por perfil
# - acelerar percepção de valor
# - aumentar qualidade dos feedbacks beta
# ============================================================


PERFIS_ONBOARDING = [
    "Investidor iniciante",
    "Investidor intermediário",
    "Investidor avançado",
    "Estudante",
    "Criador de conteúdo financeiro",
    "Fundador/Gestor do produto",
]


OBJETIVOS_ONBOARDING = [
    "Entender rapidamente o produto",
    "Fazer uma análise de valuation",
    "Testar como usuário beta",
    "Organizar minha rotina de investimentos",
    "Avaliar se o produto é vendável",
    "Produzir conteúdo e captar interessados",
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


def _extrair_contexto_onboarding() -> Dict[str, Any]:
    valuation = _safe_get_dict("resultado_valuation")
    negocio = _safe_get_dict("resultado_dashboard_negocio")
    marketing = _safe_get_dict("resultado_marketing")
    landing = _safe_get_dict("resultado_landing_page")
    lancamento = _safe_get_dict("resultado_lancamento_beta")

    return {
        "empresa": valuation.get("empresa", "Nenhuma análise ativa"),
        "ticker": valuation.get("ticker", "N/D"),
        "tipo_analise": valuation.get("tipo_analise", "N/D"),
        "status": valuation.get("status", valuation.get("status_valuation", "N/D")),
        "score_tracao": negocio.get("score_tracao", 0),
        "score_lancamento": lancamento.get("score_lancamento", 0),
        "dor_dominante": marketing.get("dor_dominante", negocio.get("dor_mais_comum", "N/D")),
        "headline": landing.get("headline", "N/D"),
    }


def _gerar_rota_por_perfil(perfil: str, objetivo: str) -> List[Dict[str, str]]:
    if perfil == "Investidor iniciante":
        return [
            {
                "Ordem": "1",
                "Aba": "Produto",
                "O que fazer": "Entenda a proposta central da plataforma.",
                "Resultado esperado": "Saber que o app é educacional e não recomenda compra/venda.",
            },
            {
                "Ordem": "2",
                "Aba": "Início",
                "O que fazer": "Siga a jornada guiada para entender o fluxo.",
                "Resultado esperado": "Saber qual é o próximo passo dentro do app.",
            },
            {
                "Ordem": "3",
                "Aba": "Valuation",
                "O que fazer": "Veja preço justo, preço-teto e margem de segurança.",
                "Resultado esperado": "Entender que preço importa tanto quanto qualidade.",
            },
            {
                "Ordem": "4",
                "Aba": "Tese & Convicção",
                "O que fazer": "Leia e preencha a tese qualitativa.",
                "Resultado esperado": "Perceber que número sem tese é frágil.",
            },
            {
                "Ordem": "5",
                "Aba": "Feedback Beta",
                "O que fazer": "Registre sua opinião sobre clareza e utilidade.",
                "Resultado esperado": "Ajudar a melhorar o produto.",
            },
        ]

    if perfil == "Investidor intermediário":
        return [
            {
                "Ordem": "1",
                "Aba": "Valuation",
                "O que fazer": "Revise premissas e compare preço atual com preço-teto.",
                "Resultado esperado": "Avaliar se a zona de preço faz sentido.",
            },
            {
                "Ordem": "2",
                "Aba": "Checklist",
                "O que fazer": "Audite riscos, vieses e pontos fracos da análise.",
                "Resultado esperado": "Evitar decisões por narrativa ou otimismo.",
            },
            {
                "Ordem": "3",
                "Aba": "Painel Executivo",
                "O que fazer": "Veja a leitura integrada da análise.",
                "Resultado esperado": "Ter uma visão consolidada antes da decisão.",
            },
            {
                "Ordem": "4",
                "Aba": "Relatórios",
                "O que fazer": "Baixe um relatório de análise.",
                "Resultado esperado": "Registrar o raciocínio para revisar depois.",
            },
            {
                "Ordem": "5",
                "Aba": "Watchlist",
                "O que fazer": "Salve o ativo com status, prioridade e próxima ação.",
                "Resultado esperado": "Transformar análise em acompanhamento.",
            },
        ]

    if perfil == "Investidor avançado":
        return [
            {
                "Ordem": "1",
                "Aba": "Premissas",
                "O que fazer": "Revise lucro, FCF, ações, múltiplos e margem.",
                "Resultado esperado": "Testar robustez das premissas.",
            },
            {
                "Ordem": "2",
                "Aba": "Simulador",
                "O que fazer": "Teste cenários conservador, base e otimista.",
                "Resultado esperado": "Entender sensibilidade do valuation.",
            },
            {
                "Ordem": "3",
                "Aba": "Multiativos",
                "O que fazer": "Compare lógica para ações, FIIs e renda fixa.",
                "Resultado esperado": "Avaliar se a arquitetura multiativos faz sentido.",
            },
            {
                "Ordem": "4",
                "Aba": "Resumo da Decisão",
                "O que fazer": "Analise a decisão educacional consolidada.",
                "Resultado esperado": "Separar preço, risco, tese e convicção.",
            },
            {
                "Ordem": "5",
                "Aba": "Feedback Beta",
                "O que fazer": "Dê feedback técnico e crítico.",
                "Resultado esperado": "Melhorar o motor e a credibilidade do produto.",
            },
        ]

    if perfil == "Criador de conteúdo financeiro":
        return [
            {
                "Ordem": "1",
                "Aba": "Produto",
                "O que fazer": "Entenda o posicionamento da ferramenta.",
                "Resultado esperado": "Ter clareza da proposta para comunicar.",
            },
            {
                "Ordem": "2",
                "Aba": "Relatórios",
                "O que fazer": "Veja como transformar análise em material estruturado.",
                "Resultado esperado": "Identificar potencial para conteúdo educativo.",
            },
            {
                "Ordem": "3",
                "Aba": "Marketing",
                "O que fazer": "Analise copies, promessa e posicionamento.",
                "Resultado esperado": "Encontrar ângulos de comunicação.",
            },
            {
                "Ordem": "4",
                "Aba": "Conteúdo",
                "O que fazer": "Gere roteiros de reels e carrosséis.",
                "Resultado esperado": "Criar posts para atrair usuários beta.",
            },
            {
                "Ordem": "5",
                "Aba": "Landing Page",
                "O que fazer": "Use a copy para montar uma página externa.",
                "Resultado esperado": "Preparar captação de interessados.",
            },
        ]

    if perfil == "Fundador/Gestor do produto":
        return [
            {
                "Ordem": "1",
                "Aba": "Negócio",
                "O que fazer": "Veja score de tração, lista de espera e intenção de pagamento.",
                "Resultado esperado": "Saber se o produto está ganhando validação.",
            },
            {
                "Ordem": "2",
                "Aba": "Feedback Beta",
                "O que fazer": "Analise clareza, utilidade, confiança e dificuldades.",
                "Resultado esperado": "Descobrir onde o usuário trava.",
            },
            {
                "Ordem": "3",
                "Aba": "Oferta Beta",
                "O que fazer": "Veja plano, preço e dor mais citados.",
                "Resultado esperado": "Medir intenção de compra.",
            },
            {
                "Ordem": "4",
                "Aba": "Marketing",
                "O que fazer": "Defina comunicação e próximos conteúdos.",
                "Resultado esperado": "Criar demanda com base em dores reais.",
            },
            {
                "Ordem": "5",
                "Aba": "Lançamento",
                "O que fazer": "Acompanhe checklist e tarefas do beta.",
                "Resultado esperado": "Executar o lançamento controlado.",
            },
        ]

    return [
        {
            "Ordem": "1",
            "Aba": "Produto",
            "O que fazer": "Entenda o que é a plataforma.",
            "Resultado esperado": "Compreender a proposta geral.",
        },
        {
            "Ordem": "2",
            "Aba": "Valuation",
            "O que fazer": "Veja como o cálculo funciona.",
            "Resultado esperado": "Entender preço justo e preço-teto.",
        },
        {
            "Ordem": "3",
            "Aba": "Relatórios",
            "O que fazer": "Baixe um relatório de exemplo.",
            "Resultado esperado": "Ver a entrega final.",
        },
        {
            "Ordem": "4",
            "Aba": "Feedback Beta",
            "O que fazer": "Registre sua opinião.",
            "Resultado esperado": "Ajudar a melhorar o produto.",
        },
    ]


def _gerar_roteiro_15_minutos() -> List[Dict[str, str]]:
    return [
        {
            "Tempo": "0–2 min",
            "Aba": "Produto",
            "Ação": "Leia a proposta central.",
            "Objetivo": "Entender o que o app faz.",
        },
        {
            "Tempo": "2–5 min",
            "Aba": "Valuation",
            "Ação": "Veja preço atual, preço justo e preço-teto.",
            "Objetivo": "Entender a lógica principal.",
        },
        {
            "Tempo": "5–8 min",
            "Aba": "Tese & Convicção",
            "Ação": "Observe como a tese qualitativa entra na análise.",
            "Objetivo": "Perceber que não é só número.",
        },
        {
            "Tempo": "8–11 min",
            "Aba": "Checklist",
            "Ação": "Revise os riscos e erros comuns.",
            "Objetivo": "Ver proteção contra decisões ruins.",
        },
        {
            "Tempo": "11–13 min",
            "Aba": "Relatórios",
            "Ação": "Baixe ou visualize um relatório.",
            "Objetivo": "Entender a entrega final.",
        },
        {
            "Tempo": "13–15 min",
            "Aba": "Feedback Beta",
            "Ação": "Preencha o feedback.",
            "Objetivo": "Registrar percepção real do usuário.",
        },
    ]


def _gerar_roteiro_completo() -> List[Dict[str, str]]:
    return [
        {
            "Etapa": "1",
            "Aba": "Produto",
            "Ação": "Entender promessa, público e proposta de valor.",
        },
        {
            "Etapa": "2",
            "Aba": "Início",
            "Ação": "Seguir a jornada guiada.",
        },
        {
            "Etapa": "3",
            "Aba": "Premissas",
            "Ação": "Revisar dados financeiros e múltiplos usados.",
        },
        {
            "Etapa": "4",
            "Aba": "Valuation",
            "Ação": "Analisar preço justo, preço-teto e margem.",
        },
        {
            "Etapa": "5",
            "Aba": "Simulador",
            "Ação": "Testar cenários diferentes.",
        },
        {
            "Etapa": "6",
            "Aba": "Tese & Convicção",
            "Ação": "Avaliar tese, riscos e fundamentos.",
        },
        {
            "Etapa": "7",
            "Aba": "Checklist",
            "Ação": "Auditar erros de análise.",
        },
        {
            "Etapa": "8",
            "Aba": "Painel Executivo",
            "Ação": "Ler a visão integrada.",
        },
        {
            "Etapa": "9",
            "Aba": "Resumo da Decisão",
            "Ação": "Consolidar leitura educacional.",
        },
        {
            "Etapa": "10",
            "Aba": "Relatórios",
            "Ação": "Baixar relatório para revisão futura.",
        },
        {
            "Etapa": "11",
            "Aba": "Watchlist",
            "Ação": "Salvar ativo e definir próxima ação.",
        },
        {
            "Etapa": "12",
            "Aba": "Feedback Beta",
            "Ação": "Dar feedback sobre experiência e valor percebido.",
        },
    ]


def _gerar_checklist_primeira_experiencia() -> List[Dict[str, str]]:
    return [
        {
            "Pergunta": "Entendi o que o produto faz em menos de 1 minuto?",
            "Sinal positivo": "Consigo explicar a proposta com minhas palavras.",
        },
        {
            "Pergunta": "Entendi que o app é educacional e não recomenda compra/venda?",
            "Sinal positivo": "Não confundi o status com recomendação profissional.",
        },
        {
            "Pergunta": "Encontrei rapidamente onde fazer valuation?",
            "Sinal positivo": "A aba Valuation ficou clara.",
        },
        {
            "Pergunta": "Percebi valor no relatório?",
            "Sinal positivo": "Eu salvaria ou revisaria o relatório depois.",
        },
        {
            "Pergunta": "A Watchlist parece útil para acompanhar ativos?",
            "Sinal positivo": "Eu usaria semanalmente ou mensalmente.",
        },
        {
            "Pergunta": "Eu pagaria por uma versão melhorada?",
            "Sinal positivo": "Sim ou talvez, dependendo do preço e dos dados automáticos.",
        },
        {
            "Pergunta": "Onde travei?",
            "Sinal positivo": "Consigo apontar uma melhoria clara.",
        },
    ]


def _injetar_css_onboarding() -> None:
    st.markdown(
        """
        <style>
            .onb-hero {
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

            .onb-eyebrow {
                color: #d6b56d;
                font-size: 0.78rem;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.35rem;
            }

            .onb-title {
                color: #f4f7fb;
                font-size: 2.1rem;
                font-weight: 900;
                margin-bottom: 0.45rem;
                line-height: 1.14;
            }

            .onb-subtitle {
                color: rgba(244, 247, 251, 0.76);
                font-size: 1rem;
                line-height: 1.62;
                max-width: 1080px;
            }

            .onb-card {
                padding: 1.1rem 1.15rem;
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.035);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.18);
                height: 100%;
            }

            .onb-card-label {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .onb-card-value {
                color: #f4f7fb;
                font-size: 1.22rem;
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .onb-card-note {
                color: rgba(244, 247, 251, 0.68);
                font-size: 0.87rem;
                line-height: 1.47;
            }

            .onb-highlight {
                padding: 0.95rem 1rem;
                border-radius: 16px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.92rem;
                line-height: 1.55;
                margin-bottom: 0.7rem;
            }

            .onb-disclaimer {
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
        <div class="onb-card">
            <div class="onb-card-label">{label}</div>
            <div class="onb-card-value">{value}</div>
            <div class="onb-card-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def renderizar_onboarding_usuario() -> None:
    """
    Renderiza o onboarding inteligente do usuário.
    """
    _injetar_css_onboarding()

    contexto = _extrair_contexto_onboarding()

    st.markdown(
        """
        <div class="onb-hero">
            <div class="onb-eyebrow">Primeira experiência guiada</div>
            <div class="onb-title">Onboarding Inteligente da Máquina de Preço-Teto</div>
            <div class="onb-subtitle">
                Use esta área para saber por onde começar. A plataforma tem muitos módulos,
                então o onboarding cria uma jornada de uso conforme o perfil do usuário e o objetivo do teste.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="onb-highlight">
            O objetivo do onboarding é simples: fazer o usuário perceber valor rápido,
            sem se perder entre muitas abas.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Contexto atual")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        _card("Análise ativa", _fmt_texto(contexto["empresa"]), "Empresa atualmente selecionada.")

    with col_2:
        _card("Ticker", _fmt_texto(contexto["ticker"]), "Ativo em análise.")

    with col_3:
        _card("Status", _fmt_texto(contexto["status"]), "Status educacional do valuation.")

    with col_4:
        _card("Tipo de análise", _fmt_texto(contexto["tipo_analise"]), "Modo atual usado no app.")

    col_5, col_6, col_7 = st.columns(3)

    with col_5:
        _card("Score de tração", f"{contexto['score_tracao']}/100", "Sinal de validação do negócio.")

    with col_6:
        _card("Score de lançamento", f"{contexto['score_lancamento']}/100", "Preparação para beta controlado.")

    with col_7:
        _card("Dor dominante", _fmt_texto(contexto["dor_dominante"]), "Base da comunicação do produto.")

    st.divider()

    st.markdown("### Escolha sua jornada")

    col_a, col_b = st.columns(2)

    with col_a:
        perfil = st.selectbox(
            "Qual é o seu perfil?",
            PERFIS_ONBOARDING,
            key="onboarding_perfil",
        )

    with col_b:
        objetivo = st.selectbox(
            "Qual é seu objetivo agora?",
            OBJETIVOS_ONBOARDING,
            key="onboarding_objetivo",
        )

    rota = _gerar_rota_por_perfil(perfil, objetivo)

    st.session_state["resultado_onboarding"] = {
        "perfil": perfil,
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

    st.markdown("### Roteiro rápido: 15 minutos")

    st.caption(
        "Ideal para usuários beta que vão testar o produto pela primeira vez."
    )

    st.dataframe(
        _gerar_roteiro_15_minutos(),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Roteiro completo de análise")

    st.caption(
        "Ideal para usar a plataforma como ferramenta real de estudo e organização."
    )

    st.dataframe(
        _gerar_roteiro_completo(),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Checklist da primeira experiência")

    st.dataframe(
        _gerar_checklist_primeira_experiencia(),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Como transformar o app em rotina")

    rotina = [
        {
            "Frequência": "Toda nova análise",
            "Ação": "Preencher premissas, valuation, tese, checklist e relatório.",
        },
        {
            "Frequência": "Semanal",
            "Ação": "Revisar Watchlist e atualizar próxima ação dos ativos acompanhados.",
        },
        {
            "Frequência": "Mensal",
            "Ação": "Revisar relatórios antigos e comparar mudanças de tese/preço.",
        },
        {
            "Frequência": "Trimestral",
            "Ação": "Atualizar dados financeiros após resultados das empresas.",
        },
        {
            "Frequência": "Antes de qualquer compra",
            "Ação": "Checar preço-teto, tese, riscos e margem de segurança.",
        },
    ]

    st.dataframe(
        rotina,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### O que o usuário não deve fazer")

    st.markdown(
        """
        - Não tratar o status educacional como recomendação de compra.
        - Não usar dados fictícios para tomar decisão real.
        - Não confiar em valuation sem revisar premissas.
        - Não ignorar riscos qualitativos.
        - Não comparar ações, FIIs e renda fixa como se fossem iguais.
        - Não usar o app como substituto de estudo, responsabilidade e julgamento próprio.
        """
    )

    st.markdown(
        """
        <div class="onb-disclaimer">
            <strong>Nota de onboarding:</strong> esta jornada existe para orientar o uso do produto.
            A Máquina de Preço-Teto é uma plataforma educacional. A decisão final sobre qualquer ativo
            continua sendo responsabilidade do usuário.
        </div>
        """,
        unsafe_allow_html=True,
    )