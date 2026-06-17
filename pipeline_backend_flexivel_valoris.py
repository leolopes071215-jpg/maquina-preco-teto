# pipeline_backend_flexivel_valoris.py
# Valoris — Pipeline Decisão com Backend Flexível v3.10.9
# ------------------------------------------------------------
# Objetivo:
# - Criar a primeira página com escrita controlada usando Repository Backend.
# - Ler ranking inteligente, histórico e pipeline via backend flexível.
# - Manter CSV como backend seguro para escrita.
# - Manter SQLite em modo laboratório/leitura, sem forçar escrita.
# - Transformar oportunidades em ações operacionais com prioridade, prazo e rollback.

from __future__ import annotations

import csv
import json
from collections import Counter, deque
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st


VERSAO_PIPELINE_BACKEND_FLEXIVEL_VALORIS = "3.10.9"

BACKEND_CSV = "csv"
BACKEND_SQLITE = "sqlite_laboratorio"

ENTIDADE_PIPELINE = "pipeline_acoes"

CAMINHO_PIPELINE_FALLBACK = Path("pipeline_acoes_backend_flexivel_valoris.csv")
CAMINHO_DECISOES = Path("decisoes_pipeline_backend_flexivel_valoris.csv")
CAMINHO_RELATORIO = Path("RELATORIO_PIPELINE_BACKEND_FLEXIVEL_VALORIS.md")
CAMINHO_MANIFESTO = Path("manifesto_pipeline_backend_flexivel_valoris.json")

CAMPOS_PIPELINE = [
    "data_hora",
    "ticker",
    "empresa",
    "tipo_acao",
    "prioridade",
    "status",
    "responsavel",
    "prazo",
    "origem",
    "score_inteligente",
    "classificacao",
    "observacao",
]

CAMPOS_DECISOES = [
    "data_hora",
    "backend_leitura",
    "backend_escrita",
    "ticker",
    "empresa",
    "tipo_acao",
    "prioridade",
    "status",
    "prazo",
    "observacao",
]


def _agora_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat(sep=" ")


def _txt(valor: Any) -> str:
    return "" if valor is None else str(valor).strip()


def _int(valor: Any, padrao: int = 0) -> int:
    try:
        if valor is None:
            return padrao

        if isinstance(valor, str):
            valor = valor.replace("%", "").replace(".", "").replace(",", ".").strip()

            if valor == "":
                return padrao

        return int(float(valor))
    except Exception:
        return padrao


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


def _garantir_csv(caminho: Path, campos: List[str]) -> None:
    if caminho.exists():
        return

    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()


def _data_padrao(dias: int = 30) -> str:
    return (date.today() + timedelta(days=dias)).isoformat()


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


def salvar_backend(entidade: str, dados: Dict[str, Any], backend: str = BACKEND_CSV) -> bool:
    try:
        from repository_backend_sqlite_valoris import salvar_registro_backend

        salvar_registro_backend(entidade, dados, backend=backend)
        return True
    except Exception:
        return False


def carregar_pipeline_fallback(max_registros: int = 1000) -> List[Dict[str, Any]]:
    _garantir_csv(CAMINHO_PIPELINE_FALLBACK, CAMPOS_PIPELINE)

    try:
        with CAMINHO_PIPELINE_FALLBACK.open("r", newline="", encoding="utf-8") as arquivo:
            leitor = csv.DictReader(arquivo)
            return list(deque(leitor, maxlen=max_registros))
    except Exception:
        return []


def salvar_pipeline_fallback(dados: Dict[str, Any]) -> Path:
    _garantir_csv(CAMINHO_PIPELINE_FALLBACK, CAMPOS_PIPELINE)

    linha = {campo: _txt(dados.get(campo, "")) for campo in CAMPOS_PIPELINE}

    with CAMINHO_PIPELINE_FALLBACK.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_PIPELINE)
        escritor.writerow(linha)

    return CAMINHO_PIPELINE_FALLBACK


def carregar_pipeline(backend: str = BACKEND_CSV, max_registros: int = 1000) -> List[Dict[str, Any]]:
    registros = listar_backend(ENTIDADE_PIPELINE, backend=backend, max_registros=max_registros)

    if registros:
        return [normalizar_acao_pipeline(item) for item in registros]

    return [normalizar_acao_pipeline(item) for item in carregar_pipeline_fallback(max_registros=max_registros)]


