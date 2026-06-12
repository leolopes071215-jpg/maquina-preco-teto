# roadmap_premium_valoris.py

from __future__ import annotations

import csv
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

import streamlit as st


VERSAO_ROADMAP_PREMIUM_VALORIS = "3.8.90"

CAMINHO_BACKLOG_ROADMAP = Path("backlog_roadmap_premium_valoris.csv")
CAMINHO_DECISOES_ROADMAP = Path("decisoes_roadmap_premium_valoris.csv")
CAMINHO_MANIFESTO_ROADMAP = Path("manifesto_roadmap_premium_valoris.json")
CAMINHO_ROADMAP_MD = Path("ROADMAP_PREMIUM_VALORIS.md")
CAMINHO_SPRINT_MD = Path("SPRINT_PLANNING_PREMIUM_VALORIS.md")
CAMINHO_CHECKLIST_MD = Path("CHECKLIST_ROADMAP_PREMIUM_VALORIS.md")

CAMPOS_BACKLOG_ROADMAP = [
    "id",
    "data_registro",
    "titulo",
    "categoria",
    "origem",
    "dor_resolvida",
    "impacto_valor",
    "impacto_retencao",
    "impacto_comercial",
    "esforco",
    "risco",
    "score_prioridade",
    "prazo_sugerido",
    "status",
    "criterio_sucesso",
    "observacoes",
]

CAMPOS_DECISAO_ROADMAP = [
    "id",
    "data_registro",
    "score_roadmap",
    "score_aprendizado",
    "score_priorizacao",
    "score_execucao",
    "score_comercial",
    "itens_backlog",
    "itens_alta_prioridade",
    "sprint_sugerida",
    "risco",
    "decisao",
    "proximo_passo",
    "observacoes",
]

CATEGORIAS_ROADMAP = [
    "Clareza",
    "Dados",
    "Relatório",
    "Watchlist",
    "Comparador",
    "Alertas",
    "Onboarding",
    "Comercial",
    "Retenção",
    "Infraestrutura",
]

PLAYBOOK_ROADMAP = [
    {
        "etapa": "Transformar feedback em item de backlog",
        "objetivo": "Evitar que feedback vire apenas anotação solta.",
        "acao": "Converter objeção, confusão ou feature pedida em item priorizável.",
        "sinal_sucesso": "Cada dor importante tem título, categoria, impacto, esforço e critério de sucesso.",
    },
    {
        "etapa": "Priorizar por valor e retenção",
        "objetivo": "Evitar construir o que é bonito, mas não retém.",
        "acao": "Ponderar impacto em valor percebido, retenção, comercial e esforço.",
        "sinal_sucesso": "Os itens de maior impacto aparecem no topo do roadmap.",
    },
    {
        "etapa": "Definir sprint pequena",
        "objetivo": "Manter avanço sem quebrar o app.",
        "acao": "Escolher 1 a 3 itens para a próxima sprint.",
        "sinal_sucesso": "A próxima versão tem escopo claro.",
    },
    {
        "etapa": "Vincular a métrica",
        "objetivo": "Não lançar melhoria sem critério de sucesso.",
        "acao": "Cada item precisa de um indicador: clareza, uso, feedback, pagamento ou retenção.",
        "sinal_sucesso": "Depois da entrega é possível dizer se melhorou ou não.",
    },
    {
        "etapa": "Fechar loop",
        "objetivo": "Aprender com fundadores e voltar ao produto.",
        "acao": "Depois da sprint, entregar pacote atualizado e coletar novo feedback.",
        "sinal_sucesso": "O próximo feedback fica melhor que o anterior.",
    },
]

CHECKLIST_ROADMAP = [
    "Feedbacks do pacote foram lidos",
    "Principal objeção foi convertida em item",
    "Feature mais pedida foi convertida em item",
    "Parte confusa virou melhoria de clareza",
    "Itens têm categoria",
    "Itens têm impacto estimado",
    "Itens têm esforço estimado",
    "Itens têm critério de sucesso",
    "Sprint sugerida tem no máximo 3 itens",
    "Decisão de roadmap foi salva",
]


