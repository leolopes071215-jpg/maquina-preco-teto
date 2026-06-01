# marketing.py

import streamlit as st
from typing import Any, Dict, List


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v1.30 — Central de Marketing e Go-to-Market
# ------------------------------------------------------------
# Esta tela organiza a estratégia inicial de aquisição:
# - público-alvo
# - dor dominante
# - proposta de valor
# - copy
# - canais
# - conteúdos
# - funil simples
#
# Objetivo:
# sair do produto interno e começar a criar demanda.
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


def _fmt_numero(valor: Any) -> str:
    try:
        return str(int(float(valor)))
    except (TypeError, ValueError):
        return "0"


def _extrair_contexto_marketing() -> Dict[str, Any]:
    negocio = _safe_get_dict("resultado_dashboard_negocio")
    oferta = _safe_get_dict("resultado_oferta_beta")
    feedback = _safe_get_dict("resultado_feedback_beta")

    return {
        "score_tracao": negocio.get("score_tracao", 0),
        "classificacao_tracao": negocio.get("classificacao", "N/D"),
        "perfil_dominante": negocio.get(
            "perfil_lista_mais_comum",
            oferta.get("perfil_mais_comum", feedback.get("perfil_mais_comum", "N/D")),
        ),
        "dor_dominante": negocio.get(
            "dor_mais_comum",
            oferta.get("dor_mais_comum", "N/D"),
        ),
        "modulo_campeao": negocio.get(
            "modulo_mais_util",
            feedback.get("modulo_mais_citado", "N/D"),
        ),
        "preco_citado": negocio.get(
            "preco_lista_mais_citado",
            oferta.get("preco_mais_citado", feedback.get("preco_mais_citado", "N/D")),
        ),
        "total_feedbacks": negocio.get(
            "total_feedbacks",
            feedback.get("total", 0),
        ),
        "total_lista": negocio.get(
            "total_lista_espera",
            oferta.get("total", 0),
        ),
        "pagaria_sim": negocio.get(
            "lista_pagaria_sim",
            oferta.get("pagaria_sim", 0),
        ),
    }


def _gerar_posicionamento(contexto: Dict[str, Any]) -> str:
    dor = _fmt_texto(contexto.get("dor_dominante"))
    perfil = _fmt_texto(contexto.get("perfil_dominante"))

    if dor != "N/D" and perfil != "N/D":
        return (
            f"Para {perfil.lower()} que sente que '{dor.lower()}', "
            "a Máquina de Preço-Teto é uma plataforma educacional que organiza valuation, "
            "preço-teto, tese, riscos, relatórios e watchlist para transformar decisões de investimento em método."
        )

    return (
        "Para investidores que querem analisar ativos com mais método, "
        "a Máquina de Preço-Teto organiza valuation, margem de segurança, tese, riscos, relatórios e watchlist "
        "em uma única jornada educacional."
    )


def _gerar_promessa_principal(contexto: Dict[str, Any]) -> str:
    dor = _fmt_texto(contexto.get("dor_dominante"))

    if "pagar caro" in dor.lower():
        return (
            "Pare de comprar ativos apenas pela narrativa. Aprenda a estimar uma zona racional de preço "
            "com valuation, margem de segurança e revisão da tese."
        )

    if "organizar" in dor.lower():
        return (
            "Organize suas análises de investimento em uma jornada clara: premissas, valuation, tese, checklist, relatório e watchlist."
        )

    if "relatórios" in dor.lower() or "relatorio" in dor.lower():
        return (
            "Transforme suas premissas e riscos em relatórios organizados para revisar antes de qualquer decisão."
        )

    if "watchlist" in dor.lower() or "acompanhar" in dor.lower():
        return (
            "Pare de perder oportunidades no improviso. Salve ativos, defina prioridade, status e próxima ação em uma watchlist inteligente."
        )

    return (
        "Analise ativos com mais disciplina: valuation, preço-teto, margem de segurança, tese, riscos, relatório e acompanhamento."
    )


