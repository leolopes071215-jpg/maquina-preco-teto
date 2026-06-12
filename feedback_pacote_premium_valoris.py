# feedback_pacote_premium_valoris.py

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

import streamlit as st


VERSAO_FEEDBACK_PACOTE_PREMIUM_VALORIS = "3.8.89"

CAMINHO_FEEDBACKS_PACOTE = Path("feedbacks_pacote_premium_valoris.csv")
CAMINHO_DECISOES_FEEDBACK_PACOTE = Path("decisoes_feedback_pacote_premium_valoris.csv")
CAMINHO_MANIFESTO_FEEDBACK_PACOTE = Path("manifesto_feedback_pacote_premium_valoris.json")
CAMINHO_MATRIZ_MELHORIAS_MD = Path("MATRIZ_MELHORIAS_PACOTE_PREMIUM_VALORIS.md")
CAMINHO_ROTEIRO_FEEDBACK_MD = Path("ROTEIRO_FEEDBACK_PACOTE_PREMIUM_VALORIS.md")
CAMINHO_CHECKLIST_FEEDBACK_MD = Path("CHECKLIST_FEEDBACK_PACOTE_PREMIUM_VALORIS.md")

CAMPOS_FEEDBACK_PACOTE = [
    "id",
    "data_registro",
    "fundador_nome",
    "fundador_email",
    "ticker_base",
    "empresa_base",
    "clareza_entrega",
    "valor_percebido",
    "utilidade_pratica",
    "confianca_analise",
    "facilidade_consumo",
    "vontade_continuar",
    "pagaria_por_isso",
    "preco_justo",
    "melhor_parte",
    "parte_confusa",
    "principal_objeção",
    "feature_mais_desejada",
    "nota_geral",
    "observacoes",
]

CAMPOS_DECISAO_FEEDBACK_PACOTE = [
    "id",
    "data_registro",
    "score_feedback_pacote",
    "score_valor",
    "score_clareza",
    "score_comercial",
    "score_produto",
    "feedbacks_total",
    "pagantes_potenciais",
    "nota_media",
    "principal_objeção",
    "feature_mais_pedida",
    "risco",
    "decisao",
    "proximo_passo",
    "observacoes",
]

ROTEIRO_PERGUNTAS = [
    {
        "pergunta": "O pacote deixou claro o que a empresa faz e por que ela está sendo analisada?",
        "objetivo": "Medir clareza inicial.",
        "tipo": "nota_0_10",
    },
    {
        "pergunta": "Você percebeu valor real no dossiê, na watchlist e no comparador?",
        "objetivo": "Medir percepção de entrega premium.",
        "tipo": "nota_0_10",
    },
    {
        "pergunta": "O relatório ajudaria você a tomar uma decisão melhor ou estudar com mais disciplina?",
        "objetivo": "Medir utilidade prática.",
        "tipo": "nota_0_10",
    },
    {
        "pergunta": "O que mais te gerou confiança na análise?",
        "objetivo": "Identificar o bloco de maior valor.",
        "tipo": "texto",
    },
    {
        "pergunta": "Qual parte ficou confusa, rasa ou exagerada?",
        "objetivo": "Encontrar fricção.",
        "tipo": "texto",
    },
    {
        "pergunta": "Você pagaria por uma entrega desse tipo de forma recorrente?",
        "objetivo": "Validar intenção comercial.",
        "tipo": "sim_nao",
    },
    {
        "pergunta": "Qual feature faria você usar a Valoris toda semana?",
        "objetivo": "Guiar roadmap de retenção.",
        "tipo": "texto",
    },
]

CHECKLIST_FEEDBACK = [
    "Pacote premium entregue ao fundador",
    "Ticker base identificado",
    "Nota de clareza coletada",
    "Nota de valor percebido coletada",
    "Nota de utilidade prática coletada",
    "Objeção principal registrada",
    "Feature mais desejada registrada",
    "Intenção de pagamento registrada",
    "Matriz de melhorias gerada",
    "Decisão de produto registrada",
]


