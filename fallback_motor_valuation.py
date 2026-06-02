# fallback_motor_valuation.py

from datetime import datetime
from typing import Any, Dict, List

from valuation import EntradasValuation
from motor_valuation_controlado import (
    MOTOR_CORE,
    MOTOR_LEGACY,
    VERSAO_MOTOR_CONTROLADO,
    calcular_valuation_controlado,
    normalizar_motor,
    obter_motor_padrao,
    obter_rotulo_motor_por_id,
)


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v3.8.11 — Fallback Seguro do Motor Principal
# ------------------------------------------------------------
# Este arquivo adiciona resiliência ao cálculo principal.
#
# Objetivo:
# - tentar calcular com o motor escolhido
# - se o Core Engine falhar, voltar automaticamente para Legacy
# - impedir que o app quebre em produção
# - registrar metadados técnicos da tentativa
# - preparar migração segura para Core Engine como padrão futuro
# ============================================================


VERSAO_FALLBACK_MOTOR = "3.8.11"


STATUS_FALLBACK_NAO_NECESSARIO = "NAO_NECESSARIO"
STATUS_FALLBACK_EXECUTADO = "FALLBACK_EXECUTADO"
STATUS_FALLBACK_DESABILITADO = "FALLBACK_DESABILITADO"
STATUS_FALLBACK_FALHOU = "FALLBACK_FALHOU"


def _agora_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _safe_str(valor: Any) -> str:
    return str(valor).strip()


def _criar_metadados_base(
    motor_preferido: str,
    moeda: str,
    permitir_fallback: bool,
) -> Dict[str, Any]:
    motor_id = normalizar_motor(motor_preferido)

    return {
        "versao_fallback_motor": VERSAO_FALLBACK_MOTOR,
        "versao_motor_controlado": VERSAO_MOTOR_CONTROLADO,
        "motor_preferido": obter_rotulo_motor_por_id(motor_id),
        "motor_preferido_id": motor_id,
        "moeda_fallback": moeda,
        "permitir_fallback": permitir_fallback,
        "data_tentativa_fallback": _agora_iso(),
    }


def _calcular_com_motor(
    entradas: EntradasValuation,
    motor: str,
    moeda: str,
    forcar_falha_core: bool = False,
) -> Dict[str, Any]:
    """
    Executa o cálculo com o motor solicitado.

    O parâmetro forcar_falha_core existe apenas para autotestes controlados.
    Ele simula uma falha no Core Engine para validar se o fallback funciona.
    """
    motor_id = normalizar_motor(motor)

    if motor_id == "core" and forcar_falha_core:
        raise RuntimeError("Falha simulada no Core Engine para teste de fallback.")

    return calcular_valuation_controlado(
        entradas=entradas,
        motor=motor,
        moeda=moeda,
    )


def calcular_valuation_com_fallback(
    entradas: EntradasValuation,
    motor_preferido: str = MOTOR_LEGACY,
    moeda: str = "R$",
    permitir_fallback: bool = True,
    forcar_falha_core: bool = False,
) -> Dict[str, Any]:
    """
    Calcula valuation usando o motor preferido.

    Regra principal:
    - Se o motor preferido for Legacy e der erro, o erro sobe.
    - Se o motor preferido for Core Engine e der erro, o sistema tenta Legacy.
    - Se Legacy também falhar, o erro sobe com contexto.
    """
    metadados_base = _criar_metadados_base(
        motor_preferido=motor_preferido,
        moeda=moeda,
        permitir_fallback=permitir_fallback,
    )

    motor_id = metadados_base["motor_preferido_id"]

    try:
        resultado = _calcular_com_motor(
            entradas=entradas,
            motor=motor_preferido,
            moeda=moeda,
            forcar_falha_core=forcar_falha_core,
        )

        return {
            **resultado,
            **metadados_base,
            "motor_executado": resultado.get(
                "motor_selecionado",
                obter_rotulo_motor_por_id(motor_id),
            ),
            "motor_executado_id": resultado.get("motor_id", motor_id),
            "fallback_ocorreu": False,
            "status_fallback": STATUS_FALLBACK_NAO_NECESSARIO,
            "erro_motor_preferido": "",
            "erro_fallback": "",
            "data_resultado_fallback": _agora_iso(),
        }

    except Exception as erro_motor_preferido:
        erro_preferido_texto = _safe_str(erro_motor_preferido)

        if motor_id != "core":
            raise RuntimeError(
                f"Falha no motor Legacy. Fallback não aplicável. Erro: {erro_preferido_texto}"
            ) from erro_motor_preferido

        if not permitir_fallback:
            raise RuntimeError(
                f"Falha no Core Engine e fallback desabilitado. Erro: {erro_preferido_texto}"
            ) from erro_motor_preferido

        try:
            resultado_fallback = _calcular_com_motor(
                entradas=entradas,
                motor=MOTOR_LEGACY,
                moeda=moeda,
                forcar_falha_core=False,
            )

            return {
                **resultado_fallback,
                **metadados_base,
                "motor_executado": MOTOR_LEGACY,
                "motor_executado_id": "legacy",
                "fallback_ocorreu": True,
                "status_fallback": STATUS_FALLBACK_EXECUTADO,
                "erro_motor_preferido": erro_preferido_texto,
                "erro_fallback": "",
                "data_resultado_fallback": _agora_iso(),
            }

        except Exception as erro_fallback:
            raise RuntimeError(
                "Falha crítica: Core Engine falhou e o fallback para Legacy também falhou. "
                f"Erro Core: {erro_preferido_texto}. "
                f"Erro Legacy: {_safe_str(erro_fallback)}"
            ) from erro_fallback


