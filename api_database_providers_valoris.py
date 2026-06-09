# api_database_providers_valoris.py

from __future__ import annotations

import csv
import json
import py_compile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

import streamlit as st

from api_database_contracts_valoris import (
    METODOS_REPOSITORY_CONTRACT,
    PROVEDORES_DATABASE,
    REGRAS_MIGRACAO_DATABASE,
    calcular_saude_database_contracts,
)
from api_database_cloud_valoris import calcular_saude_database_cloud
from api_security_key_valoris import calcular_saude_api_security
from api_storage_adapter_valoris import calcular_saude_api_adapter
from api_endpoint_tests_valoris import calcular_saude_api_endpoint_tests
from api_smoke_tests_valoris import testar_health_api


VERSAO_API_DATABASE_PROVIDERS_VALORIS = "3.8.72"

CAMINHO_DECISOES_DATABASE_PROVIDERS = Path("decisoes_api_database_providers_valoris.csv")
CAMINHO_MANIFESTO_DATABASE_PROVIDERS = Path("manifesto_api_database_providers_valoris.json")
CAMINHO_PROVIDERS_SCAFFOLD = Path("api_valoris/app/services/database_providers.py")
CAMINHO_PROVIDER_FACTORY_SCAFFOLD = Path("api_valoris/app/services/provider_factory.py")
CAMINHO_PROVIDER_BLUEPRINT_MD = Path("PROVIDERS_DATABASE_VALORIS.md")

CAMINHO_REPOSITORY_BRIDGE = Path("api_valoris/app/services/repository_bridge.py")
CAMINHO_STORAGE_CONFIG = Path("api_valoris/app/core/storage_config.py")
CAMINHO_DB_LOCAL = Path("valoris_api_local.sqlite3")
CAMINHO_LEADS_CSV = Path("lista_espera_beta.csv")
CAMINHO_EVENTS_CSV = Path("eventos_publicos_valoris.csv")
CAMINHO_GITIGNORE = Path(".gitignore")

CAMPOS_DECISAO_DATABASE_PROVIDERS = [
    "id", "data_registro", "score_providers", "score_contracts", "score_cloud",
    "score_security", "score_adapter", "score_tests", "api_online",
    "fallback_local_ok", "scaffold_pronto", "factory_pronto",
    "providers_planejados", "risco", "decisao", "proximo_passo", "observacoes",
]

PROVIDER_FACTORY_RULES = [
    {"regra": "ProviderFactory nunca deve exigir secrets no import", "motivo": "O app deve abrir mesmo sem Supabase/Postgres configurado.", "prioridade": "Obrigatória"},
    {"regra": "Provider local deve ser o padrão", "motivo": "O beta local precisa sobreviver sem rede.", "prioridade": "Obrigatória"},
    {"regra": "SupabaseProvider e PostgresProvider começam como placeholder", "motivo": "A primeira etapa é arquitetura, não conexão real.", "prioridade": "Obrigatória"},
    {"regra": "HybridProvider continua recomendado", "motivo": "CSV + SQLite oferecem rastreabilidade e redundância local.", "prioridade": "Alta"},
    {"regra": "Provider cloud precisa retornar erro controlado", "motivo": "Sem variável de ambiente, deve falhar claro, não quebrar o app.", "prioridade": "Alta"},
]

PROVIDER_SCENARIOS = [
    {"cenario": "Beta local", "provider": "hybrid", "descricao": "Grava CSV + SQLite.", "risco": "Baixo"},
    {"cenario": "Debug rápido", "provider": "local_csv", "descricao": "Permite auditoria manual simples.", "risco": "Médio"},
    {"cenario": "Uso local robusto", "provider": "local_sqlite", "descricao": "Usa SQLite como fonte local principal.", "risco": "Baixo/médio"},
    {"cenario": "Cloud experimental", "provider": "supabase", "descricao": "Provider futuro com secrets e RLS.", "risco": "Alto se prematuro"},
    {"cenario": "Cloud avançado", "provider": "postgres", "descricao": "Provider futuro com DSN seguro.", "risco": "Alto se prematuro"},
]

