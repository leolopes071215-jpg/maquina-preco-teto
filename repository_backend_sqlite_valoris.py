# repository_backend_sqlite_valoris.py
# Valoris — Repository com Backend SQLite Opcional v3.10.2
# ------------------------------------------------------------
# Objetivo:
# - Permitir que o Repository opere em modo CSV ou SQLite laboratório.
# - Manter CSV como padrão seguro.
# - Usar SQLite como backend opcional para testes controlados.
# - Preparar a transição gradual sem quebrar as páginas atuais.
# ------------------------------------------------------------

from __future__ import annotations

import csv
import json
import sqlite3
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st


VERSAO_REPOSITORY_BACKEND_SQLITE_VALORIS = "3.10.2"

CAMINHO_CONFIG = Path("config_backend_repositorio_valoris.json")
CAMINHO_LOG = Path("eventos_repository_backend_sqlite_valoris.csv")
CAMINHO_RELATORIO = Path("RELATORIO_REPOSITORY_BACKEND_SQLITE_VALORIS.md")
CAMINHO_MANIFESTO = Path("manifesto_repository_backend_sqlite_valoris.json")

CAMPOS_LOG = [
    "data_hora",
    "evento",
    "backend",
    "entidade",
    "status",
    "observacao",
]

BACKEND_CSV = "csv"
BACKEND_SQLITE = "sqlite_laboratorio"

ENTIDADE_TABELA_SQLITE = {
    "analises": "analises_ativos",
    "watchlist": "watchlist",
    "pipeline_acoes": "pipeline_acoes",
    "alertas": "alertas_revisoes",
    "decisoes": "decisoes",
    "eventos_repositorio": "eventos_sistema",
}

ALIASES_ENTIDADE = {
    "analise": "analises",
    "analises_ativos": "analises",
    "watch": "watchlist",
    "pipeline": "pipeline_acoes",
    "acoes": "pipeline_acoes",
    "alerta": "alertas",
    "alertas_revisoes": "alertas",
    "evento": "eventos_repositorio",
    "eventos": "eventos_repositorio",
    "eventos_sistema": "eventos_repositorio",
}


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


def registrar_evento(evento: str, backend: str, entidade: str, status: str, observacao: str = "") -> None:
    _garantir_csv(CAMINHO_LOG, CAMPOS_LOG)

    with CAMINHO_LOG.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_LOG)
        escritor.writerow(
            {
                "data_hora": _agora_iso(),
                "evento": evento,
                "backend": backend,
                "entidade": entidade,
                "status": status,
                "observacao": observacao,
            }
        )


def normalizar_entidade(entidade: str) -> str:
    chave = _txt(entidade).lower()

    if chave in ENTIDADE_TABELA_SQLITE:
        return chave

    return ALIASES_ENTIDADE.get(chave, chave)


def carregar_config_backend() -> Dict[str, Any]:
    if not CAMINHO_CONFIG.exists():
        return {
            "backend_padrao": BACKEND_CSV,
            "modo_sqlite": "laboratorio",
            "permitir_escrita_sqlite": False,
            "atualizado_em": _agora_iso(),
        }

    try:
        return json.loads(CAMINHO_CONFIG.read_text(encoding="utf-8"))
    except Exception:
        return {
            "backend_padrao": BACKEND_CSV,
            "modo_sqlite": "laboratorio",
            "permitir_escrita_sqlite": False,
            "atualizado_em": _agora_iso(),
        }


def salvar_config_backend(backend_padrao: str, permitir_escrita_sqlite: bool) -> Path:
    dados = {
        "backend_padrao": backend_padrao,
        "modo_sqlite": "laboratorio",
        "permitir_escrita_sqlite": bool(permitir_escrita_sqlite),
        "atualizado_em": _agora_iso(),
        "observacao": "CSV continua sendo o padrão seguro; SQLite é backend opcional de laboratório.",
    }

    CAMINHO_CONFIG.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")

    registrar_evento(
        evento="salvar_config_backend",
        backend=backend_padrao,
        entidade="config",
        status="ok",
        observacao=f"permitir_escrita_sqlite={permitir_escrita_sqlite}",
    )

    return CAMINHO_CONFIG


