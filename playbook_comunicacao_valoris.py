# playbook_comunicacao_valoris.py
# Valoris — Playbook de Comunicação v3.12.6
# ------------------------------------------------------------
# Objetivo:
# - Transformar a Otimização de Canais em padrões práticos de comunicação.
# - Criar recomendações por canal: WhatsApp, E-mail, Calendário e Resumo Executivo.
# - Gerar templates seguros para uso manual.
# - Registrar padrões aprovados antes de qualquer automação externa real.
# - Não envia mensagens automaticamente.

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict, deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st


VERSAO_PLAYBOOK_COMUNICACAO_VALORIS = "3.12.6"

CAMINHO_RESULTADOS = Path("resultados_comunicacoes_valoris.csv")
CAMINHO_PLANO_CANAIS = Path("plano_otimizacao_canais_valoris.csv")
CAMINHO_PLAYBOOK = Path("playbook_comunicacao_valoris.csv")
CAMINHO_RELATORIO = Path("RELATORIO_PLAYBOOK_COMUNICACAO_VALORIS.md")
CAMINHO_MANIFESTO = Path("manifesto_playbook_comunicacao_valoris.json")

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

CAMPOS_PLANO_CANAIS = [
    "data_hora",
    "canal",
    "score_canal",
    "diagnostico",
    "acao_otimizacao",
    "prioridade",
    "responsavel",
    "status_plano",
    "observacao",
]

CAMPOS_PLAYBOOK = [
    "data_hora",
    "canal",
    "tipo_comunicacao",
    "prioridade",
    "template",
    "quando_usar",
    "quando_evitar",
    "responsavel",
    "status_playbook",
    "observacao",
]


def _agora_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat(sep=" ")


def _txt(valor: Any) -> str:
    return "" if valor is None else str(valor).strip()


def _pct(parte: int, total: int) -> float:
    if not total:
        return 0.0
    return round((parte / total) * 100, 1)


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


def carregar_resultados() -> List[Dict[str, str]]:
    return _ler_csv(CAMINHO_RESULTADOS, CAMPOS_RESULTADOS)


def carregar_planos_canais() -> List[Dict[str, str]]:
    return _ler_csv(CAMINHO_PLANO_CANAIS, CAMPOS_PLANO_CANAIS)


def carregar_playbook() -> List[Dict[str, str]]:
    return _ler_csv(CAMINHO_PLAYBOOK, CAMPOS_PLAYBOOK, max_registros=1200)


def carregar_ranking_canais() -> List[Dict[str, Any]]:
    try:
        from otimizacao_canais_valoris import gerar_ranking_canais
        return gerar_ranking_canais()
    except Exception:
        return []


def carregar_metricas_otimizacao() -> Dict[str, Any]:
    try:
        from otimizacao_canais_valoris import calcular_metricas_otimizacao_canais
        return calcular_metricas_otimizacao_canais()
    except Exception:
        return {}