def _limpar_texto(valor: Any) -> str:
    if valor is None:
        return ""
    return str(valor).strip()


def _to_int(valor: Any, padrao: int = 0) -> int:
    try:
        return int(valor)
    except Exception:
        return padrao


def _garantir_csv(caminho: Path, campos: List[str]) -> None:
    if caminho.exists():
        return

    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()


def _calcular_saude_feedback_pacote() -> Dict[str, Any]:
    try:
        from feedback_pacote_premium_valoris import calcular_saude_feedback_pacote_premium

        return calcular_saude_feedback_pacote_premium()
    except Exception as erro:
        return {
            "score_feedback_pacote": 0,
            "principal_objeção": "",
            "feature_mais_pedida": "",
            "erro": str(erro),
        }


def _calcular_saude_pacote() -> Dict[str, Any]:
    try:
        from pacote_premium_valoris import calcular_saude_pacote_premium

        return calcular_saude_pacote_premium()
    except Exception as erro:
        return {"score_pacote": 0, "erro": str(erro)}


def carregar_backlog_roadmap() -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_BACKLOG_ROADMAP, CAMPOS_BACKLOG_ROADMAP)

    with CAMINHO_BACKLOG_ROADMAP.open("r", newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def carregar_decisoes_roadmap() -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_DECISOES_ROADMAP, CAMPOS_DECISAO_ROADMAP)

    with CAMINHO_DECISOES_ROADMAP.open("r", newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def gerar_csv_backlog_roadmap() -> str:
    _garantir_csv(CAMINHO_BACKLOG_ROADMAP, CAMPOS_BACKLOG_ROADMAP)
    return CAMINHO_BACKLOG_ROADMAP.read_text(encoding="utf-8")


def gerar_csv_decisoes_roadmap() -> str:
    _garantir_csv(CAMINHO_DECISOES_ROADMAP, CAMPOS_DECISAO_ROADMAP)
    return CAMINHO_DECISOES_ROADMAP.read_text(encoding="utf-8")


def calcular_score_prioridade(
    impacto_valor: int,
    impacto_retencao: int,
    impacto_comercial: int,
    esforco: int,
    risco: int,
) -> int:
    valor = max(0, min(10, impacto_valor))
    retencao = max(0, min(10, impacto_retencao))
    comercial = max(0, min(10, impacto_comercial))
    esforco = max(1, min(10, esforco))
    risco = max(0, min(10, risco))

    score = (
        valor * 3.0
        + retencao * 3.2
        + comercial * 2.2
        - esforco * 1.35
        - risco * 0.85
        + 20
    )

    return int(max(0, min(100, round(score))))


def classificar_prazo(score: int, esforco: int) -> str:
    if score >= 78 and esforco <= 5:
        return "Sprint atual"
    if score >= 68:
        return "Próxima sprint"
    if score >= 52:
        return "Backlog priorizado"
    return "Backlog futuro"


def salvar_item_roadmap(dados: Dict[str, Any]) -> Dict[str, str]:
    _garantir_csv(CAMINHO_BACKLOG_ROADMAP, CAMPOS_BACKLOG_ROADMAP)

    impacto_valor = _to_int(dados.get("impacto_valor"), 0)
    impacto_retencao = _to_int(dados.get("impacto_retencao"), 0)
    impacto_comercial = _to_int(dados.get("impacto_comercial"), 0)
    esforco = _to_int(dados.get("esforco"), 5)
    risco = _to_int(dados.get("risco"), 5)

    score = calcular_score_prioridade(
        impacto_valor=impacto_valor,
        impacto_retencao=impacto_retencao,
        impacto_comercial=impacto_comercial,
        esforco=esforco,
        risco=risco,
    )

    registro = {
        "id": str(uuid4())[:8],
        "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "titulo": _limpar_texto(dados.get("titulo")),
        "categoria": _limpar_texto(dados.get("categoria", "Produto")),
        "origem": _limpar_texto(dados.get("origem", "Manual")),
        "dor_resolvida": _limpar_texto(dados.get("dor_resolvida")),
        "impacto_valor": str(impacto_valor),
        "impacto_retencao": str(impacto_retencao),
        "impacto_comercial": str(impacto_comercial),
        "esforco": str(esforco),
        "risco": str(risco),
        "score_prioridade": str(score),
        "prazo_sugerido": classificar_prazo(score, esforco),
        "status": _limpar_texto(dados.get("status", "Aberto")),
        "criterio_sucesso": _limpar_texto(dados.get("criterio_sucesso")),
        "observacoes": _limpar_texto(dados.get("observacoes")),
    }

    with CAMINHO_BACKLOG_ROADMAP.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_BACKLOG_ROADMAP)
        escritor.writerow(registro)

    return registro


