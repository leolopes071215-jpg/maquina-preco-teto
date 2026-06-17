# historico_backend_flexivel_valoris.py
# Valoris — Histórico Análises com Backend Flexível v3.10.5
# ------------------------------------------------------------
# Objetivo:
# - Criar a primeira página real usando Repository Backend de forma controlada.
# - Ler o Histórico de Análises via backend flexível: CSV seguro ou SQLite laboratório.
# - Comparar dados, preservar rollback e melhorar a experiência do cliente.
# - Não remove a página antiga ainda; roda em paralelo para validação premium.

from __future__ import annotations

import csv
import json
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st


VERSAO_HISTORICO_BACKEND_FLEXIVEL_VALORIS = "3.10.5"

ENTIDADE_ANALISES = "analises"
BACKEND_CSV = "csv"
BACKEND_SQLITE = "sqlite_laboratorio"

CAMINHO_DECISOES = Path("decisoes_historico_backend_flexivel_valoris.csv")
CAMINHO_RELATORIO = Path("RELATORIO_HISTORICO_BACKEND_FLEXIVEL_VALORIS.md")
CAMINHO_MANIFESTO = Path("manifesto_historico_backend_flexivel_valoris.json")

CAMPOS_DECISOES = [
    "data_hora",
    "backend",
    "ticker",
    "decisao",
    "score_final",
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


def backend_padrao_flexivel() -> str:
    try:
        from repository_backend_sqlite_valoris import obter_backend_padrao

        return obter_backend_padrao()
    except Exception:
        return BACKEND_CSV


def sqlite_disponivel() -> bool:
    try:
        from repository_backend_sqlite_valoris import sqlite_disponivel as verificar

        return bool(verificar())
    except Exception:
        return Path("valoris_local.db").exists()


def listar_analises_backend(backend: str = BACKEND_CSV, max_registros: int = 800) -> List[Dict[str, Any]]:
    try:
        from repository_backend_sqlite_valoris import listar_registros_backend

        return listar_registros_backend(
            ENTIDADE_ANALISES,
            backend=backend,
            max_registros=max_registros,
        )
    except Exception:
        return listar_analises_csv_fallback(max_registros=max_registros)


def listar_analises_csv_fallback(max_registros: int = 800) -> List[Dict[str, Any]]:
    caminho = Path("analises_motor_ativos_valoris.csv")

    if not caminho.exists():
        return []

    try:
        with caminho.open("r", newline="", encoding="utf-8", errors="replace") as arquivo:
            leitor = csv.DictReader(arquivo)
            return list(deque(leitor, maxlen=max_registros))
    except Exception:
        return []


def comparar_csv_sqlite_analises() -> Dict[str, Any]:
    try:
        from repository_backend_sqlite_valoris import comparar_csv_sqlite

        comparacao = comparar_csv_sqlite()
        item = next((linha for linha in comparacao if linha.get("entidade") == ENTIDADE_ANALISES), None)

        if item:
            return dict(item)

    except Exception:
        pass

    csv_total = len(listar_analises_csv_fallback(max_registros=100000))

    return {
        "entidade": ENTIDADE_ANALISES,
        "tabela_sqlite": "analises_ativos",
        "csv": csv_total,
        "sqlite": 0,
        "diferenca": -csv_total,
        "status": "comparacao_indisponivel",
    }


def normalizar_analise(registro: Dict[str, Any]) -> Dict[str, Any]:
    ticker = _txt(registro.get("ticker")).upper()
    empresa = _txt(registro.get("nome_empresa")) or _txt(registro.get("empresa")) or ticker

    return {
        "id": registro.get("id", ""),
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
        "origem_id": registro.get("id", ""),
    }


def carregar_historico_flexivel(backend: str = BACKEND_CSV, max_registros: int = 800) -> List[Dict[str, Any]]:
    registros = listar_analises_backend(backend=backend, max_registros=max_registros)
    normalizados = [normalizar_analise(registro) for registro in registros]

    normalizados.sort(key=lambda item: _txt(item.get("data_hora")), reverse=True)

    return normalizados


def filtrar_historico(
    registros: List[Dict[str, Any]],
    ticker: str = "",
    decisao: str = "Todas",
    score_minimo: float = 0.0,
    margem_minima: float = -999.0,
) -> List[Dict[str, Any]]:
    ticker = _txt(ticker).upper()
    filtrados = []

    for item in registros:
        if ticker and ticker not in _txt(item.get("ticker")).upper():
            continue

        if decisao != "Todas" and _txt(item.get("decisao")) != decisao:
            continue

        if _float(item.get("score_final")) < score_minimo:
            continue

        if _float(item.get("margem_seguranca_atual")) < margem_minima:
            continue

        filtrados.append(item)

    return filtrados


def calcular_metricas_historico_backend(backend: str = BACKEND_CSV) -> Dict[str, Any]:
    registros = carregar_historico_flexivel(backend=backend)
    comparacao = comparar_csv_sqlite_analises()

    total = len(registros)
    tickers = [_txt(item.get("ticker")).upper() for item in registros if _txt(item.get("ticker"))]
    scores = [_float(item.get("score_final")) for item in registros]
    compras = len([item for item in registros if "COMPRA" in _txt(item.get("decisao")).upper()])
    precos_validos = len([item for item in registros if _float(item.get("preco_teto")) > 0])

    score_medio = round(sum(scores) / len(scores), 1) if scores else 0.0

    score_experiencia = 30
    score_experiencia += min(total * 8, 32)
    score_experiencia += min(len(set(tickers)) * 6, 18)
    score_experiencia += min(precos_validos * 5, 15)

    if comparacao.get("status") == "alinhado":
        score_experiencia += 15

    if backend == BACKEND_SQLITE and not sqlite_disponivel():
        score_experiencia = min(score_experiencia, 45)

    score_experiencia = max(0, min(100, int(score_experiencia)))

    if total == 0:
        risco = "Médio"
        decisao = "Histórico vazio no backend selecionado"
        proximo = "Usar CSV como fallback ou importar dados para SQLite."
    elif backend == BACKEND_SQLITE and comparacao.get("status") != "alinhado":
        risco = "Médio"
        decisao = "Histórico SQLite funcional, mas exige comparação cuidadosa"
        proximo = "Conferir CSV x SQLite antes de tornar SQLite padrão."
    elif score_experiencia >= 80:
        risco = "Baixo"
        decisao = "Histórico pronto para experiência premium com backend flexível"
        proximo = "Validar filtros e depois substituir gradualmente a página antiga."
    else:
        risco = "Baixo/Médio"
        decisao = "Histórico funcional, ainda com pouca massa de dados"
        proximo = "Gerar mais análises reais para melhorar a experiência do cliente."

    return {
        "versao": VERSAO_HISTORICO_BACKEND_FLEXIVEL_VALORIS,
        "backend": backend,
        "gerado_em": _agora_iso(),
        "score_experiencia": score_experiencia,
        "analises": total,
        "tickers": len(set(tickers)),
        "score_medio": score_medio,
        "compras": compras,
        "precos_validos": precos_validos,
        "comparacao_csv_sqlite": comparacao,
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo,
    }


def salvar_decisao_historico_backend(backend: str, ticker: str, decisao: str, score_final: Any, observacao: str = "") -> Path:
    _garantir_csv(CAMINHO_DECISOES, CAMPOS_DECISOES)

    with CAMINHO_DECISOES.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISOES)
        escritor.writerow(
            {
                "data_hora": _agora_iso(),
                "backend": _txt(backend),
                "ticker": _txt(ticker).upper(),
                "decisao": _txt(decisao),
                "score_final": _txt(score_final),
                "observacao": _txt(observacao),
            }
        )

    return CAMINHO_DECISOES


