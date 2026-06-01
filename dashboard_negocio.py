# dashboard_negocio.py

import csv
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st

from feedback_beta import carregar_feedbacks
from oferta_beta import carregar_lista_espera


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v1.29 — Dashboard de Negócio e Tração
# ------------------------------------------------------------
# Esta tela consolida sinais de validação do produto:
# - feedbacks beta
# - intenção de pagamento
# - lista de espera
# - dores dominantes
# - perfil mais interessado
# - score de tração
#
# Objetivo:
# ajudar a decidir se o produto está pronto para beta ampliado,
# pré-venda controlada ou ajustes antes de venda.
# ============================================================


CAMINHO_RESUMO_NEGOCIO = Path("resumo_negocio.csv")


def _safe_int(valor: Any, default: int = 0) -> int:
    try:
        return int(float(valor))
    except (TypeError, ValueError):
        return default


def _safe_float(valor: Any, default: float = 0.0) -> float:
    try:
        return float(valor)
    except (TypeError, ValueError):
        return default


def _media(registros: List[Dict[str, str]], campo: str) -> float:
    if len(registros) == 0:
        return 0.0

    valores = []

    for registro in registros:
        valor = _safe_float(registro.get(campo), 0.0)

        if valor > 0:
            valores.append(valor)

    if len(valores) == 0:
        return 0.0

    return sum(valores) / len(valores)


def _contar(registros: List[Dict[str, str]], campo: str, valor: str) -> int:
    return len([
        registro for registro in registros
        if registro.get(campo) == valor
    ])


def _mais_frequente(registros: List[Dict[str, str]], campo: str) -> str:
    if len(registros) == 0:
        return "N/D"

    contagem = {}

    for registro in registros:
        valor = registro.get(campo, "")

        if valor == "":
            continue

        contagem[valor] = contagem.get(valor, 0) + 1

    if len(contagem) == 0:
        return "N/D"

    return max(contagem, key=contagem.get)


def _percentual(parte: int, total: int) -> float:
    if total <= 0:
        return 0.0

    return (parte / total) * 100


def _extrair_resumo_feedback(feedbacks: List[Dict[str, str]]) -> Dict[str, Any]:
    total = len(feedbacks)

    pagaria_sim = _contar(feedbacks, "pagaria", "Sim")
    pagaria_talvez = _contar(feedbacks, "pagaria", "Talvez")
    pagaria_nao = _contar(feedbacks, "pagaria", "Não")

    return {
        "total_feedbacks": total,
        "media_clareza": _media(feedbacks, "nota_clareza"),
        "media_utilidade": _media(feedbacks, "nota_utilidade"),
        "media_visual": _media(feedbacks, "nota_visual"),
        "media_confianca": _media(feedbacks, "nota_confianca"),
        "feedback_pagaria_sim": pagaria_sim,
        "feedback_pagaria_talvez": pagaria_talvez,
        "feedback_pagaria_nao": pagaria_nao,
        "feedback_taxa_pagaria": _percentual(pagaria_sim, total),
        "perfil_feedback_mais_comum": _mais_frequente(feedbacks, "perfil_usuario"),
        "modulo_mais_util": _mais_frequente(feedbacks, "modulo_mais_util"),
        "preco_feedback_mais_citado": _mais_frequente(feedbacks, "preco_aceitavel"),
        "objetivo_mais_comum": _mais_frequente(feedbacks, "objetivo_principal"),
    }


def _extrair_resumo_lista(registros: List[Dict[str, str]]) -> Dict[str, Any]:
    total = len(registros)

    pagaria_sim = _contar(registros, "pagaria_agora", "Sim, se o preço fosse justo")
    pagaria_talvez = _contar(registros, "pagaria_agora", "Talvez, preciso testar mais")
    pagaria_nao = _contar(registros, "pagaria_agora", "Não pagaria agora")

    return {
        "total_lista_espera": total,
        "lista_pagaria_sim": pagaria_sim,
        "lista_pagaria_talvez": pagaria_talvez,
        "lista_pagaria_nao": pagaria_nao,
        "lista_taxa_pagaria": _percentual(pagaria_sim, total),
        "perfil_lista_mais_comum": _mais_frequente(registros, "perfil"),
        "dor_mais_comum": _mais_frequente(registros, "principal_dor"),
        "plano_mais_citado": _mais_frequente(registros, "plano_interesse"),
        "preco_lista_mais_citado": _mais_frequente(registros, "preco_aceitavel"),
    }


