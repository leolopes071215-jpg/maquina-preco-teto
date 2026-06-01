# rodadas_beta.py

import csv
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v2.2 — Rodadas de Teste Beta e Entrevista Guiada
# ------------------------------------------------------------
# Esta tela organiza ciclos de teste do beta real.
#
# Objetivo:
# - estruturar rodadas de validação
# - controlar meta de usuários por rodada
# - registrar aprendizados consolidados
# - transformar feedback em decisão de produto
# - evitar crescimento desorganizado do beta
# ============================================================


CAMINHO_RODADAS_BETA = Path("rodadas_beta.csv")


CAMPOS_RODADAS = [
    "id",
    "data_registro",
    "nome_rodada",
    "fase",
    "publico_alvo",
    "canal_principal",
    "objetivo_rodada",
    "meta_testers",
    "testes_realizados",
    "status_rodada",
    "clareza_media",
    "utilidade_media",
    "intencao_pagamento",
    "principal_aprendizado",
    "principal_friccao",
    "decisao_produto",
    "proxima_acao",
    "observacoes",
]


FASES_BETA = [
    "Fase 2.1 — 5 usuários próximos",
    "Fase 2.2 — 10 usuários segmentados",
    "Fase 2.3 — 20 usuários ampliados",
    "Fase 2.4 — pré-venda manual",
    "Fase 2.5 — beta pago controlado",
]


PUBLICOS_ALVO = [
    "Pessoas próximas",
    "Investidores iniciantes",
    "Investidores intermediários",
    "Investidores avançados",
    "Estudantes",
    "Criadores de conteúdo financeiro",
    "Comunidade de investimentos",
    "Misto",
]


CANAIS_CONVITE = [
    "WhatsApp",
    "Instagram",
    "LinkedIn",
    "E-mail",
    "Presencial",
    "Indicação",
    "Grupo de investidores",
    "Misto",
]


STATUS_RODADA = [
    "Planejada",
    "Em andamento",
    "Concluída",
    "Pausada",
    "Cancelada",
]


DECISOES_PRODUTO = [
    "Continuar coletando feedback",
    "Melhorar clareza da proposta",
    "Melhorar onboarding",
    "Simplificar navegação",
    "Melhorar relatório",
    "Melhorar valuation",
    "Melhorar visual",
    "Testar preço/oferta",
    "Avançar para próxima rodada",
    "Pausar e corrigir produto",
]


PROXIMAS_ACOES = [
    "Convidar mais testers",
    "Fazer entrevistas individuais",
    "Corrigir fricção principal",
    "Revisar copy do produto",
    "Revisar fluxo do usuário beta",
    "Preparar nova rodada",
    "Testar intenção de pagamento",
    "Criar oferta manual",
    "Aguardar mais dados",
]


def _garantir_arquivo_rodadas() -> None:
    if CAMINHO_RODADAS_BETA.exists():
        return

    with open(CAMINHO_RODADAS_BETA, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_RODADAS)
        escritor.writeheader()


