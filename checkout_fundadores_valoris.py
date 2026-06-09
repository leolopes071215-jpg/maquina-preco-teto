# checkout_fundadores_valoris.py

from __future__ import annotations

import csv
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

import streamlit as st

from oferta_beta_fundador_valoris import (
    PLANOS_BETA_FUNDADOR,
    calcular_saude_oferta_beta_fundador,
    carregar_interesses_oferta_beta,
)
from beta_publico_valoris import calcular_saude_beta_publico
from onboarding_premium_valoris import calcular_saude_onboarding_premium
from beta_insights_valoris import calcular_saude_beta_insights
from beta_feedback_valoris import calcular_saude_beta_feedback
from launch_readiness_valoris import calcular_saude_launch_readiness


VERSAO_CHECKOUT_FUNDADORES_VALORIS = "3.8.83"

CAMINHO_FUNDADORES_VALORIS = Path("fundadores_beta_valoris.csv")
CAMINHO_DECISOES_CHECKOUT_FUNDADORES = Path("decisoes_checkout_fundadores_valoris.csv")
CAMINHO_MANIFESTO_CHECKOUT_FUNDADORES = Path("manifesto_checkout_fundadores_valoris.json")
CAMINHO_ROTEIRO_CHECKOUT_MD = Path("ROTEIRO_CHECKOUT_MANUAL_FUNDADORES_VALORIS.md")
CAMINHO_CHECKLIST_CHECKOUT_MD = Path("CHECKLIST_CHECKOUT_FUNDADORES_VALORIS.md")
CAMINHO_CONTRATO_BETA_MD = Path("TERMO_BETA_FUNDADOR_VALORIS.md")
CAMINHO_PIPELINE_FUNDADORES_JSON = Path("pipeline_fundadores_valoris.json")

CAMPOS_FUNDADORES = [
    "id",
    "data_registro",
    "nome",
    "email",
    "perfil",
    "plano",
    "valor_mensal",
    "valor_anual",
    "status",
    "metodo_pagamento",
    "data_inicio",
    "data_proximo_contato",
    "origem",
    "observacoes",
]

CAMPOS_DECISAO_CHECKOUT = [
    "id",
    "data_registro",
    "score_checkout",
    "score_pipeline",
    "score_receita",
    "score_operacional",
    "score_risco",
    "fundadores_total",
    "fundadores_ativos",
    "mrr_estimado",
    "arr_estimado",
    "risco",
    "decisao",
    "proximo_passo",
    "observacoes",
]

STATUS_FUNDADOR = [
    "lead_interessado",
    "convite_enviado",
    "negociacao",
    "pagamento_pendente",
    "ativo",
    "pausado",
    "cancelado",
    "perdido",
]

METODOS_PAGAMENTO_MANUAL = [
    "Pix manual",
    "Link de pagamento externo",
    "Transferência",
    "Aguardando método",
    "Não aplicável",
]

PIPELINE_CHECKOUT_FUNDADORES = [
    {
        "etapa": "Lead interessado",
        "objetivo": "Identificar quem demonstrou intenção de pagar.",
        "acao": "Registrar lead com plano, preço aceito e objeção principal.",
        "criterio_saida": "Lead respondeu se quer avançar para convite fundador.",
    },
    {
        "etapa": "Convite fundador",
        "objetivo": "Explicar acesso, preço, limites e caráter beta.",
        "acao": "Enviar mensagem curta com plano, valor e aviso educacional.",
        "criterio_saida": "Lead aceita receber instruções de pagamento.",
    },
    {
        "etapa": "Pagamento manual",
        "objetivo": "Validar disposição real de pagamento sem integrar gateway ainda.",
        "acao": "Usar Pix/link externo e registrar status manualmente.",
        "criterio_saida": "Pagamento confirmado ou lead perdido.",
    },
    {
        "etapa": "Ativação",
        "objetivo": "Transformar pagante em usuário ativo.",
        "acao": "Enviar acesso, roteiro de uso e pedir primeira análise.",
        "criterio_saida": "Fundador gerou análise ou deixou feedback.",
    },
    {
        "etapa": "Retenção beta",
        "objetivo": "Entender valor real percebido.",
        "acao": "Acompanhar uso, objeções e intenção de renovação.",
        "criterio_saida": "Fundador continua, pausa ou cancela com motivo registrado.",
    },
]

