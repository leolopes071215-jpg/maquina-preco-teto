# release_candidate.py

from datetime import datetime
from typing import Any, Dict, List

import streamlit as st


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v1.40 — Release Candidate da Fase 1
# ------------------------------------------------------------
# Esta tela fecha a Fase 1 do produto.
#
# Objetivo:
# - consolidar prontidão do MVP
# - revisar UX, dados, convite beta, lançamento e modos
# - orientar checklist final antes da Fase 2
# - preparar início do beta real com usuários
# ============================================================


def _safe_get_dict(key: str) -> Dict[str, Any]:
    valor = st.session_state.get(key)

    if isinstance(valor, dict):
        return valor

    return {}


def _safe_int(valor: Any, default: int = 0) -> int:
    try:
        return int(float(valor))
    except (TypeError, ValueError):
        return default


def _fmt_texto(valor: Any, padrao: str = "N/D") -> str:
    if valor is None or valor == "":
        return padrao

    return str(valor)


def _extrair_contexto_release() -> Dict[str, Any]:
    valuation = _safe_get_dict("resultado_valuation")
    onboarding = _safe_get_dict("resultado_onboarding")
    navegacao = _safe_get_dict("resultado_navegacao_simplificada")
    negocio = _safe_get_dict("resultado_dashboard_negocio")
    lancamento = _safe_get_dict("resultado_lancamento_beta")
    persistencia = _safe_get_dict("resultado_persistencia_dados")
    ux = _safe_get_dict("resultado_auditoria_ux")
    convite = _safe_get_dict("resultado_convite_beta_publico")
    landing = _safe_get_dict("resultado_landing_page")

    modo_exibicao = st.session_state.get("modo_exibicao_app", "Fundador")

    return {
        "modo_exibicao": modo_exibicao,
        "empresa": valuation.get("empresa", "N/D"),
        "ticker": valuation.get("ticker", "N/D"),
        "status_valuation": valuation.get("status", valuation.get("status_valuation", "N/D")),
        "perfil_onboarding": onboarding.get("perfil", "N/D"),
        "objetivo_onboarding": onboarding.get("objetivo", "N/D"),
        "objetivo_navegacao": navegacao.get("objetivo", "N/D"),
        "score_tracao": negocio.get("score_tracao", 0),
        "score_lancamento": lancamento.get("score_lancamento", 0),
        "score_ux": ux.get("score_ux", 0),
        "classificacao_ux": ux.get("classificacao", "N/D"),
        "classificacao_convite": convite.get("classificacao", "N/D"),
        "headline_landing": landing.get("headline", "N/D"),
        "arquivos_existentes": persistencia.get("arquivos_existentes", 0),
        "gitignore_pendente": persistencia.get("gitignore_pendente", 0),
        "total_feedbacks": negocio.get("total_feedbacks", 0),
        "total_lista": negocio.get("total_lista_espera", 0),
    }


def _gerar_criterios_release(contexto: Dict[str, Any]) -> List[Dict[str, str]]:
    modo = _fmt_texto(contexto.get("modo_exibicao"))
    perfil_onboarding = _fmt_texto(contexto.get("perfil_onboarding"))
    objetivo_navegacao = _fmt_texto(contexto.get("objetivo_navegacao"))
    headline_landing = _fmt_texto(contexto.get("headline_landing"))
    classificacao_convite = _fmt_texto(contexto.get("classificacao_convite"))

    score_ux = _safe_int(contexto.get("score_ux"))
    score_lancamento = _safe_int(contexto.get("score_lancamento"))
    score_tracao = _safe_int(contexto.get("score_tracao"))
    gitignore_pendente = _safe_int(contexto.get("gitignore_pendente"))

    return [
        {
            "Área": "Produto principal",
            "Critério": "O app calcula valuation e mostra preço-teto/status educacional.",
            "Status": "OK" if contexto.get("status_valuation") != "N/D" else "Atenção",
            "Leitura": "Motor principal funcionando e visível.",
        },
        {
            "Área": "Modo de exibição",
            "Critério": "Existe separação entre Usuário Beta, Investidor Completo e Fundador.",
            "Status": "OK" if modo in ["Usuário Beta", "Investidor Completo", "Fundador"] else "Pendente",
            "Leitura": "Essencial para não expor áreas internas ao usuário beta.",
        },
        {
            "Área": "Navegação",
            "Critério": "A central de navegação está configurada.",
            "Status": "OK" if objetivo_navegacao != "N/D" else "Atenção",
            "Leitura": "Ajuda o usuário a não se perder.",
        },
        {
            "Área": "Onboarding",
            "Critério": "O usuário consegue escolher perfil e objetivo.",
            "Status": "OK" if perfil_onboarding != "N/D" else "Atenção",
            "Leitura": "Reduz fricção na primeira experiência.",
        },
        {
            "Área": "UX",
            "Critério": "Score UX mínimo para beta controlado.",
            "Status": "OK" if score_ux >= 70 else "Atenção",
            "Leitura": "Quanto maior o score, menor a chance de confusão.",
        },
        {
            "Área": "Dados",
            "Critério": "Arquivos sensíveis protegidos no .gitignore.",
            "Status": "OK" if gitignore_pendente == 0 else "Pendente",
            "Leitura": "Não avance sem proteger CSVs de feedback/lista de espera.",
        },
        {
            "Área": "Landing Page",
            "Critério": "Headline e promessa estão estruturadas.",
            "Status": "OK" if headline_landing != "N/D" else "Atenção",
            "Leitura": "Ajuda a comunicar o produto fora do app.",
        },
        {
            "Área": "Convite Beta",
            "Critério": "Kit de convite está estruturado.",
            "Status": "OK" if classificacao_convite != "N/D" else "Atenção",
            "Leitura": "Permite enviar o app com instruções claras.",
        },
        {
            "Área": "Lançamento",
            "Critério": "Score de lançamento mínimo para teste controlado.",
            "Status": "OK" if score_lancamento >= 50 else "Atenção",
            "Leitura": "Beta deve começar pequeno, organizado e mensurável.",
        },
        {
            "Área": "Tração",
            "Critério": "Existem sinais iniciais de feedback/lista de espera.",
            "Status": "OK" if score_tracao >= 50 else "Atenção",
            "Leitura": "Tração baixa não impede beta, mas pede cautela.",
        },
    ]