def normalizar_acao_pipeline(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "data_hora": _txt(item.get("data_hora")) or _txt(item.get("criado_em")) or _txt(item.get("data_registro")),
        "ticker": _txt(item.get("ticker")).upper(),
        "empresa": _txt(item.get("empresa")) or _txt(item.get("nome_empresa")) or _txt(item.get("ticker")).upper(),
        "tipo_acao": _txt(item.get("tipo_acao")) or _txt(item.get("acao")) or _txt(item.get("etapa")),
        "prioridade": _txt(item.get("prioridade")) or "Média",
        "status": _txt(item.get("status")) or "Aberta",
        "responsavel": _txt(item.get("responsavel")) or "Fundador",
        "prazo": _txt(item.get("prazo")) or _txt(item.get("data_revisao")),
        "origem": _txt(item.get("origem")) or "Pipeline Backend",
        "score_inteligente": _txt(item.get("score_inteligente")),
        "classificacao": _txt(item.get("classificacao")),
        "observacao": _txt(item.get("observacao")) or _txt(item.get("observacoes")),
    }


def gerar_ranking_backend(backend: str = BACKEND_CSV) -> List[Dict[str, Any]]:
    try:
        from analise_inteligente_backend_valoris import gerar_ranking_inteligente_backend

        return gerar_ranking_inteligente_backend(backend=backend, max_registros=2000)
    except Exception:
        return []


def classificar_prioridade_para_pipeline(item: Dict[str, Any]) -> str:
    classificacao = _txt(item.get("classificacao"))
    score = _int(item.get("score_inteligente"))

    if classificacao == "Alta prioridade" or score >= 80:
        return "Alta"

    if classificacao.startswith("Boa candidata") or score >= 65:
        return "Média"

    if classificacao == "Premissas incompletas":
        return "Alta"

    if classificacao in {"Risco elevado", "Qualidade fraca"}:
        return "Baixa"

    return "Média"


def sugerir_tipo_acao_pipeline(item: Dict[str, Any]) -> str:
    classificacao = _txt(item.get("classificacao"))
    watchlist = _txt(item.get("ja_na_watchlist"))

    if classificacao == "Alta prioridade" and watchlist == "Sim":
        return "Gerar dossiê premium e definir gatilho"

    if classificacao == "Alta prioridade":
        return "Enviar para Watchlist e gerar dossiê"

    if classificacao.startswith("Boa candidata") and watchlist == "Sim":
        return "Acompanhar próximo evento"

    if classificacao.startswith("Boa candidata"):
        return "Adicionar à Watchlist"

    if classificacao == "Premissas incompletas":
        return "Revisar premissas do Motor"

    if classificacao == "Risco elevado":
        return "Revisar riscos antes de avançar"

    if classificacao == "Qualidade fraca":
        return "Arquivar temporariamente"

    return "Aguardar novo gatilho"


def sugerir_prazo_pipeline(item: Dict[str, Any]) -> str:
    prioridade = classificar_prioridade_para_pipeline(item)
    classificacao = _txt(item.get("classificacao"))

    if classificacao == "Premissas incompletas":
        return _data_padrao(7)

    if prioridade == "Alta":
        return _data_padrao(14)

    if prioridade == "Média":
        return _data_padrao(30)

    return _data_padrao(60)


def gerar_sugestoes_pipeline(backend: str = BACKEND_CSV) -> List[Dict[str, Any]]:
    ranking = gerar_ranking_backend(backend=backend)
    pipeline_atual = carregar_pipeline(backend=BACKEND_CSV, max_registros=3000)

    chaves_abertas = {
        (_txt(item.get("ticker")).upper(), _txt(item.get("tipo_acao")).lower())
        for item in pipeline_atual
        if _txt(item.get("status")).lower() not in {"concluída", "concluida", "cancelada", "arquivada"}
    }

    sugestoes = []

    for item in ranking:
        ticker = _txt(item.get("ticker")).upper()

        if not ticker:
            continue

        tipo_acao = sugerir_tipo_acao_pipeline(item)
        chave = (ticker, tipo_acao.lower())

        if chave in chaves_abertas:
            continue

        sugestoes.append(
            {
                "data_hora": _agora_iso(),
                "ticker": ticker,
                "empresa": _txt(item.get("empresa")) or ticker,
                "tipo_acao": tipo_acao,
                "prioridade": classificar_prioridade_para_pipeline(item),
                "status": "Aberta",
                "responsavel": "Fundador",
                "prazo": sugerir_prazo_pipeline(item),
                "origem": f"Análise Backend {VERSAO_PIPELINE_BACKEND_FLEXIVEL_VALORIS}",
                "score_inteligente": _txt(item.get("score_inteligente")),
                "classificacao": _txt(item.get("classificacao")),
                "observacao": _txt(item.get("acao_recomendada")),
            }
        )

    ordem_prioridade = {"Alta": 1, "Média": 2, "Baixa": 3}
    sugestoes.sort(
        key=lambda item: (
            ordem_prioridade.get(item["prioridade"], 9),
            item["prazo"],
            item["ticker"],
        )
    )

    return sugestoes