CHECKLIST_CHECKOUT = [
    "Preço e entrega explicados antes do pagamento",
    "Aviso educacional visível",
    "Sem promessa de rentabilidade",
    "Status manual do fundador registrado",
    "Valor mensal/anual registrado",
    "Método de pagamento registrado",
    "Data de próximo contato definida",
    "Termo beta simples disponível",
    "Pipeline com critérios de avanço",
    "MRR/ARR estimado acompanhados",
]

TERMO_BETA_FUNDADOR = {
    "titulo": "Termo simples de participação beta fundador",
    "itens": [
        "A Valoris é uma ferramenta educacional de análise fundamentalista e valuation.",
        "A Valoris não oferece recomendação personalizada de investimento.",
        "Os cálculos dependem das premissas inseridas pelo usuário.",
        "Durante o beta, funcionalidades podem mudar, ser pausadas ou ajustadas.",
        "O pagamento fundador valida acesso antecipado, participação no desenvolvimento e uso da versão beta.",
        "Não há promessa de lucro, rentabilidade ou acerto de mercado.",
        "Feedbacks podem ser usados para melhorar o produto, sem exposição pública de dados pessoais.",
    ],
}


def _limpar_texto(valor: Any) -> str:
    if valor is None:
        return ""
    return str(valor).strip()


def _email_valido(email: str) -> bool:
    email = _limpar_texto(email).lower()
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))


def _to_float(valor: Any, padrao: float = 0.0) -> float:
    try:
        if isinstance(valor, str):
            valor = valor.replace("R$", "").replace(".", "").replace(",", ".").strip()
        return float(valor)
    except Exception:
        return padrao


def _garantir_csv(caminho: Path, campos: List[str]) -> None:
    if caminho.exists():
        return
    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()


def carregar_fundadores_valoris() -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_FUNDADORES_VALORIS, CAMPOS_FUNDADORES)
    with CAMINHO_FUNDADORES_VALORIS.open("r", newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def carregar_decisoes_checkout_fundadores() -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_DECISOES_CHECKOUT_FUNDADORES, CAMPOS_DECISAO_CHECKOUT)
    with CAMINHO_DECISOES_CHECKOUT_FUNDADORES.open("r", newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def gerar_csv_fundadores_valoris() -> str:
    _garantir_csv(CAMINHO_FUNDADORES_VALORIS, CAMPOS_FUNDADORES)
    return CAMINHO_FUNDADORES_VALORIS.read_text(encoding="utf-8")


def gerar_csv_decisoes_checkout_fundadores() -> str:
    _garantir_csv(CAMINHO_DECISOES_CHECKOUT_FUNDADORES, CAMPOS_DECISAO_CHECKOUT)
    return CAMINHO_DECISOES_CHECKOUT_FUNDADORES.read_text(encoding="utf-8")


def _plano_por_nome(nome: str) -> Dict[str, Any]:
    for plano in PLANOS_BETA_FUNDADOR:
        if plano["plano"] == nome:
            return plano
    return PLANOS_BETA_FUNDADOR[1]


def salvar_fundador_valoris(dados: Dict[str, Any]) -> Dict[str, str]:
    _garantir_csv(CAMINHO_FUNDADORES_VALORIS, CAMPOS_FUNDADORES)

    plano_nome = _limpar_texto(dados.get("plano"))
    plano = _plano_por_nome(plano_nome)

    valor_mensal = _to_float(dados.get("valor_mensal"), plano["preco_mensal"])
    valor_anual = _to_float(dados.get("valor_anual"), plano["preco_anual"])

    registro = {
        "id": str(uuid4())[:8],
        "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "nome": _limpar_texto(dados.get("nome")),
        "email": _limpar_texto(dados.get("email")).lower(),
        "perfil": _limpar_texto(dados.get("perfil")),
        "plano": plano_nome or plano["plano"],
        "valor_mensal": str(valor_mensal),
        "valor_anual": str(valor_anual),
        "status": _limpar_texto(dados.get("status", "lead_interessado")),
        "metodo_pagamento": _limpar_texto(dados.get("metodo_pagamento", "Aguardando método")),
        "data_inicio": _limpar_texto(dados.get("data_inicio", datetime.now().strftime("%Y-%m-%d"))),
        "data_proximo_contato": _limpar_texto(dados.get("data_proximo_contato", "")),
        "origem": _limpar_texto(dados.get("origem", "checkout_manual_fundadores")),
        "observacoes": _limpar_texto(dados.get("observacoes")),
    }

    with CAMINHO_FUNDADORES_VALORIS.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_FUNDADORES)
        escritor.writerow(registro)

    return registro


