# checklist_produto_vendavel_valoris.py
# Valoris — Checklist de Produto Vendável v3.13.3
# ------------------------------------------------------------
# Objetivo:
# - Avaliar se o Valoris está pronto para ser apresentado, testado e vendido em beta.
# - Transformar a demo e a jornada em critérios objetivos de produto.
# - Medir clareza, valor percebido, utilidade, confiança, risco, onboarding e prontidão comercial.
# - Registrar revisões de produto sem alterar dados financeiros reais.

from __future__ import annotations

import csv
import json
from collections import Counter, deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st


VERSAO_CHECKLIST_PRODUTO_VENDAVEL_VALORIS = "3.13.3"

CAMINHO_AVALIACOES = Path("avaliacoes_produto_vendavel_valoris.csv")
CAMINHO_RELATORIO = Path("RELATORIO_CHECKLIST_PRODUTO_VENDAVEL_VALORIS.md")
CAMINHO_MANIFESTO = Path("manifesto_checklist_produto_vendavel_valoris.json")

CAMPOS_AVALIACOES = [
    "data_hora",
    "perfil_avaliador",
    "score_produto",
    "clareza",
    "valor_percebido",
    "facilidade_uso",
    "confianca",
    "disposicao_pagar",
    "status_validacao",
    "responsavel",
    "decisao",
    "proximo_passo",
    "observacao",
]


CRITERIOS_PRODUTO: List[Dict[str, Any]] = [
    {
        "bloco": "Proposta de valor",
        "criterio": "O usuário entende em menos de 60 segundos para que o Valoris serve?",
        "peso": 10,
        "evidencia": "Jornada Beta + Demo Premium",
        "risco_se_falhar": "Produto parecer complexo demais.",
    },
    {
        "bloco": "Dor real",
        "criterio": "O produto resolve uma dor clara: transformar análise em decisão acompanhável?",
        "peso": 12,
        "evidencia": "Motor Análise + Pipeline Principal + Cockpit Principal",
        "risco_se_falhar": "Virar ferramenta interessante, mas não indispensável.",
    },
    {
        "bloco": "Fluxo guiado",
        "criterio": "Existe caminho simples para usuário novo seguir sem se perder?",
        "peso": 10,
        "evidencia": "Jornada Beta + Modos de Uso",
        "risco_se_falhar": "Abandono na primeira experiência.",
    },
    {
        "bloco": "Demonstração",
        "criterio": "Existe demo com dados exemplo que mostra o valor em 5 minutos?",
        "peso": 10,
        "evidencia": "Demo Premium",
        "risco_se_falhar": "Dificuldade de vender ou captar feedback.",
    },
    {
        "bloco": "Utilidade prática",
        "criterio": "A análise vira ação concreta, prazo, alerta ou revisão?",
        "peso": 12,
        "evidencia": "Pipeline Principal + Radar Principal + Agenda Revisões",
        "risco_se_falhar": "A análise fica bonita, mas não operacional.",
    },
    {
        "bloco": "Confiança",
        "criterio": "O produto deixa claro que não promete lucro e exige julgamento humano?",
        "peso": 10,
        "evidencia": "Textos, decisões conservadoras e etapas manuais",
        "risco_se_falhar": "Risco reputacional e expectativa errada.",
    },
    {
        "bloco": "Comunicação",
        "criterio": "Existe fluxo para comunicar, aprovar, exportar, enviar manualmente e medir resultado?",
        "peso": 8,
        "evidencia": "Cockpit Comunicação + Playbook + Resultados",
        "risco_se_falhar": "Perder rastreabilidade depois da decisão.",
    },
    {
        "bloco": "Dados e estabilidade",
        "criterio": "A base está organizada, com CSV seguro e backend preparado?",
        "peso": 8,
        "evidencia": "Repository Backend + Health Check + Release Guard",
        "risco_se_falhar": "Produto quebrar em teste com usuário.",
    },
    {
        "bloco": "Prontidão comercial",
        "criterio": "Existe uma narrativa clara de venda e uma promessa simples?",
        "peso": 10,
        "evidencia": "Demo Premium + Modos de Uso",
        "risco_se_falhar": "Produto parecer projeto técnico, não solução vendável.",
    },
    {
        "bloco": "Feedback beta",
        "criterio": "Existe um jeito de registrar avaliações e decidir próximos ajustes?",
        "peso": 10,
        "evidencia": "Checklist Produto Vendável",
        "risco_se_falhar": "Construir mais sem validar com o mercado.",
    },
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


def carregar_avaliacoes() -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_AVALIACOES, CAMPOS_AVALIACOES)
    try:
        with CAMINHO_AVALIACOES.open("r", newline="", encoding="utf-8") as arquivo:
            leitor = csv.DictReader(arquivo)
            return list(deque(leitor, maxlen=1200))
    except Exception:
        return []


