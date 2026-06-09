# onboarding_premium_valoris.py

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

import streamlit as st

from beta_insights_valoris import calcular_saude_beta_insights
from beta_feedback_valoris import calcular_saude_beta_feedback
from demo_guiada_2min_valoris import calcular_demo_2min_valoris
from analise_premium_valoris import (
    DADOS_DEMO_ANALISE_PREMIUM,
    calcular_analise_premium_valoris,
    gerar_markdown_analise_premium,
)
from launch_readiness_valoris import calcular_saude_launch_readiness


VERSAO_ONBOARDING_PREMIUM_VALORIS = "3.8.80"

CAMINHO_DECISOES_ONBOARDING = Path("decisoes_onboarding_premium_valoris.csv")
CAMINHO_MANIFESTO_ONBOARDING = Path("manifesto_onboarding_premium_valoris.json")
CAMINHO_ROTEIRO_ONBOARDING_MD = Path("ROTEIRO_ONBOARDING_PREMIUM_VALORIS.md")
CAMINHO_CHECKLIST_ONBOARDING_MD = Path("CHECKLIST_ONBOARDING_PREMIUM_VALORIS.md")
CAMINHO_ONBOARDING_JSON = Path("onboarding_premium_valoris.json")

CAMPOS_DECISAO_ONBOARDING = [
    "id",
    "data_registro",
    "score_onboarding",
    "score_clareza",
    "score_ativacao",
    "score_confianca",
    "score_reducao_friccao",
    "passos_total",
    "tempo_estimado_minutos",
    "momento_uau",
    "decisao",
    "risco",
    "proximo_passo",
    "observacoes",
]

PASSOS_ONBOARDING_PREMIUM = [
    {
        "ordem": 1,
        "titulo": "Entenda a promessa",
        "tempo_estimado": "20 segundos",
        "objetivo": "Mostrar rapidamente que a Valoris transforma dados financeiros em decisão explicável.",
        "acao_usuario": "Ler a promessa e clicar em começar análise guiada.",
        "texto_guia": "A Valoris não tenta prever o mercado. Ela organiza premissas, calcula margem de segurança e transforma isso em uma tese clara.",
        "criterio_sucesso": "Usuário entende o valor antes de preencher dados.",
    },
    {
        "ordem": 2,
        "titulo": "Use uma empresa exemplo",
        "tempo_estimado": "30 segundos",
        "objetivo": "Reduzir fricção inicial usando dados de demonstração.",
        "acao_usuario": "Carregar a empresa exemplo ou editar poucos campos principais.",
        "texto_guia": "Comece pelo exemplo. Depois você troca os dados por uma empresa real.",
        "criterio_sucesso": "Usuário não trava no preenchimento inicial.",
    },
    {
        "ordem": 3,
        "titulo": "Veja preço teto e margem",
        "tempo_estimado": "30 segundos",
        "objetivo": "Conectar valuation com decisão prática.",
        "acao_usuario": "Comparar preço atual, preço teto e margem de segurança.",
        "texto_guia": "Preço bom não é o menor preço. É preço com margem suficiente contra erro de premissa.",
        "criterio_sucesso": "Usuário entende a diferença entre preço atual e preço aceitável.",
    },
    {
        "ordem": 4,
        "titulo": "Leia a tese e os riscos",
        "tempo_estimado": "45 segundos",
        "objetivo": "Aumentar confiança e evitar score cego.",
        "acao_usuario": "Ler tese, gatilhos positivos e alertas.",
        "texto_guia": "O score resume a análise, mas a tese explica o porquê da decisão.",
        "criterio_sucesso": "Usuário entende que a ferramenta é analítica e educacional.",
    },
    {
        "ordem": 5,
        "titulo": "Exporte o relatório",
        "tempo_estimado": "25 segundos",
        "objetivo": "Transformar resultado em ativo de estudo.",
        "acao_usuario": "Baixar relatório em Markdown.",
        "texto_guia": "O relatório serve para revisar premissas, comparar empresas e acompanhar evolução da tese.",
        "criterio_sucesso": "Usuário percebe utilidade além da tela.",
    },
    {
        "ordem": 6,
        "titulo": "Registre feedback beta",
        "tempo_estimado": "40 segundos",
        "objetivo": "Converter uso em validação real do produto.",
        "acao_usuario": "Responder o feedback beta sobre clareza, utilidade, confiança e disposição de pagamento.",
        "texto_guia": "Seu feedback define a próxima prioridade da Valoris.",
        "criterio_sucesso": "Usuário vira beta tester ativo.",
    },
]

