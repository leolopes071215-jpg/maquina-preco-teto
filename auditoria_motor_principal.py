# auditoria_motor_principal.py

from datetime import datetime
from typing import Any, Dict, List

from valuation import EntradasValuation
from motor_valuation_controlado import (
    MOTOR_CORE,
    MOTOR_LEGACY,
    VERSAO_MOTOR_CONTROLADO,
    auditar_motor_selecionado,
    calcular_valuation_controlado,
    gerar_tabela_auditoria_motor_controlado,
    obter_motor_padrao,
    obter_motores_disponiveis,
)


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v3.8.9 — Auditoria Pós-Integração do Motor Principal
# ------------------------------------------------------------
# Este arquivo audita o fluxo principal após a integração do
# Motor Controlado ao app.py.
#
# Objetivo:
# - validar se o motor principal calcula corretamente
# - confirmar compatibilidade Legacy vs Core
# - detectar diferenças críticas antes de avançar
# - gerar relatório técnico de segurança da migração
# - preparar decisão futura sobre tornar Core Engine padrão
# ============================================================


VERSAO_AUDITORIA_MOTOR_PRINCIPAL = "3.8.9"


def _safe_float(valor: Any, default: float = 0.0) -> float:
    try:
        return float(valor)
    except (TypeError, ValueError):
        return default


def _formatar_moeda(valor: Any, moeda: str = "R$") -> str:
    numero = _safe_float(valor)
    return f"{moeda} {numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _formatar_percentual(valor: Any) -> str:
    numero = _safe_float(valor)
    return f"{numero:.2f}%"


