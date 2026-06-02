# clientes_beta.py

import csv
import uuid
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List

import streamlit as st


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v3.0 — Clientes Beta Pagos e Controle Manual de Acesso
# ------------------------------------------------------------
# Esta tela controla os primeiros clientes beta pagos.
#
# Objetivo:
# - registrar clientes pagantes
# - controlar pagamento, acesso, onboarding e suporte
# - medir receita real e recorrente
# - identificar risco de cancelamento
# - evitar vender sem conseguir entregar suporte mínimo
# ============================================================


CAMINHO_CLIENTES_BETA = Path("clientes_beta.csv")


CAMPOS_CLIENTES = [
    "id",
    "data_registro",
    "nome_cliente",
    "email_ou_contato",
    "perfil",
    "canal_origem",
    "plano",
    "valor_pago",
    "periodicidade",
    "forma_pagamento",
    "status_pagamento",
    "status_acesso",
    "status_onboarding",
    "data_inicio",
    "data_renovacao",
    "satisfacao",
    "risco_cancelamento",
    "principal_motivo_compra",
    "principal_duvida",
    "suporte_pendente",
    "proxima_acao",
    "status_cliente",
    "observacoes",
]


PERFIS_CLIENTE = [
    "Investidor iniciante",
    "Investidor intermediário",
    "Investidor avançado",
    "Estudante",
    "Criador de conteúdo financeiro",
    "Usuário fundador",
    "Pessoa próxima",
    "Outro",
]


CANAIS_ORIGEM = [
    "WhatsApp",
    "Instagram",
    "LinkedIn",
    "E-mail",
    "Indicação",
    "CRM Beta",
    "Pré-venda Beta",
    "Oferta Paga",
    "Outro",
]


PLANOS = [
    "Beta pago mensal",
    "Beta pago trimestral",
    "Acesso fundador",
    "Pagamento único beta",
    "Plano básico",
    "Plano premium",
    "Mentoria + ferramenta",
    "Outro",
]


PERIODICIDADES = [
    "Mensal",
    "Trimestral",
    "Anual",
    "Pagamento único",
    "Sem recorrência definida",
]


FORMAS_PAGAMENTO = [
    "Pix",
    "Transferência",
    "Link de pagamento",
    "Cartão",
    "Dinheiro",
    "Ainda não pago",
    "Outro",
]


STATUS_PAGAMENTO = [
    "Pago",
    "Pendente",
    "Aguardando confirmação",
    "Atrasado",
    "Cancelado",
    "Reembolsado",
]


STATUS_ACESSO = [
    "Não liberado",
    "Liberado",
    "Com problema de acesso",
    "Pausado",
    "Removido",
]


STATUS_ONBOARDING = [
    "Não iniciado",
    "Mensagem inicial enviada",
    "Primeiro acesso feito",
    "Onboarding completo",
    "Travado",
]


RISCO_CANCELAMENTO = [
    "Baixo",
    "Médio",
    "Alto",
    "Crítico",
]


STATUS_CLIENTE = [
    "Ativo",
    "Em onboarding",
    "Precisa de suporte",
    "Em risco",
    "Cancelado",
    "Reembolsado",
    "Pausado",
]


PROXIMAS_ACOES = [
    "Liberar acesso",
    "Confirmar pagamento",
    "Enviar mensagem de boas-vindas",
    "Guiar primeiro uso",
    "Pedir feedback inicial",
    "Resolver suporte",
    "Fazer follow-up de satisfação",
    "Oferecer renovação",
    "Registrar cancelamento",
    "Aguardar",
]


def _garantir_arquivo_clientes() -> None:
    if CAMINHO_CLIENTES_BETA.exists():
        return

    with open(CAMINHO_CLIENTES_BETA, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_CLIENTES)
        escritor.writeheader()


