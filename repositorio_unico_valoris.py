# repositorio_unico_valoris.py
# Valoris — Repository Único / Camada de Dados v3.9.9
# ------------------------------------------------------------
# Objetivo:
# - Criar uma camada única de acesso a dados antes do banco.
# - Manter backend CSV por enquanto, mas com interface preparada para SQLite/PostgreSQL.
# - Reduzir acoplamento entre páginas Streamlit e arquivos locais.
# ------------------------------------------------------------

from __future__ import annotations

import csv
import json
from collections import Counter, deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st


VERSAO_REPOSITORIO_UNICO_VALORIS = "3.9.9"
BACKEND_ATUAL = "csv"

CAMINHO_RELATORIO = Path("RELATORIO_REPOSITORIO_UNICO_VALORIS.md")
CAMINHO_MANIFESTO = Path("manifesto_repositorio_unico_valoris.json")
CAMINHO_EVENTOS_REPOSITORIO = Path("eventos_repositorio_unico_valoris.csv")
CAMINHO_DECISOES_REPOSITORIO = Path("decisoes_repositorio_unico_valoris.csv")

CAMPOS_EVENTOS_REPOSITORIO = [
    "data_hora",
    "evento",
    "entidade",
    "backend",
    "status",
    "observacao",
]

CAMPOS_DECISOES_REPOSITORIO = [
    "data_hora",
    "entidade",
    "acao",
    "status",
    "observacao",
]


CONTRATOS_REPOSITORIO: Dict[str, Dict[str, Any]] = {
    "analises": {
        "arquivo": "analises_motor_ativos_valoris.csv",
        "tabela_futura": "analises_ativos",
        "chave_logica": "ticker",
        "criticidade": "Alta",
        "descricao": "Análises salvas pelo Motor Central.",
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
    },
    "watchlist": {
        "arquivo": "watchlist_fundadores_valoris.csv",
        "tabela_futura": "watchlist",
        "chave_logica": "ticker",
        "criticidade": "Alta",
        "descricao": "Itens acompanhados na Watchlist.",
        "campos": [
            "data_hora",
            "fundador_email",
            "empresa",
            "ticker",
            "setor",
            "preco_atual",
            "preco_teto",
            "status_oportunidade",
            "prioridade",
            "tese_resumo",
            "principal_risco",
            "proximo_evento",
            "data_revisao",
            "observacoes",
        ],
    },
    "pipeline_acoes": {
        "arquivo": "acoes_pipeline_decisao_valoris.csv",
        "tabela_futura": "pipeline_acoes",
        "chave_logica": "ticker",
        "criticidade": "Alta",
        "descricao": "Ações do Pipeline de Decisão.",
        "campos": [
            "data_hora",
            "ticker",
            "empresa",
            "etapa",
            "prioridade",
            "acao",
            "responsavel",
            "prazo",
            "status",
            "observacao",
        ],
    },
    "alertas": {
        "arquivo": "alertas_radar_revisoes_valoris.csv",
        "tabela_futura": "alertas_revisoes",
        "chave_logica": "ticker",
        "criticidade": "Alta",
        "descricao": "Tratamentos de alertas do Radar.",
        "campos": [
            "data_hora",
            "ticker",
            "empresa",
            "tipo_alerta",
            "prioridade",
            "status",
            "prazo",
            "descricao",
            "acao_sugerida",
            "observacao",
        ],
    },
    "decisoes": {
        "arquivo": "decisoes_repositorio_unico_valoris.csv",
        "tabela_futura": "decisoes",
        "chave_logica": "entidade",
        "criticidade": "Média",
        "descricao": "Decisões unificadas da camada Repository.",
        "campos": CAMPOS_DECISOES_REPOSITORIO,
    },
    "eventos_repositorio": {
        "arquivo": "eventos_repositorio_unico_valoris.csv",
        "tabela_futura": "eventos_sistema",
        "chave_logica": "evento",
        "criticidade": "Média",
        "descricao": "Eventos técnicos do Repository Único.",
        "campos": CAMPOS_EVENTOS_REPOSITORIO,
    },
}


