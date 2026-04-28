from datetime import date, timedelta
from typing import Optional

_ORIENTACOES_POR_FAIXA: dict[str, list[str]] = {
    "VERDE": ["NUTRICAO", "RETORNO_CONSULTA"],
    "AMARELO": ["NUTRICAO", "RETORNO_CONSULTA", "VACINACAO", "SINAIS_ALARME"],
    "LARANJA": [
        "NUTRICAO", "RETORNO_CONSULTA", "VACINACAO", "SINAIS_ALARME",
        "SAUDE_MENTAL", "SUPORTE_SOCIAL",
    ],
    "VERMELHO": [
        "NUTRICAO", "RETORNO_CONSULTA", "VACINACAO", "SINAIS_ALARME",
        "SAUDE_MENTAL", "SUPORTE_SOCIAL", "VIOLENCIA_DOMESTICA",
    ],
}


def calcular_data_sugerida(
    ig_semanas: Optional[int],
    faixa_risco: str,
    data_base: date,
) -> date:
    if ig_semanas is None:
        prazo_dias = 30
    elif ig_semanas < 28:
        prazo_dias = 28
    elif ig_semanas <= 36:
        prazo_dias = 14
    else:
        prazo_dias = 7

    if faixa_risco == "AMARELO":
        prazo_dias = prazo_dias // 2
    elif faixa_risco == "LARANJA":
        prazo_dias = min(prazo_dias, 7)
    elif faixa_risco == "VERMELHO":
        prazo_dias = min(prazo_dias, 2)

    return data_base + timedelta(days=max(1, prazo_dias))


def orientacoes_recomendadas(faixa_risco: str) -> list[str]:
    return _ORIENTACOES_POR_FAIXA.get(faixa_risco, ["RETORNO_CONSULTA"])
