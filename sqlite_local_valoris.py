# sqlite_local_valoris.py
# Valoris — SQLite Local / Laboratório de Banco v3.10.1
from __future__ import annotations

import csv
import json
import shutil
import sqlite3
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st

VERSAO_SQLITE_LOCAL_VALORIS = "3.10.1"
CAMINHO_DB = Path("valoris_local.db")
CAMINHO_BACKUPS = Path("backups_sqlite_valoris")
CAMINHO_RELATORIO = Path("RELATORIO_SQLITE_LOCAL_VALORIS.md")
CAMINHO_MANIFESTO = Path("manifesto_sqlite_local_valoris.json")
CAMINHO_LOG = Path("eventos_sqlite_local_valoris.csv")
CAMPOS_LOG = ["data_hora", "evento", "tabela", "status", "linhas", "observacao"]

SCHEMA_SQL = {
    "ativos": """
        CREATE TABLE IF NOT EXISTS ativos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL UNIQUE,
            empresa TEXT,
            setor TEXT,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
            atualizado_em TEXT
        );
    """,
    "analises_ativos": """
        CREATE TABLE IF NOT EXISTS analises_ativos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT,
            nome_empresa TEXT,
            setor TEXT,
            preco_atual REAL,
            preco_teto REAL,
            margem_seguranca_atual REAL,
            score_qualidade REAL,
            score_risco REAL,
            score_valor REAL,
            score_final REAL,
            decisao TEXT,
            nivel_conviccao TEXT,
            modelo_preco_teto TEXT,
            observacao TEXT,
            data_hora TEXT,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """,
    "watchlist": """
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fundador_email TEXT,
            ticker TEXT,
            empresa TEXT,
            setor TEXT,
            preco_atual REAL,
            preco_teto REAL,
            margem_seguranca_atual REAL,
            status_oportunidade TEXT,
            prioridade TEXT,
            tese_resumo TEXT,
            principal_risco TEXT,
            proximo_evento TEXT,
            data_revisao TEXT,
            observacoes TEXT,
            data_hora TEXT,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """,
    "pipeline_acoes": """
        CREATE TABLE IF NOT EXISTS pipeline_acoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT,
            empresa TEXT,
            etapa TEXT,
            prioridade TEXT,
            acao TEXT,
            responsavel TEXT,
            prazo TEXT,
            status TEXT,
            observacao TEXT,
            data_hora TEXT,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """,
    "alertas_revisoes": """
        CREATE TABLE IF NOT EXISTS alertas_revisoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT,
            empresa TEXT,
            tipo_alerta TEXT,
            prioridade TEXT,
            status TEXT,
            prazo TEXT,
            descricao TEXT,
            acao_sugerida TEXT,
            observacao TEXT,
            data_hora TEXT,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """,
    "decisoes": """
        CREATE TABLE IF NOT EXISTS decisoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entidade TEXT,
            ticker TEXT,
            empresa TEXT,
            origem TEXT,
            acao TEXT,
            decisao TEXT,
            status TEXT,
            observacao TEXT,
            data_hora TEXT,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """,
    "eventos_sistema": """
        CREATE TABLE IF NOT EXISTS eventos_sistema (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            evento TEXT,
            entidade TEXT,
            backend TEXT,
            status TEXT,
            observacao TEXT,
            data_hora TEXT,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """,
    "migracoes": """
        CREATE TABLE IF NOT EXISTS migracoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            versao TEXT,
            origem TEXT,
            destino TEXT,
            linhas INTEGER,
            status TEXT,
            observacao TEXT,
            data_hora TEXT,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """,
}

