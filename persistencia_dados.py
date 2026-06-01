# persistencia_dados.py

import csv
import zipfile
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v1.37 — Central de Persistência, Backups e Dados
# ------------------------------------------------------------
# Esta tela organiza a camada de dados local do MVP.
#
# Objetivo:
# - auditar arquivos CSV usados pelo app
# - mostrar quais arquivos existem
# - mostrar quantidade de registros
# - orientar .gitignore
# - permitir backup em .zip
# - preparar futura migração para banco de dados
# ============================================================


ARQUIVOS_DADOS = [
    {
        "arquivo": "historico_analises.csv",
        "modulo": "Histórico",
        "tipo": "Análises salvas",
        "sensibilidade": "Média",
        "deve_ir_gitignore": "Sim",
        "observacao": "Registra premissas e resultados de análises feitas no app.",
    },
    {
        "arquivo": "watchlist_multiativos.csv",
        "modulo": "Watchlist",
        "tipo": "Ativos acompanhados",
        "sensibilidade": "Média",
        "deve_ir_gitignore": "Sim",
        "observacao": "Registra ativos, prioridades, status e próximas ações.",
    },
    {
        "arquivo": "feedback_beta.csv",
        "modulo": "Feedback Beta",
        "tipo": "Feedbacks de usuários",
        "sensibilidade": "Alta",
        "deve_ir_gitignore": "Sim",
        "observacao": "Pode conter perfil, opinião e intenção de pagamento.",
    },
    {
        "arquivo": "lista_espera_beta.csv",
        "modulo": "Oferta Beta",
        "tipo": "Lista de espera",
        "sensibilidade": "Alta",
        "deve_ir_gitignore": "Sim",
        "observacao": "Pode conter nome, e-mail, WhatsApp e intenção de compra.",
    },
    {
        "arquivo": "calendario_conteudo.csv",
        "modulo": "Conteúdo",
        "tipo": "Calendário editorial",
        "sensibilidade": "Baixa",
        "deve_ir_gitignore": "Sim",
        "observacao": "Registra ideias, roteiros, CTAs e status de produção.",
    },
    {
        "arquivo": "tarefas_lancamento_beta.csv",
        "modulo": "Lançamento",
        "tipo": "Tarefas do beta",
        "sensibilidade": "Baixa",
        "deve_ir_gitignore": "Sim",
        "observacao": "Registra tarefas, fase, prazo, prioridade e status.",
    },
]


ENTRADAS_RECOMENDADAS_GITIGNORE = [
    "historico_analises.csv",
    "watchlist_multiativos.csv",
    "feedback_beta.csv",
    "lista_espera_beta.csv",
    "calendario_conteudo.csv",
    "tarefas_lancamento_beta.csv",
    "__pycache__/",
    "*.pyc",
    ".streamlit/secrets.toml",
]


def _arquivo_existe(nome_arquivo: str) -> bool:
    return Path(nome_arquivo).exists()


def _tamanho_arquivo(nome_arquivo: str) -> int:
    caminho = Path(nome_arquivo)

    if not caminho.exists():
        return 0

    return caminho.stat().st_size


def _formatar_tamanho(bytes_arquivo: int) -> str:
    if bytes_arquivo <= 0:
        return "0 B"

    if bytes_arquivo < 1024:
        return f"{bytes_arquivo} B"

    if bytes_arquivo < 1024 * 1024:
        return f"{bytes_arquivo / 1024:.1f} KB"

    return f"{bytes_arquivo / (1024 * 1024):.2f} MB"


def _contar_linhas_csv(nome_arquivo: str) -> int:
    caminho = Path(nome_arquivo)

    if not caminho.exists():
        return 0

    try:
        with open(caminho, "r", encoding="utf-8", newline="") as arquivo:
            leitor = csv.reader(arquivo)
            linhas = list(leitor)

        if len(linhas) == 0:
            return 0

        return max(0, len(linhas) - 1)

    except Exception:
        return 0


def _ler_colunas_csv(nome_arquivo: str) -> str:
    caminho = Path(nome_arquivo)

    if not caminho.exists():
        return "Arquivo não existe"

    try:
        with open(caminho, "r", encoding="utf-8", newline="") as arquivo:
            leitor = csv.reader(arquivo)
            cabecalho = next(leitor, [])

        if len(cabecalho) == 0:
            return "Sem cabeçalho"

        return ", ".join(cabecalho)

    except Exception:
        return "Não foi possível ler"


