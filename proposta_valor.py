# proposta_valor.py

import streamlit as st
from typing import Any, Dict, Optional


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v1.25 — Página de Produto e Proposta de Valor
# ------------------------------------------------------------
# Esta tela explica o produto de forma clara, premium e vendável.
# Objetivo:
# - melhorar percepção de valor
# - orientar usuários novos
# - preparar o produto para marketing e venda
# ============================================================


def _safe_get_dict(key: str) -> Dict[str, Any]:
    valor = st.session_state.get(key)

    if isinstance(valor, dict):
        return valor

    return {}


def _fmt_texto(valor: Optional[Any], padrao: str = "N/D") -> str:
    if valor is None or valor == "":
        return padrao

    return str(valor)


def _fmt_score(valor: Optional[Any]) -> str:
    if valor is None or valor == "":
        return "N/D"

    try:
        return f"{int(round(float(valor)))}/100"
    except (TypeError, ValueError):
        return "N/D"


def _extrair_contexto_produto() -> Dict[str, Any]:
    valuation = _safe_get_dict("resultado_valuation")
    painel = _safe_get_dict("resultado_painel_multiativos")
    watchlist = _safe_get_dict("resultado_watchlist")

    return {
        "empresa": valuation.get("empresa", "Nenhuma análise ativa"),
        "ticker": valuation.get("ticker", "N/D"),
        "tipo_analise": valuation.get("tipo_analise", "N/D"),
        "status": valuation.get("status_valuation", valuation.get("status", "N/D")),
        "score_integrado": painel.get("score_integrado"),
        "classificacao_integrada": painel.get("classificacao_integrada"),
        "ativos_watchlist": watchlist.get("total"),
    }


