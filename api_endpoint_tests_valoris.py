# api_endpoint_tests_valoris.py

from __future__ import annotations

import csv
import json
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

import streamlit as st

from api_repository_bridge_valoris import calcular_saude_api_bridge
from api_smoke_tests_valoris import (
    URL_API_LOCAL,
    testar_health_api,
)


# ============================================================
# VALORIS
# v3.8.65 — Testes Automatizados da API e Qualidade dos Endpoints
# ------------------------------------------------------------
# Esta etapa transforma a API local em algo testável.
#
# Objetivo:
# - testar GET /health;
# - testar POST /leads;
# - testar GET /leads;
# - testar POST /events;
# - testar payload inválido em /leads;
# - confirmar gravação em CSV real;
# - gerar scripts locais de teste;
# - salvar manifesto e decisão de qualidade.
# ============================================================


VERSAO_API_ENDPOINT_TESTS_VALORIS = "3.8.65"

CAMINHO_DECISOES_API_TESTS = Path("decisoes_api_tests_valoris.csv")
CAMINHO_MANIFESTO_API_TESTS = Path("manifesto_api_tests_valoris.json")
CAMINHO_RELATORIO_API_TESTS = Path("relatorio_api_tests_valoris.json")

API_KEY_HEADER_NAME = "X-Valoris-API-Key"
DEFAULT_LOCAL_API_KEY = "valoris-local-dev-key"

PASTA_SCRIPTS_API = Path("scripts_api_valoris")
CAMINHO_SCRIPT_ENDPOINTS_PS1 = PASTA_SCRIPTS_API / "testar_endpoints_api_valoris.ps1"
CAMINHO_SCRIPT_ENDPOINTS_PY = PASTA_SCRIPTS_API / "testar_endpoints_api_valoris.py"

CAMINHO_LEADS_CSV = Path("lista_espera_beta.csv")
CAMINHO_EVENTS_CSV = Path("eventos_publicos_valoris.csv")

CAMPOS_DECISAO_API_TESTS = [
    "id",
    "data_registro",
    "score_tests",
    "api_rodando",
    "health_ok",
    "testes_ok",
    "testes_total",
    "decisao",
    "proximo_passo",
    "observacoes",
]

