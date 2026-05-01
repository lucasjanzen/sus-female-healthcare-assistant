import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.db.session import Base


class ConsultaAudio(Base):
    __tablename__ = "consulta_audio"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_consulta = Column(UUID(as_uuid=True), nullable=False)
    transcricao = Column(Text, nullable=True)
    status_processamento = Column(String(20), nullable=False, default="AGUARDANDO")
    criado_em = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    deletar_em = Column(DateTime(timezone=True), nullable=False)


class ConsultaResultado(Base):
    __tablename__ = "consulta_resultado"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_consulta = Column(UUID(as_uuid=True), nullable=False, unique=True)
    score_geral = Column(SmallInteger, nullable=False)
    faixa_risco = Column(String(10), nullable=False)
    indicadores = Column(JSONB, nullable=False)
    resumo_ia = Column(Text, nullable=True)
    calculado_em = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    confirmado = Column(Boolean, nullable=False, default=False)
    confirmado_em = Column(DateTime(timezone=True), nullable=True)
