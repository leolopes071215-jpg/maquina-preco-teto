# api_security_key_valoris.py

from __future__ import annotations

import csv
import json
import py_compile
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

import streamlit as st

from api_storage_adapter_valoris import calcular_saude_api_adapter
from api_endpoint_tests_valoris import calcular_saude_api_endpoint_tests
from api_smoke_tests_valoris import PASTA_API_SCAFFOLD, URL_API_LOCAL, testar_health_api


VERSAO_API_SECURITY_KEY_VALORIS = "3.8.68"

API_KEY_HEADER_NAME = "X-Valoris-API-Key"
DEFAULT_LOCAL_API_KEY = "valoris-local-dev-key"

CAMINHO_DECISOES_API_SECURITY = Path("decisoes_api_security_valoris.csv")
CAMINHO_MANIFESTO_API_SECURITY = Path("manifesto_api_security_valoris.json")

CAMINHO_SECURITY = Path("api_valoris/app/core/security.py")
CAMINHO_ROUTES_LEADS = Path("api_valoris/app/routes/leads.py")
CAMINHO_ROUTES_EVENTS = Path("api_valoris/app/routes/events.py")
CAMINHO_ENV_EXAMPLE = Path("api_valoris/.env.example")
CAMINHO_README_API = Path("api_valoris/README.md")

ARQUIVOS_SECURITY = [
    CAMINHO_SECURITY,
    CAMINHO_ROUTES_LEADS,
    CAMINHO_ROUTES_EVENTS,
]

CAMPOS_DECISAO_API_SECURITY = [
    "id",
    "data_registro",
    "score_security",
    "security_aplicada",
    "health_ok",
    "protected_ok",
    "public_ok",
    "decisao",
    "proximo_passo",
    "observacoes",
]

SECURITY_CORE_PY = 'from __future__ import annotations\n\nimport os\n\nfrom fastapi import Header, HTTPException, status\n\n\nAPI_KEY_HEADER_NAME = "X-Valoris-API-Key"\nDEFAULT_LOCAL_API_KEY = "valoris-local-dev-key"\n\n\ndef get_api_key() -> str:\n    return os.getenv("VALORIS_API_KEY", DEFAULT_LOCAL_API_KEY).strip()\n\n\ndef require_api_key(x_valoris_api_key: str | None = Header(default=None, alias=API_KEY_HEADER_NAME)) -> bool:\n    expected = get_api_key()\n\n    if not expected:\n        raise HTTPException(\n            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,\n            detail="API key local não configurada.",\n        )\n\n    if x_valoris_api_key != expected:\n        raise HTTPException(\n            status_code=status.HTTP_401_UNAUTHORIZED,\n            detail="API key ausente ou inválida.",\n        )\n\n    return True\n\n\ndef get_security_status() -> dict:\n    api_key = get_api_key()\n\n    return {\n        "ok": True,\n        "api_key_required": True,\n        "header_name": API_KEY_HEADER_NAME,\n        "using_default_local_key": api_key == DEFAULT_LOCAL_API_KEY,\n        "key_hint": f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) >= 8 else "***",\n    }'
ROUTES_LEADS_SECURE_PY = 'from fastapi import APIRouter, Depends, Query\n\nfrom app.core.security import get_security_status, require_api_key\nfrom app.schemas.lead import LeadCreate\nfrom app.services.repository_bridge import RepositoryBridge\n\n\nrouter = APIRouter()\nrepository = RepositoryBridge()\n\n\n@router.post("")\ndef create_lead(payload: LeadCreate):\n    result = repository.create_lead(payload)\n\n    return {\n        "ok": result["ok"],\n        "message": f"Lead salvo via storage_mode={result[\'storage_mode\']}.",\n        "storage_mode": result["storage_mode"],\n        "source": result["source"],\n        "file": result["file"],\n        "database": result["database"],\n        "lead": result["lead"],\n    }\n\n\n@router.get("")\ndef list_leads(\n    limit: int = Query(default=100, ge=1, le=500),\n    source: str = Query(default="auto"),\n    _authorized: bool = Depends(require_api_key),\n):\n    return repository.list_leads(limit=limit, source=source)\n\n\n@router.get("/storage-health")\ndef storage_health(_authorized: bool = Depends(require_api_key)):\n    return repository.storage_health()\n\n\n@router.get("/security")\ndef security_status(_authorized: bool = Depends(require_api_key)):\n    return get_security_status()'
ROUTES_EVENTS_SECURE_PY = 'from fastapi import APIRouter, Depends\n\nfrom app.core.security import require_api_key\nfrom app.schemas.event import EventCreate\nfrom app.services.repository_bridge import RepositoryBridge\n\n\nrouter = APIRouter()\nrepository = RepositoryBridge()\n\n\n@router.post("")\ndef create_event(payload: EventCreate, _authorized: bool = Depends(require_api_key)):\n    result = repository.create_event(payload)\n\n    return {\n        "ok": result["ok"],\n        "message": f"Evento salvo via storage_mode={result[\'storage_mode\']}.",\n        "storage_mode": result["storage_mode"],\n        "source": result["source"],\n        "file": result["file"],\n        "database": result["database"],\n        "event": result["event"],\n    }\n\n\n@router.get("/storage-health")\ndef storage_health(_authorized: bool = Depends(require_api_key)):\n    return repository.storage_health()'
ENV_EXAMPLE_APPEND = '# Segurança local da API Valoris\n# Em produção, substitua por uma chave forte e nunca publique em repositório.\nVALORIS_API_KEY=valoris-local-dev-key\nVALORIS_STORAGE_MODE=hybrid'
README_APPEND_SECURITY = '## Segurança local com API Key\n\nA partir da v3.8.68, alguns endpoints passam a exigir o header:\n\n`X-Valoris-API-Key: valoris-local-dev-key`\n\nEndpoints protegidos nesta fase:\n\n- `GET /leads`\n- `GET /leads/storage-health`\n- `GET /leads/security`\n- `POST /events`\n- `GET /events/storage-health`\n\nEndpoints mantidos públicos/localmente:\n\n- `GET /health`\n- `POST /leads`\n\nA chave padrão é apenas local. Antes de deploy público, trocar por variável de ambiente forte.'


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


