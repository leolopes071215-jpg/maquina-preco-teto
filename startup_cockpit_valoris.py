# startup_cockpit_valoris.py
# Valoris — Cockpit como Página Inicial Oficial v3.11.3
# ------------------------------------------------------------
# Objetivo:
# - Validar se o Cockpit Principal está configurado como primeira experiência do app.
# - Conferir app.py, modo_exibicao.py e release_guard.py.
# - Gerar relatório de prontidão da entrada oficial.
# - Não substitui módulos: apenas governa a experiência inicial.

from __future__ import annotations

import ast
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


VERSAO_STARTUP_COCKPIT_VALORIS = "3.11.3"

PAGINA_OFICIAL = "Cockpit Principal"
MODULO_COCKPIT = "cockpit_principal_valoris"
FUNCAO_COCKPIT = "renderizar_cockpit_principal_valoris"

CAMINHO_RELATORIO = Path("RELATORIO_STARTUP_COCKPIT_VALORIS.md")
CAMINHO_MANIFESTO = Path("manifesto_startup_cockpit_valoris.json")


def _agora_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat(sep=" ")


def _ler(caminho: str | Path) -> str:
    caminho = Path(caminho)
    if not caminho.exists():
        return ""
    return caminho.read_text(encoding="utf-8", errors="replace")


def _literal_assign(caminho: str | Path, nome: str) -> Any:
    texto = _ler(caminho)

    if not texto:
        return None

    try:
        arvore = ast.parse(texto)
    except Exception:
        return None

    for node in ast.walk(arvore):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == nome:
                    try:
                        return ast.literal_eval(node.value)
                    except Exception:
                        return None

    return None


def validar_cockpit_em_paginas() -> Dict[str, Any]:
    paginas = _literal_assign("app.py", "PAGINAS")

    if not isinstance(paginas, dict):
        return {
            "ok": False,
            "primeira": "",
            "existe": False,
            "mensagem": "Não foi possível ler PAGINAS em app.py.",
        }

    chaves = list(paginas.keys())
    primeira = chaves[0] if chaves else ""

    entrada = paginas.get(PAGINA_OFICIAL)

    return {
        "ok": primeira == PAGINA_OFICIAL and PAGINA_OFICIAL in paginas,
        "primeira": primeira,
        "existe": PAGINA_OFICIAL in paginas,
        "entrada": entrada,
        "mensagem": "Cockpit é a primeira página de PAGINAS." if primeira == PAGINA_OFICIAL else "Cockpit ainda não é a primeira página de PAGINAS.",
    }


def validar_ordem_app() -> Dict[str, Any]:
    ordem = _literal_assign("app.py", "ABAS_ORDEM_COMPLETA")

    if not isinstance(ordem, list):
        return {
            "ok": False,
            "primeira": "",
            "existe": False,
            "mensagem": "Não foi possível ler ABAS_ORDEM_COMPLETA em app.py.",
        }

    primeira = ordem[0] if ordem else ""

    return {
        "ok": primeira == PAGINA_OFICIAL and PAGINA_OFICIAL in ordem,
        "primeira": primeira,
        "existe": PAGINA_OFICIAL in ordem,
        "mensagem": "Cockpit é a primeira aba da ordem completa." if primeira == PAGINA_OFICIAL else "Cockpit ainda não é a primeira aba da ordem completa.",
    }


def validar_modo_fundador() -> Dict[str, Any]:
    ordem = _literal_assign("modo_exibicao.py", "ABAS_MODO_FUNDADOR")

    if not isinstance(ordem, list):
        return {
            "ok": False,
            "primeira": "",
            "existe": False,
            "mensagem": "Não foi possível ler ABAS_MODO_FUNDADOR em modo_exibicao.py.",
        }

    primeira = ordem[0] if ordem else ""

    return {
        "ok": primeira == PAGINA_OFICIAL and PAGINA_OFICIAL in ordem,
        "primeira": primeira,
        "existe": PAGINA_OFICIAL in ordem,
        "mensagem": "Cockpit é a primeira aba do modo fundador." if primeira == PAGINA_OFICIAL else "Cockpit ainda não é a primeira aba do modo fundador.",
    }


def validar_release_guard() -> Dict[str, Any]:
    texto = _ler("release_guard.py")

    if not texto:
        return {
            "ok": False,
            "versao_ok": False,
            "arquivo_ok": False,
            "mensagem": "release_guard.py não encontrado.",
        }

    versao_ok = 'VERSAO_RELEASE_GUARD = "3.11.3"' in texto
    arquivo_ok = '"startup_cockpit_valoris.py"' in texto and '"cockpit_principal_valoris.py"' in texto

    return {
        "ok": versao_ok and arquivo_ok,
        "versao_ok": versao_ok,
        "arquivo_ok": arquivo_ok,
        "mensagem": "Release Guard reconhece a entrada oficial." if versao_ok and arquivo_ok else "Release Guard ainda precisa reconhecer a entrada oficial.",
    }


