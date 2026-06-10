# retencao_fundadores_valoris.py

from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

import streamlit as st

from checkout_fundadores_valoris import (
    carregar_fundadores_valoris,
    calcular_saude_checkout_fundadores,
)
from oferta_beta_fundador_valoris import calcular_saude_oferta_beta_fundador
from beta_publico_valoris import calcular_saude_beta_publico
from onboarding_premium_valoris import calcular_saude_onboarding_premium
from beta_insights_valoris import calcular_saude_beta_insights
from beta_feedback_valoris import calcular_saude_beta_feedback
from analise_premium_valoris import calcular_saude_analise_premium
from launch_readiness_valoris import calcular_saude_launch_readiness


VERSAO_RETENCAO_FUNDADORES_VALORIS = "3.8.84"

CAMINHO_ATIVACOES_FUNDADORES = Path("ativacoes_fundadores_valoris.csv")
CAMINHO_FEEDBACKS_POS_PAGAMENTO = Path("feedbacks_pos_pagamento_valoris.csv")
CAMINHO_DECISOES_RETENCAO = Path("decisoes_retencao_fundadores_valoris.csv")
CAMINHO_MANIFESTO_RETENCAO = Path("manifesto_retencao_fundadores_valoris.json")
CAMINHO_PLAYBOOK_RETENCAO_MD = Path("PLAYBOOK_RETENCAO_FUNDADORES_VALORIS.md")
CAMINHO_CHECKLIST_RETENCAO_MD = Path("CHECKLIST_RETENCAO_FUNDADORES_VALORIS.md")
CAMINHO_RELATORIO_RETENCAO_MD = Path("RELATORIO_RETENCAO_FUNDADORES_VALORIS.md")

CAMPOS_ATIVACAO = [
    "id",
    "data_registro",
    "fundador_email",
    "fundador_nome",
    "plano",
    "primeiro_acesso",
    "primeira_analise",
    "relatorio_exportado",
    "feedback_enviado",
    "duvida_principal",
    "valor_percebido",
    "risco_cancelamento",
    "proximo_contato",
    "status_sucesso",
    "observacoes",
]

CAMPOS_FEEDBACK_POS_PAGAMENTO = [
    "id",
    "data_registro",
    "fundador_email",
    "fundador_nome",
    "clareza_valor",
    "utilidade_real",
    "confianca",
    "facilidade_uso",
    "chance_continuar",
    "principal_valor",
    "principal_friccao",
    "feature_necessaria",
    "pagaria_novamente",
    "observacoes",
]

CAMPOS_DECISAO_RETENCAO = [
    "id",
    "data_registro",
    "score_retencao",
    "score_ativacao",
    "score_valor_percebido",
    "score_risco_churn",
    "score_operacional",
    "fundadores_total",
    "fundadores_ativos",
    "ativacoes_total",
    "feedbacks_pos_pagamento_total",
    "mrr_estimado",
    "risco",
    "decisao",
    "proximo_passo",
    "observacoes",
]

MARCOS_RETENCAO = [
    {
        "marco": "Primeiro acesso concluído",
        "peso": 18,
        "motivo": "Sem primeiro acesso, não há chance real de retenção.",
    },
    {
        "marco": "Primeira análise gerada",
        "peso": 24,
        "motivo": "A primeira análise é o momento principal de valor.",
    },
    {
        "marco": "Relatório exportado",
        "peso": 18,
        "motivo": "Exportar relatório aumenta valor percebido e recorrência.",
    },
    {
        "marco": "Feedback pós-pagamento enviado",
        "peso": 20,
        "motivo": "Feedback de pagante é mais forte que opinião gratuita.",
    },
    {
        "marco": "Próximo contato definido",
        "peso": 10,
        "motivo": "Retenção no beta precisa de acompanhamento próximo.",
    },
    {
        "marco": "Baixo risco de cancelamento",
        "peso": 10,
        "motivo": "Pagante com risco baixo indica encaixe melhor de produto.",
    },
]

PLAYBOOK_RETENCAO = [
    {
        "etapa": "D0 — Confirmação de fundador",
        "objetivo": "Garantir que o fundador entendeu acesso, limites e proposta.",
        "acao": "Enviar mensagem de boas-vindas, termo beta e roteiro de primeira análise.",
        "sinal_sucesso": "Fundador responde ou acessa o fluxo.",
    },
    {
        "etapa": "D1 — Primeira análise",
        "objetivo": "Levar o fundador ao momento de valor rapidamente.",
        "acao": "Guiar para analisar uma empresa exemplo ou uma empresa da carteira dele.",
        "sinal_sucesso": "Primeira análise registrada.",
    },
    {
        "etapa": "D3 — Relatório e tese",
        "objetivo": "Mostrar que a Valoris não é só calculadora.",
        "acao": "Incentivar exportação do relatório e leitura da tese/risco.",
        "sinal_sucesso": "Relatório exportado ou tese comentada.",
    },
    {
        "etapa": "D7 — Feedback de pagante",
        "objetivo": "Medir valor percebido com quem já pagou.",
        "acao": "Coletar notas de utilidade, clareza, confiança e chance de continuar.",
        "sinal_sucesso": "Feedback pós-pagamento registrado.",
    },
    {
        "etapa": "D14 — Retenção ou ajuste",
        "objetivo": "Decidir se o fundador deve continuar, pausar ou virar estudo de caso.",
        "acao": "Mapear objeção principal, feature necessária e intenção de continuidade.",
        "sinal_sucesso": "Próximo passo claro para retenção.",
    },
]