def _limpar_texto(valor: Any) -> str:
    if valor is None:
        return ""
    return str(valor).strip()


def _to_int(valor: Any, padrao: int = 0) -> int:
    try:
        return int(valor)
    except Exception:
        return padrao


def _to_float(valor: Any, padrao: float = 0.0) -> float:
    try:
        if isinstance(valor, str):
            valor = valor.replace("R$", "").replace(".", "").replace(",", ".").strip()
        return float(valor)
    except Exception:
        return padrao


def _as_bool(valor: Any) -> bool:
    if isinstance(valor, bool):
        return valor
    return str(valor).strip().lower() in {"true", "1", "sim", "yes", "y"}


def _bool_str(valor: Any) -> str:
    return "True" if bool(valor) else "False"


def _garantir_csv(caminho: Path, campos: List[str]) -> None:
    if caminho.exists():
        return

    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()


def _calcular_saude_pacote() -> Dict[str, Any]:
    try:
        from pacote_premium_valoris import calcular_saude_pacote_premium

        return calcular_saude_pacote_premium()
    except Exception as erro:
        return {"score_pacote": 0, "ticker_base": "PENDENTE", "empresa_base": "", "erro": str(erro)}


def carregar_feedbacks_pacote_premium() -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_FEEDBACKS_PACOTE, CAMPOS_FEEDBACK_PACOTE)

    with CAMINHO_FEEDBACKS_PACOTE.open("r", newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def carregar_decisoes_feedback_pacote() -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_DECISOES_FEEDBACK_PACOTE, CAMPOS_DECISAO_FEEDBACK_PACOTE)

    with CAMINHO_DECISOES_FEEDBACK_PACOTE.open("r", newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def gerar_csv_feedbacks_pacote() -> str:
    _garantir_csv(CAMINHO_FEEDBACKS_PACOTE, CAMPOS_FEEDBACK_PACOTE)
    return CAMINHO_FEEDBACKS_PACOTE.read_text(encoding="utf-8")


def gerar_csv_decisoes_feedback_pacote() -> str:
    _garantir_csv(CAMINHO_DECISOES_FEEDBACK_PACOTE, CAMPOS_DECISAO_FEEDBACK_PACOTE)
    return CAMINHO_DECISOES_FEEDBACK_PACOTE.read_text(encoding="utf-8")


def salvar_feedback_pacote_premium(dados: Dict[str, Any]) -> Dict[str, str]:
    _garantir_csv(CAMINHO_FEEDBACKS_PACOTE, CAMPOS_FEEDBACK_PACOTE)

    registro = {
        "id": str(uuid4())[:8],
        "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "fundador_nome": _limpar_texto(dados.get("fundador_nome")),
        "fundador_email": _limpar_texto(dados.get("fundador_email")).lower(),
        "ticker_base": _limpar_texto(dados.get("ticker_base")).upper(),
        "empresa_base": _limpar_texto(dados.get("empresa_base")),
        "clareza_entrega": str(_to_int(dados.get("clareza_entrega"), 0)),
        "valor_percebido": str(_to_int(dados.get("valor_percebido"), 0)),
        "utilidade_pratica": str(_to_int(dados.get("utilidade_pratica"), 0)),
        "confianca_analise": str(_to_int(dados.get("confianca_analise"), 0)),
        "facilidade_consumo": str(_to_int(dados.get("facilidade_consumo"), 0)),
        "vontade_continuar": str(_to_int(dados.get("vontade_continuar"), 0)),
        "pagaria_por_isso": _bool_str(dados.get("pagaria_por_isso")),
        "preco_justo": str(_to_float(dados.get("preco_justo"), 0.0)),
        "melhor_parte": _limpar_texto(dados.get("melhor_parte")),
        "parte_confusa": _limpar_texto(dados.get("parte_confusa")),
        "principal_objeção": _limpar_texto(dados.get("principal_objeção")),
        "feature_mais_desejada": _limpar_texto(dados.get("feature_mais_desejada")),
        "nota_geral": str(_to_int(dados.get("nota_geral"), 0)),
        "observacoes": _limpar_texto(dados.get("observacoes")),
    }

    with CAMINHO_FEEDBACKS_PACOTE.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_FEEDBACK_PACOTE)
        escritor.writerow(registro)

    return registro


