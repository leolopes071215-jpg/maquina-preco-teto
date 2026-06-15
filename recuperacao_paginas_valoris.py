# recuperacao_paginas_valoris.py
# Valoris — Recuperação Controlada de Páginas v3.8.94
# ------------------------------------------------------------
# Objetivo:
# - Transformar o catálogo de navegação em plano de recuperação.
# - Priorizar páginas antigas que podem voltar ao app seguro.
# - Evitar regressão para o modelo pesado de renderização simultânea.
# ------------------------------------------------------------

from __future__ import annotations

import ast
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st


VERSAO_RECUPERACAO_PAGINAS_VALORIS = "3.8.94"

CAMINHO_PLANO = Path("plano_recuperacao_paginas_valoris.csv")
CAMINHO_DECISOES = Path("decisoes_recuperacao_paginas_valoris.csv")
CAMINHO_RELATORIO = Path("RELATORIO_RECUPERACAO_PAGINAS_VALORIS.md")
CAMINHO_MANIFESTO = Path("manifesto_recuperacao_paginas_valoris.json")

CAMPOS_PLANO = [
    "prioridade",
    "pagina_sugerida",
    "arquivo",
    "modulo",
    "funcao",
    "tipo",
    "linhas",
    "risco_memoria",
    "score",
    "motivo",
]

CAMPOS_DECISOES = [
    "data_hora",
    "decisao",
    "pagina",
    "modulo",
    "funcao",
    "observacao",
]


def _agora_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat(sep=" ")


def _ler_ast(caminho: Path) -> Optional[ast.AST]:
    try:
        return ast.parse(caminho.read_text(encoding="utf-8"))
    except Exception:
        return None


def _normalizar_pagina(nome_modulo: str) -> str:
    base = nome_modulo.replace("_valoris", "").replace("_beta", "").replace("_", " ").strip()
    siglas = {
        "api": "API",
        "ux": "UX",
        "crm": "CRM",
        "fiis": "FIIs",
        "sqlite": "SQLite",
        "sql": "SQL",
    }

    palavras = [siglas.get(p.lower(), p.capitalize()) for p in base.split()]
    return " ".join(palavras) or nome_modulo


def _extrair_paginas_app(caminho_app: Path = Path("app.py")) -> Dict[str, Dict[str, str]]:
    paginas: Dict[str, Dict[str, str]] = {}
    arvore = _ler_ast(caminho_app)

    if arvore is None:
        return paginas

    for node in ast.walk(arvore):
        if not isinstance(node, ast.Assign):
            continue

        nomes = [alvo.id for alvo in node.targets if isinstance(alvo, ast.Name)]
        if "PAGINAS" not in nomes:
            continue

        if not isinstance(node.value, ast.Dict):
            continue

        for chave, valor in zip(node.value.keys, node.value.values):
            if not (isinstance(chave, ast.Constant) and isinstance(chave.value, str)):
                continue

            pagina = chave.value
            modulo = ""
            funcao = ""

            if isinstance(valor, ast.Tuple):
                partes = valor.elts
                if len(partes) >= 2:
                    if isinstance(partes[0], ast.Constant) and isinstance(partes[0].value, str):
                        modulo = partes[0].value
                    if isinstance(partes[1], ast.Constant) and isinstance(partes[1].value, str):
                        funcao = partes[1].value

            paginas[pagina] = {"modulo": modulo, "funcao": funcao}

    return paginas


def _extrair_funcoes_renderizaveis(caminho: Path) -> List[Dict[str, Any]]:
    arvore = _ler_ast(caminho)
    if arvore is None:
        return []

    registros: List[Dict[str, Any]] = []
    modulo = caminho.stem

    for node in ast.walk(arvore):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        nome = node.name

        if not nome.startswith("renderizar_"):
            continue

        linhas = 1
        if getattr(node, "end_lineno", None) and getattr(node, "lineno", None):
            linhas = max(1, node.end_lineno - node.lineno + 1)

        registros.append(
            {
                "arquivo": caminho.name,
                "modulo": modulo,
                "funcao": nome,
                "tipo": "renderizador",
                "linhas": linhas,
                "pagina_sugerida": _normalizar_pagina(modulo),
            }
        )

    return registros


def _ignorar_arquivo(caminho: Path) -> bool:
    nome = caminho.name.lower()

    if nome in {
        "app.py",
        "release_guard.py",
        "style.py",
        "valuation.py",
        "patch_v3_8_94_recuperacao_paginas.py",
    }:
        return True

    return nome.startswith(("app_v", "modo_exibicao_v", "release_guard_v", "patch_"))


