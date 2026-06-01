# aprendizado_beta_real.py

import csv
import uuid
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List

import streamlit as st


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v2.1 — Painel de Aprendizado do Beta Real
# ------------------------------------------------------------
# Esta tela inicia a Fase 2 do negócio.
#
# Objetivo:
# - registrar testes reais com usuários
# - transformar feedback em aprendizado de produto
# - medir clareza, utilidade, confiança, UX e intenção de pagamento
# - identificar fricções repetidas
# - orientar próximas decisões antes de adicionar novas funções
# ============================================================


CAMINHO_APRENDIZADO_BETA = Path("aprendizado_beta_real.csv")


CAMPOS_APRENDIZADO = [
    "id",
    "data_registro",
    "nome_tester",
    "perfil",
    "canal_origem",
    "data_teste",
    "tempo_teste_minutos",
    "entendeu_proposta",
    "nota_clareza",
    "nota_utilidade",
    "nota_confianca",
    "nota_visual",
    "nota_facilidade",
    "aba_mais_util",
    "onde_travou",
    "usaria_analise_real",
    "pagaria_versao_melhorada",
    "preco_aceitavel",
    "principal_melhoria",
    "comentario_livre",
    "proxima_acao",
    "status_followup",
]


PERFIS_TESTER = [
    "Investidor iniciante",
    "Investidor intermediário",
    "Investidor avançado",
    "Estudante",
    "Criador de conteúdo financeiro",
    "Pessoa próxima sem perfil investidor",
    "Outro",
]


CANAIS_ORIGEM = [
    "WhatsApp",
    "Instagram",
    "LinkedIn",
    "E-mail",
    "Indicação",
    "Teste presencial",
    "Outro",
]


OPCOES_SIM_NAO_TALVEZ = [
    "Sim",
    "Talvez",
    "Não",
]


ABAS_PRODUTO = [
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
    "Outra",
]


STATUS_FOLLOWUP = [
    "Não iniciado",
    "Aguardando resposta",
    "Feedback recebido",
    "Precisa conversar de novo",
    "Concluído",
]


PROXIMAS_ACOES = [
    "Apenas registrar",
    "Pedir mais detalhes",
    "Convidar para novo teste",
    "Adicionar à lista de espera",
    "Transformar feedback em melhoria",
    "Ignorar por enquanto",
]


def _garantir_arquivo_aprendizado() -> None:
    if CAMINHO_APRENDIZADO_BETA.exists():
        return

    with open(CAMINHO_APRENDIZADO_BETA, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_APRENDIZADO)
        escritor.writeheader()


