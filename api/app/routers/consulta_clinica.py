from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.db.session import get_db
from app.db.session_b import get_db_b
from app.models.consulta import ConsultaIdentidade, ConsultaTriagem
from app.models.consulta_banco_b import ConsultaAudio, ConsultaResultado
from app.models.consulta_clinica import (
    ConsultaAnamnese,
    ConsultaExameFisico,
    ConsultaExamesLab,
    ConsultaParecer,
    ConsultaRastreioPsicossocial,
)
from app.models.user import User
from app.schemas.consulta_clinica import (
    AnamneseCreate,
    AnamneseOut,
    AudioIniciarOut,
    AudioStatusOut,
    ExameFisicoCreate,
    ExameFisicoOut,
    ExamesLabCreate,
    ExamesLabOut,
    ParecerCreate,
    ParecerOut,
    RastreioCreate,
    RastreioOut,
    ResultadoOut,
    TranscricaoEditadaUpdate,
    AlertaResultado,
)
from app.services.rastreio_service import calcular_rastreio
from app.services.score_service import calcular_score

router = APIRouter()


# ── helpers ───────────────────────────────────────────────────────────────────

def _get_consulta_or_404(id_consulta: UUID, db: Session) -> ConsultaIdentidade:
    c = db.query(ConsultaIdentidade).filter(ConsultaIdentidade.id_consulta == id_consulta).first()
    if not c:
        raise HTTPException(status_code=404, detail="Consulta não encontrada")
    return c


def _alertas_exame_fisico(exame: ConsultaExameFisico) -> list[dict]:
    alertas = []
    if exame.bcf_bpm is not None and (exame.bcf_bpm < 110 or exame.bcf_bpm > 160):
        alertas.append({
            "tipo": "BCF_ALTERADO",
            "descricao": f"BCF {exame.bcf_bpm} bpm fora da faixa normal (110–160 bpm).",
            "nivel": "CRITICO",
        })
    if exame.edema_grau is not None and exame.edema_grau >= 3:
        alertas.append({
            "tipo": "EDEMA_GRAVE",
            "descricao": "Edema grau 3+ — avaliar pré-eclâmpsia.",
            "nivel": "CRITICO",
        })
    return alertas


def _mock_transcricao(audio_id: UUID, db_b: Session) -> None:
    audio = db_b.query(ConsultaAudio).filter(ConsultaAudio.id == audio_id).first()
    if not audio:
        return
    audio.status_processamento = "CONCLUIDO"
    audio.transcricao = "[Transcrição automática indisponível — integração ASR prevista para v2]"
    db_b.commit()


def _build_resultado_out(resultado: ConsultaResultado, audio: Optional[ConsultaAudio]) -> ResultadoOut:
    alertas = [AlertaResultado(**a) for a in (resultado.alertas or [])]
    transcricao = audio.transcricao if audio else None
    status_audio = audio.status_processamento if audio else "INDISPONIVEL"
    return ResultadoOut(
        id_consulta=resultado.id_consulta,
        score_geral=resultado.score_geral,
        faixa_risco=resultado.faixa_risco,
        score_psicossocial=resultado.score_psicossocial,
        score_audio=resultado.score_audio,
        score_estruturado=resultado.score_estruturado,
        alertas=alertas,
        resumo_encaminhamento=resultado.resumo_encaminhamento,
        sugestao_conduta=resultado.sugestao_conduta,
        transcricao=transcricao,
        transcricao_editada=resultado.transcricao_editada,
        status_audio=status_audio,
        confirmado=resultado.confirmado_pelo_profissional,
        calculado_em=resultado.calculado_em,
    )


# ── Anamnese ─────────────────────────────────────────────────────────────────

