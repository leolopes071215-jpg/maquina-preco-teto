# pipeline_decisao_valoris.py
# Valoris — Pipeline de Decisão Premium v3.9.6
# ------------------------------------------------------------
# Objetivo:
# - Criar uma esteira executiva de decisão para os ativos analisados.
# - Transformar análise em fluxo: revisar premissas, watchlist, dossiê, acompanhamento ou arquivamento.
# - Organizar a Valoris como produto operacional, não apenas como conjunto de páginas.
# ------------------------------------------------------------

from __future__ import annotations

import csv
import json
from collections import Counter, deque
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st


VERSAO_PIPELINE_DECISAO_VALORIS = "3.9.6"

CAMINHO_ACOES_PIPELINE = Path("acoes_pipeline_decisao_valoris.csv")
CAMINHO_RELATORIO = Path("RELATORIO_PIPELINE_DECISAO_VALORIS.md")
CAMINHO_MANIFESTO = Path("manifesto_pipeline_decisao_valoris.json")

CAMPOS_ACOES_PIPELINE = [
    "data_hora",
    "ticker",
    "empresa",
    "etapa",
    "prioridade",
    "acao",
    "responsavel",
    "prazo",
    "status",
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


def _garantir_csv(caminho: Path, campos: List[str]) -> None:
    if caminho.exists():
        return

    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()


def carregar_csv(caminho: Path, campos: List[str], max_registros: int = 800) -> List[Dict[str, str]]:
    _garantir_csv(caminho, campos)

    try:
        with caminho.open("r", newline="", encoding="utf-8") as arquivo:
            leitor = csv.DictReader(arquivo)
            return list(deque(leitor, maxlen=max_registros))
    except Exception:
        return []


def carregar_ranking_inteligente() -> List[Dict[str, Any]]:
    try:
        from analise_inteligente_valoris import gerar_ranking_inteligente

        return gerar_ranking_inteligente()
    except Exception:
        return []


def carregar_watchlist() -> List[Dict[str, str]]:
    try:
        from watchlist_fundadores_valoris import carregar_watchlist_fundadores

        return carregar_watchlist_fundadores()
    except Exception:
        return []


def carregar_acoes_pipeline(max_registros: int = 500) -> List[Dict[str, str]]:
    return carregar_csv(CAMINHO_ACOES_PIPELINE, CAMPOS_ACOES_PIPELINE, max_registros=max_registros)


def salvar_acao_pipeline(
    ticker: str,
    empresa: str,
    etapa: str,
    prioridade: str,
    acao: str,
    responsavel: str,
    prazo: str,
    status: str,
    observacao: str,
) -> Path:
    _garantir_csv(CAMINHO_ACOES_PIPELINE, CAMPOS_ACOES_PIPELINE)

    with CAMINHO_ACOES_PIPELINE.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_ACOES_PIPELINE)
        escritor.writerow(
            {
                "data_hora": _agora_iso(),
                "ticker": _txt(ticker).upper(),
                "empresa": _txt(empresa),
                "etapa": _txt(etapa),
                "prioridade": _txt(prioridade),
                "acao": _txt(acao),
                "responsavel": _txt(responsavel),
                "prazo": _txt(prazo),
                "status": _txt(status),
                "observacao": _txt(observacao),
            }
        )

    return CAMINHO_ACOES_PIPELINE


def determinar_etapa_pipeline(item: Dict[str, Any]) -> str:
    classificacao = _txt(item.get("classificacao"))
    acao = _txt(item.get("acao_recomendada"))
    ja_watchlist = _txt(item.get("ja_na_watchlist")).lower() == "sim"
    score = _float(item.get("score_inteligente"))
    preco_teto = _float(item.get("preco_teto"))

    if preco_teto <= 0 or classificacao == "Premissas incompletas":
        return "1. Revisar premissas"

    if classificacao in {"Risco elevado", "Qualidade fraca", "Baixa prioridade"}:
        return "5. Arquivar ou observar"

    if classificacao == "Alta prioridade":
        if ja_watchlist:
            return "3. Gerar dossiê"
        return "2. Enviar para Watchlist"

    if classificacao == "Boa candidata":
        if ja_watchlist and score >= 72:
            return "3. Gerar dossiê"
        return "2. Enviar para Watchlist"

    if classificacao == "Neutra":
        return "4. Aguardar gatilho"

    if "Gerar dossiê" in acao:
        return "3. Gerar dossiê"

    return "4. Aguardar gatilho"