def salvar_avaliacao(
    perfil_avaliador: str,
    score_produto: int,
    clareza: int,
    valor_percebido: int,
    facilidade_uso: int,
    confianca: int,
    disposicao_pagar: int,
    status_validacao: str,
    responsavel: str,
    decisao: str,
    proximo_passo: str,
    observacao: str = "",
) -> Path:
    _garantir_csv(CAMINHO_AVALIACOES, CAMPOS_AVALIACOES)

    with CAMINHO_AVALIACOES.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_AVALIACOES)
        escritor.writerow(
            {
                "data_hora": _agora_iso(),
                "perfil_avaliador": _txt(perfil_avaliador),
                "score_produto": _int(score_produto),
                "clareza": _int(clareza),
                "valor_percebido": _int(valor_percebido),
                "facilidade_uso": _int(facilidade_uso),
                "confianca": _int(confianca),
                "disposicao_pagar": _int(disposicao_pagar),
                "status_validacao": _txt(status_validacao),
                "responsavel": _txt(responsavel),
                "decisao": _txt(decisao),
                "proximo_passo": _txt(proximo_passo),
                "observacao": _txt(observacao),
            }
        )

    return CAMINHO_AVALIACOES


def carregar_metricas_externas() -> Dict[str, Dict[str, Any]]:
    metricas: Dict[str, Dict[str, Any]] = {}

    modulos = [
        ("jornada", "jornada_beta_valoris", "calcular_metricas_jornada_beta"),
        ("modos", "modos_uso_valoris", "calcular_metricas_modos_uso"),
        ("demo", "demo_premium_valoris", "calcular_metricas_demo"),
        ("cockpit_principal", "cockpit_principal_valoris", "calcular_metricas_cockpit_principal"),
        ("cockpit_comunicacao", "cockpit_comunicacao_valoris", "calcular_metricas_cockpit_comunicacao"),
    ]

    for nome, modulo, funcao in modulos:
        try:
            mod = __import__(modulo, fromlist=[funcao])
            if nome == "demo":
                metricas[nome] = getattr(mod, funcao)("Investidor Beta")
            else:
                metricas[nome] = getattr(mod, funcao)()
        except Exception:
            metricas[nome] = {}

    return metricas


def avaliar_criterios_produto() -> List[Dict[str, Any]]:
    metricas = carregar_metricas_externas()
    avaliacoes = carregar_avaliacoes()

    score_jornada = _int(metricas.get("jornada", {}).get("score_jornada"), 0)
    score_modos = _int(metricas.get("modos", {}).get("score_modos"), 0)
    score_demo = _int(metricas.get("demo", {}).get("score_demo"), 0)
    score_cockpit = _int(metricas.get("cockpit_principal", {}).get("score_cockpit"), 0)
    score_comunicacao = _int(metricas.get("cockpit_comunicacao", {}).get("score_cockpit"), 0)

    mapa_scores = {
        "Proposta de valor": max(score_jornada, score_demo),
        "Dor real": score_cockpit,
        "Fluxo guiado": max(score_jornada, score_modos),
        "Demonstração": score_demo,
        "Utilidade prática": score_cockpit,
        "Confiança": max(score_demo, score_jornada),
        "Comunicação": score_comunicacao,
        "Dados e estabilidade": score_cockpit,
        "Prontidão comercial": max(score_demo, score_modos),
        "Feedback beta": 80 if avaliacoes else 45,
    }

    avaliados = []
    for criterio in CRITERIOS_PRODUTO:
        bloco = criterio["bloco"]
        score_bloco = mapa_scores.get(bloco, 50)

        if score_bloco >= 80:
            status = "Forte"
            recomendacao = "Manter e usar como argumento da demo."
        elif score_bloco >= 65:
            status = "Funcional"
            recomendacao = "Pode apresentar, mas deve observar dúvidas do usuário."
        elif score_bloco >= 50:
            status = "Em ajuste"
            recomendacao = "Melhorar antes de vender com força."
        else:
            status = "Fraco"
            recomendacao = "Priorizar correção antes de validação externa."

        avaliados.append(
            {
                **criterio,
                "score_bloco": score_bloco,
                "status": status,
                "recomendacao": recomendacao,
            }
        )

    avaliados.sort(key=lambda item: (item["score_bloco"], -item["peso"]))
    return avaliados


