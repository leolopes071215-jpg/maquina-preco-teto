# watchlist_fundadores_valoris.py

from __future__ import annotations

import csv
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

import streamlit as st


VERSAO_WATCHLIST_FUNDADORES_VALORIS = "3.8.85"

CAMINHO_WATCHLIST_FUNDADORES = Path("watchlist_fundadores_valoris.csv")
CAMINHO_ALERTAS_WATCHLIST = Path("alertas_watchlist_fundadores_valoris.csv")
CAMINHO_DECISOES_WATCHLIST = Path("decisoes_watchlist_fundadores_valoris.csv")
CAMINHO_MANIFESTO_WATCHLIST = Path("manifesto_watchlist_fundadores_valoris.json")
CAMINHO_RELATORIO_WATCHLIST_MD = Path("RELATORIO_WATCHLIST_FUNDADORES_VALORIS.md")
CAMINHO_PLAYBOOK_WATCHLIST_MD = Path("PLAYBOOK_WATCHLIST_FUNDADORES_VALORIS.md")
CAMINHO_CHECKLIST_WATCHLIST_MD = Path("CHECKLIST_WATCHLIST_FUNDADORES_VALORIS.md")

CAMPOS_WATCHLIST = [
    "id",
    "data_registro",
    "fundador_email",
    "empresa",
    "ticker",
    "setor",
    "preco_atual",
    "preco_teto",
    "margem_seguranca",
    "status_oportunidade",
    "prioridade",
    "tese_resumo",
    "principal_risco",
    "proximo_evento",
    "data_revisao",
    "observacoes",
]

CAMPOS_ALERTAS_WATCHLIST = [
    "id",
    "data_registro",
    "watchlist_id",
    "ticker",
    "tipo_alerta",
    "mensagem",
    "criticidade",
    "status",
    "data_alvo",
    "observacoes",
]

CAMPOS_DECISAO_WATCHLIST = [
    "id",
    "data_registro",
    "score_watchlist",
    "score_cobertura",
    "score_oportunidade",
    "score_alertas",
    "score_retencao",
    "ativos_total",
    "alertas_total",
    "oportunidades_compra",
    "ativos_revisar",
    "risco",
    "decisao",
    "proximo_passo",
    "observacoes",
]

STATUS_OPORTUNIDADE = [
    "Abaixo do preço teto",
    "Próximo do preço teto",
    "Acima do preço teto",
    "Revisar premissas",
    "Evitar por enquanto",
]

PRIORIDADES = ["Alta", "Média", "Baixa"]

TIPOS_ALERTA = [
    "Preço chegou no teto",
    "Margem de segurança aumentou",
    "Margem de segurança sumiu",
    "Revisar tese",
    "Revisar resultado trimestral",
    "Risco relevante",
]

PLAYBOOK_WATCHLIST = [
    {
        "etapa": "Registrar ativo",
        "objetivo": "Transformar uma análise pontual em acompanhamento contínuo.",
        "acao": "Adicionar empresa, ticker, preço atual, preço teto, margem e tese resumida.",
        "sinal_sucesso": "Fundador tem pelo menos uma empresa monitorada.",
    },
    {
        "etapa": "Classificar oportunidade",
        "objetivo": "Separar oportunidade real de ativo apenas interessante.",
        "acao": "Classificar se está abaixo, próximo ou acima do preço teto.",
        "sinal_sucesso": "Fundador sabe o que acompanhar primeiro.",
    },
    {
        "etapa": "Criar alerta manual",
        "objetivo": "Evitar que o fundador precise refazer a análise toda semana.",
        "acao": "Criar alerta para revisão de preço, tese, resultado ou risco.",
        "sinal_sucesso": "Há próximo evento claro para cada tese importante.",
    },
    {
        "etapa": "Revisar tese",
        "objetivo": "Manter a análise viva e não congelada no tempo.",
        "acao": "Atualizar tese, risco e preço teto após resultados ou mudança de premissa.",
        "sinal_sucesso": "Watchlist vira rotina de acompanhamento.",
    },
    {
        "etapa": "Medir retenção",
        "objetivo": "Usar watchlist como recurso de recorrência.",
        "acao": "Observar se fundadores voltam para revisar ativos e alertas.",
        "sinal_sucesso": "Uso recorrente aumenta e risco de churn cai.",
    },
]

