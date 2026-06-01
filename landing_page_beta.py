# landing_page_beta.py

from datetime import datetime
from typing import Any, Dict, List

import streamlit as st


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v1.32 — Landing Page Beta e Página de Vendas
# ------------------------------------------------------------
# Esta tela estrutura a primeira landing page do produto.
# Objetivo:
# - transformar a proposta de valor em página de conversão
# - organizar headline, promessa, dor, benefícios e CTA
# - gerar copy pronta para Canva, Framer, Carrd, Notion ou site próprio
# ============================================================


def _safe_get_dict(key: str) -> Dict[str, Any]:
    valor = st.session_state.get(key)

    if isinstance(valor, dict):
        return valor

    return {}


def _fmt_texto(valor: Any, padrao: str = "N/D") -> str:
    if valor is None or valor == "":
        return padrao

    return str(valor)


def _extrair_contexto_landing() -> Dict[str, Any]:
    marketing = _safe_get_dict("resultado_marketing")
    negocio = _safe_get_dict("resultado_dashboard_negocio")
    oferta = _safe_get_dict("resultado_oferta_beta")
    conteudo = _safe_get_dict("resultado_conteudo_marketing")

    return {
        "perfil_dominante": marketing.get(
            "perfil_dominante",
            negocio.get("perfil_lista_mais_comum", "investidores iniciantes e intermediários"),
        ),
        "dor_dominante": marketing.get(
            "dor_dominante",
            negocio.get("dor_mais_comum", "medo de pagar caro em ações"),
        ),
        "modulo_campeao": marketing.get(
            "modulo_campeao",
            negocio.get("modulo_mais_util", "Valuation"),
        ),
        "preco_citado": marketing.get(
            "preco_citado",
            negocio.get("preco_lista_mais_citado", oferta.get("preco_mais_citado", "R$ 19,90 a R$ 29,90/mês")),
        ),
        "score_tracao": marketing.get(
            "score_tracao",
            negocio.get("score_tracao", 0),
        ),
        "classificacao_tracao": marketing.get(
            "classificacao_tracao",
            negocio.get("classificacao", "Validação inicial"),
        ),
        "total_lista": marketing.get(
            "total_lista",
            negocio.get("total_lista_espera", oferta.get("total", 0)),
        ),
        "total_conteudos": conteudo.get("total_conteudos", 0),
    }


def _gerar_headline(contexto: Dict[str, Any]) -> str:
    dor = _fmt_texto(contexto.get("dor_dominante")).lower()

    if "pagar caro" in dor:
        return "Descubra se o preço de uma ação faz sentido antes de comprar."

    if "preço-teto" in dor or "preco-teto" in dor:
        return "Calcule preço-teto, margem de segurança e organize sua tese em uma única plataforma."

    if "organizar" in dor:
        return "Organize suas análises de investimento com método, clareza e disciplina."

    if "relatório" in dor or "relatorio" in dor:
        return "Transforme suas análises em relatórios claros antes de investir."

    if "watchlist" in dor or "acompanhar" in dor:
        return "Acompanhe oportunidades com valuation, status, prioridade e próxima ação."

    return "Analise investimentos com método antes de tomar decisões."


def _gerar_subheadline(contexto: Dict[str, Any]) -> str:
    return (
        "A Máquina de Preço-Teto é uma plataforma educacional para organizar valuation, "
        "preço-teto, margem de segurança, tese, riscos, checklist, relatórios e watchlist "
        "em uma jornada simples e disciplinada."
    )


def _gerar_promessa(contexto: Dict[str, Any]) -> str:
    dor = _fmt_texto(contexto.get("dor_dominante")).lower()

    if "pagar caro" in dor:
        return (
            "Pare de comprar ativos apenas porque parecem bons. Aprenda a pensar em preço, "
            "margem de segurança, risco e qualidade da tese antes de agir."
        )

    if "organizar" in dor:
        return (
            "Saia das análises soltas e transforme seu processo em uma rotina clara: premissas, "
            "valuation, tese, checklist, relatório e acompanhamento."
        )

    return (
        "A plataforma não promete prever o mercado. Ela ajuda você a estruturar melhor o raciocínio "
        "antes de investir."
    )


