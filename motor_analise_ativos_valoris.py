# motor_analise_ativos_valoris.py
# Valoris — Motor Central de Análise de Ativos v3.9.0
# ------------------------------------------------------------
# Objetivo:
# - Criar o coração analítico da Valoris.
# - Transformar dados fundamentais em preço teto, risco, qualidade e decisão.
# - Servir como camada central para relatórios, comparador, watchlist e pacote premium.
# ------------------------------------------------------------

from __future__ import annotations

import csv
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st


VERSAO_MOTOR_ANALISE_ATIVOS_VALORIS = "3.9.0"

CAMINHO_ANALISES = Path("analises_motor_ativos_valoris.csv")
CAMINHO_DECISOES = Path("decisoes_motor_analise_ativos_valoris.csv")
CAMINHO_RELATORIO = Path("RELATORIO_MOTOR_ANALISE_ATIVOS_VALORIS.md")
CAMINHO_MANIFESTO = Path("manifesto_motor_analise_ativos_valoris.json")

CAMPOS_ANALISES = [
    "data_hora",
    "ticker",
    "nome_empresa",
    "setor",
    "preco_atual",
    "preco_teto",
    "margem_seguranca_atual",
    "score_qualidade",
    "score_risco",
    "score_valor",
    "score_final",
    "decisao",
    "nivel_conviccao",
    "modelo_preco_teto",
    "observacao",
]

CAMPOS_DECISOES = [
    "data_hora",
    "ticker",
    "decisao",
    "preco_atual",
    "preco_teto",
    "score_final",
    "observacao",
]


def _agora_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat(sep=" ")


def _numero(valor: Any, padrao: float = 0.0) -> float:
    try:
        if valor is None:
            return padrao
        if isinstance(valor, str):
            valor = valor.replace("%", "").replace(",", ".").strip()
            if valor == "":
                return padrao
        numero = float(valor)
        if math.isnan(numero) or math.isinf(numero):
            return padrao
        return numero
    except Exception:
        return padrao


def _limitar(valor: float, minimo: float = 0.0, maximo: float = 100.0) -> float:
    return max(minimo, min(maximo, valor))


def _pct(valor: float) -> str:
    return f"{valor:.1f}%"


