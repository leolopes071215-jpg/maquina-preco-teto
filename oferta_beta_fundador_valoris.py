# oferta_beta_fundador_valoris.py

from __future__ import annotations

import csv
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

import streamlit as st

from beta_publico_valoris import calcular_saude_beta_publico, carregar_leads_beta_publico
from onboarding_premium_valoris import calcular_saude_onboarding_premium
from beta_insights_valoris import calcular_saude_beta_insights
from beta_feedback_valoris import calcular_saude_beta_feedback
from demo_guiada_2min_valoris import calcular_demo_2min_valoris
from analise_premium_valoris import calcular_saude_analise_premium
from launch_readiness_valoris import calcular_saude_launch_readiness


VERSAO_OFERTA_BETA_FUNDADOR_VALORIS = "3.8.82"

CAMINHO_INTERESSES_OFERTA_BETA = Path("interesses_oferta_beta_fundador_valoris.csv")
CAMINHO_DECISOES_OFERTA_BETA = Path("decisoes_oferta_beta_fundador_valoris.csv")
CAMINHO_MANIFESTO_OFERTA_BETA = Path("manifesto_oferta_beta_fundador_valoris.json")
CAMINHO_COPY_OFERTA_BETA_MD = Path("COPY_OFERTA_BETA_FUNDADOR_VALORIS.md")
CAMINHO_PAGINA_OFERTA_BETA_MD = Path("PAGINA_OFERTA_BETA_FUNDADOR_VALORIS.md")
CAMINHO_CHECKLIST_OFERTA_BETA_MD = Path("CHECKLIST_OFERTA_BETA_FUNDADOR_VALORIS.md")
CAMINHO_EXPERIMENTO_PRECO_BETA_MD = Path("EXPERIMENTO_PRECO_BETA_FUNDADOR_VALORIS.md")

CAMPOS_INTERESSES_OFERTA = [
    "id",
    "data_registro",
    "nome",
    "email",
    "perfil",
    "plano_interesse",
    "valor_aceitavel",
    "principal_motivo",
    "principal_objecao",
    "aceita_contato",
    "origem",
    "status",
]

CAMPOS_DECISAO_OFERTA = [
    "id",
    "data_registro",
    "score_oferta",
    "score_precificacao",
    "score_copy",
    "score_produto",
    "score_validacao",
    "interesses_total",
    "ticket_medio_indicado",
    "plano_prioritario",
    "risco",
    "decisao",
    "proximo_passo",
    "observacoes",
]

PLANOS_BETA_FUNDADOR = [
    {
        "plano": "Beta Fundador Essencial",
        "preco_mensal": 29,
        "preco_anual": 290,
        "publico": "Investidor iniciante/intermediário que quer método e clareza.",
        "entrega": [
            "Análise premium com preço teto e margem de segurança",
            "Tese explicada em linguagem simples",
            "Relatório exportável",
            "Acesso ao beta fechado",
        ],
        "limite": "Até 20 análises/mês no beta",
        "posicionamento": "Entrada acessível para validar disposição real de pagamento.",
    },
    {
        "plano": "Beta Fundador Pro",
        "preco_mensal": 59,
        "preco_anual": 590,
        "publico": "Investidor que compara empresas e quer acompanhar oportunidades.",
        "entrega": [
            "Tudo do Essencial",
            "Comparação inicial entre empresas",
            "Watchlist local",
            "Prioridade em novas features",
        ],
        "limite": "Até 80 análises/mês no beta",
        "posicionamento": "Plano principal para validar valor percebido e recorrência.",
    },
    {
        "plano": "Beta Fundador Elite",
        "preco_mensal": 97,
        "preco_anual": 970,
        "publico": "Usuário avançado, criador de conteúdo ou estudante sério de valuation.",
        "entrega": [
            "Tudo do Pro",
            "Relatórios premium avançados",
            "Participação em calls/feedback de produto",
            "Influência direta no roadmap",
        ],
        "limite": "Uso ampliado durante o beta",
        "posicionamento": "Teste de teto de preço sem depender dele para validar o produto.",
    },
]

COPY_OFERTA_BETA = {
    "headline": "Entre como fundador da Valoris e ajude a construir uma análise de ações mais racional.",
    "subheadline": "Acesso beta com preço fundador, foco em preço teto, margem de segurança, tese, riscos e relatório.",
    "promessa": "Uma ferramenta para organizar seu processo de análise fundamentalista sem transformar investimento em chute.",
    "cta_principal": "Quero entrar como fundador",
    "cta_secundario": "Quero ver a demo primeiro",
    "garantia_prudente": "Durante o beta, o foco é validação e evolução do produto. A oferta pode ser pausada ou ajustada conforme feedback.",
    "disclaimer": "Ferramenta educacional. Não é recomendação personalizada de investimento. Não há promessa de rentabilidade.",
}

