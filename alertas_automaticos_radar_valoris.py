# alertas_automaticos_radar_valoris.py
# Valoris — Alertas Automáticos do Radar v3.11.4
# ------------------------------------------------------------
# Objetivo:
# - Transformar o Radar Principal em um sistema de alertas acionáveis.
# - Gerar alertas automáticos de atraso, prazo próximo, alta criticidade e falta de prazo.
# - Registrar tratamento de alertas sem alterar a base operacional principal.
# - Preparar o produto para futuras notificações, e-mail, WhatsApp ou automações.

from __future__ import annotations

import csv
import json
from collections import Counter, deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st


VERSAO_ALERTAS_AUTOMATICOS_RADAR_VALORIS = "3.11.4"

CAMINHO_TRATAMENTOS = Path("tratamentos_alertas_automaticos_radar_valoris.csv")
CAMINHO_RELATORIO = Path("RELATORIO_ALERTAS_AUTOMATICOS_RADAR_VALORIS.md")
CAMINHO_MANIFESTO = Path("manifesto_alertas_automaticos_radar_valoris.json")

CAMPOS_TRATAMENTOS = [
    "data_hora",
    "id_alerta",
    "ticker",
    "empresa",
    "tipo_alerta",
    "severidade",
    "prioridade",
    "status_tratamento",
    "responsavel",
    "acao_tomada",
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
            valor = valor.replace(",", ".").strip()

            if valor == "":
                return padrao

        return int(float(valor))
    except Exception:
        return padrao


def _garantir_csv(caminho: Path, campos: List[str]) -> None:
    if caminho.exists():
        return

    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()


def carregar_radar_base() -> List[Dict[str, Any]]:
    try:
        from radar_principal_valoris import gerar_radar_principal

        return gerar_radar_principal()
    except Exception:
        return []


def calcular_id_alerta(item: Dict[str, Any]) -> str:
    partes = [
        _txt(item.get("ticker")).upper(),
        _txt(item.get("tipo_alerta")),
        _txt(item.get("prazo")),
        _txt(item.get("tipo_acao")),
    ]

    bruto = "|".join(partes)
    seguro = "".join(ch if ch.isalnum() else "_" for ch in bruto)
    seguro = "_".join([parte for parte in seguro.split("_") if parte])

    return seguro[:120] or "alerta_sem_id"


def severidade_por_item(item: Dict[str, Any]) -> str:
    tipo_alerta = _txt(item.get("tipo_alerta"))
    criticidade = _txt(item.get("criticidade"))
    dias = item.get("dias_ate_prazo")

    if tipo_alerta == "Atrasada":
        return "Crítica"

    if tipo_alerta == "Sem prazo":
        return "Alta"

    if criticidade == "Alta":
        return "Alta"

    if criticidade == "Média/Alta":
        return "Média/Alta"

    if isinstance(dias, int) and dias <= 7:
        return "Média/Alta"

    return "Média"


def acao_automatica(item: Dict[str, Any]) -> str:
    ticker = _txt(item.get("ticker")).upper()
    tipo_alerta = _txt(item.get("tipo_alerta"))
    tipo_acao = _txt(item.get("tipo_acao"))
    dias = item.get("dias_ate_prazo")

    if tipo_alerta == "Atrasada":
        return f"Resolver hoje a pendência de {ticker}: {tipo_acao}."

    if tipo_alerta == "Sem prazo":
        return f"Definir prazo e responsável para {ticker} antes de criar novas ações."

    if tipo_alerta == "Prioridade alta próxima":
        return f"Executar ou revisar {ticker} em até {dias} dias."

    if tipo_alerta == "Próxima revisão":
        return f"Preparar revisão de {ticker} antes do prazo."

    if tipo_alerta == "Acompanhar no mês":
        return f"Incluir {ticker} no ciclo semanal/mensal de acompanhamento."

    return f"Manter {ticker} monitorado sem ação imediata."


def gerar_alertas_automaticos() -> List[Dict[str, Any]]:
    radar = carregar_radar_base()
    alertas = []

    tipos_relevantes = {
        "Atrasada",
        "Sem prazo",
        "Prioridade alta próxima",
        "Próxima revisão",
        "Acompanhar no mês",
    }

    for item in radar:
        tipo_alerta = _txt(item.get("tipo_alerta"))

        if tipo_alerta not in tipos_relevantes:
            continue

        alerta = {
            "id_alerta": calcular_id_alerta(item),
            "data_hora": _agora_iso(),
            "ticker": _txt(item.get("ticker")).upper(),
            "empresa": _txt(item.get("empresa")),
            "tipo_alerta": tipo_alerta,
            "severidade": severidade_por_item(item),
            "prioridade": _txt(item.get("prioridade")) or "Média",
            "status_pipeline": _txt(item.get("status")),
            "prazo": _txt(item.get("prazo")),
            "dias_ate_prazo": item.get("dias_ate_prazo"),
            "tipo_acao": _txt(item.get("tipo_acao")),
            "acao_recomendada": acao_automatica(item),
            "origem": "Radar Principal",
        }
        alertas.append(alerta)

    ordem = {
        "Crítica": 1,
        "Alta": 2,
        "Média/Alta": 3,
        "Média": 4,
        "Baixa": 5,
    }

    alertas.sort(
        key=lambda item: (
            ordem.get(item.get("severidade"), 9),
            9999 if item.get("dias_ate_prazo") in {"", None} else _int(item.get("dias_ate_prazo"), 9999),
            item.get("ticker", ""),
        )
    )

    return alertas


def salvar_tratamento_alerta(alerta: Dict[str, Any], status_tratamento: str, responsavel: str, acao_tomada: str, observacao: str = "") -> Path:
    _garantir_csv(CAMINHO_TRATAMENTOS, CAMPOS_TRATAMENTOS)

    with CAMINHO_TRATAMENTOS.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_TRATAMENTOS)
        escritor.writerow(
            {
                "data_hora": _agora_iso(),
                "id_alerta": _txt(alerta.get("id_alerta")),
                "ticker": _txt(alerta.get("ticker")).upper(),
                "empresa": _txt(alerta.get("empresa")),
                "tipo_alerta": _txt(alerta.get("tipo_alerta")),
                "severidade": _txt(alerta.get("severidade")),
                "prioridade": _txt(alerta.get("prioridade")),
                "status_tratamento": _txt(status_tratamento),
                "responsavel": _txt(responsavel),
                "acao_tomada": _txt(acao_tomada),
                "observacao": _txt(observacao),
            }
        )

    return CAMINHO_TRATAMENTOS


