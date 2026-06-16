# radar_revisoes_valoris.py
# Valoris — Radar de Revisões e Alertas v3.9.7
# ------------------------------------------------------------
# Objetivo:
# - Transformar pipeline e watchlist em rotina de acompanhamento.
# - Identificar ações vencidas, revisões próximas e ativos que exigem atenção.
# - Fechar o ciclo: análise → decisão → ação → revisão.
# ------------------------------------------------------------

from __future__ import annotations

import csv
import json
from collections import Counter, deque
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st


VERSAO_RADAR_REVISOES_VALORIS = "3.9.7"

CAMINHO_ACOES_PIPELINE = Path("acoes_pipeline_decisao_valoris.csv")
CAMINHO_ALERTAS = Path("alertas_radar_revisoes_valoris.csv")
CAMINHO_RELATORIO = Path("RELATORIO_RADAR_REVISOES_VALORIS.md")
CAMINHO_MANIFESTO = Path("manifesto_radar_revisoes_valoris.json")

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

CAMPOS_ALERTAS = [
    "data_hora",
    "ticker",
    "empresa",
    "tipo_alerta",
    "prioridade",
    "status",
    "prazo",
    "descricao",
    "acao_sugerida",
    "observacao",
]


def _agora_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat(sep=" ")


def _hoje() -> date:
    return datetime.now().date()


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


def _data(valor: Any) -> Optional[date]:
    texto = _txt(valor)

    if not texto:
        return None

    formatos = ["%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"]

    for formato in formatos:
        try:
            return datetime.strptime(texto[:19], formato).date()
        except Exception:
            pass

    return None


def _dias_ate(valor: Any) -> Optional[int]:
    data_valor = _data(valor)

    if data_valor is None:
        return None

    return (data_valor - _hoje()).days


def _garantir_csv(caminho: Path, campos: List[str]) -> None:
    if caminho.exists():
        return

    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()


def carregar_csv(caminho: Path, campos: List[str], max_registros: int = 1000) -> List[Dict[str, str]]:
    _garantir_csv(caminho, campos)

    try:
        with caminho.open("r", newline="", encoding="utf-8") as arquivo:
            leitor = csv.DictReader(arquivo)
            return list(deque(leitor, maxlen=max_registros))
    except Exception:
        return []


def carregar_acoes_pipeline(max_registros: int = 1000) -> List[Dict[str, str]]:
    return carregar_csv(CAMINHO_ACOES_PIPELINE, CAMPOS_ACOES_PIPELINE, max_registros=max_registros)


def carregar_watchlist() -> List[Dict[str, str]]:
    try:
        from watchlist_fundadores_valoris import carregar_watchlist_fundadores

        return carregar_watchlist_fundadores()
    except Exception:
        return []


def carregar_ranking_inteligente() -> List[Dict[str, Any]]:
    try:
        from analise_inteligente_valoris import gerar_ranking_inteligente

        return gerar_ranking_inteligente()
    except Exception:
        return []


def carregar_alertas_registrados(max_registros: int = 500) -> List[Dict[str, str]]:
    return carregar_csv(CAMINHO_ALERTAS, CAMPOS_ALERTAS, max_registros=max_registros)


def status_tem_pendencia(status: Any) -> bool:
    status_txt = _txt(status).lower()

    if not status_txt:
        return True

    encerrados = ["concluída", "concluida", "cancelada", "cancelado", "fechado", "finalizado"]

    return status_txt not in encerrados