CHECKLIST_WATCHLIST = [
    "Ativo registrado com ticker e empresa",
    "Preço atual informado",
    "Preço teto informado",
    "Margem de segurança calculada",
    "Status da oportunidade definido",
    "Tese resumida registrada",
    "Principal risco registrado",
    "Data de revisão definida",
    "Alerta manual criado",
    "Relatório de watchlist gerado",
]


def _limpar_texto(valor: Any) -> str:
    if valor is None:
        return ""
    return str(valor).strip()


def _to_float(valor: Any, padrao: float = 0.0) -> float:
    try:
        if isinstance(valor, str):
            valor = valor.replace("R$", "").replace(".", "").replace(",", ".").replace("%", "").strip()
        return float(valor)
    except Exception:
        return padrao


def _garantir_csv(caminho: Path, campos: List[str]) -> None:
    if caminho.exists():
        return

    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()


def _calcular_margem(preco_atual: float, preco_teto: float) -> float:
    if preco_atual <= 0:
        return 0.0
    return round(((preco_teto - preco_atual) / preco_atual) * 100, 2)


def _classificar_status(preco_atual: float, preco_teto: float) -> str:
    if preco_atual <= 0 or preco_teto <= 0:
        return "Revisar premissas"

    margem = _calcular_margem(preco_atual, preco_teto)

    if margem >= 15:
        return "Abaixo do preço teto"

    if -5 <= margem < 15:
        return "Próximo do preço teto"

    if margem < -5:
        return "Acima do preço teto"

    return "Revisar premissas"


def carregar_watchlist_fundadores() -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_WATCHLIST_FUNDADORES, CAMPOS_WATCHLIST)

    with CAMINHO_WATCHLIST_FUNDADORES.open("r", newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def carregar_alertas_watchlist() -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_ALERTAS_WATCHLIST, CAMPOS_ALERTAS_WATCHLIST)

    with CAMINHO_ALERTAS_WATCHLIST.open("r", newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def carregar_decisoes_watchlist() -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_DECISOES_WATCHLIST, CAMPOS_DECISAO_WATCHLIST)

    with CAMINHO_DECISOES_WATCHLIST.open("r", newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def gerar_csv_watchlist_fundadores() -> str:
    _garantir_csv(CAMINHO_WATCHLIST_FUNDADORES, CAMPOS_WATCHLIST)
    return CAMINHO_WATCHLIST_FUNDADORES.read_text(encoding="utf-8")


def gerar_csv_alertas_watchlist() -> str:
    _garantir_csv(CAMINHO_ALERTAS_WATCHLIST, CAMPOS_ALERTAS_WATCHLIST)
    return CAMINHO_ALERTAS_WATCHLIST.read_text(encoding="utf-8")


def gerar_csv_decisoes_watchlist() -> str:
    _garantir_csv(CAMINHO_DECISOES_WATCHLIST, CAMPOS_DECISAO_WATCHLIST)
    return CAMINHO_DECISOES_WATCHLIST.read_text(encoding="utf-8")


def salvar_item_watchlist(dados: Dict[str, Any]) -> Dict[str, str]:
    _garantir_csv(CAMINHO_WATCHLIST_FUNDADORES, CAMPOS_WATCHLIST)

    preco_atual = _to_float(dados.get("preco_atual"), 0.0)
    preco_teto = _to_float(dados.get("preco_teto"), 0.0)
    margem = _calcular_margem(preco_atual, preco_teto)

    status = _limpar_texto(dados.get("status_oportunidade"))
    if not status:
        status = _classificar_status(preco_atual, preco_teto)

    registro = {
        "id": str(uuid4())[:8],
        "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "fundador_email": _limpar_texto(dados.get("fundador_email")).lower(),
        "empresa": _limpar_texto(dados.get("empresa")),
        "ticker": _limpar_texto(dados.get("ticker")).upper(),
        "setor": _limpar_texto(dados.get("setor")),
        "preco_atual": str(preco_atual),
        "preco_teto": str(preco_teto),
        "margem_seguranca": str(margem),
        "status_oportunidade": status,
        "prioridade": _limpar_texto(dados.get("prioridade", "Média")),
        "tese_resumo": _limpar_texto(dados.get("tese_resumo")),
        "principal_risco": _limpar_texto(dados.get("principal_risco")),
        "proximo_evento": _limpar_texto(dados.get("proximo_evento")),
        "data_revisao": _limpar_texto(dados.get("data_revisao")),
        "observacoes": _limpar_texto(dados.get("observacoes")),
    }

    with CAMINHO_WATCHLIST_FUNDADORES.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_WATCHLIST)
        escritor.writerow(registro)

    return registro