DATABASE_PROVIDERS_PY = '"""Camada abstrata de providers de banco — Valoris.\n\nScaffold v3.8.72. Não conecta em Supabase/PostgreSQL ainda.\n"""\n\nfrom __future__ import annotations\n\nfrom typing import Any, Dict, Protocol\n\n\nclass DatabaseProvider(Protocol):\n    name: str\n\n    def create_lead(self, payload: Any) -> Dict[str, Any]:\n        ...\n\n    def list_leads(self, limit: int = 100, source: str = "auto") -> Dict[str, Any]:\n        ...\n\n    def create_event(self, payload: Any) -> Dict[str, Any]:\n        ...\n\n    def storage_health(self) -> Dict[str, Any]:\n        ...\n\n\nclass ProviderUnavailableError(RuntimeError):\n    pass\n\n\nclass LocalCSVProvider:\n    name = "local_csv"\n\n    def __init__(self, repository_bridge: Any):\n        self.repository_bridge = repository_bridge\n\n    def create_lead(self, payload: Any) -> Dict[str, Any]:\n        return self.repository_bridge.create_lead(payload)\n\n    def list_leads(self, limit: int = 100, source: str = "csv") -> Dict[str, Any]:\n        return self.repository_bridge.list_leads(limit=limit, source="csv")\n\n    def create_event(self, payload: Any) -> Dict[str, Any]:\n        return self.repository_bridge.create_event(payload)\n\n    def storage_health(self) -> Dict[str, Any]:\n        health = self.repository_bridge.storage_health()\n        health["active_provider"] = self.name\n        return health\n\n\nclass LocalSQLiteProvider:\n    name = "local_sqlite"\n\n    def __init__(self, repository_bridge: Any):\n        self.repository_bridge = repository_bridge\n\n    def create_lead(self, payload: Any) -> Dict[str, Any]:\n        return self.repository_bridge.create_lead(payload)\n\n    def list_leads(self, limit: int = 100, source: str = "sqlite") -> Dict[str, Any]:\n        return self.repository_bridge.list_leads(limit=limit, source="sqlite")\n\n    def create_event(self, payload: Any) -> Dict[str, Any]:\n        return self.repository_bridge.create_event(payload)\n\n    def storage_health(self) -> Dict[str, Any]:\n        health = self.repository_bridge.storage_health()\n        health["active_provider"] = self.name\n        return health\n\n\nclass HybridProvider:\n    name = "hybrid"\n\n    def __init__(self, repository_bridge: Any):\n        self.repository_bridge = repository_bridge\n\n    def create_lead(self, payload: Any) -> Dict[str, Any]:\n        return self.repository_bridge.create_lead(payload)\n\n    def list_leads(self, limit: int = 100, source: str = "auto") -> Dict[str, Any]:\n        return self.repository_bridge.list_leads(limit=limit, source=source)\n\n    def create_event(self, payload: Any) -> Dict[str, Any]:\n        return self.repository_bridge.create_event(payload)\n\n    def storage_health(self) -> Dict[str, Any]:\n        health = self.repository_bridge.storage_health()\n        health["active_provider"] = self.name\n        return health\n\n\nclass SupabaseProvider:\n    name = "supabase"\n\n    def _unavailable(self) -> Dict[str, Any]:\n        raise ProviderUnavailableError("SupabaseProvider é placeholder seguro. Nenhuma conexão externa foi aberta.")\n\n    def create_lead(self, payload: Any) -> Dict[str, Any]:\n        return self._unavailable()\n\n    def list_leads(self, limit: int = 100, source: str = "auto") -> Dict[str, Any]:\n        return self._unavailable()\n\n    def create_event(self, payload: Any) -> Dict[str, Any]:\n        return self._unavailable()\n\n    def storage_health(self) -> Dict[str, Any]:\n        return {"ok": False, "active_provider": self.name, "configured": False}\n\n\nclass PostgresProvider:\n    name = "postgres"\n\n    def _unavailable(self) -> Dict[str, Any]:\n        raise ProviderUnavailableError("PostgresProvider é placeholder seguro. Nenhuma conexão externa foi aberta.")\n\n    def create_lead(self, payload: Any) -> Dict[str, Any]:\n        return self._unavailable()\n\n    def list_leads(self, limit: int = 100, source: str = "auto") -> Dict[str, Any]:\n        return self._unavailable()\n\n    def create_event(self, payload: Any) -> Dict[str, Any]:\n        return self._unavailable()\n\n    def storage_health(self) -> Dict[str, Any]:\n        return {"ok": False, "active_provider": self.name, "configured": False}\n'
PROVIDER_FACTORY_PY = '"""Factory de providers de banco — Valoris.\n\nScaffold v3.8.72. Mantém hybrid como padrão seguro.\n"""\n\nfrom __future__ import annotations\n\nimport os\nfrom typing import Any\n\nfrom app.services.database_providers import (\n    HybridProvider,\n    LocalCSVProvider,\n    LocalSQLiteProvider,\n    PostgresProvider,\n    SupabaseProvider,\n)\n\n\nSUPPORTED_DATABASE_PROVIDERS = {"local_csv", "local_sqlite", "hybrid", "supabase", "postgres"}\n\n\ndef get_database_provider_name() -> str:\n    provider = os.getenv("VALORIS_DATABASE_PROVIDER", "hybrid").strip().lower()\n    if provider not in SUPPORTED_DATABASE_PROVIDERS:\n        return "hybrid"\n    return provider\n\n\ndef build_database_provider(repository_bridge: Any):\n    provider = get_database_provider_name()\n\n    if provider == "local_csv":\n        return LocalCSVProvider(repository_bridge)\n    if provider == "local_sqlite":\n        return LocalSQLiteProvider(repository_bridge)\n    if provider == "supabase":\n        return SupabaseProvider()\n    if provider == "postgres":\n        return PostgresProvider()\n\n    return HybridProvider(repository_bridge)\n'


