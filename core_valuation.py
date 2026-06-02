# core_valuation.py

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v3.8 — Core Engine de Valuation
# ------------------------------------------------------------
# Este arquivo contém o núcleo puro de cálculo do produto.
#
# Objetivo:
# - separar a lógica financeira da interface Streamlit
# - preparar o motor para futura API em FastAPI
# - padronizar entradas, saídas, validações e contratos
# - permitir testes automatizados
# - reduzir dependência da interface atual
# ============================================================


VERSAO_CORE_VALUATION = "3.8"


@dataclass
class EntradaCoreValuation:
    empresa: str
    ticker: str
    lucro_liquido_sustentavel: float
    fluxo_caixa_livre: float
    quantidade_acoes: float
    multiplo_justo_eps: float
    multiplo_justo_fcf: float
    peso_eps: float
    peso_fcf: float
    margem_seguranca: float
    preco_atual: float
    moeda: str = "R$"


@dataclass
class ResultadoCoreValuation:
    empresa: str
    ticker: str
    eps_normalizado: float
    fcf_por_acao: float
    preco_justo_eps: float
    preco_justo_fcf: float
    preco_justo_combinado: float
    preco_teto: float
    preco_atual: float
    margem_seguranca: float
    margem_ate_preco_teto: float
    potencial_ate_preco_justo: float
    status: str
    explicacao_status: str
    peso_eps_normalizado: float
    peso_fcf_normalizado: float
    moeda: str
    versao_core: str
    data_calculo: str


def _safe_float(valor: Any, nome_campo: str) -> float:
    try:
        return float(valor)
    except (TypeError, ValueError):
        raise ValueError(f"O campo '{nome_campo}' precisa ser numérico.")


def _validar_texto_obrigatorio(valor: str, nome_campo: str) -> None:
    if str(valor).strip() == "":
        raise ValueError(f"O campo '{nome_campo}' é obrigatório.")


def _validar_maior_que_zero(valor: float, nome_campo: str) -> None:
    if valor <= 0:
        raise ValueError(f"O campo '{nome_campo}' precisa ser maior que zero.")


def _validar_maior_ou_igual_zero(valor: float, nome_campo: str) -> None:
    if valor < 0:
        raise ValueError(f"O campo '{nome_campo}' precisa ser maior ou igual a zero.")


def _validar_intervalo(
    valor: float,
    nome_campo: str,
    minimo: float,
    maximo: float,
) -> None:
    if valor < minimo or valor > maximo:
        raise ValueError(
            f"O campo '{nome_campo}' precisa estar entre {minimo} e {maximo}."
        )


def validar_entrada_core(entrada: EntradaCoreValuation) -> None:
    """
    Valida as premissas mínimas necessárias para o cálculo.
    """
    _validar_texto_obrigatorio(entrada.empresa, "empresa")
    _validar_texto_obrigatorio(entrada.ticker, "ticker")

    _validar_maior_que_zero(entrada.quantidade_acoes, "quantidade_acoes")
    _validar_maior_que_zero(entrada.preco_atual, "preco_atual")

    _validar_maior_ou_igual_zero(
        entrada.multiplo_justo_eps,
        "multiplo_justo_eps",
    )
    _validar_maior_ou_igual_zero(
        entrada.multiplo_justo_fcf,
        "multiplo_justo_fcf",
    )

    _validar_maior_ou_igual_zero(entrada.peso_eps, "peso_eps")
    _validar_maior_ou_igual_zero(entrada.peso_fcf, "peso_fcf")

    _validar_intervalo(
        entrada.margem_seguranca,
        "margem_seguranca",
        0,
        90,
    )

    soma_pesos = entrada.peso_eps + entrada.peso_fcf

    if soma_pesos <= 0:
        raise ValueError("A soma de peso_eps e peso_fcf precisa ser maior que zero.")


def normalizar_pesos(peso_eps: float, peso_fcf: float) -> Dict[str, float]:
    soma = peso_eps + peso_fcf

    if soma <= 0:
        raise ValueError("A soma dos pesos precisa ser maior que zero.")

    return {
        "peso_eps_normalizado": peso_eps / soma,
        "peso_fcf_normalizado": peso_fcf / soma,
    }