@router.post(
    "/{id_consulta}/anamnese",
    response_model=AnamneseOut,
    status_code=201,
    response_model_by_alias=True,
)
def criar_anamnese(
    id_consulta: UUID,
    payload: AnamneseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO", "ENFERMEIRO")),
):
    _get_consulta_or_404(id_consulta, db)
    existente = db.query(ConsultaAnamnese).filter(ConsultaAnamnese.id_consulta == id_consulta).first()
    if existente:
        raise HTTPException(status_code=409, detail="Anamnese já registrada")

    meds = [m.model_dump() for m in payload.medicamentos] if payload.medicamentos else None
    anamnese = ConsultaAnamnese(
        id_consulta=id_consulta,
        gestacoes=payload.gestacoes,
        partos=payload.partos,
        abortos=payload.abortos,
        doencas=payload.doencas,
        medicamentos=meds,
        situacao_moradia=payload.situacao_moradia,
        situacao_renda=payload.situacao_renda,
        suporte_familiar=payload.suporte_familiar,
        historico_saude_mental=payload.historico_saude_mental,
        registrado_por=current_user.id,
    )
    db.add(anamnese)
    db.commit()
    db.refresh(anamnese)
    return AnamneseOut.model_validate(anamnese)


@router.get(
    "/{id_consulta}/anamnese",
    response_model=AnamneseOut,
    response_model_by_alias=True,
)
def obter_anamnese(
    id_consulta: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO", "ENFERMEIRO")),
):
    _get_consulta_or_404(id_consulta, db)
    anamnese = db.query(ConsultaAnamnese).filter(ConsultaAnamnese.id_consulta == id_consulta).first()
    if not anamnese:
        raise HTTPException(status_code=404, detail="Anamnese não encontrada")
    return AnamneseOut.model_validate(anamnese)


@router.patch(
    "/{id_consulta}/anamnese",
    response_model=AnamneseOut,
    response_model_by_alias=True,
)
def atualizar_anamnese(
    id_consulta: UUID,
    payload: AnamneseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO", "ENFERMEIRO")),
):
    _get_consulta_or_404(id_consulta, db)
    anamnese = db.query(ConsultaAnamnese).filter(ConsultaAnamnese.id_consulta == id_consulta).first()
    if not anamnese:
        raise HTTPException(status_code=404, detail="Anamnese não encontrada")

    for field, value in payload.model_dump(exclude_unset=True).items():
        if field == "medicamentos" and value is not None:
            value = [m if isinstance(m, dict) else m.model_dump() for m in (payload.medicamentos or [])]
        setattr(anamnese, field, value)
    anamnese.atualizado_em = datetime.now(timezone.utc)
    db.commit()
    db.refresh(anamnese)
    return AnamneseOut.model_validate(anamnese)


# ── Exame Físico ─────────────────────────────────────────────────────────────

@router.post(
    "/{id_consulta}/exame-fisico",
    response_model=ExameFisicoOut,
    status_code=201,
    response_model_by_alias=True,
)
def criar_exame_fisico(
    id_consulta: UUID,
    payload: ExameFisicoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO", "ENFERMEIRO")),
):
    _get_consulta_or_404(id_consulta, db)
    existente = db.query(ConsultaExameFisico).filter(ConsultaExameFisico.id_consulta == id_consulta).first()
    if existente:
        raise HTTPException(status_code=409, detail="Exame físico já registrado")

    exame = ConsultaExameFisico(
        id_consulta=id_consulta,
        registrado_por=current_user.id,
        **payload.model_dump(),
    )
    db.add(exame)
    db.commit()
    db.refresh(exame)
    alertas = _alertas_exame_fisico(exame)
    out = ExameFisicoOut.model_validate(exame)
    out.alertas = alertas
    return out


@router.get(
    "/{id_consulta}/exame-fisico",
    response_model=ExameFisicoOut,
    response_model_by_alias=True,
)
def obter_exame_fisico(
    id_consulta: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO", "ENFERMEIRO")),
):
    _get_consulta_or_404(id_consulta, db)
    exame = db.query(ConsultaExameFisico).filter(ConsultaExameFisico.id_consulta == id_consulta).first()
    if not exame:
        raise HTTPException(status_code=404, detail="Exame físico não encontrado")
    alertas = _alertas_exame_fisico(exame)
    out = ExameFisicoOut.model_validate(exame)
    out.alertas = alertas
    return out


