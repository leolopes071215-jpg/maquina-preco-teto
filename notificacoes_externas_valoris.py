# notificacoes_externas_valoris.py
# Valoris — Notificações Externas em Modo Rascunho v3.11.9
# ------------------------------------------------------------
# Esta página prepara rascunhos para canais externos, mas não envia nada automaticamente.

from __future__ import annotations

import csv
import json
from collections import Counter, deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st

VERSAO_NOTIFICACOES_EXTERNAS_VALORIS = "3.11.9"

CAMINHO_RASCUNHOS = Path("rascunhos_notificacoes_externas_valoris.csv")
CAMINHO_RELATORIO = Path("RELATORIO_NOTIFICACOES_EXTERNAS_VALORIS.md")
CAMINHO_MANIFESTO = Path("manifesto_notificacoes_externas_valoris.json")

CAMPOS_RASCUNHOS = [
    "data_hora",
    "canal",
    "ticker",
    "empresa",
    "tipo",
    "severidade",
    "destinatario",
    "assunto",
    "mensagem",
    "status",
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


def carregar_notificacoes() -> List[Dict[str, Any]]:
    try:
        from central_notificacoes_valoris import gerar_notificacoes
        return gerar_notificacoes()
    except Exception:
        return []


def carregar_metricas_notificacoes() -> Dict[str, Any]:
    try:
        from central_notificacoes_valoris import calcular_metricas_notificacoes
        return calcular_metricas_notificacoes()
    except Exception:
        return {}


def carregar_metricas_higiene() -> Dict[str, Any]:
    try:
        from higiene_operacional_valoris import calcular_metricas_higiene_operacional
        return calcular_metricas_higiene_operacional()
    except Exception:
        return {}


def severidade_rank(valor: Any) -> int:
    return {
        "Crítica": 1,
        "Alta": 2,
        "Média/Alta": 3,
        "Média": 4,
        "Baixa": 5,
    }.get(_txt(valor), 9)


def filtrar_notificacoes_relevantes() -> List[Dict[str, Any]]:
    notificacoes = carregar_notificacoes()
    relevantes = []

    for item in notificacoes:
        severidade = _txt(item.get("severidade"))
        tipo = _txt(item.get("tipo"))

        if severidade in {"Crítica", "Alta", "Média/Alta"}:
            relevantes.append(item)
            continue

        if tipo in {"Atrasado", "Sem prazo", "Vence em 7 dias", "Vence em 15 dias"}:
            relevantes.append(item)
            continue

    relevantes.sort(
        key=lambda item: (
            severidade_rank(item.get("severidade")),
            9999 if item.get("dias") in {"", None} else _int(item.get("dias"), 9999),
            item.get("ticker", ""),
        )
    )
    return relevantes


def gerar_assunto(item: Dict[str, Any], canal: str) -> str:
    ticker = _txt(item.get("ticker")).upper()
    tipo = _txt(item.get("tipo"))
    severidade = _txt(item.get("severidade"))

    if canal == "Calendário":
        return f"Revisão Valoris — {ticker} — {tipo}"
    if canal == "E-mail":
        return f"[Valoris] {severidade}: {ticker} — {tipo}"
    if canal == "WhatsApp":
        return f"Valoris | {ticker} | {tipo}"
    return f"Valoris — {ticker} — {tipo}"


def gerar_mensagem(item: Dict[str, Any], canal: str = "Resumo Executivo") -> str:
    ticker = _txt(item.get("ticker")).upper()
    empresa = _txt(item.get("empresa")) or ticker
    tipo = _txt(item.get("tipo"))
    severidade = _txt(item.get("severidade"))
    origem = _txt(item.get("origem"))
    data_evento = _txt(item.get("data_evento")) or "sem data definida"
    dias = _txt(item.get("dias"))
    acao = _txt(item.get("acao_recomendada"))
    contexto = _txt(item.get("contexto"))
    dias_texto = f"{dias} dias" if dias not in {"", "None"} else "sem prazo claro"

    if canal == "WhatsApp":
        return (
            f"Valoris — {severidade}\n"
            f"Ativo: {ticker} ({empresa})\n"
            f"Tipo: {tipo}\n"
            f"Prazo: {data_evento} ({dias_texto})\n"
            f"Ação: {acao}\n"
            f"Origem: {origem}\n"
            f"Obs.: rascunho interno; nada foi enviado automaticamente."
        )

    if canal == "E-mail":
        return (
            f"Olá,\n\n"
            f"O Valoris identificou uma notificação que exige atenção.\n\n"
            f"Ativo: {ticker} — {empresa}\n"
            f"Severidade: {severidade}\n"
            f"Tipo: {tipo}\n"
            f"Origem: {origem}\n"
            f"Data/prazo: {data_evento} ({dias_texto})\n\n"
            f"Ação recomendada:\n{acao}\n\n"
            f"Contexto:\n{contexto or 'Sem contexto adicional.'}\n\n"
            f"Este é um rascunho interno. Nada foi enviado automaticamente."
        )

    if canal == "Calendário":
        return (
            f"Revisão Valoris\n\n"
            f"Ativo: {ticker} — {empresa}\n"
            f"Tipo: {tipo}\n"
            f"Severidade: {severidade}\n"
            f"Origem: {origem}\n\n"
            f"Ação recomendada:\n{acao}\n\n"
            f"Observação: rascunho de evento. Criar no calendário somente após revisão."
        )

    return (
        f"{severidade} | {ticker} — {empresa} | {tipo}\n"
        f"Origem: {origem}\n"
        f"Prazo: {data_evento} ({dias_texto})\n"
        f"Ação recomendada: {acao}"
    )


def gerar_rascunhos_notificacoes(canal: str = "Resumo Executivo") -> List[Dict[str, Any]]:
    rascunhos = []
    for item in filtrar_notificacoes_relevantes():
        rascunhos.append(
            {
                "canal": canal,
                "ticker": _txt(item.get("ticker")).upper(),
                "empresa": _txt(item.get("empresa")),
                "tipo": _txt(item.get("tipo")),
                "severidade": _txt(item.get("severidade")),
                "origem": _txt(item.get("origem")),
                "data_evento": _txt(item.get("data_evento")),
                "dias": _txt(item.get("dias")),
                "assunto": gerar_assunto(item, canal),
                "mensagem": gerar_mensagem(item, canal),
                "acao_recomendada": _txt(item.get("acao_recomendada")),
            }
        )
    return rascunhos


def salvar_rascunho(rascunho: Dict[str, Any], destinatario: str, status: str, observacao: str = "") -> Path:
    _garantir_csv(CAMINHO_RASCUNHOS, CAMPOS_RASCUNHOS)
    with CAMINHO_RASCUNHOS.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_RASCUNHOS)
        escritor.writerow(
            {
                "data_hora": _agora_iso(),
                "canal": _txt(rascunho.get("canal")),
                "ticker": _txt(rascunho.get("ticker")).upper(),
                "empresa": _txt(rascunho.get("empresa")),
                "tipo": _txt(rascunho.get("tipo")),
                "severidade": _txt(rascunho.get("severidade")),
                "destinatario": _txt(destinatario),
                "assunto": _txt(rascunho.get("assunto")),
                "mensagem": _txt(rascunho.get("mensagem")),
                "status": _txt(status),
                "observacao": _txt(observacao),
            }
        )
    return CAMINHO_RASCUNHOS


