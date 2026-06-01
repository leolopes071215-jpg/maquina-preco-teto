# oferta_beta.py

import csv
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v1.28 — Oferta Beta e Lista de Espera
# ------------------------------------------------------------
# Esta tela prepara a primeira oferta controlada do produto.
# Objetivo:
# - apresentar proposta de valor
# - testar intenção de compra
# - captar interessados
# - medir plano/preço mais atrativo
# - preparar futura monetização
# ============================================================


CAMINHO_LISTA_ESPERA = Path("lista_espera_beta.csv")


CAMPOS_LISTA_ESPERA = [
    "id",
    "data_criacao",
    "nome",
    "contato",
    "perfil",
    "principal_dor",
    "plano_interesse",
    "preco_aceitavel",
    "pagaria_agora",
    "comentario",
]


PERFIS = [
    "Investidor iniciante",
    "Investidor intermediário",
    "Investidor avançado",
    "Estudante",
    "Criador de conteúdo financeiro",
    "Assessor/analista",
    "Curioso sobre investimentos",
    "Outro",
]


DORES = [
    "Tenho medo de pagar caro em ações",
    "Não sei calcular preço-teto",
    "Tenho dificuldade de organizar minhas análises",
    "Quero comparar ativos com mais método",
    "Quero gerar relatórios de análise",
    "Quero acompanhar ativos em uma watchlist",
    "Quero evitar decisões emocionais",
    "Quero estudar ações, FIIs e renda fixa",
    "Outra",
]


PLANOS_INTERESSE = [
    "Plano Gratuito",
    "Plano Premium",
    "Plano Pro",
    "Ainda não sei",
]


PRECOS_ACEITAVEIS = [
    "Não pagaria agora",
    "Até R$ 9,90/mês",
    "Até R$ 19,90/mês",
    "Até R$ 29,90/mês",
    "Até R$ 49,90/mês",
    "Mais de R$ 49,90/mês",
    "Prefiro pagamento único",
]


OPCOES_PAGARIA_AGORA = [
    "Sim, se o preço fosse justo",
    "Talvez, preciso testar mais",
    "Não pagaria agora",
]


def _garantir_arquivo_lista() -> None:
    if CAMINHO_LISTA_ESPERA.exists():
        return

    with open(CAMINHO_LISTA_ESPERA, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_LISTA_ESPERA)
        escritor.writeheader()


def carregar_lista_espera() -> List[Dict[str, str]]:
    _garantir_arquivo_lista()

    with open(CAMINHO_LISTA_ESPERA, "r", newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)

        registros = []

        for linha in leitor:
            registro = {campo: linha.get(campo, "") for campo in CAMPOS_LISTA_ESPERA}
            registros.append(registro)

        return registros


def salvar_lista_espera(registros: List[Dict[str, Any]]) -> None:
    with open(CAMINHO_LISTA_ESPERA, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_LISTA_ESPERA)
        escritor.writeheader()

        for registro in registros:
            linha = {campo: registro.get(campo, "") for campo in CAMPOS_LISTA_ESPERA}
            escritor.writerow(linha)


def adicionar_interessado(
    nome: str,
    contato: str,
    perfil: str,
    principal_dor: str,
    plano_interesse: str,
    preco_aceitavel: str,
    pagaria_agora: str,
    comentario: str,
) -> None:
    registros = carregar_lista_espera()

    novo_registro = {
        "id": str(uuid.uuid4())[:8],
        "data_criacao": datetime.now().isoformat(timespec="minutes"),
        "nome": nome.strip(),
        "contato": contato.strip(),
        "perfil": perfil,
        "principal_dor": principal_dor,
        "plano_interesse": plano_interesse,
        "preco_aceitavel": preco_aceitavel,
        "pagaria_agora": pagaria_agora,
        "comentario": comentario.strip(),
    }

    registros.append(novo_registro)
    salvar_lista_espera(registros)


def limpar_lista_espera() -> None:
    salvar_lista_espera([])


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


def _gerar_resumo(registros: List[Dict[str, str]]) -> Dict[str, Any]:
    total = len(registros)

    return {
        "total": total,
        "pagaria_sim": _contar(registros, "pagaria_agora", "Sim, se o preço fosse justo"),
        "pagaria_talvez": _contar(registros, "pagaria_agora", "Talvez, preciso testar mais"),
        "pagaria_nao": _contar(registros, "pagaria_agora", "Não pagaria agora"),
        "perfil_mais_comum": _mais_frequente(registros, "perfil"),
        "dor_mais_comum": _mais_frequente(registros, "principal_dor"),
        "plano_mais_citado": _mais_frequente(registros, "plano_interesse"),
        "preco_mais_citado": _mais_frequente(registros, "preco_aceitavel"),
    }