SCRIPT_ENDPOINTS_PY = 'from __future__ import annotations\n\nimport json\nimport sys\nimport urllib.error\nimport urllib.request\nfrom datetime import datetime\nfrom pathlib import Path\nfrom uuid import uuid4\n\n\nAPI_URL = "http://127.0.0.1:8000"\nLEADS_CSV = Path("lista_espera_beta.csv").resolve()\nEVENTS_CSV = Path("eventos_publicos_valoris.csv").resolve()\n\n\ndef request_json(method: str, path: str, payload: dict | None = None, timeout: float = 4.0, api_key: str | None = None) -> dict:\n    url = API_URL + path\n    data = None\n    headers = {"Content-Type": "application/json"}\n\n    if payload is not None:\n        data = json.dumps(payload).encode("utf-8")\n\n    req = urllib.request.Request(url, data=data, headers=headers, method=method)\n\n    try:\n        with urllib.request.urlopen(req, timeout=timeout) as res:\n            body = res.read().decode("utf-8", errors="ignore")\n            return {\n                "ok": 200 <= res.status < 300,\n                "status_code": res.status,\n                "data": json.loads(body) if body else {},\n                "error": "",\n            }\n    except urllib.error.HTTPError as err:\n        body = err.read().decode("utf-8", errors="ignore")\n        try:\n            parsed = json.loads(body) if body else {}\n        except Exception:\n            parsed = {"raw": body}\n\n        return {\n            "ok": False,\n            "status_code": err.code,\n            "data": parsed,\n            "error": str(err),\n        }\n    except Exception as err:\n        return {\n            "ok": False,\n            "status_code": None,\n            "data": {},\n            "error": str(err),\n        }\n\n\ndef file_contains(path: Path, text: str) -> bool:\n    if not path.exists():\n        return False\n    return text in path.read_text(encoding="utf-8", errors="ignore")\n\n\ndef main() -> int:\n    unique = str(uuid4())[:8]\n    contato = f"qa+{unique}@valoris.local"\n    evento_nome = f"api_endpoint_test_{unique}"\n\n    tests = []\n\n    health = request_json("GET", "/health")\n    tests.append({\n        "teste": "GET /health",\n        "ok": health["ok"] and health["data"].get("status") == "ok",\n        "status_code": health["status_code"],\n        "detalhe": health,\n    })\n\n    lead_payload = {\n        "nome": f"Lead QA {unique}",\n        "contato": contato,\n        "perfil": "qa",\n        "principal_dor": "validar endpoint",\n        "plano_interesse": "beta",\n        "preco_aceitavel": "teste",\n        "pagaria_agora": "nao",\n        "comentario": "teste automatizado v3.8.65",\n    }\n\n    post_lead = request_json("POST", "/leads", lead_payload)\n    tests.append({\n        "teste": "POST /leads",\n        "ok": post_lead["ok"] and post_lead["data"].get("ok") is True,\n        "status_code": post_lead["status_code"],\n        "detalhe": post_lead,\n    })\n\n    get_leads = request_json("GET", "/leads", api_key=DEFAULT_LOCAL_API_KEY)\n    leads_payload = json.dumps(get_leads["data"], ensure_ascii=False)\n    tests.append({\n        "teste": "GET /leads encontra lead criado",\n        "ok": get_leads["ok"] and contato in leads_payload,\n        "status_code": get_leads["status_code"],\n        "detalhe": {"contato": contato},\n    })\n\n    tests.append({\n        "teste": "CSV lista_espera_beta contém lead",\n        "ok": file_contains(LEADS_CSV, contato),\n        "status_code": None,\n        "detalhe": {"arquivo": str(LEADS_CSV), "contato": contato},\n    })\n\n    event_payload = {\n        "sessao_id": unique,\n        "evento": evento_nome,\n        "origem": "api-tests",\n        "contexto": "v3.8.65",\n        "perfil": "qa",\n        "valor": "1",\n        "detalhe": "teste automatizado de evento",\n    }\n\n    post_event = request_json("POST", "/events", event_payload, api_key=DEFAULT_LOCAL_API_KEY)\n    tests.append({\n        "teste": "POST /events",\n        "ok": post_event["ok"] and post_event["data"].get("ok") is True,\n        "status_code": post_event["status_code"],\n        "detalhe": post_event,\n    })\n\n    tests.append({\n        "teste": "CSV eventos_publicos_valoris contém evento",\n        "ok": file_contains(EVENTS_CSV, evento_nome),\n        "status_code": None,\n        "detalhe": {"arquivo": str(EVENTS_CSV), "evento": evento_nome},\n    })\n\n    invalid = request_json("POST", "/leads", {"nome": "Payload Inválido"})\n    tests.append({\n        "teste": "POST /leads inválido retorna erro 422",\n        "ok": invalid["status_code"] == 422,\n        "status_code": invalid["status_code"],\n        "detalhe": invalid,\n    })\n\n    ok_count = len([test for test in tests if test["ok"]])\n    total = len(tests)\n\n    summary = {\n        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),\n        "ok": ok_count == total,\n        "ok_count": ok_count,\n        "total": total,\n        "tests": tests,\n    }\n\n    print(json.dumps(summary, ensure_ascii=False, indent=2))\n    return 0 if summary["ok"] else 1\n\n\nif __name__ == "__main__":\n    sys.exit(main())'
SCRIPT_ENDPOINTS_PS1 = '# Testes de endpoints da API Valoris\n# Pré-requisito: API rodando em outro terminal.\n# Execute na raiz do projeto:\n# .\\scripts_api_valoris\\testar_endpoints_api_valoris.ps1\n\nSet-Location "$PSScriptRoot\\.."\n\nif (!(Test-Path ".\\scripts_api_valoris\\testar_endpoints_api_valoris.py")) {\n    Write-Host "Script Python de testes não encontrado. Gere novamente pela aba API Tests." -ForegroundColor Red\n    exit 1\n}\n\npython .\\scripts_api_valoris\\testar_endpoints_api_valoris.py'


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


