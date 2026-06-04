# validacao_manual_valoris.py

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

import streamlit as st

from conversao_fundador_valoris import carregar_sinais_conversao
from lista_espera_beta import carregar_leads_lista_espera


# ============================================================
# VALORIS
# v3.8.53.1 — Validação Manual e CRM Fundador
# ------------------------------------------------------------
# Arquivo necessário para a v3.8.53.
#
# Objetivo:
# - organizar contatos manuais com leads;
# - priorizar pessoas com maior intenção comercial;
# - registrar objeções, respostas e próximos passos;
# - validar oferta antes de criar checkout;
# - alimentar a Central de Fundadores.
# ============================================================


VERSAO_VALIDACAO_MANUAL_VALORIS = "3.8.53.1"

CAMINHO_VALIDACOES_MANUAIS = Path("validacoes_manuais_valoris.csv")

CAMPOS_VALIDACAO = [
    "id",
    "data_registro",
    "nome",
    "contato",
    "origem",
    "perfil",
    "dor",
    "oferta_testada",
    "preco_testado",
    "canal",
    "status",
    "intencao",
    "objecao",
    "resposta_manual",
    "proximo_passo",
    "prioridade",
    "observacoes",
]


CANAIS_CONTATO = [
    "WhatsApp",
    "E-mail",
    "Instagram",
    "Telegram",
    "Ligação",
    "Presencial",
    "Outro",
]


STATUS_VALIDACAO = [
    "Selecionado para contato",
    "Mensagem enviada",
    "Respondeu",
    "Agendou conversa",
    "Testou o produto",
    "Demonstrou intenção",
    "Compraria",
    "Não compraria",
    "Aguardando evolução",
    "Perdido",
]


OFERTAS_TESTADAS = [
    "Lista beta gratuita",
    "Relatório Premium Avulso",
    "Beta Mensal R$ 19,90",
    "Beta Fundador R$ 97",
    "Premium futuro com automação",
    "Conversa de descoberta",
]


INTENCOES_MANUAIS = [
    "Alta intenção",
    "Intenção promissora",
    "Curioso",
    "Precisa entender melhor",
    "Baixa intenção",
    "Não respondeu",
]


OBJECOES_COMUNS = [
    "Não entendeu o produto",
    "Quer dados automáticos",
    "Quer testar com ação real",
    "Não confia em valuation",
    "Achou caro",
    "Precisa de visual mais profissional",
    "Não vê urgência",
    "Sem objeção forte",
    "Não informado",
]


PROXIMOS_PASSOS = [
    "Enviar link do app",
    "Enviar mensagem de convite beta",
    "Enviar exemplo de relatório",
    "Marcar conversa de 15 minutos",
    "Oferecer beta fundador manualmente",
    "Pedir feedback específico",
    "Aguardar nova versão",
    "Encerrar por enquanto",
]


def _limpar_texto(valor: Any) -> str:
    if valor is None:
        return ""

    return str(valor).strip()


def _garantir_arquivo() -> None:
    if CAMINHO_VALIDACOES_MANUAIS.exists():
        return

    with CAMINHO_VALIDACOES_MANUAIS.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_VALIDACAO)
        escritor.writeheader()


def carregar_validacoes_manuais() -> List[Dict[str, str]]:
    _garantir_arquivo()

    with CAMINHO_VALIDACOES_MANUAIS.open("r", newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        return list(leitor)


def salvar_validacoes_manuais(registros: List[Dict[str, Any]]) -> None:
    with CAMINHO_VALIDACOES_MANUAIS.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_VALIDACAO)
        escritor.writeheader()

        for registro in registros:
            escritor.writerow({campo: registro.get(campo, "") for campo in CAMPOS_VALIDACAO})


def gerar_csv_validacoes_manuais() -> str:
    _garantir_arquivo()

    return CAMINHO_VALIDACOES_MANUAIS.read_text(encoding="utf-8")


