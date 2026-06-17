# release_guard.py

from __future__ import annotations

import argparse
import ast
import os
import py_compile
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional


# ============================================================
# VALORIS
# v3.8.91 — Guardião com Estabilidade de Execução e Validação Leve
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


VERSAO_RELEASE_GUARD = "3.10.4"


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
    "maturidade_produto_valoris.py",
    "arquitetura_transicao_valoris.py",
    "camada_dados_valoris.py",
    "gateway_dados_valoris.py",
    "piloto_sqlite_valoris.py",
    "repositorios_valoris.py",
    "postgres_supabase_valoris.py",
    "api_contratos_valoris.py",
    "api_scaffold_valoris.py",
    "api_smoke_tests_valoris.py",
    "api_repository_bridge_valoris.py",
    "api_endpoint_tests_valoris.py",
    "api_sqlite_bridge_valoris.py",
    "api_storage_adapter_valoris.py",
    "api_security_key_valoris.py",
    "api_security_panel_valoris.py",
    "api_database_cloud_valoris.py",
    "api_database_contracts_valoris.py",
    "api_database_providers_valoris.py",
    "api_provider_runtime_valoris.py",
    "api_provider_backend_valoris.py",
    "launch_readiness_valoris.py",
    "analise_premium_valoris.py",
    "demo_guiada_2min_valoris.py",
    "beta_feedback_valoris.py",
    "beta_insights_valoris.py",
    "onboarding_premium_valoris.py",
    "beta_publico_valoris.py",
    "oferta_beta_fundador_valoris.py",
    "checkout_fundadores_valoris.py",
    "retencao_fundadores_valoris.py",
    "watchlist_fundadores_valoris.py",
    "comparador_setorial_valoris.py",
    "relatorio_premium_v2_valoris.py",
    "pacote_premium_valoris.py",
    "feedback_pacote_premium_valoris.py",
    "roadmap_premium_valoris.py",
    "estabilidade_execucao_valoris.py",
    "navegacao_segura_valoris.py",
    "recuperacao_paginas_valoris.py",
    "motor_analise_ativos_valoris.py",
    "historico_analises_valoris.py",
    "integracao_motor_watchlist_valoris.py",
    "integracao_motor_relatorio_valoris.py",
    "analise_inteligente_valoris.py",
    "pipeline_decisao_valoris.py",
    "radar_revisoes_valoris.py",
    "mapa_dados_contratos_valoris.py",
    "repositorio_unico_valoris.py",
    "simulador_migracao_banco_valoris.py",
    "sqlite_local_valoris.py",
    "repository_backend_sqlite_valoris.py",
    "healthcheck_banco_repository_valoris.py",
    "migracao_paginas_backend_valoris.py",
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
    "decisoes_maturidade_valoris.csv",
    "decisoes_arquitetura_valoris.csv",
    "decisoes_dados_valoris.csv",
    "logs_gateway_dados_valoris.csv",
    "valoris_local_piloto.db",
    "manifesto_sqlite_valoris.json",
    "manifesto_repositorios_valoris.json",
    "valoris_schema_postgres_supabase.sql",
    "valoris_fastapi_blueprint.py",
    "api_valoris/",
    "scripts_api_valoris/",
    "manifesto_api_bridge_valoris.json",
    "relatorio_api_tests_valoris.json",
    "valoris_api_local.sqlite3",
    "manifesto_api_sqlite_valoris.json",
    "manifesto_api_adapter_valoris.json",
    "manifesto_api_security_valoris.json",
    "manifesto_api_security_panel_valoris.json",
    "manifesto_api_database_cloud_valoris.json",
    "manifesto_api_database_contracts_valoris.json",
    "manifesto_api_database_providers_valoris.json",
    "manifesto_api_provider_runtime_valoris.json",
    "manifesto_api_provider_backend_valoris.json",
    "manifesto_launch_readiness_valoris.json",
    "manifesto_analise_premium_valoris.json",
    "manifesto_demo_2min_valoris.json",
    "manifesto_beta_feedback_valoris.json",
    "manifesto_beta_insights_valoris.json",
    "manifesto_onboarding_premium_valoris.json",
    "manifesto_beta_publico_valoris.json",
    "manifesto_oferta_beta_fundador_valoris.json",
    "manifesto_checkout_fundadores_valoris.json",
    "manifesto_retencao_fundadores_valoris.json",
    "manifesto_watchlist_fundadores_valoris.json",
    "manifesto_comparador_setorial_valoris.json",
    "manifesto_relatorio_premium_v2_valoris.json",
    "manifesto_pacote_premium_valoris.json",
    "manifesto_feedback_pacote_premium_valoris.json",
    "manifesto_roadmap_premium_valoris.json",
    "manifesto_estabilidade_execucao_valoris.json",
    "validacao_leve_valoris.json",
    "logs_*_backup_*.csv",
    "BLUEPRINT_DATABASE_CLOUD_VALORIS.md",
    "CONTRATOS_DATABASE_VALORIS.md",
    "PROVIDERS_DATABASE_VALORIS.md",
    "PROVIDER_RUNTIME_VALORIS.md",
    "PROVIDER_BACKEND_VALORIS.md",
    "PLANO_LANCAMENTO_VALORIS.md",
    "RELATORIO_ANALISE_PREMIUM_VALORIS.md",
    "ROTEIRO_DEMO_2MIN_VALORIS.md",
    "ROTEIRO_BETA_TESTER_VALORIS.md",
    "FORMULARIO_FEEDBACK_BETA_VALORIS.md",
    "PLANO_BETA_FEEDBACK_VALORIS.md",
    "INSIGHTS_BETA_VALORIS.md",
    "ROADMAP_PRIORIZADO_VALORIS.md",
    "ROTEIRO_ONBOARDING_PREMIUM_VALORIS.md",
    "COPY_BETA_PUBLICO_VALORIS.md",
    "COPY_OFERTA_BETA_FUNDADOR_VALORIS.md",
    "PAGINA_BETA_PUBLICO_VALORIS.md",
    "PAGINA_OFERTA_BETA_FUNDADOR_VALORIS.md",
    "CHECKLIST_BETA_PUBLICO_VALORIS.md",
    "CHECKLIST_OFERTA_BETA_FUNDADOR_VALORIS.md",
    "EXPERIMENTO_PRECO_BETA_FUNDADOR_VALORIS.md",
    "ROTEIRO_CHECKOUT_MANUAL_FUNDADORES_VALORIS.md",
    "PLAYBOOK_RETENCAO_FUNDADORES_VALORIS.md",
    "CHECKLIST_RETENCAO_FUNDADORES_VALORIS.md",
    "RELATORIO_RETENCAO_FUNDADORES_VALORIS.md",
    "RELATORIO_WATCHLIST_FUNDADORES_VALORIS.md",
    "RELATORIO_COMPARADOR_SETORIAL_VALORIS.md",
    "DOSSIE_PREMIUM_V2_VALORIS.md",
    "PACOTE_PREMIUM_VALORIS.md",
    "MATRIZ_MELHORIAS_PACOTE_PREMIUM_VALORIS.md",
    "ROADMAP_PREMIUM_VALORIS.md",
    "RELATORIO_ESTABILIDADE_EXECUCAO_VALORIS.md",
    "SPRINT_PLANNING_PREMIUM_VALORIS.md",
    "ROTEIRO_FEEDBACK_PACOTE_PREMIUM_VALORIS.md",
    "CHECKLIST_FEEDBACK_PACOTE_PREMIUM_VALORIS.md",
    "CHECKLIST_ROADMAP_PREMIUM_VALORIS.md",
    "CHECKLIST_ESTABILIDADE_EXECUCAO_VALORIS.md",
    "SUMARIO_EXECUTIVO_PACOTE_PREMIUM_VALORIS.md",
    "PLAYBOOK_WATCHLIST_FUNDADORES_VALORIS.md",
    "PLAYBOOK_COMPARADOR_SETORIAL_VALORIS.md",
    "PLAYBOOK_RELATORIO_PREMIUM_V2_VALORIS.md",
    "PLAYBOOK_PACOTE_PREMIUM_VALORIS.md",
    "CHECKLIST_WATCHLIST_FUNDADORES_VALORIS.md",
    "CHECKLIST_COMPARADOR_SETORIAL_VALORIS.md",
    "CHECKLIST_RELATORIO_PREMIUM_V2_VALORIS.md",
    "CHECKLIST_PACOTE_PREMIUM_VALORIS.md",
    "pacote_premium_valoris.zip",
    "CHECKLIST_CHECKOUT_FUNDADORES_VALORIS.md",
    "TERMO_BETA_FUNDADOR_VALORIS.md",
    "pipeline_fundadores_valoris.json",
    "CHECKLIST_ONBOARDING_PREMIUM_VALORIS.md",
    "matriz_prioridade_beta_valoris.csv",
    "CHECKLIST_DEMO_2MIN_VALORIS.md",
    "demo_analise_premium_valoris.json",
    "CHECKLIST_LANCAMENTO_VALORIS.md",
    "relatorio_provider_runtime_valoris.json",
    "relatorio_provider_backend_valoris.json",
    "scripts_api_valoris/testar_provider_runtime_valoris.py",
    "scripts_api_valoris/testar_provider_backend_valoris.py",
    "api_valoris/app/services/database_providers.py",
    "api_valoris/app/services/provider_factory.py",
    "api_valoris/app/services/provider_runtime_bridge.py",
    "manifesto_api_tests_valoris.json",
    "manifesto_api_smoke_valoris.json",
    "manifesto_api_scaffold_valoris.json",
    "openapi_valoris_rascunho.json",
    "manifesto_api_valoris.json",
    ".env.example.valoris",
    "manifesto_postgres_supabase_valoris.json",
    "logs_sqlite_valoris.csv",
    "logs_repositorios_valoris.csv",
    "decisoes_postgres_supabase_valoris.csv",
    "decisoes_api_valoris.csv",
    "decisoes_api_scaffold_valoris.csv",
    "decisoes_api_smoke_valoris.csv",
    "decisoes_api_bridge_valoris.csv",
    "decisoes_api_tests_valoris.csv",
    "decisoes_api_sqlite_valoris.csv",
    "decisoes_api_adapter_valoris.csv",
    "decisoes_api_security_valoris.csv",
    "decisoes_api_security_panel_valoris.csv",
    "decisoes_api_database_cloud_valoris.csv",
    "decisoes_api_database_contracts_valoris.csv",
    "decisoes_api_database_providers_valoris.csv",
    "decisoes_api_provider_runtime_valoris.csv",
    "decisoes_api_provider_backend_valoris.csv",
    "decisoes_launch_readiness_valoris.csv",
    "decisoes_analise_premium_valoris.csv",
    "decisoes_demo_2min_valoris.csv",
    "feedback_beta_valoris.csv",
    "decisoes_beta_feedback_valoris.csv",
    "decisoes_beta_insights_valoris.csv",
    "decisoes_onboarding_premium_valoris.csv",
    "leads_beta_publico_valoris.csv",
    "interesses_oferta_beta_fundador_valoris.csv",
    "fundadores_beta_valoris.csv",
    "ativacoes_fundadores_valoris.csv",
    "watchlist_fundadores_valoris.csv",
    "ranking_comparador_setorial_valoris.csv",
    "alertas_watchlist_fundadores_valoris.csv",
    "feedbacks_pos_pagamento_valoris.csv",
    "decisoes_beta_publico_valoris.csv",
    "decisoes_oferta_beta_fundador_valoris.csv",
    "decisoes_checkout_fundadores_valoris.csv",
    "decisoes_retencao_fundadores_valoris.csv",
    "decisoes_watchlist_fundadores_valoris.csv",
    "decisoes_comparador_setorial_valoris.csv",
    "decisoes_relatorio_premium_v2_valoris.csv",
    "decisoes_pacote_premium_valoris.csv",
    "feedbacks_pacote_premium_valoris.csv",
    "backlog_roadmap_premium_valoris.csv",
    "decisoes_feedback_pacote_premium_valoris.csv",
    "decisoes_roadmap_premium_valoris.csv",
    "decisoes_estabilidade_execucao_valoris.csv",
    "decisoes_repositorios_valoris.csv",
    "decisoes_sqlite_valoris.csv",
    "decisoes_gateway_dados_valoris.csv",
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



