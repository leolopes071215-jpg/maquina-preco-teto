# relatorio_multiativos.py

import streamlit as st
from typing import Any, Dict, List, Optional

from relatorio import gerar_relatorio_markdown, gerar_nome_arquivo_relatorio


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v1.20 — Relatório Premium Multiativos
# ------------------------------------------------------------
# Este módulo consolida os principais resultados da plataforma:
# valuation, decisão, painel executivo, convicção, checklist,
# Ações Brasil, FIIs e Renda Fixa.
# Não é recomendação de investimento.
# É um relatório educacional de análise multiativos.
# ============================================================


def _get_dict_session(key: str) -> Dict[str, Any]:
    valor = st.session_state.get(key)

    if isinstance(valor, dict):
        return valor

    return {}


def _fmt_texto(valor: Any, padrao: str = "N/D") -> str:
    if valor is None or valor == "":
        return padrao

    return str(valor)


def _fmt_score(valor: Any) -> str:
    if valor is None or valor == "":
        return "N/D"

    try:
        return f"{int(round(float(valor)))}/100"
    except (TypeError, ValueError):
        return "N/D"


def _fmt_percentual(valor: Any) -> str:
    if valor is None or valor == "":
        return "N/D"

    try:
        return f"{float(valor):.2f}%"
    except (TypeError, ValueError):
        return "N/D"


def _fmt_moeda(valor: Any, simbolo_moeda: str = "R$") -> str:
    if valor is None or valor == "":
        return "N/D"

    try:
        numero = float(valor)
        return f"{simbolo_moeda} {numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return "N/D"


def _lista_markdown(itens: Optional[List[Any]], vazio: str) -> str:
    if not itens:
        return f"- {vazio}"

    linhas = []

    for item in itens:
        if item is not None and str(item).strip() != "":
            linhas.append(f"- {item}")

    if len(linhas) == 0:
        return f"- {vazio}"

    return "\n".join(linhas)


def _tabela_notas(notas: Dict[str, Any]) -> str:
    if not isinstance(notas, dict) or len(notas) == 0:
        return "- Notas não registradas."

    linhas = ["| Critério | Nota |", "|---|---|"]

    for chave, valor in notas.items():
        nome = str(chave).replace("_", " ").title()
        linhas.append(f"| {nome} | {_fmt_texto(valor)} |")

    return "\n".join(linhas)


def _gerar_secao_painel_executivo(simbolo_moeda: str = "R$") -> str:
    painel = _get_dict_session("resultado_painel_multiativos")
    valuation = _get_dict_session("resultado_valuation")

    if not painel:
        return """
---

# Painel Executivo Multiativos

O Painel Executivo ainda não foi preenchido nesta sessão.  
Para consolidar a análise, abra a aba **Painel Executivo** antes de baixar o relatório multiativos.
"""

    return f"""
---

# Painel Executivo Multiativos

## Síntese do painel

| Indicador | Resultado |
|---|---|
| Empresa | {_fmt_texto(painel.get("empresa", valuation.get("empresa")))} |
| Ticker | {_fmt_texto(painel.get("ticker", valuation.get("ticker")))} |
| Score integrado | {_fmt_score(painel.get("score_integrado"))} |
| Classificação integrada | {_fmt_texto(painel.get("classificacao_integrada"))} |
| Status do valuation | {_fmt_texto(valuation.get("status_valuation", valuation.get("status")))} |
| Preço atual | {_fmt_moeda(valuation.get("preco_atual"), simbolo_moeda)} |
| Preço-teto | {_fmt_moeda(valuation.get("preco_teto"), simbolo_moeda)} |
| Preço justo estimado | {_fmt_moeda(valuation.get("preco_justo", valuation.get("preco_justo_combinado")), simbolo_moeda)} |

## Leitura integrada

{_fmt_texto(painel.get("leitura_integrada"))}

## Scores consolidados

| Módulo | Resultado |
|---|---|
| Resumo da Decisão | {_fmt_score(painel.get("score_decisao"))} |
| Convicção da Tese | {_fmt_score(painel.get("score_conviccao"))} |
| Checklist de Erros | {_fmt_score(painel.get("score_checklist"))} |
| Risco Ações Brasil | {_fmt_score(painel.get("risco_brasil"))} |
| Risco FIIs | {_fmt_score(painel.get("risco_fii"))} |
| Risco Renda Fixa | {_fmt_score(painel.get("risco_renda_fixa"))} |
"""