def obter_backend_padrao() -> str:
    config = carregar_config_backend()
    backend = config.get("backend_padrao", BACKEND_CSV)

    if backend not in {BACKEND_CSV, BACKEND_SQLITE}:
        return BACKEND_CSV

    return backend


def sqlite_disponivel() -> bool:
    try:
        from sqlite_local_valoris import CAMINHO_DB

        return Path(CAMINHO_DB).exists()
    except Exception:
        return Path("valoris_local.db").exists()


def caminho_db_sqlite() -> Path:
    try:
        from sqlite_local_valoris import CAMINHO_DB

        return Path(CAMINHO_DB)
    except Exception:
        return Path("valoris_local.db")


def conectar_sqlite() -> sqlite3.Connection:
    caminho = caminho_db_sqlite()
    conexao = sqlite3.connect(caminho)
    conexao.row_factory = sqlite3.Row
    return conexao


def garantir_schema_sqlite() -> None:
    try:
        from sqlite_local_valoris import criar_schema_sqlite

        criar_schema_sqlite()
    except Exception as exc:
        registrar_evento(
            evento="garantir_schema_sqlite",
            backend=BACKEND_SQLITE,
            entidade="schema",
            status="erro",
            observacao=str(exc),
        )
        raise


def campos_entidade(entidade: str) -> List[str]:
    try:
        from repositorio_unico_valoris import campos_entidade as campos_csv

        return list(campos_csv(entidade))
    except Exception:
        tabela = ENTIDADE_TABELA_SQLITE.get(normalizar_entidade(entidade), "")
        if not tabela or not sqlite_disponivel():
            return []

        with conectar_sqlite() as conexao:
            linhas = conexao.execute(f"PRAGMA table_info({tabela})").fetchall()

        return [linha["name"] for linha in linhas if linha["name"] not in {"id", "criado_em"}]


def tabela_sqlite(entidade: str) -> str:
    entidade_normalizada = normalizar_entidade(entidade)

    if entidade_normalizada not in ENTIDADE_TABELA_SQLITE:
        raise ValueError(f"Entidade sem tabela SQLite mapeada: {entidade}")

    return ENTIDADE_TABELA_SQLITE[entidade_normalizada]


def listar_registros_csv(entidade: str, max_registros: int = 800) -> List[Dict[str, Any]]:
    from repositorio_unico_valoris import listar_registros

    return listar_registros(entidade, max_registros=max_registros)


def salvar_registro_csv(entidade: str, dados: Dict[str, Any]) -> Dict[str, Any]:
    from repositorio_unico_valoris import salvar_registro

    return salvar_registro(entidade, dados)


def listar_registros_sqlite(entidade: str, max_registros: int = 800) -> List[Dict[str, Any]]:
    if not sqlite_disponivel():
        return []

    tabela = tabela_sqlite(entidade)

    with conectar_sqlite() as conexao:
        linhas = conexao.execute(
            f"SELECT * FROM {tabela} ORDER BY id DESC LIMIT ?",
            [int(max_registros)],
        ).fetchall()

    return [dict(linha) for linha in linhas]


def preparar_registro_sqlite(entidade: str, dados: Dict[str, Any]) -> Dict[str, Any]:
    campos = campos_entidade(entidade)
    tabela = tabela_sqlite(entidade)

    if not campos and sqlite_disponivel():
        with conectar_sqlite() as conexao:
            linhas = conexao.execute(f"PRAGMA table_info({tabela})").fetchall()
        campos = [linha["name"] for linha in linhas if linha["name"] not in {"id", "criado_em"}]

    registro = {campo: dados.get(campo, "") for campo in campos if campo not in {"id", "criado_em"}}

    if "data_hora" in registro and not _txt(registro.get("data_hora")):
        registro["data_hora"] = _agora_iso()

    if "ticker" in registro:
        registro["ticker"] = _txt(registro.get("ticker")).upper()

    for campo in list(registro.keys()):
        if campo.startswith("preco") or campo.startswith("score") or campo.startswith("margem"):
            valor = registro[campo]
            registro[campo] = _float(valor, None)

    return registro


