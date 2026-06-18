# rotina_semanal_inteligente_valoris.py
# Valoris — Rotina Semanal Inteligente v3.11.5

from __future__ import annotations

import csv
import json
from collections import Counter, deque
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st


VERSAO_ROTINA_SEMANAL_INTELIGENTE_VALORIS = "3.11.5"

CAMINHO_EXECUCOES = Path("execucoes_rotina_semanal_valoris.csv")
CAMINHO_RELATORIO = Path("RELATORIO_ROTINA_SEMANAL_INTELIGENTE_VALORIS.md")
CAMINHO_MANIFESTO = Path("manifesto_rotina_semanal_inteligente_valoris.json")

CAMPOS_EXECUCOES = [
    "data_hora",
    "semana_inicio",
    "semana_fim",
    "ticker",
    "empresa",
    "bloco",
    "prioridade",
    "acao",
    "status_execucao",
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


def _data(valor: Any) -> date | None:
    texto = _txt(valor)
    if not texto:
        return None

    for formato in ["%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d %H:%M:%S"]:
        try:
            return datetime.strptime(texto, formato).date()
        except Exception:
            pass

    try:
        return datetime.fromisoformat(texto).date()
    except Exception:
        return None


def _garantir_csv(caminho: Path, campos: List[str]) -> None:
    if caminho.exists():
        return
    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()


def intervalo_semana() -> Dict[str, str]:
    hoje = date.today()
    inicio = hoje - timedelta(days=hoje.weekday())
    fim = inicio + timedelta(days=6)
    return {"inicio": inicio.isoformat(), "fim": fim.isoformat()}


def prioridade_rank(valor: Any) -> int:
    return {
        "Crítica": 1,
        "Alta": 2,
        "Média/Alta": 3,
        "Média": 4,
        "Baixa": 5,
    }.get(_txt(valor), 9)


def chave_item(ticker: str, acao: str, bloco: str) -> str:
    bruto = f"{ticker}|{acao}|{bloco}"
    return "".join(ch if ch.isalnum() else "_" for ch in bruto)[:120]


def carregar_alertas() -> List[Dict[str, Any]]:
    try:
        from alertas_automaticos_radar_valoris import gerar_alertas_automaticos
        return gerar_alertas_automaticos()
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
        return carregar_pipeline(backend="csv", max_registros=2000)
    except Exception:
        return []


def carregar_ranking() -> List[Dict[str, Any]]:
    try:
        from analise_inteligente_backend_valoris import gerar_ranking_inteligente_backend
        return gerar_ranking_inteligente_backend(backend="csv", max_registros=2000)
    except Exception:
        return []


def obter_score_cockpit() -> int:
    try:
        from cockpit_principal_valoris import calcular_metricas_cockpit_principal
        return _int(calcular_metricas_cockpit_principal().get("score_cockpit"), 0)
    except Exception:
        return 0


def gerar_rotina_semanal() -> List[Dict[str, Any]]:
    itens: List[Dict[str, Any]] = []

    for alerta in carregar_alertas():
        severidade = _txt(alerta.get("severidade"))
        ticker = _txt(alerta.get("ticker")).upper()
        if not ticker:
            continue

        if severidade in {"Crítica", "Alta"}:
            bloco, prioridade = "Resolver hoje", "Alta"
        elif severidade == "Média/Alta":
            bloco, prioridade = "Revisar nesta semana", "Média/Alta"
        else:
            bloco, prioridade = "Acompanhar", "Média"

        acao = _txt(alerta.get("acao_recomendada"))
        itens.append({
            "id": chave_item(ticker, acao, bloco),
            "ticker": ticker,
            "empresa": _txt(alerta.get("empresa")),
            "bloco": bloco,
            "prioridade": prioridade,
            "origem": "Alertas Radar",
            "prazo": _txt(alerta.get("prazo")),
            "dias": alerta.get("dias_ate_prazo"),
            "acao": acao,
            "contexto": f"{_txt(alerta.get('tipo_alerta'))} | severidade {severidade}",
        })

    for item in carregar_radar():
        ticker = _txt(item.get("ticker")).upper()
        tipo_alerta = _txt(item.get("tipo_alerta"))
        criticidade = _txt(item.get("criticidade"))
        if not ticker or tipo_alerta in {"Monitoramento", "Concluída/fechada"}:
            continue

        bloco = "Resolver hoje" if criticidade == "Alta" or tipo_alerta == "Atrasada" else "Revisar nesta semana"
        acao = _txt(item.get("acao_recomendada_radar"))
        itens.append({
            "id": chave_item(ticker, acao, bloco),
            "ticker": ticker,
            "empresa": _txt(item.get("empresa")),
            "bloco": bloco,
            "prioridade": criticidade or "Média",
            "origem": "Radar Principal",
            "prazo": _txt(item.get("prazo")),
            "dias": item.get("dias_ate_prazo"),
            "acao": acao,
            "contexto": f"{tipo_alerta} | {criticidade}",
        })

    for item in carregar_pipeline():
        ticker = _txt(item.get("ticker")).upper()
        status = _txt(item.get("status")).lower()
        if not ticker or status in {"concluída", "concluida", "cancelada", "arquivada", "fechada"}:
            continue

        prioridade = _txt(item.get("prioridade")) or "Média"
        prazo = _data(item.get("prazo"))
        dias = (prazo - date.today()).days if prazo else None

        if prioridade == "Alta" or (dias is not None and dias <= 7):
            bloco = "Revisar nesta semana"
        elif dias is None:
            bloco = "Organizar pendências"
        else:
            bloco = "Acompanhar"

        acao = _txt(item.get("tipo_acao")) or "Acompanhar ação aberta"
        itens.append({
            "id": chave_item(ticker, acao, bloco),
            "ticker": ticker,
            "empresa": _txt(item.get("empresa")),
            "bloco": bloco,
            "prioridade": prioridade,
            "origem": "Pipeline Principal",
            "prazo": _txt(item.get("prazo")),
            "dias": dias if dias is not None else "",
            "acao": acao,
            "contexto": _txt(item.get("observacao")),
        })

    for item in carregar_ranking()[:10]:
        ticker = _txt(item.get("ticker")).upper()
        classificacao = _txt(item.get("classificacao"))
        if not ticker:
            continue

        if classificacao == "Alta prioridade":
            bloco, prioridade = "Decisões estratégicas", "Alta"
        elif classificacao.startswith("Boa candidata"):
            bloco, prioridade = "Decisões estratégicas", "Média"
        else:
            continue

        acao = _txt(item.get("acao_recomendada"))
        itens.append({
            "id": chave_item(ticker, acao, bloco),
            "ticker": ticker,
            "empresa": _txt(item.get("empresa")),
            "bloco": bloco,
            "prioridade": prioridade,
            "origem": "Análise Principal",
            "prazo": "",
            "dias": "",
            "acao": acao,
            "contexto": f"{classificacao} | score {_int(item.get('score_inteligente'), 0)}/100",
        })

    unicos: Dict[str, Dict[str, Any]] = {}
    for item in itens:
        item_id = _txt(item.get("id"))
        if item_id not in unicos or prioridade_rank(item.get("prioridade")) < prioridade_rank(unicos[item_id].get("prioridade")):
            unicos[item_id] = item

    rotina = list(unicos.values())
    ordem_bloco = {
        "Resolver hoje": 1,
        "Revisar nesta semana": 2,
        "Decisões estratégicas": 3,
        "Organizar pendências": 4,
        "Acompanhar": 5,
    }

    rotina.sort(key=lambda item: (
        ordem_bloco.get(item.get("bloco"), 9),
        prioridade_rank(item.get("prioridade")),
        9999 if item.get("dias") in {"", None} else _int(item.get("dias"), 9999),
        item.get("ticker", ""),
    ))
    return rotina


def carregar_execucoes(max_registros: int = 500) -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_EXECUCOES, CAMPOS_EXECUCOES)
    try:
        with CAMINHO_EXECUCOES.open("r", newline="", encoding="utf-8") as arquivo:
            return list(deque(csv.DictReader(arquivo), maxlen=max_registros))
    except Exception:
        return []