MAPEAMENTO_IMPORTACAO = {
    "analises_ativos": {"arquivo": "analises_motor_ativos_valoris.csv", "campos": ["ticker", "nome_empresa", "setor", "preco_atual", "preco_teto", "margem_seguranca_atual", "score_qualidade", "score_risco", "score_valor", "score_final", "decisao", "nivel_conviccao", "modelo_preco_teto", "observacao", "data_hora"], "aliases": {}},
    "watchlist": {"arquivo": "watchlist_fundadores_valoris.csv", "campos": ["fundador_email", "ticker", "empresa", "setor", "preco_atual", "preco_teto", "margem_seguranca_atual", "status_oportunidade", "prioridade", "tese_resumo", "principal_risco", "proximo_evento", "data_revisao", "observacoes", "data_hora"], "aliases": {"data_hora": ["data_registro", "criado_em", "created_at"], "observacoes": ["observacao"], "margem_seguranca_atual": ["margem_segura", "margem_seguranca", "margem_segurança"]}},
    "pipeline_acoes": {"arquivo": "acoes_pipeline_decisao_valoris.csv", "campos": ["ticker", "empresa", "etapa", "prioridade", "acao", "responsavel", "prazo", "status", "observacao", "data_hora"], "aliases": {}},
    "alertas_revisoes": {"arquivo": "alertas_radar_revisoes_valoris.csv", "campos": ["ticker", "empresa", "tipo_alerta", "prioridade", "status", "prazo", "descricao", "acao_sugerida", "observacao", "data_hora"], "aliases": {}},
    "decisoes": {"arquivo": "decisoes_repositorio_unico_valoris.csv", "campos": ["entidade", "acao", "status", "observacao", "data_hora"], "aliases": {}},
    "eventos_sistema": {"arquivo": "eventos_repositorio_unico_valoris.csv", "campos": ["evento", "entidade", "backend", "status", "observacao", "data_hora"], "aliases": {}},
}
NUMERICOS = {"preco_atual", "preco_teto", "margem_seguranca_atual", "score_qualidade", "score_risco", "score_valor", "score_final"}

def _agora_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat(sep=" ")

def _txt(valor: Any) -> str:
    return "" if valor is None else str(valor).strip()

def _float(valor: Any, padrao: Optional[float] = None) -> Optional[float]:
    try:
        if valor is None:
            return padrao
        if isinstance(valor, str):
            valor = valor.replace("R$", "").replace("%", "").replace(".", "").replace(",", ".").strip()
            if valor == "":
                return padrao
        return float(valor)
    except Exception:
        return padrao

def _garantir_csv(caminho: Path, campos: List[str]) -> None:
    if caminho.exists():
        return
    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()

def registrar_evento_sqlite(evento: str, tabela: str, status: str, linhas: int = 0, observacao: str = "") -> None:
    _garantir_csv(CAMINHO_LOG, CAMPOS_LOG)
    with CAMINHO_LOG.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_LOG)
        escritor.writerow({"data_hora": _agora_iso(), "evento": evento, "tabela": tabela, "status": status, "linhas": linhas, "observacao": observacao})

def conectar() -> sqlite3.Connection:
    conexao = sqlite3.connect(CAMINHO_DB)
    conexao.row_factory = sqlite3.Row
    return conexao

def criar_schema_sqlite() -> Dict[str, Any]:
    tabelas_criadas = []
    with conectar() as conexao:
        for tabela, sql in SCHEMA_SQL.items():
            conexao.execute(sql)
            tabelas_criadas.append(tabela)
        conexao.commit()
    registrar_evento_sqlite("criar_schema", "todas", "ok", len(tabelas_criadas), "Schema SQLite criado/atualizado em modo laboratório.")
    return {"ok": True, "tabelas": tabelas_criadas, "db": str(CAMINHO_DB)}

def listar_tabelas_sqlite() -> List[str]:
    if not CAMINHO_DB.exists():
        return []
    with conectar() as conexao:
        linhas = conexao.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name").fetchall()
    return [linha["name"] for linha in linhas]

def contar_linhas_tabela(tabela: str) -> int:
    if not CAMINHO_DB.exists():
        return 0
    try:
        with conectar() as conexao:
            linha = conexao.execute(f"SELECT COUNT(*) AS total FROM {tabela}").fetchone()
        return int(linha["total"] or 0)
    except Exception:
        return 0

def carregar_csv_origem(caminho: Path, max_registros: int = 10000) -> List[Dict[str, str]]:
    if not caminho.exists():
        return []
    try:
        with caminho.open("r", newline="", encoding="utf-8", errors="replace") as arquivo:
            leitor = csv.DictReader(arquivo)
            return list(deque(leitor, maxlen=max_registros))
    except Exception:
        return []

def valor_com_alias(registro: Dict[str, str], campo: str, aliases: Dict[str, List[str]]) -> Any:
    if _txt(registro.get(campo)):
        return registro.get(campo)
    for alias in aliases.get(campo, []):
        if _txt(registro.get(alias)):
            return registro.get(alias)
    return ""

def normalizar_registro(registro: Dict[str, str], config: Dict[str, Any]) -> Dict[str, Any]:
    dados: Dict[str, Any] = {}
    aliases = config.get("aliases", {})
    for campo in config.get("campos", []):
        valor = valor_com_alias(registro, campo, aliases)
        if campo in NUMERICOS:
            dados[campo] = _float(valor, None)
        elif campo == "ticker":
            dados[campo] = _txt(valor).upper()
        else:
            dados[campo] = _txt(valor)
    if "data_hora" in dados and not dados["data_hora"]:
        dados["data_hora"] = _agora_iso()
    return dados

