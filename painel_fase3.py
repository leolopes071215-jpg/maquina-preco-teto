# painel_fase3.py

import csv
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List

import streamlit as st


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v3.3 — Painel Mestre da Fase 3
# ------------------------------------------------------------
# Esta tela consolida clientes beta, suporte beta e retenção.
#
# Objetivo:
# - medir se a Fase 3 está saudável
# - decidir se vale vender mais, corrigir, pausar ou automatizar
# - proteger retenção antes de escalar aquisição
# - transformar clientes pagos em aprendizado de negócio
# ============================================================


CAMINHO_CLIENTES_BETA = Path("clientes_beta.csv")
CAMINHO_SUPORTE_BETA = Path("suporte_beta.csv")
CAMINHO_RETENCAO_BETA = Path("retencao_beta.csv")


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


def _mais_frequente(registros: List[Dict[str, str]], campo: str) -> str:
    contagem: Dict[str, int] = {}

    for registro in registros:
        valor = str(registro.get(campo, "")).strip()

        if valor == "":
            continue

        contagem[valor] = contagem.get(valor, 0) + 1

    if len(contagem) == 0:
        return "N/D"

    return max(contagem, key=contagem.get)


def _receita_real(clientes: List[Dict[str, str]]) -> float:
    total = 0.0

    for cliente in clientes:
        if cliente.get("status_pagamento") == "Pago":
            total += _safe_float(cliente.get("valor_pago"))

    return total


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


def _clientes_pagos(clientes: List[Dict[str, str]]) -> int:
    return _contar(clientes, "status_pagamento", "Pago")


def _clientes_ativos_pagos(clientes: List[Dict[str, str]]) -> int:
    status_ativos = ["Ativo", "Em onboarding", "Precisa de suporte", "Em risco"]

    return len(
        [
            cliente for cliente in clientes
            if cliente.get("status_pagamento") == "Pago"
            and cliente.get("status_cliente") in status_ativos
        ]
    )


def _clientes_em_risco_clientes(clientes: List[Dict[str, str]]) -> int:
    return len(
        [
            cliente for cliente in clientes
            if cliente.get("risco_cancelamento") in ["Alto", "Crítico"]
            or cliente.get("status_cliente") == "Em risco"
        ]
    )


def _satisfacao_media_clientes(clientes: List[Dict[str, str]]) -> float:
    return _media_campo(clientes, "satisfacao")


def _tickets_abertos(suporte: List[Dict[str, str]]) -> int:
    status_fechados = ["Resolvido", "Fechado", "Virou melhoria de produto"]

    return len(
        [
            ticket for ticket in suporte
            if ticket.get("status_atendimento") not in status_fechados
        ]
    )


