# historico_analises_valoris.py
# Valoris — Histórico de Análises do Motor v3.9.2
# ------------------------------------------------------------
# Objetivo:
# - Transformar o Motor de Análise em uma ferramenta com memória.
# - Ler análises salvas pelo motor central.
# - Filtrar, resumir, auditar e preparar integração com Watchlist e Relatório Premium.
# ------------------------------------------------------------

from __future__ import annotations

import csv
import json
from collections import Counter, deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st


VERSAO_HISTORICO_ANALISES_VALORIS = "3.9.2"

CAMINHO_ANALISES = Path("analises_motor_ativos_valoris.csv")
CAMINHO_DECISOES = Path("decisoes_historico_analises_valoris.csv")
CAMINHO_RELATORIO = Path("RELATORIO_HISTORICO_ANALISES_VALORIS.md")
CAMINHO_MANIFESTO = Path("manifesto_historico_analises_valoris.json")

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
    "decisao",
    "ticker",
    "score_final",
    "observacao",
]


def _agora_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat(sep=" ")


def _txt(valor: Any) -> str:
    return "" if valor is None else str(valor).strip()


def _float(valor: Any, padrao: float = 0.0) -> float:
    try:
        if valor is None:
            return padrao

        if isinstance(valor, str):
            valor = valor.replace("R$", "").replace("%", "").replace(".", "").replace(",", ".").strip()

            if valor == "":
                return padrao

        return float(valor)
    except Exception:
        return padrao


def _moeda(valor: Any) -> str:
    numero = _float(valor)
    return f"R$ {numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _pct(valor: Any) -> str:
    return f"{_float(valor):.1f}%"


def _garantir_csv(caminho: Path, campos: List[str]) -> None:
    if caminho.exists():
        return

    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()


def carregar_historico_analises(max_registros: int = 800) -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_ANALISES, CAMPOS_ANALISES)

    try:
        with CAMINHO_ANALISES.open("r", newline="", encoding="utf-8") as arquivo:
            leitor = csv.DictReader(arquivo)
            return list(deque(leitor, maxlen=max_registros))
    except Exception:
        return []


def carregar_decisoes_historico(max_registros: int = 300) -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_DECISOES, CAMPOS_DECISOES)

    try:
        with CAMINHO_DECISOES.open("r", newline="", encoding="utf-8") as arquivo:
            leitor = csv.DictReader(arquivo)
            return list(deque(leitor, maxlen=max_registros))
    except Exception:
        return []


def salvar_decisao_historico(decisao: str, ticker: str = "", score_final: Any = "", observacao: str = "") -> Path:
    _garantir_csv(CAMINHO_DECISOES, CAMPOS_DECISOES)

    with CAMINHO_DECISOES.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISOES)
        escritor.writerow(
            {
                "data_hora": _agora_iso(),
                "decisao": _txt(decisao),
                "ticker": _txt(ticker).upper(),
                "score_final": _txt(score_final),
                "observacao": _txt(observacao),
            }
        )

    return CAMINHO_DECISOES


def filtrar_historico(
    registros: List[Dict[str, str]],
    ticker: str = "",
    decisao: str = "Todas",
    score_minimo: float = 0.0,
) -> List[Dict[str, str]]:
    ticker = _txt(ticker).upper()
    decisao = _txt(decisao)

    filtrados = []

    for item in registros:
        item_ticker = _txt(item.get("ticker")).upper()
        item_decisao = _txt(item.get("decisao"))
        item_score = _float(item.get("score_final"), 0.0)

        if ticker and ticker not in item_ticker:
            continue

        if decisao and decisao != "Todas" and decisao != item_decisao:
            continue

        if item_score < score_minimo:
            continue

        filtrados.append(item)

    return filtrados


