# copiloto_valoris.py

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

import streamlit as st

from analytics_publico_valoris import registrar_evento_publico, registrar_visualizacao_unica
from lista_espera_beta import renderizar_lista_espera_valoris


# ============================================================
# VALORIS
# v3.8.47 — Copiloto Valoris e Diagnóstico Personalizado
# ------------------------------------------------------------
# Este módulo cria uma experiência consultiva e educativa.
#
# Objetivo:
# - transformar a jornada pública em diagnóstico personalizado
# - guiar o usuário com perguntas simples
# - entregar um plano de uso da Valoris por perfil
# - gerar valor antes do cadastro
# - preparar a ponte entre educação, produto e monetização
# ============================================================


VERSAO_COPILOTO_VALORIS = "3.8.47"

CAMINHO_DIAGNOSTICOS_COPILOTO = Path("diagnosticos_copiloto_valoris.csv")

CAMPOS_DIAGNOSTICO = [
    "id",
    "data_registro",
    "sessao_id",
    "perfil",
    "dor_principal",
    "nivel_confianca",
    "maior_risco",
    "horizonte",
    "pontuacao",
    "classificacao",
    "plano_recomendado",
    "proxima_acao",
]


PERFIS_COPILOTO = [
    "Estou começando",
    "Já invisto",
    "Uso planilhas/ferramentas",
    "Quero analisar com mais profundidade",
]


DORES_COPILOTO = [
    "Tenho medo de comprar ação cara",
    "Não sei interpretar valuation",
    "Tenho dificuldade com balanços",
    "Compro por impulso ou narrativa",
    "Não sei montar uma tese",
    "Quero comparar ativos com mais clareza",
]


RISCOS_COPILOTO = [
    "Pagar caro demais",
    "Confiar em dividendos que não se repetem",
    "Ignorar dívida e alavancagem",
    "Usar premissas otimistas",
    "Comprar empresa boa em ciclo ruim",
    "Não saber quando esperar",
]


HORIZONTES_COPILOTO = [
    "Curto prazo — ainda fico ansioso com oscilação",
    "Médio prazo — quero acompanhar melhor",
    "Longo prazo — quero decidir com disciplina",
    "Ainda não tenho horizonte claro",
]


PLANOS_RECOMENDADOS = {
    "Base em formação": {
        "plano": "Trilha Valoris + Demonstração Guiada",
        "proxima_acao": (
            "Comece pela trilha educativa para entender preço, valor e margem. Depois use a demonstração guiada "
            "antes de preencher uma análise real."
        ),
    },
    "Investidor em evolução": {
        "plano": "Demonstração Guiada + Auditor Valoris",
        "proxima_acao": (
            "Use a demonstração para consolidar a lógica e depois rode uma análise com premissas conservadoras. "
            "Priorize o Auditor Valoris antes de olhar o status final."
        ),
    },
    "Usuário avançado": {
        "plano": "Valuation + Relatório Premium + Auditoria",
        "proxima_acao": (
            "Abra premissas, teste cenários, baixe o relatório e revise o que ainda não foi verificado: dividendos, "
            "dívida, margens, ciclo e tese."
        ),
    },
}


def _limpar_texto(valor: Any) -> str:
    if valor is None:
        return ""

    return str(valor).strip()


def _obter_sessao() -> str:
    if "sessao_publica_valoris" not in st.session_state:
        st.session_state["sessao_publica_valoris"] = str(uuid4())[:12]

    return st.session_state["sessao_publica_valoris"]


def _garantir_arquivo() -> None:
    if CAMINHO_DIAGNOSTICOS_COPILOTO.exists():
        return

    with CAMINHO_DIAGNOSTICOS_COPILOTO.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DIAGNOSTICO)
        escritor.writeheader()


