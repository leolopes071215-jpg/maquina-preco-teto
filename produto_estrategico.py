# produto_estrategico.py

from datetime import datetime
from typing import Dict, List

import streamlit as st


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v3.8.23 — Reposicionamento Estratégico do Produto
# ------------------------------------------------------------
# Este arquivo organiza a estratégia de produto, posicionamento,
# público-alvo, promessa, modelo de negócio e próximos passos.
#
# Objetivo:
# - parar expansão infinita de módulos internos
# - transformar o MVP em produto vendável
# - orientar o beta real
# - priorizar deploy e validação com usuários
# - separar produto do fundador de produto para usuário final
# ============================================================


VERSAO_PRODUTO_ESTRATEGICO = "3.8.23"


POSICIONAMENTO_OFICIAL = {
    "nome": "Máquina de Preço-Teto",
    "categoria": "Copiloto educacional de decisão para investidores",
    "frase_curta": "Pare de comprar ação no impulso. Descubra seu preço-teto antes de investir.",
    "frase_institucional": (
        "A Máquina de Preço-Teto ajuda investidores a transformar premissas financeiras "
        "em preço justo, preço-teto, margem de segurança e decisão educacional."
    ),
    "nao_e": (
        "Não é casa de análise, não é recomendação de compra, não é promessa de rentabilidade "
        "e não substitui estudo próprio."
    ),
}


PUBLICO_ALVO = [
    {
        "Segmento": "Investidor iniciante consciente",
        "Dor": "Quer investir melhor, mas não sabe quanto pagar por uma ação.",
        "Desejo": "Ter um método simples para não comprar por impulso.",
        "Oferta ideal": "Plano gratuito ou Pro básico.",
    },
    {
        "Segmento": "Investidor intermediário",
        "Dor": "Já investe, mas não registra premissas nem compara oportunidades com disciplina.",
        "Desejo": "Ter uma rotina de análise, histórico, relatórios e watchlist.",
        "Oferta ideal": "Plano Pro mensal.",
    },
    {
        "Segmento": "Estudante de finanças / mercado",
        "Dor": "Aprende valuation de forma solta, sem ferramenta prática.",
        "Desejo": "Entender a lógica por trás do preço justo e margem de segurança.",
        "Oferta ideal": "Plano educacional ou acesso beta.",
    },
    {
        "Segmento": "Criador/comunidade de investimentos",
        "Dor": "Precisa ensinar análise de forma visual, simples e replicável.",
        "Desejo": "Usar a ferramenta como apoio didático.",
        "Oferta ideal": "Plano Premium ou B2B futuro.",
    },
]


DORES_PRINCIPAIS = [
    {
        "Dor": "Não saber quanto pagar por uma ação",
        "Gravidade": "Alta",
        "Como o produto resolve": "Calcula preço justo e preço-teto com margem de segurança.",
    },
    {
        "Dor": "Comprar por emoção ou por dica",
        "Gravidade": "Alta",
        "Como o produto resolve": "Transforma a decisão em processo racional e registrado.",
    },
    {
        "Dor": "Não registrar premissas",
        "Gravidade": "Média",
        "Como o produto resolve": "Salva análise, histórico e relatório.",
    },
    {
        "Dor": "Não comparar oportunidades",
        "Gravidade": "Média",
        "Como o produto resolve": "Usa ranking, comparativo, watchlist e status educacional.",
    },
    {
        "Dor": "Achar valuation complexo demais",
        "Gravidade": "Alta",
        "Como o produto resolve": "Mostra leitura visual, explicação simples e decisão guiada.",
    },
]


PROMESSAS_PRODUTO = [
    {
        "Nível": "Promessa principal",
        "Mensagem": "Descubra o preço máximo que faz sentido pagar antes de investir.",
    },
    {
        "Nível": "Promessa emocional",
        "Mensagem": "Invista com mais disciplina e menos impulso.",
    },
    {
        "Nível": "Promessa racional",
        "Mensagem": "Transforme lucro, fluxo de caixa, múltiplos e margem de segurança em decisão.",
    },
    {
        "Nível": "Promessa educacional",
        "Mensagem": "Entenda por que uma ação parece barata, neutra ou cara dentro das suas premissas.",
    },
]