def calcular_eps_normalizado(
    lucro_liquido_sustentavel: float,
    quantidade_acoes: float,
) -> float:
    _validar_maior_que_zero(quantidade_acoes, "quantidade_acoes")
    return lucro_liquido_sustentavel / quantidade_acoes


def calcular_fcf_por_acao(
    fluxo_caixa_livre: float,
    quantidade_acoes: float,
) -> float:
    _validar_maior_que_zero(quantidade_acoes, "quantidade_acoes")
    return fluxo_caixa_livre / quantidade_acoes


def calcular_preco_justo_eps(
    eps_normalizado: float,
    multiplo_justo_eps: float,
) -> float:
    return eps_normalizado * multiplo_justo_eps


def calcular_preco_justo_fcf(
    fcf_por_acao: float,
    multiplo_justo_fcf: float,
) -> float:
    return fcf_por_acao * multiplo_justo_fcf


def calcular_preco_justo_combinado(
    preco_justo_eps: float,
    preco_justo_fcf: float,
    peso_eps_normalizado: float,
    peso_fcf_normalizado: float,
) -> float:
    return (
        preco_justo_eps * peso_eps_normalizado
        + preco_justo_fcf * peso_fcf_normalizado
    )


def aplicar_margem_seguranca(
    preco_justo_combinado: float,
    margem_seguranca: float,
) -> float:
    fator_margem = 1 - (margem_seguranca / 100)
    return preco_justo_combinado * fator_margem


def calcular_margem_ate_preco_teto(
    preco_atual: float,
    preco_teto: float,
) -> float:
    _validar_maior_que_zero(preco_atual, "preco_atual")
    return ((preco_teto - preco_atual) / preco_atual) * 100


def calcular_potencial_ate_preco_justo(
    preco_atual: float,
    preco_justo_combinado: float,
) -> float:
    _validar_maior_que_zero(preco_atual, "preco_atual")
    return ((preco_justo_combinado - preco_atual) / preco_atual) * 100


def classificar_status_valuation(
    preco_atual: float,
    preco_teto: float,
    preco_justo_combinado: float,
) -> str:
    if preco_atual <= preco_teto:
        return "COMPRA"

    if preco_atual <= preco_justo_combinado:
        return "NEUTRO"

    return "AGUARDE"


def formatar_moeda_core(valor: float, moeda: str = "R$") -> str:
    return f"{moeda} {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def formatar_percentual_core(valor: float) -> str:
    return f"{valor:.2f}%"


def gerar_explicacao_status(
    status: str,
    preco_atual: float,
    preco_teto: float,
    preco_justo_combinado: float,
    moeda: str,
) -> str:
    if status == "COMPRA":
        return (
            f"O preço atual de {formatar_moeda_core(preco_atual, moeda)} está abaixo ou igual "
            f"ao preço-teto de {formatar_moeda_core(preco_teto, moeda)}. Pelas premissas "
            f"informadas, o ativo está dentro da zona conservadora do modelo."
        )

    if status == "NEUTRO":
        return (
            f"O preço atual de {formatar_moeda_core(preco_atual, moeda)} está acima do "
            f"preço-teto de {formatar_moeda_core(preco_teto, moeda)}, mas ainda abaixo ou "
            f"próximo do preço justo estimado de {formatar_moeda_core(preco_justo_combinado, moeda)}. "
            f"O modelo indica cautela."
        )

    return (
        f"O preço atual de {formatar_moeda_core(preco_atual, moeda)} está acima do preço justo "
        f"estimado de {formatar_moeda_core(preco_justo_combinado, moeda)}. Pelas premissas "
        f"informadas, o modelo indica aguardar."
    )


