# agenda_revisoes_valoris.py
# Valoris — Agenda e Próximas Revisões v3.11.6
# ------------------------------------------------------------
# Objetivo:
# - Transformar a Rotina Semanal, o Radar e o Pipeline em uma agenda operacional.
# - Mostrar próximos 7, 15 e 30 dias.
# - Agrupar ações por prazo, ativo, prioridade e origem.
# - Registrar decisões de agenda sem alterar dados operacionais principais.
# - Preparar futura integração com calendário, notificações e automações.

from __future__ import annotations

import csv
import json
from collections import Counter, deque
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st


VERSAO_AGENDA_REVISOES_VALORIS = "3.11.6"

CAMINHO_DECISOES = Path("decisoes_agenda_revisoes_valoris.csv")
CAMINHO_RELATORIO = Path("RELATORIO_AGENDA_REVISOES_VALORIS.md")
CAMINHO_MANIFESTO = Path("manifesto_agenda_revisoes_valoris.json")

CAMPOS_DECISOES = [
    "data_hora",
    "ticker",
    "empresa",
    "data_evento",
    "janela",
    "prioridade",
    "origem",
    "acao",
    "status_agenda",
    "responsavel",
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


def _dias_ate(data_evento: Optional[date]) -> Optional[int]:
    if data_evento is None:
        return None
    return (data_evento - date.today()).days


def _janela_por_dias(dias: Optional[int]) -> str:
    if dias is None:
        return "Sem prazo"

    if dias < 0:
        return "Atrasado"

    if dias <= 7:
        return "Próximos 7 dias"

    if dias <= 15:
        return "Próximos 15 dias"

    if dias <= 30:
        return "Próximos 30 dias"

    return "Depois de 30 dias"


def _prioridade_rank(valor: Any) -> int:
    return {
        "Crítica": 1,
        "Alta": 2,
        "Média/Alta": 3,
        "Média": 4,
        "Baixa": 5,
    }.get(_txt(valor), 9)


def _garantir_csv(caminho: Path, campos: List[str]) -> None:
    if caminho.exists():
        return

    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()


def carregar_rotina() -> List[Dict[str, Any]]:
    try:
        from rotina_semanal_inteligente_valoris import gerar_rotina_semanal

        return gerar_rotina_semanal()
    except Exception:
        return []


def carregar_radar() -> List[Dict[str, Any]]:
    try:
        from radar_principal_valoris import gerar_radar_principal

        return gerar_radar_principal()
    except Exception:
        return []


def carregar_pipeline() -> List[Dict[str, Any]]:
    try:
        from pipeline_backend_flexivel_valoris import carregar_pipeline

        return carregar_pipeline(backend="csv", max_registros=3000)
    except Exception:
        return []


def carregar_alertas() -> List[Dict[str, Any]]:
    try:
        from alertas_automaticos_radar_valoris import gerar_alertas_automaticos

        return gerar_alertas_automaticos()
    except Exception:
        return []


def carregar_execucoes_rotina() -> List[Dict[str, Any]]:
    try:
        from rotina_semanal_inteligente_valoris import carregar_execucoes

        return carregar_execucoes(max_registros=1000)
    except Exception:
        return []


def gerar_item_agenda(
    ticker: str,
    empresa: str,
    data_evento: Any,
    prioridade: str,
    origem: str,
    acao: str,
    contexto: str = "",
) -> Dict[str, Any]:
    data_obj = _data(data_evento)
    dias = _dias_ate(data_obj)

    return {
        "id": _id_agenda(ticker, origem, acao, data_obj.isoformat() if data_obj else ""),
        "ticker": _txt(ticker).upper(),
        "empresa": _txt(empresa),
        "data_evento": data_obj.isoformat() if data_obj else "",
        "dias": "" if dias is None else dias,
        "janela": _janela_por_dias(dias),
        "prioridade": _txt(prioridade) or "Média",
        "origem": _txt(origem),
        "acao": _txt(acao),
        "contexto": _txt(contexto),
    }


def _id_agenda(ticker: str, origem: str, acao: str, data_evento: str) -> str:
    bruto = f"{ticker}|{origem}|{acao}|{data_evento}"
    seguro = "".join(ch if ch.isalnum() else "_" for ch in bruto)
    return "_".join([p for p in seguro.split("_") if p])[:140] or "agenda_sem_id"


def gerar_agenda_revisoes() -> List[Dict[str, Any]]:
    itens: List[Dict[str, Any]] = []

    for item in carregar_pipeline():
        ticker = _txt(item.get("ticker")).upper()
        status = _txt(item.get("status")).lower()

        if not ticker or status in {"concluída", "concluida", "cancelada", "arquivada", "fechada"}:
            continue

        itens.append(
            gerar_item_agenda(
                ticker=ticker,
                empresa=_txt(item.get("empresa")) or ticker,
                data_evento=item.get("prazo"),
                prioridade=_txt(item.get("prioridade")) or "Média",
                origem="Pipeline Principal",
                acao=_txt(item.get("tipo_acao")) or "Acompanhar ação aberta",
                contexto=_txt(item.get("observacao")),
            )
        )

    for item in carregar_radar():
        ticker = _txt(item.get("ticker")).upper()

        if not ticker:
            continue

        tipo_alerta = _txt(item.get("tipo_alerta"))

        if tipo_alerta in {"Monitoramento", "Concluída/fechada"}:
            continue

        itens.append(
            gerar_item_agenda(
                ticker=ticker,
                empresa=_txt(item.get("empresa")) or ticker,
                data_evento=item.get("prazo"),
                prioridade=_txt(item.get("criticidade")) or _txt(item.get("prioridade")) or "Média",
                origem="Radar Principal",
                acao=_txt(item.get("acao_recomendada_radar")),
                contexto=tipo_alerta,
            )
        )

    for item in carregar_alertas():
        ticker = _txt(item.get("ticker")).upper()

        if not ticker:
            continue

        itens.append(
            gerar_item_agenda(
                ticker=ticker,
                empresa=_txt(item.get("empresa")) or ticker,
                data_evento=item.get("prazo"),
                prioridade=_txt(item.get("severidade")) or _txt(item.get("prioridade")) or "Média",
                origem="Alertas Radar",
                acao=_txt(item.get("acao_recomendada")),
                contexto=_txt(item.get("tipo_alerta")),
            )
        )

    for item in carregar_rotina():
        ticker = _txt(item.get("ticker")).upper()

        if not ticker:
            continue

        itens.append(
            gerar_item_agenda(
                ticker=ticker,
                empresa=_txt(item.get("empresa")) or ticker,
                data_evento=item.get("prazo"),
                prioridade=_txt(item.get("prioridade")) or "Média",
                origem="Rotina Semanal",
                acao=_txt(item.get("acao")),
                contexto=_txt(item.get("bloco")),
            )
        )

    unicos: Dict[str, Dict[str, Any]] = {}

    for item in itens:
        chave = item["id"]

        if chave not in unicos:
            unicos[chave] = item
            continue

        if _prioridade_rank(item.get("prioridade")) < _prioridade_rank(unicos[chave].get("prioridade")):
            unicos[chave] = item

    agenda = list(unicos.values())

    ordem_janela = {
        "Atrasado": 1,
        "Próximos 7 dias": 2,
        "Próximos 15 dias": 3,
        "Próximos 30 dias": 4,
        "Depois de 30 dias": 5,
        "Sem prazo": 6,
    }

    agenda.sort(
        key=lambda item: (
            ordem_janela.get(item.get("janela"), 9),
            _prioridade_rank(item.get("prioridade")),
            9999 if item.get("dias") in {"", None} else _int(item.get("dias"), 9999),
            item.get("ticker", ""),
            item.get("origem", ""),
        )
    )

    return agenda


def carregar_decisoes_agenda(max_registros: int = 500) -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_DECISOES, CAMPOS_DECISOES)

    try:
        with CAMINHO_DECISOES.open("r", newline="", encoding="utf-8") as arquivo:
            leitor = csv.DictReader(arquivo)
            return list(deque(leitor, maxlen=max_registros))
    except Exception:
        return []