def carregar_clientes_beta() -> List[Dict[str, str]]:
    _garantir_arquivo_clientes()

    with open(CAMINHO_CLIENTES_BETA, "r", newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        registros = []

        for linha in leitor:
            registro = {campo: linha.get(campo, "") for campo in CAMPOS_CLIENTES}
            registros.append(registro)

        return registros


def salvar_clientes_beta(registros: List[Dict[str, Any]]) -> None:
    with open(CAMINHO_CLIENTES_BETA, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_CLIENTES)
        escritor.writeheader()

        for registro in registros:
            linha = {campo: registro.get(campo, "") for campo in CAMPOS_CLIENTES}
            escritor.writerow(linha)


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


def adicionar_cliente_beta(
    nome_cliente: str,
    email_ou_contato: str,
    perfil: str,
    canal_origem: str,
    plano: str,
    valor_pago: float,
    periodicidade: str,
    forma_pagamento: str,
    status_pagamento: str,
    status_acesso: str,
    status_onboarding: str,
    data_inicio: str,
    data_renovacao: str,
    satisfacao: int,
    risco_cancelamento: str,
    principal_motivo_compra: str,
    principal_duvida: str,
    suporte_pendente: str,
    proxima_acao: str,
    status_cliente: str,
    observacoes: str,
) -> None:
    registros = carregar_clientes_beta()

    novo_registro = {
        "id": str(uuid.uuid4())[:8],
        "data_registro": datetime.now().isoformat(timespec="minutes"),
        "nome_cliente": nome_cliente.strip(),
        "email_ou_contato": email_ou_contato.strip(),
        "perfil": perfil,
        "canal_origem": canal_origem,
        "plano": plano,
        "valor_pago": str(valor_pago),
        "periodicidade": periodicidade,
        "forma_pagamento": forma_pagamento,
        "status_pagamento": status_pagamento,
        "status_acesso": status_acesso,
        "status_onboarding": status_onboarding,
        "data_inicio": data_inicio.strip(),
        "data_renovacao": data_renovacao.strip(),
        "satisfacao": str(satisfacao),
        "risco_cancelamento": risco_cancelamento,
        "principal_motivo_compra": principal_motivo_compra.strip(),
        "principal_duvida": principal_duvida.strip(),
        "suporte_pendente": suporte_pendente.strip(),
        "proxima_acao": proxima_acao,
        "status_cliente": status_cliente,
        "observacoes": observacoes.strip(),
    }

    registros.append(novo_registro)
    salvar_clientes_beta(registros)


def limpar_clientes_beta() -> None:
    salvar_clientes_beta([])


def _contar(registros: List[Dict[str, str]], campo: str, valor: str) -> int:
    return len([registro for registro in registros if registro.get(campo) == valor])


def _media_campo(registros: List[Dict[str, str]], campo: str) -> float:
    valores = []

    for registro in registros:
        valor = _safe_float(registro.get(campo))

        if valor > 0:
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


def _receita_total(registros: List[Dict[str, str]]) -> float:
    return sum(
        _safe_float(registro.get("valor_pago"))
        for registro in registros
        if registro.get("status_pagamento") == "Pago"
    )


def _mrr_estimado(registros: List[Dict[str, str]]) -> float:
    total = 0.0

    for registro in registros:
        if registro.get("status_pagamento") != "Pago":
            continue

        valor = _safe_float(registro.get("valor_pago"))
        periodicidade = registro.get("periodicidade", "")

        if periodicidade == "Mensal":
            total += valor
        elif periodicidade == "Trimestral":
            total += valor / 3
        elif periodicidade == "Anual":
            total += valor / 12

    return total


def _clientes_ativos(registros: List[Dict[str, str]]) -> int:
    return len(
        [
            registro for registro in registros
            if registro.get("status_cliente") in ["Ativo", "Em onboarding", "Precisa de suporte", "Em risco"]
            and registro.get("status_pagamento") == "Pago"
        ]
    )


def _clientes_em_risco(registros: List[Dict[str, str]]) -> int:
    return len(
        [
            registro for registro in registros
            if registro.get("risco_cancelamento") in ["Alto", "Crítico"]
            or registro.get("status_cliente") == "Em risco"
        ]
    )


def _calcular_score_clientes(registros: List[Dict[str, str]]) -> int:
    total = len(registros)

    if total == 0:
        return 0

    pagos = _contar(registros, "status_pagamento", "Pago")
    ativos = _clientes_ativos(registros)
    onboarding_completo = _contar(registros, "status_onboarding", "Onboarding completo")
    acesso_liberado = _contar(registros, "status_acesso", "Liberado")
    em_risco = _clientes_em_risco(registros)
    satisfacao_media = _media_campo(registros, "satisfacao")
    receita = _receita_total(registros)
    mrr = _mrr_estimado(registros)

    pontos = 0.0
    pontos += min(pagos * 12.0, 36)
    pontos += min(ativos * 8.0, 24)
    pontos += min(onboarding_completo * 6.0, 18)
    pontos += min(acesso_liberado * 5.0, 15)
    pontos += satisfacao_media * 3.0
    pontos += min(receita / 10, 15)
    pontos += min(mrr / 10, 10)
    pontos -= min(em_risco * 8.0, 24)

    return int(round(max(0, min(100, pontos))))


def _classificar_clientes(score: int, total: int) -> str:
    if total == 0:
        return "Sem clientes beta pagos"

    if score >= 85:
        return "Base beta paga forte"
    if score >= 70:
        return "Boa tração inicial"
    if score >= 55:
        return "Tração inicial em validação"
    if score >= 40:
        return "Base ainda frágil"
    return "Entrega paga ainda não validada"


def _gerar_leitura_clientes(score: int, registros: List[Dict[str, str]]) -> str:
    if len(registros) == 0:
        return (
            "Ainda não há clientes beta pagos registrados. O próximo passo é converter poucos leads "
            "manualmente e acompanhar pagamento, acesso, onboarding e satisfação."
        )

    if score >= 85:
        return (
            "A base beta paga está forte para o estágio atual. O foco deve ser manter suporte, "
            "medir retenção e decidir se vale automatizar pagamento e acesso."
        )

    if score >= 70:
        return (
            "Há boa tração inicial. Continue vendendo manualmente para poucos usuários e observe "
            "se a entrega sustenta satisfação e renovação."
        )

    if score >= 55:
        return (
            "Existe tração inicial, mas ainda precisa validação. Priorize onboarding, suporte e "
            "redução do risco de cancelamento antes de escalar."
        )

    if score >= 40:
        return (
            "A base ainda é frágil. Talvez existam pagamentos, mas o processo de entrega, acesso "
            "ou satisfação ainda não está sólido."
        )

    return (
        "A entrega paga ainda não foi validada. Foque em poucos clientes, suporte intenso e aprendizado."
    )


def _gerar_tabela_clientes(registros: List[Dict[str, str]]) -> List[Dict[str, str]]:
    ordem_risco = {
        "Crítico": 4,
        "Alto": 3,
        "Médio": 2,
        "Baixo": 1,
    }

    registros_ordenados = sorted(
        registros,
        key=lambda registro: (
            ordem_risco.get(registro.get("risco_cancelamento", ""), 0),
            _safe_float(registro.get("valor_pago")),
        ),
        reverse=True,
    )

    tabela = []

    for registro in registros_ordenados:
        tabela.append(
            {
                "Cliente": registro.get("nome_cliente", ""),
                "Contato": registro.get("email_ou_contato", ""),
                "Plano": registro.get("plano", ""),
                "Valor": _fmt_moeda(_safe_float(registro.get("valor_pago"))),
                "Periodicidade": registro.get("periodicidade", ""),
                "Pagamento": registro.get("status_pagamento", ""),
                "Acesso": registro.get("status_acesso", ""),
                "Onboarding": registro.get("status_onboarding", ""),
                "Satisfação": f"{registro.get('satisfacao', '')}/10",
                "Risco": registro.get("risco_cancelamento", ""),
                "Status": registro.get("status_cliente", ""),
                "Próxima ação": registro.get("proxima_acao", ""),
            }
        )

    return tabela


def _gerar_tabela_suporte(registros: List[Dict[str, str]]) -> List[Dict[str, str]]:
    tabela = []

    for registro in registros:
        suporte = registro.get("suporte_pendente", "").strip()
        duvida = registro.get("principal_duvida", "").strip()

        if suporte == "" and duvida == "":
            continue

        tabela.append(
            {
                "Cliente": registro.get("nome_cliente", ""),
                "Status": registro.get("status_cliente", ""),
                "Suporte pendente": suporte,
                "Principal dúvida": duvida,
                "Risco": registro.get("risco_cancelamento", ""),
                "Ação sugerida": _acao_suporte(registro),
            }
        )

    return tabela


def _acao_suporte(registro: Dict[str, str]) -> str:
    risco = registro.get("risco_cancelamento", "")
    acesso = registro.get("status_acesso", "")
    onboarding = registro.get("status_onboarding", "")

    if acesso == "Com problema de acesso":
        return "Resolver acesso imediatamente."

    if risco in ["Alto", "Crítico"]:
        return "Fazer contato direto e reduzir risco de cancelamento."

    if onboarding in ["Não iniciado", "Travado"]:
        return "Guiar primeiro uso e destravar onboarding."

    return "Responder dúvida e registrar aprendizado."


def _gerar_tabela_metricas(registros: List[Dict[str, str]]) -> List[Dict[str, str]]:
    total = len(registros)
    pagos = _contar(registros, "status_pagamento", "Pago")
    pendentes = _contar(registros, "status_pagamento", "Pendente") + _contar(
        registros,
        "status_pagamento",
        "Aguardando confirmação",
    )
    ativos = _clientes_ativos(registros)
    cancelados = _contar(registros, "status_cliente", "Cancelado")
    risco = _clientes_em_risco(registros)

    taxa_pagamento = (pagos / total) * 100 if total > 0 else 0
    taxa_cancelamento = (cancelados / total) * 100 if total > 0 else 0
    taxa_risco = (risco / total) * 100 if total > 0 else 0

    return [
        {
            "Métrica": "Clientes registrados",
            "Valor": str(total),
            "Leitura": "Tamanho da base beta paga cadastrada.",
        },
        {
            "Métrica": "Clientes pagos",
            "Valor": str(pagos),
            "Leitura": "Usuários com pagamento confirmado.",
        },
        {
            "Métrica": "Clientes ativos pagos",
            "Valor": str(ativos),
            "Leitura": "Base ativa com potencial de aprendizado real.",
        },
        {
            "Métrica": "Pagamentos pendentes",
            "Valor": str(pendentes),
            "Leitura": "Precisam de confirmação ou cobrança manual.",
        },
        {
            "Métrica": "Receita real recebida",
            "Valor": _fmt_moeda(_receita_total(registros)),
            "Leitura": "Dinheiro efetivamente confirmado.",
        },
        {
            "Métrica": "MRR estimado",
            "Valor": _fmt_moeda(_mrr_estimado(registros)),
            "Leitura": "Receita recorrente mensal estimada.",
        },
        {
            "Métrica": "Satisfação média",
            "Valor": f"{_media_campo(registros, 'satisfacao'):.1f}/10",
            "Leitura": "Percepção inicial de valor dos clientes.",
        },
        {
            "Métrica": "Taxa de pagamento",
            "Valor": _fmt_percentual(taxa_pagamento),
            "Leitura": "Proporção da base com pagamento confirmado.",
        },
        {
            "Métrica": "Taxa de risco",
            "Valor": _fmt_percentual(taxa_risco),
            "Leitura": "Clientes com risco alto ou crítico.",
        },
        {
            "Métrica": "Taxa de cancelamento",
            "Valor": _fmt_percentual(taxa_cancelamento),
            "Leitura": "Cancelamentos na base beta paga.",
        },
    ]


def _gerar_insights_clientes(registros: List[Dict[str, str]]) -> List[str]:
    if len(registros) == 0:
        return [
            "Ainda não há clientes beta pagos registrados.",
            "O próximo passo é vender manualmente para poucos leads qualificados.",
            "Não automatize pagamento antes de provar que consegue vender e entregar manualmente.",
        ]

    insights = []

    total = len(registros)
    pagos = _contar(registros, "status_pagamento", "Pago")
    ativos = _clientes_ativos(registros)
    em_risco = _clientes_em_risco(registros)
    receita = _receita_total(registros)
    mrr = _mrr_estimado(registros)
    satisfacao = _media_campo(registros, "satisfacao")
    plano_comum = _mais_frequente(registros, "plano")
    canal_comum = _mais_frequente(registros, "canal_origem")
    duvida_comum = _mais_frequente(registros, "principal_duvida")

    insights.append(f"Você tem {total} cliente(s) beta registrados.")
    insights.append(f"{pagos} cliente(s) têm pagamento confirmado.")
    insights.append(f"{ativos} cliente(s) estão ativos com pagamento confirmado.")
    insights.append(f"Receita real recebida: {_fmt_moeda(receita)}.")
    insights.append(f"MRR estimado: {_fmt_moeda(mrr)}.")
    insights.append(f"Satisfação média: {satisfacao:.1f}/10.")

    if em_risco > 0:
        insights.append(f"Existem {em_risco} cliente(s) em risco alto/crítico. Priorize suporte e follow-up.")

    if plano_comum != "N/D":
        insights.append(f"Plano mais comum: {plano_comum}.")

    if canal_comum != "N/D":
        insights.append(f"Canal de origem mais comum: {canal_comum}.")

    if duvida_comum != "N/D":
        insights.append(f"Dúvida mais recorrente: {duvida_comum}.")

    if satisfacao < 7 and total > 0:
        insights.append("A satisfação média ainda está abaixo do ideal. Não escale vendas antes de melhorar entrega.")

    insights.append("Na Fase 3, vender é só metade do teste. A outra metade é entregar, suportar e reter.")

    return insights


def _gerar_decisoes_clientes(registros: List[Dict[str, str]]) -> List[Dict[str, str]]:
    if len(registros) == 0:
        return [
            {
                "Decisão": "Buscar primeiros clientes beta pagos",
                "Critério": "Nenhum cliente registrado.",
                "Ação": "Selecionar 3 a 5 leads quentes e testar venda manual.",
                "Prioridade": "Muito alta",
            }
        ]

    decisoes = []

    pagos = _contar(registros, "status_pagamento", "Pago")
    pendentes = _contar(registros, "status_pagamento", "Pendente") + _contar(
        registros,
        "status_pagamento",
        "Aguardando confirmação",
    )
    problemas_acesso = _contar(registros, "status_acesso", "Com problema de acesso")
    sem_acesso = _contar(registros, "status_acesso", "Não liberado")
    onboarding_travado = _contar(registros, "status_onboarding", "Travado")
    em_risco = _clientes_em_risco(registros)
    satisfacao = _media_campo(registros, "satisfacao")
    mrr = _mrr_estimado(registros)

    if sem_acesso > 0:
        decisoes.append(
            {
                "Decisão": "Liberar acessos pendentes",
                "Critério": "Há clientes sem acesso.",
                "Ação": "Liberar acesso antes de vender para novos usuários.",
                "Prioridade": "Muito alta",
            }
        )

    if problemas_acesso > 0:
        decisoes.append(
            {
                "Decisão": "Corrigir problemas de acesso",
                "Critério": "Há clientes com problema de acesso.",
                "Ação": "Resolver imediatamente para proteger confiança.",
                "Prioridade": "Muito alta",
            }
        )

    if pendentes > 0:
        decisoes.append(
            {
                "Decisão": "Confirmar pagamentos pendentes",
                "Critério": "Há pagamento pendente ou aguardando confirmação.",
                "Ação": "Fazer follow-up de confirmação sem pressionar.",
                "Prioridade": "Alta",
            }
        )

    if onboarding_travado > 0:
        decisoes.append(
            {
                "Decisão": "Destravar onboarding",
                "Critério": "Há cliente travado no primeiro uso.",
                "Ação": "Guiar o usuário na primeira análise.",
                "Prioridade": "Alta",
            }
        )

    if em_risco > 0:
        decisoes.append(
            {
                "Decisão": "Reduzir risco de cancelamento",
                "Critério": "Há clientes com risco alto ou crítico.",
                "Ação": "Fazer contato direto, entender dor e resolver suporte.",
                "Prioridade": "Alta",
            }
        )

    if pagos >= 3 and satisfacao >= 8 and mrr > 0:
        decisoes.append(
            {
                "Decisão": "Considerar automação leve",
                "Critério": "Já há clientes pagos, satisfação alta e MRR inicial.",
                "Ação": "Começar a planejar checkout/acesso automatizado, sem pressa.",
                "Prioridade": "Média",
            }
        )

    if len(decisoes) == 0:
        decisoes.append(
            {
                "Decisão": "Continuar beta pago controlado",
                "Critério": "Sem alerta crítico.",
                "Ação": "Vender pouco, acompanhar muito e medir retenção.",
                "Prioridade": "Média",
            }
        )

    return decisoes


def _gerar_script_boas_vindas() -> str:
    return """Mensagem de boas-vindas ao cliente beta:

Olá! Seu acesso à Máquina de Preço-Teto foi registrado.

Antes de começar, um ponto importante:
a ferramenta é educacional e não faz recomendação de compra, venda ou manutenção de investimentos.

O objetivo é te ajudar a organizar uma análise com mais método:
- premissas;
- valuation;
- preço-teto;
- margem de segurança;
- tese;
- riscos;
- checklist;
- relatório.

Primeiro passo:
acesse o app, escolha uma empresa ou análise manual e tente gerar seu primeiro relatório.

Depois me envie:
1. o que ficou claro;
2. onde você travou;
3. o que mais te ajudaria na próxima versão.

Como essa é uma versão beta, seu feedback vai influenciar diretamente a evolução do produto."""


def _gerar_script_followup_satisfacao() -> str:
    return """Mensagem de follow-up de satisfação:

Oi! Queria saber como foi sua primeira experiência usando a Máquina de Preço-Teto.

Pode me responder de forma direta?

1. Você conseguiu usar sem travar?
2. O relatório gerado foi útil?
3. O que ficou confuso?
4. De 0 a 10, quanto valor você sentiu na ferramenta?
5. O que precisaria melhorar para você continuar usando?

Feedback sincero é o mais importante agora."""


def _gerar_markdown_clientes(registros: List[Dict[str, str]]) -> str:
    score = _calcular_score_clientes(registros)
    classificacao = _classificar_clientes(score, len(registros))
    leitura = _gerar_leitura_clientes(score, registros)

    linhas_metricas = "\n".join(
        [
            f"| {item['Métrica']} | {item['Valor']} | {item['Leitura']} |"
            for item in _gerar_tabela_metricas(registros)
        ]
    )

    linhas_clientes = "\n".join(
        [
            f"| {item['Cliente']} | {item['Plano']} | {item['Valor']} | {item['Pagamento']} | {item['Acesso']} | {item['Risco']} | {item['Próxima ação']} |"
            for item in _gerar_tabela_clientes(registros)
        ]
    )

    linhas_insights = "\n".join([f"- {item}" for item in _gerar_insights_clientes(registros)])

    linhas_decisoes = "\n".join(
        [
            f"| {item['Decisão']} | {item['Critério']} | {item['Ação']} | {item['Prioridade']} |"
            for item in _gerar_decisoes_clientes(registros)
        ]
    )

    return f"""# Clientes Beta Pagos — Máquina de Preço-Teto

Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Diagnóstico

**Score de clientes beta:** {score}/100  
**Classificação:** {classificacao}  

## Leitura

{leitura}

## Métricas

| Métrica | Valor | Leitura |
|---|---:|---|
{linhas_metricas}

## Clientes

| Cliente | Plano | Valor | Pagamento | Acesso | Risco | Próxima ação |
|---|---|---:|---|---|---|---|
{linhas_clientes}

## Insights

{linhas_insights}

## Decisões recomendadas

| Decisão | Critério | Ação | Prioridade |
|---|---|---|---|
{linhas_decisoes}

## Regra

Na Fase 3, não basta vender. É preciso entregar, acompanhar, suportar e medir retenção.
"""


def _injetar_css_clientes() -> None:
    st.markdown(
        """
        <style>
            .cb-hero {
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

            .cb-eyebrow {
                color: #d6b56d;
                font-size: 0.78rem;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.35rem;
            }

            .cb-title {
                color: #f4f7fb;
                font-size: 2.1rem;
                font-weight: 900;
                margin-bottom: 0.45rem;
                line-height: 1.14;
            }

            .cb-subtitle {
                color: rgba(244, 247, 251, 0.76);
                font-size: 1rem;
                line-height: 1.62;
                max-width: 1080px;
            }

            .cb-card {
                padding: 1.1rem 1.15rem;
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.035);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.18);
                height: 100%;
            }

            .cb-card-label {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .cb-card-value {
                color: #f4f7fb;
                font-size: 1.22rem;
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .cb-card-note {
                color: rgba(244, 247, 251, 0.68);
                font-size: 0.87rem;
                line-height: 1.47;
            }

            .cb-highlight {
                padding: 0.95rem 1rem;
                border-radius: 16px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.92rem;
                line-height: 1.55;
                margin-bottom: 0.7rem;
            }

            .cb-copy {
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

            .cb-disclaimer {
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
        <div class="cb-card">
            <div class="cb-card-label">{label}</div>
            <div class="cb-card-value">{value}</div>
            <div class="cb-card-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _copy_box(texto: str) -> None:
    st.markdown(
        f"""
        <div class="cb-copy">{texto}</div>
        """,
        unsafe_allow_html=True,
    )


def renderizar_clientes_beta() -> None:
    """
    Renderiza a central de clientes beta pagos.
    """
    _injetar_css_clientes()

    registros = carregar_clientes_beta()

    score = _calcular_score_clientes(registros)
    classificacao = _classificar_clientes(score, len(registros))
    leitura = _gerar_leitura_clientes(score, registros)

    total = len(registros)
    pagos = _contar(registros, "status_pagamento", "Pago")
    ativos = _clientes_ativos(registros)
    receita = _receita_total(registros)
    mrr = _mrr_estimado(registros)
    em_risco = _clientes_em_risco(registros)
    satisfacao_media = _media_campo(registros, "satisfacao")

    st.session_state["resultado_clientes_beta"] = {
        "score_clientes_beta": score,
        "classificacao": classificacao,
        "total_clientes": total,
        "clientes_pagos": pagos,
        "clientes_ativos": ativos,
        "receita_total": receita,
        "mrr_estimado": mrr,
        "clientes_em_risco": em_risco,
        "satisfacao_media": satisfacao_media,
    }

    st.markdown(
        """
        <div class="cb-hero">
            <div class="cb-eyebrow">Fase 3.0 — Clientes beta pagos</div>
            <div class="cb-title">Clientes Beta Pagos e Controle Manual de Acesso</div>
            <div class="cb-subtitle">
                Controle os primeiros clientes pagantes, pagamento, acesso, onboarding, suporte,
                satisfação e risco de cancelamento antes de automatizar o negócio.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="cb-highlight">
            O primeiro dinheiro valida interesse. A primeira entrega valida negócio.
            Cliente pagante precisa de acesso, suporte, clareza e acompanhamento.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Diagnóstico dos clientes beta")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Score clientes", f"{score}/100")

    with col_2:
        st.metric("Classificação", classificacao)

    with col_3:
        st.metric("Receita real", _fmt_moeda(receita))

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
        _card("Clientes registrados", str(total), "Base beta paga cadastrada.")

    with col_b:
        _card("Pagos", str(pagos), "Pagamentos confirmados.")

    with col_c:
        _card("Ativos pagos", str(ativos), "Usuários com entrega em andamento.")

    with col_d:
        _card("Em risco", str(em_risco), "Prioridade de suporte e retenção.")

    st.divider()

    st.markdown("### Métricas operacionais")

    st.dataframe(
        _gerar_tabela_metricas(registros),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Insights automáticos")

    for insight in _gerar_insights_clientes(registros):
        st.markdown(f"- {insight}")

    st.divider()

    st.markdown("### Decisões recomendadas")

    st.dataframe(
        _gerar_decisoes_clientes(registros),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Registrar cliente beta pago")

    with st.form("form_clientes_beta"):
        col_form_1, col_form_2 = st.columns(2)

        with col_form_1:
            nome_cliente = st.text_input(
                "Nome do cliente",
                value="",
                placeholder="Ex: João, Maria, Cliente 01...",
                key="cb_nome_cliente",
            )

            email_ou_contato = st.text_input(
                "E-mail ou contato",
                value="",
                placeholder="WhatsApp, e-mail ou identificação",
                key="cb_contato",
            )

            perfil = st.selectbox(
                "Perfil",
                PERFIS_CLIENTE,
                key="cb_perfil",
            )

            canal_origem = st.selectbox(
                "Canal de origem",
                CANAIS_ORIGEM,
                key="cb_canal",
            )

            plano = st.selectbox(
                "Plano vendido",
                PLANOS,
                key="cb_plano",
            )

            valor_pago = st.number_input(
                "Valor pago",
                min_value=0.0,
                max_value=10000.0,
                value=29.0,
                step=1.0,
                key="cb_valor",
            )

            periodicidade = st.selectbox(
                "Periodicidade",
                PERIODICIDADES,
                key="cb_periodicidade",
            )

        with col_form_2:
            forma_pagamento = st.selectbox(
                "Forma de pagamento",
                FORMAS_PAGAMENTO,
                key="cb_forma_pagamento",
            )

            status_pagamento = st.selectbox(
                "Status do pagamento",
                STATUS_PAGAMENTO,
                key="cb_status_pagamento",
            )

            status_acesso = st.selectbox(
                "Status do acesso",
                STATUS_ACESSO,
                key="cb_status_acesso",
            )

            status_onboarding = st.selectbox(
                "Status do onboarding",
                STATUS_ONBOARDING,
                key="cb_status_onboarding",
            )

            status_cliente = st.selectbox(
                "Status do cliente",
                STATUS_CLIENTE,
                key="cb_status_cliente",
            )

            risco_cancelamento = st.selectbox(
                "Risco de cancelamento",
                RISCO_CANCELAMENTO,
                key="cb_risco",
            )

            satisfacao = st.slider(
                "Satisfação inicial",
                0,
                10,
                7,
                key="cb_satisfacao",
            )

        col_datas_1, col_datas_2 = st.columns(2)

        with col_datas_1:
            data_inicio = st.text_input(
                "Data de início",
                value="",
                placeholder="Ex: 20/06/2026",
                key="cb_data_inicio",
            )

        with col_datas_2:
            data_renovacao = st.text_input(
                "Data de renovação",
                value="",
                placeholder="Ex: 20/07/2026",
                key="cb_data_renovacao",
            )

        principal_motivo_compra = st.text_area(
            "Principal motivo da compra",
            value="",
            height=80,
            placeholder="O que fez essa pessoa pagar?",
            key="cb_motivo_compra",
        )

        principal_duvida = st.text_area(
            "Principal dúvida",
            value="",
            height=80,
            placeholder="O que ainda está confuso para o cliente?",
            key="cb_duvida",
        )

        suporte_pendente = st.text_area(
            "Suporte pendente",
            value="",
            height=80,
            placeholder="Existe algo que precisa ser resolvido?",
            key="cb_suporte",
        )

        proxima_acao = st.selectbox(
            "Próxima ação",
            PROXIMAS_ACOES,
            key="cb_proxima_acao",
        )

        observacoes = st.text_area(
            "Observações",
            value="",
            height=90,
            key="cb_observacoes",
        )

        enviar = st.form_submit_button("Salvar cliente beta")

        if enviar:
            if nome_cliente.strip() == "":
                st.error("Preencha o nome do cliente.")
            else:
                adicionar_cliente_beta(
                    nome_cliente=nome_cliente,
                    email_ou_contato=email_ou_contato,
                    perfil=perfil,
                    canal_origem=canal_origem,
                    plano=plano,
                    valor_pago=valor_pago,
                    periodicidade=periodicidade,
                    forma_pagamento=forma_pagamento,
                    status_pagamento=status_pagamento,
                    status_acesso=status_acesso,
                    status_onboarding=status_onboarding,
                    data_inicio=data_inicio,
                    data_renovacao=data_renovacao,
                    satisfacao=satisfacao,
                    risco_cancelamento=risco_cancelamento,
                    principal_motivo_compra=principal_motivo_compra,
                    principal_duvida=principal_duvida,
                    suporte_pendente=suporte_pendente,
                    proxima_acao=proxima_acao,
                    status_cliente=status_cliente,
                    observacoes=observacoes,
                )

                st.success("Cliente beta registrado com sucesso.")
                st.rerun()

    st.divider()

    st.markdown("### Clientes beta registrados")

    registros = carregar_clientes_beta()

    if len(registros) == 0:
        st.info("Nenhum cliente beta pago registrado ainda.")
    else:
        st.dataframe(
            _gerar_tabela_clientes(registros),
            use_container_width=True,
            hide_index=True,
        )

        suporte = _gerar_tabela_suporte(registros)

        if len(suporte) > 0:
            st.divider()
            st.markdown("### Suporte e dúvidas pendentes")
            st.dataframe(
                suporte,
                use_container_width=True,
                hide_index=True,
            )

    st.divider()

    st.markdown("### Mensagem de boas-vindas")

    _copy_box(_gerar_script_boas_vindas())

    st.divider()

    st.markdown("### Mensagem de follow-up de satisfação")

    _copy_box(_gerar_script_followup_satisfacao())

    st.divider()

    if len(registros) > 0:
        col_download, col_limpar = st.columns(2)

        with col_download:
            with open(CAMINHO_CLIENTES_BETA, "rb") as arquivo:
                st.download_button(
                    label="Baixar clientes beta em CSV",
                    data=arquivo,
                    file_name="clientes_beta.csv",
                    mime="text/csv",
                    key="download_clientes_beta_csv",
                )

            st.download_button(
                label="Baixar relatório clientes beta (.md)",
                data=_gerar_markdown_clientes(registros),
                file_name="relatorio_clientes_beta.md",
                mime="text/markdown",
                key="download_clientes_beta_md",
            )

        with col_limpar:
            confirmar = st.checkbox(
                "Confirmar limpeza dos clientes beta",
                value=False,
                key="cb_confirmar_limpeza",
            )

            if st.button("Limpar clientes beta", key="cb_limpar"):
                if confirmar:
                    limpar_clientes_beta()
                    st.success("Clientes beta limpos com sucesso.")
                    st.rerun()
                else:
                    st.warning("Marque a confirmação antes de limpar.")

    st.markdown(
        """
        <div class="cb-disclaimer">
            <strong>Regra da Fase 3:</strong> cliente beta pago não é apenas venda.
            É entrega, suporte, confiança, aprendizado e retenção. Só automatize depois de provar isso manualmente.
        </div>
        """,
        unsafe_allow_html=True,
    )