def _calcular_score_release(criterios: List[Dict[str, str]]) -> int:
    if len(criterios) == 0:
        return 0

    pontos = 0

    for criterio in criterios:
        status = criterio.get("Status", "")

        if status == "OK":
            pontos += 10
        elif status == "Atenção":
            pontos += 5
        else:
            pontos += 0

    return min(100, pontos)


def _classificar_release(score: int) -> str:
    if score >= 85:
        return "Pronto para Fase 2"
    if score >= 70:
        return "Quase pronto para Fase 2"
    if score >= 55:
        return "Beta possível, mas com acompanhamento próximo"
    if score >= 40:
        return "Ainda precisa de correções antes da Fase 2"
    return "Não recomendado avançar ainda"


def _gerar_leitura_release(score: int) -> str:
    if score >= 85:
        return (
            "O MVP está pronto para entrar na Fase 2 com beta controlado. "
            "Agora o foco deixa de ser construir novas funções e passa a ser observar usuários reais."
        )

    if score >= 70:
        return (
            "O MVP está quase pronto. É possível iniciar testes com poucas pessoas, "
            "mas ainda vale revisar UX, convite beta, dados e fluxo mínimo."
        )

    if score >= 55:
        return (
            "O beta é possível, mas precisa ser bem guiado. Envie para pessoas próximas, "
            "observe uso real e colete feedback com atenção."
        )

    if score >= 40:
        return (
            "Ainda existem pontos críticos antes da Fase 2. Priorize correções, clareza, dados e fluxo do usuário beta."
        )

    return (
        "Ainda não é hora de enviar para usuários reais. O produto precisa de mais organização antes do beta."
    )


def _gerar_checklist_final() -> List[Dict[str, str]]:
    return [
        {
            "Item": "Rodar py_compile em todos os arquivos principais",
            "Comando/ação": "python -m py_compile app.py",
            "Obrigatório": "Sim",
        },
        {
            "Item": "Testar app localmente",
            "Comando/ação": "python -m streamlit run app.py",
            "Obrigatório": "Sim",
        },
        {
            "Item": "Testar Streamlit Cloud",
            "Comando/ação": "Abrir o link público do app",
            "Obrigatório": "Sim",
        },
        {
            "Item": "Verificar Modo Usuário Beta",
            "Comando/ação": "Confirmar que abas internas não aparecem",
            "Obrigatório": "Sim",
        },
        {
            "Item": "Verificar Modo Fundador",
            "Comando/ação": "Confirmar que todas as abas aparecem",
            "Obrigatório": "Sim",
        },
        {
            "Item": "Testar download de relatório",
            "Comando/ação": "Aba Relatórios",
            "Obrigatório": "Sim",
        },
        {
            "Item": "Testar Feedback Beta",
            "Comando/ação": "Salvar um feedback teste",
            "Obrigatório": "Sim",
        },
        {
            "Item": "Testar Oferta Beta",
            "Comando/ação": "Salvar um cadastro teste",
            "Obrigatório": "Sim",
        },
        {
            "Item": "Verificar Dados",
            "Comando/ação": "Aba Dados → checar .gitignore e backup",
            "Obrigatório": "Sim",
        },
        {
            "Item": "Gerar Convite Beta",
            "Comando/ação": "Aba Convite Beta → baixar kit",
            "Obrigatório": "Recomendado",
        },
    ]


