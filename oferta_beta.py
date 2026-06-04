# oferta_beta.py

from datetime import datetime
from typing import Any, Dict, List

import streamlit as st

from lista_espera_beta import (
    carregar_leads_lista_espera,
    gerar_csv_lista_espera,
    renderizar_lista_espera_valoris,
)


# ============================================================
# VALORIS
# v3.8.40.2 — Oferta Beta Fundador com chaves únicas
# ------------------------------------------------------------
# Esta tela transforma a lista de espera em uma primeira oferta
# controlada, honesta e testável.
#
# Objetivo:
# - apresentar a oferta Beta Fundador com clareza
# - separar gratuito, beta fundador e premium futuro
# - mostrar benefícios sem prometer rentabilidade
# - apoiar teste manual de monetização
# - manter dados locais fora do Git
# ============================================================


VERSAO_OFERTA_BETA = "3.8.40.2"


OFERTA_FUNDADOR = {
    "nome": "Valoris Beta Fundador",
    "preco_unico": "R$ 97",
    "preco_mensal": "R$ 19,90/mês",
    "promessa": (
        "Ajudar investidores a auditar decisões antes de comprar ações, usando valuation, "
        "margem de segurança, relatório e revisão de riscos fundamentais."
    ),
    "condicao": (
        "Acesso antecipado para acompanhar a evolução do produto, testar novas versões e ajudar "
        "a moldar a plataforma."
    ),
    "aviso": (
        "A Valoris é educacional. Não recomenda compra, venda ou manutenção de ativos e não promete rentabilidade."
    ),
}


# ============================================================
# Compatibilidade com módulos antigos
# ------------------------------------------------------------
# Alguns módulos do projeto, como dashboard_negocio.py, ainda
# importam carregar_lista_espera diretamente de oferta_beta.py.
# Na v3.8.39 a persistência foi movida para lista_espera_beta.py.
# Estas funções preservam a compatibilidade sem quebrar imports.
# ============================================================


def carregar_lista_espera() -> List[Dict[str, str]]:
    """
    Compatibilidade: retorna os leads da lista de espera.

    Mantido porque módulos antigos ainda executam:
    from oferta_beta import carregar_lista_espera
    """
    return carregar_leads_lista_espera()


def exportar_lista_espera_csv() -> str:
    """
    Compatibilidade: retorna o CSV bruto da lista de espera.
    """
    return gerar_csv_lista_espera()




def _safe_str(valor: Any, padrao: str = "N/D") -> str:
    if valor is None or valor == "":
        return padrao

    return str(valor)


def _contar_por_texto(leads: List[Dict[str, str]], campo: str, termo: str) -> int:
    termo_normalizado = termo.lower()

    return len(
        [
            lead for lead in leads
            if termo_normalizado in _safe_str(lead.get(campo, ""), "").lower()
        ]
    )


def _mais_frequente(leads: List[Dict[str, str]], campo: str) -> str:
    contagem: Dict[str, int] = {}

    for lead in leads:
        valor = _safe_str(lead.get(campo, ""), "").strip()

        if not valor:
            continue

        contagem[valor] = contagem.get(valor, 0) + 1

    if not contagem:
        return "N/D"

    return sorted(contagem.items(), key=lambda item: item[1], reverse=True)[0][0]


def _calcular_metricas_beta() -> Dict[str, Any]:
    leads = carregar_leads_lista_espera()

    return {
        "total": len(leads),
        "pagariam_agora": _contar_por_texto(leads, "pagaria_agora", "sim"),
        "talvez_pagariam": _contar_por_texto(leads, "pagaria_agora", "talvez"),
        "dor_mais_comum": _mais_frequente(leads, "principal_dor"),
        "plano_mais_citado": _mais_frequente(leads, "plano_interesse"),
        "preco_mais_citado": _mais_frequente(leads, "preco_aceitavel"),
    }


