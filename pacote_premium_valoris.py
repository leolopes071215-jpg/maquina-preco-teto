# pacote_premium_valoris.py

from __future__ import annotations

import csv
import json
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

import streamlit as st


VERSAO_PACOTE_PREMIUM_VALORIS = "3.8.88"

CAMINHO_DECISOES_PACOTE = Path("decisoes_pacote_premium_valoris.csv")
CAMINHO_MANIFESTO_PACOTE = Path("manifesto_pacote_premium_valoris.json")
CAMINHO_PACOTE_MD = Path("PACOTE_PREMIUM_VALORIS.md")
CAMINHO_SUMARIO_MD = Path("SUMARIO_EXECUTIVO_PACOTE_PREMIUM_VALORIS.md")
CAMINHO_PLAYBOOK_MD = Path("PLAYBOOK_PACOTE_PREMIUM_VALORIS.md")
CAMINHO_CHECKLIST_MD = Path("CHECKLIST_PACOTE_PREMIUM_VALORIS.md")
CAMINHO_ZIP = Path("pacote_premium_valoris.zip")

CAMPOS_DECISAO = [
    "id", "data_registro", "score_pacote", "score_relatorio", "score_comparador",
    "score_watchlist", "score_entrega", "ticker_base", "empresa_base", "artefatos_total",
    "risco", "decisao", "proximo_passo", "observacoes",
]

ARTEFATOS_PACOTE = [
    {"nome": "Dossiê Premium v2", "arquivo": "DOSSIE_PREMIUM_V2_VALORIS.md", "peso": 32},
    {"nome": "Sumário executivo", "arquivo": "SUMARIO_EXECUTIVO_PACOTE_PREMIUM_VALORIS.md", "peso": 18},
    {"nome": "Relatório Watchlist", "arquivo": "RELATORIO_WATCHLIST_FUNDADORES_VALORIS.md", "peso": 16},
    {"nome": "Relatório Comparador", "arquivo": "RELATORIO_COMPARADOR_SETORIAL_VALORIS.md", "peso": 18},
    {"nome": "Checklist de entrega", "arquivo": "CHECKLIST_PACOTE_PREMIUM_VALORIS.md", "peso": 16},
]

PLAYBOOK_PACOTE = [
    {"etapa": "Escolher ativo central", "acao": "Usar o ativo base do dossiê ou o melhor ranqueado no comparador."},
    {"etapa": "Gerar dossiê", "acao": "Gerar tese, risco, preço teto, perguntas críticas e plano de acompanhamento."},
    {"etapa": "Anexar contexto", "acao": "Adicionar watchlist, comparador setorial e sumário executivo."},
    {"etapa": "Checar completude", "acao": "Validar se os artefatos essenciais existem e se o ativo base está definido."},
    {"etapa": "Coletar feedback", "acao": "Pedir nota de clareza, utilidade e percepção de valor premium."},
]

CHECKLIST_PACOTE = [
    "Dossiê Premium v2 gerado",
    "Ativo base definido",
    "Tese e risco presentes",
    "Preço teto e margem presentes",
    "Perguntas críticas presentes",
    "Plano de acompanhamento presente",
    "Watchlist anexada",
    "Comparador setorial anexado",
    "Sumário executivo gerado",
    "Playbook de entrega gerado",
    "Checklist de entrega gerado",
    "ZIP opcional gerado",
]


def _limpar_texto(valor: Any) -> str:
    return "" if valor is None else str(valor).strip()


def _garantir_csv(caminho: Path, campos: List[str]) -> None:
    if caminho.exists():
        return
    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()


def _try_call(module_name: str, function_name: str, *args: Any, fallback: Any = None) -> Any:
    try:
        modulo = __import__(module_name, fromlist=[function_name])
        funcao = getattr(modulo, function_name)
        return funcao(*args)
    except Exception:
        return fallback


def _selecionar_ticker_padrao() -> str:
    ativo = _try_call("relatorio_premium_v2_valoris", "selecionar_ativo_base_relatorio", fallback={}) or {}
    return _limpar_texto(ativo.get("ticker"))


