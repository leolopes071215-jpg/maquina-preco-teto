from datetime import datetime
from typing import Any, Dict, List

from valuation import EntradasValuation


# ============================================================
# VALORIS
# v3.8.37 — Relatório Valoris Premium
# ------------------------------------------------------------
# Este arquivo gera relatórios em Markdown para a plataforma.
#
# Mantém o relatório executivo original e adiciona uma nova
# entrega premium em linguagem humana:
# - leitura clara da decisão
# - diagnóstico do Auditor Valoris
# - pontos que podem distorcer a análise
# - conclusão educacional premium
# ============================================================


def limpar_nome_arquivo(texto: str) -> str:
    texto_limpo = texto.lower().strip()
    caracteres_invalidos = [" ", "/", "\\", ":", "*", "?", '"', "<", ">", "|", "'", "."]

    for caractere in caracteres_invalidos:
        texto_limpo = texto_limpo.replace(caractere, "-")

    while "--" in texto_limpo:
        texto_limpo = texto_limpo.replace("--", "-")

    return texto_limpo.strip("-")


def gerar_nome_arquivo_relatorio(empresa: str, ticker: str) -> str:
    data_atual = datetime.now().strftime("%Y-%m-%d")
    empresa_limpa = limpar_nome_arquivo(empresa)
    ticker_limpo = limpar_nome_arquivo(ticker)

    return f"relatorio-valuation-{ticker_limpo}-{empresa_limpa}-{data_atual}.md"


def gerar_nome_arquivo_relatorio_valoris_premium(empresa: str, ticker: str) -> str:
    data_atual = datetime.now().strftime("%Y-%m-%d")
    empresa_limpa = limpar_nome_arquivo(empresa)
    ticker_limpo = limpar_nome_arquivo(ticker)

    return f"relatorio-valoris-premium-{ticker_limpo}-{empresa_limpa}-{data_atual}.md"


def _safe_float(valor: Any, default: float = 0.0) -> float:
    try:
        return float(valor)
    except (TypeError, ValueError):
        return default


def _safe_str(valor: Any, default: str = "N/D") -> str:
    if valor is None or valor == "":
        return default

    return str(valor)


def _normalizar_status(status: Any) -> str:
    texto = _safe_str(status, "").upper()

    if texto in ["COMPRA", "COMPRAR", "BUY"]:
        return "COMPRA"

    if texto in ["NEUTRO", "NEUTRA", "OBSERVAR"]:
        return "NEUTRO"

    if texto in ["AGUARDE", "AGUARDAR", "WAIT"]:
        return "AGUARDE"

    return texto if texto else "N/D"


def _obter_leitura_humana_status(status: Any) -> Dict[str, str]:
    status_normalizado = _normalizar_status(status)

    if status_normalizado == "COMPRA":
        return {
            "zona": "Zona de oportunidade",
            "resumo": (
                "Pelas premissas atuais, o ativo está dentro da zona conservadora do modelo. "
                "Isso não significa compra automática. Significa que existe margem suficiente para continuar a análise."
            ),
            "acao": (
                "Revisar tese, qualidade dos dados, riscos fundamentais e tamanho de posição antes de qualquer decisão."
            ),
        }

    if status_normalizado == "NEUTRO":
        return {
            "zona": "Zona de atenção",
            "resumo": (
                "O ativo não parece claramente caro, mas também não oferece margem forte o bastante "
                "para uma entrada conservadora. A decisão mais racional pode ser acompanhar e esperar melhor assimetria."
            ),
            "acao": (
                "Adicionar à watchlist, testar premissas conservadoras e revisar se a tese continua forte."
            ),
        }

    if status_normalizado == "AGUARDE":
        return {
            "zona": "Zona de paciência",
            "resumo": (
                "Pelas premissas atuais, o preço não oferece margem de segurança suficiente. "
                "A empresa pode ser boa, mas o preço atual exige cautela."
            ),
            "acao": (
                "Evitar compra por impulso, definir preço de alerta e reavaliar após novos dados ou queda no preço."
            ),
        }

    return {
        "zona": "Resultado não classificado",
        "resumo": (
            "A Valoris não conseguiu classificar o resultado com segurança. "
            "Revise dados e premissas antes de interpretar a análise."
        ),
        "acao": "Revisar informações inseridas antes de tomar qualquer conclusão.",
    }