FUNCIONALIDADES_ESSENCIAIS_BETA = [
    {
        "Funcionalidade": "Análise de valuation",
        "Prioridade": "Obrigatória",
        "Motivo": "É o coração do produto.",
    },
    {
        "Funcionalidade": "Preço-teto com margem de segurança",
        "Prioridade": "Obrigatória",
        "Motivo": "É a promessa principal.",
    },
    {
        "Funcionalidade": "Status educacional",
        "Prioridade": "Obrigatória",
        "Motivo": "Traduz cálculo em decisão compreensível.",
    },
    {
        "Funcionalidade": "Relatório",
        "Prioridade": "Alta",
        "Motivo": "Aumenta percepção de valor e compartilhamento.",
    },
    {
        "Funcionalidade": "Checklist",
        "Prioridade": "Alta",
        "Motivo": "Evita decisão impulsiva.",
    },
    {
        "Funcionalidade": "Tese & Convicção",
        "Prioridade": "Média",
        "Motivo": "Ajuda o usuário a refletir além do número.",
    },
    {
        "Funcionalidade": "Feedback Beta",
        "Prioridade": "Obrigatória",
        "Motivo": "Sem feedback real, não existe validação.",
    },
]


FUNCIONALIDADES_ESCONDIDAS_FUNDADOR = [
    "Core Engine",
    "Compatibilidade Core",
    "Motor Adapter",
    "Motor Controlado",
    "Auditoria Motor Principal",
    "Fallback Motor",
    "Logs Motor",
    "Saúde Motor",
    "Decisão Core",
    "Promoção Core",
    "Negócio",
    "Marketing",
    "Conteúdo",
    "Landing Page",
    "Lançamento",
    "CRM Beta",
    "Painel Beta",
    "Fase 3",
    "Métricas Fase 3",
    "Plano Fase 4",
    "Arquitetura Fase 4",
    "Dados",
    "UX",
]


MODELO_MONETIZACAO = [
    {
        "Plano": "Gratuito",
        "Preço sugerido": "R$ 0",
        "Entrega": "Análises limitadas, relatório simples e educação básica.",
        "Objetivo": "Aquisição e aprendizado.",
    },
    {
        "Plano": "Pro",
        "Preço sugerido": "R$ 19 a R$ 39/mês",
        "Entrega": "Análises ilimitadas, histórico, relatórios premium, watchlist e comparativo.",
        "Objetivo": "Primeira monetização real.",
    },
    {
        "Plano": "Premium",
        "Preço sugerido": "R$ 59 a R$ 97/mês",
        "Entrega": "Multiativos, cenários, tese guiada, carteira, exportações e alertas futuros.",
        "Objetivo": "Usuário mais sério e maior LTV.",
    },
    {
        "Plano": "B2B Futuro",
        "Preço sugerido": "Sob consulta",
        "Entrega": "Uso por comunidades, educadores, clubes e assessores independentes.",
        "Objetivo": "Escala futura.",
    },
]


EXPERIENCIA_IDEAL_USUARIO_BETA = [
    {
        "Etapa": "1",
        "Tela/ação": "Entrar no app",
        "Experiência desejada": "Entender em menos de 10 segundos o que o produto faz.",
    },
    {
        "Etapa": "2",
        "Tela/ação": "Escolher ou preencher ativo",
        "Experiência desejada": "Sentir que está fazendo uma análise real, sem complexidade excessiva.",
    },
    {
        "Etapa": "3",
        "Tela/ação": "Ver preço-teto",
        "Experiência desejada": "Ter um momento de clareza: 'agora eu sei o preço máximo racional'.",
    },
    {
        "Etapa": "4",
        "Tela/ação": "Ler decisão",
        "Experiência desejada": "Entender se o ativo está em zona de compra, neutra ou aguarde.",
    },
    {
        "Etapa": "5",
        "Tela/ação": "Baixar relatório",
        "Experiência desejada": "Sentir que recebeu algo premium e útil.",
    },
    {
        "Etapa": "6",
        "Tela/ação": "Enviar feedback",
        "Experiência desejada": "Contribuir com a evolução do produto sem fricção.",
    },
]


NAO_CONSTRUIR_AGORA = [
    {
        "Item": "Mais painéis técnicos internos",
        "Motivo": "Já temos governança técnica suficiente para o MVP.",
        "Risco se insistir": "Virar fuga do mercado e atrasar validação real.",
    },
    {
        "Item": "Funcionalidades avançadas sem usuários",
        "Motivo": "Ainda não sabemos o que usuários reais realmente valorizam.",
        "Risco se insistir": "Construir coisas que ninguém usa.",
    },
    {
        "Item": "Complexidade visual no modo beta",
        "Motivo": "Usuário comum precisa de clareza, não de painel de fundador.",
        "Risco se insistir": "Aumentar abandono.",
    },
    {
        "Item": "Pagamento antes de deploy e feedback",
        "Motivo": "Primeiro precisamos validar se usuários entendem e desejam a solução.",
        "Risco se insistir": "Vender algo sem fricção resolvida.",
    },
    {
        "Item": "Backend/API antes de limpar UX",
        "Motivo": "A experiência do usuário ainda precisa ficar mais simples.",
        "Risco se insistir": "Escalar um produto confuso.",
    },
]


