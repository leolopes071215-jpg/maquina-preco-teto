# otimizacao_canais_valoris.py
# Valoris — Otimização de Canais v3.12.5
# ------------------------------------------------------------
# Objetivo:
# - Transformar resultados de comunicação em inteligência por canal.
# - Comparar WhatsApp, E-mail, Calendário e Resumo Executivo.
# - Medir resposta, conclusão, erro, retorno necessário e pendências.
# - Criar plano de otimização por canal antes de qualquer automação externa real.
# - Não envia mensagens automaticamente.

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict, deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st


VERSAO_OTIMIZACAO_CANAIS_VALORIS = "3.12.5"

CAMINHO_RESULTADOS = Path("resultados_comunicacoes_valoris.csv")
CAMINHO_EXECUCOES = Path("execucoes_envio_manual_notificacoes_valoris.csv")
CAMINHO_EXPORTACOES = Path("exportacoes_notificacoes_valoris.csv")
CAMINHO_APROVACOES = Path("aprovacoes_notificacoes_externas_valoris.csv")
CAMINHO_RASCUNHOS = Path("rascunhos_notificacoes_externas_valoris.csv")

CAMINHO_PLANO = Path("plano_otimizacao_canais_valoris.csv")
CAMINHO_RELATORIO = Path("RELATORIO_OTIMIZACAO_CANAIS_VALORIS.md")
CAMINHO_MANIFESTO = Path("manifesto_otimizacao_canais_valoris.json")

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

