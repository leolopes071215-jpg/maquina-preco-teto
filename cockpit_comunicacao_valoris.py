# cockpit_comunicacao_valoris.py
# Valoris — Cockpit de Comunicação v3.12.9
# ------------------------------------------------------------
# Objetivo:
# - Consolidar toda a esteira de comunicação em uma visão executiva.
# - Unificar Playbook, Rascunhos, Aprovação Playbook, Aprovação Oficial,
#   Exportação, Envio Manual, Auditoria, Resultados e Otimização.
# - Identificar gargalos, pendências e próximo passo recomendado.
# - Não envia mensagens automaticamente.

from __future__ import annotations

import csv
import json
from collections import Counter, deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st


VERSAO_COCKPIT_COMUNICACAO_VALORIS = "3.12.9"

CAMINHO_PLAYBOOK = Path("playbook_comunicacao_valoris.csv")
CAMINHO_RASCUNHOS_PLAYBOOK = Path("rascunhos_playbook_comunicacao_valoris.csv")
CAMINHO_APROVACOES_PLAYBOOK = Path("aprovacoes_rascunhos_playbook_valoris.csv")
CAMINHO_RASCUNHOS_OFICIAIS = Path("rascunhos_notificacoes_externas_valoris.csv")
CAMINHO_APROVACOES_OFICIAIS = Path("aprovacoes_notificacoes_externas_valoris.csv")
CAMINHO_EXPORTACOES = Path("exportacoes_notificacoes_valoris.csv")
CAMINHO_EXECUCOES = Path("execucoes_envio_manual_notificacoes_valoris.csv")
CAMINHO_AUDITORIA = Path("revisoes_auditoria_comunicacoes_valoris.csv")
CAMINHO_RESULTADOS = Path("resultados_comunicacoes_valoris.csv")
CAMINHO_OTIMIZACAO = Path("plano_otimizacao_canais_valoris.csv")

CAMINHO_REVISOES = Path("revisoes_cockpit_comunicacao_valoris.csv")
CAMINHO_RELATORIO = Path("RELATORIO_COCKPIT_COMUNICACAO_VALORIS.md")
CAMINHO_MANIFESTO = Path("manifesto_cockpit_comunicacao_valoris.json")

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

