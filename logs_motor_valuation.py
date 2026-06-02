# logs_motor_valuation.py

import csv
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fallback_motor_valuation import (
    VERSAO_FALLBACK_MOTOR,
    calcular_valuation_com_fallback,
)
from motor_valuation_controlado import (
    MOTOR_LEGACY,
    VERSAO_MOTOR_CONTROLADO,
    obter_motor_padrao,
)
from valuation import EntradasValuation


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v3.8.14 — Logs Técnicos do Motor de Valuation
# ------------------------------------------------------------
# Este arquivo registra execuções do motor principal.
#
# Objetivo:
# - registrar motor preferido
# - registrar motor executado
# - registrar se houve fallback
# - registrar erros técnicos
# - criar histórico técnico para auditoria
# - preparar painel de saúde do motor
# ============================================================


VERSAO_LOGS_MOTOR = "3.8.14"

CAMINHO_LOGS_MOTOR = Path("logs_motor_valuation.csv")


CAMPOS_LOGS_MOTOR = [
    "id_execucao",
    "data_execucao",
    "origem",
    "contexto",
    "empresa",
    "ticker",
    "moeda",
    "status_execucao",
    "status_valuation",
    "preco_atual",
    "preco_teto",
    "preco_justo_combinado",
    "margem_ate_preco_teto",
    "potencial_ate_preco_justo",
    "motor_preferido",
    "motor_executado",
    "motor_preferido_id",
    "motor_executado_id",
    "fallback_ocorreu",
    "status_fallback",
    "permitir_fallback",
    "erro_motor_preferido",
    "erro_execucao",
    "versao_logs_motor",
    "versao_fallback_motor",
    "versao_motor_controlado",
]


def _agora_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _safe_str(valor: Any) -> str:
    if valor is None:
        return ""

    return str(valor)


def _safe_float(valor: Any, default: float = 0.0) -> float:
    try:
        return float(valor)
    except (TypeError, ValueError):
        return default


def _safe_bool_texto(valor: Any) -> str:
    return "Sim" if bool(valor) else "Não"


def _garantir_caminho_path(caminho: Optional[Path]) -> Path:
    if caminho is None:
        return CAMINHO_LOGS_MOTOR

    return Path(caminho)


def _normalizar_registro_para_csv(registro: Dict[str, Any]) -> Dict[str, str]:
    return {
        campo: _safe_str(registro.get(campo, ""))
        for campo in CAMPOS_LOGS_MOTOR
    }


def inicializar_arquivo_logs_motor(caminho: Optional[Path] = None) -> Path:
    """
    Cria o arquivo CSV de logs se ele ainda não existir.
    """
    caminho_logs = _garantir_caminho_path(caminho)

    if not caminho_logs.exists():
        with caminho_logs.open("w", newline="", encoding="utf-8") as arquivo:
            escritor = csv.DictWriter(
                arquivo,
                fieldnames=CAMPOS_LOGS_MOTOR,
            )
            escritor.writeheader()

    return caminho_logs


