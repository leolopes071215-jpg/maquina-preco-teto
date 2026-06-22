# resultados_comunicacoes_valoris.py
# Valoris — Resultados de Comunicação v3.12.4
# ------------------------------------------------------------
# Objetivo:
# - Medir o resultado do ciclo de comunicação depois do envio manual.
# - Consolidar rascunhos, aprovações, exportações, envios e auditoria.
# - Registrar retorno pós-envio: respondido, sem resposta, demanda retorno, erro de canal ou concluído.
# - Criar visão executiva por canal, ativo, severidade e responsável.
# - Não envia mensagens automaticamente.

from __future__ import annotations

import csv
import json
from collections import Counter, deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st


VERSAO_RESULTADOS_COMUNICACOES_VALORIS = "3.12.4"

CAMINHO_RASCUNHOS = Path("rascunhos_notificacoes_externas_valoris.csv")
CAMINHO_APROVACOES = Path("aprovacoes_notificacoes_externas_valoris.csv")
CAMINHO_EXPORTACOES = Path("exportacoes_notificacoes_valoris.csv")
CAMINHO_EXECUCOES = Path("execucoes_envio_manual_notificacoes_valoris.csv")
CAMINHO_REVISOES_AUDITORIA = Path("revisoes_auditoria_comunicacoes_valoris.csv")

CAMINHO_RESULTADOS = Path("resultados_comunicacoes_valoris.csv")
CAMINHO_RELATORIO = Path("RELATORIO_RESULTADOS_COMUNICACOES_VALORIS.md")
CAMINHO_MANIFESTO = Path("manifesto_resultados_comunicacoes_valoris.json")

CAMPOS_RESULTADOS = [
    "data_hora",
    "id_rascunho",
    "canal",
    "ticker",
    "empresa",
    "tipo",
    "severidade",
    "status_resultado",
    "responsavel",
    "resposta_recebida",
    "acao_pos_envio",
    "observacao",
]

CAMPOS_RASCUNHOS = [
    "data_hora",
    "canal",
    "ticker",
    "empresa",
    "tipo",
    "severidade",
    "destinatario",
    "assunto",
    "mensagem",
    "status",
    "observacao",
]

CAMPOS_APROVACOES = [
    "data_hora",
    "id_rascunho",
    "canal",
    "ticker",
    "empresa",
    "tipo",
    "severidade",
    "decisao_aprovacao",
    "responsavel",
    "motivo",
    "proxima_acao",
]

CAMPOS_EXPORTACOES = [
    "data_hora",
    "id_rascunho",
    "canal",
    "ticker",
    "empresa",
    "tipo",
    "severidade",
    "arquivo_csv",
    "arquivo_md",
    "status_exportacao",
    "responsavel",
    "observacao",
]

CAMPOS_EXECUCOES = [
    "data_hora",
    "id_rascunho",
    "canal",
    "ticker",
    "empresa",
    "tipo",
    "severidade",
    "status_envio",
    "responsavel",
    "destino_utilizado",
    "comprovante",
    "observacao",
]

CAMPOS_REVISOES_AUDITORIA = [
    "data_hora",
    "score_auditoria",
    "status_auditoria",
    "responsavel",
    "decisao",
    "observacao",
]


def _agora_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat(sep=" ")


def _txt(valor: Any) -> str:
    return "" if valor is None else str(valor).strip()


def _safe(valor: Any) -> str:
    texto = _txt(valor)
    seguro = "".join(ch if ch.isalnum() else "_" for ch in texto)
    return "_".join([p for p in seguro.split("_") if p])[:160] or "sem_id"


def _data(valor: Any) -> Optional[datetime]:
    texto = _txt(valor)

    if not texto:
        return None

    formatos = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
    ]

    for formato in formatos:
        try:
            return datetime.strptime(texto, formato)
        except Exception:
            continue

    try:
        return datetime.fromisoformat(texto)
    except Exception:
        return None