def carregar_aprendizados_beta() -> List[Dict[str, str]]:
    _garantir_arquivo_aprendizado()

    with open(CAMINHO_APRENDIZADO_BETA, "r", newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        registros = []

        for linha in leitor:
            registro = {campo: linha.get(campo, "") for campo in CAMPOS_APRENDIZADO}
            registros.append(registro)

        return registros


def salvar_aprendizados_beta(registros: List[Dict[str, Any]]) -> None:
    with open(CAMINHO_APRENDIZADO_BETA, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_APRENDIZADO)
        escritor.writeheader()

        for registro in registros:
            linha = {campo: registro.get(campo, "") for campo in CAMPOS_APRENDIZADO}
            escritor.writerow(linha)


def adicionar_aprendizado_beta(
    nome_tester: str,
    perfil: str,
    canal_origem: str,
    data_teste: str,
    tempo_teste_minutos: int,
    entendeu_proposta: str,
    nota_clareza: int,
    nota_utilidade: int,
    nota_confianca: int,
    nota_visual: int,
    nota_facilidade: int,
    aba_mais_util: str,
    onde_travou: str,
    usaria_analise_real: str,
    pagaria_versao_melhorada: str,
    preco_aceitavel: str,
    principal_melhoria: str,
    comentario_livre: str,
    proxima_acao: str,
    status_followup: str,
) -> None:
    registros = carregar_aprendizados_beta()

    novo_registro = {
        "id": str(uuid.uuid4())[:8],
        "data_registro": datetime.now().isoformat(timespec="minutes"),
        "nome_tester": nome_tester.strip(),
        "perfil": perfil,
        "canal_origem": canal_origem,
        "data_teste": data_teste.strip(),
        "tempo_teste_minutos": str(tempo_teste_minutos),
        "entendeu_proposta": entendeu_proposta,
        "nota_clareza": str(nota_clareza),
        "nota_utilidade": str(nota_utilidade),
        "nota_confianca": str(nota_confianca),
        "nota_visual": str(nota_visual),
        "nota_facilidade": str(nota_facilidade),
        "aba_mais_util": aba_mais_util,
        "onde_travou": onde_travou.strip(),
        "usaria_analise_real": usaria_analise_real,
        "pagaria_versao_melhorada": pagaria_versao_melhorada,
        "preco_aceitavel": preco_aceitavel.strip(),
        "principal_melhoria": principal_melhoria.strip(),
        "comentario_livre": comentario_livre.strip(),
        "proxima_acao": proxima_acao,
        "status_followup": status_followup,
    }

    registros.append(novo_registro)
    salvar_aprendizados_beta(registros)


def limpar_aprendizados_beta() -> None:
    salvar_aprendizados_beta([])


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


def _contar(registros: List[Dict[str, str]], campo: str, valor: str) -> int:
    return len([registro for registro in registros if registro.get(campo) == valor])


def _taxa(registros: List[Dict[str, str]], campo: str, valor: str) -> float:
    if len(registros) == 0:
        return 0.0

    return (_contar(registros, campo, valor) / len(registros)) * 100


def _media_campo(registros: List[Dict[str, str]], campo: str) -> float:
    valores = []

    for registro in registros:
        valor = _safe_float(registro.get(campo))

        if valor > 0:
            valores.append(valor)

    if len(valores) == 0:
        return 0.0

    return mean(valores)


def _mais_frequente(registros: List[Dict[str, str]], campo: str) -> str:
    if len(registros) == 0:
        return "N/D"

    contagem = {}

    for registro in registros:
        valor = registro.get(campo, "").strip()

        if valor == "":
            continue

        contagem[valor] = contagem.get(valor, 0) + 1

    if len(contagem) == 0:
        return "N/D"

    return max(contagem, key=contagem.get)


def _calcular_media_geral_notas(registros: List[Dict[str, str]]) -> float:
    campos_nota = [
        "nota_clareza",
        "nota_utilidade",
        "nota_confianca",
        "nota_visual",
        "nota_facilidade",
    ]

    medias = [_media_campo(registros, campo) for campo in campos_nota]
    medias_validas = [valor for valor in medias if valor > 0]

    if len(medias_validas) == 0:
        return 0.0

    return mean(medias_validas)


def _calcular_score_aprendizado(registros: List[Dict[str, str]]) -> int:
    total = len(registros)

    if total == 0:
        return 0

    taxa_entendeu = _taxa(registros, "entendeu_proposta", "Sim")
    taxa_usaria = _taxa(registros, "usaria_analise_real", "Sim")
    taxa_pagaria = _taxa(registros, "pagaria_versao_melhorada", "Sim")
    media_notas = _calcular_media_geral_notas(registros)

    pontos = 0.0

    pontos += min(total * 7.0, 28)
    pontos += taxa_entendeu * 0.22
    pontos += taxa_usaria * 0.20
    pontos += taxa_pagaria * 0.15
    pontos += media_notas * 3.0

    return int(round(max(0, min(100, pontos))))


def _classificar_aprendizado(score: int, total: int) -> str:
    if total == 0:
        return "Sem dados reais ainda"

    if score >= 85:
        return "Sinais fortes de validação inicial"

    if score >= 70:
        return "Boa validação inicial"

    if score >= 55:
        return "Validação parcial"

    if score >= 40:
        return "Sinais fracos ou confusos"

    return "Produto ainda não validado"


def _gerar_leitura_aprendizado(score: int, total: int) -> str:
    if total == 0:
        return (
            "Ainda não há feedbacks reais registrados. O próximo passo é enviar o app para 5 pessoas "
            "e registrar cada teste nesta central."
        )

    if score >= 85:
        return (
            "Os sinais iniciais são fortes. O produto parece claro, útil e com intenção de uso/pagamento. "
            "Ainda assim, avance com beta controlado antes de escalar."
        )

    if score >= 70:
        return (
            "A validação está boa. Há sinais de valor, mas ainda é cedo para concluir. "
            "Colete mais testes e observe padrões de fricção."
        )

    if score >= 55:
        return (
            "Existe algum valor percebido, mas a experiência ainda pode estar confusa ou incompleta. "
            "Priorize melhorias repetidas antes de criar novas funcionalidades."
        )

    if score >= 40:
        return (
            "Os sinais ainda são fracos. Talvez o usuário não esteja entendendo a proposta, ou o produto "
            "ainda não entrega valor rápido o suficiente."
        )

    return (
        "O beta ainda não validou o produto. Volte para clareza de proposta, fluxo mínimo e onboarding."
    )


def _gerar_tabela_resumo(registros: List[Dict[str, str]]) -> List[Dict[str, str]]:
    total = len(registros)

    return [
        {
            "Métrica": "Total de testes registrados",
            "Valor": str(total),
            "Leitura": "Quantidade de pessoas que realmente testaram.",
        },
        {
            "Métrica": "Entenderam a proposta",
            "Valor": _fmt_percentual(_taxa(registros, "entendeu_proposta", "Sim")),
            "Leitura": "Mede clareza da comunicação inicial.",
        },
        {
            "Métrica": "Usariam numa análise real",
            "Valor": _fmt_percentual(_taxa(registros, "usaria_analise_real", "Sim")),
            "Leitura": "Mede utilidade prática percebida.",
        },
        {
            "Métrica": "Pagariam por versão melhorada",
            "Valor": _fmt_percentual(_taxa(registros, "pagaria_versao_melhorada", "Sim")),
            "Leitura": "Mede potencial inicial de monetização.",
        },
        {
            "Métrica": "Nota média de clareza",
            "Valor": f"{_media_campo(registros, 'nota_clareza'):.1f}/10",
            "Leitura": "Se for baixa, o produto está difícil de entender.",
        },
        {
            "Métrica": "Nota média de utilidade",
            "Valor": f"{_media_campo(registros, 'nota_utilidade'):.1f}/10",
            "Leitura": "Se for baixa, o valor percebido ainda é fraco.",
        },
        {
            "Métrica": "Nota média de confiança",
            "Valor": f"{_media_campo(registros, 'nota_confianca'):.1f}/10",
            "Leitura": "Mede sensação de credibilidade.",
        },
        {
            "Métrica": "Nota média visual",
            "Valor": f"{_media_campo(registros, 'nota_visual'):.1f}/10",
            "Leitura": "Mede percepção estética e profissional.",
        },
        {
            "Métrica": "Nota média de facilidade",
            "Valor": f"{_media_campo(registros, 'nota_facilidade'):.1f}/10",
            "Leitura": "Mede fricção de uso.",
        },
    ]


def _gerar_insights_automaticos(registros: List[Dict[str, str]]) -> List[str]:
    if len(registros) == 0:
        return [
            "Ainda não há dados reais. Envie o app para 5 pessoas e registre os testes.",
            "Não adicione novas funções grandes antes de observar usuários reais.",
        ]

    insights = []

    total = len(registros)
    taxa_entendeu = _taxa(registros, "entendeu_proposta", "Sim")
    taxa_usaria = _taxa(registros, "usaria_analise_real", "Sim")
    taxa_pagaria = _taxa(registros, "pagaria_versao_melhorada", "Sim")
    media_clareza = _media_campo(registros, "nota_clareza")
    media_utilidade = _media_campo(registros, "nota_utilidade")
    media_facilidade = _media_campo(registros, "nota_facilidade")
    aba_mais_util = _mais_frequente(registros, "aba_mais_util")
    perfil_mais_comum = _mais_frequente(registros, "perfil")

    if total < 5:
        insights.append("Ainda há poucos testes. Meta mínima inicial: 5 usuários reais.")

    if taxa_entendeu < 70:
        insights.append("A clareza da proposta parece fraca. Reforce Produto, Navegação e Onboarding.")

    if media_clareza < 7 and total > 0:
        insights.append("A nota de clareza está abaixo do ideal. Simplifique textos e explique o fluxo em menos passos.")

    if media_utilidade >= 8:
        insights.append("A utilidade percebida está forte. Preserve o núcleo do produto e evite mudar tudo.")

    if media_facilidade < 7 and total > 0:
        insights.append("A facilidade de uso está baixa. O produto pode estar poderoso, mas ainda difícil de navegar.")

    if taxa_usaria >= 60:
        insights.append("Há sinal de uso real. Pessoas dizem que poderiam usar em uma análise de verdade.")

    if taxa_pagaria >= 40:
        insights.append("Existe sinal inicial de monetização. Comece a mapear preço, plano e promessa com cuidado.")

    if aba_mais_util != "N/D":
        insights.append(f"A aba mais citada como útil até agora é: {aba_mais_util}.")

    if perfil_mais_comum != "N/D":
        insights.append(f"O perfil mais presente nos testes até agora é: {perfil_mais_comum}.")

    insights.append("Na Fase 2, feedback repetido vale mais do que opinião isolada.")

    return insights


def _gerar_proximas_decisoes(registros: List[Dict[str, str]]) -> List[Dict[str, str]]:
    total = len(registros)
    taxa_entendeu = _taxa(registros, "entendeu_proposta", "Sim")
    taxa_usaria = _taxa(registros, "usaria_analise_real", "Sim")
    taxa_pagaria = _taxa(registros, "pagaria_versao_melhorada", "Sim")
    media_facilidade = _media_campo(registros, "nota_facilidade")

    decisoes = []

    if total < 5:
        decisoes.append(
            {
                "Decisão": "Coletar mais testes",
                "Critério": "Menos de 5 usuários registrados.",
                "Ação": "Enviar para mais pessoas próximas antes de mexer no produto.",
                "Prioridade": "Muito alta",
            }
        )

    if taxa_entendeu < 70 and total >= 3:
        decisoes.append(
            {
                "Decisão": "Melhorar clareza da proposta",
                "Critério": "Menos de 70% entenderam claramente.",
                "Ação": "Simplificar textos iniciais e reforçar fluxo recomendado.",
                "Prioridade": "Alta",
            }
        )

    if media_facilidade < 7 and total >= 3:
        decisoes.append(
            {
                "Decisão": "Reduzir fricção de uso",
                "Critério": "Nota de facilidade abaixo de 7.",
                "Ação": "Rever tabelas, excesso de abas e instruções de cada etapa.",
                "Prioridade": "Alta",
            }
        )

    if taxa_usaria >= 60 and total >= 5:
        decisoes.append(
            {
                "Decisão": "Avançar para beta ampliado",
                "Critério": "Pelo menos 60% usariam numa análise real.",
                "Ação": "Chamar mais 10 a 20 pessoas com perfil parecido.",
                "Prioridade": "Média",
            }
        )

    if taxa_pagaria >= 40 and total >= 5:
        decisoes.append(
            {
                "Decisão": "Testar oferta manual",
                "Critério": "Pelo menos 40% pagariam por versão melhorada.",
                "Ação": "Conversar individualmente sobre preço, plano e objeções.",
                "Prioridade": "Média",
            }
        )

    if len(decisoes) == 0:
        decisoes.append(
            {
                "Decisão": "Manter observação",
                "Critério": "Dados ainda inconclusivos.",
                "Ação": "Continuar coletando feedbacks e buscar padrões repetidos.",
                "Prioridade": "Média",
            }
        )

    return decisoes


def _preparar_tabela_registros(registros: List[Dict[str, str]]) -> List[Dict[str, str]]:
    tabela = []

    for registro in reversed(registros):
        tabela.append(
            {
                "Data": registro.get("data_teste", ""),
                "Tester": registro.get("nome_tester", ""),
                "Perfil": registro.get("perfil", ""),
                "Canal": registro.get("canal_origem", ""),
                "Entendeu": registro.get("entendeu_proposta", ""),
                "Usaria": registro.get("usaria_analise_real", ""),
                "Pagaria": registro.get("pagaria_versao_melhorada", ""),
                "Aba mais útil": registro.get("aba_mais_util", ""),
                "Travou em": registro.get("onde_travou", ""),
                "Melhoria principal": registro.get("principal_melhoria", ""),
                "Próxima ação": registro.get("proxima_acao", ""),
                "Follow-up": registro.get("status_followup", ""),
            }
        )

    return tabela


def _gerar_markdown_aprendizado(registros: List[Dict[str, str]]) -> str:
    score = _calcular_score_aprendizado(registros)
    classificacao = _classificar_aprendizado(score, len(registros))
    leitura = _gerar_leitura_aprendizado(score, len(registros))
    resumo = _gerar_tabela_resumo(registros)
    insights = _gerar_insights_automaticos(registros)
    decisoes = _gerar_proximas_decisoes(registros)

    linhas_resumo = "\n".join(
        [
            f"| {item['Métrica']} | {item['Valor']} | {item['Leitura']} |"
            for item in resumo
        ]
    )

    linhas_insights = "\n".join([f"- {item}" for item in insights])

    linhas_decisoes = "\n".join(
        [
            f"| {item['Decisão']} | {item['Critério']} | {item['Ação']} | {item['Prioridade']} |"
            for item in decisoes
        ]
    )

    return f"""# Aprendizado do Beta Real — Máquina de Preço-Teto

Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Resultado geral

**Score de aprendizado:** {score}/100  
**Classificação:** {classificacao}

## Leitura

{leitura}

## Resumo de métricas

| Métrica | Valor | Leitura |
|---|---:|---|
{linhas_resumo}

## Insights automáticos

{linhas_insights}

## Próximas decisões

| Decisão | Critério | Ação | Prioridade |
|---|---|---|---|
{linhas_decisoes}

## Regra da Fase 2

Não adicionar grandes funcionalidades sem feedback real repetido.
"""


def _injetar_css_aprendizado() -> None:
    st.markdown(
        """
        <style>
            .beta-hero {
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

            .beta-eyebrow {
                color: #d6b56d;
                font-size: 0.78rem;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.35rem;
            }

            .beta-title {
                color: #f4f7fb;
                font-size: 2.1rem;
                font-weight: 900;
                margin-bottom: 0.45rem;
                line-height: 1.14;
            }

            .beta-subtitle {
                color: rgba(244, 247, 251, 0.76);
                font-size: 1rem;
                line-height: 1.62;
                max-width: 1080px;
            }

            .beta-card {
                padding: 1.1rem 1.15rem;
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.035);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.18);
                height: 100%;
            }

            .beta-card-label {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .beta-card-value {
                color: #f4f7fb;
                font-size: 1.22rem;
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .beta-card-note {
                color: rgba(244, 247, 251, 0.68);
                font-size: 0.87rem;
                line-height: 1.47;
            }

            .beta-highlight {
                padding: 0.95rem 1rem;
                border-radius: 16px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.92rem;
                line-height: 1.55;
                margin-bottom: 0.7rem;
            }

            .beta-disclaimer {
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
        <div class="beta-card">
            <div class="beta-card-label">{label}</div>
            <div class="beta-card-value">{value}</div>
            <div class="beta-card-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def renderizar_aprendizado_beta_real() -> None:
    """
    Renderiza o painel de aprendizado do beta real.
    """
    _injetar_css_aprendizado()

    registros = carregar_aprendizados_beta()

    score = _calcular_score_aprendizado(registros)
    classificacao = _classificar_aprendizado(score, len(registros))
    leitura = _gerar_leitura_aprendizado(score, len(registros))

    total = len(registros)
    taxa_entendeu = _taxa(registros, "entendeu_proposta", "Sim")
    taxa_usaria = _taxa(registros, "usaria_analise_real", "Sim")
    taxa_pagaria = _taxa(registros, "pagaria_versao_melhorada", "Sim")
    aba_mais_util = _mais_frequente(registros, "aba_mais_util")
    perfil_mais_comum = _mais_frequente(registros, "perfil")

    st.session_state["resultado_aprendizado_beta_real"] = {
        "score_aprendizado": score,
        "classificacao": classificacao,
        "total_testes": total,
        "taxa_entendeu": taxa_entendeu,
        "taxa_usaria": taxa_usaria,
        "taxa_pagaria": taxa_pagaria,
        "aba_mais_util": aba_mais_util,
        "perfil_mais_comum": perfil_mais_comum,
    }

    st.markdown(
        """
        <div class="beta-hero">
            <div class="beta-eyebrow">Fase 2.1 — Beta real</div>
            <div class="beta-title">Painel de Aprendizado do Beta Real</div>
            <div class="beta-subtitle">
                Registre testes reais, transforme feedback em decisão e descubra se a Máquina de Preço-Teto
                está clara, útil, confiável e vendável para usuários de verdade.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="beta-highlight">
            Na Fase 2, o usuário real manda no roadmap. Feedback repetido vale mais que opinião interna.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Diagnóstico do beta real")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Score de aprendizado", f"{score}/100")

    with col_2:
        st.metric("Classificação", classificacao)

    with col_3:
        st.metric("Testes registrados", total)

    with col_4:
        st.metric("Aba mais útil", aba_mais_util)

    st.progress(score / 100)

    if score >= 70:
        st.success(leitura)
    elif score >= 40:
        st.warning(leitura)
    else:
        st.error(leitura)

    st.divider()

    st.markdown("### Indicadores principais")

    col_a, col_b, col_c, col_d = st.columns(4)

    with col_a:
        _card("Entenderam", _fmt_percentual(taxa_entendeu), "Clareza da proposta.")

    with col_b:
        _card("Usariam", _fmt_percentual(taxa_usaria), "Utilidade prática.")

    with col_c:
        _card("Pagariam", _fmt_percentual(taxa_pagaria), "Sinal de monetização.")

    with col_d:
        _card("Perfil mais comum", perfil_mais_comum, "Quem está testando mais.")

    st.divider()

    st.markdown("### Resumo quantitativo")

    st.dataframe(
        _gerar_tabela_resumo(registros),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Insights automáticos")

    for insight in _gerar_insights_automaticos(registros):
        st.markdown(f"- {insight}")

    st.divider()

    st.markdown("### Próximas decisões recomendadas")

    st.dataframe(
        _gerar_proximas_decisoes(registros),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Registrar teste real")

    with st.form("form_aprendizado_beta_real"):
        col_form_1, col_form_2 = st.columns(2)

        with col_form_1:
            nome_tester = st.text_input(
                "Nome ou identificação do tester",
                value="",
                placeholder="Ex: João, Maria, Investidor 01...",
                key="apr_nome_tester",
            )

            perfil = st.selectbox(
                "Perfil do tester",
                PERFIS_TESTER,
                key="apr_perfil",
            )

            canal_origem = st.selectbox(
                "Canal de origem",
                CANAIS_ORIGEM,
                key="apr_canal_origem",
            )

            data_teste = st.text_input(
                "Data do teste",
                value=datetime.now().strftime("%d/%m/%Y"),
                key="apr_data_teste",
            )

            tempo_teste_minutos = st.number_input(
                "Tempo aproximado de teste em minutos",
                min_value=1,
                max_value=180,
                value=15,
                step=1,
                key="apr_tempo_teste",
            )

        with col_form_2:
            entendeu_proposta = st.selectbox(
                "A pessoa entendeu a proposta?",
                OPCOES_SIM_NAO_TALVEZ,
                key="apr_entendeu",
            )

            usaria_analise_real = st.selectbox(
                "Usaria numa análise real?",
                OPCOES_SIM_NAO_TALVEZ,
                key="apr_usaria",
            )

            pagaria_versao_melhorada = st.selectbox(
                "Pagaria por uma versão melhorada?",
                OPCOES_SIM_NAO_TALVEZ,
                key="apr_pagaria",
            )

            preco_aceitavel = st.text_input(
                "Preço aceitável citado",
                value="",
                placeholder="Ex: R$ 19/mês, R$ 29/mês, não pagaria...",
                key="apr_preco",
            )

            aba_mais_util = st.selectbox(
                "Qual aba pareceu mais útil?",
                ABAS_PRODUTO,
                key="apr_aba_mais_util",
            )

        st.markdown("#### Notas de 0 a 10")

        col_n1, col_n2, col_n3, col_n4, col_n5 = st.columns(5)

        with col_n1:
            nota_clareza = st.slider("Clareza", 0, 10, 7, key="apr_nota_clareza")

        with col_n2:
            nota_utilidade = st.slider("Utilidade", 0, 10, 7, key="apr_nota_utilidade")

        with col_n3:
            nota_confianca = st.slider("Confiança", 0, 10, 7, key="apr_nota_confianca")

        with col_n4:
            nota_visual = st.slider("Visual", 0, 10, 7, key="apr_nota_visual")

        with col_n5:
            nota_facilidade = st.slider("Facilidade", 0, 10, 7, key="apr_nota_facilidade")

        onde_travou = st.text_area(
            "Onde a pessoa travou?",
            value="",
            height=90,
            placeholder="Ex: muitas abas, não entendeu valuation, não sabia onde clicar...",
            key="apr_onde_travou",
        )

        principal_melhoria = st.text_area(
            "Principal melhoria sugerida",
            value="",
            height=90,
            placeholder="Ex: simplificar início, melhorar visual, explicar melhor preço-teto...",
            key="apr_melhoria",
        )

        comentario_livre = st.text_area(
            "Comentário livre",
            value="",
            height=90,
            key="apr_comentario_livre",
        )

        col_final_1, col_final_2 = st.columns(2)

        with col_final_1:
            proxima_acao = st.selectbox(
                "Próxima ação",
                PROXIMAS_ACOES,
                key="apr_proxima_acao",
            )

        with col_final_2:
            status_followup = st.selectbox(
                "Status do follow-up",
                STATUS_FOLLOWUP,
                key="apr_status_followup",
            )

        enviar = st.form_submit_button("Salvar teste real")

        if enviar:
            if nome_tester.strip() == "":
                st.error("Preencha pelo menos o nome ou identificação do tester.")
            else:
                adicionar_aprendizado_beta(
                    nome_tester=nome_tester,
                    perfil=perfil,
                    canal_origem=canal_origem,
                    data_teste=data_teste,
                    tempo_teste_minutos=tempo_teste_minutos,
                    entendeu_proposta=entendeu_proposta,
                    nota_clareza=nota_clareza,
                    nota_utilidade=nota_utilidade,
                    nota_confianca=nota_confianca,
                    nota_visual=nota_visual,
                    nota_facilidade=nota_facilidade,
                    aba_mais_util=aba_mais_util,
                    onde_travou=onde_travou,
                    usaria_analise_real=usaria_analise_real,
                    pagaria_versao_melhorada=pagaria_versao_melhorada,
                    preco_aceitavel=preco_aceitavel,
                    principal_melhoria=principal_melhoria,
                    comentario_livre=comentario_livre,
                    proxima_acao=proxima_acao,
                    status_followup=status_followup,
                )

                st.success("Teste real registrado com sucesso.")
                st.rerun()

    st.divider()

    st.markdown("### Registros do beta real")

    registros = carregar_aprendizados_beta()

    if len(registros) == 0:
        st.info("Nenhum teste real registrado ainda.")
    else:
        st.dataframe(
            _preparar_tabela_registros(registros),
            use_container_width=True,
            hide_index=True,
        )

        st.divider()

        col_download, col_limpar = st.columns(2)

        with col_download:
            with open(CAMINHO_APRENDIZADO_BETA, "rb") as arquivo:
                st.download_button(
                    label="Baixar aprendizado beta em CSV",
                    data=arquivo,
                    file_name="aprendizado_beta_real.csv",
                    mime="text/csv",
                    key="download_aprendizado_beta_csv",
                )

            st.download_button(
                label="Baixar relatório de aprendizado (.md)",
                data=_gerar_markdown_aprendizado(registros),
                file_name="relatorio_aprendizado_beta_real.md",
                mime="text/markdown",
                key="download_aprendizado_beta_md",
            )

        with col_limpar:
            confirmar = st.checkbox(
                "Confirmar limpeza dos registros",
                value=False,
                key="apr_confirmar_limpeza",
            )

            if st.button("Limpar registros do beta", key="apr_limpar_registros"):
                if confirmar:
                    limpar_aprendizados_beta()
                    st.success("Registros limpos com sucesso.")
                    st.rerun()
                else:
                    st.warning("Marque a confirmação antes de limpar.")

    st.markdown(
        """
        <div class="beta-disclaimer">
            <strong>Regra da Fase 2:</strong> não transforme opinião isolada em decisão definitiva.
            Busque padrões repetidos em pelo menos 5 a 10 testes reais.
        </div>
        """,
        unsafe_allow_html=True,
    )