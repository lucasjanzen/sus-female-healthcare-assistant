from app.schemas.consulta_clinica import RastreioCreate


def calcular_epds(respostas: dict[str, int]) -> tuple[int, bool]:
    score = sum(respostas.get(f"item_{i}", 0) for i in range(1, 11))
    return score, score >= 12


def calcular_gad7(respostas: dict[str, int]) -> tuple[int, bool]:
    score = sum(respostas.get(f"item_{i}", 0) for i in range(1, 8))
    return score, score >= 10


def calcular_hits(respostas: dict[str, int]) -> tuple[int, bool]:
    score = sum(respostas.get(f"item_{i}", 0) for i in range(1, 5))
    return score, score >= 11


def calcular_rastreio(payload: RastreioCreate) -> dict:
    epds_score, epds_flag = calcular_epds(payload.epds_respostas)
    gad7_score, gad7_flag = calcular_gad7(payload.gad7_respostas)
    hits_score, hits_flag = calcular_hits(payload.hits_respostas)

    return {
        "epds_score": epds_score,
        "epds_flag": epds_flag,
        "gad7_score": gad7_score,
        "gad7_flag": gad7_flag,
        "hits_score": hits_score,
        "hits_flag": hits_flag,
    }
