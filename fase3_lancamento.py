# fase3_lancamento.py

import csv
import uuid
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List

import streamlit as st


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v2.9 — Plano da Fase 3 e Lançamento Beta Pago Controlado
# ------------------------------------------------------------
# Esta tela transforma a decisão do Painel Beta em plano prático.
#
# Objetivo:
# - organizar a preparação da Fase 3
# - controlar itens críticos antes do beta pago
# - evitar criar checkout/automação antes da validação manual
# - definir critérios mínimos para vender com segurança
# - transformar sinais da Fase 2 em um roteiro de lançamento
# ============================================================


CAMINHO_FASE3 = Path("fase3_lancamento.csv")

ARQUIVOS_FASE_2 = {
    "aprendizado_beta": Path("aprendizado_beta_real.csv"),
    "rodadas_beta": Path("rodadas_beta.csv"),
    "prioridades_beta": Path("priorizacao_feedback_beta.csv"),
    "sprints_beta": Path("sprints_beta.csv"),
    "pre_venda_beta": Path("pre_venda_beta.csv"),
    "oferta_paga": Path("ofertas_beta_pago.csv"),
    "crm_beta": Path("crm_beta.csv"),
}

CAMPOS_FASE3 = [
    "id",
    "data_registro",
    "nome_item",
    "categoria",
    "prioridade",
    "status",
    "objetivo",
    "criterio_sucesso",
    "responsavel",
    "prazo",
    "risco_principal",
    "proxima_acao",
    "observacoes",
]

CATEGORIAS = [
    "Produto",
    "Oferta",
    "Pagamento",
    "Onboarding",
    "Suporte",
    "Conteúdo",
    "Legal/Educacional",
    "Operação",
    "Métricas",
    "Dados/Backups",
    "Marketing",
    "Outro",
]

PRIORIDADES = [
    "Crítica",
    "Alta",
    "Média",
    "Baixa",
]

STATUS = [
    "Não iniciado",
    "Planejado",
    "Em execução",
    "Pronto",
    "Validado",
    "Bloqueado",
    "Descartado",
]

PROXIMAS_ACOES = [
    "Definir melhor",
    "Criar tarefa técnica",
    "Executar agora",
    "Testar manualmente",
    "Validar com usuários",
    "Aguardar mais dados",
    "Corrigir antes de lançar",
    "Marcar como pronto",
    "Descartar por enquanto",
]


def _garantir_arquivo_fase3() -> None:
    if CAMINHO_FASE3.exists():
        return

    with open(CAMINHO_FASE3, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_FASE3)
        escritor.writeheader()