@router.patch(
    "/{id_consulta}/exame-fisico",
    response_model=ExameFisicoOut,
    response_model_by_alias=True,
)
def atualizar_exame_fisico(
    id_consulta: UUID,
    payload: ExameFisicoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO", "ENFERMEIRO")),
):
    _get_consulta_or_404(id_consulta, db)
    exame = db.query(ConsultaExameFisico).filter(ConsultaExameFisico.id_consulta == id_consulta).first()
    if not exame:
        raise HTTPException(status_code=404, detail="Exame físico não encontrado")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(exame, field, value)
    exame.atualizado_em = datetime.now(timezone.utc)
    db.commit()
    db.refresh(exame)
    alertas = _alertas_exame_fisico(exame)
    out = ExameFisicoOut.model_validate(exame)
    out.alertas = alertas
    return out


# ── Exames Laboratoriais ──────────────────────────────────────────────────────

@router.post(
    "/{id_consulta}/exames-lab",
    response_model=ExamesLabOut,
    status_code=201,
    response_model_by_alias=True,
)
def criar_exames_lab(
    id_consulta: UUID,
    payload: ExamesLabCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO", "ENFERMEIRO")),
):
    _get_consulta_or_404(id_consulta, db)
    existente = db.query(ConsultaExamesLab).filter(ConsultaExamesLab.id_consulta == id_consulta).first()
    if existente:
        raise HTTPException(status_code=409, detail="Exames laboratoriais já registrados")

    lab = ConsultaExamesLab(
        id_consulta=id_consulta,
        registrado_por=current_user.id,
        **payload.model_dump(),
    )
    db.add(lab)
    db.commit()
    db.refresh(lab)
    return ExamesLabOut.model_validate(lab)


@router.get(
    "/{id_consulta}/exames-lab",
    response_model=ExamesLabOut,
    response_model_by_alias=True,
)
def obter_exames_lab(
    id_consulta: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO", "ENFERMEIRO")),
):
    _get_consulta_or_404(id_consulta, db)
    lab = db.query(ConsultaExamesLab).filter(ConsultaExamesLab.id_consulta == id_consulta).first()
    if not lab:
        raise HTTPException(status_code=404, detail="Exames laboratoriais não encontrados")
    return ExamesLabOut.model_validate(lab)


@router.patch(
    "/{id_consulta}/exames-lab",
    response_model=ExamesLabOut,
    response_model_by_alias=True,
)
def atualizar_exames_lab(
    id_consulta: UUID,
    payload: ExamesLabCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO", "ENFERMEIRO")),
):
    _get_consulta_or_404(id_consulta, db)
    lab = db.query(ConsultaExamesLab).filter(ConsultaExamesLab.id_consulta == id_consulta).first()
    if not lab:
        raise HTTPException(status_code=404, detail="Exames laboratoriais não encontrados")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(lab, field, value)
    lab.atualizado_em = datetime.now(timezone.utc)
    db.commit()
    db.refresh(lab)
    return ExamesLabOut.model_validate(lab)


# ── Rastreio Psicossocial ─────────────────────────────────────────────────────

@router.post(
    "/{id_consulta}/rastreio",
    response_model=RastreioOut,
    status_code=201,
    response_model_by_alias=True,
)
def criar_rastreio(
    id_consulta: UUID,
    payload: RastreioCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO", "ENFERMEIRO")),
):
    _get_consulta_or_404(id_consulta, db)
    existente = db.query(ConsultaRastreioPsicossocial).filter(
        ConsultaRastreioPsicossocial.id_consulta == id_consulta
    ).first()
    if existente:
        raise HTTPException(status_code=409, detail="Rastreio psicossocial já registrado")

    calc = calcular_rastreio(payload)
    rastreio = ConsultaRastreioPsicossocial(
        id_consulta=id_consulta,
        epds_respostas=payload.epds_respostas,
        epds_score=calc["epds_score"],
        epds_flag=calc["epds_flag"],
        gad7_respostas=payload.gad7_respostas,
        gad7_score=calc["gad7_score"],
        gad7_flag=calc["gad7_flag"],
        hits_respostas=payload.hits_respostas,
        hits_score=calc["hits_score"],
        hits_flag=calc["hits_flag"],
        situacao_social=payload.situacao_social,
        registrado_por=current_user.id,
    )
    db.add(rastreio)
    db.commit()
    db.refresh(rastreio)
    return RastreioOut.model_validate(rastreio)


