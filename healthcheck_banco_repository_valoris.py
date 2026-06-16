# healthcheck_banco_repository_valoris.py
# Valoris — Health Check Banco e Repository v3.10.3

from __future__ import annotations

import csv
import json
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st


VERSAO_HEALTHCHECK_BANCO_REPOSITORY_VALORIS = "3.10.3"

CAMINHO_RELATORIO = Path("RELATORIO_HEALTHCHECK_BANCO_REPOSITORY_VALORIS.md")
CAMINHO_MANIFESTO = Path("manifesto_healthcheck_banco_repository_valoris.json")
CAMINHO_LOG = Path("eventos_healthcheck_banco_repository_valoris.csv")

CAMPOS_LOG = [
    "data_hora",
    "evento",
    "area",
    "status",
    "score",
    "observacao",
]


def _agora_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat(sep=" ")


def _txt(valor: Any) -> str:
    return "" if valor is None else str(valor).strip()


def _garantir_csv(caminho: Path, campos: List[str]) -> None:
    if caminho.exists():
        return

    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()


def registrar_evento_healthcheck(evento: str, area: str, status: str, score: Any = "", observacao: str = "") -> Path:
    _garantir_csv(CAMINHO_LOG, CAMPOS_LOG)

    with CAMINHO_LOG.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_LOG)
        escritor.writerow(
            {
                "data_hora": _agora_iso(),
                "evento": _txt(evento),
                "area": _txt(area),
                "status": _txt(status),
                "score": _txt(score),
                "observacao": _txt(observacao),
            }
        )

    return CAMINHO_LOG


def carregar_eventos_healthcheck(max_registros: int = 300) -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_LOG, CAMPOS_LOG)

    try:
        with CAMINHO_LOG.open("r", newline="", encoding="utf-8") as arquivo:
            leitor = csv.DictReader(arquivo)
            return list(deque(leitor, maxlen=max_registros))
    except Exception:
        return []


def status_por_score(score: int) -> str:
    if score >= 85:
        return "Saudável"
    if score >= 65:
        return "Atenção"
    if score >= 40:
        return "Frágil"
    return "Crítico"


def obter_metricas_sqlite() -> Dict[str, Any]:
    try:
        from sqlite_local_valoris import calcular_metricas_sqlite

        return calcular_metricas_sqlite()
    except Exception as erro:
        return {
            "score_sqlite": 0,
            "existe": False,
            "tabelas": 0,
            "linhas_totais": 0,
            "tabelas_faltantes": [],
            "risco": "Alto",
            "decisao": "SQLite indisponível",
            "proximo_passo": str(erro),
        }


def obter_metricas_backend() -> Dict[str, Any]:
    try:
        from repository_backend_sqlite_valoris import calcular_metricas_backend

        return calcular_metricas_backend()
    except Exception as erro:
        return {
            "score_backend": 0,
            "backend_padrao": "indisponível",
            "sqlite_disponivel": False,
            "entidades_alinhadas": 0,
            "divergentes": 0,
            "risco": "Alto",
            "decisao": "Repository Backend indisponível",
            "proximo_passo": str(erro),
        }


def obter_metricas_repository_unico() -> Dict[str, Any]:
    try:
        from repositorio_unico_valoris import calcular_metricas_repositorio

        return calcular_metricas_repositorio()
    except Exception as erro:
        return {
            "score_repositorio": 0,
            "entidades_total": 0,
            "entidades_existentes": 0,
            "entidades_alto_risco": 1,
            "risco": "Alto",
            "decisao": "Repository Único indisponível",
            "proximo_passo": str(erro),
        }


def obter_metricas_simulador() -> Dict[str, Any]:
    try:
        from simulador_migracao_banco_valoris import calcular_metricas_simulador

        return calcular_metricas_simulador()
    except Exception as erro:
        return {
            "score_migracao": 0,
            "tabelas_total": 0,
            "alto_risco": 1,
            "medio_risco": 0,
            "risco": "Alto",
            "decisao": "Simulador indisponível",
            "proximo_passo": str(erro),
        }


def obter_comparacao_csv_sqlite() -> List[Dict[str, Any]]:
    try:
        from repository_backend_sqlite_valoris import comparar_csv_sqlite

        return comparar_csv_sqlite()
    except Exception:
        return []


