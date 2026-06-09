# analise_premium_valoris.py

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

import streamlit as st

from launch_readiness_valoris import calcular_saude_launch_readiness


VERSAO_ANALISE_PREMIUM_VALORIS = "3.8.76"

CAMINHO_DECISOES_ANALISE_PREMIUM = Path("decisoes_analise_premium_valoris.csv")
CAMINHO_MANIFESTO_ANALISE_PREMIUM = Path("manifesto_analise_premium_valoris.json")
CAMINHO_RELATORIO_ANALISE_PREMIUM_MD = Path("RELATORIO_ANALISE_PREMIUM_VALORIS.md")
CAMINHO_DEMO_ANALISE_PREMIUM_JSON = Path("demo_analise_premium_valoris.json")

CAMPOS_DECISAO_ANALISE_PREMIUM = [
    "id",
    "data_registro",
    "empresa",
    "ticker",
    "preco_atual",
    "preco_teto",
    "margem_seguranca",
    "score_final",
    "score_qualidade",
    "score_valuation",
    "score_risco",
    "decisao",
    "classificacao",
    "risco",
    "proximo_passo",
    "observacoes",
]

DADOS_DEMO_ANALISE_PREMIUM = {
    "empresa": "Empresa Exemplo Valoris",
    "ticker": "VALR3",
    "setor": "Tecnologia / Serviços financeiros",
    "preco_atual": 82.00,
    "preco_teto": 105.00,
    "lucro_por_acao": 6.20,
    "fluxo_caixa_livre_por_acao": 5.60,
    "crescimento_receita_5a": 9.0,
    "crescimento_lucro_5a": 11.0,
    "roic": 18.0,
    "roe": 22.0,
    "margem_liquida": 17.0,
    "divida_liquida_ebitda": 1.2,
    "payout": 35.0,
    "previsibilidade": 8,
    "vantagem_competitiva": 8,
    "qualidade_gestao": 8,
    "risco_regulatorio": 4,
    "risco_ciclico": 5,
    "risco_disrupcao": 4,
    "premissa_central": "Companhia com boa geração de caixa, rentabilidade elevada e valuation ainda com margem de segurança.",
}

CRITERIOS_ANALISE_PREMIUM = [
    {
        "criterio": "Margem de segurança",
        "objetivo": "Evitar comprar bons ativos por preço ruim.",
        "peso": 24,
    },
    {
        "criterio": "Qualidade do negócio",
        "objetivo": "Avaliar retorno sobre capital, margens, previsibilidade e vantagem competitiva.",
        "peso": 28,
    },
    {
        "criterio": "Risco financeiro",
        "objetivo": "Evitar empresas frágeis em dívida, ciclo, disrupção ou regulação.",
        "peso": 20,
    },
    {
        "criterio": "Clareza da tese",
        "objetivo": "Transformar número em decisão compreensível.",
        "peso": 16,
    },
    {
        "criterio": "Próximo passo",
        "objetivo": "Dar ação prática: comprar, aguardar, estudar ou evitar.",
        "peso": 12,
    },
]