def gerar_fundador_exemplo() -> Dict[str, str]:
    return salvar_fundador_valoris(
        {
            "nome": "Fundador Exemplo",
            "email": f"fundador.{datetime.now().strftime('%H%M%S')}@exemplo.com",
            "perfil": "Investidor intermediário",
            "plano": "Beta Fundador Pro",
            "valor_mensal": 59,
            "valor_anual": 590,
            "status": "pagamento_pendente",
            "metodo_pagamento": "Pix manual",
            "data_proximo_contato": datetime.now().strftime("%Y-%m-%d"),
            "origem": "terminal_demo",
            "observacoes": "Registro exemplo para validar pipeline fundador.",
        }
    )


def gerar_fundador_ativo_exemplo() -> Dict[str, str]:
    return salvar_fundador_valoris(
        {
            "nome": "Fundador Ativo Exemplo",
            "email": f"fundador.ativo.{datetime.now().strftime('%H%M%S')}@exemplo.com",
            "perfil": "Investidor avançado",
            "plano": "Beta Fundador Pro",
            "valor_mensal": 59,
            "valor_anual": 590,
            "status": "ativo",
            "metodo_pagamento": "Pix manual",
            "data_proximo_contato": datetime.now().strftime("%Y-%m-%d"),
            "origem": "terminal_demo",
            "observacoes": "Registro exemplo de fundador ativo para estimar MRR.",
        }
    )


def calcular_metricas_fundadores() -> Dict[str, Any]:
    fundadores = carregar_fundadores_valoris()
    total = len(fundadores)

    ativos = [item for item in fundadores if item.get("status") == "ativo"]
    pendentes = [item for item in fundadores if item.get("status") == "pagamento_pendente"]
    negociacao = [item for item in fundadores if item.get("status") in {"convite_enviado", "negociacao"}]
    perdidos = [item for item in fundadores if item.get("status") in {"cancelado", "perdido"}]

    mrr_estimado = round(sum(_to_float(item.get("valor_mensal"), 0.0) for item in ativos), 2)
    arr_estimado = round(mrr_estimado * 12, 2)

    pipeline_por_status: Dict[str, int] = {}
    planos: Dict[str, int] = {}

    for item in fundadores:
        status = item.get("status", "não informado")
        plano = item.get("plano", "não informado")
        pipeline_por_status[status] = pipeline_por_status.get(status, 0) + 1
        planos[plano] = planos.get(plano, 0) + 1

    taxa_ativacao = round((len(ativos) / total) * 100, 2) if total else 0
    taxa_perda = round((len(perdidos) / total) * 100, 2) if total else 0

    return {
        "fundadores_total": total,
        "fundadores_ativos": len(ativos),
        "pagamentos_pendentes": len(pendentes),
        "em_negociacao": len(negociacao),
        "perdidos_cancelados": len(perdidos),
        "mrr_estimado": mrr_estimado,
        "arr_estimado": arr_estimado,
        "taxa_ativacao": taxa_ativacao,
        "taxa_perda": taxa_perda,
        "pipeline_por_status": pipeline_por_status,
        "planos": planos,
        "ultimos_fundadores": fundadores[-25:],
    }


