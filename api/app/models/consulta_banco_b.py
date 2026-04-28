import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.db.session_b import BaseB


class ConsultaAudio(BaseB):
    __tablename__ = "consulta_audio"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_consulta = Column(UUID(as_uuid=True), nullable=False)
    tipo_audio = Column(String(30), nullable=False)
    duracao_segundos = Column(Integer, nullable=True)
    transcricao = Column(Text, nullable=True)
    status_processamento = Column(String(20), nullable=False, default="AGUARDANDO")
    criado_em = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    deletar_em = Column(DateTime(timezone=True), nullable=False)


class ConsultaResultado(BaseB):
    __tablename__ = "consulta_resultado"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_consulta = Column(UUID(as_uuid=True), nullable=False, unique=True)
    score_geral = Column(SmallInteger, nullable=False)
    faixa_risco = Column(String(10), nullable=False)
    score_psicossocial = Column(SmallInteger, nullable=False)
    score_audio = Column(SmallInteger, nullable=True)
    score_estruturado = Column(SmallInteger, nullable=False)
    alertas = Column(JSONB, nullable=False)
    resumo_encaminhamento = Column(Text, nullable=True)
    sugestao_conduta = Column(Text, nullable=True)
    transcricao_editada = Column(Text, nullable=True)
    calculado_em = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    confirmado_pelo_profissional = Column(Boolean, nullable=False, default=False)
    confirmado_em = Column(DateTime(timezone=True), nullable=True)
