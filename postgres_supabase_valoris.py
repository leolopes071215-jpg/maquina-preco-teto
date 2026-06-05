# postgres_supabase_valoris.py

from __future__ import annotations

import csv
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

import streamlit as st

from camada_dados_valoris import DDL_POSTGRES_INICIAL
from piloto_sqlite_valoris import calcular_saude_sqlite
from repositorios_valoris import calcular_saude_repositorios


# ============================================================
# VALORIS
# v3.8.60.1 — Preparação PostgreSQL/Supabase
# ------------------------------------------------------------
# Correção da v3.8.60:
# - garante a função renderizar_postgres_supabase_valoris;
# - mantém o módulo sem dependência externa de banco;
# - prepara variáveis, DDL, manifesto e plano de migração.
# ============================================================


VERSAO_POSTGRES_SUPABASE_VALORIS = "3.8.60.1"

CAMINHO_DECISOES_POSTGRES = Path("decisoes_postgres_supabase_valoris.csv")
CAMINHO_MANIFESTO_POSTGRES = Path("manifesto_postgres_supabase_valoris.json")
CAMINHO_ENV_EXEMPLO = Path(".env.example.valoris")
CAMINHO_SQL_POSTGRES = Path("valoris_schema_postgres_supabase.sql")

CAMPOS_DECISAO_POSTGRES = [
    "id",
    "data_registro",
    "score_prontidao",
    "database_url_configurada",
    "supabase_url_configurada",
    "sqlite_score",
    "repositorio_score",
    "decisao",
    "proximo_passo",
    "observacoes",
]


VARIAVEIS_AMBIENTE_RECOMENDADAS = [
    {
        "nome": "VALORIS_DATABASE_URL",
        "obrigatoria": True,
        "descricao": "String de conexão PostgreSQL/Supabase. Deve ficar fora do Git.",
        "exemplo": "postgresql://postgres:senha@host:5432/postgres",
    },
    {
        "nome": "SUPABASE_URL",
        "obrigatoria": False,
        "descricao": "URL do projeto Supabase, útil se futuramente usarmos API Supabase.",
        "exemplo": "https://seu-projeto.supabase.co",
    },
    {
        "nome": "SUPABASE_SERVICE_ROLE_KEY",
        "obrigatoria": False,
        "descricao": "Chave server-side. Nunca deve ir para o Git nem para o front-end.",
        "exemplo": "sua-chave-service-role",
    },
    {
        "nome": "SUPABASE_ANON_KEY",
        "obrigatoria": False,
        "descricao": "Chave pública para front-end futuro, ainda não necessária no Streamlit MVP.",
        "exemplo": "sua-chave-anon",
    },
    {
        "nome": "VALORIS_ENV",
        "obrigatoria": False,
        "descricao": "Ambiente atual da aplicação.",
        "exemplo": "local",
    },
]


PLANO_MIGRACAO_POSTGRES = [
    {
        "fase": "1",
        "nome": "Manter CSV/SQLite como fonte segura",
        "objetivo": "Evitar quebrar o MVP enquanto o banco externo é preparado.",
        "entrega": "Gateway, SQLite e Repositórios continuam funcionando.",
    },
    {
        "fase": "2",
        "nome": "Criar projeto Supabase/PostgreSQL",
        "objetivo": "Ter banco real pronto para receber dados.",
        "entrega": "Database URL segura, tabelas criadas e acesso testado.",
    },
    {
        "fase": "3",
        "nome": "Migrar dados piloto",
        "objetivo": "Levar leads, validações, fundadores e eventos para PostgreSQL.",
        "entrega": "Importação controlada, sem remover os CSVs ainda.",
    },
    {
        "fase": "4",
        "nome": "Criar PostgresAdapter",
        "objetivo": "Fazer o repositório trocar CSV/SQLite por PostgreSQL.",
        "entrega": "Mesmo contrato de leitura com novo adapter.",
    },
    {
        "fase": "5",
        "nome": "Criar FastAPI",
        "objetivo": "Separar backend de interface.",
        "entrega": "Endpoints de leads, valuation, reports, events e founders.",
    },
]


