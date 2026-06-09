# api_provider_runtime_valoris.py

from __future__ import annotations

import csv
import json
import py_compile
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

import streamlit as st

from api_database_providers_valoris import calcular_saude_database_providers
from api_database_contracts_valoris import calcular_saude_database_contracts
from api_database_cloud_valoris import calcular_saude_database_cloud
from api_security_key_valoris import calcular_saude_api_security
from api_storage_adapter_valoris import calcular_saude_api_adapter
from api_endpoint_tests_valoris import calcular_saude_api_endpoint_tests
from api_smoke_tests_valoris import testar_health_api


VERSAO_API_PROVIDER_RUNTIME_VALORIS = "3.8.73"

CAMINHO_DECISOES_PROVIDER_RUNTIME = Path("decisoes_api_provider_runtime_valoris.csv")
CAMINHO_MANIFESTO_PROVIDER_RUNTIME = Path("manifesto_api_provider_runtime_valoris.json")
CAMINHO_PROVIDER_RUNTIME_MD = Path("PROVIDER_RUNTIME_VALORIS.md")
CAMINHO_PROVIDER_RUNTIME_REPORT = Path("relatorio_provider_runtime_valoris.json")

CAMINHO_DATABASE_PROVIDERS = Path("api_valoris/app/services/database_providers.py")
CAMINHO_PROVIDER_FACTORY = Path("api_valoris/app/services/provider_factory.py")
CAMINHO_PROVIDER_RUNTIME_PROBE = Path("scripts_api_valoris/testar_provider_runtime_valoris.py")

CAMINHO_REPOSITORY_BRIDGE = Path("api_valoris/app/services/repository_bridge.py")
CAMINHO_DB_LOCAL = Path("valoris_api_local.sqlite3")
CAMINHO_LEADS_CSV = Path("lista_espera_beta.csv")
CAMINHO_EVENTS_CSV = Path("eventos_publicos_valoris.csv")
CAMINHO_GITIGNORE = Path(".gitignore")

CAMPOS_DECISAO_PROVIDER_RUNTIME = [
    "id",
    "data_registro",
    "score_runtime",
    "score_providers",
    "score_contracts",
    "score_cloud",
    "score_security",
    "score_adapter",
    "score_tests",
    "api_online",
    "runtime_probe_ok",
    "fallback_local_ok",
    "scaffold_ok",
    "providers_testados",
    "risco",
    "decisao",
    "proximo_passo",
    "observacoes",
]

PROVIDERS_RUNTIME_TESTADOS = [
    "local_csv",
    "local_sqlite",
    "hybrid",
    "supabase",
    "postgres",
    "provider_invalido",
]

PROVIDER_RUNTIME_RULES = [
    {
        "regra": "Provider padrão deve ser hybrid",
        "motivo": "O produto precisa preservar CSV + SQLite enquanto está em beta.",
        "prioridade": "Obrigatória",
    },
    {
        "regra": "Provider inválido deve cair para hybrid",
        "motivo": "Erro de configuração não pode quebrar o backend.",
        "prioridade": "Obrigatória",
    },
    {
        "regra": "Supabase/Postgres não podem abrir conexão real nesta versão",
        "motivo": "Ainda não existem secrets produtivos, RLS ou plano de rollback.",
        "prioridade": "Obrigatória",
    },
    {
        "regra": "Probe deve testar providers sem depender do navegador",
        "motivo": "A validação precisa funcionar em terminal e CI local.",
        "prioridade": "Alta",
    },
    {
        "regra": "Provider runtime deve ser reproduzível",
        "motivo": "Arquivos ignorados em api_valoris precisam ser regeneráveis pelos módulos versionados.",
        "prioridade": "Alta",
    },
]

