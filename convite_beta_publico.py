# convite_beta_publico.py

from datetime import datetime
from typing import Dict, List

import streamlit as st

from lista_espera_beta import renderizar_lista_espera_valoris


# ============================================================
# VALORIS
# v3.8.41 — Convite Beta Público
# ------------------------------------------------------------
# Esta tela cria uma página curta de convite para o beta.
#
# Objetivo:
# - ter uma versão mais direta que a landing completa
# - facilitar compartilhamento com amigos/leads
# - explicar quem deve testar
# - capturar interessados com CTA simples
# ============================================================


VERSAO_CONVITE_BETA_PUBLICO = "3.8.41"


QUEM_DEVE_ENTRAR = [
    "Quem já investe em ações e sente insegurança sobre preço.",
    "Quem quer entender melhor margem de segurança.",
    "Quem usa planilhas, mas quer uma leitura mais didática.",
    "Quem quer testar uma plataforma de valuation em construção.",
    "Quem aceita participar de um beta educacional sem promessa de retorno.",
]


QUEM_NAO_DEVE_ENTRAR = [
    "Quem procura call de compra ou venda.",
    "Quem quer promessa de lucro rápido.",
    "Quem não quer revisar premissas e riscos.",
    "Quem espera uma ferramenta finalizada e 100% automatizada agora.",
]


MENSAGENS_PRONTAS = {
    "curta": (
        "Estou testando a Valoris, uma plataforma educacional que ajuda investidores a auditar decisões "
        "antes de comprar ações. Ela combina valuation, margem de segurança, riscos fundamentais e relatório "
        "em linguagem simples. Quer entrar na lista beta?"
    ),
    "media": (
        "Estou abrindo a lista beta da Valoris. A ideia é ajudar investidores a não comprarem ação no impulso: "
        "você informa premissas, a plataforma calcula preço justo/preço-teto e o Auditor Valoris mostra pontos "
        "que podem enfraquecer a decisão. Não é recomendação de investimento, é uma ferramenta educacional "
        "para pensar melhor antes de comprar. Quer testar?"
    ),
    "fundador": (
        "Estou selecionando alguns usuários fundadores para testar a Valoris. O produto ainda está em beta, "
        "mas já entrega valuation, margem de segurança, Auditor Valoris e relatório premium. A proposta é construir "
        "com feedback real e validar uma possível oferta fundadora. Faz sentido eu te colocar na lista?"
    ),
}


