# api_smoke_tests_valoris.py

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

from api_scaffold_valoris import ARQUIVOS_SCAFFOLD, PASTA_API_SCAFFOLD
from api_contratos_valoris import calcular_prontidao_api
from repositorios_valoris import calcular_saude_repositorios


# ============================================================
# VALORIS
# v3.8.63 — Smoke Tests da API Local
# ------------------------------------------------------------
# Valida se o laboratório FastAPI está pronto para uso local.
# ============================================================


VERSAO_API_SMOKE_TESTS_VALORIS = "3.8.63"

CAMINHO_DECISOES_API_SMOKE = Path("decisoes_api_smoke_valoris.csv")
CAMINHO_MANIFESTO_API_SMOKE = Path("manifesto_api_smoke_valoris.json")
PASTA_SCRIPTS_API = Path("scripts_api_valoris")
CAMINHO_SCRIPT_RUN_PS1 = PASTA_SCRIPTS_API / "rodar_api_valoris.ps1"
CAMINHO_SCRIPT_TEST_PS1 = PASTA_SCRIPTS_API / "testar_api_valoris.ps1"

URL_API_LOCAL = "http://127.0.0.1:8000"
URL_HEALTH = f"{URL_API_LOCAL}/health"
URL_DOCS = f"{URL_API_LOCAL}/docs"

CAMPOS_DECISAO_API_SMOKE = [
    "id",
    "data_registro",
    "score_smoke",
    "scaffold_existe",
    "arquivos_ok",
    "compilacao_ok",
    "api_rodando",
    "health_ok",
    "decisao",
    "proximo_passo",
    "observacoes",
]

ARQUIVOS_PY_API = [
    "api_valoris/app/__init__.py",
    "api_valoris/app/main.py",
    "api_valoris/app/core/__init__.py",
    "api_valoris/app/core/config.py",
    "api_valoris/app/schemas/__init__.py",
    "api_valoris/app/schemas/lead.py",
    "api_valoris/app/schemas/event.py",
    "api_valoris/app/schemas/health.py",
    "api_valoris/app/routes/__init__.py",
    "api_valoris/app/routes/health.py",
    "api_valoris/app/routes/events.py",
    "api_valoris/app/routes/leads.py",
    "api_valoris/app/services/__init__.py",
    "api_valoris/app/services/repository_bridge.py",
]

SCRIPT_RUN_PS1 = r"""# Rodar API Valoris localmente
Set-Location "$PSScriptRoot\.."

if (!(Test-Path ".\api_valoris")) {
    Write-Host "A pasta api_valoris não existe. Gere o scaffold no app primeiro." -ForegroundColor Red
    exit 1
}

Set-Location ".\api_valoris"

if (!(Test-Path ".\.venv")) {
    python -m venv .venv
}

.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements_api.txt
python -m uvicorn app.main:app --reload --port 8000
""".strip()

