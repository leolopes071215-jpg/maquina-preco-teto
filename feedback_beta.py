# feedback_beta.py

import csv
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v1.26 — Feedback Beta e Validação de Produto
# ------------------------------------------------------------
# Esta tela coleta feedback de usuários beta.
# Objetivo:
# - validar clareza
# - medir valor percebido
# - identificar fricções
# - testar intenção de pagamento
# - preparar o produto para venda
# ============================================================


CAMINHO_FEEDBACK = Path("feedback_beta.csv")


CAMPOS_FEEDBACK = [
    "id",
    "data_criacao",
    "nome",
    "perfil_usuario",
    "nivel_experiencia",
    "objetivo_principal",
    "nota_clareza",
    "nota_utilidade",
    "nota_visual",
    "nota_confianca",
    "modulo_mais_util",
    "maior_dificuldade",
    "pagaria",
    "preco_aceitavel",
    "comentario",
    "sugestao",
]


PERFIS_USUARIO = [
    "Investidor iniciante",
    "Investidor intermediário",
    "Investidor avançado",
    "Estudante",
    "Criador de conteúdo financeiro",
    "Assessor/analista",
    "Curioso sobre investimentos",
    "Outro",
]


NIVEIS_EXPERIENCIA = [
    "Nunca investi",
    "Invisto há menos de 1 ano",
    "Invisto entre 1 e 3 anos",
    "Invisto entre 3 e 5 anos",
    "Invisto há mais de 5 anos",
]


OBJETIVOS_PRINCIPAIS = [
    "Aprender a analisar melhor",
    "Calcular preço-teto",
    "Organizar minhas análises",
    "Comparar ativos",
    "Gerar relatórios",
    "Acompanhar ativos na watchlist",
    "Evitar decisões emocionais",
    "Outro",
]


MODULOS = [
    "Produto",
    "Início",
    "Painel Executivo",
    "Valuation",
    "Simulador",
    "Tese & Convicção",
    "Checklist",
    "Watchlist",
    "Relatórios",
    "Multiativos",
    "Ações Brasil",
    "FIIs",
    "Renda Fixa",
    "Educação",
]


OPCOES_PAGARIA = [
    "Sim",
    "Talvez",
    "Não",
]


PRECOS_ACEITAVEIS = [
    "Não pagaria",
    "Até R$ 9,90/mês",
    "Até R$ 19,90/mês",
    "Até R$ 29,90/mês",
    "Até R$ 49,90/mês",
    "Mais de R$ 49,90/mês",
    "Prefiro pagar uma vez, não assinatura",
]


def _garantir_arquivo_feedback() -> None:
    if CAMINHO_FEEDBACK.exists():
        return

    with open(CAMINHO_FEEDBACK, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_FEEDBACK)
        escritor.writeheader()


def carregar_feedbacks() -> List[Dict[str, str]]:
    _garantir_arquivo_feedback()

    with open(CAMINHO_FEEDBACK, "r", newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)

        feedbacks = []

        for linha in leitor:
            feedback = {campo: linha.get(campo, "") for campo in CAMPOS_FEEDBACK}
            feedbacks.append(feedback)

        return feedbacks


def salvar_feedbacks(feedbacks: List[Dict[str, Any]]) -> None:
    with open(CAMINHO_FEEDBACK, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_FEEDBACK)
        escritor.writeheader()

        for feedback in feedbacks:
            linha = {campo: feedback.get(campo, "") for campo in CAMPOS_FEEDBACK}
            escritor.writerow(linha)


def adicionar_feedback(
    nome: str,
    perfil_usuario: str,
    nivel_experiencia: str,
    objetivo_principal: str,
    nota_clareza: int,
    nota_utilidade: int,
    nota_visual: int,
    nota_confianca: int,
    modulo_mais_util: str,
    maior_dificuldade: str,
    pagaria: str,
    preco_aceitavel: str,
    comentario: str,
    sugestao: str,
) -> None:
    feedbacks = carregar_feedbacks()

    novo_feedback = {
        "id": str(uuid.uuid4())[:8],
        "data_criacao": datetime.now().isoformat(timespec="minutes"),
        "nome": nome.strip(),
        "perfil_usuario": perfil_usuario,
        "nivel_experiencia": nivel_experiencia,
        "objetivo_principal": objetivo_principal,
        "nota_clareza": nota_clareza,
        "nota_utilidade": nota_utilidade,
        "nota_visual": nota_visual,
        "nota_confianca": nota_confianca,
        "modulo_mais_util": modulo_mais_util,
        "maior_dificuldade": maior_dificuldade.strip(),
        "pagaria": pagaria,
        "preco_aceitavel": preco_aceitavel,
        "comentario": comentario.strip(),
        "sugestao": sugestao.strip(),
    }

    feedbacks.append(novo_feedback)
    salvar_feedbacks(feedbacks)


