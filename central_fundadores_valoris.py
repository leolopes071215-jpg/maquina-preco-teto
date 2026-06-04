# central_fundadores_valoris.py

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

import streamlit as st

from validacao_manual_valoris import carregar_validacoes_manuais


# ============================================================
# VALORIS
# v3.8.53 — Central de Fundadores e Onboarding Beta
# ------------------------------------------------------------
# Transforma validação manual em operação beta.
#
# Objetivo:
# - organizar usuários fundadores;
# - acompanhar pagamento manual, acesso e onboarding;
# - registrar feedback, risco de churn e entusiasmo;
# - preparar a transição futura para checkout/banco real.
# ============================================================


VERSAO_CENTRAL_FUNDADORES_VALORIS = "3.8.53"

CAMINHO_FUNDADORES_VALORIS = Path("fundadores_valoris.csv")

CAMPOS_FUNDADOR = [
    "id",
    "data_registro",
    "nome",
    "contato",
    "origem",
    "perfil",
    "dor_principal",
    "plano",
    "valor_combinado",
    "status_pagamento",
    "status_acesso",
    "etapa_onboarding",
    "uso_inicial",
    "feedback_principal",
    "risco_churn",
    "nivel_entusiasmo",
    "proximo_passo",
    "observacoes",
]


PLANOS_FUNDADOR = [
    "Beta Fundador R$ 97",
    "Beta Mensal R$ 19,90",
    "Relatório Premium Avulso",
    "Acesso gratuito estratégico",
    "Premium futuro",
    "Outro",
]


STATUS_PAGAMENTO = [
    "Não cobrado",
    "Aguardando pagamento",
    "Pago manualmente",
    "Isento",
    "Desistiu",
    "Reembolsado",
]


STATUS_ACESSO = [
    "Não liberado",
    "Acesso liberado",
    "Aguardando instruções",
    "Em teste",
    "Pausado",
    "Encerrado",
]


ETAPAS_ONBOARDING = [
    "Selecionado",
    "Convite enviado",
    "Entrou no beta",
    "Recebeu instruções",
    "Fez primeiro acesso",
    "Gerou primeira análise",
    "Baixou relatório",
    "Enviou feedback",
    "Virou caso de sucesso",
]


USO_INICIAL = [
    "Ainda não usou",
    "Só abriu a landing",
    "Usou Copiloto/Jornada",
    "Usou Demonstração",
    "Usou Valuation",
    "Baixou relatório",
    "Testou com ação real",
]


RISCO_CHURN = [
    "Baixo",
    "Médio",
    "Alto",
    "Não avaliado",
]


NIVEIS_ENTUSIASMO = [
    "Muito alto",
    "Alto",
    "Médio",
    "Baixo",
    "Não avaliado",
]


PROXIMOS_PASSOS_FUNDADOR = [
    "Enviar link do app",
    "Enviar instruções de uso",
    "Pedir primeira análise",
    "Pedir feedback do relatório",
    "Agendar conversa de 15 minutos",
    "Oferecer condição fundador",
    "Coletar depoimento",
    "Aguardar evolução do produto",
    "Encerrar acompanhamento",
]


def _limpar_texto(valor: Any) -> str:
    if valor is None:
        return ""

    return str(valor).strip()


def _garantir_arquivo() -> None:
    if CAMINHO_FUNDADORES_VALORIS.exists():
        return

    with CAMINHO_FUNDADORES_VALORIS.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_FUNDADOR)
        escritor.writeheader()


def carregar_fundadores_valoris() -> List[Dict[str, str]]:
    _garantir_arquivo()

    with CAMINHO_FUNDADORES_VALORIS.open("r", newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        return list(leitor)


def salvar_fundadores_valoris(registros: List[Dict[str, Any]]) -> None:
    with CAMINHO_FUNDADORES_VALORIS.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_FUNDADOR)
        escritor.writeheader()

        for registro in registros:
            escritor.writerow({campo: registro.get(campo, "") for campo in CAMPOS_FUNDADOR})


def gerar_csv_fundadores_valoris() -> str:
    _garantir_arquivo()

    return CAMINHO_FUNDADORES_VALORIS.read_text(encoding="utf-8")


