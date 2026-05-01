import hashlib
from datetime import date, datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import require_role
from app.db.session import get_db
from app.models.consulta import ConsultaIdentidade, ConsultaTriagem
from app.models.paciente import Paciente
from app.models.user import User
from app.schemas.consulta import (
    ConsultaEtapa1Update,
    ConsultaIniciarRequest,
    Etapa1Out,
    PacienteConsultaOut,
    TriagemCreate,
    TriagemOut,
)
from app.services.triagem_service import gerar_alertas

router = APIRouter()


def _hash_cpf(cpf: str) -> str:
    return hashlib.sha256((cpf + settings.secret_salt).encode()).hexdigest()


def _calcular_ig(dum: date) -> tuple[int, int]:
    diff = (date.today() - dum).days
    return diff // 7, diff % 7


def _build_etapa1_out(
    consulta: ConsultaIdentidade,
    triagem: Optional[ConsultaTriagem],
) -> Etapa1Out:
    triagem_out = None
    if triagem:
        triagem_out = TriagemOut(
            peso_kg=float(triagem.peso_kg),
            pa_sistolica=triagem.pa_sistolica,
            pa_diastolica=triagem.pa_diastolica,
        )

    return Etapa1Out(
        id_consulta=consulta.id_consulta,
        paciente_id=consulta.paciente_id,
        tipo_consulta=consulta.tipo_consulta,
        status=consulta.status,
        dum=consulta.dum,
        ig_semanas=consulta.ig_semanas,
        ig_dias=consulta.ig_dias,
        triagem_concluida=consulta.triagem_concluida,
        triagem=triagem_out,
        aberta_em=consulta.aberta_em,
        triagem_concluida_em=consulta.triagem_concluida_em,
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
    response_model=Etapa1Out,
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
        raise HTTPException(status_code=404, detail="Paciente não encontrada")

    ig_semanas = ig_dias = None
    if payload.dum:
        ig_semanas, ig_dias = _calcular_ig(payload.dum)

    consulta = ConsultaIdentidade(
        paciente_id=payload.paciente_id,
        profissional_id=current_user.id,
        ubs_id=getattr(current_user, "ubs_id", None),
        tipo_consulta=payload.tipo_consulta.value,
        dum=payload.dum,
        ig_semanas=ig_semanas,
        ig_dias=ig_dias,
    )
    db.add(consulta)
    db.commit()
    db.refresh(consulta)
    return _build_etapa1_out(consulta, None)


@router.post(
    "/{id_consulta}/triagem",
    response_model=Etapa1Out,
    response_model_by_alias=True,
)
def registrar_triagem(
    id_consulta: UUID,
    payload: TriagemCreate,
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
    if consulta.status == "ENCERRADA":
        raise HTTPException(status_code=409, detail="Consulta já encerrada")
    if consulta.triagem_concluida:
        raise HTTPException(status_code=409, detail="Triagem já registrada para esta consulta")

    agora = datetime.now(timezone.utc)

    triagem = ConsultaTriagem(
        id_consulta=id_consulta,
        peso_kg=payload.peso_kg,
        pa_sistolica=payload.pa_sistolica,
        pa_diastolica=payload.pa_diastolica,
        registrado_por=current_user.id,
    )
    db.add(triagem)

    consulta.triagem_concluida = True
    consulta.triagem_concluida_em = agora
    consulta.status = "EM_ATENDIMENTO"

    db.commit()
    db.refresh(consulta)
    db.refresh(triagem)

    return _build_etapa1_out(consulta, triagem)


@router.get(
    "/{id_consulta}/etapa1",
    response_model=Etapa1Out,
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

    triagem = (
        db.query(ConsultaTriagem)
        .filter(ConsultaTriagem.id_consulta == id_consulta)
        .first()
    )
    return _build_etapa1_out(consulta, triagem)


@router.patch(
    "/{id_consulta}/etapa1",
    response_model=Etapa1Out,
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

    triagem = (
        db.query(ConsultaTriagem)
        .filter(ConsultaTriagem.id_consulta == id_consulta)
        .first()
    )
    return _build_etapa1_out(consulta, triagem)
