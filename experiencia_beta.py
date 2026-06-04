# experiencia_beta.py

from datetime import datetime
from typing import Any, Dict, List, Optional

import streamlit as st

from explicabilidade_valoris import renderizar_explicabilidade_valoris
from lista_espera_beta import renderizar_lista_espera_valoris


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v3.8.39 — Experiência Beta com Lista de Espera
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


VERSAO_EXPERIENCIA_BETA = "3.8.39"


COPY_EXPERIENCIA_BETA = {
    "headline": "Audite sua decisão antes de investir.",
    "subheadline": (
        "Valuation, margem de segurança e riscos fundamentais em uma leitura clara, "
        "didática e preparada para diferentes níveis de investidor."
    ),
    "promessa": "A Valoris não entrega só um número: ela mostra o que sustenta, enfraquece ou limita a decisão.",
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

    return f"""# Análise Beta — Valoris

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
                padding: clamp(1.25rem, 3vw, 2rem);
                border-radius: 30px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    radial-gradient(circle at top left, rgba(214, 181, 109, 0.20), transparent 30%),
                    radial-gradient(circle at bottom right, rgba(36, 128, 91, 0.22), transparent 34%),
                    linear-gradient(135deg, rgba(8, 15, 27, 0.99), rgba(5, 9, 18, 0.99));
                box-shadow: 0 18px 55px rgba(0, 0, 0, 0.30);
                margin-bottom: 1rem;
            }

            .xb-eyebrow {
                color: #d6b56d;
                font-size: 0.74rem;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.38rem;
            }

            .xb-title {
                color: #f4f7fb;
                font-size: clamp(1.75rem, 5vw, 2.45rem);
                font-weight: 920;
                margin-bottom: 0.55rem;
                line-height: 1.08;
                letter-spacing: -0.045em;
            }

            .xb-subtitle {
                color: rgba(244, 247, 251, 0.76);
                font-size: clamp(0.94rem, 2.2vw, 1.03rem);
                line-height: 1.56;
                max-width: 980px;
            }

            .xb-card {
                padding: 1rem 1.05rem;
                border-radius: 21px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background:
                    radial-gradient(circle at top right, rgba(214, 181, 109, 0.07), transparent 30%),
                    rgba(255, 255, 255, 0.034);
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.17);
                height: 100%;
            }

            .xb-card-label {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.72rem;
                text-transform: uppercase;
                letter-spacing: 0.085em;
                font-weight: 820;
                margin-bottom: 0.32rem;
            }

            .xb-card-value {
                color: #f4f7fb;
                font-size: clamp(1.04rem, 2.2vw, 1.28rem);
                font-weight: 870;
                margin-bottom: 0.25rem;
                letter-spacing: -0.025em;
            }

            .xb-card-note {
                color: rgba(244, 247, 251, 0.66);
                font-size: 0.84rem;
                line-height: 1.44;
            }

            .xb-highlight {
                padding: 0.88rem 0.95rem;
                border-radius: 18px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.90rem;
                line-height: 1.50;
                margin-bottom: 0.65rem;
            }

            .xb-decision-strip {
                padding: 1.05rem 1.1rem;
                border-radius: 24px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(30, 41, 59, 0.64));
                box-shadow: 0 14px 42px rgba(0, 0, 0, 0.24);
                margin: 0.85rem 0 0.95rem 0;
            }

            .xb-decision-kicker {
                color: #d6b56d;
                font-size: 0.72rem;
                letter-spacing: 0.12em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.32rem;
            }

            .xb-decision-title {
                color: #f4f7fb;
                font-size: clamp(1.22rem, 3.4vw, 1.70rem);
                font-weight: 900;
                line-height: 1.15;
                margin-bottom: 0.36rem;
            }

            .xb-decision-text {
                color: rgba(244, 247, 251, 0.72);
                font-size: 0.93rem;
                line-height: 1.50;
            }

            .xb-mini-row {
                display: grid;
                grid-template-columns: repeat(4, minmax(0, 1fr));
                gap: 0.75rem;
                margin: 0.85rem 0 0.95rem 0;
            }

            .xb-section-label {
                color: rgba(244, 247, 251, 0.62);
                font-size: 0.76rem;
                letter-spacing: 0.10em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .xb-disclaimer {
                padding: 0.9rem 0.95rem;
                border-radius: 16px;
                background: rgba(74, 144, 226, 0.08);
                border: 1px solid rgba(74, 144, 226, 0.18);
                color: rgba(244, 247, 251, 0.78);
                font-size: 0.88rem;
                line-height: 1.50;
                margin-top: 1rem;
            }

            @media (max-width: 900px) {
                .xb-mini-row {
                    grid-template-columns: repeat(2, minmax(0, 1fr));
                    gap: 0.65rem;
                }

                .xb-hero {
                    border-radius: 24px;
                    margin-bottom: 0.85rem;
                }

                .xb-card {
                    border-radius: 18px;
                    padding: 0.92rem 0.95rem;
                }
            }

            @media (max-width: 520px) {
                .xb-mini-row {
                    grid-template-columns: 1fr;
                    gap: 0.56rem;
                }

                .xb-hero {
                    padding: 1.12rem 1rem;
                    border-radius: 22px;
                }

                .xb-highlight,
                .xb-decision-strip,
                .xb-disclaimer {
                    border-radius: 16px;
                }

                .xb-decision-strip {
                    padding: 0.95rem;
                }

                .xb-card-note {
                    font-size: 0.81rem;
                }
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


def _obter_frase_decisao(snapshot: Dict[str, Any]) -> str:
    status = _normalizar_status(snapshot.get("status", ""))

    if status == "COMPRA":
        return (
            "Existe margem para continuar a análise, mas a Valoris ainda recomenda revisar tese, "
            "qualidade dos dados e riscos fundamentais antes de qualquer decisão."
        )

    if status == "NEUTRO":
        return (
            "O ativo merece acompanhamento. A decisão mais racional pode ser observar, testar premissas "
            "mais conservadoras e esperar uma assimetria melhor."
        )

    if status == "AGUARDE":
        return (
            "O preço atual exige paciência. A Valoris sugere evitar impulso, definir um preço de alerta "
            "e reavaliar quando houver novos dados ou melhor margem."
        )

    return "Revise os dados antes de interpretar a análise."


def _renderizar_decision_strip(snapshot: Dict[str, Any]) -> None:
    st.markdown(
        f"""
        <div class="xb-decision-strip">
            <div class="xb-decision-kicker">Leitura principal da Valoris</div>
            <div class="xb-decision-title">{snapshot.get("leitura_titulo", "Resultado")}</div>
            <div class="xb-decision-text">{_obter_frase_decisao(snapshot)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _renderizar_cards_resumo_mobile_first(snapshot: Dict[str, Any], simbolo: str) -> None:
    st.markdown(
        f"""
        <div class="xb-mini-row">
            <div class="xb-card">
                <div class="xb-card-label">Preço atual</div>
                <div class="xb-card-value">{_formatar_moeda(snapshot.get("preco_atual", 0), simbolo)}</div>
                <div class="xb-card-note">Referência usada contra teto e valor justo.</div>
            </div>
            <div class="xb-card">
                <div class="xb-card-label">Preço-teto</div>
                <div class="xb-card-value">{_formatar_moeda(snapshot.get("preco_teto", 0), simbolo)}</div>
                <div class="xb-card-note">Entrada conservadora com margem.</div>
            </div>
            <div class="xb-card">
                <div class="xb-card-label">Preço justo</div>
                <div class="xb-card-value">{_formatar_moeda(snapshot.get("preco_justo", 0), simbolo)}</div>
                <div class="xb-card-note">Valor estimado antes do desconto.</div>
            </div>
            <div class="xb-card">
                <div class="xb-card-label">Zona</div>
                <div class="xb-card-value">{snapshot.get("leitura_titulo", "")}</div>
                <div class="xb-card-note">Tradução humana do status.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )



def _normalizar_camada_visualizacao(camada: Any) -> str:
    texto = _safe_str(camada, "Intermediário").lower()

    if "leigo" in texto or "simples" in texto or "iniciante" in texto:
        return "Leigo"

    if "avanç" in texto or "avanc" in texto or "pro" in texto:
        return "Avançado"

    return "Intermediário"


def _obter_descricao_camada(camada: str) -> Dict[str, str]:
    camada_normalizada = _normalizar_camada_visualizacao(camada)

    descricoes = {
        "Leigo": {
            "titulo": "Leitura simples",
            "descricao": (
                "Mostra a resposta principal em linguagem humana, sem excesso de termos técnicos. "
                "Ideal para entender rapidamente se o ativo está em zona de oportunidade, atenção ou paciência."
            ),
        },
        "Intermediário": {
            "titulo": "Análise guiada",
            "descricao": (
                "Mostra a leitura principal, o mapa da decisão, próximos passos e o Auditor Valoris. "
                "Ideal para quem quer entender o raciocínio sem abrir todas as premissas."
            ),
        },
        "Avançado": {
            "titulo": "Premissas abertas",
            "descricao": (
                "Mostra a análise completa, incluindo premissas, pesos, múltiplos, checklist e relatório. "
                "Ideal para quem quer revisar a estrutura do modelo e questionar os inputs."
            ),
        },
    }

    return descricoes[camada_normalizada]


def _renderizar_card_texto(label: str, valor: str, nota: str = "") -> None:
    st.markdown(
        f"""
        <div class="xb-card">
            <div class="xb-card-label">{label}</div>
            <div class="xb-card-value">{valor}</div>
            <div class="xb-card-note">{nota}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _renderizar_lista_acoes(snapshot: Dict[str, Any]) -> None:
    st.markdown("### Próximas ações sugeridas")

    for indice, acao in enumerate(gerar_acoes_sugeridas_beta(snapshot), start=1):
        with st.container(border=True):
            st.markdown(f"**{indice}. {acao['Ação']}**")
            st.caption(acao["Motivo"])


def _renderizar_checklist_beta() -> None:
    st.markdown("### Checklist antes de decidir")

    for item in CHECKLIST_BETA_DECISAO:
        with st.container(border=True):
            st.markdown(f"**{item['Pergunta']}**")
            st.caption(item["Por que importa"])


def _renderizar_resumo_beta(snapshot: Dict[str, Any]) -> None:
    st.markdown("### Resumo da análise")

    for item in gerar_tabela_resumo_beta(snapshot):
        with st.container(border=True):
            col_nome, col_valor = st.columns([1, 2])

            with col_nome:
                st.caption(item["Indicador"])

            with col_valor:
                st.markdown(f"**{item['Valor']}**")


def _renderizar_mapa_simples_decisao(snapshot: Dict[str, Any]) -> None:
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


def _renderizar_relatorio_beta(snapshot: Dict[str, Any]) -> None:
    st.markdown("### Relatório beta")

    st.download_button(
        label="Baixar análise beta (.md)",
        data=gerar_markdown_experiencia_beta(snapshot),
        file_name=f"analise_beta_{snapshot['ticker'].lower()}.md",
        mime="text/markdown",
        key="download_experiencia_beta",
    )


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
            <div class="xb-eyebrow">Valoris • v{VERSAO_EXPERIENCIA_BETA}</div>
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

    st.markdown(f"### {snapshot['empresa']} ({snapshot['ticker']})")

    _renderizar_decision_strip(snapshot)

    _renderizar_cards_resumo_mobile_first(snapshot, simbolo)

    st.divider()

    st.markdown("### Como você quer visualizar esta análise?")

    camada_visualizacao = st.radio(
        "Escolha a profundidade da análise",
        ["Leigo", "Intermediário", "Avançado"],
        index=1,
        horizontal=True,
        key="camada_visualizacao_valoris_beta",
        help=(
            "Leigo simplifica a leitura. Intermediário mostra o auditor e os próximos passos. "
            "Avançado abre premissas e revisão técnica."
        ),
    )

    camada_visualizacao = _normalizar_camada_visualizacao(camada_visualizacao)
    descricao_camada = _obter_descricao_camada(camada_visualizacao)

    st.info(f"**{descricao_camada['titulo']}** — {descricao_camada['descricao']}")

    st.divider()

    if camada_visualizacao == "Leigo":
        _renderizar_lista_acoes(snapshot)

        st.divider()

        renderizar_explicabilidade_valoris(
            resultado_valuation=resultado_valuation,
            entradas_valuation=entradas_valuation,
            snapshot=snapshot,
            camada_visualizacao="Leigo",
        )

    elif camada_visualizacao == "Intermediário":
        _renderizar_mapa_simples_decisao(snapshot)

        st.divider()

        _renderizar_lista_acoes(snapshot)

        st.divider()

        renderizar_explicabilidade_valoris(
            resultado_valuation=resultado_valuation,
            entradas_valuation=entradas_valuation,
            snapshot=snapshot,
            camada_visualizacao="Intermediário",
        )

        st.divider()

        with st.expander("Checklist antes de decidir", expanded=False):
            _renderizar_checklist_beta()

    else:
        _renderizar_mapa_simples_decisao(snapshot)

        st.divider()

        renderizar_explicabilidade_valoris(
            resultado_valuation=resultado_valuation,
            entradas_valuation=entradas_valuation,
            snapshot=snapshot,
            camada_visualizacao="Avançado",
        )

        st.divider()

        _renderizar_lista_acoes(snapshot)

        st.divider()

        with st.expander("Checklist antes de decidir", expanded=True):
            _renderizar_checklist_beta()

        st.divider()

        with st.expander("Resumo técnico da análise", expanded=False):
            _renderizar_resumo_beta(snapshot)

        st.divider()

        _renderizar_relatorio_beta(snapshot)

    st.divider()

    renderizar_lista_espera_valoris(modo_admin=False, chave_contexto="experiencia_beta")

    st.markdown(
        f"""
        <div class="xb-disclaimer">
            <strong>Aviso:</strong> {COPY_EXPERIENCIA_BETA["disclaimer"]}
        </div>
        """,
        unsafe_allow_html=True,
    )
