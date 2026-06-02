# painel_core_engine.py

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

import streamlit as st

from core_valuation import (
    VERSAO_CORE_VALUATION,
    calcular_core_valuation_por_payload,
    executar_autoteste_core,
    formatar_moeda_core,
    formatar_percentual_core,
    gerar_contrato_api_core,
    gerar_markdown_especificacao_core,
    gerar_payload_exemplo_core,
    gerar_regras_core,
)


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v3.8.1 — Painel Interno do Core Engine
# ------------------------------------------------------------
# Esta tela audita o núcleo puro de valuation criado na v3.8.
#
# Objetivo:
# - testar o Core Engine dentro do app
# - validar payloads estilo API
# - visualizar contrato futuro da API
# - revisar regras do motor
# - baixar especificação técnica
# - preparar integração futura com FastAPI e Next.js
# ============================================================


def _injetar_css_core_engine() -> None:
    st.markdown(
        """
        <style>
            .ce-hero {
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

            .ce-eyebrow {
                color: #d6b56d;
                font-size: 0.78rem;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.35rem;
            }

            .ce-title {
                color: #f4f7fb;
                font-size: 2.1rem;
                font-weight: 900;
                margin-bottom: 0.45rem;
                line-height: 1.14;
            }

            .ce-subtitle {
                color: rgba(244, 247, 251, 0.76);
                font-size: 1rem;
                line-height: 1.62;
                max-width: 1080px;
            }

            .ce-card {
                padding: 1.1rem 1.15rem;
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.035);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.18);
                height: 100%;
            }

            .ce-card-label {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .ce-card-value {
                color: #f4f7fb;
                font-size: 1.22rem;
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .ce-card-note {
                color: rgba(244, 247, 251, 0.68);
                font-size: 0.87rem;
                line-height: 1.47;
            }

            .ce-highlight {
                padding: 0.95rem 1rem;
                border-radius: 16px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.92rem;
                line-height: 1.55;
                margin-bottom: 0.7rem;
            }

            .ce-disclaimer {
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
        <div class="ce-card">
            <div class="ce-card-label">{label}</div>
            <div class="ce-card-value">{value}</div>
            <div class="ce-card-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _todos_testes_ok(testes: List[Dict[str, Any]]) -> bool:
    return all(teste.get("status") == "OK" for teste in testes)


def _formatar_resultado_core(resultado: Dict[str, Any]) -> List[Dict[str, str]]:
    moeda = resultado.get("moeda", "R$")

    return [
        {
            "Indicador": "Empresa",
            "Valor": str(resultado.get("empresa", "")),
            "Leitura": "Nome analisado pelo Core Engine.",
        },
        {
            "Indicador": "Ticker",
            "Valor": str(resultado.get("ticker", "")),
            "Leitura": "Código do ativo.",
        },
        {
            "Indicador": "EPS normalizado",
            "Valor": formatar_moeda_core(float(resultado.get("eps_normalizado", 0)), moeda),
            "Leitura": "Lucro sustentável por ação.",
        },
        {
            "Indicador": "FCF por ação",
            "Valor": formatar_moeda_core(float(resultado.get("fcf_por_acao", 0)), moeda),
            "Leitura": "Fluxo de caixa livre por ação.",
        },
        {
            "Indicador": "Preço justo por EPS",
            "Valor": formatar_moeda_core(float(resultado.get("preco_justo_eps", 0)), moeda),
            "Leitura": "Valuation baseado em lucro.",
        },
        {
            "Indicador": "Preço justo por FCF",
            "Valor": formatar_moeda_core(float(resultado.get("preco_justo_fcf", 0)), moeda),
            "Leitura": "Valuation baseado em caixa.",
        },
        {
            "Indicador": "Preço justo combinado",
            "Valor": formatar_moeda_core(float(resultado.get("preco_justo_combinado", 0)), moeda),
            "Leitura": "Combinação ponderada de EPS e FCF.",
        },
        {
            "Indicador": "Preço-teto",
            "Valor": formatar_moeda_core(float(resultado.get("preco_teto", 0)), moeda),
            "Leitura": "Preço justo com margem de segurança.",
        },
        {
            "Indicador": "Preço atual",
            "Valor": formatar_moeda_core(float(resultado.get("preco_atual", 0)), moeda),
            "Leitura": "Preço informado no payload.",
        },
        {
            "Indicador": "Margem até preço-teto",
            "Valor": formatar_percentual_core(float(resultado.get("margem_ate_preco_teto", 0))),
            "Leitura": "Distância entre preço atual e preço-teto.",
        },
        {
            "Indicador": "Potencial até preço justo",
            "Valor": formatar_percentual_core(float(resultado.get("potencial_ate_preco_justo", 0))),
            "Leitura": "Distância entre preço atual e preço justo.",
        },
        {
            "Indicador": "Status",
            "Valor": str(resultado.get("status", "")),
            "Leitura": "Classificação educacional do motor.",
        },
    ]


def _gerar_markdown_auditoria_core(
    testes: List[Dict[str, Any]],
    contrato: Dict[str, Any],
    resultado_payload: Optional[Dict[str, Any]],
) -> str:
    linhas_testes = "\n".join(
        [
            f"| {teste.get('teste', '')} | {teste.get('status', '')} | {teste.get('detalhe', '')} |"
            for teste in testes
        ]
    )

    regras = gerar_regras_core()

    linhas_regras = "\n".join(
        [
            f"| {regra.get('Regra', '')} | {regra.get('Fórmula', '')} | {regra.get('Uso', '')} |"
            for regra in regras
        ]
    )

    bloco_resultado = "Nenhum payload manual foi calculado nesta auditoria."

    if resultado_payload is not None:
        bloco_resultado = json.dumps(
            resultado_payload,
            indent=2,
            ensure_ascii=False,
        )

    payload_exemplo = json.dumps(
        contrato.get("entrada_esperada", {}),
        indent=2,
        ensure_ascii=False,
    )

    return f"""# Auditoria do Core Engine de Valuation

Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Versão

Core Valuation: {VERSAO_CORE_VALUATION}

## Autotestes

| Teste | Status | Detalhe |
|---|---|---|
{linhas_testes}

## Contrato futuro da API

**Endpoint futuro:** {contrato.get("endpoint_futuro", "")}

**Descrição:** {contrato.get("descricao", "")}

## Payload de exemplo

```json
{payload_exemplo}
```

## Campos principais de saída

{", ".join(contrato.get("saida_principal", []))}

## Status possíveis

{", ".join(contrato.get("status_possiveis", []))}

## Regras do motor

| Regra | Fórmula | Uso |
|---|---|---|
{linhas_regras}

## Último resultado de payload manual

```json
{bloco_resultado}
```

## Princípio

O Core Engine deve continuar independente de interface.
Ele não deve importar Streamlit, FastAPI, banco de dados ou bibliotecas de tela.
"""


def renderizar_painel_core_engine() -> None:
    """
    Renderiza o painel interno de auditoria do Core Engine.
    """
    _injetar_css_core_engine()

    st.markdown(
        """
        <div class="ce-hero">
            <div class="ce-eyebrow">v3.8.1 — Auditoria interna</div>
            <div class="ce-title">Core Engine de Valuation</div>
            <div class="ce-subtitle">
                Audite o núcleo puro de cálculo da Máquina de Preço-Teto.
                Este motor é independente do Streamlit e prepara o produto para API, testes,
                banco de dados e futura aplicação profissional.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="ce-highlight">
            O Core Engine é o coração do produto. Ele deve calcular corretamente sem depender da interface.
            Primeiro auditamos. Depois integramos ao app principal com segurança.
        </div>
        """,
        unsafe_allow_html=True,
    )

    testes = executar_autoteste_core()
    contrato = gerar_contrato_api_core()

    st.session_state["resultado_core_engine"] = {
        "versao_core": VERSAO_CORE_VALUATION,
        "autotestes_ok": _todos_testes_ok(testes),
        "quantidade_testes": len(testes),
        "endpoint_futuro": contrato.get("endpoint_futuro", ""),
    }

    st.markdown("### Diagnóstico do Core Engine")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Versão Core", VERSAO_CORE_VALUATION)

    with col_2:
        st.metric("Autotestes", len(testes))

    with col_3:
        st.metric("Status geral", "OK" if _todos_testes_ok(testes) else "FALHA")

    with col_4:
        st.metric("Endpoint futuro", contrato.get("endpoint_futuro", "N/D"))

    if _todos_testes_ok(testes):
        st.success("Core Engine passou nos autotestes básicos.")
    else:
        st.error("Core Engine apresentou falha em pelo menos um autoteste.")

    st.divider()

    st.markdown("### Autotestes do motor")

    st.dataframe(
        testes,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Testar payload manual")

    payload_exemplo = gerar_payload_exemplo_core()
    payload_texto_padrao = json.dumps(
        payload_exemplo,
        indent=2,
        ensure_ascii=False,
    )

    if "ultimo_resultado_payload_core" not in st.session_state:
        st.session_state["ultimo_resultado_payload_core"] = None

    with st.form("form_payload_core_engine"):
        payload_texto = st.text_area(
            "Payload em JSON",
            value=payload_texto_padrao,
            height=320,
            help="Edite as premissas abaixo para testar o Core Engine como se fosse uma futura chamada de API.",
            key="ce_payload_texto",
        )

        calcular_payload = st.form_submit_button("Calcular payload no Core Engine")

        if calcular_payload:
            try:
                payload = json.loads(payload_texto)
                resultado_payload = calcular_core_valuation_por_payload(payload)
                st.session_state["ultimo_resultado_payload_core"] = resultado_payload
                st.success("Payload calculado com sucesso pelo Core Engine.")
            except json.JSONDecodeError as erro:
                st.session_state["ultimo_resultado_payload_core"] = None
                st.error(f"JSON inválido: {erro}")
            except ValueError as erro:
                st.session_state["ultimo_resultado_payload_core"] = None
                st.error(str(erro))
            except Exception as erro:
                st.session_state["ultimo_resultado_payload_core"] = None
                st.error(f"Erro inesperado ao calcular payload: {erro}")

    resultado_payload_atual = st.session_state.get("ultimo_resultado_payload_core")

    if resultado_payload_atual is not None:
        st.markdown("### Resultado do payload manual")

        col_r1, col_r2, col_r3, col_r4 = st.columns(4)

        moeda = resultado_payload_atual.get("moeda", "R$")

        with col_r1:
            _card(
                "Preço justo",
                formatar_moeda_core(
                    float(resultado_payload_atual.get("preco_justo_combinado", 0)),
                    moeda,
                ),
                "Valor justo combinado.",
            )

        with col_r2:
            _card(
                "Preço-teto",
                formatar_moeda_core(
                    float(resultado_payload_atual.get("preco_teto", 0)),
                    moeda,
                ),
                "Com margem de segurança.",
            )

        with col_r3:
            _card(
                "Status",
                str(resultado_payload_atual.get("status", "")),
                "Classificação educacional.",
            )

        with col_r4:
            _card(
                "Margem até teto",
                formatar_percentual_core(
                    float(resultado_payload_atual.get("margem_ate_preco_teto", 0))
                ),
                "Distância até preço-teto.",
            )

        st.info(str(resultado_payload_atual.get("explicacao_status", "")))

        st.dataframe(
            _formatar_resultado_core(resultado_payload_atual),
            use_container_width=True,
            hide_index=True,
        )

        with st.expander("Ver resultado bruto em JSON"):
            st.json(resultado_payload_atual)

    st.divider()

    st.markdown("### Contrato futuro da API")

    col_c1, col_c2 = st.columns(2)

    with col_c1:
        st.markdown("#### Endpoint")
        st.code(contrato.get("endpoint_futuro", ""), language="text")

        st.markdown("#### Status possíveis")
        st.write(", ".join(contrato.get("status_possiveis", [])))

    with col_c2:
        st.markdown("#### Descrição")
        st.write(contrato.get("descricao", ""))

        st.markdown("#### Campos principais de saída")
        st.write(", ".join(contrato.get("saida_principal", [])))

    st.markdown("#### Payload de exemplo")
    st.json(contrato.get("entrada_esperada", {}))

    st.divider()

    st.markdown("### Regras do motor")

    st.dataframe(
        gerar_regras_core(),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Downloads técnicos")

    col_d1, col_d2 = st.columns(2)

    with col_d1:
        st.download_button(
            label="Baixar especificação do Core Engine (.md)",
            data=gerar_markdown_especificacao_core(),
            file_name="especificacao_core_engine.md",
            mime="text/markdown",
            key="download_especificacao_core_engine",
        )

    with col_d2:
        st.download_button(
            label="Baixar auditoria do Core Engine (.md)",
            data=_gerar_markdown_auditoria_core(
                testes=testes,
                contrato=contrato,
                resultado_payload=resultado_payload_atual,
            ),
            file_name="auditoria_core_engine.md",
            mime="text/markdown",
            key="download_auditoria_core_engine",
        )

    st.markdown(
        """
        <div class="ce-disclaimer">
            <strong>Regra técnica:</strong> este painel não substitui o motor antigo do app ainda.
            Ele audita o novo núcleo. A troca definitiva só deve acontecer depois de validarmos
            compatibilidade, resultados e testes.
        </div>
        """,
        unsafe_allow_html=True,
    )