# api_provider_backend_valoris.py

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

from api_provider_runtime_valoris import calcular_saude_provider_runtime
from api_database_providers_valoris import calcular_saude_database_providers
from api_database_contracts_valoris import calcular_saude_database_contracts
from api_database_cloud_valoris import calcular_saude_database_cloud
from api_security_key_valoris import calcular_saude_api_security
from api_storage_adapter_valoris import calcular_saude_api_adapter
from api_endpoint_tests_valoris import calcular_saude_api_endpoint_tests
from api_smoke_tests_valoris import testar_health_api


VERSAO_API_PROVIDER_BACKEND_VALORIS = "3.8.74"

CAMINHO_DECISOES_PROVIDER_BACKEND = Path("decisoes_api_provider_backend_valoris.csv")
CAMINHO_MANIFESTO_PROVIDER_BACKEND = Path("manifesto_api_provider_backend_valoris.json")
CAMINHO_PROVIDER_BACKEND_MD = Path("PROVIDER_BACKEND_VALORIS.md")
CAMINHO_PROVIDER_BACKEND_REPORT = Path("relatorio_provider_backend_valoris.json")

CAMINHO_PROVIDER_RUNTIME_BRIDGE = Path("api_valoris/app/services/provider_runtime_bridge.py")
CAMINHO_PROVIDER_BACKEND_PROBE = Path("scripts_api_valoris/testar_provider_backend_valoris.py")

CAMINHO_DATABASE_PROVIDERS = Path("api_valoris/app/services/database_providers.py")
CAMINHO_PROVIDER_FACTORY = Path("api_valoris/app/services/provider_factory.py")
CAMINHO_REPOSITORY_BRIDGE = Path("api_valoris/app/services/repository_bridge.py")

CAMINHO_DB_LOCAL = Path("valoris_api_local.sqlite3")
CAMINHO_LEADS_CSV = Path("lista_espera_beta.csv")
CAMINHO_EVENTS_CSV = Path("eventos_publicos_valoris.csv")
CAMINHO_GITIGNORE = Path(".gitignore")

CAMPOS_DECISAO_PROVIDER_BACKEND = [
    "id",
    "data_registro",
    "score_backend",
    "score_runtime",
    "score_providers",
    "score_contracts",
    "score_cloud",
    "score_security",
    "score_adapter",
    "score_tests",
    "api_online",
    "backend_probe_ok",
    "runtime_bridge_ok",
    "fallback_local_ok",
    "providers_testados",
    "risco",
    "decisao",
    "proximo_passo",
    "observacoes",
]

PROVIDERS_BACKEND_TESTADOS = [
    "local_csv",
    "local_sqlite",
    "hybrid",
    "supabase",
    "postgres",
    "provider_invalido",
]

PROVIDER_BACKEND_RULES = [
    {
        "regra": "ProviderRuntimeBridge deve envolver RepositoryBridge sem reescrever o backend",
        "motivo": "Integração controlada reduz risco e permite rollback simples.",
        "prioridade": "Obrigatória",
    },
    {
        "regra": "Provider inválido deve cair para hybrid",
        "motivo": "Configuração errada não pode quebrar o app nem a API local.",
        "prioridade": "Obrigatória",
    },
    {
        "regra": "Supabase/Postgres continuam placeholders",
        "motivo": "Ainda não há conexão real, secrets produtivos, RLS ou observabilidade.",
        "prioridade": "Obrigatória",
    },
    {
        "regra": "Probe deve rodar via terminal",
        "motivo": "O navegador do usuário apresenta instabilidade e não deve bloquear release.",
        "prioridade": "Alta",
    },
    {
        "regra": "Arquivos locais gerados não devem entrar no Git",
        "motivo": "api_valoris e scripts locais são regeneráveis e/ou ambiente-dependentes.",
        "prioridade": "Alta",
    },
]

