# hub_ativacao_valoris.py

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
# v3.8.49 — Hub de Ativação e Progresso Público
# ------------------------------------------------------------
# Este módulo centraliza a jornada pública em um painel simples.
#
# Objetivo:
# - transformar várias abas em um caminho claro
# - mostrar progresso do usuário na experiência
# - reforçar o "aha moment" do produto
# - guiar para próximos passos sem parecer confuso
# - medir intenção e ativação antes da monetização
# ============================================================


VERSAO_HUB_ATIVACAO_VALORIS = "3.8.49"

CAMINHO_ATIVACAO_VALORIS = Path("ativacao_valoris.csv")

CAMPOS_ATIVACAO = [
    "id",
    "data_registro",
    "sessao_id",
    "perfil",
    "objetivo",
    "passo_foco",
    "score_ativacao",
    "classificacao",
    "proximo_passo",
]


PASSOS_ATIVACAO = [
    {
        "id": "copiloto",
        "numero": "01",
        "titulo": "Copiloto",
        "aba": "Copiloto",
        "descricao": "Descubra sua dor, risco principal e rota recomendada.",
        "valor": "Personalização",
    },
    {
        "id": "jornada",
        "numero": "02",
        "titulo": "Jornada",
        "aba": "Jornada",
        "descricao": "Receba o caminho certo dentro da Valoris.",
        "valor": "Direção",
    },
    {
        "id": "demo",
        "numero": "03",
        "titulo": "Demonstração",
        "aba": "Demonstração",
        "descricao": "Veja a Valoris pensando sobre uma ação fictícia.",
        "valor": "Aha moment",
    },
    {
        "id": "trilha",
        "numero": "04",
        "titulo": "Trilha Valoris",
        "aba": "Trilha Valoris",
        "descricao": "Aprenda preço, valor, margem e auditoria em missões rápidas.",
        "valor": "Educação",
    },
    {
        "id": "valuation",
        "numero": "05",
        "titulo": "Valuation",
        "aba": "Valuation",
        "descricao": "Rode uma análise com premissas conservadoras.",
        "valor": "Ferramenta",
    },
    {
        "id": "relatorio",
        "numero": "06",
        "titulo": "Relatórios",
        "aba": "Relatórios",
        "descricao": "Transforme análise em documento claro e revisável.",
        "valor": "Entrega",
    },
    {
        "id": "lista",
        "numero": "07",
        "titulo": "Lista Beta",
        "aba": "Convite Beta",
        "descricao": "Entre na lista para acompanhar a evolução da plataforma.",
        "valor": "Conversão",
    },
]


PERFIS_ATIVACAO = [
    "Quero entender a Valoris rapidamente",
    "Quero aprender antes de analisar",
    "Quero testar se a ferramenta é útil",
    "Quero avaliar se entraria no beta",
]


OBJETIVOS_ATIVACAO = [
    "Entender o produto em 2 minutos",
    "Sentir a experiência funcionando",
    "Aprender o básico de decisão",
    "Chegar em um relatório",
    "Entrar na lista beta",
]


def _limpar_texto(valor: Any) -> str:
    if valor is None:
        return ""

    return str(valor).strip()


def _obter_sessao() -> str:
    if "sessao_publica_valoris" not in st.session_state:
        st.session_state["sessao_publica_valoris"] = str(uuid4())[:12]

    return st.session_state["sessao_publica_valoris"]


def _garantir_arquivo() -> None:
    if CAMINHO_ATIVACAO_VALORIS.exists():
        return

    with CAMINHO_ATIVACAO_VALORIS.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_ATIVACAO)
        escritor.writeheader()


def _registrar_ativacao(dados: Dict[str, Any]) -> None:
    try:
        _garantir_arquivo()

        registro = {
            "id": str(uuid4()),
            "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sessao_id": _obter_sessao(),
            "perfil": _limpar_texto(dados.get("perfil")),
            "objetivo": _limpar_texto(dados.get("objetivo")),
            "passo_foco": _limpar_texto(dados.get("passo_foco")),
            "score_ativacao": str(dados.get("score_ativacao", "")),
            "classificacao": _limpar_texto(dados.get("classificacao")),
            "proximo_passo": _limpar_texto(dados.get("proximo_passo")),
        }

        with CAMINHO_ATIVACAO_VALORIS.open("a", newline="", encoding="utf-8") as arquivo:
            escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_ATIVACAO)
            escritor.writerow(registro)

    except Exception:
        return


