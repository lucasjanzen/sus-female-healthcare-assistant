import hashlib
import io
from datetime import date, datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import require_role
from app.db.session import get_db
from app.models.consulta import (
    ConsultaAudio,
    ConsultaEncerramento,
    ConsultaIdentidade,
    ConsultaRelato,
    ConsultaResultado,
    ConsultaTriagem,
)
from app.models.paciente import Paciente
from app.models.user import User
from app.schemas.consulta import (
    AudioIniciarOut,
    AudioStatusOut,
    ConsultaIniciarOut,
    ConsultaIniciarRequest,
    EncerramentoCreate,
    EncerramentoOut,
    Etapa1Out,
    PacienteConsultaOut,
    RelatoCreate,
    RelatoOut,
    RelatoUpdate,
    ResumoPecOut,
    ResultadoIAOut,
    SugestaoEncerramentoOut,
    TriagemCreate,
    TriagemResumo,
)
from app.services.analise_service import analisar
from app.services.encerramento_service import (
    calcular_data_sugerida,
    encaminhamentos_sugeridos,
    gerar_pdf_resumo,
)

router = APIRouter()


def _hash_cpf(cpf: str) -> str:
    return hashlib.sha256((cpf + settings.secret_salt).encode()).hexdigest()


def _calcular_ig(dum: date | None) -> tuple[int | None, int | None]:
    if not dum:
        return None, None
    dias = max((date.today() - dum).days, 0)
    return dias // 7, dias % 7


def _consulta_ou_404(id_consulta: UUID, db: Session) -> ConsultaIdentidade:
    consulta = (
        db.query(ConsultaIdentidade).filter(ConsultaIdentidade.id_consulta == id_consulta).first()
    )
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta nao encontrada")
    return consulta


def _triagem_resumo(triagem: ConsultaTriagem | None) -> TriagemResumo | None:
    if not triagem:
        return None
    return TriagemResumo(
        peso_kg=float(triagem.peso_kg),
        pa_sistolica=triagem.pa_sistolica,
        pa_diastolica=triagem.pa_diastolica,
    )


def _build_etapa1_out(consulta: ConsultaIdentidade, db: Session) -> Etapa1Out:
    triagem = (
        db.query(ConsultaTriagem)
        .filter(ConsultaTriagem.id_consulta == consulta.id_consulta)
        .first()
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
        triagem=_triagem_resumo(triagem),
        aberta_em=consulta.aberta_em,
        triagem_concluida_em=consulta.triagem_concluida_em,
    )


def _build_relato_out(relato: ConsultaRelato) -> RelatoOut:
    return RelatoOut(
        id_consulta=relato.id_consulta,
        relato_texto=relato.relato_texto,
        parecer_medico=relato.parecer_medico,
        registrado_em=relato.registrado_em,
        atualizado_em=relato.atualizado_em,
    )


def _ultimo_audio(id_consulta: UUID, db: Session) -> ConsultaAudio | None:
    return (
        db.query(ConsultaAudio)
        .filter(ConsultaAudio.id_consulta == id_consulta)
        .order_by(ConsultaAudio.criado_em.desc())
        .first()
    )


def _build_resultado_out(resultado: ConsultaResultado, db: Session) -> ResultadoIAOut:
    audio = _ultimo_audio(resultado.id_consulta, db)
    return ResultadoIAOut(
        id_consulta=resultado.id_consulta,
        score_geral=resultado.score_geral,
        faixa_risco=resultado.faixa_risco,
        indicadores=resultado.indicadores,
        resumo_ia=resultado.resumo_ia or "",
        status_audio=audio.status_processamento if audio else "AGUARDANDO",
        confirmado=resultado.confirmado,
        calculado_em=resultado.calculado_em,
    )


