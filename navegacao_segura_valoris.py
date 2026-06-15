# navegacao_segura_valoris.py
# Valoris — Navegação Segura e Catálogo de Módulos v3.8.93

from __future__ import annotations

import ast
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st


VERSAO_NAVEGACAO_SEGURA_VALORIS = "3.8.93"

CAMINHO_CATALOGO = Path("catalogo_navegacao_segura_valoris.csv")
CAMINHO_RELATORIO = Path("RELATORIO_NAVEGACAO_SEGURA_VALORIS.md")
CAMINHO_MANIFESTO = Path("manifesto_navegacao_segura_valoris.json")
CAMINHO_DECISOES = Path("decisoes_navegacao_segura_valoris.csv")

CAMPOS_CATALOGO = [
    "pagina_app",
    "arquivo",
    "modulo",
    "funcao",
    "tipo",
    "linhas",
    "status_app",
    "sugestao_pagina",
]

CAMPOS_DECISOES = [
    "data_hora",
    "decisao",
    "modulo",
    "funcao",
    "observacao",
]


def _agora_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat(sep=" ")


def _normalizar_nome_pagina(nome_modulo: str) -> str:
    base = nome_modulo.replace("_valoris", "").replace("_beta", "").replace("_", " ").strip()
    palavras = []
    siglas = {"api": "API", "ux": "UX", "crm": "CRM", "fiis": "FIIs", "sqlite": "SQLite", "sql": "SQL"}

    for palavra in base.split():
        palavras.append(siglas.get(palavra.lower(), palavra.capitalize()))

    return " ".join(palavras) or nome_modulo


def _ignorar_arquivo(caminho: Path) -> bool:
    nome = caminho.name.lower()

    ignorados_exatos = {
        "app.py",
        "release_guard.py",
        "style.py",
        "valuation.py",
        "patch_v3_8_91_estabilidade.py",
        "patch_v3_8_93_navegacao_segura.py",
    }

    ignorados_prefixos = (
        "app_v",
        "modo_exibicao_v",
        "release_guard_v",
        "patch_",
    )

    if nome in ignorados_exatos:
        return True

    return any(nome.startswith(prefixo) for prefixo in ignorados_prefixos)


def _ler_ast(caminho: Path) -> Optional[ast.AST]:
    try:
        return ast.parse(caminho.read_text(encoding="utf-8"))
    except Exception:
        return None


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

            paginas[pagina] = {
                "pagina": pagina,
                "modulo": modulo,
                "funcao": funcao,
            }

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

        if nome.startswith("renderizar_"):
            tipo = "renderizador"
        elif nome.startswith("executar_autoteste_"):
            tipo = "autoteste"
        else:
            continue

        linhas = 1
        if getattr(node, "end_lineno", None) and getattr(node, "lineno", None):
            linhas = max(1, node.end_lineno - node.lineno + 1)

        registros.append(
            {
                "arquivo": caminho.name,
                "modulo": modulo,
                "funcao": nome,
                "tipo": tipo,
                "linhas": linhas,
            }
        )

    return registros


def gerar_catalogo_navegacao_segura(raiz: Path = Path(".")) -> List[Dict[str, Any]]:
    paginas_app = _extrair_paginas_app(raiz / "app.py")
    por_modulo_funcao = {
        (dados["modulo"], dados["funcao"]): pagina
        for pagina, dados in paginas_app.items()
        if dados.get("modulo") and dados.get("funcao")
    }

    registros: List[Dict[str, Any]] = []

    for caminho in sorted(raiz.glob("*.py")):
        if _ignorar_arquivo(caminho):
            continue

        for item in _extrair_funcoes_renderizaveis(caminho):
            chave = (item["modulo"], item["funcao"])
            pagina_app = por_modulo_funcao.get(chave, "")
            status_app = "no_app_seguro" if pagina_app else "fora_do_app_seguro"

            registros.append(
                {
                    "pagina_app": pagina_app,
                    "arquivo": item["arquivo"],
                    "modulo": item["modulo"],
                    "funcao": item["funcao"],
                    "tipo": item["tipo"],
                    "linhas": item["linhas"],
                    "status_app": status_app,
                    "sugestao_pagina": pagina_app or _normalizar_nome_pagina(item["modulo"]),
                }
            )

    registros.sort(key=lambda x: (x["status_app"], x["modulo"], x["funcao"]))
    return registros


