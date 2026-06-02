# decisao_core_engine.py

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from logs_motor_valuation import (
    CAMINHO_LOGS_MOTOR,
    carregar_logs_motor,
)
from saude_motor_valuation import (
    VERSAO_SAUDE_MOTOR,
    STATUS_SAUDE_SEM_DADOS,
    STATUS_SAUDE_SAUDAVEL,
    STATUS_SAUDE_OBSERVACAO,
    STATUS_SAUDE_ATENCAO,
    STATUS_SAUDE_CRITICO,
    PRONTIDAO_SEM_DADOS,
    PRONTIDAO_NAO_PRONTO,
    PRONTIDAO_EM_OBSERVACAO,
    PRONTIDAO_TESTE_CONTROLADO,
    PRONTIDAO_CORE_PADRAO,
    analisar_saude_motor,
    analisar_saude_motor_por_arquivo,
    criar_logs_sinteticos_saudaveis,
    criar_logs_sinteticos_com_alerta,
)


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v3.8.19 — Decisão Controlada do Core Engine
# ------------------------------------------------------------
# Este arquivo transforma saúde técnica em decisão operacional.
#
# Objetivo:
# - decidir se o Core Engine pode continuar em teste
# - decidir se o Core pode ser usado com mais frequência
# - decidir se o Core pode ser promovido futuramente
# - impedir promoção arriscada
# - gerar recomendação objetiva para o fundador
# - preparar governança técnica da migração Legacy -> Core
# ============================================================


VERSAO_DECISAO_CORE_ENGINE = "3.8.19"


DECISAO_SEM_DADOS = "SEM_DADOS"
DECISAO_MANTER_LEGACY = "MANTER_LEGACY"
DECISAO_CONTINUAR_TESTE_CONTROLADO = "CONTINUAR_TESTE_CONTROLADO"
DECISAO_AUMENTAR_TESTES_CORE = "AUMENTAR_TESTES_CORE"
DECISAO_CORE_PODE_SER_PROMOVIDO_COM_FALLBACK = "CORE_PODE_SER_PROMOVIDO_COM_FALLBACK"
DECISAO_NAO_PROMOVER_CORE = "NAO_PROMOVER_CORE"


RISCO_BAIXO = "BAIXO"
RISCO_MODERADO = "MODERADO"
RISCO_ALTO = "ALTO"
RISCO_CRITICO = "CRITICO"
RISCO_INDEFINIDO = "INDEFINIDO"


def _agora_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _safe_float(valor: Any, default: float = 0.0) -> float:
    try:
        return float(valor)
    except (TypeError, ValueError):
        return default


def _safe_int(valor: Any, default: int = 0) -> int:
    try:
        return int(valor)
    except (TypeError, ValueError):
        return default


def _safe_str(valor: Any) -> str:
    if valor is None:
        return ""

    return str(valor).strip()


def _bool_texto(valor: bool) -> str:
    return "Sim" if valor else "Não"


def calcular_nivel_risco_core(
    analise_saude: Dict[str, Any],
) -> str:
    """
    Classifica o risco técnico de promover ou ampliar o Core Engine.
    """
    status_saude = _safe_str(analise_saude.get("status_saude"))
    prontidao_core = _safe_str(analise_saude.get("prontidao_core"))
    score = _safe_int(analise_saude.get("score_saude", 0))
    metricas = analise_saude.get("metricas", {})

    total_logs = _safe_int(metricas.get("total_logs", 0))
    execucoes_erro = _safe_int(metricas.get("execucoes_erro", 0))
    fallbacks = _safe_int(metricas.get("fallbacks", 0))
    core_executado = _safe_int(metricas.get("core_executado", 0))

    if total_logs == 0 or prontidao_core == PRONTIDAO_SEM_DADOS:
        return RISCO_INDEFINIDO

    if status_saude == STATUS_SAUDE_CRITICO or execucoes_erro > 0:
        return RISCO_CRITICO

    if fallbacks > 0:
        return RISCO_ALTO

    if status_saude == STATUS_SAUDE_ATENCAO:
        return RISCO_ALTO

    if status_saude == STATUS_SAUDE_OBSERVACAO:
        return RISCO_MODERADO

    if score >= 95 and core_executado >= 10 and status_saude == STATUS_SAUDE_SAUDAVEL:
        return RISCO_BAIXO

    if score >= 90 and core_executado >= 3:
        return RISCO_MODERADO

    return RISCO_MODERADO


