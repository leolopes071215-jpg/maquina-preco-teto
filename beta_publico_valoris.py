# beta_publico_valoris.py

from __future__ import annotations

import csv
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

import streamlit as st

from onboarding_premium_valoris import calcular_saude_onboarding_premium
from beta_insights_valoris import calcular_saude_beta_insights
from beta_feedback_valoris import calcular_saude_beta_feedback
from demo_guiada_2min_valoris import calcular_demo_2min_valoris
from analise_premium_valoris import calcular_saude_analise_premium
from launch_readiness_valoris import calcular_saude_launch_readiness


VERSAO_BETA_PUBLICO_VALORIS = "3.8.81"

CAMINHO_LEADS_BETA_PUBLICO = Path("leads_beta_publico_valoris.csv")
CAMINHO_DECISOES_BETA_PUBLICO = Path("decisoes_beta_publico_valoris.csv")
CAMINHO_MANIFESTO_BETA_PUBLICO = Path("manifesto_beta_publico_valoris.json")
CAMINHO_COPY_BETA_PUBLICO_MD = Path("COPY_BETA_PUBLICO_VALORIS.md")
CAMINHO_PAGINA_BETA_PUBLICO_MD = Path("PAGINA_BETA_PUBLICO_VALORIS.md")
CAMINHO_CHECKLIST_BETA_PUBLICO_MD = Path("CHECKLIST_BETA_PUBLICO_VALORIS.md")

CAMPOS_LEADS_BETA_PUBLICO = [
    "id",
    "data_registro",
    "nome",
    "email",
    "perfil",
    "nivel_investidor",
    "principal_dor",
    "objetivo",
    "aceita_contato",
    "origem",
    "status",
]

CAMPOS_DECISAO_BETA_PUBLICO = [
    "id",
    "data_registro",
    "score_beta_publico",
    "score_copy",
    "score_conversao",
    "score_produto",
    "score_validacao",
    "leads_total",
    "risco",
    "decisao",
    "proximo_passo",
    "observacoes",
]

PERFIS_LEAD_BETA = [
    "Investidor iniciante",
    "Investidor intermediário",
    "Investidor avançado",
    "Estudante de finanças",
    "Criador de conteúdo financeiro",
    "Profissional do mercado",
    "Curioso em valuation",
]

NIVEIS_LEAD_BETA = [
    "Ainda não invisto",
    "Invisto há menos de 1 ano",
    "Invisto entre 1 e 3 anos",
    "Invisto há mais de 3 anos",
    "Já faço análise fundamentalista",
]

COPY_BETA_PUBLICO = {
    "headline": "Analise ações com mais método, margem de segurança e clareza.",
    "subheadline": "A Valoris transforma dados financeiros em preço teto, tese, riscos, decisão e relatório exportável.",
    "promessa": "Pare de depender de achismo. Use uma análise estruturada para decidir se uma ação merece estudo, espera ou distância.",
    "cta_principal": "Entrar na lista beta",
    "cta_secundario": "Ver demonstração de 2 minutos",
    "disclaimer": "Ferramenta educacional. Não é recomendação personalizada de investimento.",
}

BLOCOS_PAGINA_BETA = [
    {
        "bloco": "Dor",
        "titulo": "Você sabe quando uma boa empresa está cara?",
        "texto": "Muitos investidores compram boas empresas sem margem de segurança, ou desistem de estudar porque os dados parecem confusos.",
        "objetivo": "Conectar com a dor real do investidor.",
    },
    {
        "bloco": "Solução",
        "titulo": "A Valoris organiza a decisão.",
        "texto": "Você informa premissas principais e recebe preço teto, margem de segurança, score, tese, riscos e próximo passo.",
        "objetivo": "Mostrar clareza do produto.",
    },
    {
        "bloco": "Prova",
        "titulo": "Não é só uma calculadora.",
        "texto": "A ferramenta explica por que a decisão foi tomada e gera um relatório para estudo e acompanhamento.",
        "objetivo": "Diferenciar de planilha simples.",
    },
    {
        "bloco": "Confiança",
        "titulo": "Método conservador e transparente.",
        "texto": "A análise mostra limitações, riscos e premissas. O objetivo é melhorar seu processo, não prever o mercado.",
        "objetivo": "Reduzir objeção e risco jurídico.",
    },
    {
        "bloco": "Beta",
        "titulo": "Entre como beta tester.",
        "texto": "A versão beta será liberada para poucas pessoas que querem testar, criticar e ajudar a construir a ferramenta.",
        "objetivo": "Converter interesse em lead.",
    },
]