CAMPOS_APROVACOES_OFICIAIS = [
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

CAMPOS_AUDITORIA = [
    "data_hora",
    "score_auditoria",
    "status_auditoria",
    "responsavel",
    "decisao",
    "observacao",
]

CAMPOS_RESULTADOS = [
    "data_hora",
    "id_rascunho",
    "canal",
    "ticker",
    "empresa",
    "tipo",
    "severidade",
    "status_resultado",
    "responsavel",
    "resposta_recebida",
    "acao_pos_envio",
    "observacao",
]

CAMPOS_OTIMIZACAO = [
    "data_hora",
    "canal",
    "score_canal",
    "diagnostico",
    "acao_otimizacao",
    "prioridade",
    "responsavel",
    "status_plano",
    "observacao",
]

CAMPOS_REVISOES = [
    "data_hora",
    "score_cockpit",
    "maturidade",
    "gargalo",
    "responsavel",
    "decisao",
    "proximo_passo",
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


def _pct(parte: int, total: int) -> float:
    if not total:
        return 0.0
    return round((parte / total) * 100, 1)


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
    return _ler_csv(CAMINHO_PLAYBOOK, CAMPOS_PLAYBOOK)


def carregar_rascunhos_playbook() -> List[Dict[str, str]]:
    return _ler_csv(CAMINHO_RASCUNHOS_PLAYBOOK, CAMPOS_RASCUNHOS_PLAYBOOK)


def carregar_aprovacoes_playbook() -> List[Dict[str, str]]:
    return _ler_csv(CAMINHO_APROVACOES_PLAYBOOK, CAMPOS_APROVACOES_PLAYBOOK)


def carregar_rascunhos_oficiais() -> List[Dict[str, str]]:
    return _ler_csv(CAMINHO_RASCUNHOS_OFICIAIS, CAMPOS_RASCUNHOS_OFICIAIS)


def carregar_aprovacoes_oficiais() -> List[Dict[str, str]]:
    return _ler_csv(CAMINHO_APROVACOES_OFICIAIS, CAMPOS_APROVACOES_OFICIAIS)


def carregar_exportacoes() -> List[Dict[str, str]]:
    return _ler_csv(CAMINHO_EXPORTACOES, CAMPOS_EXPORTACOES)


def carregar_execucoes() -> List[Dict[str, str]]:
    return _ler_csv(CAMINHO_EXECUCOES, CAMPOS_EXECUCOES)


def carregar_auditoria() -> List[Dict[str, str]]:
    return _ler_csv(CAMINHO_AUDITORIA, CAMPOS_AUDITORIA)


def carregar_resultados() -> List[Dict[str, str]]:
    return _ler_csv(CAMINHO_RESULTADOS, CAMPOS_RESULTADOS)


def carregar_otimizacao() -> List[Dict[str, str]]:
    return _ler_csv(CAMINHO_OTIMIZACAO, CAMPOS_OTIMIZACAO)


def carregar_revisoes_cockpit() -> List[Dict[str, str]]:
    return _ler_csv(CAMINHO_REVISOES, CAMPOS_REVISOES, max_registros=1000)


def carregar_metricas_externas() -> Dict[str, Dict[str, Any]]:
    metricas: Dict[str, Dict[str, Any]] = {}

    modulos = [
        ("playbook", "playbook_comunicacao_valoris", "calcular_metricas_playbook"),
        ("rascunhos_playbook", "rascunhos_playbook_valoris", "calcular_metricas_rascunhos_playbook"),
        ("aprovacao_playbook", "aprovacao_rascunhos_playbook_valoris", "calcular_metricas_aprovacao_rascunhos_playbook"),
        ("aprovacao_oficial", "aprovacao_notificacoes_valoris", "calcular_metricas_aprovacao_notificacoes"),
        ("exportacao", "exportacao_notificacoes_valoris", "calcular_metricas_exportacao"),
        ("envio_manual", "envio_manual_notificacoes_valoris", "calcular_metricas_envio_manual"),
        ("auditoria", "auditoria_comunicacoes_valoris", "calcular_metricas_auditoria"),
        ("resultados", "resultados_comunicacoes_valoris", "calcular_metricas_resultados_comunicacoes"),
        ("otimizacao", "otimizacao_canais_valoris", "calcular_metricas_otimizacao_canais"),
    ]

    for nome, modulo, funcao in modulos:
        try:
            mod = __import__(modulo, fromlist=[funcao])
            metricas[nome] = getattr(mod, funcao)()
        except Exception:
            metricas[nome] = {}

    return metricas


def _ids(campo: str, itens: List[Dict[str, str]]) -> set[str]:
    return {_txt(item.get(campo)) for item in itens if _txt(item.get(campo))}


def analisar_gargalos() -> List[Dict[str, Any]]:
    playbook = carregar_playbook()
    rascunhos_playbook = carregar_rascunhos_playbook()
    aprovacoes_playbook = carregar_aprovacoes_playbook()
    rascunhos_oficiais = carregar_rascunhos_oficiais()
    aprovacoes_oficiais = carregar_aprovacoes_oficiais()
    exportacoes = carregar_exportacoes()
    execucoes = carregar_execucoes()
    resultados = carregar_resultados()
    auditoria = carregar_auditoria()
    otimizacao = carregar_otimizacao()

    gargalos = []

    playbook_aprovado = [
        item for item in playbook
        if _txt(item.get("status_playbook")) in {"Aprovado", "Padrão oficial", "Em uso"}
    ]

    if not playbook_aprovado:
        gargalos.append(
            {
                "etapa": "Playbook",
                "status": "Atenção",
                "impacto": "Sem padrão aprovado, os rascunhos ficam menos consistentes.",
                "proxima_acao": "Aprovar pelo menos um padrão de comunicação.",
                "prioridade": "Alta",
            }
        )

    if not rascunhos_playbook:
        gargalos.append(
            {
                "etapa": "Rascunhos Playbook",
                "status": "Atenção",
                "impacto": "O playbook ainda não está gerando rascunhos operacionais.",
                "proxima_acao": "Gerar e salvar rascunho com playbook.",
                "prioridade": "Alta",
            }
        )

    aprovados_playbook = [
        item for item in aprovacoes_playbook
        if _txt(item.get("decisao_aprovacao")) == "Aprovado"
    ]
    promovidos = [
        item for item in aprovacoes_playbook
        if _txt(item.get("promovido_fluxo_oficial")) == "Sim"
    ]

    if rascunhos_playbook and not aprovados_playbook:
        gargalos.append(
            {
                "etapa": "Aprovação Playbook",
                "status": "Pendente",
                "impacto": "Há rascunhos do playbook sem aprovação.",
                "proxima_acao": "Aprovar, revisar ou bloquear rascunhos do playbook.",
                "prioridade": "Alta",
            }
        )

    if aprovados_playbook and not promovidos:
        gargalos.append(
            {
                "etapa": "Promoção Oficial",
                "status": "Pendente",
                "impacto": "Rascunhos aprovados ainda não entraram no fluxo oficial.",
                "proxima_acao": "Promover rascunhos aprovados para Notificações Externas.",
                "prioridade": "Média/Alta",
            }
        )

    if rascunhos_oficiais and not aprovacoes_oficiais:
        gargalos.append(
            {
                "etapa": "Aprovação Oficial",
                "status": "Pendente",
                "impacto": "Rascunhos oficiais ainda não foram aprovados para exportação.",
                "proxima_acao": "Aprovar rascunhos oficiais na página Aprovação Notificações.",
                "prioridade": "Alta",
            }
        )

    aprovados_oficiais = [
        item for item in aprovacoes_oficiais
        if "aprovado" in _txt(item.get("decisao_aprovacao")).lower()
    ]

    if aprovados_oficiais and not exportacoes:
        gargalos.append(
            {
                "etapa": "Exportação",
                "status": "Pendente",
                "impacto": "Aprovações oficiais existem, mas ainda não viraram pacote seguro.",
                "proxima_acao": "Exportar rascunhos aprovados para envio manual.",
                "prioridade": "Média/Alta",
            }
        )

    if exportacoes and not execucoes:
        gargalos.append(
            {
                "etapa": "Envio Manual",
                "status": "Pendente",
                "impacto": "Há pacotes exportados sem execução manual registrada.",
                "proxima_acao": "Registrar envio manual, reagendamento ou bloqueio.",
                "prioridade": "Média/Alta",
            }
        )

    envios_concluidos = [
        item for item in execucoes
        if "enviado manualmente" in _txt(item.get("status_envio")).lower()
    ]

    if envios_concluidos and not resultados:
        gargalos.append(
            {
                "etapa": "Resultados",
                "status": "Pendente",
                "impacto": "Envios foram registrados, mas ainda não há medição de resultado.",
                "proxima_acao": "Registrar resposta, sem resposta, retorno, conclusão ou erro.",
                "prioridade": "Média",
            }
        )

    if resultados and not auditoria:
        gargalos.append(
            {
                "etapa": "Auditoria",
                "status": "Pendente",
                "impacto": "Resultados existem, mas ainda falta revisão executiva/auditoria.",
                "proxima_acao": "Registrar revisão na Auditoria de Comunicações.",
                "prioridade": "Média",
            }
        )

    if resultados and not otimizacao:
        gargalos.append(
            {
                "etapa": "Otimização",
                "status": "Pendente",
                "impacto": "Há resultados, mas ainda falta plano de melhoria por canal.",
                "proxima_acao": "Salvar plano na Otimização Canais.",
                "prioridade": "Baixa/Média",
            }
        )

    if not gargalos:
        gargalos.append(
            {
                "etapa": "Esteira",
                "status": "Saudável",
                "impacto": "A comunicação está com ciclo funcional e sem gargalos críticos detectados.",
                "proxima_acao": "Continuar medindo resultados e melhorar padrões.",
                "prioridade": "Baixa",
            }
        )

    ordem = {"Alta": 1, "Média/Alta": 2, "Média": 3, "Baixa/Média": 4, "Baixa": 5}
    gargalos.sort(key=lambda item: (ordem.get(item["prioridade"], 9), item["etapa"]))

    return gargalos


def calcular_metricas_cockpit_comunicacao() -> Dict[str, Any]:
    playbook = carregar_playbook()
    rascunhos_playbook = carregar_rascunhos_playbook()
    aprovacoes_playbook = carregar_aprovacoes_playbook()
    rascunhos_oficiais = carregar_rascunhos_oficiais()
    aprovacoes_oficiais = carregar_aprovacoes_oficiais()
    exportacoes = carregar_exportacoes()
    execucoes = carregar_execucoes()
    auditoria = carregar_auditoria()
    resultados = carregar_resultados()
    otimizacao = carregar_otimizacao()
    revisoes = carregar_revisoes_cockpit()

    metricas_externas = carregar_metricas_externas()
    gargalos = analisar_gargalos()

    etapas = {
        "playbook": len(playbook),
        "rascunhos_playbook": len(rascunhos_playbook),
        "aprovacoes_playbook": len(aprovacoes_playbook),
        "rascunhos_oficiais": len(rascunhos_oficiais),
        "aprovacoes_oficiais": len(aprovacoes_oficiais),
        "exportacoes": len(exportacoes),
        "execucoes": len(execucoes),
        "auditoria": len(auditoria),
        "resultados": len(resultados),
        "otimizacao": len(otimizacao),
    }

    etapas_com_dados = len([valor for valor in etapas.values() if valor > 0])
    etapas_total = len(etapas)

    enviados = len([
        item for item in execucoes
        if "enviado manualmente" in _txt(item.get("status_envio")).lower()
    ])

    respondidos = len([
        item for item in resultados
        if _txt(item.get("status_resultado")) == "Respondido"
    ])

    concluidos = len([
        item for item in resultados
        if _txt(item.get("status_resultado")) == "Concluído"
    ])

    gargalos_alta = len([item for item in gargalos if item.get("prioridade") == "Alta"])
    gargalos_media_alta = len([item for item in gargalos if item.get("prioridade") == "Média/Alta"])

    score = 35
    score += min(etapas_com_dados * 5, 35)

    if enviados:
        score += 10

    if resultados:
        score += 10

    if auditoria:
        score += 5

    if otimizacao:
        score += 5

    if respondidos or concluidos:
        score += 5

    if gargalos_alta:
        score -= min(gargalos_alta * 12, 35)

    if gargalos_media_alta:
        score -= min(gargalos_media_alta * 7, 20)

    score = max(0, min(100, int(score)))

    cobertura = _pct(etapas_com_dados, etapas_total)
    taxa_resposta = _pct(respondidos, enviados)
    taxa_conclusao = _pct(concluidos, enviados)

    if score >= 85:
        maturidade = "Operacional avançado"
    elif score >= 70:
        maturidade = "Operacional funcional"
    elif score >= 55:
        maturidade = "Em validação"
    elif score >= 40:
        maturidade = "Inicial com gargalos"
    else:
        maturidade = "Imaturo"

    gargalo_principal = gargalos[0]["etapa"] if gargalos else "Sem gargalo"

    if gargalos and gargalos[0]["status"] != "Saudável":
        decisao = f"Gargalo principal em {gargalo_principal}"
        proximo = gargalos[0]["proxima_acao"]
        risco = "Médio" if gargalos_alta or gargalos_media_alta else "Baixo/Médio"
    else:
        decisao = "Esteira de comunicação funcional"
        proximo = "Manter ciclo de medição, otimização e playbook."
        risco = "Baixo"

    return {
        "versao": VERSAO_COCKPIT_COMUNICACAO_VALORIS,
        "gerado_em": _agora_iso(),
        "score_cockpit": score,
        "maturidade": maturidade,
        "cobertura_etapas": cobertura,
        "etapas_com_dados": etapas_com_dados,
        "etapas_total": etapas_total,
        "gargalos": len([g for g in gargalos if g.get("status") != "Saudável"]),
        "gargalos_alta": gargalos_alta,
        "gargalos_media_alta": gargalos_media_alta,
        "gargalo_principal": gargalo_principal,
        "playbook": len(playbook),
        "rascunhos_playbook": len(rascunhos_playbook),
        "aprovacoes_playbook": len(aprovacoes_playbook),
        "rascunhos_oficiais": len(rascunhos_oficiais),
        "aprovacoes_oficiais": len(aprovacoes_oficiais),
        "exportacoes": len(exportacoes),
        "execucoes": len(execucoes),
        "resultados": len(resultados),
        "auditoria": len(auditoria),
        "otimizacao": len(otimizacao),
        "enviados": enviados,
        "respondidos": respondidos,
        "concluidos": concluidos,
        "taxa_resposta": taxa_resposta,
        "taxa_conclusao": taxa_conclusao,
        "revisoes_cockpit": len(revisoes),
        "etapas": etapas,
        "metricas_externas": metricas_externas,
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo,
    }


def salvar_revisao_cockpit_comunicacao(responsavel: str, decisao: str, proximo_passo: str, observacao: str = "") -> Path:
    _garantir_csv(CAMINHO_REVISOES, CAMPOS_REVISOES)

    metricas = calcular_metricas_cockpit_comunicacao()

    with CAMINHO_REVISOES.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_REVISOES)
        escritor.writerow(
            {
                "data_hora": _agora_iso(),
                "score_cockpit": metricas["score_cockpit"],
                "maturidade": metricas["maturidade"],
                "gargalo": metricas["gargalo_principal"],
                "responsavel": _txt(responsavel),
                "decisao": _txt(decisao),
                "proximo_passo": _txt(proximo_passo),
                "observacao": _txt(observacao),
            }
        )

    return CAMINHO_REVISOES


def gerar_relatorio_cockpit_markdown() -> str:
    metricas = calcular_metricas_cockpit_comunicacao()
    gargalos = analisar_gargalos()

    linhas_gargalos = "\n".join(
        [
            f"- **{item['prioridade']} — {item['etapa']} — {item['status']}**: {item['impacto']} Próxima ação: {item['proxima_acao']}"
            for item in gargalos
        ]
    ) or "- Nenhum gargalo detectado."

    etapas = metricas["etapas"]
    linhas_etapas = "\n".join(
        [
            f"- {nome}: {valor}"
            for nome, valor in etapas.items()
        ]
    )

    return f"""# Cockpit de Comunicação — Valoris

Versão: {VERSAO_COCKPIT_COMUNICACAO_VALORIS}  
Gerado em: {_agora_iso()}

## Diagnóstico executivo

Score cockpit: {metricas['score_cockpit']}/100  
Maturidade: {metricas['maturidade']}  
Cobertura de etapas: {metricas['cobertura_etapas']}%  
Etapas com dados: {metricas['etapas_com_dados']}/{metricas['etapas_total']}  
Gargalo principal: {metricas['gargalo_principal']}  
Gargalos alta prioridade: {metricas['gargalos_alta']}  
Gargalos média/alta: {metricas['gargalos_media_alta']}  

Enviados: {metricas['enviados']}  
Respondidos: {metricas['respondidos']}  
Concluídos: {metricas['concluidos']}  
Taxa de resposta: {metricas['taxa_resposta']}%  
Taxa de conclusão: {metricas['taxa_conclusao']}%  

Risco: {metricas['risco']}  
Decisão: {metricas['decisao']}  
Próximo passo: {metricas['proximo_passo']}

## Contagem por etapa

{linhas_etapas}

## Gargalos

{linhas_gargalos}

## Estratégia

Esta versão consolida a comunicação como sistema. O Valoris passa a enxergar a esteira inteira, do playbook ao resultado, sem automatizar envios. O objetivo é identificar gargalos antes de escalar.
"""


def salvar_relatorio_cockpit() -> Path:
    CAMINHO_RELATORIO.write_text(gerar_relatorio_cockpit_markdown(), encoding="utf-8")
    return CAMINHO_RELATORIO


def gerar_manifesto_cockpit() -> Dict[str, Any]:
    return {
        "produto": "Valoris",
        "versao": VERSAO_COCKPIT_COMUNICACAO_VALORIS,
        "modulo": "cockpit_comunicacao_valoris",
        "data_hora": _agora_iso(),
        "metricas": calcular_metricas_cockpit_comunicacao(),
        "gargalos": analisar_gargalos(),
        "revisoes": carregar_revisoes_cockpit(),
        "principio": "não escalar comunicação sem visão da esteira completa",
        "proxima_etapa": "automatização controlada ou cockpit como página principal da comunicação",
    }


def salvar_manifesto_cockpit() -> Path:
    CAMINHO_MANIFESTO.write_text(
        json.dumps(gerar_manifesto_cockpit(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return CAMINHO_MANIFESTO


def renderizar_cockpit_comunicacao_valoris() -> None:
    st.subheader("Cockpit Comunicação")
    st.caption("Visão executiva da esteira completa: playbook, rascunhos, aprovações, exportações, envios, resultados e otimização.")

    metricas = calcular_metricas_cockpit_comunicacao()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Score cockpit", f"{metricas['score_cockpit']}/100")
    col2.metric("Maturidade", metricas["maturidade"])
    col3.metric("Cobertura", f"{metricas['cobertura_etapas']}%")
    col4.metric("Gargalos", metricas["gargalos"])
    col5.metric("Resposta", f"{metricas['taxa_resposta']}%")

    if metricas["risco"] == "Médio":
        st.warning(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    elif metricas["risco"] == "Baixo":
        st.success(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    else:
        st.info(f"{metricas['decisao']} — {metricas['proximo_passo']}")

    st.divider()

    st.markdown("### Esteira de comunicação")

    etapas = metricas["etapas"]

    tabela_etapas = [
        {"etapa": "Playbook Comunicação", "registros": etapas["playbook"], "objetivo": "Padrões de comunicação por canal"},
        {"etapa": "Rascunhos Playbook", "registros": etapas["rascunhos_playbook"], "objetivo": "Rascunhos gerados com template"},
        {"etapa": "Aprovação Playbook", "registros": etapas["aprovacoes_playbook"], "objetivo": "Aprovação e promoção para fluxo oficial"},
        {"etapa": "Notificações Externas", "registros": etapas["rascunhos_oficiais"], "objetivo": "Rascunhos oficiais"},
        {"etapa": "Aprovação Notificações", "registros": etapas["aprovacoes_oficiais"], "objetivo": "Aprovação oficial antes de exportar"},
        {"etapa": "Exportação Notificações", "registros": etapas["exportacoes"], "objetivo": "Pacote seguro para envio manual"},
        {"etapa": "Envio Manual", "registros": etapas["execucoes"], "objetivo": "Registro de execução manual"},
        {"etapa": "Resultados Comunicações", "registros": etapas["resultados"], "objetivo": "Medição de retorno"},
        {"etapa": "Auditoria Comunicações", "registros": etapas["auditoria"], "objetivo": "Rastreabilidade e revisão"},
        {"etapa": "Otimização Canais", "registros": etapas["otimizacao"], "objetivo": "Melhoria por canal"},
    ]

    st.dataframe(tabela_etapas, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Gargalos e próximas ações")

    gargalos = analisar_gargalos()

    st.dataframe(
        [
            {
                "prioridade": item.get("prioridade"),
                "etapa": item.get("etapa"),
                "status": item.get("status"),
                "impacto": item.get("impacto"),
                "próxima ação": item.get("proxima_acao"),
            }
            for item in gargalos
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Indicadores de comunicação")

    col_i1, col_i2, col_i3, col_i4 = st.columns(4)
    col_i1.metric("Enviados", metricas["enviados"])
    col_i2.metric("Respondidos", metricas["respondidos"])
    col_i3.metric("Concluídos", metricas["concluidos"])
    col_i4.metric("Taxa conclusão", f"{metricas['taxa_conclusao']}%")

    st.divider()

    st.markdown("### Registrar revisão do cockpit")

    col_a, col_b = st.columns(2)
    responsavel = col_a.text_input("Responsável", value="Fundador")
    decisao = col_b.text_input("Decisão", value=metricas["decisao"])

    proximo = st.text_input("Próximo passo", value=metricas["proximo_passo"])
    observacao = st.text_area(
        "Observação",
        value=f"Revisão registrada no Cockpit Comunicação v{VERSAO_COCKPIT_COMUNICACAO_VALORIS}.",
        height=90,
    )

    if st.button("Salvar revisão do cockpit"):
        salvar_revisao_cockpit_comunicacao(
            responsavel=responsavel,
            decisao=decisao,
            proximo_passo=proximo,
            observacao=observacao,
        )
        st.success("Revisão do cockpit registrada.")
        st.rerun()

    revisoes = carregar_revisoes_cockpit()
    if revisoes:
        st.markdown("### Revisões registradas")
        st.dataframe(revisoes, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Relatórios")

    col_r1, col_r2 = st.columns(2)

    if col_r1.button("Salvar relatório do cockpit"):
        caminho = salvar_relatorio_cockpit()
        st.success(f"Relatório salvo em {caminho}")

    if col_r2.button("Salvar manifesto do cockpit"):
        caminho = salvar_manifesto_cockpit()
        st.success(f"Manifesto salvo em {caminho}")

    st.download_button(
        "Baixar relatório do cockpit (.md)",
        data=gerar_relatorio_cockpit_markdown(),
        file_name="RELATORIO_COCKPIT_COMUNICACAO_VALORIS.md",
        mime="text/markdown",
    )


def executar_autoteste_cockpit_comunicacao_valoris() -> Dict[str, Any]:
    return {
        "ok": True,
        "versao": VERSAO_COCKPIT_COMUNICACAO_VALORIS,
        "metricas": calcular_metricas_cockpit_comunicacao(),
    }
