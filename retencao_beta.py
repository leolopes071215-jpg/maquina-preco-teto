# retencao_beta.py

import csv
import uuid
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List

import streamlit as st


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v3.2 — Retenção Beta, Renovação e Risco de Churn
# ------------------------------------------------------------
# Esta tela controla retenção dos primeiros clientes beta pagos.
#
# Objetivo:
# - acompanhar satisfação, uso percebido e valor percebido
# - controlar risco de churn/cancelamento
# - registrar follow-ups de renovação
# - transformar retenção em aprendizado de produto
# - decidir se já faz sentido vender para mais clientes
# ============================================================


CAMINHO_RETENCAO_BETA = Path("retencao_beta.csv")
CAMINHO_CLIENTES_BETA = Path("clientes_beta.csv")
CAMINHO_SUPORTE_BETA = Path("suporte_beta.csv")


CAMPOS_RETENCAO = [
    "id",
    "data_registro",
    "cliente",
    "contato_cliente",
    "plano",
    "status_cliente",
    "status_renovacao",
    "saude_cliente",
    "nps",
    "uso_percebido",
    "valor_percebido",
    "risco_churn",
    "motivo_risco",
    "principal_valor_percebido",
    "principal_frustracao",
    "feedback_positivo",
    "feedback_negativo",
    "acao_retencao",
    "oferta_renovacao",
    "status_followup",
    "proxima_acao",
    "responsavel",
    "prazo",
    "observacoes",
]


STATUS_CLIENTE = [
    "Ativo",
    "Em onboarding",
    "Precisa de suporte",
    "Em risco",
    "Renovou",
    "Não renovou",
    "Cancelado",
    "Pausado",
]


STATUS_RENOVACAO = [
    "Ainda não chegou",
    "Renovação próxima",
    "Renovação oferecida",
    "Renovou",
    "Não renovou",
    "Cancelou antes",
    "Indefinido",
]


SAUDE_CLIENTE = [
    "Excelente",
    "Boa",
    "Atenção",
    "Risco",
    "Crítica",
]


USO_PERCEBIDO = [
    "Usa com frequência",
    "Usa ocasionalmente",
    "Usou uma vez",
    "Ainda não usou",
    "Travou no uso",
    "Não sei",
]


VALOR_PERCEBIDO = [
    "Muito alto",
    "Alto",
    "Médio",
    "Baixo",
    "Muito baixo",
    "Não identificado",
]


RISCO_CHURN = [
    "Baixo",
    "Médio",
    "Alto",
    "Crítico",
]


STATUS_FOLLOWUP = [
    "Não iniciado",
    "Follow-up marcado",
    "Mensagem enviada",
    "Aguardando resposta",
    "Respondido",
    "Resolvido",
    "Sem resposta",
]


PROXIMAS_ACOES = [
    "Fazer follow-up de valor",
    "Guiar novo uso",
    "Resolver suporte pendente",
    "Enviar tutorial",
    "Pedir feedback sincero",
    "Oferecer renovação",
    "Melhorar entrega antes de renovar",
    "Registrar cancelamento",
    "Manter acompanhamento",
    "Aguardar",
]


ACOES_RETENCAO = [
    "Nenhuma ainda",
    "Explicar melhor o valor",
    "Guiar primeira análise",
    "Enviar exemplo de relatório",
    "Resolver problema técnico",
    "Melhorar onboarding",
    "Dar atenção individual",
    "Oferecer condição fundador",
    "Pedir feedback profundo",
    "Transformar feedback em melhoria",
]


def _garantir_arquivo_retencao() -> None:
    if CAMINHO_RETENCAO_BETA.exists():
        return

    with open(CAMINHO_RETENCAO_BETA, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_RETENCAO)
        escritor.writeheader()


