# piloto_sqlite_valoris.py

from __future__ import annotations

import csv
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple
from uuid import uuid4

import streamlit as st

from gateway_dados_valoris import (
    CONTRATOS_TABELAS_VALORIS,
    validar_todos_contratos,
    carregar_tabela_logica,
)
from maturidade_produto_valoris import calcular_maturidade_produto_valoris


# ============================================================
# VALORIS
# v3.8.58 — Piloto SQLite e Repositório Local
# ------------------------------------------------------------
# Este módulo cria um piloto real de banco local.
#
# Objetivo:
# - transformar os contratos do Gateway em tabelas SQLite;
# - migrar CSVs para um banco local controlado;
# - testar leitura de dados fora dos CSVs;
# - preparar a futura troca para PostgreSQL/Supabase;
# - não mexer na lógica principal do app ainda.
# ============================================================


VERSAO_PILOTO_SQLITE_VALORIS = "3.8.58"

CAMINHO_BANCO_SQLITE = Path("valoris_local_piloto.db")
CAMINHO_DECISOES_SQLITE = Path("decisoes_sqlite_valoris.csv")
CAMINHO_LOGS_SQLITE = Path("logs_sqlite_valoris.csv")
CAMINHO_MANIFESTO_SQLITE = Path("manifesto_sqlite_valoris.json")

CAMPOS_DECISAO_SQLITE = [
    "id",
    "data_registro",
    "banco",
    "tabelas_criadas",
    "linhas_migradas",
    "score_sqlite",
    "decisao",
    "proximo_passo",
    "observacoes",
]

CAMPOS_LOG_SQLITE = [
    "id",
    "data_registro",
    "operacao",
    "tabela_logica",
    "tabela_sqlite",
    "status",
    "detalhe",
]


def _limpar_texto(valor: Any) -> str:
    if valor is None:
        return ""

    return str(valor).strip()


def _normalizar_nome_tabela(nome: str) -> str:
    return (
        nome.strip()
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
        .replace("/", "_")
    )


def _garantir_csv(caminho: Path, campos: List[str]) -> None:
    if caminho.exists():
        return

    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()


def registrar_log_sqlite(
    operacao: str,
    tabela_logica: str,
    tabela_sqlite: str,
    status: str,
    detalhe: str,
) -> None:
    try:
        _garantir_csv(CAMINHO_LOGS_SQLITE, CAMPOS_LOG_SQLITE)

        registro = {
            "id": str(uuid4())[:8],
            "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "operacao": _limpar_texto(operacao),
            "tabela_logica": _limpar_texto(tabela_logica),
            "tabela_sqlite": _limpar_texto(tabela_sqlite),
            "status": _limpar_texto(status),
            "detalhe": _limpar_texto(detalhe),
        }

        with CAMINHO_LOGS_SQLITE.open("a", newline="", encoding="utf-8") as arquivo:
            escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_LOG_SQLITE)
            escritor.writerow(registro)

    except Exception:
        return


def carregar_logs_sqlite() -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_LOGS_SQLITE, CAMPOS_LOG_SQLITE)

    with CAMINHO_LOGS_SQLITE.open("r", newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        return list(leitor)


def gerar_csv_logs_sqlite() -> str:
    _garantir_csv(CAMINHO_LOGS_SQLITE, CAMPOS_LOG_SQLITE)

    return CAMINHO_LOGS_SQLITE.read_text(encoding="utf-8")


def carregar_decisoes_sqlite() -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_DECISOES_SQLITE, CAMPOS_DECISAO_SQLITE)

    with CAMINHO_DECISOES_SQLITE.open("r", newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        return list(leitor)


def gerar_csv_decisoes_sqlite() -> str:
    _garantir_csv(CAMINHO_DECISOES_SQLITE, CAMPOS_DECISAO_SQLITE)

    return CAMINHO_DECISOES_SQLITE.read_text(encoding="utf-8")


def salvar_decisao_sqlite(decisao: Dict[str, Any]) -> Dict[str, str]:
    _garantir_csv(CAMINHO_DECISOES_SQLITE, CAMPOS_DECISAO_SQLITE)

    registro = {
        "id": str(uuid4())[:8],
        "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "banco": str(CAMINHO_BANCO_SQLITE),
        "tabelas_criadas": str(decisao.get("tabelas_criadas", "")),
        "linhas_migradas": str(decisao.get("linhas_migradas", "")),
        "score_sqlite": str(decisao.get("score_sqlite", "")),
        "decisao": _limpar_texto(decisao.get("decisao", "")),
        "proximo_passo": _limpar_texto(decisao.get("proximo_passo", "")),
        "observacoes": _limpar_texto(decisao.get("observacoes", "")),
    }

    with CAMINHO_DECISOES_SQLITE.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISAO_SQLITE)
        escritor.writerow(registro)

    return registro