def _gerar_secao_resumo_decisao() -> str:
    resumo = _get_dict_session("resultado_resumo_decisao")

    if not resumo:
        return """
---

# Resumo da Decisão

O Resumo da Decisão ainda não foi gerado nesta sessão.  
Abra a aba **Resumo da Decisão** para consolidar valuation, tese, cenários e alertas.
"""

    alertas = resumo.get("alertas", [])

    return f"""
---

# Resumo Executivo da Decisão

## Síntese final

| Indicador | Resultado |
|---|---|
| Empresa | {_fmt_texto(resumo.get("empresa"))} |
| Score final | {_fmt_score(resumo.get("score_final"))} |
| Classificação da decisão | {_fmt_texto(resumo.get("classificacao_decisao"))} |
| Status do valuation | {_fmt_texto(resumo.get("status_valuation"))} |
| Score de convicção | {_fmt_score(resumo.get("score_conviccao"))} |
| Classificação da tese | {_fmt_texto(resumo.get("classificacao_tese"))} |
| Risco de depender de otimismo | {_fmt_texto(resumo.get("risco_otimista"))} |

## Leitura dos cenários

| Cenário | Status |
|---|---|
| Conservador | {_fmt_texto(resumo.get("cenario_conservador"))} |
| Base | {_fmt_texto(resumo.get("cenario_base"))} |
| Otimista | {_fmt_texto(resumo.get("cenario_otimista"))} |

**Interpretação:**  
{_fmt_texto(resumo.get("leitura_cenarios"))}

## Alertas qualitativos

{_lista_markdown(alertas, "Nenhum alerta qualitativo relevante foi identificado no momento.")}

## Ação educacional sugerida

**{_fmt_texto(resumo.get("classificacao_decisao"))}**

{_fmt_texto(resumo.get("acao_educacional"))}
"""


def _gerar_secao_conviccao() -> str:
    conviccao = _get_dict_session("resultado_conviccao_tese")

    if not conviccao:
        return """
---

# Convicção da Tese

A Convicção da Tese ainda não foi preenchida nesta sessão.  
Abra a aba **Convicção da Tese** para avaliar previsibilidade, caixa, endividamento, vantagem competitiva, gestão e riscos.
"""

    alertas = conviccao.get("alertas", [])
    matriz = conviccao.get("matriz_qualitativa", {})

    return f"""
---

# Convicção da Tese

## Síntese

| Indicador | Resultado |
|---|---|
| Empresa | {_fmt_texto(conviccao.get("empresa"))} |
| Ticker | {_fmt_texto(conviccao.get("ticker"))} |
| Score de convicção | {_fmt_score(conviccao.get("score_conviccao"))} |
| Classificação da tese | {_fmt_texto(conviccao.get("classificacao_tese"))} |
| Status do valuation | {_fmt_texto(conviccao.get("status_valuation"))} |

## Leitura executiva

{_fmt_texto(conviccao.get("leitura_executiva"))}

## Alertas da tese

{_lista_markdown(alertas, "Nenhum alerta crítico foi registrado na convicção da tese.")}

## Matriz qualitativa

{_tabela_notas(matriz)}
"""


def _gerar_secao_checklist() -> str:
    checklist = _get_dict_session("resultado_checklist_erros")

    if not checklist:
        return """
---

# Checklist de Erros

O Checklist de Erros ainda não foi preenchido nesta sessão.  
Abra a aba **Checklist de Erros** para auditar vieses, fragilidades e riscos da análise.
"""

    erros = checklist.get("erros_marcados", [])
    perguntas = checklist.get("perguntas_criticas", [])

    return f"""
---

# Checklist de Erros

## Síntese

| Indicador | Resultado |
|---|---|
| Classe de ativo | {_fmt_texto(checklist.get("classe_ativo"))} |
| Score de risco | {_fmt_score(checklist.get("score_risco"))} |
| Classificação do risco | {_fmt_texto(checklist.get("classificacao_risco"))} |

## Erros marcados

{_lista_markdown(erros, "Nenhum erro foi marcado no checklist.")}

## Perguntas críticas

{_lista_markdown(perguntas, "Nenhuma pergunta crítica foi registrada.")}

## Ação educacional sugerida

{_fmt_texto(checklist.get("acao_educacional"))}
"""


