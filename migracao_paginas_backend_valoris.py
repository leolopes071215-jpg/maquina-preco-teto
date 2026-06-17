# migracao_paginas_backend_valoris.py
# Valoris — Migração Controlada de Páginas para Backend Flexível v3.10.4
# ---------------------------------------------------------------------
# Objetivo:
# - Criar uma central para migrar páginas gradualmente para o backend flexível.
# - Validar quais páginas ainda leem CSV diretamente e quais podem usar Repository Backend.
# - Criar plano de migração com risco, prioridade, rollback e experiência do cliente.
# - Não altera páginas antigas automaticamente. Esta versão é de governança e transição segura.

from __future__ import annotations

import ast
import csv
import json
import re
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st


VERSAO_MIGRACAO_PAGINAS_BACKEND_VALORIS = "3.10.4"

CAMINHO_RELATORIO = Path("RELATORIO_MIGRACAO_PAGINAS_BACKEND_VALORIS.md")
CAMINHO_MANIFESTO = Path("manifesto_migracao_paginas_backend_valoris.json")
CAMINHO_DECISOES = Path("decisoes_migracao_paginas_backend_valoris.csv")

CAMPOS_DECISOES = [
    "data_hora",
    "modulo",
    "pagina",
    "risco",
    "prioridade",
    "decisao",
    "observacao",
]

PAGINAS_PRIORITARIAS = {
    "historico_analises_valoris.py": {
        "pagina": "Histórico Análises",
        "entidades": ["analises"],
        "risco_cliente": "Baixo",
        "motivo": "Página principalmente de leitura; boa candidata para backend flexível.",
    },
    "analise_inteligente_valoris.py": {
        "pagina": "Análise Inteligente",
        "entidades": ["analises", "watchlist"],
        "risco_cliente": "Médio",
        "motivo": "Central de ranking depende de múltiplas fontes; migrar após Histórico.",
    },
    "pipeline_decisao_valoris.py": {
        "pagina": "Pipeline Decisão",
        "entidades": ["pipeline_acoes", "analises", "watchlist"],
        "risco_cliente": "Médio",
        "motivo": "Possui escrita de ações; exige flag e rollback.",
    },
    "radar_revisoes_valoris.py": {
        "pagina": "Radar Revisões",
        "entidades": ["alertas", "pipeline_acoes", "watchlist"],
        "risco_cliente": "Médio",
        "motivo": "Depende de prazos e alertas; precisa preservar consistência.",
    },
    "repository_backend_sqlite_valoris.py": {
        "pagina": "Repository Backend",
        "entidades": ["analises", "watchlist", "pipeline_acoes", "alertas"],
        "risco_cliente": "Baixo",
        "motivo": "Já é a própria página de controle do backend.",
    },
}


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


def carregar_app_paginas() -> Dict[str, Any]:
    caminho = Path("app.py")

    if not caminho.exists():
        return {}

    texto = caminho.read_text(encoding="utf-8", errors="replace")

    try:
        arvore = ast.parse(texto)
    except Exception:
        return {}

    for node in ast.walk(arvore):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "PAGINAS":
                    try:
                        return ast.literal_eval(node.value)
                    except Exception:
                        return {}

    return {}


def detectar_uso_backend_flexivel(texto: str) -> Dict[str, bool]:
    return {
        "importa_backend_flexivel": "repository_backend_sqlite_valoris" in texto,
        "usa_listar_backend": "listar_registros_backend" in texto,
        "usa_salvar_backend": "salvar_registro_backend" in texto,
        "usa_repo_unico": "repositorio_unico_valoris" in texto,
        "usa_sqlite_direto": "sqlite3" in texto or "sqlite_local_valoris" in texto,
    }


def detectar_acesso_csv_direto(texto: str) -> Dict[str, Any]:
    csvs = sorted(set(re.findall(r'["\']([A-Za-z0-9_\-]+\.csv)["\']', texto)))
    leituras = len(re.findall(r'\.open\(|open\(', texto))
    csv_dict = "csv.DictReader" in texto or "csv.DictWriter" in texto
    path_csv = ".csv" in texto

    return {
        "csvs_referenciados": csvs,
        "qtd_csvs": len(csvs),
        "leituras_open": leituras,
        "usa_csv_lib": csv_dict,
        "tem_csv_direto": bool(csvs or csv_dict or path_csv),
    }


def detectar_funcoes_render(texto: str) -> List[str]:
    funcoes = []

    try:
        arvore = ast.parse(texto)
    except Exception:
        return funcoes

    for node in ast.walk(arvore):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("renderizar_"):
            funcoes.append(node.name)

    return sorted(funcoes)


