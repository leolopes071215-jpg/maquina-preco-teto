# painel_beta.py

import csv
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List

import streamlit as st


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v2.8 — Painel Mestre Beta e Decisão de Avanço
# ------------------------------------------------------------
# Esta tela consolida a Fase 2 inteira.
#
# Objetivo:
# - juntar aprendizado, rodadas, prioridades, sprints,
#   pré-venda, oferta paga e CRM
# - medir maturidade do beta
# - indicar se o produto deve continuar em validação,
#   corrigir gargalos, vender manualmente ou avançar para Fase 3
# ============================================================


ARQUIVOS_FASE_2 = {
    "aprendizado_beta": Path("aprendizado_beta_real.csv"),
    "rodadas_beta": Path("rodadas_beta.csv"),
    "prioridades_beta": Path("priorizacao_feedback_beta.csv"),
    "sprints_beta": Path("sprints_beta.csv"),
    "pre_venda_beta": Path("pre_venda_beta.csv"),
    "oferta_paga": Path("ofertas_beta_pago.csv"),
    "crm_beta": Path("crm_beta.csv"),
}


def _carregar_csv(caminho: Path) -> List[Dict[str, str]]:
    if not caminho.exists():
        return []

    try:
        with open(caminho, "r", newline="", encoding="utf-8") as arquivo:
            leitor = csv.DictReader(arquivo)
            return [dict(linha) for linha in leitor]
    except Exception:
        return []


def _safe_float(valor: Any, default: float = 0.0) -> float:
    try:
        texto = str(valor).replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
        return float(texto)
    except (TypeError, ValueError):
        return default


def _safe_int(valor: Any, default: int = 0) -> int:
    try:
        return int(float(valor))
    except (TypeError, ValueError):
        return default