def _gerar_ideias_conteudo(contexto: Dict[str, Any]) -> List[Dict[str, str]]:
    dor = _fmt_texto(contexto.get("dor_dominante"))
    modulo = _fmt_texto(contexto.get("modulo_campeao"))

    ideias = [
        {
            "Tema": "Preço-teto",
            "Gancho": "Empresa boa pode virar péssimo investimento se você pagar caro.",
            "Formato": "Reels/TikTok curto",
            "CTA": "Teste a Máquina de Preço-Teto no beta.",
        },
        {
            "Tema": "Margem de segurança",
            "Gancho": "O investidor inteligente não busca certeza. Busca margem de erro.",
            "Formato": "Carrossel",
            "CTA": "Entre na lista de espera.",
        },
        {
            "Tema": "Tese de investimento",
            "Gancho": "Se você não consegue explicar a tese em 30 segundos, talvez não tenha uma tese.",
            "Formato": "Reels/TikTok",
            "CTA": "Use o checklist da plataforma.",
        },
        {
            "Tema": "Checklist de erros",
            "Gancho": "Antes de comprar uma ação, responda estas 7 perguntas.",
            "Formato": "Carrossel educativo",
            "CTA": "Baixe um relatório de análise.",
        },
        {
            "Tema": "FIIs",
            "Gancho": "Dividend yield alto pode ser renda ou armadilha.",
            "Formato": "Reels/TikTok",
            "CTA": "Analise FIIs com método.",
        },
        {
            "Tema": "Renda fixa",
            "Gancho": "Nem todo investimento seguro é bom. O preço do tempo também importa.",
            "Formato": "Post curto",
            "CTA": "Compare alternativas com racionalidade.",
        },
        {
            "Tema": "Relatórios",
            "Gancho": "Se você não registra sua análise, você não sabe se está evoluindo.",
            "Formato": "Demonstração de tela",
            "CTA": "Entre no beta fechado.",
        },
        {
            "Tema": "Watchlist",
            "Gancho": "Oportunidade não acompanhada vira esquecimento.",
            "Formato": "Reels com tela do app",
            "CTA": "Salve ativos na watchlist.",
        },
    ]

    if dor != "N/D":
        ideias.insert(
            0,
            {
                "Tema": "Dor dominante",
                "Gancho": f"Você também sente isso: {dor}?",
                "Formato": "Post de validação",
                "CTA": "Responda e entre na lista de espera.",
            },
        )

    if modulo != "N/D":
        ideias.insert(
            1,
            {
                "Tema": f"Módulo destaque: {modulo}",
                "Gancho": f"O módulo mais valorizado pelos primeiros usuários foi: {modulo}.",
                "Formato": "Demonstração prática",
                "CTA": "Teste a plataforma e dê feedback.",
            },
        )

    return ideias


def _gerar_funil() -> List[Dict[str, str]]:
    return [
        {
            "Etapa": "1. Atenção",
            "Objetivo": "Atrair investidores com dores reais.",
            "Ação": "Postar conteúdos sobre preço-teto, margem de segurança, erros de análise e FIIs.",
            "Métrica": "Visualizações, comentários e salvamentos.",
        },
        {
            "Etapa": "2. Interesse",
            "Objetivo": "Mostrar que existe uma ferramenta em construção.",
            "Ação": "Publicar demonstrações curtas do app e prints dos relatórios.",
            "Métrica": "Cliques no link e respostas no direct.",
        },
        {
            "Etapa": "3. Validação",
            "Objetivo": "Coletar feedback de usuários reais.",
            "Ação": "Enviar o link do app para usuários beta preencherem Feedback Beta.",
            "Métrica": "Quantidade e qualidade dos feedbacks.",
        },
        {
            "Etapa": "4. Lista de espera",
            "Objetivo": "Medir intenção real de compra.",
            "Ação": "Direcionar interessados para Oferta Beta.",
            "Métrica": "Cadastros e intenção de pagamento.",
        },
        {
            "Etapa": "5. Pré-venda controlada",
            "Objetivo": "Testar monetização com baixo risco.",
            "Ação": "Oferecer acesso beta premium para poucos usuários.",
            "Métrica": "Conversões pagas e retenção.",
        },
    ]