def _registrar_diagnostico(diagnostico: Dict[str, Any]) -> None:
    try:
        _garantir_arquivo()

        registro = {
            "id": str(uuid4()),
            "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sessao_id": _obter_sessao(),
            "perfil": _limpar_texto(diagnostico.get("perfil")),
            "dor_principal": _limpar_texto(diagnostico.get("dor_principal")),
            "nivel_confianca": _limpar_texto(diagnostico.get("nivel_confianca")),
            "maior_risco": _limpar_texto(diagnostico.get("maior_risco")),
            "horizonte": _limpar_texto(diagnostico.get("horizonte")),
            "pontuacao": str(diagnostico.get("pontuacao", "")),
            "classificacao": _limpar_texto(diagnostico.get("classificacao")),
            "plano_recomendado": _limpar_texto(diagnostico.get("plano_recomendado")),
            "proxima_acao": _limpar_texto(diagnostico.get("proxima_acao")),
        }

        with CAMINHO_DIAGNOSTICOS_COPILOTO.open("a", newline="", encoding="utf-8") as arquivo:
            escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DIAGNOSTICO)
            escritor.writerow(registro)

    except Exception:
        return


def carregar_diagnosticos_copiloto() -> List[Dict[str, str]]:
    _garantir_arquivo()

    with CAMINHO_DIAGNOSTICOS_COPILOTO.open("r", newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        return list(leitor)


def gerar_csv_diagnosticos_copiloto() -> str:
    _garantir_arquivo()

    return CAMINHO_DIAGNOSTICOS_COPILOTO.read_text(encoding="utf-8")


def _calcular_diagnostico(
    perfil: str,
    dor_principal: str,
    nivel_confianca: int,
    maior_risco: str,
    horizonte: str,
) -> Dict[str, Any]:
    pontuacao = 40

    if perfil in ["Uso planilhas/ferramentas", "Quero analisar com mais profundidade"]:
        pontuacao += 20
    elif perfil == "Já invisto":
        pontuacao += 12
    else:
        pontuacao += 4

    if nivel_confianca >= 8:
        pontuacao += 16
    elif nivel_confianca >= 5:
        pontuacao += 8
    else:
        pontuacao -= 4

    if dor_principal in ["Compro por impulso ou narrativa", "Não sei interpretar valuation"]:
        pontuacao -= 4

    if maior_risco in ["Usar premissas otimistas", "Confiar em dividendos que não se repetem"]:
        pontuacao += 6

    if "Longo prazo" in horizonte:
        pontuacao += 8
    elif "Ainda não" in horizonte:
        pontuacao -= 6

    pontuacao = max(0, min(100, pontuacao))

    if pontuacao >= 78:
        classificacao = "Usuário avançado"
    elif pontuacao >= 55:
        classificacao = "Investidor em evolução"
    else:
        classificacao = "Base em formação"

    plano = PLANOS_RECOMENDADOS[classificacao]

    return {
        "perfil": perfil,
        "dor_principal": dor_principal,
        "nivel_confianca": str(nivel_confianca),
        "maior_risco": maior_risco,
        "horizonte": horizonte,
        "pontuacao": pontuacao,
        "classificacao": classificacao,
        "plano_recomendado": plano["plano"],
        "proxima_acao": plano["proxima_acao"],
    }


def _injetar_css_copiloto() -> None:
    st.markdown(
        """
        <style>
            .cop-hero {
                padding: clamp(1.18rem, 3vw, 2rem);
                border-radius: 30px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    radial-gradient(circle at top left, rgba(214, 181, 109, 0.25), transparent 30%),
                    radial-gradient(circle at bottom right, rgba(36, 128, 91, 0.24), transparent 34%),
                    linear-gradient(135deg, rgba(8, 15, 27, 0.99), rgba(5, 9, 18, 0.99));
                box-shadow: 0 18px 58px rgba(0, 0, 0, 0.31);
                margin-bottom: 1rem;
            }

            .cop-eyebrow {
                color: #d6b56d;
                font-size: 0.74rem;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                font-weight: 880;
                margin-bottom: 0.35rem;
            }

            .cop-title {
                color: #f4f7fb;
                font-size: clamp(1.75rem, 5.4vw, 3.1rem);
                font-weight: 950;
                line-height: 1.02;
                letter-spacing: -0.058em;
                margin-bottom: 0.55rem;
            }

            .cop-subtitle {
                color: rgba(244, 247, 251, 0.75);
                font-size: clamp(0.94rem, 2.2vw, 1.06rem);
                line-height: 1.56;
                max-width: 1020px;
            }

            .cop-grid-3 {
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 0.8rem;
                margin: 0.9rem 0;
            }

            .cop-grid-2 {
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 0.8rem;
                margin: 0.9rem 0;
            }

            .cop-card {
                padding: 1.02rem 1.06rem;
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background:
                    radial-gradient(circle at top right, rgba(214, 181, 109, 0.08), transparent 30%),
                    rgba(255, 255, 255, 0.034);
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.17);
                height: 100%;
            }

            .cop-kicker {
                color: #d6b56d;
                font-size: 0.72rem;
                letter-spacing: 0.11em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.4rem;
            }

            .cop-card-title {
                color: #f4f7fb;
                font-size: 1.08rem;
                font-weight: 880;
                letter-spacing: -0.026em;
                margin-bottom: 0.3rem;
            }

            .cop-card-value {
                color: #f4f7fb;
                font-size: 1.45rem;
                font-weight: 940;
                letter-spacing: -0.045em;
                margin-bottom: 0.25rem;
            }

            .cop-card-text {
                color: rgba(244, 247, 251, 0.68);
                font-size: 0.90rem;
                line-height: 1.50;
            }

            .cop-stage {
                padding: 1.05rem 1.08rem;
                border-radius: 24px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    linear-gradient(135deg, rgba(15, 23, 42, 0.93), rgba(30, 41, 59, 0.58));
                box-shadow: 0 14px 44px rgba(0, 0, 0, 0.24);
                margin: 0.9rem 0;
            }

            .cop-stage-title {
                color: #f4f7fb;
                font-size: clamp(1.18rem, 3vw, 1.65rem);
                font-weight: 920;
                line-height: 1.15;
                letter-spacing: -0.04em;
                margin-bottom: 0.35rem;
            }

            .cop-stage-text {
                color: rgba(244, 247, 251, 0.72);
                font-size: 0.93rem;
                line-height: 1.52;
            }

            .cop-note {
                padding: 0.92rem 0.98rem;
                border-radius: 17px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.90rem;
                line-height: 1.55;
                margin: 0.85rem 0;
            }

            @media (max-width: 900px) {
                .cop-grid-3,
                .cop-grid-2 {
                    grid-template-columns: 1fr;
                }

                .cop-hero {
                    border-radius: 22px;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _renderizar_hero() -> None:
    st.markdown(
        f"""
        <div class="cop-hero">
            <div class="cop-eyebrow">Valoris • Copiloto • v{VERSAO_COPILOTO_VALORIS}</div>
            <div class="cop-title">Receba um diagnóstico antes de usar a ferramenta.</div>
            <div class="cop-subtitle">
                O Copiloto Valoris faz perguntas simples, identifica sua maior fricção como investidor
                e recomenda o melhor caminho dentro da plataforma.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _renderizar_formulario(chave_contexto: str) -> Dict[str, Any]:
    col_1, col_2 = st.columns(2)

    with col_1:
        perfil = st.selectbox(
            "Qual perfil mais parece com você?",
            PERFIS_COPILOTO,
            key=f"cop_perfil_{chave_contexto}",
        )

        dor_principal = st.selectbox(
            "Qual sua maior dor hoje?",
            DORES_COPILOTO,
            key=f"cop_dor_{chave_contexto}",
        )

    with col_2:
        maior_risco = st.selectbox(
            "Qual risco você mais quer evitar?",
            RISCOS_COPILOTO,
            key=f"cop_risco_{chave_contexto}",
        )

        horizonte = st.selectbox(
            "Qual seu horizonte de investimento?",
            HORIZONTES_COPILOTO,
            key=f"cop_horizonte_{chave_contexto}",
        )

    nivel_confianca = st.slider(
        "De 0 a 10, quanta confiança você tem hoje para avaliar uma ação sozinho?",
        min_value=0,
        max_value=10,
        value=5,
        key=f"cop_confianca_{chave_contexto}",
    )

    return _calcular_diagnostico(
        perfil=perfil,
        dor_principal=dor_principal,
        nivel_confianca=nivel_confianca,
        maior_risco=maior_risco,
        horizonte=horizonte,
    )


def _renderizar_diagnostico(diagnostico: Dict[str, Any], chave_contexto: str) -> None:
    registrar_evento_publico(
        evento="copiloto_diagnostico_gerado",
        origem="copiloto_valoris",
        contexto=chave_contexto,
        perfil=diagnostico["perfil"],
        valor=diagnostico["pontuacao"],
        detalhe=f"Classificação: {diagnostico['classificacao']}; dor: {diagnostico['dor_principal']}",
    )

    if not st.session_state.get(f"copiloto_salvo_{chave_contexto}_{diagnostico['pontuacao']}"):
        _registrar_diagnostico(diagnostico)
        st.session_state[f"copiloto_salvo_{chave_contexto}_{diagnostico['pontuacao']}"] = True

    st.markdown(
        f"""
        <div class="cop-stage">
            <div class="cop-kicker">Diagnóstico Valoris</div>
            <div class="cop-stage-title">{diagnostico["classificacao"]}</div>
            <div class="cop-stage-text">
                Seu caminho recomendado é: <strong>{diagnostico["plano_recomendado"]}</strong>.
                A Valoris deve ser usada primeiro para reduzir ruído, organizar premissas e evitar decisões impulsivas.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="cop-grid-3">
            <div class="cop-card">
                <div class="cop-kicker">Maturidade estimada</div>
                <div class="cop-card-value">{diagnostico["pontuacao"]}/100</div>
                <div class="cop-card-text">Não mede inteligência. Mede prontidão para usar valuation com responsabilidade.</div>
            </div>
            <div class="cop-card">
                <div class="cop-kicker">Maior dor</div>
                <div class="cop-card-title">{diagnostico["dor_principal"]}</div>
                <div class="cop-card-text">Este ponto deve guiar sua primeira experiência dentro da Valoris.</div>
            </div>
            <div class="cop-card">
                <div class="cop-kicker">Risco prioritário</div>
                <div class="cop-card-title">{diagnostico["maior_risco"]}</div>
                <div class="cop-card-text">O Auditor Valoris deve ajudar você a revisar esse risco antes da decisão.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.progress(diagnostico["pontuacao"] / 100)

    st.info(f"**Próxima ação:** {diagnostico['proxima_acao']}")

    markdown = f"""# Diagnóstico Copiloto Valoris

Perfil: {diagnostico["perfil"]}  
Dor principal: {diagnostico["dor_principal"]}  
Risco prioritário: {diagnostico["maior_risco"]}  
Horizonte: {diagnostico["horizonte"]}  
Confiança atual: {diagnostico["nivel_confianca"]}/10  

## Resultado

Pontuação: {diagnostico["pontuacao"]}/100  
Classificação: {diagnostico["classificacao"]}  
Plano recomendado: {diagnostico["plano_recomendado"]}  

## Próxima ação

{diagnostico["proxima_acao"]}

Aviso: conteúdo educacional. Não representa recomendação de investimento.
"""

    st.download_button(
        "Baixar meu diagnóstico",
        data=markdown,
        file_name="diagnostico_copiloto_valoris.md",
        mime="text/markdown",
        key=f"download_copiloto_{chave_contexto}",
    )


def renderizar_copiloto_valoris(
    modo_compacto: bool = False,
    mostrar_cta: bool = True,
    chave_contexto: str = "principal",
) -> None:
    """
    Renderiza o Copiloto Valoris.
    """
    registrar_visualizacao_unica(
        chave=f"copiloto_valoris_{chave_contexto}",
        evento="copiloto_visualizado",
        origem="copiloto_valoris",
        contexto=chave_contexto,
        detalhe="Copiloto Valoris visualizado.",
    )

    _injetar_css_copiloto()

    if not modo_compacto:
        _renderizar_hero()
    else:
        st.markdown("### Copiloto Valoris: descubra seu melhor caminho")
        st.caption(
            "Responda perguntas rápidas e receba uma rota personalizada dentro da plataforma."
        )

    diagnostico = _renderizar_formulario(chave_contexto)

    _renderizar_diagnostico(diagnostico, chave_contexto)

    st.markdown(
        """
        <div class="cop-note">
            <strong>Ideia central:</strong> a Valoris não começa vendendo uma resposta.
            Ela começa entendendo o tipo de decisão que você precisa melhorar.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if mostrar_cta:
        st.divider()
        renderizar_lista_espera_valoris(
            modo_admin=False,
            chave_contexto=f"copiloto_valoris_{chave_contexto}",
        )


def renderizar_painel_copiloto_valoris() -> None:
    registros = carregar_diagnosticos_copiloto()

    st.markdown("## Painel do Copiloto Valoris")

    st.caption(
        f"v{VERSAO_COPILOTO_VALORIS} — acompanha dores, riscos e maturidade dos usuários."
    )

    if not registros:
        st.info("Ainda não há diagnósticos registrados.")
        return

    total = len(registros)
    pontuacoes = []

    for registro in registros:
        try:
            pontuacoes.append(float(registro.get("pontuacao", 0)))
        except (TypeError, ValueError):
            continue

    media = sum(pontuacoes) / len(pontuacoes) if pontuacoes else 0

    dores: Dict[str, int] = {}
    riscos: Dict[str, int] = {}

    for registro in registros:
        dor = registro.get("dor_principal", "N/D")
        risco = registro.get("maior_risco", "N/D")
        dores[dor] = dores.get(dor, 0) + 1
        riscos[risco] = riscos.get(risco, 0) + 1

    dor_mais_comum = sorted(dores.items(), key=lambda item: item[1], reverse=True)[0][0]
    risco_mais_comum = sorted(riscos.items(), key=lambda item: item[1], reverse=True)[0][0]

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Diagnósticos", total)

    with col_2:
        st.metric("Pontuação média", f"{media:.1f}/100")

    with col_3:
        st.metric("Dor mais comum", dor_mais_comum)

    with col_4:
        st.metric("Risco mais comum", risco_mais_comum)

    with st.expander("Últimos diagnósticos", expanded=False):
        for registro in reversed(registros[-20:]):
            with st.container(border=True):
                st.markdown(f"**{registro.get('classificacao', 'N/D')}**")
                st.caption(f"{registro.get('data_registro', 'N/D')} • {registro.get('perfil', 'N/D')}")
                st.markdown(f"**Dor:** {registro.get('dor_principal', 'N/D')}")
                st.markdown(f"**Risco:** {registro.get('maior_risco', 'N/D')}")
                st.markdown(f"**Plano:** {registro.get('plano_recomendado', 'N/D')}")

    st.download_button(
        "Baixar diagnósticos do copiloto (.csv)",
        data=gerar_csv_diagnosticos_copiloto(),
        file_name="diagnosticos_copiloto_valoris.csv",
        mime="text/csv",
        key="download_diagnosticos_copiloto_valoris",
    )


def executar_autoteste_copiloto_valoris() -> List[Dict[str, str]]:
    diagnostico = _calcular_diagnostico(
        perfil="Já invisto",
        dor_principal="Tenho medo de comprar ação cara",
        nivel_confianca=6,
        maior_risco="Pagar caro demais",
        horizonte="Longo prazo — quero decidir com disciplina",
    )

    return [
        {
            "teste": "versao_copiloto",
            "status": "OK" if VERSAO_COPILOTO_VALORIS == "3.8.47" else "FALHA",
            "detalhe": VERSAO_COPILOTO_VALORIS,
        },
        {
            "teste": "diagnostico",
            "status": "OK" if 0 <= diagnostico["pontuacao"] <= 100 else "FALHA",
            "detalhe": str(diagnostico["pontuacao"]),
        },
        {
            "teste": "plano_recomendado",
            "status": "OK" if diagnostico["plano_recomendado"] != "" else "FALHA",
            "detalhe": diagnostico["plano_recomendado"],
        },
    ]
