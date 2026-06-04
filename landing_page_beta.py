# landing_page_beta.py

from datetime import datetime
from typing import Any, Dict, List

import streamlit as st

from lista_espera_beta import renderizar_lista_espera_valoris
from demo_guiada_valoris import renderizar_demo_guiada_valoris
from trilha_educativa_valoris import renderizar_trilha_educativa_valoris
from copiloto_valoris import renderizar_copiloto_valoris
from analytics_publico_valoris import registrar_visualizacao_unica, registrar_evento_publico


# ============================================================
# VALORIS
# v3.8.47 — Landing Page com Copiloto Valoris
# ------------------------------------------------------------
# Esta tela apresenta a Valoris para usuários públicos.
#
# Objetivo:
# - explicar a proposta em poucos segundos
# - diferenciar a Valoris de calculadoras comuns
# - comunicar dor, método, benefícios e limites
# - capturar leads para o beta fundador
# - preparar aquisição de usuários e monetização manual
# ============================================================


VERSAO_LANDING_PAGE_BETA = "3.8.47"


COPY_LANDING = {
    "eyebrow": "Valoris Beta",
    "headline": "Pare de comprar ação no impulso.",
    "subheadline": (
        "A Valoris ajuda você a auditar decisões de investimento antes da compra, "
        "combinando valuation, margem de segurança, riscos fundamentais e linguagem simples."
    ),
    "cta": "Entrar na lista beta",
    "disclaimer": (
        "A Valoris é uma ferramenta educacional. Não representa recomendação de compra, venda "
        "ou manutenção de investimentos."
    ),
}


DORES_USUARIO = [
    {
        "titulo": "Você não sabe se está pagando caro",
        "texto": (
            "A maior dúvida do investidor não é apenas encontrar boas empresas. "
            "É saber se o preço atual ainda faz sentido."
        ),
    },
    {
        "titulo": "As ferramentas mostram números, mas não explicam a decisão",
        "texto": (
            "Preço justo, múltiplos e dividendos podem parecer precisos, mas continuam perigosos "
            "quando as premissas estão frágeis."
        ),
    },
    {
        "titulo": "O investidor erra mais no raciocínio do que na fórmula",
        "texto": (
            "Ansiedade, narrativa, dividendo alto, notícia recente e medo de perder oportunidade "
            "podem contaminar a decisão."
        ),
    },
]


COMO_FUNCIONA = [
    {
        "numero": "01",
        "titulo": "Organize as premissas",
        "texto": "Você informa lucro, fluxo de caixa, múltiplos, margem de segurança e preço atual.",
    },
    {
        "numero": "02",
        "titulo": "Calcule valor e preço-teto",
        "texto": "A Valoris estima preço justo e preço-teto conservador com base nas premissas usadas.",
    },
    {
        "numero": "03",
        "titulo": "Audite a decisão",
        "texto": "O Auditor Valoris mostra o que sustenta, enfraquece ou ainda limita a análise.",
    },
    {
        "numero": "04",
        "titulo": "Baixe um relatório",
        "texto": "Você recebe uma leitura clara em linguagem humana, sem tratar o número como verdade absoluta.",
    },
]


DIFERENCIAIS = [
    {
        "titulo": "Não é só uma calculadora",
        "texto": "A Valoris não para no preço-teto. Ela explica o que pode estar errado na decisão.",
    },
    {
        "titulo": "Camadas de profundidade",
        "texto": "Leigo, intermediário e avançado enxergam a mesma análise em níveis diferentes de complexidade.",
    },
    {
        "titulo": "Auditor de riscos",
        "texto": "A plataforma separa o que já consegue verificar do que ainda exige confirmação externa.",
    },
    {
        "titulo": "Relatório premium",
        "texto": "A análise vira um documento organizado para revisar, comparar e estudar melhor depois.",
    },
    {
        "titulo": "Construída com feedback real",
        "texto": "O produto está sendo moldado com testes, lista de espera e validação de usuários.",
    },
    {
        "titulo": "Sem promessa de lucro fácil",
        "texto": "A proposta é melhorar o raciocínio, não vender sinal, call ou recomendação milagrosa.",
    },
]


