# analise_inteligente_valoris.py
# Valoris — Análise Inteligente v3.9.5
# ------------------------------------------------------------
# Objetivo:
# - Criar uma página central e mais sofisticada para a jornada de análise.
# - Unir Motor, Histórico, Watchlist e Relatório em uma visão executiva.
# - Dar ao usuário uma leitura clara: o que analisar, acompanhar, revisar ou transformar em dossiê.
# ------------------------------------------------------------

from __future__ import annotations

import csv
import json
from collections import Counter, deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st


VERSAO_ANALISE_INTELIGENTE_VALORIS = "3.9.5"

CAMINHO_ANALISES_MOTOR = Path("analises_motor_ativos_valoris.csv")
CAMINHO_WATCHLIST = Path("watchlist_fundadores_valoris.csv")
CAMINHO_DECISOES = Path("decisoes_analise_inteligente_valoris.csv")
CAMINHO_RELATORIO = Path("RELATORIO_ANALISE_INTELIGENTE_VALORIS.md")
CAMINHO_MANIFESTO = Path("manifesto_analise_inteligente_valoris.json")

CAMPOS_ANALISES = [
    "data_hora",
    "ticker",
    "nome_empresa",
    "setor",
    "preco_atual",
    "preco_teto",
    "margem_seguranca_atual",
    "score_qualidade",
    "score_risco",
    "score_valor",
    "score_final",
    "decisao",
    "nivel_conviccao",
    "modelo_preco_teto",
    "observacao",
]

CAMPOS_DECISOES = [
    "data_hora",
    "ticker",
    "empresa",
    "score_inteligente",
    "classificacao",
    "acao_recomendada",
    "proximo_passo",
    "observacao",
]


def _agora_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat(sep=" ")


def _txt(valor: Any) -> str:
    return "" if valor is None else str(valor).strip()


def _float(valor: Any, padrao: float = 0.0) -> float:
    try:
        if valor is None:
            return padrao

        if isinstance(valor, str):
            valor = valor.replace("R$", "").replace("%", "").replace(".", "").replace(",", ".").strip()

            if valor == "":
                return padrao

        return float(valor)
    except Exception:
        return padrao


def _moeda(valor: Any) -> str:
    numero = _float(valor)
    return f"R$ {numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _pct(valor: Any) -> str:
    return f"{_float(valor):.1f}%"


def _limitar(valor: float, minimo: float = 0.0, maximo: float = 100.0) -> float:
    return max(minimo, min(maximo, valor))


def _garantir_csv(caminho: Path, campos: List[str]) -> None:
    if caminho.exists():
        return

    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()


def carregar_csv_seguro(caminho: Path, campos: List[str], max_registros: int = 800) -> List[Dict[str, str]]:
    _garantir_csv(caminho, campos)

    try:
        with caminho.open("r", newline="", encoding="utf-8") as arquivo:
            leitor = csv.DictReader(arquivo)
            return list(deque(leitor, maxlen=max_registros))
    except Exception:
        return []


def carregar_analises_motor(max_registros: int = 800) -> List[Dict[str, str]]:
    return carregar_csv_seguro(CAMINHO_ANALISES_MOTOR, CAMPOS_ANALISES, max_registros=max_registros)


def carregar_watchlist(max_registros: int = 800) -> List[Dict[str, str]]:
    try:
        from watchlist_fundadores_valoris import carregar_watchlist_fundadores

        return carregar_watchlist_fundadores()[-max_registros:]
    except Exception:
        if not CAMINHO_WATCHLIST.exists():
            return []

        try:
            with CAMINHO_WATCHLIST.open("r", newline="", encoding="utf-8") as arquivo:
                leitor = csv.DictReader(arquivo)
                return list(deque(leitor, maxlen=max_registros))
        except Exception:
            return []


def carregar_metricas_relatorio() -> Dict[str, Any]:
    try:
        from integracao_motor_relatorio_valoris import calcular_metricas_integracao_relatorio

        return calcular_metricas_integracao_relatorio()
    except Exception as erro:
        return {"erro": str(erro), "score_integracao_relatorio": 0}


def carregar_metricas_watchlist() -> Dict[str, Any]:
    try:
        from watchlist_fundadores_valoris import calcular_saude_watchlist_fundadores

        return calcular_saude_watchlist_fundadores()
    except Exception as erro:
        return {"erro": str(erro), "score_watchlist": 0}