def _obter_leads_priorizados() -> List[Dict[str, str]]:
    try:
        leads = carregar_leads_lista_espera()
    except Exception:
        leads = []

    try:
        conversoes = carregar_sinais_conversao()
    except Exception:
        conversoes = []

    alta_intencao = [
        sinal for sinal in conversoes
        if "Alta" in sinal.get("intencao", "")
    ]

    lista_priorizada: List[Dict[str, str]] = []

    for lead in leads:
        pagaria = lead.get("pagaria_agora", "")
        preco = lead.get("preco_aceitavel", "")
        dor = lead.get("principal_dor", "")
        perfil = lead.get("perfil", "")

        score = 40

        if "Sim" in pagaria:
            score += 30
        elif "Talvez" in pagaria:
            score += 18

        if "49" in preco or "29" in preco or "97" in preco:
            score += 12
        elif "19" in preco:
            score += 8

        if "caro" in dor.lower() or "premissa" in dor.lower() or "valuation" in dor.lower():
            score += 10

        if "Avançado" in perfil or "Intermediário" in perfil:
            score += 6

        if alta_intencao:
            score += 4

        score = max(0, min(100, score))

        if score >= 82:
            prioridade = "Muito alta"
        elif score >= 68:
            prioridade = "Alta"
        elif score >= 50:
            prioridade = "Média"
        else:
            prioridade = "Baixa"

        lista_priorizada.append(
            {
                "nome": lead.get("nome", ""),
                "contato": lead.get("contato", ""),
                "perfil": perfil,
                "dor": dor,
                "plano_interesse": lead.get("plano_interesse", ""),
                "preco_aceitavel": preco,
                "pagaria_agora": pagaria,
                "score": str(score),
                "prioridade": prioridade,
            }
        )

    return sorted(
        lista_priorizada,
        key=lambda item: int(item.get("score", "0") or 0),
        reverse=True,
    )


def _calcular_prioridade_por_formulario(
    intencao: str,
    status: str,
    objecao: str,
) -> str:
    if intencao == "Alta intenção" or status in ["Compraria", "Demonstrou intenção"]:
        return "Muito alta"

    if intencao == "Intenção promissora" or status in ["Agendou conversa", "Testou o produto"]:
        return "Alta"

    if objecao in ["Quer dados automáticos", "Quer testar com ação real", "Precisa de visual mais profissional"]:
        return "Média"

    if intencao in ["Baixa intenção", "Não respondeu"] or status in ["Não compraria", "Perdido"]:
        return "Baixa"

    return "Média"


def adicionar_validacao_manual(
    nome: str,
    contato: str,
    origem: str,
    perfil: str,
    dor: str,
    oferta_testada: str,
    preco_testado: str,
    canal: str,
    status: str,
    intencao: str,
    objecao: str,
    resposta_manual: str,
    proximo_passo: str,
    observacoes: str,
) -> Dict[str, str]:
    registros = carregar_validacoes_manuais()

    prioridade = _calcular_prioridade_por_formulario(
        intencao=intencao,
        status=status,
        objecao=objecao,
    )

    novo = {
        "id": str(uuid4())[:8],
        "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "nome": _limpar_texto(nome),
        "contato": _limpar_texto(contato),
        "origem": _limpar_texto(origem),
        "perfil": _limpar_texto(perfil),
        "dor": _limpar_texto(dor),
        "oferta_testada": oferta_testada,
        "preco_testado": _limpar_texto(preco_testado),
        "canal": canal,
        "status": status,
        "intencao": intencao,
        "objecao": objecao,
        "resposta_manual": _limpar_texto(resposta_manual),
        "proximo_passo": proximo_passo,
        "prioridade": prioridade,
        "observacoes": _limpar_texto(observacoes),
    }

    registros.append(novo)
    salvar_validacoes_manuais(registros)

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


def _gerar_mensagem_abordagem(
    nome: str,
    dor: str,
    oferta: str,
    preco: str,
) -> str:
    nome_limpo = nome.strip() or "tudo bem"

    return f"""Olá, {nome_limpo}! Estou testando uma versão beta da Valoris.

Vi que sua principal dor é:
{dor or "entender melhor se uma decisão de investimento faz sentido antes da compra."}

A Valoris está sendo construída para ajudar investidores a:
- comparar preço atual com preço-teto;
- revisar margem de segurança;
- auditar riscos e premissas;
- gerar um relatório claro da análise;
- evitar decisão por impulso.

A condição que estou validando agora é:
{oferta} — {preco or "condição beta em validação"}

Importante: não é recomendação de investimento e não promete rentabilidade. É uma ferramenta educacional para organizar raciocínio e melhorar decisões.

Faz sentido eu te mandar o link/teste para você avaliar e me dar um feedback sincero?"""


