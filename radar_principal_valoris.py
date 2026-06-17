# radar_principal_valoris.py
# Valoris — Radar Principal v3.11.1
# ------------------------------------------------------------
# Objetivo:
# - Conectar o Pipeline Principal a uma central executiva de acompanhamento.
# - Mostrar ações abertas, atrasos, próximas revisões, prioridades e próximos movimentos.
# - Manter leitura segura pelo pipeline atual em CSV.
# - Criar visão premium de acompanhamento: análise -> decisão -> ação -> revisão.

from __future__ import annotations

import csv
import json
from collections import Counter, deque
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st


VERSAO_RADAR_PRINCIPAL_VALORIS = "3.11.1"

BACKEND_CSV = "csv"

CAMINHO_DECISOES = Path("decisoes_radar_principal_valoris.csv")
CAMINHO_RELATORIO = Path("RELATORIO_RADAR_PRINCIPAL_VALORIS.md")
CAMINHO_MANIFESTO = Path("manifesto_radar_principal_valoris.json")

CAMPOS_DECISOES = [
    "data_hora",
    "ticker",
    "empresa",
    "tipo_alerta",
    "prioridade",
    "status",
    "acao_recomendada",
    "observacao",
]


def _agora_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat(sep=" ")


def _txt(valor: Any) -> str:
    return "" if valor is None else str(valor).strip()


def _data(valor: Any) -> Optional[date]:
    texto = _txt(valor)

    if not texto:
        return None

    formatos = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y-%m-%d %H:%M:%S",
    ]

    for formato in formatos:
        try:
            return datetime.strptime(texto, formato).date()
        except Exception:
            continue

    try:
        return datetime.fromisoformat(texto).date()
    except Exception:
        return None


def _dias_ate(valor: Any) -> Optional[int]:
    data = _data(valor)

    if data is None:
        return None

    return (data - date.today()).days


def _garantir_csv(caminho: Path, campos: List[str]) -> None:
    if caminho.exists():
        return

    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()


def carregar_pipeline_principal(max_registros: int = 2000) -> List[Dict[str, Any]]:
    try:
        from pipeline_backend_flexivel_valoris import carregar_pipeline

        return carregar_pipeline(backend=BACKEND_CSV, max_registros=max_registros)
    except Exception:
        return []


def gerar_sugestoes_pipeline(max_registros: int = 2000) -> List[Dict[str, Any]]:
    try:
        from pipeline_backend_flexivel_valoris import gerar_sugestoes_pipeline

        return gerar_sugestoes_pipeline(backend=BACKEND_CSV)[:max_registros]
    except Exception:
        return []


def calcular_metricas_pipeline_base() -> Dict[str, Any]:
    try:
        from pipeline_backend_flexivel_valoris import calcular_metricas_pipeline_backend

        return calcular_metricas_pipeline_backend(backend_leitura=BACKEND_CSV)
    except Exception:
        return {}


def status_aberto(status: Any) -> bool:
    texto = _txt(status).lower()

    if not texto:
        return True

    fechados = {"concluída", "concluida", "cancelada", "arquivada", "fechada", "finalizada"}

    return texto not in fechados