def carregar_decisoes_historico_backend(max_registros: int = 300) -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_DECISOES, CAMPOS_DECISOES)

    try:
        with CAMINHO_DECISOES.open("r", newline="", encoding="utf-8") as arquivo:
            leitor = csv.DictReader(arquivo)
            return list(deque(leitor, maxlen=max_registros))
    except Exception:
        return []


def gerar_relatorio_historico_backend_markdown(backend: str = BACKEND_CSV) -> str:
    metricas = calcular_metricas_historico_backend(backend=backend)
    registros = carregar_historico_flexivel(backend=backend)

    linhas_top = "\n".join(
        [
            f"- **{item['ticker']} — {item['empresa']}**: score {item['score_final']}/100, decisão {item['decisao']}, preço teto {_moeda(item['preco_teto'])}."
            for item in registros[:15]
        ]
    ) or "- Nenhuma análise encontrada."

    comparacao = metricas["comparacao_csv_sqlite"]

    return f"""# Histórico Análises com Backend Flexível — Valoris

Versão: {VERSAO_HISTORICO_BACKEND_FLEXIVEL_VALORIS}  
Gerado em: {_agora_iso()}

## Diagnóstico

Backend usado: {backend}  
Score experiência: {metricas['score_experiencia']}/100  
Análises: {metricas['analises']}  
Tickers: {metricas['tickers']}  
Score médio: {metricas['score_medio']}/100  
Compras: {metricas['compras']}  

Comparação CSV x SQLite: CSV={comparacao.get('csv')} | SQLite={comparacao.get('sqlite')} | status={comparacao.get('status')}

Risco: {metricas['risco']}  
Decisão: {metricas['decisao']}  
Próximo passo: {metricas['proximo_passo']}

## Últimas análises

{linhas_top}

## Leitura estratégica

Esta é a primeira página de experiência real usando backend flexível. A migração é segura porque CSV continua como padrão e SQLite entra como opção de leitura validada.
"""


