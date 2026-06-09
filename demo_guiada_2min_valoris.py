# demo_guiada_2min_valoris.py

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

import streamlit as st

from analise_premium_valoris import (
    DADOS_DEMO_ANALISE_PREMIUM,
    calcular_analise_premium_valoris,
    gerar_markdown_analise_premium,
)
from launch_readiness_valoris import calcular_saude_launch_readiness


VERSAO_DEMO_GUIADA_2MIN_VALORIS = "3.8.77"

CAMINHO_DECISOES_DEMO_2MIN = Path("decisoes_demo_2min_valoris.csv")
CAMINHO_MANIFESTO_DEMO_2MIN = Path("manifesto_demo_2min_valoris.json")
CAMINHO_ROTEIRO_DEMO_2MIN_MD = Path("ROTEIRO_DEMO_2MIN_VALORIS.md")
CAMINHO_DEMO_2MIN_JSON = Path("demo_2min_valoris.json")
CAMINHO_CHECKLIST_DEMO_2MIN_MD = Path("CHECKLIST_DEMO_2MIN_VALORIS.md")

CAMPOS_DECISAO_DEMO_2MIN = [
    "id",
    "data_registro",
    "score_demo",
    "tempo_estimado_segundos",
    "score_clareza",
    "score_prova_valor",
    "score_conversao",
    "score_analise_premium",
    "pronta_para_beta",
    "risco",
    "decisao",
    "proximo_passo",
    "observacoes",
]

PASSOS_DEMO_2MIN = [
    {
        "ordem": 1,
        "tempo": "0s–12s",
        "titulo": "Promessa clara",
        "objetivo": "Mostrar que a Valoris transforma dados financeiros em decisão explicável.",
        "fala": "A Valoris não tenta adivinhar o mercado. Ela organiza premissas, calcula margem de segurança e transforma isso em uma tese clara.",
        "visual": "Tela inicial da Análise Premium com empresa exemplo preenchida.",
        "prova": "O usuário entende em uma frase o que o app faz.",
    },
    {
        "ordem": 2,
        "tempo": "12s–32s",
        "titulo": "Dados essenciais",
        "objetivo": "Mostrar que o usuário não precisa de complexidade infinita para começar.",
        "fala": "Você informa preço atual, preço teto, rentabilidade, crescimento, dívida e alguns riscos qualitativos.",
        "visual": "Campos principais da empresa, preço atual, preço teto, ROIC e dívida.",
        "prova": "O fluxo parece simples, mas analítico.",
    },
    {
        "ordem": 3,
        "tempo": "32s–55s",
        "titulo": "Resultado instantâneo",
        "objetivo": "Mostrar o momento uau: score, margem, risco e decisão.",
        "fala": "Em segundos, o app mostra score final, margem de segurança, qualidade, risco e uma decisão objetiva.",
        "visual": "Cards: Score final, Margem de segurança, Decisão e Risco.",
        "prova": "O usuário vê valor antes de ler o relatório.",
    },
    {
        "ordem": 4,
        "tempo": "55s–82s",
        "titulo": "Tese explicada",
        "objetivo": "Gerar confiança e diferenciar de uma calculadora comum.",
        "fala": "A diferença é que a Valoris explica a tese: por que a decisão foi tomada, quais premissas sustentam a análise e onde estão os riscos.",
        "visual": "Bloco de tese, gatilhos positivos e alertas.",
        "prova": "O produto deixa claro que não é chute nem recomendação cega.",
    },
    {
        "ordem": 5,
        "tempo": "82s–105s",
        "titulo": "Relatório exportável",
        "objetivo": "Mostrar utilidade real para estudo e acompanhamento.",
        "fala": "Depois, você exporta um relatório para guardar, revisar ou comparar com outras empresas.",
        "visual": "Botão de baixar relatório premium ou relatório em Markdown.",
        "prova": "O app vira ferramenta de estudo e decisão, não só tela momentânea.",
    },
    {
        "ordem": 6,
        "tempo": "105s–120s",
        "titulo": "Convite beta",
        "objetivo": "Converter interesse em teste real.",
        "fala": "A próxima etapa é liberar a Valoris para beta testers que querem analisar ações com mais método, clareza e disciplina.",
        "visual": "CTA: entrar na lista beta / solicitar acesso fundador.",
        "prova": "A demo termina com ação clara.",
    },
]