CHECKLIST_RETENCAO = [
    "Fundador recebeu boas-vindas",
    "Primeiro acesso registrado",
    "Primeira análise registrada",
    "Relatório exportado",
    "Feedback pós-pagamento coletado",
    "Risco de cancelamento classificado",
    "Próximo contato definido",
    "Objeção principal registrada",
    "Feature necessária registrada",
    "Decisão de retenção salva",
]


def _limpar_texto(valor: Any) -> str:
    if valor is None:
        return ""
    return str(valor).strip()


def _email_valido(email: str) -> bool:
    email = _limpar_texto(email).lower()
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))


def _to_int(valor: Any, padrao: int = 0) -> int:
    try:
        return int(valor)
    except Exception:
        return padrao


def _to_float(valor: Any, padrao: float = 0.0) -> float:
    try:
        if isinstance(valor, str):
            valor = valor.replace("R$", "").replace(".", "").replace(",", ".").strip()
        return float(valor)
    except Exception:
        return padrao


def _bool_str(valor: Any) -> str:
    return "True" if bool(valor) else "False"


def _as_bool(valor: Any) -> bool:
    if isinstance(valor, bool):
        return valor
    return str(valor).strip().lower() in {"true", "1", "sim", "yes", "y"}


def _garantir_csv(caminho: Path, campos: List[str]) -> None:
    if caminho.exists():
        return
    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()


def carregar_ativacoes_fundadores() -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_ATIVACOES_FUNDADORES, CAMPOS_ATIVACAO)
    with CAMINHO_ATIVACOES_FUNDADORES.open("r", newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def carregar_feedbacks_pos_pagamento() -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_FEEDBACKS_POS_PAGAMENTO, CAMPOS_FEEDBACK_POS_PAGAMENTO)
    with CAMINHO_FEEDBACKS_POS_PAGAMENTO.open("r", newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def carregar_decisoes_retencao_fundadores() -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_DECISOES_RETENCAO, CAMPOS_DECISAO_RETENCAO)
    with CAMINHO_DECISOES_RETENCAO.open("r", newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def gerar_csv_ativacoes_fundadores() -> str:
    _garantir_csv(CAMINHO_ATIVACOES_FUNDADORES, CAMPOS_ATIVACAO)
    return CAMINHO_ATIVACOES_FUNDADORES.read_text(encoding="utf-8")


def gerar_csv_feedbacks_pos_pagamento() -> str:
    _garantir_csv(CAMINHO_FEEDBACKS_POS_PAGAMENTO, CAMPOS_FEEDBACK_POS_PAGAMENTO)
    return CAMINHO_FEEDBACKS_POS_PAGAMENTO.read_text(encoding="utf-8")


def gerar_csv_decisoes_retencao() -> str:
    _garantir_csv(CAMINHO_DECISOES_RETENCAO, CAMPOS_DECISAO_RETENCAO)
    return CAMINHO_DECISOES_RETENCAO.read_text(encoding="utf-8")


def salvar_ativacao_fundador(dados: Dict[str, Any]) -> Dict[str, str]:
    _garantir_csv(CAMINHO_ATIVACOES_FUNDADORES, CAMPOS_ATIVACAO)

    registro = {
        "id": str(uuid4())[:8],
        "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "fundador_email": _limpar_texto(dados.get("fundador_email")).lower(),
        "fundador_nome": _limpar_texto(dados.get("fundador_nome")),
        "plano": _limpar_texto(dados.get("plano")),
        "primeiro_acesso": _bool_str(dados.get("primeiro_acesso")),
        "primeira_analise": _bool_str(dados.get("primeira_analise")),
        "relatorio_exportado": _bool_str(dados.get("relatorio_exportado")),
        "feedback_enviado": _bool_str(dados.get("feedback_enviado")),
        "duvida_principal": _limpar_texto(dados.get("duvida_principal")),
        "valor_percebido": str(_to_int(dados.get("valor_percebido"), 0)),
        "risco_cancelamento": _limpar_texto(dados.get("risco_cancelamento", "Médio")),
        "proximo_contato": _limpar_texto(dados.get("proximo_contato")),
        "status_sucesso": _limpar_texto(dados.get("status_sucesso", "em_acompanhamento")),
        "observacoes": _limpar_texto(dados.get("observacoes")),
    }

    with CAMINHO_ATIVACOES_FUNDADORES.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_ATIVACAO)
        escritor.writerow(registro)

    return registro


