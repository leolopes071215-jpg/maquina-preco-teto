# aprovacao_notificacoes_valoris.py
# Valoris — Aprovação de Notificações v3.12.0

from __future__ import annotations

import csv
import json
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st

VERSAO_APROVACAO_NOTIFICACOES_VALORIS = "3.12.0"
CAMINHO_RASCUNHOS = Path("rascunhos_notificacoes_externas_valoris.csv")
CAMINHO_APROVACOES = Path("aprovacoes_notificacoes_externas_valoris.csv")
CAMINHO_RELATORIO = Path("RELATORIO_APROVACAO_NOTIFICACOES_VALORIS.md")
CAMINHO_MANIFESTO = Path("manifesto_aprovacao_notificacoes_valoris.json")

CAMPOS_RASCUNHOS = ["data_hora", "canal", "ticker", "empresa", "tipo", "severidade", "destinatario", "assunto", "mensagem", "status", "observacao"]
CAMPOS_APROVACOES = ["data_hora", "id_rascunho", "canal", "ticker", "empresa", "tipo", "severidade", "decisao_aprovacao", "responsavel", "motivo", "proxima_acao"]


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


def _id_rascunho(item: Dict[str, Any]) -> str:
    bruto = "|".join([
        _txt(item.get("data_hora")),
        _txt(item.get("canal")),
        _txt(item.get("ticker")).upper(),
        _txt(item.get("tipo")),
        _txt(item.get("assunto")),
    ])
    seguro = "".join(ch if ch.isalnum() else "_" for ch in bruto)
    return "_".join([p for p in seguro.split("_") if p])[:160] or "rascunho_sem_id"


def severidade_rank(valor: Any) -> int:
    return {"Crítica": 1, "Alta": 2, "Média/Alta": 3, "Média": 4, "Baixa": 5}.get(_txt(valor), 9)


def carregar_metricas_higiene() -> Dict[str, Any]:
    try:
        from higiene_operacional_valoris import calcular_metricas_higiene_operacional
        return calcular_metricas_higiene_operacional()
    except Exception:
        return {}


def carregar_metricas_externas() -> Dict[str, Any]:
    try:
        from notificacoes_externas_valoris import calcular_metricas_notificacoes_externas
        return calcular_metricas_notificacoes_externas()
    except Exception:
        return {}


def carregar_rascunhos(max_registros: int = 1000) -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_RASCUNHOS, CAMPOS_RASCUNHOS)
    try:
        with CAMINHO_RASCUNHOS.open("r", newline="", encoding="utf-8") as arquivo:
            return list(deque(csv.DictReader(arquivo), maxlen=max_registros))
    except Exception:
        return []


def carregar_aprovacoes(max_registros: int = 1000) -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_APROVACOES, CAMPOS_APROVACOES)
    try:
        with CAMINHO_APROVACOES.open("r", newline="", encoding="utf-8") as arquivo:
            return list(deque(csv.DictReader(arquivo), maxlen=max_registros))
    except Exception:
        return []


def mapa_aprovacoes() -> Dict[str, Dict[str, str]]:
    mapa: Dict[str, Dict[str, str]] = {}
    for item in carregar_aprovacoes():
        rid = _txt(item.get("id_rascunho"))
        if rid:
            mapa[rid] = item
    return mapa


def classificar_rascunho(item: Dict[str, Any]) -> Dict[str, Any]:
    higiene = carregar_metricas_higiene()
    score_higiene = _int(higiene.get("score_higiene"), 0)
    pendentes_higiene = _int(higiene.get("pendentes"), 0)
    status = _txt(item.get("status")).lower()
    severidade = _txt(item.get("severidade"))
    mensagem = _txt(item.get("mensagem"))
    canal = _txt(item.get("canal"))

    bloqueios: List[str] = []
    if not mensagem:
        bloqueios.append("mensagem vazia")
    if not canal:
        bloqueios.append("canal não definido")
    if "não enviar" in status or "nao enviar" in status:
        bloqueios.append("rascunho marcado para não enviar")
    if score_higiene < 55 or pendentes_higiene >= 10:
        bloqueios.append("higiene operacional fraca")

    if bloqueios:
        return {"recomendacao": "Bloquear envio", "proxima_acao": "Corrigir bloqueios antes de aprovar.", "bloqueios": "; ".join(bloqueios)}
    if severidade in {"Crítica", "Alta"}:
        return {"recomendacao": "Revisão manual obrigatória", "proxima_acao": "Revisar texto, destinatário e risco antes de aprovar.", "bloqueios": ""}
    if "aprovado" in status:
        return {"recomendacao": "Pronto para fila manual", "proxima_acao": "Pode entrar na fila de envio manual.", "bloqueios": ""}
    return {"recomendacao": "Revisar antes de aprovar", "proxima_acao": "Validar conteúdo e decidir aprovação.", "bloqueios": ""}


