# oferta_beta_pago.py

import csv
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st


# ============================================================
# VALORIS
# v3.8.40 — Oferta Beta Paga e Teste Manual
# ------------------------------------------------------------
# Esta tela transforma a oferta Beta Fundador em um experimento
# comercial controlado.
#
# Objetivo:
# - cadastrar versões de oferta
# - calcular score comercial
# - gerar mensagem manual de venda
# - decidir se a oferta está pronta para testar
# - evitar checkout antes de validação real
# ============================================================


VERSAO_OFERTA_BETA_PAGO = "3.8.40"

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
    "Pessoas da lista beta",
    "Usuários que disseram que pagariam",
    "Investidor iniciante",
    "Investidor intermediário",
    "Investidor avançado",
    "Estudante interessado em investimentos",
    "Criador de conteúdo financeiro",
    "Público misto",
]


TIPOS_PLANO = [
    "Acesso fundador",
    "Beta pago mensal",
    "Pagamento único beta",
    "Plano básico",
    "Plano premium",
    "Relatório premium avulso",
    "Outro",
]


PERIODICIDADES = [
    "Pagamento único",
    "Mensal",
    "Trimestral",
    "Anual",
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
    "Testar com 5 leads",
    "Enviar proposta manual",
    "Melhorar promessa",
    "Melhorar entrega",
    "Reduzir preço",
    "Aumentar preço",
    "Criar página simples",
    "Criar checkout depois",
    "Aguardar mais lista de espera",
]


def _garantir_arquivo_ofertas() -> None:
    if CAMINHO_OFERTAS_BETA_PAGO.exists():
        return

    with CAMINHO_OFERTAS_BETA_PAGO.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_OFERTA)
        escritor.writeheader()


def carregar_ofertas_beta_pago() -> List[Dict[str, str]]:
    _garantir_arquivo_ofertas()

    with CAMINHO_OFERTAS_BETA_PAGO.open("r", newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        return [{campo: linha.get(campo, "") for campo in CAMPOS_OFERTA} for linha in leitor]


def salvar_ofertas_beta_pago(registros: List[Dict[str, Any]]) -> None:
    with CAMINHO_OFERTAS_BETA_PAGO.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_OFERTA)
        escritor.writeheader()

        for registro in registros:
            escritor.writerow({campo: registro.get(campo, "") for campo in CAMPOS_OFERTA})


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
    scores = [_safe_float(registro.get("score_oferta")) for registro in registros]
    scores = [score for score in scores if score > 0]

    if not scores:
        return 0.0

    return sum(scores) / len(scores)


def _preco_medio(registros: List[Dict[str, str]]) -> float:
    precos = [_safe_float(registro.get("preco")) for registro in registros]
    precos = [preco for preco in precos if preco > 0]

    if not precos:
        return 0.0

    return sum(precos) / len(precos)


def _gerar_mensagem_oferta(registro: Dict[str, str]) -> str:
    nome_oferta = registro.get("nome_oferta", "Valoris Beta Fundador")
    promessa = registro.get("promessa_principal", "")
    entrega = registro.get("entrega_principal", "")
    bonus = registro.get("bonus", "")
    garantia = registro.get("garantia_beta", "")
    preco = _fmt_moeda(_safe_float(registro.get("preco")))
    periodicidade = registro.get("periodicidade", "")
    limite = registro.get("limite_vagas", "")

    return f"""Olá! Estou abrindo uma versão beta paga da Valoris.

Oferta: {nome_oferta}

A ideia é simples:
{promessa}

O que está incluído:
{entrega}

Bônus/apoio:
{bonus}

Condição beta:
{garantia}

Preço testado:
{preco} — {periodicidade}

{limite}

Importante: a Valoris é educacional. Não é recomendação de investimento e não promete rentabilidade.

Faz sentido para você participar dessa versão beta?"""


def _gerar_mensagem_melhor_oferta(registros: List[Dict[str, str]]) -> str:
    if not registros:
        return "Nenhuma oferta cadastrada ainda."

    melhor = _ordenar_ofertas(registros)[0]
    return _gerar_mensagem_oferta(melhor)


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


