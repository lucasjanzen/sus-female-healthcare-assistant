import logging
import urllib.parse
import urllib.request
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


def transcrever_audio(audio_bytes: bytes, content_type: str) -> Optional[str]:
    """Transcreve áudio usando a REST API do Azure AI Speech (modo conversa, até ~10 min).
    Retorna None se o Azure não estiver configurado ou se a transcrição falhar.
    Formatos suportados: audio/webm, audio/ogg, audio/wav, audio/mp4.
    """
    if not settings.azure_speech_key or not settings.azure_speech_region:
        logger.info("Azure Speech nao configurado; transcricao indisponivel.")
        return None

    base = (
        f"https://{settings.azure_speech_region}.stt.speech.microsoft.com"
        "/speech/recognition/conversation/cognitiveservices/v1"
    )
    params = urllib.parse.urlencode({"language": "pt-BR", "format": "detailed"})
    url = f"{base}?{params}"

    req = urllib.request.Request(
        url,
        data=audio_bytes,
        headers={
            "Ocp-Apim-Subscription-Key": settings.azure_speech_key,
            "Content-Type": content_type or "audio/webm",
        },
        method="POST",
    )
    try:
        import json

        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
        if data.get("RecognitionStatus") == "Success":
            return data.get("DisplayText")
        logger.warning("Azure Speech status inesperado: %s", data.get("RecognitionStatus"))
    except Exception as exc:
        logger.error("Erro ao chamar Azure Speech: %s", exc)
    return None


def analisar_sentimento_azure(texto: str) -> Optional[dict]:
    """Analisa sentimento usando o SDK azure-ai-textanalytics.
    Retorna dict com 'sentimento' (positive/neutral/negative/mixed) e 'scores',
    ou None se o Azure não estiver configurado ou ocorrer erro.
    """
    if not settings.azure_language_key or not settings.azure_language_endpoint:
        logger.info("Azure Language nao configurado; sentimento local sera usado.")
        return None

    try:
        from azure.ai.textanalytics import TextAnalyticsClient
        from azure.core.credentials import AzureKeyCredential

        client = TextAnalyticsClient(
            endpoint=settings.azure_language_endpoint,
            credential=AzureKeyCredential(settings.azure_language_key),
        )
        docs = client.analyze_sentiment([texto], language="pt")
        doc = docs[0]
        if doc.is_error:
            logger.error("Azure Language retornou erro: %s", doc.error)
            return None
        return {
            "sentimento": doc.sentiment,
            "scores": {
                "positivo": round(doc.confidence_scores.positive, 3),
                "neutro": round(doc.confidence_scores.neutral, 3),
                "negativo": round(doc.confidence_scores.negative, 3),
            },
        }
    except Exception as exc:
        logger.error("Erro ao chamar Azure Language: %s", exc)
        return None
