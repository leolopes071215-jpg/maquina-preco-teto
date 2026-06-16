# simulador_migracao_banco_valoris.py
# Valoris — Simulador de Migração para Banco v3.10.0
# ------------------------------------------------------------
# Objetivo:
# - Simular a migração dos dados atuais em CSV para tabelas reais.
# - Validar campos, chaves, duplicidades, datas e valores antes do SQLite.
# - Preparar a próxima etapa: SQLite Local.
# ------------------------------------------------------------

from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict, deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st


VERSAO_SIMULADOR_MIGRACAO_BANCO_VALORIS = "3.10.0"

CAMINHO_RELATORIO = Path("RELATORIO_SIMULADOR_MIGRACAO_BANCO_VALORIS.md")
CAMINHO_MANIFESTO = Path("manifesto_simulador_migracao_banco_valoris.json")
CAMINHO_DECISOES = Path("decisoes_simulador_migracao_banco_valoris.csv")
CAMINHO_PLANO_SQL = Path("PLANO_SQLITE_VALORIS_v3_10_0.sql")

CAMPOS_DECISOES = [
    "data_hora",
    "tabela",
    "risco",
    "decisao",
    "observacao",
]

TIPOS_SUGERIDOS = {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "data_hora": "TEXT",
    "criado_em": "TEXT",
    "atualizado_em": "TEXT",
    "ticker": "TEXT",
    "empresa": "TEXT",
    "nome_empresa": "TEXT",
    "setor": "TEXT",
    "preco_atual": "REAL",
    "preco_teto": "REAL",
    "margem_seguranca_atual": "REAL",
    "score_qualidade": "REAL",
    "score_risco": "REAL",
    "score_valor": "REAL",
    "score_final": "REAL",
    "score_inteligente": "REAL",
    "prioridade": "TEXT",
    "status": "TEXT",
    "status_oportunidade": "TEXT",
    "decisao": "TEXT",
    "decisao_motor": "TEXT",
    "nivel_conviccao": "TEXT",
    "modelo_preco_teto": "TEXT",
    "observacao": "TEXT",
    "observacoes": "TEXT",
    "descricao": "TEXT",
    "acao": "TEXT",
    "acao_sugerida": "TEXT",
    "acao_recomendada": "TEXT",
    "proximo_passo": "TEXT",
    "proximo_evento": "TEXT",
    "data_revisao": "TEXT",
    "prazo": "TEXT",
    "responsavel": "TEXT",
    "fundador_email": "TEXT",
    "tese_resumo": "TEXT",
    "principal_risco": "TEXT",
    "tipo_alerta": "TEXT",
    "etapa": "TEXT",
    "backend": "TEXT",
    "evento": "TEXT",
    "entidade": "TEXT",
}

NUMERICOS = {
    "preco_atual",
    "preco_teto",
    "margem_seguranca_atual",
    "score_qualidade",
    "score_risco",
    "score_valor",
    "score_final",
    "score_inteligente",
}

DATAS = {
    "data_hora",
    "data_revisao",
    "prazo",
    "criado_em",
    "atualizado_em",
}

CHAVES_POR_ENTIDADE = {
    "analises": ["ticker", "data_hora"],
    "watchlist": ["ticker"],
    "pipeline_acoes": ["ticker", "acao", "prazo"],
    "alertas": ["ticker", "tipo_alerta", "prazo"],
    "decisoes": ["entidade", "acao", "data_hora"],
    "eventos_repositorio": ["evento", "entidade", "data_hora"],
}

ALIASES_CAMPOS_MIGRACAO = {
    "watchlist": {
        "data_hora": ["data_registro", "criado_em", "created_at"],
        "observacoes": ["observacao"],
    },
}

EXTRAS_IGNORADOS_MIGRACAO = {
    "watchlist": {"id", "data_registro"},
}


def campo_presente_ou_alias(entidade: str, campo: str, campos_arquivo: List[str]) -> bool:
    if campo in campos_arquivo:
        return True

    aliases = ALIASES_CAMPOS_MIGRACAO.get(entidade, {}).get(campo, [])

    return any(alias in campos_arquivo for alias in aliases)


