# camada_dados_valoris.py

from __future__ import annotations

import csv
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

import streamlit as st

from arquitetura_transicao_valoris import TABELAS_RECOMENDADAS
from maturidade_produto_valoris import calcular_maturidade_produto_valoris


# ============================================================
# VALORIS
# v3.8.56 — Camada de Dados e Preparação para Banco
# ------------------------------------------------------------
# Este módulo é a ponte prática entre CSV e banco real.
#
# Objetivo:
# - mapear arquivos CSV locais;
# - verificar saúde dos dados;
# - gerar backup simples;
# - sugerir tabelas futuras;
# - criar DDL inicial para PostgreSQL/Supabase;
# - reduzir dependência de CSV antes de criar API/front-end.
# ============================================================


VERSAO_CAMADA_DADOS_VALORIS = "3.8.56"

PASTA_BACKUPS_DADOS = Path("backups_dados_valoris")
CAMINHO_DECISOES_DADOS = Path("decisoes_dados_valoris.csv")

CAMPOS_DECISAO_DADOS = [
    "id",
    "data_registro",
    "score_dados",
    "arquivos_detectados",
    "linhas_totais",
    "arquivos_criticos_ausentes",
    "decisao",
    "proximo_passo",
    "observacoes",
]


CATALOGO_CSVS_VALORIS = [
    {
        "arquivo": "lista_espera_beta.csv",
        "dominio": "leads",
        "tabela_futura": "leads",
        "criticidade": "Alta",
        "descricao": "Lista de espera, contatos, dores, plano de interesse e intenção de pagamento.",
    },
    {
        "arquivo": "eventos_publicos_valoris.csv",
        "dominio": "analytics",
        "tabela_futura": "events",
        "criticidade": "Média",
        "descricao": "Eventos públicos de landing, demo, lista beta e interações.",
    },
    {
        "arquivo": "progresso_trilha_valoris.csv",
        "dominio": "educacao",
        "tabela_futura": "events",
        "criticidade": "Média",
        "descricao": "Progresso e pontuação da trilha educativa.",
    },
    {
        "arquivo": "diagnosticos_copiloto_valoris.csv",
        "dominio": "copiloto",
        "tabela_futura": "events",
        "criticidade": "Média",
        "descricao": "Diagnósticos do Copiloto Valoris.",
    },
    {
        "arquivo": "jornadas_personalizadas_valoris.csv",
        "dominio": "jornada",
        "tabela_futura": "events",
        "criticidade": "Média",
        "descricao": "Rotas recomendadas e bloqueios dos usuários.",
    },
    {
        "arquivo": "ativacao_valoris.csv",
        "dominio": "ativacao",
        "tabela_futura": "events",
        "criticidade": "Média",
        "descricao": "Checklist e score de ativação.",
    },
    {
        "arquivo": "sinais_conversao_valoris.csv",
        "dominio": "conversao",
        "tabela_futura": "events",
        "criticidade": "Alta",
        "descricao": "Sinais de intenção comercial e barreiras de compra.",
    },
    {
        "arquivo": "experimentos_growth_valoris.csv",
        "dominio": "growth",
        "tabela_futura": "events",
        "criticidade": "Média",
        "descricao": "Experimentos de growth, score e decisão.",
    },
    {
        "arquivo": "validacoes_manuais_valoris.csv",
        "dominio": "validacao",
        "tabela_futura": "founders",
        "criticidade": "Alta",
        "descricao": "Conversas manuais, objeções, intenção e próximos passos.",
    },
    {
        "arquivo": "fundadores_valoris.csv",
        "dominio": "fundadores",
        "tabela_futura": "founders",
        "criticidade": "Alta",
        "descricao": "Usuários fundadores, pagamento manual, acesso, onboarding e feedback.",
    },
    {
        "arquivo": "decisoes_maturidade_valoris.csv",
        "dominio": "produto",
        "tabela_futura": "events",
        "criticidade": "Baixa",
        "descricao": "Histórico de decisões de maturidade do produto.",
    },
    {
        "arquivo": "decisoes_arquitetura_valoris.csv",
        "dominio": "arquitetura",
        "tabela_futura": "events",
        "criticidade": "Baixa",
        "descricao": "Histórico de decisões técnicas e arquitetura.",
    },
]


