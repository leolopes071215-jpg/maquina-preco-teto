# comparador_setorial_valoris.py

from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

import streamlit as st


VERSAO_COMPARADOR_SETORIAL_VALORIS = "3.8.86"

CAMINHO_RANKING_COMPARADOR = Path("ranking_comparador_setorial_valoris.csv")
CAMINHO_DECISOES_COMPARADOR = Path("decisoes_comparador_setorial_valoris.csv")
CAMINHO_MANIFESTO_COMPARADOR = Path("manifesto_comparador_setorial_valoris.json")
CAMINHO_RELATORIO_COMPARADOR_MD = Path("RELATORIO_COMPARADOR_SETORIAL_VALORIS.md")
CAMINHO_PLAYBOOK_COMPARADOR_MD = Path("PLAYBOOK_COMPARADOR_SETORIAL_VALORIS.md")
CAMINHO_CHECKLIST_COMPARADOR_MD = Path("CHECKLIST_COMPARADOR_SETORIAL_VALORIS.md")

CAMPOS_RANKING_COMPARADOR = [
    "id",
    "data_registro",
    "ticker",
    "empresa",
    "setor",
    "preco_atual",
    "preco_teto",
    "margem_seguranca",
    "status_oportunidade",
    "prioridade",
    "score_preco",
    "score_prioridade",
    "score_tese",
    "score_risco",
    "score_setorial",
    "ranking",
    "decisao",
    "proximo_passo",
]

CAMPOS_DECISAO_COMPARADOR = [
    "id",
    "data_registro",
    "score_comparador",
    "score_cobertura",
    "score_ranking",
    "score_confianca",
    "setores_total",
    "ativos_total",
    "ativos_ranqueados",
    "melhor_ticker",
    "melhor_setor",
    "risco",
    "decisao",
    "proximo_passo",
    "observacoes",
]

PLAYBOOK_COMPARADOR = [
    {
        "etapa": "Agrupar por setor",
        "objetivo": "Evitar comparar empresas com motores econômicos diferentes.",
        "acao": "Separar ativos por setor e analisar concorrentes dentro do mesmo grupo.",
        "sinal_sucesso": "Cada setor tem pelo menos uma tese comparável.",
    },
    {
        "etapa": "Comparar preço versus teto",
        "objetivo": "Identificar onde existe maior margem de segurança.",
        "acao": "Usar margem de segurança e status da oportunidade.",
        "sinal_sucesso": "Ranking mostra quais ativos estão mais próximos de oportunidade.",
    },
    {
        "etapa": "Ponderar tese e risco",
        "objetivo": "Evitar escolher apenas o ativo mais barato.",
        "acao": "Considerar tese resumida, principal risco e prioridade.",
        "sinal_sucesso": "Ativo barato, mas com tese fraca, não lidera automaticamente.",
    },
    {
        "etapa": "Decidir próximo estudo",
        "objetivo": "Transformar watchlist em ação analítica.",
        "acao": "Escolher qual empresa estudar, revisar ou descartar primeiro.",
        "sinal_sucesso": "Fundador sabe o próximo ativo a analisar.",
    },
    {
        "etapa": "Atualizar após eventos",
        "objetivo": "Manter comparação viva.",
        "acao": "Revisar ranking após resultado trimestral, mudança de preço ou tese.",
        "sinal_sucesso": "Comparador vira rotina de tomada de decisão.",
    },
]