def carregar_rodadas_beta() -> List[Dict[str, str]]:
    _garantir_arquivo_rodadas()

    with open(CAMINHO_RODADAS_BETA, "r", newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        registros = []

        for linha in leitor:
            registro = {campo: linha.get(campo, "") for campo in CAMPOS_RODADAS}
            registros.append(registro)

        return registros


def salvar_rodadas_beta(registros: List[Dict[str, Any]]) -> None:
    with open(CAMINHO_RODADAS_BETA, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_RODADAS)
        escritor.writeheader()

        for registro in registros:
            linha = {campo: registro.get(campo, "") for campo in CAMPOS_RODADAS}
            escritor.writerow(linha)


def adicionar_rodada_beta(
    nome_rodada: str,
    fase: str,
    publico_alvo: str,
    canal_principal: str,
    objetivo_rodada: str,
    meta_testers: int,
    testes_realizados: int,
    status_rodada: str,
    clareza_media: int,
    utilidade_media: int,
    intencao_pagamento: str,
    principal_aprendizado: str,
    principal_friccao: str,
    decisao_produto: str,
    proxima_acao: str,
    observacoes: str,
) -> None:
    registros = carregar_rodadas_beta()

    novo_registro = {
        "id": str(uuid.uuid4())[:8],
        "data_registro": datetime.now().isoformat(timespec="minutes"),
        "nome_rodada": nome_rodada.strip(),
        "fase": fase,
        "publico_alvo": publico_alvo,
        "canal_principal": canal_principal,
        "objetivo_rodada": objetivo_rodada.strip(),
        "meta_testers": str(meta_testers),
        "testes_realizados": str(testes_realizados),
        "status_rodada": status_rodada,
        "clareza_media": str(clareza_media),
        "utilidade_media": str(utilidade_media),
        "intencao_pagamento": intencao_pagamento.strip(),
        "principal_aprendizado": principal_aprendizado.strip(),
        "principal_friccao": principal_friccao.strip(),
        "decisao_produto": decisao_produto,
        "proxima_acao": proxima_acao,
        "observacoes": observacoes.strip(),
    }

    registros.append(novo_registro)
    salvar_rodadas_beta(registros)


def limpar_rodadas_beta() -> None:
    salvar_rodadas_beta([])


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


def _fmt_percentual(valor: float) -> str:
    return f"{valor:.1f}%"


def _calcular_progresso(meta: int, realizados: int) -> float:
    if meta <= 0:
        return 0.0

    return min(100.0, (realizados / meta) * 100)


def _media_campo(registros: List[Dict[str, str]], campo: str) -> float:
    valores = []

    for registro in registros:
        valor = _safe_float(registro.get(campo))

        if valor > 0:
            valores.append(valor)

    if len(valores) == 0:
        return 0.0

    return sum(valores) / len(valores)


def _somar_campo(registros: List[Dict[str, str]], campo: str) -> int:
    return sum([_safe_int(registro.get(campo)) for registro in registros])


def _contar_status(registros: List[Dict[str, str]], status: str) -> int:
    return len([registro for registro in registros if registro.get("status_rodada") == status])


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


def _calcular_score_rodadas(registros: List[Dict[str, str]]) -> int:
    if len(registros) == 0:
        return 0

    total_rodadas = len(registros)
    rodadas_concluidas = _contar_status(registros, "Concluída")
    total_meta = _somar_campo(registros, "meta_testers")
    total_testes = _somar_campo(registros, "testes_realizados")
    media_clareza = _media_campo(registros, "clareza_media")
    media_utilidade = _media_campo(registros, "utilidade_media")

    progresso_testes = 0.0

    if total_meta > 0:
        progresso_testes = min(100.0, (total_testes / total_meta) * 100)

    pontos = 0.0

    pontos += min(total_rodadas * 10.0, 25)
    pontos += min(rodadas_concluidas * 12.0, 25)
    pontos += progresso_testes * 0.25
    pontos += media_clareza * 1.2
    pontos += media_utilidade * 1.3

    return int(round(max(0, min(100, pontos))))


def _classificar_score(score: int) -> str:
    if score >= 85:
        return "Validação beta bem estruturada"
    if score >= 70:
        return "Boa estrutura de validação"
    if score >= 55:
        return "Validação em andamento"
    if score >= 40:
        return "Estrutura ainda frágil"
    return "Pouca validação estruturada"


def _gerar_leitura_score(score: int, registros: List[Dict[str, str]]) -> str:
    if len(registros) == 0:
        return (
            "Nenhuma rodada foi registrada ainda. Comece com uma rodada pequena: 5 pessoas próximas, "
            "objetivo claro e registro disciplinado dos aprendizados."
        )

    if score >= 85:
        return (
            "As rodadas estão bem estruturadas. Agora o foco deve ser transformar padrões repetidos "
            "em melhorias objetivas no produto e testar intenção de pagamento."
        )

    if score >= 70:
        return (
            "A estrutura de validação está boa. Continue coletando dados e evite decisões baseadas "
            "em feedbacks isolados."
        )

    if score >= 55:
        return (
            "A validação está em andamento, mas ainda precisa de mais volume, clareza de objetivo "
            "e consolidação dos aprendizados."
        )

    if score >= 40:
        return (
            "A estrutura ainda está frágil. Organize melhor metas, público, decisões e próximos passos."
        )

    return (
        "Ainda não existe validação estruturada suficiente. Registre a primeira rodada antes de avançar."
    )


def _gerar_tabela_rodadas(registros: List[Dict[str, str]]) -> List[Dict[str, str]]:
    tabela = []

    for registro in reversed(registros):
        meta = _safe_int(registro.get("meta_testers"))
        realizados = _safe_int(registro.get("testes_realizados"))
        progresso = _calcular_progresso(meta, realizados)

        tabela.append(
            {
                "Rodada": registro.get("nome_rodada", ""),
                "Fase": registro.get("fase", ""),
                "Público": registro.get("publico_alvo", ""),
                "Canal": registro.get("canal_principal", ""),
                "Status": registro.get("status_rodada", ""),
                "Meta": str(meta),
                "Realizados": str(realizados),
                "Progresso": _fmt_percentual(progresso),
                "Clareza": f"{registro.get('clareza_media', '')}/10",
                "Utilidade": f"{registro.get('utilidade_media', '')}/10",
                "Decisão": registro.get("decisao_produto", ""),
                "Próxima ação": registro.get("proxima_acao", ""),
            }
        )

    return tabela


def _gerar_tabela_aprendizados(registros: List[Dict[str, str]]) -> List[Dict[str, str]]:
    tabela = []

    for registro in reversed(registros):
        tabela.append(
            {
                "Rodada": registro.get("nome_rodada", ""),
                "Principal aprendizado": registro.get("principal_aprendizado", ""),
                "Principal fricção": registro.get("principal_friccao", ""),
                "Intenção de pagamento": registro.get("intencao_pagamento", ""),
                "Observações": registro.get("observacoes", ""),
            }
        )

    return tabela


def _gerar_roteiro_entrevista() -> List[Dict[str, str]]:
    return [
        {
            "Momento": "Antes do teste",
            "Pergunta": "O que você acha que este produto faz só olhando a primeira tela?",
            "Objetivo": "Medir clareza da primeira impressão.",
        },
        {
            "Momento": "Antes do teste",
            "Pergunta": "Você já usa alguma planilha, app ou método para analisar investimentos?",
            "Objetivo": "Entender concorrentes reais e hábitos atuais.",
        },
        {
            "Momento": "Durante o teste",
            "Pergunta": "Qual seria seu próximo clique agora?",
            "Objetivo": "Descobrir se a navegação é intuitiva.",
        },
        {
            "Momento": "Durante o teste",
            "Pergunta": "O que ficou confuso nessa tela?",
            "Objetivo": "Identificar fricções específicas.",
        },
        {
            "Momento": "Durante o teste",
            "Pergunta": "O que parece mais valioso até agora?",
            "Objetivo": "Descobrir valor percebido real.",
        },
        {
            "Momento": "Depois do teste",
            "Pergunta": "Você usaria isso numa análise real? Por quê?",
            "Objetivo": "Medir utilidade prática.",
        },
        {
            "Momento": "Depois do teste",
            "Pergunta": "O que impediria você de usar de novo?",
            "Objetivo": "Descobrir barreiras de retenção.",
        },
        {
            "Momento": "Depois do teste",
            "Pergunta": "Você pagaria por uma versão melhor? Quanto pareceria justo?",
            "Objetivo": "Testar monetização sem forçar venda.",
        },
        {
            "Momento": "Depois do teste",
            "Pergunta": "Qual melhoria deixaria isso 2x mais útil?",
            "Objetivo": "Priorizar melhorias de alto impacto.",
        },
    ]


def _gerar_checklist_rodada() -> List[Dict[str, str]]:
    return [
        {
            "Etapa": "Planejamento",
            "Item": "Definir público da rodada",
            "Critério de pronto": "Saber exatamente quem será convidado.",
        },
        {
            "Etapa": "Planejamento",
            "Item": "Definir meta de testers",
            "Critério de pronto": "Exemplo: 5, 10 ou 20 pessoas.",
        },
        {
            "Etapa": "Planejamento",
            "Item": "Definir objetivo da rodada",
            "Critério de pronto": "Exemplo: medir clareza, utilidade ou preço.",
        },
        {
            "Etapa": "Execução",
            "Item": "Enviar link em Modo Usuário Beta",
            "Critério de pronto": "Usuário não vê abas internas.",
        },
        {
            "Etapa": "Execução",
            "Item": "Pedir feedback logo após o teste",
            "Critério de pronto": "Feedback registrado no mesmo dia.",
        },
        {
            "Etapa": "Análise",
            "Item": "Registrar teste individual em Aprendizado Beta",
            "Critério de pronto": "Cada tester vira dado.",
        },
        {
            "Etapa": "Análise",
            "Item": "Registrar conclusão da rodada",
            "Critério de pronto": "Aprendizado, fricção e decisão preenchidos.",
        },
        {
            "Etapa": "Decisão",
            "Item": "Escolher próxima ação",
            "Critério de pronto": "Corrigir, testar mais, avançar ou pausar.",
        },
    ]


def _gerar_plano_rodadas_recomendado() -> List[Dict[str, str]]:
    return [
        {
            "Rodada": "Rodada 1",
            "Público": "5 pessoas próximas",
            "Objetivo": "Ver se entendem a proposta sem explicação longa.",
            "Decisão esperada": "Corrigir clareza e fluxo inicial.",
        },
        {
            "Rodada": "Rodada 2",
            "Público": "10 investidores iniciantes/intermediários",
            "Objetivo": "Medir utilidade do valuation, relatório e onboarding.",
            "Decisão esperada": "Ajustar valor percebido e linguagem.",
        },
        {
            "Rodada": "Rodada 3",
            "Público": "10 investidores mais avançados",
            "Objetivo": "Validar profundidade, premissas e credibilidade.",
            "Decisão esperada": "Melhorar robustez do produto.",
        },
        {
            "Rodada": "Rodada 4",
            "Público": "10 pessoas com intenção de pagar",
            "Objetivo": "Testar preço, oferta e disposição real de compra.",
            "Decisão esperada": "Definir pré-venda ou beta pago.",
        },
    ]


def _gerar_insights_rodadas(registros: List[Dict[str, str]]) -> List[str]:
    if len(registros) == 0:
        return [
            "Comece com uma rodada pequena de 5 pessoas próximas.",
            "Defina um objetivo simples: clareza, utilidade ou intenção de pagamento.",
            "Não convide muita gente antes de aprender com os primeiros testes.",
        ]

    insights = []

    total_rodadas = len(registros)
    total_meta = _somar_campo(registros, "meta_testers")
    total_testes = _somar_campo(registros, "testes_realizados")
    media_clareza = _media_campo(registros, "clareza_media")
    media_utilidade = _media_campo(registros, "utilidade_media")
    publico_mais_comum = _mais_frequente(registros, "publico_alvo")
    decisao_mais_comum = _mais_frequente(registros, "decisao_produto")

    insights.append(f"Você já registrou {total_rodadas} rodada(s) beta.")
    insights.append(f"Meta acumulada: {total_meta} testers. Testes realizados: {total_testes}.")

    if total_meta > 0:
        progresso = _calcular_progresso(total_meta, total_testes)
        insights.append(f"Progresso acumulado das rodadas: {_fmt_percentual(progresso)}.")

    if media_clareza < 7 and total_rodadas > 0:
        insights.append("A clareza média está abaixo do ideal. Reforce Produto, Navegação e Onboarding.")

    if media_utilidade >= 8:
        insights.append("A utilidade média está forte. Preserve o núcleo do produto e valide preço/oferta.")

    if publico_mais_comum != "N/D":
        insights.append(f"O público mais testado até agora é: {publico_mais_comum}.")

    if decisao_mais_comum != "N/D":
        insights.append(f"A decisão mais recorrente até agora é: {decisao_mais_comum}.")

    insights.append("Rodadas bem documentadas evitam que você construa baseado em achismo.")

    return insights


def _gerar_markdown_rodadas(registros: List[Dict[str, str]]) -> str:
    score = _calcular_score_rodadas(registros)
    classificacao = _classificar_score(score)
    leitura = _gerar_leitura_score(score, registros)

    linhas_rodadas = "\n".join(
        [
            f"| {item['Rodada']} | {item['Fase']} | {item['Público']} | {item['Status']} | {item['Meta']} | {item['Realizados']} | {item['Decisão']} |"
            for item in _gerar_tabela_rodadas(registros)
        ]
    )

    linhas_insights = "\n".join(
        [
            f"- {insight}"
            for insight in _gerar_insights_rodadas(registros)
        ]
    )

    return f"""# Rodadas Beta — Máquina de Preço-Teto

Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Resultado

**Score de rodadas:** {score}/100  
**Classificação:** {classificacao}

## Leitura

{leitura}

## Rodadas registradas

| Rodada | Fase | Público | Status | Meta | Realizados | Decisão |
|---|---|---|---|---:|---:|---|
{linhas_rodadas}

## Insights automáticos

{linhas_insights}

## Regra

Cada rodada deve ter objetivo, público, meta, aprendizado, fricção e decisão.
"""


def _injetar_css_rodadas() -> None:
    st.markdown(
        """
        <style>
            .rod-hero {
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

            .rod-eyebrow {
                color: #d6b56d;
                font-size: 0.78rem;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.35rem;
            }

            .rod-title {
                color: #f4f7fb;
                font-size: 2.1rem;
                font-weight: 900;
                margin-bottom: 0.45rem;
                line-height: 1.14;
            }

            .rod-subtitle {
                color: rgba(244, 247, 251, 0.76);
                font-size: 1rem;
                line-height: 1.62;
                max-width: 1080px;
            }

            .rod-card {
                padding: 1.1rem 1.15rem;
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.035);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.18);
                height: 100%;
            }

            .rod-card-label {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .rod-card-value {
                color: #f4f7fb;
                font-size: 1.22rem;
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .rod-card-note {
                color: rgba(244, 247, 251, 0.68);
                font-size: 0.87rem;
                line-height: 1.47;
            }

            .rod-highlight {
                padding: 0.95rem 1rem;
                border-radius: 16px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.92rem;
                line-height: 1.55;
                margin-bottom: 0.7rem;
            }

            .rod-disclaimer {
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
        <div class="rod-card">
            <div class="rod-card-label">{label}</div>
            <div class="rod-card-value">{value}</div>
            <div class="rod-card-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def renderizar_rodadas_beta() -> None:
    """
    Renderiza o painel de rodadas beta.
    """
    _injetar_css_rodadas()

    registros = carregar_rodadas_beta()

    score = _calcular_score_rodadas(registros)
    classificacao = _classificar_score(score)
    leitura = _gerar_leitura_score(score, registros)

    total_rodadas = len(registros)
    rodadas_em_andamento = _contar_status(registros, "Em andamento")
    rodadas_concluidas = _contar_status(registros, "Concluída")
    total_meta = _somar_campo(registros, "meta_testers")
    total_testes = _somar_campo(registros, "testes_realizados")
    progresso_total = _calcular_progresso(total_meta, total_testes)
    publico_mais_comum = _mais_frequente(registros, "publico_alvo")

    st.session_state["resultado_rodadas_beta"] = {
        "score_rodadas": score,
        "classificacao": classificacao,
        "total_rodadas": total_rodadas,
        "rodadas_em_andamento": rodadas_em_andamento,
        "rodadas_concluidas": rodadas_concluidas,
        "total_meta": total_meta,
        "total_testes": total_testes,
        "progresso_total": progresso_total,
        "publico_mais_comum": publico_mais_comum,
    }

    st.markdown(
        """
        <div class="rod-hero">
            <div class="rod-eyebrow">Fase 2.2 — Validação por ciclos</div>
            <div class="rod-title">Rodadas Beta e Entrevista Guiada</div>
            <div class="rod-subtitle">
                Organize ciclos de teste com públicos definidos, metas claras, entrevistas estruturadas
                e decisões baseadas em aprendizado real.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="rod-highlight">
            Uma rodada beta boa não é “mandar o link para todo mundo”. É testar com objetivo,
            observar comportamento, registrar fricções e decidir o próximo passo.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Diagnóstico das rodadas")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Score de rodadas", f"{score}/100")

    with col_2:
        st.metric("Classificação", classificacao)

    with col_3:
        st.metric("Rodadas registradas", total_rodadas)

    with col_4:
        st.metric("Progresso total", _fmt_percentual(progresso_total))

    st.progress(score / 100)

    if score >= 70:
        st.success(leitura)
    elif score >= 40:
        st.warning(leitura)
    else:
        st.error(leitura)

    st.divider()

    st.markdown("### Indicadores operacionais")

    col_a, col_b, col_c, col_d = st.columns(4)

    with col_a:
        _card("Testers planejados", str(total_meta), "Soma das metas de todas as rodadas.")

    with col_b:
        _card("Testes realizados", str(total_testes), "Total informado nas rodadas.")

    with col_c:
        _card("Rodadas em andamento", str(rodadas_em_andamento), "Ciclos ainda ativos.")

    with col_d:
        _card("Público mais testado", publico_mais_comum, "Segmento mais usado nas rodadas.")

    st.divider()

    st.markdown("### Insights automáticos")

    for insight in _gerar_insights_rodadas(registros):
        st.markdown(f"- {insight}")

    st.divider()

    st.markdown("### Criar ou registrar rodada beta")

    with st.form("form_rodada_beta"):
        col_form_1, col_form_2 = st.columns(2)

        with col_form_1:
            nome_rodada = st.text_input(
                "Nome da rodada",
                value="Rodada 1 — 5 usuários próximos",
                key="rod_nome",
            )

            fase = st.selectbox(
                "Fase",
                FASES_BETA,
                key="rod_fase",
            )

            publico_alvo = st.selectbox(
                "Público-alvo",
                PUBLICOS_ALVO,
                key="rod_publico",
            )

            canal_principal = st.selectbox(
                "Canal principal",
                CANAIS_CONVITE,
                key="rod_canal",
            )

            objetivo_rodada = st.text_area(
                "Objetivo da rodada",
                value="Validar se usuários reais entendem a proposta e percebem valor no fluxo principal.",
                height=90,
                key="rod_objetivo",
            )

        with col_form_2:
            meta_testers = st.number_input(
                "Meta de testers",
                min_value=1,
                max_value=500,
                value=5,
                step=1,
                key="rod_meta",
            )

            testes_realizados = st.number_input(
                "Testes realizados",
                min_value=0,
                max_value=500,
                value=0,
                step=1,
                key="rod_realizados",
            )

            status_rodada = st.selectbox(
                "Status da rodada",
                STATUS_RODADA,
                key="rod_status",
            )

            clareza_media = st.slider(
                "Clareza média estimada",
                0,
                10,
                7,
                key="rod_clareza",
            )

            utilidade_media = st.slider(
                "Utilidade média estimada",
                0,
                10,
                7,
                key="rod_utilidade",
            )

        intencao_pagamento = st.text_input(
            "Sinal de intenção de pagamento",
            value="Ainda não testado",
            placeholder="Ex: 2 de 5 pagariam R$ 19/mês",
            key="rod_intencao_pagamento",
        )

        principal_aprendizado = st.text_area(
            "Principal aprendizado da rodada",
            value="",
            height=90,
            placeholder="Ex: usuários entendem preço-teto, mas travam nas premissas.",
            key="rod_aprendizado",
        )

        principal_friccao = st.text_area(
            "Principal fricção observada",
            value="",
            height=90,
            placeholder="Ex: muitas abas, termos técnicos, dificuldade no primeiro uso...",
            key="rod_friccao",
        )

        col_decisao_1, col_decisao_2 = st.columns(2)

        with col_decisao_1:
            decisao_produto = st.selectbox(
                "Decisão de produto",
                DECISOES_PRODUTO,
                key="rod_decisao",
            )

        with col_decisao_2:
            proxima_acao = st.selectbox(
                "Próxima ação",
                PROXIMAS_ACOES,
                key="rod_proxima_acao",
            )

        observacoes = st.text_area(
            "Observações",
            value="",
            height=90,
            key="rod_observacoes",
        )

        enviar = st.form_submit_button("Salvar rodada beta")

        if enviar:
            if nome_rodada.strip() == "":
                st.error("Preencha o nome da rodada.")
            else:
                adicionar_rodada_beta(
                    nome_rodada=nome_rodada,
                    fase=fase,
                    publico_alvo=publico_alvo,
                    canal_principal=canal_principal,
                    objetivo_rodada=objetivo_rodada,
                    meta_testers=meta_testers,
                    testes_realizados=testes_realizados,
                    status_rodada=status_rodada,
                    clareza_media=clareza_media,
                    utilidade_media=utilidade_media,
                    intencao_pagamento=intencao_pagamento,
                    principal_aprendizado=principal_aprendizado,
                    principal_friccao=principal_friccao,
                    decisao_produto=decisao_produto,
                    proxima_acao=proxima_acao,
                    observacoes=observacoes,
                )

                st.success("Rodada beta registrada com sucesso.")
                st.rerun()

    st.divider()

    st.markdown("### Rodadas registradas")

    registros = carregar_rodadas_beta()

    if len(registros) == 0:
        st.info("Nenhuma rodada beta registrada ainda.")
    else:
        st.dataframe(
            _gerar_tabela_rodadas(registros),
            use_container_width=True,
            hide_index=True,
        )

        st.divider()

        st.markdown("### Aprendizados consolidados por rodada")

        st.dataframe(
            _gerar_tabela_aprendizados(registros),
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    st.markdown("### Roteiro de entrevista guiada")

    st.dataframe(
        _gerar_roteiro_entrevista(),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Checklist para executar uma rodada")

    st.dataframe(
        _gerar_checklist_rodada(),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Plano recomendado de rodadas")

    st.dataframe(
        _gerar_plano_rodadas_recomendado(),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    if len(registros) > 0:
        col_download, col_limpar = st.columns(2)

        with col_download:
            with open(CAMINHO_RODADAS_BETA, "rb") as arquivo:
                st.download_button(
                    label="Baixar rodadas beta em CSV",
                    data=arquivo,
                    file_name="rodadas_beta.csv",
                    mime="text/csv",
                    key="download_rodadas_beta_csv",
                )

            st.download_button(
                label="Baixar relatório de rodadas (.md)",
                data=_gerar_markdown_rodadas(registros),
                file_name="relatorio_rodadas_beta.md",
                mime="text/markdown",
                key="download_rodadas_beta_md",
            )

        with col_limpar:
            confirmar = st.checkbox(
                "Confirmar limpeza das rodadas",
                value=False,
                key="rod_confirmar_limpeza",
            )

            if st.button("Limpar rodadas beta", key="rod_limpar"):
                if confirmar:
                    limpar_rodadas_beta()
                    st.success("Rodadas limpas com sucesso.")
                    st.rerun()
                else:
                    st.warning("Marque a confirmação antes de limpar.")

    st.markdown(
        """
        <div class="rod-disclaimer">
            <strong>Regra operacional:</strong> cada rodada deve terminar com uma decisão clara:
            corrigir, testar mais, avançar, pausar ou testar pagamento.
        </div>
        """,
        unsafe_allow_html=True,
    )