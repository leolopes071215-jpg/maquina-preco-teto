# maturidade_produto_valoris.py

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

import streamlit as st

from analytics_publico_valoris import calcular_metricas_funil_publico
from central_fundadores_valoris import carregar_fundadores_valoris
from conversao_fundador_valoris import carregar_sinais_conversao
from hub_ativacao_valoris import carregar_ativacoes_valoris
from laboratorio_growth_valoris import carregar_experimentos_growth
from lista_espera_beta import carregar_leads_lista_espera
from validacao_manual_valoris import carregar_validacoes_manuais


# ============================================================
# VALORIS
# v3.8.54 — Motor de Maturidade do Produto
# ------------------------------------------------------------
# Este módulo consolida os sinais do MVP e responde:
#
# A Valoris deve:
# - continuar validando?
# - melhorar produto?
# - testar pagamento?
# - criar banco de dados?
# - criar API?
# - iniciar front-end moderno?
#
# Objetivo:
# - impedir salto técnico prematuro;
# - transformar dados internos em decisão de roadmap;
# - dar disciplina de startup ao projeto;
# - preparar a transição correta para banco/API/React.
# ============================================================


VERSAO_MATURIDADE_PRODUTO_VALORIS = "3.8.54"

CAMINHO_DECISOES_MATURIDADE = Path("decisoes_maturidade_valoris.csv")

CAMPOS_DECISAO_MATURIDADE = [
    "id",
    "data_registro",
    "score_produto",
    "score_ativacao",
    "score_conversao",
    "score_operacao",
    "score_tecnico",
    "classificacao",
    "decisao_recomendada",
    "proximo_passo",
    "observacoes",
]


PESOS_MATURIDADE = {
    "produto": 0.28,
    "ativacao": 0.22,
    "conversao": 0.22,
    "operacao": 0.16,
    "tecnico": 0.12,
}


DECISOES_ROADMAP = {
    "validar": {
        "titulo": "Continuar validando manualmente",
        "descricao": (
            "Ainda não há sinal suficiente para avançar para arquitetura mais cara. "
            "Priorize conversas, feedbacks e clareza de proposta."
        ),
    },
    "produto": {
        "titulo": "Melhorar núcleo do produto",
        "descricao": (
            "A proposta existe, mas a entrega principal precisa ficar mais forte: valuation, auditor, relatório e explicabilidade."
        ),
    },
    "pagamento": {
        "titulo": "Testar pagamento manual",
        "descricao": (
            "Já há sinais comerciais. Antes de checkout, valide pagamento manual com poucos fundadores."
        ),
    },
    "banco": {
        "titulo": "Criar banco de dados",
        "descricao": (
            "Há dados suficientes para justificar sair dos CSVs e organizar leads, usuários, análises e relatórios em banco real."
        ),
    },
    "api": {
        "titulo": "Criar API em Python/FastAPI",
        "descricao": (
            "O produto começa a pedir separação entre cérebro e interface. A API deve vir antes do front-end moderno."
        ),
    },
    "frontend": {
        "titulo": "Iniciar front-end moderno",
        "descricao": (
            "Somente faz sentido quando produto, conversão e operação já têm sinais fortes. TypeScript/React vira vitrine premium."
        ),
    },
}


def _limpar_texto(valor: Any) -> str:
    if valor is None:
        return ""

    return str(valor).strip()


def _garantir_arquivo() -> None:
    if CAMINHO_DECISOES_MATURIDADE.exists():
        return

    with CAMINHO_DECISOES_MATURIDADE.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISAO_MATURIDADE)
        escritor.writeheader()


