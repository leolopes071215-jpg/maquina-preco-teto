# laboratorio_growth_valoris.py

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

import streamlit as st

from analytics_publico_valoris import calcular_metricas_funil_publico
from conversao_fundador_valoris import carregar_sinais_conversao
from hub_ativacao_valoris import carregar_ativacoes_valoris
from lista_espera_beta import carregar_leads_lista_espera


# ============================================================
# VALORIS
# v3.8.51 — Laboratório de Growth e Experimentos
# ------------------------------------------------------------
# Este módulo transforma sinais do MVP em decisões de startup.
#
# Objetivo:
# - evitar construir no escuro
# - criar experimentos de crescimento, ativação e monetização
# - usar score ICE/RICE simplificado
# - decidir: testar, melhorar, pausar ou escalar
# - consolidar sinais de funil, leads, ativação e conversão
# ============================================================


VERSAO_LABORATORIO_GROWTH_VALORIS = "3.8.51"

CAMINHO_EXPERIMENTOS_GROWTH = Path("experimentos_growth_valoris.csv")

CAMPOS_EXPERIMENTO = [
    "id",
    "data_registro",
    "nome",
    "area",
    "hipotese",
    "metrica_principal",
    "publico",
    "impacto",
    "confianca",
    "facilidade",
    "risco",
    "score",
    "status",
    "decisao",
    "proximo_passo",
    "observacoes",
]


AREAS_EXPERIMENTO = [
    "Aquisição",
    "Ativação",
    "Educação",
    "Conversão",
    "Retenção",
    "Produto",
    "Monetização",
]


STATUS_EXPERIMENTO = [
    "Ideia",
    "Pronto para testar",
    "Em teste",
    "Validado",
    "Precisa ajustar",
    "Pausado",
    "Descartado",
]


METRICAS_PRINCIPAIS = [
    "Taxa Landing → Demo",
    "Taxa Landing → Lead",
    "Leads cadastrados",
    "Score médio de ativação",
    "Intenção alta de conversão",
    "Barreira dominante reduzida",
    "Download de relatório",
    "Resposta manual positiva",
]


PUBLICOS_EXPERIMENTO = [
    "Usuários públicos",
    "Lista beta",
    "Usuários com alta intenção",
    "Iniciantes",
    "Intermediários",
    "Avançados",
    "Fundadores potenciais",
]


EXPERIMENTOS_SUGERIDOS = [
    {
        "nome": "Aha moment em 60 segundos",
        "area": "Ativação",
        "hipotese": (
            "Se a demonstração guiada aparecer antes do valuation técnico, mais usuários entenderão o valor da Valoris."
        ),
        "metrica": "Taxa Landing → Demo",
    },
    {
        "nome": "Relatório premium como primeira entrega paga",
        "area": "Monetização",
        "hipotese": (
            "Usuários podem aceitar pagar por um relatório claro antes de aceitar uma assinatura mensal."
        ),
        "metrica": "Download de relatório",
    },
    {
        "nome": "Oferta fundador para alta intenção",
        "area": "Conversão",
        "hipotese": (
            "Usuários que escolhem alto valor percebido e baixa barreira devem receber convite manual para beta fundador."
        ),
        "metrica": "Intenção alta de conversão",
    },
    {
        "nome": "Trilha educativa antes da lista beta",
        "area": "Educação",
        "hipotese": (
            "Usuários que aprendem preço, valor e margem antes do cadastro tendem a deixar leads mais qualificados."
        ),
        "metrica": "Taxa Landing → Lead",
    },
]


def _limpar_texto(valor: Any) -> str:
    if valor is None:
        return ""

    return str(valor).strip()


def _garantir_arquivo() -> None:
    if CAMINHO_EXPERIMENTOS_GROWTH.exists():
        return

    with CAMINHO_EXPERIMENTOS_GROWTH.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_EXPERIMENTO)
        escritor.writeheader()