def _conectar() -> sqlite3.Connection:
    conexao = sqlite3.connect(CAMINHO_BANCO_SQLITE)
    conexao.row_factory = sqlite3.Row
    return conexao


def gerar_create_table_sql(tabela_logica: str, contrato: Dict[str, Any]) -> str:
    tabela_sqlite = _normalizar_nome_tabela(tabela_logica)
    campos = contrato["campos_minimos"]

    definicoes = []

    for campo in campos:
        nome_campo = _normalizar_nome_tabela(campo)

        if nome_campo == "id":
            definicoes.append("id TEXT PRIMARY KEY")
        else:
            definicoes.append(f"{nome_campo} TEXT")

    if "id" not in [campo.lower() for campo in campos]:
        definicoes.insert(0, "id TEXT PRIMARY KEY")

    definicoes.append("_origem_csv TEXT")
    definicoes.append("_migrado_em TEXT")

    return f"CREATE TABLE IF NOT EXISTS {tabela_sqlite} (\n    " + ",\n    ".join(definicoes) + "\n);"


def gerar_schema_sqlite() -> str:
    partes = [
        "-- Schema SQLite piloto da Valoris",
        f"-- Versão {VERSAO_PILOTO_SQLITE_VALORIS}",
        f"-- Gerado em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
    ]

    for tabela_logica, contrato in CONTRATOS_TABELAS_VALORIS.items():
        partes.append(gerar_create_table_sql(tabela_logica, contrato))
        partes.append("")

    return "\n".join(partes).strip()


def criar_schema_sqlite() -> Dict[str, Any]:
    tabelas_criadas = []

    with _conectar() as conexao:
        for tabela_logica, contrato in CONTRATOS_TABELAS_VALORIS.items():
            sql = gerar_create_table_sql(tabela_logica, contrato)
            conexao.execute(sql)
            tabelas_criadas.append(_normalizar_nome_tabela(tabela_logica))

        conexao.commit()

    registrar_log_sqlite(
        operacao="schema",
        tabela_logica="all",
        tabela_sqlite="all",
        status="ok",
        detalhe=f"{len(tabelas_criadas)} tabela(s) criadas/verificadas.",
    )

    return {
        "tabelas_criadas": tabelas_criadas,
        "total": len(tabelas_criadas),
    }


def _preparar_linha_para_sqlite(
    tabela_logica: str,
    contrato: Dict[str, Any],
    registro: Dict[str, Any],
) -> Tuple[List[str], List[str]]:
    campos = contrato["campos_minimos"]
    colunas = []

    for campo in campos:
        colunas.append(_normalizar_nome_tabela(campo))

    if "id" not in colunas:
        colunas.insert(0, "id")

    colunas.append("_origem_csv")
    colunas.append("_migrado_em")

    valores = []

    for coluna in colunas:
        if coluna == "id":
            valor = registro.get("id", "") or str(uuid4())[:8]
        elif coluna == "_origem_csv":
            valor = contrato["arquivo_csv"]
        elif coluna == "_migrado_em":
            valor = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        else:
            valor = registro.get(coluna, "")

            if valor == "":
                # Tenta mapear campo original sem normalização.
                for campo_original in campos:
                    if _normalizar_nome_tabela(campo_original) == coluna:
                        valor = registro.get(campo_original, "")
                        break

        valores.append(_limpar_texto(valor))

    return colunas, valores


