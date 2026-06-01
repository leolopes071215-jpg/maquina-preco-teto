# fiis.py

import streamlit as st
from typing import Any, Dict, Optional


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v1.17 — Motor Inicial de FIIs
# ------------------------------------------------------------
# Este módulo cria uma leitura educacional específica para
# Fundos Imobiliários.
# Ele não recomenda compra/venda.
# Ele avalia renda recorrente, P/VP, vacância, contratos,
# concentração, gestão, liquidez, emissões e sensibilidade a juros.
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
        "empresa": dados.get("empresa", "FII analisado"),
        "ticker": dados.get("ticker", "N/D"),
        "status": _normalizar_status(
            dados.get("status_valuation", dados.get("status", "N/D"))
        ),
        "preco_atual": dados.get("preco_atual"),
        "preco_teto": dados.get("preco_teto"),
        "preco_justo": dados.get("preco_justo", dados.get("preco_justo_combinado")),
    }


def _classificar_risco_fii(score_risco: int) -> str:
    if score_risco <= 25:
        return "Risco controlado"
    if score_risco <= 50:
        return "Atenção moderada"
    if score_risco <= 75:
        return "Risco elevado"
    return "Risco crítico"


def _gerar_leitura_fii(
    score_risco: int,
    classificacao: str,
    dividend_yield: float,
    p_vp: float,
) -> str:
    if classificacao == "Risco controlado":
        return (
            "A análise indica uma estrutura relativamente saudável para um FII. "
            "A renda parece mais sustentável, mas ainda é necessário revisar contratos, vacância, gestão, liquidez e setor."
        )

    if classificacao == "Atenção moderada":
        return (
            "O FII apresenta pontos positivos, mas também alguns riscos relevantes. "
            "A análise exige atenção especial à recorrência dos rendimentos, qualidade dos ativos e sensibilidade aos juros."
        )

    if classificacao == "Risco elevado":
        return (
            "O FII mostra fragilidades importantes. Um dividend yield aparentemente alto pode estar escondendo risco de vacância, "
            "queda de renda, concentração, emissões ruins ou qualidade inferior dos ativos."
        )

    return (
        "O risco da análise parece crítico. Antes de confiar em yield, P/VP ou narrativa de renda passiva, "
        "revise profundamente qualidade dos imóveis, contratos, gestão, alavancagem, liquidez e sustentabilidade dos rendimentos."
    )


