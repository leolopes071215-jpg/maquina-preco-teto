# valor_comercial_valoris.py
# Valoris — Valor Comercial e Pitch v3.13.4
# ------------------------------------------------------------
# Objetivo:
# - Transformar o produto técnico em uma narrativa comercial clara.
# - Criar pitch curto, pitch médio, pitch executivo e página de valor.
# - Organizar dores, promessa, diferenciais, provas operacionais e objeções.
# - Registrar revisão de posicionamento antes de apresentar para usuários beta.
# - Não altera dados financeiros reais.
# - Não envia mensagens automaticamente.

from __future__ import annotations

import csv
import json
from collections import Counter, deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st


VERSAO_VALOR_COMERCIAL_VALORIS = "3.13.4"

CAMINHO_REVISOES = Path("revisoes_valor_comercial_valoris.csv")
CAMINHO_RELATORIO = Path("RELATORIO_VALOR_COMERCIAL_VALORIS.md")
CAMINHO_MANIFESTO = Path("manifesto_valor_comercial_valoris.json")

CAMPOS_REVISOES = [
    "data_hora",
    "publico_alvo",
    "promessa",
    "score_pitch",
    "clareza",
    "forca_comercial",
    "confianca",
    "diferenciacao",
    "responsavel",
    "decisao",
    "proximo_passo",
    "observacao",
]


PUBLICOS_ALVO: Dict[str, Dict[str, str]] = {
    "Investidor iniciante": {
        "dor": "Tem vontade de investir melhor, mas se perde entre vídeos, planilhas, opiniões e emoções.",
        "desejo": "Ter um caminho claro para analisar, decidir e acompanhar sem se sentir perdido.",
        "linguagem": "Simples, didática, direta e sem excesso de jargão.",
        "promessa": "Transforme dúvidas sobre ativos em decisões organizadas e acompanháveis.",
    },
    "Investidor intermediário": {
        "dor": "Já estuda ações, FIIs ou ETFs, mas não tem um sistema para acompanhar tese, preço teto, alertas e revisões.",
        "desejo": "Ter método, disciplina e histórico das próprias decisões.",
        "linguagem": "Racional, técnica na medida certa, com foco em processo e gestão de decisão.",
        "promessa": "Saia da análise solta para um processo completo de decisão, acompanhamento e revisão.",
    },
    "Investidor fundamentalista": {
        "dor": "Analisa dados, mas precisa de uma camada operacional para transformar tese em ação e revisão contínua.",
        "desejo": "Ter um cockpit decisório que una valuation, tese, pipeline, alertas e comunicação.",
        "linguagem": "Cética, numérica, conservadora e orientada a processo.",
        "promessa": "Organize valuation, decisão e acompanhamento em um sistema operacional de investimentos.",
    },
    "Usuário beta / early adopter": {
        "dor": "Quer testar uma ferramenta poderosa, mas precisa entender rapidamente o valor do produto.",
        "desejo": "Ver uma experiência clara, guiada e útil em poucos minutos.",
        "linguagem": "Premium, objetiva, estratégica e demonstrável.",
        "promessa": "Entenda em 5 minutos como o Valoris transforma análise em decisão acompanhável.",
    },
}