def gerar_itens_roadmap_por_feedback() -> List[Dict[str, str]]:
    feedback = _calcular_saude_feedback_pacote()
    metricas = feedback.get("metricas_feedback", {})

    principal_objecao = _limpar_texto(feedback.get("principal_objeção") or metricas.get("principal_objeção"))
    feature_pedida = _limpar_texto(feedback.get("feature_mais_pedida") or metricas.get("feature_mais_pedida"))
    parte_confusa = _limpar_texto(metricas.get("parte_confusa"))
    melhor_parte = _limpar_texto(metricas.get("melhor_parte"))

    sugestoes = []

    if principal_objecao:
        sugestoes.append(
            {
                "titulo": "Reduzir principal objeção do pacote premium",
                "categoria": "Comercial",
                "origem": "Feedback Pacote",
                "dor_resolvida": principal_objecao,
                "impacto_valor": 8,
                "impacto_retencao": 7,
                "impacto_comercial": 9,
                "esforco": 4,
                "risco": 4,
                "criterio_sucesso": "Objeção aparece menos nos próximos 3 feedbacks.",
                "observacoes": "Gerado automaticamente a partir da principal objeção registrada.",
            }
        )

    if feature_pedida:
        sugestoes.append(
            {
                "titulo": "Construir ou prototipar feature mais pedida",
                "categoria": "Retenção",
                "origem": "Feedback Pacote",
                "dor_resolvida": feature_pedida,
                "impacto_valor": 9,
                "impacto_retencao": 9,
                "impacto_comercial": 7,
                "esforco": 6,
                "risco": 5,
                "criterio_sucesso": "Pelo menos 1 fundador usa ou pede explicitamente a feature no próximo ciclo.",
                "observacoes": "Gerado automaticamente a partir da feature mais desejada.",
            }
        )

    if parte_confusa:
        sugestoes.append(
            {
                "titulo": "Simplificar parte confusa do pacote premium",
                "categoria": "Clareza",
                "origem": "Feedback Pacote",
                "dor_resolvida": parte_confusa,
                "impacto_valor": 8,
                "impacto_retencao": 6,
                "impacto_comercial": 6,
                "esforco": 3,
                "risco": 2,
                "criterio_sucesso": "Nota média de clareza subir no próximo feedback.",
                "observacoes": "Gerado automaticamente a partir da parte confusa.",
            }
        )

    if melhor_parte:
        sugestoes.append(
            {
                "titulo": "Reforçar bloco de maior valor percebido",
                "categoria": "Relatório",
                "origem": "Feedback Pacote",
                "dor_resolvida": melhor_parte,
                "impacto_valor": 7,
                "impacto_retencao": 6,
                "impacto_comercial": 7,
                "esforco": 3,
                "risco": 2,
                "criterio_sucesso": "Melhor parte continua sendo citada e a nota geral sobe.",
                "observacoes": "Gerado automaticamente a partir do maior valor percebido.",
            }
        )

    if not sugestoes:
        sugestoes.append(
            {
                "titulo": "Coletar feedback real do pacote premium",
                "categoria": "Produto",
                "origem": "Sistema",
                "dor_resolvida": "Ainda não há feedback suficiente para priorizar roadmap com segurança.",
                "impacto_valor": 7,
                "impacto_retencao": 8,
                "impacto_comercial": 7,
                "esforco": 2,
                "risco": 2,
                "criterio_sucesso": "Coletar pelo menos 3 feedbacks de fundadores.",
                "observacoes": "Item criado porque ainda não há dados suficientes.",
            }
        )

    registros = []
    for item in sugestoes:
        registros.append(salvar_item_roadmap(item))

    return registros


