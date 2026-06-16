# mapa_dados_contratos_valoris.py
# Valoris — Mapa de Dados e Contratos v3.9.8
# ------------------------------------------------------------
# Objetivo:
# - Mapear CSVs, campos, entidades e contratos de dados antes do banco.
# - Mostrar quais arquivos existem, quem lê/escreve, quantas linhas têm e quais riscos existem.
# - Preparar a transição futura para Repository, SQLite e PostgreSQL/Supabase.
# ------------------------------------------------------------

from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict, deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import streamlit as st


VERSAO_MAPA_DADOS_CONTRATOS_VALORIS = "3.9.8"

CAMINHO_RELATORIO = Path("RELATORIO_MAPA_DADOS_CONTRATOS_VALORIS.md")
CAMINHO_MANIFESTO = Path("manifesto_mapa_dados_contratos_valoris.json")
CAMINHO_DECISOES = Path("decisoes_mapa_dados_contratos_valoris.csv")

CAMPOS_DECISOES = [
    "data_hora",
    "contrato",
    "entidade",
    "risco",
    "decisao",
    "observacao",
]


CONTRATOS_DADOS: List[Dict[str, Any]] = [
    {
        "arquivo": "analises_motor_ativos_valoris.csv",
        "entidade": "analise_ativo",
        "dono": "motor_analise_ativos_valoris.py",
        "criticidade": "Alta",
        "destino_banco": "analises_ativos",
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
    {
        "arquivo": "watchlist_fundadores_valoris.csv",
        "entidade": "watchlist_item",
        "dono": "watchlist_fundadores_valoris.py",
        "criticidade": "Alta",
        "destino_banco": "watchlist",
        "descricao": "Ativos acompanhados, tese, risco, evento e revisão.",
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
    {
        "arquivo": "acoes_pipeline_decisao_valoris.csv",
        "entidade": "acao_pipeline",
        "dono": "pipeline_decisao_valoris.py",
        "criticidade": "Alta",
        "destino_banco": "pipeline_acoes",
        "descricao": "Ações operacionais do pipeline de decisão.",
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
    {
        "arquivo": "alertas_radar_revisoes_valoris.csv",
        "entidade": "alerta_tratado",
        "dono": "radar_revisoes_valoris.py",
        "criticidade": "Alta",
        "destino_banco": "alertas_revisoes",
        "descricao": "Tratamentos registrados para alertas e revisões.",
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
    {
        "arquivo": "decisoes_analise_inteligente_valoris.csv",
        "entidade": "decisao_inteligente",
        "dono": "analise_inteligente_valoris.py",
        "criticidade": "Média",
        "destino_banco": "decisoes",
        "descricao": "Decisões registradas pela central de análise inteligente.",
        "campos": [
            "data_hora",
            "ticker",
            "empresa",
            "score_inteligente",
            "classificacao",
            "acao_recomendada",
            "proximo_passo",
            "observacao",
        ],
    },
    {
        "arquivo": "decisoes_integracao_motor_watchlist_valoris.csv",
        "entidade": "decisao_integracao_watchlist",
        "dono": "integracao_motor_watchlist_valoris.py",
        "criticidade": "Média",
        "destino_banco": "decisoes",
        "descricao": "Decisões de envio ou não envio para Watchlist.",
        "campos": [
            "data_hora",
            "ticker",
            "empresa",
            "score_final",
            "decisao_motor",
            "acao_integracao",
            "status",
            "observacao",
        ],
    },
    {
        "arquivo": "decisoes_integracao_motor_relatorio_valoris.csv",
        "entidade": "decisao_integracao_relatorio",
        "dono": "integracao_motor_relatorio_valoris.py",
        "criticidade": "Média",
        "destino_banco": "decisoes",
        "descricao": "Decisões ligadas à geração de dossiês e relatórios.",
        "campos": [
            "data_hora",
            "ticker",
            "empresa",
            "score_final",
            "decisao_motor",
            "acao_relatorio",
            "status",
            "observacao",
        ],
    },
    {
        "arquivo": "decisoes_historico_analises_valoris.csv",
        "entidade": "decisao_historico",
        "dono": "historico_analises_valoris.py",
        "criticidade": "Média",
        "destino_banco": "decisoes",
        "descricao": "Decisões registradas durante revisão de histórico.",
        "campos": [
            "data_hora",
            "decisao",
            "ticker",
            "score_final",
            "observacao",
        ],
    },
]


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


def _garantir_csv(caminho: Path, campos: List[str]) -> None:
    if caminho.exists():
        return

    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()


def contar_linhas_csv(caminho: Path, limite_seguro: int = 200_000) -> int:
    if not caminho.exists():
        return 0

    total = 0

    try:
        with caminho.open("r", encoding="utf-8", errors="replace") as arquivo:
            for total, _ in enumerate(arquivo, start=1):
                if total >= limite_seguro:
                    return total

        return max(total - 1, 0)
    except Exception:
        return 0


def ler_cabecalho_csv(caminho: Path) -> List[str]:
    if not caminho.exists():
        return []

    try:
        with caminho.open("r", newline="", encoding="utf-8", errors="replace") as arquivo:
            leitor = csv.reader(arquivo)
            cabecalho = next(leitor, [])
            return [_txt(campo) for campo in cabecalho]
    except Exception:
        return []


def carregar_amostra_csv(caminho: Path, max_registros: int = 5) -> List[Dict[str, str]]:
    if not caminho.exists():
        return []

    try:
        with caminho.open("r", newline="", encoding="utf-8", errors="replace") as arquivo:
            leitor = csv.DictReader(arquivo)
            return list(deque(leitor, maxlen=max_registros))
    except Exception:
        return []


def auditar_contrato(contrato: Dict[str, Any]) -> Dict[str, Any]:
    caminho = Path(contrato["arquivo"])
    existe = caminho.exists()
    campos_esperados = contrato.get("campos", [])
    campos_arquivo = ler_cabecalho_csv(caminho)

    faltantes = [campo for campo in campos_esperados if campo not in campos_arquivo] if campos_arquivo else campos_esperados
    extras = [campo for campo in campos_arquivo if campo not in campos_esperados]

    linhas = contar_linhas_csv(caminho)
    tamanho = caminho.stat().st_size if existe else 0

    risco = "Baixo"
    problemas: List[str] = []

    if not existe:
        risco = "Médio"
        problemas.append("Arquivo ainda não existe. Pode ser normal se nenhum dado foi gerado.")
    elif faltantes:
        risco = "Alto"
        problemas.append(f"Campos esperados ausentes: {', '.join(faltantes)}")
    elif extras:
        risco = "Médio"
        problemas.append(f"Campos extras encontrados: {', '.join(extras)}")

    if tamanho > 5 * 1024 * 1024:
        risco = "Alto"
        problemas.append("Arquivo grande. Deve ser migrado ou paginado antes de uso intenso.")

    if linhas > 50_000:
        risco = "Alto"
        problemas.append("CSV com muitas linhas. Pode exigir migração rápida para banco.")

    if not problemas:
        problemas.append("Contrato consistente no estado atual.")

    return {
        "arquivo": contrato["arquivo"],
        "entidade": contrato["entidade"],
        "dono": contrato["dono"],
        "criticidade": contrato["criticidade"],
        "destino_banco": contrato["destino_banco"],
        "existe": "Sim" if existe else "Não",
        "linhas": linhas,
        "tamanho": _tamanho_formatado(tamanho),
        "campos_esperados": len(campos_esperados),
        "campos_arquivo": len(campos_arquivo),
        "campos_faltantes": ", ".join(faltantes),
        "campos_extras": ", ".join(extras),
        "risco": risco,
        "diagnostico": " | ".join(problemas),
    }


def auditar_todos_contratos() -> List[Dict[str, Any]]:
    return [auditar_contrato(contrato) for contrato in CONTRATOS_DADOS]


def descobrir_csvs_na_raiz() -> List[Dict[str, Any]]:
    conhecidos = {contrato["arquivo"] for contrato in CONTRATOS_DADOS}
    csvs: List[Dict[str, Any]] = []

    for caminho in sorted(Path(".").glob("*.csv")):
        csvs.append(
            {
                "arquivo": caminho.name,
                "mapeado": "Sim" if caminho.name in conhecidos else "Não",
                "linhas": contar_linhas_csv(caminho),
                "tamanho": _tamanho_formatado(caminho.stat().st_size),
                "campos": ", ".join(ler_cabecalho_csv(caminho)[:20]),
            }
        )

    return csvs


def buscar_referencias_csv_em_codigo(max_arquivos: int = 250) -> List[Dict[str, str]]:
    referencias: List[Dict[str, str]] = []
    padrao = re.compile(r'["\']([A-Za-z0-9_\-]+\.csv)["\']')

    arquivos = sorted(Path(".").glob("*.py"))[:max_arquivos]

    for caminho in arquivos:
        try:
            texto = caminho.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        encontrados = sorted(set(padrao.findall(texto)))

        for csv_nome in encontrados:
            referencias.append(
                {
                    "modulo": caminho.name,
                    "csv": csv_nome,
                    "mapeado": "Sim" if csv_nome in {c["arquivo"] for c in CONTRATOS_DADOS} else "Não",
                }
            )

    return referencias


def analisar_campos_padrao() -> Dict[str, Any]:
    contador = Counter()
    origem_campos = defaultdict(list)

    for contrato in CONTRATOS_DADOS:
        for campo in contrato.get("campos", []):
            contador[campo] += 1
            origem_campos[campo].append(contrato["arquivo"])

    campos_frequentes = dict(contador.most_common())

    nomes_empresa = [campo for campo in contador if campo in {"empresa", "nome_empresa"}]
    nomes_data = [campo for campo in contador if campo in {"data_hora", "data_revisao", "prazo"}]
    nomes_status = [campo for campo in contador if "status" in campo]
    nomes_observacao = [campo for campo in contador if "observ" in campo.lower()]

    recomendacoes = [
        "Padronizar empresa/nome_empresa antes do banco.",
        "Separar datas de criação, revisão e prazo em colunas claras.",
        "Padronizar status entre pipeline, watchlist e alertas.",
        "Padronizar observacao/observacoes em um único nome ou mapear aliases.",
        "Criar IDs internos para análise, watchlist, decisão, ação e alerta.",
    ]

    return {
        "campos_frequentes": campos_frequentes,
        "origem_campos": dict(origem_campos),
        "nomes_empresa": nomes_empresa,
        "nomes_data": nomes_data,
        "nomes_status": nomes_status,
        "nomes_observacao": nomes_observacao,
        "recomendacoes": recomendacoes,
    }


def sugerir_modelo_banco() -> List[Dict[str, str]]:
    return [
        {
            "tabela": "ativos",
            "descricao": "Cadastro único de tickers/empresas/setores.",
            "campos_chave": "id, ticker, empresa, setor, criado_em, atualizado_em",
            "prioridade": "Alta",
        },
        {
            "tabela": "analises_ativos",
            "descricao": "Análises calculadas pelo Motor Central.",
            "campos_chave": "id, ativo_id, preco_atual, preco_teto, scores, decisao, criado_em",
            "prioridade": "Alta",
        },
        {
            "tabela": "watchlist",
            "descricao": "Ativos acompanhados, tese, risco, evento e revisão.",
            "campos_chave": "id, ativo_id, prioridade, tese, risco, data_revisao, status",
            "prioridade": "Alta",
        },
        {
            "tabela": "pipeline_acoes",
            "descricao": "Ações operacionais por ativo.",
            "campos_chave": "id, ativo_id, etapa, prioridade, acao, responsavel, prazo, status",
            "prioridade": "Alta",
        },
        {
            "tabela": "alertas_revisoes",
            "descricao": "Alertas gerados/tratados pelo Radar.",
            "campos_chave": "id, ativo_id, tipo_alerta, prioridade, prazo, status, tratado_em",
            "prioridade": "Alta",
        },
        {
            "tabela": "decisoes",
            "descricao": "Registro unificado de decisões manuais ou automáticas.",
            "campos_chave": "id, ativo_id, origem, decisao, status, observacao, criado_em",
            "prioridade": "Média",
        },
        {
            "tabela": "relatorios",
            "descricao": "Dossiês, relatórios e manifestos gerados.",
            "campos_chave": "id, ativo_id, tipo, caminho_arquivo, conteudo, criado_em",
            "prioridade": "Média",
        },
    ]


def calcular_metricas_mapa_dados() -> Dict[str, Any]:
    auditoria = auditar_todos_contratos()
    csvs = descobrir_csvs_na_raiz()
    referencias = buscar_referencias_csv_em_codigo()

    contratos_total = len(auditoria)
    contratos_existentes = len([item for item in auditoria if item["existe"] == "Sim"])
    alto_risco = len([item for item in auditoria if item["risco"] == "Alto"])
    medio_risco = len([item for item in auditoria if item["risco"] == "Médio"])
    csvs_nao_mapeados = len([item for item in csvs if item["mapeado"] == "Não"])
    refs_nao_mapeadas = len([item for item in referencias if item["mapeado"] == "Não"])

    score_prontidao = 100
    score_prontidao -= alto_risco * 18
    score_prontidao -= medio_risco * 8
    score_prontidao -= min(csvs_nao_mapeados * 2, 18)
    score_prontidao -= min(refs_nao_mapeadas * 1, 12)

    if contratos_existentes == 0:
        score_prontidao = min(score_prontidao, 45)

    score_prontidao = max(0, min(100, int(score_prontidao)))

    if alto_risco > 0:
        risco = "Alto"
        decisao = "Ainda não migrar para banco"
        proximo = "Corrigir contratos de alto risco antes de criar SQLite/PostgreSQL."
    elif medio_risco > 0 or csvs_nao_mapeados > 10:
        risco = "Médio"
        decisao = "Pronto para desenhar repository, mas não para migração definitiva"
        proximo = "Criar camada Repository e aliases de padronização."
    elif score_prontidao >= 80:
        risco = "Baixo"
        decisao = "Pronto para camada Repository"
        proximo = "Criar repositório único com backend CSV, preparando SQLite."
    else:
        risco = "Médio"
        decisao = "Base funcional, mas precisa de saneamento"
        proximo = "Mapear CSVs restantes e padronizar campos críticos."

    return {
        "versao": VERSAO_MAPA_DADOS_CONTRATOS_VALORIS,
        "gerado_em": _agora_iso(),
        "score_prontidao_banco": score_prontidao,
        "contratos_total": contratos_total,
        "contratos_existentes": contratos_existentes,
        "alto_risco": alto_risco,
        "medio_risco": medio_risco,
        "csvs_na_raiz": len(csvs),
        "csvs_nao_mapeados": csvs_nao_mapeados,
        "referencias_csv_codigo": len(referencias),
        "referencias_nao_mapeadas": refs_nao_mapeadas,
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo,
    }


def salvar_decisao_mapa(contrato: str, entidade: str, risco: str, decisao: str, observacao: str = "") -> Path:
    _garantir_csv(CAMINHO_DECISOES, CAMPOS_DECISOES)

    with CAMINHO_DECISOES.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISOES)
        escritor.writerow(
            {
                "data_hora": _agora_iso(),
                "contrato": _txt(contrato),
                "entidade": _txt(entidade),
                "risco": _txt(risco),
                "decisao": _txt(decisao),
                "observacao": _txt(observacao),
            }
        )

    return CAMINHO_DECISOES


def carregar_decisoes_mapa(max_registros: int = 300) -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_DECISOES, CAMPOS_DECISOES)

    try:
        with CAMINHO_DECISOES.open("r", newline="", encoding="utf-8") as arquivo:
            leitor = csv.DictReader(arquivo)
            return list(deque(leitor, maxlen=max_registros))
    except Exception:
        return []


def gerar_relatorio_mapa_markdown() -> str:
    metricas = calcular_metricas_mapa_dados()
    auditoria = auditar_todos_contratos()
    modelo = sugerir_modelo_banco()
    padroes = analisar_campos_padrao()

    linhas_contratos = "\n".join(
        [
            f"- **{item['arquivo']}** → {item['destino_banco']} | entidade: {item['entidade']} | risco: {item['risco']} | linhas: {item['linhas']} | {item['diagnostico']}"
            for item in auditoria
        ]
    )

    linhas_modelo = "\n".join(
        [
            f"- **{item['tabela']}** ({item['prioridade']}): {item['descricao']} Campos: {item['campos_chave']}"
            for item in modelo
        ]
    )

    linhas_recomendacoes = "\n".join([f"- {item}" for item in padroes["recomendacoes"]])

    return f"""# Mapa de Dados e Contratos — Valoris

Versão: {VERSAO_MAPA_DADOS_CONTRATOS_VALORIS}  
Gerado em: {_agora_iso()}

## Diagnóstico

Score de prontidão para banco: {metricas['score_prontidao_banco']}/100  
Contratos mapeados: {metricas['contratos_total']}  
Contratos com arquivo existente: {metricas['contratos_existentes']}  
Contratos de alto risco: {metricas['alto_risco']}  
Contratos de médio risco: {metricas['medio_risco']}  
CSVs na raiz: {metricas['csvs_na_raiz']}  
CSVs não mapeados: {metricas['csvs_nao_mapeados']}  

Risco: {metricas['risco']}  
Decisão: {metricas['decisao']}  
Próximo passo: {metricas['proximo_passo']}

## Contratos atuais

{linhas_contratos}

## Modelo de banco sugerido

{linhas_modelo}

## Recomendações de padronização

{linhas_recomendacoes}

## Leitura estratégica

Esta versão prepara a Valoris para a migração correta. O banco não deve nascer antes dos contratos, porque banco sem contrato vira apenas CSV bagunçado em outro formato.
"""


def salvar_relatorio_mapa_markdown() -> Path:
    CAMINHO_RELATORIO.write_text(gerar_relatorio_mapa_markdown(), encoding="utf-8")
    return CAMINHO_RELATORIO


def gerar_manifesto_mapa() -> Dict[str, Any]:
    return {
        "produto": "Valoris",
        "versao": VERSAO_MAPA_DADOS_CONTRATOS_VALORIS,
        "modulo": "mapa_dados_contratos_valoris",
        "data_hora": _agora_iso(),
        "metricas": calcular_metricas_mapa_dados(),
        "contratos": CONTRATOS_DADOS,
        "modelo_banco_sugerido": sugerir_modelo_banco(),
        "principio": "antes do banco, contratos; antes da migração, padronização",
        "proximo_modulo": "repositorio_unico_valoris.py",
    }


def salvar_manifesto_mapa() -> Path:
    CAMINHO_MANIFESTO.write_text(
        json.dumps(gerar_manifesto_mapa(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return CAMINHO_MANIFESTO


def renderizar_mapa_dados_contratos_valoris() -> None:
    st.subheader("Mapa de Dados e Contratos")
    st.caption(
        "Radiografia dos CSVs, contratos, campos e riscos antes da criação da camada Repository e banco de dados."
    )

    metricas = calcular_metricas_mapa_dados()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Prontidão banco", f"{metricas['score_prontidao_banco']}/100")
    col2.metric("Contratos", metricas["contratos_total"])
    col3.metric("Alto risco", metricas["alto_risco"])
    col4.metric("CSVs raiz", metricas["csvs_na_raiz"])
    col5.metric("Não mapeados", metricas["csvs_nao_mapeados"])

    if metricas["risco"] == "Alto":
        st.error(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    elif metricas["risco"] == "Médio":
        st.warning(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    else:
        st.success(f"{metricas['decisao']} — {metricas['proximo_passo']}")

    st.divider()

    st.markdown("### Contratos principais")
    auditoria = auditar_todos_contratos()
    st.dataframe(auditoria, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### CSVs encontrados na raiz")
    csvs = descobrir_csvs_na_raiz()
    st.dataframe(csvs, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Referências a CSV no código")
    referencias = buscar_referencias_csv_em_codigo()
    st.dataframe(referencias, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Padronização de campos")
    padroes = analisar_campos_padrao()

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("#### Campos mais frequentes")
        st.json(padroes["campos_frequentes"])

    with col_b:
        st.markdown("#### Recomendações")
        for item in padroes["recomendacoes"]:
            st.write(f"- {item}")

    st.divider()

    st.markdown("### Modelo de banco sugerido")
    st.dataframe(sugerir_modelo_banco(), use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Registrar decisão de saneamento")

    opcoes = [item["arquivo"] for item in auditoria]
    contrato_escolhido = st.selectbox("Contrato", opcoes)
    contrato = next(item for item in auditoria if item["arquivo"] == contrato_escolhido)

    col1, col2 = st.columns(2)
    decisao = col1.selectbox(
        "Decisão",
        [
            "Manter contrato",
            "Padronizar campos",
            "Migrar primeiro",
            "Ignorar por enquanto",
            "Investigar manualmente",
        ],
    )
    risco = col2.selectbox("Risco revisado", ["Baixo", "Médio", "Alto"], index=["Baixo", "Médio", "Alto"].index(contrato["risco"]))

    observacao = st.text_area("Observação", value=contrato["diagnostico"], height=90)

    if st.button("Salvar decisão de saneamento"):
        salvar_decisao_mapa(
            contrato=contrato["arquivo"],
            entidade=contrato["entidade"],
            risco=risco,
            decisao=decisao,
            observacao=observacao,
        )
        st.success("Decisão registrada.")
        st.rerun()

    decisoes = carregar_decisoes_mapa()

    if decisoes:
        st.markdown("### Decisões registradas")
        st.dataframe(decisoes, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Relatórios")

    col1, col2 = st.columns(2)

    if col1.button("Salvar relatório do mapa"):
        caminho = salvar_relatorio_mapa_markdown()
        st.success(f"Relatório salvo em {caminho}")

    if col2.button("Salvar manifesto do mapa"):
        caminho = salvar_manifesto_mapa()
        st.success(f"Manifesto salvo em {caminho}")

    st.download_button(
        "Baixar relatório do mapa (.md)",
        data=gerar_relatorio_mapa_markdown(),
        file_name="RELATORIO_MAPA_DADOS_CONTRATOS_VALORIS.md",
        mime="text/markdown",
    )


def executar_autoteste_mapa_dados_contratos_valoris() -> Dict[str, Any]:
    metricas = calcular_metricas_mapa_dados()

    return {
        "ok": True,
        "versao": VERSAO_MAPA_DADOS_CONTRATOS_VALORIS,
        "metricas": {
            "score_prontidao_banco": metricas["score_prontidao_banco"],
            "contratos_total": metricas["contratos_total"],
            "alto_risco": metricas["alto_risco"],
        },
    }
