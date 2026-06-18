# higiene_operacional_valoris.py
# Valoris — Higiene Operacional v3.11.8

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict, deque
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st


VERSAO_HIGIENE_OPERACIONAL_VALORIS = "3.11.8"

CAMINHO_TRATAMENTOS = Path("tratamentos_higiene_operacional_valoris.csv")
CAMINHO_RELATORIO = Path("RELATORIO_HIGIENE_OPERACIONAL_VALORIS.md")
CAMINHO_MANIFESTO = Path("manifesto_higiene_operacional_valoris.json")

CAMPOS_TRATAMENTOS = [
    "data_hora",
    "id_problema",
    "categoria",
    "ticker",
    "empresa",
    "gravidade",
    "acao_recomendada",
    "status_tratamento",
    "responsavel",
    "observacao",
]


def _agora_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat(sep=" ")


def _txt(valor: Any) -> str:
    return "" if valor is None else str(valor).strip()


def _int(valor: Any, padrao: int = 0) -> int:
    try:
        if valor is None:
            return padrao
        if isinstance(valor, str):
            valor = valor.replace(",", ".").strip()
            if valor == "":
                return padrao
        return int(float(valor))
    except Exception:
        return padrao


def _data(valor: Any) -> Optional[date]:
    texto = _txt(valor)
    if not texto:
        return None
    for formato in ["%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d %H:%M:%S"]:
        try:
            return datetime.strptime(texto, formato).date()
        except Exception:
            pass
    try:
        return datetime.fromisoformat(texto).date()
    except Exception:
        return None


def _dias_ate(valor: Any) -> Optional[int]:
    data_obj = _data(valor)
    if data_obj is None:
        return None
    return (data_obj - date.today()).days


def _id_problema(categoria: str, ticker: str, acao: str, extra: str = "") -> str:
    bruto = f"{categoria}|{ticker}|{acao}|{extra}"
    seguro = "".join(ch if ch.isalnum() else "_" for ch in bruto)
    return "_".join([p for p in seguro.split("_") if p])[:150] or "problema_sem_id"


def _garantir_csv(caminho: Path, campos: List[str]) -> None:
    if caminho.exists():
        return
    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()


def carregar_notificacoes() -> List[Dict[str, Any]]:
    try:
        from central_notificacoes_valoris import gerar_notificacoes
        return gerar_notificacoes()
    except Exception:
        return []


def carregar_agenda() -> List[Dict[str, Any]]:
    try:
        from agenda_revisoes_valoris import gerar_agenda_revisoes
        return gerar_agenda_revisoes()
    except Exception:
        return []


def carregar_rotina() -> List[Dict[str, Any]]:
    try:
        from rotina_semanal_inteligente_valoris import gerar_rotina_semanal
        return gerar_rotina_semanal()
    except Exception:
        return []


def carregar_alertas() -> List[Dict[str, Any]]:
    try:
        from alertas_automaticos_radar_valoris import gerar_alertas_automaticos
        return gerar_alertas_automaticos()
    except Exception:
        return []


def carregar_pipeline() -> List[Dict[str, Any]]:
    try:
        from pipeline_backend_flexivel_valoris import carregar_pipeline
        return carregar_pipeline(backend="csv", max_registros=3000)
    except Exception:
        return []


def carregar_tratamentos_higiene(max_registros: int = 800) -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_TRATAMENTOS, CAMPOS_TRATAMENTOS)
    try:
        with CAMINHO_TRATAMENTOS.open("r", newline="", encoding="utf-8") as arquivo:
            return list(deque(csv.DictReader(arquivo), maxlen=max_registros))
    except Exception:
        return []


def ids_problemas_tratados() -> set[str]:
    ids = set()
    for item in carregar_tratamentos_higiene():
        status = _txt(item.get("status_tratamento")).lower()
        if status in {"tratado", "resolvido", "feito", "ignorado", "em acompanhamento", "adiado conscientemente"}:
            ids.add(_txt(item.get("id_problema")))
    return ids