def carregar_decisoes_api_tests() -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_DECISOES_API_TESTS, CAMPOS_DECISAO_API_TESTS)

    with CAMINHO_DECISOES_API_TESTS.open("r", newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def gerar_csv_decisoes_api_tests() -> str:
    _garantir_csv(CAMINHO_DECISOES_API_TESTS, CAMPOS_DECISAO_API_TESTS)
    return CAMINHO_DECISOES_API_TESTS.read_text(encoding="utf-8")


def salvar_decisao_api_tests(decisao: Dict[str, Any]) -> Dict[str, str]:
    _garantir_csv(CAMINHO_DECISOES_API_TESTS, CAMPOS_DECISAO_API_TESTS)

    registro = {
        "id": str(uuid4())[:8],
        "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score_tests": str(decisao.get("score_tests", "")),
        "api_rodando": str(decisao.get("api_rodando", "")),
        "health_ok": str(decisao.get("health_ok", "")),
        "testes_ok": str(decisao.get("testes_ok", "")),
        "testes_total": str(decisao.get("testes_total", "")),
        "decisao": _limpar_texto(decisao.get("decisao", "")),
        "proximo_passo": _limpar_texto(decisao.get("proximo_passo", "")),
        "observacoes": _limpar_texto(decisao.get("observacoes", "")),
    }

    with CAMINHO_DECISOES_API_TESTS.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISAO_API_TESTS)
        escritor.writerow(registro)

    return registro


def _request_json(
    method: str,
    path: str,
    payload: Dict[str, Any] | None = None,
    timeout: float = 4.0,
    api_key: str | None = None,
) -> Dict[str, Any]:
    url = URL_API_LOCAL + path
    data = None
    headers = {"Content-Type": "application/json"}

    if api_key is not None:
        headers[API_KEY_HEADER_NAME] = api_key

    if payload is not None:
        data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(request, timeout=timeout) as resposta:
            corpo = resposta.read().decode("utf-8", errors="ignore")
            return {
                "ok": 200 <= resposta.status < 300,
                "status_code": resposta.status,
                "data": json.loads(corpo) if corpo else {},
                "error": "",
            }

    except urllib.error.HTTPError as erro:
        corpo = erro.read().decode("utf-8", errors="ignore")

        try:
            parsed = json.loads(corpo) if corpo else {}
        except Exception:
            parsed = {"raw": corpo}

        return {
            "ok": False,
            "status_code": erro.code,
            "data": parsed,
            "error": str(erro),
        }

    except Exception as erro:
        return {
            "ok": False,
            "status_code": None,
            "data": {},
            "error": str(erro),
        }


def _arquivo_contem(caminho: Path, texto: str) -> bool:
    if not caminho.exists():
        return False

    return texto in caminho.read_text(encoding="utf-8", errors="ignore")


