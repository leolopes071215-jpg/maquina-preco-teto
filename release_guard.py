# release_guard.py

from __future__ import annotations

import argparse
import os
import py_compile
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional


# ============================================================
# VALORIS
# v3.8.53 — Guardião de Release com central de fundadores
# ------------------------------------------------------------
# Este script ajuda a proteger o projeto antes de fechar versão.
#
# Ele verifica:
# - arquivos Python que não compilam;
# - arquivos temporários/versionados que não deveriam ficar no projeto;
# - CSVs locais que devem ficar fora do Git;
# - presença de arquivos essenciais;
# - estado básico do repositório Git.
#
# Uso recomendado antes de cada commit:
#
# python release_guard.py
#
# Uso mais completo:
#
# python release_guard.py --strict
# ============================================================


VERSAO_RELEASE_GUARD = "3.8.53"


ARQUIVOS_ESSENCIAIS = [
    "app.py",
    "style.py",
    "valuation.py",
    "modo_exibicao.py",
    "experiencia_beta.py",
    "explicabilidade_valoris.py",
    "lista_espera_beta.py",
    "oferta_beta.py",
    "oferta_beta_pago.py",
    "landing_page_beta.py",
    "convite_beta_publico.py",
    "hub_ativacao_valoris.py",
    "conversao_fundador_valoris.py",
    "laboratorio_growth_valoris.py",
    "central_fundadores_valoris.py",
    "validacao_manual_valoris.py",
    "jornada_personalizada_valoris.py",
    "copiloto_valoris.py",
    "trilha_educativa_valoris.py",
    "demo_guiada_valoris.py",
    "analytics_publico_valoris.py",
    "relatorio.py",
    "central_relatorios.py",
]


CSV_LOCAIS_ESPERADOS_NO_GITIGNORE = [
    "lista_espera_beta.csv",
    "ofertas_beta_pago.csv",
    "feedback_beta.csv",
    "logs_motor_valuation.csv",
    "metricas_fase3.csv",
    "decisoes_fase3.csv",
    "clientes_beta.csv",
    "crm_beta.csv",
    "watchlist_multiativos.csv",
    "historico.csv",
    "historico_analises.csv",
    "ativacao_valoris.csv",
    "sinais_conversao_valoris.csv",
    "experimentos_growth_valoris.csv",
    "fundadores_valoris.csv",
    "validacoes_manuais_valoris.csv",
    "jornadas_personalizadas_valoris.csv",
    "diagnosticos_copiloto_valoris.csv",
    "progresso_trilha_valoris.csv",
    "eventos_publicos_valoris.csv",
]


PASTAS_IGNORADAS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".streamlit",
    ".pytest_cache",
    ".mypy_cache",
    "node_modules",
    "dist",
    "build",
}


@dataclass
class ResultadoChecagem:
    nome: str
    ok: bool
    detalhes: List[str]

    def status_texto(self) -> str:
        return "OK" if self.ok else "FALHA"