def _horas_entre(inicio: Any, fim: Any) -> Optional[float]:
    data_inicio = _data(inicio)
    data_fim = _data(fim)

    if not data_inicio or not data_fim:
        return None

    return round((data_fim - data_inicio).total_seconds() / 3600, 2)


def _garantir_csv(caminho: Path, campos: List[str]) -> None:
    if caminho.exists():
        return

    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()


def _ler_csv(caminho: Path, campos: List[str], max_registros: int = 3000) -> List[Dict[str, str]]:
    _garantir_csv(caminho, campos)

    try:
        with caminho.open("r", newline="", encoding="utf-8") as arquivo:
            leitor = csv.DictReader(arquivo)
            return list(deque(leitor, maxlen=max_registros))
    except Exception:
        return []


def _id_rascunho(item: Dict[str, Any]) -> str:
    bruto = "|".join(
        [
            _txt(item.get("data_hora")),
            _txt(item.get("canal")),
            _txt(item.get("ticker")).upper(),
            _txt(item.get("tipo")),
            _txt(item.get("assunto")),
        ]
    )
    return _safe(bruto)


def carregar_rascunhos() -> List[Dict[str, str]]:
    return _ler_csv(CAMINHO_RASCUNHOS, CAMPOS_RASCUNHOS)


def carregar_aprovacoes() -> List[Dict[str, str]]:
    return _ler_csv(CAMINHO_APROVACOES, CAMPOS_APROVACOES)


def carregar_exportacoes() -> List[Dict[str, str]]:
    return _ler_csv(CAMINHO_EXPORTACOES, CAMPOS_EXPORTACOES)


def carregar_execucoes() -> List[Dict[str, str]]:
    return _ler_csv(CAMINHO_EXECUCOES, CAMPOS_EXECUCOES)


def carregar_revisoes_auditoria() -> List[Dict[str, str]]:
    return _ler_csv(CAMINHO_REVISOES_AUDITORIA, CAMPOS_REVISOES_AUDITORIA, max_registros=1000)


def carregar_resultados() -> List[Dict[str, str]]:
    return _ler_csv(CAMINHO_RESULTADOS, CAMPOS_RESULTADOS, max_registros=2000)


def _ultima_por_id(itens: List[Dict[str, str]], campo_id: str = "id_rascunho") -> Dict[str, Dict[str, str]]:
    mapa = {}

    for item in itens:
        rid = _txt(item.get(campo_id))
        if rid:
            mapa[rid] = item

    return mapa


def _enviado(item: Dict[str, str]) -> bool:
    return "enviado manualmente" in _txt(item.get("status_envio")).lower()