BANDAS_DECISAO = [
    {
        "faixa": "Score final >= 82 e margem >= 25%",
        "decisao": "Compra prudente",
        "descricao": "Ativo aparenta unir qualidade, preço e margem de segurança.",
    },
    {
        "faixa": "Score final >= 70 e margem entre 10% e 25%",
        "decisao": "Aguardar preço melhor",
        "descricao": "Boa tese, mas sem folga suficiente para erro.",
    },
    {
        "faixa": "Score final entre 55 e 70",
        "decisao": "Neutro / estudar mais",
        "descricao": "Há pontos positivos, mas a assimetria ainda não é forte.",
    },
    {
        "faixa": "Score final < 55 ou risco elevado",
        "decisao": "Evitar por enquanto",
        "descricao": "Relação risco-retorno fraca ou premissas frágeis.",
    },
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


def _to_int(valor: Any, padrao: int = 0) -> int:
    try:
        return int(valor)
    except Exception:
        return padrao


def _clamp(valor: float, minimo: float = 0.0, maximo: float = 100.0) -> float:
    return max(minimo, min(maximo, valor))


def _score_maior_melhor(valor: float, ruim: float, bom: float) -> float:
    if bom == ruim:
        return 0
    return _clamp(((valor - ruim) / (bom - ruim)) * 100)


def _score_menor_melhor(valor: float, bom: float, ruim: float) -> float:
    if ruim == bom:
        return 0
    return _clamp(((ruim - valor) / (ruim - bom)) * 100)


def _garantir_csv(caminho: Path, campos: List[str]) -> None:
    if caminho.exists():
        return

    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()


def carregar_decisoes_analise_premium() -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_DECISOES_ANALISE_PREMIUM, CAMPOS_DECISAO_ANALISE_PREMIUM)

    with CAMINHO_DECISOES_ANALISE_PREMIUM.open("r", newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def gerar_csv_decisoes_analise_premium() -> str:
    _garantir_csv(CAMINHO_DECISOES_ANALISE_PREMIUM, CAMPOS_DECISAO_ANALISE_PREMIUM)
    return CAMINHO_DECISOES_ANALISE_PREMIUM.read_text(encoding="utf-8")


def salvar_decisao_analise_premium(resultado: Dict[str, Any], observacoes: str = "") -> Dict[str, str]:
    _garantir_csv(CAMINHO_DECISOES_ANALISE_PREMIUM, CAMPOS_DECISAO_ANALISE_PREMIUM)

    dados = resultado["dados"]
    registro = {
        "id": str(uuid4())[:8],
        "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "empresa": _limpar_texto(dados.get("empresa", "")),
        "ticker": _limpar_texto(dados.get("ticker", "")),
        "preco_atual": f"{resultado['preco_atual']:.2f}",
        "preco_teto": f"{resultado['preco_teto']:.2f}",
        "margem_seguranca": f"{resultado['margem_seguranca']:.2f}",
        "score_final": str(resultado["score_final"]),
        "score_qualidade": str(resultado["score_qualidade"]),
        "score_valuation": str(resultado["score_valuation"]),
        "score_risco": str(resultado["score_risco"]),
        "decisao": resultado["decisao"],
        "classificacao": resultado["classificacao"],
        "risco": resultado["risco"],
        "proximo_passo": resultado["proximo_passo"],
        "observacoes": _limpar_texto(observacoes),
    }

    with CAMINHO_DECISOES_ANALISE_PREMIUM.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISAO_ANALISE_PREMIUM)
        escritor.writerow(registro)

    return registro


