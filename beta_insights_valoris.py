# beta_insights_valoris.py

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

import streamlit as st

from beta_feedback_valoris import carregar_feedbacks_beta, calcular_saude_beta_feedback
from demo_guiada_2min_valoris import calcular_demo_2min_valoris
from analise_premium_valoris import calcular_saude_analise_premium
from launch_readiness_valoris import calcular_saude_launch_readiness


VERSAO_BETA_INSIGHTS_VALORIS = "3.8.79"

CAMINHO_DECISOES_BETA_INSIGHTS = Path("decisoes_beta_insights_valoris.csv")
CAMINHO_MANIFESTO_BETA_INSIGHTS = Path("manifesto_beta_insights_valoris.json")
CAMINHO_INSIGHTS_BETA_MD = Path("INSIGHTS_BETA_VALORIS.md")
CAMINHO_ROADMAP_PRIORIZADO_MD = Path("ROADMAP_PRIORIZADO_VALORIS.md")
CAMINHO_MATRIZ_PRIORIDADE_CSV = Path("matriz_prioridade_beta_valoris.csv")

CAMPOS_DECISAO_BETA_INSIGHTS = [
    "id", "data_registro", "score_insights", "score_feedback", "score_oportunidade",
    "score_criticidade", "feedbacks_total", "top_prioridade", "decisao", "risco",
    "proximo_passo", "observacoes",
]

CAMPOS_MATRIZ_PRIORIDADE = [
    "id", "data_registro", "tema", "categoria", "dor", "impacto", "esforco",
    "confianca", "urgencia", "score_prioridade", "evidencias", "proxima_acao",
]

TEMAS_PRIORIZACAO = [
    {
        "tema": "UX e onboarding guiado",
        "categoria": "Experiência",
        "palavras_chave": ["confuso", "difícil", "facilidade", "usar", "ux", "onboarding", "guia", "passo", "tutorial"],
        "dor": "Usuário precisa entender o app sem explicação externa.",
        "impacto_base": 94,
        "esforco_base": 44,
        "proxima_acao": "Criar onboarding guiado com exemplo preenchido, instruções curtas e checklist de uso.",
    },
    {
        "tema": "Relatório premium mais forte",
        "categoria": "Produto",
        "palavras_chave": ["relatório", "pdf", "exportar", "markdown", "guardar", "compartilhar", "documento"],
        "dor": "Usuário quer transformar análise em material claro para estudo e acompanhamento.",
        "impacto_base": 86,
        "esforco_base": 36,
        "proxima_acao": "Melhorar relatório com resumo executivo, tese, riscos, tabela final e CTA de revisão.",
    },
    {
        "tema": "Explicabilidade da decisão",
        "categoria": "Confiança",
        "palavras_chave": ["tese", "explica", "explicação", "decisão", "risco", "premissa", "confiança", "por que"],
        "dor": "Usuário quer confiar no motivo da decisão, não só ver um score.",
        "impacto_base": 91,
        "esforco_base": 42,
        "proxima_acao": "Aprimorar explicação com premissas, sensibilidade, riscos e interpretação dos scores.",
    },
    {
        "tema": "Comparação entre empresas",
        "categoria": "Produto",
        "palavras_chave": ["comparar", "comparação", "pares", "setor", "concorrentes", "ranking", "melhor empresa"],
        "dor": "Usuário quer saber qual empresa parece melhor dentro do mesmo setor.",
        "impacto_base": 88,
        "esforco_base": 52,
        "proxima_acao": "Criar comparador simples de tese, preço teto, qualidade, risco e margem de segurança.",
    },
    {
        "tema": "Dados reais e atualização automática",
        "categoria": "Dados",
        "palavras_chave": ["dados", "atualizados", "atualização", "balanço", "cvm", "finance", "real", "automático", "api"],
        "dor": "Usuário quer analisar empresas reais sem preencher tudo manualmente.",
        "impacto_base": 96,
        "esforco_base": 82,
        "proxima_acao": "Criar importação controlada de dados reais sem abandonar fallback local.",
    },
    {
        "tema": "Watchlist e alertas",
        "categoria": "Produto",
        "palavras_chave": ["watchlist", "alerta", "acompanhar", "monitorar", "notificação", "preço chegou"],
        "dor": "Usuário quer acompanhar oportunidades sem refazer toda a análise.",
        "impacto_base": 76,
        "esforco_base": 50,
        "proxima_acao": "Criar watchlist local com preço atual, preço teto, margem e status.",
    },
    {
        "tema": "Modelo de preço e oferta beta",
        "categoria": "Growth",
        "palavras_chave": ["preço", "pagar", "mensal", "plano", "assinatura", "oferta", "valor", "caro", "barato"],
        "dor": "Usuário precisa perceber valor suficiente para pagar.",
        "impacto_base": 78,
        "esforco_base": 30,
        "proxima_acao": "Testar oferta beta simples com preço fundador e proposta clara.",
    },
]