def gerar_base_resultados_comunicacoes() -> List[Dict[str, Any]]:
    rascunhos = carregar_rascunhos()
    aprovacoes = carregar_aprovacoes()
    exportacoes = carregar_exportacoes()
    execucoes = carregar_execucoes()
    resultados = carregar_resultados()

    rascunho_por_id = {_id_rascunho(item): item for item in rascunhos}
    aprovacao_por_id = _ultima_por_id(aprovacoes)
    exportacao_por_id = _ultima_por_id(exportacoes)
    execucao_por_id = _ultima_por_id(execucoes)
    resultado_por_id = _ultima_por_id(resultados)

    ids = set(rascunho_por_id)
    ids.update(aprovacao_por_id)
    ids.update(exportacao_por_id)
    ids.update(execucao_por_id)
    ids.update(resultado_por_id)

    base = []

    for rid in sorted(ids):
        rascunho = rascunho_por_id.get(rid, {})
        aprovacao = aprovacao_por_id.get(rid, {})
        exportacao = exportacao_por_id.get(rid, {})
        execucao = execucao_por_id.get(rid, {})
        resultado = resultado_por_id.get(rid, {})

        canal = _txt(rascunho.get("canal")) or _txt(aprovacao.get("canal")) or _txt(exportacao.get("canal")) or _txt(execucao.get("canal")) or _txt(resultado.get("canal"))
        ticker = _txt(rascunho.get("ticker")).upper() or _txt(aprovacao.get("ticker")).upper() or _txt(exportacao.get("ticker")).upper() or _txt(execucao.get("ticker")).upper() or _txt(resultado.get("ticker")).upper()
        empresa = _txt(rascunho.get("empresa")) or _txt(aprovacao.get("empresa")) or _txt(exportacao.get("empresa")) or _txt(execucao.get("empresa")) or _txt(resultado.get("empresa"))
        tipo = _txt(rascunho.get("tipo")) or _txt(aprovacao.get("tipo")) or _txt(exportacao.get("tipo")) or _txt(execucao.get("tipo")) or _txt(resultado.get("tipo"))
        severidade = _txt(rascunho.get("severidade")) or _txt(aprovacao.get("severidade")) or _txt(exportacao.get("severidade")) or _txt(execucao.get("severidade")) or _txt(resultado.get("severidade"))

        horas_rascunho_envio = _horas_entre(rascunho.get("data_hora"), execucao.get("data_hora"))
        horas_envio_resultado = _horas_entre(execucao.get("data_hora"), resultado.get("data_hora"))

        enviado = _enviado(execucao)

        status_resultado = _txt(resultado.get("status_resultado"))
        if not status_resultado:
            if enviado:
                status_resultado = "Enviado sem resultado registrado"
            elif execucao:
                status_resultado = "Execução registrada sem envio concluído"
            elif exportacao:
                status_resultado = "Exportado sem execução"
            elif aprovacao:
                status_resultado = "Aprovado sem exportação"
            elif rascunho:
                status_resultado = "Rascunho sem aprovação"
            else:
                status_resultado = "Indefinido"

        base.append(
            {
                "id_rascunho": rid,
                "canal": canal,
                "ticker": ticker,
                "empresa": empresa,
                "tipo": tipo,
                "severidade": severidade,
                "status_resultado": status_resultado,
                "resposta_recebida": _txt(resultado.get("resposta_recebida")),
                "acao_pos_envio": _txt(resultado.get("acao_pos_envio")),
                "responsavel_resultado": _txt(resultado.get("responsavel")),
                "responsavel_envio": _txt(execucao.get("responsavel")),
                "tem_rascunho": "Sim" if rascunho else "Não",
                "tem_aprovacao": "Sim" if aprovacao else "Não",
                "tem_exportacao": "Sim" if exportacao else "Não",
                "tem_execucao": "Sim" if execucao else "Não",
                "enviado": "Sim" if enviado else "Não",
                "tem_resultado": "Sim" if resultado else "Não",
                "horas_rascunho_envio": "" if horas_rascunho_envio is None else horas_rascunho_envio,
                "horas_envio_resultado": "" if horas_envio_resultado is None else horas_envio_resultado,
                "data_rascunho": _txt(rascunho.get("data_hora")),
                "data_aprovacao": _txt(aprovacao.get("data_hora")),
                "data_exportacao": _txt(exportacao.get("data_hora")),
                "data_envio": _txt(execucao.get("data_hora")),
                "data_resultado": _txt(resultado.get("data_hora")),
            }
        )

    ordem = {
        "Enviado sem resultado registrado": 1,
        "Execução registrada sem envio concluído": 2,
        "Exportado sem execução": 3,
        "Aprovado sem exportação": 4,
        "Rascunho sem aprovação": 5,
        "Demanda retorno": 6,
        "Sem resposta": 7,
        "Respondido": 8,
        "Concluído": 9,
        "Erro de canal": 10,
        "Indefinido": 99,
    }

    base.sort(
        key=lambda item: (
            ordem.get(item.get("status_resultado"), 50),
            item.get("canal", ""),
            item.get("ticker", ""),
        )
    )

    return base


