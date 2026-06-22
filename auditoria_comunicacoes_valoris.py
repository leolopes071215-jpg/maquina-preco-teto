# auditoria_comunicacoes_valoris.py
# Valoris — Auditoria de Comunicações v3.12.3
# ------------------------------------------------------------
# Objetivo:
# - Consolidar rascunhos, aprovações, exportações e envios manuais.
# - Mostrar rastreabilidade completa por ID de rascunho.
# - Detectar inconsistências antes de qualquer automação externa real.
# - Registrar revisão de auditoria sem alterar dados operacionais principais.

from __future__ import annotations

import csv
import json
from collections import Counter, deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st


VERSAO_AUDITORIA_COMUNICACOES_VALORIS = "3.12.3"

CAMINHO_RASCUNHOS = Path("rascunhos_notificacoes_externas_valoris.csv")
CAMINHO_APROVACOES = Path("aprovacoes_notificacoes_externas_valoris.csv")
CAMINHO_EXPORTACOES = Path("exportacoes_notificacoes_valoris.csv")
CAMINHO_EXECUCOES = Path("execucoes_envio_manual_notificacoes_valoris.csv")

CAMINHO_REVISOES = Path("revisoes_auditoria_comunicacoes_valoris.csv")
CAMINHO_RELATORIO = Path("RELATORIO_AUDITORIA_COMUNICACOES_VALORIS.md")
CAMINHO_MANIFESTO = Path("manifesto_auditoria_comunicacoes_valoris.json")

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

CAMPOS_APROVACOES = [
    "data_hora",
    "id_rascunho",
    "canal",
    "ticker",
    "empresa",
    "tipo",
    "severidade",
    "decisao_aprovacao",
    "responsavel",
    "motivo",
    "proxima_acao",
]

CAMPOS_EXPORTACOES = [
    "data_hora",
    "id_rascunho",
    "canal",
    "ticker",
    "empresa",
    "tipo",
    "severidade",
    "arquivo_csv",
    "arquivo_md",
    "status_exportacao",
    "responsavel",
    "observacao",
]

CAMPOS_EXECUCOES = [
    "data_hora",
    "id_rascunho",
    "canal",
    "ticker",
    "empresa",
    "tipo",
    "severidade",
    "status_envio",
    "responsavel",
    "destino_utilizado",
    "comprovante",
    "observacao",
]

CAMPOS_REVISOES = [
    "data_hora",
    "score_auditoria",
    "status_auditoria",
    "responsavel",
    "decisao",
    "observacao",
]


def _agora_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat(sep=" ")


def _txt(valor: Any) -> str:
    return "" if valor is None else str(valor).strip()


def _safe(valor: Any) -> str:
    texto = _txt(valor)
    seguro = "".join(ch if ch.isalnum() else "_" for ch in texto)
    return "_".join([p for p in seguro.split("_") if p])[:160] or "sem_id"


def _float(valor: Any, padrao: float = 0.0) -> float:
    try:
        if valor is None:
            return padrao
        if isinstance(valor, str):
            valor = valor.replace(",", ".").strip()
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


def _ler_csv(caminho: Path, campos: List[str], max_registros: int = 3000) -> List[Dict[str, str]]:
    _garantir_csv(caminho, campos)

    try:
        with caminho.open("r", newline="", encoding="utf-8") as arquivo:
            leitor = csv.DictReader(arquivo)
            return list(deque(leitor, maxlen=max_registros))
    except Exception:
        return []


def _id_rascunho(item: Dict[str, Any]) -> str:
    bruto = "|".join(
        [
            _txt(item.get("data_hora")),
            _txt(item.get("canal")),
            _txt(item.get("ticker")).upper(),
            _txt(item.get("tipo")),
            _txt(item.get("assunto")),
        ]
    )
    return _safe(bruto)


def carregar_rascunhos() -> List[Dict[str, str]]:
    return _ler_csv(CAMINHO_RASCUNHOS, CAMPOS_RASCUNHOS)


def carregar_aprovacoes() -> List[Dict[str, str]]:
    return _ler_csv(CAMINHO_APROVACOES, CAMPOS_APROVACOES)


def carregar_exportacoes() -> List[Dict[str, str]]:
    return _ler_csv(CAMINHO_EXPORTACOES, CAMPOS_EXPORTACOES)