def salvar_tratamento_higiene(problema: Dict[str, Any], status_tratamento: str, responsavel: str, observacao: str = "") -> Path:
    _garantir_csv(CAMINHO_TRATAMENTOS, CAMPOS_TRATAMENTOS)
    with CAMINHO_TRATAMENTOS.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_TRATAMENTOS)
        escritor.writerow({
            "data_hora": _agora_iso(),
            "id_problema": _txt(problema.get("id_problema")),
            "categoria": _txt(problema.get("categoria")),
            "ticker": _txt(problema.get("ticker")).upper(),
            "empresa": _txt(problema.get("empresa")),
            "gravidade": _txt(problema.get("gravidade")),
            "acao_recomendada": _txt(problema.get("acao_recomendada")),
            "status_tratamento": _txt(status_tratamento),
            "responsavel": _txt(responsavel),
            "observacao": _txt(observacao),
        })
    return CAMINHO_TRATAMENTOS


def _problema(categoria: str, ticker: str, empresa: str, gravidade: str, origem: str, acao: str, contexto: str = "") -> Dict[str, Any]:
    return {
        "id_problema": _id_problema(categoria, ticker, acao, contexto[:60]),
        "categoria": categoria,
        "ticker": _txt(ticker).upper(),
        "empresa": _txt(empresa) or _txt(ticker).upper(),
        "gravidade": gravidade,
        "origem": origem,
        "acao_recomendada": acao,
        "contexto": contexto,
    }


def gerar_problemas_higiene() -> List[Dict[str, Any]]:
    problemas: List[Dict[str, Any]] = []

    notificacoes = carregar_notificacoes()
    agenda = carregar_agenda()
    rotina = carregar_rotina()
    alertas = carregar_alertas()
    pipeline = carregar_pipeline()

    fontes_sem_prazo = [
        ("Notificação sem prazo", notificacoes, "data_evento", "acao_recomendada", "Central Notificações"),
        ("Agenda sem prazo", agenda, "data_evento", "acao", "Agenda Revisões"),
        ("Rotina sem prazo", rotina, "prazo", "acao", "Rotina Semanal"),
        ("Pipeline sem prazo", pipeline, "prazo", "tipo_acao", "Pipeline Principal"),
    ]

    for categoria, itens, campo_data, campo_acao, origem in fontes_sem_prazo:
        for item in itens:
            ticker = _txt(item.get("ticker")).upper()
            if not ticker:
                continue
            if _data(item.get(campo_data)) is not None:
                continue
            acao_original = _txt(item.get(campo_acao)) or "Definir próxima ação."
            problemas.append(_problema(
                categoria,
                ticker,
                _txt(item.get("empresa")) or ticker,
                "Alta",
                origem,
                f"Definir prazo para {ticker} e registrar responsável.",
                acao_original,
            ))

    grupos: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for origem, itens, campo_acao in [
        ("Central Notificações", notificacoes, "acao_recomendada"),
        ("Agenda Revisões", agenda, "acao"),
        ("Rotina Semanal", rotina, "acao"),
        ("Alertas Radar", alertas, "acao_recomendada"),
    ]:
        for item in itens:
            ticker = _txt(item.get("ticker")).upper()
            acao = _txt(item.get(campo_acao)).lower()[:80]
            if ticker and acao:
                grupos[f"{ticker}|{acao}"].append({"origem_higiene": origem, **item})

    for chave, itens in grupos.items():
        if len(itens) <= 1:
            continue
        ticker = chave.split("|", 1)[0]
        exemplo = itens[0]
        acao = _txt(exemplo.get("acao_recomendada")) or _txt(exemplo.get("acao")) or "Ação duplicada."
        origens = ", ".join(sorted({_txt(i.get("origem_higiene")) for i in itens if _txt(i.get("origem_higiene"))}))
        problemas.append(_problema(
            "Duplicidade operacional",
            ticker,
            _txt(exemplo.get("empresa")) or ticker,
            "Média",
            origens,
            f"Consolidar {len(itens)} registros semelhantes de {ticker} em uma única ação clara.",
            acao,
        ))

    for origem, itens, campo_data, campo_acao in [
        ("Agenda Revisões", agenda, "data_evento", "acao"),
        ("Pipeline Principal", pipeline, "prazo", "tipo_acao"),
        ("Alertas Radar", alertas, "prazo", "acao_recomendada"),
        ("Rotina Semanal", rotina, "prazo", "acao"),
    ]:
        for item in itens:
            ticker = _txt(item.get("ticker")).upper()
            dias = _dias_ate(item.get(campo_data))
            if not ticker or dias is None or dias >= 0:
                continue
            acao = _txt(item.get(campo_acao)) or "Ação atrasada."
            problemas.append(_problema(
                "Prazo atrasado",
                ticker,
                _txt(item.get("empresa")) or ticker,
                "Crítica",
                origem,
                f"Resolver ou reprogramar imediatamente a ação atrasada de {ticker}.",
                f"{acao} | atraso {abs(dias)} dias",
            ))

    contador_ticker = Counter(_txt(item.get("ticker")).upper() for item in notificacoes + agenda + rotina if _txt(item.get("ticker")))
    for ticker, qtd in contador_ticker.items():
        if qtd < 5:
            continue
        problemas.append(_problema(
            "Acúmulo por ativo",
            ticker,
            ticker,
            "Média/Alta",
            "Central Notificações / Agenda / Rotina",
            f"Fazer saneamento concentrado de {ticker}; há {qtd} sinais acumulados.",
            f"{qtd} registros relacionados ao mesmo ativo.",
        ))

    unicos: Dict[str, Dict[str, Any]] = {}
    for p in problemas:
        pid = _txt(p.get("id_problema"))
        if pid and pid not in unicos:
            unicos[pid] = p

    ordem_gravidade = {"Crítica": 1, "Alta": 2, "Média/Alta": 3, "Média": 4, "Baixa": 5}
    lista = list(unicos.values())
    lista.sort(key=lambda p: (ordem_gravidade.get(p.get("gravidade"), 9), p.get("ticker", ""), p.get("categoria", "")))
    return lista