def calcular_metricas_produto_vendavel() -> Dict[str, Any]:
    criterios = avaliar_criterios_produto()
    avaliacoes = carregar_avaliacoes()

    peso_total = sum(_int(c["peso"]) for c in criterios)
    score_ponderado = 0

    for criterio in criterios:
        score_ponderado += (_int(criterio["score_bloco"]) * _int(criterio["peso"]))

    score_produto = int(score_ponderado / peso_total) if peso_total else 0

    fortes = len([c for c in criterios if c["status"] == "Forte"])
    funcionais = len([c for c in criterios if c["status"] == "Funcional"])
    ajustes = len([c for c in criterios if c["status"] == "Em ajuste"])
    fracos = len([c for c in criterios if c["status"] == "Fraco"])

    scores_avaliacao = [_int(a.get("score_produto")) for a in avaliacoes if _txt(a.get("score_produto"))]
    clarezas = [_int(a.get("clareza")) for a in avaliacoes if _txt(a.get("clareza"))]
    valores = [_int(a.get("valor_percebido")) for a in avaliacoes if _txt(a.get("valor_percebido"))]
    disposicoes = [_int(a.get("disposicao_pagar")) for a in avaliacoes if _txt(a.get("disposicao_pagar"))]

    media_avaliacao = round(sum(scores_avaliacao) / len(scores_avaliacao), 1) if scores_avaliacao else 0
    media_clareza = round(sum(clarezas) / len(clarezas), 1) if clarezas else 0
    media_valor = round(sum(valores) / len(valores), 1) if valores else 0
    media_pagar = round(sum(disposicoes) / len(disposicoes), 1) if disposicoes else 0

    status_validacao = Counter(_txt(a.get("status_validacao")) for a in avaliacoes if _txt(a.get("status_validacao")))

    if score_produto >= 85 and avaliacoes:
        maturidade = "Pronto para beta externo"
        risco = "Baixo"
        decisao = "Produto pode ser apresentado para primeiros usuários beta"
        proximo = "Fazer 3 demonstrações reais e registrar feedback."
    elif score_produto >= 75:
        maturidade = "Quase vendável"
        risco = "Baixo/Médio"
        decisao = "Produto forte, mas ainda precisa de validação externa"
        proximo = "Apresentar Demo Premium para 1 pessoa real antes de vender."
    elif score_produto >= 60:
        maturidade = "Produto em lapidação"
        risco = "Médio"
        decisao = "Há valor, mas a experiência ainda precisa ficar mais clara"
        proximo = "Corrigir critérios mais fracos e repetir demo."
    else:
        maturidade = "Produto ainda técnico"
        risco = "Médio/Alto"
        decisao = "Ainda não vender; simplificar e validar proposta de valor"
        proximo = "Focar em clareza, onboarding e demo."

    return {
        "versao": VERSAO_CHECKLIST_PRODUTO_VENDAVEL_VALORIS,
        "gerado_em": _agora_iso(),
        "score_produto": score_produto,
        "maturidade": maturidade,
        "criterios": len(criterios),
        "fortes": fortes,
        "funcionais": funcionais,
        "em_ajuste": ajustes,
        "fracos": fracos,
        "avaliacoes": len(avaliacoes),
        "media_avaliacao": media_avaliacao,
        "media_clareza": media_clareza,
        "media_valor": media_valor,
        "media_disposicao_pagar": media_pagar,
        "status_validacao": dict(status_validacao),
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo,
    }


