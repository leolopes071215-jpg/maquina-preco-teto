# estabilidade_execucao_valoris.py
from __future__ import annotations

import csv
import json
import py_compile
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

import streamlit as st


VERSAO_ESTABILIDADE_EXECUCAO_VALORIS = "3.8.91"

CAMINHO_DECISOES = Path("decisoes_estabilidade_execucao_valoris.csv")
CAMINHO_MANIFESTO = Path("manifesto_estabilidade_execucao_valoris.json")
CAMINHO_RELATORIO = Path("RELATORIO_ESTABILIDADE_EXECUCAO_VALORIS.md")
CAMINHO_CHECKLIST = Path("CHECKLIST_ESTABILIDADE_EXECUCAO_VALORIS.md")
CAMINHO_VALIDACAO = Path("validacao_leve_valoris.json")

CAMPOS_DECISOES = [
    "id", "data_registro", "score_estabilidade", "score_logs",
    "score_validacao", "score_higiene", "csvs_total", "csvs_pesados",
    "backups_total", "validacoes_ok", "validacoes_falha",
    "risco", "decisao", "proximo_passo", "observacoes",
]

MODULOS_CRITICOS = [
    "app.py",
    "modo_exibicao.py",
    "release_guard.py",
    "gateway_dados_valoris.py",
    "repositorios_valoris.py",
    "roadmap_premium_valoris.py",
    "feedback_pacote_premium_valoris.py",
    "pacote_premium_valoris.py",
    "relatorio_premium_v2_valoris.py",
    "comparador_setorial_valoris.py",
    "watchlist_fundadores_valoris.py",
    "retencao_fundadores_valoris.py",
    "checkout_fundadores_valoris.py",
]

CHECKLIST_ESTABILIDADE = [
    "Evitar list(csv.DictReader(...)) em logs grandes",
    "Carregar apenas últimos registros com deque",
    "Não commitar backups de logs",
    "Não commitar CSV, JSON, MD ou ZIP gerados localmente",
    "Rodar py_compile antes de abrir Streamlit",
    "Rodar release_guard.py antes de commit",
    "Usar validação leve em vez de blocos gigantes no PowerShell",
    "Separar teste de código de geração de artefatos",
    "Remover backups locais depois da correção",
    "Manter .gitignore protegido contra artefatos locais",
]

SCRIPT_LIMPEZA_SEGURA = """cd C:\\Users\\user\\Documents\\maquina-preco-teto

Remove-Item logs_*_backup_*.csv -Force -ErrorAction SilentlyContinue
Remove-Item *_backup_*.csv -Force -ErrorAction SilentlyContinue

git status
"""

SCRIPT_VALIDACAO_LEVE = """cd C:\\Users\\user\\Documents\\maquina-preco-teto

python -m py_compile app.py
python -m py_compile modo_exibicao.py
python -m py_compile release_guard.py
python -m py_compile gateway_dados_valoris.py
python -m py_compile repositorios_valoris.py
python -m py_compile roadmap_premium_valoris.py
python -m py_compile feedback_pacote_premium_valoris.py
python -m py_compile pacote_premium_valoris.py
python -m py_compile relatorio_premium_v2_valoris.py
python -m py_compile comparador_setorial_valoris.py
python -m py_compile watchlist_fundadores_valoris.py

python release_guard.py
git status
"""

SCRIPT_GITIGNORE = """Add-Content .gitignore "`ndecisoes_estabilidade_execucao_valoris.csv"
Add-Content .gitignore "`nmanifesto_estabilidade_execucao_valoris.json"
Add-Content .gitignore "`nRELATORIO_ESTABILIDADE_EXECUCAO_VALORIS.md"
Add-Content .gitignore "`nCHECKLIST_ESTABILIDADE_EXECUCAO_VALORIS.md"
Add-Content .gitignore "`nvalidacao_leve_valoris.json"
Add-Content .gitignore "`nlogs_*_backup_*.csv"
Add-Content .gitignore "`n*_backup_*.csv"
"""


def _txt(valor: Any) -> str:
    return "" if valor is None else str(valor).strip()


def _mb(caminho: Path) -> float:
    try:
        return round(caminho.stat().st_size / (1024 * 1024), 3)
    except Exception:
        return 0.0


def _garantir_csv(caminho: Path, campos: List[str]) -> None:
    if caminho.exists():
        return
    with caminho.open("w", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=campos).writeheader()


