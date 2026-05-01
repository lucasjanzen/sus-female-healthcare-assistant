from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.db.session import get_db
from app.models.consulta import ConsultaIdentidade
from app.models.consulta_banco_b import ConsultaAudio, ConsultaResultado
from app.models.consulta_clinica import ConsultaRelato
from app.models.user import User
from app.schemas.consulta_clinica import (
    AudioIniciarOut,
    AudioStatusOut,
    RelatoCreate,
    RelatoOut,
    ResultadoOut,
)
from app.services.score_service import calcular_score

router = APIRouter()


def _get_consulta_or_404(id_consulta: UUID, db: Session) -> ConsultaIdentidade:
    c = db.query(ConsultaIdentidade).filter(ConsultaIdentidade.id_consulta == id_consulta).first()
    if not c:
        raise HTTPException(status_code=404, detail="Consulta não encontrada")
    return c


# ── Relato ────────────────────────────────────────────────────────────────────

@router.post(
    "/{id_consulta}/relato",
    response_model=RelatoOut,
    status_code=201,
    response_model_by_alias=True,
)
def criar_relato(
    id_consulta: UUID,
    payload: RelatoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO", "ENFERMEIRO")),
):
    _get_consulta_or_404(id_consulta, db)
    existente = db.query(ConsultaRelato).filter(ConsultaRelato.id_consulta == id_consulta).first()
    if existente:
        raise HTTPException(status_code=409, detail="Relato já registrado")

    relato = ConsultaRelato(
        id_consulta=id_consulta,
        relato_texto=payload.relato_texto,
        parecer_medico=payload.parecer_medico,
        registrado_por=current_user.id,
    )
    db.add(relato)
    db.commit()
    db.refresh(relato)
    return RelatoOut.model_validate(relato)


@router.get(
    "/{id_consulta}/relato",
    response_model=RelatoOut,
    response_model_by_alias=True,
)
def obter_relato(
    id_consulta: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO", "ENFERMEIRO")),
):
    _get_consulta_or_404(id_consulta, db)
    relato = db.query(ConsultaRelato).filter(ConsultaRelato.id_consulta == id_consulta).first()
    if not relato:
        raise HTTPException(status_code=404, detail="Relato não encontrado")
    return RelatoOut.model_validate(relato)


@router.patch(
    "/{id_consulta}/relato",
    response_model=RelatoOut,
    response_model_by_alias=True,
)
def atualizar_relato(
    id_consulta: UUID,
    payload: RelatoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO", "ENFERMEIRO")),
):
    _get_consulta_or_404(id_consulta, db)
    relato = db.query(ConsultaRelato).filter(ConsultaRelato.id_consulta == id_consulta).first()
    if not relato:
        raise HTTPException(status_code=404, detail="Relato não encontrado")

    if payload.relato_texto is not None:
        relato.relato_texto = payload.relato_texto
    if payload.parecer_medico is not None:
        relato.parecer_medico = payload.parecer_medico
    relato.atualizado_em = datetime.now(timezone.utc)
    db.commit()
    db.refresh(relato)
    return RelatoOut.model_validate(relato)


# ── Áudio ─────────────────────────────────────────────────────────────────────

@router.post(
    "/{id_consulta}/audio/iniciar",
    response_model=AudioIniciarOut,
    status_code=201,
    response_model_by_alias=True,
)
def iniciar_audio(
    id_consulta: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO", "ENFERMEIRO")),
):
    _get_consulta_or_404(id_consulta, db)
    agora = datetime.now(timezone.utc)
    audio = ConsultaAudio(
        id_consulta=id_consulta,
        status_processamento="AGUARDANDO",
        criado_em=agora,
        deletar_em=agora + timedelta(days=90),
    )
    db.add(audio)
    db.commit()
    db.refresh(audio)
    return AudioIniciarOut(audio_id=audio.id, status=audio.status_processamento)


