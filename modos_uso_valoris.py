# modos_uso_valoris.py
# Valoris — Modos de Uso e Menu Inteligente v3.13.1
# ------------------------------------------------------------
# Objetivo:
# - Simplificar a experiência do usuário beta.
# - Organizar o Valoris por modos de uso, não apenas por páginas técnicas.
# - Recomendar a menor jornada possível conforme o perfil do usuário.
# - Registrar preferência de modo e revisão da experiência.
# - Não altera decisões financeiras automaticamente.
# - Não envia mensagens automaticamente.

from __future__ import annotations

import csv
import json
from collections import Counter, deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st


VERSAO_MODOS_USO_VALORIS = "3.13.1"

CAMINHO_PREFERENCIA = Path("preferencia_modo_uso_valoris.json")
CAMINHO_REVISOES = Path("revisoes_modos_uso_valoris.csv")
CAMINHO_RELATORIO = Path("RELATORIO_MODOS_USO_VALORIS.md")
CAMINHO_MANIFESTO = Path("manifesto_modos_uso_valoris.json")

CAMPOS_REVISOES = [
    "data_hora",
    "modo",
    "perfil_usuario",
    "score_clareza",
    "responsavel",
    "decisao",
    "proximo_passo",
    "observacao",
]


MODOS_USO: Dict[str, Dict[str, Any]] = {
    "Beta Guiado": {
        "perfil": "Usuário novo ou avaliador do produto",
        "promessa": "Entender o Valoris em poucos minutos e seguir uma jornada simples.",
        "quando_usar": "Quando alguém vai testar o produto pela primeira vez.",
        "paginas_essenciais": [
            "Jornada Beta",
            "Cockpit Principal",
            "Motor Análise Ativos",
            "Pipeline Principal",
            "Cockpit Comunicação",
        ],
        "passos": [
            "Abrir Jornada Beta.",
            "Ver próxima etapa recomendada.",
            "Analisar um ativo.",
            "Salvar uma decisão ou pipeline.",
            "Abrir Cockpit Principal para visão executiva.",
        ],
    },
    "Investidor": {
        "perfil": "Usuário que quer analisar ativos e acompanhar decisões",
        "promessa": "Sair de uma análise solta para uma decisão acompanhável.",
        "quando_usar": "Quando o objetivo é estudar ações/FIIs e decidir o que fazer.",
        "paginas_essenciais": [
            "Motor Análise Ativos",
            "Análise Principal",
            "Histórico Principal",
            "Pipeline Principal",
            "Radar Principal",
            "Agenda Revisões",
            "Cockpit Principal",
        ],
        "passos": [
            "Analisar ativo no Motor.",
            "Conferir ranking na Análise Principal.",
            "Transformar tese em ação no Pipeline.",
            "Acompanhar riscos no Radar.",
            "Revisar tudo no Cockpit Principal.",
        ],
    },
    "Comunicação": {
        "perfil": "Usuário que quer transformar decisões em mensagens e acompanhamento",
        "promessa": "Criar, aprovar, exportar, enviar manualmente e medir comunicação.",
        "quando_usar": "Quando uma decisão precisa virar comunicação rastreável.",
        "paginas_essenciais": [
            "Cockpit Comunicação",
            "Playbook Comunicação",
            "Rascunhos Playbook",
            "Aprovação Playbook",
            "Notificações Externas",
            "Aprovação Notificações",
            "Exportação Notificações",
            "Envio Manual",
            "Resultados Comunicações",
            "Otimização Canais",
        ],
        "passos": [
            "Abrir Cockpit Comunicação.",
            "Ver gargalo principal.",
            "Gerar rascunho com Playbook.",
            "Aprovar e promover para fluxo oficial.",
            "Exportar, registrar envio manual e medir resultado.",
        ],
    },
    "Fundador": {
        "perfil": "Criador do produto, gestor do beta ou operador estratégico",
        "promessa": "Enxergar maturidade, gargalos, qualidade e próximos movimentos do produto.",
        "quando_usar": "Quando o objetivo é evoluir o Valoris como produto.",
        "paginas_essenciais": [
            "Jornada Beta",
            "Cockpit Principal",
            "Cockpit Comunicação",
            "Health Check",
            "Migração Backend",
            "Repository Backend",
            "Launch Readiness",
        ],
        "passos": [
            "Abrir Jornada Beta para ver maturidade.",
            "Conferir Cockpit Principal.",
            "Conferir Cockpit Comunicação.",
            "Validar saúde técnica.",
            "Definir próxima melhoria de produto.",
        ],
    },
    "Técnico": {
        "perfil": "Desenvolvedor ou responsável por estabilidade e dados",
        "promessa": "Validar saúde, dados, backend, repository e risco técnico.",
        "quando_usar": "Quando o objetivo é manutenção, migração ou estabilidade.",
        "paginas_essenciais": [
            "Health Check",
            "Repository Backend",
            "SQLite Local",
            "Simulador Migração",
            "Mapa Dados",
            "Migração Backend",
            "Release Guard",
        ],
        "passos": [
            "Rodar release_guard.py.",
            "Abrir Health Check.",
            "Conferir Repository Backend.",
            "Validar dados locais.",
            "Só depois avançar versão.",
        ],
    },
}


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