def gerar_feedback_pacote_exemplo() -> Dict[str, str]:
    pacote = _calcular_saude_pacote()

    return salvar_feedback_pacote_premium(
        {
            "fundador_nome": "Fundador Exemplo",
            "fundador_email": "fundador.feedback@exemplo.com",
            "ticker_base": pacote.get("ticker_base", "MA"),
            "empresa_base": pacote.get("empresa_base", "Mastercard"),
            "clareza_entrega": 9,
            "valor_percebido": 8,
            "utilidade_pratica": 8,
            "confianca_analise": 8,
            "facilidade_consumo": 7,
            "vontade_continuar": 8,
            "pagaria_por_isso": True,
            "preco_justo": 59,
            "melhor_parte": "O dossiê organiza tese, risco e acompanhamento em um só lugar.",
            "parte_confusa": "Alguns termos financeiros poderiam ter explicações mais simples.",
            "principal_objeção": "Quero ver dados reais mais automatizados no futuro.",
            "feature_mais_desejada": "Alertas automáticos por preço teto e mudança de margem.",
            "nota_geral": 8,
            "observacoes": "Feedback exemplo para validar loop de melhoria do pacote premium.",
        }
    )


def _media(feedbacks: List[Dict[str, str]], campo: str) -> float:
    valores = [_to_int(item.get(campo), 0) for item in feedbacks if _to_int(item.get(campo), 0) > 0]
    if not valores:
        return 0.0
    return round(sum(valores) / len(valores), 2)


def _top_texto(feedbacks: List[Dict[str, str]], campo: str) -> str:
    contagem: Dict[str, int] = {}

    for item in feedbacks:
        valor = _limpar_texto(item.get(campo))
        if not valor:
            continue
        chave = valor[:160]
        contagem[chave] = contagem.get(chave, 0) + 1

    if not contagem:
        return ""

    return sorted(contagem.items(), key=lambda par: par[1], reverse=True)[0][0]


def calcular_metricas_feedback_pacote() -> Dict[str, Any]:
    feedbacks = carregar_feedbacks_pacote_premium()

    pagantes_potenciais = sum(1 for item in feedbacks if _as_bool(item.get("pagaria_por_isso")))
    precos = [_to_float(item.get("preco_justo"), 0.0) for item in feedbacks if _to_float(item.get("preco_justo"), 0.0) > 0]

    preco_medio = round(sum(precos) / len(precos), 2) if precos else 0.0

    return {
        "feedbacks_total": len(feedbacks),
        "pagantes_potenciais": pagantes_potenciais,
        "taxa_pagaria": round((pagantes_potenciais / len(feedbacks)) * 100, 2) if feedbacks else 0.0,
        "preco_medio": preco_medio,
        "media_clareza": _media(feedbacks, "clareza_entrega"),
        "media_valor": _media(feedbacks, "valor_percebido"),
        "media_utilidade": _media(feedbacks, "utilidade_pratica"),
        "media_confianca": _media(feedbacks, "confianca_analise"),
        "media_facilidade": _media(feedbacks, "facilidade_consumo"),
        "media_continuar": _media(feedbacks, "vontade_continuar"),
        "nota_media": _media(feedbacks, "nota_geral"),
        "principal_objeção": _top_texto(feedbacks, "principal_objeção"),
        "feature_mais_pedida": _top_texto(feedbacks, "feature_mais_desejada"),
        "melhor_parte": _top_texto(feedbacks, "melhor_parte"),
        "parte_confusa": _top_texto(feedbacks, "parte_confusa"),
        "ultimos_feedbacks": feedbacks[-25:],
    }