def carregar_metricas_historico() -> Dict[str, Any]:
    try:
        from historico_analises_valoris import calcular_metricas_historico, classificar_saude_historico

        registros = carregar_analises_motor()
        metricas = calcular_metricas_historico(registros)
        saude = classificar_saude_historico(metricas)

        return {"metricas": metricas, "saude": saude}
    except Exception as erro:
        return {"erro": str(erro), "metricas": {}, "saude": {"score_historico": 0}}


def ticker_na_watchlist(ticker: str, watchlist: Optional[List[Dict[str, str]]] = None) -> bool:
    ticker = _txt(ticker).upper()

    if not ticker:
        return False

    if watchlist is None:
        watchlist = carregar_watchlist()

    tickers = {_txt(item.get("ticker")).upper() for item in watchlist}

    return ticker in tickers


def calcular_score_inteligente(analise: Dict[str, str], presente_watchlist: bool = False) -> float:
    score_final = _float(analise.get("score_final"))
    score_qualidade = _float(analise.get("score_qualidade"))
    score_risco = _float(analise.get("score_risco"))
    score_valor = _float(analise.get("score_valor"))
    margem = _float(analise.get("margem_seguranca_atual"))
    preco_teto = _float(analise.get("preco_teto"))

    score_margem = 0.0

    if preco_teto > 0:
        if margem >= 25:
            score_margem = 100
        elif margem >= 15:
            score_margem = 82
        elif margem >= 5:
            score_margem = 65
        elif margem >= -5:
            score_margem = 42
        else:
            score_margem = 18

    bonus_acompanhamento = 8 if presente_watchlist else 0

    score = (
        score_final * 0.34
        + score_qualidade * 0.22
        + score_risco * 0.18
        + score_valor * 0.14
        + score_margem * 0.12
        + bonus_acompanhamento
    )

    return round(_limitar(score), 1)


def classificar_analise_inteligente(analise: Dict[str, str], presente_watchlist: bool = False) -> Dict[str, Any]:
    score = calcular_score_inteligente(analise, presente_watchlist=presente_watchlist)
    decisao_motor = _txt(analise.get("decisao")).upper()
    margem = _float(analise.get("margem_seguranca_atual"))
    risco = _float(analise.get("score_risco"))
    qualidade = _float(analise.get("score_qualidade"))
    preco_teto = _float(analise.get("preco_teto"))

    if preco_teto <= 0:
        classificacao = "Premissas incompletas"
        acao = "Revisar dados"
        proximo = "Voltar ao Motor e preencher premissas suficientes para preço teto positivo."
    elif risco < 35:
        classificacao = "Risco elevado"
        acao = "Não avançar"
        proximo = "Ler riscos, balanço e tese antes de colocar em watchlist ou relatório."
    elif qualidade < 45:
        classificacao = "Qualidade fraca"
        acao = "Monitorar com cautela"
        proximo = "Validar se a empresa merece estar no radar antes de aprofundar."
    elif "COMPRA" in decisao_motor and score >= 78 and margem >= 5:
        classificacao = "Alta prioridade"
        acao = "Gerar dossiê e acompanhar"
        proximo = "Enviar para Watchlist, gerar dossiê premium e definir data de revisão."
    elif score >= 68:
        classificacao = "Boa candidata"
        acao = "Acompanhar"
        proximo = "Enviar para Watchlist e revisar após próximo evento relevante."
    elif score >= 55:
        classificacao = "Neutra"
        acao = "Esperar melhor preço ou dados"
        proximo = "Manter no histórico, mas não priorizar dossiê premium agora."
    else:
        classificacao = "Baixa prioridade"
        acao = "Não priorizar"
        proximo = "Só revisitar se preço, qualidade ou tese mudarem."

    if presente_watchlist and classificacao in {"Alta prioridade", "Boa candidata"}:
        proximo = "Ativo já está na Watchlist. Próximo passo: gerar dossiê ou revisar alerta."

    return {
        "score_inteligente": score,
        "classificacao": classificacao,
        "acao_recomendada": acao,
        "proximo_passo": proximo,
        "ja_na_watchlist": presente_watchlist,
    }


