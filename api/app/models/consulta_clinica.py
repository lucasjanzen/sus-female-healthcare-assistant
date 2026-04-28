import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Numeric, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.db.session import Base


class ConsultaAnamnese(Base):
    __tablename__ = "consulta_anamnese"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_consulta = Column(UUID(as_uuid=True), nullable=False, unique=True)
    gestacoes = Column(SmallInteger, nullable=True)
    partos = Column(SmallInteger, nullable=True)
    abortos = Column(SmallInteger, nullable=True)
    doencas = Column(JSONB, nullable=True)
    medicamentos = Column(JSONB, nullable=True)
    situacao_moradia = Column(String(20), nullable=True)
    situacao_renda = Column(String(20), nullable=True)
    suporte_familiar = Column(String(20), nullable=True)
    historico_saude_mental = Column(Text, nullable=True)
    registrado_por = Column(UUID(as_uuid=True), nullable=False)
    registrado_em = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    atualizado_em = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class ConsultaExameFisico(Base):
    __tablename__ = "consulta_exame_fisico"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_consulta = Column(UUID(as_uuid=True), nullable=False, unique=True)
    altura_uterina_cm = Column(Numeric(4, 1), nullable=True)
    bcf_bpm = Column(SmallInteger, nullable=True)
    movimentacao_fetal = Column(String(20), nullable=True)
    edema_grau = Column(SmallInteger, nullable=True)
    edema_localizacao = Column(String(100), nullable=True)
    apresentacao_fetal = Column(String(20), nullable=True)
    registrado_por = Column(UUID(as_uuid=True), nullable=False)
    registrado_em = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    atualizado_em = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class ConsultaExamesLab(Base):
    __tablename__ = "consulta_exames_lab"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_consulta = Column(UUID(as_uuid=True), nullable=False, unique=True)
    hemograma = Column(JSONB, nullable=True)
    tipagem_sanguinea = Column(String(10), nullable=True)
    vdrl = Column(JSONB, nullable=True)
    glicemia_jejum = Column(JSONB, nullable=True)
    totg = Column(JSONB, nullable=True)
    urina = Column(JSONB, nullable=True)
    urocultura = Column(JSONB, nullable=True)
    hiv = Column(JSONB, nullable=True)
    hepatite_b = Column(JSONB, nullable=True)
    hepatite_c = Column(JSONB, nullable=True)
    toxoplasmose = Column(JSONB, nullable=True)
    usg_obstetrica = Column(JSONB, nullable=True)
    registrado_por = Column(UUID(as_uuid=True), nullable=False)
    registrado_em = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    atualizado_em = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class ConsultaRastreioPsicossocial(Base):
    __tablename__ = "consulta_rastreio_psicossocial"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_consulta = Column(UUID(as_uuid=True), nullable=False, unique=True)
    epds_respostas = Column(JSONB, nullable=False)
    epds_score = Column(SmallInteger, nullable=False)
    epds_flag = Column(Boolean, nullable=False)
    gad7_respostas = Column(JSONB, nullable=False)
    gad7_score = Column(SmallInteger, nullable=False)
    gad7_flag = Column(Boolean, nullable=False)
    hits_respostas = Column(JSONB, nullable=False)
    hits_score = Column(SmallInteger, nullable=False)
    hits_flag = Column(Boolean, nullable=False)
    situacao_social = Column(JSONB, nullable=False)
    registrado_por = Column(UUID(as_uuid=True), nullable=False)
    registrado_em = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    atualizado_em = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class ConsultaParecer(Base):
    __tablename__ = "consulta_parecer"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_consulta = Column(UUID(as_uuid=True), nullable=False, unique=True)
    parecer_texto = Column(Text, nullable=True)
    audio_parecer_id = Column(UUID(as_uuid=True), nullable=True)
    registrado_por = Column(UUID(as_uuid=True), nullable=False)
    registrado_em = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    atualizado_em = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
