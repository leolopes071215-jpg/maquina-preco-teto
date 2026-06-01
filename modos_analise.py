# modos_analise.py

from typing import Dict, List


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v1.24 — Modo Demonstração vs Nova Análise
# ------------------------------------------------------------
# Este arquivo separa claramente:
# 1. Modo Demonstração
# 2. Nova Análise Manual
# 3. Empresas reais da base
#
# Objetivo:
# evitar que o usuário interprete dados genéricos como uma análise real.
# ============================================================


OPCAO_MODO_DEMONSTRACAO = "Modo Demonstração"
OPCAO_NOVA_ANALISE_MANUAL = "Nova Análise Manual"


DADOS_DEMONSTRACAO = {
    "empresa": "Empresa Demonstração",
    "ticker": "DEMO",
    "perfil_empresa": (
        "Exemplo fictício criado apenas para demonstrar como a Máquina de Preço-Teto funciona."
    ),
    "moeda": (
        "Dados fictícios em unidade simplificada. Não use esta análise para tomar decisões reais."
    ),
    "simbolo_moeda": "R$",
    "data_referencia": "Demonstração educacional",
    "fonte_premissas": (
        "Dados fictícios. Este modo serve apenas para mostrar a jornada do app: "
        "valuation, tese, checklist, painel, relatório e watchlist."
    ),
    "lucro_liquido_sustentavel": 1_000.0,
    "fluxo_caixa_livre": 850.0,
    "quantidade_acoes": 100.0,
    "preco_atual": 82.0,
    "multiplo_justo_eps": 10.0,
    "multiplo_justo_fcf": 10.0,
    "peso_eps": 50,
    "peso_fcf": 50,
    "margem_seguranca": 25,
    "tese": (
        "Esta é uma tese fictícia de demonstração. Use este modo para entender como o relatório, "
        "o painel executivo, a watchlist e os módulos qualitativos funcionam."
    ),
    "riscos": (
        "Riscos fictícios: dados não auditados, premissas genéricas, ausência de fonte real e ausência "
        "de análise fundamentalista completa."
    ),
    "fundamentos": (
        "Fundamentos fictícios usados apenas para demonstrar o fluxo do produto. "
        "Substitua por dados reais ao fazer uma análise verdadeira."
    ),
}


DADOS_NOVA_ANALISE_MANUAL = {
    "empresa": "Nova Empresa",
    "ticker": "NOVO",
    "perfil_empresa": "Empresa inserida manualmente pelo usuário.",
    "moeda": (
        "Valores inseridos manualmente. Use sempre a mesma unidade para lucro, FCF e quantidade de ações."
    ),
    "simbolo_moeda": "R$",
    "data_referencia": "Dados inseridos manualmente pelo usuário",
    "fonte_premissas": (
        "Nova análise manual. Os dados não foram puxados automaticamente. "
        "O usuário deve conferir lucro líquido sustentável, FCF, quantidade de ações, preço atual e múltiplos usados."
    ),
    "lucro_liquido_sustentavel": 1_000.0,
    "fluxo_caixa_livre": 800.0,
    "quantidade_acoes": 100.0,
    "preco_atual": 120.0,
    "multiplo_justo_eps": 10.0,
    "multiplo_justo_fcf": 10.0,
    "peso_eps": 50,
    "peso_fcf": 50,
    "margem_seguranca": 25,
    "tese": (
        "Descreva aqui a tese da empresa: o que ela faz, como ganha dinheiro, "
        "quais são suas vantagens competitivas e por que ela poderia gerar valor no longo prazo."
    ),
    "riscos": (
        "Descreva aqui os principais riscos: concorrência, endividamento, queda de margens, "
        "regulação, ciclicidade, dependência de poucos clientes ou risco de pagar caro demais."
    ),
    "fundamentos": (
        "Descreva aqui os fundamentos observados: crescimento de receita, margens, lucro, "
        "geração de caixa, retorno sobre capital, endividamento e qualidade da gestão."
    ),
}


def obter_opcoes_modelo(empresas: Dict) -> List[str]:
    """
    Retorna a lista de opções que aparecerá no seletor principal da sidebar.
    """
    return [
        OPCAO_MODO_DEMONSTRACAO,
        OPCAO_NOVA_ANALISE_MANUAL,
    ] + list(empresas.keys())


def eh_modo_demonstracao(modelo_escolhido: str) -> bool:
    return modelo_escolhido == OPCAO_MODO_DEMONSTRACAO


def eh_nova_analise_manual(modelo_escolhido: str) -> bool:
    return modelo_escolhido == OPCAO_NOVA_ANALISE_MANUAL


def eh_modo_editavel(modelo_escolhido: str) -> bool:
    """
    Demonstração e nova análise manual são totalmente editáveis.
    Empresas da base também continuam editáveis no app, mas esta função
    identifica os modos criados pelo usuário.
    """
    return modelo_escolhido in [
        OPCAO_MODO_DEMONSTRACAO,
        OPCAO_NOVA_ANALISE_MANUAL,
    ]


def obter_dados_modelo(modelo_escolhido: str, empresas: Dict) -> Dict:
    """
    Retorna os dados iniciais com base no modo selecionado.
    """
    if eh_modo_demonstracao(modelo_escolhido):
        return DADOS_DEMONSTRACAO.copy()

    if eh_nova_analise_manual(modelo_escolhido):
        return DADOS_NOVA_ANALISE_MANUAL.copy()

    return empresas[modelo_escolhido]


def obter_tipo_analise(modelo_escolhido: str) -> str:
    if eh_modo_demonstracao(modelo_escolhido):
        return "Demonstração"

    if eh_nova_analise_manual(modelo_escolhido):
        return "Manual"

    return "Base"


def obter_aviso_modo(modelo_escolhido: str) -> str:
    """
    Retorna aviso específico para cada modo.
    """
    if eh_modo_demonstracao(modelo_escolhido):
        return (
            "Modo Demonstração ativado. Os dados são fictícios e servem apenas para entender a jornada do app. "
            "Não interprete o status como análise real."
        )

    if eh_nova_analise_manual(modelo_escolhido):
        return (
            "Nova Análise Manual ativada. Substitua os dados padrão por informações reais antes de interpretar "
            "valuation, preço-teto ou status educacional."
        )

    return (
        "Empresa da base selecionada. Revise as premissas antes de interpretar o resultado. "
        "Os dados podem estar desatualizados ou simplificados."
    )


def obter_titulo_modo(modelo_escolhido: str) -> str:
    if eh_modo_demonstracao(modelo_escolhido):
        return "Modo Demonstração"

    if eh_nova_analise_manual(modelo_escolhido):
        return "Nova Análise Manual"

    return "Empresa da Base"


def obter_descricao_modo(modelo_escolhido: str) -> str:
    if eh_modo_demonstracao(modelo_escolhido):
        return (
            "Use este modo para conhecer o funcionamento da plataforma sem inserir dados reais."
        )

    if eh_nova_analise_manual(modelo_escolhido):
        return (
            "Use este modo para analisar uma empresa, FII, ação ou ativo com dados inseridos por você."
        )

    return (
        "Use este modo como ponto de partida, sempre revisando as premissas antes de concluir qualquer análise."
    )