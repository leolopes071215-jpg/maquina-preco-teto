# arquitetura_transicao_valoris.py

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

import streamlit as st

from maturidade_produto_valoris import calcular_maturidade_produto_valoris


# ============================================================
# VALORIS
# v3.8.55 — Blueprint de Arquitetura e Transição Técnica
# ------------------------------------------------------------
# Este módulo transforma a maturidade do produto em um plano
# técnico de transição.
#
# Objetivo:
# - preparar migração gradual sem abandonar o MVP;
# - desenhar banco, API e front-end futuro;
# - evitar troca prematura de tecnologia;
# - criar uma ponte clara:
#   CSV → Banco → API → Front-end moderno → Pagamentos/Auth.
# ============================================================


VERSAO_ARQUITETURA_TRANSICAO_VALORIS = "3.8.55"

CAMINHO_DECISOES_ARQUITETURA = Path("decisoes_arquitetura_valoris.csv")

CAMPOS_DECISAO_ARQUITETURA = [
    "id",
    "data_registro",
    "estagio_recomendado",
    "stack_recomendada",
    "risco_principal",
    "prioridade_tecnica",
    "proximo_passo",
    "observacoes",
]


ESTAGIOS_ARQUITETURA = [
    "Continuar Streamlit",
    "Preparar banco local/SQL",
    "Migrar CSVs para PostgreSQL/Supabase",
    "Criar API Python/FastAPI",
    "Criar front-end TypeScript/Next.js",
    "Integrar autenticação e pagamentos",
]


STACKS_RECOMENDADAS = [
    "Python + Streamlit + CSV",
    "Python + Streamlit + SQLite",
    "Python + Streamlit + PostgreSQL/Supabase",
    "Python + FastAPI + PostgreSQL/Supabase",
    "TypeScript + Next.js + FastAPI + PostgreSQL",
    "Next.js + Auth + Payments + FastAPI + PostgreSQL",
]


RISCOS_TECNICOS = [
    "Migrar cedo demais",
    "Acumular dívida técnica no Streamlit",
    "Perder dados por excesso de CSV",
    "Criar API antes de validar uso",
    "Criar front-end bonito sem retenção",
    "Criar checkout sem validação manual",
]


PRIORIDADES_TECNICAS = [
    "Fortalecer núcleo de valuation",
    "Padronizar camada de dados",
    "Modelar banco de dados",
    "Criar endpoints da API",
    "Criar design system e front-end",
    "Criar login, planos e pagamentos",
]


TABELAS_RECOMENDADAS = [
    {
        "nome": "users",
        "objetivo": "Guardar usuários, perfil, plano e origem.",
        "campos": "id, nome, email, perfil, plano, criado_em, status",
    },
    {
        "nome": "leads",
        "objetivo": "Substituir lista de espera e leads beta.",
        "campos": "id, nome, contato, perfil, dor, plano_interesse, pagaria_agora, criado_em",
    },
    {
        "nome": "valuations",
        "objetivo": "Guardar análises realizadas pelo usuário.",
        "campos": "id, user_id, ticker, preco_atual, preco_teto, preco_justo, status, criado_em",
    },
    {
        "nome": "reports",
        "objetivo": "Guardar relatórios gerados e versões.",
        "campos": "id, valuation_id, user_id, titulo, tipo, conteudo, criado_em",
    },
    {
        "nome": "events",
        "objetivo": "Substituir analytics CSV por eventos rastreáveis.",
        "campos": "id, user_id, session_id, event_name, context, value, criado_em",
    },
    {
        "nome": "founders",
        "objetivo": "Organizar usuários fundadores, onboarding e feedback.",
        "campos": "id, user_id, plano, status_pagamento, status_acesso, etapa_onboarding, feedback",
    },
    {
        "nome": "payments",
        "objetivo": "Registrar pagamentos manuais e futuros checkouts.",
        "campos": "id, user_id, provider, amount, status, paid_at, created_at",
    },
]


