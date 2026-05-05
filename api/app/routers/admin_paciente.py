import hashlib
import math
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import require_role
from app.db.session import get_db
from app.models.paciente import Paciente, PacienteLog
from app.models.user import User
from app.schemas.admin_paciente import (
    PacienteAdminCreate,
    PacienteAdminOut,
    PacienteAdminUpdate,
    PacienteListItem,
    PaginatedResponse,
)

router = APIRouter()


def _hash_cpf(cpf: str) -> str:
    return hashlib.sha256((cpf + settings.secret_salt).encode()).hexdigest()


@router.get(
    "/buscar", response_model=list[PacienteListItem], response_model_by_alias=True
)
def buscar_pacientes(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    _: User = Depends(require_role("ADMIN")),
):
    termo = q.strip()
    query = db.query(Paciente)

    if termo.isdigit() and len(termo) == 11:
        cpf_hash = _hash_cpf(termo)
        query = query.filter(Paciente.cpf_hash == cpf_hash)
    elif termo.isdigit() and 15 <= len(termo) <= 20:
        query = query.filter(Paciente.cns == termo)
    else:
        query = query.filter(Paciente.nome.ilike(f"%{termo}%"))

    pacientes = query.order_by(Paciente.nome).all()
    return [PacienteListItem.model_validate(p) for p in pacientes]


@router.get(
    "", response_model=PaginatedResponse[PacienteListItem], response_model_by_alias=True
)
def listar_pacientes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    nome: str | None = Query(None),
    ativo: bool | None = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(require_role("ADMIN")),
):
    query = db.query(Paciente)

    if nome:
        query = query.filter(Paciente.nome.ilike(f"%{nome}%"))
    if ativo is not None:
        query = query.filter(Paciente.ativo.is_(ativo))

    total = query.count()
    pages = max(1, math.ceil(total / page_size))
    items = (
        query.order_by(Paciente.nome)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return PaginatedResponse[PacienteListItem](
        items=[PacienteListItem.model_validate(p) for p in items],
        total=total,
        page=page,
        pages=pages,
    )


@router.get(
    "/{paciente_id}", response_model=PacienteAdminOut, response_model_by_alias=True
)
def obter_paciente(
    paciente_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("ADMIN")),
):
    paciente = db.query(Paciente).filter(Paciente.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrada")
    return PacienteAdminOut.model_validate(paciente)


@router.post(
    "", response_model=PacienteAdminOut, status_code=201, response_model_by_alias=True
)
def criar_paciente(
    payload: PacienteAdminCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("ADMIN")),
):
    cpf_hash = _hash_cpf(payload.cpf)

    if db.query(Paciente).filter(Paciente.cpf_hash == cpf_hash).first():
        raise HTTPException(
            status_code=409, detail="Paciente com este CPF já cadastrada"
        )

    if payload.cns and db.query(Paciente).filter(Paciente.cns == payload.cns).first():
        raise HTTPException(
            status_code=409, detail="Paciente com este CNS já cadastrada"
        )

    paciente = Paciente(
        cpf_hash=cpf_hash,
        cns=payload.cns,
        nome=payload.nome,
        data_nascimento=payload.data_nascimento,
        telefone=payload.telefone,
        email=payload.email,
        estado_civil=payload.estado_civil.value,
        possui_filhos=payload.possui_filhos,
        quantidade_filhos=payload.quantidade_filhos if payload.possui_filhos else None,
        altura_cm=payload.altura_cm,
        endereco=payload.endereco,
    )
    db.add(paciente)
    db.commit()
    db.refresh(paciente)

    return PacienteAdminOut.model_validate(paciente)


@router.put(
    "/{paciente_id}", response_model=PacienteAdminOut, response_model_by_alias=True
)
def atualizar_paciente(
    paciente_id: UUID,
    payload: PacienteAdminUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN")),
):
    paciente = db.query(Paciente).filter(Paciente.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrada")

    if payload.cns and payload.cns != paciente.cns:
        conflito = (
            db.query(Paciente)
            .filter(Paciente.cns == payload.cns, Paciente.id != paciente_id)
            .first()
        )
        if conflito:
            raise HTTPException(status_code=409, detail="Este CNS já está em uso")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "estado_civil" and value is not None:
            setattr(paciente, field, value.value if hasattr(value, "value") else value)
        else:
            setattr(paciente, field, value)

    possui_filhos = update_data.get("possui_filhos", paciente.possui_filhos)
    if not possui_filhos:
        paciente.quantidade_filhos = None

    paciente.atualizado_em = datetime.now(timezone.utc)

    db.add(PacienteLog(paciente_id=paciente.id, atualizado_por=current_user.id))
    db.commit()
    db.refresh(paciente)

    return PacienteAdminOut.model_validate(paciente)


@router.delete("/{paciente_id}", status_code=204)
def desativar_paciente(
    paciente_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN")),
):
    paciente = db.query(Paciente).filter(Paciente.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrada")

    paciente.ativo = False
    paciente.atualizado_em = datetime.now(timezone.utc)

    db.add(PacienteLog(paciente_id=paciente.id, atualizado_por=current_user.id))
    db.commit()