CAMPOS_PLANO = [
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


def _agora_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat(sep=" ")


def _txt(valor: Any) -> str:
    return "" if valor is None else str(valor).strip()


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


def carregar_resultados() -> List[Dict[str, str]]:
    return _ler_csv(CAMINHO_RESULTADOS, CAMPOS_RESULTADOS)


def carregar_execucoes() -> List[Dict[str, str]]:
    return _ler_csv(CAMINHO_EXECUCOES, CAMPOS_EXECUCOES)


def carregar_exportacoes() -> List[Dict[str, str]]:
    return _ler_csv(CAMINHO_EXPORTACOES, CAMPOS_EXPORTACOES)


def carregar_aprovacoes() -> List[Dict[str, str]]:
    return _ler_csv(CAMINHO_APROVACOES, CAMPOS_APROVACOES)


def carregar_rascunhos() -> List[Dict[str, str]]:
    return _ler_csv(CAMINHO_RASCUNHOS, CAMPOS_RASCUNHOS)


def carregar_planos() -> List[Dict[str, str]]:
    return _ler_csv(CAMINHO_PLANO, CAMPOS_PLANO, max_registros=1000)


def canal_normalizado(valor: Any) -> str:
    canal = _txt(valor)
    return canal or "Sem canal"


def calcular_metricas_canal(canal: str, dados: Dict[str, Any]) -> Dict[str, Any]:
    rascunhos = dados["rascunhos"]
    aprovacoes = dados["aprovacoes"]
    exportacoes = dados["exportacoes"]
    execucoes = dados["execucoes"]
    resultados = dados["resultados"]

    enviados = len([i for i in execucoes if "enviado manualmente" in _txt(i.get("status_envio")).lower()])
    respondidos = len([i for i in resultados if _txt(i.get("status_resultado")) == "Respondido"])
    concluidos = len([i for i in resultados if _txt(i.get("status_resultado")) == "Concluído"])
    sem_resposta = len([i for i in resultados if _txt(i.get("status_resultado")) == "Sem resposta"])
    demanda_retorno = len([i for i in resultados if _txt(i.get("status_resultado")) == "Demanda retorno"])
    erros = len([i for i in resultados if _txt(i.get("status_resultado")) == "Erro de canal"])

    aprovados = len([i for i in aprovacoes if "aprovado" in _txt(i.get("decisao_aprovacao")).lower()])
    exportados = len(exportacoes)
    resultados_registrados = len(resultados)

    taxa_aprovacao = _pct(aprovados, len(rascunhos))
    taxa_exportacao = _pct(exportados, aprovados)
    taxa_execucao = _pct(enviados, exportados)
    taxa_resultado = _pct(resultados_registrados, enviados)
    taxa_resposta = _pct(respondidos, enviados)
    taxa_conclusao = _pct(concluidos, enviados)
    taxa_erro = _pct(erros, enviados)

    score = 45

    if rascunhos:
        score += 8

    if aprovados:
        score += 8

    if enviados:
        score += 12

    if resultados_registrados:
        score += 15

    if respondidos:
        score += 10

    if concluidos:
        score += 10

    if sem_resposta:
        score -= min(sem_resposta * 6, 18)

    if erros:
        score -= min(erros * 15, 35)

    if enviados and not resultados_registrados:
        score -= 20

    score = max(0, min(100, int(score)))

    if not rascunhos and not enviados:
        diagnostico = "Canal sem base suficiente"
        acao = "Gerar rascunhos e executar um teste manual antes de avaliar."
        prioridade = "Baixa"
    elif erros:
        diagnostico = "Canal com erro operacional"
        acao = "Revisar destino, formato da mensagem e processo de envio antes de repetir."
        prioridade = "Alta"
    elif enviados and not resultados_registrados:
        diagnostico = "Canal sem medição pós-envio"
        acao = "Registrar resultado de cada envio manual para medir efetividade."
        prioridade = "Alta"
    elif sem_resposta and not respondidos:
        diagnostico = "Canal com baixa resposta"
        acao = "Testar nova abordagem de mensagem, assunto, horário ou canal alternativo."
        prioridade = "Média/Alta"
    elif demanda_retorno:
        diagnostico = "Canal gerou retorno acionável"
        acao = "Converter retornos em próximas ações no fluxo operacional."
        prioridade = "Média"
    elif respondidos or concluidos:
        diagnostico = "Canal promissor"
        acao = "Manter canal, documentar padrão de mensagem e repetir com controle."
        prioridade = "Baixa/Média"
    else:
        diagnostico = "Canal em validação"
        acao = "Continuar coleta de dados antes de automatizar."
        prioridade = "Média"

    return {
        "canal": canal,
        "score_canal": score,
        "rascunhos": len(rascunhos),
        "aprovados": aprovados,
        "exportados": exportados,
        "enviados": enviados,
        "resultados": resultados_registrados,
        "respondidos": respondidos,
        "concluidos": concluidos,
        "sem_resposta": sem_resposta,
        "demanda_retorno": demanda_retorno,
        "erros": erros,
        "taxa_aprovacao": taxa_aprovacao,
        "taxa_exportacao": taxa_exportacao,
        "taxa_execucao": taxa_execucao,
        "taxa_resultado": taxa_resultado,
        "taxa_resposta": taxa_resposta,
        "taxa_conclusao": taxa_conclusao,
        "taxa_erro": taxa_erro,
        "diagnostico": diagnostico,
        "acao_otimizacao": acao,
        "prioridade": prioridade,
    }


def gerar_ranking_canais() -> List[Dict[str, Any]]:
    dados_por_canal: Dict[str, Dict[str, List[Dict[str, str]]]] = defaultdict(
        lambda: {
            "rascunhos": [],
            "aprovacoes": [],
            "exportacoes": [],
            "execucoes": [],
            "resultados": [],
        }
    )

    for item in carregar_rascunhos():
        dados_por_canal[canal_normalizado(item.get("canal"))]["rascunhos"].append(item)

    for item in carregar_aprovacoes():
        dados_por_canal[canal_normalizado(item.get("canal"))]["aprovacoes"].append(item)

    for item in carregar_exportacoes():
        dados_por_canal[canal_normalizado(item.get("canal"))]["exportacoes"].append(item)

    for item in carregar_execucoes():
        dados_por_canal[canal_normalizado(item.get("canal"))]["execucoes"].append(item)

    for item in carregar_resultados():
        dados_por_canal[canal_normalizado(item.get("canal"))]["resultados"].append(item)

    ranking = [
        calcular_metricas_canal(canal, dados)
        for canal, dados in dados_por_canal.items()
    ]

    ranking.sort(
        key=lambda item: (
            -int(item.get("score_canal", 0)),
            -int(item.get("enviados", 0)),
            item.get("canal", ""),
        )
    )

    return ranking


def salvar_plano_otimizacao(item: Dict[str, Any], status_plano: str, responsavel: str, observacao: str = "") -> Path:
    _garantir_csv(CAMINHO_PLANO, CAMPOS_PLANO)

    with CAMINHO_PLANO.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_PLANO)
        escritor.writerow(
            {
                "data_hora": _agora_iso(),
                "canal": _txt(item.get("canal")),
                "score_canal": _txt(item.get("score_canal")),
                "diagnostico": _txt(item.get("diagnostico")),
                "acao_otimizacao": _txt(item.get("acao_otimizacao")),
                "prioridade": _txt(item.get("prioridade")),
                "responsavel": _txt(responsavel),
                "status_plano": _txt(status_plano),
                "observacao": _txt(observacao),
            }
        )

    return CAMINHO_PLANO


