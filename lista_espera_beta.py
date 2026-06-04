# lista_espera_beta.py

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4
import csv

import streamlit as st


# ============================================================
# VALORIS
# v3.8.39 — Lista de Espera e Captura de Leads
# ------------------------------------------------------------
# Este módulo cria uma captura simples de leads para o beta.
#
# Objetivo:
# - transformar usuários interessados em base de relacionamento
# - validar disposição de pagamento
# - entender dores reais dos investidores
# - preparar monetização beta/fundador
#
# Observação:
# - Armazena dados em CSV local.
# - O arquivo deve estar no .gitignore.
# - Em produção madura, migrar para banco, Google Sheets,
#   Supabase, Airtable ou CRM.
# ============================================================


VERSAO_LISTA_ESPERA_BETA = "3.8.39"

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


PERFIS_INVESTIDOR = [
    "Iniciante — ainda estou aprendendo",
    "Intermediário — já invisto e quero decidir melhor",
    "Avançado — já uso planilhas/ferramentas",
    "Profissional/estudante de mercado financeiro",
    "Outro",
]


PLANOS_INTERESSE = [
    "Quero testar gratuitamente",
    "Beta Fundador barato",
    "Plano mensal",
    "Plano anual com desconto",
    "Relatório premium avulso",
    "Ainda não sei",
]


PRECOS_ACEITAVEIS = [
    "Não pagaria agora",
    "Até R$ 9,90/mês",
    "Até R$ 19,90/mês",
    "Até R$ 29,90/mês",
    "Até R$ 49,90/mês",
    "Mais de R$ 49,90/mês se entregar muito valor",
    "Preferiria pagar uma vez só",
]


PAGARIA_AGORA = [
    "Sim, se o produto já estivesse disponível",
    "Talvez, preciso ver mais valor",
    "Não agora, mas quero acompanhar",
    "Não pagaria",
]


def _garantir_arquivo_lista_espera() -> None:
    if CAMINHO_LISTA_ESPERA.exists():
        return

    with CAMINHO_LISTA_ESPERA.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_LISTA_ESPERA)
        escritor.writeheader()


def _limpar_texto(valor: Any) -> str:
    if valor is None:
        return ""

    return str(valor).strip()


def _contato_parece_valido(contato: str) -> bool:
    contato_limpo = _limpar_texto(contato)

    if len(contato_limpo) < 5:
        return False

    if "@" in contato_limpo and "." in contato_limpo:
        return True

    digitos = "".join(caractere for caractere in contato_limpo if caractere.isdigit())

    return len(digitos) >= 8


def _lead_ja_existe(contato: str) -> bool:
    _garantir_arquivo_lista_espera()

    contato_normalizado = _limpar_texto(contato).lower()

    if not contato_normalizado:
        return False

    try:
        with CAMINHO_LISTA_ESPERA.open("r", newline="", encoding="utf-8") as arquivo:
            leitor = csv.DictReader(arquivo)

            for linha in leitor:
                if _limpar_texto(linha.get("contato", "")).lower() == contato_normalizado:
                    return True

    except FileNotFoundError:
        return False

    return False


def salvar_lead_lista_espera(dados: Dict[str, Any]) -> Dict[str, Any]:
    _garantir_arquivo_lista_espera()

    nome = _limpar_texto(dados.get("nome"))
    contato = _limpar_texto(dados.get("contato"))

    if len(nome) < 2:
        return {
            "ok": False,
            "mensagem": "Informe seu nome para entrar na lista.",
        }

    if not _contato_parece_valido(contato):
        return {
            "ok": False,
            "mensagem": "Informe um e-mail ou WhatsApp válido.",
        }

    if _lead_ja_existe(contato):
        return {
            "ok": False,
            "mensagem": "Esse contato já está na lista de espera da Valoris.",
        }

    registro = {
        "id": str(uuid4()),
        "data_criacao": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "nome": nome,
        "contato": contato,
        "perfil": _limpar_texto(dados.get("perfil")),
        "principal_dor": _limpar_texto(dados.get("principal_dor")),
        "plano_interesse": _limpar_texto(dados.get("plano_interesse")),
        "preco_aceitavel": _limpar_texto(dados.get("preco_aceitavel")),
        "pagaria_agora": _limpar_texto(dados.get("pagaria_agora")),
        "comentario": _limpar_texto(dados.get("comentario")),
    }

    with CAMINHO_LISTA_ESPERA.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_LISTA_ESPERA)
        escritor.writerow(registro)

    return {
        "ok": True,
        "mensagem": "Entrada registrada com sucesso.",
        "registro": registro,
    }


