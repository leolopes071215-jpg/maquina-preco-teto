# aprovacao_rascunhos_playbook_valoris.py
# Valoris — Aprovação de Rascunhos do Playbook v3.12.8
# ------------------------------------------------------------
# Objetivo:
# - Criar uma ponte segura entre "Rascunhos Playbook" e o fluxo oficial de aprovação.
# - Revisar rascunhos gerados pelo playbook.
# - Aprovar, revisar, bloquear ou promover para a fila oficial de Notificações Externas.
# - Não envia mensagens automaticamente.

from __future__ import annotations

import csv
import json
from collections import Counter, deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st


VERSAO_APROVACAO_RASCUNHOS_PLAYBOOK_VALORIS = "3.12.8"

CAMINHO_RASCUNHOS_PLAYBOOK = Path("rascunhos_playbook_comunicacao_valoris.csv")
CAMINHO_APROVACOES_PLAYBOOK = Path("aprovacoes_rascunhos_playbook_valoris.csv")
CAMINHO_RASCUNHOS_OFICIAIS = Path("rascunhos_notificacoes_externas_valoris.csv")

CAMINHO_RELATORIO = Path("RELATORIO_APROVACAO_RASCUNHOS_PLAYBOOK_VALORIS.md")
CAMINHO_MANIFESTO = Path("manifesto_aprovacao_rascunhos_playbook_valoris.json")

CAMPOS_RASCUNHOS_PLAYBOOK = [
    "data_hora",
    "canal",
    "ticker",
    "empresa",
    "tipo",
    "severidade",
    "assunto",
    "mensagem",
    "template_origem",
    "status_rascunho",
    "responsavel",
    "observacao",
]

CAMPOS_APROVACOES_PLAYBOOK = [
    "data_hora",
    "id_rascunho_playbook",
    "canal",
    "ticker",
    "empresa",
    "tipo",
    "severidade",
    "decisao_aprovacao",
    "promovido_fluxo_oficial",
    "responsavel",
    "motivo",
    "proxima_acao",
]

