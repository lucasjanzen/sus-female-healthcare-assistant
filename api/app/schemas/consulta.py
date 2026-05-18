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
            raise ValueError("DUM é obrigatória para consulta pré-natal")
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

    @field_validator("relato_texto")
    @classmethod
    def validar_relato(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and len(value.strip()) < 20:
            raise ValueError("Relato deve ter pelo menos 20 caracteres")
        return value


class RelatoOut(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id_consulta: UUID
    relato_texto: Optional[str] = None
    registrado_em: datetime
    atualizado_em: datetime


class IndicadorIA(BaseModel):
    tipo: str
    nivel: str
    descricao: str
    origem: str


class IndicadorRisco(BaseModel):
    tipo: str
    nivel: str
    evidencias: list[str]
    recomendacao: str


class SumarioEstruturado(BaseModel):
    indicadores: list[IndicadorRisco]
    score_geral: int
    faixa_risco: str
    pontos_atencao: list[str]
    encaminhamentos_sugeridos: list[str]
    contexto_historico: str
    modo_fallback: bool = False


class SentimentoVozScores(BaseModel):
    positivo: float
    negativo: float
    neutro: float


class SentimentoVozOut(BaseModel):
    dominante: str  # 'POSITIVO' | 'NEGATIVO' | 'NEUTRO'
    scores: SentimentoVozScores


class FontesUtilizadasOut(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    relato: bool = False
    transcricao: bool = False
    sentimento_voz: bool = False
    dados_consulta: bool = False
    historico: bool = False


class ResultadoIAOut(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id_consulta: Optional[UUID] = None
    score_geral: int
    faixa_risco: str
    indicadores: list[IndicadorIA]
    resumo_ia: str
    calculado_em: datetime
    transcricao_audio: Optional[str] = None
    sentimento_voz: Optional[SentimentoVozOut] = None
    sumario_estruturado: Optional[SumarioEstruturado] = None
    texto_clinico: Optional[str] = None
    fontes_utilizadas: Optional[FontesUtilizadasOut] = None
    tokens_utilizados: Optional[int] = None
    prompt_enviado: Optional[str] = None
    resposta_bruta_llm: Optional[str] = None