def calcular_campos_faltantes_migracao(entidade: str, campos_esperados: List[str], campos_arquivo: List[str]) -> List[str]:
    return [
        campo
        for campo in campos_esperados
        if not campo_presente_ou_alias(entidade, campo, campos_arquivo)
    ]


def calcular_campos_extras_migracao(entidade: str, campos_esperados: List[str], campos_arquivo: List[str]) -> List[str]:
    aliases_usados = set()

    for aliases in ALIASES_CAMPOS_MIGRACAO.get(entidade, {}).values():
        aliases_usados.update(aliases)

    ignorados = EXTRAS_IGNORADOS_MIGRACAO.get(entidade, set())

    return [
        campo
        for campo in campos_arquivo
        if campo not in campos_esperados
        and campo not in aliases_usados
        and campo not in ignorados
    ]


def aplicar_aliases_vazios_migracao(
    entidade: str,
    vazios: Dict[str, int],
    registros: List[Dict[str, str]],
    campos_arquivo: List[str],
) -> Dict[str, int]:
    aliases_entidade = ALIASES_CAMPOS_MIGRACAO.get(entidade, {})

    for campo_esperado, aliases in aliases_entidade.items():
        campos_possiveis = [campo_esperado] + aliases

        if campo_esperado in vazios and any(campo in campos_arquivo for campo in campos_possiveis):
            vazios[campo_esperado] = sum(
                1
                for registro in registros
                if not any(_txt(registro.get(campo)) for campo in campos_possiveis)
            )

    return vazios



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


def _data_valida(valor: Any) -> bool:
    texto = _txt(valor)

    if not texto:
        return False

    formatos = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
    ]

    for formato in formatos:
        try:
            datetime.strptime(texto[:19], formato)
            return True
        except Exception:
            pass

    return False


def _nome_sql(nome: str) -> str:
    texto = _txt(nome).lower()
    texto = texto.replace("ç", "c").replace("ã", "a").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
    texto = re.sub(r"[^a-z0-9_]+", "_", texto)
    texto = re.sub(r"_+", "_", texto).strip("_")
    return texto or "campo"


def _garantir_csv(caminho: Path, campos: List[str]) -> None:
    if caminho.exists():
        return

    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()


def carregar_contratos_repository() -> Dict[str, Dict[str, Any]]:
    try:
        from repositorio_unico_valoris import CONTRATOS_REPOSITORIO

        return dict(CONTRATOS_REPOSITORIO)
    except Exception:
        return {
            "analises": {
                "arquivo": "analises_motor_ativos_valoris.csv",
                "tabela_futura": "analises_ativos",
                "chave_logica": "ticker",
                "criticidade": "Alta",
                "campos": [
                    "data_hora",
                    "ticker",
                    "nome_empresa",
                    "setor",
                    "preco_atual",
                    "preco_teto",
                    "margem_seguranca_atual",
                    "score_qualidade",
                    "score_risco",
                    "score_valor",
                    "score_final",
                    "decisao",
                    "nivel_conviccao",
                    "modelo_preco_teto",
                    "observacao",
                ],
            }
        }


def carregar_csv_seguro(caminho: Path, max_registros: int = 5000) -> List[Dict[str, str]]:
    if not caminho.exists():
        return []

    try:
        with caminho.open("r", newline="", encoding="utf-8", errors="replace") as arquivo:
            leitor = csv.DictReader(arquivo)
            return list(deque(leitor, maxlen=max_registros))
    except Exception:
        return []


def ler_cabecalho_csv(caminho: Path) -> List[str]:
    if not caminho.exists():
        return []

    try:
        with caminho.open("r", newline="", encoding="utf-8", errors="replace") as arquivo:
            leitor = csv.reader(arquivo)
            return next(leitor, [])
    except Exception:
        return []


def contar_linhas_csv(caminho: Path) -> int:
    if not caminho.exists():
        return 0

    total = 0

    try:
        with caminho.open("r", encoding="utf-8", errors="replace") as arquivo:
            for total, _ in enumerate(arquivo, start=1):
                pass

        return max(total - 1, 0)
    except Exception:
        return 0


def analisar_vazios(registros: List[Dict[str, str]], campos: List[str]) -> Dict[str, int]:
    vazios = {}

    for campo in campos:
        total_vazio = 0

        for registro in registros:
            if not _txt(registro.get(campo)):
                total_vazio += 1

        vazios[campo] = total_vazio

    return vazios


