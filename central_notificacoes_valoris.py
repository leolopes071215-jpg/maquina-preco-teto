# central_notificacoes_valoris.py
# Valoris — Central de Notificações v3.11.7
# ------------------------------------------------------------
# Objetivo:
# - Consolidar Agenda, Alertas, Radar e Rotina em uma central única de notificações internas.
# - Mostrar o que precisa de atenção agora, o que vence em breve, o que está sem prazo e o que já foi tratado.
# - Registrar tratamento de notificações sem alterar dados operacionais principais.
# - Preparar o produto para notificações externas no futuro: calendário, e-mail, WhatsApp e automações.

from __future__ import annotations

import csv
import json
from collections import Counter, deque
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st


VERSAO_CENTRAL_NOTIFICACOES_VALORIS = "3.11.7"

CAMINHO_TRATAMENTOS = Path("tratamentos_central_notificacoes_valoris.csv")
CAMINHO_RELATORIO = Path("RELATORIO_CENTRAL_NOTIFICACOES_VALORIS.md")
CAMINHO_MANIFESTO = Path("manifesto_central_notificacoes_valoris.json")

CAMPOS_TRATAMENTOS = [
    "data_hora",
    "id_notificacao",
    "ticker",
    "empresa",
    "tipo",
    "severidade",
    "origem",
    "status_tratamento",
    "responsavel",
    "acao_tomada",
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

    formatos = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y-%m-%d %H:%M:%S",
    ]

    for formato in formatos:
        try:
            return datetime.strptime(texto, formato).date()
        except Exception:
            continue

    try:
        return datetime.fromisoformat(texto).date()
    except Exception:
        return None


def _dias_ate(valor: Any) -> Optional[int]:
    data_obj = _data(valor)

    if data_obj is None:
        return None

    return (data_obj - date.today()).days


def _garantir_csv(caminho: Path, campos: List[str]) -> None:
    if caminho.exists():
        return

    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()


def _id_notificacao(ticker: str, tipo: str, origem: str, acao: str, data_evento: str = "") -> str:
    bruto = f"{ticker}|{tipo}|{origem}|{acao}|{data_evento}"
    seguro = "".join(ch if ch.isalnum() else "_" for ch in bruto)
    return "_".join([p for p in seguro.split("_") if p])[:150] or "notificacao_sem_id"


def severidade_rank(valor: Any) -> int:
    return {
        "Crítica": 1,
        "Alta": 2,
        "Média/Alta": 3,
        "Média": 4,
        "Baixa": 5,
    }.get(_txt(valor), 9)


def carregar_agenda() -> List[Dict[str, Any]]:
    try:
        from agenda_revisoes_valoris import gerar_agenda_revisoes

        return gerar_agenda_revisoes()
    except Exception:
        return []


def carregar_alertas() -> List[Dict[str, Any]]:
    try:
        from alertas_automaticos_radar_valoris import gerar_alertas_automaticos

        return gerar_alertas_automaticos()
    except Exception:
        return []


def carregar_radar() -> List[Dict[str, Any]]:
    try:
        from radar_principal_valoris import gerar_radar_principal

        return gerar_radar_principal()
    except Exception:
        return []


def carregar_rotina() -> List[Dict[str, Any]]:
    try:
        from rotina_semanal_inteligente_valoris import gerar_rotina_semanal

        return gerar_rotina_semanal()
    except Exception:
        return []


def carregar_tratamentos(max_registros: int = 800) -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_TRATAMENTOS, CAMPOS_TRATAMENTOS)

    try:
        with CAMINHO_TRATAMENTOS.open("r", newline="", encoding="utf-8") as arquivo:
            leitor = csv.DictReader(arquivo)
            return list(deque(leitor, maxlen=max_registros))
    except Exception:
        return []


def ids_tratados() -> set[str]:
    ids = set()

    for tratamento in carregar_tratamentos():
        status = _txt(tratamento.get("status_tratamento")).lower()

        if status in {"tratado", "resolvido", "feito", "ignorado", "em acompanhamento", "adiado conscientemente"}:
            ids.add(_txt(tratamento.get("id_notificacao")))

    return ids


