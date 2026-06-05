# gateway_dados_valoris.py

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

import streamlit as st

from camada_dados_valoris import DDL_POSTGRES_INICIAL, calcular_saude_dados_valoris


# ============================================================
# VALORIS
# v3.8.57 — Gateway de Dados e Contratos de Tabelas
# ------------------------------------------------------------
# Primeira camada prática para separar interface, CSV e futuro
# banco de dados. A regra daqui para frente é: módulos novos
# devem ler e gravar dados por contrato, não diretamente no CSV.
# ============================================================

VERSAO_GATEWAY_DADOS_VALORIS = "3.8.57"

CAMINHO_DECISOES_GATEWAY = Path("decisoes_gateway_dados_valoris.csv")
CAMINHO_LOG_GATEWAY = Path("logs_gateway_dados_valoris.csv")
CAMINHO_MANIFESTO_GATEWAY = Path("manifesto_gateway_dados_valoris.json")

CAMPOS_DECISOES_GATEWAY = [
    "id", "data_registro", "score_gateway", "tabelas_mapeadas",
    "contratos_validos", "decisao", "proximo_passo", "observacoes",
]

CAMPOS_LOG_GATEWAY = [
    "id", "data_registro", "operacao", "tabela_logica", "arquivo", "status", "detalhe",
]

CONTRATOS_TABELAS_VALORIS: Dict[str, Dict[str, Any]] = {
    "leads": {
        "arquivo_csv": "lista_espera_beta.csv",
        "criticidade": "Alta",
        "futura_tabela": "leads",
        "descricao": "Leads, dores, interesse e disposição de pagamento.",
        "campos_minimos": [
            "id", "data_criacao", "nome", "contato", "perfil", "principal_dor",
            "plano_interesse", "preco_aceitavel", "pagaria_agora", "comentario",
        ],
    },
    "events": {
        "arquivo_csv": "eventos_publicos_valoris.csv",
        "criticidade": "Média",
        "futura_tabela": "events",
        "descricao": "Eventos públicos e comportamento da jornada.",
        "campos_minimos": [
            "id", "data_evento", "sessao_id", "evento", "origem", "contexto",
            "perfil", "valor", "detalhe",
        ],
    },
    "validations": {
        "arquivo_csv": "validacoes_manuais_valoris.csv",
        "criticidade": "Alta",
        "futura_tabela": "founders",
        "descricao": "Validações manuais, objeções, intenção e próximos passos.",
        "campos_minimos": [
            "id", "data_registro", "nome", "contato", "origem", "perfil", "dor",
            "oferta_testada", "preco_testado", "canal", "status", "intencao",
            "objecao", "resposta_manual", "proximo_passo", "prioridade", "observacoes",
        ],
    },
    "founders": {
        "arquivo_csv": "fundadores_valoris.csv",
        "criticidade": "Alta",
        "futura_tabela": "founders",
        "descricao": "Usuários fundadores, pagamento manual, acesso, onboarding e feedback.",
        "campos_minimos": [
            "id", "data_registro", "nome", "contato", "origem", "perfil",
            "dor_principal", "plano", "valor_combinado", "status_pagamento",
            "status_acesso", "etapa_onboarding", "uso_inicial", "feedback_principal",
            "risco_churn", "nivel_entusiasmo", "proximo_passo", "observacoes",
        ],
    },
    "maturity_decisions": {
        "arquivo_csv": "decisoes_maturidade_valoris.csv",
        "criticidade": "Baixa",
        "futura_tabela": "events",
        "descricao": "Decisões de maturidade do produto.",
        "campos_minimos": [
            "id", "data_registro", "score_produto", "score_ativacao", "score_conversao",
            "score_operacao", "score_tecnico", "classificacao", "decisao_recomendada",
            "proximo_passo", "observacoes",
        ],
    },
    "architecture_decisions": {
        "arquivo_csv": "decisoes_arquitetura_valoris.csv",
        "criticidade": "Baixa",
        "futura_tabela": "events",
        "descricao": "Decisões técnicas e arquitetura.",
        "campos_minimos": [
            "id", "data_registro", "estagio_recomendado", "stack_recomendada",
            "risco_principal", "prioridade_tecnica", "proximo_passo", "observacoes",
        ],
    },
    "data_decisions": {
        "arquivo_csv": "decisoes_dados_valoris.csv",
        "criticidade": "Baixa",
        "futura_tabela": "events",
        "descricao": "Decisões da camada de dados.",
        "campos_minimos": [
            "id", "data_registro", "score_dados", "arquivos_detectados", "linhas_totais",
            "arquivos_criticos_ausentes", "decisao", "proximo_passo", "observacoes",
        ],
    },
}