MARCOS_ATIVACAO = [
    {
        "marco": "Primeira análise gerada",
        "descricao": "Usuário viu score, tese, decisão e risco.",
        "peso": 24,
    },
    {
        "marco": "Relatório exportado",
        "descricao": "Usuário percebeu valor fora da interface.",
        "peso": 18,
    },
    {
        "marco": "Feedback registrado",
        "descricao": "Usuário virou insumo real de validação.",
        "peso": 22,
    },
    {
        "marco": "Próxima ação compreendida",
        "descricao": "Usuário sabe se deve estudar, aguardar, comparar ou evitar.",
        "peso": 20,
    },
    {
        "marco": "Confiança preservada",
        "descricao": "Usuário entendeu limitações e caráter educacional.",
        "peso": 16,
    },
]

CHECKLIST_UX_LANCAMENTO = [
    {
        "item": "Promessa clara no topo",
        "motivo": "Sem promessa clara, o usuário abandona antes de ver o valor.",
        "prioridade": "Máxima",
    },
    {
        "item": "Exemplo preenchido",
        "motivo": "Reduz fricção de início e acelera o momento uau.",
        "prioridade": "Máxima",
    },
    {
        "item": "Cards de decisão acima da explicação",
        "motivo": "O usuário precisa ver valor antes do detalhe.",
        "prioridade": "Alta",
    },
    {
        "item": "Tese e riscos em linguagem simples",
        "motivo": "Confiança vem da explicação, não só do score.",
        "prioridade": "Alta",
    },
    {
        "item": "Relatório exportável",
        "motivo": "Aumenta valor percebido e uso recorrente.",
        "prioridade": "Alta",
    },
    {
        "item": "CTA beta visível",
        "motivo": "Sem CTA, a demo não gera validação.",
        "prioridade": "Alta",
    },
]


def _limpar_texto(valor: Any) -> str:
    if valor is None:
        return ""
    return str(valor).strip()


def _garantir_csv(caminho: Path, campos: List[str]) -> None:
    if caminho.exists():
        return
    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()


def carregar_decisoes_onboarding_premium() -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_DECISOES_ONBOARDING, CAMPOS_DECISAO_ONBOARDING)
    with CAMINHO_DECISOES_ONBOARDING.open("r", newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def gerar_csv_decisoes_onboarding_premium() -> str:
    _garantir_csv(CAMINHO_DECISOES_ONBOARDING, CAMPOS_DECISAO_ONBOARDING)
    return CAMINHO_DECISOES_ONBOARDING.read_text(encoding="utf-8")


def salvar_decisao_onboarding_premium(saude: Dict[str, Any], observacoes: str = "") -> Dict[str, str]:
    _garantir_csv(CAMINHO_DECISOES_ONBOARDING, CAMPOS_DECISAO_ONBOARDING)

    registro = {
        "id": str(uuid4())[:8],
        "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score_onboarding": str(saude.get("score_onboarding", "")),
        "score_clareza": str(saude.get("score_clareza", "")),
        "score_ativacao": str(saude.get("score_ativacao", "")),
        "score_confianca": str(saude.get("score_confianca", "")),
        "score_reducao_friccao": str(saude.get("score_reducao_friccao", "")),
        "passos_total": str(saude.get("passos_total", "")),
        "tempo_estimado_minutos": str(saude.get("tempo_estimado_minutos", "")),
        "momento_uau": str(saude.get("momento_uau", "")),
        "decisao": _limpar_texto(saude.get("decisao")),
        "risco": _limpar_texto(saude.get("risco")),
        "proximo_passo": _limpar_texto(saude.get("proximo_passo")),
        "observacoes": _limpar_texto(observacoes),
    }

    with CAMINHO_DECISOES_ONBOARDING.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISAO_ONBOARDING)
        escritor.writerow(registro)

    return registro