DDL_POSTGRES_INICIAL = """
-- Blueprint inicial PostgreSQL/Supabase para a Valoris
-- v3.8.56 — rascunho para futura migração

create table if not exists users (
    id uuid primary key default gen_random_uuid(),
    nome text,
    email text unique,
    perfil text,
    plano text,
    status text default 'active',
    created_at timestamp with time zone default now()
);

create table if not exists leads (
    id uuid primary key default gen_random_uuid(),
    nome text,
    contato text,
    perfil text,
    dor text,
    plano_interesse text,
    preco_aceitavel text,
    pagaria_agora text,
    origem text,
    created_at timestamp with time zone default now()
);

create table if not exists valuations (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references users(id),
    ticker text,
    preco_atual numeric,
    preco_teto numeric,
    preco_justo numeric,
    margem_seguranca numeric,
    status text,
    premissas jsonb,
    created_at timestamp with time zone default now()
);

create table if not exists reports (
    id uuid primary key default gen_random_uuid(),
    valuation_id uuid references valuations(id),
    user_id uuid references users(id),
    titulo text,
    tipo text,
    conteudo text,
    metadata jsonb,
    created_at timestamp with time zone default now()
);

create table if not exists events (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references users(id),
    session_id text,
    event_name text not null,
    context text,
    value text,
    metadata jsonb,
    created_at timestamp with time zone default now()
);

create table if not exists founders (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references users(id),
    nome text,
    contato text,
    plano text,
    valor_combinado text,
    status_pagamento text,
    status_acesso text,
    etapa_onboarding text,
    feedback text,
    risco_churn text,
    nivel_entusiasmo text,
    created_at timestamp with time zone default now()
);

create table if not exists payments (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references users(id),
    provider text,
    amount numeric,
    currency text default 'BRL',
    status text,
    external_id text,
    paid_at timestamp with time zone,
    created_at timestamp with time zone default now()
);
""".strip()


def _limpar_texto(valor: Any) -> str:
    if valor is None:
        return ""

    return str(valor).strip()


def _garantir_arquivo_decisoes() -> None:
    if CAMINHO_DECISOES_DADOS.exists():
        return

    with CAMINHO_DECISOES_DADOS.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISAO_DADOS)
        escritor.writeheader()


def carregar_decisoes_dados() -> List[Dict[str, str]]:
    _garantir_arquivo_decisoes()

    with CAMINHO_DECISOES_DADOS.open("r", newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        return list(leitor)


def gerar_csv_decisoes_dados() -> str:
    _garantir_arquivo_decisoes()

    return CAMINHO_DECISOES_DADOS.read_text(encoding="utf-8")


def salvar_decisao_dados(decisao: Dict[str, Any]) -> Dict[str, str]:
    _garantir_arquivo_decisoes()

    registro = {
        "id": str(uuid4())[:8],
        "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score_dados": str(decisao.get("score_dados", "")),
        "arquivos_detectados": str(decisao.get("arquivos_detectados", "")),
        "linhas_totais": str(decisao.get("linhas_totais", "")),
        "arquivos_criticos_ausentes": str(decisao.get("arquivos_criticos_ausentes", "")),
        "decisao": _limpar_texto(decisao.get("decisao", "")),
        "proximo_passo": _limpar_texto(decisao.get("proximo_passo", "")),
        "observacoes": _limpar_texto(decisao.get("observacoes", "")),
    }

    with CAMINHO_DECISOES_DADOS.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISAO_DADOS)
        escritor.writerow(registro)

    return registro


def _contar_linhas_csv(caminho: Path) -> int:
    if not caminho.exists():
        return 0

    try:
        with caminho.open("r", newline="", encoding="utf-8") as arquivo:
            leitor = csv.reader(arquivo)
            linhas = list(leitor)

        if not linhas:
            return 0

        return max(0, len(linhas) - 1)

    except Exception:
        return 0


def _ler_cabecalho_csv(caminho: Path) -> List[str]:
    if not caminho.exists():
        return []

    try:
        with caminho.open("r", newline="", encoding="utf-8") as arquivo:
            leitor = csv.reader(arquivo)
            return next(leitor, [])
    except Exception:
        return []


