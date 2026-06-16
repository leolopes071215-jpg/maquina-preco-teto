# integracao_motor_watchlist_valoris.py
# Valoris — Integração Motor + Watchlist v3.9.3
from __future__ import annotations

import csv
import json
from collections import deque
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st

VERSAO_INTEGRACAO_MOTOR_WATCHLIST_VALORIS = "3.9.3"
CAMINHO_ANALISES_MOTOR = Path("analises_motor_ativos_valoris.csv")
CAMINHO_DECISOES = Path("decisoes_integracao_motor_watchlist_valoris.csv")
CAMINHO_RELATORIO = Path("RELATORIO_INTEGRACAO_MOTOR_WATCHLIST_VALORIS.md")
CAMINHO_MANIFESTO = Path("manifesto_integracao_motor_watchlist_valoris.json")

CAMPOS_ANALISES_MOTOR = [
    "data_hora", "ticker", "nome_empresa", "setor", "preco_atual", "preco_teto",
    "margem_seguranca_atual", "score_qualidade", "score_risco", "score_valor",
    "score_final", "decisao", "nivel_conviccao", "modelo_preco_teto", "observacao",
]
CAMPOS_DECISOES = [
    "data_hora", "ticker", "empresa", "score_final", "decisao_motor",
    "acao_integracao", "status", "observacao",
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


def _garantir_csv(caminho: Path, campos: List[str]) -> None:
    if caminho.exists():
        return
    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        csv.DictWriter(arquivo, fieldnames=campos).writeheader()


def carregar_analises_motor(max_registros: int = 800) -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_ANALISES_MOTOR, CAMPOS_ANALISES_MOTOR)
    try:
        with CAMINHO_ANALISES_MOTOR.open("r", newline="", encoding="utf-8") as arquivo:
            return list(deque(csv.DictReader(arquivo), maxlen=max_registros))
    except Exception:
        return []


def carregar_watchlist_atual() -> List[Dict[str, str]]:
    try:
        from watchlist_fundadores_valoris import carregar_watchlist_fundadores
        return carregar_watchlist_fundadores()
    except Exception:
        return []


def tickers_na_watchlist() -> set[str]:
    return {_txt(item.get("ticker")).upper() for item in carregar_watchlist_atual() if _txt(item.get("ticker"))}


def calcular_metricas_integracao() -> Dict[str, Any]:
    analises = carregar_analises_motor()
    watchlist = carregar_watchlist_atual()
    tickers_watchlist = tickers_na_watchlist()
    tickers_analisados = {_txt(item.get("ticker")).upper() for item in analises if _txt(item.get("ticker"))}
    candidatos = [item for item in analises if _txt(item.get("ticker")).upper() and _txt(item.get("ticker")).upper() not in tickers_watchlist]
    compras = [item for item in analises if "COMPRA" in _txt(item.get("decisao")).upper()]
    monitorar = [item for item in analises if "MONITORAR" in _txt(item.get("decisao")).upper() or "AGUARDAR" in _txt(item.get("decisao")).upper()]
    scores = [_float(item.get("score_final"), 0.0) for item in analises]
    score_medio = round(sum(scores) / len(scores), 1) if scores else 0.0
    score_integracao = 25 + min(len(analises) * 5, 25) + min(len(watchlist) * 6, 24) + min(len(candidatos) * 4, 16)
    if score_medio >= 70:
        score_integracao += 10
    elif score_medio >= 55:
        score_integracao += 6
    score_integracao = max(0, min(100, int(score_integracao)))
    if len(analises) == 0:
        risco = "Alto"; decisao = "Sem análises para integrar"; proximo_passo = "Salvar pelo menos uma análise no Motor antes de enviar ativos para a Watchlist."
    elif len(candidatos) == 0:
        risco = "Baixo"; decisao = "Todas as análises relevantes já parecem estar cobertas ou precisam de revisão"; proximo_passo = "Revisar a Watchlist e avançar para Comparador ou Relatório Premium."
    elif score_integracao >= 75:
        risco = "Baixo"; decisao = "Integração pronta para uso recorrente"; proximo_passo = "Enviar os melhores candidatos para a Watchlist e acompanhar eventos."
    else:
        risco = "Médio"; decisao = "Integração funcional, mas ainda depende de mais análises"; proximo_passo = "Salvar mais análises e selecionar ativos de maior qualidade."
    return {
        "versao": VERSAO_INTEGRACAO_MOTOR_WATCHLIST_VALORIS,
        "gerado_em": _agora_iso(),
        "score_integracao": score_integracao,
        "analises_total": len(analises),
        "watchlist_total": len(watchlist),
        "tickers_analisados": len(tickers_analisados),
        "candidatos_integracao": len(candidatos),
        "compras_racionais": len(compras),
        "monitorar_ou_aguardar": len(monitorar),
        "score_medio_motor": score_medio,
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo_passo,
    }