def _inferir_setor_por_ticker(ticker: str) -> str:
    ticker_limpo = _safe_str(ticker, "").upper()

    mapa_aproximado = {
        "PETR": "Commodity",
        "VALE": "Commodity",
        "CSNA": "Commodity",
        "GGBR": "Commodity",
        "USIM": "Commodity",
        "TAEE": "Elétrica",
        "TRPL": "Elétrica",
        "EGIE": "Elétrica",
        "CPFE": "Elétrica",
        "CMIG": "Elétrica",
        "ITUB": "Banco",
        "BBDC": "Banco",
        "BBAS": "Banco",
        "SANB": "Banco",
        "BPAC": "Banco",
        "WEGE": "Industrial",
        "ABEV": "Consumo",
        "MGLU": "Varejo",
        "VIIA": "Varejo",
        "LREN": "Varejo",
        "RENT": "Serviços",
        "SBSP": "Saneamento",
        "SAPR": "Saneamento",
        "KLBN": "Papel e Celulose",
        "SUZB": "Papel e Celulose",
    }

    for prefixo, setor in mapa_aproximado.items():
        if ticker_limpo.startswith(prefixo):
            return setor

    return "Não identificado"


def _gerar_diagnostico_auditor_relatorio(
    entradas: EntradasValuation,
    resultado: dict,
) -> List[Dict[str, str]]:
    diagnosticos: List[Dict[str, str]] = []

    status = _normalizar_status(resultado.get("status"))
    preco_atual = _safe_float(entradas.preco_atual)
    preco_teto = _safe_float(resultado.get("preco_teto"))
    preco_justo = _safe_float(resultado.get("preco_justo_combinado"))
    margem_seguranca = _safe_float(entradas.margem_seguranca)
    margem_ate_teto = _safe_float(resultado.get("margem_ate_preco_teto"))
    lucro = _safe_float(entradas.lucro_liquido_sustentavel)
    fcf = _safe_float(entradas.fluxo_caixa_livre)
    peso_eps = _safe_float(entradas.peso_eps)
    peso_fcf = _safe_float(entradas.peso_fcf)
    setor = _inferir_setor_por_ticker(entradas.ticker)

    if preco_teto > 0 and preco_atual <= preco_teto:
        diagnosticos.append(
            {
                "nivel": "Favorável",
                "titulo": "Preço dentro do teto conservador",
                "leitura": (
                    "O preço atual está abaixo ou igual ao preço-teto estimado. "
                    "Isso favorece a margem de segurança, desde que as premissas estejam corretas."
                ),
            }
        )
    elif preco_teto > 0 and preco_atual > preco_teto:
        diagnosticos.append(
            {
                "nivel": "Atenção",
                "titulo": "Preço acima do teto conservador",
                "leitura": (
                    "O preço atual está acima do preço-teto. A empresa pode continuar sendo boa, "
                    "mas o preço atual reduz a proteção contra erro de premissa."
                ),
            }
        )

    if preco_justo > 0 and preco_atual > preco_justo:
        diagnosticos.append(
            {
                "nivel": "Risco",
                "titulo": "Preço acima do valor justo estimado",
                "leitura": (
                    "O preço atual está acima do valor justo calculado. Isso pode indicar que o mercado já "
                    "precifica um cenário otimista."
                ),
            }
        )
    elif preco_justo > 0:
        diagnosticos.append(
            {
                "nivel": "Verificado",
                "titulo": "Preço justo usado como referência",
                "leitura": (
                    "A Valoris calculou uma referência de valor justo antes de aplicar a margem de segurança."
                ),
            }
        )

    if margem_seguranca >= 30:
        diagnosticos.append(
            {
                "nivel": "Favorável",
                "titulo": "Margem de segurança conservadora",
                "leitura": (
                    "A margem de segurança usada é robusta. Isso reduz o risco de uma decisão baseada em excesso de otimismo."
                ),
            }
        )
    elif margem_seguranca >= 20:
        diagnosticos.append(
            {
                "nivel": "Atenção",
                "titulo": "Margem de segurança moderada",
                "leitura": (
                    "A margem usada é razoável, mas ainda exige cuidado com qualidade do lucro, fluxo de caixa e múltiplos escolhidos."
                ),
            }
        )
    else:
        diagnosticos.append(
            {
                "nivel": "Risco",
                "titulo": "Margem de segurança baixa",
                "leitura": (
                    "A margem de segurança está baixa. O valuation fica mais sensível a qualquer erro nas premissas."
                ),
            }
        )

    if lucro > 0 and fcf > 0:
        diagnosticos.append(
            {
                "nivel": "Favorável",
                "titulo": "Lucro e caixa positivos",
                "leitura": (
                    "Lucro sustentável e fluxo de caixa livre foram informados como positivos. Isso fortalece a análise, "
                    "pois o lucro contábil tem apoio parcial em geração de caixa."
                ),
            }
        )
    elif lucro > 0 and fcf <= 0:
        diagnosticos.append(
            {
                "nivel": "Risco",
                "titulo": "Lucro positivo com caixa frágil",
                "leitura": (
                    "A empresa apresenta lucro positivo, mas fluxo de caixa livre frágil. Isso pode indicar baixa conversão "
                    "de lucro em caixa, investimentos elevados ou capital de giro pressionado."
                ),
            }
        )
    elif lucro <= 0:
        diagnosticos.append(
            {
                "nivel": "Risco",
                "titulo": "Lucro sustentável frágil",
                "leitura": (
                    "O lucro sustentável informado está zerado ou negativo. Modelos baseados em lucro perdem confiabilidade nesse cenário."
                ),
            }
        )

    if abs((peso_eps + peso_fcf) - 100) <= 0.01:
        diagnosticos.append(
            {
                "nivel": "Verificado",
                "titulo": "Pesos do modelo consistentes",
                "leitura": "Os pesos de EPS e FCF somam 100%, então a composição do preço justo está coerente.",
            }
        )
    else:
        diagnosticos.append(
            {
                "nivel": "Atenção",
                "titulo": "Pesos do modelo incoerentes",
                "leitura": (
                    "Os pesos de EPS e FCF não somam 100%. Isso pode distorcer a leitura do preço justo combinado."
                ),
            }
        )

    if setor != "Não identificado":
        diagnosticos.append(
            {
                "nivel": "Parcial",
                "titulo": f"Setor inferido: {setor}",
                "leitura": (
                    "A Valoris inferiu o setor de forma aproximada pelo ticker. Essa leitura ajuda a pensar riscos setoriais, "
                    "mas ainda precisa ser confirmada por dados mais completos."
                ),
            }
        )

    if setor == "Commodity":
        diagnosticos.append(
            {
                "nivel": "Atenção",
                "titulo": "Risco de ciclo em commodity",
                "leitura": (
                    "Empresas de commodities podem parecer baratas no pico do ciclo. A análise deve usar lucro normalizado, "
                    "não apenas o lucro de um ano excepcional."
                ),
            }
        )

    if status == "COMPRA" and margem_ate_teto > 0:
        diagnosticos.append(
            {
                "nivel": "Revisão",
                "titulo": "Preço bom não elimina risco de tese",
                "leitura": (
                    "Mesmo em zona de oportunidade, a decisão precisa revisar tese, dívida, margens, recorrência do lucro e governança."
                ),
            }
        )

    return diagnosticos


