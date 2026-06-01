# crm_beta.py

import csv
import uuid
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List

import streamlit as st


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v2.7 — CRM Beta e Pipeline Comercial Manual
# ------------------------------------------------------------
# Esta tela organiza leads, follow-ups e oportunidades comerciais.
#
# Objetivo:
# - controlar quem recebeu a oferta beta paga
# - acompanhar etapa do funil
# - registrar objeções e próximos passos
# - estimar receita potencial
# - evitar perder leads por falta de follow-up
# ============================================================


CAMINHO_CRM_BETA = Path("crm_beta.csv")


CAMPOS_CRM = [
    "id",
    "data_registro",
    "nome_lead",
    "perfil",
    "canal_origem",
    "oferta_enviada",
    "etapa_funil",
    "temperatura_lead",
    "chance_conversao",
    "valor_potencial",
    "objecao_principal",
    "motivo_interesse",
    "ultima_interacao",
    "proxima_acao",
    "data_followup",
    "status_comercial",
    "observacoes",
]


PERFIS_LEAD = [
    "Investidor iniciante",
    "Investidor intermediário",
    "Investidor avançado",
    "Estudante",
    "Criador de conteúdo financeiro",
    "Pessoa próxima",
    "Lead da lista beta",
    "Outro",
]


CANAIS_ORIGEM = [
    "WhatsApp",
    "Instagram",
    "LinkedIn",
    "E-mail",
    "Indicação",
    "Rodada beta",
    "Pré-venda",
    "Oferta paga",
    "Outro",
]


ETAPAS_FUNIL = [
    "Novo lead",
    "Recebeu convite beta",
    "Testou o app",
    "Respondeu feedback",
    "Recebeu oferta paga",
    "Demonstrou interesse",
    "Em negociação",
    "Convertido",
    "Perdido",
    "Sem prioridade agora",
]


TEMPERATURAS = [
    "Frio",
    "Morno",
    "Quente",
    "Muito quente",
]


OBJECÕES = [
    "Preço",
    "Falta de confiança",
    "Não entendeu valor",
    "Produto incompleto",
    "Falta de tempo",
    "Não investe com frequência",
    "Precisa testar mais",
    "Precisa de dados automáticos",
    "Sem objeção clara",
    "Outro",
]


PROXIMAS_ACOES = [
    "Enviar link do app",
    "Enviar oferta paga",
    "Pedir feedback",
    "Fazer follow-up",
    "Marcar conversa",
    "Enviar exemplo de relatório",
    "Explicar preço-teto",
    "Colocar na lista de espera",
    "Fechar pagamento manual",
    "Arquivar por enquanto",
]


STATUS_COMERCIAL = [
    "Aberto",
    "Aguardando resposta",
    "Follow-up marcado",
    "Negociação ativa",
    "Convertido",
    "Perdido",
    "Pausado",
]


def _garantir_arquivo_crm() -> None:
    if CAMINHO_CRM_BETA.exists():
        return

    with open(CAMINHO_CRM_BETA, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_CRM)
        escritor.writeheader()