def carregar_decisoes_maturidade() -> List[Dict[str, str]]:
    _garantir_arquivo()

    with CAMINHO_DECISOES_MATURIDADE.open("r", newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        return list(leitor)


def salvar_decisao_maturidade(decisao: Dict[str, Any]) -> Dict[str, str]:
    _garantir_arquivo()

    registro = {
        "id": str(uuid4())[:8],
        "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score_produto": str(decisao.get("score_produto", "")),
        "score_ativacao": str(decisao.get("score_ativacao", "")),
        "score_conversao": str(decisao.get("score_conversao", "")),
        "score_operacao": str(decisao.get("score_operacao", "")),
        "score_tecnico": str(decisao.get("score_tecnico", "")),
        "classificacao": _limpar_texto(decisao.get("classificacao", "")),
        "decisao_recomendada": _limpar_texto(decisao.get("decisao_recomendada", "")),
        "proximo_passo": _limpar_texto(decisao.get("proximo_passo", "")),
        "observacoes": _limpar_texto(decisao.get("observacoes", "")),
    }

    with CAMINHO_DECISOES_MATURIDADE.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISAO_MATURIDADE)
        escritor.writerow(registro)

    return registro


def gerar_csv_decisoes_maturidade() -> str:
    _garantir_arquivo()

    return CAMINHO_DECISOES_MATURIDADE.read_text(encoding="utf-8")


def _safe_len(funcao) -> int:
    try:
        return len(funcao())
    except Exception:
        return 0


def _safe_funil() -> Dict[str, Any]:
    try:
        return calcular_metricas_funil_publico()
    except Exception:
        return {}


def _coletar_sinais() -> Dict[str, Any]:
    funil = _safe_funil()

    leads = _safe_len(carregar_leads_lista_espera)
    ativacoes = _safe_len(carregar_ativacoes_valoris)
    conversoes = _safe_len(carregar_sinais_conversao)
    validacoes = _safe_len(carregar_validacoes_manuais)
    fundadores = _safe_len(carregar_fundadores_valoris)
    experimentos = _safe_len(carregar_experimentos_growth)

    try:
        sinais_conversao = carregar_sinais_conversao()
    except Exception:
        sinais_conversao = []

    try:
        validacoes_lista = carregar_validacoes_manuais()
    except Exception:
        validacoes_lista = []

    try:
        fundadores_lista = carregar_fundadores_valoris()
    except Exception:
        fundadores_lista = []

    alta_intencao = len(
        [
            item for item in sinais_conversao
            if "Alta" in item.get("intencao", "")
        ]
    )

    compraria = len(
        [
            item for item in validacoes_lista
            if item.get("status") == "Compraria" or item.get("intencao") == "Alta intenção"
        ]
    )

    pagos = len(
        [
            item for item in fundadores_lista
            if item.get("status_pagamento") == "Pago manualmente"
        ]
    )

    relatorios_feedback = len(
        [
            item for item in fundadores_lista
            if item.get("etapa_onboarding") in ["Baixou relatório", "Enviou feedback", "Virou caso de sucesso"]
        ]
    )

    return {
        "funil": funil,
        "leads": leads,
        "ativacoes": ativacoes,
        "conversoes": conversoes,
        "validacoes": validacoes,
        "fundadores": fundadores,
        "experimentos": experimentos,
        "alta_intencao": alta_intencao,
        "compraria": compraria,
        "pagos": pagos,
        "relatorios_feedback": relatorios_feedback,
        "taxa_landing_demo": float(funil.get("taxa_landing_demo", 0) or 0),
        "taxa_landing_lead": float(funil.get("taxa_landing_lead", 0) or 0),
        "taxa_demo_interacao": float(funil.get("taxa_demo_interacao", 0) or 0),
    }


def _clamp(valor: float, minimo: int = 0, maximo: int = 100) -> int:
    return int(round(max(minimo, min(maximo, valor))))