PROVIDER_RUNTIME_BRIDGE_CODE = '"""Bridge runtime para integrar ProviderFactory ao backend local — Valoris.\n\nScaffold v3.8.74. Mantém hybrid como padrão seguro.\nSupabase/Postgres continuam placeholders enquanto não houver secrets e plano de rollback.\n"""\n\nfrom __future__ import annotations\n\nfrom typing import Any, Dict\n\nfrom app.services.provider_factory import build_database_provider, get_database_provider_name\n\n\nclass ProviderRuntimeBridge:\n    """Adaptador fino entre RepositoryBridge e DatabaseProvider selecionável."""\n\n    def __init__(self, repository_bridge: Any):\n        self.repository_bridge = repository_bridge\n        self.provider_name = get_database_provider_name()\n        self.provider = build_database_provider(repository_bridge)\n\n    def create_lead(self, payload: Any) -> Dict[str, Any]:\n        resultado = self.provider.create_lead(payload)\n        resultado["runtime_bridge"] = True\n        resultado["provider_name"] = self.provider_name\n        return resultado\n\n    def list_leads(self, limit: int = 100, source: str = "auto") -> Dict[str, Any]:\n        resultado = self.provider.list_leads(limit=limit, source=source)\n        resultado["runtime_bridge"] = True\n        resultado["provider_name"] = self.provider_name\n        return resultado\n\n    def create_event(self, payload: Any) -> Dict[str, Any]:\n        resultado = self.provider.create_event(payload)\n        resultado["runtime_bridge"] = True\n        resultado["provider_name"] = self.provider_name\n        return resultado\n\n    def storage_health(self) -> Dict[str, Any]:\n        resultado = self.provider.storage_health()\n        resultado["runtime_bridge"] = True\n        resultado["provider_name"] = self.provider_name\n        return resultado\n\n\ndef build_provider_runtime_bridge(repository_bridge: Any) -> ProviderRuntimeBridge:\n    return ProviderRuntimeBridge(repository_bridge)\n'
PROVIDER_BACKEND_PROBE_CODE = 'from __future__ import annotations\n\nimport json\nimport os\nimport sys\nfrom datetime import datetime\nfrom pathlib import Path\nfrom typing import Any, Dict\n\n\nROOT = Path(__file__).resolve().parents[1]\nAPI_ROOT = ROOT / "api_valoris"\n\nif str(API_ROOT) not in sys.path:\n    sys.path.insert(0, str(API_ROOT))\n\n\nclass DummyRepositoryBridge:\n    def create_lead(self, payload: Any) -> Dict[str, Any]:\n        return {"ok": True, "source": "dummy", "operation": "create_lead", "payload_type": type(payload).__name__}\n\n    def list_leads(self, limit: int = 100, source: str = "auto") -> Dict[str, Any]:\n        return {"ok": True, "source": source, "limit": limit, "count": 0, "leads": []}\n\n    def create_event(self, payload: Any) -> Dict[str, Any]:\n        return {"ok": True, "source": "dummy", "operation": "create_event", "payload_type": type(payload).__name__}\n\n    def storage_health(self) -> Dict[str, Any]:\n        return {"ok": True, "source": "dummy", "storage_mode": "hybrid"}\n\n\ndef testar_backend_provider(provider_name: str) -> Dict[str, Any]:\n    os.environ["VALORIS_DATABASE_PROVIDER"] = provider_name\n\n    from app.services.provider_factory import get_database_provider_name\n    from app.services.provider_runtime_bridge import build_provider_runtime_bridge\n\n    resolved_provider = get_database_provider_name()\n    bridge = build_provider_runtime_bridge(DummyRepositoryBridge())\n\n    resultado = {\n        "input": provider_name,\n        "resolved_provider": resolved_provider,\n        "bridge_class": bridge.__class__.__name__,\n        "provider_class": bridge.provider.__class__.__name__,\n        "provider_name": getattr(bridge.provider, "name", ""),\n        "health": None,\n        "list_leads": None,\n        "ok": False,\n        "erro": "",\n    }\n\n    try:\n        resultado["health"] = bridge.storage_health()\n\n        if provider_name in {"local_csv", "local_sqlite", "hybrid", "provider_invalido"}:\n            resultado["list_leads"] = bridge.list_leads(limit=5)\n            fallback_ok = provider_name != "provider_invalido" or resolved_provider == "hybrid"\n            resultado["ok"] = (\n                bool(resultado["health"].get("runtime_bridge"))\n                and bool(resultado["list_leads"].get("runtime_bridge"))\n                and getattr(bridge.provider, "name", "") == resolved_provider\n                and fallback_ok\n            )\n        elif provider_name in {"supabase", "postgres"}:\n            resultado["ok"] = (\n                bool(resultado["health"].get("runtime_bridge"))\n                and resultado["health"].get("ok") is False\n                and getattr(bridge.provider, "name", "") == provider_name\n            )\n        else:\n            resultado["ok"] = False\n\n    except Exception as erro:\n        resultado["erro"] = str(erro)\n        resultado["ok"] = False\n\n    return resultado\n\n\ndef main() -> int:\n    providers = ["local_csv", "local_sqlite", "hybrid", "supabase", "postgres", "provider_invalido"]\n    resultados = [testar_backend_provider(provider) for provider in providers]\n\n    relatorio = {\n        "versao": "3.8.74",\n        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),\n        "providers_testados": providers,\n        "ok": all(item["ok"] for item in resultados),\n        "resultados": resultados,\n    }\n\n    output_path = ROOT / "relatorio_provider_backend_valoris.json"\n    output_path.write_text(json.dumps(relatorio, ensure_ascii=False, indent=2), encoding="utf-8")\n\n    print(json.dumps(relatorio, ensure_ascii=False, indent=2))\n    return 0 if relatorio["ok"] else 1\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


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


