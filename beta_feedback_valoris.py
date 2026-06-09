# beta_feedback_valoris.py

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

import streamlit as st

from demo_guiada_2min_valoris import calcular_demo_2min_valoris
from analise_premium_valoris import calcular_saude_analise_premium
from launch_readiness_valoris import calcular_saude_launch_readiness


VERSAO_BETA_FEEDBACK_VALORIS = "3.8.78"

CAMINHO_BETA_FEEDBACK_CSV = Path("feedback_beta_valoris.csv")
CAMINHO_DECISOES_BETA_FEEDBACK = Path("decisoes_beta_feedback_valoris.csv")
CAMINHO_MANIFESTO_BETA_FEEDBACK = Path("manifesto_beta_feedback_valoris.json")
CAMINHO_ROTEIRO_BETA_MD = Path("ROTEIRO_BETA_TESTER_VALORIS.md")
CAMINHO_FORMULARIO_BETA_MD = Path("FORMULARIO_FEEDBACK_BETA_VALORIS.md")
CAMINHO_PLANO_BETA_MD = Path("PLANO_BETA_FEEDBACK_VALORIS.md")

CAMPOS_FEEDBACK_BETA = [
    "id",
    "data_registro",
    "nome",
    "email",
    "perfil",
    "nivel_investidor",
    "clareza_demo",
    "utilidade_analise",
    "confianca_resultado",
    "facilidade_uso",
    "probabilidade_usar",
    "probabilidade_pagar",
    "preco_justo_mensal",
    "maior_valor",
    "maior_duvida",
    "funcionalidade_mais_importante",
    "observacoes",
]

CAMPOS_DECISAO_BETA = [
    "id",
    "data_registro",
    "score_beta",
    "score_demo",
    "score_premium",
    "score_launch",
    "feedbacks_total",
    "nps_beta_estimado",
    "pronto_para_beta_fechado",
    "risco",
    "decisao",
    "proximo_passo",
    "observacoes",
]

PERFIS_BETA = [
    "Investidor iniciante",
    "Investidor intermediário",
    "Investidor avançado",
    "Estudante de finanças",
    "Criador de conteúdo financeiro",
    "Assessor/analista em formação",
    "Curioso em valuation",
]

NIVEIS_INVESTIDOR = [
    "Ainda não invisto",
    "Invisto há menos de 1 ano",
    "Invisto entre 1 e 3 anos",
    "Invisto há mais de 3 anos",
    "Já faço valuation/análise fundamentalista",
]

PERGUNTAS_FEEDBACK_BETA = [
    {
        "bloco": "Clareza",
        "pergunta": "Em até 2 minutos, você entendeu o que a Valoris faz?",
        "tipo": "nota 0-10",
        "objetivo": "Validar promessa e comunicação.",
    },
    {
        "bloco": "Valor",
        "pergunta": "A análise premium parece útil para decidir estudar/comprar/aguardar uma ação?",
        "tipo": "nota 0-10",
        "objetivo": "Validar valor central do produto.",
    },
    {
        "bloco": "Confiança",
        "pergunta": "A tese, os riscos e a margem de segurança aumentaram sua confiança no processo?",
        "tipo": "nota 0-10",
        "objetivo": "Validar confiança e explicabilidade.",
    },
    {
        "bloco": "Usabilidade",
        "pergunta": "Você conseguiria usar esse fluxo sozinho?",
        "tipo": "nota 0-10",
        "objetivo": "Validar fricção do produto.",
    },
    {
        "bloco": "Pagamento",
        "pergunta": "Você pagaria por uma ferramenta assim se ela analisasse empresas reais?",
        "tipo": "nota 0-10",
        "objetivo": "Validar monetização.",
    },
]