CHECKLIST_COMPARADOR = [
    "Ativos carregados da watchlist",
    "Setores identificados",
    "Margem de segurança calculada",
    "Status da oportunidade considerado",
    "Prioridade considerada",
    "Tese resumida considerada",
    "Principal risco considerado",
    "Ranking gerado",
    "Melhor ativo identificado",
    "Relatório comparativo gerado",
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


def _calcular_saude_watchlist() -> Dict[str, Any]:
    try:
        from watchlist_fundadores_valoris import calcular_saude_watchlist_fundadores

        return calcular_saude_watchlist_fundadores()
    except Exception as erro:
        return {"score_watchlist": 0, "erro": str(erro)}


def _score_preco(margem: float, status: str) -> int:
    score = 0

    if margem >= 25:
        score += 45
    elif margem >= 15:
        score += 38
    elif margem >= 5:
        score += 25
    elif margem >= -5:
        score += 14
    else:
        score += 4

    if status == "Abaixo do preço teto":
        score += 35
    elif status == "Próximo do preço teto":
        score += 22
    elif status == "Acima do preço teto":
        score += 8
    elif status == "Revisar premissas":
        score += 5

    return min(100, score)


def _score_prioridade(valor: str) -> int:
    mapa = {"Alta": 100, "Média": 68, "Baixa": 38}
    return mapa.get(valor, 50)


def _score_tese(texto: str) -> int:
    texto = _limpar_texto(texto)

    if len(texto) >= 220:
        return 100
    if len(texto) >= 140:
        return 82
    if len(texto) >= 80:
        return 64
    if len(texto) >= 30:
        return 42
    return 15


def _score_risco(texto: str) -> int:
    texto = _limpar_texto(texto)

    if len(texto) >= 160:
        return 92
    if len(texto) >= 90:
        return 74
    if len(texto) >= 35:
        return 55
    if len(texto) > 0:
        return 32
    return 10


def _decisao_por_score(score: int, margem: float, status: str) -> Dict[str, str]:
    if score >= 82 and margem >= 10:
        return {
            "decisao": "Prioridade alta para estudo",
            "proximo_passo": "Aprofundar tese, revisar premissas e comparar com pares antes de qualquer decisão.",
        }

    if score >= 70:
        return {
            "decisao": "Boa candidata para acompanhar",
            "proximo_passo": "Manter na watchlist e revisar após próximo evento relevante.",
        }

    if status == "Revisar premissas":
        return {
            "decisao": "Premissas insuficientes",
            "proximo_passo": "Completar preço teto, tese, risco e próximo evento antes de ranquear.",
        }

    if score >= 55:
        return {
            "decisao": "Acompanhar com cautela",
            "proximo_passo": "Revisar tese ou aguardar margem de segurança melhor.",
        }

    return {
        "decisao": "Baixa prioridade no momento",
        "proximo_passo": "Só revisitar se preço, tese ou risco mudarem de forma relevante.",
    }


def gerar_ranking_comparador_setorial() -> List[Dict[str, Any]]:
    itens = _carregar_watchlist()
    ranking = []

    for item in itens:
        margem = _to_float(item.get("margem_seguranca"), 0.0)
        status = item.get("status_oportunidade", "")
        prioridade = item.get("prioridade", "")

        score_preco = _score_preco(margem, status)
        score_prioridade = _score_prioridade(prioridade)
        score_tese = _score_tese(item.get("tese_resumo", ""))
        score_risco = _score_risco(item.get("principal_risco", ""))

        score_setorial = int(round(
            score_preco * 0.36
            + score_prioridade * 0.20
            + score_tese * 0.24
            + score_risco * 0.20
        ))

        decisao = _decisao_por_score(score_setorial, margem, status)

        ranking.append(
            {
                "id": item.get("id", str(uuid4())[:8]),
                "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "ticker": item.get("ticker", ""),
                "empresa": item.get("empresa", ""),
                "setor": item.get("setor", "não informado"),
                "preco_atual": item.get("preco_atual", ""),
                "preco_teto": item.get("preco_teto", ""),
                "margem_seguranca": margem,
                "status_oportunidade": status,
                "prioridade": prioridade,
                "score_preco": score_preco,
                "score_prioridade": score_prioridade,
                "score_tese": score_tese,
                "score_risco": score_risco,
                "score_setorial": score_setorial,
                "ranking": 0,
                "decisao": decisao["decisao"],
                "proximo_passo": decisao["proximo_passo"],
            }
        )

    ranking.sort(key=lambda item: item["score_setorial"], reverse=True)

    for posicao, item in enumerate(ranking, start=1):
        item["ranking"] = posicao

    return ranking


def salvar_ranking_comparador_setorial() -> Dict[str, Any]:
    ranking = gerar_ranking_comparador_setorial()
    _garantir_csv(CAMINHO_RANKING_COMPARADOR, CAMPOS_RANKING_COMPARADOR)

    with CAMINHO_RANKING_COMPARADOR.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_RANKING_COMPARADOR)
        escritor.writeheader()

        for item in ranking:
            escritor.writerow({campo: item.get(campo, "") for campo in CAMPOS_RANKING_COMPARADOR})

    return {
        "ok": True,
        "arquivo": str(CAMINHO_RANKING_COMPARADOR),
        "ativos_ranqueados": len(ranking),
        "melhor_ticker": ranking[0]["ticker"] if ranking else "",
    }