PLANOS_LANDING = [
    {
        "badge": "Conhecer",
        "nome": "Gratuito",
        "preco": "R$ 0",
        "texto": "Teste a proposta, veja a análise demonstrativa e entre na lista beta.",
    },
    {
        "badge": "Beta",
        "nome": "Fundador",
        "preco": "R$ 97",
        "texto": "Condição simbólica para participar cedo, testar versões e ajudar a moldar a plataforma.",
    },
    {
        "badge": "Futuro",
        "nome": "Premium",
        "preco": "A definir",
        "texto": "Automação por ticker, histórico, alertas, auditorias avançadas e relatórios mais completos.",
    },
]


FAQ_LANDING = [
    {
        "pergunta": "A Valoris recomenda ações?",
        "resposta": (
            "Não. A Valoris é educacional. Ela organiza premissas, calcula referências de valor "
            "e ajuda a revisar riscos antes de uma decisão."
        ),
    },
    {
        "pergunta": "A ferramenta garante que vou ganhar dinheiro?",
        "resposta": (
            "Não. Nenhuma ferramenta honesta garante retorno. A proposta é reduzir decisões impulsivas "
            "e melhorar a qualidade da análise."
        ),
    },
    {
        "pergunta": "Ela já busca dados automaticamente?",
        "resposta": (
            "A versão atual ainda está em beta e trabalha principalmente com premissas informadas pelo usuário. "
            "A automação por ticker é uma etapa futura do roadmap."
        ),
    },
    {
        "pergunta": "Para quem a Valoris serve?",
        "resposta": (
            "Serve para investidores iniciantes, intermediários e avançados que querem pensar melhor antes "
            "de comprar ações e documentar suas decisões."
        ),
    },
    {
        "pergunta": "Por que entrar no beta?",
        "resposta": (
            "Porque os usuários fundadores ajudam a moldar o produto, recebem acesso antecipado e participam "
            "da evolução antes da versão premium madura."
        ),
    },
]


JORNADAS_INTERATIVAS = {
    "Iniciante": {
        "titulo": "Você precisa de clareza antes de complexidade.",
        "texto": (
            "A Valoris deve traduzir a análise para uma leitura simples: preço atual, preço-teto, "
            "zona de decisão e próximos passos sem economês."
        ),
        "foco": "Entender se o preço exige oportunidade, atenção ou paciência.",
        "progresso": 34,
    },
    "Intermediário": {
        "titulo": "Você precisa auditar premissas.",
        "texto": (
            "A Valoris deve mostrar se o número está sustentado por lucro, caixa, margem de segurança "
            "e riscos que podem distorcer a tese."
        ),
        "foco": "Comparar valuation, relatório, checklist e Auditor Valoris.",
        "progresso": 67,
    },
    "Avançado": {
        "titulo": "Você precisa de controle e transparência.",
        "texto": (
            "A Valoris deve abrir premissas, pesos, múltiplos, limites do modelo e pontos ainda não verificados."
        ),
        "foco": "Estressar cenários, revisar tese e preparar automação futura por ticker.",
        "progresso": 92,
    },
}


