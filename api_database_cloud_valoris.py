# api_database_cloud_valoris.py

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

import streamlit as st

from api_security_panel_valoris import calcular_saude_api_security_panel
from api_security_key_valoris import API_KEY_HEADER_NAME, DEFAULT_LOCAL_API_KEY, calcular_saude_api_security
from api_storage_adapter_valoris import calcular_saude_api_adapter
from api_endpoint_tests_valoris import calcular_saude_api_endpoint_tests
from api_smoke_tests_valoris import testar_health_api


VERSAO_API_DATABASE_CLOUD_VALORIS = "3.8.70"

CAMINHO_DECISOES_DATABASE_CLOUD = Path("decisoes_api_database_cloud_valoris.csv")
CAMINHO_MANIFESTO_DATABASE_CLOUD = Path("manifesto_api_database_cloud_valoris.json")
CAMINHO_BLUEPRINT_DATABASE_CLOUD = Path("BLUEPRINT_DATABASE_CLOUD_VALORIS.md")

CAMINHO_ENV_EXAMPLE = Path("api_valoris/.env.example")
CAMINHO_ENV_CLOUD_EXAMPLE = Path("api_valoris/.env.cloud.example")
CAMINHO_API_MAIN = Path("api_valoris/app/main.py")
CAMINHO_REPOSITORY_BRIDGE = Path("api_valoris/app/services/repository_bridge.py")
CAMINHO_STORAGE_CONFIG = Path("api_valoris/app/core/storage_config.py")
CAMINHO_SECURITY_CORE = Path("api_valoris/app/core/security.py")
CAMINHO_DB_LOCAL = Path("valoris_api_local.sqlite3")
CAMINHO_LEADS_CSV = Path("lista_espera_beta.csv")
CAMINHO_EVENTS_CSV = Path("eventos_publicos_valoris.csv")
CAMINHO_GITIGNORE = Path(".gitignore")

CAMPOS_DECISAO_DATABASE_CLOUD = [
    "id",
    "data_registro",
    "score_cloud",
    "score_security_panel",
    "score_security",
    "score_adapter",
    "score_tests",
    "api_online",
    "storage_local_ok",
    "security_ok",
    "env_pronto",
    "schema_pronto",
    "risco",
    "decisao",
    "proximo_passo",
    "observacoes",
]


ENV_VARS_CLOUD = [
    {
        "nome": "VALORIS_DATABASE_PROVIDER",
        "exemplo": "local",
        "obrigatoria_agora": False,
        "obrigatoria_producao": True,
        "descricao": "Define o provedor futuro de banco. Na fase local, manter local. No futuro: supabase ou postgres.",
    },
    {
        "nome": "VALORIS_STORAGE_MODE",
        "exemplo": "hybrid",
        "obrigatoria_agora": True,
        "obrigatoria_producao": True,
        "descricao": "Mantém compatibilidade com csv/sqlite/hybrid. Hoje o recomendado é hybrid.",
    },
    {
        "nome": "VALORIS_API_KEY",
        "exemplo": "trocar-por-chave-forte",
        "obrigatoria_agora": True,
        "obrigatoria_producao": True,
        "descricao": "Chave da API. Em produção, nunca usar a chave local padrão.",
    },
    {
        "nome": "VALORIS_SUPABASE_URL",
        "exemplo": "https://seu-projeto.supabase.co",
        "obrigatoria_agora": False,
        "obrigatoria_producao": False,
        "descricao": "URL do projeto Supabase, apenas quando a integração Supabase for ativada.",
    },
    {
        "nome": "VALORIS_SUPABASE_SERVICE_ROLE_KEY",
        "exemplo": "definir-somente-em-ambiente-seguro",
        "obrigatoria_agora": False,
        "obrigatoria_producao": False,
        "descricao": "Chave sensível de serviço Supabase. Nunca versionar e nunca expor no front-end.",
    },
    {
        "nome": "VALORIS_POSTGRES_DSN",
        "exemplo": "postgresql://usuario:senha@host:5432/banco",
        "obrigatoria_agora": False,
        "obrigatoria_producao": False,
        "descricao": "String de conexão PostgreSQL direta, caso a Valoris não use o SDK Supabase.",
    },
]


