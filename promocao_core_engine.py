# promocao_core_engine.py

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from decisao_core_engine import (
    VERSAO_DECISAO_CORE_ENGINE,
    DECISAO_SEM_DADOS,
    DECISAO_MANTER_LEGACY,
    DECISAO_CONTINUAR_TESTE_CONTROLADO,
    DECISAO_AUMENTAR_TESTES_CORE,
    DECISAO_CORE_PODE_SER_PROMOVIDO_COM_FALLBACK,
    DECISAO_NAO_PROMOVER_CORE,
    RISCO_BAIXO,
    RISCO_MODERADO,
    RISCO_ALTO,
    RISCO_CRITICO,
    RISCO_INDEFINIDO,
    analisar_decisao_core_engine,
    analisar_decisao_core_engine_por_arquivo,
)
from logs_motor_valuation import CAMINHO_LOGS_MOTOR
from saude_motor_valuation import (
    VERSAO_SAUDE_MOTOR,
    analisar_saude_motor,
    criar_logs_sinteticos_com_alerta,
)


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v3.8.21 — Promoção Controlada do Core Engine
# ------------------------------------------------------------
# Este arquivo transforma a decisão técnica em uma política
# controlada de promoção do Core Engine.
#
# Objetivo:
# - decidir se o Core pode virar padrão
# - impedir promoção insegura
# - exigir fallback e rollback
# - limitar exposição por perfil de usuário
# - gerar configuração recomendada de operação
# - preparar migração segura Legacy -> Core
# ============================================================


VERSAO_PROMOCAO_CORE_ENGINE = "3.8.21"


ESTADO_PROMOCAO_SEM_DADOS = "SEM_DADOS"
ESTADO_PROMOCAO_BLOQUEADA = "BLOQUEADA"
ESTADO_PROMOCAO_OBSERVACAO = "EM_OBSERVACAO"
ESTADO_PROMOCAO_TESTE_INTERNO = "TESTE_INTERNO"
ESTADO_PROMOCAO_APTA_COM_CONTROLES = "APTA_COM_CONTROLES"


MOTOR_LEGACY = "Legacy"
MOTOR_CORE = "Core Engine"


EXPOSICAO_NENHUMA = "NENHUMA"
EXPOSICAO_FUNDADOR = "FUNDADOR"
EXPOSICAO_CONTROLADA = "CONTROLADA"


def _agora_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _safe_str(valor: Any) -> str:
    if valor is None:
        return ""

    return str(valor).strip()


def _safe_int(valor: Any, default: int = 0) -> int:
    try:
        return int(valor)
    except (TypeError, ValueError):
        return default


def _bool_texto(valor: bool) -> str:
    return "Sim" if valor else "Não"


def decidir_estado_promocao_core(
    decisao_core: Dict[str, Any],
) -> str:
    """
    Converte a decisão técnica em estado de promoção operacional.
    """
    decisao = _safe_str(decisao_core.get("decisao"))
    risco = _safe_str(decisao_core.get("risco"))
    promocao_segura = bool(decisao_core.get("promocao_core_segura", False))

    if decisao == DECISAO_SEM_DADOS:
        return ESTADO_PROMOCAO_SEM_DADOS

    if decisao in [DECISAO_NAO_PROMOVER_CORE, DECISAO_MANTER_LEGACY]:
        return ESTADO_PROMOCAO_BLOQUEADA

    if risco in [RISCO_CRITICO, RISCO_ALTO]:
        return ESTADO_PROMOCAO_BLOQUEADA

    if decisao == DECISAO_CONTINUAR_TESTE_CONTROLADO:
        return ESTADO_PROMOCAO_OBSERVACAO

    if decisao == DECISAO_AUMENTAR_TESTES_CORE:
        return ESTADO_PROMOCAO_TESTE_INTERNO

    if decisao == DECISAO_CORE_PODE_SER_PROMOVIDO_COM_FALLBACK and promocao_segura:
        return ESTADO_PROMOCAO_APTA_COM_CONTROLES

    return ESTADO_PROMOCAO_OBSERVACAO