def classificar_notificacao(dias: Optional[int], severidade_base: str, tipo_base: str) -> Dict[str, str]:
    if dias is not None and dias < 0:
        return {
            "tipo": "Atrasado",
            "severidade": "Crítica",
        }

    if tipo_base in {"Atrasada", "Atrasado"}:
        return {
            "tipo": "Atrasado",
            "severidade": "Crítica",
        }

    if tipo_base in {"Sem prazo", "Sem data"}:
        return {
            "tipo": "Sem prazo",
            "severidade": "Alta",
        }

    if dias is None:
        return {
            "tipo": "Sem prazo",
            "severidade": "Alta",
        }

    if dias <= 7:
        return {
            "tipo": "Vence em 7 dias",
            "severidade": "Alta" if severidade_base in {"Crítica", "Alta"} else "Média/Alta",
        }

    if dias <= 15:
        return {
            "tipo": "Vence em 15 dias",
            "severidade": "Média/Alta" if severidade_base in {"Crítica", "Alta", "Média/Alta"} else "Média",
        }

    if dias <= 30:
        return {
            "tipo": "Vence em 30 dias",
            "severidade": severidade_base or "Média",
        }

    return {
        "tipo": "Monitoramento futuro",
        "severidade": "Baixa",
    }


def gerar_notificacoes() -> List[Dict[str, Any]]:
    notificacoes: List[Dict[str, Any]] = []

    for item in carregar_agenda():
        ticker = _txt(item.get("ticker")).upper()

        if not ticker:
            continue

        dias = _dias_ate(item.get("data_evento"))
        tipo_base = _txt(item.get("janela"))
        severidade_base = _txt(item.get("prioridade")) or "Média"
        classificacao = classificar_notificacao(dias, severidade_base, tipo_base)
        acao = _txt(item.get("acao"))

        notificacoes.append(
            {
                "id_notificacao": _id_notificacao(ticker, classificacao["tipo"], "Agenda Revisões", acao, _txt(item.get("data_evento"))),
                "ticker": ticker,
                "empresa": _txt(item.get("empresa")),
                "tipo": classificacao["tipo"],
                "severidade": classificacao["severidade"],
                "origem": "Agenda Revisões",
                "data_evento": _txt(item.get("data_evento")),
                "dias": "" if dias is None else dias,
                "prioridade": _txt(item.get("prioridade")),
                "acao_recomendada": acao or "Revisar item de agenda.",
                "contexto": _txt(item.get("contexto")),
            }
        )

    for item in carregar_alertas():
        ticker = _txt(item.get("ticker")).upper()

        if not ticker:
            continue

        dias = _dias_ate(item.get("prazo"))
        tipo_base = _txt(item.get("tipo_alerta"))
        severidade_base = _txt(item.get("severidade")) or "Média"
        classificacao = classificar_notificacao(dias, severidade_base, tipo_base)
        acao = _txt(item.get("acao_recomendada"))

        notificacoes.append(
            {
                "id_notificacao": _id_notificacao(ticker, classificacao["tipo"], "Alertas Radar", acao, _txt(item.get("prazo"))),
                "ticker": ticker,
                "empresa": _txt(item.get("empresa")),
                "tipo": classificacao["tipo"],
                "severidade": classificacao["severidade"],
                "origem": "Alertas Radar",
                "data_evento": _txt(item.get("prazo")),
                "dias": "" if dias is None else dias,
                "prioridade": _txt(item.get("prioridade")),
                "acao_recomendada": acao or "Tratar alerta do radar.",
                "contexto": tipo_base,
            }
        )

    for item in carregar_radar():
        ticker = _txt(item.get("ticker")).upper()

        if not ticker:
            continue

        tipo_alerta = _txt(item.get("tipo_alerta"))

        if tipo_alerta in {"Monitoramento", "Concluída/fechada"}:
            continue

        dias = _dias_ate(item.get("prazo"))
        severidade_base = _txt(item.get("criticidade")) or "Média"
        classificacao = classificar_notificacao(dias, severidade_base, tipo_alerta)
        acao = _txt(item.get("acao_recomendada_radar"))

        notificacoes.append(
            {
                "id_notificacao": _id_notificacao(ticker, classificacao["tipo"], "Radar Principal", acao, _txt(item.get("prazo"))),
                "ticker": ticker,
                "empresa": _txt(item.get("empresa")),
                "tipo": classificacao["tipo"],
                "severidade": classificacao["severidade"],
                "origem": "Radar Principal",
                "data_evento": _txt(item.get("prazo")),
                "dias": "" if dias is None else dias,
                "prioridade": _txt(item.get("prioridade")),
                "acao_recomendada": acao or "Revisar ação no Radar Principal.",
                "contexto": tipo_alerta,
            }
        )

    for item in carregar_rotina():
        ticker = _txt(item.get("ticker")).upper()

        if not ticker:
            continue

        dias = _dias_ate(item.get("prazo"))
        bloco = _txt(item.get("bloco"))
        prioridade = _txt(item.get("prioridade")) or "Média"
        classificacao = classificar_notificacao(dias, prioridade, bloco)
        acao = _txt(item.get("acao"))

        notificacoes.append(
            {
                "id_notificacao": _id_notificacao(ticker, classificacao["tipo"], "Rotina Semanal", acao, _txt(item.get("prazo"))),
                "ticker": ticker,
                "empresa": _txt(item.get("empresa")),
                "tipo": classificacao["tipo"],
                "severidade": classificacao["severidade"],
                "origem": "Rotina Semanal",
                "data_evento": _txt(item.get("prazo")),
                "dias": "" if dias is None else dias,
                "prioridade": prioridade,
                "acao_recomendada": acao or "Executar item da rotina semanal.",
                "contexto": bloco,
            }
        )

    unicas: Dict[str, Dict[str, Any]] = {}

    for item in notificacoes:
        chave = _txt(item.get("id_notificacao"))

        if not chave:
            continue

        if chave not in unicas:
            unicas[chave] = item
            continue

        if severidade_rank(item.get("severidade")) < severidade_rank(unicas[chave].get("severidade")):
            unicas[chave] = item

    lista = list(unicas.values())

    lista.sort(
        key=lambda item: (
            severidade_rank(item.get("severidade")),
            9999 if item.get("dias") in {"", None} else _int(item.get("dias"), 9999),
            item.get("ticker", ""),
            item.get("origem", ""),
        )
    )

    return lista