def limpar_tabelas_importacao() -> None:
    tabelas = list(MAPEAMENTO_IMPORTACAO.keys())
    with conectar() as conexao:
        for tabela in tabelas:
            conexao.execute(f"DELETE FROM {tabela}")
        conexao.commit()
    registrar_evento_sqlite("limpar_tabelas_importacao", ", ".join(tabelas), "ok", 0, "Tabelas laboratoriais limpas.")

def inserir_lote(tabela: str, registros: List[Dict[str, Any]]) -> int:
    if not registros:
        return 0
    campos = list(registros[0].keys())
    placeholders = ", ".join(["?"] * len(campos))
    sql = f"INSERT INTO {tabela} ({', '.join(campos)}) VALUES ({placeholders})"
    valores = [[registro.get(campo) for campo in campos] for registro in registros]
    with conectar() as conexao:
        conexao.executemany(sql, valores)
        conexao.commit()
    return len(registros)

def atualizar_cadastro_ativos() -> int:
    if not CAMINHO_DB.exists():
        return 0
    ativos: Dict[str, Dict[str, str]] = {}
    consultas = [
        ("analises_ativos", "SELECT ticker, nome_empresa AS empresa, setor FROM analises_ativos WHERE ticker IS NOT NULL AND ticker != ''"),
        ("watchlist", "SELECT ticker, empresa, setor FROM watchlist WHERE ticker IS NOT NULL AND ticker != ''"),
        ("pipeline_acoes", "SELECT ticker, empresa, '' AS setor FROM pipeline_acoes WHERE ticker IS NOT NULL AND ticker != ''"),
        ("alertas_revisoes", "SELECT ticker, empresa, '' AS setor FROM alertas_revisoes WHERE ticker IS NOT NULL AND ticker != ''"),
    ]
    with conectar() as conexao:
        tabelas = listar_tabelas_sqlite()
        for tabela, consulta in consultas:
            if tabela not in tabelas:
                continue
            try:
                linhas = conexao.execute(consulta).fetchall()
            except Exception:
                linhas = []
            for linha in linhas:
                ticker = _txt(linha["ticker"]).upper()
                if not ticker:
                    continue
                ativos.setdefault(ticker, {"ticker": ticker, "empresa": "", "setor": ""})
                if not ativos[ticker]["empresa"] and _txt(linha["empresa"]):
                    ativos[ticker]["empresa"] = _txt(linha["empresa"])
                if not ativos[ticker]["setor"] and _txt(linha["setor"]):
                    ativos[ticker]["setor"] = _txt(linha["setor"])
        for item in ativos.values():
            conexao.execute(
                """
                INSERT INTO ativos (ticker, empresa, setor, atualizado_em)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(ticker) DO UPDATE SET
                    empresa = COALESCE(NULLIF(excluded.empresa, ''), ativos.empresa),
                    setor = COALESCE(NULLIF(excluded.setor, ''), ativos.setor),
                    atualizado_em = excluded.atualizado_em
                """,
                [item["ticker"], item["empresa"], item["setor"], _agora_iso()],
            )
        conexao.commit()
    registrar_evento_sqlite("atualizar_cadastro_ativos", "ativos", "ok", len(ativos), "Cadastro único atualizado.")
    return len(ativos)

def importar_csvs_para_sqlite(limpar_antes: bool = True) -> Dict[str, Any]:
    criar_schema_sqlite()
    if limpar_antes:
        limpar_tabelas_importacao()
    resultados = []
    for tabela, config in MAPEAMENTO_IMPORTACAO.items():
        caminho = Path(config["arquivo"])
        origem = carregar_csv_origem(caminho)
        normalizados = [normalizar_registro(registro, config) for registro in origem]
        try:
            inseridos = inserir_lote(tabela, normalizados)
            status, erro = "ok", ""
        except Exception as exc:
            inseridos, status, erro = 0, "erro", str(exc)
        registrar_evento_sqlite("importar_csv", tabela, status, inseridos, erro or f"Origem: {caminho}")
        resultados.append({"tabela": tabela, "arquivo": str(caminho), "linhas_origem": len(origem), "linhas_importadas": inseridos, "status": status, "erro": erro})
    ativos = atualizar_cadastro_ativos()
    with conectar() as conexao:
        conexao.execute("INSERT INTO migracoes (versao, origem, destino, linhas, status, observacao, data_hora) VALUES (?, ?, ?, ?, ?, ?, ?)", [VERSAO_SQLITE_LOCAL_VALORIS, "csv", "sqlite", sum(item["linhas_importadas"] for item in resultados), "ok", f"Importação laboratório concluída. Ativos atualizados: {ativos}", _agora_iso()])
        conexao.commit()
    return {"ok": True, "resultados": resultados, "ativos_atualizados": ativos}