BLOCOS_PAGINA_OFERTA = [
    {
        "bloco": "Problema",
        "titulo": "Investir sem método custa caro.",
        "texto": "A maior parte dos erros nasce antes da compra: premissas ruins, preço sem margem e tese mal entendida.",
    },
    {
        "bloco": "Mecanismo",
        "titulo": "A Valoris força uma análise estruturada.",
        "texto": "Você vê preço teto, margem de segurança, qualidade, risco, tese e próximo passo em uma experiência guiada.",
    },
    {
        "bloco": "Produto",
        "titulo": "Mais que calculadora: uma decisão explicada.",
        "texto": "A Valoris entrega raciocínio, relatório e clareza para você estudar melhor as empresas.",
    },
    {
        "bloco": "Oferta",
        "titulo": "Preço fundador para os primeiros beta testers.",
        "texto": "Os primeiros usuários ajudam a moldar o produto e recebem condições especiais enquanto o beta evolui.",
    },
    {
        "bloco": "Segurança",
        "titulo": "Sem promessa de lucro. Sem recomendação disfarçada.",
        "texto": "A ferramenta é educacional e transparente. O objetivo é melhorar o processo de análise.",
    },
]

OBJECOES_OFERTA = [
    {
        "objecao": "Por que eu pagaria se ainda é beta?",
        "resposta": "Porque o preço fundador compra acesso antecipado, influência no roadmap e uma ferramenta que já entrega análise, tese e relatório.",
    },
    {
        "objecao": "Isso substitui um analista?",
        "resposta": "Não. A Valoris organiza premissas e raciocínio. Ela ajuda no estudo, mas não substitui julgamento, leitura de balanços e responsabilidade individual.",
    },
    {
        "objecao": "E se os dados ainda forem manuais?",
        "resposta": "O beta prioriza método, clareza e relatório. Dados automáticos entram depois de validar a experiência central.",
    },
    {
        "objecao": "Isso recomenda compra ou venda?",
        "resposta": "Não. A decisão é educacional e baseada nas premissas inseridas. Não é recomendação personalizada.",
    },
]

CHECKLIST_OFERTA = [
    "Oferta sem promessa de lucro",
    "Disclaimer educacional visível",
    "Preço fundador limitado",
    "Benefício claro para beta tester",
    "Planos simples",
    "CTA principal direto",
    "Objeções respondidas",
    "Experimento de preço definido",
    "Critério de validação objetivo",
]


def _limpar_texto(valor: Any) -> str:
    if valor is None:
        return ""
    return str(valor).strip()


def _email_valido(email: str) -> bool:
    email = _limpar_texto(email).lower()
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))


def _to_float(valor: Any, padrao: float = 0.0) -> float:
    try:
        if isinstance(valor, str):
            valor = valor.replace("R$", "").replace(".", "").replace(",", ".").strip()
        return float(valor)
    except Exception:
        return padrao


def _garantir_csv(caminho: Path, campos: List[str]) -> None:
    if caminho.exists():
        return
    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()


def carregar_interesses_oferta_beta() -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_INTERESSES_OFERTA_BETA, CAMPOS_INTERESSES_OFERTA)
    with CAMINHO_INTERESSES_OFERTA_BETA.open("r", newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def carregar_decisoes_oferta_beta() -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_DECISOES_OFERTA_BETA, CAMPOS_DECISAO_OFERTA)
    with CAMINHO_DECISOES_OFERTA_BETA.open("r", newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def gerar_csv_interesses_oferta_beta() -> str:
    _garantir_csv(CAMINHO_INTERESSES_OFERTA_BETA, CAMPOS_INTERESSES_OFERTA)
    return CAMINHO_INTERESSES_OFERTA_BETA.read_text(encoding="utf-8")


def gerar_csv_decisoes_oferta_beta() -> str:
    _garantir_csv(CAMINHO_DECISOES_OFERTA_BETA, CAMPOS_DECISAO_OFERTA)
    return CAMINHO_DECISOES_OFERTA_BETA.read_text(encoding="utf-8")


def salvar_interesse_oferta_beta(dados: Dict[str, Any]) -> Dict[str, str]:
    _garantir_csv(CAMINHO_INTERESSES_OFERTA_BETA, CAMPOS_INTERESSES_OFERTA)

    registro = {
        "id": str(uuid4())[:8],
        "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "nome": _limpar_texto(dados.get("nome")),
        "email": _limpar_texto(dados.get("email")).lower(),
        "perfil": _limpar_texto(dados.get("perfil")),
        "plano_interesse": _limpar_texto(dados.get("plano_interesse")),
        "valor_aceitavel": str(_to_float(dados.get("valor_aceitavel"), 0.0)),
        "principal_motivo": _limpar_texto(dados.get("principal_motivo")),
        "principal_objecao": _limpar_texto(dados.get("principal_objecao")),
        "aceita_contato": str(bool(dados.get("aceita_contato"))),
        "origem": _limpar_texto(dados.get("origem", "oferta_beta_fundador")),
        "status": _limpar_texto(dados.get("status", "novo")),
    }

    with CAMINHO_INTERESSES_OFERTA_BETA.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_INTERESSES_OFERTA)
        escritor.writerow(registro)

    return registro