def gerar_fila_aprovacao() -> List[Dict[str, Any]]:
    aprovacoes = mapa_aprovacoes()
    fila: List[Dict[str, Any]] = []

    for item in carregar_rascunhos():
        rid = _id_rascunho(item)
        classe = classificar_rascunho(item)
        anterior = aprovacoes.get(rid, {}).get("decisao_aprovacao", "")
        fila.append({
            "id_rascunho": rid,
            "data_hora": _txt(item.get("data_hora")),
            "canal": _txt(item.get("canal")),
            "ticker": _txt(item.get("ticker")).upper(),
            "empresa": _txt(item.get("empresa")),
            "tipo": _txt(item.get("tipo")),
            "severidade": _txt(item.get("severidade")),
            "destinatario": _txt(item.get("destinatario")),
            "assunto": _txt(item.get("assunto")),
            "mensagem": _txt(item.get("mensagem")),
            "status_rascunho": _txt(item.get("status")),
            "observacao_rascunho": _txt(item.get("observacao")),
            "recomendacao": classe["recomendacao"],
            "proxima_acao": classe["proxima_acao"],
            "bloqueios": classe["bloqueios"],
            "decisao_anterior": anterior,
        })

    fila.sort(key=lambda i: (0 if not i["decisao_anterior"] else 1, severidade_rank(i.get("severidade")), i.get("ticker", "")))
    return fila


def salvar_aprovacao(item: Dict[str, Any], decisao: str, responsavel: str, motivo: str, proxima_acao: str) -> Path:
    _garantir_csv(CAMINHO_APROVACOES, CAMPOS_APROVACOES)
    with CAMINHO_APROVACOES.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_APROVACOES)
        escritor.writerow({
            "data_hora": _agora_iso(),
            "id_rascunho": _txt(item.get("id_rascunho")),
            "canal": _txt(item.get("canal")),
            "ticker": _txt(item.get("ticker")).upper(),
            "empresa": _txt(item.get("empresa")),
            "tipo": _txt(item.get("tipo")),
            "severidade": _txt(item.get("severidade")),
            "decisao_aprovacao": _txt(decisao),
            "responsavel": _txt(responsavel),
            "motivo": _txt(motivo),
            "proxima_acao": _txt(proxima_acao),
        })
    return CAMINHO_APROVACOES