def _fmt_moeda(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_percentual(valor: float) -> str:
    return f"{valor:.1f}%"


def _media(registros: List[Dict[str, str]], campo: str) -> float:
    valores = []

    for registro in registros:
        valor = _safe_float(registro.get(campo))

        if valor > 0:
            valores.append(valor)

    if len(valores) == 0:
        return 0.0

    return mean(valores)


def _contar(registros: List[Dict[str, str]], campo: str, valor: str) -> int:
    return len([registro for registro in registros if registro.get(campo) == valor])


def _somar(registros: List[Dict[str, str]], campo: str) -> float:
    return sum(_safe_float(registro.get(campo)) for registro in registros)


def _mais_frequente(registros: List[Dict[str, str]], campo: str) -> str:
    contagem: Dict[str, int] = {}

    for registro in registros:
        valor = str(registro.get(campo, "")).strip()

        if valor == "":
            continue

        contagem[valor] = contagem.get(valor, 0) + 1

    if len(contagem) == 0:
        return "N/D"

    return max(contagem, key=contagem.get)


def _carregar_dados_fase_2() -> Dict[str, List[Dict[str, str]]]:
    return {
        nome: _carregar_csv(caminho)
        for nome, caminho in ARQUIVOS_FASE_2.items()
    }


def _calcular_receita_ponderada_crm(registros_crm: List[Dict[str, str]]) -> float:
    total = 0.0

    for registro in registros_crm:
        valor = _safe_float(registro.get("valor_potencial"))
        chance = _safe_float(registro.get("chance_conversao")) / 100
        total += valor * chance

    return total


def _calcular_receita_ponderada_pre_venda(registros_pre_venda: List[Dict[str, str]]) -> float:
    total = 0.0

    for registro in registros_pre_venda:
        resposta = registro.get("resposta_pagamento", "")
        preco = _safe_float(registro.get("preco_apresentado"))
        chance = _safe_float(registro.get("chance_conversao")) / 100

        if resposta in ["Pagaria agora", "Pagaria depois de melhorias", "Talvez pagaria"]:
            total += preco * chance

    return total


def _calcular_score_validacao(dados: Dict[str, List[Dict[str, str]]]) -> int:
    aprendizado = dados["aprendizado_beta"]
    rodadas = dados["rodadas_beta"]
    prioridades = dados["prioridades_beta"]
    sprints = dados["sprints_beta"]
    pre_venda = dados["pre_venda_beta"]
    ofertas = dados["oferta_paga"]
    crm = dados["crm_beta"]

    testes_reais = len(aprendizado)
    rodadas_concluidas = _contar(rodadas, "status_rodada", "Concluída")
    melhorias_criticas = len(
        [
            registro for registro in prioridades
            if _safe_int(registro.get("score_prioridade")) >= 70
        ]
    )
    sprints_concluidas = _contar(sprints, "status_sprint", "Concluída")
    pre_vendas = len(pre_venda)
    leads_crm = len(crm)

    pontos = 0.0

    pontos += min(testes_reais * 4.0, 20)
    pontos += min(len(rodadas) * 5.0, 15)
    pontos += min(rodadas_concluidas * 6.0, 12)
    pontos += min(melhorias_criticas * 4.0, 12)
    pontos += min(len(sprints) * 3.0, 9)
    pontos += min(sprints_concluidas * 5.0, 10)
    pontos += min(pre_vendas * 3.0, 12)
    pontos += min(len(ofertas) * 4.0, 8)
    pontos += min(leads_crm * 2.5, 15)

    return int(round(max(0, min(100, pontos))))


def _calcular_score_comercial(dados: Dict[str, List[Dict[str, str]]]) -> int:
    pre_venda = dados["pre_venda_beta"]
    ofertas = dados["oferta_paga"]
    crm = dados["crm_beta"]

    total_pre_venda = len(pre_venda)
    total_ofertas = len(ofertas)
    total_leads = len(crm)

    pagaria_agora = _contar(pre_venda, "resposta_pagamento", "Pagaria agora")
    pagaria_depois = _contar(pre_venda, "resposta_pagamento", "Pagaria depois de melhorias")
    leads_quentes = _contar(crm, "temperatura_lead", "Quente") + _contar(
        crm,
        "temperatura_lead",
        "Muito quente",
    )
    convertidos = _contar(crm, "status_comercial", "Convertido")
    ofertas_boas = len(
        [
            oferta for oferta in ofertas
            if _safe_int(oferta.get("score_oferta")) >= 70
        ]
    )

    receita_pre_venda = _calcular_receita_ponderada_pre_venda(pre_venda)
    receita_crm = _calcular_receita_ponderada_crm(crm)
    receita_total = receita_pre_venda + receita_crm

    pontos = 0.0

    pontos += min(total_pre_venda * 5.0, 20)
    pontos += min(pagaria_agora * 10.0, 25)
    pontos += min(pagaria_depois * 5.0, 15)
    pontos += min(total_ofertas * 5.0, 10)
    pontos += min(ofertas_boas * 8.0, 16)
    pontos += min(total_leads * 3.0, 18)
    pontos += min(leads_quentes * 6.0, 18)
    pontos += min(convertidos * 15.0, 30)

    if receita_total > 0:
        pontos += min(receita_total / 10, 15)

    return int(round(max(0, min(100, pontos))))


def _calcular_score_execucao(dados: Dict[str, List[Dict[str, str]]]) -> int:
    prioridades = dados["prioridades_beta"]
    sprints = dados["sprints_beta"]
    rodadas = dados["rodadas_beta"]

    prioridades_altas = len(
        [
            registro for registro in prioridades
            if _safe_int(registro.get("score_prioridade")) >= 70
        ]
    )
    prioridades_concluidas = _contar(prioridades, "status", "Concluída")

    sprints_total = len(sprints)
    sprints_em_desenvolvimento = _contar(sprints, "status_sprint", "Em desenvolvimento")
    sprints_teste = _contar(sprints, "status_sprint", "Em teste")
    sprints_concluidas = _contar(sprints, "status_sprint", "Concluída")

    rodadas_concluidas = _contar(rodadas, "status_rodada", "Concluída")

    media_score_sprints = _media(sprints, "score_execucao")
    media_score_prioridades = _media(prioridades, "score_prioridade")

    pontos = 0.0

    pontos += min(prioridades_altas * 5.0, 20)
    pontos += min(prioridades_concluidas * 8.0, 16)
    pontos += min(sprints_total * 4.0, 16)
    pontos += min(sprints_concluidas * 10.0, 30)
    pontos += min(sprints_teste * 6.0, 12)
    pontos += min(rodadas_concluidas * 5.0, 15)
    pontos += media_score_sprints * 0.12
    pontos += media_score_prioridades * 0.08

    if sprints_em_desenvolvimento > 3:
        pontos -= 12

    return int(round(max(0, min(100, pontos))))


def _calcular_score_geral_fase_2(dados: Dict[str, List[Dict[str, str]]]) -> Dict[str, int]:
    score_validacao = _calcular_score_validacao(dados)
    score_comercial = _calcular_score_comercial(dados)
    score_execucao = _calcular_score_execucao(dados)

    score_geral = int(
        round(
            score_validacao * 0.40
            + score_comercial * 0.35
            + score_execucao * 0.25
        )
    )

    return {
        "validacao": score_validacao,
        "comercial": score_comercial,
        "execucao": score_execucao,
        "geral": max(0, min(100, score_geral)),
    }


def _classificar_fase_2(score_geral: int) -> str:
    if score_geral >= 85:
        return "Pronto para avançar com cautela"
    if score_geral >= 70:
        return "Fase 2 forte, preparar Fase 3"
    if score_geral >= 55:
        return "Boa evolução, ainda precisa validação"
    if score_geral >= 40:
        return "Fase 2 incompleta"
    return "Ainda cedo para avançar"


def _decisao_recomendada(dados: Dict[str, List[Dict[str, str]]], scores: Dict[str, int]) -> str:
    score_geral = scores["geral"]
    score_comercial = scores["comercial"]
    score_execucao = scores["execucao"]

    pre_venda = dados["pre_venda_beta"]
    crm = dados["crm_beta"]
    ofertas = dados["oferta_paga"]
    sprints = dados["sprints_beta"]
    aprendizado = dados["aprendizado_beta"]

    pagaria_agora = _contar(pre_venda, "resposta_pagamento", "Pagaria agora")
    leads_quentes = _contar(crm, "temperatura_lead", "Quente") + _contar(
        crm,
        "temperatura_lead",
        "Muito quente",
    )
    ofertas_boas = len(
        [
            oferta for oferta in ofertas
            if _safe_int(oferta.get("score_oferta")) >= 70
        ]
    )
    sprints_em_desenvolvimento = _contar(sprints, "status_sprint", "Em desenvolvimento")

    if score_geral >= 85 and score_comercial >= 70:
        return "Avançar para Fase 3 com beta pago controlado"

    if pagaria_agora > 0 and leads_quentes > 0 and ofertas_boas > 0:
        return "Testar venda manual com poucos leads antes da Fase 3"

    if score_comercial < 45 and len(aprendizado) >= 5:
        return "Melhorar oferta, clareza de valor e pré-venda antes de avançar"

    if score_execucao < 45 and len(sprints) > 0:
        return "Concluir sprints pendentes antes de abrir nova fase"

    if sprints_em_desenvolvimento > 3:
        return "Reduzir escopo e finalizar uma sprint por vez"

    if score_geral >= 70:
        return "Preparar Fase 3, mas continuar validando comercialmente"

    if score_geral >= 55:
        return "Continuar Fase 2 com foco em usuários reais e pré-venda"

    return "Não avançar ainda; coletar mais testes, feedback e sinais comerciais"


def _gerar_tabela_resumo(dados: Dict[str, List[Dict[str, str]]]) -> List[Dict[str, str]]:
    aprendizado = dados["aprendizado_beta"]
    rodadas = dados["rodadas_beta"]
    prioridades = dados["prioridades_beta"]
    sprints = dados["sprints_beta"]
    pre_venda = dados["pre_venda_beta"]
    ofertas = dados["oferta_paga"]
    crm = dados["crm_beta"]

    return [
        {
            "Área": "Aprendizado Beta",
            "Registros": str(len(aprendizado)),
            "Indicador-chave": "Testes reais registrados",
            "Leitura": _ler_volume(len(aprendizado), 5, 10),
        },
        {
            "Área": "Rodadas Beta",
            "Registros": str(len(rodadas)),
            "Indicador-chave": f"{_contar(rodadas, 'status_rodada', 'Concluída')} concluída(s)",
            "Leitura": _ler_volume(len(rodadas), 1, 3),
        },
        {
            "Área": "Prioridades Beta",
            "Registros": str(len(prioridades)),
            "Indicador-chave": f"{_media(prioridades, 'score_prioridade'):.1f}/100 score médio",
            "Leitura": _ler_volume(len(prioridades), 3, 8),
        },
        {
            "Área": "Sprints Beta",
            "Registros": str(len(sprints)),
            "Indicador-chave": f"{_contar(sprints, 'status_sprint', 'Concluída')} concluída(s)",
            "Leitura": _ler_volume(len(sprints), 1, 4),
        },
        {
            "Área": "Pré-venda Beta",
            "Registros": str(len(pre_venda)),
            "Indicador-chave": f"{_contar(pre_venda, 'resposta_pagamento', 'Pagaria agora')} pagaria(m) agora",
            "Leitura": _ler_volume(len(pre_venda), 5, 15),
        },
        {
            "Área": "Oferta Paga",
            "Registros": str(len(ofertas)),
            "Indicador-chave": f"{_media(ofertas, 'score_oferta'):.1f}/100 score médio",
            "Leitura": _ler_volume(len(ofertas), 1, 3),
        },
        {
            "Área": "CRM Beta",
            "Registros": str(len(crm)),
            "Indicador-chave": f"{_fmt_moeda(_calcular_receita_ponderada_crm(crm))} ponderado",
            "Leitura": _ler_volume(len(crm), 5, 20),
        },
    ]


def _ler_volume(valor: int, minimo: int, forte: int) -> str:
    if valor >= forte:
        return "Forte"
    if valor >= minimo:
        return "Em validação"
    if valor > 0:
        return "Inicial"
    return "Vazio"


def _gerar_alertas(dados: Dict[str, List[Dict[str, str]]], scores: Dict[str, int]) -> List[str]:
    alertas = []

    aprendizado = dados["aprendizado_beta"]
    rodadas = dados["rodadas_beta"]
    prioridades = dados["prioridades_beta"]
    sprints = dados["sprints_beta"]
    pre_venda = dados["pre_venda_beta"]
    ofertas = dados["oferta_paga"]
    crm = dados["crm_beta"]

    if len(aprendizado) < 5:
        alertas.append("Poucos testes reais registrados. Antes de escalar, colete pelo menos 5 feedbacks reais.")

    if len(rodadas) == 0:
        alertas.append("Nenhuma rodada beta registrada. Organize os testes por ciclos, não por mensagens soltas.")

    if len(prioridades) == 0:
        alertas.append("Nenhuma prioridade registrada. Feedback sem priorização vira bagunça.")

    if len(sprints) == 0:
        alertas.append("Nenhuma sprint beta registrada. Transforme prioridade em execução controlada.")

    if len(pre_venda) < 5:
        alertas.append("Poucas conversas de pré-venda. Validação comercial exige falar de preço com usuários reais.")

    if len(ofertas) == 0:
        alertas.append("Nenhuma oferta paga criada. Sem oferta clara, o CRM não terá o que vender.")

    if len(crm) == 0:
        alertas.append("CRM vazio. Leads sem registro geram follow-up perdido.")

    if scores["comercial"] < 45:
        alertas.append("Score comercial baixo. Foque em promessa, objeções, preço e conversas manuais.")

    if scores["execucao"] < 45 and len(sprints) > 0:
        alertas.append("Score de execução baixo. Finalize sprints pequenas antes de abrir novas frentes.")

    if len(alertas) == 0:
        alertas.append("Nenhum alerta crítico. A Fase 2 está bem estruturada para continuar evoluindo.")

    return alertas


def _gerar_proximas_acoes(dados: Dict[str, List[Dict[str, str]]], scores: Dict[str, int]) -> List[Dict[str, str]]:
    acoes = []

    aprendizado = dados["aprendizado_beta"]
    pre_venda = dados["pre_venda_beta"]
    ofertas = dados["oferta_paga"]
    crm = dados["crm_beta"]
    sprints = dados["sprints_beta"]

    if len(aprendizado) < 5:
        acoes.append(
            {
                "Prioridade": "Muito alta",
                "Ação": "Coletar 5 testes reais",
                "Motivo": "Sem usuário real, o produto fica baseado em achismo.",
            }
        )

    if len(pre_venda) < 5:
        acoes.append(
            {
                "Prioridade": "Muito alta",
                "Ação": "Fazer 5 conversas de preço",
                "Motivo": "É preciso saber se existe intenção real de pagamento.",
            }
        )

    if len(ofertas) == 0:
        acoes.append(
            {
                "Prioridade": "Alta",
                "Ação": "Criar uma oferta paga simples",
                "Motivo": "Sem oferta clara, não dá para validar venda.",
            }
        )

    if len(crm) == 0:
        acoes.append(
            {
                "Prioridade": "Alta",
                "Ação": "Cadastrar leads no CRM Beta",
                "Motivo": "Todo lead precisa de próxima ação e follow-up.",
            }
        )

    sprints_abertas = _contar(sprints, "status_sprint", "Em desenvolvimento") + _contar(
        sprints,
        "status_sprint",
        "Em teste",
    )

    if sprints_abertas > 0:
        acoes.append(
            {
                "Prioridade": "Alta",
                "Ação": "Finalizar ou testar sprints abertas",
                "Motivo": "Execução precisa virar aprendizado real.",
            }
        )

    if scores["geral"] >= 70 and scores["comercial"] >= 60:
        acoes.append(
            {
                "Prioridade": "Alta",
                "Ação": "Preparar beta pago controlado",
                "Motivo": "Já existe sinal suficiente para testar monetização com poucos usuários.",
            }
        )

    if len(acoes) == 0:
        acoes.append(
            {
                "Prioridade": "Média",
                "Ação": "Manter ciclo semanal de melhoria",
                "Motivo": "Continuar rodando teste, prioridade, sprint e follow-up.",
            }
        )

    return acoes


def _gerar_mapa_fase_3(scores: Dict[str, int]) -> List[Dict[str, str]]:
    return [
        {
            "Condição": "Score geral ≥ 70",
            "Status": "OK" if scores["geral"] >= 70 else "Pendente",
            "Por quê": "Mostra maturidade mínima da Fase 2.",
        },
        {
            "Condição": "Score comercial ≥ 60",
            "Status": "OK" if scores["comercial"] >= 60 else "Pendente",
            "Por quê": "Indica que há sinal de pagamento, oferta ou leads.",
        },
        {
            "Condição": "Score execução ≥ 50",
            "Status": "OK" if scores["execucao"] >= 50 else "Pendente",
            "Por quê": "Mostra capacidade de transformar feedback em melhoria.",
        },
        {
            "Condição": "Score validação ≥ 60",
            "Status": "OK" if scores["validacao"] >= 60 else "Pendente",
            "Por quê": "Indica que usuários reais já testaram e geraram aprendizado.",
        },
    ]


def _gerar_relatorio_markdown(
    dados: Dict[str, List[Dict[str, str]]],
    scores: Dict[str, int],
) -> str:
    classificacao = _classificar_fase_2(scores["geral"])
    decisao = _decisao_recomendada(dados, scores)

    linhas_resumo = "\n".join(
        [
            f"| {linha['Área']} | {linha['Registros']} | {linha['Indicador-chave']} | {linha['Leitura']} |"
            for linha in _gerar_tabela_resumo(dados)
        ]
    )

    linhas_alertas = "\n".join([f"- {alerta}" for alerta in _gerar_alertas(dados, scores)])

    linhas_acoes = "\n".join(
        [
            f"| {acao['Prioridade']} | {acao['Ação']} | {acao['Motivo']} |"
            for acao in _gerar_proximas_acoes(dados, scores)
        ]
    )

    linhas_mapa = "\n".join(
        [
            f"| {item['Condição']} | {item['Status']} | {item['Por quê']} |"
            for item in _gerar_mapa_fase_3(scores)
        ]
    )

    return f"""# Painel Mestre Beta — Máquina de Preço-Teto

Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Score da Fase 2

**Score geral:** {scores["geral"]}/100  
**Score de validação:** {scores["validacao"]}/100  
**Score comercial:** {scores["comercial"]}/100  
**Score de execução:** {scores["execucao"]}/100  

**Classificação:** {classificacao}  
**Decisão recomendada:** {decisao}

## Resumo das áreas

| Área | Registros | Indicador-chave | Leitura |
|---|---:|---|---|
{linhas_resumo}

## Alertas

{linhas_alertas}

## Próximas ações

| Prioridade | Ação | Motivo |
|---|---|---|
{linhas_acoes}

## Mapa de avanço para Fase 3

| Condição | Status | Por quê |
|---|---|---|
{linhas_mapa}

## Regra

A Fase 3 só deve começar quando validação, execução e sinal comercial estiverem minimamente sustentados por dados reais.
"""


def _injetar_css_painel_beta() -> None:
    st.markdown(
        """
        <style>
            .pb-hero {
                padding: 1.75rem 1.8rem;
                border-radius: 30px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    radial-gradient(circle at top left, rgba(214, 181, 109, 0.25), transparent 30%),
                    radial-gradient(circle at bottom right, rgba(74, 144, 226, 0.22), transparent 34%),
                    linear-gradient(135deg, rgba(8, 15, 27, 0.99), rgba(5, 9, 18, 0.99));
                box-shadow: 0 18px 55px rgba(0, 0, 0, 0.34);
                margin-bottom: 1.25rem;
            }

            .pb-eyebrow {
                color: #d6b56d;
                font-size: 0.78rem;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.35rem;
            }

            .pb-title {
                color: #f4f7fb;
                font-size: 2.1rem;
                font-weight: 900;
                margin-bottom: 0.45rem;
                line-height: 1.14;
            }

            .pb-subtitle {
                color: rgba(244, 247, 251, 0.76);
                font-size: 1rem;
                line-height: 1.62;
                max-width: 1080px;
            }

            .pb-card {
                padding: 1.1rem 1.15rem;
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.035);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.18);
                height: 100%;
            }

            .pb-card-label {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .pb-card-value {
                color: #f4f7fb;
                font-size: 1.25rem;
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .pb-card-note {
                color: rgba(244, 247, 251, 0.68);
                font-size: 0.87rem;
                line-height: 1.47;
            }

            .pb-highlight {
                padding: 0.95rem 1rem;
                border-radius: 16px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.92rem;
                line-height: 1.55;
                margin-bottom: 0.7rem;
            }

            .pb-disclaimer {
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
        <div class="pb-card">
            <div class="pb-card-label">{label}</div>
            <div class="pb-card-value">{value}</div>
            <div class="pb-card-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def renderizar_painel_beta() -> None:
    """
    Renderiza o painel mestre da Fase 2 beta.
    """
    _injetar_css_painel_beta()

    dados = _carregar_dados_fase_2()
    scores = _calcular_score_geral_fase_2(dados)

    classificacao = _classificar_fase_2(scores["geral"])
    decisao = _decisao_recomendada(dados, scores)

    receita_pre_venda = _calcular_receita_ponderada_pre_venda(dados["pre_venda_beta"])
    receita_crm = _calcular_receita_ponderada_crm(dados["crm_beta"])
    receita_total = receita_pre_venda + receita_crm

    st.session_state["resultado_painel_beta"] = {
        "score_geral_fase_2": scores["geral"],
        "score_validacao": scores["validacao"],
        "score_comercial": scores["comercial"],
        "score_execucao": scores["execucao"],
        "classificacao": classificacao,
        "decisao_recomendada": decisao,
        "receita_ponderada_total": receita_total,
    }

    st.markdown(
        """
        <div class="pb-hero">
            <div class="pb-eyebrow">Fase 2.8 — Painel mestre beta</div>
            <div class="pb-title">Painel Beta e Decisão de Avanço para Fase 3</div>
            <div class="pb-subtitle">
                Consolide validação, execução e sinal comercial em uma visão única.
                Use este painel para decidir se o produto continua em beta, vende manualmente ou prepara a Fase 3.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="pb-highlight">
            A pergunta principal não é “o app está ficando grande?”. A pergunta é:
            existe aprendizado real, execução disciplinada e sinal comercial suficiente?
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Score geral da Fase 2")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Score geral", f"{scores['geral']}/100")

    with col_2:
        st.metric("Validação", f"{scores['validacao']}/100")

    with col_3:
        st.metric("Comercial", f"{scores['comercial']}/100")

    with col_4:
        st.metric("Execução", f"{scores['execucao']}/100")

    st.progress(scores["geral"] / 100)

    if scores["geral"] >= 70:
        st.success(f"{classificacao}. Decisão: {decisao}.")
    elif scores["geral"] >= 45:
        st.warning(f"{classificacao}. Decisão: {decisao}.")
    else:
        st.error(f"{classificacao}. Decisão: {decisao}.")

    st.divider()

    st.markdown("### Indicadores consolidados")

    col_a, col_b, col_c, col_d = st.columns(4)

    with col_a:
        _card(
            "Testes reais",
            str(len(dados["aprendizado_beta"])),
            "Registros no Aprendizado Beta.",
        )

    with col_b:
        _card(
            "Pré-vendas",
            str(len(dados["pre_venda_beta"])),
            "Conversas comerciais registradas.",
        )

    with col_c:
        _card(
            "Leads no CRM",
            str(len(dados["crm_beta"])),
            "Pipeline comercial manual.",
        )

    with col_d:
        _card(
            "Receita ponderada",
            _fmt_moeda(receita_total),
            "Pré-venda + CRM ponderados.",
        )

    st.divider()

    st.markdown("### Resumo por área")

    st.dataframe(
        _gerar_tabela_resumo(dados),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Alertas estratégicos")

    for alerta in _gerar_alertas(dados, scores):
        st.markdown(f"- {alerta}")

    st.divider()

    st.markdown("### Próximas ações recomendadas")

    st.dataframe(
        _gerar_proximas_acoes(dados, scores),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Mapa de avanço para Fase 3")

    st.dataframe(
        _gerar_mapa_fase_3(scores),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Leitura executiva")

    st.info(
        f"""
        **Classificação atual:** {classificacao}  

        **Decisão recomendada:** {decisao}  

        **Interpretação:** a Fase 2 deve provar três coisas ao mesmo tempo:
        1. usuários reais entendem e usam;
        2. feedback vira melhoria executada;
        3. existe algum sinal comercial concreto.
        """
    )

    st.divider()

    st.download_button(
        label="Baixar relatório mestre beta (.md)",
        data=_gerar_relatorio_markdown(dados, scores),
        file_name="relatorio_painel_mestre_beta.md",
        mime="text/markdown",
        key="download_painel_beta_md",
    )

    st.markdown(
        """
        <div class="pb-disclaimer">
            <strong>Regra de avanço:</strong> não avance para uma Fase 3 mais complexa apenas porque o app ficou maior.
            Avance quando houver validação real, execução disciplinada e sinal comercial mínimo.
        </div>
        """,
        unsafe_allow_html=True,
    )