def ids_tratados_agenda() -> set[str]:
    ids = set()

    for decisao in carregar_decisoes_agenda():
        status = _txt(decisao.get("status_agenda")).lower()

        if status in {"feito", "resolvido", "adiado conscientemente", "em acompanhamento", "cancelado"}:
            ids.add(
                _id_agenda(
                    decisao.get("ticker", ""),
                    decisao.get("origem", ""),
                    decisao.get("acao", ""),
                    decisao.get("data_evento", ""),
                )
            )

    return ids


def salvar_decisao_agenda(item: Dict[str, Any], status_agenda: str, responsavel: str, observacao: str = "") -> Path:
    _garantir_csv(CAMINHO_DECISOES, CAMPOS_DECISOES)

    with CAMINHO_DECISOES.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISOES)
        escritor.writerow(
            {
                "data_hora": _agora_iso(),
                "ticker": _txt(item.get("ticker")).upper(),
                "empresa": _txt(item.get("empresa")),
                "data_evento": _txt(item.get("data_evento")),
                "janela": _txt(item.get("janela")),
                "prioridade": _txt(item.get("prioridade")),
                "origem": _txt(item.get("origem")),
                "acao": _txt(item.get("acao")),
                "status_agenda": _txt(status_agenda),
                "responsavel": _txt(responsavel),
                "observacao": _txt(observacao),
            }
        )

    return CAMINHO_DECISOES