def _avaliar_risco_memoria(item: Dict[str, Any]) -> Dict[str, Any]:
    modulo = str(item.get("modulo", "")).lower()
    funcao = str(item.get("funcao", "")).lower()
    linhas = int(item.get("linhas", 0) or 0)
    texto = f"{modulo} {funcao}"

    risco = 20
    motivos = []

    if linhas > 220:
        risco += 25
        motivos.append("renderizador muito longo")
    elif linhas > 120:
        risco += 15
        motivos.append("renderizador médio/alto")

    termos_pesados = {
        "logs": 20,
        "dados": 18,
        "database": 18,
        "postgres": 18,
        "sqlite": 14,
        "gateway": 16,
        "analytics": 14,
        "repositorios": 14,
        "relatorio": 10,
        "premium": 8,
        "catalogo": 8,
    }

    for termo, peso in termos_pesados.items():
        if termo in texto:
            risco += peso
            motivos.append(f"contém {termo}")

    risco = max(0, min(100, risco))

    if risco >= 70:
        classe = "alto"
    elif risco >= 45:
        classe = "medio"
    else:
        classe = "baixo"

    if not motivos:
        motivos.append("renderizador simples")

    return {
        "risco_memoria": classe,
        "risco_num": risco,
        "motivo": ", ".join(dict.fromkeys(motivos)),
    }


def gerar_plano_recuperacao_paginas(raiz: Path = Path(".")) -> List[Dict[str, Any]]:
    paginas_app = _extrair_paginas_app(raiz / "app.py")
    chaves_app = {
        (dados.get("modulo", ""), dados.get("funcao", ""))
        for dados in paginas_app.values()
    }

    candidatos: List[Dict[str, Any]] = []

    for caminho in sorted(raiz.glob("*.py")):
        if _ignorar_arquivo(caminho):
            continue

        for item in _extrair_funcoes_renderizaveis(caminho):
            chave = (item["modulo"], item["funcao"])

            if chave in chaves_app:
                continue

            risco = _avaliar_risco_memoria(item)
            score = 100 - int(risco["risco_num"])

            if "beta" in item["modulo"]:
                score += 5
            if "landing" in item["modulo"] or "convite" in item["modulo"]:
                score += 6
            if "api" in item["modulo"] or "database" in item["modulo"]:
                score -= 10

            score = max(0, min(100, score))

            candidatos.append(
                {
                    "prioridade": "",
                    "pagina_sugerida": item["pagina_sugerida"],
                    "arquivo": item["arquivo"],
                    "modulo": item["modulo"],
                    "funcao": item["funcao"],
                    "tipo": item["tipo"],
                    "linhas": item["linhas"],
                    "risco_memoria": risco["risco_memoria"],
                    "score": score,
                    "motivo": risco["motivo"],
                }
            )

    candidatos.sort(key=lambda x: (-int(x["score"]), x["risco_memoria"], x["modulo"]))

    for i, item in enumerate(candidatos, start=1):
        item["prioridade"] = i

    return candidatos


def salvar_plano_recuperacao_csv(plano: List[Dict[str, Any]], caminho: Path = CAMINHO_PLANO) -> Path:
    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_PLANO)
        escritor.writeheader()
        for item in plano:
            escritor.writerow({campo: item.get(campo, "") for campo in CAMPOS_PLANO})

    return caminho