def inventariar_csvs_valoris() -> List[Dict[str, Any]]:
    inventario = []

    for item in CATALOGO_CSVS_VALORIS:
        caminho = Path(item["arquivo"])
        existe = caminho.exists()
        linhas = _contar_linhas_csv(caminho)
        cabecalho = _ler_cabecalho_csv(caminho)

        if existe and linhas > 0:
            status = "Ativo"
        elif existe:
            status = "Criado sem dados"
        else:
            status = "Ausente"

        inventario.append(
            {
                **item,
                "existe": existe,
                "linhas": linhas,
                "cabecalho": cabecalho,
                "status": status,
                "tamanho_bytes": caminho.stat().st_size if existe else 0,
            }
        )

    return inventario


def calcular_saude_dados_valoris() -> Dict[str, Any]:
    inventario = inventariar_csvs_valoris()

    arquivos_detectados = len([item for item in inventario if item["existe"]])
    linhas_totais = sum([int(item["linhas"]) for item in inventario])
    criticos_ausentes = [
        item["arquivo"] for item in inventario
        if item["criticidade"] == "Alta" and not item["existe"]
    ]
    arquivos_com_dados = len([item for item in inventario if item["linhas"] > 0])

    score = 25
    score += min(arquivos_detectados * 4, 32)
    score += min(arquivos_com_dados * 5, 30)
    score += min(linhas_totais * 1.5, 20)
    score -= len(criticos_ausentes) * 10

    score = int(round(max(0, min(100, score))))

    if score >= 80:
        decisao = "Pronto para modelar banco"
        proximo_passo = "Criar camada de acesso a dados e começar migração planejada para PostgreSQL/Supabase."
    elif score >= 60:
        decisao = "Preparar padronização"
        proximo_passo = "Padronizar campos, criar backups e mapear quais CSVs viram tabelas."
    elif score >= 40:
        decisao = "Continuar CSV com disciplina"
        proximo_passo = "Manter MVP em CSV, mas usar backup e catálogo para não perder dados."
    else:
        decisao = "Poucos dados para migrar"
        proximo_passo = "Foque em gerar leads, validações e fundadores antes de pensar em banco."

    return {
        "inventario": inventario,
        "arquivos_detectados": arquivos_detectados,
        "linhas_totais": linhas_totais,
        "arquivos_com_dados": arquivos_com_dados,
        "criticos_ausentes": criticos_ausentes,
        "score_dados": score,
        "decisao": decisao,
        "proximo_passo": proximo_passo,
    }


def criar_backup_dados_valoris() -> Dict[str, Any]:
    inventario = inventariar_csvs_valoris()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pasta = PASTA_BACKUPS_DADOS / f"backup_{timestamp}"
    pasta.mkdir(parents=True, exist_ok=True)

    copiados = []

    for item in inventario:
        origem = Path(item["arquivo"])

        if origem.exists():
            destino = pasta / origem.name
            shutil.copy2(origem, destino)
            copiados.append(origem.name)

    manifesto = {
        "id": str(uuid4())[:8],
        "data_backup": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "arquivos": copiados,
        "total_arquivos": len(copiados),
    }

    (pasta / "manifesto_backup_valoris.json").write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return {
        "pasta": str(pasta),
        "copiados": copiados,
        "manifesto": manifesto,
    }


def _obter_maturidade() -> Dict[str, Any]:
    try:
        return calcular_maturidade_produto_valoris()
    except Exception:
        return {
            "score_total": 0,
            "classificacao": "Indisponível",
            "leads": 0,
            "fundadores": 0,
            "pagos": 0,
        }