def salvar_alerta_watchlist(dados: Dict[str, Any]) -> Dict[str, str]:
    _garantir_csv(CAMINHO_ALERTAS_WATCHLIST, CAMPOS_ALERTAS_WATCHLIST)

    registro = {
        "id": str(uuid4())[:8],
        "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "watchlist_id": _limpar_texto(dados.get("watchlist_id")),
        "ticker": _limpar_texto(dados.get("ticker")).upper(),
        "tipo_alerta": _limpar_texto(dados.get("tipo_alerta")),
        "mensagem": _limpar_texto(dados.get("mensagem")),
        "criticidade": _limpar_texto(dados.get("criticidade", "Média")),
        "status": _limpar_texto(dados.get("status", "Aberto")),
        "data_alvo": _limpar_texto(dados.get("data_alvo")),
        "observacoes": _limpar_texto(dados.get("observacoes")),
    }

    with CAMINHO_ALERTAS_WATCHLIST.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_ALERTAS_WATCHLIST)
        escritor.writerow(registro)

    return registro


def gerar_item_watchlist_exemplo() -> Dict[str, str]:
    return salvar_item_watchlist(
        {
            "fundador_email": "fundador@exemplo.com",
            "empresa": "Mastercard",
            "ticker": "MA",
            "setor": "Pagamentos",
            "preco_atual": 450,
            "preco_teto": 520,
            "prioridade": "Alta",
            "tese_resumo": "Empresa de alta qualidade, rede forte e geração de caixa elevada.",
            "principal_risco": "Valuation exigente e compressão de múltiplos.",
            "proximo_evento": "Próximo resultado trimestral",
            "data_revisao": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            "observacoes": "Exemplo para testar watchlist de fundadores.",
        }
    )


def gerar_alerta_watchlist_exemplo() -> Dict[str, str]:
    itens = carregar_watchlist_fundadores()
    item = itens[-1] if itens else gerar_item_watchlist_exemplo()

    return salvar_alerta_watchlist(
        {
            "watchlist_id": item.get("id", ""),
            "ticker": item.get("ticker", "MA"),
            "tipo_alerta": "Revisar resultado trimestral",
            "mensagem": f"Revisar tese de {item.get('ticker', 'MA')} após resultado e atualizar preço teto.",
            "criticidade": "Alta",
            "status": "Aberto",
            "data_alvo": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            "observacoes": "Alerta exemplo para validar recorrência.",
        }
    )


def calcular_metricas_watchlist() -> Dict[str, Any]:
    itens = carregar_watchlist_fundadores()
    alertas = carregar_alertas_watchlist()

    ativos_total = len(itens)
    alertas_total = len(alertas)

    oportunidades_compra = [
        item for item in itens
        if item.get("status_oportunidade") == "Abaixo do preço teto"
    ]

    ativos_proximos = [
        item for item in itens
        if item.get("status_oportunidade") == "Próximo do preço teto"
    ]

    ativos_revisar = [
        item for item in itens
        if item.get("status_oportunidade") in {"Revisar premissas", "Evitar por enquanto"}
    ]

    alta_prioridade = [
        item for item in itens
        if item.get("prioridade") == "Alta"
    ]

    alertas_abertos = [
        alerta for alerta in alertas
        if alerta.get("status") == "Aberto"
    ]

    margens = [_to_float(item.get("margem_seguranca"), 0.0) for item in itens]
    margem_media = round(sum(margens) / len(margens), 2) if margens else 0.0

    setores: Dict[str, int] = {}
    for item in itens:
        setor = item.get("setor", "não informado")
        setores[setor] = setores.get(setor, 0) + 1

    return {
        "ativos_total": ativos_total,
        "alertas_total": alertas_total,
        "alertas_abertos": len(alertas_abertos),
        "oportunidades_compra": len(oportunidades_compra),
        "ativos_proximos": len(ativos_proximos),
        "ativos_revisar": len(ativos_revisar),
        "alta_prioridade": len(alta_prioridade),
        "margem_media": margem_media,
        "setores": setores,
        "ultimos_itens": itens[-25:],
        "ultimos_alertas": alertas[-25:],
    }


def _calcular_saude_modulo(nome_modulo: str, nome_funcao: str) -> Dict[str, Any]:
    try:
        modulo = __import__(nome_modulo, fromlist=[nome_funcao])
        funcao = getattr(modulo, nome_funcao)
        return funcao()
    except Exception as erro:
        return {"erro": str(erro)}


