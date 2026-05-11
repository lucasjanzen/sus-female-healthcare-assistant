import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.db.session import get_db
from app.models.consulta import ConsultaAudio, ConsultaRelato, ConsultaResultado
from app.models.user import User
from app.schemas.consulta import (
    RelatoCreate,
    RelatoOut,
    RelatoUpdate,
    ResultadoIAOut,
)
import app.services.analise_service as analise_service
import app.services.analise_llm_service as analise_llm_service

from .helpers import (
    _build_relato_out,
    _build_resultado_out,
    _consulta_ou_404,
)

MAX_AUDIO_SIZE_BYTES = 60 * 1024 * 1024  # 60 MB

logger = logging.getLogger(__name__)
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
    "/{id_consulta}/analisar",
    response_model=ResultadoIAOut,
    response_model_by_alias=True,
)
async def analisar_consulta(
    id_consulta: UUID,
    audio: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO")),
):
    _consulta_ou_404(id_consulta, db)

    relato = (
        db.query(ConsultaRelato)
        .filter(ConsultaRelato.id_consulta == id_consulta)
        .first()
    )
    relato_texto = relato.relato_texto if relato else ""

    audio_bytes: Optional[bytes] = None
    audio_content_type = "audio/webm"

    if audio:
        audio_bytes = await audio.read()
        if len(audio_bytes) > MAX_AUDIO_SIZE_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"Arquivo de audio excede o limite de {MAX_AUDIO_SIZE_BYTES // (1024 * 1024)} MB.",
            )
        audio_content_type = audio.content_type or "audio/webm"
    elif not relato_texto:
        raise HTTPException(status_code=400, detail="Informe o relato antes da analise")

    try:
        resultado_ia = await analise_service.analisar(
            relato_texto=relato_texto,
            id_consulta=id_consulta,
            audio_bytes=audio_bytes,
            audio_content_type=audio_content_type,
        )
    except Exception as exc:
        logger.error("Falha no processamento de áudio para consulta %s: %s", id_consulta, exc)
        raise HTTPException(status_code=502, detail="Serviço de análise indisponível. Tente novamente.")

    sentimento_voz_dict = (
        resultado_ia.sentimento_voz.model_dump() if resultado_ia.sentimento_voz else None
    )

    # Persiste a transcrição para o LLM ler
    if resultado_ia.transcricao:
        db.add(ConsultaAudio(
            id_consulta=id_consulta,
            transcricao=resultado_ia.transcricao,
        ))

    # Cria / atualiza resultado parcial com sentimento_voz antes de chamar o LLM
    resultado = (
        db.query(ConsultaResultado)
        .filter(ConsultaResultado.id_consulta == id_consulta)
        .first()
    )
    if not resultado:
        resultado = ConsultaResultado(id_consulta=id_consulta, indicadores=[])
        db.add(resultado)

    resultado.sentimento_voz = sentimento_voz_dict
    resultado.score_geral = resultado_ia.score_geral
    resultado.faixa_risco = resultado_ia.faixa_risco
    resultado.indicadores = [i.model_dump() for i in resultado_ia.indicadores]
    resultado.resumo_ia = resultado_ia.resumo_ia
    resultado.calculado_em = datetime.now(timezone.utc)
    resultado.confirmado = False
    resultado.confirmado_em = None
    db.flush()

    # Análise LLM (GPT-4o com fallback local) — executado em thread para não bloquear o event loop
    resultado_llm = await asyncio.to_thread(analise_llm_service.analisar_com_llm, id_consulta, db)

    resultado.score_geral = int(resultado_llm["score_geral"])
    resultado.faixa_risco = resultado_llm["faixa_risco"]
    resultado.resumo_ia = resultado_llm["resumo_ia"]
    resultado.indicadores = _llm_indicadores_para_ia(resultado_llm["indicadores"])
    resultado.sumario_estruturado = resultado_llm["sumario_estruturado"]
    resultado.texto_clinico = resultado_llm["texto_clinico"]
    resultado.fontes_utilizadas = resultado_llm["fontes_utilizadas"]
    resultado.tokens_utilizados = resultado_llm["tokens_utilizados"]

    db.commit()
    db.refresh(resultado)
    return _build_resultado_out(resultado)


def _llm_indicadores_para_ia(indicadores_llm: list) -> list:
    """Converte IndicadorRisco (LLM) para formato legado IndicadorIA."""
    result = []
    for ind in indicadores_llm:
        evidencias = ind.get("evidencias", [])
        result.append({
            "tipo": ind.get("tipo", ""),
            "nivel": ind.get("nivel", "BAIXO"),
            "descricao": "; ".join(evidencias) if evidencias else ind.get("recomendacao", ""),
            "origem": "LLM",
        })
    return result


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
    return _build_resultado_out(resultado)


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
    return _build_resultado_out(resultado)