def calcular_analise_premium_valoris(dados: Dict[str, Any]) -> Dict[str, Any]:
    preco_atual = max(0.0, _to_float(dados.get("preco_atual")))
    preco_teto = max(0.0, _to_float(dados.get("preco_teto")))

    if preco_teto > 0:
        margem_seguranca = ((preco_teto - preco_atual) / preco_teto) * 100
    else:
        margem_seguranca = 0.0

    roic = _to_float(dados.get("roic"))
    roe = _to_float(dados.get("roe"))
    margem_liquida = _to_float(dados.get("margem_liquida"))
    crescimento_receita = _to_float(dados.get("crescimento_receita_5a"))
    crescimento_lucro = _to_float(dados.get("crescimento_lucro_5a"))
    divida_liquida_ebitda = _to_float(dados.get("divida_liquida_ebitda"))
    payout = _to_float(dados.get("payout"))

    previsibilidade = _to_int(dados.get("previsibilidade"))
    vantagem_competitiva = _to_int(dados.get("vantagem_competitiva"))
    qualidade_gestao = _to_int(dados.get("qualidade_gestao"))

    risco_regulatorio = _to_int(dados.get("risco_regulatorio"))
    risco_ciclico = _to_int(dados.get("risco_ciclico"))
    risco_disrupcao = _to_int(dados.get("risco_disrupcao"))

    score_valuation = int(round(_clamp((margem_seguranca + 5) * 2.35)))
    score_roic = _score_maior_melhor(roic, 5, 22)
    score_roe = _score_maior_melhor(roe, 8, 25)
    score_margem = _score_maior_melhor(margem_liquida, 5, 25)
    score_crescimento = (_score_maior_melhor(crescimento_receita, 0, 15) * 0.45) + (_score_maior_melhor(crescimento_lucro, 0, 18) * 0.55)
    score_moat = _clamp(vantagem_competitiva * 10)
    score_previsibilidade = _clamp(previsibilidade * 10)
    score_gestao = _clamp(qualidade_gestao * 10)

    score_qualidade = int(round(
        score_roic * 0.23
        + score_roe * 0.12
        + score_margem * 0.16
        + score_crescimento * 0.15
        + score_moat * 0.14
        + score_previsibilidade * 0.10
        + score_gestao * 0.10
    ))

    score_divida = _score_menor_melhor(divida_liquida_ebitda, 0.5, 4.0)
    score_payout = _score_menor_melhor(abs(payout - 45), 0, 65)
    score_risco_operacional = 100 - _clamp(((risco_regulatorio + risco_ciclico + risco_disrupcao) / 30) * 100)

    score_risco = int(round(
        score_divida * 0.42
        + score_payout * 0.18
        + score_risco_operacional * 0.40
    ))

    score_final = int(round(
        score_valuation * 0.34
        + score_qualidade * 0.42
        + score_risco * 0.24
    ))

    if score_final >= 82 and margem_seguranca >= 25 and score_risco >= 55:
        decisao = "COMPRA PRUDENTE"
        classificacao = "Assimetria positiva"
        risco = "Médio controlado"
        proximo_passo = "Validar premissas no relatório da empresa e considerar entrada gradual."
    elif score_final >= 72 and margem_seguranca >= 12:
        decisao = "AGUARDAR PREÇO MELHOR"
        classificacao = "Boa empresa, preço ainda justo/apertado"
        risco = "Médio"
        proximo_passo = "Colocar em watchlist e definir alerta próximo ao preço teto conservador."
    elif score_final >= 58:
        decisao = "NEUTRO / ESTUDAR MAIS"
        classificacao = "Tese incompleta ou assimetria moderada"
        risco = "Médio/alto"
        proximo_passo = "Revisar premissas, comparar com pares e exigir margem maior."
    else:
        decisao = "EVITAR POR ENQUANTO"
        classificacao = "Relação risco-retorno fraca"
        risco = "Alto"
        proximo_passo = "Não comprar até haver preço melhor, tese mais clara ou redução de risco."

    gatilhos_positivos = []
    gatilhos_negativos = []

    if margem_seguranca >= 25:
        gatilhos_positivos.append("Margem de segurança robusta acima de 25%.")
    elif margem_seguranca < 10:
        gatilhos_negativos.append("Margem de segurança baixa ou inexistente.")

    if roic >= 15:
        gatilhos_positivos.append("ROIC indica boa eficiência sobre capital.")
    elif roic < 8:
        gatilhos_negativos.append("ROIC baixo reduz qualidade da tese.")

    if divida_liquida_ebitda <= 1.5:
        gatilhos_positivos.append("Alavancagem aparentemente controlada.")
    elif divida_liquida_ebitda >= 3:
        gatilhos_negativos.append("Dívida elevada aumenta fragilidade da tese.")

    if vantagem_competitiva >= 8:
        gatilhos_positivos.append("Vantagem competitiva percebida como forte.")
    elif vantagem_competitiva <= 4:
        gatilhos_negativos.append("Vantagem competitiva fraca ou pouco clara.")

    if not gatilhos_positivos:
        gatilhos_positivos.append("Há pontos positivos, mas nenhum gatilho de alta convicção foi dominante.")

    if not gatilhos_negativos:
        gatilhos_negativos.append("Nenhum alerta extremo apareceu nos dados informados, mas as premissas ainda devem ser validadas.")

    tese = gerar_tese_analise_premium(
        dados=dados,
        margem_seguranca=margem_seguranca,
        score_final=score_final,
        score_qualidade=score_qualidade,
        score_valuation=score_valuation,
        score_risco=score_risco,
        decisao=decisao,
        classificacao=classificacao,
        risco=risco,
    )

    return {
        "versao": VERSAO_ANALISE_PREMIUM_VALORIS,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "dados": dados,
        "preco_atual": preco_atual,
        "preco_teto": preco_teto,
        "margem_seguranca": round(margem_seguranca, 2),
        "score_valuation": score_valuation,
        "score_qualidade": score_qualidade,
        "score_risco": score_risco,
        "score_final": score_final,
        "decisao": decisao,
        "classificacao": classificacao,
        "risco": risco,
        "proximo_passo": proximo_passo,
        "gatilhos_positivos": gatilhos_positivos,
        "gatilhos_negativos": gatilhos_negativos,
        "tese": tese,
        "criterios": CRITERIOS_ANALISE_PREMIUM,
        "bandas_decisao": BANDAS_DECISAO,
    }