def gerar_interesse_exemplo_oferta_beta() -> Dict[str, str]:
    return salvar_interesse_oferta_beta(
        {
            "nome": "Interessado Fundador Exemplo",
            "email": f"fundador.beta.{datetime.now().strftime('%H%M%S')}@exemplo.com",
            "perfil": "Investidor intermediário",
            "plano_interesse": "Beta Fundador Pro",
            "valor_aceitavel": 59,
            "principal_motivo": "Quero uma ferramenta que una preço teto, tese e relatório.",
            "principal_objecao": "Quero saber se os dados ficarão automáticos depois.",
            "aceita_contato": True,
            "origem": "terminal_demo",
            "status": "novo",
        }
    )


def _plano_por_nome(nome: str) -> Dict[str, Any]:
    for plano in PLANOS_BETA_FUNDADOR:
        if plano["plano"] == nome:
            return plano
    return PLANOS_BETA_FUNDADOR[1]


def calcular_metricas_interesse_oferta() -> Dict[str, Any]:
    interesses = carregar_interesses_oferta_beta()
    total = len(interesses)

    emails_validos = sum(1 for item in interesses if _email_valido(item.get("email", "")))
    aceites = sum(1 for item in interesses if str(item.get("aceita_contato", "")).lower() == "true")
    valores = [_to_float(item.get("valor_aceitavel"), 0.0) for item in interesses if _to_float(item.get("valor_aceitavel"), 0.0) > 0]

    contador_planos: Dict[str, int] = {}
    for item in interesses:
        plano = item.get("plano_interesse", "não informado")
        contador_planos[plano] = contador_planos.get(plano, 0) + 1

    plano_prioritario = ""
    if contador_planos:
        plano_prioritario = sorted(contador_planos.items(), key=lambda par: par[1], reverse=True)[0][0]

    ticket_medio = round(sum(valores) / len(valores), 2) if valores else 0.0

    return {
        "interesses_total": total,
        "emails_validos": emails_validos,
        "taxa_email_valido": round((emails_validos / total) * 100, 2) if total else 0,
        "aceites_contato": aceites,
        "taxa_aceite_contato": round((aceites / total) * 100, 2) if total else 0,
        "ticket_medio_indicado": ticket_medio,
        "plano_prioritario": plano_prioritario,
        "distribuicao_planos": contador_planos,
        "ultimos_interesses": interesses[-20:],
    }