def calcular_metricas_agenda_revisoes() -> Dict[str, Any]:
    agenda = gerar_agenda_revisoes()
    tratados = ids_tratados_agenda()

    pendentes = [item for item in agenda if item["id"] not in tratados]
    por_janela = Counter(item.get("janela", "Sem janela") for item in agenda)
    por_prioridade = Counter(item.get("prioridade", "Sem prioridade") for item in agenda)

    atrasados = por_janela.get("Atrasado", 0)
    sete_dias = por_janela.get("Próximos 7 dias", 0)
    quinze_dias = por_janela.get("Próximos 15 dias", 0)
    trinta_dias = por_janela.get("Próximos 30 dias", 0)
    sem_prazo = por_janela.get("Sem prazo", 0)

    score = 55

    if agenda:
        score += 15

    if not pendentes and agenda:
        score += 15
    elif len(pendentes) <= 5:
        score += 7

    if atrasados:
        score -= min(atrasados * 18, 45)

    if sem_prazo:
        score -= min(sem_prazo * 8, 24)

    if sete_dias or quinze_dias or trinta_dias:
        score += 8

    score = max(0, min(100, int(score)))

    if not agenda:
        risco = "Baixo"
        decisao = "Agenda sem revisões pendentes"
        proximo = "Manter acompanhamento pelo Cockpit e Rotina Semanal."
    elif atrasados:
        risco = "Alto"
        decisao = "Há revisões ou ações atrasadas"
        proximo = "Resolver itens atrasados antes de planejar novas ações."
    elif sem_prazo:
        risco = "Médio"
        decisao = "Há itens sem prazo definido"
        proximo = "Definir prazo para itens sem data antes de fechar a semana."
    elif pendentes:
        risco = "Baixo/Médio"
        decisao = "Agenda funcional com revisões pendentes"
        proximo = "Executar ou registrar decisões dos próximos 7 e 15 dias."
    else:
        risco = "Baixo"
        decisao = "Agenda da semana sob controle"
        proximo = "Preparar próxima janela de acompanhamento."

    return {
        "versao": VERSAO_AGENDA_REVISOES_VALORIS,
        "gerado_em": _agora_iso(),
        "score_agenda": score,
        "itens": len(agenda),
        "pendentes": len(pendentes),
        "tratados": len(agenda) - len(pendentes),
        "atrasados": atrasados,
        "proximos_7_dias": sete_dias,
        "proximos_15_dias": quinze_dias,
        "proximos_30_dias": trinta_dias,
        "sem_prazo": sem_prazo,
        "por_janela": dict(por_janela),
        "por_prioridade": dict(por_prioridade),
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo,
    }