def gerar_resumo_fallback(
    resultado: Dict[str, Any],
) -> Dict[str, str]:
    """
    Gera resumo legível do cálculo com fallback.
    """
    return {
        "Motor preferido": str(resultado.get("motor_preferido", "")),
        "Motor executado": str(resultado.get("motor_executado", "")),
        "Fallback ocorreu": "Sim" if resultado.get("fallback_ocorreu") else "Não",
        "Status fallback": str(resultado.get("status_fallback", "")),
        "Status valuation": str(resultado.get("status", "")),
        "Preço-teto": str(resultado.get("preco_teto", "")),
        "Versão fallback": str(resultado.get("versao_fallback_motor", "")),
        "Versão motor controlado": str(resultado.get("versao_motor_controlado", "")),
        "Erro motor preferido": str(resultado.get("erro_motor_preferido", "")),
        "Data": str(resultado.get("data_resultado_fallback", "")),
    }


def gerar_tabela_resumo_fallback(
    resultado: Dict[str, Any],
) -> List[Dict[str, str]]:
    resumo = gerar_resumo_fallback(resultado)

    return [
        {
            "Campo": chave,
            "Valor": valor,
        }
        for chave, valor in resumo.items()
    ]


def gerar_markdown_fallback_motor(
    resultado: Dict[str, Any],
) -> str:
    """
    Gera relatório técnico do cálculo com fallback.
    """
    linhas = "\n".join(
        [
            f"| {linha['Campo']} | {linha['Valor']} |"
            for linha in gerar_tabela_resumo_fallback(resultado)
        ]
    )

    leitura = (
        "O cálculo foi executado diretamente pelo motor preferido."
        if not resultado.get("fallback_ocorreu")
        else "O motor preferido falhou e o sistema executou fallback automático para Legacy."
    )

    return f"""# Relatório de Fallback do Motor de Valuation

Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Resumo

| Campo | Valor |
|---|---|
{linhas}

## Leitura técnica

{leitura}

## Regra de segurança

Se o Core Engine falhar durante a transição, o sistema deve retornar automaticamente para Legacy.
Isso reduz o risco de quebra do app principal enquanto o Core Engine ainda está em processo de migração.
"""


def gerar_entradas_exemplo_fallback() -> EntradasValuation:
    """
    Gera entradas de exemplo para autotestes.
    """
    return EntradasValuation(
        empresa="Empresa Exemplo Fallback",
        ticker="FBCK3",
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


def executar_autoteste_fallback_motor() -> List[Dict[str, str]]:
    """
    Executa testes básicos do fallback seguro.
    """
    testes = []
    entradas = gerar_entradas_exemplo_fallback()

    resultado_legacy = calcular_valuation_com_fallback(
        entradas=entradas,
        motor_preferido=MOTOR_LEGACY,
        moeda="R$",
    )

    testes.append(
        {
            "teste": "legacy_calcula_sem_fallback",
            "status": (
                "OK"
                if resultado_legacy.get("preco_teto", 0) != 0
                and not resultado_legacy.get("fallback_ocorreu")
                else "FALHA"
            ),
            "detalhe": f"Motor executado: {resultado_legacy.get('motor_executado')}",
        }
    )

    resultado_core = calcular_valuation_com_fallback(
        entradas=entradas,
        motor_preferido=MOTOR_CORE,
        moeda="R$",
    )

    testes.append(
        {
            "teste": "core_calcula_sem_fallback",
            "status": (
                "OK"
                if resultado_core.get("preco_teto", 0) != 0
                and not resultado_core.get("fallback_ocorreu")
                else "FALHA"
            ),
            "detalhe": f"Motor executado: {resultado_core.get('motor_executado')}",
        }
    )

    resultado_core_com_falha = calcular_valuation_com_fallback(
        entradas=entradas,
        motor_preferido=MOTOR_CORE,
        moeda="R$",
        permitir_fallback=True,
        forcar_falha_core=True,
    )

    testes.append(
        {
            "teste": "core_falha_e_usa_fallback_legacy",
            "status": (
                "OK"
                if resultado_core_com_falha.get("preco_teto", 0) != 0
                and resultado_core_com_falha.get("fallback_ocorreu")
                and resultado_core_com_falha.get("motor_executado_id") == "legacy"
                else "FALHA"
            ),
            "detalhe": (
                f"Status fallback: {resultado_core_com_falha.get('status_fallback')}"
            ),
        }
    )

    try:
        calcular_valuation_com_fallback(
            entradas=entradas,
            motor_preferido=MOTOR_CORE,
            moeda="R$",
            permitir_fallback=False,
            forcar_falha_core=True,
        )

        testes.append(
            {
                "teste": "core_falha_sem_fallback_gera_erro",
                "status": "FALHA",
                "detalhe": "Era esperado erro, mas o cálculo passou.",
            }
        )
    except RuntimeError:
        testes.append(
            {
                "teste": "core_falha_sem_fallback_gera_erro",
                "status": "OK",
                "detalhe": "Erro capturado corretamente.",
            }
        )

    testes.append(
        {
            "teste": "resultado_tem_metadados_fallback",
            "status": (
                "OK"
                if "versao_fallback_motor" in resultado_core_com_falha
                and "status_fallback" in resultado_core_com_falha
                and "erro_motor_preferido" in resultado_core_com_falha
                else "FALHA"
            ),
            "detalhe": f"Versão: {resultado_core_com_falha.get('versao_fallback_motor')}",
        }
    )

    testes.append(
        {
            "teste": "motor_padrao_permanece_legacy",
            "status": "OK" if obter_motor_padrao() == MOTOR_LEGACY else "FALHA",
            "detalhe": f"Motor padrão: {obter_motor_padrao()}",
        }
    )

    return testes