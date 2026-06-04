# conversao_fundador_valoris.py

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
# v3.8.50 — Conversão Ética e Oferta Fundador Personalizada
# ------------------------------------------------------------
# Este módulo transforma interesse em intenção comercial sem
# parecer venda agressiva.
#
# Objetivo:
# - recomendar uma oferta com base no perfil e intenção do usuário
# - testar preço e disposição de pagamento
# - registrar sinais de compra
# - manter linguagem educacional, honesta e sem promessa de lucro
# - preparar validação manual antes de checkout
# ============================================================


VERSAO_CONVERSAO_FUNDADOR_VALORIS = "3.8.50"

CAMINHO_SINAIS_CONVERSAO = Path("sinais_conversao_valoris.csv")

CAMPOS_SINAIS_CONVERSAO = [
    "id",
    "data_registro",
    "sessao_id",
    "perfil",
    "valor_percebido",
    "momento",
    "preferencia_pagamento",
    "barreira",
    "oferta_recomendada",
    "preco_recomendado",
    "intencao",
    "proxima_acao",
]


PERFIS_CONVERSAO = [
    "Estou apenas conhecendo",
    "Gostei da ideia, mas preciso testar mais",
    "Eu usaria se fosse mais automático",
    "Eu pagaria se o relatório e auditor forem bons",
    "Quero participar como fundador",
]


VALOR_PERCEBIDO = [
    "Baixo — ainda não entendi o valor",
    "Médio — parece útil, mas preciso testar",
    "Alto — resolveria uma dor real minha",
    "Muito alto — eu usaria com frequência",
]


MOMENTOS_USO = [
    "Antes de comprar uma ação",
    "Depois de ver uma queda forte",
    "Durante temporada de resultados",
    "Ao revisar minha carteira",
    "Para estudar e aprender valuation",
]


PREFERENCIAS_PAGAMENTO = [
    "Não pagaria agora",
    "Pagaria um relatório avulso",
    "Pagaria mensal barato",
    "Pagaria acesso fundador único",
    "Pagaria premium se tivesse dados automáticos",
]


BARREIRAS_COMPRA = [
    "Ainda não confio nos dados",
    "Quero ver mais automação",
    "Quero visual mais profissional",
    "Preciso testar com ações reais",
    "Preço precisa ser baixo no beta",
    "Nenhuma barreira forte",
]