def _gerar_pontos_nao_verificados_relatorio() -> List[Dict[str, str]]:
    return [
        {
            "ponto": "Dividendos extraordinários",
            "leitura": (
                "A versão atual ainda não verifica histórico automático de proventos. Dividendos fora do padrão podem inflar "
                "uma análise baseada em yield."
            ),
        },
        {
            "ponto": "Dívida e alavancagem",
            "leitura": (
                "A versão atual ainda não compara dívida líquida, EBITDA, cobertura de juros ou cronograma de vencimentos."
            ),
        },
        {
            "ponto": "Margens operacionais",
            "leitura": (
                "A Valoris ainda não verifica automaticamente tendência de margem bruta, operacional ou líquida."
            ),
        },
        {
            "ponto": "Lucro não recorrente",
            "leitura": (
                "A ferramenta ainda não lê notas explicativas e balanços para separar lucro recorrente de eventos extraordinários."
            ),
        },
        {
            "ponto": "Ciclo setorial",
            "leitura": (
                "Setores cíclicos exigem cautela porque o lucro atual pode estar acima da média histórica."
            ),
        },
        {
            "ponto": "Qualidade da tese",
            "leitura": (
                "A Valoris organiza os números, mas a tese qualitativa ainda precisa ser validada pelo investidor."
            ),
        },
    ]