def gerar_ranking_inteligente() -> List[Dict[str, Any]]:
    analises = carregar_analises_motor()
    watchlist = carregar_watchlist()

    linhas: List[Dict[str, Any]] = []

    for analise in analises:
        ticker = _txt(analise.get("ticker")).upper()

        if not ticker:
            continue

        presente = ticker_na_watchlist(ticker, watchlist=watchlist)
        inteligencia = classificar_analise_inteligente(analise, presente_watchlist=presente)

        linhas.append(
            {
                "data_hora": analise.get("data_hora", ""),
                "ticker": ticker,
                "empresa": analise.get("nome_empresa", ""),
                "setor": analise.get("setor", ""),
                "preco_atual": _float(analise.get("preco_atual")),
                "preco_teto": _float(analise.get("preco_teto")),
                "margem_seguranca": _float(analise.get("margem_seguranca_atual")),
                "score_motor": _float(analise.get("score_final")),
                "score_qualidade": _float(analise.get("score_qualidade")),
                "score_risco": _float(analise.get("score_risco")),
                "score_valor": _float(analise.get("score_valor")),
                "score_inteligente": inteligencia["score_inteligente"],
                "classificacao": inteligencia["classificacao"],
                "acao_recomendada": inteligencia["acao_recomendada"],
                "proximo_passo": inteligencia["proximo_passo"],
                "ja_na_watchlist": "Sim" if presente else "Não",
                "decisao_motor": analise.get("decisao", ""),
            }
        )

    linhas.sort(key=lambda item: item["score_inteligente"], reverse=True)

    for indice, item in enumerate(linhas, start=1):
        item["ranking"] = indice

    return linhas


def calcular_metricas_analise_inteligente() -> Dict[str, Any]:
    ranking = gerar_ranking_inteligente()
    watchlist = carregar_watchlist()
    historico = carregar_metricas_historico()
    relatorio = carregar_metricas_relatorio()
    watchlist_saude = carregar_metricas_watchlist()

    total = len(ranking)
    alta = len([item for item in ranking if item["classificacao"] == "Alta prioridade"])
    boas = len([item for item in ranking if item["classificacao"] == "Boa candidata"])
    incompletas = len([item for item in ranking if item["classificacao"] == "Premissas incompletas"])
    na_watchlist = len([item for item in ranking if item["ja_na_watchlist"] == "Sim"])
    score_medio = round(sum(item["score_inteligente"] for item in ranking) / total, 1) if total else 0.0

    score_historico = int(historico.get("saude", {}).get("score_historico", 0) or 0)
    score_relatorio = int(relatorio.get("score_integracao_relatorio", 0) or 0)
    score_watchlist = int(watchlist_saude.get("score_watchlist", 0) or 0)

    score_produto = int(round(
        min(100, total * 8) * 0.24
        + min(100, na_watchlist * 12) * 0.18
        + min(100, (alta + boas) * 12) * 0.22
        + score_historico * 0.14
        + score_watchlist * 0.11
        + score_relatorio * 0.11
    ))

    if total == 0:
        risco = "Alto"
        decisao = "Sem análises para inteligência"
        proximo = "Criar e salvar análises no Motor Central."
    elif alta >= 1 and score_produto >= 75:
        risco = "Baixo"
        decisao = "Análise Inteligente pronta para orientar uso real"
        proximo = "Priorizar alta prioridade, gerar dossiê e acompanhar via Watchlist."
    elif alta + boas >= 1:
        risco = "Médio"
        decisao = "Há candidatos úteis, mas a base ainda pode amadurecer"
        proximo = "Integrar candidatos à Watchlist e gerar dossiê para os melhores."
    elif incompletas > 0:
        risco = "Médio/Alto"
        decisao = "Muitas premissas incompletas"
        proximo = "Revisar entradas do Motor para melhorar preço teto e score."
    else:
        risco = "Médio"
        decisao = "Base existe, mas sem oportunidades fortes"
        proximo = "Continuar acompanhando e esperar melhor margem ou dados."

    return {
        "versao": VERSAO_ANALISE_INTELIGENTE_VALORIS,
        "gerado_em": _agora_iso(),
        "score_produto": score_produto,
        "analises_total": total,
        "watchlist_total": len(watchlist),
        "alta_prioridade": alta,
        "boas_candidatas": boas,
        "premissas_incompletas": incompletas,
        "na_watchlist": na_watchlist,
        "score_medio_inteligente": score_medio,
        "score_historico": score_historico,
        "score_watchlist": score_watchlist,
        "score_relatorio": score_relatorio,
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo,
    }