ROADMAP_SUGERIDO_BASE = [
    {"fase": "v3.8.80", "entrega": "UX guiada + onboarding premium", "objetivo": "Reduzir fricção e aumentar clareza."},
    {"fase": "v3.8.81", "entrega": "Relatório premium v2", "objetivo": "Aumentar valor percebido e exportação útil."},
    {"fase": "v3.8.82", "entrega": "Comparador setorial inicial", "objetivo": "Comparar empresas por tese, qualidade, risco e preço."},
    {"fase": "v3.8.83", "entrega": "Watchlist local", "objetivo": "Acompanhar oportunidades com preço teto."},
    {"fase": "v3.8.84", "entrega": "Dados reais controlados", "objetivo": "Começar integração de dados reais com fallback local."},
]


def _limpar_texto(valor: Any) -> str:
    if valor is None:
        return ""
    return str(valor).strip()


def _to_float(valor: Any, padrao: float = 0.0) -> float:
    try:
        return float(valor)
    except Exception:
        return padrao


def _normalizar(texto: str) -> str:
    texto = texto.lower()
    mapa = str.maketrans("áàãâéêíóôõúç", "aaaaeeiooouc")
    return texto.translate(mapa)


def _garantir_csv(caminho: Path, campos: List[str]) -> None:
    if caminho.exists():
        return
    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()


def _texto_feedback(feedback: Dict[str, str]) -> str:
    campos = ["maior_valor", "maior_duvida", "funcionalidade_mais_importante", "observacoes", "perfil", "nivel_investidor"]
    return " ".join([_limpar_texto(feedback.get(campo, "")) for campo in campos])