def calcular_metricas_higiene_operacional() -> Dict[str, Any]:
    problemas = gerar_problemas_higiene()
    tratados = ids_problemas_tratados()
    pendentes = [p for p in problemas if p.get("id_problema") not in tratados]

    categorias = Counter(p.get("categoria", "Sem categoria") for p in problemas)
    gravidades = Counter(p.get("gravidade", "Sem gravidade") for p in problemas)

    criticos = gravidades.get("Crítica", 0)
    alta = gravidades.get("Alta", 0)
    media_alta = gravidades.get("Média/Alta", 0)
    sem_prazo = sum(qtd for categoria, qtd in categorias.items() if "sem prazo" in categoria.lower())
    duplicidades = categorias.get("Duplicidade operacional", 0)

    score = 75
    if not problemas:
        score += 15
    if pendentes:
        score -= min(len(pendentes) * 4, 28)
    if criticos:
        score -= min(criticos * 18, 40)
    if alta:
        score -= min(alta * 8, 24)
    if duplicidades:
        score -= min(duplicidades * 4, 16)
    score = max(0, min(100, int(score)))

    if not problemas:
        risco, decisao, proximo = "Baixo", "Operação limpa no momento", "Manter rotina semanal e monitorar novas notificações."
    elif criticos:
        risco, decisao, proximo = "Alto", "Há problemas críticos de higiene operacional", "Resolver prazos atrasados e consolidar pendências críticas."
    elif alta or sem_prazo:
        risco, decisao, proximo = "Médio", "Há problemas importantes de organização interna", "Definir prazos, responsáveis e consolidar duplicidades."
    elif pendentes:
        risco, decisao, proximo = "Baixo/Médio", "Higiene operacional funcional com pendências leves", "Tratar pendências antes de avançar para notificações externas."
    else:
        risco, decisao, proximo = "Baixo", "Problemas detectados já foram tratados", "Preparar próxima etapa de notificações externas."

    return {
        "versao": VERSAO_HIGIENE_OPERACIONAL_VALORIS,
        "gerado_em": _agora_iso(),
        "score_higiene": score,
        "problemas": len(problemas),
        "pendentes": len(pendentes),
        "tratados": len(problemas) - len(pendentes),
        "criticos": criticos,
        "alta": alta,
        "media_alta": media_alta,
        "sem_prazo": sem_prazo,
        "duplicidades": duplicidades,
        "por_categoria": dict(categorias),
        "por_gravidade": dict(gravidades),
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo,
    }


