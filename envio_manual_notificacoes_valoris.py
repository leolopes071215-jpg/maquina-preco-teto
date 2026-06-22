# envio_manual_notificacoes_valoris.py
# Valoris — Envio Manual Assistido v3.12.2
# ------------------------------------------------------------
# Objetivo:
# - Criar a etapa posterior à exportação segura.
# - Ajudar o usuário a executar envios manualmente, sem automação real.
# - Ler exportações geradas em Exportação Notificações.
# - Registrar status: enviado manualmente, não enviado, reagendado ou aguardando.
# - Manter trilha: rascunho -> aprovação -> exportação -> execução manual.

from __future__ import annotations

import csv
import json
from collections import Counter, deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st


VERSAO_ENVIO_MANUAL_VALORIS = "3.12.2"

CAMINHO_EXPORTACOES = Path("exportacoes_notificacoes_valoris.csv")
CAMINHO_EXECUCOES = Path("execucoes_envio_manual_notificacoes_valoris.csv")
CAMINHO_RELATORIO = Path("RELATORIO_ENVIO_MANUAL_NOTIFICACOES_VALORIS.md")
CAMINHO_MANIFESTO = Path("manifesto_envio_manual_notificacoes_valoris.json")

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


def _agora_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat(sep=" ")


def _txt(valor: Any) -> str:
    return "" if valor is None else str(valor).strip()


def _garantir_csv(caminho: Path, campos: List[str]) -> None:
    if caminho.exists():
        return

    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()


def carregar_exportacoes(max_registros: int = 2000) -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_EXPORTACOES, CAMPOS_EXPORTACOES)

    try:
        with CAMINHO_EXPORTACOES.open("r", newline="", encoding="utf-8") as arquivo:
            leitor = csv.DictReader(arquivo)
            return list(deque(leitor, maxlen=max_registros))
    except Exception:
        return []


def carregar_execucoes(max_registros: int = 2000) -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_EXECUCOES, CAMPOS_EXECUCOES)

    try:
        with CAMINHO_EXECUCOES.open("r", newline="", encoding="utf-8") as arquivo:
            leitor = csv.DictReader(arquivo)
            return list(deque(leitor, maxlen=max_registros))
    except Exception:
        return []


def mapa_execucoes() -> Dict[str, Dict[str, str]]:
    mapa = {}

    for item in carregar_execucoes():
        rid = _txt(item.get("id_rascunho"))
        if rid:
            mapa[rid] = item

    return mapa


def carregar_preview_markdown(caminho: str, limite: int = 3000) -> str:
    path = Path(_txt(caminho))

    if not path.exists() or not path.is_file():
        return "Arquivo Markdown não encontrado no caminho registrado."

    try:
        texto = path.read_text(encoding="utf-8", errors="replace")
        return texto[:limite] + ("\n\n..." if len(texto) > limite else "")
    except Exception as exc:
        return f"Não foi possível ler o arquivo: {exc}"


def gerar_fila_envio_manual() -> List[Dict[str, Any]]:
    exportacoes = carregar_exportacoes()
    execucoes = mapa_execucoes()
    fila = []

    for item in exportacoes:
        rid = _txt(item.get("id_rascunho"))

        if not rid:
            continue

        execucao = execucoes.get(rid, {})
        status_envio = _txt(execucao.get("status_envio")) or "Pendente"

        fila.append(
            {
                "id_rascunho": rid,
                "canal": _txt(item.get("canal")),
                "ticker": _txt(item.get("ticker")).upper(),
                "empresa": _txt(item.get("empresa")),
                "tipo": _txt(item.get("tipo")),
                "severidade": _txt(item.get("severidade")),
                "arquivo_csv": _txt(item.get("arquivo_csv")),
                "arquivo_md": _txt(item.get("arquivo_md")),
                "status_exportacao": _txt(item.get("status_exportacao")),
                "responsavel_exportacao": _txt(item.get("responsavel")),
                "status_envio": status_envio,
                "responsavel_envio": _txt(execucao.get("responsavel")),
                "destino_utilizado": _txt(execucao.get("destino_utilizado")),
                "comprovante": _txt(execucao.get("comprovante")),
                "observacao_envio": _txt(execucao.get("observacao")),
            }
        )

    fila.sort(
        key=lambda item: (
            0 if item.get("status_envio") == "Pendente" else 1,
            item.get("canal", ""),
            item.get("ticker", ""),
            item.get("severidade", ""),
        )
    )

    return fila


