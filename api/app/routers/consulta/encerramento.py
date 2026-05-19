from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

import logging

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


@router.post(
    "/{id_consulta}/encerrar",
    response_model=EncerramentoSimplesOut,
    status_code=200,
    response_model_by_alias=True,
)
async def encerrar_consulta(
    id_consulta: UUID,
    background_tasks: BackgroundTasks,
    audio: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO")),
):
    consulta = _consulta_ou_404(id_consulta, db)
    if consulta.status == "ENCERRADA":
        raise HTTPException(status_code=409, detail="Consulta já encerrada")

    consulta.status = "ENCERRADA"
    consulta.encerrada_em = datetime.now(timezone.utc)
    consulta.analise_concluida_em = None
    consulta.analise_erro = None
    db.commit()

    audio_bytes: Optional[bytes] = None
    content_type = "audio/webm"
    if audio:
        audio_bytes = await audio.read()
        content_type = audio.content_type or "audio/webm"

    background_tasks.add_task(processar_analise, str(id_consulta), audio_bytes, content_type)

    return EncerramentoSimplesOut(
        id_consulta=id_consulta,
        status="ENCERRADA",
        mensagem="Consulta encerrada. A análise será processada em breve e estará disponível na Fila de Análises.",
    )