def _injetar_css_produto() -> None:
    st.markdown(
        """
        <style>
            .prod-hero {
                padding: 1.65rem 1.7rem;
                border-radius: 28px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    radial-gradient(circle at top left, rgba(214, 181, 109, 0.24), transparent 30%),
                    radial-gradient(circle at bottom right, rgba(74, 144, 226, 0.22), transparent 34%),
                    linear-gradient(135deg, rgba(8, 15, 27, 0.99), rgba(5, 9, 18, 0.99));
                box-shadow: 0 18px 55px rgba(0, 0, 0, 0.34);
                margin-bottom: 1.25rem;
            }

            .prod-eyebrow {
                color: #d6b56d;
                font-size: 0.78rem;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.35rem;
            }

            .prod-title {
                color: #f4f7fb;
                font-size: 2.05rem;
                font-weight: 900;
                margin-bottom: 0.45rem;
                line-height: 1.14;
            }

            .prod-subtitle {
                color: rgba(244, 247, 251, 0.76);
                font-size: 1rem;
                line-height: 1.62;
                max-width: 1080px;
            }

            .prod-card {
                padding: 1.08rem 1.12rem;
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.035);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.18);
                height: 100%;
            }

            .prod-card-label {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .prod-card-value {
                color: #f4f7fb;
                font-size: 1.23rem;
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .prod-card-note {
                color: rgba(244, 247, 251, 0.68);
                font-size: 0.87rem;
                line-height: 1.47;
            }

            .prod-section {
                padding: 1.1rem 1.15rem;
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.028);
                margin-bottom: 1rem;
            }

            .prod-section-title {
                color: #f4f7fb;
                font-size: 1.15rem;
                font-weight: 850;
                margin-bottom: 0.35rem;
            }

            .prod-section-text {
                color: rgba(244, 247, 251, 0.70);
                font-size: 0.92rem;
                line-height: 1.55;
            }

            .prod-badge {
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

            .prod-highlight {
                padding: 0.95rem 1rem;
                border-radius: 16px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.92rem;
                line-height: 1.55;
                margin-bottom: 0.7rem;
            }

            .prod-disclaimer {
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
        <div class="prod-card">
            <div class="prod-card-label">{label}</div>
            <div class="prod-card-value">{value}</div>
            <div class="prod-card-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _section(badge: str, title: str, text: str) -> None:
    st.markdown(
        f"""
        <div class="prod-section">
            <div class="prod-badge">{badge}</div>
            <div class="prod-section-title">{title}</div>
            <div class="prod-section-text">{text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def renderizar_proposta_valor() -> None:
    """
    Renderiza a página de produto e proposta de valor.
    """
    _injetar_css_produto()

    contexto = _extrair_contexto_produto()

    st.markdown(
        """
        <div class="prod-hero">
            <div class="prod-eyebrow">Produto educacional de análise financeira</div>
            <div class="prod-title">Máquina de Preço-Teto: transforme investimento em método.</div>
            <div class="prod-subtitle">
                Uma plataforma para organizar valuation, margem de segurança, tese, riscos,
                checklist de erros, relatórios e watchlist em uma única jornada. O objetivo é
                ajudar o investidor a pensar melhor antes de tomar decisões.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Proposta central")

    st.markdown(
        """
        <div class="prod-highlight">
            A Máquina de Preço-Teto não tenta prever o futuro. Ela organiza uma pergunta mais importante:
            <strong>o preço atual compensa as premissas, os riscos e a qualidade da tese?</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_ctx_1, col_ctx_2, col_ctx_3, col_ctx_4 = st.columns(4)

    with col_ctx_1:
        st.metric("Análise ativa", _fmt_texto(contexto["empresa"]))

    with col_ctx_2:
        st.metric("Ticker", _fmt_texto(contexto["ticker"]))

    with col_ctx_3:
        st.metric("Tipo", _fmt_texto(contexto["tipo_analise"]))

    with col_ctx_4:
        st.metric("Score integrado", _fmt_score(contexto["score_integrado"]))

    st.divider()

    st.markdown("### Para quem este produto foi criado")

    col_publico_1, col_publico_2, col_publico_3 = st.columns(3)

    with col_publico_1:
        _card(
            "Investidor iniciante",
            "Organização",
            "Ajuda a sair do achismo e seguir um fluxo: premissas, valuation, tese, checklist e relatório.",
        )

    with col_publico_2:
        _card(
            "Investidor intermediário",
            "Disciplina",
            "Ajuda a comparar oportunidades, registrar premissas e evitar decisões por emoção ou narrativa.",
        )

    with col_publico_3:
        _card(
            "Criador de análise",
            "Material estruturado",
            "Gera relatórios e uma leitura mais apresentável para estudos, conteúdos e acompanhamento.",
        )

    st.divider()

    st.markdown("### Dores que a plataforma resolve")

    col_dor_1, col_dor_2 = st.columns(2)

    with col_dor_1:
        _section(
            "Dor 1",
            "Medo de pagar caro",
            "O app calcula preço justo e preço-teto com margem de segurança para ajudar o usuário a pensar em zona racional de entrada.",
        )

        _section(
            "Dor 2",
            "Tese desorganizada",
            "A plataforma força o usuário a escrever tese, riscos, fundamentos e avaliar a qualidade qualitativa da empresa.",
        )

        _section(
            "Dor 3",
            "Excesso de ativos para acompanhar",
            "A watchlist transforma análises soltas em rotina de acompanhamento com prioridade, status e próxima ação.",
        )

    with col_dor_2:
        _section(
            "Dor 4",
            "Confundir preço baixo com oportunidade",
            "O checklist e os módulos de risco ajudam a separar desconto real de possível armadilha de valor.",
        )

        _section(
            "Dor 5",
            "Falta de método entre classes de ativos",
            "Ações, FIIs e renda fixa não são tratados como se fossem iguais. Cada classe recebe filtros próprios.",
        )

        _section(
            "Dor 6",
            "Não registrar o raciocínio",
            "Os relatórios transformam premissas, riscos e decisões educacionais em documentos claros para revisão futura.",
        )

    st.divider()

    st.markdown("### O que torna o produto diferente")

    col_diff_1, col_diff_2, col_diff_3 = st.columns(3)

    with col_diff_1:
        _card(
            "Não é só calculadora",
            "É jornada",
            "O app guia o usuário do preenchimento das premissas até o relatório e a watchlist.",
        )

    with col_diff_2:
        _card(
            "Não é recomendação",
            "É método",
            "A plataforma não diz o que comprar. Ela melhora a qualidade do raciocínio.",
        )

    with col_diff_3:
        _card(
            "Não é uma planilha solta",
            "É produto",
            "Une interface, análise, risco, relatório, histórico e acompanhamento em um fluxo único.",
        )

    st.divider()

    st.markdown("### Jornada de uso recomendada")

    st.markdown(
        """
        1. **Escolha o modo de análise**: demonstração, nova análise manual ou empresa da base.  
        2. **Preencha as premissas**: lucro, fluxo de caixa, ações, preço e múltiplos.  
        3. **Veja o Valuation**: preço justo, preço-teto, margem e status educacional.  
        4. **Avalie a Tese & Convicção**: qualidade do negócio, caixa, gestão, riscos e clareza.  
        5. **Rode o Checklist**: encontre vieses, fragilidades e erros de análise.  
        6. **Abra o Painel Executivo**: veja a leitura integrada da análise.  
        7. **Baixe o Relatório**: registre o raciocínio em um documento.  
        8. **Salve na Watchlist**: acompanhe com prioridade e próxima ação.
        """
    )

    st.divider()

    st.markdown("### Módulos atuais da plataforma")

    modulos = [
        {
            "Módulo": "Início",
            "Função": "Guia o usuário pela jornada principal.",
            "Valor": "Reduz confusão e mostra o próximo passo.",
        },
        {
            "Módulo": "Valuation",
            "Função": "Calcula preço justo, preço-teto e margem de segurança.",
            "Valor": "Ajuda a pensar em preço racional.",
        },
        {
            "Módulo": "Tese & Convicção",
            "Função": "Avalia qualidade qualitativa da tese.",
            "Valor": "Evita confiar apenas no número.",
        },
        {
            "Módulo": "Checklist",
            "Função": "Audita erros e vieses.",
            "Valor": "Reduz risco de análise otimista.",
        },
        {
            "Módulo": "Painel Executivo",
            "Função": "Consolida os sinais principais.",
            "Valor": "Cria visão de sala de controle.",
        },
        {
            "Módulo": "Watchlist",
            "Função": "Salva ativos para acompanhamento.",
            "Valor": "Transforma análise em rotina.",
        },
        {
            "Módulo": "Relatórios",
            "Função": "Exporta documentos em Markdown.",
            "Valor": "Entrega material organizado e revisável.",
        },
        {
            "Módulo": "Multiativos",
            "Função": "Organiza ações, FIIs e renda fixa.",
            "Valor": "Adapta o método para classes diferentes.",
        },
    ]

    st.dataframe(
        modulos,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Visão de negócio")

    col_negocio_1, col_negocio_2, col_negocio_3 = st.columns(3)

    with col_negocio_1:
        _card(
            "Fase atual",
            "MVP avançado",
            "Estamos validando utilidade, clareza, jornada e percepção de valor.",
        )

    with col_negocio_2:
        _card(
            "Próxima fase",
            "Beta fechado",
            "Testar com usuários reais, coletar feedback e ajustar fricções.",
        )

    with col_negocio_3:
        _card(
            "Fase futura",
            "SaaS educacional",
            "Login, banco de dados, assinatura, landing page, pagamentos e interface premium.",
        )

    st.markdown(
        """
        <div class="prod-disclaimer">
            <strong>Aviso educacional:</strong> a Máquina de Preço-Teto é uma plataforma de estudo e organização de raciocínio.
            Ela não recomenda compra, venda ou manutenção de ativos. Toda decisão real deve considerar objetivos pessoais,
            liquidez, diversificação, tributação, horizonte de tempo, qualidade dos dados e responsabilidade individual.
        </div>
        """,
        unsafe_allow_html=True,
    )