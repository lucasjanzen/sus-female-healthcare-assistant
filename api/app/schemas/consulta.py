import enum
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class TipoConsultaEnum(str, enum.Enum):
    PRENATAL = "PRENATAL"
    GINECOLOGICA = "GINECOLOGICA"
    PUERPERIO = "PUERPERIO"
    PLANEJAMENTO_FAMILIAR = "PLANEJAMENTO_FAMILIAR"


class PacienteConsultaOut(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    id: UUID
    nome: str
    data_nascimento: date
    cns: Optional[str] = None


class ConsultaIniciarRequest(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    paciente_id: UUID
    tipo_consulta: TipoConsultaEnum
    dum: Optional[date] = None
    tcle_assinado: bool


class ConsultaEtapa1Out(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    id_consulta: UUID
    paciente_id: UUID
    tipo_consulta: str
    status: str
    dum: Optional[date] = None
    ig_semanas: Optional[int] = None
    ig_dias: Optional[int] = None
    tcle_assinado: bool
    aberta_em: datetime


class ConsultaEtapa1Update(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    tipo_consulta: Optional[TipoConsultaEnum] = None
    dum: Optional[date] = None
