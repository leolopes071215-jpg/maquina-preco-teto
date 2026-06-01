# pre_venda_beta.py

import csv
import uuid
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List

import streamlit as st


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v2.5 — Pré-venda Manual e Validação de Pagamento
# ------------------------------------------------------------
# Esta tela valida monetização antes de construir grande demais.
#
# Objetivo:
# - registrar conversas de pré-venda
# - medir intenção real de pagamento
# - testar planos e preços
# - mapear objeções
# - estimar receita potencial
# - orientar decisão comercial do beta pago
# ============================================================


CAMINHO_PRE_VENDA_BETA = Path("pre_venda_beta.csv")


CAMPOS_PRE_VENDA = [
    "id",
    "data_registro",
    "nome_lead",
    "perfil",
    "canal_origem",
    "plano_testado",
    "preco_apresentado",
    "periodicidade",
    "resposta_pagamento",
    "chance_conversao",
    "objeção_principal",
    "valor_percebido",
    "principal_motivo_interesse",
    "principal_duvida",
    "condicao_para_pagar",
    "status_followup",
    "proxima_acao",
    "data_followup",
    "decisao_comercial",
    "observacoes",
]


PERFIS_LEAD = [
    "Investidor iniciante",
    "Investidor intermediário",
    "Investidor avançado",
    "Estudante",
    "Criador de conteúdo financeiro",
    "Pessoa próxima sem perfil investidor",
    "Outro",
]


CANAIS_ORIGEM = [
    "WhatsApp",
    "Instagram",
    "LinkedIn",
    "E-mail",
    "Indicação",
    "Rodada beta",
    "Entrevista direta",
    "Outro",
]


PLANOS_TESTADOS = [
    "Beta gratuito com lista de espera",
    "Beta pago individual",
    "Plano mensal básico",
    "Plano mensal premium",
    "Plano anual",
    "Consultoria/mentoria junto ao app",
    "Acesso vitalício inicial",
    "Outro",
]


PERIODICIDADES = [
    "Mensal",
    "Anual",
    "Pagamento único",
    "Gratuito",
    "Ainda não definido",
]


RESPOSTAS_PAGAMENTO = [
    "Pagaria agora",
    "Pagaria depois de melhorias",
    "Talvez pagaria",
    "Não pagaria",
    "Precisa pensar",
    "Não foi perguntado",
]


OBJECOES_PRINCIPAIS = [
    "Preço alto",
    "Ainda não entendeu valor",
    "Precisa de mais confiança",
    "Produto parece incompleto",
    "Já usa outra solução",
    "Não investe com frequência",
    "Medo de recomendação financeira",
    "Falta dados automáticos",
    "Falta visual/profissionalismo",
    "Sem objeção clara",
    "Outra",
]


STATUS_FOLLOWUP = [
    "Não iniciado",
    "Aguardando resposta",
    "Follow-up marcado",
    "Conversa em andamento",
    "Convertido",
    "Perdido",
    "Sem prioridade",
]


PROXIMAS_ACOES = [
    "Enviar link do app",
    "Marcar conversa",
    "Pedir feedback detalhado",
    "Apresentar preço",
    "Enviar proposta beta pago",
    "Colocar na lista de espera",
    "Fazer follow-up",
    "Arquivar por enquanto",
]


DECISOES_COMERCIAIS = [
    "Continuar validando preço",
    "Testar preço menor",
    "Testar preço maior",
    "Criar plano beta pago",
    "Melhorar produto antes de cobrar",
    "Focar em outro perfil",
    "Avançar para pré-venda",
    "Não vender ainda",
]


def _garantir_arquivo_pre_venda() -> None:
    if CAMINHO_PRE_VENDA_BETA.exists():
        return

    with open(CAMINHO_PRE_VENDA_BETA, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_PRE_VENDA)
        escritor.writeheader()