@router.get(
    "/{id_consulta}/rastreio",
    response_model=RastreioOut,
    response_model_by_alias=True,
)
def obter_rastreio(
    id_consulta: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO", "ENFERMEIRO")),
):
    _get_consulta_or_404(id_consulta, db)
    rastreio = db.query(ConsultaRastreioPsicossocial).filter(
        ConsultaRastreioPsicossocial.id_consulta == id_consulta
    ).first()
    if not rastreio:
        raise HTTPException(status_code=404, detail="Rastreio não encontrado")
    return RastreioOut.model_validate(rastreio)


@router.patch(
    "/{id_consulta}/rastreio",
    response_model=RastreioOut,
    response_model_by_alias=True,
)
def atualizar_rastreio(
    id_consulta: UUID,
    payload: RastreioCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO", "ENFERMEIRO")),
):
    _get_consulta_or_404(id_consulta, db)
    rastreio = db.query(ConsultaRastreioPsicossocial).filter(
        ConsultaRastreioPsicossocial.id_consulta == id_consulta
    ).first()
    if not rastreio:
        raise HTTPException(status_code=404, detail="Rastreio não encontrado")

    calc = calcular_rastreio(payload)
    rastreio.epds_respostas = payload.epds_respostas
    rastreio.epds_score = calc["epds_score"]
    rastreio.epds_flag = calc["epds_flag"]
    rastreio.gad7_respostas = payload.gad7_respostas
    rastreio.gad7_score = calc["gad7_score"]
    rastreio.gad7_flag = calc["gad7_flag"]
    rastreio.hits_respostas = payload.hits_respostas
    rastreio.hits_score = calc["hits_score"]
    rastreio.hits_flag = calc["hits_flag"]
    rastreio.situacao_social = payload.situacao_social
    rastreio.atualizado_em = datetime.now(timezone.utc)
    db.commit()
    db.refresh(rastreio)
    return RastreioOut.model_validate(rastreio)


# ── Parecer ───────────────────────────────────────────────────────────────────

@router.post(
    "/{id_consulta}/parecer",
    response_model=ParecerOut,
    status_code=201,
    response_model_by_alias=True,
)
def criar_parecer(
    id_consulta: UUID,
    payload: ParecerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO", "ENFERMEIRO")),
):
    _get_consulta_or_404(id_consulta, db)
    existente = db.query(ConsultaParecer).filter(ConsultaParecer.id_consulta == id_consulta).first()
    if existente:
        raise HTTPException(status_code=409, detail="Parecer já registrado")

    parecer = ConsultaParecer(
        id_consulta=id_consulta,
        parecer_texto=payload.parecer_texto,
        audio_parecer_id=payload.audio_parecer_id,
        registrado_por=current_user.id,
    )
    db.add(parecer)
    db.commit()
    db.refresh(parecer)
    return ParecerOut.model_validate(parecer)


@router.get(
    "/{id_consulta}/parecer",
    response_model=ParecerOut,
    response_model_by_alias=True,
)
def obter_parecer(
    id_consulta: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO", "ENFERMEIRO")),
):
    _get_consulta_or_404(id_consulta, db)
    parecer = db.query(ConsultaParecer).filter(ConsultaParecer.id_consulta == id_consulta).first()
    if not parecer:
        raise HTTPException(status_code=404, detail="Parecer não encontrado")
    return ParecerOut.model_validate(parecer)


@router.patch(
    "/{id_consulta}/parecer",
    response_model=ParecerOut,
    response_model_by_alias=True,
)
def atualizar_parecer(
    id_consulta: UUID,
    payload: ParecerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO", "ENFERMEIRO")),
):
    _get_consulta_or_404(id_consulta, db)
    parecer = db.query(ConsultaParecer).filter(ConsultaParecer.id_consulta == id_consulta).first()
    if not parecer:
        raise HTTPException(status_code=404, detail="Parecer não encontrado")

    if payload.parecer_texto is not None:
        parecer.parecer_texto = payload.parecer_texto
    if payload.audio_parecer_id is not None:
        parecer.audio_parecer_id = payload.audio_parecer_id
    parecer.atualizado_em = datetime.now(timezone.utc)
    db.commit()
    db.refresh(parecer)
    return ParecerOut.model_validate(parecer)