def _limpar_texto(valor: Any) -> str:
    return "" if valor is None else str(valor).strip()


def _garantir_csv(caminho: Path, campos: List[str]) -> None:
    if caminho.exists():
        return
    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        csv.DictWriter(arquivo, fieldnames=campos).writeheader()


def _cabecalho(caminho: Path) -> List[str]:
    if not caminho.exists():
        return []
    try:
        with caminho.open("r", newline="", encoding="utf-8") as arquivo:
            return next(csv.reader(arquivo), [])
    except Exception:
        return []


def _linhas(caminho: Path) -> int:
    if not caminho.exists():
        return 0
    try:
        with caminho.open("r", newline="", encoding="utf-8") as arquivo:
            return max(0, len(list(csv.reader(arquivo))) - 1)
    except Exception:
        return 0


def registrar_log_gateway(operacao: str, tabela_logica: str, arquivo: str, status: str, detalhe: str) -> None:
    try:
        _garantir_csv(CAMINHO_LOG_GATEWAY, CAMPOS_LOG_GATEWAY)
        with CAMINHO_LOG_GATEWAY.open("a", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=CAMPOS_LOG_GATEWAY).writerow({
                "id": str(uuid4())[:8],
                "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "operacao": _limpar_texto(operacao),
                "tabela_logica": _limpar_texto(tabela_logica),
                "arquivo": _limpar_texto(arquivo),
                "status": _limpar_texto(status),
                "detalhe": _limpar_texto(detalhe),
            })
    except Exception:
        return


def carregar_logs_gateway() -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_LOG_GATEWAY, CAMPOS_LOG_GATEWAY)
    with CAMINHO_LOG_GATEWAY.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def carregar_decisoes_gateway() -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_DECISOES_GATEWAY, CAMPOS_DECISOES_GATEWAY)
    with CAMINHO_DECISOES_GATEWAY.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def gerar_csv_decisoes_gateway() -> str:
    _garantir_csv(CAMINHO_DECISOES_GATEWAY, CAMPOS_DECISOES_GATEWAY)
    return CAMINHO_DECISOES_GATEWAY.read_text(encoding="utf-8")


def gerar_csv_logs_gateway() -> str:
    _garantir_csv(CAMINHO_LOG_GATEWAY, CAMPOS_LOG_GATEWAY)
    return CAMINHO_LOG_GATEWAY.read_text(encoding="utf-8")


def validar_contrato_tabela(tabela_logica: str) -> Dict[str, Any]:
    contrato = CONTRATOS_TABELAS_VALORIS.get(tabela_logica)
    if not contrato:
        return {"tabela_logica": tabela_logica, "status": "Contrato ausente", "campos_ausentes": [], "linhas": 0}

    caminho = Path(contrato["arquivo_csv"])
    cab = _cabecalho(caminho)
    ausentes = [campo for campo in contrato["campos_minimos"] if campo not in cab]

    if not caminho.exists():
        status = "Arquivo ausente"
    elif ausentes:
        status = "Contrato incompleto"
    else:
        status = "Contrato válido"

    return {
        "tabela_logica": tabela_logica,
        "arquivo_csv": contrato["arquivo_csv"],
        "criticidade": contrato["criticidade"],
        "futura_tabela": contrato["futura_tabela"],
        "descricao": contrato["descricao"],
        "campos_presentes": cab,
        "campos_ausentes": ausentes,
        "linhas": _linhas(caminho),
        "status": status,
        "existe_arquivo": caminho.exists(),
    }


def validar_todos_contratos() -> List[Dict[str, Any]]:
    return [validar_contrato_tabela(nome) for nome in CONTRATOS_TABELAS_VALORIS]


