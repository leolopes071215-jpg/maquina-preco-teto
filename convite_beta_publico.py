# convite_beta_publico.py

from datetime import datetime
from typing import Any, Dict, List

import streamlit as st


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v1.39 — Página Pública e Convite Beta
# ------------------------------------------------------------
# Esta tela organiza a comunicação para enviar o app a usuários reais.
#
# Objetivo:
# - gerar convite beta profissional
# - orientar o usuário a testar sem se perder
# - reforçar aviso educacional
# - aumentar chance de feedback real
# - preparar a ponte entre MVP e Fase 2
# ============================================================


CANAIS_CONVITE = [
    "WhatsApp",
    "Instagram Direct",
    "LinkedIn",
    "E-mail",
    "Stories",
    "Grupo de investidores",
]


PERFIS_TESTE = [
    "Investidor iniciante",
    "Investidor intermediário",
    "Investidor avançado",
    "Estudante",
    "Criador de conteúdo financeiro",
    "Amigo/conhecido para teste inicial",
]


def _safe_get_dict(key: str) -> Dict[str, Any]:
    valor = st.session_state.get(key)

    if isinstance(valor, dict):
        return valor

    return {}


def _fmt_texto(valor: Any, padrao: str = "N/D") -> str:
    if valor is None or valor == "":
        return padrao

    return str(valor)


def _safe_int(valor: Any, default: int = 0) -> int:
    try:
        return int(float(valor))
    except (TypeError, ValueError):
        return default


def _extrair_contexto_convite() -> Dict[str, Any]:
    marketing = _safe_get_dict("resultado_marketing")
    landing = _safe_get_dict("resultado_landing_page")
    lancamento = _safe_get_dict("resultado_lancamento_beta")
    ux = _safe_get_dict("resultado_auditoria_ux")
    negocio = _safe_get_dict("resultado_dashboard_negocio")

    return {
        "headline": landing.get(
            "headline",
            "Analise investimentos com método antes de tomar decisões.",
        ),
        "subheadline": landing.get(
            "subheadline",
            "Plataforma educacional para organizar valuation, preço-teto, tese, riscos, relatórios e watchlist.",
        ),
        "promessa": landing.get(
            "promessa",
            "Ajudar investidores a estruturar melhor o raciocínio antes de investir.",
        ),
        "dor_dominante": marketing.get(
            "dor_dominante",
            negocio.get("dor_mais_comum", "medo de pagar caro em ativos"),
        ),
        "perfil_dominante": marketing.get(
            "perfil_dominante",
            negocio.get("perfil_lista_mais_comum", "investidores iniciantes e intermediários"),
        ),
        "score_lancamento": lancamento.get("score_lancamento", 0),
        "score_ux": ux.get("score_ux", 0),
        "classificacao_ux": ux.get("classificacao", "N/D"),
        "score_tracao": negocio.get("score_tracao", 0),
        "total_feedbacks": negocio.get("total_feedbacks", 0),
        "total_lista": negocio.get("total_lista_espera", 0),
    }


def _gerar_fluxo_teste() -> List[Dict[str, str]]:
    return [
        {
            "Passo": "1",
            "Aba": "Produto",
            "O que fazer": "Leia a proposta central do app.",
            "Objetivo": "Entender o que a plataforma faz.",
            "Tempo": "1 minuto",
        },
        {
            "Passo": "2",
            "Aba": "Navegação",
            "O que fazer": "Veja a rota recomendada.",
            "Objetivo": "Não se perder entre as abas.",
            "Tempo": "1 minuto",
        },
        {
            "Passo": "3",
            "Aba": "Onboarding",
            "O que fazer": "Escolha seu perfil e objetivo.",
            "Objetivo": "Receber uma jornada personalizada.",
            "Tempo": "2 minutos",
        },
        {
            "Passo": "4",
            "Aba": "Valuation",
            "O que fazer": "Observe preço atual, preço justo e preço-teto.",
            "Objetivo": "Entender o motor principal.",
            "Tempo": "4 minutos",
        },
        {
            "Passo": "5",
            "Aba": "Tese & Convicção",
            "O que fazer": "Veja como tese, fundamentos e riscos entram na análise.",
            "Objetivo": "Perceber que não é só número.",
            "Tempo": "3 minutos",
        },
        {
            "Passo": "6",
            "Aba": "Relatórios",
            "O que fazer": "Baixe ou visualize um relatório.",
            "Objetivo": "Ver a entrega final.",
            "Tempo": "3 minutos",
        },
        {
            "Passo": "7",
            "Aba": "Feedback Beta",
            "O que fazer": "Preencha sua opinião sincera.",
            "Objetivo": "Ajudar a melhorar o produto.",
            "Tempo": "3 minutos",
        },
        {
            "Passo": "8",
            "Aba": "Oferta Beta",
            "O que fazer": "Entre na lista de espera, caso tenha interesse.",
            "Objetivo": "Medir valor percebido.",
            "Tempo": "2 minutos",
        },
    ]