def calcular_saude_oferta_beta_fundador() -> Dict[str, Any]:
    metricas = calcular_metricas_interesse_oferta()

    try:
        beta_publico = calcular_saude_beta_publico()
    except Exception as erro:
        beta_publico = {"score_beta_publico": 0, "leads_total": 0, "erro": str(erro)}

    try:
        onboarding = calcular_saude_onboarding_premium()
    except Exception as erro:
        onboarding = {"score_onboarding": 0, "erro": str(erro)}

    try:
        insights = calcular_saude_beta_insights()
    except Exception as erro:
        insights = {"score_insights": 0, "erro": str(erro)}

    try:
        beta_feedback = calcular_saude_beta_feedback()
    except Exception as erro:
        beta_feedback = {"score_beta": 0, "erro": str(erro)}

    try:
        demo = calcular_demo_2min_valoris()
    except Exception as erro:
        demo = {"score_demo": 0, "erro": str(erro)}

    try:
        premium = calcular_saude_analise_premium()
    except Exception as erro:
        premium = {"score_produto_premium": 0, "erro": str(erro)}

    try:
        launch = calcular_saude_launch_readiness()
    except Exception as erro:
        launch = {"score_launch": 0, "erro": str(erro)}

    score_copy = 0
    score_copy += 16 if "fundador" in COPY_OFERTA_BETA["headline"].lower() else 0
    score_copy += 16 if "preço fundador" in COPY_OFERTA_BETA["subheadline"].lower() else 0
    score_copy += 16 if "margem de segurança" in COPY_OFERTA_BETA["subheadline"].lower() else 0
    score_copy += 16 if "educacional" in COPY_OFERTA_BETA["disclaimer"].lower() else 0
    score_copy += 16 if len(OBJECOES_OFERTA) >= 4 else 0
    score_copy += 20 if len(BLOCOS_PAGINA_OFERTA) >= 5 else 0
    score_copy = min(100, score_copy)

    score_precificacao = 0
    precos = [plano["preco_mensal"] for plano in PLANOS_BETA_FUNDADOR]
    score_precificacao += 20 if min(precos) <= 39 else 0
    score_precificacao += 20 if max(precos) >= 79 else 0
    score_precificacao += 18 if len(PLANOS_BETA_FUNDADOR) == 3 else 0
    score_precificacao += 18 if metricas["ticket_medio_indicado"] >= 29 else 0
    score_precificacao += 14 if metricas["interesses_total"] >= 1 else 0
    score_precificacao += 10 if metricas["plano_prioritario"] else 0
    score_precificacao = min(100, score_precificacao)

    score_produto = int(round(
        int(beta_publico.get("score_beta_publico", 0) or 0) * 0.24
        + int(onboarding.get("score_onboarding", 0) or 0) * 0.20
        + int(insights.get("score_insights", 0) or 0) * 0.16
        + int(demo.get("score_demo", 0) or 0) * 0.14
        + int(premium.get("score_produto_premium", 0) or 0) * 0.16
        + int(launch.get("score_launch", 0) or 0) * 0.10
    ))

    score_validacao = int(beta_feedback.get("score_beta", 0) or 0)
    if metricas["interesses_total"] >= 5:
        score_validacao = min(100, score_validacao + 18)
    elif metricas["interesses_total"] >= 3:
        score_validacao = min(100, score_validacao + 12)
    elif metricas["interesses_total"] >= 1:
        score_validacao = min(100, score_validacao + 6)

    score_oferta = int(round(
        score_precificacao * 0.26
        + score_copy * 0.24
        + score_produto * 0.28
        + score_validacao * 0.22
    ))

    interesses_total = metricas["interesses_total"]

    if interesses_total < 3:
        risco = "Médio"
        decisao = "Oferta estruturada, mas ainda sem validação comercial suficiente"
        proximo_passo = "Apresentar a oferta para 3 a 5 leads beta e medir interesse real por preço."
    elif score_oferta >= 84 and metricas["ticket_medio_indicado"] >= 39:
        risco = "Médio controlado"
        decisao = "Oferta beta fundador pronta para teste controlado de pagamento"
        proximo_passo = "Criar checkout/teste manual para poucos fundadores e validar conversão real."
    elif score_oferta >= 70:
        risco = "Médio"
        decisao = "Oferta promissora, mas preço ou copy precisam ajuste"
        proximo_passo = "Testar duas versões de preço e reforçar a prova de valor antes de escalar."
    else:
        risco = "Alto"
        decisao = "Não cobrar ainda"
        proximo_passo = "Melhorar produto percebido, onboarding e sinal de disposição de pagamento."

    return {
        "versao": VERSAO_OFERTA_BETA_FUNDADOR_VALORIS,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score_oferta": max(0, min(100, score_oferta)),
        "score_precificacao": score_precificacao,
        "score_copy": score_copy,
        "score_produto": score_produto,
        "score_validacao": score_validacao,
        "interesses_total": interesses_total,
        "ticket_medio_indicado": metricas["ticket_medio_indicado"],
        "plano_prioritario": metricas["plano_prioritario"],
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo_passo,
        "metricas_interesse": metricas,
        "planos": PLANOS_BETA_FUNDADOR,
        "copy": COPY_OFERTA_BETA,
        "blocos_pagina": BLOCOS_PAGINA_OFERTA,
        "objecoes": OBJECOES_OFERTA,
        "checklist": CHECKLIST_OFERTA,
        "beta_publico": beta_publico,
        "onboarding": onboarding,
        "insights": insights,
        "beta_feedback": beta_feedback,
        "demo": demo,
        "premium": premium,
        "launch": launch,
    }


