# exportacao_notificacoes_valoris.py
# Valoris — Exportação Segura de Notificações v3.12.1
# ------------------------------------------------------------
# Objetivo:
# - Exportar rascunhos aprovados manualmente sem enviar automaticamente.
# - Criar pacotes em CSV e Markdown por canal: WhatsApp, E-mail, Calendário e Resumo Executivo.
# - Manter trilha de auditoria: rascunho -> aprovação -> exportação.
# - Preparar futura integração real com canais externos.

from __future__ import annotations

import csv
import json
from collections import Counter, deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st


VERSAO_EXPORTACAO_NOTIFICACOES_VALORIS = "3.12.1"

CAMINHO_RASCUNHOS = Path("rascunhos_notificacoes_externas_valoris.csv")
CAMINHO_APROVACOES = Path("aprovacoes_notificacoes_externas_valoris.csv")
CAMINHO_EXPORTACOES = Path("exportacoes_notificacoes_valoris.csv")
PASTA_EXPORTACOES = Path("exports_notificacoes_valoris")

CAMINHO_RELATORIO = Path("RELATORIO_EXPORTACAO_NOTIFICACOES_VALORIS.md")
CAMINHO_MANIFESTO = Path("manifesto_exportacao_notificacoes_valoris.json")

CAMPOS_RASCUNHOS = [
    "data_hora", "canal", "ticker", "empresa", "tipo", "severidade",
    "destinatario", "assunto", "mensagem", "status", "observacao",
]

CAMPOS_APROVACOES = [
    "data_hora", "id_rascunho", "canal", "ticker", "empresa", "tipo",
    "severidade", "decisao_aprovacao", "responsavel", "motivo", "proxima_acao",
]

CAMPOS_EXPORTACOES = [
    "data_hora", "id_rascunho", "canal", "ticker", "empresa", "tipo",
    "severidade", "arquivo_csv", "arquivo_md", "status_exportacao",
    "responsavel", "observacao",
]


def _agora_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat(sep=" ")


def _stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _txt(valor: Any) -> str:
    return "" if valor is None else str(valor).strip()


def _safe(valor: Any) -> str:
    texto = _txt(valor)
    seguro = "".join(ch if ch.isalnum() else "_" for ch in texto)
    return "_".join([p for p in seguro.split("_") if p])[:80] or "sem_nome"


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
    return _safe(bruto)[:160] or "rascunho_sem_id"


def carregar_rascunhos(max_registros: int = 2000) -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_RASCUNHOS, CAMPOS_RASCUNHOS)
    try:
        with CAMINHO_RASCUNHOS.open("r", newline="", encoding="utf-8") as arquivo:
            return list(deque(csv.DictReader(arquivo), maxlen=max_registros))
    except Exception:
        return []


def carregar_aprovacoes(max_registros: int = 2000) -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_APROVACOES, CAMPOS_APROVACOES)
    try:
        with CAMINHO_APROVACOES.open("r", newline="", encoding="utf-8") as arquivo:
            return list(deque(csv.DictReader(arquivo), maxlen=max_registros))
    except Exception:
        return []


def carregar_exportacoes(max_registros: int = 2000) -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_EXPORTACOES, CAMPOS_EXPORTACOES)
    try:
        with CAMINHO_EXPORTACOES.open("r", newline="", encoding="utf-8") as arquivo:
            return list(deque(csv.DictReader(arquivo), maxlen=max_registros))
    except Exception:
        return []


def mapa_aprovacoes_validas() -> Dict[str, Dict[str, str]]:
    aprovadas: Dict[str, Dict[str, str]] = {}
    for item in carregar_aprovacoes():
        rid = _txt(item.get("id_rascunho"))
        decisao = _txt(item.get("decisao_aprovacao")).lower()
        if rid and "aprovado" in decisao:
            aprovadas[rid] = item
    return aprovadas


def ids_exportados() -> set[str]:
    return {_txt(item.get("id_rascunho")) for item in carregar_exportacoes() if _txt(item.get("id_rascunho"))}


