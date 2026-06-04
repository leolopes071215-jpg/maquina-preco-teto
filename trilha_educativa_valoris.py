# trilha_educativa_valoris.py

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
# v3.8.54.1 — Trilha Educativa com chaves únicas
# ------------------------------------------------------------
# Este módulo cria uma experiência inspirada em produtos
# product-led modernos: o usuário aprende fazendo.
#
# Objetivo:
# - transformar onboarding em aprendizado ativo
# - criar um "aha moment" antes do cadastro
# - gamificar sem viciar: progresso com responsabilidade
# - conduzir para lista beta e relatório
# - ensinar preço, valor, margem, auditoria e tese
# ============================================================


VERSAO_TRILHA_EDUCATIVA_VALORIS = "3.8.54.1"

CAMINHO_PROGRESSO_TRILHA = Path("progresso_trilha_valoris.csv")

CAMPOS_PROGRESSO_TRILHA = [
    "id",
    "data_registro",
    "sessao_id",
    "perfil",
    "missao",
    "resposta",
    "pontuacao",
    "classificacao",
    "proximo_passo",
]


PERFIS_TRILHA = {
    "Estou começando": {
        "titulo": "Aprender a não comprar no impulso",
        "descricao": (
            "Você vai entender a diferença entre preço atual, preço justo e preço-teto sem precisar dominar valuation."
        ),
        "foco": "Clareza e segurança emocional.",
    },
    "Já invisto": {
        "titulo": "Melhorar a qualidade da decisão",
        "descricao": (
            "Você vai revisar premissas, margem de segurança e riscos que podem deixar um valuation bonito, mas frágil."
        ),
        "foco": "Disciplina e auditoria.",
    },
    "Sou avançado": {
        "titulo": "Estressar a tese e controlar premissas",
        "descricao": (
            "Você vai pensar como um auditor: recorrência, caixa, alavancagem, ciclo, tese e limite do modelo."
        ),
        "foco": "Transparência e controle.",
    },
}


MISSOES_TRILHA = [
    {
        "id": "missao_1",
        "nome": "Missão 1 — Preço não é valor",
        "pergunta": "Uma ação caiu 30%. Isso significa que ela ficou barata?",
        "opcoes": [
            "Sim, se caiu bastante ficou barata",
            "Não necessariamente; preciso comparar preço com valor e fundamentos",
            "Depende apenas dos dividendos",
        ],
        "resposta_correta": "Não necessariamente; preciso comparar preço com valor e fundamentos",
        "explicacao": (
            "Preço é o que o mercado cobra. Valor é uma estimativa baseada em fundamentos. "
            "Uma queda pode criar oportunidade ou apenas refletir deterioração da empresa."
        ),
    },
    {
        "id": "missao_2",
        "nome": "Missão 2 — Margem de segurança",
        "pergunta": "Por que a Valoris usa preço-teto abaixo do preço justo?",
        "opcoes": [
            "Para tentar prever o preço exato da ação",
            "Para proteger contra erros de premissa e excesso de otimismo",
            "Para garantir lucro",
        ],
        "resposta_correta": "Para proteger contra erros de premissa e excesso de otimismo",
        "explicacao": (
            "A margem de segurança existe porque o valuation nunca é uma verdade absoluta. "
            "Ela cria folga para erros, ciclos ruins e premissas imperfeitas."
        ),
    },
    {
        "id": "missao_3",
        "nome": "Missão 3 — Dividendo pode enganar",
        "pergunta": "Uma empresa pagou dividendos enormes no último ano. Qual é o cuidado principal?",
        "opcoes": [
            "Projetar o mesmo dividendo para sempre",
            "Verificar se foi recorrente ou extraordinário",
            "Comprar antes que todo mundo veja",
        ],
        "resposta_correta": "Verificar se foi recorrente ou extraordinário",
        "explicacao": (
            "Dividendos extraordinários podem inflar preço-teto baseado em yield. "
            "A análise madura separa pagamento recorrente de evento fora do padrão."
        ),
    },
    {
        "id": "missao_4",
        "nome": "Missão 4 — Auditor de decisão",
        "pergunta": "Qual é a pergunta mais madura antes de comprar?",
        "opcoes": [
            "Essa ação vai subir amanhã?",
            "Essa decisão continua fazendo sentido se minhas premissas estiverem erradas?",
            "Todo mundo está falando bem dela?",
        ],
        "resposta_correta": "Essa decisão continua fazendo sentido se minhas premissas estiverem erradas?",
        "explicacao": (
            "A Valoris não tenta vender certeza. Ela ajuda a revisar se a decisão é robusta mesmo com incerteza."
        ),
    },
]


