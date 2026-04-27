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


class NivelAlertaEnum(str, enum.Enum):
    INFO = "INFO"
    ATENCAO = "ATENCAO"
    CRITICO = "CRITICO"


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
    tcle_assinado: bool


class TriagemCreate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    peso_kg: float = Field(..., ge=30, le=300)
    pa_sistolica: int = Field(..., ge=60, le=250)
    pa_diastolica: int = Field(..., ge=40, le=150)
    temperatura_c: float = Field(..., ge=34.0, le=42.0)
    queixas_texto: Optional[str] = None
    queixas_tags: Optional[list[str]] = None


class AlertaTriagem(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    tipo: str
    descricao: str
    nivel: str


class TriagemOut(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    peso_kg: float
    imc: float
    pa_sistolica: int
    pa_diastolica: int
    temperatura_c: float
    queixas_texto: Optional[str] = None
    queixas_tags: Optional[list[str]] = None
    alertas: list[AlertaTriagem] = []


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
    tcle_assinado: bool
    triagem_concluida: bool = False
    triagem: Optional[TriagemOut] = None
    aberta_em: datetime
    triagem_concluida_em: Optional[datetime] = None


# Alias para compatibilidade com código existente
ConsultaEtapa1Out = Etapa1Out


class ConsultaEtapa1Update(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    tipo_consulta: Optional[TipoConsultaEnum] = None
    dum: Optional[date] = None