def sugerir_prioridade(analise: Dict[str, str]) -> str:
    score = _float(analise.get("score_final"), 0.0)
    decisao = _txt(analise.get("decisao")).upper()
    if "COMPRA" in decisao and score >= 75:
        return "Alta"
    if score >= 65:
        return "Alta"
    if score >= 50:
        return "Média"
    return "Baixa"


def gerar_tese_sugerida(analise: Dict[str, str]) -> str:
    ticker = _txt(analise.get("ticker")).upper()
    empresa = _txt(analise.get("nome_empresa")) or ticker
    return (
        f"{empresa} ({ticker}) foi analisada pelo Motor Central da Valoris. "
        f"A decisão do motor foi '{_txt(analise.get('decisao'))}', com score final {_txt(analise.get('score_final'))}/100. "
        f"Qualidade: {_txt(analise.get('score_qualidade'))}/100; risco: {_txt(analise.get('score_risco'))}/100; valor/preço: {_txt(analise.get('score_valor'))}/100. "
        "A tese deve ser aprofundada com leitura de balanços, vantagem competitiva, riscos setoriais e validação das premissas do preço teto."
    )


def gerar_risco_sugerido(analise: Dict[str, str]) -> str:
    return (
        f"Risco principal: as premissas do modelo '{_txt(analise.get('modelo_preco_teto'))}' podem estar otimistas ou incompletas. "
        f"A margem de segurança atual informada foi {_txt(analise.get('margem_seguranca_atual'))}%. "
        f"A decisão '{_txt(analise.get('decisao'))}' deve ser revista caso preço, lucro, fluxo de caixa, dívida, governança ou cenário setorial mudem."
    )


def converter_analise_para_watchlist(analise: Dict[str, str], fundador_email: str, prioridade: str, tese_resumo: str, principal_risco: str, proximo_evento: str, data_revisao: str, observacoes: str) -> Dict[str, Any]:
    return {
        "fundador_email": fundador_email,
        "empresa": _txt(analise.get("nome_empresa")) or _txt(analise.get("ticker")).upper(),
        "ticker": _txt(analise.get("ticker")).upper(),
        "setor": _txt(analise.get("setor")),
        "preco_atual": _float(analise.get("preco_atual")),
        "preco_teto": _float(analise.get("preco_teto")),
        "status_oportunidade": "",
        "prioridade": prioridade,
        "tese_resumo": tese_resumo,
        "principal_risco": principal_risco,
        "proximo_evento": proximo_evento,
        "data_revisao": data_revisao,
        "observacoes": observacoes,
    }


def salvar_analise_na_watchlist(payload_watchlist: Dict[str, Any]) -> Dict[str, Any]:
    try:
        from watchlist_fundadores_valoris import salvar_item_watchlist
        registro = salvar_item_watchlist(payload_watchlist)
        return {"ok": True, "registro": registro}
    except Exception as erro:
        return {"ok": False, "erro": str(erro)}


def salvar_decisao_integracao(analise: Dict[str, str], acao_integracao: str, status: str, observacao: str = "") -> Path:
    _garantir_csv(CAMINHO_DECISOES, CAMPOS_DECISOES)
    with CAMINHO_DECISOES.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISOES)
        escritor.writerow({
            "data_hora": _agora_iso(),
            "ticker": _txt(analise.get("ticker")).upper(),
            "empresa": _txt(analise.get("nome_empresa")),
            "score_final": _txt(analise.get("score_final")),
            "decisao_motor": _txt(analise.get("decisao")),
            "acao_integracao": _txt(acao_integracao),
            "status": _txt(status),
            "observacao": _txt(observacao),
        })
    return CAMINHO_DECISOES


