# rascunhos_playbook_valoris.py
# Valoris — Rascunhos com Playbook v3.12.7
# ------------------------------------------------------------
# Objetivo:
# - Usar padrões aprovados no Playbook de Comunicação para gerar novos rascunhos.
# - Transformar notificações internas em mensagens mais consistentes por canal.
# - Manter revisão manual antes de qualquer aprovação, exportação ou envio.
# - Não envia mensagens automaticamente.

from __future__ import annotations

import csv
import json
from collections import Counter, deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st


VERSAO_RASCUNHOS_PLAYBOOK_VALORIS = "3.12.7"

CAMINHO_PLAYBOOK = Path("playbook_comunicacao_valoris.csv")
CAMINHO_RASCUNHOS_PLAYBOOK = Path("rascunhos_playbook_comunicacao_valoris.csv")
CAMINHO_RELATORIO = Path("RELATORIO_RASCUNHOS_PLAYBOOK_VALORIS.md")
CAMINHO_MANIFESTO = Path("manifesto_rascunhos_playbook_valoris.json")

CAMPOS_PLAYBOOK = [
    "data_hora",
    "canal",
    "tipo_comunicacao",
    "prioridade",
    "template",
    "quando_usar",
    "quando_evitar",
    "responsavel",
    "status_playbook",
    "observacao",
]

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


def _ler_csv(caminho: Path, campos: List[str], max_registros: int = 3000) -> List[Dict[str, str]]:
    _garantir_csv(caminho, campos)

    try:
        with caminho.open("r", newline="", encoding="utf-8") as arquivo:
            leitor = csv.DictReader(arquivo)
            return list(deque(leitor, maxlen=max_registros))
    except Exception:
        return []


def carregar_playbook() -> List[Dict[str, str]]:
    return _ler_csv(CAMINHO_PLAYBOOK, CAMPOS_PLAYBOOK, max_registros=1200)


def carregar_rascunhos_playbook() -> List[Dict[str, str]]:
    return _ler_csv(CAMINHO_RASCUNHOS_PLAYBOOK, CAMPOS_RASCUNHOS_PLAYBOOK, max_registros=2000)


def carregar_notificacoes() -> List[Dict[str, Any]]:
    try:
        from central_notificacoes_valoris import gerar_notificacoes

        return gerar_notificacoes()
    except Exception:
        return []


def carregar_sugestoes_playbook() -> List[Dict[str, Any]]:
    try:
        from playbook_comunicacao_valoris import gerar_sugestoes_playbook

        return gerar_sugestoes_playbook()
    except Exception:
        return []


def carregar_metricas_playbook() -> Dict[str, Any]:
    try:
        from playbook_comunicacao_valoris import calcular_metricas_playbook

        return calcular_metricas_playbook()
    except Exception:
        return {}


def playbook_aprovado() -> List[Dict[str, Any]]:
    salvos = carregar_playbook()

    aprovados = [
        item
        for item in salvos
        if _txt(item.get("status_playbook")) in {"Aprovado", "Padrão oficial", "Em uso"}
    ]

    if aprovados:
        return aprovados

    # Se ainda não houver padrão salvo, usa sugestões como modo de teste,
    # sem tratá-las como padrão oficial.
    sugestoes = carregar_sugestoes_playbook()
    adaptadas = []

    for item in sugestoes:
        adaptadas.append(
            {
                "data_hora": _agora_iso(),
                "canal": _txt(item.get("canal")),
                "tipo_comunicacao": _txt(item.get("tipo_comunicacao")) or "Experimento manual",
                "prioridade": _txt(item.get("prioridade")),
                "template": _txt(item.get("template")),
                "quando_usar": _txt(item.get("quando_usar")),
                "quando_evitar": _txt(item.get("quando_evitar")),
                "responsavel": "Sistema",
                "status_playbook": "Sugestão não aprovada",
                "observacao": "Sugestão usada apenas para teste de rascunho.",
            }
        )

    return adaptadas