def _garantir_csv(caminho: Path, campos: List[str]) -> None:
    if caminho.exists():
        return

    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()


def carregar_revisoes() -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_REVISOES, CAMPOS_REVISOES)

    try:
        with CAMINHO_REVISOES.open("r", newline="", encoding="utf-8") as arquivo:
            leitor = csv.DictReader(arquivo)
            return list(deque(leitor, maxlen=1000))
    except Exception:
        return []


def carregar_preferencia() -> Dict[str, Any]:
    if not CAMINHO_PREFERENCIA.exists():
        return {}

    try:
        return json.loads(CAMINHO_PREFERENCIA.read_text(encoding="utf-8"))
    except Exception:
        return {}


def salvar_preferencia(modo: str, perfil_usuario: str, responsavel: str, observacao: str = "") -> Path:
    payload = {
        "produto": "Valoris",
        "versao": VERSAO_MODOS_USO_VALORIS,
        "data_hora": _agora_iso(),
        "modo": _txt(modo),
        "perfil_usuario": _txt(perfil_usuario),
        "responsavel": _txt(responsavel),
        "observacao": _txt(observacao),
    }

    CAMINHO_PREFERENCIA.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return CAMINHO_PREFERENCIA


def salvar_revisao_modo(modo: str, perfil_usuario: str, score_clareza: int, responsavel: str, decisao: str, proximo_passo: str, observacao: str = "") -> Path:
    _garantir_csv(CAMINHO_REVISOES, CAMPOS_REVISOES)

    with CAMINHO_REVISOES.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_REVISOES)
        escritor.writerow(
            {
                "data_hora": _agora_iso(),
                "modo": _txt(modo),
                "perfil_usuario": _txt(perfil_usuario),
                "score_clareza": _int(score_clareza),
                "responsavel": _txt(responsavel),
                "decisao": _txt(decisao),
                "proximo_passo": _txt(proximo_passo),
                "observacao": _txt(observacao),
            }
        )

    return CAMINHO_REVISOES


def carregar_metricas_jornada() -> Dict[str, Any]:
    try:
        from jornada_beta_valoris import calcular_metricas_jornada_beta
        return calcular_metricas_jornada_beta()
    except Exception:
        return {}


def carregar_metricas_cockpits() -> Dict[str, Dict[str, Any]]:
    metricas: Dict[str, Dict[str, Any]] = {}

    try:
        from cockpit_principal_valoris import calcular_metricas_cockpit_principal
        metricas["Cockpit Principal"] = calcular_metricas_cockpit_principal()
    except Exception:
        metricas["Cockpit Principal"] = {}

    try:
        from cockpit_comunicacao_valoris import calcular_metricas_cockpit_comunicacao
        metricas["Cockpit Comunicação"] = calcular_metricas_cockpit_comunicacao()
    except Exception:
        metricas["Cockpit Comunicação"] = {}

    return metricas


def detectar_modo_recomendado() -> Dict[str, Any]:
    metricas_jornada = carregar_metricas_jornada()
    metricas_cockpits = carregar_metricas_cockpits()
    preferencia = carregar_preferencia()

    score_jornada = _int(metricas_jornada.get("score_jornada"), 0)
    pendentes_jornada = _int(metricas_jornada.get("pendentes"), 0)
    score_cockpit_principal = _int(metricas_cockpits.get("Cockpit Principal", {}).get("score_cockpit"), 0)
    score_cockpit_comunicacao = _int(metricas_cockpits.get("Cockpit Comunicação", {}).get("score_cockpit"), 0)

    if preferencia.get("modo"):
        modo = preferencia["modo"]
        motivo = "Preferência de modo já registrada."
    elif score_jornada < 70 or pendentes_jornada >= 2:
        modo = "Beta Guiado"
        motivo = "A jornada beta ainda precisa de condução simples."
    elif score_cockpit_principal >= 75 and score_cockpit_comunicacao < 60:
        modo = "Investidor"
        motivo = "A análise/pipeline está mais madura que a comunicação."
    elif score_cockpit_comunicacao >= 70:
        modo = "Comunicação"
        motivo = "A esteira de comunicação já possui dados suficientes para gestão."
    else:
        modo = "Fundador"
        motivo = "O produto precisa de visão executiva e priorização."

    info = MODOS_USO.get(modo, MODOS_USO["Beta Guiado"])

    return {
        "modo": modo,
        "motivo": motivo,
        "info": info,
        "score_jornada": score_jornada,
        "pendentes_jornada": pendentes_jornada,
        "score_cockpit_principal": score_cockpit_principal,
        "score_cockpit_comunicacao": score_cockpit_comunicacao,
        "preferencia": preferencia,
    }