def carregar_crm_beta() -> List[Dict[str, str]]:
    _garantir_arquivo_crm()

    with open(CAMINHO_CRM_BETA, "r", newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        registros = []

        for linha in leitor:
            registro = {campo: linha.get(campo, "") for campo in CAMPOS_CRM}
            registros.append(registro)

        return registros


def salvar_crm_beta(registros: List[Dict[str, Any]]) -> None:
    with open(CAMINHO_CRM_BETA, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_CRM)
        escritor.writeheader()

        for registro in registros:
            linha = {campo: registro.get(campo, "") for campo in CAMPOS_CRM}
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


def adicionar_lead_crm(
    nome_lead: str,
    perfil: str,
    canal_origem: str,
    oferta_enviada: str,
    etapa_funil: str,
    temperatura_lead: str,
    chance_conversao: int,
    valor_potencial: float,
    objecao_principal: str,
    motivo_interesse: str,
    ultima_interacao: str,
    proxima_acao: str,
    data_followup: str,
    status_comercial: str,
    observacoes: str,
) -> None:
    registros = carregar_crm_beta()

    novo_registro = {
        "id": str(uuid.uuid4())[:8],
        "data_registro": datetime.now().isoformat(timespec="minutes"),
        "nome_lead": nome_lead.strip(),
        "perfil": perfil,
        "canal_origem": canal_origem,
        "oferta_enviada": oferta_enviada.strip(),
        "etapa_funil": etapa_funil,
        "temperatura_lead": temperatura_lead,
        "chance_conversao": str(chance_conversao),
        "valor_potencial": str(valor_potencial),
        "objecao_principal": objecao_principal,
        "motivo_interesse": motivo_interesse.strip(),
        "ultima_interacao": ultima_interacao.strip(),
        "proxima_acao": proxima_acao,
        "data_followup": data_followup.strip(),
        "status_comercial": status_comercial,
        "observacoes": observacoes.strip(),
    }

    registros.append(novo_registro)
    salvar_crm_beta(registros)


def limpar_crm_beta() -> None:
    salvar_crm_beta([])


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
        valor = registro.get(campo, "").strip()

        if valor == "":
            continue

        contagem[valor] = contagem.get(valor, 0) + 1

    if len(contagem) == 0:
        return "N/D"

    return max(contagem, key=contagem.get)


def _receita_potencial_total(registros: List[Dict[str, str]]) -> float:
    return sum(_safe_float(registro.get("valor_potencial")) for registro in registros)


def _receita_ponderada(registros: List[Dict[str, str]]) -> float:
    total = 0.0

    for registro in registros:
        valor = _safe_float(registro.get("valor_potencial"))
        chance = _safe_float(registro.get("chance_conversao")) / 100
        total += valor * chance

    return total


def _calcular_score_pipeline(registros: List[Dict[str, str]]) -> int:
    total = len(registros)

    if total == 0:
        return 0

    quentes = _contar(registros, "temperatura_lead", "Quente")
    muito_quentes = _contar(registros, "temperatura_lead", "Muito quente")
    convertidos = _contar(registros, "status_comercial", "Convertido")
    negociacao = _contar(registros, "status_comercial", "Negociação ativa")
    followups = _contar(registros, "status_comercial", "Follow-up marcado")
    chance_media = _media_campo(registros, "chance_conversao")

    pontos = 0.0
    pontos += min(total * 5.0, 25)
    pontos += min(quentes * 8.0, 20)
    pontos += min(muito_quentes * 12.0, 24)
    pontos += min(convertidos * 18.0, 30)
    pontos += min(negociacao * 8.0, 16)
    pontos += min(followups * 5.0, 10)
    pontos += chance_media * 0.15

    return int(round(max(0, min(100, pontos))))


def _classificar_pipeline(score: int, total: int) -> str:
    if total == 0:
        return "Sem pipeline comercial"

    if score >= 85:
        return "Pipeline forte"
    if score >= 70:
        return "Pipeline promissor"
    if score >= 55:
        return "Pipeline em formação"
    if score >= 40:
        return "Pipeline fraco"
    return "Pipeline ainda insuficiente"


def _gerar_leitura_pipeline(score: int, total: int) -> str:
    if total == 0:
        return (
            "Ainda não há leads registrados no CRM. O próximo passo é cadastrar as pessoas "
            "que receberam convite, testaram o app ou receberam a oferta paga."
        )

    if score >= 85:
        return (
            "O pipeline está forte. Agora foque em follow-up disciplinado, fechamento manual "
            "e registro das objeções reais."
        )

    if score >= 70:
        return (
            "O pipeline está promissor. Existem leads suficientes para testar conversão manual "
            "sem ainda criar estrutura complexa de vendas."
        )

    if score >= 55:
        return (
            "O pipeline está em formação. Continue alimentando o CRM e priorize leads quentes."
        )

    if score >= 40:
        return (
            "O pipeline ainda está fraco. Talvez faltem leads qualificados, follow-ups ou oferta clara."
        )

    return (
        "Ainda não existe tração comercial suficiente. Volte para convite beta, pré-venda e oferta manual."
    )


def _gerar_tabela_pipeline(registros: List[Dict[str, str]]) -> List[Dict[str, str]]:
    ordem_temperatura = {
        "Muito quente": 4,
        "Quente": 3,
        "Morno": 2,
        "Frio": 1,
    }

    registros_ordenados = sorted(
        registros,
        key=lambda registro: (
            ordem_temperatura.get(registro.get("temperatura_lead", ""), 0),
            _safe_int(registro.get("chance_conversao")),
            _safe_float(registro.get("valor_potencial")),
        ),
        reverse=True,
    )

    tabela = []

    for registro in registros_ordenados:
        tabela.append(
            {
                "Lead": registro.get("nome_lead", ""),
                "Perfil": registro.get("perfil", ""),
                "Canal": registro.get("canal_origem", ""),
                "Etapa": registro.get("etapa_funil", ""),
                "Temperatura": registro.get("temperatura_lead", ""),
                "Chance": f"{registro.get('chance_conversao', '')}%",
                "Valor potencial": _fmt_moeda(_safe_float(registro.get("valor_potencial"))),
                "Status": registro.get("status_comercial", ""),
                "Follow-up": registro.get("data_followup", ""),
                "Próxima ação": registro.get("proxima_acao", ""),
            }
        )

    return tabela


def _gerar_tabela_objeções(registros: List[Dict[str, str]]) -> List[Dict[str, str]]:
    contagem: Dict[str, int] = {}

    for registro in registros:
        objecao = registro.get("objecao_principal", "")

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
                "Ação sugerida": _acao_para_objecao(objecao),
            }
        )

    return tabela


