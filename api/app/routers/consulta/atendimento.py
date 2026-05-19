from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.db.session import get_db
from app.models.consulta import ConsultaRelato, ConsultaResultado
from app.models.user import User
from app.schemas.consulta import (
    RelatoCreate,
    RelatoOut,
    RelatoUpdate,
    ResultadoIAOut,
)

from .helpers import (
    _build_relato_out,
    _build_resultado_out,
    _consulta_ou_404,
    _exigir_em_atendimento_do_medico,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Relato
# ---------------------------------------------------------------------------

@router.post(
    "/{id_consulta}/relato", response_model=RelatoOut, response_model_by_alias=True
)
def criar_relato(
    id_consulta: UUID,
    payload: RelatoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO")),
):
    _exigir_em_atendimento_do_medico(id_consulta, current_user.id, db)
    relato = (
        db.query(ConsultaRelato)
        .filter(ConsultaRelato.id_consulta == id_consulta)
        .first()
    )
    if relato:
        relato.relato_texto = payload.relato_texto
        relato.atualizado_em = datetime.now(timezone.utc)
    else:
        relato = ConsultaRelato(
            id_consulta=id_consulta,
            relato_texto=payload.relato_texto,
            registrado_por=current_user.id,
        )
        db.add(relato)
    db.commit()
    db.refresh(relato)
    return _build_relato_out(relato)


@router.patch(
    "/{id_consulta}/relato", response_model=RelatoOut, response_model_by_alias=True
)
def atualizar_relato(
    id_consulta: UUID,
    payload: RelatoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO")),
):
    _exigir_em_atendimento_do_medico(id_consulta, current_user.id, db)
    relato = (
        db.query(ConsultaRelato)
        .filter(ConsultaRelato.id_consulta == id_consulta)
        .first()
    )
    if not relato:
        relato = ConsultaRelato(id_consulta=id_consulta, registrado_por=current_user.id)
        db.add(relato)
    if payload.relato_texto is not None:
        relato.relato_texto = payload.relato_texto
    if payload.parecer_medico is not None:
        relato.parecer_medico = payload.parecer_medico
    relato.atualizado_em = datetime.now(timezone.utc)
    db.commit()
    db.refresh(relato)
    return _build_relato_out(relato)


@router.get(
    "/{id_consulta}/relato", response_model=RelatoOut, response_model_by_alias=True
)
def obter_relato(
    id_consulta: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO")),
):
    _consulta_ou_404(id_consulta, db)
    relato = (
        db.query(ConsultaRelato)
        .filter(ConsultaRelato.id_consulta == id_consulta)
        .first()
    )
    if not relato:
        raise HTTPException(status_code=404, detail="Relato não encontrado")
    return _build_relato_out(relato)


# ---------------------------------------------------------------------------
# Resultado (somente leitura — gravado pelo analise_task em background)
# ---------------------------------------------------------------------------

@router.get(
    "/{id_consulta}/resultado",
    response_model=ResultadoIAOut,
    response_model_by_alias=True,
)
def obter_resultado(
    id_consulta: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO", "ENFERMEIRO")),
):
    consulta = _consulta_ou_404(id_consulta, db)
    resultado = (
        db.query(ConsultaResultado)
        .filter(ConsultaResultado.id_consulta == id_consulta)
        .first()
    )
    if not resultado:
        raise HTTPException(status_code=404, detail="Resultado não encontrado")
    return _build_resultado_out(resultado)