def _limpar_texto(valor: Any) -> str:
    return "" if valor is None else str(valor).strip()


def _garantir_csv(caminho: Path, campos: List[str]) -> None:
    if caminho.exists():
        return
    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()


def carregar_decisoes_database_providers() -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_DECISOES_DATABASE_PROVIDERS, CAMPOS_DECISAO_DATABASE_PROVIDERS)
    with CAMINHO_DECISOES_DATABASE_PROVIDERS.open("r", newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def gerar_csv_decisoes_database_providers() -> str:
    _garantir_csv(CAMINHO_DECISOES_DATABASE_PROVIDERS, CAMPOS_DECISAO_DATABASE_PROVIDERS)
    return CAMINHO_DECISOES_DATABASE_PROVIDERS.read_text(encoding="utf-8")


def salvar_decisao_database_providers(decisao: Dict[str, Any]) -> Dict[str, str]:
    _garantir_csv(CAMINHO_DECISOES_DATABASE_PROVIDERS, CAMPOS_DECISAO_DATABASE_PROVIDERS)
    registro = {
        "id": str(uuid4())[:8],
        "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score_providers": str(decisao.get("score_providers", "")),
        "score_contracts": str(decisao.get("score_contracts", "")),
        "score_cloud": str(decisao.get("score_cloud", "")),
        "score_security": str(decisao.get("score_security", "")),
        "score_adapter": str(decisao.get("score_adapter", "")),
        "score_tests": str(decisao.get("score_tests", "")),
        "api_online": str(decisao.get("api_online", "")),
        "fallback_local_ok": str(decisao.get("fallback_local_ok", "")),
        "scaffold_pronto": str(decisao.get("scaffold_pronto", "")),
        "factory_pronto": str(decisao.get("factory_pronto", "")),
        "providers_planejados": str(decisao.get("providers_planejados", "")),
        "risco": _limpar_texto(decisao.get("risco", "")),
        "decisao": _limpar_texto(decisao.get("decisao", "")),
        "proximo_passo": _limpar_texto(decisao.get("proximo_passo", "")),
        "observacoes": _limpar_texto(decisao.get("observacoes", "")),
    }
    with CAMINHO_DECISOES_DATABASE_PROVIDERS.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISAO_DATABASE_PROVIDERS)
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