def _gerar_canais() -> List[Dict[str, str]]:
    return [
        {
            "Canal": "TikTok",
            "Função": "Alcance rápido.",
            "Tipo de conteúdo": "Ganchos fortes, erros comuns, demonstrações rápidas.",
            "Prioridade": "Alta",
        },
        {
            "Canal": "Instagram",
            "Função": "Autoridade e relacionamento.",
            "Tipo de conteúdo": "Carrosséis, reels, stories, bastidores do produto.",
            "Prioridade": "Alta",
        },
        {
            "Canal": "YouTube Shorts",
            "Função": "Reaproveitar vídeos curtos.",
            "Tipo de conteúdo": "Cortes educativos e demonstrações do app.",
            "Prioridade": "Média",
        },
        {
            "Canal": "WhatsApp",
            "Função": "Beta fechado manual.",
            "Tipo de conteúdo": "Convite direto para testar e preencher feedback.",
            "Prioridade": "Alta",
        },
        {
            "Canal": "LinkedIn",
            "Função": "Credibilidade futura.",
            "Tipo de conteúdo": "Construção pública, produto, análise e educação financeira.",
            "Prioridade": "Média",
        },
        {
            "Canal": "Newsletter",
            "Função": "Retenção e autoridade.",
            "Tipo de conteúdo": "Resumo semanal, estudos de caso e evolução do produto.",
            "Prioridade": "Futura",
        },
    ]


def _gerar_copies(contexto: Dict[str, Any]) -> Dict[str, str]:
    promessa = _gerar_promessa_principal(contexto)
    posicionamento = _gerar_posicionamento(contexto)

    return {
        "bio_instagram": (
            "📊 Valuation, preço-teto e margem de segurança\n"
            "🧠 Invista com método, não com impulso\n"
            "🧪 Beta da Máquina de Preço-Teto"
        ),
        "cta_lista_espera": (
            "Estou abrindo uma lista de espera para a Máquina de Preço-Teto, "
            "uma plataforma educacional para organizar valuation, tese, riscos, relatórios e watchlist. "
            "Entre no beta e ajude a construir a versão final."
        ),
        "pitch_curto": (
            "A Máquina de Preço-Teto é uma plataforma educacional para investidores que querem analisar ativos com mais método. "
            "Ela organiza preço justo, preço-teto, margem de segurança, tese, riscos, checklist, relatórios e watchlist."
        ),
        "promessa": promessa,
        "posicionamento": posicionamento,
        "post_apresentacao": (
            "Estou construindo uma plataforma para resolver um problema que muitos investidores têm: "
            "comprar ativos sem saber se o preço faz sentido.\n\n"
            "A Máquina de Preço-Teto organiza valuation, margem de segurança, tese, riscos, relatório e watchlist em uma única jornada.\n\n"
            "Ainda está em beta. Quem quiser testar, entra na lista de espera."
        ),
    }


def _gerar_proximas_acoes_marketing(contexto: Dict[str, Any]) -> List[str]:
    total_feedbacks = int(contexto.get("total_feedbacks", 0) or 0)
    total_lista = int(contexto.get("total_lista", 0) or 0)
    score = int(float(contexto.get("score_tracao", 0) or 0))

    acoes = []

    if total_feedbacks < 10:
        acoes.append("Convidar pelo menos 10 pessoas para testar o app e preencher Feedback Beta.")

    if total_lista < 10:
        acoes.append("Direcionar interessados para a aba Oferta Beta e começar a formar lista de espera.")

    acoes.append("Gravar 3 vídeos curtos mostrando o problema: pagar caro, não ter tese e não registrar análise.")
    acoes.append("Criar 2 carrosséis educativos: margem de segurança e checklist antes de comprar uma ação.")
    acoes.append("Publicar 1 demonstração curta da aba Relatórios ou Watchlist.")
    acoes.append("Usar os feedbacks para descobrir qual módulo deve virar promessa principal.")

    if score >= 65:
        acoes.append("Preparar uma landing page externa simples com promessa, prints, lista de espera e aviso educacional.")

    if score >= 80:
        acoes.append("Testar uma pré-venda manual com poucos usuários e preço beta.")

    return acoes