def _moeda(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _score_intervalo(valor: float, ruim: float, bom: float, inverso: bool = False) -> float:
    if bom == ruim:
        return 50.0

    if inverso:
        bruto = (ruim - valor) / (ruim - bom)
    else:
        bruto = (valor - ruim) / (bom - ruim)

    return _limitar(bruto * 100)


def calcular_preco_teto_por_lucro(lpa: float, pe_teto: float, margem_seguranca: float) -> Optional[float]:
    lpa = _numero(lpa)
    pe_teto = _numero(pe_teto)
    margem_seguranca = _limitar(_numero(margem_seguranca), 0, 80)

    if lpa <= 0 or pe_teto <= 0:
        return None

    valor_justo = lpa * pe_teto
    return max(0.0, valor_justo * (1 - margem_seguranca / 100))


def calcular_preco_teto_por_fcf(fcf_por_acao: float, yield_fcf_requerido: float, margem_seguranca: float) -> Optional[float]:
    fcf_por_acao = _numero(fcf_por_acao)
    yield_fcf_requerido = _numero(yield_fcf_requerido)
    margem_seguranca = _limitar(_numero(margem_seguranca), 0, 80)

    if fcf_por_acao <= 0 or yield_fcf_requerido <= 0:
        return None

    valor_justo = fcf_por_acao / (yield_fcf_requerido / 100)
    return max(0.0, valor_justo * (1 - margem_seguranca / 100))


def calcular_preco_teto_por_dividendos(dividendo_por_acao: float, dy_minimo: float, margem_seguranca: float) -> Optional[float]:
    dividendo_por_acao = _numero(dividendo_por_acao)
    dy_minimo = _numero(dy_minimo)
    margem_seguranca = _limitar(_numero(margem_seguranca), 0, 80)

    if dividendo_por_acao <= 0 or dy_minimo <= 0:
        return None

    valor_justo = dividendo_por_acao / (dy_minimo / 100)
    return max(0.0, valor_justo * (1 - margem_seguranca / 100))


def calcular_preco_teto_por_patrimonio(vpa: float, pvp_teto: float, margem_seguranca: float) -> Optional[float]:
    vpa = _numero(vpa)
    pvp_teto = _numero(pvp_teto)
    margem_seguranca = _limitar(_numero(margem_seguranca), 0, 80)

    if vpa <= 0 or pvp_teto <= 0:
        return None

    valor_justo = vpa * pvp_teto
    return max(0.0, valor_justo * (1 - margem_seguranca / 100))


def calcular_modelos_preco_teto(dados: Dict[str, Any]) -> Dict[str, Optional[float]]:
    margem = _numero(dados.get("margem_seguranca", 25))

    modelos = {
        "Lucro/P-L": calcular_preco_teto_por_lucro(
            dados.get("lpa", 0),
            dados.get("pe_teto", 15),
            margem,
        ),
        "Fluxo de Caixa/Yield FCF": calcular_preco_teto_por_fcf(
            dados.get("fcf_por_acao", 0),
            dados.get("yield_fcf_requerido", 8),
            margem,
        ),
        "Dividendos/DY": calcular_preco_teto_por_dividendos(
            dados.get("dividendo_por_acao", 0),
            dados.get("dy_minimo", 6),
            margem,
        ),
        "Patrimônio/P-VP": calcular_preco_teto_por_patrimonio(
            dados.get("vpa", 0),
            dados.get("pvp_teto", 1.5),
            margem,
        ),
    }

    return modelos


def escolher_preco_teto_conservador(modelos: Dict[str, Optional[float]]) -> Tuple[float, str]:
    validos = {
        nome: valor
        for nome, valor in modelos.items()
        if valor is not None and valor > 0
    }

    if not validos:
        return 0.0, "Sem modelo válido"

    # Critério conservador: usa o menor preço teto entre os modelos válidos.
    nome_modelo, preco_teto = min(validos.items(), key=lambda item: item[1])
    return float(preco_teto), nome_modelo


def calcular_score_qualidade(dados: Dict[str, Any]) -> float:
    roe = _numero(dados.get("roe", 0))
    margem_liquida = _numero(dados.get("margem_liquida", 0))
    crescimento_receita = _numero(dados.get("crescimento_receita", 0))
    div_liquida_ebitda = _numero(dados.get("div_liquida_ebitda", 0))
    recorrencia = _numero(dados.get("recorrencia_receita", 50))
    governanca = _numero(dados.get("governanca", 50))
    vantagem = _numero(dados.get("vantagem_competitiva", 50))

    score_roe = _score_intervalo(roe, 5, 22)
    score_margem = _score_intervalo(margem_liquida, 5, 25)
    score_crescimento = _score_intervalo(crescimento_receita, -5, 15)
    score_alavancagem = _score_intervalo(div_liquida_ebitda, 4, 0.5, inverso=True)
    score_recorrencia = _limitar(recorrencia)
    score_governanca = _limitar(governanca)
    score_vantagem = _limitar(vantagem)

    score = (
        score_roe * 0.20
        + score_margem * 0.15
        + score_crescimento * 0.12
        + score_alavancagem * 0.16
        + score_recorrencia * 0.12
        + score_governanca * 0.12
        + score_vantagem * 0.13
    )

    return round(_limitar(score), 1)


def calcular_score_risco(dados: Dict[str, Any]) -> float:
    # Neste app, score_risco alto significa MENOR risco.
    div_liquida_ebitda = _numero(dados.get("div_liquida_ebitda", 0))
    ciclicidade = _numero(dados.get("ciclicidade", 50))
    volatilidade_lucro = _numero(dados.get("volatilidade_lucro", 50))
    dependencia_regulatoria = _numero(dados.get("dependencia_regulatoria", 50))
    concentracao_receita = _numero(dados.get("concentracao_receita", 50))
    risco_governanca = 100 - _numero(dados.get("governanca", 50))

    score_alavancagem = _score_intervalo(div_liquida_ebitda, 4.5, 0.5, inverso=True)
    score_ciclicidade = 100 - _limitar(ciclicidade)
    score_volatilidade = 100 - _limitar(volatilidade_lucro)
    score_regulatorio = 100 - _limitar(dependencia_regulatoria)
    score_concentracao = 100 - _limitar(concentracao_receita)
    score_governanca = 100 - _limitar(risco_governanca)

    score = (
        score_alavancagem * 0.24
        + score_ciclicidade * 0.16
        + score_volatilidade * 0.18
        + score_regulatorio * 0.15
        + score_concentracao * 0.12
        + score_governanca * 0.15
    )

    return round(_limitar(score), 1)


def calcular_score_valor(preco_atual: float, preco_teto: float) -> Tuple[float, float]:
    preco_atual = _numero(preco_atual)
    preco_teto = _numero(preco_teto)

    if preco_atual <= 0 or preco_teto <= 0:
        return 0.0, 0.0

    margem_seguranca_atual = ((preco_teto - preco_atual) / preco_atual) * 100

    if preco_atual <= preco_teto * 0.85:
        score = 100
    elif preco_atual <= preco_teto:
        score = 82
    elif preco_atual <= preco_teto * 1.15:
        score = 55
    elif preco_atual <= preco_teto * 1.35:
        score = 30
    else:
        score = 10

    return float(score), round(margem_seguranca_atual, 1)


def calcular_score_final(score_qualidade: float, score_risco: float, score_valor: float) -> float:
    score = (
        _limitar(score_qualidade) * 0.42
        + _limitar(score_risco) * 0.28
        + _limitar(score_valor) * 0.30
    )

    return round(_limitar(score), 1)


def decidir_analise(score_final: float, score_qualidade: float, score_risco: float, score_valor: float) -> Tuple[str, str]:
    score_final = _numero(score_final)
    score_qualidade = _numero(score_qualidade)
    score_risco = _numero(score_risco)
    score_valor = _numero(score_valor)

    if score_risco < 35:
        return "DESCARTAR / RISCO ALTO", "Baixa"
    if score_qualidade < 40:
        return "NEUTRO / QUALIDADE FRACA", "Baixa"
    if score_final >= 78 and score_valor >= 80 and score_qualidade >= 65:
        return "COMPRA RACIONAL", "Alta"
    if score_final >= 65 and score_valor >= 55:
        return "AGUARDAR / COMPRAR AOS POUCOS", "Média"
    if score_final >= 55:
        return "NEUTRO / MONITORAR", "Média"
    return "AGUARDAR / CARO OU INCERTO", "Baixa"


def gerar_alertas_qualitativos(dados: Dict[str, Any], resultado: Dict[str, Any]) -> List[str]:
    alertas: List[str] = []

    if _numero(dados.get("div_liquida_ebitda", 0)) > 3:
        alertas.append("Alavancagem elevada: dívida líquida/EBITDA acima de 3x.")

    if _numero(dados.get("roe", 0)) < 8:
        alertas.append("ROE baixo: retorno sobre patrimônio ainda fraco.")

    if _numero(dados.get("margem_liquida", 0)) < 5:
        alertas.append("Margem líquida baixa: pouca folga operacional.")

    if _numero(dados.get("dependencia_regulatoria", 0)) > 70:
        alertas.append("Risco regulatório alto: a tese depende fortemente de regras externas.")

    if _numero(resultado.get("preco_teto", 0)) <= 0:
        alertas.append("Preço teto indisponível: faltam dados válidos para valuation.")

    if not alertas:
        alertas.append("Nenhum alerta crítico detectado pelos critérios atuais.")

    return alertas


def analisar_ativo(dados: Dict[str, Any]) -> Dict[str, Any]:
    modelos = calcular_modelos_preco_teto(dados)
    preco_teto, modelo_preco_teto = escolher_preco_teto_conservador(modelos)

    score_qualidade = calcular_score_qualidade(dados)
    score_risco = calcular_score_risco(dados)
    score_valor, margem_seguranca_atual = calcular_score_valor(dados.get("preco_atual", 0), preco_teto)
    score_final = calcular_score_final(score_qualidade, score_risco, score_valor)

    decisao, nivel_conviccao = decidir_analise(
        score_final=score_final,
        score_qualidade=score_qualidade,
        score_risco=score_risco,
        score_valor=score_valor,
    )

    resultado = {
        "data_hora": _agora_iso(),
        "ticker": str(dados.get("ticker", "")).upper().strip(),
        "nome_empresa": str(dados.get("nome_empresa", "")).strip(),
        "setor": str(dados.get("setor", "")).strip(),
        "preco_atual": round(_numero(dados.get("preco_atual", 0)), 2),
        "preco_teto": round(preco_teto, 2),
        "margem_seguranca_atual": margem_seguranca_atual,
        "score_qualidade": score_qualidade,
        "score_risco": score_risco,
        "score_valor": score_valor,
        "score_final": score_final,
        "decisao": decisao,
        "nivel_conviccao": nivel_conviccao,
        "modelo_preco_teto": modelo_preco_teto,
        "modelos_preco_teto": modelos,
        "alertas": [],
    }

    resultado["alertas"] = gerar_alertas_qualitativos(dados, resultado)

    return resultado


def explicar_decisao(resultado: Dict[str, Any]) -> str:
    preco_atual = _numero(resultado.get("preco_atual", 0))
    preco_teto = _numero(resultado.get("preco_teto", 0))
    margem = _numero(resultado.get("margem_seguranca_atual", 0))

    linhas = [
        f"A decisão foi **{resultado.get('decisao', 'indefinida')}** com convicção **{resultado.get('nivel_conviccao', 'indefinida')}**.",
        "",
        f"O preço atual informado foi **{_moeda(preco_atual)}** e o preço teto conservador calculado foi **{_moeda(preco_teto)}**.",
        f"A margem de segurança atual é de **{_pct(margem)}**.",
        "",
        "Scores:",
        f"- Qualidade: {resultado.get('score_qualidade', 0)}/100",
        f"- Risco: {resultado.get('score_risco', 0)}/100",
        f"- Valor/preço: {resultado.get('score_valor', 0)}/100",
        f"- Score final: {resultado.get('score_final', 0)}/100",
        "",
        f"Modelo conservador usado para preço teto: **{resultado.get('modelo_preco_teto', '')}**.",
    ]

    alertas = resultado.get("alertas", [])
    if alertas:
        linhas.append("")
        linhas.append("Alertas:")
        for alerta in alertas:
            linhas.append(f"- {alerta}")

    return "\n".join(linhas)


def salvar_analise_motor_ativos(resultado: Dict[str, Any], caminho: Path = CAMINHO_ANALISES) -> Path:
    existe = caminho.exists()

    with caminho.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_ANALISES)

        if not existe:
            escritor.writeheader()

        escritor.writerow(
            {
                campo: resultado.get(campo, "")
                for campo in CAMPOS_ANALISES
            }
        )

    return caminho