def salvar_feedback_pos_pagamento(dados: Dict[str, Any]) -> Dict[str, str]:
    _garantir_csv(CAMINHO_FEEDBACKS_POS_PAGAMENTO, CAMPOS_FEEDBACK_POS_PAGAMENTO)

    registro = {
        "id": str(uuid4())[:8],
        "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "fundador_email": _limpar_texto(dados.get("fundador_email")).lower(),
        "fundador_nome": _limpar_texto(dados.get("fundador_nome")),
        "clareza_valor": str(_to_int(dados.get("clareza_valor"), 0)),
        "utilidade_real": str(_to_int(dados.get("utilidade_real"), 0)),
        "confianca": str(_to_int(dados.get("confianca"), 0)),
        "facilidade_uso": str(_to_int(dados.get("facilidade_uso"), 0)),
        "chance_continuar": str(_to_int(dados.get("chance_continuar"), 0)),
        "principal_valor": _limpar_texto(dados.get("principal_valor")),
        "principal_friccao": _limpar_texto(dados.get("principal_friccao")),
        "feature_necessaria": _limpar_texto(dados.get("feature_necessaria")),
        "pagaria_novamente": _bool_str(dados.get("pagaria_novamente")),
        "observacoes": _limpar_texto(dados.get("observacoes")),
    }

    with CAMINHO_FEEDBACKS_POS_PAGAMENTO.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_FEEDBACK_POS_PAGAMENTO)
        escritor.writerow(registro)

    return registro


def gerar_ativacao_exemplo() -> Dict[str, str]:
    fundadores = carregar_fundadores_valoris()
    fundador_ativo = next((item for item in reversed(fundadores) if item.get("status") == "ativo"), None)
    fundador = fundador_ativo or (fundadores[-1] if fundadores else {})

    return salvar_ativacao_fundador(
        {
            "fundador_email": fundador.get("email", f"fundador.retencao.{datetime.now().strftime('%H%M%S')}@exemplo.com"),
            "fundador_nome": fundador.get("nome", "Fundador Retenção Exemplo"),
            "plano": fundador.get("plano", "Beta Fundador Pro"),
            "primeiro_acesso": True,
            "primeira_analise": True,
            "relatorio_exportado": True,
            "feedback_enviado": True,
            "duvida_principal": "Como acompanhar uma empresa depois da primeira análise?",
            "valor_percebido": 8,
            "risco_cancelamento": "Baixo",
            "proximo_contato": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "status_sucesso": "ativado",
            "observacoes": "Ativação exemplo para validar retenção de fundadores.",
        }
    )


def gerar_feedback_pos_pagamento_exemplo() -> Dict[str, str]:
    fundadores = carregar_fundadores_valoris()
    fundador_ativo = next((item for item in reversed(fundadores) if item.get("status") == "ativo"), None)
    fundador = fundador_ativo or (fundadores[-1] if fundadores else {})

    return salvar_feedback_pos_pagamento(
        {
            "fundador_email": fundador.get("email", f"fundador.feedback.{datetime.now().strftime('%H%M%S')}@exemplo.com"),
            "fundador_nome": fundador.get("nome", "Fundador Feedback Exemplo"),
            "clareza_valor": 9,
            "utilidade_real": 8,
            "confianca": 8,
            "facilidade_uso": 8,
            "chance_continuar": 8,
            "principal_valor": "A tese e o relatório deixam a análise mais organizada.",
            "principal_friccao": "Ainda quero dados reais automáticos no futuro.",
            "feature_necessaria": "Watchlist para acompanhar preço teto e oportunidade.",
            "pagaria_novamente": True,
            "observacoes": "Feedback pós-pagamento exemplo para validar retenção.",
        }
    )


def _media_notas(feedbacks: List[Dict[str, str]], campo: str) -> float:
    valores = [_to_int(item.get(campo), 0) for item in feedbacks if _to_int(item.get(campo), 0) > 0]
    if not valores:
        return 0.0
    return round(sum(valores) / len(valores), 2)


def calcular_metricas_retencao() -> Dict[str, Any]:
    fundadores = carregar_fundadores_valoris()
    ativacoes = carregar_ativacoes_fundadores()
    feedbacks = carregar_feedbacks_pos_pagamento()

    fundadores_ativos = [item for item in fundadores if item.get("status") == "ativo"]
    mrr_estimado = round(sum(_to_float(item.get("valor_mensal"), 0.0) for item in fundadores_ativos), 2)
    arr_estimado = round(mrr_estimado * 12, 2)

    ativacoes_total = len(ativacoes)
    feedbacks_total = len(feedbacks)

    primeira_analise = sum(1 for item in ativacoes if _as_bool(item.get("primeira_analise")))
    relatorio_exportado = sum(1 for item in ativacoes if _as_bool(item.get("relatorio_exportado")))
    feedback_enviado = sum(1 for item in ativacoes if _as_bool(item.get("feedback_enviado")))
    risco_alto = sum(1 for item in ativacoes if item.get("risco_cancelamento") == "Alto")
    risco_baixo = sum(1 for item in ativacoes if item.get("risco_cancelamento") == "Baixo")
    pagaria_novamente = sum(1 for item in feedbacks if _as_bool(item.get("pagaria_novamente")))

    return {
        "fundadores_total": len(fundadores),
        "fundadores_ativos": len(fundadores_ativos),
        "ativacoes_total": ativacoes_total,
        "feedbacks_pos_pagamento_total": feedbacks_total,
        "mrr_estimado": mrr_estimado,
        "arr_estimado": arr_estimado,
        "primeira_analise_total": primeira_analise,
        "relatorio_exportado_total": relatorio_exportado,
        "feedback_enviado_total": feedback_enviado,
        "risco_alto_total": risco_alto,
        "risco_baixo_total": risco_baixo,
        "pagaria_novamente_total": pagaria_novamente,
        "taxa_primeira_analise": round((primeira_analise / ativacoes_total) * 100, 2) if ativacoes_total else 0,
        "taxa_relatorio_exportado": round((relatorio_exportado / ativacoes_total) * 100, 2) if ativacoes_total else 0,
        "taxa_feedback_enviado": round((feedback_enviado / ativacoes_total) * 100, 2) if ativacoes_total else 0,
        "taxa_pagaria_novamente": round((pagaria_novamente / feedbacks_total) * 100, 2) if feedbacks_total else 0,
        "media_clareza_valor": _media_notas(feedbacks, "clareza_valor"),
        "media_utilidade_real": _media_notas(feedbacks, "utilidade_real"),
        "media_confianca": _media_notas(feedbacks, "confianca"),
        "media_facilidade_uso": _media_notas(feedbacks, "facilidade_uso"),
        "media_chance_continuar": _media_notas(feedbacks, "chance_continuar"),
        "ultimas_ativacoes": ativacoes[-25:],
        "ultimos_feedbacks": feedbacks[-25:],
    }