def _injetar_css_marketing() -> None:
    st.markdown(
        """
        <style>
            .mkt-hero {
                padding: 1.7rem 1.75rem;
                border-radius: 30px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    radial-gradient(circle at top left, rgba(214, 181, 109, 0.25), transparent 30%),
                    radial-gradient(circle at bottom right, rgba(74, 144, 226, 0.22), transparent 34%),
                    linear-gradient(135deg, rgba(8, 15, 27, 0.99), rgba(5, 9, 18, 0.99));
                box-shadow: 0 18px 55px rgba(0, 0, 0, 0.34);
                margin-bottom: 1.25rem;
            }

            .mkt-eyebrow {
                color: #d6b56d;
                font-size: 0.78rem;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.35rem;
            }

            .mkt-title {
                color: #f4f7fb;
                font-size: 2.08rem;
                font-weight: 900;
                margin-bottom: 0.45rem;
                line-height: 1.14;
            }

            .mkt-subtitle {
                color: rgba(244, 247, 251, 0.76);
                font-size: 1rem;
                line-height: 1.62;
                max-width: 1080px;
            }

            .mkt-card {
                padding: 1.1rem 1.15rem;
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.035);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.18);
                height: 100%;
            }

            .mkt-card-label {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .mkt-card-value {
                color: #f4f7fb;
                font-size: 1.22rem;
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .mkt-card-note {
                color: rgba(244, 247, 251, 0.68);
                font-size: 0.87rem;
                line-height: 1.47;
            }

            .mkt-copy {
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

            .mkt-highlight {
                padding: 0.95rem 1rem;
                border-radius: 16px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.92rem;
                line-height: 1.55;
                margin-bottom: 0.7rem;
            }

            .mkt-disclaimer {
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
        <div class="mkt-card">
            <div class="mkt-card-label">{label}</div>
            <div class="mkt-card-value">{value}</div>
            <div class="mkt-card-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _renderizar_copy(titulo: str, texto: str) -> None:
    st.markdown(f"#### {titulo}")
    st.markdown(
        f"""
        <div class="mkt-copy">{texto}</div>
        """,
        unsafe_allow_html=True,
    )


def renderizar_central_marketing() -> None:
    """
    Renderiza a Central de Marketing e Go-to-Market.
    """
    _injetar_css_marketing()

    contexto = _extrair_contexto_marketing()
    posicionamento = _gerar_posicionamento(contexto)
    promessa = _gerar_promessa_principal(contexto)
    ideias = _gerar_ideias_conteudo(contexto)
    funil = _gerar_funil()
    canais = _gerar_canais()
    copies = _gerar_copies(contexto)
    proximas_acoes = _gerar_proximas_acoes_marketing(contexto)

    st.session_state["resultado_marketing"] = {
        "posicionamento": posicionamento,
        "promessa": promessa,
        "proximas_acoes": proximas_acoes,
        **contexto,
    }

    st.markdown(
        """
        <div class="mkt-hero">
            <div class="mkt-eyebrow">Aquisição e demanda</div>
            <div class="mkt-title">Central de Marketing e Go-to-Market</div>
            <div class="mkt-subtitle">
                Organize a comunicação inicial da Máquina de Preço-Teto: público-alvo,
                dor dominante, promessa educacional, funil, canais, ideias de conteúdo e copies.
                O objetivo é transformar o produto em demanda real.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="mkt-highlight">
            Marketing não começa com “compre meu app”. Começa mostrando uma dor real:
            pagar caro, decidir por impulso, não ter tese, não registrar análise e não acompanhar oportunidades.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Diagnóstico atual de mercado")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        _card(
            "Score de tração",
            f"{_fmt_numero(contexto['score_tracao'])}/100",
            _fmt_texto(contexto["classificacao_tracao"]),
        )

    with col_2:
        _card(
            "Perfil dominante",
            _fmt_texto(contexto["perfil_dominante"]),
            "Público que mais sinalizou interesse.",
        )

    with col_3:
        _card(
            "Dor dominante",
            _fmt_texto(contexto["dor_dominante"]),
            "Principal dor para a copy inicial.",
        )

    with col_4:
        _card(
            "Preço citado",
            _fmt_texto(contexto["preco_citado"]),
            "Sinal inicial de valor percebido.",
        )

    col_5, col_6, col_7 = st.columns(3)

    with col_5:
        _card(
            "Módulo campeão",
            _fmt_texto(contexto["modulo_campeao"]),
            "Pode virar destaque no conteúdo.",
        )

    with col_6:
        _card(
            "Feedbacks",
            _fmt_numero(contexto["total_feedbacks"]),
            "Base de aprendizado do produto.",
        )

    with col_7:
        _card(
            "Lista de espera",
            _fmt_numero(contexto["total_lista"]),
            "Base inicial de demanda.",
        )

    st.divider()

    st.markdown("### Posicionamento e promessa")

    _renderizar_copy("Posicionamento", posicionamento)
    _renderizar_copy("Promessa educacional principal", promessa)

    st.divider()

    st.markdown("### Copies prontas")

    _renderizar_copy("Bio do Instagram", copies["bio_instagram"])
    _renderizar_copy("Pitch curto", copies["pitch_curto"])
    _renderizar_copy("CTA para lista de espera", copies["cta_lista_espera"])
    _renderizar_copy("Post de apresentação", copies["post_apresentacao"])

    st.divider()

    st.markdown("### Ideias de conteúdo")

    st.dataframe(
        ideias,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Funil inicial")

    st.dataframe(
        funil,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Canais prioritários")

    st.dataframe(
        canais,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Próximas ações de marketing")

    for acao in proximas_acoes:
        st.markdown(f"- {acao}")

    st.divider()

    st.markdown("### Plano de 7 dias")

    plano_7_dias = [
        {
            "Dia": "Dia 1",
            "Ação": "Postar apresentação do projeto e chamar 3 pessoas para testar.",
            "Meta": "3 feedbacks.",
        },
        {
            "Dia": "Dia 2",
            "Ação": "Criar vídeo curto sobre erro de pagar caro em empresa boa.",
            "Meta": "Gerar comentários e directs.",
        },
        {
            "Dia": "Dia 3",
            "Ação": "Publicar carrossel sobre margem de segurança.",
            "Meta": "Salvamentos.",
        },
        {
            "Dia": "Dia 4",
            "Ação": "Mostrar print ou gravação da aba Relatórios.",
            "Meta": "Cliques na lista de espera.",
        },
        {
            "Dia": "Dia 5",
            "Ação": "Mostrar a Watchlist como rotina de acompanhamento.",
            "Meta": "Interesse recorrente.",
        },
        {
            "Dia": "Dia 6",
            "Ação": "Fazer post perguntando qual dor mais incomoda: preço, tese, relatório ou acompanhamento.",
            "Meta": "Validação de dor.",
        },
        {
            "Dia": "Dia 7",
            "Ação": "Chamar para beta fechado e lista de espera.",
            "Meta": "10 interessados ou feedbacks acumulados.",
        },
    ]

    st.dataframe(
        plano_7_dias,
        use_container_width=True,
        hide_index=True,
    )

    st.markdown(
        """
        <div class="mkt-disclaimer">
            <strong>Nota estratégica:</strong> esta central organiza a comunicação inicial.
            O marketing deve ser ajustado com base no comportamento real: comentários, cliques, feedbacks,
            cadastros na lista de espera e intenção de pagamento.
        </div>
        """,
        unsafe_allow_html=True,
    )