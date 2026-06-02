# experiencia_beta.py

from datetime import datetime
from typing import Any, Dict, List, Optional

import streamlit as st


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v3.8.24 — Experiência Premium do Usuário Beta
# ------------------------------------------------------------
# Este arquivo cria uma experiência simplificada e vendável
# para o usuário comum.
#
# Objetivo:
# - reduzir complexidade visual
# - mostrar o valor do produto rapidamente
# - transformar cálculo em clareza de decisão
# - preparar experiência para beta real e deploy público
# - esconder complexidade técnica do fundador
# ============================================================


VERSAO_EXPERIENCIA_BETA = "3.8.24"


COPY_EXPERIENCIA_BETA = {
    "headline": "Descubra seu preço-teto antes de investir.",
    "subheadline": (
        "Transforme lucro, fluxo de caixa, múltiplos e margem de segurança "
        "em uma decisão clara: comprar, observar ou aguardar."
    ),
    "promessa": "Menos impulso. Mais método. Mais clareza antes de comprar.",
    "disclaimer": (
        "Ferramenta educacional. Não representa recomendação de compra, venda "
        "ou manutenção de investimentos."
    ),
}


PRINCIPIOS_EXPERIENCIA_BETA = [
    {
        "Princípio": "Clareza antes de profundidade",
        "Aplicação": "O usuário precisa entender o resultado em poucos segundos.",
    },
    {
        "Princípio": "Decisão antes de planilha",
        "Aplicação": "Mostrar preço-teto, margem de segurança e leitura prática antes dos detalhes.",
    },
    {
        "Princípio": "Educação sem ruído",
        "Aplicação": "Explicar o raciocínio sem expor motor, logs, fallback ou painéis técnicos.",
    },
    {
        "Princípio": "Valor percebido rápido",
        "Aplicação": "O usuário deve sentir que recebeu uma análise premium logo no primeiro uso.",
    },
]


FLUXO_IDEAL_BETA = [
    {
        "Etapa": "1",
        "Nome": "Entender a proposta",
        "Objetivo": "Saber que o produto ajuda a descobrir preço-teto antes de investir.",
    },
    {
        "Etapa": "2",
        "Nome": "Analisar o ativo",
        "Objetivo": "Ver preço atual, preço justo, preço-teto e margem de segurança.",
    },
    {
        "Etapa": "3",
        "Nome": "Interpretar a decisão",
        "Objetivo": "Entender se o ativo está em zona de compra, neutra ou aguarde.",
    },
    {
        "Etapa": "4",
        "Nome": "Revisar premissas",
        "Objetivo": "Perceber que a conclusão depende dos dados usados.",
    },
    {
        "Etapa": "5",
        "Nome": "Baixar relatório ou enviar feedback",
        "Objetivo": "Gerar valor percebido e coletar aprendizado real.",
    },
]


CHECKLIST_BETA_DECISAO = [
    {
        "Pergunta": "O preço atual está abaixo do preço-teto?",
        "Por que importa": "Ajuda a evitar pagar caro demais.",
    },
    {
        "Pergunta": "A margem de segurança é suficiente?",
        "Por que importa": "Protege contra erro de premissa e otimismo excessivo.",
    },
    {
        "Pergunta": "As premissas são conservadoras?",
        "Por que importa": "Um valuation bonito com premissas ruins engana.",
    },
    {
        "Pergunta": "A tese da empresa ainda faz sentido?",
        "Por que importa": "Preço barato não compensa uma tese quebrada.",
    },
    {
        "Pergunta": "Você compraria mesmo se o mercado caísse amanhã?",
        "Por que importa": "Testa convicção e reduz impulso emocional.",
    },
]


ELEMENTOS_OCULTAR_USUARIO_BETA = [
    "Core Engine",
    "Fallback",
    "Logs técnicos",
    "Saúde do motor",
    "Decisão Core",
    "Promoção Core",
    "CRM Beta",
    "Métricas Fase 3",
    "Arquitetura Fase 4",
    "Painéis internos de fundador",
]


def _safe_str(valor: Any, default: str = "") -> str:
    if valor is None:
        return default

    return str(valor).strip()


def _safe_float(valor: Any, default: float = 0.0) -> float:
    try:
        return float(valor)
    except (TypeError, ValueError):
        return default


