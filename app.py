import csv
from io import StringIO

import streamlit as st

from valuation import EntradasValuation
from empresas import EMPRESAS
from historico import salvar_analise, carregar_historico, CAMINHO_HISTORICO
from style import aplicar_estilo
from inicio import renderizar_inicio_premium
from proposta_valor import renderizar_proposta_valor
from navegacao_simplificada import renderizar_navegacao_simplificada
from onboarding_usuario import renderizar_onboarding_usuario
from feedback_beta import renderizar_feedback_beta
from beta_fechado import renderizar_beta_fechado
from oferta_beta import renderizar_oferta_beta
from dashboard_negocio import renderizar_dashboard_negocio
from marketing import renderizar_central_marketing
from conteudo_marketing import renderizar_central_conteudo
from landing_page_beta import renderizar_landing_page_beta
from demo_guiada_valoris import renderizar_demo_guiada_valoris
from trilha_educativa_valoris import renderizar_trilha_educativa_valoris, renderizar_painel_trilha_educativa_valoris
from copiloto_valoris import renderizar_copiloto_valoris, renderizar_painel_copiloto_valoris
from jornada_personalizada_valoris import renderizar_jornada_personalizada_valoris, renderizar_painel_jornada_personalizada_valoris
from hub_ativacao_valoris import renderizar_hub_ativacao_valoris, renderizar_painel_hub_ativacao_valoris
from conversao_fundador_valoris import renderizar_conversao_fundador_valoris, renderizar_painel_conversao_fundador_valoris
from laboratorio_growth_valoris import renderizar_laboratorio_growth_valoris
from validacao_manual_valoris import renderizar_validacao_manual_valoris
from central_fundadores_valoris import renderizar_central_fundadores_valoris
from maturidade_produto_valoris import renderizar_maturidade_produto_valoris
from arquitetura_transicao_valoris import renderizar_arquitetura_transicao_valoris
from camada_dados_valoris import renderizar_camada_dados_valoris
from gateway_dados_valoris import renderizar_gateway_dados_valoris
from piloto_sqlite_valoris import renderizar_piloto_sqlite_valoris
from repositorios_valoris import renderizar_repositorios_valoris
from postgres_supabase_valoris import renderizar_postgres_supabase_valoris
from api_contratos_valoris import renderizar_api_contratos_valoris
from api_scaffold_valoris import renderizar_api_scaffold_valoris
from api_smoke_tests_valoris import renderizar_api_smoke_tests_valoris
from api_repository_bridge_valoris import renderizar_api_repository_bridge_valoris
from api_endpoint_tests_valoris import renderizar_api_endpoint_tests_valoris
from api_sqlite_bridge_valoris import renderizar_api_sqlite_bridge_valoris
from api_storage_adapter_valoris import renderizar_api_storage_adapter_valoris
from api_security_key_valoris import renderizar_api_security_key_valoris
from api_security_panel_valoris import renderizar_api_security_panel_valoris
from api_database_cloud_valoris import renderizar_api_database_cloud_valoris
from api_database_contracts_valoris import renderizar_api_database_contracts_valoris
from api_database_providers_valoris import renderizar_api_database_providers_valoris
from api_provider_runtime_valoris import renderizar_api_provider_runtime_valoris
from api_provider_backend_valoris import renderizar_api_provider_backend_valoris
from launch_readiness_valoris import renderizar_launch_readiness_valoris
from analise_premium_valoris import renderizar_analise_premium_valoris
from demo_guiada_2min_valoris import renderizar_demo_guiada_2min_valoris
from beta_feedback_valoris import renderizar_beta_feedback_valoris
from beta_insights_valoris import renderizar_beta_insights_valoris
from lancamento_beta import renderizar_lancamento_beta
from convite_beta_publico import renderizar_convite_beta_publico
from release_candidate import renderizar_release_candidate_fase1
from aprendizado_beta_real import renderizar_aprendizado_beta_real
from rodadas_beta import renderizar_rodadas_beta
from priorizacao_feedback import renderizar_priorizacao_feedback_beta
from sprints_beta import renderizar_sprints_beta
from pre_venda_beta import renderizar_pre_venda_beta
from oferta_beta_pago import renderizar_oferta_beta_pago
from crm_beta import renderizar_crm_beta
from painel_beta import renderizar_painel_beta
from fase3_lancamento import renderizar_fase3_lancamento
from clientes_beta import renderizar_clientes_beta
from suporte_beta import renderizar_suporte_beta
from retencao_beta import renderizar_retencao_beta
from painel_fase3 import renderizar_painel_fase3
from metricas_fase3 import renderizar_metricas_fase3
from go_no_go_fase3 import renderizar_go_no_go_fase3
from plano_fase4 import renderizar_plano_fase4
from arquitetura_fase4 import renderizar_arquitetura_fase4
from painel_core_engine import renderizar_painel_core_engine
from painel_compatibilidade_core import renderizar_painel_compatibilidade_core
from painel_motor_adapter import renderizar_painel_motor_adapter
from painel_motor_controlado import renderizar_painel_motor_controlado
from painel_auditoria_motor_principal import renderizar_painel_auditoria_motor_principal
from painel_fallback_motor import renderizar_painel_fallback_motor
from painel_logs_motor import renderizar_painel_logs_motor
from painel_saude_motor import renderizar_painel_saude_motor
from painel_decisao_core import renderizar_painel_decisao_core
from painel_promocao_core import renderizar_painel_promocao_core
from produto_estrategico import renderizar_produto_estrategico
from deploy_publico import renderizar_deploy_publico
from analytics_publico_valoris import renderizar_painel_analytics_publico, registrar_visualizacao_unica
from experiencia_beta import renderizar_experiencia_usuario_beta
from persistencia_dados import renderizar_central_persistencia_dados
from auditoria_ux import renderizar_auditoria_ux
from educacional import renderizar_aba_educacional
from simulador import renderizar_simulador_cenarios
from relatorio import gerar_relatorio_markdown, gerar_nome_arquivo_relatorio
from conviccao import renderizar_aba_conviccao
from decisao import render_resumo_decisao, gerar_bloco_markdown_decisao
from checklist import renderizar_checklist_erros
from central_multiativos import renderizar_central_multiativos
from central_relatorios import renderizar_central_relatorios
from acoes_brasil import renderizar_motor_acoes_brasil
from fiis import renderizar_motor_fiis
from renda_fixa import renderizar_motor_renda_fixa
from painel_multiativos import renderizar_painel_executivo_multiativos
from watchlist import renderizar_watchlist_multiativos
from modo_exibicao import (
    MODO_FUNDADOR,
    MODO_USUARIO_BETA,
    obter_abas_por_modo,
    obter_mensagem_modo_para_hero,
    obter_rotulo_metrica_modo,
    renderizar_controle_modo_exibicao,
    renderizar_painel_modo_exibicao,
)
from modos_analise import (
    obter_opcoes_modelo,
    obter_dados_modelo,
    obter_tipo_analise,
    obter_aviso_modo,
    obter_titulo_modo,
    obter_descricao_modo,
    eh_modo_demonstracao,
    eh_nova_analise_manual,
)
from motor_valuation_controlado import (
    obter_descricao_motor,
    obter_motor_padrao,
    obter_motores_disponiveis,
)
from logs_motor_valuation import (
    CAMINHO_LOGS_MOTOR,
    calcular_valuation_com_log,
)
from comparativo import (
    gerar_comparativo,
    encontrar_empresa_mais_atrativa,
    gerar_ranking_empresas_reais,
)