def _obter_candidatos_fundadores() -> List[Dict[str, str]]:
    try:
        validacoes = carregar_validacoes_manuais()
    except Exception:
        validacoes = []

    candidatos = []

    for validacao in validacoes:
        intencao = validacao.get("intencao", "")
        status = validacao.get("status", "")
        prioridade = validacao.get("prioridade", "")

        score = 40

        if intencao == "Alta intenção":
            score += 30
        elif intencao == "Intenção promissora":
            score += 18

        if status in ["Compraria", "Demonstrou intenção"]:
            score += 25
        elif status in ["Agendou conversa", "Testou o produto"]:
            score += 15

        if prioridade == "Muito alta":
            score += 12
        elif prioridade == "Alta":
            score += 8

        score = max(0, min(100, score))

        if score >= 80:
            recomendacao = "Convidar para fundador"
        elif score >= 65:
            recomendacao = "Conversar antes de ofertar"
        elif score >= 50:
            recomendacao = "Nutrir e pedir feedback"
        else:
            recomendacao = "Não priorizar agora"

        candidatos.append(
            {
                "nome": validacao.get("nome", ""),
                "contato": validacao.get("contato", ""),
                "perfil": validacao.get("perfil", ""),
                "dor": validacao.get("dor", ""),
                "oferta_testada": validacao.get("oferta_testada", ""),
                "preco_testado": validacao.get("preco_testado", ""),
                "intencao": intencao,
                "status": status,
                "prioridade": prioridade,
                "score": str(score),
                "recomendacao": recomendacao,
            }
        )

    return sorted(
        candidatos,
        key=lambda item: int(item.get("score", "0") or 0),
        reverse=True,
    )


def adicionar_fundador_valoris(
    nome: str,
    contato: str,
    origem: str,
    perfil: str,
    dor_principal: str,
    plano: str,
    valor_combinado: str,
    status_pagamento: str,
    status_acesso: str,
    etapa_onboarding: str,
    uso_inicial: str,
    feedback_principal: str,
    risco_churn: str,
    nivel_entusiasmo: str,
    proximo_passo: str,
    observacoes: str,
) -> Dict[str, str]:
    registros = carregar_fundadores_valoris()

    novo = {
        "id": str(uuid4())[:8],
        "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "nome": _limpar_texto(nome),
        "contato": _limpar_texto(contato),
        "origem": _limpar_texto(origem),
        "perfil": _limpar_texto(perfil),
        "dor_principal": _limpar_texto(dor_principal),
        "plano": plano,
        "valor_combinado": _limpar_texto(valor_combinado),
        "status_pagamento": status_pagamento,
        "status_acesso": status_acesso,
        "etapa_onboarding": etapa_onboarding,
        "uso_inicial": uso_inicial,
        "feedback_principal": _limpar_texto(feedback_principal),
        "risco_churn": risco_churn,
        "nivel_entusiasmo": nivel_entusiasmo,
        "proximo_passo": proximo_passo,
        "observacoes": _limpar_texto(observacoes),
    }

    registros.append(novo)
    salvar_fundadores_valoris(registros)

    return novo


def _contar_por_campo(registros: List[Dict[str, str]], campo: str) -> Dict[str, int]:
    contagem: Dict[str, int] = {}

    for registro in registros:
        valor = registro.get(campo, "N/D") or "N/D"
        contagem[valor] = contagem.get(valor, 0) + 1

    return contagem


def _mais_comum(registros: List[Dict[str, str]], campo: str) -> str:
    contagem = _contar_por_campo(registros, campo)

    if not contagem:
        return "N/D"

    return sorted(contagem.items(), key=lambda item: item[1], reverse=True)[0][0]