def limpar_feedbacks() -> None:
    salvar_feedbacks([])


def _safe_int(valor: Any, default: int = 0) -> int:
    try:
        return int(float(valor))
    except (TypeError, ValueError):
        return default


def _media(feedbacks: List[Dict[str, str]], campo: str) -> float:
    if len(feedbacks) == 0:
        return 0.0

    valores = [_safe_int(feedback.get(campo)) for feedback in feedbacks]
    valores_validos = [valor for valor in valores if valor > 0]

    if len(valores_validos) == 0:
        return 0.0

    return sum(valores_validos) / len(valores_validos)


def _contar(feedbacks: List[Dict[str, str]], campo: str, valor: str) -> int:
    return len([
        feedback for feedback in feedbacks
        if feedback.get(campo) == valor
    ])


def _item_mais_frequente(feedbacks: List[Dict[str, str]], campo: str) -> str:
    if len(feedbacks) == 0:
        return "N/D"

    contagem = {}

    for feedback in feedbacks:
        valor = feedback.get(campo, "")

        if valor == "":
            continue

        contagem[valor] = contagem.get(valor, 0) + 1

    if len(contagem) == 0:
        return "N/D"

    return max(contagem, key=contagem.get)


def _gerar_resumo(feedbacks: List[Dict[str, str]]) -> Dict[str, Any]:
    total = len(feedbacks)

    return {
        "total": total,
        "media_clareza": _media(feedbacks, "nota_clareza"),
        "media_utilidade": _media(feedbacks, "nota_utilidade"),
        "media_visual": _media(feedbacks, "nota_visual"),
        "media_confianca": _media(feedbacks, "nota_confianca"),
        "pagaria_sim": _contar(feedbacks, "pagaria", "Sim"),
        "pagaria_talvez": _contar(feedbacks, "pagaria", "Talvez"),
        "pagaria_nao": _contar(feedbacks, "pagaria", "Não"),
        "perfil_mais_comum": _item_mais_frequente(feedbacks, "perfil_usuario"),
        "modulo_mais_citado": _item_mais_frequente(feedbacks, "modulo_mais_util"),
        "preco_mais_citado": _item_mais_frequente(feedbacks, "preco_aceitavel"),
    }


def _preparar_tabela_feedback(feedbacks: List[Dict[str, str]]) -> List[Dict[str, str]]:
    tabela = []

    for feedback in reversed(feedbacks):
        tabela.append(
            {
                "Data": feedback.get("data_criacao", ""),
                "Nome": feedback.get("nome", ""),
                "Perfil": feedback.get("perfil_usuario", ""),
                "Experiência": feedback.get("nivel_experiencia", ""),
                "Objetivo": feedback.get("objetivo_principal", ""),
                "Clareza": feedback.get("nota_clareza", ""),
                "Utilidade": feedback.get("nota_utilidade", ""),
                "Visual": feedback.get("nota_visual", ""),
                "Confiança": feedback.get("nota_confianca", ""),
                "Módulo mais útil": feedback.get("modulo_mais_util", ""),
                "Pagaria": feedback.get("pagaria", ""),
                "Preço aceitável": feedback.get("preco_aceitavel", ""),
                "Dificuldade": feedback.get("maior_dificuldade", ""),
                "Comentário": feedback.get("comentario", ""),
                "Sugestão": feedback.get("sugestao", ""),
            }
        )

    return tabela


