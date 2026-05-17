from datetime import date, timedelta
from typing import Optional

_DIAS_RETORNO_FAIXA: dict[str, int] = {
    "VERDE": 30,
    "AMARELO": 14,
    "LARANJA": 7,
    "VERMELHO": 2,
}

_ENCAMINHAMENTOS_FAIXA: dict[str, list[str]] = {
    "LARANJA": ["PSICOLOGIA", "ASSISTENCIA_SOCIAL"],
    "VERMELHO": ["CAPS", "CVR", "ASSISTENCIA_SOCIAL"],
}


def calcular_data_sugerida(faixa_risco: str, ig_semanas: Optional[int]) -> date:
    dias = _DIAS_RETORNO_FAIXA.get(faixa_risco, 30)
    if ig_semanas is not None:
        if ig_semanas < 28:
            max_ig = 28
        elif ig_semanas <= 36:
            max_ig = 14
        else:
            max_ig = 7
        dias = min(dias, max_ig)
    return date.today() + timedelta(days=dias)


def encaminhamentos_sugeridos(faixa_risco: str) -> list[str]:
    return list(_ENCAMINHAMENTOS_FAIXA.get(faixa_risco, []))
