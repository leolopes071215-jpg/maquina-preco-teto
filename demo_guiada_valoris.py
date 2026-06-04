# demo_guiada_valoris.py

from typing import Any, Dict, List

import streamlit as st

from lista_espera_beta import renderizar_lista_espera_valoris
from analytics_publico_valoris import registrar_visualizacao_unica, registrar_evento_publico


# ============================================================
# VALORIS
# v3.8.45 — Demonstração Guiada com Analytics
# ------------------------------------------------------------
# Esta tela permite que o usuário sinta a Valoris funcionando
# em uma experiência didática, visual e guiada.
#
# Objetivo:
# - explicar o produto sem exigir conhecimento prévio
# - mostrar a diferença entre preço, valor, preço-teto e auditoria
# - gerar fascínio pela estrutura da análise
# - conduzir para lista beta sem parecer venda agressiva
# - manter tudo educacional, sem recomendação de investimento
# ============================================================


VERSAO_DEMO_GUIADA_VALORIS = "3.8.45"


DEMO_ATIVO = {
    "empresa": "Empresa Aurora",
    "ticker": "AURA3",
    "setor": "Empresa fictícia para demonstração",
    "preco_atual": 82.00,
    "preco_teto": 70.00,
    "preco_justo": 95.00,
    "margem_seguranca": 25.0,
    "score_confianca": 64,
    "score_fundamentalista": 58,
    "status": "Zona de atenção",
}


PERFIS_DEMO = {
    "Iniciante": {
        "titulo": "Você quer saber se está pagando caro.",
        "descricao": (
            "A Valoris traduz o valuation para uma leitura simples: preço atual, preço-teto, "
            "zona de decisão e próximos passos."
        ),
        "foco": "Clareza antes de complexidade.",
    },
    "Intermediário": {
        "titulo": "Você quer validar a qualidade da decisão.",
        "descricao": (
            "A Valoris ajuda a revisar margem de segurança, premissas, riscos e pontos ainda não verificados."
        ),
        "foco": "Auditoria antes de ação.",
    },
    "Avançado": {
        "titulo": "Você quer abrir as premissas e controlar o raciocínio.",
        "descricao": (
            "A Valoris deixa claro quais números sustentam o valuation e quais pontos ainda exigem dados externos."
        ),
        "foco": "Transparência antes de confiança.",
    },
}


ETAPAS_DEMO = [
    "1. Contexto",
    "2. Preço vs Valor",
    "3. Auditor Valoris",
    "4. Relatório",
    "5. Próximo passo",
]


def _fmt_moeda(valor: Any, simbolo: str = "R$") -> str:
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        numero = 0.0

    return f"{simbolo} {numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_percentual(valor: Any) -> str:
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        numero = 0.0

    return f"{numero:.1f}%"


def _calcular_preco_teto_simulado(
    preco_justo: float,
    margem_seguranca: float,
) -> float:
    return max(0.0, preco_justo * (1 - margem_seguranca / 100))


def _calcular_zona_simulada(
    preco_atual: float,
    preco_teto: float,
    preco_justo: float,
) -> Dict[str, str]:
    if preco_atual <= preco_teto:
        return {
            "zona": "Zona de oportunidade",
            "tom": "positivo",
            "leitura": (
                "O preço atual está dentro da faixa conservadora do modelo. "
                "Ainda assim, a decisão só deveria avançar após revisar tese, riscos e qualidade das premissas."
            ),
        }

    if preco_atual <= preco_justo:
        return {
            "zona": "Zona de atenção",
            "tom": "neutro",
            "leitura": (
                "O ativo ainda não parece absurdamente acima do valor estimado, mas está acima do preço-teto. "
                "A melhor atitude pode ser observar, revisar premissas e esperar margem melhor."
            ),
        }

    return {
        "zona": "Zona de paciência",
        "tom": "cautela",
        "leitura": (
            "O preço atual está acima do valor justo estimado. O risco de pagar caro aumenta e a decisão exige paciência."
        ),
    }


