import enum
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator
from pydantic.alias_generators import to_camel


class EstadoCivilEnum(str, enum.Enum):
    SOLTEIRA = "SOLTEIRA"
    CASADA = "CASADA"
    DIVORCIADA = "DIVORCIADA"
    VIUVA = "VIUVA"
    UNIAO_ESTAVEL = "UNIAO_ESTAVEL"


class PacienteCreate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    cpf: str
    nome: str
    telefone: str
    email: Optional[str] = None
    estado_civil: EstadoCivilEnum
    data_nascimento: date
    possui_filhos: bool
    quantidade_filhos: Optional[int] = None
    altura_cm: int
    peso_kg: float
    endereco: Optional[str] = None

    @field_validator("cpf")
    @classmethod
    def cpf_apenas_digitos(cls, v: str) -> str:
        if not v.isdigit() or len(v) != 11:
            raise ValueError("CPF deve conter exatamente 11 dígitos")
        return v


class PacienteUpdate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    nome: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[str] = None
    estado_civil: Optional[EstadoCivilEnum] = None
    data_nascimento: Optional[date] = None
    possui_filhos: Optional[bool] = None
    quantidade_filhos: Optional[int] = None
    altura_cm: Optional[int] = None
    peso_kg: float
    endereco: Optional[str] = None


class PacienteOut(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    id: UUID
    nome: str
    telefone: str
    email: Optional[str] = None
    estado_civil: str
    data_nascimento: date
    possui_filhos: bool
    quantidade_filhos: Optional[int] = None
    altura_cm: int
    endereco: Optional[str] = None


class ConsultaIniciadaOut(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    paciente: PacienteOut
    id_consulta: UUID


class HistoricoPesoItem(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    peso_kg: float
    registrado_em: datetime
    id_consulta: UUID