def carregar_decisoes_api_security() -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_DECISOES_API_SECURITY, CAMPOS_DECISAO_API_SECURITY)

    with CAMINHO_DECISOES_API_SECURITY.open("r", newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def gerar_csv_decisoes_api_security() -> str:
    _garantir_csv(CAMINHO_DECISOES_API_SECURITY, CAMPOS_DECISAO_API_SECURITY)
    return CAMINHO_DECISOES_API_SECURITY.read_text(encoding="utf-8")


def salvar_decisao_api_security(decisao: Dict[str, Any]) -> Dict[str, str]:
    _garantir_csv(CAMINHO_DECISOES_API_SECURITY, CAMPOS_DECISAO_API_SECURITY)

    registro = {
        "id": str(uuid4())[:8],
        "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score_security": str(decisao.get("score_security", "")),
        "security_aplicada": str(decisao.get("security_aplicada", "")),
        "health_ok": str(decisao.get("health_ok", "")),
        "protected_ok": str(decisao.get("protected_ok", "")),
        "public_ok": str(decisao.get("public_ok", "")),
        "decisao": _limpar_texto(decisao.get("decisao", "")),
        "proximo_passo": _limpar_texto(decisao.get("proximo_passo", "")),
        "observacoes": _limpar_texto(decisao.get("observacoes", "")),
    }

    with CAMINHO_DECISOES_API_SECURITY.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISAO_API_SECURITY)
        escritor.writerow(registro)

    return registro