def gerar_alertas_pipeline() -> List[Dict[str, Any]]:
    alertas: List[Dict[str, Any]] = []

    for acao in carregar_acoes_pipeline():
        if not status_tem_pendencia(acao.get("status")):
            continue

        prazo = acao.get("prazo", "")
        dias = _dias_ate(prazo)

        if dias is None:
            tipo = "Sem prazo"
            prioridade = acao.get("prioridade", "Média") or "Média"
            descricao = "Ação do pipeline sem prazo definido."
        elif dias < 0:
            tipo = "Ação vencida"
            prioridade = "Alta"
            descricao = f"Ação vencida há {abs(dias)} dia(s)."
        elif dias <= 3:
            tipo = "Ação próxima"
            prioridade = "Alta" if acao.get("prioridade") == "Alta" else "Média"
            descricao = f"Ação vence em {dias} dia(s)."
        elif dias <= 7:
            tipo = "Ação da semana"
            prioridade = acao.get("prioridade", "Média") or "Média"
            descricao = f"Ação vence em {dias} dia(s)."
        else:
            continue

        alertas.append(
            {
                "origem": "Pipeline",
                "ticker": _txt(acao.get("ticker")).upper(),
                "empresa": _txt(acao.get("empresa")),
                "tipo_alerta": tipo,
                "prioridade": prioridade,
                "status": _txt(acao.get("status")) or "Aberta",
                "prazo": prazo,
                "dias": dias,
                "descricao": descricao,
                "acao_sugerida": _txt(acao.get("acao")),
                "observacao": _txt(acao.get("observacao")),
            }
        )

    return alertas


def gerar_alertas_watchlist() -> List[Dict[str, Any]]:
    alertas: List[Dict[str, Any]] = []

    for item in carregar_watchlist():
        ticker = _txt(item.get("ticker")).upper()
        empresa = _txt(item.get("empresa")) or _txt(item.get("nome_empresa")) or ticker

        if not ticker:
            continue

        data_revisao = item.get("data_revisao", "")
        dias = _dias_ate(data_revisao)
        prioridade_original = _txt(item.get("prioridade")) or "Média"

        if dias is None:
            tipo = "Watchlist sem revisão"
            prioridade = "Média"
            descricao = "Ativo na Watchlist sem data de revisão definida."
        elif dias < 0:
            tipo = "Revisão vencida"
            prioridade = "Alta"
            descricao = f"Revisão vencida há {abs(dias)} dia(s)."
        elif dias <= 7:
            tipo = "Revisão próxima"
            prioridade = "Alta" if prioridade_original == "Alta" else "Média"
            descricao = f"Revisão programada para daqui {dias} dia(s)."
        elif dias <= 15:
            tipo = "Revisão em breve"
            prioridade = prioridade_original
            descricao = f"Revisão programada para daqui {dias} dia(s)."
        else:
            continue

        proximo_evento = _txt(item.get("proximo_evento")) or "Revisar tese, preço teto, risco e próximo resultado."

        alertas.append(
            {
                "origem": "Watchlist",
                "ticker": ticker,
                "empresa": empresa,
                "tipo_alerta": tipo,
                "prioridade": prioridade,
                "status": _txt(item.get("status_oportunidade")) or "Em acompanhamento",
                "prazo": data_revisao,
                "dias": dias,
                "descricao": descricao,
                "acao_sugerida": proximo_evento,
                "observacao": _txt(item.get("observacoes")) or _txt(item.get("observacao")),
            }
        )

    return alertas


def gerar_alertas_inteligencia() -> List[Dict[str, Any]]:
    alertas: List[Dict[str, Any]] = []

    for item in carregar_ranking_inteligente():
        ticker = _txt(item.get("ticker")).upper()
        empresa = _txt(item.get("empresa")) or ticker
        classificacao = _txt(item.get("classificacao"))
        watchlist = _txt(item.get("ja_na_watchlist"))
        score = _float(item.get("score_inteligente"))

        if not ticker:
            continue

        if classificacao == "Alta prioridade" and watchlist != "Sim":
            alertas.append(
                {
                    "origem": "Análise Inteligente",
                    "ticker": ticker,
                    "empresa": empresa,
                    "tipo_alerta": "Alta prioridade fora da Watchlist",
                    "prioridade": "Alta",
                    "status": "Pendente",
                    "prazo": str(_hoje() + timedelta(days=2)),
                    "dias": 2,
                    "descricao": f"{ticker} tem score inteligente {score}/100 e ainda não está na Watchlist.",
                    "acao_sugerida": "Enviar para Watchlist ou justificar por que não acompanhar.",
                    "observacao": _txt(item.get("proximo_passo")),
                }
            )

        if classificacao == "Premissas incompletas":
            alertas.append(
                {
                    "origem": "Análise Inteligente",
                    "ticker": ticker,
                    "empresa": empresa,
                    "tipo_alerta": "Premissas incompletas",
                    "prioridade": "Média",
                    "status": "Pendente",
                    "prazo": str(_hoje() + timedelta(days=7)),
                    "dias": 7,
                    "descricao": f"{ticker} precisa de revisão de dados antes de decisão.",
                    "acao_sugerida": "Voltar ao Motor Análise Ativos e revisar entradas.",
                    "observacao": _txt(item.get("proximo_passo")),
                }
            )

    return alertas