def gerar_backlog_ordenado() -> List[Dict[str, Any]]:
    itens = carregar_backlog_roadmap()
    normalizados: List[Dict[str, Any]] = []

    for item in itens:
        novo = dict(item)
        novo["impacto_valor"] = _to_int(item.get("impacto_valor"), 0)
        novo["impacto_retencao"] = _to_int(item.get("impacto_retencao"), 0)
        novo["impacto_comercial"] = _to_int(item.get("impacto_comercial"), 0)
        novo["esforco"] = _to_int(item.get("esforco"), 0)
        novo["risco"] = _to_int(item.get("risco"), 0)
        novo["score_prioridade"] = _to_int(item.get("score_prioridade"), 0)
        normalizados.append(novo)

    normalizados.sort(key=lambda x: x["score_prioridade"], reverse=True)
    return normalizados


def sugerir_sprint_roadmap(limite: int = 3) -> List[Dict[str, Any]]:
    backlog = gerar_backlog_ordenado()
    candidatos = [
        item for item in backlog
        if item.get("status", "Aberto") != "Concluído"
    ]

    sprint = candidatos[:limite]
    data_inicio = datetime.now().date()
    data_fim = data_inicio + timedelta(days=14)

    for item in sprint:
        item["sprint_inicio"] = str(data_inicio)
        item["sprint_fim"] = str(data_fim)

    return sprint


def calcular_metricas_roadmap() -> Dict[str, Any]:
    backlog = gerar_backlog_ordenado()
    sprint = sugerir_sprint_roadmap()

    itens_alta = [item for item in backlog if _to_int(item.get("score_prioridade"), 0) >= 75]
    itens_sprint = [item for item in backlog if item.get("prazo_sugerido") == "Sprint atual"]
    itens_abertos = [item for item in backlog if item.get("status") != "Concluído"]
    itens_concluidos = [item for item in backlog if item.get("status") == "Concluído"]

    categorias: Dict[str, int] = {}
    for item in backlog:
        categoria = item.get("categoria", "não informado")
        categorias[categoria] = categorias.get(categoria, 0) + 1

    return {
        "itens_backlog": len(backlog),
        "itens_alta_prioridade": len(itens_alta),
        "itens_sprint_atual": len(itens_sprint),
        "itens_abertos": len(itens_abertos),
        "itens_concluidos": len(itens_concluidos),
        "categorias": categorias,
        "sprint_sugerida": sprint,
        "backlog": backlog,
    }