SCRIPT_TEST_PS1 = r"""# Testar API Valoris local
try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -Method GET
    Write-Host "Health OK:" -ForegroundColor Green
    $health | ConvertTo-Json
} catch {
    Write-Host "Falha no /health. A API está rodando?" -ForegroundColor Red
    Write-Host $_
}

try {
    $payload = @{
        nome = "Lead Teste"
        contato = "teste@valoris.local"
        perfil = "teste"
        principal_dor = "validar API"
        plano_interesse = "beta"
        preco_aceitavel = "manual"
        pagaria_agora = "nao"
        comentario = "gerado por smoke test"
    } | ConvertTo-Json

    $lead = Invoke-RestMethod -Uri "http://127.0.0.1:8000/leads" -Method POST -Body $payload -ContentType "application/json"
    Write-Host "Lead POST OK:" -ForegroundColor Green
    $lead | ConvertTo-Json
} catch {
    Write-Host "Falha no POST /leads." -ForegroundColor Red
    Write-Host $_
}
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


def carregar_decisoes_api_smoke() -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_DECISOES_API_SMOKE, CAMPOS_DECISAO_API_SMOKE)

    with CAMINHO_DECISOES_API_SMOKE.open("r", newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def gerar_csv_decisoes_api_smoke() -> str:
    _garantir_csv(CAMINHO_DECISOES_API_SMOKE, CAMPOS_DECISAO_API_SMOKE)
    return CAMINHO_DECISOES_API_SMOKE.read_text(encoding="utf-8")


def salvar_decisao_api_smoke(decisao: Dict[str, Any]) -> Dict[str, str]:
    _garantir_csv(CAMINHO_DECISOES_API_SMOKE, CAMPOS_DECISAO_API_SMOKE)

    registro = {
        "id": str(uuid4())[:8],
        "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score_smoke": str(decisao.get("score_smoke", "")),
        "scaffold_existe": str(decisao.get("scaffold_existe", "")),
        "arquivos_ok": str(decisao.get("arquivos_ok", "")),
        "compilacao_ok": str(decisao.get("compilacao_ok", "")),
        "api_rodando": str(decisao.get("api_rodando", "")),
        "health_ok": str(decisao.get("health_ok", "")),
        "decisao": _limpar_texto(decisao.get("decisao", "")),
        "proximo_passo": _limpar_texto(decisao.get("proximo_passo", "")),
        "observacoes": _limpar_texto(decisao.get("observacoes", "")),
    }

    with CAMINHO_DECISOES_API_SMOKE.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISAO_API_SMOKE)
        escritor.writerow(registro)

    return registro


def verificar_arquivos_scaffold() -> Dict[str, Any]:
    itens = []

    for caminho in ARQUIVOS_SCAFFOLD:
        path = Path(caminho)
        itens.append(
            {
                "arquivo": caminho,
                "existe": path.exists(),
                "tamanho_bytes": path.stat().st_size if path.exists() else 0,
            }
        )

    existentes = len([item for item in itens if item["existe"]])

    return {
        "itens": itens,
        "total": len(itens),
        "existentes": existentes,
        "ausentes": [item["arquivo"] for item in itens if not item["existe"]],
        "ok": existentes == len(itens),
    }


def compilar_arquivos_api() -> Dict[str, Any]:
    resultados = []

    for arquivo in ARQUIVOS_PY_API:
        caminho = Path(arquivo)

        if not caminho.exists():
            resultados.append(
                {
                    "arquivo": arquivo,
                    "status": "ausente",
                    "detalhe": "Arquivo não encontrado.",
                }
            )
            continue

        try:
            py_compile.compile(str(caminho), doraise=True)
            resultados.append(
                {
                    "arquivo": arquivo,
                    "status": "ok",
                    "detalhe": "Compilação OK.",
                }
            )
        except Exception as erro:
            resultados.append(
                {
                    "arquivo": arquivo,
                    "status": "erro",
                    "detalhe": str(erro),
                }
            )

    erros = [item for item in resultados if item["status"] != "ok"]

    return {
        "resultados": resultados,
        "ok": len(resultados) - len(erros),
        "total": len(resultados),
        "erros": erros,
        "compilacao_ok": len(erros) == 0,
    }


def testar_health_api(timeout: float = 1.5) -> Dict[str, Any]:
    try:
        with urllib.request.urlopen(URL_HEALTH, timeout=timeout) as resposta:
            status_code = resposta.status
            corpo = resposta.read().decode("utf-8", errors="ignore")

        try:
            dados = json.loads(corpo)
        except Exception:
            dados = {"raw": corpo}

        return {
            "api_rodando": True,
            "health_ok": status_code == 200,
            "status_code": status_code,
            "resposta": dados,
            "erro": "",
        }

    except urllib.error.URLError as erro:
        return {
            "api_rodando": False,
            "health_ok": False,
            "status_code": None,
            "resposta": {},
            "erro": str(erro),
        }
    except Exception as erro:
        return {
            "api_rodando": False,
            "health_ok": False,
            "status_code": None,
            "resposta": {},
            "erro": str(erro),
        }


def gerar_scripts_api() -> Dict[str, Any]:
    PASTA_SCRIPTS_API.mkdir(parents=True, exist_ok=True)
    CAMINHO_SCRIPT_RUN_PS1.write_text(SCRIPT_RUN_PS1 + "\n", encoding="utf-8")
    CAMINHO_SCRIPT_TEST_PS1.write_text(SCRIPT_TEST_PS1 + "\n", encoding="utf-8")

    return {
        "pasta": str(PASTA_SCRIPTS_API),
        "scripts": [
            str(CAMINHO_SCRIPT_RUN_PS1),
            str(CAMINHO_SCRIPT_TEST_PS1),
        ],
    }


def calcular_saude_api_smoke() -> Dict[str, Any]:
    arquivos = verificar_arquivos_scaffold()
    compilacao = compilar_arquivos_api()
    health = testar_health_api()

    try:
        prontidao_api = calcular_prontidao_api()
    except Exception:
        prontidao_api = {"score_api": 0}

    try:
        saude_repositorios = calcular_saude_repositorios()
    except Exception:
        saude_repositorios = {"score_repositorio": 0}

    score_api = int(prontidao_api.get("score_api", 0) or 0)
    score_repositorio = int(saude_repositorios.get("score_repositorio", 0) or 0)

    score = 10
    score += min(score_api * 0.20, 20)
    score += min(score_repositorio * 0.12, 12)
    score += min(arquivos["existentes"] * 2.2, 35)
    score += 18 if compilacao["compilacao_ok"] else 0
    score += 15 if health["health_ok"] else 0
    score = int(round(max(0, min(100, score))))

    if score >= 85 and health["health_ok"]:
        decisao = "API local validada"
        proximo_passo = "Testar POST /events e POST /leads, depois criar ponte real com repositórios."
    elif score >= 70 and arquivos["ok"] and compilacao["compilacao_ok"]:
        decisao = "API pronta para rodar localmente"
        proximo_passo = "Abra um terminal separado e rode o script da API. Depois volte aqui e teste /health."
    elif score >= 50:
        decisao = "Scaffold parcialmente pronto"
        proximo_passo = "Corrija arquivos ausentes ou gere novamente o scaffold antes de rodar a API."
    else:
        decisao = "API ainda não preparada"
        proximo_passo = "Gere o scaffold FastAPI pela aba API Scaffold antes dos smoke tests."

    return {
        "score_smoke": score,
        "score_api": score_api,
        "score_repositorio": score_repositorio,
        "scaffold_existe": PASTA_API_SCAFFOLD.exists(),
        "arquivos": arquivos,
        "compilacao": compilacao,
        "health": health,
        "api_rodando": health["api_rodando"],
        "health_ok": health["health_ok"],
        "decisao": decisao,
        "proximo_passo": proximo_passo,
    }


def gerar_manifesto_api_smoke() -> Dict[str, Any]:
    saude = calcular_saude_api_smoke()

    manifesto = {
        "versao": VERSAO_API_SMOKE_TESTS_VALORIS,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "saude": saude,
        "url_api_local": URL_API_LOCAL,
        "url_health": URL_HEALTH,
        "url_docs": URL_DOCS,
    }

    CAMINHO_MANIFESTO_API_SMOKE.write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return manifesto


def _gerar_markdown_smoke(saude: Dict[str, Any]) -> str:
    ausentes = "\n".join([f"- `{item}`" for item in saude["arquivos"]["ausentes"]]) or "- Nenhum"
    erros_compilacao = "\n".join(
        [
            f"- `{item['arquivo']}` — {item['status']}: {item['detalhe']}"
            for item in saude["compilacao"]["erros"]
        ]
    ) or "- Nenhum"

    return f"""# Smoke Tests API Local — Valoris

Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Diagnóstico

