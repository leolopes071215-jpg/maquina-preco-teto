# repositorios_valoris.py

from __future__ import annotations

import csv
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Protocol
from uuid import uuid4

import streamlit as st

from gateway_dados_valoris import (
    CONTRATOS_TABELAS_VALORIS,
    carregar_tabela_logica,
    validar_contrato_tabela,
)
from piloto_sqlite_valoris import (
    CAMINHO_BANCO_SQLITE,
    _normalizar_nome_tabela,
    calcular_saude_sqlite,
    criar_schema_sqlite,
    migrar_tabela_para_sqlite,
)


# ============================================================
# VALORIS
# v3.8.59 — Repositórios de Dados e Adapter Strategy
# ------------------------------------------------------------
# Esta versão começa a separar oficialmente:
#
# Interface Streamlit → Repositório → Adapter → CSV/SQLite
#
# Objetivo:
# - padronizar acesso a dados;
# - testar CSV vs SQLite;
# - preparar futura troca para PostgreSQL/Supabase;
# - criar uma camada que poderá ser usada pela FastAPI.
# ============================================================


VERSAO_REPOSITORIOS_VALORIS = "3.8.59"

CAMINHO_DECISOES_REPOSITORIOS = Path("decisoes_repositorios_valoris.csv")
CAMINHO_LOGS_REPOSITORIOS = Path("logs_repositorios_valoris.csv")
CAMINHO_MANIFESTO_REPOSITORIOS = Path("manifesto_repositorios_valoris.json")

CAMPOS_DECISAO_REPOSITORIOS = [
    "id",
    "data_registro",
    "adapter_recomendado",
    "score_repositorio",
    "tabelas_testadas",
    "leituras_ok",
    "decisao",
    "proximo_passo",
    "observacoes",
]

CAMPOS_LOG_REPOSITORIOS = [
    "id",
    "data_registro",
    "adapter",
    "operacao",
    "tabela_logica",
    "status",
    "linhas",
    "detalhe",
]


class AdapterDados(Protocol):
    nome: str

    def listar(self, tabela_logica: str, limite: int = 50) -> List[Dict[str, Any]]:
        ...

    def contar(self, tabela_logica: str) -> int:
        ...


class CsvAdapter:
    nome = "CSV"

    def listar(self, tabela_logica: str, limite: int = 50) -> List[Dict[str, Any]]:
        registros = carregar_tabela_logica(tabela_logica)
        return registros[:limite]

    def contar(self, tabela_logica: str) -> int:
        return len(carregar_tabela_logica(tabela_logica))


class SqliteAdapter:
    nome = "SQLite"

    def listar(self, tabela_logica: str, limite: int = 50) -> List[Dict[str, Any]]:
        tabela_sqlite = _normalizar_nome_tabela(tabela_logica)

        if not CAMINHO_BANCO_SQLITE.exists():
            return []

        try:
            with sqlite3.connect(CAMINHO_BANCO_SQLITE) as conexao:
                conexao.row_factory = sqlite3.Row
                cursor = conexao.execute(
                    f"SELECT * FROM {tabela_sqlite} LIMIT ?",
                    (limite,),
                )
                return [dict(linha) for linha in cursor.fetchall()]
        except Exception:
            return []

    def contar(self, tabela_logica: str) -> int:
        tabela_sqlite = _normalizar_nome_tabela(tabela_logica)

        if not CAMINHO_BANCO_SQLITE.exists():
            return 0

        try:
            with sqlite3.connect(CAMINHO_BANCO_SQLITE) as conexao:
                conexao.row_factory = sqlite3.Row
                cursor = conexao.execute(f"SELECT COUNT(*) as total FROM {tabela_sqlite}")
                linha = cursor.fetchone()
                return int(linha["total"]) if linha else 0
        except Exception:
            return 0


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