def _injetar_css_oferta_beta() -> None:
    st.markdown(
        """
        <style>
            .oferta-fundador-hero {
                padding: clamp(1.25rem, 3vw, 2rem);
                border-radius: 30px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    radial-gradient(circle at top left, rgba(214, 181, 109, 0.24), transparent 30%),
                    radial-gradient(circle at bottom right, rgba(36, 128, 91, 0.24), transparent 34%),
                    linear-gradient(135deg, rgba(8, 15, 27, 0.99), rgba(5, 9, 18, 0.99));
                box-shadow: 0 18px 55px rgba(0, 0, 0, 0.30);
                margin-bottom: 1rem;
            }

            .oferta-fundador-eyebrow {
                color: #d6b56d;
                font-size: 0.74rem;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.38rem;
            }

            .oferta-fundador-title {
                color: #f4f7fb;
                font-size: clamp(1.75rem, 5vw, 2.45rem);
                font-weight: 920;
                margin-bottom: 0.55rem;
                line-height: 1.08;
                letter-spacing: -0.045em;
            }

            .oferta-fundador-subtitle {
                color: rgba(244, 247, 251, 0.76);
                font-size: clamp(0.94rem, 2.2vw, 1.03rem);
                line-height: 1.56;
                max-width: 980px;
            }

            .oferta-fundador-grid {
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 0.85rem;
                margin: 1rem 0;
            }

            .oferta-fundador-card {
                padding: 1.05rem 1.08rem;
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background:
                    radial-gradient(circle at top right, rgba(214, 181, 109, 0.07), transparent 30%),
                    rgba(255, 255, 255, 0.034);
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.17);
                height: 100%;
            }

            .oferta-fundador-badge {
                display: inline-block;
                padding: 0.18rem 0.58rem;
                border-radius: 999px;
                background: rgba(214, 181, 109, 0.10);
                border: 1px solid rgba(214, 181, 109, 0.20);
                color: #d6b56d;
                font-size: 0.72rem;
                font-weight: 780;
                margin-bottom: 0.55rem;
            }

            .oferta-fundador-card-title {
                color: #f4f7fb;
                font-size: 1.1rem;
                font-weight: 850;
                margin-bottom: 0.35rem;
            }

            .oferta-fundador-card-text {
                color: rgba(244, 247, 251, 0.70);
                font-size: 0.90rem;
                line-height: 1.52;
            }

            .oferta-fundador-price {
                color: #f4f7fb;
                font-size: 1.45rem;
                font-weight: 920;
                letter-spacing: -0.03em;
                margin: 0.35rem 0;
            }

            .oferta-fundador-note {
                padding: 0.95rem 1rem;
                border-radius: 16px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.92rem;
                line-height: 1.55;
                margin: 0.75rem 0;
            }

            @media (max-width: 900px) {
                .oferta-fundador-grid {
                    grid-template-columns: 1fr;
                }

                .oferta-fundador-hero {
                    border-radius: 22px;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _card_plano(badge: str, titulo: str, preco: str, texto: str) -> None:
    st.markdown(
        f"""
        <div class="oferta-fundador-card">
            <div class="oferta-fundador-badge">{badge}</div>
            <div class="oferta-fundador-card-title">{titulo}</div>
            <div class="oferta-fundador-price">{preco}</div>
            <div class="oferta-fundador-card-text">{texto}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _gerar_mensagem_manual_oferta() -> str:
    return f"""Estou abrindo uma versão beta da Valoris para um grupo pequeno de usuários fundadores.

A Valoris é uma plataforma educacional para ajudar investidores a auditar decisões antes de comprar ações.

Ela organiza:
- valuation e preço-teto;
- margem de segurança;
- riscos que podem distorcer a análise;
- relatório em linguagem simples;
- lista de espera e evolução guiada do produto.

A condição beta que estou testando é:

1. Acesso fundador simbólico: {OFERTA_FUNDADOR["preco_unico"]}
ou
2. Beta mensal: {OFERTA_FUNDADOR["preco_mensal"]}

Importante: não é recomendação de investimento e não promete rentabilidade. É uma ferramenta para organizar raciocínio, evitar decisões impulsivas e melhorar a análise.

Faz sentido para você participar do beta fundador?"""


def _renderizar_metricas_lista() -> None:
    metricas = _calcular_metricas_beta()

    st.markdown("### Sinais comerciais da lista")

    col_1, col_2, col_3 = st.columns(3)

    with col_1:
        st.metric("Leads", metricas["total"])

    with col_2:
        st.metric("Pagariam agora", metricas["pagariam_agora"])

    with col_3:
        st.metric("Talvez pagariam", metricas["talvez_pagariam"])

    col_4, col_5, col_6 = st.columns(3)

    with col_4:
        st.metric("Dor dominante", metricas["dor_mais_comum"])

    with col_5:
        st.metric("Plano mais citado", metricas["plano_mais_citado"])

    with col_6:
        st.metric("Preço mais citado", metricas["preco_mais_citado"])


def renderizar_oferta_beta() -> None:
    """
    Renderiza a Oferta Beta Fundador.
    """
    _injetar_css_oferta_beta()

    st.markdown(
        f"""
        <div class="oferta-fundador-hero">
            <div class="oferta-fundador-eyebrow">Valoris • v{VERSAO_OFERTA_BETA}</div>
            <div class="oferta-fundador-title">Oferta Beta Fundador</div>
            <div class="oferta-fundador-subtitle">
                A Valoris ainda está em construção, mas já resolve uma dor clara:
                ajudar o investidor a pensar melhor antes de comprar. Esta tela estrutura
                a primeira oferta controlada, sem checkout automático e sem promessa de rentabilidade.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="oferta-fundador-note">
            <strong>Promessa central:</strong> {OFERTA_FUNDADOR["promessa"]}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Estrutura de planos")

    st.markdown(
        """
        <div class="oferta-fundador-grid">
        """,
        unsafe_allow_html=True,
    )

    _card_plano(
        "Entrada",
        "Plano Gratuito",
        "R$ 0",
        """
        Para conhecer a proposta, testar modo demonstração, entender valuation básico
        e entrar na lista beta.
        """,
    )

    _card_plano(
        "Recomendado",
        "Beta Fundador",
        OFERTA_FUNDADOR["preco_unico"],
        """
        Acesso antecipado, participação na evolução do produto, condição simbólica
        e prioridade nos próximos testes.
        """,
    )

    _card_plano(
        "Alternativa",
        "Beta Mensal",
        OFERTA_FUNDADOR["preco_mensal"],
        """
        Para validar recorrência e disposição real de pagamento antes de construir
        checkout, assinatura e estrutura premium.
        """,
    )

    st.markdown("</div>", unsafe_allow_html=True)

    st.divider()

    st.markdown("### O que o Beta Fundador inclui")

    beneficios = [
        "Acesso antecipado às novas versões da Valoris.",
        "Uso do Auditor Valoris e das camadas Leigo, Intermediário e Avançado.",
        "Relatório Valoris Premium em Markdown.",
        "Participação direta no refinamento da plataforma.",
        "Condição simbólica enquanto o produto ainda está em construção.",
        "Prioridade para testar automações futuras por ticker e dados fundamentalistas.",
    ]

    for beneficio in beneficios:
        st.success(f"**{beneficio}**")

    st.divider()

    st.markdown("### O que ainda não está incluso")

    limites = [
        "Ainda não há recomendação de investimento.",
        "Ainda não há promessa de retorno financeiro.",
        "Ainda não há integração completa com APIs de dados fundamentalistas.",
        "Ainda não há checkout automático.",
        "Ainda não há leitura automática completa de balanços e dividendos.",
    ]

    for limite in limites:
        st.warning(f"**{limite}**")

    st.divider()

    _renderizar_metricas_lista()

    st.divider()

    st.markdown("### Captura de interessados")

    renderizar_lista_espera_valoris(modo_admin=True, chave_contexto="oferta_beta")

    st.divider()

    st.markdown("### Mensagem manual para testar com leads")

    st.text_area(
        "Copie e envie manualmente para pessoas qualificadas",
        value=_gerar_mensagem_manual_oferta(),
        height=310,
        key="mensagem_manual_oferta_beta_fundador",
    )

    st.download_button(
        label="Baixar lista de espera (.csv)",
        data=gerar_csv_lista_espera(),
        file_name="lista_espera_beta.csv",
        mime="text/csv",
        key="oferta_beta_download_lista_espera",
    )

    st.info(
        OFERTA_FUNDADOR["aviso"]
    )


def executar_autoteste_oferta_beta() -> List[Dict[str, str]]:
    return [
        {
            "teste": "versao_oferta_beta",
            "status": "OK" if VERSAO_OFERTA_BETA == "3.8.40" else "FALHA",
            "detalhe": VERSAO_OFERTA_BETA,
        },
        {
            "teste": "mensagem_manual",
            "status": "OK" if "Valoris" in _gerar_mensagem_manual_oferta() else "FALHA",
            "detalhe": "Mensagem gerada.",
        },
        {
            "teste": "oferta_fundador",
            "status": "OK" if OFERTA_FUNDADOR["preco_unico"] == "R$ 97" else "FALHA",
            "detalhe": OFERTA_FUNDADOR["preco_unico"],
        },
    ]