def migrar_tabela_para_sqlite(tabela_logica: str, limpar_antes: bool = True) -> Dict[str, Any]:
    contrato = CONTRATOS_TABELAS_VALORIS.get(tabela_logica)

    if not contrato:
        return {
            "tabela_logica": tabela_logica,
            "status": "falha",
            "linhas": 0,
            "detalhe": "Contrato não encontrado.",
        }

    tabela_sqlite = _normalizar_nome_tabela(tabela_logica)

    criar_schema_sqlite()

    registros = carregar_tabela_logica(tabela_logica)

    if not registros:
        registrar_log_sqlite(
            operacao="migrate",
            tabela_logica=tabela_logica,
            tabela_sqlite=tabela_sqlite,
            status="sem_dados",
            detalhe="Nenhum registro encontrado para migração.",
        )

        return {
            "tabela_logica": tabela_logica,
            "status": "sem_dados",
            "linhas": 0,
            "detalhe": "Nenhum registro encontrado.",
        }

    linhas = 0

    try:
        with _conectar() as conexao:
            if limpar_antes:
                conexao.execute(f"DELETE FROM {tabela_sqlite}")

            for registro in registros:
                colunas, valores = _preparar_linha_para_sqlite(tabela_logica, contrato, registro)
                marcadores = ", ".join(["?"] * len(colunas))
                colunas_sql = ", ".join(colunas)

                conexao.execute(
                    f"INSERT OR REPLACE INTO {tabela_sqlite} ({colunas_sql}) VALUES ({marcadores})",
                    valores,
                )
                linhas += 1

            conexao.commit()

        registrar_log_sqlite(
            operacao="migrate",
            tabela_logica=tabela_logica,
            tabela_sqlite=tabela_sqlite,
            status="ok",
            detalhe=f"{linhas} linha(s) migrada(s).",
        )

        return {
            "tabela_logica": tabela_logica,
            "status": "ok",
            "linhas": linhas,
            "detalhe": f"{linhas} linha(s) migrada(s).",
        }

    except Exception as erro:
        registrar_log_sqlite(
            operacao="migrate",
            tabela_logica=tabela_logica,
            tabela_sqlite=tabela_sqlite,
            status="erro",
            detalhe=str(erro),
        )

        return {
            "tabela_logica": tabela_logica,
            "status": "erro",
            "linhas": linhas,
            "detalhe": str(erro),
        }


def migrar_tudo_para_sqlite() -> Dict[str, Any]:
    resultados = []
    linhas_totais = 0

    criar_schema_sqlite()

    for tabela_logica in CONTRATOS_TABELAS_VALORIS.keys():
        resultado = migrar_tabela_para_sqlite(tabela_logica=tabela_logica, limpar_antes=True)
        resultados.append(resultado)
        linhas_totais += int(resultado.get("linhas", 0))

    manifesto = gerar_manifesto_sqlite(
        resultados=resultados,
        linhas_totais=linhas_totais,
    )

    return {
        "resultados": resultados,
        "linhas_totais": linhas_totais,
        "manifesto": manifesto,
    }


def listar_tabelas_sqlite() -> List[str]:
    if not CAMINHO_BANCO_SQLITE.exists():
        return []

    with _conectar() as conexao:
        cursor = conexao.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        return [linha["name"] for linha in cursor.fetchall()]


def contar_linhas_tabela_sqlite(tabela_sqlite: str) -> int:
    if not CAMINHO_BANCO_SQLITE.exists():
        return 0

    try:
        with _conectar() as conexao:
            cursor = conexao.execute(f"SELECT COUNT(*) as total FROM {tabela_sqlite}")
            linha = cursor.fetchone()
            return int(linha["total"]) if linha else 0
    except Exception:
        return 0


def carregar_preview_sqlite(tabela_sqlite: str, limite: int = 5) -> List[Dict[str, Any]]:
    if not CAMINHO_BANCO_SQLITE.exists():
        return []

    try:
        with _conectar() as conexao:
            cursor = conexao.execute(f"SELECT * FROM {tabela_sqlite} LIMIT ?", (limite,))
            return [dict(linha) for linha in cursor.fetchall()]
    except Exception:
        return []


