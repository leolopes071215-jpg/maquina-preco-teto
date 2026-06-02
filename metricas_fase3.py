# metricas_fase3.py

import csv
import uuid
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List

import streamlit as st


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v3.4 — Métricas de Negócio, Receita, Retenção e Unit Economics
# ------------------------------------------------------------
# Esta tela consolida métricas financeiras e operacionais da Fase 3.
#
# Objetivo:
# - medir receita real, MRR, ARR, ticket médio e churn
# - avaliar suporte, retenção, NPS e eficiência operacional
# - registrar snapshots manuais de métricas
# - decidir se o negócio está pronto para vender mais ou automatizar
# ============================================================


CAMINHO_CLIENTES_BETA = Path("clientes_beta.csv")
CAMINHO_SUPORTE_BETA = Path("suporte_beta.csv")
CAMINHO_RETENCAO_BETA = Path("retencao_beta.csv")
CAMINHO_METRICAS_FASE3 = Path("metricas_fase3.csv")


CAMPOS_METRICAS = [
    "id",
    "data_registro",
    "periodo",
    "receita_real",
    "mrr_estimado",
    "arr_estimado",
    "clientes_pagos",
    "clientes_ativos",
    "ticket_medio",
    "nps_medio",
    "tickets_abertos",
    "tickets_criticos",
    "clientes_em_risco",
    "renovacoes",
    "cancelamentos",
    "cac_estimado",
    "horas_suporte_mes",
    "custo_hora_estimado",
    "observacoes",
]


def _garantir_arquivo_metricas() -> None:
    if CAMINHO_METRICAS_FASE3.exists():
        return

    with open(CAMINHO_METRICAS_FASE3, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_METRICAS)
        escritor.writeheader()


