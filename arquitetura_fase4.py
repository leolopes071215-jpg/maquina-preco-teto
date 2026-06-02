# arquitetura_fase4.py

import csv
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List

import streamlit as st


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v3.7 — Blueprint Técnico da Fase 4
# ------------------------------------------------------------
# Esta tela transforma a visão de migração em arquitetura real.
#
# Objetivo:
# - desenhar a arquitetura profissional do web app
# - organizar frontend, backend, banco, login, pagamento e deploy
# - definir contratos iniciais de API
# - estruturar o roadmap técnico sem abandonar a validação
# - evitar reescrita caótica do MVP
# ============================================================


CAMINHO_CLIENTES_BETA = Path("clientes_beta.csv")
CAMINHO_SUPORTE_BETA = Path("suporte_beta.csv")
CAMINHO_RETENCAO_BETA = Path("retencao_beta.csv")
CAMINHO_METRICAS_FASE3 = Path("metricas_fase3.csv")
CAMINHO_DECISOES_FASE3 = Path("decisoes_fase3.csv")


def _carregar_csv(caminho: Path) -> List[Dict[str, str]]:
    if not caminho.exists():
        return []

    try:
        with open(caminho, "r", newline="", encoding="utf-8") as arquivo:
            leitor = csv.DictReader(arquivo)
            return [dict(linha) for linha in leitor]
    except Exception:
        return []


def _safe_float(valor: Any, default: float = 0.0) -> float:
    try:
        texto = str(valor).replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
        return float(texto)
    except (TypeError, ValueError):
        return default