def carregar_tratamentos_alertas(max_registros: int = 500) -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_TRATAMENTOS, CAMPOS_TRATAMENTOS)

    try:
        with CAMINHO_TRATAMENTOS.open("r", newline="", encoding="utf-8") as arquivo:
            leitor = csv.DictReader(arquivo)
            return list(deque(leitor, maxlen=max_registros))
    except Exception:
        return []


def ids_tratados() -> set[str]:
    tratamentos = carregar_tratamentos_alertas()
    return {
        _txt(item.get("id_alerta"))
        for item in tratamentos
        if _txt(item.get("status_tratamento")).lower() in {"tratado", "resolvido", "ignorado", "em acompanhamento"}
    }


def calcular_metricas_alertas_automaticos() -> Dict[str, Any]:
    alertas = gerar_alertas_automaticos()
    tratados = ids_tratados()

    pendentes = [
        item for item in alertas
        if _txt(item.get("id_alerta")) not in tratados
    ]

    contador_severidade = Counter(item.get("severidade", "Sem severidade") for item in alertas)
    criticos = contador_severidade.get("Crítica", 0)
    alta = contador_severidade.get("Alta", 0)
    media_alta = contador_severidade.get("Média/Alta", 0)

    score = 70

    if alertas:
        score += 10

    if not pendentes:
        score += 10

    if criticos:
        score -= min(criticos * 20, 45)

    if alta:
        score -= min(alta * 12, 30)

    if media_alta:
        score -= min(media_alta * 6, 18)

    score = max(0, min(100, int(score)))

    if not alertas:
        risco = "Baixo"
        decisao = "Nenhum alerta automático relevante no momento"
        proximo = "Manter rotina de acompanhamento pelo Cockpit e Radar."
    elif criticos:
        risco = "Alto"
        decisao = "Existem alertas críticos automáticos"
        proximo = "Resolver alertas críticos antes de criar novas ações."
    elif alta or media_alta:
        risco = "Médio"
        decisao = "Existem alertas relevantes para acompanhamento"
        proximo = "Registrar tratamento dos alertas de maior severidade."
    else:
        risco = "Baixo/Médio"
        decisao = "Alertas automáticos funcionais e sob controle"
        proximo = "Usar alertas como rotina semanal de acompanhamento."

    return {
        "versao": VERSAO_ALERTAS_AUTOMATICOS_RADAR_VALORIS,
        "gerado_em": _agora_iso(),
        "score_alertas": score,
        "alertas_total": len(alertas),
        "alertas_pendentes": len(pendentes),
        "alertas_tratados": len(alertas) - len(pendentes),
        "criticos": criticos,
        "alta": alta,
        "media_alta": media_alta,
        "severidades": dict(contador_severidade),
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo,
    }