TABELAS_PRIORITARIAS_MIGRACAO = [
    {
        "tabela": "leads",
        "prioridade": "Alta",
        "motivo": "Base comercial e lista beta. É o primeiro ativo real do produto.",
    },
    {
        "tabela": "events",
        "prioridade": "Alta",
        "motivo": "Permite medir ativação, conversão e comportamento sem depender de CSV.",
    },
    {
        "tabela": "founders",
        "prioridade": "Alta",
        "motivo": "Organiza usuários fundadores, onboarding, acesso e feedback.",
    },
    {
        "tabela": "valuations",
        "prioridade": "Média",
        "motivo": "Ganha importância quando usuários começarem a salvar análises reais.",
    },
    {
        "tabela": "reports",
        "prioridade": "Média",
        "motivo": "Será essencial para histórico do usuário e área premium.",
    },
    {
        "tabela": "payments",
        "prioridade": "Média",
        "motivo": "Só deve ser ativada depois de pagamento manual validado.",
    },
]


POSTGRES_ADAPTER_RASCUNHO = """
class PostgresAdapter:
    nome = "PostgreSQL"

    def __init__(self, database_url: str):
        self.database_url = database_url

    def listar(self, tabela_logica: str, limite: int = 50) -> list[dict]:
        # Futuro:
        # - mapear tabela_logica para tabela real;
        # - abrir conexão PostgreSQL;
        # - executar SELECT seguro;
        # - retornar lista de dicts.
        raise NotImplementedError("PostgresAdapter ainda não está ativo.")

    def contar(self, tabela_logica: str) -> int:
        # Futuro:
        # - contar registros da tabela real;
        # - manter mesma interface do CsvAdapter/SqliteAdapter.
        raise NotImplementedError("PostgresAdapter ainda não está ativo.")
""".strip()


def _limpar_texto(valor: Any) -> str:
    if valor is None:
        return ""
    return str(valor).strip()


def _garantir_csv(caminho: Path, campos: List[str]) -> None:
    if caminho.exists():
        return

    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()


def carregar_decisoes_postgres() -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_DECISOES_POSTGRES, CAMPOS_DECISAO_POSTGRES)
    with CAMINHO_DECISOES_POSTGRES.open("r", newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        return list(leitor)


def gerar_csv_decisoes_postgres() -> str:
    _garantir_csv(CAMINHO_DECISOES_POSTGRES, CAMPOS_DECISAO_POSTGRES)
    return CAMINHO_DECISOES_POSTGRES.read_text(encoding="utf-8")


def salvar_decisao_postgres(decisao: Dict[str, Any]) -> Dict[str, str]:
    _garantir_csv(CAMINHO_DECISOES_POSTGRES, CAMPOS_DECISAO_POSTGRES)

    registro = {
        "id": str(uuid4())[:8],
        "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score_prontidao": str(decisao.get("score_prontidao", "")),
        "database_url_configurada": str(decisao.get("database_url_configurada", "")),
        "supabase_url_configurada": str(decisao.get("supabase_url_configurada", "")),
        "sqlite_score": str(decisao.get("sqlite_score", "")),
        "repositorio_score": str(decisao.get("repositorio_score", "")),
        "decisao": _limpar_texto(decisao.get("decisao", "")),
        "proximo_passo": _limpar_texto(decisao.get("proximo_passo", "")),
        "observacoes": _limpar_texto(decisao.get("observacoes", "")),
    }

    with CAMINHO_DECISOES_POSTGRES.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISAO_POSTGRES)
        escritor.writerow(registro)

    return registro


def verificar_variaveis_ambiente() -> List[Dict[str, Any]]:
    resultados = []

    for variavel in VARIAVEIS_AMBIENTE_RECOMENDADAS:
        nome = variavel["nome"]
        valor = os.getenv(nome, "")
        configurada = bool(valor.strip())

        if configurada:
            visualizacao = valor[:12] + "..." if len(valor) > 12 else "***"
        else:
            visualizacao = ""

        resultados.append(
            {
                **variavel,
                "configurada": configurada,
                "visualizacao": visualizacao,
            }
        )

    return resultados