@router.get(
    "/pacientes/buscar", response_model=list[PacienteConsultaOut], response_model_by_alias=True
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
        pacientes = db.query(Paciente).filter(Paciente.cns == termo, Paciente.ativo.is_(True)).all()
    else:
        pacientes = (
            db.query(Paciente)
            .filter(Paciente.nome.ilike(f"%{termo}%"), Paciente.ativo.is_(True))
            .all()
        )

    return [
        PacienteConsultaOut(id=p.id, nome=p.nome, data_nascimento=p.data_nascimento, cns=p.cns)
        for p in pacientes
    ]


@router.post(
    "/iniciar", response_model=ConsultaIniciarOut, status_code=201, response_model_by_alias=True
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


@router.post("/{id_consulta}/triagem", response_model=Etapa1Out, response_model_by_alias=True)
def salvar_triagem(
    id_consulta: UUID,
    payload: TriagemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO", "ENFERMEIRO")),
):
    consulta = _consulta_ou_404(id_consulta, db)
    triagem = db.query(ConsultaTriagem).filter(ConsultaTriagem.id_consulta == id_consulta).first()
    if not triagem:
        triagem = ConsultaTriagem(id_consulta=id_consulta, registrado_por=current_user.id)
        db.add(triagem)
    triagem.peso_kg = payload.peso_kg
    triagem.pa_sistolica = payload.pa_sistolica
    triagem.pa_diastolica = payload.pa_diastolica
    consulta.triagem_concluida = True
    consulta.triagem_concluida_em = datetime.now(timezone.utc)
    db.commit()
    db.refresh(consulta)
    return _build_etapa1_out(consulta, db)


@router.get("/{id_consulta}/etapa1", response_model=Etapa1Out, response_model_by_alias=True)
def obter_etapa1(
    id_consulta: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO", "ENFERMEIRO")),
):
    return _build_etapa1_out(_consulta_ou_404(id_consulta, db), db)


@router.post("/{id_consulta}/relato", response_model=RelatoOut, response_model_by_alias=True)
def criar_relato(
    id_consulta: UUID,
    payload: RelatoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO")),
):
    _consulta_ou_404(id_consulta, db)
    relato = db.query(ConsultaRelato).filter(ConsultaRelato.id_consulta == id_consulta).first()
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


@router.patch("/{id_consulta}/relato", response_model=RelatoOut, response_model_by_alias=True)
def atualizar_relato(
    id_consulta: UUID,
    payload: RelatoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO")),
):
    _consulta_ou_404(id_consulta, db)
    relato = db.query(ConsultaRelato).filter(ConsultaRelato.id_consulta == id_consulta).first()
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


@router.get("/{id_consulta}/relato", response_model=RelatoOut, response_model_by_alias=True)
def obter_relato(
    id_consulta: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO")),
):
    _consulta_ou_404(id_consulta, db)
    relato = db.query(ConsultaRelato).filter(ConsultaRelato.id_consulta == id_consulta).first()
    if not relato:
        raise HTTPException(status_code=404, detail="Relato nao encontrado")
    return _build_relato_out(relato)


@router.post(
    "/{id_consulta}/audio/iniciar", response_model=AudioIniciarOut, response_model_by_alias=True
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


@router.post("/{id_consulta}/analisar", response_model=ResultadoIAOut, response_model_by_alias=True)
def analisar_consulta(
    id_consulta: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO")),
):
    _consulta_ou_404(id_consulta, db)
    relato = db.query(ConsultaRelato).filter(ConsultaRelato.id_consulta == id_consulta).first()
    if not relato or not relato.relato_texto:
        raise HTTPException(status_code=400, detail="Informe o relato antes da analise")
    audio = _ultimo_audio(id_consulta, db)
    resultado_ia = analisar(
        relato.relato_texto, audio.transcricao if audio else None, id_consulta=id_consulta
    )

    resultado = (
        db.query(ConsultaResultado).filter(ConsultaResultado.id_consulta == id_consulta).first()
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


@router.get("/{id_consulta}/resultado", response_model=ResultadoIAOut, response_model_by_alias=True)
def obter_resultado(
    id_consulta: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO")),
):
    _consulta_ou_404(id_consulta, db)
    resultado = (
        db.query(ConsultaResultado).filter(ConsultaResultado.id_consulta == id_consulta).first()
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
        db.query(ConsultaResultado).filter(ConsultaResultado.id_consulta == id_consulta).first()
    )
    if not resultado:
        raise HTTPException(status_code=404, detail="Resultado nao encontrado")
    resultado.confirmado = True
    resultado.confirmado_em = datetime.now(timezone.utc)
    db.commit()
    db.refresh(resultado)
    return _build_resultado_out(resultado, db)


# ---------------------------------------------------------------------------
# Etapa 3 — Encerramento
# ---------------------------------------------------------------------------


@router.get(
    "/{id_consulta}/encerramento/sugestao",
    response_model=SugestaoEncerramentoOut,
    response_model_by_alias=True,
)
def obter_sugestao_encerramento(
    id_consulta: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO")),
):
    consulta = _consulta_ou_404(id_consulta, db)
    resultado = (
        db.query(ConsultaResultado).filter(ConsultaResultado.id_consulta == id_consulta).first()
    )
    if not resultado:
        raise HTTPException(status_code=404, detail="Resultado de analise nao encontrado")
    data_sugerida = calcular_data_sugerida(resultado.faixa_risco, consulta.ig_semanas)
    encs = encaminhamentos_sugeridos(resultado.faixa_risco)
    return SugestaoEncerramentoOut(
        data_sugerida=data_sugerida,
        encaminhamentos_sugeridos=encs,
        conduta_sugerida=resultado.resumo_ia or "",
    )


@router.post(
    "/{id_consulta}/encerrar",
    response_model=EncerramentoOut,
    status_code=201,
    response_model_by_alias=True,
)
def encerrar_consulta(
    id_consulta: UUID,
    payload: EncerramentoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO")),
):
    consulta = _consulta_ou_404(id_consulta, db)
    if consulta.status == "ENCERRADA":
        raise HTTPException(status_code=409, detail="Consulta ja encerrada")
    enc_existente = (
        db.query(ConsultaEncerramento)
        .filter(ConsultaEncerramento.id_consulta == id_consulta)
        .first()
    )
    if enc_existente:
        raise HTTPException(status_code=409, detail="Encerramento ja registrado")

    encerramento = ConsultaEncerramento(
        id_consulta=id_consulta,
        conduta=payload.conduta,
        encaminhamentos=payload.encaminhamentos,
        data_proximo_retorno=payload.data_proximo_retorno,
        observacoes=payload.observacoes,
        encerrado_por=current_user.id,
    )
    db.add(encerramento)
    consulta.status = "ENCERRADA"
    consulta.encerrada_em = datetime.now(timezone.utc)
    db.commit()
    db.refresh(encerramento)

    return EncerramentoOut(
        id_consulta=encerramento.id_consulta,
        conduta=encerramento.conduta,
        encaminhamentos=encerramento.encaminhamentos,
        data_proximo_retorno=encerramento.data_proximo_retorno,
        observacoes=encerramento.observacoes,
        encerrado_em=encerramento.encerrado_em,
    )


@router.get("/{id_consulta}/resumo-pec", response_model=ResumoPecOut, response_model_by_alias=True)
def obter_resumo_pec(
    id_consulta: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO")),
):
    consulta = _consulta_ou_404(id_consulta, db)
    if consulta.status != "ENCERRADA":
        raise HTTPException(
            status_code=400, detail="Resumo disponivel apenas para consultas encerradas"
        )

    triagem = db.query(ConsultaTriagem).filter(ConsultaTriagem.id_consulta == id_consulta).first()
    resultado = (
        db.query(ConsultaResultado).filter(ConsultaResultado.id_consulta == id_consulta).first()
    )
    encerramento = (
        db.query(ConsultaEncerramento)
        .filter(ConsultaEncerramento.id_consulta == id_consulta)
        .first()
    )

    if not resultado or not encerramento:
        raise HTTPException(status_code=404, detail="Dados incompletos para gerar o resumo")

    pa = f"{triagem.pa_sistolica}/{triagem.pa_diastolica} mmHg" if triagem else None
    indicadores_desc = (
        [i["descricao"] for i in resultado.indicadores] if resultado.indicadores else []
    )

    return ResumoPecOut(
        id_consulta=consulta.id_consulta,
        tipo_consulta=consulta.tipo_consulta,
        data_consulta=consulta.aberta_em.date(),
        ig_semanas=consulta.ig_semanas,
        ig_dias=consulta.ig_dias,
        peso_kg=float(triagem.peso_kg) if triagem else None,
        pa=pa,
        score_risco=resultado.score_geral,
        faixa_risco=resultado.faixa_risco,
        indicadores=indicadores_desc,
        conduta=encerramento.conduta,
        encaminhamentos=encerramento.encaminhamentos or [],
        data_proximo_retorno=encerramento.data_proximo_retorno,
        gerado_em=datetime.now(timezone.utc),
    )


@router.get("/{id_consulta}/resumo-pec/pdf")
def baixar_resumo_pec_pdf(
    id_consulta: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO")),
):
    resumo = obter_resumo_pec(id_consulta=id_consulta, db=db, current_user=current_user)
    pdf_bytes = gerar_pdf_resumo(resumo)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=resumo-pec-{id_consulta}.pdf"},
    )