ROTEIRO_ENTREVISTA_BETA = [
    {
        "etapa": 1,
        "titulo": "Contexto",
        "fala": "Antes de mostrar a ferramenta, me conta como você analisa uma ação hoje.",
        "objetivo": "Entender comportamento atual e dor real.",
    },
    {
        "etapa": 2,
        "titulo": "Demo curta",
        "fala": "Vou te mostrar uma análise exemplo em até 2 minutos. Repara se a decisão fica clara.",
        "objetivo": "Testar clareza e momento uau.",
    },
    {
        "etapa": 3,
        "titulo": "Reação imediata",
        "fala": "O que ficou mais claro? O que ficou confuso? Em qual momento você viu valor?",
        "objetivo": "Capturar percepção espontânea.",
    },
    {
        "etapa": 4,
        "titulo": "Utilidade real",
        "fala": "Você usaria isso para estudar empresas? Em qual situação?",
        "objetivo": "Entender caso de uso verdadeiro.",
    },
    {
        "etapa": 5,
        "titulo": "Preço e disposição",
        "fala": "Se a ferramenta analisasse empresas reais e gerasse relatórios, quanto faria sentido pagar por mês?",
        "objetivo": "Validar monetização sem empurrar venda.",
    },
    {
        "etapa": 6,
        "titulo": "Próximo passo",
        "fala": "Posso te colocar na lista beta para testar as próximas versões?",
        "objetivo": "Converter interesse em beta tester.",
    },
]

HIPOTESES_BETA = [
    {
        "hipotese": "Investidores iniciantes querem clareza de decisão, não só fórmulas.",
        "sinal_valido": "Notas altas em clareza e utilidade.",
        "risco": "O usuário achar a análise complexa demais.",
    },
    {
        "hipotese": "A tese explicada aumenta confiança no valuation.",
        "sinal_valido": "Notas altas em confiança e comentários positivos sobre a tese.",
        "risco": "O usuário enxergar como recomendação automática.",
    },
    {
        "hipotese": "Relatório exportável aumenta percepção de valor.",
        "sinal_valido": "Usuário citar que guardaria/compararia relatórios.",
        "risco": "Relatório parecer genérico.",
    },
    {
        "hipotese": "Há disposição de pagamento se houver dados reais e facilidade.",
        "sinal_valido": "Probabilidade de pagar >= 7 e preço justo declarado.",
        "risco": "Interesse educacional sem intenção de pagar.",
    },
]


def _limpar_texto(valor: Any) -> str:
    if valor is None:
        return ""
    return str(valor).strip()


def _to_int(valor: Any, padrao: int = 0) -> int:
    try:
        return int(valor)
    except Exception:
        return padrao


def _to_float(valor: Any, padrao: float = 0.0) -> float:
    try:
        return float(valor)
    except Exception:
        return padrao


def _garantir_csv(caminho: Path, campos: List[str]) -> None:
    if caminho.exists():
        return

    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()