def carregar_pre_vendas_beta() -> List[Dict[str, str]]:
    _garantir_arquivo_pre_venda()

    with open(CAMINHO_PRE_VENDA_BETA, "r", newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        registros = []

        for linha in leitor:
            registro = {campo: linha.get(campo, "") for campo in CAMPOS_PRE_VENDA}
            registros.append(registro)

        return registros


def salvar_pre_vendas_beta(registros: List[Dict[str, Any]]) -> None:
    with open(CAMINHO_PRE_VENDA_BETA, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_PRE_VENDA)
        escritor.writeheader()

        for registro in registros:
            linha = {campo: registro.get(campo, "") for campo in CAMPOS_PRE_VENDA}
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


def adicionar_pre_venda_beta(
    nome_lead: str,
    perfil: str,
    canal_origem: str,
    plano_testado: str,
    preco_apresentado: float,
    periodicidade: str,
    resposta_pagamento: str,
    chance_conversao: int,
    objecao_principal: str,
    valor_percebido: int,
    principal_motivo_interesse: str,
    principal_duvida: str,
    condicao_para_pagar: str,
    status_followup: str,
    proxima_acao: str,
    data_followup: str,
    decisao_comercial: str,
    observacoes: str,
) -> None:
    registros = carregar_pre_vendas_beta()

    novo_registro = {
        "id": str(uuid.uuid4())[:8],
        "data_registro": datetime.now().isoformat(timespec="minutes"),
        "nome_lead": nome_lead.strip(),
        "perfil": perfil,
        "canal_origem": canal_origem,
        "plano_testado": plano_testado,
        "preco_apresentado": str(preco_apresentado),
        "periodicidade": periodicidade,
        "resposta_pagamento": resposta_pagamento,
        "chance_conversao": str(chance_conversao),
        "objeção_principal": objecao_principal,
        "valor_percebido": str(valor_percebido),
        "principal_motivo_interesse": principal_motivo_interesse.strip(),
        "principal_duvida": principal_duvida.strip(),
        "condicao_para_pagar": condicao_para_pagar.strip(),
        "status_followup": status_followup,
        "proxima_acao": proxima_acao,
        "data_followup": data_followup.strip(),
        "decisao_comercial": decisao_comercial,
        "observacoes": observacoes.strip(),
    }

    registros.append(novo_registro)
    salvar_pre_vendas_beta(registros)


def limpar_pre_vendas_beta() -> None:
    salvar_pre_vendas_beta([])


def _contar(registros: List[Dict[str, str]], campo: str, valor: str) -> int:
    return len([registro for registro in registros if registro.get(campo) == valor])


def _taxa(registros: List[Dict[str, str]], campo: str, valor: str) -> float:
    if len(registros) == 0:
        return 0.0

    return (_contar(registros, campo, valor) / len(registros)) * 100


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
        valor = registro.get(campo, "").strip()

        if valor == "":
            continue

        contagem[valor] = contagem.get(valor, 0) + 1

    if len(contagem) == 0:
        return "N/D"

    return max(contagem, key=contagem.get)


def _calcular_receita_potencial(registros: List[Dict[str, str]]) -> float:
    receita = 0.0

    for registro in registros:
        resposta = registro.get("resposta_pagamento", "")
        preco = _safe_float(registro.get("preco_apresentado"))
        chance = _safe_float(registro.get("chance_conversao")) / 100

        if resposta in ["Pagaria agora", "Pagaria depois de melhorias", "Talvez pagaria"]:
            receita += preco * chance

    return receita


def _calcular_score_pre_venda(registros: List[Dict[str, str]]) -> int:
    total = len(registros)

    if total == 0:
        return 0

    taxa_pagaria_agora = _taxa(registros, "resposta_pagamento", "Pagaria agora")
    taxa_pagaria_depois = _taxa(registros, "resposta_pagamento", "Pagaria depois de melhorias")
    taxa_talvez = _taxa(registros, "resposta_pagamento", "Talvez pagaria")
    media_chance = _media_campo(registros, "chance_conversao")
    media_valor = _media_campo(registros, "valor_percebido")

    pontos = 0.0
    pontos += min(total * 7.0, 28)
    pontos += taxa_pagaria_agora * 0.28
    pontos += taxa_pagaria_depois * 0.18
    pontos += taxa_talvez * 0.08
    pontos += media_chance * 0.18
    pontos += media_valor * 2.0

    return int(round(max(0, min(100, pontos))))


def _classificar_pre_venda(score: int, total: int) -> str:
    if total == 0:
        return "Sem validação comercial ainda"

    if score >= 85:
        return "Sinal forte para beta pago"
    if score >= 70:
        return "Boa validação comercial inicial"
    if score >= 55:
        return "Sinal comercial parcial"
    if score >= 40:
        return "Interesse fraco ou indefinido"
    return "Ainda não validado para cobrança"


def _gerar_leitura_pre_venda(score: int, total: int) -> str:
    if total == 0:
        return (
            "Ainda não há conversas de pré-venda registradas. O próximo passo é perguntar diretamente "
            "para alguns usuários se eles pagariam por uma versão melhorada."
        )

    if score >= 85:
        return (
            "Existe sinal forte de monetização. O próximo passo é testar uma oferta beta paga simples, "
            "com poucos usuários e promessa muito clara."
        )

    if score >= 70:
        return (
            "A validação comercial está boa, mas ainda precisa de mais conversas. Teste preço, objeções "
            "e plano antes de construir uma estrutura complexa."
        )

    if score >= 55:
        return (
            "Há interesse, mas ainda não está claro se as pessoas pagariam. Reforce valor percebido, "
            "confiança e clareza antes de cobrar."
        )

    if score >= 40:
        return (
            "O sinal comercial ainda é fraco. Talvez o produto esteja interessante, mas não urgente ou confiável "
            "o suficiente para virar pagamento."
        )

    return (
        "Ainda não há validação suficiente para cobrar. Continue testando utilidade, clareza e confiança."
    )


def _gerar_tabela_pre_vendas(registros: List[Dict[str, str]]) -> List[Dict[str, str]]:
    tabela = []

    for registro in reversed(registros):
        tabela.append(
            {
                "Lead": registro.get("nome_lead", ""),
                "Perfil": registro.get("perfil", ""),
                "Canal": registro.get("canal_origem", ""),
                "Plano": registro.get("plano_testado", ""),
                "Preço": _fmt_moeda(_safe_float(registro.get("preco_apresentado"))),
                "Resposta": registro.get("resposta_pagamento", ""),
                "Chance": f"{registro.get('chance_conversao', '')}%",
                "Valor percebido": f"{registro.get('valor_percebido', '')}/10",
                "Objeção": registro.get("objeção_principal", ""),
                "Follow-up": registro.get("status_followup", ""),
                "Próxima ação": registro.get("proxima_acao", ""),
            }
        )

    return tabela


def _gerar_tabela_objeções(registros: List[Dict[str, str]]) -> List[Dict[str, str]]:
    contagem: Dict[str, int] = {}

    for registro in registros:
        objecao = registro.get("objeção_principal", "N/D")

        if objecao == "":
            objecao = "N/D"

        contagem[objecao] = contagem.get(objecao, 0) + 1

    tabela = []

    for objecao, quantidade in sorted(contagem.items(), key=lambda item: item[1], reverse=True):
        percentual = (quantidade / len(registros)) * 100 if len(registros) > 0 else 0

        tabela.append(
            {
                "Objeção": objecao,
                "Ocorrências": str(quantidade),
                "Peso": _fmt_percentual(percentual),
                "Leitura": _ler_objecao(objecao),
            }
        )

    return tabela


def _ler_objecao(objecao: str) -> str:
    if objecao == "Preço alto":
        return "Teste preço menor ou aumente percepção de valor."
    if objecao == "Ainda não entendeu valor":
        return "Melhore copy, onboarding e demonstração."
    if objecao == "Precisa de mais confiança":
        return "Reforce metodologia, avisos educacionais e transparência."
    if objecao == "Produto parece incompleto":
        return "Mostre roadmap e limite a promessa do beta."
    if objecao == "Falta dados automáticos":
        return "Explique limitações do MVP e planeje integração futura."
    if objecao == "Falta visual/profissionalismo":
        return "Priorize polimento visual e primeira impressão."
    return "Analisar individualmente."


def _gerar_insights_pre_venda(registros: List[Dict[str, str]]) -> List[str]:
    if len(registros) == 0:
        return [
            "Ainda não há conversas comerciais registradas.",
            "Comece perguntando para 5 usuários beta se eles pagariam por uma versão melhorada.",
            "Não esconda a pergunta de preço. Validação real exige falar de dinheiro.",
        ]

    insights = []

    total = len(registros)
    taxa_agora = _taxa(registros, "resposta_pagamento", "Pagaria agora")
    taxa_depois = _taxa(registros, "resposta_pagamento", "Pagaria depois de melhorias")
    taxa_nao = _taxa(registros, "resposta_pagamento", "Não pagaria")
    preco_medio = _media_campo(registros, "preco_apresentado")
    chance_media = _media_campo(registros, "chance_conversao")
    valor_medio = _media_campo(registros, "valor_percebido")
    objecao_mais_comum = _mais_frequente(registros, "objeção_principal")
    perfil_mais_comum = _mais_frequente(registros, "perfil")
    receita_potencial = _calcular_receita_potencial(registros)

    insights.append(f"Você já registrou {total} conversa(s) de pré-venda.")
    insights.append(f"Preço médio apresentado: {_fmt_moeda(preco_medio)}.")
    insights.append(f"Receita potencial ponderada estimada: {_fmt_moeda(receita_potencial)}.")
    insights.append(f"Chance média de conversão: {_fmt_percentual(chance_media)}.")
    insights.append(f"Valor percebido médio: {valor_medio:.1f}/10.")

    if taxa_agora >= 20:
        insights.append("Já existe sinal de pagamento imediato. Considere testar beta pago controlado.")

    if taxa_depois >= 40:
        insights.append("Muitos pagariam depois de melhorias. Use Prioridades Beta e Sprints Beta para remover barreiras.")

    if taxa_nao >= 50:
        insights.append("A taxa de rejeição comercial está alta. Talvez o valor ainda não esteja claro ou o perfil esteja errado.")

    if objecao_mais_comum != "N/D":
        insights.append(f"Objeção mais comum: {objecao_mais_comum}.")

    if perfil_mais_comum != "N/D":
        insights.append(f"Perfil mais presente nas conversas comerciais: {perfil_mais_comum}.")

    insights.append("Pré-venda boa não é convencer a qualquer custo. É descobrir se existe dor forte o suficiente para pagar.")

    return insights


def _gerar_decisoes_comerciais(registros: List[Dict[str, str]]) -> List[Dict[str, str]]:
    if len(registros) == 0:
        return [
            {
                "Decisão": "Iniciar conversas de preço",
                "Critério": "Nenhuma pré-venda registrada.",
                "Ação": "Falar com 5 usuários beta e perguntar se pagariam.",
                "Prioridade": "Muito alta",
            }
        ]

    decisoes = []

    total = len(registros)
    taxa_agora = _taxa(registros, "resposta_pagamento", "Pagaria agora")
    taxa_depois = _taxa(registros, "resposta_pagamento", "Pagaria depois de melhorias")
    taxa_nao = _taxa(registros, "resposta_pagamento", "Não pagaria")
    objecao_mais_comum = _mais_frequente(registros, "objeção_principal")
    valor_medio = _media_campo(registros, "valor_percebido")

    if total < 5:
        decisoes.append(
            {
                "Decisão": "Coletar mais conversas",
                "Critério": "Menos de 5 conversas comerciais.",
                "Ação": "Validar preço com mais usuários antes de decidir.",
                "Prioridade": "Muito alta",
            }
        )

    if taxa_agora >= 20 and total >= 5:
        decisoes.append(
            {
                "Decisão": "Testar beta pago controlado",
                "Critério": "Parte dos leads pagaria agora.",
                "Ação": "Criar uma oferta simples para poucos usuários.",
                "Prioridade": "Alta",
            }
        )

    if taxa_depois >= 40:
        decisoes.append(
            {
                "Decisão": "Remover barreiras antes de cobrar",
                "Critério": "Muitos pagariam após melhorias.",
                "Ação": "Priorizar as objeções mais repetidas nas próximas sprints.",
                "Prioridade": "Alta",
            }
        )

    if objecao_mais_comum == "Ainda não entendeu valor":
        decisoes.append(
            {
                "Decisão": "Melhorar comunicação da oferta",
                "Critério": "Objeção dominante é falta de clareza de valor.",
                "Ação": "Revisar página Produto, Convite Beta e explicação da entrega.",
                "Prioridade": "Alta",
            }
        )

    if objecao_mais_comum == "Precisa de mais confiança":
        decisoes.append(
            {
                "Decisão": "Aumentar confiança",
                "Critério": "Objeção dominante é confiança.",
                "Ação": "Mostrar metodologia, limitações e exemplos de relatório.",
                "Prioridade": "Alta",
            }
        )

    if taxa_nao >= 50 and total >= 5:
        decisoes.append(
            {
                "Decisão": "Revisar perfil-alvo ou proposta",
                "Critério": "Maioria não pagaria.",
                "Ação": "Entender se o problema é público, preço ou valor percebido.",
                "Prioridade": "Alta",
            }
        )

    if valor_medio >= 8 and taxa_agora < 20:
        decisoes.append(
            {
                "Decisão": "Investigar distância entre valor e pagamento",
                "Critério": "Valor percebido alto, mas baixa decisão de pagar agora.",
                "Ação": "Mapear objeções e testar preço menor ou garantia beta.",
                "Prioridade": "Média",
            }
        )

    if len(decisoes) == 0:
        decisoes.append(
            {
                "Decisão": "Continuar validação comercial",
                "Critério": "Dados ainda inconclusivos.",
                "Ação": "Fazer mais conversas e comparar perfis.",
                "Prioridade": "Média",
            }
        )

    return decisoes


def _gerar_script_pre_venda() -> str:
    return """Roteiro simples para conversa de pré-venda:

1. Contexto
"Estou construindo uma ferramenta educacional para ajudar investidores a analisar ativos com mais método."

2. Valor
"Ela organiza valuation, preço-teto, margem de segurança, tese, riscos, checklist, relatório e acompanhamento."

3. Pergunta de uso
"Você usaria algo assim numa análise real?"

4. Pergunta de valor
"Qual parte parece mais útil para você?"

5. Pergunta de pagamento
"Se essa ferramenta estivesse mais polida e com uma experiência melhor, você pagaria por ela?"

6. Teste de preço
"Um preço como R$ 19, R$ 29 ou R$ 49 por mês faria sentido para você?"

7. Objeção
"O que te impediria de pagar?"

8. Fechamento
"Posso te colocar numa lista beta para testar a próxima versão?"
"""


def _gerar_tabela_planos_teste() -> List[Dict[str, str]]:
    return [
        {
            "Plano": "Beta gratuito",
            "Preço teste": "R$ 0",
            "Objetivo": "Gerar uso, feedback e lista de espera.",
            "Quando usar": "Quando o produto ainda precisa de validação básica.",
        },
        {
            "Plano": "Beta pago simbólico",
            "Preço teste": "R$ 9 a R$ 19/mês",
            "Objetivo": "Testar disposição mínima de pagamento.",
            "Quando usar": "Quando há interesse, mas pouca confiança ainda.",
        },
        {
            "Plano": "Plano básico",
            "Preço teste": "R$ 19 a R$ 29/mês",
            "Objetivo": "Validar assinatura acessível.",
            "Quando usar": "Quando usuários entendem valor e usariam mensalmente.",
        },
        {
            "Plano": "Plano premium",
            "Preço teste": "R$ 39 a R$ 79/mês",
            "Objetivo": "Testar valor percebido alto.",
            "Quando usar": "Quando há relatórios, watchlist e melhorias recorrentes.",
        },
        {
            "Plano": "Acesso fundador",
            "Preço teste": "Pagamento único",
            "Objetivo": "Gerar primeiros clientes e caixa inicial.",
            "Quando usar": "Quando há confiança pessoal e proposta limitada.",
        },
    ]


def _gerar_markdown_pre_venda(registros: List[Dict[str, str]]) -> str:
    score = _calcular_score_pre_venda(registros)
    classificacao = _classificar_pre_venda(score, len(registros))
    leitura = _gerar_leitura_pre_venda(score, len(registros))
    receita_potencial = _calcular_receita_potencial(registros)

    linhas_insights = "\n".join([f"- {item}" for item in _gerar_insights_pre_venda(registros)])

    linhas_decisoes = "\n".join(
        [
            f"| {item['Decisão']} | {item['Critério']} | {item['Ação']} | {item['Prioridade']} |"
            for item in _gerar_decisoes_comerciais(registros)
        ]
    )

    return f"""# Pré-venda Beta — Máquina de Preço-Teto

Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Resultado

**Score de pré-venda:** {score}/100  
**Classificação:** {classificacao}  
**Receita potencial ponderada:** {_fmt_moeda(receita_potencial)}

## Leitura

{leitura}

## Indicadores

- Total de conversas: {len(registros)}
- Pagariam agora: {_fmt_percentual(_taxa(registros, "resposta_pagamento", "Pagaria agora"))}
- Pagariam depois de melhorias: {_fmt_percentual(_taxa(registros, "resposta_pagamento", "Pagaria depois de melhorias"))}
- Talvez pagariam: {_fmt_percentual(_taxa(registros, "resposta_pagamento", "Talvez pagaria"))}
- Preço médio apresentado: {_fmt_moeda(_media_campo(registros, "preco_apresentado"))}
- Chance média de conversão: {_fmt_percentual(_media_campo(registros, "chance_conversao"))}
- Objeção mais comum: {_mais_frequente(registros, "objeção_principal")}

## Insights

{linhas_insights}

## Decisões comerciais recomendadas

| Decisão | Critério | Ação | Prioridade |
|---|---|---|---|
{linhas_decisoes}

## Regra

Não criar estrutura complexa de pagamento antes de validar preço, perfil e objeções.
"""


def _injetar_css_pre_venda() -> None:
    st.markdown(
        """
        <style>
            .pv-hero {
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

            .pv-eyebrow {
                color: #d6b56d;
                font-size: 0.78rem;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.35rem;
            }

            .pv-title {
                color: #f4f7fb;
                font-size: 2.1rem;
                font-weight: 900;
                margin-bottom: 0.45rem;
                line-height: 1.14;
            }

            .pv-subtitle {
                color: rgba(244, 247, 251, 0.76);
                font-size: 1rem;
                line-height: 1.62;
                max-width: 1080px;
            }

            .pv-card {
                padding: 1.1rem 1.15rem;
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.035);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.18);
                height: 100%;
            }

            .pv-card-label {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .pv-card-value {
                color: #f4f7fb;
                font-size: 1.22rem;
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .pv-card-note {
                color: rgba(244, 247, 251, 0.68);
                font-size: 0.87rem;
                line-height: 1.47;
            }

            .pv-highlight {
                padding: 0.95rem 1rem;
                border-radius: 16px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.92rem;
                line-height: 1.55;
                margin-bottom: 0.7rem;
            }

            .pv-copy {
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

            .pv-disclaimer {
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
        <div class="pv-card">
            <div class="pv-card-label">{label}</div>
            <div class="pv-card-value">{value}</div>
            <div class="pv-card-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _copy_box(texto: str) -> None:
    st.markdown(
        f"""
        <div class="pv-copy">{texto}</div>
        """,
        unsafe_allow_html=True,
    )


def renderizar_pre_venda_beta() -> None:
    """
    Renderiza a central de pré-venda beta.
    """
    _injetar_css_pre_venda()

    registros = carregar_pre_vendas_beta()

    score = _calcular_score_pre_venda(registros)
    classificacao = _classificar_pre_venda(score, len(registros))
    leitura = _gerar_leitura_pre_venda(score, len(registros))

    total = len(registros)
    taxa_agora = _taxa(registros, "resposta_pagamento", "Pagaria agora")
    taxa_depois = _taxa(registros, "resposta_pagamento", "Pagaria depois de melhorias")
    preco_medio = _media_campo(registros, "preco_apresentado")
    chance_media = _media_campo(registros, "chance_conversao")
    receita_potencial = _calcular_receita_potencial(registros)
    objecao_mais_comum = _mais_frequente(registros, "objeção_principal")

    st.session_state["resultado_pre_venda_beta"] = {
        "score_pre_venda": score,
        "classificacao": classificacao,
        "total_conversas": total,
        "taxa_pagaria_agora": taxa_agora,
        "taxa_pagaria_depois": taxa_depois,
        "preco_medio": preco_medio,
        "chance_media": chance_media,
        "receita_potencial": receita_potencial,
        "objecao_mais_comum": objecao_mais_comum,
    }

    st.markdown(
        """
        <div class="pv-hero">
            <div class="pv-eyebrow">Fase 2.5 — Validação comercial</div>
            <div class="pv-title">Pré-venda Manual e Validação de Pagamento</div>
            <div class="pv-subtitle">
                Teste preço, objeções e intenção real de pagamento antes de criar estrutura complexa.
                A pergunta central é: existe dor forte o suficiente para alguém pagar?
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="pv-highlight">
            Curtida, elogio e “achei legal” não pagam boleto. A validação comercial começa quando você fala de preço.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Diagnóstico da pré-venda")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Score comercial", f"{score}/100")

    with col_2:
        st.metric("Classificação", classificacao)

    with col_3:
        st.metric("Conversas", total)

    with col_4:
        st.metric("Receita potencial", _fmt_moeda(receita_potencial))

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
        _card("Pagariam agora", _fmt_percentual(taxa_agora), "Sinal comercial mais forte.")

    with col_b:
        _card("Pagariam depois", _fmt_percentual(taxa_depois), "Valor existe, mas há barreiras.")

    with col_c:
        _card("Preço médio", _fmt_moeda(preco_medio), "Preço apresentado nas conversas.")

    with col_d:
        _card("Objeção dominante", objecao_mais_comum, "Barreira mais repetida.")

    st.divider()

    st.markdown("### Insights automáticos")

    for insight in _gerar_insights_pre_venda(registros):
        st.markdown(f"- {insight}")

    st.divider()

    st.markdown("### Decisões comerciais recomendadas")

    st.dataframe(
        _gerar_decisoes_comerciais(registros),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Registrar conversa de pré-venda")

    with st.form("form_pre_venda_beta"):
        col_form_1, col_form_2 = st.columns(2)

        with col_form_1:
            nome_lead = st.text_input(
                "Nome ou identificação do lead",
                value="",
                placeholder="Ex: João, Maria, Investidor 01...",
                key="pv_nome_lead",
            )

            perfil = st.selectbox(
                "Perfil do lead",
                PERFIS_LEAD,
                key="pv_perfil",
            )

            canal_origem = st.selectbox(
                "Canal de origem",
                CANAIS_ORIGEM,
                key="pv_canal",
            )

            plano_testado = st.selectbox(
                "Plano testado",
                PLANOS_TESTADOS,
                key="pv_plano",
            )

            preco_apresentado = st.number_input(
                "Preço apresentado",
                min_value=0.0,
                max_value=10000.0,
                value=29.0,
                step=1.0,
                key="pv_preco",
            )

            periodicidade = st.selectbox(
                "Periodicidade",
                PERIODICIDADES,
                key="pv_periodicidade",
            )

        with col_form_2:
            resposta_pagamento = st.selectbox(
                "Resposta sobre pagamento",
                RESPOSTAS_PAGAMENTO,
                key="pv_resposta",
            )

            chance_conversao = st.slider(
                "Chance estimada de conversão",
                0,
                100,
                30,
                key="pv_chance",
            )

            objecao_principal = st.selectbox(
                "Objeção principal",
                OBJECOES_PRINCIPAIS,
                key="pv_objecao",
            )

            valor_percebido = st.slider(
                "Valor percebido pelo lead",
                0,
                10,
                7,
                key="pv_valor_percebido",
            )

            status_followup = st.selectbox(
                "Status do follow-up",
                STATUS_FOLLOWUP,
                key="pv_status_followup",
            )

            proxima_acao = st.selectbox(
                "Próxima ação",
                PROXIMAS_ACOES,
                key="pv_proxima_acao",
            )

        principal_motivo_interesse = st.text_area(
            "Principal motivo de interesse",
            value="",
            height=80,
            placeholder="O que chamou atenção nessa pessoa?",
            key="pv_motivo",
        )

        principal_duvida = st.text_area(
            "Principal dúvida",
            value="",
            height=80,
            placeholder="O que a pessoa ainda não entendeu?",
            key="pv_duvida",
        )

        condicao_para_pagar = st.text_area(
            "Condição para pagar",
            value="",
            height=80,
            placeholder="Ex: pagaria se tivesse dados automáticos, relatório melhor, mais confiança...",
            key="pv_condicao",
        )

        col_final_1, col_final_2 = st.columns(2)

        with col_final_1:
            data_followup = st.text_input(
                "Data de follow-up",
                value="",
                placeholder="Ex: 20/06/2026",
                key="pv_data_followup",
            )

        with col_final_2:
            decisao_comercial = st.selectbox(
                "Decisão comercial",
                DECISOES_COMERCIAIS,
                key="pv_decisao",
            )

        observacoes = st.text_area(
            "Observações",
            value="",
            height=90,
            key="pv_observacoes",
        )

        enviar = st.form_submit_button("Salvar conversa de pré-venda")

        if enviar:
            if nome_lead.strip() == "":
                st.error("Preencha o nome ou identificação do lead.")
            else:
                adicionar_pre_venda_beta(
                    nome_lead=nome_lead,
                    perfil=perfil,
                    canal_origem=canal_origem,
                    plano_testado=plano_testado,
                    preco_apresentado=preco_apresentado,
                    periodicidade=periodicidade,
                    resposta_pagamento=resposta_pagamento,
                    chance_conversao=chance_conversao,
                    objecao_principal=objecao_principal,
                    valor_percebido=valor_percebido,
                    principal_motivo_interesse=principal_motivo_interesse,
                    principal_duvida=principal_duvida,
                    condicao_para_pagar=condicao_para_pagar,
                    status_followup=status_followup,
                    proxima_acao=proxima_acao,
                    data_followup=data_followup,
                    decisao_comercial=decisao_comercial,
                    observacoes=observacoes,
                )

                st.success("Conversa de pré-venda registrada com sucesso.")
                st.rerun()

    st.divider()

    st.markdown("### Conversas registradas")

    registros = carregar_pre_vendas_beta()

    if len(registros) == 0:
        st.info("Nenhuma conversa de pré-venda registrada ainda.")
    else:
        st.dataframe(
            _gerar_tabela_pre_vendas(registros),
            use_container_width=True,
            hide_index=True,
        )

        st.divider()

        st.markdown("### Mapa de objeções")

        st.dataframe(
            _gerar_tabela_objeções(registros),
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    st.markdown("### Script de conversa de pré-venda")

    _copy_box(_gerar_script_pre_venda())

    st.divider()

    st.markdown("### Planos e preços para testar")

    st.dataframe(
        _gerar_tabela_planos_teste(),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    if len(registros) > 0:
        col_download, col_limpar = st.columns(2)

        with col_download:
            with open(CAMINHO_PRE_VENDA_BETA, "rb") as arquivo:
                st.download_button(
                    label="Baixar pré-venda em CSV",
                    data=arquivo,
                    file_name="pre_venda_beta.csv",
                    mime="text/csv",
                    key="download_pre_venda_csv",
                )

            st.download_button(
                label="Baixar relatório de pré-venda (.md)",
                data=_gerar_markdown_pre_venda(registros),
                file_name="relatorio_pre_venda_beta.md",
                mime="text/markdown",
                key="download_pre_venda_md",
            )

        with col_limpar:
            confirmar = st.checkbox(
                "Confirmar limpeza das conversas de pré-venda",
                value=False,
                key="pv_confirmar_limpeza",
            )

            if st.button("Limpar pré-vendas", key="pv_limpar"):
                if confirmar:
                    limpar_pre_vendas_beta()
                    st.success("Conversas de pré-venda limpas com sucesso.")
                    st.rerun()
                else:
                    st.warning("Marque a confirmação antes de limpar.")

    st.markdown(
        """
        <div class="pv-disclaimer">
            <strong>Regra comercial:</strong> antes de criar assinatura, checkout ou estrutura complexa,
            valide manualmente se alguém pagaria, quanto pagaria e por quê.
        </div>
        """,
        unsafe_allow_html=True,
    )