ALIASES_ENTIDADES = {
    "analise": "analises",
    "analise_ativo": "analises",
    "analises_ativos": "analises",
    "watch": "watchlist",
    "acoes": "pipeline_acoes",
    "pipeline": "pipeline_acoes",
    "alerta": "alertas",
    "alertas_revisoes": "alertas",
    "decisao": "decisoes",
    "decisoes_unificadas": "decisoes",
    "evento": "eventos_repositorio",
    "eventos": "eventos_repositorio",
}


def _agora_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat(sep=" ")


def _txt(valor: Any) -> str:
    return "" if valor is None else str(valor).strip()


def _float(valor: Any, padrao: float = 0.0) -> float:
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


def _tamanho_formatado(bytes_total: int) -> str:
    if bytes_total < 1024:
        return f"{bytes_total} B"

    kb = bytes_total / 1024

    if kb < 1024:
        return f"{kb:.1f} KB"

    mb = kb / 1024

    return f"{mb:.2f} MB"


def normalizar_entidade(entidade: str) -> str:
    chave = _txt(entidade).lower()

    if chave in CONTRATOS_REPOSITORIO:
        return chave

    return ALIASES_ENTIDADES.get(chave, chave)


def obter_contrato(entidade: str) -> Dict[str, Any]:
    entidade_normalizada = normalizar_entidade(entidade)

    if entidade_normalizada not in CONTRATOS_REPOSITORIO:
        raise ValueError(f"Entidade não mapeada no repositório: {entidade}")

    return CONTRATOS_REPOSITORIO[entidade_normalizada]


def caminho_entidade(entidade: str) -> Path:
    contrato = obter_contrato(entidade)
    return Path(contrato["arquivo"])


def campos_entidade(entidade: str) -> List[str]:
    contrato = obter_contrato(entidade)
    return list(contrato["campos"])


def garantir_arquivo_entidade(entidade: str) -> Path:
    caminho = caminho_entidade(entidade)
    campos = campos_entidade(entidade)

    if caminho.exists():
        return caminho

    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()

    return caminho


def preparar_registro(entidade: str, dados: Dict[str, Any]) -> Dict[str, Any]:
    campos = campos_entidade(entidade)
    registro = {campo: dados.get(campo, "") for campo in campos}

    if "data_hora" in campos and not _txt(registro.get("data_hora")):
        registro["data_hora"] = _agora_iso()

    for chave in ["ticker"]:
        if chave in registro:
            registro[chave] = _txt(registro[chave]).upper()

    return registro


def listar_registros(entidade: str, max_registros: int = 800) -> List[Dict[str, str]]:
    caminho = garantir_arquivo_entidade(entidade)

    try:
        with caminho.open("r", newline="", encoding="utf-8", errors="replace") as arquivo:
            leitor = csv.DictReader(arquivo)
            return list(deque(leitor, maxlen=max_registros))
    except Exception:
        return []


def salvar_registro(entidade: str, dados: Dict[str, Any]) -> Dict[str, Any]:
    caminho = garantir_arquivo_entidade(entidade)
    campos = campos_entidade(entidade)
    registro = preparar_registro(entidade, dados)

    with caminho.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writerow(registro)

    return registro


def contar_registros(entidade: str) -> int:
    caminho = garantir_arquivo_entidade(entidade)
    total = 0

    try:
        with caminho.open("r", encoding="utf-8", errors="replace") as arquivo:
            for total, _ in enumerate(arquivo, start=1):
                pass

        return max(total - 1, 0)
    except Exception:
        return 0


def salvar_evento_repositorio(evento: str, entidade: str, status: str = "ok", observacao: str = "") -> Dict[str, Any]:
    return salvar_registro(
        "eventos_repositorio",
        {
            "data_hora": _agora_iso(),
            "evento": evento,
            "entidade": entidade,
            "backend": BACKEND_ATUAL,
            "status": status,
            "observacao": observacao,
        },
    )