def calcular_metricas_modos_uso() -> Dict[str, Any]:
    revisoes = carregar_revisoes()
    preferencia = carregar_preferencia()
    recomendado = detectar_modo_recomendado()

    modos_revisados = Counter(_txt(item.get("modo")) for item in revisoes if _txt(item.get("modo")))
    scores = [_int(item.get("score_clareza")) for item in revisoes if _txt(item.get("score_clareza"))]

    score_clareza_medio = 0
    if scores:
        score_clareza_medio = round(sum(scores) / len(scores), 1)

    score = 45

    if preferencia.get("modo"):
        score += 20

    if revisoes:
        score += 15

    if score_clareza_medio >= 8:
        score += 15
    elif score_clareza_medio >= 6:
        score += 8

    if recomendado["score_jornada"] >= 70:
        score += 10

    score = max(0, min(100, int(score)))

    if not preferencia.get("modo"):
        risco = "Médio"
        decisao = "Ainda falta definir o modo principal de uso"
        proximo = "Selecionar um modo recomendado e salvar preferência."
    elif not revisoes:
        risco = "Baixo/Médio"
        decisao = "Modo definido, mas ainda sem revisão de clareza"
        proximo = "Registrar revisão do modo e avaliar se a jornada ficou simples."
    elif score_clareza_medio < 7:
        risco = "Baixo/Médio"
        decisao = "Experiência ainda pode estar confusa"
        proximo = "Reduzir páginas essenciais e melhorar a orientação inicial."
    else:
        risco = "Baixo"
        decisao = "Modo de uso definido e experiência mais clara"
        proximo = "Avançar para demo premium com dados exemplo."

    return {
        "versao": VERSAO_MODOS_USO_VALORIS,
        "gerado_em": _agora_iso(),
        "score_modos": score,
        "modo_recomendado": recomendado["modo"],
        "motivo_recomendacao": recomendado["motivo"],
        "modo_preferido": preferencia.get("modo", ""),
        "revisoes": len(revisoes),
        "score_clareza_medio": score_clareza_medio,
        "modos_revisados": dict(modos_revisados),
        "score_jornada": recomendado["score_jornada"],
        "score_cockpit_principal": recomendado["score_cockpit_principal"],
        "score_cockpit_comunicacao": recomendado["score_cockpit_comunicacao"],
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo,
    }


def gerar_relatorio_modos_markdown() -> str:
    metricas = calcular_metricas_modos_uso()
    recomendado = detectar_modo_recomendado()

    blocos_modos = "\n\n".join(
        [
            f"""## {nome}

Perfil: {info['perfil']}  
Promessa: {info['promessa']}  
Quando usar: {info['quando_usar']}  

Páginas essenciais:
{chr(10).join([f"- {pagina}" for pagina in info['paginas_essenciais']])}

Passos:
{chr(10).join([f"{i + 1}. {passo}" for i, passo in enumerate(info['passos'])])}
"""
            for nome, info in MODOS_USO.items()
        ]
    )

    return f"""# Modos de Uso — Valoris

Versão: {VERSAO_MODOS_USO_VALORIS}  
Gerado em: {_agora_iso()}

## Diagnóstico

Score modos: {metricas['score_modos']}/100  
Modo recomendado: {metricas['modo_recomendado']}  
Motivo: {metricas['motivo_recomendacao']}  
Modo preferido: {metricas['modo_preferido'] or 'não definido'}  
Revisões: {metricas['revisoes']}  
Score médio de clareza: {metricas['score_clareza_medio']}/10  

Risco: {metricas['risco']}  
Decisão: {metricas['decisao']}  
Próximo passo: {metricas['proximo_passo']}

## Modo recomendado agora

**{recomendado['modo']}** — {recomendado['info']['promessa']}

## Modos disponíveis

{blocos_modos}

## Estratégia

Esta versão transforma o menu técnico em experiência por intenção. O usuário não deve precisar entender todas as páginas; ele deve escolher um modo e seguir um caminho curto.
"""


def salvar_relatorio_modos() -> Path:
    CAMINHO_RELATORIO.write_text(gerar_relatorio_modos_markdown(), encoding="utf-8")
    return CAMINHO_RELATORIO