def salvar_tratamento_notificacao(item: Dict[str, Any], status_tratamento: str, responsavel: str, acao_tomada: str, observacao: str = "") -> Path:
    _garantir_csv(CAMINHO_TRATAMENTOS, CAMPOS_TRATAMENTOS)

    with CAMINHO_TRATAMENTOS.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_TRATAMENTOS)
        escritor.writerow(
            {
                "data_hora": _agora_iso(),
                "id_notificacao": _txt(item.get("id_notificacao")),
                "ticker": _txt(item.get("ticker")).upper(),
                "empresa": _txt(item.get("empresa")),
                "tipo": _txt(item.get("tipo")),
                "severidade": _txt(item.get("severidade")),
                "origem": _txt(item.get("origem")),
                "status_tratamento": _txt(status_tratamento),
                "responsavel": _txt(responsavel),
                "acao_tomada": _txt(acao_tomada),
                "observacao": _txt(observacao),
            }
        )

    return CAMINHO_TRATAMENTOS


def calcular_metricas_notificacoes() -> Dict[str, Any]:
    notificacoes = gerar_notificacoes()
    tratados = ids_tratados()

    pendentes = [item for item in notificacoes if item.get("id_notificacao") not in tratados]
    contador_tipo = Counter(item.get("tipo", "Sem tipo") for item in notificacoes)
    contador_severidade = Counter(item.get("severidade", "Sem severidade") for item in notificacoes)

    criticas = contador_severidade.get("Crítica", 0)
    altas = contador_severidade.get("Alta", 0)
    media_alta = contador_severidade.get("Média/Alta", 0)
    sem_prazo = contador_tipo.get("Sem prazo", 0)
    atrasadas = contador_tipo.get("Atrasado", 0)
    sete_dias = contador_tipo.get("Vence em 7 dias", 0)

    score = 65

    if notificacoes:
        score += 10

    if not pendentes and notificacoes:
        score += 15
    elif len(pendentes) <= 5:
        score += 8

    if criticas:
        score -= min(criticas * 20, 45)

    if altas:
        score -= min(altas * 10, 25)

    if sem_prazo:
        score -= min(sem_prazo * 7, 21)

    score = max(0, min(100, int(score)))

    if not notificacoes:
        risco = "Baixo"
        decisao = "Nenhuma notificação relevante no momento"
        proximo = "Manter rotina semanal e acompanhamento pelo Cockpit."
    elif atrasadas or criticas:
        risco = "Alto"
        decisao = "Existem notificações críticas ou atrasadas"
        proximo = "Resolver notificações críticas antes de abrir novas ações."
    elif altas or sem_prazo:
        risco = "Médio"
        decisao = "Existem notificações importantes que exigem organização"
        proximo = "Tratar notificações de alta severidade e itens sem prazo."
    elif pendentes:
        risco = "Baixo/Médio"
        decisao = "Central funcional com notificações pendentes leves"
        proximo = "Registrar tratamento das notificações da semana."
    else:
        risco = "Baixo"
        decisao = "Central de notificações sob controle"
        proximo = "Manter acompanhamento e preparar notificações externas no futuro."

    return {
        "versao": VERSAO_CENTRAL_NOTIFICACOES_VALORIS,
        "gerado_em": _agora_iso(),
        "score_notificacoes": score,
        "notificacoes": len(notificacoes),
        "pendentes": len(pendentes),
        "tratadas": len(notificacoes) - len(pendentes),
        "criticas": criticas,
        "altas": altas,
        "media_alta": media_alta,
        "sem_prazo": sem_prazo,
        "atrasadas": atrasadas,
        "vence_7_dias": sete_dias,
        "por_tipo": dict(contador_tipo),
        "por_severidade": dict(contador_severidade),
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo,
    }