def carregar_ranking_comparador() -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_RANKING_COMPARADOR, CAMPOS_RANKING_COMPARADOR)

    with CAMINHO_RANKING_COMPARADOR.open("r", newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def carregar_decisoes_comparador() -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_DECISOES_COMPARADOR, CAMPOS_DECISAO_COMPARADOR)

    with CAMINHO_DECISOES_COMPARADOR.open("r", newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def gerar_csv_ranking_comparador() -> str:
    _garantir_csv(CAMINHO_RANKING_COMPARADOR, CAMPOS_RANKING_COMPARADOR)
    return CAMINHO_RANKING_COMPARADOR.read_text(encoding="utf-8")


def gerar_csv_decisoes_comparador() -> str:
    _garantir_csv(CAMINHO_DECISOES_COMPARADOR, CAMPOS_DECISAO_COMPARADOR)
    return CAMINHO_DECISOES_COMPARADOR.read_text(encoding="utf-8")


def calcular_metricas_comparador() -> Dict[str, Any]:
    itens = _carregar_watchlist()
    ranking = gerar_ranking_comparador_setorial()

    setores = defaultdict(int)
    for item in itens:
        setores[item.get("setor", "não informado")] += 1

    setores_com_2_ativos = sum(1 for _, qtd in setores.items() if qtd >= 2)

    melhor = ranking[0] if ranking else {}
    oportunidades = [item for item in ranking if item.get("decisao") == "Prioridade alta para estudo"]
    revisar = [item for item in ranking if item.get("status_oportunidade") == "Revisar premissas"]

    return {
        "ativos_total": len(itens),
        "ativos_ranqueados": len(ranking),
        "setores_total": len(setores),
        "setores_com_2_ativos": setores_com_2_ativos,
        "oportunidades_prioritarias": len(oportunidades),
        "ativos_revisar": len(revisar),
        "melhor_ticker": melhor.get("ticker", ""),
        "melhor_empresa": melhor.get("empresa", ""),
        "melhor_setor": melhor.get("setor", ""),
        "melhor_score": melhor.get("score_setorial", 0),
        "setores": dict(setores),
        "ranking": ranking,
    }


def calcular_saude_comparador_setorial() -> Dict[str, Any]:
    metricas = calcular_metricas_comparador()
    watchlist = _calcular_saude_watchlist()

    score_cobertura = 0
    score_cobertura += 25 if metricas["ativos_total"] >= 2 else 0
    score_cobertura += 25 if metricas["ativos_total"] >= 4 else 0
    score_cobertura += 20 if metricas["setores_total"] >= 2 else 0
    score_cobertura += 20 if metricas["setores_com_2_ativos"] >= 1 else 0
    score_cobertura += 10 if metricas["ativos_revisar"] == 0 and metricas["ativos_total"] > 0 else 0
    score_cobertura = min(100, score_cobertura)

    score_ranking = 0
    score_ranking += 30 if metricas["ativos_ranqueados"] >= 1 else 0
    score_ranking += 25 if metricas["melhor_score"] >= 75 else 0
    score_ranking += 20 if metricas["oportunidades_prioritarias"] >= 1 else 0
    score_ranking += 15 if metricas["ativos_ranqueados"] >= 3 else 0
    score_ranking += 10 if bool(metricas["melhor_ticker"]) else 0
    score_ranking = min(100, score_ranking)

    score_confianca = 0
    score_confianca += 20 if len(PLAYBOOK_COMPARADOR) >= 5 else 0
    score_confianca += 20 if len(CHECKLIST_COMPARADOR) >= 10 else 0
    score_confianca += 20 if metricas["ativos_revisar"] == 0 and metricas["ativos_total"] > 0 else 0
    score_confianca += 20 if int(watchlist.get("score_watchlist", 0) or 0) >= 70 else 0
    score_confianca += 20 if metricas["setores_com_2_ativos"] >= 1 else 0
    score_confianca = min(100, score_confianca)

    score_watchlist = int(watchlist.get("score_watchlist", 0) or 0)

    score_comparador = int(round(
        score_cobertura * 0.30
        + score_ranking * 0.30
        + score_confianca * 0.22
        + score_watchlist * 0.18
    ))

    if metricas["ativos_total"] >= 4 and metricas["setores_com_2_ativos"] >= 1 and score_comparador >= 82:
        risco = "Médio controlado"
        decisao = "Comparador pronto para orientar próximos estudos"
        proximo_passo = "Usar o ranking para escolher qual empresa estudar primeiro e atualizar após eventos."
    elif metricas["ativos_total"] >= 2:
        risco = "Médio"
        decisao = "Comparador funcional, mas precisa de mais pares por setor"
        proximo_passo = "Adicionar concorrentes aos setores mais importantes da watchlist."
    elif metricas["ativos_total"] >= 1:
        risco = "Médio/Alto"
        decisao = "Ranking inicial existe, mas comparação ainda é fraca"
        proximo_passo = "Adicionar pelo menos mais uma empresa comparável no mesmo setor."
    else:
        risco = "Alto"
        decisao = "Comparador ainda sem base"
        proximo_passo = "Registrar ativos na watchlist antes de comparar."

    return {
        "versao": VERSAO_COMPARADOR_SETORIAL_VALORIS,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score_comparador": max(0, min(100, score_comparador)),
        "score_cobertura": score_cobertura,
        "score_ranking": score_ranking,
        "score_confianca": score_confianca,
        "score_watchlist": score_watchlist,
        "setores_total": metricas["setores_total"],
        "ativos_total": metricas["ativos_total"],
        "ativos_ranqueados": metricas["ativos_ranqueados"],
        "melhor_ticker": metricas["melhor_ticker"],
        "melhor_setor": metricas["melhor_setor"],
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo_passo,
        "metricas_comparador": metricas,
        "playbook": PLAYBOOK_COMPARADOR,
        "checklist": CHECKLIST_COMPARADOR,
        "watchlist": watchlist,
    }


def salvar_decisao_comparador(saude: Dict[str, Any], observacoes: str = "") -> Dict[str, str]:
    _garantir_csv(CAMINHO_DECISOES_COMPARADOR, CAMPOS_DECISAO_COMPARADOR)

    registro = {
        "id": str(uuid4())[:8],
        "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score_comparador": str(saude.get("score_comparador", "")),
        "score_cobertura": str(saude.get("score_cobertura", "")),
        "score_ranking": str(saude.get("score_ranking", "")),
        "score_confianca": str(saude.get("score_confianca", "")),
        "setores_total": str(saude.get("setores_total", "")),
        "ativos_total": str(saude.get("ativos_total", "")),
        "ativos_ranqueados": str(saude.get("ativos_ranqueados", "")),
        "melhor_ticker": _limpar_texto(saude.get("melhor_ticker")),
        "melhor_setor": _limpar_texto(saude.get("melhor_setor")),
        "risco": _limpar_texto(saude.get("risco")),
        "decisao": _limpar_texto(saude.get("decisao")),
        "proximo_passo": _limpar_texto(saude.get("proximo_passo")),
        "observacoes": _limpar_texto(observacoes),
    }

    with CAMINHO_DECISOES_COMPARADOR.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISAO_COMPARADOR)
        escritor.writerow(registro)

    return registro


