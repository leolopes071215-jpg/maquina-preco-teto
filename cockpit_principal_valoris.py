# cockpit_principal_valoris.py
# Valoris — Cockpit Principal v3.11.2
# ------------------------------------------------------------
# Objetivo:
# - Criar a primeira tela inicial executiva do Valoris.
# - Consolidar saúde do produto, histórico, análise, pipeline, radar e banco.
# - Mostrar uma visão única de decisão: o que está funcionando, o que exige atenção e qual é o próximo movimento.
# - Não substitui páginas antigas; apenas organiza a experiência premium em um cockpit principal.

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import streamlit as st


VERSAO_COCKPIT_PRINCIPAL_VALORIS = "3.11.2"

CAMINHO_RELATORIO = Path("RELATORIO_COCKPIT_PRINCIPAL_VALORIS.md")
CAMINHO_MANIFESTO = Path("manifesto_cockpit_principal_valoris.json")


def _agora_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat(sep=" ")


def _txt(valor: Any) -> str:
    return "" if valor is None else str(valor).strip()


def _int(valor: Any, padrao: int = 0) -> int:
    try:
        if valor is None:
            return padrao

        if isinstance(valor, str):
            valor = valor.replace("%", "").replace(",", ".").strip()

            if valor == "":
                return padrao

        return int(float(valor))
    except Exception:
        return padrao


def _extrair_score(metricas: Dict[str, Any]) -> int:
    chaves = [
        "score_promocao",
        "score_acompanhamento",
        "score_experiencia",
        "score_controle",
        "score_migracao_paginas",
        "score_health",
        "score_healthcheck",
        "score_geral",
        "score",
    ]

    for chave in chaves:
        if chave in metricas:
            return _int(metricas.get(chave), 0)

    return 0


def _extrair_decisao(metricas: Dict[str, Any]) -> str:
    return _txt(metricas.get("decisao")) or _txt(metricas.get("status")) or "Sem decisão informada."


def _extrair_proximo(metricas: Dict[str, Any]) -> str:
    return _txt(metricas.get("proximo_passo")) or _txt(metricas.get("proximo")) or "Sem próximo passo informado."


def _executar_bloco(nome: str, funcao: Callable[[], Dict[str, Any]], peso: int = 1) -> Dict[str, Any]:
    try:
        metricas = funcao()

        if not isinstance(metricas, dict):
            metricas = {"valor": metricas}

        score = _extrair_score(metricas)
        decisao = _extrair_decisao(metricas)
        proximo = _extrair_proximo(metricas)

        if score >= 85:
            status = "Saudável"
            criticidade = "Baixa"
        elif score >= 65:
            status = "Funcional"
            criticidade = "Média"
        elif score >= 45:
            status = "Atenção"
            criticidade = "Média/Alta"
        else:
            status = "Crítico"
            criticidade = "Alta"

        return {
            "nome": nome,
            "ok": True,
            "score": score,
            "status": status,
            "criticidade": criticidade,
            "decisao": decisao,
            "proximo_passo": proximo,
            "peso": peso,
            "metricas": metricas,
            "erro": "",
        }
    except Exception as erro:
        return {
            "nome": nome,
            "ok": False,
            "score": 0,
            "status": "Indisponível",
            "criticidade": "Alta",
            "decisao": "Módulo indisponível ou com erro.",
            "proximo_passo": f"Revisar módulo: {erro}",
            "peso": peso,
            "metricas": {},
            "erro": str(erro),
        }


def _metricas_historico() -> Dict[str, Any]:
    from historico_principal_valoris import calcular_score_promocao_historico

    return calcular_score_promocao_historico()


def _metricas_analise() -> Dict[str, Any]:
    from analise_principal_valoris import calcular_score_promocao_analise

    return calcular_score_promocao_analise()


def _metricas_pipeline() -> Dict[str, Any]:
    from pipeline_principal_valoris import calcular_score_promocao_pipeline

    return calcular_score_promocao_pipeline()


def _metricas_radar() -> Dict[str, Any]:
    from radar_principal_valoris import calcular_metricas_radar_principal

    return calcular_metricas_radar_principal()


def _metricas_healthcheck() -> Dict[str, Any]:
    try:
        from healthcheck_banco_repository_valoris import calcular_metricas_healthcheck

        return calcular_metricas_healthcheck()
    except Exception:
        from healthcheck_banco_repository_valoris import calcular_metricas_healthcheck_banco_repository

        return calcular_metricas_healthcheck_banco_repository()


def _metricas_repository_backend() -> Dict[str, Any]:
    from repository_backend_sqlite_valoris import comparar_csv_sqlite, obter_backend_padrao

    comparacao = comparar_csv_sqlite()
    divergentes = [
        item for item in comparacao
        if _txt(item.get("status")).lower() not in {"alinhado", "ok", "sem dados"}
    ]

    score = 85 if not divergentes else 65

    return {
        "score": score,
        "backend_padrao": obter_backend_padrao(),
        "entidades": len(comparacao),
        "divergentes": len(divergentes),
        "decisao": "Repository Backend funcional e comparável." if not divergentes else "Repository Backend tem divergências para revisar.",
        "proximo_passo": "Manter CSV como padrão seguro e SQLite como laboratório." if not divergentes else "Revisar entidades divergentes antes de promover SQLite.",
        "comparacao": comparacao,
    }