def registrar_log_repositorio(
    adapter: str,
    operacao: str,
    tabela_logica: str,
    status: str,
    linhas: int,
    detalhe: str,
) -> None:
    try:
        _garantir_csv(CAMINHO_LOGS_REPOSITORIOS, CAMPOS_LOG_REPOSITORIOS)

        registro = {
            "id": str(uuid4())[:8],
            "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "adapter": _limpar_texto(adapter),
            "operacao": _limpar_texto(operacao),
            "tabela_logica": _limpar_texto(tabela_logica),
            "status": _limpar_texto(status),
            "linhas": str(linhas),
            "detalhe": _limpar_texto(detalhe),
        }

        with CAMINHO_LOGS_REPOSITORIOS.open("a", newline="", encoding="utf-8") as arquivo:
            escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_LOG_REPOSITORIOS)
            escritor.writerow(registro)
    except Exception:
        return


def carregar_logs_repositorios(max_registros: int = 300) -> List[Dict[str, str]]:
    """
    Carrega apenas os ?ltimos logs para evitar MemoryError no Streamlit.

    Antes, esta fun??o fazia list(leitor), carregando o CSV inteiro.
    Em arquivos de log grandes, isso estourava mem?ria.
    """
    from collections import deque

    _garantir_csv(CAMINHO_LOGS_REPOSITORIOS, CAMPOS_LOG_REPOSITORIOS)

    try:
        with CAMINHO_LOGS_REPOSITORIOS.open("r", newline="", encoding="utf-8") as arquivo:
            leitor = csv.DictReader(arquivo)
            ultimos = deque(leitor, maxlen=max_registros)
            return list(ultimos)
    except MemoryError:
        return []
    except Exception:
        return []


def gerar_csv_logs_repositorios(max_registros: int = 500) -> str:
    """
    Gera download apenas dos ?ltimos registros, evitando ler arquivo gigante inteiro.
    """
    import io

    _garantir_csv(CAMINHO_LOGS_REPOSITORIOS, CAMPOS_LOG_REPOSITORIOS)

    logs = carregar_logs_repositorios(max_registros=max_registros)

    saida = io.StringIO()
    escritor = csv.DictWriter(saida, fieldnames=CAMPOS_LOG_REPOSITORIOS)
    escritor.writeheader()

    for item in logs:
        escritor.writerow({campo: item.get(campo, "") for campo in CAMPOS_LOG_REPOSITORIOS})

    return saida.getvalue()


def carregar_decisoes_repositorios() -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_DECISOES_REPOSITORIOS, CAMPOS_DECISAO_REPOSITORIOS)

    with CAMINHO_DECISOES_REPOSITORIOS.open("r", newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        return list(leitor)


def gerar_csv_decisoes_repositorios() -> str:
    _garantir_csv(CAMINHO_DECISOES_REPOSITORIOS, CAMPOS_DECISAO_REPOSITORIOS)

    return CAMINHO_DECISOES_REPOSITORIOS.read_text(encoding="utf-8")


def salvar_decisao_repositorios(decisao: Dict[str, Any]) -> Dict[str, str]:
    _garantir_csv(CAMINHO_DECISOES_REPOSITORIOS, CAMPOS_DECISAO_REPOSITORIOS)

    registro = {
        "id": str(uuid4())[:8],
        "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "adapter_recomendado": _limpar_texto(decisao.get("adapter_recomendado", "")),
        "score_repositorio": str(decisao.get("score_repositorio", "")),
        "tabelas_testadas": str(decisao.get("tabelas_testadas", "")),
        "leituras_ok": str(decisao.get("leituras_ok", "")),
        "decisao": _limpar_texto(decisao.get("decisao", "")),
        "proximo_passo": _limpar_texto(decisao.get("proximo_passo", "")),
        "observacoes": _limpar_texto(decisao.get("observacoes", "")),
    }

    with CAMINHO_DECISOES_REPOSITORIOS.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISAO_REPOSITORIOS)
        escritor.writerow(registro)

    return registro


def obter_adapter(nome_adapter: str) -> AdapterDados:
    if nome_adapter == "SQLite":
        return SqliteAdapter()

    return CsvAdapter()


