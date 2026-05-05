import io
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.db.session import get_db
from app.models.consulta import ConsultaEncerramento, ConsultaResultado, ConsultaTriagem
from app.models.user import User
from app.schemas.consulta import (
    EncerramentoCreate,
    EncerramentoOut,
    ResumoPecOut,
    SugestaoEncerramentoOut,
)
from app.services.encerramento_service import (
    calcular_data_sugerida,
    encaminhamentos_sugeridos,
    gerar_pdf_resumo,
)

from .helpers import _consulta_ou_404

router = APIRouter()


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
        db.query(ConsultaResultado)
        .filter(ConsultaResultado.id_consulta == id_consulta)
        .first()
    )
    if not resultado:
        raise HTTPException(
            status_code=404, detail="Resultado de analise nao encontrado"
        )
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


@router.get(
    "/{id_consulta}/resumo-pec",
    response_model=ResumoPecOut,
    response_model_by_alias=True,
)
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

    triagem = (
        db.query(ConsultaTriagem)
        .filter(ConsultaTriagem.id_consulta == id_consulta)
        .first()
    )
    resultado = (
        db.query(ConsultaResultado)
        .filter(ConsultaResultado.id_consulta == id_consulta)
        .first()
    )
    encerramento = (
        db.query(ConsultaEncerramento)
        .filter(ConsultaEncerramento.id_consulta == id_consulta)
        .first()
    )

    if not resultado or not encerramento:
        raise HTTPException(
            status_code=404, detail="Dados incompletos para gerar o resumo"
        )

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
        headers={
            "Content-Disposition": f"attachment; filename=resumo-pec-{id_consulta}.pdf"
        },
    )
