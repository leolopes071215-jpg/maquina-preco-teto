# analise_inteligente_backend_valoris.py
# Valoris — Análise Inteligente com Backend Flexível v3.10.7
# ------------------------------------------------------------
# Objetivo:
# - Criar a primeira central de decisão inteligente lendo via backend flexível.
# - Usar CSV como padrão seguro e SQLite laboratório como opção validada.
# - Comparar experiência entre backends sem quebrar a página antiga.
# - Transformar histórico + watchlist em ranking executivo de decisão.

from __future__ import annotations

import csv
import json
from collections import Counter, deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Set

import streamlit as st


VERSAO_ANALISE_INTELIGENTE_BACKEND_VALORIS = "3.10.7"

BACKEND_CSV = "csv"
BACKEND_SQLITE = "sqlite_laboratorio"

CAMINHO_DECISOES = Path("decisoes_analise_inteligente_backend_valoris.csv")
CAMINHO_RELATORIO = Path("RELATORIO_ANALISE_INTELIGENTE_BACKEND_VALORIS.md")
CAMINHO_MANIFESTO = Path("manifesto_analise_inteligente_backend_valoris.json")

CAMPOS_DECISOES = [
    "data_hora",
    "backend",
    "ticker",
    "empresa",
    "score_inteligente",
    "classificacao",
    "acao_recomendada",
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


def obter_backend_padrao() -> str:
    try:
        from repository_backend_sqlite_valoris import obter_backend_padrao as obter

        backend = obter()

        if backend in {BACKEND_CSV, BACKEND_SQLITE}:
            return backend
    except Exception:
        pass

    return BACKEND_CSV


def listar_backend(entidade: str, backend: str, max_registros: int = 1000) -> List[Dict[str, Any]]:
    try:
        from repository_backend_sqlite_valoris import listar_registros_backend

        return listar_registros_backend(entidade, backend=backend, max_registros=max_registros)
    except Exception:
        return []


def comparar_csv_sqlite() -> List[Dict[str, Any]]:
    try:
        from repository_backend_sqlite_valoris import comparar_csv_sqlite as comparar

        return comparar()
    except Exception:
        return []


def normalizar_analise(registro: Dict[str, Any]) -> Dict[str, Any]:
    ticker = _txt(registro.get("ticker")).upper()
    empresa = _txt(registro.get("nome_empresa")) or _txt(registro.get("empresa")) or ticker

    return {
        "data_hora": _txt(registro.get("data_hora")),
        "ticker": ticker,
        "empresa": empresa,
        "setor": _txt(registro.get("setor")),
        "preco_atual": _float(registro.get("preco_atual")),
        "preco_teto": _float(registro.get("preco_teto")),
        "margem_seguranca_atual": _float(registro.get("margem_seguranca_atual")),
        "score_qualidade": _float(registro.get("score_qualidade")),
        "score_risco": _float(registro.get("score_risco")),
        "score_valor": _float(registro.get("score_valor")),
        "score_final": _float(registro.get("score_final")),
        "decisao": _txt(registro.get("decisao")),
        "nivel_conviccao": _txt(registro.get("nivel_conviccao")),
        "modelo_preco_teto": _txt(registro.get("modelo_preco_teto")),
        "observacao": _txt(registro.get("observacao")),
    }


def normalizar_watchlist(registro: Dict[str, Any]) -> Dict[str, Any]:
    ticker = _txt(registro.get("ticker")).upper()
    empresa = _txt(registro.get("empresa")) or _txt(registro.get("nome_empresa")) or ticker

    return {
        "data_hora": _txt(registro.get("data_hora")) or _txt(registro.get("data_registro")),
        "ticker": ticker,
        "empresa": empresa,
        "setor": _txt(registro.get("setor")),
        "prioridade": _txt(registro.get("prioridade")),
        "status_oportunidade": _txt(registro.get("status_oportunidade")),
        "preco_atual": _float(registro.get("preco_atual")),
        "preco_teto": _float(registro.get("preco_teto")),
        "data_revisao": _txt(registro.get("data_revisao")),
        "tese_resumo": _txt(registro.get("tese_resumo")),
        "principal_risco": _txt(registro.get("principal_risco")),
        "proximo_evento": _txt(registro.get("proximo_evento")),
        "observacoes": _txt(registro.get("observacoes")) or _txt(registro.get("observacao")),
    }


def tickers_watchlist(backend: str) -> Set[str]:
    registros = listar_backend("watchlist", backend=backend, max_registros=2000)
    return {
        _txt(item.get("ticker")).upper()
        for item in registros
        if _txt(item.get("ticker"))
    }


def calcular_score_inteligente(item: Dict[str, Any], em_watchlist: bool) -> int:
    score_final = _float(item.get("score_final"))
    score_qualidade = _float(item.get("score_qualidade"))
    score_valor = _float(item.get("score_valor"))
    score_risco = _float(item.get("score_risco"))
    margem = _float(item.get("margem_seguranca_atual"))

    score = 0.0
    score += score_final * 0.45
    score += score_qualidade * 0.20
    score += score_valor * 0.15
    score += score_risco * 0.10

    if margem >= 20:
        score += 10
    elif margem >= 10:
        score += 7
    elif margem >= 0:
        score += 4
    elif margem <= -20:
        score -= 8

    if em_watchlist:
        score += 5

    if _float(item.get("preco_teto")) <= 0:
        score -= 15

    return max(0, min(100, int(round(score))))


def classificar_item(item: Dict[str, Any], score_inteligente: int, em_watchlist: bool) -> str:
    preco_teto = _float(item.get("preco_teto"))
    score_risco = _float(item.get("score_risco"))
    score_qualidade = _float(item.get("score_qualidade"))

    if preco_teto <= 0:
        return "Premissas incompletas"

    if score_risco < 35:
        return "Risco elevado"

    if score_qualidade < 45:
        return "Qualidade fraca"

    if score_inteligente >= 80:
        return "Alta prioridade"

    if score_inteligente >= 65:
        return "Boa candidata" if not em_watchlist else "Boa candidata em acompanhamento"

    if score_inteligente >= 50:
        return "Neutra"

    return "Baixa prioridade"


def sugerir_acao(item: Dict[str, Any], classificacao: str, em_watchlist: bool) -> str:
    ticker = _txt(item.get("ticker")).upper()

    if classificacao == "Premissas incompletas":
        return f"Revisar premissas de {ticker} no Motor antes de qualquer decisão."

    if classificacao == "Risco elevado":
        return f"Manter {ticker} fora da prioridade até reduzir incertezas."

    if classificacao == "Qualidade fraca":
        return f"Evitar avanço em {ticker} sem nova tese de qualidade."

    if classificacao == "Alta prioridade":
        if em_watchlist:
            return f"Gerar dossiê premium de {ticker} e definir próximo gatilho."
        return f"Enviar {ticker} para Watchlist e preparar dossiê."

    if classificacao.startswith("Boa candidata"):
        if em_watchlist:
            return f"Acompanhar {ticker} e revisar após próximo evento."
        return f"Adicionar {ticker} à Watchlist com tese e preço de gatilho."

    if classificacao == "Neutra":
        return f"Aguardar preço melhor ou novo resultado antes de avançar com {ticker}."

    return f"Arquivar {ticker} por enquanto e priorizar oportunidades melhores."


def gerar_ranking_inteligente_backend(backend: str = BACKEND_CSV, max_registros: int = 1000) -> List[Dict[str, Any]]:
    analises = [
        normalizar_analise(item)
        for item in listar_backend("analises", backend=backend, max_registros=max_registros)
    ]

    watch = tickers_watchlist(backend=backend)
    ranking: List[Dict[str, Any]] = []

    for item in analises:
        ticker = _txt(item.get("ticker")).upper()

        if not ticker:
            continue

        em_watchlist = ticker in watch
        score_inteligente = calcular_score_inteligente(item, em_watchlist=em_watchlist)
        classificacao = classificar_item(item, score_inteligente, em_watchlist=em_watchlist)
        acao = sugerir_acao(item, classificacao, em_watchlist=em_watchlist)

        ranking.append(
            {
                **item,
                "score_inteligente": score_inteligente,
                "classificacao": classificacao,
                "ja_na_watchlist": "Sim" if em_watchlist else "Não",
                "acao_recomendada": acao,
                "backend": backend,
            }
        )

    ranking.sort(
        key=lambda item: (
            -int(item.get("score_inteligente", 0)),
            _txt(item.get("ticker")),
        )
    )

    for indice, item in enumerate(ranking, start=1):
        item["ranking"] = indice

    return ranking


def calcular_metricas_analise_backend(backend: str = BACKEND_CSV) -> Dict[str, Any]:
    ranking = gerar_ranking_inteligente_backend(backend=backend)
    comparacao = comparar_csv_sqlite()

    total = len(ranking)
    alta = len([item for item in ranking if item["classificacao"] == "Alta prioridade"])
    boas = len([item for item in ranking if item["classificacao"].startswith("Boa candidata")])
    incompletas = len([item for item in ranking if item["classificacao"] == "Premissas incompletas"])
    watch = len([item for item in ranking if item["ja_na_watchlist"] == "Sim"])

    score_medio = round(sum(int(item["score_inteligente"]) for item in ranking) / total, 1) if total else 0.0

    score_experiencia = 35
    score_experiencia += min(total * 8, 28)
    score_experiencia += min(alta * 12, 18)
    score_experiencia += min(boas * 8, 16)

    if incompletas:
        score_experiencia -= min(incompletas * 8, 24)

    if any(item.get("status") == "divergente" for item in comparacao):
        score_experiencia -= 15

    score_experiencia = max(0, min(100, int(score_experiencia)))

    if total == 0:
        risco = "Médio"
        decisao = "Sem análises para ranquear no backend selecionado"
        proximo = "Criar análises no Motor ou importar CSVs para SQLite."
    elif incompletas > 0:
        risco = "Médio"
        decisao = "Ranking funcional, mas há premissas incompletas"
        proximo = "Revisar premissas antes de usar ranking como decisão final."
    elif score_experiencia >= 80:
        risco = "Baixo"
        decisao = "Análise Inteligente pronta para uso premium com backend flexível"
        proximo = "Validar com mais ativos e depois substituir a página antiga."
    else:
        risco = "Baixo/Médio"
        decisao = "Ranking funcional, ainda com pouca base de dados"
        proximo = "Adicionar mais análises reais para aumentar qualidade da priorização."

    return {
        "versao": VERSAO_ANALISE_INTELIGENTE_BACKEND_VALORIS,
        "backend": backend,
        "gerado_em": _agora_iso(),
        "score_experiencia": score_experiencia,
        "ativos_ranqueados": total,
        "alta_prioridade": alta,
        "boas_candidatas": boas,
        "premissas_incompletas": incompletas,
        "em_watchlist": watch,
        "score_medio": score_medio,
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo,
    }


def salvar_decisao_analise_backend(
    backend: str,
    ticker: str,
    empresa: str,
    score_inteligente: Any,
    classificacao: str,
    acao_recomendada: str,
    observacao: str = "",
) -> Path:
    _garantir_csv(CAMINHO_DECISOES, CAMPOS_DECISOES)

    with CAMINHO_DECISOES.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISOES)
        escritor.writerow(
            {
                "data_hora": _agora_iso(),
                "backend": _txt(backend),
                "ticker": _txt(ticker).upper(),
                "empresa": _txt(empresa),
                "score_inteligente": _txt(score_inteligente),
                "classificacao": _txt(classificacao),
                "acao_recomendada": _txt(acao_recomendada),
                "observacao": _txt(observacao),
            }
        )

    return CAMINHO_DECISOES