SCHEMAS_POSTGRES = [
    {
        "tabela": "leads",
        "objetivo": "Armazenar contatos capturados pela página pública/lista de espera.",
        "campos": [
            {"nome": "id", "tipo": "uuid/text", "regra": "chave primária"},
            {"nome": "data_criacao", "tipo": "timestamp", "regra": "obrigatório"},
            {"nome": "nome", "tipo": "text", "regra": "obrigatório"},
            {"nome": "contato", "tipo": "text", "regra": "obrigatório; índice recomendado"},
            {"nome": "perfil", "tipo": "text", "regra": "opcional"},
            {"nome": "principal_dor", "tipo": "text", "regra": "opcional"},
            {"nome": "plano_interesse", "tipo": "text", "regra": "opcional"},
            {"nome": "preco_aceitavel", "tipo": "text", "regra": "opcional"},
            {"nome": "pagaria_agora", "tipo": "text", "regra": "opcional"},
            {"nome": "comentario", "tipo": "text", "regra": "opcional"},
        ],
    },
    {
        "tabela": "events",
        "objetivo": "Armazenar eventos públicos/técnicos de uso do produto e funil.",
        "campos": [
            {"nome": "id", "tipo": "uuid/text", "regra": "chave primária"},
            {"nome": "data_criacao", "tipo": "timestamp", "regra": "obrigatório"},
            {"nome": "sessao_id", "tipo": "text", "regra": "índice recomendado"},
            {"nome": "evento", "tipo": "text", "regra": "obrigatório; índice recomendado"},
            {"nome": "origem", "tipo": "text", "regra": "opcional"},
            {"nome": "contexto", "tipo": "text", "regra": "opcional"},
            {"nome": "perfil", "tipo": "text", "regra": "opcional"},
            {"nome": "valor", "tipo": "text", "regra": "opcional"},
            {"nome": "detalhe", "tipo": "text", "regra": "opcional"},
        ],
    },
    {
        "tabela": "founder_decisions",
        "objetivo": "Registrar decisões técnicas e de produto do Modo Fundador.",
        "campos": [
            {"nome": "id", "tipo": "uuid/text", "regra": "chave primária"},
            {"nome": "data_registro", "tipo": "timestamp", "regra": "obrigatório"},
            {"nome": "modulo", "tipo": "text", "regra": "obrigatório; índice recomendado"},
            {"nome": "score", "tipo": "integer", "regra": "opcional"},
            {"nome": "decisao", "tipo": "text", "regra": "obrigatório"},
            {"nome": "proximo_passo", "tipo": "text", "regra": "opcional"},
            {"nome": "observacoes", "tipo": "text", "regra": "opcional"},
        ],
    },
]


FASES_MIGRACAO_CLOUD = [
    {
        "fase": "1. Blueprint",
        "status": "Agora",
        "objetivo": "Documentar schemas, variáveis, riscos e caminho de migração sem conectar nada externo.",
        "criterio": "Painel v3.8.70 funcionando e manifesto gerado.",
    },
    {
        "fase": "2. Contratos",
        "status": "Próxima",
        "objetivo": "Criar camada abstrata de banco com contratos para local, supabase e postgres.",
        "criterio": "RepositoryBridge não deve quebrar CSV/SQLite.",
    },
    {
        "fase": "3. Conexão externa controlada",
        "status": "Futura",
        "objetivo": "Permitir conexão experimental com Supabase/PostgreSQL via variáveis de ambiente.",
        "criterio": "Sem secrets no Git e com fallback local.",
    },
    {
        "fase": "4. Migração assistida",
        "status": "Futura",
        "objetivo": "Migrar CSV/SQLite para PostgreSQL com validação, logs e conferência.",
        "criterio": "Contagem de registros local e cloud batendo.",
    },
    {
        "fase": "5. Deploy",
        "status": "Futura",
        "objetivo": "Expor API com segurança real, HTTPS, rate limit e observabilidade.",
        "criterio": "Ambiente dev/prod separado e hardening concluído.",
    },
]


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