def gerar_env_exemplo() -> str:
    linhas = [
        "# .env.example.valoris",
        "# Copie para .env local se for configurar PostgreSQL/Supabase.",
        "# Nunca suba .env real para o Git.",
        "",
    ]

    for variavel in VARIAVEIS_AMBIENTE_RECOMENDADAS:
        linhas.append(f"# {variavel['descricao']}")
        linhas.append(f'{variavel["nome"]}="{variavel["exemplo"]}"')
        linhas.append("")

    conteudo = "\n".join(linhas).strip() + "\n"
    CAMINHO_ENV_EXEMPLO.write_text(conteudo, encoding="utf-8")
    return conteudo


def gerar_sql_postgres() -> str:
    conteudo = DDL_POSTGRES_INICIAL.strip() + "\n"
    CAMINHO_SQL_POSTGRES.write_text(conteudo, encoding="utf-8")
    return conteudo


def calcular_prontidao_postgres() -> Dict[str, Any]:
    variaveis = verificar_variaveis_ambiente()

    try:
        saude_sqlite = calcular_saude_sqlite()
    except Exception:
        saude_sqlite = {"score_sqlite": 0, "linhas_totais": 0, "tabelas_criadas": 0}

    try:
        saude_repositorios = calcular_saude_repositorios()
    except Exception:
        saude_repositorios = {
            "score_repositorio": 0,
            "adapter_recomendado": "CSV",
            "leituras_ok": 0,
            "tabelas_testadas": 0,
        }

    database_url_configurada = any(
        item["nome"] == "VALORIS_DATABASE_URL" and item["configurada"]
        for item in variaveis
    )
    supabase_url_configurada = any(
        item["nome"] == "SUPABASE_URL" and item["configurada"]
        for item in variaveis
    )

    sqlite_score = int(saude_sqlite.get("score_sqlite", 0) or 0)
    repositorio_score = int(saude_repositorios.get("score_repositorio", 0) or 0)
    sqlite_linhas = int(saude_sqlite.get("linhas_totais", 0) or 0)
    sqlite_tabelas = int(saude_sqlite.get("tabelas_criadas", 0) or 0)

    score = 20
    score += min(sqlite_score * 0.30, 30)
    score += min(repositorio_score * 0.30, 30)
    score += 12 if database_url_configurada else 0
    score += 6 if supabase_url_configurada else 0
    score += 8 if sqlite_linhas > 0 else 0
    score = int(round(max(0, min(100, score))))

    if score >= 82 and database_url_configurada:
        decisao = "Pronto para testar PostgresAdapter"
        proximo_passo = "Criar teste controlado de conexão e leitura em PostgreSQL/Supabase."
    elif score >= 65:
        decisao = "Preparar credenciais e projeto Supabase"
        proximo_passo = "Criar projeto Supabase, salvar DATABASE_URL local e rodar DDL manualmente."
    elif score >= 45:
        decisao = "Consolidar SQLite/Repositórios antes do PostgreSQL"
        proximo_passo = "Garanta que SQLite e Repositórios estejam sincronizados antes de conectar banco externo."
    else:
        decisao = "Ainda cedo para PostgreSQL"
        proximo_passo = "Continue usando CSV/SQLite até ter dados e contratos mais consistentes."

    return {
        "score_prontidao": score,
        "variaveis": variaveis,
        "database_url_configurada": database_url_configurada,
        "supabase_url_configurada": supabase_url_configurada,
        "sqlite_score": sqlite_score,
        "sqlite_linhas": sqlite_linhas,
        "sqlite_tabelas": sqlite_tabelas,
        "repositorio_score": repositorio_score,
        "adapter_recomendado": saude_repositorios.get("adapter_recomendado", "CSV"),
        "decisao": decisao,
        "proximo_passo": proximo_passo,
    }