def _calcular_saudes(ticker: str = "") -> Dict[str, Dict[str, Any]]:
    relatorio = _try_call(
        "relatorio_premium_v2_valoris",
        "calcular_saude_relatorio_premium_v2",
        ticker,
        fallback={"score_relatorio_v2": 0, "ticker_base": "PENDENTE", "empresa_base": ""},
    ) or {}
    comparador = _try_call(
        "comparador_setorial_valoris",
        "calcular_saude_comparador_setorial",
        fallback={"score_comparador": 0},
    ) or {}
    watchlist = _try_call(
        "watchlist_fundadores_valoris",
        "calcular_saude_watchlist_fundadores",
        fallback={"score_watchlist": 0},
    ) or {}
    return {"relatorio": relatorio, "comparador": comparador, "watchlist": watchlist}


def calcular_saude_pacote_premium(ticker: str = "") -> Dict[str, Any]:
    ticker = _limpar_texto(ticker).upper() or _selecionar_ticker_padrao()
    saudes = _calcular_saudes(ticker)

    relatorio = saudes["relatorio"]
    comparador = saudes["comparador"]
    watchlist = saudes["watchlist"]

    score_relatorio = int(relatorio.get("score_relatorio_v2", 0) or 0)
    score_comparador = int(comparador.get("score_comparador", 0) or 0)
    score_watchlist = int(watchlist.get("score_watchlist", 0) or 0)

    ticker_base = _limpar_texto(relatorio.get("ticker_base", ticker or "PENDENTE")) or "PENDENTE"
    empresa_base = _limpar_texto(relatorio.get("empresa_base", ""))

    score_entrega = 0
    score_entrega += 25 if ticker_base != "PENDENTE" else 0
    score_entrega += 25 if empresa_base else 0
    score_entrega += 20 if len(ARTEFATOS_PACOTE) >= 5 else 0
    score_entrega += 15 if len(PLAYBOOK_PACOTE) >= 5 else 0
    score_entrega += 15 if len(CHECKLIST_PACOTE) >= 12 else 0
    score_entrega = min(100, score_entrega)

    score_pacote = int(round(
        score_relatorio * 0.38
        + score_comparador * 0.22
        + score_watchlist * 0.20
        + score_entrega * 0.20
    ))

    if ticker_base == "PENDENTE" or not empresa_base:
        risco = "Alto"
        decisao = "Pacote ainda sem ativo principal"
        proximo_passo = "Registrar ativo na watchlist, gerar ranking e depois criar o pacote premium."
    elif score_pacote >= 82:
        risco = "Médio controlado"
        decisao = "Pacote premium pronto para entrega assistida"
        proximo_passo = "Enviar para fundador, pedir feedback e medir percepção de valor."
    elif score_pacote >= 65:
        risco = "Médio"
        decisao = "Pacote utilizável, mas ainda pode parecer incompleto"
        proximo_passo = "Fortalecer dossiê, comparador ou watchlist antes de usar como material comercial."
    else:
        risco = "Médio/Alto"
        decisao = "Pacote fraco para promessa premium"
        proximo_passo = "Completar os artefatos essenciais antes de entregar."

    return {
        "versao": VERSAO_PACOTE_PREMIUM_VALORIS,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score_pacote": max(0, min(100, score_pacote)),
        "score_relatorio": score_relatorio,
        "score_comparador": score_comparador,
        "score_watchlist": score_watchlist,
        "score_entrega": score_entrega,
        "ticker_base": ticker_base,
        "empresa_base": empresa_base,
        "artefatos_total": len(ARTEFATOS_PACOTE),
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo_passo,
        "artefatos": ARTEFATOS_PACOTE,
        "playbook": PLAYBOOK_PACOTE,
        "checklist": CHECKLIST_PACOTE,
        "relatorio": relatorio,
        "comparador": comparador,
        "watchlist": watchlist,
    }