def _injetar_css_feedback() -> None:
    st.markdown(
        """
        <style>
            .fb-hero {
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

            .fb-eyebrow {
                color: #d6b56d;
                font-size: 0.78rem;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.35rem;
            }

            .fb-title {
                color: #f4f7fb;
                font-size: 2rem;
                font-weight: 900;
                margin-bottom: 0.45rem;
                line-height: 1.14;
            }

            .fb-subtitle {
                color: rgba(244, 247, 251, 0.76);
                font-size: 1rem;
                line-height: 1.62;
                max-width: 1080px;
            }

            .fb-card {
                padding: 1.08rem 1.12rem;
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.035);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.18);
                height: 100%;
            }

            .fb-card-label {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .fb-card-value {
                color: #f4f7fb;
                font-size: 1.24rem;
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .fb-card-note {
                color: rgba(244, 247, 251, 0.68);
                font-size: 0.87rem;
                line-height: 1.47;
            }

            .fb-highlight {
                padding: 0.95rem 1rem;
                border-radius: 16px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.92rem;
                line-height: 1.55;
                margin-bottom: 0.7rem;
            }

            .fb-disclaimer {
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
        <div class="fb-card">
            <div class="fb-card-label">{label}</div>
            <div class="fb-card-value">{value}</div>
            <div class="fb-card-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def renderizar_feedback_beta() -> None:
    """
    Renderiza a Central de Feedback Beta.
    """
    _injetar_css_feedback()

    feedbacks = carregar_feedbacks()
    resumo = _gerar_resumo(feedbacks)

    st.session_state["resultado_feedback_beta"] = resumo

    st.markdown(
        """
        <div class="fb-hero">
            <div class="fb-eyebrow">Validação antes da venda</div>
            <div class="fb-title">Feedback Beta e Validação de Produto</div>
            <div class="fb-subtitle">
                Use esta tela para coletar feedback de usuários reais. O objetivo é descobrir
                se a plataforma é clara, útil, confiável, visualmente forte e se as pessoas pagariam por ela.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="fb-highlight">
            Antes de vender forte, valide com pessoas reais. O feedback certo mostra onde o usuário trava,
            qual módulo gera mais valor e qual preço faz sentido.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Resumo da validação")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Feedbacks", resumo["total"])

    with col_2:
        st.metric("Clareza média", f"{resumo['media_clareza']:.1f}/10")

    with col_3:
        st.metric("Utilidade média", f"{resumo['media_utilidade']:.1f}/10")

    with col_4:
        st.metric("Confiança média", f"{resumo['media_confianca']:.1f}/10")

    col_5, col_6, col_7, col_8 = st.columns(4)

    with col_5:
        _card("Pagaria", str(resumo["pagaria_sim"]), "Quantidade de usuários que responderam sim.")

    with col_6:
        _card("Talvez pagaria", str(resumo["pagaria_talvez"]), "Usuários que precisam de mais valor ou clareza.")

    with col_7:
        _card("Perfil mais comum", resumo["perfil_mais_comum"], "Público que mais respondeu ao teste.")

    with col_8:
        _card("Preço mais citado", resumo["preco_mais_citado"], "Faixa de preço mais recorrente.")

    st.divider()

    st.markdown("### Registrar feedback de usuário")

    with st.form("form_feedback_beta"):
        col_a, col_b = st.columns(2)

        with col_a:
            nome = st.text_input(
                "Nome ou identificação",
                value="",
                placeholder="Ex: João, investidor beta 01, amigo da faculdade...",
                key="fb_nome",
            )

            perfil_usuario = st.selectbox(
                "Perfil do usuário",
                PERFIS_USUARIO,
                key="fb_perfil_usuario",
            )

            nivel_experiencia = st.selectbox(
                "Nível de experiência com investimentos",
                NIVEIS_EXPERIENCIA,
                key="fb_nivel_experiencia",
            )

            objetivo_principal = st.selectbox(
                "Principal objetivo ao usar o app",
                OBJETIVOS_PRINCIPAIS,
                key="fb_objetivo_principal",
            )

            modulo_mais_util = st.selectbox(
                "Módulo mais útil",
                MODULOS,
                key="fb_modulo_mais_util",
            )

        with col_b:
            nota_clareza = st.slider(
                "Nota de clareza do app",
                min_value=0,
                max_value=10,
                value=7,
                key="fb_nota_clareza",
            )

            nota_utilidade = st.slider(
                "Nota de utilidade percebida",
                min_value=0,
                max_value=10,
                value=8,
                key="fb_nota_utilidade",
            )

            nota_visual = st.slider(
                "Nota da estética/visual",
                min_value=0,
                max_value=10,
                value=8,
                key="fb_nota_visual",
            )

            nota_confianca = st.slider(
                "Nota de confiança no produto",
                min_value=0,
                max_value=10,
                value=7,
                key="fb_nota_confianca",
            )

            pagaria = st.selectbox(
                "Pagaria por esse produto?",
                OPCOES_PAGARIA,
                key="fb_pagaria",
            )

            preco_aceitavel = st.selectbox(
                "Preço aceitável",
                PRECOS_ACEITAVEIS,
                key="fb_preco_aceitavel",
            )

        maior_dificuldade = st.text_area(
            "Qual foi a maior dificuldade ou ponto de confusão?",
            value="",
            height=90,
            key="fb_maior_dificuldade",
        )

        comentario = st.text_area(
            "Comentário geral sobre o produto",
            value="",
            height=90,
            key="fb_comentario",
        )

        sugestao = st.text_area(
            "Sugestão de melhoria",
            value="",
            height=90,
            key="fb_sugestao",
        )

        enviar = st.form_submit_button("Salvar feedback")

        if enviar:
            if nome.strip() == "":
                st.error("Preencha pelo menos uma identificação para o feedback.")
            else:
                adicionar_feedback(
                    nome=nome,
                    perfil_usuario=perfil_usuario,
                    nivel_experiencia=nivel_experiencia,
                    objetivo_principal=objetivo_principal,
                    nota_clareza=nota_clareza,
                    nota_utilidade=nota_utilidade,
                    nota_visual=nota_visual,
                    nota_confianca=nota_confianca,
                    modulo_mais_util=modulo_mais_util,
                    maior_dificuldade=maior_dificuldade,
                    pagaria=pagaria,
                    preco_aceitavel=preco_aceitavel,
                    comentario=comentario,
                    sugestao=sugestao,
                )

                st.success("Feedback salvo com sucesso.")
                st.rerun()

    st.divider()

    st.markdown("### Feedbacks registrados")

    feedbacks = carregar_feedbacks()

    if len(feedbacks) == 0:
        st.info("Nenhum feedback registrado ainda.")
    else:
        tabela = _preparar_tabela_feedback(feedbacks)

        st.dataframe(
            tabela,
            use_container_width=True,
            hide_index=True,
        )

        st.divider()

        st.markdown("### Exportar ou limpar feedbacks")

        col_down, col_clean = st.columns(2)

        with col_down:
            with open(CAMINHO_FEEDBACK, "rb") as arquivo:
                st.download_button(
                    label="Baixar feedbacks em CSV",
                    data=arquivo,
                    file_name="feedback_beta.csv",
                    mime="text/csv",
                    key="fb_download_csv",
                )

        with col_clean:
            confirmar = st.checkbox(
                "Confirmar limpeza dos feedbacks",
                value=False,
                key="fb_confirmar_limpeza",
            )

            if st.button("Limpar feedbacks", key="fb_limpar"):
                if confirmar:
                    limpar_feedbacks()
                    st.success("Feedbacks limpos com sucesso.")
                    st.rerun()
                else:
                    st.warning("Marque a confirmação antes de limpar os feedbacks.")

    st.divider()

    st.markdown("### Como interpretar os feedbacks")

    st.markdown(
        """
        - Se a **clareza média** estiver baixa, o problema é UX/onboarding.
        - Se a **utilidade média** estiver baixa, o produto ainda não está resolvendo uma dor forte.
        - Se a **confiança média** estiver baixa, faltam avisos, fontes, explicações ou consistência.
        - Se muitos responderem **talvez pagaria**, precisamos melhorar valor percebido antes de vender.
        - Se um módulo aparecer muitas vezes como mais útil, ele deve virar destaque no marketing.
        """
    )

    st.markdown(
        """
        <div class="fb-disclaimer">
            <strong>Nota de validação:</strong> esta área é para aprendizado de produto.
            Não use os feedbacks para forçar uma conclusão. O objetivo é entender o comportamento real dos usuários,
            remover fricções e melhorar a proposta de valor antes de iniciar vendas.
        </div>
        """,
        unsafe_allow_html=True,
    )