def _formatar_moeda(valor: Any, simbolo: str = "R$") -> str:
    numero = _safe_float(valor)

    return f"{simbolo} {numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _formatar_percentual(valor: Any) -> str:
    return f"{_safe_float(valor):.2f}%"


def _normalizar_status(status: Any) -> str:
    texto = _safe_str(status).upper()

    if texto in ["COMPRA", "COMPRAR", "BUY"]:
        return "COMPRA"

    if texto in ["NEUTRO", "NEUTRA", "OBSERVAR"]:
        return "NEUTRO"

    if texto in ["AGUARDE", "AGUARDAR", "WAIT"]:
        return "AGUARDE"

    return texto if texto else "N/D"


def obter_leitura_humana_status(status: str) -> Dict[str, str]:
    status_normalizado = _normalizar_status(status)

    if status_normalizado == "COMPRA":
        return {
            "titulo": "Zona de oportunidade",
            "mensagem": (
                "Pelas premissas atuais, o preço está dentro da zona conservadora do modelo. "
                "Ainda assim, revise a tese, os riscos e a qualidade dos dados antes de decidir."
            ),
            "tom": "positivo",
        }

    if status_normalizado == "NEUTRO":
        return {
            "titulo": "Zona de observação",
            "mensagem": (
                "O ativo não parece caro o suficiente para descartar, mas também não parece barato "
                "o bastante para uma entrada conservadora. A melhor decisão pode ser observar."
            ),
            "tom": "neutro",
        }

    if status_normalizado == "AGUARDE":
        return {
            "titulo": "Zona de paciência",
            "mensagem": (
                "Pelas premissas atuais, o preço não oferece margem de segurança suficiente. "
                "O modelo sugere paciência, revisão das premissas ou espera por preço melhor."
            ),
            "tom": "cautela",
        }

    return {
        "titulo": "Resultado não classificado",
        "mensagem": "Não foi possível classificar a decisão com os dados atuais.",
        "tom": "neutro",
    }