def _injetar_css_fiis() -> None:
    st.markdown(
        """
        <style>
            .fii-hero {
                padding: 1.45rem 1.5rem;
                border-radius: 24px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    radial-gradient(circle at top left, rgba(214, 181, 109, 0.18), transparent 30%),
                    radial-gradient(circle at bottom right, rgba(46, 204, 113, 0.14), transparent 34%),
                    linear-gradient(135deg, rgba(8, 15, 24, 0.98), rgba(5, 10, 18, 0.98));
                box-shadow: 0 18px 55px rgba(0, 0, 0, 0.30);
                margin-bottom: 1.25rem;
            }

            .fii-eyebrow {
                color: #d6b56d;
                font-size: 0.78rem;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .fii-title {
                color: #f4f7fb;
                font-size: 1.75rem;
                font-weight: 850;
                margin-bottom: 0.45rem;
            }

            .fii-subtitle {
                color: rgba(244, 247, 251, 0.74);
                font-size: 0.96rem;
                line-height: 1.58;
                max-width: 980px;
            }

            .fii-card {
                padding: 1.05rem 1.1rem;
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.035);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.18);
                height: 100%;
            }

            .fii-card-label {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .fii-card-value {
                color: #f4f7fb;
                font-size: 1.25rem;
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .fii-card-note {
                color: rgba(244, 247, 251, 0.66);
                font-size: 0.86rem;
                line-height: 1.45;
            }

            .fii-alert {
                padding: 0.82rem 1rem;
                border-radius: 14px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.84);
                margin-bottom: 0.6rem;
            }

            .fii-disclaimer {
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
        <div class="fii-card">
            <div class="fii-card-label">{label}</div>
            <div class="fii-card-value">{value}</div>
            <div class="fii-card-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _calcular_score_risco_fii(
    qualidade_renda: int,
    vacancia: int,
    qualidade_imoveis: int,
    diversificacao: int,
    contratos: int,
    gestao: int,
    alavancagem: int,
    liquidez: int,
    risco_emissao: int,
    resistencia_juros: int,
) -> int:
    """
    Quanto maior o score, maior o risco.
    As notas são de qualidade. Para transformar em risco, usamos 10 - nota.
    """
    score = (
        (10 - qualidade_renda) * 1.35
        + (10 - vacancia) * 1.20
        + (10 - qualidade_imoveis) * 1.10
        + (10 - diversificacao) * 1.05
        + (10 - contratos) * 1.05
        + (10 - gestao) * 1.15
        + (10 - alavancagem) * 0.95
        + (10 - liquidez) * 0.80
        + (10 - risco_emissao) * 0.75
        + (10 - resistencia_juros) * 0.60
    )

    score_final = int(round(score))
    return max(0, min(100, score_final))


def _gerar_alertas_fii(
    dividend_yield: float,
    p_vp: float,
    qualidade_renda: int,
    vacancia: int,
    qualidade_imoveis: int,
    diversificacao: int,
    contratos: int,
    gestao: int,
    alavancagem: int,
    liquidez: int,
    risco_emissao: int,
    resistencia_juros: int,
) -> list[str]:
    alertas = []

    if dividend_yield >= 12:
        alertas.append(
            "Dividend yield muito alto: pode indicar oportunidade, mas também pode sinalizar risco, renda não recorrente ou queda esperada nos rendimentos."
        )

    if p_vp < 0.80:
        alertas.append(
            "P/VP muito baixo: desconto patrimonial pode ser oportunidade, mas também pode refletir ativos ruins, gestão fraca ou risco estrutural."
        )

    if p_vp > 1.15:
        alertas.append(
            "P/VP elevado: o mercado pode estar pagando prêmio pelo fundo. Verifique se a qualidade dos ativos e da gestão justifica isso."
        )

    if qualidade_renda <= 4:
        alertas.append(
            "Renda pouco recorrente: rendimentos extraordinários não devem ser tratados como renda sustentável."
        )

    if vacancia <= 4:
        alertas.append(
            "Vacância ou inadimplência preocupante: isso pode pressionar os rendimentos futuros."
        )

    if qualidade_imoveis <= 4:
        alertas.append(
            "Qualidade dos imóveis fraca: localização, padrão dos ativos e liquidez imobiliária afetam o valor real do fundo."
        )

    if diversificacao <= 4:
        alertas.append(
            "Concentração elevada: poucos imóveis ou poucos inquilinos aumentam o risco operacional."
        )

    if contratos <= 4:
        alertas.append(
            "Contratos frágeis: vencimentos próximos, revisões negativas ou contratos atípicos mal avaliados podem afetar renda."
        )

    if gestao <= 4:
        alertas.append(
            "Gestão fraca: uma gestão ruim pode destruir valor mesmo em um fundo com bons imóveis."
        )

    if alavancagem <= 4:
        alertas.append(
            "Alavancagem ou obrigações futuras relevantes: dívidas, obras e compromissos podem afetar dividendos."
        )

    if liquidez <= 4:
        alertas.append(
            "Liquidez baixa: pode dificultar entrada e saída, principalmente para posições maiores."
        )

    if risco_emissao <= 4:
        alertas.append(
            "Risco de emissões ruins: emissões abaixo do valor justo ou mal alocadas podem diluir cotistas."
        )

    if resistencia_juros <= 4:
        alertas.append(
            "Alta sensibilidade aos juros: FIIs podem sofrer quando a renda fixa fica mais atrativa ou o custo de capital sobe."
        )

    return alertas


def renderizar_motor_fiis(
    resultado_valuation: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Renderiza o Motor Inicial de FIIs.
    """
    _injetar_css_fiis()

    contexto = _extrair_contexto_valuation(resultado_valuation)

    st.markdown(
        """
        <div class="fii-hero">
            <div class="fii-eyebrow">Motor educacional de renda imobiliária</div>
            <div class="fii-title">Fundos Imobiliários — Renda, Patrimônio e Risco</div>
            <div class="fii-subtitle">
                FIIs não devem ser analisados como ações comuns. O foco deve estar na sustentabilidade da renda,
                qualidade dos ativos, contratos, vacância, gestão, liquidez, emissões, alavancagem e sensibilidade aos juros.
                Este módulo ajuda a separar yield real de armadilha de renda.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_ctx_1, col_ctx_2, col_ctx_3 = st.columns(3)

    with col_ctx_1:
        st.metric("Ativo analisado", contexto["empresa"])

    with col_ctx_2:
        st.metric("Ticker", contexto["ticker"])

    with col_ctx_3:
        st.metric("Status valuation atual", contexto["status"])

    st.info(
        "Este módulo é uma camada educacional específica para FIIs. "
        "O valuation por EPS/FCF não é o modelo ideal para FIIs; nas próximas versões, criaremos um motor próprio de preço-teto por renda recorrente."
    )

    st.divider()

    st.markdown("### Indicadores básicos do FII")

    col_ind_1, col_ind_2 = st.columns(2)

    with col_ind_1:
        dividend_yield = st.number_input(
            "Dividend yield anual estimado (%)",
            min_value=0.0,
            max_value=50.0,
            value=9.0,
            step=0.1,
            help="Use uma estimativa anualizada e, de preferência, baseada em renda recorrente.",
            key="fii_dividend_yield",
        )

    with col_ind_2:
        p_vp = st.number_input(
            "P/VP atual",
            min_value=0.0,
            max_value=3.0,
            value=0.95,
            step=0.01,
            help="Preço sobre valor patrimonial. P/VP baixo não garante oportunidade; P/VP alto exige qualidade.",
            key="fii_p_vp",
        )

    st.divider()

    st.markdown("### Diagnóstico qualitativo do FII")

    st.caption(
        "Dê notas de 0 a 10. Quanto maior a nota, melhor a qualidade ou menor o risco percebido naquele critério."
    )

    col1, col2 = st.columns(2)

    with col1:
        qualidade_renda = st.slider(
            "Sustentabilidade da renda",
            min_value=0,
            max_value=10,
            value=7,
            help="Nota alta significa renda recorrente, previsível e não dependente de eventos extraordinários.",
            key="fii_renda",
        )

        vacancia = st.slider(
            "Baixo risco de vacância/inadimplência",
            min_value=0,
            max_value=10,
            value=7,
            help="Nota alta significa vacância controlada, boa ocupação e baixo risco de inadimplência.",
            key="fii_vacancia",
        )

        qualidade_imoveis = st.slider(
            "Qualidade dos imóveis/ativos",
            min_value=0,
            max_value=10,
            value=7,
            help="Nota alta significa bons imóveis, boa localização, boa liquidez e ativos competitivos.",
            key="fii_imoveis",
        )

        diversificacao = st.slider(
            "Diversificação de imóveis e inquilinos",
            min_value=0,
            max_value=10,
            value=6,
            help="Nota alta significa menor concentração em poucos imóveis, regiões ou inquilinos.",
            key="fii_diversificacao",
        )

        contratos = st.slider(
            "Qualidade dos contratos",
            min_value=0,
            max_value=10,
            value=6,
            help="Nota alta significa contratos sólidos, prazos saudáveis, bons reajustes e menor risco de revisão negativa.",
            key="fii_contratos",
        )

    with col2:
        gestao = st.slider(
            "Qualidade da gestão",
            min_value=0,
            max_value=10,
            value=7,
            help="Nota alta significa gestão alinhada, transparente e com bom histórico de alocação.",
            key="fii_gestao",
        )

        alavancagem = st.slider(
            "Baixo risco de alavancagem/obrigações",
            min_value=0,
            max_value=10,
            value=7,
            help="Nota alta significa baixa dívida, poucas obrigações futuras e menor risco de pressão sobre rendimentos.",
            key="fii_alavancagem",
        )

        liquidez = st.slider(
            "Liquidez das cotas",
            min_value=0,
            max_value=10,
            value=6,
            help="Nota alta significa facilidade de negociação sem distorcer muito o preço.",
            key="fii_liquidez",
        )

        risco_emissao = st.slider(
            "Baixo risco de emissões ruins",
            min_value=0,
            max_value=10,
            value=6,
            help="Nota alta significa menor risco de emissões dilutivas ou mal alocadas.",
            key="fii_emissao",
        )

        resistencia_juros = st.slider(
            "Resistência ao ciclo de juros",
            min_value=0,
            max_value=10,
            value=6,
            help="Nota alta significa menor sensibilidade negativa a juros altos ou mudanças no custo de capital.",
            key="fii_juros",
        )

    score_risco = _calcular_score_risco_fii(
        qualidade_renda=qualidade_renda,
        vacancia=vacancia,
        qualidade_imoveis=qualidade_imoveis,
        diversificacao=diversificacao,
        contratos=contratos,
        gestao=gestao,
        alavancagem=alavancagem,
        liquidez=liquidez,
        risco_emissao=risco_emissao,
        resistencia_juros=resistencia_juros,
    )

    classificacao = _classificar_risco_fii(score_risco)

    leitura = _gerar_leitura_fii(
        score_risco=score_risco,
        classificacao=classificacao,
        dividend_yield=dividend_yield,
        p_vp=p_vp,
    )

    alertas = _gerar_alertas_fii(
        dividend_yield=dividend_yield,
        p_vp=p_vp,
        qualidade_renda=qualidade_renda,
        vacancia=vacancia,
        qualidade_imoveis=qualidade_imoveis,
        diversificacao=diversificacao,
        contratos=contratos,
        gestao=gestao,
        alavancagem=alavancagem,
        liquidez=liquidez,
        risco_emissao=risco_emissao,
        resistencia_juros=resistencia_juros,
    )

    st.divider()

    st.markdown("### Resultado da análise de FIIs")

    col_res_1, col_res_2, col_res_3, col_res_4 = st.columns(4)

    with col_res_1:
        st.metric("Score de risco", f"{score_risco}/100")

    with col_res_2:
        st.metric("Classificação", classificacao)

    with col_res_3:
        st.metric("DY estimado", f"{dividend_yield:.2f}%")

    with col_res_4:
        st.metric("P/VP", f"{p_vp:.2f}")

    st.progress(score_risco / 100)

    if score_risco <= 25:
        st.success("A estrutura do FII parece relativamente controlada para as notas atuais.")
    elif score_risco <= 50:
        st.warning("O FII possui pontos de atenção relevantes. Revise antes de confiar no yield.")
    else:
        st.error("O FII apresenta riscos importantes. Yield alto pode estar mascarando fragilidades.")

    st.markdown("### Leitura educacional")
    st.info(leitura)

    st.markdown("### Alertas específicos")

    if len(alertas) == 0:
        st.success(
            "Nenhum alerta crítico foi identificado. Ainda assim, revise o relatório gerencial, contratos, vacância, gestão e setor."
        )
    else:
        for alerta in alertas:
            st.markdown(
                f"""
                <div class="fii-alert">
                    {alerta}
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.divider()

    st.markdown("### Como interpretar FIIs com mais disciplina")

    col_info_1, col_info_2, col_info_3 = st.columns(3)

    with col_info_1:
        _card(
            "Dividend yield",
            "Recorrência",
            "Yield alto só tem valor se vier de renda sustentável, contratos saudáveis e ativos de qualidade.",
        )

    with col_info_2:
        _card(
            "P/VP",
            "Preço vs patrimônio",
            "P/VP baixo pode ser desconto ou armadilha. A qualidade dos ativos e da gestão decide a leitura.",
        )

    with col_info_3:
        _card(
            "Juros",
            "Comparação de atratividade",
            "Quando juros sobem, FIIs podem sofrer por competição com renda fixa e aumento do custo de capital.",
        )

    st.markdown("### Perguntas críticas antes de concluir")

    st.markdown(
        """
        - O rendimento atual é recorrente ou extraordinário?
        - A vacância está controlada?
        - Os imóveis são bons e bem localizados?
        - O fundo depende demais de poucos inquilinos?
        - A gestão tem histórico de criar valor?
        - O P/VP reflete oportunidade ou baixa qualidade?
        - Existem dívidas, obras, emissões ou obrigações futuras relevantes?
        - O yield compensa o risco em comparação com a renda fixa?
        """
    )

    resultado_fii = {
        "empresa": contexto["empresa"],
        "ticker": contexto["ticker"],
        "dividend_yield": dividend_yield,
        "p_vp": p_vp,
        "score_risco_fii": score_risco,
        "classificacao_risco_fii": classificacao,
        "leitura_fii": leitura,
        "alertas_fii": alertas,
        "notas": {
            "qualidade_renda": qualidade_renda,
            "vacancia": vacancia,
            "qualidade_imoveis": qualidade_imoveis,
            "diversificacao": diversificacao,
            "contratos": contratos,
            "gestao": gestao,
            "alavancagem": alavancagem,
            "liquidez": liquidez,
            "risco_emissao": risco_emissao,
            "resistencia_juros": resistencia_juros,
        },
    }

    st.session_state["resultado_fiis"] = resultado_fii

    st.markdown(
        """
        <div class="fii-disclaimer">
            <strong>Aviso educacional:</strong> esta leitura não representa recomendação de investimento.
            O módulo de FIIs organiza uma análise de renda, patrimônio e risco. Toda decisão real deve considerar
            objetivos pessoais, diversificação, liquidez, horizonte de tempo, tributação, riscos específicos
            e responsabilidade individual.
        </div>
        """,
        unsafe_allow_html=True,
    )