def carregar_execucoes() -> List[Dict[str, str]]:
    return _ler_csv(CAMINHO_EXECUCOES, CAMPOS_EXECUCOES)


def carregar_revisoes() -> List[Dict[str, str]]:
    return _ler_csv(CAMINHO_REVISOES, CAMPOS_REVISOES, max_registros=1000)


def _ultima_por_id(itens: List[Dict[str, str]], campo_id: str = "id_rascunho") -> Dict[str, Dict[str, str]]:
    mapa = {}

    for item in itens:
        rid = _txt(item.get(campo_id))
        if rid:
            mapa[rid] = item

    return mapa


def _aprovacao_valida(item: Dict[str, str]) -> bool:
    decisao = _txt(item.get("decisao_aprovacao")).lower()
    return "aprovado" in decisao


def _envio_concluido(item: Dict[str, str]) -> bool:
    status = _txt(item.get("status_envio")).lower()
    return "enviado manualmente" in status


def gerar_trilha_comunicacoes() -> List[Dict[str, Any]]:
    rascunhos = carregar_rascunhos()
    aprovacoes = carregar_aprovacoes()
    exportacoes = carregar_exportacoes()
    execucoes = carregar_execucoes()

    mapa_aprov = _ultima_por_id(aprovacoes)
    mapa_export = _ultima_por_id(exportacoes)
    mapa_exec = _ultima_por_id(execucoes)

    ids = set()

    for rascunho in rascunhos:
        ids.add(_id_rascunho(rascunho))

    ids.update(mapa_aprov.keys())
    ids.update(mapa_export.keys())
    ids.update(mapa_exec.keys())

    rascunho_por_id = {_id_rascunho(item): item for item in rascunhos}

    trilha = []

    for rid in sorted(ids):
        rascunho = rascunho_por_id.get(rid, {})
        aprovacao = mapa_aprov.get(rid, {})
        exportacao = mapa_export.get(rid, {})
        execucao = mapa_exec.get(rid, {})

        canal = _txt(rascunho.get("canal")) or _txt(aprovacao.get("canal")) or _txt(exportacao.get("canal")) or _txt(execucao.get("canal"))
        ticker = _txt(rascunho.get("ticker")).upper() or _txt(aprovacao.get("ticker")).upper() or _txt(exportacao.get("ticker")).upper() or _txt(execucao.get("ticker")).upper()
        empresa = _txt(rascunho.get("empresa")) or _txt(aprovacao.get("empresa")) or _txt(exportacao.get("empresa")) or _txt(execucao.get("empresa"))
        tipo = _txt(rascunho.get("tipo")) or _txt(aprovacao.get("tipo")) or _txt(exportacao.get("tipo")) or _txt(execucao.get("tipo"))
        severidade = _txt(rascunho.get("severidade")) or _txt(aprovacao.get("severidade")) or _txt(exportacao.get("severidade")) or _txt(execucao.get("severidade"))

        tem_rascunho = bool(rascunho)
        tem_aprovacao = bool(aprovacao)
        aprovado = tem_aprovacao and _aprovacao_valida(aprovacao)
        tem_exportacao = bool(exportacao)
        tem_execucao = bool(execucao)
        enviado = tem_execucao and _envio_concluido(execucao)

        inconsistencias = []

        if not tem_rascunho:
            inconsistencias.append("Sem rascunho original")

        if tem_exportacao and not aprovado:
            inconsistencias.append("Exportado sem aprovação válida")

        if tem_execucao and not tem_exportacao:
            inconsistencias.append("Execução registrada sem exportação")

        if enviado and not aprovado:
            inconsistencias.append("Envio manual sem aprovação válida")

        if aprovado and not tem_exportacao:
            inconsistencias.append("Aprovado mas não exportado")

        if tem_exportacao and not tem_execucao:
            inconsistencias.append("Exportado mas sem execução registrada")

        if not canal:
            inconsistencias.append("Canal ausente")

        if not ticker:
            inconsistencias.append("Ticker ausente")

        if enviado and not _txt(execucao.get("responsavel")):
            inconsistencias.append("Envio sem responsável")

        if enviado and not _txt(execucao.get("destino_utilizado")):
            inconsistencias.append("Envio sem destino registrado")

        if inconsistencias:
            status_auditoria = "Atenção"
        elif enviado:
            status_auditoria = "Completo"
        elif tem_exportacao:
            status_auditoria = "Exportado"
        elif aprovado:
            status_auditoria = "Aprovado"
        elif tem_rascunho:
            status_auditoria = "Rascunho"
        else:
            status_auditoria = "Indefinido"

        trilha.append(
            {
                "id_rascunho": rid,
                "canal": canal,
                "ticker": ticker,
                "empresa": empresa,
                "tipo": tipo,
                "severidade": severidade,
                "tem_rascunho": "Sim" if tem_rascunho else "Não",
                "tem_aprovacao": "Sim" if tem_aprovacao else "Não",
                "aprovado": "Sim" if aprovado else "Não",
                "tem_exportacao": "Sim" if tem_exportacao else "Não",
                "tem_execucao": "Sim" if tem_execucao else "Não",
                "enviado": "Sim" if enviado else "Não",
                "status_envio": _txt(execucao.get("status_envio")),
                "status_auditoria": status_auditoria,
                "inconsistencias": "; ".join(inconsistencias),
                "responsavel_aprovacao": _txt(aprovacao.get("responsavel")),
                "responsavel_exportacao": _txt(exportacao.get("responsavel")),
                "responsavel_envio": _txt(execucao.get("responsavel")),
                "data_rascunho": _txt(rascunho.get("data_hora")),
                "data_aprovacao": _txt(aprovacao.get("data_hora")),
                "data_exportacao": _txt(exportacao.get("data_hora")),
                "data_execucao": _txt(execucao.get("data_hora")),
            }
        )

    ordem_status = {
        "Atenção": 1,
        "Exportado": 2,
        "Aprovado": 3,
        "Rascunho": 4,
        "Completo": 5,
        "Indefinido": 9,
    }

    trilha.sort(
        key=lambda item: (
            ordem_status.get(item.get("status_auditoria"), 9),
            item.get("canal", ""),
            item.get("ticker", ""),
        )
    )

    return trilha