st.set_page_config(
    page_title="Valoris",
    page_icon="📈",
    layout="wide",
)

aplicar_estilo()


ABAS_ORDEM_COMPLETA = [
    "Landing Page",
    "Ativação",
    "Copiloto",
    "Jornada",
    "Demonstração",
    "Trilha Valoris",
    "Início",
    "Valuation",
    "Relatórios",
    "Conversão",
    "Convite Beta",
    "Oferta Beta",
    "Feedback Beta",
    "Educação",
    "Produto",
    "Navegação",
    "Onboarding",
    "Painel Executivo",
    "Simulador",
    "Tese & Convicção",
    "Checklist",
    "Watchlist",
    "Beta Fechado",
    "Negócio",
    "Marketing",
    "Conteúdo",
    "Lançamento",
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
    "Retenção Beta",
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
    "Decisão Core",
    "Promoção Core",
    "Estratégia Produto",
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
    "Gateway Dados",
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
    "Beta Feedback",
    "Beta Insights",
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
]


def formatar_moeda(valor: float, simbolo: str = "R$") -> str:
    return f"{simbolo} {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def formatar_numero(valor: float) -> str:
    return f"{valor:,.0f}".replace(",", ".")


def formatar_percentual(valor: float) -> str:
    return f"{valor:.2f}%"


def preparar_tabela(tabela: list[dict]) -> list[dict]:
    return [
        {chave: str(valor) for chave, valor in linha.items()}
        for linha in tabela
    ]


def converter_tabela_para_csv(tabela: list[dict]) -> str:
    if len(tabela) == 0:
        return ""

    saida = StringIO()
    campos = tabela[0].keys()

    escritor = csv.DictWriter(saida, fieldnames=campos)
    escritor.writeheader()
    escritor.writerows(tabela)

    return saida.getvalue()


def obter_rotulo_motor_executado(resultado: dict, motor_valuation: str) -> str:
    return str(
        resultado.get(
            "motor_executado",
            resultado.get("motor_selecionado", motor_valuation),
        )
    )


