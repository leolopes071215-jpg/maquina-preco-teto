# plano_fase4.py

import csv
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List

import streamlit as st


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v3.6 — Plano de Migração para Web App Profissional / Fase 4
# ------------------------------------------------------------
# Esta tela prepara a transição do MVP em Streamlit para uma
# arquitetura profissional de produto digital.
#
# Objetivo:
# - decidir quando migrar
# - definir stack técnica
# - separar MVP interno de produto público
# - organizar roadmap de frontend, backend, banco, login,
#   pagamentos, deploy e automação
# - evitar reescrever o produto antes de validar negócio
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


def _fmt_percentual(valor: float) -> str:
    return f"{valor:.1f}%"


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
    return sum(
        _safe_float(cliente.get("valor_pago"))
        for cliente in clientes
        if cliente.get("status_pagamento") == "Pago"
    )


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


def _clientes_em_risco_retencao(retencao: List[Dict[str, str]]) -> int:
    return len(
        [
            registro for registro in retencao
            if registro.get("risco_churn") in ["Alto", "Crítico"]
            or registro.get("saude_cliente") in ["Risco", "Crítica"]
            or registro.get("status_cliente") in ["Em risco", "Cancelado", "Não renovou"]
        ]
    )


def _ultimo_score_go_no_go(decisoes: List[Dict[str, str]]) -> float:
    if len(decisoes) == 0:
        return 0.0

    return _safe_float(decisoes[-1].get("score_go_no_go"))


def _ultima_decisao(decisoes: List[Dict[str, str]]) -> str:
    if len(decisoes) == 0:
        return "Sem decisão registrada"

    return decisoes[-1].get("decisao", "Sem decisão registrada")


def _calcular_score_prontidao_fase4(
    clientes: List[Dict[str, str]],
    suporte: List[Dict[str, str]],
    retencao: List[Dict[str, str]],
    metricas: List[Dict[str, str]],
    decisoes: List[Dict[str, str]],
) -> int:
    clientes_pagos = _clientes_pagos(clientes)
    clientes_ativos = _clientes_ativos(clientes)
    receita = _receita_real(clientes)
    mrr = _mrr_estimado(clientes)
    tickets_criticos = _tickets_criticos(suporte)
    tickets_abertos = _tickets_abertos(suporte)
    nps = _nps_medio(retencao)
    renovacoes = _renovacoes(retencao)
    cancelamentos = _cancelamentos(retencao)
    risco = _clientes_em_risco_retencao(retencao)
    score_go_no_go = _ultimo_score_go_no_go(decisoes)

    pontos = 0.0

    pontos += min(clientes_pagos * 12.0, 30)
    pontos += min(clientes_ativos * 8.0, 20)
    pontos += min(receita / 10, 15)
    pontos += min(mrr / 10, 15)

    if nps >= 7:
        pontos += 10
    if nps >= 8:
        pontos += 10

    pontos += min(renovacoes * 12.0, 24)

    if len(metricas) > 0:
        pontos += 8

    if len(decisoes) > 0:
        pontos += 8

    if score_go_no_go >= 70:
        pontos += 10

    if score_go_no_go >= 85:
        pontos += 10

    pontos -= min(tickets_criticos * 18.0, 36)
    pontos -= min(tickets_abertos * 4.0, 20)
    pontos -= min(cancelamentos * 16.0, 32)
    pontos -= min(risco * 10.0, 30)

    return int(round(max(0, min(100, pontos))))


def _classificar_prontidao(score: int) -> str:
    if score >= 85:
        return "Pronto para iniciar Fase 4 com automação leve"
    if score >= 70:
        return "Quase pronto para Fase 4"
    if score >= 55:
        return "Ainda em validação avançada"
    if score >= 40:
        return "Prematuro para migrar"
    return "Não migrar ainda"