# ── Áudio ─────────────────────────────────────────────────────────────────────

@router.post(
    "/{id_consulta}/audio/iniciar",
    response_model=AudioIniciarOut,
    status_code=201,
    response_model_by_alias=True,
)
def iniciar_audio(
    id_consulta: UUID,
    tipo_audio: str = "CONSULTA_GERAL",
    db: Session = Depends(get_db),
    db_b: Session = Depends(get_db_b),
    current_user: User = Depends(require_role("MEDICO", "ENFERMEIRO")),
):
    _get_consulta_or_404(id_consulta, db)
    agora = datetime.now(timezone.utc)
    audio = ConsultaAudio(
        id_consulta=id_consulta,
        tipo_audio=tipo_audio,
        status_processamento="AGUARDANDO",
        criado_em=agora,
        deletar_em=agora + timedelta(days=90),
    )
    db_b.add(audio)
    db_b.commit()
    db_b.refresh(audio)
    return AudioIniciarOut(audio_id=audio.id, status=audio.status_processamento)


@router.post(
    "/{id_consulta}/audio/encerrar",
    response_model=AudioStatusOut,
    response_model_by_alias=True,
)
def encerrar_audio(
    id_consulta: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    db_b: Session = Depends(get_db_b),
    current_user: User = Depends(require_role("MEDICO", "ENFERMEIRO")),
):
    _get_consulta_or_404(id_consulta, db)
    audio = (
        db_b.query(ConsultaAudio)
        .filter(
            ConsultaAudio.id_consulta == id_consulta,
            ConsultaAudio.tipo_audio == "CONSULTA_GERAL",
        )
        .order_by(ConsultaAudio.criado_em.desc())
        .first()
    )
    if not audio:
        raise HTTPException(status_code=404, detail="Gravação não encontrada")
    if audio.status_processamento != "AGUARDANDO":
        raise HTTPException(status_code=409, detail="Gravação já encerrada")

    audio.status_processamento = "PROCESSANDO"
    db_b.commit()
    db_b.refresh(audio)

    audio_id = audio.id
    background_tasks.add_task(_mock_transcricao, audio_id, db_b)

    return AudioStatusOut(
        audio_id=audio.id,
        status_processamento=audio.status_processamento,
        transcricao=audio.transcricao,
        duracao_segundos=audio.duracao_segundos,
    )


