from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from app.schemas.consulta import ResultadoIAOut


class AnaliseFilaItem(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id_consulta: UUID
    paciente_nome: str
    tipo_consulta: str
    ig_semanas: Optional[int] = None
    data_consulta: date
    score_geral: int
    faixa_risco: str
    indicadores_criticos: list[str]
    analise_concluida_em: datetime
    tem_erro: bool


class AnaliseFilaTotais(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    total: int
    criticos: int


class AnaliseResultadoOut(ResultadoIAOut):
    analise_revisada: bool = False
    analise_revisada_em: Optional[datetime] = None
    encaminhado: bool = False
    encaminhado_em: Optional[datetime] = None


class EncaminharRequest(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    observacao: Optional[str] = None


class EncerramentoSimplesOut(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id_consulta: UUID
    status: str
    mensagem: str
