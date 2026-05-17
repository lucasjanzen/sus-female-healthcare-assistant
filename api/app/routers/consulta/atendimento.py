import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.db.session import SessionLocal, get_db
from app.models.consulta import ConsultaIdentidade, ConsultaRelato, ConsultaResultado
from app.models.user import User
from app.schemas.consulta import (
    RelatoCreate,
    RelatoOut,
    RelatoUpdate,
    ResultadoIAOut,
)
import app.services.analise_llm_service as analise_llm_service

from .helpers import (
    _build_relato_out,
    _build_resultado_out,
    _consulta_ou_404,
)

MAX_AUDIO_SIZE_BYTES = 60 * 1024 * 1024  # 60 MB

logger = logging.getLogger(__name__)
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
        raise HTTPException(status_code=404, detail="Relato não encontrado")
    return _build_relato_out(relato)


# ---------------------------------------------------------------------------
# Análise — lógica híbrida
# ---------------------------------------------------------------------------

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


def _processar_audio_background(
    id_consulta: UUID,
    audio_bytes: bytes,
    content_type: str,
    relato_texto: str,
) -> None:
    """Processa áudio em background (roda em thread pool via BackgroundTasks)."""
    db = SessionLocal()
    try:
        from app.services.azure_service import transcrever_e_analisar_voz

        resultado_voz = transcrever_e_analisar_voz(audio_bytes, content_type)
        transcricao = resultado_voz.get("transcricao", "")
        sentimento_voz = resultado_voz.get("sentimento_voz")

        resultado_llm = analise_llm_service.analisar_com_llm(
            id_consulta, db, transcricao or "", sentimento_voz
        )

        resultado = (
            db.query(ConsultaResultado)
            .filter(ConsultaResultado.id_consulta == id_consulta)
            .first()
        )
        if not resultado:
            resultado = ConsultaResultado(id_consulta=id_consulta, indicadores=[])
            db.add(resultado)

        resultado.sentimento_voz = sentimento_voz
        resultado.score_geral = int(resultado_llm["score_geral"])
        resultado.faixa_risco = resultado_llm["faixa_risco"]
        resultado.resumo_ia = resultado_llm["resumo_ia"]
        resultado.indicadores = _llm_indicadores_para_ia(resultado_llm["indicadores"])
        resultado.sumario_estruturado = resultado_llm["sumario_estruturado"]
        resultado.texto_clinico = resultado_llm["texto_clinico"]
        resultado.fontes_utilizadas = resultado_llm["fontes_utilizadas"]
        resultado.tokens_utilizados = resultado_llm["tokens_utilizados"]
        resultado.prompt_enviado = resultado_llm.get("prompt_enviado")
        resultado.resposta_bruta_llm = resultado_llm.get("resposta_bruta_llm")
        resultado.calculado_em = datetime.now(timezone.utc)
        resultado.confirmado = False
        resultado.confirmado_em = None

        # Volta para EM_ATENDIMENTO → aparece na seção "Para Finalizar" da fila
        consulta = (
            db.query(ConsultaIdentidade)
            .filter(ConsultaIdentidade.id_consulta == id_consulta)
            .first()
        )
        if consulta:
            consulta.status = "EM_ATENDIMENTO"

        db.commit()
        logger.warning("Análise em background concluída para consulta %s", id_consulta)

    except Exception as exc:
        logger.error("Falha na análise em background para consulta %s: %s", id_consulta, exc)
        try:
            consulta = (
                db.query(ConsultaIdentidade)
                .filter(ConsultaIdentidade.id_consulta == id_consulta)
                .first()
            )
            if consulta:
                consulta.status = "EM_ATENDIMENTO"
            db.commit()
        except Exception:
            pass
    finally:
        db.close()


