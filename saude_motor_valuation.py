# saude_motor_valuation.py

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from logs_motor_valuation import (
    CAMINHO_LOGS_MOTOR,
    carregar_logs_motor,
)


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v3.8.17 — Saúde Técnica do Motor de Valuation
# ------------------------------------------------------------
# Este arquivo interpreta os logs do motor e transforma dados
# técnicos em diagnóstico de estabilidade.
#
# Objetivo:
# - medir saúde do motor
# - medir taxa de erros
# - medir taxa de fallback
# - medir uso de Core Engine e Legacy
# - gerar score técnico
# - avaliar prontidão do Core Engine para virar padrão
# - preparar painel estratégico de saúde do motor
# ============================================================


VERSAO_SAUDE_MOTOR = "3.8.17"


STATUS_SAUDE_SEM_DADOS = "SEM_DADOS"
STATUS_SAUDE_SAUDAVEL = "SAUDAVEL"
STATUS_SAUDE_OBSERVACAO = "EM_OBSERVACAO"
STATUS_SAUDE_ATENCAO = "ATENCAO"
STATUS_SAUDE_CRITICO = "CRITICO"


PRONTIDAO_SEM_DADOS = "SEM_DADOS"
PRONTIDAO_NAO_PRONTO = "NAO_PRONTO"
PRONTIDAO_EM_OBSERVACAO = "EM_OBSERVACAO"
PRONTIDAO_TESTE_CONTROLADO = "PRONTO_PARA_TESTE_CONTROLADO"
PRONTIDAO_CORE_PADRAO = "POTENCIALMENTE_PRONTO_PARA_CORE_PADRAO"


def _agora_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _safe_float(valor: Any, default: float = 0.0) -> float:
    try:
        return float(valor)
    except (TypeError, ValueError):
        return default


def _safe_str(valor: Any) -> str:
    if valor is None:
        return ""

    return str(valor).strip()


def _percentual(parte: float, total: float) -> float:
    if total <= 0:
        return 0.0

    return round((parte / total) * 100, 2)


def _eh_sim(valor: Any) -> bool:
    return _safe_str(valor).lower() in ["sim", "true", "1", "yes"]


def _normalizar_motor(valor: Any) -> str:
    texto = _safe_str(valor).lower()

    if texto in ["core", "core engine", "core_engine"]:
        return "Core Engine"

    if texto in ["legacy", "motor antigo"]:
        return "Legacy"

    return _safe_str(valor)


def gerar_metricas_saude_motor(
    logs: List[Dict[str, str]],
) -> Dict[str, Any]:
    """
    Gera métricas quantitativas a partir dos logs do motor.
    """
    total = len(logs)

    if total == 0:
        return {
            "total_logs": 0,
            "execucoes_ok": 0,
            "execucoes_erro": 0,
            "fallbacks": 0,
            "legacy_preferido": 0,
            "core_preferido": 0,
            "legacy_executado": 0,
            "core_executado": 0,
            "taxa_erro": 0.0,
            "taxa_fallback": 0.0,
            "taxa_core_preferido": 0.0,
            "taxa_core_executado": 0.0,
            "taxa_legacy_executado": 0.0,
            "ultimo_log": "",
            "primeiro_log_da_amostra": "",
            "preco_teto_medio": 0.0,
            "quantidade_empresas_distintas": 0,
            "tickers_distintos": 0,
        }

    execucoes_ok = len(
        [
            log for log in logs
            if _safe_str(log.get("status_execucao")).upper() == "OK"
        ]
    )

    execucoes_erro = len(
        [
            log for log in logs
            if _safe_str(log.get("status_execucao")).upper() == "ERRO"
        ]
    )

    fallbacks = len(
        [
            log for log in logs
            if _eh_sim(log.get("fallback_ocorreu"))
        ]
    )

    legacy_preferido = len(
        [
            log for log in logs
            if _normalizar_motor(log.get("motor_preferido")) == "Legacy"
        ]
    )

    core_preferido = len(
        [
            log for log in logs
            if _normalizar_motor(log.get("motor_preferido")) == "Core Engine"
        ]
    )

    legacy_executado = len(
        [
            log for log in logs
            if _normalizar_motor(log.get("motor_executado")) == "Legacy"
        ]
    )

    core_executado = len(
        [
            log for log in logs
            if _normalizar_motor(log.get("motor_executado")) == "Core Engine"
        ]
    )

    precos_teto = [
        _safe_float(log.get("preco_teto", 0))
        for log in logs
        if _safe_float(log.get("preco_teto", 0)) > 0
    ]

    preco_teto_medio = (
        round(sum(precos_teto) / len(precos_teto), 2)
        if len(precos_teto) > 0
        else 0.0
    )

    empresas = {
        _safe_str(log.get("empresa"))
        for log in logs
        if _safe_str(log.get("empresa")) != ""
    }

    tickers = {
        _safe_str(log.get("ticker")).upper()
        for log in logs
        if _safe_str(log.get("ticker")) != ""
    }

    return {
        "total_logs": total,
        "execucoes_ok": execucoes_ok,
        "execucoes_erro": execucoes_erro,
        "fallbacks": fallbacks,
        "legacy_preferido": legacy_preferido,
        "core_preferido": core_preferido,
        "legacy_executado": legacy_executado,
        "core_executado": core_executado,
        "taxa_erro": _percentual(execucoes_erro, total),
        "taxa_fallback": _percentual(fallbacks, total),
        "taxa_core_preferido": _percentual(core_preferido, total),
        "taxa_core_executado": _percentual(core_executado, total),
        "taxa_legacy_executado": _percentual(legacy_executado, total),
        "ultimo_log": logs[0].get("data_execucao", ""),
        "primeiro_log_da_amostra": logs[-1].get("data_execucao", ""),
        "preco_teto_medio": preco_teto_medio,
        "quantidade_empresas_distintas": len(empresas),
        "tickers_distintos": len(tickers),
    }