def carregar_decisoes_integracao(max_registros: int = 300) -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_DECISOES, CAMPOS_DECISOES)
    try:
        with CAMINHO_DECISOES.open("r", newline="", encoding="utf-8") as arquivo:
            return list(deque(csv.DictReader(arquivo), maxlen=max_registros))
    except Exception:
        return []


def gerar_relatorio_integracao_markdown() -> str:
    metricas = calcular_metricas_integracao()
    decisoes = carregar_decisoes_integracao()
    linhas_decisoes = "\n".join([
        f"- **{item.get('ticker', '')}** — {item.get('acao_integracao', '')} — {item.get('status', '')} — {item.get('data_hora', '')}"
        for item in reversed(decisoes[-20:])
    ]) or "- Nenhuma decisão de integração registrada."
    return f"""# Integração Motor + Watchlist — Valoris

Versão: {VERSAO_INTEGRACAO_MOTOR_WATCHLIST_VALORIS}  
Gerado em: {_agora_iso()}

## Diagnóstico

Score Integração: {metricas['score_integracao']}/100  
Análises no motor: {metricas['analises_total']}  
Itens na watchlist: {metricas['watchlist_total']}  
Candidatos para integração: {metricas['candidatos_integracao']}  
Score médio do motor: {metricas['score_medio_motor']}/100  

Risco: {metricas['risco']}  
Decisão: {metricas['decisao']}  
Próximo passo: {metricas['proximo_passo']}

## Decisões recentes

{linhas_decisoes}

## Leitura estratégica

Esta etapa transforma cálculo em acompanhamento. O usuário deixa de apenas calcular preço teto e passa a acompanhar uma tese ao longo do tempo.
"""


def salvar_relatorio_integracao_markdown() -> Path:
    CAMINHO_RELATORIO.write_text(gerar_relatorio_integracao_markdown(), encoding="utf-8")
    return CAMINHO_RELATORIO


def gerar_manifesto_integracao() -> Dict[str, Any]:
    return {
        "produto": "Valoris",
        "versao": VERSAO_INTEGRACAO_MOTOR_WATCHLIST_VALORIS,
        "modulo": "integracao_motor_watchlist_valoris",
        "data_hora": _agora_iso(),
        "metricas": calcular_metricas_integracao(),
        "principio": "transformar análise pontual em acompanhamento recorrente",
        "fluxo": "Motor → Histórico → Watchlist → Comparador → Relatório Premium",
    }


def salvar_manifesto_integracao() -> Path:
    CAMINHO_MANIFESTO.write_text(json.dumps(gerar_manifesto_integracao(), ensure_ascii=False, indent=2), encoding="utf-8")
    return CAMINHO_MANIFESTO