def salvar_registro_sqlite(entidade: str, dados: Dict[str, Any]) -> Dict[str, Any]:
    config = carregar_config_backend()

    if not bool(config.get("permitir_escrita_sqlite", False)):
        raise PermissionError(
            "Escrita SQLite está desativada. Ative manualmente na página Repository Backend antes de salvar no SQLite."
        )

    garantir_schema_sqlite()

    tabela = tabela_sqlite(entidade)
    registro = preparar_registro_sqlite(entidade, dados)

    if not registro:
        raise ValueError("Registro vazio para salvar no SQLite.")

    campos = list(registro.keys())
    placeholders = ", ".join(["?"] * len(campos))
    colunas = ", ".join(campos)
    valores = [registro.get(campo) for campo in campos]

    with conectar_sqlite() as conexao:
        conexao.execute(f"INSERT INTO {tabela} ({colunas}) VALUES ({placeholders})", valores)
        conexao.commit()

    return registro


def listar_registros_backend(entidade: str, backend: Optional[str] = None, max_registros: int = 800) -> List[Dict[str, Any]]:
    entidade = normalizar_entidade(entidade)
    backend = backend or obter_backend_padrao()

    if backend == BACKEND_SQLITE:
        registros = listar_registros_sqlite(entidade, max_registros=max_registros)
    else:
        registros = listar_registros_csv(entidade, max_registros=max_registros)

    registrar_evento(
        evento="listar_registros_backend",
        backend=backend,
        entidade=entidade,
        status="ok",
        observacao=f"registros={len(registros)}",
    )

    return registros


def salvar_registro_backend(entidade: str, dados: Dict[str, Any], backend: Optional[str] = None) -> Dict[str, Any]:
    entidade = normalizar_entidade(entidade)
    backend = backend or obter_backend_padrao()

    if backend == BACKEND_SQLITE:
        registro = salvar_registro_sqlite(entidade, dados)
    else:
        registro = salvar_registro_csv(entidade, dados)

    registrar_evento(
        evento="salvar_registro_backend",
        backend=backend,
        entidade=entidade,
        status="ok",
        observacao="registro salvo",
    )

    return registro


def contar_registros_sqlite(entidade: str) -> int:
    if not sqlite_disponivel():
        return 0

    tabela = tabela_sqlite(entidade)

    try:
        with conectar_sqlite() as conexao:
            linha = conexao.execute(f"SELECT COUNT(*) AS total FROM {tabela}").fetchone()

        return int(linha["total"] or 0)
    except Exception:
        return 0


def contar_registros_csv(entidade: str) -> int:
    try:
        from repositorio_unico_valoris import contar_registros

        return int(contar_registros(entidade))
    except Exception:
        return len(listar_registros_csv(entidade, max_registros=100000))


def comparar_csv_sqlite() -> List[Dict[str, Any]]:
    linhas = []

    for entidade in ENTIDADE_TABELA_SQLITE:
        try:
            csv_total = contar_registros_csv(entidade)
        except Exception as exc:
            csv_total = 0
            csv_erro = str(exc)
        else:
            csv_erro = ""

        try:
            sqlite_total = contar_registros_sqlite(entidade)
        except Exception as exc:
            sqlite_total = 0
            sqlite_erro = str(exc)
        else:
            sqlite_erro = ""

        diferenca = sqlite_total - csv_total

        if sqlite_total == csv_total:
            status = "alinhado"
        elif sqlite_total > 0 and csv_total == 0:
            status = "sqlite_tem_dados"
        elif sqlite_total == 0 and csv_total > 0:
            status = "csv_tem_dados"
        else:
            status = "divergente"

        linhas.append(
            {
                "entidade": entidade,
                "tabela_sqlite": ENTIDADE_TABELA_SQLITE[entidade],
                "csv": csv_total,
                "sqlite": sqlite_total,
                "diferenca": diferenca,
                "status": status,
                "erro_csv": csv_erro,
                "erro_sqlite": sqlite_erro,
            }
        )

    return linhas