def carregar_rascunhos_salvos(max_registros: int = 800) -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_RASCUNHOS, CAMPOS_RASCUNHOS)
    try:
        with CAMINHO_RASCUNHOS.open("r", newline="", encoding="utf-8") as arquivo:
            return list(deque(csv.DictReader(arquivo), maxlen=max_registros))
    except Exception:
        return []


def calcular_metricas_notificacoes_externas() -> Dict[str, Any]:
    notificacoes = carregar_notificacoes()
    relevantes = filtrar_notificacoes_relevantes()
    metricas_central = carregar_metricas_notificacoes()
    metricas_higiene = carregar_metricas_higiene()
    rascunhos_salvos = carregar_rascunhos_salvos()

    contador_severidade = Counter(_txt(item.get("severidade")) for item in relevantes)
    criticas = contador_severidade.get("Crítica", 0)
    altas = contador_severidade.get("Alta", 0)
    media_alta = contador_severidade.get("Média/Alta", 0)

    score_higiene = _int(metricas_higiene.get("score_higiene"), 0)
    score_central = _int(metricas_central.get("score_notificacoes"), 0)
    problemas_higiene = _int(metricas_higiene.get("pendentes"), 0)

    score = 45
    score += min(score_higiene // 4, 25)
    score += min(score_central // 5, 20)
    if relevantes:
        score += 10
    if rascunhos_salvos:
        score += 5
    if problemas_higiene:
        score -= min(problemas_higiene * 4, 25)
    if criticas:
        score -= min(criticas * 12, 30)
    score = max(0, min(100, int(score)))

    if not notificacoes:
        risco = "Baixo"
        decisao = "Não há base de notificações para rascunhos externos"
        proximo = "Manter operação interna e aguardar novas notificações."
    elif problemas_higiene > 0:
        risco = "Médio"
        decisao = "Notificações externas ainda exigem higiene operacional"
        proximo = "Resolver pendências de higiene antes de automatizar envios."
    elif criticas:
        risco = "Médio/Alto"
        decisao = "Há notificações críticas; gerar rascunhos, mas revisar manualmente"
        proximo = "Aprovar manualmente rascunhos críticos antes de qualquer integração externa."
    elif relevantes:
        risco = "Baixo/Médio"
        decisao = "Rascunhos externos prontos para revisão manual"
        proximo = "Salvar rascunhos aprovados e só depois pensar em automação real."
    else:
        risco = "Baixo"
        decisao = "Sem notificações relevantes para canais externos"
        proximo = "Manter central interna como fonte principal."

    return {
        "versao": VERSAO_NOTIFICACOES_EXTERNAS_VALORIS,
        "gerado_em": _agora_iso(),
        "score_prontidao": score,
        "notificacoes_internas": len(notificacoes),
        "notificacoes_relevantes": len(relevantes),
        "rascunhos_salvos": len(rascunhos_salvos),
        "criticas": criticas,
        "altas": altas,
        "media_alta": media_alta,
        "score_higiene": score_higiene,
        "score_central": score_central,
        "problemas_higiene_pendentes": problemas_higiene,
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo,
    }


def gerar_relatorio_notificacoes_externas_markdown(canal: str = "Resumo Executivo") -> str:
    metricas = calcular_metricas_notificacoes_externas()
    rascunhos = gerar_rascunhos_notificacoes(canal=canal)
    linhas = "\n\n".join(
        [
            f"### {r['ticker']} — {r['tipo']} — {r['severidade']}\n\n**Assunto:** {r['assunto']}\n\n{r['mensagem']}"
            for r in rascunhos[:30]
        ]
    ) or "Nenhum rascunho externo relevante."

    return f"""# Notificações Externas em Modo Rascunho — Valoris

Versão: {VERSAO_NOTIFICACOES_EXTERNAS_VALORIS}  
Gerado em: {_agora_iso()}  
Canal: {canal}

## Diagnóstico

Score prontidão: {metricas['score_prontidao']}/100  
Notificações internas: {metricas['notificacoes_internas']}  
Notificações relevantes: {metricas['notificacoes_relevantes']}  
Rascunhos salvos: {metricas['rascunhos_salvos']}  
Críticas: {metricas['criticas']}  
Altas: {metricas['altas']}  
Score higiene: {metricas['score_higiene']}/100  
Score central: {metricas['score_central']}/100  
Problemas de higiene pendentes: {metricas['problemas_higiene_pendentes']}  

Risco: {metricas['risco']}  
Decisão: {metricas['decisao']}  
Próximo passo: {metricas['proximo_passo']}

## Rascunhos

{linhas}

## Estratégia

Esta versão não envia mensagens. Ela prepara rascunhos para revisão manual. O Valoris só deve avançar para automação externa quando a operação interna estiver limpa, com baixa duplicidade e baixa pendência.
"""


def salvar_relatorio_notificacoes_externas(canal: str = "Resumo Executivo") -> Path:
    CAMINHO_RELATORIO.write_text(gerar_relatorio_notificacoes_externas_markdown(canal=canal), encoding="utf-8")
    return CAMINHO_RELATORIO


def gerar_manifesto_notificacoes_externas(canal: str = "Resumo Executivo") -> Dict[str, Any]:
    return {
        "produto": "Valoris",
        "versao": VERSAO_NOTIFICACOES_EXTERNAS_VALORIS,
        "modulo": "notificacoes_externas_valoris",
        "data_hora": _agora_iso(),
        "canal": canal,
        "metricas": calcular_metricas_notificacoes_externas(),
        "rascunhos": gerar_rascunhos_notificacoes(canal=canal),
        "principio": "rascunhar antes de enviar; revisão manual antes de automação",
        "proxima_etapa": "integração com calendário ou e-mail somente após aprovação manual",
    }


def salvar_manifesto_notificacoes_externas(canal: str = "Resumo Executivo") -> Path:
    CAMINHO_MANIFESTO.write_text(json.dumps(gerar_manifesto_notificacoes_externas(canal=canal), ensure_ascii=False, indent=2), encoding="utf-8")
    return CAMINHO_MANIFESTO


def renderizar_notificacoes_externas_valoris() -> None:
    st.subheader("Notificações Externas")
    st.caption("Modo rascunho: prepara mensagens para canais externos, mas não envia nada automaticamente.")

    metricas = calcular_metricas_notificacoes_externas()
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Score prontidão", f"{metricas['score_prontidao']}/100")
    col2.metric("Relevantes", metricas["notificacoes_relevantes"])
    col3.metric("Rascunhos", metricas["rascunhos_salvos"])
    col4.metric("Críticas", metricas["criticas"])
    col5.metric("Higiene", f"{metricas['score_higiene']}/100")

    if metricas["risco"] in {"Médio/Alto", "Alto"}:
        st.error(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    elif metricas["risco"] == "Médio":
        st.warning(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    elif metricas["risco"] == "Baixo":
        st.success(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    else:
        st.info(f"{metricas['decisao']} — {metricas['proximo_passo']}")

    st.divider()
    canal = st.selectbox("Canal de rascunho", ["Resumo Executivo", "WhatsApp", "E-mail", "Calendário"])
    rascunhos = gerar_rascunhos_notificacoes(canal=canal)

    st.markdown("### Rascunhos gerados")
    col_f1, col_f2 = st.columns(2)
    filtro_ticker = col_f1.text_input("Ticker", value="")
    severidades = ["Todas"] + sorted({r.get("severidade", "") for r in rascunhos if r.get("severidade")})
    filtro_severidade = col_f2.selectbox("Severidade", severidades)

    filtrados = []
    for r in rascunhos:
        if filtro_ticker.strip() and filtro_ticker.strip().upper() not in r.get("ticker", ""):
            continue
        if filtro_severidade != "Todas" and r.get("severidade") != filtro_severidade:
            continue
        filtrados.append(r)

    st.dataframe(
        [
            {
                "canal": r.get("canal"),
                "ticker": r.get("ticker"),
                "empresa": r.get("empresa"),
                "tipo": r.get("tipo"),
                "severidade": r.get("severidade"),
                "origem": r.get("origem"),
                "assunto": r.get("assunto"),
            }
            for r in filtrados
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.divider()
    st.markdown("### Revisar e salvar rascunho")

    if filtrados:
        opcoes = [f"{r['severidade']} | {r['ticker']} | {r['tipo']} | {r['canal']}" for r in filtrados]
        escolha = st.selectbox("Rascunho", opcoes)
        rascunho = filtrados[opcoes.index(escolha)]

        assunto = st.text_input("Assunto", value=rascunho.get("assunto", ""))
        mensagem = st.text_area("Mensagem", value=rascunho.get("mensagem", ""), height=220)
        destinatario = st.text_input("Destinatário", value="Revisão manual")
        status = st.selectbox("Status do rascunho", ["Rascunho aprovado", "Rascunho em revisão", "Não enviar", "Aguardar higiene operacional"])
        observacao = st.text_area("Observação", value=f"Rascunho salvo em modo seguro na v{VERSAO_NOTIFICACOES_EXTERNAS_VALORIS}. Nenhum envio automático realizado.", height=90)

        rascunho_editado = dict(rascunho)
        rascunho_editado["assunto"] = assunto
        rascunho_editado["mensagem"] = mensagem

        if st.button("Salvar rascunho revisado"):
            salvar_rascunho(rascunho_editado, destinatario=destinatario, status=status, observacao=observacao)
            st.success("Rascunho salvo. Nenhuma mensagem foi enviada.")
            st.rerun()
    else:
        st.info("Nenhum rascunho encontrado com os filtros atuais.")

    salvos = carregar_rascunhos_salvos()
    if salvos:
        st.markdown("### Rascunhos salvos")
        st.dataframe(salvos, use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("### Relatórios")
    col_r1, col_r2 = st.columns(2)
    if col_r1.button("Salvar relatório de notificações externas"):
        st.success(f"Relatório salvo em {salvar_relatorio_notificacoes_externas(canal=canal)}")
    if col_r2.button("Salvar manifesto de notificações externas"):
        st.success(f"Manifesto salvo em {salvar_manifesto_notificacoes_externas(canal=canal)}")

    st.download_button(
        "Baixar relatório de notificações externas (.md)",
        data=gerar_relatorio_notificacoes_externas_markdown(canal=canal),
        file_name="RELATORIO_NOTIFICACOES_EXTERNAS_VALORIS.md",
        mime="text/markdown",
    )


def executar_autoteste_notificacoes_externas_valoris() -> Dict[str, Any]:
    return {"ok": True, "versao": VERSAO_NOTIFICACOES_EXTERNAS_VALORIS, "metricas": calcular_metricas_notificacoes_externas()}