def calcular_metricas_otimizacao_canais() -> Dict[str, Any]:
    ranking = gerar_ranking_canais()
    planos = carregar_planos()

    canais = len(ranking)
    enviados = sum(int(item.get("enviados", 0)) for item in ranking)
    respondidos = sum(int(item.get("respondidos", 0)) for item in ranking)
    concluidos = sum(int(item.get("concluidos", 0)) for item in ranking)
    erros = sum(int(item.get("erros", 0)) for item in ranking)
    sem_resposta = sum(int(item.get("sem_resposta", 0)) for item in ranking)

    taxa_resposta_geral = _pct(respondidos, enviados)
    taxa_conclusao_geral = _pct(concluidos, enviados)

    melhor_canal = ranking[0]["canal"] if ranking else ""
    pior_canal = ranking[-1]["canal"] if ranking else ""

    score_medio = 0
    if ranking:
        score_medio = round(sum(int(item.get("score_canal", 0)) for item in ranking) / len(ranking), 1)

    score = int(score_medio) if ranking else 50

    if enviados:
        score += 5

    if respondidos:
        score += 5

    if erros:
        score -= min(erros * 10, 25)

    if sem_resposta:
        score -= min(sem_resposta * 4, 16)

    if planos:
        score += 5

    score = max(0, min(100, int(score)))

    if not ranking:
        risco = "Baixo"
        decisao = "Ainda não há canais com dados suficientes"
        proximo = "Executar comunicações manuais e registrar resultados antes de otimizar."
    elif erros:
        risco = "Médio"
        decisao = "Há canais com erro que precisam ser corrigidos"
        proximo = "Priorizar correção de canais com erro antes de automatizar."
    elif enviados and not respondidos and not concluidos:
        risco = "Médio"
        decisao = "Comunicações foram enviadas, mas ainda sem resposta/conclusão relevante"
        proximo = "Testar novos textos, horários ou canais alternativos."
    elif respondidos or concluidos:
        risco = "Baixo/Médio"
        decisao = "Há sinais positivos para otimização por canal"
        proximo = "Documentar o padrão do melhor canal e repetir com controle."
    else:
        risco = "Baixo/Médio"
        decisao = "Otimização ainda em fase inicial"
        proximo = "Coletar mais resultados por canal antes de qualquer automação real."

    return {
        "versao": VERSAO_OTIMIZACAO_CANAIS_VALORIS,
        "gerado_em": _agora_iso(),
        "score_otimizacao": score,
        "score_medio_canais": score_medio,
        "canais": canais,
        "enviados": enviados,
        "respondidos": respondidos,
        "concluidos": concluidos,
        "erros": erros,
        "sem_resposta": sem_resposta,
        "taxa_resposta_geral": taxa_resposta_geral,
        "taxa_conclusao_geral": taxa_conclusao_geral,
        "melhor_canal": melhor_canal,
        "pior_canal": pior_canal,
        "planos_registrados": len(planos),
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo,
    }


def gerar_relatorio_otimizacao_markdown() -> str:
    metricas = calcular_metricas_otimizacao_canais()
    ranking = gerar_ranking_canais()

    linhas = "\n".join(
        [
            f"- **{item['canal']} — score {item['score_canal']}/100**: enviados={item['enviados']}, resposta={item['taxa_resposta']}%, conclusão={item['taxa_conclusao']}%, erro={item['taxa_erro']}%. Diagnóstico: {item['diagnostico']}. Ação: {item['acao_otimizacao']}"
            for item in ranking
        ]
    ) or "- Nenhum canal com dados suficientes."

    return f"""# Otimização de Canais — Valoris

Versão: {VERSAO_OTIMIZACAO_CANAIS_VALORIS}  
Gerado em: {_agora_iso()}

## Diagnóstico

Score otimização: {metricas['score_otimizacao']}/100  
Canais: {metricas['canais']}  
Enviados: {metricas['enviados']}  
Respondidos: {metricas['respondidos']}  
Concluídos: {metricas['concluidos']}  
Erros: {metricas['erros']}  
Sem resposta: {metricas['sem_resposta']}  
Taxa de resposta geral: {metricas['taxa_resposta_geral']}%  
Taxa de conclusão geral: {metricas['taxa_conclusao_geral']}%  
Melhor canal: {metricas['melhor_canal'] or 'não definido'}  
Pior canal: {metricas['pior_canal'] or 'não definido'}  

Risco: {metricas['risco']}  
Decisão: {metricas['decisao']}  
Próximo passo: {metricas['proximo_passo']}

## Ranking por canal

{linhas}

## Estratégia

Esta versão transforma resultados de comunicação em inteligência de canal. Antes de automatizar, o Valoris precisa saber qual canal funciona melhor, qual gera resposta, qual gera erro e qual deve ser evitado ou melhorado.
"""


def salvar_relatorio_otimizacao() -> Path:
    CAMINHO_RELATORIO.write_text(gerar_relatorio_otimizacao_markdown(), encoding="utf-8")
    return CAMINHO_RELATORIO


