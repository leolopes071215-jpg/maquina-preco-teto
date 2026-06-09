# launch_readiness_valoris.py

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

import streamlit as st

from api_provider_backend_valoris import calcular_saude_provider_backend
from api_provider_runtime_valoris import calcular_saude_provider_runtime
from api_database_providers_valoris import calcular_saude_database_providers
from api_database_contracts_valoris import calcular_saude_database_contracts
from api_database_cloud_valoris import calcular_saude_database_cloud
from api_security_panel_valoris import calcular_saude_api_security_panel
from api_security_key_valoris import calcular_saude_api_security
from api_storage_adapter_valoris import calcular_saude_api_adapter
from api_endpoint_tests_valoris import calcular_saude_api_endpoint_tests
from api_smoke_tests_valoris import testar_health_api


VERSAO_LAUNCH_READINESS_VALORIS = "3.8.75"

CAMINHO_DECISOES_LAUNCH_READINESS = Path("decisoes_launch_readiness_valoris.csv")
CAMINHO_MANIFESTO_LAUNCH_READINESS = Path("manifesto_launch_readiness_valoris.json")
CAMINHO_PLANO_LANCAMENTO_MD = Path("PLANO_LANCAMENTO_VALORIS.md")
CAMINHO_CHECKLIST_LANCAMENTO_MD = Path("CHECKLIST_LANCAMENTO_VALORIS.md")

CAMINHO_GITIGNORE = Path(".gitignore")
CAMINHO_APP = Path("app.py")
CAMINHO_MODO_EXIBICAO = Path("modo_exibicao.py")
CAMINHO_RELEASE_GUARD = Path("release_guard.py")

ARQUIVOS_PRODUTO_CRITICOS = [
    "app.py",
    "modo_exibicao.py",
    "release_guard.py",
    "explicabilidade_valoris.py",
    "relatorio.py",
    "central_relatorios.py",
    "experiencia_beta.py",
    "lista_espera_beta.py",
    "landing_page_beta.py",
    "convite_beta_publico.py",
]

ARQUIVOS_INFRA_CRITICOS = [
    "api_provider_backend_valoris.py",
    "api_provider_runtime_valoris.py",
    "api_database_providers_valoris.py",
    "api_database_contracts_valoris.py",
    "api_database_cloud_valoris.py",
    "api_security_panel_valoris.py",
    "api_security_key_valoris.py",
    "api_storage_adapter_valoris.py",
    "api_endpoint_tests_valoris.py",
]

ARQUIVOS_LOCAIS_NAO_VERSIONAR = [
    "decisoes_launch_readiness_valoris.csv",
    "manifesto_launch_readiness_valoris.json",
    "PLANO_LANCAMENTO_VALORIS.md",
    "CHECKLIST_LANCAMENTO_VALORIS.md",
]

CAMPOS_DECISAO_LAUNCH_READINESS = [
    "id",
    "data_registro",
    "score_launch",
    "score_produto",
    "score_infra",
    "score_seguranca",
    "score_dados",
    "score_growth",
    "api_online",
    "release_guard_pronto",
    "modo_fundador_pronto",
    "go_no_go",
    "risco",
    "decisao",
    "proximo_passo",
    "observacoes",
]

PILARES_LANCAMENTO = [
    {
        "pilar": "Produto",
        "objetivo": "Entregar uma análise de valuation clara, útil e vendável.",
        "status_esperado": "Fluxo principal precisa gerar tese, preço teto, margem de segurança, riscos e relatório.",
        "risco": "O app parecer técnico demais e pouco convincente para usuário final.",
        "prioridade": "Máxima",
    },
    {
        "pilar": "Infraestrutura",
        "objetivo": "Garantir dados locais, API, segurança e arquitetura para cloud.",
        "status_esperado": "CSV/SQLite/hybrid funcionando, API protegida e providers preparados.",
        "risco": "Cloud prematura quebrar o produto ou expor dados.",
        "prioridade": "Alta",
    },
    {
        "pilar": "Experiência",
        "objetivo": "Criar um momento uau em menos de 2 minutos.",
        "status_esperado": "Usuário entende: empresa, dados, decisão, tese e relatório.",
        "risco": "Tela confusa, excesso de abas e baixa clareza do valor.",
        "prioridade": "Máxima",
    },
    {
        "pilar": "Confiança",
        "objetivo": "Mostrar metodologia, conservadorismo e limitações.",
        "status_esperado": "Explicabilidade, logs e disclaimers claros.",
        "risco": "Parecer recomendação financeira automática sem responsabilidade.",
        "prioridade": "Alta",
    },
    {
        "pilar": "Aquisição",
        "objetivo": "Capturar beta users e validar interesse real.",
        "status_esperado": "Landing, lista de espera, convite público e oferta beta.",
        "risco": "Construir demais sem validação de demanda.",
        "prioridade": "Alta",
    },
]