def analisar_numericos_invalidos(registros: List[Dict[str, str]], campos: List[str]) -> Dict[str, int]:
    invalidos = {}

    for campo in campos:
        if campo not in NUMERICOS:
            continue

        total = 0

        for registro in registros:
            valor = registro.get(campo)

            if _txt(valor) and _float(valor, None) is None:
                total += 1

        invalidos[campo] = total

    return invalidos


def analisar_datas_invalidas(registros: List[Dict[str, str]], campos: List[str]) -> Dict[str, int]:
    invalidas = {}

    for campo in campos:
        if campo not in DATAS:
            continue

        total = 0

        for registro in registros:
            valor = registro.get(campo)

            if _txt(valor) and not _data_valida(valor):
                total += 1

        invalidas[campo] = total

    return invalidas


def analisar_duplicidades(registros: List[Dict[str, str]], campos_chave: List[str]) -> Dict[str, Any]:
    if not campos_chave:
        return {"duplicados": 0, "amostras": []}

    contador = Counter()

    for registro in registros:
        chave = " | ".join(_txt(registro.get(campo)).upper() for campo in campos_chave)
        if chave.strip(" |"):
            contador[chave] += 1

    duplicados = {chave: qtd for chave, qtd in contador.items() if qtd > 1}
    amostras = [{"chave": chave, "ocorrencias": qtd} for chave, qtd in list(duplicados.items())[:20]]

    return {
        "duplicados": len(duplicados),
        "amostras": amostras,
    }


def simular_tabela(entidade: str, contrato: Dict[str, Any]) -> Dict[str, Any]:
    arquivo = Path(contrato.get("arquivo", ""))
    tabela = contrato.get("tabela_futura", entidade)
    campos_esperados = list(contrato.get("campos", []))
    campos_arquivo = ler_cabecalho_csv(arquivo)
    registros = carregar_csv_seguro(arquivo)
    linhas = contar_linhas_csv(arquivo)
    existe = arquivo.exists()

    campos_faltantes = calcular_campos_faltantes_migracao(entidade, campos_esperados, campos_arquivo) if campos_arquivo else []
    campos_extras = calcular_campos_extras_migracao(entidade, campos_esperados, campos_arquivo) if campos_arquivo else []
    vazios = analisar_vazios(registros, campos_esperados)
    vazios = aplicar_aliases_vazios_migracao(entidade, vazios, registros, campos_arquivo)
    numericos_invalidos = analisar_numericos_invalidos(registros, campos_esperados)
    datas_invalidas = analisar_datas_invalidas(registros, campos_esperados)
    chaves = CHAVES_POR_ENTIDADE.get(entidade, [contrato.get("chave_logica", "")])
    chaves = [campo for campo in chaves if campo]
    duplicidades = analisar_duplicidades(registros, chaves)

    campos_vazios_criticos = {
        campo: qtd
        for campo, qtd in vazios.items()
        if qtd > 0 and campo in {"ticker", "data_hora", "empresa", "nome_empresa", "preco_teto", "status", "prioridade"}
    }

    problemas: List[str] = []

    if not existe:
        problemas.append("Arquivo ainda não existe.")
    if campos_faltantes:
        problemas.append(f"Campos faltantes: {', '.join(campos_faltantes)}")
    if campos_extras:
        problemas.append(f"Campos extras: {', '.join(campos_extras)}")
    if campos_vazios_criticos:
        problemas.append(f"Campos críticos vazios: {campos_vazios_criticos}")
    if any(numericos_invalidos.values()):
        problemas.append(f"Numéricos inválidos: {numericos_invalidos}")
    if any(datas_invalidas.values()):
        problemas.append(f"Datas inválidas: {datas_invalidas}")
    if duplicidades["duplicados"] > 0 and entidade in {"watchlist"}:
        problemas.append(f"Duplicidades por chave lógica: {duplicidades['duplicados']}")

    risco = "Baixo"

    if not existe:
        risco = "Médio"
    if campos_faltantes or any(numericos_invalidos.values()) or any(datas_invalidas.values()):
        risco = "Alto"
    elif campos_extras or campos_vazios_criticos or duplicidades["duplicados"] > 0:
        risco = "Médio"

    pronto = risco == "Baixo" or (risco == "Médio" and linhas == 0)

    return {
        "entidade": entidade,
        "tabela": tabela,
        "arquivo": str(arquivo),
        "existe": "Sim" if existe else "Não",
        "linhas": linhas,
        "amostra_carregada": len(registros),
        "campos_esperados": len(campos_esperados),
        "campos_arquivo": len(campos_arquivo),
        "campos_faltantes": ", ".join(campos_faltantes),
        "campos_extras": ", ".join(campos_extras),
        "campos_vazios_criticos": json.dumps(campos_vazios_criticos, ensure_ascii=False),
        "numericos_invalidos": json.dumps(numericos_invalidos, ensure_ascii=False),
        "datas_invalidas": json.dumps(datas_invalidas, ensure_ascii=False),
        "duplicidades": duplicidades["duplicados"],
        "risco": risco,
        "pronto_sqlite": "Sim" if pronto else "Não",
        "diagnostico": " | ".join(problemas) if problemas else "Migração simulada sem problemas relevantes.",
    }