OBJECOES_BETA_PUBLICO = [
    {
        "objecao": "Isso recomenda compra?",
        "resposta": "Não. A Valoris é uma ferramenta educacional de análise. Ela organiza dados, riscos e premissas para apoiar seu estudo.",
    },
    {
        "objecao": "Preciso ser avançado?",
        "resposta": "Não. O fluxo é guiado, com exemplo preenchido e explicação em linguagem simples.",
    },
    {
        "objecao": "Os dados são automáticos?",
        "resposta": "A primeira fase prioriza clareza, tese e validação. Dados reais automáticos entram de forma controlada depois.",
    },
    {
        "objecao": "Por que entrar no beta?",
        "resposta": "Para testar antes, influenciar prioridades e ajudar a moldar uma ferramenta realmente útil.",
    },
]

CHECKLIST_PUBLICO = [
    "Headline clara",
    "Subheadline explicando o resultado",
    "CTA principal visível",
    "Disclaimers educacionais",
    "Promessa sem garantia de lucro",
    "Formulário simples",
    "Demonstração de 2 minutos",
    "Benefício do beta tester claro",
]


def _limpar_texto(valor: Any) -> str:
    if valor is None:
        return ""
    return str(valor).strip()


def _email_valido(email: str) -> bool:
    email = _limpar_texto(email).lower()
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))


def _garantir_csv(caminho: Path, campos: List[str]) -> None:
    if caminho.exists():
        return
    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()


def carregar_leads_beta_publico() -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_LEADS_BETA_PUBLICO, CAMPOS_LEADS_BETA_PUBLICO)
    with CAMINHO_LEADS_BETA_PUBLICO.open("r", newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def carregar_decisoes_beta_publico() -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_DECISOES_BETA_PUBLICO, CAMPOS_DECISAO_BETA_PUBLICO)
    with CAMINHO_DECISOES_BETA_PUBLICO.open("r", newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def gerar_csv_leads_beta_publico() -> str:
    _garantir_csv(CAMINHO_LEADS_BETA_PUBLICO, CAMPOS_LEADS_BETA_PUBLICO)
    return CAMINHO_LEADS_BETA_PUBLICO.read_text(encoding="utf-8")


def gerar_csv_decisoes_beta_publico() -> str:
    _garantir_csv(CAMINHO_DECISOES_BETA_PUBLICO, CAMPOS_DECISAO_BETA_PUBLICO)
    return CAMINHO_DECISOES_BETA_PUBLICO.read_text(encoding="utf-8")


def salvar_lead_beta_publico(dados: Dict[str, Any]) -> Dict[str, str]:
    _garantir_csv(CAMINHO_LEADS_BETA_PUBLICO, CAMPOS_LEADS_BETA_PUBLICO)

    registro = {
        "id": str(uuid4())[:8],
        "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "nome": _limpar_texto(dados.get("nome")),
        "email": _limpar_texto(dados.get("email")).lower(),
        "perfil": _limpar_texto(dados.get("perfil")),
        "nivel_investidor": _limpar_texto(dados.get("nivel_investidor")),
        "principal_dor": _limpar_texto(dados.get("principal_dor")),
        "objetivo": _limpar_texto(dados.get("objetivo")),
        "aceita_contato": str(bool(dados.get("aceita_contato"))),
        "origem": _limpar_texto(dados.get("origem", "beta_publico")),
        "status": _limpar_texto(dados.get("status", "novo")),
    }

    with CAMINHO_LEADS_BETA_PUBLICO.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_LEADS_BETA_PUBLICO)
        escritor.writerow(registro)

    return registro