def carregar_decisoes_beta_insights() -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_DECISOES_BETA_INSIGHTS, CAMPOS_DECISAO_BETA_INSIGHTS)
    with CAMINHO_DECISOES_BETA_INSIGHTS.open("r", newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def gerar_csv_decisoes_beta_insights() -> str:
    _garantir_csv(CAMINHO_DECISOES_BETA_INSIGHTS, CAMPOS_DECISAO_BETA_INSIGHTS)
    return CAMINHO_DECISOES_BETA_INSIGHTS.read_text(encoding="utf-8")


def gerar_csv_matriz_prioridade() -> str:
    _garantir_csv(CAMINHO_MATRIZ_PRIORIDADE_CSV, CAMPOS_MATRIZ_PRIORIDADE)
    return CAMINHO_MATRIZ_PRIORIDADE_CSV.read_text(encoding="utf-8")


def extrair_palavras_frequentes(feedbacks: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    texto = " ".join([_normalizar(_texto_feedback(item)) for item in feedbacks])
    tokens = re.findall(r"[a-zA-ZÀ-ÿ0-9]{4,}", texto)
    stopwords = {"para", "com", "uma", "mais", "isso", "esse", "essa", "como", "pela", "pelo", "qual", "muito", "sobre", "beta", "tester", "exemplo", "feedback", "gerado", "validar", "fluxo"}
    tokens = [token for token in tokens if token not in stopwords]
    contador = Counter(tokens)
    return [{"termo": termo, "ocorrencias": qtd} for termo, qtd in contador.most_common(20)]


def _evidencias_tema(tema: Dict[str, Any], feedbacks: List[Dict[str, str]]) -> Dict[str, Any]:
    evidencias = []
    score_evidencia = 0
    palavras = [_normalizar(p) for p in tema["palavras_chave"]]
    for feedback in feedbacks:
        texto = _normalizar(_texto_feedback(feedback))
        hits = [palavra for palavra in palavras if palavra in texto]
        if hits:
            score_evidencia += min(18, 6 * len(hits))
            evidencias.append({"id": feedback.get("id", ""), "hits": hits, "trecho": _texto_feedback(feedback)[:260]})
    return {"score_evidencia": min(100, score_evidencia), "evidencias": evidencias[:8]}


def calcular_matriz_prioridade_beta() -> List[Dict[str, Any]]:
    feedbacks = carregar_feedbacks_beta()
    matriz = []
    for tema in TEMAS_PRIORIZACAO:
        avaliacao = _evidencias_tema(tema, feedbacks)
        impacto = int(tema["impacto_base"])
        esforco = int(tema["esforco_base"])
        confianca = 35 if not feedbacks else min(100, 45 + avaliacao["score_evidencia"])
        urgencia = 50
        if tema["categoria"] in {"Experiência", "Confiança"}:
            urgencia += 18
        if avaliacao["score_evidencia"] >= 30:
            urgencia += 12
        if tema["categoria"] == "Dados" and len(feedbacks) >= 3:
            urgencia += 8
        urgencia = min(100, urgencia)
        score_prioridade = int(round(impacto * 0.34 + confianca * 0.24 + urgencia * 0.22 + (100 - esforco) * 0.20))
        matriz.append({
            "id": str(uuid4())[:8],
            "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "tema": tema["tema"],
            "categoria": tema["categoria"],
            "dor": tema["dor"],
            "impacto": impacto,
            "esforco": esforco,
            "confianca": int(confianca),
            "urgencia": int(urgencia),
            "score_prioridade": score_prioridade,
            "evidencias": avaliacao["evidencias"],
            "proxima_acao": tema["proxima_acao"],
        })
    matriz.sort(key=lambda item: item["score_prioridade"], reverse=True)
    return matriz


def salvar_matriz_prioridade_beta() -> Dict[str, Any]:
    matriz = calcular_matriz_prioridade_beta()
    _garantir_csv(CAMINHO_MATRIZ_PRIORIDADE_CSV, CAMPOS_MATRIZ_PRIORIDADE)
    with CAMINHO_MATRIZ_PRIORIDADE_CSV.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_MATRIZ_PRIORIDADE)
        escritor.writeheader()
        for item in matriz:
            linha = dict(item)
            linha["evidencias"] = json.dumps(item["evidencias"], ensure_ascii=False)
            escritor.writerow(linha)
    return {"ok": True, "arquivo": str(CAMINHO_MATRIZ_PRIORIDADE_CSV), "itens": len(matriz), "top_prioridade": matriz[0]["tema"] if matriz else ""}


def calcular_saude_beta_insights() -> Dict[str, Any]:
    feedbacks = carregar_feedbacks_beta()
    matriz = calcular_matriz_prioridade_beta()
    palavras = extrair_palavras_frequentes(feedbacks)
    try:
        beta = calcular_saude_beta_feedback()
    except Exception as erro:
        beta = {"score_beta": 0, "feedbacks_total": len(feedbacks), "erro": str(erro)}
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

    feedbacks_total = len(feedbacks)
    score_beta = int(beta.get("score_beta", 0) or 0)
    score_demo = int(demo.get("score_demo", 0) or 0)
    score_premium = int(premium.get("score_produto_premium", 0) or 0)
    score_launch = int(launch.get("score_launch", 0) or 0)
    if feedbacks_total == 0:
        score_feedback = 0
    else:
        metricas = beta.get("metricas", {})
        score_feedback = int(round(
            _to_float(metricas.get("media_clareza")) * 2.0
            + _to_float(metricas.get("media_utilidade")) * 2.0
            + _to_float(metricas.get("media_confianca")) * 1.8
            + _to_float(metricas.get("media_probabilidade_usar")) * 1.8
            + _to_float(metricas.get("media_probabilidade_pagar")) * 1.2
            + min(feedbacks_total, 10) * 2
        ))
        score_feedback = max(0, min(100, score_feedback))
    top = matriz[0] if matriz else {}
    score_oportunidade = int(top.get("score_prioridade", 0) or 0)
    score_criticidade = int(round((100 - int(top.get("esforco", 100) or 100)) * 0.35 + int(top.get("impacto", 0) or 0) * 0.65)) if top else 0
    score_insights = int(round(score_feedback * 0.34 + score_oportunidade * 0.28 + score_beta * 0.16 + score_premium * 0.10 + score_demo * 0.07 + score_launch * 0.05))

    if feedbacks_total < 3:
        risco = "Médio"
        decisao = "Insights iniciais, validação real ainda pequena"
        proximo_passo = "Coletar mais feedbacks antes de alterar grandes partes do produto."
    elif score_insights >= 82 and top:
        risco = "Médio controlado"
        decisao = "Priorizar roadmap baseado em feedback real"
        proximo_passo = f"Construir primeiro: {top['tema']}."
    elif score_insights >= 68:
        risco = "Médio"
        decisao = "Há sinais úteis, mas a prioridade ainda precisa de confirmação"
        proximo_passo = "Rodar mais entrevistas e revisar a matriz de prioridade."
    else:
        risco = "Alto"
        decisao = "Não avançar roadmap ainda"
        proximo_passo = "Melhorar coleta de feedback e clareza da demo."

    roadmap = []
    for index, item in enumerate(matriz[:6], start=1):
        roadmap.append({
            "ordem": index,
            "tema": item["tema"],
            "categoria": item["categoria"],
            "score_prioridade": item["score_prioridade"],
            "proxima_acao": item["proxima_acao"],
            "versao_sugerida": f"v3.8.{79 + index}",
        })
    return {
        "versao": VERSAO_BETA_INSIGHTS_VALORIS,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score_insights": max(0, min(100, score_insights)),
        "score_feedback": score_feedback,
        "score_oportunidade": score_oportunidade,
        "score_criticidade": score_criticidade,
        "feedbacks_total": feedbacks_total,
        "top_prioridade": top.get("tema", ""),
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo_passo,
        "beta": beta,
        "demo": demo,
        "premium": premium,
        "launch": launch,
        "matriz_prioridade": matriz,
        "roadmap_priorizado": roadmap,
        "palavras_frequentes": palavras,
        "feedbacks": feedbacks[-25:],
    }


def salvar_decisao_beta_insights(saude: Dict[str, Any], observacoes: str = "") -> Dict[str, str]:
    _garantir_csv(CAMINHO_DECISOES_BETA_INSIGHTS, CAMPOS_DECISAO_BETA_INSIGHTS)
    registro = {
        "id": str(uuid4())[:8],
        "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score_insights": str(saude.get("score_insights", "")),
        "score_feedback": str(saude.get("score_feedback", "")),
        "score_oportunidade": str(saude.get("score_oportunidade", "")),
        "score_criticidade": str(saude.get("score_criticidade", "")),
        "feedbacks_total": str(saude.get("feedbacks_total", "")),
        "top_prioridade": _limpar_texto(saude.get("top_prioridade")),
        "decisao": _limpar_texto(saude.get("decisao")),
        "risco": _limpar_texto(saude.get("risco")),
        "proximo_passo": _limpar_texto(saude.get("proximo_passo")),
        "observacoes": _limpar_texto(observacoes),
    }
    with CAMINHO_DECISOES_BETA_INSIGHTS.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISAO_BETA_INSIGHTS)
        escritor.writerow(registro)
    return registro