def gerar_relatorio_alertas_markdown() -> str:
    metricas = calcular_metricas_alertas_automaticos()
    alertas = gerar_alertas_automaticos()

    linhas = "\n".join(
        [
            f"- **{item['ticker']} — {item['empresa']}**: {item['tipo_alerta']} | severidade {item['severidade']} | ação: {item['acao_recomendada']}"
            for item in alertas[:30]
        ]
    ) or "- Nenhum alerta automático relevante."

    return f"""# Alertas Automáticos do Radar — Valoris

Versão: {VERSAO_ALERTAS_AUTOMATICOS_RADAR_VALORIS}  
Gerado em: {_agora_iso()}

## Diagnóstico

Score alertas: {metricas['score_alertas']}/100  
Alertas totais: {metricas['alertas_total']}  
Pendentes: {metricas['alertas_pendentes']}  
Tratados: {metricas['alertas_tratados']}  
Críticos: {metricas['criticos']}  
Alta severidade: {metricas['alta']}  
Média/Alta: {metricas['media_alta']}  

Risco: {metricas['risco']}  
Decisão: {metricas['decisao']}  
Próximo passo: {metricas['proximo_passo']}

## Alertas

{linhas}

## Estratégia

Esta versão transforma o Radar Principal em um sistema de acompanhamento acionável. O próximo passo natural será conectar esses alertas a notificações, rotina semanal e automações.
"""


def salvar_relatorio_alertas() -> Path:
    CAMINHO_RELATORIO.write_text(gerar_relatorio_alertas_markdown(), encoding="utf-8")
    return CAMINHO_RELATORIO


def gerar_manifesto_alertas() -> Dict[str, Any]:
    return {
        "produto": "Valoris",
        "versao": VERSAO_ALERTAS_AUTOMATICOS_RADAR_VALORIS,
        "modulo": "alertas_automaticos_radar_valoris",
        "data_hora": _agora_iso(),
        "metricas": calcular_metricas_alertas_automaticos(),
        "alertas": gerar_alertas_automaticos(),
        "principio": "alerta bom não é barulho; é decisão acionável no momento certo",
        "proxima_etapa": "Central de rotina semanal e notificações automáticas",
    }