def gerar_lead_exemplo_beta_publico() -> Dict[str, str]:
    return salvar_lead_beta_publico(
        {
            "nome": "Lead Beta Exemplo",
            "email": f"lead.beta.{datetime.now().strftime('%H%M%S')}@exemplo.com",
            "perfil": "Investidor intermediário",
            "nivel_investidor": "Invisto entre 1 e 3 anos",
            "principal_dor": "Tenho dificuldade para saber se uma ação está cara ou barata.",
            "objetivo": "Quero uma análise mais clara com preço teto, tese e riscos.",
            "aceita_contato": True,
            "origem": "terminal_demo",
            "status": "novo",
        }
    )


def salvar_decisao_beta_publico(saude: Dict[str, Any], observacoes: str = "") -> Dict[str, str]:
    _garantir_csv(CAMINHO_DECISOES_BETA_PUBLICO, CAMPOS_DECISAO_BETA_PUBLICO)

    registro = {
        "id": str(uuid4())[:8],
        "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score_beta_publico": str(saude.get("score_beta_publico", "")),
        "score_copy": str(saude.get("score_copy", "")),
        "score_conversao": str(saude.get("score_conversao", "")),
        "score_produto": str(saude.get("score_produto", "")),
        "score_validacao": str(saude.get("score_validacao", "")),
        "leads_total": str(saude.get("leads_total", "")),
        "risco": _limpar_texto(saude.get("risco")),
        "decisao": _limpar_texto(saude.get("decisao")),
        "proximo_passo": _limpar_texto(saude.get("proximo_passo")),
        "observacoes": _limpar_texto(observacoes),
    }

    with CAMINHO_DECISOES_BETA_PUBLICO.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISAO_BETA_PUBLICO)
        escritor.writerow(registro)

    return registro


def calcular_metricas_leads() -> Dict[str, Any]:
    leads = carregar_leads_beta_publico()
    total = len(leads)
    emails_validos = sum(1 for lead in leads if _email_valido(lead.get("email", "")))
    aceites = sum(1 for lead in leads if str(lead.get("aceita_contato", "")).lower() == "true")
    perfis = {}
    for lead in leads:
        perfil = lead.get("perfil", "não informado")
        perfis[perfil] = perfis.get(perfil, 0) + 1

    return {
        "leads_total": total,
        "emails_validos": emails_validos,
        "taxa_email_valido": round((emails_validos / total) * 100, 2) if total else 0,
        "aceites_contato": aceites,
        "taxa_aceite_contato": round((aceites / total) * 100, 2) if total else 0,
        "perfis": perfis,
        "ultimos_leads": leads[-20:],
    }