def obter_config_backend() -> Dict[str, Any]:
    try:
        from repository_backend_sqlite_valoris import carregar_config_backend

        return carregar_config_backend()
    except Exception:
        return {
            "backend_padrao": "csv",
            "permitir_escrita_sqlite": False,
            "modo_sqlite": "laboratorio",
        }


def verificar_backups_sqlite() -> Dict[str, Any]:
    pasta = Path("backups_sqlite_valoris")

    if not pasta.exists():
        return {
            "existe": False,
            "quantidade": 0,
            "ultimo_backup": "",
            "status": "Atenção",
            "diagnostico": "Nenhum backup SQLite encontrado ainda.",
        }

    backups = sorted(pasta.glob("*.db"), key=lambda p: p.stat().st_mtime, reverse=True)

    if not backups:
        return {
            "existe": True,
            "quantidade": 0,
            "ultimo_backup": "",
            "status": "Atenção",
            "diagnostico": "Pasta de backup existe, mas ainda não há arquivos .db.",
        }

    ultimo = backups[0]
    modificado = datetime.fromtimestamp(ultimo.stat().st_mtime).replace(microsecond=0).isoformat(sep=" ")

    return {
        "existe": True,
        "quantidade": len(backups),
        "ultimo_backup": modificado,
        "status": "Saudável",
        "diagnostico": f"Último backup: {ultimo.name}",
    }


def verificar_arquivos_locais_ignorados() -> Dict[str, Any]:
    gitignore = Path(".gitignore")
    conteudo = gitignore.read_text(encoding="utf-8", errors="replace") if gitignore.exists() else ""

    esperados = [
        "valoris_local.db",
        "backups_sqlite_valoris/",
        "config_backend_repositorio_valoris.json",
        "eventos_repository_backend_sqlite_valoris.csv",
        "eventos_sqlite_local_valoris.csv",
        "RELATORIO_SQLITE_LOCAL_VALORIS.md",
        "RELATORIO_REPOSITORY_BACKEND_SQLITE_VALORIS.md",
    ]

    faltantes = [item for item in esperados if item not in conteudo]

    if faltantes:
        return {
            "status": "Atenção",
            "faltantes": faltantes,
            "diagnostico": "Alguns arquivos locais de banco/backend não aparecem no .gitignore.",
        }

    return {
        "status": "Saudável",
        "faltantes": [],
        "diagnostico": "Arquivos locais críticos aparecem no .gitignore.",
    }


def gerar_checklist_saude() -> List[Dict[str, Any]]:
    sqlite = obter_metricas_sqlite()
    backend = obter_metricas_backend()
    repo = obter_metricas_repository_unico()
    simulador = obter_metricas_simulador()
    backups = verificar_backups_sqlite()
    gitignore = verificar_arquivos_locais_ignorados()

    checks = [
        {
            "area": "SQLite Local",
            "score": int(sqlite.get("score_sqlite", 0) or 0),
            "status": status_por_score(int(sqlite.get("score_sqlite", 0) or 0)),
            "diagnostico": sqlite.get("decisao", ""),
            "proximo_passo": sqlite.get("proximo_passo", ""),
        },
        {
            "area": "Repository Backend",
            "score": int(backend.get("score_backend", 0) or 0),
            "status": status_por_score(int(backend.get("score_backend", 0) or 0)),
            "diagnostico": backend.get("decisao", ""),
            "proximo_passo": backend.get("proximo_passo", ""),
        },
        {
            "area": "Repository Único",
            "score": int(repo.get("score_repositorio", 0) or 0),
            "status": status_por_score(int(repo.get("score_repositorio", 0) or 0)),
            "diagnostico": repo.get("decisao", ""),
            "proximo_passo": repo.get("proximo_passo", ""),
        },
        {
            "area": "Simulador Migração",
            "score": int(simulador.get("score_migracao", 0) or 0),
            "status": status_por_score(int(simulador.get("score_migracao", 0) or 0)),
            "diagnostico": simulador.get("decisao", ""),
            "proximo_passo": simulador.get("proximo_passo", ""),
        },
        {
            "area": "Backups SQLite",
            "score": 90 if backups.get("quantidade", 0) > 0 else 55,
            "status": backups["status"],
            "diagnostico": backups["diagnostico"],
            "proximo_passo": "Criar backup do banco local regularmente.",
        },
        {
            "area": "Gitignore Dados Locais",
            "score": 90 if gitignore["status"] == "Saudável" else 60,
            "status": gitignore["status"],
            "diagnostico": gitignore["diagnostico"],
            "proximo_passo": "Manter dados locais fora do Git.",
        },
    ]

    return checks