def _injetar_css_landing() -> None:
    st.markdown(
        """
        <style>
            .lp-hero {
                padding: clamp(1.35rem, 3.5vw, 2.35rem);
                border-radius: 34px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    radial-gradient(circle at top left, rgba(214, 181, 109, 0.26), transparent 30%),
                    radial-gradient(circle at bottom right, rgba(36, 128, 91, 0.25), transparent 34%),
                    linear-gradient(135deg, rgba(8, 15, 27, 0.99), rgba(5, 9, 18, 0.99));
                box-shadow: 0 22px 70px rgba(0, 0, 0, 0.34);
                margin-bottom: 1.1rem;
            }

            .lp-eyebrow {
                color: #d6b56d;
                font-size: 0.75rem;
                letter-spacing: 0.15em;
                text-transform: uppercase;
                font-weight: 900;
                margin-bottom: 0.42rem;
            }

            .lp-title {
                color: #f4f7fb;
                font-size: clamp(2.0rem, 7vw, 4rem);
                font-weight: 950;
                line-height: 0.98;
                letter-spacing: -0.065em;
                max-width: 980px;
                margin-bottom: 0.75rem;
            }

            .lp-subtitle {
                color: rgba(244, 247, 251, 0.76);
                font-size: clamp(1rem, 2.35vw, 1.16rem);
                line-height: 1.58;
                max-width: 960px;
                margin-bottom: 1rem;
            }

            .lp-cta-row {
                display: flex;
                gap: 0.75rem;
                flex-wrap: wrap;
                align-items: center;
                margin-top: 1rem;
            }

            .lp-pill {
                display: inline-block;
                padding: 0.42rem 0.72rem;
                border-radius: 999px;
                border: 1px solid rgba(214, 181, 109, 0.26);
                background: rgba(214, 181, 109, 0.08);
                color: #d6b56d;
                font-weight: 820;
                font-size: 0.78rem;
            }

            .lp-section-title {
                color: #f4f7fb;
                font-size: clamp(1.35rem, 3.5vw, 2rem);
                font-weight: 900;
                letter-spacing: -0.045em;
                margin: 1.4rem 0 0.45rem 0;
            }

            .lp-section-subtitle {
                color: rgba(244, 247, 251, 0.68);
                font-size: 0.96rem;
                line-height: 1.55;
                max-width: 900px;
                margin-bottom: 0.8rem;
            }

            .lp-grid-3 {
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 0.85rem;
                margin: 1rem 0;
            }

            .lp-grid-2 {
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 0.85rem;
                margin: 1rem 0;
            }

            .lp-card {
                padding: 1.05rem 1.08rem;
                border-radius: 23px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background:
                    radial-gradient(circle at top right, rgba(214, 181, 109, 0.07), transparent 30%),
                    rgba(255, 255, 255, 0.034);
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.17);
                height: 100%;
            }

            .lp-card-kicker {
                color: #d6b56d;
                font-size: 0.73rem;
                letter-spacing: 0.11em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.42rem;
            }

            .lp-card-title {
                color: #f4f7fb;
                font-size: 1.08rem;
                font-weight: 850;
                margin-bottom: 0.35rem;
                letter-spacing: -0.025em;
            }

            .lp-card-text {
                color: rgba(244, 247, 251, 0.69);
                font-size: 0.90rem;
                line-height: 1.52;
            }

            .lp-price {
                color: #f4f7fb;
                font-size: 1.55rem;
                font-weight: 950;
                letter-spacing: -0.04em;
                margin: 0.35rem 0;
            }

            .lp-note {
                padding: 1rem 1.05rem;
                border-radius: 18px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.80);
                font-size: 0.92rem;
                line-height: 1.55;
                margin: 1rem 0;
            }

            .lp-disclaimer {
                padding: 0.95rem 1rem;
                border-radius: 16px;
                background: rgba(74, 144, 226, 0.08);
                border: 1px solid rgba(74, 144, 226, 0.18);
                color: rgba(244, 247, 251, 0.76);
                font-size: 0.88rem;
                line-height: 1.50;
                margin-top: 1rem;
            }


            .lp-interactive-panel {
                padding: 1.05rem 1.08rem;
                border-radius: 24px;
                border: 1px solid rgba(214, 181, 109, 0.16);
                background:
                    radial-gradient(circle at top left, rgba(214, 181, 109, 0.10), transparent 34%),
                    rgba(255, 255, 255, 0.035);
                box-shadow: 0 12px 34px rgba(0, 0, 0, 0.18);
                margin: 1rem 0;
            }

            .lp-interactive-title {
                color: #f4f7fb;
                font-size: 1.18rem;
                font-weight: 880;
                letter-spacing: -0.03em;
                margin-bottom: 0.38rem;
            }

            .lp-interactive-text {
                color: rgba(244, 247, 251, 0.72);
                font-size: 0.92rem;
                line-height: 1.52;
                margin-bottom: 0.75rem;
            }

            .lp-progress-wrap {
                width: 100%;
                height: 10px;
                border-radius: 999px;
                background: rgba(148, 163, 184, 0.16);
                overflow: hidden;
                margin-top: 0.55rem;
            }

            .lp-progress-fill {
                height: 100%;
                border-radius: 999px;
                background: linear-gradient(90deg, #d6b56d, #24805b);
            }

            @media (max-width: 900px) {
                .lp-grid-3,
                .lp-grid-2 {
                    grid-template-columns: 1fr;
                }

                .lp-hero {
                    border-radius: 24px;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _renderizar_hero() -> None:
    st.markdown(
        f"""
        <div class="lp-hero">
            <div class="lp-eyebrow">{COPY_LANDING["eyebrow"]} • v{VERSAO_LANDING_PAGE_BETA}</div>
            <div class="lp-title">{COPY_LANDING["headline"]}</div>
            <div class="lp-subtitle">{COPY_LANDING["subheadline"]}</div>
            <div class="lp-cta-row">
                <span class="lp-pill">Valuation</span>
                <span class="lp-pill">Auditor de decisão</span>
                <span class="lp-pill">Margem de segurança</span>
                <span class="lp-pill">Relatório premium</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _renderizar_jornada_interativa() -> None:
    st.markdown('<div class="lp-section-title">Escolha como você quer enxergar a Valoris</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="lp-section-subtitle">A experiência precisa se adaptar ao nível do investidor, não obrigar todo mundo a encarar a mesma complexidade.</div>',
        unsafe_allow_html=True,
    )

    perfil = st.radio(
        "Qual perfil mais parece com você hoje?",
        ["Iniciante", "Intermediário", "Avançado"],
        horizontal=True,
        key="landing_perfil_interativo_valoris",
    )

    jornada = JORNADAS_INTERATIVAS[perfil]

    registrar_evento_publico(
        evento="demo_interacao",
        origem="landing_page",
        contexto="perfil_interativo",
        perfil=perfil,
        detalhe=f"Perfil selecionado na landing: {perfil}",
    )

    st.markdown(
        f"""
        <div class="lp-interactive-panel">
            <div class="lp-card-kicker">Modo {perfil}</div>
            <div class="lp-interactive-title">{jornada["titulo"]}</div>
            <div class="lp-interactive-text">{jornada["texto"]}</div>
            <div class="lp-card-text"><strong>Foco da experiência:</strong> {jornada["foco"]}</div>
            <div class="lp-progress-wrap">
                <div class="lp-progress-fill" style="width: {jornada["progresso"]}%;"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )



def _renderizar_secao_dores() -> None:
    st.markdown('<div class="lp-section-title">O problema não é só calcular. É decidir bem.</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="lp-section-subtitle">O investidor comum encontra muitos números, mas pouca clareza sobre a qualidade da decisão.</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="lp-grid-3">', unsafe_allow_html=True)

    for dor in DORES_USUARIO:
        st.markdown(
            f"""
            <div class="lp-card">
                <div class="lp-card-title">{dor["titulo"]}</div>
                <div class="lp-card-text">{dor["texto"]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


def _renderizar_como_funciona() -> None:
    st.markdown('<div class="lp-section-title">Como a Valoris funciona</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="lp-section-subtitle">A Valoris transforma a análise em uma jornada: premissa, preço, auditoria e relatório.</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="lp-grid-2">', unsafe_allow_html=True)

    for passo in COMO_FUNCIONA:
        st.markdown(
            f"""
            <div class="lp-card">
                <div class="lp-card-kicker">{passo["numero"]}</div>
                <div class="lp-card-title">{passo["titulo"]}</div>
                <div class="lp-card-text">{passo["texto"]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


def _renderizar_diferenciais() -> None:
    st.markdown('<div class="lp-section-title">Por que a Valoris é diferente</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="lp-section-subtitle">Calculadoras entregam números. A Valoris quer auditar a qualidade da decisão.</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="lp-grid-3">', unsafe_allow_html=True)

    for diferencial in DIFERENCIAIS:
        st.markdown(
            f"""
            <div class="lp-card">
                <div class="lp-card-title">{diferencial["titulo"]}</div>
                <div class="lp-card-text">{diferencial["texto"]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


def _renderizar_planos() -> None:
    st.markdown('<div class="lp-section-title">Entre agora como usuário beta</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="lp-section-subtitle">A versão beta serve para testar, aprender, validar e construir a Valoris com usuários reais.</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="lp-grid-3">', unsafe_allow_html=True)

    for plano in PLANOS_LANDING:
        st.markdown(
            f"""
            <div class="lp-card">
                <div class="lp-card-kicker">{plano["badge"]}</div>
                <div class="lp-card-title">{plano["nome"]}</div>
                <div class="lp-price">{plano["preco"]}</div>
                <div class="lp-card-text">{plano["texto"]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        """
        <div class="lp-note">
            <strong>Estratégia atual:</strong> a Valoris ainda não deve depender de checkout automático.
            O foco agora é lista beta, feedback real e venda manual controlada para poucos usuários fundadores.
        </div>
        """,
        unsafe_allow_html=True,
    )


def _renderizar_faq() -> None:
    st.markdown('<div class="lp-section-title">Perguntas frequentes</div>', unsafe_allow_html=True)

    for item in FAQ_LANDING:
        with st.expander(item["pergunta"], expanded=False):
            st.write(item["resposta"])


def _renderizar_cta() -> None:
    st.markdown('<div class="lp-section-title">Entre na lista beta</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="lp-section-subtitle">Deixe seu contato para testar novas versões, receber melhorias e participar da construção do produto.</div>',
        unsafe_allow_html=True,
    )

    renderizar_lista_espera_valoris(
        modo_admin=False,
        chave_contexto="landing_page_beta",
    )


def renderizar_landing_page_beta() -> None:
    """
    Renderiza a landing page pública de conversão da Valoris.
    """
    registrar_visualizacao_unica(
        chave="landing_page_beta",
        evento="landing_visualizada",
        origem="landing_page",
        contexto="renderizacao",
        detalhe="Landing page pública visualizada.",
    )

    _injetar_css_landing()

    _renderizar_hero()

    _renderizar_jornada_interativa()

    st.divider()

    renderizar_copiloto_valoris(
        modo_compacto=True,
        mostrar_cta=False,
        chave_contexto="landing_page",
    )

    st.divider()

    renderizar_demo_guiada_valoris(
        modo_compacto=True,
        mostrar_cta=False,
        chave_contexto="landing_page",
    )

    st.divider()

    renderizar_trilha_educativa_valoris(
        modo_compacto=True,
        mostrar_cta=False,
        chave_contexto="landing_page",
    )

    st.divider()

    _renderizar_secao_dores()

    st.divider()

    _renderizar_como_funciona()

    st.divider()

    _renderizar_diferenciais()

    st.divider()

    _renderizar_planos()

    st.divider()

    _renderizar_faq()

    st.divider()

    _renderizar_cta()

    st.markdown(
        f"""
        <div class="lp-disclaimer">
            <strong>Aviso educacional:</strong> {COPY_LANDING["disclaimer"]}
            A responsabilidade pela decisão continua sendo do investidor.
        </div>
        """,
        unsafe_allow_html=True,
    )


def executar_autoteste_landing_page_beta() -> List[Dict[str, str]]:
    return [
        {
            "teste": "versao_landing",
            "status": "OK" if VERSAO_LANDING_PAGE_BETA == "3.8.47" else "FALHA",
            "detalhe": VERSAO_LANDING_PAGE_BETA,
        },
        {
            "teste": "dores_usuario",
            "status": "OK" if len(DORES_USUARIO) >= 3 else "FALHA",
            "detalhe": str(len(DORES_USUARIO)),
        },
        {
            "teste": "faq_landing",
            "status": "OK" if len(FAQ_LANDING) >= 4 else "FALHA",
            "detalhe": str(len(FAQ_LANDING)),
        },
    ]