def _gerar_insights_oferta(registros: List[Dict[str, str]]) -> List[str]:
    if not registros:
        return [
            "Ainda não existe oferta beta paga cadastrada.",
            "Crie uma oferta simples antes de pensar em checkout, assinatura ou automação.",
            "A primeira oferta deve ser manual, clara, limitada e honesta.",
        ]

    melhor = _ordenar_ofertas(registros)[0]
    melhor_score = _safe_int(melhor.get("score_oferta"))
    melhor_nome = melhor.get("nome_oferta", "N/D")

    insights = [
        f"Você tem {len(registros)} versão(ões) de oferta cadastradas.",
        f"Score médio das ofertas: {_media_score(registros):.1f}/100.",
        f"Preço médio testado: {_fmt_moeda(_preco_medio(registros))}.",
        f"Melhor oferta atual: {melhor_nome} com score {melhor_score}/100.",
    ]

    if melhor_score >= 70:
        insights.append("Já existe uma oferta boa o suficiente para testar manualmente com poucos leads.")
    else:
        insights.append("A melhor oferta ainda precisa melhorar antes de ser enviada para muitos leads.")

    insights.append("A oferta deve vender uma transformação específica, não uma lista infinita de funções.")

    return insights


def _gerar_decisoes_oferta(registros: List[Dict[str, str]]) -> List[Dict[str, str]]:
    if not registros:
        return [
            {
                "Decisão": "Criar primeira oferta beta paga",
                "Critério": "Nenhuma oferta cadastrada.",
                "Ação": "Montar uma oferta simples com preço, entrega e condição beta.",
                "Prioridade": "Muito alta",
            }
        ]

    melhor = _ordenar_ofertas(registros)[0]
    melhor_score = _safe_int(melhor.get("score_oferta"))
    nome = melhor.get("nome_oferta", "oferta principal")

    if melhor_score >= 85:
        return [
            {
                "Decisão": "Testar imediatamente",
                "Critério": "Oferta com score muito forte.",
                "Ação": f"Enviar a oferta '{nome}' para 5 leads qualificados.",
                "Prioridade": "Muito alta",
            }
        ]

    if melhor_score >= 70:
        return [
            {
                "Decisão": "Testar manualmente",
                "Critério": "Oferta boa para teste.",
                "Ação": f"Enviar a oferta '{nome}' para poucos leads e registrar respostas.",
                "Prioridade": "Alta",
            }
        ]

    if melhor_score >= 55:
        return [
            {
                "Decisão": "Ajustar antes de vender",
                "Critério": "Oferta promissora, mas ainda com pontos fracos.",
                "Ação": "Melhorar clareza, credibilidade ou condição beta antes do teste.",
                "Prioridade": "Alta",
            }
        ]

    return [
        {
            "Decisão": "Não vender ainda",
            "Critério": "Oferta fraca ou confusa.",
            "Ação": "Voltar para a lista de espera e entender melhor objeções.",
            "Prioridade": "Muito alta",
        }
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

    return f"""# Oferta Beta Paga — Valoris

Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Resumo

Total de ofertas: {len(registros)}  
Score médio: {_media_score(registros):.1f}/100  
Preço médio: {_fmt_moeda(_preco_medio(registros))}

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


def _injetar_css_oferta_pago() -> None:
    st.markdown(
        """
        <style>
            .ofp-hero {
                padding: clamp(1.25rem, 3vw, 1.9rem);
                border-radius: 30px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    radial-gradient(circle at top left, rgba(214, 181, 109, 0.22), transparent 30%),
                    radial-gradient(circle at bottom right, rgba(74, 144, 226, 0.20), transparent 34%),
                    linear-gradient(135deg, rgba(8, 15, 27, 0.98), rgba(5, 9, 18, 0.98));
                box-shadow: 0 18px 55px rgba(0, 0, 0, 0.30);
                margin-bottom: 1rem;
            }

            .ofp-eyebrow {
                color: #d6b56d;
                font-size: 0.74rem;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.38rem;
            }

            .ofp-title {
                color: #f4f7fb;
                font-size: clamp(1.65rem, 4vw, 2.25rem);
                font-weight: 920;
                margin-bottom: 0.55rem;
                line-height: 1.08;
                letter-spacing: -0.045em;
            }

            .ofp-subtitle {
                color: rgba(244, 247, 251, 0.76);
                font-size: 0.98rem;
                line-height: 1.56;
                max-width: 980px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _renderizar_metricas(registros: List[Dict[str, str]]) -> None:
    col_1, col_2, col_3 = st.columns(3)

    with col_1:
        st.metric("Ofertas", len(registros))

    with col_2:
        st.metric("Score médio", f"{_media_score(registros):.1f}/100")

    with col_3:
        st.metric("Preço médio", _fmt_moeda(_preco_medio(registros)))


def _renderizar_formulario_oferta() -> None:
    st.markdown("### Criar ou testar uma oferta")

    with st.form("form_oferta_beta_pago"):
        col_1, col_2 = st.columns(2)

        with col_1:
            nome_oferta = st.text_input(
                "Nome da oferta",
                value="Valoris Beta Fundador",
                key="ofp_nome_oferta",
            )

            publico_alvo = st.selectbox(
                "Público-alvo",
                PUBLICOS_ALVO,
                key="ofp_publico_alvo",
            )

            tipo_plano = st.selectbox(
                "Tipo de plano",
                TIPOS_PLANO,
                key="ofp_tipo_plano",
            )

            preco = st.number_input(
                "Preço testado",
                min_value=0.0,
                value=97.0,
                step=10.0,
                key="ofp_preco",
            )

            periodicidade = st.selectbox(
                "Periodicidade",
                PERIODICIDADES,
                key="ofp_periodicidade",
            )

        with col_2:
            status_oferta = st.selectbox(
                "Status da oferta",
                STATUS_OFERTA,
                index=1,
                key="ofp_status",
            )

            proxima_acao = st.selectbox(
                "Próxima ação",
                PROXIMAS_ACOES,
                key="ofp_proxima_acao",
            )

            limite_vagas = st.text_input(
                "Limite/vagas",
                value="Primeiras 10 vagas beta.",
                key="ofp_limite_vagas",
            )

            prova_credibilidade = st.text_input(
                "Prova de credibilidade",
                value="Produto já está online, com feedback real e relatório premium.",
                key="ofp_prova",
            )

        promessa_principal = st.text_area(
            "Promessa principal",
            value=(
                "Ajudar investidores a auditar decisões antes de comprar ações, com valuation, "
                "margem de segurança, relatório e revisão de riscos."
            ),
            height=90,
            key="ofp_promessa",
        )

        entrega_principal = st.text_area(
            "Entrega principal",
            value=(
                "- acesso à plataforma beta;\n"
                "- Auditor Valoris;\n"
                "- Relatório Valoris Premium;\n"
                "- camadas leigo, intermediário e avançado;\n"
                "- participação nas melhorias do produto."
            ),
            height=120,
            key="ofp_entrega",
        )

        bonus = st.text_area(
            "Bônus/apoio",
            value="Canal direto para enviar feedback e sugerir melhorias prioritárias.",
            height=80,
            key="ofp_bonus",
        )

        garantia_beta = st.text_area(
            "Condição/garantia beta",
            value=(
                "Produto em evolução. O usuário entende que está entrando cedo e ajudando a construir. "
                "Se não fizer sentido após testar, a oferta pode ser pausada ou ajustada manualmente."
            ),
            height=95,
            key="ofp_garantia",
        )

        objecao_resolvida = st.text_area(
            "Objeção resolvida",
            value=(
                "Não é uma promessa de lucro: é uma ferramenta para organizar raciocínio, premissas e riscos."
            ),
            height=80,
            key="ofp_objecao",
        )

        st.markdown("#### Score comercial da oferta")

        col_s1, col_s2, col_s3 = st.columns(3)

        with col_s1:
            clareza_promessa = st.slider("Clareza da promessa", 1, 10, 8, key="ofp_clareza")
            forca_dor = st.slider("Força da dor", 1, 10, 8, key="ofp_dor")

        with col_s2:
            valor_percebido = st.slider("Valor percebido", 1, 10, 8, key="ofp_valor")
            credibilidade = st.slider("Credibilidade", 1, 10, 7, key="ofp_credibilidade")

        with col_s3:
            simplicidade = st.slider("Simplicidade", 1, 10, 8, key="ofp_simplicidade")
            risco_preco = st.slider("Risco de preço", 1, 10, 4, key="ofp_risco")

        observacoes = st.text_area(
            "Observações",
            value="",
            height=80,
            key="ofp_observacoes",
        )

        enviado = st.form_submit_button("Salvar oferta beta paga")

        if enviado:
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

            st.success("Oferta cadastrada com sucesso.")
            st.rerun()


def renderizar_oferta_beta_pago() -> None:
    """
    Renderiza a página de oferta beta paga.
    """
    _injetar_css_oferta_pago()

    registros = carregar_ofertas_beta_pago()

    st.markdown(
        f"""
        <div class="ofp-hero">
            <div class="ofp-eyebrow">Valoris • v{VERSAO_OFERTA_BETA_PAGO}</div>
            <div class="ofp-title">Oferta Beta Paga</div>
            <div class="ofp-subtitle">
                Estruture a primeira oferta monetizável antes de criar checkout. O objetivo é testar
                promessa, preço, entrega e objeções com poucos leads qualificados.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _renderizar_metricas(registros)

    st.divider()

    for insight in _gerar_insights_oferta(registros):
        st.info(insight)

    st.divider()

    st.markdown("### Decisão recomendada")

    for decisao in _gerar_decisoes_oferta(registros):
        with st.container(border=True):
            st.markdown(f"**{decisao['Decisão']}**")
            st.caption(f"Critério: {decisao['Critério']}")
            st.markdown(f"**Ação:** {decisao['Ação']}")
            st.markdown(f"**Prioridade:** {decisao['Prioridade']}")

    st.divider()

    _renderizar_formulario_oferta()

    st.divider()

    st.markdown("### Ofertas cadastradas")

    if not registros:
        st.info("Nenhuma oferta cadastrada ainda.")
    else:
        for item in _gerar_tabela_ofertas(registros):
            with st.container(border=True):
                st.markdown(f"**{item['Oferta']}** — {item['Classificação']}")
                st.caption(
                    f"Score: {item['Score']} • Público: {item['Público']} • Plano: {item['Plano']} • Preço: {item['Preço']}"
                )
                st.markdown(f"**Status:** {item['Status']}")
                st.markdown(f"**Próxima ação:** {item['Próxima ação']}")

    st.divider()

    st.markdown("### Mensagem da melhor oferta")

    st.text_area(
        "Copie e envie manualmente",
        value=_gerar_mensagem_melhor_oferta(registros),
        height=300,
        key="ofp_mensagem_melhor_oferta",
    )

    st.download_button(
        label="Baixar relatório de ofertas (.md)",
        data=_gerar_markdown_oferta(registros),
        file_name="oferta_beta_paga_valoris.md",
        mime="text/markdown",
        key="ofp_download_markdown",
    )

    st.download_button(
        label="Baixar ofertas cadastradas (.csv)",
        data=CAMINHO_OFERTAS_BETA_PAGO.read_text(encoding="utf-8") if CAMINHO_OFERTAS_BETA_PAGO.exists() else "",
        file_name="ofertas_beta_pago.csv",
        mime="text/csv",
        key="ofp_download_csv",
    )

    st.warning(
        "Não crie checkout ainda. Primeiro teste manualmente com poucos leads e registre respostas reais."
    )


def executar_autoteste_oferta_beta_pago() -> List[Dict[str, str]]:
    score = calcular_score_oferta(
        clareza_promessa=8,
        forca_dor=8,
        valor_percebido=8,
        credibilidade=7,
        simplicidade=8,
        risco_preco=4,
    )

    return [
        {
            "teste": "score_oferta",
            "status": "OK" if 0 <= score <= 100 else "FALHA",
            "detalhe": str(score),
        },
        {
            "teste": "classificacao",
            "status": "OK" if classificar_oferta(score) != "" else "FALHA",
            "detalhe": classificar_oferta(score),
        },
        {
            "teste": "campos_oferta",
            "status": "OK" if "score_oferta" in CAMPOS_OFERTA else "FALHA",
            "detalhe": str(len(CAMPOS_OFERTA)),
        },
    ]