def _calcular_score_tracao(
    resumo_feedback: Dict[str, Any],
    resumo_lista: Dict[str, Any],
) -> int:
    total_feedbacks = int(resumo_feedback["total_feedbacks"])
    total_lista = int(resumo_lista["total_lista_espera"])

    media_clareza = float(resumo_feedback["media_clareza"])
    media_utilidade = float(resumo_feedback["media_utilidade"])
    media_confianca = float(resumo_feedback["media_confianca"])
    media_visual = float(resumo_feedback["media_visual"])

    feedback_pagaria_sim = int(resumo_feedback["feedback_pagaria_sim"])
    lista_pagaria_sim = int(resumo_lista["lista_pagaria_sim"])
    lista_pagaria_talvez = int(resumo_lista["lista_pagaria_talvez"])

    pontos = 0.0

    pontos += min(total_feedbacks * 3.0, 18)
    pontos += min(total_lista * 4.0, 24)

    pontos += min(media_clareza * 1.3, 13)
    pontos += min(media_utilidade * 1.8, 18)
    pontos += min(media_confianca * 1.4, 14)
    pontos += min(media_visual * 0.8, 8)

    pontos += min(feedback_pagaria_sim * 3.0, 9)
    pontos += min(lista_pagaria_sim * 4.0, 12)
    pontos += min(lista_pagaria_talvez * 1.0, 4)

    return int(round(max(0, min(100, pontos))))


def _classificar_tracao(score: int) -> str:
    if score >= 80:
        return "Tração forte para pré-venda"
    if score >= 65:
        return "Boa tração para beta ampliado"
    if score >= 50:
        return "Sinais iniciais positivos"
    if score >= 35:
        return "Validação ainda fraca"
    return "Sem tração suficiente"


def _gerar_leitura_tracao(score: int, classificacao: str) -> str:
    if classificacao == "Tração forte para pré-venda":
        return (
            "O produto já mostra sinais relevantes de interesse, utilidade e intenção de pagamento. "
            "A próxima ação deve ser testar uma pré-venda controlada com poucos usuários, deixando claro que é um produto educacional em evolução."
        )

    if classificacao == "Boa tração para beta ampliado":
        return (
            "O produto parece pronto para ser testado com mais usuários. "
            "Antes de cobrar, amplie o beta, colete mais feedbacks e observe se a intenção de pagamento se mantém."
        )

    if classificacao == "Sinais iniciais positivos":
        return (
            "Existem sinais promissores, mas ainda falta volume de validação. "
            "Continue chamando usuários beta, melhore o onboarding e busque entender qual dor é mais forte."
        )

    if classificacao == "Validação ainda fraca":
        return (
            "A validação ainda está fraca. O foco deve ser melhorar clareza, proposta de valor, UX e convite para teste. "
            "Não é o momento de vender com força."
        )

    return (
        "Ainda não há sinais suficientes de tração. Primeiro colete feedbacks reais e cadastros na lista de espera."
    )