def _gerar_plano_fase2() -> List[Dict[str, str]]:
    return [
        {
            "Etapa": "1",
            "Foco": "Beta controlado",
            "Ação": "Enviar o app para 5 pessoas próximas.",
            "Métrica": "Pelo menos 3 feedbacks reais.",
        },
        {
            "Etapa": "2",
            "Foco": "Observação de uso",
            "Ação": "Perguntar onde travaram e qual aba entenderam melhor.",
            "Métrica": "Top 3 fricções identificadas.",
        },
        {
            "Etapa": "3",
            "Foco": "Valor percebido",
            "Ação": "Medir se usariam numa análise real.",
            "Métrica": "Pelo menos 2 pessoas dizendo que usariam.",
        },
        {
            "Etapa": "4",
            "Foco": "Intenção de pagamento",
            "Ação": "Direcionar interessados para Oferta Beta.",
            "Métrica": "Primeiros cadastros reais na lista.",
        },
        {
            "Etapa": "5",
            "Foco": "Ajuste do produto",
            "Ação": "Corrigir os pontos mais repetidos.",
            "Métrica": "Nova versão com melhorias baseadas em feedback real.",
        },
        {
            "Etapa": "6",
            "Foco": "Beta ampliado",
            "Ação": "Enviar para 10 a 20 pessoas.",
            "Métrica": "Clareza, retenção, feedback e interesse.",
        },
    ]


def _gerar_regras_fase2() -> List[Dict[str, str]]:
    return [
        {
            "Regra": "Não adicionar função grande sem feedback real",
            "Motivo": "A partir daqui, o usuário deve guiar prioridades.",
        },
        {
            "Regra": "Não enviar em Modo Fundador",
            "Motivo": "Usuário comum não deve ver áreas internas.",
        },
        {
            "Regra": "Não prometer rentabilidade",
            "Motivo": "O produto é educacional, não recomendação financeira.",
        },
        {
            "Regra": "Fazer backup após cada rodada de feedback",
            "Motivo": "Evita perder dados de validação.",
        },
        {
            "Regra": "Medir comportamento, não só opinião",
            "Motivo": "O que a pessoa faz importa mais do que elogio genérico.",
        },
        {
            "Regra": "Corrigir fricção antes de escalar",
            "Motivo": "Escalar um fluxo confuso queima oportunidades.",
        },
    ]


def _gerar_comandos_release() -> str:
    return """python -m py_compile app.py
python -m py_compile modo_exibicao.py
python -m py_compile release_candidate.py
python -m py_compile convite_beta_publico.py
python -m py_compile auditoria_ux.py
python -m py_compile persistencia_dados.py
python -m streamlit run app.py"""


def _gerar_comandos_git_v140() -> str:
    return """git status
git add app.py modo_exibicao.py release_candidate.py
git commit -m "Adiciona release candidate da fase 1 v1.40"
git push
git tag v1.40
git push origin v1.40
git status"""


def _gerar_relatorio_release_markdown(
    contexto: Dict[str, Any],
    criterios: List[Dict[str, str]],
    score: int,
    classificacao: str,
    leitura: str,
) -> str:
    linhas_criterios = "\n".join(
        [
            f"| {item['Área']} | {item['Critério']} | {item['Status']} | {item['Leitura']} |"
            for item in criterios
        ]
    )

    return f"""# Release Candidate — Máquina de Preço-Teto v1.40

Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Resultado

**Score Release:** {score}/100  
**Classificação:** {classificacao}

## Leitura

{leitura}

## Contexto

- Modo de exibição atual: {contexto["modo_exibicao"]}
- Empresa ativa: {contexto["empresa"]}
- Ticker: {contexto["ticker"]}
- Status valuation: {contexto["status_valuation"]}
- Score UX: {contexto["score_ux"]}
- Score lançamento: {contexto["score_lancamento"]}
- Score tração: {contexto["score_tracao"]}
- Total feedbacks: {contexto["total_feedbacks"]}
- Total lista de espera: {contexto["total_lista"]}

## Critérios avaliados

| Área | Critério | Status | Leitura |
|---|---|---|---|
{linhas_criterios}

## Decisão

Se a classificação for “Pronto para Fase 2” ou “Quase pronto para Fase 2”, avance com beta controlado.

Se estiver abaixo disso, corrija UX, dados, convite beta e fluxo mínimo antes de divulgar.
"""