def carregar_decisoes_database_cloud() -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_DECISOES_DATABASE_CLOUD, CAMPOS_DECISAO_DATABASE_CLOUD)

    with CAMINHO_DECISOES_DATABASE_CLOUD.open("r", newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def gerar_csv_decisoes_database_cloud() -> str:
    _garantir_csv(CAMINHO_DECISOES_DATABASE_CLOUD, CAMPOS_DECISAO_DATABASE_CLOUD)
    return CAMINHO_DECISOES_DATABASE_CLOUD.read_text(encoding="utf-8")


def salvar_decisao_database_cloud(decisao: Dict[str, Any]) -> Dict[str, str]:
    _garantir_csv(CAMINHO_DECISOES_DATABASE_CLOUD, CAMPOS_DECISAO_DATABASE_CLOUD)

    registro = {
        "id": str(uuid4())[:8],
        "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score_cloud": str(decisao.get("score_cloud", "")),
        "score_security_panel": str(decisao.get("score_security_panel", "")),
        "score_security": str(decisao.get("score_security", "")),
        "score_adapter": str(decisao.get("score_adapter", "")),
        "score_tests": str(decisao.get("score_tests", "")),
        "api_online": str(decisao.get("api_online", "")),
        "storage_local_ok": str(decisao.get("storage_local_ok", "")),
        "security_ok": str(decisao.get("security_ok", "")),
        "env_pronto": str(decisao.get("env_pronto", "")),
        "schema_pronto": str(decisao.get("schema_pronto", "")),
        "risco": _limpar_texto(decisao.get("risco", "")),
        "decisao": _limpar_texto(decisao.get("decisao", "")),
        "proximo_passo": _limpar_texto(decisao.get("proximo_passo", "")),
        "observacoes": _limpar_texto(decisao.get("observacoes", "")),
    }

    with CAMINHO_DECISOES_DATABASE_CLOUD.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISAO_DATABASE_CLOUD)
        escritor.writerow(registro)

    return registro


def _arquivo_contem(caminho: Path, termos: List[str]) -> bool:
    if not caminho.exists():
        return False

    conteudo = caminho.read_text(encoding="utf-8", errors="ignore")
    return all(termo in conteudo for termo in termos)


def _gitignore_contem(termo: str) -> bool:
    if not CAMINHO_GITIGNORE.exists():
        return False

    return termo in CAMINHO_GITIGNORE.read_text(encoding="utf-8", errors="ignore")


def avaliar_variaveis_ambiente_cloud() -> List[Dict[str, Any]]:
    env_text = ""
    if CAMINHO_ENV_EXAMPLE.exists():
        env_text += CAMINHO_ENV_EXAMPLE.read_text(encoding="utf-8", errors="ignore")

    if CAMINHO_ENV_CLOUD_EXAMPLE.exists():
        env_text += "\n" + CAMINHO_ENV_CLOUD_EXAMPLE.read_text(encoding="utf-8", errors="ignore")

    avaliacao = []

    for item in ENV_VARS_CLOUD:
        avaliacao.append(
            {
                "Variável": item["nome"],
                "Exemplo": item["exemplo"],
                "Obrigatória agora": item["obrigatoria_agora"],
                "Obrigatória produção": item["obrigatoria_producao"],
                "Documentada": item["nome"] in env_text,
                "Descrição": item["descricao"],
            }
        )

    return avaliacao