def listar_via_repositorio(
    tabela_logica: str,
    adapter_nome: str = "CSV",
    limite: int = 50,
) -> List[Dict[str, Any]]:
    adapter = obter_adapter(adapter_nome)

    try:
        registros = adapter.listar(tabela_logica=tabela_logica, limite=limite)

        registrar_log_repositorio(
            adapter=adapter.nome,
            operacao="listar",
            tabela_logica=tabela_logica,
            status="ok",
            linhas=len(registros),
            detalhe=f"{len(registros)} registro(s) lido(s).",
        )

        return registros

    except Exception as erro:
        registrar_log_repositorio(
            adapter=adapter.nome,
            operacao="listar",
            tabela_logica=tabela_logica,
            status="erro",
            linhas=0,
            detalhe=str(erro),
        )

        return []


def contar_via_repositorio(
    tabela_logica: str,
    adapter_nome: str = "CSV",
) -> int:
    adapter = obter_adapter(adapter_nome)

    try:
        total = adapter.contar(tabela_logica=tabela_logica)

        registrar_log_repositorio(
            adapter=adapter.nome,
            operacao="contar",
            tabela_logica=tabela_logica,
            status="ok",
            linhas=total,
            detalhe=f"{total} registro(s) encontrado(s).",
        )

        return total

    except Exception as erro:
        registrar_log_repositorio(
            adapter=adapter.nome,
            operacao="contar",
            tabela_logica=tabela_logica,
            status="erro",
            linhas=0,
            detalhe=str(erro),
        )

        return 0


def comparar_csv_sqlite(tabela_logica: str) -> Dict[str, Any]:
    contrato = validar_contrato_tabela(tabela_logica)
    total_csv = contar_via_repositorio(tabela_logica=tabela_logica, adapter_nome="CSV")
    total_sqlite = contar_via_repositorio(tabela_logica=tabela_logica, adapter_nome="SQLite")

    diferenca = abs(total_csv - total_sqlite)

    if not contrato.get("existe_arquivo", False) and total_sqlite == 0:
        status = "Sem dados"
    elif diferenca == 0:
        status = "Sincronizado"
    elif total_sqlite == 0 and total_csv > 0:
        status = "Precisa migrar para SQLite"
    else:
        status = "Divergente"

    return {
        "tabela_logica": tabela_logica,
        "arquivo_csv": contrato.get("arquivo_csv", ""),
        "status_contrato": contrato.get("status", ""),
        "total_csv": total_csv,
        "total_sqlite": total_sqlite,
        "diferenca": diferenca,
        "status": status,
    }


def comparar_todas_tabelas() -> List[Dict[str, Any]]:
    return [
        comparar_csv_sqlite(tabela_logica)
        for tabela_logica in CONTRATOS_TABELAS_VALORIS.keys()
    ]


def calcular_saude_repositorios() -> Dict[str, Any]:
    comparacoes = comparar_todas_tabelas()
    saude_sqlite = calcular_saude_sqlite()

    tabelas_testadas = len(comparacoes)
    leituras_ok = len([item for item in comparacoes if item["status"] in ["Sincronizado", "Sem dados"]])
    precisam_migrar = len([item for item in comparacoes if item["status"] == "Precisa migrar para SQLite"])
    divergentes = len([item for item in comparacoes if item["status"] == "Divergente"])

    score = 25
    score += min(tabelas_testadas * 4, 28)
    score += min(leituras_ok * 6, 36)
    score += min(saude_sqlite.get("score_sqlite", 0) * 0.25, 25)
    score -= precisam_migrar * 4
    score -= divergentes * 8

    score = int(round(max(0, min(100, score))))

    if score >= 82:
        decisao = "Repositórios prontos para módulos novos"
        proximo_passo = "Começar a criar módulos novos usando o repositório em vez de CSV direto."
        adapter_recomendado = "SQLite"
    elif score >= 62:
        decisao = "Repositórios funcionais com ajustes"
        proximo_passo = "Migrar tabelas pendentes e usar adapter SQLite apenas em testes internos."
        adapter_recomendado = "CSV/SQLite híbrido"
    elif score >= 42:
        decisao = "Repositórios em validação"
        proximo_passo = "Manter CSV como fonte principal e validar sincronização com SQLite."
        adapter_recomendado = "CSV"
    else:
        decisao = "Ainda cedo para depender do repositório"
        proximo_passo = "Criar schema SQLite, migrar dados e repetir comparação."
        adapter_recomendado = "CSV"

    return {
        "comparacoes": comparacoes,
        "score_repositorio": score,
        "tabelas_testadas": tabelas_testadas,
        "leituras_ok": leituras_ok,
        "precisam_migrar": precisam_migrar,
        "divergentes": divergentes,
        "adapter_recomendado": adapter_recomendado,
        "decisao": decisao,
        "proximo_passo": proximo_passo,
        "score_sqlite": saude_sqlite.get("score_sqlite", 0),
    }