def calcular_score_saude_motor(
    metricas: Dict[str, Any],
) -> int:
    """
    Calcula score técnico de 0 a 100.

    Quanto maior:
    - menos erros
    - menos fallback
    - mais estabilidade operacional
    """
    total = int(metricas.get("total_logs", 0))

    if total == 0:
        return 0

    taxa_erro = _safe_float(metricas.get("taxa_erro", 0))
    taxa_fallback = _safe_float(metricas.get("taxa_fallback", 0))

    score = 100

    score -= taxa_erro * 4
    score -= taxa_fallback * 2

    if total < 5:
        score -= 20
    elif total < 10:
        score -= 10

    if metricas.get("execucoes_erro", 0) > 0:
        score -= 10

    if metricas.get("fallbacks", 0) > 0:
        score -= 5

    score_final = max(0, min(100, round(score)))

    return int(score_final)


def classificar_saude_motor(
    metricas: Dict[str, Any],
    score: int,
) -> str:
    """
    Classifica a saúde geral do motor.
    """
    total = int(metricas.get("total_logs", 0))
    taxa_erro = _safe_float(metricas.get("taxa_erro", 0))
    taxa_fallback = _safe_float(metricas.get("taxa_fallback", 0))

    if total == 0:
        return STATUS_SAUDE_SEM_DADOS

    if taxa_erro >= 10 or taxa_fallback >= 30 or score < 50:
        return STATUS_SAUDE_CRITICO

    if taxa_erro > 0 or taxa_fallback >= 10 or score < 75:
        return STATUS_SAUDE_ATENCAO

    if taxa_fallback > 0 or total < 10 or score < 90:
        return STATUS_SAUDE_OBSERVACAO

    return STATUS_SAUDE_SAUDAVEL


def classificar_prontidao_core(
    metricas: Dict[str, Any],
    score: int,
    status_saude: str,
) -> str:
    """
    Avalia se o Core Engine está pronto para ser usado como padrão.
    """
    total = int(metricas.get("total_logs", 0))
    core_executado = int(metricas.get("core_executado", 0))
    core_preferido = int(metricas.get("core_preferido", 0))
    execucoes_erro = int(metricas.get("execucoes_erro", 0))
    fallbacks = int(metricas.get("fallbacks", 0))

    if total == 0:
        return PRONTIDAO_SEM_DADOS

    if execucoes_erro > 0:
        return PRONTIDAO_NAO_PRONTO

    if fallbacks > 0:
        return PRONTIDAO_NAO_PRONTO

    if core_preferido == 0 or core_executado == 0:
        return PRONTIDAO_EM_OBSERVACAO

    if total >= 30 and core_executado >= 10 and score >= 95 and status_saude == STATUS_SAUDE_SAUDAVEL:
        return PRONTIDAO_CORE_PADRAO

    if total >= 10 and core_executado >= 3 and score >= 90:
        return PRONTIDAO_TESTE_CONTROLADO

    return PRONTIDAO_EM_OBSERVACAO