def gerar_bloqueios_promocao_core(
    decisao_core: Dict[str, Any],
) -> List[Dict[str, str]]:
    """
    Lista os bloqueios que impedem a promoção do Core Engine.
    """
    bloqueios = []

    decisao = _safe_str(decisao_core.get("decisao"))
    risco = _safe_str(decisao_core.get("risco"))
    condicoes = decisao_core.get("condicoes_promocao", [])
    analise_saude = decisao_core.get("analise_saude", {})
    metricas = analise_saude.get("metricas", {})

    erros = _safe_int(metricas.get("execucoes_erro", 0))
    fallbacks = _safe_int(metricas.get("fallbacks", 0))
    total_logs = _safe_int(metricas.get("total_logs", 0))
    core_executado = _safe_int(metricas.get("core_executado", 0))

    if total_logs < 30:
        bloqueios.append(
            {
                "Bloqueio": "Amostra insuficiente",
                "Detalhe": f"Logs atuais: {total_logs}. Mínimo recomendado: 30.",
            }
        )

    if core_executado < 10:
        bloqueios.append(
            {
                "Bloqueio": "Poucas execuções com Core Engine",
                "Detalhe": f"Core executado {core_executado} vezes. Mínimo recomendado: 10.",
            }
        )

    if erros > 0:
        bloqueios.append(
            {
                "Bloqueio": "Erros técnicos detectados",
                "Detalhe": f"Execuções com erro: {erros}.",
            }
        )

    if fallbacks > 0:
        bloqueios.append(
            {
                "Bloqueio": "Fallbacks detectados",
                "Detalhe": f"Fallbacks recentes: {fallbacks}.",
            }
        )

    if risco in [RISCO_ALTO, RISCO_CRITICO, RISCO_INDEFINIDO]:
        bloqueios.append(
            {
                "Bloqueio": "Risco técnico inadequado",
                "Detalhe": f"Risco atual: {risco}.",
            }
        )

    if decisao in [DECISAO_SEM_DADOS, DECISAO_MANTER_LEGACY, DECISAO_NAO_PROMOVER_CORE]:
        bloqueios.append(
            {
                "Bloqueio": "Decisão técnica não permite promoção",
                "Detalhe": f"Decisão atual: {decisao}.",
            }
        )

    for condicao in condicoes:
        if condicao.get("Status") != "OK":
            bloqueios.append(
                {
                    "Bloqueio": f"Condição pendente: {condicao.get('Condição', '')}",
                    "Detalhe": condicao.get("Detalhe", ""),
                }
            )

    bloqueios_unicos = []
    vistos = set()

    for bloqueio in bloqueios:
        chave = (bloqueio["Bloqueio"], bloqueio["Detalhe"])
        if chave not in vistos:
            bloqueios_unicos.append(bloqueio)
            vistos.add(chave)

    return bloqueios_unicos