def calcular_saude_retencao_fundadores() -> Dict[str, Any]:
    metricas = calcular_metricas_retencao()

    try:
        checkout = calcular_saude_checkout_fundadores()
    except Exception as erro:
        checkout = {"score_checkout": 0, "erro": str(erro)}

    try:
        oferta = calcular_saude_oferta_beta_fundador()
    except Exception as erro:
        oferta = {"score_oferta": 0, "erro": str(erro)}

    try:
        beta_publico = calcular_saude_beta_publico()
    except Exception as erro:
        beta_publico = {"score_beta_publico": 0, "erro": str(erro)}

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
        premium = calcular_saude_analise_premium()
    except Exception as erro:
        premium = {"score_produto_premium": 0, "erro": str(erro)}

    try:
        launch = calcular_saude_launch_readiness()
    except Exception as erro:
        launch = {"score_launch": 0, "erro": str(erro)}

    score_ativacao = 0
    score_ativacao += 18 if metricas["ativacoes_total"] >= 1 else 0
    score_ativacao += 24 if metricas["taxa_primeira_analise"] >= 70 else 0
    score_ativacao += 18 if metricas["taxa_relatorio_exportado"] >= 60 else 0
    score_ativacao += 20 if metricas["taxa_feedback_enviado"] >= 60 else 0
    score_ativacao += 10 if metricas["risco_baixo_total"] >= 1 else 0
    score_ativacao += 10 if metricas["fundadores_ativos"] >= 1 else 0
    score_ativacao = min(100, score_ativacao)

    score_valor_percebido = 0
    score_valor_percebido += int(metricas["media_clareza_valor"] * 2)
    score_valor_percebido += int(metricas["media_utilidade_real"] * 2)
    score_valor_percebido += int(metricas["media_confianca"] * 1.6)
    score_valor_percebido += int(metricas["media_facilidade_uso"] * 1.4)
    score_valor_percebido += int(metricas["media_chance_continuar"] * 2)
    score_valor_percebido += 10 if metricas["taxa_pagaria_novamente"] >= 70 else 0
    score_valor_percebido = min(100, score_valor_percebido)

    if metricas["ativacoes_total"] == 0:
        score_risco_churn = 25
    else:
        score_risco_churn = 100
        score_risco_churn -= metricas["risco_alto_total"] * 25
        score_risco_churn -= max(0, 70 - metricas["taxa_primeira_analise"]) * 0.25
        score_risco_churn -= max(0, 70 - metricas["taxa_pagaria_novamente"]) * 0.25 if metricas["feedbacks_pos_pagamento_total"] else 20
        score_risco_churn = int(max(0, min(100, score_risco_churn)))

    score_operacional = 0
    score_operacional += 20 if len(PLAYBOOK_RETENCAO) >= 5 else 0
    score_operacional += 18 if len(CHECKLIST_RETENCAO) >= 10 else 0
    score_operacional += 18 if CAMINHO_ATIVACOES_FUNDADORES.name.endswith(".csv") else 0
    score_operacional += 16 if CAMINHO_FEEDBACKS_POS_PAGAMENTO.name.endswith(".csv") else 0
    score_operacional += 14 if metricas["mrr_estimado"] >= 59 else 0
    score_operacional += 14 if int(launch.get("score_launch", 0) or 0) >= 70 else 0
    score_operacional = min(100, score_operacional)

    score_base_produto = int(round(
        int(checkout.get("score_checkout", 0) or 0) * 0.22
        + int(oferta.get("score_oferta", 0) or 0) * 0.18
        + int(beta_publico.get("score_beta_publico", 0) or 0) * 0.14
        + int(onboarding.get("score_onboarding", 0) or 0) * 0.16
        + int(insights.get("score_insights", 0) or 0) * 0.12
        + int(beta_feedback.get("score_beta", 0) or 0) * 0.10
        + int(premium.get("score_produto_premium", 0) or 0) * 0.08
    ))

    score_retencao = int(round(
        score_ativacao * 0.28
        + score_valor_percebido * 0.24
        + score_risco_churn * 0.20
        + score_operacional * 0.16
        + score_base_produto * 0.12
    ))

    if metricas["fundadores_ativos"] >= 1 and metricas["feedbacks_pos_pagamento_total"] >= 1 and score_retencao >= 82:
        risco = "Médio controlado"
        decisao = "Retenção inicial validada com sinal de valor pós-pagamento"
        proximo_passo = "Priorizar feature mais pedida por pagantes e acompanhar renovação."
    elif metricas["fundadores_ativos"] >= 1 and metricas["ativacoes_total"] >= 1:
        risco = "Médio"
        decisao = "Ativação inicial existe, mas retenção ainda precisa de mais evidência"
        proximo_passo = "Coletar feedback pós-pagamento e reduzir fricção da primeira análise."
    elif metricas["fundadores_ativos"] >= 1:
        risco = "Médio/Alto"
        decisao = "Há fundador ativo, mas ativação ainda não foi comprovada"
        proximo_passo = "Guiar primeiro acesso, primeira análise e relatório exportado."
    else:
        risco = "Alto"
        decisao = "Não há base suficiente para falar em retenção"
        proximo_passo = "Converter e ativar pelo menos 1 fundador antes de automatizar crescimento."

    return {
        "versao": VERSAO_RETENCAO_FUNDADORES_VALORIS,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score_retencao": max(0, min(100, score_retencao)),
        "score_ativacao": score_ativacao,
        "score_valor_percebido": score_valor_percebido,
        "score_risco_churn": score_risco_churn,
        "score_operacional": score_operacional,
        "score_base_produto": score_base_produto,
        "fundadores_total": metricas["fundadores_total"],
        "fundadores_ativos": metricas["fundadores_ativos"],
        "ativacoes_total": metricas["ativacoes_total"],
        "feedbacks_pos_pagamento_total": metricas["feedbacks_pos_pagamento_total"],
        "mrr_estimado": metricas["mrr_estimado"],
        "arr_estimado": metricas["arr_estimado"],
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo_passo,
        "metricas_retencao": metricas,
        "marcos": MARCOS_RETENCAO,
        "playbook": PLAYBOOK_RETENCAO,
        "checklist": CHECKLIST_RETENCAO,
        "checkout": checkout,
        "oferta": oferta,
        "beta_publico": beta_publico,
        "onboarding": onboarding,
        "insights": insights,
        "beta_feedback": beta_feedback,
        "premium": premium,
        "launch": launch,
    }