def simular_migracao() -> List[Dict[str, Any]]:
    contratos = carregar_contratos_repository()

    return [
        simular_tabela(entidade, contrato)
        for entidade, contrato in contratos.items()
    ]


def tipo_sql_campo(campo: str) -> str:
    campo_sql = _nome_sql(campo)

    if campo_sql in TIPOS_SUGERIDOS:
        return TIPOS_SUGERIDOS[campo_sql]

    if campo_sql.startswith("score") or campo_sql.startswith("preco") or campo_sql.startswith("valor"):
        return "REAL"

    if "data" in campo_sql or campo_sql.endswith("_em") or "prazo" in campo_sql:
        return "TEXT"

    return "TEXT"


def gerar_create_table(entidade: str, contrato: Dict[str, Any]) -> str:
    tabela = _nome_sql(contrato.get("tabela_futura", entidade))
    campos = list(contrato.get("campos", []))

    linhas = ["id INTEGER PRIMARY KEY AUTOINCREMENT"]

    for campo in campos:
        campo_sql = _nome_sql(campo)

        if campo_sql == "id":
            continue

        tipo = tipo_sql_campo(campo)
        linhas.append(f"{campo_sql} {tipo}")

    linhas.append("criado_em TEXT DEFAULT CURRENT_TIMESTAMP")
    colunas = ",\n    ".join(linhas)

    return f"CREATE TABLE IF NOT EXISTS {tabela} (\n    {colunas}\n);"


def gerar_plano_sqlite() -> str:
    contratos = carregar_contratos_repository()
    blocos = [
        "-- Valoris v3.10.0 — Plano SQL inicial simulado",
        "-- Este arquivo é uma simulação. Revise antes de executar em qualquer banco real.",
        "",
    ]

    ordem_preferencial = [
        "analises",
        "watchlist",
        "pipeline_acoes",
        "alertas",
        "decisoes",
        "eventos_repositorio",
    ]

    entidades = ordem_preferencial + [entidade for entidade in contratos if entidade not in ordem_preferencial]

    for entidade in entidades:
        if entidade in contratos:
            blocos.append(f"-- Entidade: {entidade}")
            blocos.append(gerar_create_table(entidade, contratos[entidade]))
            blocos.append("")

    return "\n".join(blocos)


def salvar_plano_sqlite() -> Path:
    CAMINHO_PLANO_SQL.write_text(gerar_plano_sqlite(), encoding="utf-8")
    return CAMINHO_PLANO_SQL


