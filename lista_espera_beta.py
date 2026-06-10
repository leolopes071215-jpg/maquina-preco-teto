

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