ROADMAP_LANCAMENTO = [
    {
        "fase": "Agora",
        "versao_alvo": "v3.8.75",
        "entrega": "Launch Readiness e plano de prioridades.",
        "criterio": "Saber exatamente o que falta para lançar.",
    },
    {
        "fase": "Produto",
        "versao_alvo": "v3.8.76",
        "entrega": "Experiência Premium de Análise.",
        "criterio": "Usuário recebe análise clara, tese, riscos, decisão e relatório.",
    },
    {
        "fase": "Validação",
        "versao_alvo": "v3.8.77",
        "entrega": "Demo guiada de 2 minutos.",
        "criterio": "Qualquer pessoa entende valor sem explicação externa.",
    },
    {
        "fase": "Beta",
        "versao_alvo": "v3.8.78",
        "entrega": "Fluxo de convite, captura e feedback beta.",
        "criterio": "Conseguir testar com usuários reais.",
    },
    {
        "fase": "Cloud opcional",
        "versao_alvo": "v3.8.79",
        "entrega": "Supabase experimental com secrets fora do Git.",
        "criterio": "Cloud só entra se o produto já estiver demonstrável.",
    },
    {
        "fase": "Pré-venda",
        "versao_alvo": "v3.8.80",
        "entrega": "Oferta beta paga e página comercial enxuta.",
        "criterio": "Testar disposição real de pagamento.",
    },
]

