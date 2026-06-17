
import streamlit as st

st.set_page_config(
    page_title="Valoris — Modo Seguro",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.sidebar.title("Valoris")
st.sidebar.caption("Modo Seguro — carrega apenas uma tela por vez")

PAGINAS = {
    "Histórico Principal": (
        "historico_principal_valoris",
        "renderizar_historico_principal_valoris",
        "Histórico oficial com backend flexível, rollback e experiência premium.",
    ),

    "Simulador Migração": (
        "simulador_migracao_banco_valoris",
        "renderizar_simulador_migracao_banco_valoris",
        "Simula migra??o CSV para SQLite/PostgreSQL antes de criar o banco.",
    ),

    "SQLite Local": (
        "sqlite_local_valoris",
        "renderizar_sqlite_local_valoris",
        "Banco SQLite local em modo laboratório.",
    ),

    "Repository Backend": (
        "repository_backend_sqlite_valoris",
        "renderizar_repository_backend_sqlite_valoris",
        "Configura CSV ou SQLite como backend flexível do Repository.",
    ),

    "Health Check": (
        "healthcheck_banco_repository_valoris",
        "renderizar_healthcheck_banco_repository_valoris",
        "Central de saúde técnica do banco, CSV e Repository.",
    ),

    "Migração Backend": (
        "migracao_paginas_backend_valoris",
        "renderizar_migracao_paginas_backend_valoris",
        "Governança de migração gradual das páginas para backend flexível.",
    ),

    "Histórico Backend": (
        "historico_backend_flexivel_valoris",
        "renderizar_historico_backend_flexivel_valoris",
        "Histórico de análises lendo via backend flexível com rollback.",
    ),

    "Histórico Análises": (
        "historico_analises_valoris",
        "renderizar_historico_analises_valoris",
        "Hist?rico do motor: an?lises salvas, filtros, scores e decis?es.",
    ),

    "Motor + Watchlist": (
        "integracao_motor_watchlist_valoris",
        "renderizar_integracao_motor_watchlist_valoris",
        "Ponte entre o motor de análise e a watchlist de acompanhamento.",
    ),

    "Motor + Relatório": (
        "integracao_motor_relatorio_valoris",
        "renderizar_integracao_motor_relatorio_valoris",
        "Transforma análise do motor em dossiê premium estruturado.",
    ),

    "Análise Inteligente": (
        "analise_inteligente_valoris",
        "renderizar_analise_inteligente_valoris",
        "Central de decisão que une motor, histórico, watchlist e relatório.",
    ),

    "Pipeline Decisão": (
        "pipeline_decisao_valoris",
        "renderizar_pipeline_decisao_valoris",
        "Esteira operacional que transforma análise inteligente em próximas ações.",
    ),

    "Radar Revisões": (
        "radar_revisoes_valoris",
        "renderizar_radar_revisoes_valoris",
        "Radar de prazos, revisões, alertas e ações pendentes.",
    ),

    "Mapa Dados": (
        "mapa_dados_contratos_valoris",
        "renderizar_mapa_dados_contratos_valoris",
        "Mapa de CSVs, contratos, campos e prontidão para banco.",
    ),

    "Repository Único": (
        "repositorio_unico_valoris",
        "renderizar_repositorio_unico_valoris",
        "Camada central de dados: CSV hoje, banco amanhã.",
    ),

    "Motor Análise Ativos": (
        "motor_analise_ativos_valoris",
        "renderizar_motor_analise_ativos_valoris",
        "Motor central: ativo, dados, preço teto, risco e decisão.",
    ),

    "Recuperação Páginas": (
        "recuperacao_paginas_valoris",
        "renderizar_recuperacao_paginas_valoris",
        "Prioriza páginas antigas para recuperação controlada.",
    ),

    "Navegação Segura": (
        "navegacao_segura_valoris",
        "renderizar_navegacao_segura_valoris",
        "Catálogo de módulos e recuperação segura de páginas.",
    ),

    "Estabilidade": ("estabilidade_execucao_valoris", "renderizar_estabilidade_execucao_valoris"),
    "Roadmap Premium": ("roadmap_premium_valoris", "renderizar_roadmap_premium_valoris"),
    "Feedback Pacote": ("feedback_pacote_premium_valoris", "renderizar_feedback_pacote_premium_valoris"),
    "Pacote Premium": ("pacote_premium_valoris", "renderizar_pacote_premium_valoris"),
    "Relatório Premium v2": ("relatorio_premium_v2_valoris", "renderizar_relatorio_premium_v2_valoris"),
    "Comparador Setorial": ("comparador_setorial_valoris", "renderizar_comparador_setorial_valoris"),
    "Watchlist Fundadores": ("watchlist_fundadores_valoris", "renderizar_watchlist_fundadores_valoris"),
    "Retenção Fundadores": ("retencao_fundadores_valoris", "renderizar_retencao_fundadores_valoris"),
    "Checkout Fundadores": ("checkout_fundadores_valoris", "renderizar_checkout_fundadores_valoris"),
    "Oferta Beta": ("oferta_beta_fundador_valoris", "renderizar_oferta_beta_fundador_valoris"),
    "Beta Público": ("beta_publico_valoris", "renderizar_beta_publico_valoris"),
    "Onboarding Premium": ("onboarding_premium_valoris", "renderizar_onboarding_premium_valoris"),
    "Beta Insights": ("beta_insights_valoris", "renderizar_beta_insights_valoris"),
    "Beta Feedback": ("beta_feedback_valoris", "renderizar_beta_feedback_valoris"),
    "Lista de Espera": ("lista_espera_beta", "renderizar_lista_espera_valoris"),
    "Gateway Dados": ("gateway_dados_valoris", "renderizar_gateway_dados_valoris"),
    "Repositórios": ("repositorios_valoris", "renderizar_repositorios_valoris"),
}

pagina = st.sidebar.radio(
    "Escolha uma área",
    list(PAGINAS.keys()),
    index=0,
)

dados_pagina = PAGINAS[pagina]

if len(dados_pagina) == 2:
    modulo_nome, funcao_nome = dados_pagina
    descricao_pagina = ""
else:
    modulo_nome, funcao_nome, descricao_pagina = dados_pagina[0], dados_pagina[1], dados_pagina[2]


st.title(f"Valoris — {pagina}")
st.caption("Modo Seguro: esta versão importa e renderiza somente a página selecionada.")

try:
    modulo = __import__(modulo_nome, fromlist=[funcao_nome])
    funcao = getattr(modulo, funcao_nome)
    funcao()
except MemoryError:
    st.error("MemoryError: esta página tentou carregar dados demais.")
    st.info("Volte para a aba Estabilidade, limpe logs/backups e tente novamente.")
except Exception as erro:
    st.error(f"Erro ao carregar {pagina}")
    st.exception(erro)

# Compatibilidade com release_guard.py


# Compatibilidade com release_guard.py
# O app seguro usa PAGINAS para carregar uma tela por vez.
# Esta lista existe para o release_guard validar a ordem hist?rica do projeto.
ABAS_ORDEM_COMPLETA = [
    "Estabilidade",
    "Produto",
    "Navegação",
    "Onboarding",
    "Landing Page",
    "Ativação",
    "Copiloto",
    "Jornada",
    "Demonstração",
    "Trilha Valoris",
    "Início",
    "Painel Executivo",
    "Valuation",
    "Simulador",
    "Tese & Convicção",
    "Checklist",
    "Watchlist",
    "Relatórios",
    "Feedback Beta",
    "Beta Fechado",
    "Neg?cio",
    "Marketing",
    "Conte?do",
    "Lançamento",
    "Convite Beta",
    "Release",
    "Aprendizado Beta",
    "Rodadas Beta",
    "Prioridades Beta",
    "Sprints Beta",
    "Pré-venda Beta",
    "Oferta Paga",
    "CRM Beta",
    "Painel Beta",
    "Fase 3",
    "Clientes Beta",
    "Suporte Beta",
    "Reten??o Beta",
    "Painel Fase 3",
    "Métricas Fase 3",
    "Decisão Fase 3",
    "Plano Fase 4",
    "Arquitetura Fase 4",
    "Core Engine",
    "Compatibilidade Core",
    "Motor Adapter",
    "Motor Controlado",
    "Auditoria Motor Principal",
    "Fallback Motor",
    "Logs Motor",
    "Saúde Motor",
    "Decis?o Core",
    "Promoção Core",
    "Estrat?gia Produto",
    "Deploy Público",
    "Dados",
    "Analytics Público",
    "Painel Trilha",
    "Painel Copiloto",
    "Painel Jornada",
    "Painel Ativação",
    "Painel Conversão",
    "Growth",
    "Validação Manual",
    "Fundadores",
    "Maturidade",
    "Arquitetura",
    "Camada Dados",
    "SQLite Piloto",
    "Repositórios",
    "PostgreSQL",
    "API",
    "API Scaffold",
    "API Smoke",
    "API Bridge",
    "API Tests",
    "API SQLite",
    "API Adapter",
    "API Security",
    "API Security Panel",
    "API Database Cloud",
    "API Database Contracts",
    "API Database Providers",
    "API Provider Runtime",
    "API Provider Backend",
    "Launch Readiness",
    "Análise Premium",
    "Demo 2 Min",
    "Beta Público",
    "UX",
    "Multiativos",
    "Ações Brasil",
    "FIIs",
    "Renda Fixa",
    "Resumo da Decisão",
    "Comparativo",
    "Tese qualitativa",
    "Premissas",
    "Histórico",
    "Educação",
    "Roadmap Premium",
    "Feedback Pacote",
    "Pacote Premium",
    "Relatório Premium v2",
    "Comparador Setorial",
    "Watchlist Fundadores",
    "Retenção Fundadores",
    "Checkout Fundadores",
    "Oferta Beta",
    "Onboarding Premium",
    "Beta Insights",
    "Beta Feedback",
    "Lista de Espera",
    "Gateway Dados",
]