def calcular_metricas_simulador() -> Dict[str, Any]:
    simulacao = simular_migracao()

    total = len(simulacao)
    prontas = len([item for item in simulacao if item["pronto_sqlite"] == "Sim"])
    alto = len([item for item in simulacao if item["risco"] == "Alto"])
    medio = len([item for item in simulacao if item["risco"] == "Médio"])
    baixo = len([item for item in simulacao if item["risco"] == "Baixo"])
    linhas = sum(int(item["linhas"]) for item in simulacao)
    existentes = len([item for item in simulacao if item["existe"] == "Sim"])

    score = 100
    score -= alto * 22
    score -= medio * 9

    if total > 0:
        cobertura = prontas / total
        score = int(score * (0.70 + cobertura * 0.30))

    if existentes == 0:
        score = min(score, 45)

    score = max(0, min(100, score))

    if alto > 0:
        risco = "Alto"
        decisao = "Não criar banco ainda"
        proximo = "Corrigir tabelas de alto risco antes do SQLite."
    elif medio > 0:
        risco = "Médio"
        decisao = "Pode criar SQLite experimental, mas não migrar como definitivo"
        proximo = "Criar SQLite local em modo laboratório e validar contratos médios."
    elif score >= 85:
        risco = "Baixo"
        decisao = "Pronto para SQLite local"
        proximo = "Criar v3.10.1 com banco SQLite local e migração controlada."
    else:
        risco = "Médio"
        decisao = "Base quase pronta, mas precisa de mais validação"
        proximo = "Gerar plano SQL, revisar campos e registrar decisões."

    return {
        "versao": VERSAO_SIMULADOR_MIGRACAO_BANCO_VALORIS,
        "gerado_em": _agora_iso(),
        "score_migracao": score,
        "tabelas_total": total,
        "tabelas_prontas": prontas,
        "alto_risco": alto,
        "medio_risco": medio,
        "baixo_risco": baixo,
        "arquivos_existentes": existentes,
        "linhas_a_migrar": linhas,
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo,
    }


def salvar_decisao_simulador(tabela: str, risco: str, decisao: str, observacao: str = "") -> Path:
    _garantir_csv(CAMINHO_DECISOES, CAMPOS_DECISOES)

    with CAMINHO_DECISOES.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISOES)
        escritor.writerow(
            {
                "data_hora": _agora_iso(),
                "tabela": _txt(tabela),
                "risco": _txt(risco),
                "decisao": _txt(decisao),
                "observacao": _txt(observacao),
            }
        )

    return CAMINHO_DECISOES


def carregar_decisoes_simulador(max_registros: int = 300) -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_DECISOES, CAMPOS_DECISOES)

    try:
        with CAMINHO_DECISOES.open("r", newline="", encoding="utf-8") as arquivo:
            leitor = csv.DictReader(arquivo)
            return list(deque(leitor, maxlen=max_registros))
    except Exception:
        return []


def gerar_relatorio_simulador_markdown() -> str:
    metricas = calcular_metricas_simulador()
    simulacao = simular_migracao()

    linhas = "\n".join(
        [
            f"- **{item['tabela']}** ({item['entidade']}) — risco {item['risco']} — pronto SQLite: {item['pronto_sqlite']} — linhas: {item['linhas']} — {item['diagnostico']}"
            for item in simulacao
        ]
    ) or "- Nenhuma tabela simulada."

    return f"""# Simulador de Migração para Banco — Valoris

Versão: {VERSAO_SIMULADOR_MIGRACAO_BANCO_VALORIS}  
Gerado em: {_agora_iso()}

## Diagnóstico

Score de migração: {metricas['score_migracao']}/100  
Tabelas simuladas: {metricas['tabelas_total']}  
Tabelas prontas: {metricas['tabelas_prontas']}  
Alto risco: {metricas['alto_risco']}  
Médio risco: {metricas['medio_risco']}  
Linhas a migrar: {metricas['linhas_a_migrar']}  

Risco: {metricas['risco']}  
Decisão: {metricas['decisao']}  
Próximo passo: {metricas['proximo_passo']}

## Tabelas simuladas

{linhas}

## Leitura estratégica

Esta etapa evita criar um banco prematuro. O objetivo não é migrar imediatamente, mas descobrir se os dados atuais estão prontos para virar tabelas reais com segurança.
"""


def salvar_relatorio_simulador_markdown() -> Path:
    CAMINHO_RELATORIO.write_text(gerar_relatorio_simulador_markdown(), encoding="utf-8")
    return CAMINHO_RELATORIO


def gerar_manifesto_simulador() -> Dict[str, Any]:
    return {
        "produto": "Valoris",
        "versao": VERSAO_SIMULADOR_MIGRACAO_BANCO_VALORIS,
        "modulo": "simulador_migracao_banco_valoris",
        "data_hora": _agora_iso(),
        "metricas": calcular_metricas_simulador(),
        "simulacao": simular_migracao(),
        "plano_sqlite": gerar_plano_sqlite(),
        "principio": "simular antes de migrar; banco sem contrato vira bagunça persistente",
        "proxima_etapa": "sqlite_local_valoris.py",
    }


