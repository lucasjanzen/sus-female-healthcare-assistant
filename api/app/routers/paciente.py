import hashlib
import uuid
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import require_role
from app.db.session import get_db
from app.models.paciente import ConsultaPeso, Paciente, PacienteLog
from app.models.user import User
from app.schemas.paciente import (
    ConsultaIniciadaOut,
    PacienteCreate,
    PacienteOut,
    PacienteUpdate,
)

router = APIRouter()


def _hash_cpf(cpf: str) -> str:
    return hashlib.sha256((cpf + settings.secret_salt).encode()).hexdigest()


@router.get("/buscar", response_model=list[PacienteOut], response_model_by_alias=True)
def buscar_pacientes(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO", "ENFERMEIRO")),
):
    termo = q.strip()
    if termo.isdigit() and len(termo) == 11:
        cpf_hash = _hash_cpf(termo)
        pacientes = (
            db.query(Paciente)
            .filter(Paciente.cpf_hash == cpf_hash, Paciente.ativo.is_(True))
            .all()
        )
    else:
        pacientes = (
            db.query(Paciente)
            .filter(Paciente.nome.ilike(f"%{termo}%"), Paciente.ativo.is_(True))
            .all()
        )
    return pacientes


@router.post(
    "",
    response_model=ConsultaIniciadaOut,
    status_code=201,
    response_model_by_alias=True,
)
def criar_paciente(
    payload: PacienteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO", "ENFERMEIRO")),
):
    cpf_hash = _hash_cpf(payload.cpf)

    if db.query(Paciente).filter(Paciente.cpf_hash == cpf_hash).first():
        raise HTTPException(
            status_code=409, detail="Paciente com este CPF já cadastrada"
        )

    paciente = Paciente(
        cpf_hash=cpf_hash,
        nome=payload.nome,
        telefone=payload.telefone,
        email=payload.email,
        estado_civil=payload.estado_civil.value,
        data_nascimento=payload.data_nascimento,
        possui_filhos=payload.possui_filhos,
        quantidade_filhos=payload.quantidade_filhos if payload.possui_filhos else None,
        altura_cm=payload.altura_cm,
        endereco=payload.endereco,
    )
    db.add(paciente)
    db.flush()

    id_consulta = uuid.uuid4()
    db.add(
        ConsultaPeso(
            id_consulta=id_consulta, paciente_id=paciente.id, peso_kg=payload.peso_kg
        )
    )
    db.commit()
    db.refresh(paciente)

    return ConsultaIniciadaOut(
        paciente=PacienteOut.model_validate(paciente),
        id_consulta=id_consulta,
    )


@router.put(
    "/{paciente_id}", response_model=ConsultaIniciadaOut, response_model_by_alias=True
)
def atualizar_paciente(
    paciente_id: UUID,
    payload: PacienteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO", "ENFERMEIRO")),
):
    paciente = (
        db.query(Paciente)
        .filter(Paciente.id == paciente_id, Paciente.ativo.is_(True))
        .first()
    )
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrada")

    update_data = payload.model_dump(exclude={"peso_kg"}, exclude_unset=True)
    for field, value in update_data.items():
        if field == "estado_civil" and value is not None:
            setattr(paciente, field, value.value if hasattr(value, "value") else value)
        else:
            setattr(paciente, field, value)

    if not paciente.possui_filhos:
        paciente.quantidade_filhos = None

    paciente.atualizado_em = datetime.now(timezone.utc)

    db.add(PacienteLog(paciente_id=paciente.id, atualizado_por=current_user.id))

    id_consulta = uuid.uuid4()
    db.add(
        ConsultaPeso(
            id_consulta=id_consulta, paciente_id=paciente.id, peso_kg=payload.peso_kg
        )
    )

    db.commit()
    db.refresh(paciente)

    return ConsultaIniciadaOut(
        paciente=PacienteOut.model_validate(paciente),
        id_consulta=id_consulta,
    )