def salvar_acao_pipeline_controlada(dados: Dict[str, Any], backend_escrita: str = BACKEND_CSV) -> Dict[str, Any]:
    dados = {campo: dados.get(campo, "") for campo in CAMPOS_PIPELINE}
    dados["data_hora"] = dados.get("data_hora") or _agora_iso()

    if backend_escrita != BACKEND_CSV:
        return {
            "ok": False,
            "mensagem": "Escrita em SQLite permanece bloqueada nesta versão. Use CSV como backend seguro.",
            "backend_escrita": backend_escrita,
        }

    ok_repo = salvar_backend(ENTIDADE_PIPELINE, dados, backend=BACKEND_CSV)

    if not ok_repo:
        salvar_pipeline_fallback(dados)

    salvar_decisao_pipeline(
        backend_leitura=_txt(dados.get("origem")),
        backend_escrita=backend_escrita,
        ticker=_txt(dados.get("ticker")),
        empresa=_txt(dados.get("empresa")),
        tipo_acao=_txt(dados.get("tipo_acao")),
        prioridade=_txt(dados.get("prioridade")),
        status=_txt(dados.get("status")),
        prazo=_txt(dados.get("prazo")),
        observacao=_txt(dados.get("observacao")),
    )

    return {
        "ok": True,
        "mensagem": "Ação salva com escrita controlada em CSV.",
        "backend_escrita": backend_escrita,
        "repo_usado": ok_repo,
    }


def salvar_decisao_pipeline(
    backend_leitura: str,
    backend_escrita: str,
    ticker: str,
    empresa: str,
    tipo_acao: str,
    prioridade: str,
    status: str,
    prazo: str,
    observacao: str = "",
) -> Path:
    _garantir_csv(CAMINHO_DECISOES, CAMPOS_DECISOES)

    with CAMINHO_DECISOES.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISOES)
        escritor.writerow(
            {
                "data_hora": _agora_iso(),
                "backend_leitura": _txt(backend_leitura),
                "backend_escrita": _txt(backend_escrita),
                "ticker": _txt(ticker).upper(),
                "empresa": _txt(empresa),
                "tipo_acao": _txt(tipo_acao),
                "prioridade": _txt(prioridade),
                "status": _txt(status),
                "prazo": _txt(prazo),
                "observacao": _txt(observacao),
            }
        )

    return CAMINHO_DECISOES


def carregar_decisoes_pipeline(max_registros: int = 300) -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_DECISOES, CAMPOS_DECISOES)

    try:
        with CAMINHO_DECISOES.open("r", newline="", encoding="utf-8") as arquivo:
            leitor = csv.DictReader(arquivo)
            return list(deque(leitor, maxlen=max_registros))
    except Exception:
        return []


def calcular_metricas_pipeline_backend(backend_leitura: str = BACKEND_CSV) -> Dict[str, Any]:
    ranking = gerar_ranking_backend(backend=backend_leitura)
    sugestoes = gerar_sugestoes_pipeline(backend=backend_leitura)
    pipeline = carregar_pipeline(backend=BACKEND_CSV)

    status_counter = Counter(_txt(item.get("status")) or "Sem status" for item in pipeline)
    prioridade_counter = Counter(_txt(item.get("prioridade")) or "Sem prioridade" for item in pipeline)

    abertas = len([
        item for item in pipeline
        if _txt(item.get("status")).lower() not in {"concluída", "concluida", "cancelada", "arquivada"}
    ])

    score_controle = 35
    score_controle += min(len(ranking) * 8, 24)
    score_controle += min(len(sugestoes) * 7, 21)

    if pipeline:
        score_controle += 10

    if abertas <= 20:
        score_controle += 10
    else:
        score_controle -= 10

    score_controle = max(0, min(100, int(score_controle)))

    if not ranking:
        risco = "Médio"
        decisao = "Pipeline sem ranking inteligente para gerar ações"
        proximo = "Criar análises e validar Análise Principal."
    elif sugestoes:
        risco = "Baixo/Médio"
        decisao = "Pipeline pronto para escrita controlada de ações"
        proximo = "Salvar primeiras ações sugeridas em CSV e validar no fluxo antigo."
    else:
        risco = "Baixo"
        decisao = "Pipeline sem novas ações pendentes"
        proximo = "Acompanhar status das ações existentes."

    return {
        "versao": VERSAO_PIPELINE_BACKEND_FLEXIVEL_VALORIS,
        "backend_leitura": backend_leitura,
        "backend_escrita": BACKEND_CSV,
        "gerado_em": _agora_iso(),
        "score_controle": score_controle,
        "ativos_no_ranking": len(ranking),
        "sugestoes": len(sugestoes),
        "acoes_pipeline": len(pipeline),
        "acoes_abertas": abertas,
        "status": dict(status_counter),
        "prioridades": dict(prioridade_counter),
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo,
    }