def gerar_leitura_saude_motor(
    status_saude: str,
    prontidao_core: str,
    metricas: Dict[str, Any],
    score: int,
) -> str:
    """
    Gera leitura executiva do estado técnico do motor.
    """
    total = int(metricas.get("total_logs", 0))
    taxa_erro = _safe_float(metricas.get("taxa_erro", 0))
    taxa_fallback = _safe_float(metricas.get("taxa_fallback", 0))

    if status_saude == STATUS_SAUDE_SEM_DADOS:
        return (
            "Ainda não há logs suficientes para avaliar a saúde do motor. "
            "Execute cálculos reais no app para construir histórico técnico."
        )

    if status_saude == STATUS_SAUDE_CRITICO:
        return (
            f"Estado crítico. A amostra tem {total} logs, taxa de erro de {taxa_erro}% "
            f"e taxa de fallback de {taxa_fallback}%. Não avance a migração do Core Engine."
        )

    if status_saude == STATUS_SAUDE_ATENCAO:
        return (
            f"Estado de atenção. O motor funciona, mas a amostra mostra sinais de instabilidade. "
            f"Score atual: {score}. Core Engine ainda não deve virar padrão."
        )

    if status_saude == STATUS_SAUDE_OBSERVACAO:
        return (
            f"Estado em observação. O motor está operacional, mas ainda precisa de mais histórico "
            f"ou menor dependência de fallback. Prontidão Core: {prontidao_core}."
        )

    return (
        f"Estado saudável. O motor apresentou estabilidade na amostra avaliada. "
        f"Score técnico: {score}. Prontidão Core: {prontidao_core}."
    )


def gerar_checklist_saude_motor(
    metricas: Dict[str, Any],
    score: int,
    status_saude: str,
    prontidao_core: str,
) -> List[Dict[str, str]]:
    """
    Gera checklist de decisão técnica.
    """
    total = int(metricas.get("total_logs", 0))
    execucoes_erro = int(metricas.get("execucoes_erro", 0))
    fallbacks = int(metricas.get("fallbacks", 0))
    core_executado = int(metricas.get("core_executado", 0))

    return [
        {
            "Critério": "Existem logs suficientes?",
            "Status": "OK" if total >= 10 else "OBSERVAR",
            "Detalhe": f"Logs avaliados: {total}. Ideal mínimo: 10.",
        },
        {
            "Critério": "Há erros técnicos?",
            "Status": "OK" if execucoes_erro == 0 else "FALHA",
            "Detalhe": f"Execuções com erro: {execucoes_erro}.",
        },
        {
            "Critério": "Houve fallback?",
            "Status": "OK" if fallbacks == 0 else "ATENÇÃO",
            "Detalhe": f"Fallbacks detectados: {fallbacks}.",
        },
        {
            "Critério": "Core Engine já foi executado?",
            "Status": "OK" if core_executado > 0 else "OBSERVAR",
            "Detalhe": f"Execuções com Core Engine: {core_executado}.",
        },
        {
            "Critério": "Score técnico é forte?",
            "Status": "OK" if score >= 90 else "OBSERVAR",
            "Detalhe": f"Score atual: {score}/100.",
        },
        {
            "Critério": "Saúde geral está boa?",
            "Status": "OK" if status_saude == STATUS_SAUDE_SAUDAVEL else "OBSERVAR",
            "Detalhe": f"Classificação atual: {status_saude}.",
        },
        {
            "Critério": "Core pode virar padrão?",
            "Status": (
                "OK"
                if prontidao_core == PRONTIDAO_CORE_PADRAO
                else "NÃO"
            ),
            "Detalhe": f"Prontidão atual: {prontidao_core}.",
        },
    ]


def analisar_saude_motor(
    logs: List[Dict[str, str]],
) -> Dict[str, Any]:
    """
    Executa análise completa de saúde do motor.
    """
    metricas = gerar_metricas_saude_motor(logs)
    score = calcular_score_saude_motor(metricas)
    status_saude = classificar_saude_motor(metricas, score)
    prontidao_core = classificar_prontidao_core(metricas, score, status_saude)

    checklist = gerar_checklist_saude_motor(
        metricas=metricas,
        score=score,
        status_saude=status_saude,
        prontidao_core=prontidao_core,
    )

    return {
        "versao_saude_motor": VERSAO_SAUDE_MOTOR,
        "data_analise": _agora_iso(),
        "metricas": metricas,
        "score_saude": score,
        "status_saude": status_saude,
        "prontidao_core": prontidao_core,
        "leitura": gerar_leitura_saude_motor(
            status_saude=status_saude,
            prontidao_core=prontidao_core,
            metricas=metricas,
            score=score,
        ),
        "checklist": checklist,
    }