def salvar_decisao_retencao_fundadores(saude: Dict[str, Any], observacoes: str = "") -> Dict[str, str]:
    _garantir_csv(CAMINHO_DECISOES_RETENCAO, CAMPOS_DECISAO_RETENCAO)

    registro = {
        "id": str(uuid4())[:8],
        "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score_retencao": str(saude.get("score_retencao", "")),
        "score_ativacao": str(saude.get("score_ativacao", "")),
        "score_valor_percebido": str(saude.get("score_valor_percebido", "")),
        "score_risco_churn": str(saude.get("score_risco_churn", "")),
        "score_operacional": str(saude.get("score_operacional", "")),
        "fundadores_total": str(saude.get("fundadores_total", "")),
        "fundadores_ativos": str(saude.get("fundadores_ativos", "")),
        "ativacoes_total": str(saude.get("ativacoes_total", "")),
        "feedbacks_pos_pagamento_total": str(saude.get("feedbacks_pos_pagamento_total", "")),
        "mrr_estimado": str(saude.get("mrr_estimado", "")),
        "risco": _limpar_texto(saude.get("risco")),
        "decisao": _limpar_texto(saude.get("decisao")),
        "proximo_passo": _limpar_texto(saude.get("proximo_passo")),
        "observacoes": _limpar_texto(observacoes),
    }

    with CAMINHO_DECISOES_RETENCAO.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISAO_RETENCAO)
        escritor.writerow(registro)

    return registro


def gerar_playbook_retencao_markdown(saude: Dict[str, Any] | None = None) -> str:
    if saude is None:
        saude = calcular_saude_retencao_fundadores()

    etapas = "\n\n".join(
        [
            f"""## {item['etapa']}

**Objetivo:** {item['objetivo']}  
**Ação:** {item['acao']}  
**Sinal de sucesso:** {item['sinal_sucesso']}
"""
            for item in PLAYBOOK_RETENCAO
        ]
    )

    return f"""# Playbook Retenção de Fundadores — Valoris

Versão: {VERSAO_RETENCAO_FUNDADORES_VALORIS}  
Gerado em: {saude["gerado_em"]}

## Diagnóstico

Score Retenção: {saude["score_retencao"]}/100  
Fundadores ativos: {saude["fundadores_ativos"]}  
Ativações: {saude["ativacoes_total"]}  
Feedbacks pós-pagamento: {saude["feedbacks_pos_pagamento_total"]}  
MRR estimado: R$ {saude["mrr_estimado"]}  
Decisão: {saude["decisao"]}

## Princípio

Receita inicial não prova SaaS. Retenção começa quando o fundador usa, percebe valor e quer continuar.

## Etapas

{etapas}

## Próximo passo

{saude["proximo_passo"]}
"""