def _gerar_beneficios() -> List[Dict[str, str]]:
    return [
        {
            "Benefício": "Preço-teto com margem de segurança",
            "Descrição": "Ajuda a pensar em uma zona racional de entrada com base em premissas explícitas.",
        },
        {
            "Benefício": "Tese mais clara",
            "Descrição": "Organiza o que a empresa faz, como ganha dinheiro, fundamentos, riscos e pontos de atenção.",
        },
        {
            "Benefício": "Checklist contra erros",
            "Descrição": "Reduz decisões por impulso, narrativa, preço baixo aparente ou excesso de otimismo.",
        },
        {
            "Benefício": "Relatórios de análise",
            "Descrição": "Transforma suas premissas e conclusões em documentos para revisão futura.",
        },
        {
            "Benefício": "Watchlist inteligente",
            "Descrição": "Salva ativos com status, prioridade e próxima ação para acompanhar oportunidades.",
        },
        {
            "Benefício": "Visão multiativos",
            "Descrição": "Inclui estruturas para ações, FIIs e renda fixa dentro de uma mesma jornada educacional.",
        },
    ]


def _gerar_modulos() -> List[Dict[str, str]]:
    return [
        {
            "Módulo": "Valuation",
            "Função": "Calcula EPS, FCF por ação, preço justo, preço-teto e margem de segurança.",
        },
        {
            "Módulo": "Tese & Convicção",
            "Função": "Ajuda a avaliar a qualidade da tese e os fundamentos qualitativos.",
        },
        {
            "Módulo": "Checklist",
            "Função": "Audita possíveis erros antes de uma decisão de investimento.",
        },
        {
            "Módulo": "Painel Executivo",
            "Função": "Consolida a leitura geral da análise em uma visão prática.",
        },
        {
            "Módulo": "Relatórios",
            "Função": "Gera documentos em Markdown com os principais pontos da análise.",
        },
        {
            "Módulo": "Watchlist",
            "Função": "Permite acompanhar ativos com prioridade, status e próxima ação.",
        },
        {
            "Módulo": "Ações Brasil, FIIs e Renda Fixa",
            "Função": "Adapta a jornada para diferentes classes de ativos.",
        },
    ]


def _gerar_faq() -> List[Dict[str, str]]:
    return [
        {
            "Pergunta": "A Máquina de Preço-Teto recomenda compra ou venda?",
            "Resposta": "Não. A plataforma é educacional. Ela organiza premissas, riscos e raciocínio, mas não recomenda compra, venda ou manutenção.",
        },
        {
            "Pergunta": "Os dados são puxados automaticamente?",
            "Resposta": "Nesta fase beta, a maior parte dos dados deve ser inserida ou revisada manualmente pelo usuário.",
        },
        {
            "Pergunta": "O preço-teto é uma previsão?",
            "Resposta": "Não. É uma estimativa baseada em premissas. Se as premissas forem ruins, o resultado também será ruim.",
        },
        {
            "Pergunta": "Serve para iniciantes?",
            "Resposta": "Sim, principalmente para quem quer aprender um método mais organizado para analisar ativos.",
        },
        {
            "Pergunta": "Serve para investidores mais avançados?",
            "Resposta": "Sim, como ferramenta de organização, registro de premissas, relatórios e acompanhamento.",
        },
    ]


def _gerar_copy_landing_markdown(contexto: Dict[str, Any]) -> str:
    headline = _gerar_headline(contexto)
    subheadline = _gerar_subheadline(contexto)
    promessa = _gerar_promessa(contexto)
    beneficios = _gerar_beneficios()
    modulos = _gerar_modulos()
    faq = _gerar_faq()

    beneficios_md = "\n".join(
        [
            f"- **{item['Benefício']}**: {item['Descrição']}"
            for item in beneficios
        ]
    )

    modulos_md = "\n".join(
        [
            f"- **{item['Módulo']}**: {item['Função']}"
            for item in modulos
        ]
    )

    faq_md = "\n".join(
        [
            f"### {item['Pergunta']}\n{item['Resposta']}\n"
            for item in faq
        ]
    )

    return f"""# Landing Page — Máquina de Preço-Teto

Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Headline

{headline}

## Subheadline

{subheadline}

## Promessa Educacional

{promessa}

## Para quem é

Para investidores iniciantes e intermediários que querem analisar ações, FIIs e renda fixa com mais método, disciplina e clareza.

## Dor principal

{_fmt_texto(contexto.get("dor_dominante"))}

## Benefícios

{beneficios_md}

## Módulos

{modulos_md}

## Oferta Beta

Entre na lista de espera da Máquina de Preço-Teto e ajude a construir uma plataforma educacional para análise de investimentos.

Possível faixa de preço validada: {_fmt_texto(contexto.get("preco_citado"))}

## CTA principal

Quero entrar na lista de espera

## CTA secundário

Quero testar o beta fechado

## Aviso educacional

A Máquina de Preço-Teto não recomenda compra, venda ou manutenção de ativos.  
A plataforma é educacional e serve para organizar raciocínio, premissas, riscos, valuation e acompanhamento.

## FAQ

{faq_md}
"""