def gerar_env_cloud_example() -> Dict[str, Any]:
    linhas = [
        "# Valoris — exemplo de variáveis para futura camada Supabase/PostgreSQL",
        "# Não coloque secrets reais neste arquivo.",
        "# Este arquivo é blueprint. O uso real deve ser por .env local ou variáveis do ambiente de deploy.",
        "",
    ]

    for item in ENV_VARS_CLOUD:
        linhas.append(f"# {item['descricao']}")
        linhas.append(f"{item['nome']}={item['exemplo']}")
        linhas.append("")

    CAMINHO_ENV_CLOUD_EXAMPLE.parent.mkdir(parents=True, exist_ok=True)
    CAMINHO_ENV_CLOUD_EXAMPLE.write_text("\n".join(linhas).rstrip() + "\n", encoding="utf-8")

    return {
        "ok": True,
        "arquivo": str(CAMINHO_ENV_CLOUD_EXAMPLE),
        "variaveis": [item["nome"] for item in ENV_VARS_CLOUD],
        "mensagem": "Arquivo .env.cloud.example gerado como blueprint. Não use secrets reais nele.",
    }


def calcular_sql_blueprint() -> str:
    return """-- Blueprint PostgreSQL/Supabase — Valoris v3.8.70
-- Revisar antes de executar em qualquer banco real.

create table if not exists leads (
    id text primary key,
    data_criacao timestamp not null,
    nome text not null,
    contato text not null,
    perfil text,
    principal_dor text,
    plano_interesse text,
    preco_aceitavel text,
    pagaria_agora text,
    comentario text
);

create index if not exists idx_leads_contato on leads(contato);
create index if not exists idx_leads_data_criacao on leads(data_criacao);

create table if not exists events (
    id text primary key,
    data_criacao timestamp not null,
    sessao_id text,
    evento text not null,
    origem text,
    contexto text,
    perfil text,
    valor text,
    detalhe text
);

create index if not exists idx_events_evento on events(evento);
create index if not exists idx_events_sessao_id on events(sessao_id);
create index if not exists idx_events_data_criacao on events(data_criacao);

create table if not exists founder_decisions (
    id text primary key,
    data_registro timestamp not null,
    modulo text not null,
    score integer,
    decisao text not null,
    proximo_passo text,
    observacoes text
);

create index if not exists idx_founder_decisions_modulo on founder_decisions(modulo);
create index if not exists idx_founder_decisions_data_registro on founder_decisions(data_registro);
"""


def gerar_blueprint_markdown(saude: Dict[str, Any] | None = None) -> str:
    if saude is None:
        saude = calcular_saude_database_cloud()

    env_linhas = "\n".join(
        [
            f"- `{item['nome']}` — {item['descricao']}"
            for item in ENV_VARS_CLOUD
        ]
    )

    tabelas_linhas = []
    for tabela in SCHEMAS_POSTGRES:
        tabelas_linhas.append(f"### {tabela['tabela']}\n")
        tabelas_linhas.append(f"{tabela['objetivo']}\n")
        for campo in tabela["campos"]:
            tabelas_linhas.append(f"- `{campo['nome']}` ({campo['tipo']}): {campo['regra']}")
        tabelas_linhas.append("")

    fases_linhas = "\n".join(
        [
            f"- **{fase['fase']}** ({fase['status']}): {fase['objetivo']} Critério: {fase['criterio']}"
            for fase in FASES_MIGRACAO_CLOUD
        ]
    )

    return f"""# Blueprint Database Cloud — Valoris

Versão: {VERSAO_API_DATABASE_CLOUD_VALORIS}  
Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Diagnóstico

Score Cloud: {saude["score_cloud"]}/100  
Risco: {saude["risco"]}  
Decisão: {saude["decisao"]}  
Próximo passo: {saude["proximo_passo"]}

## Princípio de arquitetura

A Valoris não deve abandonar CSV/SQLite agora. O caminho correto é manter `hybrid` como ambiente local confiável e preparar Supabase/PostgreSQL como camada externa futura, sempre com fallback local e sem secrets versionados.

## Variáveis de ambiente planejadas

{env_linhas}

## Tabelas planejadas

{chr(10).join(tabelas_linhas)}

## Fases de migração

{fases_linhas}

## SQL blueprint

```sql
{calcular_sql_blueprint()}
```

## Regras de segurança

- Nunca versionar `.env` real.
- Nunca colocar service role key no front-end.
- Trocar a API Key local antes de qualquer deploy público.
- Manter HTTPS e rate limit antes de produção.
- Migrar dados com conferência de contagem e amostragem.
"""