def template_padrao_por_canal(canal: str, tipo: str = "Acompanhamento") -> Dict[str, str]:
    canal = _txt(canal) or "Resumo Executivo"
    tipo = _txt(tipo) or "Acompanhamento"

    if canal == "WhatsApp":
        template = (
            "Olá. Passando para registrar um ponto do Valoris:\n\n"
            "Ativo: {ticker} — {empresa}\n"
            "Tipo: {tipo}\n"
            "Prioridade: {severidade}\n"
            "Ação recomendada: {acao}\n\n"
            "Pode me confirmar se seguimos com essa direção?"
        )
        quando_usar = "Quando a comunicação precisa ser curta, direta e com pedido claro de confirmação."
        quando_evitar = "Evitar para análises longas, decisões complexas ou mensagens que exijam histórico detalhado."
    elif canal == "E-mail":
        template = (
            "Assunto: [Valoris] {ticker} — {tipo}\n\n"
            "Olá,\n\n"
            "Segue ponto identificado pelo Valoris.\n\n"
            "Ativo: {ticker} — {empresa}\n"
            "Severidade: {severidade}\n"
            "Tipo: {tipo}\n\n"
            "Contexto:\n{contexto}\n\n"
            "Ação recomendada:\n{acao}\n\n"
            "Próximo passo sugerido:\n{proximo_passo}\n\n"
            "Fico à disposição."
        )
        quando_usar = "Quando a comunicação exige contexto, registro formal e maior organização."
        quando_evitar = "Evitar quando a decisão precisa de resposta muito rápida."
    elif canal == "Calendário":
        template = (
            "Título: Revisão Valoris — {ticker} — {tipo}\n\n"
            "Descrição:\n"
            "Ativo: {ticker} — {empresa}\n"
            "Severidade: {severidade}\n"
            "Ação recomendada: {acao}\n\n"
            "Checklist da reunião:\n"
            "1. Conferir contexto.\n"
            "2. Decidir próxima ação.\n"
            "3. Registrar resultado."
        )
        quando_usar = "Quando o tema precisa virar compromisso, revisão futura ou reunião."
        quando_evitar = "Evitar para alertas simples que podem ser resolvidos no mesmo dia."
    else:
        template = (
            "Resumo Valoris\n\n"
            "Ativo: {ticker} — {empresa}\n"
            "Tipo: {tipo}\n"
            "Severidade: {severidade}\n"
            "Diagnóstico: {contexto}\n"
            "Ação recomendada: {acao}\n"
            "Próximo passo: {proximo_passo}"
        )
        quando_usar = "Quando o objetivo é consolidar várias informações em uma visão executiva."
        quando_evitar = "Evitar quando o usuário precisa de uma mensagem curta para envio direto."

    return {
        "canal": canal,
        "tipo_comunicacao": tipo,
        "template": template,
        "quando_usar": quando_usar,
        "quando_evitar": quando_evitar,
    }


def diagnosticar_canal_para_playbook(item: Dict[str, Any]) -> Dict[str, Any]:
    canal = _txt(item.get("canal")) or "Sem canal"
    score = _int(item.get("score_canal"), 0)
    enviados = _int(item.get("enviados"), 0)
    taxa_resposta = float(item.get("taxa_resposta") or 0)
    taxa_erro = float(item.get("taxa_erro") or 0)
    diagnostico = _txt(item.get("diagnostico"))
    acao = _txt(item.get("acao_otimizacao"))

    if score >= 80 and enviados:
        prioridade = "Padronizar"
        status = "Canal promissor para virar padrão"
        tipo = "Padrão recomendado"
    elif taxa_erro > 0:
        prioridade = "Corrigir"
        status = "Canal exige correção antes de virar padrão"
        tipo = "Correção operacional"
    elif enviados and taxa_resposta == 0:
        prioridade = "Testar"
        status = "Canal precisa de novo texto, horário ou abordagem"
        tipo = "Teste de abordagem"
    elif not enviados:
        prioridade = "Validar"
        status = "Canal ainda sem dados suficientes"
        tipo = "Experimento manual"
    else:
        prioridade = "Acompanhar"
        status = "Canal em validação"
        tipo = "Acompanhamento"

    base_template = template_padrao_por_canal(canal, tipo)

    return {
        "canal": canal,
        "score_canal": score,
        "enviados": enviados,
        "taxa_resposta": taxa_resposta,
        "taxa_erro": taxa_erro,
        "diagnostico": diagnostico,
        "acao_otimizacao": acao,
        "prioridade": prioridade,
        "status": status,
        "tipo_comunicacao": tipo,
        "template": base_template["template"],
        "quando_usar": base_template["quando_usar"],
        "quando_evitar": base_template["quando_evitar"],
    }