def _decisao_fase4(
    score: int,
    clientes: List[Dict[str, str]],
    suporte: List[Dict[str, str]],
    retencao: List[Dict[str, str]],
) -> str:
    if _clientes_pagos(clientes) == 0:
        return "Não migrar ainda: buscar clientes pagos primeiro"

    if _tickets_criticos(suporte) > 0:
        return "Não migrar ainda: resolver suporte crítico"

    if _clientes_em_risco_retencao(retencao) > 0:
        return "Não migrar ainda: reduzir risco de churn"

    if _cancelamentos(retencao) > 0 and _renovacoes(retencao) == 0:
        return "Não migrar ainda: entender cancelamentos"

    if score >= 85:
        return "Iniciar Fase 4 com automação leve e arquitetura profissional"

    if score >= 70:
        return "Preparar documentação técnica e protótipo da nova arquitetura"

    if score >= 55:
        return "Continuar Fase 3, mas mapear arquitetura futura"

    return "Focar validação manual antes de qualquer migração"


def _gerar_stack_recomendada() -> List[Dict[str, str]]:
    return [
        {
            "Camada": "Frontend público",
            "Tecnologia recomendada": "Next.js + TypeScript",
            "Motivo": "Interface profissional, rápida, vendável, com páginas públicas, dashboard e boa experiência.",
            "Quando usar": "Fase 4",
        },
        {
            "Camada": "Backend/API",
            "Tecnologia recomendada": "Python FastAPI",
            "Motivo": "Permite reaproveitar lógica do valuation em Python e expor cálculos via API.",
            "Quando usar": "Fase 4",
        },
        {
            "Camada": "Banco de dados",
            "Tecnologia recomendada": "PostgreSQL ou Supabase",
            "Motivo": "Substitui CSV, permite usuários, histórico, pagamentos, relatórios e dados seguros.",
            "Quando usar": "Fase 4",
        },
        {
            "Camada": "Autenticação",
            "Tecnologia recomendada": "Supabase Auth ou NextAuth",
            "Motivo": "Login por e-mail, Google e controle de acesso para assinantes.",
            "Quando usar": "Após validar beta pago",
        },
        {
            "Camada": "Pagamentos",
            "Tecnologia recomendada": "Mercado Pago, Asaas, Stripe ou Kiwify/Hotmart",
            "Motivo": "Checkout, assinatura, confirmação de pagamento e automação de acesso.",
            "Quando usar": "Após primeira validação de oferta",
        },
        {
            "Camada": "Deploy frontend",
            "Tecnologia recomendada": "Vercel",
            "Motivo": "Deploy rápido, boa integração com Next.js e aparência profissional.",
            "Quando usar": "Fase 4",
        },
        {
            "Camada": "Deploy backend",
            "Tecnologia recomendada": "Render, Railway ou Fly.io",
            "Motivo": "Hospedagem simples para API Python com bom custo inicial.",
            "Quando usar": "Fase 4",
        },
        {
            "Camada": "Analytics",
            "Tecnologia recomendada": "PostHog, Plausible ou Google Analytics",
            "Motivo": "Mede ativação, uso, funil, retenção e comportamento real.",
            "Quando usar": "Logo no início da Fase 4",
        },
        {
            "Camada": "E-mail/transacional",
            "Tecnologia recomendada": "Resend, Brevo ou Mailgun",
            "Motivo": "Envio de acesso, onboarding, alertas, relatórios e recuperação de usuários.",
            "Quando usar": "Após login/checkout",
        },
    ]


def _gerar_mapa_migracao() -> List[Dict[str, str]]:
    return [
        {
            "Ordem": "1",
            "Etapa": "Separar núcleo de cálculo",
            "Descrição": "Organizar valuation, relatórios e regras de decisão em funções puras reutilizáveis.",
            "Resultado esperado": "Motor de cálculo pronto para virar API.",
        },
        {
            "Ordem": "2",
            "Etapa": "Modelar banco de dados",
            "Descrição": "Definir tabelas de usuários, análises, empresas, relatórios, pagamentos e feedbacks.",
            "Resultado esperado": "Modelo relacional claro para substituir CSV.",
        },
        {
            "Ordem": "3",
            "Etapa": "Criar API em FastAPI",
            "Descrição": "Expor endpoints para valuation, salvar análise, gerar relatório e consultar histórico.",
            "Resultado esperado": "Backend funcional e testável.",
        },
        {
            "Ordem": "4",
            "Etapa": "Criar frontend em Next.js",
            "Descrição": "Construir landing page, dashboard do usuário, tela de valuation e relatórios.",
            "Resultado esperado": "Produto com aparência vendável.",
        },
        {
            "Ordem": "5",
            "Etapa": "Adicionar autenticação",
            "Descrição": "Permitir login, sessão, usuário ativo e controle de acesso.",
            "Resultado esperado": "Cada cliente acessa suas próprias análises.",
        },
        {
            "Ordem": "6",
            "Etapa": "Integrar pagamento",
            "Descrição": "Adicionar checkout, status de assinatura e liberação automática.",
            "Resultado esperado": "Venda sem operação manual pesada.",
        },
        {
            "Ordem": "7",
            "Etapa": "Migrar dados relevantes",
            "Descrição": "Levar histórico útil dos CSVs para banco somente se fizer sentido.",
            "Resultado esperado": "Base inicial limpa.",
        },
        {
            "Ordem": "8",
            "Etapa": "Beta web controlado",
            "Descrição": "Liberar nova versão para poucos usuários pagantes antes de escalar.",
            "Resultado esperado": "Validação da nova arquitetura.",
        },
    ]


