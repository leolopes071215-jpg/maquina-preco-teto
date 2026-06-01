# watchlist.py

import csv
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v1.21 — Watchlist Inteligente Multiativos
# ------------------------------------------------------------
# Este módulo cria uma lista de acompanhamento para:
# Ações EUA, Ações Brasil, FIIs e Renda Fixa.
# O objetivo é transformar análises em rotina de acompanhamento.
# Não é recomendação de investimento.
# ============================================================


CAMINHO_WATCHLIST = Path("watchlist_multiativos.csv")


CAMPOS_WATCHLIST = [
    "id",
    "data_criacao",
    "classe_ativo",
    "ticker",
    "nome_ativo",
    "preco_atual",
    "preco_referencia",
    "status",
    "prioridade",
    "proxima_acao",
    "tese_curta",
]


CLASSES_ATIVOS = [
    "Ações EUA",
    "Ações Brasil",
    "FIIs",
    "Renda Fixa",
]


STATUS_WATCHLIST = [
    "Estudar com prioridade",
    "Aguardar preço melhor",
    "Monitorar",
    "Revisar premissas",
    "Evitar por enquanto",
]


PRIORIDADES = [
    "Alta",
    "Média",
    "Baixa",
]


def _safe_float(valor: Any, default: Optional[float] = None) -> Optional[float]:
    if valor is None or valor == "":
        return default

    if isinstance(valor, (int, float)):
        return float(valor)

    if isinstance(valor, str):
        texto = (
            valor.replace("R$", "")
            .replace("US$", "")
            .replace("$", "")
            .replace("%", "")
            .replace(".", "")
            .replace(",", ".")
            .strip()
        )

        try:
            return float(texto)
        except ValueError:
            return default

    return default


def _fmt_moeda(valor: Any, simbolo: str = "R$") -> str:
    numero = _safe_float(valor)

    if numero is None:
        return "N/D"

    return f"{simbolo} {numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_data(data: str) -> str:
    if not data:
        return "N/D"

    try:
        data_obj = datetime.fromisoformat(data)
        return data_obj.strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return data


def _normalizar_status(status: Any) -> str:
    if status is None:
        return "Monitorar"

    texto = str(status).upper().strip()

    if "COMPRA" in texto:
        return "Estudar com prioridade"

    if "NEUTRO" in texto:
        return "Monitorar"

    if "AGUARDE" in texto:
        return "Aguardar preço melhor"

    if "REVISAR" in texto:
        return "Revisar premissas"

    return str(status)


def _garantir_arquivo_watchlist() -> None:
    if CAMINHO_WATCHLIST.exists():
        return

    with open(CAMINHO_WATCHLIST, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_WATCHLIST)
        escritor.writeheader()


def carregar_watchlist() -> List[Dict[str, str]]:
    _garantir_arquivo_watchlist()

    with open(CAMINHO_WATCHLIST, "r", newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)

        registros = []

        for linha in leitor:
            registro = {campo: linha.get(campo, "") for campo in CAMPOS_WATCHLIST}
            registros.append(registro)

        return registros


def salvar_watchlist(registros: List[Dict[str, Any]]) -> None:
    with open(CAMINHO_WATCHLIST, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_WATCHLIST)
        escritor.writeheader()

        for registro in registros:
            linha = {campo: registro.get(campo, "") for campo in CAMPOS_WATCHLIST}
            escritor.writerow(linha)


def adicionar_ativo_watchlist(
    classe_ativo: str,
    ticker: str,
    nome_ativo: str,
    preco_atual: float,
    preco_referencia: float,
    status: str,
    prioridade: str,
    proxima_acao: str,
    tese_curta: str,
) -> None:
    registros = carregar_watchlist()

    novo_registro = {
        "id": str(uuid.uuid4())[:8],
        "data_criacao": datetime.now().isoformat(timespec="minutes"),
        "classe_ativo": classe_ativo,
        "ticker": ticker.upper().strip(),
        "nome_ativo": nome_ativo.strip(),
        "preco_atual": preco_atual,
        "preco_referencia": preco_referencia,
        "status": status,
        "prioridade": prioridade,
        "proxima_acao": proxima_acao.strip(),
        "tese_curta": tese_curta.strip(),
    }

    registros.append(novo_registro)
    salvar_watchlist(registros)


