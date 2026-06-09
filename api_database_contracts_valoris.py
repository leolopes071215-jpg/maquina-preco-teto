# api_database_contracts_valoris.py

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

import streamlit as st

from api_database_cloud_valoris import calcular_saude_database_cloud, calcular_sql_blueprint, SCHEMAS_POSTGRES, ENV_VARS_CLOUD
from api_security_panel_valoris import calcular_saude_api_security_panel
from api_security_key_valoris import calcular_saude_api_security
from api_storage_adapter_valoris import calcular_saude_api_adapter
from api_endpoint_tests_valoris import calcular_saude_api_endpoint_tests
from api_smoke_tests_valoris import testar_health_api

VERSAO_API_DATABASE_CONTRACTS_VALORIS = "3.8.71"

CAMINHO_DECISOES_DATABASE_CONTRACTS = Path("decisoes_api_database_contracts_valoris.csv")
CAMINHO_MANIFESTO_DATABASE_CONTRACTS = Path("manifesto_api_database_contracts_valoris.json")
CAMINHO_CONTRATOS_DATABASE_MD = Path("CONTRATOS_DATABASE_VALORIS.md")
CAMINHO_DATABASE_CONTRACTS_EXAMPLE = Path("api_valoris/app/services/database_contracts_example.py")
CAMINHO_REPOSITORY_BRIDGE = Path("api_valoris/app/services/repository_bridge.py")
CAMINHO_STORAGE_CONFIG = Path("api_valoris/app/core/storage_config.py")
CAMINHO_DB_LOCAL = Path("valoris_api_local.sqlite3")
CAMINHO_LEADS_CSV = Path("lista_espera_beta.csv")
CAMINHO_EVENTS_CSV = Path("eventos_publicos_valoris.csv")
CAMINHO_GITIGNORE = Path(".gitignore")

CAMPOS_DECISAO_DATABASE_CONTRACTS = [
    "id", "data_registro", "score_contracts", "score_cloud", "score_security",
    "score_adapter", "score_tests", "api_online", "fallback_local_ok", "contratos_prontos",
    "providers_mapeados", "metodos_obrigatorios", "risco", "decisao", "proximo_passo", "observacoes",
]

METODOS_REPOSITORY_CONTRACT = [
    {"metodo": "create_lead(payload)", "entrada": "LeadCreate", "saida": "dict normalizado", "regra": "Gravar lead mantendo CSV/SQLite e futuro provider cloud.", "criticidade": "Alta"},
    {"metodo": "list_leads(limit, source)", "entrada": "limit:int, source:auto/csv/sqlite/cloud", "saida": "dict com count e leads", "regra": "Listar dados apenas por rota protegida.", "criticidade": "Alta"},
    {"metodo": "create_event(payload)", "entrada": "EventCreate", "saida": "dict normalizado", "regra": "Gravar analytics somente por endpoint protegido.", "criticidade": "Média/alta"},
    {"metodo": "storage_health()", "entrada": "nenhuma", "saida": "dict de saúde do storage", "regra": "Diagnóstico interno protegido por API Key.", "criticidade": "Média"},
    {"metodo": "migrate_from_local(batch_size)", "entrada": "batch_size:int", "saida": "dict de migração", "regra": "Futuro: migrar sem apagar origem local sem conferência.", "criticidade": "Alta futura"},
]

PROVEDORES_DATABASE = [
    {"provider": "local_csv", "status": "Ativo", "uso": "Fallback simples e auditoria manual", "forca": "Transparente", "risco": "Não escala", "manter": True},
    {"provider": "local_sqlite", "status": "Ativo", "uso": "Banco local principal do beta", "forca": "Leve e transacional", "risco": "Não é multiusuário remoto", "manter": True},
    {"provider": "hybrid", "status": "Ativo recomendado", "uso": "CSV + SQLite", "forca": "Redundância local", "risco": "Pode divergir se mal usado", "manter": True},
    {"provider": "supabase", "status": "Planejado", "uso": "Cloud gerenciada com Postgres", "forca": "Dashboard, APIs, auth futura", "risco": "Secrets e custo", "manter": False},
    {"provider": "postgres", "status": "Planejado", "uso": "Banco PostgreSQL direto", "forca": "Robusto e portável", "risco": "Operação mais complexa", "manter": False},
]

