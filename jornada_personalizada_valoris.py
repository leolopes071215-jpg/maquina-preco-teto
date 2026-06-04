# jornada_personalizada_valoris.py

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
# v3.8.48 — Jornada Personalizada Pós-Diagnóstico
# ------------------------------------------------------------
# Este módulo transforma o diagnóstico do usuário em uma rota
# clara dentro da plataforma.
#
# Objetivo:
# - reduzir confusão entre abas
# - guiar o usuário para o próximo melhor passo
# - conectar Copiloto, Trilha, Demonstração, Valuation e Relatório
# - aumentar ativação e conversão da lista beta
# - criar sensação de produto inteligente e orientado
# ============================================================


VERSAO_JORNADA_PERSONALIZADA_VALORIS = "3.8.48"

CAMINHO_JORNADAS_VALORIS = Path("jornadas_personalizadas_valoris.csv")

CAMPOS_JORNADA = [
    "id",
    "data_registro",
    "sessao_id",
    "perfil",
    "objetivo",
    "bloqueio",
    "tempo_disponivel",
    "rota_recomendada",
    "prioridade",
    "proximo_passo",
]


PERFIS_JORNADA = [
    "Iniciante",
    "Investidor em evolução",
    "Usuário avançado",
]


OBJETIVOS_JORNADA = [
    "Entender se estou pagando caro",
    "Aprender valuation sem economês",
    "Auditar premissas e riscos",
    "Gerar um relatório organizado",
    "Entrar no beta fundador",
]


BLOQUEIOS_JORNADA = [
    "Não sei por onde começar",
    "Tenho pouco tempo",
    "Tenho medo de errar premissas",
    "Não confio em ferramenta caixa-preta",
    "Quero ver valor antes de deixar contato",
]


TEMPOS_DISPONIVEIS = [
    "Tenho 2 minutos",
    "Tenho 5 minutos",
    "Tenho 15 minutos",
    "Quero explorar tudo",
]


ROTAS_VALORIS = {
    "rota_clareza": {
        "nome": "Rota Clareza",
        "prioridade": "Entender antes de analisar",
        "passos": [
            {
                "titulo": "Comece pela Trilha Valoris",
                "aba": "Trilha Valoris",
                "acao": "Complete as missões sobre preço, valor e margem.",
                "por_que": "Isso reduz ansiedade e cria base antes do valuation.",
            },
            {
                "titulo": "Veja a Demonstração Guiada",
                "aba": "Demonstração",
                "acao": "Explore a empresa fictícia e altere a margem de segurança.",
                "por_que": "Você sente a lógica da Valoris sem risco de interpretar um ativo real.",
            },
            {
                "titulo": "Entre na lista beta",
                "aba": "Convite Beta",
                "acao": "Deixe contato se a experiência fez sentido.",
                "por_que": "Você acompanha melhorias e ajuda a moldar o produto.",
            },
        ],
    },
    "rota_auditoria": {
        "nome": "Rota Auditoria",
        "prioridade": "Revisar decisão antes de agir",
        "passos": [
            {
                "titulo": "Use o Copiloto",
                "aba": "Copiloto",
                "acao": "Identifique sua dor, risco principal e maturidade.",
                "por_que": "A Valoris recomenda uma rota mais precisa quando entende seu contexto.",
            },
            {
                "titulo": "Rode um valuation conservador",
                "aba": "Valuation",
                "acao": "Use premissas duras, margem adequada e compare preço atual com preço-teto.",
                "por_que": "O número só é útil se as premissas forem honestas.",
            },
            {
                "titulo": "Abra o Auditor Valoris",
                "aba": "Início",
                "acao": "Revise o que sustenta e o que enfraquece a análise.",
                "por_que": "A decisão madura começa quando você questiona o próprio valuation.",
            },
            {
                "titulo": "Baixe o relatório",
                "aba": "Relatórios",
                "acao": "Gere o Relatório Valoris Premium.",
                "por_que": "Documentar a decisão ajuda a reduzir impulso e revisar depois.",
            },
        ],
    },
    "rota_profunda": {
        "nome": "Rota Profunda",
        "prioridade": "Controlar premissas e tese",
        "passos": [
            {
                "titulo": "Comece pelo Copiloto",
                "aba": "Copiloto",
                "acao": "Mapeie dor, risco e horizonte.",
                "por_que": "Mesmo usuários avançados precisam saber qual problema estão tentando resolver.",
            },
            {
                "titulo": "Analise com premissas abertas",
                "aba": "Valuation",
                "acao": "Teste múltiplos, margem, lucro sustentável e fluxo de caixa.",
                "por_que": "A qualidade da análise depende da qualidade das premissas.",
            },
            {
                "titulo": "Use o relatório como tese",
                "aba": "Relatórios",
                "acao": "Baixe e revise a análise como se fosse um memorando de decisão.",
                "por_que": "A tese precisa sobreviver fora da tela do app.",
            },
            {
                "titulo": "Acompanhe evolução",
                "aba": "Oferta Beta",
                "acao": "Entre no beta fundador se quiser participar da construção.",
                "por_que": "O produto futuro deve priorizar usuários que sabem exigir transparência.",
            },
        ],
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
    if CAMINHO_JORNADAS_VALORIS.exists():
        return

    with CAMINHO_JORNADAS_VALORIS.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_JORNADA)
        escritor.writeheader()


def _registrar_jornada(jornada: Dict[str, Any]) -> None:
    try:
        _garantir_arquivo()

        registro = {
            "id": str(uuid4()),
            "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sessao_id": _obter_sessao(),
            "perfil": _limpar_texto(jornada.get("perfil")),
            "objetivo": _limpar_texto(jornada.get("objetivo")),
            "bloqueio": _limpar_texto(jornada.get("bloqueio")),
            "tempo_disponivel": _limpar_texto(jornada.get("tempo_disponivel")),
            "rota_recomendada": _limpar_texto(jornada.get("rota_recomendada")),
            "prioridade": _limpar_texto(jornada.get("prioridade")),
            "proximo_passo": _limpar_texto(jornada.get("proximo_passo")),
        }

        with CAMINHO_JORNADAS_VALORIS.open("a", newline="", encoding="utf-8") as arquivo:
            escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_JORNADA)
            escritor.writerow(registro)

    except Exception:
        return