def _gerar_markdown_dados(saude: Dict[str, Any], maturidade: Dict[str, Any]) -> str:
    linhas_inventario = "\n".join(
        [
            f"| {item['arquivo']} | {item['dominio']} | {item['criticidade']} | {item['status']} | {item['linhas']} | {item['tabela_futura']} |"
            for item in saude["inventario"]
        ]
    )

    tabelas = "\n".join(
        [
            f"- **{item['nome']}** — {item['objetivo']} Campos: `{item['campos']}`"
            for item in TABELAS_RECOMENDADAS
        ]
    )

    criticos = "\n".join([f"- {item}" for item in saude["criticos_ausentes"]]) or "- Nenhum"

    return f"""# Camada de Dados — Valoris

Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Diagnóstico

Score de dados: {saude["score_dados"]}/100  
Decisão: {saude["decisao"]}  
Próximo passo: {saude["proximo_passo"]}

Arquivos detectados: {saude["arquivos_detectados"]}  
Arquivos com dados: {saude["arquivos_com_dados"]}  
Linhas totais: {saude["linhas_totais"]}  

## Arquivos críticos ausentes

{criticos}

## Maturidade do produto

Score geral: {maturidade.get("score_total", 0)}/100  
Classificação: {maturidade.get("classificacao", "N/D")}  
Leads: {maturidade.get("leads", 0)}  
Fundadores: {maturidade.get("fundadores", 0)}  
Pagos: {maturidade.get("pagos", 0)}  

## Inventário CSV

| Arquivo | Domínio | Criticidade | Status | Linhas | Tabela futura |
|---|---|---|---|---:|---|
{linhas_inventario}

## Tabelas futuras recomendadas

{tabelas}

## DDL inicial PostgreSQL/Supabase

```sql
{DDL_POSTGRES_INICIAL}
```

## Regra estratégica

CSV é bom para MVP.  
Banco é necessário quando há dados reais, usuários, histórico e operação.  
A transição deve ser gradual: catálogo → backup → camada de dados → banco → API.
"""