def carregar_ativacoes_valoris() -> List[Dict[str, str]]:
    _garantir_arquivo()

    with CAMINHO_ATIVACAO_VALORIS.open("r", newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        return list(leitor)


def gerar_csv_ativacoes_valoris() -> str:
    _garantir_arquivo()

    return CAMINHO_ATIVACAO_VALORIS.read_text(encoding="utf-8")


def _obter_passos_marcados() -> Dict[str, bool]:
    if "passos_ativacao_valoris" not in st.session_state:
        st.session_state["passos_ativacao_valoris"] = {}

    return st.session_state["passos_ativacao_valoris"]


def _calcular_score_ativacao(passos_marcados: Dict[str, bool]) -> int:
    total = len(PASSOS_ATIVACAO)
    concluidos = len([item for item in passos_marcados.values() if item])

    if total <= 0:
        return 0

    return int(round((concluidos / total) * 100))


def _classificar_ativacao(score: int) -> Dict[str, str]:
    if score >= 85:
        return {
            "classificacao": "Usuário altamente ativado",
            "proximo_passo": "Conduzir para oferta beta ou conversa direta com o fundador.",
        }

    if score >= 55:
        return {
            "classificacao": "Usuário engajado",
            "proximo_passo": "Levar para relatório, lista beta e convite fundador.",
        }

    if score >= 25:
        return {
            "classificacao": "Interesse inicial",
            "proximo_passo": "Guiar para Copiloto, Demonstração e Trilha Valoris.",
        }

    return {
        "classificacao": "Primeiro contato",
        "proximo_passo": "Mostrar valor em poucos segundos com a landing e o Copiloto.",
    }


def _sugerir_passo_foco(objetivo: str, passos_marcados: Dict[str, bool]) -> Dict[str, str]:
    if objetivo == "Entender o produto em 2 minutos":
        prioridade = ["copiloto", "demo", "lista"]
    elif objetivo == "Sentir a experiência funcionando":
        prioridade = ["demo", "jornada", "valuation"]
    elif objetivo == "Aprender o básico de decisão":
        prioridade = ["trilha", "demo", "relatorio"]
    elif objetivo == "Chegar em um relatório":
        prioridade = ["valuation", "relatorio", "lista"]
    else:
        prioridade = ["copiloto", "jornada", "lista"]

    for passo_id in prioridade:
        if not passos_marcados.get(passo_id, False):
            for passo in PASSOS_ATIVACAO:
                if passo["id"] == passo_id:
                    return passo

    for passo in PASSOS_ATIVACAO:
        if not passos_marcados.get(passo["id"], False):
            return passo

    return PASSOS_ATIVACAO[-1]


def _injetar_css_hub() -> None:
    st.markdown(
        """
        <style>
            .hub-hero {
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

            .hub-eyebrow {
                color: #d6b56d;
                font-size: 0.74rem;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                font-weight: 880;
                margin-bottom: 0.35rem;
            }

            .hub-title {
                color: #f4f7fb;
                font-size: clamp(1.75rem, 5.4vw, 3.1rem);
                font-weight: 950;
                line-height: 1.02;
                letter-spacing: -0.058em;
                margin-bottom: 0.55rem;
            }

            .hub-subtitle {
                color: rgba(244, 247, 251, 0.75);
                font-size: clamp(0.94rem, 2.2vw, 1.06rem);
                line-height: 1.56;
                max-width: 1020px;
            }

            .hub-grid-3 {
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 0.8rem;
                margin: 0.9rem 0;
            }

            .hub-card {
                padding: 1.02rem 1.06rem;
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background:
                    radial-gradient(circle at top right, rgba(214, 181, 109, 0.08), transparent 30%),
                    rgba(255, 255, 255, 0.034);
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.17);
                height: 100%;
            }

            .hub-kicker {
                color: #d6b56d;
                font-size: 0.72rem;
                letter-spacing: 0.11em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.4rem;
            }

            .hub-card-title {
                color: #f4f7fb;
                font-size: 1.08rem;
                font-weight: 880;
                letter-spacing: -0.026em;
                margin-bottom: 0.3rem;
            }

            .hub-card-value {
                color: #f4f7fb;
                font-size: 1.48rem;
                font-weight: 940;
                letter-spacing: -0.045em;
                margin-bottom: 0.25rem;
            }

            .hub-card-text {
                color: rgba(244, 247, 251, 0.68);
                font-size: 0.90rem;
                line-height: 1.50;
            }

            .hub-stage {
                padding: 1.05rem 1.08rem;
                border-radius: 24px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    linear-gradient(135deg, rgba(15, 23, 42, 0.93), rgba(30, 41, 59, 0.58));
                box-shadow: 0 14px 44px rgba(0, 0, 0, 0.24);
                margin: 0.9rem 0;
            }

            .hub-stage-title {
                color: #f4f7fb;
                font-size: clamp(1.18rem, 3vw, 1.65rem);
                font-weight: 920;
                line-height: 1.15;
                letter-spacing: -0.04em;
                margin-bottom: 0.35rem;
            }

            .hub-stage-text {
                color: rgba(244, 247, 251, 0.72);
                font-size: 0.93rem;
                line-height: 1.52;
            }

            .hub-note {
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
                .hub-grid-3 {
                    grid-template-columns: 1fr;
                }

                .hub-hero {
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
        <div class="hub-hero">
            <div class="hub-eyebrow">Valoris • Hub de ativação • v{VERSAO_HUB_ATIVACAO_VALORIS}</div>
            <div class="hub-title">Seu painel de progresso na Valoris.</div>
            <div class="hub-subtitle">
                Uma plataforma moderna não deve deixar o usuário perdido. Este hub mostra onde você está,
                o que já explorou e qual próximo passo faz mais sentido.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _renderizar_configuracao(chave_contexto: str) -> Dict[str, str]:
    col_1, col_2 = st.columns(2)

    with col_1:
        perfil = st.selectbox(
            "Qual intenção mais combina com você agora?",
            PERFIS_ATIVACAO,
            key=f"hub_perfil_{chave_contexto}",
        )

    with col_2:
        objetivo = st.selectbox(
            "Qual objetivo você quer cumprir?",
            OBJETIVOS_ATIVACAO,
            key=f"hub_objetivo_{chave_contexto}",
        )

    return {
        "perfil": perfil,
        "objetivo": objetivo,
    }


def _renderizar_passos(chave_contexto: str) -> Dict[str, bool]:
    passos_marcados = _obter_passos_marcados()

    st.markdown("### Checklist de ativação")

    for passo in PASSOS_ATIVACAO:
        valor_atual = bool(passos_marcados.get(passo["id"], False))

        novo_valor = st.checkbox(
            f"{passo['numero']} — {passo['titulo']} ({passo['aba']})",
            value=valor_atual,
            key=f"hub_check_{passo['id']}_{chave_contexto}",
            help=passo["descricao"],
        )

        passos_marcados[passo["id"]] = novo_valor

        with st.container(border=True):
            st.markdown(f"**{passo['titulo']}** — {passo['valor']}")
            st.caption(f"Aba: {passo['aba']}")
            st.markdown(passo["descricao"])

    st.session_state["passos_ativacao_valoris"] = passos_marcados

    return passos_marcados


def _renderizar_resumo(
    perfil: str,
    objetivo: str,
    passos_marcados: Dict[str, bool],
    chave_contexto: str,
) -> Dict[str, Any]:
    score = _calcular_score_ativacao(passos_marcados)
    classificacao = _classificar_ativacao(score)
    passo_foco = _sugerir_passo_foco(objetivo, passos_marcados)

    concluidos = len([item for item in passos_marcados.values() if item])
    total = len(PASSOS_ATIVACAO)

    st.markdown(
        f"""
        <div class="hub-stage">
            <div class="hub-kicker">Resumo da ativação</div>
            <div class="hub-stage-title">{classificacao["classificacao"]}</div>
            <div class="hub-stage-text">
                Você concluiu <strong>{concluidos}/{total}</strong> passos da jornada pública.
                O próximo foco recomendado é: <strong>{passo_foco["titulo"]}</strong>.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="hub-grid-3">
            <div class="hub-card">
                <div class="hub-kicker">Score de ativação</div>
                <div class="hub-card-value">{score}/100</div>
                <div class="hub-card-text">Mede o quanto você já sentiu o produto funcionando.</div>
            </div>
            <div class="hub-card">
                <div class="hub-kicker">Próximo módulo</div>
                <div class="hub-card-title">{passo_foco["aba"]}</div>
                <div class="hub-card-text">{passo_foco["descricao"]}</div>
            </div>
            <div class="hub-card">
                <div class="hub-kicker">Objetivo atual</div>
                <div class="hub-card-title">{objetivo}</div>
                <div class="hub-card-text">A jornada deve servir ao objetivo do usuário, não ao mapa interno do produto.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.progress(score / 100)

    st.info(f"**Próxima ação:** {classificacao['proximo_passo']}")

    dados = {
        "perfil": perfil,
        "objetivo": objetivo,
        "passo_foco": passo_foco["titulo"],
        "score_ativacao": score,
        "classificacao": classificacao["classificacao"],
        "proximo_passo": classificacao["proximo_passo"],
    }

    registrar_evento_publico(
        evento="hub_ativacao_atualizado",
        origem="hub_ativacao",
        contexto=chave_contexto,
        perfil=perfil,
        valor=score,
        detalhe=f"Objetivo: {objetivo}; foco: {passo_foco['titulo']}",
    )

    chave_salva = f"hub_ativacao_salvo_{chave_contexto}_{score}_{passo_foco['id']}"

    if not st.session_state.get(chave_salva):
        _registrar_ativacao(dados)
        st.session_state[chave_salva] = True

    return dados


def _renderizar_download(dados: Dict[str, Any], passos_marcados: Dict[str, bool], chave_contexto: str) -> None:
    linhas = []

    for passo in PASSOS_ATIVACAO:
        status = "Concluído" if passos_marcados.get(passo["id"], False) else "Pendente"
        linhas.append(
            f"- {passo['numero']} — {passo['titulo']} ({passo['aba']}): {status}. {passo['descricao']}"
        )

    markdown = f"""# Hub de Ativação Valoris

Perfil/intenção: {dados["perfil"]}  
Objetivo: {dados["objetivo"]}  
Score de ativação: {dados["score_ativacao"]}/100  
Classificação: {dados["classificacao"]}  
Próximo foco: {dados["passo_foco"]}  

## Próxima ação

{dados["proximo_passo"]}

## Checklist

{chr(10).join(linhas)}

Aviso: conteúdo educacional. Não representa recomendação de investimento.
"""

    st.download_button(
        "Baixar meu progresso",
        data=markdown,
        file_name="hub_ativacao_valoris.md",
        mime="text/markdown",
        key=f"download_hub_ativacao_{chave_contexto}",
    )


def renderizar_hub_ativacao_valoris(
    modo_compacto: bool = False,
    mostrar_cta: bool = True,
    chave_contexto: str = "principal",
) -> None:
    registrar_visualizacao_unica(
        chave=f"hub_ativacao_{chave_contexto}",
        evento="hub_ativacao_visualizado",
        origem="hub_ativacao",
        contexto=chave_contexto,
        detalhe="Hub de ativação visualizado.",
    )

    _injetar_css_hub()

    if not modo_compacto:
        _renderizar_hero()
    else:
        st.markdown("### Hub de ativação")
        st.caption(
            "Um painel simples para o usuário saber o que já viu e qual próximo passo seguir."
        )

    configuracao = _renderizar_configuracao(chave_contexto)

    passos_marcados = _renderizar_passos(chave_contexto)

    dados = _renderizar_resumo(
        perfil=configuracao["perfil"],
        objetivo=configuracao["objetivo"],
        passos_marcados=passos_marcados,
        chave_contexto=chave_contexto,
    )

    _renderizar_download(
        dados=dados,
        passos_marcados=passos_marcados,
        chave_contexto=chave_contexto,
    )

    st.markdown(
        """
        <div class="hub-note">
            <strong>Princípio Valoris:</strong> o usuário não deve navegar por tentativa e erro.
            A plataforma precisa orientar, educar e conduzir até o momento de valor.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if mostrar_cta:
        st.divider()
        renderizar_lista_espera_valoris(
            modo_admin=False,
            chave_contexto=f"hub_ativacao_{chave_contexto}",
        )


def renderizar_painel_hub_ativacao_valoris() -> None:
    registros = carregar_ativacoes_valoris()

    st.markdown("## Painel do Hub de Ativação")

    st.caption(
        f"v{VERSAO_HUB_ATIVACAO_VALORIS} — acompanha ativação, progresso e próximo foco dos usuários."
    )

    if not registros:
        st.info("Ainda não há registros de ativação.")
        return

    scores = []

    for registro in registros:
        try:
            scores.append(float(registro.get("score_ativacao", 0)))
        except (TypeError, ValueError):
            continue

    media = sum(scores) / len(scores) if scores else 0

    focos: Dict[str, int] = {}
    objetivos: Dict[str, int] = {}

    for registro in registros:
        foco = registro.get("passo_foco", "N/D")
        objetivo = registro.get("objetivo", "N/D")
        focos[foco] = focos.get(foco, 0) + 1
        objetivos[objetivo] = objetivos.get(objetivo, 0) + 1

    foco_mais_comum = sorted(focos.items(), key=lambda item: item[1], reverse=True)[0][0]
    objetivo_mais_comum = sorted(objetivos.items(), key=lambda item: item[1], reverse=True)[0][0]

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Registros", len(registros))

    with col_2:
        st.metric("Score médio", f"{media:.1f}/100")

    with col_3:
        st.metric("Foco mais comum", foco_mais_comum)

    with col_4:
        st.metric("Objetivo dominante", objetivo_mais_comum)

    with st.expander("Últimas ativações", expanded=False):
        for registro in reversed(registros[-20:]):
            with st.container(border=True):
                st.markdown(f"**{registro.get('classificacao', 'N/D')}**")
                st.caption(f"{registro.get('data_registro', 'N/D')} • {registro.get('perfil', 'N/D')}")
                st.markdown(f"**Score:** {registro.get('score_ativacao', 'N/D')}/100")
                st.markdown(f"**Objetivo:** {registro.get('objetivo', 'N/D')}")
                st.markdown(f"**Próximo foco:** {registro.get('passo_foco', 'N/D')}")

    st.download_button(
        "Baixar ativações (.csv)",
        data=gerar_csv_ativacoes_valoris(),
        file_name="ativacao_valoris.csv",
        mime="text/csv",
        key="download_ativacoes_valoris",
    )


def executar_autoteste_hub_ativacao_valoris() -> List[Dict[str, str]]:
    score = _calcular_score_ativacao(
        {
            "copiloto": True,
            "jornada": True,
            "demo": False,
            "trilha": False,
            "valuation": False,
            "relatorio": False,
            "lista": False,
        }
    )

    classificacao = _classificar_ativacao(score)

    return [
        {
            "teste": "versao_hub",
            "status": "OK" if VERSAO_HUB_ATIVACAO_VALORIS == "3.8.49" else "FALHA",
            "detalhe": VERSAO_HUB_ATIVACAO_VALORIS,
        },
        {
            "teste": "score",
            "status": "OK" if 0 <= score <= 100 else "FALHA",
            "detalhe": str(score),
        },
        {
            "teste": "classificacao",
            "status": "OK" if classificacao["classificacao"] != "" else "FALHA",
            "detalhe": classificacao["classificacao"],
        },
    ]