def gerar_manifesto_modos() -> Dict[str, Any]:
    return {
        "produto": "Valoris",
        "versao": VERSAO_MODOS_USO_VALORIS,
        "modulo": "modos_uso_valoris",
        "data_hora": _agora_iso(),
        "metricas": calcular_metricas_modos_uso(),
        "modo_recomendado": detectar_modo_recomendado(),
        "modos": MODOS_USO,
        "preferencia": carregar_preferencia(),
        "revisoes": carregar_revisoes(),
        "principio": "usuário não compra complexidade; compra clareza, direção e resultado",
        "proxima_etapa": "demo premium com dados exemplo",
    }


def salvar_manifesto_modos() -> Path:
    CAMINHO_MANIFESTO.write_text(
        json.dumps(gerar_manifesto_modos(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return CAMINHO_MANIFESTO


def renderizar_modos_uso_valoris() -> None:
    st.subheader("Modos de Uso")
    st.caption("Menu inteligente por intenção: beta, investidor, comunicação, fundador ou técnico.")

    metricas = calcular_metricas_modos_uso()
    recomendado = detectar_modo_recomendado()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Score modos", f"{metricas['score_modos']}/100")
    col2.metric("Recomendado", metricas["modo_recomendado"])
    col3.metric("Preferido", metricas["modo_preferido"] or "Não definido")
    col4.metric("Revisões", metricas["revisoes"])
    col5.metric("Clareza", f"{metricas['score_clareza_medio']}/10")

    if metricas["risco"] == "Médio":
        st.warning(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    elif metricas["risco"] == "Baixo":
        st.success(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    else:
        st.info(f"{metricas['decisao']} — {metricas['proximo_passo']}")

    st.markdown(
        f"""
### Modo recomendado agora

**{recomendado['modo']}**  
Motivo: {recomendado['motivo']}  
Promessa: {recomendado['info']['promessa']}
"""
    )

    st.divider()

    st.markdown("### Escolha o modo de uso")

    modo = st.selectbox("Modo", list(MODOS_USO.keys()), index=list(MODOS_USO.keys()).index(recomendado["modo"]))
    info = MODOS_USO[modo]

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f"**Perfil:** {info['perfil']}")
        st.markdown(f"**Promessa:** {info['promessa']}")
        st.markdown(f"**Quando usar:** {info['quando_usar']}")

    with col_b:
        st.markdown("**Páginas essenciais:**")
        for pagina in info["paginas_essenciais"]:
            st.markdown(f"- {pagina}")

    st.markdown("### Caminho curto recomendado")

    for indice, passo in enumerate(info["passos"], start=1):
        st.markdown(f"**{indice}.** {passo}")

    st.divider()

    st.markdown("### Salvar preferência e revisão")

    col_p1, col_p2 = st.columns(2)
    perfil_usuario = col_p1.text_input("Perfil do usuário", value=info["perfil"])
    responsavel = col_p2.text_input("Responsável", value="Fundador")

    score_clareza = st.slider("O caminho ficou claro?", min_value=0, max_value=10, value=8)
    decisao = st.text_input("Decisão", value=f"Usar modo {modo} como referência da experiência.")
    proximo = st.text_input("Próximo passo", value="Testar este modo em uma demo curta.")
    observacao = st.text_area(
        "Observação",
        value=f"Revisão registrada em Modos de Uso v{VERSAO_MODOS_USO_VALORIS}.",
        height=90,
    )

    col_s1, col_s2 = st.columns(2)

    if col_s1.button("Salvar preferência de modo"):
        salvar_preferencia(
            modo=modo,
            perfil_usuario=perfil_usuario,
            responsavel=responsavel,
            observacao=observacao,
        )
        st.success("Preferência de modo salva.")
        st.rerun()

    if col_s2.button("Salvar revisão de clareza"):
        salvar_revisao_modo(
            modo=modo,
            perfil_usuario=perfil_usuario,
            score_clareza=score_clareza,
            responsavel=responsavel,
            decisao=decisao,
            proximo_passo=proximo,
            observacao=observacao,
        )
        st.success("Revisão de clareza salva.")
        st.rerun()

    revisoes = carregar_revisoes()
    if revisoes:
        st.markdown("### Revisões registradas")
        st.dataframe(revisoes, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Relatórios")

    col_r1, col_r2 = st.columns(2)

    if col_r1.button("Salvar relatório de modos"):
        caminho = salvar_relatorio_modos()
        st.success(f"Relatório salvo em {caminho}")

    if col_r2.button("Salvar manifesto de modos"):
        caminho = salvar_manifesto_modos()
        st.success(f"Manifesto salvo em {caminho}")

    st.download_button(
        "Baixar relatório de modos (.md)",
        data=gerar_relatorio_modos_markdown(),
        file_name="RELATORIO_MODOS_USO_VALORIS.md",
        mime="text/markdown",
    )


def executar_autoteste_modos_uso_valoris() -> Dict[str, Any]:
    return {
        "ok": True,
        "versao": VERSAO_MODOS_USO_VALORIS,
        "metricas": calcular_metricas_modos_uso(),
    }
