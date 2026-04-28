import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, Date, DateTime, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.db.session import Base


class ConsultaEncerramento(Base):
    __tablename__ = "consulta_encerramento"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_consulta = Column(UUID(as_uuid=True), nullable=False, unique=True)
    orientacoes = Column(JSONB, nullable=False)
    vacinacao = Column(JSONB, nullable=True)
    data_proximo_retorno = Column(Date, nullable=False)
    data_proximo_retorno_sugerida = Column(Date, nullable=False)
    encaminhamentos = Column(JSONB, nullable=True)
    cartao_gestante_atualizado = Column(Boolean, nullable=False, default=False)
    observacoes_finais = Column(Text, nullable=True)
    encerrado_por = Column(UUID(as_uuid=True), nullable=False)
    encerrado_em = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