REGRAS_MIGRACAO_DATABASE = [
    {"regra": "Nada externo pode quebrar o local", "detalhe": "CSV/SQLite continuam como fallback.", "prioridade": "Obrigatória"},
    {"regra": "Secrets nunca entram no Git", "detalhe": "DSN e service key só em ambiente seguro.", "prioridade": "Obrigatória"},
    {"regra": "Cloud começa como espelho", "detalhe": "Primeiro copiar, depois validar, só então promover.", "prioridade": "Alta"},
    {"regra": "Migração exige contagem", "detalhe": "Contagem local e cloud precisa bater.", "prioridade": "Alta"},
    {"regra": "Rotas sensíveis continuam protegidas", "detalhe": "API Key evolui para segredo forte e auth real.", "prioridade": "Alta"},
]


def _limpar_texto(valor: Any) -> str:
    return "" if valor is None else str(valor).strip()


def _garantir_csv(caminho: Path, campos: List[str]) -> None:
    if caminho.exists():
        return
    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()


def gerar_csv_decisoes_database_contracts() -> str:
    _garantir_csv(CAMINHO_DECISOES_DATABASE_CONTRACTS, CAMPOS_DECISAO_DATABASE_CONTRACTS)
    return CAMINHO_DECISOES_DATABASE_CONTRACTS.read_text(encoding="utf-8")


def salvar_decisao_database_contracts(decisao: Dict[str, Any]) -> Dict[str, str]:
    _garantir_csv(CAMINHO_DECISOES_DATABASE_CONTRACTS, CAMPOS_DECISAO_DATABASE_CONTRACTS)
    registro = {campo: "" for campo in CAMPOS_DECISAO_DATABASE_CONTRACTS}
    registro.update({
        "id": str(uuid4())[:8],
        "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score_contracts": str(decisao.get("score_contracts", "")),
        "score_cloud": str(decisao.get("score_cloud", "")),
        "score_security": str(decisao.get("score_security", "")),
        "score_adapter": str(decisao.get("score_adapter", "")),
        "score_tests": str(decisao.get("score_tests", "")),
        "api_online": str(decisao.get("api_online", "")),
        "fallback_local_ok": str(decisao.get("fallback_local_ok", "")),
        "contratos_prontos": str(decisao.get("contratos_prontos", "")),
        "providers_mapeados": str(decisao.get("providers_mapeados", "")),
        "metodos_obrigatorios": str(decisao.get("metodos_obrigatorios", "")),
        "risco": _limpar_texto(decisao.get("risco", "")),
        "decisao": _limpar_texto(decisao.get("decisao", "")),
        "proximo_passo": _limpar_texto(decisao.get("proximo_passo", "")),
        "observacoes": _limpar_texto(decisao.get("observacoes", "")),
    })
    with CAMINHO_DECISOES_DATABASE_CONTRACTS.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISAO_DATABASE_CONTRACTS)
        escritor.writerow(registro)
    return registro


def _arquivo_contem(caminho: Path, termos: List[str]) -> bool:
    if not caminho.exists():
        return False
    conteudo = caminho.read_text(encoding="utf-8", errors="ignore")
    return all(termo in conteudo for termo in termos)


def _gitignore_contem(termo: str) -> bool:
    return CAMINHO_GITIGNORE.exists() and termo in CAMINHO_GITIGNORE.read_text(encoding="utf-8", errors="ignore")


def avaliar_repository_bridge_atual() -> Dict[str, Any]:
    termos = ["class RepositoryBridge", "create_lead", "list_leads", "create_event", "storage_health"]
    existe = CAMINHO_REPOSITORY_BRIDGE.exists()
    return {
        "arquivo": str(CAMINHO_REPOSITORY_BRIDGE),
        "existe": existe,
        "validado": _arquivo_contem(CAMINHO_REPOSITORY_BRIDGE, termos),
        "termos_obrigatorios": termos,
        "tamanho_bytes": CAMINHO_REPOSITORY_BRIDGE.stat().st_size if existe else 0,
    }


def avaliar_contratos_database() -> Dict[str, Any]:
    return {
        "schemas_ok": len(SCHEMAS_POSTGRES) >= 3,
        "providers_ok": len(PROVEDORES_DATABASE) >= 5,
        "metodos_ok": len(METODOS_REPOSITORY_CONTRACT) >= 4,
        "regras_ok": len(REGRAS_MIGRACAO_DATABASE) >= 5,
        "env_ok": len(ENV_VARS_CLOUD) >= 5,
        "schemas_total": len(SCHEMAS_POSTGRES),
        "providers_total": len(PROVEDORES_DATABASE),
        "metodos_total": len(METODOS_REPOSITORY_CONTRACT),
        "regras_total": len(REGRAS_MIGRACAO_DATABASE),
        "env_total": len(ENV_VARS_CLOUD),
        "ok": len(SCHEMAS_POSTGRES) >= 3 and len(PROVEDORES_DATABASE) >= 5 and len(METODOS_REPOSITORY_CONTRACT) >= 4 and len(REGRAS_MIGRACAO_DATABASE) >= 5,
    }


