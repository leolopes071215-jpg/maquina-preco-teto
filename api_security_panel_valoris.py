# api_security_panel_valoris.py

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

import streamlit as st

from api_security_key_valoris import (
    API_KEY_HEADER_NAME,
    DEFAULT_LOCAL_API_KEY,
    CAMINHO_MANIFESTO_API_SECURITY,
    calcular_saude_api_security,
    testar_api_key_local,
)
from api_storage_adapter_valoris import calcular_saude_api_adapter
from api_endpoint_tests_valoris import calcular_saude_api_endpoint_tests
from api_smoke_tests_valoris import testar_health_api


VERSAO_API_SECURITY_PANEL_VALORIS = "3.8.69"

CAMINHO_DECISOES_API_SECURITY_PANEL = Path("decisoes_api_security_panel_valoris.csv")
CAMINHO_MANIFESTO_API_SECURITY_PANEL = Path("manifesto_api_security_panel_valoris.json")
CAMINHO_RELATORIO_API_TESTS = Path("relatorio_api_tests_valoris.json")
CAMINHO_README_API = Path("api_valoris/README.md")
CAMINHO_SECURITY_CORE = Path("api_valoris/app/core/security.py")
CAMINHO_ROUTES_LEADS = Path("api_valoris/app/routes/leads.py")
CAMINHO_ROUTES_EVENTS = Path("api_valoris/app/routes/events.py")
CAMINHO_ENV_EXAMPLE = Path("api_valoris/.env.example")

CAMPOS_DECISAO_SECURITY_PANEL = [
    "id",
    "data_registro",
    "score_panel",
    "score_security",
    "score_adapter",
    "score_tests",
    "api_online",
    "security_aplicada",
    "protected_ok",
    "public_ok",
    "api_key_default",
    "risco",
    "decisao",
    "proximo_passo",
    "observacoes",
]


ENDPOINTS_GOVERNANCA = [
    {
        "endpoint": "GET /health",
        "classificacao": "Público/local",
        "api_key": "Não exige",
        "motivo": "Permite verificar se a API está viva sem expor dados sensíveis.",
        "risco": "Baixo",
    },
    {
        "endpoint": "POST /leads",
        "classificacao": "Público/local",
        "api_key": "Não exige nesta fase",
        "motivo": "Captura leads de página pública. Futuramente pode receber rate limit e captcha.",
        "risco": "Médio",
    },
    {
        "endpoint": "GET /leads",
        "classificacao": "Protegido",
        "api_key": "Exige",
        "motivo": "Retorna dados de leads e não deve ficar aberto.",
        "risco": "Alto se público",
    },
    {
        "endpoint": "GET /leads/storage-health",
        "classificacao": "Protegido",
        "api_key": "Exige",
        "motivo": "Revela detalhes internos de armazenamento e contadores.",
        "risco": "Médio se público",
    },
    {
        "endpoint": "GET /leads/security",
        "classificacao": "Protegido",
        "api_key": "Exige",
        "motivo": "Revela status da chave e configuração de segurança.",
        "risco": "Médio se público",
    },
    {
        "endpoint": "POST /events",
        "classificacao": "Protegido",
        "api_key": "Exige",
        "motivo": "Grava eventos internos de analytics e deve evitar spam/contaminação.",
        "risco": "Médio/alto se público",
    },
    {
        "endpoint": "GET /events/storage-health",
        "classificacao": "Protegido",
        "api_key": "Exige",
        "motivo": "Expõe estado do armazenamento de eventos.",
        "risco": "Médio se público",
    },
]