def carregar_experimentos_growth() -> List[Dict[str, str]]:
    _garantir_arquivo()

    with CAMINHO_EXPERIMENTOS_GROWTH.open("r", newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        return list(leitor)


def salvar_experimentos_growth(registros: List[Dict[str, Any]]) -> None:
    with CAMINHO_EXPERIMENTOS_GROWTH.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_EXPERIMENTO)
        escritor.writeheader()

        for registro in registros:
            escritor.writerow({campo: registro.get(campo, "") for campo in CAMPOS_EXPERIMENTO})


def gerar_csv_experimentos_growth() -> str:
    _garantir_arquivo()

    return CAMINHO_EXPERIMENTOS_GROWTH.read_text(encoding="utf-8")


def _safe_float(valor: Any, default: float = 0.0) -> float:
    try:
        return float(str(valor).replace(",", "."))
    except (TypeError, ValueError):
        return default


def _safe_int(valor: Any, default: int = 0) -> int:
    try:
        return int(float(valor))
    except (TypeError, ValueError):
        return default


def calcular_score_experimento(
    impacto: int,
    confianca: int,
    facilidade: int,
    risco: int,
) -> int:
    """
    Score ICE ajustado por risco.
    Impacto, confiança, facilidade e risco vão de 1 a 10.
    """
    score = ((impacto * 2.2) + (confianca * 1.8) + (facilidade * 1.5) - (risco * 1.2)) * 5

    return int(round(max(0, min(100, score))))


def classificar_score_experimento(score: int) -> Dict[str, str]:
    if score >= 82:
        return {
            "decisao": "Testar imediatamente",
            "proximo_passo": "Rodar com poucos usuários qualificados e medir resultado em até 7 dias.",
        }

    if score >= 68:
        return {
            "decisao": "Bom teste controlado",
            "proximo_passo": "Refinar hipótese, definir métrica e testar com amostra pequena.",
        }

    if score >= 50:
        return {
            "decisao": "Ajustar antes de testar",
            "proximo_passo": "Melhorar clareza da hipótese, reduzir risco ou simplificar execução.",
        }

    return {
        "decisao": "Não priorizar agora",
        "proximo_passo": "Guardar como ideia e priorizar experimentos com maior impacto ou facilidade.",
    }


def adicionar_experimento_growth(
    nome: str,
    area: str,
    hipotese: str,
    metrica_principal: str,
    publico: str,
    impacto: int,
    confianca: int,
    facilidade: int,
    risco: int,
    status: str,
    observacoes: str,
) -> Dict[str, Any]:
    registros = carregar_experimentos_growth()

    score = calcular_score_experimento(
        impacto=impacto,
        confianca=confianca,
        facilidade=facilidade,
        risco=risco,
    )

    classificacao = classificar_score_experimento(score)

    novo = {
        "id": str(uuid4())[:8],
        "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "nome": _limpar_texto(nome),
        "area": area,
        "hipotese": _limpar_texto(hipotese),
        "metrica_principal": metrica_principal,
        "publico": publico,
        "impacto": str(impacto),
        "confianca": str(confianca),
        "facilidade": str(facilidade),
        "risco": str(risco),
        "score": str(score),
        "status": status,
        "decisao": classificacao["decisao"],
        "proximo_passo": classificacao["proximo_passo"],
        "observacoes": _limpar_texto(observacoes),
    }

    registros.append(novo)
    salvar_experimentos_growth(registros)

    return novo