def _calcular_scores(sinais: Dict[str, Any]) -> Dict[str, int]:
    score_produto = 35
    score_produto += min(sinais["relatorios_feedback"] * 18, 30)
    score_produto += min(sinais["experimentos"] * 4, 12)
    score_produto += 10 if sinais["taxa_demo_interacao"] >= 50 else 0
    score_produto += 8 if sinais["taxa_landing_demo"] >= 35 else 0

    score_ativacao = 25
    score_ativacao += min(sinais["ativacoes"] * 8, 30)
    score_ativacao += 18 if sinais["taxa_landing_demo"] >= 40 else 8 if sinais["taxa_landing_demo"] >= 20 else 0
    score_ativacao += 16 if sinais["taxa_demo_interacao"] >= 60 else 7 if sinais["taxa_demo_interacao"] >= 30 else 0

    score_conversao = 20
    score_conversao += min(sinais["leads"] * 5, 25)
    score_conversao += min(sinais["conversoes"] * 5, 20)
    score_conversao += min(sinais["alta_intencao"] * 12, 24)
    score_conversao += min(sinais["compraria"] * 14, 28)
    score_conversao += 10 if sinais["taxa_landing_lead"] >= 8 else 4 if sinais["taxa_landing_lead"] >= 3 else 0

    score_operacao = 20
    score_operacao += min(sinais["validacoes"] * 8, 32)
    score_operacao += min(sinais["fundadores"] * 12, 36)
    score_operacao += min(sinais["pagos"] * 18, 36)

    score_tecnico = 45
    score_tecnico += 10 if sinais["leads"] >= 5 else 0
    score_tecnico += 12 if sinais["fundadores"] >= 3 else 0
    score_tecnico += 15 if sinais["pagos"] >= 2 else 0
    score_tecnico += 12 if sinais["relatorios_feedback"] >= 2 else 0

    return {
        "score_produto": _clamp(score_produto),
        "score_ativacao": _clamp(score_ativacao),
        "score_conversao": _clamp(score_conversao),
        "score_operacao": _clamp(score_operacao),
        "score_tecnico": _clamp(score_tecnico),
    }


def _score_geral(scores: Dict[str, int]) -> int:
    total = (
        scores["score_produto"] * PESOS_MATURIDADE["produto"]
        + scores["score_ativacao"] * PESOS_MATURIDADE["ativacao"]
        + scores["score_conversao"] * PESOS_MATURIDADE["conversao"]
        + scores["score_operacao"] * PESOS_MATURIDADE["operacao"]
        + scores["score_tecnico"] * PESOS_MATURIDADE["tecnico"]
    )

    return _clamp(total)


def _classificar_maturidade(score: int) -> str:
    if score >= 85:
        return "Pronto para plataforma"
    if score >= 72:
        return "Pronto para infraestrutura"
    if score >= 58:
        return "Pronto para pagamento manual forte"
    if score >= 42:
        return "MVP com sinais iniciais"
    return "Ainda em descoberta"


def _decidir_roadmap(sinais: Dict[str, Any], scores: Dict[str, int], score_total: int) -> Dict[str, str]:
    if sinais["leads"] < 5 and sinais["validacoes"] < 3:
        chave = "validar"
    elif scores["score_produto"] < 58:
        chave = "produto"
    elif sinais["alta_intencao"] >= 1 or sinais["compraria"] >= 1:
        chave = "pagamento"
    elif sinais["fundadores"] >= 3 or sinais["leads"] >= 20:
        chave = "banco"
    elif sinais["pagos"] >= 3 and sinais["relatorios_feedback"] >= 2:
        chave = "api"
    elif score_total >= 85 and sinais["pagos"] >= 5:
        chave = "frontend"
    else:
        chave = "produto"

    decisao = DECISOES_ROADMAP[chave]

    return {
        "chave": chave,
        "titulo": decisao["titulo"],
        "descricao": decisao["descricao"],
    }


