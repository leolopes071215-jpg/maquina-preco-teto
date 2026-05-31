# decisao.py

import streamlit as st
from typing import Any, Dict, List, Optional


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v1.13 — Resumo Executivo da Decisão + Relatório Premium
# ------------------------------------------------------------
# Este módulo transforma os dados do valuation, da convicção
# da tese e dos cenários em uma leitura educacional consolidada.
# Não é recomendação de investimento.
# ============================================================


def _safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    """
    Converte valores para float com segurança.
    Aceita números, strings com vírgula e strings com símbolos.
    """
    if value is None:
        return default

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        cleaned = (
            value.replace("R$", "")
            .replace("US$", "")
            .replace("$", "")
            .replace("%", "")
            .replace(".", "")
            .replace(",", ".")
            .strip()
        )

        try:
            return float(cleaned)
        except ValueError:
            return default

    return default


def _clamp(value: float, minimum: float = 0, maximum: float = 100) -> float:
    """Limita um número entre mínimo e máximo."""
    return max(minimum, min(maximum, value))


def _fmt_money(value: Optional[float]) -> str:
    """Formata valores monetários de forma simples para a tela."""
    if value is None:
        return "N/D"
    return f"${value:,.2f}"


def _fmt_percent(value: Optional[float]) -> str:
    """Formata percentual para a tela."""
    if value is None:
        return "N/D"
    return f"{value:.1f}%"


def _fmt_money_markdown(value: Optional[float], simbolo_moeda: str = "R$") -> str:
    """Formata dinheiro para o relatório em Markdown."""
    if value is None:
        return "N/D"

    return f"{simbolo_moeda} {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_percent_markdown(value: Optional[float]) -> str:
    """Formata percentual para o relatório em Markdown."""
    if value is None:
        return "N/D"

    return f"{value:.2f}%"


def _normalizar_status(status: Any) -> str:
    """Normaliza o status do valuation."""
    if status is None:
        return "N/D"

    status_str = str(status).upper().strip()

    if "COMPRA" in status_str:
        return "COMPRA"
    if "NEUTRO" in status_str:
        return "NEUTRO"
    if "AGUARDE" in status_str:
        return "AGUARDE"

    return status_str or "N/D"


def _normalizar_classificacao(classificacao: Any) -> str:
    """Normaliza a classificação da tese."""
    if classificacao is None:
        return "N/D"

    texto = str(classificacao).upper().strip()

    if "FORTE" in texto:
        return "FORTE"
    if "BOA" in texto:
        return "BOA"
    if "MODERADA" in texto:
        return "MODERADA"
    if "FRACA" in texto:
        return "FRACA"
    if "RISCO" in texto:
        return "RISCO ELEVADO"

    return texto or "N/D"


def _pick_from_dict(data: Dict[str, Any], possible_keys: List[str], default: Any = None) -> Any:
    """
    Procura uma informação em um dicionário usando várias chaves possíveis.
    Isso deixa o módulo mais resistente a nomes diferentes nos outros arquivos.
    """
    if not isinstance(data, dict):
        return default

    for key in possible_keys:
        if key in data and data[key] not in [None, ""]:
            return data[key]

    return default


def _merge_session_dicts(possible_keys: List[str]) -> Dict[str, Any]:
    """
    Junta possíveis dicionários salvos no st.session_state.
    O objetivo é funcionar mesmo que o app use nomes diferentes.
    """
    merged: Dict[str, Any] = {}

    for key in possible_keys:
        value = st.session_state.get(key)

        if isinstance(value, dict):
            merged.update(value)

    return merged