OFERTAS_CONVERSAO = {
    "gratuito": {
        "nome": "Continuar no gratuito",
        "preco": "R$ 0",
        "proxima_acao": (
            "Use a Trilha, a Demonstração e a Jornada antes de decidir se quer participar do beta."
        ),
        "mensagem": (
            "Você ainda está em fase de descoberta. O melhor caminho é sentir valor antes de qualquer pagamento."
        ),
    },
    "relatorio_avulso": {
        "nome": "Relatório Premium Avulso",
        "preco": "R$ 9,90 a R$ 19,90",
        "proxima_acao": (
            "Validar se usuários pagariam por uma entrega clara, bonita e revisável antes de uma assinatura."
        ),
        "mensagem": (
            "Faz sentido para quem quer uma entrega concreta sem compromisso mensal."
        ),
    },
    "beta_mensal": {
        "nome": "Beta Mensal",
        "preco": "R$ 19,90/mês",
        "proxima_acao": (
            "Testar recorrência com poucos usuários antes de checkout automático."
        ),
        "mensagem": (
            "Faz sentido para quem quer acompanhar a evolução e usar a Valoris com frequência."
        ),
    },
    "fundador": {
        "nome": "Beta Fundador",
        "preco": "R$ 97 pagamento único",
        "proxima_acao": (
            "Convidar manualmente usuários qualificados para um grupo fundador pequeno."
        ),
        "mensagem": (
            "Faz sentido para quem quer participar cedo, ajudar a moldar o produto e receber condição simbólica."
        ),
    },
    "premium_futuro": {
        "nome": "Premium Futuro",
        "preco": "A definir",
        "proxima_acao": (
            "Priorizar automação por ticker, dados fundamentalistas, alertas e relatórios avançados."
        ),
        "mensagem": (
            "Faz sentido para usuários que só pagariam quando a plataforma tiver dados automáticos e mais robustez."
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
    if CAMINHO_SINAIS_CONVERSAO.exists():
        return

    with CAMINHO_SINAIS_CONVERSAO.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_SINAIS_CONVERSAO)
        escritor.writeheader()


def _registrar_sinal_conversao(dados: Dict[str, Any]) -> None:
    try:
        _garantir_arquivo()

        registro = {
            "id": str(uuid4()),
            "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sessao_id": _obter_sessao(),
            "perfil": _limpar_texto(dados.get("perfil")),
            "valor_percebido": _limpar_texto(dados.get("valor_percebido")),
            "momento": _limpar_texto(dados.get("momento")),
            "preferencia_pagamento": _limpar_texto(dados.get("preferencia_pagamento")),
            "barreira": _limpar_texto(dados.get("barreira")),
            "oferta_recomendada": _limpar_texto(dados.get("oferta_recomendada")),
            "preco_recomendado": _limpar_texto(dados.get("preco_recomendado")),
            "intencao": _limpar_texto(dados.get("intencao")),
            "proxima_acao": _limpar_texto(dados.get("proxima_acao")),
        }

        with CAMINHO_SINAIS_CONVERSAO.open("a", newline="", encoding="utf-8") as arquivo:
            escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_SINAIS_CONVERSAO)
            escritor.writerow(registro)

    except Exception:
        return


def carregar_sinais_conversao() -> List[Dict[str, str]]:
    _garantir_arquivo()

    with CAMINHO_SINAIS_CONVERSAO.open("r", newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        return list(leitor)


def gerar_csv_sinais_conversao() -> str:
    _garantir_arquivo()

    return CAMINHO_SINAIS_CONVERSAO.read_text(encoding="utf-8")


def _escolher_oferta(
    perfil: str,
    valor_percebido: str,
    preferencia_pagamento: str,
    barreira: str,
) -> str:
    if "Não pagaria" in preferencia_pagamento or "Baixo" in valor_percebido:
        return "gratuito"

    if "relatório avulso" in preferencia_pagamento:
        return "relatorio_avulso"

    if "mensal" in preferencia_pagamento:
        return "beta_mensal"

    if "fundador" in preferencia_pagamento or "fundador" in perfil.lower():
        return "fundador"

    if "dados automáticos" in preferencia_pagamento or "automação" in barreira:
        return "premium_futuro"

    if "Muito alto" in valor_percebido:
        return "fundador"

    if "Alto" in valor_percebido:
        return "beta_mensal"

    return "gratuito"


def _classificar_intencao(
    valor_percebido: str,
    preferencia_pagamento: str,
    barreira: str,
) -> str:
    if "Não pagaria" in preferencia_pagamento:
        return "Baixa intenção"

    if "Muito alto" in valor_percebido and "Nenhuma" in barreira:
        return "Alta intenção"

    if "Alto" in valor_percebido:
        return "Intenção promissora"

    if "Médio" in valor_percebido:
        return "Intenção em validação"

    return "Baixa intenção"


def _montar_diagnostico_conversao(
    perfil: str,
    valor_percebido: str,
    momento: str,
    preferencia_pagamento: str,
    barreira: str,
) -> Dict[str, str]:
    oferta_id = _escolher_oferta(
        perfil=perfil,
        valor_percebido=valor_percebido,
        preferencia_pagamento=preferencia_pagamento,
        barreira=barreira,
    )

    oferta = OFERTAS_CONVERSAO[oferta_id]
    intencao = _classificar_intencao(
        valor_percebido=valor_percebido,
        preferencia_pagamento=preferencia_pagamento,
        barreira=barreira,
    )

    return {
        "perfil": perfil,
        "valor_percebido": valor_percebido,
        "momento": momento,
        "preferencia_pagamento": preferencia_pagamento,
        "barreira": barreira,
        "oferta_id": oferta_id,
        "oferta_recomendada": oferta["nome"],
        "preco_recomendado": oferta["preco"],
        "mensagem": oferta["mensagem"],
        "intencao": intencao,
        "proxima_acao": oferta["proxima_acao"],
    }


def _injetar_css_conversao() -> None:
    st.markdown(
        """
        <style>
            .conv-hero {
                padding: clamp(1.18rem, 3vw, 2rem);
                border-radius: 30px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    radial-gradient(circle at top left, rgba(214, 181, 109, 0.26), transparent 30%),
                    radial-gradient(circle at bottom right, rgba(36, 128, 91, 0.24), transparent 34%),
                    linear-gradient(135deg, rgba(8, 15, 27, 0.99), rgba(5, 9, 18, 0.99));
                box-shadow: 0 18px 58px rgba(0, 0, 0, 0.31);
                margin-bottom: 1rem;
            }

            .conv-eyebrow {
                color: #d6b56d;
                font-size: 0.74rem;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                font-weight: 880;
                margin-bottom: 0.35rem;
            }

            .conv-title {
                color: #f4f7fb;
                font-size: clamp(1.75rem, 5.4vw, 3.1rem);
                font-weight: 950;
                line-height: 1.02;
                letter-spacing: -0.058em;
                margin-bottom: 0.55rem;
            }

            .conv-subtitle {
                color: rgba(244, 247, 251, 0.75);
                font-size: clamp(0.94rem, 2.2vw, 1.06rem);
                line-height: 1.56;
                max-width: 1020px;
            }

            .conv-grid-3 {
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 0.8rem;
                margin: 0.9rem 0;
            }

            .conv-card {
                padding: 1.02rem 1.06rem;
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background:
                    radial-gradient(circle at top right, rgba(214, 181, 109, 0.08), transparent 30%),
                    rgba(255, 255, 255, 0.034);
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.17);
                height: 100%;
            }

            .conv-kicker {
                color: #d6b56d;
                font-size: 0.72rem;
                letter-spacing: 0.11em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.4rem;
            }

            .conv-card-title {
                color: #f4f7fb;
                font-size: 1.08rem;
                font-weight: 880;
                letter-spacing: -0.026em;
                margin-bottom: 0.3rem;
            }

            .conv-card-value {
                color: #f4f7fb;
                font-size: 1.48rem;
                font-weight: 940;
                letter-spacing: -0.045em;
                margin-bottom: 0.25rem;
            }

            .conv-card-text {
                color: rgba(244, 247, 251, 0.68);
                font-size: 0.90rem;
                line-height: 1.50;
            }

            .conv-stage {
                padding: 1.05rem 1.08rem;
                border-radius: 24px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    linear-gradient(135deg, rgba(15, 23, 42, 0.93), rgba(30, 41, 59, 0.58));
                box-shadow: 0 14px 44px rgba(0, 0, 0, 0.24);
                margin: 0.9rem 0;
            }

            .conv-stage-title {
                color: #f4f7fb;
                font-size: clamp(1.18rem, 3vw, 1.65rem);
                font-weight: 920;
                line-height: 1.15;
                letter-spacing: -0.04em;
                margin-bottom: 0.35rem;
            }

            .conv-stage-text {
                color: rgba(244, 247, 251, 0.72);
                font-size: 0.93rem;
                line-height: 1.52;
            }

            .conv-note {
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
                .conv-grid-3 {
                    grid-template-columns: 1fr;
                }

                .conv-hero {
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
        <div class="conv-hero">
            <div class="conv-eyebrow">Valoris • Conversão ética • v{VERSAO_CONVERSAO_FUNDADOR_VALORIS}</div>
            <div class="conv-title">Oferta certa, para o usuário certo, no momento certo.</div>
            <div class="conv-subtitle">
                A Valoris não precisa forçar venda. Ela deve entender valor percebido, barreira de confiança
                e intenção real antes de apresentar uma condição beta.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _renderizar_formulario(chave_contexto: str) -> Dict[str, str]:
    col_1, col_2 = st.columns(2)

    with col_1:
        perfil = st.selectbox(
            "Qual frase mais combina com você agora?",
            PERFIS_CONVERSAO,
            key=f"conv_perfil_{chave_contexto}",
        )

        valor_percebido = st.selectbox(
            "Qual valor você percebeu até aqui?",
            VALOR_PERCEBIDO,
            key=f"conv_valor_{chave_contexto}",
        )

        momento = st.selectbox(
            "Quando você usaria a Valoris?",
            MOMENTOS_USO,
            key=f"conv_momento_{chave_contexto}",
        )

    with col_2:
        preferencia_pagamento = st.selectbox(
            "Qual modelo de pagamento faria mais sentido?",
            PREFERENCIAS_PAGAMENTO,
            key=f"conv_pagamento_{chave_contexto}",
        )

        barreira = st.selectbox(
            "O que ainda te impediria de pagar?",
            BARREIRAS_COMPRA,
            key=f"conv_barreira_{chave_contexto}",
        )

    return _montar_diagnostico_conversao(
        perfil=perfil,
        valor_percebido=valor_percebido,
        momento=momento,
        preferencia_pagamento=preferencia_pagamento,
        barreira=barreira,
    )


def _renderizar_diagnostico(dados: Dict[str, str], chave_contexto: str) -> None:
    registrar_evento_publico(
        evento="conversao_fundador_gerada",
        origem="conversao_fundador",
        contexto=chave_contexto,
        perfil=dados["perfil"],
        valor=dados["oferta_recomendada"],
        detalhe=f"Intenção: {dados['intencao']}; barreira: {dados['barreira']}",
    )

    chave_salva = f"conversao_salva_{chave_contexto}_{dados['oferta_id']}_{dados['intencao']}"

    if not st.session_state.get(chave_salva):
        _registrar_sinal_conversao(dados)
        st.session_state[chave_salva] = True

    st.markdown(
        f"""
        <div class="conv-stage">
            <div class="conv-kicker">Oferta recomendada</div>
            <div class="conv-stage-title">{dados["oferta_recomendada"]}</div>
            <div class="conv-stage-text">
                Preço/condição sugerida: <strong>{dados["preco_recomendado"]}</strong>.
                {dados["mensagem"]}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="conv-grid-3">
            <div class="conv-card">
                <div class="conv-kicker">Intenção</div>
                <div class="conv-card-title">{dados["intencao"]}</div>
                <div class="conv-card-text">A intenção ajuda a decidir se devemos vender agora ou educar mais.</div>
            </div>
            <div class="conv-card">
                <div class="conv-kicker">Barreira principal</div>
                <div class="conv-card-title">{dados["barreira"]}</div>
                <div class="conv-card-text">A Valoris precisa resolver essa objeção antes de escalar venda.</div>
            </div>
            <div class="conv-card">
                <div class="conv-kicker">Momento de uso</div>
                <div class="conv-card-title">{dados["momento"]}</div>
                <div class="conv-card-text">O melhor produto nasce do contexto real de uso.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if dados["intencao"] == "Alta intenção":
        st.success(f"**Próxima ação:** {dados['proxima_acao']}")
    elif dados["intencao"] == "Intenção promissora":
        st.warning(f"**Próxima ação:** {dados['proxima_acao']}")
    else:
        st.info(f"**Próxima ação:** {dados['proxima_acao']}")


def _renderizar_mensagem_manual(dados: Dict[str, str], chave_contexto: str) -> None:
    mensagem = f"""Olá! Com base no seu perfil, a condição que mais parece fazer sentido hoje é:

{dados["oferta_recomendada"]} — {dados["preco_recomendado"]}

Por quê:
{dados["mensagem"]}

O que a Valoris entrega:
- valuation com margem de segurança;
- demonstração guiada;
- trilha educativa;
- auditor de decisão;
- relatório premium;
- evolução do produto com usuários fundadores.

Importante:
A Valoris é educacional. Não recomenda compra ou venda de ativos e não promete rentabilidade.

Sua principal barreira hoje parece ser:
{dados["barreira"]}

Se fizer sentido, posso te colocar na lista beta/fundador para acompanhar os próximos testes.
"""

    st.text_area(
        "Mensagem manual sugerida",
        value=mensagem,
        height=300,
        key=f"mensagem_manual_conversao_{chave_contexto}",
    )

    markdown = f"""# Diagnóstico de Conversão Valoris

Oferta recomendada: {dados["oferta_recomendada"]}  
Preço/condição: {dados["preco_recomendado"]}  
Intenção: {dados["intencao"]}  
Barreira: {dados["barreira"]}  
Momento de uso: {dados["momento"]}  

## Próxima ação

{dados["proxima_acao"]}

Aviso: conteúdo educacional. Não representa recomendação de investimento.
"""

    st.download_button(
        "Baixar diagnóstico de conversão",
        data=markdown,
        file_name="diagnostico_conversao_valoris.md",
        mime="text/markdown",
        key=f"download_conversao_{chave_contexto}",
    )


def renderizar_conversao_fundador_valoris(
    modo_compacto: bool = False,
    mostrar_cta: bool = True,
    chave_contexto: str = "principal",
) -> None:
    registrar_visualizacao_unica(
        chave=f"conversao_fundador_{chave_contexto}",
        evento="conversao_fundador_visualizada",
        origem="conversao_fundador",
        contexto=chave_contexto,
        detalhe="Tela de conversão fundador visualizada.",
    )

    _injetar_css_conversao()

    if not modo_compacto:
        _renderizar_hero()
    else:
        st.markdown("### Oferta recomendada para seu momento")
        st.caption(
            "A Valoris testa intenção comercial sem venda agressiva: primeiro entende valor, depois recomenda condição."
        )

    dados = _renderizar_formulario(chave_contexto)

    _renderizar_diagnostico(dados, chave_contexto)

    _renderizar_mensagem_manual(dados, chave_contexto)

    st.markdown(
        """
        <div class="conv-note">
            <strong>Regra Valoris:</strong> vender sem prometer retorno. O produto deve monetizar clareza,
            método, relatório e disciplina — nunca ilusão de lucro fácil.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if mostrar_cta:
        st.divider()
        renderizar_lista_espera_valoris(
            modo_admin=False,
            chave_contexto=f"conversao_fundador_{chave_contexto}",
        )


def renderizar_painel_conversao_fundador_valoris() -> None:
    registros = carregar_sinais_conversao()

    st.markdown("## Painel de Conversão Fundador")

    st.caption(
        f"v{VERSAO_CONVERSAO_FUNDADOR_VALORIS} — acompanha intenção comercial, barreiras e oferta recomendada."
    )

    if not registros:
        st.info("Ainda não há sinais de conversão registrados.")
        return

    ofertas: Dict[str, int] = {}
    intencoes: Dict[str, int] = {}
    barreiras: Dict[str, int] = {}

    for registro in registros:
        oferta = registro.get("oferta_recomendada", "N/D")
        intencao = registro.get("intencao", "N/D")
        barreira = registro.get("barreira", "N/D")
        ofertas[oferta] = ofertas.get(oferta, 0) + 1
        intencoes[intencao] = intencoes.get(intencao, 0) + 1
        barreiras[barreira] = barreiras.get(barreira, 0) + 1

    oferta_top = sorted(ofertas.items(), key=lambda item: item[1], reverse=True)[0][0]
    intencao_top = sorted(intencoes.items(), key=lambda item: item[1], reverse=True)[0][0]
    barreira_top = sorted(barreiras.items(), key=lambda item: item[1], reverse=True)[0][0]

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Sinais", len(registros))

    with col_2:
        st.metric("Oferta dominante", oferta_top)

    with col_3:
        st.metric("Intenção dominante", intencao_top)

    with col_4:
        st.metric("Barreira dominante", barreira_top)

    with st.expander("Últimos sinais", expanded=False):
        for registro in reversed(registros[-20:]):
            with st.container(border=True):
                st.markdown(f"**{registro.get('oferta_recomendada', 'N/D')}**")
                st.caption(f"{registro.get('data_registro', 'N/D')} • {registro.get('intencao', 'N/D')}")
                st.markdown(f"**Perfil:** {registro.get('perfil', 'N/D')}")
                st.markdown(f"**Valor percebido:** {registro.get('valor_percebido', 'N/D')}")
                st.markdown(f"**Barreira:** {registro.get('barreira', 'N/D')}")
                st.markdown(f"**Próxima ação:** {registro.get('proxima_acao', 'N/D')}")

    st.download_button(
        "Baixar sinais de conversão (.csv)",
        data=gerar_csv_sinais_conversao(),
        file_name="sinais_conversao_valoris.csv",
        mime="text/csv",
        key="download_sinais_conversao_valoris",
    )


def executar_autoteste_conversao_fundador_valoris() -> List[Dict[str, str]]:
    dados = _montar_diagnostico_conversao(
        perfil="Quero participar como fundador",
        valor_percebido="Muito alto — eu usaria com frequência",
        momento="Antes de comprar uma ação",
        preferencia_pagamento="Pagaria acesso fundador único",
        barreira="Nenhuma barreira forte",
    )

    return [
        {
            "teste": "versao_conversao",
            "status": "OK" if VERSAO_CONVERSAO_FUNDADOR_VALORIS == "3.8.50" else "FALHA",
            "detalhe": VERSAO_CONVERSAO_FUNDADOR_VALORIS,
        },
        {
            "teste": "oferta_recomendada",
            "status": "OK" if dados["oferta_recomendada"] != "" else "FALHA",
            "detalhe": dados["oferta_recomendada"],
        },
        {
            "teste": "intencao",
            "status": "OK" if dados["intencao"] != "" else "FALHA",
            "detalhe": dados["intencao"],
        },
    ]