def _request_json(
    method: str,
    path: str,
    payload: Dict[str, Any] | None = None,
    api_key: str | None = None,
    timeout: float = 4.0,
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


def verificar_arquivos_security() -> Dict[str, Any]:
    itens = []

    for caminho in ARQUIVOS_SECURITY:
        itens.append(
            {
                "arquivo": str(caminho),
                "existe": caminho.exists(),
                "tamanho_bytes": caminho.stat().st_size if caminho.exists() else 0,
            }
        )

    total = len(itens)
    existentes = len([item for item in itens if item["existe"]])

    return {
        "itens": itens,
        "total": total,
        "existentes": existentes,
        "ok": existentes == total,
    }


def compilar_arquivos_security() -> Dict[str, Any]:
    resultados = []

    for caminho in ARQUIVOS_SECURITY:
        if not caminho.exists():
            resultados.append(
                {
                    "arquivo": str(caminho),
                    "status": "ausente",
                    "detalhe": "Arquivo não encontrado.",
                }
            )
            continue

        try:
            py_compile.compile(str(caminho), doraise=True)
            resultados.append(
                {
                    "arquivo": str(caminho),
                    "status": "ok",
                    "detalhe": "Compilação OK.",
                }
            )
        except Exception as erro:
            resultados.append(
                {
                    "arquivo": str(caminho),
                    "status": "erro",
                    "detalhe": str(erro),
                }
            )

    erros = [item for item in resultados if item["status"] != "ok"]

    return {
        "resultados": resultados,
        "erros": erros,
        "ok": len(erros) == 0,
    }


def aplicar_api_key_local() -> Dict[str, Any]:
    if not PASTA_API_SCAFFOLD.exists():
        return {
            "ok": False,
            "mensagem": "A pasta api_valoris não existe. Gere o scaffold antes.",
            "arquivos": [],
        }

    CAMINHO_SECURITY.parent.mkdir(parents=True, exist_ok=True)
    CAMINHO_ROUTES_LEADS.parent.mkdir(parents=True, exist_ok=True)
    CAMINHO_ROUTES_EVENTS.parent.mkdir(parents=True, exist_ok=True)

    CAMINHO_SECURITY.write_text(SECURITY_CORE_PY + "\n", encoding="utf-8")
    CAMINHO_ROUTES_LEADS.write_text(ROUTES_LEADS_SECURE_PY + "\n", encoding="utf-8")
    CAMINHO_ROUTES_EVENTS.write_text(ROUTES_EVENTS_SECURE_PY + "\n", encoding="utf-8")

    if CAMINHO_ENV_EXAMPLE.exists():
        texto_env = CAMINHO_ENV_EXAMPLE.read_text(encoding="utf-8", errors="ignore")
        if "VALORIS_API_KEY" not in texto_env:
            CAMINHO_ENV_EXAMPLE.write_text(
                texto_env.rstrip() + "\n\n" + ENV_EXAMPLE_APPEND + "\n",
                encoding="utf-8",
            )
    else:
        CAMINHO_ENV_EXAMPLE.write_text(ENV_EXAMPLE_APPEND + "\n", encoding="utf-8")

    if CAMINHO_README_API.exists():
        texto_readme = CAMINHO_README_API.read_text(encoding="utf-8", errors="ignore")
        if "Segurança local com API Key" not in texto_readme:
            CAMINHO_README_API.write_text(
                texto_readme.rstrip() + "\n\n" + README_APPEND_SECURITY + "\n",
                encoding="utf-8",
            )

    compilacao = compilar_arquivos_security()
    manifesto = gerar_manifesto_api_security()

    return {
        "ok": compilacao["ok"],
        "mensagem": "API Key local aplicada. Reinicie a API para carregar a proteção.",
        "header": API_KEY_HEADER_NAME,
        "api_key_local": DEFAULT_LOCAL_API_KEY,
        "arquivos": [str(item) for item in ARQUIVOS_SECURITY],
        "compilacao": compilacao,
        "manifesto": manifesto,
    }


def testar_api_key_local() -> Dict[str, Any]:
    health = _request_json("GET", "/health")
    lead_public = _request_json(
        "POST",
        "/leads",
        {
            "nome": "Lead Security Test",
            "contato": f"security+{str(uuid4())[:8]}@valoris.local",
            "perfil": "security",
            "principal_dor": "validar api key",
            "plano_interesse": "beta",
            "preco_aceitavel": "teste",
            "pagaria_agora": "nao",
            "comentario": "teste da v3.8.68",
        },
    )

    leads_without_key = _request_json("GET", "/leads")
    leads_with_key = _request_json("GET", "/leads", api_key=DEFAULT_LOCAL_API_KEY)
    events_without_key = _request_json(
        "POST",
        "/events",
        {
            "sessao_id": str(uuid4())[:8],
            "evento": "security_without_key",
            "origem": "api-security",
            "contexto": "v3.8.68",
            "perfil": "qa",
            "valor": "1",
            "detalhe": "deve falhar sem chave",
        },
    )
    events_with_key = _request_json(
        "POST",
        "/events",
        {
            "sessao_id": str(uuid4())[:8],
            "evento": "security_with_key",
            "origem": "api-security",
            "contexto": "v3.8.68",
            "perfil": "qa",
            "valor": "1",
            "detalhe": "deve passar com chave",
        },
        api_key=DEFAULT_LOCAL_API_KEY,
    )
    security_status = _request_json("GET", "/leads/security", api_key=DEFAULT_LOCAL_API_KEY)

    testes = [
        {
            "teste": "GET /health público",
            "ok": health["ok"] and health["status_code"] == 200,
            "resultado": health,
        },
        {
            "teste": "POST /leads público",
            "ok": lead_public["ok"] and lead_public["status_code"] == 200,
            "resultado": lead_public,
        },
        {
            "teste": "GET /leads sem chave bloqueia",
            "ok": leads_without_key["status_code"] == 401,
            "resultado": leads_without_key,
        },
        {
            "teste": "GET /leads com chave libera",
            "ok": leads_with_key["ok"] and leads_with_key["status_code"] == 200,
            "resultado": leads_with_key,
        },
        {
            "teste": "POST /events sem chave bloqueia",
            "ok": events_without_key["status_code"] == 401,
            "resultado": events_without_key,
        },
        {
            "teste": "POST /events com chave libera",
            "ok": events_with_key["ok"] and events_with_key["status_code"] == 200,
            "resultado": events_with_key,
        },
        {
            "teste": "GET /leads/security com chave",
            "ok": security_status["ok"] and security_status["status_code"] == 200,
            "resultado": security_status,
        },
    ]

    ok_count = len([teste for teste in testes if teste["ok"]])

    return {
        "ok": ok_count == len(testes),
        "ok_count": ok_count,
        "total": len(testes),
        "testes": testes,
    }


def calcular_saude_api_security() -> Dict[str, Any]:
    arquivos = verificar_arquivos_security()
    compilacao = compilar_arquivos_security()
    health = testar_health_api()

    security_aplicada = CAMINHO_SECURITY.exists() and "require_api_key" in CAMINHO_SECURITY.read_text(
        encoding="utf-8",
        errors="ignore",
    ) if CAMINHO_SECURITY.exists() else False

    try:
        adapter = calcular_saude_api_adapter()
    except Exception:
        adapter = {"score_adapter": 0}

    try:
        endpoint_tests = calcular_saude_api_endpoint_tests()
    except Exception:
        endpoint_tests = {"score_tests": 0}

    score_adapter = int(adapter.get("score_adapter", 0) or 0)
    score_tests = int(endpoint_tests.get("score_tests", 0) or 0)

    protected_ok = False
    public_ok = False

    if health["health_ok"]:
        resultado_seg = testar_api_key_local()
        protected_ok = any(t["teste"] == "GET /leads sem chave bloqueia" and t["ok"] for t in resultado_seg["testes"])
        public_ok = any(t["teste"] == "GET /health público" and t["ok"] for t in resultado_seg["testes"])
    else:
        resultado_seg = {"ok": False, "ok_count": 0, "total": 0, "testes": []}

    score = 10
    score += min(arquivos["existentes"] * 8, 24)
    score += 12 if compilacao["ok"] else 0
    score += 15 if security_aplicada else 0
    score += 10 if health["health_ok"] else 0
    score += 12 if protected_ok else 0
    score += 8 if public_ok else 0
    score += min(score_adapter * 0.05, 5)
    score += min(score_tests * 0.04, 4)
    score = int(round(max(0, min(100, score))))

    if score >= 85 and protected_ok:
        decisao = "API Key local validada"
        proximo_passo = "Fechar versão e avançar para painel de segurança/API hardening."
    elif score >= 70 and security_aplicada:
        decisao = "API Key aplicada, falta validação com API reiniciada"
        proximo_passo = "Reinicie a API e rode os testes de segurança."
    elif score >= 50:
        decisao = "Segurança parcialmente preparada"
        proximo_passo = "Aplique API Key local pela aba e reinicie a API."
    else:
        decisao = "Segurança ainda não preparada"
        proximo_passo = "Aplique API Key local antes de conectar PostgreSQL/Supabase."

    return {
        "score_security": score,
        "security_aplicada": security_aplicada,
        "arquivos": arquivos,
        "compilacao": compilacao,
        "health": health,
        "health_ok": health["health_ok"],
        "protected_ok": protected_ok,
        "public_ok": public_ok,
        "resultado_seg": resultado_seg,
        "score_adapter": score_adapter,
        "score_tests": score_tests,
        "decisao": decisao,
        "proximo_passo": proximo_passo,
    }


def gerar_manifesto_api_security() -> Dict[str, Any]:
    saude = calcular_saude_api_security()

    manifesto = {
        "versao": VERSAO_API_SECURITY_KEY_VALORIS,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "saude": saude,
        "header": API_KEY_HEADER_NAME,
        "chave_local_padrao": DEFAULT_LOCAL_API_KEY,
        "endpoints_publicos": [
            "GET /health",
            "POST /leads",
        ],
        "endpoints_protegidos": [
            "GET /leads",
            "GET /leads/storage-health",
            "GET /leads/security",
            "POST /events",
            "GET /events/storage-health",
        ],
    }

    CAMINHO_MANIFESTO_API_SECURITY.write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return manifesto


def _gerar_markdown_security(saude: Dict[str, Any]) -> str:
    return f"""# API Key Local — Valoris

Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Diagnóstico

Score Security: {saude["score_security"]}/100  
Decisão: {saude["decisao"]}  
Próximo passo: {saude["proximo_passo"]}

Security aplicada: {saude["security_aplicada"]}  
Health OK: {saude["health_ok"]}  
Proteção OK: {saude["protected_ok"]}  
Públicos OK: {saude["public_ok"]}  

## Header

`{API_KEY_HEADER_NAME}: {DEFAULT_LOCAL_API_KEY}`

## Endpoints públicos

- `GET /health`
- `POST /leads`

## Endpoints protegidos

- `GET /leads`
- `GET /leads/storage-health`
- `GET /leads/security`
- `POST /events`
- `GET /events/storage-health`

## Teste PowerShell

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/leads/storage-health" -Headers @{{"X-Valoris-API-Key"="valoris-local-dev-key"}}
```

## Regra

Esta é uma proteção local. Antes de deploy real, trocar a chave por variável de ambiente forte.
"""


def _injetar_css_security() -> None:
    st.markdown(
        """
        <style>
            .security-hero {
                padding: clamp(1.18rem, 3vw, 2rem);
                border-radius: 30px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    radial-gradient(circle at top left, rgba(214, 181, 109, 0.26), transparent 30%),
                    radial-gradient(circle at bottom right, rgba(127, 36, 36, 0.28), transparent 34%),
                    linear-gradient(135deg, rgba(8, 15, 27, 0.99), rgba(5, 9, 18, 0.99));
                box-shadow: 0 18px 58px rgba(0, 0, 0, 0.31);
                margin-bottom: 1rem;
            }

            .security-eyebrow {
                color: #d6b56d;
                font-size: 0.74rem;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                font-weight: 880;
                margin-bottom: 0.35rem;
            }

            .security-title {
                color: #f4f7fb;
                font-size: clamp(1.75rem, 5.4vw, 3.1rem);
                font-weight: 950;
                line-height: 1.02;
                letter-spacing: -0.058em;
                margin-bottom: 0.55rem;
            }

            .security-subtitle {
                color: rgba(244, 247, 251, 0.75);
                font-size: clamp(0.94rem, 2.2vw, 1.06rem);
                line-height: 1.56;
                max-width: 1020px;
            }

            .security-note {
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


def renderizar_api_security_key_valoris() -> None:
    _injetar_css_security()

    st.markdown(
        f"""
        <div class="security-hero">
            <div class="security-eyebrow">Valoris • API Security • v{VERSAO_API_SECURITY_KEY_VALORIS}</div>
            <div class="security-title">Proteja os endpoints antes de escalar.</div>
            <div class="security-subtitle">
                Esta etapa aplica API Key local nos endpoints sensíveis, mantendo health e captura de leads públicos.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    saude = calcular_saude_api_security()

    st.markdown("### Diagnóstico de segurança")
    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Score Security", f"{saude['score_security']}/100")

    with col_2:
        st.metric("Security", "OK" if saude["security_aplicada"] else "Pendente")

    with col_3:
        st.metric("Proteção", "OK" if saude["protected_ok"] else "Pendente")

    with col_4:
        st.metric("Health", "OK" if saude["health_ok"] else "Offline")

    st.progress(saude["score_security"] / 100)

    if saude["score_security"] >= 85:
        st.success(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    elif saude["score_security"] >= 50:
        st.warning(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    else:
        st.info(f"**{saude['decisao']}** — {saude['proximo_passo']}")

    st.divider()

    st.markdown("### Chave local")
    st.code(f"{API_KEY_HEADER_NAME}: {DEFAULT_LOCAL_API_KEY}", language="text")

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        if st.button("Aplicar API Key local", key="aplicar_api_key_local"):
            resultado = aplicar_api_key_local()
            if resultado["ok"]:
                st.success(resultado["mensagem"])
            else:
                st.warning(resultado["mensagem"])
            st.json(resultado)
            st.rerun()

    with col_b:
        if st.button("Testar proteção agora", key="testar_api_key_local"):
            resultado = testar_api_key_local()
            if resultado["ok"]:
                st.success(f"Proteção aprovada: {resultado['ok_count']}/{resultado['total']}")
            else:
                st.warning(f"Proteção com falhas: {resultado['ok_count']}/{resultado['total']}")
            st.session_state["resultado_api_security"] = resultado

    with col_c:
        if st.button("Gerar manifesto Security", key="gerar_manifesto_api_security"):
            manifesto = gerar_manifesto_api_security()
            st.success(f"Manifesto gerado: {CAMINHO_MANIFESTO_API_SECURITY}")
            st.json(
                {
                    "versao": manifesto["versao"],
                    "score": manifesto["saude"]["score_security"],
                    "header": manifesto["header"],
                }
            )

    if st.button("Salvar decisão Security", key="salvar_decisao_api_security"):
        registro = salvar_decisao_api_security(
            {
                "score_security": saude["score_security"],
                "security_aplicada": saude["security_aplicada"],
                "health_ok": saude["health_ok"],
                "protected_ok": saude["protected_ok"],
                "public_ok": saude["public_ok"],
                "decisao": saude["decisao"],
                "proximo_passo": saude["proximo_passo"],
                "observacoes": "Decisão gerada pela proteção local com API Key.",
            }
        )
        st.success(f"Decisão salva: {registro['decisao']}")
        st.rerun()

    st.download_button(
        "Baixar diagnóstico API Security (.md)",
        data=_gerar_markdown_security(saude),
        file_name="api_security_key_valoris.md",
        mime="text/markdown",
        key="download_api_security",
    )

    st.download_button(
        "Baixar decisões API Security (.csv)",
        data=gerar_csv_decisoes_api_security(),
        file_name="decisoes_api_security_valoris.csv",
        mime="text/csv",
        key="download_decisoes_api_security",
    )

    st.divider()

    resultado = st.session_state.get("resultado_api_security", saude.get("resultado_seg", {}))
    st.markdown("### Resultado dos testes de segurança")
    if resultado:
        st.json(resultado)
    else:
        st.info("Rode a API e teste a proteção.")

    st.divider()

    st.markdown("### Arquivos de segurança")
    for item in saude["arquivos"]["itens"]:
        with st.container(border=True):
            st.markdown(f"**{item['arquivo']}**")
            st.caption("OK" if item["existe"] else "Ausente")
            st.markdown(f"Tamanho: **{item['tamanho_bytes']} bytes**")

    st.markdown(
        """
        <div class="security-note">
            <strong>Regra Security:</strong> esta chave é local. Para produção, use variável de ambiente forte,
            rotação de segredo, HTTPS e autenticação real.
        </div>
        """,
        unsafe_allow_html=True,
    )


def executar_autoteste_api_security_key_valoris() -> List[Dict[str, str]]:
    saude = calcular_saude_api_security()

    return [
        {
            "teste": "versao_security",
            "status": "OK" if VERSAO_API_SECURITY_KEY_VALORIS == "3.8.68" else "FALHA",
            "detalhe": VERSAO_API_SECURITY_KEY_VALORIS,
        },
        {
            "teste": "score_security",
            "status": "OK" if 0 <= saude["score_security"] <= 100 else "FALHA",
            "detalhe": str(saude["score_security"]),
        },
        {
            "teste": "renderizador",
            "status": "OK" if callable(renderizar_api_security_key_valoris) else "FALHA",
            "detalhe": "renderizar_api_security_key_valoris",
        },
    ]