def calcular_saude_checkout_fundadores() -> Dict[str, Any]:
    metricas = calcular_metricas_fundadores()

    try:
        oferta = calcular_saude_oferta_beta_fundador()
    except Exception as erro:
        oferta = {"score_oferta": 0, "interesses_total": 0, "erro": str(erro)}

    try:
        beta_publico = calcular_saude_beta_publico()
    except Exception as erro:
        beta_publico = {"score_beta_publico": 0, "leads_total": 0, "erro": str(erro)}

    try:
        onboarding = calcular_saude_onboarding_premium()
    except Exception as erro:
        onboarding = {"score_onboarding": 0, "erro": str(erro)}

    try:
        insights = calcular_saude_beta_insights()
    except Exception as erro:
        insights = {"score_insights": 0, "erro": str(erro)}

    try:
        beta_feedback = calcular_saude_beta_feedback()
    except Exception as erro:
        beta_feedback = {"score_beta": 0, "erro": str(erro)}

    try:
        launch = calcular_saude_launch_readiness()
    except Exception as erro:
        launch = {"score_launch": 0, "erro": str(erro)}

    score_pipeline = 0
    score_pipeline += 20 if len(PIPELINE_CHECKOUT_FUNDADORES) >= 5 else 0
    score_pipeline += 18 if len(CHECKLIST_CHECKOUT) >= 9 else 0
    score_pipeline += 18 if metricas["fundadores_total"] >= 1 else 0
    score_pipeline += 16 if metricas["pagamentos_pendentes"] >= 1 else 0
    score_pipeline += 18 if metricas["fundadores_ativos"] >= 1 else 0
    score_pipeline += 10 if bool(metricas["pipeline_por_status"]) else 0
    score_pipeline = min(100, score_pipeline)

    score_receita = 0
    score_receita += 35 if metricas["mrr_estimado"] >= 59 else 0
    score_receita += 25 if metricas["arr_estimado"] >= 590 else 0
    score_receita += 20 if metricas["fundadores_ativos"] >= 1 else 0
    score_receita += 10 if metricas["taxa_ativacao"] >= 20 else 0
    score_receita += 10 if metricas["fundadores_total"] >= 3 else 0
    score_receita = min(100, score_receita)

    score_operacional = 0
    score_operacional += 18 if "Pix manual" in METODOS_PAGAMENTO_MANUAL else 0
    score_operacional += 18 if CAMINHO_FUNDADORES_VALORIS.name.endswith(".csv") else 0
    score_operacional += 18 if len(STATUS_FUNDADOR) >= 8 else 0
    score_operacional += 16 if len(TERMO_BETA_FUNDADOR["itens"]) >= 6 else 0
    score_operacional += 16 if "Sem promessa de rentabilidade" in CHECKLIST_CHECKOUT else 0
    score_operacional += 14 if "Status manual do fundador registrado" in CHECKLIST_CHECKOUT else 0
    score_operacional = min(100, score_operacional)

    score_risco = 0
    score_risco += 25 if "Não há promessa de lucro" in " ".join(TERMO_BETA_FUNDADOR["itens"]) else 0
    score_risco += 20 if "Não é recomendação personalizada" in " ".join(TERMO_BETA_FUNDADOR["itens"]) else 0
    score_risco += 18 if "Aviso educacional visível" in CHECKLIST_CHECKOUT else 0
    score_risco += 17 if "Sem promessa de rentabilidade" in CHECKLIST_CHECKOUT else 0
    score_risco += 20 if int(launch.get("score_launch", 0) or 0) >= 70 else 0
    score_risco = min(100, score_risco)

    score_base_produto = int(round(
        int(oferta.get("score_oferta", 0) or 0) * 0.26
        + int(beta_publico.get("score_beta_publico", 0) or 0) * 0.20
        + int(onboarding.get("score_onboarding", 0) or 0) * 0.18
        + int(insights.get("score_insights", 0) or 0) * 0.16
        + int(beta_feedback.get("score_beta", 0) or 0) * 0.20
    ))

    score_checkout = int(round(
        score_pipeline * 0.24
        + score_receita * 0.24
        + score_operacional * 0.22
        + score_risco * 0.16
        + score_base_produto * 0.14
    ))

    if metricas["fundadores_ativos"] >= 1 and score_checkout >= 78:
        risco = "Médio controlado"
        decisao = "Checkout manual validado com sinal real de receita"
        proximo_passo = "Acompanhar uso do fundador ativo e só depois automatizar checkout/gateway."
    elif metricas["fundadores_total"] >= 1:
        risco = "Médio"
        decisao = "Pipeline fundador criado, ainda sem validação suficiente de receita"
        proximo_passo = "Converter pelo menos 1 fundador ativo antes de integrar pagamento automático."
    else:
        risco = "Médio/Alto"
        decisao = "Checkout pronto para teste, mas sem fundadores registrados"
        proximo_passo = "Registrar interessados reais e conduzir pagamento manual controlado."

    return {
        "versao": VERSAO_CHECKOUT_FUNDADORES_VALORIS,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score_checkout": max(0, min(100, score_checkout)),
        "score_pipeline": score_pipeline,
        "score_receita": score_receita,
        "score_operacional": score_operacional,
        "score_risco": score_risco,
        "score_base_produto": score_base_produto,
        "fundadores_total": metricas["fundadores_total"],
        "fundadores_ativos": metricas["fundadores_ativos"],
        "mrr_estimado": metricas["mrr_estimado"],
        "arr_estimado": metricas["arr_estimado"],
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo_passo,
        "metricas_fundadores": metricas,
        "pipeline": PIPELINE_CHECKOUT_FUNDADORES,
        "checklist": CHECKLIST_CHECKOUT,
        "termo": TERMO_BETA_FUNDADOR,
        "oferta": oferta,
        "beta_publico": beta_publico,
        "onboarding": onboarding,
        "insights": insights,
        "beta_feedback": beta_feedback,
        "launch": launch,
    }