def calcular_core_valuation(entrada: EntradaCoreValuation) -> ResultadoCoreValuation:
    """
    Executa o cálculo central de valuation sem depender de Streamlit.

    Esta função é candidata direta para ser usada futuramente por:
    - API FastAPI
    - testes automatizados
    - frontend Next.js
    - relatórios
    - banco de dados
    """
    entrada_convertida = EntradaCoreValuation(
        empresa=str(entrada.empresa).strip(),
        ticker=str(entrada.ticker).upper().strip(),
        lucro_liquido_sustentavel=_safe_float(
            entrada.lucro_liquido_sustentavel,
            "lucro_liquido_sustentavel",
        ),
        fluxo_caixa_livre=_safe_float(
            entrada.fluxo_caixa_livre,
            "fluxo_caixa_livre",
        ),
        quantidade_acoes=_safe_float(
            entrada.quantidade_acoes,
            "quantidade_acoes",
        ),
        multiplo_justo_eps=_safe_float(
            entrada.multiplo_justo_eps,
            "multiplo_justo_eps",
        ),
        multiplo_justo_fcf=_safe_float(
            entrada.multiplo_justo_fcf,
            "multiplo_justo_fcf",
        ),
        peso_eps=_safe_float(entrada.peso_eps, "peso_eps"),
        peso_fcf=_safe_float(entrada.peso_fcf, "peso_fcf"),
        margem_seguranca=_safe_float(
            entrada.margem_seguranca,
            "margem_seguranca",
        ),
        preco_atual=_safe_float(entrada.preco_atual, "preco_atual"),
        moeda=str(entrada.moeda).strip() or "R$",
    )

    validar_entrada_core(entrada_convertida)

    pesos = normalizar_pesos(
        peso_eps=entrada_convertida.peso_eps,
        peso_fcf=entrada_convertida.peso_fcf,
    )

    eps_normalizado = calcular_eps_normalizado(
        lucro_liquido_sustentavel=entrada_convertida.lucro_liquido_sustentavel,
        quantidade_acoes=entrada_convertida.quantidade_acoes,
    )

    fcf_por_acao = calcular_fcf_por_acao(
        fluxo_caixa_livre=entrada_convertida.fluxo_caixa_livre,
        quantidade_acoes=entrada_convertida.quantidade_acoes,
    )

    preco_justo_eps = calcular_preco_justo_eps(
        eps_normalizado=eps_normalizado,
        multiplo_justo_eps=entrada_convertida.multiplo_justo_eps,
    )

    preco_justo_fcf = calcular_preco_justo_fcf(
        fcf_por_acao=fcf_por_acao,
        multiplo_justo_fcf=entrada_convertida.multiplo_justo_fcf,
    )

    preco_justo_combinado = calcular_preco_justo_combinado(
        preco_justo_eps=preco_justo_eps,
        preco_justo_fcf=preco_justo_fcf,
        peso_eps_normalizado=pesos["peso_eps_normalizado"],
        peso_fcf_normalizado=pesos["peso_fcf_normalizado"],
    )

    preco_teto = aplicar_margem_seguranca(
        preco_justo_combinado=preco_justo_combinado,
        margem_seguranca=entrada_convertida.margem_seguranca,
    )

    margem_ate_preco_teto = calcular_margem_ate_preco_teto(
        preco_atual=entrada_convertida.preco_atual,
        preco_teto=preco_teto,
    )

    potencial_ate_preco_justo = calcular_potencial_ate_preco_justo(
        preco_atual=entrada_convertida.preco_atual,
        preco_justo_combinado=preco_justo_combinado,
    )

    status = classificar_status_valuation(
        preco_atual=entrada_convertida.preco_atual,
        preco_teto=preco_teto,
        preco_justo_combinado=preco_justo_combinado,
    )

    explicacao_status = gerar_explicacao_status(
        status=status,
        preco_atual=entrada_convertida.preco_atual,
        preco_teto=preco_teto,
        preco_justo_combinado=preco_justo_combinado,
        moeda=entrada_convertida.moeda,
    )

    return ResultadoCoreValuation(
        empresa=entrada_convertida.empresa,
        ticker=entrada_convertida.ticker,
        eps_normalizado=eps_normalizado,
        fcf_por_acao=fcf_por_acao,
        preco_justo_eps=preco_justo_eps,
        preco_justo_fcf=preco_justo_fcf,
        preco_justo_combinado=preco_justo_combinado,
        preco_teto=preco_teto,
        preco_atual=entrada_convertida.preco_atual,
        margem_seguranca=entrada_convertida.margem_seguranca,
        margem_ate_preco_teto=margem_ate_preco_teto,
        potencial_ate_preco_justo=potencial_ate_preco_justo,
        status=status,
        explicacao_status=explicacao_status,
        peso_eps_normalizado=pesos["peso_eps_normalizado"],
        peso_fcf_normalizado=pesos["peso_fcf_normalizado"],
        moeda=entrada_convertida.moeda,
        versao_core=VERSAO_CORE_VALUATION,
        data_calculo=datetime.now().isoformat(timespec="seconds"),
    )