def carregar_feedbacks_beta() -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_BETA_FEEDBACK_CSV, CAMPOS_FEEDBACK_BETA)

    with CAMINHO_BETA_FEEDBACK_CSV.open("r", newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def carregar_decisoes_beta_feedback() -> List[Dict[str, str]]:
    _garantir_csv(CAMINHO_DECISOES_BETA_FEEDBACK, CAMPOS_DECISAO_BETA)

    with CAMINHO_DECISOES_BETA_FEEDBACK.open("r", newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def gerar_csv_feedbacks_beta() -> str:
    _garantir_csv(CAMINHO_BETA_FEEDBACK_CSV, CAMPOS_FEEDBACK_BETA)
    return CAMINHO_BETA_FEEDBACK_CSV.read_text(encoding="utf-8")


def gerar_csv_decisoes_beta_feedback() -> str:
    _garantir_csv(CAMINHO_DECISOES_BETA_FEEDBACK, CAMPOS_DECISAO_BETA)
    return CAMINHO_DECISOES_BETA_FEEDBACK.read_text(encoding="utf-8")


def salvar_feedback_beta(dados: Dict[str, Any]) -> Dict[str, str]:
    _garantir_csv(CAMINHO_BETA_FEEDBACK_CSV, CAMPOS_FEEDBACK_BETA)

    registro = {
        "id": str(uuid4())[:8],
        "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "nome": _limpar_texto(dados.get("nome")),
        "email": _limpar_texto(dados.get("email")),
        "perfil": _limpar_texto(dados.get("perfil")),
        "nivel_investidor": _limpar_texto(dados.get("nivel_investidor")),
        "clareza_demo": str(dados.get("clareza_demo", "")),
        "utilidade_analise": str(dados.get("utilidade_analise", "")),
        "confianca_resultado": str(dados.get("confianca_resultado", "")),
        "facilidade_uso": str(dados.get("facilidade_uso", "")),
        "probabilidade_usar": str(dados.get("probabilidade_usar", "")),
        "probabilidade_pagar": str(dados.get("probabilidade_pagar", "")),
        "preco_justo_mensal": str(dados.get("preco_justo_mensal", "")),
        "maior_valor": _limpar_texto(dados.get("maior_valor")),
        "maior_duvida": _limpar_texto(dados.get("maior_duvida")),
        "funcionalidade_mais_importante": _limpar_texto(dados.get("funcionalidade_mais_importante")),
        "observacoes": _limpar_texto(dados.get("observacoes")),
    }

    with CAMINHO_BETA_FEEDBACK_CSV.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_FEEDBACK_BETA)
        escritor.writerow(registro)

    return registro


def salvar_decisao_beta_feedback(saude: Dict[str, Any], observacoes: str = "") -> Dict[str, str]:
    _garantir_csv(CAMINHO_DECISOES_BETA_FEEDBACK, CAMPOS_DECISAO_BETA)

    registro = {
        "id": str(uuid4())[:8],
        "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score_beta": str(saude.get("score_beta", "")),
        "score_demo": str(saude.get("score_demo", "")),
        "score_premium": str(saude.get("score_premium", "")),
        "score_launch": str(saude.get("score_launch", "")),
        "feedbacks_total": str(saude.get("feedbacks_total", "")),
        "nps_beta_estimado": str(saude.get("nps_beta_estimado", "")),
        "pronto_para_beta_fechado": str(saude.get("pronto_para_beta_fechado", "")),
        "risco": _limpar_texto(saude.get("risco")),
        "decisao": _limpar_texto(saude.get("decisao")),
        "proximo_passo": _limpar_texto(saude.get("proximo_passo")),
        "observacoes": _limpar_texto(observacoes),
    }

    with CAMINHO_DECISOES_BETA_FEEDBACK.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISAO_BETA)
        escritor.writerow(registro)

    return registro


def calcular_metricas_feedbacks(feedbacks: List[Dict[str, str]]) -> Dict[str, Any]:
    total = len(feedbacks)

    if total == 0:
        return {
            "feedbacks_total": 0,
            "media_clareza": 0,
            "media_utilidade": 0,
            "media_confianca": 0,
            "media_facilidade": 0,
            "media_probabilidade_usar": 0,
            "media_probabilidade_pagar": 0,
            "ticket_medio_declarado": 0,
            "nps_beta_estimado": 0,
            "promotores": 0,
            "neutros": 0,
            "detratores": 0,
        }

    def media(campo: str) -> float:
        valores = [_to_float(item.get(campo)) for item in feedbacks]
        return round(sum(valores) / len(valores), 2) if valores else 0

    notas_uso = [_to_int(item.get("probabilidade_usar")) for item in feedbacks]
    promotores = sum(1 for nota in notas_uso if nota >= 9)
    neutros = sum(1 for nota in notas_uso if 7 <= nota <= 8)
    detratores = sum(1 for nota in notas_uso if nota <= 6)
    nps = round(((promotores - detratores) / total) * 100, 2) if total else 0

    precos = [_to_float(item.get("preco_justo_mensal")) for item in feedbacks if _to_float(item.get("preco_justo_mensal")) > 0]
    ticket_medio = round(sum(precos) / len(precos), 2) if precos else 0

    return {
        "feedbacks_total": total,
        "media_clareza": media("clareza_demo"),
        "media_utilidade": media("utilidade_analise"),
        "media_confianca": media("confianca_resultado"),
        "media_facilidade": media("facilidade_uso"),
        "media_probabilidade_usar": media("probabilidade_usar"),
        "media_probabilidade_pagar": media("probabilidade_pagar"),
        "ticket_medio_declarado": ticket_medio,
        "nps_beta_estimado": nps,
        "promotores": promotores,
        "neutros": neutros,
        "detratores": detratores,
    }