def executar_suite_endpoint_tests() -> Dict[str, Any]:
    identificador = str(uuid4())[:8]
    contato = f"qa+{identificador}@valoris.local"
    evento_nome = f"api_endpoint_test_{identificador}"

    testes: List[Dict[str, Any]] = []

    health = _request_json("GET", "/health")
    testes.append(
        {
            "teste": "GET /health",
            "ok": health["ok"] and health["data"].get("status") == "ok",
            "status_code": health["status_code"],
            "detalhe": health,
        }
    )

    lead_payload = {
        "nome": f"Lead QA {identificador}",
        "contato": contato,
        "perfil": "qa",
        "principal_dor": "validar endpoint",
        "plano_interesse": "beta",
        "preco_aceitavel": "teste",
        "pagaria_agora": "nao",
        "comentario": "teste automatizado v3.8.65",
    }

    post_lead = _request_json("POST", "/leads", lead_payload)
    testes.append(
        {
            "teste": "POST /leads",
            "ok": post_lead["ok"] and post_lead["data"].get("ok") is True,
            "status_code": post_lead["status_code"],
            "detalhe": post_lead,
        }
    )

    get_leads = _request_json("GET", "/leads", api_key=DEFAULT_LOCAL_API_KEY)
    payload_leads = json.dumps(get_leads["data"], ensure_ascii=False)
    testes.append(
        {
            "teste": "GET /leads encontra lead criado",
            "ok": get_leads["ok"] and contato in payload_leads,
            "status_code": get_leads["status_code"],
            "detalhe": {"contato": contato},
        }
    )

    testes.append(
        {
            "teste": "CSV lista_espera_beta contém lead",
            "ok": _arquivo_contem(CAMINHO_LEADS_CSV, contato),
            "status_code": None,
            "detalhe": {"arquivo": str(CAMINHO_LEADS_CSV), "contato": contato},
        }
    )

    event_payload = {
        "sessao_id": identificador,
        "evento": evento_nome,
        "origem": "api-tests",
        "contexto": "v3.8.65",
        "perfil": "qa",
        "valor": "1",
        "detalhe": "teste automatizado de evento",
    }

    post_event = _request_json("POST", "/events", event_payload, api_key=DEFAULT_LOCAL_API_KEY)
    testes.append(
        {
            "teste": "POST /events",
            "ok": post_event["ok"] and post_event["data"].get("ok") is True,
            "status_code": post_event["status_code"],
            "detalhe": post_event,
        }
    )

    testes.append(
        {
            "teste": "CSV eventos_publicos_valoris contém evento",
            "ok": _arquivo_contem(CAMINHO_EVENTS_CSV, evento_nome),
            "status_code": None,
            "detalhe": {"arquivo": str(CAMINHO_EVENTS_CSV), "evento": evento_nome},
        }
    )

    invalid = _request_json("POST", "/leads", {"nome": "Payload Inválido"})
    testes.append(
        {
            "teste": "POST /leads inválido retorna erro 422",
            "ok": invalid["status_code"] == 422,
            "status_code": invalid["status_code"],
            "detalhe": invalid,
        }
    )

    total = len(testes)
    ok_count = len([teste for teste in testes if teste["ok"]])

    resultado = {
        "versao": VERSAO_API_ENDPOINT_TESTS_VALORIS,
        "executado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ok": ok_count == total,
        "ok_count": ok_count,
        "total": total,
        "contato_teste": contato,
        "evento_teste": evento_nome,
        "testes": testes,
    }

    CAMINHO_RELATORIO_API_TESTS.write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return resultado


def gerar_scripts_endpoint_tests() -> Dict[str, Any]:
    PASTA_SCRIPTS_API.mkdir(parents=True, exist_ok=True)
    CAMINHO_SCRIPT_ENDPOINTS_PY.write_text(SCRIPT_ENDPOINTS_PY + "\n", encoding="utf-8")
    CAMINHO_SCRIPT_ENDPOINTS_PS1.write_text(SCRIPT_ENDPOINTS_PS1 + "\n", encoding="utf-8")

    return {
        "pasta": str(PASTA_SCRIPTS_API),
        "scripts": [
            str(CAMINHO_SCRIPT_ENDPOINTS_PY),
            str(CAMINHO_SCRIPT_ENDPOINTS_PS1),
        ],
    }


