# sprints_beta.py

import csv
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v2.4 — Sprints Beta e Execução do Roadmap
# ------------------------------------------------------------
# Esta tela transforma prioridades em execução controlada.
#
# Objetivo:
# - organizar sprints pequenas de melhoria
# - evitar escopo inflado
# - ligar feedback priorizado a versões reais
# - definir critério de sucesso antes de programar
# - registrar resultado após teste
# ============================================================


CAMINHO_SPRINTS_BETA = Path("sprints_beta.csv")


CAMPOS_SPRINTS = [
    "id",
    "data_registro",
    "nome_sprint",
    "versao_alvo",
    "melhoria_priorizada",
    "area_produto",
    "tipo_sprint",
    "objetivo_sprint",
    "escopo_incluido",
    "escopo_excluido",
    "criterio_sucesso",
    "risco_principal",
    "nivel_impacto",
    "nivel_esforco",
    "risco_escopo",
    "score_execucao",
    "classificacao",
    "status_sprint",
    "responsavel",
    "prazo_estimado",
    "resultado_teste",
    "decisao_pos_teste",
    "proxima_acao",
    "observacoes",
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
    "Aprendizado Beta",
    "Rodadas Beta",
    "Prioridades Beta",
    "Outro",
]


TIPOS_SPRINT = [
    "Clareza",
    "Usabilidade",
    "Visual",
    "Funcionalidade",
    "Correção de bug",
    "Relatório",
    "Valuation",
    "Conversão",
    "Dados",
    "Marketing",
    "Arquitetura",
    "Outro",
]


STATUS_SPRINT = [
    "Planejada",
    "Em desenvolvimento",
    "Em teste",
    "Concluída",
    "Pausada",
    "Cancelada",
    "Reabrir depois",
]


DECISOES_POS_TESTE = [
    "Ainda não testado",
    "Melhoria validada",
    "Precisa ajustar",
    "Testar com mais usuários",
    "Reverter mudança",
    "Transformar em nova sprint",
    "Descartar por enquanto",
]


PROXIMAS_ACOES = [
    "Começar desenvolvimento",
    "Quebrar em tarefas menores",
    "Testar localmente",
    "Publicar versão",
    "Enviar para beta testers",
    "Coletar feedback",
    "Criar nova prioridade",
    "Fechar sprint",
    "Aguardar",
]


def _garantir_arquivo_sprints() -> None:
    if CAMINHO_SPRINTS_BETA.exists():
        return

    with open(CAMINHO_SPRINTS_BETA, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_SPRINTS)
        escritor.writeheader()