def gerar_manifesto_postgres() -> Dict[str, Any]:
    prontidao = calcular_prontidao_postgres()

    manifesto = {
        "versao": VERSAO_POSTGRES_SUPABASE_VALORIS,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score_prontidao": prontidao["score_prontidao"],
        "decisao": prontidao["decisao"],
        "proximo_passo": prontidao["proximo_passo"],
        "database_url_configurada": prontidao["database_url_configurada"],
        "supabase_url_configurada": prontidao["supabase_url_configurada"],
        "sqlite_score": prontidao["sqlite_score"],
        "repositorio_score": prontidao["repositorio_score"],
        "plano_migracao": PLANO_MIGRACAO_POSTGRES,
        "tabelas_prioritarias": TABELAS_PRIORITARIAS_MIGRACAO,
    }

    CAMINHO_MANIFESTO_POSTGRES.write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return manifesto


def _gerar_markdown_postgres(prontidao: Dict[str, Any]) -> str:
    variaveis = "\n".join(
        [
            f"| {item['nome']} | {'Sim' if item['configurada'] else 'Não'} | {'Sim' if item['obrigatoria'] else 'Não'} | {item['descricao']} |"
            for item in prontidao["variaveis"]
        ]
    )

    fases = "\n".join(
        [
            f"### Fase {item['fase']} — {item['nome']}\nObjetivo: {item['objetivo']}\nEntrega: {item['entrega']}\n"
            for item in PLANO_MIGRACAO_POSTGRES
        ]
    )

    tabelas = "\n".join(
        [
            f"- **{item['tabela']}** ({item['prioridade']}) — {item['motivo']}"
            for item in TABELAS_PRIORITARIAS_MIGRACAO
        ]
    )

    return f"""# Preparação PostgreSQL/Supabase — Valoris

Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Diagnóstico

Score de prontidão: {prontidao["score_prontidao"]}/100  
Decisão: {prontidao["decisao"]}  
Próximo passo: {prontidao["proximo_passo"]}

Database URL configurada: {prontidao["database_url_configurada"]}  
Supabase URL configurada: {prontidao["supabase_url_configurada"]}  
Score SQLite: {prontidao["sqlite_score"]}/100  
Score Repositório: {prontidao["repositorio_score"]}/100  
Adapter atual recomendado: {prontidao["adapter_recomendado"]}

## Variáveis de ambiente

| Variável | Configurada | Obrigatória | Descrição |
|---|---|---|---|
{variaveis}

## Tabelas prioritárias

{tabelas}

## Plano de migração

{fases}

## DDL inicial

```sql
{DDL_POSTGRES_INICIAL}
```

## Rascunho do PostgresAdapter

```python
{POSTGRES_ADAPTER_RASCUNHO}
```

## Regra

Não conectar PostgreSQL em produção antes de:
1. SQLite estar funcionando;
2. Repositórios estarem testados;
3. .env estar seguro;
4. tabelas prioritárias estarem claras;
5. migração estar reversível.
"""