def salvar_execucao_envio(item: Dict[str, Any], status_envio: str, responsavel: str, destino: str, comprovante: str, observacao: str = "") -> Path:
    _garantir_csv(CAMINHO_EXECUCOES, CAMPOS_EXECUCOES)

    with CAMINHO_EXECUCOES.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_EXECUCOES)
        escritor.writerow(
            {
                "data_hora": _agora_iso(),
                "id_rascunho": _txt(item.get("id_rascunho")),
                "canal": _txt(item.get("canal")),
                "ticker": _txt(item.get("ticker")).upper(),
                "empresa": _txt(item.get("empresa")),
                "tipo": _txt(item.get("tipo")),
                "severidade": _txt(item.get("severidade")),
                "status_envio": _txt(status_envio),
                "responsavel": _txt(responsavel),
                "destino_utilizado": _txt(destino),
                "comprovante": _txt(comprovante),
                "observacao": _txt(observacao),
            }
        )

    return CAMINHO_EXECUCOES


def calcular_metricas_envio_manual() -> Dict[str, Any]:
    fila = gerar_fila_envio_manual()
    execucoes = carregar_execucoes()

    contador_status = Counter(_txt(item.get("status_envio")) or "Pendente" for item in fila)
    contador_canal = Counter(_txt(item.get("canal")) or "Sem canal" for item in fila)

    pendentes = contador_status.get("Pendente", 0)
    enviados = contador_status.get("Enviado manualmente", 0)
    reagendados = contador_status.get("Reagendado", 0)
    bloqueados = contador_status.get("Não enviado", 0)

    score = 55

    if fila:
        score += 15

    if enviados:
        score += 15

    if pendentes:
        score -= min(pendentes * 5, 25)

    if bloqueados:
        score -= min(bloqueados * 4, 15)

    score = max(0, min(100, int(score)))

    if not fila:
        risco = "Baixo"
        decisao = "Sem exportações para envio manual"
        proximo = "Exportar rascunhos aprovados antes de executar envios."
    elif pendentes:
        risco = "Baixo/Médio"
        decisao = "Há notificações exportadas aguardando execução manual"
        proximo = "Enviar manualmente, reagendar ou bloquear cada item exportado."
    elif enviados:
        risco = "Baixo"
        decisao = "Envios manuais registrados"
        proximo = "Conferir resultados e preparar auditoria de comunicação."
    else:
        risco = "Baixo"
        decisao = "Fila de envio manual sob controle"
        proximo = "Manter registro de execução antes de qualquer automação real."

    return {
        "versao": VERSAO_ENVIO_MANUAL_VALORIS,
        "gerado_em": _agora_iso(),
        "score_envio_manual": score,
        "exportados": len(fila),
        "pendentes": pendentes,
        "enviados": enviados,
        "reagendados": reagendados,
        "nao_enviados": bloqueados,
        "execucoes_registradas": len(execucoes),
        "por_status": dict(contador_status),
        "por_canal": dict(contador_canal),
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo,
    }


def gerar_relatorio_envio_manual_markdown() -> str:
    metricas = calcular_metricas_envio_manual()
    fila = gerar_fila_envio_manual()

    linhas = "\n".join(
        [
            f"- **{item['canal']} — {item['ticker']} — {item['status_envio']}**: {item['tipo']} | arquivo: {item['arquivo_md']}"
            for item in fila[:80]
        ]
    ) or "- Nenhum item na fila de envio manual."

    return f"""# Envio Manual Assistido — Valoris

Versão: {VERSAO_ENVIO_MANUAL_VALORIS}  
Gerado em: {_agora_iso()}

## Diagnóstico

Score envio manual: {metricas['score_envio_manual']}/100  
Exportados: {metricas['exportados']}  
Pendentes: {metricas['pendentes']}  
Enviados: {metricas['enviados']}  
Reagendados: {metricas['reagendados']}  
Não enviados: {metricas['nao_enviados']}  
Execuções registradas: {metricas['execucoes_registradas']}  

Risco: {metricas['risco']}  
Decisão: {metricas['decisao']}  
Próximo passo: {metricas['proximo_passo']}

## Fila

{linhas}

## Estratégia

Esta versão cria execução manual assistida. O Valoris continua sem enviar mensagens automaticamente; ele organiza, orienta e registra a ação humana.
"""


def salvar_relatorio_envio_manual() -> Path:
    CAMINHO_RELATORIO.write_text(gerar_relatorio_envio_manual_markdown(), encoding="utf-8")
    return CAMINHO_RELATORIO


def gerar_manifesto_envio_manual() -> Dict[str, Any]:
    return {
        "produto": "Valoris",
        "versao": VERSAO_ENVIO_MANUAL_VALORIS,
        "modulo": "envio_manual_notificacoes_valoris",
        "data_hora": _agora_iso(),
        "metricas": calcular_metricas_envio_manual(),
        "fila_envio_manual": gerar_fila_envio_manual(),
        "principio": "antes de automatizar envio, o processo manual precisa ser executável e auditável",
        "proxima_etapa": "auditoria de comunicações e resultados",
    }


