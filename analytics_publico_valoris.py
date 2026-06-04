# analytics_publico_valoris.py

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

import streamlit as st


# ============================================================
# VALORIS
# v3.8.45 — Analytics Público e Funil de Conversão
# ------------------------------------------------------------
# Este módulo registra eventos simples da experiência pública.
#
# Objetivo:
# - medir se usuários chegam na landing
# - medir se interagem com a demonstração
# - medir se chegam na lista beta
# - medir intenção comercial antes de criar checkout
# - transformar a evolução da Valoris em produto guiado por dados
#
# Observação:
# - Armazena dados em CSV local.
# - O arquivo deve ficar no .gitignore.
# - Em produção madura, migrar para banco/analytics real.
# ============================================================


VERSAO_ANALYTICS_PUBLICO_VALORIS = "3.8.45"

CAMINHO_EVENTOS_PUBLICOS = Path("eventos_publicos_valoris.csv")

CAMPOS_EVENTOS_PUBLICOS = [
    "id",
    "data_evento",
    "sessao_id",
    "evento",
    "origem",
    "contexto",
    "perfil",
    "etapa",
    "ticker",
    "valor",
    "detalhe",
]


EVENTOS_IMPORTANTES = {
    "landing_visualizada": "Usuário viu a landing.",
    "demo_visualizada": "Usuário viu a demonstração.",
    "demo_interacao": "Usuário interagiu com a demonstração.",
    "lista_beta_visualizada": "Usuário chegou na lista beta.",
    "lead_cadastrado": "Usuário entrou na lista beta.",
    "oferta_visualizada": "Usuário viu uma oferta.",
    "relatorio_demo_baixado": "Usuário baixou relatório demo.",
}


def _limpar_texto(valor: Any) -> str:
    if valor is None:
        return ""

    return str(valor).strip()


def obter_sessao_publica_valoris() -> str:
    if "sessao_publica_valoris" not in st.session_state:
        st.session_state["sessao_publica_valoris"] = str(uuid4())[:12]

    return st.session_state["sessao_publica_valoris"]


def _garantir_arquivo_eventos() -> None:
    if CAMINHO_EVENTOS_PUBLICOS.exists():
        return

    with CAMINHO_EVENTOS_PUBLICOS.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_EVENTOS_PUBLICOS)
        escritor.writeheader()


def registrar_evento_publico(
    evento: str,
    origem: str = "",
    contexto: str = "",
    perfil: str = "",
    etapa: str = "",
    ticker: str = "",
    valor: Any = "",
    detalhe: str = "",
) -> None:
    """
    Registra um evento público simples em CSV.

    A função é propositalmente defensiva: se algo falhar, não derruba o app.
    """
    try:
        _garantir_arquivo_eventos()

        registro = {
            "id": str(uuid4()),
            "data_evento": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sessao_id": obter_sessao_publica_valoris(),
            "evento": _limpar_texto(evento),
            "origem": _limpar_texto(origem),
            "contexto": _limpar_texto(contexto),
            "perfil": _limpar_texto(perfil),
            "etapa": _limpar_texto(etapa),
            "ticker": _limpar_texto(ticker),
            "valor": _limpar_texto(valor),
            "detalhe": _limpar_texto(detalhe),
        }

        with CAMINHO_EVENTOS_PUBLICOS.open("a", newline="", encoding="utf-8") as arquivo:
            escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_EVENTOS_PUBLICOS)
            escritor.writerow(registro)

    except Exception:
        return


def registrar_visualizacao_unica(
    chave: str,
    evento: str,
    origem: str = "",
    contexto: str = "",
    detalhe: str = "",
) -> None:
    """
    Registra uma visualização apenas uma vez por sessão do Streamlit.
    """
    chave_estado = f"evento_publico_registrado_{chave}"

    if st.session_state.get(chave_estado):
        return

    registrar_evento_publico(
        evento=evento,
        origem=origem,
        contexto=contexto,
        detalhe=detalhe,
    )

    st.session_state[chave_estado] = True


