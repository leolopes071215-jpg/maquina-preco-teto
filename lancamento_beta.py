# lancamento_beta.py

import csv
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v1.33 — Central de Lançamento Beta
# ------------------------------------------------------------
# Esta tela organiza o lançamento controlado do produto:
# - checklist de prontidão
# - plano de 14 dias
# - tarefas
# - status de execução
# - score de preparação
#
# Objetivo:
# transformar produto + marketing + landing page em execução real.
# ============================================================


CAMINHO_TAREFAS_LANCAMENTO = Path("tarefas_lancamento_beta.csv")


CAMPOS_TAREFAS = [
    "id",
    "data_criacao",
    "fase",
    "tarefa",
    "responsavel",
    "prazo",
    "prioridade",
    "status",
    "observacoes",
]


FASES = [
    "Pré-lançamento",
    "Convite Beta",
    "Conteúdo",
    "Landing Page",
    "Feedback",
    "Oferta",
    "Pós-lançamento",
]


PRIORIDADES = [
    "Alta",
    "Média",
    "Baixa",
]


STATUS_TAREFA = [
    "A fazer",
    "Em andamento",
    "Concluído",
    "Travado",
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


def _garantir_arquivo_tarefas() -> None:
    if CAMINHO_TAREFAS_LANCAMENTO.exists():
        return

    with open(CAMINHO_TAREFAS_LANCAMENTO, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_TAREFAS)
        escritor.writeheader()


def carregar_tarefas_lancamento() -> List[Dict[str, str]]:
    _garantir_arquivo_tarefas()

    with open(CAMINHO_TAREFAS_LANCAMENTO, "r", newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)

        tarefas = []

        for linha in leitor:
            tarefa = {campo: linha.get(campo, "") for campo in CAMPOS_TAREFAS}
            tarefas.append(tarefa)

        return tarefas


def salvar_tarefas_lancamento(tarefas: List[Dict[str, Any]]) -> None:
    with open(CAMINHO_TAREFAS_LANCAMENTO, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_TAREFAS)
        escritor.writeheader()

        for tarefa in tarefas:
            linha = {campo: tarefa.get(campo, "") for campo in CAMPOS_TAREFAS}
            escritor.writerow(linha)


def adicionar_tarefa_lancamento(
    fase: str,
    tarefa: str,
    responsavel: str,
    prazo: str,
    prioridade: str,
    status: str,
    observacoes: str,
) -> None:
    tarefas = carregar_tarefas_lancamento()

    nova_tarefa = {
        "id": str(uuid.uuid4())[:8],
        "data_criacao": datetime.now().isoformat(timespec="minutes"),
        "fase": fase,
        "tarefa": tarefa.strip(),
        "responsavel": responsavel.strip(),
        "prazo": prazo.strip(),
        "prioridade": prioridade,
        "status": status,
        "observacoes": observacoes.strip(),
    }

    tarefas.append(nova_tarefa)
    salvar_tarefas_lancamento(tarefas)


def limpar_tarefas_lancamento() -> None:
    salvar_tarefas_lancamento([])


def _contar(tarefas: List[Dict[str, str]], campo: str, valor: str) -> int:
    return len([
        tarefa for tarefa in tarefas
        if tarefa.get(campo) == valor
    ])


def _mais_frequente(tarefas: List[Dict[str, str]], campo: str) -> str:
    if len(tarefas) == 0:
        return "N/D"

    contagem = {}

    for tarefa in tarefas:
        valor = tarefa.get(campo, "")

        if valor == "":
            continue

        contagem[valor] = contagem.get(valor, 0) + 1

    if len(contagem) == 0:
        return "N/D"

    return max(contagem, key=contagem.get)


def _extrair_contexto_lancamento() -> Dict[str, Any]:
    negocio = _safe_get_dict("resultado_dashboard_negocio")
    marketing = _safe_get_dict("resultado_marketing")
    conteudo = _safe_get_dict("resultado_conteudo_marketing")
    landing = _safe_get_dict("resultado_landing_page")
    oferta = _safe_get_dict("resultado_oferta_beta")
    feedback = _safe_get_dict("resultado_feedback_beta")

    return {
        "score_tracao": negocio.get("score_tracao", 0),
        "classificacao_tracao": negocio.get("classificacao", "N/D"),
        "total_feedbacks": negocio.get("total_feedbacks", feedback.get("total", 0)),
        "total_lista": negocio.get("total_lista_espera", oferta.get("total", 0)),
        "pagaria_sim": negocio.get("lista_pagaria_sim", oferta.get("pagaria_sim", 0)),
        "perfil_dominante": marketing.get(
            "perfil_dominante",
            negocio.get("perfil_lista_mais_comum", "N/D"),
        ),
        "dor_dominante": marketing.get(
            "dor_dominante",
            negocio.get("dor_mais_comum", "N/D"),
        ),
        "modulo_campeao": marketing.get(
            "modulo_campeao",
            negocio.get("modulo_mais_util", "N/D"),
        ),
        "headline": landing.get("headline", "N/D"),
        "promessa": landing.get("promessa", "N/D"),
        "total_conteudos": conteudo.get("total_conteudos", 0),
        "conteudos_postados": conteudo.get("postados", 0),
    }


def _calcular_score_lancamento(contexto: Dict[str, Any], tarefas: List[Dict[str, str]]) -> int:
    total_feedbacks = _safe_int(contexto.get("total_feedbacks"))
    total_lista = _safe_int(contexto.get("total_lista"))
    pagaria_sim = _safe_int(contexto.get("pagaria_sim"))
    total_conteudos = _safe_int(contexto.get("total_conteudos"))
    conteudos_postados = _safe_int(contexto.get("conteudos_postados"))
    score_tracao = _safe_int(contexto.get("score_tracao"))

    total_tarefas = len(tarefas)
    tarefas_concluidas = _contar(tarefas, "status", "Concluído")

    pontos = 0.0

    pontos += min(score_tracao * 0.22, 22)
    pontos += min(total_feedbacks * 2.0, 16)
    pontos += min(total_lista * 2.5, 20)
    pontos += min(pagaria_sim * 4.0, 12)
    pontos += min(total_conteudos * 1.5, 12)
    pontos += min(conteudos_postados * 2.0, 8)

    if total_tarefas > 0:
        taxa_execucao = tarefas_concluidas / total_tarefas
        pontos += min(taxa_execucao * 10, 10)

    return int(round(max(0, min(100, pontos))))


def _classificar_lancamento(score: int) -> str:
    if score >= 80:
        return "Pronto para lançamento beta controlado"
    if score >= 65:
        return "Quase pronto para lançamento"
    if score >= 50:
        return "Preparação intermediária"
    if score >= 35:
        return "Ainda precisa estruturar"
    return "Muito cedo para lançar"


def _gerar_leitura_lancamento(score: int, classificacao: str) -> str:
    if classificacao == "Pronto para lançamento beta controlado":
        return (
            "O produto já possui sinais suficientes para um lançamento beta pequeno. "
            "A recomendação é chamar poucos usuários, acompanhar uso real, coletar feedbacks e evitar promessas comerciais fortes."
        )

    if classificacao == "Quase pronto para lançamento":
        return (
            "O produto está próximo de um lançamento beta. Antes de abrir mais usuários, finalize a landing page, "
            "organize convites, publique conteúdos e defina como o feedback será coletado."
        )

    if classificacao == "Preparação intermediária":
        return (
            "A base está sendo construída, mas ainda falta tração, lista de espera, conteúdo ou tarefas concluídas. "
            "O foco deve ser preparar o terreno antes de chamar mais pessoas."
        )

    if classificacao == "Ainda precisa estruturar":
        return (
            "Ainda há pontos importantes em aberto. Organize tarefas, gere conteúdos, valide a dor e aumente a lista de espera."
        )

    return (
        "Ainda é cedo para lançar. Primeiro colete feedbacks, crie conteúdos, fortaleça a landing page e registre interessados."
    )


def _gerar_checklist_prontidao(contexto: Dict[str, Any], tarefas: List[Dict[str, str]]) -> List[Dict[str, str]]:
    total_feedbacks = _safe_int(contexto.get("total_feedbacks"))
    total_lista = _safe_int(contexto.get("total_lista"))
    total_conteudos = _safe_int(contexto.get("total_conteudos"))
    conteudos_postados = _safe_int(contexto.get("conteudos_postados"))
    score_tracao = _safe_int(contexto.get("score_tracao"))
    headline = _fmt_texto(contexto.get("headline"))

    return [
        {
            "Critério": "Produto funcional",
            "Status": "OK",
            "Meta": "App abrindo e módulos principais funcionando.",
        },
        {
            "Critério": "Feedbacks reais",
            "Status": "OK" if total_feedbacks >= 10 else "Pendente",
            "Meta": "Pelo menos 10 feedbacks.",
        },
        {
            "Critério": "Lista de espera",
            "Status": "OK" if total_lista >= 10 else "Pendente",
            "Meta": "Pelo menos 10 interessados.",
        },
        {
            "Critério": "Conteúdo criado",
            "Status": "OK" if total_conteudos >= 7 else "Pendente",
            "Meta": "Pelo menos 7 conteúdos planejados.",
        },
        {
            "Critério": "Conteúdo publicado",
            "Status": "OK" if conteudos_postados >= 3 else "Pendente",
            "Meta": "Pelo menos 3 conteúdos publicados.",
        },
        {
            "Critério": "Landing page estruturada",
            "Status": "OK" if headline != "N/D" else "Pendente",
            "Meta": "Headline, promessa, benefícios e CTA definidos.",
        },
        {
            "Critério": "Tração mínima",
            "Status": "OK" if score_tracao >= 50 else "Pendente",
            "Meta": "Score de tração acima de 50.",
        },
        {
            "Critério": "Tarefas de lançamento",
            "Status": "OK" if len(tarefas) >= 5 else "Pendente",
            "Meta": "Pelo menos 5 tarefas registradas.",
        },
    ]


def _gerar_plano_14_dias() -> List[Dict[str, str]]:
    return [
        {
            "Dia": "Dia 1",
            "Foco": "Revisar produto",
            "Ação": "Testar todas as abas principais e corrigir erros visíveis.",
            "Métrica": "App funcionando sem erro crítico.",
        },
        {
            "Dia": "Dia 2",
            "Foco": "Landing page",
            "Ação": "Copiar a estrutura da aba Landing Page para Canva, Framer, Carrd ou Notion.",
            "Métrica": "Página externa rascunhada.",
        },
        {
            "Dia": "Dia 3",
            "Foco": "Conteúdo 1",
            "Ação": "Publicar post sobre o erro de pagar caro em uma boa empresa.",
            "Métrica": "Comentários, salvamentos ou directs.",
        },
        {
            "Dia": "Dia 4",
            "Foco": "Convites",
            "Ação": "Chamar 5 pessoas para testar o beta.",
            "Métrica": "5 convites enviados.",
        },
        {
            "Dia": "Dia 5",
            "Foco": "Feedback",
            "Ação": "Pedir que os usuários preencham a aba Feedback Beta.",
            "Métrica": "3 feedbacks registrados.",
        },
        {
            "Dia": "Dia 6",
            "Foco": "Conteúdo 2",
            "Ação": "Publicar carrossel sobre margem de segurança.",
            "Métrica": "Salvamentos.",
        },
        {
            "Dia": "Dia 7",
            "Foco": "Lista de espera",
            "Ação": "Direcionar interessados para a aba Oferta Beta.",
            "Métrica": "5 cadastros.",
        },
        {
            "Dia": "Dia 8",
            "Foco": "Demonstração",
            "Ação": "Mostrar a aba Relatórios ou Watchlist em vídeo curto.",
            "Métrica": "Cliques ou respostas.",
        },
        {
            "Dia": "Dia 9",
            "Foco": "Correções",
            "Ação": "Ajustar pontos confusos apontados nos feedbacks.",
            "Métrica": "Top 3 fricções corrigidas.",
        },
        {
            "Dia": "Dia 10",
            "Foco": "Convites 2",
            "Ação": "Chamar mais 5 pessoas para testar.",
            "Métrica": "10 convites acumulados.",
        },
        {
            "Dia": "Dia 11",
            "Foco": "Conteúdo 3",
            "Ação": "Publicar post sobre checklist antes de comprar uma ação.",
            "Métrica": "Salvamentos e comentários.",
        },
        {
            "Dia": "Dia 12",
            "Foco": "Oferta beta",
            "Ação": "Testar mensagem de pré-venda manual sem pagamento automático.",
            "Métrica": "Respostas de interesse.",
        },
        {
            "Dia": "Dia 13",
            "Foco": "Análise",
            "Ação": "Revisar Dashboard de Negócio e score de tração.",
            "Métrica": "Decisão: continuar beta, pré-venda ou ajustar.",
        },
        {
            "Dia": "Dia 14",
            "Foco": "Decisão",
            "Ação": "Definir próxima etapa: beta ampliado, landing externa ou pré-venda controlada.",
            "Métrica": "Plano da próxima versão definido.",
        },
    ]


def _gerar_proximas_acoes(score: int, contexto: Dict[str, Any], tarefas: List[Dict[str, str]]) -> List[str]:
    acoes = []

    total_feedbacks = _safe_int(contexto.get("total_feedbacks"))
    total_lista = _safe_int(contexto.get("total_lista"))
    total_conteudos = _safe_int(contexto.get("total_conteudos"))
    conteudos_postados = _safe_int(contexto.get("conteudos_postados"))

    if total_feedbacks < 10:
        acoes.append("Coletar mais feedbacks reais antes de abrir o beta para muitas pessoas.")

    if total_lista < 10:
        acoes.append("Aumentar a lista de espera usando conteúdo e convites diretos.")

    if total_conteudos < 7:
        acoes.append("Planejar pelo menos 7 conteúdos na aba Conteúdo.")

    if conteudos_postados < 3:
        acoes.append("Publicar pelo menos 3 conteúdos antes de fazer uma oferta mais direta.")

    if len(tarefas) < 5:
        acoes.append("Registrar pelo menos 5 tarefas de lançamento com prazo e prioridade.")

    if score >= 65:
        acoes.append("Preparar uma página externa simples e começar a chamar usuários beta com mais consistência.")

    if score >= 80:
        acoes.append("Testar uma pré-venda manual com poucos usuários e preço beta, sem automatizar pagamentos ainda.")

    if len(acoes) == 0:
        acoes.append("Manter o lançamento controlado, medir comportamento real e evitar escalar antes de validar retenção.")

    return acoes


def _preparar_tabela_tarefas(tarefas: List[Dict[str, str]]) -> List[Dict[str, str]]:
    tabela = []

    for tarefa in reversed(tarefas):
        tabela.append(
            {
                "Fase": tarefa.get("fase", ""),
                "Tarefa": tarefa.get("tarefa", ""),
                "Responsável": tarefa.get("responsavel", ""),
                "Prazo": tarefa.get("prazo", ""),
                "Prioridade": tarefa.get("prioridade", ""),
                "Status": tarefa.get("status", ""),
                "Observações": tarefa.get("observacoes", ""),
            }
        )

    return tabela


def _injetar_css_lancamento() -> None:
    st.markdown(
        """
        <style>
            .lan-hero {
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

            .lan-eyebrow {
                color: #d6b56d;
                font-size: 0.78rem;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.35rem;
            }

            .lan-title {
                color: #f4f7fb;
                font-size: 2.1rem;
                font-weight: 900;
                margin-bottom: 0.45rem;
                line-height: 1.14;
            }

            .lan-subtitle {
                color: rgba(244, 247, 251, 0.76);
                font-size: 1rem;
                line-height: 1.62;
                max-width: 1080px;
            }

            .lan-card {
                padding: 1.1rem 1.15rem;
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.035);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.18);
                height: 100%;
            }

            .lan-card-label {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .lan-card-value {
                color: #f4f7fb;
                font-size: 1.22rem;
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .lan-card-note {
                color: rgba(244, 247, 251, 0.68);
                font-size: 0.87rem;
                line-height: 1.47;
            }

            .lan-highlight {
                padding: 0.95rem 1rem;
                border-radius: 16px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.92rem;
                line-height: 1.55;
                margin-bottom: 0.7rem;
            }

            .lan-disclaimer {
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
        <div class="lan-card">
            <div class="lan-card-label">{label}</div>
            <div class="lan-card-value">{value}</div>
            <div class="lan-card-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def renderizar_lancamento_beta() -> None:
    """
    Renderiza a Central de Lançamento Beta.
    """
    _injetar_css_lancamento()

    contexto = _extrair_contexto_lancamento()
    tarefas = carregar_tarefas_lancamento()

    score_lancamento = _calcular_score_lancamento(
        contexto=contexto,
        tarefas=tarefas,
    )

    classificacao = _classificar_lancamento(score_lancamento)
    leitura = _gerar_leitura_lancamento(score_lancamento, classificacao)
    checklist = _gerar_checklist_prontidao(contexto, tarefas)
    plano_14_dias = _gerar_plano_14_dias()
    proximas_acoes = _gerar_proximas_acoes(score_lancamento, contexto, tarefas)

    total_tarefas = len(tarefas)
    tarefas_concluidas = _contar(tarefas, "status", "Concluído")
    tarefas_travadas = _contar(tarefas, "status", "Travado")
    fase_mais_comum = _mais_frequente(tarefas, "fase")

    st.session_state["resultado_lancamento_beta"] = {
        "score_lancamento": score_lancamento,
        "classificacao": classificacao,
        "leitura": leitura,
        "total_tarefas": total_tarefas,
        "tarefas_concluidas": tarefas_concluidas,
        "tarefas_travadas": tarefas_travadas,
        "fase_mais_comum": fase_mais_comum,
        **contexto,
    }

    st.markdown(
        """
        <div class="lan-hero">
            <div class="lan-eyebrow">Execução controlada</div>
            <div class="lan-title">Central de Lançamento Beta</div>
            <div class="lan-subtitle">
                Organize a transição entre produto construído e usuários reais.
                Esta central acompanha prontidão, tarefas, plano de 14 dias e próximas ações
                para lançar sem exagerar promessa, sem escalar cedo demais e sem perder controle.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="lan-highlight">
            Lançamento beta não é lançamento agressivo. É teste controlado com usuários reais,
            coleta de feedback, ajustes rápidos e validação de intenção de pagamento.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Score de preparação para lançamento")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Score de lançamento", f"{score_lancamento}/100")

    with col_2:
        st.metric("Classificação", classificacao)

    with col_3:
        st.metric("Feedbacks", contexto["total_feedbacks"])

    with col_4:
        st.metric("Lista de espera", contexto["total_lista"])

    st.progress(score_lancamento / 100)

    if score_lancamento >= 65:
        st.success(leitura)
    elif score_lancamento >= 50:
        st.warning(leitura)
    else:
        st.error(leitura)

    st.divider()

    st.markdown("### Indicadores do lançamento")

    col_a, col_b, col_c, col_d = st.columns(4)

    with col_a:
        _card(
            "Tarefas",
            str(total_tarefas),
            "Total de tarefas registradas.",
        )

    with col_b:
        _card(
            "Concluídas",
            str(tarefas_concluidas),
            "Execução real do plano.",
        )

    with col_c:
        _card(
            "Travadas",
            str(tarefas_travadas),
            "Pontos que exigem atenção.",
        )

    with col_d:
        _card(
            "Fase dominante",
            fase_mais_comum,
            "Onde está concentrado o trabalho.",
        )

    col_e, col_f, col_g = st.columns(3)

    with col_e:
        _card(
            "Dor dominante",
            _fmt_texto(contexto["dor_dominante"]),
            "Base da comunicação.",
        )

    with col_f:
        _card(
            "Módulo campeão",
            _fmt_texto(contexto["modulo_campeao"]),
            "Tela que deve aparecer nos conteúdos.",
        )

    with col_g:
        _card(
            "Pagaria agora",
            str(contexto["pagaria_sim"]),
            "Sinal inicial de monetização.",
        )

    st.divider()

    st.markdown("### Checklist de prontidão")

    st.dataframe(
        checklist,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Plano de 14 dias")

    st.dataframe(
        plano_14_dias,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Próximas ações recomendadas")

    for acao in proximas_acoes:
        st.markdown(f"- {acao}")

    st.divider()

    st.markdown("### Registrar tarefa de lançamento")

    with st.form("form_tarefa_lancamento"):
        col_form_1, col_form_2 = st.columns(2)

        with col_form_1:
            fase = st.selectbox(
                "Fase",
                FASES,
                key="lancamento_fase",
            )

            tarefa = st.text_area(
                "Tarefa",
                value="",
                height=95,
                placeholder="Ex: Publicar vídeo sobre preço-teto no TikTok",
                key="lancamento_tarefa",
            )

            responsavel = st.text_input(
                "Responsável",
                value="Leo",
                key="lancamento_responsavel",
            )

        with col_form_2:
            prazo = st.text_input(
                "Prazo",
                value=datetime.now().strftime("%d/%m/%Y"),
                key="lancamento_prazo",
            )

            prioridade = st.selectbox(
                "Prioridade",
                PRIORIDADES,
                key="lancamento_prioridade",
            )

            status = st.selectbox(
                "Status",
                STATUS_TAREFA,
                key="lancamento_status",
            )

        observacoes = st.text_area(
            "Observações",
            value="",
            height=80,
            key="lancamento_observacoes",
        )

        enviar = st.form_submit_button("Salvar tarefa")

        if enviar:
            if tarefa.strip() == "":
                st.error("Preencha a tarefa antes de salvar.")
            else:
                adicionar_tarefa_lancamento(
                    fase=fase,
                    tarefa=tarefa,
                    responsavel=responsavel,
                    prazo=prazo,
                    prioridade=prioridade,
                    status=status,
                    observacoes=observacoes,
                )

                st.success("Tarefa salva com sucesso.")
                st.rerun()

    st.divider()

    st.markdown("### Tarefas registradas")

    tarefas = carregar_tarefas_lancamento()

    if len(tarefas) == 0:
        st.info("Nenhuma tarefa de lançamento registrada ainda.")
    else:
        tabela = _preparar_tabela_tarefas(tarefas)

        st.dataframe(
            tabela,
            use_container_width=True,
            hide_index=True,
        )

        st.divider()

        col_down, col_clean = st.columns(2)

        with col_down:
            with open(CAMINHO_TAREFAS_LANCAMENTO, "rb") as arquivo:
                st.download_button(
                    label="Baixar tarefas em CSV",
                    data=arquivo,
                    file_name="tarefas_lancamento_beta.csv",
                    mime="text/csv",
                    key="lancamento_download_csv",
                )

        with col_clean:
            confirmar = st.checkbox(
                "Confirmar limpeza das tarefas",
                value=False,
                key="lancamento_confirmar_limpeza",
            )

            if st.button("Limpar tarefas", key="lancamento_limpar_tarefas"):
                if confirmar:
                    limpar_tarefas_lancamento()
                    st.success("Tarefas limpas com sucesso.")
                    st.rerun()
                else:
                    st.warning("Marque a confirmação antes de limpar as tarefas.")

    st.divider()

    st.markdown("### Regra do lançamento beta")

    st.markdown(
        """
        - Não abrir para todo mundo de uma vez.
        - Não prometer rentabilidade.
        - Não vender como recomendação de investimento.
        - Chamar poucos usuários por vez.
        - Observar onde travam.
        - Coletar feedback estruturado.
        - Ajustar o produto antes de escalar.
        - Só pensar em pagamento automático depois de validar intenção real.
        """
    )

    st.markdown(
        """
        <div class="lan-disclaimer">
            <strong>Nota estratégica:</strong> lançamento beta é uma fase de aprendizado.
            O objetivo não é maximizar vendas imediatamente. O objetivo é descobrir se o produto
            entrega valor, se o usuário entende, se ele volta a usar e se existe intenção real de pagamento.
        </div>
        """,
        unsafe_allow_html=True,
    )