def _gerar_secao_acoes_brasil() -> str:
    brasil = _get_dict_session("resultado_acoes_brasil")

    if not brasil:
        return """
---

# Ações Brasil

O módulo de Ações Brasil ainda não foi preenchido nesta sessão.  
Abra a aba **Ações Brasil** para avaliar governança, dívida, juros, regulação, dividendos e riscos específicos da B3.
"""

    alertas = brasil.get("alertas_brasil", [])
    notas = brasil.get("notas", {})

    return f"""
---

# Ações Brasil

## Síntese

| Indicador | Resultado |
|---|---|
| Empresa | {_fmt_texto(brasil.get("empresa"))} |
| Ticker | {_fmt_texto(brasil.get("ticker"))} |
| Score de risco Brasil | {_fmt_score(brasil.get("score_risco_brasil"))} |
| Classificação | {_fmt_texto(brasil.get("classificacao_risco_brasil"))} |

## Leitura educacional

{_fmt_texto(brasil.get("leitura_risco_brasil"))}

## Alertas Brasil

{_lista_markdown(alertas, "Nenhum alerta crítico foi registrado no módulo de Ações Brasil.")}

## Notas do diagnóstico

{_tabela_notas(notas)}
"""


def _gerar_secao_fiis() -> str:
    fiis = _get_dict_session("resultado_fiis")

    if not fiis:
        return """
---

# Fundos Imobiliários

O módulo de FIIs ainda não foi preenchido nesta sessão.  
Abra a aba **FIIs** para avaliar renda recorrente, P/VP, vacância, contratos, gestão, liquidez, emissões e sensibilidade aos juros.
"""

    alertas = fiis.get("alertas_fii", [])
    notas = fiis.get("notas", {})

    return f"""
---

# Fundos Imobiliários

## Síntese

| Indicador | Resultado |
|---|---|
| Empresa/FII | {_fmt_texto(fiis.get("empresa"))} |
| Ticker | {_fmt_texto(fiis.get("ticker"))} |
| Dividend Yield estimado | {_fmt_percentual(fiis.get("dividend_yield"))} |
| P/VP | {_fmt_texto(fiis.get("p_vp"))} |
| Score de risco FII | {_fmt_score(fiis.get("score_risco_fii"))} |
| Classificação | {_fmt_texto(fiis.get("classificacao_risco_fii"))} |

## Leitura educacional

{_fmt_texto(fiis.get("leitura_fii"))}

## Alertas de FIIs

{_lista_markdown(alertas, "Nenhum alerta crítico foi registrado no módulo de FIIs.")}

## Notas do diagnóstico

{_tabela_notas(notas)}
"""


def _gerar_secao_renda_fixa() -> str:
    renda_fixa = _get_dict_session("resultado_renda_fixa")

    if not renda_fixa:
        return """
---

# Renda Fixa

O módulo de Renda Fixa ainda não foi preenchido nesta sessão.  
Abra a aba **Renda Fixa** para avaliar emissor, prazo, liquidez, indexador, FGC, imposto, marcação a mercado e adequação.
"""

    alertas = renda_fixa.get("alertas_renda_fixa", [])
    notas = renda_fixa.get("notas", {})

    return f"""
---

# Renda Fixa

## Síntese

| Indicador | Resultado |
|---|---|
| Tipo de título | {_fmt_texto(renda_fixa.get("tipo_titulo"))} |
| Indexador | {_fmt_texto(renda_fixa.get("indexador"))} |
| Tem FGC? | {_fmt_texto(renda_fixa.get("possui_fgc"))} |
| Taxa anual informada | {_fmt_percentual(renda_fixa.get("taxa_anual"))} |
| Prazo | {_fmt_texto(renda_fixa.get("prazo_meses"))} meses |
| Score de risco | {_fmt_score(renda_fixa.get("score_risco_renda_fixa"))} |
| Classificação | {_fmt_texto(renda_fixa.get("classificacao_renda_fixa"))} |

## Leitura educacional

{_fmt_texto(renda_fixa.get("leitura_renda_fixa"))}

## Alertas de Renda Fixa

{_lista_markdown(alertas, "Nenhum alerta crítico foi registrado no módulo de Renda Fixa.")}

## Notas do diagnóstico

{_tabela_notas(notas)}
"""


