# suporte_beta.py

import csv
import uuid
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List

import streamlit as st


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v3.1 — Suporte Beta, Tickets e Controle de Problemas
# ------------------------------------------------------------
# Esta tela controla suporte dos primeiros clientes beta pagos.
#
# Objetivo:
# - registrar problemas de clientes pagantes
# - controlar prioridade, status e risco de cancelamento
# - medir qualidade do suporte
# - transformar problemas em melhorias de produto
# - evitar que suporte desorganizado destrua retenção
# ============================================================


CAMINHO_SUPORTE_BETA = Path("suporte_beta.csv")
CAMINHO_CLIENTES_BETA = Path("clientes_beta.csv")


CAMPOS_SUPORTE = [
    "id",
    "data_registro",
    "cliente",
    "contato_cliente",
    "perfil_cliente",
    "tipo_problema",
    "categoria",
    "prioridade",
    "status_atendimento",
    "impacto_cliente",
    "risco_cancelamento",
    "descricao_problema",
    "causa_provavel",
    "solucao_aplicada",
    "aprendizado_produto",
    "tempo_resposta_horas",
    "satisfacao_pos_atendimento",
    "proxima_acao",
    "responsavel",
    "prazo",
    "observacoes",
]


TIPOS_PROBLEMA = [
    "Dúvida de uso",
    "Problema de acesso",
    "Erro técnico",
    "Dificuldade no valuation",
    "Dúvida sobre relatório",
    "Confusão sobre preço-teto",
    "Problema no onboarding",
    "Dúvida sobre pagamento",
    "Pedido de melhoria",
    "Reclamação",
    "Outro",
]


CATEGORIAS = [
    "Acesso",
    "Onboarding",
    "Valuation",
    "Relatórios",
    "UX",
    "Pagamento",
    "Dados",
    "Educação",
    "Produto",
    "Comercial",
    "Outro",
]


PRIORIDADES = [
    "Crítica",
    "Alta",
    "Média",
    "Baixa",
]


STATUS_ATENDIMENTO = [
    "Aberto",
    "Em análise",
    "Aguardando cliente",
    "Em correção",
    "Resolvido",
    "Fechado",
    "Virou melhoria de produto",
    "Sem solução por enquanto",
]


IMPACTOS_CLIENTE = [
    "Impede o uso",
    "Dificulta muito o uso",
    "Dificulta pouco o uso",
    "Dúvida simples",
    "Sugestão sem urgência",
]


RISCO_CANCELAMENTO = [
    "Baixo",
    "Médio",
    "Alto",
    "Crítico",
]


PROXIMAS_ACOES = [
    "Responder cliente",
    "Corrigir erro",
    "Explicar funcionamento",
    "Enviar tutorial",
    "Guiar primeiro uso",
    "Pedir print/detalhe",
    "Transformar em melhoria",
    "Validar se resolveu",
    "Encerrar atendimento",
    "Aguardar cliente",
]


def _garantir_arquivo_suporte() -> None:
    if CAMINHO_SUPORTE_BETA.exists():
        return

    with open(CAMINHO_SUPORTE_BETA, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_SUPORTE)
        escritor.writeheader()