def calcular_saude_roadmap_premium() -> Dict[str, Any]:
    metricas = calcular_metricas_roadmap()
    feedback = _calcular_saude_feedback_pacote()
    pacote = _calcular_saude_pacote()

    score_aprendizado = 0
    score_aprendizado += 30 if int(feedback.get("feedbacks_total", 0) or 0) >= 1 else 0
    score_aprendizado += 25 if feedback.get("principal_objeção") else 0
    score_aprendizado += 25 if feedback.get("feature_mais_pedida") else 0
    score_aprendizado += 20 if int(feedback.get("score_feedback_pacote", 0) or 0) >= 65 else 0
    score_aprendizado = min(100, score_aprendizado)

    score_priorizacao = 0
    score_priorizacao += 25 if metricas["itens_backlog"] >= 1 else 0
    score_priorizacao += 25 if metricas["itens_alta_prioridade"] >= 1 else 0
    score_priorizacao += 20 if len(metricas["categorias"]) >= 2 else 0
    score_priorizacao += 15 if len(metricas["sprint_sugerida"]) >= 1 else 0
    score_priorizacao += 15 if len(metricas["sprint_sugerida"]) <= 3 else 0
    score_priorizacao = min(100, score_priorizacao)

    score_execucao = 0
    score_execucao += 25 if len(PLAYBOOK_ROADMAP) >= 5 else 0
    score_execucao += 25 if len(CHECKLIST_ROADMAP) >= 10 else 0
    score_execucao += 25 if metricas["itens_abertos"] >= 1 else 0
    score_execucao += 25 if metricas["itens_concluidos"] >= 1 else 0
    score_execucao = min(100, score_execucao)

    score_comercial = 0
    score_comercial += 35 if int(pacote.get("score_pacote", 0) or 0) >= 70 else 0
    score_comercial += 35 if int(feedback.get("score_comercial", 0) or 0) >= 55 else 0
    score_comercial += 30 if int(feedback.get("pagantes_potenciais", 0) or 0) >= 1 else 0
    score_comercial = min(100, score_comercial)

    score_roadmap = int(round(
        score_aprendizado * 0.30
        + score_priorizacao * 0.28
        + score_execucao * 0.22
        + score_comercial * 0.20
    ))

    if metricas["itens_backlog"] >= 3 and len(metricas["sprint_sugerida"]) >= 1 and score_roadmap >= 82:
        risco = "Médio controlado"
        decisao = "Roadmap premium pronto para próxima sprint"
        proximo_passo = "Executar os 1 a 3 itens de maior prioridade e medir novo feedback."
    elif metricas["itens_backlog"] >= 1:
        risco = "Médio"
        decisao = "Roadmap inicial criado, mas ainda precisa de mais aprendizado"
        proximo_passo = "Coletar mais feedbacks e refinar critérios de sucesso antes de escalar."
    else:
        risco = "Alto"
        decisao = "Roadmap ainda sem backlog real"
        proximo_passo = "Converter feedback do pacote em itens de roadmap."

    return {
        "versao": VERSAO_ROADMAP_PREMIUM_VALORIS,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score_roadmap": max(0, min(100, score_roadmap)),
        "score_aprendizado": score_aprendizado,
        "score_priorizacao": score_priorizacao,
        "score_execucao": score_execucao,
        "score_comercial": score_comercial,
        "itens_backlog": metricas["itens_backlog"],
        "itens_alta_prioridade": metricas["itens_alta_prioridade"],
        "sprint_sugerida": len(metricas["sprint_sugerida"]),
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo_passo,
        "metricas_roadmap": metricas,
        "feedback": feedback,
        "pacote": pacote,
        "playbook": PLAYBOOK_ROADMAP,
        "checklist": CHECKLIST_ROADMAP,
    }


def salvar_decisao_roadmap(saude: Dict[str, Any], observacoes: str = "") -> Dict[str, str]:
    _garantir_csv(CAMINHO_DECISOES_ROADMAP, CAMPOS_DECISAO_ROADMAP)

    registro = {
        "id": str(uuid4())[:8],
        "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score_roadmap": str(saude.get("score_roadmap", "")),
        "score_aprendizado": str(saude.get("score_aprendizado", "")),
        "score_priorizacao": str(saude.get("score_priorizacao", "")),
        "score_execucao": str(saude.get("score_execucao", "")),
        "score_comercial": str(saude.get("score_comercial", "")),
        "itens_backlog": str(saude.get("itens_backlog", "")),
        "itens_alta_prioridade": str(saude.get("itens_alta_prioridade", "")),
        "sprint_sugerida": str(saude.get("sprint_sugerida", "")),
        "risco": _limpar_texto(saude.get("risco")),
        "decisao": _limpar_texto(saude.get("decisao")),
        "proximo_passo": _limpar_texto(saude.get("proximo_passo")),
        "observacoes": _limpar_texto(observacoes),
    }

    with CAMINHO_DECISOES_ROADMAP.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISAO_ROADMAP)
        escritor.writerow(registro)

    return registro


