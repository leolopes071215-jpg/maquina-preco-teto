# relatorio_premium_v2_valoris.py

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

import streamlit as st


VERSAO_RELATORIO_PREMIUM_V2_VALORIS = "3.8.87"

CAMINHO_DECISOES_RELATORIO_V2 = Path("decisoes_relatorio_premium_v2_valoris.csv")
CAMINHO_MANIFESTO_RELATORIO_V2 = Path("manifesto_relatorio_premium_v2_valoris.json")
CAMINHO_DOSSIE_RELATORIO_V2_MD = Path("DOSSIE_PREMIUM_V2_VALORIS.md")
CAMINHO_PLAYBOOK_RELATORIO_V2_MD = Path("PLAYBOOK_RELATORIO_PREMIUM_V2_VALORIS.md")
CAMINHO_CHECKLIST_RELATORIO_V2_MD = Path("CHECKLIST_RELATORIO_PREMIUM_V2_VALORIS.md")

CAMPOS_DECISAO_RELATORIO_V2 = [
    "id",
    "data_registro",
    "score_relatorio_v2",
    "score_tese",
    "score_risco",
    "score_oportunidade",
    "score_acompanhamento",
    "ticker_base",
    "empresa_base",
    "setor_base",
    "decisao",
    "risco",
    "proximo_passo",
    "observacoes",
]

BLOCOS_RELATORIO_V2 = [
    {
        "bloco": "Resumo executivo",
        "objetivo": "Explicar em poucas linhas o que a empresa faz, por que está no radar e qual decisão analítica o usuário deve tomar.",
        "peso": 18,
    },
    {
        "bloco": "Preço teto e margem de segurança",
        "objetivo": "Mostrar se o ativo está abaixo, próximo ou acima da zona aceitável de estudo.",
        "peso": 18,
    },
    {
        "bloco": "Tese de investimento",
        "objetivo": "Transformar a tese resumida em argumentos claros, sem promessa de retorno.",
        "peso": 20,
    },
    {
        "bloco": "Riscos e pontos cegos",
        "objetivo": "Evitar viés de confirmação e proteger o usuário de uma decisão superficial.",
        "peso": 20,
    },
    {
        "bloco": "Comparação setorial",
        "objetivo": "Contextualizar o ativo contra alternativas da própria watchlist.",
        "peso": 12,
    },
    {
        "bloco": "Plano de acompanhamento",
        "objetivo": "Definir o que acompanhar antes de comprar, manter ou descartar.",
        "peso": 12,
    },
]

PLAYBOOK_RELATORIO_V2 = [
    {
        "etapa": "Escolher ativo base",
        "objetivo": "Evitar relatório genérico.",
        "acao": "Selecionar o ativo mais relevante da watchlist ou o melhor ranqueado no comparador.",
        "sinal_sucesso": "Relatório nasce de uma tese específica.",
    },
    {
        "etapa": "Checar oportunidade",
        "objetivo": "Separar qualidade de preço.",
        "acao": "Usar preço atual, preço teto, margem de segurança e status da oportunidade.",
        "sinal_sucesso": "Usuário entende se vale estudar agora ou esperar.",
    },
    {
        "etapa": "Escrever tese",
        "objetivo": "Deixar claro por que a empresa merece atenção.",
        "acao": "Descrever motor de valor, vantagem competitiva, setor e motivo de monitoramento.",
        "sinal_sucesso": "Tese pode ser lida sem depender da memória do usuário.",
    },
    {
        "etapa": "Forçar ceticismo",
        "objetivo": "Reduzir erro de análise.",
        "acao": "Listar riscos, pontos cegos, premissas frágeis e perguntas críticas.",
        "sinal_sucesso": "Relatório não parece propaganda da empresa.",
    },
    {
        "etapa": "Definir acompanhamento",
        "objetivo": "Criar recorrência e retenção.",
        "acao": "Definir próximo evento, data de revisão, alerta e pergunta para próxima análise.",
        "sinal_sucesso": "Fundador sabe quando e por que voltar ao app.",
    },
]

