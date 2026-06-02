# motor_valuation_controlado.py

from datetime import datetime
from typing import Any, Dict, List

from valuation import EntradasValuation
from valuation_core_adapter import (
    VERSAO_ADAPTER_CORE,
    calcular_valuation_por_motor,
    comparar_motores_por_entradas,
    gerar_markdown_adapter_core,
    gerar_tabela_comparacao_adapter,
)


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v3.8.6 — Seletor Controlado de Motor
# ------------------------------------------------------------
# Este arquivo centraliza a decisão sobre qual motor de valuation
# deve ser usado pelo app principal.
#
# Motores disponíveis:
# - Legacy: valuation.py
# - Core Engine: core_valuation.py via valuation_core_adapter.py
#
# Objetivo:
# - permitir alternância segura entre motores
# - manter opção de retorno ao motor antigo
# - criar metadados da escolha do motor
# - preparar integração controlada no app.py
# - reduzir risco antes da migração definitiva
# ============================================================


VERSAO_MOTOR_CONTROLADO = "3.8.6"

MOTOR_LEGACY = "Legacy"
MOTOR_CORE = "Core Engine"

MOTORES_DISPONIVEIS = [
    MOTOR_LEGACY,
    MOTOR_CORE,
]


DESCRICAO_MOTORES = {
    MOTOR_LEGACY: {
        "id": "legacy",
        "nome": "Legacy",
        "descricao": "Motor antigo atual do app, localizado em valuation.py.",
        "uso_recomendado": "Uso seguro padrão enquanto a migração ainda está em validação.",
        "risco": "Baixo, pois já é o motor usado pelo app.",
    },
    MOTOR_CORE: {
        "id": "core",
        "nome": "Core Engine",
        "descricao": "Novo motor profissional, localizado em core_valuation.py e acessado via adapter.",
        "uso_recomendado": "Uso controlado após auditorias de compatibilidade aprovadas.",
        "risco": "Baixo/Médio enquanto ainda está em transição. Deve manter comparação com o legacy.",
    },
}


def obter_motores_disponiveis() -> List[str]:
    """
    Retorna os motores disponíveis para seleção futura no app.
    """
    return MOTORES_DISPONIVEIS.copy()


def obter_motor_padrao() -> str:
    """
    Por segurança, o motor padrão continua sendo o Legacy.
    A migração para Core Engine deve ser ativada de forma controlada.
    """
    return MOTOR_LEGACY


def normalizar_motor(motor: str) -> str:
    """
    Normaliza diferentes textos possíveis para os IDs internos usados pelo adapter.
    """
    texto = str(motor).strip().lower()

    if texto in ["core", "core engine", "core_engine", "novo", "motor novo"]:
        return "core"

    return "legacy"


def obter_rotulo_motor_por_id(motor_id: str) -> str:
    """
    Converte ID interno para rótulo visual.
    """
    motor_normalizado = normalizar_motor(motor_id)

    if motor_normalizado == "core":
        return MOTOR_CORE

    return MOTOR_LEGACY


def obter_descricao_motor(motor: str) -> Dict[str, str]:
    """
    Retorna descrição do motor selecionado.
    """
    rotulo = obter_rotulo_motor_por_id(motor)

    return DESCRICAO_MOTORES.get(rotulo, DESCRICAO_MOTORES[MOTOR_LEGACY])


def motor_eh_core(motor: str) -> bool:
    return normalizar_motor(motor) == "core"


def motor_eh_legacy(motor: str) -> bool:
    return normalizar_motor(motor) == "legacy"


def calcular_valuation_controlado(
    entradas: EntradasValuation,
    motor: str = MOTOR_LEGACY,
    moeda: str = "R$",
) -> Dict[str, Any]:
    """
    Calcula valuation usando o motor selecionado.

    Esta função será usada futuramente pelo app.py no lugar da chamada direta:

        calcular_valuation(entradas)

    Ela preserva o formato de saída esperado pelo app, adicionando metadados.
    """
    motor_id = normalizar_motor(motor)

    resultado = calcular_valuation_por_motor(
        entradas=entradas,
        motor=motor_id,
        moeda=moeda,
    )

    resultado_com_contexto = {
        **resultado,
        "motor_selecionado": obter_rotulo_motor_por_id(motor_id),
        "motor_id": motor_id,
        "versao_motor_controlado": VERSAO_MOTOR_CONTROLADO,
        "versao_adapter_core": VERSAO_ADAPTER_CORE,
        "data_calculo_controlado": datetime.now().isoformat(timespec="seconds"),
    }

    return resultado_com_contexto


def auditar_motor_selecionado(
    entradas: EntradasValuation,
    moeda: str = "R$",
    tolerancia: float = 0.0001,
) -> Dict[str, Any]:
    """
    Executa comparação entre Legacy e Core para a mesma entrada.
    Serve para validar se é seguro usar o Core Engine naquela entrada.
    """
    comparacao = comparar_motores_por_entradas(
        entradas=entradas,
        moeda=moeda,
        tolerancia=tolerancia,
    )

    return {
        **comparacao,
        "versao_motor_controlado": VERSAO_MOTOR_CONTROLADO,
        "versao_adapter_core": VERSAO_ADAPTER_CORE,
        "data_auditoria_controlada": datetime.now().isoformat(timespec="seconds"),
    }