def gerar_relatorio_notificacoes_markdown() -> str:
    metricas = calcular_metricas_notificacoes()
    notificacoes = gerar_notificacoes()

    linhas = "\n".join(
        [
            f"- **{item['severidade']} — {item['ticker']} — {item['empresa']}**: {item['tipo']} | origem {item['origem']} | ação: {item['acao_recomendada']}"
            for item in notificacoes[:60]
        ]
    ) or "- Nenhuma notificação relevante."

    return f"""# Central de Notificações — Valoris

Versão: {VERSAO_CENTRAL_NOTIFICACOES_VALORIS}  
Gerado em: {_agora_iso()}

## Diagnóstico

Score notificações: {metricas['score_notificacoes']}/100  
Notificações: {metricas['notificacoes']}  
Pendentes: {metricas['pendentes']}  
Tratadas: {metricas['tratadas']}  
Críticas: {metricas['criticas']}  
Altas: {metricas['altas']}  
Sem prazo: {metricas['sem_prazo']}  
Atrasadas: {metricas['atrasadas']}  
Vence em 7 dias: {metricas['vence_7_dias']}  

Risco: {metricas['risco']}  
Decisão: {metricas['decisao']}  
Próximo passo: {metricas['proximo_passo']}

## Notificações

{linhas}

## Estratégia

Esta versão centraliza os sinais que exigem atenção do usuário. O Valoris passa a organizar a atenção antes de enviar notificações externas, criando uma base segura para agenda, e-mail, WhatsApp e automações futuras.
"""


def salvar_relatorio_notificacoes() -> Path:
    CAMINHO_RELATORIO.write_text(gerar_relatorio_notificacoes_markdown(), encoding="utf-8")
    return CAMINHO_RELATORIO


def gerar_manifesto_notificacoes() -> Dict[str, Any]:
    return {
        "produto": "Valoris",
        "versao": VERSAO_CENTRAL_NOTIFICACOES_VALORIS,
        "modulo": "central_notificacoes_valoris",
        "data_hora": _agora_iso(),
        "metricas": calcular_metricas_notificacoes(),
        "notificacoes": gerar_notificacoes(),
        "principio": "notificação interna vem antes de notificação externa; primeiro organiza a atenção, depois automatiza",
        "proxima_etapa": "notificações externas e integração com calendário",
    }