def sugerir_prioridade_pipeline(item: Dict[str, Any]) -> str:
    score = _float(item.get("score_inteligente"))
    etapa = determinar_etapa_pipeline(item)

    if etapa.startswith("1."):
        return "Alta" if score >= 60 else "Média"

    if etapa.startswith("2.") or etapa.startswith("3."):
        if score >= 78:
            return "Alta"
        if score >= 65:
            return "Média"
        return "Baixa"

    if etapa.startswith("5."):
        return "Baixa"

    return "Média"


def sugerir_acao_pipeline(item: Dict[str, Any]) -> str:
    etapa = determinar_etapa_pipeline(item)
    ticker = _txt(item.get("ticker")).upper()

    if etapa.startswith("1."):
        return f"Revisar dados do Motor para {ticker}: preço, lucro, FCF, dívida, qualidade e risco."

    if etapa.startswith("2."):
        return f"Enviar {ticker} para Watchlist com tese, risco principal, próximo evento e data de revisão."

    if etapa.startswith("3."):
        return f"Gerar dossiê premium de {ticker} usando Motor + Relatório."

    if etapa.startswith("4."):
        return f"Aguardar preço melhor, resultado trimestral ou novo dado relevante antes de avançar com {ticker}."

    return f"Não priorizar {ticker} agora; manter apenas como observação histórica."


def gerar_pipeline_decisao() -> List[Dict[str, Any]]:
    ranking = carregar_ranking_inteligente()
    pipeline: List[Dict[str, Any]] = []

    for item in ranking:
        etapa = determinar_etapa_pipeline(item)
        prioridade = sugerir_prioridade_pipeline(item)
        acao = sugerir_acao_pipeline(item)

        pipeline.append(
            {
                **item,
                "etapa_pipeline": etapa,
                "prioridade_pipeline": prioridade,
                "acao_pipeline": acao,
            }
        )

    ordem_etapas = {
        "1. Revisar premissas": 1,
        "2. Enviar para Watchlist": 2,
        "3. Gerar dossiê": 3,
        "4. Aguardar gatilho": 4,
        "5. Arquivar ou observar": 5,
    }

    ordem_prioridade = {"Alta": 1, "Média": 2, "Baixa": 3}

    pipeline.sort(
        key=lambda item: (
            ordem_etapas.get(item["etapa_pipeline"], 9),
            ordem_prioridade.get(item["prioridade_pipeline"], 9),
            -_float(item.get("score_inteligente")),
        )
    )

    return pipeline


def calcular_metricas_pipeline() -> Dict[str, Any]:
    pipeline = gerar_pipeline_decisao()
    acoes = carregar_acoes_pipeline()
    etapas = Counter(item["etapa_pipeline"] for item in pipeline)
    prioridades = Counter(item["prioridade_pipeline"] for item in pipeline)

    alta = prioridades.get("Alta", 0)
    media = prioridades.get("Média", 0)
    baixa = prioridades.get("Baixa", 0)

    score_operacional = 20
    score_operacional += min(len(pipeline) * 6, 30)
    score_operacional += min(alta * 10, 20)
    score_operacional += min(len(acoes) * 4, 18)

    if etapas.get("3. Gerar dossiê", 0) > 0:
        score_operacional += 8

    if etapas.get("2. Enviar para Watchlist", 0) > 0:
        score_operacional += 6

    score_operacional = max(0, min(100, int(score_operacional)))

    if len(pipeline) == 0:
        risco = "Alto"
        decisao = "Pipeline vazio"
        proximo = "Criar análises no Motor e passar pela Análise Inteligente."
    elif alta > 0:
        risco = "Baixo/Médio"
        decisao = "Há ações prioritárias para executar"
        proximo = "Executar primeiro as etapas de alta prioridade."
    elif media > 0:
        risco = "Médio"
        decisao = "Pipeline funcional, mas sem urgência alta"
        proximo = "Acompanhar gatilhos e melhorar dados dos ativos."
    else:
        risco = "Baixo"
        decisao = "Nada urgente no momento"
        proximo = "Manter acompanhamento e aguardar novas oportunidades."

    return {
        "versao": VERSAO_PIPELINE_DECISAO_VALORIS,
        "gerado_em": _agora_iso(),
        "score_operacional": score_operacional,
        "ativos_no_pipeline": len(pipeline),
        "acoes_registradas": len(acoes),
        "alta_prioridade": alta,
        "media_prioridade": media,
        "baixa_prioridade": baixa,
        "etapas": dict(etapas),
        "prioridades": dict(prioridades),
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo,
    }


