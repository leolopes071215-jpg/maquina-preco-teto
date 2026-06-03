# explicabilidade_valoris.py

from typing import Any, Dict, List, Optional

import streamlit as st


# ============================================================
# VALORIS
# v3.8.36 — Motor de Auditoria Fundamentalista
# ------------------------------------------------------------
# Este módulo explica o cálculo, audita automaticamente o que
# é possível com os dados atuais e adiciona uma camada de
# Auditoria Fundamentalista manual/híbrida.
#
# Objetivo:
# - reduzir sensação de caixa-preta
# - separar o que a Valoris consegue auditar sozinha do que ainda precisa de dados externos
# - criar um índice simples de confiança da análise
# - iniciar auditorias de dividendos, dívida, margens, ciclo setorial e tese
# - manter o módulo leve, sem pandas e sem dependências pesadas
# ============================================================


VERSAO_EXPLICABILIDADE_VALORIS = "3.8.36"


# ============================================================
# Funções utilitárias
# ============================================================


def _safe_str(valor: Any, default: str = "") -> str:
    if valor is None:
        return default

    texto = str(valor).strip()

    return texto if texto else default


def _safe_float(valor: Any, default: float = 0.0) -> float:
    try:
        return float(valor)
    except (TypeError, ValueError):
        return default


def _formatar_moeda(valor: Any, simbolo: str = "R$") -> str:
    numero = _safe_float(valor)

    return f"{simbolo} {numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _formatar_percentual(valor: Any) -> str:
    return f"{_safe_float(valor):.2f}%"


def _normalizar_status(status: Any) -> str:
    texto = _safe_str(status).upper()

    if texto in ["COMPRA", "COMPRAR", "BUY"]:
        return "COMPRA"

    if texto in ["NEUTRO", "NEUTRA", "OBSERVAR"]:
        return "NEUTRO"

    if texto in ["AGUARDE", "AGUARDAR", "WAIT"]:
        return "AGUARDE"

    return texto if texto else "N/D"


def _normalizar_camada_visualizacao(camada: Any) -> str:
    texto = _safe_str(camada, "Intermediário").lower()

    if "leigo" in texto or "simples" in texto or "iniciante" in texto:
        return "Leigo"

    if "avanç" in texto or "avanc" in texto or "pro" in texto:
        return "Avançado"

    return "Intermediário"


def _obter_valor(
    chave: str,
    resultado_valuation: Dict[str, Any],
    entradas_valuation: Dict[str, Any],
    snapshot: Dict[str, Any],
    default: Any = 0,
) -> Any:
    if chave in snapshot:
        return snapshot.get(chave, default)

    if chave in resultado_valuation:
        return resultado_valuation.get(chave, default)

    if chave in entradas_valuation:
        return entradas_valuation.get(chave, default)

    return default


# ============================================================
# Contexto central da análise
# ============================================================