def obter_blocos_cockpit() -> List[Dict[str, Any]]:
    return [
        _executar_bloco("Histórico Principal", _metricas_historico, peso=2),
        _executar_bloco("Análise Principal", _metricas_analise, peso=3),
        _executar_bloco("Pipeline Principal", _metricas_pipeline, peso=3),
        _executar_bloco("Radar Principal", _metricas_radar, peso=3),
        _executar_bloco("Health Check Banco/Repository", _metricas_healthcheck, peso=2),
        _executar_bloco("Repository Backend", _metricas_repository_backend, peso=2),
    ]


def calcular_metricas_cockpit_principal() -> Dict[str, Any]:
    blocos = obter_blocos_cockpit()

    pesos_total = sum(int(bloco.get("peso", 1)) for bloco in blocos) or 1
    score_ponderado = sum(
        int(bloco.get("score", 0)) * int(bloco.get("peso", 1))
        for bloco in blocos
    ) / pesos_total

    score = int(round(score_ponderado))

    saudaveis = len([b for b in blocos if b["status"] == "Saudável"])
    funcionais = len([b for b in blocos if b["status"] == "Funcional"])
    atencao = len([b for b in blocos if b["status"] == "Atenção"])
    criticos = len([b for b in blocos if b["status"] in {"Crítico", "Indisponível"}])
    indisponiveis = len([b for b in blocos if not b.get("ok")])

    if criticos > 0:
        status = "Atenção Crítica"
        decisao = "Há módulos críticos ou indisponíveis no cockpit"
        proximo = "Corrigir módulos críticos antes de promover novas funcionalidades."
    elif atencao > 0:
        status = "Atenção"
        decisao = "Cockpit funcional, mas há blocos que exigem acompanhamento"
        proximo = "Priorizar blocos em atenção antes de expandir o produto."
    elif score >= 85:
        status = "Pronto"
        decisao = "Cockpit pronto para ser a tela inicial executiva do Valoris"
        proximo = "Usar como página principal e evoluir alertas automáticos."
    else:
        status = "Funcional"
        decisao = "Cockpit funcional, ainda em fase de maturação operacional"
        proximo = "Alimentar mais dados reais e acompanhar ciclos de uso."

    return {
        "versao": VERSAO_COCKPIT_PRINCIPAL_VALORIS,
        "gerado_em": _agora_iso(),
        "score_cockpit": score,
        "status": status,
        "saudaveis": saudaveis,
        "funcionais": funcionais,
        "atencao": atencao,
        "criticos": criticos,
        "indisponiveis": indisponiveis,
        "modulos": len(blocos),
        "decisao": decisao,
        "proximo_passo": proximo,
        "blocos": blocos,
    }