@router.get(
    "/{id_consulta}/audio/status",
    response_model=AudioStatusOut,
    response_model_by_alias=True,
)
def status_audio(
    id_consulta: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO", "ENFERMEIRO")),
):
    _get_consulta_or_404(id_consulta, db)
    audio = (
        db.query(ConsultaAudio)
        .filter(ConsultaAudio.id_consulta == id_consulta)
        .order_by(ConsultaAudio.criado_em.desc())
        .first()
    )
    if not audio:
        raise HTTPException(status_code=404, detail="Gravação não encontrada")
    return AudioStatusOut(
        audio_id=audio.id,
        status_processamento=audio.status_processamento,
        transcricao=audio.transcricao,
    )


# ── Score / Resultado ─────────────────────────────────────────────────────────

@router.post(
    "/{id_consulta}/calcular-score",
    response_model=ResultadoOut,
    response_model_by_alias=True,
)
def calcular_score_endpoint(
    id_consulta: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO", "ENFERMEIRO")),
):
    from app.models.consulta import ConsultaTriagem
    consulta = _get_consulta_or_404(id_consulta, db)

    triagem = db.query(ConsultaTriagem).filter(ConsultaTriagem.id_consulta == id_consulta).first()
    audio = (
        db.query(ConsultaAudio)
        .filter(ConsultaAudio.id_consulta == id_consulta)
        .order_by(ConsultaAudio.criado_em.desc())
        .first()
    )

    dados = calcular_score(id_consulta, triagem, audio)

    existente = db.query(ConsultaResultado).filter(ConsultaResultado.id_consulta == id_consulta).first()
    if existente:
        existente.score_geral = dados["score_geral"]
        existente.faixa_risco = dados["faixa_risco"]
        existente.indicadores = dados["indicadores"]
        existente.resumo_ia = dados["resumo_ia"]
        resultado = existente
    else:
        resultado = ConsultaResultado(
            id_consulta=id_consulta,
            score_geral=dados["score_geral"],
            faixa_risco=dados["faixa_risco"],
            indicadores=dados["indicadores"],
            resumo_ia=dados["resumo_ia"],
        )
        db.add(resultado)

    db.commit()
    db.refresh(resultado)
    return ResultadoOut(
        id_consulta=resultado.id_consulta,
        score_geral=resultado.score_geral,
        faixa_risco=resultado.faixa_risco,
        indicadores=resultado.indicadores,
        resumo_ia=resultado.resumo_ia,
        confirmado=resultado.confirmado,
        calculado_em=resultado.calculado_em,
    )


@router.get(
    "/{id_consulta}/resultado",
    response_model=ResultadoOut,
    response_model_by_alias=True,
)
def obter_resultado(
    id_consulta: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO", "ENFERMEIRO")),
):
    _get_consulta_or_404(id_consulta, db)
    resultado = db.query(ConsultaResultado).filter(ConsultaResultado.id_consulta == id_consulta).first()
    if not resultado:
        raise HTTPException(status_code=404, detail="Score ainda não calculado")

    return ResultadoOut(
        id_consulta=resultado.id_consulta,
        score_geral=resultado.score_geral,
        faixa_risco=resultado.faixa_risco,
        indicadores=resultado.indicadores,
        resumo_ia=resultado.resumo_ia,
        confirmado=resultado.confirmado,
        calculado_em=resultado.calculado_em,
    )


@router.post("/{id_consulta}/resultado/confirmar", status_code=204)
def confirmar_resultado(
    id_consulta: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO", "ENFERMEIRO")),
):
    _get_consulta_or_404(id_consulta, db)
    resultado = db.query(ConsultaResultado).filter(ConsultaResultado.id_consulta == id_consulta).first()
    if not resultado:
        raise HTTPException(status_code=404, detail="Score ainda não calculado")

    resultado.confirmado = True
    resultado.confirmado_em = datetime.now(timezone.utc)
    db.commit()