def severidade_rank(valor: Any) -> int:
    return {
        "Crítica": 1,
        "Alta": 2,
        "Média/Alta": 3,
        "Média": 4,
        "Baixa": 5,
    }.get(_txt(valor), 9)


def assunto_por_canal(canal: str, notificacao: Dict[str, Any]) -> str:
    ticker = _txt(notificacao.get("ticker")).upper()
    tipo = _txt(notificacao.get("tipo"))
    severidade = _txt(notificacao.get("severidade"))

    if canal == "E-mail":
        return f"[Valoris] {severidade}: {ticker} — {tipo}"

    if canal == "Calendário":
        return f"Revisão Valoris — {ticker} — {tipo}"

    if canal == "WhatsApp":
        return f"Valoris | {ticker} | {tipo}"

    return f"Resumo Valoris — {ticker} — {tipo}"


def preencher_template(template: str, notificacao: Dict[str, Any]) -> str:
    contexto = _txt(notificacao.get("contexto")) or _txt(notificacao.get("origem")) or "Sem contexto adicional."
    acao = _txt(notificacao.get("acao_recomendada")) or "Revisar e definir próxima ação."
    proximo = "Registrar decisão no Valoris após revisão manual."

    valores = {
        "ticker": _txt(notificacao.get("ticker")).upper(),
        "empresa": _txt(notificacao.get("empresa")) or _txt(notificacao.get("ticker")).upper(),
        "tipo": _txt(notificacao.get("tipo")) or "Acompanhamento",
        "severidade": _txt(notificacao.get("severidade")) or "Média",
        "acao": acao,
        "contexto": contexto,
        "proximo_passo": proximo,
    }

    try:
        return template.format(**valores)
    except Exception:
        # Se o template tiver marcador inesperado, mantém o conteúdo e adiciona contexto.
        return (
            f"{template}\n\n"
            f"Ativo: {valores['ticker']} — {valores['empresa']}\n"
            f"Tipo: {valores['tipo']}\n"
            f"Severidade: {valores['severidade']}\n"
            f"Ação: {valores['acao']}"
        )


def gerar_rascunhos_com_playbook() -> List[Dict[str, Any]]:
    notificacoes = carregar_notificacoes()
    padroes = playbook_aprovado()

    rascunhos = []

    if not notificacoes or not padroes:
        return rascunhos

    notificacoes_relevantes = [
        item
        for item in notificacoes
        if _txt(item.get("tipo")) in {"Atrasado", "Sem prazo", "Vence em 7 dias", "Vence em 15 dias"}
        or _txt(item.get("severidade")) in {"Crítica", "Alta", "Média/Alta"}
    ]

    if not notificacoes_relevantes:
        notificacoes_relevantes = notificacoes[:20]

    for notificacao in notificacoes_relevantes:
        for padrao in padroes:
            canal = _txt(padrao.get("canal")) or "Resumo Executivo"
            template = _txt(padrao.get("template"))

            if not template:
                continue

            mensagem = preencher_template(template, notificacao)
            status_base = _txt(padrao.get("status_playbook"))

            rascunhos.append(
                {
                    "canal": canal,
                    "ticker": _txt(notificacao.get("ticker")).upper(),
                    "empresa": _txt(notificacao.get("empresa")) or _txt(notificacao.get("ticker")).upper(),
                    "tipo": _txt(notificacao.get("tipo")),
                    "severidade": _txt(notificacao.get("severidade")),
                    "assunto": assunto_por_canal(canal, notificacao),
                    "mensagem": mensagem,
                    "template_origem": f"{canal} | {padrao.get('tipo_comunicacao')} | {status_base}",
                    "quando_usar": _txt(padrao.get("quando_usar")),
                    "quando_evitar": _txt(padrao.get("quando_evitar")),
                    "status_playbook": status_base,
                }
            )

    rascunhos.sort(
        key=lambda item: (
            0 if item.get("status_playbook") in {"Aprovado", "Padrão oficial", "Em uso"} else 1,
            severidade_rank(item.get("severidade")),
            item.get("canal", ""),
            item.get("ticker", ""),
        )
    )

    return rascunhos


