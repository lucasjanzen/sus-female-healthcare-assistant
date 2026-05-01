from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class EncerramentoCreate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    conduta: str = Field(..., min_length=1)
    encaminhamentos: Optional[list[str]] = None
    data_proximo_retorno: date
    observacoes: Optional[str] = None


class EncerramentoOut(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    id_consulta: UUID
    conduta: str
    encaminhamentos: Optional[list[str]] = None
    data_proximo_retorno: date
    observacoes: Optional[str] = None
    encerrado_em: datetime


class ResumoPecOut(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id_consulta: UUID
    tipo_consulta: str
    data_consulta: date
    ig_semanas: Optional[int] = None
    ig_dias: Optional[int] = None
    peso_kg: Optional[float] = None
    pa: Optional[str] = None
    score_risco: Optional[int] = None
    faixa_risco: Optional[str] = None
    conduta: str
    encaminhamentos: list[str] = []
    data_proximo_retorno: date
    gerado_em: datetime
