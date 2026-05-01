import enum
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
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


class TriagemCreate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    peso_kg: float = Field(..., ge=30, le=300)
    pa_sistolica: int = Field(..., ge=60, le=250)
    pa_diastolica: int = Field(..., ge=40, le=150)


class TriagemOut(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    peso_kg: float
    pa_sistolica: int
    pa_diastolica: int


class Etapa1Out(BaseModel):
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
    triagem_concluida: bool = False
    triagem: Optional[TriagemOut] = None
    aberta_em: datetime
    triagem_concluida_em: Optional[datetime] = None


ConsultaEtapa1Out = Etapa1Out


class ConsultaEtapa1Update(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    tipo_consulta: Optional[TipoConsultaEnum] = None
    dum: Optional[date] = None