def salvar_decisao_checkout_fundadores(saude: Dict[str, Any], observacoes: str = "") -> Dict[str, str]:
    _garantir_csv(CAMINHO_DECISOES_CHECKOUT_FUNDADORES, CAMPOS_DECISAO_CHECKOUT)

    registro = {
        "id": str(uuid4())[:8],
        "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score_checkout": str(saude.get("score_checkout", "")),
        "score_pipeline": str(saude.get("score_pipeline", "")),
        "score_receita": str(saude.get("score_receita", "")),
        "score_operacional": str(saude.get("score_operacional", "")),
        "score_risco": str(saude.get("score_risco", "")),
        "fundadores_total": str(saude.get("fundadores_total", "")),
        "fundadores_ativos": str(saude.get("fundadores_ativos", "")),
        "mrr_estimado": str(saude.get("mrr_estimado", "")),
        "arr_estimado": str(saude.get("arr_estimado", "")),
        "risco": _limpar_texto(saude.get("risco")),
        "decisao": _limpar_texto(saude.get("decisao")),
        "proximo_passo": _limpar_texto(saude.get("proximo_passo")),
        "observacoes": _limpar_texto(observacoes),
    }

    with CAMINHO_DECISOES_CHECKOUT_FUNDADORES.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISAO_CHECKOUT)
        escritor.writerow(registro)

    return registro


def gerar_roteiro_checkout_markdown(saude: Dict[str, Any] | None = None) -> str:
    if saude is None:
        saude = calcular_saude_checkout_fundadores()

    etapas = "\n\n".join(
        [
            f"""## {item['etapa']}

**Objetivo:** {item['objetivo']}  
**Ação:** {item['acao']}  
**Critério de saída:** {item['criterio_saida']}
"""
            for item in PIPELINE_CHECKOUT_FUNDADORES
        ]
    )

    return f"""# Roteiro Checkout Manual Fundadores — Valoris

Versão: {VERSAO_CHECKOUT_FUNDADORES_VALORIS}  
Gerado em: {saude["gerado_em"]}

## Diagnóstico

Score Checkout: {saude["score_checkout"]}/100  
Fundadores ativos: {saude["fundadores_ativos"]}  
MRR estimado: R$ {saude["mrr_estimado"]}  
ARR estimado: R$ {saude["arr_estimado"]}  
Decisão: {saude["decisao"]}

## Regra estratégica

Não integrar gateway de pagamento antes de validar disposição real de pagamento manualmente.

## Pipeline

{etapas}

## Próximo passo

{saude["proximo_passo"]}
"""


def gerar_checklist_checkout_markdown(saude: Dict[str, Any] | None = None) -> str:
    if saude is None:
        saude = calcular_saude_checkout_fundadores()

    checklist = "\n".join([f"- [x] {item}" for item in CHECKLIST_CHECKOUT])

    return f"""# Checklist Checkout Fundadores — Valoris

Versão: {VERSAO_CHECKOUT_FUNDADORES_VALORIS}  
Gerado em: {saude["gerado_em"]}

## Status

Score Checkout: {saude["score_checkout"]}/100  
Risco: {saude["risco"]}  
Decisão: {saude["decisao"]}

## Checklist

{checklist}

## Próxima ação

{saude["proximo_passo"]}
"""


