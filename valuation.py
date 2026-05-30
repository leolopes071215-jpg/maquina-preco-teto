from dataclasses import dataclass


@dataclass
class EntradasValuation:
    empresa: str
    ticker: str
    lucro_liquido_sustentavel: float
    fluxo_caixa_livre: float
    quantidade_acoes: float
    multiplo_justo_eps: float
    multiplo_justo_fcf: float
    peso_eps: float
    peso_fcf: float
    margem_seguranca: float
    preco_atual: float


def calcular_valuation(entradas: EntradasValuation) -> dict:
    validar_entradas(entradas)

    eps_normalizado = entradas.lucro_liquido_sustentavel / entradas.quantidade_acoes
    fcf_por_acao = entradas.fluxo_caixa_livre / entradas.quantidade_acoes

    preco_justo_eps = eps_normalizado * entradas.multiplo_justo_eps
    preco_justo_fcf = fcf_por_acao * entradas.multiplo_justo_fcf

    soma_pesos = entradas.peso_eps + entradas.peso_fcf

    peso_eps_normalizado = entradas.peso_eps / soma_pesos
    peso_fcf_normalizado = entradas.peso_fcf / soma_pesos

    preco_justo_combinado = (
        preco_justo_eps * peso_eps_normalizado
        + preco_justo_fcf * peso_fcf_normalizado
    )

    preco_teto = preco_justo_combinado * (1 - entradas.margem_seguranca / 100)

    margem_ate_preco_teto = calcular_percentual(
        valor_final=preco_teto,
        valor_inicial=entradas.preco_atual,
    )

    potencial_ate_preco_justo = calcular_percentual(
        valor_final=preco_justo_combinado,
        valor_inicial=entradas.preco_atual,
    )

    status = definir_status(
        preco_atual=entradas.preco_atual,
        preco_teto=preco_teto,
        preco_justo=preco_justo_combinado,
        
    )

    explicacao_status = explicar_status(status)

    return {
    "eps_normalizado": eps_normalizado,
    "fcf_por_acao": fcf_por_acao,
    "preco_justo_eps": preco_justo_eps,
    "preco_justo_fcf": preco_justo_fcf,
    "preco_justo_combinado": preco_justo_combinado,
    "preco_teto": preco_teto,
    "margem_ate_preco_teto": margem_ate_preco_teto,
    "potencial_ate_preco_justo": potencial_ate_preco_justo,
    "status": status,
    "explicacao_status": explicacao_status,
}
        
        
        
        
        

def validar_entradas(entradas: EntradasValuation) -> None:
    if entradas.quantidade_acoes <= 0:
        raise ValueError("A quantidade de ações precisa ser maior que zero.")

    if entradas.preco_atual <= 0:
        raise ValueError("O preço atual precisa ser maior que zero.")

    if entradas.peso_eps < 0 or entradas.peso_fcf < 0:
        raise ValueError("Os pesos não podem ser negativos.")

    if entradas.peso_eps + entradas.peso_fcf == 0:
        raise ValueError("A soma dos pesos precisa ser maior que zero.")

    if entradas.margem_seguranca < 0 or entradas.margem_seguranca >= 100:
        raise ValueError("A margem de segurança precisa estar entre 0% e 99%.")

    if entradas.multiplo_justo_eps < 0:
        raise ValueError("O múltiplo justo de EPS não pode ser negativo.")

    if entradas.multiplo_justo_fcf < 0:
        raise ValueError("O múltiplo justo de FCF não pode ser negativo.")


def calcular_percentual(valor_final: float, valor_inicial: float) -> float:
    return ((valor_final / valor_inicial) - 1) * 100


def definir_status(preco_atual: float, preco_teto: float, preco_justo: float) -> str:
    if preco_atual <= preco_teto:
        return "COMPRA"

    if preco_atual <= preco_justo:
        return "NEUTRO"

    return "AGUARDE"


def explicar_status(status: str) -> str:
    if status == "COMPRA":
        return (
            "O preço atual está abaixo ou igual ao preço-teto calculado. "
            "Pelas premissas inseridas, a ação está dentro de uma zona de entrada com margem de segurança."
        )

    if status == "NEUTRO":
        return (
            "O preço atual está acima do preço-teto conservador, mas ainda abaixo ou próximo do preço justo estimado. "
            "Pelas premissas inseridas, a ação não está barata o suficiente para uma compra com margem de segurança, "
            "mas também não está claramente cara."
        )

    return (
        "O preço atual está acima do preço justo estimado. "
        "Pelas premissas inseridas, a ação exige paciência, revisão das premissas ou uma queda de preço para oferecer melhor relação risco-retorno."
    )