def gerar_radar_revisoes() -> List[Dict[str, Any]]:
    alertas = gerar_alertas_pipeline() + gerar_alertas_watchlist() + gerar_alertas_inteligencia()

    ordem_prioridade = {"Alta": 1, "Média": 2, "Baixa": 3, "": 4}

    alertas.sort(
        key=lambda item: (
            ordem_prioridade.get(_txt(item.get("prioridade")), 4),
            999 if item.get("dias") is None else item.get("dias"),
            item.get("ticker", ""),
        )
    )

    for indice, item in enumerate(alertas, start=1):
        item["ranking_alerta"] = indice

    return alertas


def calcular_metricas_radar() -> Dict[str, Any]:
    alertas = gerar_radar_revisoes()
    registrados = carregar_alertas_registrados()

    total = len(alertas)
    altas = len([item for item in alertas if item.get("prioridade") == "Alta"])
    vencidos = len([item for item in alertas if item.get("dias") is not None and item.get("dias") < 0])
    proximos = len([item for item in alertas if item.get("dias") is not None and 0 <= item.get("dias") <= 7])
    sem_prazo = len([item for item in alertas if item.get("dias") is None])
    origens = Counter(item.get("origem", "") for item in alertas)

    score_disciplina = 100
    score_disciplina -= min(vencidos * 18, 54)
    score_disciplina -= min(altas * 6, 24)
    score_disciplina -= min(sem_prazo * 5, 15)

    if total == 0:
        score_disciplina = 75

    score_disciplina += min(len(registrados) * 2, 8)
    score_disciplina = max(0, min(100, int(score_disciplina)))

    if vencidos > 0:
        risco = "Alto"
        decisao = "Há revisões ou ações vencidas"
        proximo = "Resolver primeiro os alertas vencidos de alta prioridade."
    elif altas > 0:
        risco = "Médio/Alto"
        decisao = "Há alertas de alta prioridade"
        proximo = "Executar ou justificar cada alerta de alta prioridade."
    elif total > 0:
        risco = "Médio"
        decisao = "Radar ativo com pendências controláveis"
        proximo = "Revisar próximos prazos e registrar decisões."
    else:
        risco = "Baixo"
        decisao = "Nenhum alerta relevante no momento"
        proximo = "Manter rotina semanal de revisão."

    return {
        "versao": VERSAO_RADAR_REVISOES_VALORIS,
        "gerado_em": _agora_iso(),
        "score_disciplina": score_disciplina,
        "alertas_total": total,
        "altas_prioridades": altas,
        "vencidos": vencidos,
        "proximos_7_dias": proximos,
        "sem_prazo": sem_prazo,
        "alertas_registrados": len(registrados),
        "origens": dict(origens),
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo,
    }


def salvar_alerta_registrado(alerta: Dict[str, Any], status: str, observacao: str = "") -> Path:
    _garantir_csv(CAMINHO_ALERTAS, CAMPOS_ALERTAS)

    with CAMINHO_ALERTAS.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_ALERTAS)
        escritor.writerow(
            {
                "data_hora": _agora_iso(),
                "ticker": _txt(alerta.get("ticker")).upper(),
                "empresa": _txt(alerta.get("empresa")),
                "tipo_alerta": _txt(alerta.get("tipo_alerta")),
                "prioridade": _txt(alerta.get("prioridade")),
                "status": _txt(status),
                "prazo": _txt(alerta.get("prazo")),
                "descricao": _txt(alerta.get("descricao")),
                "acao_sugerida": _txt(alerta.get("acao_sugerida")),
                "observacao": _txt(observacao),
            }
        )

    return CAMINHO_ALERTAS