def gerar_database_providers_scaffold() -> Dict[str, Any]:
    CAMINHO_PROVIDERS_SCAFFOLD.parent.mkdir(parents=True, exist_ok=True)
    CAMINHO_PROVIDERS_SCAFFOLD.write_text(DATABASE_PROVIDERS_PY, encoding="utf-8")
    CAMINHO_PROVIDER_FACTORY_SCAFFOLD.write_text(PROVIDER_FACTORY_PY, encoding="utf-8")

    resultados = []
    for caminho in [CAMINHO_PROVIDERS_SCAFFOLD, CAMINHO_PROVIDER_FACTORY_SCAFFOLD]:
        try:
            py_compile.compile(str(caminho), doraise=True)
            resultados.append({"arquivo": str(caminho), "ok": True, "erro": ""})
        except Exception as erro:
            resultados.append({"arquivo": str(caminho), "ok": False, "erro": str(erro)})

    return {
        "ok": all(item["ok"] for item in resultados),
        "arquivos": resultados,
        "mensagem": "Scaffold de providers gerado. Ainda não há conexão externa real.",
    }


def avaliar_scaffold_providers() -> Dict[str, Any]:
    providers_ok = _arquivo_contem(
        CAMINHO_PROVIDERS_SCAFFOLD,
        ["class DatabaseProvider", "class LocalCSVProvider", "class LocalSQLiteProvider", "class HybridProvider", "class SupabaseProvider", "class PostgresProvider"],
    )
    factory_ok = _arquivo_contem(
        CAMINHO_PROVIDER_FACTORY_SCAFFOLD,
        ["build_database_provider", "get_database_provider_name", "SUPPORTED_DATABASE_PROVIDERS"],
    )
    return {
        "providers_file": str(CAMINHO_PROVIDERS_SCAFFOLD),
        "factory_file": str(CAMINHO_PROVIDER_FACTORY_SCAFFOLD),
        "providers_existe": CAMINHO_PROVIDERS_SCAFFOLD.exists(),
        "factory_existe": CAMINHO_PROVIDER_FACTORY_SCAFFOLD.exists(),
        "providers_ok": providers_ok,
        "factory_ok": factory_ok,
        "ok": providers_ok and factory_ok,
    }


def gerar_markdown_providers_database(saude: Dict[str, Any] | None = None) -> str:
    if saude is None:
        saude = calcular_saude_database_providers()

    providers = "\n".join([
        f"- **{item.get('provider', '')}** ({item.get('status', '')}): "
        f"{item.get('uso', '')} | riscos: {item.get('riscos', item.get('risco', 'n?o informado'))}"
        for item in PROVEDORES_DATABASE
    ])
    regras = "\n".join([f"- **{item['prioridade']}** — {item['regra']}: {item['motivo']}" for item in PROVIDER_FACTORY_RULES])
    cenarios = "\n".join([f"- **{item['cenario']}** → `{item['provider']}`: {item['descricao']} Risco: {item['risco']}" for item in PROVIDER_SCENARIOS])

    return f"""# Providers Database — Valoris

Versão: {VERSAO_API_DATABASE_PROVIDERS_VALORIS}  
Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Diagnóstico

Score Providers: {saude["score_providers"]}/100  
Risco: {saude["risco"]}  
Decisão: {saude["decisao"]}  
Próximo passo: {saude["proximo_passo"]}

## Objetivo

Criar uma camada abstrata para providers de banco sem conectar ainda em Supabase/PostgreSQL. A Valoris deve continuar funcionando em CSV/SQLite/hybrid mesmo depois da chegada da cloud.

## Providers

{providers}

## Regras da factory

{regras}

## Cenários

{cenarios}

## Arquivos scaffold

- `{CAMINHO_PROVIDERS_SCAFFOLD}`
- `{CAMINHO_PROVIDER_FACTORY_SCAFFOLD}`
"""


def salvar_providers_database_markdown() -> Dict[str, Any]:
    saude = calcular_saude_database_providers()
    CAMINHO_PROVIDER_BLUEPRINT_MD.write_text(gerar_markdown_providers_database(saude), encoding="utf-8")
    return {
        "ok": True,
        "arquivo": str(CAMINHO_PROVIDER_BLUEPRINT_MD),
        "score_providers": saude["score_providers"],
        "decisao": saude["decisao"],
    }