def analisar_saude_motor_por_arquivo(
    caminho_logs: Optional[Path] = None,
    limite: int = 300,
) -> Dict[str, Any]:
    """
    Carrega logs de arquivo e executa análise completa.
    """
    caminho = Path(caminho_logs) if caminho_logs is not None else CAMINHO_LOGS_MOTOR

    logs = carregar_logs_motor(
        caminho=caminho,
        limite=limite,
    )

    analise = analisar_saude_motor(logs)

    return {
        **analise,
        "caminho_logs": str(caminho),
        "limite_logs": limite,
    }


def gerar_tabela_metricas_saude_motor(
    analise: Dict[str, Any],
) -> List[Dict[str, str]]:
    """
    Gera tabela amigável com métricas principais.
    """
    metricas = analise.get("metricas", {})

    return [
        {"Indicador": "Score de saúde", "Valor": f"{analise.get('score_saude', 0)}/100"},
        {"Indicador": "Status de saúde", "Valor": str(analise.get("status_saude", ""))},
        {"Indicador": "Prontidão Core", "Valor": str(analise.get("prontidao_core", ""))},
        {"Indicador": "Total de logs", "Valor": str(metricas.get("total_logs", 0))},
        {"Indicador": "Execuções OK", "Valor": str(metricas.get("execucoes_ok", 0))},
        {"Indicador": "Execuções com erro", "Valor": str(metricas.get("execucoes_erro", 0))},
        {"Indicador": "Fallbacks", "Valor": str(metricas.get("fallbacks", 0))},
        {"Indicador": "Taxa de erro", "Valor": f"{metricas.get('taxa_erro', 0)}%"},
        {"Indicador": "Taxa de fallback", "Valor": f"{metricas.get('taxa_fallback', 0)}%"},
        {"Indicador": "Core preferido", "Valor": str(metricas.get("core_preferido", 0))},
        {"Indicador": "Core executado", "Valor": str(metricas.get("core_executado", 0))},
        {"Indicador": "Legacy executado", "Valor": str(metricas.get("legacy_executado", 0))},
        {"Indicador": "Empresas distintas", "Valor": str(metricas.get("quantidade_empresas_distintas", 0))},
        {"Indicador": "Tickers distintos", "Valor": str(metricas.get("tickers_distintos", 0))},
        {"Indicador": "Último log", "Valor": str(metricas.get("ultimo_log", ""))},
    ]


def gerar_markdown_saude_motor(
    analise: Dict[str, Any],
) -> str:
    """
    Gera relatório markdown da saúde do motor.
    """
    metricas_tabela = gerar_tabela_metricas_saude_motor(analise)
    checklist = analise.get("checklist", [])

    linhas_metricas = "\n".join(
        [
            f"| {linha['Indicador']} | {linha['Valor']} |"
            for linha in metricas_tabela
        ]
    )

    linhas_checklist = "\n".join(
        [
            f"| {linha['Critério']} | {linha['Status']} | {linha['Detalhe']} |"
            for linha in checklist
        ]
    )

    return f"""# Relatório de Saúde Técnica do Motor

Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Diagnóstico geral

**Score:** {analise.get("score_saude")}/100  
**Status:** {analise.get("status_saude")}  
**Prontidão Core Engine:** {analise.get("prontidao_core")}  

## Leitura executiva

{analise.get("leitura", "")}

## Métricas

| Indicador | Valor |
|---|---|
{linhas_metricas}

## Checklist técnico

| Critério | Status | Detalhe |
|---|---|---|
{linhas_checklist}

## Decisão recomendada

Enquanto houver erros técnicos, fallbacks recorrentes ou pouca amostra de uso real,
o Core Engine deve continuar em teste controlado e o Legacy deve permanecer como proteção.

O Core Engine só deve virar padrão quando houver amostra suficiente, score alto,
zero erros críticos e zero fallbacks recentes.
"""