def gerar_relatorio_agenda_markdown() -> str:
    metricas = calcular_metricas_agenda_revisoes()
    agenda = gerar_agenda_revisoes()

    linhas = "\n".join(
        [
            f"- **{item['janela']} — {item['ticker']} — {item['empresa']}**: {item['acao']} | prioridade {item['prioridade']} | data {item['data_evento'] or 'sem prazo'} | origem {item['origem']}."
            for item in agenda[:50]
        ]
    ) or "- Nenhum item de agenda."

    return f"""# Agenda e Próximas Revisões — Valoris

Versão: {VERSAO_AGENDA_REVISOES_VALORIS}  
Gerado em: {_agora_iso()}

## Diagnóstico

Score agenda: {metricas['score_agenda']}/100  
Itens: {metricas['itens']}  
Pendentes: {metricas['pendentes']}  
Tratados: {metricas['tratados']}  
Atrasados: {metricas['atrasados']}  
Próximos 7 dias: {metricas['proximos_7_dias']}  
Próximos 15 dias: {metricas['proximos_15_dias']}  
Próximos 30 dias: {metricas['proximos_30_dias']}  
Sem prazo: {metricas['sem_prazo']}  

Risco: {metricas['risco']}  
Decisão: {metricas['decisao']}  
Próximo passo: {metricas['proximo_passo']}

## Agenda

{linhas}

## Estratégia

Esta versão transforma a rotina operacional em agenda. O usuário passa a enxergar o tempo: o que vence, o que está atrasado, o que precisa de revisão e o que deve virar decisão.
"""


def salvar_relatorio_agenda() -> Path:
    CAMINHO_RELATORIO.write_text(gerar_relatorio_agenda_markdown(), encoding="utf-8")
    return CAMINHO_RELATORIO


def gerar_manifesto_agenda() -> Dict[str, Any]:
    return {
        "produto": "Valoris",
        "versao": VERSAO_AGENDA_REVISOES_VALORIS,
        "modulo": "agenda_revisoes_valoris",
        "data_hora": _agora_iso(),
        "metricas": calcular_metricas_agenda_revisoes(),
        "agenda": gerar_agenda_revisoes(),
        "principio": "o tempo transforma análise em disciplina; agenda evita que boas decisões sejam esquecidas",
        "proxima_etapa": "notificações conectadas à agenda operacional",
    }