def resultado_core_para_dict(resultado: ResultadoCoreValuation) -> Dict[str, Any]:
    return asdict(resultado)


def entrada_core_para_dict(entrada: EntradaCoreValuation) -> Dict[str, Any]:
    return asdict(entrada)


def criar_entrada_core_por_payload(payload: Dict[str, Any]) -> EntradaCoreValuation:
    """
    Converte um payload estilo API em EntradaCoreValuation.
    """
    return EntradaCoreValuation(
        empresa=payload.get("empresa", ""),
        ticker=payload.get("ticker", ""),
        lucro_liquido_sustentavel=payload.get("lucro_liquido_sustentavel", 0),
        fluxo_caixa_livre=payload.get("fluxo_caixa_livre", 0),
        quantidade_acoes=payload.get("quantidade_acoes", 0),
        multiplo_justo_eps=payload.get("multiplo_justo_eps", 0),
        multiplo_justo_fcf=payload.get("multiplo_justo_fcf", 0),
        peso_eps=payload.get("peso_eps", 50),
        peso_fcf=payload.get("peso_fcf", 50),
        margem_seguranca=payload.get("margem_seguranca", 30),
        preco_atual=payload.get("preco_atual", 0),
        moeda=payload.get("moeda", "R$"),
    )


def calcular_core_valuation_por_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Interface pronta para futura API.

    Entrada:
    dict com premissas

    Saída:
    dict serializável com resultado
    """
    entrada = criar_entrada_core_por_payload(payload)
    resultado = calcular_core_valuation(entrada)
    return resultado_core_para_dict(resultado)


def gerar_payload_exemplo_core() -> Dict[str, Any]:
    return {
        "empresa": "Empresa Exemplo",
        "ticker": "EXPL3",
        "lucro_liquido_sustentavel": 1_000_000_000,
        "fluxo_caixa_livre": 900_000_000,
        "quantidade_acoes": 500_000_000,
        "multiplo_justo_eps": 15,
        "multiplo_justo_fcf": 14,
        "peso_eps": 50,
        "peso_fcf": 50,
        "margem_seguranca": 30,
        "preco_atual": 18,
        "moeda": "R$",
    }


def gerar_contrato_api_core() -> Dict[str, Any]:
    return {
        "endpoint_futuro": "POST /valuation/calculate",
        "versao_core": VERSAO_CORE_VALUATION,
        "descricao": (
            "Calcula preço justo, preço-teto, margem de segurança, potencial e status educacional "
            "a partir das premissas financeiras informadas."
        ),
        "entrada_esperada": gerar_payload_exemplo_core(),
        "saida_principal": [
            "eps_normalizado",
            "fcf_por_acao",
            "preco_justo_eps",
            "preco_justo_fcf",
            "preco_justo_combinado",
            "preco_teto",
            "margem_ate_preco_teto",
            "potencial_ate_preco_justo",
            "status",
            "explicacao_status",
        ],
        "status_possiveis": ["COMPRA", "NEUTRO", "AGUARDE"],
    }


def gerar_regras_core() -> List[Dict[str, str]]:
    return [
        {
            "Regra": "EPS normalizado",
            "Fórmula": "lucro_liquido_sustentavel / quantidade_acoes",
            "Uso": "Estimar lucro por ação sustentável.",
        },
        {
            "Regra": "FCF por ação",
            "Fórmula": "fluxo_caixa_livre / quantidade_acoes",
            "Uso": "Estimar caixa livre por ação.",
        },
        {
            "Regra": "Preço justo por EPS",
            "Fórmula": "eps_normalizado * multiplo_justo_eps",
            "Uso": "Valuation baseado em lucro.",
        },
        {
            "Regra": "Preço justo por FCF",
            "Fórmula": "fcf_por_acao * multiplo_justo_fcf",
            "Uso": "Valuation baseado em caixa.",
        },
        {
            "Regra": "Preço justo combinado",
            "Fórmula": "preco_justo_eps * peso_eps + preco_justo_fcf * peso_fcf",
            "Uso": "Combinar lucro e caixa em uma estimativa única.",
        },
        {
            "Regra": "Preço-teto",
            "Fórmula": "preco_justo_combinado * (1 - margem_seguranca)",
            "Uso": "Definir zona conservadora de entrada.",
        },
        {
            "Regra": "Status COMPRA",
            "Fórmula": "preco_atual <= preco_teto",
            "Uso": "Preço está dentro da zona conservadora.",
        },
        {
            "Regra": "Status NEUTRO",
            "Fórmula": "preco_teto < preco_atual <= preco_justo_combinado",
            "Uso": "Preço não está barato o suficiente, mas não passou do justo.",
        },
        {
            "Regra": "Status AGUARDE",
            "Fórmula": "preco_atual > preco_justo_combinado",
            "Uso": "Preço está acima do justo estimado.",
        },
    ]


def gerar_markdown_especificacao_core() -> str:
    contrato = gerar_contrato_api_core()
    regras = gerar_regras_core()
    payload_json = json.dumps(
        contrato["entrada_esperada"],
        indent=2,
        ensure_ascii=False,
    )

    linhas_regras = "\n".join(
        [
            f"| {item['Regra']} | {item['Fórmula']} | {item['Uso']} |"
            for item in regras
        ]
    )

    return f"""# Especificação do Core Engine de Valuation

Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Versão