def gerar_checklist_retencao_markdown(saude: Dict[str, Any] | None = None) -> str:
    if saude is None:
        saude = calcular_saude_retencao_fundadores()

    checklist = "\n".join([f"- [x] {item}" for item in CHECKLIST_RETENCAO])

    return f"""# Checklist Retenção de Fundadores — Valoris

Versão: {VERSAO_RETENCAO_FUNDADORES_VALORIS}  
Gerado em: {saude["gerado_em"]}

## Status

Score Retenção: {saude["score_retencao"]}/100  
Risco: {saude["risco"]}  
Decisão: {saude["decisao"]}

## Checklist

{checklist}

## Próxima ação

{saude["proximo_passo"]}
"""


def gerar_relatorio_retencao_markdown(saude: Dict[str, Any] | None = None) -> str:
    if saude is None:
        saude = calcular_saude_retencao_fundadores()

    metricas = saude["metricas_retencao"]

    return f"""# Relatório de Retenção — Fundadores Valoris

Versão: {VERSAO_RETENCAO_FUNDADORES_VALORIS}  
Gerado em: {saude["gerado_em"]}

## Resumo executivo

Score Retenção: {saude["score_retencao"]}/100  
Decisão: {saude["decisao"]}  
Risco: {saude["risco"]}  
Próximo passo: {saude["proximo_passo"]}

## Métricas principais

- Fundadores totais: {saude["fundadores_total"]}
- Fundadores ativos: {saude["fundadores_ativos"]}
- Ativações registradas: {saude["ativacoes_total"]}
- Feedbacks pós-pagamento: {saude["feedbacks_pos_pagamento_total"]}
- MRR estimado: R$ {saude["mrr_estimado"]}
- ARR estimado: R$ {saude["arr_estimado"]}
- Taxa de primeira análise: {metricas["taxa_primeira_analise"]}%
- Taxa de relatório exportado: {metricas["taxa_relatorio_exportado"]}%
- Taxa de pagaria novamente: {metricas["taxa_pagaria_novamente"]}%

## Leitura

A próxima fase deve priorizar uso recorrente e valor percebido dos fundadores antes de automatizar growth, checkout ou integrações complexas.
"""


def salvar_playbook_retencao_markdown() -> Dict[str, Any]:
    saude = calcular_saude_retencao_fundadores()
    CAMINHO_PLAYBOOK_RETENCAO_MD.write_text(gerar_playbook_retencao_markdown(saude), encoding="utf-8")
    return {"ok": True, "arquivo": str(CAMINHO_PLAYBOOK_RETENCAO_MD), "score_retencao": saude["score_retencao"]}


def salvar_checklist_retencao_markdown() -> Dict[str, Any]:
    saude = calcular_saude_retencao_fundadores()
    CAMINHO_CHECKLIST_RETENCAO_MD.write_text(gerar_checklist_retencao_markdown(saude), encoding="utf-8")
    return {"ok": True, "arquivo": str(CAMINHO_CHECKLIST_RETENCAO_MD), "score_retencao": saude["score_retencao"]}


def salvar_relatorio_retencao_markdown() -> Dict[str, Any]:
    saude = calcular_saude_retencao_fundadores()
    CAMINHO_RELATORIO_RETENCAO_MD.write_text(gerar_relatorio_retencao_markdown(saude), encoding="utf-8")
    return {"ok": True, "arquivo": str(CAMINHO_RELATORIO_RETENCAO_MD), "score_retencao": saude["score_retencao"]}


