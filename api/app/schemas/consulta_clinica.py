from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class RelatoCreate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    relato_texto: Optional[str] = None
    parecer_medico: Optional[str] = None


class RelatoOut(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    id_consulta: UUID
    relato_texto: Optional[str] = None
    parecer_medico: Optional[str] = None
    registrado_em: datetime
    atualizado_em: datetime


class AudioIniciarOut(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    audio_id: UUID
    status: str


class AudioStatusOut(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    audio_id: UUID
    status_processamento: str
    transcricao: Optional[str] = None


class ResultadoOut(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id_consulta: UUID
    score_geral: int
    faixa_risco: str
    indicadores: dict
    resumo_ia: Optional[str] = None
    confirmado: bool
    calculado_em: datetime