def salvar_decisao_repositorio(entidade: str, acao: str, status: str = "registrado", observacao: str = "") -> Dict[str, Any]:
    return salvar_registro(
        "decisoes",
        {
            "data_hora": _agora_iso(),
            "entidade": entidade,
            "acao": acao,
            "status": status,
            "observacao": observacao,
        },
    )


def listar_analises(max_registros: int = 800) -> List[Dict[str, str]]:
    return listar_registros("analises", max_registros=max_registros)


def salvar_analise(dados: Dict[str, Any]) -> Dict[str, Any]:
    return salvar_registro("analises", dados)


def listar_watchlist(max_registros: int = 800) -> List[Dict[str, str]]:
    return listar_registros("watchlist", max_registros=max_registros)


def salvar_watchlist_item(dados: Dict[str, Any]) -> Dict[str, Any]:
    return salvar_registro("watchlist", dados)


def listar_acoes_pipeline(max_registros: int = 800) -> List[Dict[str, str]]:
    return listar_registros("pipeline_acoes", max_registros=max_registros)


def salvar_acao_pipeline(dados: Dict[str, Any]) -> Dict[str, Any]:
    return salvar_registro("pipeline_acoes", dados)


def listar_alertas(max_registros: int = 800) -> List[Dict[str, str]]:
    return listar_registros("alertas", max_registros=max_registros)


def salvar_alerta(dados: Dict[str, Any]) -> Dict[str, Any]:
    return salvar_registro("alertas", dados)


def diagnosticar_entidade(entidade: str) -> Dict[str, Any]:
    entidade_normalizada = normalizar_entidade(entidade)
    contrato = obter_contrato(entidade_normalizada)
    caminho = caminho_entidade(entidade_normalizada)
    existe = caminho.exists()
    campos_esperados = campos_entidade(entidade_normalizada)

    campos_arquivo: List[str] = []

    if existe:
        try:
            with caminho.open("r", newline="", encoding="utf-8", errors="replace") as arquivo:
                leitor = csv.reader(arquivo)
                campos_arquivo = next(leitor, [])
        except Exception:
            campos_arquivo = []

    faltantes = [campo for campo in campos_esperados if campo not in campos_arquivo] if campos_arquivo else []
    extras = [campo for campo in campos_arquivo if campo not in campos_esperados] if campos_arquivo else []

    tamanho = caminho.stat().st_size if existe else 0
    linhas = contar_registros(entidade_normalizada)

    risco = "Baixo"
    diagnostico = "Contrato operacional."

    if not existe:
        risco = "Médio"
        diagnostico = "Arquivo ainda não existe; será criado pelo repositório quando necessário."
    elif faltantes:
        risco = "Alto"
        diagnostico = f"Campos faltantes: {', '.join(faltantes)}"
    elif extras:
        risco = "Médio"
        diagnostico = f"Campos extras: {', '.join(extras)}"
    elif tamanho > 5 * 1024 * 1024:
        risco = "Alto"
        diagnostico = "Arquivo CSV grande; migração para banco deve ser priorizada."

    return {
        "entidade": entidade_normalizada,
        "arquivo": contrato["arquivo"],
        "tabela_futura": contrato["tabela_futura"],
        "criticidade": contrato["criticidade"],
        "existe": "Sim" if existe else "Não",
        "linhas": linhas,
        "tamanho": _tamanho_formatado(tamanho),
        "campos": len(campos_esperados),
        "risco": risco,
        "diagnostico": diagnostico,
    }


def diagnosticar_repositorio() -> List[Dict[str, Any]]:
    return [diagnosticar_entidade(entidade) for entidade in CONTRATOS_REPOSITORIO]