def gerar_tese_analise_premium(
    dados: Dict[str, Any],
    margem_seguranca: float,
    score_final: int,
    score_qualidade: int,
    score_valuation: int,
    score_risco: int,
    decisao: str,
    classificacao: str,
    risco: str,
) -> str:
    empresa = _limpar_texto(dados.get("empresa", "Empresa analisada"))
    ticker = _limpar_texto(dados.get("ticker", ""))
    setor = _limpar_texto(dados.get("setor", "setor não informado"))
    premissa = _limpar_texto(dados.get("premissa_central", ""))

    identificador = f"{empresa} ({ticker})" if ticker else empresa

    if margem_seguranca >= 25:
        leitura_preco = "o preço atual oferece folga relevante contra o preço teto informado"
    elif margem_seguranca >= 10:
        leitura_preco = "há alguma folga, mas ela ainda não parece ampla o suficiente para erro de premissa"
    else:
        leitura_preco = "a margem de segurança parece limitada, exigindo mais paciência ou premissas muito confiáveis"

    if score_qualidade >= 78:
        leitura_qualidade = "A qualidade operacional informada é forte, com bons sinais de rentabilidade, previsibilidade e vantagem competitiva."
    elif score_qualidade >= 60:
        leitura_qualidade = "A qualidade do negócio parece aceitável, mas ainda existem pontos que precisam de confirmação."
    else:
        leitura_qualidade = "A qualidade do negócio ainda não sustenta uma tese de alta convicção."

    return (
        f"A análise premium da Valoris indica que {identificador}, no setor de {setor}, recebeu score final de "
        f"{score_final}/100. A decisão sugerida é **{decisao}**, classificada como **{classificacao}**, com risco "
        f"**{risco}**. Pelo preço informado, {leitura_preco}. {leitura_qualidade} "
        f"O score de valuation foi {score_valuation}/100, o score de qualidade foi {score_qualidade}/100 e o score de risco foi {score_risco}/100. "
        f"{premissa}"
    ).strip()


def gerar_markdown_analise_premium(resultado: Dict[str, Any]) -> str:
    dados = resultado["dados"]
    positivos = "\n".join([f"- {item}" for item in resultado["gatilhos_positivos"]])
    negativos = "\n".join([f"- {item}" for item in resultado["gatilhos_negativos"]])

    criterios = "\n".join(
        [
            f"- **{item['criterio']}** ({item['peso']} pts): {item['objetivo']}"
            for item in CRITERIOS_ANALISE_PREMIUM
        ]
    )

    return f"""# Relatório de Análise Premium — Valoris

Versão: {VERSAO_ANALISE_PREMIUM_VALORIS}  
Gerado em: {resultado["gerado_em"]}

## Empresa

Empresa: {dados.get("empresa", "")}  
Ticker: {dados.get("ticker", "")}  
Setor: {dados.get("setor", "")}

## Decisão

Decisão: **{resultado["decisao"]}**  
Classificação: **{resultado["classificacao"]}**  
Risco: **{resultado["risco"]}**  
Próximo passo: {resultado["proximo_passo"]}

## Valuation

Preço atual: {resultado["preco_atual"]:.2f}  
Preço teto: {resultado["preco_teto"]:.2f}  
Margem de segurança: {resultado["margem_seguranca"]:.2f}%

## Scores

Score final: {resultado["score_final"]}/100  
Score valuation: {resultado["score_valuation"]}/100  
Score qualidade: {resultado["score_qualidade"]}/100  
Score risco: {resultado["score_risco"]}/100

## Tese

{resultado["tese"]}

## Gatilhos positivos

{positivos}

## Alertas e riscos

{negativos}

## Critérios usados

{criterios}

## Aviso

Este relatório é uma ferramenta educacional e analítica. Não é recomendação personalizada de investimento.
"""