def calcular_saude_watchlist_fundadores() -> Dict[str, Any]:
    metricas = calcular_metricas_watchlist()

    retencao = _calcular_saude_modulo("retencao_fundadores_valoris", "calcular_saude_retencao_fundadores")
    checkout = _calcular_saude_modulo("checkout_fundadores_valoris", "calcular_saude_checkout_fundadores")
    oferta = _calcular_saude_modulo("oferta_beta_fundador_valoris", "calcular_saude_oferta_beta_fundador")
    premium = _calcular_saude_modulo("analise_premium_valoris", "calcular_saude_analise_premium")

    score_cobertura = 0
    score_cobertura += 25 if metricas["ativos_total"] >= 1 else 0
    score_cobertura += 20 if metricas["ativos_total"] >= 3 else 0
    score_cobertura += 15 if len(metricas["setores"]) >= 2 else 0
    score_cobertura += 20 if metricas["alta_prioridade"] >= 1 else 0
    score_cobertura += 20 if metricas["alertas_total"] >= 1 else 0
    score_cobertura = min(100, score_cobertura)

    score_oportunidade = 0
    score_oportunidade += 30 if metricas["oportunidades_compra"] >= 1 else 0
    score_oportunidade += 20 if metricas["ativos_proximos"] >= 1 else 0
    score_oportunidade += 20 if metricas["margem_media"] >= 5 else 0
    score_oportunidade += 15 if metricas["ativos_revisar"] == 0 and metricas["ativos_total"] > 0 else 0
    score_oportunidade += 15 if metricas["alta_prioridade"] >= 1 else 0
    score_oportunidade = min(100, score_oportunidade)

    score_alertas = 0
    score_alertas += 30 if metricas["alertas_total"] >= 1 else 0
    score_alertas += 25 if metricas["alertas_abertos"] >= 1 else 0
    score_alertas += 20 if metricas["alertas_total"] >= metricas["ativos_total"] and metricas["ativos_total"] > 0 else 0
    score_alertas += 15 if len(PLAYBOOK_WATCHLIST) >= 5 else 0
    score_alertas += 10 if len(CHECKLIST_WATCHLIST) >= 10 else 0
    score_alertas = min(100, score_alertas)

    score_retencao = int(retencao.get("score_retencao", 0) or 0)
    score_checkout = int(checkout.get("score_checkout", 0) or 0)
    score_oferta = int(oferta.get("score_oferta", 0) or 0)
    score_premium = int(premium.get("score_produto_premium", 0) or 0)

    score_base_produto = int(round(
        score_retencao * 0.32
        + score_checkout * 0.24
        + score_oferta * 0.18
        + score_premium * 0.26
    ))

    score_watchlist = int(round(
        score_cobertura * 0.28
        + score_oportunidade * 0.24
        + score_alertas * 0.22
        + score_base_produto * 0.26
    ))

    if metricas["ativos_total"] >= 3 and metricas["alertas_total"] >= 3 and score_watchlist >= 82:
        risco = "Médio controlado"
        decisao = "Watchlist pronta para testar recorrência com fundadores"
        proximo_passo = "Usar a watchlist como rotina semanal de acompanhamento e medir retorno ao app."
    elif metricas["ativos_total"] >= 1 and metricas["alertas_total"] >= 1:
        risco = "Médio"
        decisao = "Watchlist funcional, mas ainda precisa de mais cobertura"
        proximo_passo = "Registrar mais ativos e criar alertas para cada tese importante."
    elif metricas["ativos_total"] >= 1:
        risco = "Médio/Alto"
        decisao = "Ativos registrados, mas sem rotina de alerta suficiente"
        proximo_passo = "Criar alertas manuais para transformar análise em acompanhamento."
    else:
        risco = "Alto"
        decisao = "Watchlist ainda não validada"
        proximo_passo = "Registrar pelo menos uma empresa acompanhada por fundador."

    return {
        "versao": VERSAO_WATCHLIST_FUNDADORES_VALORIS,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score_watchlist": max(0, min(100, score_watchlist)),
        "score_cobertura": score_cobertura,
        "score_oportunidade": score_oportunidade,
        "score_alertas": score_alertas,
        "score_retencao": score_retencao,
        "score_base_produto": score_base_produto,
        "ativos_total": metricas["ativos_total"],
        "alertas_total": metricas["alertas_total"],
        "oportunidades_compra": metricas["oportunidades_compra"],
        "ativos_revisar": metricas["ativos_revisar"],
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo_passo,
        "metricas_watchlist": metricas,
        "playbook": PLAYBOOK_WATCHLIST,
        "checklist": CHECKLIST_WATCHLIST,
        "retencao": retencao,
        "checkout": checkout,
        "oferta": oferta,
        "premium": premium,
    }