def _gerar_proximas_acoes(
    resumo_feedback: Dict[str, Any],
    resumo_lista: Dict[str, Any],
    score: int,
) -> List[str]:
    acoes = []

    total_feedbacks = int(resumo_feedback["total_feedbacks"])
    total_lista = int(resumo_lista["total_lista_espera"])
    media_clareza = float(resumo_feedback["media_clareza"])
    media_utilidade = float(resumo_feedback["media_utilidade"])
    media_confianca = float(resumo_feedback["media_confianca"])
    lista_pagaria_sim = int(resumo_lista["lista_pagaria_sim"])

    if total_feedbacks < 10:
        acoes.append("Coletar pelo menos 10 feedbacks reais antes de tomar decisão comercial.")

    if total_lista < 10:
        acoes.append("Convidar mais pessoas para entrar na lista de espera e medir interesse real.")

    if media_clareza < 7 and total_feedbacks > 0:
        acoes.append("Melhorar a clareza da tela Produto e da jornada Início.")

    if media_utilidade < 8 and total_feedbacks > 0:
        acoes.append("Reforçar a entrega de valor nos módulos Valuation, Relatórios e Watchlist.")

    if media_confianca < 7 and total_feedbacks > 0:
        acoes.append("Melhorar avisos educacionais, explicações de premissas e transparência do método.")

    if lista_pagaria_sim >= 5:
        acoes.append("Preparar uma pré-venda manual para poucos usuários com preço beta controlado.")

    if score >= 65:
        acoes.append("Criar uma página externa simples de apresentação e captar mais interessados.")

    if len(acoes) == 0:
        acoes.append("Continuar testando com usuários reais e observar padrões de comportamento.")

    return acoes


def _criar_resumo_markdown(
    resumo_feedback: Dict[str, Any],
    resumo_lista: Dict[str, Any],
    score: int,
    classificacao: str,
    leitura: str,
    proximas_acoes: List[str],
) -> str:
    linhas_acoes = "\n".join([f"- {acao}" for acao in proximas_acoes])

    return f"""# Resumo de Negócio — Máquina de Preço-Teto

Data: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Score de Tração

**Score:** {score}/100  
**Classificação:** {classificacao}

## Leitura Estratégica

{leitura}

## Feedback Beta

| Métrica | Valor |
|---|---|
| Total de feedbacks | {resumo_feedback["total_feedbacks"]} |
| Clareza média | {resumo_feedback["media_clareza"]:.1f}/10 |
| Utilidade média | {resumo_feedback["media_utilidade"]:.1f}/10 |
| Visual médio | {resumo_feedback["media_visual"]:.1f}/10 |
| Confiança média | {resumo_feedback["media_confianca"]:.1f}/10 |
| Pagaria | {resumo_feedback["feedback_pagaria_sim"]} |
| Talvez pagaria | {resumo_feedback["feedback_pagaria_talvez"]} |
| Perfil mais comum | {resumo_feedback["perfil_feedback_mais_comum"]} |
| Módulo mais útil | {resumo_feedback["modulo_mais_util"]} |
| Preço mais citado | {resumo_feedback["preco_feedback_mais_citado"]} |

## Lista de Espera

| Métrica | Valor |
|---|---|
| Total de interessados | {resumo_lista["total_lista_espera"]} |
| Pagaria agora | {resumo_lista["lista_pagaria_sim"]} |
| Talvez pagaria | {resumo_lista["lista_pagaria_talvez"]} |
| Perfil mais comum | {resumo_lista["perfil_lista_mais_comum"]} |
| Dor mais comum | {resumo_lista["dor_mais_comum"]} |
| Plano mais citado | {resumo_lista["plano_mais_citado"]} |
| Preço mais citado | {resumo_lista["preco_lista_mais_citado"]} |

## Próximas Ações

{linhas_acoes}

## Nota

Este resumo é uma ferramenta interna de decisão. Ele não prova sucesso comercial, mas ajuda a organizar sinais de validação antes de investir em venda, tráfego ou reconstrução técnica.
"""


