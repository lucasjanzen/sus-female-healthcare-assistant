import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, Date, DateTime, Integer, JSON, Numeric, SmallInteger, String, Text
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
    ig_semanas = Column(SmallInteger, nullable=True)
    ig_dias = Column(SmallInteger, nullable=True)
    triagem_concluida = Column(Boolean, nullable=False, default=False)
    triagem_concluida_em = Column(DateTime(timezone=True), nullable=True)
    medico_id = Column(UUID(as_uuid=True), nullable=True)
    assumida_em = Column(DateTime(timezone=True), nullable=True)
    aberta_em = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    encerrada_em = Column(DateTime(timezone=True), nullable=True)
    analise_concluida_em = Column(DateTime(timezone=True), nullable=True)
    analise_erro = Column(Text, nullable=True)
    analise_revisada = Column(Boolean, nullable=False, default=False)
    analise_revisada_em = Column(DateTime(timezone=True), nullable=True)
    analise_revisada_por = Column(UUID(as_uuid=True), nullable=True)
    encaminhado = Column(Boolean, nullable=False, default=False)
    encaminhado_em = Column(DateTime(timezone=True), nullable=True)
    encaminhado_por = Column(UUID(as_uuid=True), nullable=True)


class ConsultaTriagem(Base):
    __tablename__ = "consulta_triagem"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_consulta = Column(UUID(as_uuid=True), nullable=False, unique=True)
    peso_kg = Column(Numeric(5, 2), nullable=False)
    pa_sistolica = Column(SmallInteger, nullable=False)
    pa_diastolica = Column(SmallInteger, nullable=False)
    registrado_por = Column(UUID(as_uuid=True), nullable=False)
    registrado_em = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


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


class ConsultaResultado(Base):
    __tablename__ = "consulta_resultado"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_consulta = Column(UUID(as_uuid=True), nullable=False, unique=True)
    score_geral = Column(SmallInteger, nullable=False)
    faixa_risco = Column(String(20), nullable=False)
    indicadores = Column(JSON, nullable=False)
    resumo_ia = Column(Text, nullable=True)
    sentimento_voz = Column(JSON, nullable=True)
    calculado_em = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    confirmado = Column(Boolean, nullable=False, default=False)
    confirmado_em = Column(DateTime(timezone=True), nullable=True)
    sumario_estruturado = Column(JSON, nullable=True)
    texto_clinico = Column(Text, nullable=True)
    fontes_utilizadas = Column(JSON, nullable=True)
    tokens_utilizados = Column(Integer, nullable=True)
    prompt_enviado = Column(Text, nullable=True)
    resposta_bruta_llm = Column(Text, nullable=True)


class ConsultaEncerramento(Base):
    __tablename__ = "consulta_encerramento"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_consulta = Column(UUID(as_uuid=True), nullable=False, unique=True)
    conduta = Column(Text, nullable=False)
    encaminhamentos = Column(JSON, nullable=True)
    data_proximo_retorno = Column(Date, nullable=False)
    observacoes = Column(Text, nullable=True)
    encerrado_por = Column(UUID(as_uuid=True), nullable=False)
    encerrado_em = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class HistoricoPeso(Base):
    __tablename__ = "historico_peso"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paciente_id = Column(UUID(as_uuid=True), nullable=False)
    id_consulta = Column(UUID(as_uuid=True), nullable=False, unique=True)
    peso_kg = Column(Numeric(5, 2), nullable=False)
    registrado_em = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
