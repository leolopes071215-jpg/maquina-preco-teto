# inicio.py

import streamlit as st
from typing import Any, Dict, List, Optional


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v1.22 — Início Premium e Jornada Guiada
# ------------------------------------------------------------
# Esta tela organiza a primeira experiência do usuário.
# O objetivo é transformar o app em uma jornada clara:
# preencher premissas, rodar valuation, revisar tese, auditar erros,
# abrir painel executivo, baixar relatório e salvar na watchlist.
# ============================================================


def _safe_get_dict(key: str) -> Dict[str, Any]:
    valor = st.session_state.get(key)

    if isinstance(valor, dict):
        return valor

    return {}


def _normalizar_status(status: Any) -> str:
    if status is None:
        return "N/D"

    texto = str(status).upper().strip()

    if "COMPRA" in texto:
        return "COMPRA"
    if "NEUTRO" in texto:
        return "NEUTRO"
    if "AGUARDE" in texto:
        return "AGUARDE"

    return texto or "N/D"


def _fmt_moeda(valor: Optional[Any], simbolo: str = "R$") -> str:
    if valor is None or valor == "":
        return "N/D"

    try:
        numero = float(valor)
        return f"{simbolo} {numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return "N/D"


def _fmt_score(valor: Optional[Any]) -> str:
    if valor is None or valor == "":
        return "N/D"

    try:
        return f"{int(round(float(valor)))}/100"
    except (TypeError, ValueError):
        return "N/D"