def calcular_saude_sqlite() -> Dict[str, Any]:
    tabelas_contrato = [_normalizar_nome_tabela(tabela) for tabela in CONTRATOS_TABELAS_VALORIS.keys()]
    tabelas_existentes = listar_tabelas_sqlite()
    tabelas_criadas = len([tabela for tabela in tabelas_contrato if tabela in tabelas_existentes])

    linhas_por_tabela = {
        tabela: contar_linhas_tabela_sqlite(tabela)
        for tabela in tabelas_existentes
    }

    linhas_totais = sum(linhas_por_tabela.values())

    score = 20
    score += min(tabelas_criadas * 8, 45)
    score += min(linhas_totais * 1.5, 25)

    if CAMINHO_BANCO_SQLITE.exists():
        score += 10

    score = int(round(max(0, min(100, score))))

    if score >= 82:
        decisao = "Piloto SQLite pronto"
        proximo_passo = "Começar a criar repositórios para módulos novos e preparar adapter PostgreSQL/Supabase."
    elif score >= 60:
        decisao = "Piloto SQLite funcional"
        proximo_passo = "Migrar dados principais e validar leitura por tabela antes de refatorar módulos antigos."
    elif score >= 35:
        decisao = "SQLite em preparação"
        proximo_passo = "Criar schema e migrar os CSVs mais importantes: leads, validations e founders."
    else:
        decisao = "Banco piloto ainda não criado"
        proximo_passo = "Criar schema SQLite e rodar uma migração controlada dos CSVs."

    return {
        "existe_banco": CAMINHO_BANCO_SQLITE.exists(),
        "tabelas_existentes": tabelas_existentes,
        "tabelas_criadas": tabelas_criadas,
        "linhas_por_tabela": linhas_por_tabela,
        "linhas_totais": linhas_totais,
        "score_sqlite": score,
        "decisao": decisao,
        "proximo_passo": proximo_passo,
    }


def gerar_manifesto_sqlite(
    resultados: Optional[List[Dict[str, Any]]] = None,
    linhas_totais: Optional[int] = None,
) -> Dict[str, Any]:
    saude = calcular_saude_sqlite()

    try:
        maturidade = calcular_maturidade_produto_valoris()
    except Exception:
        maturidade = {}

    manifesto = {
        "versao": VERSAO_PILOTO_SQLITE_VALORIS,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "banco": str(CAMINHO_BANCO_SQLITE),
        "saude_sqlite": saude,
        "maturidade_produto": {
            "score_total": maturidade.get("score_total", 0),
            "classificacao": maturidade.get("classificacao", "N/D"),
        },
        "resultados_migracao": resultados or [],
        "linhas_migradas_execucao": linhas_totais or 0,
    }

    CAMINHO_MANIFESTO_SQLITE.write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    registrar_log_sqlite(
        operacao="manifest",
        tabela_logica="all",
        tabela_sqlite="all",
        status="ok",
        detalhe="Manifesto SQLite gerado.",
    )

    return manifesto


def _gerar_markdown_sqlite(saude: Dict[str, Any]) -> str:
    linhas_tabelas = "\n".join(
        [
            f"| {tabela} | {linhas} |"
            for tabela, linhas in saude["linhas_por_tabela"].items()
        ]
    )

    return f"""# Piloto SQLite — Valoris

Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Diagnóstico

Banco existe: {saude["existe_banco"]}  
Arquivo: {CAMINHO_BANCO_SQLITE}  
Score SQLite: {saude["score_sqlite"]}/100  
Decisão: {saude["decisao"]}  
Próximo passo: {saude["proximo_passo"]}

Tabelas criadas: {saude["tabelas_criadas"]}  
Linhas totais: {saude["linhas_totais"]}  

## Tabelas

| Tabela | Linhas |
|---|---:|
{linhas_tabelas}

## Schema SQLite

```sql
{gerar_schema_sqlite()}
```

## Regra

SQLite é uma ponte, não o destino final.  
Use SQLite para testar repositórios e contratos localmente.  
Depois, a migração natural será PostgreSQL/Supabase.
"""