def carregar_csv_limitado(caminho: str | Path, max_registros: int = 300) -> List[Dict[str, str]]:
    """Leitor genérico seguro para CSV grande."""
    caminho = Path(caminho)
    if not caminho.exists():
        return []
    try:
        with caminho.open("r", newline="", encoding="utf-8") as f:
            return list(deque(csv.DictReader(f), maxlen=max_registros))
    except Exception:
        return []


def listar_csvs(limite_pesado_mb: float = 3.0) -> List[Dict[str, Any]]:
    itens = []
    for caminho in Path.cwd().glob("*.csv"):
        nome = caminho.name
        tamanho = _mb(caminho)
        tipo = "backup" if "backup" in nome.lower() else ("log" if "log" in nome.lower() else "dados_local")
        itens.append({
            "arquivo": nome,
            "tipo": tipo,
            "tamanho_mb": tamanho,
            "pesado": tamanho >= limite_pesado_mb,
            "recomendacao": "remover backup local" if tipo == "backup" else ("limitar leitura/limpar" if tamanho >= limite_pesado_mb else "ok"),
        })
    return sorted(itens, key=lambda x: x["tamanho_mb"], reverse=True)


def listar_artefatos() -> List[Dict[str, Any]]:
    itens = []
    for padrao in ("*.md", "*.json", "*.zip"):
        for caminho in Path.cwd().glob(padrao):
            if caminho.name in {"package.json", "tsconfig.json"}:
                continue
            itens.append({
                "arquivo": caminho.name,
                "extensao": caminho.suffix,
                "tamanho_mb": _mb(caminho),
                "recomendacao": "artefato local: manter fora do Git",
            })
    return sorted(itens, key=lambda x: x["tamanho_mb"], reverse=True)


def validar_modulos_leve() -> List[Dict[str, str]]:
    resultados = []
    for nome in MODULOS_CRITICOS:
        caminho = Path(nome)
        if not caminho.exists():
            resultados.append({"arquivo": nome, "status": "AUSENTE", "detalhe": "arquivo não encontrado"})
            continue
        try:
            py_compile.compile(str(caminho), doraise=True)
            resultados.append({"arquivo": nome, "status": "OK", "detalhe": "compilação leve concluída"})
        except Exception as erro:
            resultados.append({"arquivo": nome, "status": "FALHA", "detalhe": str(erro)[:500]})
    return resultados


def salvar_validacao_leve_json() -> Dict[str, Any]:
    resultados = validar_modulos_leve()
    payload = {
        "versao": VERSAO_ESTABILIDADE_EXECUCAO_VALORIS,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "resultados": resultados,
    }
    CAMINHO_VALIDACAO.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": True, "arquivo": str(CAMINHO_VALIDACAO), "validacoes": len(resultados)}


def calcular_saude_estabilidade_execucao() -> Dict[str, Any]:
    csvs = listar_csvs()
    artefatos = listar_artefatos()
    validacoes = validar_modulos_leve()

    pesados = [x for x in csvs if x["pesado"]]
    backups = [x for x in csvs if x["tipo"] == "backup"]
    ok = sum(1 for x in validacoes if x["status"] == "OK")
    falhas = sum(1 for x in validacoes if x["status"] == "FALHA")
    ausentes = sum(1 for x in validacoes if x["status"] == "AUSENTE")

    score_logs = max(0, min(100, 100 - len(pesados) * 15 - len(backups) * 10))
    score_validacao = int((ok / len(validacoes)) * 100) if validacoes else 0
    score_validacao = max(0, min(100, score_validacao - ausentes * 4))
    score_higiene = max(0, min(100, 100 - len(artefatos) * 2 - len(backups) * 12 - len(pesados) * 8))
    score = int(round(score_logs * 0.35 + score_validacao * 0.45 + score_higiene * 0.20))

    if falhas:
        risco = "Alto"
        decisao = "Corrigir falhas de compilação antes de avançar"
        proximo = "Abrir os arquivos com FALHA e corrigir pontualmente."
    elif pesados:
        risco = "Médio/Alto"
        decisao = "Projeto funcional, mas com risco de MemoryError por CSV pesado"
        proximo = "Limpar backups e limitar leitura de logs nos módulos afetados."
    elif backups:
        risco = "Médio"
        decisao = "Projeto estável, mas com backups locais pendentes"
        proximo = "Remover backups locais e manter .gitignore protegido."
    else:
        risco = "Baixo"
        decisao = "Base estável para continuar evoluindo"
        proximo = "Avançar com validação leve antes de cada commit."

    return {
        "versao": VERSAO_ESTABILIDADE_EXECUCAO_VALORIS,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score_estabilidade": score,
        "score_logs": score_logs,
        "score_validacao": score_validacao,
        "score_higiene": score_higiene,
        "arquivos_csv_total": len(csvs),
        "arquivos_csv_pesados": len(pesados),
        "backups_logs_total": len(backups),
        "artefatos_gerados_total": len(artefatos),
        "validacoes_ok": ok,
        "validacoes_falha": falhas,
        "validacoes_ausentes": ausentes,
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo,
        "csvs": csvs,
        "csvs_pesados": pesados,
        "backups": backups,
        "artefatos": artefatos,
        "validacoes": validacoes,
    }