def gerar_fila_exportacao() -> List[Dict[str, Any]]:
    aprovadas = mapa_aprovacoes_validas()
    exportados = ids_exportados()
    fila = []

    for rascunho in carregar_rascunhos():
        rid = _id_rascunho(rascunho)
        aprovacao = aprovadas.get(rid)

        if not aprovacao:
            continue

        fila.append({
            "id_rascunho": rid,
            "exportado": "Sim" if rid in exportados else "Não",
            "canal": _txt(rascunho.get("canal")),
            "ticker": _txt(rascunho.get("ticker")).upper(),
            "empresa": _txt(rascunho.get("empresa")),
            "tipo": _txt(rascunho.get("tipo")),
            "severidade": _txt(rascunho.get("severidade")),
            "destinatario": _txt(rascunho.get("destinatario")),
            "assunto": _txt(rascunho.get("assunto")),
            "mensagem": _txt(rascunho.get("mensagem")),
            "status_rascunho": _txt(rascunho.get("status")),
            "responsavel_aprovacao": _txt(aprovacao.get("responsavel")),
            "motivo_aprovacao": _txt(aprovacao.get("motivo")),
            "proxima_acao": _txt(aprovacao.get("proxima_acao")),
        })

    fila.sort(key=lambda x: (x["exportado"], x["canal"], x["ticker"], x["severidade"]))
    return fila


def gerar_markdown_exportacao(itens: List[Dict[str, Any]], canal: str) -> str:
    linhas = []

    for item in itens:
        linhas.append(
            f"""## {item['ticker']} — {item['empresa']} — {item['tipo']}

Canal: {item['canal']}  
Severidade: {item['severidade']}  
Destinatário: {item['destinatario']}  
Assunto: {item['assunto']}  
Responsável pela aprovação: {item['responsavel_aprovacao']}

### Mensagem

{item['mensagem']}

### Observação de aprovação

{item['motivo_aprovacao']}

---
"""
        )

    corpo = "\n".join(linhas) or "Nenhum item aprovado para exportar."

    return f"""# Exportação Segura de Notificações — Valoris

Versão: {VERSAO_EXPORTACAO_NOTIFICACOES_VALORIS}  
Gerado em: {_agora_iso()}  
Canal: {canal}

> Este arquivo é uma exportação segura. Nenhuma mensagem foi enviada automaticamente.

{corpo}
"""


def exportar_itens(itens: List[Dict[str, Any]], canal: str, responsavel: str, observacao: str = "") -> Dict[str, Any]:
    PASTA_EXPORTACOES.mkdir(exist_ok=True)

    canal_seguro = _safe(canal)
    stamp = _stamp()

    csv_path = PASTA_EXPORTACOES / f"export_notificacoes_{canal_seguro}_{stamp}.csv"
    md_path = PASTA_EXPORTACOES / f"export_notificacoes_{canal_seguro}_{stamp}.md"

    campos = [
        "id_rascunho", "canal", "ticker", "empresa", "tipo", "severidade",
        "destinatario", "assunto", "mensagem", "responsavel_aprovacao", "proxima_acao",
    ]

    with csv_path.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()
        for item in itens:
            escritor.writerow({campo: _txt(item.get(campo)) for campo in campos})

    md_path.write_text(gerar_markdown_exportacao(itens, canal=canal), encoding="utf-8")

    _garantir_csv(CAMINHO_EXPORTACOES, CAMPOS_EXPORTACOES)
    with CAMINHO_EXPORTACOES.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_EXPORTACOES)
        for item in itens:
            escritor.writerow({
                "data_hora": _agora_iso(),
                "id_rascunho": _txt(item.get("id_rascunho")),
                "canal": _txt(item.get("canal")),
                "ticker": _txt(item.get("ticker")),
                "empresa": _txt(item.get("empresa")),
                "tipo": _txt(item.get("tipo")),
                "severidade": _txt(item.get("severidade")),
                "arquivo_csv": str(csv_path),
                "arquivo_md": str(md_path),
                "status_exportacao": "Exportado para envio manual",
                "responsavel": _txt(responsavel),
                "observacao": _txt(observacao),
            })

    return {
        "ok": True,
        "csv_path": str(csv_path),
        "md_path": str(md_path),
        "itens": len(itens),
    }