def calcular_saude_database_providers() -> Dict[str, Any]:
    try:
        contracts = calcular_saude_database_contracts()
    except Exception as erro:
        contracts = {"score_contracts": 0, "contratos_prontos": False, "fallback_local_ok": False, "erro": str(erro)}

    try:
        cloud = calcular_saude_database_cloud()
    except Exception as erro:
        cloud = {"score_cloud": 0, "security_ok": False, "erro": str(erro)}

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
    scaffold = avaliar_scaffold_providers()

    fallback_local_ok = CAMINHO_DB_LOCAL.exists() and CAMINHO_LEADS_CSV.exists() and CAMINHO_EVENTS_CSV.exists()
    repository_bridge_ok = _arquivo_contem(CAMINHO_REPOSITORY_BRIDGE, ["class RepositoryBridge", "storage_health"])
    storage_config_ok = _arquivo_contem(CAMINHO_STORAGE_CONFIG, ["csv", "sqlite", "hybrid"])
    gitignore_ok = _gitignore_contem("api_valoris/app/services/database_providers.py") and _gitignore_contem("api_valoris/app/services/provider_factory.py")

    score_contracts = int(contracts.get("score_contracts", 0) or 0)
    score_cloud = int(cloud.get("score_cloud", 0) or 0)
    score_security = int(security.get("score_security", 0) or 0)
    score_adapter = int(adapter.get("score_adapter", 0) or 0)
    score_tests = int(endpoint_tests.get("score_tests", 0) or 0)

    score = 10
    score += min(score_contracts * 0.18, 18)
    score += min(score_cloud * 0.12, 12)
    score += min(score_security * 0.10, 10)
    score += min(score_adapter * 0.10, 10)
    score += min(score_tests * 0.08, 8)
    score += 8 if health.get("health_ok") else 0
    score += 8 if fallback_local_ok else 0
    score += 8 if repository_bridge_ok else 0
    score += 6 if storage_config_ok else 0
    score += 8 if scaffold["ok"] else 0
    score += 4 if gitignore_ok else 0
    score += 4 if len(PROVIDER_FACTORY_RULES) >= 5 and len(PROVIDER_SCENARIOS) >= 5 else 0
    score = int(round(max(0, min(100, score))))

    security_ok = bool(security.get("protected_ok")) or bool(cloud.get("security_ok"))

    if not security_ok:
        risco = "Alto"
        decisao = "Não avançar providers cloud ainda"
        proximo_passo = "Validar proteção da API antes de qualquer provider externo."
    elif not fallback_local_ok:
        risco = "Médio/alto"
        decisao = "Fallback local incompleto"
        proximo_passo = "Garantir CSV/SQLite antes de criar camada provider."
    elif not scaffold["ok"]:
        risco = "Médio"
        decisao = "Scaffold de providers pendente"
        proximo_passo = "Gerar database_providers.py e provider_factory.py."
    elif score >= 84:
        risco = "Médio controlado"
        decisao = "Camada abstrata de providers aprovada"
        proximo_passo = "Avançar para provider selecionável no backend, mantendo Supabase/Postgres como placeholder."
    else:
        risco = "Médio"
        decisao = "Providers em progresso"
        proximo_passo = "Gerar manifesto, blueprint e revisar factory."

    return {
        "score_providers": score,
        "score_contracts": score_contracts,
        "score_cloud": score_cloud,
        "score_security": score_security,
        "score_adapter": score_adapter,
        "score_tests": score_tests,
        "api_online": bool(health.get("health_ok")),
        "fallback_local_ok": fallback_local_ok,
        "security_ok": security_ok,
        "scaffold_pronto": scaffold["ok"],
        "factory_pronto": scaffold["factory_ok"],
        "providers_planejados": len(PROVEDORES_DATABASE),
        "repository_bridge_ok": repository_bridge_ok,
        "storage_config_ok": storage_config_ok,
        "gitignore_ok": gitignore_ok,
        "health": health,
        "contracts": contracts,
        "cloud": cloud,
        "security": security,
        "adapter": adapter,
        "endpoint_tests": endpoint_tests,
        "scaffold": scaffold,
        "providers": PROVEDORES_DATABASE,
        "factory_rules": PROVIDER_FACTORY_RULES,
        "scenarios": PROVIDER_SCENARIOS,
        "migration_rules": REGRAS_MIGRACAO_DATABASE,
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo_passo,
    }