def gerar_sumario_executivo_pacote_markdown(ticker: str = "") -> str:
    saude = calcular_saude_pacote_premium(ticker)
    artefatos = "\n".join(
        [f"- **{item['nome']}** — `{item['arquivo']}`." for item in ARTEFATOS_PACOTE]
    )
    return f"""# Sumário Executivo — Pacote Premium Valoris

Versão: {VERSAO_PACOTE_PREMIUM_VALORIS}  
Gerado em: {saude['gerado_em']}

## Entrega

Empresa base: {saude['empresa_base'] or 'pendente'}  
Ticker base: {saude['ticker_base']}  
Score do pacote: {saude['score_pacote']}/100  
Risco: {saude['risco']}  
Decisão: {saude['decisao']}

## O que este pacote entrega

Este pacote reúne dossiê premium, contexto de watchlist, comparação setorial, perguntas críticas e plano de acompanhamento.

O objetivo não é prometer retorno. O objetivo é organizar uma análise mais clara, cética e acionável.

## Próximo passo recomendado

{saude['proximo_passo']}

## Artefatos incluídos

{artefatos}
"""


def _gerar_dossie(ticker: str = "") -> str:
    return _try_call(
        "relatorio_premium_v2_valoris",
        "gerar_dossie_premium_v2_markdown",
        ticker,
        fallback="# Dossiê Premium v2 indisponível\n",
    )


def _gerar_watchlist() -> str:
    return _try_call(
        "watchlist_fundadores_valoris",
        "gerar_relatorio_watchlist_markdown",
        fallback="# Relatório Watchlist indisponível\n",
    )


def _gerar_comparador() -> str:
    return _try_call(
        "comparador_setorial_valoris",
        "gerar_relatorio_comparador_markdown",
        fallback="# Relatório Comparador indisponível\n",
    )


def gerar_pacote_premium_markdown(ticker: str = "") -> str:
    ticker_base = ticker or _selecionar_ticker_padrao()
    return f"""{gerar_sumario_executivo_pacote_markdown(ticker_base)}

---

# Dossiê Premium v2

{_gerar_dossie(ticker_base)}

---

# Watchlist e Acompanhamento

{_gerar_watchlist()}

---

# Comparador Setorial

{_gerar_comparador()}

---

# Nota de responsabilidade

Este pacote é uma ferramenta educacional e analítica. Ele não é recomendação individual de investimento.
"""


def gerar_playbook_pacote_markdown(saude: Dict[str, Any] | None = None) -> str:
    if saude is None:
        saude = calcular_saude_pacote_premium()
    etapas = "\n".join([f"- **{item['etapa']}**: {item['acao']}" for item in PLAYBOOK_PACOTE])
    return f"""# Playbook Pacote Premium — Valoris

Versão: {VERSAO_PACOTE_PREMIUM_VALORIS}  
Gerado em: {saude['gerado_em']}

## Princípio

Uma entrega premium deve ser clara, completa e útil o suficiente para o fundador perceber avanço real.

## Etapas

{etapas}
"""


def gerar_checklist_pacote_markdown(saude: Dict[str, Any] | None = None) -> str:
    if saude is None:
        saude = calcular_saude_pacote_premium()
    checklist = "\n".join([f"- [x] {item}" for item in CHECKLIST_PACOTE])
    return f"""# Checklist Pacote Premium — Valoris

Versão: {VERSAO_PACOTE_PREMIUM_VALORIS}  
Gerado em: {saude['gerado_em']}

Score Pacote: {saude['score_pacote']}/100  
Decisão: {saude['decisao']}

## Checklist

{checklist}
"""


def salvar_sumario_executivo_pacote_markdown(ticker: str = "") -> Dict[str, Any]:
    saude = calcular_saude_pacote_premium(ticker)
    CAMINHO_SUMARIO_MD.write_text(gerar_sumario_executivo_pacote_markdown(ticker), encoding="utf-8")
    return {"ok": True, "arquivo": str(CAMINHO_SUMARIO_MD), "score_pacote": saude["score_pacote"]}


def salvar_pacote_premium_markdown(ticker: str = "") -> Dict[str, Any]:
    saude = calcular_saude_pacote_premium(ticker)
    CAMINHO_PACOTE_MD.write_text(gerar_pacote_premium_markdown(ticker), encoding="utf-8")
    return {"ok": True, "arquivo": str(CAMINHO_PACOTE_MD), "score_pacote": saude["score_pacote"]}


