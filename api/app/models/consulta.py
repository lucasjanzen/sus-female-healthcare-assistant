import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, Date, DateTime, String
from sqlalchemy.dialects.postgresql import UUID

from app.db.session import Base


class TipoConsultaEnum(str, enum.Enum):
    PRENATAL = "PRENATAL"
    GINECOLOGICA = "GINECOLOGICA"
    PUERPERIO = "PUERPERIO"
    PLANEJAMENTO_FAMILIAR = "PLANEJAMENTO_FAMILIAR"


class StatusConsultaEnum(str, enum.Enum):
    ABERTA = "ABERTA"
    EM_ATENDIMENTO = "EM_ATENDIMENTO"
    ENCERRADA = "ENCERRADA"


class ConsultaIdentidade(Base):
    __tablename__ = "consultas_identidade"

    id_consulta = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paciente_id = Column(UUID(as_uuid=True), nullable=False)
    profissional_id = Column(UUID(as_uuid=True), nullable=False)
    ubs_id = Column(UUID(as_uuid=True), nullable=True)
    estado_id = Column(String(10), nullable=True)
    tipo_consulta = Column(String(30), nullable=False)
    status = Column(String(20), nullable=False, default="ABERTA")
    dum = Column(Date, nullable=True)
    aberta_em = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    encerrada_em = Column(DateTime(timezone=True), nullable=True)