def carregar_tabela_logica(tabela_logica: str) -> List[Dict[str, str]]:
    validacao = validar_contrato_tabela(tabela_logica)
    caminho = Path(validacao.get("arquivo_csv", ""))
    if not caminho.exists():
        registrar_log_gateway("read", tabela_logica, str(caminho), "falha", "Arquivo ausente.")
        return []
    try:
        with caminho.open("r", newline="", encoding="utf-8") as f:
            registros = list(csv.DictReader(f))
        registrar_log_gateway("read", tabela_logica, str(caminho), "ok", f"{len(registros)} registro(s) carregado(s).")
        return registros
    except Exception as erro:
        registrar_log_gateway("read", tabela_logica, str(caminho), "erro", str(erro))
        return []


def adicionar_registro_tabela_logica(tabela_logica: str, registro: Dict[str, Any]) -> bool:
    contrato = CONTRATOS_TABELAS_VALORIS.get(tabela_logica)
    if not contrato:
        registrar_log_gateway("write", tabela_logica, "", "falha", "Contrato inexistente.")
        return False

    caminho = Path(contrato["arquivo_csv"])
    campos = contrato["campos_minimos"]
    _garantir_csv(caminho, campos)
    linha = {campo: _limpar_texto(registro.get(campo, "")) for campo in campos}
    linha["id"] = linha.get("id") or str(uuid4())[:8]
    for campo_data in ["data_registro", "data_criacao", "data_evento"]:
        if campo_data in campos and not linha.get(campo_data):
            linha[campo_data] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        with caminho.open("a", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=campos).writerow(linha)
        registrar_log_gateway("write", tabela_logica, contrato["arquivo_csv"], "ok", "Registro adicionado via gateway.")
        return True
    except Exception as erro:
        registrar_log_gateway("write", tabela_logica, contrato["arquivo_csv"], "erro", str(erro))
        return False


def calcular_saude_gateway() -> Dict[str, Any]:
    contratos = validar_todos_contratos()
    tabelas = len(contratos)
    validos = len([c for c in contratos if c["status"] == "Contrato válido"])
    incompletos = len([c for c in contratos if c["status"] == "Contrato incompleto"])
    ausentes = len([c for c in contratos if c["status"] == "Arquivo ausente"])
    linhas = sum(int(c["linhas"]) for c in contratos)

    score = 25 + min(tabelas * 5, 30) + min(validos * 7, 35) + min(linhas * 1.2, 18) - incompletos * 8 - ausentes * 4
    score = int(round(max(0, min(100, score))))

    if score >= 82:
        decisao = "Gateway pronto para primeira migração"
        proximo = "Criar adapters SQLite/PostgreSQL e substituir leituras diretas de CSV gradualmente."
    elif score >= 65:
        decisao = "Gateway funcional, ainda com ajustes"
        proximo = "Corrigir contratos incompletos e usar o gateway em módulos novos."
    elif score >= 45:
        decisao = "Gateway em preparação"
        proximo = "Manter CSV, validar contratos e registrar logs antes de migrar dados."
    else:
        decisao = "Pouca base para gateway"
        proximo = "Gerar mais dados reais e manter o app simples por enquanto."

    return {
        "contratos": contratos,
        "tabelas_mapeadas": tabelas,
        "contratos_validos": validos,
        "contratos_incompletos": incompletos,
        "arquivos_ausentes": ausentes,
        "linhas_totais": linhas,
        "score_gateway": score,
        "decisao": decisao,
        "proximo_passo": proximo,
    }


def salvar_decisao_gateway(saude: Dict[str, Any]) -> Dict[str, str]:
    _garantir_csv(CAMINHO_DECISOES_GATEWAY, CAMPOS_DECISOES_GATEWAY)
    registro = {
        "id": str(uuid4())[:8],
        "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score_gateway": str(saude["score_gateway"]),
        "tabelas_mapeadas": str(saude["tabelas_mapeadas"]),
        "contratos_validos": str(saude["contratos_validos"]),
        "decisao": saude["decisao"],
        "proximo_passo": saude["proximo_passo"],
        "observacoes": "Decisão gerada pelo Gateway de Dados.",
    }
    with CAMINHO_DECISOES_GATEWAY.open("a", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=CAMPOS_DECISOES_GATEWAY).writerow(registro)
    return registro