def gerar_manifesto_database_providers() -> Dict[str, Any]:
    saude = calcular_saude_database_providers()
    manifesto = {
        "versao": VERSAO_API_DATABASE_PROVIDERS_VALORIS,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "saude": saude,
        "providers": PROVEDORES_DATABASE,
        "factory_rules": PROVIDER_FACTORY_RULES,
        "provider_scenarios": PROVIDER_SCENARIOS,
        "repository_contract": METODOS_REPOSITORY_CONTRACT,
        "migration_rules": REGRAS_MIGRACAO_DATABASE,
        "estrategia": {
            "agora": "Criar camada abstrata e placeholders seguros.",
            "proxima_versao": "Integrar provider factory no backend sem conexão externa real.",
            "regra": "Local/hybrid permanece padrão e fallback obrigatório.",
        },
    }
    CAMINHO_MANIFESTO_DATABASE_PROVIDERS.write_text(json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifesto


def _injetar_css_database_providers() -> None:
    st.markdown(
        """
        <style>
            .database-providers-hero {
                padding: clamp(1.2rem, 3vw, 2.05rem);
                border-radius: 30px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    radial-gradient(circle at top left, rgba(214, 181, 109, 0.20), transparent 32%),
                    radial-gradient(circle at bottom right, rgba(65, 120, 190, 0.20), transparent 36%),
                    linear-gradient(135deg, rgba(6, 12, 23, 0.99), rgba(4, 8, 16, 0.99));
                box-shadow: 0 20px 62px rgba(0, 0, 0, 0.34);
                margin-bottom: 1rem;
            }
            .database-providers-eyebrow { color: #d6b56d; font-size: 0.74rem; letter-spacing: 0.14em; text-transform: uppercase; font-weight: 880; margin-bottom: 0.35rem; }
            .database-providers-title { color: #f4f7fb; font-size: clamp(1.8rem, 5.5vw, 3.2rem); font-weight: 950; line-height: 1.02; letter-spacing: -0.058em; margin-bottom: 0.55rem; }
            .database-providers-subtitle { color: rgba(244, 247, 251, 0.75); font-size: clamp(0.94rem, 2.2vw, 1.06rem); line-height: 1.56; max-width: 1050px; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def renderizar_api_database_providers_valoris() -> None:
    _injetar_css_database_providers()

    st.markdown(
        f"""
        <div class="database-providers-hero">
            <div class="database-providers-eyebrow">Valoris • Database Providers • v{VERSAO_API_DATABASE_PROVIDERS_VALORIS}</div>
            <div class="database-providers-title">Camada abstrata de providers.</div>
            <div class="database-providers-subtitle">
                Estrutura para LocalCSV, LocalSQLite, Hybrid, Supabase e Postgres sem abrir conexão externa real.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    saude = calcular_saude_database_providers()

    st.markdown("### Diagnóstico dos providers")
    col_1, col_2, col_3, col_4 = st.columns(4)
    with col_1:
        st.metric("Score Providers", f"{saude['score_providers']}/100")
    with col_2:
        st.metric("Risco", saude["risco"])
    with col_3:
        st.metric("Scaffold", "OK" if saude["scaffold_pronto"] else "Pendente")
    with col_4:
        st.metric("Fallback", "OK" if saude["fallback_local_ok"] else "Pendente")

    st.progress(saude["score_providers"] / 100)

    if saude["score_providers"] >= 84 and saude["scaffold_pronto"]:
        st.success(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    elif saude["score_providers"] >= 60:
        st.warning(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    else:
        st.info(f"**{saude['decisao']}** — {saude['proximo_passo']}")

    st.divider()

    st.markdown("### Scores herdados")
    col_a, col_b, col_c, col_d = st.columns(4)
    with col_a:
        st.metric("Contracts", f"{saude['score_contracts']}/100")
    with col_b:
        st.metric("Cloud", f"{saude['score_cloud']}/100")
    with col_c:
        st.metric("Security", f"{saude['score_security']}/100")
    with col_d:
        st.metric("Adapter", f"{saude['score_adapter']}/100")

    st.divider()

    st.markdown("### Providers planejados")
    st.dataframe(PROVEDORES_DATABASE, width="stretch", hide_index=True)
    st.markdown("### Regras da factory")
    st.dataframe(PROVIDER_FACTORY_RULES, width="stretch", hide_index=True)
    st.markdown("### Cenários")
    st.dataframe(PROVIDER_SCENARIOS, width="stretch", hide_index=True)

    st.divider()

    col_btn_1, col_btn_2, col_btn_3, col_btn_4 = st.columns(4)

    with col_btn_1:
        if st.button("Gerar scaffold providers", key="db_providers_scaffold"):
            resultado = gerar_database_providers_scaffold()
            st.success(resultado["mensagem"] if resultado["ok"] else "Scaffold gerado com erro de compilação.")
            st.json(resultado)

    with col_btn_2:
        if st.button("Gerar manifesto Providers", key="db_providers_manifesto"):
            manifesto = gerar_manifesto_database_providers()
            st.success(f"Manifesto gerado: {CAMINHO_MANIFESTO_DATABASE_PROVIDERS}")
            st.json({"versao": manifesto["versao"], "score_providers": manifesto["saude"]["score_providers"], "decisao": manifesto["saude"]["decisao"]})

    with col_btn_3:
        if st.button("Salvar providers .md", key="db_providers_md"):
            resultado = salvar_providers_database_markdown()
            st.success(f"Blueprint salvo: {resultado['arquivo']}")
            st.json(resultado)

    with col_btn_4:
        if st.button("Salvar decisão Providers", key="db_providers_decisao"):
            registro = salvar_decisao_database_providers(
                {
                    "score_providers": saude["score_providers"],
                    "score_contracts": saude["score_contracts"],
                    "score_cloud": saude["score_cloud"],
                    "score_security": saude["score_security"],
                    "score_adapter": saude["score_adapter"],
                    "score_tests": saude["score_tests"],
                    "api_online": saude["api_online"],
                    "fallback_local_ok": saude["fallback_local_ok"],
                    "scaffold_pronto": saude["scaffold_pronto"],
                    "factory_pronto": saude["factory_pronto"],
                    "providers_planejados": saude["providers_planejados"],
                    "risco": saude["risco"],
                    "decisao": saude["decisao"],
                    "proximo_passo": saude["proximo_passo"],
                    "observacoes": "Decisão gerada pela camada abstrata de providers.",
                }
            )
            st.success(f"Decisão salva: {registro['decisao']}")
            st.rerun()

    st.download_button("Baixar providers Database (.md)", data=gerar_markdown_providers_database(saude), file_name="PROVIDERS_DATABASE_VALORIS.md", mime="text/markdown", key="download_providers_database_md")
    st.download_button("Baixar decisões Providers (.csv)", data=gerar_csv_decisoes_database_providers(), file_name="decisoes_api_database_providers_valoris.csv", mime="text/csv", key="download_decisoes_database_providers")

    st.divider()
    st.markdown("### Scaffold atual")
    st.json(saude["scaffold"])

    with st.expander("Ver resumo técnico"):
        st.json(
            {
                "score_providers": saude["score_providers"],
                "risco": saude["risco"],
                "decisao": saude["decisao"],
                "proximo_passo": saude["proximo_passo"],
                "api_online": saude["api_online"],
                "fallback_local_ok": saude["fallback_local_ok"],
                "security_ok": saude["security_ok"],
                "scaffold_pronto": saude["scaffold_pronto"],
                "factory_pronto": saude["factory_pronto"],
                "repository_bridge_ok": saude["repository_bridge_ok"],
                "storage_config_ok": saude["storage_config_ok"],
                "gitignore_ok": saude["gitignore_ok"],
            }
        )


def executar_autoteste_api_database_providers_valoris() -> List[Dict[str, str]]:
    saude = calcular_saude_database_providers()
    return [
        {"teste": "versao_database_providers", "status": "OK" if VERSAO_API_DATABASE_PROVIDERS_VALORIS == "3.8.72" else "FALHA", "detalhe": VERSAO_API_DATABASE_PROVIDERS_VALORIS},
        {"teste": "score_providers", "status": "OK" if 0 <= saude["score_providers"] <= 100 else "FALHA", "detalhe": str(saude["score_providers"])},
        {"teste": "providers_planejados", "status": "OK" if len(PROVEDORES_DATABASE) >= 5 else "FALHA", "detalhe": str(len(PROVEDORES_DATABASE))},
        {"teste": "renderizador", "status": "OK" if callable(renderizar_api_database_providers_valoris) else "FALHA", "detalhe": "renderizar_api_database_providers_valoris"},
    ]