def salvar_decisao_analise_inteligente(item: Dict[str, Any], observacao: str = "") -> Path:
    _garantir_csv(CAMINHO_DECISOES, CAMPOS_DECISOES)

    with CAMINHO_DECISOES.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISOES)
        escritor.writerow(
            {
                "data_hora": _agora_iso(),
                "ticker": _txt(item.get("ticker")).upper(),
                "empresa": _txt(item.get("empresa")),
                "score_inteligente": _txt(item.get("score_inteligente")),
                "classificacao": _txt(item.get("classificacao")),
                "acao_recomendada": _txt(item.get("acao_recomendada")),
                "proximo_passo": _txt(item.get("proximo_passo")),
                "observacao": _txt(observacao),
            }
        )

    return CAMINHO_DECISOES


def carregar_decisoes_analise_inteligente(max_registros: int = 300) -> List[Dict[str, str]]:
    return carregar_csv_seguro(CAMINHO_DECISOES, CAMPOS_DECISOES, max_registros=max_registros)


def gerar_relatorio_analise_inteligente_markdown(ranking: Optional[List[Dict[str, Any]]] = None) -> str:
    if ranking is None:
        ranking = gerar_ranking_inteligente()

    metricas = calcular_metricas_analise_inteligente()

    linhas_top = "\n".join(
        [
            f"- **#{item['ranking']} {item['ticker']} — {item['empresa']}**: score inteligente {item['score_inteligente']}/100, classificação {item['classificacao']}, ação: {item['acao_recomendada']}."
            for item in ranking[:15]
        ]
    ) or "- Nenhuma análise ranqueada."

    return f"""# Relatório de Análise Inteligente — Valoris

Versão: {VERSAO_ANALISE_INTELIGENTE_VALORIS}  
Gerado em: {_agora_iso()}

## Diagnóstico

Score do Produto: {metricas['score_produto']}/100  
Análises: {metricas['analises_total']}  
Watchlist: {metricas['watchlist_total']}  
Alta prioridade: {metricas['alta_prioridade']}  
Boas candidatas: {metricas['boas_candidatas']}  
Score médio inteligente: {metricas['score_medio_inteligente']}/100  

Risco: {metricas['risco']}  
Decisão: {metricas['decisao']}  
Próximo passo: {metricas['proximo_passo']}

## Ranking inteligente

{linhas_top}

## Leitura estratégica

A Análise Inteligente é a central de decisão da Valoris. Ela não substitui o julgamento do investidor, mas organiza preço, qualidade, risco, histórico, watchlist e relatório em uma ordem de ação mais profissional.
"""


def salvar_relatorio_analise_inteligente_markdown() -> Path:
    CAMINHO_RELATORIO.write_text(gerar_relatorio_analise_inteligente_markdown(), encoding="utf-8")
    return CAMINHO_RELATORIO


def gerar_manifesto_analise_inteligente() -> Dict[str, Any]:
    return {
        "produto": "Valoris",
        "versao": VERSAO_ANALISE_INTELIGENTE_VALORIS,
        "modulo": "analise_inteligente_valoris",
        "data_hora": _agora_iso(),
        "metricas": calcular_metricas_analise_inteligente(),
        "principio": "unir análise, histórico, acompanhamento e dossiê em uma central de decisão",
        "fluxo": "Motor → Histórico → Watchlist → Relatório → Análise Inteligente",
    }


