

# ============================================================

# ============================================================
# Compatibilidade v3.8.83
# ------------------------------------------------------------
# Alguns m?dulos antigos importam renderizar_lista_espera_valoris.
# Este wrapper garante compatibilidade mesmo se o arquivo local
# estiver com outro nome de renderiza??o.
# ============================================================

def renderizar_lista_espera_valoris():
    if "renderizar_painel_lista_espera_valoris" in globals():
        return renderizar_painel_lista_espera_valoris()

    if "renderizar_lista_espera_beta" in globals():
        return renderizar_lista_espera_beta()

    if "renderizar_lista_espera" in globals():
        return renderizar_lista_espera()

    import streamlit as st
    st.warning("Lista de espera carregada, mas nenhum renderizador principal foi encontrado.")

# ============================================================
# Compatibilidade v3.8.83 ? fun??es antigas da lista de espera
# ============================================================

def _compat_caminho_lista_espera():
    from pathlib import Path
    return Path("lista_espera_beta.csv")


def _compat_campos_lista_espera():
    return [
        "id",
        "data_criacao",
        "nome",
        "contato",
        "perfil",
        "principal_dor",
        "plano_interesse",
        "preco_aceitavel",
        "pagaria_agora",
        "comentario",
    ]


def _compat_garantir_lista_espera():
    import csv

    caminho = _compat_caminho_lista_espera()
    campos = _compat_campos_lista_espera()

    if caminho.exists():
        return

    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()


def carregar_leads_lista_espera():
    import csv

    _compat_garantir_lista_espera()
    caminho = _compat_caminho_lista_espera()

    with caminho.open("r", newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        return list(leitor)


def gerar_csv_lista_espera():
    _compat_garantir_lista_espera()
    return _compat_caminho_lista_espera().read_text(encoding="utf-8")


def salvar_lead_lista_espera(dados):
    import csv
    from datetime import datetime
    from uuid import uuid4

    _compat_garantir_lista_espera()

    campos = _compat_campos_lista_espera()
    caminho = _compat_caminho_lista_espera()

    registro = {
        "id": str(uuid4()),
        "data_criacao": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "nome": str(dados.get("nome", "")).strip(),
        "contato": str(dados.get("contato", dados.get("email", ""))).strip(),
        "perfil": str(dados.get("perfil", "")).strip(),
        "principal_dor": str(dados.get("principal_dor", "")).strip(),
        "plano_interesse": str(dados.get("plano_interesse", "")).strip(),
        "preco_aceitavel": str(dados.get("preco_aceitavel", "")).strip(),
        "pagaria_agora": str(dados.get("pagaria_agora", "")).strip(),
        "comentario": str(dados.get("comentario", "")).strip(),
    }

    with caminho.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writerow(registro)

    return {
        "ok": True,
        "mensagem": "Entrada registrada com sucesso.",
        "registro": registro,
    }

# ============================================================
# Compatibilidade v3.8.86 ? renderizador da lista de espera
# ------------------------------------------------------------
# Aceita chamadas antigas e novas:
# renderizar_lista_espera_valoris()
# renderizar_lista_espera_valoris(modo_admin=False, chave_contexto="...")
# ============================================================

def renderizar_lista_espera_valoris(*args, **kwargs):
    candidatos = [
        "renderizar_painel_lista_espera_valoris",
        "renderizar_lista_espera_beta",
        "renderizar_lista_espera",
    ]

    for nome in candidatos:
        funcao = globals().get(nome)

        if callable(funcao):
            try:
                return funcao(*args, **kwargs)
            except TypeError:
                try:
                    return funcao()
                except TypeError:
                    continue

    import streamlit as st

    modo_admin = bool(kwargs.get("modo_admin", False))
    chave_contexto = str(kwargs.get("chave_contexto", "lista_espera"))

    st.markdown("### Entrar na lista de espera")

    with st.form(f"form_lista_espera_{chave_contexto}"):
        nome = st.text_input("Nome", key=f"{chave_contexto}_nome")
        contato = st.text_input("E-mail ou WhatsApp", key=f"{chave_contexto}_contato")
        perfil = st.selectbox(
            "Perfil",
            ["Investidor iniciante", "Investidor intermedi?rio", "Investidor avan?ado", "Analista", "Outro"],
            key=f"{chave_contexto}_perfil",
        )
        principal_dor = st.text_area(
            "Qual sua maior dificuldade ao analisar uma empresa?",
            key=f"{chave_contexto}_dor",
        )
        comentario = st.text_area(
            "Coment?rio adicional",
            key=f"{chave_contexto}_comentario",
        )

        enviado = st.form_submit_button("Entrar na lista")

        if enviado:
            if "salvar_lead_lista_espera" in globals():
                registro = salvar_lead_lista_espera(
                    {
                        "nome": nome,
                        "contato": contato,
                        "perfil": perfil,
                        "principal_dor": principal_dor,
                        "comentario": comentario,
                    }
                )
                st.success("Entrada registrada com sucesso.")
                return registro

            st.warning("Lista de espera dispon?vel, mas a fun??o de salvamento n?o foi encontrada.")

    if modo_admin:
        st.markdown("#### Leads registrados")

        if "carregar_leads_lista_espera" in globals():
            leads = carregar_leads_lista_espera()

            if leads:
                st.dataframe(leads, use_container_width=True)
            else:
                st.info("Nenhum lead registrado ainda.")
        else:
            st.warning("Fun??o carregar_leads_lista_espera n?o encontrada.")

