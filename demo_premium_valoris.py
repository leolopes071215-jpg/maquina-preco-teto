# demo_premium_valoris.py
# Valoris — Demo Premium com Dados Exemplo v3.13.2
# ------------------------------------------------------------
# Cria uma demonstração curta, clara e vendável do Valoris usando dados exemplo isolados.
# Não altera dados reais, não toma decisões financeiras e não envia mensagens automaticamente.

from __future__ import annotations

import csv
import json
from collections import deque
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st


VERSAO_DEMO_PREMIUM_VALORIS = "3.13.2"
PASTA_DEMO = Path("demo_premium_valoris")
CAMINHO_REVISOES = Path("revisoes_demo_premium_valoris.csv")
CAMINHO_RELATORIO = Path("RELATORIO_DEMO_PREMIUM_VALORIS.md")
CAMINHO_MANIFESTO = Path("manifesto_demo_premium_valoris.json")

CAMPOS_REVISOES = [
    "data_hora", "perfil_demo", "score_demo", "clareza", "valor_percebido",
    "responsavel", "decisao", "proximo_passo", "observacao",
]

PERFIS_DEMO: Dict[str, Dict[str, str]] = {
    "Investidor Beta": {
        "publico": "Pessoa que quer decidir melhor onde aportar",
        "dor": "Análises espalhadas, decisões emocionais e falta de acompanhamento.",
        "promessa": "Transformar uma tese de investimento em decisão acompanhável.",
        "tom": "Didático, claro e prático.",
    },
    "Investidor Fundamentalista": {
        "publico": "Usuário que já analisa empresas, FIIs ou ETFs",
        "dor": "Tem dados, mas falta método para transformar análise em decisão e revisão.",
        "promessa": "Unir valuation, tese, pipeline e revisão em um fluxo único.",
        "tom": "Técnico, cético e objetivo.",
    },
    "Fundador / Produto": {
        "publico": "Pessoa avaliando o Valoris como produto ou beta",
        "dor": "Produto poderoso, mas precisa parecer simples e validável.",
        "promessa": "Mostrar a experiência completa em poucos minutos.",
        "tom": "Executivo, estratégico e premium.",
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
            return list(deque(csv.DictReader(arquivo), maxlen=1000))
    except Exception:
        return []


def salvar_revisao_demo(perfil_demo: str, score_demo: int, clareza: int, valor_percebido: int, responsavel: str, decisao: str, proximo_passo: str, observacao: str = "") -> Path:
    _garantir_csv(CAMINHO_REVISOES, CAMPOS_REVISOES)
    with CAMINHO_REVISOES.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_REVISOES)
        escritor.writerow({
            "data_hora": _agora_iso(),
            "perfil_demo": _txt(perfil_demo),
            "score_demo": _int(score_demo),
            "clareza": _int(clareza),
            "valor_percebido": _int(valor_percebido),
            "responsavel": _txt(responsavel),
            "decisao": _txt(decisao),
            "proximo_passo": _txt(proximo_passo),
            "observacao": _txt(observacao),
        })
    return CAMINHO_REVISOES


def dados_demo_analises() -> List[Dict[str, Any]]:
    return [
        {"ticker": "WEGE3", "empresa": "WEG", "classe": "Ação", "preco_atual": 38.50, "preco_teto": 32.00, "margem_seguranca": -16.9, "qualidade": 88, "risco": 32, "decisao": "Aguardar preço melhor", "tese": "Empresa excelente, mas valuation exige disciplina."},
        {"ticker": "ITUB4", "empresa": "Itaú Unibanco", "classe": "Ação", "preco_atual": 34.20, "preco_teto": 36.80, "margem_seguranca": 7.6, "qualidade": 84, "risco": 38, "decisao": "Compra moderada", "tese": "Banco resiliente, rentabilidade forte e risco controlado."},
        {"ticker": "XPLG11", "empresa": "XP Log", "classe": "FII", "preco_atual": 101.40, "preco_teto": 106.00, "margem_seguranca": 4.5, "qualidade": 76, "risco": 45, "decisao": "Acompanhar com atenção", "tese": "Logística interessante, mas exige acompanhar vacância e revisão."},
    ]


def dados_demo_pipeline() -> List[Dict[str, Any]]:
    hoje = datetime.now().date()
    return [
        {"ticker": "WEGE3", "etapa": "Watchlist", "acao": "Aguardar margem de segurança mínima de 15%", "prioridade": "Média", "prazo": str(hoje + timedelta(days=30)), "status": "Aberta"},
        {"ticker": "ITUB4", "etapa": "Decisão", "acao": "Simular aporte inicial e acompanhar resultado trimestral", "prioridade": "Alta", "prazo": str(hoje + timedelta(days=7)), "status": "Aberta"},
        {"ticker": "XPLG11", "etapa": "Revisão", "acao": "Revisar relatório gerencial e risco de vacância", "prioridade": "Média/Alta", "prazo": str(hoje + timedelta(days=15)), "status": "Aberta"},
    ]


def dados_demo_comunicacao() -> List[Dict[str, Any]]:
    return [
        {"canal": "Resumo Executivo", "ticker": "ITUB4", "tipo": "Decisão de aporte", "status": "Respondido", "mensagem": "Ativo com margem positiva e qualidade alta. Próximo passo: simular aporte moderado.", "resultado": "Usuário confirmou interesse em aprofundar tese."},
        {"canal": "E-mail", "ticker": "WEGE3", "tipo": "Alerta de valuation", "status": "Sem resposta", "mensagem": "Empresa excelente, porém acima do preço teto conservador.", "resultado": "Aguardar nova revisão."},
        {"canal": "Calendário", "ticker": "XPLG11", "tipo": "Revisão futura", "status": "Demanda retorno", "mensagem": "Agendar revisão de relatório gerencial e vacância.", "resultado": "Criar alerta para próxima revisão."},
    ]


def roteiro_demo(perfil: str) -> List[Dict[str, str]]:
    return [
        {"minuto": "0:00–0:40", "etapa": "Abertura", "fala": "O Valoris não é só uma calculadora. Ele transforma análise em decisão acompanhável.", "pagina": "Jornada Beta"},
        {"minuto": "0:40–1:30", "etapa": "Análise", "fala": "Vemos preço teto, margem de segurança, qualidade, risco e decisão sugerida.", "pagina": "Motor Análise Ativos / Análise Principal"},
        {"minuto": "1:30–2:20", "etapa": "Pipeline", "fala": "A decisão vira ação, prazo, prioridade e acompanhamento.", "pagina": "Pipeline Principal"},
        {"minuto": "2:20–3:10", "etapa": "Alertas", "fala": "O sistema mostra o que precisa ser revisado, tratado ou acompanhado.", "pagina": "Radar Principal / Agenda Revisões"},
        {"minuto": "3:10–4:10", "etapa": "Comunicação", "fala": "O Valoris gera rascunhos, aprova, exporta e registra envio manual com rastreabilidade.", "pagina": "Cockpit Comunicação"},
        {"minuto": "4:10–5:00", "etapa": "Fechamento", "fala": "No cockpit final, o usuário sabe o que foi feito, o que falta e qual próximo passo executar.", "pagina": "Cockpit Principal / Demo Premium"},
    ]


def calcular_metricas_demo(perfil: str) -> Dict[str, Any]:
    analises = dados_demo_analises()
    pipeline = dados_demo_pipeline()
    comunicacao = dados_demo_comunicacao()
    revisoes = carregar_revisoes()
    ativos = len({item["ticker"] for item in analises})
    decisoes = len([item for item in analises if item.get("decisao")])
    respondidos = len([item for item in comunicacao if item.get("status") == "Respondido"])
    retornos = len([item for item in comunicacao if item.get("status") == "Demanda retorno"])
    score = 50 + min(ativos * 5, 15) + min(decisoes * 5, 15) + min(len(pipeline) * 5, 15) + min(len(comunicacao) * 4, 12) + 8
    if revisoes:
        score += 8
    score = max(0, min(100, int(score)))
    if score >= 85:
        maturidade = "Demo premium pronta"
        risco = "Baixo"
        decisao = "Demo clara para apresentação beta"
        proximo = "Testar a demo em 5 minutos com uma pessoa real."
    elif score >= 70:
        maturidade = "Demo funcional"
        risco = "Baixo/Médio"
        decisao = "Demo utilizável, mas ainda pode ficar mais convincente"
        proximo = "Salvar revisão e ajustar narrativa de venda."
    else:
        maturidade = "Demo inicial"
        risco = "Médio"
        decisao = "Demo precisa de mais clareza antes de apresentar"
        proximo = "Gerar pacote demo e revisar roteiro."
    return {"versao": VERSAO_DEMO_PREMIUM_VALORIS, "gerado_em": _agora_iso(), "perfil_demo": perfil, "score_demo": score, "maturidade": maturidade, "ativos": ativos, "decisoes": decisoes, "acoes_pipeline": len(pipeline), "comunicacoes": len(comunicacao), "respondidos": respondidos, "retornos": retornos, "passos_roteiro": len(roteiro_demo(perfil)), "revisoes": len(revisoes), "risco": risco, "decisao": decisao, "proximo_passo": proximo}


def salvar_csv_demo(nome: str, dados: List[Dict[str, Any]]) -> Path:
    PASTA_DEMO.mkdir(exist_ok=True)
    caminho = PASTA_DEMO / nome
    if not dados:
        caminho.write_text("", encoding="utf-8")
        return caminho
    campos = list(dados[0].keys())
    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()
        for item in dados:
            escritor.writerow(item)
    return caminho


def gerar_relatorio_demo_markdown(perfil: str) -> str:
    metricas = calcular_metricas_demo(perfil)
    info = PERFIS_DEMO[perfil]
    linhas_roteiro = "\n".join([f"- **{item['minuto']} — {item['etapa']}**: {item['fala']} Página: {item['pagina']}." for item in roteiro_demo(perfil)])
    linhas_analises = "\n".join([f"- **{item['ticker']} — {item['empresa']}**: preço atual R$ {item['preco_atual']:.2f}, preço teto R$ {item['preco_teto']:.2f}, margem {item['margem_seguranca']}%, decisão: {item['decisao']}." for item in dados_demo_analises()])
    linhas_pipeline = "\n".join([f"- **{item['ticker']} — {item['etapa']} — {item['prioridade']}**: {item['acao']} Prazo: {item['prazo']}." for item in dados_demo_pipeline()])
    linhas_comunicacao = "\n".join([f"- **{item['canal']} — {item['ticker']} — {item['status']}**: {item['mensagem']} Resultado: {item['resultado']}" for item in dados_demo_comunicacao()])
    return f"""# Demo Premium — Valoris

Versão: {VERSAO_DEMO_PREMIUM_VALORIS}  
Gerado em: {_agora_iso()}  
Perfil da demo: {perfil}

## Persona

Público: {info['publico']}  
Dor: {info['dor']}  
Promessa: {info['promessa']}  
Tom: {info['tom']}

## Diagnóstico

Score demo: {metricas['score_demo']}/100  
Maturidade: {metricas['maturidade']}  
Ativos exemplo: {metricas['ativos']}  
Decisões: {metricas['decisoes']}  
Ações no pipeline: {metricas['acoes_pipeline']}  
Comunicações: {metricas['comunicacoes']}  
Respondidos: {metricas['respondidos']}  
Retornos: {metricas['retornos']}  

Risco: {metricas['risco']}  
Decisão: {metricas['decisao']}  
Próximo passo: {metricas['proximo_passo']}

## Demonstração em 5 minutos

{linhas_roteiro}

## Ativos exemplo

{linhas_analises}

## Pipeline exemplo

{linhas_pipeline}

## Comunicação exemplo

{linhas_comunicacao}

## Estratégia

Esta demo usa dados isolados para mostrar o valor do Valoris sem depender da base real do usuário. A proposta é vender clareza: análise, decisão, acompanhamento, comunicação e resultado em uma jornada única.
"""


def salvar_pacote_demo(perfil: str) -> Dict[str, str]:
    PASTA_DEMO.mkdir(exist_ok=True)
    caminhos = {
        "analises": salvar_csv_demo("demo_analises_valoris.csv", dados_demo_analises()),
        "pipeline": salvar_csv_demo("demo_pipeline_valoris.csv", dados_demo_pipeline()),
        "comunicacao": salvar_csv_demo("demo_comunicacao_valoris.csv", dados_demo_comunicacao()),
        "roteiro": salvar_csv_demo("demo_roteiro_valoris.csv", roteiro_demo(perfil)),
    }
    relatorio_demo = PASTA_DEMO / "DEMO_PREMIUM_VALORIS.md"
    relatorio_demo.write_text(gerar_relatorio_demo_markdown(perfil), encoding="utf-8")
    caminhos["relatorio_demo"] = relatorio_demo
    manifesto_demo = PASTA_DEMO / "manifesto_demo_premium_valoris.json"
    manifesto_demo.write_text(json.dumps({"produto": "Valoris", "versao": VERSAO_DEMO_PREMIUM_VALORIS, "perfil": perfil, "metricas": calcular_metricas_demo(perfil), "analises": dados_demo_analises(), "pipeline": dados_demo_pipeline(), "comunicacao": dados_demo_comunicacao(), "roteiro": roteiro_demo(perfil), "principio": "demonstração boa vende clareza antes de vender complexidade"}, ensure_ascii=False, indent=2), encoding="utf-8")
    caminhos["manifesto_demo"] = manifesto_demo
    return {nome: str(caminho) for nome, caminho in caminhos.items()}


def salvar_relatorio_demo(perfil: str) -> Path:
    CAMINHO_RELATORIO.write_text(gerar_relatorio_demo_markdown(perfil), encoding="utf-8")
    return CAMINHO_RELATORIO


def gerar_manifesto_demo(perfil: str) -> Dict[str, Any]:
    return {"produto": "Valoris", "versao": VERSAO_DEMO_PREMIUM_VALORIS, "modulo": "demo_premium_valoris", "data_hora": _agora_iso(), "perfil": perfil, "metricas": calcular_metricas_demo(perfil), "dados_demo": {"analises": dados_demo_analises(), "pipeline": dados_demo_pipeline(), "comunicacao": dados_demo_comunicacao(), "roteiro": roteiro_demo(perfil)}, "revisoes": carregar_revisoes(), "principio": "uma demo premium deve explicar o valor em poucos minutos", "proxima_etapa": "checklist de produto vendável"}


def salvar_manifesto_demo(perfil: str) -> Path:
    CAMINHO_MANIFESTO.write_text(json.dumps(gerar_manifesto_demo(perfil), ensure_ascii=False, indent=2), encoding="utf-8")
    return CAMINHO_MANIFESTO


def renderizar_demo_premium_valoris() -> None:
    st.subheader("Demo Premium")
    st.caption("Demonstração com dados exemplo isolados para apresentar o valor do Valoris em poucos minutos.")
    perfil = st.selectbox("Perfil da demo", list(PERFIS_DEMO.keys()))
    info = PERFIS_DEMO[perfil]
    metricas = calcular_metricas_demo(perfil)
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Score demo", f"{metricas['score_demo']}/100")
    col2.metric("Maturidade", metricas["maturidade"])
    col3.metric("Ativos", metricas["ativos"])
    col4.metric("Pipeline", metricas["acoes_pipeline"])
    col5.metric("Comunicações", metricas["comunicacoes"])
    if metricas["risco"] == "Médio":
        st.warning(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    elif metricas["risco"] == "Baixo":
        st.success(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    else:
        st.info(f"{metricas['decisao']} — {metricas['proximo_passo']}")
    st.markdown(f"""
### Persona da demonstração

**Público:** {info['publico']}  
**Dor:** {info['dor']}  
**Promessa:** {info['promessa']}  
**Tom:** {info['tom']}
""")
    st.divider()
    st.markdown("### Roteiro de demo em 5 minutos")
    st.dataframe(roteiro_demo(perfil), use_container_width=True, hide_index=True)
    st.divider()
    tab1, tab2, tab3 = st.tabs(["Ativos exemplo", "Pipeline exemplo", "Comunicação exemplo"])
    with tab1:
        st.dataframe(dados_demo_analises(), use_container_width=True, hide_index=True)
    with tab2:
        st.dataframe(dados_demo_pipeline(), use_container_width=True, hide_index=True)
    with tab3:
        st.dataframe(dados_demo_comunicacao(), use_container_width=True, hide_index=True)
    st.divider()
    st.markdown("### Gerar pacote demo isolado")
    col_p1, col_p2 = st.columns(2)
    if col_p1.button("Gerar pacote demo local"):
        caminhos = salvar_pacote_demo(perfil)
        st.success("Pacote demo gerado em pasta isolada.")
        st.json(caminhos)
    if col_p2.button("Salvar relatório da demo"):
        caminho = salvar_relatorio_demo(perfil)
        st.success(f"Relatório salvo em {caminho}")
    st.download_button("Baixar relatório da demo (.md)", data=gerar_relatorio_demo_markdown(perfil), file_name="RELATORIO_DEMO_PREMIUM_VALORIS.md", mime="text/markdown")
    st.divider()
    st.markdown("### Registrar revisão da demo")
    col_r1, col_r2 = st.columns(2)
    clareza = col_r1.slider("Clareza da demo", min_value=0, max_value=10, value=8)
    valor = col_r2.slider("Valor percebido", min_value=0, max_value=10, value=8)
    responsavel = st.text_input("Responsável", value="Fundador")
    decisao = st.text_input("Decisão", value="Demo premium pronta para teste curto.")
    proximo = st.text_input("Próximo passo", value="Apresentar a demo para uma pessoa real e observar dúvidas.")
    observacao = st.text_area("Observação", value=f"Revisão registrada na Demo Premium v{VERSAO_DEMO_PREMIUM_VALORIS}.", height=90)
    if st.button("Salvar revisão da demo"):
        salvar_revisao_demo(perfil_demo=perfil, score_demo=metricas["score_demo"], clareza=clareza, valor_percebido=valor, responsavel=responsavel, decisao=decisao, proximo_passo=proximo, observacao=observacao)
        st.success("Revisão da demo registrada.")
        st.rerun()
    revisoes = carregar_revisoes()
    if revisoes:
        st.markdown("### Revisões registradas")
        st.dataframe(revisoes, use_container_width=True, hide_index=True)
    st.divider()
    st.markdown("### Manifesto")
    if st.button("Salvar manifesto da demo"):
        caminho = salvar_manifesto_demo(perfil)
        st.success(f"Manifesto salvo em {caminho}")


def executar_autoteste_demo_premium_valoris() -> Dict[str, Any]:
    perfil = "Investidor Beta"
    return {"ok": True, "versao": VERSAO_DEMO_PREMIUM_VALORIS, "metricas": calcular_metricas_demo(perfil)}
