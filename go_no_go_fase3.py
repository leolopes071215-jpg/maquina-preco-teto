# go_no_go_fase3.py

import csv
import uuid
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List

import streamlit as st


# ============================================================
# MÁQUINA DE PREÇO-TETO
# v3.5 — Decisão Go/No-Go para Escala e Automação
# ------------------------------------------------------------
# Esta tela consolida a decisão estratégica da Fase 3.
#
# Objetivo:
# - decidir se o negócio deve vender mais, pausar, corrigir,
#   melhorar retenção, resolver suporte ou preparar automação
# - transformar métricas em decisão executiva
# - evitar escalar antes de provar entrega, suporte e retenção
# ============================================================


CAMINHO_CLIENTES_BETA = Path("clientes_beta.csv")
CAMINHO_SUPORTE_BETA = Path("suporte_beta.csv")
CAMINHO_RETENCAO_BETA = Path("retencao_beta.csv")
CAMINHO_METRICAS_FASE3 = Path("metricas_fase3.csv")
CAMINHO_DECISOES_FASE3 = Path("decisoes_fase3.csv")


CAMPOS_DECISOES = [
    "id",
    "data_registro",
    "decisao",
    "classificacao",
    "score_go_no_go",
    "score_receita",
    "score_retencao",
    "score_suporte",
    "score_operacional",
    "score_automacao",
    "clientes_pagos",
    "clientes_ativos",
    "receita_real",
    "mrr_estimado",
    "nps_medio",
    "tickets_criticos",
    "clientes_em_risco",
    "cancelamentos",
    "renovacoes",
    "racional",
    "acao_primaria",
    "acao_secundaria",
    "prazo",
    "observacoes",
]


DECISOES_POSSIVEIS = [
    "Vender pequeno lote adicional",
    "Continuar beta pago controlado",
    "Pausar novas vendas e corrigir suporte",
    "Focar retenção antes de vender mais",
    "Melhorar produto e onboarding",
    "Validar preço e oferta manualmente",
    "Preparar automação leve",
    "Não escalar ainda",
]


def _garantir_arquivo_decisoes() -> None:
    if CAMINHO_DECISOES_FASE3.exists():
        return

    with open(CAMINHO_DECISOES_FASE3, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISOES)
        escritor.writeheader()