def _carregar_gitignore() -> List[str]:
    caminho = Path(".gitignore")

    if not caminho.exists():
        return []

    try:
        with open(caminho, "r", encoding="utf-8") as arquivo:
            linhas = arquivo.read().splitlines()

        return [linha.strip() for linha in linhas if linha.strip() != ""]

    except Exception:
        return []


def _entrada_no_gitignore(entrada: str, linhas_gitignore: List[str]) -> bool:
    return entrada in linhas_gitignore


def _gerar_tabela_arquivos() -> List[Dict[str, str]]:
    tabela = []

    for item in ARQUIVOS_DADOS:
        nome = item["arquivo"]
        existe = _arquivo_existe(nome)
        tamanho = _tamanho_arquivo(nome)
        registros = _contar_linhas_csv(nome)
        colunas = _ler_colunas_csv(nome)

        tabela.append(
            {
                "Arquivo": nome,
                "Existe": "Sim" if existe else "Não",
                "Registros": str(registros),
                "Tamanho": _formatar_tamanho(tamanho),
                "Módulo": item["modulo"],
                "Tipo de dado": item["tipo"],
                "Sensibilidade": item["sensibilidade"],
                "Deve estar no .gitignore": item["deve_ir_gitignore"],
                "Colunas": colunas,
            }
        )

    return tabela


def _gerar_tabela_gitignore() -> List[Dict[str, str]]:
    linhas_gitignore = _carregar_gitignore()
    tabela = []

    for entrada in ENTRADAS_RECOMENDADAS_GITIGNORE:
        esta = _entrada_no_gitignore(entrada, linhas_gitignore)

        tabela.append(
            {
                "Entrada recomendada": entrada,
                "Está no .gitignore": "Sim" if esta else "Não",
                "Status": "OK" if esta else "Pendente",
            }
        )

    return tabela


def _contar_status_gitignore() -> Dict[str, int]:
    tabela = _gerar_tabela_gitignore()

    ok = len([linha for linha in tabela if linha["Status"] == "OK"])
    pendente = len([linha for linha in tabela if linha["Status"] == "Pendente"])

    return {
        "ok": ok,
        "pendente": pendente,
        "total": len(tabela),
    }


def _gerar_comando_gitignore() -> str:
    comandos = []

    for entrada in ENTRADAS_RECOMENDADAS_GITIGNORE:
        comandos.append(f'Add-Content .gitignore "{entrada}"')

    return "\n".join(comandos)


def _gerar_backup_zip() -> bytes:
    buffer = BytesIO()

    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as arquivo_zip:
        for item in ARQUIVOS_DADOS:
            nome_arquivo = item["arquivo"]
            caminho = Path(nome_arquivo)

            if caminho.exists():
                arquivo_zip.write(caminho, arcname=nome_arquivo)

        resumo = _gerar_resumo_markdown()
        arquivo_zip.writestr("resumo_backup_dados.md", resumo)

    buffer.seek(0)
    return buffer.getvalue()


def _gerar_resumo_markdown() -> str:
    tabela_arquivos = _gerar_tabela_arquivos()
    tabela_gitignore = _gerar_tabela_gitignore()

    linhas_arquivos = "\n".join(
        [
            f"| {linha['Arquivo']} | {linha['Existe']} | {linha['Registros']} | {linha['Tamanho']} | {linha['Sensibilidade']} |"
            for linha in tabela_arquivos
        ]
    )

    linhas_gitignore = "\n".join(
        [
            f"| {linha['Entrada recomendada']} | {linha['Está no .gitignore']} | {linha['Status']} |"
            for linha in tabela_gitignore
        ]
    )

    return f"""# Backup de Dados — Máquina de Preço-Teto

Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Arquivos auditados

| Arquivo | Existe | Registros | Tamanho | Sensibilidade |
|---|---:|---:|---:|---|
{linhas_arquivos}

## Verificação do .gitignore

| Entrada | Está no .gitignore | Status |
|---|---:|---|
{linhas_gitignore}

## Observação importante

Este MVP usa arquivos CSV locais para persistência simples.

Isso é suficiente para desenvolvimento e testes controlados, mas não é a arquitetura ideal para escala, múltiplos usuários ou dados sensíveis.

Para a Fase 2, o ideal será estudar uma migração gradual para banco de dados, autenticação e separação de dados por usuário.
"""


