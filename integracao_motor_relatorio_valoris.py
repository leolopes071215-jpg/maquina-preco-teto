# integracao_motor_relatorio_valoris.py
# Valoris — Integração Motor + Relatório Premium v3.9.4
# ------------------------------------------------------------
# Objetivo:
# - Transformar análises salvas pelo Motor Central em dossiês premium.
# - Criar a ponte: Motor → Histórico → Motor + Relatório → Relatório Premium/Pacote Premium.
# - Gerar resumo executivo, tese, riscos, perguntas críticas e plano de acompanhamento.
# ------------------------------------------------------------

from __future__ import annotations

import csv
import json
from collections import Counter, deque
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st


VERSAO_INTEGRACAO_MOTOR_RELATORIO_VALORIS = "3.9.4"

CAMINHO_ANALISES_MOTOR = Path("analises_motor_ativos_valoris.csv")
CAMINHO_DECISOES = Path("decisoes_integracao_motor_relatorio_valoris.csv")
CAMINHO_DOSSIE = Path("DOSSIE_MOTOR_RELATORIO_VALORIS.md")
CAMINHO_RELATORIO = Path("RELATORIO_INTEGRACAO_MOTOR_RELATORIO_VALORIS.md")
CAMINHO_MANIFESTO = Path("manifesto_integracao_motor_relatorio_valoris.json")

CAMPOS_ANALISES_MOTOR = [
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
    "empresa",
    "score_final",
    "decisao_motor",
    "acao_relatorio",
    "status",
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


def carregar_analises_motor(max_registros: int = 800) -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_ANALISES_MOTOR, CAMPOS_ANALISES_MOTOR)

    try:
        with CAMINHO_ANALISES_MOTOR.open("r", newline="", encoding="utf-8") as arquivo:
            leitor = csv.DictReader(arquivo)
            return list(deque(leitor, maxlen=max_registros))
    except Exception:
        return []


def carregar_decisoes_relatorio(max_registros: int = 300) -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_DECISOES, CAMPOS_DECISOES)

    try:
        with CAMINHO_DECISOES.open("r", newline="", encoding="utf-8") as arquivo:
            leitor = csv.DictReader(arquivo)
            return list(deque(leitor, maxlen=max_registros))
    except Exception:
        return []


def salvar_decisao_relatorio(
    analise: Dict[str, str],
    acao_relatorio: str,
    status: str,
    observacao: str = "",
) -> Path:
    _garantir_csv(CAMINHO_DECISOES, CAMPOS_DECISOES)

    with CAMINHO_DECISOES.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISOES)
        escritor.writerow(
            {
                "data_hora": _agora_iso(),
                "ticker": _txt(analise.get("ticker")).upper(),
                "empresa": _txt(analise.get("nome_empresa")),
                "score_final": _txt(analise.get("score_final")),
                "decisao_motor": _txt(analise.get("decisao")),
                "acao_relatorio": _txt(acao_relatorio),
                "status": _txt(status),
                "observacao": _txt(observacao),
            }
        )

    return CAMINHO_DECISOES


def calcular_metricas_integracao_relatorio() -> Dict[str, Any]:
    analises = carregar_analises_motor()
    decisoes = carregar_decisoes_relatorio()

    tickers = [_txt(item.get("ticker")).upper() for item in analises if _txt(item.get("ticker"))]
    setores = [_txt(item.get("setor")) for item in analises if _txt(item.get("setor"))]
    scores = [_float(item.get("score_final"), 0.0) for item in analises]

    score_medio = round(sum(scores) / len(scores), 1) if scores else 0.0
    melhores = [item for item in analises if _float(item.get("score_final"), 0.0) >= 70]
    com_preco_teto = [item for item in analises if _float(item.get("preco_teto"), 0.0) > 0]

    score_integracao = 25
    score_integracao += min(len(analises) * 5, 25)
    score_integracao += min(len(set(tickers)) * 6, 20)
    score_integracao += min(len(melhores) * 8, 20)
    score_integracao += min(len(decisoes) * 3, 10)

    if score_medio >= 70:
        score_integracao += 10
    elif score_medio >= 55:
        score_integracao += 6

    score_integracao = max(0, min(100, int(score_integracao)))

    if len(analises) == 0:
        risco = "Alto"
        decisao = "Sem análises para gerar relatório"
        proximo_passo = "Salvar pelo menos uma análise no Motor antes de gerar dossiê."
    elif len(com_preco_teto) == 0:
        risco = "Médio/Alto"
        decisao = "Análises sem preço teto confiável"
        proximo_passo = "Revisar premissas do motor e garantir preço teto positivo."
    elif score_integracao >= 75:
        risco = "Baixo"
        decisao = "Integração pronta para gerar dossiês premium"
        proximo_passo = "Gerar dossiê, revisar texto e comparar com Relatório Premium v2."
    else:
        risco = "Médio"
        decisao = "Integração funcional, mas precisa de mais análises"
        proximo_passo = "Salvar análises de mais ativos para criar relatórios melhores."

    return {
        "versao": VERSAO_INTEGRACAO_MOTOR_RELATORIO_VALORIS,
        "gerado_em": _agora_iso(),
        "score_integracao_relatorio": score_integracao,
        "analises_total": len(analises),
        "tickers_unicos": len(set(tickers)),
        "setores_unicos": len(set(setores)),
        "analises_score_alto": len(melhores),
        "analises_com_preco_teto": len(com_preco_teto),
        "decisoes_registradas": len(decisoes),
        "score_medio_motor": score_medio,
        "tickers_mais_analisados": dict(Counter(tickers).most_common(10)),
        "setores": dict(Counter(setores)),
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo_passo,
    }