def carregar_decisoes_fase3() -> List[Dict[str, str]]:
    _garantir_arquivo_decisoes()

    with open(CAMINHO_DECISOES_FASE3, "r", newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        return [
            {campo: linha.get(campo, "") for campo in CAMPOS_DECISOES}
            for linha in leitor
        ]


def salvar_decisoes_fase3(registros: List[Dict[str, Any]]) -> None:
    with open(CAMINHO_DECISOES_FASE3, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_DECISOES)
        escritor.writeheader()

        for registro in registros:
            escritor.writerow(
                {campo: registro.get(campo, "") for campo in CAMPOS_DECISOES}
            )


def limpar_decisoes_fase3() -> None:
    salvar_decisoes_fase3([])


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


def _contar(registros: List[Dict[str, str]], campo: str, valor: str) -> int:
    return len([registro for registro in registros if registro.get(campo) == valor])


def _media_campo(registros: List[Dict[str, str]], campo: str) -> float:
    valores = []

    for registro in registros:
        valor = _safe_float(registro.get(campo))

        if valor >= 0:
            valores.append(valor)

    if len(valores) == 0:
        return 0.0

    return mean(valores)


def _receita_real(clientes: List[Dict[str, str]]) -> float:
    return sum(
        _safe_float(cliente.get("valor_pago"))
        for cliente in clientes
        if cliente.get("status_pagamento") == "Pago"
    )


def _mrr_estimado(clientes: List[Dict[str, str]]) -> float:
    total = 0.0

    for cliente in clientes:
        if cliente.get("status_pagamento") != "Pago":
            continue

        valor = _safe_float(cliente.get("valor_pago"))
        periodicidade = cliente.get("periodicidade", "")

        if periodicidade == "Mensal":
            total += valor
        elif periodicidade == "Trimestral":
            total += valor / 3
        elif periodicidade == "Anual":
            total += valor / 12

    return total


def _clientes_pagos(clientes: List[Dict[str, str]]) -> int:
    return _contar(clientes, "status_pagamento", "Pago")


def _clientes_ativos(clientes: List[Dict[str, str]]) -> int:
    status_ativos = ["Ativo", "Em onboarding", "Precisa de suporte", "Em risco"]

    return len(
        [
            cliente for cliente in clientes
            if cliente.get("status_pagamento") == "Pago"
            and cliente.get("status_cliente") in status_ativos
        ]
    )


def _clientes_em_risco_clientes(clientes: List[Dict[str, str]]) -> int:
    return len(
        [
            cliente for cliente in clientes
            if cliente.get("risco_cancelamento") in ["Alto", "Crítico"]
            or cliente.get("status_cliente") == "Em risco"
        ]
    )


def _satisfacao_clientes(clientes: List[Dict[str, str]]) -> float:
    return _media_campo(clientes, "satisfacao")


def _tickets_abertos(suporte: List[Dict[str, str]]) -> int:
    status_fechados = ["Resolvido", "Fechado", "Virou melhoria de produto"]

    return len(
        [
            ticket for ticket in suporte
            if ticket.get("status_atendimento") not in status_fechados
        ]
    )


def _tickets_resolvidos(suporte: List[Dict[str, str]]) -> int:
    return len(
        [
            ticket for ticket in suporte
            if ticket.get("status_atendimento") in ["Resolvido", "Fechado"]
        ]
    )


def _tickets_criticos(suporte: List[Dict[str, str]]) -> int:
    return len(
        [
            ticket for ticket in suporte
            if ticket.get("prioridade") == "Crítica"
            or ticket.get("risco_cancelamento") == "Crítico"
            or ticket.get("impacto_cliente") == "Impede o uso"
        ]
    )


def _taxa_resolucao(suporte: List[Dict[str, str]]) -> float:
    if len(suporte) == 0:
        return 0.0

    return (_tickets_resolvidos(suporte) / len(suporte)) * 100


def _tempo_medio_suporte(suporte: List[Dict[str, str]]) -> float:
    return _media_campo(suporte, "tempo_resposta_horas")


def _satisfacao_suporte(suporte: List[Dict[str, str]]) -> float:
    return _media_campo(suporte, "satisfacao_pos_atendimento")


def _nps_medio(retencao: List[Dict[str, str]]) -> float:
    return _media_campo(retencao, "nps")


def _renovacoes(retencao: List[Dict[str, str]]) -> int:
    return _contar(retencao, "status_renovacao", "Renovou") + _contar(
        retencao,
        "status_cliente",
        "Renovou",
    )


def _cancelamentos(retencao: List[Dict[str, str]]) -> int:
    return _contar(retencao, "status_cliente", "Cancelado") + _contar(
        retencao,
        "status_renovacao",
        "Não renovou",
    )


def _clientes_em_risco_retencao(retencao: List[Dict[str, str]]) -> int:
    return len(
        [
            registro for registro in retencao
            if registro.get("risco_churn") in ["Alto", "Crítico"]
            or registro.get("saude_cliente") in ["Risco", "Crítica"]
            or registro.get("status_cliente") in ["Em risco", "Cancelado", "Não renovou"]
        ]
    )


def _valor_percebido_alto(retencao: List[Dict[str, str]]) -> int:
    return _contar(retencao, "valor_percebido", "Alto") + _contar(
        retencao,
        "valor_percebido",
        "Muito alto",
    )


def _uso_relevante(retencao: List[Dict[str, str]]) -> int:
    return _contar(retencao, "uso_percebido", "Usa com frequência") + _contar(
        retencao,
        "uso_percebido",
        "Usa ocasionalmente",
    )


def _ultimo_snapshot_metricas(metricas: List[Dict[str, str]]) -> Dict[str, str]:
    if len(metricas) == 0:
        return {}

    return metricas[-1]


def _score_receita(clientes: List[Dict[str, str]]) -> int:
    pagos = _clientes_pagos(clientes)
    ativos = _clientes_ativos(clientes)
    receita = _receita_real(clientes)
    mrr = _mrr_estimado(clientes)

    pontos = 0.0
    pontos += min(pagos * 18.0, 45)
    pontos += min(ativos * 10.0, 25)
    pontos += min(receita / 8, 20)
    pontos += min(mrr / 8, 20)

    return int(round(max(0, min(100, pontos))))


def _score_retencao(retencao: List[Dict[str, str]]) -> int:
    if len(retencao) == 0:
        return 0

    nps = _nps_medio(retencao)
    renovacoes = _renovacoes(retencao)
    cancelamentos = _cancelamentos(retencao)
    risco = _clientes_em_risco_retencao(retencao)
    valor_alto = _valor_percebido_alto(retencao)
    uso = _uso_relevante(retencao)

    pontos = 0.0
    pontos += nps * 4.0
    pontos += min(renovacoes * 18.0, 36)
    pontos += min(valor_alto * 10.0, 25)
    pontos += min(uso * 8.0, 20)
    pontos -= min(cancelamentos * 18.0, 36)
    pontos -= min(risco * 10.0, 30)

    return int(round(max(0, min(100, pontos))))


def _score_suporte(suporte: List[Dict[str, str]]) -> int:
    if len(suporte) == 0:
        return 65

    taxa = _taxa_resolucao(suporte)
    satisfacao = _satisfacao_suporte(suporte)
    tempo = _tempo_medio_suporte(suporte)
    abertos = _tickets_abertos(suporte)
    criticos = _tickets_criticos(suporte)

    pontos = 0.0
    pontos += taxa * 0.35
    pontos += satisfacao * 4.0

    if tempo > 0:
        if tempo <= 2:
            pontos += 18
        elif tempo <= 8:
            pontos += 12
        elif tempo <= 24:
            pontos += 6
        else:
            pontos -= 10

    pontos -= min(abertos * 4.0, 20)
    pontos -= min(criticos * 12.0, 36)

    return int(round(max(0, min(100, pontos))))


def _score_operacional(
    clientes: List[Dict[str, str]],
    suporte: List[Dict[str, str]],
    retencao: List[Dict[str, str]],
) -> int:
    clientes_pagos = _clientes_pagos(clientes)
    clientes_ativos = _clientes_ativos(clientes)
    tickets_abertos = _tickets_abertos(suporte)
    tickets_criticos = _tickets_criticos(suporte)
    satisfacao = _satisfacao_clientes(clientes)
    nps = _nps_medio(retencao)

    pontos = 0.0
    pontos += min(clientes_pagos * 8.0, 24)
    pontos += min(clientes_ativos * 8.0, 24)
    pontos += satisfacao * 3.0
    pontos += nps * 2.0
    pontos -= min(tickets_abertos * 4.0, 20)
    pontos -= min(tickets_criticos * 10.0, 30)

    return int(round(max(0, min(100, pontos))))


def _score_automacao(
    clientes: List[Dict[str, str]],
    suporte: List[Dict[str, str]],
    retencao: List[Dict[str, str]],
    metricas: List[Dict[str, str]],
) -> int:
    pagos = _clientes_pagos(clientes)
    mrr = _mrr_estimado(clientes)
    tickets_criticos = _tickets_criticos(suporte)
    tickets_abertos = _tickets_abertos(suporte)
    nps = _nps_medio(retencao)
    renovacoes = _renovacoes(retencao)
    cancelamentos = _cancelamentos(retencao)
    ultimo_snapshot = _ultimo_snapshot_metricas(metricas)

    pontos = 0.0

    if pagos >= 1:
        pontos += 15
    if pagos >= 3:
        pontos += 15
    if mrr > 0:
        pontos += 15
    if nps >= 7:
        pontos += 15
    if nps >= 8:
        pontos += 10
    if renovacoes > 0:
        pontos += 15
    if tickets_criticos == 0:
        pontos += 10
    if tickets_abertos <= 2:
        pontos += 5
    if cancelamentos == 0:
        pontos += 10
    if len(ultimo_snapshot) > 0:
        pontos += 5

    return int(round(max(0, min(100, pontos))))


def _calcular_scores(
    clientes: List[Dict[str, str]],
    suporte: List[Dict[str, str]],
    retencao: List[Dict[str, str]],
    metricas: List[Dict[str, str]],
) -> Dict[str, int]:
    score_receita = _score_receita(clientes)
    score_retencao = _score_retencao(retencao)
    score_suporte = _score_suporte(suporte)
    score_operacional = _score_operacional(clientes, suporte, retencao)
    score_automacao = _score_automacao(clientes, suporte, retencao, metricas)

    score_go_no_go = int(
        round(
            score_receita * 0.25
            + score_retencao * 0.25
            + score_suporte * 0.20
            + score_operacional * 0.15
            + score_automacao * 0.15
        )
    )

    return {
        "go_no_go": max(0, min(100, score_go_no_go)),
        "receita": score_receita,
        "retencao": score_retencao,
        "suporte": score_suporte,
        "operacional": score_operacional,
        "automacao": score_automacao,
    }


def _classificar(score: int) -> str:
    if score >= 85:
        return "Pronto para automação leve controlada"
    if score >= 70:
        return "Apto para novo lote pequeno"
    if score >= 55:
        return "Continuar beta controlado"
    if score >= 40:
        return "Corrigir antes de vender mais"
    return "Não escalar"


def _decisao_automatica(
    clientes: List[Dict[str, str]],
    suporte: List[Dict[str, str]],
    retencao: List[Dict[str, str]],
    metricas: List[Dict[str, str]],
    scores: Dict[str, int],
) -> str:
    pagos = _clientes_pagos(clientes)
    tickets_criticos = _tickets_criticos(suporte)
    tickets_abertos = _tickets_abertos(suporte)
    risco_clientes = _clientes_em_risco_clientes(clientes)
    risco_retencao = _clientes_em_risco_retencao(retencao)
    cancelamentos = _cancelamentos(retencao)
    renovacoes = _renovacoes(retencao)
    nps = _nps_medio(retencao)

    if pagos == 0:
        return "Validar preço e oferta manualmente"

    if tickets_criticos > 0:
        return "Pausar novas vendas e corrigir suporte"

    if risco_clientes > 0 or risco_retencao > 0:
        return "Focar retenção antes de vender mais"

    if cancelamentos > 0 and renovacoes == 0:
        return "Não escalar ainda"

    if tickets_abertos > 3:
        return "Pausar novas vendas e corrigir suporte"

    if len(retencao) > 0 and nps < 7:
        return "Melhorar produto e onboarding"

    if scores["go_no_go"] >= 85 and scores["automacao"] >= 75:
        return "Preparar automação leve"

    if scores["go_no_go"] >= 70:
        return "Vender pequeno lote adicional"

    if scores["go_no_go"] >= 55:
        return "Continuar beta pago controlado"

    return "Não escalar ainda"


def _racional_decisao(
    decisao: str,
    clientes: List[Dict[str, str]],
    suporte: List[Dict[str, str]],
    retencao: List[Dict[str, str]],
    scores: Dict[str, int],
) -> str:
    pagos = _clientes_pagos(clientes)
    tickets_criticos = _tickets_criticos(suporte)
    risco = _clientes_em_risco_clientes(clientes) + _clientes_em_risco_retencao(retencao)
    nps = _nps_medio(retencao)
    cancelamentos = _cancelamentos(retencao)
    mrr = _mrr_estimado(clientes)

    if decisao == "Validar preço e oferta manualmente":
        return (
            "Ainda não existe pagamento confirmado. A prioridade não é automação, mas sim venda manual, "
            "conversa com leads e validação real de disposição de pagamento."
        )

    if decisao == "Pausar novas vendas e corrigir suporte":
        return (
            "Existem problemas de suporte que podem bloquear uso ou destruir confiança. "
            "Antes de buscar novos clientes, é melhor resolver a fricção atual."
        )

    if decisao == "Focar retenção antes de vender mais":
        return (
            "Há clientes em risco de churn ou cancelamento. Crescer aquisição agora pode mascarar "
            "um problema de valor percebido, onboarding ou entrega."
        )

    if decisao == "Melhorar produto e onboarding":
        return (
            "O NPS ou o uso real ainda não indicam valor forte. O produto precisa ficar mais claro, "
            "mais guiado e mais fácil de usar antes de abrir novo lote."
        )

    if decisao == "Preparar automação leve":
        return (
            "Os sinais combinados de receita, retenção, suporte e automação são positivos. "
            "Já faz sentido preparar checkout, login e acesso de forma gradual, sem abandonar validação manual."
        )

    if decisao == "Vender pequeno lote adicional":
        return (
            "Existe validação suficiente para testar mais clientes, mas ainda de forma controlada. "
            "A prioridade é aumentar amostra sem perder qualidade de suporte e retenção."
        )

    if decisao == "Continuar beta pago controlado":
        return (
            "O negócio tem sinais iniciais, mas ainda não há maturidade suficiente para automação ou escala. "
            "Continue medindo venda, entrega, suporte e retenção."
        )

    return (
        f"Score geral: {scores['go_no_go']}/100. Clientes pagos: {pagos}. MRR estimado: {_fmt_moeda(mrr)}. "
        f"NPS: {nps:.1f}/10. Tickets críticos: {tickets_criticos}. Clientes em risco: {risco}. "
        f"Cancelamentos: {cancelamentos}."
    )


def _acoes_para_decisao(decisao: str) -> Dict[str, str]:
    mapa = {
        "Validar preço e oferta manualmente": {
            "primaria": "Conversar com 5 leads quentes e tentar vender manualmente.",
            "secundaria": "Testar variações de preço, promessa e bônus sem automatizar.",
            "prazo": "3 a 7 dias",
        },
        "Pausar novas vendas e corrigir suporte": {
            "primaria": "Resolver todos os tickets críticos e problemas que impedem uso.",
            "secundaria": "Criar tutorial ou resposta padrão para os problemas recorrentes.",
            "prazo": "24 a 72 horas",
        },
        "Focar retenção antes de vender mais": {
            "primaria": "Fazer contato direto com clientes em risco e entender a dor real.",
            "secundaria": "Guiar o cliente em uma análise prática para aumentar valor percebido.",
            "prazo": "2 a 5 dias",
        },
        "Melhorar produto e onboarding": {
            "primaria": "Simplificar o primeiro uso e criar uma jornada guiada.",
            "secundaria": "Melhorar textos, exemplos, relatórios e explicações das premissas.",
            "prazo": "1 semana",
        },
        "Preparar automação leve": {
            "primaria": "Planejar login, checkout, liberação de acesso e banco de dados real.",
            "secundaria": "Manter venda e suporte controlados durante a transição.",
            "prazo": "1 a 3 semanas",
        },
        "Vender pequeno lote adicional": {
            "primaria": "Abrir mais 3 a 5 vagas beta pagas com acompanhamento próximo.",
            "secundaria": "Registrar suporte, retenção e feedback de cada novo usuário.",
            "prazo": "1 semana",
        },
        "Continuar beta pago controlado": {
            "primaria": "Manter poucos clientes, medir uso e gerar snapshots semanais.",
            "secundaria": "Corrigir pontos fracos antes de aumentar aquisição.",
            "prazo": "1 semana",
        },
        "Não escalar ainda": {
            "primaria": "Diagnosticar gargalo principal: venda, produto, suporte ou retenção.",
            "secundaria": "Corrigir o gargalo mais crítico antes de qualquer automação.",
            "prazo": "3 a 7 dias",
        },
    }

    return mapa.get(
        decisao,
        {
            "primaria": "Revisar os dados e definir ação manual.",
            "secundaria": "Acompanhar clientes de perto antes de escalar.",
            "prazo": "1 semana",
        },
    )


def _registrar_decisao(
    decisao: str,
    classificacao: str,
    scores: Dict[str, int],
    clientes: List[Dict[str, str]],
    suporte: List[Dict[str, str]],
    retencao: List[Dict[str, str]],
    racional: str,
    acao_primaria: str,
    acao_secundaria: str,
    prazo: str,
    observacoes: str,
) -> None:
    registros = carregar_decisoes_fase3()

    registros.append(
        {
            "id": str(uuid.uuid4())[:8],
            "data_registro": datetime.now().isoformat(timespec="minutes"),
            "decisao": decisao,
            "classificacao": classificacao,
            "score_go_no_go": str(scores["go_no_go"]),
            "score_receita": str(scores["receita"]),
            "score_retencao": str(scores["retencao"]),
            "score_suporte": str(scores["suporte"]),
            "score_operacional": str(scores["operacional"]),
            "score_automacao": str(scores["automacao"]),
            "clientes_pagos": str(_clientes_pagos(clientes)),
            "clientes_ativos": str(_clientes_ativos(clientes)),
            "receita_real": str(_receita_real(clientes)),
            "mrr_estimado": str(_mrr_estimado(clientes)),
            "nps_medio": str(_nps_medio(retencao)),
            "tickets_criticos": str(_tickets_criticos(suporte)),
            "clientes_em_risco": str(_clientes_em_risco_clientes(clientes) + _clientes_em_risco_retencao(retencao)),
            "cancelamentos": str(_cancelamentos(retencao)),
            "renovacoes": str(_renovacoes(retencao)),
            "racional": racional,
            "acao_primaria": acao_primaria,
            "acao_secundaria": acao_secundaria,
            "prazo": prazo,
            "observacoes": observacoes.strip(),
        }
    )

    salvar_decisoes_fase3(registros)


def _gerar_tabela_criterios(
    clientes: List[Dict[str, str]],
    suporte: List[Dict[str, str]],
    retencao: List[Dict[str, str]],
    scores: Dict[str, int],
) -> List[Dict[str, str]]:
    return [
        {
            "Critério": "Cliente pago confirmado",
            "Status": "OK" if _clientes_pagos(clientes) >= 1 else "Pendente",
            "Leitura": "Sem pagamento, não há validação comercial.",
        },
        {
            "Critério": "Pelo menos 2 clientes ativos pagos",
            "Status": "OK" if _clientes_ativos(clientes) >= 2 else "Pendente",
            "Leitura": "Ajuda a reduzir viés de um único cliente.",
        },
        {
            "Critério": "MRR inicial positivo",
            "Status": "OK" if _mrr_estimado(clientes) > 0 else "Pendente",
            "Leitura": "Indica potencial de recorrência.",
        },
        {
            "Critério": "Sem tickets críticos",
            "Status": "OK" if _tickets_criticos(suporte) == 0 else "Pendente",
            "Leitura": "Suporte crítico trava escala.",
        },
        {
            "Critério": "NPS médio igual ou maior que 7",
            "Status": "OK" if _nps_medio(retencao) >= 7 else "Pendente",
            "Leitura": "Indica valor percebido mínimo.",
        },
        {
            "Critério": "Sem clientes em risco alto/crítico",
            "Status": "OK"
            if (_clientes_em_risco_clientes(clientes) + _clientes_em_risco_retencao(retencao)) == 0
            else "Pendente",
            "Leitura": "Risco de churn precisa ser tratado antes de aquisição.",
        },
        {
            "Critério": "Sem cancelamento/não renovação",
            "Status": "OK" if _cancelamentos(retencao) == 0 else "Pendente",
            "Leitura": "Cancelamento exige investigação.",
        },
        {
            "Critério": "Score Go/No-Go igual ou maior que 70",
            "Status": "OK" if scores["go_no_go"] >= 70 else "Pendente",
            "Leitura": "Maturidade mínima para novo lote ou automação leve.",
        },
    ]


def _gerar_alertas(
    clientes: List[Dict[str, str]],
    suporte: List[Dict[str, str]],
    retencao: List[Dict[str, str]],
    scores: Dict[str, int],
) -> List[str]:
    alertas = []

    if _clientes_pagos(clientes) == 0:
        alertas.append("Sem cliente pago confirmado. Foque em venda manual e validação de oferta.")

    if _tickets_criticos(suporte) > 0:
        alertas.append("Há tickets críticos. Corrigir suporte vem antes de vender mais.")

    if _tickets_abertos(suporte) > 3:
        alertas.append("Há muitos tickets abertos. A operação pode ficar pesada para um fundador solo.")

    risco_total = _clientes_em_risco_clientes(clientes) + _clientes_em_risco_retencao(retencao)

    if risco_total > 0:
        alertas.append("Há clientes em risco. A retenção deve ser priorizada.")

    if _cancelamentos(retencao) > 0:
        alertas.append("Há cancelamentos ou não renovações. Investigue a causa raiz.")

    if _nps_medio(retencao) < 7 and len(retencao) > 0:
        alertas.append("NPS abaixo de 7. O produto ainda precisa melhorar valor percebido.")

    if scores["automacao"] < 60 and scores["go_no_go"] < 85:
        alertas.append("Automação pesada ainda é cedo. Use automação leve apenas quando os sinais ficarem mais fortes.")

    if len(alertas) == 0:
        alertas.append("Nenhum alerta crítico. Ainda assim, mantenha crescimento controlado.")

    return alertas


def _gerar_tabela_historico(registros: List[Dict[str, str]]) -> List[Dict[str, str]]:
    tabela = []

    for registro in reversed(registros):
        tabela.append(
            {
                "Data": registro.get("data_registro", ""),
                "Decisão": registro.get("decisao", ""),
                "Classificação": registro.get("classificacao", ""),
                "Score": f"{registro.get('score_go_no_go', '')}/100",
                "Receita": _fmt_moeda(_safe_float(registro.get("receita_real"))),
                "MRR": _fmt_moeda(_safe_float(registro.get("mrr_estimado"))),
                "Clientes pagos": registro.get("clientes_pagos", ""),
                "NPS": f"{_safe_float(registro.get('nps_medio')):.1f}/10",
                "Críticos": registro.get("tickets_criticos", ""),
                "Prazo": registro.get("prazo", ""),
            }
        )

    return tabela


def _gerar_markdown_decisao(
    decisao: str,
    classificacao: str,
    scores: Dict[str, int],
    clientes: List[Dict[str, str]],
    suporte: List[Dict[str, str]],
    retencao: List[Dict[str, str]],
    racional: str,
    acoes: Dict[str, str],
) -> str:
    linhas_criterios = "\n".join(
        [
            f"| {item['Critério']} | {item['Status']} | {item['Leitura']} |"
            for item in _gerar_tabela_criterios(clientes, suporte, retencao, scores)
        ]
    )

    linhas_alertas = "\n".join(
        [
            f"- {alerta}"
            for alerta in _gerar_alertas(clientes, suporte, retencao, scores)
        ]
    )

    return f"""# Decisão Go/No-Go da Fase 3 — Máquina de Preço-Teto

Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}

## Decisão

**Decisão automática:** {decisao}  
**Classificação:** {classificacao}  
**Score Go/No-Go:** {scores["go_no_go"]}/100  

## Scores

- Receita: {scores["receita"]}/100
- Retenção: {scores["retencao"]}/100
- Suporte: {scores["suporte"]}/100
- Operacional: {scores["operacional"]}/100
- Automação: {scores["automacao"]}/100

## Indicadores

- Clientes pagos: {_clientes_pagos(clientes)}
- Clientes ativos: {_clientes_ativos(clientes)}
- Receita real: {_fmt_moeda(_receita_real(clientes))}
- MRR estimado: {_fmt_moeda(_mrr_estimado(clientes))}
- NPS médio: {_nps_medio(retencao):.1f}/10
- Tickets críticos: {_tickets_criticos(suporte)}
- Clientes em risco: {_clientes_em_risco_clientes(clientes) + _clientes_em_risco_retencao(retencao)}
- Cancelamentos/não renovação: {_cancelamentos(retencao)}
- Renovações: {_renovacoes(retencao)}

## Racional

{racional}

## Ações

**Ação primária:** {acoes["primaria"]}  
**Ação secundária:** {acoes["secundaria"]}  
**Prazo sugerido:** {acoes["prazo"]}  

## Critérios Go/No-Go

| Critério | Status | Leitura |
|---|---|---|
{linhas_criterios}

## Alertas

{linhas_alertas}

## Regra

A Fase 3 só avança quando venda, entrega, suporte e retenção caminham juntas.
"""


def _injetar_css_go_no_go() -> None:
    st.markdown(
        """
        <style>
            .gng-hero {
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

            .gng-eyebrow {
                color: #d6b56d;
                font-size: 0.78rem;
                letter-spacing: 0.13em;
                text-transform: uppercase;
                font-weight: 850;
                margin-bottom: 0.35rem;
            }

            .gng-title {
                color: #f4f7fb;
                font-size: 2.1rem;
                font-weight: 900;
                margin-bottom: 0.45rem;
                line-height: 1.14;
            }

            .gng-subtitle {
                color: rgba(244, 247, 251, 0.76);
                font-size: 1rem;
                line-height: 1.62;
                max-width: 1080px;
            }

            .gng-card {
                padding: 1.1rem 1.15rem;
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.035);
                box-shadow: 0 10px 35px rgba(0, 0, 0, 0.18);
                height: 100%;
            }

            .gng-card-label {
                color: rgba(244, 247, 251, 0.58);
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 800;
                margin-bottom: 0.35rem;
            }

            .gng-card-value {
                color: #f4f7fb;
                font-size: 1.22rem;
                font-weight: 850;
                margin-bottom: 0.25rem;
            }

            .gng-card-note {
                color: rgba(244, 247, 251, 0.68);
                font-size: 0.87rem;
                line-height: 1.47;
            }

            .gng-highlight {
                padding: 0.95rem 1rem;
                border-radius: 16px;
                border-left: 4px solid #d6b56d;
                background: rgba(214, 181, 109, 0.08);
                color: rgba(244, 247, 251, 0.82);
                font-size: 0.92rem;
                line-height: 1.55;
                margin-bottom: 0.7rem;
            }

            .gng-disclaimer {
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
        <div class="gng-card">
            <div class="gng-card-label">{label}</div>
            <div class="gng-card-value">{value}</div>
            <div class="gng-card-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def renderizar_go_no_go_fase3() -> None:
    """
    Renderiza a central de decisão Go/No-Go da Fase 3.
    """
    _injetar_css_go_no_go()

    clientes = _carregar_csv(CAMINHO_CLIENTES_BETA)
    suporte = _carregar_csv(CAMINHO_SUPORTE_BETA)
    retencao = _carregar_csv(CAMINHO_RETENCAO_BETA)
    metricas = _carregar_csv(CAMINHO_METRICAS_FASE3)
    historico_decisoes = carregar_decisoes_fase3()

    scores = _calcular_scores(clientes, suporte, retencao, metricas)
    classificacao = _classificar(scores["go_no_go"])
    decisao = _decisao_automatica(clientes, suporte, retencao, metricas, scores)
    racional = _racional_decisao(decisao, clientes, suporte, retencao, scores)
    acoes = _acoes_para_decisao(decisao)

    st.session_state["resultado_go_no_go_fase3"] = {
        "decisao": decisao,
        "classificacao": classificacao,
        "score_go_no_go": scores["go_no_go"],
        "score_receita": scores["receita"],
        "score_retencao": scores["retencao"],
        "score_suporte": scores["suporte"],
        "score_operacional": scores["operacional"],
        "score_automacao": scores["automacao"],
        "clientes_pagos": _clientes_pagos(clientes),
        "clientes_ativos": _clientes_ativos(clientes),
        "receita_real": _receita_real(clientes),
        "mrr_estimado": _mrr_estimado(clientes),
        "nps_medio": _nps_medio(retencao),
        "tickets_criticos": _tickets_criticos(suporte),
        "cancelamentos": _cancelamentos(retencao),
    }

    st.markdown(
        """
        <div class="gng-hero">
            <div class="gng-eyebrow">Fase 3.5 — Go/No-Go</div>
            <div class="gng-title">Decisão Go/No-Go para Escala, Automação e Próxima Fase</div>
            <div class="gng-subtitle">
                Transforme os dados de clientes, suporte, retenção e métricas em uma decisão objetiva:
                vender mais, pausar, corrigir, reter ou preparar automação.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="gng-highlight">
            O fundador disciplinado não escala no impulso. Ele escala quando os sinais de venda, entrega,
            suporte e retenção apontam na mesma direção.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Decisão executiva")

    col_1, col_2, col_3, col_4 = st.columns(4)

    with col_1:
        st.metric("Score Go/No-Go", f"{scores['go_no_go']}/100")

    with col_2:
        st.metric("Classificação", classificacao)

    with col_3:
        st.metric("Clientes pagos", _clientes_pagos(clientes))

    with col_4:
        st.metric("MRR estimado", _fmt_moeda(_mrr_estimado(clientes)))

    st.progress(scores["go_no_go"] / 100)

    if scores["go_no_go"] >= 70:
        st.success(decisao)
    elif scores["go_no_go"] >= 40:
        st.warning(decisao)
    else:
        st.error(decisao)

    st.info(racional)

    st.divider()

    st.markdown("### Scores por dimensão")

    col_s1, col_s2, col_s3, col_s4, col_s5 = st.columns(5)

    with col_s1:
        _card("Receita", f"{scores['receita']}/100", "Venda, receita e MRR.")

    with col_s2:
        _card("Retenção", f"{scores['retencao']}/100", "NPS, uso, valor e churn.")

    with col_s3:
        _card("Suporte", f"{scores['suporte']}/100", "Tickets e resolução.")

    with col_s4:
        _card("Operacional", f"{scores['operacional']}/100", "Entrega e carga operacional.")

    with col_s5:
        _card("Automação", f"{scores['automacao']}/100", "Prontidão para sistema profissional.")

    st.divider()

    st.markdown("### Indicadores usados na decisão")

    col_i1, col_i2, col_i3, col_i4 = st.columns(4)

    with col_i1:
        _card("Receita real", _fmt_moeda(_receita_real(clientes)), "Dinheiro confirmado.")

    with col_i2:
        _card("NPS médio", f"{_nps_medio(retencao):.1f}/10", "Valor percebido.")

    with col_i3:
        _card("Tickets críticos", str(_tickets_criticos(suporte)), "Travamento de escala.")

    with col_i4:
        _card("Clientes em risco", str(_clientes_em_risco_clientes(clientes) + _clientes_em_risco_retencao(retencao)), "Risco de churn.")

    col_i5, col_i6, col_i7, col_i8 = st.columns(4)

    with col_i5:
        _card("Clientes ativos", str(_clientes_ativos(clientes)), "Pagantes em entrega.")

    with col_i6:
        _card("Renovações", str(_renovacoes(retencao)), "Valor sustentado.")

    with col_i7:
        _card("Cancelamentos", str(_cancelamentos(retencao)), "Perda ou não renovação.")

    with col_i8:
        _card("Suporte aberto", str(_tickets_abertos(suporte)), "Fila operacional.")

    st.divider()

    st.markdown("### Critérios Go/No-Go")

    st.dataframe(
        _gerar_tabela_criterios(clientes, suporte, retencao, scores),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Alertas estratégicos")

    for alerta in _gerar_alertas(clientes, suporte, retencao, scores):
        st.markdown(f"- {alerta}")

    st.divider()

    st.markdown("### Plano recomendado")

    st.dataframe(
        [
            {
                "Ação": "Ação primária",
                "Descrição": acoes["primaria"],
                "Prazo": acoes["prazo"],
            },
            {
                "Ação": "Ação secundária",
                "Descrição": acoes["secundaria"],
                "Prazo": acoes["prazo"],
            },
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Registrar decisão executiva")

    with st.form("form_decisao_fase3"):
        decisao_manual = st.selectbox(
            "Decisão final",
            DECISOES_POSSIVEIS,
            index=DECISOES_POSSIVEIS.index(decisao) if decisao in DECISOES_POSSIVEIS else 0,
            key="gng_decisao_manual",
        )

        racional_manual = st.text_area(
            "Racional da decisão",
            value=racional,
            height=120,
            key="gng_racional",
        )

        col_a1, col_a2 = st.columns(2)

        with col_a1:
            acao_primaria = st.text_area(
                "Ação primária",
                value=acoes["primaria"],
                height=90,
                key="gng_acao_primaria",
            )

        with col_a2:
            acao_secundaria = st.text_area(
                "Ação secundária",
                value=acoes["secundaria"],
                height=90,
                key="gng_acao_secundaria",
            )

        prazo = st.text_input(
            "Prazo",
            value=acoes["prazo"],
            key="gng_prazo",
        )

        observacoes = st.text_area(
            "Observações",
            value="",
            height=90,
            key="gng_observacoes",
        )

        salvar = st.form_submit_button("Salvar decisão da Fase 3")

        if salvar:
            _registrar_decisao(
                decisao=decisao_manual,
                classificacao=classificacao,
                scores=scores,
                clientes=clientes,
                suporte=suporte,
                retencao=retencao,
                racional=racional_manual,
                acao_primaria=acao_primaria,
                acao_secundaria=acao_secundaria,
                prazo=prazo,
                observacoes=observacoes,
            )

            st.success("Decisão da Fase 3 registrada com sucesso.")
            st.rerun()

    st.divider()

    st.markdown("### Histórico de decisões")

    historico_decisoes = carregar_decisoes_fase3()

    if len(historico_decisoes) == 0:
        st.info("Nenhuma decisão registrada ainda.")
    else:
        st.dataframe(
            _gerar_tabela_historico(historico_decisoes),
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    col_download, col_limpar = st.columns(2)

    with col_download:
        st.download_button(
            label="Baixar relatório Go/No-Go (.md)",
            data=_gerar_markdown_decisao(
                decisao=decisao,
                classificacao=classificacao,
                scores=scores,
                clientes=clientes,
                suporte=suporte,
                retencao=retencao,
                racional=racional,
                acoes=acoes,
            ),
            file_name="relatorio_go_no_go_fase3.md",
            mime="text/markdown",
            key="download_go_no_go_fase3_md",
        )

        if CAMINHO_DECISOES_FASE3.exists():
            with open(CAMINHO_DECISOES_FASE3, "rb") as arquivo:
                st.download_button(
                    label="Baixar decisões em CSV",
                    data=arquivo,
                    file_name="decisoes_fase3.csv",
                    mime="text/csv",
                    key="download_decisoes_fase3_csv",
                )

    with col_limpar:
        confirmar = st.checkbox(
            "Confirmar limpeza do histórico de decisões",
            value=False,
            key="gng_confirmar_limpeza",
        )

        if st.button("Limpar decisões da Fase 3", key="gng_limpar"):
            if confirmar:
                limpar_decisoes_fase3()
                st.success("Histórico de decisões limpo com sucesso.")
                st.rerun()
            else:
                st.warning("Marque a confirmação antes de limpar.")

    st.markdown(
        """
        <div class="gng-disclaimer">
            <strong>Regra Go/No-Go:</strong> não avance para automação, aquisição ou nova stack
            enquanto venda, entrega, suporte e retenção não mostrarem sinais coerentes.
        </div>
        """,
        unsafe_allow_html=True,
    )