def gerar_relatorio_comparador_markdown(saude: Dict[str, Any] | None = None) -> str:
    if saude is None:
        saude = calcular_saude_comparador_setorial()

    ranking = saude["metricas_comparador"]["ranking"]

    linhas_ranking = "\n".join(
        [
            f"- **#{item['ranking']} {item['ticker']} — {item['empresa']}** ({item['setor']}): score {item['score_setorial']}/100, margem {item['margem_seguranca']}%, status {item['status_oportunidade']}. Decisão: {item['decisao']}."
            for item in ranking[:20]
        ]
    ) or "- Nenhum ativo ranqueado."

    setores = "\n".join(
        [
            f"- {setor}: {qtd} ativo(s)"
            for setor, qtd in saude["metricas_comparador"]["setores"].items()
        ]
    ) or "- Nenhum setor identificado."

    return f"""# Relatório Comparador Setorial — Valoris

Versão: {VERSAO_COMPARADOR_SETORIAL_VALORIS}  
Gerado em: {saude["gerado_em"]}

## Resumo executivo

Score Comparador: {saude["score_comparador"]}/100  
Ativos ranqueados: {saude["ativos_ranqueados"]}  
Setores: {saude["setores_total"]}  
Melhor ticker: {saude["melhor_ticker"] or "pendente"}  
Decisão: {saude["decisao"]}  
Próximo passo: {saude["proximo_passo"]}

## Ranking

{linhas_ranking}

## Cobertura por setor

{setores}

## Leitura

O comparador não deve escolher automaticamente a melhor ação. Ele organiza prioridade de estudo, margem de segurança, tese e risco para melhorar a decisão do investidor.
"""


