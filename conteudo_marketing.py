# conteudo_marketing.py

import csv
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v1.31 — Central de Conteúdo e Calendário Editorial
# ------------------------------------------------------------
# Esta tela transforma a estratégia de marketing em produção:
# - ideias de conteúdo
# - roteiros curtos
# - carrosséis
# - CTAs
# - calendário editorial
# - status de produção
#
# Objetivo:
# ajudar a gerar demanda real para o beta/lista de espera.
# ============================================================


CAMINHO_CALENDARIO = Path("calendario_conteudo.csv")


CAMPOS_CALENDARIO = [
    "id",
    "data_criacao",
    "data_postagem",
    "canal",
    "formato",
    "tema",
    "gancho",
    "roteiro",
    "cta",
    "status",
    "observacoes",
]


CANAIS = [
    "TikTok",
    "Instagram Reels",
    "Instagram Carrossel",
    "Stories",
    "YouTube Shorts",
    "LinkedIn",
    "WhatsApp",
]


FORMATOS = [
    "Reels curto",
    "Carrossel",
    "Story",
    "Post texto",
    "Demonstração de tela",
    "Estudo de caso",
    "Thread curta",
]


STATUS_CONTEUDO = [
    "Ideia",
    "Roteiro pronto",
    "Gravado",
    "Editado",
    "Postado",
    "Reaproveitar",
]


TEMAS_BASE = [
    "Preço-teto",
    "Margem de segurança",
    "Erro de pagar caro",
    "Tese de investimento",
    "Checklist antes de comprar",
    "Relatório de análise",
    "Watchlist",
    "FIIs",
    "Renda Fixa",
    "Ações Brasil",
    "Disciplina do investidor",
    "Produto em construção",
]


def _safe_get_dict(key: str) -> Dict[str, Any]:
    valor = st.session_state.get(key)

    if isinstance(valor, dict):
        return valor

    return {}


def _fmt_texto(valor: Any, padrao: str = "N/D") -> str:
    if valor is None or valor == "":
        return padrao

    return str(valor)


def _garantir_arquivo_calendario() -> None:
    if CAMINHO_CALENDARIO.exists():
        return

    with open(CAMINHO_CALENDARIO, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_CALENDARIO)
        escritor.writeheader()