def gerar_relatorio_checklist_markdown() -> str:
    metricas = calcular_metricas_produto_vendavel()
    criterios = avaliar_criterios_produto()
    avaliacoes = carregar_avaliacoes()

    linhas_criterios = "\n".join(
        [
            f"- **{item['bloco']} — {item['status']} — {item['score_bloco']}/100**: {item['criterio']} Recomendação: {item['recomendacao']}"
            for item in criterios
        ]
    )

    linhas_avaliacoes = "\n".join(
        [
            f"- **{item['perfil_avaliador']} — score {item['score_produto']}/100 — {item['status_validacao']}**: clareza {item['clareza']}/10, valor {item['valor_percebido']}/10, pagar {item['disposicao_pagar']}/10. Decisão: {item['decisao']}"
            for item in avaliacoes[-30:]
        ]
    ) or "- Nenhuma avaliação registrada ainda."

    return f"""# Checklist de Produto Vendável — Valoris

Versão: {VERSAO_CHECKLIST_PRODUTO_VENDAVEL_VALORIS}  
Gerado em: {_agora_iso()}

## Diagnóstico

Score produto: {metricas['score_produto']}/100  
Maturidade: {metricas['maturidade']}  
Critérios: {metricas['criterios']}  
Fortes: {metricas['fortes']}  
Funcionais: {metricas['funcionais']}  
Em ajuste: {metricas['em_ajuste']}  
Fracos: {metricas['fracos']}  
Avaliações: {metricas['avaliacoes']}  

Média avaliação: {metricas['media_avaliacao']}/100  
Média clareza: {metricas['media_clareza']}/10  
Média valor percebido: {metricas['media_valor']}/10  
Média disposição a pagar: {metricas['media_disposicao_pagar']}/10  

Risco: {metricas['risco']}  
Decisão: {metricas['decisao']}  
Próximo passo: {metricas['proximo_passo']}

## Critérios avaliados

{linhas_criterios}

## Avaliações registradas

{linhas_avaliacoes}

## Estratégia

Esta versão coloca o Valoris em linguagem de produto. A pergunta deixa de ser “tem mais uma funcionalidade?” e passa a ser “isso está claro, útil, confiável e vendável para alguém de fora?”.
"""


def salvar_relatorio_checklist() -> Path:
    CAMINHO_RELATORIO.write_text(gerar_relatorio_checklist_markdown(), encoding="utf-8")
    return CAMINHO_RELATORIO


def gerar_manifesto_checklist() -> Dict[str, Any]:
    return {
        "produto": "Valoris",
        "versao": VERSAO_CHECKLIST_PRODUTO_VENDAVEL_VALORIS,
        "modulo": "checklist_produto_vendavel_valoris",
        "data_hora": _agora_iso(),
        "metricas": calcular_metricas_produto_vendavel(),
        "criterios": avaliar_criterios_produto(),
        "avaliacoes": carregar_avaliacoes(),
        "principio": "produto vendável é clareza, dor real, confiança, utilidade e disposição de uso",
        "proxima_etapa": "página de valor comercial e pitch do produto",
    }