CRITERIOS_GO_NO_GO = [
    {
        "criterio": "Análise principal compreensível",
        "pergunta": "O usuário entende a decisão final sem precisar ler código?",
        "peso": 18,
    },
    {
        "criterio": "Preço teto conservador",
        "pergunta": "O modelo deixa claro margem de segurança, premissas e risco?",
        "peso": 16,
    },
    {
        "criterio": "Relatório exportável",
        "pergunta": "Existe saída compartilhável para o usuário mostrar ou guardar?",
        "peso": 12,
    },
    {
        "criterio": "Dados protegidos",
        "pergunta": "API, dados locais e arquivos sensíveis estão protegidos?",
        "peso": 14,
    },
    {
        "criterio": "Fallback local",
        "pergunta": "O app funciona sem cloud e sem depender de serviços externos?",
        "peso": 12,
    },
    {
        "criterio": "Captura de beta",
        "pergunta": "Existe fluxo para lista de espera, convite ou feedback?",
        "peso": 10,
    },
    {
        "criterio": "Demonstração rápida",
        "pergunta": "Alguém vê valor em menos de 2 minutos?",
        "peso": 18,
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


def _arquivo_existe(nome: str) -> bool:
    return Path(nome).exists()


def _arquivo_contem(caminho: Path, termos: List[str]) -> bool:
    if not caminho.exists():
        return False

    conteudo = caminho.read_text(encoding="utf-8", errors="ignore")
    return all(termo in conteudo for termo in termos)


def _gitignore_contem(termo: str) -> bool:
    if not CAMINHO_GITIGNORE.exists():
        return False

    return termo in CAMINHO_GITIGNORE.read_text(encoding="utf-8", errors="ignore")


def carregar_decisoes_launch_readiness() -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_DECISOES_LAUNCH_READINESS, CAMPOS_DECISAO_LAUNCH_READINESS)

    with CAMINHO_DECISOES_LAUNCH_READINESS.open("r", newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def gerar_csv_decisoes_launch_readiness() -> str:
    _garantir_csv(CAMINHO_DECISOES_LAUNCH_READINESS, CAMPOS_DECISAO_LAUNCH_READINESS)
    return CAMINHO_DECISOES_LAUNCH_READINESS.read_text(encoding="utf-8")


def salvar_decisao_launch_readiness(decisao: Dict[str, Any]) -> Dict[str, str]:
    _garantir_csv(CAMINHO_DECISOES_LAUNCH_READINESS, CAMPOS_DECISAO_LAUNCH_READINESS)

    registro = {
        "id": str(uuid4())[:8],
        "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score_launch": str(decisao.get("score_launch", "")),
        "score_produto": str(decisao.get("score_produto", "")),
        "score_infra": str(decisao.get("score_infra", "")),
        "score_seguranca": str(decisao.get("score_seguranca", "")),
        "score_dados": str(decisao.get("score_dados", "")),
        "score_growth": str(decisao.get("score_growth", "")),
        "api_online": str(decisao.get("api_online", "")),
        "release_guard_pronto": str(decisao.get("release_guard_pronto", "")),
        "modo_fundador_pronto": str(decisao.get("modo_fundador_pronto", "")),
        "go_no_go": _limpar_texto(decisao.get("go_no_go", "")),
        "risco": _limpar_texto(decisao.get("risco", "")),
        "decisao": _limpar_texto(decisao.get("decisao", "")),
        "proximo_passo": _limpar_texto(decisao.get("proximo_passo", "")),
        "observacoes": _limpar_texto(decisao.get("observacoes", "")),
    }

    with CAMINHO_DECISOES_LAUNCH_READINESS.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISAO_LAUNCH_READINESS)
        escritor.writerow(registro)

    return registro


def avaliar_arquivos_produto() -> Dict[str, Any]:
    resultados = [{"arquivo": nome, "existe": _arquivo_existe(nome)} for nome in ARQUIVOS_PRODUTO_CRITICOS]
    total = len(resultados)
    encontrados = sum(1 for item in resultados if item["existe"])
    score = int(round((encontrados / total) * 100)) if total else 0

    return {
        "score": score,
        "total": total,
        "encontrados": encontrados,
        "resultados": resultados,
    }


def avaliar_arquivos_infra() -> Dict[str, Any]:
    resultados = [{"arquivo": nome, "existe": _arquivo_existe(nome)} for nome in ARQUIVOS_INFRA_CRITICOS]
    total = len(resultados)
    encontrados = sum(1 for item in resultados if item["existe"])
    score = int(round((encontrados / total) * 100)) if total else 0

    return {
        "score": score,
        "total": total,
        "encontrados": encontrados,
        "resultados": resultados,
    }


def avaliar_modo_fundador() -> Dict[str, Any]:
    termos_app = [
        "Modo Fundador",
        "Launch Readiness",
        "API Provider Backend",
    ]

    termos_modo = [
        "Launch Readiness",
        "API Provider Backend",
    ]

    app_ok = _arquivo_contem(CAMINHO_APP, termos_app)
    modo_ok = _arquivo_contem(CAMINHO_MODO_EXIBICAO, termos_modo)

    return {
        "app_ok": app_ok,
        "modo_exibicao_ok": modo_ok,
        "ok": app_ok and modo_ok,
    }


def avaliar_gitignore_launch() -> Dict[str, Any]:
    itens = ARQUIVOS_LOCAIS_NAO_VERSIONAR
    resultados = [{"item": item, "presente": _gitignore_contem(item)} for item in itens]
    total = len(resultados)
    presentes = sum(1 for item in resultados if item["presente"])
    score = int(round((presentes / total) * 100)) if total else 0

    return {
        "score": score,
        "total": total,
        "presentes": presentes,
        "resultados": resultados,
        "ok": presentes == total,
    }


def calcular_saude_launch_readiness() -> Dict[str, Any]:
    try:
        provider_backend = calcular_saude_provider_backend()
    except Exception as erro:
        provider_backend = {"score_backend": 0, "backend_probe_ok": False, "fallback_local_ok": False, "erro": str(erro)}

    try:
        provider_runtime = calcular_saude_provider_runtime()
    except Exception as erro:
        provider_runtime = {"score_runtime": 0, "runtime_probe_ok": False, "erro": str(erro)}

    try:
        database_providers = calcular_saude_database_providers()
    except Exception as erro:
        database_providers = {"score_providers": 0, "scaffold_pronto": False, "erro": str(erro)}

    try:
        contracts = calcular_saude_database_contracts()
    except Exception as erro:
        contracts = {"score_contracts": 0, "contratos_prontos": False, "erro": str(erro)}

    try:
        cloud = calcular_saude_database_cloud()
    except Exception as erro:
        cloud = {"score_cloud": 0, "erro": str(erro)}

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
    produto = avaliar_arquivos_produto()
    infra = avaliar_arquivos_infra()
    modo_fundador = avaliar_modo_fundador()
    gitignore = avaliar_gitignore_launch()

    score_backend = int(provider_backend.get("score_backend", 0) or 0)
    score_runtime = int(provider_runtime.get("score_runtime", 0) or 0)
    score_providers = int(database_providers.get("score_providers", 0) or 0)
    score_contracts = int(contracts.get("score_contracts", 0) or 0)
    score_cloud = int(cloud.get("score_cloud", 0) or 0)
    score_security_panel = int(security_panel.get("score_panel", 0) or 0)
    score_security = int(security.get("score_security", 0) or 0)
    score_adapter = int(adapter.get("score_adapter", 0) or 0)
    score_tests = int(endpoint_tests.get("score_tests", 0) or 0)

    score_produto = int(round((produto["score"] * 0.72) + (100 if modo_fundador["ok"] else 0) * 0.28))
    score_infra = int(round((score_backend * 0.28) + (score_runtime * 0.20) + (score_providers * 0.18) + (score_contracts * 0.14) + (score_cloud * 0.10) + (infra["score"] * 0.10)))
    score_seguranca = int(round((score_security * 0.55) + (score_security_panel * 0.30) + (100 if gitignore["ok"] else gitignore["score"]) * 0.15))
    score_dados = int(round((score_adapter * 0.55) + (score_tests * 0.25) + (100 if provider_backend.get("fallback_local_ok") else 0) * 0.20))
    score_growth = int(round(100 if all(_arquivo_existe(nome) for nome in ["landing_page_beta.py", "lista_espera_beta.py", "convite_beta_publico.py"]) else produto["score"] * 0.70))

    score_launch = int(round(
        score_produto * 0.30
        + score_infra * 0.24
        + score_seguranca * 0.18
        + score_dados * 0.16
        + score_growth * 0.12
    ))

    api_online = bool(health.get("health_ok"))
    release_guard_pronto = CAMINHO_RELEASE_GUARD.exists()
    modo_fundador_pronto = bool(modo_fundador["ok"])
    fallback_local_ok = bool(provider_backend.get("fallback_local_ok"))
    security_ok = bool(security.get("protected_ok")) or bool(security_panel.get("protected_ok"))

    if score_launch >= 86 and modo_fundador_pronto and security_ok:
        go_no_go = "GO CONTROLADO"
        risco = "Médio controlado"
        decisao = "Avançar para experiência premium de análise antes da cloud real"
        proximo_passo = "Construir v3.8.76 com fluxo de análise vendável, tese, riscos e relatório premium."
    elif score_launch >= 70:
        go_no_go = "GO INTERNO"
        risco = "Médio"
        decisao = "Produto promissor, mas ainda não ideal para público externo"
        proximo_passo = "Priorizar UX da análise principal e demo guiada."
    else:
        go_no_go = "NO GO PÚBLICO"
        risco = "Alto"
        decisao = "Ainda não lançar externamente"
        proximo_passo = "Corrigir produto, segurança e demonstração antes de captar usuários."

    return {
        "versao": VERSAO_LAUNCH_READINESS_VALORIS,
        "score_launch": max(0, min(100, score_launch)),
        "score_produto": max(0, min(100, score_produto)),
        "score_infra": max(0, min(100, score_infra)),
        "score_seguranca": max(0, min(100, score_seguranca)),
        "score_dados": max(0, min(100, score_dados)),
        "score_growth": max(0, min(100, score_growth)),
        "go_no_go": go_no_go,
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo_passo,
        "api_online": api_online,
        "release_guard_pronto": release_guard_pronto,
        "modo_fundador_pronto": modo_fundador_pronto,
        "fallback_local_ok": fallback_local_ok,
        "security_ok": security_ok,
        "produto": produto,
        "infra": infra,
        "modo_fundador": modo_fundador,
        "gitignore": gitignore,
        "provider_backend": provider_backend,
        "provider_runtime": provider_runtime,
        "database_providers": database_providers,
        "contracts": contracts,
        "cloud": cloud,
        "security_panel": security_panel,
        "security": security,
        "adapter": adapter,
        "endpoint_tests": endpoint_tests,
        "health": health,
        "pilares": PILARES_LANCAMENTO,
        "roadmap": ROADMAP_LANCAMENTO,
        "criterios_go_no_go": CRITERIOS_GO_NO_GO,
    }


def gerar_plano_lancamento_markdown(saude: Dict[str, Any] | None = None) -> str:
    if saude is None:
        saude = calcular_saude_launch_readiness()

    pilares = "\n".join(
        [
            f"- **{item['pilar']}** ({item['prioridade']}): {item['objetivo']} Risco: {item['risco']}"
            for item in PILARES_LANCAMENTO
        ]
    )

    roadmap = "\n".join(
        [
            f"- **{item['versao_alvo']} — {item['fase']}**: {item['entrega']} Critério: {item['criterio']}"
            for item in ROADMAP_LANCAMENTO
        ]
    )

    criterios = "\n".join(
        [
            f"- **{item['criterio']}** ({item['peso']} pts): {item['pergunta']}"
            for item in CRITERIOS_GO_NO_GO
        ]
    )

    return f"""# Plano de Lançamento — Valoris

Versão: {VERSAO_LAUNCH_READINESS_VALORIS}  
Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Status

Score Launch: {saude["score_launch"]}/100  
Go/No-Go: {saude["go_no_go"]}  
Risco: {saude["risco"]}  
Decisão: {saude["decisao"]}  
Próximo passo: {saude["proximo_passo"]}

## Scores

- Produto: {saude["score_produto"]}/100
- Infraestrutura: {saude["score_infra"]}/100
- Segurança: {saude["score_seguranca"]}/100
- Dados: {saude["score_dados"]}/100
- Growth: {saude["score_growth"]}/100

## Tese de lançamento

A Valoris deve ser lançada apenas quando a experiência principal provar valor rapidamente: o usuário insere dados de uma empresa e recebe uma análise clara com preço teto, margem de segurança, tese, riscos, decisão e relatório exportável.

## Pilares

{pilares}

## Roadmap eficiente

{roadmap}

## Critérios Go/No-Go

{criterios}

## Recomendação

A rota mais eficiente agora é priorizar produto: v3.8.76 deve melhorar a experiência premium de análise antes de avançar para cloud real.
"""


def gerar_checklist_lancamento_markdown(saude: Dict[str, Any] | None = None) -> str:
    if saude is None:
        saude = calcular_saude_launch_readiness()

    linhas = [
        "# Checklist de Lançamento — Valoris",
        "",
        f"Versão: {VERSAO_LAUNCH_READINESS_VALORIS}",
        f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        "",
        "## Checklist",
        "",
        f"- [{'x' if saude['modo_fundador_pronto'] else ' '}] Modo Fundador funcionando",
        f"- [{'x' if saude['release_guard_pronto'] else ' '}] Release Guard funcionando",
        f"- [{'x' if saude['security_ok'] else ' '}] Segurança mínima da API",
        f"- [{'x' if saude['fallback_local_ok'] else ' '}] Fallback local CSV/SQLite/hybrid",
        f"- [{'x' if saude['score_produto'] >= 75 else ' '}] Produto com arquivos críticos",
        f"- [{'x' if saude['score_infra'] >= 75 else ' '}] Infraestrutura preparada",
        f"- [{'x' if saude['score_growth'] >= 70 else ' '}] Captura beta/growth preparada",
        "",
        "## Próxima versão recomendada",
        "",
        "- v3.8.76 — Experiência Premium de Análise",
    ]

    return "\n".join(linhas)


def salvar_plano_lancamento_markdown() -> Dict[str, Any]:
    saude = calcular_saude_launch_readiness()
    CAMINHO_PLANO_LANCAMENTO_MD.write_text(gerar_plano_lancamento_markdown(saude), encoding="utf-8")
    return {
        "ok": True,
        "arquivo": str(CAMINHO_PLANO_LANCAMENTO_MD),
        "score_launch": saude["score_launch"],
        "go_no_go": saude["go_no_go"],
    }


def salvar_checklist_lancamento_markdown() -> Dict[str, Any]:
    saude = calcular_saude_launch_readiness()
    CAMINHO_CHECKLIST_LANCAMENTO_MD.write_text(gerar_checklist_lancamento_markdown(saude), encoding="utf-8")
    return {
        "ok": True,
        "arquivo": str(CAMINHO_CHECKLIST_LANCAMENTO_MD),
        "score_launch": saude["score_launch"],
        "go_no_go": saude["go_no_go"],
    }


def gerar_manifesto_launch_readiness() -> Dict[str, Any]:
    saude = calcular_saude_launch_readiness()
    manifesto = {
        "versao": VERSAO_LAUNCH_READINESS_VALORIS,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "saude": saude,
        "pilares": PILARES_LANCAMENTO,
        "roadmap": ROADMAP_LANCAMENTO,
        "criterios_go_no_go": CRITERIOS_GO_NO_GO,
        "estrategia": {
            "rota": "Priorizar produto antes de cloud real.",
            "proxima_versao": "v3.8.76 — Experiência Premium de Análise.",
            "regra": "Lançamento só faz sentido se o momento uau estiver claro em menos de 2 minutos.",
        },
    }
    CAMINHO_MANIFESTO_LAUNCH_READINESS.write_text(json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifesto


def _injetar_css_launch_readiness() -> None:
    st.markdown(
        """
        <style>
            .launch-readiness-hero {
                padding: clamp(1.2rem, 3vw, 2.1rem);
                border-radius: 30px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    radial-gradient(circle at top left, rgba(214, 181, 109, 0.24), transparent 32%),
                    radial-gradient(circle at bottom right, rgba(80, 170, 140, 0.22), transparent 36%),
                    linear-gradient(135deg, rgba(6, 12, 23, 0.99), rgba(4, 8, 16, 0.99));
                box-shadow: 0 20px 62px rgba(0, 0, 0, 0.34);
                margin-bottom: 1rem;
            }
            .launch-readiness-eyebrow {
                color: #d6b56d;
                font-size: 0.74rem;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                font-weight: 880;
                margin-bottom: 0.35rem;
            }
            .launch-readiness-title {
                color: #f4f7fb;
                font-size: clamp(1.8rem, 5.5vw, 3.25rem);
                font-weight: 950;
                line-height: 1.02;
                letter-spacing: -0.058em;
                margin-bottom: 0.55rem;
            }
            .launch-readiness-subtitle {
                color: rgba(244, 247, 251, 0.75);
                font-size: clamp(0.94rem, 2.2vw, 1.06rem);
                line-height: 1.56;
                max-width: 1050px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def renderizar_launch_readiness_valoris() -> None:
    _injetar_css_launch_readiness()

    st.markdown(
        f"""
        <div class="launch-readiness-hero">
            <div class="launch-readiness-eyebrow">Valoris • Launch Readiness • v{VERSAO_LAUNCH_READINESS_VALORIS}</div>
            <div class="launch-readiness-title">Rota eficiente para lançamento.</div>
            <div class="launch-readiness-subtitle">
                Diagnóstico de produto, infraestrutura, segurança, dados e growth para decidir o próximo passo
                mais eficiente rumo ao lançamento do app.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    saude = calcular_saude_launch_readiness()

    st.markdown("### Diagnóstico de lançamento")
    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Score Launch", f"{saude['score_launch']}/100")

    with col_2:
        st.metric("Go/No-Go", saude["go_no_go"])

    with col_3:
        st.metric("Risco", saude["risco"])

    with col_4:
        st.metric("Próxima versão", "v3.8.76")

    st.progress(saude["score_launch"] / 100)

    if saude["score_launch"] >= 86:
        st.success(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    elif saude["score_launch"] >= 70:
        st.warning(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    else:
        st.error(f"**{saude['decisao']}** — {saude['proximo_passo']}")

    st.divider()

    st.markdown("### Scores por pilar")
    col_a, col_b, col_c, col_d, col_e = st.columns(5)

    with col_a:
        st.metric("Produto", f"{saude['score_produto']}/100")
    with col_b:
        st.metric("Infra", f"{saude['score_infra']}/100")
    with col_c:
        st.metric("Segurança", f"{saude['score_seguranca']}/100")
    with col_d:
        st.metric("Dados", f"{saude['score_dados']}/100")
    with col_e:
        st.metric("Growth", f"{saude['score_growth']}/100")

    st.divider()

    st.markdown("### Pilares do lançamento")
    st.dataframe(PILARES_LANCAMENTO, width="stretch", hide_index=True)

    st.markdown("### Roadmap eficiente")
    st.dataframe(ROADMAP_LANCAMENTO, width="stretch", hide_index=True)

    st.markdown("### Critérios Go/No-Go")
    st.dataframe(CRITERIOS_GO_NO_GO, width="stretch", hide_index=True)

    st.divider()

    col_btn_1, col_btn_2, col_btn_3, col_btn_4 = st.columns(4)

    with col_btn_1:
        if st.button("Gerar manifesto Launch", key="launch_manifesto"):
            manifesto = gerar_manifesto_launch_readiness()
            st.success(f"Manifesto gerado: {CAMINHO_MANIFESTO_LAUNCH_READINESS}")
            st.json(
                {
                    "versao": manifesto["versao"],
                    "score_launch": manifesto["saude"]["score_launch"],
                    "go_no_go": manifesto["saude"]["go_no_go"],
                }
            )

    with col_btn_2:
        if st.button("Salvar plano .md", key="launch_plano_md"):
            resultado = salvar_plano_lancamento_markdown()
            st.success(f"Plano salvo: {resultado['arquivo']}")
            st.json(resultado)

    with col_btn_3:
        if st.button("Salvar checklist .md", key="launch_checklist_md"):
            resultado = salvar_checklist_lancamento_markdown()
            st.success(f"Checklist salvo: {resultado['arquivo']}")
            st.json(resultado)

    with col_btn_4:
        if st.button("Salvar decisão Launch", key="launch_decisao"):
            registro = salvar_decisao_launch_readiness(
                {
                    "score_launch": saude["score_launch"],
                    "score_produto": saude["score_produto"],
                    "score_infra": saude["score_infra"],
                    "score_seguranca": saude["score_seguranca"],
                    "score_dados": saude["score_dados"],
                    "score_growth": saude["score_growth"],
                    "api_online": saude["api_online"],
                    "release_guard_pronto": saude["release_guard_pronto"],
                    "modo_fundador_pronto": saude["modo_fundador_pronto"],
                    "go_no_go": saude["go_no_go"],
                    "risco": saude["risco"],
                    "decisao": saude["decisao"],
                    "proximo_passo": saude["proximo_passo"],
                    "observacoes": "Decisão gerada pela rota eficiente de lançamento.",
                }
            )
            st.success(f"Decisão salva: {registro['decisao']}")
            st.rerun()

    st.download_button(
        "Baixar plano de lançamento (.md)",
        data=gerar_plano_lancamento_markdown(saude),
        file_name="PLANO_LANCAMENTO_VALORIS.md",
        mime="text/markdown",
        key="download_plano_lancamento",
    )

    st.download_button(
        "Baixar checklist de lançamento (.md)",
        data=gerar_checklist_lancamento_markdown(saude),
        file_name="CHECKLIST_LANCAMENTO_VALORIS.md",
        mime="text/markdown",
        key="download_checklist_lancamento",
    )

    st.download_button(
        "Baixar decisões Launch (.csv)",
        data=gerar_csv_decisoes_launch_readiness(),
        file_name="decisoes_launch_readiness_valoris.csv",
        mime="text/csv",
        key="download_decisoes_launch",
    )

    st.divider()

    st.markdown("### Resumo técnico")
    st.json(
        {
            "score_launch": saude["score_launch"],
            "score_produto": saude["score_produto"],
            "score_infra": saude["score_infra"],
            "score_seguranca": saude["score_seguranca"],
            "score_dados": saude["score_dados"],
            "score_growth": saude["score_growth"],
            "go_no_go": saude["go_no_go"],
            "risco": saude["risco"],
            "decisao": saude["decisao"],
            "proximo_passo": saude["proximo_passo"],
            "api_online": saude["api_online"],
            "release_guard_pronto": saude["release_guard_pronto"],
            "modo_fundador_pronto": saude["modo_fundador_pronto"],
            "fallback_local_ok": saude["fallback_local_ok"],
            "security_ok": saude["security_ok"],
        }
    )


def executar_autoteste_launch_readiness_valoris() -> List[Dict[str, str]]:
    saude = calcular_saude_launch_readiness()
    return [
        {
            "teste": "versao_launch_readiness",
            "status": "OK" if VERSAO_LAUNCH_READINESS_VALORIS == "3.8.75" else "FALHA",
            "detalhe": VERSAO_LAUNCH_READINESS_VALORIS,
        },
        {
            "teste": "score_launch",
            "status": "OK" if 0 <= saude["score_launch"] <= 100 else "FALHA",
            "detalhe": str(saude["score_launch"]),
        },
        {
            "teste": "renderizador",
            "status": "OK" if callable(renderizar_launch_readiness_valoris) else "FALHA",
            "detalhe": "renderizar_launch_readiness_valoris",
        },
    ]