def salvar_manifesto_alertas() -> Path:
    CAMINHO_MANIFESTO.write_text(
        json.dumps(gerar_manifesto_alertas(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return CAMINHO_MANIFESTO


def renderizar_alertas_automaticos_radar_valoris() -> None:
    st.subheader("Alertas Automáticos do Radar")
    st.caption("Acompanhamento acionável: atraso, prazo próximo, severidade, tratamento e próxima ação.")

    metricas = calcular_metricas_alertas_automaticos()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Score alertas", f"{metricas['score_alertas']}/100")
    col2.metric("Alertas", metricas["alertas_total"])
    col3.metric("Pendentes", metricas["alertas_pendentes"])
    col4.metric("Críticos", metricas["criticos"])
    col5.metric("Alta", metricas["alta"])

    if metricas["risco"] == "Alto":
        st.error(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    elif metricas["risco"] == "Médio":
        st.warning(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    elif metricas["risco"] == "Baixo":
        st.success(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    else:
        st.info(f"{metricas['decisao']} — {metricas['proximo_passo']}")

    st.divider()

    alertas = gerar_alertas_automaticos()
    tratados = ids_tratados()

    st.markdown("### Alertas gerados")

    col_f1, col_f2, col_f3 = st.columns(3)
    filtro_ticker = col_f1.text_input("Ticker", value="")
    severidades = ["Todas"] + sorted({item.get("severidade", "") for item in alertas if item.get("severidade")})
    tipos = ["Todos"] + sorted({item.get("tipo_alerta", "") for item in alertas if item.get("tipo_alerta")})
    filtro_severidade = col_f2.selectbox("Severidade", severidades)
    filtro_tipo = col_f3.selectbox("Tipo", tipos)

    filtrados = []

    for item in alertas:
        if filtro_ticker.strip() and filtro_ticker.strip().upper() not in item.get("ticker", ""):
            continue

        if filtro_severidade != "Todas" and item.get("severidade") != filtro_severidade:
            continue

        if filtro_tipo != "Todos" and item.get("tipo_alerta") != filtro_tipo:
            continue

        filtrados.append(item)

    tabela = [
        {
            "tratado": "Sim" if item.get("id_alerta") in tratados else "Não",
            "ticker": item.get("ticker"),
            "empresa": item.get("empresa"),
            "tipo": item.get("tipo_alerta"),
            "severidade": item.get("severidade"),
            "prioridade": item.get("prioridade"),
            "prazo": item.get("prazo"),
            "dias": item.get("dias_ate_prazo"),
            "ação recomendada": item.get("acao_recomendada"),
        }
        for item in filtrados
    ]

    st.dataframe(tabela, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Registrar tratamento")

    if filtrados:
        opcoes = [
            f"{item['ticker']} | {item['tipo_alerta']} | {item['severidade']} | prazo {item['prazo']}"
            for item in filtrados
        ]

        escolha = st.selectbox("Alerta", opcoes)
        alerta = filtrados[opcoes.index(escolha)]

        st.info(alerta.get("acao_recomendada"))

        col_a, col_b = st.columns(2)
        status_tratamento = col_a.selectbox("Status do tratamento", ["Em acompanhamento", "Tratado", "Resolvido", "Ignorado"])
        responsavel = col_b.text_input("Responsável", value="Fundador")

        acao_tomada = st.text_input("Ação tomada", value=alerta.get("acao_recomendada", ""))
        observacao = st.text_area("Observação", value=f"Tratamento registrado nos Alertas Automáticos v{VERSAO_ALERTAS_AUTOMATICOS_RADAR_VALORIS}.", height=90)

        if st.button("Salvar tratamento do alerta"):
            salvar_tratamento_alerta(
                alerta,
                status_tratamento=status_tratamento,
                responsavel=responsavel,
                acao_tomada=acao_tomada,
                observacao=observacao,
            )
            st.success("Tratamento do alerta registrado.")
            st.rerun()
    else:
        st.info("Nenhum alerta encontrado com os filtros atuais.")

    tratamentos = carregar_tratamentos_alertas()

    if tratamentos:
        st.markdown("### Tratamentos registrados")
        st.dataframe(tratamentos, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Relatórios")

    col_r1, col_r2 = st.columns(2)

    if col_r1.button("Salvar relatório de alertas"):
        caminho = salvar_relatorio_alertas()
        st.success(f"Relatório salvo em {caminho}")

    if col_r2.button("Salvar manifesto de alertas"):
        caminho = salvar_manifesto_alertas()
        st.success(f"Manifesto salvo em {caminho}")

    st.download_button(
        "Baixar relatório de alertas (.md)",
        data=gerar_relatorio_alertas_markdown(),
        file_name="RELATORIO_ALERTAS_AUTOMATICOS_RADAR_VALORIS.md",
        mime="text/markdown",
    )


def executar_autoteste_alertas_automaticos_radar_valoris() -> Dict[str, Any]:
    metricas = calcular_metricas_alertas_automaticos()

    return {
        "ok": True,
        "versao": VERSAO_ALERTAS_AUTOMATICOS_RADAR_VALORIS,
        "metricas": metricas,
    }