def calcular_metricas_backend() -> Dict[str, Any]:
    config = carregar_config_backend()
    comparacao = comparar_csv_sqlite()
    sqlite_ok = sqlite_disponivel()
    entidades_alinhadas = len([item for item in comparacao if item["status"] == "alinhado"])
    entidades_com_sqlite = len([item for item in comparacao if item["sqlite"] > 0])
    divergentes = len([item for item in comparacao if item["status"] == "divergente"])
    csv_tem_dados = len([item for item in comparacao if item["status"] == "csv_tem_dados"])

    score = 20

    if sqlite_ok:
        score += 25

    score += min(entidades_alinhadas * 8, 32)
    score += min(entidades_com_sqlite * 6, 18)

    if config.get("backend_padrao") == BACKEND_SQLITE:
        score += 5

    score -= min(divergentes * 10, 30)
    score -= min(csv_tem_dados * 4, 16)
    score = max(0, min(100, int(score)))

    if not sqlite_ok:
        risco = "Alto"
        decisao = "SQLite ainda não disponível"
        proximo = "Voltar em SQLite Local e criar/importar o banco laboratório."
    elif divergentes > 0:
        risco = "Médio"
        decisao = "Backend SQLite disponível, mas há divergências"
        proximo = "Comparar entidades divergentes antes de usar SQLite como padrão."
    elif score >= 80:
        risco = "Baixo"
        decisao = "Repository pronto para operar com SQLite opcional"
        proximo = "Usar SQLite em laboratório e começar a migrar páginas novas para o backend flexível."
    else:
        risco = "Médio"
        decisao = "Repository flexível funcional, mas ainda em validação"
        proximo = "Manter CSV como padrão e testar leituras SQLite por entidade."

    return {
        "versao": VERSAO_REPOSITORY_BACKEND_SQLITE_VALORIS,
        "backend_padrao": config.get("backend_padrao", BACKEND_CSV),
        "escrita_sqlite": bool(config.get("permitir_escrita_sqlite", False)),
        "sqlite_disponivel": sqlite_ok,
        "score_backend": score,
        "entidades": len(comparacao),
        "entidades_alinhadas": entidades_alinhadas,
        "entidades_com_sqlite": entidades_com_sqlite,
        "divergentes": divergentes,
        "csv_tem_dados": csv_tem_dados,
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo,
        "gerado_em": _agora_iso(),
    }


def gerar_relatorio_backend_markdown() -> str:
    metricas = calcular_metricas_backend()
    comparacao = comparar_csv_sqlite()

    linhas = "\n".join(
        [
            f"- **{item['entidade']}**: CSV={item['csv']} | SQLite={item['sqlite']} | status={item['status']}"
            for item in comparacao
        ]
    ) or "- Nenhuma entidade comparada."

    return f"""# Repository com Backend SQLite Opcional — Valoris

Versão: {VERSAO_REPOSITORY_BACKEND_SQLITE_VALORIS}  
Gerado em: {_agora_iso()}

## Diagnóstico

Backend padrão: {metricas['backend_padrao']}  
SQLite disponível: {'Sim' if metricas['sqlite_disponivel'] else 'Não'}  
Escrita SQLite ativa: {'Sim' if metricas['escrita_sqlite'] else 'Não'}  
Score backend: {metricas['score_backend']}/100  
Entidades alinhadas: {metricas['entidades_alinhadas']}  
Entidades com dados SQLite: {metricas['entidades_com_sqlite']}  
Divergentes: {metricas['divergentes']}  

Risco: {metricas['risco']}  
Decisão: {metricas['decisao']}  
Próximo passo: {metricas['proximo_passo']}

## Comparação CSV x SQLite

{linhas}

## Leitura estratégica

Esta versão cria a ponte entre o app atual e o banco. O usuário continua seguro no CSV, mas o produto já consegue testar SQLite como backend opcional.
"""


def salvar_relatorio_backend_markdown() -> Path:
    CAMINHO_RELATORIO.write_text(gerar_relatorio_backend_markdown(), encoding="utf-8")
    return CAMINHO_RELATORIO


def gerar_manifesto_backend() -> Dict[str, Any]:
    return {
        "produto": "Valoris",
        "versao": VERSAO_REPOSITORY_BACKEND_SQLITE_VALORIS,
        "modulo": "repository_backend_sqlite_valoris",
        "data_hora": _agora_iso(),
        "metricas": calcular_metricas_backend(),
        "comparacao": comparar_csv_sqlite(),
        "config": carregar_config_backend(),
        "principio": "CSV permanece seguro; SQLite entra como backend opcional de laboratório.",
        "proxima_etapa": "migrar páginas novas para listar_registros_backend/salvar_registro_backend",
    }