def calcular_metricas_repositorio() -> Dict[str, Any]:
    diagnostico = diagnosticar_repositorio()

    total_entidades = len(diagnostico)
    existentes = len([item for item in diagnostico if item["existe"] == "Sim"])
    alto_risco = len([item for item in diagnostico if item["risco"] == "Alto"])
    medio_risco = len([item for item in diagnostico if item["risco"] == "Médio"])
    total_linhas = sum(int(item["linhas"]) for item in diagnostico)

    entidades_criticas = len(
        [
            item
            for item in diagnostico
            if item["criticidade"] == "Alta"
        ]
    )

    score_repositorio = 100
    score_repositorio -= alto_risco * 20
    score_repositorio -= medio_risco * 8

    if existentes == 0:
        score_repositorio = min(score_repositorio, 50)

    if existentes >= max(1, entidades_criticas):
        score_repositorio += 5

    score_repositorio = max(0, min(100, int(score_repositorio)))

    if alto_risco > 0:
        risco = "Alto"
        decisao = "Repository criado, mas ainda há contratos de alto risco"
        proximo = "Corrigir contratos de alto risco antes de simular migração para banco."
    elif medio_risco > 0:
        risco = "Médio"
        decisao = "Repository funcional com pontos de atenção"
        proximo = "Usar o Repository em novos módulos e preparar simulador de migração."
    elif score_repositorio >= 85:
        risco = "Baixo"
        decisao = "Repository pronto para ser usado como camada oficial"
        proximo = "Criar simulador de migração para SQLite."
    else:
        risco = "Médio"
        decisao = "Repository funcional, mas base ainda inicial"
        proximo = "Gerar mais dados reais e validar contratos."

    return {
        "versao": VERSAO_REPOSITORIO_UNICO_VALORIS,
        "backend": BACKEND_ATUAL,
        "gerado_em": _agora_iso(),
        "score_repositorio": score_repositorio,
        "entidades_total": total_entidades,
        "entidades_existentes": existentes,
        "entidades_alto_risco": alto_risco,
        "entidades_medio_risco": medio_risco,
        "linhas_totais": total_linhas,
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo,
    }


def gerar_relatorio_repositorio_markdown() -> str:
    metricas = calcular_metricas_repositorio()
    diagnostico = diagnosticar_repositorio()

    linhas = "\n".join(
        [
            f"- **{item['entidade']}** → {item['arquivo']} → {item['tabela_futura']} | risco: {item['risco']} | linhas: {item['linhas']} | {item['diagnostico']}"
            for item in diagnostico
        ]
    )

    return f"""# Repository Único — Valoris

Versão: {VERSAO_REPOSITORIO_UNICO_VALORIS}  
Backend atual: {BACKEND_ATUAL}  
Gerado em: {_agora_iso()}

## Diagnóstico

Score do Repository: {metricas['score_repositorio']}/100  
Entidades mapeadas: {metricas['entidades_total']}  
Entidades existentes: {metricas['entidades_existentes']}  
Alto risco: {metricas['entidades_alto_risco']}  
Médio risco: {metricas['entidades_medio_risco']}  
Linhas totais: {metricas['linhas_totais']}  

Risco: {metricas['risco']}  
Decisão: {metricas['decisao']}  
Próximo passo: {metricas['proximo_passo']}

## Entidades

{linhas}

## Leitura estratégica

Esta camada é o ponto de virada técnico. A partir daqui, as páginas novas devem depender do Repository, não diretamente de CSV. Depois, trocar CSV por SQLite ou PostgreSQL fica muito mais seguro.
"""


def salvar_relatorio_repositorio_markdown() -> Path:
    CAMINHO_RELATORIO.write_text(gerar_relatorio_repositorio_markdown(), encoding="utf-8")
    return CAMINHO_RELATORIO


def gerar_manifesto_repositorio() -> Dict[str, Any]:
    return {
        "produto": "Valoris",
        "versao": VERSAO_REPOSITORIO_UNICO_VALORIS,
        "modulo": "repositorio_unico_valoris",
        "backend_atual": BACKEND_ATUAL,
        "data_hora": _agora_iso(),
        "metricas": calcular_metricas_repositorio(),
        "contratos": CONTRATOS_REPOSITORIO,
        "principio": "páginas não devem depender diretamente de CSV; devem depender do repository",
        "proxima_etapa": "simulador_migracao_banco_valoris.py",
    }


