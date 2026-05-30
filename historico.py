import csv
from datetime import datetime
from pathlib import Path


CAMINHO_HISTORICO = Path("data") / "historico_analises.csv"


CAMPOS_HISTORICO = [
    "data_hora",
    "empresa",
    "ticker",
    "preco_atual",
    "eps_normalizado",
    "fcf_por_acao",
    "preco_justo_eps",
    "preco_justo_fcf",
    "preco_justo_combinado",
    "preco_teto",
    "margem_ate_preco_teto",
    "potencial_ate_preco_justo",
    "status",
    "lucro_liquido_sustentavel",
    "fluxo_caixa_livre",
    "quantidade_acoes",
    "multiplo_justo_eps",
    "multiplo_justo_fcf",
    "peso_eps",
    "peso_fcf",
    "margem_seguranca",
]


def garantir_arquivo_historico() -> None:
    CAMINHO_HISTORICO.parent.mkdir(parents=True, exist_ok=True)

    if not CAMINHO_HISTORICO.exists():
        with open(CAMINHO_HISTORICO, mode="w", newline="", encoding="utf-8") as arquivo:
            escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_HISTORICO)
            escritor.writeheader()


def salvar_analise(entradas, resultado: dict) -> None:
    garantir_arquivo_historico()

    linha = {
        "data_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "empresa": entradas.empresa,
        "ticker": entradas.ticker,
        "preco_atual": entradas.preco_atual,
        "eps_normalizado": resultado["eps_normalizado"],
        "fcf_por_acao": resultado["fcf_por_acao"],
        "preco_justo_eps": resultado["preco_justo_eps"],
        "preco_justo_fcf": resultado["preco_justo_fcf"],
        "preco_justo_combinado": resultado["preco_justo_combinado"],
        "preco_teto": resultado["preco_teto"],
        "margem_ate_preco_teto": resultado["margem_ate_preco_teto"],
        "potencial_ate_preco_justo": resultado["potencial_ate_preco_justo"],
        "status": resultado["status"],
        "lucro_liquido_sustentavel": entradas.lucro_liquido_sustentavel,
        "fluxo_caixa_livre": entradas.fluxo_caixa_livre,
        "quantidade_acoes": entradas.quantidade_acoes,
        "multiplo_justo_eps": entradas.multiplo_justo_eps,
        "multiplo_justo_fcf": entradas.multiplo_justo_fcf,
        "peso_eps": entradas.peso_eps,
        "peso_fcf": entradas.peso_fcf,
        "margem_seguranca": entradas.margem_seguranca,
    }

    with open(CAMINHO_HISTORICO, mode="a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_HISTORICO)
        escritor.writerow(linha)


def carregar_historico() -> list[dict]:
    garantir_arquivo_historico()

    with open(CAMINHO_HISTORICO, mode="r", newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        return list(leitor)