def gerar_entradas_exemplo_auditoria_motor_principal() -> EntradasValuation:
    """
    Gera uma entrada padrão para testar o fluxo principal.
    """
    return EntradasValuation(
        empresa="Empresa Exemplo Fluxo Principal",
        ticker="MAIN3",
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


def criar_cenarios_auditoria_motor_principal() -> List[Dict[str, Any]]:
    """
    Cria cenários representativos para testar o fluxo principal.
    """
    return [
        {
            "nome": "Base equilibrado",
            "entradas": EntradasValuation(
                empresa="Base Equilibrado",
                ticker="BASE3",
                lucro_liquido_sustentavel=1_000_000_000,
                fluxo_caixa_livre=900_000_000,
                quantidade_acoes=500_000_000,
                multiplo_justo_eps=15,
                multiplo_justo_fcf=14,
                peso_eps=50,
                peso_fcf=50,
                margem_seguranca=30,
                preco_atual=18,
            ),
        },
        {
            "nome": "Preço em zona de compra",
            "entradas": EntradasValuation(
                empresa="Zona de Compra",
                ticker="COMP3",
                lucro_liquido_sustentavel=1_000_000_000,
                fluxo_caixa_livre=900_000_000,
                quantidade_acoes=500_000_000,
                multiplo_justo_eps=15,
                multiplo_justo_fcf=14,
                peso_eps=50,
                peso_fcf=50,
                margem_seguranca=30,
                preco_atual=10,
            ),
        },
        {
            "nome": "Preço acima do justo",
            "entradas": EntradasValuation(
                empresa="Preço Esticado",
                ticker="AGRD3",
                lucro_liquido_sustentavel=1_000_000_000,
                fluxo_caixa_livre=900_000_000,
                quantidade_acoes=500_000_000,
                multiplo_justo_eps=15,
                multiplo_justo_fcf=14,
                peso_eps=50,
                peso_fcf=50,
                margem_seguranca=30,
                preco_atual=100,
            ),
        },
        {
            "nome": "Peso maior em lucro",
            "entradas": EntradasValuation(
                empresa="Peso EPS",
                ticker="EPS3",
                lucro_liquido_sustentavel=1_500_000_000,
                fluxo_caixa_livre=800_000_000,
                quantidade_acoes=400_000_000,
                multiplo_justo_eps=16,
                multiplo_justo_fcf=12,
                peso_eps=80,
                peso_fcf=20,
                margem_seguranca=35,
                preco_atual=35,
            ),
        },
        {
            "nome": "Peso maior em caixa",
            "entradas": EntradasValuation(
                empresa="Peso FCF",
                ticker="FCF3",
                lucro_liquido_sustentavel=900_000_000,
                fluxo_caixa_livre=1_400_000_000,
                quantidade_acoes=450_000_000,
                multiplo_justo_eps=13,
                multiplo_justo_fcf=15,
                peso_eps=20,
                peso_fcf=80,
                margem_seguranca=30,
                preco_atual=28,
            ),
        },
    ]


def classificar_seguranca_fluxo(
    motor_selecionado: str,
    resultado_principal: Dict[str, Any],
    auditoria_paralela: Dict[str, Any],
) -> str:
    """
    Classifica a segurança do fluxo principal.
    """
    preco_teto = _safe_float(resultado_principal.get("preco_teto", 0))
    status = str(resultado_principal.get("status", "")).strip()

    if preco_teto <= 0 or status == "":
        return "FALHA_OPERACIONAL"

    if motor_selecionado == MOTOR_LEGACY:
        if auditoria_paralela.get("aprovado"):
            return "SEGURO_LEGACY_CORE_COMPATIVEL"

        return "SEGURO_LEGACY_COM_ALERTA_CORE"

    if motor_selecionado == MOTOR_CORE:
        if auditoria_paralela.get("aprovado"):
            return "CORE_CONTROLADO_APROVADO"

        return "CORE_NAO_SEGURO"

    return "MOTOR_DESCONHECIDO"


def gerar_leitura_seguranca(
    classificacao: str,
) -> str:
    """
    Gera leitura executiva para a classificação de segurança.
    """
    if classificacao == "SEGURO_LEGACY_CORE_COMPATIVEL":
        return (
            "Fluxo seguro. O app está usando Legacy como motor principal e a auditoria paralela "
            "mostra que o Core Engine está compatível. É um cenário saudável para continuar a migração."
        )

    if classificacao == "SEGURO_LEGACY_COM_ALERTA_CORE":
        return (
            "Fluxo principal seguro porque o Legacy está ativo, mas existe alerta na comparação com o Core. "
            "Não avance para tornar o Core padrão até resolver as diferenças."
        )

    if classificacao == "CORE_CONTROLADO_APROVADO":
        return (
            "Core Engine está ativo de forma controlada e a auditoria paralela foi aprovada. "
            "O sistema está em bom estado para testes internos com o novo motor."
        )

    if classificacao == "CORE_NAO_SEGURO":
        return (
            "Core Engine está ativo, mas a auditoria paralela encontrou diferenças críticas. "
            "Volte para Legacy e revise os campos divergentes."
        )

    if classificacao == "FALHA_OPERACIONAL":
        return (
            "O fluxo principal não retornou dados mínimos válidos. Revise entradas, motor selecionado "
            "e estrutura de saída do cálculo."
        )

    return (
        "Motor desconhecido ou configuração inesperada. Recomenda-se voltar para Legacy e revisar o seletor."
    )


def executar_auditoria_motor_principal(
    entradas: EntradasValuation,
    motor_selecionado: str = MOTOR_LEGACY,
    moeda: str = "R$",
    tolerancia: float = 0.0001,
) -> Dict[str, Any]:
    """
    Executa uma auditoria completa do motor usado no fluxo principal.
    """
    resultado_principal = calcular_valuation_controlado(
        entradas=entradas,
        motor=motor_selecionado,
        moeda=moeda,
    )

    auditoria_paralela = auditar_motor_selecionado(
        entradas=entradas,
        moeda=moeda,
        tolerancia=tolerancia,
    )

    classificacao = classificar_seguranca_fluxo(
        motor_selecionado=motor_selecionado,
        resultado_principal=resultado_principal,
        auditoria_paralela=auditoria_paralela,
    )

    return {
        "versao_auditoria": VERSAO_AUDITORIA_MOTOR_PRINCIPAL,
        "versao_motor_controlado": VERSAO_MOTOR_CONTROLADO,
        "data_auditoria": datetime.now().isoformat(timespec="seconds"),
        "motor_selecionado": motor_selecionado,
        "moeda": moeda,
        "tolerancia": tolerancia,
        "resultado_principal": resultado_principal,
        "auditoria_paralela": auditoria_paralela,
        "classificacao_seguranca": classificacao,
        "leitura_seguranca": gerar_leitura_seguranca(classificacao),
        "aprovado_para_teste_core": (
            classificacao in [
                "SEGURO_LEGACY_CORE_COMPATIVEL",
                "CORE_CONTROLADO_APROVADO",
            ]
        ),
        "aprovado_para_core_padrao": classificacao == "CORE_CONTROLADO_APROVADO",
        "campos_com_diferenca": auditoria_paralela.get("campos_com_diferenca", []),
    }


def executar_bateria_auditoria_motor_principal(
    moeda: str = "R$",
    tolerancia: float = 0.0001,
) -> Dict[str, Any]:
    """
    Executa bateria de auditorias usando Legacy e Core em vários cenários.
    """
    cenarios = criar_cenarios_auditoria_motor_principal()
    resultados = []

    for cenario in cenarios:
        for motor in [MOTOR_LEGACY, MOTOR_CORE]:
            auditoria = executar_auditoria_motor_principal(
                entradas=cenario["entradas"],
                motor_selecionado=motor,
                moeda=moeda,
                tolerancia=tolerancia,
            )

            resultados.append(
                {
                    "cenario": cenario["nome"],
                    "motor": motor,
                    "auditoria": auditoria,
                }
            )

    total = len(resultados)
    aprovados_teste_core = len(
        [
            item
            for item in resultados
            if item["auditoria"].get("aprovado_para_teste_core")
        ]
    )
    aprovados_core_padrao = len(
        [
            item
            for item in resultados
            if item["auditoria"].get("aprovado_para_core_padrao")
        ]
    )
    com_diferenca = len(
        [
            item
            for item in resultados
            if len(item["auditoria"].get("campos_com_diferenca", [])) > 0
        ]
    )

    return {
        "versao_auditoria": VERSAO_AUDITORIA_MOTOR_PRINCIPAL,
        "data_bateria": datetime.now().isoformat(timespec="seconds"),
        "total_execucoes": total,
        "aprovados_para_teste_core": aprovados_teste_core,
        "aprovados_para_core_padrao": aprovados_core_padrao,
        "execucoes_com_diferenca": com_diferenca,
        "bateria_aprovada": com_diferenca == 0,
        "resultados": resultados,
    }


def gerar_tabela_resumo_auditoria_motor_principal(
    auditoria: Dict[str, Any],
) -> List[Dict[str, str]]:
    """
    Gera tabela resumida da auditoria de uma entrada.
    """
    resultado = auditoria.get("resultado_principal", {})
    auditoria_paralela = auditoria.get("auditoria_paralela", {})
    moeda = auditoria.get("moeda", "R$")

    return [
        {
            "Campo": "Motor selecionado",
            "Valor": str(auditoria.get("motor_selecionado", "")),
        },
        {
            "Campo": "Status do valuation",
            "Valor": str(resultado.get("status", "")),
        },
        {
            "Campo": "Preço-teto",
            "Valor": _formatar_moeda(resultado.get("preco_teto", 0), moeda),
        },
        {
            "Campo": "Preço justo combinado",
            "Valor": _formatar_moeda(resultado.get("preco_justo_combinado", 0), moeda),
        },
        {
            "Campo": "Margem até preço-teto",
            "Valor": _formatar_percentual(resultado.get("margem_ate_preco_teto", 0)),
        },
        {
            "Campo": "Auditoria paralela",
            "Valor": "APROVADA" if auditoria_paralela.get("aprovado") else "REPROVADA",
        },
        {
            "Campo": "Classificação de segurança",
            "Valor": str(auditoria.get("classificacao_seguranca", "")),
        },
        {
            "Campo": "Diferenças críticas",
            "Valor": str(len(auditoria.get("campos_com_diferenca", []))),
        },
    ]


def gerar_tabela_bateria_motor_principal(
    bateria: Dict[str, Any],
) -> List[Dict[str, str]]:
    """
    Gera tabela com a bateria de cenários.
    """
    linhas = []

    for item in bateria.get("resultados", []):
        auditoria = item.get("auditoria", {})
        resultado = auditoria.get("resultado_principal", {})

        linhas.append(
            {
                "Cenário": str(item.get("cenario", "")),
                "Motor": str(item.get("motor", "")),
                "Status": str(resultado.get("status", "")),
                "Preço-teto": _formatar_moeda(
                    resultado.get("preco_teto", 0),
                    auditoria.get("moeda", "R$"),
                ),
                "Auditoria paralela": (
                    "Aprovada"
                    if auditoria.get("auditoria_paralela", {}).get("aprovado")
                    else "Reprovada"
                ),
                "Segurança": str(auditoria.get("classificacao_seguranca", "")),
                "Diferenças críticas": str(len(auditoria.get("campos_com_diferenca", []))),
            }
        )

    return linhas


def gerar_tabela_detalhada_comparacao_motor_principal(
    auditoria: Dict[str, Any],
) -> List[Dict[str, str]]:
    """
    Gera tabela detalhada de comparação Legacy vs Core.
    """
    return gerar_tabela_auditoria_motor_controlado(
        auditoria.get("auditoria_paralela", {})
    )


def gerar_markdown_auditoria_motor_principal(
    auditoria: Dict[str, Any],
) -> str:
    """
    Gera relatório técnico da auditoria de uma entrada.
    """
    resumo = gerar_tabela_resumo_auditoria_motor_principal(auditoria)
    detalhe = gerar_tabela_detalhada_comparacao_motor_principal(auditoria)

    linhas_resumo = "\n".join(
        [
            f"| {linha['Campo']} | {linha['Valor']} |"
            for linha in resumo
        ]
    )

    linhas_detalhe = "\n".join(
        [
            f"| {linha['Campo']} | {linha['Legacy']} | {linha['Core']} | {linha['Diferença']} | {linha['Compatível']} | {linha['Tipo']} |"
            for linha in detalhe
        ]
    )

    return f"""# Auditoria do Motor Principal

Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Resumo

| Campo | Valor |
|---|---|
{linhas_resumo}

## Leitura de segurança

{auditoria.get("leitura_seguranca", "")}

## Comparação Legacy vs Core

| Campo | Legacy | Core | Diferença | Compatível | Tipo |
|---|---:|---:|---:|---|---|
{linhas_detalhe}

## Decisão

**Aprovado para teste com Core:** {auditoria.get("aprovado_para_teste_core")}  
**Aprovado para Core como padrão:** {auditoria.get("aprovado_para_core_padrao")}  

## Observação

Esta auditoria verifica o comportamento do motor principal após a integração do Motor Controlado
ao fluxo principal do app.

O Core Engine só deve se tornar padrão quando a bateria completa estiver aprovada
e o uso real não apresentar divergências críticas.
"""


def gerar_markdown_bateria_motor_principal(
    bateria: Dict[str, Any],
) -> str:
    """
    Gera relatório técnico da bateria de cenários.
    """
    tabela = gerar_tabela_bateria_motor_principal(bateria)

    linhas = "\n".join(
        [
            f"| {linha['Cenário']} | {linha['Motor']} | {linha['Status']} | {linha['Preço-teto']} | {linha['Auditoria paralela']} | {linha['Segurança']} | {linha['Diferenças críticas']} |"
            for linha in tabela
        ]
    )

    status = "APROVADA" if bateria.get("bateria_aprovada") else "REPROVADA"

    return f"""# Bateria de Auditoria do Motor Principal

Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Resultado geral

**Status:** {status}  
**Total de execuções:** {bateria.get("total_execucoes")}  
**Aprovados para teste Core:** {bateria.get("aprovados_para_teste_core")}  
**Aprovados para Core padrão:** {bateria.get("aprovados_para_core_padrao")}  
**Execuções com diferença crítica:** {bateria.get("execucoes_com_diferenca")}  

## Cenários testados

| Cenário | Motor | Status | Preço-teto | Auditoria paralela | Segurança | Diferenças críticas |
|---|---|---|---:|---|---|---:|
{linhas}

## Leitura

Esta bateria testa múltiplos cenários com Legacy e Core Engine.
Ela serve para reduzir o risco antes de considerar o Core Engine como motor padrão.
"""


def executar_autoteste_auditoria_motor_principal() -> List[Dict[str, str]]:
    """
    Executa autotestes da auditoria pós-integração.
    """
    testes = []

    entradas = gerar_entradas_exemplo_auditoria_motor_principal()

    auditoria_legacy = executar_auditoria_motor_principal(
        entradas=entradas,
        motor_selecionado=MOTOR_LEGACY,
        moeda="R$",
        tolerancia=0.0001,
    )

    auditoria_core = executar_auditoria_motor_principal(
        entradas=entradas,
        motor_selecionado=MOTOR_CORE,
        moeda="R$",
        tolerancia=0.0001,
    )

    bateria = executar_bateria_auditoria_motor_principal(
        moeda="R$",
        tolerancia=0.0001,
    )

    testes.append(
        {
            "teste": "auditoria_legacy_executa",
            "status": "OK" if auditoria_legacy.get("resultado_principal", {}).get("preco_teto", 0) != 0 else "FALHA",
            "detalhe": auditoria_legacy.get("classificacao_seguranca", ""),
        }
    )

    testes.append(
        {
            "teste": "auditoria_core_executa",
            "status": "OK" if auditoria_core.get("resultado_principal", {}).get("preco_teto", 0) != 0 else "FALHA",
            "detalhe": auditoria_core.get("classificacao_seguranca", ""),
        }
    )

    testes.append(
        {
            "teste": "auditoria_core_aprovada_para_teste",
            "status": "OK" if auditoria_core.get("aprovado_para_teste_core") else "FALHA",
            "detalhe": f"Diferenças: {len(auditoria_core.get('campos_com_diferenca', []))}",
        }
    )

    testes.append(
        {
            "teste": "bateria_executa",
            "status": "OK" if bateria.get("total_execucoes", 0) > 0 else "FALHA",
            "detalhe": f"Execuções: {bateria.get('total_execucoes')}",
        }
    )

    testes.append(
        {
            "teste": "bateria_sem_diferencas",
            "status": "OK" if bateria.get("bateria_aprovada") else "FALHA",
            "detalhe": f"Diferenças críticas: {bateria.get('execucoes_com_diferenca')}",
        }
    )

    testes.append(
        {
            "teste": "motor_padrao_continua_legacy",
            "status": "OK" if obter_motor_padrao() == MOTOR_LEGACY else "FALHA",
            "detalhe": f"Motor padrão: {obter_motor_padrao()}",
        }
    )

    testes.append(
        {
            "teste": "motores_disponiveis_validos",
            "status": (
                "OK"
                if MOTOR_LEGACY in obter_motores_disponiveis()
                and MOTOR_CORE in obter_motores_disponiveis()
                else "FALHA"
            ),
            "detalhe": ", ".join(obter_motores_disponiveis()),
        }
    )

    return testes