def calcular_saude_beta_feedback() -> Dict[str, Any]:
    feedbacks = carregar_feedbacks_beta()
    metricas = calcular_metricas_feedbacks(feedbacks)

    try:
        demo = calcular_demo_2min_valoris()
    except Exception as erro:
        demo = {"score_demo": 0, "pronta_para_beta": False, "erro": str(erro)}

    try:
        premium = calcular_saude_analise_premium()
    except Exception as erro:
        premium = {"score_produto_premium": 0, "erro": str(erro)}

    try:
        launch = calcular_saude_launch_readiness()
    except Exception as erro:
        launch = {"score_launch": 0, "erro": str(erro)}

    score_demo = int(demo.get("score_demo", 0) or 0)
    score_premium = int(premium.get("score_produto_premium", 0) or 0)
    score_launch = int(launch.get("score_launch", 0) or 0)

    if metricas["feedbacks_total"] == 0:
        score_feedback_real = 0
    else:
        score_feedback_real = int(round(
            metricas["media_clareza"] * 2.0
            + metricas["media_utilidade"] * 2.2
            + metricas["media_confianca"] * 1.8
            + metricas["media_facilidade"] * 1.6
            + metricas["media_probabilidade_usar"] * 1.5
            + metricas["media_probabilidade_pagar"] * 0.9
        ))
        score_feedback_real = max(0, min(100, score_feedback_real))

    score_beta = int(round(
        score_demo * 0.26
        + score_premium * 0.22
        + score_launch * 0.18
        + score_feedback_real * 0.34
    ))

    pronto_para_beta_fechado = (
        score_beta >= 78
        and score_demo >= 85
        and score_premium >= 85
    )

    if metricas["feedbacks_total"] < 3:
        risco = "Médio"
        decisao = "Beta técnico pronto, validação real insuficiente"
        proximo_passo = "Coletar pelo menos 3 feedbacks reais com a demo de 2 minutos."
    elif score_beta >= 82 and metricas["media_probabilidade_usar"] >= 8:
        risco = "Médio controlado"
        decisao = "Avançar para beta fechado"
        proximo_passo = "Convidar usuários selecionados e medir retenção, dúvidas e disposição de pagamento."
    elif score_beta >= 68:
        risco = "Médio"
        decisao = "Continuar validação antes do beta fechado"
        proximo_passo = "Ajustar UX e clareza com base nas maiores dúvidas dos feedbacks."
    else:
        risco = "Alto"
        decisao = "Não abrir beta ainda"
        proximo_passo = "Refinar proposta de valor, demo e análise premium."

    return {
        "versao": VERSAO_BETA_FEEDBACK_VALORIS,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score_beta": max(0, min(100, score_beta)),
        "score_feedback_real": score_feedback_real,
        "score_demo": score_demo,
        "score_premium": score_premium,
        "score_launch": score_launch,
        "feedbacks_total": metricas["feedbacks_total"],
        "nps_beta_estimado": metricas["nps_beta_estimado"],
        "pronto_para_beta_fechado": pronto_para_beta_fechado,
        "risco": risco,
        "decisao": decisao,
        "proximo_passo": proximo_passo,
        "metricas": metricas,
        "feedbacks": feedbacks[-25:],
        "demo": demo,
        "premium": premium,
        "launch": launch,
        "perguntas": PERGUNTAS_FEEDBACK_BETA,
        "roteiro": ROTEIRO_ENTREVISTA_BETA,
        "hipoteses": HIPOTESES_BETA,
    }


