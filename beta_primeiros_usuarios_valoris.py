# beta_primeiros_usuarios_valoris.py
# Valoris — Beta para Primeiros Usuários v3.13.5
# Organiza candidatos, convites manuais, sessões, feedbacks e sinais reais de validação.
# Não envia mensagens automaticamente e não altera dados financeiros reais.

from __future__ import annotations

import csv
import json
from collections import Counter, deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st


VERSAO_BETA_USUARIOS_VALORIS = "3.13.5"

CAMINHO_CANDIDATOS = Path("candidatos_beta_valoris.csv")
CAMINHO_SESSOES = Path("sessoes_beta_valoris.csv")
CAMINHO_FEEDBACKS = Path("feedbacks_beta_valoris.csv")
CAMINHO_RELATORIO = Path("RELATORIO_BETA_USUARIOS_VALORIS.md")
CAMINHO_MANIFESTO = Path("manifesto_beta_usuarios_valoris.json")

CAMPOS_CANDIDATOS = [
    "data_hora", "nome", "perfil", "origem", "dor_principal",
    "nivel_interesse", "status", "responsavel", "observacao",
]

CAMPOS_SESSOES = [
    "data_hora", "nome", "perfil", "tipo_sessao", "status_sessao",
    "clareza", "valor_percebido", "facilidade", "confianca",
    "disposicao_pagar", "principal_objecao", "principal_duvida",
    "responsavel", "proximo_passo", "observacao",
]

CAMPOS_FEEDBACKS = [
    "data_hora", "nome", "perfil", "o_que_entendeu", "maior_valor",
    "maior_confusao", "usaria", "pagaria", "preco_sugerido",
    "nota_geral", "responsavel", "acao_recomendada", "observacao",
]

PERFIS_BETA: Dict[str, Dict[str, str]] = {
    "Investidor iniciante": {
        "dor": "Quer investir melhor, mas se sente perdido entre opiniões, vídeos e planilhas.",
        "promessa": "Mostrar como transformar dúvida em decisão organizada.",
        "foco": "Clareza, simplicidade e sensação de direção.",
    },
    "Investidor intermediário": {
        "dor": "Já estuda ativos, mas não acompanha decisões com método.",
        "promessa": "Mostrar análise, pipeline, revisão e cockpit em uma jornada única.",
        "foco": "Processo, disciplina e acompanhamento.",
    },
    "Investidor fundamentalista": {
        "dor": "Faz análise, mas precisa de rastreabilidade, tese, alertas e revisão contínua.",
        "promessa": "Mostrar o Valoris como sistema operacional de decisão.",
        "foco": "Valuation, tese, decisão, risco e revisão.",
    },
    "Pessoa de negócio/produto": {
        "dor": "Quer entender se o Valoris tem clareza, mercado e proposta vendável.",
        "promessa": "Mostrar produto, demo, pitch, jornada e próximos passos de validação.",
        "foco": "Valor comercial, diferenciação e beta.",
    },
}

