import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.db.session import Base


class AuditAcesso(Base):
    __tablename__ = "audit_acessos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    profissional_id = Column(UUID(as_uuid=True), nullable=False)
    unidade_id = Column(UUID(as_uuid=True), nullable=True)
    cpf_hash = Column(String(64), nullable=True)
    tipo_acesso = Column(String(50), nullable=False)
    justificativa = Column(Text, nullable=True)
