import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.db.session import get_db
from app.models.user import User
from app.schemas.analise import EncerramentoSimplesOut
from app.tasks.analise_task import processar_analise

from .helpers import _consulta_ou_404

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_AUDIO_BYTES = 50 * 1024 * 1024


def _encerrar_consulta(id_consulta: UUID, db: Session):
    consulta = _consulta_ou_404(id_consulta, db)
    if consulta.status == "ENCERRADA":
        raise HTTPException(status_code=409, detail="Consulta ja encerrada")

    consulta.status = "ENCERRADA"
    consulta.encerrada_em = datetime.now(timezone.utc)
    consulta.analise_concluida_em = None
    consulta.analise_erro = None
    db.commit()
    return consulta


def _build_response(id_consulta: UUID) -> EncerramentoSimplesOut:
    return EncerramentoSimplesOut(
        id_consulta=id_consulta,
        status="ENCERRADA",
        mensagem=(
            "Consulta encerrada. A analise sera processada em breve e estara "
            "disponivel na Fila de Analises."
        ),
    )


@router.post(
    "/{id_consulta}/encerrar",
    response_model=EncerramentoSimplesOut,
    status_code=200,
    response_model_by_alias=True,
)
def encerrar_consulta(
    id_consulta: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO")),
):
    _encerrar_consulta(id_consulta, db)
    background_tasks.add_task(processar_analise, str(id_consulta))
    return _build_response(id_consulta)


@router.post(
    "/{id_consulta}/encerrar-com-audio",
    response_model=EncerramentoSimplesOut,
    status_code=200,
    response_model_by_alias=True,
)
def encerrar_consulta_com_audio(
    id_consulta: UUID,
    background_tasks: BackgroundTasks,
    audio: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO")),
):
    content_type = audio.content_type or "application/octet-stream"
    if not content_type.startswith("audio/"):
        raise HTTPException(status_code=415, detail="Arquivo de audio invalido")

    audio_bytes = audio.file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Arquivo de audio vazio")
    if len(audio_bytes) > MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="Arquivo de audio excede 50 MB")

    _encerrar_consulta(id_consulta, db)
    background_tasks.add_task(
        processar_analise,
        str(id_consulta),
        audio_bytes,
        content_type,
    )
    return _build_response(id_consulta)