def salvar_decisao_oferta_beta_fundador(saude: Dict[str, Any], observacoes: str = "") -> Dict[str, str]:
    _garantir_csv(CAMINHO_DECISOES_OFERTA_BETA, CAMPOS_DECISAO_OFERTA)

    registro = {
        "id": str(uuid4())[:8],
        "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score_oferta": str(saude.get("score_oferta", "")),
        "score_precificacao": str(saude.get("score_precificacao", "")),
        "score_copy": str(saude.get("score_copy", "")),
        "score_produto": str(saude.get("score_produto", "")),
        "score_validacao": str(saude.get("score_validacao", "")),
        "interesses_total": str(saude.get("interesses_total", "")),
        "ticket_medio_indicado": str(saude.get("ticket_medio_indicado", "")),
        "plano_prioritario": _limpar_texto(saude.get("plano_prioritario")),
        "risco": _limpar_texto(saude.get("risco")),
        "decisao": _limpar_texto(saude.get("decisao")),
        "proximo_passo": _limpar_texto(saude.get("proximo_passo")),
        "observacoes": _limpar_texto(observacoes),
    }

    with CAMINHO_DECISOES_OFERTA_BETA.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISAO_OFERTA)
        escritor.writerow(registro)

    return registro


def gerar_copy_oferta_beta_markdown(saude: Dict[str, Any] | None = None) -> str:
    if saude is None:
        saude = calcular_saude_oferta_beta_fundador()

    planos = "\n\n".join(
        [
            f"""### {plano['plano']}

Preço mensal: R$ {plano['preco_mensal']}  
Preço anual: R$ {plano['preco_anual']}  
Público: {plano['publico']}  
Limite: {plano['limite']}  
Posicionamento: {plano['posicionamento']}

Entregas:
{chr(10).join([f"- {item}" for item in plano['entrega']])}
"""
            for plano in PLANOS_BETA_FUNDADOR
        ]
    )

    objecoes = "\n".join(
        [
            f"- **{item['objecao']}** {item['resposta']}"
            for item in OBJECOES_OFERTA
        ]
    )

    return f"""# Copy Oferta Beta Fundador — Valoris

Versão: {VERSAO_OFERTA_BETA_FUNDADOR_VALORIS}  
Gerado em: {saude["gerado_em"]}

## Headline

{COPY_OFERTA_BETA["headline"]}

## Subheadline

{COPY_OFERTA_BETA["subheadline"]}

## Promessa

{COPY_OFERTA_BETA["promessa"]}

## CTAs

Principal: {COPY_OFERTA_BETA["cta_principal"]}  
Secundário: {COPY_OFERTA_BETA["cta_secundario"]}

## Planos

{planos}

## Objeções

{objecoes}

## Disclaimer

{COPY_OFERTA_BETA["disclaimer"]}
"""


def gerar_pagina_oferta_beta_markdown(saude: Dict[str, Any] | None = None) -> str:
    if saude is None:
        saude = calcular_saude_oferta_beta_fundador()

    blocos = "\n\n".join(
        [
            f"""## {item['titulo']}

{item['texto']}
"""
            for item in BLOCOS_PAGINA_OFERTA
        ]
    )

    planos = "\n".join(
        [
            f"- **{plano['plano']}** — R$ {plano['preco_mensal']}/mês ou R$ {plano['preco_anual']}/ano. {plano['posicionamento']}"
            for plano in PLANOS_BETA_FUNDADOR
        ]
    )

    return f"""# Página Oferta Beta Fundador — Valoris

Versão: {VERSAO_OFERTA_BETA_FUNDADOR_VALORIS}  
Gerado em: {saude["gerado_em"]}

# {COPY_OFERTA_BETA["headline"]}

{COPY_OFERTA_BETA["subheadline"]}

**CTA:** {COPY_OFERTA_BETA["cta_principal"]}

{blocos}

## Planos fundadores

{planos}

## Formulário de interesse

- Nome
- E-mail
- Perfil
- Plano de interesse
- Valor aceitável
- Principal motivo
- Principal objeção
- Aceite de contato

## Aviso

{COPY_OFERTA_BETA["disclaimer"]}
"""


def gerar_checklist_oferta_beta_markdown(saude: Dict[str, Any] | None = None) -> str:
    if saude is None:
        saude = calcular_saude_oferta_beta_fundador()

    checklist = "\n".join([f"- [x] {item}" for item in CHECKLIST_OFERTA])

    return f"""# Checklist Oferta Beta Fundador — Valoris

Versão: {VERSAO_OFERTA_BETA_FUNDADOR_VALORIS}  
Gerado em: {saude["gerado_em"]}

## Status

Score Oferta: {saude["score_oferta"]}/100  
Interesses: {saude["interesses_total"]}  
Ticket médio indicado: R$ {saude["ticket_medio_indicado"]}  
Plano prioritário: {saude["plano_prioritario"] or "pendente"}  
Decisão: {saude["decisao"]}

## Checklist

{checklist}

## Próxima ação

{saude["proximo_passo"]}
"""