def calcular_metricas_auditoria() -> Dict[str, Any]:
    trilha = gerar_trilha_comunicacoes()

    total = len(trilha)
    completos = len([i for i in trilha if i.get("status_auditoria") == "Completo"])
    atencao = len([i for i in trilha if i.get("status_auditoria") == "Atenção"])
    rascunhos = len([i for i in trilha if i.get("tem_rascunho") == "Sim"])
    aprovados = len([i for i in trilha if i.get("aprovado") == "Sim"])
    exportados = len([i for i in trilha if i.get("tem_exportacao") == "Sim"])
    enviados = len([i for i in trilha if i.get("enviado") == "Sim"])

    por_status = Counter(i.get("status_auditoria", "Indefinido") for i in trilha)
    por_canal = Counter(i.get("canal", "Sem canal") or "Sem canal" for i in trilha)
    por_severidade = Counter(i.get("severidade", "Sem severidade") or "Sem severidade" for i in trilha)

    taxa_execucao = 0.0
    if exportados:
        taxa_execucao = round((enviados / exportados) * 100, 1)

    taxa_aprovacao = 0.0
    if rascunhos:
        taxa_aprovacao = round((aprovados / rascunhos) * 100, 1)

    score = 55

    if total:
        score += 15

    if completos:
        score += 15

    if atencao:
        score -= min(atencao * 12, 45)

    if exportados and enviados == exportados:
        score += 10

    if aprovados and exportados > aprovados:
        score -= 15

    score = max(0, min(100, int(score)))

    if total == 0:
        risco = "Baixo"
        decisao = "Sem comunicações para auditar"
        proximo = "Criar rascunhos, aprovar, exportar e registrar envios manuais."
    elif atencao:
        risco = "Médio"
        decisao = "Há inconsistências na trilha de comunicação"
        proximo = "Corrigir itens em atenção antes de automatizar qualquer envio."
    elif enviados and enviados == exportados and exportados == aprovados:
        risco = "Baixo"
        decisao = "Trilha de comunicação completa e auditável"
        proximo = "Preparar painel de resultados ou futura automação controlada."
    elif exportados and not enviados:
        risco = "Baixo/Médio"
        decisao = "Há exportações sem execução manual registrada"
        proximo = "Registrar execução manual ou reagendar itens exportados."
    else:
        risco = "Baixo/Médio"
        decisao = "Auditoria funcional com ciclo parcialmente completo"
        proximo = "Completar aprovações, exportações e execuções pendentes."

    return {
        "versao": VERSAO_AUDITORIA_COMUNICACOES_VALORIS,
        "gerado_em": _agora_iso(),
        "score_auditoria": score,
        "itens_auditados": total,
        "completos": completos,
        "atencao": atencao,
        "rascunhos": rascunhos,
        "aprovados": aprovados,
        "exportados": exportados,
        "enviados": enviados,
        "taxa_aprovacao": taxa_aprovacao,
        "taxa_execucao": taxa_execucao,
        "por_status": dict(por_status),
        "por_canal": dict(por_canal),
        "por_severidade": dict(por_severidade),
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo,
    }