def carregar_decisoes_provider_backend() -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_DECISOES_PROVIDER_BACKEND, CAMPOS_DECISAO_PROVIDER_BACKEND)
    with CAMINHO_DECISOES_PROVIDER_BACKEND.open("r", newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def gerar_csv_decisoes_provider_backend() -> str:
    _garantir_csv(CAMINHO_DECISOES_PROVIDER_BACKEND, CAMPOS_DECISAO_PROVIDER_BACKEND)
    return CAMINHO_DECISOES_PROVIDER_BACKEND.read_text(encoding="utf-8")


def salvar_decisao_provider_backend(decisao: Dict[str, Any]) -> Dict[str, str]:
    _garantir_csv(CAMINHO_DECISOES_PROVIDER_BACKEND, CAMPOS_DECISAO_PROVIDER_BACKEND)

    registro = {
        "id": str(uuid4())[:8],
        "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score_backend": str(decisao.get("score_backend", "")),
        "score_runtime": str(decisao.get("score_runtime", "")),
        "score_providers": str(decisao.get("score_providers", "")),
        "score_contracts": str(decisao.get("score_contracts", "")),
        "score_cloud": str(decisao.get("score_cloud", "")),
        "score_security": str(decisao.get("score_security", "")),
        "score_adapter": str(decisao.get("score_adapter", "")),
        "score_tests": str(decisao.get("score_tests", "")),
        "api_online": str(decisao.get("api_online", "")),
        "backend_probe_ok": str(decisao.get("backend_probe_ok", "")),
        "runtime_bridge_ok": str(decisao.get("runtime_bridge_ok", "")),
        "fallback_local_ok": str(decisao.get("fallback_local_ok", "")),
        "providers_testados": str(decisao.get("providers_testados", "")),
        "risco": _limpar_texto(decisao.get("risco", "")),
        "decisao": _limpar_texto(decisao.get("decisao", "")),
        "proximo_passo": _limpar_texto(decisao.get("proximo_passo", "")),
        "observacoes": _limpar_texto(decisao.get("observacoes", "")),
    }

    with CAMINHO_DECISOES_PROVIDER_BACKEND.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISAO_PROVIDER_BACKEND)
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