def gerar_experimento_preco_beta_markdown(saude: Dict[str, Any] | None = None) -> str:
    if saude is None:
        saude = calcular_saude_oferta_beta_fundador()

    return f"""# Experimento de Preço — Beta Fundador Valoris

Versão: {VERSAO_OFERTA_BETA_FUNDADOR_VALORIS}  
Gerado em: {saude["gerado_em"]}

## Hipótese

Usuários que entendem o valor da análise premium aceitam pagar entre R$ 29 e R$ 59/mês para ter acesso beta fundador.

## Amostra inicial

3 a 5 leads qualificados.

## Critério de validação

- Pelo menos 3 interessados reais.
- Pelo menos 1 pessoa aceitar pagar ou demonstrar forte intenção.
- Ticket médio indicado acima de R$ 39.
- Objeções principais mapeadas.

## Planos testados

- Essencial: R$ 29/mês.
- Pro: R$ 59/mês.
- Elite: R$ 97/mês.

## Decisão atual

{saude["decisao"]}

## Próximo passo

{saude["proximo_passo"]}
"""


def salvar_copy_oferta_beta_markdown() -> Dict[str, Any]:
    saude = calcular_saude_oferta_beta_fundador()
    CAMINHO_COPY_OFERTA_BETA_MD.write_text(gerar_copy_oferta_beta_markdown(saude), encoding="utf-8")
    return {"ok": True, "arquivo": str(CAMINHO_COPY_OFERTA_BETA_MD), "score_oferta": saude["score_oferta"]}


def salvar_pagina_oferta_beta_markdown() -> Dict[str, Any]:
    saude = calcular_saude_oferta_beta_fundador()
    CAMINHO_PAGINA_OFERTA_BETA_MD.write_text(gerar_pagina_oferta_beta_markdown(saude), encoding="utf-8")
    return {"ok": True, "arquivo": str(CAMINHO_PAGINA_OFERTA_BETA_MD), "score_oferta": saude["score_oferta"]}


def salvar_checklist_oferta_beta_markdown() -> Dict[str, Any]:
    saude = calcular_saude_oferta_beta_fundador()
    CAMINHO_CHECKLIST_OFERTA_BETA_MD.write_text(gerar_checklist_oferta_beta_markdown(saude), encoding="utf-8")
    return {"ok": True, "arquivo": str(CAMINHO_CHECKLIST_OFERTA_BETA_MD), "score_oferta": saude["score_oferta"]}


def salvar_experimento_preco_beta_markdown() -> Dict[str, Any]:
    saude = calcular_saude_oferta_beta_fundador()
    CAMINHO_EXPERIMENTO_PRECO_BETA_MD.write_text(gerar_experimento_preco_beta_markdown(saude), encoding="utf-8")
    return {"ok": True, "arquivo": str(CAMINHO_EXPERIMENTO_PRECO_BETA_MD), "score_oferta": saude["score_oferta"]}


