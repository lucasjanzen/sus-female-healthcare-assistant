from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


# ── Anamnese ─────────────────────────────────────────────────────────────────

class MedicamentoItem(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    nome: str
    dose: Optional[str] = None
    frequencia: Optional[str] = None


class AnamneseCreate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    gestacoes: Optional[int] = Field(None, ge=0, le=20)
    partos: Optional[int] = Field(None, ge=0, le=20)
    abortos: Optional[int] = Field(None, ge=0, le=20)
    doencas: Optional[list[str]] = None
    medicamentos: Optional[list[MedicamentoItem]] = None
    situacao_moradia: Optional[str] = None
    situacao_renda: Optional[str] = None
    suporte_familiar: Optional[str] = None
    historico_saude_mental: Optional[str] = None


class AnamneseOut(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    id_consulta: UUID
    gestacoes: Optional[int] = None
    partos: Optional[int] = None
    abortos: Optional[int] = None
    doencas: Optional[list[str]] = None
    medicamentos: Optional[list[Any]] = None
    situacao_moradia: Optional[str] = None
    situacao_renda: Optional[str] = None
    suporte_familiar: Optional[str] = None
    historico_saude_mental: Optional[str] = None
    registrado_em: datetime
    atualizado_em: datetime


# ── Exame Físico ─────────────────────────────────────────────────────────────

class ExameFisicoCreate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    altura_uterina_cm: Optional[float] = Field(None, ge=0, le=50)
    bcf_bpm: Optional[int] = Field(None, ge=50, le=220)
    movimentacao_fetal: Optional[str] = None
    edema_grau: Optional[int] = Field(None, ge=0, le=4)
    edema_localizacao: Optional[str] = None
    apresentacao_fetal: Optional[str] = None


class AlertaExame(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    tipo: str
    descricao: str
    nivel: str


class ExameFisicoOut(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    id_consulta: UUID
    altura_uterina_cm: Optional[float] = None
    bcf_bpm: Optional[int] = None
    movimentacao_fetal: Optional[str] = None
    edema_grau: Optional[int] = None
    edema_localizacao: Optional[str] = None
    apresentacao_fetal: Optional[str] = None
    alertas: list[AlertaExame] = []
    registrado_em: datetime
    atualizado_em: datetime


# ── Exames Laboratoriais ──────────────────────────────────────────────────────

class ExamesLabCreate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    hemograma: Optional[Any] = None
    tipagem_sanguinea: Optional[str] = None
    vdrl: Optional[Any] = None
    glicemia_jejum: Optional[Any] = None
    totg: Optional[Any] = None
    urina: Optional[Any] = None
    urocultura: Optional[Any] = None
    hiv: Optional[Any] = None
    hepatite_b: Optional[Any] = None
    hepatite_c: Optional[Any] = None
    toxoplasmose: Optional[Any] = None
    usg_obstetrica: Optional[Any] = None


class ExamesLabOut(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    id_consulta: UUID
    hemograma: Optional[Any] = None
    tipagem_sanguinea: Optional[str] = None
    vdrl: Optional[Any] = None
    glicemia_jejum: Optional[Any] = None
    totg: Optional[Any] = None
    urina: Optional[Any] = None
    urocultura: Optional[Any] = None
    hiv: Optional[Any] = None
    hepatite_b: Optional[Any] = None
    hepatite_c: Optional[Any] = None
    toxoplasmose: Optional[Any] = None
    usg_obstetrica: Optional[Any] = None
    registrado_em: datetime
    atualizado_em: datetime


# ── Rastreio Psicossocial ─────────────────────────────────────────────────────

class RastreioCreate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    epds_respostas: dict[str, int] = Field(..., description="item_1..item_10, valores 0-3")
    gad7_respostas: dict[str, int] = Field(..., description="item_1..item_7, valores 0-3")
    hits_respostas: dict[str, int] = Field(..., description="item_1..item_4, valores 1-5")
    situacao_social: dict[str, bool] = Field(..., description="item_1..item_6, booleanos")


class RastreioOut(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    id_consulta: UUID
    epds_respostas: dict[str, int]
    epds_score: int
    epds_flag: bool
    gad7_respostas: dict[str, int]
    gad7_score: int
    gad7_flag: bool
    hits_respostas: dict[str, int]
    hits_score: int
    hits_flag: bool
    situacao_social: dict[str, bool]
    registrado_em: datetime
    atualizado_em: datetime


# ── Parecer ───────────────────────────────────────────────────────────────────

class ParecerCreate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    parecer_texto: Optional[str] = None
    audio_parecer_id: Optional[UUID] = None


class ParecerOut(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    id_consulta: UUID
    parecer_texto: Optional[str] = None
    audio_parecer_id: Optional[UUID] = None
    registrado_em: datetime
    atualizado_em: datetime


# ── Áudio ─────────────────────────────────────────────────────────────────────

class AudioIniciarOut(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    audio_id: UUID
    status: str


class AudioStatusOut(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    audio_id: UUID
    status_processamento: str
    transcricao: Optional[str] = None
    duracao_segundos: Optional[int] = None


# ── Resultado / Score ─────────────────────────────────────────────────────────

class AlertaResultado(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    tipo: str
    descricao: str
    nivel: str
    origem: str


class ResultadoOut(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id_consulta: UUID
    score_geral: int
    faixa_risco: str
    score_psicossocial: int
    score_audio: Optional[int] = None
    score_estruturado: int
    alertas: list[AlertaResultado]
    resumo_encaminhamento: Optional[str] = None
    sugestao_conduta: Optional[str] = None
    transcricao: Optional[str] = None
    transcricao_editada: Optional[str] = None
    status_audio: str
    confirmado: bool
    calculado_em: datetime


class TranscricaoEditadaUpdate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    transcricao_editada: str