def ids_executados_semana() -> set[str]:
    semana = intervalo_semana()
    ids = set()
    for execucao in carregar_execucoes():
        if execucao.get("semana_inicio") != semana["inicio"]:
            continue
        status = _txt(execucao.get("status_execucao")).lower()
        if status in {"feito", "resolvido", "adiado conscientemente", "em acompanhamento"}:
            ids.add(chave_item(execucao.get("ticker", ""), execucao.get("acao", ""), execucao.get("bloco", "")))
    return ids


def salvar_execucao(item: Dict[str, Any], status_execucao: str, responsavel: str, observacao: str = "") -> Path:
    _garantir_csv(CAMINHO_EXECUCOES, CAMPOS_EXECUCOES)
    semana = intervalo_semana()

    with CAMINHO_EXECUCOES.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_EXECUCOES)
        escritor.writerow({
            "data_hora": _agora_iso(),
            "semana_inicio": semana["inicio"],
            "semana_fim": semana["fim"],
            "ticker": _txt(item.get("ticker")).upper(),
            "empresa": _txt(item.get("empresa")),
            "bloco": _txt(item.get("bloco")),
            "prioridade": _txt(item.get("prioridade")),
            "acao": _txt(item.get("acao")),
            "status_execucao": _txt(status_execucao),
            "responsavel": _txt(responsavel),
            "observacao": _txt(observacao),
        })
    return CAMINHO_EXECUCOES