def _extrair_lista_literal_python(caminho: Path, nome_variavel: str) -> List[str]:
    try:
        arvore = ast.parse(caminho.read_text(encoding="utf-8"))
    except Exception:
        return []

    for no in arvore.body:
        if not isinstance(no, ast.Assign):
            continue

        for alvo in no.targets:
            if isinstance(alvo, ast.Name) and alvo.id == nome_variavel:
                try:
                    valor = ast.literal_eval(no.value)
                except Exception:
                    return []

                if isinstance(valor, list):
                    return [str(item) for item in valor]

    return []




def _extrair_chaves_dict_literal_python(caminho: Path, nome_variavel: str) -> List[str]:
    try:
        arvore = ast.parse(caminho.read_text(encoding="utf-8"))
    except Exception:
        return []

    for node in ast.walk(arvore):
        if isinstance(node, ast.Assign):
            nomes = [
                alvo.id
                for alvo in node.targets
                if isinstance(alvo, ast.Name)
            ]

            if nome_variavel in nomes and isinstance(node.value, ast.Dict):
                chaves = []

                for chave in node.value.keys:
                    if isinstance(chave, ast.Constant) and isinstance(chave.value, str):
                        chaves.append(chave.value)

                return chaves

    return []

def verificar_abas_fundador_renderizaveis(raiz: Path) -> ResultadoChecagem:
    caminho_app = raiz / "app.py"
    caminho_modo = raiz / "modo_exibicao.py"

    detalhes: List[str] = []

    abas_ordem = _extrair_lista_literal_python(caminho_app, "ABAS_ORDEM_COMPLETA")
    paginas_app = _extrair_chaves_dict_literal_python(caminho_app, "PAGINAS")

    if paginas_app:
        abas_ordem = list(dict.fromkeys([*paginas_app, *(abas_ordem or [])]))

    abas_fundador = _extrair_lista_literal_python(caminho_modo, "ABAS_MODO_FUNDADOR")

    if not abas_fundador:
        abas_fundador = _extrair_lista_literal_python(caminho_modo, "ABAS_FUNDADOR")

    if not abas_ordem:
        return ResultadoChecagem(
            nome="Abas renderizáveis",
            ok=False,
            detalhes=["Não foi possível ler ABAS_ORDEM_COMPLETA em app.py."],
        )

    if not abas_fundador:
        return ResultadoChecagem(
            nome="Abas renderizáveis",
            ok=False,
            detalhes=["Não foi possível ler ABAS_FUNDADOR em modo_exibicao.py."],
        )

    ausentes = [aba for aba in abas_fundador if aba not in abas_ordem]

    if ausentes:
        detalhes.append("Abas do modo fundador ausentes em ABAS_ORDEM_COMPLETA:")
        detalhes.extend([f"- {aba}" for aba in ausentes])
    else:
        detalhes.append("Todas as abas do modo fundador estão na ordem global de renderização.")

    return ResultadoChecagem(
        nome="Abas renderizáveis",
        ok=len(ausentes) == 0,
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
        "maturidade_produto_valoris.py": [
            "renderizar_maturidade_produto_valoris",
        ],
        "arquitetura_transicao_valoris.py": [
            "renderizar_arquitetura_transicao_valoris",
        ],
        "camada_dados_valoris.py": [
            "renderizar_camada_dados_valoris",
        ],
        "gateway_dados_valoris.py": [
            "renderizar_gateway_dados_valoris",
        ],
        "piloto_sqlite_valoris.py": [
            "renderizar_piloto_sqlite_valoris",
        ],
        "repositorios_valoris.py": [
            "renderizar_repositorios_valoris",
        ],
        "postgres_supabase_valoris.py": [
            "renderizar_postgres_supabase_valoris",
        ],
        "api_contratos_valoris.py": [
            "renderizar_api_contratos_valoris",
        ],
        "api_scaffold_valoris.py": [
            "renderizar_api_scaffold_valoris",
        ],
        "api_smoke_tests_valoris.py": [
            "renderizar_api_smoke_tests_valoris",
        ],
        "api_repository_bridge_valoris.py": [
            "renderizar_api_repository_bridge_valoris",
        ],
        "api_endpoint_tests_valoris.py": [
            "renderizar_api_endpoint_tests_valoris",
        ],
        "api_sqlite_bridge_valoris.py": [
            "renderizar_api_sqlite_bridge_valoris",
        ],
        "api_storage_adapter_valoris.py": [
            "renderizar_api_storage_adapter_valoris",
        ],
        "api_security_key_valoris.py": [
            "renderizar_api_security_key_valoris",
        ],
        "api_security_panel_valoris.py": [
            "renderizar_api_security_panel_valoris",
        ],
        "api_database_cloud_valoris.py": [
            "renderizar_api_database_cloud_valoris",
        ],
        "api_database_contracts_valoris.py": [
            "renderizar_api_database_contracts_valoris",
        ],
        "api_database_providers_valoris.py": [
            "renderizar_api_database_providers_valoris",
        ],
        "api_provider_runtime_valoris.py": [
            "renderizar_api_provider_runtime_valoris",
        ],
        "api_provider_backend_valoris.py": [
            "renderizar_api_provider_backend_valoris",
        ],
        "launch_readiness_valoris.py": [
            "renderizar_launch_readiness_valoris",
        ],
        "analise_premium_valoris.py": [
            "renderizar_analise_premium_valoris",
        ],
        "demo_guiada_2min_valoris.py": [
            "renderizar_demo_guiada_2min_valoris",
        ],
        "beta_feedback_valoris.py": [
            "renderizar_beta_feedback_valoris",
        ],
        "beta_insights_valoris.py": [
            "renderizar_beta_insights_valoris",
        ],
        "onboarding_premium_valoris.py": [
            "renderizar_onboarding_premium_valoris",
        ],
        "beta_publico_valoris.py": [
            "renderizar_beta_publico_valoris",
        ],
        "oferta_beta_fundador_valoris.py": [
            "renderizar_oferta_beta_fundador_valoris",
        ],
        "checkout_fundadores_valoris.py": [
            "renderizar_checkout_fundadores_valoris",
        ],
        "retencao_fundadores_valoris.py": [
            "renderizar_retencao_fundadores_valoris",
        ],
        "watchlist_fundadores_valoris.py": [
            "renderizar_watchlist_fundadores_valoris",
        ],
        "comparador_setorial_valoris.py": [
            "renderizar_comparador_setorial_valoris",
        ],
        "relatorio_premium_v2_valoris.py": [
            "renderizar_relatorio_premium_v2_valoris",
        ],
        "pacote_premium_valoris.py": [
            "renderizar_pacote_premium_valoris",
        ],
        "feedback_pacote_premium_valoris.py": [
            "renderizar_feedback_pacote_premium_valoris",
        ],
        "roadmap_premium_valoris.py": [
            "renderizar_roadmap_premium_valoris",
        ],
        "estabilidade_execucao_valoris.py": [
            "renderizar_estabilidade_execucao_valoris",
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
    marcador = "[OK]" if resultado.ok else "[FALHA]"

    print(f"\n{marcador} {resultado.nome}: {resultado.status_texto()}")

    for detalhe in resultado.detalhes:
        print(f"   {detalhe}")


def executar_guardiao_release(strict: bool = False) -> int:
    raiz = Path.cwd()

    print(f"Valoris Release Guard v{VERSAO_RELEASE_GUARD}")
    print(f"Pasta analisada: {raiz}")

    checagens = [
        verificar_arquivos_essenciais(raiz),
        verificar_abas_fundador_renderizaveis(raiz),
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
        print("\n[FALHA] Release Guard encontrou problemas que merecem revisão.")

        if strict:
            return 1

        print("Modo normal: problemas foram reportados, mas o script não bloqueou a execução.")
        return 0

    print("\n[OK] Release Guard concluído sem falhas críticas.")
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