def _injetar_css_sqlite() -> None:
    st.markdown(
        """
        <style>
            .sqlite-hero {
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

            .sqlite-eyebrow {
                color: #d6b56d;
                font-size: 0.74rem;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                font-weight: 880;
                margin-bottom: 0.35rem;
            }

            .sqlite-title {
                color: #f4f7fb;
                font-size: clamp(1.75rem, 5.4vw, 3.1rem);
                font-weight: 950;
                line-height: 1.02;
                letter-spacing: -0.058em;
                margin-bottom: 0.55rem;
            }

            .sqlite-subtitle {
                color: rgba(244, 247, 251, 0.75);
                font-size: clamp(0.94rem, 2.2vw, 1.06rem);
                line-height: 1.56;
                max-width: 1020px;
            }

            .sqlite-note {
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
        <div class="sqlite-hero">
            <div class="sqlite-eyebrow">Valoris • SQLite • v{VERSAO_PILOTO_SQLITE_VALORIS}</div>
            <div class="sqlite-title">Crie o primeiro banco local da Valoris.</div>
            <div class="sqlite-subtitle">
                Esta etapa transforma os contratos do Gateway em tabelas SQLite, migra CSVs para banco local
                e prepara o caminho real para PostgreSQL/Supabase.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _renderizar_metricas(saude: Dict[str, Any]) -> None:
    st.markdown("### Diagnóstico SQLite")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Score SQLite", f"{saude['score_sqlite']}/100")

    with col_2:
        st.metric("Banco existe", "Sim" if saude["existe_banco"] else "Não")

    with col_3:
        st.metric("Tabelas criadas", saude["tabelas_criadas"])

    with col_4:
        st.metric("Linhas totais", saude["linhas_totais"])

    st.progress(saude["score_sqlite"] / 100)

    if saude["score_sqlite"] >= 70:
        st.success(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    elif saude["score_sqlite"] >= 35:
        st.warning(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    else:
        st.info(f"**{saude['decisao']}** — {saude['proximo_passo']}")


def _renderizar_acoes(saude: Dict[str, Any]) -> None:
    st.markdown("### Ações controladas")

    col_1, col_2, col_3 = st.columns(3)

    with col_1:
        if st.button("Criar/verificar schema SQLite", key="criar_schema_sqlite_valoris"):
            resultado = criar_schema_sqlite()
            st.success(f"{resultado['total']} tabela(s) criadas/verificadas.")
            st.rerun()

    with col_2:
        if st.button("Migrar CSVs para SQLite piloto", key="migrar_csvs_sqlite_valoris"):
            resultado = migrar_tudo_para_sqlite()
            st.success(f"{resultado['linhas_totais']} linha(s) migrada(s) para SQLite.")
            st.rerun()

    with col_3:
        if st.button("Gerar manifesto SQLite", key="gerar_manifesto_sqlite_valoris"):
            manifesto = gerar_manifesto_sqlite()
            st.success(f"Manifesto gerado: {CAMINHO_MANIFESTO_SQLITE}")
            st.json(
                {
                    "versao": manifesto["versao"],
                    "banco": manifesto["banco"],
                    "score": manifesto["saude_sqlite"]["score_sqlite"],
                }
            )

    if st.button("Salvar decisão SQLite", key="salvar_decisao_sqlite_valoris"):
        registro = salvar_decisao_sqlite(
            {
                "tabelas_criadas": saude["tabelas_criadas"],
                "linhas_migradas": saude["linhas_totais"],
                "score_sqlite": saude["score_sqlite"],
                "decisao": saude["decisao"],
                "proximo_passo": saude["proximo_passo"],
                "observacoes": "Decisão gerada pelo piloto SQLite.",
            }
        )
        st.success(f"Decisão salva: {registro['decisao']}")
        st.rerun()


def _renderizar_tabelas(saude: Dict[str, Any]) -> None:
    st.markdown("### Tabelas SQLite")

    if not saude["tabelas_existentes"]:
        st.info("Nenhuma tabela SQLite criada ainda.")
        return

    for tabela, linhas in saude["linhas_por_tabela"].items():
        with st.container(border=True):
            st.markdown(f"**{tabela}**")
            st.caption(f"{linhas} linha(s)")

            preview = carregar_preview_sqlite(tabela, limite=3)

            if preview:
                with st.expander("Preview", expanded=False):
                    st.json(preview)


def _renderizar_consulta() -> None:
    st.markdown("### Consulta rápida")

    tabelas = listar_tabelas_sqlite()

    if not tabelas:
        st.info("Crie o schema SQLite antes de consultar.")
        return

    tabela = st.selectbox(
        "Tabela",
        tabelas,
        key="consulta_tabela_sqlite_valoris",
    )

    limite = st.slider(
        "Limite de linhas",
        min_value=1,
        max_value=20,
        value=5,
        key="consulta_limite_sqlite_valoris",
    )

    if st.button("Consultar tabela", key="consultar_tabela_sqlite_valoris"):
        registros = carregar_preview_sqlite(tabela, limite=limite)
        st.json(registros)


def _renderizar_schema() -> None:
    st.markdown("### Schema SQLite")

    schema = gerar_schema_sqlite()
    st.code(schema, language="sql")

    st.download_button(
        "Baixar schema SQLite (.sql)",
        data=schema,
        file_name="valoris_schema_sqlite.sql",
        mime="text/sql",
        key="download_schema_sqlite_valoris",
    )


def _renderizar_logs() -> None:
    logs = carregar_logs_sqlite()

    st.markdown("### Logs SQLite")

    if not logs:
        st.info("Ainda não há logs SQLite.")
        return

    for item in reversed(logs[-20:]):
        with st.container(border=True):
            st.markdown(f"**{item.get('operacao', 'N/D')}** — {item.get('status', 'N/D')}")
            st.caption(f"{item.get('data_registro', 'N/D')} • {item.get('tabela_logica', 'N/D')} → {item.get('tabela_sqlite', 'N/D')}")
            st.markdown(item.get("detalhe", ""))


def _renderizar_historico() -> None:
    historico = carregar_decisoes_sqlite()

    st.markdown("### Histórico de decisões SQLite")

    if not historico:
        st.info("Ainda não há decisões SQLite salvas.")
        return

    for item in reversed(historico[-10:]):
        with st.container(border=True):
            st.markdown(f"**{item.get('decisao', 'N/D')}**")
            st.caption(item.get("data_registro", "N/D"))
            st.markdown(f"Score: {item.get('score_sqlite', 'N/D')}/100")
            st.markdown(f"Tabelas: {item.get('tabelas_criadas', 'N/D')} • Linhas: {item.get('linhas_migradas', 'N/D')}")
            st.markdown(f"Próximo passo: {item.get('proximo_passo', 'N/D')}")


def renderizar_piloto_sqlite_valoris() -> None:
    _injetar_css_sqlite()
    _renderizar_hero()

    saude = calcular_saude_sqlite()

    _renderizar_metricas(saude)

    st.divider()

    _renderizar_acoes(saude)

    st.divider()

    st.download_button(
        "Baixar relatório SQLite (.md)",
        data=_gerar_markdown_sqlite(saude),
        file_name="piloto_sqlite_valoris.md",
        mime="text/markdown",
        key="download_piloto_sqlite_valoris",
    )

    st.download_button(
        "Baixar decisões SQLite (.csv)",
        data=gerar_csv_decisoes_sqlite(),
        file_name="decisoes_sqlite_valoris.csv",
        mime="text/csv",
        key="download_decisoes_sqlite_valoris",
    )

    st.download_button(
        "Baixar logs SQLite (.csv)",
        data=gerar_csv_logs_sqlite(),
        file_name="logs_sqlite_valoris.csv",
        mime="text/csv",
        key="download_logs_sqlite_valoris",
    )

    st.divider()

    _renderizar_tabelas(saude)

    st.divider()

    _renderizar_consulta()

    st.divider()

    _renderizar_schema()

    st.divider()

    _renderizar_logs()

    st.divider()

    _renderizar_historico()

    st.markdown(
        """
        <div class="sqlite-note">
            <strong>Regra SQLite:</strong> este banco é piloto local. Ele serve para testar contratos,
            migração e repositórios antes de conectar PostgreSQL/Supabase.
        </div>
        """,
        unsafe_allow_html=True,
    )


def executar_autoteste_piloto_sqlite_valoris() -> List[Dict[str, str]]:
    schema = gerar_schema_sqlite()
    saude = calcular_saude_sqlite()

    return [
        {
            "teste": "versao_sqlite",
            "status": "OK" if VERSAO_PILOTO_SQLITE_VALORIS == "3.8.58" else "FALHA",
            "detalhe": VERSAO_PILOTO_SQLITE_VALORIS,
        },
        {
            "teste": "schema",
            "status": "OK" if "CREATE TABLE" in schema else "FALHA",
            "detalhe": "Schema gerado.",
        },
        {
            "teste": "score_sqlite",
            "status": "OK" if 0 <= saude["score_sqlite"] <= 100 else "FALHA",
            "detalhe": str(saude["score_sqlite"]),
        },
    ]