def carregar_leads_lista_espera() -> List[Dict[str, str]]:
    _garantir_arquivo_lista_espera()

    with CAMINHO_LISTA_ESPERA.open("r", newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        return list(leitor)


def gerar_csv_lista_espera() -> str:
    _garantir_arquivo_lista_espera()

    return CAMINHO_LISTA_ESPERA.read_text(encoding="utf-8")


def _calcular_metricas_lista_espera(leads: List[Dict[str, str]]) -> Dict[str, Any]:
    total = len(leads)

    pagariam = [
        lead for lead in leads
        if "sim" in _limpar_texto(lead.get("pagaria_agora", "")).lower()
    ]

    talvez = [
        lead for lead in leads
        if "talvez" in _limpar_texto(lead.get("pagaria_agora", "")).lower()
    ]

    planos: Dict[str, int] = {}

    for lead in leads:
        plano = _limpar_texto(lead.get("plano_interesse", "Não informado"))

        if not plano:
            plano = "Não informado"

        planos[plano] = planos.get(plano, 0) + 1

    plano_mais_citado = "N/D"

    if planos:
        plano_mais_citado = sorted(planos.items(), key=lambda item: item[1], reverse=True)[0][0]

    return {
        "total": total,
        "pagariam": len(pagariam),
        "talvez": len(talvez),
        "plano_mais_citado": plano_mais_citado,
    }


def _renderizar_css_lista_espera() -> None:
    st.markdown(
        """
        <style>
            .lead-box {
                padding: 1.15rem 1.18rem;
                border-radius: 24px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    radial-gradient(circle at top left, rgba(214, 181, 109, 0.16), transparent 28%),
                    radial-gradient(circle at bottom right, rgba(36, 128, 91, 0.18), transparent 34%),
                    linear-gradient(135deg, rgba(15, 23, 42, 0.94), rgba(2, 6, 23, 0.94));
                box-shadow: 0 16px 45px rgba(0, 0, 0, 0.24);
                margin-top: 1rem;
                margin-bottom: 1rem;
            }

            .lead-eyebrow {
                color: #d6b56d;
                font-size: 0.74rem;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.28rem;
            }

            .lead-title {
                color: #f4f7fb;
                font-size: clamp(1.25rem, 3.2vw, 1.75rem);
                font-weight: 900;
                letter-spacing: -0.035em;
                margin-bottom: 0.35rem;
                line-height: 1.12;
            }

            .lead-text {
                color: rgba(244, 247, 251, 0.72);
                font-size: 0.93rem;
                line-height: 1.52;
                max-width: 960px;
            }

            .lead-note {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.82rem;
                line-height: 1.45;
                margin-top: 0.75rem;
            }

            @media (max-width: 520px) {
                .lead-box {
                    padding: 1rem;
                    border-radius: 18px;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def renderizar_lista_espera_valoris(modo_admin: bool = False) -> None:
    """
    Renderiza a captura pública de leads da Valoris.
    """
    _renderizar_css_lista_espera()

    st.markdown(
        """
        <div class="lead-box">
            <div class="lead-eyebrow">Beta fundador</div>
            <div class="lead-title">Entre na lista beta da Valoris</div>
            <div class="lead-text">
                Estamos construindo uma plataforma para ajudar investidores a auditar decisões antes de comprar ações.
                Se você quer testar novas versões, receber melhorias e participar do grupo fundador, deixe seu contato.
            </div>
            <div class="lead-note">
                Seus dados serão usados apenas para contato sobre o beta, melhorias do produto e convites futuros da Valoris.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("form_lista_espera_valoris", clear_on_submit=True):
        col_nome, col_contato = st.columns(2)

        with col_nome:
            nome = st.text_input(
                "Nome",
                placeholder="Seu nome",
                key="lista_espera_nome",
            )

        with col_contato:
            contato = st.text_input(
                "E-mail ou WhatsApp",
                placeholder="exemplo@email.com ou WhatsApp",
                key="lista_espera_contato",
            )

        perfil = st.selectbox(
            "Qual é seu perfil como investidor?",
            PERFIS_INVESTIDOR,
            key="lista_espera_perfil",
        )

        principal_dor = st.text_area(
            "Qual sua maior dificuldade ao analisar ações hoje?",
            placeholder="Ex: não sei se estou pagando caro, não entendo balanços, não confio nas premissas...",
            height=90,
            key="lista_espera_principal_dor",
        )

        col_plano, col_preco = st.columns(2)

        with col_plano:
            plano_interesse = st.selectbox(
                "Qual formato faria mais sentido para você?",
                PLANOS_INTERESSE,
                key="lista_espera_plano",
            )

        with col_preco:
            preco_aceitavel = st.selectbox(
                "Quanto você aceitaria pagar se a ferramenta entregasse valor real?",
                PRECOS_ACEITAVEIS,
                key="lista_espera_preco",
            )

        pagaria_agora = st.radio(
            "Você pagaria por uma ferramenta assim hoje?",
            PAGARIA_AGORA,
            horizontal=False,
            key="lista_espera_pagaria_agora",
        )

        comentario = st.text_area(
            "Comentário opcional",
            placeholder="O que faria você confiar e usar a Valoris com frequência?",
            height=80,
            key="lista_espera_comentario",
        )

        enviado = st.form_submit_button("Entrar na lista beta")

        if enviado:
            resultado = salvar_lead_lista_espera(
                {
                    "nome": nome,
                    "contato": contato,
                    "perfil": perfil,
                    "principal_dor": principal_dor,
                    "plano_interesse": plano_interesse,
                    "preco_aceitavel": preco_aceitavel,
                    "pagaria_agora": pagaria_agora,
                    "comentario": comentario,
                }
            )

            if resultado["ok"]:
                st.success(
                    "Você entrou na lista beta da Valoris. Obrigado por ajudar a construir uma plataforma mais útil."
                )
            else:
                st.warning(resultado["mensagem"])

    if modo_admin:
        st.divider()
        renderizar_painel_lista_espera_valoris()


def renderizar_painel_lista_espera_valoris() -> None:
    leads = carregar_leads_lista_espera()
    metricas = _calcular_metricas_lista_espera(leads)

    st.markdown("### Painel da lista de espera")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Leads", metricas["total"])

    with col_2:
        st.metric("Pagariam agora", metricas["pagariam"])

    with col_3:
        st.metric("Talvez pagariam", metricas["talvez"])

    with col_4:
        st.metric("Plano mais citado", metricas["plano_mais_citado"])

    if len(leads) == 0:
        st.info("Ainda não há leads registrados.")
        return

    with st.expander("Ver últimos leads", expanded=False):
        ultimos = leads[-10:]

        for lead in reversed(ultimos):
            with st.container(border=True):
                st.markdown(f"**{lead.get('nome', 'N/D')}**")
                st.caption(f"{lead.get('contato', 'N/D')} • {lead.get('data_criacao', 'N/D')}")
                st.markdown(f"**Perfil:** {lead.get('perfil', 'N/D')}")
                st.markdown(f"**Dor:** {lead.get('principal_dor', 'N/D')}")
                st.markdown(f"**Plano:** {lead.get('plano_interesse', 'N/D')}")
                st.markdown(f"**Preço:** {lead.get('preco_aceitavel', 'N/D')}")
                st.markdown(f"**Pagaria agora:** {lead.get('pagaria_agora', 'N/D')}")

    st.download_button(
        label="Baixar lista de espera (.csv)",
        data=gerar_csv_lista_espera(),
        file_name="lista_espera_beta.csv",
        mime="text/csv",
        key="download_lista_espera_beta",
    )


def executar_autoteste_lista_espera_beta() -> List[Dict[str, str]]:
    campos_ok = CAMPOS_LISTA_ESPERA == [
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

    return [
        {
            "teste": "campos_lista_espera",
            "status": "OK" if campos_ok else "FALHA",
            "detalhe": ", ".join(CAMPOS_LISTA_ESPERA),
        },
        {
            "teste": "validacao_contato_email",
            "status": "OK" if _contato_parece_valido("teste@email.com") else "FALHA",
            "detalhe": "teste@email.com",
        },
        {
            "teste": "validacao_contato_whatsapp",
            "status": "OK" if _contato_parece_valido("(11) 99999-9999") else "FALHA",
            "detalhe": "(11) 99999-9999",
        },
    ]