def salvar_decisao_watchlist(saude: Dict[str, Any], observacoes: str = "") -> Dict[str, str]:
    _garantir_csv(CAMINHO_DECISOES_WATCHLIST, CAMPOS_DECISAO_WATCHLIST)

    registro = {
        "id": str(uuid4())[:8],
        "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score_watchlist": str(saude.get("score_watchlist", "")),
        "score_cobertura": str(saude.get("score_cobertura", "")),
        "score_oportunidade": str(saude.get("score_oportunidade", "")),
        "score_alertas": str(saude.get("score_alertas", "")),
        "score_retencao": str(saude.get("score_retencao", "")),
        "ativos_total": str(saude.get("ativos_total", "")),
        "alertas_total": str(saude.get("alertas_total", "")),
        "oportunidades_compra": str(saude.get("oportunidades_compra", "")),
        "ativos_revisar": str(saude.get("ativos_revisar", "")),
        "risco": _limpar_texto(saude.get("risco")),
        "decisao": _limpar_texto(saude.get("decisao")),
        "proximo_passo": _limpar_texto(saude.get("proximo_passo")),
        "observacoes": _limpar_texto(observacoes),
    }

    with CAMINHO_DECISOES_WATCHLIST.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISAO_WATCHLIST)
        escritor.writerow(registro)

    return registro


def gerar_relatorio_watchlist_markdown(saude: Dict[str, Any] | None = None) -> str:
    if saude is None:
        saude = calcular_saude_watchlist_fundadores()

    itens = carregar_watchlist_fundadores()
    alertas = carregar_alertas_watchlist()

    tabela_itens = "\n".join(
        [
            f"- **{item['ticker']} — {item['empresa']}**: preço atual R$ {item['preco_atual']}, teto R$ {item['preco_teto']}, margem {item['margem_seguranca']}%, status: {item['status_oportunidade']}, prioridade: {item['prioridade']}."
            for item in itens[-20:]
        ]
    ) or "- Nenhum ativo registrado."

    tabela_alertas = "\n".join(
        [
            f"- **{alerta['ticker']}**: {alerta['tipo_alerta']} — {alerta['mensagem']} ({alerta['criticidade']}, {alerta['status']})."
            for alerta in alertas[-20:]
        ]
    ) or "- Nenhum alerta registrado."

    return f"""# Relatório Watchlist de Fundadores — Valoris

Versão: {VERSAO_WATCHLIST_FUNDADORES_VALORIS}  
Gerado em: {saude["gerado_em"]}

## Resumo executivo

Score Watchlist: {saude["score_watchlist"]}/100  
Ativos monitorados: {saude["ativos_total"]}  
Alertas: {saude["alertas_total"]}  
Oportunidades abaixo do preço teto: {saude["oportunidades_compra"]}  
Decisão: {saude["decisao"]}  
Próximo passo: {saude["proximo_passo"]}

## Ativos acompanhados

{tabela_itens}

## Alertas

{tabela_alertas}

## Leitura

A watchlist transforma uma análise isolada em rotina. Esse é um dos caminhos mais fortes para retenção porque cria motivo para o fundador voltar.
"""


def gerar_playbook_watchlist_markdown(saude: Dict[str, Any] | None = None) -> str:
    if saude is None:
        saude = calcular_saude_watchlist_fundadores()

    etapas = "\n\n".join(
        [
            f"""## {item['etapa']}

**Objetivo:** {item['objetivo']}  
**Ação:** {item['acao']}  
**Sinal de sucesso:** {item['sinal_sucesso']}
"""
            for item in PLAYBOOK_WATCHLIST
        ]
    )

    return f"""# Playbook Watchlist de Fundadores — Valoris

Versão: {VERSAO_WATCHLIST_FUNDADORES_VALORIS}  
Gerado em: {saude["gerado_em"]}

## Princípio

O produto deixa de ser uma calculadora quando ajuda o usuário a acompanhar uma tese ao longo do tempo.

## Etapas

{etapas}
"""