def _executar_comando(comando: List[str]) -> tuple[int, str, str]:
    try:
        processo = subprocess.run(
            comando,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        return processo.returncode, processo.stdout.strip(), processo.stderr.strip()

    except FileNotFoundError as erro:
        return 127, "", str(erro)


def _iterar_arquivos_python(raiz: Path) -> Iterable[Path]:
    for caminho in raiz.rglob("*.py"):
        partes = set(caminho.parts)

        if partes.intersection(PASTAS_IGNORADAS):
            continue

        yield caminho


def _eh_arquivo_versionado_temporario(caminho: Path) -> bool:
    nome = caminho.name.lower()

    if "_v3_" in nome:
        return True

    if "_v4_" in nome:
        return True

    if nome.startswith("codigo colado"):
        return True

    if nome.startswith("código colado"):
        return True

    if nome.startswith("copy of "):
        return True

    return False


def verificar_arquivos_essenciais(raiz: Path) -> ResultadoChecagem:
    faltando = []

    for nome_arquivo in ARQUIVOS_ESSENCIAIS:
        if not (raiz / nome_arquivo).exists():
            faltando.append(nome_arquivo)

    detalhes = []

    if faltando:
        detalhes.append("Arquivos essenciais ausentes:")
        detalhes.extend([f"- {item}" for item in faltando])
    else:
        detalhes.append("Todos os arquivos essenciais foram encontrados.")

    return ResultadoChecagem(
        nome="Arquivos essenciais",
        ok=len(faltando) == 0,
        detalhes=detalhes,
    )


def verificar_compilacao_python(raiz: Path) -> ResultadoChecagem:
    erros = []
    arquivos_verificados = 0

    for caminho in _iterar_arquivos_python(raiz):
        arquivos_verificados += 1

        try:
            py_compile.compile(
                str(caminho),
                doraise=True,
            )
        except py_compile.PyCompileError as erro:
            erros.append(f"{caminho}: {erro.msg}")

    detalhes = [f"Arquivos Python verificados: {arquivos_verificados}"]

    if erros:
        detalhes.append("Arquivos com erro de compilação:")
        detalhes.extend([f"- {erro}" for erro in erros[:20]])

        if len(erros) > 20:
            detalhes.append(f"... e mais {len(erros) - 20} erro(s).")
    else:
        detalhes.append("Nenhum erro de compilação encontrado.")

    return ResultadoChecagem(
        nome="Compilação Python",
        ok=len(erros) == 0,
        detalhes=detalhes,
    )


def verificar_arquivos_temporarios(raiz: Path) -> ResultadoChecagem:
    suspeitos = []

    for caminho in raiz.iterdir():
        if not caminho.is_file():
            continue

        if _eh_arquivo_versionado_temporario(caminho):
            suspeitos.append(caminho.name)

    detalhes = []

    if suspeitos:
        detalhes.append("Arquivos temporários/versionados encontrados na raiz do projeto:")
        detalhes.extend([f"- {item}" for item in suspeitos])
        detalhes.append("Recomendação: mantenha apenas nomes finais como app.py, style.py, oferta_beta.py etc.")
    else:
        detalhes.append("Nenhum arquivo temporário/versionado encontrado na raiz.")

    return ResultadoChecagem(
        nome="Arquivos temporários",
        ok=len(suspeitos) == 0,
        detalhes=detalhes,
    )


def verificar_gitignore_csvs(raiz: Path) -> ResultadoChecagem:
    caminho_gitignore = raiz / ".gitignore"

    if not caminho_gitignore.exists():
        return ResultadoChecagem(
            nome="Gitignore de dados locais",
            ok=False,
            detalhes=[".gitignore não encontrado."],
        )

    conteudo = caminho_gitignore.read_text(encoding="utf-8", errors="ignore")

    ausentes = [
        item for item in CSV_LOCAIS_ESPERADOS_NO_GITIGNORE
        if item not in conteudo
    ]

    detalhes = []

    if ausentes:
        detalhes.append("CSVs locais recomendados ausentes do .gitignore:")
        detalhes.extend([f"- {item}" for item in ausentes])
    else:
        detalhes.append("Principais CSVs locais aparecem no .gitignore.")

    return ResultadoChecagem(
        nome="Gitignore de dados locais",
        ok=len(ausentes) == 0,
        detalhes=detalhes,
    )


def verificar_csvs_rastreados_pelo_git(raiz: Path) -> ResultadoChecagem:
    codigo, stdout, stderr = _executar_comando(
        ["git", "ls-files", "*.csv"]
    )

    if codigo != 0:
        return ResultadoChecagem(
            nome="CSVs rastreados pelo Git",
            ok=False,
            detalhes=[
                "Não foi possível consultar arquivos rastreados pelo Git.",
                stderr or stdout or "Sem detalhe.",
            ],
        )

    arquivos = [linha.strip() for linha in stdout.splitlines() if linha.strip()]

    csvs_locais_rastreados = [
        arquivo for arquivo in arquivos
        if Path(arquivo).name in CSV_LOCAIS_ESPERADOS_NO_GITIGNORE
    ]

    detalhes = []

    if csvs_locais_rastreados:
        detalhes.append("Atenção: CSVs locais aparecem rastreados pelo Git:")
        detalhes.extend([f"- {item}" for item in csvs_locais_rastreados])
        detalhes.append("Recomendação: remover do índice com git rm --cached <arquivo>.")
    else:
        detalhes.append("Nenhum CSV local crítico aparece rastreado pelo Git.")

    return ResultadoChecagem(
        nome="CSVs rastreados pelo Git",
        ok=len(csvs_locais_rastreados) == 0,
        detalhes=detalhes,
    )


def verificar_estado_git() -> ResultadoChecagem:
    codigo, stdout, stderr = _executar_comando(
        ["git", "status", "--short"]
    )

    if codigo != 0:
        return ResultadoChecagem(
            nome="Estado Git",
            ok=False,
            detalhes=[
                "Não foi possível executar git status.",
                stderr or stdout or "Sem detalhe.",
            ],
        )

    linhas = [linha for linha in stdout.splitlines() if linha.strip()]

    detalhes = []

    if linhas:
        detalhes.append("Há alterações pendentes no Git:")
        detalhes.extend([f"- {linha}" for linha in linhas[:30]])

        if len(linhas) > 30:
            detalhes.append(f"... e mais {len(linhas) - 30} alteração(ões).")
    else:
        detalhes.append("Git limpo. Nenhuma alteração pendente.")

    return ResultadoChecagem(
        nome="Estado Git",
        ok=True,
        detalhes=detalhes,
    )


def verificar_imports_criticos(raiz: Path) -> ResultadoChecagem:
    imports_criticos = {
        "lista_espera_beta.py": [
            "renderizar_lista_espera_valoris",
            "carregar_leads_lista_espera",
            "gerar_csv_lista_espera",
        ],
        "oferta_beta.py": [
            "renderizar_oferta_beta",
            "carregar_lista_espera",
        ],
        "experiencia_beta.py": [
            "renderizar_experiencia_usuario_beta",
        ],
        "landing_page_beta.py": [
            "renderizar_landing_page_beta",
        ],
        "convite_beta_publico.py": [
            "renderizar_convite_beta_publico",
        ],
        "hub_ativacao_valoris.py": [
            "renderizar_hub_ativacao_valoris",
            "renderizar_painel_hub_ativacao_valoris",
        ],
        "conversao_fundador_valoris.py": [
            "renderizar_conversao_fundador_valoris",
            "renderizar_painel_conversao_fundador_valoris",
        ],
        "laboratorio_growth_valoris.py": [
            "renderizar_laboratorio_growth_valoris",
        ],
        "validacao_manual_valoris.py": [
            "renderizar_validacao_manual_valoris",
        ],
        "central_fundadores_valoris.py": [
            "renderizar_central_fundadores_valoris",
        ],
    }

    problemas = []

    for arquivo, termos in imports_criticos.items():
        caminho = raiz / arquivo

        if not caminho.exists():
            problemas.append(f"{arquivo}: arquivo não encontrado.")
            continue

        conteudo = caminho.read_text(encoding="utf-8", errors="ignore")

        for termo in termos:
            if f"def {termo}" not in conteudo:
                problemas.append(f"{arquivo}: função esperada não encontrada: {termo}")

    detalhes = []

    if problemas:
        detalhes.append("Problemas em imports/funções críticas:")
        detalhes.extend([f"- {item}" for item in problemas])
    else:
        detalhes.append("Funções críticas encontradas nos módulos principais.")

    return ResultadoChecagem(
        nome="Imports críticos",
        ok=len(problemas) == 0,
        detalhes=detalhes,
    )


def imprimir_resultado(resultado: ResultadoChecagem) -> None:
    marcador = "✅" if resultado.ok else "❌"

    print(f"\n{marcador} {resultado.nome}: {resultado.status_texto()}")

    for detalhe in resultado.detalhes:
        print(f"   {detalhe}")


def executar_guardiao_release(strict: bool = False) -> int:
    raiz = Path.cwd()

    print(f"Valoris Release Guard v{VERSAO_RELEASE_GUARD}")
    print(f"Pasta analisada: {raiz}")

    checagens = [
        verificar_arquivos_essenciais(raiz),
        verificar_imports_criticos(raiz),
        verificar_compilacao_python(raiz),
        verificar_arquivos_temporarios(raiz),
        verificar_gitignore_csvs(raiz),
        verificar_csvs_rastreados_pelo_git(raiz),
        verificar_estado_git(),
    ]

    for checagem in checagens:
        imprimir_resultado(checagem)

    falhas = [checagem for checagem in checagens if not checagem.ok]

    if falhas:
        print("\n❌ Release Guard encontrou problemas que merecem revisão.")

        if strict:
            return 1

        print("Modo normal: problemas foram reportados, mas o script não bloqueou a execução.")
        return 0

    print("\n✅ Release Guard concluído sem falhas críticas.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Guardião de release da Valoris."
    )

    parser.add_argument(
        "--strict",
        action="store_true",
        help="Retorna erro se qualquer checagem falhar.",
    )

    args = parser.parse_args()

    codigo_saida = executar_guardiao_release(strict=args.strict)

    sys.exit(codigo_saida)


if __name__ == "__main__":
    main()