def _gerar_o_que_nao_fazer_agora() -> List[Dict[str, str]]:
    return [
        {
            "Não fazer agora": "Reescrever tudo do zero sem validação",
            "Por quê": "Pode consumir semanas e não aumentar vendas nem retenção.",
        },
        {
            "Não fazer agora": "Criar app mobile",
            "Por quê": "Ainda não há necessidade comprovada. Web app resolve primeiro.",
        },
        {
            "Não fazer agora": "Automatizar suporte inteiro",
            "Por quê": "Suporte ainda é fonte de aprendizado real.",
        },
        {
            "Não fazer agora": "Adicionar dezenas de funcionalidades financeiras",
            "Por quê": "Pode deixar o produto confuso antes de provar o core.",
        },
        {
            "Não fazer agora": "Contratar tráfego pago agressivo",
            "Por quê": "Sem retenção e onboarding forte, aquisição paga queima dinheiro.",
        },
        {
            "Não fazer agora": "Criar marketplace/comunidade complexa",
            "Por quê": "Isso é outra empresa dentro da empresa. Primeiro valide o produto principal.",
        },
    ]


def _gerar_checklist_fase4(
    clientes: List[Dict[str, str]],
    suporte: List[Dict[str, str]],
    retencao: List[Dict[str, str]],
    metricas: List[Dict[str, str]],
    decisoes: List[Dict[str, str]],
    score: int,
) -> List[Dict[str, str]]:
    return [
        {
            "Critério": "Pelo menos 1 cliente pago",
            "Status": "OK" if _clientes_pagos(clientes) >= 1 else "Pendente",
            "Leitura": "Sem cliente pago, ainda não há validação comercial.",
        },
        {
            "Critério": "Pelo menos 2 clientes ativos pagos",
            "Status": "OK" if _clientes_ativos(clientes) >= 2 else "Pendente",
            "Leitura": "Reduz dependência de um único caso.",
        },
        {
            "Critério": "MRR estimado positivo",
            "Status": "OK" if _mrr_estimado(clientes) > 0 else "Pendente",
            "Leitura": "Indica potencial de recorrência.",
        },
        {
            "Critério": "Nenhum ticket crítico",
            "Status": "OK" if _tickets_criticos(suporte) == 0 else "Pendente",
            "Leitura": "Não se migra problema crítico para arquitetura nova.",
        },
        {
            "Critério": "NPS médio ≥ 7",
            "Status": "OK" if _nps_medio(retencao) >= 7 else "Pendente",
            "Leitura": "Mostra valor percebido mínimo.",
        },
        {
            "Critério": "Sem churn crítico",
            "Status": "OK" if _cancelamentos(retencao) == 0 else "Pendente",
            "Leitura": "Cancelamentos precisam de diagnóstico antes de escalar.",
        },
        {
            "Critério": "Snapshots de métricas registrados",
            "Status": "OK" if len(metricas) > 0 else "Pendente",
            "Leitura": "Sem métrica histórica, a decisão fica fraca.",
        },
        {
            "Critério": "Decisão Go/No-Go registrada",
            "Status": "OK" if len(decisoes) > 0 else "Pendente",
            "Leitura": "A migração precisa de decisão executiva registrada.",
        },
        {
            "Critério": "Score prontidão Fase 4 ≥ 70",
            "Status": "OK" if score >= 70 else "Pendente",
            "Leitura": "Maturidade mínima para planejar migração.",
        },
    ]