def gerar_relatorio_pipeline_markdown(pipeline: Optional[List[Dict[str, Any]]] = None) -> str:
    if pipeline is None:
        pipeline = gerar_pipeline_decisao()

    metricas = calcular_metricas_pipeline()

    linhas = "\n".join(
        [
            f"- **{item.get('ticker', '')}** — {item.get('etapa_pipeline', '')} — prioridade {item.get('prioridade_pipeline', '')} — score {item.get('score_inteligente', '')}/100 — {item.get('acao_pipeline', '')}"
            for item in pipeline[:25]
        ]
    ) or "- Nenhum ativo no pipeline."

    etapas = "\n".join(
        [f"- {etapa}: {quantidade}" for etapa, quantidade in metricas["etapas"].items()]
    ) or "- Nenhuma etapa."

    return f"""# Pipeline de Decisão Premium — Valoris

Versão: {VERSAO_PIPELINE_DECISAO_VALORIS}  
Gerado em: {_agora_iso()}

## Diagnóstico operacional

Score operacional: {metricas['score_operacional']}/100  
Ativos no pipeline: {metricas['ativos_no_pipeline']}  
Ações registradas: {metricas['acoes_registradas']}  
Alta prioridade: {metricas['alta_prioridade']}  
Média prioridade: {metricas['media_prioridade']}  
Baixa prioridade: {metricas['baixa_prioridade']}  

Risco: {metricas['risco']}  
Decisão: {metricas['decisao']}  
Próximo passo: {metricas['proximo_passo']}

## Distribuição por etapa

{etapas}

## Próximas ações

{linhas}

## Leitura estratégica

O Pipeline de Decisão transforma a Valoris em uma esteira operacional: cada ativo analisado recebe uma etapa, uma prioridade e uma ação. Isso reduz dispersão, evita decisões soltas e cria disciplina de acompanhamento.
"""


def salvar_relatorio_pipeline_markdown() -> Path:
    CAMINHO_RELATORIO.write_text(gerar_relatorio_pipeline_markdown(), encoding="utf-8")
    return CAMINHO_RELATORIO


def gerar_manifesto_pipeline() -> Dict[str, Any]:
    return {
        "produto": "Valoris",
        "versao": VERSAO_PIPELINE_DECISAO_VALORIS,
        "modulo": "pipeline_decisao_valoris",
        "data_hora": _agora_iso(),
        "metricas": calcular_metricas_pipeline(),
        "principio": "transformar inteligência em execução disciplinada",
        "fluxo": "Análise Inteligente → Pipeline → Watchlist/Relatório/Revisão",
    }