def salvar_playbook_pacote_markdown() -> Dict[str, Any]:
    saude = calcular_saude_pacote_premium()
    CAMINHO_PLAYBOOK_MD.write_text(gerar_playbook_pacote_markdown(saude), encoding="utf-8")
    return {"ok": True, "arquivo": str(CAMINHO_PLAYBOOK_MD), "score_pacote": saude["score_pacote"]}


def salvar_checklist_pacote_markdown() -> Dict[str, Any]:
    saude = calcular_saude_pacote_premium()
    CAMINHO_CHECKLIST_MD.write_text(gerar_checklist_pacote_markdown(saude), encoding="utf-8")
    return {"ok": True, "arquivo": str(CAMINHO_CHECKLIST_MD), "score_pacote": saude["score_pacote"]}


def gerar_manifesto_pacote_premium(ticker: str = "") -> Dict[str, Any]:
    saude = calcular_saude_pacote_premium(ticker)
    manifesto = {
        "versao": VERSAO_PACOTE_PREMIUM_VALORIS,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "saude": saude,
        "artefatos": ARTEFATOS_PACOTE,
        "playbook": PLAYBOOK_PACOTE,
        "checklist": CHECKLIST_PACOTE,
    }
    CAMINHO_MANIFESTO_PACOTE.write_text(json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifesto


def salvar_zip_pacote_premium(ticker: str = "") -> Dict[str, Any]:
    saude = calcular_saude_pacote_premium(ticker)
    arquivos = {
        "SUMARIO_EXECUTIVO_PACOTE_PREMIUM_VALORIS.md": gerar_sumario_executivo_pacote_markdown(ticker),
        "PACOTE_PREMIUM_VALORIS.md": gerar_pacote_premium_markdown(ticker),
        "PLAYBOOK_PACOTE_PREMIUM_VALORIS.md": gerar_playbook_pacote_markdown(saude),
        "CHECKLIST_PACOTE_PREMIUM_VALORIS.md": gerar_checklist_pacote_markdown(saude),
        "manifesto_pacote_premium_valoris.json": json.dumps(gerar_manifesto_pacote_premium(ticker), ensure_ascii=False, indent=2),
    }
    with zipfile.ZipFile(CAMINHO_ZIP, "w", compression=zipfile.ZIP_DEFLATED) as pacote:
        for nome, conteudo in arquivos.items():
            pacote.writestr(nome, conteudo)
    return {"ok": True, "arquivo": str(CAMINHO_ZIP), "score_pacote": saude["score_pacote"], "arquivos": list(arquivos.keys())}


def salvar_decisao_pacote_premium(saude: Dict[str, Any], observacoes: str = "") -> Dict[str, str]:
    _garantir_csv(CAMINHO_DECISOES_PACOTE, CAMPOS_DECISAO)
    registro = {
        "id": str(uuid4())[:8],
        "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score_pacote": str(saude.get("score_pacote", "")),
        "score_relatorio": str(saude.get("score_relatorio", "")),
        "score_comparador": str(saude.get("score_comparador", "")),
        "score_watchlist": str(saude.get("score_watchlist", "")),
        "score_entrega": str(saude.get("score_entrega", "")),
        "ticker_base": _limpar_texto(saude.get("ticker_base")),
        "empresa_base": _limpar_texto(saude.get("empresa_base")),
        "artefatos_total": str(saude.get("artefatos_total", "")),
        "risco": _limpar_texto(saude.get("risco")),
        "decisao": _limpar_texto(saude.get("decisao")),
        "proximo_passo": _limpar_texto(saude.get("proximo_passo")),
        "observacoes": _limpar_texto(observacoes),
    }
    with CAMINHO_DECISOES_PACOTE.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISAO)
        escritor.writerow(registro)
    return registro


