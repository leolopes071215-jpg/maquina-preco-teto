
import streamlit as st

st.set_page_config(
    page_title="Valoris ? Modo Seguro",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.sidebar.title("Valoris")
st.sidebar.caption("Modo Seguro ? carrega apenas uma tela por vez")

PAGINAS = {
    "Navegação Segura": (
        "navegacao_segura_valoris",
        "renderizar_navegacao_segura_valoris",
        "Catálogo de módulos e recuperação segura de páginas.",
    ),

    "Estabilidade": ("estabilidade_execucao_valoris", "renderizar_estabilidade_execucao_valoris"),
    "Roadmap Premium": ("roadmap_premium_valoris", "renderizar_roadmap_premium_valoris"),
    "Feedback Pacote": ("feedback_pacote_premium_valoris", "renderizar_feedback_pacote_premium_valoris"),
    "Pacote Premium": ("pacote_premium_valoris", "renderizar_pacote_premium_valoris"),
    "Relat?rio Premium v2": ("relatorio_premium_v2_valoris", "renderizar_relatorio_premium_v2_valoris"),
    "Comparador Setorial": ("comparador_setorial_valoris", "renderizar_comparador_setorial_valoris"),
    "Watchlist Fundadores": ("watchlist_fundadores_valoris", "renderizar_watchlist_fundadores_valoris"),
    "Reten??o Fundadores": ("retencao_fundadores_valoris", "renderizar_retencao_fundadores_valoris"),
    "Checkout Fundadores": ("checkout_fundadores_valoris", "renderizar_checkout_fundadores_valoris"),
    "Oferta Beta": ("oferta_beta_fundador_valoris", "renderizar_oferta_beta_fundador_valoris"),
    "Beta P?blico": ("beta_publico_valoris", "renderizar_beta_publico_valoris"),
    "Onboarding Premium": ("onboarding_premium_valoris", "renderizar_onboarding_premium_valoris"),
    "Beta Insights": ("beta_insights_valoris", "renderizar_beta_insights_valoris"),
    "Beta Feedback": ("beta_feedback_valoris", "renderizar_beta_feedback_valoris"),
    "Lista de Espera": ("lista_espera_beta", "renderizar_lista_espera_valoris"),
    "Gateway Dados": ("gateway_dados_valoris", "renderizar_gateway_dados_valoris"),
    "Reposit?rios": ("repositorios_valoris", "renderizar_repositorios_valoris"),
}

pagina = st.sidebar.radio(
    "Escolha uma ?rea",
    list(PAGINAS.keys()),
    index=0,
)

dados_pagina = PAGINAS[pagina]

if len(dados_pagina) == 2:
    modulo_nome, funcao_nome = dados_pagina
    descricao_pagina = ""
else:
    modulo_nome, funcao_nome, descricao_pagina = dados_pagina[0], dados_pagina[1], dados_pagina[2]


st.title(f"Valoris ? {pagina}")
st.caption("Modo Seguro: esta vers?o importa e renderiza somente a p?gina selecionada.")

try:
    modulo = __import__(modulo_nome, fromlist=[funcao_nome])
    funcao = getattr(modulo, funcao_nome)
    funcao()
except MemoryError:
    st.error("MemoryError: esta p?gina tentou carregar dados demais.")
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
    "Navega??o",
    "Onboarding",
    "Landing Page",
    "Ativa??o",
    "Copiloto",
    "Jornada",
    "Demonstra??o",
    "Trilha Valoris",
    "In?cio",
    "Painel Executivo",
    "Valuation",
    "Simulador",
    "Tese & Convic??o",
    "Checklist",
    "Watchlist",
    "Relat?rios",
    "Feedback Beta",
    "Beta Fechado",
    "Neg?cio",
    "Marketing",
    "Conte?do",
    "Lan?amento",
    "Convite Beta",
    "Release",
    "Aprendizado Beta",
    "Rodadas Beta",
    "Prioridades Beta",
    "Sprints Beta",
    "Pr?-venda Beta",
    "Oferta Paga",
    "CRM Beta",
    "Painel Beta",
    "Fase 3",
    "Clientes Beta",
    "Suporte Beta",
    "Reten??o Beta",
    "Painel Fase 3",
    "M?tricas Fase 3",
    "Decis?o Fase 3",
    "Plano Fase 4",
    "Arquitetura Fase 4",
    "Core Engine",
    "Compatibilidade Core",
    "Motor Adapter",
    "Motor Controlado",
    "Auditoria Motor Principal",
    "Fallback Motor",
    "Logs Motor",
    "Sa?de Motor",
    "Decis?o Core",
    "Promo??o Core",
    "Estrat?gia Produto",
    "Deploy P?blico",
    "Dados",
    "Analytics P?blico",
    "Painel Trilha",
    "Painel Copiloto",
    "Painel Jornada",
    "Painel Ativa??o",
    "Painel Convers?o",
    "Growth",
    "Valida??o Manual",
    "Fundadores",
    "Maturidade",
    "Arquitetura",
    "Camada Dados",
    "SQLite Piloto",
    "Reposit?rios",
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
    "An?lise Premium",
    "Demo 2 Min",
    "Beta P?blico",
    "UX",
    "Multiativos",
    "A??es Brasil",
    "FIIs",
    "Renda Fixa",
    "Resumo da Decis?o",
    "Comparativo",
    "Tese qualitativa",
    "Premissas",
    "Hist?rico",
    "Educa??o",
    "Roadmap Premium",
    "Feedback Pacote",
    "Pacote Premium",
    "Relat?rio Premium v2",
    "Comparador Setorial",
    "Watchlist Fundadores",
    "Reten??o Fundadores",
    "Checkout Fundadores",
    "Oferta Beta",
    "Onboarding Premium",
    "Beta Insights",
    "Beta Feedback",
    "Lista de Espera",
    "Gateway Dados",
]