def gerar_relatorio_radar_markdown(alertas: Optional[List[Dict[str, Any]]] = None) -> str:
    if alertas is None:
        alertas = gerar_radar_revisoes()

    metricas = calcular_metricas_radar()

    linhas = "\n".join(
        [
            f"- **#{item.get('ranking_alerta')} {item.get('ticker')}** — {item.get('tipo_alerta')} — prioridade {item.get('prioridade')} — prazo {item.get('prazo') or 'sem prazo'} — {item.get('acao_sugerida')}"
            for item in alertas[:30]
        ]
    ) or "- Nenhum alerta ativo."

    origens = "\n".join(
        [f"- {origem}: {quantidade}" for origem, quantidade in metricas["origens"].items()]
    ) or "- Nenhuma origem."

    return f"""# Radar de Revisões e Alertas — Valoris

Versão: {VERSAO_RADAR_REVISOES_VALORIS}  
Gerado em: {_agora_iso()}

## Diagnóstico

Score de disciplina: {metricas['score_disciplina']}/100  
Alertas ativos: {metricas['alertas_total']}  
Alta prioridade: {metricas['altas_prioridades']}  
Vencidos: {metricas['vencidos']}  
Próximos 7 dias: {metricas['proximos_7_dias']}  
Sem prazo: {metricas['sem_prazo']}  

Risco: {metricas['risco']}  
Decisão: {metricas['decisao']}  
Próximo passo: {metricas['proximo_passo']}

## Alertas por origem

{origens}

## Principais alertas

{linhas}

## Leitura estratégica

O Radar fecha o ciclo de acompanhamento da Valoris. Ele impede que análises boas fiquem esquecidas, que prazos vençam sem revisão e que ativos de alta prioridade fiquem fora da rotina.
"""


def salvar_relatorio_radar_markdown() -> Path:
    CAMINHO_RELATORIO.write_text(gerar_relatorio_radar_markdown(), encoding="utf-8")
    return CAMINHO_RELATORIO


def gerar_manifesto_radar() -> Dict[str, Any]:
    return {
        "produto": "Valoris",
        "versao": VERSAO_RADAR_REVISOES_VALORIS,
        "modulo": "radar_revisoes_valoris",
        "data_hora": _agora_iso(),
        "metricas": calcular_metricas_radar(),
        "principio": "transformar decisão em disciplina de revisão",
        "fluxo": "Pipeline → Watchlist → Radar → Revisão → Nova decisão",
    }