def renderizar_integracao_motor_watchlist_valoris() -> None:
    st.subheader("Integração Motor + Watchlist")
    st.caption("Envie análises salvas pelo Motor Central para a Watchlist, criando acompanhamento real por ativo.")
    analises = carregar_analises_motor()
    metricas = calcular_metricas_integracao()
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Score integração", f"{metricas['score_integracao']}/100")
    col2.metric("Análises", metricas["analises_total"])
    col3.metric("Watchlist", metricas["watchlist_total"])
    col4.metric("Candidatos", metricas["candidatos_integracao"])
    col5.metric("Score médio", f"{metricas['score_medio_motor']}/100")
    if metricas["score_integracao"] >= 75:
        st.success(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    elif metricas["analises_total"] > 0:
        st.warning(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    else:
        st.info(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    st.divider()
    if not analises:
        st.info("Ainda não há análises salvas. Vá até Motor Análise Ativos, rode uma análise e clique em Salvar análise.")
    else:
        tickers_existentes = tickers_na_watchlist()
        opcoes = [f"{item.get('data_hora', '')} | {item.get('ticker', '')} | {item.get('decisao', '')} | score {item.get('score_final', '')}" for item in reversed(analises)]
        escolha = st.selectbox("Análise para enviar à Watchlist", opcoes)
        analise = list(reversed(analises))[opcoes.index(escolha)]
        ticker = _txt(analise.get("ticker")).upper()
        ja_existe = ticker in tickers_existentes
        st.markdown("### Resumo da análise selecionada")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Ticker", ticker)
        col2.metric("Preço atual", _moeda(analise.get("preco_atual", 0)))
        col3.metric("Preço teto", _moeda(analise.get("preco_teto", 0)))
        col4.metric("Score final", f"{analise.get('score_final', '')}/100")
        st.markdown(f"**Decisão do motor:** {analise.get('decisao', '')}")
        if ja_existe:
            st.warning("Este ticker já aparece na Watchlist. Enviar novamente pode criar duplicidade.")
        st.divider()
        st.markdown("### Preparar item da Watchlist")
        col1, col2, col3 = st.columns(3)
        fundador_email = col1.text_input("E-mail do fundador", value="fundador@exemplo.com")
        prioridade = col2.selectbox("Prioridade", ["Alta", "Média", "Baixa"], index=["Alta", "Média", "Baixa"].index(sugerir_prioridade(analise)))
        data_revisao = col3.date_input("Data de revisão", value=datetime.now().date() + timedelta(days=30))
        proximo_evento = st.text_input("Próximo evento", value="Próximo resultado trimestral ou fato relevante")
        tese_resumo = st.text_area("Tese resumida", value=gerar_tese_sugerida(analise), height=120)
        principal_risco = st.text_area("Principal risco", value=gerar_risco_sugerido(analise), height=110)
        observacoes = st.text_area("Observações", value=f"Item criado a partir da análise do motor em {analise.get('data_hora', '')}.", height=90)
        payload = converter_analise_para_watchlist(analise, fundador_email, prioridade, tese_resumo, principal_risco, proximo_evento, str(data_revisao), observacoes)
        with st.expander("Ver payload que será enviado para a Watchlist", expanded=False):
            st.json(payload)
        col_a, col_b = st.columns(2)
        if col_a.button("Enviar para Watchlist"):
            retorno = salvar_analise_na_watchlist(payload)
            if retorno.get("ok"):
                salvar_decisao_integracao(analise, "enviar_para_watchlist", "ok", f"Registro criado na watchlist para {ticker}.")
                st.success(f"{ticker} enviado para a Watchlist.")
                st.json(retorno.get("registro", {}))
                st.rerun()
            else:
                salvar_decisao_integracao(analise, "enviar_para_watchlist", "erro", retorno.get("erro", ""))
                st.error(retorno.get("erro", "Erro ao enviar para Watchlist."))
        if col_b.button("Registrar como não enviar agora"):
            salvar_decisao_integracao(analise, "nao_enviar_agora", "registrado", "Decisão manual: análise não enviada para watchlist neste momento.")
            st.warning("Decisão registrada.")
            st.rerun()
    st.divider()
    st.markdown("### Ações e relatórios")
    col1, col2 = st.columns(2)
    if col1.button("Salvar relatório da integração"):
        st.success(f"Relatório salvo em {salvar_relatorio_integracao_markdown()}")
    if col2.button("Salvar manifesto da integração"):
        st.success(f"Manifesto salvo em {salvar_manifesto_integracao()}")
    st.download_button("Baixar relatório da integração (.md)", data=gerar_relatorio_integracao_markdown(), file_name="RELATORIO_INTEGRACAO_MOTOR_WATCHLIST_VALORIS.md", mime="text/markdown")
    st.markdown("### Decisões de integração")
    decisoes = carregar_decisoes_integracao()
    if decisoes:
        st.dataframe(decisoes, use_container_width=True, hide_index=True)
    else:
        st.info("Ainda não há decisões de integração registradas.")


def executar_autoteste_integracao_motor_watchlist_valoris() -> Dict[str, Any]:
    return {"ok": True, "versao": VERSAO_INTEGRACAO_MOTOR_WATCHLIST_VALORIS, "metricas": calcular_metricas_integracao()}
