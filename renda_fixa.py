# renda_fixa.py

import streamlit as st
from typing import Any, Dict, Optional


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v1.18 — Motor Inicial de Renda Fixa
# ------------------------------------------------------------
# Este módulo cria uma leitura educacional específica para
# renda fixa.
# Ele não recomenda compra/venda.
# Ele avalia emissor, prazo, liquidez, indexador, FGC, imposto,
# marcação a mercado e prêmio de risco.
# ============================================================


def _normalizar_status(status: Any) -> str:
    if status is None:
        return "N/D"

    texto = str(status).upper().strip()

    if "COMPRA" in texto:
        return "COMPRA"
    if "NEUTRO" in texto:
        return "NEUTRO"
    if "AGUARDE" in texto:
        return "AGUARDE"

    return texto or "N/D"


def _extrair_contexto_valuation(
    resultado_valuation: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    dados = {}

    if isinstance(st.session_state.get("resultado_valuation"), dict):
        dados.update(st.session_state["resultado_valuation"])

    if isinstance(resultado_valuation, dict):
        dados.update(resultado_valuation)

    return {
        "empresa": dados.get("empresa", "Ativo de renda fixa analisado"),
        "ticker": dados.get("ticker", "N/D"),
        "status": _normalizar_status(
            dados.get("status_valuation", dados.get("status", "N/D"))
        ),
    }


def _classificar_risco_renda_fixa(score_risco: int) -> str:
    if score_risco <= 25:
        return "Adequação forte"
    if score_risco <= 50:
        return "Atenção moderada"
    if score_risco <= 75:
        return "Risco elevado"
    return "Risco crítico"


def _gerar_leitura_renda_fixa(
    classificacao: str,
    tipo_titulo: str,
    indexador: str,
    possui_fgc: str,
) -> str:
    if classificacao == "Adequação forte":
        return (
            f"A análise indica boa adequação educacional para um título de renda fixa do tipo {tipo_titulo}, "
            f"indexado a {indexador}. Mesmo assim, revise emissor, prazo, liquidez, tributação e objetivo do dinheiro."
        )

    if classificacao == "Atenção moderada":
        return (
            f"O título de renda fixa analisado tem pontos positivos, mas exige atenção. "
            f"A decisão não deve depender apenas da taxa. Revise risco do emissor, prazo, liquidez, FGC e marcação a mercado."
        )

    if classificacao == "Risco elevado":
        return (
            f"A análise mostra riscos relevantes. Taxa alta pode ser compensação por risco maior. "
            f"Antes de avançar, revise crédito do emissor, prazo, liquidez, proteção do FGC e compatibilidade com seu objetivo."
        )

    return (
        f"A análise mostra risco crítico. O produto pode estar sendo avaliado apenas pela rentabilidade aparente, "
        f"sem considerar adequadamente risco de crédito, liquidez, prazo, imposto, FGC ou marcação a mercado."
    )


def _injetar_css_renda_fixa() -> None:
    st.markdown(
        """
        <style>
            .rf-hero {
                padding: 1.45rem 1.5rem;
                border-radius: 24px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    radial-gradient(circle at top left, rgba(74, 144, 226, 0.20), transparent 30%),
                    radial-gradient(circle at bottom right, rgba(214, 181, 109, 0.15), transparent 34%),
                    linear-gradient(135deg, rgba(8, 15, 24, 0.98), rgba(5, 10, 18, 0.98));
                box-shadow: 0 18px 55px rgba(0, 0, 0, 0.30);
                margin-bottom: 1.25rem;
            }

            .rf-eyebrow {
                color: #d6b56d;
                font-size: 0.78rem;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .rf-title {
                color: #f4f7fb;
                font-size: 1.75rem;
                font-weight: 850;
                margin-bottom: 0.45rem;
            }

            .rf-subtitle {
                color: rgba(244, 247, 251, 0.74);
                font-size: 0.96rem;
                line-height: 1.58;
                max-width: 980px;
            }

            .rf-card {
                padding: 1.05rem 1.1rem;
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.035);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.18);
                height: 100%;
            }

            .rf-card-label {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .rf-card-value {
                color: #f4f7fb;
                font-size: 1.25rem;
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .rf-card-note {
                color: rgba(244, 247, 251, 0.66);
                font-size: 0.86rem;
                line-height: 1.45;
            }

            .rf-alert {
                padding: 0.82rem 1rem;
                border-radius: 14px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.84);
                margin-bottom: 0.6rem;
            }

            .rf-disclaimer {
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
        <div class="rf-card">
            <div class="rf-card-label">{label}</div>
            <div class="rf-card-value">{value}</div>
            <div class="rf-card-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _calcular_score_risco_renda_fixa(
    qualidade_emissor: int,
    adequacao_prazo: int,
    liquidez: int,
    protecao_fgc: int,
    entendimento_indexador: int,
    risco_marcacao: int,
    rentabilidade_liquida: int,
    diversificacao: int,
    premio_risco: int,
    adequacao_objetivo: int,
) -> int:
    """
    Quanto maior o score, maior o risco.
    As notas são de qualidade. Para transformar em risco, usamos 10 - nota.
    """
    score = (
        (10 - qualidade_emissor) * 1.35
        + (10 - adequacao_prazo) * 1.15
        + (10 - liquidez) * 1.15
        + (10 - protecao_fgc) * 1.00
        + (10 - entendimento_indexador) * 0.90
        + (10 - risco_marcacao) * 1.00
        + (10 - rentabilidade_liquida) * 0.90
        + (10 - diversificacao) * 0.80
        + (10 - premio_risco) * 0.90
        + (10 - adequacao_objetivo) * 1.10
    )

    score_final = int(round(score))
    return max(0, min(100, score_final))


def _gerar_alertas_renda_fixa(
    tipo_titulo: str,
    indexador: str,
    taxa_anual: float,
    prazo_meses: int,
    possui_fgc: str,
    qualidade_emissor: int,
    adequacao_prazo: int,
    liquidez: int,
    protecao_fgc: int,
    entendimento_indexador: int,
    risco_marcacao: int,
    rentabilidade_liquida: int,
    diversificacao: int,
    premio_risco: int,
    adequacao_objetivo: int,
) -> list[str]:
    alertas = []

    if qualidade_emissor <= 4:
        alertas.append(
            "Risco de crédito relevante: a taxa pode estar alta porque o emissor oferece mais risco."
        )

    if adequacao_prazo <= 4:
        alertas.append(
            "Prazo inadequado: o vencimento pode não combinar com o objetivo do dinheiro."
        )

    if liquidez <= 4:
        alertas.append(
            "Liquidez baixa: pode ser difícil sair antes do vencimento sem perda ou sem mercado secundário."
        )

    if protecao_fgc <= 4 or possui_fgc == "Não":
        alertas.append(
            "Proteção limitada: sem FGC, a análise do emissor precisa ser muito mais rigorosa."
        )

    if entendimento_indexador <= 4:
        alertas.append(
            "Indexador mal compreendido: CDI, IPCA e prefixado reagem de formas diferentes a juros e inflação."
        )

    if risco_marcacao <= 4:
        alertas.append(
            "Marcação a mercado relevante: títulos prefixados e IPCA+ podem oscilar antes do vencimento."
        )

    if rentabilidade_liquida <= 4:
        alertas.append(
            "Rentabilidade líquida pouco clara: imposto, IOF, taxas e prazo podem reduzir bastante o retorno final."
        )

    if diversificacao <= 4:
        alertas.append(
            "Concentração elevada: colocar muito em um emissor, indexador ou vencimento aumenta o risco."
        )

    if premio_risco <= 4:
        alertas.append(
            "Prêmio de risco duvidoso: a taxa pode não compensar o risco em comparação com Tesouro, CDI ou alternativas similares."
        )

    if adequacao_objetivo <= 4:
        alertas.append(
            "Incompatibilidade com objetivo: reserva de emergência, médio prazo e longo prazo exigem produtos diferentes."
        )

    if prazo_meses > 60 and liquidez <= 5:
        alertas.append(
            "Prazo longo com baixa liquidez: isso pode prender o dinheiro por tempo demais."
        )

    if tipo_titulo in ["Debênture", "CRI", "CRA"] and possui_fgc == "Não":
        alertas.append(
            "Produto sem FGC: debêntures, CRIs e CRAs exigem análise profunda de crédito e garantias."
        )

    if indexador == "Prefixado" and prazo_meses >= 36:
        alertas.append(
            "Prefixado longo: pode sofrer forte marcação a mercado se os juros subirem."
        )

    if taxa_anual <= 0:
        alertas.append(
            "Taxa inválida ou zerada: revise o dado inserido antes de concluir a análise."
        )

    return alertas


def renderizar_motor_renda_fixa(
    resultado_valuation: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Renderiza o Motor Inicial de Renda Fixa.
    """
    _injetar_css_renda_fixa()

    contexto = _extrair_contexto_valuation(resultado_valuation)

    st.markdown(
        """
        <div class="rf-hero">
            <div class="rf-eyebrow">Motor educacional de proteção e taxa</div>
            <div class="rf-title">Renda Fixa — Risco, Prazo, Liquidez e Adequação</div>
            <div class="rf-subtitle">
                Renda fixa não deve ser analisada como ação. O centro da decisão é adequação:
                emissor, risco de crédito, prazo, liquidez, indexador, FGC, imposto, marcação a mercado
                e comparação com alternativas como CDI e Tesouro Direto.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_ctx_1, col_ctx_2, col_ctx_3 = st.columns(3)

    with col_ctx_1:
        st.metric("Contexto atual", contexto["empresa"])

    with col_ctx_2:
        st.metric("Código/Ticker", contexto["ticker"])

    with col_ctx_3:
        st.metric("Status valuation atual", contexto["status"])

    st.info(
        "Este módulo é uma camada educacional específica para renda fixa. "
        "Aqui a pergunta principal não é 'qual é o preço-teto?', mas sim: "
        "'esse produto combina com o objetivo, risco, prazo e liquidez do investidor?'."
    )

    st.divider()

    st.markdown("### Dados básicos do título")

    col_dado_1, col_dado_2, col_dado_3 = st.columns(3)

    with col_dado_1:
        tipo_titulo = st.selectbox(
            "Tipo de produto",
            [
                "CDB",
                "LCI/LCA",
                "Tesouro Selic",
                "Tesouro IPCA+",
                "Tesouro Prefixado",
                "Debênture",
                "CRI",
                "CRA",
                "Outro",
            ],
            help="Escolha a categoria mais próxima do produto analisado.",
            key="rf_tipo_titulo",
        )

    with col_dado_2:
        indexador = st.selectbox(
            "Indexador",
            [
                "CDI",
                "IPCA",
                "Prefixado",
                "Selic",
                "Híbrido",
                "Outro",
            ],
            help="O indexador define como a rentabilidade reage a juros e inflação.",
            key="rf_indexador",
        )

    with col_dado_3:
        possui_fgc = st.selectbox(
            "Tem proteção do FGC?",
            [
                "Sim",
                "Não",
                "Não sei",
            ],
            help="FGC não elimina todo risco, mas muda bastante a análise de crédito para produtos elegíveis.",
            key="rf_fgc",
        )

    col_dado_4, col_dado_5 = st.columns(2)

    with col_dado_4:
        taxa_anual = st.number_input(
            "Taxa anual informada (%)",
            min_value=0.0,
            max_value=100.0,
            value=12.0,
            step=0.1,
            help="Informe a taxa anual aproximada. Exemplo: 12 para 12% ao ano.",
            key="rf_taxa_anual",
        )

    with col_dado_5:
        prazo_meses = st.number_input(
            "Prazo até o vencimento (meses)",
            min_value=1,
            max_value=600,
            value=24,
            step=1,
            help="Informe em meses. Exemplo: 24 para dois anos.",
            key="rf_prazo_meses",
        )

    st.divider()

    st.markdown("### Diagnóstico de qualidade da renda fixa")

    st.caption(
        "Dê notas de 0 a 10. Quanto maior a nota, melhor a qualidade ou menor o risco percebido naquele critério."
    )

    col1, col2 = st.columns(2)

    with col1:
        qualidade_emissor = st.slider(
            "Qualidade do emissor",
            min_value=0,
            max_value=10,
            value=7,
            help="Nota alta significa emissor mais confiável e menor risco de crédito.",
            key="rf_emissor",
        )

        adequacao_prazo = st.slider(
            "Adequação do prazo ao objetivo",
            min_value=0,
            max_value=10,
            value=7,
            help="Nota alta significa que o vencimento combina com o objetivo do dinheiro.",
            key="rf_prazo",
        )

        liquidez = st.slider(
            "Liquidez antes do vencimento",
            min_value=0,
            max_value=10,
            value=7,
            help="Nota alta significa facilidade de resgatar ou vender antes do vencimento.",
            key="rf_liquidez",
        )

        protecao_fgc = st.slider(
            "Proteção e segurança estrutural",
            min_value=0,
            max_value=10,
            value=7,
            help="Nota alta significa boa proteção estrutural, FGC quando aplicável ou garantias claras.",
            key="rf_protecao",
        )

        entendimento_indexador = st.slider(
            "Entendimento do indexador",
            min_value=0,
            max_value=10,
            value=7,
            help="Nota alta significa que você entende como CDI, IPCA ou prefixado se comporta.",
            key="rf_entendimento_indexador",
        )

    with col2:
        risco_marcacao = st.slider(
            "Baixo risco de marcação a mercado",
            min_value=0,
            max_value=10,
            value=6,
            help="Nota alta significa menor risco de oscilação relevante antes do vencimento.",
            key="rf_marcacao",
        )

        rentabilidade_liquida = st.slider(
            "Clareza da rentabilidade líquida",
            min_value=0,
            max_value=10,
            value=6,
            help="Nota alta significa que imposto, IOF, taxas e prazo já foram considerados.",
            key="rf_liquida",
        )

        diversificacao = st.slider(
            "Diversificação da alocação",
            min_value=0,
            max_value=10,
            value=6,
            help="Nota alta significa baixa concentração em um único emissor, prazo ou indexador.",
            key="rf_diversificacao",
        )

        premio_risco = st.slider(
            "Prêmio de risco suficiente",
            min_value=0,
            max_value=10,
            value=6,
            help="Nota alta significa que a taxa compensa bem o risco frente a alternativas como CDI e Tesouro.",
            key="rf_premio",
        )

        adequacao_objetivo = st.slider(
            "Adequação ao objetivo do dinheiro",
            min_value=0,
            max_value=10,
            value=7,
            help="Nota alta significa que o produto combina com reserva, médio prazo ou longo prazo.",
            key="rf_objetivo",
        )

    score_risco = _calcular_score_risco_renda_fixa(
        qualidade_emissor=qualidade_emissor,
        adequacao_prazo=adequacao_prazo,
        liquidez=liquidez,
        protecao_fgc=protecao_fgc,
        entendimento_indexador=entendimento_indexador,
        risco_marcacao=risco_marcacao,
        rentabilidade_liquida=rentabilidade_liquida,
        diversificacao=diversificacao,
        premio_risco=premio_risco,
        adequacao_objetivo=adequacao_objetivo,
    )

    classificacao = _classificar_risco_renda_fixa(score_risco)

    leitura = _gerar_leitura_renda_fixa(
        classificacao=classificacao,
        tipo_titulo=tipo_titulo,
        indexador=indexador,
        possui_fgc=possui_fgc,
    )

    alertas = _gerar_alertas_renda_fixa(
        tipo_titulo=tipo_titulo,
        indexador=indexador,
        taxa_anual=taxa_anual,
        prazo_meses=int(prazo_meses),
        possui_fgc=possui_fgc,
        qualidade_emissor=qualidade_emissor,
        adequacao_prazo=adequacao_prazo,
        liquidez=liquidez,
        protecao_fgc=protecao_fgc,
        entendimento_indexador=entendimento_indexador,
        risco_marcacao=risco_marcacao,
        rentabilidade_liquida=rentabilidade_liquida,
        diversificacao=diversificacao,
        premio_risco=premio_risco,
        adequacao_objetivo=adequacao_objetivo,
    )

    st.divider()

    st.markdown("### Resultado da análise de renda fixa")

    col_res_1, col_res_2, col_res_3, col_res_4 = st.columns(4)

    with col_res_1:
        st.metric("Score de risco", f"{score_risco}/100")

    with col_res_2:
        st.metric("Classificação", classificacao)

    with col_res_3:
        st.metric("Taxa informada", f"{taxa_anual:.2f}% a.a.")

    with col_res_4:
        st.metric("Prazo", f"{int(prazo_meses)} meses")

    st.progress(score_risco / 100)

    if score_risco <= 25:
        st.success("A estrutura do título parece adequada para as notas atuais.")
    elif score_risco <= 50:
        st.warning("Existem pontos de atenção. Revise antes de decidir pela taxa.")
    else:
        st.error("O produto apresenta riscos relevantes. Taxa alta pode estar mascarando fragilidades.")

    st.markdown("### Leitura educacional")
    st.info(leitura)

    st.markdown("### Alertas específicos")

    if len(alertas) == 0:
        st.success(
            "Nenhum alerta crítico foi identificado. Ainda assim, compare com CDI, Tesouro Direto e alternativas similares."
        )
    else:
        for alerta in alertas:
            st.markdown(
                f"""
                <div class="rf-alert">
                    {alerta}
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.divider()

    st.markdown("### Como interpretar renda fixa com mais disciplina")

    col_info_1, col_info_2, col_info_3 = st.columns(3)

    with col_info_1:
        _card(
            "Taxa",
            "Não basta",
            "Taxa alta pode ser oportunidade, mas também pode ser compensação por risco maior.",
        )

    with col_info_2:
        _card(
            "Liquidez",
            "Combina com o objetivo?",
            "Reserva de emergência exige liquidez. Longo prazo aceita travamento maior.",
        )

    with col_info_3:
        _card(
            "Crédito",
            "Quem promete pagar?",
            "Em renda fixa privada, o emissor é parte central da análise.",
        )

    st.markdown("### Perguntas críticas antes de concluir")

    st.markdown(
        """
        - O emissor é confiável?
        - O produto tem FGC? Se não tem, o prêmio compensa?
        - A liquidez combina com o objetivo do dinheiro?
        - O prazo é adequado?
        - A rentabilidade líquida foi calculada?
        - O indexador faz sentido para o cenário econômico?
        - O risco de marcação a mercado foi entendido?
        - A taxa compensa em comparação com CDI, Tesouro Selic, IPCA+ ou alternativas similares?
        """
    )

    resultado_renda_fixa = {
        "tipo_titulo": tipo_titulo,
        "indexador": indexador,
        "possui_fgc": possui_fgc,
        "taxa_anual": taxa_anual,
        "prazo_meses": int(prazo_meses),
        "score_risco_renda_fixa": score_risco,
        "classificacao_renda_fixa": classificacao,
        "leitura_renda_fixa": leitura,
        "alertas_renda_fixa": alertas,
        "notas": {
            "qualidade_emissor": qualidade_emissor,
            "adequacao_prazo": adequacao_prazo,
            "liquidez": liquidez,
            "protecao_fgc": protecao_fgc,
            "entendimento_indexador": entendimento_indexador,
            "risco_marcacao": risco_marcacao,
            "rentabilidade_liquida": rentabilidade_liquida,
            "diversificacao": diversificacao,
            "premio_risco": premio_risco,
            "adequacao_objetivo": adequacao_objetivo,
        },
    }

    st.session_state["resultado_renda_fixa"] = resultado_renda_fixa

    st.markdown(
        """
        <div class="rf-disclaimer">
            <strong>Aviso educacional:</strong> esta leitura não representa recomendação de investimento.
            O módulo de Renda Fixa organiza uma análise de risco, prazo, liquidez, emissor e adequação.
            Toda decisão real deve considerar objetivos pessoais, diversificação, tributação, liquidez,
            garantias, risco de crédito e responsabilidade individual.
        </div>
        """,
        unsafe_allow_html=True,
    )