ENDPOINTS_RECOMENDADOS = [
    {
        "metodo": "POST",
        "rota": "/api/leads",
        "objetivo": "Cadastrar lead beta.",
    },
    {
        "metodo": "POST",
        "rota": "/api/valuation",
        "objetivo": "Executar valuation e salvar análise.",
    },
    {
        "metodo": "GET",
        "rota": "/api/valuation/{id}",
        "objetivo": "Buscar análise salva.",
    },
    {
        "metodo": "POST",
        "rota": "/api/reports",
        "objetivo": "Gerar relatório a partir de valuation.",
    },
    {
        "metodo": "POST",
        "rota": "/api/events",
        "objetivo": "Registrar evento de uso.",
    },
    {
        "metodo": "GET",
        "rota": "/api/me",
        "objetivo": "Buscar dados do usuário autenticado.",
    },
    {
        "metodo": "POST",
        "rota": "/api/payments/checkout",
        "objetivo": "Iniciar pagamento quando a monetização estiver validada.",
    },
]


FASES_TRANSICAO = [
    {
        "fase": "Fase 1",
        "nome": "Organizar dados",
        "quando": "Agora ou quando CSVs começarem a atrapalhar.",
        "entrega": "Mapear CSVs, padronizar campos e criar camada de acesso a dados.",
    },
    {
        "fase": "Fase 2",
        "nome": "Banco de dados",
        "quando": "Quando houver leads, fundadores e análises suficientes para justificar persistência real.",
        "entrega": "Criar PostgreSQL/Supabase e migrar tabelas essenciais.",
    },
    {
        "fase": "Fase 3",
        "nome": "API",
        "quando": "Quando a interface precisar deixar de ser Streamlit.",
        "entrega": "Criar FastAPI com endpoints de valuation, leads, relatórios e eventos.",
    },
    {
        "fase": "Fase 4",
        "nome": "Front-end moderno",
        "quando": "Quando produto, conversão e operação tiverem sinais fortes.",
        "entrega": "Criar Next.js/TypeScript para landing, área logada e dashboard premium.",
    },
    {
        "fase": "Fase 5",
        "nome": "Monetização escalável",
        "quando": "Depois de pagamento manual validado.",
        "entrega": "Integrar autenticação, planos, checkout e controle de acesso.",
    },
]


def _limpar_texto(valor: Any) -> str:
    if valor is None:
        return ""

    return str(valor).strip()


def _garantir_arquivo() -> None:
    if CAMINHO_DECISOES_ARQUITETURA.exists():
        return

    with CAMINHO_DECISOES_ARQUITETURA.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISAO_ARQUITETURA)
        escritor.writeheader()


def carregar_decisoes_arquitetura() -> List[Dict[str, str]]:
    _garantir_arquivo()

    with CAMINHO_DECISOES_ARQUITETURA.open("r", newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        return list(leitor)


def gerar_csv_decisoes_arquitetura() -> str:
    _garantir_arquivo()

    return CAMINHO_DECISOES_ARQUITETURA.read_text(encoding="utf-8")


def salvar_decisao_arquitetura(decisao: Dict[str, str]) -> Dict[str, str]:
    _garantir_arquivo()

    registro = {
        "id": str(uuid4())[:8],
        "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "estagio_recomendado": _limpar_texto(decisao.get("estagio_recomendado")),
        "stack_recomendada": _limpar_texto(decisao.get("stack_recomendada")),
        "risco_principal": _limpar_texto(decisao.get("risco_principal")),
        "prioridade_tecnica": _limpar_texto(decisao.get("prioridade_tecnica")),
        "proximo_passo": _limpar_texto(decisao.get("proximo_passo")),
        "observacoes": _limpar_texto(decisao.get("observacoes")),
    }

    with CAMINHO_DECISOES_ARQUITETURA.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISAO_ARQUITETURA)
        escritor.writerow(registro)

    return registro


def _obter_maturidade() -> Dict[str, Any]:
    try:
        return calcular_maturidade_produto_valoris()
    except Exception:
        return {
            "score_total": 0,
            "score_produto": 0,
            "score_ativacao": 0,
            "score_conversao": 0,
            "score_operacao": 0,
            "score_tecnico": 0,
            "classificacao": "Indisponível",
            "decisao": {
                "titulo": "Continuar validando manualmente",
                "descricao": "Não foi possível calcular maturidade automaticamente.",
            },
            "leads": 0,
            "fundadores": 0,
            "pagos": 0,
            "relatorios_feedback": 0,
            "validacoes": 0,
        }