def carregar_jornadas_personalizadas() -> List[Dict[str, str]]:
    _garantir_arquivo()

    with CAMINHO_JORNADAS_VALORIS.open("r", newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        return list(leitor)


def gerar_csv_jornadas_personalizadas() -> str:
    _garantir_arquivo()

    return CAMINHO_JORNADAS_VALORIS.read_text(encoding="utf-8")


def _escolher_rota(
    perfil: str,
    objetivo: str,
    bloqueio: str,
    tempo_disponivel: str,
) -> str:
    if perfil == "Iniciante":
        return "rota_clareza"

    if "Aprender" in objetivo or "por onde começar" in bloqueio:
        return "rota_clareza"

    if "caixa-preta" in bloqueio or "Auditar" in objetivo or "premissas" in bloqueio:
        return "rota_auditoria"

    if perfil == "Usuário avançado":
        return "rota_profunda"

    if tempo_disponivel == "Tenho 2 minutos":
        return "rota_clareza"

    return "rota_auditoria"


def _montar_jornada(
    perfil: str,
    objetivo: str,
    bloqueio: str,
    tempo_disponivel: str,
) -> Dict[str, Any]:
    rota_id = _escolher_rota(
        perfil=perfil,
        objetivo=objetivo,
        bloqueio=bloqueio,
        tempo_disponivel=tempo_disponivel,
    )

    rota = ROTAS_VALORIS[rota_id]

    return {
        "perfil": perfil,
        "objetivo": objetivo,
        "bloqueio": bloqueio,
        "tempo_disponivel": tempo_disponivel,
        "rota_id": rota_id,
        "rota_recomendada": rota["nome"],
        "prioridade": rota["prioridade"],
        "passos": rota["passos"],
        "proximo_passo": rota["passos"][0]["titulo"],
    }


def _injetar_css_jornada() -> None:
    st.markdown(
        """
        <style>
            .jor-hero {
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

            .jor-eyebrow {
                color: #d6b56d;
                font-size: 0.74rem;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                font-weight: 880;
                margin-bottom: 0.35rem;
            }

            .jor-title {
                color: #f4f7fb;
                font-size: clamp(1.75rem, 5.4vw, 3.1rem);
                font-weight: 950;
                line-height: 1.02;
                letter-spacing: -0.058em;
                margin-bottom: 0.55rem;
            }

            .jor-subtitle {
                color: rgba(244, 247, 251, 0.75);
                font-size: clamp(0.94rem, 2.2vw, 1.06rem);
                line-height: 1.56;
                max-width: 1020px;
            }

            .jor-grid-3 {
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 0.8rem;
                margin: 0.9rem 0;
            }

            .jor-card {
                padding: 1.02rem 1.06rem;
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background:
                    radial-gradient(circle at top right, rgba(214, 181, 109, 0.08), transparent 30%),
                    rgba(255, 255, 255, 0.034);
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.17);
                height: 100%;
            }

            .jor-kicker {
                color: #d6b56d;
                font-size: 0.72rem;
                letter-spacing: 0.11em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.4rem;
            }

            .jor-card-title {
                color: #f4f7fb;
                font-size: 1.08rem;
                font-weight: 880;
                letter-spacing: -0.026em;
                margin-bottom: 0.3rem;
            }

            .jor-card-text {
                color: rgba(244, 247, 251, 0.68);
                font-size: 0.90rem;
                line-height: 1.50;
            }

            .jor-stage {
                padding: 1.05rem 1.08rem;
                border-radius: 24px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    linear-gradient(135deg, rgba(15, 23, 42, 0.93), rgba(30, 41, 59, 0.58));
                box-shadow: 0 14px 44px rgba(0, 0, 0, 0.24);
                margin: 0.9rem 0;
            }

            .jor-stage-title {
                color: #f4f7fb;
                font-size: clamp(1.18rem, 3vw, 1.65rem);
                font-weight: 920;
                line-height: 1.15;
                letter-spacing: -0.04em;
                margin-bottom: 0.35rem;
            }

            .jor-stage-text {
                color: rgba(244, 247, 251, 0.72);
                font-size: 0.93rem;
                line-height: 1.52;
            }

            .jor-note {
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
                .jor-grid-3 {
                    grid-template-columns: 1fr;
                }

                .jor-hero {
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
        <div class="jor-hero">
            <div class="jor-eyebrow">Valoris • Jornada personalizada • v{VERSAO_JORNADA_PERSONALIZADA_VALORIS}</div>
            <div class="jor-title">Seu próximo passo dentro da Valoris.</div>
            <div class="jor-subtitle">
                Em vez de deixar o usuário perdido entre abas, a Valoris monta uma rota prática:
                o que fazer agora, por quê fazer e qual módulo usar primeiro.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _renderizar_formulario(chave_contexto: str) -> Dict[str, Any]:
    col_1, col_2 = st.columns(2)

    with col_1:
        perfil = st.selectbox(
            "Qual é seu perfil agora?",
            PERFIS_JORNADA,
            key=f"jornada_perfil_{chave_contexto}",
        )

        objetivo = st.selectbox(
            "O que você quer fazer primeiro?",
            OBJETIVOS_JORNADA,
            key=f"jornada_objetivo_{chave_contexto}",
        )

    with col_2:
        bloqueio = st.selectbox(
            "O que mais te trava?",
            BLOQUEIOS_JORNADA,
            key=f"jornada_bloqueio_{chave_contexto}",
        )

        tempo_disponivel = st.selectbox(
            "Quanto tempo você tem agora?",
            TEMPOS_DISPONIVEIS,
            key=f"jornada_tempo_{chave_contexto}",
        )

    return _montar_jornada(
        perfil=perfil,
        objetivo=objetivo,
        bloqueio=bloqueio,
        tempo_disponivel=tempo_disponivel,
    )


def _renderizar_resumo_jornada(jornada: Dict[str, Any], chave_contexto: str) -> None:
    registrar_evento_publico(
        evento="jornada_personalizada_gerada",
        origem="jornada_personalizada",
        contexto=chave_contexto,
        perfil=jornada["perfil"],
        valor=jornada["rota_recomendada"],
        detalhe=f"Objetivo: {jornada['objetivo']}; bloqueio: {jornada['bloqueio']}",
    )

    chave_salva = f"jornada_salva_{chave_contexto}_{jornada['rota_id']}_{jornada['perfil']}"

    if not st.session_state.get(chave_salva):
        _registrar_jornada(jornada)
        st.session_state[chave_salva] = True

    st.markdown(
        f"""
        <div class="jor-stage">
            <div class="jor-kicker">Rota recomendada</div>
            <div class="jor-stage-title">{jornada["rota_recomendada"]}</div>
            <div class="jor-stage-text">
                Prioridade: <strong>{jornada["prioridade"]}</strong>. 
                Seu próximo passo agora é: <strong>{jornada["proximo_passo"]}</strong>.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="jor-grid-3">
            <div class="jor-card">
                <div class="jor-kicker">Perfil</div>
                <div class="jor-card-title">{jornada["perfil"]}</div>
                <div class="jor-card-text">A rota muda conforme seu nível de maturidade e necessidade atual.</div>
            </div>
            <div class="jor-card">
                <div class="jor-kicker">Objetivo</div>
                <div class="jor-card-title">{jornada["objetivo"]}</div>
                <div class="jor-card-text">A Valoris prioriza o que você quer resolver primeiro.</div>
            </div>
            <div class="jor-card">
                <div class="jor-kicker">Bloqueio</div>
                <div class="jor-card-title">{jornada["bloqueio"]}</div>
                <div class="jor-card-text">A jornada tenta reduzir a fricção que impede seu avanço.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _renderizar_passos(jornada: Dict[str, Any]) -> None:
    st.markdown("### Sua rota dentro da Valoris")

    passos = jornada["passos"]
    total = len(passos)

    for indice, passo in enumerate(passos, start=1):
        with st.container(border=True):
            st.markdown(f"#### {indice}. {passo['titulo']}")
            st.caption(f"Aba recomendada: {passo['aba']}")
            st.markdown(f"**O que fazer:** {passo['acao']}")
            st.markdown(f"**Por que importa:** {passo['por_que']}")

    st.progress(1 / max(total, 1))
    st.caption("Comece pelo primeiro passo. A Valoris foi pensada para reduzir confusão, não aumentar complexidade.")


def _renderizar_download(jornada: Dict[str, Any], chave_contexto: str) -> None:
    linhas_passos = "\n".join(
        [
            f"{indice}. {passo['titulo']} — Aba: {passo['aba']}\n   - Ação: {passo['acao']}\n   - Por quê: {passo['por_que']}"
            for indice, passo in enumerate(jornada["passos"], start=1)
        ]
    )

    markdown = f"""# Jornada Personalizada Valoris

Perfil: {jornada["perfil"]}  
Objetivo: {jornada["objetivo"]}  
Bloqueio: {jornada["bloqueio"]}  
Tempo disponível: {jornada["tempo_disponivel"]}  

## Rota recomendada

{jornada["rota_recomendada"]}

Prioridade: {jornada["prioridade"]}  
Próximo passo: {jornada["proximo_passo"]}

## Passos

{linhas_passos}

Aviso: conteúdo educacional. Não representa recomendação de investimento.
"""

    st.download_button(
        "Baixar minha jornada",
        data=markdown,
        file_name="jornada_personalizada_valoris.md",
        mime="text/markdown",
        key=f"download_jornada_{chave_contexto}",
    )


def renderizar_jornada_personalizada_valoris(
    modo_compacto: bool = False,
    mostrar_cta: bool = True,
    chave_contexto: str = "principal",
) -> None:
    registrar_visualizacao_unica(
        chave=f"jornada_personalizada_{chave_contexto}",
        evento="jornada_personalizada_visualizada",
        origem="jornada_personalizada",
        contexto=chave_contexto,
        detalhe="Jornada personalizada visualizada.",
    )

    _injetar_css_jornada()

    if not modo_compacto:
        _renderizar_hero()
    else:
        st.markdown("### Jornada personalizada")
        st.caption(
            "A Valoris recomenda uma rota prática para o usuário não se perder entre módulos."
        )

    jornada = _renderizar_formulario(chave_contexto)

    _renderizar_resumo_jornada(jornada, chave_contexto)

    _renderizar_passos(jornada)

    _renderizar_download(jornada, chave_contexto)

    st.markdown(
        """
        <div class="jor-note">
            <strong>Princípio de produto:</strong> uma boa plataforma não mostra apenas funcionalidades.
            Ela guia o usuário até o próximo passo certo.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if mostrar_cta:
        st.divider()
        renderizar_lista_espera_valoris(
            modo_admin=False,
            chave_contexto=f"jornada_personalizada_{chave_contexto}",
        )


def renderizar_painel_jornada_personalizada_valoris() -> None:
    registros = carregar_jornadas_personalizadas()

    st.markdown("## Painel de Jornadas Personalizadas")

    st.caption(
        f"v{VERSAO_JORNADA_PERSONALIZADA_VALORIS} — acompanha rotas recomendadas, objetivos e bloqueios dos usuários."
    )

    if not registros:
        st.info("Ainda não há jornadas registradas.")
        return

    rotas: Dict[str, int] = {}
    objetivos: Dict[str, int] = {}
    bloqueios: Dict[str, int] = {}

    for registro in registros:
        rota = registro.get("rota_recomendada", "N/D")
        objetivo = registro.get("objetivo", "N/D")
        bloqueio = registro.get("bloqueio", "N/D")
        rotas[rota] = rotas.get(rota, 0) + 1
        objetivos[objetivo] = objetivos.get(objetivo, 0) + 1
        bloqueios[bloqueio] = bloqueios.get(bloqueio, 0) + 1

    rota_mais_comum = sorted(rotas.items(), key=lambda item: item[1], reverse=True)[0][0]
    objetivo_mais_comum = sorted(objetivos.items(), key=lambda item: item[1], reverse=True)[0][0]
    bloqueio_mais_comum = sorted(bloqueios.items(), key=lambda item: item[1], reverse=True)[0][0]

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Jornadas", len(registros))

    with col_2:
        st.metric("Rota mais comum", rota_mais_comum)

    with col_3:
        st.metric("Objetivo dominante", objetivo_mais_comum)

    with col_4:
        st.metric("Bloqueio dominante", bloqueio_mais_comum)

    with st.expander("Últimas jornadas", expanded=False):
        for registro in reversed(registros[-20:]):
            with st.container(border=True):
                st.markdown(f"**{registro.get('rota_recomendada', 'N/D')}**")
                st.caption(f"{registro.get('data_registro', 'N/D')} • {registro.get('perfil', 'N/D')}")
                st.markdown(f"**Objetivo:** {registro.get('objetivo', 'N/D')}")
                st.markdown(f"**Bloqueio:** {registro.get('bloqueio', 'N/D')}")
                st.markdown(f"**Próximo passo:** {registro.get('proximo_passo', 'N/D')}")

    st.download_button(
        "Baixar jornadas personalizadas (.csv)",
        data=gerar_csv_jornadas_personalizadas(),
        file_name="jornadas_personalizadas_valoris.csv",
        mime="text/csv",
        key="download_jornadas_personalizadas_valoris",
    )


def executar_autoteste_jornada_personalizada_valoris() -> List[Dict[str, str]]:
    jornada = _montar_jornada(
        perfil="Investidor em evolução",
        objetivo="Auditar premissas e riscos",
        bloqueio="Tenho medo de errar premissas",
        tempo_disponivel="Tenho 15 minutos",
    )

    return [
        {
            "teste": "versao_jornada",
            "status": "OK" if VERSAO_JORNADA_PERSONALIZADA_VALORIS == "3.8.48" else "FALHA",
            "detalhe": VERSAO_JORNADA_PERSONALIZADA_VALORIS,
        },
        {
            "teste": "rota_recomendada",
            "status": "OK" if jornada["rota_recomendada"] != "" else "FALHA",
            "detalhe": jornada["rota_recomendada"],
        },
        {
            "teste": "passos",
            "status": "OK" if len(jornada["passos"]) >= 3 else "FALHA",
            "detalhe": str(len(jornada["passos"])),
        },
    ]