def calcular_saude_feedback_pacote_premium() -> Dict[str, Any]:
    metricas = calcular_metricas_feedback_pacote()
    pacote = _calcular_saude_pacote()

    score_valor = 0
    score_valor += int(metricas["media_valor"] * 2.8)
    score_valor += int(metricas["media_utilidade"] * 2.6)
    score_valor += int(metricas["media_continuar"] * 2.4)
    score_valor += 20 if metricas["nota_media"] >= 8 else 0
    score_valor = min(100, score_valor)

    score_clareza = 0
    score_clareza += int(metricas["media_clareza"] * 3.2)
    score_clareza += int(metricas["media_facilidade"] * 2.4)
    score_clareza += int(metricas["media_confianca"] * 2.2)
    score_clareza += 14 if metricas["parte_confusa"] else 0
    score_clareza = min(100, score_clareza)

    score_comercial = 0
    score_comercial += 35 if metricas["pagantes_potenciais"] >= 1 else 0
    score_comercial += 25 if metricas["taxa_pagaria"] >= 60 else 0
    score_comercial += 20 if metricas["preco_medio"] >= 29 else 0
    score_comercial += 20 if metricas["preco_medio"] >= 59 else 0
    score_comercial = min(100, score_comercial)

    score_produto = 0
    score_produto += 25 if metricas["feedbacks_total"] >= 1 else 0
    score_produto += 20 if metricas["principal_objeção"] else 0
    score_produto += 20 if metricas["feature_mais_pedida"] else 0
    score_produto += 15 if metricas["melhor_parte"] else 0
    score_produto += 20 if int(pacote.get("score_pacote", 0) or 0) >= 70 else 0
    score_produto = min(100, score_produto)

    score_feedback = int(round(
        score_valor * 0.30
        + score_clareza * 0.22
        + score_comercial * 0.24
        + score_produto * 0.24
    ))

    if metricas["feedbacks_total"] >= 3 and score_feedback >= 82 and metricas["taxa_pagaria"] >= 60:
        risco = "Médio controlado"
        decisao = "Pacote premium validado com sinal comercial inicial"
        proximo_passo = "Transformar objeções em melhorias e testar nova entrega com mais fundadores."
    elif metricas["feedbacks_total"] >= 1 and score_feedback >= 65:
        risco = "Médio"
        decisao = "Feedback inicial positivo, mas amostra ainda pequena"
        proximo_passo = "Coletar pelo menos 3 feedbacks e priorizar a feature mais pedida."
    elif metricas["feedbacks_total"] >= 1:
        risco = "Médio/Alto"
        decisao = "Feedback coletado, mas pacote ainda não convenceu o suficiente"
        proximo_passo = "Reescrever partes confusas e reduzir objeção principal antes de escalar."
    else:
        risco = "Alto"
        decisao = "Ainda não há feedback real sobre o pacote premium"
        proximo_passo = "Entregar o pacote para pelo menos 1 fundador e registrar feedback."

    return {
        "versao": VERSAO_FEEDBACK_PACOTE_PREMIUM_VALORIS,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score_feedback_pacote": max(0, min(100, score_feedback)),
        "score_valor": score_valor,
        "score_clareza": score_clareza,
        "score_comercial": score_comercial,
        "score_produto": score_produto,
        "feedbacks_total": metricas["feedbacks_total"],
        "pagantes_potenciais": metricas["pagantes_potenciais"],
        "nota_media": metricas["nota_media"],
        "principal_objeção": metricas["principal_objeção"],
        "feature_mais_pedida": metricas["feature_mais_pedida"],
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo_passo,
        "metricas_feedback": metricas,
        "pacote": pacote,
        "roteiro_perguntas": ROTEIRO_PERGUNTAS,
        "checklist": CHECKLIST_FEEDBACK,
    }


