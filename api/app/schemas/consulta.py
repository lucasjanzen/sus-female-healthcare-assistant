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
    altura_cm: int


class ConsultaIniciarRequest(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    paciente_id: UUID
    tipo_consulta: TipoConsultaEnum
    dum: Optional[date] = None


class ConsultaIniciarOut(BaseModel):
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
    aberta_em: datetime