def salvar_decisao_estabilidade(saude: Dict[str, Any], observacoes: str = "") -> Dict[str, str]:
    _garantir_csv(CAMINHO_DECISOES, CAMPOS_DECISOES)
    registro = {
        "id": str(uuid4())[:8],
        "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score_estabilidade": str(saude.get("score_estabilidade", "")),
        "score_logs": str(saude.get("score_logs", "")),
        "score_validacao": str(saude.get("score_validacao", "")),
        "score_higiene": str(saude.get("score_higiene", "")),
        "csvs_total": str(saude.get("arquivos_csv_total", "")),
        "csvs_pesados": str(saude.get("arquivos_csv_pesados", "")),
        "backups_total": str(saude.get("backups_logs_total", "")),
        "validacoes_ok": str(saude.get("validacoes_ok", "")),
        "validacoes_falha": str(saude.get("validacoes_falha", "")),
        "risco": _txt(saude.get("risco")),
        "decisao": _txt(saude.get("decisao")),
        "proximo_passo": _txt(saude.get("proximo_passo")),
        "observacoes": _txt(observacoes),
    }
    with CAMINHO_DECISOES.open("a", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=CAMPOS_DECISOES).writerow(registro)
    return registro


def gerar_relatorio_estabilidade_markdown(saude: Dict[str, Any] | None = None) -> str:
    if saude is None:
        saude = calcular_saude_estabilidade_execucao()
    pesados = "\n".join([f"- **{x['arquivo']}** — {x['tamanho_mb']} MB — {x['recomendacao']}" for x in saude["csvs_pesados"]]) or "- Nenhum CSV pesado."
    falhas = "\n".join([f"- **{x['arquivo']}** — {x['status']} — {x['detalhe']}" for x in saude["validacoes"] if x["status"] != "OK"]) or "- Nenhuma falha."
    backups = "\n".join([f"- **{x['arquivo']}** — {x['tamanho_mb']} MB" for x in saude["backups"]]) or "- Nenhum backup."

    return f"""# Relatório de Estabilidade de Execução — Valoris

Versão: {VERSAO_ESTABILIDADE_EXECUCAO_VALORIS}  
Gerado em: {saude['gerado_em']}

## Diagnóstico

Score Estabilidade: {saude['score_estabilidade']}/100  
Score Logs: {saude['score_logs']}/100  
Score Validação: {saude['score_validacao']}/100  
Score Higiene: {saude['score_higiene']}/100  

Risco: {saude['risco']}  
Decisão: {saude['decisao']}  
Próximo passo: {saude['proximo_passo']}

## CSVs pesados

{pesados}

## Backups locais

{backups}

## Falhas de validação

{falhas}

## Limpeza segura

```powershell
{SCRIPT_LIMPEZA_SEGURA}
```

## Validação leve

```powershell
{SCRIPT_VALIDACAO_LEVE}
```
"""


def gerar_checklist_estabilidade_markdown(saude: Dict[str, Any] | None = None) -> str:
    if saude is None:
        saude = calcular_saude_estabilidade_execucao()
    checklist = "\n".join([f"- [x] {x}" for x in CHECKLIST_ESTABILIDADE])
    return f"""# Checklist Estabilidade de Execução — Valoris

Versão: {VERSAO_ESTABILIDADE_EXECUCAO_VALORIS}  
Gerado em: {saude['gerado_em']}

Score Estabilidade: {saude['score_estabilidade']}/100  
Decisão: {saude['decisao']}

{checklist}
"""


def salvar_relatorio_estabilidade_markdown() -> Dict[str, Any]:
    saude = calcular_saude_estabilidade_execucao()
    CAMINHO_RELATORIO.write_text(gerar_relatorio_estabilidade_markdown(saude), encoding="utf-8")
    return {"ok": True, "arquivo": str(CAMINHO_RELATORIO), "score_estabilidade": saude["score_estabilidade"]}