def gerar_relatorio_higiene_markdown() -> str:
    metricas = calcular_metricas_higiene_operacional()
    problemas = gerar_problemas_higiene()
    linhas = "\n".join([
        f"- **{p['gravidade']} — {p['categoria']} — {p['ticker']}**: {p['acao_recomendada']} Contexto: {p.get('contexto', '')}"
        for p in problemas[:80]
    ]) or "- Nenhum problema de higiene operacional detectado."

    return f"""# Higiene Operacional — Valoris

Versão: {VERSAO_HIGIENE_OPERACIONAL_VALORIS}  
Gerado em: {_agora_iso()}

## Diagnóstico

Score higiene: {metricas['score_higiene']}/100  
Problemas: {metricas['problemas']}  
Pendentes: {metricas['pendentes']}  
Tratados: {metricas['tratados']}  
Críticos: {metricas['criticos']}  
Alta gravidade: {metricas['alta']}  
Sem prazo: {metricas['sem_prazo']}  
Duplicidades: {metricas['duplicidades']}  

Risco: {metricas['risco']}  
Decisão: {metricas['decisao']}  
Próximo passo: {metricas['proximo_passo']}

## Plano de saneamento

{linhas}

## Estratégia

Antes de automatizar notificações externas, a operação precisa estar limpa. A Higiene Operacional evita que o usuário receba alertas duplicados, sem prazo ou sem ação clara.
"""


def salvar_relatorio_higiene() -> Path:
    CAMINHO_RELATORIO.write_text(gerar_relatorio_higiene_markdown(), encoding="utf-8")
    return CAMINHO_RELATORIO


def gerar_manifesto_higiene() -> Dict[str, Any]:
    return {
        "produto": "Valoris",
        "versao": VERSAO_HIGIENE_OPERACIONAL_VALORIS,
        "modulo": "higiene_operacional_valoris",
        "data_hora": _agora_iso(),
        "metricas": calcular_metricas_higiene_operacional(),
        "problemas": gerar_problemas_higiene(),
        "principio": "automação em operação suja aumenta ruído; primeiro limpa, depois escala",
        "proxima_etapa": "notificações externas com base operacional saneada",
    }


def salvar_manifesto_higiene() -> Path:
    CAMINHO_MANIFESTO.write_text(json.dumps(gerar_manifesto_higiene(), ensure_ascii=False, indent=2), encoding="utf-8")
    return CAMINHO_MANIFESTO