def gerar_database_contracts_example() -> Dict[str, Any]:
    conteudo = '''"""Contratos futuros de banco — Valoris.

Arquivo exemplo. A implementação real deve manter compatibilidade com RepositoryBridge e fallback local.
"""

from __future__ import annotations

from typing import Any, Dict, Protocol


class ValorisDatabaseProvider(Protocol):
    def create_lead(self, payload: Any) -> Dict[str, Any]: ...
    def list_leads(self, limit: int = 100, source: str = "auto") -> Dict[str, Any]: ...
    def create_event(self, payload: Any) -> Dict[str, Any]: ...
    def storage_health(self) -> Dict[str, Any]: ...


class MigrationProvider(Protocol):
    def migrate_from_local(self, batch_size: int = 100) -> Dict[str, Any]: ...
'''
    CAMINHO_DATABASE_CONTRACTS_EXAMPLE.parent.mkdir(parents=True, exist_ok=True)
    CAMINHO_DATABASE_CONTRACTS_EXAMPLE.write_text(conteudo, encoding="utf-8")
    return {"ok": True, "arquivo": str(CAMINHO_DATABASE_CONTRACTS_EXAMPLE), "mensagem": "Exemplo de contratos gerado."}


def calcular_saude_database_contracts() -> Dict[str, Any]:
    try:
        cloud = calcular_saude_database_cloud()
    except Exception as erro:
        cloud = {"score_cloud": 0, "security_ok": False, "storage_local_ok": False, "erro": str(erro)}
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
    contratos = avaliar_contratos_database()
    bridge = avaliar_repository_bridge_atual()

    fallback_local_ok = CAMINHO_DB_LOCAL.exists() and CAMINHO_LEADS_CSV.exists() and CAMINHO_EVENTS_CSV.exists()
    storage_config_ok = _arquivo_contem(CAMINHO_STORAGE_CONFIG, ["csv", "sqlite", "hybrid"])
    gitignore_ok = _gitignore_contem("valoris_api_local.sqlite3") and _gitignore_contem("lista_espera_beta.csv") and _gitignore_contem("eventos_publicos_valoris.csv")

    score_cloud = int(cloud.get("score_cloud", 0) or 0)
    score_security = int(security.get("score_security", 0) or 0)
    score_adapter = int(adapter.get("score_adapter", 0) or 0)
    score_tests = int(endpoint_tests.get("score_tests", 0) or 0)

    score = 10
    score += min(score_cloud * 0.20, 20)
    score += min(score_security * 0.12, 12)
    score += min(score_adapter * 0.12, 12)
    score += min(score_tests * 0.08, 8)
    score += 10 if health.get("health_ok") else 0
    score += 10 if contratos["ok"] else 0
    score += 8 if bridge["validado"] else 0
    score += 8 if fallback_local_ok else 0
    score += 6 if storage_config_ok else 0
    score += 4 if gitignore_ok else 0
    score = int(round(max(0, min(100, score))))

    security_ok = bool(security.get("protected_ok")) or bool(security_panel.get("protected_ok"))
    contratos_prontos = contratos["ok"] and bridge["validado"]

    if not security_ok:
        risco = "Alto"
        decisao = "Não criar conexão cloud ainda"
        proximo_passo = "Validar segurança da API antes dos contratos externos."
    elif not fallback_local_ok:
        risco = "Médio/alto"
        decisao = "Fallback local incompleto"
        proximo_passo = "Garantir CSV/SQLite antes de criar provider cloud."
    elif not contratos_prontos:
        risco = "Médio"
        decisao = "Contratos ainda incompletos"
        proximo_passo = "Revisar métodos obrigatórios e providers."
    elif score >= 84:
        risco = "Médio controlado"
        decisao = "Contratos aprovados para próxima etapa"
        proximo_passo = "Avançar para camada abstrata local/cloud sem secrets reais."
    else:
        risco = "Médio"
        decisao = "Contratos em progresso"
        proximo_passo = "Gerar manifesto, markdown e exemplo de contracts."

    return {
        "score_contracts": score,
        "score_cloud": score_cloud,
        "score_security": score_security,
        "score_adapter": score_adapter,
        "score_tests": score_tests,
        "api_online": bool(health.get("health_ok")),
        "fallback_local_ok": fallback_local_ok,
        "security_ok": security_ok,
        "contratos_prontos": contratos_prontos,
        "providers_mapeados": contratos["providers_total"],
        "metodos_obrigatorios": contratos["metodos_total"],
        "storage_config_ok": storage_config_ok,
        "gitignore_ok": gitignore_ok,
        "contratos": contratos,
        "bridge": bridge,
        "health": health,
        "providers": PROVEDORES_DATABASE,
        "metodos": METODOS_REPOSITORY_CONTRACT,
        "regras": REGRAS_MIGRACAO_DATABASE,
        "schemas": SCHEMAS_POSTGRES,
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo_passo,
    }