def gerar_relatorio_pipeline_backend_markdown(backend_leitura: str = BACKEND_CSV) -> str:
    metricas = calcular_metricas_pipeline_backend(backend_leitura=backend_leitura)
    sugestoes = gerar_sugestoes_pipeline(backend=backend_leitura)
    pipeline = carregar_pipeline(backend=BACKEND_CSV)

    linhas_sugestoes = "\n".join(
        [
            f"- **{item['ticker']} — {item['empresa']}**: {item['tipo_acao']} | prioridade {item['prioridade']} | prazo {item['prazo']}."
            for item in sugestoes[:20]
        ]
    ) or "- Nenhuma sugestão nova."

    linhas_pipeline = "\n".join(
        [
            f"- **{item['ticker']} — {item['empresa']}**: {item['tipo_acao']} | {item['status']} | prazo {item['prazo']}."
            for item in pipeline[:20]
        ]
    ) or "- Nenhuma ação registrada."

    return f"""# Pipeline Decisão com Backend Flexível — Valoris

Versão: {VERSAO_PIPELINE_BACKEND_FLEXIVEL_VALORIS}  
Gerado em: {_agora_iso()}

## Diagnóstico

Backend de leitura: {backend_leitura}  
Backend de escrita: {BACKEND_CSV}  
Score controle: {metricas['score_controle']}/100  
Ativos no ranking: {metricas['ativos_no_ranking']}  
Sugestões: {metricas['sugestoes']}  
Ações no pipeline: {metricas['acoes_pipeline']}  
Ações abertas: {metricas['acoes_abertas']}  

Risco: {metricas['risco']}  
Decisão: {metricas['decisao']}  
Próximo passo: {metricas['proximo_passo']}

## Sugestões de ação

{linhas_sugestoes}

## Pipeline atual

{linhas_pipeline}

## Estratégia

Esta é a primeira etapa de escrita controlada com backend flexível. A escrita fica restrita ao CSV seguro, enquanto SQLite permanece laboratório. Assim, o produto avança sem comprometer dados reais.
"""


def salvar_relatorio_pipeline_backend(backend_leitura: str = BACKEND_CSV) -> Path:
    CAMINHO_RELATORIO.write_text(
        gerar_relatorio_pipeline_backend_markdown(backend_leitura=backend_leitura),
        encoding="utf-8",
    )
    return CAMINHO_RELATORIO


def gerar_manifesto_pipeline_backend(backend_leitura: str = BACKEND_CSV) -> Dict[str, Any]:
    return {
        "produto": "Valoris",
        "versao": VERSAO_PIPELINE_BACKEND_FLEXIVEL_VALORIS,
        "modulo": "pipeline_backend_flexivel_valoris",
        "data_hora": _agora_iso(),
        "backend_leitura": backend_leitura,
        "backend_escrita": BACKEND_CSV,
        "metricas": calcular_metricas_pipeline_backend(backend_leitura=backend_leitura),
        "sugestoes": gerar_sugestoes_pipeline(backend=backend_leitura),
        "principio": "escrita controlada primeiro, migração definitiva depois",
        "proxima_etapa": "promover Pipeline Backend para principal após validar ações reais",
    }