def calcular_metricas_historico(registros: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
    if registros is None:
        registros = carregar_historico_analises()

    total = len(registros)
    tickers = [_txt(item.get("ticker")).upper() for item in registros if _txt(item.get("ticker"))]
    decisoes = [_txt(item.get("decisao")) for item in registros if _txt(item.get("decisao"))]
    setores = [_txt(item.get("setor")) for item in registros if _txt(item.get("setor"))]
    scores = [_float(item.get("score_final"), 0.0) for item in registros]

    score_medio = round(sum(scores) / len(scores), 1) if scores else 0.0

    melhor = None
    if registros:
        melhor = max(registros, key=lambda item: _float(item.get("score_final"), 0.0))

    contador_decisoes = Counter(decisoes)
    contador_setores = Counter(setores)
    contador_tickers = Counter(tickers)

    compras = sum(
        quantidade
        for decisao, quantidade in contador_decisoes.items()
        if "COMPRA" in decisao.upper()
    )

    aguardando = sum(
        quantidade
        for decisao, quantidade in contador_decisoes.items()
        if "AGUARDAR" in decisao.upper() or "MONITORAR" in decisao.upper()
    )

    descartes = sum(
        quantidade
        for decisao, quantidade in contador_decisoes.items()
        if "DESCARTAR" in decisao.upper() or "RISCO" in decisao.upper()
    )

    return {
        "versao": VERSAO_HISTORICO_ANALISES_VALORIS,
        "gerado_em": _agora_iso(),
        "analises_total": total,
        "tickers_unicos": len(set(tickers)),
        "score_medio": score_medio,
        "compras": compras,
        "aguardando": aguardando,
        "descartes": descartes,
        "decisoes": dict(contador_decisoes),
        "setores": dict(contador_setores),
        "tickers_mais_analisados": dict(contador_tickers.most_common(10)),
        "melhor_analise": melhor or {},
    }


def classificar_saude_historico(metricas: Dict[str, Any]) -> Dict[str, Any]:
    total = int(metricas.get("analises_total", 0) or 0)
    tickers = int(metricas.get("tickers_unicos", 0) or 0)
    score_medio = _float(metricas.get("score_medio"), 0.0)

    score = 25
    score += min(total * 6, 36)
    score += min(tickers * 8, 24)

    if score_medio >= 70:
        score += 18
    elif score_medio >= 55:
        score += 10
    elif score_medio > 0:
        score += 5

    score = max(0, min(100, int(score)))

    if total == 0:
        risco = "Alto"
        decisao = "Histórico vazio"
        proximo = "Criar pelo menos uma análise no Motor Análise Ativos e salvá-la."
    elif total < 3:
        risco = "Médio/Alto"
        decisao = "Histórico inicial, ainda fraco para aprendizado"
        proximo = "Salvar análises de pelo menos 3 ativos diferentes."
    elif tickers < 3:
        risco = "Médio"
        decisao = "Histórico funcional, mas concentrado"
        proximo = "Analisar mais tickers para comparar qualidade, risco e preço."
    elif score >= 75:
        risco = "Baixo"
        decisao = "Histórico útil para integração com Watchlist e Relatório Premium"
        proximo = "Criar integração entre análise salva, watchlist e dossiê premium."
    else:
        risco = "Médio"
        decisao = "Histórico útil, mas ainda precisa de mais volume"
        proximo = "Continuar registrando análises antes de automatizar decisões."

    return {
        "score_historico": score,
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo,
    }


def gerar_exemplo_analise() -> Dict[str, Any]:
    try:
        from motor_analise_ativos_valoris import analisar_ativo, salvar_analise_motor_ativos

        dados = {
            "ticker": "MA",
            "nome_empresa": "Mastercard",
            "setor": "Pagamentos",
            "preco_atual": 450,
            "margem_seguranca": 25,
            "pe_teto": 28,
            "yield_fcf_requerido": 5,
            "lpa": 13.5,
            "fcf_por_acao": 14.5,
            "dividendo_por_acao": 2.4,
            "dy_minimo": 1.2,
            "vpa": 35,
            "pvp_teto": 12,
            "roe": 80,
            "margem_liquida": 45,
            "crescimento_receita": 11,
            "div_liquida_ebitda": 0.8,
            "recorrencia_receita": 85,
            "governanca": 80,
            "vantagem_competitiva": 90,
            "ciclicidade": 25,
            "volatilidade_lucro": 25,
            "dependencia_regulatoria": 45,
            "concentracao_receita": 20,
        }

        resultado = analisar_ativo(dados)
        resultado["observacao"] = "Exemplo gerado pelo Histórico de Análises v3.9.2."
        salvar_analise_motor_ativos(resultado)

        return {"ok": True, "resultado": resultado}

    except Exception as erro:
        return {"ok": False, "erro": str(erro)}


def gerar_csv_historico(registros: Optional[List[Dict[str, str]]] = None) -> str:
    if registros is None:
        registros = carregar_historico_analises()

    import io

    buffer = io.StringIO()
    escritor = csv.DictWriter(buffer, fieldnames=CAMPOS_ANALISES)
    escritor.writeheader()

    for item in registros:
        escritor.writerow({campo: item.get(campo, "") for campo in CAMPOS_ANALISES})

    return buffer.getvalue()


def gerar_relatorio_historico_markdown(registros: Optional[List[Dict[str, str]]] = None) -> str:
    if registros is None:
        registros = carregar_historico_analises()

    metricas = calcular_metricas_historico(registros)
    saude = classificar_saude_historico(metricas)

    melhor = metricas.get("melhor_analise", {}) or {}

    ultimas = registros[-20:]
    linhas_ultimas = "\n".join(
        [
            f"- **{item.get('ticker', '')}** — {item.get('decisao', '')} — score {item.get('score_final', '')}/100 — teto {_moeda(item.get('preco_teto', 0))} — {item.get('data_hora', '')}"
            for item in reversed(ultimas)
        ]
    ) or "- Nenhuma análise registrada."

    linhas_decisoes = "\n".join(
        [
            f"- {decisao}: {quantidade}"
            for decisao, quantidade in metricas.get("decisoes", {}).items()
        ]
    ) or "- Nenhuma decisão registrada."

    return f"""# Histórico de Análises — Valoris

Versão: {VERSAO_HISTORICO_ANALISES_VALORIS}  
Gerado em: {_agora_iso()}

## Diagnóstico

Score Histórico: {saude['score_historico']}/100  
Risco: {saude['risco']}  
Decisão: {saude['decisao']}  
Próximo passo: {saude['proximo_passo']}

## Métricas

Análises salvas: {metricas['analises_total']}  
Tickers únicos: {metricas['tickers_unicos']}  
Score médio: {metricas['score_medio']}/100  
Compras racionais: {metricas['compras']}  
Aguardando/monitorando: {metricas['aguardando']}  
Descartes/risco alto: {metricas['descartes']}

## Melhor análise por score

Ticker: {melhor.get('ticker', 'N/D')}  
Empresa: {melhor.get('nome_empresa', 'N/D')}  
Score: {melhor.get('score_final', 'N/D')}/100  
Decisão: {melhor.get('decisao', 'N/D')}  

## Decisões

{linhas_decisoes}

## Últimas análises

{linhas_ultimas}

## Leitura estratégica

O histórico é a ponte entre cálculo pontual e produto real. Sem histórico, a Valoris é apenas uma calculadora. Com histórico, ela passa a acompanhar evolução de tese, preço teto, risco e decisão.
"""


def salvar_relatorio_historico_markdown(registros: Optional[List[Dict[str, str]]] = None) -> Path:
    CAMINHO_RELATORIO.write_text(gerar_relatorio_historico_markdown(registros), encoding="utf-8")
    return CAMINHO_RELATORIO


def gerar_manifesto_historico(registros: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
    if registros is None:
        registros = carregar_historico_analises()

    metricas = calcular_metricas_historico(registros)
    saude = classificar_saude_historico(metricas)

    return {
        "produto": "Valoris",
        "versao": VERSAO_HISTORICO_ANALISES_VALORIS,
        "modulo": "historico_analises_valoris",
        "data_hora": _agora_iso(),
        "metricas": metricas,
        "saude": saude,
        "principio": "transformar análises pontuais em memória, comparação e acompanhamento",
        "proxima_integracao": "Motor Análise Ativos → Histórico → Watchlist → Relatório Premium",
    }


def salvar_manifesto_historico(registros: Optional[List[Dict[str, str]]] = None) -> Path:
    CAMINHO_MANIFESTO.write_text(
        json.dumps(gerar_manifesto_historico(registros), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return CAMINHO_MANIFESTO


def renderizar_cards_metricas(metricas: Dict[str, Any], saude: Dict[str, Any]) -> None:
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Score histórico", f"{saude['score_historico']}/100")
    col2.metric("Análises", metricas["analises_total"])
    col3.metric("Tickers", metricas["tickers_unicos"])
    col4.metric("Score médio", f"{metricas['score_medio']}/100")
    col5.metric("Compras", metricas["compras"])


def renderizar_historico_analises_valoris() -> None:
    st.subheader("Histórico de Análises")
    st.caption(
        "Memória do Motor Central: análises salvas, decisões, scores, preço teto e evolução do estudo."
    )

    registros = carregar_historico_analises()
    metricas = calcular_metricas_historico(registros)
    saude = classificar_saude_historico(metricas)

    renderizar_cards_metricas(metricas, saude)

    if saude["score_historico"] >= 75:
        st.success(f"{saude['decisao']} — {saude['proximo_passo']}")
    elif metricas["analises_total"] > 0:
        st.warning(f"{saude['decisao']} — {saude['proximo_passo']}")
    else:
        st.info(f"{saude['decisao']} — {saude['proximo_passo']}")

    st.divider()

    st.markdown("### Filtros")

    decisoes_disponiveis = ["Todas"] + sorted(
        list({item.get("decisao", "") for item in registros if item.get("decisao", "")})
    )

    col1, col2, col3 = st.columns(3)
    filtro_ticker = col1.text_input("Ticker", value="")
    filtro_decisao = col2.selectbox("Decisão", decisoes_disponiveis)
    score_minimo = col3.slider("Score mínimo", 0, 100, 0)

    filtrados = filtrar_historico(
        registros=registros,
        ticker=filtro_ticker,
        decisao=filtro_decisao,
        score_minimo=score_minimo,
    )

    st.markdown("### Análises encontradas")
    st.dataframe(filtrados, use_container_width=True, hide_index=True)

    st.download_button(
        "Baixar histórico filtrado em CSV",
        data=gerar_csv_historico(filtrados),
        file_name="historico_analises_valoris_filtrado.csv",
        mime="text/csv",
        disabled=not bool(filtrados),
    )

    st.divider()

    st.markdown("### Reabrir análise")

    if filtrados:
        opcoes = [
            f"{item.get('data_hora', '')} | {item.get('ticker', '')} | {item.get('decisao', '')} | score {item.get('score_final', '')}"
            for item in reversed(filtrados)
        ]

        escolha = st.selectbox("Escolha uma análise", opcoes)
        selecionado = list(reversed(filtrados))[opcoes.index(escolha)]

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Ticker", selecionado.get("ticker", ""))
        col2.metric("Preço atual", _moeda(selecionado.get("preco_atual", 0)))
        col3.metric("Preço teto", _moeda(selecionado.get("preco_teto", 0)))
        col4.metric("Score final", f"{selecionado.get('score_final', '')}/100")

        st.markdown("#### Detalhes")
        st.json(selecionado)

        st.markdown("#### Próximos usos desta análise")
        st.info(
            "Na próxima versão, este registro poderá ser enviado diretamente para a Watchlist e depois para o Relatório Premium."
        )

        if st.button("Registrar decisão sobre esta análise"):
            salvar_decisao_historico(
                decisao="revisada_no_historico",
                ticker=selecionado.get("ticker", ""),
                score_final=selecionado.get("score_final", ""),
                observacao=f"Análise revisada manualmente em {_agora_iso()}",
            )
            st.success("Decisão registrada no histórico.")
            st.rerun()
    else:
        st.info("Nenhuma análise encontrada com os filtros atuais.")

    st.divider()

    st.markdown("### Ações")

    col1, col2, col3, col4 = st.columns(4)

    if col1.button("Gerar análise exemplo"):
        retorno = gerar_exemplo_analise()
        if retorno.get("ok"):
            st.success("Análise exemplo gerada e salva.")
            st.rerun()
        else:
            st.error(retorno.get("erro", "Erro ao gerar exemplo."))

    if col2.button("Salvar relatório"):
        caminho = salvar_relatorio_historico_markdown(registros)
        st.success(f"Relatório salvo em {caminho}")

    if col3.button("Salvar manifesto"):
        caminho = salvar_manifesto_historico(registros)
        st.success(f"Manifesto salvo em {caminho}")

    if col4.button("Salvar decisão do histórico"):
        salvar_decisao_historico(
            decisao=saude["decisao"],
            ticker="GERAL",
            score_final=saude["score_historico"],
            observacao=saude["proximo_passo"],
        )
        st.success("Decisão geral do histórico salva.")
        st.rerun()

    st.download_button(
        "Baixar relatório do histórico (.md)",
        data=gerar_relatorio_historico_markdown(registros),
        file_name="RELATORIO_HISTORICO_ANALISES_VALORIS.md",
        mime="text/markdown",
    )

    st.markdown("### Decisões registradas")
    decisoes = carregar_decisoes_historico()
    if decisoes:
        st.dataframe(decisoes, use_container_width=True, hide_index=True)
    else:
        st.info("Ainda não há decisões específicas do histórico.")


def executar_autoteste_historico_analises_valoris() -> Dict[str, Any]:
    registros = carregar_historico_analises(max_registros=50)
    metricas = calcular_metricas_historico(registros)
    saude = classificar_saude_historico(metricas)

    return {
        "ok": True,
        "versao": VERSAO_HISTORICO_ANALISES_VALORIS,
        "metricas": {
            "analises_total": metricas["analises_total"],
            "tickers_unicos": metricas["tickers_unicos"],
            "score_historico": saude["score_historico"],
        },
    }