def salvar_revisao_auditoria(status_auditoria: str, responsavel: str, decisao: str, observacao: str = "") -> Path:
    _garantir_csv(CAMINHO_REVISOES, CAMPOS_REVISOES)
    metricas = calcular_metricas_auditoria()

    with CAMINHO_REVISOES.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_REVISOES)
        escritor.writerow(
            {
                "data_hora": _agora_iso(),
                "score_auditoria": metricas["score_auditoria"],
                "status_auditoria": _txt(status_auditoria),
                "responsavel": _txt(responsavel),
                "decisao": _txt(decisao),
                "observacao": _txt(observacao),
            }
        )

    return CAMINHO_REVISOES


def gerar_relatorio_auditoria_markdown() -> str:
    metricas = calcular_metricas_auditoria()
    trilha = gerar_trilha_comunicacoes()

    linhas = "\n".join(
        [
            f"- **{item['status_auditoria']} — {item['canal']} — {item['ticker']}**: rascunho={item['tem_rascunho']}, aprovado={item['aprovado']}, exportado={item['tem_exportacao']}, enviado={item['enviado']} | inconsistências: {item['inconsistencias'] or 'nenhuma'}"
            for item in trilha[:100]
        ]
    ) or "- Nenhuma comunicação auditada."

    return f"""# Auditoria de Comunicações — Valoris

Versão: {VERSAO_AUDITORIA_COMUNICACOES_VALORIS}  
Gerado em: {_agora_iso()}

## Diagnóstico

Score auditoria: {metricas['score_auditoria']}/100  
Itens auditados: {metricas['itens_auditados']}  
Completos: {metricas['completos']}  
Em atenção: {metricas['atencao']}  
Rascunhos: {metricas['rascunhos']}  
Aprovados: {metricas['aprovados']}  
Exportados: {metricas['exportados']}  
Enviados: {metricas['enviados']}  
Taxa de aprovação: {metricas['taxa_aprovacao']}%  
Taxa de execução: {metricas['taxa_execucao']}%  

Risco: {metricas['risco']}  
Decisão: {metricas['decisao']}  
Próximo passo: {metricas['proximo_passo']}

## Trilha auditada

{linhas}

## Estratégia

Esta versão consolida a rastreabilidade completa da comunicação. Antes de qualquer envio automático real, o Valoris precisa provar o ciclo: rascunho, aprovação, exportação, execução e auditoria.
"""


def salvar_relatorio_auditoria() -> Path:
    CAMINHO_RELATORIO.write_text(gerar_relatorio_auditoria_markdown(), encoding="utf-8")
    return CAMINHO_RELATORIO


def gerar_manifesto_auditoria() -> Dict[str, Any]:
    return {
        "produto": "Valoris",
        "versao": VERSAO_AUDITORIA_COMUNICACOES_VALORIS,
        "modulo": "auditoria_comunicacoes_valoris",
        "data_hora": _agora_iso(),
        "metricas": calcular_metricas_auditoria(),
        "trilha": gerar_trilha_comunicacoes(),
        "principio": "sem rastreabilidade, não existe automação confiável",
        "proxima_etapa": "resultados de comunicação ou automação externa controlada",
    }