def salvar_resultado_comunicacao(item: Dict[str, Any], status_resultado: str, responsavel: str, resposta_recebida: str, acao_pos_envio: str, observacao: str = "") -> Path:
    _garantir_csv(CAMINHO_RESULTADOS, CAMPOS_RESULTADOS)

    with CAMINHO_RESULTADOS.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_RESULTADOS)
        escritor.writerow(
            {
                "data_hora": _agora_iso(),
                "id_rascunho": _txt(item.get("id_rascunho")),
                "canal": _txt(item.get("canal")),
                "ticker": _txt(item.get("ticker")).upper(),
                "empresa": _txt(item.get("empresa")),
                "tipo": _txt(item.get("tipo")),
                "severidade": _txt(item.get("severidade")),
                "status_resultado": _txt(status_resultado),
                "responsavel": _txt(responsavel),
                "resposta_recebida": _txt(resposta_recebida),
                "acao_pos_envio": _txt(acao_pos_envio),
                "observacao": _txt(observacao),
            }
        )

    return CAMINHO_RESULTADOS


def calcular_metricas_resultados_comunicacoes() -> Dict[str, Any]:
    base = gerar_base_resultados_comunicacoes()
    revisoes = carregar_revisoes_auditoria()

    total = len(base)
    enviados = len([i for i in base if i.get("enviado") == "Sim"])
    com_resultado = len([i for i in base if i.get("tem_resultado") == "Sim"])
    respondidos = len([i for i in base if i.get("status_resultado") == "Respondido"])
    concluidos = len([i for i in base if i.get("status_resultado") == "Concluído"])
    sem_resposta = len([i for i in base if i.get("status_resultado") == "Sem resposta"])
    demanda_retorno = len([i for i in base if i.get("status_resultado") == "Demanda retorno"])
    erros = len([i for i in base if i.get("status_resultado") == "Erro de canal"])
    enviados_sem_resultado = len([i for i in base if i.get("status_resultado") == "Enviado sem resultado registrado"])

    por_canal = Counter(i.get("canal", "Sem canal") or "Sem canal" for i in base)
    por_status = Counter(i.get("status_resultado", "Sem status") for i in base)
    por_ticker = Counter(i.get("ticker", "Sem ticker") or "Sem ticker" for i in base)

    taxa_resultado = 0.0
    if enviados:
        taxa_resultado = round((com_resultado / enviados) * 100, 1)

    taxa_resposta = 0.0
    if enviados:
        taxa_resposta = round((respondidos / enviados) * 100, 1)

    score = 50

    if total:
        score += 10

    if enviados:
        score += 10

    if com_resultado:
        score += 20

    if enviados_sem_resultado:
        score -= min(enviados_sem_resultado * 12, 35)

    if erros:
        score -= min(erros * 10, 25)

    if demanda_retorno:
        score += 5

    if concluidos:
        score += 10

    score = max(0, min(100, int(score)))

    if total == 0:
        risco = "Baixo"
        decisao = "Sem comunicações para medir"
        proximo = "Executar o ciclo de comunicação antes de medir resultados."
    elif enviados_sem_resultado:
        risco = "Médio"
        decisao = "Há envios manuais sem resultado registrado"
        proximo = "Registrar resposta, ausência de resposta ou próxima ação de cada envio."
    elif erros:
        risco = "Médio"
        decisao = "Há erros de canal nas comunicações"
        proximo = "Corrigir destinos e validar canal antes de novas exportações."
    elif demanda_retorno:
        risco = "Baixo/Médio"
        decisao = "Há comunicações que demandam retorno"
        proximo = "Criar próxima ação no fluxo operacional."
    elif com_resultado:
        risco = "Baixo"
        decisao = "Resultados de comunicação registrados"
        proximo = "Analisar eficácia por canal e preparar melhoria do processo."
    else:
        risco = "Baixo/Médio"
        decisao = "Comunicações existem, mas ainda sem medição completa"
        proximo = "Registrar resultados pós-envio."

    return {
        "versao": VERSAO_RESULTADOS_COMUNICACOES_VALORIS,
        "gerado_em": _agora_iso(),
        "score_resultados": score,
        "itens": total,
        "enviados": enviados,
        "com_resultado": com_resultado,
        "respondidos": respondidos,
        "concluidos": concluidos,
        "sem_resposta": sem_resposta,
        "demanda_retorno": demanda_retorno,
        "erros": erros,
        "enviados_sem_resultado": enviados_sem_resultado,
        "taxa_resultado": taxa_resultado,
        "taxa_resposta": taxa_resposta,
        "revisoes_auditoria": len(revisoes),
        "por_canal": dict(por_canal),
        "por_status": dict(por_status),
        "por_ticker": dict(por_ticker),
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo,
    }


