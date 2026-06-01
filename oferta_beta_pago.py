# oferta_beta_pago.py

import csv
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v2.6 — Oferta Beta Paga e Proposta Comercial Manual
# ------------------------------------------------------------
# Esta tela transforma validação comercial em oferta testável.
#
# Objetivo:
# - estruturar uma oferta beta paga simples
# - testar preço, promessa e entrega antes de criar checkout
# - gerar mensagens comerciais manuais
# - comparar versões de oferta
# - evitar vender algo confuso ou amplo demais
# ============================================================


CAMINHO_OFERTAS_BETA_PAGO = Path("ofertas_beta_pago.csv")


CAMPOS_OFERTA = [
    "id",
    "data_registro",
    "nome_oferta",
    "publico_alvo",
    "tipo_plano",
    "preco",
    "periodicidade",
    "promessa_principal",
    "entrega_principal",
    "bonus",
    "garantia_beta",
    "objecao_resolvida",
    "prova_credibilidade",
    "limite_vagas",
    "clareza_promessa",
    "forca_dor",
    "valor_percebido",
    "credibilidade",
    "simplicidade",
    "risco_preco",
    "score_oferta",
    "classificacao",
    "status_oferta",
    "proxima_acao",
    "observacoes",
]


PUBLICOS_ALVO = [
    "Investidor iniciante",
    "Investidor intermediário",
    "Investidor avançado",
    "Estudante interessado em investimentos",
    "Criador de conteúdo financeiro",
    "Pessoas da lista beta",
    "Usuários que disseram que pagariam",
    "Público misto",
]


TIPOS_PLANO = [
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
    "Ainda não definido",
]


STATUS_OFERTA = [
    "Rascunho",
    "Pronta para testar",
    "Em teste manual",
    "Validada",
    "Precisa melhorar",
    "Pausada",
    "Descartada",
]


PROXIMAS_ACOES = [
    "Melhorar promessa",
    "Melhorar entrega",
    "Reduzir preço",
    "Aumentar preço",
    "Testar com 5 leads",
    "Enviar proposta manual",
    "Criar página simples",
    "Criar checkout depois",
    "Aguardar mais pré-venda",
]


def _garantir_arquivo_ofertas() -> None:
    if CAMINHO_OFERTAS_BETA_PAGO.exists():
        return

    with open(CAMINHO_OFERTAS_BETA_PAGO, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_OFERTA)
        escritor.writeheader()