def _preparar_tabela(registros: List[Dict[str, str]]) -> List[Dict[str, str]]:
    tabela = []

    for registro in reversed(registros):
        tabela.append(
            {
                "Data": registro.get("data_criacao", ""),
                "Nome": registro.get("nome", ""),
                "Contato": registro.get("contato", ""),
                "Perfil": registro.get("perfil", ""),
                "Dor principal": registro.get("principal_dor", ""),
                "Plano": registro.get("plano_interesse", ""),
                "Preço": registro.get("preco_aceitavel", ""),
                "Pagaria agora": registro.get("pagaria_agora", ""),
                "Comentário": registro.get("comentario", ""),
            }
        )

    return tabela


def _injetar_css_oferta() -> None:
    st.markdown(
        """
        <style>
            .oferta-hero {
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

            .oferta-eyebrow {
                color: #d6b56d;
                font-size: 0.78rem;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.35rem;
            }

            .oferta-title {
                color: #f4f7fb;
                font-size: 2.08rem;
                font-weight: 900;
                margin-bottom: 0.45rem;
                line-height: 1.14;
            }

            .oferta-subtitle {
                color: rgba(244, 247, 251, 0.76);
                font-size: 1rem;
                line-height: 1.62;
                max-width: 1080px;
            }

            .oferta-card {
                padding: 1.1rem 1.15rem;
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.035);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.18);
                height: 100%;
            }

            .oferta-card-label {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .oferta-card-value {
                color: #f4f7fb;
                font-size: 1.25rem;
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .oferta-card-note {
                color: rgba(244, 247, 251, 0.68);
                font-size: 0.87rem;
                line-height: 1.47;
            }

            .oferta-box {
                padding: 1.05rem 1.1rem;
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.028);
                margin-bottom: 1rem;
                height: 100%;
            }

            .oferta-badge {
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

            .oferta-box-title {
                color: #f4f7fb;
                font-size: 1.1rem;
                font-weight: 850;
                margin-bottom: 0.35rem;
            }

            .oferta-box-text {
                color: rgba(244, 247, 251, 0.70);
                font-size: 0.90rem;
                line-height: 1.52;
            }

            .oferta-highlight {
                padding: 0.95rem 1rem;
                border-radius: 16px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.92rem;
                line-height: 1.55;
                margin-bottom: 0.7rem;
            }

            .oferta-disclaimer {
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
        <div class="oferta-card">
            <div class="oferta-card-label">{label}</div>
            <div class="oferta-card-value">{value}</div>
            <div class="oferta-card-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _plano(badge: str, titulo: str, texto: str) -> None:
    st.markdown(
        f"""
        <div class="oferta-box">
            <div class="oferta-badge">{badge}</div>
            <div class="oferta-box-title">{titulo}</div>
            <div class="oferta-box-text">{texto}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def renderizar_oferta_beta() -> None:
    """
    Renderiza a página de Oferta Beta e Lista de Espera.
    """
    _injetar_css_oferta()

    registros = carregar_lista_espera()
    resumo = _gerar_resumo(registros)

    st.session_state["resultado_oferta_beta"] = resumo

    st.markdown(
        """
        <div class="oferta-hero">
            <div class="oferta-eyebrow">Primeira oferta controlada</div>
            <div class="oferta-title">Entre na lista de espera da Máquina de Preço-Teto.</div>
            <div class="oferta-subtitle">
                Uma plataforma educacional para analisar ativos com método: valuation, preço-teto,
                margem de segurança, tese, checklist, relatórios e watchlist. Esta página mede interesse real
                antes da primeira oferta paga.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="oferta-highlight">
            Esta ainda não é uma venda automática. É uma validação de demanda. O objetivo é entender
            quem realmente teria interesse em usar e pagar por uma versão mais completa do produto.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Resumo da lista de espera")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Interessados", resumo["total"])

    with col_2:
        st.metric("Pagaria agora", resumo["pagaria_sim"])

    with col_3:
        st.metric("Talvez pagaria", resumo["pagaria_talvez"])

    with col_4:
        st.metric("Não pagaria", resumo["pagaria_nao"])

    col_5, col_6, col_7, col_8 = st.columns(4)

    with col_5:
        _card("Perfil dominante", resumo["perfil_mais_comum"], "Público que mais entrou na lista.")

    with col_6:
        _card("Dor dominante", resumo["dor_mais_comum"], "Dor que mais aparece na intenção de compra.")

    with col_7:
        _card("Plano mais citado", resumo["plano_mais_citado"], "Plano com maior interesse inicial.")

    with col_8:
        _card("Preço mais citado", resumo["preco_mais_citado"], "Faixa de preço mais aceita.")

    st.divider()

    st.markdown("### Oferta beta proposta")

    col_p1, col_p2, col_p3 = st.columns(3)

    with col_p1:
        _plano(
            "Gratuito",
            "Plano Free",
            """
            Para testar a plataforma e entender a jornada.
            Inclui modo demonstração, valuation básico, início guiado e visão educacional.
            Ideal para entrada de novos usuários.
            """,
        )

    with col_p2:
        _plano(
            "Mais provável",
            "Plano Premium",
            """
            Para usuários que querem analisar com mais organização.
            Inclui valuation, tese, checklist, relatórios, watchlist e módulos multiativos.
            Possível faixa inicial: R$ 19,90 a R$ 29,90/mês.
            """,
        )

    with col_p3:
        _plano(
            "Futuro",
            "Plano Pro",
            """
            Para usuários avançados, criadores ou analistas.
            Futuramente pode incluir dados automáticos, banco de dados, histórico avançado,
            alertas, exportação em PDF e dashboards profissionais.
            """,
        )

    st.divider()

    st.markdown("### Entrar na lista de espera")

    with st.form("form_lista_espera_beta"):
        col_a, col_b = st.columns(2)

        with col_a:
            nome = st.text_input(
                "Nome",
                value="",
                placeholder="Seu nome ou identificação",
                key="oferta_nome",
            )

            contato = st.text_input(
                "E-mail ou WhatsApp",
                value="",
                placeholder="Como você quer ser chamado quando o beta abrir?",
                key="oferta_contato",
            )

            perfil = st.selectbox(
                "Perfil",
                PERFIS,
                key="oferta_perfil",
            )

            principal_dor = st.selectbox(
                "Principal dor",
                DORES,
                key="oferta_principal_dor",
            )

        with col_b:
            plano_interesse = st.selectbox(
                "Plano que mais chamaria sua atenção",
                PLANOS_INTERESSE,
                key="oferta_plano_interesse",
            )

            preco_aceitavel = st.selectbox(
                "Preço aceitável",
                PRECOS_ACEITAVEIS,
                key="oferta_preco_aceitavel",
            )

            pagaria_agora = st.selectbox(
                "Você pagaria por uma versão melhorada?",
                OPCOES_PAGARIA_AGORA,
                key="oferta_pagaria_agora",
            )

            comentario = st.text_area(
                "Comentário opcional",
                value="",
                height=118,
                placeholder="O que faria você pagar? O que ainda falta? Qual módulo mais chamou atenção?",
                key="oferta_comentario",
            )

        enviar = st.form_submit_button("Entrar na lista de espera")

        if enviar:
            if nome.strip() == "":
                st.error("Preencha seu nome ou uma identificação.")
            elif contato.strip() == "":
                st.error("Preencha um e-mail ou WhatsApp para contato.")
            else:
                adicionar_interessado(
                    nome=nome,
                    contato=contato,
                    perfil=perfil,
                    principal_dor=principal_dor,
                    plano_interesse=plano_interesse,
                    preco_aceitavel=preco_aceitavel,
                    pagaria_agora=pagaria_agora,
                    comentario=comentario,
                )

                st.success("Cadastro salvo na lista de espera com sucesso.")
                st.rerun()

    st.divider()

    st.markdown("### Lista de interessados")

    registros = carregar_lista_espera()

    if len(registros) == 0:
        st.info("Nenhum interessado registrado ainda.")
    else:
        tabela = _preparar_tabela(registros)

        st.dataframe(
            tabela,
            use_container_width=True,
            hide_index=True,
        )

        st.divider()

        col_down, col_clean = st.columns(2)

        with col_down:
            with open(CAMINHO_LISTA_ESPERA, "rb") as arquivo:
                st.download_button(
                    label="Baixar lista de espera em CSV",
                    data=arquivo,
                    file_name="lista_espera_beta.csv",
                    mime="text/csv",
                    key="oferta_download_csv",
                )

        with col_clean:
            confirmar = st.checkbox(
                "Confirmar limpeza da lista de espera",
                value=False,
                key="oferta_confirmar_limpeza",
            )

            if st.button("Limpar lista de espera", key="oferta_limpar_lista"):
                if confirmar:
                    limpar_lista_espera()
                    st.success("Lista de espera limpa com sucesso.")
                    st.rerun()
                else:
                    st.warning("Marque a confirmação antes de limpar a lista.")

    st.divider()

    st.markdown("### Como interpretar a lista de espera")

    st.markdown(
        """
        - Se poucas pessoas entram na lista, a proposta ainda não está clara ou o público ainda não foi bem escolhido.
        - Se muitas pessoas escolhem “talvez pagaria”, precisamos melhorar a demonstração de valor.
        - Se o plano Premium for o mais citado, podemos testar uma primeira oferta simples.
        - Se a dor dominante for “medo de pagar caro”, o marketing deve focar em preço-teto e margem de segurança.
        - Se a dor dominante for “organizar análises”, o marketing deve focar em relatório, watchlist e método.
        """
    )

    st.markdown(
        """
        <div class="oferta-disclaimer">
            <strong>Nota estratégica:</strong> esta página não processa pagamentos e não representa oferta definitiva.
            Ela serve para validar demanda, intenção de compra e percepção de valor antes de construir a estrutura comercial completa.
        </div>
        """,
        unsafe_allow_html=True,
    )