def classificar_alerta(item: Dict[str, Any]) -> Dict[str, Any]:
    prazo = _data(item.get("prazo"))
    dias = _dias_ate(item.get("prazo"))
    prioridade = _txt(item.get("prioridade")) or "Média"
    status = _txt(item.get("status")) or "Aberta"
    ticker = _txt(item.get("ticker")).upper()
    tipo_acao = _txt(item.get("tipo_acao"))

    if not status_aberto(status):
        return {
            **item,
            "tipo_alerta": "Concluída/fechada",
            "criticidade": "Baixa",
            "dias_ate_prazo": dias,
            "acao_recomendada_radar": "Manter registro histórico.",
        }

    if prazo is None:
        return {
            **item,
            "tipo_alerta": "Sem prazo",
            "criticidade": "Média",
            "dias_ate_prazo": "",
            "acao_recomendada_radar": f"Definir prazo para {ticker} antes de avançar.",
        }

    if dias is not None and dias < 0:
        return {
            **item,
            "tipo_alerta": "Atrasada",
            "criticidade": "Alta",
            "dias_ate_prazo": dias,
            "acao_recomendada_radar": f"Revisar imediatamente a ação de {ticker}: {tipo_acao}.",
        }

    if prioridade == "Alta" and dias is not None and dias <= 14:
        return {
            **item,
            "tipo_alerta": "Prioridade alta próxima",
            "criticidade": "Alta",
            "dias_ate_prazo": dias,
            "acao_recomendada_radar": f"Executar ou revisar {ticker} nos próximos dias.",
        }

    if dias is not None and dias <= 7:
        return {
            **item,
            "tipo_alerta": "Próxima revisão",
            "criticidade": "Média/Alta",
            "dias_ate_prazo": dias,
            "acao_recomendada_radar": f"Preparar revisão de {ticker} antes do prazo.",
        }

    if dias is not None and dias <= 30:
        return {
            **item,
            "tipo_alerta": "Acompanhar no mês",
            "criticidade": "Média",
            "dias_ate_prazo": dias,
            "acao_recomendada_radar": f"Acompanhar {ticker} dentro do ciclo mensal.",
        }

    return {
        **item,
        "tipo_alerta": "Monitoramento",
        "criticidade": "Baixa",
        "dias_ate_prazo": dias,
        "acao_recomendada_radar": f"Manter {ticker} em monitoramento.",
    }


def gerar_radar_principal() -> List[Dict[str, Any]]:
    pipeline = carregar_pipeline_principal()
    alertas = [classificar_alerta(item) for item in pipeline]

    ordem_criticidade = {"Alta": 1, "Média/Alta": 2, "Média": 3, "Baixa": 4}

    alertas.sort(
        key=lambda item: (
            ordem_criticidade.get(_txt(item.get("criticidade")), 9),
            9999 if item.get("dias_ate_prazo") in {"", None} else int(item.get("dias_ate_prazo")),
            _txt(item.get("ticker")),
        )
    )

    return alertas


def calcular_metricas_radar_principal() -> Dict[str, Any]:
    alertas = gerar_radar_principal()
    sugestoes = gerar_sugestoes_pipeline()
    base = calcular_metricas_pipeline_base()

    abertas = [item for item in alertas if status_aberto(item.get("status"))]
    atrasadas = [item for item in alertas if item.get("tipo_alerta") == "Atrasada"]
    proximas = [
        item for item in alertas
        if item.get("tipo_alerta") in {"Próxima revisão", "Prioridade alta próxima"}
    ]
    altas = [item for item in alertas if item.get("criticidade") == "Alta"]
    sem_prazo = [item for item in alertas if item.get("tipo_alerta") == "Sem prazo"]

    score = 45
    score += min(len(alertas) * 6, 18)

    if abertas:
        score += 10

    if sugestoes:
        score += 8

    if atrasadas:
        score -= min(len(atrasadas) * 12, 30)

    if sem_prazo:
        score -= min(len(sem_prazo) * 8, 20)

    if proximas:
        score += 7

    score += min(int(base.get("score_controle", 0) or 0) // 10, 10)
    score = max(0, min(100, int(score)))

    if not alertas:
        risco = "Médio"
        decisao = "Radar sem ações para acompanhar"
        proximo = "Criar ações no Pipeline Principal."
    elif atrasadas:
        risco = "Alto"
        decisao = "Há ações atrasadas no radar"
        proximo = "Regularizar ações atrasadas antes de criar novas prioridades."
    elif sem_prazo:
        risco = "Médio"
        decisao = "Há ações sem prazo definido"
        proximo = "Definir prazos para todas as ações abertas."
    elif score >= 85:
        risco = "Baixo"
        decisao = "Radar pronto para acompanhamento executivo"
        proximo = "Usar como painel diário/semanal de decisão."
    else:
        risco = "Baixo/Médio"
        decisao = "Radar funcional, ainda com pouca massa operacional"
        proximo = "Criar mais ações reais e acompanhar ciclos de revisão."

    return {
        "versao": VERSAO_RADAR_PRINCIPAL_VALORIS,
        "gerado_em": _agora_iso(),
        "score_acompanhamento": score,
        "acoes_total": len(alertas),
        "acoes_abertas": len(abertas),
        "acoes_atrasadas": len(atrasadas),
        "proximas_revisoes": len(proximas),
        "alta_criticidade": len(altas),
        "sem_prazo": len(sem_prazo),
        "sugestoes_pipeline": len(sugestoes),
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo,
    }


def salvar_decisao_radar(item: Dict[str, Any], observacao: str = "") -> Path:
    _garantir_csv(CAMINHO_DECISOES, CAMPOS_DECISOES)

    with CAMINHO_DECISOES.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISOES)
        escritor.writerow(
            {
                "data_hora": _agora_iso(),
                "ticker": _txt(item.get("ticker")).upper(),
                "empresa": _txt(item.get("empresa")),
                "tipo_alerta": _txt(item.get("tipo_alerta")),
                "prioridade": _txt(item.get("prioridade")),
                "status": _txt(item.get("status")),
                "acao_recomendada": _txt(item.get("acao_recomendada_radar")),
                "observacao": _txt(observacao),
            }
        )

    return CAMINHO_DECISOES