def salvar_manifesto_pipeline() -> Path:
    CAMINHO_MANIFESTO.write_text(
        json.dumps(gerar_manifesto_pipeline(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return CAMINHO_MANIFESTO


def renderizar_pipeline_decisao_valoris() -> None:
    st.subheader("Pipeline de Decisão Premium")
    st.caption(
        "Esteira operacional: transforma análises em próximas ações claras, com etapa, prioridade, prazo e status."
    )

    pipeline = gerar_pipeline_decisao()
    metricas = calcular_metricas_pipeline()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Score operacional", f"{metricas['score_operacional']}/100")
    col2.metric("Ativos", metricas["ativos_no_pipeline"])
    col3.metric("Alta", metricas["alta_prioridade"])
    col4.metric("Média", metricas["media_prioridade"])
    col5.metric("Ações", metricas["acoes_registradas"])

    if metricas["alta_prioridade"] > 0:
        st.warning(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    elif metricas["ativos_no_pipeline"] > 0:
        st.info(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    else:
        st.info(f"{metricas['decisao']} — {metricas['proximo_passo']}")

    st.divider()

    st.markdown("### Filtros")

    etapas_disponiveis = ["Todas"] + sorted(list({item["etapa_pipeline"] for item in pipeline}))
    prioridades_disponiveis = ["Todas", "Alta", "Média", "Baixa"]

    col_f1, col_f2, col_f3 = st.columns(3)
    filtro_etapa = col_f1.selectbox("Etapa", etapas_disponiveis)
    filtro_prioridade = col_f2.selectbox("Prioridade", prioridades_disponiveis)
    filtro_ticker = col_f3.text_input("Ticker", value="")

    filtrado: List[Dict[str, Any]] = []

    for item in pipeline:
        if filtro_etapa != "Todas" and item["etapa_pipeline"] != filtro_etapa:
            continue

        if filtro_prioridade != "Todas" and item["prioridade_pipeline"] != filtro_prioridade:
            continue

        if filtro_ticker.strip() and filtro_ticker.strip().upper() not in item["ticker"]:
            continue

        filtrado.append(item)

    tabela = [
        {
            "ranking": item.get("ranking", ""),
            "ticker": item.get("ticker", ""),
            "empresa": item.get("empresa", ""),
            "etapa": item.get("etapa_pipeline", ""),
            "prioridade": item.get("prioridade_pipeline", ""),
            "score": item.get("score_inteligente", ""),
            "watchlist": item.get("ja_na_watchlist", ""),
            "ação": item.get("acao_pipeline", ""),
        }
        for item in filtrado
    ]

    st.dataframe(tabela, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Registrar ação")

    if filtrado:
        opcoes = [
            f"{item.get('ticker', '')} | {item.get('etapa_pipeline', '')} | {item.get('prioridade_pipeline', '')} | score {item.get('score_inteligente', '')}"
            for item in filtrado
        ]

        escolha = st.selectbox("Ativo/ação", opcoes)
        item = filtrado[opcoes.index(escolha)]

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Ticker", item.get("ticker", ""))
        col2.metric("Etapa", item.get("etapa_pipeline", ""))
        col3.metric("Prioridade", item.get("prioridade_pipeline", ""))
        col4.metric("Score", f"{item.get('score_inteligente', '')}/100")

        acao = st.text_area("Ação", value=item.get("acao_pipeline", ""), height=90)
        col_a, col_b, col_c = st.columns(3)
        responsavel = col_a.text_input("Responsável", value="Leo")
        prazo = col_b.date_input("Prazo", value=datetime.now().date() + timedelta(days=7))
        status = col_c.selectbox("Status", ["Aberta", "Em andamento", "Concluída", "Adiada", "Cancelada"])

        observacao = st.text_area("Observação", value="", height=80)

        if st.button("Registrar ação no pipeline"):
            salvar_acao_pipeline(
                ticker=item.get("ticker", ""),
                empresa=item.get("empresa", ""),
                etapa=item.get("etapa_pipeline", ""),
                prioridade=item.get("prioridade_pipeline", ""),
                acao=acao,
                responsavel=responsavel,
                prazo=str(prazo),
                status=status,
                observacao=observacao,
            )
            st.success("Ação registrada.")
            st.rerun()
    else:
        st.info("Nenhum item encontrado com os filtros atuais.")

    st.divider()

    st.markdown("### Ações registradas")
    acoes = carregar_acoes_pipeline()

    if acoes:
        st.dataframe(acoes, use_container_width=True, hide_index=True)
    else:
        st.info("Ainda não há ações registradas no pipeline.")

    st.divider()

    st.markdown("### Relatórios")

    col1, col2 = st.columns(2)

    if col1.button("Salvar relatório do pipeline"):
        caminho = salvar_relatorio_pipeline_markdown()
        st.success(f"Relatório salvo em {caminho}")

    if col2.button("Salvar manifesto do pipeline"):
        caminho = salvar_manifesto_pipeline()
        st.success(f"Manifesto salvo em {caminho}")

    st.download_button(
        "Baixar relatório do pipeline (.md)",
        data=gerar_relatorio_pipeline_markdown(pipeline),
        file_name="RELATORIO_PIPELINE_DECISAO_VALORIS.md",
        mime="text/markdown",
    )


def executar_autoteste_pipeline_decisao_valoris() -> Dict[str, Any]:
    metricas = calcular_metricas_pipeline()

    return {
        "ok": True,
        "versao": VERSAO_PIPELINE_DECISAO_VALORIS,
        "metricas": {
            "score_operacional": metricas["score_operacional"],
            "ativos_no_pipeline": metricas["ativos_no_pipeline"],
            "alta_prioridade": metricas["alta_prioridade"],
        },
    }