def calcular_saude_api_endpoint_tests() -> Dict[str, Any]:
    health = testar_health_api()

    try:
        bridge = calcular_saude_api_bridge()
    except Exception:
        bridge = {"score_bridge": 0, "health_ok": False}

    scripts_existentes = [
        CAMINHO_SCRIPT_ENDPOINTS_PY.exists(),
        CAMINHO_SCRIPT_ENDPOINTS_PS1.exists(),
    ]

    relatorio_existe = CAMINHO_RELATORIO_API_TESTS.exists()
    ultimo_relatorio: Dict[str, Any] = {}

    if relatorio_existe:
        try:
            ultimo_relatorio = json.loads(CAMINHO_RELATORIO_API_TESTS.read_text(encoding="utf-8"))
        except Exception:
            ultimo_relatorio = {}

    testes_ok = int(ultimo_relatorio.get("ok_count", 0) or 0)
    testes_total = int(ultimo_relatorio.get("total", 0) or 0)
    ultima_suite_ok = bool(ultimo_relatorio.get("ok", False))

    score_bridge = int(bridge.get("score_bridge", 0) or 0)

    score = 12
    score += 16 if health["health_ok"] else 0
    score += min(score_bridge * 0.22, 22)
    score += len([item for item in scripts_existentes if item]) * 8
    score += 30 if ultima_suite_ok else min(testes_ok * 4, 24)
    score += 12 if CAMINHO_LEADS_CSV.exists() else 0
    score += 8 if CAMINHO_EVENTS_CSV.exists() else 0
    score = int(round(max(0, min(100, score))))

    if score >= 85 and ultima_suite_ok:
        decisao = "API aprovada nos testes automatizados"
        proximo_passo = "Avançar para bridge API → SQLite sem quebrar contratos atuais."
    elif score >= 70 and health["health_ok"]:
        decisao = "API pronta para executar suite completa"
        proximo_passo = "Execute a suite de endpoints e confirme POST /events, POST /leads e GET /leads."
    elif score >= 50:
        decisao = "API parcialmente testável"
        proximo_passo = "Rode a API local e gere os scripts de teste antes de avançar."
    else:
        decisao = "API ainda não validada"
        proximo_passo = "Rode a API local e execute os testes automatizados."

    return {
        "score_tests": score,
        "health": health,
        "api_rodando": health["api_rodando"],
        "health_ok": health["health_ok"],
        "score_bridge": score_bridge,
        "scripts_ok": all(scripts_existentes),
        "relatorio_existe": relatorio_existe,
        "ultima_suite_ok": ultima_suite_ok,
        "testes_ok": testes_ok,
        "testes_total": testes_total,
        "ultimo_relatorio": ultimo_relatorio,
        "decisao": decisao,
        "proximo_passo": proximo_passo,
    }


def gerar_manifesto_api_tests() -> Dict[str, Any]:
    saude = calcular_saude_api_endpoint_tests()

    manifesto = {
        "versao": VERSAO_API_ENDPOINT_TESTS_VALORIS,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "saude": saude,
        "endpoints_testados": [
            "GET /health",
            "POST /leads",
            "GET /leads",
            "POST /events",
            "POST /leads inválido",
        ],
        "arquivos_de_dados": [
            str(CAMINHO_LEADS_CSV),
            str(CAMINHO_EVENTS_CSV),
        ],
        "scripts": [
            str(CAMINHO_SCRIPT_ENDPOINTS_PY),
            str(CAMINHO_SCRIPT_ENDPOINTS_PS1),
        ],
    }

    CAMINHO_MANIFESTO_API_TESTS.write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return manifesto


def _gerar_markdown_api_tests(saude: Dict[str, Any]) -> str:
    ultimo = saude.get("ultimo_relatorio", {})
    testes = ultimo.get("testes", [])

    linhas_testes = "\n".join(
        [
            f"- {'✅' if item.get('ok') else '❌'} {item.get('teste')} — status: {item.get('status_code')}"
            for item in testes
        ]
    ) or "- Nenhuma suite executada ainda."

    return f"""# Testes Automatizados da API — Valoris

Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Diagnóstico

Score Tests: {saude["score_tests"]}/100  
Decisão: {saude["decisao"]}  
Próximo passo: {saude["proximo_passo"]}

API rodando: {saude["api_rodando"]}  
Health OK: {saude["health_ok"]}  
Score Bridge: {saude["score_bridge"]}/100  
Scripts OK: {saude["scripts_ok"]}  
Última suite OK: {saude["ultima_suite_ok"]}  
Testes OK: {saude["testes_ok"]}/{saude["testes_total"]}  

## Testes da última suite

{linhas_testes}

## Endpoints cobertos

- `GET /health`
- `POST /leads`
- `GET /leads`
- `POST /events`
- `POST /leads` inválido esperando `422`

## Rodar por script

Com a API ligada:

```powershell
.\\scripts_api_valoris\\testar_endpoints_api_valoris.ps1
```

## Regra

Não avançar para SQLite/PostgreSQL enquanto os endpoints básicos não estiverem previsíveis.
"""