def salvar_blueprint_markdown() -> Dict[str, Any]:
    saude = calcular_saude_database_cloud()
    conteudo = gerar_blueprint_markdown(saude)
    CAMINHO_BLUEPRINT_DATABASE_CLOUD.write_text(conteudo, encoding="utf-8")

    return {
        "ok": True,
        "arquivo": str(CAMINHO_BLUEPRINT_DATABASE_CLOUD),
        "score_cloud": saude["score_cloud"],
        "decisao": saude["decisao"],
    }


def calcular_saude_database_cloud() -> Dict[str, Any]:
    try:
        security_panel = calcular_saude_api_security_panel()
    except Exception as erro:
        security_panel = {"score_panel": 0, "protected_ok": False, "erro": str(erro)}

    try:
        security = calcular_saude_api_security()
    except Exception as erro:
        security = {"score_security": 0, "protected_ok": False, "erro": str(erro)}

    try:
        adapter = calcular_saude_api_adapter()
    except Exception as erro:
        adapter = {"score_adapter": 0, "erro": str(erro)}

    try:
        endpoint_tests = calcular_saude_api_endpoint_tests()
    except Exception as erro:
        endpoint_tests = {"score_tests": 0, "erro": str(erro)}

    health = testar_health_api()

    env_avaliacao = avaliar_variaveis_ambiente_cloud()
    env_documentadas = len([item for item in env_avaliacao if item["Documentada"]])
    env_total = len(env_avaliacao)
    env_obrigatorias_agora = [item for item in env_avaliacao if item["Obrigatória agora"]]
    env_obrigatorias_ok = all(item["Documentada"] for item in env_obrigatorias_agora) if env_obrigatorias_agora else True

    storage_local_ok = CAMINHO_DB_LOCAL.exists() and CAMINHO_LEADS_CSV.exists() and CAMINHO_EVENTS_CSV.exists()

    arquivos_base = [
        {"arquivo": str(CAMINHO_API_MAIN), "existe": CAMINHO_API_MAIN.exists()},
        {"arquivo": str(CAMINHO_REPOSITORY_BRIDGE), "existe": CAMINHO_REPOSITORY_BRIDGE.exists()},
        {"arquivo": str(CAMINHO_STORAGE_CONFIG), "existe": CAMINHO_STORAGE_CONFIG.exists()},
        {"arquivo": str(CAMINHO_SECURITY_CORE), "existe": CAMINHO_SECURITY_CORE.exists()},
    ]

    arquivos_base_ok = len([item for item in arquivos_base if item["existe"]])

    schemas_prontos = len(SCHEMAS_POSTGRES) >= 3 and all(len(tabela["campos"]) >= 3 for tabela in SCHEMAS_POSTGRES)

    gitignore_ok = (
        _gitignore_contem("valoris_api_local.sqlite3")
        and _gitignore_contem("lista_espera_beta.csv")
        and _gitignore_contem("eventos_publicos_valoris.csv")
    )

    score_security_panel = int(security_panel.get("score_panel", 0) or 0)
    score_security = int(security.get("score_security", 0) or 0)
    score_adapter = int(adapter.get("score_adapter", 0) or 0)
    score_tests = int(endpoint_tests.get("score_tests", 0) or 0)

    score = 10
    score += min(score_security_panel * 0.20, 20)
    score += min(score_security * 0.15, 15)
    score += min(score_adapter * 0.12, 12)
    score += min(score_tests * 0.10, 10)
    score += 8 if health.get("health_ok") else 0
    score += 8 if storage_local_ok else 0
    score += 8 if schemas_prontos else 0
    score += min((env_documentadas / max(env_total, 1)) * 10, 10)
    score += 5 if gitignore_ok else 0
    score += min((arquivos_base_ok / max(len(arquivos_base), 1)) * 4, 4)
    score = int(round(max(0, min(100, score))))

    security_ok = bool(security.get("protected_ok")) or bool(security_panel.get("protected_ok"))

    if not security_ok:
        risco = "Alto"
        decisao = "Não avançar para cloud ainda"
        proximo_passo = "Validar API Key e endpoints protegidos antes de qualquer conexão externa."
    elif not storage_local_ok:
        risco = "Médio/alto"
        decisao = "Corrigir base local antes da cloud"
        proximo_passo = "Garantir SQLite/CSV funcionando como fallback."
    elif not env_obrigatorias_ok:
        risco = "Médio"
        decisao = "Documentar variáveis obrigatórias"
        proximo_passo = "Gerar .env.cloud.example e revisar .env.example."
    elif score >= 82:
        risco = "Médio controlado"
        decisao = "Blueprint cloud aprovado"
        proximo_passo = "Avançar para contratos de repositório local/supabase/postgres."
    else:
        risco = "Médio"
        decisao = "Preparação cloud em progresso"
        proximo_passo = "Gerar blueprint, manifesto e revisar checklist."

    return {
        "score_cloud": score,
        "score_security_panel": score_security_panel,
        "score_security": score_security,
        "score_adapter": score_adapter,
        "score_tests": score_tests,
        "api_online": bool(health.get("health_ok")),
        "storage_local_ok": storage_local_ok,
        "security_ok": security_ok,
        "env_pronto": env_obrigatorias_ok,
        "schema_pronto": schemas_prontos,
        "gitignore_ok": gitignore_ok,
        "env_documentadas": env_documentadas,
        "env_total": env_total,
        "env_avaliacao": env_avaliacao,
        "arquivos_base": arquivos_base,
        "arquivos_base_ok": arquivos_base_ok,
        "schemas": SCHEMAS_POSTGRES,
        "fases": FASES_MIGRACAO_CLOUD,
        "health": health,
        "security_panel": security_panel,
        "security": security,
        "adapter": adapter,
        "endpoint_tests": endpoint_tests,
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo_passo,
    }


