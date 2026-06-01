# beta_fechado.py

import streamlit as st
from typing import Any, Dict, List


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v1.27 — Central do Beta Fechado
# ------------------------------------------------------------
# Esta tela prepara a validação com usuários reais.
# Objetivo:
# - orientar testes
# - definir perfil dos usuários beta
# - criar roteiro de uso
# - medir sinais de prontidão para venda
# - transformar o MVP em produto testável
# ============================================================


def _safe_get_dict(key: str) -> Dict[str, Any]:
    valor = st.session_state.get(key)

    if isinstance(valor, dict):
        return valor

    return {}


def _fmt_score(valor: Any) -> str:
    if valor is None or valor == "":
        return "N/D"

    try:
        return f"{int(round(float(valor)))}/100"
    except (TypeError, ValueError):
        return "N/D"


def _fmt_texto(valor: Any, padrao: str = "N/D") -> str:
    if valor is None or valor == "":
        return padrao

    return str(valor)


def _extrair_contexto_beta() -> Dict[str, Any]:
    feedback = _safe_get_dict("resultado_feedback_beta")
    watchlist = _safe_get_dict("resultado_watchlist")
    painel = _safe_get_dict("resultado_painel_multiativos")

    return {
        "total_feedbacks": feedback.get("total", 0),
        "media_clareza": feedback.get("media_clareza", 0.0),
        "media_utilidade": feedback.get("media_utilidade", 0.0),
        "media_visual": feedback.get("media_visual", 0.0),
        "media_confianca": feedback.get("media_confianca", 0.0),
        "pagaria_sim": feedback.get("pagaria_sim", 0),
        "pagaria_talvez": feedback.get("pagaria_talvez", 0),
        "perfil_mais_comum": feedback.get("perfil_mais_comum", "N/D"),
        "modulo_mais_citado": feedback.get("modulo_mais_citado", "N/D"),
        "preco_mais_citado": feedback.get("preco_mais_citado", "N/D"),
        "ativos_watchlist": watchlist.get("total", 0),
        "score_painel": painel.get("score_integrado"),
        "classificacao_painel": painel.get("classificacao_integrada"),
    }


def _calcular_score_prontidao_beta(contexto: Dict[str, Any]) -> int:
    """
    Score educacional de prontidão do produto para testes e venda inicial.
    Não é métrica científica. É uma leitura prática para orientar evolução.
    """
    total_feedbacks = int(contexto.get("total_feedbacks", 0) or 0)
    media_clareza = float(contexto.get("media_clareza", 0.0) or 0.0)
    media_utilidade = float(contexto.get("media_utilidade", 0.0) or 0.0)
    media_visual = float(contexto.get("media_visual", 0.0) or 0.0)
    media_confianca = float(contexto.get("media_confianca", 0.0) or 0.0)
    pagaria_sim = int(contexto.get("pagaria_sim", 0) or 0)
    pagaria_talvez = int(contexto.get("pagaria_talvez", 0) or 0)

    pontos = 0

    pontos += min(total_feedbacks * 4, 24)
    pontos += min(media_clareza * 1.6, 16)
    pontos += min(media_utilidade * 2.0, 20)
    pontos += min(media_visual * 1.2, 12)
    pontos += min(media_confianca * 1.6, 16)
    pontos += min(pagaria_sim * 4, 8)
    pontos += min(pagaria_talvez * 2, 4)

    return int(round(max(0, min(100, pontos))))


def _classificar_prontidao(score: int) -> str:
    if score >= 80:
        return "Pronto para pré-venda controlada"
    if score >= 65:
        return "Forte para beta fechado"
    if score >= 50:
        return "Validando com sinais positivos"
    if score >= 35:
        return "Ainda precisa de ajustes"
    return "Muito cedo para vender"


def _gerar_leitura_prontidao(score: int, classificacao: str) -> str:
    if classificacao == "Pronto para pré-venda controlada":
        return (
            "O produto já mostra sinais suficientes para testar uma oferta simples com poucos usuários. "
            "Ainda assim, venda de forma controlada, com promessa educacional clara e sem exagerar nos benefícios."
        )

    if classificacao == "Forte para beta fechado":
        return (
            "O produto parece forte para continuar o beta com mais usuários. "
            "Antes de vender, colete mais feedbacks, observe onde as pessoas travam e refine a proposta de valor."
        )

    if classificacao == "Validando com sinais positivos":
        return (
            "Há sinais promissores, mas ainda não é hora de escalar venda. "
            "O foco deve ser aumentar o número de feedbacks e melhorar clareza, confiança e utilidade percebida."
        )

    if classificacao == "Ainda precisa de ajustes":
        return (
            "O produto ainda precisa de refinamento antes de uma oferta paga. "
            "Priorize UX, onboarding, clareza da proposta e redução de complexidade."
        )

    return (
        "Ainda é cedo para vender. Primeiro precisamos testar com usuários reais, coletar feedbacks e entender se a dor é forte."
    )