def calcular_saude_onboarding_premium() -> Dict[str, Any]:
    analise = calcular_analise_premium_valoris(DADOS_DEMO_ANALISE_PREMIUM)
    relatorio = gerar_markdown_analise_premium(analise)

    try:
        insights = calcular_saude_beta_insights()
    except Exception as erro:
        insights = {"score_insights": 0, "feedbacks_total": 0, "erro": str(erro)}

    try:
        beta = calcular_saude_beta_feedback()
    except Exception as erro:
        beta = {"score_beta": 0, "feedbacks_total": 0, "erro": str(erro)}

    try:
        demo = calcular_demo_2min_valoris()
    except Exception as erro:
        demo = {"score_demo": 0, "erro": str(erro)}

    try:
        launch = calcular_saude_launch_readiness()
    except Exception as erro:
        launch = {"score_launch": 0, "erro": str(erro)}

    passos_total = len(PASSOS_ONBOARDING_PREMIUM)
    tempo_estimado_minutos = 4.0

    promessa_ok = PASSOS_ONBOARDING_PREMIUM[0]["titulo"] == "Entenda a promessa"
    exemplo_ok = bool(DADOS_DEMO_ANALISE_PREMIUM.get("empresa")) and analise["score_final"] > 0
    relatorio_ok = bool(relatorio) and "Relatório de Análise Premium" in relatorio
    feedback_ok = "feedback" in PASSOS_ONBOARDING_PREMIUM[-1]["titulo"].lower()
    momento_uau = analise["score_final"] > 0 and bool(analise["decisao"]) and bool(analise["tese"])

    score_clareza = 0
    score_clareza += 25 if promessa_ok else 0
    score_clareza += 20 if passos_total <= 7 else 0
    score_clareza += 25 if momento_uau else 0
    score_clareza += 15 if tempo_estimado_minutos <= 5 else 0
    score_clareza += 15 if len(CHECKLIST_UX_LANCAMENTO) >= 6 else 0
    score_clareza = min(100, score_clareza)

    score_ativacao = 0
    score_ativacao += 24 if exemplo_ok else 0
    score_ativacao += 18 if relatorio_ok else 0
    score_ativacao += 22 if feedback_ok else 0
    score_ativacao += 18 if int(demo.get("score_demo", 0) or 0) >= 80 else 0
    score_ativacao += 18 if int(beta.get("score_beta", 0) or 0) >= 60 else 0
    score_ativacao = min(100, score_ativacao)

    score_confianca = 0
    score_confianca += 28 if "risco" in analise and bool(analise["risco"]) else 0
    score_confianca += 24 if bool(analise.get("gatilhos_negativos")) else 0
    score_confianca += 22 if "educacional" in relatorio.lower() else 0
    score_confianca += 16 if int(launch.get("score_launch", 0) or 0) >= 70 else 0
    score_confianca += 10 if int(insights.get("score_insights", 0) or 0) >= 60 else 0
    score_confianca = min(100, score_confianca)

    score_reducao_friccao = 0
    score_reducao_friccao += 30 if exemplo_ok else 0
    score_reducao_friccao += 25 if passos_total <= 6 else 0
    score_reducao_friccao += 20 if tempo_estimado_minutos <= 5 else 0
    score_reducao_friccao += 15 if relatorio_ok else 0
    score_reducao_friccao += 10 if feedback_ok else 0
    score_reducao_friccao = min(100, score_reducao_friccao)

    score_onboarding = int(round(
        score_clareza * 0.28
        + score_ativacao * 0.28
        + score_confianca * 0.24
        + score_reducao_friccao * 0.20
    ))

    if score_onboarding >= 86:
        risco = "Médio controlado"
        decisao = "Onboarding premium pronto para beta fechado"
        proximo_passo = "Criar a tela/fluxo público de entrada beta com CTA claro e formulário enxuto."
    elif score_onboarding >= 72:
        risco = "Médio"
        decisao = "Onboarding promissor, mas ainda precisa teste real"
        proximo_passo = "Testar o fluxo com 3 usuários e medir onde eles travam."
    else:
        risco = "Alto"
        decisao = "Onboarding ainda fraco para lançamento"
        proximo_passo = "Reduzir etapas, simplificar linguagem e reforçar o exemplo preenchido."

    return {
        "versao": VERSAO_ONBOARDING_PREMIUM_VALORIS,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score_onboarding": score_onboarding,
        "score_clareza": score_clareza,
        "score_ativacao": score_ativacao,
        "score_confianca": score_confianca,
        "score_reducao_friccao": score_reducao_friccao,
        "passos_total": passos_total,
        "tempo_estimado_minutos": tempo_estimado_minutos,
        "momento_uau": momento_uau,
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo_passo,
        "passos": PASSOS_ONBOARDING_PREMIUM,
        "marcos_ativacao": MARCOS_ATIVACAO,
        "checklist_ux": CHECKLIST_UX_LANCAMENTO,
        "analise_demo": analise,
        "insights": insights,
        "beta": beta,
        "demo_2min": demo,
        "launch": launch,
    }