ROADMAP_FASE4 = [
    {
        "Fase": "4.1",
        "Nome": "Congelamento estratégico do MVP",
        "Status": "Atual",
        "Objetivo": "Parar expansão desnecessária e definir foco de validação.",
    },
    {
        "Fase": "4.2",
        "Nome": "Limpeza do Modo Usuário Beta",
        "Status": "Próxima",
        "Objetivo": "Transformar o app em experiência simples, bonita e testável.",
    },
    {
        "Fase": "4.3",
        "Nome": "Deploy público",
        "Status": "Pendente",
        "Objetivo": "Colocar o produto online para usuários reais.",
    },
    {
        "Fase": "4.4",
        "Nome": "Beta real com 5 a 10 usuários",
        "Status": "Pendente",
        "Objetivo": "Observar uso, coletar feedback e validar dor.",
    },
    {
        "Fase": "4.5",
        "Nome": "Ajustes pós-feedback",
        "Status": "Pendente",
        "Objetivo": "Corrigir fricções e melhorar percepção de valor.",
    },
    {
        "Fase": "4.6",
        "Nome": "Banco de dados real",
        "Status": "Pendente",
        "Objetivo": "Persistir usuários, análises, feedbacks e histórico de forma robusta.",
    },
    {
        "Fase": "4.7",
        "Nome": "Login e planos",
        "Status": "Pendente",
        "Objetivo": "Preparar SaaS com controle de acesso.",
    },
    {
        "Fase": "4.8",
        "Nome": "Pagamento",
        "Status": "Futuro",
        "Objetivo": "Monetizar apenas após sinais reais de valor.",
    },
]


PROXIMAS_ACOES_OBRIGATORIAS = [
    {
        "Ordem": "1",
        "Ação": "Integrar este painel ao Modo Fundador",
        "Resultado esperado": "Ter uma central de direção estratégica.",
    },
    {
        "Ordem": "2",
        "Ação": "Redesenhar Modo Usuário Beta",
        "Resultado esperado": "Experiência simples, premium e vendável.",
    },
    {
        "Ordem": "3",
        "Ação": "Reduzir ruído visual e excesso de abas para usuário comum",
        "Resultado esperado": "Mais clareza e menor abandono.",
    },
    {
        "Ordem": "4",
        "Ação": "Preparar deploy",
        "Resultado esperado": "App acessível por link.",
    },
    {
        "Ordem": "5",
        "Ação": "Chamar 5 a 10 usuários para testar",
        "Resultado esperado": "Feedback real de mercado.",
    },
]