def _acao_para_objecao(objecao: str) -> str:
    if objecao == "Preço":
        return "Testar ancoragem, desconto beta ou plano menor."
    if objecao == "Falta de confiança":
        return "Mostrar metodologia, limitações e exemplos."
    if objecao == "Não entendeu valor":
        return "Melhorar promessa e demonstração da oferta."
    if objecao == "Produto incompleto":
        return "Explicar condição beta e roadmap."
    if objecao == "Precisa testar mais":
        return "Dar acesso e marcar follow-up curto."
    if objecao == "Precisa de dados automáticos":
        return "Explicar MVP atual e futuro das integrações."
    return "Analisar caso a caso."


def _gerar_insights_crm(registros: List[Dict[str, str]]) -> List[str]:
    if len(registros) == 0:
        return [
            "Ainda não há leads no CRM.",
            "Cadastre primeiro as pessoas que testaram o app, responderam feedback ou receberam oferta.",
            "Sem CRM, você perde dinheiro por esquecer follow-up.",
        ]

    insights = []

    total = len(registros)
    quentes = _contar(registros, "temperatura_lead", "Quente")
    muito_quentes = _contar(registros, "temperatura_lead", "Muito quente")
    convertidos = _contar(registros, "status_comercial", "Convertido")
    aguardando = _contar(registros, "status_comercial", "Aguardando resposta")
    negociacao = _contar(registros, "status_comercial", "Negociação ativa")
    receita_total = _receita_potencial_total(registros)
    receita_pond = _receita_ponderada(registros)
    chance_media = _media_campo(registros, "chance_conversao")
    objecao = _mais_frequente(registros, "objecao_principal")
    canal = _mais_frequente(registros, "canal_origem")

    insights.append(f"Existem {total} lead(s) registrados no CRM beta.")
    insights.append(f"Leads quentes ou muito quentes: {quentes + muito_quentes}.")
    insights.append(f"Leads em negociação ativa: {negociacao}.")
    insights.append(f"Leads convertidos: {convertidos}.")
    insights.append(f"Receita potencial total: {_fmt_moeda(receita_total)}.")
    insights.append(f"Receita ponderada por chance de conversão: {_fmt_moeda(receita_pond)}.")
    insights.append(f"Chance média de conversão: {_fmt_percentual(chance_media)}.")

    if aguardando > 0:
        insights.append(f"Há {aguardando} lead(s) aguardando resposta. Faça follow-up com cuidado.")

    if objecao != "N/D":
        insights.append(f"Objeção mais comum no CRM: {objecao}.")

    if canal != "N/D":
        insights.append(f"Canal mais comum de origem: {canal}.")

    insights.append("Pipeline bom não é ter muitos contatos. É ter próximos passos claros para cada lead.")

    return insights