def calcular_saude_beta_publico() -> Dict[str, Any]:
    metricas = calcular_metricas_leads()

    try:
        onboarding = calcular_saude_onboarding_premium()
    except Exception as erro:
        onboarding = {"score_onboarding": 0, "erro": str(erro)}

    try:
        insights = calcular_saude_beta_insights()
    except Exception as erro:
        insights = {"score_insights": 0, "erro": str(erro)}

    try:
        beta = calcular_saude_beta_feedback()
    except Exception as erro:
        beta = {"score_beta": 0, "erro": str(erro)}

    try:
        demo = calcular_demo_2min_valoris()
    except Exception as erro:
        demo = {"score_demo": 0, "erro": str(erro)}

    try:
        premium = calcular_saude_analise_premium()
    except Exception as erro:
        premium = {"score_produto_premium": 0, "erro": str(erro)}

    try:
        launch = calcular_saude_launch_readiness()
    except Exception as erro:
        launch = {"score_launch": 0, "erro": str(erro)}

    score_copy = 0
    score_copy += 18 if len(COPY_BETA_PUBLICO["headline"]) >= 20 else 0
    score_copy += 18 if "preço teto" in COPY_BETA_PUBLICO["subheadline"].lower() else 0
    score_copy += 16 if "margem de segurança" in COPY_BETA_PUBLICO["headline"].lower() or "margem de segurança" in COPY_BETA_PUBLICO["subheadline"].lower() else 0
    score_copy += 16 if "educacional" in COPY_BETA_PUBLICO["disclaimer"].lower() else 0
    score_copy += 16 if len(BLOCOS_PAGINA_BETA) >= 5 else 0
    score_copy += 16 if len(OBJECOES_BETA_PUBLICO) >= 4 else 0
    score_copy = min(100, score_copy)

    score_conversao = 0
    score_conversao += 20 if COPY_BETA_PUBLICO["cta_principal"] else 0
    score_conversao += 18 if COPY_BETA_PUBLICO["cta_secundario"] else 0
    score_conversao += 18 if len(CHECKLIST_PUBLICO) >= 8 else 0
    score_conversao += 18 if metricas["leads_total"] >= 1 else 0
    score_conversao += 14 if metricas["taxa_email_valido"] >= 80 else 0
    score_conversao += 12 if metricas["taxa_aceite_contato"] >= 70 else 0
    score_conversao = min(100, score_conversao)

    score_produto = int(round(
        int(onboarding.get("score_onboarding", 0) or 0) * 0.28
        + int(insights.get("score_insights", 0) or 0) * 0.18
        + int(demo.get("score_demo", 0) or 0) * 0.18
        + int(premium.get("score_produto_premium", 0) or 0) * 0.18
        + int(launch.get("score_launch", 0) or 0) * 0.18
    ))

    score_validacao = int(beta.get("score_beta", 0) or 0)
    if metricas["leads_total"] >= 3:
        score_validacao = min(100, score_validacao + 12)
    elif metricas["leads_total"] >= 1:
        score_validacao = min(100, score_validacao + 6)

    score_beta_publico = int(round(
        score_copy * 0.24
        + score_conversao * 0.24
        + score_produto * 0.30
        + score_validacao * 0.22
    ))

    if metricas["leads_total"] < 3:
        risco = "Médio"
        decisao = "Página beta pronta para captação inicial, ainda com poucos leads"
        proximo_passo = "Convidar 3 a 5 pessoas e medir conversão da promessa para cadastro."
    elif score_beta_publico >= 84:
        risco = "Médio controlado"
        decisao = "Beta público controlado pronto para divulgação limitada"
        proximo_passo = "Publicar a chamada beta para audiência pequena e acompanhar qualidade dos leads."
    elif score_beta_publico >= 70:
        risco = "Médio"
        decisao = "Captação promissora, mas copy/conversão ainda precisam ajuste"
        proximo_passo = "Melhorar headline, prova de valor e CTA antes de ampliar divulgação."
    else:
        risco = "Alto"
        decisao = "Não divulgar beta publicamente ainda"
        proximo_passo = "Reforçar copy, onboarding e clareza da proposta."

    return {
        "versao": VERSAO_BETA_PUBLICO_VALORIS,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score_beta_publico": max(0, min(100, score_beta_publico)),
        "score_copy": score_copy,
        "score_conversao": score_conversao,
        "score_produto": score_produto,
        "score_validacao": score_validacao,
        "leads_total": metricas["leads_total"],
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo_passo,
        "metricas_leads": metricas,
        "copy": COPY_BETA_PUBLICO,
        "blocos_pagina": BLOCOS_PAGINA_BETA,
        "objecoes": OBJECOES_BETA_PUBLICO,
        "checklist_publico": CHECKLIST_PUBLICO,
        "onboarding": onboarding,
        "insights": insights,
        "beta": beta,
        "demo": demo,
        "premium": premium,
        "launch": launch,
    }


def gerar_copy_beta_publico_markdown(saude: Dict[str, Any] | None = None) -> str:
    if saude is None:
        saude = calcular_saude_beta_publico()

    objecoes = "\n".join(
        [
            f"- **{item['objecao']}** {item['resposta']}"
            for item in OBJECOES_BETA_PUBLICO
        ]
    )

    return f"""# Copy Beta Público — Valoris

Versão: {VERSAO_BETA_PUBLICO_VALORIS}  
Gerado em: {saude["gerado_em"]}

## Headline

{COPY_BETA_PUBLICO["headline"]}

## Subheadline

{COPY_BETA_PUBLICO["subheadline"]}

## Promessa

{COPY_BETA_PUBLICO["promessa"]}

## CTAs

Principal: {COPY_BETA_PUBLICO["cta_principal"]}  
Secundário: {COPY_BETA_PUBLICO["cta_secundario"]}

## Objeções

{objecoes}

## Disclaimer

{COPY_BETA_PUBLICO["disclaimer"]}
"""