def calcular_metricas_startup_cockpit() -> Dict[str, Any]:
    check_paginas = validar_cockpit_em_paginas()
    check_ordem = validar_ordem_app()
    check_modo = validar_modo_fundador()
    check_release = validar_release_guard()

    checks = [check_paginas, check_ordem, check_modo, check_release]
    ok = len([item for item in checks if item.get("ok")])

    score = int(round((ok / len(checks)) * 100)) if checks else 0

    if score == 100:
        status = "Pronto"
        decisao = "Cockpit Principal configurado como página inicial oficial"
        proximo = "Usar o Cockpit como entrada do produto e evoluir alertas automáticos."
    elif score >= 75:
        status = "Quase pronto"
        decisao = "Cockpit quase configurado como entrada oficial"
        proximo = "Ajustar os itens pendentes antes de fechar a versão."
    else:
        status = "Atenção"
        decisao = "Cockpit ainda não está consolidado como entrada oficial"
        proximo = "Reaplicar patch v3.11.3 e validar app.py, modo_exibicao.py e release_guard.py."

    return {
        "versao": VERSAO_STARTUP_COCKPIT_VALORIS,
        "gerado_em": _agora_iso(),
        "score_startup": score,
        "status": status,
        "checks_ok": ok,
        "checks_total": len(checks),
        "decisao": decisao,
        "proximo_passo": proximo,
        "checks": {
            "paginas": check_paginas,
            "ordem_app": check_ordem,
            "modo_fundador": check_modo,
            "release_guard": check_release,
        },
    }


def gerar_relatorio_startup_cockpit_markdown() -> str:
    metricas = calcular_metricas_startup_cockpit()

    linhas = "\n".join(
        [
            f"- **{nome}**: {'OK' if dados.get('ok') else 'Atenção'} — {dados.get('mensagem')}"
            for nome, dados in metricas["checks"].items()
        ]
    )

    return f"""# Cockpit como Página Inicial Oficial — Valoris

Versão: {VERSAO_STARTUP_COCKPIT_VALORIS}  
Gerado em: {_agora_iso()}

## Diagnóstico

Score startup: {metricas['score_startup']}/100  
Status: {metricas['status']}  
Checks OK: {metricas['checks_ok']}/{metricas['checks_total']}  

Decisão: {metricas['decisao']}  
Próximo passo: {metricas['proximo_passo']}

## Checks

{linhas}

## Estratégia

O Valoris agora deve abrir pela tela que melhor resume o produto: o Cockpit Principal. Isso transforma a primeira impressão do usuário, reduz fricção, aumenta clareza e cria uma jornada mais profissional.
"""


def salvar_relatorio_startup_cockpit() -> Path:
    CAMINHO_RELATORIO.write_text(gerar_relatorio_startup_cockpit_markdown(), encoding="utf-8")
    return CAMINHO_RELATORIO


def gerar_manifesto_startup_cockpit() -> Dict[str, Any]:
    return {
        "produto": "Valoris",
        "versao": VERSAO_STARTUP_COCKPIT_VALORIS,
        "modulo": "startup_cockpit_valoris",
        "data_hora": _agora_iso(),
        "metricas": calcular_metricas_startup_cockpit(),
        "pagina_oficial": PAGINA_OFICIAL,
        "principio": "a primeira tela deve entregar clareza executiva em poucos segundos",
        "proxima_etapa": "alertas automáticos a partir do Radar Principal",
    }


def salvar_manifesto_startup_cockpit() -> Path:
    CAMINHO_MANIFESTO.write_text(
        json.dumps(gerar_manifesto_startup_cockpit(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return CAMINHO_MANIFESTO


def executar_autoteste_startup_cockpit_valoris() -> Dict[str, Any]:
    metricas = calcular_metricas_startup_cockpit()

    return {
        "ok": metricas["score_startup"] == 100,
        "versao": VERSAO_STARTUP_COCKPIT_VALORIS,
        "metricas": {
            "score_startup": metricas["score_startup"],
            "status": metricas["status"],
            "checks_ok": metricas["checks_ok"],
            "checks_total": metricas["checks_total"],
        },
    }


if __name__ == "__main__":
    metricas = calcular_metricas_startup_cockpit()
    print(json.dumps(metricas, ensure_ascii=False, indent=2))