def _injetar_css_release() -> None:
    st.markdown(
        """
        <style>
            .rel-hero {
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

            .rel-eyebrow {
                color: #d6b56d;
                font-size: 0.78rem;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.35rem;
            }

            .rel-title {
                color: #f4f7fb;
                font-size: 2.1rem;
                font-weight: 900;
                margin-bottom: 0.45rem;
                line-height: 1.14;
            }

            .rel-subtitle {
                color: rgba(244, 247, 251, 0.76);
                font-size: 1rem;
                line-height: 1.62;
                max-width: 1080px;
            }

            .rel-card {
                padding: 1.1rem 1.15rem;
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.035);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.18);
                height: 100%;
            }

            .rel-card-label {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .rel-card-value {
                color: #f4f7fb;
                font-size: 1.22rem;
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .rel-card-note {
                color: rgba(244, 247, 251, 0.68);
                font-size: 0.87rem;
                line-height: 1.47;
            }

            .rel-highlight {
                padding: 0.95rem 1rem;
                border-radius: 16px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.92rem;
                line-height: 1.55;
                margin-bottom: 0.7rem;
            }

            .rel-copy {
                padding: 1rem 1.05rem;
                border-radius: 18px;
                background: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(255, 255, 255, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.92rem;
                line-height: 1.58;
                white-space: pre-wrap;
                margin-bottom: 0.85rem;
                font-family: monospace;
            }

            .rel-disclaimer {
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
        <div class="rel-card">
            <div class="rel-card-label">{label}</div>
            <div class="rel-card-value">{value}</div>
            <div class="rel-card-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _copy_box(texto: str) -> None:
    st.markdown(
        f"""
        <div class="rel-copy">{texto}</div>
        """,
        unsafe_allow_html=True,
    )


def renderizar_release_candidate_fase1() -> None:
    """
    Renderiza a central de Release Candidate da Fase 1.
    """
    _injetar_css_release()

    contexto = _extrair_contexto_release()
    criterios = _gerar_criterios_release(contexto)
    score_release = _calcular_score_release(criterios)
    classificacao = _classificar_release(score_release)
    leitura = _gerar_leitura_release(score_release)

    st.session_state["resultado_release_candidate"] = {
        "score_release": score_release,
        "classificacao": classificacao,
        "leitura": leitura,
        **contexto,
    }

    st.markdown(
        """
        <div class="rel-hero">
            <div class="rel-eyebrow">Fechamento da Fase 1</div>
            <div class="rel-title">Release Candidate v1.40</div>
            <div class="rel-subtitle">
                Esta é a revisão final antes da Fase 2. O objetivo é confirmar se o MVP
                está pronto para sair da construção interna e entrar em beta real com usuários.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="rel-highlight">
            A Fase 1 termina quando o produto está pronto para ser testado por pessoas reais.
            A Fase 2 começa quando feedback real passa a guiar as próximas decisões.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Diagnóstico final da Fase 1")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Score Release", f"{score_release}/100")

    with col_2:
        st.metric("Classificação", classificacao)

    with col_3:
        st.metric("Score UX", f"{contexto['score_ux']}/100")

    with col_4:
        st.metric("Score lançamento", f"{contexto['score_lancamento']}/100")

    st.progress(score_release / 100)

    if score_release >= 85:
        st.success(leitura)
    elif score_release >= 55:
        st.warning(leitura)
    else:
        st.error(leitura)

    st.divider()

    st.markdown("### Critérios de prontidão")

    st.dataframe(
        criterios,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Checklist final antes da Fase 2")

    st.dataframe(
        _gerar_checklist_final(),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Plano inicial da Fase 2")

    st.dataframe(
        _gerar_plano_fase2(),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Regras da Fase 2")

    st.dataframe(
        _gerar_regras_fase2(),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Comandos de teste recomendados")

    _copy_box(_gerar_comandos_release())

    st.divider()

    st.markdown("### Comandos para fechar v1.40")

    _copy_box(_gerar_comandos_git_v140())

    st.divider()

    st.markdown("### Baixar relatório de release")

    relatorio = _gerar_relatorio_release_markdown(
        contexto=contexto,
        criterios=criterios,
        score=score_release,
        classificacao=classificacao,
        leitura=leitura,
    )

    st.download_button(
        label="Baixar release candidate v1.40 (.md)",
        data=relatorio,
        file_name="release_candidate_v1_40_maquina_preco_teto.md",
        mime="text/markdown",
        key="download_release_candidate_v140",
    )

    st.markdown(
        """
        <div class="rel-disclaimer">
            <strong>Decisão estratégica:</strong> depois da v1.40, evite criar novas grandes áreas sem feedback real.
            O próximo ciclo deve ser guiado por usuários, não por suposição interna.
        </div>
        """,
        unsafe_allow_html=True,
    )