# jornada_beta_valoris.py
# Valoris — Jornada Guiada Beta v3.13.0
# ------------------------------------------------------------
# Objetivo:
# - Transformar o Valoris em uma experiência guiada para usuário beta.
# - Mostrar o que fazer agora, em qual etapa o usuário está e qual próximo passo seguir.
# - Consolidar análise, pipeline, alertas, comunicação e cockpits.
# - Não altera decisões financeiras automaticamente.
# - Não envia mensagens automaticamente.

from __future__ import annotations

import csv
import json
from collections import Counter, deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st


VERSAO_JORNADA_BETA_VALORIS = "3.13.0"

CAMINHO_PROGRESSO = Path("progresso_jornada_beta_valoris.csv")
CAMINHO_RELATORIO = Path("RELATORIO_JORNADA_BETA_VALORIS.md")
CAMINHO_MANIFESTO = Path("manifesto_jornada_beta_valoris.json")

CAMPOS_PROGRESSO = [
    "data_hora",
    "etapa",
    "status",
    "responsavel",
    "decisao",
    "proximo_passo",
    "observacao",
]

ARQUIVOS_SINAIS = {
    "analises": [
        "analises_motor_ativos_valoris.csv",
        "historico_analises_valoris.csv",
    ],
    "watchlist": [
        "watchlist_fundadores_valoris.csv",
    ],
    "pipeline": [
        "pipeline_acoes_valoris.csv",
        "acoes_pipeline_valoris.csv",
    ],
    "alertas": [
        "alertas_revisoes_valoris.csv",
        "tratamentos_alertas_radar_valoris.csv",
    ],
    "notificacoes": [
        "rascunhos_notificacoes_externas_valoris.csv",
        "rascunhos_playbook_comunicacao_valoris.csv",
    ],
    "aprovacoes": [
        "aprovacoes_notificacoes_externas_valoris.csv",
        "aprovacoes_rascunhos_playbook_valoris.csv",
    ],
    "exportacoes": [
        "exportacoes_notificacoes_valoris.csv",
    ],
    "envios": [
        "execucoes_envio_manual_notificacoes_valoris.csv",
    ],
    "resultados": [
        "resultados_comunicacoes_valoris.csv",
    ],
    "cockpits": [
        "revisoes_cockpit_comunicacao_valoris.csv",
        "decisoes_cockpit_principal_valoris.csv",
        "revisoes_cockpit_principal_valoris.csv",
    ],
}


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


def _ler_csv_generico(caminho: Path, max_registros: int = 3000) -> List[Dict[str, str]]:
    if not caminho.exists():
        return []

    try:
        with caminho.open("r", newline="", encoding="utf-8") as arquivo:
            leitor = csv.DictReader(arquivo)
            return list(deque(leitor, maxlen=max_registros))
    except Exception:
        return []


def _contar_linhas_csv(caminho: Path) -> int:
    return len(_ler_csv_generico(caminho))


def _somar_registros(possiveis_caminhos: List[str]) -> int:
    total = 0

    for item in possiveis_caminhos:
        total += _contar_linhas_csv(Path(item))

    return total


def carregar_progresso() -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_PROGRESSO, CAMPOS_PROGRESSO)

    try:
        with CAMINHO_PROGRESSO.open("r", newline="", encoding="utf-8") as arquivo:
            leitor = csv.DictReader(arquivo)
            return list(deque(leitor, maxlen=1000))
    except Exception:
        return []


def salvar_progresso(etapa: str, status: str, responsavel: str, decisao: str, proximo_passo: str, observacao: str = "") -> Path:
    _garantir_csv(CAMINHO_PROGRESSO, CAMPOS_PROGRESSO)

    with CAMINHO_PROGRESSO.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_PROGRESSO)
        escritor.writerow(
            {
                "data_hora": _agora_iso(),
                "etapa": _txt(etapa),
                "status": _txt(status),
                "responsavel": _txt(responsavel),
                "decisao": _txt(decisao),
                "proximo_passo": _txt(proximo_passo),
                "observacao": _txt(observacao),
            }
        )

    return CAMINHO_PROGRESSO


