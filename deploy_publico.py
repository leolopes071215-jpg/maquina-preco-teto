# deploy_publico.py

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v3.8.26 — Preparação para Deploy Público
# ------------------------------------------------------------
# Este arquivo cria uma central de preparação para deploy.
#
# Objetivo:
# - verificar se o projeto está pronto para rodar por link
# - identificar arquivos obrigatórios
# - orientar criação de requirements.txt
# - separar pendências críticas de melhorias futuras
# - preparar o MVP para teste real com usuários beta
# ============================================================


VERSAO_DEPLOY_PUBLICO = "3.8.26"


ARQUIVOS_OBRIGATORIOS_DEPLOY = [
    {
        "Arquivo": "app.py",
        "Obrigatório": "Sim",
        "Motivo": "Arquivo principal executado pelo Streamlit.",
    },
    {
        "Arquivo": "requirements.txt",
        "Obrigatório": "Sim",
        "Motivo": "Lista de dependências necessárias para instalar o app no servidor.",
    },
    {
        "Arquivo": "valuation.py",
        "Obrigatório": "Sim",
        "Motivo": "Motor base de cálculo do valuation.",
    },
    {
        "Arquivo": "empresas.py",
        "Obrigatório": "Sim",
        "Motivo": "Base inicial de empresas e dados usados pelo app.",
    },
    {
        "Arquivo": "modo_exibicao.py",
        "Obrigatório": "Sim",
        "Motivo": "Controla a experiência Beta, Investidor e Fundador.",
    },
    {
        "Arquivo": "experiencia_beta.py",
        "Obrigatório": "Sim",
        "Motivo": "Tela premium simplificada do usuário beta.",
    },
    {
        "Arquivo": "style.py",
        "Obrigatório": "Sim",
        "Motivo": "Aplica estilo visual global ao app.",
    },
    {
        "Arquivo": ".gitignore",
        "Obrigatório": "Recomendado",
        "Motivo": "Evita enviar arquivos desnecessários, cache e dados locais para o GitHub.",
    },
    {
        "Arquivo": "README.md",
        "Obrigatório": "Recomendado",
        "Motivo": "Explica o projeto, como rodar e como testar.",
    },
]


DEPENDENCIAS_RECOMENDADAS = [
    {
        "Pacote": "streamlit",
        "Motivo": "Framework principal do app.",
    },
    {
        "Pacote": "pandas",
        "Motivo": "Manipulação de tabelas e dados.",
    },
    {
        "Pacote": "numpy",
        "Motivo": "Cálculos numéricos, caso algum módulo use operações avançadas.",
    },
]


CHECKLIST_DEPLOY = [
    {
        "Etapa": "1",
        "Item": "App abre localmente sem erro",
        "Tipo": "Crítico",
        "Critério de pronto": "python -m streamlit run app.py funciona.",
    },
    {
        "Etapa": "2",
        "Item": "Modo Usuário Beta abre por padrão",
        "Tipo": "Crítico",
        "Critério de pronto": "Usuário comum vê experiência simples, sem áreas internas.",
    },
    {
        "Etapa": "3",
        "Item": "Arquivo requirements.txt existe",
        "Tipo": "Crítico",
        "Critério de pronto": "Servidor consegue instalar dependências.",
    },
    {
        "Etapa": "4",
        "Item": "Arquivos novos estão versionados no Git",
        "Tipo": "Crítico",
        "Critério de pronto": "git status termina com working tree clean.",
    },
    {
        "Etapa": "5",
        "Item": "Não existem imports quebrados",
        "Tipo": "Crítico",
        "Critério de pronto": "python -m py_compile app.py e módulos principais passam.",
    },
    {
        "Etapa": "6",
        "Item": "Dados locais sensíveis não são enviados",
        "Tipo": "Importante",
        "Critério de pronto": ".gitignore protege cache, env, chaves e arquivos temporários.",
    },
    {
        "Etapa": "7",
        "Item": "README explica como rodar",
        "Tipo": "Importante",
        "Critério de pronto": "Qualquer pessoa entende como instalar e executar.",
    },
    {
        "Etapa": "8",
        "Item": "Link público testado",
        "Tipo": "Crítico",
        "Critério de pronto": "Outra pessoa consegue abrir o app por link.",
    },
    {
        "Etapa": "9",
        "Item": "Feedback beta disponível",
        "Tipo": "Importante",
        "Critério de pronto": "Usuário consegue enviar feedback após usar.",
    },
]