def gerar_relatorio_resultados_markdown() -> str:
    metricas = calcular_metricas_resultados_comunicacoes()
    base = gerar_base_resultados_comunicacoes()

    linhas = "\n".join(
        [
            f"- **{item['status_resultado']} — {item['canal']} — {item['ticker']}**: enviado={item['enviado']}, resultado={item['tem_resultado']}, resposta={item['resposta_recebida'] or 'não registrada'}, ação pós-envio={item['acao_pos_envio'] or 'não definida'}"
            for item in base[:100]
        ]
    ) or "- Nenhuma comunicação medida."

    return f"""# Resultados de Comunicação — Valoris

Versão: {VERSAO_RESULTADOS_COMUNICACOES_VALORIS}  
Gerado em: {_agora_iso()}

## Diagnóstico

Score resultados: {metricas['score_resultados']}/100  
Itens: {metricas['itens']}  
Enviados: {metricas['enviados']}  
Com resultado: {metricas['com_resultado']}  
Respondidos: {metricas['respondidos']}  
Concluídos: {metricas['concluidos']}  
Sem resposta: {metricas['sem_resposta']}  
Demanda retorno: {metricas['demanda_retorno']}  
Erros de canal: {metricas['erros']}  
Enviados sem resultado: {metricas['enviados_sem_resultado']}  
Taxa de resultado: {metricas['taxa_resultado']}%  
Taxa de resposta: {metricas['taxa_resposta']}%  

Risco: {metricas['risco']}  
Decisão: {metricas['decisao']}  
Próximo passo: {metricas['proximo_passo']}

## Resultados registrados

{linhas}

## Estratégia

Esta versão transforma comunicação em aprendizado. O Valoris deixa de apenas enviar e passa a medir: o que funcionou, o que ficou sem resposta, o que exigiu retorno e o que precisa ser melhorado.
"""


def salvar_relatorio_resultados() -> Path:
    CAMINHO_RELATORIO.write_text(gerar_relatorio_resultados_markdown(), encoding="utf-8")
    return CAMINHO_RELATORIO


def gerar_manifesto_resultados() -> Dict[str, Any]:
    return {
        "produto": "Valoris",
        "versao": VERSAO_RESULTADOS_COMUNICACOES_VALORIS,
        "modulo": "resultados_comunicacoes_valoris",
        "data_hora": _agora_iso(),
        "metricas": calcular_metricas_resultados_comunicacoes(),
        "base_resultados": gerar_base_resultados_comunicacoes(),
        "principio": "comunicação sem resultado medido vira ruído; comunicação medida vira inteligência",
        "proxima_etapa": "otimização de canais e preparação de automação controlada",
    }