def gerar_provider_backend_bridge() -> Dict[str, Any]:
    CAMINHO_PROVIDER_RUNTIME_BRIDGE.parent.mkdir(parents=True, exist_ok=True)
    CAMINHO_PROVIDER_RUNTIME_BRIDGE.write_text(PROVIDER_RUNTIME_BRIDGE_CODE, encoding="utf-8")

    try:
        py_compile.compile(str(CAMINHO_PROVIDER_RUNTIME_BRIDGE), doraise=True)
        ok = True
        erro = ""
    except Exception as exc:
        ok = False
        erro = str(exc)

    return {
        "ok": ok,
        "arquivo": str(CAMINHO_PROVIDER_RUNTIME_BRIDGE),
        "erro": erro,
        "mensagem": "ProviderRuntimeBridge gerado para integração controlada ao backend local.",
    }


def gerar_provider_backend_probe() -> Dict[str, Any]:
    CAMINHO_PROVIDER_BACKEND_PROBE.parent.mkdir(parents=True, exist_ok=True)
    CAMINHO_PROVIDER_BACKEND_PROBE.write_text(PROVIDER_BACKEND_PROBE_CODE, encoding="utf-8")

    try:
        py_compile.compile(str(CAMINHO_PROVIDER_BACKEND_PROBE), doraise=True)
        ok = True
        erro = ""
    except Exception as exc:
        ok = False
        erro = str(exc)

    return {
        "ok": ok,
        "arquivo": str(CAMINHO_PROVIDER_BACKEND_PROBE),
        "erro": erro,
        "mensagem": "Probe backend gerado para testar a ponte ProviderFactory -> RepositoryBridge.",
    }


def executar_provider_backend_probe() -> Dict[str, Any]:
    if not CAMINHO_PROVIDER_RUNTIME_BRIDGE.exists():
        gerar_provider_backend_bridge()

    if not CAMINHO_PROVIDER_BACKEND_PROBE.exists():
        gerar_provider_backend_probe()

    comando = [sys.executable, str(CAMINHO_PROVIDER_BACKEND_PROBE)]
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
    if CAMINHO_PROVIDER_BACKEND_REPORT.exists():
        try:
            relatorio = json.loads(CAMINHO_PROVIDER_BACKEND_REPORT.read_text(encoding="utf-8"))
        except Exception:
            relatorio = {}

    return {
        "ok": processo.returncode == 0 and bool(relatorio.get("ok")),
        "returncode": processo.returncode,
        "stdout": stdout[-4000:],
        "stderr": stderr[-4000:],
        "relatorio": relatorio,
        "arquivo_relatorio": str(CAMINHO_PROVIDER_BACKEND_REPORT),
    }