def _tickets_resolvidos(suporte: List[Dict[str, str]]) -> int:
    return len(
        [
            ticket for ticket in suporte
            if ticket.get("status_atendimento") in ["Resolvido", "Fechado"]
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


def _tickets_risco_alto(suporte: List[Dict[str, str]]) -> int:
    return len(
        [
            ticket for ticket in suporte
            if ticket.get("risco_cancelamento") in ["Alto", "Crítico"]
        ]
    )


def _taxa_resolucao_suporte(suporte: List[Dict[str, str]]) -> float:
    if len(suporte) == 0:
        return 0.0

    return (_tickets_resolvidos(suporte) / len(suporte)) * 100


def _satisfacao_media_suporte(suporte: List[Dict[str, str]]) -> float:
    return _media_campo(suporte, "satisfacao_pos_atendimento")


def _tempo_medio_suporte(suporte: List[Dict[str, str]]) -> float:
    return _media_campo(suporte, "tempo_resposta_horas")


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


def _valor_percebido_alto(retencao: List[Dict[str, str]]) -> int:
    return _contar(retencao, "valor_percebido", "Alto") + _contar(
        retencao,
        "valor_percebido",
        "Muito alto",
    )


def _uso_relevante(retencao: List[Dict[str, str]]) -> int:
    return _contar(retencao, "uso_percebido", "Usa com frequência") + _contar(
        retencao,
        "uso_percebido",
        "Usa ocasionalmente",
    )


def _calcular_score_receita(clientes: List[Dict[str, str]], retencao: List[Dict[str, str]]) -> int:
    pagos = _clientes_pagos(clientes)
    ativos = _clientes_ativos_pagos(clientes)
    receita = _receita_real(clientes)
    mrr = _mrr_estimado(clientes)
    renovacoes = _renovacoes(retencao)
    cancelamentos = _cancelamentos(retencao)

    pontos = 0.0
    pontos += min(pagos * 16.0, 40)
    pontos += min(ativos * 10.0, 25)
    pontos += min(receita / 8, 20)
    pontos += min(mrr / 8, 20)
    pontos += min(renovacoes * 18.0, 30)
    pontos -= min(cancelamentos * 16.0, 30)

    return int(round(max(0, min(100, pontos))))


def _calcular_score_suporte(suporte: List[Dict[str, str]]) -> int:
    if len(suporte) == 0:
        return 50

    abertos = _tickets_abertos(suporte)
    resolvidos = _tickets_resolvidos(suporte)
    criticos = _tickets_criticos(suporte)
    risco_alto = _tickets_risco_alto(suporte)
    taxa_resolucao = _taxa_resolucao_suporte(suporte)
    satisfacao = _satisfacao_media_suporte(suporte)
    tempo_medio = _tempo_medio_suporte(suporte)

    pontos = 0.0
    pontos += min(resolvidos * 10.0, 30)
    pontos += taxa_resolucao * 0.30
    pontos += satisfacao * 4.0

    if tempo_medio > 0:
        if tempo_medio <= 2:
            pontos += 18
        elif tempo_medio <= 8:
            pontos += 12
        elif tempo_medio <= 24:
            pontos += 6
        else:
            pontos -= 10

    pontos -= min(abertos * 4.0, 20)
    pontos -= min(criticos * 12.0, 36)
    pontos -= min(risco_alto * 8.0, 24)

    return int(round(max(0, min(100, pontos))))


def _calcular_score_retencao(
    retencao: List[Dict[str, str]],
    clientes: List[Dict[str, str]],
    suporte: List[Dict[str, str]],
) -> int:
    if len(retencao) == 0 and _clientes_ativos_pagos(clientes) == 0:
        return 0

    clientes_ativos = _clientes_ativos_pagos(clientes)
    nps = _nps_medio(retencao)
    renovacoes = _renovacoes(retencao)
    cancelamentos = _cancelamentos(retencao)
    risco = _clientes_em_risco_retencao(retencao)
    valor_alto = _valor_percebido_alto(retencao)
    uso = _uso_relevante(retencao)
    tickets_criticos = _tickets_criticos(suporte)

    pontos = 0.0
    pontos += min(clientes_ativos * 12.0, 30)
    pontos += min(len(retencao) * 7.0, 25)
    pontos += nps * 3.0
    pontos += min(renovacoes * 18.0, 36)
    pontos += min(valor_alto * 10.0, 25)
    pontos += min(uso * 8.0, 20)

    pontos -= min(risco * 10.0, 30)
    pontos -= min(cancelamentos * 18.0, 36)
    pontos -= min(tickets_criticos * 8.0, 24)

    return int(round(max(0, min(100, pontos))))


def _calcular_score_entrega(
    clientes: List[Dict[str, str]],
    suporte: List[Dict[str, str]],
    retencao: List[Dict[str, str]],
) -> int:
    pagos = _clientes_pagos(clientes)
    ativos = _clientes_ativos_pagos(clientes)
    satisfacao_clientes = _satisfacao_media_clientes(clientes)
    satisfacao_suporte = _satisfacao_media_suporte(suporte)
    nps = _nps_medio(retencao)
    tickets_abertos = _tickets_abertos(suporte)
    tickets_criticos = _tickets_criticos(suporte)

    pontos = 0.0
    pontos += min(pagos * 8.0, 24)
    pontos += min(ativos * 8.0, 24)
    pontos += satisfacao_clientes * 3.0
    pontos += satisfacao_suporte * 2.0
    pontos += nps * 2.0

    pontos -= min(tickets_abertos * 4.0, 20)
    pontos -= min(tickets_criticos * 10.0, 30)

    return int(round(max(0, min(100, pontos))))


def _calcular_scores_fase3(
    clientes: List[Dict[str, str]],
    suporte: List[Dict[str, str]],
    retencao: List[Dict[str, str]],
) -> Dict[str, int]:
    score_receita = _calcular_score_receita(clientes, retencao)
    score_suporte = _calcular_score_suporte(suporte)
    score_retencao = _calcular_score_retencao(retencao, clientes, suporte)
    score_entrega = _calcular_score_entrega(clientes, suporte, retencao)

    score_geral = int(
        round(
            score_receita * 0.30
            + score_retencao * 0.30
            + score_suporte * 0.20
            + score_entrega * 0.20
        )
    )

    return {
        "geral": max(0, min(100, score_geral)),
        "receita": score_receita,
        "retencao": score_retencao,
        "suporte": score_suporte,
        "entrega": score_entrega,
    }


def _classificar_fase3(score: int) -> str:
    if score >= 85:
        return "Fase 3 forte"
    if score >= 70:
        return "Fase 3 saudável"
    if score >= 55:
        return "Fase 3 em validação"
    if score >= 40:
        return "Fase 3 frágil"
    return "Fase 3 ainda imatura"


def _decisao_estrategica(
    clientes: List[Dict[str, str]],
    suporte: List[Dict[str, str]],
    retencao: List[Dict[str, str]],
    scores: Dict[str, int],
) -> str:
    pagos = _clientes_pagos(clientes)
    ativos = _clientes_ativos_pagos(clientes)
    tickets_criticos = _tickets_criticos(suporte)
    tickets_abertos = _tickets_abertos(suporte)
    risco_retencao = _clientes_em_risco_retencao(retencao)
    risco_clientes = _clientes_em_risco_clientes(clientes)
    nps = _nps_medio(retencao)
    renovacoes = _renovacoes(retencao)
    cancelamentos = _cancelamentos(retencao)

    if pagos == 0:
        return "Buscar primeiros clientes beta pagos manualmente"

    if tickets_criticos > 0:
        return "Pausar novas vendas e resolver suporte crítico"

    if risco_retencao > 0 or risco_clientes > 0:
        return "Focar retenção antes de vender mais"

    if cancelamentos > 0 and renovacoes == 0:
        return "Investigar cancelamentos antes de escalar"

    if tickets_abertos > 3:
        return "Reduzir fila de suporte antes de aumentar aquisição"

    if scores["geral"] >= 85 and scores["retencao"] >= 75 and scores["suporte"] >= 70:
        return "Preparar automação leve e vender novo lote controlado"

    if scores["geral"] >= 70 and ativos >= 2 and nps >= 8:
        return "Vender pequeno lote adicional de clientes beta"

    if scores["retencao"] < 55 and len(retencao) > 0:
        return "Melhorar retenção, onboarding e valor percebido"

    if scores["suporte"] < 55 and len(suporte) > 0:
        return "Melhorar suporte antes de vender mais"

    if scores["receita"] < 45:
        return "Aumentar conversas de venda manual e validar preço"

    return "Continuar beta pago controlado com acompanhamento próximo"


def _gerar_resumo_areas(
    clientes: List[Dict[str, str]],
    suporte: List[Dict[str, str]],
    retencao: List[Dict[str, str]],
    scores: Dict[str, int],
) -> List[Dict[str, str]]:
    return [
        {
            "Área": "Receita",
            "Score": f"{scores['receita']}/100",
            "Indicador-chave": f"{_fmt_moeda(_receita_real(clientes))} recebidos",
            "Leitura": _ler_score(scores["receita"]),
        },
        {
            "Área": "MRR",
            "Score": "-",
            "Indicador-chave": f"{_fmt_moeda(_mrr_estimado(clientes))} estimados/mês",
            "Leitura": "Recorrência inicial",
        },
        {
            "Área": "Clientes",
            "Score": "-",
            "Indicador-chave": f"{_clientes_pagos(clientes)} pagos / {_clientes_ativos_pagos(clientes)} ativos",
            "Leitura": _ler_volume(_clientes_pagos(clientes), 1, 5),
        },
        {
            "Área": "Suporte",
            "Score": f"{scores['suporte']}/100",
            "Indicador-chave": f"{_tickets_abertos(suporte)} abertos / {_tickets_criticos(suporte)} críticos",
            "Leitura": _ler_score(scores["suporte"]),
        },
        {
            "Área": "Retenção",
            "Score": f"{scores['retencao']}/100",
            "Indicador-chave": f"NPS {_nps_medio(retencao):.1f}/10",
            "Leitura": _ler_score(scores["retencao"]),
        },
        {
            "Área": "Entrega",
            "Score": f"{scores['entrega']}/100",
            "Indicador-chave": f"Satisfação clientes {_satisfacao_media_clientes(clientes):.1f}/10",
            "Leitura": _ler_score(scores["entrega"]),
        },
        {
            "Área": "Renovação",
            "Score": "-",
            "Indicador-chave": f"{_renovacoes(retencao)} renovação(ões)",
            "Leitura": _ler_volume(_renovacoes(retencao), 1, 3),
        },
        {
            "Área": "Churn",
            "Score": "-",
            "Indicador-chave": f"{_cancelamentos(retencao)} cancelamento(s)/não renovação",
            "Leitura": "Atenção" if _cancelamentos(retencao) > 0 else "Sem perda registrada",
        },
    ]


def _ler_score(score: int) -> str:
    if score >= 85:
        return "Forte"
    if score >= 70:
        return "Saudável"
    if score >= 55:
        return "Em validação"
    if score >= 40:
        return "Frágil"
    return "Crítico"


def _ler_volume(valor: int, minimo: int, forte: int) -> str:
    if valor >= forte:
        return "Forte"
    if valor >= minimo:
        return "Inicial validado"
    if valor > 0:
        return "Muito inicial"
    return "Vazio"


def _gerar_alertas(
    clientes: List[Dict[str, str]],
    suporte: List[Dict[str, str]],
    retencao: List[Dict[str, str]],
    scores: Dict[str, int],
) -> List[str]:
    alertas = []

    if len(clientes) == 0:
        alertas.append("Nenhum cliente beta pago registrado. A Fase 3 ainda não começou comercialmente.")

    if _clientes_pagos(clientes) == 0 and len(clientes) > 0:
        alertas.append("Há clientes registrados, mas nenhum pagamento confirmado.")

    if _tickets_criticos(suporte) > 0:
        alertas.append("Existem tickets críticos. Pausar novas vendas pode ser necessário até resolver.")

    if _tickets_abertos(suporte) > 3:
        alertas.append("Há muitos tickets abertos. A fila de suporte pode prejudicar retenção.")

    if _clientes_em_risco_retencao(retencao) > 0:
        alertas.append("Existem clientes com risco de churn. Faça contato direto antes de vender mais.")

    if _clientes_em_risco_clientes(clientes) > 0:
        alertas.append("Clientes Beta possui usuários em risco alto/crítico de cancelamento.")

    if _nps_medio(retencao) < 7 and len(retencao) >= 2:
        alertas.append("NPS médio abaixo de 7. O produto ainda não deve acelerar aquisição.")

    if _cancelamentos(retencao) > 0:
        alertas.append("Há cancelamento ou não renovação. Investigue a causa antes de escalar.")

    if scores["suporte"] < 55 and len(suporte) > 0:
        alertas.append("Score de suporte baixo. Melhorar atendimento é prioridade.")

    if scores["retencao"] < 55 and len(retencao) > 0:
        alertas.append("Score de retenção baixo. A entrega ainda precisa provar valor sustentado.")

    if len(alertas) == 0:
        alertas.append("Nenhum alerta crítico. Continue vendendo pouco, acompanhando muito e melhorando com dados.")

    return alertas


def _gerar_acoes_recomendadas(
    clientes: List[Dict[str, str]],
    suporte: List[Dict[str, str]],
    retencao: List[Dict[str, str]],
    scores: Dict[str, int],
) -> List[Dict[str, str]]:
    acoes = []

    if _clientes_pagos(clientes) == 0:
        acoes.append(
            {
                "Prioridade": "Muito alta",
                "Ação": "Converter o primeiro cliente beta pago",
                "Motivo": "Sem pagamento confirmado, a Fase 3 ainda é hipótese comercial.",
            }
        )

    if _tickets_criticos(suporte) > 0:
        acoes.append(
            {
                "Prioridade": "Muito alta",
                "Ação": "Resolver tickets críticos",
                "Motivo": "Problemas que impedem uso destroem confiança e retenção.",
            }
        )

    if _clientes_em_risco_retencao(retencao) > 0:
        acoes.append(
            {
                "Prioridade": "Muito alta",
                "Ação": "Executar plano de retenção para clientes em risco",
                "Motivo": "Risco de churn precisa ser tratado antes de buscar novos clientes.",
            }
        )

    if _tickets_abertos(suporte) > 3:
        acoes.append(
            {
                "Prioridade": "Alta",
                "Ação": "Reduzir fila de suporte",
                "Motivo": "Suporte acumulado vira atraso, insatisfação e cancelamento.",
            }
        )

    if len(retencao) == 0 and _clientes_pagos(clientes) > 0:
        acoes.append(
            {
                "Prioridade": "Alta",
                "Ação": "Registrar acompanhamento de retenção",
                "Motivo": "Cliente pago precisa ser acompanhado depois da venda.",
            }
        )

    if _nps_medio(retencao) < 7 and len(retencao) >= 2:
        acoes.append(
            {
                "Prioridade": "Alta",
                "Ação": "Melhorar valor percebido",
                "Motivo": "NPS baixo indica que o cliente ainda não sentiu valor suficiente.",
            }
        )

    if scores["geral"] >= 70 and _tickets_criticos(suporte) == 0:
        acoes.append(
            {
                "Prioridade": "Média",
                "Ação": "Vender pequeno lote adicional",
                "Motivo": "Há sinal suficiente para testar mais clientes sem escalar agressivamente.",
            }
        )

    if scores["geral"] >= 85 and scores["retencao"] >= 75:
        acoes.append(
            {
                "Prioridade": "Média",
                "Ação": "Começar plano de automação leve",
                "Motivo": "Com receita, suporte e retenção saudáveis, já faz sentido preparar sistema profissional.",
            }
        )

    if len(acoes) == 0:
        acoes.append(
            {
                "Prioridade": "Média",
                "Ação": "Manter rotina semanal da Fase 3",
                "Motivo": "Continuar medindo clientes, suporte, retenção e receita.",
            }
        )

    return acoes


def _gerar_mapa_go_no_go(
    clientes: List[Dict[str, str]],
    suporte: List[Dict[str, str]],
    retencao: List[Dict[str, str]],
    scores: Dict[str, int],
) -> List[Dict[str, str]]:
    return [
        {
            "Critério": "Existe pelo menos 1 cliente pago",
            "Status": "OK" if _clientes_pagos(clientes) >= 1 else "Pendente",
            "Leitura": "Sem cliente pago, ainda não há validação comercial real.",
        },
        {
            "Critério": "Não há ticket crítico",
            "Status": "OK" if _tickets_criticos(suporte) == 0 else "Pendente",
            "Leitura": "Problemas críticos devem ser resolvidos antes de vender mais.",
        },
        {
            "Critério": "NPS médio ≥ 7",
            "Status": "OK" if _nps_medio(retencao) >= 7 or len(retencao) == 0 else "Pendente",
            "Leitura": "NPS baixo indica valor percebido insuficiente.",
        },
        {
            "Critério": "Score retenção ≥ 60",
            "Status": "OK" if scores["retencao"] >= 60 else "Pendente",
            "Leitura": "Retenção precisa sustentar a venda.",
        },
        {
            "Critério": "Score suporte ≥ 60",
            "Status": "OK" if scores["suporte"] >= 60 else "Pendente",
            "Leitura": "Suporte precisa estar minimamente controlado.",
        },
        {
            "Critério": "Sem churn relevante",
            "Status": "OK" if _cancelamentos(retencao) == 0 else "Pendente",
            "Leitura": "Cancelamento exige investigação antes de escalar.",
        },
        {
            "Critério": "Score geral ≥ 70",
            "Status": "OK" if scores["geral"] >= 70 else "Pendente",
            "Leitura": "Maturidade mínima para vender mais ou preparar automação.",
        },
    ]


def _gerar_rotina_semanal() -> List[Dict[str, str]]:
    return [
        {
            "Dia/ritual": "Segunda-feira",
            "Ação": "Revisar clientes pagos e acessos",
            "Objetivo": "Garantir que ninguém pagou e ficou sem entrega.",
        },
        {
            "Dia/ritual": "Terça-feira",
            "Ação": "Resolver tickets de suporte",
            "Objetivo": "Reduzir fricção antes que vire churn.",
        },
        {
            "Dia/ritual": "Quarta-feira",
            "Ação": "Fazer follow-up de retenção",
            "Objetivo": "Medir NPS, uso e valor percebido.",
        },
        {
            "Dia/ritual": "Quinta-feira",
            "Ação": "Transformar feedback em melhoria",
            "Objetivo": "Converter dor real em produto melhor.",
        },
        {
            "Dia/ritual": "Sexta-feira",
            "Ação": "Decidir vender, corrigir ou pausar",
            "Objetivo": "Manter crescimento controlado e racional.",
        },
    ]


def _gerar_markdown_fase3(
    clientes: List[Dict[str, str]],
    suporte: List[Dict[str, str]],
    retencao: List[Dict[str, str]],
    scores: Dict[str, int],
) -> str:
    classificacao = _classificar_fase3(scores["geral"])
    decisao = _decisao_estrategica(clientes, suporte, retencao, scores)

    linhas_resumo = "\n".join(
        [
            f"| {item['Área']} | {item['Score']} | {item['Indicador-chave']} | {item['Leitura']} |"
            for item in _gerar_resumo_areas(clientes, suporte, retencao, scores)
        ]
    )

    linhas_alertas = "\n".join(
        [
            f"- {alerta}"
            for alerta in _gerar_alertas(clientes, suporte, retencao, scores)
        ]
    )

    linhas_acoes = "\n".join(
        [
            f"| {acao['Prioridade']} | {acao['Ação']} | {acao['Motivo']} |"
            for acao in _gerar_acoes_recomendadas(clientes, suporte, retencao, scores)
        ]
    )

    linhas_go = "\n".join(
        [
            f"| {item['Critério']} | {item['Status']} | {item['Leitura']} |"
            for item in _gerar_mapa_go_no_go(clientes, suporte, retencao, scores)
        ]
    )

    return f"""# Painel Mestre da Fase 3 — Máquina de Preço-Teto

Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Diagnóstico geral

**Score geral da Fase 3:** {scores["geral"]}/100  
**Score de receita:** {scores["receita"]}/100  
**Score de retenção:** {scores["retencao"]}/100  
**Score de suporte:** {scores["suporte"]}/100  
**Score de entrega:** {scores["entrega"]}/100  

**Classificação:** {classificacao}  
**Decisão estratégica:** {decisao}

## Indicadores principais

- Clientes pagos: {_clientes_pagos(clientes)}
- Clientes ativos pagos: {_clientes_ativos_pagos(clientes)}
- Receita real: {_fmt_moeda(_receita_real(clientes))}
- MRR estimado: {_fmt_moeda(_mrr_estimado(clientes))}
- NPS médio: {_nps_medio(retencao):.1f}/10
- Tickets abertos: {_tickets_abertos(suporte)}
- Tickets críticos: {_tickets_criticos(suporte)}
- Renovações: {_renovacoes(retencao)}
- Cancelamentos/não renovação: {_cancelamentos(retencao)}

## Resumo por área

| Área | Score | Indicador-chave | Leitura |
|---|---:|---|---|
{linhas_resumo}

## Alertas estratégicos

{linhas_alertas}

## Próximas ações

| Prioridade | Ação | Motivo |
|---|---|---|
{linhas_acoes}

## Go/No-Go para vender mais ou automatizar

| Critério | Status | Leitura |
|---|---|---|
{linhas_go}

## Regra

A Fase 3 só deve escalar quando clientes pagantes usam, entendem valor, recebem suporte e demonstram retenção.
"""


def _injetar_css_painel_fase3() -> None:
    st.markdown(
        """
        <style>
            .pf3-hero {
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

            .pf3-eyebrow {
                color: #d6b56d;
                font-size: 0.78rem;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.35rem;
            }

            .pf3-title {
                color: #f4f7fb;
                font-size: 2.1rem;
                font-weight: 900;
                margin-bottom: 0.45rem;
                line-height: 1.14;
            }

            .pf3-subtitle {
                color: rgba(244, 247, 251, 0.76);
                font-size: 1rem;
                line-height: 1.62;
                max-width: 1080px;
            }

            .pf3-card {
                padding: 1.1rem 1.15rem;
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.035);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.18);
                height: 100%;
            }

            .pf3-card-label {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .pf3-card-value {
                color: #f4f7fb;
                font-size: 1.22rem;
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .pf3-card-note {
                color: rgba(244, 247, 251, 0.68);
                font-size: 0.87rem;
                line-height: 1.47;
            }

            .pf3-highlight {
                padding: 0.95rem 1rem;
                border-radius: 16px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.92rem;
                line-height: 1.55;
                margin-bottom: 0.7rem;
            }

            .pf3-disclaimer {
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
        <div class="pf3-card">
            <div class="pf3-card-label">{label}</div>
            <div class="pf3-card-value">{value}</div>
            <div class="pf3-card-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def renderizar_painel_fase3() -> None:
    """
    Renderiza o painel mestre da Fase 3.
    """
    _injetar_css_painel_fase3()

    clientes = _carregar_csv(CAMINHO_CLIENTES_BETA)
    suporte = _carregar_csv(CAMINHO_SUPORTE_BETA)
    retencao = _carregar_csv(CAMINHO_RETENCAO_BETA)

    scores = _calcular_scores_fase3(clientes, suporte, retencao)
    classificacao = _classificar_fase3(scores["geral"])
    decisao = _decisao_estrategica(clientes, suporte, retencao, scores)

    receita = _receita_real(clientes)
    mrr = _mrr_estimado(clientes)
    clientes_pagos = _clientes_pagos(clientes)
    clientes_ativos = _clientes_ativos_pagos(clientes)
    nps = _nps_medio(retencao)
    tickets_criticos = _tickets_criticos(suporte)
    churn = _cancelamentos(retencao)

    st.session_state["resultado_painel_fase3"] = {
        "score_geral_fase3": scores["geral"],
        "score_receita": scores["receita"],
        "score_retencao": scores["retencao"],
        "score_suporte": scores["suporte"],
        "score_entrega": scores["entrega"],
        "classificacao": classificacao,
        "decisao": decisao,
        "receita_real": receita,
        "mrr_estimado": mrr,
        "clientes_pagos": clientes_pagos,
        "clientes_ativos": clientes_ativos,
        "nps_medio": nps,
        "tickets_criticos": tickets_criticos,
        "cancelamentos": churn,
    }

    st.markdown(
        """
        <div class="pf3-hero">
            <div class="pf3-eyebrow">Fase 3.3 — Painel mestre</div>
            <div class="pf3-title">Painel Mestre da Fase 3</div>
            <div class="pf3-subtitle">
                Consolide clientes pagos, receita, suporte, retenção, NPS, churn e decisão estratégica.
                Use este painel para decidir se deve vender mais, corrigir, pausar ou preparar automação.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="pf3-highlight">
            Negócio excelente não escala só porque vendeu. Escala quando vende, entrega, suporta e retém.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Diagnóstico geral da Fase 3")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Score geral", f"{scores['geral']}/100")

    with col_2:
        st.metric("Classificação", classificacao)

    with col_3:
        st.metric("Receita real", _fmt_moeda(receita))

    with col_4:
        st.metric("MRR estimado", _fmt_moeda(mrr))

    st.progress(scores["geral"] / 100)

    if scores["geral"] >= 70:
        st.success(decisao)
    elif scores["geral"] >= 40:
        st.warning(decisao)
    else:
        st.error(decisao)

    st.divider()

    st.markdown("### Scores por dimensão")

    col_a, col_b, col_c, col_d = st.columns(4)

    with col_a:
        _card("Receita", f"{scores['receita']}/100", "Pagamento, MRR e renovações.")

    with col_b:
        _card("Retenção", f"{scores['retencao']}/100", "NPS, uso, valor percebido e churn.")

    with col_c:
        _card("Suporte", f"{scores['suporte']}/100", "Tickets, resolução e satisfação.")

    with col_d:
        _card("Entrega", f"{scores['entrega']}/100", "Satisfação, acesso e experiência.")

    st.divider()

    st.markdown("### Indicadores principais")

    col_i1, col_i2, col_i3, col_i4 = st.columns(4)

    with col_i1:
        _card("Clientes pagos", str(clientes_pagos), f"{clientes_ativos} ativos pagos.")

    with col_i2:
        _card("NPS médio", f"{nps:.1f}/10", "Medido na retenção.")

    with col_i3:
        _card("Tickets críticos", str(tickets_criticos), "Devem travar novas vendas se existirem.")

    with col_i4:
        _card("Churn", str(churn), "Cancelamento ou não renovação.")

    st.divider()

    st.markdown("### Resumo por área")

    st.dataframe(
        _gerar_resumo_areas(clientes, suporte, retencao, scores),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Alertas estratégicos")

    for alerta in _gerar_alertas(clientes, suporte, retencao, scores):
        st.markdown(f"- {alerta}")

    st.divider()

    st.markdown("### Próximas ações recomendadas")

    st.dataframe(
        _gerar_acoes_recomendadas(clientes, suporte, retencao, scores),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Go/No-Go para vender mais ou automatizar")

    st.dataframe(
        _gerar_mapa_go_no_go(clientes, suporte, retencao, scores),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Rotina semanal da Fase 3")

    st.dataframe(
        _gerar_rotina_semanal(),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Leitura executiva")

    st.info(
        f"""
        **Classificação atual:** {classificacao}  

        **Decisão estratégica:** {decisao}  

        **Leitura fria:** a Fase 3 só está saudável quando existe cliente pago,
        entrega funcionando, suporte controlado e sinal de retenção. Se uma dessas partes quebra,
        o correto é corrigir antes de escalar.
        """
    )

    st.divider()

    st.download_button(
        label="Baixar relatório mestre da Fase 3 (.md)",
        data=_gerar_markdown_fase3(clientes, suporte, retencao, scores),
        file_name="relatorio_painel_fase3.md",
        mime="text/markdown",
        key="download_painel_fase3_md",
    )

    st.markdown(
        """
        <div class="pf3-disclaimer">
            <strong>Regra da Fase 3:</strong> não automatize uma operação que ainda não provou retenção.
            Primeiro venda manualmente, entregue bem, resolva suporte e confirme que o cliente continuaria usando.
        </div>
        """,
        unsafe_allow_html=True,
    )