def gerar_resumo_motor_controlado(
    motor: str,
    resultado: Dict[str, Any],
) -> Dict[str, str]:
    """
    Gera resumo amigável do motor usado no cálculo.
    """
    descricao = obter_descricao_motor(motor)

    return {
        "Motor selecionado": str(resultado.get("motor_selecionado", descricao["nome"])),
        "ID interno": str(resultado.get("motor_id", descricao["id"])),
        "Descrição": descricao["descricao"],
        "Uso recomendado": descricao["uso_recomendado"],
        "Risco": descricao["risco"],
        "Versão controlador": str(resultado.get("versao_motor_controlado", VERSAO_MOTOR_CONTROLADO)),
        "Versão adapter": str(resultado.get("versao_adapter_core", VERSAO_ADAPTER_CORE)),
        "Data do cálculo": str(resultado.get("data_calculo_controlado", "")),
    }


def gerar_tabela_auditoria_motor_controlado(
    auditoria: Dict[str, Any],
) -> List[Dict[str, str]]:
    """
    Reaproveita a tabela de comparação do adapter para exibir auditoria.
    """
    return gerar_tabela_comparacao_adapter(auditoria)


def gerar_markdown_motor_controlado(
    motor: str,
    resultado: Dict[str, Any],
    auditoria: Dict[str, Any],
) -> str:
    """
    Gera relatório técnico do uso do motor controlado.
    """
    resumo = gerar_resumo_motor_controlado(
        motor=motor,
        resultado=resultado,
    )

    linhas_resumo = "\n".join(
        [
            f"| {chave} | {valor} |"
            for chave, valor in resumo.items()
        ]
    )

    linhas_comparacao = "\n".join(
        [
            f"| {linha['Campo']} | {linha['Legacy']} | {linha['Core']} | {linha['Diferença']} | {linha['Compatível']} | {linha['Tipo']} |"
            for linha in gerar_tabela_auditoria_motor_controlado(auditoria)
        ]
    )

    status_auditoria = "APROVADA" if auditoria.get("aprovado") else "REPROVADA"

    return f"""# Relatório do Motor Controlado

Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Resumo do motor usado

| Campo | Valor |
|---|---|
{linhas_resumo}

## Resultado da auditoria paralela

**Status:** {status_auditoria}  
**Tolerância:** {auditoria.get("tolerancia")}  
**Diferenças críticas:** {len(auditoria.get("campos_com_diferenca", []))}  

## Comparação Legacy vs Core

| Campo | Legacy | Core | Diferença | Compatível | Tipo |
|---|---:|---:|---:|---|---|
{linhas_comparacao}

## Leitura

O seletor controlado permite alternar entre o motor Legacy e o Core Engine
sem alterar a interface principal do app.

Enquanto a migração estiver em andamento, o Legacy continua sendo o padrão seguro.
O Core Engine pode ser ativado de forma controlada após auditorias aprovadas.
"""


def gerar_entradas_exemplo_motor_controlado() -> EntradasValuation:
    """
    Gera entradas de exemplo para testar o seletor controlado.
    """
    return EntradasValuation(
        empresa="Empresa Exemplo Motor Controlado",
        ticker="CTRL3",
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


def executar_autoteste_motor_controlado() -> List[Dict[str, str]]:
    """
    Executa autotestes básicos do seletor controlado.
    """
    testes = []
    entradas = gerar_entradas_exemplo_motor_controlado()

    resultado_legacy = calcular_valuation_controlado(
        entradas=entradas,
        motor=MOTOR_LEGACY,
        moeda="R$",
    )

    resultado_core = calcular_valuation_controlado(
        entradas=entradas,
        motor=MOTOR_CORE,
        moeda="R$",
    )

    auditoria = auditar_motor_selecionado(
        entradas=entradas,
        moeda="R$",
        tolerancia=0.0001,
    )

    testes.append(
        {
            "teste": "motor_legacy_controlado_calcula",
            "status": "OK" if resultado_legacy.get("preco_teto", 0) != 0 else "FALHA",
            "detalhe": f"Status: {resultado_legacy.get('status')}",
        }
    )

    testes.append(
        {
            "teste": "motor_core_controlado_calcula",
            "status": "OK" if resultado_core.get("preco_teto", 0) != 0 else "FALHA",
            "detalhe": f"Status: {resultado_core.get('status')}",
        }
    )

    testes.append(
        {
            "teste": "normalizacao_motor_core",
            "status": "OK" if normalizar_motor("Core Engine") == "core" else "FALHA",
            "detalhe": f"Resultado: {normalizar_motor('Core Engine')}",
        }
    )

    testes.append(
        {
            "teste": "normalizacao_motor_legacy",
            "status": "OK" if normalizar_motor("Legacy") == "legacy" else "FALHA",
            "detalhe": f"Resultado: {normalizar_motor('Legacy')}",
        }
    )

    testes.append(
        {
            "teste": "auditoria_controlada_aprovada",
            "status": "OK" if auditoria.get("aprovado") else "FALHA",
            "detalhe": f"Diferenças críticas: {len(auditoria.get('campos_com_diferenca', []))}",
        }
    )

    testes.append(
        {
            "teste": "resultado_tem_metadados_motor",
            "status": (
                "OK"
                if "motor_selecionado" in resultado_core
                and "versao_motor_controlado" in resultado_core
                else "FALHA"
            ),
            "detalhe": f"Motor: {resultado_core.get('motor_selecionado')}",
        }
    )

    return testes