def _injetar_css_tests() -> None:
    st.markdown(
        """
        <style>
            .tests-hero {
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

            .tests-eyebrow {
                color: #d6b56d;
                font-size: 0.74rem;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                font-weight: 880;
                margin-bottom: 0.35rem;
            }

            .tests-title {
                color: #f4f7fb;
                font-size: clamp(1.75rem, 5.4vw, 3.1rem);
                font-weight: 950;
                line-height: 1.02;
                letter-spacing: -0.058em;
                margin-bottom: 0.55rem;
            }

            .tests-subtitle {
                color: rgba(244, 247, 251, 0.75);
                font-size: clamp(0.94rem, 2.2vw, 1.06rem);
                line-height: 1.56;
                max-width: 1020px;
            }

            .tests-note {
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
        <div class="tests-hero">
            <div class="tests-eyebrow">Valoris • API Tests • v{VERSAO_API_ENDPOINT_TESTS_VALORIS}</div>
            <div class="tests-title">Transforme a API em algo confiável.</div>
            <div class="tests-subtitle">
                Esta etapa executa testes reais nos endpoints, confirma gravação em CSV
                e evita avançar para banco externo com uma API instável.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _renderizar_metricas(saude: Dict[str, Any]) -> None:
    st.markdown("### Diagnóstico dos testes")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Score Tests", f"{saude['score_tests']}/100")

    with col_2:
        st.metric("Health", "OK" if saude["health_ok"] else "Offline")

    with col_3:
        st.metric("Última suite", "OK" if saude["ultima_suite_ok"] else "Pendente")

    with col_4:
        st.metric("Testes", f"{saude['testes_ok']}/{saude['testes_total']}")

    st.progress(saude["score_tests"] / 100)

    if saude["score_tests"] >= 85:
        st.success(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    elif saude["score_tests"] >= 50:
        st.warning(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    else:
        st.info(f"**{saude['decisao']}** — {saude['proximo_passo']}")


def _renderizar_resultado_suite(resultado: Dict[str, Any]) -> None:
    st.markdown("### Resultado da suite")

    if not resultado:
        st.info("Nenhuma suite executada nesta sessão.")
        return

    if resultado.get("ok"):
        st.success(f"Suite aprovada: {resultado.get('ok_count')}/{resultado.get('total')} testes.")
    else:
        st.warning(f"Suite com falhas: {resultado.get('ok_count')}/{resultado.get('total')} testes.")

    for item in resultado.get("testes", []):
        with st.container(border=True):
            st.markdown(f"**{'✅' if item.get('ok') else '❌'} {item.get('teste')}**")
            st.caption(f"Status code: {item.get('status_code')}")
            with st.expander("Detalhes", expanded=False):
                st.json(item.get("detalhe", {}))


def _renderizar_historico() -> None:
    historico = carregar_decisoes_api_tests()

    st.markdown("### Histórico de decisões API Tests")

    if not historico:
        st.info("Ainda não há decisões salvas.")
        return

    for item in reversed(historico[-10:]):
        with st.container(border=True):
            st.markdown(f"**{item.get('decisao', 'N/D')}**")
            st.caption(item.get("data_registro", "N/D"))
            st.markdown(f"Score: {item.get('score_tests', 'N/D')}/100")
            st.markdown(f"Testes: {item.get('testes_ok', 'N/D')}/{item.get('testes_total', 'N/D')}")
            st.markdown(f"Próximo passo: {item.get('proximo_passo', 'N/D')}")


def renderizar_api_endpoint_tests_valoris() -> None:
    _injetar_css_tests()
    _renderizar_hero()

    saude = calcular_saude_api_endpoint_tests()
    _renderizar_metricas(saude)

    st.divider()

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        if st.button("Executar suite de endpoints", key="executar_suite_api_endpoints"):
            resultado = executar_suite_endpoint_tests()
            st.session_state["resultado_api_endpoint_tests"] = resultado
            if resultado["ok"]:
                st.success("Suite de endpoints aprovada.")
            else:
                st.warning("Suite executada com falhas.")
            st.rerun()

    with col_2:
        if st.button("Gerar scripts de teste", key="gerar_scripts_endpoint_tests"):
            resultado = gerar_scripts_endpoint_tests()
            st.success(f"Scripts gerados em {resultado['pasta']}")
            st.json(resultado)

    with col_3:
        if st.button("Gerar manifesto Tests", key="gerar_manifesto_api_tests"):
            manifesto = gerar_manifesto_api_tests()
            st.success(f"Manifesto gerado: {CAMINHO_MANIFESTO_API_TESTS}")
            st.json(
                {
                    "versao": manifesto["versao"],
                    "score": manifesto["saude"]["score_tests"],
                    "health_ok": manifesto["saude"]["health_ok"],
                }
            )

    with col_4:
        if st.button("Salvar decisão Tests", key="salvar_decisao_api_tests"):
            registro = salvar_decisao_api_tests(
                {
                    "score_tests": saude["score_tests"],
                    "api_rodando": saude["api_rodando"],
                    "health_ok": saude["health_ok"],
                    "testes_ok": saude["testes_ok"],
                    "testes_total": saude["testes_total"],
                    "decisao": saude["decisao"],
                    "proximo_passo": saude["proximo_passo"],
                    "observacoes": "Decisão gerada pelos testes automatizados da API.",
                }
            )
            st.success(f"Decisão salva: {registro['decisao']}")
            st.rerun()

    st.download_button(
        "Baixar diagnóstico API Tests (.md)",
        data=_gerar_markdown_api_tests(saude),
        file_name="api_endpoint_tests_valoris.md",
        mime="text/markdown",
        key="download_api_endpoint_tests",
    )

    st.download_button(
        "Baixar decisões API Tests (.csv)",
        data=gerar_csv_decisoes_api_tests(),
        file_name="decisoes_api_tests_valoris.csv",
        mime="text/csv",
        key="download_decisoes_api_tests",
    )

    st.divider()

    resultado_sessao = st.session_state.get("resultado_api_endpoint_tests", {})
    if not resultado_sessao and CAMINHO_RELATORIO_API_TESTS.exists():
        try:
            resultado_sessao = json.loads(CAMINHO_RELATORIO_API_TESTS.read_text(encoding="utf-8"))
        except Exception:
            resultado_sessao = {}

    _renderizar_resultado_suite(resultado_sessao)

    st.divider()

    st.markdown("### Endpoints cobertos")
    st.code(
        """GET  /health
POST /leads
GET  /leads
POST /events
POST /leads inválido -> espera 422""",
        language="text",
    )

    st.divider()
    _renderizar_historico()

    st.markdown(
        """
        <div class="tests-note">
            <strong>Regra Tests:</strong> não conecte SQLite/PostgreSQL à API enquanto health,
            leads e events não passarem em testes repetíveis.
        </div>
        """,
        unsafe_allow_html=True,
    )


def executar_autoteste_api_endpoint_tests_valoris() -> List[Dict[str, str]]:
    saude = calcular_saude_api_endpoint_tests()

    return [
        {
            "teste": "versao_tests",
            "status": "OK" if VERSAO_API_ENDPOINT_TESTS_VALORIS == "3.8.65" else "FALHA",
            "detalhe": VERSAO_API_ENDPOINT_TESTS_VALORIS,
        },
        {
            "teste": "score_tests",
            "status": "OK" if 0 <= saude["score_tests"] <= 100 else "FALHA",
            "detalhe": str(saude["score_tests"]),
        },
        {
            "teste": "renderizador",
            "status": "OK" if callable(renderizar_api_endpoint_tests_valoris) else "FALHA",
            "detalhe": "renderizar_api_endpoint_tests_valoris",
        },
    ]
