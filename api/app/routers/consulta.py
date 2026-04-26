import hashlib
from datetime import date, datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import require_role
from app.db.session import get_db
from app.models.consulta import ConsultaIdentidade, ConsultaTcleLog
from app.models.paciente import Paciente
from app.models.user import User
from app.schemas.consulta import (
    ConsultaEtapa1Out,
    ConsultaEtapa1Update,
    ConsultaIniciarRequest,
    PacienteConsultaOut,
)

router = APIRouter()


def _hash_cpf(cpf: str) -> str:
    return hashlib.sha256((cpf + settings.secret_salt).encode()).hexdigest()


def _calcular_ig(dum: date) -> tuple[int, int]:
    diff = (date.today() - dum).days
    return diff // 7, diff % 7


# ── Busca de pacientes para contexto de consulta ─────────────────────────────

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
        )
        for p in pacientes
    ]


# ── Iniciar consulta (Etapa 1) ────────────────────────────────────────────────

@router.post(
    "/iniciar",
    response_model=ConsultaEtapa1Out,
    status_code=201,
    response_model_by_alias=True,
)
def iniciar_consulta(
    payload: ConsultaIniciarRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO", "ENFERMEIRO")),
):
    if not payload.tcle_assinado:
        raise HTTPException(
            status_code=422,
            detail="O TCLE deve ser assinado para iniciar a consulta",
        )

    paciente = (
        db.query(Paciente)
        .filter(Paciente.id == payload.paciente_id, Paciente.ativo.is_(True))
        .first()
    )
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrada")

    ig_semanas = ig_dias = None
    if payload.dum:
        ig_semanas, ig_dias = _calcular_ig(payload.dum)

    agora = datetime.now(timezone.utc)

    consulta = ConsultaIdentidade(
        paciente_id=payload.paciente_id,
        profissional_id=current_user.id,
        tipo_consulta=payload.tipo_consulta.value,
        dum=payload.dum,
        ig_semanas=ig_semanas,
        ig_dias=ig_dias,
        tcle_assinado=True,
        tcle_assinado_em=agora,
    )
    db.add(consulta)
    db.flush()

    ip = request.client.host if request.client else None
    db.add(
        ConsultaTcleLog(
            id_consulta=consulta.id_consulta,
            paciente_id=payload.paciente_id,
            profissional_id=current_user.id,
            ip_origem=ip,
        )
    )

    db.commit()
    db.refresh(consulta)
    return ConsultaEtapa1Out.model_validate(consulta)


# ── Obter Etapa 1 ─────────────────────────────────────────────────────────────

@router.get(
    "/{id_consulta}/etapa1",
    response_model=ConsultaEtapa1Out,
    response_model_by_alias=True,
)
def obter_etapa1(
    id_consulta: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO", "ENFERMEIRO")),
):
    consulta = (
        db.query(ConsultaIdentidade)
        .filter(ConsultaIdentidade.id_consulta == id_consulta)
        .first()
    )
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta não encontrada")
    if consulta.profissional_id != current_user.id:
        raise HTTPException(status_code=403, detail="Acesso negado a esta consulta")
    return ConsultaEtapa1Out.model_validate(consulta)


# ── Atualizar Etapa 1 ─────────────────────────────────────────────────────────

@router.patch(
    "/{id_consulta}/etapa1",
    response_model=ConsultaEtapa1Out,
    response_model_by_alias=True,
)
def atualizar_etapa1(
    id_consulta: UUID,
    payload: ConsultaEtapa1Update,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO", "ENFERMEIRO")),
):
    consulta = (
        db.query(ConsultaIdentidade)
        .filter(ConsultaIdentidade.id_consulta == id_consulta)
        .first()
    )
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta não encontrada")
    if consulta.profissional_id != current_user.id:
        raise HTTPException(status_code=403, detail="Acesso negado a esta consulta")
    if consulta.status == "ENCERRADA":
        raise HTTPException(status_code=409, detail="Consulta já encerrada")

    if payload.tipo_consulta is not None:
        consulta.tipo_consulta = payload.tipo_consulta.value

    if "dum" in payload.model_fields_set:
        consulta.dum = payload.dum
        if payload.dum:
            consulta.ig_semanas, consulta.ig_dias = _calcular_ig(payload.dum)
        else:
            consulta.ig_semanas = None
            consulta.ig_dias = None

    db.commit()
    db.refresh(consulta)
    return ConsultaEtapa1Out.model_validate(consulta)