def salvar_decisao_feedback_pacote(saude: Dict[str, Any], observacoes: str = "") -> Dict[str, str]:
    _garantir_csv(CAMINHO_DECISOES_FEEDBACK_PACOTE, CAMPOS_DECISAO_FEEDBACK_PACOTE)

    registro = {
        "id": str(uuid4())[:8],
        "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score_feedback_pacote": str(saude.get("score_feedback_pacote", "")),
        "score_valor": str(saude.get("score_valor", "")),
        "score_clareza": str(saude.get("score_clareza", "")),
        "score_comercial": str(saude.get("score_comercial", "")),
        "score_produto": str(saude.get("score_produto", "")),
        "feedbacks_total": str(saude.get("feedbacks_total", "")),
        "pagantes_potenciais": str(saude.get("pagantes_potenciais", "")),
        "nota_media": str(saude.get("nota_media", "")),
        "principal_objeção": _limpar_texto(saude.get("principal_objeção")),
        "feature_mais_pedida": _limpar_texto(saude.get("feature_mais_pedida")),
        "risco": _limpar_texto(saude.get("risco")),
        "decisao": _limpar_texto(saude.get("decisao")),
        "proximo_passo": _limpar_texto(saude.get("proximo_passo")),
        "observacoes": _limpar_texto(observacoes),
    }

    with CAMINHO_DECISOES_FEEDBACK_PACOTE.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISAO_FEEDBACK_PACOTE)
        escritor.writerow(registro)

    return registro


def gerar_matriz_melhorias_markdown(saude: Dict[str, Any] | None = None) -> str:
    if saude is None:
        saude = calcular_saude_feedback_pacote_premium()

    m = saude["metricas_feedback"]

    return f"""# Matriz de Melhorias — Pacote Premium Valoris

Versão: {VERSAO_FEEDBACK_PACOTE_PREMIUM_VALORIS}  
Gerado em: {saude["gerado_em"]}

## Diagnóstico

Score Feedback Pacote: {saude["score_feedback_pacote"]}/100  
Feedbacks coletados: {saude["feedbacks_total"]}  
Nota média: {saude["nota_media"]}  
Taxa que pagaria: {m["taxa_pagaria"]}%  
Preço médio justo: R$ {m["preco_medio"]}

## Principal valor percebido

{m["melhor_parte"] or "Ainda sem padrão claro."}

## Parte mais confusa

{m["parte_confusa"] or "Ainda sem padrão claro."}

## Principal objeção

{saude["principal_objeção"] or "Ainda sem objeção registrada."}

## Feature mais pedida

{saude["feature_mais_pedida"] or "Ainda sem feature dominante."}

## Matriz de decisão

| Área | Sinal | Ação sugerida |
|---|---|---|
| Clareza | {saude["score_clareza"]}/100 | Simplificar explicações e termos técnicos se abaixo de 75. |
| Valor | {saude["score_valor"]}/100 | Reforçar os blocos percebidos como mais úteis. |
| Comercial | {saude["score_comercial"]}/100 | Testar preço e oferta se houver intenção de pagamento. |
| Produto | {saude["score_produto"]}/100 | Priorizar objeção e feature mais repetidas. |

## Próximo passo

{saude["proximo_passo"]}
"""


def gerar_roteiro_feedback_markdown(saude: Dict[str, Any] | None = None) -> str:
    if saude is None:
        saude = calcular_saude_feedback_pacote_premium()

    perguntas = "\n".join(
        [
            f"- **{item['pergunta']}** Objetivo: {item['objetivo']} Tipo: {item['tipo']}."
            for item in ROTEIRO_PERGUNTAS
        ]
    )

    return f"""# Roteiro de Feedback — Pacote Premium Valoris

Versão: {VERSAO_FEEDBACK_PACOTE_PREMIUM_VALORIS}  
Gerado em: {saude["gerado_em"]}

## Como usar

Envie o pacote premium para um fundador e faça as perguntas abaixo sem defender o produto. O objetivo é descobrir se a entrega realmente parece útil, clara e pagável.

## Perguntas

{perguntas}

## Fechamento

Pergunte: "O que precisaria mudar para você usar isso toda semana?"
"""