def gerar_manifesto_otimizacao() -> Dict[str, Any]:
    return {
        "produto": "Valoris",
        "versao": VERSAO_OTIMIZACAO_CANAIS_VALORIS,
        "modulo": "otimizacao_canais_valoris",
        "data_hora": _agora_iso(),
        "metricas": calcular_metricas_otimizacao_canais(),
        "ranking_canais": gerar_ranking_canais(),
        "planos": carregar_planos(),
        "principio": "automatizar o canal errado escala ruído; otimizar antes de automatizar",
        "proxima_etapa": "playbook de comunicação por canal ou automação controlada",
    }


def salvar_manifesto_otimizacao() -> Path:
    CAMINHO_MANIFESTO.write_text(
        json.dumps(gerar_manifesto_otimizacao(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return CAMINHO_MANIFESTO


def renderizar_otimizacao_canais_valoris() -> None:
    st.subheader("Otimização de Canais")
    st.caption("Compara canais de comunicação e sugere melhorias antes de qualquer automação externa real.")

    metricas = calcular_metricas_otimizacao_canais()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Score otimização", f"{metricas['score_otimizacao']}/100")
    col2.metric("Canais", metricas["canais"])
    col3.metric("Enviados", metricas["enviados"])
    col4.metric("Resposta", f"{metricas['taxa_resposta_geral']}%")
    col5.metric("Erros", metricas["erros"])

    if metricas["risco"] == "Médio":
        st.warning(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    elif metricas["risco"] == "Baixo":
        st.success(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    else:
        st.info(f"{metricas['decisao']} — {metricas['proximo_passo']}")

    st.divider()

    ranking = gerar_ranking_canais()

    st.markdown("### Ranking por canal")

    col_f1, col_f2 = st.columns(2)
    canais = ["Todos"] + sorted({item.get("canal", "") for item in ranking if item.get("canal")})
    filtro_canal = col_f1.selectbox("Canal", canais)
    filtro_prioridade = col_f2.selectbox("Prioridade", ["Todas", "Alta", "Média/Alta", "Média", "Baixa/Média", "Baixa"])

    filtrados = []

    for item in ranking:
        if filtro_canal != "Todos" and item.get("canal") != filtro_canal:
            continue

        if filtro_prioridade != "Todas" and item.get("prioridade") != filtro_prioridade:
            continue

        filtrados.append(item)

    st.dataframe(
        [
            {
                "canal": item.get("canal"),
                "score": item.get("score_canal"),
                "enviados": item.get("enviados"),
                "resposta %": item.get("taxa_resposta"),
                "conclusão %": item.get("taxa_conclusao"),
                "erro %": item.get("taxa_erro"),
                "diagnóstico": item.get("diagnostico"),
                "prioridade": item.get("prioridade"),
                "ação": item.get("acao_otimizacao"),
            }
            for item in filtrados
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Registrar plano de otimização")

    if filtrados:
        opcoes = [
            f"{item['canal']} | score {item['score_canal']} | {item['diagnostico']}"
            for item in filtrados
        ]

        escolha = st.selectbox("Canal para otimizar", opcoes)
        item = filtrados[opcoes.index(escolha)]

        st.info(item.get("acao_otimizacao"))

        col_a, col_b = st.columns(2)
        status_plano = col_a.selectbox("Status do plano", ["Planejado", "Em execução", "Concluído", "Adiado", "Bloqueado"])
        responsavel = col_b.text_input("Responsável", value="Fundador")

        observacao = st.text_area(
            "Observação",
            value=f"Plano de otimização registrado na v{VERSAO_OTIMIZACAO_CANAIS_VALORIS}.",
            height=90,
        )

        if st.button("Salvar plano de otimização"):
            salvar_plano_otimizacao(
                item,
                status_plano=status_plano,
                responsavel=responsavel,
                observacao=observacao,
            )
            st.success("Plano de otimização registrado.")
            st.rerun()
    else:
        st.info("Nenhum canal encontrado com os filtros atuais.")

    planos = carregar_planos()
    if planos:
        st.markdown("### Planos registrados")
        st.dataframe(planos, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Relatórios")

    col_r1, col_r2 = st.columns(2)

    if col_r1.button("Salvar relatório de otimização"):
        caminho = salvar_relatorio_otimizacao()
        st.success(f"Relatório salvo em {caminho}")

    if col_r2.button("Salvar manifesto de otimização"):
        caminho = salvar_manifesto_otimizacao()
        st.success(f"Manifesto salvo em {caminho}")

    st.download_button(
        "Baixar relatório de otimização (.md)",
        data=gerar_relatorio_otimizacao_markdown(),
        file_name="RELATORIO_OTIMIZACAO_CANAIS_VALORIS.md",
        mime="text/markdown",
    )


def executar_autoteste_otimizacao_canais_valoris() -> Dict[str, Any]:
    return {
        "ok": True,
        "versao": VERSAO_OTIMIZACAO_CANAIS_VALORIS,
        "metricas": calcular_metricas_otimizacao_canais(),
    }
