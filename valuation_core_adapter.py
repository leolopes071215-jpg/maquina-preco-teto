# valuation_core_adapter.py

from datetime import datetime
from typing import Any, Dict, List

from core_valuation import (
    EntradaCoreValuation,
    ResultadoCoreValuation,
    calcular_core_valuation,
    resultado_core_para_dict,
)
from valuation import EntradasValuation, calcular_valuation


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v3.8.4 — Adaptador Seguro do Core Engine
# ------------------------------------------------------------
# Este arquivo cria uma ponte entre:
#
# - valuation.py       -> motor legacy usado atualmente pelo app
# - core_valuation.py  -> novo motor profissional da Fase 4
#
# Objetivo:
# - permitir que o app use o Core Engine sem quebrar a interface
# - manter a mesma estrutura de saída esperada pelo app.py
# - facilitar troca controlada do motor principal
# - manter opção de auditoria lado a lado
# ============================================================


VERSAO_ADAPTER_CORE = "3.8.4"


CAMPOS_LEGACY_ESPERADOS = [
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
]


CAMPOS_NUMERICOS_COMPARADOS = [
    "eps_normalizado",
    "fcf_por_acao",
    "preco_justo_eps",
    "preco_justo_fcf",
    "preco_justo_combinado",
    "preco_teto",
    "margem_ate_preco_teto",
    "potencial_ate_preco_justo",
]


CAMPOS_TEXTO_ESTRUTURAL = [
    "status",
]


CAMPOS_TEXTO_INFORMATIVO = [
    "explicacao_status",
]


def _safe_float(valor: Any, default: float = 0.0) -> float:
    try:
        return float(valor)
    except (TypeError, ValueError):
        return default


def _texto_preenchido(valor: Any) -> bool:
    return str(valor).strip() != ""


def criar_entrada_core_por_entradas_legacy(
    entradas: EntradasValuation,
    moeda: str = "R$",
) -> EntradaCoreValuation:
    """
    Converte o objeto EntradasValuation usado pelo app atual
    para EntradaCoreValuation usada pelo Core Engine.
    """
    return EntradaCoreValuation(
        empresa=str(entradas.empresa),
        ticker=str(entradas.ticker).upper(),
        lucro_liquido_sustentavel=_safe_float(entradas.lucro_liquido_sustentavel),
        fluxo_caixa_livre=_safe_float(entradas.fluxo_caixa_livre),
        quantidade_acoes=_safe_float(entradas.quantidade_acoes),
        multiplo_justo_eps=_safe_float(entradas.multiplo_justo_eps),
        multiplo_justo_fcf=_safe_float(entradas.multiplo_justo_fcf),
        peso_eps=_safe_float(entradas.peso_eps),
        peso_fcf=_safe_float(entradas.peso_fcf),
        margem_seguranca=_safe_float(entradas.margem_seguranca),
        preco_atual=_safe_float(entradas.preco_atual),
        moeda=moeda,
    )


def converter_resultado_core_para_legacy(
    resultado_core: ResultadoCoreValuation,
) -> Dict[str, Any]:
    """
    Converte ResultadoCoreValuation para o formato de dicionário
    esperado pelo app atual.

    Isso permite que o app.py continue usando as mesmas chaves:
    - resultado["preco_teto"]
    - resultado["status"]
    - resultado["explicacao_status"]
    etc.
    """
    resultado_dict = resultado_core_para_dict(resultado_core)

    return {
        "eps_normalizado": resultado_dict["eps_normalizado"],
        "fcf_por_acao": resultado_dict["fcf_por_acao"],
        "preco_justo_eps": resultado_dict["preco_justo_eps"],
        "preco_justo_fcf": resultado_dict["preco_justo_fcf"],
        "preco_justo_combinado": resultado_dict["preco_justo_combinado"],
        "preco_teto": resultado_dict["preco_teto"],
        "margem_ate_preco_teto": resultado_dict["margem_ate_preco_teto"],
        "potencial_ate_preco_justo": resultado_dict["potencial_ate_preco_justo"],
        "status": resultado_dict["status"],
        "explicacao_status": resultado_dict["explicacao_status"],
        "motor": "core_engine",
        "versao_motor": resultado_dict["versao_core"],
        "data_calculo_motor": resultado_dict["data_calculo"],
        "moeda": resultado_dict["moeda"],
    }


def calcular_valuation_via_core(
    entradas: EntradasValuation,
    moeda: str = "R$",
) -> Dict[str, Any]:
    """
    Calcula valuation usando o Core Engine, mas devolvendo resultado
    no formato compatível com o app atual.
    """
    entrada_core = criar_entrada_core_por_entradas_legacy(
        entradas=entradas,
        moeda=moeda,
    )

    resultado_core = calcular_core_valuation(entrada_core)

    return converter_resultado_core_para_legacy(resultado_core)