def gerar_checklist_feedback_markdown(saude: Dict[str, Any] | None = None) -> str:
    if saude is None:
        saude = calcular_saude_feedback_pacote_premium()

    checklist = "\n".join([f"- [x] {item}" for item in CHECKLIST_FEEDBACK])

    return f"""# Checklist Feedback Pacote Premium — Valoris

Versão: {VERSAO_FEEDBACK_PACOTE_PREMIUM_VALORIS}  
Gerado em: {saude["gerado_em"]}

## Status

Score Feedback Pacote: {saude["score_feedback_pacote"]}/100  
Decisão: {saude["decisao"]}

## Checklist

{checklist}
"""


def salvar_matriz_melhorias_markdown() -> Dict[str, Any]:
    saude = calcular_saude_feedback_pacote_premium()
    CAMINHO_MATRIZ_MELHORIAS_MD.write_text(gerar_matriz_melhorias_markdown(saude), encoding="utf-8")
    return {"ok": True, "arquivo": str(CAMINHO_MATRIZ_MELHORIAS_MD), "score_feedback_pacote": saude["score_feedback_pacote"]}


def salvar_roteiro_feedback_markdown() -> Dict[str, Any]:
    saude = calcular_saude_feedback_pacote_premium()
    CAMINHO_ROTEIRO_FEEDBACK_MD.write_text(gerar_roteiro_feedback_markdown(saude), encoding="utf-8")
    return {"ok": True, "arquivo": str(CAMINHO_ROTEIRO_FEEDBACK_MD), "score_feedback_pacote": saude["score_feedback_pacote"]}


def salvar_checklist_feedback_markdown() -> Dict[str, Any]:
    saude = calcular_saude_feedback_pacote_premium()
    CAMINHO_CHECKLIST_FEEDBACK_MD.write_text(gerar_checklist_feedback_markdown(saude), encoding="utf-8")
    return {"ok": True, "arquivo": str(CAMINHO_CHECKLIST_FEEDBACK_MD), "score_feedback_pacote": saude["score_feedback_pacote"]}