def gerar_checklist_watchlist_markdown(saude: Dict[str, Any] | None = None) -> str:
    if saude is None:
        saude = calcular_saude_watchlist_fundadores()

    checklist = "\n".join([f"- [x] {item}" for item in CHECKLIST_WATCHLIST])

    return f"""# Checklist Watchlist de Fundadores — Valoris

Versão: {VERSAO_WATCHLIST_FUNDADORES_VALORIS}  
Gerado em: {saude["gerado_em"]}

## Status

Score Watchlist: {saude["score_watchlist"]}/100  
Decisão: {saude["decisao"]}

## Checklist

{checklist}
"""


def salvar_relatorio_watchlist_markdown() -> Dict[str, Any]:
    saude = calcular_saude_watchlist_fundadores()
    CAMINHO_RELATORIO_WATCHLIST_MD.write_text(gerar_relatorio_watchlist_markdown(saude), encoding="utf-8")
    return {"ok": True, "arquivo": str(CAMINHO_RELATORIO_WATCHLIST_MD), "score_watchlist": saude["score_watchlist"]}


def salvar_playbook_watchlist_markdown() -> Dict[str, Any]:
    saude = calcular_saude_watchlist_fundadores()
    CAMINHO_PLAYBOOK_WATCHLIST_MD.write_text(gerar_playbook_watchlist_markdown(saude), encoding="utf-8")
    return {"ok": True, "arquivo": str(CAMINHO_PLAYBOOK_WATCHLIST_MD), "score_watchlist": saude["score_watchlist"]}


def salvar_checklist_watchlist_markdown() -> Dict[str, Any]:
    saude = calcular_saude_watchlist_fundadores()
    CAMINHO_CHECKLIST_WATCHLIST_MD.write_text(gerar_checklist_watchlist_markdown(saude), encoding="utf-8")
    return {"ok": True, "arquivo": str(CAMINHO_CHECKLIST_WATCHLIST_MD), "score_watchlist": saude["score_watchlist"]}