def _fmt_moeda(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _contar(registros: List[Dict[str, str]], campo: str, valor: str) -> int:
    return len([registro for registro in registros if registro.get(campo) == valor])


def _media_campo(registros: List[Dict[str, str]], campo: str) -> float:
    valores = []

    for registro in registros:
        valor = _safe_float(registro.get(campo))

        if valor >= 0:
            valores.append(valor)

    if len(valores) == 0:
        return 0.0

    return mean(valores)


def _clientes_pagos(clientes: List[Dict[str, str]]) -> int:
    return _contar(clientes, "status_pagamento", "Pago")


def _clientes_ativos(clientes: List[Dict[str, str]]) -> int:
    status_ativos = ["Ativo", "Em onboarding", "Precisa de suporte", "Em risco"]

    return len(
        [
            cliente for cliente in clientes
            if cliente.get("status_pagamento") == "Pago"
            and cliente.get("status_cliente") in status_ativos
        ]
    )


def _receita_real(clientes: List[Dict[str, str]]) -> float:
    total = 0.0

    for cliente in clientes:
        if cliente.get("status_pagamento") == "Pago":
            total += _safe_float(cliente.get("valor_pago"))

    return total


def _mrr_estimado(clientes: List[Dict[str, str]]) -> float:
    total = 0.0

    for cliente in clientes:
        if cliente.get("status_pagamento") != "Pago":
            continue

        valor = _safe_float(cliente.get("valor_pago"))
        periodicidade = cliente.get("periodicidade", "")

        if periodicidade == "Mensal":
            total += valor
        elif periodicidade == "Trimestral":
            total += valor / 3
        elif periodicidade == "Anual":
            total += valor / 12

    return total


def _tickets_abertos(suporte: List[Dict[str, str]]) -> int:
    status_fechados = ["Resolvido", "Fechado", "Virou melhoria de produto"]

    return len(
        [
            ticket for ticket in suporte
            if ticket.get("status_atendimento") not in status_fechados
        ]
    )


def _tickets_criticos(suporte: List[Dict[str, str]]) -> int:
    return len(
        [
            ticket for ticket in suporte
            if ticket.get("prioridade") == "Crítica"
            or ticket.get("risco_cancelamento") == "Crítico"
            or ticket.get("impacto_cliente") == "Impede o uso"
        ]
    )


def _nps_medio(retencao: List[Dict[str, str]]) -> float:
    return _media_campo(retencao, "nps")


def _renovacoes(retencao: List[Dict[str, str]]) -> int:
    return _contar(retencao, "status_renovacao", "Renovou") + _contar(
        retencao,
        "status_cliente",
        "Renovou",
    )


def _cancelamentos(retencao: List[Dict[str, str]]) -> int:
    return _contar(retencao, "status_cliente", "Cancelado") + _contar(
        retencao,
        "status_renovacao",
        "Não renovou",
    )


def _ultima_decisao(decisoes: List[Dict[str, str]]) -> str:
    if len(decisoes) == 0:
        return "Sem decisão registrada"

    return decisoes[-1].get("decisao", "Sem decisão registrada")


def _score_prontidao_arquitetura(
    clientes: List[Dict[str, str]],
    suporte: List[Dict[str, str]],
    retencao: List[Dict[str, str]],
    metricas: List[Dict[str, str]],
    decisoes: List[Dict[str, str]],
) -> int:
    pontos = 0.0

    clientes_pagos = _clientes_pagos(clientes)
    clientes_ativos = _clientes_ativos(clientes)
    receita = _receita_real(clientes)
    mrr = _mrr_estimado(clientes)
    nps = _nps_medio(retencao)
    tickets_criticos = _tickets_criticos(suporte)
    tickets_abertos = _tickets_abertos(suporte)
    renovacoes = _renovacoes(retencao)
    cancelamentos = _cancelamentos(retencao)

    pontos += min(clientes_pagos * 10.0, 30)
    pontos += min(clientes_ativos * 8.0, 20)
    pontos += min(receita / 10, 15)
    pontos += min(mrr / 10, 15)

    if nps >= 7:
        pontos += 12

    if nps >= 8:
        pontos += 10

    pontos += min(renovacoes * 12.0, 24)

    if len(metricas) > 0:
        pontos += 8

    if len(decisoes) > 0:
        pontos += 8

    pontos -= min(tickets_criticos * 18.0, 36)
    pontos -= min(tickets_abertos * 4.0, 20)
    pontos -= min(cancelamentos * 16.0, 32)

    return int(round(max(0, min(100, pontos))))


def _classificar_arquitetura(score: int) -> str:
    if score >= 85:
        return "Pode iniciar arquitetura profissional"
    if score >= 70:
        return "Pode preparar arquitetura com cautela"
    if score >= 55:
        return "Mapear arquitetura, mas manter MVP"
    if score >= 40:
        return "Arquitetura ainda prematura"
    return "Focar validação antes da arquitetura"


def _decisao_tecnica(score: int, suporte: List[Dict[str, str]], clientes: List[Dict[str, str]]) -> str:
    if _clientes_pagos(clientes) == 0:
        return "Não iniciar Fase 4 técnica: primeiro validar venda paga."

    if _tickets_criticos(suporte) > 0:
        return "Não migrar problema crítico para arquitetura nova: corrigir suporte antes."

    if score >= 85:
        return "Iniciar construção técnica da Fase 4 com API, banco e frontend mínimo."

    if score >= 70:
        return "Preparar repositório, schema e contratos de API, sem abandonar o MVP."

    if score >= 55:
        return "Documentar arquitetura e extrair motor de cálculo, mas não reescrever tudo."

    return "Manter Streamlit como laboratório e continuar validação manual."


def _gerar_stack_alvo() -> List[Dict[str, str]]:
    return [
        {
            "Camada": "Frontend",
            "Escolha recomendada": "Next.js + TypeScript",
            "Função": "Landing page, dashboard, telas de análise, área do assinante e experiência premium.",
            "Motivo estratégico": "Deixa o produto mais vendável, rápido e profissional.",
        },
        {
            "Camada": "Design/UI",
            "Escolha recomendada": "Tailwind CSS + shadcn/ui",
            "Função": "Criar componentes elegantes, consistentes e rápidos de montar.",
            "Motivo estratégico": "Aumenta percepção de valor sem inflar complexidade.",
        },
        {
            "Camada": "Backend",
            "Escolha recomendada": "Python FastAPI",
            "Função": "Expor cálculo de valuation, relatórios, histórico, usuários e planos.",
            "Motivo estratégico": "Reaproveita o conhecimento e a lógica Python do MVP atual.",
        },
        {
            "Camada": "Banco",
            "Escolha recomendada": "PostgreSQL via Supabase",
            "Função": "Salvar usuários, análises, empresas, relatórios, feedbacks e assinaturas.",
            "Motivo estratégico": "Substitui CSV por dados seguros e escaláveis.",
        },
        {
            "Camada": "Autenticação",
            "Escolha recomendada": "Supabase Auth",
            "Função": "Login, sessão, recuperação de senha e controle por usuário.",
            "Motivo estratégico": "Reduz trabalho técnico e acelera lançamento.",
        },
        {
            "Camada": "Pagamento",
            "Escolha recomendada": "Mercado Pago, Asaas ou Stripe",
            "Função": "Checkout, assinatura, webhooks e liberação de acesso.",
            "Motivo estratégico": "Remove operação manual quando o beta pago justificar.",
        },
        {
            "Camada": "Deploy Frontend",
            "Escolha recomendada": "Vercel",
            "Função": "Hospedar a aplicação Next.js.",
            "Motivo estratégico": "Deploy simples, rápido e confiável.",
        },
        {
            "Camada": "Deploy Backend",
            "Escolha recomendada": "Render ou Railway",
            "Função": "Hospedar API Python.",
            "Motivo estratégico": "Boa relação entre simplicidade e custo.",
        },
        {
            "Camada": "Analytics",
            "Escolha recomendada": "PostHog",
            "Função": "Medir ativação, uso, funil, retenção e eventos do produto.",
            "Motivo estratégico": "Transforma comportamento real em decisão de produto.",
        },
    ]


def _gerar_estrutura_repositorio() -> List[Dict[str, str]]:
    return [
        {
            "Pasta/arquivo": "apps/web",
            "Responsabilidade": "Frontend Next.js com TypeScript.",
            "Observação": "Landing, dashboard, valuation, relatórios e conta do usuário.",
        },
        {
            "Pasta/arquivo": "apps/api",
            "Responsabilidade": "Backend FastAPI.",
            "Observação": "Endpoints de valuation, relatórios, histórico, usuários e pagamentos.",
        },
        {
            "Pasta/arquivo": "packages/core",
            "Responsabilidade": "Motor puro de cálculo.",
            "Observação": "Regras de valuation independentes de Streamlit, API ou frontend.",
        },
        {
            "Pasta/arquivo": "packages/schemas",
            "Responsabilidade": "Schemas compartilhados.",
            "Observação": "Tipos de entrada, saída, validações e contratos.",
        },
        {
            "Pasta/arquivo": "packages/config",
            "Responsabilidade": "Configurações compartilhadas.",
            "Observação": "Constantes, flags de ambiente e variáveis.",
        },
        {
            "Pasta/arquivo": "docs",
            "Responsabilidade": "Documentação técnica e de produto.",
            "Observação": "Roadmap, decisões, API, banco e instruções de deploy.",
        },
        {
            "Pasta/arquivo": "legacy/streamlit-mvp",
            "Responsabilidade": "Preservar o MVP atual.",
            "Observação": "O Streamlit vira laboratório interno, não precisa ser destruído.",
        },
    ]


def _gerar_contratos_api() -> List[Dict[str, str]]:
    return [
        {
            "Endpoint": "POST /valuation/calculate",
            "Entrada": "empresa, ticker, lucro, FCF, ações, múltiplos, pesos, margem, preço atual",
            "Saída": "EPS, FCF/ação, preço justo, preço-teto, status e leitura",
            "Prioridade": "Muito alta",
        },
        {
            "Endpoint": "POST /valuation/save",
            "Entrada": "user_id, inputs_json, result_json",
            "Saída": "valuation_id, created_at",
            "Prioridade": "Muito alta",
        },
        {
            "Endpoint": "GET /valuation/history",
            "Entrada": "user_id",
            "Saída": "lista de análises salvas",
            "Prioridade": "Alta",
        },
        {
            "Endpoint": "POST /reports/generate",
            "Entrada": "valuation_id ou inputs + result",
            "Saída": "relatório em markdown/html/pdf futuramente",
            "Prioridade": "Alta",
        },
        {
            "Endpoint": "GET /companies",
            "Entrada": "filtros opcionais",
            "Saída": "empresas cadastradas",
            "Prioridade": "Média",
        },
        {
            "Endpoint": "POST /feedback",
            "Entrada": "user_id, nota, comentário, categoria",
            "Saída": "feedback_id",
            "Prioridade": "Média",
        },
        {
            "Endpoint": "POST /payments/webhook",
            "Entrada": "evento do provedor de pagamento",
            "Saída": "status atualizado da assinatura",
            "Prioridade": "Alta depois do checkout",
        },
    ]


def _gerar_schema_banco() -> List[Dict[str, str]]:
    return [
        {
            "Tabela": "users",
            "Campos": "id, name, email, created_at, last_login_at",
            "Função": "Identificar cada usuário/assinante.",
        },
        {
            "Tabela": "subscriptions",
            "Campos": "id, user_id, provider, status, plan, amount, renewal_date",
            "Função": "Controlar plano, pagamento e acesso.",
        },
        {
            "Tabela": "companies",
            "Campos": "id, ticker, name, sector, country, currency",
            "Função": "Base de empresas analisáveis.",
        },
        {
            "Tabela": "valuations",
            "Campos": "id, user_id, company_id, inputs_json, result_json, created_at",
            "Função": "Salvar análises de valuation.",
        },
        {
            "Tabela": "reports",
            "Campos": "id, valuation_id, format, content, created_at",
            "Função": "Guardar relatórios gerados.",
        },
        {
            "Tabela": "watchlist",
            "Campos": "id, user_id, asset_type, ticker, target_price, notes",
            "Função": "Acompanhar ativos de interesse.",
        },
        {
            "Tabela": "feedbacks",
            "Campos": "id, user_id, rating, category, comment, created_at",
            "Função": "Coletar aprendizado de produto.",
        },
        {
            "Tabela": "support_tickets",
            "Campos": "id, user_id, priority, status, subject, description, created_at",
            "Função": "Controlar suporte dentro do produto.",
        },
    ]


def _gerar_fronteiras_mvp() -> List[Dict[str, str]]:
    return [
        {
            "Área": "Manter no Streamlit por enquanto",
            "Itens": "Painéis internos, aprendizado beta, sprints, CRM, suporte, retenção e métricas do fundador.",
            "Motivo": "São áreas internas de operação e ainda mudam rápido.",
        },
        {
            "Área": "Migrar para Web App primeiro",
            "Itens": "Landing page, login, valuation, relatório, histórico e dashboard do usuário.",
            "Motivo": "São as partes que o cliente realmente usa e percebe valor.",
        },
        {
            "Área": "Não migrar agora",
            "Itens": "Todas as abas internas de negócio, marketing e decisão estratégica.",
            "Motivo": "Não devem aparecer para o cliente final.",
        },
        {
            "Área": "Transformar em API",
            "Itens": "Cálculo de valuation, decisão educacional, geração de relatório e histórico.",
            "Motivo": "São o núcleo reutilizável do produto.",
        },
    ]


def _gerar_riscos_tecnicos() -> List[Dict[str, str]]:
    return [
        {
            "Risco": "Reescrever tudo cedo demais",
            "Impacto": "Alto",
            "Como evitar": "Migrar por módulos e manter Streamlit como laboratório.",
        },
        {
            "Risco": "Frontend bonito sem backend sólido",
            "Impacto": "Alto",
            "Como evitar": "Criar API e banco antes de sofisticar telas.",
        },
        {
            "Risco": "Banco mal modelado",
            "Impacto": "Alto",
            "Como evitar": "Começar com poucas tabelas essenciais e evoluir com uso real.",
        },
        {
            "Risco": "Pagamento sem suporte preparado",
            "Impacto": "Médio/Alto",
            "Como evitar": "Só automatizar checkout quando suporte e onboarding estiverem claros.",
        },
        {
            "Risco": "Misturar área do fundador com área do usuário",
            "Impacto": "Alto",
            "Como evitar": "Separar produto público de operação interna.",
        },
        {
            "Risco": "Criar muitas features financeiras",
            "Impacto": "Médio",
            "Como evitar": "Manter foco no preço-teto, relatório e decisão educacional.",
        },
    ]


def _gerar_ordem_execucao() -> List[Dict[str, str]]:
    return [
        {
            "Ordem": "1",
            "Tarefa": "Congelar o MVP como laboratório",
            "Resultado": "Streamlit continua funcionando sem ser destruído.",
        },
        {
            "Ordem": "2",
            "Tarefa": "Extrair motor de cálculo para módulo puro",
            "Resultado": "Cálculo reaproveitável na futura API.",
        },
        {
            "Ordem": "3",
            "Tarefa": "Criar schema do banco",
            "Resultado": "Modelo de dados mínimo e claro.",
        },
        {
            "Ordem": "4",
            "Tarefa": "Criar API FastAPI local",
            "Resultado": "Primeiro backend profissional.",
        },
        {
            "Ordem": "5",
            "Tarefa": "Criar frontend Next.js mínimo",
            "Resultado": "Tela inicial, valuation e relatório.",
        },
        {
            "Ordem": "6",
            "Tarefa": "Conectar frontend com API",
            "Resultado": "Usuário calcula preço-teto fora do Streamlit.",
        },
        {
            "Ordem": "7",
            "Tarefa": "Adicionar banco e histórico",
            "Resultado": "Usuário salva e consulta análises.",
        },
        {
            "Ordem": "8",
            "Tarefa": "Adicionar autenticação",
            "Resultado": "Cada cliente acessa a própria conta.",
        },
        {
            "Ordem": "9",
            "Tarefa": "Adicionar pagamento",
            "Resultado": "Liberação de acesso começa a ser automatizada.",
        },
    ]


def _gerar_mvp_web_cliente() -> List[Dict[str, str]]:
    return [
        {
            "Tela": "Landing page",
            "Objetivo": "Vender a promessa do produto.",
            "Elementos": "Headline, dor, solução, exemplos, prova, oferta e CTA.",
        },
        {
            "Tela": "Login/Cadastro",
            "Objetivo": "Permitir acesso individual.",
            "Elementos": "E-mail, senha, Google futuramente e recuperação de senha.",
        },
        {
            "Tela": "Dashboard",
            "Objetivo": "Mostrar visão inicial do usuário.",
            "Elementos": "Últimas análises, watchlist, relatórios e CTA para nova análise.",
        },
        {
            "Tela": "Nova análise",
            "Objetivo": "Calcular preço-teto.",
            "Elementos": "Inputs guiados, premissas, resultado, status e leitura.",
        },
        {
            "Tela": "Relatório",
            "Objetivo": "Entregar valor tangível.",
            "Elementos": "Resumo, premissas, tese, riscos, decisão educacional e exportação.",
        },
        {
            "Tela": "Histórico",
            "Objetivo": "Criar recorrência.",
            "Elementos": "Análises passadas, datas, tickers, preço-teto e status.",
        },
        {
            "Tela": "Conta/Plano",
            "Objetivo": "Controlar assinatura.",
            "Elementos": "Plano atual, status, renovação, suporte e cobrança.",
        },
    ]


def _gerar_markdown_arquitetura(
    score: int,
    classificacao: str,
    decisao: str,
    clientes: List[Dict[str, str]],
    suporte: List[Dict[str, str]],
    retencao: List[Dict[str, str]],
    decisoes: List[Dict[str, str]],
) -> str:
    def linhas(tabela: List[Dict[str, str]]) -> str:
        if len(tabela) == 0:
            return ""

        colunas = list(tabela[0].keys())
        cabecalho = "| " + " | ".join(colunas) + " |"
        separador = "| " + " | ".join(["---"] * len(colunas)) + " |"
        corpo = "\n".join(
            [
                "| " + " | ".join([str(linha.get(coluna, "")) for coluna in colunas]) + " |"
                for linha in tabela
            ]
        )

        return f"{cabecalho}\n{separador}\n{corpo}"

    return f"""# Blueprint Técnico da Fase 4 — Máquina de Preço-Teto

Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Diagnóstico

**Score de prontidão técnica:** {score}/100  
**Classificação:** {classificacao}  
**Decisão técnica:** {decisao}

## Indicadores atuais

- Clientes pagos: {_clientes_pagos(clientes)}
- Clientes ativos: {_clientes_ativos(clientes)}
- Receita real: {_fmt_moeda(_receita_real(clientes))}
- MRR estimado: {_fmt_moeda(_mrr_estimado(clientes))}
- NPS médio: {_nps_medio(retencao):.1f}/10
- Tickets críticos: {_tickets_criticos(suporte)}
- Tickets abertos: {_tickets_abertos(suporte)}
- Renovações: {_renovacoes(retencao)}
- Cancelamentos: {_cancelamentos(retencao)}
- Última decisão executiva: {_ultima_decisao(decisoes)}

## Stack alvo

{linhas(_gerar_stack_alvo())}

## Estrutura de repositório

{linhas(_gerar_estrutura_repositorio())}

## Contratos iniciais de API

{linhas(_gerar_contratos_api())}

## Schema inicial do banco

{linhas(_gerar_schema_banco())}

## Fronteiras do MVP

{linhas(_gerar_fronteiras_mvp())}

## Riscos técnicos

{linhas(_gerar_riscos_tecnicos())}

## Ordem de execução

{linhas(_gerar_ordem_execucao())}

## MVP Web do cliente

{linhas(_gerar_mvp_web_cliente())}

## Regra

A nova arquitetura deve nascer pequena, modular e orientada ao valor real do cliente.
O Streamlit continua sendo laboratório interno; o Web App nasce como produto público vendável.
"""


def _injetar_css_arquitetura() -> None:
    st.markdown(
        """
        <style>
            .af4-hero {
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

            .af4-eyebrow {
                color: #d6b56d;
                font-size: 0.78rem;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.35rem;
            }

            .af4-title {
                color: #f4f7fb;
                font-size: 2.1rem;
                font-weight: 900;
                margin-bottom: 0.45rem;
                line-height: 1.14;
            }

            .af4-subtitle {
                color: rgba(244, 247, 251, 0.76);
                font-size: 1rem;
                line-height: 1.62;
                max-width: 1080px;
            }

            .af4-card {
                padding: 1.1rem 1.15rem;
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.035);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.18);
                height: 100%;
            }

            .af4-card-label {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .af4-card-value {
                color: #f4f7fb;
                font-size: 1.22rem;
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .af4-card-note {
                color: rgba(244, 247, 251, 0.68);
                font-size: 0.87rem;
                line-height: 1.47;
            }

            .af4-highlight {
                padding: 0.95rem 1rem;
                border-radius: 16px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.92rem;
                line-height: 1.55;
                margin-bottom: 0.7rem;
            }

            .af4-disclaimer {
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
        <div class="af4-card">
            <div class="af4-card-label">{label}</div>
            <div class="af4-card-value">{value}</div>
            <div class="af4-card-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def renderizar_arquitetura_fase4() -> None:
    """
    Renderiza o blueprint técnico da Fase 4.
    """
    _injetar_css_arquitetura()

    clientes = _carregar_csv(CAMINHO_CLIENTES_BETA)
    suporte = _carregar_csv(CAMINHO_SUPORTE_BETA)
    retencao = _carregar_csv(CAMINHO_RETENCAO_BETA)
    metricas = _carregar_csv(CAMINHO_METRICAS_FASE3)
    decisoes = _carregar_csv(CAMINHO_DECISOES_FASE3)

    score = _score_prontidao_arquitetura(
        clientes=clientes,
        suporte=suporte,
        retencao=retencao,
        metricas=metricas,
        decisoes=decisoes,
    )

    classificacao = _classificar_arquitetura(score)
    decisao = _decisao_tecnica(score, suporte, clientes)

    st.session_state["resultado_arquitetura_fase4"] = {
        "score_prontidao_arquitetura": score,
        "classificacao": classificacao,
        "decisao": decisao,
        "clientes_pagos": _clientes_pagos(clientes),
        "mrr_estimado": _mrr_estimado(clientes),
        "tickets_criticos": _tickets_criticos(suporte),
        "ultima_decisao": _ultima_decisao(decisoes),
    }

    st.markdown(
        """
        <div class="af4-hero">
            <div class="af4-eyebrow">Fase 3.7 → Blueprint Técnico</div>
            <div class="af4-title">Arquitetura Profissional da Fase 4</div>
            <div class="af4-subtitle">
                Defina como a Máquina de Preço-Teto deve evoluir para um web app profissional:
                frontend moderno, backend em API, banco de dados, autenticação, pagamento, deploy e analytics.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="af4-highlight">
            A arquitetura certa não é a mais complexa. É a menor arquitetura capaz de entregar valor,
            cobrar, reter e evoluir com segurança.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Diagnóstico técnico")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Score arquitetura", f"{score}/100")

    with col_2:
        st.metric("Classificação", classificacao)

    with col_3:
        st.metric("Clientes pagos", _clientes_pagos(clientes))

    with col_4:
        st.metric("MRR estimado", _fmt_moeda(_mrr_estimado(clientes)))

    st.progress(score / 100)

    if score >= 70:
        st.success(decisao)
    elif score >= 40:
        st.warning(decisao)
    else:
        st.error(decisao)

    st.divider()

    st.markdown("### Indicadores considerados")

    col_a, col_b, col_c, col_d = st.columns(4)

    with col_a:
        _card("Receita real", _fmt_moeda(_receita_real(clientes)), "Dinheiro confirmado no beta.")

    with col_b:
        _card("NPS médio", f"{_nps_medio(retencao):.1f}/10", "Valor percebido e retenção.")

    with col_c:
        _card("Tickets críticos", str(_tickets_criticos(suporte)), "Não devem ir para a Fase 4.")

    with col_d:
        _card("Última decisão", _ultima_decisao(decisoes), "Base estratégica registrada.")

    st.divider()

    st.markdown("### Stack alvo recomendada")

    st.dataframe(
        _gerar_stack_alvo(),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Estrutura sugerida de repositório")

    st.dataframe(
        _gerar_estrutura_repositorio(),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Contratos iniciais de API")

    st.dataframe(
        _gerar_contratos_api(),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Schema inicial do banco de dados")

    st.dataframe(
        _gerar_schema_banco(),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Fronteiras do MVP: o que migra e o que fica")

    st.dataframe(
        _gerar_fronteiras_mvp(),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### MVP Web do cliente")

    st.dataframe(
        _gerar_mvp_web_cliente(),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Riscos técnicos")

    st.dataframe(
        _gerar_riscos_tecnicos(),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Ordem correta de execução")

    st.dataframe(
        _gerar_ordem_execucao(),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Leitura executiva")

    st.info(
        f"""
        **Classificação:** {classificacao}

        **Decisão técnica:** {decisao}

        **Leitura fria:** a próxima arquitetura deve nascer pequena. 
        Primeiro extraímos o motor de cálculo, depois criamos API, banco e frontend mínimo.
        Login, pagamento e automações entram quando o produto já provar que entrega valor e consegue reter.
        """
    )

    st.divider()

    st.download_button(
        label="Baixar blueprint técnico da Fase 4 (.md)",
        data=_gerar_markdown_arquitetura(
            score=score,
            classificacao=classificacao,
            decisao=decisao,
            clientes=clientes,
            suporte=suporte,
            retencao=retencao,
            decisoes=decisoes,
        ),
        file_name="blueprint_tecnico_fase4.md",
        mime="text/markdown",
        key="download_arquitetura_fase4_md",
    )

    st.markdown(
        """
        <div class="af4-disclaimer">
            <strong>Regra técnica:</strong> o MVP atual não deve ser destruído.
            Ele vira laboratório interno. A Fase 4 nasce em paralelo como produto público,
            com arquitetura limpa, modular e vendável.
        </div>
        """,
        unsafe_allow_html=True,
    )