def analisar_modulo(modulo_py: Path) -> Dict[str, Any]:
    texto = modulo_py.read_text(encoding="utf-8", errors="replace") if modulo_py.exists() else ""

    acesso_csv = detectar_acesso_csv_direto(texto)
    backend = detectar_uso_backend_flexivel(texto)
    funcoes_render = detectar_funcoes_render(texto)
    prioridade_info = PAGINAS_PRIORITARIAS.get(modulo_py.name, {})

    risco = "Baixo"
    motivo_risco = []

    if acesso_csv["qtd_csvs"] >= 3:
        risco = "Alto"
        motivo_risco.append("Muitos CSVs referenciados diretamente.")
    elif acesso_csv["tem_csv_direto"]:
        risco = "Médio"
        motivo_risco.append("Há acesso direto a CSV.")

    if backend["usa_salvar_backend"]:
        motivo_risco.append("Já usa escrita via backend flexível.")
    elif backend["usa_listar_backend"]:
        motivo_risco.append("Já usa leitura via backend flexível.")

    if prioridade_info.get("risco_cliente") == "Baixo" and risco == "Médio":
        risco = "Baixo/Médio"

    if not motivo_risco:
        motivo_risco.append("Sem sinais fortes de risco de dados.")

    usa_backend_flexivel = backend["usa_listar_backend"] or backend["usa_salvar_backend"]

    if usa_backend_flexivel:
        status = "Migrada ou parcialmente migrada"
    elif acesso_csv["tem_csv_direto"]:
        status = "Candidata à migração"
    else:
        status = "Sem dependência relevante de dados"

    prioridade = "Baixa"

    if modulo_py.name in PAGINAS_PRIORITARIAS:
        prioridade = "Alta" if risco in {"Baixo", "Baixo/Médio"} else "Média"

    if modulo_py.name == "historico_analises_valoris.py":
        prioridade = "Alta"

    return {
        "modulo": modulo_py.name,
        "pagina": prioridade_info.get("pagina", ""),
        "status": status,
        "risco": risco,
        "prioridade": prioridade,
        "csvs": ", ".join(acesso_csv["csvs_referenciados"]),
        "qtd_csvs": acesso_csv["qtd_csvs"],
        "usa_csv_lib": "Sim" if acesso_csv["usa_csv_lib"] else "Não",
        "usa_backend_flexivel": "Sim" if usa_backend_flexivel else "Não",
        "usa_sqlite_direto": "Sim" if backend["usa_sqlite_direto"] else "Não",
        "funcoes_render": ", ".join(funcoes_render),
        "entidades_sugeridas": ", ".join(prioridade_info.get("entidades", [])),
        "motivo": prioridade_info.get("motivo", "Módulo detectado por análise estática."),
        "diagnostico": " | ".join(motivo_risco),
    }


def listar_modulos_do_app() -> List[Path]:
    paginas = carregar_app_paginas()
    modulos = []

    for _, dados in paginas.items():
        if isinstance(dados, (tuple, list)) and len(dados) >= 1:
            modulo = _txt(dados[0])
            if modulo:
                caminho = Path(f"{modulo}.py")
                if caminho.exists():
                    modulos.append(caminho)

    modulos_unicos = sorted(set(modulos), key=lambda p: p.name)

    return modulos_unicos


def analisar_paginas_backend() -> List[Dict[str, Any]]:
    modulos = listar_modulos_do_app()
    analises = [analisar_modulo(modulo) for modulo in modulos]

    ordem_prioridade = {"Alta": 1, "Média": 2, "Baixa": 3}
    ordem_risco = {"Baixo": 1, "Baixo/Médio": 2, "Médio": 3, "Alto": 4}

    analises.sort(
        key=lambda item: (
            ordem_prioridade.get(item["prioridade"], 9),
            ordem_risco.get(item["risco"], 9),
            item["modulo"],
        )
    )

    return analises


def sugerir_ordem_migracao() -> List[Dict[str, Any]]:
    analises = analisar_paginas_backend()
    candidatos = [
        item for item in analises
        if item["status"] == "Candidata à migração"
        or item["modulo"] in PAGINAS_PRIORITARIAS
    ]

    ordem = []
    etapa = 1

    for item in candidatos:
        if item["usa_backend_flexivel"] == "Sim":
            recomendacao = "Monitorar; já possui integração flexível parcial."
        elif item["risco"] in {"Baixo", "Baixo/Médio"}:
            recomendacao = "Migrar leitura primeiro, mantendo escrita em CSV."
        elif item["risco"] == "Médio":
            recomendacao = "Criar wrapper de leitura e testar com backend csv antes de SQLite."
        else:
            recomendacao = "Adiar; exige refatoração mais cuidadosa."

        ordem.append(
            {
                "ordem": etapa,
                "modulo": item["modulo"],
                "pagina": item["pagina"],
                "risco": item["risco"],
                "prioridade": item["prioridade"],
                "entidades": item["entidades_sugeridas"],
                "recomendacao": recomendacao,
                "rollback": "Manter função antiga e ativar backend flexível por flag.",
            }
        )
        etapa += 1

    return ordem