def classificar_oportunidade(analise: Dict[str, str]) -> str:
    preco_atual = _float(analise.get("preco_atual"))
    preco_teto = _float(analise.get("preco_teto"))
    margem = _float(analise.get("margem_seguranca_atual"))

    if preco_atual <= 0 or preco_teto <= 0:
        return "Premissas insuficientes"

    if margem >= 20:
        return "Abaixo do preço teto com margem relevante"

    if margem >= 5:
        return "Próximo de zona racional de estudo"

    if margem >= -10:
        return "Próximo do preço teto, mas sem folga robusta"

    return "Acima do preço teto ou com baixa atratividade no preço"


def gerar_resumo_executivo(analise: Dict[str, str]) -> str:
    ticker = _txt(analise.get("ticker")).upper()
    empresa = _txt(analise.get("nome_empresa")) or ticker
    setor = _txt(analise.get("setor")) or "setor não informado"

    return (
        f"{empresa} ({ticker}) foi analisada pelo Motor Central da Valoris dentro do setor {setor}. "
        f"O preço atual informado foi {_moeda(analise.get('preco_atual'))}, enquanto o preço teto conservador calculado foi {_moeda(analise.get('preco_teto'))}. "
        f"A margem de segurança atual ficou em {_pct(analise.get('margem_seguranca_atual'))}. "
        f"A decisão do motor foi '{_txt(analise.get('decisao'))}', com score final de {_txt(analise.get('score_final'))}/100 e convicção {_txt(analise.get('nivel_conviccao'))}."
    )


def gerar_tese_preliminar(analise: Dict[str, str], tese_manual: str = "") -> str:
    if _txt(tese_manual):
        return _txt(tese_manual)

    empresa = _txt(analise.get("nome_empresa")) or _txt(analise.get("ticker")).upper()
    ticker = _txt(analise.get("ticker")).upper()
    qualidade = _float(analise.get("score_qualidade"))
    risco = _float(analise.get("score_risco"))
    valor = _float(analise.get("score_valor"))
    modelo = _txt(analise.get("modelo_preco_teto"))

    return (
        f"A tese preliminar de {empresa} ({ticker}) deve ser construída a partir de três eixos: qualidade, risco e preço. "
        f"O motor atribuiu score de qualidade {qualidade:.1f}/100, score de risco {risco:.1f}/100 e score de valor/preço {valor:.1f}/100. "
        f"O modelo conservador dominante foi '{modelo}'. "
        "Antes de qualquer conclusão forte, é necessário validar balanços, recorrência de caixa, endividamento, vantagem competitiva, governança e sensibilidade das premissas."
    )


def gerar_riscos_preliminares(analise: Dict[str, str], risco_manual: str = "") -> str:
    if _txt(risco_manual):
        return _txt(risco_manual)

    modelo = _txt(analise.get("modelo_preco_teto"))
    margem = _float(analise.get("margem_seguranca_atual"))
    decisao = _txt(analise.get("decisao"))

    riscos = [
        f"As premissas do modelo '{modelo}' podem estar otimistas ou incompletas.",
        f"A margem de segurança atual de {margem:.1f}% pode desaparecer se preço, lucro ou fluxo de caixa mudarem.",
        f"A decisão '{decisao}' não deve ser tratada como recomendação automática.",
        "Mudanças em juros, ciclo econômico, regulação, competição ou governança podem alterar totalmente a tese.",
    ]

    return "\n".join([f"- {item}" for item in riscos])