def carregar_ofertas_beta_pago() -> List[Dict[str, str]]:
    _garantir_arquivo_ofertas()

    with open(CAMINHO_OFERTAS_BETA_PAGO, "r", newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        registros = []

        for linha in leitor:
            registro = {campo: linha.get(campo, "") for campo in CAMPOS_OFERTA}
            registros.append(registro)

        return registros


def salvar_ofertas_beta_pago(registros: List[Dict[str, Any]]) -> None:
    with open(CAMINHO_OFERTAS_BETA_PAGO, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_OFERTA)
        escritor.writeheader()

        for registro in registros:
            linha = {campo: registro.get(campo, "") for campo in CAMPOS_OFERTA}
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


def calcular_score_oferta(
    clareza_promessa: int,
    forca_dor: int,
    valor_percebido: int,
    credibilidade: int,
    simplicidade: int,
    risco_preco: int,
) -> int:
    """
    Score de força comercial da oferta.

    Maior clareza, dor, valor, credibilidade e simplicidade aumentam o score.
    Maior risco de preço reduz o score.
    """
    score = (
        clareza_promessa * 2.2
        + forca_dor * 2.0
        + valor_percebido * 2.2
        + credibilidade * 1.7
        + simplicidade * 1.5
        - risco_preco * 1.4
    ) * 5

    return int(round(max(0, min(100, score))))


def classificar_oferta(score: int) -> str:
    if score >= 85:
        return "Oferta muito forte"
    if score >= 70:
        return "Oferta boa para teste manual"
    if score >= 55:
        return "Oferta promissora, mas precisa ajustes"
    if score >= 40:
        return "Oferta fraca ou confusa"
    return "Não testar ainda"


def adicionar_oferta_beta_pago(
    nome_oferta: str,
    publico_alvo: str,
    tipo_plano: str,
    preco: float,
    periodicidade: str,
    promessa_principal: str,
    entrega_principal: str,
    bonus: str,
    garantia_beta: str,
    objecao_resolvida: str,
    prova_credibilidade: str,
    limite_vagas: str,
    clareza_promessa: int,
    forca_dor: int,
    valor_percebido: int,
    credibilidade: int,
    simplicidade: int,
    risco_preco: int,
    status_oferta: str,
    proxima_acao: str,
    observacoes: str,
) -> None:
    registros = carregar_ofertas_beta_pago()

    score = calcular_score_oferta(
        clareza_promessa=clareza_promessa,
        forca_dor=forca_dor,
        valor_percebido=valor_percebido,
        credibilidade=credibilidade,
        simplicidade=simplicidade,
        risco_preco=risco_preco,
    )

    novo_registro = {
        "id": str(uuid.uuid4())[:8],
        "data_registro": datetime.now().isoformat(timespec="minutes"),
        "nome_oferta": nome_oferta.strip(),
        "publico_alvo": publico_alvo,
        "tipo_plano": tipo_plano,
        "preco": str(preco),
        "periodicidade": periodicidade,
        "promessa_principal": promessa_principal.strip(),
        "entrega_principal": entrega_principal.strip(),
        "bonus": bonus.strip(),
        "garantia_beta": garantia_beta.strip(),
        "objecao_resolvida": objecao_resolvida.strip(),
        "prova_credibilidade": prova_credibilidade.strip(),
        "limite_vagas": limite_vagas.strip(),
        "clareza_promessa": str(clareza_promessa),
        "forca_dor": str(forca_dor),
        "valor_percebido": str(valor_percebido),
        "credibilidade": str(credibilidade),
        "simplicidade": str(simplicidade),
        "risco_preco": str(risco_preco),
        "score_oferta": str(score),
        "classificacao": classificar_oferta(score),
        "status_oferta": status_oferta,
        "proxima_acao": proxima_acao,
        "observacoes": observacoes.strip(),
    }

    registros.append(novo_registro)
    salvar_ofertas_beta_pago(registros)


def limpar_ofertas_beta_pago() -> None:
    salvar_ofertas_beta_pago([])


def _ordenar_ofertas(registros: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return sorted(
        registros,
        key=lambda registro: _safe_int(registro.get("score_oferta")),
        reverse=True,
    )


def _media_score(registros: List[Dict[str, str]]) -> float:
    scores = []

    for registro in registros:
        score = _safe_float(registro.get("score_oferta"))

        if score > 0:
            scores.append(score)

    if len(scores) == 0:
        return 0.0

    return sum(scores) / len(scores)


def _preco_medio(registros: List[Dict[str, str]]) -> float:
    precos = []

    for registro in registros:
        preco = _safe_float(registro.get("preco"))

        if preco > 0:
            precos.append(preco)

    if len(precos) == 0:
        return 0.0

    return sum(precos) / len(precos)


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


def _contar_status(registros: List[Dict[str, str]], status: str) -> int:
    return len([registro for registro in registros if registro.get("status_oferta") == status])


def _gerar_tabela_ofertas(registros: List[Dict[str, str]]) -> List[Dict[str, str]]:
    tabela = []

    for registro in _ordenar_ofertas(registros):
        tabela.append(
            {
                "Score": registro.get("score_oferta", ""),
                "Classificação": registro.get("classificacao", ""),
                "Oferta": registro.get("nome_oferta", ""),
                "Público": registro.get("publico_alvo", ""),
                "Plano": registro.get("tipo_plano", ""),
                "Preço": _fmt_moeda(_safe_float(registro.get("preco"))),
                "Periodicidade": registro.get("periodicidade", ""),
                "Status": registro.get("status_oferta", ""),
                "Próxima ação": registro.get("proxima_acao", ""),
            }
        )

    return tabela


def _gerar_tabela_detalhada(registros: List[Dict[str, str]]) -> List[Dict[str, str]]:
    tabela = []

    for registro in _ordenar_ofertas(registros):
        tabela.append(
            {
                "Oferta": registro.get("nome_oferta", ""),
                "Promessa": registro.get("promessa_principal", ""),
                "Entrega": registro.get("entrega_principal", ""),
                "Bônus": registro.get("bonus", ""),
                "Garantia beta": registro.get("garantia_beta", ""),
                "Objeção resolvida": registro.get("objecao_resolvida", ""),
                "Credibilidade": registro.get("prova_credibilidade", ""),
                "Limite/vagas": registro.get("limite_vagas", ""),
            }
        )

    return tabela


def _gerar_mensagem_oferta(registro: Dict[str, str]) -> str:
    nome_oferta = registro.get("nome_oferta", "Oferta Beta")
    promessa = registro.get("promessa_principal", "")
    entrega = registro.get("entrega_principal", "")
    bonus = registro.get("bonus", "")
    garantia = registro.get("garantia_beta", "")
    preco = _fmt_moeda(_safe_float(registro.get("preco")))
    periodicidade = registro.get("periodicidade", "")
    limite = registro.get("limite_vagas", "")

    return f"""Olá! Estou abrindo uma versão beta paga da Máquina de Preço-Teto.

A ideia é simples: {promessa}

O que está incluído:
{entrega}

Bônus/apoio:
{bonus}

Condição beta:
{garantia}

Preço testado:
{preco} — {periodicidade}

{limite}

Não é recomendação de investimento. É uma ferramenta educacional para organizar análise, preço-teto, tese, riscos e relatório.

Faz sentido para você participar dessa versão beta?"""


def _gerar_mensagem_melhor_oferta(registros: List[Dict[str, str]]) -> str:
    if len(registros) == 0:
        return "Nenhuma oferta cadastrada ainda."

    melhor = _ordenar_ofertas(registros)[0]
    return _gerar_mensagem_oferta(melhor)


def _gerar_insights_oferta(registros: List[Dict[str, str]]) -> List[str]:
    if len(registros) == 0:
        return [
            "Ainda não existe oferta beta paga cadastrada.",
            "Crie uma oferta simples antes de pensar em checkout, assinatura ou automação.",
            "A primeira oferta deve ser manual, clara e limitada.",
        ]

    insights = []

    total = len(registros)
    media_score = _media_score(registros)
    preco_medio = _preco_medio(registros)
    melhor = _ordenar_ofertas(registros)[0]
    melhor_score = _safe_int(melhor.get("score_oferta"))
    melhor_nome = melhor.get("nome_oferta", "N/D")
    prontas = _contar_status(registros, "Pronta para testar")
    em_teste = _contar_status(registros, "Em teste manual")
    publico_mais_comum = _mais_frequente(registros, "publico_alvo")

    insights.append(f"Você tem {total} versão(ões) de oferta cadastradas.")
    insights.append(f"Score médio das ofertas: {media_score:.1f}/100.")
    insights.append(f"Preço médio testado: {_fmt_moeda(preco_medio)}.")
    insights.append(f"Melhor oferta atual: {melhor_nome} com score {melhor_score}/100.")

    if prontas > 0:
        insights.append(f"Existem {prontas} oferta(s) prontas para teste manual.")

    if em_teste > 0:
        insights.append(f"Existem {em_teste} oferta(s) em teste manual. Registre as respostas na Pré-venda Beta.")

    if melhor_score >= 70:
        insights.append("Já existe uma oferta boa o suficiente para testar com poucos leads.")

    if melhor_score < 55:
        insights.append("A melhor oferta ainda parece fraca. Melhore promessa, entrega e credibilidade antes de vender.")

    if publico_mais_comum != "N/D":
        insights.append(f"O público mais trabalhado nas ofertas é: {publico_mais_comum}.")

    insights.append("A oferta deve vender uma transformação específica, não uma lista infinita de funções.")

    return insights


def _gerar_decisoes_oferta(registros: List[Dict[str, str]]) -> List[Dict[str, str]]:
    if len(registros) == 0:
        return [
            {
                "Decisão": "Criar primeira oferta beta paga",
                "Critério": "Nenhuma oferta cadastrada.",
                "Ação": "Montar uma oferta simples com preço, entrega e condição beta.",
                "Prioridade": "Muito alta",
            }
        ]

    decisoes = []
    melhor = _ordenar_ofertas(registros)[0]
    melhor_score = _safe_int(melhor.get("score_oferta"))
    nome = melhor.get("nome_oferta", "oferta principal")

    if melhor_score >= 85:
        decisoes.append(
            {
                "Decisão": "Testar oferta imediatamente",
                "Critério": "Oferta com score muito forte.",
                "Ação": f"Enviar a oferta '{nome}' para 5 leads qualificados.",
                "Prioridade": "Muito alta",
            }
        )
    elif melhor_score >= 70:
        decisoes.append(
            {
                "Decisão": "Testar oferta manualmente",
                "Critério": "Oferta boa para teste.",
                "Ação": f"Enviar a oferta '{nome}' para poucos leads e registrar respostas.",
                "Prioridade": "Alta",
            }
        )
    elif melhor_score >= 55:
        decisoes.append(
            {
                "Decisão": "Ajustar antes de vender",
                "Critério": "Oferta promissora, mas ainda com pontos fracos.",
                "Ação": "Melhorar clareza, credibilidade ou condição beta antes do teste.",
                "Prioridade": "Alta",
            }
        )
    else:
        decisoes.append(
            {
                "Decisão": "Não vender ainda",
                "Critério": "Oferta fraca ou confusa.",
                "Ação": "Voltar para Pré-venda Beta e entender melhor objeções.",
                "Prioridade": "Muito alta",
            }
        )

    risco_preco_medio = 0.0
    valores_risco = []

    for registro in registros:
        risco = _safe_float(registro.get("risco_preco"))
        if risco > 0:
            valores_risco.append(risco)

    if len(valores_risco) > 0:
        risco_preco_medio = sum(valores_risco) / len(valores_risco)

    if risco_preco_medio >= 7:
        decisoes.append(
            {
                "Decisão": "Revisar preço ou ancoragem",
                "Critério": "Risco de preço médio alto.",
                "Ação": "Testar preço menor, bônus melhor ou comparação de valor.",
                "Prioridade": "Média",
            }
        )

    return decisoes


def _gerar_checklist_oferta() -> List[Dict[str, str]]:
    return [
        {
            "Item": "Promessa clara",
            "Critério": "A pessoa entende em uma frase o que ganha.",
        },
        {
            "Item": "Entrega objetiva",
            "Critério": "A oferta não parece ampla ou vaga demais.",
        },
        {
            "Item": "Preço visível",
            "Critério": "O lead sabe quanto custa.",
        },
        {
            "Item": "Condição beta honesta",
            "Critério": "A pessoa entende que ainda é uma versão em validação.",
        },
        {
            "Item": "Objeção endereçada",
            "Critério": "A oferta responde uma barreira real da pré-venda.",
        },
        {
            "Item": "Sem promessa de rentabilidade",
            "Critério": "A comunicação deixa claro que é educacional.",
        },
        {
            "Item": "Próximo passo simples",
            "Critério": "A pessoa sabe como responder ou entrar.",
        },
    ]


def _gerar_modelos_oferta() -> List[Dict[str, str]]:
    return [
        {
            "Modelo": "Beta pago simbólico",
            "Preço sugerido": "R$ 9 a R$ 19/mês",
            "Promessa": "Ajudar o usuário a organizar suas primeiras análises com método.",
            "Uso ideal": "Quando ainda há baixa confiança, mas existe interesse.",
        },
        {
            "Modelo": "Plano básico",
            "Preço sugerido": "R$ 19 a R$ 29/mês",
            "Promessa": "Organizar valuation, tese, riscos e relatório em um fluxo simples.",
            "Uso ideal": "Quando usuários já entendem valor e usariam mensalmente.",
        },
        {
            "Modelo": "Plano premium beta",
            "Preço sugerido": "R$ 39 a R$ 79/mês",
            "Promessa": "Apoiar análises mais completas com relatório, watchlist e acompanhamento.",
            "Uso ideal": "Quando há mais confiança e perfil intermediário/avançado.",
        },
        {
            "Modelo": "Acesso fundador",
            "Preço sugerido": "Pagamento único",
            "Promessa": "Entrar cedo, ajudar a construir e manter condição especial.",
            "Uso ideal": "Quando há proximidade, confiança e desejo de participar do projeto.",
        },
    ]


def _gerar_markdown_oferta(registros: List[Dict[str, str]]) -> str:
    linhas_ofertas = "\n".join(
        [
            f"| {item['Score']} | {item['Oferta']} | {item['Público']} | {item['Plano']} | {item['Preço']} | {item['Status']} |"
            for item in _gerar_tabela_ofertas(registros)
        ]
    )

    linhas_insights = "\n".join([f"- {item}" for item in _gerar_insights_oferta(registros)])

    linhas_decisoes = "\n".join(
        [
            f"| {item['Decisão']} | {item['Critério']} | {item['Ação']} | {item['Prioridade']} |"
            for item in _gerar_decisoes_oferta(registros)
        ]
    )

    return f"""# Oferta Beta Paga — Máquina de Preço-Teto

Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Resumo

Total de ofertas: {len(registros)}  
Score médio: {_media_score(registros):.1f}/100  
Preço médio: {_fmt_moeda(_preco_medio(registros))}  
Público mais frequente: {_mais_frequente(registros, "publico_alvo")}

## Ofertas cadastradas

| Score | Oferta | Público | Plano | Preço | Status |
|---:|---|---|---|---:|---|
{linhas_ofertas}

## Insights

{linhas_insights}

## Decisões recomendadas

| Decisão | Critério | Ação | Prioridade |
|---|---|---|---|
{linhas_decisoes}

## Mensagem da melhor oferta

{_gerar_mensagem_melhor_oferta(registros)}

## Regra

Teste a oferta manualmente antes de criar checkout, assinatura ou automação.
"""


def _injetar_css_oferta() -> None:
    st.markdown(
        """
        <style>
            .ofp-hero {
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

            .ofp-eyebrow {
                color: #d6b56d;
                font-size: 0.78rem;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.35rem;
            }

            .ofp-title {
                color: #f4f7fb;
                font-size: 2.1rem;
                font-weight: 900;
                margin-bottom: 0.45rem;
                line-height: 1.14;
            }

            .ofp-subtitle {
                color: rgba(244, 247, 251, 0.76);
                font-size: 1rem;
                line-height: 1.62;
                max-width: 1080px;
            }

            .ofp-card {
                padding: 1.1rem 1.15rem;
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.035);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.18);
                height: 100%;
            }

            .ofp-card-label {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .ofp-card-value {
                color: #f4f7fb;
                font-size: 1.22rem;
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .ofp-card-note {
                color: rgba(244, 247, 251, 0.68);
                font-size: 0.87rem;
                line-height: 1.47;
            }

            .ofp-highlight {
                padding: 0.95rem 1rem;
                border-radius: 16px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.92rem;
                line-height: 1.55;
                margin-bottom: 0.7rem;
            }

            .ofp-copy {
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

            .ofp-disclaimer {
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
        <div class="ofp-card">
            <div class="ofp-card-label">{label}</div>
            <div class="ofp-card-value">{value}</div>
            <div class="ofp-card-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _copy_box(texto: str) -> None:
    st.markdown(
        f"""
        <div class="ofp-copy">{texto}</div>
        """,
        unsafe_allow_html=True,
    )


def renderizar_oferta_beta_pago() -> None:
    """
    Renderiza a central de oferta beta paga.
    """
    _injetar_css_oferta()

    registros = carregar_ofertas_beta_pago()

    total = len(registros)
    media_score = _media_score(registros)
    preco_medio = _preco_medio(registros)
    melhor_oferta = "N/D"

    if total > 0:
        melhor_oferta = _ordenar_ofertas(registros)[0].get("nome_oferta", "N/D")

    st.session_state["resultado_oferta_beta_pago"] = {
        "total_ofertas": total,
        "media_score": media_score,
        "preco_medio": preco_medio,
        "melhor_oferta": melhor_oferta,
    }

    st.markdown(
        """
        <div class="ofp-hero">
            <div class="ofp-eyebrow">Fase 2.6 — Oferta beta paga</div>
            <div class="ofp-title">Oferta Beta Paga e Proposta Comercial Manual</div>
            <div class="ofp-subtitle">
                Estruture uma oferta simples, limitada e testável antes de criar checkout.
                O objetivo é validar promessa, preço e entrega com conversas reais.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="ofp-highlight">
            A oferta beta paga não precisa ser perfeita. Ela precisa ser clara, honesta,
            manualmente vendável e conectada a uma dor real.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Diagnóstico das ofertas")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Ofertas cadastradas", total)

    with col_2:
        st.metric("Score médio", f"{media_score:.1f}/100")

    with col_3:
        st.metric("Preço médio", _fmt_moeda(preco_medio))

    with col_4:
        st.metric("Melhor oferta", melhor_oferta)

    st.divider()

    st.markdown("### Insights automáticos")

    for insight in _gerar_insights_oferta(registros):
        st.markdown(f"- {insight}")

    st.divider()

    st.markdown("### Decisões recomendadas")

    st.dataframe(
        _gerar_decisoes_oferta(registros),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Criar oferta beta paga")

    with st.form("form_oferta_beta_pago"):
        col_form_1, col_form_2 = st.columns(2)

        with col_form_1:
            nome_oferta = st.text_input(
                "Nome da oferta",
                value="Acesso Fundador — Máquina de Preço-Teto",
                key="ofp_nome",
            )

            publico_alvo = st.selectbox(
                "Público-alvo",
                PUBLICOS_ALVO,
                key="ofp_publico",
            )

            tipo_plano = st.selectbox(
                "Tipo de plano",
                TIPOS_PLANO,
                key="ofp_tipo_plano",
            )

            preco = st.number_input(
                "Preço",
                min_value=0.0,
                max_value=10000.0,
                value=29.0,
                step=1.0,
                key="ofp_preco",
            )

            periodicidade = st.selectbox(
                "Periodicidade",
                PERIODICIDADES,
                key="ofp_periodicidade",
            )

        with col_form_2:
            status_oferta = st.selectbox(
                "Status da oferta",
                STATUS_OFERTA,
                key="ofp_status",
            )

            proxima_acao = st.selectbox(
                "Próxima ação",
                PROXIMAS_ACOES,
                key="ofp_proxima_acao",
            )

            limite_vagas = st.text_input(
                "Limite/vagas/condição",
                value="Vagas limitadas para os primeiros usuários beta.",
                key="ofp_limite",
            )

            prova_credibilidade = st.text_area(
                "Prova de credibilidade",
                value="Ferramenta educacional em construção, com valuation, margem de segurança, tese, riscos e relatório.",
                height=100,
                key="ofp_credibilidade_txt",
            )

        promessa_principal = st.text_area(
            "Promessa principal",
            value="Ajudar você a analisar ações com mais método, disciplina e clareza, evitando comprar no impulso.",
            height=90,
            key="ofp_promessa",
        )

        entrega_principal = st.text_area(
            "Entrega principal",
            value=(
                "- Acesso à Máquina de Preço-Teto\n"
                "- Fluxo de valuation educacional\n"
                "- Relatórios em Markdown\n"
                "- Checklist de erros\n"
                "- Watchlist e acompanhamento\n"
                "- Participação no beta com melhorias constantes"
            ),
            height=120,
            key="ofp_entrega",
        )

        bonus = st.text_area(
            "Bônus/apoio",
            value=(
                "- Canal direto para feedback\n"
                "- Possibilidade de influenciar o roadmap\n"
                "- Condição especial de usuário fundador"
            ),
            height=100,
            key="ofp_bonus",
        )

        garantia_beta = st.text_area(
            "Garantia ou condição beta",
            value=(
                "Essa é uma versão beta. O objetivo é testar e melhorar junto com os primeiros usuários. "
                "A ferramenta é educacional e não faz recomendação de investimento."
            ),
            height=90,
            key="ofp_garantia",
        )

        objecao_resolvida = st.text_area(
            "Objeção principal que a oferta resolve",
            value="Ajuda quem se sente perdido ao analisar ações e quer organizar premissas, riscos e preço-teto.",
            height=90,
            key="ofp_objecao",
        )

        st.markdown("#### Avaliação da força da oferta")

        col_score_1, col_score_2, col_score_3 = st.columns(3)

        with col_score_1:
            clareza_promessa = st.slider(
                "Clareza da promessa",
                1,
                10,
                8,
                key="ofp_clareza",
            )

            forca_dor = st.slider(
                "Força da dor",
                1,
                10,
                7,
                key="ofp_dor",
            )

        with col_score_2:
            valor_percebido = st.slider(
                "Valor percebido",
                1,
                10,
                7,
                key="ofp_valor",
            )

            credibilidade = st.slider(
                "Credibilidade",
                1,
                10,
                7,
                key="ofp_credibilidade",
            )

        with col_score_3:
            simplicidade = st.slider(
                "Simplicidade",
                1,
                10,
                7,
                key="ofp_simplicidade",
            )

            risco_preco = st.slider(
                "Risco de preço",
                1,
                10,
                4,
                help="Quanto maior, mais chance do preço travar a venda.",
                key="ofp_risco_preco",
            )

        score_preview = calcular_score_oferta(
            clareza_promessa=clareza_promessa,
            forca_dor=forca_dor,
            valor_percebido=valor_percebido,
            credibilidade=credibilidade,
            simplicidade=simplicidade,
            risco_preco=risco_preco,
        )

        st.info(
            f"Score da oferta: **{score_preview}/100** — {classificar_oferta(score_preview)}"
        )

        observacoes = st.text_area(
            "Observações",
            value="",
            height=80,
            key="ofp_observacoes",
        )

        enviar = st.form_submit_button("Salvar oferta beta paga")

        if enviar:
            if nome_oferta.strip() == "":
                st.error("Preencha o nome da oferta.")
            elif promessa_principal.strip() == "":
                st.error("Preencha a promessa principal.")
            elif entrega_principal.strip() == "":
                st.error("Preencha a entrega principal.")
            else:
                adicionar_oferta_beta_pago(
                    nome_oferta=nome_oferta,
                    publico_alvo=publico_alvo,
                    tipo_plano=tipo_plano,
                    preco=preco,
                    periodicidade=periodicidade,
                    promessa_principal=promessa_principal,
                    entrega_principal=entrega_principal,
                    bonus=bonus,
                    garantia_beta=garantia_beta,
                    objecao_resolvida=objecao_resolvida,
                    prova_credibilidade=prova_credibilidade,
                    limite_vagas=limite_vagas,
                    clareza_promessa=clareza_promessa,
                    forca_dor=forca_dor,
                    valor_percebido=valor_percebido,
                    credibilidade=credibilidade,
                    simplicidade=simplicidade,
                    risco_preco=risco_preco,
                    status_oferta=status_oferta,
                    proxima_acao=proxima_acao,
                    observacoes=observacoes,
                )

                st.success("Oferta beta paga registrada com sucesso.")
                st.rerun()

    st.divider()

    st.markdown("### Ofertas cadastradas")

    registros = carregar_ofertas_beta_pago()

    if len(registros) == 0:
        st.info("Nenhuma oferta beta paga cadastrada ainda.")
    else:
        st.dataframe(
            _gerar_tabela_ofertas(registros),
            use_container_width=True,
            hide_index=True,
        )

        st.divider()

        st.markdown("### Detalhamento das ofertas")

        st.dataframe(
            _gerar_tabela_detalhada(registros),
            use_container_width=True,
            hide_index=True,
        )

        st.divider()

        st.markdown("### Mensagem pronta da melhor oferta")

        _copy_box(_gerar_mensagem_melhor_oferta(registros))

    st.divider()

    st.markdown("### Checklist de oferta beta paga")

    st.dataframe(
        _gerar_checklist_oferta(),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Modelos de oferta para testar")

    st.dataframe(
        _gerar_modelos_oferta(),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    if len(registros) > 0:
        col_download, col_limpar = st.columns(2)

        with col_download:
            with open(CAMINHO_OFERTAS_BETA_PAGO, "rb") as arquivo:
                st.download_button(
                    label="Baixar ofertas beta paga em CSV",
                    data=arquivo,
                    file_name="ofertas_beta_pago.csv",
                    mime="text/csv",
                    key="download_ofertas_beta_pago_csv",
                )

            st.download_button(
                label="Baixar relatório de oferta beta paga (.md)",
                data=_gerar_markdown_oferta(registros),
                file_name="relatorio_oferta_beta_pago.md",
                mime="text/markdown",
                key="download_oferta_beta_pago_md",
            )

        with col_limpar:
            confirmar = st.checkbox(
                "Confirmar limpeza das ofertas beta paga",
                value=False,
                key="ofp_confirmar_limpeza",
            )

            if st.button("Limpar ofertas beta paga", key="ofp_limpar"):
                if confirmar:
                    limpar_ofertas_beta_pago()
                    st.success("Ofertas limpas com sucesso.")
                    st.rerun()
                else:
                    st.warning("Marque a confirmação antes de limpar.")

    st.markdown(
        """
        <div class="ofp-disclaimer">
            <strong>Regra comercial:</strong> teste a oferta manualmente com poucos leads antes de criar checkout.
            Se ninguém aceita no manual, automatizar só vai acelerar uma oferta fraca.
        </div>
        """,
        unsafe_allow_html=True,
    )