def gerar_insights_beta_markdown(saude: Dict[str, Any] | None = None) -> str:
    if saude is None:
        saude = calcular_saude_beta_insights()
    matriz = "\n".join([f"- **{item['tema']}** — score {item['score_prioridade']}/100 | impacto {item['impacto']} | esforço {item['esforco']} | ação: {item['proxima_acao']}" for item in saude["matriz_prioridade"][:8]])
    palavras = "\n".join([f"- {item['termo']}: {item['ocorrencias']}" for item in saude["palavras_frequentes"][:12]]) or "- Nenhum termo frequente encontrado."
    return f"""# Beta Insights — Valoris

Versão: {VERSAO_BETA_INSIGHTS_VALORIS}  
Gerado em: {saude['gerado_em']}

## Diagnóstico

Score Insights: {saude['score_insights']}/100  
Feedbacks analisados: {saude['feedbacks_total']}  
Top prioridade: {saude['top_prioridade']}  
Risco: {saude['risco']}  
Decisão: {saude['decisao']}  
Próximo passo: {saude['proximo_passo']}

## Matriz de prioridade

{matriz}

## Termos frequentes

{palavras}

## Leitura estratégica

A Valoris deve priorizar melhorias que aumentem clareza, confiança e valor percebido antes de avançar para cloud real. Dados reais importam, mas só devem entrar quando a experiência e a proposta de valor estiverem suficientemente validadas.
"""