def _decidir_estagio_tecnico(maturidade: Dict[str, Any]) -> Dict[str, str]:
    score_total = int(maturidade.get("score_total", 0) or 0)
    score_tecnico = int(maturidade.get("score_tecnico", 0) or 0)
    fundadores = int(maturidade.get("fundadores", 0) or 0)
    pagos = int(maturidade.get("pagos", 0) or 0)
    leads = int(maturidade.get("leads", 0) or 0)
    relatorios_feedback = int(maturidade.get("relatorios_feedback", 0) or 0)

    if score_total < 45 or leads < 5:
        return {
            "estagio_recomendado": "Continuar Streamlit",
            "stack_recomendada": "Python + Streamlit + CSV",
            "risco_principal": "Migrar cedo demais",
            "prioridade_tecnica": "Fortalecer núcleo de valuation",
            "proximo_passo": "Continuar validação, melhorar relatório e falar com usuários antes de mexer na arquitetura.",
        }

    if leads >= 5 and fundadores < 3:
        return {
            "estagio_recomendado": "Preparar banco local/SQL",
            "stack_recomendada": "Python + Streamlit + SQLite",
            "risco_principal": "Perder dados por excesso de CSV",
            "prioridade_tecnica": "Padronizar camada de dados",
            "proximo_passo": "Criar uma camada de dados que permita trocar CSV por banco sem reescrever o app inteiro.",
        }

    if fundadores >= 3 or leads >= 20:
        return {
            "estagio_recomendado": "Migrar CSVs para PostgreSQL/Supabase",
            "stack_recomendada": "Python + Streamlit + PostgreSQL/Supabase",
            "risco_principal": "Acumular dívida técnica no Streamlit",
            "prioridade_tecnica": "Modelar banco de dados",
            "proximo_passo": "Modelar tabelas e migrar leads, eventos, fundadores, relatórios e análises para banco real.",
        }

    if pagos >= 3 and relatorios_feedback >= 2 and score_tecnico >= 70:
        return {
            "estagio_recomendado": "Criar API Python/FastAPI",
            "stack_recomendada": "Python + FastAPI + PostgreSQL/Supabase",
            "risco_principal": "Criar API antes de validar uso",
            "prioridade_tecnica": "Criar endpoints da API",
            "proximo_passo": "Separar o motor de valuation e relatórios em API antes de iniciar front-end moderno.",
        }

    if score_total >= 85 and pagos >= 5:
        return {
            "estagio_recomendado": "Criar front-end TypeScript/Next.js",
            "stack_recomendada": "TypeScript + Next.js + FastAPI + PostgreSQL",
            "risco_principal": "Criar front-end bonito sem retenção",
            "prioridade_tecnica": "Criar design system e front-end",
            "proximo_passo": "Criar prova de conceito em Next.js para landing, área logada e dashboard premium.",
        }

    return {
        "estagio_recomendado": "Preparar banco local/SQL",
        "stack_recomendada": "Python + Streamlit + SQLite",
        "risco_principal": "Perder dados por excesso de CSV",
        "prioridade_tecnica": "Padronizar camada de dados",
        "proximo_passo": "Não migrar interface ainda. Primeiro organizar persistência e reduzir dependência de CSV.",
    }