def salvar_relatorio_analise_premium_markdown(resultado: Dict[str, Any] | None = None) -> Dict[str, Any]:
    if resultado is None:
        resultado = calcular_analise_premium_valoris(DADOS_DEMO_ANALISE_PREMIUM)

    CAMINHO_RELATORIO_ANALISE_PREMIUM_MD.write_text(
        gerar_markdown_analise_premium(resultado),
        encoding="utf-8",
    )

    return {
        "ok": True,
        "arquivo": str(CAMINHO_RELATORIO_ANALISE_PREMIUM_MD),
        "score_final": resultado["score_final"],
        "decisao": resultado["decisao"],
    }


def gerar_demo_analise_premium() -> Dict[str, Any]:
    resultado = calcular_analise_premium_valoris(DADOS_DEMO_ANALISE_PREMIUM)
    CAMINHO_DEMO_ANALISE_PREMIUM_JSON.write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return resultado


def gerar_manifesto_analise_premium() -> Dict[str, Any]:
    try:
        launch = calcular_saude_launch_readiness()
    except Exception as erro:
        launch = {"score_launch": 0, "erro": str(erro)}

    demo = calcular_analise_premium_valoris(DADOS_DEMO_ANALISE_PREMIUM)

    manifesto = {
        "versao": VERSAO_ANALISE_PREMIUM_VALORIS,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "launch_readiness": launch,
        "demo": demo,
        "criterios": CRITERIOS_ANALISE_PREMIUM,
        "bandas_decisao": BANDAS_DECISAO,
        "estrategia": {
            "objetivo": "Criar o momento uau do produto: decisão, tese, riscos, preço teto e relatório exportável.",
            "regra": "Produto precisa ser compreendido em menos de 2 minutos.",
            "proxima_versao": "Demo guiada e fluxo público de validação com usuários reais.",
        },
    }

    CAMINHO_MANIFESTO_ANALISE_PREMIUM.write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return manifesto


def calcular_saude_analise_premium() -> Dict[str, Any]:
    try:
        launch = calcular_saude_launch_readiness()
    except Exception as erro:
        launch = {"score_launch": 0, "go_no_go": "indefinido", "erro": str(erro)}

    demo = calcular_analise_premium_valoris(DADOS_DEMO_ANALISE_PREMIUM)

    criterios_ok = len(CRITERIOS_ANALISE_PREMIUM) >= 5
    bandas_ok = len(BANDAS_DECISAO) >= 4
    demo_ok = demo["score_final"] > 0 and bool(demo["tese"]) and bool(demo["decisao"])
    relatorio_ok = bool(gerar_markdown_analise_premium(demo))

    score_launch = int(launch.get("score_launch", 0) or 0)

    score_produto_premium = 10
    score_produto_premium += 22 if criterios_ok else 0
    score_produto_premium += 18 if bandas_ok else 0
    score_produto_premium += 25 if demo_ok else 0
    score_produto_premium += 15 if relatorio_ok else 0
    score_produto_premium += min(score_launch * 0.10, 10)
    score_produto_premium = int(round(max(0, min(100, score_produto_premium))))

    if score_produto_premium >= 86:
        risco = "Médio controlado"
        decisao = "Experiência premium pronta para demo guiada"
        proximo_passo = "Criar uma demo de 2 minutos com caso exemplo e chamada para lista beta."
    elif score_produto_premium >= 70:
        risco = "Médio"
        decisao = "Experiência premium promissora, mas ainda ajustável"
        proximo_passo = "Melhorar clareza visual e validar relatório com um usuário real."
    else:
        risco = "Alto"
        decisao = "Experiência premium ainda fraca para lançamento"
        proximo_passo = "Reforçar tese, riscos, decisão e relatório."

    return {
        "versao": VERSAO_ANALISE_PREMIUM_VALORIS,
        "score_produto_premium": score_produto_premium,
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo_passo,
        "criterios_ok": criterios_ok,
        "bandas_ok": bandas_ok,
        "demo_ok": demo_ok,
        "relatorio_ok": relatorio_ok,
        "launch": launch,
        "demo": demo,
        "criterios": CRITERIOS_ANALISE_PREMIUM,
        "bandas_decisao": BANDAS_DECISAO,
    }