def gerar_snapshot_experiencia_beta(
    resultado_valuation: Dict[str, Any],
    entradas_valuation: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    entradas = entradas_valuation or {}

    simbolo = _safe_str(
        resultado_valuation.get(
            "simbolo_moeda",
            entradas.get("simbolo_moeda", "R$"),
        ),
        "R$",
    )

    empresa = _safe_str(
        resultado_valuation.get(
            "empresa",
            entradas.get("empresa", "Empresa analisada"),
        ),
        "Empresa analisada",
    )

    ticker = _safe_str(
        resultado_valuation.get(
            "ticker",
            entradas.get("ticker", "N/D"),
        ),
        "N/D",
    ).upper()

    status = _normalizar_status(
        resultado_valuation.get(
            "status",
            resultado_valuation.get("status_valuation", "N/D"),
        )
    )

    preco_atual = _safe_float(resultado_valuation.get("preco_atual", entradas.get("preco_atual", 0)))
    preco_teto = _safe_float(resultado_valuation.get("preco_teto", 0))
    preco_justo = _safe_float(
        resultado_valuation.get(
            "preco_justo",
            resultado_valuation.get("preco_justo_combinado", 0),
        )
    )

    margem_ate_preco_teto = _safe_float(resultado_valuation.get("margem_ate_preco_teto", 0))
    potencial_ate_preco_justo = _safe_float(resultado_valuation.get("potencial_ate_preco_justo", 0))

    leitura = obter_leitura_humana_status(status)

    if preco_teto > 0:
        distancia_teto = round(((preco_teto - preco_atual) / preco_teto) * 100, 2)
    else:
        distancia_teto = 0.0

    return {
        "empresa": empresa,
        "ticker": ticker,
        "status": status,
        "leitura_titulo": leitura["titulo"],
        "leitura_mensagem": leitura["mensagem"],
        "leitura_tom": leitura["tom"],
        "simbolo_moeda": simbolo,
        "preco_atual": preco_atual,
        "preco_teto": preco_teto,
        "preco_justo": preco_justo,
        "margem_ate_preco_teto": margem_ate_preco_teto,
        "potencial_ate_preco_justo": potencial_ate_preco_justo,
        "distancia_teto": distancia_teto,
        "margem_seguranca": _safe_float(
            resultado_valuation.get(
                "margem_seguranca",
                entradas.get("margem_seguranca", 0),
            )
        ),
        "modelo_escolhido": _safe_str(
            resultado_valuation.get(
                "modelo_escolhido",
                entradas.get("modelo_escolhido", ""),
            )
        ),
        "tipo_analise": _safe_str(
            resultado_valuation.get(
                "tipo_analise",
                entradas.get("tipo_analise", ""),
            )
        ),
        "data_snapshot": datetime.now().strftime("%d/%m/%Y %H:%M"),
    }


def gerar_tabela_resumo_beta(snapshot: Dict[str, Any]) -> List[Dict[str, str]]:
    simbolo = snapshot.get("simbolo_moeda", "R$")

    return [
        {
            "Indicador": "Empresa",
            "Valor": f"{snapshot.get('empresa')} ({snapshot.get('ticker')})",
        },
        {
            "Indicador": "Status educacional",
            "Valor": str(snapshot.get("status", "")),
        },
        {
            "Indicador": "Preço atual",
            "Valor": _formatar_moeda(snapshot.get("preco_atual", 0), simbolo),
        },
        {
            "Indicador": "Preço-teto",
            "Valor": _formatar_moeda(snapshot.get("preco_teto", 0), simbolo),
        },
        {
            "Indicador": "Preço justo estimado",
            "Valor": _formatar_moeda(snapshot.get("preco_justo", 0), simbolo),
        },
        {
            "Indicador": "Margem até preço-teto",
            "Valor": _formatar_percentual(snapshot.get("margem_ate_preco_teto", 0)),
        },
        {
            "Indicador": "Potencial até preço justo",
            "Valor": _formatar_percentual(snapshot.get("potencial_ate_preco_justo", 0)),
        },
        {
            "Indicador": "Margem de segurança usada",
            "Valor": _formatar_percentual(snapshot.get("margem_seguranca", 0)),
        },
    ]


def gerar_acoes_sugeridas_beta(snapshot: Dict[str, Any]) -> List[Dict[str, str]]:
    status = _normalizar_status(snapshot.get("status", ""))

    if status == "COMPRA":
        return [
            {
                "Ação": "Revisar a tese",
                "Motivo": "Preço bom não compensa empresa ruim ou tese enfraquecida.",
            },
            {
                "Ação": "Conferir premissas",
                "Motivo": "Evite comprar baseado em números otimistas demais.",
            },
            {
                "Ação": "Definir tamanho da posição",
                "Motivo": "Mesmo boas oportunidades precisam de controle de risco.",
            },
        ]

    if status == "NEUTRO":
        return [
            {
                "Ação": "Adicionar à watchlist",
                "Motivo": "O ativo pode ficar interessante em preço melhor.",
            },
            {
                "Ação": "Testar cenário conservador",
                "Motivo": "Veja se a tese ainda funciona com premissas mais duras.",
            },
            {
                "Ação": "Aguardar confirmação",
                "Motivo": "Não há margem clara para decisão agressiva.",
            },
        ]

    if status == "AGUARDE":
        return [
            {
                "Ação": "Não comprar por impulso",
                "Motivo": "O preço atual não oferece margem suficiente pelo modelo.",
            },
            {
                "Ação": "Definir preço de alerta",
                "Motivo": "Acompanhe quando o ativo se aproximar do preço-teto.",
            },
            {
                "Ação": "Reavaliar no futuro",
                "Motivo": "Novos resultados podem mudar o valuation.",
            },
        ]

    return [
        {
            "Ação": "Revisar dados",
            "Motivo": "O resultado não foi classificado corretamente.",
        }
    ]


def gerar_markdown_experiencia_beta(snapshot: Dict[str, Any]) -> str:
    tabela = gerar_tabela_resumo_beta(snapshot)
    acoes = gerar_acoes_sugeridas_beta(snapshot)

    linhas_tabela = "\n".join(
        [f"| {linha['Indicador']} | {linha['Valor']} |" for linha in tabela]
    )

    linhas_acoes = "\n".join(
        [f"| {linha['Ação']} | {linha['Motivo']} |" for linha in acoes]
    )

    return f"""# Análise Beta — Máquina de Preço-Teto

Gerado em: {snapshot.get("data_snapshot")}

## Ativo analisado

**Empresa:** {snapshot.get("empresa")}  
**Ticker:** {snapshot.get("ticker")}  
**Status educacional:** {snapshot.get("status")}  

## Leitura principal

**{snapshot.get("leitura_titulo")}**

{snapshot.get("leitura_mensagem")}

## Resumo

| Indicador | Valor |
|---|---|
{linhas_tabela}

## Ações sugeridas

| Ação | Motivo |
|---|---|
{linhas_acoes}

## Aviso

Esta análise é educacional e depende das premissas usadas. Não representa recomendação de compra, venda ou manutenção de investimentos.
"""


def executar_autoteste_experiencia_beta() -> List[Dict[str, str]]:
    testes = []

    resultado_exemplo = {
        "empresa": "Empresa Teste",
        "ticker": "TST3",
        "status": "COMPRA",
        "preco_atual": 20,
        "preco_teto": 30,
        "preco_justo": 40,
        "margem_ate_preco_teto": 50,
        "potencial_ate_preco_justo": 100,
        "margem_seguranca": 25,
        "simbolo_moeda": "R$",
    }

    snapshot = gerar_snapshot_experiencia_beta(resultado_exemplo)

    testes.append(
        {
            "teste": "snapshot_gerado",
            "status": "OK" if snapshot.get("ticker") == "TST3" else "FALHA",
            "detalhe": f"Ticker: {snapshot.get('ticker')}",
        }
    )

    testes.append(
        {
            "teste": "status_normalizado",
            "status": "OK" if snapshot.get("status") == "COMPRA" else "FALHA",
            "detalhe": f"Status: {snapshot.get('status')}",
        }
    )

    tabela = gerar_tabela_resumo_beta(snapshot)

    testes.append(
        {
            "teste": "tabela_resumo_gerada",
            "status": "OK" if len(tabela) >= 5 else "FALHA",
            "detalhe": f"Linhas: {len(tabela)}",
        }
    )

    acoes = gerar_acoes_sugeridas_beta(snapshot)

    testes.append(
        {
            "teste": "acoes_sugeridas_geradas",
            "status": "OK" if len(acoes) >= 3 else "FALHA",
            "detalhe": f"Ações: {len(acoes)}",
        }
    )

    markdown = gerar_markdown_experiencia_beta(snapshot)

    testes.append(
        {
            "teste": "markdown_beta_gerado",
            "status": "OK" if "# Análise Beta" in markdown else "FALHA",
            "detalhe": "Relatório markdown criado.",
        }
    )

    return testes


def _injetar_css_experiencia_beta() -> None:
    st.markdown(
        """
        <style>
            .xb-hero {
                padding: 2rem 2rem;
                border-radius: 32px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    radial-gradient(circle at top left, rgba(214, 181, 109, 0.24), transparent 30%),
                    radial-gradient(circle at bottom right, rgba(36, 128, 91, 0.26), transparent 34%),
                    linear-gradient(135deg, rgba(8, 15, 27, 0.99), rgba(5, 9, 18, 0.99));
                box-shadow: 0 18px 55px rgba(0, 0, 0, 0.34);
                margin-bottom: 1.2rem;
            }

            .xb-eyebrow {
                color: #d6b56d;
                font-size: 0.78rem;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.35rem;
            }

            .xb-title {
                color: #f4f7fb;
                font-size: 2.2rem;
                font-weight: 900;
                margin-bottom: 0.55rem;
                line-height: 1.12;
            }

            .xb-subtitle {
                color: rgba(244, 247, 251, 0.76);
                font-size: 1rem;
                line-height: 1.62;
                max-width: 1050px;
            }

            .xb-card {
                padding: 1.12rem 1.18rem;
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.035);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.18);
                height: 100%;
            }

            .xb-card-label {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .xb-card-value {
                color: #f4f7fb;
                font-size: 1.22rem;
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .xb-card-note {
                color: rgba(244, 247, 251, 0.68);
                font-size: 0.87rem;
                line-height: 1.47;
            }

            .xb-highlight {
                padding: 0.95rem 1rem;
                border-radius: 16px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.92rem;
                line-height: 1.55;
                margin-bottom: 0.7rem;
            }

            .xb-disclaimer {
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
        <div class="xb-card">
            <div class="xb-card-label">{label}</div>
            <div class="xb-card-value">{value}</div>
            <div class="xb-card-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _renderizar_alerta_status(snapshot: Dict[str, Any]) -> None:
    tom = snapshot.get("leitura_tom", "neutro")
    mensagem = f"**{snapshot.get('leitura_titulo')}** — {snapshot.get('leitura_mensagem')}"

    if tom == "positivo":
        st.success(mensagem)
    elif tom == "cautela":
        st.error(mensagem)
    else:
        st.warning(mensagem)


def renderizar_experiencia_usuario_beta(
    resultado_valuation: Dict[str, Any],
    entradas_valuation: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Renderiza a experiência premium simplificada para o usuário beta.
    """
    _injetar_css_experiencia_beta()

    snapshot = gerar_snapshot_experiencia_beta(
        resultado_valuation=resultado_valuation,
        entradas_valuation=entradas_valuation,
    )

    simbolo = snapshot.get("simbolo_moeda", "R$")

    st.markdown(
        f"""
        <div class="xb-hero">
            <div class="xb-eyebrow">v{VERSAO_EXPERIENCIA_BETA} — Experiência beta</div>
            <div class="xb-title">{COPY_EXPERIENCIA_BETA["headline"]}</div>
            <div class="xb-subtitle">
                {COPY_EXPERIENCIA_BETA["subheadline"]}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="xb-highlight">
            {COPY_EXPERIENCIA_BETA["promessa"]}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(f"### Análise rápida: {snapshot['empresa']} ({snapshot['ticker']})")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        _card(
            "Preço atual",
            _formatar_moeda(snapshot.get("preco_atual", 0), simbolo),
            "Preço usado na análise.",
        )

    with col_2:
        _card(
            "Preço-teto",
            _formatar_moeda(snapshot.get("preco_teto", 0), simbolo),
            "Preço máximo conservador pelo modelo.",
        )

    with col_3:
        _card(
            "Preço justo",
            _formatar_moeda(snapshot.get("preco_justo", 0), simbolo),
            "Estimativa antes da margem de segurança.",
        )

    with col_4:
        _card(
            "Status",
            str(snapshot.get("status", "")),
            "Leitura educacional do modelo.",
        )

    st.divider()

    _renderizar_alerta_status(snapshot)

    st.markdown("### Mapa simples da decisão")

    valor_maximo = max(
        _safe_float(snapshot.get("preco_atual", 0)),
        _safe_float(snapshot.get("preco_teto", 0)),
        _safe_float(snapshot.get("preco_justo", 0)),
        1,
    )

    progresso_preco_atual = min(_safe_float(snapshot.get("preco_atual", 0)) / valor_maximo, 1)
    progresso_preco_teto = min(_safe_float(snapshot.get("preco_teto", 0)) / valor_maximo, 1)
    progresso_preco_justo = min(_safe_float(snapshot.get("preco_justo", 0)) / valor_maximo, 1)

    st.caption("Preço atual")
    st.progress(progresso_preco_atual)

    st.caption("Preço-teto")
    st.progress(progresso_preco_teto)

    st.caption("Preço justo")
    st.progress(progresso_preco_justo)

    col_m1, col_m2, col_m3 = st.columns(3)

    with col_m1:
        st.metric(
            "Margem até preço-teto",
            _formatar_percentual(snapshot.get("margem_ate_preco_teto", 0)),
        )

    with col_m2:
        st.metric(
            "Potencial até preço justo",
            _formatar_percentual(snapshot.get("potencial_ate_preco_justo", 0)),
        )

    with col_m3:
        st.metric(
            "Margem de segurança usada",
            _formatar_percentual(snapshot.get("margem_seguranca", 0)),
        )

    st.divider()

    st.markdown("### Próximas ações sugeridas")

    st.dataframe(
        gerar_acoes_sugeridas_beta(snapshot),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Checklist antes de decidir")

    st.dataframe(
        CHECKLIST_BETA_DECISAO,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Resumo da análise")

    st.dataframe(
        gerar_tabela_resumo_beta(snapshot),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Relatório beta")

    st.download_button(
        label="Baixar análise beta (.md)",
        data=gerar_markdown_experiencia_beta(snapshot),
        file_name=f"analise_beta_{snapshot['ticker'].lower()}.md",
        mime="text/markdown",
        key="download_experiencia_beta",
    )

    st.markdown(
        f"""
        <div class="xb-disclaimer">
            <strong>Aviso:</strong> {COPY_EXPERIENCIA_BETA["disclaimer"]}
        </div>
        """,
        unsafe_allow_html=True,
    )