OBJECOES = [
    {
        "objecao": "Isso é só mais uma planilha?",
        "resposta": "Não. Uma planilha guarda dados; o Valoris organiza uma jornada de decisão: análise, preço teto, pipeline, alerta, comunicação, resultado e cockpit.",
    },
    {
        "objecao": "O sistema promete lucro?",
        "resposta": "Não. O Valoris não promete lucro. Ele ajuda a estruturar raciocínio, disciplina, revisão e acompanhamento de decisões.",
    },
    {
        "objecao": "Por que não usar apenas um app de carteira?",
        "resposta": "Apps de carteira mostram posição. O Valoris foca no processo antes e depois da decisão: tese, margem, preço teto, alerta, revisão e aprendizado.",
    },
    {
        "objecao": "Parece complexo demais.",
        "resposta": "A arquitetura é profunda, mas a experiência beta é guiada por Jornada Beta, Modos de Uso e Demo Premium.",
    },
    {
        "objecao": "Para quem isso é mais útil?",
        "resposta": "Para quem quer parar de tomar decisões soltas e começar a acompanhar investimentos com método, histórico e critérios.",
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


def _garantir_csv(caminho: Path, campos: List[str]) -> None:
    if caminho.exists():
        return
    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()


def carregar_revisoes() -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_REVISOES, CAMPOS_REVISOES)

    try:
        with CAMINHO_REVISOES.open("r", newline="", encoding="utf-8") as arquivo:
            leitor = csv.DictReader(arquivo)
            return list(deque(leitor, maxlen=1000))
    except Exception:
        return []


def salvar_revisao_valor_comercial(
    publico_alvo: str,
    promessa: str,
    score_pitch: int,
    clareza: int,
    forca_comercial: int,
    confianca: int,
    diferenciacao: int,
    responsavel: str,
    decisao: str,
    proximo_passo: str,
    observacao: str = "",
) -> Path:
    _garantir_csv(CAMINHO_REVISOES, CAMPOS_REVISOES)

    with CAMINHO_REVISOES.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_REVISOES)
        escritor.writerow(
            {
                "data_hora": _agora_iso(),
                "publico_alvo": _txt(publico_alvo),
                "promessa": _txt(promessa),
                "score_pitch": _int(score_pitch),
                "clareza": _int(clareza),
                "forca_comercial": _int(forca_comercial),
                "confianca": _int(confianca),
                "diferenciacao": _int(diferenciacao),
                "responsavel": _txt(responsavel),
                "decisao": _txt(decisao),
                "proximo_passo": _txt(proximo_passo),
                "observacao": _txt(observacao),
            }
        )

    return CAMINHO_REVISOES