def salvar_catalogo_navegacao_segura_csv(registros: List[Dict[str, Any]], caminho: Path = CAMINHO_CATALOGO) -> Path:
    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_CATALOGO)
        escritor.writeheader()
        for item in registros:
            escritor.writerow({campo: item.get(campo, "") for campo in CAMPOS_CATALOGO})

    return caminho


def calcular_saude_navegacao_segura(registros: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(registros)
    renderizadores = [r for r in registros if r.get("tipo") == "renderizador"]
    no_app = [r for r in renderizadores if r.get("status_app") == "no_app_seguro"]
    fora_app = [r for r in renderizadores if r.get("status_app") == "fora_do_app_seguro"]

    if not renderizadores:
        score = 60
    else:
        cobertura = len(no_app) / max(1, len(renderizadores))
        score = 70 + min(20, int(cobertura * 40))

    if total > 80:
        score += 5

    score = max(0, min(100, score))

    return {
        "score": score,
        "total_funcoes": total,
        "renderizadores": len(renderizadores),
        "no_app_seguro": len(no_app),
        "fora_do_app_seguro": len(fora_app),
    }


def gerar_relatorio_navegacao_segura_markdown(registros: List[Dict[str, Any]]) -> str:
    metricas = calcular_saude_navegacao_segura(registros)
    fora_app = [r for r in registros if r.get("tipo") == "renderizador" and r.get("status_app") == "fora_do_app_seguro"]
    no_app = [r for r in registros if r.get("tipo") == "renderizador" and r.get("status_app") == "no_app_seguro"]

    linhas = [
        "# Relatório de Navegação Segura — Valoris",
        "",
        f"Data: {_agora_iso()}",
        f"Versão: {VERSAO_NAVEGACAO_SEGURA_VALORIS}",
        "",
        "## Diagnóstico",
        "",
        f"- Score: {metricas['score']}/100",
        f"- Funções detectadas: {metricas['total_funcoes']}",
        f"- Renderizadores: {metricas['renderizadores']}",
        f"- Renderizadores no app seguro: {metricas['no_app_seguro']}",
        f"- Renderizadores fora do app seguro: {metricas['fora_do_app_seguro']}",
        "",
        "## Páginas já disponíveis no app seguro",
        "",
    ]

    if no_app:
        for item in no_app:
            linhas.append(f"- {item['pagina_app']} — `{item['modulo']}.{item['funcao']}`")
    else:
        linhas.append("- Nenhuma página mapeada.")

    linhas.extend(["", "## Candidatos para recuperar depois", ""])

    if fora_app:
        for item in fora_app[:80]:
            linhas.append(f"- {item['sugestao_pagina']} — `{item['modulo']}.{item['funcao']}`")
    else:
        linhas.append("- Nenhum candidato fora do app seguro.")

    linhas.extend(
        [
            "",
            "## Diretriz técnica",
            "",
            "O app deve continuar usando navegação sob demanda. Páginas antigas devem ser adicionadas ao dicionário `PAGINAS` apenas quando forem úteis, testadas e leves.",
        ]
    )

    return "\n".join(linhas)


def salvar_relatorio_navegacao_segura_markdown(registros: List[Dict[str, Any]], caminho: Path = CAMINHO_RELATORIO) -> Path:
    caminho.write_text(gerar_relatorio_navegacao_segura_markdown(registros), encoding="utf-8")
    return caminho


def gerar_manifesto_navegacao_segura(registros: List[Dict[str, Any]]) -> Dict[str, Any]:
    metricas = calcular_saude_navegacao_segura(registros)
    return {
        "produto": "Valoris",
        "versao": VERSAO_NAVEGACAO_SEGURA_VALORIS,
        "modulo": "navegacao_segura_valoris",
        "data_hora": _agora_iso(),
        "metricas": metricas,
        "principio": "carregar uma página por vez, sem voltar ao modelo pesado de abas simultâneas",
    }


def salvar_manifesto_navegacao_segura(registros: List[Dict[str, Any]], caminho: Path = CAMINHO_MANIFESTO) -> Path:
    caminho.write_text(
        json.dumps(gerar_manifesto_navegacao_segura(registros), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return caminho


def salvar_decisao_navegacao_segura(decisao: str, modulo: str = "", funcao: str = "", observacao: str = "") -> Path:
    existe = CAMINHO_DECISOES.exists()

    with CAMINHO_DECISOES.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISOES)
        if not existe:
            escritor.writeheader()
        escritor.writerow(
            {
                "data_hora": _agora_iso(),
                "decisao": decisao,
                "modulo": modulo,
                "funcao": funcao,
                "observacao": observacao,
            }
        )

    return CAMINHO_DECISOES


def gerar_snippet_pagina(pagina: str, modulo: str, funcao: str) -> str:
    return (
        f'    "{pagina}": (\n'
        f'        "{modulo}",\n'
        f'        "{funcao}",\n'
        f'        "Página recuperada pelo catálogo de navegação segura.",\n'
        f'    ),'
    )


def renderizar_navegacao_segura_valoris() -> None:
    st.subheader("Navegação Segura e Catálogo de Módulos")
    st.caption(
        "Mapeia renderizadores existentes sem importar todos os módulos. "
        "Serve para recuperar páginas antigas mantendo o app leve."
    )

    registros = gerar_catalogo_navegacao_segura(Path("."))
    metricas = calcular_saude_navegacao_segura(registros)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Score", f"{metricas['score']}/100")
    col2.metric("Funções", metricas["total_funcoes"])
    col3.metric("Renderizadores", metricas["renderizadores"])
    col4.metric("No app seguro", metricas["no_app_seguro"])
    col5.metric("Fora do app", metricas["fora_do_app_seguro"])

    st.divider()

    termo = st.text_input("Buscar por página, módulo ou função", value="")
    apenas_fora = st.checkbox("Mostrar apenas renderizadores fora do app seguro", value=False)

    filtrados = registros

    if apenas_fora:
        filtrados = [r for r in filtrados if r.get("tipo") == "renderizador" and r.get("status_app") == "fora_do_app_seguro"]

    if termo.strip():
        termo_norm = termo.strip().lower()
        filtrados = [
            r
            for r in filtrados
            if termo_norm in " ".join(str(v).lower() for v in r.values())
        ]

    st.dataframe(filtrados, use_container_width=True, hide_index=True)

    csv_texto = ""
    if filtrados:
        import io

        buffer = io.StringIO()
        escritor = csv.DictWriter(buffer, fieldnames=CAMPOS_CATALOGO)
        escritor.writeheader()
        for item in filtrados:
            escritor.writerow({campo: item.get(campo, "") for campo in CAMPOS_CATALOGO})
        csv_texto = buffer.getvalue()

    st.download_button(
        "Baixar catálogo filtrado em CSV",
        data=csv_texto,
        file_name="catalogo_navegacao_segura_valoris.csv",
        mime="text/csv",
        disabled=not bool(filtrados),
    )

    st.divider()

    st.markdown("### Recuperar uma página com segurança")
    candidatos = [
        r for r in registros if r.get("tipo") == "renderizador" and r.get("status_app") == "fora_do_app_seguro"
    ]

    if candidatos:
        opcoes = [
            f"{r['sugestao_pagina']} — {r['modulo']}.{r['funcao']}"
            for r in candidatos
        ]
        escolha = st.selectbox("Escolha um candidato", opcoes)
        selecionado = candidatos[opcoes.index(escolha)]

        pagina_sugerida = st.text_input("Nome da página no app", value=selecionado["sugestao_pagina"])

        st.code(
            gerar_snippet_pagina(pagina_sugerida, selecionado["modulo"], selecionado["funcao"]),
            language="python",
        )

        if st.button("Registrar decisão de recuperar esta página"):
            salvar_decisao_navegacao_segura(
                decisao="candidata_para_recuperacao",
                modulo=selecionado["modulo"],
                funcao=selecionado["funcao"],
                observacao=f"Página sugerida: {pagina_sugerida}",
            )
            st.success("Decisão registrada.")
    else:
        st.info("Nenhum candidato fora do app seguro foi encontrado.")

    st.divider()

    col_a, col_b, col_c = st.columns(3)

    if col_a.button("Salvar catálogo CSV"):
        caminho = salvar_catalogo_navegacao_segura_csv(registros)
        st.success(f"Catálogo salvo em {caminho}")

    if col_b.button("Salvar relatório Markdown"):
        caminho = salvar_relatorio_navegacao_segura_markdown(registros)
        st.success(f"Relatório salvo em {caminho}")

    if col_c.button("Salvar manifesto JSON"):
        caminho = salvar_manifesto_navegacao_segura(registros)
        st.success(f"Manifesto salvo em {caminho}")


def executar_autoteste_navegacao_segura_valoris() -> Dict[str, Any]:
    registros = gerar_catalogo_navegacao_segura(Path("."))
    metricas = calcular_saude_navegacao_segura(registros)

    return {
        "ok": bool(registros),
        "versao": VERSAO_NAVEGACAO_SEGURA_VALORIS,
        "metricas": metricas,
    }
