from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

_FIELD_LABELS: dict[str, str] = {
    # snake_case (nome interno do campo)
    "peso_kg": "Peso",
    "pa_sistolica": "PA sistólica",
    "pa_diastolica": "PA diastólica",
    "paciente_id": "Paciente",
    "tipo_consulta": "Tipo de consulta",
    "dum": "DUM",
    "relato_texto": "Relato",
    "conduta": "Conduta",
    "data_proximo_retorno": "Data de retorno",
    "encaminhamentos": "Encaminhamentos",
    "observacoes": "Observações",
    # camelCase (alias gerado pelo to_camel do Pydantic, aparece no loc)
    "pesoKg": "Peso",
    "paSistolica": "PA sistólica",
    "paDiastolica": "PA diastólica",
    "pacienteId": "Paciente",
    "tipoConsulta": "Tipo de consulta",
    "relatoTexto": "Relato",
    "dataProximoRetorno": "Data de retorno",
}


def _traduzir(error: dict) -> str:
    tipo = error.get("type", "")
    ctx = error.get("ctx", {})

    if tipo == "value_error":
        msg = error.get("msg", "Valor inválido")
        return msg.removeprefix("Value error, ")
    if tipo == "missing":
        return "Campo obrigatório"
    if tipo == "less_than_equal":
        return f"Deve ser no máximo {ctx.get('le')}"
    if tipo == "greater_than_equal":
        return f"Deve ser no mínimo {ctx.get('ge')}"
    if tipo == "less_than":
        return f"Deve ser menor que {ctx.get('lt')}"
    if tipo == "greater_than":
        return f"Deve ser maior que {ctx.get('gt')}"
    if tipo == "string_too_short":
        min_len = ctx.get("min_length")
        return f"Mínimo de {min_len} caractere{'s' if min_len != 1 else ''}"
    if tipo == "string_too_long":
        return f"Máximo de {ctx.get('max_length')} caracteres"
    if tipo in ("int_parsing", "int_type"):
        return "Deve ser um número inteiro"
    if tipo in ("float_parsing", "float_type"):
        return "Deve ser um número"
    if tipo in ("date_from_datetime_parsing", "date_parsing", "date_type"):
        return "Data inválida"

    return error.get("msg", "Valor inválido")


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    partes: list[str] = []
    for error in exc.errors():
        loc = error.get("loc", [])
        campo = str(loc[-1]) if loc else ""
        label = _FIELD_LABELS.get(campo, campo)
        msg = _traduzir(error)
        partes.append(f"{label}: {msg}" if label else msg)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": " • ".join(partes)},
    )