def salvar_manifesto_radar() -> Path:
    CAMINHO_MANIFESTO.write_text(
        json.dumps(gerar_manifesto_radar(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return CAMINHO_MANIFESTO


def renderizar_radar_revisoes_valoris() -> None:
    st.subheader("Radar de Revisões e Alertas")
    st.caption(
        "Acompanhamento operacional: ações vencidas, revisões próximas, ativos sem prazo e alertas da Análise Inteligente."
    )

    alertas = gerar_radar_revisoes()
    metricas = calcular_metricas_radar()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Score disciplina", f"{metricas['score_disciplina']}/100")
    col2.metric("Alertas", metricas["alertas_total"])
    col3.metric("Alta prioridade", metricas["altas_prioridades"])
    col4.metric("Vencidos", metricas["vencidos"])
    col5.metric("Próx. 7 dias", metricas["proximos_7_dias"])

    if metricas["vencidos"] > 0:
        st.error(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    elif metricas["altas_prioridades"] > 0:
        st.warning(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    elif metricas["alertas_total"] > 0:
        st.info(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    else:
        st.success(f"{metricas['decisao']} — {metricas['proximo_passo']}")

    st.divider()

    st.markdown("### Filtros")

    origens = ["Todas"] + sorted(list({item.get("origem", "") for item in alertas}))
    prioridades = ["Todas", "Alta", "Média", "Baixa"]
    tipos = ["Todos"] + sorted(list({item.get("tipo_alerta", "") for item in alertas}))

    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    filtro_origem = col_f1.selectbox("Origem", origens)
    filtro_prioridade = col_f2.selectbox("Prioridade", prioridades)
    filtro_tipo = col_f3.selectbox("Tipo", tipos)
    filtro_ticker = col_f4.text_input("Ticker", value="")

    filtrados: List[Dict[str, Any]] = []

    for item in alertas:
        if filtro_origem != "Todas" and item.get("origem") != filtro_origem:
            continue
        if filtro_prioridade != "Todas" and item.get("prioridade") != filtro_prioridade:
            continue
        if filtro_tipo != "Todos" and item.get("tipo_alerta") != filtro_tipo:
            continue
        if filtro_ticker.strip() and filtro_ticker.strip().upper() not in _txt(item.get("ticker")).upper():
            continue

        filtrados.append(item)

    tabela = [
        {
            "ranking": item.get("ranking_alerta"),
            "origem": item.get("origem"),
            "ticker": item.get("ticker"),
            "empresa": item.get("empresa"),
            "tipo": item.get("tipo_alerta"),
            "prioridade": item.get("prioridade"),
            "prazo": item.get("prazo"),
            "dias": item.get("dias"),
            "status": item.get("status"),
            "ação sugerida": item.get("acao_sugerida"),
        }
        for item in filtrados
    ]

    st.dataframe(tabela, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Registrar tratamento do alerta")

    if filtrados:
        opcoes = [
            f"#{item.get('ranking_alerta')} | {item.get('ticker')} | {item.get('tipo_alerta')} | {item.get('prioridade')}"
            for item in filtrados
        ]

        escolha = st.selectbox("Alerta", opcoes)
        alerta = filtrados[opcoes.index(escolha)]

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Ticker", alerta.get("ticker", ""))
        col2.metric("Origem", alerta.get("origem", ""))
        col3.metric("Prioridade", alerta.get("prioridade", ""))
        col4.metric("Prazo", alerta.get("prazo", "") or "Sem prazo")

        st.markdown(f"**Descrição:** {alerta.get('descricao', '')}")
        st.info(alerta.get("acao_sugerida", ""))

        status = st.selectbox("Status do tratamento", ["Tratado", "Adiado", "Em andamento", "Ignorado com justificativa"])
        observacao = st.text_area("Observação", value="", height=90)

        if st.button("Registrar tratamento"):
            salvar_alerta_registrado(alerta, status=status, observacao=observacao)
            st.success("Tratamento registrado.")
            st.rerun()
    else:
        st.info("Nenhum alerta encontrado com os filtros atuais.")

    st.divider()

    st.markdown("### Tratamentos registrados")
    registrados = carregar_alertas_registrados()

    if registrados:
        st.dataframe(registrados, use_container_width=True, hide_index=True)
    else:
        st.info("Ainda não há tratamentos registrados.")

    st.divider()

    st.markdown("### Relatórios")

    col1, col2 = st.columns(2)

    if col1.button("Salvar relatório do radar"):
        caminho = salvar_relatorio_radar_markdown()
        st.success(f"Relatório salvo em {caminho}")

    if col2.button("Salvar manifesto do radar"):
        caminho = salvar_manifesto_radar()
        st.success(f"Manifesto salvo em {caminho}")

    st.download_button(
        "Baixar relatório do radar (.md)",
        data=gerar_relatorio_radar_markdown(alertas),
        file_name="RELATORIO_RADAR_REVISOES_VALORIS.md",
        mime="text/markdown",
    )


def executar_autoteste_radar_revisoes_valoris() -> Dict[str, Any]:
    metricas = calcular_metricas_radar()

    return {
        "ok": True,
        "versao": VERSAO_RADAR_REVISOES_VALORIS,
        "metricas": {
            "score_disciplina": metricas["score_disciplina"],
            "alertas_total": metricas["alertas_total"],
            "vencidos": metricas["vencidos"],
        },
    }
