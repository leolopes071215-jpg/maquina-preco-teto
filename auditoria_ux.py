# auditoria_ux.py

from datetime import datetime
from typing import Any, Dict, List

import streamlit as st


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v1.38 — Auditoria UX e Polimento Premium
# ------------------------------------------------------------
# Esta tela avalia a experiência do usuário antes da Fase 2.
#
# Objetivo:
# - medir clareza, simplicidade e prontidão visual
# - identificar excesso de complexidade
# - orientar ajustes antes de enviar para usuários reais
# - consolidar checklist de polimento premium
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


def _extrair_contexto_ux() -> Dict[str, Any]:
    valuation = _safe_get_dict("resultado_valuation")
    onboarding = _safe_get_dict("resultado_onboarding")
    navegacao = _safe_get_dict("resultado_navegacao_simplificada")
    negocio = _safe_get_dict("resultado_dashboard_negocio")
    lancamento = _safe_get_dict("resultado_lancamento_beta")
    persistencia = _safe_get_dict("resultado_persistencia_dados")

    modo_exibicao = st.session_state.get("modo_exibicao_app", "Fundador")

    return {
        "modo_exibicao": modo_exibicao,
        "empresa": valuation.get("empresa", "N/D"),
        "ticker": valuation.get("ticker", "N/D"),
        "status": valuation.get("status", valuation.get("status_valuation", "N/D")),
        "perfil_onboarding": onboarding.get("perfil", "N/D"),
        "objetivo_onboarding": onboarding.get("objetivo", "N/D"),
        "objetivo_navegacao": navegacao.get("objetivo", "N/D"),
        "score_tracao": negocio.get("score_tracao", 0),
        "score_lancamento": lancamento.get("score_lancamento", 0),
        "arquivos_existentes": persistencia.get("arquivos_existentes", 0),
        "gitignore_pendente": persistencia.get("gitignore_pendente", 0),
    }


def _gerar_criterios_ux(contexto: Dict[str, Any]) -> List[Dict[str, str]]:
    modo = _fmt_texto(contexto.get("modo_exibicao"))
    perfil_onboarding = _fmt_texto(contexto.get("perfil_onboarding"))
    objetivo_navegacao = _fmt_texto(contexto.get("objetivo_navegacao"))
    score_tracao = _safe_int(contexto.get("score_tracao"))
    score_lancamento = _safe_int(contexto.get("score_lancamento"))
    gitignore_pendente = _safe_int(contexto.get("gitignore_pendente"))

    criterios = [
        {
            "Critério": "Modo de exibição ativo",
            "Status": "OK" if modo in ["Usuário Beta", "Investidor Completo", "Fundador"] else "Pendente",
            "Leitura": "O app já consegue separar experiência de usuário e experiência interna.",
        },
        {
            "Critério": "Navegação simplificada",
            "Status": "OK" if objetivo_navegacao != "N/D" else "Atenção",
            "Leitura": "A central de navegação ajuda o usuário a escolher um caminho.",
        },
        {
            "Critério": "Onboarding configurado",
            "Status": "OK" if perfil_onboarding != "N/D" else "Atenção",
            "Leitura": "O onboarding reduz confusão para usuários novos.",
        },
        {
            "Critério": "Produto com aviso educacional",
            "Status": "OK",
            "Leitura": "O app deixa claro que não é recomendação de compra ou venda.",
        },
        {
            "Critério": "Separação de áreas internas",
            "Status": "OK" if modo == "Fundador" else "OK",
            "Leitura": "Usuários comuns não precisam ver marketing, dados e lançamento.",
        },
        {
            "Critério": "Tração mínima",
            "Status": "OK" if score_tracao >= 50 else "Atenção",
            "Leitura": "Quanto maior o score, mais preparado o produto fica para teste real.",
        },
        {
            "Critério": "Preparação para lançamento",
            "Status": "OK" if score_lancamento >= 50 else "Atenção",
            "Leitura": "O lançamento beta precisa de checklist, plano e tarefas.",
        },
        {
            "Critério": "Governança de dados",
            "Status": "OK" if gitignore_pendente == 0 else "Pendente",
            "Leitura": "Antes de usuários reais, CSVs sensíveis precisam estar protegidos.",
        },
    ]

    return criterios