def gerar_manifesto_gateway() -> Dict[str, Any]:
    saude = calcular_saude_gateway()
    manifesto = {
        "versao": VERSAO_GATEWAY_DADOS_VALORIS,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score_gateway": saude["score_gateway"],
        "decisao": saude["decisao"],
        "proximo_passo": saude["proximo_passo"],
        "contratos": saude["contratos"],
    }
    CAMINHO_MANIFESTO_GATEWAY.write_text(json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8")
    registrar_log_gateway("manifest", "gateway", str(CAMINHO_MANIFESTO_GATEWAY), "ok", "Manifesto gerado.")
    return manifesto


def _gerar_markdown_gateway(saude: Dict[str, Any]) -> str:
    linhas = "\n".join(
        [
            f"| {c['tabela_logica']} | {c.get('arquivo_csv','')} | {c.get('criticidade','')} | {c['status']} | {c['linhas']} | {', '.join(c['campos_ausentes']) or '-'} |"
            for c in saude["contratos"]
        ]
    )
    return f"""# Gateway de Dados — Valoris

Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}

Score Gateway: {saude['score_gateway']}/100  
Decisão: {saude['decisao']}  
Próximo passo: {saude['proximo_passo']}

| Tabela lógica | Arquivo CSV | Criticidade | Status | Linhas | Campos ausentes |
|---|---|---|---|---:|---|
{linhas}

## Próxima arquitetura

1. CsvAdapter  
2. SQLiteAdapter  
3. PostgresAdapter  
4. Repositories  
5. FastAPI endpoints  

```sql
{DDL_POSTGRES_INICIAL}
```
"""


def _injetar_css_gateway() -> None:
    st.markdown(
        """
        <style>
            .gate-hero {
                padding: clamp(1.18rem, 3vw, 2rem);
                border-radius: 30px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    radial-gradient(circle at top left, rgba(214, 181, 109, 0.26), transparent 30%),
                    radial-gradient(circle at bottom right, rgba(74, 144, 226, 0.22), transparent 34%),
                    linear-gradient(135deg, rgba(8, 15, 27, 0.99), rgba(5, 9, 18, 0.99));
                box-shadow: 0 18px 58px rgba(0, 0, 0, 0.31);
                margin-bottom: 1rem;
            }
            .gate-eyebrow { color: #d6b56d; font-size: 0.74rem; letter-spacing: 0.14em; text-transform: uppercase; font-weight: 880; margin-bottom: 0.35rem; }
            .gate-title { color: #f4f7fb; font-size: clamp(1.75rem, 5.4vw, 3.1rem); font-weight: 950; line-height: 1.02; letter-spacing: -0.058em; margin-bottom: 0.55rem; }
            .gate-subtitle { color: rgba(244, 247, 251, 0.75); font-size: clamp(0.94rem, 2.2vw, 1.06rem); line-height: 1.56; max-width: 1020px; }
            .gate-note { padding: 0.92rem 0.98rem; border-radius: 17px; border-left: 4px solid #d6b56d; background: rgba(214, 181, 109, 0.08); color: rgba(244, 247, 251, 0.82); font-size: 0.90rem; line-height: 1.55; margin: 0.85rem 0; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def renderizar_gateway_dados_valoris() -> None:
    _injetar_css_gateway()
    st.markdown(
        f"""
        <div class="gate-hero">
            <div class="gate-eyebrow">Valoris • Gateway de Dados • v{VERSAO_GATEWAY_DADOS_VALORIS}</div>
            <div class="gate-title">Separe os dados da interface.</div>
            <div class="gate-subtitle">O Gateway cria contratos de tabelas e padroniza leitura/escrita. É o primeiro passo real para trocar CSV por banco sem desmontar a Valoris.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    saude = calcular_saude_gateway()

    col_1, col_2, col_3, col_4 = st.columns(4)
    with col_1:
        st.metric("Score gateway", f"{saude['score_gateway']}/100")
    with col_2:
        st.metric("Tabelas", saude["tabelas_mapeadas"])
    with col_3:
        st.metric("Contratos válidos", saude["contratos_validos"])
    with col_4:
        st.metric("Linhas", saude["linhas_totais"])

    st.progress(saude["score_gateway"] / 100)
    st.info(f"**{saude['decisao']}** — {saude['proximo_passo']}")

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Gerar manifesto do gateway", key="gerar_manifesto_gateway_valoris"):
            manifesto = gerar_manifesto_gateway()
            st.success(f"Manifesto gerado com {len(manifesto['contratos'])} contrato(s).")
    with col_b:
        if st.button("Salvar decisão do gateway", key="salvar_decisao_gateway_valoris"):
            registro = salvar_decisao_gateway(saude)
            st.success(f"Decisão salva: {registro['decisao']}")
            st.rerun()

    st.download_button(
        "Baixar relatório do gateway (.md)",
        data=_gerar_markdown_gateway(saude),
        file_name="gateway_dados_valoris.md",
        mime="text/markdown",
        key="download_gateway_dados_valoris",
    )
    st.download_button(
        "Baixar decisões do gateway (.csv)",
        data=gerar_csv_decisoes_gateway(),
        file_name="decisoes_gateway_dados_valoris.csv",
        mime="text/csv",
        key="download_decisoes_gateway_dados_valoris",
    )
    st.download_button(
        "Baixar logs do gateway (.csv)",
        data=gerar_csv_logs_gateway(),
        file_name="logs_gateway_dados_valoris.csv",
        mime="text/csv",
        key="download_logs_gateway_dados_valoris",
    )

    st.divider()
    st.markdown("### Contratos de tabelas")
    for item in saude["contratos"]:
        with st.container(border=True):
            st.markdown(f"**{item['tabela_logica']}** — {item['status']}")
            st.caption(f"CSV: {item.get('arquivo_csv','')} • Criticidade: {item.get('criticidade','')} • Futuro: {item.get('futura_tabela','')}")
            st.markdown(item.get("descricao", ""))
            st.markdown(f"Linhas: **{item['linhas']}** • Campos ausentes: **{len(item['campos_ausentes'])}**")
            if item["campos_ausentes"]:
                st.warning(", ".join(item["campos_ausentes"]))
            if item["campos_presentes"]:
                with st.expander("Ver campos presentes", expanded=False):
                    st.code(", ".join(item["campos_presentes"]), language="text")

    st.divider()
    st.markdown("### Teste controlado do gateway")
    tabela = st.selectbox(
        "Tabela lógica para teste",
        list(CONTRATOS_TABELAS_VALORIS.keys()),
        index=list(CONTRATOS_TABELAS_VALORIS.keys()).index("data_decisions"),
        key="gateway_tabela_teste",
    )
    if st.button("Ler tabela via gateway", key="gateway_ler_tabela"):
        registros = carregar_tabela_logica(tabela)
        st.success(f"{len(registros)} registro(s) carregado(s) via gateway.")
        if registros:
            st.json(registros[:3])

    st.divider()
    st.markdown("### Logs do gateway")
    logs = carregar_logs_gateway()
    if not logs:
        st.info("Ainda não há logs do gateway.")
    for item in reversed(logs[-20:]):
        with st.container(border=True):
            st.markdown(f"**{item.get('operacao','N/D')}** — {item.get('status','N/D')}")
            st.caption(f"{item.get('data_registro','N/D')} • {item.get('tabela_logica','N/D')} • {item.get('arquivo','N/D')}")
            st.markdown(item.get("detalhe", ""))

    st.markdown(
        """
        <div class="gate-note">
            <strong>Regra do gateway:</strong> módulos novos devem ler e gravar dados por contrato. Isso prepara banco e API sem quebrar o MVP atual.
        </div>
        """,
        unsafe_allow_html=True,
    )


def executar_autoteste_gateway_dados_valoris() -> List[Dict[str, str]]:
    saude = calcular_saude_gateway()
    contrato = validar_contrato_tabela("leads")
    return [
        {"teste": "versao_gateway", "status": "OK" if VERSAO_GATEWAY_DADOS_VALORIS == "3.8.57" else "FALHA", "detalhe": VERSAO_GATEWAY_DADOS_VALORIS},
        {"teste": "contratos", "status": "OK" if len(CONTRATOS_TABELAS_VALORIS) >= 5 else "FALHA", "detalhe": str(len(CONTRATOS_TABELAS_VALORIS))},
        {"teste": "score_gateway", "status": "OK" if 0 <= saude["score_gateway"] <= 100 else "FALHA", "detalhe": str(saude["score_gateway"])},
        {"teste": "contrato_leads", "status": "OK" if contrato["status"] != "Contrato ausente" else "FALHA", "detalhe": contrato["status"]},
    ]