def _injetar_css_beta() -> None:
    st.markdown(
        """
        <style>
            .beta-hero {
                padding: 1.6rem 1.65rem;
                border-radius: 28px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    radial-gradient(circle at top left, rgba(214, 181, 109, 0.23), transparent 30%),
                    radial-gradient(circle at bottom right, rgba(74, 144, 226, 0.22), transparent 34%),
                    linear-gradient(135deg, rgba(8, 15, 27, 0.99), rgba(5, 9, 18, 0.99));
                box-shadow: 0 18px 55px rgba(0, 0, 0, 0.34);
                margin-bottom: 1.25rem;
            }

            .beta-eyebrow {
                color: #d6b56d;
                font-size: 0.78rem;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.35rem;
            }

            .beta-title {
                color: #f4f7fb;
                font-size: 2rem;
                font-weight: 900;
                margin-bottom: 0.45rem;
                line-height: 1.14;
            }

            .beta-subtitle {
                color: rgba(244, 247, 251, 0.76);
                font-size: 1rem;
                line-height: 1.62;
                max-width: 1080px;
            }

            .beta-card {
                padding: 1.08rem 1.12rem;
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.035);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.18);
                height: 100%;
            }

            .beta-card-label {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .beta-card-value {
                color: #f4f7fb;
                font-size: 1.24rem;
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .beta-card-note {
                color: rgba(244, 247, 251, 0.68);
                font-size: 0.87rem;
                line-height: 1.47;
            }

            .beta-box {
                padding: 1.05rem 1.1rem;
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.028);
                margin-bottom: 1rem;
            }

            .beta-box-title {
                color: #f4f7fb;
                font-size: 1.08rem;
                font-weight: 850;
                margin-bottom: 0.35rem;
            }

            .beta-box-text {
                color: rgba(244, 247, 251, 0.70);
                font-size: 0.90rem;
                line-height: 1.52;
            }

            .beta-badge {
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

            .beta-highlight {
                padding: 0.95rem 1rem;
                border-radius: 16px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.92rem;
                line-height: 1.55;
                margin-bottom: 0.7rem;
            }

            .beta-copy {
                padding: 1rem 1.05rem;
                border-radius: 18px;
                background: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(255, 255, 255, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.92rem;
                line-height: 1.58;
                white-space: pre-wrap;
            }

            .beta-disclaimer {
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
        <div class="beta-card">
            <div class="beta-card-label">{label}</div>
            <div class="beta-card-value">{value}</div>
            <div class="beta-card-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _box(badge: str, title: str, text: str) -> None:
    st.markdown(
        f"""
        <div class="beta-box">
            <div class="beta-badge">{badge}</div>
            <div class="beta-box-title">{title}</div>
            <div class="beta-box-text">{text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _renderizar_copy(titulo: str, texto: str) -> None:
    st.markdown(f"#### {titulo}")
    st.markdown(
        f"""
        <div class="beta-copy">{texto}</div>
        """,
        unsafe_allow_html=True,
    )


def renderizar_beta_fechado() -> None:
    """
    Renderiza a Central do Beta Fechado.
    """
    _injetar_css_beta()

    contexto = _extrair_contexto_beta()
    score_prontidao = _calcular_score_prontidao_beta(contexto)
    classificacao = _classificar_prontidao(score_prontidao)
    leitura = _gerar_leitura_prontidao(score_prontidao, classificacao)

    st.session_state["resultado_beta_fechado"] = {
        "score_prontidao": score_prontidao,
        "classificacao": classificacao,
        "leitura": leitura,
        **contexto,
    }

    st.markdown(
        """
        <div class="beta-hero">
            <div class="beta-eyebrow">Do MVP ao primeiro usuário real</div>
            <div class="beta-title">Central do Beta Fechado</div>
            <div class="beta-subtitle">
                Esta área transforma a Máquina de Preço-Teto em um produto testável.
                O objetivo é guiar os primeiros usuários, coletar feedbacks, medir valor percebido
                e entender se existe disposição real de pagamento.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="beta-highlight">
            Regra principal: antes de vender forte, valide com poucos usuários reais.
            O beta fechado deve mostrar se as pessoas entendem, usam, confiam e pagariam pelo produto.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Prontidão do produto")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Score de prontidão", f"{score_prontidao}/100")

    with col_2:
        st.metric("Classificação", classificacao)

    with col_3:
        st.metric("Feedbacks coletados", contexto["total_feedbacks"])

    with col_4:
        st.metric("Pagaria", contexto["pagaria_sim"])

    st.progress(score_prontidao / 100)

    if score_prontidao >= 65:
        st.success(leitura)
    elif score_prontidao >= 50:
        st.warning(leitura)
    else:
        st.error(leitura)

    st.divider()

    st.markdown("### Métricas de validação")

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)

    with col_m1:
        _card(
            "Clareza",
            f"{float(contexto['media_clareza']):.1f}/10",
            "O usuário entende o que fazer?",
        )

    with col_m2:
        _card(
            "Utilidade",
            f"{float(contexto['media_utilidade']):.1f}/10",
            "O produto resolve uma dor real?",
        )

    with col_m3:
        _card(
            "Visual",
            f"{float(contexto['media_visual']):.1f}/10",
            "A aparência passa valor e confiança?",
        )

    with col_m4:
        _card(
            "Confiança",
            f"{float(contexto['media_confianca']):.1f}/10",
            "O usuário confiaria em usar para estudar investimentos?",
        )

    col_m5, col_m6, col_m7, col_m8 = st.columns(4)

    with col_m5:
        _card(
            "Perfil dominante",
            _fmt_texto(contexto["perfil_mais_comum"]),
            "Quem mais se interessou pelo produto.",
        )

    with col_m6:
        _card(
            "Módulo mais citado",
            _fmt_texto(contexto["modulo_mais_citado"]),
            "Provável destaque do marketing inicial.",
        )

    with col_m7:
        _card(
            "Preço mais citado",
            _fmt_texto(contexto["preco_mais_citado"]),
            "Primeiro sinal de disposição de pagamento.",
        )

    with col_m8:
        _card(
            "Talvez pagaria",
            str(contexto["pagaria_talvez"]),
            "Usuários que precisam de mais clareza ou valor.",
        )

    st.divider()

    st.markdown("### Quem deve testar primeiro")

    col_p1, col_p2, col_p3 = st.columns(3)

    with col_p1:
        _box(
            "Perfil 1",
            "Investidor iniciante curioso",
            "Pessoa que já investe ou quer investir, mas ainda se sente perdida para analisar ações, FIIs ou renda fixa.",
        )

    with col_p2:
        _box(
            "Perfil 2",
            "Investidor intermediário",
            "Pessoa que já compra ativos, acompanha mercado e quer organizar melhor valuation, tese e acompanhamento.",
        )

    with col_p3:
        _box(
            "Perfil 3",
            "Criador ou estudante de finanças",
            "Pessoa que gosta de análise, conteúdo financeiro, relatórios, estudos de caso e ferramentas educacionais.",
        )

    st.divider()

    st.markdown("### Roteiro de teste para usuário beta")

    roteiro = [
        {
            "Etapa": "1",
            "Tarefa": "Abrir a aba Produto",
            "Objetivo": "Entender se a proposta de valor está clara.",
            "Pergunta": "Você entendeu o que a plataforma faz em menos de 1 minuto?",
        },
        {
            "Etapa": "2",
            "Tarefa": "Ir para Início",
            "Objetivo": "Avaliar se a jornada guiada ajuda.",
            "Pergunta": "Você saberia qual é o próximo passo sem ajuda?",
        },
        {
            "Etapa": "3",
            "Tarefa": "Fazer uma análise em Modo Demonstração",
            "Objetivo": "Testar a experiência sem dados reais.",
            "Pergunta": "O fluxo ficou simples ou complexo demais?",
        },
        {
            "Etapa": "4",
            "Tarefa": "Abrir Valuation, Tese e Checklist",
            "Objetivo": "Validar os módulos centrais.",
            "Pergunta": "Qual módulo parece mais útil para você?",
        },
        {
            "Etapa": "5",
            "Tarefa": "Abrir Painel Executivo",
            "Objetivo": "Ver se a consolidação gera valor.",
            "Pergunta": "O painel ajuda a tomar uma decisão mais racional?",
        },
        {
            "Etapa": "6",
            "Tarefa": "Baixar um relatório",
            "Objetivo": "Validar a entrega final.",
            "Pergunta": "Você guardaria esse relatório para revisar depois?",
        },
        {
            "Etapa": "7",
            "Tarefa": "Salvar ativo na Watchlist",
            "Objetivo": "Testar rotina de acompanhamento.",
            "Pergunta": "Você usaria isso semanalmente?",
        },
        {
            "Etapa": "8",
            "Tarefa": "Preencher Feedback Beta",
            "Objetivo": "Coletar validação estruturada.",
            "Pergunta": "Você pagaria por uma versão melhorada?",
        },
    ]

    st.dataframe(
        roteiro,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Checklist de validação antes de vender")

    checklist = [
        {
            "Critério": "Pelo menos 10 feedbacks reais",
            "Por que importa": "Evita decidir com base em opinião própria.",
            "Meta": "10 a 30 usuários beta",
        },
        {
            "Critério": "Clareza média acima de 7",
            "Por que importa": "Usuário precisa entender sem explicação longa.",
            "Meta": ">= 7/10",
        },
        {
            "Critério": "Utilidade média acima de 8",
            "Por que importa": "Produto precisa resolver dor percebida.",
            "Meta": ">= 8/10",
        },
        {
            "Critério": "Confiança média acima de 7",
            "Por que importa": "Finanças exigem credibilidade.",
            "Meta": ">= 7/10",
        },
        {
            "Critério": "Pelo menos 30% dizendo que pagaria",
            "Por que importa": "Mostra intenção real de compra.",
            "Meta": "Sim ou forte talvez",
        },
        {
            "Critério": "Módulo campeão identificado",
            "Por que importa": "Marketing precisa de destaque claro.",
            "Meta": "1 módulo mais citado",
        },
        {
            "Critério": "Dificuldades recorrentes corrigidas",
            "Por que importa": "Fricção mata conversão.",
            "Meta": "Top 3 dores corrigidas",
        },
    ]

    st.dataframe(
        checklist,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Sinais de que podemos começar a vender")

    st.markdown(
        """
        Podemos testar uma primeira oferta paga quando:

        - usuários entendem a proposta sem explicação longa;
        - pelo menos alguns usuários dizem que pagariam;
        - o relatório é percebido como entrega valiosa;
        - a watchlist é vista como algo de uso recorrente;
        - o painel executivo gera sensação de clareza;
        - as maiores confusões já foram corrigidas;
        - existe um público mais provável definido.
        """
    )

    st.divider()

    st.markdown("### Copy para convidar usuários beta")

    copy_whatsapp = """Estou testando uma plataforma educacional que estou criando para análise de investimentos.

A ideia é ajudar o investidor a organizar valuation, preço-teto, margem de segurança, tese, riscos, checklist de erros, relatório e watchlist em um só lugar.

Ainda é uma versão beta, então quero feedback sincero:
- o que ficou claro;
- o que ficou confuso;
- se parece útil;
- se você pagaria por algo assim no futuro.

Posso te mandar o link para testar?"""

    copy_instagram = """Estou criando uma plataforma educacional para investidores que querem analisar ativos com mais método.

Ela organiza:
valuation, preço-teto, tese, riscos, checklist, relatório e watchlist.

Estou abrindo um beta fechado para poucas pessoas testarem e me darem feedback real.

Quer testar?"""

    copy_convite_direto = """Quero sua opinião sincera sobre um produto que estou construindo.

É uma plataforma de análise educacional para investidores. Ela não recomenda compra ou venda, mas ajuda a organizar o raciocínio antes de investir.

Você testaria por alguns minutos e me diria:
1. se entendeu a proposta;
2. se achou útil;
3. onde travou;
4. se pagaria por uma versão melhorada?"""

    _renderizar_copy("WhatsApp", copy_whatsapp)
    st.divider()
    _renderizar_copy("Instagram / Direct", copy_instagram)
    st.divider()
    _renderizar_copy("Convite direto", copy_convite_direto)

    st.markdown(
        """
        <div class="beta-disclaimer">
            <strong>Nota estratégica:</strong> o objetivo do beta fechado não é agradar todo mundo.
            É descobrir qual público entende mais rápido, vê mais valor e teria maior chance de pagar.
            O produto deve evoluir com base em comportamento real, não apenas opinião positiva.
        </div>
        """,
        unsafe_allow_html=True,
    )