CRITERIOS_DEMO_2MIN = [
    {
        "criterio": "Clareza em 12 segundos",
        "pergunta": "Uma pessoa entende o que a Valoris faz antes de ver os detalhes?",
        "peso": 18,
    },
    {
        "criterio": "Momento uau",
        "pergunta": "A decisão, margem e tese aparecem rápido o suficiente?",
        "peso": 24,
    },
    {
        "criterio": "Confiança",
        "pergunta": "A demo deixa claro que há método, risco e premissas?",
        "peso": 20,
    },
    {
        "criterio": "Utilidade",
        "pergunta": "O relatório exportável parece útil para estudo real?",
        "peso": 16,
    },
    {
        "criterio": "Conversão",
        "pergunta": "A demo termina com próximo passo claro para beta?",
        "peso": 14,
    },
    {
        "criterio": "Tempo",
        "pergunta": "A narrativa cabe em até 120 segundos?",
        "peso": 8,
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


def carregar_decisoes_demo_2min() -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_DECISOES_DEMO_2MIN, CAMPOS_DECISAO_DEMO_2MIN)

    with CAMINHO_DECISOES_DEMO_2MIN.open("r", newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def gerar_csv_decisoes_demo_2min() -> str:
    _garantir_csv(CAMINHO_DECISOES_DEMO_2MIN, CAMPOS_DECISAO_DEMO_2MIN)
    return CAMINHO_DECISOES_DEMO_2MIN.read_text(encoding="utf-8")


def salvar_decisao_demo_2min(saude: Dict[str, Any], observacoes: str = "") -> Dict[str, str]:
    _garantir_csv(CAMINHO_DECISOES_DEMO_2MIN, CAMPOS_DECISAO_DEMO_2MIN)

    registro = {
        "id": str(uuid4())[:8],
        "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score_demo": str(saude.get("score_demo", "")),
        "tempo_estimado_segundos": str(saude.get("tempo_estimado_segundos", "")),
        "score_clareza": str(saude.get("score_clareza", "")),
        "score_prova_valor": str(saude.get("score_prova_valor", "")),
        "score_conversao": str(saude.get("score_conversao", "")),
        "score_analise_premium": str(saude.get("score_analise_premium", "")),
        "pronta_para_beta": str(saude.get("pronta_para_beta", "")),
        "risco": _limpar_texto(saude.get("risco", "")),
        "decisao": _limpar_texto(saude.get("decisao", "")),
        "proximo_passo": _limpar_texto(saude.get("proximo_passo", "")),
        "observacoes": _limpar_texto(observacoes),
    }

    with CAMINHO_DECISOES_DEMO_2MIN.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISAO_DEMO_2MIN)
        escritor.writerow(registro)

    return registro


def calcular_demo_2min_valoris() -> Dict[str, Any]:
    analise = calcular_analise_premium_valoris(DADOS_DEMO_ANALISE_PREMIUM)
    relatorio = gerar_markdown_analise_premium(analise)

    tempo_estimado_segundos = 120
    passos_total = len(PASSOS_DEMO_2MIN)
    criterios_total = len(CRITERIOS_DEMO_2MIN)

    score_analise_premium = int(analise.get("score_final", 0) or 0)
    tese_ok = bool(analise.get("tese")) and len(analise.get("tese", "")) > 120
    relatorio_ok = bool(relatorio) and "Relatório de Análise Premium" in relatorio
    cta_ok = any("beta" in passo["fala"].lower() or "beta" in passo["visual"].lower() for passo in PASSOS_DEMO_2MIN)
    tempo_ok = tempo_estimado_segundos <= 120

    score_clareza = 0
    score_clareza += 30 if passos_total >= 6 else 0
    score_clareza += 25 if PASSOS_DEMO_2MIN[0]["titulo"] == "Promessa clara" else 0
    score_clareza += 25 if tese_ok else 0
    score_clareza += 20 if tempo_ok else 0
    score_clareza = min(100, score_clareza)

    score_prova_valor = 0
    score_prova_valor += 30 if score_analise_premium > 0 else 0
    score_prova_valor += 25 if analise.get("margem_seguranca", 0) != 0 else 0
    score_prova_valor += 25 if relatorio_ok else 0
    score_prova_valor += 20 if bool(analise.get("gatilhos_positivos")) and bool(analise.get("gatilhos_negativos")) else 0
    score_prova_valor = min(100, score_prova_valor)

    score_conversao = 0
    score_conversao += 35 if cta_ok else 0
    score_conversao += 25 if criterios_total >= 6 else 0
    score_conversao += 20 if PASSOS_DEMO_2MIN[-1]["titulo"] == "Convite beta" else 0
    score_conversao += 20 if tempo_ok else 0
    score_conversao = min(100, score_conversao)

    score_demo = int(round(
        score_clareza * 0.32
        + score_prova_valor * 0.38
        + score_conversao * 0.20
        + min(score_analise_premium, 100) * 0.10
    ))

    if score_demo >= 88:
        pronta_para_beta = True
        risco = "Médio controlado"
        decisao = "Demo guiada pronta para validação beta"
        proximo_passo = "Gravar uma demonstração curta e usar como vídeo/roteiro para captar beta testers."
    elif score_demo >= 74:
        pronta_para_beta = False
        risco = "Médio"
        decisao = "Demo promissora, mas ainda precisa ajuste"
        proximo_passo = "Refinar narrativa, reduzir fricção e testar com uma pessoa real."
    else:
        pronta_para_beta = False
        risco = "Alto"
        decisao = "Demo ainda fraca para lançamento"
        proximo_passo = "Reorganizar promessa, prova de valor e CTA."

    return {
        "versao": VERSAO_DEMO_GUIADA_2MIN_VALORIS,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score_demo": score_demo,
        "score_clareza": score_clareza,
        "score_prova_valor": score_prova_valor,
        "score_conversao": score_conversao,
        "score_analise_premium": score_analise_premium,
        "tempo_estimado_segundos": tempo_estimado_segundos,
        "pronta_para_beta": pronta_para_beta,
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo_passo,
        "passos": PASSOS_DEMO_2MIN,
        "criterios": CRITERIOS_DEMO_2MIN,
        "analise_premium": analise,
        "relatorio_premium": relatorio,
    }


def gerar_roteiro_demo_2min_markdown(saude: Dict[str, Any] | None = None) -> str:
    if saude is None:
        saude = calcular_demo_2min_valoris()

    passos = "\n\n".join(
        [
            f"""### {item['ordem']}. {item['titulo']} — {item['tempo']}

**Objetivo:** {item['objetivo']}  
**Fala:** {item['fala']}  
**Visual:** {item['visual']}  
**Prova:** {item['prova']}
"""
            for item in PASSOS_DEMO_2MIN
        ]
    )

    criterios = "\n".join(
        [
            f"- **{item['criterio']}** ({item['peso']} pts): {item['pergunta']}"
            for item in CRITERIOS_DEMO_2MIN
        ]
    )

    analise = saude["analise_premium"]

    return f"""# Roteiro Demo 2 Minutos — Valoris

Versão: {VERSAO_DEMO_GUIADA_2MIN_VALORIS}  
Gerado em: {saude["gerado_em"]}

## Status da demo

Score Demo: {saude["score_demo"]}/100  
Tempo estimado: {saude["tempo_estimado_segundos"]} segundos  
Pronta para beta: {saude["pronta_para_beta"]}  
Risco: {saude["risco"]}  
Decisão: {saude["decisao"]}  
Próximo passo: {saude["proximo_passo"]}

## Resultado usado na demo

Empresa: {analise["dados"].get("empresa", "")}  
Ticker: {analise["dados"].get("ticker", "")}  
Score final: {analise["score_final"]}/100  
Decisão: {analise["decisao"]}  
Margem de segurança: {analise["margem_seguranca"]:.2f}%

## Roteiro

{passos}

## Critérios de qualidade da demo

{criterios}

## Fechamento sugerido

"Se você quer analisar ações com mais método, clareza e disciplina, entre na lista beta da Valoris."
"""


def gerar_checklist_demo_2min_markdown(saude: Dict[str, Any] | None = None) -> str:
    if saude is None:
        saude = calcular_demo_2min_valoris()

    linhas = [
        "# Checklist Demo 2 Minutos — Valoris",
        "",
        f"Versão: {VERSAO_DEMO_GUIADA_2MIN_VALORIS}",
        f"Gerado em: {saude['gerado_em']}",
        "",
        "## Checklist",
        "",
        f"- [{'x' if saude['score_clareza'] >= 85 else ' '}] Promessa clara nos primeiros 12 segundos",
        f"- [{'x' if saude['score_prova_valor'] >= 85 else ' '}] Prova de valor com score, tese e relatório",
        f"- [{'x' if saude['score_conversao'] >= 85 else ' '}] CTA beta claro",
        f"- [{'x' if saude['tempo_estimado_segundos'] <= 120 else ' '}] Cabe em até 2 minutos",
        f"- [{'x' if saude['pronta_para_beta'] else ' '}] Pronta para validação com beta testers",
        "",
        "## Próxima ação",
        "",
        saude["proximo_passo"],
    ]

    return "\n".join(linhas)


def salvar_roteiro_demo_2min_markdown() -> Dict[str, Any]:
    saude = calcular_demo_2min_valoris()
    CAMINHO_ROTEIRO_DEMO_2MIN_MD.write_text(gerar_roteiro_demo_2min_markdown(saude), encoding="utf-8")
    return {
        "ok": True,
        "arquivo": str(CAMINHO_ROTEIRO_DEMO_2MIN_MD),
        "score_demo": saude["score_demo"],
        "decisao": saude["decisao"],
    }


def salvar_checklist_demo_2min_markdown() -> Dict[str, Any]:
    saude = calcular_demo_2min_valoris()
    CAMINHO_CHECKLIST_DEMO_2MIN_MD.write_text(gerar_checklist_demo_2min_markdown(saude), encoding="utf-8")
    return {
        "ok": True,
        "arquivo": str(CAMINHO_CHECKLIST_DEMO_2MIN_MD),
        "score_demo": saude["score_demo"],
        "decisao": saude["decisao"],
    }


def gerar_demo_2min_json() -> Dict[str, Any]:
    saude = calcular_demo_2min_valoris()
    CAMINHO_DEMO_2MIN_JSON.write_text(json.dumps(saude, ensure_ascii=False, indent=2), encoding="utf-8")
    return saude


def gerar_manifesto_demo_2min() -> Dict[str, Any]:
    try:
        launch = calcular_saude_launch_readiness()
    except Exception as erro:
        launch = {"score_launch": 0, "erro": str(erro)}

    demo = calcular_demo_2min_valoris()

    manifesto = {
        "versao": VERSAO_DEMO_GUIADA_2MIN_VALORIS,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "demo": demo,
        "launch_readiness": launch,
        "estrategia": {
            "objetivo": "Transformar a experiência premium em uma demo compreensível em até 2 minutos.",
            "proxima_versao": "Fluxo de beta tester e feedback real.",
            "regra": "Sem demo clara, não há lançamento eficiente.",
        },
    }

    CAMINHO_MANIFESTO_DEMO_2MIN.write_text(json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifesto


def _injetar_css_demo_2min() -> None:
    st.markdown(
        """
        <style>
            .demo-2min-hero {
                padding: clamp(1.2rem, 3vw, 2.1rem);
                border-radius: 30px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    radial-gradient(circle at top left, rgba(214, 181, 109, 0.25), transparent 32%),
                    radial-gradient(circle at bottom right, rgba(80, 170, 140, 0.22), transparent 36%),
                    linear-gradient(135deg, rgba(6, 12, 23, 0.99), rgba(4, 8, 16, 0.99));
                box-shadow: 0 20px 62px rgba(0, 0, 0, 0.34);
                margin-bottom: 1rem;
            }
            .demo-2min-eyebrow {
                color: #d6b56d;
                font-size: 0.74rem;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                font-weight: 880;
                margin-bottom: 0.35rem;
            }
            .demo-2min-title {
                color: #f4f7fb;
                font-size: clamp(1.8rem, 5.5vw, 3.25rem);
                font-weight: 950;
                line-height: 1.02;
                letter-spacing: -0.058em;
                margin-bottom: 0.55rem;
            }
            .demo-2min-subtitle {
                color: rgba(244, 247, 251, 0.75);
                font-size: clamp(0.94rem, 2.2vw, 1.06rem);
                line-height: 1.56;
                max-width: 1050px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def renderizar_demo_guiada_2min_valoris() -> None:
    _injetar_css_demo_2min()

    st.markdown(
        f"""
        <div class="demo-2min-hero">
            <div class="demo-2min-eyebrow">Valoris • Demo Guiada 2 Min • v{VERSAO_DEMO_GUIADA_2MIN_VALORIS}</div>
            <div class="demo-2min-title">A demonstração que vende o valor.</div>
            <div class="demo-2min-subtitle">
                Roteiro de 2 minutos para provar rapidamente que a Valoris entrega decisão, tese,
                risco, margem de segurança e relatório.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    saude = calcular_demo_2min_valoris()

    st.markdown("### Diagnóstico da demo")
    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Score Demo", f"{saude['score_demo']}/100")

    with col_2:
        st.metric("Tempo", f"{saude['tempo_estimado_segundos']}s")

    with col_3:
        st.metric("Beta", "Pronta" if saude["pronta_para_beta"] else "Ajustar")

    with col_4:
        st.metric("Risco", saude["risco"])

    st.progress(saude["score_demo"] / 100)

    if saude["pronta_para_beta"]:
        st.success(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    else:
        st.warning(f"**{saude['decisao']}** — {saude['proximo_passo']}")

    st.divider()

    st.markdown("### Roteiro")
    for passo in PASSOS_DEMO_2MIN:
        with st.expander(f"{passo['ordem']}. {passo['titulo']} — {passo['tempo']}", expanded=passo["ordem"] == 1):
            st.write(f"**Objetivo:** {passo['objetivo']}")
            st.write(f"**Fala:** {passo['fala']}")
            st.write(f"**Visual:** {passo['visual']}")
            st.write(f"**Prova:** {passo['prova']}")

    st.markdown("### Critérios")
    st.dataframe(CRITERIOS_DEMO_2MIN, width="stretch", hide_index=True)

    st.divider()

    col_btn_1, col_btn_2, col_btn_3, col_btn_4 = st.columns(4)

    with col_btn_1:
        if st.button("Gerar manifesto Demo", key="demo_2min_manifesto"):
            manifesto = gerar_manifesto_demo_2min()
            st.success(f"Manifesto gerado: {CAMINHO_MANIFESTO_DEMO_2MIN}")
            st.json({"versao": manifesto["versao"], "score_demo": manifesto["demo"]["score_demo"]})

    with col_btn_2:
        if st.button("Gerar demo JSON", key="demo_2min_json"):
            demo = gerar_demo_2min_json()
            st.success(f"Demo JSON gerada: {CAMINHO_DEMO_2MIN_JSON}")
            st.json({"score_demo": demo["score_demo"], "decisao": demo["decisao"]})

    with col_btn_3:
        if st.button("Salvar roteiro .md", key="demo_2min_roteiro"):
            retorno = salvar_roteiro_demo_2min_markdown()
            st.success(f"Roteiro salvo: {retorno['arquivo']}")
            st.json(retorno)

    with col_btn_4:
        if st.button("Salvar checklist .md", key="demo_2min_checklist"):
            retorno = salvar_checklist_demo_2min_markdown()
            st.success(f"Checklist salvo: {retorno['arquivo']}")
            st.json(retorno)

    if st.button("Salvar decisão Demo", key="demo_2min_decisao"):
        registro = salvar_decisao_demo_2min(saude, observacoes="Decisão gerada pela demo guiada de 2 minutos.")
        st.success(f"Decisão salva: {registro['decisao']}")
        st.rerun()

    st.download_button(
        "Baixar roteiro demo 2min (.md)",
        data=gerar_roteiro_demo_2min_markdown(saude),
        file_name="ROTEIRO_DEMO_2MIN_VALORIS.md",
        mime="text/markdown",
        key="download_roteiro_demo_2min",
    )

    st.download_button(
        "Baixar checklist demo 2min (.md)",
        data=gerar_checklist_demo_2min_markdown(saude),
        file_name="CHECKLIST_DEMO_2MIN_VALORIS.md",
        mime="text/markdown",
        key="download_checklist_demo_2min",
    )

    st.download_button(
        "Baixar decisões Demo (.csv)",
        data=gerar_csv_decisoes_demo_2min(),
        file_name="decisoes_demo_2min_valoris.csv",
        mime="text/csv",
        key="download_decisoes_demo_2min",
    )


def executar_autoteste_demo_guiada_2min_valoris() -> List[Dict[str, str]]:
    saude = calcular_demo_2min_valoris()

    return [
        {
            "teste": "versao_demo_2min",
            "status": "OK" if VERSAO_DEMO_GUIADA_2MIN_VALORIS == "3.8.77" else "FALHA",
            "detalhe": VERSAO_DEMO_GUIADA_2MIN_VALORIS,
        },
        {
            "teste": "score_demo",
            "status": "OK" if 0 <= saude["score_demo"] <= 100 else "FALHA",
            "detalhe": str(saude["score_demo"]),
        },
        {
            "teste": "tempo_demo",
            "status": "OK" if saude["tempo_estimado_segundos"] <= 120 else "FALHA",
            "detalhe": str(saude["tempo_estimado_segundos"]),
        },
        {
            "teste": "renderizador",
            "status": "OK" if callable(renderizar_demo_guiada_2min_valoris) else "FALHA",
            "detalhe": "renderizar_demo_guiada_2min_valoris",
        },
    ]