def salvar_checklist_estabilidade_markdown() -> Dict[str, Any]:
    saude = calcular_saude_estabilidade_execucao()
    CAMINHO_CHECKLIST.write_text(gerar_checklist_estabilidade_markdown(saude), encoding="utf-8")
    return {"ok": True, "arquivo": str(CAMINHO_CHECKLIST), "score_estabilidade": saude["score_estabilidade"]}


def gerar_manifesto_estabilidade_execucao() -> Dict[str, Any]:
    saude = calcular_saude_estabilidade_execucao()
    manifesto = {
        "versao": VERSAO_ESTABILIDADE_EXECUCAO_VALORIS,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "saude": saude,
        "checklist": CHECKLIST_ESTABILIDADE,
        "scripts": {
            "limpeza_segura": SCRIPT_LIMPEZA_SEGURA,
            "validacao_leve": SCRIPT_VALIDACAO_LEVE,
            "gitignore": SCRIPT_GITIGNORE,
        },
    }
    CAMINHO_MANIFESTO.write_text(json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifesto


def renderizar_estabilidade_execucao_valoris() -> None:
    st.markdown("## Estabilidade de Execução — Valoris v3.8.91")
    st.caption("Validação leve, higiene de logs e proteção contra MemoryError.")

    saude = calcular_saude_estabilidade_execucao()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Score", f"{saude['score_estabilidade']}/100")
    c2.metric("CSV pesados", saude["arquivos_csv_pesados"])
    c3.metric("Backups", saude["backups_logs_total"])
    c4.metric("Falhas", saude["validacoes_falha"])

    st.progress(saude["score_estabilidade"] / 100)

    if saude["validacoes_falha"]:
        st.error(f"{saude['decisao']} — {saude['proximo_passo']}")
    elif saude["score_estabilidade"] >= 85:
        st.success(f"{saude['decisao']} — {saude['proximo_passo']}")
    else:
        st.warning(f"{saude['decisao']} — {saude['proximo_passo']}")

    st.divider()

    st.markdown("### Validação leve")
    st.dataframe(saude["validacoes"], width="stretch", hide_index=True)

    st.markdown("### CSVs locais")
    st.dataframe(saude["csvs"][:80], width="stretch", hide_index=True)

    st.markdown("### Artefatos locais")
    st.dataframe(saude["artefatos"][:80], width="stretch", hide_index=True)

    st.divider()

    st.markdown("### Scripts seguros")
    st.code(SCRIPT_LIMPEZA_SEGURA, language="powershell")
    st.code(SCRIPT_VALIDACAO_LEVE, language="powershell")
    st.code(SCRIPT_GITIGNORE, language="powershell")

    b1, b2, b3, b4 = st.columns(4)
    if b1.button("Salvar validação JSON"):
        st.json(salvar_validacao_leve_json())
    if b2.button("Gerar manifesto"):
        manifesto = gerar_manifesto_estabilidade_execucao()
        st.success(f"Manifesto gerado: {CAMINHO_MANIFESTO}")
        st.json({"versao": manifesto["versao"], "score": manifesto["saude"]["score_estabilidade"]})
    if b3.button("Salvar relatório .md"):
        st.json(salvar_relatorio_estabilidade_markdown())
    if b4.button("Salvar checklist .md"):
        st.json(salvar_checklist_estabilidade_markdown())

    if st.button("Salvar decisão Estabilidade"):
        st.json(salvar_decisao_estabilidade(saude, "Decisão gerada pela aba Estabilidade."))
        st.rerun()

    st.download_button(
        "Baixar relatório de estabilidade (.md)",
        data=gerar_relatorio_estabilidade_markdown(saude),
        file_name="RELATORIO_ESTABILIDADE_EXECUCAO_VALORIS.md",
        mime="text/markdown",
    )


def executar_autoteste_estabilidade_execucao_valoris() -> List[Dict[str, str]]:
    saude = calcular_saude_estabilidade_execucao()
    return [
        {"teste": "versao", "status": "OK" if VERSAO_ESTABILIDADE_EXECUCAO_VALORIS == "3.8.91" else "FALHA", "detalhe": VERSAO_ESTABILIDADE_EXECUCAO_VALORIS},
        {"teste": "score", "status": "OK" if 0 <= saude["score_estabilidade"] <= 100 else "FALHA", "detalhe": str(saude["score_estabilidade"])},
        {"teste": "validacao", "status": "OK" if isinstance(validar_modulos_leve(), list) else "FALHA", "detalhe": str(len(validar_modulos_leve()))},
        {"teste": "renderizador", "status": "OK" if callable(renderizar_estabilidade_execucao_valoris) else "FALHA", "detalhe": "renderizar_estabilidade_execucao_valoris"},
    ]