def _extrair_dados_valuation(resultado_valuation: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Extrai dados principais do valuation.
    Primeiro usa o argumento direto.
    Se não existir, tenta buscar no st.session_state.
    """
    data = {}

    session_data = _merge_session_dicts(
        [
            "resultado_valuation",
            "resultado_calculo",
            "ultima_analise",
            "analise_atual",
            "valuation_resultado",
            "resultado_preco_teto",
        ]
    )

    data.update(session_data)

    if isinstance(resultado_valuation, dict):
        data.update(resultado_valuation)

    empresa = _pick_from_dict(
        data,
        ["empresa", "nome_empresa", "ticker", "ativo", "companhia"],
        "Empresa analisada",
    )

    status = _pick_from_dict(
        data,
        ["status_valuation", "status", "leitura_status", "status_final"],
        st.session_state.get("status_valuation"),
    )

    preco_atual = _safe_float(
        _pick_from_dict(
            data,
            ["preco_atual", "preço_atual", "cotacao_atual", "cotação_atual", "current_price"],
            st.session_state.get("preco_atual"),
        )
    )

    preco_teto = _safe_float(
        _pick_from_dict(
            data,
            ["preco_teto", "preço_teto", "preco_teto_final", "preço_teto_final", "teto"],
            st.session_state.get("preco_teto"),
        )
    )

    preco_justo = _safe_float(
        _pick_from_dict(
            data,
            [
                "preco_justo",
                "preço_justo",
                "preco_justo_combinado",
                "preço_justo_combinado",
                "valor_justo",
                "fair_value",
            ],
            st.session_state.get("preco_justo"),
        )
    )

    margem_seguranca = _safe_float(
        _pick_from_dict(
            data,
            ["margem_seguranca", "margem_de_seguranca", "mos", "margin_of_safety"],
            st.session_state.get("margem_seguranca"),
        )
    )

    return {
        "empresa": empresa,
        "status_valuation": _normalizar_status(status),
        "preco_atual": preco_atual,
        "preco_teto": preco_teto,
        "preco_justo": preco_justo,
        "margem_seguranca": margem_seguranca,
    }


def _extrair_dados_conviccao(resultado_conviccao: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Extrai score, classificação e alertas do motor de convicção.
    """
    data = {}

    session_data = _merge_session_dicts(
        [
            "resultado_conviccao_tese",
            "conviccao_resultado",
            "resultado_conviccao",
            "motor_conviccao",
            "tese_conviccao",
        ]
    )

    data.update(session_data)

    if isinstance(resultado_conviccao, dict):
        data.update(resultado_conviccao)

    score = _safe_float(
        _pick_from_dict(
            data,
            ["score_conviccao", "score", "pontuacao", "pontuação", "score_tese"],
            st.session_state.get("score_conviccao"),
        ),
        default=50,
    )

    classificacao = _pick_from_dict(
        data,
        ["classificacao_tese", "classificação_tese", "classificacao", "classificação", "rating_tese"],
        st.session_state.get("classificacao_tese"),
    )

    alertas = _pick_from_dict(
        data,
        ["alertas", "alertas_qualitativos", "riscos_alertas", "pontos_de_atencao", "pontos_de_atenção"],
        st.session_state.get("alertas_conviccao", []),
    )

    if alertas is None:
        alertas = []

    if isinstance(alertas, str):
        alertas = [alertas]

    if not isinstance(alertas, list):
        alertas = []

    return {
        "score_conviccao": _clamp(score or 50),
        "classificacao_tese": _normalizar_classificacao(classificacao),
        "alertas": alertas,
    }


def _extrair_dados_cenarios(resultado_cenarios: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Extrai informações dos cenários, se existirem.
    O módulo funciona mesmo sem cenários salvos.
    """
    data = {}

    session_data = _merge_session_dicts(
        [
            "resultado_cenarios",
            "simulador_cenarios",
            "cenarios",
            "leitura_cenarios",
        ]
    )

    data.update(session_data)

    if isinstance(resultado_cenarios, dict):
        data.update(resultado_cenarios)

    return data


def _status_cenario(cenarios: Dict[str, Any], nomes_possiveis: List[str]) -> str:
    """
    Busca o status de um cenário específico.
    """
    if not isinstance(cenarios, dict):
        return "N/D"

    for nome in nomes_possiveis:
        cenario = cenarios.get(nome)

        if isinstance(cenario, dict):
            status = _pick_from_dict(
                cenario,
                ["status", "status_valuation", "leitura", "resultado"],
                None,
            )
            return _normalizar_status(status)

        if isinstance(cenario, str):
            return _normalizar_status(cenario)

    return "N/D"


def _analisar_dependencia_otimista(cenarios: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analisa se a tese depende demais do cenário otimista.
    """
    conservador = _status_cenario(cenarios, ["conservador", "Cenário Conservador", "Conservador"])
    base = _status_cenario(cenarios, ["base", "Cenário Base", "Base"])
    otimista = _status_cenario(cenarios, ["otimista", "Cenário Otimista", "Otimista"])

    if conservador == "N/D" and base == "N/D" and otimista == "N/D":
        return {
            "risco_otimista": "N/D",
            "score_cenarios": 50,
            "leitura": "Cenários ainda não identificados. Execute o simulador para fortalecer a leitura da decisão.",
            "conservador": conservador,
            "base": base,
            "otimista": otimista,
        }

    if otimista == "COMPRA" and base != "COMPRA" and conservador != "COMPRA":
        return {
            "risco_otimista": "ALTO",
            "score_cenarios": 35,
            "leitura": "A atratividade parece depender principalmente de premissas otimistas. Isso exige revisão cuidadosa antes de aumentar a convicção.",
            "conservador": conservador,
            "base": base,
            "otimista": otimista,
        }

    if base == "COMPRA" and conservador != "COMPRA":
        return {
            "risco_otimista": "MODERADO",
            "score_cenarios": 65,
            "leitura": "A tese se sustenta no cenário base, mas ainda perde força quando as premissas ficam mais conservadoras.",
            "conservador": conservador,
            "base": base,
            "otimista": otimista,
        }

    if conservador == "COMPRA":
        return {
            "risco_otimista": "BAIXO",
            "score_cenarios": 85,
            "leitura": "A tese parece resiliente até em premissas conservadoras. Isso aumenta a qualidade da leitura educacional.",
            "conservador": conservador,
            "base": base,
            "otimista": otimista,
        }

    return {
        "risco_otimista": "MODERADO",
        "score_cenarios": 55,
        "leitura": "Os cenários não mostram uma assimetria totalmente clara. A melhor ação educacional é revisar premissas e comparar com outras empresas.",
        "conservador": conservador,
        "base": base,
        "otimista": otimista,
    }


def _score_valuation(status: str) -> float:
    """
    Transforma o status do valuation em pontuação.
    """
    status = _normalizar_status(status)

    if status == "COMPRA":
        return 85
    if status == "NEUTRO":
        return 58
    if status == "AGUARDE":
        return 35

    return 50


def _score_preco(preco_atual: Optional[float], preco_teto: Optional[float]) -> float:
    """
    Pontua o preço atual em relação ao preço-teto.
    """
    if preco_atual is None or preco_teto is None or preco_atual <= 0 or preco_teto <= 0:
        return 50

    diferenca = (preco_teto - preco_atual) / preco_teto

    if diferenca >= 0.20:
        return 95
    if diferenca >= 0.10:
        return 85
    if diferenca >= 0:
        return 72
    if diferenca >= -0.10:
        return 55
    if diferenca >= -0.25:
        return 38

    return 25


def _calcular_metricas_preco(
    preco_atual: Optional[float],
    preco_teto: Optional[float],
    preco_justo: Optional[float],
) -> Dict[str, Optional[float]]:
    """
    Calcula diferenças entre preço atual, preço-teto e preço justo.
    """
    gap_teto = None
    potencial_justo = None

    if preco_atual is not None and preco_teto is not None and preco_atual > 0:
        gap_teto = ((preco_teto - preco_atual) / preco_atual) * 100

    if preco_atual is not None and preco_justo is not None and preco_atual > 0:
        potencial_justo = ((preco_justo - preco_atual) / preco_atual) * 100

    return {
        "gap_teto": gap_teto,
        "potencial_justo": potencial_justo,
    }


def calcular_resumo_decisao(
    resultado_valuation: Optional[Dict[str, Any]] = None,
    resultado_conviccao: Optional[Dict[str, Any]] = None,
    resultado_cenarios: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Calcula o resumo executivo da decisão educacional.
    """
    valuation = _extrair_dados_valuation(resultado_valuation)
    conviccao = _extrair_dados_conviccao(resultado_conviccao)
    cenarios = _extrair_dados_cenarios(resultado_cenarios)
    leitura_cenarios = _analisar_dependencia_otimista(cenarios)

    status_valuation = valuation["status_valuation"]
    preco_atual = valuation["preco_atual"]
    preco_teto = valuation["preco_teto"]
    preco_justo = valuation["preco_justo"]
    score_conviccao = conviccao["score_conviccao"]
    alertas = conviccao["alertas"]

    score_val = _score_valuation(status_valuation)
    score_preco = _score_preco(preco_atual, preco_teto)
    score_cenarios = leitura_cenarios["score_cenarios"]

    penalidade_alertas = min(len(alertas) * 4, 18)

    score_final = (
        score_val * 0.32
        + score_preco * 0.25
        + score_conviccao * 0.33
        + score_cenarios * 0.10
        - penalidade_alertas
    )

    score_final = int(round(_clamp(score_final)))

    metricas_preco = _calcular_metricas_preco(preco_atual, preco_teto, preco_justo)

    risco_otimista = leitura_cenarios["risco_otimista"]

    if score_final >= 75 and status_valuation == "COMPRA" and score_conviccao >= 70 and risco_otimista != "ALTO":
        classificacao_decisao = "Estudar com prioridade"
        acao_educacional = (
            "A empresa merece estudo prioritário. A leitura educacional sugere revisar a tese, "
            "validar premissas conservadoras e comparar com outras oportunidades antes de qualquer decisão real."
        )

    elif status_valuation == "AGUARDE" and score_conviccao >= 65:
        classificacao_decisao = "Aguardar preço melhor"
        acao_educacional = (
            "A tese pode ter qualidade, mas o preço atual não oferece margem de segurança suficiente. "
            "A ação educacional mais racional é monitorar a cotação e revisar o preço-teto periodicamente."
        )

    elif risco_otimista == "ALTO":
        classificacao_decisao = "Revisar premissas"
        acao_educacional = (
            "A atratividade depende demais de premissas otimistas. Revise crescimento, múltiplos, margens, "
            "FCF por ação e margem de segurança antes de elevar a convicção."
        )

    elif score_final < 40 or score_conviccao < 35:
        classificacao_decisao = "Evitar por enquanto"
        acao_educacional = (
            "A combinação entre valuation, preço, convicção e riscos ainda é fraca. "
            "A ação educacional é evitar pressa, estudar melhor a empresa e buscar dados mais confiáveis."
        )

    elif score_final >= 52:
        classificacao_decisao = "Monitorar"
        acao_educacional = (
            "A leitura não é ruim, mas ainda não é decisiva. Monitore preço, qualidade da tese, riscos e evolução dos fundamentos."
        )

    else:
        classificacao_decisao = "Revisar premissas"
        acao_educacional = (
            "O resultado ainda exige refinamento. Revise dados de lucro, FCF, margem de segurança, riscos e qualidade da tese."
        )

    resumo = {
        "empresa": valuation["empresa"],
        "score_final": score_final,
        "classificacao_decisao": classificacao_decisao,
        "status_valuation": status_valuation,
        "score_conviccao": int(round(score_conviccao)),
        "classificacao_tese": conviccao["classificacao_tese"],
        "preco_atual": preco_atual,
        "preco_teto": preco_teto,
        "preco_justo": preco_justo,
        "gap_teto": metricas_preco["gap_teto"],
        "potencial_justo": metricas_preco["potencial_justo"],
        "alertas": alertas,
        "risco_otimista": risco_otimista,
        "leitura_cenarios": leitura_cenarios["leitura"],
        "cenario_conservador": leitura_cenarios["conservador"],
        "cenario_base": leitura_cenarios["base"],
        "cenario_otimista": leitura_cenarios["otimista"],
        "acao_educacional": acao_educacional,
    }

    st.session_state["resultado_resumo_decisao"] = resumo

    return resumo


def _injetar_css_decisao() -> None:
    """
    CSS local da aba Resumo da Decisão.
    Mantém estética premium sem depender de bibliotecas externas.
    """
    st.markdown(
        """
        <style>
            .decisao-hero {
                padding: 1.35rem 1.45rem;
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    radial-gradient(circle at top left, rgba(74, 144, 226, 0.20), transparent 34%),
                    linear-gradient(135deg, rgba(12, 18, 32, 0.96), rgba(7, 11, 20, 0.98));
                box-shadow: 0 18px 50px rgba(0, 0, 0, 0.28);
                margin-bottom: 1.2rem;
            }

            .decisao-eyebrow {
                color: #d6b56d;
                font-size: 0.78rem;
                letter-spacing: 0.12em;
                text-transform: uppercase;
                font-weight: 700;
                margin-bottom: 0.35rem;
            }

            .decisao-title {
                color: #f4f7fb;
                font-size: 1.65rem;
                font-weight: 800;
                margin-bottom: 0.4rem;
            }

            .decisao-subtitle {
                color: rgba(244, 247, 251, 0.72);
                font-size: 0.96rem;
                line-height: 1.55;
                max-width: 900px;
            }

            .decisao-card {
                padding: 1.05rem 1.1rem;
                border-radius: 18px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.035);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.18);
                height: 100%;
            }

            .decisao-label {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.78rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                margin-bottom: 0.35rem;
                font-weight: 700;
            }

            .decisao-value {
                color: #f4f7fb;
                font-size: 1.35rem;
                font-weight: 800;
                margin-bottom: 0.25rem;
            }

            .decisao-note {
                color: rgba(244, 247, 251, 0.65);
                font-size: 0.86rem;
                line-height: 1.45;
            }

            .decisao-alert {
                padding: 0.82rem 1rem;
                border-radius: 14px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.84);
                margin-bottom: 0.6rem;
            }

            .decisao-disclaimer {
                padding: 0.9rem 1rem;
                border-radius: 16px;
                background: rgba(74, 144, 226, 0.08);
                border: 1px solid rgba(74, 144, 226, 0.18);
                color: rgba(244, 247, 251, 0.78);
                font-size: 0.9rem;
                line-height: 1.55;
                margin-top: 1.2rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _card(label: str, value: str, note: str = "") -> None:
    """Renderiza card premium simples."""
    st.markdown(
        f"""
        <div class="decisao-card">
            <div class="decisao-label">{label}</div>
            <div class="decisao-value">{value}</div>
            <div class="decisao-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_resumo_decisao(
    resultado_valuation: Optional[Dict[str, Any]] = None,
    resultado_conviccao: Optional[Dict[str, Any]] = None,
    resultado_cenarios: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Renderiza a aba Resumo da Decisão no Streamlit.
    """
    _injetar_css_decisao()

    resumo = calcular_resumo_decisao(
        resultado_valuation=resultado_valuation,
        resultado_conviccao=resultado_conviccao,
        resultado_cenarios=resultado_cenarios,
    )

    classificacao_decisao = resumo["classificacao_decisao"]
    acao_educacional = resumo["acao_educacional"]

    st.markdown(
        """
        <div class="decisao-hero">
            <div class="decisao-eyebrow">Copiloto educacional de valuation</div>
            <div class="decisao-title">Resumo Executivo da Decisão</div>
            <div class="decisao-subtitle">
                Uma leitura consolidada que cruza preço, margem de segurança, convicção da tese,
                cenários e alertas qualitativos. O objetivo é melhorar raciocínio, disciplina e clareza,
                não emitir recomendação de investimento.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if resumo["status_valuation"] == "N/D":
        st.warning(
            "Ainda não encontrei um resultado de valuation salvo na sessão. "
            "Execute uma análise principal antes de usar o Resumo da Decisão."
        )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        _card(
            "Score final",
            f"{resumo['score_final']}/100",
            "Combina valuation, preço, convicção, cenários e alertas.",
        )

    with col2:
        _card(
            "Classificação",
            classificacao_decisao,
            "Próxima leitura educacional sugerida.",
        )

    with col3:
        _card(
            "Valuation",
            resumo["status_valuation"],
            "Status educacional do preço atual contra o preço-teto.",
        )

    with col4:
        _card(
            "Convicção da tese",
            f"{resumo['score_conviccao']}/100",
            f"Classificação: {resumo['classificacao_tese']}",
        )

    st.markdown("### Leitura do preço")

    col5, col6, col7 = st.columns(3)

    with col5:
        st.metric("Preço atual", _fmt_money(resumo["preco_atual"]))

    with col6:
        st.metric(
            "Preço-teto",
            _fmt_money(resumo["preco_teto"]),
            delta=_fmt_percent(resumo["gap_teto"]) if resumo["gap_teto"] is not None else None,
        )

    with col7:
        st.metric(
            "Preço justo estimado",
            _fmt_money(resumo["preco_justo"]),
            delta=_fmt_percent(resumo["potencial_justo"]) if resumo["potencial_justo"] is not None else None,
        )

    st.markdown("### Qualidade da decisão")

    st.progress(resumo["score_final"] / 100)

    st.markdown(
        f"""
        <div class="decisao-card">
            <div class="decisao-label">Ação educacional sugerida</div>
            <div class="decisao-value">{classificacao_decisao}</div>
            <div class="decisao-note">{acao_educacional}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Leitura dos cenários")

    col8, col9, col10, col11 = st.columns(4)

    with col8:
        _card("Conservador", resumo["cenario_conservador"], "Resistência com premissas duras.")

    with col9:
        _card("Base", resumo["cenario_base"], "Leitura com premissas centrais.")

    with col10:
        _card("Otimista", resumo["cenario_otimista"], "Leitura com premissas favoráveis.")

    with col11:
        _card("Risco otimista", resumo["risco_otimista"], "Mede dependência de premissas agressivas.")

    st.info(resumo["leitura_cenarios"])

    st.markdown("### Alertas qualitativos")

    if resumo["alertas"]:
        for alerta in resumo["alertas"]:
            st.markdown(
                f"""
                <div class="decisao-alert">
                    {alerta}
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.success(
            "Nenhum alerta qualitativo relevante foi identificado pelo motor de convicção até o momento."
        )

    st.markdown(
        """
        <div class="decisao-disclaimer">
            <strong>Aviso educacional:</strong> esta leitura não é recomendação de compra, venda ou manutenção de ativos.
            O objetivo da Máquina de Preço-Teto é organizar premissas, estimular pensamento crítico e apoiar estudos
            de valuation fundamentalista. Toda decisão real deve considerar objetivos pessoais, riscos, diversificação,
            horizonte de tempo e responsabilidade individual.
        </div>
        """,
        unsafe_allow_html=True,
    )


def gerar_bloco_markdown_decisao(
    resumo_decisao: Optional[Dict[str, Any]] = None,
    simbolo_moeda: str = "R$",
) -> str:
    """
    Gera uma seção em Markdown com o Resumo Executivo da Decisão.
    Essa função é usada na v1.13 para enriquecer o relatório executivo.
    """
    if resumo_decisao is None:
        resumo_decisao = st.session_state.get("resultado_resumo_decisao")

    if resumo_decisao is None:
        resumo_decisao = calcular_resumo_decisao()

    alertas = resumo_decisao.get("alertas", [])

    if len(alertas) == 0:
        alertas_markdown = "- Nenhum alerta qualitativo relevante foi identificado no momento."
    else:
        alertas_markdown = "\n".join([f"- {alerta}" for alerta in alertas])

    preco_atual = resumo_decisao.get("preco_atual")
    preco_teto = resumo_decisao.get("preco_teto")
    preco_justo = resumo_decisao.get("preco_justo")
    gap_teto = resumo_decisao.get("gap_teto")
    potencial_justo = resumo_decisao.get("potencial_justo")

    return f"""

---

# Resumo Executivo da Decisão

> Esta seção consolida valuation, preço, margem de segurança, convicção da tese, cenários e alertas qualitativos.  
> O objetivo é apoiar estudo e disciplina, não recomendar compra, venda ou manutenção de ativos.

## Síntese final

| Indicador | Resultado |
|---|---|
| Empresa | {resumo_decisao.get("empresa", "N/D")} |
| Score final | {resumo_decisao.get("score_final", "N/D")}/100 |
| Classificação da decisão | {resumo_decisao.get("classificacao_decisao", "N/D")} |
| Status do valuation | {resumo_decisao.get("status_valuation", "N/D")} |
| Score de convicção | {resumo_decisao.get("score_conviccao", "N/D")}/100 |
| Classificação da tese | {resumo_decisao.get("classificacao_tese", "N/D")} |

## Leitura de preço

| Métrica | Valor |
|---|---|
| Preço atual | {_fmt_money_markdown(preco_atual, simbolo_moeda)} |
| Preço-teto | {_fmt_money_markdown(preco_teto, simbolo_moeda)} |
| Preço justo estimado | {_fmt_money_markdown(preco_justo, simbolo_moeda)} |
| Margem até preço-teto | {_fmt_percent_markdown(gap_teto)} |
| Potencial até preço justo | {_fmt_percent_markdown(potencial_justo)} |

## Leitura dos cenários

| Cenário | Status |
|---|---|
| Conservador | {resumo_decisao.get("cenario_conservador", "N/D")} |
| Base | {resumo_decisao.get("cenario_base", "N/D")} |
| Otimista | {resumo_decisao.get("cenario_otimista", "N/D")} |
| Risco de depender de otimismo | {resumo_decisao.get("risco_otimista", "N/D")} |

**Interpretação dos cenários:**  
{resumo_decisao.get("leitura_cenarios", "N/D")}

## Alertas qualitativos

{alertas_markdown}

## Ação educacional sugerida

**{resumo_decisao.get("classificacao_decisao", "N/D")}**

{resumo_decisao.get("acao_educacional", "N/D")}

## Aviso educacional

Este relatório não representa recomendação de investimento.  
A Máquina de Preço-Teto é uma ferramenta educacional para organizar premissas, melhorar raciocínio, comparar cenários e desenvolver disciplina de valuation.  
Toda decisão real deve considerar objetivos pessoais, riscos, diversificação, horizonte de tempo e responsabilidade individual.
"""