def carregar_decisoes_analise_backend(max_registros: int = 300) -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_DECISOES, CAMPOS_DECISOES)

    try:
        with CAMINHO_DECISOES.open("r", newline="", encoding="utf-8") as arquivo:
            leitor = csv.DictReader(arquivo)
            return list(deque(leitor, maxlen=max_registros))
    except Exception:
        return []


def gerar_relatorio_analise_backend_markdown(backend: str = BACKEND_CSV) -> str:
    metricas = calcular_metricas_analise_backend(backend=backend)
    ranking = gerar_ranking_inteligente_backend(backend=backend)

    linhas = "\n".join(
        [
            f"- **#{item['ranking']} {item['ticker']} — {item['empresa']}**: score {item['score_inteligente']}/100, {item['classificacao']}. Ação: {item['acao_recomendada']}"
            for item in ranking[:15]
        ]
    ) or "- Nenhum ativo ranqueado."

    return f"""# Análise Inteligente com Backend Flexível — Valoris

Versão: {VERSAO_ANALISE_INTELIGENTE_BACKEND_VALORIS}  
Gerado em: {_agora_iso()}

## Diagnóstico

Backend: {backend}  
Score experiência: {metricas['score_experiencia']}/100  
Ativos ranqueados: {metricas['ativos_ranqueados']}  
Alta prioridade: {metricas['alta_prioridade']}  
Boas candidatas: {metricas['boas_candidatas']}  
Premissas incompletas: {metricas['premissas_incompletas']}  
Score médio: {metricas['score_medio']}/100  

Risco: {metricas['risco']}  
Decisão: {metricas['decisao']}  
Próximo passo: {metricas['proximo_passo']}

## Ranking

{linhas}

## Estratégia

Esta página transforma dados do backend flexível em decisão. A migração é segura porque a página antiga permanece disponível, CSV segue como padrão e SQLite é validado como laboratório.
"""