def _gerar_perguntas_feedback() -> List[Dict[str, str]]:
    return [
        {
            "Pergunta": "Você entendeu o que o app faz?",
            "Por que importa": "Mede clareza da proposta.",
        },
        {
            "Pergunta": "Em qual parte você travou?",
            "Por que importa": "Revela problemas de UX.",
        },
        {
            "Pergunta": "Qual aba pareceu mais útil?",
            "Por que importa": "Mostra onde está o maior valor percebido.",
        },
        {
            "Pergunta": "Você usaria isso numa análise real?",
            "Por que importa": "Mede utilidade prática.",
        },
        {
            "Pergunta": "Você pagaria por uma versão melhorada?",
            "Por que importa": "Mede potencial de monetização.",
        },
        {
            "Pergunta": "O que está faltando para parecer mais profissional?",
            "Por que importa": "Ajuda no polimento antes da Fase 2.",
        },
    ]


def _gerar_checklist_envio_beta() -> List[Dict[str, str]]:
    return [
        {
            "Item": "Deixar o app em Modo Usuário Beta",
            "Status ideal": "Obrigatório",
            "Motivo": "Evita mostrar abas internas para usuários comuns.",
        },
        {
            "Item": "Testar se o app abre no Streamlit Cloud",
            "Status ideal": "Obrigatório",
            "Motivo": "O usuário não pode receber link quebrado.",
        },
        {
            "Item": "Enviar instruções claras",
            "Status ideal": "Obrigatório",
            "Motivo": "Reduz chance da pessoa se perder.",
        },
        {
            "Item": "Pedir feedback no final",
            "Status ideal": "Obrigatório",
            "Motivo": "Sem feedback, o teste não gera aprendizado.",
        },
        {
            "Item": "Enviar para poucas pessoas primeiro",
            "Status ideal": "Recomendado",
            "Motivo": "Beta bom começa controlado.",
        },
        {
            "Item": "Anotar perfil de quem testou",
            "Status ideal": "Recomendado",
            "Motivo": "Ajuda a descobrir qual público entende melhor.",
        },
        {
            "Item": "Não prometer resultado financeiro",
            "Status ideal": "Obrigatório",
            "Motivo": "Protege o produto e posiciona como ferramenta educacional.",
        },
        {
            "Item": "Fazer backup dos CSVs depois dos testes",
            "Status ideal": "Recomendado",
            "Motivo": "Evita perder feedbacks e lista de espera.",
        },
    ]


def _gerar_mensagem_whatsapp(
    nome_app: str,
    link_app: str,
    perfil_teste: str,
) -> str:
    link = link_app.strip() if link_app.strip() else "[COLE AQUI O LINK DO APP]"

    return f"""Estou testando uma plataforma educacional que estou construindo chamada {nome_app}.

A ideia é ajudar investidores a analisar ativos com mais método: valuation, preço-teto, margem de segurança, tese, riscos, checklist, relatório e watchlist.

Não é recomendação de compra ou venda. É uma ferramenta de estudo e organização.

Queria que você testasse como: {perfil_teste}.

Link:
{link}

Fluxo recomendado:
1. Produto
2. Navegação
3. Onboarding
4. Valuation
5. Tese & Convicção
6. Relatórios
7. Feedback Beta

No final, preenche a aba Feedback Beta com sua opinião sincera.

O que eu mais quero saber:
- Você entendeu a proposta?
- Onde travou?
- Qual parte achou mais útil?
- Usaria numa análise real?
- Pagaria por uma versão melhorada?
- O que precisa melhorar?"""