def remover_ativo_watchlist(id_ativo: str) -> None:
    registros = carregar_watchlist()

    registros_filtrados = [
        registro for registro in registros
        if registro.get("id") != id_ativo
    ]

    salvar_watchlist(registros_filtrados)


def limpar_watchlist() -> None:
    salvar_watchlist([])


def _extrair_contexto_valuation(
    resultado_valuation: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    dados = {}

    if isinstance(st.session_state.get("resultado_valuation"), dict):
        dados.update(st.session_state["resultado_valuation"])

    if isinstance(resultado_valuation, dict):
        dados.update(resultado_valuation)

    return {
        "empresa": dados.get("empresa", "Ativo analisado"),
        "ticker": dados.get("ticker", "N/D"),
        "status": _normalizar_status(dados.get("status_valuation", dados.get("status", "Monitorar"))),
        "preco_atual": _safe_float(dados.get("preco_atual"), 0.0) or 0.0,
        "preco_referencia": _safe_float(
            dados.get("preco_teto", dados.get("preco_justo", dados.get("preco_justo_combinado"))),
            0.0,
        ) or 0.0,
    }


def _gerar_leitura_preco(preco_atual: Any, preco_referencia: Any) -> str:
    atual = _safe_float(preco_atual)
    referencia = _safe_float(preco_referencia)

    if atual is None or referencia is None or atual <= 0 or referencia <= 0:
        return "Sem leitura automática"

    if atual <= referencia:
        return "Dentro da zona de referência"

    distancia = ((atual - referencia) / referencia) * 100

    if distancia <= 10:
        return "Próximo da zona de referência"

    if distancia <= 25:
        return "Acima da referência"

    return "Muito acima da referência"


def _preparar_tabela_visual(registros: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    tabela = []

    for registro in registros:
        leitura_preco = _gerar_leitura_preco(
            registro.get("preco_atual"),
            registro.get("preco_referencia"),
        )

        tabela.append(
            {
                "ID": registro.get("id", ""),
                "Data": _fmt_data(registro.get("data_criacao", "")),
                "Classe": registro.get("classe_ativo", ""),
                "Ticker": registro.get("ticker", ""),
                "Ativo": registro.get("nome_ativo", ""),
                "Preço atual": _fmt_moeda(registro.get("preco_atual")),
                "Referência": _fmt_moeda(registro.get("preco_referencia")),
                "Leitura de preço": leitura_preco,
                "Status": registro.get("status", ""),
                "Prioridade": registro.get("prioridade", ""),
                "Próxima ação": registro.get("proxima_acao", ""),
                "Tese curta": registro.get("tese_curta", ""),
            }
        )

    return tabela


def _contar_por_campo(registros: List[Dict[str, Any]], campo: str, valor: str) -> int:
    return len([
        registro for registro in registros
        if registro.get(campo) == valor
    ])


def _gerar_resumo_watchlist(registros: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(registros)

    resumo = {
        "total": total,
        "acoes_eua": _contar_por_campo(registros, "classe_ativo", "Ações EUA"),
        "acoes_brasil": _contar_por_campo(registros, "classe_ativo", "Ações Brasil"),
        "fiis": _contar_por_campo(registros, "classe_ativo", "FIIs"),
        "renda_fixa": _contar_por_campo(registros, "classe_ativo", "Renda Fixa"),
        "alta_prioridade": _contar_por_campo(registros, "prioridade", "Alta"),
        "estudar_prioridade": _contar_por_campo(registros, "status", "Estudar com prioridade"),
        "aguardar_preco": _contar_por_campo(registros, "status", "Aguardar preço melhor"),
    }

    return resumo


def _injetar_css_watchlist() -> None:
    st.markdown(
        """
        <style>
            .watch-hero {
                padding: 1.5rem 1.55rem;
                border-radius: 24px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    radial-gradient(circle at top left, rgba(214, 181, 109, 0.18), transparent 30%),
                    radial-gradient(circle at bottom right, rgba(74, 144, 226, 0.18), transparent 34%),
                    linear-gradient(135deg, rgba(8, 15, 27, 0.98), rgba(5, 9, 18, 0.98));
                box-shadow: 0 18px 55px rgba(0, 0, 0, 0.32);
                margin-bottom: 1.25rem;
            }

            .watch-eyebrow {
                color: #d6b56d;
                font-size: 0.78rem;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .watch-title {
                color: #f4f7fb;
                font-size: 1.85rem;
                font-weight: 850;
                margin-bottom: 0.45rem;
            }

            .watch-subtitle {
                color: rgba(244, 247, 251, 0.74);
                font-size: 0.98rem;
                line-height: 1.58;
                max-width: 980px;
            }

            .watch-card {
                padding: 1.05rem 1.1rem;
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.035);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.18);
                height: 100%;
            }

            .watch-card-label {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .watch-card-value {
                color: #f4f7fb;
                font-size: 1.25rem;
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .watch-card-note {
                color: rgba(244, 247, 251, 0.66);
                font-size: 0.86rem;
                line-height: 1.45;
            }

            .watch-disclaimer {
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
        <div class="watch-card">
            <div class="watch-card-label">{label}</div>
            <div class="watch-card-value">{value}</div>
            <div class="watch-card-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def renderizar_watchlist_multiativos(
    resultado_valuation: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Renderiza a Watchlist Inteligente Multiativos.
    """
    _injetar_css_watchlist()

    contexto = _extrair_contexto_valuation(resultado_valuation)

    st.markdown(
        """
        <div class="watch-hero">
            <div class="watch-eyebrow">Rotina de acompanhamento</div>
            <div class="watch-title">Watchlist Inteligente Multiativos</div>
            <div class="watch-subtitle">
                Salve ativos em estudo, registre preço de referência, prioridade, status, tese curta e próxima ação.
                O objetivo é transformar análise pontual em acompanhamento disciplinado.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    registros = carregar_watchlist()
    resumo = _gerar_resumo_watchlist(registros)

    st.session_state["resultado_watchlist"] = resumo

    st.markdown("### Resumo da watchlist")

    col_res_1, col_res_2, col_res_3, col_res_4 = st.columns(4)

    with col_res_1:
        st.metric("Ativos salvos", resumo["total"])

    with col_res_2:
        st.metric("Alta prioridade", resumo["alta_prioridade"])

    with col_res_3:
        st.metric("Estudar com prioridade", resumo["estudar_prioridade"])

    with col_res_4:
        st.metric("Aguardar preço", resumo["aguardar_preco"])

    col_cls_1, col_cls_2, col_cls_3, col_cls_4 = st.columns(4)

    with col_cls_1:
        _card("Ações EUA", str(resumo["acoes_eua"]), "Ativos americanos acompanhados.")

    with col_cls_2:
        _card("Ações Brasil", str(resumo["acoes_brasil"]), "Empresas brasileiras em estudo.")

    with col_cls_3:
        _card("FIIs", str(resumo["fiis"]), "Fundos imobiliários acompanhados.")

    with col_cls_4:
        _card("Renda Fixa", str(resumo["renda_fixa"]), "Títulos e produtos de renda fixa.")

    st.divider()

    st.markdown("### Adicionar ativo à watchlist")

    with st.expander("Adicionar novo ativo", expanded=True):
        col_import_1, col_import_2, col_import_3 = st.columns(3)

        with col_import_1:
            st.metric("Ativo atual", contexto["empresa"])

        with col_import_2:
            st.metric("Ticker atual", contexto["ticker"])

        with col_import_3:
            st.metric("Status sugerido", contexto["status"])

        usar_analise_atual = st.checkbox(
            "Usar dados da análise atual como base",
            value=True,
            help="Preenche nome, ticker, preço atual, preço de referência e status com base na análise atual.",
            key="watch_usar_analise_atual",
        )

        if usar_analise_atual:
            nome_padrao = contexto["empresa"]
            ticker_padrao = contexto["ticker"]
            preco_atual_padrao = float(contexto["preco_atual"])
            preco_referencia_padrao = float(contexto["preco_referencia"])
            status_padrao = contexto["status"]
        else:
            nome_padrao = ""
            ticker_padrao = ""
            preco_atual_padrao = 0.0
            preco_referencia_padrao = 0.0
            status_padrao = "Monitorar"

        with st.form("form_adicionar_watchlist"):
            col1, col2 = st.columns(2)

            with col1:
                classe_ativo = st.selectbox(
                    "Classe do ativo",
                    CLASSES_ATIVOS,
                    index=0,
                    key="watch_classe_ativo",
                )

                ticker = st.text_input(
                    "Ticker / Código",
                    value=ticker_padrao,
                    key="watch_ticker",
                )

                nome_ativo = st.text_input(
                    "Nome do ativo",
                    value=nome_padrao,
                    key="watch_nome_ativo",
                )

                preco_atual = st.number_input(
                    "Preço atual / taxa atual",
                    min_value=0.0,
                    value=preco_atual_padrao,
                    step=0.01,
                    key="watch_preco_atual",
                )

                preco_referencia = st.number_input(
                    "Preço-teto / referência",
                    min_value=0.0,
                    value=preco_referencia_padrao,
                    step=0.01,
                    key="watch_preco_referencia",
                )

            with col2:
                status_index = STATUS_WATCHLIST.index(status_padrao) if status_padrao in STATUS_WATCHLIST else 2

                status = st.selectbox(
                    "Status de acompanhamento",
                    STATUS_WATCHLIST,
                    index=status_index,
                    key="watch_status",
                )

                prioridade = st.selectbox(
                    "Prioridade",
                    PRIORIDADES,
                    index=1,
                    key="watch_prioridade",
                )

                proxima_acao = st.text_area(
                    "Próxima ação",
                    value="Revisar premissas, acompanhar preço e comparar com alternativas.",
                    height=90,
                    key="watch_proxima_acao",
                )

                tese_curta = st.text_area(
                    "Tese curta",
                    value="Ativo em estudo. Acompanhar qualidade, preço, riscos e evolução dos fundamentos.",
                    height=90,
                    key="watch_tese_curta",
                )

            enviar = st.form_submit_button("Adicionar à watchlist")

            if enviar:
                if ticker.strip() == "" or nome_ativo.strip() == "":
                    st.error("Preencha pelo menos o ticker/código e o nome do ativo.")
                else:
                    adicionar_ativo_watchlist(
                        classe_ativo=classe_ativo,
                        ticker=ticker,
                        nome_ativo=nome_ativo,
                        preco_atual=preco_atual,
                        preco_referencia=preco_referencia,
                        status=status,
                        prioridade=prioridade,
                        proxima_acao=proxima_acao,
                        tese_curta=tese_curta,
                    )

                    st.success("Ativo adicionado à watchlist com sucesso.")
                    st.rerun()

    st.divider()

    st.markdown("### Ativos acompanhados")

    registros = carregar_watchlist()

    if len(registros) == 0:
        st.info("Nenhum ativo salvo na watchlist ainda.")
    else:
        col_filtro_1, col_filtro_2, col_filtro_3 = st.columns(3)

        with col_filtro_1:
            filtro_classe = st.selectbox(
                "Filtrar por classe",
                ["Todos"] + CLASSES_ATIVOS,
                key="watch_filtro_classe",
            )

        with col_filtro_2:
            filtro_status = st.selectbox(
                "Filtrar por status",
                ["Todos"] + STATUS_WATCHLIST,
                key="watch_filtro_status",
            )

        with col_filtro_3:
            filtro_prioridade = st.selectbox(
                "Filtrar por prioridade",
                ["Todos"] + PRIORIDADES,
                key="watch_filtro_prioridade",
            )

        registros_filtrados = registros

        if filtro_classe != "Todos":
            registros_filtrados = [
                registro for registro in registros_filtrados
                if registro.get("classe_ativo") == filtro_classe
            ]

        if filtro_status != "Todos":
            registros_filtrados = [
                registro for registro in registros_filtrados
                if registro.get("status") == filtro_status
            ]

        if filtro_prioridade != "Todos":
            registros_filtrados = [
                registro for registro in registros_filtrados
                if registro.get("prioridade") == filtro_prioridade
            ]

        tabela = _preparar_tabela_visual(registros_filtrados)

        if len(tabela) == 0:
            st.warning("Nenhum ativo encontrado com os filtros selecionados.")
        else:
            st.dataframe(
                tabela,
                use_container_width=True,
                hide_index=True,
            )

        st.divider()

        st.markdown("### Gerenciar watchlist")

        col_manage_1, col_manage_2 = st.columns(2)

        with col_manage_1:
            opcoes_remover = [
                f"{registro.get('id')} — {registro.get('ticker')} — {registro.get('nome_ativo')}"
                for registro in registros
            ]

            opcao_remover = st.selectbox(
                "Selecionar ativo para remover",
                opcoes_remover,
                key="watch_remover_select",
            )

            if st.button("Remover ativo selecionado", key="watch_remover_botao"):
                id_remover = opcao_remover.split(" — ")[0]
                remover_ativo_watchlist(id_remover)
                st.success("Ativo removido da watchlist.")
                st.rerun()

        with col_manage_2:
            with open(CAMINHO_WATCHLIST, "rb") as arquivo:
                st.download_button(
                    label="Baixar watchlist em CSV",
                    data=arquivo,
                    file_name="watchlist_multiativos.csv",
                    mime="text/csv",
                    key="watch_download_csv",
                )

            confirmar_limpeza = st.checkbox(
                "Confirmar limpeza total da watchlist",
                value=False,
                key="watch_confirmar_limpeza",
            )

            if st.button("Limpar watchlist", key="watch_limpar_botao"):
                if confirmar_limpeza:
                    limpar_watchlist()
                    st.success("Watchlist limpa com sucesso.")
                    st.rerun()
                else:
                    st.warning("Marque a confirmação antes de limpar toda a watchlist.")

    st.divider()

    st.markdown("### Como usar esta watchlist")

    st.markdown(
        """
        Use a watchlist como uma mesa de acompanhamento.

        - **Estudar com prioridade:** ativos que parecem mais promissores e merecem análise profunda.
        - **Aguardar preço melhor:** ativos bons, mas ainda sem margem de segurança suficiente.
        - **Monitorar:** ativos interessantes, mas ainda sem tese forte.
        - **Revisar premissas:** análises que dependem de dados frágeis ou otimistas.
        - **Evitar por enquanto:** ativos com risco elevado ou baixa qualidade da tese.

        A lógica da plataforma é transformar cada análise em uma próxima ação clara.
        """
    )

    st.markdown(
        """
        <div class="watch-disclaimer">
            <strong>Aviso educacional:</strong> a watchlist não representa recomendação de compra, venda ou manutenção.
            Ela é uma ferramenta de organização para acompanhar estudos, premissas, riscos e prioridades.
            Toda decisão real deve considerar objetivos pessoais, diversificação, liquidez, tributação,
            horizonte de tempo e responsabilidade individual.
        </div>
        """,
        unsafe_allow_html=True,
    )