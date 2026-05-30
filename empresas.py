EMPRESAS = {
    "Empresa Exemplo": {
        "empresa": "Empresa Exemplo",
        "ticker": "EXEMPLO",
        "perfil_empresa": "Modelo didático genérico.",
        "moeda": "R$",
        "simbolo_moeda": "R$",
        "data_referencia": "Dados didáticos",
        "fonte_premissas": "Premissas fictícias criadas apenas para teste do MVP.",

        "lucro_liquido_sustentavel": 1_000_000_000.0,
        "fluxo_caixa_livre": 800_000_000.0,
        "quantidade_acoes": 500_000_000.0,
        "preco_atual": 15.00,

        "multiplo_justo_eps": 15.0,
        "multiplo_justo_fcf": 14.0,
        "peso_eps": 50,
        "peso_fcf": 50,
        "margem_seguranca": 25,

        "tese": "Empresa didática usada para testar o funcionamento do modelo.",
        "riscos": "Riscos didáticos: queda de lucro, redução de margens e múltiplo excessivo.",
        "fundamentos": "Fundamentos didáticos: lucro positivo, geração de caixa e estrutura simples.",
    },

    "Empresa de Qualidade": {
        "empresa": "Empresa de Qualidade",
        "ticker": "QUALI",
        "perfil_empresa": "Empresa de qualidade / compounder / asset-light.",
        "moeda": "R$",
        "simbolo_moeda": "R$",
        "data_referencia": "Dados didáticos",
        "fonte_premissas": "Premissas fictícias criadas apenas para teste do MVP.",

        "lucro_liquido_sustentavel": 5_000_000_000.0,
        "fluxo_caixa_livre": 4_500_000_000.0,
        "quantidade_acoes": 1_000_000_000.0,
        "preco_atual": 65.00,

        "multiplo_justo_eps": 22.0,
        "multiplo_justo_fcf": 20.0,
        "peso_eps": 45,
        "peso_fcf": 55,
        "margem_seguranca": 20,

        "tese": "Empresa com alta qualidade, boa geração de caixa e vantagem competitiva relevante.",
        "riscos": "Risco de pagar caro demais por qualidade, desaceleração do crescimento e compressão de múltiplos.",
        "fundamentos": "Margens elevadas, baixo endividamento, retorno sobre capital alto e caixa recorrente.",
    },

    "Empresa Cíclica": {
        "empresa": "Empresa Cíclica",
        "ticker": "CICLO",
        "perfil_empresa": "Empresa cíclica, sensível ao ciclo econômico.",
        "moeda": "R$",
        "simbolo_moeda": "R$",
        "data_referencia": "Dados didáticos",
        "fonte_premissas": "Premissas fictícias criadas apenas para teste do MVP.",

        "lucro_liquido_sustentavel": 2_000_000_000.0,
        "fluxo_caixa_livre": 1_200_000_000.0,
        "quantidade_acoes": 700_000_000.0,
        "preco_atual": 28.00,

        "multiplo_justo_eps": 10.0,
        "multiplo_justo_fcf": 9.0,
        "peso_eps": 60,
        "peso_fcf": 40,
        "margem_seguranca": 35,

        "tese": "Empresa mais sensível ao ciclo econômico, exigindo margem de segurança maior.",
        "riscos": "Queda de demanda, pressão de custos, volatilidade de lucro e dependência do ciclo.",
        "fundamentos": "Lucro variável, fluxo de caixa menos previsível e necessidade de valuation mais conservador.",
    },

    "Mastercard": {
        "empresa": "Mastercard Incorporated",
        "ticker": "MA",
        "perfil_empresa": "Empresa de qualidade / compounder / asset-light, com crescimento estrutural e sensibilidade moderada ao ciclo econômico.",
        "moeda": "US$ em milhões; ações em milhões; preço por ação em US$",
        "simbolo_moeda": "US$",
        "data_referencia": "10-K 2025 e cotação consultada manualmente",
        "fonte_premissas": (
            "Lucro líquido baseado no net income de 2025: US$ 14,968 bilhões. "
            "FCF estimado como caixa operacional menos compra de property/equipment e software capitalizado: "
            "17,648 - 489 - 726 = US$ 16,433 bilhões. "
            "Quantidade de ações baseada na média diluída de 2025: 906 milhões. "
            "Preço atual inserido manualmente."
        ),

        "lucro_liquido_sustentavel": 14_968.0,
        "fluxo_caixa_livre": 16_433.0,
        "quantidade_acoes": 906.0,
        "preco_atual": 493.98,

        "multiplo_justo_eps": 30.0,
        "multiplo_justo_fcf": 28.0,
        "peso_eps": 50,
        "peso_fcf": 50,
        "margem_seguranca": 20,

        "tese": (
            "Mastercard é uma empresa global de tecnologia de pagamentos, com modelo asset-light, "
            "alta geração de caixa, margens elevadas, forte efeito de rede, marca global e crescimento "
            "estrutural ligado à digitalização dos pagamentos."
        ),

        "riscos": (
            "Os principais riscos são valuation elevado, regulação sobre taxas de intercâmbio, concorrência "
            "de Visa, fintechs, carteiras digitais, bancos e soluções alternativas de pagamento, além de "
            "risco macroeconômico em volumes de consumo e pagamentos internacionais."
        ),

        "fundamentos": (
            "A empresa apresenta alta conversão de lucro em caixa, baixa necessidade de capital físico, "
            "escala global, efeito de rede, crescimento de receita, forte recompra de ações e expansão em "
            "serviços de valor agregado."
        ),
    },

    "O'Reilly Automotive": {
        "empresa": "O'Reilly Automotive, Inc.",
        "ticker": "ORLY",
        "perfil_empresa": "Empresa de qualidade / varejo especializado / compounder, com demanda relativamente resiliente e sensibilidade moderada ao ciclo econômico.",
        "moeda": "US$ em milhões; ações em milhões; preço por ação em US$",
        "simbolo_moeda": "US$",
        "data_referencia": "10-K 2025, release FY 2025 e cotação consultada manualmente",
        "fonte_premissas": (
            "Lucro líquido sustentável baseado no net income de 2025: US$ 2,538 bilhões. "
            "FCF sustentável estimado pela média dos free cash flows de 2023, 2024 e 2025: "
            "(1,987.720 + 1,987.808 + 1,563.250) / 3 = aproximadamente US$ 1,846 bilhões. "
            "Quantidade de ações baseada na média diluída de 2025: 856 milhões. "
            "Preço atual inserido manualmente."
        ),

        "lucro_liquido_sustentavel": 2_538.209,
        "fluxo_caixa_livre": 1_846.259,
        "quantidade_acoes": 856.0,
        "preco_atual": 86.88,

        "multiplo_justo_eps": 28.0,
        "multiplo_justo_fcf": 30.0,
        "peso_eps": 70,
        "peso_fcf": 30,
        "margem_seguranca": 20,

        "tese": (
            "O'Reilly Automotive é uma das principais redes de autopeças dos Estados Unidos, com forte execução operacional, "
            "histórico longo de crescimento, expansão de lojas, alta recorrência de demanda e cultura agressiva de recompra de ações. "
            "O negócio se beneficia de uma frota envelhecida, manutenção recorrente de veículos e bom posicionamento nos mercados DIY e profissional."
        ),

        "riscos": (
            "Os principais riscos são valuation elevado, pressão de custos, necessidade crescente de capital para expansão, "
            "competição com AutoZone, Advance Auto Parts, varejistas online e distribuidores regionais, além de eventual desaceleração "
            "no consumo e compressão de múltiplos. O FCF também pode oscilar por capex, estoques e expansão de lojas."
        ),

        "fundamentos": (
            "A empresa apresenta crescimento consistente de vendas, margens operacionais elevadas para o varejo, forte geração de lucro, "
            "recompras relevantes de ações e histórico de crescimento de EPS. Para valuation, o lucro por ação tende a ser mais estável "
            "do que o FCF anual isolado, por isso o modelo usa peso maior em EPS e FCF médio normalizado."
        ),
    },

    "Visa": {
        "empresa": "Visa Inc.",
        "ticker": "V",
        "perfil_empresa": "Empresa de qualidade / compounder / asset-light, com forte efeito de rede, alta margem e crescimento estrutural em pagamentos digitais.",
        "moeda": "US$ em milhões; ações em milhões; preço por ação em US$",
        "simbolo_moeda": "US$",
        "data_referencia": "Annual Report/Form 10-K 2025 e cotação consultada manualmente",
        "fonte_premissas": (
            "Lucro líquido sustentável baseado no net income de 2025: US$ 20,058 bilhões. "
            "FCF estimado como caixa operacional menos purchases of property, equipment and technology: "
            "23,059 - 1,482 = US$ 21,577 bilhões. "
            "Quantidade de ações baseada na média diluída equivalente classe A de 2025: 1,966 milhões. "
            "Preço atual inserido manualmente."
        ),

        "lucro_liquido_sustentavel": 20_058.0,
        "fluxo_caixa_livre": 21_577.0,
        "quantidade_acoes": 1_966.0,
        "preco_atual": 326.36,

        "multiplo_justo_eps": 30.0,
        "multiplo_justo_fcf": 28.0,
        "peso_eps": 50,
        "peso_fcf": 50,
        "margem_seguranca": 20,

        "tese": (
            "Visa é uma das maiores redes globais de pagamentos, com modelo altamente escalável, "
            "baixo uso de capital físico, margens elevadas, forte geração de caixa e efeito de rede global. "
            "A empresa se beneficia da digitalização dos pagamentos, crescimento do consumo eletrônico, "
            "pagamentos transfronteiriços e expansão de serviços de valor agregado."
        ),

        "riscos": (
            "Os principais riscos são valuation elevado, regulação sobre taxas de intercâmbio, disputas legais, "
            "concorrência com Mastercard, fintechs, carteiras digitais, bancos, stablecoins e novas infraestruturas de pagamento. "
            "Também existe sensibilidade ao ciclo econômico, especialmente em consumo, viagens e pagamentos internacionais."
        ),

        "fundamentos": (
            "A empresa apresenta alta margem operacional, forte conversão de lucro em caixa, baixa necessidade de capex, "
            "escala global, recompra recorrente de ações e crescimento consistente de receita e EPS. "
            "Por ser uma empresa de qualidade, aceita múltiplos superiores à média do mercado, mas ainda exige margem de segurança."
        ),
    },
}