def _gerar_mensagem_instagram(link_app: str) -> str:
    link = link_app.strip() if link_app.strip() else "[LINK NA BIO / COLE O LINK AQUI]"

    return f"""Estou construindo uma plataforma educacional para investidores analisarem ativos com mais método.

Ela organiza:
• valuation
• preço-teto
• margem de segurança
• tese
• riscos
• checklist
• relatórios
• watchlist

Ainda está em beta.

Não é recomendação de investimento. É uma ferramenta para organizar raciocínio antes de tomar decisões.

Quem quiser testar e me dar feedback, o link está aqui:

{link}"""


def _gerar_mensagem_linkedin(link_app: str) -> str:
    link = link_app.strip() if link_app.strip() else "[COLE AQUI O LINK DO APP]"

    return f"""Estou desenvolvendo um MVP educacional chamado Máquina de Preço-Teto.

O objetivo é ajudar investidores a organizarem análises de ativos com mais método, combinando valuation, preço-teto, margem de segurança, tese qualitativa, riscos, checklist, relatórios e watchlist.

A ferramenta ainda está em fase beta e não tem finalidade de recomendação de investimento. O foco é educação financeira, organização de premissas e melhoria do processo decisório.

Estou buscando pessoas para testar a primeira versão e enviar feedback sobre clareza, utilidade, experiência e valor percebido.

Link do beta:
{link}"""


def _gerar_mensagem_email(nome_app: str, link_app: str) -> str:
    link = link_app.strip() if link_app.strip() else "[COLE AQUI O LINK DO APP]"

    return f"""Assunto: Convite para testar o beta da {nome_app}

Olá,

Estou construindo uma plataforma educacional chamada {nome_app}, criada para ajudar investidores a organizar análises de ativos com mais método.

A ferramenta reúne valuation, preço-teto, margem de segurança, tese, riscos, checklist, relatórios e watchlist em uma jornada guiada.

Importante: o app não recomenda compra, venda ou manutenção de ativos. Ele serve como ferramenta educacional para organizar raciocínio, premissas e análise.

Gostaria que você testasse a versão beta e me desse um feedback sincero.

Link:
{link}

Fluxo sugerido:
Produto → Navegação → Onboarding → Valuation → Relatórios → Feedback Beta

Depois do teste, preencha a aba Feedback Beta dentro do app.

Obrigado!"""


def _gerar_copy_pagina_publica(
    contexto: Dict[str, Any],
    nome_app: str,
    link_app: str,
) -> str:
    link = link_app.strip() if link_app.strip() else "[COLE AQUI O LINK DO APP]"

    return f"""# {nome_app}

## {contexto["headline"]}

{contexto["subheadline"]}

## Para quem é

Para investidores que querem analisar ativos com mais método, clareza e disciplina antes de tomar decisões.

## O problema

Muitos investidores compram ativos sem saber se o preço faz sentido, sem registrar premissas, sem revisar riscos e sem acompanhar a tese depois da compra.

## A solução

A {nome_app} organiza uma jornada educacional de análise com:

- Valuation
- Preço-teto
- Margem de segurança
- Tese qualitativa
- Riscos
- Checklist de erros
- Relatórios
- Watchlist
- Feedback beta

## Como testar

Use o app na seguinte ordem:

1. Produto
2. Navegação
3. Onboarding
4. Valuation
5. Tese & Convicção
6. Relatórios
7. Feedback Beta

## Link do beta

{link}

## Aviso educacional

A {nome_app} não recomenda compra, venda ou manutenção de ativos.  
A plataforma é educacional e serve para organizar raciocínio, premissas, riscos e acompanhamento.
"""