def gerar_manifesto_database_cloud() -> Dict[str, Any]:
    saude = calcular_saude_database_cloud()

    manifesto = {
        "versao": VERSAO_API_DATABASE_CLOUD_VALORIS,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "saude": saude,
        "env_vars": ENV_VARS_CLOUD,
        "schemas": SCHEMAS_POSTGRES,
        "fases_migracao": FASES_MIGRACAO_CLOUD,
        "sql_blueprint": calcular_sql_blueprint(),
        "estrategia": {
            "agora": "Preparar blueprint e manter local/hybrid.",
            "proxima_versao": "Criar contratos abstratos para provedores local, supabase e postgres.",
            "regra": "Nada externo deve quebrar CSV/SQLite local.",
        },
    }

    CAMINHO_MANIFESTO_DATABASE_CLOUD.write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return manifesto


def _injetar_css_database_cloud() -> None:
    st.markdown(
        """
        <style>
            .database-cloud-hero {
                padding: clamp(1.2rem, 3vw, 2.05rem);
                border-radius: 30px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    radial-gradient(circle at top left, rgba(214, 181, 109, 0.22), transparent 32%),
                    radial-gradient(circle at bottom right, rgba(60, 118, 180, 0.22), transparent 36%),
                    linear-gradient(135deg, rgba(6, 12, 23, 0.99), rgba(4, 8, 16, 0.99));
                box-shadow: 0 20px 62px rgba(0, 0, 0, 0.34);
                margin-bottom: 1rem;
            }

            .database-cloud-eyebrow {
                color: #d6b56d;
                font-size: 0.74rem;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                font-weight: 880;
                margin-bottom: 0.35rem;
            }

            .database-cloud-title {
                color: #f4f7fb;
                font-size: clamp(1.8rem, 5.5vw, 3.2rem);
                font-weight: 950;
                line-height: 1.02;
                letter-spacing: -0.058em;
                margin-bottom: 0.55rem;
            }

            .database-cloud-subtitle {
                color: rgba(244, 247, 251, 0.75);
                font-size: clamp(0.94rem, 2.2vw, 1.06rem);
                line-height: 1.56;
                max-width: 1050px;
            }

            .database-cloud-note {
                padding: 0.95rem 1rem;
                border-radius: 18px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.90rem;
                line-height: 1.55;
                margin: 0.9rem 0;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def renderizar_api_database_cloud_valoris() -> None:
    _injetar_css_database_cloud()

    st.markdown(
        f"""
        <div class="database-cloud-hero">
            <div class="database-cloud-eyebrow">Valoris • Database Cloud • v{VERSAO_API_DATABASE_CLOUD_VALORIS}</div>
            <div class="database-cloud-title">Preparação Supabase/PostgreSQL.</div>
            <div class="database-cloud-subtitle">
                Esta etapa não conecta a Valoris a serviços externos. Ela cria o blueprint técnico:
                variáveis, schemas, fases, riscos e regras para migrar sem quebrar CSV/SQLite.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    saude = calcular_saude_database_cloud()

    st.markdown("### Diagnóstico Cloud")
    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Score Cloud", f"{saude['score_cloud']}/100")

    with col_2:
        st.metric("Risco", saude["risco"])

    with col_3:
        st.metric("Local fallback", "OK" if saude["storage_local_ok"] else "Pendente")

    with col_4:
        st.metric("Security", "OK" if saude["security_ok"] else "Pendente")

    st.progress(saude["score_cloud"] / 100)

    if saude["score_cloud"] >= 82 and saude["security_ok"]:
        st.success(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    elif saude["score_cloud"] >= 60:
        st.warning(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    else:
        st.info(f"**{saude['decisao']}** — {saude['proximo_passo']}")

    st.markdown(
        """
        <div class="database-cloud-note">
            <strong>Decisão arquitetural:</strong> não vamos conectar Supabase/PostgreSQL direto agora.
            Primeiro documentamos o contrato, mantemos fallback local e só depois criamos a camada externa controlada.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    st.markdown("### Scores herdados")
    col_a, col_b, col_c, col_d = st.columns(4)

    with col_a:
        st.metric("Security Panel", f"{saude['score_security_panel']}/100")

    with col_b:
        st.metric("Security", f"{saude['score_security']}/100")

    with col_c:
        st.metric("Adapter", f"{saude['score_adapter']}/100")

    with col_d:
        st.metric("Endpoint Tests", f"{saude['score_tests']}/100")

    st.divider()

    st.markdown("### Variáveis de ambiente planejadas")
    st.dataframe(saude["env_avaliacao"], use_container_width=True, hide_index=True)

    st.markdown("### Fases de migração")
    st.dataframe(FASES_MIGRACAO_CLOUD, use_container_width=True, hide_index=True)

    st.markdown("### Tabelas planejadas")
    for tabela in SCHEMAS_POSTGRES:
        with st.expander(f"Tabela: {tabela['tabela']}"):
            st.caption(tabela["objetivo"])
            st.dataframe(tabela["campos"], use_container_width=True, hide_index=True)

    st.divider()

    col_btn_1, col_btn_2, col_btn_3, col_btn_4 = st.columns(4)

    with col_btn_1:
        if st.button("Gerar .env.cloud.example", key="db_cloud_env_example"):
            resultado = gerar_env_cloud_example()
            st.success(resultado["mensagem"])
            st.caption(f"Arquivo gerado: {resultado['arquivo']}")

    with col_btn_2:
        if st.button("Gerar manifesto Cloud", key="db_cloud_manifesto"):
            manifesto = gerar_manifesto_database_cloud()
            st.success(f"Manifesto gerado: {CAMINHO_MANIFESTO_DATABASE_CLOUD}")
            st.json(
                {
                    "versao": manifesto["versao"],
                    "score_cloud": manifesto["saude"]["score_cloud"],
                    "decisao": manifesto["saude"]["decisao"],
                }
            )

    with col_btn_3:
        if st.button("Salvar blueprint .md", key="db_cloud_blueprint"):
            resultado = salvar_blueprint_markdown()
            st.success(f"Blueprint salvo: {resultado['arquivo']}")
            st.json(resultado)

    with col_btn_4:
        if st.button("Salvar decisão Cloud", key="db_cloud_decisao"):
            registro = salvar_decisao_database_cloud(
                {
                    "score_cloud": saude["score_cloud"],
                    "score_security_panel": saude["score_security_panel"],
                    "score_security": saude["score_security"],
                    "score_adapter": saude["score_adapter"],
                    "score_tests": saude["score_tests"],
                    "api_online": saude["api_online"],
                    "storage_local_ok": saude["storage_local_ok"],
                    "security_ok": saude["security_ok"],
                    "env_pronto": saude["env_pronto"],
                    "schema_pronto": saude["schema_pronto"],
                    "risco": saude["risco"],
                    "decisao": saude["decisao"],
                    "proximo_passo": saude["proximo_passo"],
                    "observacoes": "Decisão gerada pelo blueprint Supabase/PostgreSQL.",
                }
            )
            st.success(f"Decisão salva: {registro['decisao']}")
            st.rerun()

    st.download_button(
        "Baixar blueprint Cloud (.md)",
        data=gerar_blueprint_markdown(saude),
        file_name="BLUEPRINT_DATABASE_CLOUD_VALORIS.md",
        mime="text/markdown",
        key="download_blueprint_database_cloud",
    )

    st.download_button(
        "Baixar SQL blueprint (.sql)",
        data=calcular_sql_blueprint(),
        file_name="valoris_database_cloud_blueprint.sql",
        mime="text/sql",
        key="download_sql_database_cloud",
    )

    st.download_button(
        "Baixar decisões Cloud (.csv)",
        data=gerar_csv_decisoes_database_cloud(),
        file_name="decisoes_api_database_cloud_valoris.csv",
        mime="text/csv",
        key="download_decisoes_database_cloud",
    )

    st.divider()

    st.markdown("### SQL blueprint")
    st.code(calcular_sql_blueprint(), language="sql")

    st.markdown("### Arquivos base")
    st.dataframe(saude["arquivos_base"], use_container_width=True, hide_index=True)

    with st.expander("Ver diagnóstico bruto"):
        st.json(saude)


def executar_autoteste_api_database_cloud_valoris() -> List[Dict[str, str]]:
    saude = calcular_saude_database_cloud()

    return [
        {
            "teste": "versao_database_cloud",
            "status": "OK" if VERSAO_API_DATABASE_CLOUD_VALORIS == "3.8.70" else "FALHA",
            "detalhe": VERSAO_API_DATABASE_CLOUD_VALORIS,
        },
        {
            "teste": "score_cloud",
            "status": "OK" if 0 <= saude["score_cloud"] <= 100 else "FALHA",
            "detalhe": str(saude["score_cloud"]),
        },
        {
            "teste": "schemas",
            "status": "OK" if len(SCHEMAS_POSTGRES) >= 3 else "FALHA",
            "detalhe": str(len(SCHEMAS_POSTGRES)),
        },
        {
            "teste": "renderizador",
            "status": "OK" if callable(renderizar_api_database_cloud_valoris) else "FALHA",
            "detalhe": "renderizar_api_database_cloud_valoris",
        },
    ]