CAMPOS_RASCUNHOS_OFICIAIS = [
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


def _safe(valor: Any) -> str:
    texto = _txt(valor)
    seguro = "".join(ch if ch.isalnum() else "_" for ch in texto)
    return "_".join([p for p in seguro.split("_") if p])[:160] or "sem_id"


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


def _ler_csv(caminho: Path, campos: List[str], max_registros: int = 3000) -> List[Dict[str, str]]:
    _garantir_csv(caminho, campos)

    try:
        with caminho.open("r", newline="", encoding="utf-8") as arquivo:
            leitor = csv.DictReader(arquivo)
            return list(deque(leitor, maxlen=max_registros))
    except Exception:
        return []


def carregar_rascunhos_playbook() -> List[Dict[str, str]]:
    return _ler_csv(CAMINHO_RASCUNHOS_PLAYBOOK, CAMPOS_RASCUNHOS_PLAYBOOK, max_registros=2000)


def carregar_aprovacoes_playbook() -> List[Dict[str, str]]:
    return _ler_csv(CAMINHO_APROVACOES_PLAYBOOK, CAMPOS_APROVACOES_PLAYBOOK, max_registros=2000)


def carregar_rascunhos_oficiais() -> List[Dict[str, str]]:
    return _ler_csv(CAMINHO_RASCUNHOS_OFICIAIS, CAMPOS_RASCUNHOS_OFICIAIS, max_registros=3000)


def _id_rascunho_playbook(item: Dict[str, Any]) -> str:
    bruto = "|".join(
        [
            _txt(item.get("data_hora")),
            _txt(item.get("canal")),
            _txt(item.get("ticker")).upper(),
            _txt(item.get("tipo")),
            _txt(item.get("assunto")),
            _txt(item.get("template_origem")),
        ]
    )
    return _safe(bruto)


def _id_rascunho_oficial(item: Dict[str, Any]) -> str:
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


def mapa_aprovacoes_playbook() -> Dict[str, Dict[str, str]]:
    mapa = {}

    for item in carregar_aprovacoes_playbook():
        rid = _txt(item.get("id_rascunho_playbook"))
        if rid:
            mapa[rid] = item

    return mapa


def ids_promovidos_fluxo_oficial() -> set[str]:
    return {
        _txt(item.get("id_rascunho_playbook"))
        for item in carregar_aprovacoes_playbook()
        if _txt(item.get("promovido_fluxo_oficial")) == "Sim"
    }


def severidade_rank(valor: Any) -> int:
    return {
        "Crítica": 1,
        "Alta": 2,
        "Média/Alta": 3,
        "Média": 4,
        "Baixa": 5,
    }.get(_txt(valor), 9)


def classificar_rascunho_playbook(item: Dict[str, Any]) -> Dict[str, Any]:
    bloqueios = []
    alertas = []

    mensagem = _txt(item.get("mensagem"))
    canal = _txt(item.get("canal"))
    ticker = _txt(item.get("ticker")).upper()
    status_rascunho = _txt(item.get("status_rascunho"))
    template_origem = _txt(item.get("template_origem"))

    if not mensagem:
        bloqueios.append("Mensagem vazia")

    if not canal:
        bloqueios.append("Canal ausente")

    if not ticker:
        bloqueios.append("Ticker ausente")

    if status_rascunho == "Não usar":
        bloqueios.append("Rascunho marcado como não usar")

    if "Sugestão não aprovada" in template_origem:
        alertas.append("Template ainda não aprovado oficialmente")

    if status_rascunho == "Manter em revisão":
        alertas.append("Rascunho ainda em revisão")

    if bloqueios:
        recomendacao = "Bloquear"
        proxima = "Corrigir bloqueios antes de promover."
    elif alertas:
        recomendacao = "Revisar"
        proxima = "Revisar manualmente e aprovar apenas se o padrão for aceitável."
    else:
        recomendacao = "Aprovar"
        proxima = "Pode ser aprovado e promovido para o fluxo oficial."

    return {
        "recomendacao": recomendacao,
        "bloqueios": "; ".join(bloqueios),
        "alertas": "; ".join(alertas),
        "proxima_acao": proxima,
    }


def gerar_fila_aprovacao_playbook() -> List[Dict[str, Any]]:
    rascunhos = carregar_rascunhos_playbook()
    aprovacoes = mapa_aprovacoes_playbook()
    promovidos = ids_promovidos_fluxo_oficial()

    fila = []

    for item in rascunhos:
        rid = _id_rascunho_playbook(item)
        aprovacao = aprovacoes.get(rid, {})
        classificacao = classificar_rascunho_playbook(item)

        fila.append(
            {
                "id_rascunho_playbook": rid,
                "data_hora": _txt(item.get("data_hora")),
                "canal": _txt(item.get("canal")),
                "ticker": _txt(item.get("ticker")).upper(),
                "empresa": _txt(item.get("empresa")),
                "tipo": _txt(item.get("tipo")),
                "severidade": _txt(item.get("severidade")),
                "assunto": _txt(item.get("assunto")),
                "mensagem": _txt(item.get("mensagem")),
                "template_origem": _txt(item.get("template_origem")),
                "status_rascunho": _txt(item.get("status_rascunho")),
                "responsavel_rascunho": _txt(item.get("responsavel")),
                "recomendacao": classificacao["recomendacao"],
                "bloqueios": classificacao["bloqueios"],
                "alertas": classificacao["alertas"],
                "proxima_acao": classificacao["proxima_acao"],
                "decisao_anterior": _txt(aprovacao.get("decisao_aprovacao")),
                "promovido_fluxo_oficial": "Sim" if rid in promovidos else "Não",
            }
        )

    ordem_recomendacao = {"Bloquear": 1, "Revisar": 2, "Aprovar": 3}

    fila.sort(
        key=lambda item: (
            0 if item.get("promovido_fluxo_oficial") == "Não" else 1,
            ordem_recomendacao.get(item.get("recomendacao"), 9),
            severidade_rank(item.get("severidade")),
            item.get("canal", ""),
            item.get("ticker", ""),
        )
    )

    return fila


def salvar_aprovacao_playbook(item: Dict[str, Any], decisao: str, promover: bool, responsavel: str, motivo: str, proxima_acao: str) -> Path:
    _garantir_csv(CAMINHO_APROVACOES_PLAYBOOK, CAMPOS_APROVACOES_PLAYBOOK)

    with CAMINHO_APROVACOES_PLAYBOOK.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_APROVACOES_PLAYBOOK)
        escritor.writerow(
            {
                "data_hora": _agora_iso(),
                "id_rascunho_playbook": _txt(item.get("id_rascunho_playbook")),
                "canal": _txt(item.get("canal")),
                "ticker": _txt(item.get("ticker")).upper(),
                "empresa": _txt(item.get("empresa")),
                "tipo": _txt(item.get("tipo")),
                "severidade": _txt(item.get("severidade")),
                "decisao_aprovacao": _txt(decisao),
                "promovido_fluxo_oficial": "Sim" if promover else "Não",
                "responsavel": _txt(responsavel),
                "motivo": _txt(motivo),
                "proxima_acao": _txt(proxima_acao),
            }
        )

    if promover:
        promover_para_fluxo_oficial(item, responsavel=responsavel, motivo=motivo)

    return CAMINHO_APROVACOES_PLAYBOOK