def gerar_sugestoes_playbook() -> List[Dict[str, Any]]:
    ranking = carregar_ranking_canais()

    if not ranking:
        canais_padrao = ["WhatsApp", "E-mail", "Calendário", "Resumo Executivo"]
        return [
            {
                **template_padrao_por_canal(canal, "Experimento manual"),
                "score_canal": 0,
                "enviados": 0,
                "taxa_resposta": 0.0,
                "taxa_erro": 0.0,
                "diagnostico": "Canal ainda sem dados suficientes",
                "acao_otimizacao": "Executar comunicação manual controlada e registrar resultado.",
                "prioridade": "Validar",
                "status": "Canal precisa de teste inicial",
            }
            for canal in canais_padrao
        ]

    sugestoes = [diagnosticar_canal_para_playbook(item) for item in ranking]

    canais_existentes = {item["canal"] for item in sugestoes}
    for canal in ["WhatsApp", "E-mail", "Calendário", "Resumo Executivo"]:
        if canal not in canais_existentes:
            sugestoes.append(
                {
                    **template_padrao_por_canal(canal, "Experimento manual"),
                    "score_canal": 0,
                    "enviados": 0,
                    "taxa_resposta": 0.0,
                    "taxa_erro": 0.0,
                    "diagnostico": "Canal ainda sem dados suficientes",
                    "acao_otimizacao": "Executar comunicação manual controlada e registrar resultado.",
                    "prioridade": "Validar",
                    "status": "Canal precisa de teste inicial",
                }
            )

    ordem = {"Corrigir": 1, "Padronizar": 2, "Testar": 3, "Validar": 4, "Acompanhar": 5}
    sugestoes.sort(key=lambda item: (ordem.get(item.get("prioridade"), 9), -_int(item.get("score_canal"), 0), item.get("canal", "")))
    return sugestoes


def salvar_item_playbook(item: Dict[str, Any], responsavel: str, status_playbook: str, observacao: str = "") -> Path:
    _garantir_csv(CAMINHO_PLAYBOOK, CAMPOS_PLAYBOOK)

    with CAMINHO_PLAYBOOK.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_PLAYBOOK)
        escritor.writerow(
            {
                "data_hora": _agora_iso(),
                "canal": _txt(item.get("canal")),
                "tipo_comunicacao": _txt(item.get("tipo_comunicacao")),
                "prioridade": _txt(item.get("prioridade")),
                "template": _txt(item.get("template")),
                "quando_usar": _txt(item.get("quando_usar")),
                "quando_evitar": _txt(item.get("quando_evitar")),
                "responsavel": _txt(responsavel),
                "status_playbook": _txt(status_playbook),
                "observacao": _txt(observacao),
            }
        )

    return CAMINHO_PLAYBOOK