def _fmt_moeda(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _calcular_metricas_fundadores(registros: List[Dict[str, str]]) -> Dict[str, Any]:
    pagos = [item for item in registros if item.get("status_pagamento") == "Pago manualmente"]
    acessos = [item for item in registros if item.get("status_acesso") in ["Acesso liberado", "Em teste"]]
    relatorios = [
        item for item in registros
        if item.get("etapa_onboarding") in ["Baixou relatório", "Enviou feedback", "Virou caso de sucesso"]
    ]
    risco_alto = [item for item in registros if item.get("risco_churn") == "Alto"]

    receita_manual = 0.0

    for item in pagos:
        texto = item.get("valor_combinado", "")
        numero = "".join(caractere for caractere in texto if caractere.isdigit() or caractere in [",", "."])

        try:
            receita_manual += float(numero.replace(".", "").replace(",", "."))
        except ValueError:
            continue

    return {
        "fundadores": len(registros),
        "pagos": len(pagos),
        "acessos": len(acessos),
        "relatorios": len(relatorios),
        "risco_alto": len(risco_alto),
        "receita_manual": receita_manual,
        "plano_dominante": _mais_comum(registros, "plano"),
        "etapa_dominante": _mais_comum(registros, "etapa_onboarding"),
    }


def _gerar_mensagem_onboarding(nome: str, plano: str, proximo_passo: str) -> str:
    nome_limpo = nome.strip() or "tudo bem"

    return f"""Olá, {nome_limpo}! Você está entrando no beta da Valoris.

Plano/condição:
{plano}

Como usar primeiro:
1. Abra a Landing Page para entender a proposta.
2. Passe pelo Copiloto para receber um diagnóstico.
3. Use a Jornada para saber seu próximo passo.
4. Faça a Demonstração Guiada.
5. Só depois rode uma análise com premissas conservadoras.
6. Baixe o relatório e me envie feedback sincero.

Próximo passo combinado:
{proximo_passo}

Importante:
A Valoris é educacional. Não recomenda compra ou venda de ativos e não promete rentabilidade.
A ideia é ajudar você a pensar melhor antes de investir."""


def _gerar_relatorio_fundadores(registros: List[Dict[str, str]], candidatos: List[Dict[str, str]]) -> str:
    metricas = _calcular_metricas_fundadores(registros)

    if metricas["fundadores"] == 0:
        leitura = "Ainda não há fundadores registrados. O próximo passo é convidar manualmente 3 a 5 leads de maior intenção."
    elif metricas["pagos"] == 0:
        leitura = "Já há fundadores/usuários beta, mas ainda sem pagamento manual registrado. Valide valor percebido antes de criar checkout."
    elif metricas["relatorios"] == 0:
        leitura = "Existe sinal de pagamento/acesso, mas ainda falta levar usuários até o relatório. O foco deve ser ativação."
    else:
        leitura = "Já existe fluxo fundador mais maduro. Priorize feedback qualitativo, depoimentos e melhoria de entrega."

    top_candidatos = "\n".join(
        [
            f"- {item.get('nome', 'N/D')} | {item.get('contato', 'N/D')} | Score {item.get('score', 'N/D')} | {item.get('recomendacao', 'N/D')}"
            for item in candidatos[:10]
        ]
    )

    return f"""# Central de Fundadores — Valoris

Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Métricas

Fundadores/usuários beta: {metricas["fundadores"]}  
Pagamentos manuais: {metricas["pagos"]}  
Acessos liberados/em teste: {metricas["acessos"]}  
Chegaram ao relatório/feedback: {metricas["relatorios"]}  
Risco alto de churn: {metricas["risco_alto"]}  
Receita manual estimada: {_fmt_moeda(metricas["receita_manual"])}  
Plano dominante: {metricas["plano_dominante"]}  
Etapa dominante: {metricas["etapa_dominante"]}  

## Leitura

{leitura}

## Candidatos prioritários

{top_candidatos}

## Próximo passo

Escolha até 5 candidatos com maior score e faça onboarding manual antes de escalar aquisição.
"""


def _injetar_css_fundadores() -> None:
    st.markdown(
        """
        <style>
            .fund-hero {
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

            .fund-eyebrow {
                color: #d6b56d;
                font-size: 0.74rem;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                font-weight: 880;
                margin-bottom: 0.35rem;
            }

            .fund-title {
                color: #f4f7fb;
                font-size: clamp(1.75rem, 5.4vw, 3.1rem);
                font-weight: 950;
                line-height: 1.02;
                letter-spacing: -0.058em;
                margin-bottom: 0.55rem;
            }

            .fund-subtitle {
                color: rgba(244, 247, 251, 0.75);
                font-size: clamp(0.94rem, 2.2vw, 1.06rem);
                line-height: 1.56;
                max-width: 1020px;
            }

            .fund-note {
                padding: 0.92rem 0.98rem;
                border-radius: 17px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.90rem;
                line-height: 1.55;
                margin: 0.85rem 0;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _renderizar_hero() -> None:
    st.markdown(
        f"""
        <div class="fund-hero">
            <div class="fund-eyebrow">Valoris • Fundadores • v{VERSAO_CENTRAL_FUNDADORES_VALORIS}</div>
            <div class="fund-title">Transforme interessados em usuários fundadores.</div>
            <div class="fund-subtitle">
                Depois da validação manual, a Valoris precisa acompanhar quem entrou, quem pagou,
                quem testou, quem chegou ao relatório e quem pode virar caso de sucesso.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _renderizar_metricas(registros: List[Dict[str, str]]) -> None:
    metricas = _calcular_metricas_fundadores(registros)

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Fundadores", metricas["fundadores"])

    with col_2:
        st.metric("Pagos", metricas["pagos"])

    with col_3:
        st.metric("Acessos", metricas["acessos"])

    with col_4:
        st.metric("Receita manual", _fmt_moeda(metricas["receita_manual"]))

    col_5, col_6, col_7 = st.columns(3)

    with col_5:
        st.metric("Relatório/feedback", metricas["relatorios"])

    with col_6:
        st.metric("Risco alto", metricas["risco_alto"])

    with col_7:
        st.metric("Etapa dominante", metricas["etapa_dominante"])


def _renderizar_candidatos(candidatos: List[Dict[str, str]]) -> None:
    st.markdown("### Candidatos a fundador")

    if not candidatos:
        st.info("Ainda não há validações manuais suficientes para sugerir fundadores.")
        return

    for candidato in candidatos[:12]:
        with st.container(border=True):
            st.markdown(f"**{candidato.get('nome', 'N/D')}** — Score {candidato.get('score', 'N/D')}/100")
            st.caption(
                f"{candidato.get('contato', 'N/D')} • {candidato.get('recomendacao', 'N/D')} • {candidato.get('prioridade', 'N/D')}"
            )
            st.markdown(f"**Intenção:** {candidato.get('intencao', 'N/D')}")
            st.markdown(f"**Status:** {candidato.get('status', 'N/D')}")
            st.markdown(f"**Oferta testada:** {candidato.get('oferta_testada', 'N/D')} • {candidato.get('preco_testado', 'N/D')}")


def _renderizar_formulario_fundador(candidatos: List[Dict[str, str]]) -> None:
    st.markdown("### Registrar fundador / usuário beta")

    opcoes = ["Preencher manualmente"]

    for candidato in candidatos[:30]:
        opcoes.append(f"{candidato.get('nome', '')} | {candidato.get('contato', '')}")

    candidato_escolhido = st.selectbox(
        "Usar candidato da validação manual",
        opcoes,
        key="fundador_candidato_escolhido",
    )

    base: Dict[str, str] = {}

    if candidato_escolhido != "Preencher manualmente":
        contato = candidato_escolhido.split("|")[-1].strip()

        for candidato in candidatos:
            if candidato.get("contato", "") == contato:
                base = candidato
                break

    with st.form("form_central_fundadores_valoris"):
        col_1, col_2 = st.columns(2)

        with col_1:
            nome = st.text_input("Nome", value=base.get("nome", ""), key="fund_nome")
            contato = st.text_input("Contato", value=base.get("contato", ""), key="fund_contato")
            origem = st.text_input("Origem", value="Validação manual", key="fund_origem")
            perfil = st.text_input("Perfil", value=base.get("perfil", ""), key="fund_perfil")
            dor_principal = st.text_area("Dor principal", value=base.get("dor", ""), height=80, key="fund_dor")

        with col_2:
            plano = st.selectbox("Plano/condição", PLANOS_FUNDADOR, key="fund_plano")
            valor_combinado = st.text_input("Valor combinado", value="R$ 97", key="fund_valor")
            status_pagamento = st.selectbox("Status pagamento", STATUS_PAGAMENTO, key="fund_pagamento")
            status_acesso = st.selectbox("Status acesso", STATUS_ACESSO, key="fund_acesso")
            etapa_onboarding = st.selectbox("Etapa onboarding", ETAPAS_ONBOARDING, key="fund_onboarding")

        col_3, col_4 = st.columns(2)

        with col_3:
            uso_inicial = st.selectbox("Uso inicial", USO_INICIAL, key="fund_uso")
            risco_churn = st.selectbox("Risco churn", RISCO_CHURN, key="fund_churn")

        with col_4:
            nivel_entusiasmo = st.selectbox("Nível entusiasmo", NIVEIS_ENTUSIASMO, key="fund_entusiasmo")
            proximo_passo = st.selectbox("Próximo passo", PROXIMOS_PASSOS_FUNDADOR, key="fund_proximo")

        feedback_principal = st.text_area("Feedback principal", height=100, key="fund_feedback")
        observacoes = st.text_area("Observações internas", height=80, key="fund_obs")

        enviado = st.form_submit_button("Salvar fundador")

        if enviado:
            registro = adicionar_fundador_valoris(
                nome=nome,
                contato=contato,
                origem=origem,
                perfil=perfil,
                dor_principal=dor_principal,
                plano=plano,
                valor_combinado=valor_combinado,
                status_pagamento=status_pagamento,
                status_acesso=status_acesso,
                etapa_onboarding=etapa_onboarding,
                uso_inicial=uso_inicial,
                feedback_principal=feedback_principal,
                risco_churn=risco_churn,
                nivel_entusiasmo=nivel_entusiasmo,
                proximo_passo=proximo_passo,
                observacoes=observacoes,
            )

            st.success(f"Fundador registrado: {registro['nome']} • {registro['plano']}")
            st.rerun()


def _renderizar_mensagem_onboarding() -> None:
    st.markdown("### Gerador de mensagem de onboarding")

    with st.expander("Criar mensagem para fundador", expanded=False):
        nome = st.text_input("Nome", key="fund_msg_nome")
        plano = st.selectbox("Plano", PLANOS_FUNDADOR, key="fund_msg_plano")
        proximo = st.selectbox("Próximo passo", PROXIMOS_PASSOS_FUNDADOR, key="fund_msg_proximo")

        mensagem = _gerar_mensagem_onboarding(
            nome=nome,
            plano=plano,
            proximo_passo=proximo,
        )

        st.text_area(
            "Mensagem pronta",
            value=mensagem,
            height=330,
            key="fund_msg_pronta",
        )


def _renderizar_fundadores(registros: List[Dict[str, str]]) -> None:
    st.markdown("### Fundadores registrados")

    if not registros:
        st.info("Ainda não há fundadores registrados.")
        return

    for registro in reversed(registros[-20:]):
        with st.container(border=True):
            st.markdown(f"**{registro.get('nome', 'N/D')}** — {registro.get('plano', 'N/D')}")
            st.caption(
                f"{registro.get('data_registro', 'N/D')} • {registro.get('status_pagamento', 'N/D')} • {registro.get('status_acesso', 'N/D')}"
            )
            st.markdown(f"**Etapa:** {registro.get('etapa_onboarding', 'N/D')}")
            st.markdown(f"**Uso:** {registro.get('uso_inicial', 'N/D')}")
            st.markdown(f"**Entusiasmo:** {registro.get('nivel_entusiasmo', 'N/D')} • **Risco churn:** {registro.get('risco_churn', 'N/D')}")
            st.markdown(f"**Próximo passo:** {registro.get('proximo_passo', 'N/D')}")


def renderizar_central_fundadores_valoris() -> None:
    _injetar_css_fundadores()
    _renderizar_hero()

    registros = carregar_fundadores_valoris()
    candidatos = _obter_candidatos_fundadores()

    _renderizar_metricas(registros)

    st.divider()

    _renderizar_candidatos(candidatos)

    st.divider()

    _renderizar_mensagem_onboarding()

    st.divider()

    _renderizar_formulario_fundador(candidatos)

    st.divider()

    _renderizar_fundadores(registros)

    st.divider()

    st.download_button(
        "Baixar relatório de fundadores (.md)",
        data=_gerar_relatorio_fundadores(registros, candidatos),
        file_name="central_fundadores_valoris.md",
        mime="text/markdown",
        key="download_relatorio_fundadores_valoris",
    )

    st.download_button(
        "Baixar fundadores (.csv)",
        data=gerar_csv_fundadores_valoris(),
        file_name="fundadores_valoris.csv",
        mime="text/csv",
        key="download_fundadores_valoris",
    )

    st.markdown(
        """
        <div class="fund-note">
            <strong>Regra da central:</strong> usuário fundador não é só lead. Ele precisa de onboarding,
            acompanhamento, feedback e uma entrega que justifique confiança.
        </div>
        """,
        unsafe_allow_html=True,
    )


def executar_autoteste_central_fundadores_valoris() -> List[Dict[str, str]]:
    mensagem = _gerar_mensagem_onboarding(
        nome="Leo",
        plano="Beta Fundador R$ 97",
        proximo_passo="Enviar instruções de uso",
    )

    return [
        {
            "teste": "versao_fundadores",
            "status": "OK" if VERSAO_CENTRAL_FUNDADORES_VALORIS == "3.8.53" else "FALHA",
            "detalhe": VERSAO_CENTRAL_FUNDADORES_VALORIS,
        },
        {
            "teste": "campos_fundador",
            "status": "OK" if "status_pagamento" in CAMPOS_FUNDADOR else "FALHA",
            "detalhe": str(len(CAMPOS_FUNDADOR)),
        },
        {
            "teste": "mensagem_onboarding",
            "status": "OK" if "Valoris" in mensagem else "FALHA",
            "detalhe": "Mensagem gerada.",
        },
    ]