def promover_para_fluxo_oficial(item: Dict[str, Any], responsavel: str, motivo: str = "") -> Path:
    _garantir_csv(CAMINHO_RASCUNHOS_OFICIAIS, CAMPOS_RASCUNHOS_OFICIAIS)

    oficiais = carregar_rascunhos_oficiais()
    novo = {
        "data_hora": _agora_iso(),
        "canal": _txt(item.get("canal")),
        "ticker": _txt(item.get("ticker")).upper(),
        "empresa": _txt(item.get("empresa")),
        "tipo": _txt(item.get("tipo")),
        "severidade": _txt(item.get("severidade")),
        "destinatario": "",
        "assunto": _txt(item.get("assunto")),
        "mensagem": _txt(item.get("mensagem")),
        "status": "Gerado via Playbook e promovido para aprovação oficial",
        "observacao": (
            f"Origem: {_txt(item.get('template_origem'))}. "
            f"Aprovado por {responsavel}. Motivo: {motivo}"
        ),
    }

    # Evita duplicar o mesmo rascunho no fluxo oficial usando canal/ticker/tipo/assunto/mensagem.
    assinatura_nova = "|".join(
        [
            novo["canal"],
            novo["ticker"],
            novo["tipo"],
            novo["assunto"],
            novo["mensagem"],
        ]
    )

    for existente in oficiais:
        assinatura_existente = "|".join(
            [
                _txt(existente.get("canal")),
                _txt(existente.get("ticker")).upper(),
                _txt(existente.get("tipo")),
                _txt(existente.get("assunto")),
                _txt(existente.get("mensagem")),
            ]
        )
        if assinatura_existente == assinatura_nova:
            return CAMINHO_RASCUNHOS_OFICIAIS

    with CAMINHO_RASCUNHOS_OFICIAIS.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_RASCUNHOS_OFICIAIS)
        escritor.writerow(novo)

    return CAMINHO_RASCUNHOS_OFICIAIS