def _gerar_mensagem_lista_espera(nome_app: str) -> str:
    return f"""Entre na lista de espera da {nome_app}.

A plataforma está em fase beta e será construída com base no feedback dos primeiros usuários.

O objetivo é criar uma ferramenta educacional para analisar investimentos com mais método, clareza e disciplina.

Não é recomendação de investimento. É organização de análise."""


def _gerar_markdown_completo(
    contexto: Dict[str, Any],
    nome_app: str,
    link_app: str,
    perfil_teste: str,
) -> str:
    mensagem_whatsapp = _gerar_mensagem_whatsapp(nome_app, link_app, perfil_teste)
    mensagem_instagram = _gerar_mensagem_instagram(link_app)
    mensagem_linkedin = _gerar_mensagem_linkedin(link_app)
    mensagem_email = _gerar_mensagem_email(nome_app, link_app)
    pagina_publica = _gerar_copy_pagina_publica(contexto, nome_app, link_app)
    lista_espera = _gerar_mensagem_lista_espera(nome_app)

    fluxo_md = "\n".join(
        [
            f"{item['Passo']}. **{item['Aba']}** — {item['O que fazer']} ({item['Tempo']})"
            for item in _gerar_fluxo_teste()
        ]
    )

    perguntas_md = "\n".join(
        [
            f"- {item['Pergunta']}"
            for item in _gerar_perguntas_feedback()
        ]
    )

    checklist_md = "\n".join(
        [
            f"- **{item['Item']}** — {item['Status ideal']}: {item['Motivo']}"
            for item in _gerar_checklist_envio_beta()
        ]
    )

    return f"""# Kit de Convite Beta — {nome_app}

Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Contexto

- Headline: {contexto["headline"]}
- Dor dominante: {contexto["dor_dominante"]}
- Perfil dominante: {contexto["perfil_dominante"]}
- Score UX: {contexto["score_ux"]}
- Score lançamento: {contexto["score_lancamento"]}
- Score tração: {contexto["score_tracao"]}

## Mensagem para WhatsApp

{mensagem_whatsapp}

## Mensagem para Instagram

{mensagem_instagram}

## Mensagem para LinkedIn

{mensagem_linkedin}

## Mensagem para E-mail

{mensagem_email}

## Fluxo de teste recomendado

{fluxo_md}

## Perguntas principais de feedback

{perguntas_md}

## Mensagem de lista de espera

{lista_espera}

## Checklist antes de enviar

{checklist_md}

## Copy para página pública

{pagina_publica}
"""


def _classificar_prontidao_convite(contexto: Dict[str, Any]) -> str:
    score_ux = _safe_int(contexto.get("score_ux"))
    score_lancamento = _safe_int(contexto.get("score_lancamento"))
    score_tracao = _safe_int(contexto.get("score_tracao"))

    media = int(round((score_ux + score_lancamento + score_tracao) / 3))

    if media >= 75:
        return "Pronto para convite beta controlado"

    if media >= 55:
        return "Pode convidar poucas pessoas com acompanhamento próximo"

    if media >= 40:
        return "Convide apenas pessoas próximas e peça feedback guiado"

    return "Ainda cedo para divulgar; teste internamente primeiro"


def _gerar_acoes_recomendadas(contexto: Dict[str, Any]) -> List[str]:
    acoes = []

    score_ux = _safe_int(contexto.get("score_ux"))
    score_lancamento = _safe_int(contexto.get("score_lancamento"))
    total_feedbacks = _safe_int(contexto.get("total_feedbacks"))
    total_lista = _safe_int(contexto.get("total_lista"))

    if score_ux < 70:
        acoes.append("Revise a aba UX antes de enviar para muitas pessoas.")

    if score_lancamento < 60:
        acoes.append("Use a aba Lançamento para organizar pelo menos 5 tarefas do beta.")

    if total_feedbacks < 10:
        acoes.append("Convide primeiro 5 a 10 pessoas e peça feedback estruturado.")

    if total_lista < 10:
        acoes.append("Direcione interessados para a aba Oferta Beta após o teste.")

    acoes.append("Antes de enviar, selecione Modo Usuário Beta na sidebar.")
    acoes.append("Depois dos testes, faça backup dos dados na aba Dados.")

    return acoes