NAO_DEPLOYAR_SE = [
    {
        "Bloqueio": "app.py não compila",
        "Motivo": "O app pode quebrar no servidor.",
    },
    {
        "Bloqueio": "requirements.txt não existe",
        "Motivo": "O ambiente online não saberá quais pacotes instalar.",
    },
    {
        "Bloqueio": "arquivos importados não estão no Git",
        "Motivo": "O app funciona localmente, mas quebra no deploy.",
    },
    {
        "Bloqueio": "Modo Usuário Beta ainda mostra áreas internas",
        "Motivo": "Usuário real não deve ver complexidade de fundador.",
    },
    {
        "Bloqueio": "git status não está limpo",
        "Motivo": "Há risco de esquecer arquivos importantes fora da versão.",
    },
]


COMANDOS_PRE_DEPLOY = [
    {
        "Ordem": "1",
        "Comando": "python -m py_compile app.py",
        "Objetivo": "Garantir que o arquivo principal compila.",
    },
    {
        "Ordem": "2",
        "Comando": "python -m py_compile modo_exibicao.py",
        "Objetivo": "Validar modos de exibição.",
    },
    {
        "Ordem": "3",
        "Comando": "python -m py_compile experiencia_beta.py",
        "Objetivo": "Validar experiência beta.",
    },
    {
        "Ordem": "4",
        "Comando": "python -m streamlit run app.py",
        "Objetivo": "Abrir o app localmente e testar visualmente.",
    },
    {
        "Ordem": "5",
        "Comando": "git status",
        "Objetivo": "Verificar se há arquivos pendentes.",
    },
    {
        "Ordem": "6",
        "Comando": "git add .",
        "Objetivo": "Adicionar arquivos necessários à versão.",
    },
    {
        "Ordem": "7",
        "Comando": 'git commit -m "Prepara projeto para deploy publico v3.8.26"',
        "Objetivo": "Criar commit da preparação.",
    },
    {
        "Ordem": "8",
        "Comando": "git push",
        "Objetivo": "Enviar projeto para o GitHub.",
    },
]


CONTEUDO_REQUIREMENTS_RECOMENDADO = """streamlit
pandas
numpy
"""


CONTEUDO_GITIGNORE_RECOMENDADO = """__pycache__/
*.pyc
.env
.venv/
venv/
.DS_Store
.streamlit/secrets.toml
*.log
"""


CONTEUDO_README_RECOMENDADO = """# Máquina de Preço-Teto

Ferramenta educacional para análise de valuation, preço-teto, margem de segurança e decisão disciplinada.

## Aviso

Este projeto é educacional. Não representa recomendação de compra, venda ou manutenção de investimentos.

## Como rodar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Objetivo

Ajudar investidores a transformar premissas financeiras em:

- preço justo
- preço-teto
- margem de segurança
- status educacional
- relatório de análise
"""


def _agora_formatado() -> str:
    return datetime.now().strftime("%d/%m/%Y %H:%M")


def _arquivo_existe(caminho_base: Path, nome_arquivo: str) -> bool:
    return (caminho_base / nome_arquivo).exists()


def verificar_arquivos_deploy(caminho_base: Path | None = None) -> List[Dict[str, str]]:
    """
    Verifica se os arquivos esperados para deploy existem no projeto.
    """
    base = caminho_base or Path.cwd()

    resultado = []

    for item in ARQUIVOS_OBRIGATORIOS_DEPLOY:
        arquivo = item["Arquivo"]
        existe = _arquivo_existe(base, arquivo)

        obrigatorio = item["Obrigatório"]
        status = "OK" if existe else "FALTA"

        if obrigatorio == "Recomendado" and not existe:
            status = "RECOMENDADO"

        resultado.append(
            {
                "Arquivo": arquivo,
                "Obrigatório": obrigatorio,
                "Status": status,
                "Motivo": item["Motivo"],
            }
        )

    return resultado