def gerar_perguntas_criticas(analise: Dict[str, str]) -> List[str]:
    ticker = _txt(analise.get("ticker")).upper() or "ativo"
    empresa = _txt(analise.get("nome_empresa")) or ticker

    return [
        f"O que precisa acontecer para a tese de {empresa} continuar válida nos próximos 12 meses?",
        "Qual premissa mais influencia o preço teto calculado?",
        "O preço atual oferece margem de segurança real ou apenas aparente?",
        "O score de qualidade é sustentado por balanços ou por premissas subjetivas?",
        "Qual risco pode transformar uma empresa boa em investimento ruim?",
        "Existe outro ativo com risco menor e oportunidade semelhante?",
        "Quando essa análise deve ser obrigatoriamente revisada?",
    ]


def gerar_plano_acompanhamento(analise: Dict[str, str], proximo_evento: str = "", data_revisao: str = "") -> List[Dict[str, str]]:
    ticker = _txt(analise.get("ticker")).upper() or "ativo"
    evento = _txt(proximo_evento) or "Próximo resultado trimestral, guidance ou fato relevante"
    revisao = _txt(data_revisao) or str(datetime.now().date() + timedelta(days=30))

    return [
        {
            "etapa": "Revisar preço",
            "pergunta": f"O preço de {ticker} ainda está abaixo do preço teto?",
            "gatilho": "Movimento relevante da cotação.",
        },
        {
            "etapa": "Revisar fundamentos",
            "pergunta": "Lucro, caixa, margem e dívida continuam sustentando o preço teto?",
            "gatilho": evento,
        },
        {
            "etapa": "Revisar risco",
            "pergunta": "O risco principal aumentou ou foi reduzido?",
            "gatilho": "Notícia setorial, regulação, concorrência ou mudança de gestão.",
        },
        {
            "etapa": "Revisar comparação",
            "pergunta": "Há alternativa melhor no mesmo setor ou em outro setor?",
            "gatilho": "Atualização da watchlist e comparador setorial.",
        },
        {
            "etapa": "Data de revisão",
            "pergunta": "Quando reavaliar esta tese?",
            "gatilho": revisao,
        },
    ]


def gerar_dossie_motor_relatorio_markdown(
    analise: Dict[str, str],
    tese_manual: str = "",
    risco_manual: str = "",
    proximo_evento: str = "",
    data_revisao: str = "",
) -> str:
    perguntas = "\n".join([f"- {item}" for item in gerar_perguntas_criticas(analise)])

    plano = "\n".join(
        [
            f"- **{item['etapa']}** — {item['pergunta']} Gatilho: {item['gatilho']}"
            for item in gerar_plano_acompanhamento(analise, proximo_evento, data_revisao)
        ]
    )

    return f"""# Dossiê Premium a partir do Motor — Valoris

Versão: {VERSAO_INTEGRACAO_MOTOR_RELATORIO_VALORIS}  
Gerado em: {_agora_iso()}

## Identificação

Empresa: {_txt(analise.get('nome_empresa')) or _txt(analise.get('ticker')).upper()}  
Ticker: {_txt(analise.get('ticker')).upper()}  
Setor: {_txt(analise.get('setor')) or 'não informado'}  
Data da análise original: {_txt(analise.get('data_hora'))}

## Resumo executivo

{gerar_resumo_executivo(analise)}

## Preço, margem e decisão

Preço atual: {_moeda(analise.get('preco_atual'))}  
Preço teto conservador: {_moeda(analise.get('preco_teto'))}  
Margem de segurança atual: {_pct(analise.get('margem_seguranca_atual'))}  
Modelo usado: {_txt(analise.get('modelo_preco_teto'))}  
Classificação da oportunidade: {classificar_oportunidade(analise)}  
Decisão do motor: {_txt(analise.get('decisao'))}  
Convicção: {_txt(analise.get('nivel_conviccao'))}

## Scores

Qualidade: {_txt(analise.get('score_qualidade'))}/100  
Risco: {_txt(analise.get('score_risco'))}/100  
Valor/preço: {_txt(analise.get('score_valor'))}/100  
Score final: {_txt(analise.get('score_final'))}/100  

## Tese preliminar

{gerar_tese_preliminar(analise, tese_manual)}

## Riscos e pontos cegos

{gerar_riscos_preliminares(analise, risco_manual)}

## Perguntas críticas

{perguntas}

## Plano de acompanhamento

{plano}

## Observação original

{_txt(analise.get('observacao')) or 'Sem observação registrada.'}

## Nota de responsabilidade

Este dossiê organiza estudo, risco e acompanhamento. Ele não é recomendação individual de compra, venda ou manutenção.
"""