def _limpar_texto(valor: Any) -> str:
    if valor is None:
        return ""

    return str(valor).strip()


def _obter_sessao() -> str:
    if "sessao_publica_valoris" not in st.session_state:
        st.session_state["sessao_publica_valoris"] = str(uuid4())[:12]

    return st.session_state["sessao_publica_valoris"]


def _garantir_arquivo_progresso() -> None:
    if CAMINHO_PROGRESSO_TRILHA.exists():
        return

    with CAMINHO_PROGRESSO_TRILHA.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_PROGRESSO_TRILHA)
        escritor.writeheader()


def _registrar_progresso(
    perfil: str,
    missao: str,
    resposta: str,
    pontuacao: int,
    classificacao: str,
    proximo_passo: str,
) -> None:
    try:
        _garantir_arquivo_progresso()

        registro = {
            "id": str(uuid4()),
            "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sessao_id": _obter_sessao(),
            "perfil": _limpar_texto(perfil),
            "missao": _limpar_texto(missao),
            "resposta": _limpar_texto(resposta),
            "pontuacao": str(pontuacao),
            "classificacao": _limpar_texto(classificacao),
            "proximo_passo": _limpar_texto(proximo_passo),
        }

        with CAMINHO_PROGRESSO_TRILHA.open("a", newline="", encoding="utf-8") as arquivo:
            escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_PROGRESSO_TRILHA)
            escritor.writerow(registro)

    except Exception:
        return