def _montar_contexto(
    resultado_valuation: Dict[str, Any],
    entradas_valuation: Optional[Dict[str, Any]],
    snapshot: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    entradas = entradas_valuation or {}
    snap = snapshot or {}

    simbolo = _safe_str(
        _obter_valor("simbolo_moeda", resultado_valuation, entradas, snap, "R$"),
        "R$",
    )

    empresa = _safe_str(
        _obter_valor("empresa", resultado_valuation, entradas, snap, "Empresa analisada"),
        "Empresa analisada",
    )

    ticker = _safe_str(
        _obter_valor("ticker", resultado_valuation, entradas, snap, "N/D"),
        "N/D",
    ).upper()

    status = _normalizar_status(
        _obter_valor("status", resultado_valuation, entradas, snap, "N/D")
    )

    preco_atual = _safe_float(
        _obter_valor("preco_atual", resultado_valuation, entradas, snap, 0)
    )

    preco_teto = _safe_float(
        _obter_valor("preco_teto", resultado_valuation, entradas, snap, 0)
    )

    preco_justo = _safe_float(
        _obter_valor("preco_justo", resultado_valuation, entradas, snap, 0)
    )

    if preco_justo <= 0:
        preco_justo = _safe_float(
            resultado_valuation.get("preco_justo_combinado", 0)
        )

    margem_seguranca = _safe_float(
        _obter_valor("margem_seguranca", resultado_valuation, entradas, snap, 0)
    )

    margem_ate_preco_teto = _safe_float(
        _obter_valor("margem_ate_preco_teto", resultado_valuation, entradas, snap, 0)
    )

    potencial_ate_preco_justo = _safe_float(
        _obter_valor("potencial_ate_preco_justo", resultado_valuation, entradas, snap, 0)
    )

    lucro_liquido_sustentavel = _safe_float(
        entradas.get("lucro_liquido_sustentavel", 0)
    )

    fluxo_caixa_livre = _safe_float(
        entradas.get("fluxo_caixa_livre", 0)
    )

    quantidade_acoes = _safe_float(
        entradas.get("quantidade_acoes", 0)
    )

    multiplo_justo_eps = _safe_float(
        entradas.get("multiplo_justo_eps", 0)
    )

    multiplo_justo_fcf = _safe_float(
        entradas.get("multiplo_justo_fcf", 0)
    )

    peso_eps = _safe_float(
        entradas.get("peso_eps", 0)
    )

    peso_fcf = _safe_float(
        entradas.get("peso_fcf", 0)
    )

    tipo_analise = _safe_str(
        _obter_valor("tipo_analise", resultado_valuation, entradas, snap, "Não informado"),
        "Não informado",
    )

    modelo_escolhido = _safe_str(
        _obter_valor("modelo_escolhido", resultado_valuation, entradas, snap, "Não informado"),
        "Não informado",
    )

    return {
        "empresa": empresa,
        "ticker": ticker,
        "status": status,
        "simbolo_moeda": simbolo,
        "preco_atual": preco_atual,
        "preco_teto": preco_teto,
        "preco_justo": preco_justo,
        "margem_seguranca": margem_seguranca,
        "margem_ate_preco_teto": margem_ate_preco_teto,
        "potencial_ate_preco_justo": potencial_ate_preco_justo,
        "lucro_liquido_sustentavel": lucro_liquido_sustentavel,
        "fluxo_caixa_livre": fluxo_caixa_livre,
        "quantidade_acoes": quantidade_acoes,
        "multiplo_justo_eps": multiplo_justo_eps,
        "multiplo_justo_fcf": multiplo_justo_fcf,
        "peso_eps": peso_eps,
        "peso_fcf": peso_fcf,
        "tipo_analise": tipo_analise,
        "modelo_escolhido": modelo_escolhido,
    }


# ============================================================
# Leitura humana e premissas
# ============================================================


def _gerar_leitura_humana(contexto: Dict[str, Any]) -> Dict[str, str]:
    status = contexto["status"]

    if status == "COMPRA":
        return {
            "titulo": "Zona de oportunidade",
            "mensagem": (
                "Pelas premissas atuais, o preço está dentro da zona conservadora do modelo. "
                "Isso não significa que a compra seja automaticamente boa. Significa apenas que, "
                "dentro das premissas usadas, existe margem de segurança suficiente para continuar a análise."
            ),
            "tom": "positivo",
        }

    if status == "NEUTRO":
        return {
            "titulo": "Zona de atenção",
            "mensagem": (
                "O ativo não parece claramente caro, mas também não parece barato o suficiente "
                "para uma entrada conservadora. A decisão mais racional pode ser observar, "
                "revisar premissas e esperar uma margem melhor."
            ),
            "tom": "neutro",
        }

    if status == "AGUARDE":
        return {
            "titulo": "Zona de paciência",
            "mensagem": (
                "Pelas premissas atuais, o preço não oferece margem de segurança suficiente. "
                "Isso não significa que a empresa seja ruim. Significa que o preço atual exige cautela."
            ),
            "tom": "cautela",
        }

    return {
        "titulo": "Resultado não classificado",
        "mensagem": (
            "A Valoris não conseguiu classificar o resultado com segurança. "
            "Revise os dados inseridos antes de interpretar a análise."
        ),
        "tom": "neutro",
    }


def _gerar_premissas_chave(contexto: Dict[str, Any]) -> List[Dict[str, str]]:
    simbolo = contexto["simbolo_moeda"]

    return [
        {
            "nome": "Preço atual",
            "valor": _formatar_moeda(contexto["preco_atual"], simbolo),
            "explicacao": "É o preço usado como ponto de comparação contra o preço-teto e o preço justo.",
        },
        {
            "nome": "Preço-teto",
            "valor": _formatar_moeda(contexto["preco_teto"], simbolo),
            "explicacao": "É o preço máximo conservador estimado após aplicar margem de segurança.",
        },
        {
            "nome": "Preço justo",
            "valor": _formatar_moeda(contexto["preco_justo"], simbolo),
            "explicacao": "É uma estimativa de valor antes do desconto de segurança.",
        },
        {
            "nome": "Margem de segurança",
            "valor": _formatar_percentual(contexto["margem_seguranca"]),
            "explicacao": "É o desconto exigido para reduzir o risco de erro nas premissas.",
        },
        {
            "nome": "Múltiplo EPS",
            "valor": str(contexto["multiplo_justo_eps"]),
            "explicacao": "Indica quanto o modelo aceita pagar pelo lucro por ação.",
        },
        {
            "nome": "Múltiplo FCF",
            "valor": str(contexto["multiplo_justo_fcf"]),
            "explicacao": "Indica quanto o modelo aceita pagar pelo fluxo de caixa livre por ação.",
        },
    ]


# ============================================================
# Auditor automático da decisão
# ============================================================


def _gerar_alertas_auditor(contexto: Dict[str, Any]) -> List[Dict[str, str]]:
    alertas: List[Dict[str, str]] = []

    status = contexto["status"]
    preco_atual = contexto["preco_atual"]
    preco_teto = contexto["preco_teto"]
    preco_justo = contexto["preco_justo"]
    margem_seguranca = contexto["margem_seguranca"]
    lucro = contexto["lucro_liquido_sustentavel"]
    fcf = contexto["fluxo_caixa_livre"]
    peso_eps = contexto["peso_eps"]
    peso_fcf = contexto["peso_fcf"]
    modelo = contexto["modelo_escolhido"]

    if preco_teto > 0 and preco_atual > preco_teto:
        alertas.append(
            {
                "nivel": "Atenção",
                "titulo": "Preço acima do teto conservador",
                "mensagem": (
                    "O preço atual está acima do preço-teto. A empresa pode continuar sendo boa, "
                    "mas o preço atual reduz a margem de segurança."
                ),
            }
        )

    if preco_justo > 0 and preco_atual > preco_justo:
        alertas.append(
            {
                "nivel": "Risco",
                "titulo": "Preço acima do valor justo estimado",
                "mensagem": (
                    "O preço atual está acima do preço justo calculado. Isso pode indicar uma situação "
                    "em que o mercado já precificou um cenário otimista."
                ),
            }
        )

    if margem_seguranca < 20:
        alertas.append(
            {
                "nivel": "Atenção",
                "titulo": "Margem de segurança baixa",
                "mensagem": (
                    "Uma margem pequena deixa pouco espaço para erro. Se as premissas estiverem otimistas, "
                    "o valuation pode parecer melhor do que realmente é."
                ),
            }
        )

    if lucro <= 0:
        alertas.append(
            {
                "nivel": "Risco",
                "titulo": "Lucro sustentável não positivo",
                "mensagem": (
                    "O lucro usado na análise está zerado ou negativo. Isso reduz a confiabilidade "
                    "de modelos baseados em lucro por ação."
                ),
            }
        )

    if fcf <= 0:
        alertas.append(
            {
                "nivel": "Risco",
                "titulo": "Fluxo de caixa livre não positivo",
                "mensagem": (
                    "O fluxo de caixa livre está zerado ou negativo. Empresas podem reportar lucro, "
                    "mas ainda assim destruir caixa. Esse ponto precisa ser revisado."
                ),
            }
        )

    if abs((peso_eps + peso_fcf) - 100) > 0.01:
        alertas.append(
            {
                "nivel": "Atenção",
                "titulo": "Pesos do modelo não somam 100%",
                "mensagem": (
                    "Os pesos de EPS e FCF deveriam somar 100%. Se isso não acontecer, "
                    "a leitura do preço justo combinado pode ficar distorcida."
                ),
            }
        )

    if "demonstra" in modelo.lower():
        alertas.append(
            {
                "nivel": "Contexto",
                "titulo": "Modo demonstração",
                "mensagem": (
                    "Esta análise usa dados fictícios. Ela serve para entender a plataforma, "
                    "não para tomar decisões reais."
                ),
            }
        )

    if status == "COMPRA":
        alertas.append(
            {
                "nivel": "Revisão",
                "titulo": "Preço bom não elimina risco de tese",
                "mensagem": (
                    "Mesmo quando o modelo indica zona de oportunidade, é necessário revisar qualidade "
                    "da empresa, recorrência dos lucros, endividamento, setor e governança."
                ),
            }
        )

    if len(alertas) == 0:
        alertas.append(
            {
                "nivel": "Revisão",
                "titulo": "Nenhum alerta crítico automático",
                "mensagem": (
                    "A análise não disparou alertas críticos básicos. Ainda assim, revise a tese, "
                    "a qualidade das premissas e possíveis eventos não recorrentes."
                ),
            }
        )

    return alertas


def _gerar_diagnostico_automatico_valoris(contexto: Dict[str, Any]) -> List[Dict[str, str]]:
    diagnosticos: List[Dict[str, str]] = []

    preco_atual = contexto["preco_atual"]
    preco_teto = contexto["preco_teto"]
    preco_justo = contexto["preco_justo"]
    margem_seguranca = contexto["margem_seguranca"]
    lucro = contexto["lucro_liquido_sustentavel"]
    fcf = contexto["fluxo_caixa_livre"]
    peso_eps = contexto["peso_eps"]
    peso_fcf = contexto["peso_fcf"]
    modelo = contexto["modelo_escolhido"]

    if preco_atual > 0:
        diagnosticos.append(
            {
                "status": "Verificado",
                "titulo": "Preço atual considerado",
                "mensagem": (
                    "A Valoris conseguiu comparar o preço atual informado com o preço-teto "
                    "e com o preço justo estimado."
                ),
            }
        )
    else:
        diagnosticos.append(
            {
                "status": "Pendente",
                "titulo": "Preço atual ausente ou inválido",
                "mensagem": (
                    "Sem preço atual confiável, a Valoris não consegue avaliar margem de segurança "
                    "contra o mercado."
                ),
            }
        )

    if preco_teto > 0:
        if preco_atual <= preco_teto:
            diagnosticos.append(
                {
                    "status": "Verificado",
                    "titulo": "Preço dentro do teto conservador",
                    "mensagem": (
                        "O preço atual está abaixo ou igual ao preço-teto calculado. Isso favorece "
                        "a leitura de margem de segurança, desde que as premissas estejam corretas."
                    ),
                }
            )
        else:
            diagnosticos.append(
                {
                    "status": "Atenção",
                    "titulo": "Preço acima do teto conservador",
                    "mensagem": (
                        "O preço atual está acima do preço-teto. A empresa pode continuar sendo boa, "
                        "mas o preço atual exige mais cautela."
                    ),
                }
            )
    else:
        diagnosticos.append(
            {
                "status": "Pendente",
                "titulo": "Preço-teto não calculado",
                "mensagem": (
                    "A Valoris não encontrou um preço-teto válido. Revise lucro, fluxo de caixa, "
                    "múltiplos, pesos e margem de segurança."
                ),
            }
        )

    if preco_justo > 0:
        if preco_atual <= preco_justo:
            diagnosticos.append(
                {
                    "status": "Verificado",
                    "titulo": "Preço abaixo do valor justo estimado",
                    "mensagem": (
                        "O preço atual está abaixo ou próximo do preço justo estimado. A análise ainda "
                        "depende da margem de segurança e da qualidade das premissas."
                    ),
                }
            )
        else:
            diagnosticos.append(
                {
                    "status": "Risco",
                    "titulo": "Preço acima do valor justo estimado",
                    "mensagem": (
                        "O preço atual está acima do valor justo estimado. Isso pode indicar que o mercado "
                        "já está precificando um cenário otimista."
                    ),
                }
            )
    else:
        diagnosticos.append(
            {
                "status": "Pendente",
                "titulo": "Preço justo não verificado",
                "mensagem": (
                    "Sem preço justo válido, a decisão perde uma referência importante de valor intrínseco."
                ),
            }
        )

    if margem_seguranca >= 30:
        diagnosticos.append(
            {
                "status": "Verificado",
                "titulo": "Margem de segurança conservadora",
                "mensagem": (
                    "A margem de segurança usada é alta o suficiente para proteger melhor contra erros "
                    "de premissa."
                ),
            }
        )
    elif margem_seguranca >= 20:
        diagnosticos.append(
            {
                "status": "Atenção",
                "titulo": "Margem de segurança moderada",
                "mensagem": (
                    "A margem de segurança é razoável, mas ainda exige cuidado com premissas otimistas."
                ),
            }
        )
    else:
        diagnosticos.append(
            {
                "status": "Risco",
                "titulo": "Margem de segurança baixa",
                "mensagem": (
                    "A margem de segurança está baixa. Isso deixa pouco espaço para erro no valuation."
                ),
            }
        )

    if lucro > 0:
        diagnosticos.append(
            {
                "status": "Verificado",
                "titulo": "Lucro sustentável informado",
                "mensagem": (
                    "A Valoris recebeu um lucro sustentável positivo. Ainda assim, ela não consegue confirmar "
                    "sozinha se esse lucro é recorrente sem dados históricos ou balanços."
                ),
            }
        )
    else:
        diagnosticos.append(
            {
                "status": "Risco",
                "titulo": "Lucro sustentável frágil",
                "mensagem": (
                    "O lucro sustentável informado está zerado ou negativo. Isso enfraquece modelos baseados "
                    "em lucro por ação."
                ),
            }
        )

    if fcf > 0:
        diagnosticos.append(
            {
                "status": "Verificado",
                "titulo": "Fluxo de caixa livre positivo",
                "mensagem": (
                    "O fluxo de caixa livre informado é positivo. Isso fortalece a leitura de qualidade "
                    "econômica, mas ainda precisa ser analisado no tempo."
                ),
            }
        )
    else:
        diagnosticos.append(
            {
                "status": "Risco",
                "titulo": "Fluxo de caixa livre frágil",
                "mensagem": (
                    "O fluxo de caixa livre está zerado ou negativo. Uma empresa pode ter lucro contábil "
                    "e ainda assim não gerar caixa suficiente."
                ),
            }
        )

    if abs((peso_eps + peso_fcf) - 100) <= 0.01:
        diagnosticos.append(
            {
                "status": "Verificado",
                "titulo": "Pesos do modelo consistentes",
                "mensagem": (
                    "Os pesos de lucro e fluxo de caixa somam 100%, então a composição do preço justo "
                    "está matematicamente coerente."
                ),
            }
        )
    else:
        diagnosticos.append(
            {
                "status": "Atenção",
                "titulo": "Pesos do modelo incoerentes",
                "mensagem": (
                    "Os pesos de lucro e fluxo de caixa não somam 100%. Isso pode distorcer o preço justo combinado."
                ),
            }
        )

    if "demonstra" in modelo.lower():
        diagnosticos.append(
            {
                "status": "Pendente",
                "titulo": "Análise em modo demonstração",
                "mensagem": (
                    "Esta análise usa dados fictícios. Ela serve para testar a plataforma, não para avaliar "
                    "uma decisão real."
                ),
            }
        )

    return diagnosticos


def _gerar_pontos_nao_verificados() -> List[Dict[str, str]]:
    return [
        {
            "ponto": "Lucro não recorrente",
            "motivo": (
                "A Valoris ainda não lê automaticamente notas explicativas, balanços trimestrais "
                "ou ajustes contábeis. Por isso, ela não consegue confirmar se o lucro veio de operação recorrente."
            ),
        },
        {
            "ponto": "Dividendos extraordinários",
            "motivo": (
                "Sem histórico automático de proventos, a Valoris ainda não identifica dividendos fora do padrão "
                "que podem inflar uma análise baseada em yield."
            ),
        },
        {
            "ponto": "Dívida e alavancagem",
            "motivo": (
                "A versão atual não compara dívida líquida, EBITDA, cobertura de juros ou vencimentos futuros."
            ),
        },
        {
            "ponto": "Margens operacionais",
            "motivo": (
                "A Valoris ainda não verifica automaticamente se margem bruta, operacional ou líquida estão "
                "em queda relevante."
            ),
        },
        {
            "ponto": "Ciclo setorial",
            "motivo": (
                "Empresas de commodities, bancos, varejo e setores cíclicos podem parecer baratas no pico do ciclo."
            ),
        },
        {
            "ponto": "Qualidade da tese",
            "motivo": (
                "A ferramenta organiza os números, mas a tese qualitativa ainda precisa ser validada pelo investidor."
            ),
        },
    ]


def _calcular_indice_confianca_valoris(contexto: Dict[str, Any]) -> Dict[str, Any]:
    diagnosticos = _gerar_diagnostico_automatico_valoris(contexto)

    score = 100

    for item in diagnosticos:
        status = item.get("status", "")

        if status == "Atenção":
            score -= 8
        elif status == "Risco":
            score -= 15
        elif status == "Pendente":
            score -= 10

    # Penalidade estrutural: ainda não temos dados automáticos de balanços, dívida, dividendos e recorrência.
    score -= 12

    score = max(0, min(100, score))

    if score >= 80:
        classificacao = "Confiança alta"
        leitura = (
            "A análise possui boa consistência com os dados disponíveis. Ainda assim, revise pontos não verificados "
            "antes de uma decisão real."
        )
    elif score >= 60:
        classificacao = "Confiança moderada"
        leitura = (
            "A análise é útil como triagem, mas ainda depende de revisão manual sobre qualidade dos dados, "
            "recorrência do lucro e riscos não capturados."
        )
    elif score >= 40:
        classificacao = "Confiança baixa"
        leitura = (
            "A análise possui sinais de fragilidade. Use como ponto de partida, não como base final de decisão."
        )
    else:
        classificacao = "Decisão frágil"
        leitura = (
            "A análise está muito exposta a falhas de premissa. Revise dados, modelo e tese antes de considerar "
            "qualquer decisão."
        )

    return {
        "score": score,
        "classificacao": classificacao,
        "leitura": leitura,
        "diagnosticos": diagnosticos,
    }


# ============================================================
# Motor de Auditoria Fundamentalista
# ============================================================


def _inferir_setor_por_ticker(ticker: str) -> str:
    ticker_limpo = _safe_str(ticker).upper()

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


def _gerar_auditoria_fundamentalista_base(contexto: Dict[str, Any]) -> List[Dict[str, str]]:
    ticker = contexto["ticker"]
    setor = _inferir_setor_por_ticker(ticker)
    lucro = contexto["lucro_liquido_sustentavel"]
    fcf = contexto["fluxo_caixa_livre"]
    preco_atual = contexto["preco_atual"]
    preco_teto = contexto["preco_teto"]
    margem_seguranca = contexto["margem_seguranca"]

    auditorias: List[Dict[str, str]] = []

    if setor != "Não identificado":
        auditorias.append(
            {
                "status": "Parcial",
                "dimensao": "Ciclo setorial",
                "leitura": (
                    f"A Valoris inferiu que o ativo pode pertencer ao setor: {setor}. "
                    "Essa inferência é aproximada e precisa ser confirmada, mas já ajuda a adaptar a leitura de risco."
                ),
            }
        )
    else:
        auditorias.append(
            {
                "status": "Pendente",
                "dimensao": "Ciclo setorial",
                "leitura": (
                    "A Valoris ainda não identificou o setor do ativo. Sem setor, a análise não consegue ajustar "
                    "riscos de ciclo, regulação, commodities ou recorrência."
                ),
            }
        )

    if lucro > 0 and fcf > 0:
        auditorias.append(
            {
                "status": "Favorável",
                "dimensao": "Lucro vs caixa",
                "leitura": (
                    "Lucro sustentável e fluxo de caixa livre foram informados como positivos. Isso aumenta a robustez "
                    "do valuation, pois o lucro contábil é parcialmente confirmado por geração de caixa."
                ),
            }
        )
    elif lucro > 0 and fcf <= 0:
        auditorias.append(
            {
                "status": "Risco",
                "dimensao": "Lucro vs caixa",
                "leitura": (
                    "Há lucro positivo, mas fluxo de caixa livre frágil. Isso pode indicar necessidade de investimento elevado, "
                    "capital de giro pesado ou baixa conversão de lucro em caixa."
                ),
            }
        )
    elif lucro <= 0:
        auditorias.append(
            {
                "status": "Risco",
                "dimensao": "Lucro recorrente",
                "leitura": (
                    "O lucro sustentável informado está zerado ou negativo. A Valoris não consegue sustentar uma leitura robusta "
                    "de valuation baseada em lucro."
                ),
            }
        )

    if preco_teto > 0 and preco_atual > preco_teto and margem_seguranca < 25:
        auditorias.append(
            {
                "status": "Atenção",
                "dimensao": "Preço e margem",
                "leitura": (
                    "O preço atual está acima do preço-teto e a margem de segurança não é alta. A decisão depende fortemente "
                    "da qualidade das premissas e da tese."
                ),
            }
        )
    elif preco_teto > 0 and preco_atual <= preco_teto:
        auditorias.append(
            {
                "status": "Favorável",
                "dimensao": "Preço e margem",
                "leitura": (
                    "O preço atual está dentro da zona conservadora pelo modelo. Isso não elimina riscos, mas melhora "
                    "a relação entre preço e margem de segurança."
                ),
            }
        )

    if setor == "Commodity":
        auditorias.append(
            {
                "status": "Atenção",
                "dimensao": "Risco de ciclo",
                "leitura": (
                    "Empresas de commodities podem parecer baratas no pico do ciclo. A Valoris recomenda usar lucro normalizado, "
                    "não apenas o lucro do melhor ano."
                ),
            }
        )

    if setor in ["Banco", "Elétrica", "Saneamento"]:
        auditorias.append(
            {
                "status": "Parcial",
                "dimensao": "Regulação e setor",
                "leitura": (
                    f"O setor {setor} costuma exigir leitura regulatória e análise específica. A versão atual ainda não aplica "
                    "um modelo setorial completo, mas já sinaliza que a régua não deve ser genérica."
                ),
            }
        )

    return auditorias


def _obter_inputs_fundamentalistas_manuais(contexto: Dict[str, Any]) -> Dict[str, str]:
    ticker = contexto["ticker"].lower().replace(".", "_").replace("-", "_")
    setor_inferido = _inferir_setor_por_ticker(contexto["ticker"])

    setores = [
        "Não sei",
        "Commodity",
        "Banco",
        "Elétrica",
        "Varejo",
        "Tecnologia",
        "Industrial",
        "Saneamento",
        "Papel e Celulose",
        "Consumo",
        "Serviços",
        "FII",
        "Outro",
    ]

    if setor_inferido in setores:
        indice_setor = setores.index(setor_inferido)
    else:
        indice_setor = 0

    with st.expander("Adicionar confirmação manual ao Auditor Fundamentalista", expanded=False):
        st.caption(
            "A Valoris audita automaticamente o que consegue. Estes campos ajudam a refinar a leitura enquanto ainda não há integração automática com APIs e balanços."
        )

        col_1, col_2 = st.columns(2)

        with col_1:
            setor = st.selectbox(
                "Setor do ativo",
                setores,
                index=indice_setor,
                key=f"aud_fund_setor_{ticker}",
            )

            lucro_recorrente = st.selectbox(
                "O lucro parece recorrente?",
                ["Não sei", "Sim", "Parcialmente", "Não"],
                key=f"aud_fund_lucro_recorrente_{ticker}",
            )

            dividendos_extraordinarios = st.selectbox(
                "Houve dividendos extraordinários recentes?",
                ["Não sei", "Não", "Sim", "Talvez"],
                key=f"aud_fund_dividendos_extra_{ticker}",
            )

        with col_2:
            divida = st.selectbox(
                "Como está a dívida/alavancagem?",
                ["Não sei", "Controlada", "Subindo moderadamente", "Subindo forte", "Crítica"],
                key=f"aud_fund_divida_{ticker}",
            )

            margens = st.selectbox(
                "Como estão as margens operacionais?",
                ["Não sei", "Melhorando", "Estáveis", "Caindo moderadamente", "Caindo forte"],
                key=f"aud_fund_margens_{ticker}",
            )

            tese = st.selectbox(
                "Você entende a tese da empresa?",
                ["Não sei", "Sim", "Parcialmente", "Não"],
                key=f"aud_fund_tese_{ticker}",
            )

        ciclo = st.selectbox(
            "O setor parece estar em ciclo favorável temporário?",
            ["Não sei", "Não", "Sim", "Talvez"],
            key=f"aud_fund_ciclo_{ticker}",
        )

    return {
        "setor": setor,
        "lucro_recorrente": lucro_recorrente,
        "dividendos_extraordinarios": dividendos_extraordinarios,
        "divida": divida,
        "margens": margens,
        "tese": tese,
        "ciclo": ciclo,
    }


def _calcular_score_fundamentalista(
    auditoria_base: List[Dict[str, str]],
    inputs: Dict[str, str],
) -> Dict[str, Any]:
    score = 70
    pontos_positivos: List[str] = []
    pontos_de_atencao: List[str] = []

    for item in auditoria_base:
        status = item.get("status", "")

        if status == "Favorável":
            score += 5
            pontos_positivos.append(item.get("dimensao", "Ponto favorável"))
        elif status == "Parcial":
            score -= 2
            pontos_de_atencao.append(item.get("dimensao", "Ponto parcial"))
        elif status == "Atenção":
            score -= 8
            pontos_de_atencao.append(item.get("dimensao", "Ponto de atenção"))
        elif status == "Risco":
            score -= 14
            pontos_de_atencao.append(item.get("dimensao", "Risco"))

    if inputs.get("lucro_recorrente") == "Sim":
        score += 8
        pontos_positivos.append("Lucro recorrente confirmado")
    elif inputs.get("lucro_recorrente") == "Parcialmente":
        score -= 4
        pontos_de_atencao.append("Lucro parcialmente recorrente")
    elif inputs.get("lucro_recorrente") == "Não":
        score -= 18
        pontos_de_atencao.append("Lucro não recorrente")

    if inputs.get("dividendos_extraordinarios") == "Sim":
        score -= 14
        pontos_de_atencao.append("Dividendos extraordinários")
    elif inputs.get("dividendos_extraordinarios") == "Talvez":
        score -= 7
        pontos_de_atencao.append("Possíveis dividendos extraordinários")
    elif inputs.get("dividendos_extraordinarios") == "Não":
        score += 4
        pontos_positivos.append("Sem dividendos extraordinários aparentes")

    if inputs.get("divida") == "Controlada":
        score += 6
        pontos_positivos.append("Dívida controlada")
    elif inputs.get("divida") == "Subindo moderadamente":
        score -= 7
        pontos_de_atencao.append("Dívida em alta")
    elif inputs.get("divida") == "Subindo forte":
        score -= 13
        pontos_de_atencao.append("Dívida subindo forte")
    elif inputs.get("divida") == "Crítica":
        score -= 20
        pontos_de_atencao.append("Alavancagem crítica")

    if inputs.get("margens") == "Melhorando":
        score += 7
        pontos_positivos.append("Margens melhorando")
    elif inputs.get("margens") == "Estáveis":
        score += 3
        pontos_positivos.append("Margens estáveis")
    elif inputs.get("margens") == "Caindo moderadamente":
        score -= 8
        pontos_de_atencao.append("Margens em queda")
    elif inputs.get("margens") == "Caindo forte":
        score -= 15
        pontos_de_atencao.append("Margens em queda forte")

    if inputs.get("ciclo") == "Sim":
        score -= 12
        pontos_de_atencao.append("Possível pico de ciclo")
    elif inputs.get("ciclo") == "Talvez":
        score -= 6
        pontos_de_atencao.append("Ciclo setorial incerto")
    elif inputs.get("ciclo") == "Não":
        score += 3
        pontos_positivos.append("Ciclo não parece inflado")

    if inputs.get("tese") == "Sim":
        score += 7
        pontos_positivos.append("Tese compreendida")
    elif inputs.get("tese") == "Parcialmente":
        score -= 5
        pontos_de_atencao.append("Tese parcialmente compreendida")
    elif inputs.get("tese") == "Não":
        score -= 18
        pontos_de_atencao.append("Tese não compreendida")

    campos_nao_sei = sum(1 for valor in inputs.values() if valor == "Não sei")
    score -= campos_nao_sei * 3

    score = max(0, min(100, score))

    if score >= 80:
        classificacao = "Fundamentos robustos"
        leitura = (
            "A análise fundamentalista parece bem sustentada pelos dados e confirmações atuais. "
            "Ainda assim, revise eventos não recorrentes e riscos setoriais antes de uma decisão real."
        )
    elif score >= 60:
        classificacao = "Fundamentos razoáveis"
        leitura = (
            "A tese tem pontos positivos, mas ainda depende de confirmação de alguns fatores fundamentais. "
            "Use como triagem qualificada, não como decisão final automática."
        )
    elif score >= 40:
        classificacao = "Fundamentos frágeis"
        leitura = (
            "Há sinais relevantes de fragilidade. O valuation pode estar tecnicamente correto, mas a qualidade "
            "da decisão ainda precisa melhorar."
        )
    else:
        classificacao = "Tese em risco"
        leitura = (
            "A análise fundamentalista está muito frágil. Antes de olhar preço-teto, revise qualidade do lucro, "
            "caixa, dívida, margens, ciclo e tese."
        )

    return {
        "score": score,
        "classificacao": classificacao,
        "leitura": leitura,
        "pontos_positivos": pontos_positivos[:5],
        "pontos_de_atencao": pontos_de_atencao[:7],
    }


def _renderizar_motor_auditoria_fundamentalista(
    contexto: Dict[str, Any],
    camada: str,
) -> None:
    st.markdown("### Motor de Auditoria Fundamentalista")

    st.caption(
        "Esta camada começa a auditar a qualidade dos fundamentos por trás do valuation. "
        "Hoje ela combina leitura automática com confirmação manual opcional."
    )

    auditoria_base = _gerar_auditoria_fundamentalista_base(contexto)

    if camada == "Leigo":
        for item in auditoria_base[:3]:
            status = item.get("status", "Parcial")
            texto = f"**{status}: {item.get('dimensao', '')}**\n\n{item.get('leitura', '')}"

            if status == "Favorável":
                st.success(texto)
            elif status == "Risco":
                st.error(texto)
            else:
                st.warning(texto)

        st.info(
            "Na leitura simples, a Valoris mostra apenas os sinais principais. "
            "Para refinar dívida, margens, dividendos e tese, use Intermediário ou Avançado."
        )
        return

    st.markdown("#### Auditoria automática inicial")

    for item in auditoria_base:
        status = item.get("status", "Parcial")
        texto = f"**{status}: {item.get('dimensao', '')}**\n\n{item.get('leitura', '')}"

        if status == "Favorável":
            st.success(texto)
        elif status == "Risco":
            st.error(texto)
        elif status == "Atenção":
            st.warning(texto)
        else:
            st.info(texto)

    inputs = _obter_inputs_fundamentalistas_manuais(contexto)
    score = _calcular_score_fundamentalista(auditoria_base, inputs)

    st.markdown("#### Score de robustez fundamentalista")

    col_1, col_2 = st.columns([1, 2])

    with col_1:
        st.metric("Robustez", f"{score['score']}/100")

    with col_2:
        if score["score"] >= 80:
            st.success(f"**{score['classificacao']}**\n\n{score['leitura']}")
        elif score["score"] >= 60:
            st.warning(f"**{score['classificacao']}**\n\n{score['leitura']}")
        elif score["score"] >= 40:
            st.warning(f"**{score['classificacao']}**\n\n{score['leitura']}")
        else:
            st.error(f"**{score['classificacao']}**\n\n{score['leitura']}")

    if score["pontos_positivos"]:
        st.markdown("#### Pontos que fortalecem a análise")
        for ponto in score["pontos_positivos"]:
            st.success(f"**{ponto}**")

    if score["pontos_de_atencao"]:
        st.markdown("#### Pontos que enfraquecem ou exigem revisão")
        for ponto in score["pontos_de_atencao"]:
            st.warning(f"**{ponto}**")


# ============================================================
# Renderizações
# ============================================================


def _renderizar_item_auditoria(status: str, titulo: str, mensagem: str) -> None:
    texto = f"**{status}: {titulo}**\n\n{mensagem}"

    if status == "Verificado":
        st.success(texto)
    elif status == "Atenção":
        st.warning(texto)
    elif status == "Risco":
        st.error(texto)
    else:
        st.info(texto)


def _renderizar_auditor_automatico_valoris(
    contexto: Dict[str, Any],
    camada: str = "Intermediário",
) -> None:
    indice = _calcular_indice_confianca_valoris(contexto)
    score = indice["score"]

    st.markdown("### Auditor automático da decisão")

    st.caption(
        "A Valoris separa o que ela já consegue verificar com os dados atuais do que ainda exige confirmação externa."
    )

    col_1, col_2 = st.columns([1, 2])

    with col_1:
        st.metric(
            "Índice de confiança",
            f"{score}/100",
        )

    with col_2:
        if score >= 80:
            st.success(f"**{indice['classificacao']}**\n\n{indice['leitura']}")
        elif score >= 60:
            st.warning(f"**{indice['classificacao']}**\n\n{indice['leitura']}")
        elif score >= 40:
            st.warning(f"**{indice['classificacao']}**\n\n{indice['leitura']}")
        else:
            st.error(f"**{indice['classificacao']}**\n\n{indice['leitura']}")

    diagnosticos = indice["diagnosticos"]

    if camada == "Leigo":
        st.markdown("#### O que a Valoris conseguiu verificar")

        for item in diagnosticos[:4]:
            _renderizar_item_auditoria(
                item.get("status", "Pendente"),
                item.get("titulo", ""),
                item.get("mensagem", ""),
            )

        st.info(
            "Esta é uma leitura simplificada. Para ver tudo que foi verificado e o que ainda está pendente, "
            "use a camada Intermediário ou Avançado."
        )
        return

    st.markdown("#### Diagnóstico automático")

    for item in diagnosticos:
        _renderizar_item_auditoria(
            item.get("status", "Pendente"),
            item.get("titulo", ""),
            item.get("mensagem", ""),
        )

    st.markdown("#### Pontos que a Valoris ainda não consegue provar sozinha")

    for item in _gerar_pontos_nao_verificados():
        with st.container(border=True):
            st.markdown(f"**{item['ponto']}**")
            st.caption(item["motivo"])


def _renderizar_bloco_alerta(alerta: Dict[str, str]) -> None:
    nivel = alerta.get("nivel", "Atenção")
    titulo = alerta.get("titulo", "")
    mensagem = alerta.get("mensagem", "")

    texto = f"**{nivel}: {titulo}**\n\n{mensagem}"

    if nivel == "Risco":
        st.error(texto)
    elif nivel == "Atenção":
        st.warning(texto)
    else:
        st.info(texto)


def _renderizar_premissas(contexto: Dict[str, Any]) -> None:
    premissas = _gerar_premissas_chave(contexto)

    for premissa in premissas:
        with st.container(border=True):
            st.markdown(f"**{premissa['nome']}**")
            st.markdown(f"### {premissa['valor']}")
            st.caption(premissa["explicacao"])


def _renderizar_checklist_confianca() -> None:
    itens = [
        "O lucro usado é recorrente ou foi inflado por evento extraordinário?",
        "O fluxo de caixa livre é positivo e sustentável?",
        "A empresa pagou dividendos extraordinários que podem não se repetir?",
        "A dívida está sob controle?",
        "A margem da empresa está estável ou em queda?",
        "O setor está em um ciclo favorável temporário?",
        "Você está comprando por tese ou por ansiedade?",
        "Você aceitaria continuar sócio se a ação caísse 30% depois da compra?",
    ]

    for item in itens:
        st.checkbox(item, value=False)


def _renderizar_leigo(contexto: Dict[str, Any]) -> None:
    leitura = _gerar_leitura_humana(contexto)

    if leitura["tom"] == "positivo":
        st.success(f"**{leitura['titulo']}**\n\n{leitura['mensagem']}")
    elif leitura["tom"] == "cautela":
        st.error(f"**{leitura['titulo']}**\n\n{leitura['mensagem']}")
    else:
        st.warning(f"**{leitura['titulo']}**\n\n{leitura['mensagem']}")

    st.markdown("#### Em linguagem simples")

    st.markdown(
        """
        A Valoris compara três coisas:

        **1. Quanto o ativo custa hoje.**  
        Esse é o preço atual.

        **2. Quanto ele parece valer pelas premissas usadas.**  
        Esse é o preço justo estimado.

        **3. Quanto faria sentido pagar com desconto de segurança.**  
        Esse é o preço-teto.

        Se o preço atual está abaixo do preço-teto, existe mais margem.  
        Se está acima, a decisão exige mais cautela.
        """
    )


def _renderizar_intermediario(contexto: Dict[str, Any]) -> None:
    st.markdown("#### Como a Valoris chegou nesse resultado?")

    st.markdown(
        """
        O cálculo atual combina duas leituras de valor:

        **1. Lucro por ação (EPS/LPA)**  
        O lucro sustentável é dividido pela quantidade de ações. Depois, aplicamos um múltiplo justo.

        **2. Fluxo de caixa livre por ação (FCF/FCL)**  
        O fluxo de caixa livre é dividido pela quantidade de ações. Depois, aplicamos um múltiplo justo.

        A Valoris combina os dois valores usando os pesos definidos na análise.  
        Depois aplica a margem de segurança para chegar ao preço-teto.
        """
    )

    st.markdown("#### Premissas que mais influenciam o resultado")

    _renderizar_premissas(contexto)


def _renderizar_avancado(contexto: Dict[str, Any]) -> None:
    simbolo = contexto["simbolo_moeda"]

    st.markdown("#### Premissas técnicas usadas")

    col_1, col_2 = st.columns(2)

    with col_1:
        st.metric(
            "Lucro sustentável",
            _formatar_moeda(contexto["lucro_liquido_sustentavel"], simbolo),
        )
        st.metric(
            "Múltiplo EPS",
            str(contexto["multiplo_justo_eps"]),
        )
        st.metric(
            "Peso EPS",
            _formatar_percentual(contexto["peso_eps"]),
        )

    with col_2:
        st.metric(
            "Fluxo de caixa livre",
            _formatar_moeda(contexto["fluxo_caixa_livre"], simbolo),
        )
        st.metric(
            "Múltiplo FCF",
            str(contexto["multiplo_justo_fcf"]),
        )
        st.metric(
            "Peso FCF",
            _formatar_percentual(contexto["peso_fcf"]),
        )

    st.info(
        "Esta camada é para revisão técnica. O objetivo não é criar uma falsa precisão, "
        "mas deixar claro quais premissas sustentam o resultado."
    )


def renderizar_explicabilidade_valoris(
    resultado_valuation: Dict[str, Any],
    entradas_valuation: Optional[Dict[str, Any]] = None,
    snapshot: Optional[Dict[str, Any]] = None,
    camada_visualizacao: str = "Intermediário",
) -> None:
    """
    Renderiza a camada de explicabilidade e auditoria da Valoris.
    """
    contexto = _montar_contexto(
        resultado_valuation=resultado_valuation,
        entradas_valuation=entradas_valuation,
        snapshot=snapshot,
    )

    camada = _normalizar_camada_visualizacao(camada_visualizacao)

    st.markdown("## Auditor Valoris")

    st.caption(
        f"v{VERSAO_EXPLICABILIDADE_VALORIS} — A Valoris não apenas calcula: ela ajuda a revisar a qualidade da decisão."
    )

    with st.container(border=True):
        st.markdown(
            f"""
            ### Como interpretar {contexto['empresa']} ({contexto['ticker']})

            Antes de olhar apenas para o número final, revise a lógica por trás da decisão.

            Um valuation pode parecer preciso, mas continuar frágil se estiver baseado em lucro não recorrente,
            dividendo extraordinário, múltiplo otimista, margem de segurança baixa ou tese mal compreendida.
            """
        )

    if camada == "Leigo":
        _renderizar_leigo(contexto)

        st.divider()

        _renderizar_auditor_automatico_valoris(contexto, camada)

        st.divider()

        _renderizar_motor_auditoria_fundamentalista(contexto, camada)

        st.divider()

        st.markdown("### Alertas principais")

        alertas = _gerar_alertas_auditor(contexto)

        for alerta in alertas[:3]:
            _renderizar_bloco_alerta(alerta)

        st.info(
            "Esta é a leitura simplificada. Para abrir premissas, múltiplos e revisão técnica, "
            "troque a visualização para Intermediário ou Avançado."
        )

    elif camada == "Intermediário":
        _renderizar_leigo(contexto)

        st.divider()

        _renderizar_auditor_automatico_valoris(contexto, camada)

        st.divider()

        _renderizar_motor_auditoria_fundamentalista(contexto, camada)

        st.divider()

        _renderizar_intermediario(contexto)

        st.divider()

        st.markdown("### O que pode estar errado nessa decisão?")

        alertas = _gerar_alertas_auditor(contexto)

        for alerta in alertas:
            _renderizar_bloco_alerta(alerta)

        st.divider()

        st.markdown("### Regra de ouro da Valoris")

        st.info(
            "Empresa boa não é automaticamente investimento bom. "
            "O preço pago, a qualidade das premissas e a margem de segurança definem a qualidade da decisão."
        )

    else:
        _renderizar_leigo(contexto)

        st.divider()

        _renderizar_auditor_automatico_valoris(contexto, camada)

        st.divider()

        _renderizar_motor_auditoria_fundamentalista(contexto, camada)

        st.divider()

        _renderizar_intermediario(contexto)

        st.divider()

        _renderizar_avancado(contexto)

        st.divider()

        st.markdown("### O que pode estar errado nessa decisão?")

        alertas = _gerar_alertas_auditor(contexto)

        for alerta in alertas:
            _renderizar_bloco_alerta(alerta)

        st.divider()

        st.markdown("### Checklist de confirmação do investidor")

        st.caption(
            "A Valoris audita automaticamente o que consegue. Os itens abaixo são pontos que ainda exigem confirmação humana ou dados externos."
        )

        _renderizar_checklist_confianca()

        st.divider()

        st.markdown("### Regra de ouro da Valoris")

        st.info(
            "Empresa boa não é automaticamente investimento bom. "
            "O preço pago, a qualidade das premissas e a margem de segurança definem a qualidade da decisão."
        )


def executar_autoteste_explicabilidade_valoris() -> List[Dict[str, str]]:
    resultado = {
        "empresa": "Empresa Teste",
        "ticker": "TST3",
        "status": "NEUTRO",
        "preco_atual": 82,
        "preco_teto": 70,
        "preco_justo": 95,
        "margem_ate_preco_teto": -14.63,
        "potencial_ate_preco_justo": 15.85,
        "margem_seguranca": 25,
        "simbolo_moeda": "R$",
    }

    entradas = {
        "lucro_liquido_sustentavel": 1000000,
        "fluxo_caixa_livre": 900000,
        "quantidade_acoes": 100000,
        "multiplo_justo_eps": 10,
        "multiplo_justo_fcf": 12,
        "peso_eps": 50,
        "peso_fcf": 50,
        "modelo_escolhido": "Teste",
    }

    contexto = _montar_contexto(resultado, entradas, None)
    alertas = _gerar_alertas_auditor(contexto)
    premissas = _gerar_premissas_chave(contexto)
    diagnosticos = _gerar_diagnostico_automatico_valoris(contexto)
    indice = _calcular_indice_confianca_valoris(contexto)
    auditoria_fundamentalista = _gerar_auditoria_fundamentalista_base(contexto)
    score_fundamentalista = _calcular_score_fundamentalista(
        auditoria_base=auditoria_fundamentalista,
        inputs={
            "setor": "Industrial",
            "lucro_recorrente": "Sim",
            "dividendos_extraordinarios": "Não",
            "divida": "Controlada",
            "margens": "Estáveis",
            "tese": "Sim",
            "ciclo": "Não",
        },
    )

    return [
        {
            "teste": "contexto_montado",
            "status": "OK" if contexto["ticker"] == "TST3" else "FALHA",
            "detalhe": contexto["ticker"],
        },
        {
            "teste": "alertas_gerados",
            "status": "OK" if len(alertas) > 0 else "FALHA",
            "detalhe": str(len(alertas)),
        },
        {
            "teste": "premissas_geradas",
            "status": "OK" if len(premissas) >= 3 else "FALHA",
            "detalhe": str(len(premissas)),
        },
        {
            "teste": "diagnosticos_automaticos",
            "status": "OK" if len(diagnosticos) >= 5 else "FALHA",
            "detalhe": str(len(diagnosticos)),
        },
        {
            "teste": "indice_confianca",
            "status": "OK" if 0 <= indice["score"] <= 100 else "FALHA",
            "detalhe": f"{indice['score']}/100",
        },
        {
            "teste": "auditoria_fundamentalista",
            "status": "OK" if len(auditoria_fundamentalista) >= 2 else "FALHA",
            "detalhe": str(len(auditoria_fundamentalista)),
        },
        {
            "teste": "score_fundamentalista",
            "status": "OK" if 0 <= score_fundamentalista["score"] <= 100 else "FALHA",
            "detalhe": f"{score_fundamentalista['score']}/100",
        },
    ]