def gerar_manifesto_oferta_beta_fundador() -> Dict[str, Any]:
    saude = calcular_saude_oferta_beta_fundador()
    manifesto = {
        "versao": VERSAO_OFERTA_BETA_FUNDADOR_VALORIS,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "saude": saude,
        "planos": PLANOS_BETA_FUNDADOR,
        "copy": COPY_OFERTA_BETA,
        "blocos_pagina": BLOCOS_PAGINA_OFERTA,
        "objecoes": OBJECOES_OFERTA,
        "estrategia": {
            "objetivo": "Validar disposição real de pagamento antes de escalar a Valoris.",
            "proxima_versao": "Checkout manual/controle de fundadores ou Relatório Premium v2.",
            "regra": "Só escalar oferta após sinal mínimo de pagamento real.",
        },
    }
    CAMINHO_MANIFESTO_OFERTA_BETA.write_text(json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifesto


def _injetar_css_oferta_beta() -> None:
    st.markdown(
        """
        <style>
            .oferta-beta-hero {
                padding: clamp(1.2rem, 3vw, 2.1rem);
                border-radius: 30px;
                border: 1px solid rgba(255, 255, 255, 0.09);
                background:
                    radial-gradient(circle at top left, rgba(214, 181, 109, 0.24), transparent 32%),
                    radial-gradient(circle at bottom right, rgba(80, 170, 140, 0.22), transparent 36%),
                    linear-gradient(135deg, rgba(6, 12, 23, 0.99), rgba(4, 8, 16, 0.99));
                box-shadow: 0 20px 62px rgba(0, 0, 0, 0.34);
                margin-bottom: 1rem;
            }
            .oferta-beta-eyebrow {
                color: #d6b56d;
                font-size: 0.74rem;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                font-weight: 880;
                margin-bottom: 0.35rem;
            }
            .oferta-beta-title {
                color: #f4f7fb;
                font-size: clamp(1.8rem, 5.5vw, 3.25rem);
                font-weight: 950;
                line-height: 1.02;
                letter-spacing: -0.058em;
                margin-bottom: 0.55rem;
            }
            .oferta-beta-subtitle {
                color: rgba(244, 247, 251, 0.75);
                font-size: clamp(0.94rem, 2.2vw, 1.06rem);
                line-height: 1.56;
                max-width: 1050px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def renderizar_oferta_beta_fundador_valoris() -> None:
    _injetar_css_oferta_beta()

    st.markdown(
        f"""
        <div class="oferta-beta-hero">
            <div class="oferta-beta-eyebrow">Valoris • Oferta Beta Fundador • v{VERSAO_OFERTA_BETA_FUNDADOR_VALORIS}</div>
            <div class="oferta-beta-title">Validação comercial antes de escalar.</div>
            <div class="oferta-beta-subtitle">
                Estruture preço fundador, copy, planos, objeções e experimento para medir disposição real de pagamento.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    saude = calcular_saude_oferta_beta_fundador()

    st.markdown("### Diagnóstico da oferta")
    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Score Oferta", f"{saude['score_oferta']}/100")

    with col_2:
        st.metric("Interesses", saude["interesses_total"])

    with col_3:
        st.metric("Ticket indicado", f"R$ {saude['ticket_medio_indicado']}")

    with col_4:
        st.metric("Risco", saude["risco"])

    st.progress(saude["score_oferta"] / 100)

    if saude["score_oferta"] >= 84 and saude["interesses_total"] >= 3:
        st.success(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    elif saude["score_oferta"] >= 70:
        st.warning(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    else:
        st.info(f"**{saude['decisao']}** — {saude['proximo_passo']}")

    st.divider()

    st.markdown("### Copy principal")
    st.subheader(COPY_OFERTA_BETA["headline"])
    st.write(COPY_OFERTA_BETA["subheadline"])
    st.info(COPY_OFERTA_BETA["promessa"])
    st.caption(COPY_OFERTA_BETA["disclaimer"])

    st.markdown("### Planos beta fundador")
    st.dataframe(
        [
            {
                "plano": plano["plano"],
                "preco_mensal": plano["preco_mensal"],
                "preco_anual": plano["preco_anual"],
                "publico": plano["publico"],
                "limite": plano["limite"],
                "posicionamento": plano["posicionamento"],
            }
            for plano in PLANOS_BETA_FUNDADOR
        ],
        width="stretch",
        hide_index=True,
    )

    st.markdown("### Objeções")
    for item in OBJECOES_OFERTA:
        with st.expander(item["objecao"]):
            st.write(item["resposta"])

    st.divider()

    st.markdown("### Registrar interesse na oferta")

    with st.form("form_interesse_oferta_beta"):
        col_a, col_b = st.columns(2)

        with col_a:
            nome = st.text_input("Nome")
            email = st.text_input("E-mail")
            perfil = st.text_input("Perfil", value="Investidor intermediário")
            plano_interesse = st.selectbox("Plano de interesse", [plano["plano"] for plano in PLANOS_BETA_FUNDADOR])

        with col_b:
            valor_aceitavel = st.number_input("Valor mensal aceitável (R$)", min_value=0.0, value=float(_plano_por_nome(plano_interesse)["preco_mensal"]), step=1.0)
            principal_motivo = st.text_area("Principal motivo de interesse", height=90)
            principal_objecao = st.text_area("Principal objeção/dúvida", height=90)
            aceita_contato = st.checkbox("Aceito ser contatado sobre a oferta beta", value=True)

        enviado = st.form_submit_button("Registrar interesse fundador")

        if enviado:
            if not _email_valido(email):
                st.error("E-mail inválido. Revise antes de salvar.")
            else:
                registro = salvar_interesse_oferta_beta(
                    {
                        "nome": nome,
                        "email": email,
                        "perfil": perfil,
                        "plano_interesse": plano_interesse,
                        "valor_aceitavel": valor_aceitavel,
                        "principal_motivo": principal_motivo,
                        "principal_objecao": principal_objecao,
                        "aceita_contato": aceita_contato,
                        "origem": "aba_oferta_beta_fundador",
                        "status": "novo",
                    }
                )
                st.success(f"Interesse salvo: {registro['id']}")
                st.rerun()

    st.divider()

    st.markdown("### Métricas de interesse")
    st.json(saude["metricas_interesse"])

    if saude["metricas_interesse"]["ultimos_interesses"]:
        st.dataframe(saude["metricas_interesse"]["ultimos_interesses"], width="stretch", hide_index=True)

    st.divider()

    col_btn_1, col_btn_2, col_btn_3, col_btn_4 = st.columns(4)

    with col_btn_1:
        if st.button("Gerar interesse exemplo", key="oferta_beta_interesse_exemplo"):
            registro = gerar_interesse_exemplo_oferta_beta()
            st.success(f"Interesse exemplo criado: {registro['id']}")
            st.rerun()

    with col_btn_2:
        if st.button("Gerar manifesto", key="oferta_beta_manifesto"):
            manifesto = gerar_manifesto_oferta_beta_fundador()
            st.success(f"Manifesto gerado: {CAMINHO_MANIFESTO_OFERTA_BETA}")
            st.json({"versao": manifesto["versao"], "score": manifesto["saude"]["score_oferta"]})

    with col_btn_3:
        if st.button("Salvar copy .md", key="oferta_beta_copy"):
            retorno = salvar_copy_oferta_beta_markdown()
            st.success(f"Copy salva: {retorno['arquivo']}")
            st.json(retorno)

    with col_btn_4:
        if st.button("Salvar página .md", key="oferta_beta_pagina"):
            retorno = salvar_pagina_oferta_beta_markdown()
            st.success(f"Página salva: {retorno['arquivo']}")
            st.json(retorno)

    col_btn_5, col_btn_6 = st.columns(2)

    with col_btn_5:
        if st.button("Salvar checklist .md", key="oferta_beta_checklist"):
            retorno = salvar_checklist_oferta_beta_markdown()
            st.success(f"Checklist salvo: {retorno['arquivo']}")
            st.json(retorno)

    with col_btn_6:
        if st.button("Salvar experimento preço .md", key="oferta_beta_experimento"):
            retorno = salvar_experimento_preco_beta_markdown()
            st.success(f"Experimento salvo: {retorno['arquivo']}")
            st.json(retorno)

    if st.button("Salvar decisão Oferta Beta", key="oferta_beta_decisao"):
        registro = salvar_decisao_oferta_beta_fundador(saude, observacoes="Decisão gerada pela oferta beta fundador.")
        st.success(f"Decisão salva: {registro['decisao']}")
        st.rerun()

    st.download_button(
        "Baixar copy oferta beta (.md)",
        data=gerar_copy_oferta_beta_markdown(saude),
        file_name="COPY_OFERTA_BETA_FUNDADOR_VALORIS.md",
        mime="text/markdown",
        key="download_copy_oferta_beta",
    )

    st.download_button(
        "Baixar página oferta beta (.md)",
        data=gerar_pagina_oferta_beta_markdown(saude),
        file_name="PAGINA_OFERTA_BETA_FUNDADOR_VALORIS.md",
        mime="text/markdown",
        key="download_pagina_oferta_beta",
    )

    st.download_button(
        "Baixar interesses oferta beta (.csv)",
        data=gerar_csv_interesses_oferta_beta(),
        file_name="interesses_oferta_beta_fundador_valoris.csv",
        mime="text/csv",
        key="download_interesses_oferta_beta",
    )


def executar_autoteste_oferta_beta_fundador_valoris() -> List[Dict[str, str]]:
    saude = calcular_saude_oferta_beta_fundador()

    return [
        {
            "teste": "versao_oferta_beta_fundador",
            "status": "OK" if VERSAO_OFERTA_BETA_FUNDADOR_VALORIS == "3.8.82" else "FALHA",
            "detalhe": VERSAO_OFERTA_BETA_FUNDADOR_VALORIS,
        },
        {
            "teste": "score_oferta",
            "status": "OK" if 0 <= saude["score_oferta"] <= 100 else "FALHA",
            "detalhe": str(saude["score_oferta"]),
        },
        {
            "teste": "planos",
            "status": "OK" if len(PLANOS_BETA_FUNDADOR) == 3 else "FALHA",
            "detalhe": str(len(PLANOS_BETA_FUNDADOR)),
        },
        {
            "teste": "renderizador",
            "status": "OK" if callable(renderizar_oferta_beta_fundador_valoris) else "FALHA",
            "detalhe": "renderizar_oferta_beta_fundador_valoris",
        },
    ]