def _gerar_recomendacoes(sinais: Dict[str, Any], scores: Dict[str, int], decisao: Dict[str, str]) -> List[str]:
    recomendacoes = []

    if decisao["chave"] == "validar":
        recomendacoes.extend(
            [
                "Fale manualmente com pelo menos 5 leads ou potenciais usuários.",
                "Use a aba Validação Manual para registrar objeções, intenção e preço aceito.",
                "Não crie checkout ainda.",
            ]
        )

    if decisao["chave"] == "produto":
        recomendacoes.extend(
            [
                "Fortaleça o núcleo: Valuation → Auditor → Relatório.",
                "Melhore explicabilidade dos cálculos e reduza sensação de caixa-preta.",
                "Garanta que o usuário consiga chegar ao relatório sem fricção.",
            ]
        )

    if decisao["chave"] == "pagamento":
        recomendacoes.extend(
            [
                "Teste pagamento manual com poucos usuários fundadores.",
                "Registre preço, objeção e entrega prometida.",
                "Evite assinatura automática antes de comprovar valor percebido.",
            ]
        )

    if decisao["chave"] == "banco":
        recomendacoes.extend(
            [
                "Comece a preparar migração de CSV para banco.",
                "Modele tabelas: leads, users, valuations, reports, events, founders e payments.",
                "Considere Supabase/PostgreSQL como próxima camada.",
            ]
        )

    if decisao["chave"] == "api":
        recomendacoes.extend(
            [
                "Separe o cérebro da interface com FastAPI.",
                "Crie endpoints para valuation, relatório, leads, eventos e usuários.",
                "Mantenha Python como backend central.",
            ]
        )

    if decisao["chave"] == "frontend":
        recomendacoes.extend(
            [
                "Inicie prova de conceito em TypeScript/Next.js.",
                "Priorize landing, área logada e dashboard premium.",
                "Mantenha Streamlit como laboratório interno até a nova interface amadurecer.",
            ]
        )

    if scores["score_operacao"] < 45:
        recomendacoes.append("A operação ainda está fraca: registre mais validações, fundadores e feedbacks.")

    if scores["score_ativacao"] < 45:
        recomendacoes.append("A ativação ainda está baixa: simplifique o caminho público e destaque o aha moment.")

    return recomendacoes


def calcular_maturidade_produto_valoris() -> Dict[str, Any]:
    sinais = _coletar_sinais()
    scores = _calcular_scores(sinais)
    score_total = _score_geral(scores)
    classificacao = _classificar_maturidade(score_total)
    decisao = _decidir_roadmap(sinais, scores, score_total)
    recomendacoes = _gerar_recomendacoes(sinais, scores, decisao)

    return {
        **sinais,
        **scores,
        "score_total": score_total,
        "classificacao": classificacao,
        "decisao": decisao,
        "recomendacoes": recomendacoes,
    }


def _gerar_markdown_maturidade(resultado: Dict[str, Any]) -> str:
    recomendacoes = "\n".join([f"- {item}" for item in resultado["recomendacoes"]])

    return f"""# Motor de Maturidade do Produto — Valoris

Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Score geral

Score: {resultado["score_total"]}/100  
Classificação: {resultado["classificacao"]}  
Decisão recomendada: {resultado["decisao"]["titulo"]}

## Scores por camada

Produto: {resultado["score_produto"]}/100  
Ativação: {resultado["score_ativacao"]}/100  
Conversão: {resultado["score_conversao"]}/100  
Operação: {resultado["score_operacao"]}/100  
Técnico: {resultado["score_tecnico"]}/100  

## Sinais

Leads: {resultado["leads"]}  
Ativações: {resultado["ativacoes"]}  
Conversões: {resultado["conversoes"]}  
Validações manuais: {resultado["validacoes"]}  
Fundadores: {resultado["fundadores"]}  
Pagos: {resultado["pagos"]}  
Relatórios/feedback: {resultado["relatorios_feedback"]}  
Experimentos: {resultado["experimentos"]}  

## Leitura

{resultado["decisao"]["descricao"]}

## Recomendações

{recomendacoes}

## Regra estratégica

Python continua sendo o cérebro.  
SQL será a memória.  
FastAPI será a ponte.  
TypeScript/Next.js será a vitrine premium — somente quando a maturidade justificar.
"""