def _injetar_css_landing() -> None:
    st.markdown(
        """
        <style>
            .lp-hero {
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

            .lp-eyebrow {
                color: #d6b56d;
                font-size: 0.78rem;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.35rem;
            }

            .lp-title {
                color: #f4f7fb;
                font-size: 2.1rem;
                font-weight: 900;
                margin-bottom: 0.45rem;
                line-height: 1.14;
            }

            .lp-subtitle {
                color: rgba(244, 247, 251, 0.76);
                font-size: 1rem;
                line-height: 1.62;
                max-width: 1080px;
            }

            .lp-card {
                padding: 1.1rem 1.15rem;
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.035);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.18);
                height: 100%;
            }

            .lp-card-label {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .lp-card-value {
                color: #f4f7fb;
                font-size: 1.22rem;
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .lp-card-note {
                color: rgba(244, 247, 251, 0.68);
                font-size: 0.87rem;
                line-height: 1.47;
            }

            .lp-preview {
                padding: 1.25rem 1.3rem;
                border-radius: 24px;
                border: 1px solid rgba(214, 181, 109, 0.18);
                background:
                    radial-gradient(circle at top left, rgba(214, 181, 109, 0.12), transparent 30%),
                    rgba(255, 255, 255, 0.035);
                margin-bottom: 1rem;
            }

            .lp-preview-title {
                color: #f4f7fb;
                font-size: 1.55rem;
                font-weight: 900;
                line-height: 1.18;
                margin-bottom: 0.65rem;
            }

            .lp-preview-text {
                color: rgba(244, 247, 251, 0.75);
                font-size: 0.98rem;
                line-height: 1.58;
                margin-bottom: 0.9rem;
            }

            .lp-button {
                display: inline-block;
                padding: 0.62rem 0.95rem;
                border-radius: 999px;
                background: #d6b56d;
                color: #08101f;
                font-weight: 850;
                font-size: 0.88rem;
            }

            .lp-highlight {
                padding: 0.95rem 1rem;
                border-radius: 16px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.92rem;
                line-height: 1.55;
                margin-bottom: 0.7rem;
            }

            .lp-copy {
                padding: 1rem 1.05rem;
                border-radius: 18px;
                background: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(255, 255, 255, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.92rem;
                line-height: 1.58;
                white-space: pre-wrap;
                margin-bottom: 0.85rem;
            }

            .lp-disclaimer {
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
        <div class="lp-card">
            <div class="lp-card-label">{label}</div>
            <div class="lp-card-value">{value}</div>
            <div class="lp-card-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _copy_box(texto: str) -> None:
    st.markdown(
        f"""
        <div class="lp-copy">{texto}</div>
        """,
        unsafe_allow_html=True,
    )


def renderizar_landing_page_beta() -> None:
    """
    Renderiza a central da Landing Page Beta.
    """
    _injetar_css_landing()

    contexto = _extrair_contexto_landing()
    headline = _gerar_headline(contexto)
    subheadline = _gerar_subheadline(contexto)
    promessa = _gerar_promessa(contexto)
    beneficios = _gerar_beneficios()
    modulos = _gerar_modulos()
    faq = _gerar_faq()
    markdown_landing = _gerar_copy_landing_markdown(contexto)

    st.session_state["resultado_landing_page"] = {
        "headline": headline,
        "subheadline": subheadline,
        "promessa": promessa,
        **contexto,
    }

    st.markdown(
        """
        <div class="lp-hero">
            <div class="lp-eyebrow">Página de conversão</div>
            <div class="lp-title">Landing Page Beta e Página de Vendas</div>
            <div class="lp-subtitle">
                Estruture a primeira página externa da Máquina de Preço-Teto.
                Use esta central para organizar headline, promessa, benefícios, módulos,
                oferta beta, CTA e avisos educacionais.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="lp-highlight">
            A landing page não deve prometer lucro. Ela deve vender clareza, método,
            disciplina e organização antes da decisão de investir.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Diagnóstico para a página")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        _card(
            "Público provável",
            _fmt_texto(contexto["perfil_dominante"]),
            "Quem parece mais interessado.",
        )

    with col_2:
        _card(
            "Dor principal",
            _fmt_texto(contexto["dor_dominante"]),
            "Base da headline e da copy.",
        )

    with col_3:
        _card(
            "Preço validado",
            _fmt_texto(contexto["preco_citado"]),
            "Sinal inicial de valor percebido.",
        )

    with col_4:
        _card(
            "Score de tração",
            f"{contexto['score_tracao']}/100",
            _fmt_texto(contexto["classificacao_tracao"]),
        )

    st.divider()

    st.markdown("### Preview da primeira dobra")

    st.markdown(
        f"""
        <div class="lp-preview">
            <div class="lp-preview-title">{headline}</div>
            <div class="lp-preview-text">{subheadline}</div>
            <div class="lp-button">Quero entrar na lista de espera</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    st.markdown("### Copy principal")

    st.markdown("#### Headline")
    _copy_box(headline)

    st.markdown("#### Subheadline")
    _copy_box(subheadline)

    st.markdown("#### Promessa educacional")
    _copy_box(promessa)

    st.divider()

    st.markdown("### Benefícios da página")

    st.dataframe(
        beneficios,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Módulos para apresentar")

    st.dataframe(
        modulos,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Estrutura recomendada da landing page")

    estrutura = [
        {
            "Seção": "1. Hero",
            "Objetivo": "Explicar rapidamente o produto e chamar para lista de espera.",
            "Elemento": "Headline, subheadline e CTA.",
        },
        {
            "Seção": "2. Problema",
            "Objetivo": "Mostrar a dor: pagar caro, analisar sem método, não registrar decisões.",
            "Elemento": "Texto curto com 3 dores principais.",
        },
        {
            "Seção": "3. Solução",
            "Objetivo": "Apresentar a Máquina de Preço-Teto como método educacional.",
            "Elemento": "Explicação simples da jornada.",
        },
        {
            "Seção": "4. Benefícios",
            "Objetivo": "Mostrar valor prático.",
            "Elemento": "Preço-teto, tese, checklist, relatório, watchlist.",
        },
        {
            "Seção": "5. Demonstração",
            "Objetivo": "Mostrar prints ou gravações do app.",
            "Elemento": "Imagens da plataforma.",
        },
        {
            "Seção": "6. Oferta Beta",
            "Objetivo": "Captar interessados sem vender agressivamente.",
            "Elemento": "Lista de espera e benefício de entrar cedo.",
        },
        {
            "Seção": "7. Aviso Educacional",
            "Objetivo": "Proteger o produto e aumentar confiança.",
            "Elemento": "Não é recomendação de investimento.",
        },
        {
            "Seção": "8. FAQ",
            "Objetivo": "Remover objeções.",
            "Elemento": "Perguntas frequentes.",
        },
    ]

    st.dataframe(
        estrutura,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### FAQ para a página")

    st.dataframe(
        faq,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Copy completa para usar fora do app")

    _copy_box(markdown_landing)

    st.download_button(
        label="Baixar copy da landing page (.md)",
        data=markdown_landing,
        file_name="landing_page_maquina_preco_teto.md",
        mime="text/markdown",
        key="download_landing_page_md",
    )

    st.markdown(
        """
        <div class="lp-disclaimer">
            <strong>Nota estratégica:</strong> esta página deve ser usada primeiro como teste.
            Crie uma versão simples no Canva, Framer, Carrd, Notion ou Streamlit.
            Meça cliques, cadastros, respostas e intenção real antes de investir em design avançado.
        </div>
        """,
        unsafe_allow_html=True,
    )