def _gerar_markdown_arquitetura(decisao: Dict[str, str], maturidade: Dict[str, Any]) -> str:
    tabelas = "\n".join(
        [
            f"### {tabela['nome']}\nObjetivo: {tabela['objetivo']}\nCampos: `{tabela['campos']}`\n"
            for tabela in TABELAS_RECOMENDADAS
        ]
    )

    endpoints = "\n".join(
        [
            f"- `{endpoint['metodo']} {endpoint['rota']}` — {endpoint['objetivo']}"
            for endpoint in ENDPOINTS_RECOMENDADOS
        ]
    )

    fases = "\n".join(
        [
            f"### {fase['fase']} — {fase['nome']}\nQuando: {fase['quando']}\nEntrega: {fase['entrega']}\n"
            for fase in FASES_TRANSICAO
        ]
    )

    return f"""# Blueprint de Arquitetura — Valoris

Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Decisão recomendada

Estágio: {decisao["estagio_recomendado"]}  
Stack: {decisao["stack_recomendada"]}  
Risco principal: {decisao["risco_principal"]}  
Prioridade técnica: {decisao["prioridade_tecnica"]}  

Próximo passo:
{decisao["proximo_passo"]}

## Maturidade atual

Score geral: {maturidade.get("score_total", 0)}/100  
Classificação: {maturidade.get("classificacao", "N/D")}  
Decisão de produto: {maturidade.get("decisao", {}).get("titulo", "N/D")}  

Leads: {maturidade.get("leads", 0)}  
Fundadores: {maturidade.get("fundadores", 0)}  
Pagos: {maturidade.get("pagos", 0)}  
Relatórios/feedback: {maturidade.get("relatorios_feedback", 0)}  

## Modelo de banco recomendado

{tabelas}

## Endpoints futuros recomendados

{endpoints}

## Fases de transição

{fases}

## Regra estratégica

Python continua sendo o cérebro.  
SQL será a memória.  
FastAPI será a ponte.  
TypeScript/Next.js será a vitrine premium.  

Não trocar linguagem por ansiedade técnica. Trocar quando o produto provar que merece a nova arquitetura.
"""