def carregar_metricas_externas() -> Dict[str, Dict[str, Any]]:
    metricas: Dict[str, Dict[str, Any]] = {}

    modulos = [
        ("checklist", "checklist_produto_vendavel_valoris", "calcular_metricas_produto_vendavel"),
        ("demo", "demo_premium_valoris", "calcular_metricas_demo"),
        ("modos", "modos_uso_valoris", "calcular_metricas_modos_uso"),
        ("jornada", "jornada_beta_valoris", "calcular_metricas_jornada_beta"),
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


def montar_proposta_valor(publico: str) -> Dict[str, Any]:
    info = PUBLICOS_ALVO.get(publico, PUBLICOS_ALVO["Investidor intermediário"])

    headline = "Valoris: transforme análise de investimentos em decisão acompanhável"

    subheadline = (
        "Um sistema operacional para analisar ativos, calcular preço teto, organizar decisões, "
        "acompanhar alertas, registrar comunicações e aprender com os resultados."
    )

    promessa_curta = info["promessa"]

    diferenciais = [
        "Não é só calculadora: é fluxo completo de decisão.",
        "Une preço teto, tese, pipeline, radar, agenda, comunicação e resultado.",
        "Mantém controle humano: nada é enviado ou decidido automaticamente.",
        "Cria histórico e rastreabilidade para reduzir decisões emocionais.",
        "Organiza a experiência por Jornada Beta, Modos de Uso e Demo Premium.",
    ]

    provas = [
        "Motor de análise com preço teto e margem de segurança.",
        "Pipeline para transformar tese em ação acompanhável.",
        "Radar, alertas e agenda para revisar decisões.",
        "Cockpit Principal para visão executiva.",
        "Cockpit Comunicação para aprovar, exportar, enviar manualmente e medir resultado.",
        "Checklist Produto para medir clareza, valor percebido e prontidão beta.",
    ]

    return {
        "publico": publico,
        "dor": info["dor"],
        "desejo": info["desejo"],
        "linguagem": info["linguagem"],
        "headline": headline,
        "subheadline": subheadline,
        "promessa_curta": promessa_curta,
        "diferenciais": diferenciais,
        "provas": provas,
    }


def gerar_pitches(publico: str) -> Dict[str, str]:
    proposta = montar_proposta_valor(publico)

    pitch_10s = (
        "O Valoris é um sistema que transforma análise de investimentos em decisões acompanháveis, "
        "com preço teto, pipeline, alertas e cockpit."
    )

    pitch_30s = (
        "O Valoris ajuda investidores a saírem da análise solta para um processo completo de decisão. "
        "Você analisa um ativo, calcula preço teto, define uma ação, acompanha alertas, registra revisões "
        "e enxerga tudo em um cockpit. A ideia não é prometer lucro, mas criar método, disciplina e rastreabilidade."
    )

    pitch_60s = (
        f"{proposta['headline']}. "
        f"Ele foi criado para quem sente que {proposta['dor'].lower()} "
        "Em vez de deixar a análise morrer em uma planilha, o Valoris cria uma jornada: análise, tese, preço teto, "
        "pipeline, alertas, comunicação, resultado e revisão. "
        "Tudo com controle manual e visão executiva. "
        f"A promessa é simples: {proposta['promessa_curta'].lower()}"
    )

    pitch_executivo = (
        "O Valoris é uma plataforma de decisão para investidores que querem método e acompanhamento. "
        "Ele combina valuation conservador, organização operacional e cockpit executivo para transformar ideias de investimento "
        "em decisões rastreáveis. O diferencial está em conectar análise, acompanhamento e aprendizado, sem automatizar decisões financeiras."
    )

    return {
        "pitch_10s": pitch_10s,
        "pitch_30s": pitch_30s,
        "pitch_60s": pitch_60s,
        "pitch_executivo": pitch_executivo,
    }


def gerar_pagina_valor_markdown(publico: str) -> str:
    proposta = montar_proposta_valor(publico)
    pitches = gerar_pitches(publico)

    diferenciais = "\n".join([f"- {item}" for item in proposta["diferenciais"]])
    provas = "\n".join([f"- {item}" for item in proposta["provas"]])
    objecoes = "\n".join([f"### {item['objecao']}\n{item['resposta']}\n" for item in OBJECOES])

    return f"""# {proposta['headline']}

## {proposta['subheadline']}

**Para quem é:** {proposta['publico']}  
**Dor principal:** {proposta['dor']}  
**Desejo:** {proposta['desejo']}  
**Promessa:** {proposta['promessa_curta']}

## Pitch curto

{pitches['pitch_10s']}

## Pitch de 30 segundos

{pitches['pitch_30s']}

## Pitch executivo

{pitches['pitch_executivo']}

## Por que o Valoris é diferente?

{diferenciais}

## Provas operacionais já construídas

{provas}

## Objeções e respostas

{objecoes}

## Chamada para beta

Teste o Valoris como um beta guiado. A proposta é simples: escolher um ativo, analisar com método, transformar a análise em decisão acompanhável e revisar o processo com clareza.

## Nota importante

O Valoris não promete rentabilidade, não substitui julgamento humano e não recomenda compra ou venda de forma automática. Ele organiza processo, disciplina e acompanhamento.
"""


def calcular_metricas_valor_comercial(publico: str) -> Dict[str, Any]:
    metricas_externas = carregar_metricas_externas()
    revisoes = carregar_revisoes()

    score_checklist = _int(metricas_externas.get("checklist", {}).get("score_produto"), 0)
    score_demo = _int(metricas_externas.get("demo", {}).get("score_demo"), 0)
    score_modos = _int(metricas_externas.get("modos", {}).get("score_modos"), 0)
    score_jornada = _int(metricas_externas.get("jornada", {}).get("score_jornada"), 0)
    score_cockpit = _int(metricas_externas.get("cockpit_principal", {}).get("score_cockpit"), 0)
    score_comunicacao = _int(metricas_externas.get("cockpit_comunicacao", {}).get("score_cockpit"), 0)

    base_scores = [score for score in [score_checklist, score_demo, score_modos, score_jornada, score_cockpit, score_comunicacao] if score > 0]
    score_base = int(sum(base_scores) / len(base_scores)) if base_scores else 55

    revisoes_publico = [r for r in revisoes if _txt(r.get("publico_alvo")) == publico]
    scores_pitch = [_int(r.get("score_pitch")) for r in revisoes if _txt(r.get("score_pitch"))]
    media_pitch = round(sum(scores_pitch) / len(scores_pitch), 1) if scores_pitch else 0

    score = score_base

    if revisoes:
        score += 8

    if revisoes_publico:
        score += 5

    if media_pitch >= 80:
        score += 7
    elif media_pitch >= 65:
        score += 4

    score = max(0, min(100, int(score)))

    if score >= 85:
        maturidade = "Pitch pronto para beta"
        risco = "Baixo"
        decisao = "Valor comercial claro para apresentação externa"
        proximo = "Apresentar para 3 usuários beta e medir entendimento."
    elif score >= 72:
        maturidade = "Pitch funcional"
        risco = "Baixo/Médio"
        decisao = "Proposta comercial utilizável, mas ainda precisa de teste real"
        proximo = "Usar a Demo Premium e observar objeções."
    elif score >= 58:
        maturidade = "Pitch em lapidação"
        risco = "Médio"
        decisao = "Valor existe, mas a mensagem precisa ficar mais simples"
        proximo = "Revisar headline, promessa e público-alvo."
    else:
        maturidade = "Pitch fraco"
        risco = "Médio/Alto"
        decisao = "Ainda não apresentar comercialmente"
        proximo = "Voltar para Demo Premium e Checklist Produto."

    return {
        "versao": VERSAO_VALOR_COMERCIAL_VALORIS,
        "gerado_em": _agora_iso(),
        "publico": publico,
        "score_valor_comercial": score,
        "maturidade": maturidade,
        "score_checklist": score_checklist,
        "score_demo": score_demo,
        "score_modos": score_modos,
        "score_jornada": score_jornada,
        "score_cockpit": score_cockpit,
        "score_comunicacao": score_comunicacao,
        "revisoes": len(revisoes),
        "revisoes_publico": len(revisoes_publico),
        "media_pitch": media_pitch,
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo,
    }


def gerar_relatorio_valor_comercial(publico: str) -> str:
    metricas = calcular_metricas_valor_comercial(publico)
    pagina = gerar_pagina_valor_markdown(publico)
    revisoes = carregar_revisoes()

    linhas_revisoes = "\n".join(
        [
            f"- **{item['publico_alvo']} — score {item['score_pitch']}/100**: clareza {item['clareza']}/10, comercial {item['forca_comercial']}/10, confiança {item['confianca']}/10. Decisão: {item['decisao']}"
            for item in revisoes[-30:]
        ]
    ) or "- Nenhuma revisão comercial registrada."

    return f"""# Valor Comercial e Pitch — Valoris

Versão: {VERSAO_VALOR_COMERCIAL_VALORIS}  
Gerado em: {_agora_iso()}  
Público-alvo: {publico}

## Diagnóstico

Score valor comercial: {metricas['score_valor_comercial']}/100  
Maturidade: {metricas['maturidade']}  
Score checklist: {metricas['score_checklist']}/100  
Score demo: {metricas['score_demo']}/100  
Score modos: {metricas['score_modos']}/100  
Score jornada: {metricas['score_jornada']}/100  
Revisões: {metricas['revisoes']}  
Média pitch: {metricas['media_pitch']}/100  

Risco: {metricas['risco']}  
Decisão: {metricas['decisao']}  
Próximo passo: {metricas['proximo_passo']}

## Página de valor

{pagina}

## Revisões registradas

{linhas_revisoes}

## Estratégia

Esta versão transforma arquitetura em mensagem. O Valoris precisa ser explicado de forma clara antes de ser vendido: dor, promessa, prova, diferenciação e objeções.
"""


def salvar_relatorio_valor_comercial(publico: str) -> Path:
    CAMINHO_RELATORIO.write_text(gerar_relatorio_valor_comercial(publico), encoding="utf-8")
    return CAMINHO_RELATORIO


def gerar_manifesto_valor_comercial(publico: str) -> Dict[str, Any]:
    return {
        "produto": "Valoris",
        "versao": VERSAO_VALOR_COMERCIAL_VALORIS,
        "modulo": "valor_comercial_valoris",
        "data_hora": _agora_iso(),
        "publico": publico,
        "metricas": calcular_metricas_valor_comercial(publico),
        "proposta_valor": montar_proposta_valor(publico),
        "pitches": gerar_pitches(publico),
        "objeções": OBJECOES,
        "revisoes": carregar_revisoes(),
        "principio": "produto técnico só vira produto comercial quando sua promessa é entendida rápido",
        "proxima_etapa": "beta para primeiros usuários",
    }


def salvar_manifesto_valor_comercial(publico: str) -> Path:
    CAMINHO_MANIFESTO.write_text(
        json.dumps(gerar_manifesto_valor_comercial(publico), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return CAMINHO_MANIFESTO


def renderizar_valor_comercial_valoris() -> None:
    st.subheader("Valor Comercial")
    st.caption("Transforma o Valoris em mensagem: público, dor, promessa, pitch, provas e objeções.")

    publico = st.selectbox("Público-alvo", list(PUBLICOS_ALVO.keys()), index=1)
    proposta = montar_proposta_valor(publico)
    pitches = gerar_pitches(publico)
    metricas = calcular_metricas_valor_comercial(publico)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Score comercial", f"{metricas['score_valor_comercial']}/100")
    col2.metric("Maturidade", metricas["maturidade"])
    col3.metric("Checklist", f"{metricas['score_checklist']}/100")
    col4.metric("Demo", f"{metricas['score_demo']}/100")
    col5.metric("Revisões", metricas["revisoes"])

    if metricas["risco"] in {"Médio", "Médio/Alto"}:
        st.warning(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    elif metricas["risco"] == "Baixo":
        st.success(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    else:
        st.info(f"{metricas['decisao']} — {metricas['proximo_passo']}")

    st.divider()

    st.markdown("### Proposta de valor")

    st.markdown(f"## {proposta['headline']}")
    st.markdown(proposta["subheadline"])
    st.markdown(f"**Dor:** {proposta['dor']}")
    st.markdown(f"**Desejo:** {proposta['desejo']}")
    st.markdown(f"**Promessa:** {proposta['promessa_curta']}")
    st.markdown(f"**Linguagem:** {proposta['linguagem']}")

    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs(["Pitches", "Página de valor", "Provas", "Objeções"])

    with tab1:
        st.markdown("### Pitch de 10 segundos")
        st.info(pitches["pitch_10s"])

        st.markdown("### Pitch de 30 segundos")
        st.write(pitches["pitch_30s"])

        st.markdown("### Pitch de 60 segundos")
        st.write(pitches["pitch_60s"])

        st.markdown("### Pitch executivo")
        st.write(pitches["pitch_executivo"])

    with tab2:
        st.markdown(gerar_pagina_valor_markdown(publico))

    with tab3:
        st.markdown("### Diferenciais")
        for item in proposta["diferenciais"]:
            st.markdown(f"- {item}")

        st.markdown("### Provas operacionais")
        for item in proposta["provas"]:
            st.markdown(f"- {item}")

    with tab4:
        for item in OBJECOES:
            st.markdown(f"### {item['objecao']}")
            st.write(item["resposta"])

    st.divider()

    st.markdown("### Registrar revisão comercial")

    clareza = st.slider("Clareza da mensagem", min_value=0, max_value=10, value=8)
    forca = st.slider("Força comercial", min_value=0, max_value=10, value=8)
    confianca = st.slider("Confiança transmitida", min_value=0, max_value=10, value=8)
    diferenciacao = st.slider("Diferenciação percebida", min_value=0, max_value=10, value=8)

    score_manual = int(round((clareza + forca + confianca + diferenciacao) * 2.5, 0))

    responsavel = st.text_input("Responsável", value="Fundador")
    decisao = st.text_input("Decisão", value=metricas["decisao"])
    proximo = st.text_input("Próximo passo", value=metricas["proximo_passo"])
    observacao = st.text_area(
        "Observação",
        value=f"Revisão registrada em Valor Comercial v{VERSAO_VALOR_COMERCIAL_VALORIS}.",
        height=90,
    )

    st.info(f"Score manual do pitch: {score_manual}/100")

    if st.button("Salvar revisão comercial"):
        salvar_revisao_valor_comercial(
            publico_alvo=publico,
            promessa=proposta["promessa_curta"],
            score_pitch=score_manual,
            clareza=clareza,
            forca_comercial=forca,
            confianca=confianca,
            diferenciacao=diferenciacao,
            responsavel=responsavel,
            decisao=decisao,
            proximo_passo=proximo,
            observacao=observacao,
        )
        st.success("Revisão comercial registrada.")
        st.rerun()

    revisoes = carregar_revisoes()
    if revisoes:
        st.markdown("### Revisões registradas")
        st.dataframe(revisoes, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Relatórios")

    col_r1, col_r2 = st.columns(2)

    if col_r1.button("Salvar relatório comercial"):
        caminho = salvar_relatorio_valor_comercial(publico)
        st.success(f"Relatório salvo em {caminho}")

    if col_r2.button("Salvar manifesto comercial"):
        caminho = salvar_manifesto_valor_comercial(publico)
        st.success(f"Manifesto salvo em {caminho}")

    st.download_button(
        "Baixar relatório comercial (.md)",
        data=gerar_relatorio_valor_comercial(publico),
        file_name="RELATORIO_VALOR_COMERCIAL_VALORIS.md",
        mime="text/markdown",
    )


def executar_autoteste_valor_comercial_valoris() -> Dict[str, Any]:
    publico = "Investidor intermediário"
    return {
        "ok": True,
        "versao": VERSAO_VALOR_COMERCIAL_VALORIS,
        "metricas": calcular_metricas_valor_comercial(publico),
    }