def decidir_status_core_engine(
    analise_saude: Dict[str, Any],
) -> str:
    """
    Decide a ação principal com base na saúde técnica.
    """
    status_saude = _safe_str(analise_saude.get("status_saude"))
    prontidao_core = _safe_str(analise_saude.get("prontidao_core"))
    score = _safe_int(analise_saude.get("score_saude", 0))
    metricas = analise_saude.get("metricas", {})

    total_logs = _safe_int(metricas.get("total_logs", 0))
    execucoes_erro = _safe_int(metricas.get("execucoes_erro", 0))
    fallbacks = _safe_int(metricas.get("fallbacks", 0))
    core_executado = _safe_int(metricas.get("core_executado", 0))
    core_preferido = _safe_int(metricas.get("core_preferido", 0))

    if total_logs == 0 or status_saude == STATUS_SAUDE_SEM_DADOS:
        return DECISAO_SEM_DADOS

    if status_saude == STATUS_SAUDE_CRITICO:
        return DECISAO_NAO_PROMOVER_CORE

    if execucoes_erro > 0 or fallbacks > 0:
        return DECISAO_MANTER_LEGACY

    if prontidao_core == PRONTIDAO_NAO_PRONTO:
        return DECISAO_MANTER_LEGACY

    if prontidao_core == PRONTIDAO_CORE_PADRAO:
        return DECISAO_CORE_PODE_SER_PROMOVIDO_COM_FALLBACK

    if prontidao_core == PRONTIDAO_TESTE_CONTROLADO:
        return DECISAO_AUMENTAR_TESTES_CORE

    if core_executado > 0 and core_preferido > 0 and score >= 85:
        return DECISAO_CONTINUAR_TESTE_CONTROLADO

    return DECISAO_CONTINUAR_TESTE_CONTROLADO


def gerar_leitura_decisao_core(
    decisao: str,
    risco: str,
    analise_saude: Dict[str, Any],
) -> str:
    """
    Gera leitura executiva para a decisão do Core Engine.
    """
    metricas = analise_saude.get("metricas", {})
    score = _safe_int(analise_saude.get("score_saude", 0))
    total_logs = _safe_int(metricas.get("total_logs", 0))
    erros = _safe_int(metricas.get("execucoes_erro", 0))
    fallbacks = _safe_int(metricas.get("fallbacks", 0))
    core_executado = _safe_int(metricas.get("core_executado", 0))

    if decisao == DECISAO_SEM_DADOS:
        return (
            "Ainda não há dados suficientes para decidir sobre o Core Engine. "
            "Continue usando Legacy como padrão e gere mais logs reais no fluxo principal."
        )

    if decisao == DECISAO_NAO_PROMOVER_CORE:
        return (
            f"Não promova o Core Engine. A saúde técnica apresenta risco relevante. "
            f"Score: {score}/100, logs avaliados: {total_logs}, erros: {erros}, fallbacks: {fallbacks}."
        )

    if decisao == DECISAO_MANTER_LEGACY:
        return (
            f"Mantenha Legacy como motor padrão. O sistema até pode testar o Core no Modo Fundador, "
            f"mas existem sinais que impedem promoção segura. Erros: {erros}, fallbacks: {fallbacks}, risco: {risco}."
        )

    if decisao == DECISAO_CONTINUAR_TESTE_CONTROLADO:
        return (
            f"Continue com teste controlado. O Core Engine pode ser usado no Modo Fundador, "
            f"mas ainda não há evidência suficiente para ampliar o uso. Core executado: {core_executado} vezes."
        )

    if decisao == DECISAO_AUMENTAR_TESTES_CORE:
        return (
            f"O Core Engine já apresenta condição para testes mais frequentes no Modo Fundador. "
            f"Ainda mantenha fallback ativo e não libere como padrão para usuários comuns."
        )

    if decisao == DECISAO_CORE_PODE_SER_PROMOVIDO_COM_FALLBACK:
        return (
            "O Core Engine está potencialmente pronto para ser promovido em uma versão controlada, "
            "desde que o fallback para Legacy permaneça ativo e exista plano de rollback."
        )

    return "Decisão não classificada. Revise manualmente os indicadores técnicos."