def carregar_decisoes_radar(max_registros: int = 300) -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_DECISOES, CAMPOS_DECISOES)

    try:
        with CAMINHO_DECISOES.open("r", newline="", encoding="utf-8") as arquivo:
            leitor = csv.DictReader(arquivo)
            return list(deque(leitor, maxlen=max_registros))
    except Exception:
        return []


def gerar_relatorio_radar_principal_markdown() -> str:
    metricas = calcular_metricas_radar_principal()
    alertas = gerar_radar_principal()

    linhas = "\n".join(
        [
            f"- **{item.get('ticker')} — {item.get('empresa')}**: {item.get('tipo_alerta')} | criticidade {item.get('criticidade')} | prazo {item.get('prazo')} | ação: {item.get('acao_recomendada_radar')}"
            for item in alertas[:25]
        ]
    ) or "- Nenhuma ação no radar."

    return f"""# Radar Principal — Valoris

Versão: {VERSAO_RADAR_PRINCIPAL_VALORIS}  
Gerado em: {_agora_iso()}

## Diagnóstico

Score acompanhamento: {metricas['score_acompanhamento']}/100  
Ações totais: {metricas['acoes_total']}  
Ações abertas: {metricas['acoes_abertas']}  
Ações atrasadas: {metricas['acoes_atrasadas']}  
Próximas revisões: {metricas['proximas_revisoes']}  
Alta criticidade: {metricas['alta_criticidade']}  
Sem prazo: {metricas['sem_prazo']}  

Risco: {metricas['risco']}  
Decisão: {metricas['decisao']}  
Próximo passo: {metricas['proximo_passo']}

## Radar de ações

{linhas}

## Estratégia

Esta versão fecha o ciclo operacional do Valoris: análise, decisão, ação e acompanhamento. O Radar Principal vira o painel executivo para não deixar oportunidades e riscos se perderem.
"""


def salvar_relatorio_radar_principal() -> Path:
    CAMINHO_RELATORIO.write_text(gerar_relatorio_radar_principal_markdown(), encoding="utf-8")
    return CAMINHO_RELATORIO


def gerar_manifesto_radar_principal() -> Dict[str, Any]:
    return {
        "produto": "Valoris",
        "versao": VERSAO_RADAR_PRINCIPAL_VALORIS,
        "modulo": "radar_principal_valoris",
        "data_hora": _agora_iso(),
        "metricas": calcular_metricas_radar_principal(),
        "radar": gerar_radar_principal(),
        "principio": "decisão sem acompanhamento vira esquecimento; radar transforma análise em disciplina",
        "proxima_etapa": "promover radar como cockpit diário e conectar com alertas automáticos",
    }