CHECKLIST_RELATORIO_V2 = [
    "Ativo base selecionado",
    "Ticker e empresa preenchidos",
    "Setor identificado",
    "Preço atual informado",
    "Preço teto informado",
    "Margem de segurança calculada",
    "Status da oportunidade definido",
    "Tese resumida preenchida",
    "Principal risco preenchido",
    "Próximo evento identificado",
    "Perguntas críticas geradas",
    "Plano de acompanhamento gerado",
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


def _carregar_watchlist() -> List[Dict[str, str]]:
    try:
        from watchlist_fundadores_valoris import carregar_watchlist_fundadores

        return carregar_watchlist_fundadores()
    except Exception:
        return []


def _gerar_ranking_comparador() -> List[Dict[str, Any]]:
    try:
        from comparador_setorial_valoris import gerar_ranking_comparador_setorial

        return gerar_ranking_comparador_setorial()
    except Exception:
        return []


def _calcular_saude_comparador() -> Dict[str, Any]:
    try:
        from comparador_setorial_valoris import calcular_saude_comparador_setorial

        return calcular_saude_comparador_setorial()
    except Exception as erro:
        return {"score_comparador": 0, "erro": str(erro)}


def _calcular_saude_watchlist() -> Dict[str, Any]:
    try:
        from watchlist_fundadores_valoris import calcular_saude_watchlist_fundadores

        return calcular_saude_watchlist_fundadores()
    except Exception as erro:
        return {"score_watchlist": 0, "erro": str(erro)}


def _calcular_margem(preco_atual: float, preco_teto: float) -> float:
    if preco_atual <= 0:
        return 0.0
    return round(((preco_teto - preco_atual) / preco_atual) * 100, 2)


def _status_oportunidade(margem: float) -> str:
    if margem >= 15:
        return "Abaixo do preço teto"
    if -5 <= margem < 15:
        return "Próximo do preço teto"
    if margem < -5:
        return "Acima do preço teto"
    return "Revisar premissas"


def _score_texto(texto: str, minimo: int, bom: int, excelente: int) -> int:
    tamanho = len(_limpar_texto(texto))

    if tamanho >= excelente:
        return 100
    if tamanho >= bom:
        return 78
    if tamanho >= minimo:
        return 52
    if tamanho > 0:
        return 28
    return 8


def selecionar_ativo_base_relatorio(ticker: str = "") -> Dict[str, Any]:
    ticker = _limpar_texto(ticker).upper()
    watchlist = _carregar_watchlist()
    ranking = _gerar_ranking_comparador()

    if ticker:
        for item in watchlist:
            if item.get("ticker", "").upper() == ticker:
                return dict(item)

        for item in ranking:
            if item.get("ticker", "").upper() == ticker:
                return dict(item)

    if ranking:
        return dict(ranking[0])

    if watchlist:
        return dict(watchlist[-1])

    return {
        "id": "",
        "ticker": "PENDENTE",
        "empresa": "Empresa não definida",
        "setor": "não informado",
        "preco_atual": "0",
        "preco_teto": "0",
        "margem_seguranca": "0",
        "status_oportunidade": "Revisar premissas",
        "prioridade": "Média",
        "tese_resumo": "",
        "principal_risco": "",
        "proximo_evento": "",
        "data_revisao": "",
        "observacoes": "",
    }


def gerar_perguntas_criticas(ativo: Dict[str, Any]) -> List[str]:
    ticker = ativo.get("ticker", "ativo")
    empresa = ativo.get("empresa", "empresa")
    setor = ativo.get("setor", "setor")

    return [
        f"O que precisa acontecer para a tese de {empresa} ({ticker}) continuar válida nos próximos 12 meses?",
        f"Qual premissa do preço teto é mais frágil e pode derrubar a margem de segurança?",
        f"O risco principal está no negócio, no setor de {setor}, na gestão, no valuation ou no ciclo econômico?",
        "A empresa está barata por oportunidade real ou por deterioração estrutural?",
        "Existe outro ativo da watchlist com tese semelhante e risco menor?",
        "Qual evento futuro deve obrigar uma revisão imediata da análise?",
    ]


def gerar_plano_acompanhamento(ativo: Dict[str, Any]) -> List[Dict[str, str]]:
    ticker = ativo.get("ticker", "PENDENTE")
    proximo_evento = _limpar_texto(ativo.get("proximo_evento")) or "Próximo resultado ou fato relevante"
    data_revisao = _limpar_texto(ativo.get("data_revisao")) or "Definir data"

    return [
        {
            "etapa": "Revisar preço",
            "pergunta": f"O preço atual de {ticker} mudou a margem de segurança?",
            "gatilho": "Mudança relevante de cotação.",
        },
        {
            "etapa": "Revisar tese",
            "pergunta": "A tese continua apoiada por fatos ou virou apenas narrativa?",
            "gatilho": proximo_evento,
        },
        {
            "etapa": "Revisar risco",
            "pergunta": "O principal risco aumentou, diminuiu ou apenas ficou mais visível?",
            "gatilho": "Resultado, guidance, notícia regulatória ou mudança setorial.",
        },
        {
            "etapa": "Revisar comparação",
            "pergunta": "Há outra empresa do setor com melhor relação risco/retorno?",
            "gatilho": "Atualização do comparador setorial.",
        },
        {
            "etapa": "Próxima data",
            "pergunta": "Quando essa tese deve ser reavaliada?",
            "gatilho": data_revisao,
        },
    ]


def calcular_metricas_relatorio_v2(ticker: str = "") -> Dict[str, Any]:
    ativo = selecionar_ativo_base_relatorio(ticker)
    ranking = _gerar_ranking_comparador()

    preco_atual = _to_float(ativo.get("preco_atual"), 0.0)
    preco_teto = _to_float(ativo.get("preco_teto"), 0.0)
    margem = _to_float(ativo.get("margem_seguranca"), 0.0)

    if margem == 0 and preco_atual > 0 and preco_teto > 0:
        margem = _calcular_margem(preco_atual, preco_teto)

    status = _limpar_texto(ativo.get("status_oportunidade")) or _status_oportunidade(margem)
    tese = _limpar_texto(ativo.get("tese_resumo"))
    risco = _limpar_texto(ativo.get("principal_risco"))
    evento = _limpar_texto(ativo.get("proximo_evento"))
    data_revisao = _limpar_texto(ativo.get("data_revisao"))

    pares_setor = [
        item for item in ranking
        if item.get("setor") == ativo.get("setor") and item.get("ticker") != ativo.get("ticker")
    ]

    posicao = None
    for item in ranking:
        if item.get("ticker") == ativo.get("ticker"):
            posicao = item.get("ranking")
            break

    return {
        "ativo": ativo,
        "ticker": ativo.get("ticker", ""),
        "empresa": ativo.get("empresa", ""),
        "setor": ativo.get("setor", ""),
        "preco_atual": preco_atual,
        "preco_teto": preco_teto,
        "margem_seguranca": margem,
        "status_oportunidade": status,
        "tese_resumo": tese,
        "principal_risco": risco,
        "proximo_evento": evento,
        "data_revisao": data_revisao,
        "posicao_ranking": posicao,
        "pares_setor_total": len(pares_setor),
        "pares_setor": pares_setor[:10],
        "perguntas_criticas": gerar_perguntas_criticas(ativo),
        "plano_acompanhamento": gerar_plano_acompanhamento(ativo),
    }


def calcular_saude_relatorio_premium_v2(ticker: str = "") -> Dict[str, Any]:
    metricas = calcular_metricas_relatorio_v2(ticker)
    comparador = _calcular_saude_comparador()
    watchlist = _calcular_saude_watchlist()

    score_tese = _score_texto(metricas["tese_resumo"], minimo=40, bom=100, excelente=220)
    score_risco = _score_texto(metricas["principal_risco"], minimo=35, bom=90, excelente=180)

    margem = metricas["margem_seguranca"]
    status = metricas["status_oportunidade"]

    score_oportunidade = 0
    if margem >= 25:
        score_oportunidade += 45
    elif margem >= 15:
        score_oportunidade += 38
    elif margem >= 5:
        score_oportunidade += 26
    elif margem >= -5:
        score_oportunidade += 14
    else:
        score_oportunidade += 6

    if status == "Abaixo do preço teto":
        score_oportunidade += 35
    elif status == "Próximo do preço teto":
        score_oportunidade += 22
    elif status == "Acima do preço teto":
        score_oportunidade += 8
    else:
        score_oportunidade += 5

    if metricas["preco_atual"] > 0 and metricas["preco_teto"] > 0:
        score_oportunidade += 20

    score_oportunidade = min(100, score_oportunidade)

    score_acompanhamento = 0
    score_acompanhamento += 25 if metricas["proximo_evento"] else 0
    score_acompanhamento += 25 if metricas["data_revisao"] else 0
    score_acompanhamento += 20 if len(metricas["perguntas_criticas"]) >= 6 else 0
    score_acompanhamento += 15 if len(metricas["plano_acompanhamento"]) >= 5 else 0
    score_acompanhamento += 15 if metricas["pares_setor_total"] >= 1 else 0
    score_acompanhamento = min(100, score_acompanhamento)

    score_base = int(round(
        int(comparador.get("score_comparador", 0) or 0) * 0.55
        + int(watchlist.get("score_watchlist", 0) or 0) * 0.45
    ))

    score_relatorio_v2 = int(round(
        score_tese * 0.24
        + score_risco * 0.22
        + score_oportunidade * 0.24
        + score_acompanhamento * 0.18
        + score_base * 0.12
    ))

    if metricas["ticker"] == "PENDENTE":
        risco = "Alto"
        decisao = "Relatório sem ativo base"
        proximo_passo = "Registrar uma empresa na watchlist antes de gerar dossiê premium."
    elif score_relatorio_v2 >= 82:
        risco = "Médio controlado"
        decisao = "Dossiê premium pronto para revisão com fundador"
        proximo_passo = "Usar o relatório em uma conversa real e coletar feedback sobre clareza, tese e utilidade."
    elif score_relatorio_v2 >= 65:
        risco = "Médio"
        decisao = "Dossiê utilizável, mas ainda precisa de refinamento"
        proximo_passo = "Fortalecer tese, risco e plano de acompanhamento antes de usar como material premium."
    else:
        risco = "Médio/Alto"
        decisao = "Dossiê fraco para percepção premium"
        proximo_passo = "Completar tese, risco, preço teto e próximos eventos do ativo."

    return {
        "versao": VERSAO_RELATORIO_PREMIUM_V2_VALORIS,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score_relatorio_v2": max(0, min(100, score_relatorio_v2)),
        "score_tese": score_tese,
        "score_risco": score_risco,
        "score_oportunidade": score_oportunidade,
        "score_acompanhamento": score_acompanhamento,
        "score_base": score_base,
        "ticker_base": metricas["ticker"],
        "empresa_base": metricas["empresa"],
        "setor_base": metricas["setor"],
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo_passo,
        "metricas_relatorio_v2": metricas,
        "blocos": BLOCOS_RELATORIO_V2,
        "playbook": PLAYBOOK_RELATORIO_V2,
        "checklist": CHECKLIST_RELATORIO_V2,
        "comparador": comparador,
        "watchlist": watchlist,
    }


def salvar_decisao_relatorio_premium_v2(saude: Dict[str, Any], observacoes: str = "") -> Dict[str, str]:
    _garantir_csv(CAMINHO_DECISOES_RELATORIO_V2, CAMPOS_DECISAO_RELATORIO_V2)

    registro = {
        "id": str(uuid4())[:8],
        "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score_relatorio_v2": str(saude.get("score_relatorio_v2", "")),
        "score_tese": str(saude.get("score_tese", "")),
        "score_risco": str(saude.get("score_risco", "")),
        "score_oportunidade": str(saude.get("score_oportunidade", "")),
        "score_acompanhamento": str(saude.get("score_acompanhamento", "")),
        "ticker_base": _limpar_texto(saude.get("ticker_base")),
        "empresa_base": _limpar_texto(saude.get("empresa_base")),
        "setor_base": _limpar_texto(saude.get("setor_base")),
        "decisao": _limpar_texto(saude.get("decisao")),
        "risco": _limpar_texto(saude.get("risco")),
        "proximo_passo": _limpar_texto(saude.get("proximo_passo")),
        "observacoes": _limpar_texto(observacoes),
    }

    with CAMINHO_DECISOES_RELATORIO_V2.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISAO_RELATORIO_V2)
        escritor.writerow(registro)

    return registro