def salvar_rascunho_playbook(item: Dict[str, Any], status_rascunho: str, responsavel: str, observacao: str = "") -> Path:
    _garantir_csv(CAMINHO_RASCUNHOS_PLAYBOOK, CAMPOS_RASCUNHOS_PLAYBOOK)

    with CAMINHO_RASCUNHOS_PLAYBOOK.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_RASCUNHOS_PLAYBOOK)
        escritor.writerow(
            {
                "data_hora": _agora_iso(),
                "canal": _txt(item.get("canal")),
                "ticker": _txt(item.get("ticker")).upper(),
                "empresa": _txt(item.get("empresa")),
                "tipo": _txt(item.get("tipo")),
                "severidade": _txt(item.get("severidade")),
                "assunto": _txt(item.get("assunto")),
                "mensagem": _txt(item.get("mensagem")),
                "template_origem": _txt(item.get("template_origem")),
                "status_rascunho": _txt(status_rascunho),
                "responsavel": _txt(responsavel),
                "observacao": _txt(observacao),
            }
        )

    return CAMINHO_RASCUNHOS_PLAYBOOK


def calcular_metricas_rascunhos_playbook() -> Dict[str, Any]:
    notificacoes = carregar_notificacoes()
    padroes = playbook_aprovado()
    rascunhos = gerar_rascunhos_com_playbook()
    salvos = carregar_rascunhos_playbook()
    metricas_playbook = carregar_metricas_playbook()

    oficiais = len([p for p in padroes if _txt(p.get("status_playbook")) in {"Aprovado", "Padrão oficial", "Em uso"}])
    sugestoes = len(padroes) - oficiais

    por_canal = Counter(r.get("canal", "Sem canal") for r in rascunhos)
    por_severidade = Counter(r.get("severidade", "Sem severidade") for r in rascunhos)
    por_status_salvo = Counter(r.get("status_rascunho", "Sem status") for r in salvos)

    score_playbook = _int(metricas_playbook.get("score_playbook"), 0)

    score = 45
    score += min(score_playbook // 4, 25)

    if oficiais:
        score += 15
    elif sugestoes:
        score += 5

    if rascunhos:
        score += 10

    if salvos:
        score += 10

    if not oficiais:
        score -= 10

    score = max(0, min(100, int(score)))

    if not notificacoes:
        risco = "Baixo"
        decisao = "Sem notificações internas para gerar rascunhos"
        proximo = "Gerar notificações internas antes de aplicar playbook."
    elif not padroes:
        risco = "Médio"
        decisao = "Sem padrões de playbook disponíveis"
        proximo = "Criar e aprovar padrões no Playbook de Comunicação."
    elif not oficiais:
        risco = "Médio"
        decisao = "Rascunhos gerados com sugestões ainda não aprovadas"
        proximo = "Aprovar padrões oficiais antes de usar em escala."
    elif rascunhos and salvos:
        risco = "Baixo"
        decisao = "Rascunhos com playbook funcionando"
        proximo = "Enviar rascunhos aprovados para a etapa de aprovação manual."
    elif rascunhos:
        risco = "Baixo/Médio"
        decisao = "Rascunhos com playbook gerados para revisão"
        proximo = "Salvar rascunhos revisados e medir qualidade no próximo ciclo."
    else:
        risco = "Baixo/Médio"
        decisao = "Playbook existe, mas não gerou rascunhos relevantes"
        proximo = "Revisar critérios de notificação ou templates do playbook."

    return {
        "versao": VERSAO_RASCUNHOS_PLAYBOOK_VALORIS,
        "gerado_em": _agora_iso(),
        "score_rascunhos_playbook": score,
        "notificacoes": len(notificacoes),
        "padroes_disponiveis": len(padroes),
        "padroes_oficiais": oficiais,
        "sugestoes_nao_aprovadas": sugestoes,
        "rascunhos_gerados": len(rascunhos),
        "rascunhos_salvos": len(salvos),
        "score_playbook": score_playbook,
        "por_canal": dict(por_canal),
        "por_severidade": dict(por_severidade),
        "por_status_salvo": dict(por_status_salvo),
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo,
    }


def gerar_relatorio_rascunhos_playbook_markdown() -> str:
    metricas = calcular_metricas_rascunhos_playbook()
    rascunhos = gerar_rascunhos_com_playbook()
    salvos = carregar_rascunhos_playbook()

    linhas = "\n\n".join(
        [
            f"## {item['canal']} — {item['ticker']} — {item['tipo']}\n\n"
            f"Assunto: {item['assunto']}\n\n"
            f"{item['mensagem']}\n\n"
            f"Template: {item['template_origem']}"
            for item in rascunhos[:30]
        ]
    ) or "Nenhum rascunho gerado com playbook."

    return f"""# Rascunhos com Playbook — Valoris

Versão: {VERSAO_RASCUNHOS_PLAYBOOK_VALORIS}  
Gerado em: {_agora_iso()}

## Diagnóstico

Score rascunhos com playbook: {metricas['score_rascunhos_playbook']}/100  
Notificações: {metricas['notificacoes']}  
Padrões disponíveis: {metricas['padroes_disponiveis']}  
Padrões oficiais: {metricas['padroes_oficiais']}  
Sugestões não aprovadas: {metricas['sugestoes_nao_aprovadas']}  
Rascunhos gerados: {metricas['rascunhos_gerados']}  
Rascunhos salvos: {metricas['rascunhos_salvos']}  

Risco: {metricas['risco']}  
Decisão: {metricas['decisao']}  
Próximo passo: {metricas['proximo_passo']}

## Rascunhos gerados

{linhas}

## Rascunhos salvos

Total salvo: {len(salvos)}

## Estratégia

Esta versão conecta playbook e operação. O Valoris passa a gerar mensagens mais consistentes, sem automatizar envio. O próximo passo seguro é conectar estes rascunhos à aprovação manual.
"""


def salvar_relatorio_rascunhos_playbook() -> Path:
    CAMINHO_RELATORIO.write_text(gerar_relatorio_rascunhos_playbook_markdown(), encoding="utf-8")
    return CAMINHO_RELATORIO


def gerar_manifesto_rascunhos_playbook() -> Dict[str, Any]:
    return {
        "produto": "Valoris",
        "versao": VERSAO_RASCUNHOS_PLAYBOOK_VALORIS,
        "modulo": "rascunhos_playbook_valoris",
        "data_hora": _agora_iso(),
        "metricas": calcular_metricas_rascunhos_playbook(),
        "rascunhos_gerados": gerar_rascunhos_com_playbook(),
        "rascunhos_salvos": carregar_rascunhos_playbook(),
        "principio": "um playbook só cria valor quando vira rascunho operacional revisável",
        "proxima_etapa": "aprovação integrada de rascunhos gerados pelo playbook",
    }


def salvar_manifesto_rascunhos_playbook() -> Path:
    CAMINHO_MANIFESTO.write_text(
        json.dumps(gerar_manifesto_rascunhos_playbook(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return CAMINHO_MANIFESTO


def renderizar_rascunhos_playbook_valoris() -> None:
    st.subheader("Rascunhos com Playbook")
    st.caption("Gera rascunhos usando padrões do Playbook de Comunicação. Nenhuma mensagem é enviada automaticamente.")

    metricas = calcular_metricas_rascunhos_playbook()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Score rascunhos", f"{metricas['score_rascunhos_playbook']}/100")
    col2.metric("Notificações", metricas["notificacoes"])
    col3.metric("Padrões oficiais", metricas["padroes_oficiais"])
    col4.metric("Gerados", metricas["rascunhos_gerados"])
    col5.metric("Salvos", metricas["rascunhos_salvos"])

    if metricas["risco"] == "Médio":
        st.warning(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    elif metricas["risco"] == "Baixo":
        st.success(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    else:
        st.info(f"{metricas['decisao']} — {metricas['proximo_passo']}")

    st.divider()

    rascunhos = gerar_rascunhos_com_playbook()

    st.markdown("### Rascunhos gerados")

    col_f1, col_f2, col_f3 = st.columns(3)
    canais = ["Todos"] + sorted({item.get("canal", "") for item in rascunhos if item.get("canal")})
    severidades = ["Todas"] + sorted({item.get("severidade", "") for item in rascunhos if item.get("severidade")})
    filtro_canal = col_f1.selectbox("Canal", canais)
    filtro_severidade = col_f2.selectbox("Severidade", severidades)
    filtro_ticker = col_f3.text_input("Ticker", value="")

    filtrados = []

    for item in rascunhos:
        if filtro_canal != "Todos" and item.get("canal") != filtro_canal:
            continue
        if filtro_severidade != "Todas" and item.get("severidade") != filtro_severidade:
            continue
        if filtro_ticker.strip() and filtro_ticker.strip().upper() not in item.get("ticker", ""):
            continue
        filtrados.append(item)

    st.dataframe(
        [
            {
                "canal": item.get("canal"),
                "ticker": item.get("ticker"),
                "empresa": item.get("empresa"),
                "tipo": item.get("tipo"),
                "severidade": item.get("severidade"),
                "assunto": item.get("assunto"),
                "template": item.get("template_origem"),
            }
            for item in filtrados
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Revisar e salvar rascunho")

    if filtrados:
        opcoes = [
            f"{item['canal']} | {item['ticker']} | {item['severidade']} | {item['tipo']}"
            for item in filtrados
        ]

        escolha = st.selectbox("Rascunho", opcoes)
        item = filtrados[opcoes.index(escolha)]

        assunto = st.text_input("Assunto", value=item.get("assunto", ""))
        mensagem = st.text_area("Mensagem", value=item.get("mensagem", ""), height=260)

        st.info(f"Quando usar: {item.get('quando_usar')}")
        st.warning(f"Quando evitar: {item.get('quando_evitar')}")

        col_a, col_b = st.columns(2)
        status = col_a.selectbox("Status do rascunho", ["Rascunho revisado", "Enviar para aprovação", "Manter em revisão", "Não usar"])
        responsavel = col_b.text_input("Responsável", value="Fundador")

        observacao = st.text_area(
            "Observação",
            value=f"Rascunho gerado com Playbook v{VERSAO_RASCUNHOS_PLAYBOOK_VALORIS}.",
            height=90,
        )

        item_editado = dict(item)
        item_editado["assunto"] = assunto
        item_editado["mensagem"] = mensagem

        if st.button("Salvar rascunho com playbook"):
            salvar_rascunho_playbook(
                item_editado,
                status_rascunho=status,
                responsavel=responsavel,
                observacao=observacao,
            )
            st.success("Rascunho com playbook salvo.")
            st.rerun()
    else:
        st.info("Nenhum rascunho encontrado com os filtros atuais.")

    salvos = carregar_rascunhos_playbook()
    if salvos:
        st.markdown("### Rascunhos salvos")
        st.dataframe(salvos, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Relatórios")

    col_r1, col_r2 = st.columns(2)

    if col_r1.button("Salvar relatório de rascunhos com playbook"):
        caminho = salvar_relatorio_rascunhos_playbook()
        st.success(f"Relatório salvo em {caminho}")

    if col_r2.button("Salvar manifesto de rascunhos com playbook"):
        caminho = salvar_manifesto_rascunhos_playbook()
        st.success(f"Manifesto salvo em {caminho}")

    st.download_button(
        "Baixar relatório de rascunhos com playbook (.md)",
        data=gerar_relatorio_rascunhos_playbook_markdown(),
        file_name="RELATORIO_RASCUNHOS_PLAYBOOK_VALORIS.md",
        mime="text/markdown",
    )


def executar_autoteste_rascunhos_playbook_valoris() -> Dict[str, Any]:
    return {
        "ok": True,
        "versao": VERSAO_RASCUNHOS_PLAYBOOK_VALORIS,
        "metricas": calcular_metricas_rascunhos_playbook(),
    }