def _calcular_score_ux(criterios: List[Dict[str, str]]) -> int:
    if len(criterios) == 0:
        return 0

    pontos = 0

    for criterio in criterios:
        status = criterio.get("Status", "")

        if status == "OK":
            pontos += 12
        elif status == "Atenção":
            pontos += 6
        else:
            pontos += 0

    return min(100, pontos)


def _classificar_ux(score: int) -> str:
    if score >= 85:
        return "UX pronta para beta controlado"
    if score >= 70:
        return "UX boa, com pequenos ajustes"
    if score >= 55:
        return "UX funcional, mas ainda confusa"
    if score >= 40:
        return "UX precisa de simplificação"
    return "UX ainda frágil para usuários reais"


def _gerar_leitura_ux(score: int) -> str:
    if score >= 85:
        return (
            "A experiência está madura o suficiente para um beta controlado. "
            "O foco agora deve ser observar onde usuários reais travam, não adicionar muitas funções novas."
        )

    if score >= 70:
        return (
            "A experiência está boa, mas ainda pode melhorar em clareza, hierarquia e redução de ruído. "
            "É possível testar com poucos usuários, acompanhando feedback de perto."
        )

    if score >= 55:
        return (
            "O produto funciona, mas ainda pode parecer complexo para usuários novos. "
            "Antes de ampliar o beta, priorize simplicidade, instruções e fluxo mínimo."
        )

    if score >= 40:
        return (
            "A experiência ainda exige esforço do usuário. "
            "O risco é a pessoa não perceber valor porque se perde entre módulos."
        )

    return (
        "Ainda não é recomendado enviar para usuários reais sem orientação direta. "
        "A experiência precisa ser simplificada e explicada melhor."
    )


def _gerar_checklist_polimento() -> List[Dict[str, str]]:
    return [
        {
            "Área": "Primeira impressão",
            "Pergunta": "O usuário entende em até 30 segundos o que o app faz?",
            "Ação recomendada": "Deixar Produto, Navegação e Onboarding muito claros.",
            "Prioridade": "Alta",
        },
        {
            "Área": "Excesso de abas",
            "Pergunta": "O usuário beta está vendo apenas o necessário?",
            "Ação recomendada": "Usar Modo Usuário Beta ao enviar o app para teste.",
            "Prioridade": "Muito alta",
        },
        {
            "Área": "Valuation",
            "Pergunta": "O usuário entende preço atual, preço justo e preço-teto?",
            "Ação recomendada": "Manter explicações curtas perto dos números principais.",
            "Prioridade": "Alta",
        },
        {
            "Área": "Relatórios",
            "Pergunta": "A entrega final parece valiosa?",
            "Ação recomendada": "Incentivar o usuário a baixar e revisar o relatório.",
            "Prioridade": "Alta",
        },
        {
            "Área": "Feedback",
            "Pergunta": "O usuário sabe que deve preencher feedback no final?",
            "Ação recomendada": "Reforçar CTA para Feedback Beta no fluxo mínimo.",
            "Prioridade": "Muito alta",
        },
        {
            "Área": "Avisos educacionais",
            "Pergunta": "Está claro que não é recomendação de investimento?",
            "Ação recomendada": "Manter avisos sem deixar a experiência pesada demais.",
            "Prioridade": "Muito alta",
        },
        {
            "Área": "Mobile",
            "Pergunta": "O app fica minimamente usável no celular?",
            "Ação recomendada": "Testar no celular e observar tabelas muito largas.",
            "Prioridade": "Média",
        },
        {
            "Área": "Fundador",
            "Pergunta": "As áreas internas estão escondidas do usuário comum?",
            "Ação recomendada": "Usar Fundador apenas para gestão do negócio.",
            "Prioridade": "Alta",
        },
    ]


