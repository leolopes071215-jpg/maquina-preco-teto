# priorizacao_feedback.py

import csv
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v2.3 — Priorização de Feedback e Roadmap Beta
# ------------------------------------------------------------
# Esta tela transforma feedback real em decisões de produto.
#
# Objetivo:
# - registrar melhorias sugeridas por usuários
# - priorizar melhorias por impacto, frequência, confiança,
#   urgência e esforço
# - criar um mini-roadmap orientado por feedback real
# - evitar construir por achismo
# ============================================================


CAMINHO_PRIORIZACAO_FEEDBACK = Path("priorizacao_feedback_beta.csv")


CAMPOS_PRIORIZACAO = [
    "id",
    "data_registro",
    "titulo_melhoria",
    "origem_feedback",
    "area_produto",
    "perfil_impactado",
    "tipo_melhoria",
    "descricao",
    "problema_observado",
    "evidencia_feedback",
    "impacto_usuario",
    "frequencia_feedback",
    "confianca_feedback",
    "urgencia_estrategica",
    "esforco_desenvolvimento",
    "score_prioridade",
    "classificacao",
    "status",
    "proxima_acao",
    "observacoes",
]


ORIGENS_FEEDBACK = [
    "Aprendizado Beta",
    "Rodadas Beta",
    "Feedback Beta",
    "Entrevista direta",
    "Observação de uso",
    "Lista de espera",
    "Ideia interna validada",
    "Outro",
]


AREAS_PRODUTO = [
    "Produto",
    "Navegação",
    "Onboarding",
    "Valuation",
    "Tese & Convicção",
    "Checklist",
    "Relatórios",
    "Feedback Beta",
    "Oferta Beta",
    "Watchlist",
    "Visual/UX",
    "Dados/Backups",
    "Landing Page",
    "Convite Beta",
    "Outro",
]


PERFIS_IMPACTADOS = [
    "Investidor iniciante",
    "Investidor intermediário",
    "Investidor avançado",
    "Estudante",
    "Criador de conteúdo financeiro",
    "Todos os usuários",
    "Fundador/gestor do produto",
    "Outro",
]


TIPOS_MELHORIA = [
    "Clareza",
    "Usabilidade",
    "Visual",
    "Funcionalidade",
    "Relatório",
    "Valuation",
    "Conversão",
    "Confiança",
    "Performance",
    "Dados",
    "Marketing",
    "Outro",
]


STATUS_MELHORIA = [
    "Backlog",
    "Priorizar agora",
    "Em análise",
    "Em desenvolvimento",
    "Testando",
    "Concluída",
    "Adiada",
    "Descartada",
]


PROXIMAS_ACOES = [
    "Coletar mais evidência",
    "Transformar em tarefa técnica",
    "Corrigir na próxima versão",
    "Testar com mais usuários",
    "Criar protótipo simples",
    "Medir impacto antes",
    "Descartar por enquanto",
    "Aguardar padrão se repetir",
]


def _garantir_arquivo_priorizacao() -> None:
    if CAMINHO_PRIORIZACAO_FEEDBACK.exists():
        return

    with open(CAMINHO_PRIORIZACAO_FEEDBACK, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_PRIORIZACAO)
        escritor.writeheader()