def carregar_metricas_externas() -> Dict[str, Dict[str, Any]]:
    metricas: Dict[str, Dict[str, Any]] = {}

    modulos = [
        ("cockpit_principal", "cockpit_principal_valoris", "calcular_metricas_cockpit_principal"),
        ("cockpit_comunicacao", "cockpit_comunicacao_valoris", "calcular_metricas_cockpit_comunicacao"),
        ("analise_principal", "analise_principal_valoris", "calcular_metricas_analise_principal"),
        ("pipeline_principal", "pipeline_principal_valoris", "calcular_metricas_pipeline_principal"),
        ("radar_principal", "radar_principal_valoris", "calcular_metricas_radar_principal"),
        ("alertas_radar", "alertas_automaticos_radar_valoris", "calcular_metricas_alertas_radar"),
        ("resultados_comunicacoes", "resultados_comunicacoes_valoris", "calcular_metricas_resultados_comunicacoes"),
        ("otimizacao_canais", "otimizacao_canais_valoris", "calcular_metricas_otimizacao_canais"),
        ("playbook", "playbook_comunicacao_valoris", "calcular_metricas_playbook"),
    ]

    for nome, modulo, funcao in modulos:
        try:
            mod = __import__(modulo, fromlist=[funcao])
            metricas[nome] = getattr(mod, funcao)()
        except Exception:
            metricas[nome] = {}

    return metricas


def contar_sinais_operacionais() -> Dict[str, int]:
    return {
        nome: _somar_registros(caminhos)
        for nome, caminhos in ARQUIVOS_SINAIS.items()
    }


def status_etapa(condicao: bool, parcial: bool = False) -> str:
    if condicao:
        return "Concluída"
    if parcial:
        return "Em andamento"
    return "Pendente"


def gerar_etapas_jornada() -> List[Dict[str, Any]]:
    sinais = contar_sinais_operacionais()
    progresso = carregar_progresso()
    metricas = carregar_metricas_externas()

    revisoes_por_etapa = Counter(_txt(item.get("etapa")) for item in progresso if _txt(item.get("etapa")))

    score_cockpit_principal = _int(metricas.get("cockpit_principal", {}).get("score_cockpit"), 0)
    score_cockpit_comunicacao = _int(metricas.get("cockpit_comunicacao", {}).get("score_cockpit"), 0)

    etapas = [
        {
            "ordem": 1,
            "etapa": "Comece aqui",
            "objetivo": "Entender o produto e iniciar a experiência beta.",
            "status": status_etapa(bool(progresso), parcial=bool(sinais["analises"] or sinais["pipeline"])),
            "sinal": len(progresso),
            "pagina_recomendada": "Jornada Beta",
            "proximo_passo": "Registrar a primeira revisão da jornada beta.",
        },
        {
            "ordem": 2,
            "etapa": "Analisar ativo",
            "objetivo": "Gerar análise, tese, preço teto ou decisão inicial.",
            "status": status_etapa(sinais["analises"] > 0),
            "sinal": sinais["analises"],
            "pagina_recomendada": "Motor Análise Ativos / Análise Principal",
            "proximo_passo": "Analisar pelo menos um ativo real e salvar o histórico.",
        },
        {
            "ordem": 3,
            "etapa": "Organizar decisão",
            "objetivo": "Transformar análise em watchlist, pipeline ou ação concreta.",
            "status": status_etapa(sinais["pipeline"] > 0 or sinais["watchlist"] > 0, parcial=sinais["analises"] > 0),
            "sinal": sinais["pipeline"] + sinais["watchlist"],
            "pagina_recomendada": "Pipeline Principal / Watchlist Fundadores",
            "proximo_passo": "Colocar uma análise em acompanhamento ou pipeline.",
        },
        {
            "ordem": 4,
            "etapa": "Acompanhar risco",
            "objetivo": "Monitorar alertas, revisões, pendências e próximos movimentos.",
            "status": status_etapa(sinais["alertas"] > 0, parcial=sinais["pipeline"] > 0),
            "sinal": sinais["alertas"],
            "pagina_recomendada": "Radar Principal / Alertas Radar / Agenda Revisões",
            "proximo_passo": "Gerar ou tratar pelo menos um alerta/revisão.",
        },
        {
            "ordem": 5,
            "etapa": "Comunicar decisão",
            "objetivo": "Gerar rascunho, aprovar, exportar e registrar envio manual.",
            "status": status_etapa(
                sinais["envios"] > 0,
                parcial=(sinais["notificacoes"] + sinais["aprovacoes"] + sinais["exportacoes"] > 0),
            ),
            "sinal": sinais["notificacoes"] + sinais["aprovacoes"] + sinais["exportacoes"] + sinais["envios"],
            "pagina_recomendada": "Cockpit Comunicação",
            "proximo_passo": "Gerar rascunho, aprovar, exportar e registrar envio manual.",
        },
        {
            "ordem": 6,
            "etapa": "Medir resultado",
            "objetivo": "Registrar resposta, retorno, conclusão, erro ou ausência de resposta.",
            "status": status_etapa(sinais["resultados"] > 0, parcial=sinais["envios"] > 0),
            "sinal": sinais["resultados"],
            "pagina_recomendada": "Resultados Comunicações / Otimização Canais",
            "proximo_passo": "Registrar resultado pós-envio e plano de melhoria por canal.",
        },
        {
            "ordem": 7,
            "etapa": "Ver cockpit final",
            "objetivo": "Enxergar o sistema completo e decidir a próxima ação.",
            "status": status_etapa(
                score_cockpit_principal >= 70 or score_cockpit_comunicacao >= 70 or sinais["cockpits"] > 0,
                parcial=score_cockpit_principal > 0 or score_cockpit_comunicacao > 0,
            ),
            "sinal": max(score_cockpit_principal, score_cockpit_comunicacao, sinais["cockpits"]),
            "pagina_recomendada": "Cockpit Principal / Cockpit Comunicação",
            "proximo_passo": "Registrar revisão executiva e decidir se o beta está pronto para usuário externo.",
        },
    ]

    for etapa in etapas:
        etapa["revisoes"] = revisoes_por_etapa.get(etapa["etapa"], 0)

    return etapas