def carregar_decisoes_pacote_premium() -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_DECISOES_PACOTE, CAMPOS_DECISAO)
    with CAMINHO_DECISOES_PACOTE.open("r", newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def gerar_csv_decisoes_pacote_premium() -> str:
    _garantir_csv(CAMINHO_DECISOES_PACOTE, CAMPOS_DECISAO)
    return CAMINHO_DECISOES_PACOTE.read_text(encoding="utf-8")


def renderizar_pacote_premium_valoris() -> None:
    st.markdown(f"# Pacote Premium Valoris v{VERSAO_PACOTE_PREMIUM_VALORIS}")
    st.caption("Empacote dossiê, watchlist, comparador, sumário executivo e checklist em uma entrega premium.")

    ticker_padrao = _selecionar_ticker_padrao() or "PENDENTE"
    ticker = st.text_input("Ticker base do pacote", value=ticker_padrao)
    ticker_param = "" if ticker == "PENDENTE" else ticker
    saude = calcular_saude_pacote_premium(ticker_param)

    col_1, col_2, col_3, col_4 = st.columns(4)
    col_1.metric("Score Pacote", f"{saude['score_pacote']}/100")
    col_2.metric("Relatório", f"{saude['score_relatorio']}/100")
    col_3.metric("Comparador", f"{saude['score_comparador']}/100")
    col_4.metric("Watchlist", f"{saude['score_watchlist']}/100")
    st.progress(saude["score_pacote"] / 100)

    if saude["score_pacote"] >= 82:
        st.success(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    elif saude["ticker_base"] != "PENDENTE":
        st.warning(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    else:
        st.info(f"**{saude['decisao']}** — {saude['proximo_passo']}")

    st.divider()
    st.markdown("### Artefatos do pacote")
    st.dataframe(saude["artefatos"], width="stretch", hide_index=True)

    st.markdown("### Sumário executivo")
    st.markdown(gerar_sumario_executivo_pacote_markdown(ticker_param))

    st.divider()
    col_a, col_b, col_c, col_d = st.columns(4)
    with col_a:
        if st.button("Salvar pacote .md"):
            st.json(salvar_pacote_premium_markdown(ticker_param))
    with col_b:
        if st.button("Salvar ZIP"):
            st.json(salvar_zip_pacote_premium(ticker_param))
    with col_c:
        if st.button("Gerar manifesto"):
            manifesto = gerar_manifesto_pacote_premium(ticker_param)
            st.json({"versao": manifesto["versao"], "score": manifesto["saude"]["score_pacote"]})
    with col_d:
        if st.button("Salvar sumário .md"):
            st.json(salvar_sumario_executivo_pacote_markdown(ticker_param))

    col_e, col_f = st.columns(2)
    with col_e:
        if st.button("Salvar playbook .md"):
            st.json(salvar_playbook_pacote_markdown())
    with col_f:
        if st.button("Salvar checklist .md"):
            st.json(salvar_checklist_pacote_markdown())

    if st.button("Salvar decisão Pacote Premium"):
        registro = salvar_decisao_pacote_premium(saude, observacoes="Decisão gerada pelo pacote premium.")
        st.success(f"Decisão salva: {registro['decisao']}")
        st.rerun()

    st.download_button(
        "Baixar pacote premium (.md)",
        data=gerar_pacote_premium_markdown(ticker_param),
        file_name="PACOTE_PREMIUM_VALORIS.md",
        mime="text/markdown",
    )
    st.download_button(
        "Baixar decisões pacote (.csv)",
        data=gerar_csv_decisoes_pacote_premium(),
        file_name="decisoes_pacote_premium_valoris.csv",
        mime="text/csv",
    )


def executar_autoteste_pacote_premium_valoris() -> List[Dict[str, str]]:
    saude = calcular_saude_pacote_premium()
    return [
        {"teste": "versao_pacote_premium", "status": "OK" if VERSAO_PACOTE_PREMIUM_VALORIS == "3.8.88" else "FALHA", "detalhe": VERSAO_PACOTE_PREMIUM_VALORIS},
        {"teste": "score_pacote", "status": "OK" if 0 <= saude["score_pacote"] <= 100 else "FALHA", "detalhe": str(saude["score_pacote"])},
        {"teste": "pacote_markdown", "status": "OK" if "# Sumário Executivo" in gerar_pacote_premium_markdown() else "FALHA", "detalhe": "gerar_pacote_premium_markdown"},
        {"teste": "renderizador", "status": "OK" if callable(renderizar_pacote_premium_valoris) else "FALHA", "detalhe": "renderizar_pacote_premium_valoris"},
    ]