def _gerar_plano_migracao_banco() -> List[Dict[str, str]]:
    return [
        {
            "Fase": "Agora",
            "Solução": "CSV local",
            "Quando usar": "MVP, desenvolvimento e testes pequenos.",
            "Risco": "Pode perder dados no Streamlit Cloud e não separa usuários.",
        },
        {
            "Fase": "Fase 2 inicial",
            "Solução": "Google Sheets ou Airtable",
            "Quando usar": "Beta com poucos usuários e necessidade de visualizar dados facilmente.",
            "Risco": "Ainda limitado para escala e segurança avançada.",
        },
        {
            "Fase": "Fase 2 avançada",
            "Solução": "Supabase/PostgreSQL",
            "Quando usar": "Quando houver usuários reais, login e dados por pessoa.",
            "Risco": "Exige estrutura técnica maior.",
        },
        {
            "Fase": "Produto comercial",
            "Solução": "Banco de dados + autenticação + backups automáticos",
            "Quando usar": "Assinatura paga, dados sensíveis e uso recorrente.",
            "Risco": "Precisa de arquitetura profissional.",
        },
    ]


def _gerar_regras_dados() -> List[Dict[str, str]]:
    return [
        {
            "Regra": "Não subir CSVs de usuários para o GitHub",
            "Motivo": "Podem conter dados pessoais, feedbacks, contatos ou estratégias.",
        },
        {
            "Regra": "Fazer backup antes de grandes alterações",
            "Motivo": "Evita perder feedbacks, watchlist e lista de espera.",
        },
        {
            "Regra": "Não confiar em CSV local para beta grande",
            "Motivo": "Streamlit Cloud pode reiniciar ambiente e perder arquivos criados em runtime.",
        },
        {
            "Regra": "Separar dados do usuário e dados do produto",
            "Motivo": "Ajuda na futura migração para banco de dados.",
        },
        {
            "Regra": "Não coletar mais dados pessoais do que o necessário",
            "Motivo": "Reduz risco e aumenta confiança.",
        },
    ]