def salvar_relatorio_analise_backend(backend: str = BACKEND_CSV) -> Path:
    CAMINHO_RELATORIO.write_text(
        gerar_relatorio_analise_backend_markdown(backend=backend),
        encoding="utf-8",
    )
    return CAMINHO_RELATORIO


def gerar_manifesto_analise_backend(backend: str = BACKEND_CSV) -> Dict[str, Any]:
    return {
        "produto": "Valoris",
        "versao": VERSAO_ANALISE_INTELIGENTE_BACKEND_VALORIS,
        "modulo": "analise_inteligente_backend_valoris",
        "data_hora": _agora_iso(),
        "backend": backend,
        "metricas": calcular_metricas_analise_backend(backend=backend),
        "ranking": gerar_ranking_inteligente_backend(backend=backend),
        "principio": "decisão premium exige ranking claro, fonte confiável e rollback",
        "proxima_etapa": "promover Análise Inteligente Backend como principal após validação",
    }


def salvar_manifesto_analise_backend(backend: str = BACKEND_CSV) -> Path:
    CAMINHO_MANIFESTO.write_text(
        json.dumps(gerar_manifesto_analise_backend(backend=backend), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return CAMINHO_MANIFESTO


def renderizar_analise_inteligente_backend_valoris() -> None:
    st.subheader("Análise Inteligente — Backend Flexível")
    st.caption(
        "Ranking executivo de decisão lendo análises e watchlist pelo Repository Backend. CSV seguro por padrão; SQLite como laboratório."
    )

    backend_padrao = obter_backend_padrao()
    opcoes_backend = [BACKEND_CSV, BACKEND_SQLITE]

    if backend_padrao not in opcoes_backend:
        backend_padrao = BACKEND_CSV

    col_config1, col_config2 = st.columns(2)

    backend = col_config1.selectbox(
        "Backend de leitura",
        opcoes_backend,
        index=opcoes_backend.index(backend_padrao),
    )

    limite = col_config2.slider("Registros analisados", 50, 2000, 1000)

    metricas = calcular_metricas_analise_backend(backend=backend)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Score experiência", f"{metricas['score_experiencia']}/100")
    col2.metric("Ativos", metricas["ativos_ranqueados"])
    col3.metric("Alta prioridade", metricas["alta_prioridade"])
    col4.metric("Boas candidatas", metricas["boas_candidatas"])
    col5.metric("Score médio", f"{metricas['score_medio']}/100")

    if metricas["risco"] == "Baixo":
        st.success(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    elif metricas["risco"] == "Médio":
        st.warning(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    else:
        st.info(f"{metricas['decisao']} — {metricas['proximo_passo']}")

    st.divider()

    st.markdown("### Comparação CSV x SQLite")
    st.dataframe(comparar_csv_sqlite(), use_container_width=True, hide_index=True)

    st.divider()

    ranking = gerar_ranking_inteligente_backend(backend=backend, max_registros=limite)

    st.markdown("### Filtros")

    col_f1, col_f2, col_f3 = st.columns(3)
    filtro_ticker = col_f1.text_input("Ticker", value="")
    classificacoes = ["Todas"] + sorted(list({item["classificacao"] for item in ranking}))
    filtro_classificacao = col_f2.selectbox("Classificação", classificacoes)
    score_minimo = col_f3.slider("Score inteligente mínimo", 0, 100, 0)

    filtrado = []

    for item in ranking:
        if filtro_ticker.strip() and filtro_ticker.strip().upper() not in item["ticker"]:
            continue
        if filtro_classificacao != "Todas" and item["classificacao"] != filtro_classificacao:
            continue
        if int(item["score_inteligente"]) < score_minimo:
            continue

        filtrado.append(item)

    tabela = [
        {
            "ranking": item["ranking"],
            "ticker": item["ticker"],
            "empresa": item["empresa"],
            "setor": item["setor"],
            "score inteligente": item["score_inteligente"],
            "score final": item["score_final"],
            "margem": _pct(item["margem_seguranca_atual"]),
            "watchlist": item["ja_na_watchlist"],
            "classificação": item["classificacao"],
            "ação recomendada": item["acao_recomendada"],
        }
        for item in filtrado
    ]

    st.markdown("### Ranking inteligente")
    st.dataframe(tabela, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Decisão guiada")

    if filtrado:
        opcoes = [
            f"#{item['ranking']} | {item['ticker']} | score {item['score_inteligente']} | {item['classificacao']}"
            for item in filtrado
        ]

        escolha = st.selectbox("Ativo", opcoes)
        item = filtrado[opcoes.index(escolha)]

        col_a, col_b, col_c, col_d = st.columns(4)
        col_a.metric("Ticker", item["ticker"])
        col_b.metric("Preço atual", _moeda(item["preco_atual"]))
        col_c.metric("Preço teto", _moeda(item["preco_teto"]))
        col_d.metric("Score", f"{item['score_inteligente']}/100")

        st.info(item["acao_recomendada"])

        observacao = st.text_area(
            "Observação da decisão",
            value=f"Decisão registrada na Análise Inteligente Backend usando backend {backend}.",
            height=90,
        )

        if st.button("Salvar decisão inteligente"):
            salvar_decisao_analise_backend(
                backend=backend,
                ticker=item["ticker"],
                empresa=item["empresa"],
                score_inteligente=item["score_inteligente"],
                classificacao=item["classificacao"],
                acao_recomendada=item["acao_recomendada"],
                observacao=observacao,
            )
            st.success("Decisão inteligente registrada.")
            st.rerun()
    else:
        st.info("Nenhum ativo encontrado com os filtros atuais.")

    decisoes = carregar_decisoes_analise_backend()

    if decisoes:
        st.markdown("### Decisões registradas")
        st.dataframe(decisoes, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Relatórios")

    col_r1, col_r2 = st.columns(2)

    if col_r1.button("Salvar relatório da Análise Backend"):
        caminho = salvar_relatorio_analise_backend(backend=backend)
        st.success(f"Relatório salvo em {caminho}")

    if col_r2.button("Salvar manifesto da Análise Backend"):
        caminho = salvar_manifesto_analise_backend(backend=backend)
        st.success(f"Manifesto salvo em {caminho}")

    st.download_button(
        "Baixar relatório da Análise Backend (.md)",
        data=gerar_relatorio_analise_backend_markdown(backend=backend),
        file_name="RELATORIO_ANALISE_INTELIGENTE_BACKEND_VALORIS.md",
        mime="text/markdown",
    )


def executar_autoteste_analise_inteligente_backend_valoris() -> Dict[str, Any]:
    metricas_csv = calcular_metricas_analise_backend(backend=BACKEND_CSV)

    return {
        "ok": True,
        "versao": VERSAO_ANALISE_INTELIGENTE_BACKEND_VALORIS,
        "metricas": {
            "score_experiencia_csv": metricas_csv["score_experiencia"],
            "ativos_ranqueados_csv": metricas_csv["ativos_ranqueados"],
            "alta_prioridade_csv": metricas_csv["alta_prioridade"],
        },
    }