def renderizar_hero(modo_exibicao: str, motor_valuation: str) -> None:
    if modo_exibicao == MODO_USUARIO_BETA:
        registrar_visualizacao_unica(
            chave="porta_publica_app",
            evento="landing_visualizada",
            origem="app_hero_publico",
            contexto="porta_publica",
            detalhe="Hero público da Valoris visualizado.",
        )

        st.markdown(
            """
            <style>
                .public-gateway {
                    padding: clamp(1rem, 2.8vw, 1.65rem);
                    border-radius: 28px;
                    border: 1px solid rgba(255, 255, 255, 0.09);
                    background:
                        radial-gradient(circle at top left, rgba(214, 181, 109, 0.22), transparent 30%),
                        radial-gradient(circle at bottom right, rgba(36, 128, 91, 0.22), transparent 34%),
                        linear-gradient(135deg, rgba(8, 15, 27, 0.99), rgba(5, 9, 18, 0.99));
                    box-shadow: 0 18px 52px rgba(0, 0, 0, 0.28);
                    margin-bottom: 0.8rem;
                }

                .public-gateway-eyebrow {
                    color: #d6b56d;
                    font-size: 0.73rem;
                    letter-spacing: 0.14em;
                    text-transform: uppercase;
                    font-weight: 850;
                    margin-bottom: 0.35rem;
                }

                .public-gateway-title {
                    color: #f4f7fb;
                    font-size: clamp(1.7rem, 5vw, 2.7rem);
                    font-weight: 940;
                    line-height: 1.02;
                    letter-spacing: -0.055em;
                    margin-bottom: 0.5rem;
                }

                .public-gateway-text {
                    color: rgba(244, 247, 251, 0.74);
                    font-size: 0.96rem;
                    line-height: 1.52;
                    max-width: 980px;
                }

                .public-gateway-pills {
                    display: flex;
                    gap: 0.5rem;
                    flex-wrap: wrap;
                    margin-top: 0.85rem;
                }

                .public-gateway-pill {
                    display: inline-block;
                    padding: 0.32rem 0.62rem;
                    border-radius: 999px;
                    color: #d6b56d;
                    border: 1px solid rgba(214, 181, 109, 0.22);
                    background: rgba(214, 181, 109, 0.08);
                    font-size: 0.76rem;
                    font-weight: 780;
                }

                @media (max-width: 520px) {
                    .public-gateway {
                        border-radius: 20px;
                    }
                }
            </style>

            <div class="public-gateway">
                <div class="public-gateway-eyebrow">Valoris • Porta de entrada pública</div>
                <div class="public-gateway-title">Audite sua decisão antes de investir.</div>
                <div class="public-gateway-text">
                    Comece pela Landing Page para entender a proposta. Depois explore a demonstração,
                    revise o valuation, baixe o relatório e entre na lista beta se fizer sentido.
                </div>
                <div class="public-gateway-pills">
                    <span class="public-gateway-pill">Landing</span>
                    <span class="public-gateway-pill">Demonstração guiada</span>
                    <span class="public-gateway-pill">Relatório</span>
                    <span class="public-gateway-pill">Lista beta</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.caption(
            "Fluxo público sugerido: Landing Page → Ativação → Copiloto → Jornada → Demonstração → Trilha Valoris → Início → Valuation → Relatórios → Conversão → Convite Beta → Oferta Beta."
        )
        return

    st.markdown("# VALORIS")

    st.markdown(
        """
        ### Plataforma de Valuation, Análise Fundamentalista e Decisão de Investimentos

        O Valoris organiza o processo completo do investidor racional: premissas, valuation,
        tese, checklist, margem de segurança, comparação, relatório, aprendizado beta e governança do produto.
        """
    )

    st.caption(
        "Produto • Navegação • Onboarding • Valuation • Tese • Checklist • Watchlist • Relatórios • Beta Real • Rodadas • Prioridades • Sprints • Pré-venda • Oferta Paga • CRM • Painel Beta • Fase 3 • Clientes Beta • Suporte Beta • Retenção Beta • Painel Fase 3 • Métricas Fase 3 • Decisão Fase 3 • Plano Fase 4 • Arquitetura Fase 4 • Core Engine • Compatibilidade Core • Motor Adapter • Motor Controlado • Auditoria Motor Principal • Fallback Motor • Logs Motor • Saúde Motor • Decisão Core • Promoção Core • Estratégia Produto • Deploy Público • Negócio • Marketing • Release • Dados • UX"
    )

    col_home_1, col_home_2, col_home_3, col_home_4 = st.columns(4)

    with col_home_1:
        st.metric("Empresas", len(EMPRESAS))

    with col_home_2:
        st.metric("Motor preferido", motor_valuation)

    with col_home_3:
        st.metric("Arquitetura", "Multiativos")

    with col_home_4:
        st.metric("Modo", obter_rotulo_metrica_modo(modo_exibicao))

    st.info(obter_mensagem_modo_para_hero(modo_exibicao))

    st.warning(
        "Uso educacional. Não representa recomendação de compra, venda ou manutenção de investimentos. "
        "Os resultados dependem diretamente das premissas inseridas."
    )

    st.divider()

def renderizar_barra_valuation(
    rotulo: str,
    valor: float,
    valor_maximo: float,
    simbolo: str,
) -> None:
    if valor_maximo <= 0:
        proporcao = 0.0
    else:
        proporcao = min(max(valor / valor_maximo, 0), 1)

    col_label, col_valor = st.columns([3, 1])

    with col_label:
        st.caption(rotulo)

    with col_valor:
        st.markdown(f"**{formatar_moeda(valor, simbolo)}**")

    st.progress(proporcao)


def renderizar_mapa_valuation(
    preco_atual: float,
    preco_teto: float,
    preco_justo: float,
    simbolo: str,
) -> None:
    valor_maximo = max(preco_atual, preco_teto, preco_justo, 1)

    with st.container(border=True):
        st.markdown("### Mapa visual do valuation")

        st.caption(
            "Leitura visual entre preço atual, preço-teto conservador e preço justo estimado."
        )

        renderizar_barra_valuation(
            "Preço atual",
            preco_atual,
            valor_maximo,
            simbolo,
        )

        renderizar_barra_valuation(
            "Preço-teto com margem de segurança",
            preco_teto,
            valor_maximo,
            simbolo,
        )

        renderizar_barra_valuation(
            "Preço justo estimado",
            preco_justo,
            valor_maximo,
            simbolo,
        )

        if preco_atual <= preco_teto:
            st.success(
                "Leitura: o preço atual está abaixo ou igual ao preço-teto. "
                "Pelas premissas atuais, está dentro da zona conservadora do modelo."
            )
        elif preco_atual <= preco_justo:
            st.warning(
                "Leitura: o preço atual está acima do preço-teto, mas ainda abaixo ou próximo do preço justo. "
                "Não está barato o suficiente para uma entrada conservadora."
            )
        else:
            st.error(
                "Leitura: o preço atual está acima do preço justo estimado. "
                "Pelas premissas atuais, o modelo indica paciência."
            )


def renderizar_painel_decisao(
    preco_atual: float,
    resultado: dict,
    simbolo_moeda: str,
    motor_valuation: str,
) -> None:
    with st.container(border=True):
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            st.metric(
                label="Preço atual",
                value=formatar_moeda(preco_atual, simbolo_moeda),
            )

        with col2:
            st.metric(
                label="Preço-teto",
                value=formatar_moeda(resultado["preco_teto"], simbolo_moeda),
                delta=formatar_percentual(resultado["margem_ate_preco_teto"]),
            )

        with col3:
            status = resultado["status"]

            if status == "COMPRA":
                st.success("Status educacional: COMPRA")
            elif status == "NEUTRO":
                st.warning("Status educacional: NEUTRO")
            else:
                st.error("Status educacional: AGUARDE")

        st.markdown("#### Leitura automática")
        st.info(resultado["explicacao_status"])

        motor_executado = obter_rotulo_motor_executado(resultado, motor_valuation)

        st.caption(f"Motor preferido: {motor_valuation}")
        st.caption(f"Motor executado: {motor_executado}")

        if resultado.get("fallback_ocorreu"):
            st.warning(
                "Fallback executado: o motor preferido falhou e o sistema voltou automaticamente para Legacy."
            )

        if resultado.get("log_motor_registrado"):
            st.caption(f"Log técnico registrado: {resultado.get('id_log_motor', '')}")


def renderizar_radar_oportunidade(melhor_empresa: dict) -> None:
    with st.container(border=True):
        st.markdown("#### Radar de oportunidade pelo modelo")

        st.caption(
            "Identifica a empresa real mais bem posicionada pelo score de proximidade ao preço-teto. "
            "Não representa recomendação de compra."
        )

        col_1, col_2, col_3, col_4 = st.columns(4)

        with col_1:
            st.metric("Empresa", melhor_empresa["ticker"])

        with col_2:
            st.metric("Score", melhor_empresa["score_formatado"])

        with col_3:
            st.metric("Status", melhor_empresa["status"])

        with col_4:
            st.metric("Margem até teto", melhor_empresa["margem_ate_preco_teto"])

        st.info(
            f"""
            **{melhor_empresa["empresa"]}** é a empresa real melhor posicionada pelo modelo neste momento.  
            Preço atual: **{melhor_empresa["preco_atual"]}**.  
            Preço-teto: **{melhor_empresa["preco_teto"]}**.  
            Preço justo estimado: **{melhor_empresa["preco_justo"]}**.

            **Leitura executiva:** {melhor_empresa["leitura"]}
            """
        )


def renderizar_ranking_visual(ranking_empresas_reais: list[dict]) -> None:
    st.markdown("#### Ranking visual das empresas reais")

    st.caption(
        "Ordenado pelo score de atratividade. O score mede proximidade ao preço-teto e leitura do status, não qualidade absoluta da empresa."
    )

    if len(ranking_empresas_reais) == 0:
        st.warning("Nenhuma empresa real cadastrada para gerar ranking.")
        return

    top_empresas = ranking_empresas_reais[:3]
    colunas = st.columns(len(top_empresas))

    for coluna, empresa in zip(colunas, top_empresas):
        with coluna:
            with st.container(border=True):
                st.markdown(f"### #{empresa['Ranking']} — {empresa['Ticker']}")
                st.metric("Score", empresa["Score"])
                st.caption(empresa["Empresa"])
                st.markdown(f"**Status:** {empresa['Status']}")
                st.markdown(f"**Margem até teto:** {empresa['Margem até preço-teto']}")
                st.markdown(f"**Potencial até justo:** {empresa['Potencial até preço justo']}")


with st.sidebar:
    st.header("Configuração")

    modo_exibicao = renderizar_controle_modo_exibicao()

    st.divider()

    st.header("Modo e premissas")

    opcoes_modelo = obter_opcoes_modelo(EMPRESAS)

    modelo_escolhido = st.selectbox(
        "Escolha o modo de análise",
        opcoes_modelo,
    )

    dados = obter_dados_modelo(modelo_escolhido, EMPRESAS)

    modo_demonstracao = eh_modo_demonstracao(modelo_escolhido)
    nova_analise_manual = eh_nova_analise_manual(modelo_escolhido)
    modo_usuario = modo_demonstracao or nova_analise_manual

    tipo_analise = obter_tipo_analise(modelo_escolhido)

    st.markdown(f"#### {obter_titulo_modo(modelo_escolhido)}")
    st.caption(obter_descricao_modo(modelo_escolhido))

    if modo_demonstracao:
        st.warning(obter_aviso_modo(modelo_escolhido))
    elif nova_analise_manual:
        st.info(obter_aviso_modo(modelo_escolhido))
    else:
        st.info(obter_aviso_modo(modelo_escolhido))

    if modo_usuario:
        simbolo_moeda = st.selectbox(
            "Moeda da análise",
            ["R$", "US$"],
            index=0 if dados.get("simbolo_moeda", "R$") == "R$" else 1,
            help="Escolha apenas o símbolo visual. Os números devem ser inseridos de forma consistente.",
        )

        dados["simbolo_moeda"] = simbolo_moeda
    else:
        simbolo_moeda = dados.get("simbolo_moeda", "R$")

    st.caption("Os dados iniciais são editáveis e podem ser ajustados manualmente.")

    st.markdown("#### Empresa")

    empresa = st.text_input(
        "Nome da empresa",
        value=dados["empresa"],
        key=f"empresa_{modelo_escolhido}",
    )

    ticker = st.text_input(
        "Ticker",
        value=dados["ticker"],
        key=f"ticker_{modelo_escolhido}",
    )

    st.divider()

    st.markdown("#### Dados financeiros")

    lucro_liquido_sustentavel = st.number_input(
        "Lucro líquido sustentável",
        min_value=-1_000_000_000_000.0,
        value=float(dados["lucro_liquido_sustentavel"]),
        step=100.0 if modo_usuario else 100_000_000.0,
        help="Use um lucro normalizado, evitando anos extraordinários.",
        key=f"lucro_{modelo_escolhido}",
    )

    fluxo_caixa_livre = st.number_input(
        "Fluxo de caixa livre",
        min_value=-1_000_000_000_000.0,
        value=float(dados["fluxo_caixa_livre"]),
        step=100.0 if modo_usuario else 100_000_000.0,
        help="Fluxo de caixa operacional menos investimentos necessários.",
        key=f"fcf_{modelo_escolhido}",
    )

    quantidade_acoes = st.number_input(
        "Quantidade de ações",
        min_value=1.0,
        value=float(dados["quantidade_acoes"]),
        step=10.0 if modo_usuario else 10_000_000.0,
        help="Quantidade total de ações da empresa. Use a mesma escala dos outros dados.",
        key=f"acoes_{modelo_escolhido}",
    )

    preco_atual = st.number_input(
        "Preço atual da ação",
        min_value=0.01,
        value=float(dados["preco_atual"]),
        step=0.50,
        key=f"preco_{modelo_escolhido}",
    )

    st.divider()

    st.markdown("#### Premissas de valuation")

    multiplo_justo_eps = st.number_input(
        "Múltiplo justo de EPS",
        min_value=0.0,
        value=float(dados["multiplo_justo_eps"]),
        step=0.5,
        help="Exemplo: P/L justo que você aceita pagar pela empresa.",
        key=f"mult_eps_{modelo_escolhido}",
    )

    multiplo_justo_fcf = st.number_input(
        "Múltiplo justo de FCF",
        min_value=0.0,
        value=float(dados["multiplo_justo_fcf"]),
        step=0.5,
        help="Exemplo: P/FCF justo que você aceita pagar pela empresa.",
        key=f"mult_fcf_{modelo_escolhido}",
    )

    peso_eps = st.slider(
        "Peso do EPS no valuation",
        min_value=0,
        max_value=100,
        value=int(dados["peso_eps"]),
        key=f"peso_eps_{modelo_escolhido}",
    )

    peso_fcf = st.slider(
        "Peso do FCF no valuation",
        min_value=0,
        max_value=100,
        value=int(dados["peso_fcf"]),
        key=f"peso_fcf_{modelo_escolhido}",
    )

    margem_seguranca = st.slider(
        "Margem de segurança",
        min_value=0,
        max_value=90,
        value=int(dados["margem_seguranca"]),
        key=f"margem_{modelo_escolhido}",
    )

    st.divider()

    if modo_exibicao == MODO_FUNDADOR:
        st.markdown("#### Motor de valuation")

        motores_disponiveis = obter_motores_disponiveis()

        if "motor_valuation_principal" not in st.session_state:
            st.session_state["motor_valuation_principal"] = obter_motor_padrao()

        motor_valuation = st.selectbox(
            "Motor usado no cálculo principal",
            motores_disponiveis,
            index=motores_disponiveis.index(st.session_state["motor_valuation_principal"]),
            help="Use Legacy como padrão seguro. Use Core Engine apenas para teste controlado.",
            key="motor_valuation_principal",
        )

        descricao_motor = obter_descricao_motor(motor_valuation)

        st.caption(descricao_motor["descricao"])

        permitir_fallback_principal = st.checkbox(
            "Permitir fallback automático para Legacy",
            value=True,
            help="Se o Core Engine falhar, o app volta automaticamente para Legacy.",
            key="permitir_fallback_principal",
        )

        if motor_valuation == "Core Engine":
            st.warning(
                "Core Engine ativado no fluxo principal. O fallback automático deve permanecer ligado durante a transição."
            )
        else:
            st.success("Legacy ativo como motor seguro padrão.")
    else:
        motor_valuation = obter_motor_padrao()
        permitir_fallback_principal = True


renderizar_hero(
    modo_exibicao=modo_exibicao,
    motor_valuation=motor_valuation,
)

if modo_exibicao == MODO_USUARIO_BETA:
    st.info(
        "Esta é a porta pública da Valoris. A análise já fica preparada nos bastidores para alimentar a demonstração, "
        "o relatório e a experiência beta, mas a jornada começa pela proposta de valor."
    )
else:
    st.subheader(f"Análise de valuation: {empresa} ({ticker.upper()})")

    if modo_demonstracao:
        st.warning(
            "Modo Demonstração: os dados desta análise são fictícios. Use apenas para conhecer o funcionamento da plataforma."
        )
    elif nova_analise_manual:
        st.info(
            "Nova Análise Manual: substitua os dados padrão por informações reais antes de interpretar o status educacional."
        )
    else:
        st.info(
            "Empresa da base: revise todas as premissas antes de considerar qualquer conclusão educacional."
        )

try:
    entradas = EntradasValuation(
        empresa=empresa,
        ticker=ticker.upper(),
        lucro_liquido_sustentavel=lucro_liquido_sustentavel,
        fluxo_caixa_livre=fluxo_caixa_livre,
        quantidade_acoes=quantidade_acoes,
        multiplo_justo_eps=multiplo_justo_eps,
        multiplo_justo_fcf=multiplo_justo_fcf,
        peso_eps=peso_eps,
        peso_fcf=peso_fcf,
        margem_seguranca=margem_seguranca,
        preco_atual=preco_atual,
    )

    resultado = calcular_valuation_com_log(
        entradas=entradas,
        motor_preferido=motor_valuation,
        moeda=simbolo_moeda,
        permitir_fallback=permitir_fallback_principal,
        origem="app",
        contexto="fluxo_principal",
        caminho_log=CAMINHO_LOGS_MOTOR,
        forcar_falha_core=False,
    )

    motor_executado = obter_rotulo_motor_executado(resultado, motor_valuation)

    st.session_state["resultado_valuation"] = {
        "empresa": empresa,
        "ticker": ticker.upper(),
        "tipo_analise": tipo_analise,
        "modelo_escolhido": modelo_escolhido,
        "status_valuation": resultado["status"],
        "status": resultado["status"],
        "preco_atual": preco_atual,
        "preco_teto": resultado["preco_teto"],
        "preco_justo": resultado["preco_justo_combinado"],
        "preco_justo_combinado": resultado["preco_justo_combinado"],
        "margem_seguranca": margem_seguranca,
        "margem_ate_preco_teto": resultado["margem_ate_preco_teto"],
        "potencial_ate_preco_justo": resultado["potencial_ate_preco_justo"],
        "simbolo_moeda": simbolo_moeda,
        "motor_preferido": motor_valuation,
        "motor_executado": motor_executado,
        "motor_selecionado": resultado.get("motor_selecionado", motor_valuation),
        "motor_id": resultado.get("motor_id", ""),
        "motor_executado_id": resultado.get("motor_executado_id", ""),
        "fallback_ocorreu": resultado.get("fallback_ocorreu", False),
        "status_fallback": resultado.get("status_fallback", ""),
        "log_motor_registrado": resultado.get("log_motor_registrado", False),
        "id_log_motor": resultado.get("id_log_motor", ""),
        "versao_logs_motor": resultado.get("versao_logs_motor", ""),
        "versao_fallback_motor": resultado.get("versao_fallback_motor", ""),
        "versao_motor_controlado": resultado.get("versao_motor_controlado", ""),
        "versao_motor": resultado.get("versao_motor", ""),
    }

    st.session_state["entradas_valuation"] = {
        "empresa": empresa,
        "ticker": ticker.upper(),
        "tipo_analise": tipo_analise,
        "modelo_escolhido": modelo_escolhido,
        "lucro_liquido_sustentavel": lucro_liquido_sustentavel,
        "fluxo_caixa_livre": fluxo_caixa_livre,
        "quantidade_acoes": quantidade_acoes,
        "multiplo_justo_eps": multiplo_justo_eps,
        "multiplo_justo_fcf": multiplo_justo_fcf,
        "peso_eps": peso_eps,
        "peso_fcf": peso_fcf,
        "margem_seguranca": margem_seguranca,
        "preco_atual": preco_atual,
        "motor_valuation": motor_valuation,
        "motor_executado": motor_executado,
        "fallback_ocorreu": resultado.get("fallback_ocorreu", False),
        "log_motor_registrado": resultado.get("log_motor_registrado", False),
        "id_log_motor": resultado.get("id_log_motor", ""),
    }

    if modo_exibicao == MODO_USUARIO_BETA:
        with st.expander("Ver painel técnico da análise demonstrativa", expanded=False):
            renderizar_painel_decisao(
                preco_atual=preco_atual,
                resultado=resultado,
                simbolo_moeda=simbolo_moeda,
                motor_valuation=motor_valuation,
            )

            st.caption(
                "Este painel técnico fica recolhido no modo público para não atrapalhar a jornada de conversão."
            )

        st.divider()
    else:
        renderizar_painel_decisao(
            preco_atual=preco_atual,
            resultado=resultado,
            simbolo_moeda=simbolo_moeda,
            motor_valuation=motor_valuation,
        )

        st.divider()

        col_salvar, col_info = st.columns([1, 3])

        with col_salvar:
            if st.button("Salvar análise"):
                salvar_analise(entradas, resultado)
                st.success("Análise salva com sucesso.")

        with col_info:
            st.caption(
                "O histórico registra as premissas usadas no momento do cálculo. "
                "Isso ajuda a comparar mudanças de valuation ao longo do tempo."
            )

        st.divider()

    abas_permitidas = obter_abas_por_modo(modo_exibicao)

    abas_visiveis = [
        nome_aba for nome_aba in ABAS_ORDEM_COMPLETA
        if nome_aba in abas_permitidas
    ]

    abas_renderizadas = st.tabs(abas_visiveis)

    for nome_aba, aba in zip(abas_visiveis, abas_renderizadas):
        with aba:
            if nome_aba == "Produto":
                renderizar_proposta_valor()

            elif nome_aba == "Navegação":
                renderizar_painel_modo_exibicao(modo_exibicao)
                st.divider()
                renderizar_navegacao_simplificada()

            elif nome_aba == "Onboarding":
                renderizar_onboarding_usuario()

            elif nome_aba == "Início":
                if modo_exibicao == MODO_USUARIO_BETA:
                    renderizar_experiencia_usuario_beta(
                        resultado_valuation=st.session_state["resultado_valuation"],
                        entradas_valuation=st.session_state["entradas_valuation"],
                    )
                else:
                    renderizar_inicio_premium(
                        resultado_valuation=st.session_state["resultado_valuation"]
                    )

            elif nome_aba == "Painel Executivo":
                renderizar_painel_executivo_multiativos()

            elif nome_aba == "Valuation":
                st.markdown("### Valuation")

                col_a, col_b = st.columns(2)

                with col_a:
                    st.metric(
                        "EPS normalizado",
                        formatar_moeda(resultado["eps_normalizado"], simbolo_moeda),
                    )

                with col_b:
                    st.metric(
                        "FCF por ação",
                        formatar_moeda(resultado["fcf_por_acao"], simbolo_moeda),
                    )

                col_c, col_d = st.columns(2)

                with col_c:
                    st.metric(
                        "Preço justo por EPS",
                        formatar_moeda(resultado["preco_justo_eps"], simbolo_moeda),
                    )

                with col_d:
                    st.metric(
                        "Preço justo por FCF",
                        formatar_moeda(resultado["preco_justo_fcf"], simbolo_moeda),
                    )

                st.divider()

                col_e, col_f = st.columns(2)

                with col_e:
                    st.metric(
                        "Preço justo combinado",
                        formatar_moeda(resultado["preco_justo_combinado"], simbolo_moeda),
                        formatar_percentual(resultado["potencial_ate_preco_justo"]),
                    )

                with col_f:
                    st.metric(
                        "Preço-teto com margem de segurança",
                        formatar_moeda(resultado["preco_teto"], simbolo_moeda),
                        formatar_percentual(resultado["margem_ate_preco_teto"]),
                    )

                st.divider()

                renderizar_mapa_valuation(
                    preco_atual=preco_atual,
                    preco_teto=resultado["preco_teto"],
                    preco_justo=resultado["preco_justo_combinado"],
                    simbolo=simbolo_moeda,
                )

                st.divider()

                st.markdown("### Tabela-resumo")

                tabela_resultado = [
                    {
                        "Indicador": "EPS normalizado",
                        "Valor": formatar_moeda(resultado["eps_normalizado"], simbolo_moeda),
                    },
                    {
                        "Indicador": "FCF por ação",
                        "Valor": formatar_moeda(resultado["fcf_por_acao"], simbolo_moeda),
                    },
                    {
                        "Indicador": "Preço justo por EPS",
                        "Valor": formatar_moeda(resultado["preco_justo_eps"], simbolo_moeda),
                    },
                    {
                        "Indicador": "Preço justo por FCF",
                        "Valor": formatar_moeda(resultado["preco_justo_fcf"], simbolo_moeda),
                    },
                    {
                        "Indicador": "Preço justo combinado",
                        "Valor": formatar_moeda(resultado["preco_justo_combinado"], simbolo_moeda),
                    },
                    {
                        "Indicador": "Preço-teto",
                        "Valor": formatar_moeda(resultado["preco_teto"], simbolo_moeda),
                    },
                    {
                        "Indicador": "Preço atual",
                        "Valor": formatar_moeda(preco_atual, simbolo_moeda),
                    },
                    {
                        "Indicador": "Status",
                        "Valor": resultado["status"],
                    },
                    {
                        "Indicador": "Tipo de análise",
                        "Valor": tipo_analise,
                    },
                    {
                        "Indicador": "Motor preferido",
                        "Valor": motor_valuation,
                    },
                    {
                        "Indicador": "Motor executado",
                        "Valor": motor_executado,
                    },
                    {
                        "Indicador": "Fallback ocorreu",
                        "Valor": "Sim" if resultado.get("fallback_ocorreu") else "Não",
                    },
                    {
                        "Indicador": "Log registrado",
                        "Valor": "Sim" if resultado.get("log_motor_registrado") else "Não",
                    },
                    {
                        "Indicador": "ID do log",
                        "Valor": resultado.get("id_log_motor", "N/D"),
                    },
                    {
                        "Indicador": "Versão logs",
                        "Valor": resultado.get("versao_logs_motor", "N/D"),
                    },
                ]

                st.table(preparar_tabela(tabela_resultado))

            elif nome_aba == "Simulador":
                renderizar_simulador_cenarios(
                    entradas_base=entradas,
                    simbolo_moeda=simbolo_moeda,
                    formatar_moeda=formatar_moeda,
                    formatar_percentual=formatar_percentual,
                    preparar_tabela=preparar_tabela,
                )

            elif nome_aba == "Tese & Convicção":
                renderizar_aba_conviccao(
                    empresa=empresa,
                    ticker=ticker,
                    resultado=resultado,
                    preparar_tabela=preparar_tabela,
                )

            elif nome_aba == "Checklist":
                renderizar_checklist_erros(
                    resultado_valuation=st.session_state["resultado_valuation"]
                )

            elif nome_aba == "Watchlist":
                renderizar_watchlist_multiativos(
                    resultado_valuation=st.session_state["resultado_valuation"]
                )

            elif nome_aba == "Relatórios":
                renderizar_central_relatorios(
                    entradas=entradas,
                    resultado=resultado,
                    dados_empresa=dados,
                    simbolo_moeda=simbolo_moeda,
                    formatar_moeda=formatar_moeda,
                    formatar_percentual=formatar_percentual,
                    formatar_numero=formatar_numero,
                )

            elif nome_aba == "Feedback Beta":
                renderizar_feedback_beta()

            elif nome_aba == "Beta Fechado":
                renderizar_beta_fechado()

            elif nome_aba == "Oferta Beta":
                renderizar_oferta_beta()

            elif nome_aba == "Negócio":
                renderizar_dashboard_negocio()

            elif nome_aba == "Marketing":
                renderizar_central_marketing()

            elif nome_aba == "Conteúdo":
                renderizar_central_conteudo()

            elif nome_aba == "Landing Page":
                renderizar_landing_page_beta()

            elif nome_aba == "Ativação":
                renderizar_hub_ativacao_valoris(
                    modo_compacto=False,
                    mostrar_cta=True,
                    chave_contexto="aba_ativacao",
                )

            elif nome_aba == "Copiloto":
                renderizar_copiloto_valoris(
                    modo_compacto=False,
                    mostrar_cta=True,
                    chave_contexto="aba_copiloto",
                )

            elif nome_aba == "Jornada":
                renderizar_jornada_personalizada_valoris(
                    modo_compacto=False,
                    mostrar_cta=True,
                    chave_contexto="aba_jornada",
                )

            elif nome_aba == "Demonstração":
                renderizar_demo_guiada_valoris(
                    modo_compacto=False,
                    mostrar_cta=True,
                    chave_contexto="aba_demonstracao",
                )

            elif nome_aba == "Trilha Valoris":
                renderizar_trilha_educativa_valoris(
                    modo_compacto=False,
                    mostrar_cta=True,
                    chave_contexto="aba_trilha_valoris",
                )

            elif nome_aba == "Lançamento":
                renderizar_lancamento_beta()

            elif nome_aba == "Conversão":
                renderizar_conversao_fundador_valoris(
                    modo_compacto=False,
                    mostrar_cta=True,
                    chave_contexto="aba_conversao",
                )

            elif nome_aba == "Convite Beta":
                renderizar_convite_beta_publico()

            elif nome_aba == "Release":
                renderizar_release_candidate_fase1()

            elif nome_aba == "Aprendizado Beta":
                renderizar_aprendizado_beta_real()

            elif nome_aba == "Rodadas Beta":
                renderizar_rodadas_beta()

            elif nome_aba == "Prioridades Beta":
                renderizar_priorizacao_feedback_beta()

            elif nome_aba == "Sprints Beta":
                renderizar_sprints_beta()

            elif nome_aba == "Pré-venda Beta":
                renderizar_pre_venda_beta()

            elif nome_aba == "Oferta Paga":
                renderizar_oferta_beta_pago()

            elif nome_aba == "CRM Beta":
                renderizar_crm_beta()

            elif nome_aba == "Painel Beta":
                renderizar_painel_beta()

            elif nome_aba == "Fase 3":
                renderizar_fase3_lancamento()

            elif nome_aba == "Clientes Beta":
                renderizar_clientes_beta()

            elif nome_aba == "Suporte Beta":
                renderizar_suporte_beta()

            elif nome_aba == "Retenção Beta":
                renderizar_retencao_beta()

            elif nome_aba == "Painel Fase 3":
                renderizar_painel_fase3()

            elif nome_aba == "Métricas Fase 3":
                renderizar_metricas_fase3()

            elif nome_aba == "Decisão Fase 3":
                renderizar_go_no_go_fase3()

            elif nome_aba == "Plano Fase 4":
                renderizar_plano_fase4()

            elif nome_aba == "Arquitetura Fase 4":
                renderizar_arquitetura_fase4()

            elif nome_aba == "Core Engine":
                renderizar_painel_core_engine()

            elif nome_aba == "Compatibilidade Core":
                renderizar_painel_compatibilidade_core()

            elif nome_aba == "Motor Adapter":
                renderizar_painel_motor_adapter()

            elif nome_aba == "Motor Controlado":
                renderizar_painel_motor_controlado()

            elif nome_aba == "Auditoria Motor Principal":
                renderizar_painel_auditoria_motor_principal()

            elif nome_aba == "Fallback Motor":
                renderizar_painel_fallback_motor()

            elif nome_aba == "Logs Motor":
                renderizar_painel_logs_motor()

            elif nome_aba == "Saúde Motor":
                renderizar_painel_saude_motor()

            elif nome_aba == "Decisão Core":
                renderizar_painel_decisao_core()

            elif nome_aba == "Promoção Core":
                renderizar_painel_promocao_core()

            elif nome_aba == "Estratégia Produto":
                renderizar_produto_estrategico()

            elif nome_aba == "Deploy Público":
                renderizar_deploy_publico()

            elif nome_aba == "Dados":
                renderizar_central_persistencia_dados()

            elif nome_aba == "Analytics Público":
                renderizar_painel_analytics_publico()

            elif nome_aba == "Painel Trilha":
                renderizar_painel_trilha_educativa_valoris()

            elif nome_aba == "Painel Copiloto":
                renderizar_painel_copiloto_valoris()

            elif nome_aba == "Painel Jornada":
                renderizar_painel_jornada_personalizada_valoris()

            elif nome_aba == "Painel Ativação":
                renderizar_painel_hub_ativacao_valoris()

            elif nome_aba == "Painel Conversão":
                renderizar_painel_conversao_fundador_valoris()

            elif nome_aba == "Growth":
                renderizar_laboratorio_growth_valoris()

            elif nome_aba == "Validação Manual":
                renderizar_validacao_manual_valoris()

            elif nome_aba == "Fundadores":
                renderizar_central_fundadores_valoris()

            elif nome_aba == "Maturidade":
                renderizar_maturidade_produto_valoris()

            elif nome_aba == "Arquitetura":
                renderizar_arquitetura_transicao_valoris()

            elif nome_aba == "Camada Dados":
                renderizar_camada_dados_valoris()

            elif nome_aba == "Gateway Dados":
                renderizar_gateway_dados_valoris()

            elif nome_aba == "SQLite Piloto":
                renderizar_piloto_sqlite_valoris()

            elif nome_aba == "Repositórios":
                renderizar_repositorios_valoris()

            elif nome_aba == "PostgreSQL":
                renderizar_postgres_supabase_valoris()

            elif nome_aba == "API":
                renderizar_api_contratos_valoris()

            elif nome_aba == "API Scaffold":
                renderizar_api_scaffold_valoris()

            elif nome_aba == "API Smoke":
                renderizar_api_smoke_tests_valoris()

            elif nome_aba == "API Bridge":
                renderizar_api_repository_bridge_valoris()

            elif nome_aba == "API Tests":
                renderizar_api_endpoint_tests_valoris()

            elif nome_aba == "API SQLite":
                renderizar_api_sqlite_bridge_valoris()

            elif nome_aba == "API Adapter":
                renderizar_api_storage_adapter_valoris()

            elif nome_aba == "API Security":
                renderizar_api_security_key_valoris()

            elif nome_aba == "API Security Panel":
                renderizar_api_security_panel_valoris()

            elif nome_aba == "API Database Cloud":
                renderizar_api_database_cloud_valoris()

            elif nome_aba == "API Database Contracts":
                renderizar_api_database_contracts_valoris()

            elif nome_aba == "API Database Providers":
                renderizar_api_database_providers_valoris()

            elif nome_aba == "API Provider Runtime":
                renderizar_api_provider_runtime_valoris()

            elif nome_aba == "API Provider Backend":
                renderizar_api_provider_backend_valoris()

            elif nome_aba == "Launch Readiness":
                renderizar_launch_readiness_valoris()

            elif nome_aba == "Análise Premium":
                renderizar_analise_premium_valoris()

            elif nome_aba == "Demo 2 Min":
                renderizar_demo_guiada_2min_valoris()

            elif nome_aba == "Beta Feedback":
                renderizar_beta_feedback_valoris()

            elif nome_aba == "Beta Insights":
                renderizar_beta_insights_valoris()

            elif nome_aba == "UX":
                renderizar_auditoria_ux()

            elif nome_aba == "Multiativos":
                renderizar_central_multiativos(
                    resultado_valuation=st.session_state["resultado_valuation"]
                )

            elif nome_aba == "Ações Brasil":
                renderizar_motor_acoes_brasil(
                    resultado_valuation=st.session_state["resultado_valuation"]
                )

            elif nome_aba == "FIIs":
                renderizar_motor_fiis(
                    resultado_valuation=st.session_state["resultado_valuation"]
                )

            elif nome_aba == "Renda Fixa":
                renderizar_motor_renda_fixa(
                    resultado_valuation=st.session_state["resultado_valuation"]
                )

            elif nome_aba == "Resumo da Decisão":
                render_resumo_decisao(
                    resultado_valuation=st.session_state["resultado_valuation"]
                )

                st.divider()

                st.markdown("### Relatório premium da decisão")

                st.caption(
                    "Este relatório também está disponível de forma centralizada na aba Relatórios."
                )

                resumo_decisao_atual = st.session_state.get("resultado_resumo_decisao")

                relatorio_markdown_com_decisao = gerar_relatorio_markdown(
                    entradas=entradas,
                    resultado=resultado,
                    dados_empresa=dados,
                    simbolo_moeda=simbolo_moeda,
                    formatar_moeda=formatar_moeda,
                    formatar_percentual=formatar_percentual,
                    formatar_numero=formatar_numero,
                )

                relatorio_markdown_com_decisao += gerar_bloco_markdown_decisao(
                    resumo_decisao=resumo_decisao_atual,
                    simbolo_moeda=simbolo_moeda,
                )

                nome_arquivo_relatorio_decisao = gerar_nome_arquivo_relatorio(
                    empresa=entradas.empresa,
                    ticker=entradas.ticker,
                ).replace(".md", "_decisao.md")

                st.download_button(
                    label="Baixar relatório premium com decisão (.md)",
                    data=relatorio_markdown_com_decisao,
                    file_name=nome_arquivo_relatorio_decisao,
                    mime="text/markdown",
                    key="download_relatorio_premium_decisao",
                )

            elif nome_aba == "Comparativo":
                st.markdown("### Central inteligente de comparação")

                st.caption(
                    "Compare empresas pelo mesmo critério de valuation e identifique quais estão mais próximas de uma zona racional de entrada."
                )

                melhor_empresa = encontrar_empresa_mais_atrativa(
                    EMPRESAS,
                    formatar_moeda,
                    formatar_percentual,
                )

                renderizar_radar_oportunidade(melhor_empresa)

                st.divider()

                ranking_empresas_reais = gerar_ranking_empresas_reais(
                    EMPRESAS,
                    formatar_moeda,
                    formatar_percentual,
                )

                renderizar_ranking_visual(ranking_empresas_reais)

                st.markdown("#### Ranking técnico")

                if len(ranking_empresas_reais) == 0:
                    st.warning("Nenhuma empresa real cadastrada para gerar ranking.")
                else:
                    st.dataframe(
                        preparar_tabela(ranking_empresas_reais),
                        use_container_width=True,
                        hide_index=True,
                    )

                st.divider()

                tabela_comparativo = gerar_comparativo(
                    EMPRESAS,
                    formatar_moeda,
                    formatar_percentual,
                )

                st.markdown("#### Filtros avançados")

                col_filtro_1, col_filtro_2 = st.columns(2)

                with col_filtro_1:
                    filtro_tipo = st.selectbox(
                        "Filtrar por tipo",
                        ["Todos", "Real", "Didática"],
                        index=1,
                    )

                with col_filtro_2:
                    filtro_status = st.selectbox(
                        "Filtrar por status",
                        ["Todos", "COMPRA", "NEUTRO", "AGUARDE"],
                    )

                tabela_filtrada = tabela_comparativo

                if filtro_tipo != "Todos":
                    tabela_filtrada = [
                        linha for linha in tabela_filtrada
                        if linha["Tipo"] == filtro_tipo
                    ]

                if filtro_status != "Todos":
                    tabela_filtrada = [
                        linha for linha in tabela_filtrada
                        if linha["Status"] == filtro_status
                    ]

                st.markdown("#### Base completa de comparação")

                if len(tabela_filtrada) == 0:
                    st.warning("Nenhuma empresa encontrada com os filtros selecionados.")
                else:
                    tabela_preparada = preparar_tabela(tabela_filtrada)

                    st.dataframe(
                        tabela_preparada,
                        use_container_width=True,
                        hide_index=True,
                    )

                    csv_comparativo = converter_tabela_para_csv(tabela_preparada)

                    st.download_button(
                        label="Baixar comparativo em CSV",
                        data=csv_comparativo,
                        file_name="comparativo_preco_teto.csv",
                        mime="text/csv",
                    )

            elif nome_aba == "Tese qualitativa":
                st.markdown("### Tese qualitativa da empresa")

                st.text_area(
                    "Tese da empresa",
                    value=dados["tese"],
                    height=130,
                    key=f"tese_{modelo_escolhido}",
                )

                st.text_area(
                    "Principais riscos",
                    value=dados["riscos"],
                    height=130,
                    key=f"riscos_{modelo_escolhido}",
                )

                st.text_area(
                    "Fundamentos observados",
                    value=dados["fundamentos"],
                    height=130,
                    key=f"fundamentos_{modelo_escolhido}",
                )

            elif nome_aba == "Premissas":
                st.markdown("### Premissas utilizadas")

                moeda_unidade = dados.get("moeda", "Não informado").replace("$", "\\$")

                st.info(
                    f"""
                    **Tipo de análise:** {tipo_analise}  
                    **Modo selecionado:** {modelo_escolhido}  
                    **Perfil da empresa:** {dados.get("perfil_empresa", "Não informado")}  
                    **Moeda/unidade:** {moeda_unidade}  
                    **Data de referência:** {dados.get("data_referencia", "Não informado")}  
                    **Fonte das premissas:** {dados.get("fonte_premissas", "Não informado")}
                    """
                )

                if modo_demonstracao:
                    st.warning(
                        "Esta é uma demonstração com dados fictícios. Não use como análise real."
                    )

                if nova_analise_manual:
                    st.warning(
                        "Esta é uma análise manual. O app não verificou automaticamente os dados inseridos. "
                        "A qualidade do resultado depende totalmente da qualidade das premissas."
                    )

                tabela_premissas = [
                    {
                        "Premissa": "Lucro líquido sustentável",
                        "Valor": formatar_moeda(lucro_liquido_sustentavel, simbolo_moeda),
                    },
                    {
                        "Premissa": "Fluxo de caixa livre",
                        "Valor": formatar_moeda(fluxo_caixa_livre, simbolo_moeda),
                    },
                    {
                        "Premissa": "Quantidade de ações",
                        "Valor": formatar_numero(quantidade_acoes),
                    },
                    {
                        "Premissa": "Preço atual",
                        "Valor": formatar_moeda(preco_atual, simbolo_moeda),
                    },
                    {
                        "Premissa": "Múltiplo justo EPS",
                        "Valor": multiplo_justo_eps,
                    },
                    {
                        "Premissa": "Múltiplo justo FCF",
                        "Valor": multiplo_justo_fcf,
                    },
                    {
                        "Premissa": "Peso EPS",
                        "Valor": f"{peso_eps}%",
                    },
                    {
                        "Premissa": "Peso FCF",
                        "Valor": f"{peso_fcf}%",
                    },
                    {
                        "Premissa": "Margem de segurança",
                        "Valor": f"{margem_seguranca}%",
                    },
                    {
                        "Premissa": "Motor preferido",
                        "Valor": motor_valuation,
                    },
                    {
                        "Premissa": "Motor executado",
                        "Valor": motor_executado,
                    },
                    {
                        "Premissa": "Fallback ocorreu",
                        "Valor": "Sim" if resultado.get("fallback_ocorreu") else "Não",
                    },
                    {
                        "Premissa": "Log técnico registrado",
                        "Valor": "Sim" if resultado.get("log_motor_registrado") else "Não",
                    },
                    {
                        "Premissa": "ID do log",
                        "Valor": resultado.get("id_log_motor", "N/D"),
                    },
                ]

                st.table(preparar_tabela(tabela_premissas))

            elif nome_aba == "Histórico":
                st.markdown("### Histórico de análises salvas")

                historico = carregar_historico()

                if len(historico) == 0:
                    st.info("Nenhuma análise foi salva ainda.")
                else:
                    historico_mais_recente_primeiro = list(reversed(historico))
                    st.table(preparar_tabela(historico_mais_recente_primeiro))

                    with open(CAMINHO_HISTORICO, "rb") as arquivo:
                        st.download_button(
                            label="Baixar histórico em CSV",
                            data=arquivo,
                            file_name="historico_analises.csv",
                            mime="text/csv",
                        )

            elif nome_aba == "Educação":
                renderizar_aba_educacional()

except ValueError as erro:
    st.error(str(erro))
except RuntimeError as erro:
    st.error(str(erro))