CHECKLIST_HARDENING = [
    {
        "item": "API Key local aplicada",
        "criterio": "Endpoints sensíveis bloqueiam sem chave e liberam com chave.",
        "prioridade": "Obrigatório",
    },
    {
        "item": "Chave padrão substituída antes de produção",
        "criterio": "VALORIS_API_KEY deve ser forte e vir de variável de ambiente.",
        "prioridade": "Obrigatório antes de deploy",
    },
    {
        "item": "Dados locais fora do Git",
        "criterio": "CSV, SQLite, manifestos e decisões locais devem estar no .gitignore.",
        "prioridade": "Obrigatório",
    },
    {
        "item": "Rate limit para endpoints públicos",
        "criterio": "POST /leads deve ter limite por IP/sessão em produção.",
        "prioridade": "Alta",
    },
    {
        "item": "Logs técnicos sem dados sensíveis",
        "criterio": "Logs não devem imprimir API Key, e-mails completos ou dados pessoais desnecessários.",
        "prioridade": "Alta",
    },
    {
        "item": "HTTPS no deploy",
        "criterio": "Nenhuma chamada com dados reais deve trafegar sem TLS.",
        "prioridade": "Obrigatório antes de produção",
    },
    {
        "item": "Separação dev/prod",
        "criterio": "Banco, secrets e variáveis devem ser diferentes entre ambiente local e produção.",
        "prioridade": "Alta",
    },
    {
        "item": "Backup e migração de dados",
        "criterio": "Antes de Supabase/PostgreSQL, definir migração controlada do SQLite/CSV.",
        "prioridade": "Média/alta",
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


def carregar_decisoes_api_security_panel() -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_DECISOES_API_SECURITY_PANEL, CAMPOS_DECISAO_SECURITY_PANEL)

    with CAMINHO_DECISOES_API_SECURITY_PANEL.open("r", newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def gerar_csv_decisoes_api_security_panel() -> str:
    _garantir_csv(CAMINHO_DECISOES_API_SECURITY_PANEL, CAMPOS_DECISAO_SECURITY_PANEL)
    return CAMINHO_DECISOES_API_SECURITY_PANEL.read_text(encoding="utf-8")


def salvar_decisao_api_security_panel(decisao: Dict[str, Any]) -> Dict[str, str]:
    _garantir_csv(CAMINHO_DECISOES_API_SECURITY_PANEL, CAMPOS_DECISAO_SECURITY_PANEL)

    registro = {
        "id": str(uuid4())[:8],
        "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score_panel": str(decisao.get("score_panel", "")),
        "score_security": str(decisao.get("score_security", "")),
        "score_adapter": str(decisao.get("score_adapter", "")),
        "score_tests": str(decisao.get("score_tests", "")),
        "api_online": str(decisao.get("api_online", "")),
        "security_aplicada": str(decisao.get("security_aplicada", "")),
        "protected_ok": str(decisao.get("protected_ok", "")),
        "public_ok": str(decisao.get("public_ok", "")),
        "api_key_default": str(decisao.get("api_key_default", "")),
        "risco": _limpar_texto(decisao.get("risco", "")),
        "decisao": _limpar_texto(decisao.get("decisao", "")),
        "proximo_passo": _limpar_texto(decisao.get("proximo_passo", "")),
        "observacoes": _limpar_texto(decisao.get("observacoes", "")),
    }

    with CAMINHO_DECISOES_API_SECURITY_PANEL.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISAO_SECURITY_PANEL)
        escritor.writerow(registro)

    return registro


def _arquivo_contem(caminho: Path, termos: List[str]) -> bool:
    if not caminho.exists():
        return False

    conteudo = caminho.read_text(encoding="utf-8", errors="ignore")
    return all(termo in conteudo for termo in termos)


def _carregar_json_seguro(caminho: Path) -> Dict[str, Any]:
    if not caminho.exists():
        return {}

    try:
        return json.loads(caminho.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return {}


def _detectar_api_key_default() -> bool:
    if not CAMINHO_SECURITY_CORE.exists():
        return False

    conteudo = CAMINHO_SECURITY_CORE.read_text(encoding="utf-8", errors="ignore")
    return DEFAULT_LOCAL_API_KEY in conteudo


def _avaliar_arquivos_seguranca() -> List[Dict[str, Any]]:
    arquivos = [
        {
            "arquivo": str(CAMINHO_SECURITY_CORE),
            "objetivo": "Define header, chave local e dependência require_api_key.",
            "termos": ["require_api_key", API_KEY_HEADER_NAME],
        },
        {
            "arquivo": str(CAMINHO_ROUTES_LEADS),
            "objetivo": "Protege leitura de leads e health interno de storage.",
            "termos": ["Depends(require_api_key)", "storage_health", "security_status"],
        },
        {
            "arquivo": str(CAMINHO_ROUTES_EVENTS),
            "objetivo": "Protege gravação de eventos e health interno de events.",
            "termos": ["Depends(require_api_key)", "create_event"],
        },
        {
            "arquivo": str(CAMINHO_ENV_EXAMPLE),
            "objetivo": "Documenta variáveis locais da API.",
            "termos": ["VALORIS_API_KEY", "VALORIS_STORAGE_MODE"],
        },
    ]

    avaliacao = []

    for item in arquivos:
        caminho = Path(item["arquivo"])
        existe = caminho.exists()
        contem = _arquivo_contem(caminho, item["termos"]) if existe else False
        avaliacao.append(
            {
                "arquivo": item["arquivo"],
                "objetivo": item["objetivo"],
                "existe": existe,
                "validado": contem,
                "tamanho_bytes": caminho.stat().st_size if existe else 0,
            }
        )

    return avaliacao


def calcular_matriz_risco_api() -> List[Dict[str, Any]]:
    matriz = []

    for endpoint in ENDPOINTS_GOVERNANCA:
        risco_base = endpoint["risco"]

        if endpoint["classificacao"] == "Protegido":
            status = "Controlado se API Key estiver ativa"
            severidade = "Alta" if "Alto" in risco_base else "Média"
        elif endpoint["endpoint"] == "POST /leads":
            status = "Aceitável no beta, mas exige rate limit antes de produção"
            severidade = "Média"
        else:
            status = "Aceitável"
            severidade = "Baixa"

        matriz.append(
            {
                "Endpoint": endpoint["endpoint"],
                "Classificação": endpoint["classificacao"],
                "API Key": endpoint["api_key"],
                "Risco sem controle": risco_base,
                "Severidade": severidade,
                "Status recomendado": status,
                "Motivo": endpoint["motivo"],
            }
        )

    return matriz


def calcular_saude_api_security_panel() -> Dict[str, Any]:
    try:
        security = calcular_saude_api_security()
    except Exception as erro:
        security = {
            "score_security": 0,
            "security_aplicada": False,
            "health_ok": False,
            "protected_ok": False,
            "public_ok": False,
            "erro": str(erro),
        }

    try:
        adapter = calcular_saude_api_adapter()
    except Exception as erro:
        adapter = {"score_adapter": 0, "erro": str(erro)}

    try:
        endpoint_tests = calcular_saude_api_endpoint_tests()
    except Exception as erro:
        endpoint_tests = {"score_tests": 0, "erro": str(erro)}

    health = testar_health_api()

    arquivos = _avaliar_arquivos_seguranca()
    arquivos_validos = len([item for item in arquivos if item["validado"]])
    arquivos_total = len(arquivos)

    score_security = int(security.get("score_security", 0) or 0)
    score_adapter = int(adapter.get("score_adapter", 0) or 0)
    score_tests = int(endpoint_tests.get("score_tests", 0) or 0)

    api_key_default = _detectar_api_key_default()

    manifesto_security = _carregar_json_seguro(CAMINHO_MANIFESTO_API_SECURITY)
    relatorio_tests = _carregar_json_seguro(CAMINHO_RELATORIO_API_TESTS)

    checklist_preenchido = 0
    checklist_total = len(CHECKLIST_HARDENING)

    if security.get("security_aplicada"):
        checklist_preenchido += 1
    if not api_key_default:
        checklist_preenchido += 1
    if health.get("health_ok"):
        checklist_preenchido += 1
    if security.get("protected_ok"):
        checklist_preenchido += 1
    if security.get("public_ok"):
        checklist_preenchido += 1
    if arquivos_validos >= 3:
        checklist_preenchido += 1

    score = 12
    score += min(score_security * 0.35, 35)
    score += min(score_adapter * 0.12, 12)
    score += min(score_tests * 0.10, 10)
    score += 10 if health.get("health_ok") else 0
    score += min((arquivos_validos / max(arquivos_total, 1)) * 16, 16)
    score += 8 if manifesto_security else 0
    score += 7 if relatorio_tests else 0
    score = int(round(max(0, min(100, score))))

    if not security.get("security_aplicada"):
        risco = "Alto"
        decisao = "Segurança ainda não aplicada"
        proximo_passo = "Aplicar API Key local na aba API Security."
    elif not security.get("protected_ok"):
        risco = "Médio/alto"
        decisao = "Segurança aplicada, mas falta validação dos bloqueios"
        proximo_passo = "Reiniciar a API, testar endpoints sem chave e com chave."
    elif api_key_default:
        risco = "Médio"
        decisao = "Seguro para beta local, ainda não pronto para produção"
        proximo_passo = "Antes de deploy, trocar VALORIS_API_KEY por uma chave forte via variável de ambiente."
    elif score >= 86:
        risco = "Baixo/médio"
        decisao = "Governança de API aprovada para próxima etapa técnica"
        proximo_passo = "Avançar para preparação Supabase/PostgreSQL com cautela."
    else:
        risco = "Médio"
        decisao = "Governança em progresso"
        proximo_passo = "Completar checklist de hardening antes de conectar serviços externos."

    return {
        "score_panel": score,
        "score_security": score_security,
        "score_adapter": score_adapter,
        "score_tests": score_tests,
        "api_online": bool(health.get("health_ok")),
        "security_aplicada": bool(security.get("security_aplicada")),
        "protected_ok": bool(security.get("protected_ok")),
        "public_ok": bool(security.get("public_ok")),
        "api_key_default": api_key_default,
        "arquivos": arquivos,
        "arquivos_validos": arquivos_validos,
        "arquivos_total": arquivos_total,
        "checklist_preenchido": checklist_preenchido,
        "checklist_total": checklist_total,
        "manifesto_security_existe": bool(manifesto_security),
        "relatorio_tests_existe": bool(relatorio_tests),
        "security": security,
        "adapter": adapter,
        "endpoint_tests": endpoint_tests,
        "health": health,
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo_passo,
    }


def gerar_manifesto_api_security_panel() -> Dict[str, Any]:
    saude = calcular_saude_api_security_panel()

    manifesto = {
        "versao": VERSAO_API_SECURITY_PANEL_VALORIS,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "saude": saude,
        "endpoints": ENDPOINTS_GOVERNANCA,
        "matriz_risco": calcular_matriz_risco_api(),
        "checklist_hardening": CHECKLIST_HARDENING,
        "recomendacao": {
            "antes_de_supabase": [
                "Manter CSV/SQLite locais no .gitignore.",
                "Validar que endpoints protegidos retornam 401 sem chave.",
                "Validar que endpoints protegidos retornam 200 com X-Valoris-API-Key.",
                "Trocar a chave padrão por variável de ambiente forte antes de qualquer deploy público.",
                "Documentar quais dados podem sair do ambiente local.",
            ],
            "antes_de_producao": [
                "HTTPS obrigatório.",
                "Rate limit em POST /leads.",
                "Segredos fora do Git e fora do código.",
                "Separação clara entre dev, staging e produção.",
                "Política de backup e migração.",
            ],
        },
    }

    CAMINHO_MANIFESTO_API_SECURITY_PANEL.write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return manifesto


def _gerar_markdown_security_panel(saude: Dict[str, Any]) -> str:
    linhas_endpoints = "\n".join(
        [
            f"- **{item['endpoint']}** — {item['classificacao']} — API Key: {item['api_key']}"
            for item in ENDPOINTS_GOVERNANCA
        ]
    )

    linhas_checklist = "\n".join(
        [
            f"- **{item['prioridade']}** — {item['item']}: {item['criterio']}"
            for item in CHECKLIST_HARDENING
        ]
    )

    return f"""# Painel de Segurança da API — Valoris

Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Diagnóstico executivo

Score Panel: {saude["score_panel"]}/100  
Score Security: {saude["score_security"]}/100  
Score Adapter: {saude["score_adapter"]}/100  
Score Tests: {saude["score_tests"]}/100  

Risco atual: {saude["risco"]}  
Decisão: {saude["decisao"]}  
Próximo passo: {saude["proximo_passo"]}

## Estado operacional

API online: {saude["api_online"]}  
Security aplicada: {saude["security_aplicada"]}  
Proteção validada: {saude["protected_ok"]}  
Endpoints públicos OK: {saude["public_ok"]}  
Usando chave padrão local: {saude["api_key_default"]}

## Header local

`{API_KEY_HEADER_NAME}: {DEFAULT_LOCAL_API_KEY}`

## Endpoints

{linhas_endpoints}

## Checklist de hardening

{linhas_checklist}

## Comando de teste sem chave

```powershell
try {{
    Invoke-RestMethod -Uri "http://127.0.0.1:8000/leads/storage-health" -Method GET
}} catch {{
    $_.Exception.Response.StatusCode.value__
}}
```

## Comando de teste com chave

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/leads/storage-health" -Headers @{{"X-Valoris-API-Key"="valoris-local-dev-key"}} -Method GET
```
"""


def _injetar_css_security_panel() -> None:
    st.markdown(
        """
        <style>
            .security-panel-hero {
                padding: clamp(1.2rem, 3vw, 2.05rem);
                border-radius: 30px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    radial-gradient(circle at top left, rgba(214, 181, 109, 0.24), transparent 32%),
                    radial-gradient(circle at bottom right, rgba(38, 120, 98, 0.20), transparent 36%),
                    linear-gradient(135deg, rgba(6, 12, 23, 0.99), rgba(4, 8, 16, 0.99));
                box-shadow: 0 20px 62px rgba(0, 0, 0, 0.34);
                margin-bottom: 1rem;
            }

            .security-panel-eyebrow {
                color: #d6b56d;
                font-size: 0.74rem;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                font-weight: 880;
                margin-bottom: 0.35rem;
            }

            .security-panel-title {
                color: #f4f7fb;
                font-size: clamp(1.8rem, 5.5vw, 3.2rem);
                font-weight: 950;
                line-height: 1.02;
                letter-spacing: -0.058em;
                margin-bottom: 0.55rem;
            }

            .security-panel-subtitle {
                color: rgba(244, 247, 251, 0.75);
                font-size: clamp(0.94rem, 2.2vw, 1.06rem);
                line-height: 1.56;
                max-width: 1050px;
            }

            .security-panel-note {
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


def renderizar_api_security_panel_valoris() -> None:
    _injetar_css_security_panel()

    st.markdown(
        f"""
        <div class="security-panel-hero">
            <div class="security-panel-eyebrow">Valoris • API Governance • v{VERSAO_API_SECURITY_PANEL_VALORIS}</div>
            <div class="security-panel-title">Painel de Segurança da API.</div>
            <div class="security-panel-subtitle">
                Uma visão executiva e técnica dos endpoints públicos, endpoints protegidos, riscos,
                checklist de hardening e prontidão antes de Supabase/PostgreSQL.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    saude = calcular_saude_api_security_panel()

    st.markdown("### Visão executiva")
    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Score Panel", f"{saude['score_panel']}/100")

    with col_2:
        st.metric("Risco", saude["risco"])

    with col_3:
        st.metric("API", "Online" if saude["api_online"] else "Offline")

    with col_4:
        st.metric("Proteção", "OK" if saude["protected_ok"] else "Pendente")

    st.progress(saude["score_panel"] / 100)

    if saude["score_panel"] >= 86 and saude["protected_ok"]:
        st.success(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    elif saude["score_panel"] >= 65:
        st.warning(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    else:
        st.info(f"**{saude['decisao']}** — {saude['proximo_passo']}")

    st.divider()

    st.markdown("### Scores técnicos")
    col_a, col_b, col_c, col_d = st.columns(4)

    with col_a:
        st.metric("Security", f"{saude['score_security']}/100")

    with col_b:
        st.metric("Adapter", f"{saude['score_adapter']}/100")

    with col_c:
        st.metric("Endpoint Tests", f"{saude['score_tests']}/100")

    with col_d:
        st.metric(
            "Checklist",
            f"{saude['checklist_preenchido']}/{saude['checklist_total']}",
        )

    st.markdown(
        """
        <div class="security-panel-note">
            <strong>Leitura correta:</strong> chave padrão local é aceitável no beta local,
            mas não é aceitável em deploy público. Antes de produção, use uma variável de ambiente forte.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    st.markdown("### Governança dos endpoints")
    st.dataframe(calcular_matriz_risco_api(), use_container_width=True, hide_index=True)

    st.markdown("### Checklist de hardening")
    st.dataframe(CHECKLIST_HARDENING, use_container_width=True, hide_index=True)

    st.divider()

    col_btn_1, col_btn_2, col_btn_3 = st.columns(3)

    with col_btn_1:
        if st.button("Rodar teste de segurança", key="security_panel_rodar_teste"):
            resultado = testar_api_key_local()
            st.session_state["resultado_security_panel_teste"] = resultado
            if resultado["ok"]:
                st.success(f"Teste aprovado: {resultado['ok_count']}/{resultado['total']}")
            else:
                st.warning(f"Teste com falhas: {resultado['ok_count']}/{resultado['total']}")

    with col_btn_2:
        if st.button("Gerar manifesto do painel", key="security_panel_manifesto"):
            manifesto = gerar_manifesto_api_security_panel()
            st.success(f"Manifesto gerado: {CAMINHO_MANIFESTO_API_SECURITY_PANEL}")
            st.json(
                {
                    "versao": manifesto["versao"],
                    "score_panel": manifesto["saude"]["score_panel"],
                    "risco": manifesto["saude"]["risco"],
                }
            )

    with col_btn_3:
        if st.button("Salvar decisão do painel", key="security_panel_decisao"):
            registro = salvar_decisao_api_security_panel(
                {
                    "score_panel": saude["score_panel"],
                    "score_security": saude["score_security"],
                    "score_adapter": saude["score_adapter"],
                    "score_tests": saude["score_tests"],
                    "api_online": saude["api_online"],
                    "security_aplicada": saude["security_aplicada"],
                    "protected_ok": saude["protected_ok"],
                    "public_ok": saude["public_ok"],
                    "api_key_default": saude["api_key_default"],
                    "risco": saude["risco"],
                    "decisao": saude["decisao"],
                    "proximo_passo": saude["proximo_passo"],
                    "observacoes": "Decisão gerada pelo painel de governança de segurança da API.",
                }
            )
            st.success(f"Decisão salva: {registro['decisao']}")
            st.rerun()

    st.download_button(
        "Baixar diagnóstico do painel (.md)",
        data=_gerar_markdown_security_panel(saude),
        file_name="api_security_panel_valoris.md",
        mime="text/markdown",
        key="download_security_panel_md",
    )

    st.download_button(
        "Baixar decisões do painel (.csv)",
        data=gerar_csv_decisoes_api_security_panel(),
        file_name="decisoes_api_security_panel_valoris.csv",
        mime="text/csv",
        key="download_security_panel_csv",
    )

    st.divider()

    st.markdown("### Resultado do último teste de segurança")
    resultado_teste = st.session_state.get("resultado_security_panel_teste")
    if resultado_teste:
        st.json(resultado_teste)
    else:
        st.info("Clique em 'Rodar teste de segurança' com a API ligada para validar o bloqueio e liberação por chave.")

    st.divider()

    st.markdown("### Arquivos críticos de segurança")
    for item in saude["arquivos"]:
        with st.container(border=True):
            st.markdown(f"**{item['arquivo']}**")
            st.caption(item["objetivo"])
            st.markdown(
                f"Existe: **{item['existe']}** · Validado: **{item['validado']}** · Tamanho: **{item['tamanho_bytes']} bytes**"
            )

    with st.expander("Ver diagnóstico bruto"):
        st.json(saude)

    with st.expander("Comandos PowerShell de validação"):
        comandos = """
# Sem chave: deve retornar 401
try {
    Invoke-RestMethod -Uri "http://127.0.0.1:8000/leads/storage-health" -Method GET
} catch {
    $_.Exception.Response.StatusCode.value__
}

# Com chave: deve liberar
Invoke-RestMethod -Uri "http://127.0.0.1:8000/leads/storage-health" -Headers @{"X-Valoris-API-Key"="valoris-local-dev-key"} -Method GET
        """.strip()
        st.code(comandos, language="powershell")


def executar_autoteste_api_security_panel_valoris() -> List[Dict[str, str]]:
    saude = calcular_saude_api_security_panel()

    return [
        {
            "teste": "versao_security_panel",
            "status": "OK" if VERSAO_API_SECURITY_PANEL_VALORIS == "3.8.69" else "FALHA",
            "detalhe": VERSAO_API_SECURITY_PANEL_VALORIS,
        },
        {
            "teste": "score_panel",
            "status": "OK" if 0 <= saude["score_panel"] <= 100 else "FALHA",
            "detalhe": str(saude["score_panel"]),
        },
        {
            "teste": "renderizador",
            "status": "OK" if callable(renderizar_api_security_panel_valoris) else "FALHA",
            "detalhe": "renderizar_api_security_panel_valoris",
        },
        {
            "teste": "matriz_risco",
            "status": "OK" if len(calcular_matriz_risco_api()) >= 5 else "FALHA",
            "detalhe": str(len(calcular_matriz_risco_api())),
        },
    ]