def gerar_plano_proximo_movimento(blocos: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    blocos = blocos or obter_blocos_cockpit()

    ordem_criticidade = {
        "Alta": 1,
        "Média/Alta": 2,
        "Média": 3,
        "Baixa": 4,
    }

    plano = []

    for bloco in blocos:
        acao = bloco.get("proximo_passo", "")

        if bloco["status"] in {"Crítico", "Indisponível"}:
            prioridade = "Alta"
        elif bloco["status"] == "Atenção":
            prioridade = "Alta"
        elif bloco["status"] == "Funcional":
            prioridade = "Média"
        else:
            prioridade = "Baixa"

        plano.append(
            {
                "módulo": bloco["nome"],
                "score": bloco["score"],
                "status": bloco["status"],
                "criticidade": bloco["criticidade"],
                "prioridade": prioridade,
                "próximo movimento": acao,
            }
        )

    plano.sort(
        key=lambda item: (
            ordem_criticidade.get(item["criticidade"], 9),
            -int(item["score"]),
            item["módulo"],
        )
    )

    return plano


def gerar_relatorio_cockpit_principal_markdown() -> str:
    metricas = calcular_metricas_cockpit_principal()
    blocos = metricas["blocos"]
    plano = gerar_plano_proximo_movimento(blocos)

    linhas_blocos = "\n".join(
        [
            f"- **{bloco['nome']}**: score {bloco['score']}/100 | {bloco['status']} | decisão: {bloco['decisao']} | próximo: {bloco['proximo_passo']}"
            for bloco in blocos
        ]
    )

    linhas_plano = "\n".join(
        [
            f"- **{item['prioridade']} — {item['módulo']}**: {item['próximo movimento']}"
            for item in plano
        ]
    )

    return f"""# Cockpit Principal — Valoris

Versão: {VERSAO_COCKPIT_PRINCIPAL_VALORIS}  
Gerado em: {_agora_iso()}

## Diagnóstico Executivo

Score Cockpit: {metricas['score_cockpit']}/100  
Status: {metricas['status']}  
Módulos: {metricas['modulos']}  
Saudáveis: {metricas['saudaveis']}  
Funcionais: {metricas['funcionais']}  
Atenção: {metricas['atencao']}  
Críticos: {metricas['criticos']}  
Indisponíveis: {metricas['indisponiveis']}  

Decisão: {metricas['decisao']}  
Próximo passo: {metricas['proximo_passo']}

## Blocos do Cockpit

{linhas_blocos}

## Plano de Próximo Movimento

{linhas_plano}

## Estratégia

O Cockpit Principal transforma o Valoris em uma experiência executiva. Em vez de o usuário procurar informação em várias páginas, ele passa a enxergar saúde do sistema, decisões, ações, riscos e próximos passos em uma única tela.
"""


def salvar_relatorio_cockpit_principal() -> Path:
    CAMINHO_RELATORIO.write_text(gerar_relatorio_cockpit_principal_markdown(), encoding="utf-8")
    return CAMINHO_RELATORIO


def gerar_manifesto_cockpit_principal() -> Dict[str, Any]:
    metricas = calcular_metricas_cockpit_principal()

    return {
        "produto": "Valoris",
        "versao": VERSAO_COCKPIT_PRINCIPAL_VALORIS,
        "modulo": "cockpit_principal_valoris",
        "data_hora": _agora_iso(),
        "metricas": metricas,
        "plano_proximo_movimento": gerar_plano_proximo_movimento(metricas["blocos"]),
        "principio": "produto premium precisa começar por clareza executiva e terminar em próxima ação",
        "proxima_etapa": "promover Cockpit Principal como página inicial e criar alertas automáticos",
    }


def salvar_manifesto_cockpit_principal() -> Path:
    CAMINHO_MANIFESTO.write_text(
        json.dumps(gerar_manifesto_cockpit_principal(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return CAMINHO_MANIFESTO


def renderizar_cockpit_principal_valoris() -> None:
    st.subheader("Cockpit Principal")
    st.caption(
        "Tela inicial executiva: saúde do produto, histórico, análise, pipeline, radar, banco e próximos movimentos."
    )

    metricas = calcular_metricas_cockpit_principal()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Score Cockpit", f"{metricas['score_cockpit']}/100")
    col2.metric("Status", metricas["status"])
    col3.metric("Saudáveis", metricas["saudaveis"])
    col4.metric("Atenção", metricas["atencao"])
    col5.metric("Críticos", metricas["criticos"])

    if metricas["status"] == "Pronto":
        st.success(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    elif metricas["status"] in {"Atenção", "Funcional"}:
        st.info(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    else:
        st.error(f"{metricas['decisao']} — {metricas['proximo_passo']}")

    st.divider()

    st.markdown("### Blocos executivos")

    tabela_blocos = [
        {
            "módulo": bloco["nome"],
            "score": bloco["score"],
            "status": bloco["status"],
            "criticidade": bloco["criticidade"],
            "decisão": bloco["decisao"],
            "próximo passo": bloco["proximo_passo"],
        }
        for bloco in metricas["blocos"]
    ]

    st.dataframe(tabela_blocos, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Próximo movimento recomendado")

    plano = gerar_plano_proximo_movimento(metricas["blocos"])
    st.dataframe(plano, use_container_width=True, hide_index=True)

    st.divider()

    with st.expander("Manifesto estratégico do Cockpit", expanded=False):
        st.markdown(
            """
            **O Cockpit Principal é a tela de comando do Valoris.**

            A experiência ideal do cliente não deve começar procurando páginas. Ela deve começar com clareza:

            - O sistema está saudável?
            - O que foi analisado?
            - Qual ativo exige decisão?
            - Que ação está aberta?
            - Existe prazo, atraso ou risco?
            - Qual é o próximo movimento?

            Essa página consolida a experiência premium e prepara o produto para alertas automáticos, notificações e futura conta de usuário.
            """
        )

    st.divider()

    st.markdown("### Relatórios")

    col_a, col_b = st.columns(2)

    if col_a.button("Salvar relatório do Cockpit"):
        caminho = salvar_relatorio_cockpit_principal()
        st.success(f"Relatório salvo em {caminho}")

    if col_b.button("Salvar manifesto do Cockpit"):
        caminho = salvar_manifesto_cockpit_principal()
        st.success(f"Manifesto salvo em {caminho}")

    st.download_button(
        "Baixar relatório do Cockpit (.md)",
        data=gerar_relatorio_cockpit_principal_markdown(),
        file_name="RELATORIO_COCKPIT_PRINCIPAL_VALORIS.md",
        mime="text/markdown",
    )


def executar_autoteste_cockpit_principal_valoris() -> Dict[str, Any]:
    metricas = calcular_metricas_cockpit_principal()

    return {
        "ok": True,
        "versao": VERSAO_COCKPIT_PRINCIPAL_VALORIS,
        "metricas": {
            "score_cockpit": metricas["score_cockpit"],
            "status": metricas["status"],
            "modulos": metricas["modulos"],
            "criticos": metricas["criticos"],
        },
    }