def carregar_conteudos() -> List[Dict[str, str]]:
    _garantir_arquivo_calendario()

    with open(CAMINHO_CALENDARIO, "r", newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        conteudos = []

        for linha in leitor:
            conteudo = {campo: linha.get(campo, "") for campo in CAMPOS_CALENDARIO}
            conteudos.append(conteudo)

        return conteudos


def salvar_conteudos(conteudos: List[Dict[str, Any]]) -> None:
    with open(CAMINHO_CALENDARIO, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_CALENDARIO)
        escritor.writeheader()

        for conteudo in conteudos:
            linha = {campo: conteudo.get(campo, "") for campo in CAMPOS_CALENDARIO}
            escritor.writerow(linha)


def adicionar_conteudo(
    data_postagem: str,
    canal: str,
    formato: str,
    tema: str,
    gancho: str,
    roteiro: str,
    cta: str,
    status: str,
    observacoes: str,
) -> None:
    conteudos = carregar_conteudos()

    novo_conteudo = {
        "id": str(uuid.uuid4())[:8],
        "data_criacao": datetime.now().isoformat(timespec="minutes"),
        "data_postagem": data_postagem,
        "canal": canal,
        "formato": formato,
        "tema": tema.strip(),
        "gancho": gancho.strip(),
        "roteiro": roteiro.strip(),
        "cta": cta.strip(),
        "status": status,
        "observacoes": observacoes.strip(),
    }

    conteudos.append(novo_conteudo)
    salvar_conteudos(conteudos)


def limpar_calendario() -> None:
    salvar_conteudos([])


def _contar(conteudos: List[Dict[str, str]], campo: str, valor: str) -> int:
    return len([
        conteudo for conteudo in conteudos
        if conteudo.get(campo) == valor
    ])


def _mais_frequente(conteudos: List[Dict[str, str]], campo: str) -> str:
    if len(conteudos) == 0:
        return "N/D"

    contagem = {}

    for conteudo in conteudos:
        valor = conteudo.get(campo, "")

        if valor == "":
            continue

        contagem[valor] = contagem.get(valor, 0) + 1

    if len(contagem) == 0:
        return "N/D"

    return max(contagem, key=contagem.get)


def _extrair_contexto() -> Dict[str, Any]:
    marketing = _safe_get_dict("resultado_marketing")
    negocio = _safe_get_dict("resultado_dashboard_negocio")

    return {
        "perfil_dominante": marketing.get(
            "perfil_dominante",
            negocio.get("perfil_lista_mais_comum", "Investidor iniciante/intermediário"),
        ),
        "dor_dominante": marketing.get(
            "dor_dominante",
            negocio.get("dor_mais_comum", "Medo de pagar caro em ações"),
        ),
        "modulo_campeao": marketing.get(
            "modulo_campeao",
            negocio.get("modulo_mais_util", "Valuation"),
        ),
        "preco_citado": marketing.get(
            "preco_citado",
            negocio.get("preco_lista_mais_citado", "N/D"),
        ),
        "score_tracao": marketing.get(
            "score_tracao",
            negocio.get("score_tracao", 0),
        ),
    }


def _gerar_ideias_estrategicas(contexto: Dict[str, Any]) -> List[Dict[str, str]]:
    dor = _fmt_texto(contexto.get("dor_dominante"))
    modulo = _fmt_texto(contexto.get("modulo_campeao"))

    ideias = [
        {
            "Tema": "Preço-teto",
            "Gancho": "Empresa boa pode ser péssimo investimento se você pagar caro.",
            "Formato": "Reels curto",
            "Roteiro": "Mostre que qualidade não basta. Explique que preço, margem de segurança e tese precisam andar juntos.",
            "CTA": "Entre na lista de espera da Máquina de Preço-Teto.",
        },
        {
            "Tema": "Margem de segurança",
            "Gancho": "O investidor inteligente não precisa acertar tudo. Ele precisa de margem de erro.",
            "Formato": "Carrossel",
            "Roteiro": "Explique o conceito em 5 slides: erro comum, margem, exemplo simples, risco e aplicação no app.",
            "CTA": "Salve este post e teste o beta.",
        },
        {
            "Tema": "Checklist",
            "Gancho": "Antes de comprar uma ação, responda estas 7 perguntas.",
            "Formato": "Carrossel",
            "Roteiro": "Liste perguntas sobre lucro, caixa, dívida, tese, risco, preço e horizonte de tempo.",
            "CTA": "Use o checklist dentro da plataforma.",
        },
        {
            "Tema": "Relatórios",
            "Gancho": "Se você não registra sua análise, você não sabe se está evoluindo.",
            "Formato": "Demonstração de tela",
            "Roteiro": "Mostre a aba Relatórios e explique como ela transforma premissas em documento.",
            "CTA": "Entre no beta fechado.",
        },
        {
            "Tema": "Watchlist",
            "Gancho": "Oportunidade sem acompanhamento vira esquecimento.",
            "Formato": "Reels curto",
            "Roteiro": "Mostre como salvar ativo, status, prioridade e próxima ação.",
            "CTA": "Entre na lista de espera.",
        },
        {
            "Tema": "FIIs",
            "Gancho": "Dividend yield alto pode ser renda ou armadilha.",
            "Formato": "Reels curto",
            "Roteiro": "Explique que yield precisa ser analisado junto com qualidade, vacância, risco e sustentabilidade.",
            "CTA": "Analise FIIs com método.",
        },
        {
            "Tema": "Renda Fixa",
            "Gancho": "Nem todo investimento seguro é automaticamente bom.",
            "Formato": "Post texto",
            "Roteiro": "Explique liquidez, prazo, rentabilidade real, imposto e comparação com outras alternativas.",
            "CTA": "Use o módulo de renda fixa.",
        },
        {
            "Tema": "Construção pública",
            "Gancho": "Estou criando uma plataforma para investidores analisarem ativos com mais método.",
            "Formato": "Story/Reels",
            "Roteiro": "Mostre o app, explique a dor e convide pessoas para testar.",
            "CTA": "Me chama para entrar no beta.",
        },
    ]

    if dor != "N/D":
        ideias.insert(
            0,
            {
                "Tema": "Dor dominante",
                "Gancho": f"Você também sente isso: {dor}?",
                "Formato": "Post de validação",
                "Roteiro": "Abra com a dor, explique por que isso atrapalha o investidor e apresente o app como solução educacional em construção.",
                "CTA": "Entre na lista de espera e ajude a validar o produto.",
            },
        )

    if modulo != "N/D":
        ideias.insert(
            1,
            {
                "Tema": f"Módulo destaque: {modulo}",
                "Gancho": f"O módulo mais valorizado até agora foi: {modulo}.",
                "Formato": "Demonstração prática",
                "Roteiro": "Mostre a tela, explique o benefício e conecte com a dor do investidor.",
                "CTA": "Teste o beta e diga o que achou.",
            },
        )

    return ideias


def _gerar_roteiro_reels(tema: str, gancho: str, cta: str) -> str:
    return f"""Cena 1 — Gancho:
{gancho}

Cena 2 — Problema:
Muitos investidores compram ativos sem saber se o preço faz sentido, sem registrar premissas e sem revisar a tese.

Cena 3 — Virada:
O problema não é só escolher uma boa empresa. É entender se o preço compensa os riscos.

Cena 4 — Solução:
A Máquina de Preço-Teto organiza valuation, margem de segurança, tese, checklist, relatório e watchlist em uma jornada educacional.

Cena 5 — Fechamento:
Investir melhor começa antes da compra: começa no método.

CTA:
{cta}"""


def _gerar_estrutura_carrossel(tema: str, gancho: str, cta: str) -> str:
    return f"""Slide 1 — Capa:
{gancho}

Slide 2 — O erro:
Muita gente compra ativos por narrativa, notícia, dividendo ou empolgação.

Slide 3 — O princípio:
Preço importa. Tese importa. Risco importa. Margem de segurança importa.

Slide 4 — O método:
Antes de decidir, organize premissas, valuation, tese, riscos e cenário.

Slide 5 — Aplicação:
Use preço-teto como ferramenta de disciplina, não como previsão mágica.

Slide 6 — Checklist:
Pergunte: o lucro é sustentável? O caixa confirma? A dívida é controlada? A tese é clara?

Slide 7 — Registro:
Se a análise não fica registrada, fica difícil aprender com os próprios erros.

Slide 8 — CTA:
{cta}"""


def _preparar_tabela(conteudos: List[Dict[str, str]]) -> List[Dict[str, str]]:
    tabela = []

    for conteudo in reversed(conteudos):
        tabela.append(
            {
                "Postagem": conteudo.get("data_postagem", ""),
                "Canal": conteudo.get("canal", ""),
                "Formato": conteudo.get("formato", ""),
                "Tema": conteudo.get("tema", ""),
                "Gancho": conteudo.get("gancho", ""),
                "Status": conteudo.get("status", ""),
                "CTA": conteudo.get("cta", ""),
                "Observações": conteudo.get("observacoes", ""),
            }
        )

    return tabela


def _injetar_css_conteudo() -> None:
    st.markdown(
        """
        <style>
            .cont-hero {
                padding: 1.7rem 1.75rem;
                border-radius: 30px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    radial-gradient(circle at top left, rgba(214, 181, 109, 0.25), transparent 30%),
                    radial-gradient(circle at bottom right, rgba(74, 144, 226, 0.22), transparent 34%),
                    linear-gradient(135deg, rgba(8, 15, 27, 0.99), rgba(5, 9, 18, 0.99));
                box-shadow: 0 18px 55px rgba(0, 0, 0, 0.34);
                margin-bottom: 1.25rem;
            }

            .cont-eyebrow {
                color: #d6b56d;
                font-size: 0.78rem;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.35rem;
            }

            .cont-title {
                color: #f4f7fb;
                font-size: 2.08rem;
                font-weight: 900;
                margin-bottom: 0.45rem;
                line-height: 1.14;
            }

            .cont-subtitle {
                color: rgba(244, 247, 251, 0.76);
                font-size: 1rem;
                line-height: 1.62;
                max-width: 1080px;
            }

            .cont-card {
                padding: 1.1rem 1.15rem;
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.035);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.18);
                height: 100%;
            }

            .cont-card-label {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .cont-card-value {
                color: #f4f7fb;
                font-size: 1.22rem;
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .cont-card-note {
                color: rgba(244, 247, 251, 0.68);
                font-size: 0.87rem;
                line-height: 1.47;
            }

            .cont-highlight {
                padding: 0.95rem 1rem;
                border-radius: 16px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.92rem;
                line-height: 1.55;
                margin-bottom: 0.7rem;
            }

            .cont-copy {
                padding: 1rem 1.05rem;
                border-radius: 18px;
                background: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(255, 255, 255, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.92rem;
                line-height: 1.58;
                white-space: pre-wrap;
                margin-bottom: 0.85rem;
            }

            .cont-disclaimer {
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
        <div class="cont-card">
            <div class="cont-card-label">{label}</div>
            <div class="cont-card-value">{value}</div>
            <div class="cont-card-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _copy_box(texto: str) -> None:
    st.markdown(
        f"""
        <div class="cont-copy">{texto}</div>
        """,
        unsafe_allow_html=True,
    )


def renderizar_central_conteudo() -> None:
    """
    Renderiza a Central de Conteúdo e Calendário Editorial.
    """
    _injetar_css_conteudo()

    contexto = _extrair_contexto()
    conteudos = carregar_conteudos()
    ideias = _gerar_ideias_estrategicas(contexto)

    total = len(conteudos)
    postados = _contar(conteudos, "status", "Postado")
    roteiros_prontos = _contar(conteudos, "status", "Roteiro pronto")
    canal_mais_usado = _mais_frequente(conteudos, "canal")
    tema_mais_usado = _mais_frequente(conteudos, "tema")

    st.session_state["resultado_conteudo_marketing"] = {
        "total_conteudos": total,
        "postados": postados,
        "roteiros_prontos": roteiros_prontos,
        "canal_mais_usado": canal_mais_usado,
        "tema_mais_usado": tema_mais_usado,
        "dor_dominante": contexto["dor_dominante"],
        "modulo_campeao": contexto["modulo_campeao"],
    }

    st.markdown(
        """
        <div class="cont-hero">
            <div class="cont-eyebrow">Aquisição na prática</div>
            <div class="cont-title">Central de Conteúdo e Calendário Editorial</div>
            <div class="cont-subtitle">
                Transforme a estratégia de marketing em posts, vídeos, carrosséis e demonstrações.
                O objetivo é produzir conteúdo com consistência para atrair usuários beta,
                gerar lista de espera e validar demanda real.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="cont-highlight">
            Conteúdo bom para esse produto não vende promessa fácil. Ele educa o investidor:
            preço importa, tese importa, risco importa e decisão sem método custa caro.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Diagnóstico editorial")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        _card("Conteúdos registrados", str(total), "Total no calendário editorial.")

    with col_2:
        _card("Postados", str(postados), "Conteúdos já publicados.")

    with col_3:
        _card("Canal mais usado", canal_mais_usado, "Onde você mais está produzindo.")

    with col_4:
        _card("Tema mais usado", tema_mais_usado, "Assunto mais recorrente.")

    col_5, col_6, col_7 = st.columns(3)

    with col_5:
        _card("Dor dominante", _fmt_texto(contexto["dor_dominante"]), "Base para ganchos fortes.")

    with col_6:
        _card("Módulo campeão", _fmt_texto(contexto["modulo_campeao"]), "Tela que deve aparecer nos conteúdos.")

    with col_7:
        _card("Roteiros prontos", str(roteiros_prontos), "Prontos para gravar/postar.")

    st.divider()

    st.markdown("### Ideias estratégicas de conteúdo")

    st.dataframe(
        ideias,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Gerador rápido de roteiro")

    col_g1, col_g2 = st.columns(2)

    with col_g1:
        tema_roteiro = st.selectbox(
            "Tema",
            TEMAS_BASE,
            key="conteudo_tema_roteiro",
        )

        gancho_roteiro = st.text_area(
            "Gancho",
            value="Empresa boa pode ser péssimo investimento se você pagar caro.",
            height=95,
            key="conteudo_gancho_roteiro",
        )

    with col_g2:
        cta_roteiro = st.text_area(
            "CTA",
            value="Entre na lista de espera da Máquina de Preço-Teto.",
            height=95,
            key="conteudo_cta_roteiro",
        )

        tipo_roteiro = st.selectbox(
            "Tipo de roteiro",
            ["Reels curto", "Carrossel"],
            key="conteudo_tipo_roteiro",
        )

    if tipo_roteiro == "Reels curto":
        roteiro_gerado = _gerar_roteiro_reels(
            tema=tema_roteiro,
            gancho=gancho_roteiro,
            cta=cta_roteiro,
        )
    else:
        roteiro_gerado = _gerar_estrutura_carrossel(
            tema=tema_roteiro,
            gancho=gancho_roteiro,
            cta=cta_roteiro,
        )

    st.markdown("#### Roteiro gerado")
    _copy_box(roteiro_gerado)

    st.divider()

    st.markdown("### Adicionar conteúdo ao calendário")

    with st.form("form_calendario_conteudo"):
        col_a, col_b = st.columns(2)

        with col_a:
            data_postagem = st.text_input(
                "Data prevista de postagem",
                value=datetime.now().strftime("%d/%m/%Y"),
                key="conteudo_data_postagem",
            )

            canal = st.selectbox(
                "Canal",
                CANAIS,
                key="conteudo_canal",
            )

            formato = st.selectbox(
                "Formato",
                FORMATOS,
                key="conteudo_formato",
            )

            tema = st.text_input(
                "Tema",
                value=tema_roteiro,
                key="conteudo_tema",
            )

        with col_b:
            status = st.selectbox(
                "Status",
                STATUS_CONTEUDO,
                key="conteudo_status",
            )

            gancho = st.text_area(
                "Gancho",
                value=gancho_roteiro,
                height=100,
                key="conteudo_gancho",
            )

            cta = st.text_area(
                "CTA",
                value=cta_roteiro,
                height=100,
                key="conteudo_cta",
            )

        roteiro = st.text_area(
            "Roteiro / Estrutura",
            value=roteiro_gerado,
            height=190,
            key="conteudo_roteiro",
        )

        observacoes = st.text_area(
            "Observações",
            value="",
            height=80,
            key="conteudo_observacoes",
        )

        enviar = st.form_submit_button("Salvar conteúdo no calendário")

        if enviar:
            if tema.strip() == "":
                st.error("Preencha o tema do conteúdo.")
            elif gancho.strip() == "":
                st.error("Preencha o gancho do conteúdo.")
            else:
                adicionar_conteudo(
                    data_postagem=data_postagem,
                    canal=canal,
                    formato=formato,
                    tema=tema,
                    gancho=gancho,
                    roteiro=roteiro,
                    cta=cta,
                    status=status,
                    observacoes=observacoes,
                )

                st.success("Conteúdo salvo no calendário.")
                st.rerun()

    st.divider()

    st.markdown("### Calendário editorial")

    conteudos = carregar_conteudos()

    if len(conteudos) == 0:
        st.info("Nenhum conteúdo registrado ainda.")
    else:
        tabela = _preparar_tabela(conteudos)

        st.dataframe(
            tabela,
            use_container_width=True,
            hide_index=True,
        )

        st.divider()

        col_down, col_clean = st.columns(2)

        with col_down:
            with open(CAMINHO_CALENDARIO, "rb") as arquivo:
                st.download_button(
                    label="Baixar calendário em CSV",
                    data=arquivo,
                    file_name="calendario_conteudo.csv",
                    mime="text/csv",
                    key="conteudo_download_csv",
                )

        with col_clean:
            confirmar = st.checkbox(
                "Confirmar limpeza do calendário",
                value=False,
                key="conteudo_confirmar_limpeza",
            )

            if st.button("Limpar calendário", key="conteudo_limpar"):
                if confirmar:
                    limpar_calendario()
                    st.success("Calendário limpo com sucesso.")
                    st.rerun()
                else:
                    st.warning("Marque a confirmação antes de limpar o calendário.")

    st.divider()

    st.markdown("### Regra editorial da marca")

    st.markdown(
        """
        - Não prometa lucro.
        - Não diga que o app recomenda compra ou venda.
        - Não use linguagem de enriquecimento rápido.
        - Mostre método, processo, disciplina e clareza.
        - Use exemplos simples e educativos.
        - Convide o público para beta/lista de espera.
        - Faça o produto parecer útil, não milagroso.
        """
    )

    st.markdown(
        """
        <div class="cont-disclaimer">
            <strong>Nota estratégica:</strong> a central de conteúdo serve para criar consistência.
            O objetivo é gerar aprendizado de mercado: quais temas atraem, quais dores convertem
            e quais demonstrações levam pessoas para o beta ou lista de espera.
        </div>
        """,
        unsafe_allow_html=True,
    )