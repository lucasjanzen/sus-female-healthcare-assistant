from typing import Optional
from uuid import UUID

from app.models.consulta import ConsultaTriagem
from app.models.consulta_banco_b import ConsultaAudio


def _faixa(score: int) -> str:
    if score <= 30:
        return "VERDE"
    if score <= 50:
        return "AMARELO"
    if score <= 75:
        return "LARANJA"
    return "VERMELHO"


def calcular_score(
    id_consulta: UUID,
    triagem: Optional[ConsultaTriagem],
    audio: Optional[ConsultaAudio],
) -> dict:
    score = 0
    indicadores: dict = {}

    if triagem:
        pa_sis = triagem.pa_sistolica
        pa_dia = triagem.pa_diastolica
        if pa_sis >= 140 or pa_dia >= 90:
            score += 30
            indicadores["pa_elevada"] = True
        elif pa_sis >= 130 or pa_dia >= 80:
            score += 10
            indicadores["pa_limiar"] = True
        indicadores["peso_kg"] = float(triagem.peso_kg)

    if audio and audio.status_processamento == "CONCLUIDO" and audio.transcricao:
        indicadores["audio_disponivel"] = True

    score_geral = min(score, 100)
    faixa = _faixa(score_geral)

    resumo_ia = None
    if faixa in ("LARANJA", "VERMELHO"):
        resumo_ia = f"Score de risco: {score_geral}/100 — Faixa {faixa}. Recomenda-se avaliação especializada."

    return {
        "score_geral": score_geral,
        "faixa_risco": faixa,
        "indicadores": indicadores,
        "resumo_ia": resumo_ia,
    }