Score Smoke: {saude["score_smoke"]}/100  
Decisão: {saude["decisao"]}  
Próximo passo: {saude["proximo_passo"]}

Scaffold existe: {saude["scaffold_existe"]}  
Arquivos existentes: {saude["arquivos"]["existentes"]}/{saude["arquivos"]["total"]}  
Compilação OK: {saude["compilacao"]["compilacao_ok"]}  
API rodando: {saude["api_rodando"]}  
Health OK: {saude["health_ok"]}  

## Arquivos ausentes

{ausentes}

## Erros de compilação

{erros_compilacao}

## URLs locais

- Health: `{URL_HEALTH}`
- Docs: `{URL_DOCS}`

## Rodar API

```powershell
.\\scripts_api_valoris\\rodar_api_valoris.ps1
```

## Testar API

```powershell
.\\scripts_api_valoris\\testar_api_valoris.ps1
```

## Regra

Smoke test não é produção. É só a garantia de que o laboratório FastAPI está vivo.
"""


def _injetar_css_smoke() -> None:
    st.markdown(
        """
        <style>
            .smoke-hero {
                padding: clamp(1.18rem, 3vw, 2rem);
                border-radius: 30px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    radial-gradient(circle at top left, rgba(214, 181, 109, 0.26), transparent 30%),
                    radial-gradient(circle at bottom right, rgba(36, 128, 91, 0.22), transparent 34%),
                    linear-gradient(135deg, rgba(8, 15, 27, 0.99), rgba(5, 9, 18, 0.99));
                box-shadow: 0 18px 58px rgba(0, 0, 0, 0.31);
                margin-bottom: 1rem;
            }

            .smoke-eyebrow {
                color: #d6b56d;
                font-size: 0.74rem;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                font-weight: 880;
                margin-bottom: 0.35rem;
            }

            .smoke-title {
                color: #f4f7fb;
                font-size: clamp(1.75rem, 5.4vw, 3.1rem);
                font-weight: 950;
                line-height: 1.02;
                letter-spacing: -0.058em;
                margin-bottom: 0.55rem;
            }

            .smoke-subtitle {
                color: rgba(244, 247, 251, 0.75);
                font-size: clamp(0.94rem, 2.2vw, 1.06rem);
                line-height: 1.56;
                max-width: 1020px;
            }

            .smoke-note {
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
        <div class="smoke-hero">
            <div class="smoke-eyebrow">Valoris • API Smoke Tests • v{VERSAO_API_SMOKE_TESTS_VALORIS}</div>
            <div class="smoke-title">Valide se a API local está viva.</div>
            <div class="smoke-subtitle">
                Esta etapa checa arquivos, compilação e /health da FastAPI. É o teste de qualidade
                antes de conectar leads, eventos e valuation no backend.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _renderizar_metricas(saude: Dict[str, Any]) -> None:
    st.markdown("### Diagnóstico smoke test")
    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Score Smoke", f"{saude['score_smoke']}/100")
    with col_2:
        st.metric("Arquivos", f"{saude['arquivos']['existentes']}/{saude['arquivos']['total']}")
    with col_3:
        st.metric("Compilação", "OK" if saude["compilacao"]["compilacao_ok"] else "Falha")
    with col_4:
        st.metric("Health", "OK" if saude["health_ok"] else "Offline")

    st.progress(saude["score_smoke"] / 100)

    if saude["score_smoke"] >= 80:
        st.success(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    elif saude["score_smoke"] >= 50:
        st.warning(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    else:
        st.info(f"**{saude['decisao']}** — {saude['proximo_passo']}")


def _renderizar_arquivos(saude: Dict[str, Any]) -> None:
    st.markdown("### Arquivos do scaffold")

    for item in saude["arquivos"]["itens"]:
        with st.container(border=True):
            st.markdown(f"**{item['arquivo']}**")
            st.caption("OK" if item["existe"] else "Ausente")
            st.markdown(f"Tamanho: **{item['tamanho_bytes']} bytes**")


def _renderizar_compilacao(saude: Dict[str, Any]) -> None:
    st.markdown("### Compilação dos arquivos da API")

    for item in saude["compilacao"]["resultados"]:
        with st.container(border=True):
            st.markdown(f"**{item['arquivo']}** — {item['status']}")
            st.caption(item["detalhe"])


def _renderizar_health(saude: Dict[str, Any]) -> None:
    st.markdown("### Teste /health")

    if saude["health_ok"]:
        st.success(f"API respondeu em {URL_HEALTH}")
        st.json(saude["health"]["resposta"])
    else:
        st.warning("A API não respondeu no /health. Rode a API em outro terminal e atualize esta aba.")
        st.code(".\\scripts_api_valoris\\rodar_api_valoris.ps1", language="powershell")
        if saude["health"]["erro"]:
            st.caption(saude["health"]["erro"])


def _renderizar_historico() -> None:
    historico = carregar_decisoes_api_smoke()
    st.markdown("### Histórico de decisões Smoke API")

    if not historico:
        st.info("Ainda não há decisões salvas.")
        return

    for item in reversed(historico[-10:]):
        with st.container(border=True):
            st.markdown(f"**{item.get('decisao', 'N/D')}**")
            st.caption(item.get("data_registro", "N/D"))
            st.markdown(f"Score: {item.get('score_smoke', 'N/D')}/100")
            st.markdown(f"Próximo passo: {item.get('proximo_passo', 'N/D')}")


def renderizar_api_smoke_tests_valoris() -> None:
    _injetar_css_smoke()
    _renderizar_hero()

    saude = calcular_saude_api_smoke()
    _renderizar_metricas(saude)

    st.divider()

    col_1, col_2, col_3 = st.columns(3)

    with col_1:
        if st.button("Gerar scripts locais da API", key="gerar_scripts_api_valoris"):
            resultado = gerar_scripts_api()
            st.success(f"Scripts gerados em {resultado['pasta']}")
            st.json(resultado)

    with col_2:
        if st.button("Gerar manifesto Smoke", key="gerar_manifesto_api_smoke"):
            manifesto = gerar_manifesto_api_smoke()
            st.success(f"Manifesto gerado: {CAMINHO_MANIFESTO_API_SMOKE}")
            st.json(
                {
                    "versao": manifesto["versao"],
                    "score": manifesto["saude"]["score_smoke"],
                    "health_ok": manifesto["saude"]["health_ok"],
                }
            )

    with col_3:
        if st.button("Salvar decisão Smoke", key="salvar_decisao_api_smoke"):
            registro = salvar_decisao_api_smoke(
                {
                    "score_smoke": saude["score_smoke"],
                    "scaffold_existe": saude["scaffold_existe"],
                    "arquivos_ok": saude["arquivos"]["ok"],
                    "compilacao_ok": saude["compilacao"]["compilacao_ok"],
                    "api_rodando": saude["api_rodando"],
                    "health_ok": saude["health_ok"],
                    "decisao": saude["decisao"],
                    "proximo_passo": saude["proximo_passo"],
                    "observacoes": "Decisão gerada pelo smoke test da API.",
                }
            )
            st.success(f"Decisão salva: {registro['decisao']}")
            st.rerun()

    st.download_button(
        "Baixar diagnóstico Smoke API (.md)",
        data=_gerar_markdown_smoke(saude),
        file_name="api_smoke_tests_valoris.md",
        mime="text/markdown",
        key="download_api_smoke_valoris",
    )

    st.download_button(
        "Baixar decisões Smoke API (.csv)",
        data=gerar_csv_decisoes_api_smoke(),
        file_name="decisoes_api_smoke_valoris.csv",
        mime="text/csv",
        key="download_decisoes_api_smoke",
    )

    st.divider()
    _renderizar_health(saude)

    st.divider()
    _renderizar_arquivos(saude)

    st.divider()
    _renderizar_compilacao(saude)

    st.divider()
    _renderizar_historico()

    st.markdown(
        """
        <div class="smoke-note">
            <strong>Regra Smoke:</strong> só avançamos para conectar repositórios reais quando
            health, eventos e leads funcionarem localmente com estabilidade.
        </div>
        """,
        unsafe_allow_html=True,
    )


def executar_autoteste_api_smoke_tests_valoris() -> List[Dict[str, str]]:
    saude = calcular_saude_api_smoke()

    return [
        {
            "teste": "versao_smoke",
            "status": "OK" if VERSAO_API_SMOKE_TESTS_VALORIS == "3.8.63" else "FALHA",
            "detalhe": VERSAO_API_SMOKE_TESTS_VALORIS,
        },
        {
            "teste": "score_smoke",
            "status": "OK" if 0 <= saude["score_smoke"] <= 100 else "FALHA",
            "detalhe": str(saude["score_smoke"]),
        },
        {
            "teste": "renderizador",
            "status": "OK" if callable(renderizar_api_smoke_tests_valoris) else "FALHA",
            "detalhe": "renderizar_api_smoke_tests_valoris",
        },
    ]