def calcular_metricas_jornada_beta() -> Dict[str, Any]:
    etapas = gerar_etapas_jornada()
    sinais = contar_sinais_operacionais()
    progresso = carregar_progresso()

    concluidas = len([e for e in etapas if e["status"] == "Concluída"])
    andamento = len([e for e in etapas if e["status"] == "Em andamento"])
    pendentes = len([e for e in etapas if e["status"] == "Pendente"])

    score = 35
    score += concluidas * 8
    score += andamento * 4

    if progresso:
        score += 8

    if sinais["analises"]:
        score += 7

    if sinais["pipeline"] or sinais["watchlist"]:
        score += 5

    if sinais["resultados"]:
        score += 5

    score = max(0, min(100, int(score)))

    if score >= 85:
        maturidade = "Beta forte"
    elif score >= 70:
        maturidade = "Beta funcional"
    elif score >= 55:
        maturidade = "Beta em estruturação"
    elif score >= 40:
        maturidade = "Protótipo guiado"
    else:
        maturidade = "Inicial"

    proxima_etapa = next((e for e in etapas if e["status"] != "Concluída"), etapas[-1])

    if pendentes >= 4:
        risco = "Médio"
        decisao = "A jornada ainda precisa de uso operacional real"
        proximo = proxima_etapa["proximo_passo"]
    elif andamento or pendentes:
        risco = "Baixo/Médio"
        decisao = "Jornada beta utilizável, mas ainda incompleta"
        proximo = proxima_etapa["proximo_passo"]
    else:
        risco = "Baixo"
        decisao = "Jornada beta completa para validação inicial"
        proximo = "Preparar demo com dados exemplo e simplificação do menu."

    return {
        "versao": VERSAO_JORNADA_BETA_VALORIS,
        "gerado_em": _agora_iso(),
        "score_jornada": score,
        "maturidade": maturidade,
        "etapas": len(etapas),
        "concluidas": concluidas,
        "em_andamento": andamento,
        "pendentes": pendentes,
        "revisoes": len(progresso),
        "proxima_etapa": proxima_etapa["etapa"],
        "pagina_recomendada": proxima_etapa["pagina_recomendada"],
        "sinais": sinais,
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo,
    }


def gerar_relatorio_jornada_markdown() -> str:
    metricas = calcular_metricas_jornada_beta()
    etapas = gerar_etapas_jornada()

    linhas_etapas = "\n".join(
        [
            f"- **{item['ordem']}. {item['etapa']} — {item['status']}**: {item['objetivo']} Página: {item['pagina_recomendada']}. Próximo passo: {item['proximo_passo']}"
            for item in etapas
        ]
    )

    return f"""# Jornada Guiada Beta — Valoris

Versão: {VERSAO_JORNADA_BETA_VALORIS}  
Gerado em: {_agora_iso()}

## Diagnóstico

Score jornada: {metricas['score_jornada']}/100  
Maturidade: {metricas['maturidade']}  
Etapas: {metricas['etapas']}  
Concluídas: {metricas['concluidas']}  
Em andamento: {metricas['em_andamento']}  
Pendentes: {metricas['pendentes']}  
Revisões registradas: {metricas['revisoes']}  

Próxima etapa: {metricas['proxima_etapa']}  
Página recomendada: {metricas['pagina_recomendada']}  
Risco: {metricas['risco']}  
Decisão: {metricas['decisao']}  
Próximo passo: {metricas['proximo_passo']}

## Etapas da jornada

{linhas_etapas}

## Estratégia

Esta versão muda o foco de construção técnica para experiência de produto. O usuário beta precisa saber exatamente o que fazer, onde clicar e qual resultado esperar.
"""