def _injetar_css_arquitetura() -> None:
    st.markdown(
        """
        <style>
            .arq-hero {
                padding: clamp(1.18rem, 3vw, 2rem);
                border-radius: 30px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    radial-gradient(circle at top left, rgba(214, 181, 109, 0.26), transparent 30%),
                    radial-gradient(circle at bottom right, rgba(36, 128, 91, 0.24), transparent 34%),
                    linear-gradient(135deg, rgba(8, 15, 27, 0.99), rgba(5, 9, 18, 0.99));
                box-shadow: 0 18px 58px rgba(0, 0, 0, 0.31);
                margin-bottom: 1rem;
            }

            .arq-eyebrow {
                color: #d6b56d;
                font-size: 0.74rem;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                font-weight: 880;
                margin-bottom: 0.35rem;
            }

            .arq-title {
                color: #f4f7fb;
                font-size: clamp(1.75rem, 5.4vw, 3.1rem);
                font-weight: 950;
                line-height: 1.02;
                letter-spacing: -0.058em;
                margin-bottom: 0.55rem;
            }

            .arq-subtitle {
                color: rgba(244, 247, 251, 0.75);
                font-size: clamp(0.94rem, 2.2vw, 1.06rem);
                line-height: 1.56;
                max-width: 1020px;
            }

            .arq-note {
                padding: 0.92rem 0.98rem;
                border-radius: 17px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.90rem;
                line-height: 1.55;
                margin: 0.85rem 0;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _renderizar_hero() -> None:
    st.markdown(
        f"""
        <div class="arq-hero">
            <div class="arq-eyebrow">Valoris • Arquitetura • v{VERSAO_ARQUITETURA_TRANSICAO_VALORIS}</div>
            <div class="arq-title">Prepare a próxima arquitetura sem quebrar o MVP.</div>
            <div class="arq-subtitle">
                Este blueprint conecta maturidade do produto com decisão técnica:
                quando continuar no Streamlit, quando criar banco, quando criar API e quando iniciar TypeScript/Next.js.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _renderizar_resumo(decisao: Dict[str, str], maturidade: Dict[str, Any]) -> None:
    st.markdown("### Decisão técnica recomendada")

    col_1, col_2, col_3 = st.columns(3)

    with col_1:
        st.metric("Estágio", decisao["estagio_recomendado"])

    with col_2:
        st.metric("Score maturidade", f"{maturidade.get('score_total', 0)}/100")

    with col_3:
        st.metric("Prioridade", decisao["prioridade_tecnica"])

    st.info(decisao["proximo_passo"])

    st.warning(f"Risco principal: {decisao['risco_principal']}")


def _renderizar_fases() -> None:
    st.markdown("### Fases de transição recomendadas")

    for fase in FASES_TRANSICAO:
        with st.container(border=True):
            st.markdown(f"**{fase['fase']} — {fase['nome']}**")
            st.caption(f"Quando: {fase['quando']}")
            st.markdown(f"Entrega: {fase['entrega']}")


def _renderizar_tabelas() -> None:
    st.markdown("### Modelo de banco futuro")

    for tabela in TABELAS_RECOMENDADAS:
        with st.container(border=True):
            st.markdown(f"**{tabela['nome']}**")
            st.caption(tabela["objetivo"])
            st.code(tabela["campos"], language="text")


def _renderizar_endpoints() -> None:
    st.markdown("### Endpoints futuros da API")

    for endpoint in ENDPOINTS_RECOMENDADOS:
        with st.container(border=True):
            st.markdown(f"**{endpoint['metodo']} {endpoint['rota']}**")
            st.caption(endpoint["objetivo"])


def _renderizar_historico() -> None:
    historico = carregar_decisoes_arquitetura()

    st.markdown("### Histórico de decisões técnicas")

    if not historico:
        st.info("Ainda não há decisões de arquitetura salvas.")
        return

    for item in reversed(historico[-10:]):
        with st.container(border=True):
            st.markdown(f"**{item.get('estagio_recomendado', 'N/D')}**")
            st.caption(item.get("data_registro", "N/D"))
            st.markdown(f"Stack: {item.get('stack_recomendada', 'N/D')}")
            st.markdown(f"Próximo passo: {item.get('proximo_passo', 'N/D')}")


def renderizar_arquitetura_transicao_valoris() -> None:
    _injetar_css_arquitetura()
    _renderizar_hero()

    maturidade = _obter_maturidade()
    decisao = _decidir_estagio_tecnico(maturidade)

    _renderizar_resumo(decisao, maturidade)

    st.divider()

    _renderizar_fases()

    st.divider()

    _renderizar_tabelas()

    st.divider()

    _renderizar_endpoints()

    st.divider()

    col_1, col_2 = st.columns(2)

    with col_1:
        if st.button("Salvar decisão de arquitetura", key="salvar_decisao_arquitetura_valoris"):
            registro = salvar_decisao_arquitetura(
                {
                    **decisao,
                    "observacoes": f"Score maturidade: {maturidade.get('score_total', 0)}",
                }
            )

            st.success(f"Decisão salva: {registro['estagio_recomendado']} • {registro['stack_recomendada']}")
            st.rerun()

    with col_2:
        st.download_button(
            "Baixar blueprint técnico (.md)",
            data=_gerar_markdown_arquitetura(decisao, maturidade),
            file_name="blueprint_arquitetura_valoris.md",
            mime="text/markdown",
            key="download_blueprint_arquitetura_valoris",
        )

    st.download_button(
        "Baixar decisões de arquitetura (.csv)",
        data=gerar_csv_decisoes_arquitetura(),
        file_name="decisoes_arquitetura_valoris.csv",
        mime="text/csv",
        key="download_decisoes_arquitetura_valoris",
    )

    st.divider()

    _renderizar_historico()

    st.markdown(
        """
        <div class="arq-note">
            <strong>Regra de arquitetura:</strong> o Streamlit continua sendo laboratório e MVP.
            A arquitetura premium começa quando houver sinais suficientes para justificar banco, API e front-end moderno.
        </div>
        """,
        unsafe_allow_html=True,
    )


def executar_autoteste_arquitetura_transicao_valoris() -> List[Dict[str, str]]:
    maturidade = {
        "score_total": 60,
        "score_tecnico": 55,
        "fundadores": 1,
        "pagos": 0,
        "leads": 10,
        "relatorios_feedback": 0,
    }

    decisao = _decidir_estagio_tecnico(maturidade)

    return [
        {
            "teste": "versao_arquitetura",
            "status": "OK" if VERSAO_ARQUITETURA_TRANSICAO_VALORIS == "3.8.55" else "FALHA",
            "detalhe": VERSAO_ARQUITETURA_TRANSICAO_VALORIS,
        },
        {
            "teste": "decisao",
            "status": "OK" if decisao["estagio_recomendado"] != "" else "FALHA",
            "detalhe": decisao["estagio_recomendado"],
        },
        {
            "teste": "tabelas",
            "status": "OK" if len(TABELAS_RECOMENDADAS) >= 5 else "FALHA",
            "detalhe": str(len(TABELAS_RECOMENDADAS)),
        },
    ]