def gerar_markdown_contratos_database(saude: Dict[str, Any] | None = None) -> str:
    if saude is None:
        saude = calcular_saude_database_contracts()
    metodos = "\n".join([f"- **{m['metodo']}** — {m['regra']}" for m in METODOS_REPOSITORY_CONTRACT])
    providers = "\n".join([f"- **{p['provider']}** ({p['status']}): {p['uso']}" for p in PROVEDORES_DATABASE])
    regras = "\n".join([f"- **{r['prioridade']}** — {r['regra']}: {r['detalhe']}" for r in REGRAS_MIGRACAO_DATABASE])
    return f"""# Contratos Database — Valoris

Versão: {VERSAO_API_DATABASE_CONTRACTS_VALORIS}  
Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}

## Diagnóstico

Score Contracts: {saude['score_contracts']}/100  
Risco: {saude['risco']}  
Decisão: {saude['decisao']}  
Próximo passo: {saude['proximo_passo']}

## Princípio

A Valoris só deve avançar para Supabase/PostgreSQL quando existir contrato claro entre app, API e provedores. CSV/SQLite seguem como fallback.

## Métodos obrigatórios

{metodos}

## Provedores mapeados

{providers}

## Regras de migração

{regras}

## SQL base

```sql
{calcular_sql_blueprint()}
```
"""


def salvar_contratos_database_markdown() -> Dict[str, Any]:
    saude = calcular_saude_database_contracts()
    CAMINHO_CONTRATOS_DATABASE_MD.write_text(gerar_markdown_contratos_database(saude), encoding="utf-8")
    return {"ok": True, "arquivo": str(CAMINHO_CONTRATOS_DATABASE_MD), "score_contracts": saude["score_contracts"], "decisao": saude["decisao"]}


