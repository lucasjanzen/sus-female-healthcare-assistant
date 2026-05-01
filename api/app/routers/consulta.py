import hashlib

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import require_role
from app.db.session import get_db
from app.models.consulta import ConsultaIdentidade
from app.models.paciente import Paciente
from app.models.user import User
from app.schemas.consulta import (
    ConsultaIniciarOut,
    ConsultaIniciarRequest,
    PacienteConsultaOut,
)

router = APIRouter()


def _hash_cpf(cpf: str) -> str:
    return hashlib.sha256((cpf + settings.secret_salt).encode()).hexdigest()


def _build_consulta_out(consulta: ConsultaIdentidade) -> ConsultaIniciarOut:
    return ConsultaIniciarOut(
        id_consulta=consulta.id_consulta,
        paciente_id=consulta.paciente_id,
        tipo_consulta=consulta.tipo_consulta,
        status=consulta.status,
        dum=consulta.dum,
        aberta_em=consulta.aberta_em,
    )


@router.get(
    "/pacientes/buscar",
    response_model=list[PacienteConsultaOut],
    response_model_by_alias=True,
)
def buscar_pacientes_consulta(
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
    elif termo.isdigit() and 15 <= len(termo) <= 20:
        pacientes = (
            db.query(Paciente)
            .filter(Paciente.cns == termo, Paciente.ativo.is_(True))
            .all()
        )
    else:
        pacientes = (
            db.query(Paciente)
            .filter(Paciente.nome.ilike(f"%{termo}%"), Paciente.ativo.is_(True))
            .all()
        )

    return [
        PacienteConsultaOut(
            id=p.id,
            nome=p.nome,
            data_nascimento=p.data_nascimento,
            cns=p.cns,
            altura_cm=p.altura_cm,
        )
        for p in pacientes
    ]


@router.post(
    "/iniciar",
    response_model=ConsultaIniciarOut,
    status_code=201,
    response_model_by_alias=True,
)
def iniciar_consulta(
    payload: ConsultaIniciarRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO", "ENFERMEIRO")),
):
    paciente = (
        db.query(Paciente)
        .filter(Paciente.id == payload.paciente_id, Paciente.ativo.is_(True))
        .first()
    )
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente nao encontrada")

    consulta = ConsultaIdentidade(
        paciente_id=payload.paciente_id,
        profissional_id=current_user.id,
        ubs_id=getattr(current_user, "ubs_id", None),
        estado_id=getattr(current_user, "estado_id", None),
        tipo_consulta=payload.tipo_consulta.value,
        dum=payload.dum,
    )
    db.add(consulta)
    db.commit()
    db.refresh(consulta)
    return _build_consulta_out(consulta)
