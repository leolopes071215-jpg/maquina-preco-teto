# compatibilidade_core_legacy.py

from datetime import datetime
from typing import Any, Dict, List

from core_valuation import (
    EntradaCoreValuation,
    calcular_core_valuation,
    resultado_core_para_dict,
)
from valuation import EntradasValuation, calcular_valuation


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v3.8.3 — Auditoria de Compatibilidade Core vs Legacy
# ------------------------------------------------------------
# Este arquivo compara o motor antigo valuation.py com o novo
# Core Engine core_valuation.py.
#
# Objetivo:
# - garantir que o novo núcleo calcula de forma compatível
# - identificar diferenças antes de substituir o motor principal
# - reduzir risco de regressão
# - preparar a migração segura para a Fase 4
# ============================================================


VERSAO_COMPATIBILIDADE = "3.8.3"


CAMPOS_COMPARADOS = [
    "eps_normalizado",
    "fcf_por_acao",
    "preco_justo_eps",
    "preco_justo_fcf",
    "preco_justo_combinado",
    "preco_teto",
    "margem_ate_preco_teto",
    "potencial_ate_preco_justo",
    "status",
]


def _safe_float(valor: Any, default: float = 0.0) -> float:
    try:
        return float(valor)
    except (TypeError, ValueError):
        return default


def _normalizar_float(valor: Any, casas: int = 6) -> float:
    return round(_safe_float(valor), casas)


def _formatar_numero(valor: Any) -> str:
    if isinstance(valor, str):
        return valor

    return f"{_safe_float(valor):,.6f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _comparar_valores(
    valor_legacy: Any,
    valor_core: Any,
    tolerancia: float,
) -> Dict[str, Any]:
    if isinstance(valor_legacy, str) or isinstance(valor_core, str):
        legacy_normalizado = str(valor_legacy).strip()
        core_normalizado = str(valor_core).strip()

        return {
            "legacy": legacy_normalizado,
            "core": core_normalizado,
            "diferenca": 0 if legacy_normalizado == core_normalizado else "texto_diferente",
            "compativel": legacy_normalizado == core_normalizado,
        }

    legacy_float = _safe_float(valor_legacy)
    core_float = _safe_float(valor_core)
    diferenca = abs(legacy_float - core_float)

    return {
        "legacy": legacy_float,
        "core": core_float,
        "diferenca": diferenca,
        "compativel": diferenca <= tolerancia,
    }