def _injetar_css_convite() -> None:
    st.markdown(
        """
        <style>
            .conv-hero {
                padding: 1.75rem 1.8rem;
                border-radius: 30px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    radial-gradient(circle at top left, rgba(214, 181, 109, 0.25), transparent 30%),
                    radial-gradient(circle at bottom right, rgba(74, 144, 226, 0.22), transparent 34%),
                    linear-gradient(135deg, rgba(8, 15, 27, 0.99), rgba(5, 9, 18, 0.99));
                box-shadow: 0 18px 55px rgba(0, 0, 0, 0.34);
                margin-bottom: 1.25rem;
            }

            .conv-eyebrow {
                color: #d6b56d;
                font-size: 0.78rem;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.35rem;
            }

            .conv-title {
                color: #f4f7fb;
                font-size: 2.1rem;
                font-weight: 900;
                margin-bottom: 0.45rem;
                line-height: 1.14;
            }

            .conv-subtitle {
                color: rgba(244, 247, 251, 0.76);
                font-size: 1rem;
                line-height: 1.62;
                max-width: 1080px;
            }

            .conv-card {
                padding: 1.1rem 1.15rem;
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.035);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.18);
                height: 100%;
            }

            .conv-card-label {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .conv-card-value {
                color: #f4f7fb;
                font-size: 1.22rem;
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .conv-card-note {
                color: rgba(244, 247, 251, 0.68);
                font-size: 0.87rem;
                line-height: 1.47;
            }

            .conv-highlight {
                padding: 0.95rem 1rem;
                border-radius: 16px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.92rem;
                line-height: 1.55;
                margin-bottom: 0.7rem;
            }

            .conv-copy {
                padding: 1rem 1.05rem;
                border-radius: 18px;
                background: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(255, 255, 255, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.92rem;
                line-height: 1.58;
                white-space: pre-wrap;
                margin-bottom: 0.85rem;
            }

            .conv-disclaimer {
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


def _card(label: str, value: str, note: str = "") -> None:
    st.markdown(
        f"""
        <div class="conv-card">
            <div class="conv-card-label">{label}</div>
            <div class="conv-card-value">{value}</div>
            <div class="conv-card-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _copy_box(texto: str) -> None:
    st.markdown(
        f"""
        <div class="conv-copy">{texto}</div>
        """,
        unsafe_allow_html=True,
    )


def renderizar_convite_beta_publico() -> None:
    """
    Renderiza a Central de Página Pública e Convite Beta.
    """
    _injetar_css_convite()

    contexto = _extrair_contexto_convite()
    classificacao = _classificar_prontidao_convite(contexto)
    acoes = _gerar_acoes_recomendadas(contexto)

    st.session_state["resultado_convite_beta_publico"] = {
        "classificacao": classificacao,
        "acoes": acoes,
        **contexto,
    }

    st.markdown(
        """
        <div class="conv-hero">
            <div class="conv-eyebrow">Ponte para usuários reais</div>
            <div class="conv-title">Página Pública e Convite Beta</div>
            <div class="conv-subtitle">
                Prepare mensagens, instruções e fluxo de teste para enviar a Máquina de Preço-Teto
                a usuários reais de forma clara, segura e profissional.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="conv-highlight">
            O convite beta precisa fazer três coisas: explicar o produto, orientar o teste e pedir feedback.
            Sem isso, a pessoa pode abrir o app, se perder e não gerar aprendizado.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Configuração do convite")

    col_config_1, col_config_2 = st.columns(2)

    with col_config_1:
        nome_app = st.text_input(
            "Nome do produto",
            value="Máquina de Preço-Teto",
            key="convite_nome_app",
        )

        link_app = st.text_input(
            "Link do app",
            value="https://maquina-preco-teto.streamlit.app/",
            key="convite_link_app",
        )

    with col_config_2:
        canal = st.selectbox(
            "Canal principal",
            CANAIS_CONVITE,
            key="convite_canal",
        )

        perfil_teste = st.selectbox(
            "Perfil de quem vai testar",
            PERFIS_TESTE,
            key="convite_perfil_teste",
        )

    st.divider()

    st.markdown("### Diagnóstico do convite")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        _card("Prontidão", classificacao, "Leitura combinando UX, lançamento e tração.")

    with col_2:
        _card("Score UX", f"{contexto['score_ux']}/100", _fmt_texto(contexto["classificacao_ux"]))

    with col_3:
        _card("Score lançamento", f"{contexto['score_lancamento']}/100", "Preparação do beta.")

    with col_4:
        _card("Score tração", f"{contexto['score_tracao']}/100", "Sinais de validação.")

    st.divider()

    st.markdown("### Ações antes de enviar")

    for acao in acoes:
        st.markdown(f"- {acao}")

    st.divider()

    st.markdown("### Mensagens prontas")

    mensagem_whatsapp = _gerar_mensagem_whatsapp(
        nome_app=nome_app,
        link_app=link_app,
        perfil_teste=perfil_teste,
    )

    mensagem_instagram = _gerar_mensagem_instagram(link_app)
    mensagem_linkedin = _gerar_mensagem_linkedin(link_app)
    mensagem_email = _gerar_mensagem_email(nome_app, link_app)
    mensagem_lista_espera = _gerar_mensagem_lista_espera(nome_app)

    if canal == "WhatsApp":
        st.markdown("#### Mensagem principal para WhatsApp")
        _copy_box(mensagem_whatsapp)
    elif canal == "Instagram Direct" or canal == "Stories":
        st.markdown("#### Mensagem principal para Instagram")
        _copy_box(mensagem_instagram)
    elif canal == "LinkedIn":
        st.markdown("#### Mensagem principal para LinkedIn")
        _copy_box(mensagem_linkedin)
    elif canal == "E-mail":
        st.markdown("#### Mensagem principal para E-mail")
        _copy_box(mensagem_email)
    else:
        st.markdown("#### Mensagem principal para grupo")
        _copy_box(mensagem_whatsapp)

    with st.expander("Ver todas as mensagens"):
        st.markdown("#### WhatsApp")
        _copy_box(mensagem_whatsapp)

        st.markdown("#### Instagram")
        _copy_box(mensagem_instagram)

        st.markdown("#### LinkedIn")
        _copy_box(mensagem_linkedin)

        st.markdown("#### E-mail")
        _copy_box(mensagem_email)

        st.markdown("#### Lista de espera")
        _copy_box(mensagem_lista_espera)

    st.divider()

    st.markdown("### Fluxo recomendado para o usuário")

    st.dataframe(
        _gerar_fluxo_teste(),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Perguntas que o usuário deve responder")

    st.dataframe(
        _gerar_perguntas_feedback(),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Checklist antes de enviar o beta")

    st.dataframe(
        _gerar_checklist_envio_beta(),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Copy para página pública simples")

    copy_pagina = _gerar_copy_pagina_publica(
        contexto=contexto,
        nome_app=nome_app,
        link_app=link_app,
    )

    _copy_box(copy_pagina)

    st.divider()

    st.markdown("### Baixar kit completo")

    markdown_completo = _gerar_markdown_completo(
        contexto=contexto,
        nome_app=nome_app,
        link_app=link_app,
        perfil_teste=perfil_teste,
    )

    st.download_button(
        label="Baixar kit de convite beta (.md)",
        data=markdown_completo,
        file_name="kit_convite_beta_maquina_preco_teto.md",
        mime="text/markdown",
        key="download_kit_convite_beta",
    )

    st.markdown(
        """
        <div class="conv-disclaimer">
            <strong>Nota estratégica:</strong> envie primeiro para poucas pessoas.
            O objetivo não é viralizar agora. O objetivo é descobrir se usuários reais entendem,
            usam, valorizam e dariam dinheiro por uma versão melhor.
        </div>
        """,
        unsafe_allow_html=True,
    )