@router.post("/{id_consulta}/analisar")
async def analisar_consulta(
    id_consulta: UUID,
    background_tasks: BackgroundTasks,
    audio: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO")),
):
    consulta = _consulta_ou_404(id_consulta, db)

    relato = (
        db.query(ConsultaRelato)
        .filter(ConsultaRelato.id_consulta == id_consulta)
        .first()
    )
    relato_texto = relato.relato_texto if relato else ""

    # ------------------------------------------------------------------
    # CENÁRIO A — com áudio: libera o médico imediatamente
    # ------------------------------------------------------------------
    if audio:
        audio_bytes = await audio.read()
        if len(audio_bytes) > MAX_AUDIO_SIZE_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"Arquivo de áudio excede o limite de {MAX_AUDIO_SIZE_BYTES // (1024 * 1024)} MB.",
            )
        audio_content_type = audio.content_type or "audio/webm"

        consulta.status = "AGUARDANDO_ANALISE"
        db.commit()

        background_tasks.add_task(
            _processar_audio_background,
            id_consulta,
            audio_bytes,
            audio_content_type,
            relato_texto,
        )

        return JSONResponse(
            status_code=202,
            content={
                "status": "AGUARDANDO_ANALISE",
                "mensagem": "Análise em processamento. O resultado estará disponível em breve na fila.",
            },
        )

    # ------------------------------------------------------------------
    # CENÁRIO B — sem áudio: resposta síncrona com resultado inline
    # ------------------------------------------------------------------
    if not relato_texto:
        raise HTTPException(status_code=400, detail="Informe o relato antes da análise")

    try:
        resultado_llm = await asyncio.to_thread(
            analise_llm_service.analisar_com_llm,
            id_consulta,
            db,
            "",
            None,
        )
    except Exception as exc:
        logger.error("Falha na análise LLM para consulta %s: %s", id_consulta, exc)
        raise HTTPException(status_code=502, detail="Serviço de análise indisponível. Tente novamente.")

    resultado = (
        db.query(ConsultaResultado)
        .filter(ConsultaResultado.id_consulta == id_consulta)
        .first()
    )
    if not resultado:
        resultado = ConsultaResultado(id_consulta=id_consulta, indicadores=[])
        db.add(resultado)

    resultado.sentimento_voz = None
    resultado.score_geral = int(resultado_llm["score_geral"])
    resultado.faixa_risco = resultado_llm["faixa_risco"]
    resultado.resumo_ia = resultado_llm["resumo_ia"]
    resultado.indicadores = _llm_indicadores_para_ia(resultado_llm["indicadores"])
    resultado.sumario_estruturado = resultado_llm["sumario_estruturado"]
    resultado.texto_clinico = resultado_llm["texto_clinico"]
    resultado.fontes_utilizadas = resultado_llm["fontes_utilizadas"]
    resultado.tokens_utilizados = resultado_llm["tokens_utilizados"]
    resultado.prompt_enviado = resultado_llm.get("prompt_enviado")
    resultado.resposta_bruta_llm = resultado_llm.get("resposta_bruta_llm")
    resultado.calculado_em = datetime.now(timezone.utc)
    resultado.confirmado = False
    resultado.confirmado_em = None

    db.commit()
    db.refresh(resultado)
    return _build_resultado_out(resultado)


# ---------------------------------------------------------------------------
# Resultado
# ---------------------------------------------------------------------------

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
    consulta = _consulta_ou_404(id_consulta, db)
    resultado = (
        db.query(ConsultaResultado)
        .filter(ConsultaResultado.id_consulta == id_consulta)
        .first()
    )
    if not resultado:
        raise HTTPException(status_code=404, detail="Resultado não encontrado")

    # Apenas o médico responsável vê o resultado antes do encerramento
    if consulta.status != "ENCERRADA" and consulta.medico_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Resultado disponível apenas para o médico responsável.",
        )

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
        raise HTTPException(status_code=404, detail="Resultado não encontrado")
    resultado.confirmado = True
    resultado.confirmado_em = datetime.now(timezone.utc)
    db.commit()
    db.refresh(resultado)
    return _build_resultado_out(resultado)