def gerar_pagina_beta_publico_markdown(saude: Dict[str, Any] | None = None) -> str:
    if saude is None:
        saude = calcular_saude_beta_publico()

    blocos = "\n\n".join(
        [
            f"""## {item['titulo']}

{item['texto']}

Objetivo do bloco: {item['objetivo']}
"""
            for item in BLOCOS_PAGINA_BETA
        ]
    )

    return f"""# Página Beta Público — Valoris

Versão: {VERSAO_BETA_PUBLICO_VALORIS}  
Gerado em: {saude["gerado_em"]}

# {COPY_BETA_PUBLICO["headline"]}

{COPY_BETA_PUBLICO["subheadline"]}

**CTA:** {COPY_BETA_PUBLICO["cta_principal"]}

{blocos}

## Formulário

- Nome
- E-mail
- Perfil
- Nível como investidor
- Principal dor
- Objetivo ao testar a Valoris
- Aceite de contato

## Aviso

{COPY_BETA_PUBLICO["disclaimer"]}
"""


def gerar_checklist_beta_publico_markdown(saude: Dict[str, Any] | None = None) -> str:
    if saude is None:
        saude = calcular_saude_beta_publico()

    checklist = "\n".join([f"- [x] {item}" for item in CHECKLIST_PUBLICO])

    return f"""# Checklist Beta Público — Valoris

Versão: {VERSAO_BETA_PUBLICO_VALORIS}  
Gerado em: {saude["gerado_em"]}

## Status

Score Beta Público: {saude["score_beta_publico"]}/100  
Leads: {saude["leads_total"]}  
Decisão: {saude["decisao"]}

## Checklist

{checklist}

## Próxima ação

{saude["proximo_passo"]}
"""


def salvar_copy_beta_publico_markdown() -> Dict[str, Any]:
    saude = calcular_saude_beta_publico()
    CAMINHO_COPY_BETA_PUBLICO_MD.write_text(gerar_copy_beta_publico_markdown(saude), encoding="utf-8")
    return {"ok": True, "arquivo": str(CAMINHO_COPY_BETA_PUBLICO_MD), "score_beta_publico": saude["score_beta_publico"]}


def salvar_pagina_beta_publico_markdown() -> Dict[str, Any]:
    saude = calcular_saude_beta_publico()
    CAMINHO_PAGINA_BETA_PUBLICO_MD.write_text(gerar_pagina_beta_publico_markdown(saude), encoding="utf-8")
    return {"ok": True, "arquivo": str(CAMINHO_PAGINA_BETA_PUBLICO_MD), "score_beta_publico": saude["score_beta_publico"]}


def salvar_checklist_beta_publico_markdown() -> Dict[str, Any]:
    saude = calcular_saude_beta_publico()
    CAMINHO_CHECKLIST_BETA_PUBLICO_MD.write_text(gerar_checklist_beta_publico_markdown(saude), encoding="utf-8")
    return {"ok": True, "arquivo": str(CAMINHO_CHECKLIST_BETA_PUBLICO_MD), "score_beta_publico": saude["score_beta_publico"]}