def gerar_roadmap_priorizado_markdown(saude: Dict[str, Any] | None = None) -> str:
    if saude is None:
        saude = calcular_saude_beta_insights()
    roadmap = "\n".join([f"- **{item['versao_sugerida']}** — {item['tema']} ({item['categoria']}): {item['proxima_acao']} Score: {item['score_prioridade']}/100." for item in saude["roadmap_priorizado"]])
    base = "\n".join([f"- **{item['fase']}** — {item['entrega']}: {item['objetivo']}" for item in ROADMAP_SUGERIDO_BASE])
    return f"""# Roadmap Priorizado — Valoris

Versão: {VERSAO_BETA_INSIGHTS_VALORIS}  
Gerado em: {saude['gerado_em']}

## Decisão

{saude['decisao']}

## Próximo passo

{saude['proximo_passo']}

## Roadmap baseado em feedback

{roadmap}

## Roadmap base de lançamento

{base}
"""


def salvar_insights_beta_markdown() -> Dict[str, Any]:
    saude = calcular_saude_beta_insights()
    CAMINHO_INSIGHTS_BETA_MD.write_text(gerar_insights_beta_markdown(saude), encoding="utf-8")
    return {"ok": True, "arquivo": str(CAMINHO_INSIGHTS_BETA_MD), "score_insights": saude["score_insights"], "top_prioridade": saude["top_prioridade"]}


def salvar_roadmap_priorizado_markdown() -> Dict[str, Any]:
    saude = calcular_saude_beta_insights()
    CAMINHO_ROADMAP_PRIORIZADO_MD.write_text(gerar_roadmap_priorizado_markdown(saude), encoding="utf-8")
    return {"ok": True, "arquivo": str(CAMINHO_ROADMAP_PRIORIZADO_MD), "score_insights": saude["score_insights"], "top_prioridade": saude["top_prioridade"]}