def gerar_termo_beta_fundador_markdown(saude: Dict[str, Any] | None = None) -> str:
    if saude is None:
        saude = calcular_saude_checkout_fundadores()

    itens = "\n".join([f"- {item}" for item in TERMO_BETA_FUNDADOR["itens"]])

    return f"""# {TERMO_BETA_FUNDADOR["titulo"]}

Versão: {VERSAO_CHECKOUT_FUNDADORES_VALORIS}  
Gerado em: {saude["gerado_em"]}

## Termos

{itens}

## Observação

Este documento é um rascunho operacional para beta fechado e não substitui revisão jurídica profissional antes de venda pública em escala.
"""


def salvar_roteiro_checkout_markdown() -> Dict[str, Any]:
    saude = calcular_saude_checkout_fundadores()
    CAMINHO_ROTEIRO_CHECKOUT_MD.write_text(gerar_roteiro_checkout_markdown(saude), encoding="utf-8")
    return {"ok": True, "arquivo": str(CAMINHO_ROTEIRO_CHECKOUT_MD), "score_checkout": saude["score_checkout"]}


def salvar_checklist_checkout_markdown() -> Dict[str, Any]:
    saude = calcular_saude_checkout_fundadores()
    CAMINHO_CHECKLIST_CHECKOUT_MD.write_text(gerar_checklist_checkout_markdown(saude), encoding="utf-8")
    return {"ok": True, "arquivo": str(CAMINHO_CHECKLIST_CHECKOUT_MD), "score_checkout": saude["score_checkout"]}


def salvar_termo_beta_fundador_markdown() -> Dict[str, Any]:
    saude = calcular_saude_checkout_fundadores()
    CAMINHO_CONTRATO_BETA_MD.write_text(gerar_termo_beta_fundador_markdown(saude), encoding="utf-8")
    return {"ok": True, "arquivo": str(CAMINHO_CONTRATO_BETA_MD), "score_checkout": saude["score_checkout"]}


def gerar_pipeline_fundadores_json() -> Dict[str, Any]:
    saude = calcular_saude_checkout_fundadores()
    CAMINHO_PIPELINE_FUNDADORES_JSON.write_text(json.dumps(saude, ensure_ascii=False, indent=2), encoding="utf-8")
    return saude