def avaliar_provider_backend_scaffold() -> Dict[str, Any]:
    runtime_bridge_ok = _arquivo_contem(
        CAMINHO_PROVIDER_RUNTIME_BRIDGE,
        [
            "class ProviderRuntimeBridge",
            "build_provider_runtime_bridge",
            "build_database_provider",
            "get_database_provider_name",
            "runtime_bridge",
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
    database_providers_ok = _arquivo_contem(
        CAMINHO_DATABASE_PROVIDERS,
        [
            "class LocalCSVProvider",
            "class LocalSQLiteProvider",
            "class HybridProvider",
            "class SupabaseProvider",
            "class PostgresProvider",
        ],
    )

    runtime_compile_ok = False
    runtime_compile_error = ""

    if CAMINHO_PROVIDER_RUNTIME_BRIDGE.exists():
        try:
            py_compile.compile(str(CAMINHO_PROVIDER_RUNTIME_BRIDGE), doraise=True)
            runtime_compile_ok = True
        except Exception as erro:
            runtime_compile_error = str(erro)

    return {
        "runtime_bridge_file": str(CAMINHO_PROVIDER_RUNTIME_BRIDGE),
        "runtime_bridge_existe": CAMINHO_PROVIDER_RUNTIME_BRIDGE.exists(),
        "runtime_bridge_ok": runtime_bridge_ok,
        "runtime_compile_ok": runtime_compile_ok,
        "runtime_compile_error": runtime_compile_error,
        "factory_ok": factory_ok,
        "database_providers_ok": database_providers_ok,
        "ok": runtime_bridge_ok and runtime_compile_ok and factory_ok and database_providers_ok,
    }


def gerar_markdown_provider_backend(saude: Dict[str, Any] | None = None) -> str:
    if saude is None:
        saude = calcular_saude_provider_backend()

    regras = "\n".join(
        [
            f"- **{item['prioridade']}** — {item['regra']}: {item['motivo']}"
            for item in PROVIDER_BACKEND_RULES
        ]
    )

    providers = "\n".join([f"- `{provider}`" for provider in PROVIDERS_BACKEND_TESTADOS])

    return f"""# Provider Backend — Valoris

Versão: {VERSAO_API_PROVIDER_BACKEND_VALORIS}  
Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Diagnóstico

Score Backend: {saude["score_backend"]}/100  
Risco: {saude["risco"]}  
Decisão: {saude["decisao"]}  
Próximo passo: {saude["proximo_passo"]}

## Objetivo

Integrar de forma controlada a ProviderFactory ao backend local, sem reescrever rotas e sem abrir conexão real com Supabase/PostgreSQL.

## Providers testados

{providers}

## Regras

{regras}

## Arquivos gerados localmente

- `{CAMINHO_PROVIDER_RUNTIME_BRIDGE}`
- `{CAMINHO_PROVIDER_BACKEND_PROBE}`
- `{CAMINHO_PROVIDER_BACKEND_REPORT}`

## Segurança

SupabaseProvider e PostgresProvider continuam placeholders. A escolha padrão permanece `hybrid`.
"""


def salvar_provider_backend_markdown() -> Dict[str, Any]:
    saude = calcular_saude_provider_backend()
    CAMINHO_PROVIDER_BACKEND_MD.write_text(gerar_markdown_provider_backend(saude), encoding="utf-8")
    return {
        "ok": True,
        "arquivo": str(CAMINHO_PROVIDER_BACKEND_MD),
        "score_backend": saude["score_backend"],
        "decisao": saude["decisao"],
    }


def calcular_saude_provider_backend(executar_probe: bool = False) -> Dict[str, Any]:
    try:
        runtime = calcular_saude_provider_runtime()
    except Exception as erro:
        runtime = {"score_runtime": 0, "runtime_probe_ok": False, "erro": str(erro)}

    try:
        providers = calcular_saude_database_providers()
    except Exception as erro:
        providers = {"score_providers": 0, "scaffold_pronto": False, "erro": str(erro)}

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
    scaffold = avaliar_provider_backend_scaffold()

    if executar_probe:
        probe = executar_provider_backend_probe()
    elif CAMINHO_PROVIDER_BACKEND_REPORT.exists():
        try:
            relatorio = json.loads(CAMINHO_PROVIDER_BACKEND_REPORT.read_text(encoding="utf-8"))
        except Exception:
            relatorio = {}
        probe = {
            "ok": bool(relatorio.get("ok")),
            "returncode": 0 if relatorio.get("ok") else 1,
            "stdout": "",
            "stderr": "",
            "relatorio": relatorio,
            "arquivo_relatorio": str(CAMINHO_PROVIDER_BACKEND_REPORT),
        }
    else:
        probe = {"ok": False, "returncode": None, "stdout": "", "stderr": "", "relatorio": {}, "arquivo_relatorio": str(CAMINHO_PROVIDER_BACKEND_REPORT)}

    fallback_local_ok = CAMINHO_DB_LOCAL.exists() and CAMINHO_LEADS_CSV.exists() and CAMINHO_EVENTS_CSV.exists()
    repository_bridge_ok = _arquivo_contem(CAMINHO_REPOSITORY_BRIDGE, ["class RepositoryBridge", "storage_health"])
    gitignore_ok = (
        _gitignore_contem("api_valoris/app/services/provider_runtime_bridge.py")
        and _gitignore_contem("scripts_api_valoris/testar_provider_backend_valoris.py")
        and _gitignore_contem("relatorio_provider_backend_valoris.json")
        and _gitignore_contem("manifesto_api_provider_backend_valoris.json")
    )

    score_runtime = int(runtime.get("score_runtime", 0) or 0)
    score_providers = int(providers.get("score_providers", 0) or 0)
    score_contracts = int(contracts.get("score_contracts", 0) or 0)
    score_cloud = int(cloud.get("score_cloud", 0) or 0)
    score_security = int(security.get("score_security", 0) or 0)
    score_adapter = int(adapter.get("score_adapter", 0) or 0)
    score_tests = int(endpoint_tests.get("score_tests", 0) or 0)

    score = 10
    score += min(score_runtime * 0.14, 14)
    score += min(score_providers * 0.12, 12)
    score += min(score_contracts * 0.10, 10)
    score += min(score_cloud * 0.06, 6)
    score += min(score_security * 0.10, 10)
    score += min(score_adapter * 0.08, 8)
    score += min(score_tests * 0.06, 6)
    score += 8 if bool(health.get("health_ok")) else 0
    score += 10 if scaffold["ok"] else 0
    score += 10 if bool(probe.get("ok")) else 0
    score += 8 if fallback_local_ok else 0
    score += 4 if repository_bridge_ok else 0
    score += 4 if gitignore_ok else 0
    score = int(round(max(0, min(100, score))))

    security_ok = bool(security.get("protected_ok")) or bool(cloud.get("security_ok"))

    if not security_ok:
        risco = "Alto"
        decisao = "Não integrar provider ao backend ainda"
        proximo_passo = "Validar segurança antes de ampliar o uso da factory."
    elif not scaffold["ok"]:
        risco = "Médio/alto"
        decisao = "ProviderRuntimeBridge incompleto"
        proximo_passo = "Gerar bridge e probe backend."
    elif not probe.get("ok"):
        risco = "Médio"
        decisao = "Probe backend pendente"
        proximo_passo = "Executar o probe backend pelo terminal."
    elif score >= 84:
        risco = "Médio controlado"
        decisao = "Integração controlada aprovada"
        proximo_passo = "Avançar para conexão Supabase experimental opcional, com secrets fora do Git."
    else:
        risco = "Médio"
        decisao = "Backend provider em progresso"
        proximo_passo = "Gerar manifesto, markdown e decisão."

    return {
        "score_backend": score,
        "score_runtime": score_runtime,
        "score_providers": score_providers,
        "score_contracts": score_contracts,
        "score_cloud": score_cloud,
        "score_security": score_security,
        "score_adapter": score_adapter,
        "score_tests": score_tests,
        "api_online": bool(health.get("health_ok")),
        "backend_probe_ok": bool(probe.get("ok")),
        "runtime_bridge_ok": scaffold["runtime_bridge_ok"],
        "fallback_local_ok": fallback_local_ok,
        "scaffold_ok": scaffold["ok"],
        "providers_testados": len(PROVIDERS_BACKEND_TESTADOS),
        "security_ok": security_ok,
        "repository_bridge_ok": repository_bridge_ok,
        "gitignore_ok": gitignore_ok,
        "health": health,
        "runtime": runtime,
        "providers": providers,
        "contracts": contracts,
        "cloud": cloud,
        "security": security,
        "adapter": adapter,
        "endpoint_tests": endpoint_tests,
        "scaffold": scaffold,
        "probe": probe,
        "rules": PROVIDER_BACKEND_RULES,
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo_passo,
    }


def gerar_manifesto_provider_backend(executar_probe: bool = False) -> Dict[str, Any]:
    saude = calcular_saude_provider_backend(executar_probe=executar_probe)
    manifesto = {
        "versao": VERSAO_API_PROVIDER_BACKEND_VALORIS,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "saude": saude,
        "providers_testados": PROVIDERS_BACKEND_TESTADOS,
        "backend_rules": PROVIDER_BACKEND_RULES,
        "estrategia": {
            "agora": "Integrar ProviderFactory ao backend local por bridge controlada.",
            "proxima_versao": "Preparar conexão Supabase experimental opcional com secrets fora do Git.",
            "regra": "hybrid permanece padrão seguro e fallback obrigatório.",
        },
    }
    CAMINHO_MANIFESTO_PROVIDER_BACKEND.write_text(json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifesto


def _injetar_css_provider_backend() -> None:
    st.markdown(
        """
        <style>
            .provider-backend-hero {
                padding: clamp(1.2rem, 3vw, 2.05rem);
                border-radius: 30px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    radial-gradient(circle at top left, rgba(214, 181, 109, 0.20), transparent 32%),
                    radial-gradient(circle at bottom right, rgba(80, 170, 140, 0.20), transparent 36%),
                    linear-gradient(135deg, rgba(6, 12, 23, 0.99), rgba(4, 8, 16, 0.99));
                box-shadow: 0 20px 62px rgba(0, 0, 0, 0.34);
                margin-bottom: 1rem;
            }
            .provider-backend-eyebrow { color: #d6b56d; font-size: 0.74rem; letter-spacing: 0.14em; text-transform: uppercase; font-weight: 880; margin-bottom: 0.35rem; }
            .provider-backend-title { color: #f4f7fb; font-size: clamp(1.8rem, 5.5vw, 3.2rem); font-weight: 950; line-height: 1.02; letter-spacing: -0.058em; margin-bottom: 0.55rem; }
            .provider-backend-subtitle { color: rgba(244, 247, 251, 0.75); font-size: clamp(0.94rem, 2.2vw, 1.06rem); line-height: 1.56; max-width: 1050px; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def renderizar_api_provider_backend_valoris() -> None:
    _injetar_css_provider_backend()
    st.markdown(
        f"""
        <div class="provider-backend-hero">
            <div class="provider-backend-eyebrow">Valoris • Provider Backend • v{VERSAO_API_PROVIDER_BACKEND_VALORIS}</div>
            <div class="provider-backend-title">ProviderFactory integrada por bridge controlada.</div>
            <div class="provider-backend-subtitle">
                Ponte técnica entre RepositoryBridge e providers selecionáveis, sem conexão externa real.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    saude = calcular_saude_provider_backend()

    st.markdown("### Diagnóstico backend provider")
    col_1, col_2, col_3, col_4 = st.columns(4)
    with col_1:
        st.metric("Score Backend", f"{saude['score_backend']}/100")
    with col_2:
        st.metric("Risco", saude["risco"])
    with col_3:
        st.metric("Probe", "OK" if saude["backend_probe_ok"] else "Pendente")
    with col_4:
        st.metric("Bridge", "OK" if saude["runtime_bridge_ok"] else "Pendente")

    st.progress(saude["score_backend"] / 100)

    if saude["score_backend"] >= 84 and saude["backend_probe_ok"]:
        st.success(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    elif saude["score_backend"] >= 60:
        st.warning(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    else:
        st.info(f"**{saude['decisao']}** — {saude['proximo_passo']}")

    st.divider()
    st.markdown("### Providers testados")
    st.dataframe([{"provider": item} for item in PROVIDERS_BACKEND_TESTADOS], width="stretch", hide_index=True)

    st.markdown("### Regras de integração")
    st.dataframe(PROVIDER_BACKEND_RULES, width="stretch", hide_index=True)

    st.divider()
    col_btn_1, col_btn_2, col_btn_3, col_btn_4 = st.columns(4)

    with col_btn_1:
        if st.button("Gerar runtime bridge", key="provider_backend_bridge"):
            resultado = gerar_provider_backend_bridge()
            st.success(resultado["mensagem"] if resultado["ok"] else "Bridge gerada com erro de compilação.")
            st.json(resultado)

    with col_btn_2:
        if st.button("Gerar probe backend", key="provider_backend_probe"):
            resultado = gerar_provider_backend_probe()
            st.success(resultado["mensagem"] if resultado["ok"] else "Probe gerado com erro de compilação.")
            st.json(resultado)

    with col_btn_3:
        if st.button("Executar probe backend", key="provider_backend_run_probe"):
            resultado = executar_provider_backend_probe()
            st.success("Probe backend aprovado." if resultado["ok"] else "Probe backend falhou.")
            st.json({"ok": resultado["ok"], "returncode": resultado["returncode"], "arquivo_relatorio": resultado["arquivo_relatorio"], "stderr": resultado["stderr"]})

    with col_btn_4:
        if st.button("Gerar manifesto Backend", key="provider_backend_manifesto"):
            manifesto = gerar_manifesto_provider_backend(executar_probe=False)
            st.success(f"Manifesto gerado: {CAMINHO_MANIFESTO_PROVIDER_BACKEND}")
            st.json({"versao": manifesto["versao"], "score_backend": manifesto["saude"]["score_backend"], "decisao": manifesto["saude"]["decisao"]})

    if st.button("Salvar Provider Backend .md", key="provider_backend_md"):
        resultado = salvar_provider_backend_markdown()
        st.success(f"Markdown salvo: {resultado['arquivo']}")
        st.json(resultado)

    if st.button("Salvar decisão Backend", key="provider_backend_decisao"):
        registro = salvar_decisao_provider_backend(
            {
                "score_backend": saude["score_backend"],
                "score_runtime": saude["score_runtime"],
                "score_providers": saude["score_providers"],
                "score_contracts": saude["score_contracts"],
                "score_cloud": saude["score_cloud"],
                "score_security": saude["score_security"],
                "score_adapter": saude["score_adapter"],
                "score_tests": saude["score_tests"],
                "api_online": saude["api_online"],
                "backend_probe_ok": saude["backend_probe_ok"],
                "runtime_bridge_ok": saude["runtime_bridge_ok"],
                "fallback_local_ok": saude["fallback_local_ok"],
                "providers_testados": saude["providers_testados"],
                "risco": saude["risco"],
                "decisao": saude["decisao"],
                "proximo_passo": saude["proximo_passo"],
                "observacoes": "Decisão gerada pela integração controlada da ProviderFactory.",
            }
        )
        st.success(f"Decisão salva: {registro['decisao']}")
        st.rerun()

    st.download_button("Baixar Provider Backend (.md)", data=gerar_markdown_provider_backend(saude), file_name="PROVIDER_BACKEND_VALORIS.md", mime="text/markdown", key="download_provider_backend_md")
    st.download_button("Baixar decisões Backend (.csv)", data=gerar_csv_decisoes_provider_backend(), file_name="decisoes_api_provider_backend_valoris.csv", mime="text/csv", key="download_decisoes_provider_backend")

    st.divider()
    st.markdown("### Resumo técnico")
    st.json(
        {
            "score_backend": saude["score_backend"],
            "risco": saude["risco"],
            "decisao": saude["decisao"],
            "proximo_passo": saude["proximo_passo"],
            "backend_probe_ok": saude["backend_probe_ok"],
            "runtime_bridge_ok": saude["runtime_bridge_ok"],
            "fallback_local_ok": saude["fallback_local_ok"],
            "scaffold_ok": saude["scaffold_ok"],
            "repository_bridge_ok": saude["repository_bridge_ok"],
            "gitignore_ok": saude["gitignore_ok"],
        }
    )


def executar_autoteste_api_provider_backend_valoris() -> List[Dict[str, str]]:
    saude = calcular_saude_provider_backend(executar_probe=False)
    return [
        {"teste": "versao_provider_backend", "status": "OK" if VERSAO_API_PROVIDER_BACKEND_VALORIS == "3.8.74" else "FALHA", "detalhe": VERSAO_API_PROVIDER_BACKEND_VALORIS},
        {"teste": "score_backend", "status": "OK" if 0 <= saude["score_backend"] <= 100 else "FALHA", "detalhe": str(saude["score_backend"])},
        {"teste": "renderizador", "status": "OK" if callable(renderizar_api_provider_backend_valoris) else "FALHA", "detalhe": "renderizar_api_provider_backend_valoris"},
    ]