def calcular_metricas_exportacao() -> Dict[str, Any]:
    fila = gerar_fila_exportacao()
    exportados = ids_exportados()
    pendentes = [item for item in fila if item["id_rascunho"] not in exportados]
    exportacoes = carregar_exportacoes()

    por_canal = Counter(item.get("canal", "Sem canal") for item in fila)
    por_severidade = Counter(item.get("severidade", "Sem severidade") for item in fila)

    score = 55
    if fila:
        score += 15
    if pendentes:
        score += 10
    if exportacoes:
        score += 10
    if por_severidade.get("Crítica", 0):
        score -= 10

    score = max(0, min(100, int(score)))

    if not fila:
        risco = "Baixo"
        decisao = "Sem rascunhos aprovados para exportar"
        proximo = "Aprovar rascunhos antes de exportar."
    elif pendentes:
        risco = "Baixo/Médio"
        decisao = "Há rascunhos aprovados prontos para exportação manual"
        proximo = "Exportar pacote por canal e revisar antes de qualquer envio."
    else:
        risco = "Baixo"
        decisao = "Rascunhos aprovados já exportados"
        proximo = "Usar arquivos exportados manualmente ou preparar integração futura."

    return {
        "versao": VERSAO_EXPORTACAO_NOTIFICACOES_VALORIS,
        "gerado_em": _agora_iso(),
        "score_exportacao": score,
        "aprovados": len(fila),
        "pendentes_exportacao": len(pendentes),
        "ja_exportados": len(fila) - len(pendentes),
        "exportacoes_registradas": len(exportacoes),
        "por_canal": dict(por_canal),
        "por_severidade": dict(por_severidade),
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo,
    }


def gerar_relatorio_exportacao_markdown() -> str:
    metricas = calcular_metricas_exportacao()
    fila = gerar_fila_exportacao()

    linhas = "\n".join(
        [
            f"- **{item['canal']} — {item['ticker']} — {item['severidade']}**: {item['assunto']} | exportado: {item['exportado']}"
            for item in fila[:80]
        ]
    ) or "- Nenhum rascunho aprovado para exportar."

    return f"""# Exportação Segura de Notificações — Valoris

Versão: {VERSAO_EXPORTACAO_NOTIFICACOES_VALORIS}  
Gerado em: {_agora_iso()}

## Diagnóstico

Score exportação: {metricas['score_exportacao']}/100  
Aprovados: {metricas['aprovados']}  
Pendentes de exportação: {metricas['pendentes_exportacao']}  
Já exportados: {metricas['ja_exportados']}  
Exportações registradas: {metricas['exportacoes_registradas']}  

Risco: {metricas['risco']}  
Decisão: {metricas['decisao']}  
Próximo passo: {metricas['proximo_passo']}

## Fila

{linhas}

## Estratégia

Esta versão exporta rascunhos aprovados para envio manual. O Valoris ainda não envia mensagens automaticamente; ele prepara pacotes auditáveis em CSV e Markdown.
"""


def salvar_relatorio_exportacao() -> Path:
    CAMINHO_RELATORIO.write_text(gerar_relatorio_exportacao_markdown(), encoding="utf-8")
    return CAMINHO_RELATORIO


def gerar_manifesto_exportacao() -> Dict[str, Any]:
    return {
        "produto": "Valoris",
        "versao": VERSAO_EXPORTACAO_NOTIFICACOES_VALORIS,
        "modulo": "exportacao_notificacoes_valoris",
        "data_hora": _agora_iso(),
        "metricas": calcular_metricas_exportacao(),
        "fila_exportacao": gerar_fila_exportacao(),
        "principio": "exportar é diferente de enviar; automação só depois de trilha auditável",
        "proxima_etapa": "conector manual com calendário ou e-mail",
    }