def _calcular_score_relatorio(diagnosticos: List[Dict[str, str]]) -> Dict[str, Any]:
    score = 100

    for item in diagnosticos:
        nivel = item.get("nivel", "")

        if nivel == "Favorável":
            score += 2
        elif nivel == "Verificado":
            score += 1
        elif nivel == "Parcial":
            score -= 4
        elif nivel == "Revisão":
            score -= 5
        elif nivel == "Atenção":
            score -= 8
        elif nivel == "Risco":
            score -= 15

    # Penalidade honesta: ainda não há dados automáticos completos de balanços e proventos.
    score -= 12

    score = max(0, min(100, score))

    if score >= 80:
        classificacao = "Alta confiança educacional"
        leitura = (
            "A análise apresenta boa consistência com os dados disponíveis, mas ainda exige revisão de itens não verificados."
        )
    elif score >= 60:
        classificacao = "Confiança moderada"
        leitura = (
            "A análise é útil como triagem, mas ainda depende de confirmação sobre qualidade dos dados e fundamentos."
        )
    elif score >= 40:
        classificacao = "Confiança baixa"
        leitura = (
            "A análise possui fragilidades relevantes. Use como ponto de partida, não como conclusão final."
        )
    else:
        classificacao = "Decisão frágil"
        leitura = (
            "A análise está muito sensível a erros de premissa. Revise dados, tese e fundamentos antes de qualquer decisão."
        )

    return {
        "score": score,
        "classificacao": classificacao,
        "leitura": leitura,
    }


def _linhas_diagnostico_markdown(diagnosticos: List[Dict[str, str]]) -> str:
    linhas = []

    for item in diagnosticos:
        linhas.append(
            f"- **{item.get('nivel', 'N/D')} — {item.get('titulo', 'N/D')}:** {item.get('leitura', 'N/D')}"
        )

    return "\n".join(linhas)


def _linhas_pontos_nao_verificados_markdown(pontos: List[Dict[str, str]]) -> str:
    linhas = []

    for item in pontos:
        linhas.append(
            f"- **{item.get('ponto', 'N/D')}:** {item.get('leitura', 'N/D')}"
        )

    return "\n".join(linhas)