def carregar_decisoes_relatorio_premium_v2() -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_DECISOES_RELATORIO_V2, CAMPOS_DECISAO_RELATORIO_V2)

    with CAMINHO_DECISOES_RELATORIO_V2.open("r", newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def gerar_csv_decisoes_relatorio_v2() -> str:
    _garantir_csv(CAMINHO_DECISOES_RELATORIO_V2, CAMPOS_DECISAO_RELATORIO_V2)
    return CAMINHO_DECISOES_RELATORIO_V2.read_text(encoding="utf-8")


def gerar_dossie_premium_v2_markdown(ticker: str = "") -> str:
    saude = calcular_saude_relatorio_premium_v2(ticker)
    m = saude["metricas_relatorio_v2"]

    perguntas = "\n".join([f"- {pergunta}" for pergunta in m["perguntas_criticas"]])

    plano = "\n".join(
        [
            f"- **{item['etapa']}** — {item['pergunta']} Gatilho: {item['gatilho']}"
            for item in m["plano_acompanhamento"]
        ]
    )

    pares = "\n".join(
        [
            f"- **{item.get('ticker', '')} — {item.get('empresa', '')}**: score {item.get('score_setorial', '')}, margem {item.get('margem_seguranca', '')}%"
            for item in m["pares_setor"]
        ]
    ) or "- Nenhum par setorial encontrado na watchlist."

    return f"""# Dossiê Premium v2 — Valoris

Versão: {VERSAO_RELATORIO_PREMIUM_V2_VALORIS}  
Gerado em: {saude["gerado_em"]}

## Resumo executivo

**Empresa:** {m["empresa"]}  
**Ticker:** {m["ticker"]}  
**Setor:** {m["setor"]}  
**Score do dossiê:** {saude["score_relatorio_v2"]}/100  
**Decisão analítica:** {saude["decisao"]}  
**Risco:** {saude["risco"]}  
**Próximo passo:** {saude["proximo_passo"]}

## Preço teto e margem de segurança

Preço atual: R$ {m["preco_atual"]}  
Preço teto: R$ {m["preco_teto"]}  
Margem de segurança: {m["margem_seguranca"]}%  
Status: {m["status_oportunidade"]}

## Tese de investimento

{m["tese_resumo"] or "Tese ainda não preenchida. O relatório precisa de uma tese clara antes de ser usado como material premium."}

## Riscos e pontos cegos

{m["principal_risco"] or "Risco principal ainda não preenchido. Sem risco claro, o relatório pode gerar excesso de confiança."}

## Comparação setorial

Posição no ranking: {m["posicao_ranking"] or "pendente"}  
Pares encontrados no setor: {m["pares_setor_total"]}

{pares}

## Perguntas críticas

{perguntas}

## Plano de acompanhamento

{plano}

## Nota de uso

Este dossiê organiza estudo e acompanhamento. Ele não é recomendação de compra, venda ou manutenção.
"""


def gerar_playbook_relatorio_v2_markdown(saude: Dict[str, Any] | None = None) -> str:
    if saude is None:
        saude = calcular_saude_relatorio_premium_v2()

    etapas = "\n\n".join(
        [
            f"""## {item['etapa']}

**Objetivo:** {item['objetivo']}  
**Ação:** {item['acao']}  
**Sinal de sucesso:** {item['sinal_sucesso']}
"""
            for item in PLAYBOOK_RELATORIO_V2
        ]
    )

    return f"""# Playbook Relatório Premium v2 — Valoris

Versão: {VERSAO_RELATORIO_PREMIUM_V2_VALORIS}  
Gerado em: {saude["gerado_em"]}

## Princípio

Um relatório premium não deve ser bonito apenas visualmente. Ele precisa organizar tese, preço, risco, comparação e acompanhamento.

## Etapas

{etapas}
"""


def gerar_checklist_relatorio_v2_markdown(saude: Dict[str, Any] | None = None) -> str:
    if saude is None:
        saude = calcular_saude_relatorio_premium_v2()

    checklist = "\n".join([f"- [x] {item}" for item in CHECKLIST_RELATORIO_V2])

    return f"""# Checklist Relatório Premium v2 — Valoris

Versão: {VERSAO_RELATORIO_PREMIUM_V2_VALORIS}  
Gerado em: {saude["gerado_em"]}

## Status

Score Relatório v2: {saude["score_relatorio_v2"]}/100  
Decisão: {saude["decisao"]}

## Checklist

{checklist}
"""


def salvar_dossie_premium_v2_markdown(ticker: str = "") -> Dict[str, Any]:
    saude = calcular_saude_relatorio_premium_v2(ticker)
    CAMINHO_DOSSIE_RELATORIO_V2_MD.write_text(gerar_dossie_premium_v2_markdown(ticker), encoding="utf-8")
    return {
        "ok": True,
        "arquivo": str(CAMINHO_DOSSIE_RELATORIO_V2_MD),
        "ticker_base": saude["ticker_base"],
        "score_relatorio_v2": saude["score_relatorio_v2"],
    }


def salvar_playbook_relatorio_v2_markdown() -> Dict[str, Any]:
    saude = calcular_saude_relatorio_premium_v2()
    CAMINHO_PLAYBOOK_RELATORIO_V2_MD.write_text(gerar_playbook_relatorio_v2_markdown(saude), encoding="utf-8")
    return {"ok": True, "arquivo": str(CAMINHO_PLAYBOOK_RELATORIO_V2_MD), "score_relatorio_v2": saude["score_relatorio_v2"]}


def salvar_checklist_relatorio_v2_markdown() -> Dict[str, Any]:
    saude = calcular_saude_relatorio_premium_v2()
    CAMINHO_CHECKLIST_RELATORIO_V2_MD.write_text(gerar_checklist_relatorio_v2_markdown(saude), encoding="utf-8")
    return {"ok": True, "arquivo": str(CAMINHO_CHECKLIST_RELATORIO_V2_MD), "score_relatorio_v2": saude["score_relatorio_v2"]}


def gerar_manifesto_relatorio_premium_v2(ticker: str = "") -> Dict[str, Any]:
    saude = calcular_saude_relatorio_premium_v2(ticker)
    manifesto = {
        "versao": VERSAO_RELATORIO_PREMIUM_V2_VALORIS,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "saude": saude,
        "blocos": BLOCOS_RELATORIO_V2,
        "playbook": PLAYBOOK_RELATORIO_V2,
        "checklist": CHECKLIST_RELATORIO_V2,
        "estrategia": {
            "objetivo": "Transformar ranking e watchlist em dossiê premium de tese, risco e acompanhamento.",
            "proxima_versao": "Melhorar exportação, layout e automação de dossiê por empresa.",
            "regra": "Relatório premium precisa aumentar clareza, não apenas volume de texto.",
        },
    }

    CAMINHO_MANIFESTO_RELATORIO_V2.write_text(json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifesto


def _injetar_css_relatorio_v2() -> None:
    st.markdown(
        """
        <style>
            .relatorio-v2-hero {
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
            .relatorio-v2-eyebrow {
                color: #d6b56d;
                font-size: 0.74rem;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                font-weight: 880;
                margin-bottom: 0.35rem;
            }
            .relatorio-v2-title {
                color: #f4f7fb;
                font-size: clamp(1.8rem, 5.5vw, 3.25rem);
                font-weight: 950;
                line-height: 1.02;
                letter-spacing: -0.058em;
                margin-bottom: 0.55rem;
            }
            .relatorio-v2-subtitle {
                color: rgba(244, 247, 251, 0.75);
                font-size: clamp(0.94rem, 2.2vw, 1.06rem);
                line-height: 1.56;
                max-width: 1050px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def renderizar_relatorio_premium_v2_valoris() -> None:
    _injetar_css_relatorio_v2()

    st.markdown(
        f"""
        <div class="relatorio-v2-hero">
            <div class="relatorio-v2-eyebrow">Valoris • Relatório Premium v2 • v{VERSAO_RELATORIO_PREMIUM_V2_VALORIS}</div>
            <div class="relatorio-v2-title">Dossiê de tese, risco e acompanhamento.</div>
            <div class="relatorio-v2-subtitle">
                Transforme watchlist e ranking setorial em um relatório mais claro, cético e útil para o fundador.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    watchlist = _carregar_watchlist()
    tickers = [item.get("ticker", "") for item in watchlist if item.get("ticker")]
    tickers_unicos = list(dict.fromkeys(tickers))

    ticker_escolhido = st.selectbox(
        "Ativo base do dossiê",
        tickers_unicos or ["PENDENTE"],
        help="Use ativos já cadastrados na Watchlist Fundadores.",
    )

    saude = calcular_saude_relatorio_premium_v2(ticker_escolhido if ticker_escolhido != "PENDENTE" else "")

    st.markdown("### Diagnóstico do relatório")
    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Score Relatório v2", f"{saude['score_relatorio_v2']}/100")

    with col_2:
        st.metric("Tese", f"{saude['score_tese']}/100")

    with col_3:
        st.metric("Risco", f"{saude['score_risco']}/100")

    with col_4:
        st.metric("Ticker", saude["ticker_base"])

    st.progress(saude["score_relatorio_v2"] / 100)

    if saude["score_relatorio_v2"] >= 82:
        st.success(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    elif saude["ticker_base"] != "PENDENTE":
        st.warning(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    else:
        st.info(f"**{saude['decisao']}** — {saude['proximo_passo']}")

    st.divider()

    m = saude["metricas_relatorio_v2"]

    st.markdown("### Resumo do ativo")
    st.json(
        {
            "empresa": m["empresa"],
            "ticker": m["ticker"],
            "setor": m["setor"],
            "preco_atual": m["preco_atual"],
            "preco_teto": m["preco_teto"],
            "margem_seguranca": m["margem_seguranca"],
            "status_oportunidade": m["status_oportunidade"],
            "posicao_ranking": m["posicao_ranking"],
            "pares_setor_total": m["pares_setor_total"],
        }
    )

    st.markdown("### Dossiê gerado")
    st.markdown(gerar_dossie_premium_v2_markdown(ticker_escolhido if ticker_escolhido != "PENDENTE" else ""))

    st.divider()

    col_btn_1, col_btn_2, col_btn_3, col_btn_4 = st.columns(4)

    with col_btn_1:
        if st.button("Salvar dossiê .md", key="relatorio_v2_dossie"):
            retorno = salvar_dossie_premium_v2_markdown(ticker_escolhido if ticker_escolhido != "PENDENTE" else "")
            st.success(f"Dossiê salvo: {retorno['arquivo']}")
            st.json(retorno)

    with col_btn_2:
        if st.button("Gerar manifesto", key="relatorio_v2_manifesto"):
            manifesto = gerar_manifesto_relatorio_premium_v2(ticker_escolhido if ticker_escolhido != "PENDENTE" else "")
            st.success(f"Manifesto gerado: {CAMINHO_MANIFESTO_RELATORIO_V2}")
            st.json({"versao": manifesto["versao"], "score": manifesto["saude"]["score_relatorio_v2"]})

    with col_btn_3:
        if st.button("Salvar playbook .md", key="relatorio_v2_playbook"):
            retorno = salvar_playbook_relatorio_v2_markdown()
            st.success(f"Playbook salvo: {retorno['arquivo']}")
            st.json(retorno)

    with col_btn_4:
        if st.button("Salvar checklist .md", key="relatorio_v2_checklist"):
            retorno = salvar_checklist_relatorio_v2_markdown()
            st.success(f"Checklist salvo: {retorno['arquivo']}")
            st.json(retorno)

    if st.button("Salvar decisão Relatório v2", key="relatorio_v2_decisao"):
        registro = salvar_decisao_relatorio_premium_v2(
            saude,
            observacoes="Decisão gerada pelo relatório premium v2.",
        )
        st.success(f"Decisão salva: {registro['decisao']}")
        st.rerun()

    st.download_button(
        "Baixar dossiê premium v2 (.md)",
        data=gerar_dossie_premium_v2_markdown(ticker_escolhido if ticker_escolhido != "PENDENTE" else ""),
        file_name="DOSSIE_PREMIUM_V2_VALORIS.md",
        mime="text/markdown",
        key="download_dossie_premium_v2",
    )

    st.download_button(
        "Baixar decisões relatório v2 (.csv)",
        data=gerar_csv_decisoes_relatorio_v2(),
        file_name="decisoes_relatorio_premium_v2_valoris.csv",
        mime="text/csv",
        key="download_decisoes_relatorio_v2",
    )


def executar_autoteste_relatorio_premium_v2_valoris() -> List[Dict[str, str]]:
    saude = calcular_saude_relatorio_premium_v2()

    return [
        {
            "teste": "versao_relatorio_premium_v2",
            "status": "OK" if VERSAO_RELATORIO_PREMIUM_V2_VALORIS == "3.8.87" else "FALHA",
            "detalhe": VERSAO_RELATORIO_PREMIUM_V2_VALORIS,
        },
        {
            "teste": "score_relatorio_v2",
            "status": "OK" if 0 <= saude["score_relatorio_v2"] <= 100 else "FALHA",
            "detalhe": str(saude["score_relatorio_v2"]),
        },
        {
            "teste": "dossie_markdown",
            "status": "OK" if "# Dossiê Premium v2" in gerar_dossie_premium_v2_markdown() else "FALHA",
            "detalhe": "gerar_dossie_premium_v2_markdown",
        },
        {
            "teste": "renderizador",
            "status": "OK" if callable(renderizar_relatorio_premium_v2_valoris) else "FALHA",
            "detalhe": "renderizar_relatorio_premium_v2_valoris",
        },
    ]