def salvar_relatorio_jornada() -> Path:
    CAMINHO_RELATORIO.write_text(gerar_relatorio_jornada_markdown(), encoding="utf-8")
    return CAMINHO_RELATORIO


def gerar_manifesto_jornada() -> Dict[str, Any]:
    return {
        "produto": "Valoris",
        "versao": VERSAO_JORNADA_BETA_VALORIS,
        "modulo": "jornada_beta_valoris",
        "data_hora": _agora_iso(),
        "metricas": calcular_metricas_jornada_beta(),
        "etapas": gerar_etapas_jornada(),
        "progresso": carregar_progresso(),
        "principio": "produto bom não é só poderoso; é guiado, claro e validável",
        "proxima_etapa": "simplificação do menu e modos de uso",
    }


def salvar_manifesto_jornada() -> Path:
    CAMINHO_MANIFESTO.write_text(
        json.dumps(gerar_manifesto_jornada(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return CAMINHO_MANIFESTO


def renderizar_jornada_beta_valoris() -> None:
    st.subheader("Jornada Beta")
    st.caption("Guia operacional para transformar o Valoris em produto beta utilizável.")

    metricas = calcular_metricas_jornada_beta()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Score jornada", f"{metricas['score_jornada']}/100")
    col2.metric("Maturidade", metricas["maturidade"])
    col3.metric("Concluídas", metricas["concluidas"])
    col4.metric("Em andamento", metricas["em_andamento"])
    col5.metric("Pendentes", metricas["pendentes"])

    if metricas["risco"] == "Médio":
        st.warning(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    elif metricas["risco"] == "Baixo":
        st.success(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    else:
        st.info(f"{metricas['decisao']} — {metricas['proximo_passo']}")

    st.markdown(
        f"""
### Próximo movimento recomendado

**Etapa:** {metricas['proxima_etapa']}  
**Página:** {metricas['pagina_recomendada']}  
**Ação:** {metricas['proximo_passo']}
"""
    )

    st.divider()

    st.markdown("### Etapas da jornada beta")

    etapas = gerar_etapas_jornada()

    st.dataframe(
        [
            {
                "ordem": item["ordem"],
                "etapa": item["etapa"],
                "status": item["status"],
                "sinal": item["sinal"],
                "revisões": item["revisoes"],
                "página recomendada": item["pagina_recomendada"],
                "próximo passo": item["proximo_passo"],
            }
            for item in etapas
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Registrar avanço da jornada")

    nomes_etapas = [item["etapa"] for item in etapas]
    etapa = st.selectbox("Etapa", nomes_etapas)
    etapa_info = next((item for item in etapas if item["etapa"] == etapa), etapas[0])

    col_a, col_b = st.columns(2)
    status = col_a.selectbox("Status", ["Não iniciado", "Em andamento", "Concluído", "Bloqueado", "Revisar"])
    responsavel = col_b.text_input("Responsável", value="Fundador")

    decisao = st.text_input("Decisão", value=f"Avanço registrado em {etapa}.")
    proximo = st.text_input("Próximo passo", value=etapa_info["proximo_passo"])
    observacao = st.text_area(
        "Observação",
        value=f"Registro da Jornada Beta v{VERSAO_JORNADA_BETA_VALORIS}.",
        height=90,
    )

    if st.button("Salvar avanço da jornada"):
        salvar_progresso(
            etapa=etapa,
            status=status,
            responsavel=responsavel,
            decisao=decisao,
            proximo_passo=proximo,
            observacao=observacao,
        )
        st.success("Avanço da jornada registrado.")
        st.rerun()

    progresso = carregar_progresso()
    if progresso:
        st.markdown("### Histórico de avanços")
        st.dataframe(progresso, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Sinais operacionais")

    sinais = contar_sinais_operacionais()
    st.dataframe(
        [{"bloco": nome, "registros": total} for nome, total in sinais.items()],
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Relatórios")

    col_r1, col_r2 = st.columns(2)

    if col_r1.button("Salvar relatório da jornada"):
        caminho = salvar_relatorio_jornada()
        st.success(f"Relatório salvo em {caminho}")

    if col_r2.button("Salvar manifesto da jornada"):
        caminho = salvar_manifesto_jornada()
        st.success(f"Manifesto salvo em {caminho}")

    st.download_button(
        "Baixar relatório da jornada (.md)",
        data=gerar_relatorio_jornada_markdown(),
        file_name="RELATORIO_JORNADA_BETA_VALORIS.md",
        mime="text/markdown",
    )


def executar_autoteste_jornada_beta_valoris() -> Dict[str, Any]:
    return {
        "ok": True,
        "versao": VERSAO_JORNADA_BETA_VALORIS,
        "metricas": calcular_metricas_jornada_beta(),
    }