def gerar_roteiro_onboarding_markdown(saude: Dict[str, Any] | None = None) -> str:
    if saude is None:
        saude = calcular_saude_onboarding_premium()

    passos = "\n\n".join(
        [
            f"""### {item['ordem']}. {item['titulo']}

**Tempo estimado:** {item['tempo_estimado']}  
**Objetivo:** {item['objetivo']}  
**Ação do usuário:** {item['acao_usuario']}  
**Texto guia:** {item['texto_guia']}  
**Critério de sucesso:** {item['criterio_sucesso']}
"""
            for item in PASSOS_ONBOARDING_PREMIUM
        ]
    )

    marcos = "\n".join(
        [
            f"- **{item['marco']}** ({item['peso']} pts): {item['descricao']}"
            for item in MARCOS_ATIVACAO
        ]
    )

    return f"""# Roteiro Onboarding Premium — Valoris

Versão: {VERSAO_ONBOARDING_PREMIUM_VALORIS}  
Gerado em: {saude["gerado_em"]}

## Diagnóstico

Score Onboarding: {saude["score_onboarding"]}/100  
Risco: {saude["risco"]}  
Decisão: {saude["decisao"]}  
Próximo passo: {saude["proximo_passo"]}

## Objetivo

Levar o usuário do primeiro contato ao momento uau em poucos minutos: entender a promessa, ver uma análise exemplo, confiar na tese e deixar feedback beta.

## Passos

{passos}

## Marcos de ativação

{marcos}
"""


def gerar_checklist_onboarding_markdown(saude: Dict[str, Any] | None = None) -> str:
    if saude is None:
        saude = calcular_saude_onboarding_premium()

    checklist = "\n".join(
        [
            f"- [{'x' if item['prioridade'] in {'Máxima', 'Alta'} else ' '}] **{item['item']}** — {item['motivo']}"
            for item in CHECKLIST_UX_LANCAMENTO
        ]
    )

    return f"""# Checklist Onboarding Premium — Valoris

Versão: {VERSAO_ONBOARDING_PREMIUM_VALORIS}  
Gerado em: {saude["gerado_em"]}

## Status

Score Onboarding: {saude["score_onboarding"]}/100  
Decisão: {saude["decisao"]}

## Checklist

{checklist}

## Próxima ação

{saude["proximo_passo"]}
"""


def salvar_roteiro_onboarding_markdown() -> Dict[str, Any]:
    saude = calcular_saude_onboarding_premium()
    CAMINHO_ROTEIRO_ONBOARDING_MD.write_text(gerar_roteiro_onboarding_markdown(saude), encoding="utf-8")
    return {
        "ok": True,
        "arquivo": str(CAMINHO_ROTEIRO_ONBOARDING_MD),
        "score_onboarding": saude["score_onboarding"],
        "decisao": saude["decisao"],
    }


def salvar_checklist_onboarding_markdown() -> Dict[str, Any]:
    saude = calcular_saude_onboarding_premium()
    CAMINHO_CHECKLIST_ONBOARDING_MD.write_text(gerar_checklist_onboarding_markdown(saude), encoding="utf-8")
    return {
        "ok": True,
        "arquivo": str(CAMINHO_CHECKLIST_ONBOARDING_MD),
        "score_onboarding": saude["score_onboarding"],
        "decisao": saude["decisao"],
    }