def _gerar_decisoes_crm(registros: List[Dict[str, str]]) -> List[Dict[str, str]]:
    if len(registros) == 0:
        return [
            {
                "Decisão": "Cadastrar primeiros leads",
                "Critério": "Nenhum lead no CRM.",
                "Ação": "Adicionar quem testou, respondeu ou recebeu a oferta.",
                "Prioridade": "Muito alta",
            }
        ]

    decisoes = []

    quentes = _contar(registros, "temperatura_lead", "Quente")
    muito_quentes = _contar(registros, "temperatura_lead", "Muito quente")
    aguardando = _contar(registros, "status_comercial", "Aguardando resposta")
    negociacao = _contar(registros, "status_comercial", "Negociação ativa")
    objecao = _mais_frequente(registros, "objecao_principal")

    if muito_quentes > 0:
        decisoes.append(
            {
                "Decisão": "Priorizar leads muito quentes",
                "Critério": "Há leads com maior chance de conversão.",
                "Ação": "Fazer contato direto e tentar fechamento manual.",
                "Prioridade": "Muito alta",
            }
        )

    if quentes > 0:
        decisoes.append(
            {
                "Decisão": "Trabalhar leads quentes",
                "Critério": "Há leads com interesse relevante.",
                "Ação": "Enviar exemplo, tirar objeção e marcar follow-up.",
                "Prioridade": "Alta",
            }
        )

    if aguardando > 0:
        decisoes.append(
            {
                "Decisão": "Fazer follow-up",
                "Critério": "Existem leads aguardando resposta.",
                "Ação": "Enviar mensagem curta e objetiva sem pressionar.",
                "Prioridade": "Alta",
            }
        )

    if negociacao > 0:
        decisoes.append(
            {
                "Decisão": "Fechar negociação ativa",
                "Critério": "Há leads em negociação.",
                "Ação": "Apresentar condição beta simples e próximo passo claro.",
                "Prioridade": "Alta",
            }
        )

    if objecao == "Não entendeu valor":
        decisoes.append(
            {
                "Decisão": "Melhorar comunicação da oferta",
                "Critério": "Objeção dominante é falta de valor percebido.",
                "Ação": "Revisar promessa, mensagem e exemplo de entrega.",
                "Prioridade": "Alta",
            }
        )

    if len(decisoes) == 0:
        decisoes.append(
            {
                "Decisão": "Manter acompanhamento",
                "Critério": "Pipeline sem alerta crítico.",
                "Ação": "Atualizar status e seguir próximo follow-up.",
                "Prioridade": "Média",
            }
        )

    return decisoes


def _gerar_script_followup() -> str:
    return """Mensagem curta de follow-up:

Oi! Passando só para saber se você conseguiu olhar a Máquina de Preço-Teto.

A ideia é uma ferramenta educacional para organizar valuation, preço-teto, tese, riscos e relatório de análise.

Queria entender de forma bem sincera:
1. Ficou claro o valor da ferramenta?
2. Você usaria numa análise real?
3. O que te impediria de entrar na versão beta paga?

Sem compromisso. Seu feedback já me ajuda muito a ajustar o produto."""