def salvar_manifesto_agenda() -> Path:
    CAMINHO_MANIFESTO.write_text(
        json.dumps(gerar_manifesto_agenda(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return CAMINHO_MANIFESTO


def renderizar_agenda_revisoes_valoris() -> None:
    st.subheader("Agenda e Próximas Revisões")
    st.caption("Calendário operacional: próximos 7, 15 e 30 dias, atrasos, prazos e decisões por ativo.")

    metricas = calcular_metricas_agenda_revisoes()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Score agenda", f"{metricas['score_agenda']}/100")
    col2.metric("Itens", metricas["itens"])
    col3.metric("Pendentes", metricas["pendentes"])
    col4.metric("7 dias", metricas["proximos_7_dias"])
    col5.metric("Atrasados", metricas["atrasados"])

    if metricas["risco"] == "Alto":
        st.error(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    elif metricas["risco"] == "Médio":
        st.warning(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    elif metricas["risco"] == "Baixo":
        st.success(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    else:
        st.info(f"{metricas['decisao']} — {metricas['proximo_passo']}")

    st.divider()

    agenda = gerar_agenda_revisoes()
    tratados = ids_tratados_agenda()

    st.markdown("### Agenda operacional")

    col_f1, col_f2, col_f3 = st.columns(3)
    janelas = ["Todas"] + sorted({item.get("janela", "") for item in agenda if item.get("janela")})
    prioridades = ["Todas"] + sorted({item.get("prioridade", "") for item in agenda if item.get("prioridade")})
    filtro_janela = col_f1.selectbox("Janela", janelas)
    filtro_prioridade = col_f2.selectbox("Prioridade", prioridades)
    filtro_ticker = col_f3.text_input("Ticker", value="")

    filtrados = []

    for item in agenda:
        if filtro_janela != "Todas" and item.get("janela") != filtro_janela:
            continue

        if filtro_prioridade != "Todas" and item.get("prioridade") != filtro_prioridade:
            continue

        if filtro_ticker.strip() and filtro_ticker.strip().upper() not in item.get("ticker", ""):
            continue

        filtrados.append(item)

    tabela = [
        {
            "tratado": "Sim" if item.get("id") in tratados else "Não",
            "janela": item.get("janela"),
            "ticker": item.get("ticker"),
            "empresa": item.get("empresa"),
            "data": item.get("data_evento"),
            "dias": item.get("dias"),
            "prioridade": item.get("prioridade"),
            "origem": item.get("origem"),
            "ação": item.get("acao"),
        }
        for item in filtrados
    ]

    st.dataframe(tabela, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Registrar decisão de agenda")

    if filtrados:
        opcoes = [
            f"{item['janela']} | {item['ticker']} | {item['prioridade']} | {item['acao'][:70]}"
            for item in filtrados
        ]

        escolha = st.selectbox("Item da agenda", opcoes)
        item = filtrados[opcoes.index(escolha)]

        st.info(item.get("acao"))

        col_a, col_b = st.columns(2)
        status_agenda = col_a.selectbox("Status da agenda", ["Em acompanhamento", "Feito", "Resolvido", "Adiado conscientemente", "Cancelado"])
        responsavel = col_b.text_input("Responsável", value="Fundador")

        observacao = st.text_area(
            "Observação",
            value=f"Decisão registrada na Agenda de Revisões v{VERSAO_AGENDA_REVISOES_VALORIS}.",
            height=90,
        )

        if st.button("Salvar decisão da agenda"):
            salvar_decisao_agenda(item, status_agenda=status_agenda, responsavel=responsavel, observacao=observacao)
            st.success("Decisão da agenda registrada.")
            st.rerun()
    else:
        st.info("Nenhum item encontrado com os filtros atuais.")

    decisoes = carregar_decisoes_agenda()

    if decisoes:
        st.markdown("### Decisões registradas")
        st.dataframe(decisoes, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Relatórios")

    col_r1, col_r2 = st.columns(2)

    if col_r1.button("Salvar relatório da agenda"):
        caminho = salvar_relatorio_agenda()
        st.success(f"Relatório salvo em {caminho}")

    if col_r2.button("Salvar manifesto da agenda"):
        caminho = salvar_manifesto_agenda()
        st.success(f"Manifesto salvo em {caminho}")

    st.download_button(
        "Baixar relatório da agenda (.md)",
        data=gerar_relatorio_agenda_markdown(),
        file_name="RELATORIO_AGENDA_REVISOES_VALORIS.md",
        mime="text/markdown",
    )


def executar_autoteste_agenda_revisoes_valoris() -> Dict[str, Any]:
    metricas = calcular_metricas_agenda_revisoes()

    return {
        "ok": True,
        "versao": VERSAO_AGENDA_REVISOES_VALORIS,
        "metricas": metricas,
    }