def gerar_roteiro_beta_markdown(saude: Dict[str, Any] | None = None) -> str:
    if saude is None:
        saude = calcular_saude_beta_feedback()

    roteiro = "\n\n".join(
        [
            f"""### {item['etapa']}. {item['titulo']}

**Fala:** {item['fala']}  
**Objetivo:** {item['objetivo']}
"""
            for item in ROTEIRO_ENTREVISTA_BETA
        ]
    )

    hipoteses = "\n".join(
        [
            f"- **{item['hipotese']}** Sinal válido: {item['sinal_valido']} Risco: {item['risco']}"
            for item in HIPOTESES_BETA
        ]
    )

    return f"""# Roteiro Beta Tester — Valoris

Versão: {VERSAO_BETA_FEEDBACK_VALORIS}  
Gerado em: {saude["gerado_em"]}

## Status

Score Beta: {saude["score_beta"]}/100  
Feedbacks reais: {saude["feedbacks_total"]}  
NPS beta estimado: {saude["nps_beta_estimado"]}  
Risco: {saude["risco"]}  
Decisão: {saude["decisao"]}  
Próximo passo: {saude["proximo_passo"]}

## Objetivo da entrevista

Validar se a Valoris resolve uma dor real: transformar dados de ações em análise clara, prudente e explicável.

## Roteiro

{roteiro}

## Hipóteses testadas

{hipoteses}

## Frase de convite

"Estou liberando uma versão beta da Valoris para poucas pessoas que querem analisar ações com mais método, clareza e disciplina. Posso te colocar na lista para testar e me dar um feedback honesto?"
"""


def gerar_formulario_feedback_markdown() -> str:
    perguntas = "\n".join(
        [
            f"- **{item['bloco']}** — {item['pergunta']} ({item['tipo']})"
            for item in PERGUNTAS_FEEDBACK_BETA
        ]
    )

    return f"""# Formulário de Feedback Beta — Valoris

Versão: {VERSAO_BETA_FEEDBACK_VALORIS}

## Perguntas principais

{perguntas}

## Perguntas abertas

- O que mais gerou valor para você?
- O que ficou confuso?
- Qual funcionalidade você mais gostaria de ver?
- Você usaria isso para estudar ações reais?
- Quanto faria sentido pagar por mês se a ferramenta evoluir bem?

## Métrica de decisão

A Valoris só deve avançar para beta fechado quando clareza, utilidade e confiança ficarem acima de 8/10 em feedback real.
"""


def gerar_plano_beta_markdown(saude: Dict[str, Any] | None = None) -> str:
    if saude is None:
        saude = calcular_saude_beta_feedback()

    return f"""# Plano Beta Feedback — Valoris

Versão: {VERSAO_BETA_FEEDBACK_VALORIS}  
Gerado em: {saude["gerado_em"]}

## Diagnóstico

Score Beta: {saude["score_beta"]}/100  
Pronto para beta fechado: {saude["pronto_para_beta_fechado"]}  
Decisão: {saude["decisao"]}  
Próximo passo: {saude["proximo_passo"]}

## Plano de 7 dias

1. Selecionar 3 a 5 pessoas com perfil de investidor/estudante.
2. Mostrar a demo de 2 minutos.
3. Não explicar demais antes da demo.
4. Coletar notas de clareza, utilidade, confiança e pagamento.
5. Registrar dúvidas e objeções.
6. Ajustar a experiência premium.
7. Só avançar para beta fechado se houver sinal real de uso.

## Métricas mínimas

- Clareza média >= 8
- Utilidade média >= 8
- Confiança média >= 7
- Probabilidade de usar >= 8
- Pelo menos 3 feedbacks reais
"""