def _injetar_css_produto_estrategico() -> None:
    st.markdown(
        """
        <style>
            .pe-hero {
                padding: 1.8rem 1.9rem;
                border-radius: 30px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    radial-gradient(circle at top left, rgba(214, 181, 109, 0.25), transparent 30%),
                    radial-gradient(circle at bottom right, rgba(36, 128, 91, 0.24), transparent 34%),
                    linear-gradient(135deg, rgba(8, 15, 27, 0.99), rgba(5, 9, 18, 0.99));
                box-shadow: 0 18px 55px rgba(0, 0, 0, 0.34);
                margin-bottom: 1.25rem;
            }

            .pe-eyebrow {
                color: #d6b56d;
                font-size: 0.78rem;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.35rem;
            }

            .pe-title {
                color: #f4f7fb;
                font-size: 2.15rem;
                font-weight: 900;
                margin-bottom: 0.45rem;
                line-height: 1.14;
            }

            .pe-subtitle {
                color: rgba(244, 247, 251, 0.76);
                font-size: 1rem;
                line-height: 1.62;
                max-width: 1080px;
            }

            .pe-card {
                padding: 1.1rem 1.15rem;
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.035);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.18);
                height: 100%;
            }

            .pe-card-label {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .pe-card-value {
                color: #f4f7fb;
                font-size: 1.18rem;
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .pe-card-note {
                color: rgba(244, 247, 251, 0.68);
                font-size: 0.87rem;
                line-height: 1.47;
            }

            .pe-highlight {
                padding: 0.95rem 1rem;
                border-radius: 16px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.92rem;
                line-height: 1.55;
                margin-bottom: 0.7rem;
            }

            .pe-disclaimer {
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
        <div class="pe-card">
            <div class="pe-card-label">{label}</div>
            <div class="pe-card-value">{value}</div>
            <div class="pe-card-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _tabela_para_markdown(tabela: List[Dict[str, str]]) -> str:
    if len(tabela) == 0:
        return ""

    colunas = list(tabela[0].keys())

    cabecalho = "| " + " | ".join(colunas) + " |"
    separador = "| " + " | ".join(["---"] * len(colunas)) + " |"

    linhas = []

    for item in tabela:
        linhas.append(
            "| " + " | ".join([str(item.get(coluna, "")) for coluna in colunas]) + " |"
        )

    return "\n".join([cabecalho, separador] + linhas)


def gerar_markdown_produto_estrategico() -> str:
    return f"""# Reposicionamento Estratégico do Produto

Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Produto

**Nome:** {POSICIONAMENTO_OFICIAL["nome"]}  
**Categoria:** {POSICIONAMENTO_OFICIAL["categoria"]}  
**Frase curta:** {POSICIONAMENTO_OFICIAL["frase_curta"]}  

## Frase institucional

{POSICIONAMENTO_OFICIAL["frase_institucional"]}

## O que não é

{POSICIONAMENTO_OFICIAL["nao_e"]}

## Público-alvo

{_tabela_para_markdown(PUBLICO_ALVO)}

## Dores principais

{_tabela_para_markdown(DORES_PRINCIPAIS)}

## Promessas do produto

{_tabela_para_markdown(PROMESSAS_PRODUTO)}

## Funcionalidades essenciais para beta

{_tabela_para_markdown(FUNCIONALIDADES_ESSENCIAIS_BETA)}

## Funcionalidades que devem ficar escondidas no Modo Fundador

{", ".join(FUNCIONALIDADES_ESCONDIDAS_FUNDADOR)}

## Modelo de monetização

{_tabela_para_markdown(MODELO_MONETIZACAO)}

## Experiência ideal do usuário beta

{_tabela_para_markdown(EXPERIENCIA_IDEAL_USUARIO_BETA)}

## O que não construir agora

{_tabela_para_markdown(NAO_CONSTRUIR_AGORA)}

## Roadmap Fase 4

{_tabela_para_markdown(ROADMAP_FASE4)}

## Próximas ações obrigatórias

{_tabela_para_markdown(PROXIMAS_ACOES_OBRIGATORIAS)}

## Regra estratégica

A partir desta versão, o projeto deve parar de adicionar módulos internos sem validação.
O foco passa a ser clareza de produto, experiência do usuário beta, deploy e feedback real.
"""


def executar_autoteste_produto_estrategico() -> List[Dict[str, str]]:
    testes = []

    testes.append(
        {
            "teste": "posicionamento_tem_nome",
            "status": "OK" if POSICIONAMENTO_OFICIAL.get("nome") else "FALHA",
            "detalhe": POSICIONAMENTO_OFICIAL.get("nome", ""),
        }
    )

    testes.append(
        {
            "teste": "publico_alvo_definido",
            "status": "OK" if len(PUBLICO_ALVO) >= 3 else "FALHA",
            "detalhe": f"Segmentos: {len(PUBLICO_ALVO)}",
        }
    )

    testes.append(
        {
            "teste": "dores_principais_definidas",
            "status": "OK" if len(DORES_PRINCIPAIS) >= 3 else "FALHA",
            "detalhe": f"Dores: {len(DORES_PRINCIPAIS)}",
        }
    )

    testes.append(
        {
            "teste": "funcionalidades_beta_definidas",
            "status": "OK" if len(FUNCIONALIDADES_ESSENCIAIS_BETA) >= 5 else "FALHA",
            "detalhe": f"Funcionalidades: {len(FUNCIONALIDADES_ESSENCIAIS_BETA)}",
        }
    )

    testes.append(
        {
            "teste": "roadmap_fase4_definido",
            "status": "OK" if len(ROADMAP_FASE4) >= 5 else "FALHA",
            "detalhe": f"Etapas: {len(ROADMAP_FASE4)}",
        }
    )

    markdown = gerar_markdown_produto_estrategico()

    testes.append(
        {
            "teste": "markdown_produto_gerado",
            "status": "OK" if "# Reposicionamento Estratégico do Produto" in markdown else "FALHA",
            "detalhe": "Relatório markdown criado.",
        }
    )

    return testes


def renderizar_produto_estrategico() -> None:
    _injetar_css_produto_estrategico()

    st.markdown(
        """
        <div class="pe-hero">
            <div class="pe-eyebrow">v3.8.23 — Estratégia de produto</div>
            <div class="pe-title">Reposicionamento Estratégico</div>
            <div class="pe-subtitle">
                A partir daqui, a Máquina de Preço-Teto deixa de ser apenas um MVP técnico
                e passa a ser guiada como produto vendável, testável e preparado para beta real.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="pe-highlight">
            A regra agora é simples: menos expansão interna, mais clareza para o usuário,
            deploy público, feedback real e validação comercial.
        </div>
        """,
        unsafe_allow_html=True,
    )

    testes = executar_autoteste_produto_estrategico()

    st.markdown("### Diagnóstico estratégico")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Versão", VERSAO_PRODUTO_ESTRATEGICO)

    with col_2:
        st.metric("Públicos", len(PUBLICO_ALVO))

    with col_3:
        st.metric("Dores mapeadas", len(DORES_PRINCIPAIS))

    with col_4:
        st.metric("Status", "OK" if all(t["status"] == "OK" for t in testes) else "FALHA")

    if all(t["status"] == "OK" for t in testes):
        st.success("Estratégia mínima de produto validada.")
    else:
        st.error("Existem falhas na estrutura estratégica.")

    with st.expander("Ver autotestes"):
        st.dataframe(testes, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Posicionamento oficial")

    col_p1, col_p2, col_p3 = st.columns(3)

    with col_p1:
        _card(
            "Nome",
            POSICIONAMENTO_OFICIAL["nome"],
            "Marca principal do produto.",
        )

    with col_p2:
        _card(
            "Categoria",
            POSICIONAMENTO_OFICIAL["categoria"],
            "Como o mercado deve entender o produto.",
        )

    with col_p3:
        _card(
            "Promessa curta",
            "Preço-teto antes de investir",
            "Mensagem simples para aquisição.",
        )

    st.info(POSICIONAMENTO_OFICIAL["frase_curta"])
    st.write(POSICIONAMENTO_OFICIAL["frase_institucional"])
    st.warning(POSICIONAMENTO_OFICIAL["nao_e"])

    st.divider()

    st.markdown("### Público-alvo")

    st.dataframe(PUBLICO_ALVO, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Dores principais")

    st.dataframe(DORES_PRINCIPAIS, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Promessas do produto")

    st.dataframe(PROMESSAS_PRODUTO, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Funcionalidades essenciais para o beta")

    st.dataframe(FUNCIONALIDADES_ESSENCIAIS_BETA, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Funcionalidades que devem ficar escondidas do usuário comum")

    st.warning(
        "Essas áreas são importantes para o fundador, mas não devem aparecer para o usuário beta."
    )

    st.write(", ".join(FUNCIONALIDADES_ESCONDIDAS_FUNDADOR))

    st.divider()

    st.markdown("### Modelo de monetização provável")

    st.dataframe(MODELO_MONETIZACAO, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Experiência ideal do usuário beta")

    st.dataframe(EXPERIENCIA_IDEAL_USUARIO_BETA, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### O que NÃO construir agora")

    st.error(
        "Esta é a parte mais importante: o projeto deve parar de criar complexidade interna sem validação."
    )

    st.dataframe(NAO_CONSTRUIR_AGORA, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Roadmap da Fase 4")

    st.dataframe(ROADMAP_FASE4, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Próximas ações obrigatórias")

    st.dataframe(PROXIMAS_ACOES_OBRIGATORIAS, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Download estratégico")

    st.download_button(
        label="Baixar relatório estratégico do produto (.md)",
        data=gerar_markdown_produto_estrategico(),
        file_name="relatorio_produto_estrategico.md",
        mime="text/markdown",
        key="download_produto_estrategico",
    )

    st.markdown(
        """
        <div class="pe-disclaimer">
            <strong>Decisão de fundador:</strong> a partir daqui, o foco deve ser transformar
            o Modo Usuário Beta em uma experiência simples, bonita e validável. Mais módulos internos
            só devem ser criados se forem necessários para deploy, feedback, retenção ou monetização.
        </div>
        """,
        unsafe_allow_html=True,
    )