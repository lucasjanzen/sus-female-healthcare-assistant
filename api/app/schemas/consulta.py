import enum
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
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

    @model_validator(mode="after")
    def validar_dum_prenatal(self):
        if self.tipo_consulta == TipoConsultaEnum.PRENATAL and self.dum is None:
            raise ValueError("DUM e obrigatoria para consulta pre-natal")
        return self


class TriagemCreate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    peso_kg: float = Field(..., ge=30, le=300)
    pa_sistolica: int = Field(..., ge=60, le=250)
    pa_diastolica: int = Field(..., ge=40, le=150)


class TriagemResumo(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    peso_kg: Optional[float] = None
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
    triagem_concluida: bool
    triagem: Optional[TriagemResumo] = None
    aberta_em: datetime
    triagem_concluida_em: Optional[datetime] = None


ConsultaIniciarOut = Etapa1Out


class RelatoCreate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    relato_texto: str = Field(..., min_length=20)


class RelatoUpdate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    relato_texto: Optional[str] = None
    parecer_medico: Optional[str] = None

    @field_validator("relato_texto")
    @classmethod
    def validar_relato(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and len(value.strip()) < 20:
            raise ValueError("Relato deve ter pelo menos 20 caracteres")
        return value

    @model_validator(mode="after")
    def validar_algum_campo(self):
        if self.relato_texto is None and self.parecer_medico is None:
            raise ValueError("Informe relato_texto ou parecer_medico")
        return self


class RelatoOut(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id_consulta: UUID
    relato_texto: Optional[str] = None
    parecer_medico: Optional[str] = None
    registrado_em: datetime
    atualizado_em: datetime


class IndicadorIA(BaseModel):
    tipo: str
    nivel: str
    descricao: str
    origem: str


class ResultadoIAOut(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id_consulta: UUID
    score_geral: int
    faixa_risco: str
    indicadores: list[IndicadorIA]
    resumo_ia: str
    status_audio: str = "AGUARDANDO"
    confirmado: bool
    calculado_em: datetime


class AudioIniciarOut(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    audio_id: UUID


class AudioStatusOut(BaseModel):
    status_processamento: str
    transcricao: Optional[str] = None
