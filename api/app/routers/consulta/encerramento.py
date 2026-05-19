from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.db.session import get_db
from app.models.user import User
from app.schemas.analise import EncerramentoSimplesOut
from app.tasks.analise_task import processar_analise

from .helpers import _exigir_em_atendimento_do_medico

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
    audio: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("MEDICO")),
):
    consulta = _exigir_em_atendimento_do_medico(id_consulta, current_user.id, db)

    consulta.status = "ENCERRADA"
    consulta.encerrada_em = datetime.now(timezone.utc)
    consulta.analise_concluida_em = None
    consulta.analise_erro = None
    db.commit()

    blob_name: Optional[str] = None
    content_type = "audio/webm"
    if audio:
        content_type = audio.content_type or "audio/webm"
        ext = ".webm" if "webm" in content_type else ".wav"
        blob_name = f"{id_consulta}{ext}"
        from app.services.blob_service import upload_audio
        upload_audio(blob_name, await audio.read())

    processar_analise.delay(str(id_consulta), blob_name, content_type)

    return EncerramentoSimplesOut(
        id_consulta=id_consulta,
        status="ENCERRADA",
        mensagem="Consulta encerrada. A análise será processada em breve e estará disponível na Fila de Análises.",
    )