def salvar_roteiro_beta_markdown() -> Dict[str, Any]:
    saude = calcular_saude_beta_feedback()
    CAMINHO_ROTEIRO_BETA_MD.write_text(gerar_roteiro_beta_markdown(saude), encoding="utf-8")
    return {
        "ok": True,
        "arquivo": str(CAMINHO_ROTEIRO_BETA_MD),
        "score_beta": saude["score_beta"],
        "decisao": saude["decisao"],
    }


def salvar_formulario_feedback_markdown() -> Dict[str, Any]:
    CAMINHO_FORMULARIO_BETA_MD.write_text(gerar_formulario_feedback_markdown(), encoding="utf-8")
    return {
        "ok": True,
        "arquivo": str(CAMINHO_FORMULARIO_BETA_MD),
    }


def salvar_plano_beta_markdown() -> Dict[str, Any]:
    saude = calcular_saude_beta_feedback()
    CAMINHO_PLANO_BETA_MD.write_text(gerar_plano_beta_markdown(saude), encoding="utf-8")
    return {
        "ok": True,
        "arquivo": str(CAMINHO_PLANO_BETA_MD),
        "score_beta": saude["score_beta"],
        "decisao": saude["decisao"],
    }


def gerar_manifesto_beta_feedback() -> Dict[str, Any]:
    saude = calcular_saude_beta_feedback()
    manifesto = {
        "versao": VERSAO_BETA_FEEDBACK_VALORIS,
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "saude": saude,
        "perguntas": PERGUNTAS_FEEDBACK_BETA,
        "roteiro": ROTEIRO_ENTREVISTA_BETA,
        "hipoteses": HIPOTESES_BETA,
        "estrategia": {
            "objetivo": "Transformar a demo em validação real com beta testers.",
            "proxima_versao": "Ajustes de UX com base no feedback real ou preparação de beta fechado.",
            "regra": "Não confundir produto pronto com produto validado.",
        },
    }

    CAMINHO_MANIFESTO_BETA_FEEDBACK.write_text(json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifesto


def gerar_feedback_demo_exemplo() -> Dict[str, Any]:
    exemplo = {
        "nome": "Beta Tester Exemplo",
        "email": "tester@exemplo.com",
        "perfil": "Investidor intermediário",
        "nivel_investidor": "Invisto entre 1 e 3 anos",
        "clareza_demo": 9,
        "utilidade_analise": 9,
        "confianca_resultado": 8,
        "facilidade_uso": 8,
        "probabilidade_usar": 9,
        "probabilidade_pagar": 7,
        "preco_justo_mensal": 39.90,
        "maior_valor": "A tese explicada e a margem de segurança deixam a decisão mais clara.",
        "maior_duvida": "Como os dados reais das empresas serão atualizados?",
        "funcionalidade_mais_importante": "Comparar empresas do mesmo setor.",
        "observacoes": "Feedback exemplo gerado para validar o fluxo beta.",
    }
    return salvar_feedback_beta(exemplo)


def _injetar_css_beta_feedback() -> None:
    st.markdown(
        """
        <style>
            .beta-feedback-hero {
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
            .beta-feedback-eyebrow {
                color: #d6b56d;
                font-size: 0.74rem;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                font-weight: 880;
                margin-bottom: 0.35rem;
            }
            .beta-feedback-title {
                color: #f4f7fb;
                font-size: clamp(1.8rem, 5.5vw, 3.25rem);
                font-weight: 950;
                line-height: 1.02;
                letter-spacing: -0.058em;
                margin-bottom: 0.55rem;
            }
            .beta-feedback-subtitle {
                color: rgba(244, 247, 251, 0.75);
                font-size: clamp(0.94rem, 2.2vw, 1.06rem);
                line-height: 1.56;
                max-width: 1050px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def renderizar_beta_feedback_valoris() -> None:
    _injetar_css_beta_feedback()

    st.markdown(
        f"""
        <div class="beta-feedback-hero">
            <div class="beta-feedback-eyebrow">Valoris • Beta Feedback • v{VERSAO_BETA_FEEDBACK_VALORIS}</div>
            <div class="beta-feedback-title">Validação real antes do lançamento.</div>
            <div class="beta-feedback-subtitle">
                Capture feedback de beta testers, calcule sinal de validação, estime NPS e decida
                se a Valoris está pronta para beta fechado.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    saude = calcular_saude_beta_feedback()

    st.markdown("### Diagnóstico beta")
    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Score Beta", f"{saude['score_beta']}/100")

    with col_2:
        st.metric("Feedbacks", saude["feedbacks_total"])

    with col_3:
        st.metric("NPS estimado", saude["nps_beta_estimado"])

    with col_4:
        st.metric("Decisão", saude["decisao"])

    st.progress(saude["score_beta"] / 100)

    if saude["pronto_para_beta_fechado"]:
        st.success(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    elif saude["score_beta"] >= 68:
        st.warning(f"**{saude['decisao']}** — {saude['proximo_passo']}")
    else:
        st.info(f"**{saude['decisao']}** — {saude['proximo_passo']}")

    st.divider()

    st.markdown("### Registrar feedback beta")

    with st.form("form_feedback_beta_valoris"):
        col_a, col_b = st.columns(2)

        with col_a:
            nome = st.text_input("Nome")
            email = st.text_input("E-mail")
            perfil = st.selectbox("Perfil", PERFIS_BETA)
            nivel_investidor = st.selectbox("Nível como investidor", NIVEIS_INVESTIDOR)

        with col_b:
            clareza_demo = st.slider("Clareza da demo", 0, 10, 8)
            utilidade_analise = st.slider("Utilidade da análise", 0, 10, 8)
            confianca_resultado = st.slider("Confiança no resultado", 0, 10, 7)
            facilidade_uso = st.slider("Facilidade de uso", 0, 10, 7)
            probabilidade_usar = st.slider("Probabilidade de usar", 0, 10, 8)
            probabilidade_pagar = st.slider("Probabilidade de pagar", 0, 10, 6)
            preco_justo_mensal = st.number_input("Preço mensal justo estimado (R$)", min_value=0.0, value=29.90, step=5.0)

        maior_valor = st.text_area("O que mais gerou valor?", height=80)
        maior_duvida = st.text_area("O que ficou confuso ou gerou dúvida?", height=80)
        funcionalidade_mais_importante = st.text_area("Funcionalidade mais importante para próxima versão", height=80)
        observacoes = st.text_area("Observações adicionais", height=80)

        enviado = st.form_submit_button("Salvar feedback beta")

        if enviado:
            registro = salvar_feedback_beta(
                {
                    "nome": nome,
                    "email": email,
                    "perfil": perfil,
                    "nivel_investidor": nivel_investidor,
                    "clareza_demo": clareza_demo,
                    "utilidade_analise": utilidade_analise,
                    "confianca_resultado": confianca_resultado,
                    "facilidade_uso": facilidade_uso,
                    "probabilidade_usar": probabilidade_usar,
                    "probabilidade_pagar": probabilidade_pagar,
                    "preco_justo_mensal": preco_justo_mensal,
                    "maior_valor": maior_valor,
                    "maior_duvida": maior_duvida,
                    "funcionalidade_mais_importante": funcionalidade_mais_importante,
                    "observacoes": observacoes,
                }
            )
            st.success(f"Feedback salvo: {registro['id']}")
            st.rerun()

    st.divider()

    st.markdown("### Métricas de feedback")
    st.json(saude["metricas"])

    st.markdown("### Últimos feedbacks")
    if saude["feedbacks"]:
        st.dataframe(saude["feedbacks"], width="stretch", hide_index=True)
    else:
        st.info("Nenhum feedback real registrado ainda. Gere um exemplo ou colete com beta testers.")

    st.divider()

    col_btn_1, col_btn_2, col_btn_3, col_btn_4 = st.columns(4)

    with col_btn_1:
        if st.button("Gerar feedback exemplo", key="beta_feedback_exemplo"):
            registro = gerar_feedback_demo_exemplo()
            st.success(f"Feedback exemplo gerado: {registro['id']}")
            st.rerun()

    with col_btn_2:
        if st.button("Gerar manifesto Beta", key="beta_feedback_manifesto"):
            manifesto = gerar_manifesto_beta_feedback()
            st.success(f"Manifesto gerado: {CAMINHO_MANIFESTO_BETA_FEEDBACK}")
            st.json({"versao": manifesto["versao"], "score_beta": manifesto["saude"]["score_beta"]})

    with col_btn_3:
        if st.button("Salvar roteiro beta .md", key="beta_feedback_roteiro"):
            retorno = salvar_roteiro_beta_markdown()
            st.success(f"Roteiro salvo: {retorno['arquivo']}")
            st.json(retorno)

    with col_btn_4:
        if st.button("Salvar plano beta .md", key="beta_feedback_plano"):
            retorno = salvar_plano_beta_markdown()
            st.success(f"Plano salvo: {retorno['arquivo']}")
            st.json(retorno)

    if st.button("Salvar formulário feedback .md", key="beta_feedback_formulario"):
        retorno = salvar_formulario_feedback_markdown()
        st.success(f"Formulário salvo: {retorno['arquivo']}")
        st.json(retorno)

    if st.button("Salvar decisão Beta", key="beta_feedback_decisao"):
        registro = salvar_decisao_beta_feedback(saude, observacoes="Decisão gerada pelo módulo de validação beta.")
        st.success(f"Decisão salva: {registro['decisao']}")
        st.rerun()

    st.download_button(
        "Baixar roteiro beta (.md)",
        data=gerar_roteiro_beta_markdown(saude),
        file_name="ROTEIRO_BETA_TESTER_VALORIS.md",
        mime="text/markdown",
        key="download_roteiro_beta",
    )

    st.download_button(
        "Baixar formulário beta (.md)",
        data=gerar_formulario_feedback_markdown(),
        file_name="FORMULARIO_FEEDBACK_BETA_VALORIS.md",
        mime="text/markdown",
        key="download_formulario_beta",
    )

    st.download_button(
        "Baixar feedbacks beta (.csv)",
        data=gerar_csv_feedbacks_beta(),
        file_name="feedback_beta_valoris.csv",
        mime="text/csv",
        key="download_feedbacks_beta",
    )


def executar_autoteste_beta_feedback_valoris() -> List[Dict[str, str]]:
    saude = calcular_saude_beta_feedback()

    return [
        {
            "teste": "versao_beta_feedback",
            "status": "OK" if VERSAO_BETA_FEEDBACK_VALORIS == "3.8.78" else "FALHA",
            "detalhe": VERSAO_BETA_FEEDBACK_VALORIS,
        },
        {
            "teste": "score_beta",
            "status": "OK" if 0 <= saude["score_beta"] <= 100 else "FALHA",
            "detalhe": str(saude["score_beta"]),
        },
        {
            "teste": "perguntas_feedback",
            "status": "OK" if len(PERGUNTAS_FEEDBACK_BETA) >= 5 else "FALHA",
            "detalhe": str(len(PERGUNTAS_FEEDBACK_BETA)),
        },
        {
            "teste": "renderizador",
            "status": "OK" if callable(renderizar_beta_feedback_valoris) else "FALHA",
            "detalhe": "renderizar_beta_feedback_valoris",
        },
    ]
