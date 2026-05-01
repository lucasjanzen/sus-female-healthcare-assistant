from app.schemas.consulta import TriagemCreate


def gerar_alertas(dados: TriagemCreate) -> list[dict]:
    alertas: list[dict] = []

    if dados.pa_sistolica >= 140 or dados.pa_diastolica >= 90:
        alertas.append({
            "tipo": "PA_ELEVADA",
            "nivel": "CRITICO",
            "descricao": "Pressão arterial elevada — risco de pré-eclâmpsia.",
        })
    elif dados.pa_sistolica >= 130 or dados.pa_diastolica >= 80:
        alertas.append({
            "tipo": "PA_LIMIAR",
            "nivel": "ATENCAO",
            "descricao": "Pressão arterial no limiar — monitorar.",
        })

    return alertas