def salvar_manifesto_checklist() -> Path:
    CAMINHO_MANIFESTO.write_text(
        json.dumps(gerar_manifesto_checklist(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return CAMINHO_MANIFESTO


def renderizar_checklist_produto_vendavel_valoris() -> None:
    st.subheader("Checklist Produto Vendável")
    st.caption("Avalia se o Valoris está pronto para beta externo, demonstração e primeira validação comercial.")

    metricas = calcular_metricas_produto_vendavel()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Score produto", f"{metricas['score_produto']}/100")
    col2.metric("Maturidade", metricas["maturidade"])
    col3.metric("Fortes", metricas["fortes"])
    col4.metric("Em ajuste", metricas["em_ajuste"])
    col5.metric("Avaliações", metricas["avaliacoes"])

    if metricas["risco"] in {"Médio", "Médio/Alto"}:
        st.warning(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    elif metricas["risco"] == "Baixo":
        st.success(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    else:
        st.info(f"{metricas['decisao']} — {metricas['proximo_passo']}")

    st.divider()

    st.markdown("### Critérios de produto vendável")

    criterios = avaliar_criterios_produto()
    st.dataframe(
        [
            {
                "bloco": item["bloco"],
                "status": item["status"],
                "score": item["score_bloco"],
                "peso": item["peso"],
                "critério": item["criterio"],
                "evidência": item["evidencia"],
                "recomendação": item["recomendacao"],
            }
            for item in criterios
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Registrar avaliação de produto")

    col_a, col_b = st.columns(2)
    perfil = col_a.selectbox(
        "Perfil do avaliador",
        ["Fundador", "Investidor iniciante", "Investidor experiente", "Pessoa de negócio", "Usuário beta externo"],
    )
    responsavel = col_b.text_input("Responsável", value="Fundador")

    clareza = st.slider("Clareza", min_value=0, max_value=10, value=8)
    valor = st.slider("Valor percebido", min_value=0, max_value=10, value=8)
    facilidade = st.slider("Facilidade de uso", min_value=0, max_value=10, value=7)
    confianca = st.slider("Confiança", min_value=0, max_value=10, value=8)
    pagar = st.slider("Disposição a pagar", min_value=0, max_value=10, value=6)

    score_manual = int(round((clareza + valor + facilidade + confianca + pagar) * 2, 0))

    status = st.selectbox(
        "Status da validação",
        ["Pronto para demo", "Precisa melhorar clareza", "Precisa melhorar valor percebido", "Precisa simplificar", "Aprovado para beta externo"],
    )

    decisao = st.text_input("Decisão", value=metricas["decisao"])
    proximo = st.text_input("Próximo passo", value=metricas["proximo_passo"])
    observacao = st.text_area(
        "Observação",
        value=f"Avaliação registrada no Checklist Produto Vendável v{VERSAO_CHECKLIST_PRODUTO_VENDAVEL_VALORIS}.",
        height=90,
    )

    st.info(f"Score da avaliação manual: {score_manual}/100")

    if st.button("Salvar avaliação de produto"):
        salvar_avaliacao(
            perfil_avaliador=perfil,
            score_produto=score_manual,
            clareza=clareza,
            valor_percebido=valor,
            facilidade_uso=facilidade,
            confianca=confianca,
            disposicao_pagar=pagar,
            status_validacao=status,
            responsavel=responsavel,
            decisao=decisao,
            proximo_passo=proximo,
            observacao=observacao,
        )
        st.success("Avaliação de produto registrada.")
        st.rerun()

    avaliacoes = carregar_avaliacoes()
    if avaliacoes:
        st.markdown("### Avaliações registradas")
        st.dataframe(avaliacoes, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Relatórios")

    col_r1, col_r2 = st.columns(2)

    if col_r1.button("Salvar relatório do checklist"):
        caminho = salvar_relatorio_checklist()
        st.success(f"Relatório salvo em {caminho}")

    if col_r2.button("Salvar manifesto do checklist"):
        caminho = salvar_manifesto_checklist()
        st.success(f"Manifesto salvo em {caminho}")

    st.download_button(
        "Baixar relatório do checklist (.md)",
        data=gerar_relatorio_checklist_markdown(),
        file_name="RELATORIO_CHECKLIST_PRODUTO_VENDAVEL_VALORIS.md",
        mime="text/markdown",
    )


def executar_autoteste_checklist_produto_vendavel_valoris() -> Dict[str, Any]:
    return {
        "ok": True,
        "versao": VERSAO_CHECKLIST_PRODUTO_VENDAVEL_VALORIS,
        "metricas": calcular_metricas_produto_vendavel(),
    }