def salvar_manifesto_exportacao() -> Path:
    CAMINHO_MANIFESTO.write_text(
        json.dumps(gerar_manifesto_exportacao(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return CAMINHO_MANIFESTO


def renderizar_exportacao_notificacoes_valoris() -> None:
    st.subheader("Exportação de Notificações")
    st.caption("Exporta rascunhos aprovados para envio manual. Nenhuma mensagem é enviada automaticamente.")

    metricas = calcular_metricas_exportacao()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Score exportação", f"{metricas['score_exportacao']}/100")
    col2.metric("Aprovados", metricas["aprovados"])
    col3.metric("Pendentes", metricas["pendentes_exportacao"])
    col4.metric("Exportações", metricas["exportacoes_registradas"])

    if metricas["risco"] == "Baixo":
        st.success(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    else:
        st.info(f"{metricas['decisao']} — {metricas['proximo_passo']}")

    st.divider()

    fila = gerar_fila_exportacao()
    canais = ["Todos"] + sorted({item.get("canal", "") for item in fila if item.get("canal")})
    canal = st.selectbox("Canal para exportação", canais)

    filtro_exportado = st.selectbox("Status", ["Pendentes", "Todos", "Já exportados"])
    filtro_ticker = st.text_input("Ticker", value="")

    filtrados = []
    for item in fila:
        if canal != "Todos" and item.get("canal") != canal:
            continue
        if filtro_exportado == "Pendentes" and item.get("exportado") == "Sim":
            continue
        if filtro_exportado == "Já exportados" and item.get("exportado") != "Sim":
            continue
        if filtro_ticker.strip() and filtro_ticker.strip().upper() not in item.get("ticker", ""):
            continue
        filtrados.append(item)

    st.markdown("### Fila de exportação")
    st.dataframe(
        [
            {
                "exportado": item.get("exportado"),
                "canal": item.get("canal"),
                "ticker": item.get("ticker"),
                "empresa": item.get("empresa"),
                "severidade": item.get("severidade"),
                "assunto": item.get("assunto"),
                "responsável aprovação": item.get("responsavel_aprovacao"),
            }
            for item in filtrados
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Exportar pacote seguro")

    responsavel = st.text_input("Responsável pela exportação", value="Fundador")
    observacao = st.text_area(
        "Observação",
        value=f"Exportação segura gerada na v{VERSAO_EXPORTACAO_NOTIFICACOES_VALORIS}. Nenhum envio automático realizado.",
        height=90,
    )

    if st.button("Exportar itens filtrados"):
        if not filtrados:
            st.warning("Nenhum item filtrado para exportar.")
        else:
            canal_exportado = canal if canal != "Todos" else "Todos"
            resultado = exportar_itens(filtrados, canal=canal_exportado, responsavel=responsavel, observacao=observacao)
            st.success(f"Exportação gerada: {resultado['itens']} itens.")
            st.write(f"CSV: {resultado['csv_path']}")
            st.write(f"Markdown: {resultado['md_path']}")
            st.rerun()

    exportacoes = carregar_exportacoes()
    if exportacoes:
        st.markdown("### Exportações registradas")
        st.dataframe(exportacoes, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Relatórios")

    col_r1, col_r2 = st.columns(2)

    if col_r1.button("Salvar relatório de exportação"):
        caminho = salvar_relatorio_exportacao()
        st.success(f"Relatório salvo em {caminho}")

    if col_r2.button("Salvar manifesto de exportação"):
        caminho = salvar_manifesto_exportacao()
        st.success(f"Manifesto salvo em {caminho}")

    st.download_button(
        "Baixar relatório de exportação (.md)",
        data=gerar_relatorio_exportacao_markdown(),
        file_name="RELATORIO_EXPORTACAO_NOTIFICACOES_VALORIS.md",
        mime="text/markdown",
    )


def executar_autoteste_exportacao_notificacoes_valoris() -> Dict[str, Any]:
    metricas = calcular_metricas_exportacao()
    return {
        "ok": True,
        "versao": VERSAO_EXPORTACAO_NOTIFICACOES_VALORIS,
        "metricas": metricas,
    }