def salvar_dossie_motor_relatorio(
    analise: Dict[str, str],
    tese_manual: str = "",
    risco_manual: str = "",
    proximo_evento: str = "",
    data_revisao: str = "",
) -> Path:
    CAMINHO_DOSSIE.write_text(
        gerar_dossie_motor_relatorio_markdown(
            analise=analise,
            tese_manual=tese_manual,
            risco_manual=risco_manual,
            proximo_evento=proximo_evento,
            data_revisao=data_revisao,
        ),
        encoding="utf-8",
    )
    return CAMINHO_DOSSIE


def gerar_relatorio_integracao_markdown() -> str:
    metricas = calcular_metricas_integracao_relatorio()
    decisoes = carregar_decisoes_relatorio()

    linhas_decisoes = "\n".join(
        [
            f"- **{item.get('ticker', '')}** — {item.get('acao_relatorio', '')} — {item.get('status', '')} — {item.get('data_hora', '')}"
            for item in reversed(decisoes[-20:])
        ]
    ) or "- Nenhuma decisão registrada."

    return f"""# Integração Motor + Relatório Premium — Valoris

Versão: {VERSAO_INTEGRACAO_MOTOR_RELATORIO_VALORIS}  
Gerado em: {_agora_iso()}

## Diagnóstico

Score Integração Relatório: {metricas['score_integracao_relatorio']}/100  
Análises no motor: {metricas['analises_total']}  
Tickers únicos: {metricas['tickers_unicos']}  
Setores únicos: {metricas['setores_unicos']}  
Análises com score alto: {metricas['analises_score_alto']}  
Análises com preço teto: {metricas['analises_com_preco_teto']}  
Score médio do motor: {metricas['score_medio_motor']}/100  

Risco: {metricas['risco']}  
Decisão: {metricas['decisao']}  
Próximo passo: {metricas['proximo_passo']}

## Decisões recentes

{linhas_decisoes}

## Leitura estratégica

Esta página transforma cálculo em narrativa premium. A Valoris começa a entregar não só número, mas tese, risco, perguntas críticas e plano de acompanhamento.
"""


def salvar_relatorio_integracao_markdown() -> Path:
    CAMINHO_RELATORIO.write_text(gerar_relatorio_integracao_markdown(), encoding="utf-8")
    return CAMINHO_RELATORIO


def gerar_manifesto_integracao_relatorio() -> Dict[str, Any]:
    return {
        "produto": "Valoris",
        "versao": VERSAO_INTEGRACAO_MOTOR_RELATORIO_VALORIS,
        "modulo": "integracao_motor_relatorio_valoris",
        "data_hora": _agora_iso(),
        "metricas": calcular_metricas_integracao_relatorio(),
        "principio": "transformar análise quantitativa em dossiê premium, cético e acionável",
        "fluxo": "Motor → Histórico → Motor + Relatório → Relatório Premium → Pacote Premium",
    }