def _extrair_contexto(
    resultado_valuation: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    dados = {}

    if isinstance(st.session_state.get("resultado_valuation"), dict):
        dados.update(st.session_state["resultado_valuation"])

    if isinstance(resultado_valuation, dict):
        dados.update(resultado_valuation)

    return {
        "empresa": dados.get("empresa", "Empresa analisada"),
        "ticker": dados.get("ticker", "N/D"),
        "status": _normalizar_status(dados.get("status_valuation", dados.get("status", "N/D"))),
        "preco_atual": dados.get("preco_atual"),
        "preco_teto": dados.get("preco_teto"),
        "preco_justo": dados.get("preco_justo", dados.get("preco_justo_combinado")),
        "simbolo_moeda": dados.get("simbolo_moeda", "R$"),
    }


def _modulo_preenchido(chave: str) -> bool:
    valor = st.session_state.get(chave)

    if isinstance(valor, dict):
        return len(valor) > 0

    if isinstance(valor, list):
        return len(valor) > 0

    return valor is not None


def _gerar_status_jornada() -> List[Dict[str, Any]]:
    return [
        {
            "etapa": "1",
            "titulo": "Premissas",
            "descricao": "Preencha os dados financeiros na barra lateral.",
            "status": _modulo_preenchido("entradas_valuation"),
            "acao": "Use a sidebar para revisar empresa, lucro, FCF, ações, preço atual e múltiplos.",
        },
        {
            "etapa": "2",
            "titulo": "Valuation",
            "descricao": "Veja preço justo, preço-teto e status educacional.",
            "status": _modulo_preenchido("resultado_valuation"),
            "acao": "Abra a aba Valuation para conferir o resultado do modelo.",
        },
        {
            "etapa": "3",
            "titulo": "Tese",
            "descricao": "Avalie a qualidade da tese e seus riscos.",
            "status": _modulo_preenchido("resultado_conviccao_tese"),
            "acao": "Abra Tese & Convicção e atribua notas qualitativas.",
        },
        {
            "etapa": "4",
            "titulo": "Checklist",
            "descricao": "Audite erros, vieses e premissas frágeis.",
            "status": _modulo_preenchido("resultado_checklist_erros"),
            "acao": "Abra Checklist de Erros e marque os riscos presentes na análise.",
        },
        {
            "etapa": "5",
            "titulo": "Painel",
            "descricao": "Consolide os principais sinais da análise.",
            "status": _modulo_preenchido("resultado_painel_multiativos"),
            "acao": "Abra Painel Executivo para ver a leitura integrada.",
        },
        {
            "etapa": "6",
            "titulo": "Relatório",
            "descricao": "Baixe um relatório premium em Markdown.",
            "status": False,
            "acao": "Abra Painel Executivo e clique em Baixar relatório premium multiativos.",
        },
        {
            "etapa": "7",
            "titulo": "Watchlist",
            "descricao": "Salve o ativo para acompanhamento.",
            "status": _modulo_preenchido("resultado_watchlist"),
            "acao": "Abra Watchlist e adicione o ativo com status, prioridade e próxima ação.",
        },
    ]


def _proximo_passo_sugerido(etapas: List[Dict[str, Any]]) -> str:
    for etapa in etapas:
        if not etapa["status"]:
            return etapa["acao"]

    return "A análise está bem encaminhada. Revise os dados, baixe o relatório e acompanhe o ativo na watchlist."


def _calcular_progresso(etapas: List[Dict[str, Any]]) -> int:
    if len(etapas) == 0:
        return 0

    concluidas = len([etapa for etapa in etapas if etapa["status"]])
    progresso = int(round((concluidas / len(etapas)) * 100))

    return max(0, min(100, progresso))


def _detectar_modo_manual_padrao(contexto: Dict[str, Any]) -> bool:
    empresa = str(contexto.get("empresa", "")).strip().lower()
    ticker = str(contexto.get("ticker", "")).strip().upper()

    return empresa in ["empresa manual", "empresa analisada"] or ticker == "MANUAL"


def _injetar_css_inicio() -> None:
    st.markdown(
        """
        <style>
            .inicio-hero {
                padding: 1.55rem 1.6rem;
                border-radius: 26px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    radial-gradient(circle at top left, rgba(214, 181, 109, 0.22), transparent 30%),
                    radial-gradient(circle at bottom right, rgba(74, 144, 226, 0.20), transparent 34%),
                    linear-gradient(135deg, rgba(8, 15, 27, 0.98), rgba(5, 9, 18, 0.98));
                box-shadow: 0 18px 55px rgba(0, 0, 0, 0.33);
                margin-bottom: 1.25rem;
            }

            .inicio-eyebrow {
                color: #d6b56d;
                font-size: 0.78rem;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .inicio-title {
                color: #f4f7fb;
                font-size: 1.95rem;
                font-weight: 850;
                margin-bottom: 0.45rem;
            }

            .inicio-subtitle {
                color: rgba(244, 247, 251, 0.74);
                font-size: 0.98rem;
                line-height: 1.58;
                max-width: 1040px;
            }

            .inicio-card {
                padding: 1.05rem 1.1rem;
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.035);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.18);
                height: 100%;
            }

            .inicio-card-label {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .inicio-card-value {
                color: #f4f7fb;
                font-size: 1.22rem;
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .inicio-card-note {
                color: rgba(244, 247, 251, 0.66);
                font-size: 0.86rem;
                line-height: 1.45;
            }

            .inicio-step {
                padding: 0.95rem 1rem;
                border-radius: 18px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.028);
                margin-bottom: 0.72rem;
            }

            .inicio-step-ok {
                border-left: 4px solid rgba(46, 204, 113, 0.95);
            }

            .inicio-step-pending {
                border-left: 4px solid rgba(214, 181, 109, 0.95);
            }

            .inicio-step-title {
                color: #f4f7fb;
                font-size: 0.98rem;
                font-weight: 800;
                margin-bottom: 0.25rem;
            }

            .inicio-step-text {
                color: rgba(244, 247, 251, 0.68);
                font-size: 0.88rem;
                line-height: 1.45;
            }

            .inicio-badge {
                display: inline-block;
                padding: 0.18rem 0.55rem;
                border-radius: 999px;
                background: rgba(214, 181, 109, 0.10);
                border: 1px solid rgba(214, 181, 109, 0.20);
                color: #d6b56d;
                font-size: 0.72rem;
                font-weight: 750;
                margin-bottom: 0.5rem;
            }

            .inicio-disclaimer {
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
        <div class="inicio-card">
            <div class="inicio-card-label">{label}</div>
            <div class="inicio-card-value">{value}</div>
            <div class="inicio-card-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _renderizar_etapa(etapa: Dict[str, Any]) -> None:
    classe = "inicio-step-ok" if etapa["status"] else "inicio-step-pending"
    marcador = "Concluído" if etapa["status"] else "Pendente"

    st.markdown(
        f"""
        <div class="inicio-step {classe}">
            <div class="inicio-badge">Etapa {etapa["etapa"]} • {marcador}</div>
            <div class="inicio-step-title">{etapa["titulo"]}</div>
            <div class="inicio-step-text">{etapa["descricao"]}</div>
            <div class="inicio-step-text"><strong>Próxima ação:</strong> {etapa["acao"]}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def renderizar_inicio_premium(
    resultado_valuation: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Renderiza a tela de Início Premium.
    """
    _injetar_css_inicio()

    contexto = _extrair_contexto(resultado_valuation)
    etapas = _gerar_status_jornada()
    progresso = _calcular_progresso(etapas)
    proximo_passo = _proximo_passo_sugerido(etapas)

    simbolo = contexto["simbolo_moeda"]

    st.markdown(
        """
        <div class="inicio-hero">
            <div class="inicio-eyebrow">Comece pela clareza</div>
            <div class="inicio-title">Jornada Guiada de Análise</div>
            <div class="inicio-subtitle">
                A Máquina de Preço-Teto organiza sua análise em uma sequência disciplinada:
                premissas, valuation, tese, checklist de erros, painel executivo, relatório e watchlist.
                O objetivo não é decidir por você, mas transformar investimento em método.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if _detectar_modo_manual_padrao(contexto):
        st.warning(
            "Você está no modo manual/demonstração. Antes de interpretar qualquer status como válido, "
            "preencha dados reais da empresa ou selecione uma empresa da base. O status inicial pode refletir apenas dados padrão."
        )

    st.markdown("### Análise atual")

    col_ctx_1, col_ctx_2, col_ctx_3, col_ctx_4 = st.columns(4)

    with col_ctx_1:
        st.metric("Ativo", contexto["empresa"])

    with col_ctx_2:
        st.metric("Ticker", contexto["ticker"])

    with col_ctx_3:
        st.metric("Status educacional", contexto["status"])

    with col_ctx_4:
        st.metric("Progresso da jornada", f"{progresso}%")

    st.progress(progresso / 100)

    st.divider()

    st.markdown("### Números principais")

    col_num_1, col_num_2, col_num_3 = st.columns(3)

    with col_num_1:
        _card(
            "Preço atual",
            _fmt_moeda(contexto["preco_atual"], simbolo),
            "Preço informado ou editado na análise atual.",
        )

    with col_num_2:
        _card(
            "Preço-teto",
            _fmt_moeda(contexto["preco_teto"], simbolo),
            "Zona conservadora estimada pelo modelo.",
        )

    with col_num_3:
        _card(
            "Preço justo",
            _fmt_moeda(contexto["preco_justo"], simbolo),
            "Valor estimado antes da margem de segurança.",
        )

    st.divider()

    st.markdown("### Próximo passo sugerido")
    st.info(proximo_passo)

    st.divider()

    st.markdown("### Fluxo recomendado")

    col_fluxo_1, col_fluxo_2 = st.columns([1, 1])

    with col_fluxo_1:
        for etapa in etapas[:4]:
            _renderizar_etapa(etapa)

    with col_fluxo_2:
        for etapa in etapas[4:]:
            _renderizar_etapa(etapa)

    st.divider()

    st.markdown("### Como usar o app com inteligência")

    col_uso_1, col_uso_2, col_uso_3 = st.columns(3)

    with col_uso_1:
        _card(
            "1. Não comece pelo status",
            "Comece pelas premissas",
            "O resultado só é útil se lucro, FCF, ações, preço e múltiplos fizerem sentido.",
        )

    with col_uso_2:
        _card(
            "2. Não confie só no preço",
            "Revise a tese",
            "Empresa boa comprada cara pode virar mau investimento. Empresa barata com tese fraca também pode ser armadilha.",
        )

    with col_uso_3:
        _card(
            "3. Transforme análise em rotina",
            "Use a watchlist",
            "Salve o ativo com próxima ação, prioridade e tese curta para acompanhar com disciplina.",
        )

    st.markdown(
        """
        <div class="inicio-disclaimer">
            <strong>Aviso educacional:</strong> esta plataforma não recomenda compra, venda ou manutenção de ativos.
            Ela organiza raciocínio, valuation, riscos, tese, relatórios e acompanhamento. Toda decisão real deve considerar
            objetivos pessoais, diversificação, liquidez, tributação, horizonte de tempo e responsabilidade individual.
        </div>
        """,
        unsafe_allow_html=True,
    )