def calcular_saude_recuperacao_paginas(plano: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(plano)
    baixo = sum(1 for item in plano if item.get("risco_memoria") == "baixo")
    medio = sum(1 for item in plano if item.get("risco_memoria") == "medio")
    alto = sum(1 for item in plano if item.get("risco_memoria") == "alto")

    score = 75

    if total >= 20:
        score += 8
    if baixo >= 5:
        score += 7
    if alto > baixo:
        score -= 10

    score = max(0, min(100, score))

    return {
        "score": score,
        "candidatos": total,
        "baixo_risco": baixo,
        "medio_risco": medio,
        "alto_risco": alto,
    }


def gerar_snippet_pagina(pagina: str, modulo: str, funcao: str) -> str:
    return (
        f'    "{pagina}": (\n'
        f'        "{modulo}",\n'
        f'        "{funcao}",\n'
        f'        "Página recuperada com validação controlada.",\n'
        f'    ),'
    )


def gerar_relatorio_recuperacao_markdown(plano: List[Dict[str, Any]]) -> str:
    metricas = calcular_saude_recuperacao_paginas(plano)

    linhas = [
        "# Relatório de Recuperação Controlada de Páginas — Valoris",
        "",
        f"Data: {_agora_iso()}",
        f"Versão: {VERSAO_RECUPERACAO_PAGINAS_VALORIS}",
        "",
        "## Diagnóstico",
        "",
        f"- Score: {metricas['score']}/100",
        f"- Candidatos fora do app seguro: {metricas['candidatos']}",
        f"- Baixo risco: {metricas['baixo_risco']}",
        f"- Médio risco: {metricas['medio_risco']}",
        f"- Alto risco: {metricas['alto_risco']}",
        "",
        "## Top candidatos",
        "",
    ]

    for item in plano[:25]:
        linhas.append(
            f"- #{item['prioridade']} — {item['pagina_sugerida']} "
            f"(`{item['modulo']}.{item['funcao']}`) — risco {item['risco_memoria']} — score {item['score']}"
        )

    linhas.extend(
        [
            "",
            "## Regra de ouro",
            "",
            "Recuperar uma página por vez, validar com `python release_guard.py` e testar no Streamlit antes de recuperar a próxima.",
        ]
    )

    return "\n".join(linhas)


def salvar_relatorio_recuperacao_markdown(plano: List[Dict[str, Any]], caminho: Path = CAMINHO_RELATORIO) -> Path:
    caminho.write_text(gerar_relatorio_recuperacao_markdown(plano), encoding="utf-8")
    return caminho


def salvar_manifesto_recuperacao_paginas(plano: List[Dict[str, Any]], caminho: Path = CAMINHO_MANIFESTO) -> Path:
    manifesto = {
        "produto": "Valoris",
        "versao": VERSAO_RECUPERACAO_PAGINAS_VALORIS,
        "modulo": "recuperacao_paginas_valoris",
        "data_hora": _agora_iso(),
        "metricas": calcular_saude_recuperacao_paginas(plano),
        "principio": "recuperar páginas antigas uma por vez, com validação e sem voltar ao modelo pesado de abas",
    }

    caminho.write_text(json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8")
    return caminho


def salvar_decisao_recuperacao_paginas(decisao: str, pagina: str, modulo: str, funcao: str, observacao: str = "") -> Path:
    existe = CAMINHO_DECISOES.exists()

    with CAMINHO_DECISOES.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISOES)
        if not existe:
            escritor.writeheader()
        escritor.writerow(
            {
                "data_hora": _agora_iso(),
                "decisao": decisao,
                "pagina": pagina,
                "modulo": modulo,
                "funcao": funcao,
                "observacao": observacao,
            }
        )

    return CAMINHO_DECISOES


def renderizar_recuperacao_paginas_valoris() -> None:
    st.subheader("Recuperação Controlada de Páginas")
    st.caption(
        "Prioriza quais páginas antigas podem voltar ao app seguro, sem reativar tudo de uma vez."
    )

    plano = gerar_plano_recuperacao_paginas(Path("."))
    metricas = calcular_saude_recuperacao_paginas(plano)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Score", f"{metricas['score']}/100")
    col2.metric("Candidatos", metricas["candidatos"])
    col3.metric("Baixo risco", metricas["baixo_risco"])
    col4.metric("Médio risco", metricas["medio_risco"])
    col5.metric("Alto risco", metricas["alto_risco"])

    st.divider()

    risco = st.selectbox("Filtrar por risco", ["todos", "baixo", "medio", "alto"], index=0)
    busca = st.text_input("Buscar por página, módulo ou função", value="")

    filtrado = plano

    if risco != "todos":
        filtrado = [item for item in filtrado if item.get("risco_memoria") == risco]

    if busca.strip():
        termo = busca.strip().lower()
        filtrado = [
            item for item in filtrado
            if termo in " ".join(str(v).lower() for v in item.values())
        ]

    st.dataframe(filtrado, use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("### Gerar snippet seguro")

    if filtrado:
        opcoes = [
            f"#{item['prioridade']} — {item['pagina_sugerida']} — {item['modulo']}.{item['funcao']}"
            for item in filtrado
        ]
        escolha = st.selectbox("Escolha uma página candidata", opcoes)
        selecionado = filtrado[opcoes.index(escolha)]

        pagina = st.text_input("Nome final da página", value=selecionado["pagina_sugerida"])

        st.code(
            gerar_snippet_pagina(pagina, selecionado["modulo"], selecionado["funcao"]),
            language="python",
        )

        col_a, col_b = st.columns(2)

        if col_a.button("Registrar como candidata"):
            salvar_decisao_recuperacao_paginas(
                decisao="candidata",
                pagina=pagina,
                modulo=selecionado["modulo"],
                funcao=selecionado["funcao"],
                observacao=f"Risco {selecionado['risco_memoria']} | Score {selecionado['score']}",
            )
            st.success("Decisão registrada.")

        if col_b.button("Registrar como descartada por enquanto"):
            salvar_decisao_recuperacao_paginas(
                decisao="descartada_por_enquanto",
                pagina=pagina,
                modulo=selecionado["modulo"],
                funcao=selecionado["funcao"],
                observacao=f"Risco {selecionado['risco_memoria']} | Score {selecionado['score']}",
            )
            st.warning("Decisão registrada como descarte temporário.")

    st.divider()

    col1, col2, col3 = st.columns(3)

    if col1.button("Salvar plano CSV"):
        caminho = salvar_plano_recuperacao_csv(plano)
        st.success(f"Plano salvo em {caminho}")

    if col2.button("Salvar relatório Markdown"):
        caminho = salvar_relatorio_recuperacao_markdown(plano)
        st.success(f"Relatório salvo em {caminho}")

    if col3.button("Salvar manifesto JSON"):
        caminho = salvar_manifesto_recuperacao_paginas(plano)
        st.success(f"Manifesto salvo em {caminho}")


def executar_autoteste_recuperacao_paginas_valoris() -> Dict[str, Any]:
    plano = gerar_plano_recuperacao_paginas(Path("."))
    metricas = calcular_saude_recuperacao_paginas(plano)

    return {
        "ok": True,
        "versao": VERSAO_RECUPERACAO_PAGINAS_VALORIS,
        "metricas": metricas,
    }