def criar_backup_banco() -> Optional[Path]:
    if not CAMINHO_DB.exists():
        return None
    CAMINHO_BACKUPS.mkdir(exist_ok=True)
    destino = CAMINHO_BACKUPS / f"valoris_local_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    shutil.copy2(CAMINHO_DB, destino)
    registrar_evento_sqlite("backup_banco", "database", "ok", 0, str(destino))
    return destino

def consultar_amostra_tabela(tabela: str, limite: int = 100) -> List[Dict[str, Any]]:
    if not CAMINHO_DB.exists() or tabela not in listar_tabelas_sqlite():
        return []
    with conectar() as conexao:
        linhas = conexao.execute(f"SELECT * FROM {tabela} LIMIT ?", [limite]).fetchall()
    return [dict(linha) for linha in linhas]

def diagnosticar_sqlite() -> List[Dict[str, Any]]:
    return [{"tabela": tabela, "linhas": contar_linhas_tabela(tabela)} for tabela in listar_tabelas_sqlite()]

def calcular_metricas_sqlite() -> Dict[str, Any]:
    existe = CAMINHO_DB.exists()
    tabelas = listar_tabelas_sqlite()
    diagnostico = diagnosticar_sqlite()
    total_linhas = sum(item["linhas"] for item in diagnostico)
    faltantes = sorted(set(SCHEMA_SQL.keys()) - set(tabelas))
    score = 0
    if existe:
        score += 25
    score += min(len(tabelas) * 6, 48)
    if not faltantes:
        score += 15
    if total_linhas > 0:
        score += 12
    score = max(0, min(100, int(score)))
    if not existe:
        risco, decisao, proximo = "Alto", "Banco ainda não criado", "Criar schema SQLite local em modo laboratório."
    elif faltantes:
        risco, decisao, proximo = "Médio/Alto", "Banco criado, mas schema incompleto", "Executar criação/atualização do schema."
    elif total_linhas == 0:
        risco, decisao, proximo = "Médio", "Banco criado, mas sem dados importados", "Importar CSVs para SQLite em modo laboratório."
    elif score >= 85:
        risco, decisao, proximo = "Baixo", "SQLite local pronto para testes de Repository", "Criar v3.10.2 para Repository com backend SQLite opcional."
    else:
        risco, decisao, proximo = "Médio", "SQLite local funcional em laboratório", "Testar amostras, backups e integridade antes de conectar páginas."
    return {"versao": VERSAO_SQLITE_LOCAL_VALORIS, "db": str(CAMINHO_DB), "existe": existe, "score_sqlite": score, "tabelas": len(tabelas), "tabelas_faltantes": faltantes, "linhas_totais": total_linhas, "diagnostico": diagnostico, "risco": risco, "decisao": decisao, "proximo_passo": proximo, "gerado_em": _agora_iso()}

def gerar_relatorio_sqlite_markdown() -> str:
    metricas = calcular_metricas_sqlite()
    linhas = "\n".join([f"- **{item['tabela']}**: {item['linhas']} linha(s)" for item in diagnosticar_sqlite()]) or "- Nenhuma tabela criada."
    faltantes = ", ".join(metricas["tabelas_faltantes"]) if metricas["tabelas_faltantes"] else "Nenhuma"
    return f"""# SQLite Local — Valoris

Versão: {VERSAO_SQLITE_LOCAL_VALORIS}  
Gerado em: {_agora_iso()}

## Diagnóstico

Banco: {metricas['db']}  
Existe: {'Sim' if metricas['existe'] else 'Não'}  
Score SQLite: {metricas['score_sqlite']}/100  
Tabelas criadas: {metricas['tabelas']}  
Tabelas faltantes: {faltantes}  
Linhas totais: {metricas['linhas_totais']}  

Risco: {metricas['risco']}  
Decisão: {metricas['decisao']}  
Próximo passo: {metricas['proximo_passo']}

## Tabelas

{linhas}

## Leitura estratégica

Este banco ainda é laboratorial. Ele não substitui o fluxo atual em CSV, mas prova que a Valoris já consegue estruturar dados em tabelas e preparar a troca futura do backend do Repository.
"""