def gerar_manifesto_beta_publico() -> Dict[str, Any]:
    saude = calcular_saude_beta_publico()
    manifesto = {
        "versao": VERSAO_BETA_PUBLICO_VALORIS,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "saude": saude,
        "copy": COPY_BETA_PUBLICO,
        "blocos_pagina": BLOCOS_PAGINA_BETA,
        "objecoes": OBJECOES_BETA_PUBLICO,
        "estrategia": {
            "objetivo": "Transformar onboarding e demo em captação beta controlada.",
            "proxima_versao": "Oferta beta fundador ou relatório premium v2, conforme sinal dos leads.",
            "regra": "Captar poucos leads qualificados antes de ampliar divulgação.",
        },
    }
    CAMINHO_MANIFESTO_BETA_PUBLICO.write_text(json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifesto


def _injetar_css_beta_publico() -> None:
    st.markdown(
        """
        <style>
            .beta-publico-hero {
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
            .beta-publico-eyebrow {
                color: #d6b56d;
                font-size: 0.74rem;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                font-weight: 880;
                margin-bottom: 0.35rem;
            }
            .beta-publico-title {
                color: #f4f7fb;
                font-size: clamp(1.8rem, 5.5vw, 3.25rem);
                font-weight: 950;
                line-height: 1.02;
                letter-spacing: -0.058em;
                margin-bottom: 0.55rem;
            }
            .beta-publico-subtitle {
                color: rgba(244, 247, 251, 0.75);
                font-size: clamp(0.94rem, 2.2vw, 1.06rem);
                line-height: 1.56;
                max-width: 1050px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def renderizar_beta_publico_valoris() -> None:
    _injetar_css_beta_publico()

    st.markdown(
        f"""
        <div class="beta-publico-hero">
            <div class="beta-publico-eyebrow">Valoris • Beta Público • v{VERSAO_BETA_PUBLICO_VALORIS}</div>
            <div class="beta-publico-title">Captação beta controlada.</div>
            <div class="beta-publico-subtitle">
                Uma página e formulário para transformar a demo em leads qualificados, sem prometer lucro
                e sem abrir o produto antes da validação.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    saude = calcular_saude_beta_publico()

    st.markdown("### Diagnóstico beta público")
    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Score Beta Público", f"{saude['score_beta_publico']}/100")

    with col_2:
        st.metric("Leads", saude["leads_total"])

    with col_3:
        st.metric("Conversão", f"{saude['score_conversao']}/100")

    with col_4:
        st.metric("Risco", saude["risco"])

    st.progress(saude["score_beta_publico"] / 100)

    if saude["score_beta_publico"] >= 84 and saude["leads_total"] >= 3:
        st.success(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    elif saude["score_beta_publico"] >= 70:
        st.warning(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    else:
        st.info(f"**{saude['decisao']}** — {saude['proximo_passo']}")

    st.divider()

    st.markdown("### Prévia da página beta")
    st.subheader(COPY_BETA_PUBLICO["headline"])
    st.write(COPY_BETA_PUBLICO["subheadline"])
    st.info(COPY_BETA_PUBLICO["promessa"])
    st.caption(COPY_BETA_PUBLICO["disclaimer"])

    for bloco in BLOCOS_PAGINA_BETA:
        with st.expander(f"{bloco['bloco']} — {bloco['titulo']}", expanded=bloco["bloco"] == "Dor"):
            st.write(bloco["texto"])
            st.caption(f"Objetivo: {bloco['objetivo']}")

    st.divider()

    st.markdown("### Capturar lead beta")

    with st.form("form_lead_beta_publico"):
        col_a, col_b = st.columns(2)
        with col_a:
            nome = st.text_input("Nome")
            email = st.text_input("E-mail")
            perfil = st.selectbox("Perfil", PERFIS_LEAD_BETA)
        with col_b:
            nivel_investidor = st.selectbox("Nível como investidor", NIVEIS_LEAD_BETA)
            principal_dor = st.text_area("Principal dor ao analisar ações", height=90)
            objetivo = st.text_area("Objetivo ao testar a Valoris", height=90)
            aceita_contato = st.checkbox("Aceito ser contatado sobre o beta", value=True)

        enviado = st.form_submit_button("Entrar na lista beta")

        if enviado:
            if not _email_valido(email):
                st.error("E-mail inválido. Revise antes de salvar.")
            else:
                registro = salvar_lead_beta_publico(
                    {
                        "nome": nome,
                        "email": email,
                        "perfil": perfil,
                        "nivel_investidor": nivel_investidor,
                        "principal_dor": principal_dor,
                        "objetivo": objetivo,
                        "aceita_contato": aceita_contato,
                        "origem": "aba_beta_publico",
                        "status": "novo",
                    }
                )
                st.success(f"Lead beta salvo: {registro['id']}")
                st.rerun()

    st.divider()

    st.markdown("### Métricas de leads")
    st.json(saude["metricas_leads"])

    if saude["metricas_leads"]["ultimos_leads"]:
        st.dataframe(saude["metricas_leads"]["ultimos_leads"], width="stretch", hide_index=True)

    st.divider()

    col_btn_1, col_btn_2, col_btn_3, col_btn_4 = st.columns(4)

    with col_btn_1:
        if st.button("Gerar lead exemplo", key="beta_publico_lead_exemplo"):
            registro = gerar_lead_exemplo_beta_publico()
            st.success(f"Lead exemplo criado: {registro['id']}")
            st.rerun()

    with col_btn_2:
        if st.button("Gerar manifesto", key="beta_publico_manifesto"):
            manifesto = gerar_manifesto_beta_publico()
            st.success(f"Manifesto gerado: {CAMINHO_MANIFESTO_BETA_PUBLICO}")
            st.json({"versao": manifesto["versao"], "score": manifesto["saude"]["score_beta_publico"]})

    with col_btn_3:
        if st.button("Salvar copy .md", key="beta_publico_copy"):
            retorno = salvar_copy_beta_publico_markdown()
            st.success(f"Copy salva: {retorno['arquivo']}")
            st.json(retorno)

    with col_btn_4:
        if st.button("Salvar página .md", key="beta_publico_pagina"):
            retorno = salvar_pagina_beta_publico_markdown()
            st.success(f"Página salva: {retorno['arquivo']}")
            st.json(retorno)

    if st.button("Salvar checklist .md", key="beta_publico_checklist"):
        retorno = salvar_checklist_beta_publico_markdown()
        st.success(f"Checklist salvo: {retorno['arquivo']}")
        st.json(retorno)

    if st.button("Salvar decisão Beta Público", key="beta_publico_decisao"):
        registro = salvar_decisao_beta_publico(saude, observacoes="Decisão gerada pela captação beta pública.")
        st.success(f"Decisão salva: {registro['decisao']}")
        st.rerun()

    st.download_button(
        "Baixar copy beta público (.md)",
        data=gerar_copy_beta_publico_markdown(saude),
        file_name="COPY_BETA_PUBLICO_VALORIS.md",
        mime="text/markdown",
        key="download_copy_beta_publico",
    )

    st.download_button(
        "Baixar página beta público (.md)",
        data=gerar_pagina_beta_publico_markdown(saude),
        file_name="PAGINA_BETA_PUBLICO_VALORIS.md",
        mime="text/markdown",
        key="download_pagina_beta_publico",
    )

    st.download_button(
        "Baixar leads beta público (.csv)",
        data=gerar_csv_leads_beta_publico(),
        file_name="leads_beta_publico_valoris.csv",
        mime="text/csv",
        key="download_leads_beta_publico",
    )


def executar_autoteste_beta_publico_valoris() -> List[Dict[str, str]]:
    saude = calcular_saude_beta_publico()
    return [
        {
            "teste": "versao_beta_publico",
            "status": "OK" if VERSAO_BETA_PUBLICO_VALORIS == "3.8.81" else "FALHA",
            "detalhe": VERSAO_BETA_PUBLICO_VALORIS,
        },
        {
            "teste": "score_beta_publico",
            "status": "OK" if 0 <= saude["score_beta_publico"] <= 100 else "FALHA",
            "detalhe": str(saude["score_beta_publico"]),
        },
        {
            "teste": "copy_beta_publico",
            "status": "OK" if bool(COPY_BETA_PUBLICO["headline"]) and bool(COPY_BETA_PUBLICO["cta_principal"]) else "FALHA",
            "detalhe": COPY_BETA_PUBLICO["headline"],
        },
        {
            "teste": "renderizador",
            "status": "OK" if callable(renderizar_beta_publico_valoris) else "FALHA",
            "detalhe": "renderizar_beta_publico_valoris",
        },
    ]