def _injetar_css_convite() -> None:
    st.markdown(
        """
        <style>
            .convite-hero {
                padding: clamp(1.25rem, 3vw, 2rem);
                border-radius: 30px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    radial-gradient(circle at top left, rgba(214, 181, 109, 0.24), transparent 30%),
                    radial-gradient(circle at bottom right, rgba(36, 128, 91, 0.22), transparent 34%),
                    linear-gradient(135deg, rgba(8, 15, 27, 0.99), rgba(5, 9, 18, 0.99));
                box-shadow: 0 18px 55px rgba(0, 0, 0, 0.30);
                margin-bottom: 1rem;
            }

            .convite-eyebrow {
                color: #d6b56d;
                font-size: 0.74rem;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.38rem;
            }

            .convite-title {
                color: #f4f7fb;
                font-size: clamp(1.75rem, 5vw, 2.6rem);
                font-weight: 930;
                margin-bottom: 0.55rem;
                line-height: 1.05;
                letter-spacing: -0.055em;
            }

            .convite-subtitle {
                color: rgba(244, 247, 251, 0.76);
                font-size: clamp(0.95rem, 2.2vw, 1.08rem);
                line-height: 1.56;
                max-width: 980px;
            }

            .convite-grid {
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 0.85rem;
                margin: 1rem 0;
            }

            .convite-card {
                padding: 1.05rem 1.08rem;
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.034);
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.17);
            }

            .convite-card-title {
                color: #f4f7fb;
                font-size: 1.08rem;
                font-weight: 860;
                margin-bottom: 0.4rem;
            }

            .convite-card-text {
                color: rgba(244, 247, 251, 0.70);
                font-size: 0.90rem;
                line-height: 1.52;
            }

            .convite-note {
                padding: 0.95rem 1rem;
                border-radius: 16px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.92rem;
                line-height: 1.55;
                margin: 1rem 0;
            }

            @media (max-width: 900px) {
                .convite-grid {
                    grid-template-columns: 1fr;
                }

                .convite-hero {
                    border-radius: 22px;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _renderizar_hero() -> None:
    st.markdown(
        f"""
        <div class="convite-hero">
            <div class="convite-eyebrow">Valoris • v{VERSAO_CONVITE_BETA_PUBLICO}</div>
            <div class="convite-title">Você quer testar uma plataforma que audita decisões de investimento?</div>
            <div class="convite-subtitle">
                A Valoris está em beta. A proposta é ajudar investidores a analisar preço, valor,
                margem de segurança e riscos antes de comprar uma ação.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _renderizar_listas_qualificacao() -> None:
    st.markdown("### Para quem esse beta faz sentido")

    col_1, col_2 = st.columns(2)

    with col_1:
        st.markdown("#### Entre se você...")
        for item in QUEM_DEVE_ENTRAR:
            st.success(f"**{item}**")

    with col_2:
        st.markdown("#### Não entre se você procura...")
        for item in QUEM_NAO_DEVE_ENTRAR:
            st.warning(f"**{item}**")


def _renderizar_promessa() -> None:
    st.markdown(
        """
        <div class="convite-note">
            <strong>Promessa honesta:</strong> a Valoris não tenta prever o futuro nem entregar call.
            Ela ajuda você a organizar premissas, calcular zonas de preço e revisar pontos que podem
            tornar uma decisão frágil.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="convite-grid">', unsafe_allow_html=True)

    cards = [
        {
            "titulo": "Valuation guiado",
            "texto": "Preço justo, preço-teto e margem de segurança organizados em uma leitura clara.",
        },
        {
            "titulo": "Auditor Valoris",
            "texto": "Diagnóstico sobre riscos, limitações e pontos que ainda precisam de confirmação.",
        },
        {
            "titulo": "Relatório premium",
            "texto": "Documento em linguagem humana para revisar e estudar melhor a decisão.",
        },
        {
            "titulo": "Beta fundador",
            "texto": "Usuários iniciais ajudam a moldar o produto antes da versão premium madura.",
        },
    ]

    for card in cards:
        st.markdown(
            f"""
            <div class="convite-card">
                <div class="convite-card-title">{card["titulo"]}</div>
                <div class="convite-card-text">{card["texto"]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


def _renderizar_mensagens_prontas() -> None:
    st.markdown("### Mensagens para compartilhar")

    aba_curta, aba_media, aba_fundador = st.tabs(["Curta", "Média", "Fundador"])

    with aba_curta:
        st.text_area(
            "Mensagem curta",
            value=MENSAGENS_PRONTAS["curta"],
            height=150,
            key="convite_mensagem_curta",
        )

    with aba_media:
        st.text_area(
            "Mensagem média",
            value=MENSAGENS_PRONTAS["media"],
            height=190,
            key="convite_mensagem_media",
        )

    with aba_fundador:
        st.text_area(
            "Mensagem fundador",
            value=MENSAGENS_PRONTAS["fundador"],
            height=190,
            key="convite_mensagem_fundador",
        )


def renderizar_convite_beta_publico() -> None:
    """
    Renderiza a página pública curta de convite beta.
    """
    _injetar_css_convite()

    _renderizar_hero()

    _renderizar_promessa()

    st.divider()

    _renderizar_listas_qualificacao()

    st.divider()

    st.markdown("### Entrar na lista beta")

    renderizar_lista_espera_valoris(
        modo_admin=False,
        chave_contexto="convite_beta_publico",
    )

    st.divider()

    _renderizar_mensagens_prontas()

    st.info(
        "Aviso: a Valoris é educacional. Não representa recomendação de investimento e não promete rentabilidade."
    )


def executar_autoteste_convite_beta_publico() -> List[Dict[str, str]]:
    return [
        {
            "teste": "versao_convite",
            "status": "OK" if VERSAO_CONVITE_BETA_PUBLICO == "3.8.41" else "FALHA",
            "detalhe": VERSAO_CONVITE_BETA_PUBLICO,
        },
        {
            "teste": "qualificacao",
            "status": "OK" if len(QUEM_DEVE_ENTRAR) >= 4 and len(QUEM_NAO_DEVE_ENTRAR) >= 3 else "FALHA",
            "detalhe": f"{len(QUEM_DEVE_ENTRAR)} / {len(QUEM_NAO_DEVE_ENTRAR)}",
        },
        {
            "teste": "mensagens",
            "status": "OK" if len(MENSAGENS_PRONTAS) == 3 else "FALHA",
            "detalhe": str(len(MENSAGENS_PRONTAS)),
        },
    ]