def salvar_manifesto_resultados() -> Path:
    CAMINHO_MANIFESTO.write_text(
        json.dumps(gerar_manifesto_resultados(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return CAMINHO_MANIFESTO


def renderizar_resultados_comunicacoes_valoris() -> None:
    st.subheader("Resultados de Comunicação")
    st.caption("Mede o pós-envio: resposta, conclusão, ausência de resposta, demanda retorno ou erro de canal.")

    metricas = calcular_metricas_resultados_comunicacoes()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Score resultados", f"{metricas['score_resultados']}/100")
    col2.metric("Enviados", metricas["enviados"])
    col3.metric("Com resultado", metricas["com_resultado"])
    col4.metric("Resposta", f"{metricas['taxa_resposta']}%")
    col5.metric("Sem resultado", metricas["enviados_sem_resultado"])

    if metricas["risco"] == "Médio":
        st.warning(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    elif metricas["risco"] == "Baixo":
        st.success(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    else:
        st.info(f"{metricas['decisao']} — {metricas['proximo_passo']}")

    st.divider()

    base = gerar_base_resultados_comunicacoes()

    st.markdown("### Base de resultados")

    col_f1, col_f2, col_f3 = st.columns(3)
    status_opcoes = ["Todos"] + sorted({item.get("status_resultado", "") for item in base if item.get("status_resultado")})
    canais = ["Todos"] + sorted({item.get("canal", "") for item in base if item.get("canal")})
    filtro_status = col_f1.selectbox("Status resultado", status_opcoes)
    filtro_canal = col_f2.selectbox("Canal", canais)
    filtro_ticker = col_f3.text_input("Ticker", value="")

    filtrados = []

    for item in base:
        if filtro_status != "Todos" and item.get("status_resultado") != filtro_status:
            continue

        if filtro_canal != "Todos" and item.get("canal") != filtro_canal:
            continue

        if filtro_ticker.strip() and filtro_ticker.strip().upper() not in item.get("ticker", ""):
            continue

        filtrados.append(item)

    st.dataframe(
        [
            {
                "status resultado": item.get("status_resultado"),
                "canal": item.get("canal"),
                "ticker": item.get("ticker"),
                "empresa": item.get("empresa"),
                "enviado": item.get("enviado"),
                "resultado": item.get("tem_resultado"),
                "resposta": item.get("resposta_recebida"),
                "ação pós-envio": item.get("acao_pos_envio"),
                "responsável": item.get("responsavel_resultado") or item.get("responsavel_envio"),
            }
            for item in filtrados
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Registrar resultado pós-envio")

    if filtrados:
        opcoes = [
            f"{item['status_resultado']} | {item['canal']} | {item['ticker']} | {item['tipo']}"
            for item in filtrados
        ]

        escolha = st.selectbox("Comunicação", opcoes)
        item = filtrados[opcoes.index(escolha)]

        col_a, col_b = st.columns(2)
        status_resultado = col_a.selectbox(
            "Status do resultado",
            ["Respondido", "Sem resposta", "Demanda retorno", "Concluído", "Erro de canal"],
        )
        responsavel = col_b.text_input("Responsável", value="Fundador")

        resposta = st.text_area("Resposta recebida", value=item.get("resposta_recebida", ""), height=90)
        acao_pos = st.text_input("Ação pós-envio", value=item.get("acao_pos_envio", ""))
        observacao = st.text_area(
            "Observação",
            value=f"Resultado registrado na v{VERSAO_RESULTADOS_COMUNICACOES_VALORIS}.",
            height=90,
        )

        if st.button("Salvar resultado de comunicação"):
            salvar_resultado_comunicacao(
                item,
                status_resultado=status_resultado,
                responsavel=responsavel,
                resposta_recebida=resposta,
                acao_pos_envio=acao_pos,
                observacao=observacao,
            )
            st.success("Resultado de comunicação registrado.")
            st.rerun()
    else:
        st.info("Nenhuma comunicação encontrada com os filtros atuais.")

    resultados = carregar_resultados()
    if resultados:
        st.markdown("### Resultados registrados")
        st.dataframe(resultados, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Relatórios")

    col_r1, col_r2 = st.columns(2)

    if col_r1.button("Salvar relatório de resultados"):
        caminho = salvar_relatorio_resultados()
        st.success(f"Relatório salvo em {caminho}")

    if col_r2.button("Salvar manifesto de resultados"):
        caminho = salvar_manifesto_resultados()
        st.success(f"Manifesto salvo em {caminho}")

    st.download_button(
        "Baixar relatório de resultados (.md)",
        data=gerar_relatorio_resultados_markdown(),
        file_name="RELATORIO_RESULTADOS_COMUNICACOES_VALORIS.md",
        mime="text/markdown",
    )


def executar_autoteste_resultados_comunicacoes_valoris() -> Dict[str, Any]:
    return {
        "ok": True,
        "versao": VERSAO_RESULTADOS_COMUNICACOES_VALORIS,
        "metricas": calcular_metricas_resultados_comunicacoes(),
    }