def salvar_manifesto_repositorio() -> Path:
    CAMINHO_MANIFESTO.write_text(
        json.dumps(gerar_manifesto_repositorio(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return CAMINHO_MANIFESTO


def renderizar_repositorio_unico_valoris() -> None:
    st.subheader("Repository Único")
    st.caption(
        "Camada central de dados: hoje usa CSV, mas já organiza contratos para SQLite/PostgreSQL no futuro."
    )

    metricas = calcular_metricas_repositorio()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Score Repository", f"{metricas['score_repositorio']}/100")
    col2.metric("Backend", metricas["backend"])
    col3.metric("Entidades", metricas["entidades_total"])
    col4.metric("Existentes", metricas["entidades_existentes"])
    col5.metric("Linhas", metricas["linhas_totais"])

    if metricas["risco"] == "Alto":
        st.error(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    elif metricas["risco"] == "Médio":
        st.warning(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    else:
        st.success(f"{metricas['decisao']} — {metricas['proximo_passo']}")

    st.divider()

    st.markdown("### Contratos do Repository")
    diagnostico = diagnosticar_repositorio()
    st.dataframe(diagnostico, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Navegar dados por entidade")

    entidades = sorted(CONTRATOS_REPOSITORIO.keys())
    entidade = st.selectbox("Entidade", entidades)
    limite = st.slider("Registros para carregar", 10, 1000, 100)

    registros = listar_registros(entidade, max_registros=limite)
    st.caption(f"Arquivo: {caminho_entidade(entidade)} | Registros carregados: {len(registros)}")
    st.dataframe(registros, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Teste controlado do Repository")

    col_a, col_b = st.columns(2)

    if col_a.button("Registrar evento técnico"):
        salvar_evento_repositorio(
            evento="teste_repository_streamlit",
            entidade=entidade,
            status="ok",
            observacao=f"Teste controlado executado pela interface na entidade {entidade}.",
        )
        st.success("Evento técnico registrado via Repository.")
        st.rerun()

    if col_b.button("Registrar decisão de camada de dados"):
        salvar_decisao_repositorio(
            entidade=entidade,
            acao="validar_contrato_repository",
            status="registrado",
            observacao=f"Contrato {entidade} revisado no Repository Único.",
        )
        st.success("Decisão registrada via Repository.")
        st.rerun()

    st.divider()

    st.markdown("### API interna disponível")
    st.code(
        """
from repositorio_unico_valoris import (
    listar_analises,
    salvar_analise,
    listar_watchlist,
    salvar_watchlist_item,
    listar_acoes_pipeline,
    salvar_acao_pipeline,
    listar_alertas,
    salvar_alerta,
    listar_registros,
    salvar_registro,
)
""".strip(),
        language="python",
    )

    st.divider()

    st.markdown("### Relatórios")

    col1, col2 = st.columns(2)

    if col1.button("Salvar relatório do Repository"):
        caminho = salvar_relatorio_repositorio_markdown()
        st.success(f"Relatório salvo em {caminho}")

    if col2.button("Salvar manifesto do Repository"):
        caminho = salvar_manifesto_repositorio()
        st.success(f"Manifesto salvo em {caminho}")

    st.download_button(
        "Baixar relatório do Repository (.md)",
        data=gerar_relatorio_repositorio_markdown(),
        file_name="RELATORIO_REPOSITORIO_UNICO_VALORIS.md",
        mime="text/markdown",
    )


def executar_autoteste_repositorio_unico_valoris() -> Dict[str, Any]:
    metricas = calcular_metricas_repositorio()

    return {
        "ok": True,
        "versao": VERSAO_REPOSITORIO_UNICO_VALORIS,
        "backend": BACKEND_ATUAL,
        "metricas": {
            "score_repositorio": metricas["score_repositorio"],
            "entidades_total": metricas["entidades_total"],
            "entidades_alto_risco": metricas["entidades_alto_risco"],
        },
    }