def _injetar_css_demo() -> None:
    st.markdown(
        """
        <style>
            .demo-hero {
                padding: clamp(1.15rem, 3vw, 2rem);
                border-radius: 30px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    radial-gradient(circle at top left, rgba(214, 181, 109, 0.24), transparent 30%),
                    radial-gradient(circle at bottom right, rgba(36, 128, 91, 0.24), transparent 34%),
                    linear-gradient(135deg, rgba(8, 15, 27, 0.99), rgba(5, 9, 18, 0.99));
                box-shadow: 0 18px 58px rgba(0, 0, 0, 0.31);
                margin-bottom: 1rem;
            }

            .demo-eyebrow {
                color: #d6b56d;
                font-size: 0.74rem;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                font-weight: 880;
                margin-bottom: 0.35rem;
            }

            .demo-title {
                color: #f4f7fb;
                font-size: clamp(1.75rem, 5.6vw, 3.2rem);
                font-weight: 950;
                line-height: 1.02;
                letter-spacing: -0.058em;
                margin-bottom: 0.55rem;
            }

            .demo-subtitle {
                color: rgba(244, 247, 251, 0.75);
                font-size: clamp(0.94rem, 2.2vw, 1.08rem);
                line-height: 1.56;
                max-width: 1020px;
            }

            .demo-grid-3 {
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 0.8rem;
                margin: 0.9rem 0;
            }

            .demo-grid-2 {
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 0.8rem;
                margin: 0.9rem 0;
            }

            .demo-card {
                padding: 1.02rem 1.06rem;
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background:
                    radial-gradient(circle at top right, rgba(214, 181, 109, 0.08), transparent 30%),
                    rgba(255, 255, 255, 0.034);
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.17);
                height: 100%;
            }

            .demo-kicker {
                color: #d6b56d;
                font-size: 0.72rem;
                letter-spacing: 0.11em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.4rem;
            }

            .demo-card-title {
                color: #f4f7fb;
                font-size: 1.08rem;
                font-weight: 880;
                letter-spacing: -0.026em;
                margin-bottom: 0.3rem;
            }

            .demo-card-value {
                color: #f4f7fb;
                font-size: 1.42rem;
                font-weight: 940;
                letter-spacing: -0.045em;
                margin-bottom: 0.25rem;
            }

            .demo-card-text {
                color: rgba(244, 247, 251, 0.68);
                font-size: 0.90rem;
                line-height: 1.50;
            }

            .demo-stage {
                padding: 1.05rem 1.08rem;
                border-radius: 24px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    linear-gradient(135deg, rgba(15, 23, 42, 0.93), rgba(30, 41, 59, 0.58));
                box-shadow: 0 14px 44px rgba(0, 0, 0, 0.24);
                margin: 0.9rem 0;
            }

            .demo-stage-title {
                color: #f4f7fb;
                font-size: clamp(1.18rem, 3vw, 1.65rem);
                font-weight: 920;
                line-height: 1.15;
                letter-spacing: -0.04em;
                margin-bottom: 0.35rem;
            }

            .demo-stage-text {
                color: rgba(244, 247, 251, 0.72);
                font-size: 0.93rem;
                line-height: 1.52;
            }

            .demo-note {
                padding: 0.92rem 0.98rem;
                border-radius: 17px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.90rem;
                line-height: 1.55;
                margin: 0.85rem 0;
            }

            .demo-small {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.82rem;
                line-height: 1.45;
            }

            @media (max-width: 900px) {
                .demo-grid-3,
                .demo-grid-2 {
                    grid-template-columns: 1fr;
                }

                .demo-hero {
                    border-radius: 22px;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _renderizar_hero_demo() -> None:
    st.markdown(
        f"""
        <div class="demo-hero">
            <div class="demo-eyebrow">Valoris • Demo guiada • v{VERSAO_DEMO_GUIADA_VALORIS}</div>
            <div class="demo-title">Veja a Valoris pensando sobre uma ação.</div>
            <div class="demo-subtitle">
                Em vez de jogar uma planilha na sua frente, a Valoris conduz você por uma leitura:
                preço, valor, margem de segurança, riscos e próximos passos.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _renderizar_cards_base() -> None:
    st.markdown(
        f"""
        <div class="demo-grid-3">
            <div class="demo-card">
                <div class="demo-kicker">Ativo exemplo</div>
                <div class="demo-card-value">{DEMO_ATIVO["ticker"]}</div>
                <div class="demo-card-text">{DEMO_ATIVO["empresa"]} • {DEMO_ATIVO["setor"]}</div>
            </div>
            <div class="demo-card">
                <div class="demo-kicker">Leitura atual</div>
                <div class="demo-card-value">{DEMO_ATIVO["status"]}</div>
                <div class="demo-card-text">O preço está acima do teto conservador, mas abaixo do valor justo estimado.</div>
            </div>
            <div class="demo-card">
                <div class="demo-kicker">Confiança da análise</div>
                <div class="demo-card-value">{DEMO_ATIVO["score_confianca"]}/100</div>
                <div class="demo-card-text">Útil como triagem, mas ainda exige revisão de dados e tese.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _renderizar_seletor_contexto(chave_contexto: str) -> Dict[str, str]:
    col_1, col_2 = st.columns([1, 1])

    with col_1:
        perfil = st.radio(
            "Escolha seu perfil",
            ["Iniciante", "Intermediário", "Avançado"],
            horizontal=False,
            key=f"demo_perfil_{chave_contexto}",
        )

    with col_2:
        etapa = st.selectbox(
            "Escolha a etapa da demonstração",
            ETAPAS_DEMO,
            key=f"demo_etapa_{chave_contexto}",
        )

    perfil_info = PERFIS_DEMO[perfil]

    st.markdown(
        f"""
        <div class="demo-stage">
            <div class="demo-kicker">Experiência para {perfil}</div>
            <div class="demo-stage-title">{perfil_info["titulo"]}</div>
            <div class="demo-stage-text">{perfil_info["descricao"]}</div>
            <div class="demo-small"><strong>Foco:</strong> {perfil_info["foco"]}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    registrar_evento_publico(
        evento="demo_interacao",
        origem="demo_guiada",
        contexto=chave_contexto,
        perfil=perfil,
        etapa=etapa,
        ticker=DEMO_ATIVO["ticker"],
        detalhe=f"Interação na demo: perfil={perfil}; etapa={etapa}",
    )

    return {
        "perfil": perfil,
        "etapa": etapa,
    }


def _renderizar_etapa_contexto() -> None:
    st.markdown(
        """
        <div class="demo-stage">
            <div class="demo-kicker">Etapa 01</div>
            <div class="demo-stage-title">Antes do cálculo, a Valoris define o contexto.</div>
            <div class="demo-stage-text">
                A análise não começa perguntando se você quer comprar. Ela começa perguntando
                se os dados fazem sentido e se a empresa está sendo avaliada com premissas conservadoras.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.info(
        "Nesta demonstração, usamos uma empresa fictícia. O objetivo é mostrar a lógica do produto, não avaliar um ativo real."
    )


def _renderizar_etapa_preco_valor(chave_contexto: str) -> None:
    preco_atual = DEMO_ATIVO["preco_atual"]
    preco_justo = DEMO_ATIVO["preco_justo"]

    margem = st.slider(
        "Teste a margem de segurança",
        min_value=10,
        max_value=50,
        value=int(DEMO_ATIVO["margem_seguranca"]),
        step=5,
        key=f"demo_margem_{chave_contexto}",
        help="A margem de segurança reduz o preço máximo aceitável para proteger contra erro de premissa.",
    )

    preco_teto = _calcular_preco_teto_simulado(preco_justo, margem)
    zona = _calcular_zona_simulada(preco_atual, preco_teto, preco_justo)

    st.markdown(
        f"""
        <div class="demo-grid-3">
            <div class="demo-card">
                <div class="demo-kicker">Preço atual</div>
                <div class="demo-card-value">{_fmt_moeda(preco_atual)}</div>
                <div class="demo-card-text">Quanto o mercado está cobrando agora.</div>
            </div>
            <div class="demo-card">
                <div class="demo-kicker">Preço justo</div>
                <div class="demo-card-value">{_fmt_moeda(preco_justo)}</div>
                <div class="demo-card-text">Valor estimado antes da margem de segurança.</div>
            </div>
            <div class="demo-card">
                <div class="demo-kicker">Preço-teto</div>
                <div class="demo-card-value">{_fmt_moeda(preco_teto)}</div>
                <div class="demo-card-text">Preço máximo com {_fmt_percentual(margem)} de segurança.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if zona["tom"] == "positivo":
        st.success(f"**{zona['zona']}** — {zona['leitura']}")
    elif zona["tom"] == "cautela":
        st.error(f"**{zona['zona']}** — {zona['leitura']}")
    else:
        st.warning(f"**{zona['zona']}** — {zona['leitura']}")

    progresso = min(max(preco_atual / max(preco_justo, 1), 0), 1)
    st.caption("Mapa intuitivo: quanto mais perto do valor justo, menor a folga de segurança.")
    st.progress(progresso)


def _renderizar_etapa_auditor() -> None:
    st.markdown(
        """
        <div class="demo-stage">
            <div class="demo-kicker">Etapa 03</div>
            <div class="demo-stage-title">O Auditor Valoris questiona o número.</div>
            <div class="demo-stage-text">
                Um valuation pode parecer elegante e ainda assim estar errado. Por isso a Valoris separa
                sinais verificados, pontos frágeis e dados que ainda precisam de confirmação.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_1, col_2 = st.columns(2)

    with col_1:
        st.success("**Verificado:** preço atual, preço justo e preço-teto foram comparados.")
        st.warning("**Atenção:** preço atual acima do teto conservador.")
        st.warning("**Pendente:** dividendos extraordinários ainda precisam de histórico automático.")

    with col_2:
        st.warning("**Pendente:** dívida, margens e ciclo setorial ainda exigem confirmação.")
        st.info("**Leitura:** análise útil como triagem, não como decisão final automática.")
        st.metric("Robustez fundamentalista", f"{DEMO_ATIVO['score_fundamentalista']}/100")


def _renderizar_etapa_relatorio() -> None:
    st.markdown(
        """
        <div class="demo-stage">
            <div class="demo-kicker">Etapa 04</div>
            <div class="demo-stage-title">A análise vira um relatório claro.</div>
            <div class="demo-stage-text">
                O objetivo é transformar números soltos em uma explicação revisável: zona de decisão,
                premissas, alertas, limitações e próximos passos.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="demo-note">
            <strong>Exemplo de conclusão:</strong> A Empresa Aurora está em zona de atenção.
            O preço atual está acima do teto conservador. A análise não deve virar compra automática.
            O próximo passo racional é acompanhar, revisar premissas e validar qualidade dos fundamentos.
        </div>
        """,
        unsafe_allow_html=True,
    )

    markdown_demo = """# Relatório Demo — Valoris

## Leitura principal

Empresa Aurora (AURA3) está em **Zona de atenção**.

O preço atual está acima do preço-teto conservador, mas ainda abaixo do preço justo estimado.

## Auditor Valoris

- Preço atual comparado com preço-teto.
- Margem de segurança aplicada.
- Pontos pendentes: dividendos extraordinários, dívida, margens e ciclo setorial.

## Conclusão

A análise é útil como triagem, mas ainda precisa de confirmação de tese e fundamentos.

Aviso: exemplo fictício e educacional.
"""

    if st.download_button(
        "Baixar exemplo de relatório demo",
        data=markdown_demo,
        file_name="relatorio_demo_valoris.md",
        mime="text/markdown",
        key="download_relatorio_demo_valoris",
    ):
        registrar_evento_publico(
            evento="relatorio_demo_baixado",
            origem="demo_guiada",
            contexto="relatorio_demo",
            ticker=DEMO_ATIVO["ticker"],
            detalhe="Usuário baixou o relatório demo.",
        )


def _renderizar_etapa_proximo_passo(mostrar_cta: bool, chave_contexto: str) -> None:
    st.markdown(
        """
        <div class="demo-stage">
            <div class="demo-kicker">Etapa 05</div>
            <div class="demo-stage-title">A decisão não termina no número.</div>
            <div class="demo-stage-text">
                A Valoris conduz o usuário para uma postura mais madura: revisar premissas,
                comparar cenários, registrar relatório e acompanhar o ativo com disciplina.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    proximos = [
        "Testar premissas mais conservadoras.",
        "Validar se lucro e caixa são recorrentes.",
        "Acompanhar preço até se aproximar do preço-teto.",
        "Entrar na lista beta para acompanhar a evolução da plataforma.",
    ]

    for item in proximos:
        st.success(f"**{item}**")

    if mostrar_cta:
        st.divider()
        renderizar_lista_espera_valoris(
            modo_admin=False,
            chave_contexto=f"demo_guiada_valoris_{chave_contexto}",
        )


def _renderizar_etapa(etapa: str, mostrar_cta: bool, chave_contexto: str) -> None:
    if etapa == "1. Contexto":
        _renderizar_etapa_contexto()
    elif etapa == "2. Preço vs Valor":
        _renderizar_etapa_preco_valor(chave_contexto)
    elif etapa == "3. Auditor Valoris":
        _renderizar_etapa_auditor()
    elif etapa == "4. Relatório":
        _renderizar_etapa_relatorio()
    else:
        _renderizar_etapa_proximo_passo(
            mostrar_cta=mostrar_cta,
            chave_contexto=chave_contexto,
        )


def renderizar_demo_guiada_valoris(
    modo_compacto: bool = False,
    mostrar_cta: bool = True,
    chave_contexto: str = "principal",
) -> None:
    """
    Renderiza a demonstração guiada da Valoris.

    modo_compacto=True é útil dentro da landing page.
    mostrar_cta=False evita repetir formulário de lead quando a landing já possui CTA.
    chave_contexto evita chaves duplicadas quando a demo aparece em mais de uma aba.
    """
    registrar_visualizacao_unica(
        chave=f"demo_guiada_{chave_contexto}",
        evento="demo_visualizada",
        origem="demo_guiada",
        contexto=chave_contexto,
        detalhe="Demonstração guiada visualizada.",
    )

    _injetar_css_demo()

    if not modo_compacto:
        _renderizar_hero_demo()
    else:
        st.markdown("### Experimente a Valoris em 60 segundos")
        st.caption(
            "Uma demonstração guiada para entender como a plataforma lê preço, valor, risco e próximos passos."
        )

    _renderizar_cards_base()

    contexto = _renderizar_seletor_contexto(chave_contexto=chave_contexto)

    etapa = contexto["etapa"]

    numero_etapa = ETAPAS_DEMO.index(etapa) + 1
    st.progress(numero_etapa / len(ETAPAS_DEMO))
    st.caption(f"Etapa {numero_etapa} de {len(ETAPAS_DEMO)}")

    _renderizar_etapa(
        etapa=etapa,
        mostrar_cta=mostrar_cta and not modo_compacto,
        chave_contexto=chave_contexto,
    )

    st.markdown(
        """
        <div class="demo-note">
            <strong>Importante:</strong> esta demonstração usa uma empresa fictícia.
            Ela serve para explicar a experiência, não para recomendar qualquer ativo.
        </div>
        """,
        unsafe_allow_html=True,
    )


def executar_autoteste_demo_guiada_valoris() -> List[Dict[str, str]]:
    preco_teto = _calcular_preco_teto_simulado(100, 25)
    zona = _calcular_zona_simulada(80, preco_teto, 100)

    return [
        {
            "teste": "versao_demo",
            "status": "OK" if VERSAO_DEMO_GUIADA_VALORIS == "3.8.45" else "FALHA",
            "detalhe": VERSAO_DEMO_GUIADA_VALORIS,
        },
        {
            "teste": "preco_teto_simulado",
            "status": "OK" if preco_teto == 75 else "FALHA",
            "detalhe": str(preco_teto),
        },
        {
            "teste": "zona_simulada",
            "status": "OK" if zona["zona"] in ["Zona de oportunidade", "Zona de atenção", "Zona de paciência"] else "FALHA",
            "detalhe": zona["zona"],
        },
    ]