def carregar_progresso_trilha() -> List[Dict[str, str]]:
    _garantir_arquivo_progresso()

    with CAMINHO_PROGRESSO_TRILHA.open("r", newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        return list(leitor)


def gerar_csv_progresso_trilha() -> str:
    _garantir_arquivo_progresso()

    return CAMINHO_PROGRESSO_TRILHA.read_text(encoding="utf-8")


def _injetar_css_trilha() -> None:
    st.markdown(
        """
        <style>
            .trilha-hero {
                padding: clamp(1.18rem, 3vw, 2rem);
                border-radius: 30px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    radial-gradient(circle at top left, rgba(214, 181, 109, 0.25), transparent 30%),
                    radial-gradient(circle at bottom right, rgba(74, 144, 226, 0.20), transparent 34%),
                    linear-gradient(135deg, rgba(8, 15, 27, 0.99), rgba(5, 9, 18, 0.99));
                box-shadow: 0 18px 58px rgba(0, 0, 0, 0.31);
                margin-bottom: 1rem;
            }

            .trilha-eyebrow {
                color: #d6b56d;
                font-size: 0.74rem;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                font-weight: 880;
                margin-bottom: 0.35rem;
            }

            .trilha-title {
                color: #f4f7fb;
                font-size: clamp(1.75rem, 5.4vw, 3.1rem);
                font-weight: 950;
                line-height: 1.02;
                letter-spacing: -0.058em;
                margin-bottom: 0.55rem;
            }

            .trilha-subtitle {
                color: rgba(244, 247, 251, 0.75);
                font-size: clamp(0.94rem, 2.2vw, 1.06rem);
                line-height: 1.56;
                max-width: 1020px;
            }

            .trilha-grid-3 {
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 0.8rem;
                margin: 0.9rem 0;
            }

            .trilha-card {
                padding: 1.02rem 1.06rem;
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background:
                    radial-gradient(circle at top right, rgba(214, 181, 109, 0.08), transparent 30%),
                    rgba(255, 255, 255, 0.034);
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.17);
                height: 100%;
            }

            .trilha-kicker {
                color: #d6b56d;
                font-size: 0.72rem;
                letter-spacing: 0.11em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.4rem;
            }

            .trilha-card-title {
                color: #f4f7fb;
                font-size: 1.08rem;
                font-weight: 880;
                letter-spacing: -0.026em;
                margin-bottom: 0.3rem;
            }

            .trilha-card-text {
                color: rgba(244, 247, 251, 0.68);
                font-size: 0.90rem;
                line-height: 1.50;
            }

            .trilha-stage {
                padding: 1.05rem 1.08rem;
                border-radius: 24px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    linear-gradient(135deg, rgba(15, 23, 42, 0.93), rgba(30, 41, 59, 0.58));
                box-shadow: 0 14px 44px rgba(0, 0, 0, 0.24);
                margin: 0.9rem 0;
            }

            .trilha-stage-title {
                color: #f4f7fb;
                font-size: clamp(1.18rem, 3vw, 1.65rem);
                font-weight: 920;
                line-height: 1.15;
                letter-spacing: -0.04em;
                margin-bottom: 0.35rem;
            }

            .trilha-stage-text {
                color: rgba(244, 247, 251, 0.72);
                font-size: 0.93rem;
                line-height: 1.52;
            }

            .trilha-note {
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
                .trilha-grid-3 {
                    grid-template-columns: 1fr;
                }

                .trilha-hero {
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
        <div class="trilha-hero">
            <div class="trilha-eyebrow">Valoris • Trilha educativa • v{VERSAO_TRILHA_EDUCATIVA_VALORIS}</div>
            <div class="trilha-title">Aprenda a decidir melhor antes de investir.</div>
            <div class="trilha-subtitle">
                Uma experiência rápida, interativa e didática para transformar valuation em raciocínio.
                A ideia é simples: aprender fazendo, sem promessa de lucro e sem call pronta.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _renderizar_cards_metodo() -> None:
    st.markdown(
        """
        <div class="trilha-grid-3">
            <div class="trilha-card">
                <div class="trilha-kicker">Produto-led</div>
                <div class="trilha-card-title">O usuário entende usando</div>
                <div class="trilha-card-text">A trilha mostra valor antes de pedir cadastro, assinatura ou confiança cega.</div>
            </div>
            <div class="trilha-card">
                <div class="trilha-kicker">Educação</div>
                <div class="trilha-card-title">Microlições aplicadas</div>
                <div class="trilha-card-text">Cada missão ensina uma decisão real: preço, valor, margem, dividendos e tese.</div>
            </div>
            <div class="trilha-card">
                <div class="trilha-kicker">Disciplina</div>
                <div class="trilha-card-title">Gamificação responsável</div>
                <div class="trilha-card-text">Progresso visual sem transformar investimento em jogo ou promessa de ganho fácil.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _classificar_pontuacao(pontos: int, total: int) -> Dict[str, str]:
    percentual = (pontos / total) * 100 if total > 0 else 0

    if percentual >= 90:
        return {
            "classificacao": "Mentalidade madura",
            "proximo_passo": "Você já entende o núcleo da Valoris. Avance para auditoria, relatório e tese.",
        }

    if percentual >= 60:
        return {
            "classificacao": "Boa base, ainda com pontos de atenção",
            "proximo_passo": "Revise as missões erradas e use a demonstração guiada para consolidar o raciocínio.",
        }

    return {
        "classificacao": "Base inicial em formação",
        "proximo_passo": "Comece pela diferença entre preço, valor e margem de segurança antes de decidir comprar qualquer ativo.",
    }


def _renderizar_perfil(chave_contexto: str) -> str:
    perfil = st.radio(
        "Qual trilha combina mais com você?",
        list(PERFIS_TRILHA.keys()),
        horizontal=True,
        key=f"trilha_perfil_valoris_{chave_contexto}",
    )

    dados = PERFIS_TRILHA[perfil]

    st.markdown(
        f"""
        <div class="trilha-stage">
            <div class="trilha-kicker">{perfil}</div>
            <div class="trilha-stage-title">{dados["titulo"]}</div>
            <div class="trilha-stage-text">{dados["descricao"]}</div>
            <div class="trilha-card-text"><strong>Foco:</strong> {dados["foco"]}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    return perfil


def _renderizar_missoes(perfil: str, chave_contexto: str) -> Dict[str, Any]:
    st.markdown("### Missões rápidas")

    pontos = 0
    respostas: List[Dict[str, Any]] = []

    for indice, missao in enumerate(MISSOES_TRILHA, start=1):
        with st.container(border=True):
            st.markdown(f"#### {missao['nome']}")
            st.caption(missao["pergunta"])

            resposta = st.radio(
                "Escolha uma resposta",
                missao["opcoes"],
                key=f"trilha_{missao['id']}_{perfil}_{chave_contexto}",
                label_visibility="collapsed",
            )

            acertou = resposta == missao["resposta_correta"]

            if acertou:
                pontos += 1
                st.success(f"Correto. {missao['explicacao']}")
            else:
                st.warning(f"Revisão necessária. {missao['explicacao']}")

            respostas.append(
                {
                    "missao": missao["nome"],
                    "resposta": resposta,
                    "acertou": acertou,
                }
            )

    total = len(MISSOES_TRILHA)
    leitura = _classificar_pontuacao(pontos, total)

    percentual = int((pontos / total) * 100) if total else 0

    st.divider()

    st.markdown("### Resultado da trilha")

    col_1, col_2, col_3 = st.columns(3)

    with col_1:
        st.metric("Pontuação", f"{pontos}/{total}")

    with col_2:
        st.metric("Aproveitamento", f"{percentual}%")

    with col_3:
        st.metric("Classificação", leitura["classificacao"])

    st.progress(percentual / 100)

    if percentual >= 90:
        st.success(f"**{leitura['classificacao']}** — {leitura['proximo_passo']}")
    elif percentual >= 60:
        st.warning(f"**{leitura['classificacao']}** — {leitura['proximo_passo']}")
    else:
        st.info(f"**{leitura['classificacao']}** — {leitura['proximo_passo']}")

    return {
        "pontos": pontos,
        "total": total,
        "percentual": percentual,
        "classificacao": leitura["classificacao"],
        "proximo_passo": leitura["proximo_passo"],
        "respostas": respostas,
    }


def _renderizar_proximas_acoes(resultado: Dict[str, Any], chave_contexto: str) -> None:
    st.markdown("### Próximas ações recomendadas")

    acoes = [
        "Abrir a Demonstração Guiada para ver a Valoris pensando em etapas.",
        "Testar uma análise de valuation com premissas conservadoras.",
        "Baixar um relatório e revisar o que ainda não foi verificado.",
        "Entrar na lista beta para acompanhar a evolução da plataforma.",
    ]

    for acao in acoes:
        st.success(f"**{acao}**")

    markdown = f"""# Resultado da Trilha Valoris

Pontuação: {resultado["pontos"]}/{resultado["total"]}  
Aproveitamento: {resultado["percentual"]}%  
Classificação: {resultado["classificacao"]}

Próximo passo:
{resultado["proximo_passo"]}

Aviso:
Esta trilha é educacional. Não representa recomendação de investimento.
"""

    st.download_button(
        "Baixar resultado da trilha",
        data=markdown,
        file_name="resultado_trilha_valoris.md",
        mime="text/markdown",
        key=f"download_resultado_trilha_valoris_{chave_contexto}",
    )


def renderizar_trilha_educativa_valoris(
    modo_compacto: bool = False,
    mostrar_cta: bool = True,
    chave_contexto: str = "principal",
) -> None:
    """
    Renderiza a trilha educativa da Valoris.
    """
    registrar_visualizacao_unica(
        chave=f"trilha_educativa_{chave_contexto}",
        evento="trilha_educativa_visualizada",
        origem="trilha_educativa",
        contexto=chave_contexto,
        detalhe="Trilha educativa visualizada.",
    )

    _injetar_css_trilha()

    if not modo_compacto:
        _renderizar_hero()
    else:
        st.markdown("### Trilha rápida: aprenda antes de analisar")
        st.caption(
            "Uma sequência curta para o usuário entender preço, valor, margem e auditoria antes de usar o valuation."
        )

    _renderizar_cards_metodo()

    perfil = _renderizar_perfil(chave_contexto=chave_contexto)

    resultado = _renderizar_missoes(
        perfil=perfil,
        chave_contexto=chave_contexto,
    )

    registrar_evento_publico(
        evento="trilha_educativa_concluida",
        origem="trilha_educativa",
        contexto=chave_contexto,
        perfil=perfil,
        valor=resultado["percentual"],
        detalhe=f"Classificação: {resultado['classificacao']}",
    )

    _registrar_progresso(
        perfil=perfil,
        missao="Trilha completa",
        resposta=f"{resultado['pontos']}/{resultado['total']}",
        pontuacao=resultado["percentual"],
        classificacao=resultado["classificacao"],
        proximo_passo=resultado["proximo_passo"],
    )

    st.divider()

    _renderizar_proximas_acoes(
        resultado=resultado,
        chave_contexto=chave_contexto,
    )

    if mostrar_cta:
        st.divider()
        renderizar_lista_espera_valoris(
            modo_admin=False,
            chave_contexto=f"trilha_educativa_{chave_contexto}",
        )

    st.markdown(
        """
        <div class="trilha-note">
            <strong>Regra Valoris:</strong> educação antes de ação. O objetivo não é fazer o usuário comprar mais rápido,
            mas pensar melhor antes de comprar.
        </div>
        """,
        unsafe_allow_html=True,
    )


def renderizar_painel_trilha_educativa_valoris() -> None:
    """
    Painel interno simples para acompanhar resultados da trilha.
    """
    registros = carregar_progresso_trilha()

    st.markdown("## Painel da Trilha Educativa")

    st.caption(
        f"v{VERSAO_TRILHA_EDUCATIVA_VALORIS} — acompanha pontuação e maturidade educacional dos usuários."
    )

    if not registros:
        st.info("Ainda não há registros de progresso da trilha.")
        return

    total = len(registros)
    pontuacoes = []

    for registro in registros:
        try:
            pontuacoes.append(float(registro.get("pontuacao", 0)))
        except (TypeError, ValueError):
            continue

    media = sum(pontuacoes) / len(pontuacoes) if pontuacoes else 0

    col_1, col_2, col_3 = st.columns(3)

    with col_1:
        st.metric("Registros", total)

    with col_2:
        st.metric("Pontuação média", f"{media:.1f}%")

    with col_3:
        st.metric("Última classificação", registros[-1].get("classificacao", "N/D"))

    with st.expander("Últimos resultados", expanded=False):
        for registro in reversed(registros[-20:]):
            with st.container(border=True):
                st.markdown(f"**{registro.get('perfil', 'N/D')}** — {registro.get('classificacao', 'N/D')}")
                st.caption(registro.get("data_registro", "N/D"))
                st.markdown(f"Pontuação: **{registro.get('pontuacao', 'N/D')}%**")
                st.markdown(f"Próximo passo: {registro.get('proximo_passo', 'N/D')}")

    st.download_button(
        "Baixar progresso da trilha (.csv)",
        data=gerar_csv_progresso_trilha(),
        file_name="progresso_trilha_valoris.csv",
        mime="text/csv",
        key="download_progresso_trilha_valoris",
    )


def executar_autoteste_trilha_educativa_valoris() -> List[Dict[str, str]]:
    leitura = _classificar_pontuacao(3, 4)

    return [
        {
            "teste": "versao_trilha",
            "status": "OK" if VERSAO_TRILHA_EDUCATIVA_VALORIS == "3.8.54.1" else "FALHA",
            "detalhe": VERSAO_TRILHA_EDUCATIVA_VALORIS,
        },
        {
            "teste": "missoes",
            "status": "OK" if len(MISSOES_TRILHA) >= 4 else "FALHA",
            "detalhe": str(len(MISSOES_TRILHA)),
        },
        {
            "teste": "classificacao",
            "status": "OK" if leitura["classificacao"] != "" else "FALHA",
            "detalhe": leitura["classificacao"],
        },
    ]