def gerar_manifesto_beta_insights() -> Dict[str, Any]:
    saude = calcular_saude_beta_insights()
    manifesto = {
        "versao": VERSAO_BETA_INSIGHTS_VALORIS,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "saude": saude,
        "temas": TEMAS_PRIORIZACAO,
        "roadmap_base": ROADMAP_SUGERIDO_BASE,
        "estrategia": {
            "objetivo": "Transformar feedback beta em prioridade de produto.",
            "proxima_versao": "Construir a melhoria de maior prioridade indicada pela matriz.",
            "regra": "Não construir features por ansiedade; construir pelo sinal de validação.",
        },
    }
    CAMINHO_MANIFESTO_BETA_INSIGHTS.write_text(json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifesto


def _injetar_css_beta_insights() -> None:
    st.markdown(
        """
        <style>
            .beta-insights-hero {
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
            .beta-insights-eyebrow { color: #d6b56d; font-size: 0.74rem; letter-spacing: 0.14em; text-transform: uppercase; font-weight: 880; margin-bottom: 0.35rem; }
            .beta-insights-title { color: #f4f7fb; font-size: clamp(1.8rem, 5.5vw, 3.25rem); font-weight: 950; line-height: 1.02; letter-spacing: -0.058em; margin-bottom: 0.55rem; }
            .beta-insights-subtitle { color: rgba(244, 247, 251, 0.75); font-size: clamp(0.94rem, 2.2vw, 1.06rem); line-height: 1.56; max-width: 1050px; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def renderizar_beta_insights_valoris() -> None:
    _injetar_css_beta_insights()
    st.markdown(
        f"""
        <div class="beta-insights-hero">
            <div class="beta-insights-eyebrow">Valoris • Beta Insights • v{VERSAO_BETA_INSIGHTS_VALORIS}</div>
            <div class="beta-insights-title">Feedback virando decisão de produto.</div>
            <div class="beta-insights-subtitle">
                Analise dores, dúvidas e pedidos dos beta testers para decidir o que construir primeiro sem perder o foco do lançamento.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    saude = calcular_saude_beta_insights()
    st.markdown("### Diagnóstico de insights")
    col_1, col_2, col_3, col_4 = st.columns(4)
    with col_1:
        st.metric("Score Insights", f"{saude['score_insights']}/100")
    with col_2:
        st.metric("Feedbacks", saude["feedbacks_total"])
    with col_3:
        st.metric("Top prioridade", saude["top_prioridade"] or "Pendente")
    with col_4:
        st.metric("Risco", saude["risco"])
    st.progress(saude["score_insights"] / 100)
    if saude["score_insights"] >= 82:
        st.success(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    elif saude["score_insights"] >= 68:
        st.warning(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    else:
        st.info(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    st.divider()
    st.markdown("### Matriz de prioridade")
    tabela = [{k: item[k] for k in ["tema", "categoria", "impacto", "esforco", "confianca", "urgencia", "score_prioridade", "proxima_acao"]} for item in saude["matriz_prioridade"]]
    st.dataframe(tabela, width="stretch", hide_index=True)
    st.markdown("### Roadmap priorizado")
    st.dataframe(saude["roadmap_priorizado"], width="stretch", hide_index=True)
    st.markdown("### Termos frequentes")
    st.dataframe(saude["palavras_frequentes"], width="stretch", hide_index=True)
    st.divider()
    col_btn_1, col_btn_2, col_btn_3, col_btn_4 = st.columns(4)
    with col_btn_1:
        if st.button("Gerar manifesto Insights", key="beta_insights_manifesto"):
            manifesto = gerar_manifesto_beta_insights()
            st.success(f"Manifesto gerado: {CAMINHO_MANIFESTO_BETA_INSIGHTS}")
            st.json({"versao": manifesto["versao"], "score_insights": manifesto["saude"]["score_insights"]})
    with col_btn_2:
        if st.button("Salvar matriz CSV", key="beta_insights_matriz"):
            retorno = salvar_matriz_prioridade_beta()
            st.success(f"Matriz salva: {retorno['arquivo']}")
            st.json(retorno)
    with col_btn_3:
        if st.button("Salvar insights .md", key="beta_insights_md"):
            retorno = salvar_insights_beta_markdown()
            st.success(f"Insights salvos: {retorno['arquivo']}")
            st.json(retorno)
    with col_btn_4:
        if st.button("Salvar roadmap .md", key="beta_insights_roadmap"):
            retorno = salvar_roadmap_priorizado_markdown()
            st.success(f"Roadmap salvo: {retorno['arquivo']}")
            st.json(retorno)
    if st.button("Salvar decisão Insights", key="beta_insights_decisao"):
        registro = salvar_decisao_beta_insights(saude, observacoes="Decisão gerada pela matriz de insights beta.")
        st.success(f"Decisão salva: {registro['decisao']}")
        st.rerun()
    st.download_button("Baixar insights beta (.md)", data=gerar_insights_beta_markdown(saude), file_name="INSIGHTS_BETA_VALORIS.md", mime="text/markdown", key="download_insights_beta")
    st.download_button("Baixar roadmap priorizado (.md)", data=gerar_roadmap_priorizado_markdown(saude), file_name="ROADMAP_PRIORIZADO_VALORIS.md", mime="text/markdown", key="download_roadmap_priorizado")
    st.download_button("Baixar decisões Insights (.csv)", data=gerar_csv_decisoes_beta_insights(), file_name="decisoes_beta_insights_valoris.csv", mime="text/csv", key="download_decisoes_beta_insights")


def executar_autoteste_beta_insights_valoris() -> List[Dict[str, str]]:
    saude = calcular_saude_beta_insights()
    return [
        {"teste": "versao_beta_insights", "status": "OK" if VERSAO_BETA_INSIGHTS_VALORIS == "3.8.79" else "FALHA", "detalhe": VERSAO_BETA_INSIGHTS_VALORIS},
        {"teste": "score_insights", "status": "OK" if 0 <= saude["score_insights"] <= 100 else "FALHA", "detalhe": str(saude["score_insights"])},
        {"teste": "matriz_prioridade", "status": "OK" if len(saude["matriz_prioridade"]) >= 5 else "FALHA", "detalhe": str(len(saude["matriz_prioridade"]))},
        {"teste": "renderizador", "status": "OK" if callable(renderizar_beta_insights_valoris) else "FALHA", "detalhe": "renderizar_beta_insights_valoris"},
    ]