def salvar_manifesto_analise_inteligente() -> Path:
    CAMINHO_MANIFESTO.write_text(
        json.dumps(gerar_manifesto_analise_inteligente(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return CAMINHO_MANIFESTO


def renderizar_analise_inteligente_valoris() -> None:
    st.subheader("Análise Inteligente")
    st.caption(
        "Central de decisão: combina Motor, Histórico, Watchlist e Relatório para indicar próximos passos com mais clareza."
    )

    ranking = gerar_ranking_inteligente()
    metricas = calcular_metricas_analise_inteligente()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Score produto", f"{metricas['score_produto']}/100")
    col2.metric("Análises", metricas["analises_total"])
    col3.metric("Alta prioridade", metricas["alta_prioridade"])
    col4.metric("Boas candidatas", metricas["boas_candidatas"])
    col5.metric("Na Watchlist", metricas["na_watchlist"])

    if metricas["score_produto"] >= 75:
        st.success(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    elif metricas["analises_total"] > 0:
        st.warning(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    else:
        st.info(f"{metricas['decisao']} — {metricas['proximo_passo']}")

    st.divider()

    st.markdown("### Ranking inteligente")

    col_f1, col_f2, col_f3 = st.columns(3)
    filtro_ticker = col_f1.text_input("Filtrar ticker", value="")
    filtro_classe = col_f2.selectbox(
        "Classificação",
        ["Todas"] + sorted(list({item["classificacao"] for item in ranking})),
    )
    score_min = col_f3.slider("Score mínimo", 0, 100, 0)

    filtrado = []

    for item in ranking:
        if filtro_ticker.strip() and filtro_ticker.strip().upper() not in item["ticker"]:
            continue

        if filtro_classe != "Todas" and item["classificacao"] != filtro_classe:
            continue

        if item["score_inteligente"] < score_min:
            continue

        filtrado.append(item)

    st.dataframe(filtrado, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Decisão guiada")

    if filtrado:
        opcoes = [
            f"#{item['ranking']} | {item['ticker']} | {item['classificacao']} | score {item['score_inteligente']}"
            for item in filtrado
        ]

        escolha = st.selectbox("Escolha um ativo do ranking", opcoes)
        item = filtrado[opcoes.index(escolha)]

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Ticker", item["ticker"])
        col2.metric("Preço atual", _moeda(item["preco_atual"]))
        col3.metric("Preço teto", _moeda(item["preco_teto"]))
        col4.metric("Score inteligente", f"{item['score_inteligente']}/100")

        st.markdown(f"**Classificação:** {item['classificacao']}")
        st.markdown(f"**Ação recomendada:** {item['acao_recomendada']}")
        st.info(item["proximo_passo"])

        observacao = st.text_area(
            "Observação da decisão",
            value=f"Decisão guiada pela Análise Inteligente v{VERSAO_ANALISE_INTELIGENTE_VALORIS}.",
        )

        col_a, col_b, col_c = st.columns(3)

        if col_a.button("Registrar decisão inteligente"):
            salvar_decisao_analise_inteligente(item, observacao=observacao)
            st.success("Decisão registrada.")
            st.rerun()

        if col_b.button("Abrir próximo passo sugerido"):
            st.info(
                "Use as páginas Motor + Watchlist ou Motor + Relatório para executar o próximo passo sugerido."
            )

        if col_c.button("Gerar relatório da análise inteligente"):
            caminho = salvar_relatorio_analise_inteligente_markdown()
            st.success(f"Relatório salvo em {caminho}")
    else:
        st.info("Nenhum ativo encontrado com os filtros atuais.")

    st.divider()

    st.markdown("### Relatórios e histórico da central")

    col1, col2 = st.columns(2)

    if col1.button("Salvar relatório geral"):
        caminho = salvar_relatorio_analise_inteligente_markdown()
        st.success(f"Relatório salvo em {caminho}")

    if col2.button("Salvar manifesto"):
        caminho = salvar_manifesto_analise_inteligente()
        st.success(f"Manifesto salvo em {caminho}")

    st.download_button(
        "Baixar relatório da Análise Inteligente (.md)",
        data=gerar_relatorio_analise_inteligente_markdown(ranking),
        file_name="RELATORIO_ANALISE_INTELIGENTE_VALORIS.md",
        mime="text/markdown",
    )

    decisoes = carregar_decisoes_analise_inteligente()

    if decisoes:
        st.markdown("### Decisões registradas")
        st.dataframe(decisoes, use_container_width=True, hide_index=True)
    else:
        st.info("Ainda não há decisões registradas pela Análise Inteligente.")


def executar_autoteste_analise_inteligente_valoris() -> Dict[str, Any]:
    metricas = calcular_metricas_analise_inteligente()

    return {
        "ok": True,
        "versao": VERSAO_ANALISE_INTELIGENTE_VALORIS,
        "metricas": {
            "score_produto": metricas["score_produto"],
            "analises_total": metricas["analises_total"],
            "alta_prioridade": metricas["alta_prioridade"],
        },
    }