STATUS_VALIDACAO = [
    "Convidar", "Convite enviado manualmente", "Demo agendada", "Demo realizada",
    "Feedback coletado", "Interessado", "Não interessado", "Aguardando retorno",
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


def _pct(parte: int, total: int) -> float:
    if not total:
        return 0.0
    return round((parte / total) * 100, 1)


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


def carregar_candidatos() -> List[Dict[str, str]]:
    return _ler_csv(CAMINHO_CANDIDATOS, CAMPOS_CANDIDATOS)


def carregar_sessoes() -> List[Dict[str, str]]:
    return _ler_csv(CAMINHO_SESSOES, CAMPOS_SESSOES)


def carregar_feedbacks() -> List[Dict[str, str]]:
    return _ler_csv(CAMINHO_FEEDBACKS, CAMPOS_FEEDBACKS)


def salvar_linha(caminho: Path, campos: List[str], dados: Dict[str, Any]) -> Path:
    _garantir_csv(caminho, campos)
    with caminho.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writerow({campo: _txt(dados.get(campo)) for campo in campos})
    return caminho


def salvar_candidato(nome: str, perfil: str, origem: str, dor_principal: str, nivel_interesse: int, status: str, responsavel: str, observacao: str = "") -> Path:
    return salvar_linha(
        CAMINHO_CANDIDATOS,
        CAMPOS_CANDIDATOS,
        {
            "data_hora": _agora_iso(),
            "nome": nome,
            "perfil": perfil,
            "origem": origem,
            "dor_principal": dor_principal,
            "nivel_interesse": nivel_interesse,
            "status": status,
            "responsavel": responsavel,
            "observacao": observacao,
        },
    )


def salvar_sessao(dados: Dict[str, Any]) -> Path:
    payload = dict(dados)
    payload["data_hora"] = _agora_iso()
    return salvar_linha(CAMINHO_SESSOES, CAMPOS_SESSOES, payload)


def salvar_feedback(dados: Dict[str, Any]) -> Path:
    payload = dict(dados)
    payload["data_hora"] = _agora_iso()
    return salvar_linha(CAMINHO_FEEDBACKS, CAMPOS_FEEDBACKS, payload)


def carregar_metricas_externas() -> Dict[str, Dict[str, Any]]:
    metricas: Dict[str, Dict[str, Any]] = {}
    modulos = [
        ("valor_comercial", "valor_comercial_valoris", "calcular_metricas_valor_comercial", "Investidor intermediário"),
        ("checklist", "checklist_produto_vendavel_valoris", "calcular_metricas_produto_vendavel", None),
        ("demo", "demo_premium_valoris", "calcular_metricas_demo", "Investidor Beta"),
        ("jornada", "jornada_beta_valoris", "calcular_metricas_jornada_beta", None),
        ("modos", "modos_uso_valoris", "calcular_metricas_modos_uso", None),
    ]
    for nome, modulo, funcao, arg in modulos:
        try:
            mod = __import__(modulo, fromlist=[funcao])
            metricas[nome] = getattr(mod, funcao)(arg) if arg else getattr(mod, funcao)()
        except Exception:
            metricas[nome] = {}
    return metricas


def gerar_convite_beta(perfil: str, nome: str = "") -> str:
    info = PERFIS_BETA.get(perfil, PERFIS_BETA["Investidor intermediário"])
    saudacao = f"Olá, {nome}." if _txt(nome) else "Olá."
    return f"""{saudacao}

Estou testando uma versão beta do Valoris, uma ferramenta que ajuda investidores a transformar análise de ativos em decisões mais organizadas e acompanháveis.

A ideia não é prometer lucro nem substituir julgamento humano. O foco é criar método: analisar um ativo, registrar uma tese, acompanhar preço teto, organizar alertas, revisar decisões e enxergar tudo em um cockpit.

Pensei em você porque este perfil combina com a dor abaixo:

{info['dor']}

A demo leva cerca de 5 minutos. Eu queria observar se a proposta fica clara, se parece útil e quais partes ainda geram dúvida.

Você toparia ver uma demonstração rápida e me dar um feedback sincero?"""


def gerar_roteiro_sessao_beta(perfil: str) -> List[Dict[str, str]]:
    info = PERFIS_BETA.get(perfil, PERFIS_BETA["Investidor intermediário"])
    return [
        {"ordem": "1", "etapa": "Contexto", "fala": f"Quero validar esta dor: {info['dor']}", "objetivo": "Confirmar dor real."},
        {"ordem": "2", "etapa": "Promessa", "fala": info["promessa"], "objetivo": "Medir entendimento rápido."},
        {"ordem": "3", "etapa": "Demo", "fala": "Vou mostrar análise, decisão, pipeline, alerta, comunicação e cockpit.", "objetivo": "Demonstrar valor em poucos minutos."},
        {"ordem": "4", "etapa": "Clareza", "fala": "Em uma frase, o que você entendeu que o Valoris faz?", "objetivo": "Medir clareza."},
        {"ordem": "5", "etapa": "Valor", "fala": "Qual parte parece mais útil para você?", "objetivo": "Identificar valor percebido."},
        {"ordem": "6", "etapa": "Confusão", "fala": "Qual parte ficou confusa ou desnecessária?", "objetivo": "Encontrar atrito."},
        {"ordem": "7", "etapa": "Comercial", "fala": "Você usaria? Pagaria? Em qual formato?", "objetivo": "Medir intenção real."},
    ]


def calcular_score_sessao(item: Dict[str, Any]) -> int:
    valores = [
        _int(item.get("clareza")),
        _int(item.get("valor_percebido")),
        _int(item.get("facilidade")),
        _int(item.get("confianca")),
        _int(item.get("disposicao_pagar")),
    ]
    return int(round(sum(valores) * 2, 0))


def calcular_metricas_beta_usuarios() -> Dict[str, Any]:
    candidatos = carregar_candidatos()
    sessoes = carregar_sessoes()
    feedbacks = carregar_feedbacks()
    metricas_externas = carregar_metricas_externas()

    score_valor = _int(metricas_externas.get("valor_comercial", {}).get("score_valor_comercial"), 0)
    score_checklist = _int(metricas_externas.get("checklist", {}).get("score_produto"), 0)
    score_demo = _int(metricas_externas.get("demo", {}).get("score_demo"), 0)

    interessados = len([c for c in candidatos if _txt(c.get("status")) in {"Interessado", "Demo agendada", "Demo realizada", "Feedback coletado"}])
    demos_realizadas = len([s for s in sessoes if _txt(s.get("status_sessao")) == "Realizada"])
    feedbacks_coletados = len(feedbacks)

    notas_sessoes = [calcular_score_sessao(s) for s in sessoes]
    media_sessoes = round(sum(notas_sessoes) / len(notas_sessoes), 1) if notas_sessoes else 0

    notas_feedback = [_int(f.get("nota_geral")) for f in feedbacks if _txt(f.get("nota_geral"))]
    media_feedback = round(sum(notas_feedback) / len(notas_feedback), 1) if notas_feedback else 0

    pagariam = len([f for f in feedbacks if _txt(f.get("pagaria")).lower() in {"sim", "talvez"}])
    usariam = len([f for f in feedbacks if _txt(f.get("usaria")).lower() in {"sim", "talvez"}])

    taxa_uso = _pct(usariam, feedbacks_coletados)
    taxa_pagamento = _pct(pagariam, feedbacks_coletados)
    taxa_demo = _pct(demos_realizadas, len(candidatos))

    perfis = Counter(_txt(c.get("perfil")) for c in candidatos if _txt(c.get("perfil")))
    objecoes = Counter(_txt(s.get("principal_objecao")) for s in sessoes if _txt(s.get("principal_objecao")))

    scores_base = [s for s in [score_valor, score_checklist, score_demo] if s > 0]
    score = int(sum(scores_base) / len(scores_base)) if scores_base else 55
    if candidatos:
        score += 5
    if demos_realizadas:
        score += 8
    if feedbacks_coletados:
        score += 10
    if taxa_uso >= 60:
        score += 7
    if taxa_pagamento >= 40:
        score += 7
    if media_feedback >= 8:
        score += 5
    score = max(0, min(100, int(score)))

    if not candidatos:
        maturidade = "Pronto para convidar"
        risco = "Baixo/Médio"
        decisao = "Estrutura pronta, mas ainda sem candidatos beta"
        proximo = "Cadastrar 3 candidatos e enviar convite manualmente."
    elif candidatos and not demos_realizadas:
        maturidade = "Convites em preparação"
        risco = "Baixo/Médio"
        decisao = "Candidatos registrados, mas ainda sem demo realizada"
        proximo = "Agendar e realizar a primeira demo de 5 minutos."
    elif demos_realizadas and not feedbacks_coletados:
        maturidade = "Demo em validação"
        risco = "Médio"
        decisao = "Demos realizadas, mas falta feedback estruturado"
        proximo = "Coletar feedback com perguntas de clareza, valor e pagamento."
    elif feedbacks_coletados and taxa_uso >= 60:
        maturidade = "Beta com sinal positivo"
        risco = "Baixo"
        decisao = "Há sinal inicial de interesse no beta"
        proximo = "Rodar mais 3 demos e comparar objeções recorrentes."
    else:
        maturidade = "Beta com sinal misto"
        risco = "Médio"
        decisao = "Feedback inicial ainda não confirma força suficiente"
        proximo = "Ajustar pitch, demo ou público antes de vender."

    return {
        "versao": VERSAO_BETA_USUARIOS_VALORIS,
        "gerado_em": _agora_iso(),
        "score_beta": score,
        "maturidade": maturidade,
        "candidatos": len(candidatos),
        "interessados": interessados,
        "demos_realizadas": demos_realizadas,
        "feedbacks": feedbacks_coletados,
        "media_sessoes": media_sessoes,
        "media_feedback": media_feedback,
        "taxa_demo": taxa_demo,
        "taxa_uso": taxa_uso,
        "taxa_pagamento": taxa_pagamento,
        "score_valor_comercial": score_valor,
        "score_checklist": score_checklist,
        "score_demo": score_demo,
        "perfis": dict(perfis),
        "objecoes": dict(objecoes),
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo,
    }


def gerar_relatorio_beta_markdown() -> str:
    metricas = calcular_metricas_beta_usuarios()
    candidatos = carregar_candidatos()
    sessoes = carregar_sessoes()
    feedbacks = carregar_feedbacks()

    linhas_candidatos = "\n".join(
        [f"- **{i['nome']} — {i['perfil']} — {i['status']}**: interesse {i['nivel_interesse']}/10. Dor: {i['dor_principal']}" for i in candidatos[-30:]]
    ) or "- Nenhum candidato cadastrado."

    linhas_sessoes = "\n".join(
        [f"- **{i['nome']} — {i['perfil']} — {i['status_sessao']}**: clareza {i['clareza']}/10, valor {i['valor_percebido']}/10, pagar {i['disposicao_pagar']}/10. Objeção: {i['principal_objecao']}" for i in sessoes[-30:]]
    ) or "- Nenhuma sessão registrada."

    linhas_feedbacks = "\n".join(
        [f"- **{i['nome']} — nota {i['nota_geral']}/10**: usaria={i['usaria']}, pagaria={i['pagaria']}, valor={i['maior_valor']}, confusão={i['maior_confusao']}" for i in feedbacks[-30:]]
    ) or "- Nenhum feedback registrado."

    return f"""# Beta para Primeiros Usuários — Valoris

Versão: {VERSAO_BETA_USUARIOS_VALORIS}  
Gerado em: {_agora_iso()}

## Diagnóstico

Score beta: {metricas['score_beta']}/100  
Maturidade: {metricas['maturidade']}  
Candidatos: {metricas['candidatos']}  
Interessados: {metricas['interessados']}  
Demos realizadas: {metricas['demos_realizadas']}  
Feedbacks: {metricas['feedbacks']}  
Média sessões: {metricas['media_sessoes']}/100  
Média feedback: {metricas['media_feedback']}/10  
Taxa demo: {metricas['taxa_demo']}%  
Taxa uso: {metricas['taxa_uso']}%  
Taxa pagamento: {metricas['taxa_pagamento']}%  

Score valor comercial: {metricas['score_valor_comercial']}/100  
Score checklist: {metricas['score_checklist']}/100  
Score demo: {metricas['score_demo']}/100  

Risco: {metricas['risco']}  
Decisão: {metricas['decisao']}  
Próximo passo: {metricas['proximo_passo']}

## Candidatos

{linhas_candidatos}

## Sessões

{linhas_sessoes}

## Feedbacks

{linhas_feedbacks}

## Estratégia

Esta versão tira o Valoris da validação interna e começa a colocá-lo diante de pessoas reais. O objetivo não é buscar elogio; é medir entendimento, valor percebido, objeções e disposição real de uso ou pagamento.
"""


def salvar_relatorio_beta() -> Path:
    CAMINHO_RELATORIO.write_text(gerar_relatorio_beta_markdown(), encoding="utf-8")
    return CAMINHO_RELATORIO


def gerar_manifesto_beta() -> Dict[str, Any]:
    return {
        "produto": "Valoris",
        "versao": VERSAO_BETA_USUARIOS_VALORIS,
        "modulo": "beta_primeiros_usuarios_valoris",
        "data_hora": _agora_iso(),
        "metricas": calcular_metricas_beta_usuarios(),
        "perfis_beta": PERFIS_BETA,
        "candidatos": carregar_candidatos(),
        "sessoes": carregar_sessoes(),
        "feedbacks": carregar_feedbacks(),
        "principio": "validar com gente real antes de construir mais",
        "proxima_etapa": "síntese dos feedbacks e priorização de melhorias beta",
    }


def salvar_manifesto_beta() -> Path:
    CAMINHO_MANIFESTO.write_text(json.dumps(gerar_manifesto_beta(), ensure_ascii=False, indent=2), encoding="utf-8")
    return CAMINHO_MANIFESTO


def renderizar_beta_primeiros_usuarios_valoris() -> None:
    st.subheader("Beta Usuários")
    st.caption("Organiza candidatos, convites manuais, demos e feedbacks reais para validar o Valoris.")

    metricas = calcular_metricas_beta_usuarios()
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Score beta", f"{metricas['score_beta']}/100")
    col2.metric("Maturidade", metricas["maturidade"])
    col3.metric("Candidatos", metricas["candidatos"])
    col4.metric("Demos", metricas["demos_realizadas"])
    col5.metric("Feedbacks", metricas["feedbacks"])

    if metricas["risco"] == "Médio":
        st.warning(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    elif metricas["risco"] == "Baixo":
        st.success(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    else:
        st.info(f"{metricas['decisao']} — {metricas['proximo_passo']}")

    st.divider()

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Candidatos", "Convite", "Sessão", "Feedback", "Relatórios"])

    with tab1:
        st.markdown("### Registrar candidato beta")
        col_a, col_b = st.columns(2)
        nome = col_a.text_input("Nome", value="")
        perfil = col_b.selectbox("Perfil", list(PERFIS_BETA.keys()))
        origem = st.text_input("Origem", value="Contato manual")
        dor = st.text_area("Dor principal", value=PERFIS_BETA[perfil]["dor"], height=80)
        interesse = st.slider("Nível de interesse", min_value=0, max_value=10, value=7)
        status = st.selectbox("Status", STATUS_VALIDACAO)
        responsavel = st.text_input("Responsável pelo candidato", value="Fundador")
        observacao = st.text_area("Observação do candidato", value="", height=80)

        if st.button("Salvar candidato beta"):
            salvar_candidato(nome, perfil, origem, dor, interesse, status, responsavel, observacao)
            st.success("Candidato beta registrado.")
            st.rerun()

        candidatos = carregar_candidatos()
        if candidatos:
            st.markdown("### Candidatos registrados")
            st.dataframe(candidatos, use_container_width=True, hide_index=True)

    with tab2:
        st.markdown("### Convite manual")
        perfil_convite = st.selectbox("Perfil do convite", list(PERFIS_BETA.keys()), key="perfil_convite")
        nome_convite = st.text_input("Nome para convite", value="", key="nome_convite")
        st.text_area("Texto do convite", value=gerar_convite_beta(perfil_convite, nome_convite), height=320)
        st.markdown("### Roteiro da sessão")
        st.dataframe(gerar_roteiro_sessao_beta(perfil_convite), use_container_width=True, hide_index=True)
        st.info("Envie manualmente. O Valoris não dispara mensagens automaticamente.")

    with tab3:
        st.markdown("### Registrar sessão/demo")
        candidatos = carregar_candidatos()
        nomes = [c.get("nome", "") for c in candidatos if c.get("nome")]
        nome_sessao = st.selectbox("Nome", nomes or ["Usuário beta"], key="nome_sessao")
        perfil_sessao = st.selectbox("Perfil", list(PERFIS_BETA.keys()), key="perfil_sessao")
        tipo_sessao = st.selectbox("Tipo de sessão", ["Demo 5 minutos", "Entrevista exploratória", "Teste guiado", "Revisão de produto"])
        status_sessao = st.selectbox("Status da sessão", ["Agendada", "Realizada", "Remarcada", "Cancelada"])
        clareza = st.slider("Clareza", min_value=0, max_value=10, value=8)
        valor = st.slider("Valor percebido", min_value=0, max_value=10, value=8)
        facilidade = st.slider("Facilidade", min_value=0, max_value=10, value=7)
        confianca = st.slider("Confiança", min_value=0, max_value=10, value=8)
        pagar = st.slider("Disposição a pagar", min_value=0, max_value=10, value=6)
        objecao = st.text_input("Principal objeção", value="Ainda parece amplo/complexo.")
        duvida = st.text_input("Principal dúvida", value="Como seria usado na rotina?")
        responsavel_sessao = st.text_input("Responsável pela sessão", value="Fundador")
        proximo_sessao = st.text_input("Próximo passo da sessão", value="Coletar feedback estruturado.")
        obs_sessao = st.text_area("Observação da sessão", value="", height=80)
        st.info(f"Score estimado da sessão: {int(round((clareza + valor + facilidade + confianca + pagar) * 2, 0))}/100")

        if st.button("Salvar sessão beta"):
            salvar_sessao({
                "nome": nome_sessao, "perfil": perfil_sessao, "tipo_sessao": tipo_sessao, "status_sessao": status_sessao,
                "clareza": clareza, "valor_percebido": valor, "facilidade": facilidade, "confianca": confianca,
                "disposicao_pagar": pagar, "principal_objecao": objecao, "principal_duvida": duvida,
                "responsavel": responsavel_sessao, "proximo_passo": proximo_sessao, "observacao": obs_sessao,
            })
            st.success("Sessão beta registrada.")
            st.rerun()

        sessoes = carregar_sessoes()
        if sessoes:
            st.markdown("### Sessões registradas")
            st.dataframe(sessoes, use_container_width=True, hide_index=True)

    with tab4:
        st.markdown("### Registrar feedback estruturado")
        candidatos = carregar_candidatos()
        nomes = [c.get("nome", "") for c in candidatos if c.get("nome")]
        nome_feedback = st.selectbox("Nome", nomes or ["Usuário beta"], key="nome_feedback")
        perfil_feedback = st.selectbox("Perfil", list(PERFIS_BETA.keys()), key="perfil_feedback")
        entendeu = st.text_area("O que a pessoa entendeu?", value="Entendeu que o Valoris organiza análise e decisão.", height=80)
        maior_valor = st.text_area("Maior valor percebido", value="Acompanhar decisões e não deixar análise solta.", height=80)
        confusao = st.text_area("Maior confusão", value="Quantidade de páginas e profundidade do sistema.", height=80)
        col_f1, col_f2 = st.columns(2)
        usaria = col_f1.selectbox("Usaria?", ["Sim", "Talvez", "Não"])
        pagaria = col_f2.selectbox("Pagaria?", ["Sim", "Talvez", "Não"])
        preco = st.text_input("Preço sugerido ou faixa", value="R$ 19 a R$ 49/mês")
        nota = st.slider("Nota geral", min_value=0, max_value=10, value=8)
        responsavel_feedback = st.text_input("Responsável pelo feedback", value="Fundador")
        acao = st.text_input("Ação recomendada", value="Simplificar entrada e testar demo com mais usuários.")
        obs_feedback = st.text_area("Observação do feedback", value="", height=80)

        if st.button("Salvar feedback beta"):
            salvar_feedback({
                "nome": nome_feedback, "perfil": perfil_feedback, "o_que_entendeu": entendeu,
                "maior_valor": maior_valor, "maior_confusao": confusao, "usaria": usaria,
                "pagaria": pagaria, "preco_sugerido": preco, "nota_geral": nota,
                "responsavel": responsavel_feedback, "acao_recomendada": acao, "observacao": obs_feedback,
            })
            st.success("Feedback beta registrado.")
            st.rerun()

        feedbacks = carregar_feedbacks()
        if feedbacks:
            st.markdown("### Feedbacks registrados")
            st.dataframe(feedbacks, use_container_width=True, hide_index=True)

    with tab5:
        st.markdown("### Relatórios")
        col_r1, col_r2 = st.columns(2)
        if col_r1.button("Salvar relatório beta"):
            caminho = salvar_relatorio_beta()
            st.success(f"Relatório salvo em {caminho}")
        if col_r2.button("Salvar manifesto beta"):
            caminho = salvar_manifesto_beta()
            st.success(f"Manifesto salvo em {caminho}")
        st.download_button(
            "Baixar relatório beta (.md)",
            data=gerar_relatorio_beta_markdown(),
            file_name="RELATORIO_BETA_USUARIOS_VALORIS.md",
            mime="text/markdown",
        )
        st.markdown("### Diagnóstico detalhado")
        st.json(metricas)


def executar_autoteste_beta_primeiros_usuarios_valoris() -> Dict[str, Any]:
    return {
        "ok": True,
        "versao": VERSAO_BETA_USUARIOS_VALORIS,
        "metricas": calcular_metricas_beta_usuarios(),
    }