def calcular_metricas_playbook() -> Dict[str, Any]:
    sugestoes = gerar_sugestoes_playbook()
    playbook = carregar_playbook()
    planos = carregar_planos_canais()
    resultados = carregar_resultados()
    metricas_otimizacao = carregar_metricas_otimizacao()

    canais_sugeridos = len({item.get("canal") for item in sugestoes})
    canais_aprovados = len({item.get("canal") for item in playbook if _txt(item.get("status_playbook")) in {"Aprovado", "Padrão oficial", "Em uso"}})
    itens_playbook = len(playbook)

    prioridades = Counter(item.get("prioridade", "Sem prioridade") for item in sugestoes)
    correcoes = prioridades.get("Corrigir", 0)
    padronizar = prioridades.get("Padronizar", 0)
    testar = prioridades.get("Testar", 0)
    validar = prioridades.get("Validar", 0)

    score_otimizacao = _int(metricas_otimizacao.get("score_otimizacao"), 0)

    score = 45
    score += min(score_otimizacao // 4, 25)

    if sugestoes:
        score += 10

    if itens_playbook:
        score += 15

    if canais_aprovados:
        score += 10

    if correcoes:
        score -= min(correcoes * 10, 25)

    score = max(0, min(100, int(score)))

    if not sugestoes:
        risco = "Baixo"
        decisao = "Sem dados suficientes para criar playbook"
        proximo = "Gerar resultados de comunicação e otimização por canal."
    elif correcoes:
        risco = "Médio"
        decisao = "Há canais que precisam de correção antes de virarem padrão"
        proximo = "Corrigir canais problemáticos e aprovar apenas padrões seguros."
    elif itens_playbook and canais_aprovados:
        risco = "Baixo"
        decisao = "Playbook de comunicação em formação"
        proximo = "Usar padrões aprovados em próximos rascunhos e medir resultado."
    elif padronizar:
        risco = "Baixo/Médio"
        decisao = "Há canais promissores para padronizar"
        proximo = "Salvar padrões oficiais e usá-los no próximo ciclo."
    else:
        risco = "Baixo/Médio"
        decisao = "Playbook ainda em validação"
        proximo = "Testar templates por canal e registrar resultados."

    return {
        "versao": VERSAO_PLAYBOOK_COMUNICACAO_VALORIS,
        "gerado_em": _agora_iso(),
        "score_playbook": score,
        "canais_sugeridos": canais_sugeridos,
        "itens_playbook": itens_playbook,
        "canais_aprovados": canais_aprovados,
        "correcoes": correcoes,
        "padronizar": padronizar,
        "testar": testar,
        "validar": validar,
        "planos_otimizacao": len(planos),
        "resultados": len(resultados),
        "score_otimizacao": score_otimizacao,
        "por_prioridade": dict(prioridades),
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo,
    }


def gerar_relatorio_playbook_markdown() -> str:
    metricas = calcular_metricas_playbook()
    sugestoes = gerar_sugestoes_playbook()
    playbook = carregar_playbook()

    linhas_sugestoes = "\n".join(
        [
            f"- **{item['canal']} — {item['prioridade']} — score {item['score_canal']}/100**: {item['status']}. Ação: {item['acao_otimizacao']}"
            for item in sugestoes
        ]
    ) or "- Nenhuma sugestão de playbook."

    linhas_playbook = "\n".join(
        [
            f"- **{item['canal']} — {item['tipo_comunicacao']} — {item['status_playbook']}**: {item['quando_usar']}"
            for item in playbook[-30:]
        ]
    ) or "- Nenhum padrão salvo ainda."

    return f"""# Playbook de Comunicação — Valoris

Versão: {VERSAO_PLAYBOOK_COMUNICACAO_VALORIS}  
Gerado em: {_agora_iso()}

## Diagnóstico

Score playbook: {metricas['score_playbook']}/100  
Canais sugeridos: {metricas['canais_sugeridos']}  
Itens salvos no playbook: {metricas['itens_playbook']}  
Canais aprovados: {metricas['canais_aprovados']}  
Canais para correção: {metricas['correcoes']}  
Canais para padronizar: {metricas['padronizar']}  
Score otimização: {metricas['score_otimizacao']}/100  

Risco: {metricas['risco']}  
Decisão: {metricas['decisao']}  
Próximo passo: {metricas['proximo_passo']}

## Sugestões por canal

{linhas_sugestoes}

## Padrões já salvos

{linhas_playbook}

## Estratégia

Esta versão cria o playbook antes da automação. O Valoris passa a documentar quais mensagens usar, quando usar, quando evitar e quais canais merecem padronização.
"""


def salvar_relatorio_playbook() -> Path:
    CAMINHO_RELATORIO.write_text(gerar_relatorio_playbook_markdown(), encoding="utf-8")
    return CAMINHO_RELATORIO


def gerar_manifesto_playbook() -> Dict[str, Any]:
    return {
        "produto": "Valoris",
        "versao": VERSAO_PLAYBOOK_COMUNICACAO_VALORIS,
        "modulo": "playbook_comunicacao_valoris",
        "data_hora": _agora_iso(),
        "metricas": calcular_metricas_playbook(),
        "sugestoes": gerar_sugestoes_playbook(),
        "playbook_salvo": carregar_playbook(),
        "principio": "antes de automatizar, padronizar; antes de padronizar, medir",
        "proxima_etapa": "rascunhos usando playbook ou automação controlada",
    }


def salvar_manifesto_playbook() -> Path:
    CAMINHO_MANIFESTO.write_text(
        json.dumps(gerar_manifesto_playbook(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return CAMINHO_MANIFESTO


def renderizar_playbook_comunicacao_valoris() -> None:
    st.subheader("Playbook de Comunicação")
    st.caption("Padrões por canal antes de qualquer automação externa real.")

    metricas = calcular_metricas_playbook()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Score playbook", f"{metricas['score_playbook']}/100")
    col2.metric("Canais", metricas["canais_sugeridos"])
    col3.metric("Salvos", metricas["itens_playbook"])
    col4.metric("Aprovados", metricas["canais_aprovados"])
    col5.metric("Correções", metricas["correcoes"])

    if metricas["risco"] == "Médio":
        st.warning(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    elif metricas["risco"] == "Baixo":
        st.success(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    else:
        st.info(f"{metricas['decisao']} — {metricas['proximo_passo']}")

    st.divider()

    sugestoes = gerar_sugestoes_playbook()

    st.markdown("### Sugestões de playbook")

    col_f1, col_f2 = st.columns(2)
    canais = ["Todos"] + sorted({item.get("canal", "") for item in sugestoes if item.get("canal")})
    prioridades = ["Todas"] + sorted({item.get("prioridade", "") for item in sugestoes if item.get("prioridade")})
    filtro_canal = col_f1.selectbox("Canal", canais)
    filtro_prioridade = col_f2.selectbox("Prioridade", prioridades)

    filtrados = []

    for item in sugestoes:
        if filtro_canal != "Todos" and item.get("canal") != filtro_canal:
            continue
        if filtro_prioridade != "Todas" and item.get("prioridade") != filtro_prioridade:
            continue
        filtrados.append(item)

    st.dataframe(
        [
            {
                "canal": item.get("canal"),
                "prioridade": item.get("prioridade"),
                "score canal": item.get("score_canal"),
                "tipo": item.get("tipo_comunicacao"),
                "status": item.get("status"),
                "quando usar": item.get("quando_usar"),
                "ação": item.get("acao_otimizacao"),
            }
            for item in filtrados
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Aprovar padrão do playbook")

    if filtrados:
        opcoes = [
            f"{item['canal']} | {item['prioridade']} | {item['tipo_comunicacao']}"
            for item in filtrados
        ]

        escolha = st.selectbox("Padrão sugerido", opcoes)
        item = filtrados[opcoes.index(escolha)]

        st.text_area("Template", value=item.get("template", ""), height=260)
        st.info(f"Quando usar: {item.get('quando_usar')}")
        st.warning(f"Quando evitar: {item.get('quando_evitar')}")

        col_a, col_b = st.columns(2)
        status_playbook = col_a.selectbox("Status do playbook", ["Aprovado", "Padrão oficial", "Em teste", "Em revisão", "Bloqueado"])
        responsavel = col_b.text_input("Responsável", value="Fundador")

        observacao = st.text_area(
            "Observação",
            value=f"Padrão registrado no Playbook de Comunicação v{VERSAO_PLAYBOOK_COMUNICACAO_VALORIS}.",
            height=90,
        )

        if st.button("Salvar padrão no playbook"):
            salvar_item_playbook(
                item,
                responsavel=responsavel,
                status_playbook=status_playbook,
                observacao=observacao,
            )
            st.success("Padrão salvo no playbook.")
            st.rerun()
    else:
        st.info("Nenhuma sugestão encontrada com os filtros atuais.")

    playbook = carregar_playbook()
    if playbook:
        st.markdown("### Playbook salvo")
        st.dataframe(playbook, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Relatórios")

    col_r1, col_r2 = st.columns(2)

    if col_r1.button("Salvar relatório do playbook"):
        caminho = salvar_relatorio_playbook()
        st.success(f"Relatório salvo em {caminho}")

    if col_r2.button("Salvar manifesto do playbook"):
        caminho = salvar_manifesto_playbook()
        st.success(f"Manifesto salvo em {caminho}")

    st.download_button(
        "Baixar relatório do playbook (.md)",
        data=gerar_relatorio_playbook_markdown(),
        file_name="RELATORIO_PLAYBOOK_COMUNICACAO_VALORIS.md",
        mime="text/markdown",
    )


def executar_autoteste_playbook_comunicacao_valoris() -> Dict[str, Any]:
    return {
        "ok": True,
        "versao": VERSAO_PLAYBOOK_COMUNICACAO_VALORIS,
        "metricas": calcular_metricas_playbook(),
    }