def _gerar_secao_proximos_passos() -> str:
    painel = _get_dict_session("resultado_painel_multiativos")
    resumo = _get_dict_session("resultado_resumo_decisao")
    conviccao = _get_dict_session("resultado_conviccao_tese")
    checklist = _get_dict_session("resultado_checklist_erros")
    brasil = _get_dict_session("resultado_acoes_brasil")
    fiis = _get_dict_session("resultado_fiis")
    renda_fixa = _get_dict_session("resultado_renda_fixa")

    passos = []

    if not painel:
        passos.append("Abrir o Painel Executivo para consolidar os módulos preenchidos.")

    if not resumo:
        passos.append("Gerar o Resumo da Decisão para consolidar valuation, tese, cenários e ação educacional.")

    if not conviccao:
        passos.append("Preencher a Convicção da Tese para avaliar qualidade do negócio.")

    if not checklist:
        passos.append("Rodar o Checklist de Erros para identificar fragilidades no raciocínio.")

    if not brasil:
        passos.append("Se a análise for de empresa brasileira, preencher o módulo Ações Brasil.")

    if not fiis:
        passos.append("Se a análise for de FII, preencher o módulo FIIs.")

    if not renda_fixa:
        passos.append("Se a análise for de renda fixa, preencher o módulo Renda Fixa.")

    if len(passos) == 0:
        passos.append("Revisar os dados, comparar com outras oportunidades e acompanhar a tese ao longo do tempo.")

    return f"""
---

# Próximos Passos Educacionais

{_lista_markdown(passos, "Nenhum próximo passo registrado.")}
"""


def _gerar_aviso_educacional() -> str:
    return """
---

# Aviso Educacional

Este relatório não representa recomendação de compra, venda ou manutenção de ativos.

A Máquina de Preço-Teto é uma plataforma educacional para organizar premissas, melhorar raciocínio, comparar cenários, reduzir erros e desenvolver disciplina de análise.

Toda decisão real deve considerar:

- objetivos pessoais;
- horizonte de tempo;
- tolerância a risco;
- liquidez;
- diversificação;
- tributação;
- qualidade dos dados;
- responsabilidade individual;
- orientação profissional quando necessário.

O objetivo deste relatório é ajudar o usuário a pensar melhor, não decidir por ele.
"""


def gerar_relatorio_multiativos_markdown(
    entradas: Any,
    resultado: Dict[str, Any],
    dados_empresa: Dict[str, Any],
    simbolo_moeda: str,
    formatar_moeda,
    formatar_percentual,
    formatar_numero,
) -> str:
    """
    Gera o relatório premium multiativos completo em Markdown.
    """
    relatorio_base = gerar_relatorio_markdown(
        entradas=entradas,
        resultado=resultado,
        dados_empresa=dados_empresa,
        simbolo_moeda=simbolo_moeda,
        formatar_moeda=formatar_moeda,
        formatar_percentual=formatar_percentual,
        formatar_numero=formatar_numero,
    )

    relatorio_multiativos = ""

    relatorio_multiativos += _gerar_secao_painel_executivo(simbolo_moeda=simbolo_moeda)
    relatorio_multiativos += _gerar_secao_resumo_decisao()
    relatorio_multiativos += _gerar_secao_conviccao()
    relatorio_multiativos += _gerar_secao_checklist()
    relatorio_multiativos += _gerar_secao_acoes_brasil()
    relatorio_multiativos += _gerar_secao_fiis()
    relatorio_multiativos += _gerar_secao_renda_fixa()
    relatorio_multiativos += _gerar_secao_proximos_passos()
    relatorio_multiativos += _gerar_aviso_educacional()

    return relatorio_base + relatorio_multiativos


def gerar_nome_arquivo_relatorio_multiativos(
    empresa: str,
    ticker: str,
) -> str:
    """
    Gera nome do arquivo do relatório multiativos.
    """
    nome_base = gerar_nome_arquivo_relatorio(
        empresa=empresa,
        ticker=ticker,
    )

    return nome_base.replace(".md", "_multiativos_premium.md")


def renderizar_download_relatorio_multiativos(
    entradas: Any,
    resultado: Dict[str, Any],
    dados_empresa: Dict[str, Any],
    simbolo_moeda: str,
    formatar_moeda,
    formatar_percentual,
    formatar_numero,
) -> None:
    """
    Renderiza o bloco de download do Relatório Premium Multiativos.
    """
    st.markdown("### Relatório Premium Multiativos")

    st.caption(
        "Baixe um relatório único consolidando valuation, decisão, painel executivo, convicção, checklist, Ações Brasil, FIIs e Renda Fixa."
    )

    relatorio = gerar_relatorio_multiativos_markdown(
        entradas=entradas,
        resultado=resultado,
        dados_empresa=dados_empresa,
        simbolo_moeda=simbolo_moeda,
        formatar_moeda=formatar_moeda,
        formatar_percentual=formatar_percentual,
        formatar_numero=formatar_numero,
    )

    nome_arquivo = gerar_nome_arquivo_relatorio_multiativos(
        empresa=entradas.empresa,
        ticker=entradas.ticker,
    )

    st.download_button(
        label="Baixar relatório premium multiativos (.md)",
        data=relatorio,
        file_name=nome_arquivo,
        mime="text/markdown",
        key="download_relatorio_premium_multiativos",
    )