def salvar_relatorio_historico_backend_markdown(backend: str = BACKEND_CSV) -> Path:
    CAMINHO_RELATORIO.write_text(
        gerar_relatorio_historico_backend_markdown(backend=backend),
        encoding="utf-8",
    )
    return CAMINHO_RELATORIO


def gerar_manifesto_historico_backend(backend: str = BACKEND_CSV) -> Dict[str, Any]:
    return {
        "produto": "Valoris",
        "versao": VERSAO_HISTORICO_BACKEND_FLEXIVEL_VALORIS,
        "modulo": "historico_backend_flexivel_valoris",
        "data_hora": _agora_iso(),
        "backend": backend,
        "metricas": calcular_metricas_historico_backend(backend=backend),
        "principio": "migração real começa por leitura segura, fallback e experiência estável",
        "proxima_etapa": "substituir ou integrar a página antiga de Histórico Análises com feature flag",
    }


def salvar_manifesto_historico_backend(backend: str = BACKEND_CSV) -> Path:
    CAMINHO_MANIFESTO.write_text(
        json.dumps(gerar_manifesto_historico_backend(backend=backend), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return CAMINHO_MANIFESTO


def renderizar_historico_backend_flexivel_valoris() -> None:
    st.subheader("Histórico Análises — Backend Flexível")
    st.caption(
        "Primeira página migrada com segurança: leitura pelo Repository Backend, CSV como padrão e SQLite laboratório como opção."
    )

    backend_atual = backend_padrao_flexivel()
    opcoes_backend = [BACKEND_CSV, BACKEND_SQLITE]

    if backend_atual not in opcoes_backend:
        backend_atual = BACKEND_CSV

    col_config1, col_config2 = st.columns(2)

    backend = col_config1.selectbox(
        "Backend de leitura",
        opcoes_backend,
        index=opcoes_backend.index(backend_atual),
        help="CSV é o modo seguro. SQLite é laboratório validado.",
    )

    max_registros = col_config2.slider("Registros carregados", 50, 2000, 800)

    metricas = calcular_metricas_historico_backend(backend=backend)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Score experiência", f"{metricas['score_experiencia']}/100")
    col2.metric("Análises", metricas["analises"])
    col3.metric("Tickers", metricas["tickers"])
    col4.metric("Score médio", f"{metricas['score_medio']}/100")
    col5.metric("Compras", metricas["compras"])

    if metricas["risco"] == "Baixo":
        st.success(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    elif metricas["risco"] == "Médio":
        st.warning(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    else:
        st.info(f"{metricas['decisao']} — {metricas['proximo_passo']}")

    st.divider()

    st.markdown("### Comparação CSV x SQLite")
    st.json(metricas["comparacao_csv_sqlite"])

    st.divider()

    registros = carregar_historico_flexivel(backend=backend, max_registros=max_registros)

    st.markdown("### Filtros premium")

    col_f1, col_f2, col_f3, col_f4 = st.columns(4)

    filtro_ticker = col_f1.text_input("Ticker", value="")
    decisoes = ["Todas"] + sorted(list({item["decisao"] for item in registros if item["decisao"]}))
    filtro_decisao = col_f2.selectbox("Decisão", decisoes)
    score_minimo = col_f3.slider("Score mínimo", 0, 100, 0)
    margem_minima = col_f4.slider("Margem mínima", -100, 100, -100)

    filtrados = filtrar_historico(
        registros,
        ticker=filtro_ticker,
        decisao=filtro_decisao,
        score_minimo=score_minimo,
        margem_minima=margem_minima,
    )

    tabela = [
        {
            "data": item["data_hora"],
            "ticker": item["ticker"],
            "empresa": item["empresa"],
            "setor": item["setor"],
            "preço atual": _moeda(item["preco_atual"]),
            "preço teto": _moeda(item["preco_teto"]),
            "margem": _pct(item["margem_seguranca_atual"]),
            "score": item["score_final"],
            "decisão": item["decisao"],
            "convicção": item["nivel_conviccao"],
            "modelo": item["modelo_preco_teto"],
        }
        for item in filtrados
    ]

    st.markdown("### Histórico encontrado")
    st.dataframe(tabela, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Revisão guiada")

    if filtrados:
        opcoes = [
            f"{item['ticker']} | score {item['score_final']} | {item['decisao']} | {item['data_hora']}"
            for item in filtrados
        ]

        escolha = st.selectbox("Análise para revisar", opcoes)
        item = filtrados[opcoes.index(escolha)]

        col_a, col_b, col_c, col_d = st.columns(4)
        col_a.metric("Ticker", item["ticker"])
        col_b.metric("Preço atual", _moeda(item["preco_atual"]))
        col_c.metric("Preço teto", _moeda(item["preco_teto"]))
        col_d.metric("Score", f"{item['score_final']}/100")

        st.markdown(f"**Empresa:** {item['empresa']}")
        st.markdown(f"**Decisão original:** {item['decisao']}")
        st.markdown(f"**Observação:** {item['observacao'] or 'Sem observação.'}")

        decisao_revisao = st.selectbox(
            "Decisão da revisão",
            [
                "Manter em estudo",
                "Enviar para Watchlist",
                "Gerar dossiê",
                "Aguardar preço melhor",
                "Revisar premissas",
                "Descartar por enquanto",
            ],
        )

        observacao = st.text_area(
            "Observação da revisão",
            value=f"Revisão feita no Histórico Backend Flexível usando backend {backend}.",
            height=90,
        )

        if st.button("Salvar revisão do histórico"):
            salvar_decisao_historico_backend(
                backend=backend,
                ticker=item["ticker"],
                decisao=decisao_revisao,
                score_final=item["score_final"],
                observacao=observacao,
            )
            st.success("Revisão registrada.")
            st.rerun()
    else:
        st.info("Nenhuma análise encontrada com os filtros atuais.")

    decisoes_salvas = carregar_decisoes_historico_backend()

    if decisoes_salvas:
        st.markdown("### Revisões salvas")
        st.dataframe(decisoes_salvas, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Relatórios")

    col_r1, col_r2 = st.columns(2)

    if col_r1.button("Salvar relatório do histórico flexível"):
        caminho = salvar_relatorio_historico_backend_markdown(backend=backend)
        st.success(f"Relatório salvo em {caminho}")

    if col_r2.button("Salvar manifesto do histórico flexível"):
        caminho = salvar_manifesto_historico_backend(backend=backend)
        st.success(f"Manifesto salvo em {caminho}")

    st.download_button(
        "Baixar relatório do histórico flexível (.md)",
        data=gerar_relatorio_historico_backend_markdown(backend=backend),
        file_name="RELATORIO_HISTORICO_BACKEND_FLEXIVEL_VALORIS.md",
        mime="text/markdown",
    )


def executar_autoteste_historico_backend_flexivel_valoris() -> Dict[str, Any]:
    metricas_csv = calcular_metricas_historico_backend(backend=BACKEND_CSV)

    return {
        "ok": True,
        "versao": VERSAO_HISTORICO_BACKEND_FLEXIVEL_VALORIS,
        "metricas": {
            "score_experiencia_csv": metricas_csv["score_experiencia"],
            "analises_csv": metricas_csv["analises"],
            "tickers_csv": metricas_csv["tickers"],
        },
    }