def calcular_metricas_aprovacao_rascunhos_playbook() -> Dict[str, Any]:
    fila = gerar_fila_aprovacao_playbook()
    aprovacoes = carregar_aprovacoes_playbook()
    oficiais = carregar_rascunhos_oficiais()

    total = len(fila)
    recomendados_aprovar = len([i for i in fila if i.get("recomendacao") == "Aprovar"])
    recomendados_revisar = len([i for i in fila if i.get("recomendacao") == "Revisar"])
    recomendados_bloquear = len([i for i in fila if i.get("recomendacao") == "Bloquear"])
    aprovados = len([i for i in aprovacoes if _txt(i.get("decisao_aprovacao")) == "Aprovado"])
    promovidos = len([i for i in aprovacoes if _txt(i.get("promovido_fluxo_oficial")) == "Sim"])
    pendentes = len([i for i in fila if not _txt(i.get("decisao_anterior"))])

    por_canal = Counter(i.get("canal", "Sem canal") or "Sem canal" for i in fila)
    por_decisao = Counter(_txt(i.get("decisao_aprovacao")) or "Sem decisão" for i in aprovacoes)

    score = 45

    if total:
        score += 10

    if recomendados_aprovar:
        score += 10

    if aprovados:
        score += 15

    if promovidos:
        score += 15

    if recomendados_bloquear:
        score -= min(recomendados_bloquear * 8, 25)

    if pendentes > 5:
        score -= 10

    score = max(0, min(100, int(score)))

    if total == 0:
        risco = "Baixo"
        decisao = "Sem rascunhos do playbook para aprovar"
        proximo = "Gerar rascunhos na página Rascunhos Playbook."
    elif recomendados_bloquear:
        risco = "Médio"
        decisao = "Há rascunhos do playbook com bloqueios"
        proximo = "Bloquear ou corrigir rascunhos antes de promover ao fluxo oficial."
    elif recomendados_revisar:
        risco = "Baixo/Médio"
        decisao = "Há rascunhos que exigem revisão manual"
        proximo = "Aprovar apenas rascunhos com template confiável."
    elif promovidos:
        risco = "Baixo"
        decisao = "Rascunhos do playbook aprovados e promovidos"
        proximo = "Continuar no fluxo oficial de Aprovação Notificações."
    elif recomendados_aprovar:
        risco = "Baixo/Médio"
        decisao = "Há rascunhos prontos para aprovação"
        proximo = "Salvar aprovação e promover para o fluxo oficial."
    else:
        risco = "Baixo/Médio"
        decisao = "Fila de aprovação do playbook em validação"
        proximo = "Revisar padrões e decidir o que será promovido."

    return {
        "versao": VERSAO_APROVACAO_RASCUNHOS_PLAYBOOK_VALORIS,
        "gerado_em": _agora_iso(),
        "score_aprovacao_playbook": score,
        "rascunhos": total,
        "pendentes": pendentes,
        "recomendados_aprovar": recomendados_aprovar,
        "recomendados_revisar": recomendados_revisar,
        "recomendados_bloquear": recomendados_bloquear,
        "aprovados": aprovados,
        "promovidos": promovidos,
        "rascunhos_oficiais": len(oficiais),
        "por_canal": dict(por_canal),
        "por_decisao": dict(por_decisao),
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo,
    }


def gerar_relatorio_aprovacao_playbook_markdown() -> str:
    metricas = calcular_metricas_aprovacao_rascunhos_playbook()
    fila = gerar_fila_aprovacao_playbook()

    linhas = "\n".join(
        [
            f"- **{item['recomendacao']} — {item['canal']} — {item['ticker']} — {item['severidade']}**: decisão={item['decisao_anterior'] or 'pendente'}, promovido={item['promovido_fluxo_oficial']}, alertas={item['alertas'] or 'nenhum'}, bloqueios={item['bloqueios'] or 'nenhum'}"
            for item in fila[:100]
        ]
    ) or "- Nenhum rascunho de playbook na fila."

    return f"""# Aprovação de Rascunhos do Playbook — Valoris

Versão: {VERSAO_APROVACAO_RASCUNHOS_PLAYBOOK_VALORIS}  
Gerado em: {_agora_iso()}

## Diagnóstico

Score aprovação playbook: {metricas['score_aprovacao_playbook']}/100  
Rascunhos: {metricas['rascunhos']}  
Pendentes: {metricas['pendentes']}  
Recomendados para aprovar: {metricas['recomendados_aprovar']}  
Recomendados para revisar: {metricas['recomendados_revisar']}  
Recomendados para bloquear: {metricas['recomendados_bloquear']}  
Aprovados: {metricas['aprovados']}  
Promovidos: {metricas['promovidos']}  
Rascunhos oficiais: {metricas['rascunhos_oficiais']}  

Risco: {metricas['risco']}  
Decisão: {metricas['decisao']}  
Próximo passo: {metricas['proximo_passo']}

## Fila

{linhas}

## Estratégia

Esta versão cria a ponte segura entre o playbook e o fluxo oficial. Um rascunho gerado por template só entra na esteira oficial depois de revisão, aprovação e promoção manual.
"""


