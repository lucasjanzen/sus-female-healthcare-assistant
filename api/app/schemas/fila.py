from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from app.schemas.consulta import TriagemResumo


class ConsultaFilaItem(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id_consulta: UUID
    paciente_nome: str
    paciente_data_nascimento: date
    tipo_consulta: str
    ig_semanas: Optional[int] = None
    ig_dias: Optional[int] = None
    triagem_concluida_em: datetime


class ConsultaAssumidaOut(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id_consulta: UUID
    paciente_nome: str
    paciente_data_nascimento: date
    tipo_consulta: str
    ig_semanas: Optional[int] = None
    ig_dias: Optional[int] = None
    triagem_resumo: TriagemResumo
    assumida_em: datetime