def salvar_manifesto_radar_principal() -> Path:
    CAMINHO_MANIFESTO.write_text(
        json.dumps(gerar_manifesto_radar_principal(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return CAMINHO_MANIFESTO


def renderizar_radar_principal_valoris() -> None:
    st.subheader("Radar Principal")
    st.caption("Painel executivo de acompanhamento: ações abertas, prazos, atrasos, criticidade e próximos movimentos.")

    metricas = calcular_metricas_radar_principal()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Score acompanhamento", f"{metricas['score_acompanhamento']}/100")
    col2.metric("Abertas", metricas["acoes_abertas"])
    col3.metric("Atrasadas", metricas["acoes_atrasadas"])
    col4.metric("Próximas", metricas["proximas_revisoes"])
    col5.metric("Alta criticidade", metricas["alta_criticidade"])

    if metricas["risco"] == "Baixo":
        st.success(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    elif metricas["risco"] == "Alto":
        st.error(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    elif metricas["risco"] == "Médio":
        st.warning(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    else:
        st.info(f"{metricas['decisao']} — {metricas['proximo_passo']}")

    st.divider()

    alertas = gerar_radar_principal()

    st.markdown("### Radar de ações")

    col_f1, col_f2, col_f3 = st.columns(3)
    filtro_ticker = col_f1.text_input("Ticker", value="")
    tipos = ["Todos"] + sorted({item.get("tipo_alerta", "") for item in alertas if item.get("tipo_alerta")})
    criticidades = ["Todas"] + sorted({item.get("criticidade", "") for item in alertas if item.get("criticidade")})
    filtro_tipo = col_f2.selectbox("Tipo de alerta", tipos)
    filtro_criticidade = col_f3.selectbox("Criticidade", criticidades)

    filtrados = []

    for item in alertas:
        ticker = _txt(item.get("ticker")).upper()

        if filtro_ticker.strip() and filtro_ticker.strip().upper() not in ticker:
            continue

        if filtro_tipo != "Todos" and item.get("tipo_alerta") != filtro_tipo:
            continue

        if filtro_criticidade != "Todas" and item.get("criticidade") != filtro_criticidade:
            continue

        filtrados.append(item)

    tabela = [
        {
            "ticker": item.get("ticker"),
            "empresa": item.get("empresa"),
            "tipo alerta": item.get("tipo_alerta"),
            "criticidade": item.get("criticidade"),
            "prioridade": item.get("prioridade"),
            "status": item.get("status"),
            "prazo": item.get("prazo"),
            "dias": item.get("dias_ate_prazo"),
            "tipo ação": item.get("tipo_acao"),
            "ação recomendada": item.get("acao_recomendada_radar"),
        }
        for item in filtrados
    ]

    st.dataframe(tabela, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Decisão guiada do Radar")

    if filtrados:
        opcoes = [
            f"{item.get('ticker')} | {item.get('tipo_alerta')} | {item.get('criticidade')} | prazo {item.get('prazo')}"
            for item in filtrados
        ]

        escolha = st.selectbox("Ação para acompanhar", opcoes)
        item = filtrados[opcoes.index(escolha)]

        col_a, col_b, col_c, col_d = st.columns(4)
        col_a.metric("Ticker", item.get("ticker"))
        col_b.metric("Criticidade", item.get("criticidade"))
        col_c.metric("Status", item.get("status"))
        col_d.metric("Dias", item.get("dias_ate_prazo"))

        st.info(item.get("acao_recomendada_radar"))

        observacao = st.text_area(
            "Observação da decisão do Radar",
            value=f"Decisão registrada no Radar Principal v{VERSAO_RADAR_PRINCIPAL_VALORIS}.",
            height=90,
        )

        if st.button("Salvar decisão do Radar"):
            salvar_decisao_radar(item, observacao=observacao)
            st.success("Decisão do Radar registrada.")
            st.rerun()
    else:
        st.info("Nenhuma ação encontrada com os filtros atuais.")

    decisoes = carregar_decisoes_radar()

    if decisoes:
        st.markdown("### Decisões registradas")
        st.dataframe(decisoes, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Relatórios")

    col_r1, col_r2 = st.columns(2)

    if col_r1.button("Salvar relatório do Radar Principal"):
        caminho = salvar_relatorio_radar_principal()
        st.success(f"Relatório salvo em {caminho}")

    if col_r2.button("Salvar manifesto do Radar Principal"):
        caminho = salvar_manifesto_radar_principal()
        st.success(f"Manifesto salvo em {caminho}")

    st.download_button(
        "Baixar relatório do Radar Principal (.md)",
        data=gerar_relatorio_radar_principal_markdown(),
        file_name="RELATORIO_RADAR_PRINCIPAL_VALORIS.md",
        mime="text/markdown",
    )


def executar_autoteste_radar_principal_valoris() -> Dict[str, Any]:
    metricas = calcular_metricas_radar_principal()

    return {
        "ok": True,
        "versao": VERSAO_RADAR_PRINCIPAL_VALORIS,
        "metricas": metricas,
    }