def carregar_priorizacoes_feedback() -> List[Dict[str, str]]:
    _garantir_arquivo_priorizacao()

    with open(CAMINHO_PRIORIZACAO_FEEDBACK, "r", newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        registros = []

        for linha in leitor:
            registro = {campo: linha.get(campo, "") for campo in CAMPOS_PRIORIZACAO}
            registros.append(registro)

        return registros


def salvar_priorizacoes_feedback(registros: List[Dict[str, Any]]) -> None:
    with open(CAMINHO_PRIORIZACAO_FEEDBACK, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_PRIORIZACAO)
        escritor.writeheader()

        for registro in registros:
            linha = {campo: registro.get(campo, "") for campo in CAMPOS_PRIORIZACAO}
            escritor.writerow(linha)


def _safe_int(valor: Any, default: int = 0) -> int:
    try:
        return int(float(valor))
    except (TypeError, ValueError):
        return default


def _safe_float(valor: Any, default: float = 0.0) -> float:
    try:
        return float(valor)
    except (TypeError, ValueError):
        return default


def calcular_score_prioridade(
    impacto_usuario: int,
    frequencia_feedback: int,
    confianca_feedback: int,
    urgencia_estrategica: int,
    esforco_desenvolvimento: int,
) -> int:
    """
    Fórmula simples de priorização.

    Quanto maior impacto, frequência, confiança e urgência, maior a prioridade.
    Quanto maior esforço, menor a prioridade.
    """
    esforco = max(1, esforco_desenvolvimento)

    score_bruto = (
        impacto_usuario * 3.0
        + frequencia_feedback * 2.5
        + confianca_feedback * 2.0
        + urgencia_estrategica * 1.5
    ) / esforco

    score_normalizado = score_bruto * 10

    return int(round(max(0, min(100, score_normalizado))))


def classificar_prioridade(score: int) -> str:
    if score >= 85:
        return "Prioridade crítica"
    if score >= 70:
        return "Alta prioridade"
    if score >= 50:
        return "Prioridade média"
    if score >= 30:
        return "Baixa prioridade"
    return "Não priorizar agora"


def adicionar_priorizacao_feedback(
    titulo_melhoria: str,
    origem_feedback: str,
    area_produto: str,
    perfil_impactado: str,
    tipo_melhoria: str,
    descricao: str,
    problema_observado: str,
    evidencia_feedback: str,
    impacto_usuario: int,
    frequencia_feedback: int,
    confianca_feedback: int,
    urgencia_estrategica: int,
    esforco_desenvolvimento: int,
    status: str,
    proxima_acao: str,
    observacoes: str,
) -> None:
    registros = carregar_priorizacoes_feedback()

    score = calcular_score_prioridade(
        impacto_usuario=impacto_usuario,
        frequencia_feedback=frequencia_feedback,
        confianca_feedback=confianca_feedback,
        urgencia_estrategica=urgencia_estrategica,
        esforco_desenvolvimento=esforco_desenvolvimento,
    )

    novo_registro = {
        "id": str(uuid.uuid4())[:8],
        "data_registro": datetime.now().isoformat(timespec="minutes"),
        "titulo_melhoria": titulo_melhoria.strip(),
        "origem_feedback": origem_feedback,
        "area_produto": area_produto,
        "perfil_impactado": perfil_impactado,
        "tipo_melhoria": tipo_melhoria,
        "descricao": descricao.strip(),
        "problema_observado": problema_observado.strip(),
        "evidencia_feedback": evidencia_feedback.strip(),
        "impacto_usuario": str(impacto_usuario),
        "frequencia_feedback": str(frequencia_feedback),
        "confianca_feedback": str(confianca_feedback),
        "urgencia_estrategica": str(urgencia_estrategica),
        "esforco_desenvolvimento": str(esforco_desenvolvimento),
        "score_prioridade": str(score),
        "classificacao": classificar_prioridade(score),
        "status": status,
        "proxima_acao": proxima_acao,
        "observacoes": observacoes.strip(),
    }

    registros.append(novo_registro)
    salvar_priorizacoes_feedback(registros)


def limpar_priorizacoes_feedback() -> None:
    salvar_priorizacoes_feedback([])


def _fmt_percentual(valor: float) -> str:
    return f"{valor:.1f}%"


def _media_score(registros: List[Dict[str, str]]) -> float:
    scores = []

    for registro in registros:
        score = _safe_float(registro.get("score_prioridade"))

        if score > 0:
            scores.append(score)

    if len(scores) == 0:
        return 0.0

    return sum(scores) / len(scores)


def _contar_por_campo(registros: List[Dict[str, str]], campo: str, valor: str) -> int:
    return len([registro for registro in registros if registro.get(campo) == valor])


def _mais_frequente(registros: List[Dict[str, str]], campo: str) -> str:
    contagem: Dict[str, int] = {}

    for registro in registros:
        valor = registro.get(campo, "").strip()

        if valor == "":
            continue

        contagem[valor] = contagem.get(valor, 0) + 1

    if len(contagem) == 0:
        return "N/D"

    return max(contagem, key=contagem.get)


def _ordenar_por_prioridade(registros: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return sorted(
        registros,
        key=lambda registro: _safe_int(registro.get("score_prioridade")),
        reverse=True,
    )


def _gerar_tabela_prioridades(registros: List[Dict[str, str]]) -> List[Dict[str, str]]:
    tabela = []

    for registro in _ordenar_por_prioridade(registros):
        tabela.append(
            {
                "Score": registro.get("score_prioridade", ""),
                "Classificação": registro.get("classificacao", ""),
                "Melhoria": registro.get("titulo_melhoria", ""),
                "Área": registro.get("area_produto", ""),
                "Tipo": registro.get("tipo_melhoria", ""),
                "Perfil impactado": registro.get("perfil_impactado", ""),
                "Status": registro.get("status", ""),
                "Próxima ação": registro.get("proxima_acao", ""),
                "Esforço": registro.get("esforco_desenvolvimento", ""),
                "Origem": registro.get("origem_feedback", ""),
            }
        )

    return tabela


def _gerar_tabela_detalhada(registros: List[Dict[str, str]]) -> List[Dict[str, str]]:
    tabela = []

    for registro in _ordenar_por_prioridade(registros):
        tabela.append(
            {
                "Melhoria": registro.get("titulo_melhoria", ""),
                "Problema": registro.get("problema_observado", ""),
                "Evidência": registro.get("evidencia_feedback", ""),
                "Impacto": registro.get("impacto_usuario", ""),
                "Frequência": registro.get("frequencia_feedback", ""),
                "Confiança": registro.get("confianca_feedback", ""),
                "Urgência": registro.get("urgencia_estrategica", ""),
                "Esforço": registro.get("esforco_desenvolvimento", ""),
                "Observações": registro.get("observacoes", ""),
            }
        )

    return tabela


def _gerar_roadmap_sugerido(registros: List[Dict[str, str]]) -> List[Dict[str, str]]:
    prioridades = _ordenar_por_prioridade(registros)

    roadmap = []

    for indice, registro in enumerate(prioridades[:10], start=1):
        score = _safe_int(registro.get("score_prioridade"))

        if score >= 70:
            horizonte = "Próxima versão"
        elif score >= 50:
            horizonte = "Próximas 2-3 versões"
        elif score >= 30:
            horizonte = "Backlog monitorado"
        else:
            horizonte = "Não priorizar agora"

        roadmap.append(
            {
                "Ordem": str(indice),
                "Horizonte": horizonte,
                "Melhoria": registro.get("titulo_melhoria", ""),
                "Área": registro.get("area_produto", ""),
                "Score": registro.get("score_prioridade", ""),
                "Ação recomendada": registro.get("proxima_acao", ""),
            }
        )

    return roadmap


def _gerar_insights_priorizacao(registros: List[Dict[str, str]]) -> List[str]:
    if len(registros) == 0:
        return [
            "Ainda não há melhorias priorizadas. Registre sugestões vindas dos primeiros testes reais.",
            "Não transforme opinião isolada em tarefa. Priorize feedback repetido ou muito crítico.",
            "Toda melhoria precisa ter problema, evidência e impacto claro.",
        ]

    insights = []

    total = len(registros)
    media_score = _media_score(registros)
    area_mais_citada = _mais_frequente(registros, "area_produto")
    tipo_mais_citado = _mais_frequente(registros, "tipo_melhoria")
    criticas = len([r for r in registros if _safe_int(r.get("score_prioridade")) >= 85])
    altas = len([r for r in registros if 70 <= _safe_int(r.get("score_prioridade")) < 85])
    em_desenvolvimento = _contar_por_campo(registros, "status", "Em desenvolvimento")

    insights.append(f"Existem {total} melhoria(s) registradas no backlog beta.")
    insights.append(f"Score médio das melhorias: {media_score:.1f}/100.")

    if area_mais_citada != "N/D":
        insights.append(f"A área mais citada nas melhorias é: {area_mais_citada}.")

    if tipo_mais_citado != "N/D":
        insights.append(f"O tipo de melhoria mais recorrente é: {tipo_mais_citado}.")

    if criticas > 0:
        insights.append(f"Existem {criticas} melhoria(s) críticas. Elas devem ser analisadas antes de novas funções.")

    if altas > 0:
        insights.append(f"Existem {altas} melhoria(s) de alta prioridade candidatas para as próximas versões.")

    if em_desenvolvimento > 3:
        insights.append("Há muitas melhorias em desenvolvimento ao mesmo tempo. Reduza foco e finalize primeiro.")

    if media_score < 45:
        insights.append("O backlog ainda parece pouco urgente. Colete mais evidências antes de construir.")

    insights.append("Na Fase 2, o roadmap deve nascer de padrões de feedback, não de ansiedade por adicionar funções.")

    return insights


def _gerar_decisoes_recomendadas(registros: List[Dict[str, str]]) -> List[Dict[str, str]]:
    if len(registros) == 0:
        return [
            {
                "Decisão": "Registrar primeiras melhorias",
                "Critério": "Nenhuma melhoria priorizada ainda.",
                "Ação": "Extrair melhorias dos testes reais e das rodadas beta.",
                "Prioridade": "Muito alta",
            }
        ]

    decisoes = []

    prioridades = _ordenar_por_prioridade(registros)
    top = prioridades[0]
    top_score = _safe_int(top.get("score_prioridade"))

    if top_score >= 85:
        decisoes.append(
            {
                "Decisão": "Atacar melhoria crítica",
                "Critério": f"Maior score atual: {top_score}/100.",
                "Ação": f"Transformar '{top.get('titulo_melhoria')}' em tarefa técnica.",
                "Prioridade": "Muito alta",
            }
        )

    if top_score >= 70:
        decisoes.append(
            {
                "Decisão": "Planejar próxima versão orientada por feedback",
                "Critério": "Existe melhoria de alta prioridade.",
                "Ação": "Criar uma versão pequena focada em 1 a 3 melhorias prioritárias.",
                "Prioridade": "Alta",
            }
        )

    melhorias_clareza = len([r for r in registros if r.get("tipo_melhoria") == "Clareza"])

    if melhorias_clareza >= 2:
        decisoes.append(
            {
                "Decisão": "Revisar comunicação e onboarding",
                "Critério": "Múltiplos feedbacks de clareza.",
                "Ação": "Melhorar Produto, Navegação e Onboarding antes de funcionalidades novas.",
                "Prioridade": "Alta",
            }
        )

    melhorias_usabilidade = len([r for r in registros if r.get("tipo_melhoria") == "Usabilidade"])

    if melhorias_usabilidade >= 2:
        decisoes.append(
            {
                "Decisão": "Reduzir fricção de uso",
                "Critério": "Múltiplos feedbacks de usabilidade.",
                "Ação": "Simplificar fluxo, botões, textos e ordem das abas.",
                "Prioridade": "Alta",
            }
        )

    if len(decisoes) == 0:
        decisoes.append(
            {
                "Decisão": "Continuar coletando evidência",
                "Critério": "Prioridades ainda não são fortes o bastante.",
                "Ação": "Rodar mais entrevistas e registrar mais feedbacks.",
                "Prioridade": "Média",
            }
        )

    return decisoes


def _gerar_checklist_priorizacao() -> List[Dict[str, str]]:
    return [
        {
            "Regra": "Toda melhoria deve ter evidência",
            "Motivo": "Evita construir por achismo.",
        },
        {
            "Regra": "Feedback repetido pesa mais",
            "Motivo": "Padrões importam mais que opinião isolada.",
        },
        {
            "Regra": "Impacto alto + esforço baixo deve subir no ranking",
            "Motivo": "Gera evolução rápida do produto.",
        },
        {
            "Regra": "Não trabalhar em muitas melhorias ao mesmo tempo",
            "Motivo": "Foco aumenta chance de terminar e medir resultado.",
        },
        {
            "Regra": "Melhorias de clareza vêm antes de funções avançadas",
            "Motivo": "Se o usuário não entende, ele não valoriza.",
        },
        {
            "Regra": "Cada melhoria concluída deve ser testada novamente",
            "Motivo": "Só usuário real confirma se melhorou.",
        },
    ]


def _gerar_markdown_priorizacao(registros: List[Dict[str, str]]) -> str:
    insights = _gerar_insights_priorizacao(registros)
    decisoes = _gerar_decisoes_recomendadas(registros)
    roadmap = _gerar_roadmap_sugerido(registros)

    linhas_insights = "\n".join([f"- {insight}" for insight in insights])

    linhas_decisoes = "\n".join(
        [
            f"| {item['Decisão']} | {item['Critério']} | {item['Ação']} | {item['Prioridade']} |"
            for item in decisoes
        ]
    )

    linhas_roadmap = "\n".join(
        [
            f"| {item['Ordem']} | {item['Horizonte']} | {item['Melhoria']} | {item['Área']} | {item['Score']} | {item['Ação recomendada']} |"
            for item in roadmap
        ]
    )

    return f"""# Priorização de Feedback — Máquina de Preço-Teto

Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Resumo

Total de melhorias registradas: {len(registros)}  
Score médio: {_media_score(registros):.1f}/100  
Área mais citada: {_mais_frequente(registros, "area_produto")}  
Tipo mais citado: {_mais_frequente(registros, "tipo_melhoria")}

## Insights automáticos

{linhas_insights}

## Decisões recomendadas

| Decisão | Critério | Ação | Prioridade |
|---|---|---|---|
{linhas_decisoes}

## Roadmap sugerido

| Ordem | Horizonte | Melhoria | Área | Score | Ação recomendada |
|---:|---|---|---|---:|---|
{linhas_roadmap}

## Regra central

Não adicionar grandes funcionalidades sem evidência real e prioridade clara.
"""


def _injetar_css_priorizacao() -> None:
    st.markdown(
        """
        <style>
            .prio-hero {
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

            .prio-eyebrow {
                color: #d6b56d;
                font-size: 0.78rem;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.35rem;
            }

            .prio-title {
                color: #f4f7fb;
                font-size: 2.1rem;
                font-weight: 900;
                margin-bottom: 0.45rem;
                line-height: 1.14;
            }

            .prio-subtitle {
                color: rgba(244, 247, 251, 0.76);
                font-size: 1rem;
                line-height: 1.62;
                max-width: 1080px;
            }

            .prio-card {
                padding: 1.1rem 1.15rem;
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.035);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.18);
                height: 100%;
            }

            .prio-card-label {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .prio-card-value {
                color: #f4f7fb;
                font-size: 1.22rem;
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .prio-card-note {
                color: rgba(244, 247, 251, 0.68);
                font-size: 0.87rem;
                line-height: 1.47;
            }

            .prio-highlight {
                padding: 0.95rem 1rem;
                border-radius: 16px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.92rem;
                line-height: 1.55;
                margin-bottom: 0.7rem;
            }

            .prio-disclaimer {
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
        <div class="prio-card">
            <div class="prio-card-label">{label}</div>
            <div class="prio-card-value">{value}</div>
            <div class="prio-card-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def renderizar_priorizacao_feedback_beta() -> None:
    """
    Renderiza a central de priorização de feedback e roadmap beta.
    """
    _injetar_css_priorizacao()

    registros = carregar_priorizacoes_feedback()

    total = len(registros)
    media_score = _media_score(registros)
    area_mais_citada = _mais_frequente(registros, "area_produto")
    tipo_mais_citado = _mais_frequente(registros, "tipo_melhoria")
    criticas = len([r for r in registros if _safe_int(r.get("score_prioridade")) >= 85])

    st.session_state["resultado_priorizacao_feedback"] = {
        "total_melhorias": total,
        "media_score": media_score,
        "area_mais_citada": area_mais_citada,
        "tipo_mais_citado": tipo_mais_citado,
        "melhorias_criticas": criticas,
    }

    st.markdown(
        """
        <div class="prio-hero">
            <div class="prio-eyebrow">Fase 2.3 — Roadmap guiado por usuários</div>
            <div class="prio-title">Priorização de Feedback e Roadmap Beta</div>
            <div class="prio-subtitle">
                Transforme feedback real em prioridades claras. Decida o que construir primeiro
                com base em impacto, frequência, confiança, urgência e esforço.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="prio-highlight">
            A regra agora é simples: se não há evidência real, não entra no topo do roadmap.
            Produto bom nasce de padrões de uso, não de ansiedade por adicionar funções.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Diagnóstico do backlog beta")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Melhorias registradas", total)

    with col_2:
        st.metric("Score médio", f"{media_score:.1f}/100")

    with col_3:
        st.metric("Melhorias críticas", criticas)

    with col_4:
        st.metric("Área mais citada", area_mais_citada)

    st.divider()

    st.markdown("### Insights automáticos")

    for insight in _gerar_insights_priorizacao(registros):
        st.markdown(f"- {insight}")

    st.divider()

    st.markdown("### Decisões recomendadas")

    st.dataframe(
        _gerar_decisoes_recomendadas(registros),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Registrar melhoria priorizada")

    with st.form("form_priorizacao_feedback"):
        col_form_1, col_form_2 = st.columns(2)

        with col_form_1:
            titulo_melhoria = st.text_input(
                "Título da melhoria",
                value="",
                placeholder="Ex: Simplificar a primeira tela para usuário beta",
                key="prio_titulo",
            )

            origem_feedback = st.selectbox(
                "Origem do feedback",
                ORIGENS_FEEDBACK,
                key="prio_origem",
            )

            area_produto = st.selectbox(
                "Área do produto",
                AREAS_PRODUTO,
                key="prio_area",
            )

            perfil_impactado = st.selectbox(
                "Perfil mais impactado",
                PERFIS_IMPACTADOS,
                key="prio_perfil",
            )

            tipo_melhoria = st.selectbox(
                "Tipo de melhoria",
                TIPOS_MELHORIA,
                key="prio_tipo",
            )

        with col_form_2:
            status = st.selectbox(
                "Status",
                STATUS_MELHORIA,
                key="prio_status",
            )

            proxima_acao = st.selectbox(
                "Próxima ação",
                PROXIMAS_ACOES,
                key="prio_proxima_acao",
            )

            impacto_usuario = st.slider(
                "Impacto no usuário",
                1,
                10,
                7,
                help="Quanto essa melhoria muda a experiência ou o valor percebido?",
                key="prio_impacto",
            )

            frequencia_feedback = st.slider(
                "Frequência do feedback",
                1,
                10,
                5,
                help="Quantas vezes esse problema apareceu ou tende a aparecer?",
                key="prio_frequencia",
            )

            confianca_feedback = st.slider(
                "Confiança na evidência",
                1,
                10,
                6,
                help="O feedback é forte, observado e repetido ou apenas uma hipótese?",
                key="prio_confianca",
            )

        col_score_1, col_score_2 = st.columns(2)

        with col_score_1:
            urgencia_estrategica = st.slider(
                "Urgência estratégica",
                1,
                10,
                6,
                help="Isso é importante para avançar beta, conversão, retenção ou confiança?",
                key="prio_urgencia",
            )

        with col_score_2:
            esforco_desenvolvimento = st.slider(
                "Esforço de desenvolvimento",
                1,
                10,
                4,
                help="1 = fácil, 10 = difícil. Quanto maior o esforço, menor o score.",
                key="prio_esforco",
            )

        score_preview = calcular_score_prioridade(
            impacto_usuario=impacto_usuario,
            frequencia_feedback=frequencia_feedback,
            confianca_feedback=confianca_feedback,
            urgencia_estrategica=urgencia_estrategica,
            esforco_desenvolvimento=esforco_desenvolvimento,
        )

        st.info(
            f"Score calculado: **{score_preview}/100** — {classificar_prioridade(score_preview)}"
        )

        descricao = st.text_area(
            "Descrição da melhoria",
            value="",
            height=90,
            placeholder="Explique objetivamente o que deve mudar.",
            key="prio_descricao",
        )

        problema_observado = st.text_area(
            "Problema observado",
            value="",
            height=90,
            placeholder="Qual dor, confusão ou fricção essa melhoria resolve?",
            key="prio_problema",
        )

        evidencia_feedback = st.text_area(
            "Evidência do feedback",
            value="",
            height=90,
            placeholder="Ex: 3 usuários travaram na tela inicial; 2 disseram que não entenderam preço-teto...",
            key="prio_evidencia",
        )

        observacoes = st.text_area(
            "Observações",
            value="",
            height=80,
            key="prio_observacoes",
        )

        enviar = st.form_submit_button("Salvar melhoria priorizada")

        if enviar:
            if titulo_melhoria.strip() == "":
                st.error("Preencha o título da melhoria.")
            elif problema_observado.strip() == "":
                st.error("Preencha o problema observado.")
            else:
                adicionar_priorizacao_feedback(
                    titulo_melhoria=titulo_melhoria,
                    origem_feedback=origem_feedback,
                    area_produto=area_produto,
                    perfil_impactado=perfil_impactado,
                    tipo_melhoria=tipo_melhoria,
                    descricao=descricao,
                    problema_observado=problema_observado,
                    evidencia_feedback=evidencia_feedback,
                    impacto_usuario=impacto_usuario,
                    frequencia_feedback=frequencia_feedback,
                    confianca_feedback=confianca_feedback,
                    urgencia_estrategica=urgencia_estrategica,
                    esforco_desenvolvimento=esforco_desenvolvimento,
                    status=status,
                    proxima_acao=proxima_acao,
                    observacoes=observacoes,
                )

                st.success("Melhoria priorizada registrada com sucesso.")
                st.rerun()

    st.divider()

    st.markdown("### Ranking de prioridades")

    registros = carregar_priorizacoes_feedback()

    if len(registros) == 0:
        st.info("Nenhuma melhoria priorizada ainda.")
    else:
        st.dataframe(
            _gerar_tabela_prioridades(registros),
            use_container_width=True,
            hide_index=True,
        )

        st.divider()

        st.markdown("### Roadmap sugerido")

        st.dataframe(
            _gerar_roadmap_sugerido(registros),
            use_container_width=True,
            hide_index=True,
        )

        st.divider()

        st.markdown("### Detalhamento das evidências")

        st.dataframe(
            _gerar_tabela_detalhada(registros),
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    st.markdown("### Checklist de priorização")

    st.dataframe(
        _gerar_checklist_priorizacao(),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    if len(registros) > 0:
        col_download, col_limpar = st.columns(2)

        with col_download:
            with open(CAMINHO_PRIORIZACAO_FEEDBACK, "rb") as arquivo:
                st.download_button(
                    label="Baixar priorização em CSV",
                    data=arquivo,
                    file_name="priorizacao_feedback_beta.csv",
                    mime="text/csv",
                    key="download_priorizacao_feedback_csv",
                )

            st.download_button(
                label="Baixar relatório de priorização (.md)",
                data=_gerar_markdown_priorizacao(registros),
                file_name="relatorio_priorizacao_feedback_beta.md",
                mime="text/markdown",
                key="download_priorizacao_feedback_md",
            )

        with col_limpar:
            confirmar = st.checkbox(
                "Confirmar limpeza das priorizações",
                value=False,
                key="prio_confirmar_limpeza",
            )

            if st.button("Limpar priorizações", key="prio_limpar"):
                if confirmar:
                    limpar_priorizacoes_feedback()
                    st.success("Priorizações limpas com sucesso.")
                    st.rerun()
                else:
                    st.warning("Marque a confirmação antes de limpar.")

    st.markdown(
        """
        <div class="prio-disclaimer">
            <strong>Regra de produto:</strong> a próxima versão deve atacar poucas melhorias bem priorizadas.
            Melhor entregar 2 ajustes importantes do que 10 mudanças sem evidência.
        </div>
        """,
        unsafe_allow_html=True,
    )