def _gerar_roadmap_fase4() -> List[Dict[str, str]]:
    return [
        {
            "Semana": "Semana 1",
            "Foco": "Arquitetura e modelagem",
            "Entregas": "Definir stack, banco de dados, tabelas, fluxos e endpoints principais.",
        },
        {
            "Semana": "Semana 2",
            "Foco": "Backend/API",
            "Entregas": "Criar FastAPI com motor de valuation, relatórios e histórico.",
        },
        {
            "Semana": "Semana 3",
            "Foco": "Frontend base",
            "Entregas": "Landing page, login, dashboard inicial e tela de valuation.",
        },
        {
            "Semana": "Semana 4",
            "Foco": "Banco + autenticação",
            "Entregas": "Persistência real, usuário logado, histórico por conta.",
        },
        {
            "Semana": "Semana 5",
            "Foco": "Pagamento e acesso",
            "Entregas": "Checkout, status de plano, liberação e bloqueio de acesso.",
        },
        {
            "Semana": "Semana 6",
            "Foco": "Beta web controlado",
            "Entregas": "Liberar para poucos clientes, medir bugs, retenção, uso e suporte.",
        },
    ]


def _gerar_backlog_tecnico() -> List[Dict[str, str]]:
    return [
        {
            "Prioridade": "Muito alta",
            "Item": "Extrair motor de valuation",
            "Descrição": "Separar cálculos do Streamlit para reaproveitar em API.",
        },
        {
            "Prioridade": "Muito alta",
            "Item": "Criar schema do banco",
            "Descrição": "Usuários, análises, empresas, relatórios, pagamentos e feedback.",
        },
        {
            "Prioridade": "Alta",
            "Item": "Criar API /valuation",
            "Descrição": "Endpoint que recebe premissas e retorna preço-teto, status e relatório.",
        },
        {
            "Prioridade": "Alta",
            "Item": "Criar dashboard do usuário",
            "Descrição": "Tela onde o assinante vê suas análises e histórico.",
        },
        {
            "Prioridade": "Alta",
            "Item": "Criar landing page premium",
            "Descrição": "Página pública com promessa, prova, oferta e CTA.",
        },
        {
            "Prioridade": "Média",
            "Item": "Adicionar autenticação",
            "Descrição": "Login, sessão e controle de acesso.",
        },
        {
            "Prioridade": "Média",
            "Item": "Integrar checkout",
            "Descrição": "Pagamento, webhook e liberação automática.",
        },
        {
            "Prioridade": "Média",
            "Item": "Adicionar analytics",
            "Descrição": "Eventos de ativação, uso, relatório baixado e retenção.",
        },
    ]


def _gerar_modelo_dados() -> List[Dict[str, str]]:
    return [
        {
            "Tabela": "users",
            "Finalidade": "Armazenar usuários/clientes.",
            "Campos principais": "id, name, email, created_at, plan_status",
        },
        {
            "Tabela": "companies",
            "Finalidade": "Base de empresas analisáveis.",
            "Campos principais": "id, ticker, name, sector, country, currency",
        },
        {
            "Tabela": "valuations",
            "Finalidade": "Salvar análises de valuation.",
            "Campos principais": "id, user_id, company_id, inputs_json, result_json, created_at",
        },
        {
            "Tabela": "reports",
            "Finalidade": "Guardar relatórios gerados.",
            "Campos principais": "id, valuation_id, report_markdown, created_at",
        },
        {
            "Tabela": "subscriptions",
            "Finalidade": "Controlar plano e pagamento.",
            "Campos principais": "id, user_id, provider, status, amount, renewal_date",
        },
        {
            "Tabela": "feedbacks",
            "Finalidade": "Coletar feedback do produto.",
            "Campos principais": "id, user_id, rating, comment, category, created_at",
        },
        {
            "Tabela": "support_tickets",
            "Finalidade": "Registrar suporte.",
            "Campos principais": "id, user_id, category, priority, status, created_at",
        },
    ]