def gerar_manifesto_database_contracts() -> Dict[str, Any]:
    saude = calcular_saude_database_contracts()
    manifesto = {
        "versao": VERSAO_API_DATABASE_CONTRACTS_VALORIS,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "saude": saude,
        "providers": PROVEDORES_DATABASE,
        "metodos_repository_contract": METODOS_REPOSITORY_CONTRACT,
        "regras_migracao": REGRAS_MIGRACAO_DATABASE,
        "schemas": SCHEMAS_POSTGRES,
        "sql_blueprint": calcular_sql_blueprint(),
        "estrategia": {"agora": "Formalizar contratos", "proxima_versao": "Camada abstrata local/cloud sem secrets reais", "regra": "Fallback local não pode quebrar"},
    }
    CAMINHO_MANIFESTO_DATABASE_CONTRACTS.write_text(json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifesto


def _injetar_css_database_contracts() -> None:
    st.markdown(
        """
        <style>
            .database-contracts-hero { padding: clamp(1.2rem, 3vw, 2.05rem); border-radius: 30px; border: 1px solid rgba(255,255,255,0.09); background: linear-gradient(135deg, rgba(6,12,23,0.99), rgba(4,8,16,0.99)); box-shadow: 0 20px 62px rgba(0,0,0,0.34); margin-bottom: 1rem; }
            .database-contracts-eyebrow { color: #d6b56d; font-size: .74rem; letter-spacing: .14em; text-transform: uppercase; font-weight: 880; margin-bottom: .35rem; }
            .database-contracts-title { color: #f4f7fb; font-size: clamp(1.8rem, 5.5vw, 3.2rem); font-weight: 950; line-height: 1.02; letter-spacing: -.058em; margin-bottom: .55rem; }
            .database-contracts-subtitle { color: rgba(244,247,251,.75); font-size: clamp(.94rem, 2.2vw, 1.06rem); line-height: 1.56; max-width: 1050px; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def renderizar_api_database_contracts_valoris() -> None:
    _injetar_css_database_contracts()
    st.markdown(
        f"""
        <div class="database-contracts-hero">
            <div class="database-contracts-eyebrow">Valoris • Database Contracts • v{VERSAO_API_DATABASE_CONTRACTS_VALORIS}</div>
            <div class="database-contracts-title">Contratos Local/Supabase/Postgres.</div>
            <div class="database-contracts-subtitle">Formalização dos métodos, provedores, tabelas e regras para evoluir para cloud sem quebrar CSV/SQLite.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    saude = calcular_saude_database_contracts()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Score Contracts", f"{saude['score_contracts']}/100")
    c2.metric("Risco", saude["risco"])
    c3.metric("Fallback local", "OK" if saude["fallback_local_ok"] else "Pendente")
    c4.metric("Contratos", "OK" if saude["contratos_prontos"] else "Pendente")
    st.progress(saude["score_contracts"] / 100)
    if saude["score_contracts"] >= 84 and saude["contratos_prontos"]:
        st.success(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    elif saude["score_contracts"] >= 60:
        st.warning(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    else:
        st.info(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    st.divider()
    st.markdown("### Métodos obrigatórios")
    st.dataframe(METODOS_REPOSITORY_CONTRACT, width="stretch", hide_index=True)
    st.markdown("### Provedores")
    st.dataframe(PROVEDORES_DATABASE, width="stretch", hide_index=True)
    st.markdown("### Regras de migração")
    st.dataframe(REGRAS_MIGRACAO_DATABASE, width="stretch", hide_index=True)
    st.divider()
    b1, b2, b3, b4 = st.columns(4)
    with b1:
        if st.button("Gerar contracts example", key="db_contracts_example"):
            st.success(gerar_database_contracts_example()["mensagem"])
    with b2:
        if st.button("Gerar manifesto Contracts", key="db_contracts_manifesto"):
            manifesto = gerar_manifesto_database_contracts()
            st.success(f"Manifesto gerado: {CAMINHO_MANIFESTO_DATABASE_CONTRACTS}")
            st.json({"versao": manifesto["versao"], "score_contracts": manifesto["saude"]["score_contracts"]})
    with b3:
        if st.button("Salvar contratos .md", key="db_contracts_md"):
            st.success(f"Contratos salvos: {salvar_contratos_database_markdown()['arquivo']}")
    with b4:
        if st.button("Salvar decisão Contracts", key="db_contracts_decisao"):
            registro = salvar_decisao_database_contracts({**saude, "observacoes": "Decisão gerada pelos contratos Local/Supabase/Postgres."})
            st.success(f"Decisão salva: {registro['decisao']}")
    st.download_button("Baixar contratos Database (.md)", data=gerar_markdown_contratos_database(saude), file_name="CONTRATOS_DATABASE_VALORIS.md", mime="text/markdown", key="download_contratos_database_md")
    st.download_button("Baixar decisões Contracts (.csv)", data=gerar_csv_decisoes_database_contracts(), file_name="decisoes_api_database_contracts_valoris.csv", mime="text/csv", key="download_decisoes_database_contracts")
    with st.expander("Ver resumo técnico"):
        st.json({"score_contracts": saude["score_contracts"], "risco": saude["risco"], "decisao": saude["decisao"], "fallback_local_ok": saude["fallback_local_ok"], "contratos_prontos": saude["contratos_prontos"], "bridge": saude["bridge"]})


def executar_autoteste_api_database_contracts_valoris() -> List[Dict[str, str]]:
    saude = calcular_saude_database_contracts()
    return [
        {"teste": "versao_database_contracts", "status": "OK" if VERSAO_API_DATABASE_CONTRACTS_VALORIS == "3.8.71" else "FALHA", "detalhe": VERSAO_API_DATABASE_CONTRACTS_VALORIS},
        {"teste": "score_contracts", "status": "OK" if 0 <= saude["score_contracts"] <= 100 else "FALHA", "detalhe": str(saude["score_contracts"])},
        {"teste": "providers", "status": "OK" if len(PROVEDORES_DATABASE) >= 5 else "FALHA", "detalhe": str(len(PROVEDORES_DATABASE))},
        {"teste": "renderizador", "status": "OK" if callable(renderizar_api_database_contracts_valoris) else "FALHA", "detalhe": "renderizar_api_database_contracts_valoris"},
    ]
