import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Numeric, SmallInteger, String
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
        default=lambda: datetime.now(timezone.utc),
    )
    atualizado_em = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class PacienteLog(Base):
    __tablename__ = "pacientes_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paciente_id = Column(UUID(as_uuid=True), ForeignKey("pacientes.id"), nullable=False)
    atualizado_por = Column(UUID(as_uuid=True), nullable=False)
    atualizado_em = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class ConsultaPeso(Base):
    __tablename__ = "consulta_peso"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_consulta = Column(UUID(as_uuid=True), nullable=False)
    paciente_id = Column(UUID(as_uuid=True), ForeignKey("pacientes.id"), nullable=False)
    peso_kg = Column(Numeric(5, 2), nullable=False)
    registrado_em = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