def _gerar_markdown_plano_fase4(
    score: int,
    classificacao: str,
    decisao: str,
    clientes: List[Dict[str, str]],
    suporte: List[Dict[str, str]],
    retencao: List[Dict[str, str]],
    metricas: List[Dict[str, str]],
    decisoes: List[Dict[str, str]],
) -> str:
    linhas_stack = "\n".join(
        [
            f"| {item['Camada']} | {item['Tecnologia recomendada']} | {item['Motivo']} | {item['Quando usar']} |"
            for item in _gerar_stack_recomendada()
        ]
    )

    linhas_migracao = "\n".join(
        [
            f"| {item['Ordem']} | {item['Etapa']} | {item['Descrição']} | {item['Resultado esperado']} |"
            for item in _gerar_mapa_migracao()
        ]
    )

    linhas_checklist = "\n".join(
        [
            f"| {item['Critério']} | {item['Status']} | {item['Leitura']} |"
            for item in _gerar_checklist_fase4(clientes, suporte, retencao, metricas, decisoes, score)
        ]
    )

    linhas_roadmap = "\n".join(
        [
            f"| {item['Semana']} | {item['Foco']} | {item['Entregas']} |"
            for item in _gerar_roadmap_fase4()
        ]
    )

    linhas_backlog = "\n".join(
        [
            f"| {item['Prioridade']} | {item['Item']} | {item['Descrição']} |"
            for item in _gerar_backlog_tecnico()
        ]
    )

    return f"""# Plano de Migração para Fase 4 — Máquina de Preço-Teto

Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Diagnóstico

**Score de prontidão para Fase 4:** {score}/100  
**Classificação:** {classificacao}  
**Decisão:** {decisao}

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
- Última decisão Go/No-Go: {_ultima_decisao(decisoes)}

## Stack recomendada

| Camada | Tecnologia | Motivo | Quando usar |
|---|---|---|---|
{linhas_stack}

## Mapa de migração

| Ordem | Etapa | Descrição | Resultado esperado |
|---:|---|---|---|
{linhas_migracao}

## Checklist de prontidão

| Critério | Status | Leitura |
|---|---|---|
{linhas_checklist}

## Roadmap sugerido

| Semana | Foco | Entregas |
|---|---|---|
{linhas_roadmap}

## Backlog técnico inicial

| Prioridade | Item | Descrição |
|---|---|---|
{linhas_backlog}

## Regra

A Fase 4 não é uma fuga para tecnologia. É uma resposta a sinais de negócio.
Só migre quando venda, entrega, suporte e retenção justificarem a complexidade.
"""