def _injetar_css_dados() -> None:
    st.markdown(
        """
        <style>
            .dados-hero {
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

            .dados-eyebrow {
                color: #d6b56d;
                font-size: 0.74rem;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                font-weight: 880;
                margin-bottom: 0.35rem;
            }

            .dados-title {
                color: #f4f7fb;
                font-size: clamp(1.75rem, 5.4vw, 3.1rem);
                font-weight: 950;
                line-height: 1.02;
                letter-spacing: -0.058em;
                margin-bottom: 0.55rem;
            }

            .dados-subtitle {
                color: rgba(244, 247, 251, 0.75);
                font-size: clamp(0.94rem, 2.2vw, 1.06rem);
                line-height: 1.56;
                max-width: 1020px;
            }

            .dados-note {
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
        <div class="dados-hero">
            <div class="dados-eyebrow">Valoris • Dados • v{VERSAO_CAMADA_DADOS_VALORIS}</div>
            <div class="dados-title">Organize os dados antes de criar banco e API.</div>
            <div class="dados-subtitle">
                Esta camada mapeia os CSVs do MVP, mede saúde dos dados, gera backup e prepara
                o desenho inicial de PostgreSQL/Supabase sem abandonar o Streamlit antes da hora.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _renderizar_metricas(saude: Dict[str, Any]) -> None:
    st.markdown("### Diagnóstico dos dados")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Score dados", f"{saude['score_dados']}/100")

    with col_2:
        st.metric("Arquivos detectados", saude["arquivos_detectados"])

    with col_3:
        st.metric("Arquivos com dados", saude["arquivos_com_dados"])

    with col_4:
        st.metric("Linhas totais", saude["linhas_totais"])

    st.progress(saude["score_dados"] / 100)

    if saude["score_dados"] >= 70:
        st.success(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    elif saude["score_dados"] >= 40:
        st.warning(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    else:
        st.info(f"**{saude['decisao']}** — {saude['proximo_passo']}")


def _renderizar_inventario(saude: Dict[str, Any]) -> None:
    st.markdown("### Inventário de CSVs")

    for item in saude["inventario"]:
        with st.container(border=True):
            st.markdown(f"**{item['arquivo']}** — {item['status']}")
            st.caption(
                f"Domínio: {item['dominio']} • Criticidade: {item['criticidade']} • Tabela futura: {item['tabela_futura']}"
            )
            st.markdown(item["descricao"])
            st.markdown(f"Linhas: **{item['linhas']}** • Tamanho: **{item['tamanho_bytes']} bytes**")

            if item["cabecalho"]:
                st.code(", ".join(item["cabecalho"]), language="text")


def _renderizar_modelo_banco() -> None:
    st.markdown("### Modelo de banco recomendado")

    for tabela in TABELAS_RECOMENDADAS:
        with st.container(border=True):
            st.markdown(f"**{tabela['nome']}**")
            st.caption(tabela["objetivo"])
            st.code(tabela["campos"], language="text")


def _renderizar_ddl() -> None:
    st.markdown("### DDL inicial PostgreSQL/Supabase")

    st.code(DDL_POSTGRES_INICIAL, language="sql")

    st.download_button(
        "Baixar DDL PostgreSQL/Supabase (.sql)",
        data=DDL_POSTGRES_INICIAL,
        file_name="valoris_schema_inicial.sql",
        mime="text/sql",
        key="download_ddl_valoris",
    )


def _renderizar_historico() -> None:
    historico = carregar_decisoes_dados()

    st.markdown("### Histórico de decisões de dados")

    if not historico:
        st.info("Ainda não há decisões de dados salvas.")
        return

    for item in reversed(historico[-10:]):
        with st.container(border=True):
            st.markdown(f"**{item.get('decisao', 'N/D')}**")
            st.caption(item.get("data_registro", "N/D"))
            st.markdown(f"Score: {item.get('score_dados', 'N/D')}/100")
            st.markdown(f"Próximo passo: {item.get('proximo_passo', 'N/D')}")


def renderizar_camada_dados_valoris() -> None:
    _injetar_css_dados()
    _renderizar_hero()

    saude = calcular_saude_dados_valoris()
    maturidade = _obter_maturidade()

    _renderizar_metricas(saude)

    st.divider()

    col_1, col_2 = st.columns(2)

    with col_1:
        if st.button("Criar backup dos CSVs detectados", key="criar_backup_dados_valoris"):
            resultado = criar_backup_dados_valoris()
            st.success(
                f"Backup criado em {resultado['pasta']} com {len(resultado['copiados'])} arquivo(s)."
            )

    with col_2:
        if st.button("Salvar decisão de dados", key="salvar_decisao_dados_valoris"):
            registro = salvar_decisao_dados(
                {
                    "score_dados": saude["score_dados"],
                    "arquivos_detectados": saude["arquivos_detectados"],
                    "linhas_totais": saude["linhas_totais"],
                    "arquivos_criticos_ausentes": len(saude["criticos_ausentes"]),
                    "decisao": saude["decisao"],
                    "proximo_passo": saude["proximo_passo"],
                    "observacoes": f"Maturidade produto: {maturidade.get('score_total', 0)}/100",
                }
            )
            st.success(f"Decisão salva: {registro['decisao']}")
            st.rerun()

    st.download_button(
        "Baixar diagnóstico da camada de dados (.md)",
        data=_gerar_markdown_dados(saude, maturidade),
        file_name="camada_dados_valoris.md",
        mime="text/markdown",
        key="download_camada_dados_valoris",
    )

    st.download_button(
        "Baixar decisões de dados (.csv)",
        data=gerar_csv_decisoes_dados(),
        file_name="decisoes_dados_valoris.csv",
        mime="text/csv",
        key="download_decisoes_dados_valoris",
    )

    st.divider()

    _renderizar_inventario(saude)

    st.divider()

    _renderizar_modelo_banco()

    st.divider()

    _renderizar_ddl()

    st.divider()

    _renderizar_historico()

    st.markdown(
        """
        <div class="dados-note">
            <strong>Regra dos dados:</strong> não migre para banco por ansiedade.
            Primeiro inventarie, faça backup, padronize campos e só depois conecte PostgreSQL/Supabase.
        </div>
        """,
        unsafe_allow_html=True,
    )


def executar_autoteste_camada_dados_valoris() -> List[Dict[str, str]]:
    saude = calcular_saude_dados_valoris()

    return [
        {
            "teste": "versao_camada_dados",
            "status": "OK" if VERSAO_CAMADA_DADOS_VALORIS == "3.8.56" else "FALHA",
            "detalhe": VERSAO_CAMADA_DADOS_VALORIS,
        },
        {
            "teste": "catalogo_csvs",
            "status": "OK" if len(CATALOGO_CSVS_VALORIS) >= 8 else "FALHA",
            "detalhe": str(len(CATALOGO_CSVS_VALORIS)),
        },
        {
            "teste": "score_dados",
            "status": "OK" if 0 <= saude["score_dados"] <= 100 else "FALHA",
            "detalhe": str(saude["score_dados"]),
        },
    ]