def gerar_roadmap_markdown(saude: Dict[str, Any] | None = None) -> str:
    if saude is None:
        saude = calcular_saude_roadmap_premium()

    backlog = saude["metricas_roadmap"]["backlog"]
    linhas = "\n".join(
        [
            f"- **{item['titulo']}** ({item['categoria']}): score {item['score_prioridade']}/100, prazo {item['prazo_sugerido']}. Critério: {item['criterio_sucesso']}"
            for item in backlog[:20]
        ]
    ) or "- Nenhum item de backlog registrado."

    return f"""# Roadmap Premium Valoris

Versão: {VERSAO_ROADMAP_PREMIUM_VALORIS}  
Gerado em: {saude["gerado_em"]}

## Diagnóstico

Score Roadmap: {saude["score_roadmap"]}/100  
Itens no backlog: {saude["itens_backlog"]}  
Itens de alta prioridade: {saude["itens_alta_prioridade"]}  
Sprint sugerida: {saude["sprint_sugerida"]} item(ns)  
Decisão: {saude["decisao"]}

## Backlog priorizado

{linhas}

## Próximo passo

{saude["proximo_passo"]}
"""


def gerar_sprint_markdown(saude: Dict[str, Any] | None = None) -> str:
    if saude is None:
        saude = calcular_saude_roadmap_premium()

    sprint = saude["metricas_roadmap"]["sprint_sugerida"]
    linhas = "\n".join(
        [
            f"""## {idx}. {item['titulo']}

Categoria: {item['categoria']}  
Score: {item['score_prioridade']}/100  
Dor resolvida: {item['dor_resolvida']}  
Critério de sucesso: {item['criterio_sucesso']}  
Janela sugerida: {item.get('sprint_inicio', '')} até {item.get('sprint_fim', '')}
"""
            for idx, item in enumerate(sprint, start=1)
        ]
    ) or "Nenhum item sugerido para sprint."

    return f"""# Sprint Planning Premium — Valoris

Versão: {VERSAO_ROADMAP_PREMIUM_VALORIS}  
Gerado em: {saude["gerado_em"]}

## Objetivo da sprint

Executar poucas melhorias com impacto claro em valor percebido, retenção ou conversão.

{linhas}

## Regra

Não iniciar mais de 3 melhorias ao mesmo tempo.
"""


def gerar_checklist_roadmap_markdown(saude: Dict[str, Any] | None = None) -> str:
    if saude is None:
        saude = calcular_saude_roadmap_premium()

    checklist = "\n".join([f"- [x] {item}" for item in CHECKLIST_ROADMAP])

    return f"""# Checklist Roadmap Premium — Valoris

Versão: {VERSAO_ROADMAP_PREMIUM_VALORIS}  
Gerado em: {saude["gerado_em"]}

## Status

Score Roadmap: {saude["score_roadmap"]}/100  
Decisão: {saude["decisao"]}

## Checklist

{checklist}
"""


def salvar_roadmap_markdown() -> Dict[str, Any]:
    saude = calcular_saude_roadmap_premium()
    CAMINHO_ROADMAP_MD.write_text(gerar_roadmap_markdown(saude), encoding="utf-8")
    return {"ok": True, "arquivo": str(CAMINHO_ROADMAP_MD), "score_roadmap": saude["score_roadmap"]}


def salvar_sprint_markdown() -> Dict[str, Any]:
    saude = calcular_saude_roadmap_premium()
    CAMINHO_SPRINT_MD.write_text(gerar_sprint_markdown(saude), encoding="utf-8")
    return {"ok": True, "arquivo": str(CAMINHO_SPRINT_MD), "score_roadmap": saude["score_roadmap"]}


def salvar_checklist_roadmap_markdown() -> Dict[str, Any]:
    saude = calcular_saude_roadmap_premium()
    CAMINHO_CHECKLIST_MD.write_text(gerar_checklist_roadmap_markdown(saude), encoding="utf-8")
    return {"ok": True, "arquivo": str(CAMINHO_CHECKLIST_MD), "score_roadmap": saude["score_roadmap"]}


