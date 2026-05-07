import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.azure_service import gerar_token_speech

logger = logging.getLogger(__name__)

router = APIRouter()


class SpeechTokenOut(BaseModel):
    token: str
    region: str


@router.get("/token", response_model=SpeechTokenOut)
def obter_token_speech(
    current_user: User = Depends(get_current_user),
) -> SpeechTokenOut:
    """Emite token temporário do Azure Speech STS (validade: 10 minutos).
    A subscription key nunca é exposta — apenas o token de curta duração é retornado.
    Requer autenticação JWT para evitar uso não autorizado.
    """
    if not settings.azure_speech_region:
        raise HTTPException(status_code=503, detail="Azure Speech nao configurado")

    token = gerar_token_speech()
    if not token:
        logger.error(
            "Falha ao emitir token Azure Speech para usuario %s", current_user.id
        )
        raise HTTPException(
            status_code=503,
            detail="Nao foi possivel gerar token Azure Speech. Tente novamente.",
        )

    logger.info("Token Azure Speech emitido para usuario %s", current_user.id)
    return SpeechTokenOut(token=token, region=settings.azure_speech_region)