def calcular_metricas_migracao_paginas() -> Dict[str, Any]:
    analises = analisar_paginas_backend()
    ordem = sugerir_ordem_migracao()

    total = len(analises)
    candidatas = len([item for item in analises if item["status"] == "Candidata à migração"])
    migradas = len([item for item in analises if item["usa_backend_flexivel"] == "Sim"])
    alto_risco = len([item for item in analises if item["risco"] == "Alto"])
    prioridade_alta = len([item for item in analises if item["prioridade"] == "Alta"])

    score = 35
    score += min(migradas * 8, 24)
    score += min(prioridade_alta * 5, 20)
    score += min(len(ordem) * 3, 15)
    score -= min(alto_risco * 8, 24)
    score = max(0, min(100, int(score)))

    if total == 0:
        risco = "Alto"
        decisao = "Nenhuma página detectada"
        proximo = "Verificar app.py e mapeamento PAGINAS."
    elif alto_risco > 0:
        risco = "Médio/Alto"
        decisao = "Há páginas com risco alto de migração"
        proximo = "Começar por Histórico Análises e manter rollback."
    elif candidatas > 0:
        risco = "Médio"
        decisao = "Há páginas prontas para migração controlada"
        proximo = "Migrar leitura da página Histórico Análises para backend flexível."
    else:
        risco = "Baixo"
        decisao = "Poucas dependências diretas de CSV detectadas"
        proximo = "Migrar gradualmente páginas novas para backend flexível."

    return {
        "versao": VERSAO_MIGRACAO_PAGINAS_BACKEND_VALORIS,
        "gerado_em": _agora_iso(),
        "score_migracao_paginas": score,
        "paginas_analisadas": total,
        "candidatas": candidatas,
        "migradas_ou_parciais": migradas,
        "alto_risco": alto_risco,
        "prioridade_alta": prioridade_alta,
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo,
    }


def salvar_decisao_migracao(modulo: str, pagina: str, risco: str, prioridade: str, decisao: str, observacao: str = "") -> Path:
    _garantir_csv(CAMINHO_DECISOES, CAMPOS_DECISOES)

    with CAMINHO_DECISOES.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISOES)
        escritor.writerow(
            {
                "data_hora": _agora_iso(),
                "modulo": _txt(modulo),
                "pagina": _txt(pagina),
                "risco": _txt(risco),
                "prioridade": _txt(prioridade),
                "decisao": _txt(decisao),
                "observacao": _txt(observacao),
            }
        )

    return CAMINHO_DECISOES


def carregar_decisoes_migracao(max_registros: int = 300) -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_DECISOES, CAMPOS_DECISOES)

    try:
        with CAMINHO_DECISOES.open("r", newline="", encoding="utf-8") as arquivo:
            leitor = csv.DictReader(arquivo)
            return list(deque(leitor, maxlen=max_registros))
    except Exception:
        return []


def gerar_relatorio_migracao_markdown() -> str:
    metricas = calcular_metricas_migracao_paginas()
    ordem = sugerir_ordem_migracao()

    linhas = "\n".join(
        [
            f"- **#{item['ordem']} {item['pagina'] or item['modulo']}** — risco {item['risco']} — {item['recomendacao']} Rollback: {item['rollback']}"
            for item in ordem[:20]
        ]
    ) or "- Nenhuma página candidata."

    return f"""# Migração Controlada de Páginas para Backend Flexível — Valoris

Versão: {VERSAO_MIGRACAO_PAGINAS_BACKEND_VALORIS}  
Gerado em: {_agora_iso()}

## Diagnóstico

Score migração de páginas: {metricas['score_migracao_paginas']}/100  
Páginas analisadas: {metricas['paginas_analisadas']}  
Candidatas: {metricas['candidatas']}  
Migradas/parciais: {metricas['migradas_ou_parciais']}  
Alto risco: {metricas['alto_risco']}  
Prioridade alta: {metricas['prioridade_alta']}  

Risco: {metricas['risco']}  
Decisão: {metricas['decisao']}  
Próximo passo: {metricas['proximo_passo']}

## Ordem sugerida

{linhas}

## Leitura estratégica

A migração deve ser invisível para o cliente. A experiência deve continuar simples, rápida e confiável, enquanto o backend evolui com feature flag, rollback e testes por página.
"""