def gerar_manifesto_feedback_pacote() -> Dict[str, Any]:
    saude = calcular_saude_feedback_pacote_premium()
    manifesto = {
        "versao": VERSAO_FEEDBACK_PACOTE_PREMIUM_VALORIS,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "saude": saude,
        "roteiro_perguntas": ROTEIRO_PERGUNTAS,
        "checklist": CHECKLIST_FEEDBACK,
        "estrategia": {
            "objetivo": "Validar se o pacote premium é claro, útil e pagável.",
            "proxima_versao": "Converter feedback em melhoria de produto, copy e onboarding.",
            "regra": "Não escalar oferta premium sem feedback real de entrega.",
        },
    }

    CAMINHO_MANIFESTO_FEEDBACK_PACOTE.write_text(json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifesto


def _injetar_css_feedback() -> None:
    st.markdown(
        """
        <style>
            .feedback-pacote-hero {
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
            .feedback-pacote-eyebrow {
                color: #d6b56d;
                font-size: 0.74rem;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                font-weight: 880;
                margin-bottom: 0.35rem;
            }
            .feedback-pacote-title {
                color: #f4f7fb;
                font-size: clamp(1.8rem, 5.5vw, 3.25rem);
                font-weight: 950;
                line-height: 1.02;
                letter-spacing: -0.058em;
                margin-bottom: 0.55rem;
            }
            .feedback-pacote-subtitle {
                color: rgba(244, 247, 251, 0.75);
                font-size: clamp(0.94rem, 2.2vw, 1.06rem);
                line-height: 1.56;
                max-width: 1050px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def renderizar_feedback_pacote_premium_valoris() -> None:
    _injetar_css_feedback()

    st.markdown(
        f"""
        <div class="feedback-pacote-hero">
            <div class="feedback-pacote-eyebrow">Valoris • Feedback Pacote Premium • v{VERSAO_FEEDBACK_PACOTE_PREMIUM_VALORIS}</div>
            <div class="feedback-pacote-title">Valide se a entrega parece premium.</div>
            <div class="feedback-pacote-subtitle">
                Colete clareza, valor percebido, objeções, intenção de pagamento e melhorias antes de escalar a oferta.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    saude = calcular_saude_feedback_pacote_premium()
    pacote = saude["pacote"]

    st.markdown("### Diagnóstico do feedback")
    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Score Feedback", f"{saude['score_feedback_pacote']}/100")

    with col_2:
        st.metric("Feedbacks", saude["feedbacks_total"])

    with col_3:
        st.metric("Pagariam", saude["pagantes_potenciais"])

    with col_4:
        st.metric("Nota média", saude["nota_media"])

    st.progress(saude["score_feedback_pacote"] / 100)

    if saude["score_feedback_pacote"] >= 82:
        st.success(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    elif saude["feedbacks_total"] >= 1:
        st.warning(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    else:
        st.info(f"**{saude['decisao']}** — {saude['proximo_passo']}")

    st.divider()

    st.markdown("### Registrar feedback do pacote")

    with st.form("form_feedback_pacote_premium"):
        col_a, col_b = st.columns(2)

        with col_a:
            fundador_nome = st.text_input("Nome do fundador", value="Fundador Exemplo")
            fundador_email = st.text_input("E-mail", value="fundador@exemplo.com")
            ticker_base = st.text_input("Ticker base", value=pacote.get("ticker_base", "PENDENTE"))
            empresa_base = st.text_input("Empresa base", value=pacote.get("empresa_base", ""))
            clareza_entrega = st.slider("Clareza da entrega", 0, 10, 8)
            valor_percebido = st.slider("Valor percebido", 0, 10, 8)
            utilidade_pratica = st.slider("Utilidade prática", 0, 10, 8)
            confianca_analise = st.slider("Confiança na análise", 0, 10, 8)

        with col_b:
            facilidade_consumo = st.slider("Facilidade de consumir", 0, 10, 7)
            vontade_continuar = st.slider("Vontade de continuar usando", 0, 10, 8)
            pagaria_por_isso = st.checkbox("Pagaria por isso?", value=True)
            preco_justo = st.number_input("Preço justo percebido", min_value=0.0, value=59.0, step=10.0)
            nota_geral = st.slider("Nota geral", 0, 10, 8)
            melhor_parte = st.text_area("Melhor parte do pacote", height=80)
            parte_confusa = st.text_area("Parte confusa", height=80)
            principal_objeção = st.text_area("Principal objeção", height=80)
            feature_mais_desejada = st.text_area("Feature mais desejada", height=80)
            observacoes = st.text_area("Observações", height=80)

        enviado = st.form_submit_button("Salvar feedback")

        if enviado:
            registro = salvar_feedback_pacote_premium(
                {
                    "fundador_nome": fundador_nome,
                    "fundador_email": fundador_email,
                    "ticker_base": ticker_base,
                    "empresa_base": empresa_base,
                    "clareza_entrega": clareza_entrega,
                    "valor_percebido": valor_percebido,
                    "utilidade_pratica": utilidade_pratica,
                    "confianca_analise": confianca_analise,
                    "facilidade_consumo": facilidade_consumo,
                    "vontade_continuar": vontade_continuar,
                    "pagaria_por_isso": pagaria_por_isso,
                    "preco_justo": preco_justo,
                    "melhor_parte": melhor_parte,
                    "parte_confusa": parte_confusa,
                    "principal_objeção": principal_objeção,
                    "feature_mais_desejada": feature_mais_desejada,
                    "nota_geral": nota_geral,
                    "observacoes": observacoes,
                }
            )
            st.success(f"Feedback salvo: {registro['id']}")
            st.rerun()

    st.divider()

    st.markdown("### Matriz de melhorias")
    st.markdown(gerar_matriz_melhorias_markdown(saude))

    if saude["metricas_feedback"]["ultimos_feedbacks"]:
        st.markdown("### Últimos feedbacks")
        st.dataframe(saude["metricas_feedback"]["ultimos_feedbacks"], width="stretch", hide_index=True)

    st.divider()

    col_btn_1, col_btn_2, col_btn_3, col_btn_4 = st.columns(4)

    with col_btn_1:
        if st.button("Gerar feedback exemplo", key="feedback_pacote_exemplo"):
            registro = gerar_feedback_pacote_exemplo()
            st.success(f"Feedback exemplo criado: {registro['id']}")
            st.rerun()

    with col_btn_2:
        if st.button("Gerar manifesto", key="feedback_pacote_manifesto"):
            manifesto = gerar_manifesto_feedback_pacote()
            st.success(f"Manifesto gerado: {CAMINHO_MANIFESTO_FEEDBACK_PACOTE}")
            st.json({"versao": manifesto["versao"], "score": manifesto["saude"]["score_feedback_pacote"]})

    with col_btn_3:
        if st.button("Salvar matriz .md", key="feedback_pacote_matriz"):
            retorno = salvar_matriz_melhorias_markdown()
            st.success(f"Matriz salva: {retorno['arquivo']}")
            st.json(retorno)

    with col_btn_4:
        if st.button("Salvar roteiro .md", key="feedback_pacote_roteiro"):
            retorno = salvar_roteiro_feedback_markdown()
            st.success(f"Roteiro salvo: {retorno['arquivo']}")
            st.json(retorno)

    if st.button("Salvar checklist .md", key="feedback_pacote_checklist"):
        retorno = salvar_checklist_feedback_markdown()
        st.success(f"Checklist salvo: {retorno['arquivo']}")
        st.json(retorno)

    if st.button("Salvar decisão Feedback Pacote", key="feedback_pacote_decisao"):
        registro = salvar_decisao_feedback_pacote(
            saude,
            observacoes="Decisão gerada pelo feedback do pacote premium.",
        )
        st.success(f"Decisão salva: {registro['decisao']}")
        st.rerun()

    st.download_button(
        "Baixar matriz de melhorias (.md)",
        data=gerar_matriz_melhorias_markdown(saude),
        file_name="MATRIZ_MELHORIAS_PACOTE_PREMIUM_VALORIS.md",
        mime="text/markdown",
        key="download_matriz_feedback_pacote",
    )

    st.download_button(
        "Baixar feedbacks (.csv)",
        data=gerar_csv_feedbacks_pacote(),
        file_name="feedbacks_pacote_premium_valoris.csv",
        mime="text/csv",
        key="download_feedbacks_pacote",
    )

    st.download_button(
        "Baixar decisões feedback (.csv)",
        data=gerar_csv_decisoes_feedback_pacote(),
        file_name="decisoes_feedback_pacote_premium_valoris.csv",
        mime="text/csv",
        key="download_decisoes_feedback_pacote",
    )


def executar_autoteste_feedback_pacote_premium_valoris() -> List[Dict[str, str]]:
    saude = calcular_saude_feedback_pacote_premium()

    return [
        {
            "teste": "versao_feedback_pacote",
            "status": "OK" if VERSAO_FEEDBACK_PACOTE_PREMIUM_VALORIS == "3.8.89" else "FALHA",
            "detalhe": VERSAO_FEEDBACK_PACOTE_PREMIUM_VALORIS,
        },
        {
            "teste": "score_feedback_pacote",
            "status": "OK" if 0 <= saude["score_feedback_pacote"] <= 100 else "FALHA",
            "detalhe": str(saude["score_feedback_pacote"]),
        },
        {
            "teste": "matriz_markdown",
            "status": "OK" if "# Matriz de Melhorias" in gerar_matriz_melhorias_markdown(saude) else "FALHA",
            "detalhe": "gerar_matriz_melhorias_markdown",
        },
        {
            "teste": "renderizador",
            "status": "OK" if callable(renderizar_feedback_pacote_premium_valoris) else "FALHA",
            "detalhe": "renderizar_feedback_pacote_premium_valoris",
        },
    ]