def _gerar_jornada_beta_ideal() -> List[Dict[str, str]]:
    return [
        {
            "Passo": "1",
            "Tela": "Produto",
            "Objetivo": "Entender a promessa educacional.",
            "Tempo ideal": "1 minuto",
        },
        {
            "Passo": "2",
            "Tela": "Navegação",
            "Objetivo": "Saber qual caminho seguir.",
            "Tempo ideal": "1 minuto",
        },
        {
            "Passo": "3",
            "Tela": "Onboarding",
            "Objetivo": "Escolher perfil e objetivo.",
            "Tempo ideal": "2 minutos",
        },
        {
            "Passo": "4",
            "Tela": "Valuation",
            "Objetivo": "Ver o motor principal.",
            "Tempo ideal": "4 minutos",
        },
        {
            "Passo": "5",
            "Tela": "Tese & Convicção",
            "Objetivo": "Perceber que número precisa de contexto.",
            "Tempo ideal": "3 minutos",
        },
        {
            "Passo": "6",
            "Tela": "Relatórios",
            "Objetivo": "Ver a entrega final.",
            "Tempo ideal": "3 minutos",
        },
        {
            "Passo": "7",
            "Tela": "Feedback Beta",
            "Objetivo": "Registrar percepção real.",
            "Tempo ideal": "3 minutos",
        },
        {
            "Passo": "8",
            "Tela": "Oferta Beta",
            "Objetivo": "Medir interesse e lista de espera.",
            "Tempo ideal": "2 minutos",
        },
    ]


def _gerar_riscos_ux() -> List[Dict[str, str]]:
    return [
        {
            "Risco": "Usuário se perder nas abas",
            "Impacto": "Não percebe valor mesmo com produto bom.",
            "Prevenção": "Enviar em Modo Usuário Beta e orientar fluxo mínimo.",
        },
        {
            "Risco": "Confundir status educacional com recomendação",
            "Impacto": "Risco regulatório e expectativa errada.",
            "Prevenção": "Manter avisos educacionais e linguagem cuidadosa.",
        },
        {
            "Risco": "Achar o app técnico demais",
            "Impacto": "Iniciante abandona cedo.",
            "Prevenção": "Usar Onboarding e explicações simples.",
        },
        {
            "Risco": "Não preencher feedback",
            "Impacto": "Você perde dados de validação.",
            "Prevenção": "Pedir feedback no convite e no final da jornada.",
        },
        {
            "Risco": "Testar com público errado",
            "Impacto": "Feedback distorcido.",
            "Prevenção": "Separar iniciante, intermediário, avançado e criador de conteúdo.",
        },
    ]


def _gerar_texto_convite_beta() -> str:
    return """Estou testando uma plataforma educacional que estou construindo chamada Máquina de Preço-Teto.

A ideia é ajudar investidores a organizar análise de ativos com mais método: valuation, preço-teto, margem de segurança, tese, riscos, checklist, relatório e watchlist.

Não é recomendação de compra ou venda. É uma ferramenta de estudo e organização.

Quero que você teste por alguns minutos e me diga:
1. Se entendeu a proposta.
2. Onde travou.
3. Se achou útil.
4. Se pagaria por uma versão melhorada.
5. O que precisa melhorar.

Fluxo recomendado:
Produto → Navegação → Onboarding → Valuation → Relatórios → Feedback Beta.

Depois de testar, preencha a aba Feedback Beta dentro do app."""


def _gerar_relatorio_ux_markdown(
    contexto: Dict[str, Any],
    score: int,
    classificacao: str,
    leitura: str,
    criterios: List[Dict[str, str]],
) -> str:
    linhas_criterios = "\n".join(
        [
            f"| {item['Critério']} | {item['Status']} | {item['Leitura']} |"
            for item in criterios
        ]
    )

    return f"""# Auditoria UX — Máquina de Preço-Teto

Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Resultado

**Score UX:** {score}/100  
**Classificação:** {classificacao}

## Leitura

{leitura}

## Contexto

- Modo de exibição: {contexto["modo_exibicao"]}
- Empresa ativa: {contexto["empresa"]}
- Ticker: {contexto["ticker"]}
- Status valuation: {contexto["status"]}
- Score de tração: {contexto["score_tracao"]}
- Score de lançamento: {contexto["score_lancamento"]}

## Critérios avaliados

| Critério | Status | Leitura |
|---|---|---|
{linhas_criterios}

## Recomendação

Antes da Fase 2, priorize clareza, simplicidade, modo usuário beta, feedback estruturado e proteção de dados.
"""