def calcular_resumo_deploy(verificacao: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Calcula resumo da prontidão para deploy.
    """
    obrigatorios = [
        item for item in verificacao
        if item.get("Obrigatório") == "Sim"
    ]

    obrigatorios_ok = [
        item for item in obrigatorios
        if item.get("Status") == "OK"
    ]

    recomendados_pendentes = [
        item for item in verificacao
        if item.get("Status") == "RECOMENDADO"
    ]

    faltas_criticas = [
        item for item in verificacao
        if item.get("Obrigatório") == "Sim" and item.get("Status") != "OK"
    ]

    total_obrigatorios = len(obrigatorios)

    if total_obrigatorios == 0:
        percentual_pronto = 0.0
    else:
        percentual_pronto = round((len(obrigatorios_ok) / total_obrigatorios) * 100, 2)

    pronto_para_deploy = len(faltas_criticas) == 0

    return {
        "total_arquivos": len(verificacao),
        "obrigatorios": total_obrigatorios,
        "obrigatorios_ok": len(obrigatorios_ok),
        "faltas_criticas": len(faltas_criticas),
        "recomendados_pendentes": len(recomendados_pendentes),
        "percentual_pronto": percentual_pronto,
        "pronto_para_deploy": pronto_para_deploy,
    }


def gerar_bloqueios_deploy(verificacao: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Gera bloqueios de deploy com base na verificação.
    """
    bloqueios = []

    for item in verificacao:
        if item.get("Obrigatório") == "Sim" and item.get("Status") != "OK":
            bloqueios.append(
                {
                    "Bloqueio": f"Arquivo obrigatório ausente: {item.get('Arquivo')}",
                    "Impacto": item.get("Motivo", ""),
                }
            )

    return bloqueios


def gerar_recomendacoes_deploy(verificacao: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Gera recomendações práticas antes do deploy.
    """
    recomendacoes = []

    for item in verificacao:
        if item.get("Status") == "RECOMENDADO":
            recomendacoes.append(
                {
                    "Recomendação": f"Criar {item.get('Arquivo')}",
                    "Motivo": item.get("Motivo", ""),
                }
            )

    if len(recomendacoes) == 0:
        recomendacoes.append(
            {
                "Recomendação": "Seguir para teste local completo",
                "Motivo": "Arquivos recomendados principais já existem ou não há pendências visíveis.",
            }
        )

    return recomendacoes


def gerar_markdown_deploy_publico(
    verificacao: List[Dict[str, str]],
    resumo: Dict[str, Any],
    bloqueios: List[Dict[str, str]],
    recomendacoes: List[Dict[str, str]],
) -> str:
    """
    Gera relatório markdown da preparação de deploy.
    """
    linhas_verificacao = "\n".join(
        [
            f"| {item['Arquivo']} | {item['Obrigatório']} | {item['Status']} | {item['Motivo']} |"
            for item in verificacao
        ]
    )

    if len(bloqueios) == 0:
        linhas_bloqueios = "| Nenhum bloqueio crítico | Arquivos obrigatórios encontrados |"
    else:
        linhas_bloqueios = "\n".join(
            [
                f"| {item['Bloqueio']} | {item['Impacto']} |"
                for item in bloqueios
            ]
        )

    linhas_recomendacoes = "\n".join(
        [
            f"| {item['Recomendação']} | {item['Motivo']} |"
            for item in recomendacoes
        ]
    )

    linhas_checklist = "\n".join(
        [
            f"| {item['Etapa']} | {item['Item']} | {item['Tipo']} | {item['Critério de pronto']} |"
            for item in CHECKLIST_DEPLOY
        ]
    )

    linhas_comandos = "\n".join(
        [
            f"| {item['Ordem']} | `{item['Comando']}` | {item['Objetivo']} |"
            for item in COMANDOS_PRE_DEPLOY
        ]
    )

    pronto_texto = "Sim" if resumo.get("pronto_para_deploy") else "Não"

    return f"""# Preparação para Deploy Público

Gerado em: {_agora_formatado()}

## Resumo

| Indicador | Valor |
|---|---|
| Versão | {VERSAO_DEPLOY_PUBLICO} |
| Arquivos avaliados | {resumo.get("total_arquivos")} |
| Obrigatórios OK | {resumo.get("obrigatorios_ok")}/{resumo.get("obrigatorios")} |
| Faltas críticas | {resumo.get("faltas_criticas")} |
| Recomendados pendentes | {resumo.get("recomendados_pendentes")} |
| Prontidão | {resumo.get("percentual_pronto")}% |
| Pronto para deploy? | {pronto_texto} |

## Verificação de arquivos

| Arquivo | Obrigatório | Status | Motivo |
|---|---|---|---|
{linhas_verificacao}

## Bloqueios

| Bloqueio | Impacto |
|---|---|
{linhas_bloqueios}

## Recomendações

| Recomendação | Motivo |
|---|---|
{linhas_recomendacoes}

## Checklist de deploy

| Etapa | Item | Tipo | Critério de pronto |
|---|---|---|---|
{linhas_checklist}

## Comandos pré-deploy

| Ordem | Comando | Objetivo |
|---|---|---|
{linhas_comandos}

## Regra de founder

Não faça deploy se houver arquivo obrigatório faltando, app.py quebrando,
requirements.txt ausente ou git status com arquivos essenciais fora do versionamento.
"""


def executar_autoteste_deploy_publico() -> List[Dict[str, str]]:
    """
    Executa autotestes lógicos do módulo de deploy.
    """
    testes = []

    verificacao = verificar_arquivos_deploy(Path.cwd())
    resumo = calcular_resumo_deploy(verificacao)
    bloqueios = gerar_bloqueios_deploy(verificacao)
    recomendacoes = gerar_recomendacoes_deploy(verificacao)
    markdown = gerar_markdown_deploy_publico(
        verificacao=verificacao,
        resumo=resumo,
        bloqueios=bloqueios,
        recomendacoes=recomendacoes,
    )

    testes.append(
        {
            "teste": "verificacao_arquivos_executa",
            "status": "OK" if len(verificacao) > 0 else "FALHA",
            "detalhe": f"Arquivos avaliados: {len(verificacao)}",
        }
    )

    testes.append(
        {
            "teste": "resumo_deploy_gerado",
            "status": "OK" if "percentual_pronto" in resumo else "FALHA",
            "detalhe": f"Prontidão: {resumo.get('percentual_pronto')}%",
        }
    )

    testes.append(
        {
            "teste": "bloqueios_deploy_gerados",
            "status": "OK" if isinstance(bloqueios, list) else "FALHA",
            "detalhe": f"Bloqueios: {len(bloqueios)}",
        }
    )

    testes.append(
        {
            "teste": "recomendacoes_deploy_geradas",
            "status": "OK" if len(recomendacoes) > 0 else "FALHA",
            "detalhe": f"Recomendações: {len(recomendacoes)}",
        }
    )

    testes.append(
        {
            "teste": "markdown_deploy_gerado",
            "status": "OK" if "# Preparação para Deploy Público" in markdown else "FALHA",
            "detalhe": "Relatório markdown criado.",
        }
    )

    return testes


def _injetar_css_deploy_publico() -> None:
    st.markdown(
        """
        <style>
            .dp-hero {
                padding: 1.8rem 1.9rem;
                border-radius: 30px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    radial-gradient(circle at top left, rgba(214, 181, 109, 0.25), transparent 30%),
                    radial-gradient(circle at bottom right, rgba(36, 128, 91, 0.24), transparent 34%),
                    linear-gradient(135deg, rgba(8, 15, 27, 0.99), rgba(5, 9, 18, 0.99));
                box-shadow: 0 18px 55px rgba(0, 0, 0, 0.34);
                margin-bottom: 1.25rem;
            }

            .dp-eyebrow {
                color: #d6b56d;
                font-size: 0.78rem;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.35rem;
            }

            .dp-title {
                color: #f4f7fb;
                font-size: 2.15rem;
                font-weight: 900;
                margin-bottom: 0.45rem;
                line-height: 1.14;
            }

            .dp-subtitle {
                color: rgba(244, 247, 251, 0.76);
                font-size: 1rem;
                line-height: 1.62;
                max-width: 1080px;
            }

            .dp-highlight {
                padding: 0.95rem 1rem;
                border-radius: 16px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.92rem;
                line-height: 1.55;
                margin-bottom: 0.7rem;
            }

            .dp-disclaimer {
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


def renderizar_deploy_publico() -> None:
    """
    Renderiza central de preparação para deploy público.
    """
    _injetar_css_deploy_publico()

    st.markdown(
        """
        <div class="dp-hero">
            <div class="dp-eyebrow">v3.8.26 — Deploy público</div>
            <div class="dp-title">Preparação para Deploy</div>
            <div class="dp-subtitle">
                Antes de colocar o app no ar, precisamos garantir que os arquivos essenciais,
                dependências, versionamento e experiência beta estejam prontos para teste real.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="dp-highlight">
            Deploy não é só colocar online. Deploy é garantir que outra pessoa consiga abrir,
            entender, testar, enviar feedback e não encontrar uma experiência quebrada.
        </div>
        """,
        unsafe_allow_html=True,
    )

    testes = executar_autoteste_deploy_publico()

    verificacao = verificar_arquivos_deploy(Path.cwd())
    resumo = calcular_resumo_deploy(verificacao)
    bloqueios = gerar_bloqueios_deploy(verificacao)
    recomendacoes = gerar_recomendacoes_deploy(verificacao)

    st.markdown("### Diagnóstico de deploy")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Versão", VERSAO_DEPLOY_PUBLICO)

    with col_2:
        st.metric("Prontidão", f"{resumo['percentual_pronto']}%")

    with col_3:
        st.metric("Faltas críticas", resumo["faltas_criticas"])

    with col_4:
        st.metric("Status", "Pronto" if resumo["pronto_para_deploy"] else "Pendente")

    if all(teste["status"] == "OK" for teste in testes):
        st.success("Módulo de deploy passou nos autotestes.")
    else:
        st.error("Módulo de deploy encontrou falhas nos autotestes.")

    with st.expander("Ver autotestes"):
        st.dataframe(testes, use_container_width=True, hide_index=True)

    if resumo["pronto_para_deploy"]:
        st.success(
            "Arquivos obrigatórios encontrados. O projeto está tecnicamente mais próximo de um deploy público."
        )
    else:
        st.error(
            "Existem arquivos obrigatórios ausentes. Resolva os bloqueios antes de fazer deploy."
        )

    st.divider()

    st.markdown("### Verificação de arquivos")

    st.dataframe(
        verificacao,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Bloqueios críticos")

    if len(bloqueios) == 0:
        st.success("Nenhum bloqueio crítico detectado pela verificação de arquivos.")
    else:
        st.dataframe(
            bloqueios,
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    st.markdown("### Recomendações")

    st.dataframe(
        recomendacoes,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Checklist de deploy")

    st.dataframe(
        CHECKLIST_DEPLOY,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Não fazer deploy se...")

    st.dataframe(
        NAO_DEPLOYAR_SE,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Comandos pré-deploy")

    st.dataframe(
        COMANDOS_PRE_DEPLOY,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Arquivo requirements.txt recomendado")

    st.code(CONTEUDO_REQUIREMENTS_RECOMENDADO, language="text")

    st.download_button(
        label="Baixar requirements.txt sugerido",
        data=CONTEUDO_REQUIREMENTS_RECOMENDADO,
        file_name="requirements.txt",
        mime="text/plain",
        key="download_requirements_deploy",
    )

    st.divider()

    st.markdown("### Arquivo .gitignore recomendado")

    st.code(CONTEUDO_GITIGNORE_RECOMENDADO, language="text")

    st.download_button(
        label="Baixar .gitignore sugerido",
        data=CONTEUDO_GITIGNORE_RECOMENDADO,
        file_name=".gitignore",
        mime="text/plain",
        key="download_gitignore_deploy",
    )

    st.divider()

    st.markdown("### README.md recomendado")

    st.code(CONTEUDO_README_RECOMENDADO, language="markdown")

    st.download_button(
        label="Baixar README.md sugerido",
        data=CONTEUDO_README_RECOMENDADO,
        file_name="README.md",
        mime="text/markdown",
        key="download_readme_deploy",
    )

    st.divider()

    st.markdown("### Relatório de deploy")

    st.download_button(
        label="Baixar relatório de preparação para deploy (.md)",
        data=gerar_markdown_deploy_publico(
            verificacao=verificacao,
            resumo=resumo,
            bloqueios=bloqueios,
            recomendacoes=recomendacoes,
        ),
        file_name="relatorio_preparacao_deploy.md",
        mime="text/markdown",
        key="download_relatorio_deploy",
    )

    st.markdown(
        """
        <div class="dp-disclaimer">
            <strong>Regra:</strong> antes do deploy público, rode os testes locais,
            confirme que o Git está limpo e garanta que o Modo Usuário Beta esteja simples.
            O objetivo agora é validar com pessoas reais, não adicionar complexidade.
        </div>
        """,
        unsafe_allow_html=True,
    )