def gerar_manifesto_checkout_fundadores() -> Dict[str, Any]:
    saude = calcular_saude_checkout_fundadores()
    manifesto = {
        "versao": VERSAO_CHECKOUT_FUNDADORES_VALORIS,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "saude": saude,
        "pipeline": PIPELINE_CHECKOUT_FUNDADORES,
        "checklist": CHECKLIST_CHECKOUT,
        "termo": TERMO_BETA_FUNDADOR,
        "estrategia": {
            "objetivo": "Validar receita real manualmente antes de automatizar checkout.",
            "proxima_versao": "Retenção de fundadores ou relatório premium v2.",
            "regra": "Gateway só entra depois de sinal real de pagamento e ativação.",
        },
    }

    CAMINHO_MANIFESTO_CHECKOUT_FUNDADORES.write_text(json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifesto


def _injetar_css_checkout() -> None:
    st.markdown(
        """
        <style>
            .checkout-hero {
                padding: clamp(1.2rem, 3vw, 2.1rem);
                border-radius: 30px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    radial-gradient(circle at top left, rgba(214, 181, 109, 0.24), transparent 32%),
                    radial-gradient(circle at bottom right, rgba(80, 170, 140, 0.22), transparent 36%),
                    linear-gradient(135deg, rgba(6, 12, 23, 0.99), rgba(4, 8, 16, 0.99));
                box-shadow: 0 20px 62px rgba(0, 0, 0, 0.34);
                margin-bottom: 1rem;
            }
            .checkout-eyebrow {
                color: #d6b56d;
                font-size: 0.74rem;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                font-weight: 880;
                margin-bottom: 0.35rem;
            }
            .checkout-title {
                color: #f4f7fb;
                font-size: clamp(1.8rem, 5.5vw, 3.25rem);
                font-weight: 950;
                line-height: 1.02;
                letter-spacing: -0.058em;
                margin-bottom: 0.55rem;
            }
            .checkout-subtitle {
                color: rgba(244, 247, 251, 0.75);
                font-size: clamp(0.94rem, 2.2vw, 1.06rem);
                line-height: 1.56;
                max-width: 1050px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def renderizar_checkout_fundadores_valoris() -> None:
    _injetar_css_checkout()

    st.markdown(
        f"""
        <div class="checkout-hero">
            <div class="checkout-eyebrow">Valoris • Checkout Fundadores • v{VERSAO_CHECKOUT_FUNDADORES_VALORIS}</div>
            <div class="checkout-title">Receita real antes de automação.</div>
            <div class="checkout-subtitle">
                Controle manual de fundadores, status, preço, pagamento, MRR estimado e ativação beta
                antes de conectar um gateway.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    saude = calcular_saude_checkout_fundadores()

    st.markdown("### Diagnóstico do checkout manual")
    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Score Checkout", f"{saude['score_checkout']}/100")

    with col_2:
        st.metric("Fundadores ativos", saude["fundadores_ativos"])

    with col_3:
        st.metric("MRR estimado", f"R$ {saude['mrr_estimado']}")

    with col_4:
        st.metric("Risco", saude["risco"])

    st.progress(saude["score_checkout"] / 100)

    if saude["fundadores_ativos"] >= 1 and saude["score_checkout"] >= 78:
        st.success(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    elif saude["fundadores_total"] >= 1:
        st.warning(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    else:
        st.info(f"**{saude['decisao']}** — {saude['proximo_passo']}")

    st.divider()

    st.markdown("### Pipeline fundador")
    st.dataframe(PIPELINE_CHECKOUT_FUNDADORES, width="stretch", hide_index=True)

    st.markdown("### Registrar fundador")

    with st.form("form_fundador_valoris"):
        col_a, col_b = st.columns(2)

        with col_a:
            nome = st.text_input("Nome")
            email = st.text_input("E-mail")
            perfil = st.text_input("Perfil", value="Investidor intermediário")
            plano = st.selectbox("Plano", [plano["plano"] for plano in PLANOS_BETA_FUNDADOR])
            plano_info = _plano_por_nome(plano)
            valor_mensal = st.number_input("Valor mensal (R$)", min_value=0.0, value=float(plano_info["preco_mensal"]), step=1.0)
            valor_anual = st.number_input("Valor anual (R$)", min_value=0.0, value=float(plano_info["preco_anual"]), step=10.0)

        with col_b:
            status = st.selectbox("Status", STATUS_FUNDADOR)
            metodo_pagamento = st.selectbox("Método de pagamento", METODOS_PAGAMENTO_MANUAL)
            data_inicio = st.date_input("Data de início")
            data_proximo_contato = st.date_input("Próximo contato")
            observacoes = st.text_area("Observações", height=120)

        enviado = st.form_submit_button("Salvar fundador")

        if enviado:
            if not _email_valido(email):
                st.error("E-mail inválido. Revise antes de salvar.")
            else:
                registro = salvar_fundador_valoris(
                    {
                        "nome": nome,
                        "email": email,
                        "perfil": perfil,
                        "plano": plano,
                        "valor_mensal": valor_mensal,
                        "valor_anual": valor_anual,
                        "status": status,
                        "metodo_pagamento": metodo_pagamento,
                        "data_inicio": str(data_inicio),
                        "data_proximo_contato": str(data_proximo_contato),
                        "observacoes": observacoes,
                        "origem": "aba_checkout_fundadores",
                    }
                )
                st.success(f"Fundador salvo: {registro['id']}")
                st.rerun()

    st.divider()

    st.markdown("### Métricas de fundadores")
    st.json(saude["metricas_fundadores"])

    if saude["metricas_fundadores"]["ultimos_fundadores"]:
        st.dataframe(saude["metricas_fundadores"]["ultimos_fundadores"], width="stretch", hide_index=True)

    st.markdown("### Termo beta fundador")
    st.info(TERMO_BETA_FUNDADOR["titulo"])
    for item in TERMO_BETA_FUNDADOR["itens"]:
        st.write(f"- {item}")

    st.divider()

    col_btn_1, col_btn_2, col_btn_3, col_btn_4 = st.columns(4)

    with col_btn_1:
        if st.button("Gerar fundador exemplo", key="checkout_fundador_exemplo"):
            registro = gerar_fundador_exemplo()
            st.success(f"Fundador exemplo criado: {registro['id']}")
            st.rerun()

    with col_btn_2:
        if st.button("Gerar fundador ativo exemplo", key="checkout_fundador_ativo_exemplo"):
            registro = gerar_fundador_ativo_exemplo()
            st.success(f"Fundador ativo exemplo criado: {registro['id']}")
            st.rerun()

    with col_btn_3:
        if st.button("Gerar manifesto", key="checkout_manifesto"):
            manifesto = gerar_manifesto_checkout_fundadores()
            st.success(f"Manifesto gerado: {CAMINHO_MANIFESTO_CHECKOUT_FUNDADORES}")
            st.json({"versao": manifesto["versao"], "score": manifesto["saude"]["score_checkout"]})

    with col_btn_4:
        if st.button("Gerar pipeline JSON", key="checkout_pipeline_json"):
            retorno = gerar_pipeline_fundadores_json()
            st.success(f"Pipeline salvo: {CAMINHO_PIPELINE_FUNDADORES_JSON}")
            st.json({"score_checkout": retorno["score_checkout"], "mrr_estimado": retorno["mrr_estimado"]})

    col_btn_5, col_btn_6, col_btn_7 = st.columns(3)

    with col_btn_5:
        if st.button("Salvar roteiro .md", key="checkout_roteiro"):
            retorno = salvar_roteiro_checkout_markdown()
            st.success(f"Roteiro salvo: {retorno['arquivo']}")
            st.json(retorno)

    with col_btn_6:
        if st.button("Salvar checklist .md", key="checkout_checklist"):
            retorno = salvar_checklist_checkout_markdown()
            st.success(f"Checklist salvo: {retorno['arquivo']}")
            st.json(retorno)

    with col_btn_7:
        if st.button("Salvar termo .md", key="checkout_termo"):
            retorno = salvar_termo_beta_fundador_markdown()
            st.success(f"Termo salvo: {retorno['arquivo']}")
            st.json(retorno)

    if st.button("Salvar decisão Checkout", key="checkout_decisao"):
        registro = salvar_decisao_checkout_fundadores(saude, observacoes="Decisão gerada pelo checkout manual de fundadores.")
        st.success(f"Decisão salva: {registro['decisao']}")
        st.rerun()

    st.download_button(
        "Baixar roteiro checkout (.md)",
        data=gerar_roteiro_checkout_markdown(saude),
        file_name="ROTEIRO_CHECKOUT_MANUAL_FUNDADORES_VALORIS.md",
        mime="text/markdown",
        key="download_roteiro_checkout",
    )

    st.download_button(
        "Baixar termo beta fundador (.md)",
        data=gerar_termo_beta_fundador_markdown(saude),
        file_name="TERMO_BETA_FUNDADOR_VALORIS.md",
        mime="text/markdown",
        key="download_termo_beta_fundador",
    )

    st.download_button(
        "Baixar fundadores (.csv)",
        data=gerar_csv_fundadores_valoris(),
        file_name="fundadores_beta_valoris.csv",
        mime="text/csv",
        key="download_fundadores_valoris",
    )


def executar_autoteste_checkout_fundadores_valoris() -> List[Dict[str, str]]:
    saude = calcular_saude_checkout_fundadores()

    return [
        {
            "teste": "versao_checkout_fundadores",
            "status": "OK" if VERSAO_CHECKOUT_FUNDADORES_VALORIS == "3.8.83" else "FALHA",
            "detalhe": VERSAO_CHECKOUT_FUNDADORES_VALORIS,
        },
        {
            "teste": "score_checkout",
            "status": "OK" if 0 <= saude["score_checkout"] <= 100 else "FALHA",
            "detalhe": str(saude["score_checkout"]),
        },
        {
            "teste": "pipeline",
            "status": "OK" if len(PIPELINE_CHECKOUT_FUNDADORES) >= 5 else "FALHA",
            "detalhe": str(len(PIPELINE_CHECKOUT_FUNDADORES)),
        },
        {
            "teste": "renderizador",
            "status": "OK" if callable(renderizar_checkout_fundadores_valoris) else "FALHA",
            "detalhe": "renderizar_checkout_fundadores_valoris",
        },
    ]