def gerar_manifesto_repositorios() -> Dict[str, Any]:
    saude = calcular_saude_repositorios()

    manifesto = {
        "versao": VERSAO_REPOSITORIOS_VALORIS,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "adapter_recomendado": saude["adapter_recomendado"],
        "score_repositorio": saude["score_repositorio"],
        "decisao": saude["decisao"],
        "proximo_passo": saude["proximo_passo"],
        "comparacoes": saude["comparacoes"],
    }

    CAMINHO_MANIFESTO_REPOSITORIOS.write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    registrar_log_repositorio(
        adapter="Repository",
        operacao="manifest",
        tabela_logica="all",
        status="ok",
        linhas=len(saude["comparacoes"]),
        detalhe="Manifesto de repositórios gerado.",
    )

    return manifesto


def _gerar_markdown_repositorios(saude: Dict[str, Any]) -> str:
    linhas = "\n".join(
        [
            f"| {item['tabela_logica']} | {item['total_csv']} | {item['total_sqlite']} | {item['diferenca']} | {item['status']} |"
            for item in saude["comparacoes"]
        ]
    )

    return f"""# Repositórios de Dados — Valoris

Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Diagnóstico

Score Repositório: {saude["score_repositorio"]}/100  
Adapter recomendado: {saude["adapter_recomendado"]}  
Decisão: {saude["decisao"]}  
Próximo passo: {saude["proximo_passo"]}

Tabelas testadas: {saude["tabelas_testadas"]}  
Leituras OK: {saude["leituras_ok"]}  
Precisam migrar: {saude["precisam_migrar"]}  
Divergentes: {saude["divergentes"]}  
Score SQLite: {saude["score_sqlite"]}/100  

## Comparação CSV vs SQLite

| Tabela lógica | CSV | SQLite | Diferença | Status |
|---|---:|---:|---:|---|
{linhas}

## Arquitetura desejada

Streamlit → Repositório → Adapter → CSV/SQLite/PostgreSQL

## Próxima evolução

1. Criar `PostgresAdapter`.
2. Conectar Supabase/PostgreSQL.
3. Substituir leitura direta de CSV nos módulos novos.
4. Expor repositórios via FastAPI.
"""