def gerar_acao_recomendada_core(
    decisao: str,
) -> str:
    """
    Converte decisão técnica em ação prática.
    """
    if decisao == DECISAO_SEM_DADOS:
        return "Coletar mais logs antes de decidir."

    if decisao == DECISAO_NAO_PROMOVER_CORE:
        return "Investigar erros, revisar divergências e manter Legacy como padrão."

    if decisao == DECISAO_MANTER_LEGACY:
        return "Manter Legacy como padrão e testar Core apenas no Modo Fundador."

    if decisao == DECISAO_CONTINUAR_TESTE_CONTROLADO:
        return "Continuar testes internos com Core Engine e fallback ativo."

    if decisao == DECISAO_AUMENTAR_TESTES_CORE:
        return "Usar Core com mais frequência no Modo Fundador e monitorar logs."

    if decisao == DECISAO_CORE_PODE_SER_PROMOVIDO_COM_FALLBACK:
        return "Preparar versão controlada para tornar Core padrão apenas com fallback e rollback."

    return "Revisar decisão manualmente."


def gerar_condicoes_para_promocao_core(
    analise_saude: Dict[str, Any],
) -> List[Dict[str, str]]:
    """
    Gera condições objetivas para promoção do Core Engine.
    """
    metricas = analise_saude.get("metricas", {})
    score = _safe_int(analise_saude.get("score_saude", 0))
    status_saude = _safe_str(analise_saude.get("status_saude"))
    prontidao_core = _safe_str(analise_saude.get("prontidao_core"))

    total_logs = _safe_int(metricas.get("total_logs", 0))
    erros = _safe_int(metricas.get("execucoes_erro", 0))
    fallbacks = _safe_int(metricas.get("fallbacks", 0))
    core_executado = _safe_int(metricas.get("core_executado", 0))

    return [
        {
            "Condição": "Amostra mínima de logs",
            "Status": "OK" if total_logs >= 30 else "PENDENTE",
            "Detalhe": f"{total_logs}/30 logs mínimos.",
        },
        {
            "Condição": "Execuções com Core Engine",
            "Status": "OK" if core_executado >= 10 else "PENDENTE",
            "Detalhe": f"{core_executado}/10 execuções mínimas com Core.",
        },
        {
            "Condição": "Zero erros técnicos",
            "Status": "OK" if erros == 0 else "FALHA",
            "Detalhe": f"Erros detectados: {erros}.",
        },
        {
            "Condição": "Zero fallbacks recentes",
            "Status": "OK" if fallbacks == 0 else "FALHA",
            "Detalhe": f"Fallbacks detectados: {fallbacks}.",
        },
        {
            "Condição": "Score técnico alto",
            "Status": "OK" if score >= 95 else "PENDENTE",
            "Detalhe": f"Score atual: {score}/100. Mínimo ideal: 95.",
        },
        {
            "Condição": "Saúde geral saudável",
            "Status": "OK" if status_saude == STATUS_SAUDE_SAUDAVEL else "PENDENTE",
            "Detalhe": f"Status atual: {status_saude}.",
        },
        {
            "Condição": "Prontidão Core padrão",
            "Status": "OK" if prontidao_core == PRONTIDAO_CORE_PADRAO else "PENDENTE",
            "Detalhe": f"Prontidão atual: {prontidao_core}.",
        },
    ]


def pode_promover_core_com_seguranca(
    condicoes: List[Dict[str, str]],
) -> bool:
    """
    Define se todas as condições de promoção estão aprovadas.
    """
    if len(condicoes) == 0:
        return False

    return all(item.get("Status") == "OK" for item in condicoes)