def calcular_valuation_legacy_com_metadata(
    entradas: EntradasValuation,
) -> Dict[str, Any]:
    """
    Calcula valuation pelo motor legacy atual e adiciona metadados
    para comparação com o Core Engine.
    """
    resultado = calcular_valuation(entradas)

    resultado_com_metadata = {
        **resultado,
        "motor": "legacy",
        "versao_motor": "legacy",
        "data_calculo_motor": datetime.now().isoformat(timespec="seconds"),
    }

    return resultado_com_metadata


def calcular_valuation_por_motor(
    entradas: EntradasValuation,
    motor: str = "legacy",
    moeda: str = "R$",
) -> Dict[str, Any]:
    """
    Função central de roteamento.

    motor="legacy" -> usa valuation.py
    motor="core"   -> usa core_valuation.py via adaptador
    """
    motor_normalizado = str(motor).strip().lower()

    if motor_normalizado in ["core", "core_engine", "novo"]:
        return calcular_valuation_via_core(
            entradas=entradas,
            moeda=moeda,
        )

    return calcular_valuation_legacy_com_metadata(entradas)


def _comparar_campo_numerico(
    campo: str,
    resultado_legacy: Dict[str, Any],
    resultado_core: Dict[str, Any],
    tolerancia: float,
) -> Dict[str, Any]:
    valor_legacy = resultado_legacy.get(campo)
    valor_core = resultado_core.get(campo)

    valor_legacy_float = _safe_float(valor_legacy)
    valor_core_float = _safe_float(valor_core)
    diferenca = abs(valor_legacy_float - valor_core_float)
    compativel = diferenca <= tolerancia

    return {
        "campo": campo,
        "legacy": valor_legacy,
        "core": valor_core,
        "diferenca": diferenca,
        "compativel": compativel,
        "tipo_comparacao": "numerica",
    }


def _comparar_campo_texto_estrutural(
    campo: str,
    resultado_legacy: Dict[str, Any],
    resultado_core: Dict[str, Any],
) -> Dict[str, Any]:
    valor_legacy = str(resultado_legacy.get(campo, "")).strip()
    valor_core = str(resultado_core.get(campo, "")).strip()
    compativel = valor_legacy == valor_core

    return {
        "campo": campo,
        "legacy": valor_legacy,
        "core": valor_core,
        "diferenca": 0 if compativel else "texto_diferente",
        "compativel": compativel,
        "tipo_comparacao": "texto_estrutural",
    }


def _comparar_campo_texto_informativo(
    campo: str,
    resultado_legacy: Dict[str, Any],
    resultado_core: Dict[str, Any],
) -> Dict[str, Any]:
    valor_legacy = str(resultado_legacy.get(campo, "")).strip()
    valor_core = str(resultado_core.get(campo, "")).strip()

    compativel = _texto_preenchido(valor_legacy) and _texto_preenchido(valor_core)

    if valor_legacy == valor_core:
        diferenca = 0
    elif compativel:
        diferenca = "texto_informativo_diferente_aceito"
    else:
        diferenca = "texto_vazio"

    return {
        "campo": campo,
        "legacy": valor_legacy,
        "core": valor_core,
        "diferenca": diferenca,
        "compativel": compativel,
        "tipo_comparacao": "texto_informativo",
    }


def comparar_motores_por_entradas(
    entradas: EntradasValuation,
    moeda: str = "R$",
    tolerancia: float = 0.0001,
) -> Dict[str, Any]:
    """
    Compara o motor legacy com o Core Engine para uma entrada específica.
    Útil para auditoria antes de trocar o motor principal.

    Observação:
    - Campos numéricos precisam bater dentro da tolerância.
    - Campos estruturais, como status, precisam ser exatamente iguais.
    - Campos informativos, como explicacao_status, precisam existir, mas
      não precisam ter o mesmo texto palavra por palavra.
    """
    resultado_legacy = calcular_valuation_legacy_com_metadata(entradas)
    resultado_core = calcular_valuation_via_core(entradas, moeda=moeda)

    comparacoes = []

    for campo in CAMPOS_NUMERICOS_COMPARADOS:
        comparacoes.append(
            _comparar_campo_numerico(
                campo=campo,
                resultado_legacy=resultado_legacy,
                resultado_core=resultado_core,
                tolerancia=tolerancia,
            )
        )

    for campo in CAMPOS_TEXTO_ESTRUTURAL:
        comparacoes.append(
            _comparar_campo_texto_estrutural(
                campo=campo,
                resultado_legacy=resultado_legacy,
                resultado_core=resultado_core,
            )
        )

    for campo in CAMPOS_TEXTO_INFORMATIVO:
        comparacoes.append(
            _comparar_campo_texto_informativo(
                campo=campo,
                resultado_legacy=resultado_legacy,
                resultado_core=resultado_core,
            )
        )

    aprovado = all(item["compativel"] for item in comparacoes)

    return {
        "aprovado": aprovado,
        "tolerancia": tolerancia,
        "resultado_legacy": resultado_legacy,
        "resultado_core": resultado_core,
        "comparacoes": comparacoes,
        "campos_com_diferenca": [
            item for item in comparacoes if not item["compativel"]
        ],
    }