def gerar_playbook_comparador_markdown(saude: Dict[str, Any] | None = None) -> str:
    if saude is None:
        saude = calcular_saude_comparador_setorial()

    etapas = "\n\n".join(
        [
            f"""## {item['etapa']}

**Objetivo:** {item['objetivo']}  
**Ação:** {item['acao']}  
**Sinal de sucesso:** {item['sinal_sucesso']}
"""
            for item in PLAYBOOK_COMPARADOR
        ]
    )

    return f"""# Playbook Comparador Setorial — Valoris

Versão: {VERSAO_COMPARADOR_SETORIAL_VALORIS}  
Gerado em: {saude["gerado_em"]}

## Princípio

Comparar empresas só faz sentido quando preço, tese, risco e setor são considerados juntos.

## Etapas

{etapas}
"""


def gerar_checklist_comparador_markdown(saude: Dict[str, Any] | None = None) -> str:
    if saude is None:
        saude = calcular_saude_comparador_setorial()

    checklist = "\n".join([f"- [x] {item}" for item in CHECKLIST_COMPARADOR])

    return f"""# Checklist Comparador Setorial — Valoris

Versão: {VERSAO_COMPARADOR_SETORIAL_VALORIS}  
Gerado em: {saude["gerado_em"]}

## Status

Score Comparador: {saude["score_comparador"]}/100  
Decisão: {saude["decisao"]}

## Checklist

{checklist}
"""