def carregar_sprints_beta() -> List[Dict[str, str]]:
    _garantir_arquivo_sprints()

    with open(CAMINHO_SPRINTS_BETA, "r", newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        registros = []

        for linha in leitor:
            registro = {campo: linha.get(campo, "") for campo in CAMPOS_SPRINTS}
            registros.append(registro)

        return registros


def salvar_sprints_beta(registros: List[Dict[str, Any]]) -> None:
    with open(CAMINHO_SPRINTS_BETA, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_SPRINTS)
        escritor.writeheader()

        for registro in registros:
            linha = {campo: registro.get(campo, "") for campo in CAMPOS_SPRINTS}
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


def calcular_score_execucao(
    nivel_impacto: int,
    nivel_esforco: int,
    risco_escopo: int,
) -> int:
    """
    Score simples para avaliar se uma sprint é boa para executar agora.

    Quanto maior o impacto, melhor.
    Quanto maior o esforço e o risco de escopo, pior.
    """
    impacto = max(1, nivel_impacto)
    esforco = max(1, nivel_esforco)
    risco = max(1, risco_escopo)

    score = (impacto * 10) - (esforco * 3) - (risco * 2) + 40

    return int(round(max(0, min(100, score))))


def classificar_sprint(score: int) -> str:
    if score >= 85:
        return "Sprint excelente para executar"
    if score >= 70:
        return "Boa sprint"
    if score >= 55:
        return "Sprint viável com cuidado"
    if score >= 40:
        return "Sprint arriscada"
    return "Não executar agora"


def adicionar_sprint_beta(
    nome_sprint: str,
    versao_alvo: str,
    melhoria_priorizada: str,
    area_produto: str,
    tipo_sprint: str,
    objetivo_sprint: str,
    escopo_incluido: str,
    escopo_excluido: str,
    criterio_sucesso: str,
    risco_principal: str,
    nivel_impacto: int,
    nivel_esforco: int,
    risco_escopo: int,
    status_sprint: str,
    responsavel: str,
    prazo_estimado: str,
    resultado_teste: str,
    decisao_pos_teste: str,
    proxima_acao: str,
    observacoes: str,
) -> None:
    registros = carregar_sprints_beta()

    score = calcular_score_execucao(
        nivel_impacto=nivel_impacto,
        nivel_esforco=nivel_esforco,
        risco_escopo=risco_escopo,
    )

    novo_registro = {
        "id": str(uuid.uuid4())[:8],
        "data_registro": datetime.now().isoformat(timespec="minutes"),
        "nome_sprint": nome_sprint.strip(),
        "versao_alvo": versao_alvo.strip(),
        "melhoria_priorizada": melhoria_priorizada.strip(),
        "area_produto": area_produto,
        "tipo_sprint": tipo_sprint,
        "objetivo_sprint": objetivo_sprint.strip(),
        "escopo_incluido": escopo_incluido.strip(),
        "escopo_excluido": escopo_excluido.strip(),
        "criterio_sucesso": criterio_sucesso.strip(),
        "risco_principal": risco_principal.strip(),
        "nivel_impacto": str(nivel_impacto),
        "nivel_esforco": str(nivel_esforco),
        "risco_escopo": str(risco_escopo),
        "score_execucao": str(score),
        "classificacao": classificar_sprint(score),
        "status_sprint": status_sprint,
        "responsavel": responsavel.strip(),
        "prazo_estimado": prazo_estimado.strip(),
        "resultado_teste": resultado_teste.strip(),
        "decisao_pos_teste": decisao_pos_teste,
        "proxima_acao": proxima_acao,
        "observacoes": observacoes.strip(),
    }

    registros.append(novo_registro)
    salvar_sprints_beta(registros)


def limpar_sprints_beta() -> None:
    salvar_sprints_beta([])


def _contar_status(registros: List[Dict[str, str]], status: str) -> int:
    return len([registro for registro in registros if registro.get("status_sprint") == status])


def _media_score(registros: List[Dict[str, str]]) -> float:
    scores = []

    for registro in registros:
        score = _safe_float(registro.get("score_execucao"))

        if score > 0:
            scores.append(score)

    if len(scores) == 0:
        return 0.0

    return sum(scores) / len(scores)


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


def _ordenar_sprints(registros: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return sorted(
        registros,
        key=lambda registro: _safe_int(registro.get("score_execucao")),
        reverse=True,
    )


def _gerar_tabela_sprints(registros: List[Dict[str, str]]) -> List[Dict[str, str]]:
    tabela = []

    for registro in _ordenar_sprints(registros):
        tabela.append(
            {
                "Score": registro.get("score_execucao", ""),
                "Classificação": registro.get("classificacao", ""),
                "Sprint": registro.get("nome_sprint", ""),
                "Versão": registro.get("versao_alvo", ""),
                "Área": registro.get("area_produto", ""),
                "Tipo": registro.get("tipo_sprint", ""),
                "Status": registro.get("status_sprint", ""),
                "Próxima ação": registro.get("proxima_acao", ""),
                "Decisão pós-teste": registro.get("decisao_pos_teste", ""),
                "Prazo": registro.get("prazo_estimado", ""),
            }
        )

    return tabela


def _gerar_tabela_execucao(registros: List[Dict[str, str]]) -> List[Dict[str, str]]:
    tabela = []

    for registro in _ordenar_sprints(registros):
        tabela.append(
            {
                "Sprint": registro.get("nome_sprint", ""),
                "Melhoria priorizada": registro.get("melhoria_priorizada", ""),
                "Objetivo": registro.get("objetivo_sprint", ""),
                "Escopo incluído": registro.get("escopo_incluido", ""),
                "Escopo excluído": registro.get("escopo_excluido", ""),
                "Critério de sucesso": registro.get("criterio_sucesso", ""),
                "Risco principal": registro.get("risco_principal", ""),
            }
        )

    return tabela


def _gerar_tabela_resultados(registros: List[Dict[str, str]]) -> List[Dict[str, str]]:
    tabela = []

    for registro in reversed(registros):
        tabela.append(
            {
                "Sprint": registro.get("nome_sprint", ""),
                "Versão": registro.get("versao_alvo", ""),
                "Status": registro.get("status_sprint", ""),
                "Resultado do teste": registro.get("resultado_teste", ""),
                "Decisão pós-teste": registro.get("decisao_pos_teste", ""),
                "Observações": registro.get("observacoes", ""),
            }
        )

    return tabela


def _gerar_insights_sprints(registros: List[Dict[str, str]]) -> List[str]:
    if len(registros) == 0:
        return [
            "Ainda não há sprints registradas. Comece criando uma sprint pequena baseada na maior prioridade beta.",
            "Uma boa sprint deve ter objetivo, escopo incluído, escopo excluído e critério de sucesso.",
            "Evite colocar muitas melhorias em uma única versão.",
        ]

    insights = []

    total = len(registros)
    planejadas = _contar_status(registros, "Planejada")
    em_desenvolvimento = _contar_status(registros, "Em desenvolvimento")
    concluidas = _contar_status(registros, "Concluída")
    media_score = _media_score(registros)
    area_mais_comum = _mais_frequente(registros, "area_produto")
    tipo_mais_comum = _mais_frequente(registros, "tipo_sprint")

    insights.append(f"Existem {total} sprint(s) registradas.")
    insights.append(f"Score médio de execução: {media_score:.1f}/100.")

    if planejadas > 3:
        insights.append("Há muitas sprints planejadas. Escolha uma principal para executar primeiro.")

    if em_desenvolvimento > 2:
        insights.append("Há muitas sprints em desenvolvimento. Reduza o foco e finalize uma por vez.")

    if concluidas > 0:
        insights.append(f"{concluidas} sprint(s) já foram concluídas. Agora valide com usuários reais.")

    if area_mais_comum != "N/D":
        insights.append(f"A área mais trabalhada nas sprints é: {area_mais_comum}.")

    if tipo_mais_comum != "N/D":
        insights.append(f"O tipo de sprint mais comum é: {tipo_mais_comum}.")

    if media_score < 55:
        insights.append("O score médio está baixo. Talvez as sprints estejam grandes ou com esforço alto demais.")

    insights.append("Na Fase 2, uma sprint boa é pequena, testável e ligada a feedback real.")

    return insights


def _gerar_decisoes_recomendadas(registros: List[Dict[str, str]]) -> List[Dict[str, str]]:
    if len(registros) == 0:
        return [
            {
                "Decisão": "Criar primeira sprint beta",
                "Critério": "Nenhuma sprint registrada.",
                "Ação": "Escolher a maior prioridade beta e transformá-la numa versão pequena.",
                "Prioridade": "Muito alta",
            }
        ]

    decisoes = []
    em_desenvolvimento = _contar_status(registros, "Em desenvolvimento")
    em_teste = _contar_status(registros, "Em teste")
    concluidas = _contar_status(registros, "Concluída")
    prioridades = _ordenar_sprints(registros)

    melhor_sprint = prioridades[0]
    melhor_score = _safe_int(melhor_sprint.get("score_execucao"))

    if em_desenvolvimento == 0 and em_teste == 0:
        decisoes.append(
            {
                "Decisão": "Escolher uma sprint para executar",
                "Critério": "Nenhuma sprint em desenvolvimento ou teste.",
                "Ação": f"Começar pela sprint: {melhor_sprint.get('nome_sprint')}.",
                "Prioridade": "Alta",
            }
        )

    if em_desenvolvimento > 2:
        decisoes.append(
            {
                "Decisão": "Reduzir trabalho simultâneo",
                "Critério": "Mais de 2 sprints em desenvolvimento.",
                "Ação": "Pausar as menos importantes e terminar uma principal.",
                "Prioridade": "Muito alta",
            }
        )

    if em_teste > 0:
        decisoes.append(
            {
                "Decisão": "Coletar feedback pós-sprint",
                "Critério": "Existe sprint em teste.",
                "Ação": "Enviar a melhoria para usuários reais e registrar resultado.",
                "Prioridade": "Alta",
            }
        )

    if concluidas > 0:
        decisoes.append(
            {
                "Decisão": "Comparar antes e depois",
                "Critério": "Há sprint concluída.",
                "Ação": "Verificar se clareza, utilidade ou conversão melhoraram.",
                "Prioridade": "Média",
            }
        )

    if melhor_score < 55:
        decisoes.append(
            {
                "Decisão": "Reformular sprint",
                "Critério": "A melhor sprint ainda tem score baixo.",
                "Ação": "Reduzir escopo, esforço ou risco antes de programar.",
                "Prioridade": "Alta",
            }
        )

    if len(decisoes) == 0:
        decisoes.append(
            {
                "Decisão": "Manter execução disciplinada",
                "Critério": "Não há alerta crítico.",
                "Ação": "Executar uma sprint pequena e validar com usuários.",
                "Prioridade": "Média",
            }
        )

    return decisoes


def _gerar_checklist_sprint() -> List[Dict[str, str]]:
    return [
        {
            "Regra": "Uma sprint deve resolver um problema claro",
            "Motivo": "Evita mudar coisas sem conexão com feedback real.",
        },
        {
            "Regra": "Escopo excluído é obrigatório",
            "Motivo": "Dizer o que não entra evita versão infinita.",
        },
        {
            "Regra": "Critério de sucesso vem antes do código",
            "Motivo": "Você precisa saber o que significa melhorar.",
        },
        {
            "Regra": "Uma sprint deve ser pequena",
            "Motivo": "Beta exige velocidade e aprendizado, não perfeccionismo.",
        },
        {
            "Regra": "Toda sprint concluída precisa de teste real",
            "Motivo": "Só usuário confirma se a mudança teve valor.",
        },
        {
            "Regra": "Não abrir muitas sprints ao mesmo tempo",
            "Motivo": "Foco aumenta a chance de terminar e medir.",
        },
    ]


def _gerar_modelo_sprint_ideal() -> List[Dict[str, str]]:
    return [
        {
            "Campo": "Nome da sprint",
            "Exemplo": "v2.4.1 — Simplificar primeira experiência beta",
        },
        {
            "Campo": "Objetivo",
            "Exemplo": "Fazer o usuário entender o produto em menos de 30 segundos.",
        },
        {
            "Campo": "Escopo incluído",
            "Exemplo": "Ajustar Produto, Navegação e CTA para Feedback Beta.",
        },
        {
            "Campo": "Escopo excluído",
            "Exemplo": "Não mexer no motor de valuation, banco de dados ou visual inteiro.",
        },
        {
            "Campo": "Critério de sucesso",
            "Exemplo": "3 de 5 usuários entendem a proposta sem explicação.",
        },
        {
            "Campo": "Teste",
            "Exemplo": "Enviar para 5 usuários e registrar no Aprendizado Beta.",
        },
    ]


def _gerar_markdown_sprints(registros: List[Dict[str, str]]) -> str:
    linhas_sprints = "\n".join(
        [
            f"| {item['Score']} | {item['Sprint']} | {item['Versão']} | {item['Área']} | {item['Status']} | {item['Próxima ação']} |"
            for item in _gerar_tabela_sprints(registros)
        ]
    )

    linhas_insights = "\n".join(
        [
            f"- {insight}"
            for insight in _gerar_insights_sprints(registros)
        ]
    )

    linhas_decisoes = "\n".join(
        [
            f"| {item['Decisão']} | {item['Critério']} | {item['Ação']} | {item['Prioridade']} |"
            for item in _gerar_decisoes_recomendadas(registros)
        ]
    )

    return f"""# Sprints Beta — Máquina de Preço-Teto

Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Resumo

Total de sprints: {len(registros)}  
Score médio: {_media_score(registros):.1f}/100  
Área mais trabalhada: {_mais_frequente(registros, "area_produto")}  
Tipo mais comum: {_mais_frequente(registros, "tipo_sprint")}

## Sprints

| Score | Sprint | Versão | Área | Status | Próxima ação |
|---:|---|---|---|---|---|
{linhas_sprints}

## Insights automáticos

{linhas_insights}

## Decisões recomendadas

| Decisão | Critério | Ação | Prioridade |
|---|---|---|---|
{linhas_decisoes}

## Regra central

Cada sprint deve ser pequena, testável e conectada a feedback real.
"""


def _injetar_css_sprints() -> None:
    st.markdown(
        """
        <style>
            .sprint-hero {
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

            .sprint-eyebrow {
                color: #d6b56d;
                font-size: 0.78rem;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.35rem;
            }

            .sprint-title {
                color: #f4f7fb;
                font-size: 2.1rem;
                font-weight: 900;
                margin-bottom: 0.45rem;
                line-height: 1.14;
            }

            .sprint-subtitle {
                color: rgba(244, 247, 251, 0.76);
                font-size: 1rem;
                line-height: 1.62;
                max-width: 1080px;
            }

            .sprint-card {
                padding: 1.1rem 1.15rem;
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.035);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.18);
                height: 100%;
            }

            .sprint-card-label {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .sprint-card-value {
                color: #f4f7fb;
                font-size: 1.22rem;
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .sprint-card-note {
                color: rgba(244, 247, 251, 0.68);
                font-size: 0.87rem;
                line-height: 1.47;
            }

            .sprint-highlight {
                padding: 0.95rem 1rem;
                border-radius: 16px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.92rem;
                line-height: 1.55;
                margin-bottom: 0.7rem;
            }

            .sprint-disclaimer {
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
        <div class="sprint-card">
            <div class="sprint-card-label">{label}</div>
            <div class="sprint-card-value">{value}</div>
            <div class="sprint-card-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def renderizar_sprints_beta() -> None:
    """
    Renderiza a central de sprints beta.
    """
    _injetar_css_sprints()

    registros = carregar_sprints_beta()

    total = len(registros)
    media_score = _media_score(registros)
    planejadas = _contar_status(registros, "Planejada")
    em_desenvolvimento = _contar_status(registros, "Em desenvolvimento")
    em_teste = _contar_status(registros, "Em teste")
    concluidas = _contar_status(registros, "Concluída")
    area_mais_comum = _mais_frequente(registros, "area_produto")

    st.session_state["resultado_sprints_beta"] = {
        "total_sprints": total,
        "media_score": media_score,
        "planejadas": planejadas,
        "em_desenvolvimento": em_desenvolvimento,
        "em_teste": em_teste,
        "concluidas": concluidas,
        "area_mais_comum": area_mais_comum,
    }

    st.markdown(
        """
        <div class="sprint-hero">
            <div class="sprint-eyebrow">Fase 2.4 — Execução disciplinada</div>
            <div class="sprint-title">Sprints Beta e Execução do Roadmap</div>
            <div class="sprint-subtitle">
                Transforme prioridades em versões pequenas, testáveis e ligadas a feedback real.
                Cada sprint precisa ter objetivo, escopo, critério de sucesso e validação pós-teste.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="sprint-highlight">
            A prioridade diz o que importa. A sprint define como executar sem virar bagunça.
            O objetivo é melhorar pouco, testar rápido e aprender com usuários reais.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Diagnóstico das sprints")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Sprints registradas", total)

    with col_2:
        st.metric("Score médio", f"{media_score:.1f}/100")

    with col_3:
        st.metric("Em desenvolvimento", em_desenvolvimento)

    with col_4:
        st.metric("Concluídas", concluidas)

    st.divider()

    st.markdown("### Indicadores operacionais")

    col_a, col_b, col_c, col_d = st.columns(4)

    with col_a:
        _card("Planejadas", str(planejadas), "Sprints ainda não iniciadas.")

    with col_b:
        _card("Em teste", str(em_teste), "Mudanças aguardando validação real.")

    with col_c:
        _card("Área mais comum", area_mais_comum, "Onde o produto está evoluindo mais.")

    with col_d:
        _card("Foco recomendado", "1 sprint", "Evite trabalhar em várias ao mesmo tempo.")

    st.divider()

    st.markdown("### Insights automáticos")

    for insight in _gerar_insights_sprints(registros):
        st.markdown(f"- {insight}")

    st.divider()

    st.markdown("### Decisões recomendadas")

    st.dataframe(
        _gerar_decisoes_recomendadas(registros),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Registrar sprint beta")

    with st.form("form_sprints_beta"):
        col_form_1, col_form_2 = st.columns(2)

        with col_form_1:
            nome_sprint = st.text_input(
                "Nome da sprint",
                value="v2.4.1 — Melhorar clareza da primeira experiência",
                key="sprint_nome",
            )

            versao_alvo = st.text_input(
                "Versão alvo",
                value="v2.4.1",
                key="sprint_versao",
            )

            melhoria_priorizada = st.text_input(
                "Melhoria priorizada relacionada",
                value="",
                placeholder="Ex: Simplificar tela Produto e Navegação",
                key="sprint_melhoria",
            )

            area_produto = st.selectbox(
                "Área do produto",
                AREAS_PRODUTO,
                key="sprint_area",
            )

            tipo_sprint = st.selectbox(
                "Tipo de sprint",
                TIPOS_SPRINT,
                key="sprint_tipo",
            )

        with col_form_2:
            status_sprint = st.selectbox(
                "Status da sprint",
                STATUS_SPRINT,
                key="sprint_status",
            )

            responsavel = st.text_input(
                "Responsável",
                value="Leo",
                key="sprint_responsavel",
            )

            prazo_estimado = st.text_input(
                "Prazo estimado",
                value="",
                placeholder="Ex: 1 dia, 2 dias, esta semana...",
                key="sprint_prazo",
            )

            decisao_pos_teste = st.selectbox(
                "Decisão pós-teste",
                DECISOES_POS_TESTE,
                key="sprint_decisao_pos_teste",
            )

            proxima_acao = st.selectbox(
                "Próxima ação",
                PROXIMAS_ACOES,
                key="sprint_proxima_acao",
            )

        objetivo_sprint = st.text_area(
            "Objetivo da sprint",
            value="",
            height=90,
            placeholder="Qual resultado essa sprint precisa gerar?",
            key="sprint_objetivo",
        )

        escopo_incluido = st.text_area(
            "Escopo incluído",
            value="",
            height=90,
            placeholder="O que entra nesta versão?",
            key="sprint_escopo_incluido",
        )

        escopo_excluido = st.text_area(
            "Escopo excluído",
            value="",
            height=90,
            placeholder="O que NÃO entra nesta versão?",
            key="sprint_escopo_excluido",
        )

        criterio_sucesso = st.text_area(
            "Critério de sucesso",
            value="",
            height=90,
            placeholder="Como saberemos que a sprint deu certo?",
            key="sprint_criterio",
        )

        risco_principal = st.text_area(
            "Risco principal",
            value="",
            height=80,
            placeholder="Ex: escopo crescer demais, mexer em muitas áreas, não ter teste real...",
            key="sprint_risco",
        )

        st.markdown("#### Avaliação da sprint")

        col_score_1, col_score_2, col_score_3 = st.columns(3)

        with col_score_1:
            nivel_impacto = st.slider(
                "Impacto esperado",
                1,
                10,
                7,
                key="sprint_impacto",
            )

        with col_score_2:
            nivel_esforco = st.slider(
                "Esforço técnico",
                1,
                10,
                4,
                key="sprint_esforco",
            )

        with col_score_3:
            risco_escopo = st.slider(
                "Risco de escopo inflado",
                1,
                10,
                4,
                key="sprint_risco_escopo",
            )

        score_preview = calcular_score_execucao(
            nivel_impacto=nivel_impacto,
            nivel_esforco=nivel_esforco,
            risco_escopo=risco_escopo,
        )

        st.info(
            f"Score de execução: **{score_preview}/100** — {classificar_sprint(score_preview)}"
        )

        resultado_teste = st.text_area(
            "Resultado do teste",
            value="",
            height=80,
            placeholder="Preencha depois de testar com usuários.",
            key="sprint_resultado_teste",
        )

        observacoes = st.text_area(
            "Observações",
            value="",
            height=80,
            key="sprint_observacoes",
        )

        enviar = st.form_submit_button("Salvar sprint beta")

        if enviar:
            if nome_sprint.strip() == "":
                st.error("Preencha o nome da sprint.")
            elif objetivo_sprint.strip() == "":
                st.error("Preencha o objetivo da sprint.")
            elif escopo_excluido.strip() == "":
                st.error("Preencha o escopo excluído. Isso evita versão infinita.")
            elif criterio_sucesso.strip() == "":
                st.error("Preencha o critério de sucesso.")
            else:
                adicionar_sprint_beta(
                    nome_sprint=nome_sprint,
                    versao_alvo=versao_alvo,
                    melhoria_priorizada=melhoria_priorizada,
                    area_produto=area_produto,
                    tipo_sprint=tipo_sprint,
                    objetivo_sprint=objetivo_sprint,
                    escopo_incluido=escopo_incluido,
                    escopo_excluido=escopo_excluido,
                    criterio_sucesso=criterio_sucesso,
                    risco_principal=risco_principal,
                    nivel_impacto=nivel_impacto,
                    nivel_esforco=nivel_esforco,
                    risco_escopo=risco_escopo,
                    status_sprint=status_sprint,
                    responsavel=responsavel,
                    prazo_estimado=prazo_estimado,
                    resultado_teste=resultado_teste,
                    decisao_pos_teste=decisao_pos_teste,
                    proxima_acao=proxima_acao,
                    observacoes=observacoes,
                )

                st.success("Sprint beta registrada com sucesso.")
                st.rerun()

    st.divider()

    st.markdown("### Ranking das sprints")

    registros = carregar_sprints_beta()

    if len(registros) == 0:
        st.info("Nenhuma sprint beta registrada ainda.")
    else:
        st.dataframe(
            _gerar_tabela_sprints(registros),
            use_container_width=True,
            hide_index=True,
        )

        st.divider()

        st.markdown("### Execução e escopo")

        st.dataframe(
            _gerar_tabela_execucao(registros),
            use_container_width=True,
            hide_index=True,
        )

        st.divider()

        st.markdown("### Resultados pós-teste")

        st.dataframe(
            _gerar_tabela_resultados(registros),
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    st.markdown("### Checklist de sprint boa")

    st.dataframe(
        _gerar_checklist_sprint(),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Modelo de sprint ideal")

    st.dataframe(
        _gerar_modelo_sprint_ideal(),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    if len(registros) > 0:
        col_download, col_limpar = st.columns(2)

        with col_download:
            with open(CAMINHO_SPRINTS_BETA, "rb") as arquivo:
                st.download_button(
                    label="Baixar sprints beta em CSV",
                    data=arquivo,
                    file_name="sprints_beta.csv",
                    mime="text/csv",
                    key="download_sprints_beta_csv",
                )

            st.download_button(
                label="Baixar relatório de sprints (.md)",
                data=_gerar_markdown_sprints(registros),
                file_name="relatorio_sprints_beta.md",
                mime="text/markdown",
                key="download_sprints_beta_md",
            )

        with col_limpar:
            confirmar = st.checkbox(
                "Confirmar limpeza das sprints",
                value=False,
                key="sprint_confirmar_limpeza",
            )

            if st.button("Limpar sprints beta", key="sprint_limpar"):
                if confirmar:
                    limpar_sprints_beta()
                    st.success("Sprints limpas com sucesso.")
                    st.rerun()
                else:
                    st.warning("Marque a confirmação antes de limpar.")

    st.markdown(
        """
        <div class="sprint-disclaimer">
            <strong>Regra de execução:</strong> uma sprint deve ser pequena o suficiente para ser concluída,
            publicada e testada rapidamente. Se parece grande demais, divida.
        </div>
        """,
        unsafe_allow_html=True,
    )