def salvar_manifesto_pipeline_backend(backend_leitura: str = BACKEND_CSV) -> Path:
    CAMINHO_MANIFESTO.write_text(
        json.dumps(gerar_manifesto_pipeline_backend(backend_leitura=backend_leitura), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return CAMINHO_MANIFESTO


def renderizar_pipeline_backend_flexivel_valoris() -> None:
    st.subheader("Pipeline Decisão — Backend Flexível")
    st.caption(
        "Primeira etapa de escrita controlada: leitura flexível, escrita segura em CSV e SQLite apenas como laboratório."
    )

    backend_padrao = obter_backend_padrao()
    opcoes_backend = [BACKEND_CSV, BACKEND_SQLITE]

    if backend_padrao not in opcoes_backend:
        backend_padrao = BACKEND_CSV

    col_config1, col_config2 = st.columns(2)

    backend_leitura = col_config1.selectbox(
        "Backend de leitura",
        opcoes_backend,
        index=opcoes_backend.index(backend_padrao),
    )

    backend_escrita = col_config2.selectbox(
        "Backend de escrita",
        [BACKEND_CSV],
        index=0,
        help="Nesta versão, a escrita em SQLite fica bloqueada por segurança.",
    )

    metricas = calcular_metricas_pipeline_backend(backend_leitura=backend_leitura)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Score controle", f"{metricas['score_controle']}/100")
    col2.metric("Ranking", metricas["ativos_no_ranking"])
    col3.metric("Sugestões", metricas["sugestoes"])
    col4.metric("Ações pipeline", metricas["acoes_pipeline"])
    col5.metric("Abertas", metricas["acoes_abertas"])

    if metricas["risco"] == "Baixo":
        st.success(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    elif metricas["risco"] == "Médio":
        st.warning(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    else:
        st.info(f"{metricas['decisao']} — {metricas['proximo_passo']}")

    st.divider()

    st.markdown("### Sugestões geradas pela Análise Principal")

    sugestoes = gerar_sugestoes_pipeline(backend=backend_leitura)

    st.dataframe(sugestoes, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Salvar ação controlada")

    if sugestoes:
        opcoes = [
            f"{item['ticker']} | {item['prioridade']} | {item['tipo_acao']} | prazo {item['prazo']}"
            for item in sugestoes
        ]

        escolha = st.selectbox("Sugestão", opcoes)
        item = dict(sugestoes[opcoes.index(escolha)])

        col_a, col_b, col_c = st.columns(3)
        item["prioridade"] = col_a.selectbox(
            "Prioridade",
            ["Alta", "Média", "Baixa"],
            index=["Alta", "Média", "Baixa"].index(item["prioridade"]) if item["prioridade"] in ["Alta", "Média", "Baixa"] else 1,
        )
        item["status"] = col_b.selectbox("Status", ["Aberta", "Em andamento", "Concluída", "Arquivada"])
        item["prazo"] = col_c.date_input("Prazo", value=date.fromisoformat(item["prazo"])).isoformat()

        item["tipo_acao"] = st.text_input("Tipo de ação", value=item["tipo_acao"])
        item["observacao"] = st.text_area("Observação", value=item["observacao"], height=90)

        if st.button("Salvar ação no Pipeline"):
            resultado = salvar_acao_pipeline_controlada(item, backend_escrita=backend_escrita)

            if resultado["ok"]:
                st.success(resultado["mensagem"])
                st.rerun()
            else:
                st.error(resultado["mensagem"])
    else:
        st.info("Nenhuma sugestão nova disponível no momento.")

    st.divider()

    st.markdown("### Pipeline atual")

    pipeline = carregar_pipeline(backend=BACKEND_CSV)
    st.dataframe(pipeline, use_container_width=True, hide_index=True)

    decisoes = carregar_decisoes_pipeline()

    if decisoes:
        st.markdown("### Decisões de escrita controlada")
        st.dataframe(decisoes, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Relatórios")

    col_r1, col_r2 = st.columns(2)

    if col_r1.button("Salvar relatório do Pipeline Backend"):
        caminho = salvar_relatorio_pipeline_backend(backend_leitura=backend_leitura)
        st.success(f"Relatório salvo em {caminho}")

    if col_r2.button("Salvar manifesto do Pipeline Backend"):
        caminho = salvar_manifesto_pipeline_backend(backend_leitura=backend_leitura)
        st.success(f"Manifesto salvo em {caminho}")

    st.download_button(
        "Baixar relatório do Pipeline Backend (.md)",
        data=gerar_relatorio_pipeline_backend_markdown(backend_leitura=backend_leitura),
        file_name="RELATORIO_PIPELINE_BACKEND_FLEXIVEL_VALORIS.md",
        mime="text/markdown",
    )


def executar_autoteste_pipeline_backend_flexivel_valoris() -> Dict[str, Any]:
    metricas = calcular_metricas_pipeline_backend(backend_leitura=BACKEND_CSV)

    return {
        "ok": True,
        "versao": VERSAO_PIPELINE_BACKEND_FLEXIVEL_VALORIS,
        "metricas": {
            "score_controle": metricas["score_controle"],
            "ativos_no_ranking": metricas["ativos_no_ranking"],
            "sugestoes": metricas["sugestoes"],
        },
    }