def criar_registro_log_motor(
    entradas: EntradasValuation,
    resultado: Optional[Dict[str, Any]] = None,
    origem: str = "app",
    contexto: str = "fluxo_principal",
    status_execucao: str = "OK",
    erro_execucao: str = "",
    moeda: str = "R$",
    permitir_fallback: bool = True,
) -> Dict[str, Any]:
    """
    Cria um registro técnico padronizado para log do motor.
    """
    resultado_seguro = resultado or {}

    return {
        "id_execucao": str(uuid4()),
        "data_execucao": _agora_iso(),
        "origem": origem,
        "contexto": contexto,
        "empresa": _safe_str(getattr(entradas, "empresa", "")),
        "ticker": _safe_str(getattr(entradas, "ticker", "")).upper(),
        "moeda": moeda,
        "status_execucao": status_execucao,
        "status_valuation": _safe_str(resultado_seguro.get("status", "")),
        "preco_atual": _safe_float(getattr(entradas, "preco_atual", 0)),
        "preco_teto": _safe_float(resultado_seguro.get("preco_teto", 0)),
        "preco_justo_combinado": _safe_float(
            resultado_seguro.get("preco_justo_combinado", 0)
        ),
        "margem_ate_preco_teto": _safe_float(
            resultado_seguro.get("margem_ate_preco_teto", 0)
        ),
        "potencial_ate_preco_justo": _safe_float(
            resultado_seguro.get("potencial_ate_preco_justo", 0)
        ),
        "motor_preferido": _safe_str(
            resultado_seguro.get(
                "motor_preferido",
                resultado_seguro.get("motor_selecionado", ""),
            )
        ),
        "motor_executado": _safe_str(
            resultado_seguro.get(
                "motor_executado",
                resultado_seguro.get("motor_selecionado", ""),
            )
        ),
        "motor_preferido_id": _safe_str(resultado_seguro.get("motor_preferido_id", "")),
        "motor_executado_id": _safe_str(resultado_seguro.get("motor_executado_id", "")),
        "fallback_ocorreu": _safe_bool_texto(resultado_seguro.get("fallback_ocorreu", False)),
        "status_fallback": _safe_str(resultado_seguro.get("status_fallback", "")),
        "permitir_fallback": _safe_bool_texto(permitir_fallback),
        "erro_motor_preferido": _safe_str(resultado_seguro.get("erro_motor_preferido", "")),
        "erro_execucao": erro_execucao,
        "versao_logs_motor": VERSAO_LOGS_MOTOR,
        "versao_fallback_motor": _safe_str(
            resultado_seguro.get("versao_fallback_motor", VERSAO_FALLBACK_MOTOR)
        ),
        "versao_motor_controlado": _safe_str(
            resultado_seguro.get("versao_motor_controlado", VERSAO_MOTOR_CONTROLADO)
        ),
    }


def salvar_log_motor(
    registro: Dict[str, Any],
    caminho: Optional[Path] = None,
) -> Path:
    """
    Salva um registro no CSV de logs.
    """
    caminho_logs = inicializar_arquivo_logs_motor(caminho)
    registro_csv = _normalizar_registro_para_csv(registro)

    with caminho_logs.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(
            arquivo,
            fieldnames=CAMPOS_LOGS_MOTOR,
            extrasaction="ignore",
        )
        escritor.writerow(registro_csv)

    return caminho_logs