def _injetar_css_negocio() -> None:
    st.markdown(
        """
        <style>
            .neg-hero {
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

            .neg-eyebrow {
                color: #d6b56d;
                font-size: 0.78rem;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.35rem;
            }

            .neg-title {
                color: #f4f7fb;
                font-size: 2.08rem;
                font-weight: 900;
                margin-bottom: 0.45rem;
                line-height: 1.14;
            }

            .neg-subtitle {
                color: rgba(244, 247, 251, 0.76);
                font-size: 1rem;
                line-height: 1.62;
                max-width: 1080px;
            }

            .neg-card {
                padding: 1.1rem 1.15rem;
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.035);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.18);
                height: 100%;
            }

            .neg-card-label {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .neg-card-value {
                color: #f4f7fb;
                font-size: 1.22rem;
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .neg-card-note {
                color: rgba(244, 247, 251, 0.68);
                font-size: 0.87rem;
                line-height: 1.47;
            }

            .neg-highlight {
                padding: 0.95rem 1rem;
                border-radius: 16px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.92rem;
                line-height: 1.55;
                margin-bottom: 0.7rem;
            }

            .neg-disclaimer {
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
        <div class="neg-card">
            <div class="neg-card-label">{label}</div>
            <div class="neg-card-value">{value}</div>
            <div class="neg-card-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def renderizar_dashboard_negocio() -> None:
    """
    Renderiza o Dashboard de Negócio e Tração.
    """
    _injetar_css_negocio()

    feedbacks = carregar_feedbacks()
    lista_espera = carregar_lista_espera()

    resumo_feedback = _extrair_resumo_feedback(feedbacks)
    resumo_lista = _extrair_resumo_lista(lista_espera)

    score_tracao = _calcular_score_tracao(
        resumo_feedback=resumo_feedback,
        resumo_lista=resumo_lista,
    )

    classificacao = _classificar_tracao(score_tracao)
    leitura = _gerar_leitura_tracao(score_tracao, classificacao)

    proximas_acoes = _gerar_proximas_acoes(
        resumo_feedback=resumo_feedback,
        resumo_lista=resumo_lista,
        score=score_tracao,
    )

    st.session_state["resultado_dashboard_negocio"] = {
        "score_tracao": score_tracao,
        "classificacao": classificacao,
        "leitura": leitura,
        "proximas_acoes": proximas_acoes,
        **resumo_feedback,
        **resumo_lista,
    }

    st.markdown(
        """
        <div class="neg-hero">
            <div class="neg-eyebrow">Painel do fundador</div>
            <div class="neg-title">Dashboard de Negócio e Tração</div>
            <div class="neg-subtitle">
                Consolide feedbacks, lista de espera, intenção de pagamento, dores dominantes
                e sinais de validação. Esta tela ajuda a decidir se o produto deve continuar em beta,
                avançar para pré-venda ou voltar para ajustes de clareza e valor.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="neg-highlight">
            O objetivo agora não é apenas programar. É medir sinais reais de mercado:
            as pessoas entendem, usam, confiam e demonstram intenção de pagar?
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Score de tração")

    col_top_1, col_top_2, col_top_3, col_top_4 = st.columns(4)

    with col_top_1:
        st.metric("Score de tração", f"{score_tracao}/100")

    with col_top_2:
        st.metric("Classificação", classificacao)

    with col_top_3:
        st.metric("Feedbacks", resumo_feedback["total_feedbacks"])

    with col_top_4:
        st.metric("Lista de espera", resumo_lista["total_lista_espera"])

    st.progress(score_tracao / 100)

    if score_tracao >= 65:
        st.success(leitura)
    elif score_tracao >= 50:
        st.warning(leitura)
    else:
        st.error(leitura)

    st.divider()

    st.markdown("### Validação do produto")

    col_f1, col_f2, col_f3, col_f4 = st.columns(4)

    with col_f1:
        _card(
            "Clareza",
            f"{resumo_feedback['media_clareza']:.1f}/10",
            "O usuário entende a jornada?",
        )

    with col_f2:
        _card(
            "Utilidade",
            f"{resumo_feedback['media_utilidade']:.1f}/10",
            "O produto resolve dor real?",
        )

    with col_f3:
        _card(
            "Confiança",
            f"{resumo_feedback['media_confianca']:.1f}/10",
            "O usuário confiaria para estudar investimentos?",
        )

    with col_f4:
        _card(
            "Visual",
            f"{resumo_feedback['media_visual']:.1f}/10",
            "O produto parece premium?",
        )

    col_f5, col_f6, col_f7, col_f8 = st.columns(4)

    with col_f5:
        _card(
            "Pagaria no feedback",
            str(resumo_feedback["feedback_pagaria_sim"]),
            f"{resumo_feedback['feedback_taxa_pagaria']:.1f}% dos feedbacks.",
        )

    with col_f6:
        _card(
            "Módulo campeão",
            resumo_feedback["modulo_mais_util"],
            "Principal gancho do marketing.",
        )

    with col_f7:
        _card(
            "Objetivo comum",
            resumo_feedback["objetivo_mais_comum"],
            "Motivação mais frequente.",
        )

    with col_f8:
        _card(
            "Preço citado",
            resumo_feedback["preco_feedback_mais_citado"],
            "Sinal de valor percebido.",
        )

    st.divider()

    st.markdown("### Validação da oferta")

    col_o1, col_o2, col_o3, col_o4 = st.columns(4)

    with col_o1:
        _card(
            "Interessados",
            str(resumo_lista["total_lista_espera"]),
            "Pessoas na lista de espera.",
        )

    with col_o2:
        _card(
            "Pagaria agora",
            str(resumo_lista["lista_pagaria_sim"]),
            f"{resumo_lista['lista_taxa_pagaria']:.1f}% da lista.",
        )

    with col_o3:
        _card(
            "Talvez pagaria",
            str(resumo_lista["lista_pagaria_talvez"]),
            "Precisa de mais prova de valor.",
        )

    with col_o4:
        _card(
            "Plano citado",
            resumo_lista["plano_mais_citado"],
            "Possível plano inicial.",
        )

    col_o5, col_o6, col_o7 = st.columns(3)

    with col_o5:
        _card(
            "Perfil dominante",
            resumo_lista["perfil_lista_mais_comum"],
            "Público inicial mais provável.",
        )

    with col_o6:
        _card(
            "Dor dominante",
            resumo_lista["dor_mais_comum"],
            "Tema central da copy.",
        )

    with col_o7:
        _card(
            "Preço citado",
            resumo_lista["preco_lista_mais_citado"],
            "Faixa de preço para testar.",
        )

    st.divider()

    st.markdown("### Próximas ações recomendadas")

    for acao in proximas_acoes:
        st.markdown(f"- {acao}")

    st.divider()

    st.markdown("### Decisão estratégica sugerida")

    if score_tracao >= 80:
        st.success(
            "Decisão sugerida: preparar uma pré-venda controlada para poucos usuários, com preço beta e promessa educacional clara."
        )
    elif score_tracao >= 65:
        st.info(
            "Decisão sugerida: ampliar o beta para mais usuários e começar a preparar uma landing page externa."
        )
    elif score_tracao >= 50:
        st.warning(
            "Decisão sugerida: continuar validando. Ainda não escalar venda, mas já observar preço, dor dominante e público mais interessado."
        )
    else:
        st.error(
            "Decisão sugerida: não vender ainda. Melhorar UX, proposta de valor, onboarding e quantidade de testes reais."
        )

    st.divider()

    st.markdown("### Baixar resumo de negócio")

    resumo_markdown = _criar_resumo_markdown(
        resumo_feedback=resumo_feedback,
        resumo_lista=resumo_lista,
        score=score_tracao,
        classificacao=classificacao,
        leitura=leitura,
        proximas_acoes=proximas_acoes,
    )

    st.download_button(
        label="Baixar resumo de negócio (.md)",
        data=resumo_markdown,
        file_name="resumo_negocio_maquina_preco_teto.md",
        mime="text/markdown",
        key="download_resumo_negocio",
    )

    st.markdown(
        """
        <div class="neg-disclaimer">
            <strong>Nota estratégica:</strong> este painel não garante sucesso comercial.
            Ele organiza sinais de validação para ajudar na tomada de decisão.
            O próximo passo deve ser baseado em comportamento real dos usuários, não apenas opinião positiva.
        </div>
        """,
        unsafe_allow_html=True,
    )