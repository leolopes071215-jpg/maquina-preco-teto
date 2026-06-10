

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