Core Valuation: {VERSAO_CORE_VALUATION}

## Endpoint futuro

{contrato["endpoint_futuro"]}

## Descrição

{contrato["descricao"]}

## Payload de exemplo

```json
{payload_json}
```

## Campos principais de saída

{", ".join(contrato["saida_principal"])}

## Status possíveis

{", ".join(contrato["status_possiveis"])}

## Regras do motor

| Regra | Fórmula | Uso |
|---|---|---|
{linhas_regras}

## Princípio

O Core Engine deve continuar independente de interface.  
Ele não deve importar Streamlit, FastAPI, banco de dados ou bibliotecas de tela.
"""


def executar_autoteste_core() -> List[Dict[str, Any]]:
    """
    Executa testes simples de sanidade do motor.
    Não substitui pytest, mas ajuda a validar rapidamente o arquivo.
    """
    testes = []

    payload_base = gerar_payload_exemplo_core()
    resultado_base = calcular_core_valuation_por_payload(payload_base)

    testes.append(
        {
            "teste": "payload_exemplo_calcula_sem_erro",
            "status": "OK" if resultado_base["preco_teto"] != 0 else "FALHA",
            "detalhe": f"Status calculado: {resultado_base['status']}",
        }
    )

    payload_compra = {
        **payload_base,
        "preco_atual": 10,
    }

    resultado_compra = calcular_core_valuation_por_payload(payload_compra)

    testes.append(
        {
            "teste": "classificacao_compra",
            "status": "OK" if resultado_compra["status"] == "COMPRA" else "FALHA",
            "detalhe": f"Status calculado: {resultado_compra['status']}",
        }
    )

    payload_aguarde = {
        **payload_base,
        "preco_atual": 1000,
    }

    resultado_aguarde = calcular_core_valuation_por_payload(payload_aguarde)

    testes.append(
        {
            "teste": "classificacao_aguarde",
            "status": "OK" if resultado_aguarde["status"] == "AGUARDE" else "FALHA",
            "detalhe": f"Status calculado: {resultado_aguarde['status']}",
        }
    )

    try:
        payload_invalido = {
            **payload_base,
            "quantidade_acoes": 0,
        }

        calcular_core_valuation_por_payload(payload_invalido)

        testes.append(
            {
                "teste": "validacao_quantidade_acoes_zero",
                "status": "FALHA",
                "detalhe": "Era esperado erro, mas o cálculo passou.",
            }
        )
    except ValueError:
        testes.append(
            {
                "teste": "validacao_quantidade_acoes_zero",
                "status": "OK",
                "detalhe": "Erro capturado corretamente.",
            }
        )

    return testes