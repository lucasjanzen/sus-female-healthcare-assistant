import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID

from app.db.session import Base


class ConsultaRelato(Base):
    __tablename__ = "consulta_relato"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_consulta = Column(UUID(as_uuid=True), nullable=False, unique=True)
    relato_texto = Column(Text, nullable=True)
    parecer_medico = Column(Text, nullable=True)
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