def renderizar_higiene_operacional_valoris() -> None:
    st.subheader("Higiene Operacional")
    st.caption("Saneamento da operação: duplicidades, itens sem prazo, atrasos e acúmulo por ativo.")

    metricas = calcular_metricas_higiene_operacional()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Score higiene", f"{metricas['score_higiene']}/100")
    col2.metric("Problemas", metricas["problemas"])
    col3.metric("Pendentes", metricas["pendentes"])
    col4.metric("Sem prazo", metricas["sem_prazo"])
    col5.metric("Duplicidades", metricas["duplicidades"])

    if metricas["risco"] == "Alto":
        st.error(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    elif metricas["risco"] == "Médio":
        st.warning(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    elif metricas["risco"] == "Baixo":
        st.success(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    else:
        st.info(f"{metricas['decisao']} — {metricas['proximo_passo']}")

    st.divider()

    problemas = gerar_problemas_higiene()
    tratados = ids_problemas_tratados()

    st.markdown("### Plano de saneamento")

    col_f1, col_f2, col_f3 = st.columns(3)
    categorias = ["Todas"] + sorted({p.get("categoria", "") for p in problemas if p.get("categoria")})
    gravidades = ["Todas"] + sorted({p.get("gravidade", "") for p in problemas if p.get("gravidade")})
    filtro_categoria = col_f1.selectbox("Categoria", categorias)
    filtro_gravidade = col_f2.selectbox("Gravidade", gravidades)
    filtro_ticker = col_f3.text_input("Ticker", value="")

    filtrados = []
    for problema in problemas:
        if filtro_categoria != "Todas" and problema.get("categoria") != filtro_categoria:
            continue
        if filtro_gravidade != "Todas" and problema.get("gravidade") != filtro_gravidade:
            continue
        if filtro_ticker.strip() and filtro_ticker.strip().upper() not in problema.get("ticker", ""):
            continue
        filtrados.append(problema)

    st.dataframe([
        {
            "tratado": "Sim" if p.get("id_problema") in tratados else "Não",
            "gravidade": p.get("gravidade"),
            "categoria": p.get("categoria"),
            "ticker": p.get("ticker"),
            "empresa": p.get("empresa"),
            "origem": p.get("origem"),
            "ação recomendada": p.get("acao_recomendada"),
            "contexto": p.get("contexto"),
        }
        for p in filtrados
    ], use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("### Registrar tratamento de higiene")

    if filtrados:
        opcoes = [f"{p['gravidade']} | {p['categoria']} | {p['ticker']} | {p['acao_recomendada'][:80]}" for p in filtrados]
        escolha = st.selectbox("Problema", opcoes)
        problema = filtrados[opcoes.index(escolha)]
        st.info(problema.get("acao_recomendada"))

        col_a, col_b = st.columns(2)
        status = col_a.selectbox("Status", ["Em acompanhamento", "Tratado", "Resolvido", "Feito", "Ignorado", "Adiado conscientemente"])
        responsavel = col_b.text_input("Responsável", value="Fundador")
        observacao = st.text_area("Observação", value=f"Tratamento registrado na Higiene Operacional v{VERSAO_HIGIENE_OPERACIONAL_VALORIS}.", height=90)

        if st.button("Salvar tratamento de higiene"):
            salvar_tratamento_higiene(problema, status_tratamento=status, responsavel=responsavel, observacao=observacao)
            st.success("Tratamento de higiene registrado.")
            st.rerun()
    else:
        st.info("Nenhum problema encontrado com os filtros atuais.")

    tratamentos = carregar_tratamentos_higiene()
    if tratamentos:
        st.markdown("### Tratamentos registrados")
        st.dataframe(tratamentos, use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("### Relatórios")
    col_r1, col_r2 = st.columns(2)
    if col_r1.button("Salvar relatório de higiene"):
        st.success(f"Relatório salvo em {salvar_relatorio_higiene()}")
    if col_r2.button("Salvar manifesto de higiene"):
        st.success(f"Manifesto salvo em {salvar_manifesto_higiene()}")

    st.download_button(
        "Baixar relatório de higiene (.md)",
        data=gerar_relatorio_higiene_markdown(),
        file_name="RELATORIO_HIGIENE_OPERACIONAL_VALORIS.md",
        mime="text/markdown",
    )


def executar_autoteste_higiene_operacional_valoris() -> Dict[str, Any]:
    return {"ok": True, "versao": VERSAO_HIGIENE_OPERACIONAL_VALORIS, "metricas": calcular_metricas_higiene_operacional()}