def gerar_manifesto_roadmap_premium() -> Dict[str, Any]:
    saude = calcular_saude_roadmap_premium()
    manifesto = {
        "versao": VERSAO_ROADMAP_PREMIUM_VALORIS,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "saude": saude,
        "playbook": PLAYBOOK_ROADMAP,
        "checklist": CHECKLIST_ROADMAP,
        "estrategia": {
            "objetivo": "Transformar feedback do pacote premium em roadmap priorizado.",
            "proxima_versao": "Executar a sprint sugerida com melhorias pequenas, mensuráveis e vendáveis.",
            "regra": "Roadmap bom nasce de feedback real, não de ansiedade por features.",
        },
    }

    CAMINHO_MANIFESTO_ROADMAP.write_text(json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifesto


def _injetar_css_roadmap() -> None:
    st.markdown(
        """
        <style>
            .roadmap-hero {
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
            .roadmap-eyebrow {
                color: #d6b56d;
                font-size: 0.74rem;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                font-weight: 880;
                margin-bottom: 0.35rem;
            }
            .roadmap-title {
                color: #f4f7fb;
                font-size: clamp(1.8rem, 5.5vw, 3.25rem);
                font-weight: 950;
                line-height: 1.02;
                letter-spacing: -0.058em;
                margin-bottom: 0.55rem;
            }
            .roadmap-subtitle {
                color: rgba(244, 247, 251, 0.75);
                font-size: clamp(0.94rem, 2.2vw, 1.06rem);
                line-height: 1.56;
                max-width: 1050px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def renderizar_roadmap_premium_valoris() -> None:
    _injetar_css_roadmap()

    st.markdown(
        f"""
        <div class="roadmap-hero">
            <div class="roadmap-eyebrow">Valoris • Roadmap Premium • v{VERSAO_ROADMAP_PREMIUM_VALORIS}</div>
            <div class="roadmap-title">Feedback vira prioridade. Prioridade vira sprint.</div>
            <div class="roadmap-subtitle">
                Converta objeções, partes confusas e features pedidas em backlog, ranking e sprint sugerida.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    saude = calcular_saude_roadmap_premium()

    st.markdown("### Diagnóstico do roadmap")
    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Score Roadmap", f"{saude['score_roadmap']}/100")

    with col_2:
        st.metric("Backlog", saude["itens_backlog"])

    with col_3:
        st.metric("Alta prioridade", saude["itens_alta_prioridade"])

    with col_4:
        st.metric("Sprint", saude["sprint_sugerida"])

    st.progress(saude["score_roadmap"] / 100)

    if saude["score_roadmap"] >= 82:
        st.success(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    elif saude["itens_backlog"] >= 1:
        st.warning(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    else:
        st.info(f"**{saude['decisao']}** — {saude['proximo_passo']}")

    st.divider()

    st.markdown("### Criar item manual de roadmap")

    with st.form("form_roadmap_premium"):
        col_a, col_b = st.columns(2)

        with col_a:
            titulo = st.text_input("Título", value="Melhorar clareza do pacote premium")
            categoria = st.selectbox("Categoria", CATEGORIAS_ROADMAP)
            origem = st.text_input("Origem", value="Feedback Pacote")
            dor_resolvida = st.text_area("Dor resolvida", height=90)
            criterio_sucesso = st.text_area("Critério de sucesso", height=90)

        with col_b:
            impacto_valor = st.slider("Impacto em valor percebido", 0, 10, 8)
            impacto_retencao = st.slider("Impacto em retenção", 0, 10, 7)
            impacto_comercial = st.slider("Impacto comercial", 0, 10, 7)
            esforco = st.slider("Esforço", 1, 10, 4)
            risco = st.slider("Risco de execução", 0, 10, 3)
            status = st.selectbox("Status", ["Aberto", "Em execução", "Concluído", "Pausado"])
            observacoes = st.text_area("Observações", height=80)

        enviado = st.form_submit_button("Salvar item")

        if enviado:
            registro = salvar_item_roadmap(
                {
                    "titulo": titulo,
                    "categoria": categoria,
                    "origem": origem,
                    "dor_resolvida": dor_resolvida,
                    "impacto_valor": impacto_valor,
                    "impacto_retencao": impacto_retencao,
                    "impacto_comercial": impacto_comercial,
                    "esforco": esforco,
                    "risco": risco,
                    "status": status,
                    "criterio_sucesso": criterio_sucesso,
                    "observacoes": observacoes,
                }
            )
            st.success(f"Item salvo: {registro['titulo']} — score {registro['score_prioridade']}")
            st.rerun()

    st.divider()

    col_btn_1, col_btn_2, col_btn_3, col_btn_4 = st.columns(4)

    with col_btn_1:
        if st.button("Gerar itens do feedback", key="roadmap_feedback"):
            registros = gerar_itens_roadmap_por_feedback()
            st.success(f"{len(registros)} item(ns) gerados a partir do feedback.")
            st.json(registros)
            st.rerun()

    with col_btn_2:
        if st.button("Gerar manifesto", key="roadmap_manifesto"):
            manifesto = gerar_manifesto_roadmap_premium()
            st.success(f"Manifesto gerado: {CAMINHO_MANIFESTO_ROADMAP}")
            st.json({"versao": manifesto["versao"], "score": manifesto["saude"]["score_roadmap"]})

    with col_btn_3:
        if st.button("Salvar roadmap .md", key="roadmap_md"):
            retorno = salvar_roadmap_markdown()
            st.success(f"Roadmap salvo: {retorno['arquivo']}")
            st.json(retorno)

    with col_btn_4:
        if st.button("Salvar sprint .md", key="roadmap_sprint"):
            retorno = salvar_sprint_markdown()
            st.success(f"Sprint salva: {retorno['arquivo']}")
            st.json(retorno)

    if st.button("Salvar checklist .md", key="roadmap_checklist"):
        retorno = salvar_checklist_roadmap_markdown()
        st.success(f"Checklist salvo: {retorno['arquivo']}")
        st.json(retorno)

    if st.button("Salvar decisão Roadmap", key="roadmap_decisao"):
        registro = salvar_decisao_roadmap(saude, observacoes="Decisão gerada pelo roadmap premium.")
        st.success(f"Decisão salva: {registro['decisao']}")
        st.rerun()

    st.divider()

    st.markdown("### Sprint sugerida")
    sprint = saude["metricas_roadmap"]["sprint_sugerida"]
    if sprint:
        st.dataframe(sprint, width="stretch", hide_index=True)
    else:
        st.info("Nenhuma sprint sugerida ainda.")

    st.markdown("### Backlog priorizado")
    backlog = saude["metricas_roadmap"]["backlog"]
    if backlog:
        st.dataframe(backlog, width="stretch", hide_index=True)
    else:
        st.info("Nenhum item de roadmap registrado ainda.")

    st.download_button(
        "Baixar roadmap (.md)",
        data=gerar_roadmap_markdown(saude),
        file_name="ROADMAP_PREMIUM_VALORIS.md",
        mime="text/markdown",
        key="download_roadmap_premium",
    )

    st.download_button(
        "Baixar sprint planning (.md)",
        data=gerar_sprint_markdown(saude),
        file_name="SPRINT_PLANNING_PREMIUM_VALORIS.md",
        mime="text/markdown",
        key="download_sprint_premium",
    )

    st.download_button(
        "Baixar backlog (.csv)",
        data=gerar_csv_backlog_roadmap(),
        file_name="backlog_roadmap_premium_valoris.csv",
        mime="text/csv",
        key="download_backlog_roadmap",
    )


def executar_autoteste_roadmap_premium_valoris() -> List[Dict[str, str]]:
    saude = calcular_saude_roadmap_premium()

    return [
        {
            "teste": "versao_roadmap_premium",
            "status": "OK" if VERSAO_ROADMAP_PREMIUM_VALORIS == "3.8.90" else "FALHA",
            "detalhe": VERSAO_ROADMAP_PREMIUM_VALORIS,
        },
        {
            "teste": "score_roadmap",
            "status": "OK" if 0 <= saude["score_roadmap"] <= 100 else "FALHA",
            "detalhe": str(saude["score_roadmap"]),
        },
        {
            "teste": "roadmap_markdown",
            "status": "OK" if "# Roadmap Premium" in gerar_roadmap_markdown(saude) else "FALHA",
            "detalhe": "gerar_roadmap_markdown",
        },
        {
            "teste": "renderizador",
            "status": "OK" if callable(renderizar_roadmap_premium_valoris) else "FALHA",
            "detalhe": "renderizar_roadmap_premium_valoris",
        },
    ]