def _injetar_css_repositorios() -> None:
    st.markdown(
        """
        <style>
            .repo-hero {
                padding: clamp(1.18rem, 3vw, 2rem);
                border-radius: 30px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    radial-gradient(circle at top left, rgba(214, 181, 109, 0.26), transparent 30%),
                    radial-gradient(circle at bottom right, rgba(74, 144, 226, 0.22), transparent 34%),
                    linear-gradient(135deg, rgba(8, 15, 27, 0.99), rgba(5, 9, 18, 0.99));
                box-shadow: 0 18px 58px rgba(0, 0, 0, 0.31);
                margin-bottom: 1rem;
            }

            .repo-eyebrow {
                color: #d6b56d;
                font-size: 0.74rem;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                font-weight: 880;
                margin-bottom: 0.35rem;
            }

            .repo-title {
                color: #f4f7fb;
                font-size: clamp(1.75rem, 5.4vw, 3.1rem);
                font-weight: 950;
                line-height: 1.02;
                letter-spacing: -0.058em;
                margin-bottom: 0.55rem;
            }

            .repo-subtitle {
                color: rgba(244, 247, 251, 0.75);
                font-size: clamp(0.94rem, 2.2vw, 1.06rem);
                line-height: 1.56;
                max-width: 1020px;
            }

            .repo-note {
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
        <div class="repo-hero">
            <div class="repo-eyebrow">Valoris • Repositórios • v{VERSAO_REPOSITORIOS_VALORIS}</div>
            <div class="repo-title">Comece a separar regra de negócio e persistência.</div>
            <div class="repo-subtitle">
                Esta camada permite ler dados via CSV ou SQLite usando o mesmo contrato.
                É a preparação direta para PostgreSQL/Supabase e FastAPI.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _renderizar_metricas(saude: Dict[str, Any]) -> None:
    st.markdown("### Diagnóstico dos repositórios")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Score", f"{saude['score_repositorio']}/100")

    with col_2:
        st.metric("Adapter", saude["adapter_recomendado"])

    with col_3:
        st.metric("Leituras OK", saude["leituras_ok"])

    with col_4:
        st.metric("Divergentes", saude["divergentes"])

    st.progress(saude["score_repositorio"] / 100)

    if saude["score_repositorio"] >= 70:
        st.success(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    elif saude["score_repositorio"] >= 42:
        st.warning(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    else:
        st.info(f"**{saude['decisao']}** — {saude['proximo_passo']}")


def _renderizar_comparacoes(saude: Dict[str, Any]) -> None:
    st.markdown("### Comparação CSV vs SQLite")

    for item in saude["comparacoes"]:
        with st.container(border=True):
            st.markdown(f"**{item['tabela_logica']}** — {item['status']}")
            st.caption(f"Arquivo: {item['arquivo_csv']} • Contrato: {item['status_contrato']}")
            col_1, col_2, col_3 = st.columns(3)

            with col_1:
                st.metric("CSV", item["total_csv"])

            with col_2:
                st.metric("SQLite", item["total_sqlite"])

            with col_3:
                st.metric("Diferença", item["diferenca"])


def _renderizar_teste_leitura() -> None:
    st.markdown("### Teste de leitura por repositório")

    col_1, col_2, col_3 = st.columns(3)

    with col_1:
        tabela = st.selectbox(
            "Tabela lógica",
            list(CONTRATOS_TABELAS_VALORIS.keys()),
            key="repo_tabela_teste",
        )

    with col_2:
        adapter = st.selectbox(
            "Adapter",
            ["CSV", "SQLite"],
            key="repo_adapter_teste",
        )

    with col_3:
        limite = st.slider(
            "Limite",
            min_value=1,
            max_value=20,
            value=5,
            key="repo_limite_teste",
        )

    if st.button("Ler via repositório", key="repo_ler_via_repositorio"):
        registros = listar_via_repositorio(
            tabela_logica=tabela,
            adapter_nome=adapter,
            limite=limite,
        )

        st.success(f"{len(registros)} registro(s) lido(s) via {adapter}.")

        if registros:
            st.json(registros)


def _renderizar_acoes(saude: Dict[str, Any]) -> None:
    st.markdown("### Ações controladas")

    col_1, col_2, col_3 = st.columns(3)

    with col_1:
        if st.button("Criar schema SQLite se necessário", key="repo_criar_schema_sqlite"):
            criar_schema_sqlite()
            st.success("Schema SQLite criado/verificado.")
            st.rerun()

    with col_2:
        tabela = st.selectbox(
            "Migrar tabela específica",
            list(CONTRATOS_TABELAS_VALORIS.keys()),
            key="repo_migrar_tabela",
        )

        if st.button("Migrar tabela selecionada", key="repo_migrar_tabela_btn"):
            resultado = migrar_tabela_para_sqlite(tabela_logica=tabela, limpar_antes=True)
            st.success(f"{resultado['tabela_logica']}: {resultado['detalhe']}")
            st.rerun()

    with col_3:
        if st.button("Gerar manifesto de repositórios", key="repo_gerar_manifesto"):
            manifesto = gerar_manifesto_repositorios()
            st.success(f"Manifesto gerado: {CAMINHO_MANIFESTO_REPOSITORIOS}")
            st.json(
                {
                    "versao": manifesto["versao"],
                    "score": manifesto["score_repositorio"],
                    "adapter": manifesto["adapter_recomendado"],
                }
            )

    if st.button("Salvar decisão de repositórios", key="repo_salvar_decisao"):
        registro = salvar_decisao_repositorios(
            {
                "adapter_recomendado": saude["adapter_recomendado"],
                "score_repositorio": saude["score_repositorio"],
                "tabelas_testadas": saude["tabelas_testadas"],
                "leituras_ok": saude["leituras_ok"],
                "decisao": saude["decisao"],
                "proximo_passo": saude["proximo_passo"],
                "observacoes": "Decisão gerada pela camada de repositórios.",
            }
        )

        st.success(f"Decisão salva: {registro['decisao']}")
        st.rerun()


def _renderizar_logs() -> None:
    logs = carregar_logs_repositorios()

    st.markdown("### Logs dos repositórios")

    if not logs:
        st.info("Ainda não há logs de repositório.")
        return

    for item in reversed(logs[-20:]):
        with st.container(border=True):
            st.markdown(f"**{item.get('adapter', 'N/D')} / {item.get('operacao', 'N/D')}** — {item.get('status', 'N/D')}")
            st.caption(f"{item.get('data_registro', 'N/D')} • {item.get('tabela_logica', 'N/D')}")
            st.markdown(f"Linhas: {item.get('linhas', '0')} • {item.get('detalhe', '')}")


def _renderizar_historico() -> None:
    historico = carregar_decisoes_repositorios()

    st.markdown("### Histórico de decisões de repositórios")

    if not historico:
        st.info("Ainda não há decisões salvas.")
        return

    for item in reversed(historico[-10:]):
        with st.container(border=True):
            st.markdown(f"**{item.get('decisao', 'N/D')}**")
            st.caption(item.get("data_registro", "N/D"))
            st.markdown(f"Adapter: {item.get('adapter_recomendado', 'N/D')} • Score: {item.get('score_repositorio', 'N/D')}/100")
            st.markdown(f"Próximo passo: {item.get('proximo_passo', 'N/D')}")


def renderizar_repositorios_valoris() -> None:
    _injetar_css_repositorios()
    _renderizar_hero()

    saude = calcular_saude_repositorios()

    _renderizar_metricas(saude)

    st.divider()

    _renderizar_acoes(saude)

    st.divider()

    st.download_button(
        "Baixar relatório de repositórios (.md)",
        data=_gerar_markdown_repositorios(saude),
        file_name="repositorios_valoris.md",
        mime="text/markdown",
        key="download_repositorios_valoris",
    )

    st.download_button(
        "Baixar decisões de repositórios (.csv)",
        data=gerar_csv_decisoes_repositorios(),
        file_name="decisoes_repositorios_valoris.csv",
        mime="text/csv",
        key="download_decisoes_repositorios_valoris",
    )

    st.download_button(
        "Baixar logs de repositórios (.csv)",
        data=gerar_csv_logs_repositorios(),
        file_name="logs_repositorios_valoris.csv",
        mime="text/csv",
        key="download_logs_repositorios_valoris",
    )

    st.divider()

    _renderizar_comparacoes(saude)

    st.divider()

    _renderizar_teste_leitura()

    st.divider()

    _renderizar_logs()

    st.divider()

    _renderizar_historico()

    st.markdown(
        """
        <div class="repo-note">
            <strong>Regra dos repositórios:</strong> módulos novos não devem conversar diretamente com CSV.
            Eles devem conversar com o repositório, que decide se usa CSV, SQLite ou futuramente PostgreSQL.
        </div>
        """,
        unsafe_allow_html=True,
    )


def executar_autoteste_repositorios_valoris() -> List[Dict[str, str]]:
    saude = calcular_saude_repositorios()
    comparacoes = comparar_todas_tabelas()

    return [
        {
            "teste": "versao_repositorios",
            "status": "OK" if VERSAO_REPOSITORIOS_VALORIS == "3.8.59" else "FALHA",
            "detalhe": VERSAO_REPOSITORIOS_VALORIS,
        },
        {
            "teste": "comparacoes",
            "status": "OK" if len(comparacoes) >= 5 else "FALHA",
            "detalhe": str(len(comparacoes)),
        },
        {
            "teste": "score_repositorio",
            "status": "OK" if 0 <= saude["score_repositorio"] <= 100 else "FALHA",
            "detalhe": str(saude["score_repositorio"]),
        },
    ]