def calcular_metricas_healthcheck() -> Dict[str, Any]:
    checks = gerar_checklist_saude()
    comparacao = obter_comparacao_csv_sqlite()
    config = obter_config_backend()

    score_medio = int(round(sum(int(item["score"]) for item in checks) / max(len(checks), 1)))
    criticos = len([item for item in checks if item["status"] == "Crítico"])
    frageis = len([item for item in checks if item["status"] == "Frágil"])
    atencao = len([item for item in checks if item["status"] == "Atenção"])
    saudaveis = len([item for item in checks if item["status"] == "Saudável"])
    divergentes = len([item for item in comparacao if item.get("status") == "divergente"])

    score_final = score_medio
    score_final -= min(criticos * 18, 36)
    score_final -= min(frageis * 10, 20)
    score_final -= min(divergentes * 12, 24)
    score_final = max(0, min(100, int(score_final)))

    if criticos > 0:
        risco = "Alto"
        decisao = "Há componente crítico na camada de dados"
        proximo = "Corrigir checks críticos antes de avançar na migração."
    elif divergentes > 0:
        risco = "Médio/Alto"
        decisao = "Há divergência entre CSV e SQLite"
        proximo = "Investigar entidades divergentes antes de migrar escrita."
    elif score_final >= 85:
        risco = "Baixo"
        decisao = "Camada de dados saudável para evolução controlada"
        proximo = "Começar a migrar páginas novas para o backend flexível."
    elif score_final >= 65:
        risco = "Médio"
        decisao = "Camada funcional, mas ainda exige atenção"
        proximo = "Resolver pontos de atenção antes de ativar escrita SQLite."
    else:
        risco = "Médio/Alto"
        decisao = "Camada ainda frágil para migração de uso real"
        proximo = "Manter CSV como padrão e melhorar saúde técnica."

    return {
        "versao": VERSAO_HEALTHCHECK_BANCO_REPOSITORY_VALORIS,
        "gerado_em": _agora_iso(),
        "score_healthcheck": score_final,
        "score_medio_checks": score_medio,
        "checks_total": len(checks),
        "saudaveis": saudaveis,
        "atencao": atencao,
        "frageis": frageis,
        "criticos": criticos,
        "divergentes_csv_sqlite": divergentes,
        "backend_padrao": config.get("backend_padrao", "csv"),
        "escrita_sqlite": bool(config.get("permitir_escrita_sqlite", False)),
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo,
    }


def gerar_relatorio_healthcheck_markdown() -> str:
    metricas = calcular_metricas_healthcheck()
    checks = gerar_checklist_saude()
    comparacao = obter_comparacao_csv_sqlite()

    linhas_checks = "\\n".join(
        [
            f"- **{item['area']}** — score {item['score']}/100 — status {item['status']} — {item['diagnostico']}"
            for item in checks
        ]
    )

    linhas_comparacao = "\\n".join(
        [
            f"- **{item.get('entidade')}**: CSV={item.get('csv')} | SQLite={item.get('sqlite')} | status={item.get('status')}"
            for item in comparacao
        ]
    ) or "- Comparação indisponível."

    return f"""# Health Check Banco e Repository — Valoris

Versão: {VERSAO_HEALTHCHECK_BANCO_REPOSITORY_VALORIS}  
Gerado em: {_agora_iso()}

## Diagnóstico geral

Score Health Check: {metricas['score_healthcheck']}/100  
Checks saudáveis: {metricas['saudaveis']}  
Atenção: {metricas['atencao']}  
Frágeis: {metricas['frageis']}  
Críticos: {metricas['criticos']}  
Divergências CSV x SQLite: {metricas['divergentes_csv_sqlite']}  

Backend padrão: {metricas['backend_padrao']}  
Escrita SQLite ativa: {'Sim' if metricas['escrita_sqlite'] else 'Não'}  

Risco: {metricas['risco']}  
Decisão: {metricas['decisao']}  
Próximo passo: {metricas['proximo_passo']}

## Checks

{linhas_checks}

## Comparação CSV x SQLite

{linhas_comparacao}

## Leitura estratégica

Esta página aumenta confiança do usuário e do fundador: antes de mudar backend, o produto mostra se os dados estão saudáveis, se o banco existe, se o Repository está íntegro e se há divergência entre CSV e SQLite.
"""