def calcular_metricas_rotina_semanal() -> Dict[str, Any]:
    rotina = gerar_rotina_semanal()
    executados = ids_executados_semana()
    cockpit_score = obter_score_cockpit()

    total = len(rotina)
    feitos = len([item for item in rotina if item.get("id") in executados])
    pendentes = total - feitos
    por_bloco = Counter(item.get("bloco", "Sem bloco") for item in rotina)
    altas = len([item for item in rotina if item.get("prioridade") in {"Crítica", "Alta", "Média/Alta"}])

    score = 45 + min(cockpit_score // 5, 18)
    if total:
        score += 15
    if pendentes == 0 and total > 0:
        score += 20
    elif pendentes <= 3:
        score += 10
    if altas:
        score -= min(altas * 4, 18)
    score = max(0, min(100, int(score)))

    if total == 0:
        risco, decisao, proximo = "Baixo", "Nenhuma ação crítica para a semana", "Manter monitoramento semanal pelo Cockpit."
    elif altas and pendentes > 0:
        risco, decisao, proximo = "Médio", "Há ações importantes para executar nesta semana", "Resolver primeiro os blocos Resolver hoje e Revisar nesta semana."
    elif pendentes > 0:
        risco, decisao, proximo = "Baixo/Médio", "Rotina semanal funcional com pendências leves", "Registrar execução das ações principais."
    else:
        risco, decisao, proximo = "Baixo", "Rotina semanal concluída", "Acompanhar novos alertas e preparar próxima semana."

    return {
        "versao": VERSAO_ROTINA_SEMANAL_INTELIGENTE_VALORIS,
        "gerado_em": _agora_iso(),
        "semana": intervalo_semana(),
        "score_rotina": score,
        "itens": total,
        "executados": feitos,
        "pendentes": pendentes,
        "prioridade_alta_ou_media_alta": altas,
        "blocos": dict(por_bloco),
        "score_cockpit": cockpit_score,
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo,
    }


def gerar_relatorio_rotina_markdown() -> str:
    metricas = calcular_metricas_rotina_semanal()
    rotina = gerar_rotina_semanal()
    semana = metricas["semana"]

    linhas = "\n".join([
        f"- **{item['bloco']} — {item['ticker']} — {item['empresa']}**: {item['acao']} | prioridade {item['prioridade']} | origem {item['origem']}."
        for item in rotina[:40]
    ]) or "- Nenhuma ação relevante para esta semana."

    return f"""# Rotina Semanal Inteligente — Valoris

Versão: {VERSAO_ROTINA_SEMANAL_INTELIGENTE_VALORIS}  
Gerado em: {_agora_iso()}  
Semana: {semana['inicio']} até {semana['fim']}

## Diagnóstico

Score rotina: {metricas['score_rotina']}/100  
Itens: {metricas['itens']}  
Executados: {metricas['executados']}  
Pendentes: {metricas['pendentes']}  
Prioridade alta/média-alta: {metricas['prioridade_alta_ou_media_alta']}  
Score Cockpit: {metricas['score_cockpit']}/100  

Risco: {metricas['risco']}  
Decisão: {metricas['decisao']}  
Próximo passo: {metricas['proximo_passo']}

## Plano da semana

{linhas}

## Estratégia

Esta rotina transforma o Valoris em um hábito operacional: abrir, revisar, agir, registrar e acompanhar. O produto passa a guiar o usuário pela semana, não apenas mostrar informações.
"""


def salvar_relatorio_rotina() -> Path:
    CAMINHO_RELATORIO.write_text(gerar_relatorio_rotina_markdown(), encoding="utf-8")
    return CAMINHO_RELATORIO


def gerar_manifesto_rotina() -> Dict[str, Any]:
    return {
        "produto": "Valoris",
        "versao": VERSAO_ROTINA_SEMANAL_INTELIGENTE_VALORIS,
        "modulo": "rotina_semanal_inteligente_valoris",
        "data_hora": _agora_iso(),
        "metricas": calcular_metricas_rotina_semanal(),
        "rotina": gerar_rotina_semanal(),
        "principio": "produto premium precisa virar rotina, não apenas painel",
        "proxima_etapa": "notificações e agenda a partir da rotina semanal",
    }


def salvar_manifesto_rotina() -> Path:
    CAMINHO_MANIFESTO.write_text(json.dumps(gerar_manifesto_rotina(), ensure_ascii=False, indent=2), encoding="utf-8")
    return CAMINHO_MANIFESTO


def renderizar_rotina_semanal_inteligente_valoris() -> None:
    st.subheader("Rotina Semanal Inteligente")
    st.caption("Plano semanal acionável: o que resolver hoje, revisar na semana, decidir e acompanhar.")

    metricas = calcular_metricas_rotina_semanal()
    semana = metricas["semana"]
    st.caption(f"Semana: {semana['inicio']} até {semana['fim']}")

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Score rotina", f"{metricas['score_rotina']}/100")
    col2.metric("Itens", metricas["itens"])
    col3.metric("Executados", metricas["executados"])
    col4.metric("Pendentes", metricas["pendentes"])
    col5.metric("Prioridade alta", metricas["prioridade_alta_ou_media_alta"])

    if metricas["risco"] == "Baixo":
        st.success(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    elif metricas["risco"] == "Médio":
        st.warning(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    else:
        st.info(f"{metricas['decisao']} — {metricas['proximo_passo']}")

    st.divider()
    rotina = gerar_rotina_semanal()
    executados = ids_executados_semana()

    st.markdown("### Plano da semana")
    col_f1, col_f2, col_f3 = st.columns(3)
    blocos = ["Todos"] + sorted({item.get("bloco", "") for item in rotina if item.get("bloco")})
    prioridades = ["Todas"] + sorted({item.get("prioridade", "") for item in rotina if item.get("prioridade")})
    filtro_bloco = col_f1.selectbox("Bloco", blocos)
    filtro_prioridade = col_f2.selectbox("Prioridade", prioridades)
    filtro_ticker = col_f3.text_input("Ticker", value="")

    filtrados = []
    for item in rotina:
        if filtro_bloco != "Todos" and item.get("bloco") != filtro_bloco:
            continue
        if filtro_prioridade != "Todas" and item.get("prioridade") != filtro_prioridade:
            continue
        if filtro_ticker.strip() and filtro_ticker.strip().upper() not in item.get("ticker", ""):
            continue
        filtrados.append(item)

    tabela = [{
        "feito": "Sim" if item.get("id") in executados else "Não",
        "bloco": item.get("bloco"),
        "ticker": item.get("ticker"),
        "empresa": item.get("empresa"),
        "prioridade": item.get("prioridade"),
        "prazo": item.get("prazo"),
        "dias": item.get("dias"),
        "origem": item.get("origem"),
        "ação": item.get("acao"),
    } for item in filtrados]
    st.dataframe(tabela, use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("### Registrar execução da rotina")

    if filtrados:
        opcoes = [f"{item['bloco']} | {item['ticker']} | {item['prioridade']} | {item['acao'][:70]}" for item in filtrados]
        escolha = st.selectbox("Item da rotina", opcoes)
        item = filtrados[opcoes.index(escolha)]
        st.info(item.get("acao"))

        col_a, col_b = st.columns(2)
        status_execucao = col_a.selectbox("Status", ["Em acompanhamento", "Feito", "Resolvido", "Adiado conscientemente"])
        responsavel = col_b.text_input("Responsável", value="Fundador")
        observacao = st.text_area("Observação", value=f"Execução registrada na Rotina Semanal Inteligente v{VERSAO_ROTINA_SEMANAL_INTELIGENTE_VALORIS}.", height=90)

        if st.button("Salvar execução da rotina"):
            salvar_execucao(item, status_execucao=status_execucao, responsavel=responsavel, observacao=observacao)
            st.success("Execução da rotina registrada.")
            st.rerun()
    else:
        st.info("Nenhum item encontrado com os filtros atuais.")

    execucoes = carregar_execucoes()
    if execucoes:
        st.markdown("### Execuções registradas")
        st.dataframe(execucoes, use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("### Relatórios")
    col_r1, col_r2 = st.columns(2)
    if col_r1.button("Salvar relatório da rotina"):
        st.success(f"Relatório salvo em {salvar_relatorio_rotina()}")
    if col_r2.button("Salvar manifesto da rotina"):
        st.success(f"Manifesto salvo em {salvar_manifesto_rotina()}")

    st.download_button(
        "Baixar relatório da rotina (.md)",
        data=gerar_relatorio_rotina_markdown(),
        file_name="RELATORIO_ROTINA_SEMANAL_INTELIGENTE_VALORIS.md",
        mime="text/markdown",
    )


def executar_autoteste_rotina_semanal_inteligente_valoris() -> Dict[str, Any]:
    return {"ok": True, "versao": VERSAO_ROTINA_SEMANAL_INTELIGENTE_VALORIS, "metricas": calcular_metricas_rotina_semanal()}