def salvar_manifesto_envio_manual() -> Path:
    CAMINHO_MANIFESTO.write_text(
        json.dumps(gerar_manifesto_envio_manual(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return CAMINHO_MANIFESTO


def renderizar_envio_manual_notificacoes_valoris() -> None:
    st.subheader("Envio Manual Assistido")
    st.caption("Executa a etapa manual após a exportação segura. Nenhuma mensagem é enviada automaticamente.")

    metricas = calcular_metricas_envio_manual()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Score envio", f"{metricas['score_envio_manual']}/100")
    col2.metric("Exportados", metricas["exportados"])
    col3.metric("Pendentes", metricas["pendentes"])
    col4.metric("Enviados", metricas["enviados"])
    col5.metric("Execuções", metricas["execucoes_registradas"])

    if metricas["risco"] == "Baixo":
        st.success(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    else:
        st.info(f"{metricas['decisao']} — {metricas['proximo_passo']}")

    st.divider()

    fila = gerar_fila_envio_manual()

    col_f1, col_f2, col_f3 = st.columns(3)
    canais = ["Todos"] + sorted({item.get("canal", "") for item in fila if item.get("canal")})
    status_opcoes = ["Todos"] + sorted({item.get("status_envio", "") for item in fila if item.get("status_envio")})
    filtro_canal = col_f1.selectbox("Canal", canais)
    filtro_status = col_f2.selectbox("Status", status_opcoes)
    filtro_ticker = col_f3.text_input("Ticker", value="")

    filtrados = []
    for item in fila:
        if filtro_canal != "Todos" and item.get("canal") != filtro_canal:
            continue
        if filtro_status != "Todos" and item.get("status_envio") != filtro_status:
            continue
        if filtro_ticker.strip() and filtro_ticker.strip().upper() not in item.get("ticker", ""):
            continue
        filtrados.append(item)

    st.markdown("### Fila de envio manual")
    st.dataframe(
        [
            {
                "status": item.get("status_envio"),
                "canal": item.get("canal"),
                "ticker": item.get("ticker"),
                "empresa": item.get("empresa"),
                "tipo": item.get("tipo"),
                "severidade": item.get("severidade"),
                "arquivo md": item.get("arquivo_md"),
                "responsável": item.get("responsavel_envio"),
            }
            for item in filtrados
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Executar e registrar envio manual")

    if filtrados:
        opcoes = [
            f"{item['status_envio']} | {item['canal']} | {item['ticker']} | {item['tipo']}"
            for item in filtrados
        ]

        escolha = st.selectbox("Item exportado", opcoes)
        item = filtrados[opcoes.index(escolha)]

        st.markdown("#### Preview do pacote Markdown")
        st.text_area("Conteúdo", value=carregar_preview_markdown(item.get("arquivo_md", "")), height=260, disabled=True)

        col_a, col_b = st.columns(2)
        status_envio = col_a.selectbox("Status do envio", ["Enviado manualmente", "Pendente", "Reagendado", "Não enviado"])
        responsavel = col_b.text_input("Responsável", value="Fundador")

        destino = st.text_input("Destino utilizado", value=item.get("canal", ""))
        comprovante = st.text_input("Comprovante / referência", value="")
        observacao = st.text_area(
            "Observação",
            value=f"Execução registrada no Envio Manual Assistido v{VERSAO_ENVIO_MANUAL_VALORIS}. Nenhum envio automático realizado pelo app.",
            height=90,
        )

        if st.button("Salvar execução manual"):
            salvar_execucao_envio(
                item,
                status_envio=status_envio,
                responsavel=responsavel,
                destino=destino,
                comprovante=comprovante,
                observacao=observacao,
            )
            st.success("Execução manual registrada.")
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
    if col_r1.button("Salvar relatório de envio manual"):
        caminho = salvar_relatorio_envio_manual()
        st.success(f"Relatório salvo em {caminho}")

    if col_r2.button("Salvar manifesto de envio manual"):
        caminho = salvar_manifesto_envio_manual()
        st.success(f"Manifesto salvo em {caminho}")

    st.download_button(
        "Baixar relatório de envio manual (.md)",
        data=gerar_relatorio_envio_manual_markdown(),
        file_name="RELATORIO_ENVIO_MANUAL_NOTIFICACOES_VALORIS.md",
        mime="text/markdown",
    )


def executar_autoteste_envio_manual_notificacoes_valoris() -> Dict[str, Any]:
    return {
        "ok": True,
        "versao": VERSAO_ENVIO_MANUAL_VALORIS,
        "metricas": calcular_metricas_envio_manual(),
    }