def salvar_relatorio_healthcheck_markdown() -> Path:
    CAMINHO_RELATORIO.write_text(gerar_relatorio_healthcheck_markdown(), encoding="utf-8")
    return CAMINHO_RELATORIO


def gerar_manifesto_healthcheck() -> Dict[str, Any]:
    return {
        "produto": "Valoris",
        "versao": VERSAO_HEALTHCHECK_BANCO_REPOSITORY_VALORIS,
        "modulo": "healthcheck_banco_repository_valoris",
        "data_hora": _agora_iso(),
        "metricas": calcular_metricas_healthcheck(),
        "checks": gerar_checklist_saude(),
        "comparacao_csv_sqlite": obter_comparacao_csv_sqlite(),
        "principio": "confiança do cliente exige saúde técnica visível",
        "proxima_etapa": "migrar páginas novas para backend flexível com feature flag",
    }


def salvar_manifesto_healthcheck() -> Path:
    CAMINHO_MANIFESTO.write_text(
        json.dumps(gerar_manifesto_healthcheck(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return CAMINHO_MANIFESTO


def renderizar_healthcheck_banco_repository_valoris() -> None:
    st.subheader("Health Check Banco e Repository")
    st.caption(
        "Central de confiança técnica: monitora SQLite, CSV, Repository, backups, divergências e prontidão de migração."
    )

    metricas = calcular_metricas_healthcheck()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Score Health", f"{metricas['score_healthcheck']}/100")
    col2.metric("Saudáveis", metricas["saudaveis"])
    col3.metric("Atenção", metricas["atencao"])
    col4.metric("Críticos", metricas["criticos"])
    col5.metric("Divergências", metricas["divergentes_csv_sqlite"])

    if metricas["risco"] == "Alto":
        st.error(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    elif metricas["risco"] in {"Médio", "Médio/Alto"}:
        st.warning(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    else:
        st.success(f"{metricas['decisao']} — {metricas['proximo_passo']}")

    st.divider()

    st.markdown("### Checklist de saúde")
    checks = gerar_checklist_saude()
    st.dataframe(checks, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Comparação CSV x SQLite")
    comparacao = obter_comparacao_csv_sqlite()
    st.dataframe(comparacao, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Backups")
    backups = verificar_backups_sqlite()
    st.json(backups)

    st.divider()

    st.markdown("### Registrar evento de health check")

    col1, col2, col3 = st.columns(3)
    evento = col1.text_input("Evento", value="revisao_healthcheck")
    area = col2.selectbox("Área", [item["area"] for item in checks])
    status = col3.selectbox("Status", ["ok", "atenção", "erro", "revisado"])

    observacao = st.text_area("Observação", value=metricas["proximo_passo"], height=90)

    if st.button("Registrar evento"):
        score_area = next((item["score"] for item in checks if item["area"] == area), "")
        registrar_evento_healthcheck(evento=evento, area=area, status=status, score=score_area, observacao=observacao)
        st.success("Evento registrado.")
        st.rerun()

    eventos = carregar_eventos_healthcheck()

    if eventos:
        st.markdown("### Eventos registrados")
        st.dataframe(eventos, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Relatórios")

    col_a, col_b = st.columns(2)

    if col_a.button("Salvar relatório Health Check"):
        caminho = salvar_relatorio_healthcheck_markdown()
        st.success(f"Relatório salvo em {caminho}")

    if col_b.button("Salvar manifesto Health Check"):
        caminho = salvar_manifesto_healthcheck()
        st.success(f"Manifesto salvo em {caminho}")

    st.download_button(
        "Baixar relatório Health Check (.md)",
        data=gerar_relatorio_healthcheck_markdown(),
        file_name="RELATORIO_HEALTHCHECK_BANCO_REPOSITORY_VALORIS.md",
        mime="text/markdown",
    )


def executar_autoteste_healthcheck_banco_repository_valoris() -> Dict[str, Any]:
    metricas = calcular_metricas_healthcheck()

    return {
        "ok": True,
        "versao": VERSAO_HEALTHCHECK_BANCO_REPOSITORY_VALORIS,
        "metricas": {
            "score_healthcheck": metricas["score_healthcheck"],
            "criticos": metricas["criticos"],
            "divergentes_csv_sqlite": metricas["divergentes_csv_sqlite"],
        },
    }