def criar_logs_sinteticos_saudaveis() -> List[Dict[str, str]]:
    """
    Cria logs sintéticos para autoteste saudável.
    """
    logs = []

    for indice in range(12):
        logs.append(
            {
                "data_execucao": f"2026-01-01T12:{indice:02d}:00",
                "empresa": "Empresa Teste",
                "ticker": f"TST{indice}",
                "status_execucao": "OK",
                "status_valuation": "COMPRA",
                "preco_teto": "25.50",
                "preco_justo_combinado": "35.00",
                "motor_preferido": "Core Engine" if indice >= 6 else "Legacy",
                "motor_executado": "Core Engine" if indice >= 6 else "Legacy",
                "fallback_ocorreu": "Não",
            }
        )

    return list(reversed(logs))


def criar_logs_sinteticos_com_alerta() -> List[Dict[str, str]]:
    """
    Cria logs sintéticos com erro e fallback.
    """
    logs = criar_logs_sinteticos_saudaveis()

    logs[0]["fallback_ocorreu"] = "Sim"
    logs[0]["motor_preferido"] = "Core Engine"
    logs[0]["motor_executado"] = "Legacy"

    logs[1]["status_execucao"] = "ERRO"
    logs[1]["erro_execucao"] = "Erro sintético."

    return logs


def executar_autoteste_saude_motor() -> List[Dict[str, str]]:
    """
    Executa autotestes da análise de saúde do motor.
    """
    testes = []

    logs_saudaveis = criar_logs_sinteticos_saudaveis()
    analise_saudavel = analisar_saude_motor(logs_saudaveis)

    testes.append(
        {
            "teste": "analise_saudavel_executa",
            "status": "OK" if analise_saudavel.get("score_saude", 0) > 0 else "FALHA",
            "detalhe": f"Score: {analise_saudavel.get('score_saude')}",
        }
    )

    testes.append(
        {
            "teste": "analise_saudavel_sem_erros",
            "status": (
                "OK"
                if analise_saudavel.get("metricas", {}).get("execucoes_erro") == 0
                else "FALHA"
            ),
            "detalhe": f"Erros: {analise_saudavel.get('metricas', {}).get('execucoes_erro')}",
        }
    )

    testes.append(
        {
            "teste": "core_tem_prontidao_minima",
            "status": (
                "OK"
                if analise_saudavel.get("prontidao_core")
                in [
                    PRONTIDAO_TESTE_CONTROLADO,
                    PRONTIDAO_CORE_PADRAO,
                    PRONTIDAO_EM_OBSERVACAO,
                ]
                else "FALHA"
            ),
            "detalhe": f"Prontidão: {analise_saudavel.get('prontidao_core')}",
        }
    )

    logs_alerta = criar_logs_sinteticos_com_alerta()
    analise_alerta = analisar_saude_motor(logs_alerta)

    testes.append(
        {
            "teste": "analise_alerta_detecta_erro",
            "status": (
                "OK"
                if analise_alerta.get("metricas", {}).get("execucoes_erro", 0) > 0
                else "FALHA"
            ),
            "detalhe": f"Erros: {analise_alerta.get('metricas', {}).get('execucoes_erro')}",
        }
    )

    testes.append(
        {
            "teste": "analise_alerta_detecta_fallback",
            "status": (
                "OK"
                if analise_alerta.get("metricas", {}).get("fallbacks", 0) > 0
                else "FALHA"
            ),
            "detalhe": f"Fallbacks: {analise_alerta.get('metricas', {}).get('fallbacks')}",
        }
    )

    tabela = gerar_tabela_metricas_saude_motor(analise_saudavel)

    testes.append(
        {
            "teste": "tabela_metricas_gerada",
            "status": "OK" if len(tabela) > 0 else "FALHA",
            "detalhe": f"Linhas: {len(tabela)}",
        }
    )

    markdown = gerar_markdown_saude_motor(analise_saudavel)

    testes.append(
        {
            "teste": "markdown_saude_gerado",
            "status": "OK" if "# Relatório de Saúde Técnica do Motor" in markdown else "FALHA",
            "detalhe": "Relatório markdown criado.",
        }
    )

    analise_arquivo = analisar_saude_motor_por_arquivo(
        caminho_logs=CAMINHO_LOGS_MOTOR,
        limite=50,
    )

    testes.append(
        {
            "teste": "analise_por_arquivo_nao_quebra",
            "status": "OK" if "status_saude" in analise_arquivo else "FALHA",
            "detalhe": f"Status: {analise_arquivo.get('status_saude')}",
        }
    )

    return testes