def carregar_logs_motor(
    caminho: Optional[Path] = None,
    limite: int = 100,
) -> List[Dict[str, str]]:
    """
    Carrega os logs mais recentes.
    """
    caminho_logs = _garantir_caminho_path(caminho)

    if not caminho_logs.exists():
        return []

    with caminho_logs.open("r", newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        linhas = list(leitor)

    linhas_recentes = list(reversed(linhas))[:limite]

    return linhas_recentes


def calcular_valuation_com_log(
    entradas: EntradasValuation,
    motor_preferido: str = MOTOR_LEGACY,
    moeda: str = "R$",
    permitir_fallback: bool = True,
    origem: str = "app",
    contexto: str = "fluxo_principal",
    caminho_log: Optional[Path] = None,
    forcar_falha_core: bool = False,
) -> Dict[str, Any]:
    """
    Executa o valuation com fallback e registra log técnico.

    Se o cálculo falhar completamente, registra o erro e relança a exceção.
    """
    try:
        resultado = calcular_valuation_com_fallback(
            entradas=entradas,
            motor_preferido=motor_preferido,
            moeda=moeda,
            permitir_fallback=permitir_fallback,
            forcar_falha_core=forcar_falha_core,
        )

        registro = criar_registro_log_motor(
            entradas=entradas,
            resultado=resultado,
            origem=origem,
            contexto=contexto,
            status_execucao="OK",
            erro_execucao="",
            moeda=moeda,
            permitir_fallback=permitir_fallback,
        )

        salvar_log_motor(
            registro=registro,
            caminho=caminho_log,
        )

        return {
            **resultado,
            "log_motor_registrado": True,
            "id_log_motor": registro["id_execucao"],
            "versao_logs_motor": VERSAO_LOGS_MOTOR,
        }

    except Exception as erro:
        registro_erro = criar_registro_log_motor(
            entradas=entradas,
            resultado=None,
            origem=origem,
            contexto=contexto,
            status_execucao="ERRO",
            erro_execucao=str(erro),
            moeda=moeda,
            permitir_fallback=permitir_fallback,
        )

        salvar_log_motor(
            registro=registro_erro,
            caminho=caminho_log,
        )

        raise RuntimeError(
            f"Falha no cálculo com log registrado. Erro: {erro}"
        ) from erro


def gerar_resumo_logs_motor(
    logs: List[Dict[str, str]],
) -> Dict[str, Any]:
    """
    Gera resumo executivo dos logs técnicos.
    """
    total = len(logs)

    if total == 0:
        return {
            "total_logs": 0,
            "execucoes_ok": 0,
            "execucoes_erro": 0,
            "fallbacks": 0,
            "core_preferido": 0,
            "legacy_preferido": 0,
            "core_executado": 0,
            "legacy_executado": 0,
            "ultimo_log": "",
            "saude": "SEM_DADOS",
        }

    execucoes_ok = len([log for log in logs if log.get("status_execucao") == "OK"])
    execucoes_erro = len([log for log in logs if log.get("status_execucao") == "ERRO"])
    fallbacks = len([log for log in logs if log.get("fallback_ocorreu") == "Sim"])

    core_preferido = len(
        [
            log for log in logs
            if log.get("motor_preferido", "").strip().lower() == "core engine"
        ]
    )

    legacy_preferido = len(
        [
            log for log in logs
            if log.get("motor_preferido", "").strip().lower() == "legacy"
        ]
    )

    core_executado = len(
        [
            log for log in logs
            if log.get("motor_executado", "").strip().lower() == "core engine"
        ]
    )

    legacy_executado = len(
        [
            log for log in logs
            if log.get("motor_executado", "").strip().lower() == "legacy"
        ]
    )

    if execucoes_erro > 0:
        saude = "ATENCAO_ERROS"
    elif fallbacks > 0:
        saude = "ATENCAO_FALLBACKS"
    else:
        saude = "SAUDAVEL"

    return {
        "total_logs": total,
        "execucoes_ok": execucoes_ok,
        "execucoes_erro": execucoes_erro,
        "fallbacks": fallbacks,
        "core_preferido": core_preferido,
        "legacy_preferido": legacy_preferido,
        "core_executado": core_executado,
        "legacy_executado": legacy_executado,
        "ultimo_log": logs[0].get("data_execucao", ""),
        "saude": saude,
    }


def gerar_tabela_resumo_logs_motor(
    logs: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    """
    Gera tabela amigável com resumo dos logs.
    """
    resumo = gerar_resumo_logs_motor(logs)

    return [
        {"Indicador": "Total de logs", "Valor": str(resumo["total_logs"])},
        {"Indicador": "Execuções OK", "Valor": str(resumo["execucoes_ok"])},
        {"Indicador": "Execuções com erro", "Valor": str(resumo["execucoes_erro"])},
        {"Indicador": "Fallbacks executados", "Valor": str(resumo["fallbacks"])},
        {"Indicador": "Core preferido", "Valor": str(resumo["core_preferido"])},
        {"Indicador": "Legacy preferido", "Valor": str(resumo["legacy_preferido"])},
        {"Indicador": "Core executado", "Valor": str(resumo["core_executado"])},
        {"Indicador": "Legacy executado", "Valor": str(resumo["legacy_executado"])},
        {"Indicador": "Último log", "Valor": str(resumo["ultimo_log"])},
        {"Indicador": "Saúde", "Valor": str(resumo["saude"])},
    ]


def gerar_markdown_logs_motor(
    logs: List[Dict[str, str]],
) -> str:
    """
    Gera relatório técnico dos logs.
    """
    resumo = gerar_tabela_resumo_logs_motor(logs)

    linhas_resumo = "\n".join(
        [
            f"| {linha['Indicador']} | {linha['Valor']} |"
            for linha in resumo
        ]
    )

    linhas_logs = "\n".join(
        [
            (
                f"| {log.get('data_execucao', '')} "
                f"| {log.get('empresa', '')} "
                f"| {log.get('ticker', '')} "
                f"| {log.get('motor_preferido', '')} "
                f"| {log.get('motor_executado', '')} "
                f"| {log.get('fallback_ocorreu', '')} "
                f"| {log.get('status_execucao', '')} "
                f"| {log.get('status_valuation', '')} "
                f"| {log.get('preco_teto', '')} |"
            )
            for log in logs[:50]
        ]
    )

    return f"""# Relatório de Logs do Motor de Valuation

Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Resumo

| Indicador | Valor |
|---|---|
{linhas_resumo}

## Últimas execuções

| Data | Empresa | Ticker | Motor preferido | Motor executado | Fallback | Execução | Status valuation | Preço-teto |
|---|---|---|---|---|---|---|---|---:|
{linhas_logs}

## Leitura

Os logs técnicos permitem acompanhar a saúde do motor de valuation,
detectar falhas, identificar uso do fallback e auditar a migração gradual
do Legacy para o Core Engine.
"""


def gerar_entradas_exemplo_logs_motor() -> EntradasValuation:
    """
    Gera entradas de exemplo para autotestes.
    """
    return EntradasValuation(
        empresa="Empresa Exemplo Logs",
        ticker="LOGS3",
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


def executar_autoteste_logs_motor() -> List[Dict[str, str]]:
    """
    Executa autotestes do sistema de logs.
    """
    testes = []

    caminho_teste = Path("logs_motor_valuation_teste.csv")

    if caminho_teste.exists():
        caminho_teste.unlink()

    entradas = gerar_entradas_exemplo_logs_motor()

    resultado_legacy = calcular_valuation_com_log(
        entradas=entradas,
        motor_preferido=MOTOR_LEGACY,
        moeda="R$",
        permitir_fallback=True,
        origem="autoteste",
        contexto="legacy_sem_fallback",
        caminho_log=caminho_teste,
    )

    testes.append(
        {
            "teste": "legacy_calcula_e_salva_log",
            "status": (
                "OK"
                if resultado_legacy.get("preco_teto", 0) != 0
                and resultado_legacy.get("log_motor_registrado")
                else "FALHA"
            ),
            "detalhe": f"ID log: {resultado_legacy.get('id_log_motor')}",
        }
    )

    resultado_core = calcular_valuation_com_log(
        entradas=entradas,
        motor_preferido="Core Engine",
        moeda="R$",
        permitir_fallback=True,
        origem="autoteste",
        contexto="core_sem_fallback",
        caminho_log=caminho_teste,
    )

    testes.append(
        {
            "teste": "core_calcula_e_salva_log",
            "status": (
                "OK"
                if resultado_core.get("preco_teto", 0) != 0
                and resultado_core.get("log_motor_registrado")
                else "FALHA"
            ),
            "detalhe": f"Motor executado: {resultado_core.get('motor_executado')}",
        }
    )

    resultado_core_com_fallback = calcular_valuation_com_log(
        entradas=entradas,
        motor_preferido="Core Engine",
        moeda="R$",
        permitir_fallback=True,
        origem="autoteste",
        contexto="core_com_fallback",
        caminho_log=caminho_teste,
        forcar_falha_core=True,
    )

    testes.append(
        {
            "teste": "fallback_salva_log",
            "status": (
                "OK"
                if resultado_core_com_fallback.get("fallback_ocorreu")
                and resultado_core_com_fallback.get("log_motor_registrado")
                else "FALHA"
            ),
            "detalhe": f"Fallback: {resultado_core_com_fallback.get('status_fallback')}",
        }
    )

    logs = carregar_logs_motor(
        caminho=caminho_teste,
        limite=50,
    )

    testes.append(
        {
            "teste": "carregar_logs_retorna_registros",
            "status": "OK" if len(logs) >= 3 else "FALHA",
            "detalhe": f"Logs carregados: {len(logs)}",
        }
    )

    resumo = gerar_resumo_logs_motor(logs)

    testes.append(
        {
            "teste": "resumo_detecta_fallback",
            "status": "OK" if resumo.get("fallbacks", 0) >= 1 else "FALHA",
            "detalhe": f"Fallbacks: {resumo.get('fallbacks')}",
        }
    )

    markdown = gerar_markdown_logs_motor(logs)

    testes.append(
        {
            "teste": "markdown_logs_gerado",
            "status": "OK" if "# Relatório de Logs" in markdown else "FALHA",
            "detalhe": "Relatório markdown criado.",
        }
    )

    if caminho_teste.exists():
        caminho_teste.unlink()

    return testes