def _injetar_css_ux() -> None:
    st.markdown(
        """
        <style>
            .ux-hero {
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

            .ux-eyebrow {
                color: #d6b56d;
                font-size: 0.78rem;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.35rem;
            }

            .ux-title {
                color: #f4f7fb;
                font-size: 2.1rem;
                font-weight: 900;
                margin-bottom: 0.45rem;
                line-height: 1.14;
            }

            .ux-subtitle {
                color: rgba(244, 247, 251, 0.76);
                font-size: 1rem;
                line-height: 1.62;
                max-width: 1080px;
            }

            .ux-card {
                padding: 1.1rem 1.15rem;
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.035);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.18);
                height: 100%;
            }

            .ux-card-label {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .ux-card-value {
                color: #f4f7fb;
                font-size: 1.22rem;
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .ux-card-note {
                color: rgba(244, 247, 251, 0.68);
                font-size: 0.87rem;
                line-height: 1.47;
            }

            .ux-highlight {
                padding: 0.95rem 1rem;
                border-radius: 16px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.92rem;
                line-height: 1.55;
                margin-bottom: 0.7rem;
            }

            .ux-copy {
                padding: 1rem 1.05rem;
                border-radius: 18px;
                background: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(255, 255, 255, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.92rem;
                line-height: 1.58;
                white-space: pre-wrap;
                margin-bottom: 0.85rem;
            }

            .ux-disclaimer {
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
        <div class="ux-card">
            <div class="ux-card-label">{label}</div>
            <div class="ux-card-value">{value}</div>
            <div class="ux-card-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _copy_box(texto: str) -> None:
    st.markdown(
        f"""
        <div class="ux-copy">{texto}</div>
        """,
        unsafe_allow_html=True,
    )


def renderizar_auditoria_ux() -> None:
    """
    Renderiza a Central de Auditoria UX.
    """
    _injetar_css_ux()

    contexto = _extrair_contexto_ux()
    criterios = _gerar_criterios_ux(contexto)
    score_ux = _calcular_score_ux(criterios)
    classificacao = _classificar_ux(score_ux)
    leitura = _gerar_leitura_ux(score_ux)

    st.session_state["resultado_auditoria_ux"] = {
        "score_ux": score_ux,
        "classificacao": classificacao,
        "leitura": leitura,
        **contexto,
    }

    st.markdown(
        """
        <div class="ux-hero">
            <div class="ux-eyebrow">Polimento premium</div>
            <div class="ux-title">Auditoria UX e Prontidão para Beta</div>
            <div class="ux-subtitle">
                Avalie se a experiência está clara, simples e segura para usuários reais.
                Esta central ajuda a reduzir confusão, melhorar primeira impressão e preparar o app para a Fase 2.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="ux-highlight">
            Nesta fase, o maior risco não é faltar função. É o usuário não entender o valor por excesso de complexidade.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Diagnóstico UX")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Score UX", f"{score_ux}/100")

    with col_2:
        st.metric("Classificação", classificacao)

    with col_3:
        st.metric("Modo atual", contexto["modo_exibicao"])

    with col_4:
        st.metric("Status valuation", contexto["status"])

    st.progress(score_ux / 100)

    if score_ux >= 85:
        st.success(leitura)
    elif score_ux >= 55:
        st.warning(leitura)
    else:
        st.error(leitura)

    st.divider()

    st.markdown("### Critérios avaliados")

    st.dataframe(
        criterios,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Checklist de polimento premium")

    st.dataframe(
        _gerar_checklist_polimento(),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Jornada beta ideal")

    st.dataframe(
        _gerar_jornada_beta_ideal(),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Riscos de UX antes da Fase 2")

    st.dataframe(
        _gerar_riscos_ux(),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Texto pronto para convite beta")

    texto_convite = _gerar_texto_convite_beta()
    _copy_box(texto_convite)

    st.divider()

    st.markdown("### Baixar auditoria UX")

    relatorio = _gerar_relatorio_ux_markdown(
        contexto=contexto,
        score=score_ux,
        classificacao=classificacao,
        leitura=leitura,
        criterios=criterios,
    )

    st.download_button(
        label="Baixar auditoria UX (.md)",
        data=relatorio,
        file_name="auditoria_ux_maquina_preco_teto.md",
        mime="text/markdown",
        key="download_auditoria_ux",
    )

    st.markdown(
        """
        <div class="ux-disclaimer">
            <strong>Nota estratégica:</strong> antes da Fase 2, evite adicionar funcionalidades grandes.
            O foco agora é clareza, fluxo, confiança, feedback e teste com usuários reais.
        </div>
        """,
        unsafe_allow_html=True,
    )