def calcular_metricas_aprovacao_notificacoes() -> Dict[str, Any]:
    fila = gerar_fila_aprovacao()
    aprovacoes = carregar_aprovacoes()
    higiene = carregar_metricas_higiene()
    externas = carregar_metricas_externas()

    pendentes = len([i for i in fila if not _txt(i.get("decisao_anterior"))])
    bloqueados = len([i for i in fila if i.get("recomendacao") == "Bloquear envio"])
    revisao_obrigatoria = len([i for i in fila if i.get("recomendacao") == "Revisão manual obrigatória"])
    prontos = len([i for i in fila if i.get("recomendacao") == "Pronto para fila manual"])
    score_higiene = _int(higiene.get("score_higiene"), 0)
    score_externas = _int(externas.get("score_prontidao"), 0)

    score = 45 + min(score_higiene // 4, 25) + min(score_externas // 5, 20)
    if prontos:
        score += 8
    if pendentes <= 3:
        score += 7
    if bloqueados:
        score -= min(bloqueados * 10, 30)
    score = max(0, min(100, int(score)))

    if not fila:
        risco, decisao, proximo = "Baixo", "Sem rascunhos externos para aprovar", "Gerar rascunhos na página Notificações Externas."
    elif bloqueados:
        risco, decisao, proximo = "Médio", "Há rascunhos bloqueados para envio", "Corrigir bloqueios antes de qualquer envio manual."
    elif revisao_obrigatoria:
        risco, decisao, proximo = "Médio", "Há rascunhos sensíveis que exigem revisão manual", "Aprovar ou bloquear rascunhos críticos e de alta severidade."
    elif prontos:
        risco, decisao, proximo = "Baixo/Médio", "Há rascunhos prontos para fila manual", "Aprovar manualmente e preparar exportação segura."
    else:
        risco, decisao, proximo = "Baixo", "Fila de aprovação sob controle", "Manter revisão manual antes de automação."

    return {
        "versao": VERSAO_APROVACAO_NOTIFICACOES_VALORIS,
        "gerado_em": _agora_iso(),
        "score_aprovacao": score,
        "rascunhos": len(fila),
        "pendentes": pendentes,
        "bloqueados": bloqueados,
        "revisao_obrigatoria": revisao_obrigatoria,
        "prontos": prontos,
        "aprovacoes_registradas": len(aprovacoes),
        "score_higiene": score_higiene,
        "score_externas": score_externas,
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo,
    }


def gerar_relatorio_aprovacao_markdown() -> str:
    metricas = calcular_metricas_aprovacao_notificacoes()
    fila = gerar_fila_aprovacao()
    linhas = "\n".join([
        f"- **{i['severidade']} — {i['ticker']} — {i['canal']}**: {i['recomendacao']} | {i['proxima_acao']} | assunto: {i['assunto']}"
        for i in fila[:60]
    ]) or "- Nenhum rascunho na fila de aprovação."
    return f"""# Aprovação de Notificações — Valoris

Versão: {VERSAO_APROVACAO_NOTIFICACOES_VALORIS}  
Gerado em: {_agora_iso()}

## Diagnóstico

Score aprovação: {metricas['score_aprovacao']}/100  
Rascunhos: {metricas['rascunhos']}  
Pendentes: {metricas['pendentes']}  
Bloqueados: {metricas['bloqueados']}  
Revisão obrigatória: {metricas['revisao_obrigatoria']}  
Prontos: {metricas['prontos']}  
Aprovações registradas: {metricas['aprovacoes_registradas']}  
Score higiene: {metricas['score_higiene']}/100  
Score notificações externas: {metricas['score_externas']}/100  

Risco: {metricas['risco']}  
Decisão: {metricas['decisao']}  
Próximo passo: {metricas['proximo_passo']}

## Fila de aprovação

{linhas}

## Estratégia

Esta versão cria a barreira de segurança antes de qualquer envio externo real: rascunho, revisão, aprovação e só depois exportação ou automação.
"""


def salvar_relatorio_aprovacao() -> Path:
    CAMINHO_RELATORIO.write_text(gerar_relatorio_aprovacao_markdown(), encoding="utf-8")
    return CAMINHO_RELATORIO


def salvar_manifesto_aprovacao() -> Path:
    CAMINHO_MANIFESTO.write_text(json.dumps({
        "produto": "Valoris",
        "versao": VERSAO_APROVACAO_NOTIFICACOES_VALORIS,
        "modulo": "aprovacao_notificacoes_valoris",
        "data_hora": _agora_iso(),
        "metricas": calcular_metricas_aprovacao_notificacoes(),
        "fila": gerar_fila_aprovacao(),
        "principio": "nenhuma automação externa deve existir sem aprovação rastreável",
        "proxima_etapa": "exportação segura dos rascunhos aprovados",
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    return CAMINHO_MANIFESTO


def renderizar_aprovacao_notificacoes_valoris() -> None:
    st.subheader("Aprovação de Notificações")
    st.caption("Barreira de segurança antes de qualquer envio externo: revisar, aprovar, bloquear ou manter em análise.")

    metricas = calcular_metricas_aprovacao_notificacoes()
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Score aprovação", f"{metricas['score_aprovacao']}/100")
    col2.metric("Rascunhos", metricas["rascunhos"])
    col3.metric("Pendentes", metricas["pendentes"])
    col4.metric("Bloqueados", metricas["bloqueados"])
    col5.metric("Prontos", metricas["prontos"])

    if metricas["risco"] == "Médio":
        st.warning(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    elif metricas["risco"] == "Baixo":
        st.success(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    else:
        st.info(f"{metricas['decisao']} — {metricas['proximo_passo']}")

    st.divider()
    fila = gerar_fila_aprovacao()
    st.markdown("### Fila de aprovação")

    col_f1, col_f2, col_f3 = st.columns(3)
    canais = ["Todos"] + sorted({i.get("canal", "") for i in fila if i.get("canal")})
    recomendacoes = ["Todas"] + sorted({i.get("recomendacao", "") for i in fila if i.get("recomendacao")})
    severidades = ["Todas"] + sorted({i.get("severidade", "") for i in fila if i.get("severidade")})
    filtro_canal = col_f1.selectbox("Canal", canais)
    filtro_recomendacao = col_f2.selectbox("Recomendação", recomendacoes)
    filtro_severidade = col_f3.selectbox("Severidade", severidades)
    filtro_ticker = st.text_input("Ticker", value="")

    filtrados = []
    for item in fila:
        if filtro_canal != "Todos" and item.get("canal") != filtro_canal:
            continue
        if filtro_recomendacao != "Todas" and item.get("recomendacao") != filtro_recomendacao:
            continue
        if filtro_severidade != "Todas" and item.get("severidade") != filtro_severidade:
            continue
        if filtro_ticker.strip() and filtro_ticker.strip().upper() not in item.get("ticker", ""):
            continue
        filtrados.append(item)

    st.dataframe([{
        "decisão anterior": i.get("decisao_anterior"),
        "canal": i.get("canal"),
        "ticker": i.get("ticker"),
        "empresa": i.get("empresa"),
        "severidade": i.get("severidade"),
        "tipo": i.get("tipo"),
        "recomendação": i.get("recomendacao"),
        "bloqueios": i.get("bloqueios"),
        "assunto": i.get("assunto"),
    } for i in filtrados], use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("### Revisar rascunho e registrar aprovação")

    if filtrados:
        opcoes = [f"{i['severidade']} | {i['canal']} | {i['ticker']} | {i['recomendacao']}" for i in filtrados]
        escolha = st.selectbox("Rascunho", opcoes)
        item = filtrados[opcoes.index(escolha)]
        st.text_input("Assunto", value=item.get("assunto", ""), disabled=True)
        st.text_area("Mensagem", value=item.get("mensagem", ""), height=220, disabled=True)
        col_a, col_b = st.columns(2)
        decisao = col_a.selectbox("Decisão", ["Aprovado para fila manual", "Manter em revisão", "Bloquear envio", "Aguardar higiene operacional"])
        responsavel = col_b.text_input("Responsável", value="Fundador")
        motivo = st.text_area("Motivo", value=f"Decisão registrada na Aprovação de Notificações v{VERSAO_APROVACAO_NOTIFICACOES_VALORIS}.", height=90)
        proxima = st.text_input("Próxima ação", value=item.get("proxima_acao", ""))
        if st.button("Salvar decisão de aprovação"):
            salvar_aprovacao(item, decisao=decisao, responsavel=responsavel, motivo=motivo, proxima_acao=proxima)
            st.success("Decisão de aprovação registrada. Nenhum envio foi realizado.")
            st.rerun()
    else:
        st.info("Nenhum rascunho encontrado com os filtros atuais.")

    aprovacoes = carregar_aprovacoes()
    if aprovacoes:
        st.markdown("### Aprovações registradas")
        st.dataframe(aprovacoes, use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("### Relatórios")
    col_r1, col_r2 = st.columns(2)
    if col_r1.button("Salvar relatório de aprovação"):
        st.success(f"Relatório salvo em {salvar_relatorio_aprovacao()}")
    if col_r2.button("Salvar manifesto de aprovação"):
        st.success(f"Manifesto salvo em {salvar_manifesto_aprovacao()}")
    st.download_button("Baixar relatório de aprovação (.md)", data=gerar_relatorio_aprovacao_markdown(), file_name="RELATORIO_APROVACAO_NOTIFICACOES_VALORIS.md", mime="text/markdown")


def executar_autoteste_aprovacao_notificacoes_valoris() -> Dict[str, Any]:
    return {"ok": True, "versao": VERSAO_APROVACAO_NOTIFICACOES_VALORIS, "metricas": calcular_metricas_aprovacao_notificacoes()}