PROVIDER_RUNTIME_PROBE_CODE = 'from __future__ import annotations\n\nimport json\nimport os\nimport sys\nfrom datetime import datetime\nfrom pathlib import Path\nfrom typing import Any, Dict\n\n\nROOT = Path(__file__).resolve().parents[1]\nAPI_ROOT = ROOT / "api_valoris"\n\nif str(API_ROOT) not in sys.path:\n    sys.path.insert(0, str(API_ROOT))\n\n\nclass DummyRepositoryBridge:\n    def create_lead(self, payload: Any) -> Dict[str, Any]:\n        return {"ok": True, "source": "dummy", "operation": "create_lead", "payload_type": type(payload).__name__}\n\n    def list_leads(self, limit: int = 100, source: str = "auto") -> Dict[str, Any]:\n        return {"ok": True, "source": source, "limit": limit, "count": 0, "leads": []}\n\n    def create_event(self, payload: Any) -> Dict[str, Any]:\n        return {"ok": True, "source": "dummy", "operation": "create_event", "payload_type": type(payload).__name__}\n\n    def storage_health(self) -> Dict[str, Any]:\n        return {"ok": True, "source": "dummy", "storage_mode": "hybrid"}\n\n\ndef testar_provider(provider_name: str) -> Dict[str, Any]:\n    os.environ["VALORIS_DATABASE_PROVIDER"] = provider_name\n\n    from app.services.provider_factory import build_database_provider, get_database_provider_name\n\n    resolved_provider = get_database_provider_name()\n    provider = build_database_provider(DummyRepositoryBridge())\n\n    resultado = {\n        "input": provider_name,\n        "resolved_provider": resolved_provider,\n        "built_class": provider.__class__.__name__,\n        "name": getattr(provider, "name", ""),\n        "storage_health": None,\n        "ok": False,\n        "erro": "",\n    }\n\n    try:\n        resultado["storage_health"] = provider.storage_health()\n        if provider_name in {"supabase", "postgres"}:\n            resultado["ok"] = resultado["storage_health"].get("ok") is False\n        elif provider_name == "provider_invalido":\n            resultado["ok"] = resolved_provider == "hybrid" and getattr(provider, "name", "") == "hybrid"\n        else:\n            resultado["ok"] = bool(resultado["storage_health"].get("ok")) and getattr(provider, "name", "") == resolved_provider\n    except Exception as erro:\n        resultado["erro"] = str(erro)\n        resultado["ok"] = False\n\n    return resultado\n\n\ndef main() -> int:\n    providers = ["local_csv", "local_sqlite", "hybrid", "supabase", "postgres", "provider_invalido"]\n    resultados = [testar_provider(provider) for provider in providers]\n\n    relatorio = {\n        "versao": "3.8.73",\n        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),\n        "providers_testados": providers,\n        "ok": all(item["ok"] for item in resultados),\n        "resultados": resultados,\n    }\n\n    output_path = ROOT / "relatorio_provider_runtime_valoris.json"\n    output_path.write_text(json.dumps(relatorio, ensure_ascii=False, indent=2), encoding="utf-8")\n\n    print(json.dumps(relatorio, ensure_ascii=False, indent=2))\n    return 0 if relatorio["ok"] else 1\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


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


def carregar_decisoes_provider_runtime() -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_DECISOES_PROVIDER_RUNTIME, CAMPOS_DECISAO_PROVIDER_RUNTIME)
    with CAMINHO_DECISOES_PROVIDER_RUNTIME.open("r", newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def gerar_csv_decisoes_provider_runtime() -> str:
    _garantir_csv(CAMINHO_DECISOES_PROVIDER_RUNTIME, CAMPOS_DECISAO_PROVIDER_RUNTIME)
    return CAMINHO_DECISOES_PROVIDER_RUNTIME.read_text(encoding="utf-8")


def salvar_decisao_provider_runtime(decisao: Dict[str, Any]) -> Dict[str, str]:
    _garantir_csv(CAMINHO_DECISOES_PROVIDER_RUNTIME, CAMPOS_DECISAO_PROVIDER_RUNTIME)

    registro = {
        "id": str(uuid4())[:8],
        "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score_runtime": str(decisao.get("score_runtime", "")),
        "score_providers": str(decisao.get("score_providers", "")),
        "score_contracts": str(decisao.get("score_contracts", "")),
        "score_cloud": str(decisao.get("score_cloud", "")),
        "score_security": str(decisao.get("score_security", "")),
        "score_adapter": str(decisao.get("score_adapter", "")),
        "score_tests": str(decisao.get("score_tests", "")),
        "api_online": str(decisao.get("api_online", "")),
        "runtime_probe_ok": str(decisao.get("runtime_probe_ok", "")),
        "fallback_local_ok": str(decisao.get("fallback_local_ok", "")),
        "scaffold_ok": str(decisao.get("scaffold_ok", "")),
        "providers_testados": str(decisao.get("providers_testados", "")),
        "risco": _limpar_texto(decisao.get("risco", "")),
        "decisao": _limpar_texto(decisao.get("decisao", "")),
        "proximo_passo": _limpar_texto(decisao.get("proximo_passo", "")),
        "observacoes": _limpar_texto(decisao.get("observacoes", "")),
    }

    with CAMINHO_DECISOES_PROVIDER_RUNTIME.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISAO_PROVIDER_RUNTIME)
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


