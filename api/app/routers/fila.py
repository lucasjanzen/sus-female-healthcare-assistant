from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.db.session import get_db
from app.models.consulta import ConsultaIdentidade, ConsultaTriagem
from app.models.paciente import Paciente
from app.models.user import User
from app.schemas.consulta import TriagemOut
from app.schemas.fila import ConsultaAssumidaOut, ConsultaFilaItem

router = APIRouter()


def _ubs_id(current_user: User) -> Optional[UUID]:
    return getattr(current_user, "ubs_id", None)


def _filtrar_ubs(query, current_user: User):
    ubs_id = _ubs_id(current_user)
    if ubs_id is None:
        return query.filter(ConsultaIdentidade.ubs_id.is_(None))
    return query.filter(ConsultaIdentidade.ubs_id == ubs_id)


def _triagem_out(triagem: Optional[ConsultaTriagem]) -> Optional[TriagemOut]:
    if not triagem:
        return None
    return TriagemOut(
        peso_kg=float(triagem.peso_kg),
        pa_sistolica=triagem.pa_sistolica,
        pa_diastolica=triagem.pa_diastolica,
    )


def _carregar_assumida(
    db: Session,
    id_consulta: UUID,
    current_user: User,
) -> ConsultaAssumidaOut:
    consulta = (
        _filtrar_ubs(
            db.query(ConsultaIdentidade).filter(
                ConsultaIdentidade.id_consulta == id_consulta,
                ConsultaIdentidade.medico_id == current_user.id,
                ConsultaIdentidade.status != "ENCERRADA",
            ),
            current_user,
        )
        .first()
    )
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta em andamento não encontrada")

    paciente = db.query(Paciente).filter(Paciente.id == consulta.paciente_id).first()
    triagem = (
        db.query(ConsultaTriagem)
        .filter(ConsultaTriagem.id_consulta == consulta.id_consulta)
        .first()
    )
    if not paciente:
        raise HTTPException(status_code=404, detail="Dados da consulta não encontrados")

    return ConsultaAssumidaOut(
        id_consulta=consulta.id_consulta,
        paciente_nome=paciente.nome,
        paciente_data_nascimento=paciente.data_nascimento,
        tipo_consulta=consulta.tipo_consulta,
        ig_semanas=consulta.ig_semanas,
        ig_dias=consulta.ig_dias,
        triagem_resumo=_triagem_out(triagem),
        assumida_em=consulta.assumida_em,
    )


@router.get(
    "/consultas",
    response_model=list[ConsultaFilaItem],
    response_model_by_alias=True,
)
def listar_consultas_fila(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO")),
):
    consultas = (
        _filtrar_ubs(
            db.query(ConsultaIdentidade).filter(
                ConsultaIdentidade.status == "EM_ATENDIMENTO",
                ConsultaIdentidade.triagem_concluida.is_(True),
                ConsultaIdentidade.medico_id.is_(None),
            ),
            current_user,
        )
        .order_by(ConsultaIdentidade.triagem_concluida_em.asc())
        .all()
    )

    paciente_ids = [c.paciente_id for c in consultas]
    pacientes = (
        {p.id: p for p in db.query(Paciente).filter(Paciente.id.in_(paciente_ids)).all()}
        if paciente_ids
        else {}
    )

    itens = []
    for consulta in consultas:
        paciente = pacientes.get(consulta.paciente_id)
        if not paciente or not consulta.triagem_concluida_em:
            continue
        itens.append(
            ConsultaFilaItem(
                id_consulta=consulta.id_consulta,
                paciente_nome=paciente.nome,
                paciente_data_nascimento=paciente.data_nascimento,
                tipo_consulta=consulta.tipo_consulta,
                ig_semanas=consulta.ig_semanas,
                ig_dias=consulta.ig_dias,
                triagem_concluida_em=consulta.triagem_concluida_em,
                tem_alerta_critico=False,
            )
        )
    return itens


@router.post(
    "/consultas/{id_consulta}/assumir",
    response_model=ConsultaAssumidaOut,
    response_model_by_alias=True,
)
def assumir_consulta(
    id_consulta: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO")),
):
    consulta = (
        _filtrar_ubs(
            db.query(ConsultaIdentidade).filter(
                ConsultaIdentidade.id_consulta == id_consulta,
                ConsultaIdentidade.status == "EM_ATENDIMENTO",
                ConsultaIdentidade.triagem_concluida.is_(True),
            ),
            current_user,
        )
        .first()
    )
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta não encontrada na fila")

    agora = datetime.now(timezone.utc)
    stmt = (
        update(ConsultaIdentidade)
        .where(
            ConsultaIdentidade.id_consulta == id_consulta,
            ConsultaIdentidade.medico_id.is_(None),
        )
        .values(medico_id=current_user.id, assumida_em=agora)
    )
    result = db.execute(stmt)
    if result.rowcount == 0:
        db.rollback()
        raise HTTPException(status_code=409, detail="Esta consulta foi assumida por outro médico.")

    db.commit()
    return _carregar_assumida(db, id_consulta, current_user)


@router.get(
    "/consultas/em-andamento",
    response_model=ConsultaAssumidaOut,
    response_model_by_alias=True,
)
def consulta_em_andamento(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO")),
):
    consulta = (
        _filtrar_ubs(
            db.query(ConsultaIdentidade).filter(
                ConsultaIdentidade.medico_id == current_user.id,
                ConsultaIdentidade.status != "ENCERRADA",
            ),
            current_user,
        )
        .order_by(ConsultaIdentidade.assumida_em.desc())
        .first()
    )
    if not consulta:
        raise HTTPException(status_code=404, detail="Nenhuma consulta em andamento")
    return _carregar_assumida(db, consulta.id_consulta, current_user)


@router.get(
    "/consultas/{id_consulta}/em-andamento",
    response_model=ConsultaAssumidaOut,
    response_model_by_alias=True,
)
def consulta_em_andamento_por_id(
    id_consulta: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO")),
):
    return _carregar_assumida(db, id_consulta, current_user)


@router.get("/consultas/total")
def total_consultas_fila(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO")),
):
    total = (
        _filtrar_ubs(
            db.query(ConsultaIdentidade).filter(
                ConsultaIdentidade.status == "EM_ATENDIMENTO",
                ConsultaIdentidade.triagem_concluida.is_(True),
                ConsultaIdentidade.medico_id.is_(None),
            ),
            current_user,
        )
        .count()
    )
    return {"total": total}