def salvar_relatorio_comparador_markdown() -> Dict[str, Any]:
    saude = calcular_saude_comparador_setorial()
    CAMINHO_RELATORIO_COMPARADOR_MD.write_text(gerar_relatorio_comparador_markdown(saude), encoding="utf-8")
    return {"ok": True, "arquivo": str(CAMINHO_RELATORIO_COMPARADOR_MD), "score_comparador": saude["score_comparador"]}


def salvar_playbook_comparador_markdown() -> Dict[str, Any]:
    saude = calcular_saude_comparador_setorial()
    CAMINHO_PLAYBOOK_COMPARADOR_MD.write_text(gerar_playbook_comparador_markdown(saude), encoding="utf-8")
    return {"ok": True, "arquivo": str(CAMINHO_PLAYBOOK_COMPARADOR_MD), "score_comparador": saude["score_comparador"]}


def salvar_checklist_comparador_markdown() -> Dict[str, Any]:
    saude = calcular_saude_comparador_setorial()
    CAMINHO_CHECKLIST_COMPARADOR_MD.write_text(gerar_checklist_comparador_markdown(saude), encoding="utf-8")
    return {"ok": True, "arquivo": str(CAMINHO_CHECKLIST_COMPARADOR_MD), "score_comparador": saude["score_comparador"]}