def salvar_relatorio_sqlite_markdown() -> Path:
    CAMINHO_RELATORIO.write_text(gerar_relatorio_sqlite_markdown(), encoding="utf-8")
    return CAMINHO_RELATORIO

def gerar_manifesto_sqlite() -> Dict[str, Any]:
    return {"produto": "Valoris", "versao": VERSAO_SQLITE_LOCAL_VALORIS, "modulo": "sqlite_local_valoris", "data_hora": _agora_iso(), "metricas": calcular_metricas_sqlite(), "schema": list(SCHEMA_SQL.keys()), "mapeamento_importacao": MAPEAMENTO_IMPORTACAO, "principio": "banco local em laboratório antes de backend definitivo", "proxima_etapa": "repository com backend SQLite opcional"}

def salvar_manifesto_sqlite() -> Path:
    CAMINHO_MANIFESTO.write_text(json.dumps(gerar_manifesto_sqlite(), ensure_ascii=False, indent=2), encoding="utf-8")
    return CAMINHO_MANIFESTO

def renderizar_sqlite_local_valoris() -> None:
    st.subheader("SQLite Local")
    st.caption("Banco local em modo laboratório: cria schema, importa CSVs e valida tabelas sem substituir o fluxo atual.")
    metricas = calcular_metricas_sqlite()
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Score SQLite", f"{metricas['score_sqlite']}/100")
    col2.metric("Banco existe", "Sim" if metricas["existe"] else "Não")
    col3.metric("Tabelas", metricas["tabelas"])
    col4.metric("Linhas", metricas["linhas_totais"])
    col5.metric("Faltantes", len(metricas["tabelas_faltantes"]))
    if metricas["risco"] == "Alto":
        st.error(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    elif metricas["risco"] in {"Médio", "Médio/Alto"}:
        st.warning(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    else:
        st.success(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    st.divider()
    st.markdown("### Ações do banco local")
    col_a, col_b, col_c = st.columns(3)
    if col_a.button("Criar/atualizar schema SQLite"):
        resultado = criar_schema_sqlite()
        st.success(f"Schema criado/atualizado: {', '.join(resultado['tabelas'])}")
        st.rerun()
    limpar_antes = col_b.checkbox("Limpar tabelas antes de importar", value=True)
    if col_b.button("Importar CSVs para SQLite"):
        resultado = importar_csvs_para_sqlite(limpar_antes=limpar_antes)
        st.success("Importação concluída em modo laboratório.")
        st.json(resultado)
        st.rerun()
    if col_c.button("Criar backup do banco"):
        backup = criar_backup_banco()
        st.success(f"Backup criado: {backup}") if backup else st.warning("Banco ainda não existe para backup.")
    st.divider()
    st.markdown("### Diagnóstico das tabelas")
    st.dataframe(diagnosticar_sqlite(), use_container_width=True, hide_index=True)
    st.divider()
    st.markdown("### Navegar tabela")
    tabelas = listar_tabelas_sqlite()
    if tabelas:
        tabela = st.selectbox("Tabela", tabelas)
        limite = st.slider("Linhas para visualizar", 10, 500, 100)
        st.dataframe(consultar_amostra_tabela(tabela, limite=limite), use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma tabela criada ainda.")
    st.divider()
    st.markdown("### Relatórios")
    col1, col2 = st.columns(2)
    if col1.button("Salvar relatório SQLite"):
        st.success(f"Relatório salvo em {salvar_relatorio_sqlite_markdown()}")
    if col2.button("Salvar manifesto SQLite"):
        st.success(f"Manifesto salvo em {salvar_manifesto_sqlite()}")
    st.download_button("Baixar relatório SQLite (.md)", data=gerar_relatorio_sqlite_markdown(), file_name="RELATORIO_SQLITE_LOCAL_VALORIS.md", mime="text/markdown")

def executar_autoteste_sqlite_local_valoris() -> Dict[str, Any]:
    metricas = calcular_metricas_sqlite()
    return {"ok": True, "versao": VERSAO_SQLITE_LOCAL_VALORIS, "metricas": {"score_sqlite": metricas["score_sqlite"], "tabelas": metricas["tabelas"], "linhas_totais": metricas["linhas_totais"]}}