def criar_payload_teste_padrao() -> Dict[str, Any]:
    return {
        "empresa": "Empresa Teste",
        "ticker": "TEST3",
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


def criar_cenarios_compatibilidade() -> List[Dict[str, Any]]:
    base = criar_payload_teste_padrao()

    return [
        {
            **base,
            "nome_cenario": "Base equilibrado",
        },
        {
            **base,
            "nome_cenario": "Status compra",
            "preco_atual": 10,
        },
        {
            **base,
            "nome_cenario": "Status aguarde",
            "preco_atual": 100,
        },
        {
            **base,
            "nome_cenario": "Peso maior em EPS",
            "peso_eps": 80,
            "peso_fcf": 20,
        },
        {
            **base,
            "nome_cenario": "Peso maior em FCF",
            "peso_eps": 20,
            "peso_fcf": 80,
        },
        {
            **base,
            "nome_cenario": "Margem de segurança baixa",
            "margem_seguranca": 10,
        },
        {
            **base,
            "nome_cenario": "Margem de segurança alta",
            "margem_seguranca": 60,
        },
        {
            **base,
            "nome_cenario": "Empresa com lucro e caixa maiores",
            "lucro_liquido_sustentavel": 5_000_000_000,
            "fluxo_caixa_livre": 4_200_000_000,
            "quantidade_acoes": 1_000_000_000,
            "preco_atual": 45,
        },
        {
            **base,
            "nome_cenario": "Empresa com caixa menor que lucro",
            "lucro_liquido_sustentavel": 2_000_000_000,
            "fluxo_caixa_livre": 800_000_000,
            "quantidade_acoes": 400_000_000,
            "preco_atual": 25,
        },
    ]


def calcular_legacy_por_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    entradas = EntradasValuation(
        empresa=str(payload.get("empresa", "")),
        ticker=str(payload.get("ticker", "")).upper(),
        lucro_liquido_sustentavel=_safe_float(payload.get("lucro_liquido_sustentavel")),
        fluxo_caixa_livre=_safe_float(payload.get("fluxo_caixa_livre")),
        quantidade_acoes=_safe_float(payload.get("quantidade_acoes")),
        multiplo_justo_eps=_safe_float(payload.get("multiplo_justo_eps")),
        multiplo_justo_fcf=_safe_float(payload.get("multiplo_justo_fcf")),
        peso_eps=_safe_float(payload.get("peso_eps")),
        peso_fcf=_safe_float(payload.get("peso_fcf")),
        margem_seguranca=_safe_float(payload.get("margem_seguranca")),
        preco_atual=_safe_float(payload.get("preco_atual")),
    )

    return calcular_valuation(entradas)


def calcular_core_por_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    entrada = EntradaCoreValuation(
        empresa=str(payload.get("empresa", "")),
        ticker=str(payload.get("ticker", "")).upper(),
        lucro_liquido_sustentavel=_safe_float(payload.get("lucro_liquido_sustentavel")),
        fluxo_caixa_livre=_safe_float(payload.get("fluxo_caixa_livre")),
        quantidade_acoes=_safe_float(payload.get("quantidade_acoes")),
        multiplo_justo_eps=_safe_float(payload.get("multiplo_justo_eps")),
        multiplo_justo_fcf=_safe_float(payload.get("multiplo_justo_fcf")),
        peso_eps=_safe_float(payload.get("peso_eps")),
        peso_fcf=_safe_float(payload.get("peso_fcf")),
        margem_seguranca=_safe_float(payload.get("margem_seguranca")),
        preco_atual=_safe_float(payload.get("preco_atual")),
        moeda=str(payload.get("moeda", "R$")),
    )

    resultado = calcular_core_valuation(entrada)
    return resultado_core_para_dict(resultado)


def comparar_cenario(
    payload: Dict[str, Any],
    tolerancia: float = 0.0001,
) -> Dict[str, Any]:
    nome_cenario = str(payload.get("nome_cenario", "Cenário sem nome"))

    resultado_legacy = calcular_legacy_por_payload(payload)
    resultado_core = calcular_core_por_payload(payload)

    comparacoes = []

    for campo in CAMPOS_COMPARADOS:
        comparacao = _comparar_valores(
            valor_legacy=resultado_legacy.get(campo),
            valor_core=resultado_core.get(campo),
            tolerancia=tolerancia,
        )

        comparacoes.append(
            {
                "cenario": nome_cenario,
                "campo": campo,
                "legacy": comparacao["legacy"],
                "core": comparacao["core"],
                "diferenca": comparacao["diferenca"],
                "compativel": comparacao["compativel"],
            }
        )

    compativel = all(item["compativel"] for item in comparacoes)

    return {
        "cenario": nome_cenario,
        "compativel": compativel,
        "comparacoes": comparacoes,
        "resultado_legacy": resultado_legacy,
        "resultado_core": resultado_core,
    }


def executar_auditoria_compatibilidade(
    tolerancia: float = 0.0001,
) -> Dict[str, Any]:
    cenarios = criar_cenarios_compatibilidade()
    resultados = [
        comparar_cenario(cenario, tolerancia=tolerancia)
        for cenario in cenarios
    ]

    total_cenarios = len(resultados)
    cenarios_compativeis = len(
        [resultado for resultado in resultados if resultado["compativel"]]
    )
    cenarios_com_diferenca = total_cenarios - cenarios_compativeis

    todas_comparacoes = []

    for resultado in resultados:
        todas_comparacoes.extend(resultado["comparacoes"])

    campos_com_diferenca = [
        comparacao
        for comparacao in todas_comparacoes
        if not comparacao["compativel"]
    ]

    return {
        "versao": VERSAO_COMPATIBILIDADE,
        "data_auditoria": datetime.now().isoformat(timespec="seconds"),
        "tolerancia": tolerancia,
        "total_cenarios": total_cenarios,
        "cenarios_compativeis": cenarios_compativeis,
        "cenarios_com_diferenca": cenarios_com_diferenca,
        "aprovado": cenarios_com_diferenca == 0,
        "resultados": resultados,
        "todas_comparacoes": todas_comparacoes,
        "campos_com_diferenca": campos_com_diferenca,
    }


def gerar_tabela_resumo_compatibilidade(auditoria: Dict[str, Any]) -> List[Dict[str, str]]:
    linhas = []

    for resultado in auditoria.get("resultados", []):
        linhas.append(
            {
                "Cenário": resultado.get("cenario", ""),
                "Compatível": "Sim" if resultado.get("compativel") else "Não",
                "Status Legacy": str(resultado.get("resultado_legacy", {}).get("status", "")),
                "Status Core": str(resultado.get("resultado_core", {}).get("status", "")),
                "Preço-teto Legacy": _formatar_numero(
                    resultado.get("resultado_legacy", {}).get("preco_teto", 0)
                ),
                "Preço-teto Core": _formatar_numero(
                    resultado.get("resultado_core", {}).get("preco_teto", 0)
                ),
            }
        )

    return linhas


def gerar_tabela_detalhada_compatibilidade(
    auditoria: Dict[str, Any],
) -> List[Dict[str, str]]:
    linhas = []

    for comparacao in auditoria.get("todas_comparacoes", []):
        diferenca = comparacao.get("diferenca", "")

        if isinstance(diferenca, float):
            diferenca_formatada = _formatar_numero(diferenca)
        else:
            diferenca_formatada = str(diferenca)

        linhas.append(
            {
                "Cenário": str(comparacao.get("cenario", "")),
                "Campo": str(comparacao.get("campo", "")),
                "Legacy": str(comparacao.get("legacy", "")),
                "Core": str(comparacao.get("core", "")),
                "Diferença": diferenca_formatada,
                "Compatível": "Sim" if comparacao.get("compativel") else "Não",
            }
        )

    return linhas


def gerar_markdown_auditoria_compatibilidade(
    auditoria: Dict[str, Any],
) -> str:
    resumo = gerar_tabela_resumo_compatibilidade(auditoria)
    detalhe = gerar_tabela_detalhada_compatibilidade(auditoria)

    linhas_resumo = "\n".join(
        [
            f"| {linha['Cenário']} | {linha['Compatível']} | {linha['Status Legacy']} | {linha['Status Core']} | {linha['Preço-teto Legacy']} | {linha['Preço-teto Core']} |"
            for linha in resumo
        ]
    )

    linhas_detalhe = "\n".join(
        [
            f"| {linha['Cenário']} | {linha['Campo']} | {linha['Legacy']} | {linha['Core']} | {linha['Diferença']} | {linha['Compatível']} |"
            for linha in detalhe
        ]
    )

    status = "APROVADO" if auditoria.get("aprovado") else "REPROVADO"

    return f"""# Auditoria de Compatibilidade — Core Engine vs Legacy

Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Resultado

**Status:** {status}  
**Versão da auditoria:** {auditoria.get("versao")}  
**Tolerância:** {auditoria.get("tolerancia")}  
**Total de cenários:** {auditoria.get("total_cenarios")}  
**Cenários compatíveis:** {auditoria.get("cenarios_compativeis")}  
**Cenários com diferença:** {auditoria.get("cenarios_com_diferenca")}  

## Resumo por cenário

| Cenário | Compatível | Status Legacy | Status Core | Preço-teto Legacy | Preço-teto Core |
|---|---|---|---|---:|---:|
{linhas_resumo}

## Comparação detalhada

| Cenário | Campo | Legacy | Core | Diferença | Compatível |
|---|---|---:|---:|---:|---|
{linhas_detalhe}

## Leitura

Esta auditoria compara o motor antigo `valuation.py` com o novo `core_valuation.py`.
A substituição definitiva só deve acontecer quando os cenários principais estiverem compatíveis.
"""


def executar_autoteste_compatibilidade() -> List[Dict[str, str]]:
    testes = []

    auditoria = executar_auditoria_compatibilidade()

    testes.append(
        {
            "teste": "auditoria_executa_sem_erro",
            "status": "OK" if auditoria.get("total_cenarios", 0) > 0 else "FALHA",
            "detalhe": f"Cenários testados: {auditoria.get('total_cenarios')}",
        }
    )

    testes.append(
        {
            "teste": "auditoria_aprovada",
            "status": "OK" if auditoria.get("aprovado") else "FALHA",
            "detalhe": (
                f"Cenários com diferença: {auditoria.get('cenarios_com_diferenca')}"
            ),
        }
    )

    return testes