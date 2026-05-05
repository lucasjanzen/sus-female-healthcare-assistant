from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.db.session import get_db
from app.models.consulta import ConsultaIdentidade, ConsultaTriagem
from app.models.paciente import Paciente
from app.models.user import User
from app.schemas.consulta import (
    ConsultaIniciarOut,
    ConsultaIniciarRequest,
    Etapa1Out,
    PacienteConsultaOut,
    TriagemCreate,
)

from .helpers import _build_etapa1_out, _calcular_ig, _consulta_ou_404, _hash_cpf

router = APIRouter()


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
        pacientes = (
            db.query(Paciente)
            .filter(Paciente.cpf_hash == _hash_cpf(termo), Paciente.ativo.is_(True))
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
            id=p.id, nome=p.nome, data_nascimento=p.data_nascimento, cns=p.cns
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

    ig_semanas, ig_dias = _calcular_ig(payload.dum)
    consulta = ConsultaIdentidade(
        paciente_id=payload.paciente_id,
        profissional_id=current_user.id,
        ubs_id=getattr(current_user, "ubs_id", None),
        estado_id=getattr(current_user, "estado_id", None),
        tipo_consulta=payload.tipo_consulta.value,
        dum=payload.dum,
        ig_semanas=ig_semanas,
        ig_dias=ig_dias,
    )
    db.add(consulta)
    db.commit()
    db.refresh(consulta)
    return _build_etapa1_out(consulta, db)


@router.post(
    "/{id_consulta}/triagem", response_model=Etapa1Out, response_model_by_alias=True
)
def salvar_triagem(
    id_consulta: UUID,
    payload: TriagemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO", "ENFERMEIRO")),
):
    consulta = _consulta_ou_404(id_consulta, db)
    triagem = (
        db.query(ConsultaTriagem)
        .filter(ConsultaTriagem.id_consulta == id_consulta)
        .first()
    )
    if not triagem:
        triagem = ConsultaTriagem(
            id_consulta=id_consulta, registrado_por=current_user.id
        )
        db.add(triagem)
    triagem.peso_kg = payload.peso_kg
    triagem.pa_sistolica = payload.pa_sistolica
    triagem.pa_diastolica = payload.pa_diastolica
    consulta.triagem_concluida = True
    consulta.triagem_concluida_em = datetime.now(timezone.utc)
    db.commit()
    db.refresh(consulta)
    return _build_etapa1_out(consulta, db)


@router.get(
    "/{id_consulta}/triagem", response_model=Etapa1Out, response_model_by_alias=True
)
def obter_triagem(
    id_consulta: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO", "ENFERMEIRO")),
):
    return _build_etapa1_out(_consulta_ou_404(id_consulta, db), db)
