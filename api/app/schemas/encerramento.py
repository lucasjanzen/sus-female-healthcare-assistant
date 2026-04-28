from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class VacinaAplicada(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    vacina: str
    lote: Optional[str] = None
    data_aplicacao: date


class Encaminhamento(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    destino: str
    motivo: str


class EncerramentoCreate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    orientacoes: list[str] = Field(..., min_length=1)
    vacinacao: Optional[list[VacinaAplicada]] = None
    data_proximo_retorno: date
    encaminhamentos: Optional[list[Encaminhamento]] = None
    cartao_gestante_atualizado: bool
    observacoes_finais: Optional[str] = None


class EncerramentoOut(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    id_consulta: UUID
    orientacoes: list[str]
    vacinacao: Optional[list[VacinaAplicada]] = None
    data_proximo_retorno: date
    data_proximo_retorno_sugerida: date
    encaminhamentos: Optional[list[Encaminhamento]] = None
    cartao_gestante_atualizado: bool
    observacoes_finais: Optional[str] = None
    encerrado_em: datetime


class SugestaoEncerramentoOut(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    data_proximo_retorno_sugerida: date
    orientacoes_recomendadas: list[str]


class ResumoPecOut(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id_consulta: UUID
    tipo_consulta: str
    data_consulta: date
    ig_semanas: Optional[int] = None
    ig_dias: Optional[int] = None
    peso_kg: float
    imc: float
    pa: str
    temperatura: str
    score_risco: int
    faixa_risco: str
    alertas_criticos: list[str]
    orientacoes: list[str]
    encaminhamentos: list[str]
    data_proximo_retorno: date
    gerado_em: datetime