def salvar_manifesto_notificacoes() -> Path:
    CAMINHO_MANIFESTO.write_text(
        json.dumps(gerar_manifesto_notificacoes(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return CAMINHO_MANIFESTO


def renderizar_central_notificacoes_valoris() -> None:
    st.subheader("Central de Notificações")
    st.caption("Uma fila única para atenção: vencimentos, atrasos, sem prazo, alta severidade e próximos movimentos.")

    metricas = calcular_metricas_notificacoes()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Score notificações", f"{metricas['score_notificacoes']}/100")
    col2.metric("Notificações", metricas["notificacoes"])
    col3.metric("Pendentes", metricas["pendentes"])
    col4.metric("Críticas", metricas["criticas"])
    col5.metric("Sem prazo", metricas["sem_prazo"])

    if metricas["risco"] == "Alto":
        st.error(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    elif metricas["risco"] == "Médio":
        st.warning(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    elif metricas["risco"] == "Baixo":
        st.success(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    else:
        st.info(f"{metricas['decisao']} — {metricas['proximo_passo']}")

    st.divider()

    notificacoes = gerar_notificacoes()
    tratados = ids_tratados()

    st.markdown("### Fila de notificações")

    col_f1, col_f2, col_f3 = st.columns(3)
    severidades = ["Todas"] + sorted({item.get("severidade", "") for item in notificacoes if item.get("severidade")})
    tipos = ["Todos"] + sorted({item.get("tipo", "") for item in notificacoes if item.get("tipo")})
    origens = ["Todas"] + sorted({item.get("origem", "") for item in notificacoes if item.get("origem")})
    filtro_severidade = col_f1.selectbox("Severidade", severidades)
    filtro_tipo = col_f2.selectbox("Tipo", tipos)
    filtro_origem = col_f3.selectbox("Origem", origens)

    filtro_ticker = st.text_input("Ticker", value="")

    filtradas = []

    for item in notificacoes:
        if filtro_severidade != "Todas" and item.get("severidade") != filtro_severidade:
            continue

        if filtro_tipo != "Todos" and item.get("tipo") != filtro_tipo:
            continue

        if filtro_origem != "Todas" and item.get("origem") != filtro_origem:
            continue

        if filtro_ticker.strip() and filtro_ticker.strip().upper() not in item.get("ticker", ""):
            continue

        filtradas.append(item)

    tabela = [
        {
            "tratada": "Sim" if item.get("id_notificacao") in tratados else "Não",
            "severidade": item.get("severidade"),
            "tipo": item.get("tipo"),
            "ticker": item.get("ticker"),
            "empresa": item.get("empresa"),
            "data": item.get("data_evento"),
            "dias": item.get("dias"),
            "origem": item.get("origem"),
            "ação recomendada": item.get("acao_recomendada"),
        }
        for item in filtradas
    ]

    st.dataframe(tabela, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Registrar tratamento")

    if filtradas:
        opcoes = [
            f"{item['severidade']} | {item['tipo']} | {item['ticker']} | {item['origem']}"
            for item in filtradas
        ]

        escolha = st.selectbox("Notificação", opcoes)
        item = filtradas[opcoes.index(escolha)]

        st.info(item.get("acao_recomendada"))

        col_a, col_b = st.columns(2)
        status = col_a.selectbox("Status", ["Em acompanhamento", "Tratado", "Resolvido", "Feito", "Ignorado", "Adiado conscientemente"])
        responsavel = col_b.text_input("Responsável", value="Fundador")

        acao_tomada = st.text_input("Ação tomada", value=item.get("acao_recomendada", ""))
        observacao = st.text_area(
            "Observação",
            value=f"Tratamento registrado na Central de Notificações v{VERSAO_CENTRAL_NOTIFICACOES_VALORIS}.",
            height=90,
        )

        if st.button("Salvar tratamento da notificação"):
            salvar_tratamento_notificacao(
                item,
                status_tratamento=status,
                responsavel=responsavel,
                acao_tomada=acao_tomada,
                observacao=observacao,
            )
            st.success("Tratamento da notificação registrado.")
            st.rerun()
    else:
        st.info("Nenhuma notificação encontrada com os filtros atuais.")

    tratamentos = carregar_tratamentos()

    if tratamentos:
        st.markdown("### Tratamentos registrados")
        st.dataframe(tratamentos, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Relatórios")

    col_r1, col_r2 = st.columns(2)

    if col_r1.button("Salvar relatório de notificações"):
        caminho = salvar_relatorio_notificacoes()
        st.success(f"Relatório salvo em {caminho}")

    if col_r2.button("Salvar manifesto de notificações"):
        caminho = salvar_manifesto_notificacoes()
        st.success(f"Manifesto salvo em {caminho}")

    st.download_button(
        "Baixar relatório de notificações (.md)",
        data=gerar_relatorio_notificacoes_markdown(),
        file_name="RELATORIO_CENTRAL_NOTIFICACOES_VALORIS.md",
        mime="text/markdown",
    )


def executar_autoteste_central_notificacoes_valoris() -> Dict[str, Any]:
    metricas = calcular_metricas_notificacoes()

    return {
        "ok": True,
        "versao": VERSAO_CENTRAL_NOTIFICACOES_VALORIS,
        "metricas": metricas,
    }