def salvar_manifesto_simulador() -> Path:
    CAMINHO_MANIFESTO.write_text(
        json.dumps(gerar_manifesto_simulador(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return CAMINHO_MANIFESTO


def renderizar_simulador_migracao_banco_valoris() -> None:
    st.subheader("Simulador de Migração para Banco")
    st.caption(
        "Valida contratos, dados, chaves, datas, numéricos e duplicidades antes de criar o SQLite local."
    )

    metricas = calcular_metricas_simulador()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Score migração", f"{metricas['score_migracao']}/100")
    col2.metric("Tabelas", metricas["tabelas_total"])
    col3.metric("Prontas", metricas["tabelas_prontas"])
    col4.metric("Alto risco", metricas["alto_risco"])
    col5.metric("Linhas", metricas["linhas_a_migrar"])

    if metricas["risco"] == "Alto":
        st.error(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    elif metricas["risco"] == "Médio":
        st.warning(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    else:
        st.success(f"{metricas['decisao']} — {metricas['proximo_passo']}")

    st.divider()

    st.markdown("### Simulação por tabela")
    simulacao = simular_migracao()
    st.dataframe(simulacao, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Plano SQL inicial")

    sql = gerar_plano_sqlite()
    st.code(sql, language="sql")

    col_sql1, col_sql2 = st.columns(2)

    if col_sql1.button("Salvar plano SQL"):
        caminho = salvar_plano_sqlite()
        st.success(f"Plano SQL salvo em {caminho}")

    st.download_button(
        "Baixar plano SQLite (.sql)",
        data=sql,
        file_name="PLANO_SQLITE_VALORIS_v3_10_0.sql",
        mime="text/sql",
    )

    st.divider()

    st.markdown("### Registrar decisão de migração")

    tabelas = [item["tabela"] for item in simulacao]
    tabela_escolhida = st.selectbox("Tabela", tabelas if tabelas else ["sem_tabela"])

    item = next((linha for linha in simulacao if linha["tabela"] == tabela_escolhida), None)

    if item:
        col1, col2 = st.columns(2)
        risco = col1.selectbox("Risco revisado", ["Baixo", "Médio", "Alto"], index=["Baixo", "Médio", "Alto"].index(item["risco"]))
        decisao = col2.selectbox(
            "Decisão",
            [
                "Pronta para SQLite",
                "Migrar apenas em laboratório",
                "Corrigir antes de migrar",
                "Ignorar por enquanto",
                "Investigar manualmente",
            ],
        )
        observacao = st.text_area("Observação", value=item["diagnostico"], height=90)

        if st.button("Salvar decisão de migração"):
            salvar_decisao_simulador(
                tabela=tabela_escolhida,
                risco=risco,
                decisao=decisao,
                observacao=observacao,
            )
            st.success("Decisão registrada.")
            st.rerun()

    decisoes = carregar_decisoes_simulador()

    if decisoes:
        st.markdown("### Decisões registradas")
        st.dataframe(decisoes, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Relatórios")

    col1, col2 = st.columns(2)

    if col1.button("Salvar relatório do simulador"):
        caminho = salvar_relatorio_simulador_markdown()
        st.success(f"Relatório salvo em {caminho}")

    if col2.button("Salvar manifesto do simulador"):
        caminho = salvar_manifesto_simulador()
        st.success(f"Manifesto salvo em {caminho}")

    st.download_button(
        "Baixar relatório do simulador (.md)",
        data=gerar_relatorio_simulador_markdown(),
        file_name="RELATORIO_SIMULADOR_MIGRACAO_BANCO_VALORIS.md",
        mime="text/markdown",
    )


def executar_autoteste_simulador_migracao_banco_valoris() -> Dict[str, Any]:
    metricas = calcular_metricas_simulador()

    return {
        "ok": True,
        "versao": VERSAO_SIMULADOR_MIGRACAO_BANCO_VALORIS,
        "metricas": {
            "score_migracao": metricas["score_migracao"],
            "tabelas_total": metricas["tabelas_total"],
            "alto_risco": metricas["alto_risco"],
        },
    }