def gerar_manifesto_retencao_fundadores() -> Dict[str, Any]:
    saude = calcular_saude_retencao_fundadores()
    manifesto = {
        "versao": VERSAO_RETENCAO_FUNDADORES_VALORIS,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "saude": saude,
        "marcos": MARCOS_RETENCAO,
        "playbook": PLAYBOOK_RETENCAO,
        "checklist": CHECKLIST_RETENCAO,
        "estrategia": {
            "objetivo": "Medir ativação, valor percebido e risco de churn dos fundadores.",
            "proxima_versao": "Priorizar a feature que mais aumenta retenção antes de escalar aquisição.",
            "regra": "Não escalar aquisição sem fundador usando e percebendo valor.",
        },
    }
    CAMINHO_MANIFESTO_RETENCAO.write_text(json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifesto


def _injetar_css_retencao() -> None:
    st.markdown(
        """
        <style>
            .retencao-hero {
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
            .retencao-eyebrow {
                color: #d6b56d;
                font-size: 0.74rem;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                font-weight: 880;
                margin-bottom: 0.35rem;
            }
            .retencao-title {
                color: #f4f7fb;
                font-size: clamp(1.8rem, 5.5vw, 3.25rem);
                font-weight: 950;
                line-height: 1.02;
                letter-spacing: -0.058em;
                margin-bottom: 0.55rem;
            }
            .retencao-subtitle {
                color: rgba(244, 247, 251, 0.75);
                font-size: clamp(0.94rem, 2.2vw, 1.06rem);
                line-height: 1.56;
                max-width: 1050px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def renderizar_retencao_fundadores_valoris() -> None:
    _injetar_css_retencao()

    st.markdown(
        f"""
        <div class="retencao-hero">
            <div class="retencao-eyebrow">Valoris • Retenção Fundadores • v{VERSAO_RETENCAO_FUNDADORES_VALORIS}</div>
            <div class="retencao-title">Receita sem retenção não prova produto.</div>
            <div class="retencao-subtitle">
                Meça primeiro acesso, primeira análise, relatório exportado, feedback pós-pagamento,
                valor percebido e risco de cancelamento dos fundadores.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    saude = calcular_saude_retencao_fundadores()

    st.markdown("### Diagnóstico de retenção")
    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Score Retenção", f"{saude['score_retencao']}/100")

    with col_2:
        st.metric("Fundadores ativos", saude["fundadores_ativos"])

    with col_3:
        st.metric("Feedbacks pagantes", saude["feedbacks_pos_pagamento_total"])

    with col_4:
        st.metric("MRR", f"R$ {saude['mrr_estimado']}")

    st.progress(saude["score_retencao"] / 100)

    if saude["score_retencao"] >= 82 and saude["feedbacks_pos_pagamento_total"] >= 1:
        st.success(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    elif saude["fundadores_ativos"] >= 1:
        st.warning(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    else:
        st.info(f"**{saude['decisao']}** — {saude['proximo_passo']}")

    st.divider()

    st.markdown("### Marcos de retenção")
    st.dataframe(MARCOS_RETENCAO, width="stretch", hide_index=True)

    st.markdown("### Playbook de acompanhamento")
    st.dataframe(PLAYBOOK_RETENCAO, width="stretch", hide_index=True)

    st.divider()

    st.markdown("### Registrar ativação do fundador")

    fundadores = carregar_fundadores_valoris()
    emails = [item.get("email", "") for item in fundadores if item.get("email")]
    emails_unicos = list(dict.fromkeys(emails))

    with st.form("form_ativacao_fundador"):
        col_a, col_b = st.columns(2)

        with col_a:
            fundador_email = st.selectbox("Fundador", emails_unicos or ["fundador@exemplo.com"])
            fundador_ref = next((item for item in fundadores if item.get("email") == fundador_email), {})
            fundador_nome = st.text_input("Nome", value=fundador_ref.get("nome", ""))
            plano = st.text_input("Plano", value=fundador_ref.get("plano", "Beta Fundador Pro"))
            primeiro_acesso = st.checkbox("Primeiro acesso concluído", value=True)
            primeira_analise = st.checkbox("Primeira análise concluída", value=True)
            relatorio_exportado = st.checkbox("Relatório exportado", value=True)
            feedback_enviado = st.checkbox("Feedback enviado", value=True)

        with col_b:
            valor_percebido = st.slider("Valor percebido", min_value=0, max_value=10, value=8)
            risco_cancelamento = st.selectbox("Risco de cancelamento", ["Baixo", "Médio", "Alto"])
            proximo_contato = st.date_input("Próximo contato", value=datetime.now().date() + timedelta(days=7))
            status_sucesso = st.selectbox("Status de sucesso", ["ativado", "em_acompanhamento", "travado", "risco_churn"])
            duvida_principal = st.text_area("Dúvida principal", height=80)
            observacoes = st.text_area("Observações", height=80)

        enviado = st.form_submit_button("Salvar ativação")

        if enviado:
            registro = salvar_ativacao_fundador(
                {
                    "fundador_email": fundador_email,
                    "fundador_nome": fundador_nome,
                    "plano": plano,
                    "primeiro_acesso": primeiro_acesso,
                    "primeira_analise": primeira_analise,
                    "relatorio_exportado": relatorio_exportado,
                    "feedback_enviado": feedback_enviado,
                    "duvida_principal": duvida_principal,
                    "valor_percebido": valor_percebido,
                    "risco_cancelamento": risco_cancelamento,
                    "proximo_contato": str(proximo_contato),
                    "status_sucesso": status_sucesso,
                    "observacoes": observacoes,
                }
            )
            st.success(f"Ativação salva: {registro['id']}")
            st.rerun()

    st.markdown("### Registrar feedback pós-pagamento")

    with st.form("form_feedback_pos_pagamento"):
        col_c, col_d = st.columns(2)

        with col_c:
            fundador_email_fb = st.selectbox("Fundador do feedback", emails_unicos or ["fundador@exemplo.com"], key="fundador_feedback")
            fundador_ref_fb = next((item for item in fundadores if item.get("email") == fundador_email_fb), {})
            fundador_nome_fb = st.text_input("Nome do fundador", value=fundador_ref_fb.get("nome", ""), key="nome_feedback")
            clareza_valor = st.slider("Clareza do valor", 0, 10, 9)
            utilidade_real = st.slider("Utilidade real", 0, 10, 8)
            confianca = st.slider("Confiança", 0, 10, 8)
            facilidade_uso = st.slider("Facilidade de uso", 0, 10, 8)
            chance_continuar = st.slider("Chance de continuar", 0, 10, 8)
            pagaria_novamente = st.checkbox("Pagaria novamente?", value=True)

        with col_d:
            principal_valor = st.text_area("Principal valor percebido", height=80)
            principal_friccao = st.text_area("Principal fricção", height=80)
            feature_necessaria = st.text_area("Feature necessária para continuar", height=80)
            observacoes_fb = st.text_area("Observações do feedback", height=80)

        enviado_feedback = st.form_submit_button("Salvar feedback pós-pagamento")

        if enviado_feedback:
            registro = salvar_feedback_pos_pagamento(
                {
                    "fundador_email": fundador_email_fb,
                    "fundador_nome": fundador_nome_fb,
                    "clareza_valor": clareza_valor,
                    "utilidade_real": utilidade_real,
                    "confianca": confianca,
                    "facilidade_uso": facilidade_uso,
                    "chance_continuar": chance_continuar,
                    "principal_valor": principal_valor,
                    "principal_friccao": principal_friccao,
                    "feature_necessaria": feature_necessaria,
                    "pagaria_novamente": pagaria_novamente,
                    "observacoes": observacoes_fb,
                }
            )
            st.success(f"Feedback pós-pagamento salvo: {registro['id']}")
            st.rerun()

    st.divider()

    st.markdown("### Métricas de retenção")
    st.json(saude["metricas_retencao"])

    if saude["metricas_retencao"]["ultimas_ativacoes"]:
        st.markdown("#### Últimas ativações")
        st.dataframe(saude["metricas_retencao"]["ultimas_ativacoes"], width="stretch", hide_index=True)

    if saude["metricas_retencao"]["ultimos_feedbacks"]:
        st.markdown("#### Últimos feedbacks pós-pagamento")
        st.dataframe(saude["metricas_retencao"]["ultimos_feedbacks"], width="stretch", hide_index=True)

    st.divider()

    col_btn_1, col_btn_2, col_btn_3, col_btn_4 = st.columns(4)

    with col_btn_1:
        if st.button("Gerar ativação exemplo", key="retencao_ativacao_exemplo"):
            registro = gerar_ativacao_exemplo()
            st.success(f"Ativação exemplo criada: {registro['id']}")
            st.rerun()

    with col_btn_2:
        if st.button("Gerar feedback exemplo", key="retencao_feedback_exemplo"):
            registro = gerar_feedback_pos_pagamento_exemplo()
            st.success(f"Feedback exemplo criado: {registro['id']}")
            st.rerun()

    with col_btn_3:
        if st.button("Gerar manifesto", key="retencao_manifesto"):
            manifesto = gerar_manifesto_retencao_fundadores()
            st.success(f"Manifesto gerado: {CAMINHO_MANIFESTO_RETENCAO}")
            st.json({"versao": manifesto["versao"], "score": manifesto["saude"]["score_retencao"]})

    with col_btn_4:
        if st.button("Salvar relatório .md", key="retencao_relatorio"):
            retorno = salvar_relatorio_retencao_markdown()
            st.success(f"Relatório salvo: {retorno['arquivo']}")
            st.json(retorno)

    col_btn_5, col_btn_6 = st.columns(2)

    with col_btn_5:
        if st.button("Salvar playbook .md", key="retencao_playbook"):
            retorno = salvar_playbook_retencao_markdown()
            st.success(f"Playbook salvo: {retorno['arquivo']}")
            st.json(retorno)

    with col_btn_6:
        if st.button("Salvar checklist .md", key="retencao_checklist"):
            retorno = salvar_checklist_retencao_markdown()
            st.success(f"Checklist salvo: {retorno['arquivo']}")
            st.json(retorno)

    if st.button("Salvar decisão Retenção", key="retencao_decisao"):
        registro = salvar_decisao_retencao_fundadores(saude, observacoes="Decisão gerada pela retenção de fundadores.")
        st.success(f"Decisão salva: {registro['decisao']}")
        st.rerun()

    st.download_button(
        "Baixar relatório retenção (.md)",
        data=gerar_relatorio_retencao_markdown(saude),
        file_name="RELATORIO_RETENCAO_FUNDADORES_VALORIS.md",
        mime="text/markdown",
        key="download_relatorio_retencao",
    )

    st.download_button(
        "Baixar ativações (.csv)",
        data=gerar_csv_ativacoes_fundadores(),
        file_name="ativacoes_fundadores_valoris.csv",
        mime="text/csv",
        key="download_ativacoes_fundadores",
    )

    st.download_button(
        "Baixar feedbacks pós-pagamento (.csv)",
        data=gerar_csv_feedbacks_pos_pagamento(),
        file_name="feedbacks_pos_pagamento_valoris.csv",
        mime="text/csv",
        key="download_feedbacks_pos_pagamento",
    )


def executar_autoteste_retencao_fundadores_valoris() -> List[Dict[str, str]]:
    saude = calcular_saude_retencao_fundadores()

    return [
        {
            "teste": "versao_retencao_fundadores",
            "status": "OK" if VERSAO_RETENCAO_FUNDADORES_VALORIS == "3.8.84" else "FALHA",
            "detalhe": VERSAO_RETENCAO_FUNDADORES_VALORIS,
        },
        {
            "teste": "score_retencao",
            "status": "OK" if 0 <= saude["score_retencao"] <= 100 else "FALHA",
            "detalhe": str(saude["score_retencao"]),
        },
        {
            "teste": "playbook",
            "status": "OK" if len(PLAYBOOK_RETENCAO) >= 5 else "FALHA",
            "detalhe": str(len(PLAYBOOK_RETENCAO)),
        },
        {
            "teste": "renderizador",
            "status": "OK" if callable(renderizar_retencao_fundadores_valoris) else "FALHA",
            "detalhe": "renderizar_retencao_fundadores_valoris",
        },
    ]