def gerar_relatorio_markdown(
    entradas: EntradasValuation,
    resultado: dict,
    dados_empresa: dict,
    simbolo_moeda: str,
    formatar_moeda,
    formatar_percentual,
    formatar_numero,
) -> str:
    data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")

    tese = dados_empresa.get("tese", "Não informado.")
    riscos = dados_empresa.get("riscos", "Não informado.")
    fundamentos = dados_empresa.get("fundamentos", "Não informado.")
    perfil_empresa = dados_empresa.get("perfil_empresa", "Não informado.")
    data_referencia = dados_empresa.get("data_referencia", "Não informado.")
    fonte_premissas = dados_empresa.get("fonte_premissas", "Não informado.")
    moeda = dados_empresa.get("moeda", "Não informado.")

    relatorio = f"""# Relatório Executivo de Valuation

## 1. Identificação da análise

**Empresa:** {entradas.empresa}  
**Ticker:** {entradas.ticker}  
**Data de geração:** {data_atual}  
**Perfil da empresa:** {perfil_empresa}  
**Moeda/unidade:** {moeda}  
**Data de referência dos dados:** {data_referencia}  
**Fonte das premissas:** {fonte_premissas}  

---

## 2. Resumo executivo

**Preço atual:** {formatar_moeda(entradas.preco_atual, simbolo_moeda)}  
**Preço justo estimado:** {formatar_moeda(resultado["preco_justo_combinado"], simbolo_moeda)}  
**Preço-teto com margem de segurança:** {formatar_moeda(resultado["preco_teto"], simbolo_moeda)}  
**Status educacional:** {resultado["status"]}  

**Margem até o preço-teto:** {formatar_percentual(resultado["margem_ate_preco_teto"])}  
**Potencial até o preço justo:** {formatar_percentual(resultado["potencial_ate_preco_justo"])}  

### Leitura automática

{resultado["explicacao_status"]}

---

## 3. Indicadores calculados

| Indicador | Valor |
|---|---:|
| EPS normalizado | {formatar_moeda(resultado["eps_normalizado"], simbolo_moeda)} |
| FCF por ação | {formatar_moeda(resultado["fcf_por_acao"], simbolo_moeda)} |
| Preço justo por EPS | {formatar_moeda(resultado["preco_justo_eps"], simbolo_moeda)} |
| Preço justo por FCF | {formatar_moeda(resultado["preco_justo_fcf"], simbolo_moeda)} |
| Preço justo combinado | {formatar_moeda(resultado["preco_justo_combinado"], simbolo_moeda)} |
| Preço-teto | {formatar_moeda(resultado["preco_teto"], simbolo_moeda)} |

---

## 4. Premissas utilizadas

| Premissa | Valor |
|---|---:|
| Lucro líquido sustentável | {formatar_moeda(entradas.lucro_liquido_sustentavel, simbolo_moeda)} |
| Fluxo de caixa livre | {formatar_moeda(entradas.fluxo_caixa_livre, simbolo_moeda)} |
| Quantidade de ações | {formatar_numero(entradas.quantidade_acoes)} |
| Preço atual | {formatar_moeda(entradas.preco_atual, simbolo_moeda)} |
| Múltiplo justo EPS | {entradas.multiplo_justo_eps:.2f}x |
| Múltiplo justo FCF | {entradas.multiplo_justo_fcf:.2f}x |
| Peso EPS | {entradas.peso_eps:.0f}% |
| Peso FCF | {entradas.peso_fcf:.0f}% |
| Margem de segurança | {entradas.margem_seguranca:.0f}% |

---

## 5. Tese qualitativa

{tese}

---

## 6. Principais riscos

{riscos}

---

## 7. Fundamentos observados

{fundamentos}

---

## 8. Interpretação educacional

Este relatório não deve ser lido como recomendação de compra, venda ou manutenção de investimentos.

O objetivo é organizar premissas de valuation e transformar os números em uma análise mais clara.

Um preço-teto calculado não é uma verdade absoluta. Ele depende diretamente de:

- qualidade do lucro usado;
- recorrência do fluxo de caixa livre;
- múltiplos escolhidos;
- margem de segurança;
- preço atual;
- riscos da empresa;
- qualidade da tese;
- cenário macroeconômico;
- taxa de juros;
- qualidade da gestão;
- estrutura de capital.

A melhor análise não é a mais otimista. É a que continua fazendo sentido mesmo quando algumas premissas estão erradas.

---

## 9. Aviso importante

Esta ferramenta é apenas educacional.

Ela não representa recomendação de investimento, consultoria financeira, análise certificada, oferta de compra, oferta de venda ou sugestão individualizada.

Antes de tomar qualquer decisão financeira, estude a empresa com profundidade e considere consultar profissionais habilitados.
"""

    return relatorio