def _ordenar_experimentos(registros: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return sorted(
        registros,
        key=lambda item: _safe_int(item.get("score")),
        reverse=True,
    )


def _obter_melhor_experimento(registros: List[Dict[str, str]]) -> Dict[str, str] | None:
    if not registros:
        return None

    return _ordenar_experimentos(registros)[0]


def _calcular_metricas_contexto() -> Dict[str, Any]:
    try:
        funil = calcular_metricas_funil_publico()
    except Exception:
        funil = {}

    try:
        leads = carregar_leads_lista_espera()
    except Exception:
        leads = []

    try:
        ativacoes = carregar_ativacoes_valoris()
    except Exception:
        ativacoes = []

    try:
        conversoes = carregar_sinais_conversao()
    except Exception:
        conversoes = []

    alta_intencao = [
        item for item in conversoes
        if "Alta" in item.get("intencao", "")
    ]

    return {
        "funil": funil,
        "leads": len(leads),
        "ativacoes": len(ativacoes),
        "conversoes": len(conversoes),
        "alta_intencao": len(alta_intencao),
        "taxa_landing_lead": funil.get("taxa_landing_lead", 0),
        "taxa_landing_demo": funil.get("taxa_landing_demo", 0),
    }


def _gerar_insights_contexto(metricas: Dict[str, Any], experimentos: List[Dict[str, str]]) -> List[str]:
    insights = []

    if metricas["leads"] == 0:
        insights.append("Ainda não há leads suficientes. Prioridade: aumentar clareza da proposta e CTA da lista beta.")
    else:
        insights.append(f"Há {metricas['leads']} lead(s) registrados. Já é possível começar validação manual qualitativa.")

    if metricas["taxa_landing_demo"] < 30:
        insights.append("A passagem Landing → Demo parece baixa. Teste uma chamada mais direta para a demonstração.")
    else:
        insights.append("A demonstração já recebe atenção. O próximo desafio é transformar interação em lead.")

    if metricas["alta_intencao"] > 0:
        insights.append("Existem sinais de alta intenção. Priorize convite manual para oferta fundador antes de checkout.")
    else:
        insights.append("Ainda não há muitos sinais de alta intenção. Foque em valor percebido antes de venda.")

    if len(experimentos) == 0:
        insights.append("Nenhum experimento registrado. O próximo passo é criar 1 teste simples, não mais uma funcionalidade grande.")
    else:
        melhor = _obter_melhor_experimento(experimentos)

        if melhor:
            insights.append(
                f"Experimento mais forte: {melhor.get('nome', 'N/D')} com score {melhor.get('score', 'N/D')}/100."
            )

    return insights


def _gerar_markdown_growth(
    metricas: Dict[str, Any],
    experimentos: List[Dict[str, str]],
) -> str:
    melhor = _obter_melhor_experimento(experimentos)

    if melhor:
        melhor_bloco = f"""## Experimento prioritário

Nome: {melhor.get("nome", "N/D")}  
Área: {melhor.get("area", "N/D")}  
Score: {melhor.get("score", "N/D")}/100  
Decisão: {melhor.get("decisao", "N/D")}  
Próximo passo: {melhor.get("proximo_passo", "N/D")}  

Hipótese:
{melhor.get("hipotese", "N/D")}
"""
    else:
        melhor_bloco = "## Experimento prioritário\n\nNenhum experimento registrado ainda.\n"

    linhas_experimentos = "\n".join(
        [
            f"| {item.get('score', '')} | {item.get('nome', '')} | {item.get('area', '')} | {item.get('status', '')} | {item.get('decisao', '')} |"
            for item in _ordenar_experimentos(experimentos)
        ]
    )

    insights = "\n".join([f"- {item}" for item in _gerar_insights_contexto(metricas, experimentos)])

    return f"""# Laboratório de Growth — Valoris

Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Contexto

Leads: {metricas["leads"]}  
Ativações: {metricas["ativacoes"]}  
Sinais de conversão: {metricas["conversoes"]}  
Alta intenção: {metricas["alta_intencao"]}  
Taxa Landing → Demo: {metricas["taxa_landing_demo"]}%  
Taxa Landing → Lead: {metricas["taxa_landing_lead"]}%  

## Insights

{insights}

{melhor_bloco}

## Experimentos

| Score | Nome | Área | Status | Decisão |
|---:|---|---|---|---|
{linhas_experimentos}

## Regra

Não escalar checkout antes de validar:
- dor;
- valor percebido;
- conversão manual;
- entrega clara;
- retenção mínima.
"""


def _injetar_css_growth() -> None:
    st.markdown(
        """
        <style>
            .growth-hero {
                padding: clamp(1.18rem, 3vw, 2rem);
                border-radius: 30px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    radial-gradient(circle at top left, rgba(214, 181, 109, 0.26), transparent 30%),
                    radial-gradient(circle at bottom right, rgba(74, 144, 226, 0.22), transparent 34%),
                    linear-gradient(135deg, rgba(8, 15, 27, 0.99), rgba(5, 9, 18, 0.99));
                box-shadow: 0 18px 58px rgba(0, 0, 0, 0.31);
                margin-bottom: 1rem;
            }

            .growth-eyebrow {
                color: #d6b56d;
                font-size: 0.74rem;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                font-weight: 880;
                margin-bottom: 0.35rem;
            }

            .growth-title {
                color: #f4f7fb;
                font-size: clamp(1.75rem, 5.4vw, 3.1rem);
                font-weight: 950;
                line-height: 1.02;
                letter-spacing: -0.058em;
                margin-bottom: 0.55rem;
            }

            .growth-subtitle {
                color: rgba(244, 247, 251, 0.75);
                font-size: clamp(0.94rem, 2.2vw, 1.06rem);
                line-height: 1.56;
                max-width: 1020px;
            }

            .growth-note {
                padding: 0.92rem 0.98rem;
                border-radius: 17px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.90rem;
                line-height: 1.55;
                margin: 0.85rem 0;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _renderizar_hero() -> None:
    st.markdown(
        f"""
        <div class="growth-hero">
            <div class="growth-eyebrow">Valoris • Laboratório de Growth • v{VERSAO_LABORATORIO_GROWTH_VALORIS}</div>
            <div class="growth-title">Pare de construir no escuro.</div>
            <div class="growth-subtitle">
                O Laboratório de Growth transforma hipóteses em testes. Antes de adicionar mais funcionalidades,
                a Valoris precisa descobrir o que ativa, converte e gera valor real.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _renderizar_metricas_contexto(metricas: Dict[str, Any]) -> None:
    st.markdown("### Sinais atuais do MVP")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Leads", metricas["leads"])

    with col_2:
        st.metric("Ativações", metricas["ativacoes"])

    with col_3:
        st.metric("Sinais de conversão", metricas["conversoes"])

    with col_4:
        st.metric("Alta intenção", metricas["alta_intencao"])

    col_5, col_6 = st.columns(2)

    with col_5:
        st.metric("Landing → Demo", f"{metricas['taxa_landing_demo']}%")

    with col_6:
        st.metric("Landing → Lead", f"{metricas['taxa_landing_lead']}%")


def _renderizar_insights(metricas: Dict[str, Any], experimentos: List[Dict[str, str]]) -> None:
    st.markdown("### Leitura estratégica")

    for insight in _gerar_insights_contexto(metricas, experimentos):
        st.info(insight)


def _renderizar_sugestoes_experimentos() -> None:
    st.markdown("### Experimentos sugeridos")

    for experimento in EXPERIMENTOS_SUGERIDOS:
        with st.container(border=True):
            st.markdown(f"**{experimento['nome']}**")
            st.caption(f"Área: {experimento['area']} • Métrica: {experimento['metrica']}")
            st.markdown(experimento["hipotese"])


def _renderizar_formulario_experimento() -> None:
    st.markdown("### Criar experimento")

    with st.form("form_experimento_growth_valoris"):
        col_1, col_2 = st.columns(2)

        with col_1:
            nome = st.text_input(
                "Nome do experimento",
                value="Aha moment em 60 segundos",
                key="growth_nome",
            )

            area = st.selectbox(
                "Área",
                AREAS_EXPERIMENTO,
                key="growth_area",
            )

            metrica_principal = st.selectbox(
                "Métrica principal",
                METRICAS_PRINCIPAIS,
                key="growth_metrica",
            )

            publico = st.selectbox(
                "Público",
                PUBLICOS_EXPERIMENTO,
                key="growth_publico",
            )

        with col_2:
            status = st.selectbox(
                "Status",
                STATUS_EXPERIMENTO,
                index=1,
                key="growth_status",
            )

            impacto = st.slider("Impacto", 1, 10, 8, key="growth_impacto")
            confianca = st.slider("Confiança", 1, 10, 6, key="growth_confianca")
            facilidade = st.slider("Facilidade", 1, 10, 7, key="growth_facilidade")
            risco = st.slider("Risco", 1, 10, 4, key="growth_risco")

        hipotese = st.text_area(
            "Hipótese",
            value=(
                "Se a demonstração guiada aparecer antes do valuation técnico, mais usuários entenderão "
                "o valor da Valoris e chegarão à lista beta."
            ),
            height=100,
            key="growth_hipotese",
        )

        observacoes = st.text_area(
            "Observações",
            value="",
            height=80,
            key="growth_observacoes",
        )

        enviado = st.form_submit_button("Salvar experimento")

        if enviado:
            experimento = adicionar_experimento_growth(
                nome=nome,
                area=area,
                hipotese=hipotese,
                metrica_principal=metrica_principal,
                publico=publico,
                impacto=impacto,
                confianca=confianca,
                facilidade=facilidade,
                risco=risco,
                status=status,
                observacoes=observacoes,
            )

            st.success(
                f"Experimento salvo: {experimento['nome']} • Score {experimento['score']}/100 • {experimento['decisao']}"
            )
            st.rerun()


def _renderizar_experimentos(experimentos: List[Dict[str, str]]) -> None:
    st.markdown("### Experimentos cadastrados")

    if not experimentos:
        st.info("Nenhum experimento cadastrado ainda.")
        return

    for experimento in _ordenar_experimentos(experimentos):
        score = _safe_int(experimento.get("score"))

        with st.container(border=True):
            st.markdown(f"**{experimento.get('nome', 'N/D')}**")
            st.caption(
                f"Score {score}/100 • {experimento.get('area', 'N/D')} • {experimento.get('status', 'N/D')}"
            )
            st.markdown(f"**Hipótese:** {experimento.get('hipotese', 'N/D')}")
            st.markdown(f"**Decisão:** {experimento.get('decisao', 'N/D')}")
            st.markdown(f"**Próximo passo:** {experimento.get('proximo_passo', 'N/D')}")


def renderizar_laboratorio_growth_valoris() -> None:
    _injetar_css_growth()
    _renderizar_hero()

    metricas = _calcular_metricas_contexto()
    experimentos = carregar_experimentos_growth()

    _renderizar_metricas_contexto(metricas)

    st.divider()

    _renderizar_insights(metricas, experimentos)

    st.divider()

    _renderizar_sugestoes_experimentos()

    st.divider()

    _renderizar_formulario_experimento()

    st.divider()

    _renderizar_experimentos(experimentos)

    st.divider()

    st.download_button(
        "Baixar relatório de growth (.md)",
        data=_gerar_markdown_growth(metricas, experimentos),
        file_name="laboratorio_growth_valoris.md",
        mime="text/markdown",
        key="download_laboratorio_growth_valoris",
    )

    st.download_button(
        "Baixar experimentos (.csv)",
        data=gerar_csv_experimentos_growth(),
        file_name="experimentos_growth_valoris.csv",
        mime="text/csv",
        key="download_experimentos_growth_valoris",
    )

    st.markdown(
        """
        <div class="growth-note">
            <strong>Regra do laboratório:</strong> toda nova funcionalidade precisa responder a uma hipótese.
            Se não melhora ativação, conversão, retenção ou monetização, talvez não seja prioridade agora.
        </div>
        """,
        unsafe_allow_html=True,
    )


def executar_autoteste_laboratorio_growth_valoris() -> List[Dict[str, str]]:
    score = calcular_score_experimento(
        impacto=8,
        confianca=6,
        facilidade=7,
        risco=4,
    )

    classificacao = classificar_score_experimento(score)

    return [
        {
            "teste": "versao_growth",
            "status": "OK" if VERSAO_LABORATORIO_GROWTH_VALORIS == "3.8.51" else "FALHA",
            "detalhe": VERSAO_LABORATORIO_GROWTH_VALORIS,
        },
        {
            "teste": "score",
            "status": "OK" if 0 <= score <= 100 else "FALHA",
            "detalhe": str(score),
        },
        {
            "teste": "decisao",
            "status": "OK" if classificacao["decisao"] != "" else "FALHA",
            "detalhe": classificacao["decisao"],
        },
    ]