def gerar_manifesto_comparador_setorial() -> Dict[str, Any]:
    saude = calcular_saude_comparador_setorial()
    manifesto = {
        "versao": VERSAO_COMPARADOR_SETORIAL_VALORIS,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "saude": saude,
        "playbook": PLAYBOOK_COMPARADOR,
        "checklist": CHECKLIST_COMPARADOR,
        "estrategia": {
            "objetivo": "Transformar watchlist em ranking de prioridade de estudo.",
            "proxima_versao": "Relatório Premium v2 ou dados reais controlados, conforme necessidade dos fundadores.",
            "regra": "Ranking orienta estudo; não substitui julgamento nem recomenda compra.",
        },
    }

    CAMINHO_MANIFESTO_COMPARADOR.write_text(json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifesto


def _injetar_css_comparador() -> None:
    st.markdown(
        """
        <style>
            .comparador-hero {
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
            .comparador-eyebrow {
                color: #d6b56d;
                font-size: 0.74rem;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                font-weight: 880;
                margin-bottom: 0.35rem;
            }
            .comparador-title {
                color: #f4f7fb;
                font-size: clamp(1.8rem, 5.5vw, 3.25rem);
                font-weight: 950;
                line-height: 1.02;
                letter-spacing: -0.058em;
                margin-bottom: 0.55rem;
            }
            .comparador-subtitle {
                color: rgba(244, 247, 251, 0.75);
                font-size: clamp(0.94rem, 2.2vw, 1.06rem);
                line-height: 1.56;
                max-width: 1050px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def renderizar_comparador_setorial_valoris() -> None:
    _injetar_css_comparador()

    st.markdown(
        f"""
        <div class="comparador-hero">
            <div class="comparador-eyebrow">Valoris • Comparador Setorial • v{VERSAO_COMPARADOR_SETORIAL_VALORIS}</div>
            <div class="comparador-title">Ranking de prioridade, não recomendação cega.</div>
            <div class="comparador-subtitle">
                Compare ativos da watchlist por setor, margem de segurança, prioridade, tese e risco para decidir
                qual empresa estudar primeiro.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    saude = calcular_saude_comparador_setorial()

    st.markdown("### Diagnóstico do comparador")
    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Score Comparador", f"{saude['score_comparador']}/100")

    with col_2:
        st.metric("Ativos ranqueados", saude["ativos_ranqueados"])

    with col_3:
        st.metric("Setores", saude["setores_total"])

    with col_4:
        st.metric("Melhor ticker", saude["melhor_ticker"] or "Pendente")

    st.progress(saude["score_comparador"] / 100)

    if saude["score_comparador"] >= 82:
        st.success(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    elif saude["ativos_total"] >= 1:
        st.warning(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    else:
        st.info(f"**{saude['decisao']}** — {saude['proximo_passo']}")

    st.divider()

    ranking = gerar_ranking_comparador_setorial()

    st.markdown("### Ranking comparativo")
    st.dataframe(ranking, width="stretch", hide_index=True)

    st.markdown("### Cobertura por setor")
    st.json(saude["metricas_comparador"]["setores"])

    st.divider()

    col_btn_1, col_btn_2, col_btn_3, col_btn_4 = st.columns(4)

    with col_btn_1:
        if st.button("Gerar ranking CSV", key="comparador_ranking_csv"):
            retorno = salvar_ranking_comparador_setorial()
            st.success(f"Ranking salvo: {retorno['arquivo']}")
            st.json(retorno)

    with col_btn_2:
        if st.button("Gerar manifesto", key="comparador_manifesto"):
            manifesto = gerar_manifesto_comparador_setorial()
            st.success(f"Manifesto gerado: {CAMINHO_MANIFESTO_COMPARADOR}")
            st.json({"versao": manifesto["versao"], "score": manifesto["saude"]["score_comparador"]})

    with col_btn_3:
        if st.button("Salvar relatório .md", key="comparador_relatorio"):
            retorno = salvar_relatorio_comparador_markdown()
            st.success(f"Relatório salvo: {retorno['arquivo']}")
            st.json(retorno)

    with col_btn_4:
        if st.button("Salvar playbook .md", key="comparador_playbook"):
            retorno = salvar_playbook_comparador_markdown()
            st.success(f"Playbook salvo: {retorno['arquivo']}")
            st.json(retorno)

    if st.button("Salvar checklist .md", key="comparador_checklist"):
        retorno = salvar_checklist_comparador_markdown()
        st.success(f"Checklist salvo: {retorno['arquivo']}")
        st.json(retorno)

    if st.button("Salvar decisão Comparador", key="comparador_decisao"):
        registro = salvar_decisao_comparador(saude, observacoes="Decisão gerada pelo comparador setorial.")
        st.success(f"Decisão salva: {registro['decisao']}")
        st.rerun()

    st.download_button(
        "Baixar relatório comparador (.md)",
        data=gerar_relatorio_comparador_markdown(saude),
        file_name="RELATORIO_COMPARADOR_SETORIAL_VALORIS.md",
        mime="text/markdown",
        key="download_relatorio_comparador",
    )

    st.download_button(
        "Baixar ranking comparador (.csv)",
        data=gerar_csv_ranking_comparador(),
        file_name="ranking_comparador_setorial_valoris.csv",
        mime="text/csv",
        key="download_ranking_comparador",
    )

    st.download_button(
        "Baixar decisões comparador (.csv)",
        data=gerar_csv_decisoes_comparador(),
        file_name="decisoes_comparador_setorial_valoris.csv",
        mime="text/csv",
        key="download_decisoes_comparador",
    )


def executar_autoteste_comparador_setorial_valoris() -> List[Dict[str, str]]:
    saude = calcular_saude_comparador_setorial()

    return [
        {
            "teste": "versao_comparador_setorial",
            "status": "OK" if VERSAO_COMPARADOR_SETORIAL_VALORIS == "3.8.86" else "FALHA",
            "detalhe": VERSAO_COMPARADOR_SETORIAL_VALORIS,
        },
        {
            "teste": "score_comparador",
            "status": "OK" if 0 <= saude["score_comparador"] <= 100 else "FALHA",
            "detalhe": str(saude["score_comparador"]),
        },
        {
            "teste": "ranking",
            "status": "OK" if isinstance(gerar_ranking_comparador_setorial(), list) else "FALHA",
            "detalhe": str(len(gerar_ranking_comparador_setorial())),
        },
        {
            "teste": "renderizador",
            "status": "OK" if callable(renderizar_comparador_setorial_valoris) else "FALHA",
            "detalhe": "renderizar_comparador_setorial_valoris",
        },
    ]