def salvar_manifesto_integracao_relatorio() -> Path:
    CAMINHO_MANIFESTO.write_text(
        json.dumps(gerar_manifesto_integracao_relatorio(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return CAMINHO_MANIFESTO


def renderizar_integracao_motor_relatorio_valoris() -> None:
    st.subheader("Integração Motor + Relatório Premium")
    st.caption(
        "Transforme uma análise salva pelo Motor Central em dossiê premium com tese, risco, perguntas críticas e acompanhamento."
    )

    analises = carregar_analises_motor()
    metricas = calcular_metricas_integracao_relatorio()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Score integração", f"{metricas['score_integracao_relatorio']}/100")
    col2.metric("Análises", metricas["analises_total"])
    col3.metric("Tickers", metricas["tickers_unicos"])
    col4.metric("Score alto", metricas["analises_score_alto"])
    col5.metric("Score médio", f"{metricas['score_medio_motor']}/100")

    if metricas["score_integracao_relatorio"] >= 75:
        st.success(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    elif metricas["analises_total"] > 0:
        st.warning(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    else:
        st.info(f"{metricas['decisao']} — {metricas['proximo_passo']}")

    st.divider()

    if not analises:
        st.info("Ainda não há análises salvas. Vá até Motor Análise Ativos, rode uma análise e clique em Salvar análise.")
    else:
        opcoes = [
            f"{item.get('data_hora', '')} | {item.get('ticker', '')} | {item.get('decisao', '')} | score {item.get('score_final', '')}"
            for item in reversed(analises)
        ]

        escolha = st.selectbox("Análise base do dossiê", opcoes)
        analise = list(reversed(analises))[opcoes.index(escolha)]

        st.markdown("### Resumo da análise base")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Ticker", _txt(analise.get("ticker")).upper())
        col2.metric("Preço atual", _moeda(analise.get("preco_atual")))
        col3.metric("Preço teto", _moeda(analise.get("preco_teto")))
        col4.metric("Score final", f"{analise.get('score_final', '')}/100")

        st.markdown(f"**Decisão do motor:** {_txt(analise.get('decisao'))}")
        st.markdown(f"**Oportunidade:** {classificar_oportunidade(analise)}")

        st.divider()

        st.markdown("### Enriquecer dossiê")

        col1, col2 = st.columns(2)
        proximo_evento = col1.text_input("Próximo evento", value="Próximo resultado trimestral ou fato relevante")
        data_revisao = col2.date_input("Data de revisão", value=datetime.now().date() + timedelta(days=30))

        tese_manual = st.text_area(
            "Tese manual opcional",
            value="",
            height=120,
            placeholder="Deixe vazio para usar a tese preliminar gerada automaticamente.",
        )

        risco_manual = st.text_area(
            "Riscos manuais opcionais",
            value="",
            height=120,
            placeholder="Deixe vazio para usar os riscos preliminares gerados automaticamente.",
        )

        dossie = gerar_dossie_motor_relatorio_markdown(
            analise=analise,
            tese_manual=tese_manual,
            risco_manual=risco_manual,
            proximo_evento=proximo_evento,
            data_revisao=str(data_revisao),
        )

        st.markdown("### Prévia do dossiê")
        st.markdown(dossie)

        st.divider()

        col_a, col_b = st.columns(2)

        if col_a.button("Salvar dossiê"):
            caminho = salvar_dossie_motor_relatorio(
                analise=analise,
                tese_manual=tese_manual,
                risco_manual=risco_manual,
                proximo_evento=proximo_evento,
                data_revisao=str(data_revisao),
            )

            salvar_decisao_relatorio(
                analise=analise,
                acao_relatorio="salvar_dossie_motor",
                status="ok",
                observacao=f"Dossiê salvo em {caminho}.",
            )

            st.success(f"Dossiê salvo em {caminho}")

        if col_b.button("Registrar como revisar depois"):
            salvar_decisao_relatorio(
                analise=analise,
                acao_relatorio="revisar_depois",
                status="registrado",
                observacao="Usuário optou por não gerar dossiê definitivo agora.",
            )
            st.warning("Decisão registrada.")

        st.download_button(
            "Baixar dossiê gerado (.md)",
            data=dossie,
            file_name="DOSSIE_MOTOR_RELATORIO_VALORIS.md",
            mime="text/markdown",
        )

    st.divider()

    st.markdown("### Relatórios da integração")

    col1, col2 = st.columns(2)

    if col1.button("Salvar relatório da integração"):
        caminho = salvar_relatorio_integracao_markdown()
        st.success(f"Relatório salvo em {caminho}")

    if col2.button("Salvar manifesto da integração"):
        caminho = salvar_manifesto_integracao_relatorio()
        st.success(f"Manifesto salvo em {caminho}")

    st.download_button(
        "Baixar relatório da integração (.md)",
        data=gerar_relatorio_integracao_markdown(),
        file_name="RELATORIO_INTEGRACAO_MOTOR_RELATORIO_VALORIS.md",
        mime="text/markdown",
    )

    st.markdown("### Decisões de relatório")
    decisoes = carregar_decisoes_relatorio()

    if decisoes:
        st.dataframe(decisoes, use_container_width=True, hide_index=True)
    else:
        st.info("Ainda não há decisões de integração com relatório.")


def executar_autoteste_integracao_motor_relatorio_valoris() -> Dict[str, Any]:
    metricas = calcular_metricas_integracao_relatorio()

    return {
        "ok": True,
        "versao": VERSAO_INTEGRACAO_MOTOR_RELATORIO_VALORIS,
        "metricas": metricas,
    }