def _gerar_script_fechamento() -> str:
    return """Mensagem curta para lead quente:

Pelo que você comentou, acho que a versão beta paga pode fazer sentido para você.

A proposta é entrar como usuário beta/fundador, testar a ferramenta de perto e me ajudar a ajustar o produto com feedback real.

O foco é educacional: organizar análise, preço-teto, margem de segurança, tese, riscos e relatório.

A condição beta atual é:
[COLOQUE A OFERTA AQUI]

Faz sentido para você entrar nessa primeira versão?"""


def _gerar_markdown_crm(registros: List[Dict[str, str]]) -> str:
    score = _calcular_score_pipeline(registros)
    classificacao = _classificar_pipeline(score, len(registros))
    leitura = _gerar_leitura_pipeline(score, len(registros))

    linhas_pipeline = "\n".join(
        [
            f"| {item['Lead']} | {item['Etapa']} | {item['Temperatura']} | {item['Chance']} | {item['Valor potencial']} | {item['Status']} | {item['Próxima ação']} |"
            for item in _gerar_tabela_pipeline(registros)
        ]
    )

    linhas_insights = "\n".join([f"- {item}" for item in _gerar_insights_crm(registros)])

    linhas_decisoes = "\n".join(
        [
            f"| {item['Decisão']} | {item['Critério']} | {item['Ação']} | {item['Prioridade']} |"
            for item in _gerar_decisoes_crm(registros)
        ]
    )

    return f"""# CRM Beta — Máquina de Preço-Teto

Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Resultado geral

**Score do pipeline:** {score}/100  
**Classificação:** {classificacao}

## Leitura

{leitura}

## Indicadores

- Total de leads: {len(registros)}
- Receita potencial total: {_fmt_moeda(_receita_potencial_total(registros))}
- Receita ponderada: {_fmt_moeda(_receita_ponderada(registros))}
- Chance média de conversão: {_fmt_percentual(_media_campo(registros, "chance_conversao"))}
- Canal mais comum: {_mais_frequente(registros, "canal_origem")}
- Objeção mais comum: {_mais_frequente(registros, "objecao_principal")}

## Pipeline

| Lead | Etapa | Temperatura | Chance | Valor potencial | Status | Próxima ação |
|---|---|---|---:|---:|---|---|
{linhas_pipeline}

## Insights

{linhas_insights}

## Decisões recomendadas

| Decisão | Critério | Ação | Prioridade |
|---|---|---|---|
{linhas_decisoes}

## Regra

Todo lead precisa ter próxima ação clara. Sem follow-up, oportunidade esfria.
"""


