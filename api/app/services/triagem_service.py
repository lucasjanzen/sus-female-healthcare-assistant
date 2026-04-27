from app.schemas.consulta import AlertaTriagem, TriagemCreate


def gerar_alertas(
    dados: TriagemCreate,
    tipo_consulta: str,
    imc: float,
) -> list[AlertaTriagem]:
    alertas: list[AlertaTriagem] = []

    # Pressão arterial
    if dados.pa_sistolica >= 140 or dados.pa_diastolica >= 90:
        alertas.append(AlertaTriagem(
            tipo="PA_ELEVADA",
            nivel="CRITICO",
            descricao="Pressão arterial elevada — risco de pré-eclâmpsia.",
        ))
    elif dados.pa_sistolica >= 130 or dados.pa_diastolica >= 80:
        alertas.append(AlertaTriagem(
            tipo="PA_LIMIAR",
            nivel="ATENCAO",
            descricao="Pressão arterial no limiar — monitorar.",
        ))

    # Temperatura
    if dados.temperatura_c >= 39.0:
        alertas.append(AlertaTriagem(
            tipo="FEBRE_ALTA",
            nivel="CRITICO",
            descricao="Febre alta — avaliação imediata.",
        ))
    elif dados.temperatura_c >= 37.8:
        alertas.append(AlertaTriagem(
            tipo="FEBRE",
            nivel="ATENCAO",
            descricao="Temperatura acima do normal.",
        ))

    # IMC (calculado a partir da altura do cadastro)
    if imc < 18.5:
        alertas.append(AlertaTriagem(
            tipo="IMC_BAIXO",
            nivel="ATENCAO",
            descricao="IMC abaixo do recomendado.",
        ))
    elif imc > 30:
        alertas.append(AlertaTriagem(
            tipo="IMC_ELEVADO",
            nivel="ATENCAO",
            descricao="IMC elevado — monitorar ganho de peso.",
        ))

    # Tags de queixas
    tags = dados.queixas_tags or []
    if "SANGRAMENTO" in tags:
        alertas.append(AlertaTriagem(
            tipo="QUEIXA_SANGRAMENTO",
            nivel="CRITICO",
            descricao="Paciente relata sangramento — avaliação imediata.",
        ))
    if "MOVIMENTOS_FETAIS_REDUZIDOS" in tags and tipo_consulta == "PRENATAL":
        alertas.append(AlertaTriagem(
            tipo="QUEIXA_MF_REDUZIDOS",
            nivel="CRITICO",
            descricao="Redução dos movimentos fetais — avaliação imediata.",
        ))

    return alertas