def salvar_manifesto_backend() -> Path:
    CAMINHO_MANIFESTO.write_text(
        json.dumps(gerar_manifesto_backend(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return CAMINHO_MANIFESTO


def renderizar_repository_backend_sqlite_valoris() -> None:
    st.subheader("Repository Backend")
    st.caption(
        "Controle de backend do Repository: CSV seguro por padrão, SQLite laboratório como opção gradual."
    )

    metricas = calcular_metricas_backend()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Score backend", f"{metricas['score_backend']}/100")
    col2.metric("Backend", metricas["backend_padrao"])
    col3.metric("SQLite", "Sim" if metricas["sqlite_disponivel"] else "Não")
    col4.metric("Alinhadas", metricas["entidades_alinhadas"])
    col5.metric("Divergentes", metricas["divergentes"])



    if metricas["risco"] == "Alto":
        st.error(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    elif metricas["risco"] == "Médio":
        st.warning(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    else:
        st.success(f"{metricas['decisao']} — {metricas['proximo_passo']}")

    st.divider()

    st.markdown("### Configuração do backend")

    config = carregar_config_backend()

    backend_escolhido = st.selectbox(
        "Backend padrão para funções flexíveis",
        [BACKEND_CSV, BACKEND_SQLITE],
        index=[BACKEND_CSV, BACKEND_SQLITE].index(config.get("backend_padrao", BACKEND_CSV)),
    )

    permitir_escrita = st.checkbox(
        "Permitir escrita em SQLite laboratório",
        value=bool(config.get("permitir_escrita_sqlite", False)),
        help="Mantenha desligado até validar bem as leituras. CSV continua sendo o modo mais seguro.",
    )

    if st.button("Salvar configuração de backend"):
        salvar_config_backend(backend_padrao=backend_escolhido, permitir_escrita_sqlite=permitir_escrita)
        st.success("Configuração salva.")
        st.rerun()

    st.info(
        "Recomendação atual: manter CSV como backend padrão e usar SQLite apenas para leitura/testes até a próxima validação."
    )

    st.divider()

    st.markdown("### Comparação CSV x SQLite")
    comparacao = comparar_csv_sqlite()
    st.dataframe(comparacao, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Testar leitura flexível")

    entidades = sorted(ENTIDADE_TABELA_SQLITE.keys())
    entidade = st.selectbox("Entidade", entidades)
    backend_teste = st.selectbox("Backend de teste", [BACKEND_CSV, BACKEND_SQLITE], index=0)
    limite = st.slider("Registros", 10, 500, 100)

    if st.button("Executar leitura flexível"):
        try:
            registros = listar_registros_backend(entidade, backend=backend_teste, max_registros=limite)
            st.success(f"Leitura concluída: {len(registros)} registro(s).")
            st.dataframe(registros, use_container_width=True, hide_index=True)
        except Exception as exc:
            st.error(str(exc))

    st.divider()

    st.markdown("### API flexível disponível")
    st.code(
        """
from repository_backend_sqlite_valoris import (
    listar_registros_backend,
    salvar_registro_backend,
    comparar_csv_sqlite,
    obter_backend_padrao,
)
""".strip(),
        language="python",
    )

    st.divider()

    st.markdown("### Relatórios")

    col1, col2 = st.columns(2)

    if col1.button("Salvar relatório do backend"):
        caminho = salvar_relatorio_backend_markdown()
        st.success(f"Relatório salvo em {caminho}")

    if col2.button("Salvar manifesto do backend"):
        caminho = salvar_manifesto_backend()
        st.success(f"Manifesto salvo em {caminho}")

    st.download_button(
        "Baixar relatório do backend (.md)",
        data=gerar_relatorio_backend_markdown(),
        file_name="RELATORIO_REPOSITORY_BACKEND_SQLITE_VALORIS.md",
        mime="text/markdown",
    )


def executar_autoteste_repository_backend_sqlite_valoris() -> Dict[str, Any]:
    metricas = calcular_metricas_backend()

    return {
        "ok": True,
        "versao": VERSAO_REPOSITORY_BACKEND_SQLITE_VALORIS,
        "metricas": {
            "score_backend": metricas["score_backend"],
            "sqlite_disponivel": metricas["sqlite_disponivel"],
            "backend_padrao": metricas["backend_padrao"],
        },
    }
