import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, SmallInteger, String
from sqlalchemy.dialects.postgresql import UUID

from app.db.session import Base


class Paciente(Base):
    __tablename__ = "pacientes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cpf_hash = Column(String(64), nullable=False, unique=True)
    cns = Column(String(20), nullable=True, unique=True)
    nome = Column(String(255), nullable=False)
    telefone = Column(String(20), nullable=False)
    email = Column(String(255), nullable=True)
    estado_civil = Column(String(20), nullable=False)
    data_nascimento = Column(Date, nullable=False)
    possui_filhos = Column(Boolean, nullable=False, default=False)
    quantidade_filhos = Column(SmallInteger, nullable=True)
    altura_cm = Column(SmallInteger, nullable=False)
    endereco = Column(String(500), nullable=True)
    ativo = Column(Boolean, nullable=False, default=True)
    criado_em = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    atualizado_em = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )


class PacienteLog(Base):
    __tablename__ = "pacientes_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paciente_id = Column(UUID(as_uuid=True), ForeignKey("pacientes.id"), nullable=False)
    atualizado_por = Column(UUID(as_uuid=True), nullable=False)
    atualizado_em = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