def _injetar_css_postgres() -> None:
    st.markdown(
        """
        <style>
            .pg-hero {
                padding: clamp(1.18rem, 3vw, 2rem);
                border-radius: 30px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    radial-gradient(circle at top left, rgba(214, 181, 109, 0.26), transparent 30%),
                    radial-gradient(circle at bottom right, rgba(74, 144, 226, 0.22), transparent 34%),
                    linear-gradient(135deg, rgba(8, 15, 27, 0.99), rgba(5, 9, 18, 0.99));
                box-shadow: 0 18px 58px rgba(0, 0, 0, 0.31);
                margin-bottom: 1rem;
            }

            .pg-eyebrow {
                color: #d6b56d;
                font-size: 0.74rem;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                font-weight: 880;
                margin-bottom: 0.35rem;
            }

            .pg-title {
                color: #f4f7fb;
                font-size: clamp(1.75rem, 5.4vw, 3.1rem);
                font-weight: 950;
                line-height: 1.02;
                letter-spacing: -0.058em;
                margin-bottom: 0.55rem;
            }

            .pg-subtitle {
                color: rgba(244, 247, 251, 0.75);
                font-size: clamp(0.94rem, 2.2vw, 1.06rem);
                line-height: 1.56;
                max-width: 1020px;
            }

            .pg-note {
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
        <div class="pg-hero">
            <div class="pg-eyebrow">Valoris • PostgreSQL/Supabase • v{VERSAO_POSTGRES_SUPABASE_VALORIS}</div>
            <div class="pg-title">Prepare banco externo sem quebrar o MVP.</div>
            <div class="pg-subtitle">
                Esta etapa cria a ponte entre SQLite local e PostgreSQL/Supabase:
                variáveis de ambiente, DDL, plano de migração e estratégia de adapter.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _renderizar_metricas(prontidao: Dict[str, Any]) -> None:
    st.markdown("### Diagnóstico de prontidão")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Score prontidão", f"{prontidao['score_prontidao']}/100")

    with col_2:
        st.metric("SQLite", f"{prontidao['sqlite_score']}/100")

    with col_3:
        st.metric("Repositório", f"{prontidao['repositorio_score']}/100")

    with col_4:
        st.metric("DATABASE_URL", "OK" if prontidao["database_url_configurada"] else "Ausente")

    st.progress(prontidao["score_prontidao"] / 100)

    if prontidao["score_prontidao"] >= 70:
        st.success(f"**{prontidao['decisao']}** — {prontidao['proximo_passo']}")
    elif prontidao["score_prontidao"] >= 45:
        st.warning(f"**{prontidao['decisao']}** — {prontidao['proximo_passo']}")
    else:
        st.info(f"**{prontidao['decisao']}** — {prontidao['proximo_passo']}")


def _renderizar_variaveis(prontidao: Dict[str, Any]) -> None:
    st.markdown("### Variáveis de ambiente")

    for item in prontidao["variaveis"]:
        with st.container(border=True):
            status = "Configurada" if item["configurada"] else "Ausente"
            st.markdown(f"**{item['nome']}** — {status}")
            st.caption(f"Obrigatória: {'Sim' if item['obrigatoria'] else 'Não'}")
            st.markdown(item["descricao"])

            if item["configurada"]:
                st.code(item["visualizacao"], language="text")
            else:
                st.code(item["exemplo"], language="text")


def _renderizar_tabelas_prioritarias() -> None:
    st.markdown("### Tabelas prioritárias")

    for tabela in TABELAS_PRIORITARIAS_MIGRACAO:
        with st.container(border=True):
            st.markdown(f"**{tabela['tabela']}** — {tabela['prioridade']}")
            st.markdown(tabela["motivo"])


def _renderizar_plano_migracao() -> None:
    st.markdown("### Plano de migração")

    for fase in PLANO_MIGRACAO_POSTGRES:
        with st.container(border=True):
            st.markdown(f"**Fase {fase['fase']} — {fase['nome']}**")
            st.caption(fase["objetivo"])
            st.markdown(f"Entrega: {fase['entrega']}")


def _renderizar_ddl_e_adapter() -> None:
    st.markdown("### DDL PostgreSQL/Supabase")

    sql = gerar_sql_postgres()
    st.code(sql, language="sql")

    st.download_button(
        "Baixar DDL PostgreSQL/Supabase (.sql)",
        data=sql,
        file_name="valoris_schema_postgres_supabase.sql",
        mime="text/sql",
        key="download_sql_postgres_supabase",
    )

    st.markdown("### Rascunho do PostgresAdapter")
    st.code(POSTGRES_ADAPTER_RASCUNHO, language="python")


def _renderizar_historico() -> None:
    historico = carregar_decisoes_postgres()

    st.markdown("### Histórico de decisões PostgreSQL/Supabase")

    if not historico:
        st.info("Ainda não há decisões salvas.")
        return

    for item in reversed(historico[-10:]):
        with st.container(border=True):
            st.markdown(f"**{item.get('decisao', 'N/D')}**")
            st.caption(item.get("data_registro", "N/D"))
            st.markdown(
                f"Score: {item.get('score_prontidao', 'N/D')}/100 • SQLite: {item.get('sqlite_score', 'N/D')} • Repo: {item.get('repositorio_score', 'N/D')}"
            )
            st.markdown(f"Próximo passo: {item.get('proximo_passo', 'N/D')}")


def renderizar_postgres_supabase_valoris() -> None:
    _injetar_css_postgres()
    _renderizar_hero()

    prontidao = calcular_prontidao_postgres()
    _renderizar_metricas(prontidao)

    st.divider()

    col_1, col_2, col_3 = st.columns(3)

    with col_1:
        if st.button("Gerar .env.example", key="gerar_env_exemplo_valoris"):
            conteudo = gerar_env_exemplo()
            st.success(f"Arquivo gerado: {CAMINHO_ENV_EXEMPLO}")
            st.code(conteudo, language="text")

    with col_2:
        if st.button("Gerar manifesto PostgreSQL", key="gerar_manifesto_postgres_valoris"):
            manifesto = gerar_manifesto_postgres()
            st.success(f"Manifesto gerado: {CAMINHO_MANIFESTO_POSTGRES}")
            st.json(
                {
                    "versao": manifesto["versao"],
                    "score": manifesto["score_prontidao"],
                    "decisao": manifesto["decisao"],
                }
            )

    with col_3:
        if st.button("Salvar decisão PostgreSQL", key="salvar_decisao_postgres_valoris"):
            registro = salvar_decisao_postgres(
                {
                    "score_prontidao": prontidao["score_prontidao"],
                    "database_url_configurada": prontidao["database_url_configurada"],
                    "supabase_url_configurada": prontidao["supabase_url_configurada"],
                    "sqlite_score": prontidao["sqlite_score"],
                    "repositorio_score": prontidao["repositorio_score"],
                    "decisao": prontidao["decisao"],
                    "proximo_passo": prontidao["proximo_passo"],
                    "observacoes": "Decisão gerada pela preparação PostgreSQL/Supabase.",
                }
            )
            st.success(f"Decisão salva: {registro['decisao']}")
            st.rerun()

    st.download_button(
        "Baixar diagnóstico PostgreSQL/Supabase (.md)",
        data=_gerar_markdown_postgres(prontidao),
        file_name="postgres_supabase_valoris.md",
        mime="text/markdown",
        key="download_postgres_supabase_valoris",
    )

    st.download_button(
        "Baixar decisões PostgreSQL/Supabase (.csv)",
        data=gerar_csv_decisoes_postgres(),
        file_name="decisoes_postgres_supabase_valoris.csv",
        mime="text/csv",
        key="download_decisoes_postgres_supabase_valoris",
    )

    st.divider()
    _renderizar_variaveis(prontidao)

    st.divider()
    _renderizar_tabelas_prioritarias()

    st.divider()
    _renderizar_plano_migracao()

    st.divider()
    _renderizar_ddl_e_adapter()

    st.divider()
    _renderizar_historico()

    st.markdown(
        """
        <div class="pg-note">
            <strong>Regra PostgreSQL/Supabase:</strong> banco externo só entra quando o app já sabe operar
            com contratos, SQLite e repositórios. A troca precisa ser reversível, segura e sem expor credenciais.
        </div>
        """,
        unsafe_allow_html=True,
    )


def executar_autoteste_postgres_supabase_valoris() -> List[Dict[str, str]]:
    prontidao = calcular_prontidao_postgres()
    env_exemplo = gerar_env_exemplo()

    return [
        {
            "teste": "versao_postgres",
            "status": "OK" if VERSAO_POSTGRES_SUPABASE_VALORIS == "3.8.60.1" else "FALHA",
            "detalhe": VERSAO_POSTGRES_SUPABASE_VALORIS,
        },
        {
            "teste": "renderizador",
            "status": "OK" if callable(renderizar_postgres_supabase_valoris) else "FALHA",
            "detalhe": "renderizar_postgres_supabase_valoris",
        },
        {
            "teste": "score_prontidao",
            "status": "OK" if 0 <= prontidao["score_prontidao"] <= 100 else "FALHA",
            "detalhe": str(prontidao["score_prontidao"]),
        },
        {
            "teste": "env_exemplo",
            "status": "OK" if "VALORIS_DATABASE_URL" in env_exemplo else "FALHA",
            "detalhe": "Env exemplo gerado.",
        },
    ]
