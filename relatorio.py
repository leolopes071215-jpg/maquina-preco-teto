from datetime import datetime

from valuation import EntradasValuation


def limpar_nome_arquivo(texto: str) -> str:
    texto_limpo = texto.lower().strip()
    caracteres_invalidos = [" ", "/", "\\", ":", "*", "?", '"', "<", ">", "|", "'", "."]
    
    for caractere in caracteres_invalidos:
        texto_limpo = texto_limpo.replace(caractere, "-")

    while "--" in texto_limpo:
        texto_limpo = texto_limpo.replace("--", "-")

    return texto_limpo.strip("-")


def gerar_nome_arquivo_relatorio(empresa: str, ticker: str) -> str:
    data_atual = datetime.now().strftime("%Y-%m-%d")
    empresa_limpa = limpar_nome_arquivo(empresa)
    ticker_limpo = limpar_nome_arquivo(ticker)

    return f"relatorio-valuation-{ticker_limpo}-{empresa_limpa}-{data_atual}.md"


def gerar_relatorio_markdown(
    entradas: EntradasValuation,
    resultado: dict,
    dados_empresa: dict,
    simbolo_moeda: str,
    formatar_moeda,
    formatar_percentual,
    formatar_numero,
) -> str:
    data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")

    tese = dados_empresa.get("tese", "Não informado.")
    riscos = dados_empresa.get("riscos", "Não informado.")
    fundamentos = dados_empresa.get("fundamentos", "Não informado.")
    perfil_empresa = dados_empresa.get("perfil_empresa", "Não informado.")
    data_referencia = dados_empresa.get("data_referencia", "Não informado.")
    fonte_premissas = dados_empresa.get("fonte_premissas", "Não informado.")
    moeda = dados_empresa.get("moeda", "Não informado.")

    relatorio = f"""# Relatório Executivo de Valuation

## 1. Identificação da análise

**Empresa:** {entradas.empresa}  
**Ticker:** {entradas.ticker}  
**Data de geração:** {data_atual}  
**Perfil da empresa:** {perfil_empresa}  
**Moeda/unidade:** {moeda}  
**Data de referência dos dados:** {data_referencia}  
**Fonte das premissas:** {fonte_premissas}  

---

## 2. Resumo executivo

**Preço atual:** {formatar_moeda(entradas.preco_atual, simbolo_moeda)}  
**Preço justo estimado:** {formatar_moeda(resultado["preco_justo_combinado"], simbolo_moeda)}  
**Preço-teto com margem de segurança:** {formatar_moeda(resultado["preco_teto"], simbolo_moeda)}  
**Status educacional:** {resultado["status"]}  

**Margem até o preço-teto:** {formatar_percentual(resultado["margem_ate_preco_teto"])}  
**Potencial até o preço justo:** {formatar_percentual(resultado["potencial_ate_preco_justo"])}  

### Leitura automática

{resultado["explicacao_status"]}

---

## 3. Indicadores calculados

| Indicador | Valor |
|---|---:|
| EPS normalizado | {formatar_moeda(resultado["eps_normalizado"], simbolo_moeda)} |
| FCF por ação | {formatar_moeda(resultado["fcf_por_acao"], simbolo_moeda)} |
| Preço justo por EPS | {formatar_moeda(resultado["preco_justo_eps"], simbolo_moeda)} |
| Preço justo por FCF | {formatar_moeda(resultado["preco_justo_fcf"], simbolo_moeda)} |
| Preço justo combinado | {formatar_moeda(resultado["preco_justo_combinado"], simbolo_moeda)} |
| Preço-teto | {formatar_moeda(resultado["preco_teto"], simbolo_moeda)} |

---

## 4. Premissas utilizadas

| Premissa | Valor |
|---|---:|
| Lucro líquido sustentável | {formatar_moeda(entradas.lucro_liquido_sustentavel, simbolo_moeda)} |
| Fluxo de caixa livre | {formatar_moeda(entradas.fluxo_caixa_livre, simbolo_moeda)} |
| Quantidade de ações | {formatar_numero(entradas.quantidade_acoes)} |
| Preço atual | {formatar_moeda(entradas.preco_atual, simbolo_moeda)} |
| Múltiplo justo EPS | {entradas.multiplo_justo_eps:.2f}x |
| Múltiplo justo FCF | {entradas.multiplo_justo_fcf:.2f}x |
| Peso EPS | {entradas.peso_eps:.0f}% |
| Peso FCF | {entradas.peso_fcf:.0f}% |
| Margem de segurança | {entradas.margem_seguranca:.0f}% |

---

## 5. Tese qualitativa

{tese}

---

## 6. Principais riscos

{riscos}

---

## 7. Fundamentos observados

{fundamentos}

---

## 8. Interpretação educacional

Este relatório não deve ser lido como recomendação de compra, venda ou manutenção de investimentos.

O objetivo é organizar premissas de valuation e transformar os números em uma análise mais clara.

Um preço-teto calculado não é uma verdade absoluta. Ele depende diretamente de:

- qualidade do lucro usado;
- recorrência do fluxo de caixa livre;
- múltiplos escolhidos;
- margem de segurança;
- preço atual;
- riscos da empresa;
- qualidade da tese;
- cenário macroeconômico;
- taxa de juros;
- qualidade da gestão;
- estrutura de capital.

A melhor análise não é a mais otimista. É a que continua fazendo sentido mesmo quando algumas premissas estão erradas.

---

## 9. Aviso importante

Esta ferramenta é apenas educacional.

Ela não representa recomendação de investimento, consultoria financeira, análise certificada, oferta de compra, oferta de venda ou sugestão individualizada.

Antes de tomar qualquer decisão financeira, estude a empresa com profundidade e considere consultar profissionais habilitados.
"""

    return relatorio