def salvar_decisao_motor_ativos(resultado: Dict[str, Any], observacao: str = "", caminho: Path = CAMINHO_DECISOES) -> Path:
    existe = caminho.exists()

    with caminho.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISOES)

        if not existe:
            escritor.writeheader()

        escritor.writerow(
            {
                "data_hora": _agora_iso(),
                "ticker": resultado.get("ticker", ""),
                "decisao": resultado.get("decisao", ""),
                "preco_atual": resultado.get("preco_atual", ""),
                "preco_teto": resultado.get("preco_teto", ""),
                "score_final": resultado.get("score_final", ""),
                "observacao": observacao,
            }
        )

    return caminho


def gerar_relatorio_motor_ativos_markdown(resultado: Dict[str, Any]) -> str:
    linhas = [
        "# Relatório do Motor Central de Análise de Ativos — Valoris",
        "",
        f"Data: {_agora_iso()}",
        f"Versão: {VERSAO_MOTOR_ANALISE_ATIVOS_VALORIS}",
        "",
        f"## {resultado.get('ticker', '')} — {resultado.get('nome_empresa', '')}",
        "",
        f"- Setor: {resultado.get('setor', '')}",
        f"- Preço atual: {_moeda(_numero(resultado.get('preco_atual', 0)))}",
        f"- Preço teto conservador: {_moeda(_numero(resultado.get('preco_teto', 0)))}",
        f"- Margem de segurança atual: {_pct(_numero(resultado.get('margem_seguranca_atual', 0)))}",
        f"- Decisão: {resultado.get('decisao', '')}",
        f"- Convicção: {resultado.get('nivel_conviccao', '')}",
        "",
        "## Explicação",
        "",
        explicar_decisao(resultado),
        "",
        "## Modelos de preço teto",
        "",
    ]

    modelos = resultado.get("modelos_preco_teto", {})

    for nome, valor in modelos.items():
        if valor is None:
            linhas.append(f"- {nome}: indisponível")
        else:
            linhas.append(f"- {nome}: {_moeda(float(valor))}")

    linhas.extend(
        [
            "",
            "## Nota",
            "",
            "Este relatório é uma ferramenta educacional e de apoio à decisão. Ele não substitui análise profissional, leitura de balanços, gestão de risco e julgamento próprio.",
        ]
    )

    return "\n".join(linhas)