def gerar_plano_de_acao_core(
    decisao: str,
    risco: str,
    condicoes: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    """
    Gera plano prático de próxima ação.
    """
    pendencias = [
        item for item in condicoes
        if item.get("Status") != "OK"
    ]

    plano = []

    if decisao in [DECISAO_SEM_DADOS, DECISAO_CONTINUAR_TESTE_CONTROLADO]:
        plano.append(
            {
                "Prioridade": "Alta",
                "Ação": "Gerar mais logs reais",
                "Motivo": "Amostra técnica ainda é pequena para decisão definitiva.",
            }
        )

    if decisao in [DECISAO_MANTER_LEGACY, DECISAO_NAO_PROMOVER_CORE]:
        plano.append(
            {
                "Prioridade": "Alta",
                "Ação": "Manter Legacy como padrão",
                "Motivo": f"Risco técnico atual: {risco}.",
            }
        )

    if decisao == DECISAO_AUMENTAR_TESTES_CORE:
        plano.append(
            {
                "Prioridade": "Média",
                "Ação": "Usar Core Engine com mais frequência no Modo Fundador",
                "Motivo": "O motor novo já mostra sinais de estabilidade, mas ainda precisa de mais evidência.",
            }
        )

    if decisao == DECISAO_CORE_PODE_SER_PROMOVIDO_COM_FALLBACK:
        plano.append(
            {
                "Prioridade": "Alta",
                "Ação": "Preparar versão de promoção controlada",
                "Motivo": "Condições técnicas indicam possível promoção com fallback e rollback.",
            }
        )

    for pendencia in pendencias[:5]:
        plano.append(
            {
                "Prioridade": "Média",
                "Ação": f"Resolver pendência: {pendencia.get('Condição')}",
                "Motivo": pendencia.get("Detalhe", ""),
            }
        )

    if len(plano) == 0:
        plano.append(
            {
                "Prioridade": "Baixa",
                "Ação": "Manter monitoramento",
                "Motivo": "Nenhuma ação crítica detectada.",
            }
        )

    return plano


def analisar_decisao_core_engine(
    analise_saude: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Analisa a saúde técnica e gera decisão controlada do Core Engine.
    """
    risco = calcular_nivel_risco_core(analise_saude)
    decisao = decidir_status_core_engine(analise_saude)
    condicoes = gerar_condicoes_para_promocao_core(analise_saude)
    promocao_segura = pode_promover_core_com_seguranca(condicoes)

    return {
        "versao_decisao_core_engine": VERSAO_DECISAO_CORE_ENGINE,
        "versao_saude_motor": analise_saude.get("versao_saude_motor", VERSAO_SAUDE_MOTOR),
        "data_decisao": _agora_iso(),
        "decisao": decisao,
        "risco": risco,
        "promocao_core_segura": promocao_segura,
        "acao_recomendada": gerar_acao_recomendada_core(decisao),
        "leitura": gerar_leitura_decisao_core(
            decisao=decisao,
            risco=risco,
            analise_saude=analise_saude,
        ),
        "condicoes_promocao": condicoes,
        "plano_acao": gerar_plano_de_acao_core(
            decisao=decisao,
            risco=risco,
            condicoes=condicoes,
        ),
        "analise_saude": analise_saude,
    }


def analisar_decisao_core_engine_por_arquivo(
    caminho_logs: Optional[Path] = None,
    limite: int = 300,
) -> Dict[str, Any]:
    """
    Carrega os logs, analisa saúde e gera decisão sobre Core Engine.
    """
    caminho = Path(caminho_logs) if caminho_logs is not None else CAMINHO_LOGS_MOTOR

    analise_saude = analisar_saude_motor_por_arquivo(
        caminho_logs=caminho,
        limite=limite,
    )

    return {
        **analisar_decisao_core_engine(analise_saude),
        "caminho_logs": str(caminho),
        "limite_logs": limite,
    }


def gerar_tabela_resumo_decisao_core(
    decisao_core: Dict[str, Any],
) -> List[Dict[str, str]]:
    """
    Gera tabela resumida da decisão.
    """
    analise_saude = decisao_core.get("analise_saude", {})
    metricas = analise_saude.get("metricas", {})

    return [
        {
            "Indicador": "Decisão",
            "Valor": str(decisao_core.get("decisao", "")),
        },
        {
            "Indicador": "Risco",
            "Valor": str(decisao_core.get("risco", "")),
        },
        {
            "Indicador": "Promoção Core segura?",
            "Valor": _bool_texto(bool(decisao_core.get("promocao_core_segura", False))),
        },
        {
            "Indicador": "Ação recomendada",
            "Valor": str(decisao_core.get("acao_recomendada", "")),
        },
        {
            "Indicador": "Score saúde",
            "Valor": f"{analise_saude.get('score_saude', 0)}/100",
        },
        {
            "Indicador": "Status saúde",
            "Valor": str(analise_saude.get("status_saude", "")),
        },
        {
            "Indicador": "Prontidão Core",
            "Valor": str(analise_saude.get("prontidao_core", "")),
        },
        {
            "Indicador": "Logs analisados",
            "Valor": str(metricas.get("total_logs", 0)),
        },
        {
            "Indicador": "Erros",
            "Valor": str(metricas.get("execucoes_erro", 0)),
        },
        {
            "Indicador": "Fallbacks",
            "Valor": str(metricas.get("fallbacks", 0)),
        },
        {
            "Indicador": "Core executado",
            "Valor": str(metricas.get("core_executado", 0)),
        },
    ]


def gerar_markdown_decisao_core_engine(
    decisao_core: Dict[str, Any],
) -> str:
    """
    Gera relatório markdown da decisão controlada.
    """
    resumo = gerar_tabela_resumo_decisao_core(decisao_core)
    condicoes = decisao_core.get("condicoes_promocao", [])
    plano = decisao_core.get("plano_acao", [])

    linhas_resumo = "\n".join(
        [
            f"| {linha['Indicador']} | {linha['Valor']} |"
            for linha in resumo
        ]
    )

    linhas_condicoes = "\n".join(
        [
            f"| {linha['Condição']} | {linha['Status']} | {linha['Detalhe']} |"
            for linha in condicoes
        ]
    )

    linhas_plano = "\n".join(
        [
            f"| {linha['Prioridade']} | {linha['Ação']} | {linha['Motivo']} |"
            for linha in plano
        ]
    )

    return f"""# Decisão Controlada do Core Engine

Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Resumo executivo

| Indicador | Valor |
|---|---|
{linhas_resumo}

## Leitura

{decisao_core.get("leitura", "")}

## Condições para promoção do Core

| Condição | Status | Detalhe |
|---|---|---|
{linhas_condicoes}

## Plano de ação

| Prioridade | Ação | Motivo |
|---|---|---|
{linhas_plano}

## Regra de governança

O Core Engine não deve virar padrão apenas porque está funcionando.
Ele deve virar padrão somente quando houver amostra suficiente, zero erros,
zero fallbacks relevantes, score técnico alto, fallback ativo e plano de rollback.
"""


def executar_autoteste_decisao_core_engine() -> List[Dict[str, str]]:
    """
    Executa autotestes da decisão controlada do Core Engine.
    """
    testes = []

    logs_saudaveis = criar_logs_sinteticos_saudaveis()
    analise_saudavel = analisar_saude_motor(logs_saudaveis)
    decisao_saudavel = analisar_decisao_core_engine(analise_saudavel)

    testes.append(
        {
            "teste": "decisao_saudavel_executa",
            "status": "OK" if "decisao" in decisao_saudavel else "FALHA",
            "detalhe": f"Decisão: {decisao_saudavel.get('decisao')}",
        }
    )

    testes.append(
        {
            "teste": "decisao_saudavel_sem_erro_nao_bloqueia_totalmente",
            "status": (
                "OK"
                if decisao_saudavel.get("decisao")
                in [
                    DECISAO_CONTINUAR_TESTE_CONTROLADO,
                    DECISAO_AUMENTAR_TESTES_CORE,
                    DECISAO_CORE_PODE_SER_PROMOVIDO_COM_FALLBACK,
                ]
                else "FALHA"
            ),
            "detalhe": f"Risco: {decisao_saudavel.get('risco')}",
        }
    )

    logs_alerta = criar_logs_sinteticos_com_alerta()
    analise_alerta = analisar_saude_motor(logs_alerta)
    decisao_alerta = analisar_decisao_core_engine(analise_alerta)

    testes.append(
        {
            "teste": "decisao_alerta_detecta_risco",
            "status": (
                "OK"
                if decisao_alerta.get("risco") in [RISCO_ALTO, RISCO_CRITICO]
                else "FALHA"
            ),
            "detalhe": f"Risco: {decisao_alerta.get('risco')}",
        }
    )

    testes.append(
        {
            "teste": "decisao_alerta_nao_promove_core",
            "status": (
                "OK"
                if decisao_alerta.get("decisao")
                in [
                    DECISAO_MANTER_LEGACY,
                    DECISAO_NAO_PROMOVER_CORE,
                ]
                else "FALHA"
            ),
            "detalhe": f"Decisão: {decisao_alerta.get('decisao')}",
        }
    )

    condicoes = decisao_saudavel.get("condicoes_promocao", [])

    testes.append(
        {
            "teste": "condicoes_promocao_geradas",
            "status": "OK" if len(condicoes) > 0 else "FALHA",
            "detalhe": f"Condições: {len(condicoes)}",
        }
    )

    plano = decisao_saudavel.get("plano_acao", [])

    testes.append(
        {
            "teste": "plano_acao_gerado",
            "status": "OK" if len(plano) > 0 else "FALHA",
            "detalhe": f"Ações: {len(plano)}",
        }
    )

    markdown = gerar_markdown_decisao_core_engine(decisao_saudavel)

    testes.append(
        {
            "teste": "markdown_decisao_core_gerado",
            "status": "OK" if "# Decisão Controlada do Core Engine" in markdown else "FALHA",
            "detalhe": "Relatório markdown criado.",
        }
    )

    decisao_arquivo = analisar_decisao_core_engine_por_arquivo(
        caminho_logs=CAMINHO_LOGS_MOTOR,
        limite=50,
    )

    testes.append(
        {
            "teste": "decisao_por_arquivo_nao_quebra",
            "status": "OK" if "decisao" in decisao_arquivo else "FALHA",
            "detalhe": f"Decisão: {decisao_arquivo.get('decisao')}",
        }
    )

    return testes