def _injetar_css_analise_premium() -> None:
    st.markdown(
        """
        <style>
            .analise-premium-hero {
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
            .analise-premium-eyebrow {
                color: #d6b56d;
                font-size: 0.74rem;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                font-weight: 880;
                margin-bottom: 0.35rem;
            }
            .analise-premium-title {
                color: #f4f7fb;
                font-size: clamp(1.8rem, 5.5vw, 3.25rem);
                font-weight: 950;
                line-height: 1.02;
                letter-spacing: -0.058em;
                margin-bottom: 0.55rem;
            }
            .analise-premium-subtitle {
                color: rgba(244, 247, 251, 0.75);
                font-size: clamp(0.94rem, 2.2vw, 1.06rem);
                line-height: 1.56;
                max-width: 1050px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _renderizar_resultado_premium(resultado: Dict[str, Any]) -> None:
    st.markdown("### Resultado premium")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Score final", f"{resultado['score_final']}/100")

    with col_2:
        st.metric("Margem segurança", f"{resultado['margem_seguranca']:.2f}%")

    with col_3:
        st.metric("Decisão", resultado["decisao"])

    with col_4:
        st.metric("Risco", resultado["risco"])

    st.progress(resultado["score_final"] / 100)

    if resultado["decisao"] == "COMPRA PRUDENTE":
        st.success(f"**{resultado['classificacao']}** — {resultado['proximo_passo']}")
    elif resultado["decisao"] == "AGUARDAR PREÇO MELHOR":
        st.warning(f"**{resultado['classificacao']}** — {resultado['proximo_passo']}")
    else:
        st.info(f"**{resultado['classificacao']}** — {resultado['proximo_passo']}")

    st.markdown("### Tese")
    st.write(resultado["tese"])

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        st.metric("Valuation", f"{resultado['score_valuation']}/100")

    with col_b:
        st.metric("Qualidade", f"{resultado['score_qualidade']}/100")

    with col_c:
        st.metric("Risco ajustado", f"{resultado['score_risco']}/100")

    st.markdown("### Gatilhos positivos")
    for item in resultado["gatilhos_positivos"]:
        st.success(item)

    st.markdown("### Alertas")
    for item in resultado["gatilhos_negativos"]:
        st.warning(item)


def renderizar_analise_premium_valoris() -> None:
    _injetar_css_analise_premium()

    st.markdown(
        f"""
        <div class="analise-premium-hero">
            <div class="analise-premium-eyebrow">Valoris • Análise Premium • v{VERSAO_ANALISE_PREMIUM_VALORIS}</div>
            <div class="analise-premium-title">O momento uau do produto.</div>
            <div class="analise-premium-subtitle">
                Uma análise clara e vendável: preço teto, margem de segurança, qualidade, risco, tese,
                decisão e relatório exportável.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    saude = calcular_saude_analise_premium()

    st.markdown("### Diagnóstico da experiência premium")
    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Score Premium", f"{saude['score_produto_premium']}/100")

    with col_2:
        st.metric("Risco", saude["risco"])

    with col_3:
        st.metric("Demo", "OK" if saude["demo_ok"] else "Pendente")

    with col_4:
        st.metric("Relatório", "OK" if saude["relatorio_ok"] else "Pendente")

    st.progress(saude["score_produto_premium"] / 100)
    st.success(f"**{saude['decisao']}** — {saude['proximo_passo']}") if saude["score_produto_premium"] >= 86 else st.warning(f"**{saude['decisao']}** — {saude['proximo_passo']}")

    st.divider()

    st.markdown("### Preencha uma análise")

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        empresa = st.text_input("Empresa", value=DADOS_DEMO_ANALISE_PREMIUM["empresa"])
        ticker = st.text_input("Ticker", value=DADOS_DEMO_ANALISE_PREMIUM["ticker"])
        setor = st.text_input("Setor", value=DADOS_DEMO_ANALISE_PREMIUM["setor"])
        preco_atual = st.number_input("Preço atual", min_value=0.0, value=float(DADOS_DEMO_ANALISE_PREMIUM["preco_atual"]), step=1.0)
        preco_teto = st.number_input("Preço teto", min_value=0.0, value=float(DADOS_DEMO_ANALISE_PREMIUM["preco_teto"]), step=1.0)

    with col_b:
        lucro_por_acao = st.number_input("Lucro por ação", value=float(DADOS_DEMO_ANALISE_PREMIUM["lucro_por_acao"]), step=0.1)
        fluxo_caixa_livre_por_acao = st.number_input("FCF por ação", value=float(DADOS_DEMO_ANALISE_PREMIUM["fluxo_caixa_livre_por_acao"]), step=0.1)
        crescimento_receita_5a = st.number_input("Crescimento receita 5a (%)", value=float(DADOS_DEMO_ANALISE_PREMIUM["crescimento_receita_5a"]), step=0.5)
        crescimento_lucro_5a = st.number_input("Crescimento lucro 5a (%)", value=float(DADOS_DEMO_ANALISE_PREMIUM["crescimento_lucro_5a"]), step=0.5)
        roic = st.number_input("ROIC (%)", value=float(DADOS_DEMO_ANALISE_PREMIUM["roic"]), step=0.5)

    with col_c:
        roe = st.number_input("ROE (%)", value=float(DADOS_DEMO_ANALISE_PREMIUM["roe"]), step=0.5)
        margem_liquida = st.number_input("Margem líquida (%)", value=float(DADOS_DEMO_ANALISE_PREMIUM["margem_liquida"]), step=0.5)
        divida_liquida_ebitda = st.number_input("Dívida líquida / EBITDA", value=float(DADOS_DEMO_ANALISE_PREMIUM["divida_liquida_ebitda"]), step=0.1)
        payout = st.number_input("Payout (%)", value=float(DADOS_DEMO_ANALISE_PREMIUM["payout"]), step=1.0)
        previsibilidade = st.slider("Previsibilidade", 0, 10, int(DADOS_DEMO_ANALISE_PREMIUM["previsibilidade"]))

    col_d, col_e, col_f = st.columns(3)

    with col_d:
        vantagem_competitiva = st.slider("Vantagem competitiva", 0, 10, int(DADOS_DEMO_ANALISE_PREMIUM["vantagem_competitiva"]))

    with col_e:
        qualidade_gestao = st.slider("Qualidade da gestão", 0, 10, int(DADOS_DEMO_ANALISE_PREMIUM["qualidade_gestao"]))

    with col_f:
        risco_regulatorio = st.slider("Risco regulatório", 0, 10, int(DADOS_DEMO_ANALISE_PREMIUM["risco_regulatorio"]))
        risco_ciclico = st.slider("Risco cíclico", 0, 10, int(DADOS_DEMO_ANALISE_PREMIUM["risco_ciclico"]))
        risco_disrupcao = st.slider("Risco disrupção", 0, 10, int(DADOS_DEMO_ANALISE_PREMIUM["risco_disrupcao"]))

    premissa_central = st.text_area("Premissa central", value=DADOS_DEMO_ANALISE_PREMIUM["premissa_central"], height=90)

    dados = {
        "empresa": empresa,
        "ticker": ticker,
        "setor": setor,
        "preco_atual": preco_atual,
        "preco_teto": preco_teto,
        "lucro_por_acao": lucro_por_acao,
        "fluxo_caixa_livre_por_acao": fluxo_caixa_livre_por_acao,
        "crescimento_receita_5a": crescimento_receita_5a,
        "crescimento_lucro_5a": crescimento_lucro_5a,
        "roic": roic,
        "roe": roe,
        "margem_liquida": margem_liquida,
        "divida_liquida_ebitda": divida_liquida_ebitda,
        "payout": payout,
        "previsibilidade": previsibilidade,
        "vantagem_competitiva": vantagem_competitiva,
        "qualidade_gestao": qualidade_gestao,
        "risco_regulatorio": risco_regulatorio,
        "risco_ciclico": risco_ciclico,
        "risco_disrupcao": risco_disrupcao,
        "premissa_central": premissa_central,
    }

    resultado = calcular_analise_premium_valoris(dados)
    _renderizar_resultado_premium(resultado)

    st.divider()

    col_btn_1, col_btn_2, col_btn_3, col_btn_4 = st.columns(4)

    with col_btn_1:
        if st.button("Gerar manifesto Premium", key="premium_manifesto"):
            manifesto = gerar_manifesto_analise_premium()
            st.success(f"Manifesto gerado: {CAMINHO_MANIFESTO_ANALISE_PREMIUM}")
            st.json(
                {
                    "versao": manifesto["versao"],
                    "score_demo": manifesto["demo"]["score_final"],
                    "decisao_demo": manifesto["demo"]["decisao"],
                }
            )

    with col_btn_2:
        if st.button("Gerar demo Premium", key="premium_demo"):
            demo = gerar_demo_analise_premium()
            st.success(f"Demo gerada: {CAMINHO_DEMO_ANALISE_PREMIUM_JSON}")
            st.json({"score_final": demo["score_final"], "decisao": demo["decisao"]})

    with col_btn_3:
        if st.button("Salvar relatório .md", key="premium_relatorio"):
            retorno = salvar_relatorio_analise_premium_markdown(resultado)
            st.success(f"Relatório salvo: {retorno['arquivo']}")
            st.json(retorno)

    with col_btn_4:
        if st.button("Salvar decisão Premium", key="premium_decisao"):
            registro = salvar_decisao_analise_premium(resultado, observacoes="Decisão gerada pela experiência premium.")
            st.success(f"Decisão salva: {registro['decisao']}")
            st.rerun()

    st.download_button(
        "Baixar relatório premium (.md)",
        data=gerar_markdown_analise_premium(resultado),
        file_name="RELATORIO_ANALISE_PREMIUM_VALORIS.md",
        mime="text/markdown",
        key="download_relatorio_premium",
    )

    st.download_button(
        "Baixar decisões Premium (.csv)",
        data=gerar_csv_decisoes_analise_premium(),
        file_name="decisoes_analise_premium_valoris.csv",
        mime="text/csv",
        key="download_decisoes_premium",
    )


def executar_autoteste_analise_premium_valoris() -> List[Dict[str, str]]:
    saude = calcular_saude_analise_premium()
    demo = calcular_analise_premium_valoris(DADOS_DEMO_ANALISE_PREMIUM)

    return [
        {
            "teste": "versao_analise_premium",
            "status": "OK" if VERSAO_ANALISE_PREMIUM_VALORIS == "3.8.76" else "FALHA",
            "detalhe": VERSAO_ANALISE_PREMIUM_VALORIS,
        },
        {
            "teste": "score_produto_premium",
            "status": "OK" if 0 <= saude["score_produto_premium"] <= 100 else "FALHA",
            "detalhe": str(saude["score_produto_premium"]),
        },
        {
            "teste": "demo_premium",
            "status": "OK" if demo["score_final"] > 0 and bool(demo["decisao"]) else "FALHA",
            "detalhe": demo["decisao"],
        },
        {
            "teste": "renderizador",
            "status": "OK" if callable(renderizar_analise_premium_valoris) else "FALHA",
            "detalhe": "renderizar_analise_premium_valoris",
        },
    ]