def _gerar_relatorio_validacao(registros: List[Dict[str, str]], leads_priorizados: List[Dict[str, str]]) -> str:
    total = len(registros)
    alta_intencao = len([item for item in registros if item.get("intencao") == "Alta intenção"])
    compraria = len([item for item in registros if item.get("status") == "Compraria"])
    oferta_top = _mais_comum(registros, "oferta_testada")
    objecao_top = _mais_comum(registros, "objecao")

    if total == 0:
        leitura = "Ainda não há validações manuais registradas. O próximo passo é falar com 5 leads priorizados."
    elif alta_intencao > 0 or compraria > 0:
        leitura = "Já existem sinais comerciais. Priorize conversa direta e teste de oferta fundador antes de checkout."
    else:
        leitura = "Ainda não há compra clara. Foque em entender objeções e melhorar valor percebido."

    top_leads = "\n".join(
        [
            f"- {lead.get('nome', 'N/D')} | {lead.get('contato', 'N/D')} | Score {lead.get('score', 'N/D')} | {lead.get('prioridade', 'N/D')}"
            for lead in leads_priorizados[:10]
        ]
    )

    return f"""# Validação Manual — Valoris

Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Resumo

Validações registradas: {total}  
Alta intenção: {alta_intencao}  
Status "Compraria": {compraria}  
Oferta mais testada: {oferta_top}  
Objeção dominante: {objecao_top}  

## Leitura

{leitura}

## Leads priorizados

{top_leads}

## Próximo passo recomendado

Falar manualmente com 5 pessoas de prioridade alta ou muito alta antes de criar checkout.
"""