def gerar_configuracao_operacional_core(
    decisao_core: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Gera configuração recomendada de operação do motor.
    """
    estado_promocao = decidir_estado_promocao_core(decisao_core)
    risco = _safe_str(decisao_core.get("risco"))
    decisao = _safe_str(decisao_core.get("decisao"))
    promocao_segura = bool(decisao_core.get("promocao_core_segura", False))

    if estado_promocao == ESTADO_PROMOCAO_APTA_COM_CONTROLES:
        return {
            "estado_promocao": estado_promocao,
            "motor_padrao_recomendado": MOTOR_CORE,
            "fallback_obrigatorio": True,
            "rollback_obrigatorio": True,
            "core_liberado_modo_fundador": True,
            "core_liberado_usuario_beta": False,
            "core_liberado_investidor_completo": False,
            "nivel_exposicao": EXPOSICAO_CONTROLADA,
            "pode_promover_core": promocao_segura,
            "exige_monitoramento_logs": True,
            "exige_versao_controlada": True,
            "acao_principal": "Preparar promoção controlada do Core Engine com fallback e rollback.",
            "justificativa": (
                "A decisão técnica indica que o Core pode avançar, mas a promoção deve ser controlada."
            ),
        }

    if estado_promocao == ESTADO_PROMOCAO_TESTE_INTERNO:
        return {
            "estado_promocao": estado_promocao,
            "motor_padrao_recomendado": MOTOR_LEGACY,
            "fallback_obrigatorio": True,
            "rollback_obrigatorio": True,
            "core_liberado_modo_fundador": True,
            "core_liberado_usuario_beta": False,
            "core_liberado_investidor_completo": False,
            "nivel_exposicao": EXPOSICAO_FUNDADOR,
            "pode_promover_core": False,
            "exige_monitoramento_logs": True,
            "exige_versao_controlada": False,
            "acao_principal": "Aumentar testes internos com Core Engine no Modo Fundador.",
            "justificativa": (
                "O Core mostra sinais positivos, mas ainda não deve virar padrão."
            ),
        }

    if estado_promocao == ESTADO_PROMOCAO_OBSERVACAO:
        return {
            "estado_promocao": estado_promocao,
            "motor_padrao_recomendado": MOTOR_LEGACY,
            "fallback_obrigatorio": True,
            "rollback_obrigatorio": True,
            "core_liberado_modo_fundador": True,
            "core_liberado_usuario_beta": False,
            "core_liberado_investidor_completo": False,
            "nivel_exposicao": EXPOSICAO_FUNDADOR,
            "pode_promover_core": False,
            "exige_monitoramento_logs": True,
            "exige_versao_controlada": False,
            "acao_principal": "Continuar observando logs antes de qualquer promoção.",
            "justificativa": (
                "Ainda falta evidência técnica suficiente para promover o Core."
            ),
        }

    if estado_promocao == ESTADO_PROMOCAO_SEM_DADOS:
        return {
            "estado_promocao": estado_promocao,
            "motor_padrao_recomendado": MOTOR_LEGACY,
            "fallback_obrigatorio": True,
            "rollback_obrigatorio": True,
            "core_liberado_modo_fundador": False,
            "core_liberado_usuario_beta": False,
            "core_liberado_investidor_completo": False,
            "nivel_exposicao": EXPOSICAO_NENHUMA,
            "pode_promover_core": False,
            "exige_monitoramento_logs": True,
            "exige_versao_controlada": False,
            "acao_principal": "Coletar mais logs reais antes de decidir.",
            "justificativa": (
                "Não há dados suficientes para tomar decisão de promoção."
            ),
        }

    return {
        "estado_promocao": ESTADO_PROMOCAO_BLOQUEADA,
        "motor_padrao_recomendado": MOTOR_LEGACY,
        "fallback_obrigatorio": True,
        "rollback_obrigatorio": True,
        "core_liberado_modo_fundador": False,
        "core_liberado_usuario_beta": False,
        "core_liberado_investidor_completo": False,
        "nivel_exposicao": EXPOSICAO_NENHUMA,
        "pode_promover_core": False,
        "exige_monitoramento_logs": True,
        "exige_versao_controlada": False,
        "acao_principal": "Manter Legacy como padrão e investigar riscos antes de avançar.",
        "justificativa": (
            f"A decisão atual é {decisao}, com risco {risco}. Promoção bloqueada."
        ),
    }


def gerar_leitura_promocao_core(
    configuracao: Dict[str, Any],
    bloqueios: List[Dict[str, str]],
) -> str:
    """
    Gera leitura executiva da promoção.
    """
    estado = configuracao.get("estado_promocao", "")
    motor = configuracao.get("motor_padrao_recomendado", "")
    pode_promover = bool(configuracao.get("pode_promover_core", False))

    if estado == ESTADO_PROMOCAO_APTA_COM_CONTROLES and pode_promover:
        return (
            "O Core Engine está apto para uma promoção controlada. "
            "A mudança deve ser feita em uma versão específica, mantendo fallback obrigatório para Legacy, "
            "rollback planejado e monitoramento ativo dos logs."
        )

    if estado == ESTADO_PROMOCAO_TESTE_INTERNO:
        return (
            "O Core Engine pode ser usado com mais frequência no Modo Fundador, "
            "mas ainda não deve virar padrão. Legacy permanece como motor recomendado."
        )

    if estado == ESTADO_PROMOCAO_OBSERVACAO:
        return (
            "O Core Engine continua em observação. Ainda não há evidência suficiente para promoção. "
            "Continue gerando logs e monitorando saúde técnica."
        )

    if estado == ESTADO_PROMOCAO_SEM_DADOS:
        return (
            "Não há dados suficientes para avaliar promoção. "
            "O sistema deve operar com Legacy até existir amostra técnica relevante."
        )

    return (
        f"Promoção bloqueada. Motor recomendado: {motor}. "
        f"Bloqueios encontrados: {len(bloqueios)}. "
        "Resolva os bloqueios antes de considerar qualquer promoção."
    )


def analisar_promocao_core_engine(
    decisao_core: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Analisa a decisão do Core e gera política de promoção controlada.
    """
    configuracao = gerar_configuracao_operacional_core(decisao_core)
    bloqueios = gerar_bloqueios_promocao_core(decisao_core)
    leitura = gerar_leitura_promocao_core(
        configuracao=configuracao,
        bloqueios=bloqueios,
    )

    return {
        "versao_promocao_core_engine": VERSAO_PROMOCAO_CORE_ENGINE,
        "versao_decisao_core_engine": decisao_core.get(
            "versao_decisao_core_engine",
            VERSAO_DECISAO_CORE_ENGINE,
        ),
        "versao_saude_motor": decisao_core.get("versao_saude_motor", VERSAO_SAUDE_MOTOR),
        "data_promocao": _agora_iso(),
        "configuracao": configuracao,
        "bloqueios": bloqueios,
        "leitura": leitura,
        "decisao_core": decisao_core,
    }


def analisar_promocao_core_engine_por_arquivo(
    caminho_logs: Optional[Path] = None,
    limite: int = 300,
) -> Dict[str, Any]:
    """
    Carrega logs, analisa decisão e gera política de promoção.
    """
    caminho = Path(caminho_logs) if caminho_logs is not None else CAMINHO_LOGS_MOTOR

    decisao_core = analisar_decisao_core_engine_por_arquivo(
        caminho_logs=caminho,
        limite=limite,
    )

    return {
        **analisar_promocao_core_engine(decisao_core),
        "caminho_logs": str(caminho),
        "limite_logs": limite,
    }


def gerar_tabela_resumo_promocao_core(
    promocao: Dict[str, Any],
) -> List[Dict[str, str]]:
    """
    Gera tabela resumida da promoção controlada.
    """
    configuracao = promocao.get("configuracao", {})
    decisao_core = promocao.get("decisao_core", {})
    analise_saude = decisao_core.get("analise_saude", {})
    metricas = analise_saude.get("metricas", {})

    return [
        {
            "Indicador": "Estado da promoção",
            "Valor": str(configuracao.get("estado_promocao", "")),
        },
        {
            "Indicador": "Motor padrão recomendado",
            "Valor": str(configuracao.get("motor_padrao_recomendado", "")),
        },
        {
            "Indicador": "Pode promover Core?",
            "Valor": _bool_texto(bool(configuracao.get("pode_promover_core", False))),
        },
        {
            "Indicador": "Fallback obrigatório",
            "Valor": _bool_texto(bool(configuracao.get("fallback_obrigatorio", False))),
        },
        {
            "Indicador": "Rollback obrigatório",
            "Valor": _bool_texto(bool(configuracao.get("rollback_obrigatorio", False))),
        },
        {
            "Indicador": "Core liberado no Modo Fundador",
            "Valor": _bool_texto(bool(configuracao.get("core_liberado_modo_fundador", False))),
        },
        {
            "Indicador": "Core liberado para Usuário Beta",
            "Valor": _bool_texto(bool(configuracao.get("core_liberado_usuario_beta", False))),
        },
        {
            "Indicador": "Core liberado para Investidor Completo",
            "Valor": _bool_texto(
                bool(configuracao.get("core_liberado_investidor_completo", False))
            ),
        },
        {
            "Indicador": "Nível de exposição",
            "Valor": str(configuracao.get("nivel_exposicao", "")),
        },
        {
            "Indicador": "Decisão técnica",
            "Valor": str(decisao_core.get("decisao", "")),
        },
        {
            "Indicador": "Risco técnico",
            "Valor": str(decisao_core.get("risco", "")),
        },
        {
            "Indicador": "Score saúde",
            "Valor": f"{analise_saude.get('score_saude', 0)}/100",
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


def gerar_plano_execucao_promocao_core(
    promocao: Dict[str, Any],
) -> List[Dict[str, str]]:
    """
    Gera plano de execução para promoção ou bloqueio.
    """
    configuracao = promocao.get("configuracao", {})
    bloqueios = promocao.get("bloqueios", [])

    estado = configuracao.get("estado_promocao", "")
    pode_promover = bool(configuracao.get("pode_promover_core", False))

    plano = []

    if estado == ESTADO_PROMOCAO_APTA_COM_CONTROLES and pode_promover:
        plano.extend(
            [
                {
                    "Etapa": "1",
                    "Ação": "Criar versão de promoção controlada",
                    "Detalhe": "Preparar mudança do motor padrão para Core Engine apenas com fallback ativo.",
                },
                {
                    "Etapa": "2",
                    "Ação": "Manter rollback para Legacy",
                    "Detalhe": "Garantir que qualquer falha volte imediatamente para Legacy.",
                },
                {
                    "Etapa": "3",
                    "Ação": "Monitorar logs após promoção",
                    "Detalhe": "Observar erros, fallbacks e divergências após a mudança.",
                },
                {
                    "Etapa": "4",
                    "Ação": "Liberar apenas em escopo controlado",
                    "Detalhe": "Não liberar imediatamente para todos os usuários.",
                },
            ]
        )
    elif estado == ESTADO_PROMOCAO_TESTE_INTERNO:
        plano.extend(
            [
                {
                    "Etapa": "1",
                    "Ação": "Aumentar uso do Core no Modo Fundador",
                    "Detalhe": "Testar mais empresas e cenários com Core Engine.",
                },
                {
                    "Etapa": "2",
                    "Ação": "Manter Legacy como padrão",
                    "Detalhe": "Usuários comuns ainda devem usar o motor mais estável.",
                },
                {
                    "Etapa": "3",
                    "Ação": "Coletar mais logs",
                    "Detalhe": "A decisão futura depende de amostra técnica maior.",
                },
            ]
        )
    else:
        plano.extend(
            [
                {
                    "Etapa": "1",
                    "Ação": "Manter Legacy como padrão",
                    "Detalhe": "Não alterar motor principal enquanto houver bloqueios.",
                },
                {
                    "Etapa": "2",
                    "Ação": "Resolver bloqueios técnicos",
                    "Detalhe": f"Bloqueios encontrados: {len(bloqueios)}.",
                },
                {
                    "Etapa": "3",
                    "Ação": "Reexecutar saúde e decisão do Core",
                    "Detalhe": "Após novos testes, revisar se o Core pode avançar.",
                },
            ]
        )

    return plano


def gerar_markdown_promocao_core_engine(
    promocao: Dict[str, Any],
) -> str:
    """
    Gera relatório markdown da promoção controlada.
    """
    resumo = gerar_tabela_resumo_promocao_core(promocao)
    bloqueios = promocao.get("bloqueios", [])
    plano = gerar_plano_execucao_promocao_core(promocao)

    linhas_resumo = "\n".join(
        [
            f"| {linha['Indicador']} | {linha['Valor']} |"
            for linha in resumo
        ]
    )

    linhas_bloqueios = "\n".join(
        [
            f"| {linha['Bloqueio']} | {linha['Detalhe']} |"
            for linha in bloqueios
        ]
    )

    if linhas_bloqueios == "":
        linhas_bloqueios = "| Nenhum bloqueio crítico | Promoção tecnicamente possível com controles |"

    linhas_plano = "\n".join(
        [
            f"| {linha['Etapa']} | {linha['Ação']} | {linha['Detalhe']} |"
            for linha in plano
        ]
    )

    return f"""# Promoção Controlada do Core Engine

Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Resumo executivo

| Indicador | Valor |
|---|---|
{linhas_resumo}

## Leitura

{promocao.get("leitura", "")}

## Bloqueios

| Bloqueio | Detalhe |
|---|---|
{linhas_bloqueios}

## Plano de execução

| Etapa | Ação | Detalhe |
|---|---|---|
{linhas_plano}

## Regra de governança

O Core Engine só deve virar padrão quando a decisão técnica permitir,
a promoção estiver apta com controles, o fallback estiver ativo,
o rollback estiver planejado e os logs continuarem sendo monitorados.

A promoção deve ser feita em versão específica, nunca de forma silenciosa.
"""


def criar_logs_sinteticos_core_pronto() -> List[Dict[str, str]]:
    """
    Cria logs sintéticos em cenário forte para promoção controlada.
    """
    logs = []

    for indice in range(35):
        motor = MOTOR_CORE if indice >= 15 else MOTOR_LEGACY

        logs.append(
            {
                "data_execucao": f"2026-01-01T13:{indice:02d}:00",
                "origem": "autoteste",
                "contexto": "core_pronto",
                "empresa": "Empresa Core Pronto",
                "ticker": f"CPR{indice}",
                "status_execucao": "OK",
                "status_valuation": "COMPRA",
                "preco_atual": "18",
                "preco_teto": "25.50",
                "preco_justo_combinado": "35.00",
                "margem_ate_preco_teto": "41.66",
                "potencial_ate_preco_justo": "94.44",
                "motor_preferido": motor,
                "motor_executado": motor,
                "fallback_ocorreu": "Não",
                "status_fallback": "NAO_NECESSARIO",
                "erro_execucao": "",
            }
        )

    return list(reversed(logs))


def executar_autoteste_promocao_core_engine() -> List[Dict[str, str]]:
    """
    Executa autotestes da promoção controlada do Core Engine.
    """
    testes = []

    logs_prontos = criar_logs_sinteticos_core_pronto()
    analise_pronta = analisar_saude_motor(logs_prontos)
    decisao_pronta = analisar_decisao_core_engine(analise_pronta)
    promocao_pronta = analisar_promocao_core_engine(decisao_pronta)

    configuracao_pronta = promocao_pronta.get("configuracao", {})

    testes.append(
        {
            "teste": "promocao_pronta_executa",
            "status": "OK" if "configuracao" in promocao_pronta else "FALHA",
            "detalhe": f"Estado: {configuracao_pronta.get('estado_promocao')}",
        }
    )

    testes.append(
        {
            "teste": "promocao_pronta_recomenda_core_com_controles",
            "status": (
                "OK"
                if configuracao_pronta.get("motor_padrao_recomendado") == MOTOR_CORE
                and configuracao_pronta.get("fallback_obrigatorio")
                and configuracao_pronta.get("rollback_obrigatorio")
                else "FALHA"
            ),
            "detalhe": f"Motor: {configuracao_pronta.get('motor_padrao_recomendado')}",
        }
    )

    logs_alerta = criar_logs_sinteticos_com_alerta()
    analise_alerta = analisar_saude_motor(logs_alerta)
    decisao_alerta = analisar_decisao_core_engine(analise_alerta)
    promocao_alerta = analisar_promocao_core_engine(decisao_alerta)

    configuracao_alerta = promocao_alerta.get("configuracao", {})

    testes.append(
        {
            "teste": "promocao_alerta_bloqueia_core",
            "status": (
                "OK"
                if configuracao_alerta.get("motor_padrao_recomendado") == MOTOR_LEGACY
                and not configuracao_alerta.get("pode_promover_core")
                else "FALHA"
            ),
            "detalhe": f"Estado: {configuracao_alerta.get('estado_promocao')}",
        }
    )

    testes.append(
        {
            "teste": "bloqueios_alerta_gerados",
            "status": "OK" if len(promocao_alerta.get("bloqueios", [])) > 0 else "FALHA",
            "detalhe": f"Bloqueios: {len(promocao_alerta.get('bloqueios', []))}",
        }
    )

    tabela = gerar_tabela_resumo_promocao_core(promocao_pronta)

    testes.append(
        {
            "teste": "tabela_promocao_gerada",
            "status": "OK" if len(tabela) > 0 else "FALHA",
            "detalhe": f"Linhas: {len(tabela)}",
        }
    )

    plano = gerar_plano_execucao_promocao_core(promocao_pronta)

    testes.append(
        {
            "teste": "plano_promocao_gerado",
            "status": "OK" if len(plano) > 0 else "FALHA",
            "detalhe": f"Etapas: {len(plano)}",
        }
    )

    markdown = gerar_markdown_promocao_core_engine(promocao_pronta)

    testes.append(
        {
            "teste": "markdown_promocao_gerado",
            "status": "OK" if "# Promoção Controlada do Core Engine" in markdown else "FALHA",
            "detalhe": "Relatório markdown criado.",
        }
    )

    promocao_arquivo = analisar_promocao_core_engine_por_arquivo(
        caminho_logs=CAMINHO_LOGS_MOTOR,
        limite=50,
    )

    testes.append(
        {
            "teste": "promocao_por_arquivo_nao_quebra",
            "status": "OK" if "configuracao" in promocao_arquivo else "FALHA",
            "detalhe": f"Estado: {promocao_arquivo.get('configuracao', {}).get('estado_promocao')}",
        }
    )

    return testes