def gerar_provider_runtime_probe() -> Dict[str, Any]:
    CAMINHO_PROVIDER_RUNTIME_PROBE.parent.mkdir(parents=True, exist_ok=True)
    CAMINHO_PROVIDER_RUNTIME_PROBE.write_text(PROVIDER_RUNTIME_PROBE_CODE, encoding="utf-8")

    try:
        py_compile.compile(str(CAMINHO_PROVIDER_RUNTIME_PROBE), doraise=True)
        ok = True
        erro = ""
    except Exception as exc:
        ok = False
        erro = str(exc)

    return {
        "ok": ok,
        "arquivo": str(CAMINHO_PROVIDER_RUNTIME_PROBE),
        "erro": erro,
        "mensagem": "Probe runtime gerado para testar ProviderFactory fora do navegador.",
    }


def executar_provider_runtime_probe() -> Dict[str, Any]:
    if not CAMINHO_PROVIDER_RUNTIME_PROBE.exists():
        gerar_provider_runtime_probe()

    comando = [sys.executable, str(CAMINHO_PROVIDER_RUNTIME_PROBE)]
    processo = subprocess.run(
        comando,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    stdout = processo.stdout.strip()
    stderr = processo.stderr.strip()

    relatorio = {}
    if CAMINHO_PROVIDER_RUNTIME_REPORT.exists():
        try:
            relatorio = json.loads(CAMINHO_PROVIDER_RUNTIME_REPORT.read_text(encoding="utf-8"))
        except Exception:
            relatorio = {}

    return {
        "ok": processo.returncode == 0 and bool(relatorio.get("ok")),
        "returncode": processo.returncode,
        "stdout": stdout[-4000:],
        "stderr": stderr[-4000:],
        "relatorio": relatorio,
        "arquivo_relatorio": str(CAMINHO_PROVIDER_RUNTIME_REPORT),
    }


def avaliar_provider_runtime_scaffold() -> Dict[str, Any]:
    providers_ok = _arquivo_contem(
        CAMINHO_DATABASE_PROVIDERS,
        [
            "class DatabaseProvider",
            "class LocalCSVProvider",
            "class LocalSQLiteProvider",
            "class HybridProvider",
            "class SupabaseProvider",
            "class PostgresProvider",
            "ProviderUnavailableError",
        ],
    )
    factory_ok = _arquivo_contem(
        CAMINHO_PROVIDER_FACTORY,
        [
            "SUPPORTED_DATABASE_PROVIDERS",
            "get_database_provider_name",
            "build_database_provider",
            "VALORIS_DATABASE_PROVIDER",
        ],
    )

    provider_compile_ok = False
    factory_compile_ok = False
    provider_compile_error = ""
    factory_compile_error = ""

    if CAMINHO_DATABASE_PROVIDERS.exists():
        try:
            py_compile.compile(str(CAMINHO_DATABASE_PROVIDERS), doraise=True)
            provider_compile_ok = True
        except Exception as erro:
            provider_compile_error = str(erro)

    if CAMINHO_PROVIDER_FACTORY.exists():
        try:
            py_compile.compile(str(CAMINHO_PROVIDER_FACTORY), doraise=True)
            factory_compile_ok = True
        except Exception as erro:
            factory_compile_error = str(erro)

    return {
        "providers_file": str(CAMINHO_DATABASE_PROVIDERS),
        "factory_file": str(CAMINHO_PROVIDER_FACTORY),
        "providers_existe": CAMINHO_DATABASE_PROVIDERS.exists(),
        "factory_existe": CAMINHO_PROVIDER_FACTORY.exists(),
        "providers_ok": providers_ok,
        "factory_ok": factory_ok,
        "provider_compile_ok": provider_compile_ok,
        "factory_compile_ok": factory_compile_ok,
        "provider_compile_error": provider_compile_error,
        "factory_compile_error": factory_compile_error,
        "ok": providers_ok and factory_ok and provider_compile_ok and factory_compile_ok,
    }


def gerar_markdown_provider_runtime(saude: Dict[str, Any] | None = None) -> str:
    if saude is None:
        saude = calcular_saude_provider_runtime()

    regras = "\n".join(
        [
            f"- **{item['prioridade']}** — {item['regra']}: {item['motivo']}"
            for item in PROVIDER_RUNTIME_RULES
        ]
    )
    testes = "\n".join([f"- `{provider}`" for provider in PROVIDERS_RUNTIME_TESTADOS])

    return f"""# Provider Runtime — Valoris

Versão: {VERSAO_API_PROVIDER_RUNTIME_VALORIS}  
Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Diagnóstico

Score Runtime: {saude["score_runtime"]}/100  
Risco: {saude["risco"]}  
Decisão: {saude["decisao"]}  
Próximo passo: {saude["proximo_passo"]}

## Objetivo

Validar a ProviderFactory fora do navegador, garantindo que a Valoris consiga escolher providers por variável de ambiente sem quebrar o modo local.

## Providers testados

{testes}

## Regras

{regras}

## Arquivos gerados localmente

- `{CAMINHO_PROVIDER_RUNTIME_PROBE}`
- `{CAMINHO_PROVIDER_RUNTIME_REPORT}`

## Segurança

SupabaseProvider e PostgresProvider continuam como placeholders. Nenhuma conexão externa real é aberta nesta versão.
"""


def salvar_provider_runtime_markdown() -> Dict[str, Any]:
    saude = calcular_saude_provider_runtime()
    CAMINHO_PROVIDER_RUNTIME_MD.write_text(gerar_markdown_provider_runtime(saude), encoding="utf-8")
    return {
        "ok": True,
        "arquivo": str(CAMINHO_PROVIDER_RUNTIME_MD),
        "score_runtime": saude["score_runtime"],
        "decisao": saude["decisao"],
    }


def calcular_saude_provider_runtime(executar_probe: bool = False) -> Dict[str, Any]:
    try:
        providers = calcular_saude_database_providers()
    except Exception as erro:
        providers = {"score_providers": 0, "scaffold_pronto": False, "fallback_local_ok": False, "erro": str(erro)}

    try:
        contracts = calcular_saude_database_contracts()
    except Exception as erro:
        contracts = {"score_contracts": 0, "contratos_prontos": False, "erro": str(erro)}

    try:
        cloud = calcular_saude_database_cloud()
    except Exception as erro:
        cloud = {"score_cloud": 0, "erro": str(erro)}

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
    scaffold = avaliar_provider_runtime_scaffold()

    if executar_probe:
        probe = executar_provider_runtime_probe()
    elif CAMINHO_PROVIDER_RUNTIME_REPORT.exists():
        try:
            relatorio = json.loads(CAMINHO_PROVIDER_RUNTIME_REPORT.read_text(encoding="utf-8"))
        except Exception:
            relatorio = {}
        probe = {
            "ok": bool(relatorio.get("ok")),
            "returncode": 0 if relatorio.get("ok") else 1,
            "stdout": "",
            "stderr": "",
            "relatorio": relatorio,
            "arquivo_relatorio": str(CAMINHO_PROVIDER_RUNTIME_REPORT),
        }
    else:
        probe = {"ok": False, "returncode": None, "stdout": "", "stderr": "", "relatorio": {}, "arquivo_relatorio": str(CAMINHO_PROVIDER_RUNTIME_REPORT)}

    fallback_local_ok = CAMINHO_DB_LOCAL.exists() and CAMINHO_LEADS_CSV.exists() and CAMINHO_EVENTS_CSV.exists()
    repository_bridge_ok = _arquivo_contem(CAMINHO_REPOSITORY_BRIDGE, ["class RepositoryBridge", "storage_health"])
    gitignore_ok = (
        _gitignore_contem("scripts_api_valoris/testar_provider_runtime_valoris.py")
        and _gitignore_contem("relatorio_provider_runtime_valoris.json")
        and _gitignore_contem("manifesto_api_provider_runtime_valoris.json")
    )

    score_providers = int(providers.get("score_providers", 0) or 0)
    score_contracts = int(contracts.get("score_contracts", 0) or 0)
    score_cloud = int(cloud.get("score_cloud", 0) or 0)
    score_security = int(security.get("score_security", 0) or 0)
    score_adapter = int(adapter.get("score_adapter", 0) or 0)
    score_tests = int(endpoint_tests.get("score_tests", 0) or 0)

    score = 10
    score += min(score_providers * 0.16, 16)
    score += min(score_contracts * 0.12, 12)
    score += min(score_cloud * 0.08, 8)
    score += min(score_security * 0.10, 10)
    score += min(score_adapter * 0.08, 8)
    score += min(score_tests * 0.06, 6)
    score += 8 if bool(health.get("health_ok")) else 0
    score += 10 if scaffold["ok"] else 0
    score += 10 if bool(probe.get("ok")) else 0
    score += 8 if fallback_local_ok else 0
    score += 6 if repository_bridge_ok else 0
    score += 4 if gitignore_ok else 0
    score = int(round(max(0, min(100, score))))

    security_ok = bool(security.get("protected_ok")) or bool(cloud.get("security_ok"))

    if not security_ok:
        risco = "Alto"
        decisao = "Não avançar runtime provider ainda"
        proximo_passo = "Validar segurança antes de qualquer provider externo."
    elif not scaffold["ok"]:
        risco = "Médio/alto"
        decisao = "Scaffold dos providers incompleto"
        proximo_passo = "Regenerar database_providers.py e provider_factory.py."
    elif not probe.get("ok"):
        risco = "Médio"
        decisao = "Probe runtime pendente"
        proximo_passo = "Gerar e executar o probe runtime pelo terminal."
    elif score >= 84:
        risco = "Médio controlado"
        decisao = "Provider runtime aprovado"
        proximo_passo = "Avançar para integração controlada da factory no backend local."
    else:
        risco = "Médio"
        decisao = "Runtime em progresso"
        proximo_passo = "Gerar manifesto, markdown e decisão runtime."

    return {
        "score_runtime": score,
        "score_providers": score_providers,
        "score_contracts": score_contracts,
        "score_cloud": score_cloud,
        "score_security": score_security,
        "score_adapter": score_adapter,
        "score_tests": score_tests,
        "api_online": bool(health.get("health_ok")),
        "runtime_probe_ok": bool(probe.get("ok")),
        "fallback_local_ok": fallback_local_ok,
        "scaffold_ok": scaffold["ok"],
        "providers_testados": len(PROVIDERS_RUNTIME_TESTADOS),
        "security_ok": security_ok,
        "repository_bridge_ok": repository_bridge_ok,
        "gitignore_ok": gitignore_ok,
        "health": health,
        "providers": providers,
        "contracts": contracts,
        "cloud": cloud,
        "security": security,
        "adapter": adapter,
        "endpoint_tests": endpoint_tests,
        "scaffold": scaffold,
        "probe": probe,
        "rules": PROVIDER_RUNTIME_RULES,
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo_passo,
    }


def gerar_manifesto_provider_runtime(executar_probe: bool = False) -> Dict[str, Any]:
    saude = calcular_saude_provider_runtime(executar_probe=executar_probe)
    manifesto = {
        "versao": VERSAO_API_PROVIDER_RUNTIME_VALORIS,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "saude": saude,
        "providers_testados": PROVIDERS_RUNTIME_TESTADOS,
        "runtime_rules": PROVIDER_RUNTIME_RULES,
        "estrategia": {
            "agora": "Validar ProviderFactory fora do navegador e sem conexão externa.",
            "proxima_versao": "Integrar factory ao backend local com seletor controlado.",
            "regra": "hybrid permanece padrão seguro.",
        },
    }
    CAMINHO_MANIFESTO_PROVIDER_RUNTIME.write_text(json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifesto


def _injetar_css_provider_runtime() -> None:
    st.markdown(
        """
        <style>
            .provider-runtime-hero {
                padding: clamp(1.2rem, 3vw, 2.05rem);
                border-radius: 30px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    radial-gradient(circle at top left, rgba(214, 181, 109, 0.20), transparent 32%),
                    radial-gradient(circle at bottom right, rgba(95, 140, 210, 0.20), transparent 36%),
                    linear-gradient(135deg, rgba(6, 12, 23, 0.99), rgba(4, 8, 16, 0.99));
                box-shadow: 0 20px 62px rgba(0, 0, 0, 0.34);
                margin-bottom: 1rem;
            }
            .provider-runtime-eyebrow { color: #d6b56d; font-size: 0.74rem; letter-spacing: 0.14em; text-transform: uppercase; font-weight: 880; margin-bottom: 0.35rem; }
            .provider-runtime-title { color: #f4f7fb; font-size: clamp(1.8rem, 5.5vw, 3.2rem); font-weight: 950; line-height: 1.02; letter-spacing: -0.058em; margin-bottom: 0.55rem; }
            .provider-runtime-subtitle { color: rgba(244, 247, 251, 0.75); font-size: clamp(0.94rem, 2.2vw, 1.06rem); line-height: 1.56; max-width: 1050px; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def renderizar_api_provider_runtime_valoris() -> None:
    _injetar_css_provider_runtime()
    st.markdown(
        f"""
        <div class="provider-runtime-hero">
            <div class="provider-runtime-eyebrow">Valoris • Provider Runtime • v{VERSAO_API_PROVIDER_RUNTIME_VALORIS}</div>
            <div class="provider-runtime-title">ProviderFactory validada fora do navegador.</div>
            <div class="provider-runtime-subtitle">
                Teste terminal-first dos providers local_csv, local_sqlite, hybrid, supabase e postgres.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    saude = calcular_saude_provider_runtime()

    st.markdown("### Diagnóstico runtime")
    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Score Runtime", f"{saude['score_runtime']}/100")
    with col_2:
        st.metric("Risco", saude["risco"])
    with col_3:
        st.metric("Probe", "OK" if saude["runtime_probe_ok"] else "Pendente")
    with col_4:
        st.metric("Scaffold", "OK" if saude["scaffold_ok"] else "Pendente")

    st.progress(saude["score_runtime"] / 100)

    if saude["score_runtime"] >= 84 and saude["runtime_probe_ok"]:
        st.success(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    elif saude["score_runtime"] >= 60:
        st.warning(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    else:
        st.info(f"**{saude['decisao']}** — {saude['proximo_passo']}")

    st.divider()
    st.markdown("### Providers testados")
    st.dataframe([{"provider": item} for item in PROVIDERS_RUNTIME_TESTADOS], width="stretch", hide_index=True)

    st.markdown("### Regras de runtime")
    st.dataframe(PROVIDER_RUNTIME_RULES, width="stretch", hide_index=True)

    st.divider()

    col_btn_1, col_btn_2, col_btn_3, col_btn_4 = st.columns(4)

    with col_btn_1:
        if st.button("Gerar probe runtime", key="provider_runtime_probe"):
            resultado = gerar_provider_runtime_probe()
            st.success(resultado["mensagem"] if resultado["ok"] else "Probe gerado com erro de compilação.")
            st.json(resultado)

    with col_btn_2:
        if st.button("Executar probe runtime", key="provider_runtime_run_probe"):
            resultado = executar_provider_runtime_probe()
            if resultado["ok"]:
                st.success("Probe runtime aprovado.")
            else:
                st.warning("Probe runtime falhou. Veja detalhes.")
            st.json({"ok": resultado["ok"], "returncode": resultado["returncode"], "arquivo_relatorio": resultado["arquivo_relatorio"], "stderr": resultado["stderr"]})

    with col_btn_3:
        if st.button("Gerar manifesto Runtime", key="provider_runtime_manifesto"):
            manifesto = gerar_manifesto_provider_runtime(executar_probe=False)
            st.success(f"Manifesto gerado: {CAMINHO_MANIFESTO_PROVIDER_RUNTIME}")
            st.json({"versao": manifesto["versao"], "score_runtime": manifesto["saude"]["score_runtime"], "decisao": manifesto["saude"]["decisao"]})

    with col_btn_4:
        if st.button("Salvar decisão Runtime", key="provider_runtime_decisao"):
            registro = salvar_decisao_provider_runtime(
                {
                    "score_runtime": saude["score_runtime"],
                    "score_providers": saude["score_providers"],
                    "score_contracts": saude["score_contracts"],
                    "score_cloud": saude["score_cloud"],
                    "score_security": saude["score_security"],
                    "score_adapter": saude["score_adapter"],
                    "score_tests": saude["score_tests"],
                    "api_online": saude["api_online"],
                    "runtime_probe_ok": saude["runtime_probe_ok"],
                    "fallback_local_ok": saude["fallback_local_ok"],
                    "scaffold_ok": saude["scaffold_ok"],
                    "providers_testados": saude["providers_testados"],
                    "risco": saude["risco"],
                    "decisao": saude["decisao"],
                    "proximo_passo": saude["proximo_passo"],
                    "observacoes": "Decisão gerada pelo runtime de providers.",
                }
            )
            st.success(f"Decisão salva: {registro['decisao']}")
            st.rerun()

    if st.button("Salvar Provider Runtime .md", key="provider_runtime_md"):
        resultado = salvar_provider_runtime_markdown()
        st.success(f"Markdown salvo: {resultado['arquivo']}")
        st.json(resultado)

    st.download_button("Baixar Provider Runtime (.md)", data=gerar_markdown_provider_runtime(saude), file_name="PROVIDER_RUNTIME_VALORIS.md", mime="text/markdown", key="download_provider_runtime_md")
    st.download_button("Baixar decisões Runtime (.csv)", data=gerar_csv_decisoes_provider_runtime(), file_name="decisoes_api_provider_runtime_valoris.csv", mime="text/csv", key="download_decisoes_provider_runtime")

    st.divider()
    st.markdown("### Resumo técnico")
    st.json(
        {
            "score_runtime": saude["score_runtime"],
            "risco": saude["risco"],
            "decisao": saude["decisao"],
            "proximo_passo": saude["proximo_passo"],
            "runtime_probe_ok": saude["runtime_probe_ok"],
            "fallback_local_ok": saude["fallback_local_ok"],
            "scaffold_ok": saude["scaffold_ok"],
            "repository_bridge_ok": saude["repository_bridge_ok"],
            "gitignore_ok": saude["gitignore_ok"],
        }
    )


def executar_autoteste_api_provider_runtime_valoris() -> List[Dict[str, str]]:
    saude = calcular_saude_provider_runtime(executar_probe=False)
    return [
        {"teste": "versao_provider_runtime", "status": "OK" if VERSAO_API_PROVIDER_RUNTIME_VALORIS == "3.8.73" else "FALHA", "detalhe": VERSAO_API_PROVIDER_RUNTIME_VALORIS},
        {"teste": "score_runtime", "status": "OK" if 0 <= saude["score_runtime"] <= 100 else "FALHA", "detalhe": str(saude["score_runtime"])},
        {"teste": "renderizador", "status": "OK" if callable(renderizar_api_provider_runtime_valoris) else "FALHA", "detalhe": "renderizar_api_provider_runtime_valoris"},
    ]