def _injetar_css_validacao() -> None:
    st.markdown(
        """
        <style>
            .val-hero {
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

            .val-eyebrow {
                color: #d6b56d;
                font-size: 0.74rem;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                font-weight: 880;
                margin-bottom: 0.35rem;
            }

            .val-title {
                color: #f4f7fb;
                font-size: clamp(1.75rem, 5.4vw, 3.1rem);
                font-weight: 950;
                line-height: 1.02;
                letter-spacing: -0.058em;
                margin-bottom: 0.55rem;
            }

            .val-subtitle {
                color: rgba(244, 247, 251, 0.75);
                font-size: clamp(0.94rem, 2.2vw, 1.06rem);
                line-height: 1.56;
                max-width: 1020px;
            }

            .val-note {
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
        <div class="val-hero">
            <div class="val-eyebrow">Valoris • Validação manual • v{VERSAO_VALIDACAO_MANUAL_VALORIS}</div>
            <div class="val-title">Fale com usuários antes de criar checkout.</div>
            <div class="val-subtitle">
                O próximo salto da Valoris não é automatizar cobrança. É descobrir, manualmente,
                quem sente valor real, qual oferta faz sentido e qual objeção ainda bloqueia compra.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _renderizar_metricas(registros: List[Dict[str, str]], leads_priorizados: List[Dict[str, str]]) -> None:
    alta = len([item for item in registros if item.get("intencao") == "Alta intenção"])
    compraria = len([item for item in registros if item.get("status") == "Compraria"])
    pendentes = len([item for item in registros if item.get("status") in ["Selecionado para contato", "Mensagem enviada"]])

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Leads priorizados", len(leads_priorizados))

    with col_2:
        st.metric("Validações", len(registros))

    with col_3:
        st.metric("Alta intenção", alta)

    with col_4:
        st.metric("Compraria", compraria)

    col_5, col_6 = st.columns(2)

    with col_5:
        st.metric("Pendentes", pendentes)

    with col_6:
        st.metric("Objeção dominante", _mais_comum(registros, "objecao"))


def _renderizar_leads_priorizados(leads_priorizados: List[Dict[str, str]]) -> None:
    st.markdown("### Leads priorizados para contato")

    if not leads_priorizados:
        st.info("Ainda não há leads na lista beta.")
        return

    for lead in leads_priorizados[:12]:
        with st.container(border=True):
            st.markdown(f"**{lead.get('nome', 'N/D')}** — Score {lead.get('score', 'N/D')}/100")
            st.caption(f"{lead.get('contato', 'N/D')} • Prioridade: {lead.get('prioridade', 'N/D')}")
            st.markdown(f"**Perfil:** {lead.get('perfil', 'N/D')}")
            st.markdown(f"**Dor:** {lead.get('dor', 'N/D')}")
            st.markdown(f"**Pagaria agora:** {lead.get('pagaria_agora', 'N/D')}")
            st.markdown(f"**Preço aceitável:** {lead.get('preco_aceitavel', 'N/D')}")


def _renderizar_formulario_validacao() -> None:
    st.markdown("### Registrar validação manual")

    leads_priorizados = _obter_leads_priorizados()
    opcoes_leads = ["Preencher manualmente"]

    for lead in leads_priorizados[:30]:
        nome = lead.get("nome", "")
        contato = lead.get("contato", "")
        opcoes_leads.append(f"{nome} | {contato}")

    lead_escolhido = st.selectbox(
        "Usar lead da lista beta",
        opcoes_leads,
        key="validacao_lead_escolhido",
    )

    lead_base: Dict[str, str] = {}

    if lead_escolhido != "Preencher manualmente":
        contato_escolhido = lead_escolhido.split("|")[-1].strip()

        for lead in leads_priorizados:
            if lead.get("contato", "") == contato_escolhido:
                lead_base = lead
                break

    with st.form("form_validacao_manual_valoris"):
        col_1, col_2 = st.columns(2)

        with col_1:
            nome = st.text_input("Nome", value=lead_base.get("nome", ""), key="validacao_nome")
            contato = st.text_input("Contato", value=lead_base.get("contato", ""), key="validacao_contato")
            origem = st.text_input("Origem", value="Lista beta", key="validacao_origem")
            perfil = st.text_input("Perfil", value=lead_base.get("perfil", ""), key="validacao_perfil")
            dor = st.text_area("Dor principal", value=lead_base.get("dor", ""), height=80, key="validacao_dor")

        with col_2:
            oferta_testada = st.selectbox("Oferta testada", OFERTAS_TESTADAS, index=3, key="validacao_oferta")
            preco_testado = st.text_input("Preço/condição testada", value="R$ 97 pagamento único", key="validacao_preco")
            canal = st.selectbox("Canal", CANAIS_CONTATO, key="validacao_canal")
            status = st.selectbox("Status", STATUS_VALIDACAO, key="validacao_status")
            intencao = st.selectbox("Intenção", INTENCOES_MANUAIS, key="validacao_intencao")
            objecao = st.selectbox("Objeção principal", OBJECOES_COMUNS, key="validacao_objecao")

        resposta_manual = st.text_area("Resposta do lead / resumo da conversa", height=110, key="validacao_resposta")
        proximo_passo = st.selectbox("Próximo passo", PROXIMOS_PASSOS, key="validacao_proximo_passo")
        observacoes = st.text_area("Observações internas", height=80, key="validacao_observacoes")

        enviado = st.form_submit_button("Salvar validação manual")

        if enviado:
            registro = adicionar_validacao_manual(
                nome=nome,
                contato=contato,
                origem=origem,
                perfil=perfil,
                dor=dor,
                oferta_testada=oferta_testada,
                preco_testado=preco_testado,
                canal=canal,
                status=status,
                intencao=intencao,
                objecao=objecao,
                resposta_manual=resposta_manual,
                proximo_passo=proximo_passo,
                observacoes=observacoes,
            )

            st.success(
                f"Validação registrada: {registro['nome']} • {registro['intencao']} • Prioridade {registro['prioridade']}"
            )
            st.rerun()


def _renderizar_mensagem_manual() -> None:
    st.markdown("### Gerador de mensagem manual")

    with st.expander("Criar mensagem de abordagem", expanded=False):
        nome = st.text_input("Nome do lead", value="", key="msg_nome_lead")
        dor = st.text_area("Dor do lead", value="", height=80, key="msg_dor_lead")
        oferta = st.selectbox("Oferta", OFERTAS_TESTADAS, index=3, key="msg_oferta")
        preco = st.text_input("Preço/condição", value="R$ 97 pagamento único", key="msg_preco")

        mensagem = _gerar_mensagem_abordagem(
            nome=nome,
            dor=dor,
            oferta=oferta,
            preco=preco,
        )

        st.text_area(
            "Mensagem pronta para copiar",
            value=mensagem,
            height=310,
            key="msg_abordagem_pronta",
        )


def _renderizar_validacoes(registros: List[Dict[str, str]]) -> None:
    st.markdown("### Validações registradas")

    if not registros:
        st.info("Ainda não há validações manuais registradas.")
        return

    for registro in reversed(registros[-20:]):
        with st.container(border=True):
            st.markdown(f"**{registro.get('nome', 'N/D')}** — {registro.get('intencao', 'N/D')}")
            st.caption(
                f"{registro.get('data_registro', 'N/D')} • {registro.get('canal', 'N/D')} • Prioridade {registro.get('prioridade', 'N/D')}"
            )
            st.markdown(f"**Oferta:** {registro.get('oferta_testada', 'N/D')} • {registro.get('preco_testado', 'N/D')}")
            st.markdown(f"**Status:** {registro.get('status', 'N/D')}")
            st.markdown(f"**Objeção:** {registro.get('objecao', 'N/D')}")
            st.markdown(f"**Próximo passo:** {registro.get('proximo_passo', 'N/D')}")


def renderizar_validacao_manual_valoris() -> None:
    _injetar_css_validacao()
    _renderizar_hero()

    registros = carregar_validacoes_manuais()
    leads_priorizados = _obter_leads_priorizados()

    _renderizar_metricas(registros, leads_priorizados)

    st.divider()

    _renderizar_leads_priorizados(leads_priorizados)

    st.divider()

    _renderizar_mensagem_manual()

    st.divider()

    _renderizar_formulario_validacao()

    st.divider()

    _renderizar_validacoes(registros)

    st.divider()

    st.download_button(
        "Baixar relatório de validação (.md)",
        data=_gerar_relatorio_validacao(registros, leads_priorizados),
        file_name="validacao_manual_valoris.md",
        mime="text/markdown",
        key="download_relatorio_validacao_manual",
    )

    st.download_button(
        "Baixar validações manuais (.csv)",
        data=gerar_csv_validacoes_manuais(),
        file_name="validacoes_manuais_valoris.csv",
        mime="text/csv",
        key="download_validacoes_manuais_valoris",
    )

    st.markdown(
        """
        <div class="val-note">
            <strong>Regra da validação:</strong> não crie checkout antes de falar com usuários.
            Primeiro valide dor, linguagem, objeção, oferta e disposição real de pagamento.
        </div>
        """,
        unsafe_allow_html=True,
    )


def executar_autoteste_validacao_manual_valoris() -> List[Dict[str, str]]:
    prioridade = _calcular_prioridade_por_formulario(
        intencao="Alta intenção",
        status="Demonstrou intenção",
        objecao="Sem objeção forte",
    )

    mensagem = _gerar_mensagem_abordagem(
        nome="Leo",
        dor="Medo de comprar ação cara",
        oferta="Beta Fundador R$ 97",
        preco="R$ 97",
    )

    return [
        {
            "teste": "versao_validacao",
            "status": "OK" if VERSAO_VALIDACAO_MANUAL_VALORIS == "3.8.53.1" else "FALHA",
            "detalhe": VERSAO_VALIDACAO_MANUAL_VALORIS,
        },
        {
            "teste": "prioridade",
            "status": "OK" if prioridade == "Muito alta" else "FALHA",
            "detalhe": prioridade,
        },
        {
            "teste": "mensagem",
            "status": "OK" if "Valoris" in mensagem else "FALHA",
            "detalhe": "Mensagem gerada.",
        },
    ]