def gerar_onboarding_json() -> Dict[str, Any]:
    saude = calcular_saude_onboarding_premium()
    CAMINHO_ONBOARDING_JSON.write_text(json.dumps(saude, ensure_ascii=False, indent=2), encoding="utf-8")
    return saude


def gerar_manifesto_onboarding_premium() -> Dict[str, Any]:
    saude = calcular_saude_onboarding_premium()
    manifesto = {
        "versao": VERSAO_ONBOARDING_PREMIUM_VALORIS,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "saude": saude,
        "passos": PASSOS_ONBOARDING_PREMIUM,
        "marcos_ativacao": MARCOS_ATIVACAO,
        "checklist_ux": CHECKLIST_UX_LANCAMENTO,
        "estrategia": {
            "objetivo": "Reduzir fricção e transformar a demo em ativação real.",
            "proxima_versao": "Tela pública de entrada beta ou relatório premium v2, dependendo da prioridade.",
            "regra": "Usuário precisa perceber valor antes de preencher muitos dados.",
        },
    }
    CAMINHO_MANIFESTO_ONBOARDING.write_text(json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifesto


def _injetar_css_onboarding() -> None:
    st.markdown(
        """
        <style>
            .onboarding-hero {
                padding: clamp(1.2rem, 3vw, 2.1rem);
                border-radius: 30px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    radial-gradient(circle at top left, rgba(214, 181, 109, 0.24), transparent 32%),
                    radial-gradient(circle at bottom right, rgba(80, 170, 140, 0.22), transparent 36%),
                    linear-gradient(135deg, rgba(6, 12, 23, 0.99), rgba(4, 8, 16, 0.99));
                box-shadow: 0 20px 62px rgba(0, 0, 0, 0.34);
                margin-bottom: 1rem;
            }
            .onboarding-eyebrow {
                color: #d6b56d;
                font-size: 0.74rem;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                font-weight: 880;
                margin-bottom: 0.35rem;
            }
            .onboarding-title {
                color: #f4f7fb;
                font-size: clamp(1.8rem, 5.5vw, 3.25rem);
                font-weight: 950;
                line-height: 1.02;
                letter-spacing: -0.058em;
                margin-bottom: 0.55rem;
            }
            .onboarding-subtitle {
                color: rgba(244, 247, 251, 0.75);
                font-size: clamp(0.94rem, 2.2vw, 1.06rem);
                line-height: 1.56;
                max-width: 1050px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def renderizar_onboarding_premium_valoris() -> None:
    _injetar_css_onboarding()

    st.markdown(
        f"""
        <div class="onboarding-hero">
            <div class="onboarding-eyebrow">Valoris • Onboarding Premium • v{VERSAO_ONBOARDING_PREMIUM_VALORIS}</div>
            <div class="onboarding-title">Do primeiro clique ao momento uau.</div>
            <div class="onboarding-subtitle">
                Um fluxo guiado para o beta tester entender a promessa, ver a análise premium,
                confiar na tese, exportar relatório e registrar feedback.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    saude = calcular_saude_onboarding_premium()

    st.markdown("### Diagnóstico de onboarding")
    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Score Onboarding", f"{saude['score_onboarding']}/100")

    with col_2:
        st.metric("Ativação", f"{saude['score_ativacao']}/100")

    with col_3:
        st.metric("Tempo", f"{saude['tempo_estimado_minutos']} min")

    with col_4:
        st.metric("Risco", saude["risco"])

    st.progress(saude["score_onboarding"] / 100)

    if saude["score_onboarding"] >= 86:
        st.success(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    elif saude["score_onboarding"] >= 72:
        st.warning(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    else:
        st.info(f"**{saude['decisao']}** — {saude['proximo_passo']}")

    st.divider()

    st.markdown("### Passos do onboarding")
    for passo in PASSOS_ONBOARDING_PREMIUM:
        with st.expander(f"{passo['ordem']}. {passo['titulo']} — {passo['tempo_estimado']}", expanded=passo["ordem"] == 1):
            st.write(f"**Objetivo:** {passo['objetivo']}")
            st.write(f"**Ação do usuário:** {passo['acao_usuario']}")
            st.write(f"**Texto guia:** {passo['texto_guia']}")
            st.write(f"**Critério de sucesso:** {passo['criterio_sucesso']}")

    st.markdown("### Marcos de ativação")
    st.dataframe(MARCOS_ATIVACAO, width="stretch", hide_index=True)

    st.markdown("### Checklist UX")
    st.dataframe(CHECKLIST_UX_LANCAMENTO, width="stretch", hide_index=True)

    st.divider()

    col_btn_1, col_btn_2, col_btn_3, col_btn_4 = st.columns(4)

    with col_btn_1:
        if st.button("Gerar manifesto Onboarding", key="onboarding_manifesto"):
            manifesto = gerar_manifesto_onboarding_premium()
            st.success(f"Manifesto gerado: {CAMINHO_MANIFESTO_ONBOARDING}")
            st.json({"versao": manifesto["versao"], "score_onboarding": manifesto["saude"]["score_onboarding"]})

    with col_btn_2:
        if st.button("Gerar onboarding JSON", key="onboarding_json"):
            retorno = gerar_onboarding_json()
            st.success(f"Onboarding JSON gerado: {CAMINHO_ONBOARDING_JSON}")
            st.json({"score_onboarding": retorno["score_onboarding"], "decisao": retorno["decisao"]})

    with col_btn_3:
        if st.button("Salvar roteiro .md", key="onboarding_roteiro"):
            retorno = salvar_roteiro_onboarding_markdown()
            st.success(f"Roteiro salvo: {retorno['arquivo']}")
            st.json(retorno)

    with col_btn_4:
        if st.button("Salvar checklist .md", key="onboarding_checklist"):
            retorno = salvar_checklist_onboarding_markdown()
            st.success(f"Checklist salvo: {retorno['arquivo']}")
            st.json(retorno)

    if st.button("Salvar decisão Onboarding", key="onboarding_decisao"):
        registro = salvar_decisao_onboarding_premium(saude, observacoes="Decisão gerada pelo onboarding premium.")
        st.success(f"Decisão salva: {registro['decisao']}")
        st.rerun()

    st.download_button(
        "Baixar roteiro onboarding (.md)",
        data=gerar_roteiro_onboarding_markdown(saude),
        file_name="ROTEIRO_ONBOARDING_PREMIUM_VALORIS.md",
        mime="text/markdown",
        key="download_roteiro_onboarding",
    )

    st.download_button(
        "Baixar checklist onboarding (.md)",
        data=gerar_checklist_onboarding_markdown(saude),
        file_name="CHECKLIST_ONBOARDING_PREMIUM_VALORIS.md",
        mime="text/markdown",
        key="download_checklist_onboarding",
    )

    st.download_button(
        "Baixar decisões Onboarding (.csv)",
        data=gerar_csv_decisoes_onboarding_premium(),
        file_name="decisoes_onboarding_premium_valoris.csv",
        mime="text/csv",
        key="download_decisoes_onboarding",
    )


def executar_autoteste_onboarding_premium_valoris() -> List[Dict[str, str]]:
    saude = calcular_saude_onboarding_premium()

    return [
        {
            "teste": "versao_onboarding_premium",
            "status": "OK" if VERSAO_ONBOARDING_PREMIUM_VALORIS == "3.8.80" else "FALHA",
            "detalhe": VERSAO_ONBOARDING_PREMIUM_VALORIS,
        },
        {
            "teste": "score_onboarding",
            "status": "OK" if 0 <= saude["score_onboarding"] <= 100 else "FALHA",
            "detalhe": str(saude["score_onboarding"]),
        },
        {
            "teste": "passos_onboarding",
            "status": "OK" if len(PASSOS_ONBOARDING_PREMIUM) >= 6 else "FALHA",
            "detalhe": str(len(PASSOS_ONBOARDING_PREMIUM)),
        },
        {
            "teste": "renderizador",
            "status": "OK" if callable(renderizar_onboarding_premium_valoris) else "FALHA",
            "detalhe": "renderizar_onboarding_premium_valoris",
        },
    ]