def carregar_eventos_publicos() -> List[Dict[str, str]]:
    _garantir_arquivo_eventos()

    with CAMINHO_EVENTOS_PUBLICOS.open("r", newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        return list(leitor)


def gerar_csv_eventos_publicos() -> str:
    _garantir_arquivo_eventos()

    return CAMINHO_EVENTOS_PUBLICOS.read_text(encoding="utf-8")


def _contar_eventos(eventos: List[Dict[str, str]], nome_evento: str) -> int:
    return len(
        [
            evento for evento in eventos
            if evento.get("evento", "") == nome_evento
        ]
    )


def _contar_sessoes(eventos: List[Dict[str, str]]) -> int:
    sessoes = {
        evento.get("sessao_id", "")
        for evento in eventos
        if evento.get("sessao_id", "")
    }

    return len(sessoes)


def _taxa(numerador: int, denominador: int) -> float:
    if denominador <= 0:
        return 0.0

    return round((numerador / denominador) * 100, 1)


def calcular_metricas_funil_publico() -> Dict[str, Any]:
    eventos = carregar_eventos_publicos()

    sessoes = _contar_sessoes(eventos)
    landing = _contar_eventos(eventos, "landing_visualizada")
    demo = _contar_eventos(eventos, "demo_visualizada")
    interacoes_demo = _contar_eventos(eventos, "demo_interacao")
    lista = _contar_eventos(eventos, "lista_beta_visualizada")
    leads = _contar_eventos(eventos, "lead_cadastrado")
    ofertas = _contar_eventos(eventos, "oferta_visualizada")
    downloads = _contar_eventos(eventos, "relatorio_demo_baixado")

    base = max(landing, sessoes, 1)

    return {
        "eventos": len(eventos),
        "sessoes": sessoes,
        "landing": landing,
        "demo": demo,
        "interacoes_demo": interacoes_demo,
        "lista": lista,
        "leads": leads,
        "ofertas": ofertas,
        "downloads": downloads,
        "taxa_landing_demo": _taxa(demo, base),
        "taxa_demo_interacao": _taxa(interacoes_demo, max(demo, 1)),
        "taxa_landing_lista": _taxa(lista, base),
        "taxa_landing_lead": _taxa(leads, base),
    }


def diagnosticar_funil_publico(metricas: Dict[str, Any]) -> List[Dict[str, str]]:
    diagnosticos: List[Dict[str, str]] = []

    if metricas["landing"] == 0:
        diagnosticos.append(
            {
                "nivel": "Pendente",
                "titulo": "Sem visualizações da landing",
                "leitura": "Ainda não há dados suficientes para avaliar conversão pública.",
            }
        )
        return diagnosticos

    if metricas["taxa_landing_demo"] >= 50:
        diagnosticos.append(
            {
                "nivel": "Favorável",
                "titulo": "Boa passagem da landing para a demonstração",
                "leitura": "A proposta inicial parece estar conduzindo usuários para a experiência prática.",
            }
        )
    else:
        diagnosticos.append(
            {
                "nivel": "Atenção",
                "titulo": "Pouca passagem para a demonstração",
                "leitura": "A landing pode precisar de CTA mais forte ou demonstração mais visível.",
            }
        )

    if metricas["taxa_demo_interacao"] >= 60:
        diagnosticos.append(
            {
                "nivel": "Favorável",
                "titulo": "Demonstração gera interação",
                "leitura": "Usuários que chegam na demo estão mexendo na experiência.",
            }
        )
    else:
        diagnosticos.append(
            {
                "nivel": "Atenção",
                "titulo": "Demonstração pode estar passiva",
                "leitura": "Talvez seja necessário deixar os controles mais evidentes ou reduzir texto.",
            }
        )

    if metricas["taxa_landing_lead"] >= 8:
        diagnosticos.append(
            {
                "nivel": "Favorável",
                "titulo": "Conversão inicial promissora",
                "leitura": "A proporção de leads por visualização já indica interesse real.",
            }
        )
    elif metricas["taxa_landing_lead"] >= 3:
        diagnosticos.append(
            {
                "nivel": "Atenção",
                "titulo": "Conversão ainda moderada",
                "leitura": "Existe interesse, mas a oferta ou CTA ainda podem melhorar.",
            }
        )
    else:
        diagnosticos.append(
            {
                "nivel": "Risco",
                "titulo": "Conversão baixa para lead",
                "leitura": "A proposta pode estar clara, mas ainda não gera urgência suficiente para cadastro.",
            }
        )

    return diagnosticos


def _renderizar_diagnostico(nivel: str, titulo: str, leitura: str) -> None:
    texto = f"**{titulo}**\n\n{leitura}"

    if nivel == "Favorável":
        st.success(texto)
    elif nivel == "Risco":
        st.error(texto)
    elif nivel == "Pendente":
        st.info(texto)
    else:
        st.warning(texto)


def renderizar_painel_analytics_publico() -> None:
    """
    Renderiza painel interno de analytics do funil público.
    """
    metricas = calcular_metricas_funil_publico()

    st.markdown("## Analytics Público Valoris")

    st.caption(
        f"v{VERSAO_ANALYTICS_PUBLICO_VALORIS} — mede sinais simples de chegada, interação, interesse e conversão."
    )

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Sessões", metricas["sessoes"])

    with col_2:
        st.metric("Landing", metricas["landing"])

    with col_3:
        st.metric("Demo", metricas["demo"])

    with col_4:
        st.metric("Leads", metricas["leads"])

    col_5, col_6, col_7, col_8 = st.columns(4)

    with col_5:
        st.metric("Interações demo", metricas["interacoes_demo"])

    with col_6:
        st.metric("Lista beta", metricas["lista"])

    with col_7:
        st.metric("Ofertas vistas", metricas["ofertas"])

    with col_8:
        st.metric("Downloads demo", metricas["downloads"])

    st.divider()

    st.markdown("### Taxas do funil")

    col_a, col_b, col_c, col_d = st.columns(4)

    with col_a:
        st.metric("Landing → Demo", f"{metricas['taxa_landing_demo']}%")

    with col_b:
        st.metric("Demo → Interação", f"{metricas['taxa_demo_interacao']}%")

    with col_c:
        st.metric("Landing → Lista", f"{metricas['taxa_landing_lista']}%")

    with col_d:
        st.metric("Landing → Lead", f"{metricas['taxa_landing_lead']}%")

    st.divider()

    st.markdown("### Diagnóstico do funil")

    for diagnostico in diagnosticar_funil_publico(metricas):
        _renderizar_diagnostico(
            nivel=diagnostico["nivel"],
            titulo=diagnostico["titulo"],
            leitura=diagnostico["leitura"],
        )

    eventos = carregar_eventos_publicos()

    with st.expander("Últimos eventos registrados", expanded=False):
        if not eventos:
            st.info("Ainda não há eventos registrados.")
        else:
            for evento in reversed(eventos[-20:]):
                with st.container(border=True):
                    st.markdown(f"**{evento.get('evento', 'N/D')}**")
                    st.caption(
                        f"{evento.get('data_evento', 'N/D')} • sessão {evento.get('sessao_id', 'N/D')}"
                    )
                    st.markdown(
                        f"Origem: **{evento.get('origem', '')}** | Contexto: **{evento.get('contexto', '')}**"
                    )
                    if evento.get("detalhe"):
                        st.caption(evento.get("detalhe", ""))

    st.download_button(
        "Baixar eventos públicos (.csv)",
        data=gerar_csv_eventos_publicos(),
        file_name="eventos_publicos_valoris.csv",
        mime="text/csv",
        key="download_eventos_publicos_valoris",
    )

    st.info(
        "Essas métricas são simples e locais. Elas servem para validar o MVP. "
        "Em uma versão madura, substitua por analytics real, banco de dados e identificação de origem de tráfego."
    )


def executar_autoteste_analytics_publico_valoris() -> List[Dict[str, str]]:
    metricas_vazias = {
        "landing": 0,
        "taxa_landing_demo": 0,
        "taxa_demo_interacao": 0,
        "taxa_landing_lead": 0,
    }

    diagnosticos = diagnosticar_funil_publico(metricas_vazias)

    return [
        {
            "teste": "versao_analytics",
            "status": "OK" if VERSAO_ANALYTICS_PUBLICO_VALORIS == "3.8.45" else "FALHA",
            "detalhe": VERSAO_ANALYTICS_PUBLICO_VALORIS,
        },
        {
            "teste": "campos_eventos",
            "status": "OK" if "sessao_id" in CAMPOS_EVENTOS_PUBLICOS else "FALHA",
            "detalhe": str(len(CAMPOS_EVENTOS_PUBLICOS)),
        },
        {
            "teste": "diagnostico_funil",
            "status": "OK" if len(diagnosticos) >= 1 else "FALHA",
            "detalhe": str(len(diagnosticos)),
        },
    ]