def carregar_suporte_beta() -> List[Dict[str, str]]:
    _garantir_arquivo_suporte()

    with open(CAMINHO_SUPORTE_BETA, "r", newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        registros = []

        for linha in leitor:
            registro = {campo: linha.get(campo, "") for campo in CAMPOS_SUPORTE}
            registros.append(registro)

        return registros


def salvar_suporte_beta(registros: List[Dict[str, Any]]) -> None:
    with open(CAMINHO_SUPORTE_BETA, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_SUPORTE)
        escritor.writeheader()

        for registro in registros:
            linha = {campo: registro.get(campo, "") for campo in CAMPOS_SUPORTE}
            escritor.writerow(linha)


def limpar_suporte_beta() -> None:
    salvar_suporte_beta([])


def _carregar_clientes_beta() -> List[Dict[str, str]]:
    if not CAMINHO_CLIENTES_BETA.exists():
        return []

    try:
        with open(CAMINHO_CLIENTES_BETA, "r", newline="", encoding="utf-8") as arquivo:
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


def _fmt_percentual(valor: float) -> str:
    return f"{valor:.1f}%"


def adicionar_ticket_suporte(
    cliente: str,
    contato_cliente: str,
    perfil_cliente: str,
    tipo_problema: str,
    categoria: str,
    prioridade: str,
    status_atendimento: str,
    impacto_cliente: str,
    risco_cancelamento: str,
    descricao_problema: str,
    causa_provavel: str,
    solucao_aplicada: str,
    aprendizado_produto: str,
    tempo_resposta_horas: float,
    satisfacao_pos_atendimento: int,
    proxima_acao: str,
    responsavel: str,
    prazo: str,
    observacoes: str,
) -> None:
    registros = carregar_suporte_beta()

    novo_registro = {
        "id": str(uuid.uuid4())[:8],
        "data_registro": datetime.now().isoformat(timespec="minutes"),
        "cliente": cliente.strip(),
        "contato_cliente": contato_cliente.strip(),
        "perfil_cliente": perfil_cliente.strip(),
        "tipo_problema": tipo_problema,
        "categoria": categoria,
        "prioridade": prioridade,
        "status_atendimento": status_atendimento,
        "impacto_cliente": impacto_cliente,
        "risco_cancelamento": risco_cancelamento,
        "descricao_problema": descricao_problema.strip(),
        "causa_provavel": causa_provavel.strip(),
        "solucao_aplicada": solucao_aplicada.strip(),
        "aprendizado_produto": aprendizado_produto.strip(),
        "tempo_resposta_horas": str(tempo_resposta_horas),
        "satisfacao_pos_atendimento": str(satisfacao_pos_atendimento),
        "proxima_acao": proxima_acao,
        "responsavel": responsavel.strip(),
        "prazo": prazo.strip(),
        "observacoes": observacoes.strip(),
    }

    registros.append(novo_registro)
    salvar_suporte_beta(registros)


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


def _tickets_abertos(registros: List[Dict[str, str]]) -> int:
    status_fechados = ["Resolvido", "Fechado", "Virou melhoria de produto"]

    return len(
        [
            registro for registro in registros
            if registro.get("status_atendimento") not in status_fechados
        ]
    )


def _tickets_resolvidos(registros: List[Dict[str, str]]) -> int:
    return len(
        [
            registro for registro in registros
            if registro.get("status_atendimento") in ["Resolvido", "Fechado"]
        ]
    )


def _tickets_criticos(registros: List[Dict[str, str]]) -> int:
    return len(
        [
            registro for registro in registros
            if registro.get("prioridade") == "Crítica"
            or registro.get("risco_cancelamento") == "Crítico"
            or registro.get("impacto_cliente") == "Impede o uso"
        ]
    )


def _tickets_risco_alto(registros: List[Dict[str, str]]) -> int:
    return len(
        [
            registro for registro in registros
            if registro.get("risco_cancelamento") in ["Alto", "Crítico"]
        ]
    )


def _taxa_resolucao(registros: List[Dict[str, str]]) -> float:
    if len(registros) == 0:
        return 0.0

    return (_tickets_resolvidos(registros) / len(registros)) * 100


def _calcular_score_suporte(registros: List[Dict[str, str]]) -> int:
    total = len(registros)

    if total == 0:
        return 0

    resolvidos = _tickets_resolvidos(registros)
    abertos = _tickets_abertos(registros)
    criticos = _tickets_criticos(registros)
    risco_alto = _tickets_risco_alto(registros)
    taxa_resolucao = _taxa_resolucao(registros)
    satisfacao_media = _media_campo(registros, "satisfacao_pos_atendimento")
    tempo_medio = _media_campo(registros, "tempo_resposta_horas")

    pontos = 0.0
    pontos += min(total * 4.0, 20)
    pontos += min(resolvidos * 9.0, 36)
    pontos += taxa_resolucao * 0.25
    pontos += satisfacao_media * 3.0

    if tempo_medio > 0:
        if tempo_medio <= 2:
            pontos += 15
        elif tempo_medio <= 8:
            pontos += 10
        elif tempo_medio <= 24:
            pontos += 5
        else:
            pontos -= 8

    pontos -= min(abertos * 3.0, 18)
    pontos -= min(criticos * 8.0, 24)
    pontos -= min(risco_alto * 6.0, 18)

    return int(round(max(0, min(100, pontos))))


def _classificar_suporte(score: int, total: int) -> str:
    if total == 0:
        return "Sem tickets de suporte"

    if score >= 85:
        return "Suporte beta forte"
    if score >= 70:
        return "Suporte saudável"
    if score >= 55:
        return "Suporte em validação"
    if score >= 40:
        return "Suporte com risco"
    return "Suporte crítico"


def _gerar_leitura_suporte(score: int, registros: List[Dict[str, str]]) -> str:
    if len(registros) == 0:
        return (
            "Ainda não há tickets de suporte registrados. Quando os primeiros clientes beta usarem o app, "
            "registre dúvidas, travas, erros e reclamações para transformar suporte em melhoria."
        )

    if score >= 85:
        return (
            "O suporte beta está forte. Os problemas estão sendo resolvidos e a experiência tende a sustentar retenção."
        )

    if score >= 70:
        return (
            "O suporte está saudável. Continue medindo tempo de resposta, satisfação e recorrência de problemas."
        )

    if score >= 55:
        return (
            "O suporte ainda está em validação. Há aprendizado, mas é preciso resolver tickets e reduzir risco."
        )

    if score >= 40:
        return (
            "O suporte tem risco. Antes de vender para mais clientes, resolva problemas abertos e críticos."
        )

    return (
        "O suporte está crítico. Vender mais agora pode aumentar cancelamentos e prejudicar confiança."
    )


def _gerar_tabela_tickets(registros: List[Dict[str, str]]) -> List[Dict[str, str]]:
    ordem_prioridade = {
        "Crítica": 4,
        "Alta": 3,
        "Média": 2,
        "Baixa": 1,
    }

    ordem_risco = {
        "Crítico": 4,
        "Alto": 3,
        "Médio": 2,
        "Baixo": 1,
    }

    registros_ordenados = sorted(
        registros,
        key=lambda registro: (
            ordem_prioridade.get(registro.get("prioridade", ""), 0),
            ordem_risco.get(registro.get("risco_cancelamento", ""), 0),
            _safe_float(registro.get("tempo_resposta_horas")),
        ),
        reverse=True,
    )

    tabela = []

    for registro in registros_ordenados:
        tabela.append(
            {
                "Cliente": registro.get("cliente", ""),
                "Tipo": registro.get("tipo_problema", ""),
                "Categoria": registro.get("categoria", ""),
                "Prioridade": registro.get("prioridade", ""),
                "Status": registro.get("status_atendimento", ""),
                "Impacto": registro.get("impacto_cliente", ""),
                "Risco": registro.get("risco_cancelamento", ""),
                "Resposta": f"{registro.get('tempo_resposta_horas', '')}h",
                "Satisfação": f"{registro.get('satisfacao_pos_atendimento', '')}/10",
                "Próxima ação": registro.get("proxima_acao", ""),
                "Prazo": registro.get("prazo", ""),
            }
        )

    return tabela


def _gerar_tabela_aprendizados(registros: List[Dict[str, str]]) -> List[Dict[str, str]]:
    tabela = []

    for registro in registros:
        aprendizado = registro.get("aprendizado_produto", "").strip()

        if aprendizado == "":
            continue

        tabela.append(
            {
                "Categoria": registro.get("categoria", ""),
                "Problema": registro.get("tipo_problema", ""),
                "Aprendizado": aprendizado,
                "Possível melhoria": _sugerir_melhoria(registro),
            }
        )

    return tabela


def _sugerir_melhoria(registro: Dict[str, str]) -> str:
    categoria = registro.get("categoria", "")
    tipo = registro.get("tipo_problema", "")
    impacto = registro.get("impacto_cliente", "")

    if categoria == "Acesso":
        return "Melhorar instrução de acesso e criar checklist de liberação."
    if categoria == "Onboarding":
        return "Criar guia inicial mais simples e passo a passo."
    if categoria == "Valuation":
        return "Adicionar exemplos, validações e explicações sobre premissas."
    if categoria == "Relatórios":
        return "Melhorar clareza do relatório e leitura executiva."
    if tipo == "Erro técnico":
        return "Transformar em correção técnica prioritária."
    if impacto == "Impede o uso":
        return "Tratar como melhoria crítica antes de vender mais."
    return "Avaliar se deve virar prioridade de produto."


def _gerar_tabela_metricas(registros: List[Dict[str, str]]) -> List[Dict[str, str]]:
    total = len(registros)
    abertos = _tickets_abertos(registros)
    resolvidos = _tickets_resolvidos(registros)
    criticos = _tickets_criticos(registros)
    risco_alto = _tickets_risco_alto(registros)
    taxa_resolucao = _taxa_resolucao(registros)
    tempo_medio = _media_campo(registros, "tempo_resposta_horas")
    satisfacao_media = _media_campo(registros, "satisfacao_pos_atendimento")

    return [
        {
            "Métrica": "Tickets registrados",
            "Valor": str(total),
            "Leitura": "Volume total de atendimentos registrados.",
        },
        {
            "Métrica": "Tickets abertos",
            "Valor": str(abertos),
            "Leitura": "Demandas que ainda precisam de ação.",
        },
        {
            "Métrica": "Tickets resolvidos",
            "Valor": str(resolvidos),
            "Leitura": "Problemas encerrados ou solucionados.",
        },
        {
            "Métrica": "Tickets críticos",
            "Valor": str(criticos),
            "Leitura": "Casos que podem bloquear uso ou gerar cancelamento.",
        },
        {
            "Métrica": "Tickets com risco alto/crítico",
            "Valor": str(risco_alto),
            "Leitura": "Demandas que ameaçam retenção.",
        },
        {
            "Métrica": "Taxa de resolução",
            "Valor": _fmt_percentual(taxa_resolucao),
            "Leitura": "Percentual de tickets resolvidos.",
        },
        {
            "Métrica": "Tempo médio de resposta",
            "Valor": f"{tempo_medio:.1f}h",
            "Leitura": "Tempo médio estimado até resposta ou encaminhamento.",
        },
        {
            "Métrica": "Satisfação pós-atendimento",
            "Valor": f"{satisfacao_media:.1f}/10",
            "Leitura": "Percepção do cliente após atendimento.",
        },
    ]


def _gerar_insights_suporte(registros: List[Dict[str, str]]) -> List[str]:
    if len(registros) == 0:
        return [
            "Ainda não há tickets de suporte registrados.",
            "Registre toda dúvida ou trava dos clientes beta pagos.",
            "Suporte não é custo nesta fase: é fonte direta de produto, retenção e confiança.",
        ]

    insights = []

    total = len(registros)
    abertos = _tickets_abertos(registros)
    resolvidos = _tickets_resolvidos(registros)
    criticos = _tickets_criticos(registros)
    risco_alto = _tickets_risco_alto(registros)
    taxa_resolucao = _taxa_resolucao(registros)
    tempo_medio = _media_campo(registros, "tempo_resposta_horas")
    satisfacao = _media_campo(registros, "satisfacao_pos_atendimento")
    categoria = _mais_frequente(registros, "categoria")
    tipo = _mais_frequente(registros, "tipo_problema")

    insights.append(f"Você tem {total} ticket(s) de suporte registrados.")
    insights.append(f"Tickets abertos: {abertos}.")
    insights.append(f"Tickets resolvidos: {resolvidos}.")
    insights.append(f"Taxa de resolução: {_fmt_percentual(taxa_resolucao)}.")
    insights.append(f"Tempo médio de resposta: {tempo_medio:.1f}h.")
    insights.append(f"Satisfação média pós-atendimento: {satisfacao:.1f}/10.")

    if criticos > 0:
        insights.append(f"Existem {criticos} ticket(s) crítico(s). Eles devem ser resolvidos antes de vender mais.")

    if risco_alto > 0:
        insights.append(f"Existem {risco_alto} ticket(s) com risco alto/crítico de cancelamento.")

    if categoria != "N/D":
        insights.append(f"Categoria mais comum de suporte: {categoria}.")

    if tipo != "N/D":
        insights.append(f"Tipo de problema mais comum: {tipo}.")

    if satisfacao < 7 and total > 0:
        insights.append("A satisfação pós-atendimento está baixa. Melhore clareza, rapidez e solução.")

    insights.append("Na Fase 3, cada ticket deve virar uma decisão: corrigir, ensinar, simplificar ou transformar em produto.")

    return insights


def _gerar_decisoes_suporte(registros: List[Dict[str, str]]) -> List[Dict[str, str]]:
    if len(registros) == 0:
        return [
            {
                "Decisão": "Começar a registrar suporte",
                "Critério": "Nenhum ticket cadastrado.",
                "Ação": "Registrar dúvidas, erros e travas dos primeiros clientes.",
                "Prioridade": "Muito alta",
            }
        ]

    decisoes = []

    abertos = _tickets_abertos(registros)
    criticos = _tickets_criticos(registros)
    risco_alto = _tickets_risco_alto(registros)
    taxa_resolucao = _taxa_resolucao(registros)
    satisfacao = _media_campo(registros, "satisfacao_pos_atendimento")
    categoria = _mais_frequente(registros, "categoria")
    tipo = _mais_frequente(registros, "tipo_problema")

    if criticos > 0:
        decisoes.append(
            {
                "Decisão": "Resolver tickets críticos",
                "Critério": "Há tickets críticos ou que impedem uso.",
                "Ação": "Parar novas vendas se necessário e resolver o bloqueio.",
                "Prioridade": "Muito alta",
            }
        )

    if risco_alto > 0:
        decisoes.append(
            {
                "Decisão": "Reduzir risco de cancelamento",
                "Critério": "Há tickets com risco alto/crítico.",
                "Ação": "Fazer contato direto e resolver a dor do cliente.",
                "Prioridade": "Muito alta",
            }
        )

    if abertos > 3:
        decisoes.append(
            {
                "Decisão": "Diminuir fila de suporte",
                "Critério": "Mais de 3 tickets abertos.",
                "Ação": "Resolver tickets antes de vender para novos clientes.",
                "Prioridade": "Alta",
            }
        )

    if taxa_resolucao < 50 and len(registros) >= 3:
        decisoes.append(
            {
                "Decisão": "Melhorar processo de atendimento",
                "Critério": "Taxa de resolução baixa.",
                "Ação": "Criar respostas padrão, tutorial e rotina diária de suporte.",
                "Prioridade": "Alta",
            }
        )

    if satisfacao < 7 and len(registros) >= 2:
        decisoes.append(
            {
                "Decisão": "Melhorar qualidade do suporte",
                "Critério": "Satisfação pós-atendimento abaixo de 7.",
                "Ação": "Responder com mais clareza, rapidez e acompanhamento.",
                "Prioridade": "Alta",
            }
        )

    if categoria == "Onboarding":
        decisoes.append(
            {
                "Decisão": "Melhorar onboarding",
                "Critério": "Onboarding aparece como categoria recorrente.",
                "Ação": "Criar passo a passo mais simples para o primeiro uso.",
                "Prioridade": "Média",
            }
        )

    if tipo == "Erro técnico":
        decisoes.append(
            {
                "Decisão": "Priorizar correções técnicas",
                "Critério": "Erro técnico é recorrente.",
                "Ação": "Transformar tickets em tarefas técnicas priorizadas.",
                "Prioridade": "Alta",
            }
        )

    if len(decisoes) == 0:
        decisoes.append(
            {
                "Decisão": "Manter suporte controlado",
                "Critério": "Sem alerta crítico.",
                "Ação": "Continuar registrando, resolvendo e transformando tickets em aprendizado.",
                "Prioridade": "Média",
            }
        )

    return decisoes


def _gerar_script_resposta_inicial() -> str:
    return """Resposta inicial para suporte:

Oi! Obrigado por avisar.

Vou analisar isso com cuidado. Para eu resolver mais rápido, me envie por favor:

1. o que você estava tentando fazer;
2. em qual tela/aba aconteceu;
3. se apareceu alguma mensagem de erro;
4. um print, se possível.

Como essa é uma versão beta, esse tipo de feedback ajuda diretamente a melhorar o produto.

Vou te retornar assim que eu entender a causa ou encontrar uma solução."""


def _gerar_script_ticket_resolvido() -> str:
    return """Resposta quando o suporte foi resolvido:

Consegui ajustar/verificar esse ponto.

Pode testar novamente e me dizer se agora funcionou?

Queria também saber:
1. a explicação ficou clara?
2. isso atrapalhou muito sua experiência?
3. de 0 a 10, como você avalia esse atendimento?

Seu feedback me ajuda a melhorar o produto e o suporte para os próximos usuários beta."""


def _gerar_markdown_suporte(registros: List[Dict[str, str]]) -> str:
    score = _calcular_score_suporte(registros)
    classificacao = _classificar_suporte(score, len(registros))
    leitura = _gerar_leitura_suporte(score, registros)

    linhas_metricas = "\n".join(
        [
            f"| {item['Métrica']} | {item['Valor']} | {item['Leitura']} |"
            for item in _gerar_tabela_metricas(registros)
        ]
    )

    linhas_tickets = "\n".join(
        [
            f"| {item['Cliente']} | {item['Tipo']} | {item['Prioridade']} | {item['Status']} | {item['Risco']} | {item['Próxima ação']} |"
            for item in _gerar_tabela_tickets(registros)
        ]
    )

    linhas_insights = "\n".join([f"- {item}" for item in _gerar_insights_suporte(registros)])

    linhas_decisoes = "\n".join(
        [
            f"| {item['Decisão']} | {item['Critério']} | {item['Ação']} | {item['Prioridade']} |"
            for item in _gerar_decisoes_suporte(registros)
        ]
    )

    return f"""# Suporte Beta — Máquina de Preço-Teto

Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Diagnóstico

**Score de suporte:** {score}/100  
**Classificação:** {classificacao}  

## Leitura

{leitura}

## Métricas

| Métrica | Valor | Leitura |
|---|---:|---|
{linhas_metricas}

## Tickets

| Cliente | Tipo | Prioridade | Status | Risco | Próxima ação |
|---|---|---|---|---|---|
{linhas_tickets}

## Insights

{linhas_insights}

## Decisões recomendadas

| Decisão | Critério | Ação | Prioridade |
|---|---|---|---|
{linhas_decisoes}

## Regra

Suporte beta não é só atendimento. É descoberta de produto, retenção e confiança.
"""


def _injetar_css_suporte() -> None:
    st.markdown(
        """
        <style>
            .sb-hero {
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

            .sb-eyebrow {
                color: #d6b56d;
                font-size: 0.78rem;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.35rem;
            }

            .sb-title {
                color: #f4f7fb;
                font-size: 2.1rem;
                font-weight: 900;
                margin-bottom: 0.45rem;
                line-height: 1.14;
            }

            .sb-subtitle {
                color: rgba(244, 247, 251, 0.76);
                font-size: 1rem;
                line-height: 1.62;
                max-width: 1080px;
            }

            .sb-card {
                padding: 1.1rem 1.15rem;
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.035);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.18);
                height: 100%;
            }

            .sb-card-label {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .sb-card-value {
                color: #f4f7fb;
                font-size: 1.22rem;
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .sb-card-note {
                color: rgba(244, 247, 251, 0.68);
                font-size: 0.87rem;
                line-height: 1.47;
            }

            .sb-highlight {
                padding: 0.95rem 1rem;
                border-radius: 16px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.92rem;
                line-height: 1.55;
                margin-bottom: 0.7rem;
            }

            .sb-copy {
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

            .sb-disclaimer {
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
        <div class="sb-card">
            <div class="sb-card-label">{label}</div>
            <div class="sb-card-value">{value}</div>
            <div class="sb-card-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _copy_box(texto: str) -> None:
    st.markdown(
        f"""
        <div class="sb-copy">{texto}</div>
        """,
        unsafe_allow_html=True,
    )


def renderizar_suporte_beta() -> None:
    """
    Renderiza a central de suporte beta.
    """
    _injetar_css_suporte()

    registros = carregar_suporte_beta()
    clientes_beta = _carregar_clientes_beta()

    score = _calcular_score_suporte(registros)
    classificacao = _classificar_suporte(score, len(registros))
    leitura = _gerar_leitura_suporte(score, registros)

    total = len(registros)
    abertos = _tickets_abertos(registros)
    resolvidos = _tickets_resolvidos(registros)
    criticos = _tickets_criticos(registros)
    risco_alto = _tickets_risco_alto(registros)
    satisfacao_media = _media_campo(registros, "satisfacao_pos_atendimento")

    st.session_state["resultado_suporte_beta"] = {
        "score_suporte": score,
        "classificacao": classificacao,
        "total_tickets": total,
        "tickets_abertos": abertos,
        "tickets_resolvidos": resolvidos,
        "tickets_criticos": criticos,
        "tickets_risco_alto": risco_alto,
        "satisfacao_media": satisfacao_media,
    }

    st.markdown(
        """
        <div class="sb-hero">
            <div class="sb-eyebrow">Fase 3.1 — Suporte beta</div>
            <div class="sb-title">Suporte Beta, Tickets e Controle de Problemas</div>
            <div class="sb-subtitle">
                Registre dúvidas, erros, travas e reclamações dos clientes beta pagos.
                Transforme suporte em retenção, confiança e melhoria real de produto.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="sb-highlight">
            Na Fase 3, suporte não é detalhe. É onde você descobre se o produto realmente entrega valor para quem pagou.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Diagnóstico do suporte beta")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Score suporte", f"{score}/100")

    with col_2:
        st.metric("Classificação", classificacao)

    with col_3:
        st.metric("Tickets abertos", abertos)

    with col_4:
        st.metric("Tickets críticos", criticos)

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
        _card("Tickets registrados", str(total), "Atendimentos documentados.")

    with col_b:
        _card("Resolvidos", str(resolvidos), "Casos solucionados ou fechados.")

    with col_c:
        _card("Risco alto/crítico", str(risco_alto), "Ameaça de cancelamento.")

    with col_d:
        _card("Satisfação", f"{satisfacao_media:.1f}/10", "Pós-atendimento.")

    st.divider()

    st.markdown("### Métricas operacionais")

    st.dataframe(
        _gerar_tabela_metricas(registros),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Insights automáticos")

    for insight in _gerar_insights_suporte(registros):
        st.markdown(f"- {insight}")

    st.divider()

    st.markdown("### Decisões recomendadas")

    st.dataframe(
        _gerar_decisoes_suporte(registros),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Registrar ticket de suporte")

    opcoes_clientes = [""] + [
        cliente.get("nome_cliente", "")
        for cliente in clientes_beta
        if cliente.get("nome_cliente", "").strip() != ""
    ]

    with st.form("form_suporte_beta"):
        col_form_1, col_form_2 = st.columns(2)

        with col_form_1:
            cliente_selecionado = st.selectbox(
                "Selecionar cliente já cadastrado",
                opcoes_clientes,
                key="sb_cliente_selecionado",
            )

            cliente = st.text_input(
                "Cliente",
                value=cliente_selecionado,
                placeholder="Nome ou identificação do cliente",
                key="sb_cliente",
            )

            contato_cliente = st.text_input(
                "Contato do cliente",
                value="",
                placeholder="WhatsApp, e-mail ou outro contato",
                key="sb_contato",
            )

            perfil_cliente = st.text_input(
                "Perfil do cliente",
                value="",
                placeholder="Ex: investidor iniciante, intermediário...",
                key="sb_perfil",
            )

            tipo_problema = st.selectbox(
                "Tipo de problema",
                TIPOS_PROBLEMA,
                key="sb_tipo",
            )

            categoria = st.selectbox(
                "Categoria",
                CATEGORIAS,
                key="sb_categoria",
            )

        with col_form_2:
            prioridade = st.selectbox(
                "Prioridade",
                PRIORIDADES,
                key="sb_prioridade",
            )

            status_atendimento = st.selectbox(
                "Status do atendimento",
                STATUS_ATENDIMENTO,
                key="sb_status",
            )

            impacto_cliente = st.selectbox(
                "Impacto no cliente",
                IMPACTOS_CLIENTE,
                key="sb_impacto",
            )

            risco_cancelamento = st.selectbox(
                "Risco de cancelamento",
                RISCO_CANCELAMENTO,
                key="sb_risco",
            )

            tempo_resposta_horas = st.number_input(
                "Tempo de resposta/encaminhamento em horas",
                min_value=0.0,
                max_value=1000.0,
                value=2.0,
                step=0.5,
                key="sb_tempo",
            )

            satisfacao_pos_atendimento = st.slider(
                "Satisfação pós-atendimento",
                0,
                10,
                7,
                key="sb_satisfacao",
            )

        descricao_problema = st.text_area(
            "Descrição do problema",
            value="",
            height=90,
            placeholder="O que aconteceu? Onde o cliente travou?",
            key="sb_descricao",
        )

        causa_provavel = st.text_area(
            "Causa provável",
            value="",
            height=80,
            placeholder="Erro técnico, falta de clareza, onboarding fraco, dúvida de conceito...",
            key="sb_causa",
        )

        solucao_aplicada = st.text_area(
            "Solução aplicada",
            value="",
            height=80,
            placeholder="O que foi feito para resolver ou encaminhar?",
            key="sb_solucao",
        )

        aprendizado_produto = st.text_area(
            "Aprendizado para o produto",
            value="",
            height=80,
            placeholder="O que esse atendimento ensina sobre produto, UX, onboarding ou educação?",
            key="sb_aprendizado",
        )

        col_final_1, col_final_2, col_final_3 = st.columns(3)

        with col_final_1:
            proxima_acao = st.selectbox(
                "Próxima ação",
                PROXIMAS_ACOES,
                key="sb_proxima_acao",
            )

        with col_final_2:
            responsavel = st.text_input(
                "Responsável",
                value="Leo",
                key="sb_responsavel",
            )

        with col_final_3:
            prazo = st.text_input(
                "Prazo",
                value="",
                placeholder="Ex: hoje, amanhã, esta semana...",
                key="sb_prazo",
            )

        observacoes = st.text_area(
            "Observações",
            value="",
            height=80,
            key="sb_observacoes",
        )

        enviar = st.form_submit_button("Salvar ticket de suporte")

        if enviar:
            if cliente.strip() == "":
                st.error("Preencha o nome ou identificação do cliente.")
            elif descricao_problema.strip() == "":
                st.error("Descreva o problema do cliente.")
            else:
                adicionar_ticket_suporte(
                    cliente=cliente,
                    contato_cliente=contato_cliente,
                    perfil_cliente=perfil_cliente,
                    tipo_problema=tipo_problema,
                    categoria=categoria,
                    prioridade=prioridade,
                    status_atendimento=status_atendimento,
                    impacto_cliente=impacto_cliente,
                    risco_cancelamento=risco_cancelamento,
                    descricao_problema=descricao_problema,
                    causa_provavel=causa_provavel,
                    solucao_aplicada=solucao_aplicada,
                    aprendizado_produto=aprendizado_produto,
                    tempo_resposta_horas=tempo_resposta_horas,
                    satisfacao_pos_atendimento=satisfacao_pos_atendimento,
                    proxima_acao=proxima_acao,
                    responsavel=responsavel,
                    prazo=prazo,
                    observacoes=observacoes,
                )

                st.success("Ticket de suporte registrado com sucesso.")
                st.rerun()

    st.divider()

    st.markdown("### Tickets registrados")

    registros = carregar_suporte_beta()

    if len(registros) == 0:
        st.info("Nenhum ticket de suporte registrado ainda.")
    else:
        st.dataframe(
            _gerar_tabela_tickets(registros),
            use_container_width=True,
            hide_index=True,
        )

        aprendizados = _gerar_tabela_aprendizados(registros)

        if len(aprendizados) > 0:
            st.divider()
            st.markdown("### Aprendizados para produto")
            st.dataframe(
                aprendizados,
                use_container_width=True,
                hide_index=True,
            )

    st.divider()

    st.markdown("### Resposta inicial de suporte")

    _copy_box(_gerar_script_resposta_inicial())

    st.divider()

    st.markdown("### Mensagem após resolver ticket")

    _copy_box(_gerar_script_ticket_resolvido())

    st.divider()

    if len(registros) > 0:
        col_download, col_limpar = st.columns(2)

        with col_download:
            with open(CAMINHO_SUPORTE_BETA, "rb") as arquivo:
                st.download_button(
                    label="Baixar suporte beta em CSV",
                    data=arquivo,
                    file_name="suporte_beta.csv",
                    mime="text/csv",
                    key="download_suporte_beta_csv",
                )

            st.download_button(
                label="Baixar relatório suporte beta (.md)",
                data=_gerar_markdown_suporte(registros),
                file_name="relatorio_suporte_beta.md",
                mime="text/markdown",
                key="download_suporte_beta_md",
            )

        with col_limpar:
            confirmar = st.checkbox(
                "Confirmar limpeza dos tickets de suporte",
                value=False,
                key="sb_confirmar_limpeza",
            )

            if st.button("Limpar suporte beta", key="sb_limpar"):
                if confirmar:
                    limpar_suporte_beta()
                    st.success("Tickets de suporte limpos com sucesso.")
                    st.rerun()
                else:
                    st.warning("Marque a confirmação antes de limpar.")

    st.markdown(
        """
        <div class="sb-disclaimer">
            <strong>Regra do suporte beta:</strong> antes de vender mais, resolva o que bloqueia uso,
            reduz confiança ou aumenta risco de cancelamento. Suporte ruim mata retenção cedo.
        </div>
        """,
        unsafe_allow_html=True,
    )