# central_multiativos.py

import streamlit as st
from typing import Any, Dict, Optional


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v1.15 — Central Multiativos
# ------------------------------------------------------------
# Esta tela organiza a visão de produto da plataforma:
# Ações EUA, Ações Brasil, FIIs e Renda Fixa.
# O objetivo é guiar o usuário por classe de ativo sem misturar
# modelos analíticos diferentes.
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
        "empresa": dados.get("empresa", "Empresa analisada"),
        "ticker": dados.get("ticker", "N/D"),
        "status": _normalizar_status(
            dados.get("status_valuation", dados.get("status", "N/D"))
        ),
        "preco_atual": dados.get("preco_atual"),
        "preco_teto": dados.get("preco_teto"),
        "preco_justo": dados.get("preco_justo", dados.get("preco_justo_combinado")),
    }


def _injetar_css_central_multiativos() -> None:
    st.markdown(
        """
        <style>
            .multi-hero {
                padding: 1.5rem 1.55rem;
                border-radius: 24px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    radial-gradient(circle at top left, rgba(214, 181, 109, 0.20), transparent 30%),
                    radial-gradient(circle at bottom right, rgba(74, 144, 226, 0.18), transparent 34%),
                    linear-gradient(135deg, rgba(9, 14, 26, 0.98), rgba(5, 9, 18, 0.98));
                box-shadow: 0 18px 55px rgba(0, 0, 0, 0.32);
                margin-bottom: 1.25rem;
            }

            .multi-eyebrow {
                color: #d6b56d;
                font-size: 0.78rem;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .multi-title {
                color: #f4f7fb;
                font-size: 1.85rem;
                font-weight: 850;
                margin-bottom: 0.45rem;
            }

            .multi-subtitle {
                color: rgba(244, 247, 251, 0.74);
                font-size: 0.98rem;
                line-height: 1.58;
                max-width: 980px;
            }

            .multi-card {
                padding: 1.05rem 1.1rem;
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.035);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.18);
                height: 100%;
            }

            .multi-card-title {
                color: #f4f7fb;
                font-size: 1.08rem;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .multi-card-tag {
                display: inline-block;
                padding: 0.18rem 0.55rem;
                border-radius: 999px;
                background: rgba(214, 181, 109, 0.10);
                border: 1px solid rgba(214, 181, 109, 0.20);
                color: #d6b56d;
                font-size: 0.72rem;
                font-weight: 750;
                margin-bottom: 0.5rem;
            }

            .multi-card-text {
                color: rgba(244, 247, 251, 0.68);
                font-size: 0.88rem;
                line-height: 1.48;
            }

            .multi-section {
                padding: 1.05rem 1.1rem;
                border-radius: 18px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.025);
                margin-bottom: 1rem;
            }

            .multi-section-title {
                color: #f4f7fb;
                font-size: 1.18rem;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .multi-section-text {
                color: rgba(244, 247, 251, 0.70);
                font-size: 0.92rem;
                line-height: 1.55;
            }

            .multi-disclaimer {
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


def _card_modulo(titulo: str, tag: str, texto: str) -> None:
    st.markdown(
        f"""
        <div class="multi-card">
            <div class="multi-card-tag">{tag}</div>
            <div class="multi-card-title">{titulo}</div>
            <div class="multi-card-text">{texto}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _renderizar_leitura_por_classe(classe_ativo: str) -> None:
    if classe_ativo == "Ações EUA":
        st.markdown("### Motor recomendado para Ações EUA")
        st.info(
            """
            Para ações americanas, o núcleo atual já faz sentido: lucro normalizado, FCF por ação,
            múltiplos justos, margem de segurança, cenários, convicção da tese e checklist de erros.
            O próximo ganho de sofisticação será adicionar dados históricos, ROIC, crescimento,
            recompra de ações e comparação setorial.
            """
        )

        st.markdown("#### Perguntas que o usuário deve responder")
        st.markdown(
            """
            - A empresa converte lucro em fluxo de caixa livre?
            - O múltiplo escolhido é compatível com a qualidade do negócio?
            - O crescimento é sustentável ou otimista demais?
            - O preço atual oferece margem de segurança?
            - A tese continua boa em cenário conservador?
            """
        )

    elif classe_ativo == "Ações Brasil":
        st.markdown("### Motor futuro para Ações Brasil")
        st.info(
            """
            Para ações brasileiras, o modelo de lucro e FCF continua útil, mas precisa considerar
            fatores locais: governança, risco Brasil, dividendos, payout, dívida líquida, setor regulado,
            exposição ao câmbio, juros domésticos e histórico de alocação de capital.
            """
        )

        st.markdown("#### Perguntas que o usuário deve responder")
        st.markdown(
            """
            - A empresa é estatal, regulada ou muito dependente de ciclo econômico?
            - O lucro é recorrente ou foi afetado por evento extraordinário?
            - A dívida líquida está sob controle?
            - Os dividendos são sustentáveis?
            - O preço compensa risco Brasil, juros e governança?
            """
        )

    elif classe_ativo == "Fundos Imobiliários":
        st.markdown("### Motor futuro para Fundos Imobiliários")
        st.info(
            """
            FIIs não devem ser avaliados como ações comuns. O centro da análise deve ser renda recorrente,
            qualidade dos imóveis, contratos, vacância, inadimplência, P/VP, gestão, liquidez,
            emissões e sensibilidade a juros.
            """
        )

        st.markdown("#### Perguntas que o usuário deve responder")
        st.markdown(
            """
            - O dividend yield é recorrente ou inflado por evento não recorrente?
            - O fundo tem concentração em poucos imóveis ou inquilinos?
            - A vacância e os contratos estão saudáveis?
            - O P/VP reflete oportunidade real ou baixa qualidade?
            - A gestão cria ou destrói valor?
            """
        )

    else:
        st.markdown("### Motor futuro para Renda Fixa")
        st.info(
            """
            Renda fixa deve ser analisada por adequação, não por preço-teto. O foco deve ser:
            emissor, risco de crédito, indexador, prazo, liquidez, imposto, FGC, marcação a mercado
            e comparação com alternativas como CDI, Tesouro Selic, IPCA+ e prefixados.
            """
        )

        st.markdown("#### Perguntas que o usuário deve responder")
        st.markdown(
            """
            - O emissor é seguro para o prêmio oferecido?
            - A liquidez combina com o objetivo do dinheiro?
            - O prazo faz sentido?
            - A rentabilidade líquida compensa?
            - O risco de marcação a mercado foi entendido?
            """
        )


def renderizar_central_multiativos(
    resultado_valuation: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Renderiza a Central Multiativos.
    """
    _injetar_css_central_multiativos()

    contexto = _extrair_contexto_valuation(resultado_valuation)

    st.markdown(
        """
        <div class="multi-hero">
            <div class="multi-eyebrow">Arquitetura premium do produto</div>
            <div class="multi-title">Central Multiativos</div>
            <div class="multi-subtitle">
                A Máquina de Preço-Teto está evoluindo para uma plataforma educacional de decisão multiativos.
                Cada classe exige um raciocínio próprio: ações pedem valuation, FIIs pedem análise de renda e patrimônio,
                renda fixa pede adequação entre risco, prazo, liquidez e taxa.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Contexto atual da análise")

    col_ctx_1, col_ctx_2, col_ctx_3 = st.columns(3)

    with col_ctx_1:
        st.metric("Ativo analisado", contexto["empresa"])

    with col_ctx_2:
        st.metric("Ticker", contexto["ticker"])

    with col_ctx_3:
        st.metric("Status educacional", contexto["status"])

    st.divider()

    classe_ativo = st.selectbox(
        "Escolha o universo de análise",
        [
            "Ações EUA",
            "Ações Brasil",
            "Fundos Imobiliários",
            "Renda Fixa",
        ],
        index=0,
        help="Essa escolha ajuda o app a orientar o raciocínio correto para cada classe de ativo.",
        key="classe_ativo_principal",
    )

    # Importante:
    # Não podemos fazer st.session_state["classe_ativo_principal"] = classe_ativo aqui,
    # porque essa chave já pertence ao widget selectbox acima.
    # O Streamlit já salva automaticamente o valor nessa chave.
    # Para guardar uma cópia segura, usamos outra chave.
    st.session_state["classe_ativo_atual"] = classe_ativo

    st.markdown("### Módulos estratégicos da plataforma")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        _card_modulo(
            "Ações EUA",
            "Motor atual",
            "Valuation por EPS e FCF, margem de segurança, cenários, tese qualitativa, checklist de erros e relatório premium.",
        )

    with col2:
        _card_modulo(
            "Ações Brasil",
            "Próximo núcleo",
            "Adaptação do valuation para empresas da B3, considerando governança, dividendos, dívida, risco Brasil e setores regulados.",
        )

    with col3:
        _card_modulo(
            "Fundos Imobiliários",
            "Novo motor",
            "Análise por renda recorrente, P/VP, vacância, contratos, gestão, liquidez, emissões e sensibilidade a juros.",
        )

    with col4:
        _card_modulo(
            "Renda Fixa",
            "Novo motor",
            "Análise por risco de crédito, prazo, liquidez, indexador, FGC, imposto, marcação a mercado e prêmio sobre alternativas.",
        )

    st.divider()

    _renderizar_leitura_por_classe(classe_ativo)

    st.divider()

    st.markdown("### Jornada educacional ideal")

    st.markdown(
        """
        A experiência ideal da plataforma deve seguir uma sequência disciplinada:

        1. **Escolher a classe de ativo correta**
        2. **Inserir premissas compatíveis com aquela classe**
        3. **Calcular ou avaliar o ativo com o motor adequado**
        4. **Testar cenários**
        5. **Avaliar a tese qualitativa**
        6. **Rodar o checklist de erros**
        7. **Gerar o resumo da decisão**
        8. **Baixar o relatório premium**
        9. **Salvar a análise e acompanhar no tempo**
        """
    )

    st.markdown("### O que essa central resolve")

    st.markdown(
        """
        Muitos investidores erram porque aplicam o mesmo raciocínio para tudo.

        - Ação não é FII.
        - FII não é renda fixa.
        - Renda fixa não é valuation.
        - Dividend yield alto não é automaticamente qualidade.
        - Taxa alta não é automaticamente oportunidade.
        - Empresa boa não é automaticamente ação barata.

        A Central Multiativos existe para organizar o método antes do cálculo.
        """
    )

    st.markdown(
        """
        <div class="multi-disclaimer">
            <strong>Aviso educacional:</strong> esta central não recomenda ativos. Ela organiza a jornada de análise
            para que cada classe seja estudada com o método correto. O objetivo é reduzir erros, aumentar clareza
            e melhorar a disciplina do investidor.
        </div>
        """,
        unsafe_allow_html=True,
    )