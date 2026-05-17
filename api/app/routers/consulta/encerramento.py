from datetime import datetime, timezone
from uuid import UUID

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.db.session import get_db
from app.models.consulta import ConsultaEncerramento, ConsultaRelato, ConsultaResultado
from app.models.user import User
from app.schemas.consulta import (
    EncerramentoCreate,
    EncerramentoOut,
    SugestaoEncerramentoOut,
)
from app.services.encerramento_service import (
    calcular_data_sugerida,
    encaminhamentos_sugeridos,
)

from .helpers import _consulta_ou_404

logger = logging.getLogger(__name__)
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
            status_code=404, detail="Resultado de análise não encontrado"
        )
    data_sugerida = calcular_data_sugerida(resultado.faixa_risco, consulta.ig_semanas)

    # Encaminhamentos: preferir lista do LLM quando disponível
    encs_llm: list[str] = []
    if resultado.sumario_estruturado:
        encs_llm = resultado.sumario_estruturado.get("encaminhamentos_sugeridos", [])
    if encs_llm:
        encs = encs_llm
    else:
        logger.info(
            "Consulta %s: sumário LLM sem encaminhamentos — usando fallback por faixa de risco (%s).",
            id_consulta,
            resultado.faixa_risco,
        )
        encs = encaminhamentos_sugeridos(resultado.faixa_risco)

    # Conduta: parecer editado pelo médico > texto clínico do LLM > resumo legado
    relato = (
        db.query(ConsultaRelato)
        .filter(ConsultaRelato.id_consulta == id_consulta)
        .first()
    )
    conduta = (
        (relato.parecer_medico if relato and relato.parecer_medico else None)
        or resultado.texto_clinico
        or resultado.resumo_ia
        or ""
    )

    return SugestaoEncerramentoOut(
        data_sugerida=data_sugerida,
        encaminhamentos_sugeridos=encs,
        conduta_sugerida=conduta,
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
        raise HTTPException(status_code=409, detail="Consulta já encerrada")
    enc_existente = (
        db.query(ConsultaEncerramento)
        .filter(ConsultaEncerramento.id_consulta == id_consulta)
        .first()
    )
    if enc_existente:
        raise HTTPException(status_code=409, detail="Encerramento já registrado")

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