@router.get(
    "/{id_consulta}/audio/status",
    response_model=AudioStatusOut,
    response_model_by_alias=True,
)
def status_audio(
    id_consulta: UUID,
    db: Session = Depends(get_db),
    db_b: Session = Depends(get_db_b),
    current_user: User = Depends(require_role("MEDICO", "ENFERMEIRO")),
):
    _get_consulta_or_404(id_consulta, db)
    audio = (
        db_b.query(ConsultaAudio)
        .filter(
            ConsultaAudio.id_consulta == id_consulta,
            ConsultaAudio.tipo_audio == "CONSULTA_GERAL",
        )
        .order_by(ConsultaAudio.criado_em.desc())
        .first()
    )
    if not audio:
        raise HTTPException(status_code=404, detail="Gravação não encontrada")
    return AudioStatusOut(
        audio_id=audio.id,
        status_processamento=audio.status_processamento,
        transcricao=audio.transcricao,
        duracao_segundos=audio.duracao_segundos,
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
    db_b: Session = Depends(get_db_b),
    current_user: User = Depends(require_role("MEDICO", "ENFERMEIRO")),
):
    _get_consulta_or_404(id_consulta, db)

    triagem = db.query(ConsultaTriagem).filter(ConsultaTriagem.id_consulta == id_consulta).first()
    exame = db.query(ConsultaExameFisico).filter(ConsultaExameFisico.id_consulta == id_consulta).first()
    rastreio = db.query(ConsultaRastreioPsicossocial).filter(
        ConsultaRastreioPsicossocial.id_consulta == id_consulta
    ).first()
    audio = (
        db_b.query(ConsultaAudio)
        .filter(ConsultaAudio.id_consulta == id_consulta, ConsultaAudio.tipo_audio == "CONSULTA_GERAL")
        .order_by(ConsultaAudio.criado_em.desc())
        .first()
    )

    dados = calcular_score(id_consulta, triagem, exame, rastreio, audio)

    existente = db_b.query(ConsultaResultado).filter(
        ConsultaResultado.id_consulta == id_consulta
    ).first()
    if existente:
        existente.score_geral = dados["score_geral"]
        existente.faixa_risco = dados["faixa_risco"]
        existente.score_psicossocial = dados["score_psicossocial"]
        existente.score_audio = dados["score_audio"]
        existente.score_estruturado = dados["score_estruturado"]
        existente.alertas = dados["alertas"]
        existente.resumo_encaminhamento = dados["resumo_encaminhamento"]
        existente.sugestao_conduta = dados["sugestao_conduta"]
        existente.calculado_em = datetime.now(timezone.utc)
        resultado = existente
    else:
        resultado = ConsultaResultado(
            id_consulta=id_consulta,
            score_geral=dados["score_geral"],
            faixa_risco=dados["faixa_risco"],
            score_psicossocial=dados["score_psicossocial"],
            score_audio=dados["score_audio"],
            score_estruturado=dados["score_estruturado"],
            alertas=dados["alertas"],
            resumo_encaminhamento=dados["resumo_encaminhamento"],
            sugestao_conduta=dados["sugestao_conduta"],
        )
        db_b.add(resultado)

    db_b.commit()
    db_b.refresh(resultado)
    return _build_resultado_out(resultado, audio)


@router.get(
    "/{id_consulta}/resultado",
    response_model=ResultadoOut,
    response_model_by_alias=True,
)
def obter_resultado(
    id_consulta: UUID,
    db: Session = Depends(get_db),
    db_b: Session = Depends(get_db_b),
    current_user: User = Depends(require_role("MEDICO", "ENFERMEIRO")),
):
    _get_consulta_or_404(id_consulta, db)
    resultado = db_b.query(ConsultaResultado).filter(
        ConsultaResultado.id_consulta == id_consulta
    ).first()
    if not resultado:
        raise HTTPException(status_code=404, detail="Score ainda não calculado")

    audio = (
        db_b.query(ConsultaAudio)
        .filter(ConsultaAudio.id_consulta == id_consulta, ConsultaAudio.tipo_audio == "CONSULTA_GERAL")
        .order_by(ConsultaAudio.criado_em.desc())
        .first()
    )
    return _build_resultado_out(resultado, audio)


@router.patch(
    "/{id_consulta}/resultado/transcricao",
    status_code=204,
)
def atualizar_transcricao(
    id_consulta: UUID,
    payload: TranscricaoEditadaUpdate,
    db: Session = Depends(get_db),
    db_b: Session = Depends(get_db_b),
    current_user: User = Depends(require_role("MEDICO", "ENFERMEIRO")),
):
    _get_consulta_or_404(id_consulta, db)
    resultado = db_b.query(ConsultaResultado).filter(
        ConsultaResultado.id_consulta == id_consulta
    ).first()
    if not resultado:
        raise HTTPException(status_code=404, detail="Score ainda não calculado")

    resultado.transcricao_editada = payload.transcricao_editada
    db_b.commit()


@router.post(
    "/{id_consulta}/resultado/confirmar",
    status_code=204,
)
def confirmar_resultado(
    id_consulta: UUID,
    db: Session = Depends(get_db),
    db_b: Session = Depends(get_db_b),
    current_user: User = Depends(require_role("MEDICO", "ENFERMEIRO")),
):
    _get_consulta_or_404(id_consulta, db)
    resultado = db_b.query(ConsultaResultado).filter(
        ConsultaResultado.id_consulta == id_consulta
    ).first()
    if not resultado:
        raise HTTPException(status_code=404, detail="Score ainda não calculado")

    resultado.confirmado_pelo_profissional = True
    resultado.confirmado_em = datetime.now(timezone.utc)
    db_b.commit()