def gerar_relatorio_valoris_premium_markdown(
    entradas: EntradasValuation,
    resultado: dict,
    dados_empresa: dict,
    simbolo_moeda: str,
    formatar_moeda,
    formatar_percentual,
    formatar_numero,
) -> str:
    data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")

    tese = dados_empresa.get("tese", "Não informado.")
    riscos = dados_empresa.get("riscos", "Não informado.")
    fundamentos = dados_empresa.get("fundamentos", "Não informado.")
    perfil_empresa = dados_empresa.get("perfil_empresa", "Não informado.")
    data_referencia = dados_empresa.get("data_referencia", "Não informado.")
    fonte_premissas = dados_empresa.get("fonte_premissas", "Não informado.")
    moeda = dados_empresa.get("moeda", "Não informado.")

    leitura = _obter_leitura_humana_status(resultado.get("status"))
    diagnosticos = _gerar_diagnostico_auditor_relatorio(entradas, resultado)
    pontos_nao_verificados = _gerar_pontos_nao_verificados_relatorio()
    score = _calcular_score_relatorio(diagnosticos)
    setor = _inferir_setor_por_ticker(entradas.ticker)

    relatorio = f"""# Relatório Valoris Premium

**Plataforma:** Valoris  
**Tipo:** Valuation + Auditoria de Decisão  
**Gerado em:** {data_atual}  

---

## 1. Leitura principal

**Empresa:** {entradas.empresa}  
**Ticker:** {entradas.ticker}  
**Perfil:** {perfil_empresa}  
**Moeda/unidade:** {moeda}  
**Setor inferido:** {setor}  
**Data de referência:** {data_referencia}  
**Fonte das premissas:** {fonte_premissas}  

### {leitura["zona"]}

{leitura["resumo"]}

**Próxima ação educacional:** {leitura["acao"]}

---

## 2. Painel de decisão

| Indicador | Valor |
|---|---:|
| Preço atual | {formatar_moeda(entradas.preco_atual, simbolo_moeda)} |
| Preço justo estimado | {formatar_moeda(resultado["preco_justo_combinado"], simbolo_moeda)} |
| Preço-teto conservador | {formatar_moeda(resultado["preco_teto"], simbolo_moeda)} |
| Margem até o preço-teto | {formatar_percentual(resultado["margem_ate_preco_teto"])} |
| Potencial até o preço justo | {formatar_percentual(resultado["potencial_ate_preco_justo"])} |
| Margem de segurança usada | {entradas.margem_seguranca:.0f}% |
| Status técnico original | {resultado["status"]} |

---

## 3. Índice de confiança da análise

**Score Valoris:** {score["score"]}/100  
**Classificação:** {score["classificacao"]}  

{score["leitura"]}

Esse score não mede se a ação é boa ou ruim. Ele mede a robustez educacional da análise com os dados disponíveis.

---

## 4. Auditor Valoris — Diagnóstico automático

{_linhas_diagnostico_markdown(diagnosticos)}

---

## 5. O que ainda pode distorcer este valuation

{_linhas_pontos_nao_verificados_markdown(pontos_nao_verificados)}

---

## 6. Como a Valoris chegou ao número

A versão atual combina duas leituras de valor:

1. **Lucro por ação (EPS/LPA):** lucro líquido sustentável dividido pela quantidade de ações, multiplicado por um múltiplo justo.
2. **Fluxo de caixa livre por ação (FCF/FCL):** fluxo de caixa livre dividido pela quantidade de ações, multiplicado por um múltiplo justo.

Depois, a Valoris combina os dois valores usando os pesos definidos pelo usuário e aplica uma margem de segurança para chegar ao preço-teto.

| Premissa | Valor |
|---|---:|
| Lucro líquido sustentável | {formatar_moeda(entradas.lucro_liquido_sustentavel, simbolo_moeda)} |
| Fluxo de caixa livre | {formatar_moeda(entradas.fluxo_caixa_livre, simbolo_moeda)} |
| Quantidade de ações | {formatar_numero(entradas.quantidade_acoes)} |
| Múltiplo justo EPS | {entradas.multiplo_justo_eps:.2f}x |
| Múltiplo justo FCF | {entradas.multiplo_justo_fcf:.2f}x |
| Peso EPS | {entradas.peso_eps:.0f}% |
| Peso FCF | {entradas.peso_fcf:.0f}% |

---

## 7. Tese qualitativa registrada

{tese}

---

## 8. Principais riscos registrados

{riscos}

---

## 9. Fundamentos observados

{fundamentos}

---

## 10. Conclusão educacional Valoris

A Valoris não deve ser usada para responder apenas "compra ou não compra".

A pergunta mais madura é:

**"Essa decisão é bem fundamentada o suficiente para eu continuar analisando?"**

Com os dados atuais, a análise indica:

- zona de decisão: **{leitura["zona"]}**;
- confiança educacional: **{score["classificacao"]}**;
- score de robustez: **{score["score"]}/100**;
- principais riscos: qualidade das premissas, dados ainda não verificados e validação da tese.

Uma boa empresa pode ser um mau investimento se for comprada cara demais.  
Um preço aparentemente barato pode ser uma armadilha se lucro, caixa, dívida ou ciclo estiverem distorcidos.

---

## 11. Aviso importante

Este relatório é educacional.

Ele não representa recomendação de compra, venda ou manutenção de investimentos.  
Ele não substitui análise própria, acompanhamento dos resultados, leitura de documentos oficiais, diversificação, planejamento financeiro ou consulta a profissionais habilitados.

A Valoris organiza o raciocínio.  
A responsabilidade pela decisão continua sendo do investidor.
"""

    return relatorio