def salvar_relatorio_migracao_markdown() -> Path:
    CAMINHO_RELATORIO.write_text(gerar_relatorio_migracao_markdown(), encoding="utf-8")
    return CAMINHO_RELATORIO


def gerar_manifesto_migracao() -> Dict[str, Any]:
    return {
        "produto": "Valoris",
        "versao": VERSAO_MIGRACAO_PAGINAS_BACKEND_VALORIS,
        "modulo": "migracao_paginas_backend_valoris",
        "data_hora": _agora_iso(),
        "metricas": calcular_metricas_migracao_paginas(),
        "paginas": analisar_paginas_backend(),
        "ordem_sugerida": sugerir_ordem_migracao(),
        "principio": "a migração deve melhorar a experiência sem ser percebida como risco pelo cliente",
        "proxima_etapa": "migrar_historico_analises_backend_flexivel",
    }


def salvar_manifesto_migracao() -> Path:
    CAMINHO_MANIFESTO.write_text(
        json.dumps(gerar_manifesto_migracao(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return CAMINHO_MANIFESTO


def renderizar_migracao_paginas_backend_valoris() -> None:
    st.subheader("Migração de Páginas para Backend Flexível")
    st.caption(
        "Governança da transição: quais páginas podem migrar para Repository Backend sem prejudicar a experiência do cliente."
    )

    metricas = calcular_metricas_migracao_paginas()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Score migração", f"{metricas['score_migracao_paginas']}/100")
    col2.metric("Páginas", metricas["paginas_analisadas"])
    col3.metric("Candidatas", metricas["candidatas"])
    col4.metric("Parciais", metricas["migradas_ou_parciais"])
    col5.metric("Alto risco", metricas["alto_risco"])

    if metricas["risco"] in {"Alto", "Médio/Alto"}:
        st.warning(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    elif metricas["risco"] == "Médio":
        st.info(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    else:
        st.success(f"{metricas['decisao']} — {metricas['proximo_passo']}")

    st.divider()

    st.markdown("### Páginas analisadas")
    analises = analisar_paginas_backend()
    st.dataframe(analises, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Ordem sugerida de migração")
    ordem = sugerir_ordem_migracao()
    st.dataframe(ordem, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Registrar decisão de migração")

    opcoes = [item["modulo"] for item in analises]

    if opcoes:
        modulo_escolhido = st.selectbox("Módulo", opcoes)
        item = next(linha for linha in analises if linha["modulo"] == modulo_escolhido)

        col_a, col_b, col_c = st.columns(3)
        risco = col_a.selectbox("Risco revisado", ["Baixo", "Baixo/Médio", "Médio", "Médio/Alto", "Alto"], index=0)
        prioridade = col_b.selectbox("Prioridade", ["Alta", "Média", "Baixa"], index=["Alta", "Média", "Baixa"].index(item["prioridade"]) if item["prioridade"] in ["Alta", "Média", "Baixa"] else 1)
        decisao = col_c.selectbox(
            "Decisão",
            [
                "Migrar leitura primeiro",
                "Migrar com feature flag",
                "Adiar migração",
                "Investigar manualmente",
                "Manter como está",
            ],
        )

        observacao = st.text_area("Observação", value=item["diagnostico"], height=90)

        if st.button("Salvar decisão de migração"):
            salvar_decisao_migracao(
                modulo=item["modulo"],
                pagina=item["pagina"],
                risco=risco,
                prioridade=prioridade,
                decisao=decisao,
                observacao=observacao,
            )
            st.success("Decisão registrada.")
            st.rerun()

    decisoes = carregar_decisoes_migracao()

    if decisoes:
        st.markdown("### Decisões registradas")
        st.dataframe(decisoes, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Relatórios")

    col1, col2 = st.columns(2)

    if col1.button("Salvar relatório de migração"):
        caminho = salvar_relatorio_migracao_markdown()
        st.success(f"Relatório salvo em {caminho}")

    if col2.button("Salvar manifesto de migração"):
        caminho = salvar_manifesto_migracao()
        st.success(f"Manifesto salvo em {caminho}")

    st.download_button(
        "Baixar relatório de migração (.md)",
        data=gerar_relatorio_migracao_markdown(),
        file_name="RELATORIO_MIGRACAO_PAGINAS_BACKEND_VALORIS.md",
        mime="text/markdown",
    )


def executar_autoteste_migracao_paginas_backend_valoris() -> Dict[str, Any]:
    metricas = calcular_metricas_migracao_paginas()

    return {
        "ok": True,
        "versao": VERSAO_MIGRACAO_PAGINAS_BACKEND_VALORIS,
        "metricas": {
            "score_migracao_paginas": metricas["score_migracao_paginas"],
            "paginas_analisadas": metricas["paginas_analisadas"],
            "candidatas": metricas["candidatas"],
        },
    }