def _injetar_css_persistencia() -> None:
    st.markdown(
        """
        <style>
            .dados-hero {
                padding: 1.75rem 1.8rem;
                border-radius: 30px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    radial-gradient(circle at top left, rgba(214, 181, 109, 0.25), transparent 30%),
                    radial-gradient(circle at bottom right, rgba(74, 144, 226, 0.22), transparent 34%),
                    linear-gradient(135deg, rgba(8, 15, 27, 0.99), rgba(5, 9, 18, 0.99));
                box-shadow: 0 18px 55px rgba(0, 0, 0, 0.34);
                margin-bottom: 1.25rem;
            }

            .dados-eyebrow {
                color: #d6b56d;
                font-size: 0.78rem;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.35rem;
            }

            .dados-title {
                color: #f4f7fb;
                font-size: 2.1rem;
                font-weight: 900;
                margin-bottom: 0.45rem;
                line-height: 1.14;
            }

            .dados-subtitle {
                color: rgba(244, 247, 251, 0.76);
                font-size: 1rem;
                line-height: 1.62;
                max-width: 1080px;
            }

            .dados-card {
                padding: 1.1rem 1.15rem;
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.035);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.18);
                height: 100%;
            }

            .dados-card-label {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .dados-card-value {
                color: #f4f7fb;
                font-size: 1.22rem;
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .dados-card-note {
                color: rgba(244, 247, 251, 0.68);
                font-size: 0.87rem;
                line-height: 1.47;
            }

            .dados-highlight {
                padding: 0.95rem 1rem;
                border-radius: 16px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.92rem;
                line-height: 1.55;
                margin-bottom: 0.7rem;
            }

            .dados-code {
                padding: 1rem 1.05rem;
                border-radius: 18px;
                background: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(255, 255, 255, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.9rem;
                line-height: 1.55;
                white-space: pre-wrap;
                margin-bottom: 0.85rem;
                font-family: monospace;
            }

            .dados-disclaimer {
                padding: 0.95rem 1rem;
                border-radius: 16px;
                background: rgba(74, 144, 226, 0.08);
                border: 1px solid rgba(74, 144, 226, 0.18);
                color: rgba(244, 247, 251, 0.78);
                font-size: 0.9rem;
                line-height: 1.55;
                margin-top: 1.1rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _card(label: str, value: str, note: str = "") -> None:
    st.markdown(
        f"""
        <div class="dados-card">
            <div class="dados-card-label">{label}</div>
            <div class="dados-card-value">{value}</div>
            <div class="dados-card-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _code_box(texto: str) -> None:
    st.markdown(
        f"""
        <div class="dados-code">{texto}</div>
        """,
        unsafe_allow_html=True,
    )


def renderizar_central_persistencia_dados() -> None:
    """
    Renderiza a Central de Persistência, Backups e Dados.
    """
    _injetar_css_persistencia()

    tabela_arquivos = _gerar_tabela_arquivos()
    tabela_gitignore = _gerar_tabela_gitignore()
    status_gitignore = _contar_status_gitignore()

    arquivos_existentes = len([
        linha for linha in tabela_arquivos
        if linha["Existe"] == "Sim"
    ])

    total_registros = sum(
        [
            int(linha["Registros"])
            for linha in tabela_arquivos
            if linha["Registros"].isdigit()
        ]
    )

    arquivos_alta_sensibilidade = len([
        linha for linha in tabela_arquivos
        if linha["Sensibilidade"] == "Alta"
    ])

    st.session_state["resultado_persistencia_dados"] = {
        "arquivos_existentes": arquivos_existentes,
        "total_registros": total_registros,
        "gitignore_ok": status_gitignore["ok"],
        "gitignore_pendente": status_gitignore["pendente"],
        "arquivos_alta_sensibilidade": arquivos_alta_sensibilidade,
    }

    st.markdown(
        """
        <div class="dados-hero">
            <div class="dados-eyebrow">Governança do MVP</div>
            <div class="dados-title">Central de Persistência, Backups e Dados</div>
            <div class="dados-subtitle">
                Audite os arquivos CSV do app, veja o que está sendo salvo, proteja dados sensíveis,
                confira o .gitignore e gere backups antes de avançar para usuários reais.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="dados-highlight">
            Antes da Fase 2, precisamos tratar dados com seriedade. O MVP pode usar CSV,
            mas usuários reais exigem mais cuidado com backup, privacidade e persistência.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Diagnóstico geral")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        _card(
            "Arquivos existentes",
            f"{arquivos_existentes}/{len(ARQUIVOS_DADOS)}",
            "Arquivos CSV encontrados no projeto.",
        )

    with col_2:
        _card(
            "Registros locais",
            str(total_registros),
            "Total aproximado salvo nos CSVs.",
        )

    with col_3:
        _card(
            "Pendências .gitignore",
            str(status_gitignore["pendente"]),
            "Itens recomendados ainda não encontrados.",
        )

    with col_4:
        _card(
            "Alta sensibilidade",
            str(arquivos_alta_sensibilidade),
            "Arquivos que podem conter contatos ou feedbacks.",
        )

    st.divider()

    st.markdown("### Arquivos de dados auditados")

    st.dataframe(
        tabela_arquivos,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Verificação do .gitignore")

    st.dataframe(
        tabela_gitignore,
        use_container_width=True,
        hide_index=True,
    )

    if status_gitignore["pendente"] > 0:
        st.warning(
            "Existem entradas recomendadas que ainda não aparecem no .gitignore. "
            "Copie os comandos abaixo no PowerShell para adicionar."
        )

        _code_box(_gerar_comando_gitignore())
    else:
        st.success("O .gitignore parece conter todas as entradas recomendadas para esta fase.")

    st.divider()

    st.markdown("### Backup local dos dados")

    st.caption(
        "Gere um arquivo .zip com todos os CSVs existentes e um resumo em Markdown."
    )

    nome_backup = f"backup_dados_maquina_preco_teto_{datetime.now().strftime('%Y%m%d_%H%M')}.zip"

    st.download_button(
        label="Baixar backup dos dados (.zip)",
        data=_gerar_backup_zip(),
        file_name=nome_backup,
        mime="application/zip",
        key="download_backup_dados_zip",
    )

    st.divider()

    st.markdown("### Regras de segurança dos dados")

    st.dataframe(
        _gerar_regras_dados(),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Plano futuro de migração para banco de dados")

    st.dataframe(
        _gerar_plano_migracao_banco(),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Leitura estratégica")

    if total_registros == 0:
        st.info(
            "Ainda há poucos ou nenhum dado salvo. Isso é normal antes de usuários reais. "
            "O foco agora é garantir que a estrutura esteja preparada."
        )
    elif status_gitignore["pendente"] > 0:
        st.warning(
            "Já existem dados locais ou estrutura de dados, mas o .gitignore ainda precisa ser revisado. "
            "Não avance para beta real sem proteger esses arquivos."
        )
    else:
        st.success(
            "A estrutura local está organizada para MVP. Ainda não é ideal para escala, "
            "mas está adequada para testes controlados e backups manuais."
        )

    st.markdown(
        """
        <div class="dados-disclaimer">
            <strong>Nota estratégica:</strong> CSV local é aceitável para MVP e validação inicial.
            Para produto comercial, precisaremos evoluir para autenticação, banco de dados,
            separação por usuário e backups automáticos.
        </div>
        """,
        unsafe_allow_html=True,
    )