def gerar_entradas_exemplo_adapter() -> EntradasValuation:
    """
    Gera entradas de exemplo para testar o adaptador.
    """
    return EntradasValuation(
        empresa="Empresa Exemplo Adapter",
        ticker="ADPT3",
        lucro_liquido_sustentavel=1_000_000_000,
        fluxo_caixa_livre=900_000_000,
        quantidade_acoes=500_000_000,
        multiplo_justo_eps=15,
        multiplo_justo_fcf=14,
        peso_eps=50,
        peso_fcf=50,
        margem_seguranca=30,
        preco_atual=18,
    )


def gerar_tabela_comparacao_adapter(
    comparacao: Dict[str, Any],
) -> List[Dict[str, str]]:
    """
    Gera tabela amigável da comparação entre motores.
    """
    linhas = []

    for item in comparacao.get("comparacoes", []):
        diferenca = item.get("diferenca", "")

        if isinstance(diferenca, float):
            diferenca_formatada = f"{diferenca:.8f}"
        else:
            diferenca_formatada = str(diferenca)

        linhas.append(
            {
                "Campo": str(item.get("campo", "")),
                "Legacy": str(item.get("legacy", "")),
                "Core": str(item.get("core", "")),
                "Diferença": diferenca_formatada,
                "Compatível": "Sim" if item.get("compativel") else "Não",
                "Tipo": str(item.get("tipo_comparacao", "")),
            }
        )

    return linhas


def gerar_markdown_adapter_core(
    comparacao: Dict[str, Any],
) -> str:
    """
    Gera relatório técnico do adaptador.
    """
    linhas = "\n".join(
        [
            f"| {linha['Campo']} | {linha['Legacy']} | {linha['Core']} | {linha['Diferença']} | {linha['Compatível']} | {linha['Tipo']} |"
            for linha in gerar_tabela_comparacao_adapter(comparacao)
        ]
    )

    status = "APROVADO" if comparacao.get("aprovado") else "REPROVADO"

    return f"""# Relatório do Adaptador Core Engine

Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Status

**Status:** {status}  
**Versão do adaptador:** {VERSAO_ADAPTER_CORE}  
**Tolerância:** {comparacao.get("tolerancia")}  

## Comparação Legacy vs Core

| Campo | Legacy | Core | Diferença | Compatível | Tipo |
|---|---:|---:|---:|---|---|
{linhas}

## Leitura

O adaptador permite que o app principal use o Core Engine mantendo a mesma estrutura
de saída esperada pelo código atual.

Campos numéricos precisam bater dentro da tolerância.  
Campos estruturais, como status, precisam ser iguais.  
Campos informativos, como explicação textual, precisam existir, mas podem ter texto diferente.

A troca definitiva do motor deve ser feita apenas quando a comparação estiver aprovada.
"""


def executar_autoteste_adapter_core() -> List[Dict[str, str]]:
    """
    Executa testes rápidos do adaptador.
    """
    testes = []

    entradas = gerar_entradas_exemplo_adapter()

    resultado_legacy = calcular_valuation_por_motor(
        entradas=entradas,
        motor="legacy",
    )

    resultado_core = calcular_valuation_por_motor(
        entradas=entradas,
        motor="core",
    )

    testes.append(
        {
            "teste": "motor_legacy_calcula",
            "status": "OK" if resultado_legacy.get("preco_teto", 0) != 0 else "FALHA",
            "detalhe": f"Status: {resultado_legacy.get('status')}",
        }
    )

    testes.append(
        {
            "teste": "motor_core_calcula",
            "status": "OK" if resultado_core.get("preco_teto", 0) != 0 else "FALHA",
            "detalhe": f"Status: {resultado_core.get('status')}",
        }
    )

    testes.append(
        {
            "teste": "core_devolve_chaves_legacy",
            "status": (
                "OK"
                if all(campo in resultado_core for campo in CAMPOS_LEGACY_ESPERADOS)
                else "FALHA"
            ),
            "detalhe": "Validação das chaves principais.",
        }
    )

    comparacao = comparar_motores_por_entradas(entradas)

    testes.append(
        {
            "teste": "comparacao_legacy_core_aprovada",
            "status": "OK" if comparacao.get("aprovado") else "FALHA",
            "detalhe": f"Diferenças críticas: {len(comparacao.get('campos_com_diferenca', []))}",
        }
    )

    return testes