def _injetar_css_fase4() -> None:
    st.markdown(
        """
        <style>
            .pf4-hero {
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

            .pf4-eyebrow {
                color: #d6b56d;
                font-size: 0.78rem;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.35rem;
            }

            .pf4-title {
                color: #f4f7fb;
                font-size: 2.1rem;
                font-weight: 900;
                margin-bottom: 0.45rem;
                line-height: 1.14;
            }

            .pf4-subtitle {
                color: rgba(244, 247, 251, 0.76);
                font-size: 1rem;
                line-height: 1.62;
                max-width: 1080px;
            }

            .pf4-card {
                padding: 1.1rem 1.15rem;
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.035);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.18);
                height: 100%;
            }

            .pf4-card-label {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .pf4-card-value {
                color: #f4f7fb;
                font-size: 1.22rem;
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .pf4-card-note {
                color: rgba(244, 247, 251, 0.68);
                font-size: 0.87rem;
                line-height: 1.47;
            }

            .pf4-highlight {
                padding: 0.95rem 1rem;
                border-radius: 16px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.92rem;
                line-height: 1.55;
                margin-bottom: 0.7rem;
            }

            .pf4-disclaimer {
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
        <div class="pf4-card">
            <div class="pf4-card-label">{label}</div>
            <div class="pf4-card-value">{value}</div>
            <div class="pf4-card-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def renderizar_plano_fase4() -> None:
    """
    Renderiza o plano de migração para Fase 4.
    """
    _injetar_css_fase4()

    clientes = _carregar_csv(CAMINHO_CLIENTES_BETA)
    suporte = _carregar_csv(CAMINHO_SUPORTE_BETA)
    retencao = _carregar_csv(CAMINHO_RETENCAO_BETA)
    metricas = _carregar_csv(CAMINHO_METRICAS_FASE3)
    decisoes = _carregar_csv(CAMINHO_DECISOES_FASE3)

    score = _calcular_score_prontidao_fase4(
        clientes=clientes,
        suporte=suporte,
        retencao=retencao,
        metricas=metricas,
        decisoes=decisoes,
    )

    classificacao = _classificar_prontidao(score)
    decisao = _decisao_fase4(score, clientes, suporte, retencao)

    st.session_state["resultado_plano_fase4"] = {
        "score_prontidao_fase4": score,
        "classificacao": classificacao,
        "decisao": decisao,
        "clientes_pagos": _clientes_pagos(clientes),
        "clientes_ativos": _clientes_ativos(clientes),
        "receita_real": _receita_real(clientes),
        "mrr_estimado": _mrr_estimado(clientes),
        "nps_medio": _nps_medio(retencao),
        "tickets_criticos": _tickets_criticos(suporte),
        "ultima_decisao_go_no_go": _ultima_decisao(decisoes),
    }

    st.markdown(
        """
        <div class="pf4-hero">
            <div class="pf4-eyebrow">Fase 3.6 → Fase 4</div>
            <div class="pf4-title">Plano de Migração para Web App Profissional</div>
            <div class="pf4-subtitle">
                Prepare a transição do MVP em Streamlit para uma arquitetura profissional com
                Next.js, TypeScript, FastAPI, banco de dados, login, pagamento e deploy escalável.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="pf4-highlight">
            A Fase 4 não é sobre trocar tecnologia por vaidade. É sobre transformar validação real
            em produto vendável, confiável, automatizado e escalável.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Diagnóstico de prontidão para Fase 4")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Score Fase 4", f"{score}/100")

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

    st.markdown("### Indicadores de base")

    col_a, col_b, col_c, col_d = st.columns(4)

    with col_a:
        _card("Receita real", _fmt_moeda(_receita_real(clientes)), "Dinheiro confirmado.")

    with col_b:
        _card("NPS médio", f"{_nps_medio(retencao):.1f}/10", "Valor percebido.")

    with col_c:
        _card("Tickets críticos", str(_tickets_criticos(suporte)), "Não devem migrar para a Fase 4.")

    with col_d:
        _card("Última decisão", _ultima_decisao(decisoes), "Base executiva registrada.")

    st.divider()

    st.markdown("### Stack recomendada")

    st.dataframe(
        _gerar_stack_recomendada(),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Mapa de migração")

    st.dataframe(
        _gerar_mapa_migracao(),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Checklist de prontidão")

    st.dataframe(
        _gerar_checklist_fase4(
            clientes=clientes,
            suporte=suporte,
            retencao=retencao,
            metricas=metricas,
            decisoes=decisoes,
            score=score,
        ),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### O que NÃO fazer agora")

    st.dataframe(
        _gerar_o_que_nao_fazer_agora(),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Roadmap sugerido da Fase 4")

    st.dataframe(
        _gerar_roadmap_fase4(),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Backlog técnico inicial")

    st.dataframe(
        _gerar_backlog_tecnico(),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Modelo inicial de banco de dados")

    st.dataframe(
        _gerar_modelo_dados(),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Leitura executiva")

    st.info(
        f"""
        **Classificação:** {classificacao}

        **Decisão:** {decisao}

        **Leitura fria:** o Streamlit atual continua sendo excelente como laboratório interno.
        A nova arquitetura só deve nascer quando houver sinal suficiente de venda, entrega, suporte e retenção.
        A Fase 4 deve começar pequena: primeiro API + banco + tela principal. Depois login, checkout e automação.
        """
    )

    st.divider()

    st.download_button(
        label="Baixar plano de migração para Fase 4 (.md)",
        data=_gerar_markdown_plano_fase4(
            score=score,
            classificacao=classificacao,
            decisao=decisao,
            clientes=clientes,
            suporte=suporte,
            retencao=retencao,
            metricas=metricas,
            decisoes=decisoes,
        ),
        file_name="plano_migracao_fase4.md",
        mime="text/markdown",
        key="download_plano_fase4_md",
    )

    st.markdown(
        """
        <div class="pf4-disclaimer">
            <strong>Regra da migração:</strong> tecnologia deve servir ao negócio.
            Não reescreva o produto para parecer sofisticado. Reescreva quando isso aumentar entrega,
            confiança, retenção, automação e receita.
        </div>
        """,
        unsafe_allow_html=True,
    )