def carregar_retencao_beta() -> List[Dict[str, str]]:
    _garantir_arquivo_retencao()

    with open(CAMINHO_RETENCAO_BETA, "r", newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        registros = []

        for linha in leitor:
            registro = {campo: linha.get(campo, "") for campo in CAMPOS_RETENCAO}
            registros.append(registro)

        return registros


def salvar_retencao_beta(registros: List[Dict[str, Any]]) -> None:
    with open(CAMINHO_RETENCAO_BETA, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_RETENCAO)
        escritor.writeheader()

        for registro in registros:
            linha = {campo: registro.get(campo, "") for campo in CAMPOS_RETENCAO}
            escritor.writerow(linha)


def limpar_retencao_beta() -> None:
    salvar_retencao_beta([])


def _carregar_csv(caminho: Path) -> List[Dict[str, str]]:
    if not caminho.exists():
        return []

    try:
        with open(caminho, "r", newline="", encoding="utf-8") as arquivo:
            leitor = csv.DictReader(arquivo)
            return [dict(linha) for linha in leitor]
    except Exception:
        return []


def _carregar_clientes_beta() -> List[Dict[str, str]]:
    return _carregar_csv(CAMINHO_CLIENTES_BETA)


def _carregar_suporte_beta() -> List[Dict[str, str]]:
    return _carregar_csv(CAMINHO_SUPORTE_BETA)


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


def adicionar_registro_retencao(
    cliente: str,
    contato_cliente: str,
    plano: str,
    status_cliente: str,
    status_renovacao: str,
    saude_cliente: str,
    nps: int,
    uso_percebido: str,
    valor_percebido: str,
    risco_churn: str,
    motivo_risco: str,
    principal_valor_percebido: str,
    principal_frustracao: str,
    feedback_positivo: str,
    feedback_negativo: str,
    acao_retencao: str,
    oferta_renovacao: str,
    status_followup: str,
    proxima_acao: str,
    responsavel: str,
    prazo: str,
    observacoes: str,
) -> None:
    registros = carregar_retencao_beta()

    novo_registro = {
        "id": str(uuid.uuid4())[:8],
        "data_registro": datetime.now().isoformat(timespec="minutes"),
        "cliente": cliente.strip(),
        "contato_cliente": contato_cliente.strip(),
        "plano": plano.strip(),
        "status_cliente": status_cliente,
        "status_renovacao": status_renovacao,
        "saude_cliente": saude_cliente,
        "nps": str(nps),
        "uso_percebido": uso_percebido,
        "valor_percebido": valor_percebido,
        "risco_churn": risco_churn,
        "motivo_risco": motivo_risco.strip(),
        "principal_valor_percebido": principal_valor_percebido.strip(),
        "principal_frustracao": principal_frustracao.strip(),
        "feedback_positivo": feedback_positivo.strip(),
        "feedback_negativo": feedback_negativo.strip(),
        "acao_retencao": acao_retencao,
        "oferta_renovacao": oferta_renovacao.strip(),
        "status_followup": status_followup,
        "proxima_acao": proxima_acao,
        "responsavel": responsavel.strip(),
        "prazo": prazo.strip(),
        "observacoes": observacoes.strip(),
    }

    registros.append(novo_registro)
    salvar_retencao_beta(registros)


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


def _receita_total_clientes(clientes: List[Dict[str, str]]) -> float:
    total = 0.0

    for cliente in clientes:
        if cliente.get("status_pagamento") == "Pago":
            total += _safe_float(cliente.get("valor_pago"))

    return total


def _mrr_estimado_clientes(clientes: List[Dict[str, str]]) -> float:
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


def _clientes_pagos_ativos(clientes: List[Dict[str, str]]) -> int:
    return len(
        [
            cliente for cliente in clientes
            if cliente.get("status_pagamento") == "Pago"
            and cliente.get("status_cliente") in ["Ativo", "Em onboarding", "Precisa de suporte", "Em risco"]
        ]
    )


def _tickets_abertos_suporte(suporte: List[Dict[str, str]]) -> int:
    status_fechados = ["Resolvido", "Fechado", "Virou melhoria de produto"]

    return len(
        [
            ticket for ticket in suporte
            if ticket.get("status_atendimento") not in status_fechados
        ]
    )


def _tickets_criticos_suporte(suporte: List[Dict[str, str]]) -> int:
    return len(
        [
            ticket for ticket in suporte
            if ticket.get("prioridade") == "Crítica"
            or ticket.get("risco_cancelamento") == "Crítico"
            or ticket.get("impacto_cliente") == "Impede o uso"
        ]
    )


def _clientes_em_risco_retencao(registros: List[Dict[str, str]]) -> int:
    return len(
        [
            registro for registro in registros
            if registro.get("risco_churn") in ["Alto", "Crítico"]
            or registro.get("saude_cliente") in ["Risco", "Crítica"]
            or registro.get("status_cliente") in ["Em risco", "Cancelado", "Não renovou"]
        ]
    )


def _renovacoes_confirmadas(registros: List[Dict[str, str]]) -> int:
    return _contar(registros, "status_renovacao", "Renovou") + _contar(
        registros,
        "status_cliente",
        "Renovou",
    )


def _cancelamentos(registros: List[Dict[str, str]]) -> int:
    return _contar(registros, "status_cliente", "Cancelado") + _contar(
        registros,
        "status_renovacao",
        "Não renovou",
    )


def _calcular_score_retencao(
    registros: List[Dict[str, str]],
    clientes: List[Dict[str, str]],
    suporte: List[Dict[str, str]],
) -> int:
    total_registros = len(registros)
    clientes_ativos = _clientes_pagos_ativos(clientes)
    receita = _receita_total_clientes(clientes)
    mrr = _mrr_estimado_clientes(clientes)

    if total_registros == 0 and clientes_ativos == 0:
        return 0

    nps_medio = _media_campo(registros, "nps")
    renovacoes = _renovacoes_confirmadas(registros)
    cancelamentos = _cancelamentos(registros)
    clientes_em_risco = _clientes_em_risco_retencao(registros)
    tickets_abertos = _tickets_abertos_suporte(suporte)
    tickets_criticos = _tickets_criticos_suporte(suporte)

    valor_alto = _contar(registros, "valor_percebido", "Alto") + _contar(
        registros,
        "valor_percebido",
        "Muito alto",
    )
    uso_frequente = _contar(registros, "uso_percebido", "Usa com frequência") + _contar(
        registros,
        "uso_percebido",
        "Usa ocasionalmente",
    )

    pontos = 0.0
    pontos += min(clientes_ativos * 10.0, 30)
    pontos += min(total_registros * 6.0, 24)
    pontos += min(renovacoes * 15.0, 30)
    pontos += min(valor_alto * 8.0, 24)
    pontos += min(uso_frequente * 7.0, 21)
    pontos += min(receita / 10, 15)
    pontos += min(mrr / 10, 12)
    pontos += nps_medio * 2.5

    pontos -= min(clientes_em_risco * 9.0, 27)
    pontos -= min(cancelamentos * 15.0, 30)
    pontos -= min(tickets_abertos * 3.0, 15)
    pontos -= min(tickets_criticos * 8.0, 24)

    return int(round(max(0, min(100, pontos))))


def _classificar_retencao(score: int, total_registros: int, clientes_ativos: int) -> str:
    if total_registros == 0 and clientes_ativos == 0:
        return "Sem retenção medida"

    if score >= 85:
        return "Retenção forte"
    if score >= 70:
        return "Retenção saudável"
    if score >= 55:
        return "Retenção em validação"
    if score >= 40:
        return "Retenção frágil"
    return "Risco alto de churn"


def _gerar_leitura_retencao(score: int, registros: List[Dict[str, str]], clientes: List[Dict[str, str]]) -> str:
    clientes_ativos = _clientes_pagos_ativos(clientes)

    if len(registros) == 0 and clientes_ativos == 0:
        return (
            "Ainda não há retenção medida. Primeiro registre clientes pagantes, depois acompanhe uso, valor percebido, "
            "NPS, risco de churn e intenção de renovação."
        )

    if score >= 85:
        return (
            "A retenção está forte para o estágio beta. O produto começa a demonstrar capacidade de entregar valor após a venda."
        )

    if score >= 70:
        return (
            "A retenção está saudável. Continue acompanhando renovação, suporte e uso real antes de escalar aquisição."
        )

    if score >= 55:
        return (
            "A retenção está em validação. Existe sinal positivo, mas ainda é cedo para acelerar vendas sem acompanhar clientes de perto."
        )

    if score >= 40:
        return (
            "A retenção está frágil. Antes de vender mais, reduza fricções, resolva suporte e aumente valor percebido."
        )

    return (
        "O risco de churn está alto. Vender mais agora pode aumentar cancelamento e prejudicar confiança."
    )


def _gerar_tabela_retencao(registros: List[Dict[str, str]]) -> List[Dict[str, str]]:
    ordem_risco = {
        "Crítico": 4,
        "Alto": 3,
        "Médio": 2,
        "Baixo": 1,
    }

    ordem_saude = {
        "Crítica": 5,
        "Risco": 4,
        "Atenção": 3,
        "Boa": 2,
        "Excelente": 1,
    }

    registros_ordenados = sorted(
        registros,
        key=lambda registro: (
            ordem_risco.get(registro.get("risco_churn", ""), 0),
            ordem_saude.get(registro.get("saude_cliente", ""), 0),
            -_safe_int(registro.get("nps")),
        ),
        reverse=True,
    )

    tabela = []

    for registro in registros_ordenados:
        tabela.append(
            {
                "Cliente": registro.get("cliente", ""),
                "Plano": registro.get("plano", ""),
                "Status cliente": registro.get("status_cliente", ""),
                "Renovação": registro.get("status_renovacao", ""),
                "Saúde": registro.get("saude_cliente", ""),
                "NPS": f"{registro.get('nps', '')}/10",
                "Uso": registro.get("uso_percebido", ""),
                "Valor percebido": registro.get("valor_percebido", ""),
                "Risco churn": registro.get("risco_churn", ""),
                "Follow-up": registro.get("status_followup", ""),
                "Próxima ação": registro.get("proxima_acao", ""),
                "Prazo": registro.get("prazo", ""),
            }
        )

    return tabela


def _gerar_tabela_metricas(
    registros: List[Dict[str, str]],
    clientes: List[Dict[str, str]],
    suporte: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    clientes_ativos = _clientes_pagos_ativos(clientes)
    receita = _receita_total_clientes(clientes)
    mrr = _mrr_estimado_clientes(clientes)
    nps_medio = _media_campo(registros, "nps")
    risco = _clientes_em_risco_retencao(registros)
    renovacoes = _renovacoes_confirmadas(registros)
    cancelamentos = _cancelamentos(registros)
    tickets_abertos = _tickets_abertos_suporte(suporte)
    tickets_criticos = _tickets_criticos_suporte(suporte)

    taxa_risco = (risco / len(registros)) * 100 if len(registros) > 0 else 0
    taxa_renovacao = (renovacoes / len(registros)) * 100 if len(registros) > 0 else 0
    taxa_cancelamento = (cancelamentos / len(registros)) * 100 if len(registros) > 0 else 0

    return [
        {
            "Métrica": "Clientes pagos ativos",
            "Valor": str(clientes_ativos),
            "Leitura": "Base pagante que ainda pode gerar retenção real.",
        },
        {
            "Métrica": "Registros de retenção",
            "Valor": str(len(registros)),
            "Leitura": "Quantidade de acompanhamentos feitos.",
        },
        {
            "Métrica": "Receita real registrada",
            "Valor": _fmt_moeda(receita),
            "Leitura": "Receita confirmada nos clientes beta.",
        },
        {
            "Métrica": "MRR estimado",
            "Valor": _fmt_moeda(mrr),
            "Leitura": "Receita recorrente mensal estimada.",
        },
        {
            "Métrica": "NPS médio",
            "Valor": f"{nps_medio:.1f}/10",
            "Leitura": "Disposição média de recomendar ou continuar.",
        },
        {
            "Métrica": "Clientes em risco",
            "Valor": str(risco),
            "Leitura": "Clientes com risco alto, crítico ou saúde ruim.",
        },
        {
            "Métrica": "Taxa de risco",
            "Valor": _fmt_percentual(taxa_risco),
            "Leitura": "Percentual dos acompanhamentos com risco relevante.",
        },
        {
            "Métrica": "Renovações confirmadas",
            "Valor": str(renovacoes),
            "Leitura": "Sinal mais forte de valor sustentado.",
        },
        {
            "Métrica": "Taxa de renovação",
            "Valor": _fmt_percentual(taxa_renovacao),
            "Leitura": "Proporção dos acompanhamentos com renovação.",
        },
        {
            "Métrica": "Cancelamentos/não renovou",
            "Valor": str(cancelamentos),
            "Leitura": "Sinal de falha de valor, entrega ou timing.",
        },
        {
            "Métrica": "Taxa de cancelamento",
            "Valor": _fmt_percentual(taxa_cancelamento),
            "Leitura": "Proporção dos acompanhamentos com perda.",
        },
        {
            "Métrica": "Tickets abertos",
            "Valor": str(tickets_abertos),
            "Leitura": "Suporte ainda pendente.",
        },
        {
            "Métrica": "Tickets críticos",
            "Valor": str(tickets_criticos),
            "Leitura": "Problemas que podem afetar retenção.",
        },
    ]


def _gerar_insights_retencao(
    registros: List[Dict[str, str]],
    clientes: List[Dict[str, str]],
    suporte: List[Dict[str, str]],
) -> List[str]:
    if len(registros) == 0:
        return [
            "Ainda não há registros de retenção.",
            "Depois do primeiro cliente beta pago, acompanhe uso, NPS, valor percebido e risco de churn.",
            "Retenção é a prova de que o produto entrega valor depois da venda.",
        ]

    insights = []

    clientes_ativos = _clientes_pagos_ativos(clientes)
    nps_medio = _media_campo(registros, "nps")
    risco = _clientes_em_risco_retencao(registros)
    renovacoes = _renovacoes_confirmadas(registros)
    cancelamentos = _cancelamentos(registros)
    valor_comum = _mais_frequente(registros, "valor_percebido")
    uso_comum = _mais_frequente(registros, "uso_percebido")
    frustracao = _mais_frequente(registros, "principal_frustracao")
    tickets_criticos = _tickets_criticos_suporte(suporte)

    insights.append(f"Clientes pagos ativos cadastrados: {clientes_ativos}.")
    insights.append(f"Registros de retenção: {len(registros)}.")
    insights.append(f"NPS médio: {nps_medio:.1f}/10.")
    insights.append(f"Clientes em risco de churn: {risco}.")
    insights.append(f"Renovações confirmadas: {renovacoes}.")
    insights.append(f"Cancelamentos ou não renovações: {cancelamentos}.")

    if valor_comum != "N/D":
        insights.append(f"Valor percebido mais comum: {valor_comum}.")

    if uso_comum != "N/D":
        insights.append(f"Uso percebido mais comum: {uso_comum}.")

    if frustracao != "N/D":
        insights.append(f"Frustração mais recorrente: {frustracao}.")

    if tickets_criticos > 0:
        insights.append(f"Existem {tickets_criticos} ticket(s) crítico(s) no suporte. Isso pode afetar retenção.")

    if nps_medio < 7:
        insights.append("NPS médio abaixo de 7. Não acelere aquisição antes de melhorar entrega e clareza.")

    if risco > 0:
        insights.append("Há clientes em risco. Priorize contato direto, suporte e entrega de valor antes de novas vendas.")

    insights.append("Retenção boa vem de três coisas: valor percebido, uso real e suporte rápido.")

    return insights


def _gerar_decisoes_retencao(
    registros: List[Dict[str, str]],
    clientes: List[Dict[str, str]],
    suporte: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    if len(registros) == 0:
        return [
            {
                "Decisão": "Começar acompanhamento de retenção",
                "Critério": "Nenhum registro de retenção.",
                "Ação": "Fazer follow-up com clientes beta pagos e medir NPS, uso e risco.",
                "Prioridade": "Muito alta",
            }
        ]

    decisoes = []

    nps_medio = _media_campo(registros, "nps")
    risco = _clientes_em_risco_retencao(registros)
    cancelamentos = _cancelamentos(registros)
    renovacoes = _renovacoes_confirmadas(registros)
    clientes_ativos = _clientes_pagos_ativos(clientes)
    tickets_abertos = _tickets_abertos_suporte(suporte)
    tickets_criticos = _tickets_criticos_suporte(suporte)

    valor_baixo = _contar(registros, "valor_percebido", "Baixo") + _contar(
        registros,
        "valor_percebido",
        "Muito baixo",
    )

    uso_ruim = _contar(registros, "uso_percebido", "Ainda não usou") + _contar(
        registros,
        "uso_percebido",
        "Travou no uso",
    )

    if tickets_criticos > 0:
        decisoes.append(
            {
                "Decisão": "Resolver suporte crítico antes de vender mais",
                "Critério": "Há tickets críticos no suporte.",
                "Ação": "Corrigir bloqueios de uso e reduzir risco de churn.",
                "Prioridade": "Muito alta",
            }
        )

    if risco > 0:
        decisoes.append(
            {
                "Decisão": "Executar plano de retenção dos clientes em risco",
                "Critério": "Há clientes com risco alto/crítico ou saúde ruim.",
                "Ação": "Fazer contato direto, entender motivo e aplicar ação de retenção.",
                "Prioridade": "Muito alta",
            }
        )

    if valor_baixo > 0:
        decisoes.append(
            {
                "Decisão": "Aumentar valor percebido",
                "Critério": "Há registros com valor percebido baixo.",
                "Ação": "Mostrar caso de uso, relatório exemplo e benefício prático.",
                "Prioridade": "Alta",
            }
        )

    if uso_ruim > 0:
        decisoes.append(
            {
                "Decisão": "Guiar uso real do produto",
                "Critério": "Há clientes que ainda não usaram ou travaram.",
                "Ação": "Conduzir primeira análise e simplificar onboarding.",
                "Prioridade": "Alta",
            }
        )

    if nps_medio < 7 and len(registros) >= 2:
        decisoes.append(
            {
                "Decisão": "Não escalar aquisição ainda",
                "Critério": "NPS médio abaixo de 7.",
                "Ação": "Melhorar produto, suporte e onboarding antes de vender mais.",
                "Prioridade": "Alta",
            }
        )

    if cancelamentos > 0:
        decisoes.append(
            {
                "Decisão": "Estudar causas de cancelamento",
                "Critério": "Há cancelamento ou não renovação.",
                "Ação": "Extrair motivo real e transformar em melhoria priorizada.",
                "Prioridade": "Alta",
            }
        )

    if renovacoes >= 2 and nps_medio >= 8 and tickets_criticos == 0:
        decisoes.append(
            {
                "Decisão": "Considerar venda para novos leads",
                "Critério": "Há renovação, NPS bom e sem suporte crítico.",
                "Ação": "Abrir novo pequeno lote de clientes beta pagos.",
                "Prioridade": "Média",
            }
        )

    if clientes_ativos > 0 and tickets_abertos == 0 and nps_medio >= 8:
        decisoes.append(
            {
                "Decisão": "Preparar automação leve",
                "Critério": "Clientes ativos, bom NPS e suporte sob controle.",
                "Ação": "Planejar checkout/acesso automatizado com cautela.",
                "Prioridade": "Baixa",
            }
        )

    if len(decisoes) == 0:
        decisoes.append(
            {
                "Decisão": "Manter acompanhamento semanal",
                "Critério": "Sem alerta crítico.",
                "Ação": "Continuar medindo uso, valor percebido, suporte e renovação.",
                "Prioridade": "Média",
            }
        )

    return decisoes


def _gerar_tabela_riscos(registros: List[Dict[str, str]]) -> List[Dict[str, str]]:
    tabela = []

    for registro in registros:
        risco = registro.get("risco_churn", "")
        saude = registro.get("saude_cliente", "")
        motivo = registro.get("motivo_risco", "").strip()

        if risco not in ["Alto", "Crítico"] and saude not in ["Risco", "Crítica"] and motivo == "":
            continue

        tabela.append(
            {
                "Cliente": registro.get("cliente", ""),
                "Saúde": saude,
                "Risco churn": risco,
                "Motivo": motivo,
                "Ação de retenção": registro.get("acao_retencao", ""),
                "Próxima ação": registro.get("proxima_acao", ""),
            }
        )

    return tabela


def _gerar_script_followup_retencao() -> str:
    return """Mensagem de follow-up de retenção:

Oi! Queria entender como está sua experiência com a Máquina de Preço-Teto depois dos primeiros usos.

Pode me responder de forma bem direta?

1. Você conseguiu usar a ferramenta em uma análise real?
2. O que mais gerou valor para você?
3. O que ficou confuso ou travado?
4. De 0 a 10, quanto você recomendaria ou continuaria usando?
5. O que precisaria melhorar para você renovar/continuar?

Seu feedback é essencial para eu melhorar a entrega antes de abrir para mais pessoas."""


def _gerar_script_cliente_em_risco() -> str:
    return """Mensagem para cliente em risco:

Oi! Percebi que talvez a ferramenta ainda não tenha te entregado o valor esperado.

Quero entender com sinceridade para melhorar:

1. O que te frustrou até agora?
2. Você travou em alguma parte?
3. O problema foi clareza, uso, relatório, acesso ou falta de tempo?
4. O que eu poderia ajustar para a ferramenta realmente valer a pena para você?

Se fizer sentido, posso te guiar em uma primeira análise para garantir que você consiga extrair valor real do produto."""


def _gerar_markdown_retencao(
    registros: List[Dict[str, str]],
    clientes: List[Dict[str, str]],
    suporte: List[Dict[str, str]],
) -> str:
    score = _calcular_score_retencao(registros, clientes, suporte)
    classificacao = _classificar_retencao(score, len(registros), _clientes_pagos_ativos(clientes))
    leitura = _gerar_leitura_retencao(score, registros, clientes)

    linhas_metricas = "\n".join(
        [
            f"| {item['Métrica']} | {item['Valor']} | {item['Leitura']} |"
            for item in _gerar_tabela_metricas(registros, clientes, suporte)
        ]
    )

    linhas_retencao = "\n".join(
        [
            f"| {item['Cliente']} | {item['Status cliente']} | {item['Renovação']} | {item['Saúde']} | {item['NPS']} | {item['Risco churn']} | {item['Próxima ação']} |"
            for item in _gerar_tabela_retencao(registros)
        ]
    )

    linhas_insights = "\n".join([f"- {item}" for item in _gerar_insights_retencao(registros, clientes, suporte)])

    linhas_decisoes = "\n".join(
        [
            f"| {item['Decisão']} | {item['Critério']} | {item['Ação']} | {item['Prioridade']} |"
            for item in _gerar_decisoes_retencao(registros, clientes, suporte)
        ]
    )

    return f"""# Retenção Beta — Máquina de Preço-Teto

Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Diagnóstico

**Score de retenção:** {score}/100  
**Classificação:** {classificacao}  

## Leitura

{leitura}

## Métricas

| Métrica | Valor | Leitura |
|---|---:|---|
{linhas_metricas}

## Registros de retenção

| Cliente | Status | Renovação | Saúde | NPS | Risco | Próxima ação |
|---|---|---|---|---:|---|---|
{linhas_retencao}

## Insights

{linhas_insights}

## Decisões recomendadas

| Decisão | Critério | Ação | Prioridade |
|---|---|---|---|
{linhas_decisoes}

## Regra

Retenção prova valor sustentado. Antes de escalar aquisição, prove que clientes pagantes usam, entendem, renovam e recebem suporte.
"""


def _injetar_css_retencao() -> None:
    st.markdown(
        """
        <style>
            .rb-hero {
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

            .rb-eyebrow {
                color: #d6b56d;
                font-size: 0.78rem;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.35rem;
            }

            .rb-title {
                color: #f4f7fb;
                font-size: 2.1rem;
                font-weight: 900;
                margin-bottom: 0.45rem;
                line-height: 1.14;
            }

            .rb-subtitle {
                color: rgba(244, 247, 251, 0.76);
                font-size: 1rem;
                line-height: 1.62;
                max-width: 1080px;
            }

            .rb-card {
                padding: 1.1rem 1.15rem;
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.035);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.18);
                height: 100%;
            }

            .rb-card-label {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .rb-card-value {
                color: #f4f7fb;
                font-size: 1.22rem;
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .rb-card-note {
                color: rgba(244, 247, 251, 0.68);
                font-size: 0.87rem;
                line-height: 1.47;
            }

            .rb-highlight {
                padding: 0.95rem 1rem;
                border-radius: 16px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.92rem;
                line-height: 1.55;
                margin-bottom: 0.7rem;
            }

            .rb-copy {
                padding: 1rem 1.05rem;
                border-radius: 18px;
                background: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(255, 255, 255, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.92rem;
                line-height: 1.58;
                white-space: pre-wrap;
                margin-bottom: 0.85rem;
            }

            .rb-disclaimer {
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
        <div class="rb-card">
            <div class="rb-card-label">{label}</div>
            <div class="rb-card-value">{value}</div>
            <div class="rb-card-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _copy_box(texto: str) -> None:
    st.markdown(
        f"""
        <div class="rb-copy">{texto}</div>
        """,
        unsafe_allow_html=True,
    )


def renderizar_retencao_beta() -> None:
    """
    Renderiza a central de retenção beta.
    """
    _injetar_css_retencao()

    registros = carregar_retencao_beta()
    clientes = _carregar_clientes_beta()
    suporte = _carregar_suporte_beta()

    clientes_ativos = _clientes_pagos_ativos(clientes)
    score = _calcular_score_retencao(registros, clientes, suporte)
    classificacao = _classificar_retencao(score, len(registros), clientes_ativos)
    leitura = _gerar_leitura_retencao(score, registros, clientes)

    receita = _receita_total_clientes(clientes)
    mrr = _mrr_estimado_clientes(clientes)
    nps_medio = _media_campo(registros, "nps")
    clientes_em_risco = _clientes_em_risco_retencao(registros)
    renovacoes = _renovacoes_confirmadas(registros)
    cancelamentos = _cancelamentos(registros)

    st.session_state["resultado_retencao_beta"] = {
        "score_retencao": score,
        "classificacao": classificacao,
        "clientes_ativos": clientes_ativos,
        "receita_total": receita,
        "mrr_estimado": mrr,
        "nps_medio": nps_medio,
        "clientes_em_risco": clientes_em_risco,
        "renovacoes": renovacoes,
        "cancelamentos": cancelamentos,
    }

    st.markdown(
        """
        <div class="rb-hero">
            <div class="rb-eyebrow">Fase 3.2 — Retenção beta</div>
            <div class="rb-title">Retenção Beta, Renovação e Risco de Churn</div>
            <div class="rb-subtitle">
                Acompanhe se os primeiros clientes pagantes estão usando, entendendo valor,
                renovando e permanecendo satisfeitos antes de acelerar novas vendas.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="rb-highlight">
            Venda prova interesse. Retenção prova valor. Antes de escalar aquisição,
            confirme se o cliente pagante usa, entende, renova e recomenda.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Diagnóstico de retenção")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Score retenção", f"{score}/100")

    with col_2:
        st.metric("Classificação", classificacao)

    with col_3:
        st.metric("NPS médio", f"{nps_medio:.1f}/10")

    with col_4:
        st.metric("MRR estimado", _fmt_moeda(mrr))

    st.progress(score / 100)

    if score >= 70:
        st.success(leitura)
    elif score >= 40:
        st.warning(leitura)
    else:
        st.error(leitura)

    st.divider()

    st.markdown("### Indicadores principais")

    col_a, col_b, col_c, col_d = st.columns(4)

    with col_a:
        _card("Clientes ativos pagos", str(clientes_ativos), "Base que precisa reter.")

    with col_b:
        _card("Renovações", str(renovacoes), "Sinal forte de valor sustentado.")

    with col_c:
        _card("Em risco", str(clientes_em_risco), "Prioridade de retenção.")

    with col_d:
        _card("Cancelamentos", str(cancelamentos), "Perda ou não renovação.")

    st.divider()

    st.markdown("### Métricas operacionais")

    st.dataframe(
        _gerar_tabela_metricas(registros, clientes, suporte),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Insights automáticos")

    for insight in _gerar_insights_retencao(registros, clientes, suporte):
        st.markdown(f"- {insight}")

    st.divider()

    st.markdown("### Decisões recomendadas")

    st.dataframe(
        _gerar_decisoes_retencao(registros, clientes, suporte),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Registrar acompanhamento de retenção")

    opcoes_clientes = [""] + [
        cliente.get("nome_cliente", "")
        for cliente in clientes
        if cliente.get("nome_cliente", "").strip() != ""
    ]

    dados_cliente = {}

    for cliente_item in clientes:
        nome = cliente_item.get("nome_cliente", "")
        if nome != "":
            dados_cliente[nome] = cliente_item

    with st.form("form_retencao_beta"):
        col_form_1, col_form_2 = st.columns(2)

        with col_form_1:
            cliente_selecionado = st.selectbox(
                "Selecionar cliente já cadastrado",
                opcoes_clientes,
                key="rb_cliente_selecionado",
            )

            cliente_base = dados_cliente.get(cliente_selecionado, {})

            cliente = st.text_input(
                "Cliente",
                value=cliente_selecionado,
                placeholder="Nome ou identificação do cliente",
                key="rb_cliente",
            )

            contato_cliente = st.text_input(
                "Contato do cliente",
                value=cliente_base.get("email_ou_contato", ""),
                placeholder="WhatsApp, e-mail ou outro contato",
                key="rb_contato",
            )

            plano = st.text_input(
                "Plano",
                value=cliente_base.get("plano", ""),
                placeholder="Plano vendido",
                key="rb_plano",
            )

            status_cliente = st.selectbox(
                "Status do cliente",
                STATUS_CLIENTE,
                key="rb_status_cliente",
            )

            status_renovacao = st.selectbox(
                "Status da renovação",
                STATUS_RENOVACAO,
                key="rb_status_renovacao",
            )

        with col_form_2:
            saude_cliente = st.selectbox(
                "Saúde do cliente",
                SAUDE_CLIENTE,
                key="rb_saude",
            )

            nps = st.slider(
                "NPS / chance de continuar ou recomendar",
                0,
                10,
                7,
                key="rb_nps",
            )

            uso_percebido = st.selectbox(
                "Uso percebido",
                USO_PERCEBIDO,
                key="rb_uso",
            )

            valor_percebido = st.selectbox(
                "Valor percebido",
                VALOR_PERCEBIDO,
                key="rb_valor_percebido",
            )

            risco_churn = st.selectbox(
                "Risco de churn",
                RISCO_CHURN,
                key="rb_risco_churn",
            )

        motivo_risco = st.text_area(
            "Motivo do risco",
            value="",
            height=80,
            placeholder="Por que esse cliente pode cancelar ou não renovar?",
            key="rb_motivo_risco",
        )

        principal_valor_percebido = st.text_area(
            "Principal valor percebido",
            value="",
            height=80,
            placeholder="O que gerou mais valor para esse cliente?",
            key="rb_valor",
        )

        principal_frustracao = st.text_area(
            "Principal frustração",
            value="",
            height=80,
            placeholder="O que irritou, confundiu ou travou o cliente?",
            key="rb_frustracao",
        )

        col_feedback_1, col_feedback_2 = st.columns(2)

        with col_feedback_1:
            feedback_positivo = st.text_area(
                "Feedback positivo",
                value="",
                height=90,
                key="rb_feedback_positivo",
            )

        with col_feedback_2:
            feedback_negativo = st.text_area(
                "Feedback negativo",
                value="",
                height=90,
                key="rb_feedback_negativo",
            )

        col_final_1, col_final_2 = st.columns(2)

        with col_final_1:
            acao_retencao = st.selectbox(
                "Ação de retenção",
                ACOES_RETENCAO,
                key="rb_acao_retencao",
            )

            status_followup = st.selectbox(
                "Status do follow-up",
                STATUS_FOLLOWUP,
                key="rb_status_followup",
            )

            proxima_acao = st.selectbox(
                "Próxima ação",
                PROXIMAS_ACOES,
                key="rb_proxima_acao",
            )

        with col_final_2:
            oferta_renovacao = st.text_input(
                "Oferta/condição de renovação",
                value="",
                placeholder="Ex: manter condição fundador por mais 1 mês...",
                key="rb_oferta_renovacao",
            )

            responsavel = st.text_input(
                "Responsável",
                value="Leo",
                key="rb_responsavel",
            )

            prazo = st.text_input(
                "Prazo",
                value="",
                placeholder="Ex: hoje, amanhã, esta semana...",
                key="rb_prazo",
            )

        observacoes = st.text_area(
            "Observações",
            value="",
            height=80,
            key="rb_observacoes",
        )

        enviar = st.form_submit_button("Salvar acompanhamento de retenção")

        if enviar:
            if cliente.strip() == "":
                st.error("Preencha o nome ou identificação do cliente.")
            else:
                adicionar_registro_retencao(
                    cliente=cliente,
                    contato_cliente=contato_cliente,
                    plano=plano,
                    status_cliente=status_cliente,
                    status_renovacao=status_renovacao,
                    saude_cliente=saude_cliente,
                    nps=nps,
                    uso_percebido=uso_percebido,
                    valor_percebido=valor_percebido,
                    risco_churn=risco_churn,
                    motivo_risco=motivo_risco,
                    principal_valor_percebido=principal_valor_percebido,
                    principal_frustracao=principal_frustracao,
                    feedback_positivo=feedback_positivo,
                    feedback_negativo=feedback_negativo,
                    acao_retencao=acao_retencao,
                    oferta_renovacao=oferta_renovacao,
                    status_followup=status_followup,
                    proxima_acao=proxima_acao,
                    responsavel=responsavel,
                    prazo=prazo,
                    observacoes=observacoes,
                )

                st.success("Acompanhamento de retenção registrado com sucesso.")
                st.rerun()

    st.divider()

    st.markdown("### Registros de retenção")

    registros = carregar_retencao_beta()

    if len(registros) == 0:
        st.info("Nenhum acompanhamento de retenção registrado ainda.")
    else:
        st.dataframe(
            _gerar_tabela_retencao(registros),
            use_container_width=True,
            hide_index=True,
        )

        riscos = _gerar_tabela_riscos(registros)

        if len(riscos) > 0:
            st.divider()
            st.markdown("### Mapa de risco de churn")
            st.dataframe(
                riscos,
                use_container_width=True,
                hide_index=True,
            )

    st.divider()

    st.markdown("### Mensagem de follow-up de retenção")

    _copy_box(_gerar_script_followup_retencao())

    st.divider()

    st.markdown("### Mensagem para cliente em risco")

    _copy_box(_gerar_script_cliente_em_risco())

    st.divider()

    if len(registros) > 0:
        col_download, col_limpar = st.columns(2)

        with col_download:
            with open(CAMINHO_RETENCAO_BETA, "rb") as arquivo:
                st.download_button(
                    label="Baixar retenção beta em CSV",
                    data=arquivo,
                    file_name="retencao_beta.csv",
                    mime="text/csv",
                    key="download_retencao_beta_csv",
                )

            st.download_button(
                label="Baixar relatório retenção beta (.md)",
                data=_gerar_markdown_retencao(registros, clientes, suporte),
                file_name="relatorio_retencao_beta.md",
                mime="text/markdown",
                key="download_retencao_beta_md",
            )

        with col_limpar:
            confirmar = st.checkbox(
                "Confirmar limpeza dos registros de retenção",
                value=False,
                key="rb_confirmar_limpeza",
            )

            if st.button("Limpar retenção beta", key="rb_limpar"):
                if confirmar:
                    limpar_retencao_beta()
                    st.success("Registros de retenção limpos com sucesso.")
                    st.rerun()
                else:
                    st.warning("Marque a confirmação antes de limpar.")

    st.markdown(
        """
        <div class="rb-disclaimer">
            <strong>Regra da retenção:</strong> não escale aquisição enquanto clientes pagantes
            não estiverem usando, entendendo valor, recebendo suporte e demonstrando chance real de renovar.
        </div>
        """,
        unsafe_allow_html=True,
    )