def gerar_manifesto_watchlist() -> Dict[str, Any]:
    saude = calcular_saude_watchlist_fundadores()
    manifesto = {
        "versao": VERSAO_WATCHLIST_FUNDADORES_VALORIS,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "saude": saude,
        "playbook": PLAYBOOK_WATCHLIST,
        "checklist": CHECKLIST_WATCHLIST,
        "estrategia": {
            "objetivo": "Transformar análise premium em acompanhamento recorrente.",
            "proxima_versao": "Comparador setorial ou relatório premium v2 com base nos ativos da watchlist.",
            "regra": "Retenção aumenta quando o usuário volta para revisar tese e oportunidade.",
        },
    }

    CAMINHO_MANIFESTO_WATCHLIST.write_text(json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifesto


def _injetar_css_watchlist() -> None:
    st.markdown(
        """
        <style>
            .watchlist-hero {
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
            .watchlist-eyebrow {
                color: #d6b56d;
                font-size: 0.74rem;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                font-weight: 880;
                margin-bottom: 0.35rem;
            }
            .watchlist-title {
                color: #f4f7fb;
                font-size: clamp(1.8rem, 5.5vw, 3.25rem);
                font-weight: 950;
                line-height: 1.02;
                letter-spacing: -0.058em;
                margin-bottom: 0.55rem;
            }
            .watchlist-subtitle {
                color: rgba(244, 247, 251, 0.75);
                font-size: clamp(0.94rem, 2.2vw, 1.06rem);
                line-height: 1.56;
                max-width: 1050px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def renderizar_watchlist_fundadores_valoris() -> None:
    _injetar_css_watchlist()

    st.markdown(
        f"""
        <div class="watchlist-hero">
            <div class="watchlist-eyebrow">Valoris • Watchlist Fundadores • v{VERSAO_WATCHLIST_FUNDADORES_VALORIS}</div>
            <div class="watchlist-title">Da análise pontual ao acompanhamento recorrente.</div>
            <div class="watchlist-subtitle">
                Registre empresas, preço teto, margem de segurança, tese, risco e alertas manuais para criar rotina de uso.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    saude = calcular_saude_watchlist_fundadores()

    st.markdown("### Diagnóstico da watchlist")
    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Score Watchlist", f"{saude['score_watchlist']}/100")

    with col_2:
        st.metric("Ativos", saude["ativos_total"])

    with col_3:
        st.metric("Alertas", saude["alertas_total"])

    with col_4:
        st.metric("Oportunidades", saude["oportunidades_compra"])

    st.progress(saude["score_watchlist"] / 100)

    if saude["score_watchlist"] >= 82:
        st.success(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    elif saude["ativos_total"] >= 1:
        st.warning(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    else:
        st.info(f"**{saude['decisao']}** — {saude['proximo_passo']}")

    st.divider()

    st.markdown("### Registrar ativo na watchlist")
    with st.form("form_watchlist_fundadores"):
        col_a, col_b = st.columns(2)

        with col_a:
            fundador_email = st.text_input("E-mail do fundador", value="fundador@exemplo.com")
            empresa = st.text_input("Empresa", value="Mastercard")
            ticker = st.text_input("Ticker", value="MA")
            setor = st.text_input("Setor", value="Pagamentos")
            preco_atual = st.number_input("Preço atual", min_value=0.0, value=450.0, step=1.0)
            preco_teto = st.number_input("Preço teto", min_value=0.0, value=520.0, step=1.0)

        with col_b:
            prioridade = st.selectbox("Prioridade", PRIORIDADES)
            status_oportunidade = st.selectbox("Status da oportunidade", ["Automático"] + STATUS_OPORTUNIDADE)
            tese_resumo = st.text_area("Tese resumida", height=90)
            principal_risco = st.text_area("Principal risco", height=90)
            proximo_evento = st.text_input("Próximo evento", value="Próximo resultado trimestral")
            data_revisao = st.date_input("Data de revisão", value=datetime.now().date() + timedelta(days=30))
            observacoes = st.text_area("Observações", height=80)

        enviado = st.form_submit_button("Salvar ativo")

        if enviado:
            registro = salvar_item_watchlist(
                {
                    "fundador_email": fundador_email,
                    "empresa": empresa,
                    "ticker": ticker,
                    "setor": setor,
                    "preco_atual": preco_atual,
                    "preco_teto": preco_teto,
                    "status_oportunidade": "" if status_oportunidade == "Automático" else status_oportunidade,
                    "prioridade": prioridade,
                    "tese_resumo": tese_resumo,
                    "principal_risco": principal_risco,
                    "proximo_evento": proximo_evento,
                    "data_revisao": str(data_revisao),
                    "observacoes": observacoes,
                }
            )
            st.success(f"Ativo salvo: {registro['ticker']} — {registro['status_oportunidade']}")
            st.rerun()

    st.markdown("### Registrar alerta")
    itens = carregar_watchlist_fundadores()
    opcoes_itens = [f"{item['id']} | {item['ticker']} | {item['empresa']}" for item in itens]

    with st.form("form_alerta_watchlist"):
        col_c, col_d = st.columns(2)

        with col_c:
            item_escolhido = st.selectbox("Ativo", opcoes_itens or ["sem_item | MA | Mastercard"])
            watchlist_id = item_escolhido.split("|")[0].strip() if "|" in item_escolhido else ""
            ticker_alerta = item_escolhido.split("|")[1].strip() if "|" in item_escolhido else "MA"
            tipo_alerta = st.selectbox("Tipo de alerta", TIPOS_ALERTA)
            criticidade = st.selectbox("Criticidade", ["Alta", "Média", "Baixa"])

        with col_d:
            mensagem = st.text_area("Mensagem", value="Revisar tese e preço teto após próximo evento.", height=90)
            status = st.selectbox("Status", ["Aberto", "Em revisão", "Concluído"])
            data_alvo = st.date_input("Data alvo", value=datetime.now().date() + timedelta(days=30), key="data_alvo_alerta")
            observacoes_alerta = st.text_area("Observações do alerta", height=80)

        enviado_alerta = st.form_submit_button("Salvar alerta")

        if enviado_alerta:
            registro = salvar_alerta_watchlist(
                {
                    "watchlist_id": watchlist_id,
                    "ticker": ticker_alerta,
                    "tipo_alerta": tipo_alerta,
                    "mensagem": mensagem,
                    "criticidade": criticidade,
                    "status": status,
                    "data_alvo": str(data_alvo),
                    "observacoes": observacoes_alerta,
                }
            )
            st.success(f"Alerta salvo: {registro['ticker']} — {registro['tipo_alerta']}")
            st.rerun()

    st.divider()

    st.markdown("### Métricas da watchlist")
    st.json(saude["metricas_watchlist"])

    if saude["metricas_watchlist"]["ultimos_itens"]:
        st.markdown("#### Últimos ativos")
        st.dataframe(saude["metricas_watchlist"]["ultimos_itens"], width="stretch", hide_index=True)

    if saude["metricas_watchlist"]["ultimos_alertas"]:
        st.markdown("#### Últimos alertas")
        st.dataframe(saude["metricas_watchlist"]["ultimos_alertas"], width="stretch", hide_index=True)

    st.divider()

    col_btn_1, col_btn_2, col_btn_3, col_btn_4 = st.columns(4)

    with col_btn_1:
        if st.button("Gerar ativo exemplo", key="watchlist_item_exemplo"):
            registro = gerar_item_watchlist_exemplo()
            st.success(f"Ativo exemplo criado: {registro['ticker']}")
            st.rerun()

    with col_btn_2:
        if st.button("Gerar alerta exemplo", key="watchlist_alerta_exemplo"):
            registro = gerar_alerta_watchlist_exemplo()
            st.success(f"Alerta exemplo criado: {registro['ticker']}")
            st.rerun()

    with col_btn_3:
        if st.button("Gerar manifesto", key="watchlist_manifesto"):
            manifesto = gerar_manifesto_watchlist()
            st.success(f"Manifesto gerado: {CAMINHO_MANIFESTO_WATCHLIST}")
            st.json({"versao": manifesto["versao"], "score": manifesto["saude"]["score_watchlist"]})

    with col_btn_4:
        if st.button("Salvar relatório .md", key="watchlist_relatorio"):
            retorno = salvar_relatorio_watchlist_markdown()
            st.success(f"Relatório salvo: {retorno['arquivo']}")
            st.json(retorno)

    col_btn_5, col_btn_6 = st.columns(2)

    with col_btn_5:
        if st.button("Salvar playbook .md", key="watchlist_playbook"):
            retorno = salvar_playbook_watchlist_markdown()
            st.success(f"Playbook salvo: {retorno['arquivo']}")
            st.json(retorno)

    with col_btn_6:
        if st.button("Salvar checklist .md", key="watchlist_checklist"):
            retorno = salvar_checklist_watchlist_markdown()
            st.success(f"Checklist salvo: {retorno['arquivo']}")
            st.json(retorno)

    if st.button("Salvar decisão Watchlist", key="watchlist_decisao"):
        registro = salvar_decisao_watchlist(saude, observacoes="Decisão gerada pela watchlist de fundadores.")
        st.success(f"Decisão salva: {registro['decisao']}")
        st.rerun()

    st.download_button(
        "Baixar relatório watchlist (.md)",
        data=gerar_relatorio_watchlist_markdown(saude),
        file_name="RELATORIO_WATCHLIST_FUNDADORES_VALORIS.md",
        mime="text/markdown",
        key="download_relatorio_watchlist",
    )

    st.download_button(
        "Baixar watchlist (.csv)",
        data=gerar_csv_watchlist_fundadores(),
        file_name="watchlist_fundadores_valoris.csv",
        mime="text/csv",
        key="download_watchlist_fundadores",
    )

    st.download_button(
        "Baixar alertas (.csv)",
        data=gerar_csv_alertas_watchlist(),
        file_name="alertas_watchlist_fundadores_valoris.csv",
        mime="text/csv",
        key="download_alertas_watchlist",
    )


def executar_autoteste_watchlist_fundadores_valoris() -> List[Dict[str, str]]:
    saude = calcular_saude_watchlist_fundadores()

    return [
        {
            "teste": "versao_watchlist_fundadores",
            "status": "OK" if VERSAO_WATCHLIST_FUNDADORES_VALORIS == "3.8.85" else "FALHA",
            "detalhe": VERSAO_WATCHLIST_FUNDADORES_VALORIS,
        },
        {
            "teste": "score_watchlist",
            "status": "OK" if 0 <= saude["score_watchlist"] <= 100 else "FALHA",
            "detalhe": str(saude["score_watchlist"]),
        },
        {
            "teste": "playbook",
            "status": "OK" if len(PLAYBOOK_WATCHLIST) >= 5 else "FALHA",
            "detalhe": str(len(PLAYBOOK_WATCHLIST)),
        },
        {
            "teste": "renderizador",
            "status": "OK" if callable(renderizar_watchlist_fundadores_valoris) else "FALHA",
            "detalhe": "renderizar_watchlist_fundadores_valoris",
        },
    ]