def _injetar_css_crm() -> None:
    st.markdown(
        """
        <style>
            .crm-hero {
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

            .crm-eyebrow {
                color: #d6b56d;
                font-size: 0.78rem;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.35rem;
            }

            .crm-title {
                color: #f4f7fb;
                font-size: 2.1rem;
                font-weight: 900;
                margin-bottom: 0.45rem;
                line-height: 1.14;
            }

            .crm-subtitle {
                color: rgba(244, 247, 251, 0.76);
                font-size: 1rem;
                line-height: 1.62;
                max-width: 1080px;
            }

            .crm-card {
                padding: 1.1rem 1.15rem;
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.035);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.18);
                height: 100%;
            }

            .crm-card-label {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .crm-card-value {
                color: #f4f7fb;
                font-size: 1.22rem;
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .crm-card-note {
                color: rgba(244, 247, 251, 0.68);
                font-size: 0.87rem;
                line-height: 1.47;
            }

            .crm-highlight {
                padding: 0.95rem 1rem;
                border-radius: 16px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.92rem;
                line-height: 1.55;
                margin-bottom: 0.7rem;
            }

            .crm-copy {
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

            .crm-disclaimer {
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
        <div class="crm-card">
            <div class="crm-card-label">{label}</div>
            <div class="crm-card-value">{value}</div>
            <div class="crm-card-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _copy_box(texto: str) -> None:
    st.markdown(
        f"""
        <div class="crm-copy">{texto}</div>
        """,
        unsafe_allow_html=True,
    )


def renderizar_crm_beta() -> None:
    """
    Renderiza a central de CRM beta.
    """
    _injetar_css_crm()

    registros = carregar_crm_beta()

    score = _calcular_score_pipeline(registros)
    classificacao = _classificar_pipeline(score, len(registros))
    leitura = _gerar_leitura_pipeline(score, len(registros))

    total = len(registros)
    receita_total = _receita_potencial_total(registros)
    receita_pond = _receita_ponderada(registros)
    chance_media = _media_campo(registros, "chance_conversao")
    quentes = _contar(registros, "temperatura_lead", "Quente")
    muito_quentes = _contar(registros, "temperatura_lead", "Muito quente")

    st.session_state["resultado_crm_beta"] = {
        "score_pipeline": score,
        "classificacao": classificacao,
        "total_leads": total,
        "receita_potencial_total": receita_total,
        "receita_ponderada": receita_pond,
        "chance_media": chance_media,
        "leads_quentes": quentes,
        "leads_muito_quentes": muito_quentes,
    }

    st.markdown(
        """
        <div class="crm-hero">
            <div class="crm-eyebrow">Fase 2.7 — Pipeline comercial</div>
            <div class="crm-title">CRM Beta e Pipeline Comercial Manual</div>
            <div class="crm-subtitle">
                Controle leads, follow-ups, objeções e oportunidades comerciais antes de automatizar vendas.
                Todo lead precisa ter etapa, temperatura e próxima ação clara.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="crm-highlight">
            O dinheiro geralmente está no follow-up. Sem CRM, você esquece leads quentes e perde aprendizado comercial.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Diagnóstico do pipeline")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Score do pipeline", f"{score}/100")

    with col_2:
        st.metric("Classificação", classificacao)

    with col_3:
        st.metric("Leads", total)

    with col_4:
        st.metric("Receita ponderada", _fmt_moeda(receita_pond))

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
        _card("Receita potencial", _fmt_moeda(receita_total), "Soma dos valores potenciais.")

    with col_b:
        _card("Chance média", _fmt_percentual(chance_media), "Média estimada de conversão.")

    with col_c:
        _card("Leads quentes", str(quentes + muito_quentes), "Prioridade de follow-up.")

    with col_d:
        _card("Objeção principal", _mais_frequente(registros, "objecao_principal"), "Barreira mais repetida.")

    st.divider()

    st.markdown("### Insights automáticos")

    for insight in _gerar_insights_crm(registros):
        st.markdown(f"- {insight}")

    st.divider()

    st.markdown("### Decisões recomendadas")

    st.dataframe(
        _gerar_decisoes_crm(registros),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Cadastrar lead no CRM")

    with st.form("form_crm_beta"):
        col_form_1, col_form_2 = st.columns(2)

        with col_form_1:
            nome_lead = st.text_input(
                "Nome ou identificação do lead",
                value="",
                placeholder="Ex: João, Maria, Investidor 01...",
                key="crm_nome_lead",
            )

            perfil = st.selectbox(
                "Perfil",
                PERFIS_LEAD,
                key="crm_perfil",
            )

            canal_origem = st.selectbox(
                "Canal de origem",
                CANAIS_ORIGEM,
                key="crm_canal",
            )

            oferta_enviada = st.text_input(
                "Oferta enviada",
                value="",
                placeholder="Ex: Acesso Fundador — R$ 29/mês",
                key="crm_oferta",
            )

            etapa_funil = st.selectbox(
                "Etapa do funil",
                ETAPAS_FUNIL,
                key="crm_etapa",
            )

        with col_form_2:
            temperatura_lead = st.selectbox(
                "Temperatura do lead",
                TEMPERATURAS,
                index=1,
                key="crm_temperatura",
            )

            chance_conversao = st.slider(
                "Chance de conversão",
                0,
                100,
                30,
                key="crm_chance",
            )

            valor_potencial = st.number_input(
                "Valor potencial",
                min_value=0.0,
                max_value=10000.0,
                value=29.0,
                step=1.0,
                key="crm_valor",
            )

            objecao_principal = st.selectbox(
                "Objeção principal",
                OBJECÕES,
                key="crm_objecao",
            )

            status_comercial = st.selectbox(
                "Status comercial",
                STATUS_COMERCIAL,
                key="crm_status",
            )

        motivo_interesse = st.text_area(
            "Motivo de interesse",
            value="",
            height=80,
            placeholder="O que chamou atenção nesse lead?",
            key="crm_motivo",
        )

        ultima_interacao = st.text_area(
            "Última interação",
            value="",
            height=80,
            placeholder="Resumo da última conversa.",
            key="crm_ultima_interacao",
        )

        col_final_1, col_final_2 = st.columns(2)

        with col_final_1:
            proxima_acao = st.selectbox(
                "Próxima ação",
                PROXIMAS_ACOES,
                key="crm_proxima_acao",
            )

        with col_final_2:
            data_followup = st.text_input(
                "Data de follow-up",
                value="",
                placeholder="Ex: 20/06/2026",
                key="crm_data_followup",
            )

        observacoes = st.text_area(
            "Observações",
            value="",
            height=90,
            key="crm_observacoes",
        )

        enviar = st.form_submit_button("Salvar lead no CRM")

        if enviar:
            if nome_lead.strip() == "":
                st.error("Preencha o nome ou identificação do lead.")
            else:
                adicionar_lead_crm(
                    nome_lead=nome_lead,
                    perfil=perfil,
                    canal_origem=canal_origem,
                    oferta_enviada=oferta_enviada,
                    etapa_funil=etapa_funil,
                    temperatura_lead=temperatura_lead,
                    chance_conversao=chance_conversao,
                    valor_potencial=valor_potencial,
                    objecao_principal=objecao_principal,
                    motivo_interesse=motivo_interesse,
                    ultima_interacao=ultima_interacao,
                    proxima_acao=proxima_acao,
                    data_followup=data_followup,
                    status_comercial=status_comercial,
                    observacoes=observacoes,
                )

                st.success("Lead registrado no CRM com sucesso.")
                st.rerun()

    st.divider()

    st.markdown("### Pipeline de leads")

    registros = carregar_crm_beta()

    if len(registros) == 0:
        st.info("Nenhum lead cadastrado ainda.")
    else:
        st.dataframe(
            _gerar_tabela_pipeline(registros),
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

    st.markdown("### Script de follow-up")

    _copy_box(_gerar_script_followup())

    st.divider()

    st.markdown("### Script para lead quente")

    _copy_box(_gerar_script_fechamento())

    st.divider()

    if len(registros) > 0:
        col_download, col_limpar = st.columns(2)

        with col_download:
            with open(CAMINHO_CRM_BETA, "rb") as arquivo:
                st.download_button(
                    label="Baixar CRM beta em CSV",
                    data=arquivo,
                    file_name="crm_beta.csv",
                    mime="text/csv",
                    key="download_crm_beta_csv",
                )

            st.download_button(
                label="Baixar relatório CRM beta (.md)",
                data=_gerar_markdown_crm(registros),
                file_name="relatorio_crm_beta.md",
                mime="text/markdown",
                key="download_crm_beta_md",
            )

        with col_limpar:
            confirmar = st.checkbox(
                "Confirmar limpeza do CRM beta",
                value=False,
                key="crm_confirmar_limpeza",
            )

            if st.button("Limpar CRM beta", key="crm_limpar"):
                if confirmar:
                    limpar_crm_beta()
                    st.success("CRM limpo com sucesso.")
                    st.rerun()
                else:
                    st.warning("Marque a confirmação antes de limpar.")

    st.markdown(
        """
        <div class="crm-disclaimer">
            <strong>Regra comercial:</strong> todo lead precisa ter próxima ação.
            Lead sem follow-up vira oportunidade perdida.
        </div>
        """,
        unsafe_allow_html=True,
    )