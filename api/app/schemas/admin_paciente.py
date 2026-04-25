import enum
from datetime import date, datetime
from typing import Generic, List, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator, model_validator
from pydantic.alias_generators import to_camel


class EstadoCivilEnum(str, enum.Enum):
    SOLTEIRA = "SOLTEIRA"
    CASADA = "CASADA"
    DIVORCIADA = "DIVORCIADA"
    VIUVA = "VIUVA"
    UNIAO_ESTAVEL = "UNIAO_ESTAVEL"


class PacienteAdminCreate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    cpf: str
    cns: Optional[str] = None
    nome: str
    data_nascimento: date
    telefone: str
    email: Optional[EmailStr] = None
    estado_civil: EstadoCivilEnum
    possui_filhos: bool
    quantidade_filhos: Optional[int] = None
    altura_cm: int
    endereco: Optional[str] = None

    @field_validator("cpf")
    @classmethod
    def cpf_apenas_digitos(cls, v: str) -> str:
        digits = "".join(c for c in v if c.isdigit())
        if len(digits) != 11:
            raise ValueError("CPF deve conter exatamente 11 dígitos")
        return digits

    @field_validator("cns")
    @classmethod
    def cns_digitos(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        digits = "".join(c for c in v if c.isdigit())
        if not (15 <= len(digits) <= 20):
            raise ValueError("CNS deve conter entre 15 e 20 dígitos")
        return digits

    @field_validator("nome")
    @classmethod
    def nome_minimo(cls, v: str) -> str:
        if len(v.strip()) < 3:
            raise ValueError("Nome deve ter no mínimo 3 caracteres")
        return v.strip()

    @field_validator("telefone")
    @classmethod
    def telefone_minimo(cls, v: str) -> str:
        digits = "".join(c for c in v if c.isdigit())
        if len(digits) < 10:
            raise ValueError("Telefone deve ter no mínimo 10 dígitos")
        return v

    @field_validator("altura_cm")
    @classmethod
    def altura_valida(cls, v: int) -> int:
        if not (100 <= v <= 250):
            raise ValueError("Altura deve ser entre 100 e 250 cm")
        return v

    @model_validator(mode="after")
    def filhos_consistente(self) -> "PacienteAdminCreate":
        if self.possui_filhos and self.quantidade_filhos is None:
            raise ValueError("quantidade_filhos é obrigatório quando possui_filhos é verdadeiro")
        if not self.possui_filhos:
            self.quantidade_filhos = None
        return self


class PacienteAdminUpdate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    cns: Optional[str] = None
    nome: Optional[str] = None
    data_nascimento: Optional[date] = None
    telefone: Optional[str] = None
    email: Optional[EmailStr] = None
    estado_civil: Optional[EstadoCivilEnum] = None
    possui_filhos: Optional[bool] = None
    quantidade_filhos: Optional[int] = None
    altura_cm: Optional[int] = None
    endereco: Optional[str] = None

    @field_validator("cns")
    @classmethod
    def cns_digitos(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        digits = "".join(c for c in v if c.isdigit())
        if not (15 <= len(digits) <= 20):
            raise ValueError("CNS deve conter entre 15 e 20 dígitos")
        return digits

    @field_validator("nome")
    @classmethod
    def nome_minimo(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if len(v.strip()) < 3:
            raise ValueError("Nome deve ter no mínimo 3 caracteres")
        return v.strip()

    @field_validator("telefone")
    @classmethod
    def telefone_minimo(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        digits = "".join(c for c in v if c.isdigit())
        if len(digits) < 10:
            raise ValueError("Telefone deve ter no mínimo 10 dígitos")
        return v

    @field_validator("altura_cm")
    @classmethod
    def altura_valida(cls, v: Optional[int]) -> Optional[int]:
        if v is None:
            return v
        if not (100 <= v <= 250):
            raise ValueError("Altura deve ser entre 100 e 250 cm")
        return v


class PacienteAdminOut(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    id: UUID
    cns: Optional[str] = None
    nome: str
    data_nascimento: date
    telefone: str
    email: Optional[str] = None
    estado_civil: str
    possui_filhos: bool
    quantidade_filhos: Optional[int] = None
    altura_cm: int
    endereco: Optional[str] = None
    ativo: bool
    criado_em: datetime
    atualizado_em: datetime


class PacienteListItem(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    id: UUID
    nome: str
    data_nascimento: date
    cns: Optional[str] = None
    ativo: bool


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    items: List[T]
    total: int
    page: int
    pages: int