def salvar_manifesto_auditoria() -> Path:
    CAMINHO_MANIFESTO.write_text(
        json.dumps(gerar_manifesto_auditoria(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return CAMINHO_MANIFESTO


def renderizar_auditoria_comunicacoes_valoris() -> None:
    st.subheader("Auditoria de Comunicações")
    st.caption("Rastreia rascunhos, aprovações, exportações e envios manuais antes de qualquer automação real.")

    metricas = calcular_metricas_auditoria()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Score auditoria", f"{metricas['score_auditoria']}/100")
    col2.metric("Auditados", metricas["itens_auditados"])
    col3.metric("Completos", metricas["completos"])
    col4.metric("Atenção", metricas["atencao"])
    col5.metric("Execução", f"{metricas['taxa_execucao']}%")

    if metricas["risco"] == "Médio":
        st.warning(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    elif metricas["risco"] == "Baixo":
        st.success(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    else:
        st.info(f"{metricas['decisao']} — {metricas['proximo_passo']}")

    st.divider()

    trilha = gerar_trilha_comunicacoes()

    st.markdown("### Trilha de comunicação")

    col_f1, col_f2, col_f3 = st.columns(3)
    status_opcoes = ["Todos"] + sorted({item.get("status_auditoria", "") for item in trilha if item.get("status_auditoria")})
    canais = ["Todos"] + sorted({item.get("canal", "") for item in trilha if item.get("canal")})
    filtro_status = col_f1.selectbox("Status auditoria", status_opcoes)
    filtro_canal = col_f2.selectbox("Canal", canais)
    filtro_ticker = col_f3.text_input("Ticker", value="")

    filtrados = []

    for item in trilha:
        if filtro_status != "Todos" and item.get("status_auditoria") != filtro_status:
            continue

        if filtro_canal != "Todos" and item.get("canal") != filtro_canal:
            continue

        if filtro_ticker.strip() and filtro_ticker.strip().upper() not in item.get("ticker", ""):
            continue

        filtrados.append(item)

    st.dataframe(
        [
            {
                "status": item.get("status_auditoria"),
                "canal": item.get("canal"),
                "ticker": item.get("ticker"),
                "empresa": item.get("empresa"),
                "rascunho": item.get("tem_rascunho"),
                "aprovado": item.get("aprovado"),
                "exportado": item.get("tem_exportacao"),
                "enviado": item.get("enviado"),
                "inconsistências": item.get("inconsistencias"),
                "responsável envio": item.get("responsavel_envio"),
            }
            for item in filtrados
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Registrar revisão de auditoria")

    col_a, col_b = st.columns(2)
    status_revisao = col_a.selectbox("Status da auditoria", ["Auditado", "Com pendências", "Aprovado para próxima etapa", "Bloquear automação externa"])
    responsavel = col_b.text_input("Responsável", value="Fundador")

    decisao = st.text_input("Decisão", value=metricas["decisao"])
    observacao = st.text_area(
        "Observação",
        value=f"Revisão registrada na Auditoria de Comunicações v{VERSAO_AUDITORIA_COMUNICACOES_VALORIS}.",
        height=90,
    )

    if st.button("Salvar revisão de auditoria"):
        salvar_revisao_auditoria(
            status_auditoria=status_revisao,
            responsavel=responsavel,
            decisao=decisao,
            observacao=observacao,
        )
        st.success("Revisão de auditoria registrada.")
        st.rerun()

    revisoes = carregar_revisoes()
    if revisoes:
        st.markdown("### Revisões registradas")
        st.dataframe(revisoes, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Relatórios")

    col_r1, col_r2 = st.columns(2)

    if col_r1.button("Salvar relatório de auditoria"):
        caminho = salvar_relatorio_auditoria()
        st.success(f"Relatório salvo em {caminho}")

    if col_r2.button("Salvar manifesto de auditoria"):
        caminho = salvar_manifesto_auditoria()
        st.success(f"Manifesto salvo em {caminho}")

    st.download_button(
        "Baixar relatório de auditoria (.md)",
        data=gerar_relatorio_auditoria_markdown(),
        file_name="RELATORIO_AUDITORIA_COMUNICACOES_VALORIS.md",
        mime="text/markdown",
    )


def executar_autoteste_auditoria_comunicacoes_valoris() -> Dict[str, Any]:
    return {
        "ok": True,
        "versao": VERSAO_AUDITORIA_COMUNICACOES_VALORIS,
        "metricas": calcular_metricas_auditoria(),
    }
