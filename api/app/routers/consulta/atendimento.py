from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.db.session import get_db
from app.models.consulta import ConsultaAudio, ConsultaRelato, ConsultaResultado
from app.models.user import User
from app.schemas.consulta import (
    AudioIniciarOut,
    AudioStatusOut,
    RelatoCreate,
    RelatoOut,
    RelatoUpdate,
    ResultadoIAOut,
)
from app.services.analise_service import analisar

from .helpers import (
    _build_relato_out,
    _build_resultado_out,
    _consulta_ou_404,
    _ultimo_audio,
)

router = APIRouter()


@router.post(
    "/{id_consulta}/relato", response_model=RelatoOut, response_model_by_alias=True
)
def criar_relato(
    id_consulta: UUID,
    payload: RelatoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO")),
):
    _consulta_ou_404(id_consulta, db)
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
    _consulta_ou_404(id_consulta, db)
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
        raise HTTPException(status_code=404, detail="Relato nao encontrado")
    return _build_relato_out(relato)


@router.post(
    "/{id_consulta}/audio/iniciar",
    response_model=AudioIniciarOut,
    response_model_by_alias=True,
)
def iniciar_audio(
    id_consulta: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO")),
):
    _consulta_ou_404(id_consulta, db)
    audio = ConsultaAudio(id_consulta=id_consulta, status_processamento="PROCESSANDO")
    db.add(audio)
    db.commit()
    db.refresh(audio)
    return AudioIniciarOut(audio_id=audio.id)


@router.post("/{id_consulta}/audio/encerrar", response_model=AudioStatusOut)
def encerrar_audio(
    id_consulta: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO")),
):
    _consulta_ou_404(id_consulta, db)
    audio = _ultimo_audio(id_consulta, db)
    if not audio:
        raise HTTPException(status_code=404, detail="Audio nao encontrado")
    audio.status_processamento = "CONCLUIDO"
    audio.transcricao = "Transcricao mockada do audio da consulta. Revisar e complementar conforme relato da paciente."
    db.commit()
    return AudioStatusOut(
        status_processamento=audio.status_processamento, transcricao=audio.transcricao
    )


@router.get("/{id_consulta}/audio/status", response_model=AudioStatusOut)
def status_audio(
    id_consulta: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO")),
):
    _consulta_ou_404(id_consulta, db)
    audio = _ultimo_audio(id_consulta, db)
    if not audio:
        return AudioStatusOut(status_processamento="AGUARDANDO", transcricao=None)
    return AudioStatusOut(
        status_processamento=audio.status_processamento, transcricao=audio.transcricao
    )


@router.post(
    "/{id_consulta}/analisar",
    response_model=ResultadoIAOut,
    response_model_by_alias=True,
)
def analisar_consulta(
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
    if not relato or not relato.relato_texto:
        raise HTTPException(status_code=400, detail="Informe o relato antes da analise")
    audio = _ultimo_audio(id_consulta, db)
    resultado_ia = analisar(
        relato.relato_texto,
        audio.transcricao if audio else None,
        id_consulta=id_consulta,
    )

    resultado = (
        db.query(ConsultaResultado)
        .filter(ConsultaResultado.id_consulta == id_consulta)
        .first()
    )
    if not resultado:
        resultado = ConsultaResultado(id_consulta=id_consulta, indicadores=[])
        db.add(resultado)
    resultado.score_geral = resultado_ia.score_geral
    resultado.faixa_risco = resultado_ia.faixa_risco
    resultado.indicadores = [i.model_dump() for i in resultado_ia.indicadores]
    resultado.resumo_ia = resultado_ia.resumo_ia
    resultado.calculado_em = datetime.now(timezone.utc)
    resultado.confirmado = False
    resultado.confirmado_em = None
    db.commit()
    db.refresh(resultado)
    return _build_resultado_out(resultado, db)


@router.get(
    "/{id_consulta}/resultado",
    response_model=ResultadoIAOut,
    response_model_by_alias=True,
)
def obter_resultado(
    id_consulta: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO")),
):
    _consulta_ou_404(id_consulta, db)
    resultado = (
        db.query(ConsultaResultado)
        .filter(ConsultaResultado.id_consulta == id_consulta)
        .first()
    )
    if not resultado:
        raise HTTPException(status_code=404, detail="Resultado nao encontrado")
    return _build_resultado_out(resultado, db)


@router.post(
    "/{id_consulta}/resultado/confirmar",
    response_model=ResultadoIAOut,
    response_model_by_alias=True,
)
def confirmar_resultado(
    id_consulta: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO")),
):
    _consulta_ou_404(id_consulta, db)
    resultado = (
        db.query(ConsultaResultado)
        .filter(ConsultaResultado.id_consulta == id_consulta)
        .first()
    )
    if not resultado:
        raise HTTPException(status_code=404, detail="Resultado nao encontrado")
    resultado.confirmado = True
    resultado.confirmado_em = datetime.now(timezone.utc)
    db.commit()
    db.refresh(resultado)
    return _build_resultado_out(resultado, db)