def salvar_relatorio_aprovacao_playbook() -> Path:
    CAMINHO_RELATORIO.write_text(gerar_relatorio_aprovacao_playbook_markdown(), encoding="utf-8")
    return CAMINHO_RELATORIO


def gerar_manifesto_aprovacao_playbook() -> Dict[str, Any]:
    return {
        "produto": "Valoris",
        "versao": VERSAO_APROVACAO_RASCUNHOS_PLAYBOOK_VALORIS,
        "modulo": "aprovacao_rascunhos_playbook_valoris",
        "data_hora": _agora_iso(),
        "metricas": calcular_metricas_aprovacao_rascunhos_playbook(),
        "fila": gerar_fila_aprovacao_playbook(),
        "aprovacoes": carregar_aprovacoes_playbook(),
        "principio": "todo rascunho gerado por playbook precisa de aprovação antes de entrar no fluxo oficial",
        "proxima_etapa": "conector entre rascunhos oficiais e aprovação/exportação já existente",
    }


def salvar_manifesto_aprovacao_playbook() -> Path:
    CAMINHO_MANIFESTO.write_text(
        json.dumps(gerar_manifesto_aprovacao_playbook(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return CAMINHO_MANIFESTO


def renderizar_aprovacao_rascunhos_playbook_valoris() -> None:
    st.subheader("Aprovação Playbook")
    st.caption("Revisa rascunhos gerados pelo playbook e promove manualmente para o fluxo oficial de aprovação.")

    metricas = calcular_metricas_aprovacao_rascunhos_playbook()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Score aprovação", f"{metricas['score_aprovacao_playbook']}/100")
    col2.metric("Rascunhos", metricas["rascunhos"])
    col3.metric("Pendentes", metricas["pendentes"])
    col4.metric("Aprovados", metricas["aprovados"])
    col5.metric("Promovidos", metricas["promovidos"])

    if metricas["risco"] == "Médio":
        st.warning(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    elif metricas["risco"] == "Baixo":
        st.success(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    else:
        st.info(f"{metricas['decisao']} — {metricas['proximo_passo']}")

    st.divider()

    fila = gerar_fila_aprovacao_playbook()

    st.markdown("### Fila de aprovação do playbook")

    col_f1, col_f2, col_f3 = st.columns(3)
    canais = ["Todos"] + sorted({item.get("canal", "") for item in fila if item.get("canal")})
    recomendacoes = ["Todas"] + sorted({item.get("recomendacao", "") for item in fila if item.get("recomendacao")})
    filtro_canal = col_f1.selectbox("Canal", canais)
    filtro_recomendacao = col_f2.selectbox("Recomendação", recomendacoes)
    filtro_ticker = col_f3.text_input("Ticker", value="")

    filtrados = []

    for item in fila:
        if filtro_canal != "Todos" and item.get("canal") != filtro_canal:
            continue
        if filtro_recomendacao != "Todas" and item.get("recomendacao") != filtro_recomendacao:
            continue
        if filtro_ticker.strip() and filtro_ticker.strip().upper() not in item.get("ticker", ""):
            continue
        filtrados.append(item)

    st.dataframe(
        [
            {
                "recomendação": item.get("recomendacao"),
                "promovido": item.get("promovido_fluxo_oficial"),
                "decisão": item.get("decisao_anterior"),
                "canal": item.get("canal"),
                "ticker": item.get("ticker"),
                "severidade": item.get("severidade"),
                "assunto": item.get("assunto"),
                "alertas": item.get("alertas"),
                "bloqueios": item.get("bloqueios"),
            }
            for item in filtrados
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Revisar, aprovar e promover")

    if filtrados:
        opcoes = [
            f"{item['recomendacao']} | {item['canal']} | {item['ticker']} | {item['severidade']} | promovido: {item['promovido_fluxo_oficial']}"
            for item in filtrados
        ]

        escolha = st.selectbox("Rascunho do playbook", opcoes)
        item = filtrados[opcoes.index(escolha)]

        st.text_input("Assunto", value=item.get("assunto", ""), disabled=True)
        st.text_area("Mensagem", value=item.get("mensagem", ""), height=260, disabled=True)

        if item.get("alertas"):
            st.warning(item.get("alertas"))

        if item.get("bloqueios"):
            st.error(item.get("bloqueios"))

        col_a, col_b = st.columns(2)
        decisao = col_a.selectbox("Decisão", ["Aprovado", "Manter em revisão", "Bloqueado", "Descartado"])
        responsavel = col_b.text_input("Responsável", value="Fundador")

        promover = st.checkbox("Promover para rascunhos oficiais de Notificações Externas", value=(item.get("recomendacao") == "Aprovar"))

        motivo = st.text_area(
            "Motivo",
            value=f"Decisão registrada na Aprovação Playbook v{VERSAO_APROVACAO_RASCUNHOS_PLAYBOOK_VALORIS}.",
            height=90,
        )

        proxima_acao = st.text_input("Próxima ação", value=item.get("proxima_acao", ""))

        if st.button("Salvar decisão do playbook"):
            if promover and decisao != "Aprovado":
                st.error("Para promover ao fluxo oficial, a decisão precisa ser 'Aprovado'.")
            elif promover and item.get("bloqueios"):
                st.error("Rascunhos com bloqueios não devem ser promovidos. Corrija ou bloqueie primeiro.")
            else:
                salvar_aprovacao_playbook(
                    item,
                    decisao=decisao,
                    promover=promover,
                    responsavel=responsavel,
                    motivo=motivo,
                    proxima_acao=proxima_acao,
                )
                if promover:
                    st.success("Decisão salva e rascunho promovido para o fluxo oficial.")
                else:
                    st.success("Decisão salva. Nenhuma promoção automática foi feita.")
                st.rerun()
    else:
        st.info("Nenhum rascunho encontrado com os filtros atuais.")

    aprovacoes = carregar_aprovacoes_playbook()
    if aprovacoes:
        st.markdown("### Aprovações registradas")
        st.dataframe(aprovacoes, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Relatórios")

    col_r1, col_r2 = st.columns(2)

    if col_r1.button("Salvar relatório de aprovação playbook"):
        caminho = salvar_relatorio_aprovacao_playbook()
        st.success(f"Relatório salvo em {caminho}")

    if col_r2.button("Salvar manifesto de aprovação playbook"):
        caminho = salvar_manifesto_aprovacao_playbook()
        st.success(f"Manifesto salvo em {caminho}")

    st.download_button(
        "Baixar relatório de aprovação playbook (.md)",
        data=gerar_relatorio_aprovacao_playbook_markdown(),
        file_name="RELATORIO_APROVACAO_RASCUNHOS_PLAYBOOK_VALORIS.md",
        mime="text/markdown",
    )


def executar_autoteste_aprovacao_rascunhos_playbook_valoris() -> Dict[str, Any]:
    return {
        "ok": True,
        "versao": VERSAO_APROVACAO_RASCUNHOS_PLAYBOOK_VALORIS,
        "metricas": calcular_metricas_aprovacao_rascunhos_playbook(),
    }