def carregar_metricas_fase3() -> List[Dict[str, str]]:
    _garantir_arquivo_metricas()

    with open(CAMINHO_METRICAS_FASE3, "r", newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        return [
            {campo: linha.get(campo, "") for campo in CAMPOS_METRICAS}
            for linha in leitor
        ]


def salvar_metricas_fase3(registros: List[Dict[str, Any]]) -> None:
    with open(CAMINHO_METRICAS_FASE3, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_METRICAS)
        escritor.writeheader()

        for registro in registros:
            escritor.writerow({campo: registro.get(campo, "") for campo in CAMPOS_METRICAS})


def limpar_metricas_fase3() -> None:
    salvar_metricas_fase3([])


def _carregar_csv(caminho: Path) -> List[Dict[str, str]]:
    if not caminho.exists():
        return []

    try:
        with open(caminho, "r", newline="", encoding="utf-8") as arquivo:
            leitor = csv.DictReader(arquivo)
            return [dict(linha) for linha in leitor]
    except Exception:
        return []


def _safe_float(valor: Any, default: float = 0.0) -> float:
    try:
        texto = str(valor).replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
        return float(texto)
    except (TypeError, ValueError):
        return default


def _safe_int(valor: Any, default: int = 0) -> int:
    try:
        return int(float(valor))
    except (TypeError, ValueError):
        return default


def _fmt_moeda(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_percentual(valor: float) -> str:
    return f"{valor:.1f}%"


def _contar(registros: List[Dict[str, str]], campo: str, valor: str) -> int:
    return len([registro for registro in registros if registro.get(campo) == valor])


def _media_campo(registros: List[Dict[str, str]], campo: str) -> float:
    valores = []

    for registro in registros:
        valor = _safe_float(registro.get(campo))

        if valor >= 0:
            valores.append(valor)

    if len(valores) == 0:
        return 0.0

    return mean(valores)


def _receita_real(clientes: List[Dict[str, str]]) -> float:
    return sum(
        _safe_float(cliente.get("valor_pago"))
        for cliente in clientes
        if cliente.get("status_pagamento") == "Pago"
    )


def _clientes_pagos(clientes: List[Dict[str, str]]) -> int:
    return _contar(clientes, "status_pagamento", "Pago")


def _clientes_ativos(clientes: List[Dict[str, str]]) -> int:
    status_ativos = ["Ativo", "Em onboarding", "Precisa de suporte", "Em risco"]

    return len(
        [
            cliente for cliente in clientes
            if cliente.get("status_pagamento") == "Pago"
            and cliente.get("status_cliente") in status_ativos
        ]
    )


def _mrr_estimado(clientes: List[Dict[str, str]]) -> float:
    total = 0.0

    for cliente in clientes:
        if cliente.get("status_pagamento") != "Pago":
            continue

        valor = _safe_float(cliente.get("valor_pago"))
        periodicidade = cliente.get("periodicidade", "")

        if periodicidade == "Mensal":
            total += valor
        elif periodicidade == "Trimestral":
            total += valor / 3
        elif periodicidade == "Anual":
            total += valor / 12

    return total


def _arr_estimado(clientes: List[Dict[str, str]]) -> float:
    return _mrr_estimado(clientes) * 12


def _ticket_medio(clientes: List[Dict[str, str]]) -> float:
    pagos = [
        _safe_float(cliente.get("valor_pago"))
        for cliente in clientes
        if cliente.get("status_pagamento") == "Pago"
    ]

    if len(pagos) == 0:
        return 0.0

    return mean(pagos)


def _clientes_em_risco_clientes(clientes: List[Dict[str, str]]) -> int:
    return len(
        [
            cliente for cliente in clientes
            if cliente.get("risco_cancelamento") in ["Alto", "Crítico"]
            or cliente.get("status_cliente") == "Em risco"
        ]
    )


def _tickets_abertos(suporte: List[Dict[str, str]]) -> int:
    status_fechados = ["Resolvido", "Fechado", "Virou melhoria de produto"]

    return len(
        [
            ticket for ticket in suporte
            if ticket.get("status_atendimento") not in status_fechados
        ]
    )


def _tickets_criticos(suporte: List[Dict[str, str]]) -> int:
    return len(
        [
            ticket for ticket in suporte
            if ticket.get("prioridade") == "Crítica"
            or ticket.get("risco_cancelamento") == "Crítico"
            or ticket.get("impacto_cliente") == "Impede o uso"
        ]
    )


def _tickets_resolvidos(suporte: List[Dict[str, str]]) -> int:
    return len(
        [
            ticket for ticket in suporte
            if ticket.get("status_atendimento") in ["Resolvido", "Fechado"]
        ]
    )


def _taxa_resolucao(suporte: List[Dict[str, str]]) -> float:
    if len(suporte) == 0:
        return 0.0

    return (_tickets_resolvidos(suporte) / len(suporte)) * 100


def _tempo_medio_suporte(suporte: List[Dict[str, str]]) -> float:
    return _media_campo(suporte, "tempo_resposta_horas")


def _satisfacao_media_suporte(suporte: List[Dict[str, str]]) -> float:
    return _media_campo(suporte, "satisfacao_pos_atendimento")


def _nps_medio(retencao: List[Dict[str, str]]) -> float:
    return _media_campo(retencao, "nps")


def _renovacoes(retencao: List[Dict[str, str]]) -> int:
    return _contar(retencao, "status_renovacao", "Renovou") + _contar(
        retencao,
        "status_cliente",
        "Renovou",
    )


def _cancelamentos(retencao: List[Dict[str, str]]) -> int:
    return _contar(retencao, "status_cliente", "Cancelado") + _contar(
        retencao,
        "status_renovacao",
        "Não renovou",
    )


def _clientes_em_risco_retencao(retencao: List[Dict[str, str]]) -> int:
    return len(
        [
            registro for registro in retencao
            if registro.get("risco_churn") in ["Alto", "Crítico"]
            or registro.get("saude_cliente") in ["Risco", "Crítica"]
            or registro.get("status_cliente") in ["Em risco", "Cancelado", "Não renovou"]
        ]
    )


def _taxa_churn(retencao: List[Dict[str, str]]) -> float:
    if len(retencao) == 0:
        return 0.0

    return (_cancelamentos(retencao) / len(retencao)) * 100


def _taxa_renovacao(retencao: List[Dict[str, str]]) -> float:
    if len(retencao) == 0:
        return 0.0

    return (_renovacoes(retencao) / len(retencao)) * 100


def _registrar_snapshot(
    periodo: str,
    receita_real: float,
    mrr_estimado: float,
    arr_estimado: float,
    clientes_pagos: int,
    clientes_ativos: int,
    ticket_medio: float,
    nps_medio: float,
    tickets_abertos: int,
    tickets_criticos: int,
    clientes_em_risco: int,
    renovacoes: int,
    cancelamentos: int,
    cac_estimado: float,
    horas_suporte_mes: float,
    custo_hora_estimado: float,
    observacoes: str,
) -> None:
    registros = carregar_metricas_fase3()

    registros.append(
        {
            "id": str(uuid.uuid4())[:8],
            "data_registro": datetime.now().isoformat(timespec="minutes"),
            "periodo": periodo.strip(),
            "receita_real": str(receita_real),
            "mrr_estimado": str(mrr_estimado),
            "arr_estimado": str(arr_estimado),
            "clientes_pagos": str(clientes_pagos),
            "clientes_ativos": str(clientes_ativos),
            "ticket_medio": str(ticket_medio),
            "nps_medio": str(nps_medio),
            "tickets_abertos": str(tickets_abertos),
            "tickets_criticos": str(tickets_criticos),
            "clientes_em_risco": str(clientes_em_risco),
            "renovacoes": str(renovacoes),
            "cancelamentos": str(cancelamentos),
            "cac_estimado": str(cac_estimado),
            "horas_suporte_mes": str(horas_suporte_mes),
            "custo_hora_estimado": str(custo_hora_estimado),
            "observacoes": observacoes.strip(),
        }
    )

    salvar_metricas_fase3(registros)


def _calcular_metricas_unitarias(
    clientes: List[Dict[str, str]],
    suporte: List[Dict[str, str]],
    retencao: List[Dict[str, str]],
    cac_estimado: float,
    horas_suporte_mes: float,
    custo_hora_estimado: float,
) -> Dict[str, float]:
    clientes_pagos = _clientes_pagos(clientes)
    mrr = _mrr_estimado(clientes)
    ticket = _ticket_medio(clientes)
    churn = _taxa_churn(retencao) / 100
    custo_suporte = horas_suporte_mes * custo_hora_estimado

    if clientes_pagos > 0:
        suporte_por_cliente = custo_suporte / clientes_pagos
    else:
        suporte_por_cliente = 0.0

    if churn > 0:
        ltv_estimado = ticket / churn
    else:
        ltv_estimado = ticket * 12 if ticket > 0 else 0.0

    if cac_estimado > 0:
        ltv_cac = ltv_estimado / cac_estimado
    else:
        ltv_cac = 0.0

    if mrr > 0 and cac_estimado > 0:
        payback_meses = cac_estimado / mrr
    else:
        payback_meses = 0.0

    margem_operacional_simples = mrr - custo_suporte

    return {
        "custo_suporte": custo_suporte,
        "suporte_por_cliente": suporte_por_cliente,
        "ltv_estimado": ltv_estimado,
        "ltv_cac": ltv_cac,
        "payback_meses": payback_meses,
        "margem_operacional_simples": margem_operacional_simples,
    }


def _score_receita(clientes: List[Dict[str, str]]) -> int:
    pagos = _clientes_pagos(clientes)
    ativos = _clientes_ativos(clientes)
    receita = _receita_real(clientes)
    mrr = _mrr_estimado(clientes)

    pontos = 0.0
    pontos += min(pagos * 18.0, 45)
    pontos += min(ativos * 10.0, 25)
    pontos += min(receita / 8, 20)
    pontos += min(mrr / 8, 20)

    return int(round(max(0, min(100, pontos))))


def _score_retencao(retencao: List[Dict[str, str]]) -> int:
    if len(retencao) == 0:
        return 0

    nps = _nps_medio(retencao)
    renovacoes = _renovacoes(retencao)
    cancelamentos = _cancelamentos(retencao)
    risco = _clientes_em_risco_retencao(retencao)

    valor_alto = _contar(retencao, "valor_percebido", "Alto") + _contar(
        retencao,
        "valor_percebido",
        "Muito alto",
    )

    uso_bom = _contar(retencao, "uso_percebido", "Usa com frequência") + _contar(
        retencao,
        "uso_percebido",
        "Usa ocasionalmente",
    )

    pontos = 0.0
    pontos += nps * 4.0
    pontos += min(renovacoes * 18.0, 36)
    pontos += min(valor_alto * 10.0, 25)
    pontos += min(uso_bom * 8.0, 20)
    pontos -= min(cancelamentos * 18.0, 36)
    pontos -= min(risco * 10.0, 30)

    return int(round(max(0, min(100, pontos))))


def _score_suporte(suporte: List[Dict[str, str]]) -> int:
    if len(suporte) == 0:
        return 65

    taxa = _taxa_resolucao(suporte)
    satisfacao = _satisfacao_media_suporte(suporte)
    tempo = _tempo_medio_suporte(suporte)
    abertos = _tickets_abertos(suporte)
    criticos = _tickets_criticos(suporte)

    pontos = 0.0
    pontos += taxa * 0.35
    pontos += satisfacao * 4.0

    if tempo > 0:
        if tempo <= 2:
            pontos += 18
        elif tempo <= 8:
            pontos += 12
        elif tempo <= 24:
            pontos += 6
        else:
            pontos -= 10

    pontos -= min(abertos * 4.0, 20)
    pontos -= min(criticos * 12.0, 36)

    return int(round(max(0, min(100, pontos))))


def _score_unit_economics(unit: Dict[str, float], clientes: List[Dict[str, str]]) -> int:
    mrr = _mrr_estimado(clientes)
    ltv_cac = unit["ltv_cac"]
    payback = unit["payback_meses"]
    margem = unit["margem_operacional_simples"]

    pontos = 0.0

    if mrr > 0:
        pontos += 25

    if margem > 0:
        pontos += 20

    if ltv_cac >= 3:
        pontos += 30
    elif ltv_cac >= 2:
        pontos += 20
    elif ltv_cac >= 1:
        pontos += 10

    if payback == 0:
        pontos += 5
    elif payback <= 1:
        pontos += 20
    elif payback <= 3:
        pontos += 12
    elif payback <= 6:
        pontos += 6

    if _clientes_pagos(clientes) >= 3:
        pontos += 10

    return int(round(max(0, min(100, pontos))))


def _score_geral(
    clientes: List[Dict[str, str]],
    suporte: List[Dict[str, str]],
    retencao: List[Dict[str, str]],
    unit: Dict[str, float],
) -> Dict[str, int]:
    receita = _score_receita(clientes)
    ret = _score_retencao(retencao)
    sup = _score_suporte(suporte)
    unit_score = _score_unit_economics(unit, clientes)

    geral = int(round(receita * 0.30 + ret * 0.30 + sup * 0.20 + unit_score * 0.20))

    return {
        "geral": max(0, min(100, geral)),
        "receita": receita,
        "retencao": ret,
        "suporte": sup,
        "unit_economics": unit_score,
    }


def _classificar(score: int) -> str:
    if score >= 85:
        return "Negócio beta forte"
    if score >= 70:
        return "Negócio beta saudável"
    if score >= 55:
        return "Negócio em validação"
    if score >= 40:
        return "Negócio frágil"
    return "Negócio ainda imaturo"


def _decisao(scores: Dict[str, int], clientes: List[Dict[str, str]], suporte: List[Dict[str, str]], retencao: List[Dict[str, str]]) -> str:
    if _clientes_pagos(clientes) == 0:
        return "Buscar primeiros clientes pagos antes de otimizar métricas"

    if _tickets_criticos(suporte) > 0:
        return "Resolver suporte crítico antes de vender mais"

    if _clientes_em_risco_retencao(retencao) > 0:
        return "Priorizar retenção e reduzir risco de churn"

    if _cancelamentos(retencao) > 0 and _renovacoes(retencao) == 0:
        return "Investigar cancelamentos antes de escalar"

    if scores["geral"] >= 85 and scores["retencao"] >= 70 and scores["unit_economics"] >= 65:
        return "Preparar automação leve e novo lote controlado de vendas"

    if scores["geral"] >= 70:
        return "Vender pequeno lote adicional mantendo suporte próximo"

    if scores["receita"] < 50:
        return "Aumentar conversas de venda manual e validar preço"

    if scores["retencao"] < 55 and len(retencao) > 0:
        return "Melhorar onboarding, valor percebido e uso real"

    return "Continuar medindo, vendendo pouco e melhorando entrega"


def _gerar_tabela_metricas(
    clientes: List[Dict[str, str]],
    suporte: List[Dict[str, str]],
    retencao: List[Dict[str, str]],
    unit: Dict[str, float],
) -> List[Dict[str, str]]:
    return [
        {
            "Métrica": "Receita real",
            "Valor": _fmt_moeda(_receita_real(clientes)),
            "Leitura": "Dinheiro confirmado no beta.",
        },
        {
            "Métrica": "MRR estimado",
            "Valor": _fmt_moeda(_mrr_estimado(clientes)),
            "Leitura": "Receita recorrente mensal estimada.",
        },
        {
            "Métrica": "ARR estimado",
            "Valor": _fmt_moeda(_arr_estimado(clientes)),
            "Leitura": "MRR anualizado.",
        },
        {
            "Métrica": "Clientes pagos",
            "Valor": str(_clientes_pagos(clientes)),
            "Leitura": "Validação comercial real.",
        },
        {
            "Métrica": "Clientes ativos pagos",
            "Valor": str(_clientes_ativos(clientes)),
            "Leitura": "Pagantes que ainda estão em entrega.",
        },
        {
            "Métrica": "Ticket médio",
            "Valor": _fmt_moeda(_ticket_medio(clientes)),
            "Leitura": "Valor médio por cliente pago.",
        },
        {
            "Métrica": "NPS médio",
            "Valor": f"{_nps_medio(retencao):.1f}/10",
            "Leitura": "Sinal de satisfação e intenção de continuidade.",
        },
        {
            "Métrica": "Taxa de churn",
            "Valor": _fmt_percentual(_taxa_churn(retencao)),
            "Leitura": "Cancelamento ou não renovação nos registros de retenção.",
        },
        {
            "Métrica": "Taxa de renovação",
            "Valor": _fmt_percentual(_taxa_renovacao(retencao)),
            "Leitura": "Sinal de valor sustentado.",
        },
        {
            "Métrica": "Tickets críticos",
            "Valor": str(_tickets_criticos(suporte)),
            "Leitura": "Travamento de suporte que pode impedir escala.",
        },
        {
            "Métrica": "Taxa de resolução suporte",
            "Valor": _fmt_percentual(_taxa_resolucao(suporte)),
            "Leitura": "Qualidade operacional do atendimento.",
        },
        {
            "Métrica": "Custo suporte estimado",
            "Valor": _fmt_moeda(unit["custo_suporte"]),
            "Leitura": "Horas de suporte vezes custo/hora.",
        },
        {
            "Métrica": "Suporte por cliente",
            "Valor": _fmt_moeda(unit["suporte_por_cliente"]),
            "Leitura": "Custo médio operacional por cliente.",
        },
        {
            "Métrica": "LTV estimado",
            "Valor": _fmt_moeda(unit["ltv_estimado"]),
            "Leitura": "Estimativa simples baseada em ticket e churn.",
        },
        {
            "Métrica": "LTV/CAC",
            "Valor": f"{unit['ltv_cac']:.2f}x",
            "Leitura": "Relação entre valor vitalício e custo de aquisição.",
        },
        {
            "Métrica": "Payback estimado",
            "Valor": f"{unit['payback_meses']:.1f} mês(es)",
            "Leitura": "Tempo estimado para recuperar CAC.",
        },
        {
            "Métrica": "Margem operacional simples",
            "Valor": _fmt_moeda(unit["margem_operacional_simples"]),
            "Leitura": "MRR menos custo de suporte estimado.",
        },
    ]


def _gerar_alertas(
    clientes: List[Dict[str, str]],
    suporte: List[Dict[str, str]],
    retencao: List[Dict[str, str]],
    unit: Dict[str, float],
    scores: Dict[str, int],
) -> List[str]:
    alertas = []

    if _clientes_pagos(clientes) == 0:
        alertas.append("Nenhum cliente pago confirmado. A métrica mais importante agora é venda manual.")

    if _tickets_criticos(suporte) > 0:
        alertas.append("Existem tickets críticos. Não escale aquisição antes de resolver.")

    if _clientes_em_risco_retencao(retencao) > 0:
        alertas.append("Existem clientes em risco de churn. Priorize retenção.")

    if _cancelamentos(retencao) > 0:
        alertas.append("Há cancelamento ou não renovação. Investigue causa raiz.")

    if _nps_medio(retencao) < 7 and len(retencao) >= 2:
        alertas.append("NPS médio abaixo de 7. Valor percebido ainda não está forte.")

    if unit["margem_operacional_simples"] < 0 and _mrr_estimado(clientes) > 0:
        alertas.append("Custo de suporte estimado maior que MRR. A operação pode não escalar bem.")

    if unit["ltv_cac"] > 0 and unit["ltv_cac"] < 1:
        alertas.append("LTV/CAC abaixo de 1. Aquisição paga ainda não faz sentido.")

    if scores["unit_economics"] < 50 and _clientes_pagos(clientes) > 0:
        alertas.append("Unit economics ainda frágil. Continue manual e evite automação pesada.")

    if len(alertas) == 0:
        alertas.append("Sem alerta crítico. Continue medindo antes de acelerar.")

    return alertas


def _gerar_acoes(
    clientes: List[Dict[str, str]],
    suporte: List[Dict[str, str]],
    retencao: List[Dict[str, str]],
    unit: Dict[str, float],
    scores: Dict[str, int],
) -> List[Dict[str, str]]:
    acoes = []

    if _clientes_pagos(clientes) == 0:
        acoes.append(
            {
                "Prioridade": "Muito alta",
                "Ação": "Vender manualmente para o primeiro cliente",
                "Motivo": "Sem pagamento não há validação comercial.",
            }
        )

    if _tickets_criticos(suporte) > 0:
        acoes.append(
            {
                "Prioridade": "Muito alta",
                "Ação": "Resolver suporte crítico",
                "Motivo": "Suporte crítico destrói confiança e retenção.",
            }
        )

    if len(retencao) == 0 and _clientes_pagos(clientes) > 0:
        acoes.append(
            {
                "Prioridade": "Alta",
                "Ação": "Registrar retenção dos clientes pagos",
                "Motivo": "Venda sem retenção não prova negócio.",
            }
        )

    if _nps_medio(retencao) < 7 and len(retencao) >= 2:
        acoes.append(
            {
                "Prioridade": "Alta",
                "Ação": "Melhorar onboarding e valor percebido",
                "Motivo": "NPS baixo indica que a entrega ainda não convenceu.",
            }
        )

    if unit["margem_operacional_simples"] < 0 and _mrr_estimado(clientes) > 0:
        acoes.append(
            {
                "Prioridade": "Alta",
                "Ação": "Reduzir carga de suporte por cliente",
                "Motivo": "Custo operacional pode engolir a receita recorrente.",
            }
        )

    if scores["geral"] >= 70 and _tickets_criticos(suporte) == 0:
        acoes.append(
            {
                "Prioridade": "Média",
                "Ação": "Abrir novo pequeno lote de clientes beta",
                "Motivo": "Métricas indicam maturidade suficiente para teste controlado.",
            }
        )

    if scores["geral"] >= 85 and scores["unit_economics"] >= 65:
        acoes.append(
            {
                "Prioridade": "Média",
                "Ação": "Preparar automação leve de pagamento e acesso",
                "Motivo": "O negócio começa a ter sinal de escala operacional.",
            }
        )

    if len(acoes) == 0:
        acoes.append(
            {
                "Prioridade": "Média",
                "Ação": "Manter ciclo semanal de métricas",
                "Motivo": "Continuar medindo receita, retenção, suporte e churn.",
            }
        )

    return acoes


def _gerar_tabela_snapshots(registros: List[Dict[str, str]]) -> List[Dict[str, str]]:
    tabela = []

    for registro in reversed(registros):
        tabela.append(
            {
                "Período": registro.get("periodo", ""),
                "Data": registro.get("data_registro", ""),
                "Receita": _fmt_moeda(_safe_float(registro.get("receita_real"))),
                "MRR": _fmt_moeda(_safe_float(registro.get("mrr_estimado"))),
                "ARR": _fmt_moeda(_safe_float(registro.get("arr_estimado"))),
                "Clientes pagos": registro.get("clientes_pagos", ""),
                "Ativos": registro.get("clientes_ativos", ""),
                "Ticket médio": _fmt_moeda(_safe_float(registro.get("ticket_medio"))),
                "NPS": f"{_safe_float(registro.get('nps_medio')):.1f}/10",
                "Críticos": registro.get("tickets_criticos", ""),
                "Risco": registro.get("clientes_em_risco", ""),
                "Cancelamentos": registro.get("cancelamentos", ""),
            }
        )

    return tabela


def _gerar_markdown_metricas(
    clientes: List[Dict[str, str]],
    suporte: List[Dict[str, str]],
    retencao: List[Dict[str, str]],
    unit: Dict[str, float],
    scores: Dict[str, int],
) -> str:
    classificacao = _classificar(scores["geral"])
    decisao = _decisao(scores, clientes, suporte, retencao)

    linhas_metricas = "\n".join(
        [
            f"| {item['Métrica']} | {item['Valor']} | {item['Leitura']} |"
            for item in _gerar_tabela_metricas(clientes, suporte, retencao, unit)
        ]
    )

    linhas_alertas = "\n".join(
        [
            f"- {alerta}"
            for alerta in _gerar_alertas(clientes, suporte, retencao, unit, scores)
        ]
    )

    linhas_acoes = "\n".join(
        [
            f"| {acao['Prioridade']} | {acao['Ação']} | {acao['Motivo']} |"
            for acao in _gerar_acoes(clientes, suporte, retencao, unit, scores)
        ]
    )

    return f"""# Métricas da Fase 3 — Máquina de Preço-Teto

Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Diagnóstico

**Score geral:** {scores["geral"]}/100  
**Score receita:** {scores["receita"]}/100  
**Score retenção:** {scores["retencao"]}/100  
**Score suporte:** {scores["suporte"]}/100  
**Score unit economics:** {scores["unit_economics"]}/100  

**Classificação:** {classificacao}  
**Decisão:** {decisao}

## Métricas

| Métrica | Valor | Leitura |
|---|---:|---|
{linhas_metricas}

## Alertas

{linhas_alertas}

## Ações recomendadas

| Prioridade | Ação | Motivo |
|---|---|---|
{linhas_acoes}

## Regra

O negócio só deve escalar quando receita, retenção, suporte e unit economics mostrarem sinais positivos juntos.
"""


def _injetar_css_metricas() -> None:
    st.markdown(
        """
        <style>
            .mf3-hero {
                padding: 1.75rem 1.8rem;
                border-radius: 30px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    radial-gradient(circle at top left, rgba(214, 181, 109, 0.25), transparent 30%),
                    radial-gradient(circle at bottom right, rgba(74, 144, 226, 0.22), transparent 34%),
                    linear-gradient(135deg, rgba(8, 15, 27, 0.99), rgba(5, 9, 18, 0.99));
                box-shadow: 0 18px 55px rgba(0, 0, 0, 0.34);
                margin-bottom: 1.25rem;
            }

            .mf3-eyebrow {
                color: #d6b56d;
                font-size: 0.78rem;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.35rem;
            }

            .mf3-title {
                color: #f4f7fb;
                font-size: 2.1rem;
                font-weight: 900;
                margin-bottom: 0.45rem;
                line-height: 1.14;
            }

            .mf3-subtitle {
                color: rgba(244, 247, 251, 0.76);
                font-size: 1rem;
                line-height: 1.62;
                max-width: 1080px;
            }

            .mf3-card {
                padding: 1.1rem 1.15rem;
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.035);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.18);
                height: 100%;
            }

            .mf3-card-label {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .mf3-card-value {
                color: #f4f7fb;
                font-size: 1.22rem;
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .mf3-card-note {
                color: rgba(244, 247, 251, 0.68);
                font-size: 0.87rem;
                line-height: 1.47;
            }

            .mf3-highlight {
                padding: 0.95rem 1rem;
                border-radius: 16px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.92rem;
                line-height: 1.55;
                margin-bottom: 0.7rem;
            }

            .mf3-disclaimer {
                padding: 0.95rem 1rem;
                border-radius: 16px;
                background: rgba(74, 144, 226, 0.08);
                border: 1px solid rgba(74, 144, 226, 0.18);
                color: rgba(244, 247, 251, 0.78);
                font-size: 0.9rem;
                line-height: 1.55;
                margin-top: 1.1rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _card(label: str, value: str, note: str = "") -> None:
    st.markdown(
        f"""
        <div class="mf3-card">
            <div class="mf3-card-label">{label}</div>
            <div class="mf3-card-value">{value}</div>
            <div class="mf3-card-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def renderizar_metricas_fase3() -> None:
    """
    Renderiza a central de métricas da Fase 3.
    """
    _injetar_css_metricas()

    clientes = _carregar_csv(CAMINHO_CLIENTES_BETA)
    suporte = _carregar_csv(CAMINHO_SUPORTE_BETA)
    retencao = _carregar_csv(CAMINHO_RETENCAO_BETA)
    snapshots = carregar_metricas_fase3()

    receita = _receita_real(clientes)
    mrr = _mrr_estimado(clientes)
    arr = _arr_estimado(clientes)
    pagos = _clientes_pagos(clientes)
    ativos = _clientes_ativos(clientes)
    ticket = _ticket_medio(clientes)
    nps = _nps_medio(retencao)
    tickets_abertos = _tickets_abertos(suporte)
    tickets_criticos = _tickets_criticos(suporte)
    risco = _clientes_em_risco_clientes(clientes) + _clientes_em_risco_retencao(retencao)
    renovacoes = _renovacoes(retencao)
    cancelamentos = _cancelamentos(retencao)

    st.markdown(
        """
        <div class="mf3-hero">
            <div class="mf3-eyebrow">Fase 3.4 — Métricas e unit economics</div>
            <div class="mf3-title">Métricas de Negócio, Receita, Retenção e Unit Economics</div>
            <div class="mf3-subtitle">
                Meça receita real, MRR, ARR, ticket médio, churn, suporte, NPS e eficiência operacional.
                O objetivo é decidir se o negócio pode vender mais, corrigir a entrega ou preparar automação.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="mf3-highlight">
            Produto excelente não é só bonito. Ele precisa vender, entregar valor, reter clientes e operar sem quebrar.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Premissas manuais para unit economics")

    col_p1, col_p2, col_p3 = st.columns(3)

    with col_p1:
        cac_estimado = st.number_input(
            "CAC estimado por cliente",
            min_value=0.0,
            max_value=10000.0,
            value=0.0,
            step=5.0,
            help="Custo médio estimado para adquirir um cliente. Pode ser zero na venda manual inicial.",
            key="mf3_cac",
        )

    with col_p2:
        horas_suporte_mes = st.number_input(
            "Horas de suporte no mês",
            min_value=0.0,
            max_value=1000.0,
            value=0.0,
            step=1.0,
            help="Estimativa manual de horas gastas com suporte no mês.",
            key="mf3_horas_suporte",
        )

    with col_p3:
        custo_hora_estimado = st.number_input(
            "Custo/hora estimado",
            min_value=0.0,
            max_value=1000.0,
            value=20.0,
            step=5.0,
            help="Valor estimado da sua hora para calcular custo operacional.",
            key="mf3_custo_hora",
        )

    unit = _calcular_metricas_unitarias(
        clientes=clientes,
        suporte=suporte,
        retencao=retencao,
        cac_estimado=cac_estimado,
        horas_suporte_mes=horas_suporte_mes,
        custo_hora_estimado=custo_hora_estimado,
    )

    scores = _score_geral(clientes, suporte, retencao, unit)
    classificacao = _classificar(scores["geral"])
    decisao = _decisao(scores, clientes, suporte, retencao)

    st.session_state["resultado_metricas_fase3"] = {
        "score_geral": scores["geral"],
        "score_receita": scores["receita"],
        "score_retencao": scores["retencao"],
        "score_suporte": scores["suporte"],
        "score_unit_economics": scores["unit_economics"],
        "classificacao": classificacao,
        "decisao": decisao,
        "receita_real": receita,
        "mrr_estimado": mrr,
        "arr_estimado": arr,
        "ticket_medio": ticket,
        "clientes_pagos": pagos,
        "clientes_ativos": ativos,
        "nps_medio": nps,
        "taxa_churn": _taxa_churn(retencao),
        "ltv_estimado": unit["ltv_estimado"],
        "ltv_cac": unit["ltv_cac"],
        "payback_meses": unit["payback_meses"],
    }

    st.divider()

    st.markdown("### Diagnóstico geral das métricas")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Score geral", f"{scores['geral']}/100")

    with col_2:
        st.metric("Classificação", classificacao)

    with col_3:
        st.metric("MRR estimado", _fmt_moeda(mrr))

    with col_4:
        st.metric("LTV/CAC", f"{unit['ltv_cac']:.2f}x")

    st.progress(scores["geral"] / 100)

    if scores["geral"] >= 70:
        st.success(decisao)
    elif scores["geral"] >= 40:
        st.warning(decisao)
    else:
        st.error(decisao)

    st.divider()

    st.markdown("### Indicadores principais")

    col_i1, col_i2, col_i3, col_i4 = st.columns(4)

    with col_i1:
        _card("Receita real", _fmt_moeda(receita), "Dinheiro confirmado.")

    with col_i2:
        _card("ARR estimado", _fmt_moeda(arr), "MRR anualizado.")

    with col_i3:
        _card("Ticket médio", _fmt_moeda(ticket), "Média por cliente pago.")

    with col_i4:
        _card("Churn", _fmt_percentual(_taxa_churn(retencao)), "Cancelamento/não renovação.")

    col_i5, col_i6, col_i7, col_i8 = st.columns(4)

    with col_i5:
        _card("Clientes pagos", str(pagos), f"{ativos} ativos.")

    with col_i6:
        _card("NPS médio", f"{nps:.1f}/10", "Retenção e valor percebido.")

    with col_i7:
        _card("Tickets críticos", str(tickets_criticos), "Travam escala se existirem.")

    with col_i8:
        _card("Payback", f"{unit['payback_meses']:.1f} mês(es)", "Tempo para recuperar CAC.")

    st.divider()

    st.markdown("### Scores por dimensão")

    col_s1, col_s2, col_s3, col_s4 = st.columns(4)

    with col_s1:
        _card("Receita", f"{scores['receita']}/100", "Clientes pagos, MRR e receita.")

    with col_s2:
        _card("Retenção", f"{scores['retencao']}/100", "NPS, uso, churn e renovação.")

    with col_s3:
        _card("Suporte", f"{scores['suporte']}/100", "Tickets, resolução e satisfação.")

    with col_s4:
        _card("Unit economics", f"{scores['unit_economics']}/100", "LTV/CAC, payback e margem.")

    st.divider()

    st.markdown("### Tabela completa de métricas")

    st.dataframe(
        _gerar_tabela_metricas(clientes, suporte, retencao, unit),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Alertas estratégicos")

    for alerta in _gerar_alertas(clientes, suporte, retencao, unit, scores):
        st.markdown(f"- {alerta}")

    st.divider()

    st.markdown("### Ações recomendadas")

    st.dataframe(
        _gerar_acoes(clientes, suporte, retencao, unit, scores),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Registrar snapshot de métricas")

    periodo_padrao = datetime.now().strftime("%m/%Y")

    with st.form("form_metricas_fase3"):
        periodo = st.text_input(
            "Período",
            value=periodo_padrao,
            placeholder="Ex: 06/2026, Semana 1, Lote 1...",
            key="mf3_periodo",
        )

        observacoes = st.text_area(
            "Observações do período",
            value="",
            height=90,
            placeholder="O que aconteceu neste período? O que melhorou? O que piorou?",
            key="mf3_observacoes",
        )

        salvar_snapshot = st.form_submit_button("Salvar snapshot das métricas atuais")

        if salvar_snapshot:
            _registrar_snapshot(
                periodo=periodo,
                receita_real=receita,
                mrr_estimado=mrr,
                arr_estimado=arr,
                clientes_pagos=pagos,
                clientes_ativos=ativos,
                ticket_medio=ticket,
                nps_medio=nps,
                tickets_abertos=tickets_abertos,
                tickets_criticos=tickets_criticos,
                clientes_em_risco=risco,
                renovacoes=renovacoes,
                cancelamentos=cancelamentos,
                cac_estimado=cac_estimado,
                horas_suporte_mes=horas_suporte_mes,
                custo_hora_estimado=custo_hora_estimado,
                observacoes=observacoes,
            )

            st.success("Snapshot de métricas registrado com sucesso.")
            st.rerun()

    st.divider()

    st.markdown("### Histórico de snapshots")

    snapshots = carregar_metricas_fase3()

    if len(snapshots) == 0:
        st.info("Nenhum snapshot de métricas registrado ainda.")
    else:
        st.dataframe(
            _gerar_tabela_snapshots(snapshots),
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    col_download, col_limpar = st.columns(2)

    with col_download:
        st.download_button(
            label="Baixar relatório de métricas da Fase 3 (.md)",
            data=_gerar_markdown_metricas(clientes, suporte, retencao, unit, scores),
            file_name="relatorio_metricas_fase3.md",
            mime="text/markdown",
            key="download_metricas_fase3_md",
        )

        if CAMINHO_METRICAS_FASE3.exists():
            with open(CAMINHO_METRICAS_FASE3, "rb") as arquivo:
                st.download_button(
                    label="Baixar snapshots em CSV",
                    data=arquivo,
                    file_name="metricas_fase3.csv",
                    mime="text/csv",
                    key="download_metricas_fase3_csv",
                )

    with col_limpar:
        confirmar = st.checkbox(
            "Confirmar limpeza dos snapshots",
            value=False,
            key="mf3_confirmar_limpeza",
        )

        if st.button("Limpar snapshots de métricas", key="mf3_limpar"):
            if confirmar:
                limpar_metricas_fase3()
                st.success("Snapshots limpos com sucesso.")
                st.rerun()
            else:
                st.warning("Marque a confirmação antes de limpar.")

    st.markdown(
        """
        <div class="mf3-disclaimer">
            <strong>Regra das métricas:</strong> não escale só porque existe receita.
            Escale quando receita, retenção, suporte e unit economics apontarem na mesma direção.
        </div>
        """,
        unsafe_allow_html=True,
    )