def _injetar_css_maturidade() -> None:
    st.markdown(
        """
        <style>
            .mat-hero {
                padding: clamp(1.18rem, 3vw, 2rem);
                border-radius: 30px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    radial-gradient(circle at top left, rgba(214, 181, 109, 0.26), transparent 30%),
                    radial-gradient(circle at bottom right, rgba(74, 144, 226, 0.22), transparent 34%),
                    linear-gradient(135deg, rgba(8, 15, 27, 0.99), rgba(5, 9, 18, 0.99));
                box-shadow: 0 18px 58px rgba(0, 0, 0, 0.31);
                margin-bottom: 1rem;
            }

            .mat-eyebrow {
                color: #d6b56d;
                font-size: 0.74rem;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                font-weight: 880;
                margin-bottom: 0.35rem;
            }

            .mat-title {
                color: #f4f7fb;
                font-size: clamp(1.75rem, 5.4vw, 3.1rem);
                font-weight: 950;
                line-height: 1.02;
                letter-spacing: -0.058em;
                margin-bottom: 0.55rem;
            }

            .mat-subtitle {
                color: rgba(244, 247, 251, 0.75);
                font-size: clamp(0.94rem, 2.2vw, 1.06rem);
                line-height: 1.56;
                max-width: 1020px;
            }

            .mat-note {
                padding: 0.92rem 0.98rem;
                border-radius: 17px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.90rem;
                line-height: 1.55;
                margin: 0.85rem 0;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _renderizar_hero() -> None:
    st.markdown(
        f"""
        <div class="mat-hero">
            <div class="mat-eyebrow">Valoris • Maturidade do Produto • v{VERSAO_MATURIDADE_PRODUTO_VALORIS}</div>
            <div class="mat-title">Decida o próximo salto com base em sinais reais.</div>
            <div class="mat-subtitle">
                Este motor consolida leads, ativações, conversões, validações, fundadores e experimentos
                para dizer se a Valoris deve validar mais, melhorar produto, testar pagamento, criar banco,
                criar API ou iniciar front-end moderno.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _renderizar_score_principal(resultado: Dict[str, Any]) -> None:
    st.markdown("### Diagnóstico principal")

    col_1, col_2, col_3 = st.columns(3)

    with col_1:
        st.metric("Score geral", f"{resultado['score_total']}/100")

    with col_2:
        st.metric("Classificação", resultado["classificacao"])

    with col_3:
        st.metric("Decisão", resultado["decisao"]["titulo"])

    st.progress(resultado["score_total"] / 100)

    st.info(resultado["decisao"]["descricao"])


def _renderizar_scores(resultado: Dict[str, Any]) -> None:
    st.markdown("### Scores por camada")

    col_1, col_2, col_3, col_4, col_5 = st.columns(5)

    with col_1:
        st.metric("Produto", f"{resultado['score_produto']}/100")

    with col_2:
        st.metric("Ativação", f"{resultado['score_ativacao']}/100")

    with col_3:
        st.metric("Conversão", f"{resultado['score_conversao']}/100")

    with col_4:
        st.metric("Operação", f"{resultado['score_operacao']}/100")

    with col_5:
        st.metric("Técnico", f"{resultado['score_tecnico']}/100")


def _renderizar_sinais(resultado: Dict[str, Any]) -> None:
    st.markdown("### Sinais usados no cálculo")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Leads", resultado["leads"])

    with col_2:
        st.metric("Ativações", resultado["ativacoes"])

    with col_3:
        st.metric("Conversões", resultado["conversoes"])

    with col_4:
        st.metric("Validações", resultado["validacoes"])

    col_5, col_6, col_7, col_8 = st.columns(4)

    with col_5:
        st.metric("Fundadores", resultado["fundadores"])

    with col_6:
        st.metric("Pagos", resultado["pagos"])

    with col_7:
        st.metric("Relatório/feedback", resultado["relatorios_feedback"])

    with col_8:
        st.metric("Experimentos", resultado["experimentos"])


def _renderizar_recomendacoes(resultado: Dict[str, Any]) -> None:
    st.markdown("### Recomendações práticas")

    for recomendacao in resultado["recomendacoes"]:
        st.success(recomendacao)


def _renderizar_historico() -> None:
    historico = carregar_decisoes_maturidade()

    st.markdown("### Histórico de decisões")

    if not historico:
        st.info("Ainda não há decisões salvas.")
        return

    for item in reversed(historico[-10:]):
        with st.container(border=True):
            st.markdown(f"**{item.get('classificacao', 'N/D')}** — {item.get('decisao_recomendada', 'N/D')}")
            st.caption(item.get("data_registro", "N/D"))
            st.markdown(f"Score geral aproximado: **{item.get('score_produto', 'N/D')} / {item.get('score_ativacao', 'N/D')} / {item.get('score_conversao', 'N/D')}**")
            st.markdown(f"Próximo passo: {item.get('proximo_passo', 'N/D')}")


def renderizar_maturidade_produto_valoris() -> None:
    _injetar_css_maturidade()
    _renderizar_hero()

    resultado = calcular_maturidade_produto_valoris()

    _renderizar_score_principal(resultado)

    st.divider()

    _renderizar_scores(resultado)

    st.divider()

    _renderizar_sinais(resultado)

    st.divider()

    _renderizar_recomendacoes(resultado)

    st.divider()

    col_1, col_2 = st.columns(2)

    with col_1:
        if st.button("Salvar decisão de maturidade", key="salvar_decisao_maturidade_valoris"):
            registro = salvar_decisao_maturidade(
                {
                    "score_produto": resultado["score_produto"],
                    "score_ativacao": resultado["score_ativacao"],
                    "score_conversao": resultado["score_conversao"],
                    "score_operacao": resultado["score_operacao"],
                    "score_tecnico": resultado["score_tecnico"],
                    "classificacao": resultado["classificacao"],
                    "decisao_recomendada": resultado["decisao"]["titulo"],
                    "proximo_passo": resultado["recomendacoes"][0] if resultado["recomendacoes"] else "",
                    "observacoes": resultado["decisao"]["descricao"],
                }
            )

            st.success(f"Decisão salva: {registro['classificacao']} • {registro['decisao_recomendada']}")
            st.rerun()

    with col_2:
        st.download_button(
            "Baixar diagnóstico de maturidade (.md)",
            data=_gerar_markdown_maturidade(resultado),
            file_name="maturidade_produto_valoris.md",
            mime="text/markdown",
            key="download_maturidade_produto_valoris",
        )

    st.download_button(
        "Baixar histórico de maturidade (.csv)",
        data=gerar_csv_decisoes_maturidade(),
        file_name="decisoes_maturidade_valoris.csv",
        mime="text/csv",
        key="download_decisoes_maturidade_valoris",
    )

    st.divider()

    _renderizar_historico()

    st.markdown(
        """
        <div class="mat-note">
            <strong>Regra da maturidade:</strong> não migrar para outra linguagem por estética.
            Migrar só quando os sinais mostrarem que o produto merece uma arquitetura mais sofisticada.
        </div>
        """,
        unsafe_allow_html=True,
    )


def executar_autoteste_maturidade_produto_valoris() -> List[Dict[str, str]]:
    sinais = {
        "funil": {},
        "leads": 10,
        "ativacoes": 4,
        "conversoes": 3,
        "validacoes": 4,
        "fundadores": 2,
        "experimentos": 3,
        "alta_intencao": 1,
        "compraria": 1,
        "pagos": 1,
        "relatorios_feedback": 1,
        "taxa_landing_demo": 35,
        "taxa_landing_lead": 6,
        "taxa_demo_interacao": 45,
    }

    scores = _calcular_scores(sinais)
    score = _score_geral(scores)
    classificacao = _classificar_maturidade(score)

    return [
        {
            "teste": "versao_maturidade",
            "status": "OK" if VERSAO_MATURIDADE_PRODUTO_VALORIS == "3.8.54" else "FALHA",
            "detalhe": VERSAO_MATURIDADE_PRODUTO_VALORIS,
        },
        {
            "teste": "score_geral",
            "status": "OK" if 0 <= score <= 100 else "FALHA",
            "detalhe": str(score),
        },
        {
            "teste": "classificacao",
            "status": "OK" if classificacao != "" else "FALHA",
            "detalhe": classificacao,
        },
    ]