def salvar_relatorio_motor_ativos_markdown(resultado: Dict[str, Any], caminho: Path = CAMINHO_RELATORIO) -> Path:
    caminho.write_text(gerar_relatorio_motor_ativos_markdown(resultado), encoding="utf-8")
    return caminho


def gerar_manifesto_motor_ativos(resultado: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "produto": "Valoris",
        "versao": VERSAO_MOTOR_ANALISE_ATIVOS_VALORIS,
        "modulo": "motor_analise_ativos_valoris",
        "data_hora": _agora_iso(),
        "ticker": resultado.get("ticker", ""),
        "score_final": resultado.get("score_final", 0),
        "decisao": resultado.get("decisao", ""),
        "principio": "análise conservadora, cética, didática e baseada em margem de segurança",
    }


def salvar_manifesto_motor_ativos(resultado: Dict[str, Any], caminho: Path = CAMINHO_MANIFESTO) -> Path:
    caminho.write_text(
        json.dumps(gerar_manifesto_motor_ativos(resultado), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return caminho


def renderizar_modelos_preco_teto(modelos: Dict[str, Optional[float]]) -> None:
    st.markdown("### Modelos de preço teto")

    linhas = []

    for nome, valor in modelos.items():
        linhas.append(
            {
                "Modelo": nome,
                "Preço teto": "Indisponível" if valor is None else _moeda(float(valor)),
            }
        )

    st.dataframe(linhas, use_container_width=True, hide_index=True)


def renderizar_motor_analise_ativos_valoris() -> None:
    st.subheader("Motor Central de Análise de Ativos")
    st.caption(
        "Primeira versão do coração da Valoris: dados fundamentais → preço teto → qualidade → risco → decisão."
    )

    with st.form("form_motor_analise_ativos"):
        st.markdown("### Identificação")

        col1, col2, col3 = st.columns(3)
        ticker = col1.text_input("Ticker", value="ITUB4")
        nome_empresa = col2.text_input("Nome da empresa", value="Itaú Unibanco")
        setor = col3.text_input("Setor", value="Financeiro")

        st.markdown("### Preço e premissas de valuation")

        col1, col2, col3, col4 = st.columns(4)
        preco_atual = col1.number_input("Preço atual", min_value=0.0, value=30.00, step=0.10)
        margem_seguranca = col2.slider("Margem de segurança exigida (%)", 0, 80, 25)
        pe_teto = col3.number_input("P/L teto aceitável", min_value=0.0, value=12.0, step=0.5)
        yield_fcf_requerido = col4.number_input("Yield FCF requerido (%)", min_value=0.0, value=8.0, step=0.5)

        col1, col2, col3, col4 = st.columns(4)
        lpa = col1.number_input("Lucro por ação — LPA", min_value=0.0, value=2.50, step=0.10)
        fcf_por_acao = col2.number_input("FCF por ação", min_value=0.0, value=2.20, step=0.10)
        dividendo_por_acao = col3.number_input("Dividendo por ação", min_value=0.0, value=1.20, step=0.10)
        dy_minimo = col4.number_input("DY mínimo exigido (%)", min_value=0.0, value=6.0, step=0.5)

        col1, col2 = st.columns(2)
        vpa = col1.number_input("Valor patrimonial por ação — VPA", min_value=0.0, value=18.0, step=0.10)
        pvp_teto = col2.number_input("P/VP teto aceitável", min_value=0.0, value=1.5, step=0.1)

        st.markdown("### Qualidade e risco")

        col1, col2, col3, col4 = st.columns(4)
        roe = col1.number_input("ROE (%)", value=18.0, step=0.5)
        margem_liquida = col2.number_input("Margem líquida (%)", value=18.0, step=0.5)
        crescimento_receita = col3.number_input("Crescimento de receita (%)", value=8.0, step=0.5)
        div_liquida_ebitda = col4.number_input("Dívida líquida / EBITDA", value=1.5, step=0.1)

        col1, col2, col3 = st.columns(3)
        recorrencia_receita = col1.slider("Recorrência da receita", 0, 100, 70)
        governanca = col2.slider("Governança", 0, 100, 75)
        vantagem_competitiva = col3.slider("Vantagem competitiva", 0, 100, 70)

        col1, col2, col3, col4 = st.columns(4)
        ciclicidade = col1.slider("Ciclicidade do negócio", 0, 100, 40)
        volatilidade_lucro = col2.slider("Volatilidade dos lucros", 0, 100, 35)
        dependencia_regulatoria = col3.slider("Dependência regulatória", 0, 100, 45)
        concentracao_receita = col4.slider("Concentração de receita", 0, 100, 35)

        observacao = st.text_area("Observação qualitativa", value="Análise inicial do motor central.")

        enviado = st.form_submit_button("Analisar ativo")

    if not enviado:
        st.info("Preencha os dados e clique em **Analisar ativo**.")
        return

    dados = {
        "ticker": ticker,
        "nome_empresa": nome_empresa,
        "setor": setor,
        "preco_atual": preco_atual,
        "margem_seguranca": margem_seguranca,
        "pe_teto": pe_teto,
        "yield_fcf_requerido": yield_fcf_requerido,
        "lpa": lpa,
        "fcf_por_acao": fcf_por_acao,
        "dividendo_por_acao": dividendo_por_acao,
        "dy_minimo": dy_minimo,
        "vpa": vpa,
        "pvp_teto": pvp_teto,
        "roe": roe,
        "margem_liquida": margem_liquida,
        "crescimento_receita": crescimento_receita,
        "div_liquida_ebitda": div_liquida_ebitda,
        "recorrencia_receita": recorrencia_receita,
        "governanca": governanca,
        "vantagem_competitiva": vantagem_competitiva,
        "ciclicidade": ciclicidade,
        "volatilidade_lucro": volatilidade_lucro,
        "dependencia_regulatoria": dependencia_regulatoria,
        "concentracao_receita": concentracao_receita,
    }

    resultado = analisar_ativo(dados)
    resultado["observacao"] = observacao

    st.divider()

    st.markdown("### Resultado da análise")

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Preço atual", _moeda(resultado["preco_atual"]))
    col2.metric("Preço teto", _moeda(resultado["preco_teto"]))
    col3.metric("Margem atual", _pct(resultado["margem_seguranca_atual"]))
    col4.metric("Score final", f"{resultado['score_final']}/100")
    col5.metric("Convicção", resultado["nivel_conviccao"])

    st.success(resultado["decisao"])

    st.markdown("### Explicação racional")
    st.markdown(explicar_decisao(resultado))

    renderizar_modelos_preco_teto(resultado["modelos_preco_teto"])

    st.markdown("### Alertas")
    for alerta in resultado["alertas"]:
        st.warning(alerta)

    st.divider()

    col1, col2, col3, col4 = st.columns(4)

    if col1.button("Salvar análise"):
        caminho = salvar_analise_motor_ativos(resultado)
        st.success(f"Análise salva em {caminho}")

    if col2.button("Salvar decisão"):
        caminho = salvar_decisao_motor_ativos(resultado, observacao=observacao)
        st.success(f"Decisão salva em {caminho}")

    if col3.button("Salvar relatório"):
        caminho = salvar_relatorio_motor_ativos_markdown(resultado)
        st.success(f"Relatório salvo em {caminho}")

    if col4.button("Salvar manifesto"):
        caminho = salvar_manifesto_motor_ativos(resultado)
        st.success(f"Manifesto salvo em {caminho}")


def executar_autoteste_motor_analise_ativos_valoris() -> Dict[str, Any]:
    dados = {
        "ticker": "TEST3",
        "nome_empresa": "Empresa Teste",
        "setor": "Teste",
        "preco_atual": 20,
        "margem_seguranca": 25,
        "pe_teto": 12,
        "yield_fcf_requerido": 8,
        "lpa": 2.5,
        "fcf_por_acao": 2.2,
        "dividendo_por_acao": 1.0,
        "dy_minimo": 6,
        "vpa": 15,
        "pvp_teto": 1.4,
        "roe": 18,
        "margem_liquida": 15,
        "crescimento_receita": 7,
        "div_liquida_ebitda": 1.5,
        "recorrencia_receita": 70,
        "governanca": 75,
        "vantagem_competitiva": 70,
        "ciclicidade": 40,
        "volatilidade_lucro": 35,
        "dependencia_regulatoria": 45,
        "concentracao_receita": 35,
    }

    resultado = analisar_ativo(dados)

    return {
        "ok": resultado["preco_teto"] > 0 and resultado["score_final"] > 0,
        "versao": VERSAO_MOTOR_ANALISE_ATIVOS_VALORIS,
        "resultado": {
            "ticker": resultado["ticker"],
            "preco_teto": resultado["preco_teto"],
            "score_final": resultado["score_final"],
            "decisao": resultado["decisao"],
        },
    }