def carregar_itens_fase3() -> List[Dict[str, str]]:
    _garantir_arquivo_fase3()

    with open(CAMINHO_FASE3, "r", newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        registros = []

        for linha in leitor:
            registro = {campo: linha.get(campo, "") for campo in CAMPOS_FASE3}
            registros.append(registro)

        return registros


def salvar_itens_fase3(registros: List[Dict[str, Any]]) -> None:
    with open(CAMINHO_FASE3, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_FASE3)
        escritor.writeheader()

        for registro in registros:
            linha = {campo: registro.get(campo, "") for campo in CAMPOS_FASE3}
            escritor.writerow(linha)


def adicionar_item_fase3(
    nome_item: str,
    categoria: str,
    prioridade: str,
    status: str,
    objetivo: str,
    criterio_sucesso: str,
    responsavel: str,
    prazo: str,
    risco_principal: str,
    proxima_acao: str,
    observacoes: str,
) -> None:
    registros = carregar_itens_fase3()

    novo_registro = {
        "id": str(uuid.uuid4())[:8],
        "data_registro": datetime.now().isoformat(timespec="minutes"),
        "nome_item": nome_item.strip(),
        "categoria": categoria,
        "prioridade": prioridade,
        "status": status,
        "objetivo": objetivo.strip(),
        "criterio_sucesso": criterio_sucesso.strip(),
        "responsavel": responsavel.strip(),
        "prazo": prazo.strip(),
        "risco_principal": risco_principal.strip(),
        "proxima_acao": proxima_acao,
        "observacoes": observacoes.strip(),
    }

    registros.append(novo_registro)
    salvar_itens_fase3(registros)


def limpar_itens_fase3() -> None:
    salvar_itens_fase3([])


def _carregar_csv(caminho: Path) -> List[Dict[str, str]]:
    if not caminho.exists():
        return []

    try:
        with open(caminho, "r", newline="", encoding="utf-8") as arquivo:
            leitor = csv.DictReader(arquivo)
            return [dict(linha) for linha in leitor]
    except Exception:
        return []


def _carregar_dados_fase2() -> Dict[str, List[Dict[str, str]]]:
    return {
        nome: _carregar_csv(caminho)
        for nome, caminho in ARQUIVOS_FASE_2.items()
    }


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


def _media(registros: List[Dict[str, str]], campo: str) -> float:
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


def _receita_ponderada_crm(registros_crm: List[Dict[str, str]]) -> float:
    total = 0.0

    for registro in registros_crm:
        valor = _safe_float(registro.get("valor_potencial"))
        chance = _safe_float(registro.get("chance_conversao")) / 100
        total += valor * chance

    return total


def _receita_ponderada_pre_venda(registros_pre_venda: List[Dict[str, str]]) -> float:
    total = 0.0

    for registro in registros_pre_venda:
        resposta = registro.get("resposta_pagamento", "")
        preco = _safe_float(registro.get("preco_apresentado"))
        chance = _safe_float(registro.get("chance_conversao")) / 100

        if resposta in ["Pagaria agora", "Pagaria depois de melhorias", "Talvez pagaria"]:
            total += preco * chance

    return total


def _calcular_score_sinal_fase2(dados: Dict[str, List[Dict[str, str]]]) -> int:
    aprendizado = dados["aprendizado_beta"]
    pre_venda = dados["pre_venda_beta"]
    ofertas = dados["oferta_paga"]
    crm = dados["crm_beta"]
    sprints = dados["sprints_beta"]

    testes = len(aprendizado)
    conversas_pre_venda = len(pre_venda)
    pagaria_agora = _contar(pre_venda, "resposta_pagamento", "Pagaria agora")
    ofertas_boas = len(
        [oferta for oferta in ofertas if _safe_int(oferta.get("score_oferta")) >= 70]
    )
    leads_quentes = _contar(crm, "temperatura_lead", "Quente") + _contar(
        crm,
        "temperatura_lead",
        "Muito quente",
    )
    sprints_concluidas = _contar(sprints, "status_sprint", "Concluída")

    pontos = 0.0
    pontos += min(testes * 5.0, 25)
    pontos += min(conversas_pre_venda * 5.0, 25)
    pontos += min(pagaria_agora * 12.0, 24)
    pontos += min(ofertas_boas * 10.0, 20)
    pontos += min(leads_quentes * 8.0, 24)
    pontos += min(sprints_concluidas * 8.0, 16)

    return int(round(max(0, min(100, pontos))))


def _score_preparacao_fase3(itens: List[Dict[str, str]]) -> int:
    if len(itens) == 0:
        return 0

    pesos_prioridade = {
        "Crítica": 1.4,
        "Alta": 1.2,
        "Média": 1.0,
        "Baixa": 0.7,
    }

    pesos_status = {
        "Não iniciado": 0,
        "Planejado": 20,
        "Em execução": 45,
        "Pronto": 75,
        "Validado": 100,
        "Bloqueado": 5,
        "Descartado": 0,
    }

    pontos = []

    for item in itens:
        prioridade = item.get("prioridade", "Média")
        status = item.get("status", "Não iniciado")

        peso = pesos_prioridade.get(prioridade, 1.0)
        valor = pesos_status.get(status, 0)
        pontos.append(valor * peso)

    if len(pontos) == 0:
        return 0

    score = sum(pontos) / (len(pontos) * 1.4)

    return int(round(max(0, min(100, score))))


def _classificar_preparacao(score: int) -> str:
    if score >= 85:
        return "Pronto para beta pago controlado"
    if score >= 70:
        return "Preparação forte"
    if score >= 55:
        return "Preparação em andamento"
    if score >= 40:
        return "Preparação incompleta"
    return "Ainda cedo para Fase 3"


def _decisao_fase3(score_sinal: int, score_preparacao: int, itens: List[Dict[str, str]]) -> str:
    bloqueados = _contar(itens, "status", "Bloqueado")
    criticos_pendentes = len(
        [
            item for item in itens
            if item.get("prioridade") == "Crítica"
            and item.get("status") not in ["Pronto", "Validado", "Descartado"]
        ]
    )

    if bloqueados > 0:
        return "Resolver bloqueios antes de avançar"

    if criticos_pendentes > 0:
        return "Concluir itens críticos antes do beta pago"

    if score_sinal >= 70 and score_preparacao >= 70:
        return "Testar beta pago controlado com poucos usuários"

    if score_sinal >= 70 and score_preparacao < 70:
        return "Há sinal comercial; preparar operação antes de vender"

    if score_sinal < 70 and score_preparacao >= 70:
        return "Operação preparada; buscar mais sinal comercial antes de vender"

    if score_sinal >= 55 or score_preparacao >= 55:
        return "Continuar preparação e validação manual"

    return "Não avançar ainda; fortalecer Fase 2"


def _gerar_itens_iniciais_sugeridos() -> List[Dict[str, str]]:
    return [
        {
            "Item": "Definir oferta beta paga principal",
            "Categoria": "Oferta",
            "Prioridade": "Crítica",
            "Critério de sucesso": "Uma frase clara de promessa, entrega, preço e condição beta.",
        },
        {
            "Item": "Criar fluxo manual de pagamento",
            "Categoria": "Pagamento",
            "Prioridade": "Crítica",
            "Critério de sucesso": "Forma simples e segura para receber dos primeiros usuários.",
        },
        {
            "Item": "Criar onboarding dos pagantes",
            "Categoria": "Onboarding",
            "Prioridade": "Alta",
            "Critério de sucesso": "Usuário sabe o que fazer nos primeiros 5 minutos.",
        },
        {
            "Item": "Criar aviso educacional/compliance simples",
            "Categoria": "Legal/Educacional",
            "Prioridade": "Crítica",
            "Critério de sucesso": "Deixar claro que a ferramenta não recomenda compra ou venda.",
        },
        {
            "Item": "Definir rotina de suporte e feedback",
            "Categoria": "Suporte",
            "Prioridade": "Alta",
            "Critério de sucesso": "Todo usuário beta pago sabe por onde enviar dúvidas e feedback.",
        },
        {
            "Item": "Definir métricas mínimas da Fase 3",
            "Categoria": "Métricas",
            "Prioridade": "Alta",
            "Critério de sucesso": "Acompanhar usuários pagantes, conversão, retenção, reclamações e feedback.",
        },
    ]


def _gerar_tabela_itens(itens: List[Dict[str, str]]) -> List[Dict[str, str]]:
    ordem_prioridade = {
        "Crítica": 4,
        "Alta": 3,
        "Média": 2,
        "Baixa": 1,
    }

    ordem_status = {
        "Bloqueado": 7,
        "Não iniciado": 6,
        "Planejado": 5,
        "Em execução": 4,
        "Pronto": 3,
        "Validado": 2,
        "Descartado": 1,
    }

    itens_ordenados = sorted(
        itens,
        key=lambda item: (
            ordem_prioridade.get(item.get("prioridade", ""), 0),
            ordem_status.get(item.get("status", ""), 0),
        ),
        reverse=True,
    )

    tabela = []

    for item in itens_ordenados:
        tabela.append(
            {
                "Item": item.get("nome_item", ""),
                "Categoria": item.get("categoria", ""),
                "Prioridade": item.get("prioridade", ""),
                "Status": item.get("status", ""),
                "Prazo": item.get("prazo", ""),
                "Responsável": item.get("responsavel", ""),
                "Próxima ação": item.get("proxima_acao", ""),
                "Critério de sucesso": item.get("criterio_sucesso", ""),
            }
        )

    return tabela


def _gerar_tabela_riscos(itens: List[Dict[str, str]]) -> List[Dict[str, str]]:
    tabela = []

    for item in itens:
        risco = item.get("risco_principal", "").strip()

        if risco == "":
            continue

        tabela.append(
            {
                "Item": item.get("nome_item", ""),
                "Prioridade": item.get("prioridade", ""),
                "Status": item.get("status", ""),
                "Risco principal": risco,
                "Ação sugerida": _acao_para_risco(item),
            }
        )

    return tabela


def _acao_para_risco(item: Dict[str, str]) -> str:
    status = item.get("status", "")
    prioridade = item.get("prioridade", "")

    if status == "Bloqueado":
        return "Resolver antes de qualquer venda."

    if prioridade == "Crítica" and status not in ["Pronto", "Validado"]:
        return "Executar antes de abrir beta pago."

    if status == "Em execução":
        return "Definir prazo curto e critério de conclusão."

    return "Monitorar e revisar antes do lançamento."


def _gerar_insights(
    dados_fase2: Dict[str, List[Dict[str, str]]],
    itens: List[Dict[str, str]],
    score_sinal: int,
    score_preparacao: int,
) -> List[str]:
    insights = []

    pre_venda = dados_fase2["pre_venda_beta"]
    ofertas = dados_fase2["oferta_paga"]
    crm = dados_fase2["crm_beta"]

    receita = _receita_ponderada_pre_venda(pre_venda) + _receita_ponderada_crm(crm)
    pagaria_agora = _contar(pre_venda, "resposta_pagamento", "Pagaria agora")
    leads_quentes = _contar(crm, "temperatura_lead", "Quente") + _contar(
        crm,
        "temperatura_lead",
        "Muito quente",
    )
    ofertas_boas = len(
        [oferta for oferta in ofertas if _safe_int(oferta.get("score_oferta")) >= 70]
    )
    prontos = _contar(itens, "status", "Pronto") + _contar(itens, "status", "Validado")
    bloqueados = _contar(itens, "status", "Bloqueado")

    insights.append(f"Score de sinal da Fase 2: {score_sinal}/100.")
    insights.append(f"Score de preparação da Fase 3: {score_preparacao}/100.")
    insights.append(f"Receita ponderada estimada pela Fase 2: {_fmt_moeda(receita)}.")
    insights.append(f"Leads quentes/muito quentes no CRM: {leads_quentes}.")
    insights.append(f"Pessoas que disseram que pagariam agora: {pagaria_agora}.")
    insights.append(f"Ofertas com score igual ou acima de 70: {ofertas_boas}.")
    insights.append(f"Itens de preparação prontos ou validados: {prontos}.")

    if bloqueados > 0:
        insights.append(f"Existem {bloqueados} item(ns) bloqueado(s). Eles devem ser resolvidos antes de vender.")

    if score_sinal >= 70 and score_preparacao < 70:
        insights.append("O mercado começa a sinalizar interesse, mas a operação ainda não está pronta.")

    if score_sinal < 70 and score_preparacao >= 70:
        insights.append("A operação está ficando pronta, mas ainda falta sinal comercial suficiente.")

    if len(itens) == 0:
        insights.append("Nenhum item de Fase 3 foi registrado. Comece pelos itens críticos sugeridos.")

    insights.append("A Fase 3 deve ser um beta pago controlado, não um lançamento grande e irreversível.")

    return insights


def _gerar_acoes_recomendadas(
    dados_fase2: Dict[str, List[Dict[str, str]]],
    itens: List[Dict[str, str]],
    score_sinal: int,
    score_preparacao: int,
) -> List[Dict[str, str]]:
    acoes = []

    pre_venda = dados_fase2["pre_venda_beta"]
    ofertas = dados_fase2["oferta_paga"]
    crm = dados_fase2["crm_beta"]

    itens_criticos_pendentes = len(
        [
            item for item in itens
            if item.get("prioridade") == "Crítica"
            and item.get("status") not in ["Pronto", "Validado", "Descartado"]
        ]
    )

    if len(itens) == 0:
        acoes.append(
            {
                "Prioridade": "Muito alta",
                "Ação": "Cadastrar itens críticos da Fase 3",
                "Motivo": "Sem checklist operacional, a venda pode virar improviso.",
            }
        )

    if itens_criticos_pendentes > 0:
        acoes.append(
            {
                "Prioridade": "Muito alta",
                "Ação": "Finalizar itens críticos pendentes",
                "Motivo": "Itens críticos seguram pagamento, suporte, oferta ou risco educacional.",
            }
        )

    if len(ofertas) == 0:
        acoes.append(
            {
                "Prioridade": "Muito alta",
                "Ação": "Criar oferta paga principal",
                "Motivo": "Não há Fase 3 comercial sem oferta clara.",
            }
        )

    if len(pre_venda) < 5:
        acoes.append(
            {
                "Prioridade": "Alta",
                "Ação": "Fazer pelo menos 5 conversas de pré-venda",
                "Motivo": "A decisão de venda precisa de sinal real de preço.",
            }
        )

    if len(crm) < 5:
        acoes.append(
            {
                "Prioridade": "Alta",
                "Ação": "Cadastrar e qualificar leads no CRM",
                "Motivo": "O beta pago controlado precisa de poucos leads bons, não audiência gigante.",
            }
        )

    if score_sinal >= 70 and score_preparacao >= 70:
        acoes.append(
            {
                "Prioridade": "Alta",
                "Ação": "Selecionar 3 a 5 leads para oferta manual",
                "Motivo": "Já existe sinal e preparação suficientes para um teste pequeno.",
            }
        )

    if len(acoes) == 0:
        acoes.append(
            {
                "Prioridade": "Média",
                "Ação": "Manter ciclo de venda manual controlada",
                "Motivo": "A fase está pronta para testes pequenos e aprendizado contínuo.",
            }
        )

    return acoes


def _gerar_roteiro_fase3() -> List[Dict[str, str]]:
    return [
        {
            "Etapa": "1",
            "Nome": "Preparar oferta e condição beta",
            "Resultado esperado": "Uma oferta simples, limitada e sem promessa financeira.",
        },
        {
            "Etapa": "2",
            "Nome": "Selecionar poucos leads qualificados",
            "Resultado esperado": "3 a 5 pessoas com sinal real de interesse.",
        },
        {
            "Etapa": "3",
            "Nome": "Vender manualmente",
            "Resultado esperado": "Testar pagamento sem construir automação complexa.",
        },
        {
            "Etapa": "4",
            "Nome": "Onboardar usuários pagantes",
            "Resultado esperado": "Usuário entende como usar e onde pedir suporte.",
        },
        {
            "Etapa": "5",
            "Nome": "Medir uso e reclamações",
            "Resultado esperado": "Saber se a entrega realmente sustenta o preço.",
        },
        {
            "Etapa": "6",
            "Nome": "Decidir se escala ou corrige",
            "Resultado esperado": "Aumentar vendas apenas se o beta pago for validado.",
        },
    ]


def _gerar_checklist_go_no_go() -> List[Dict[str, str]]:
    return [
        {
            "Critério": "Oferta clara",
            "Go": "Usuário entende promessa, preço e entrega.",
            "No-Go": "Oferta depende de muita explicação.",
        },
        {
            "Critério": "Aviso educacional",
            "Go": "Fica claro que não é recomendação de investimento.",
            "No-Go": "Comunicação pode parecer promessa de ganho.",
        },
        {
            "Critério": "Pagamento manual simples",
            "Go": "Forma de cobrança definida e segura.",
            "No-Go": "Ainda não há forma prática de receber.",
        },
        {
            "Critério": "Suporte mínimo",
            "Go": "Canal e rotina de resposta definidos.",
            "No-Go": "Usuário pagante não sabe com quem falar.",
        },
        {
            "Critério": "Leads qualificados",
            "Go": "Há poucos leads quentes no CRM.",
            "No-Go": "Não há com quem testar venda.",
        },
        {
            "Critério": "Métrica de sucesso",
            "Go": "Você sabe o que observar após a venda.",
            "No-Go": "Vende e não sabe como medir se deu certo.",
        },
    ]


def _gerar_markdown_fase3(
    dados_fase2: Dict[str, List[Dict[str, str]]],
    itens: List[Dict[str, str]],
    score_sinal: int,
    score_preparacao: int,
) -> str:
    classificacao = _classificar_preparacao(score_preparacao)
    decisao = _decisao_fase3(score_sinal, score_preparacao, itens)
    receita = _receita_ponderada_pre_venda(dados_fase2["pre_venda_beta"]) + _receita_ponderada_crm(dados_fase2["crm_beta"])

    linhas_itens = "\n".join(
        [
            f"| {item['Item']} | {item['Categoria']} | {item['Prioridade']} | {item['Status']} | {item['Próxima ação']} |"
            for item in _gerar_tabela_itens(itens)
        ]
    )

    linhas_acoes = "\n".join(
        [
            f"| {acao['Prioridade']} | {acao['Ação']} | {acao['Motivo']} |"
            for acao in _gerar_acoes_recomendadas(dados_fase2, itens, score_sinal, score_preparacao)
        ]
    )

    linhas_roteiro = "\n".join(
        [
            f"| {etapa['Etapa']} | {etapa['Nome']} | {etapa['Resultado esperado']} |"
            for etapa in _gerar_roteiro_fase3()
        ]
    )

    linhas_insights = "\n".join(
        [
            f"- {insight}"
            for insight in _gerar_insights(dados_fase2, itens, score_sinal, score_preparacao)
        ]
    )

    return f"""# Plano da Fase 3 — Máquina de Preço-Teto

Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Diagnóstico

**Score de sinal da Fase 2:** {score_sinal}/100  
**Score de preparação da Fase 3:** {score_preparacao}/100  
**Classificação:** {classificacao}  
**Decisão recomendada:** {decisao}  
**Receita ponderada estimada:** {_fmt_moeda(receita)}

## Insights

{linhas_insights}

## Itens de preparação

| Item | Categoria | Prioridade | Status | Próxima ação |
|---|---|---|---|---|
{linhas_itens}

## Próximas ações

| Prioridade | Ação | Motivo |
|---|---|---|
{linhas_acoes}

## Roteiro da Fase 3

| Etapa | Nome | Resultado esperado |
|---:|---|---|
{linhas_roteiro}

## Regra

A Fase 3 deve começar como beta pago controlado, manual e pequeno. Só automatize depois de validar venda, entrega e suporte.
"""


def _injetar_css_fase3() -> None:
    st.markdown(
        """
        <style>
            .f3-hero {
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

            .f3-eyebrow {
                color: #d6b56d;
                font-size: 0.78rem;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.35rem;
            }

            .f3-title {
                color: #f4f7fb;
                font-size: 2.1rem;
                font-weight: 900;
                margin-bottom: 0.45rem;
                line-height: 1.14;
            }

            .f3-subtitle {
                color: rgba(244, 247, 251, 0.76);
                font-size: 1rem;
                line-height: 1.62;
                max-width: 1080px;
            }

            .f3-card {
                padding: 1.1rem 1.15rem;
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.035);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.18);
                height: 100%;
            }

            .f3-card-label {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .f3-card-value {
                color: #f4f7fb;
                font-size: 1.22rem;
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .f3-card-note {
                color: rgba(244, 247, 251, 0.68);
                font-size: 0.87rem;
                line-height: 1.47;
            }

            .f3-highlight {
                padding: 0.95rem 1rem;
                border-radius: 16px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.92rem;
                line-height: 1.55;
                margin-bottom: 0.7rem;
            }

            .f3-disclaimer {
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
        <div class="f3-card">
            <div class="f3-card-label">{label}</div>
            <div class="f3-card-value">{value}</div>
            <div class="f3-card-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def renderizar_fase3_lancamento() -> None:
    """
    Renderiza o plano de preparação da Fase 3.
    """
    _injetar_css_fase3()

    dados_fase2 = _carregar_dados_fase2()
    itens = carregar_itens_fase3()

    score_sinal = _calcular_score_sinal_fase2(dados_fase2)
    score_preparacao = _score_preparacao_fase3(itens)
    classificacao = _classificar_preparacao(score_preparacao)
    decisao = _decisao_fase3(score_sinal, score_preparacao, itens)

    receita = _receita_ponderada_pre_venda(dados_fase2["pre_venda_beta"]) + _receita_ponderada_crm(dados_fase2["crm_beta"])
    itens_prontos = _contar(itens, "status", "Pronto") + _contar(itens, "status", "Validado")
    itens_bloqueados = _contar(itens, "status", "Bloqueado")

    st.session_state["resultado_fase3_lancamento"] = {
        "score_sinal_fase2": score_sinal,
        "score_preparacao_fase3": score_preparacao,
        "classificacao": classificacao,
        "decisao": decisao,
        "receita_ponderada": receita,
        "itens_prontos": itens_prontos,
        "itens_bloqueados": itens_bloqueados,
    }

    st.markdown(
        """
        <div class="f3-hero">
            <div class="f3-eyebrow">Fase 2.9 — Preparação para Fase 3</div>
            <div class="f3-title">Plano da Fase 3 e Lançamento Beta Pago Controlado</div>
            <div class="f3-subtitle">
                Transforme os sinais da Fase 2 em um plano prático para vender manualmente,
                onboardar poucos usuários pagantes e validar monetização sem escalar cedo demais.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="f3-highlight">
            A Fase 3 não é “lançar grande”. É vender pequeno, manualmente, medir a entrega e corrigir antes de automatizar.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Diagnóstico de avanço")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Sinal da Fase 2", f"{score_sinal}/100")

    with col_2:
        st.metric("Preparação Fase 3", f"{score_preparacao}/100")

    with col_3:
        st.metric("Classificação", classificacao)

    with col_4:
        st.metric("Receita ponderada", _fmt_moeda(receita))

    st.progress(score_preparacao / 100)

    if score_sinal >= 70 and score_preparacao >= 70:
        st.success(decisao)
    elif score_sinal >= 55 or score_preparacao >= 55:
        st.warning(decisao)
    else:
        st.error(decisao)

    st.divider()

    st.markdown("### Indicadores operacionais")

    col_a, col_b, col_c, col_d = st.columns(4)

    with col_a:
        _card("Itens Fase 3", str(len(itens)), "Checklist operacional registrado.")

    with col_b:
        _card("Prontos/validados", str(itens_prontos), "Itens liberados para lançamento.")

    with col_c:
        _card("Bloqueados", str(itens_bloqueados), "Devem ser resolvidos antes de vender.")

    with col_d:
        _card("Categoria dominante", _mais_frequente(itens, "categoria"), "Área com mais preparo registrado.")

    st.divider()

    st.markdown("### Insights automáticos")

    for insight in _gerar_insights(dados_fase2, itens, score_sinal, score_preparacao):
        st.markdown(f"- {insight}")

    st.divider()

    st.markdown("### Próximas ações recomendadas")

    st.dataframe(
        _gerar_acoes_recomendadas(dados_fase2, itens, score_sinal, score_preparacao),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Registrar item da Fase 3")

    with st.form("form_fase3_lancamento"):
        col_form_1, col_form_2 = st.columns(2)

        with col_form_1:
            nome_item = st.text_input(
                "Nome do item",
                value="Definir oferta beta paga principal",
                key="f3_nome_item",
            )

            categoria = st.selectbox(
                "Categoria",
                CATEGORIAS,
                key="f3_categoria",
            )

            prioridade = st.selectbox(
                "Prioridade",
                PRIORIDADES,
                key="f3_prioridade",
            )

            status = st.selectbox(
                "Status",
                STATUS,
                key="f3_status",
            )

        with col_form_2:
            responsavel = st.text_input(
                "Responsável",
                value="Leo",
                key="f3_responsavel",
            )

            prazo = st.text_input(
                "Prazo",
                value="",
                placeholder="Ex: hoje, esta semana, antes da v3.0...",
                key="f3_prazo",
            )

            proxima_acao = st.selectbox(
                "Próxima ação",
                PROXIMAS_ACOES,
                key="f3_proxima_acao",
            )

        objetivo = st.text_area(
            "Objetivo",
            value="Preparar uma condição beta paga simples, clara e vendável manualmente.",
            height=85,
            key="f3_objetivo",
        )

        criterio_sucesso = st.text_area(
            "Critério de sucesso",
            value="Oferta entendida em menos de 30 segundos, com preço, entrega e condição beta claros.",
            height=85,
            key="f3_criterio",
        )

        risco_principal = st.text_area(
            "Risco principal",
            value="Oferta ficar confusa, ampla demais ou parecer recomendação financeira.",
            height=85,
            key="f3_risco",
        )

        observacoes = st.text_area(
            "Observações",
            value="",
            height=80,
            key="f3_observacoes",
        )

        enviar = st.form_submit_button("Salvar item da Fase 3")

        if enviar:
            if nome_item.strip() == "":
                st.error("Preencha o nome do item.")
            elif objetivo.strip() == "":
                st.error("Preencha o objetivo.")
            elif criterio_sucesso.strip() == "":
                st.error("Preencha o critério de sucesso.")
            else:
                adicionar_item_fase3(
                    nome_item=nome_item,
                    categoria=categoria,
                    prioridade=prioridade,
                    status=status,
                    objetivo=objetivo,
                    criterio_sucesso=criterio_sucesso,
                    responsavel=responsavel,
                    prazo=prazo,
                    risco_principal=risco_principal,
                    proxima_acao=proxima_acao,
                    observacoes=observacoes,
                )

                st.success("Item da Fase 3 registrado com sucesso.")
                st.rerun()

    st.divider()

    st.markdown("### Itens registrados da Fase 3")

    itens = carregar_itens_fase3()

    if len(itens) == 0:
        st.info("Nenhum item da Fase 3 registrado ainda. Use a tabela de sugestões abaixo para começar.")
    else:
        st.dataframe(
            _gerar_tabela_itens(itens),
            use_container_width=True,
            hide_index=True,
        )

        riscos = _gerar_tabela_riscos(itens)

        if len(riscos) > 0:
            st.divider()
            st.markdown("### Mapa de riscos da Fase 3")
            st.dataframe(
                riscos,
                use_container_width=True,
                hide_index=True,
            )

    st.divider()

    st.markdown("### Itens críticos sugeridos")

    st.dataframe(
        _gerar_itens_iniciais_sugeridos(),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Roteiro de execução da Fase 3")

    st.dataframe(
        _gerar_roteiro_fase3(),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Checklist Go/No-Go")

    st.dataframe(
        _gerar_checklist_go_no_go(),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    if len(itens) > 0:
        col_download, col_limpar = st.columns(2)

        with col_download:
            with open(CAMINHO_FASE3, "rb") as arquivo:
                st.download_button(
                    label="Baixar plano da Fase 3 em CSV",
                    data=arquivo,
                    file_name="fase3_lancamento.csv",
                    mime="text/csv",
                    key="download_fase3_csv",
                )

            st.download_button(
                label="Baixar relatório da Fase 3 (.md)",
                data=_gerar_markdown_fase3(dados_fase2, itens, score_sinal, score_preparacao),
                file_name="relatorio_fase3_lancamento.md",
                mime="text/markdown",
                key="download_fase3_md",
            )

        with col_limpar:
            confirmar = st.checkbox(
                "Confirmar limpeza dos itens da Fase 3",
                value=False,
                key="f3_confirmar_limpeza",
            )

            if st.button("Limpar plano da Fase 3", key="f3_limpar"):
                if confirmar:
                    limpar_itens_fase3()
                    st.success("Itens da Fase 3 limpos com sucesso.")
                    st.rerun()
                else:
                    st.warning("Marque a confirmação antes de limpar.")

    st.markdown(
        """
        <div class="f3-disclaimer">
            <strong>Regra de Fase 3:</strong> vender pequeno, entregar bem e medir com frieza.
            Só crie checkout, assinatura e automação depois que a venda manual provar que a oferta sustenta pagamento.
        </div>
        """,
        unsafe_allow_html=True,
    )