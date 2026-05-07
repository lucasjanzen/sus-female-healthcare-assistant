import logging
import urllib.parse
import urllib.request
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


def gerar_token_speech() -> Optional[str]:
    """Gera token temporário para o Azure Speech SDK (válido por 10 minutos).
    O token é emitido pelo STS do Azure — a subscription key nunca sai do backend.
    Retorna None se o Azure não estiver configurado ou se a requisição falhar.
    """
    if not settings.azure_speech_key or not settings.azure_speech_region:
        logger.info("Azure Speech nao configurado; token indisponivel.")
        return None

    url = (
        f"https://{settings.azure_speech_region}"
        ".api.cognitive.microsoft.com/sts/v1.0/issueToken"
    )
    req = urllib.request.Request(
        url,
        data=b"",
        headers={
            "Ocp-Apim-Subscription-Key": settings.azure_speech_key,
            "Content-Type": "application/x-www-form-urlencoded",
            "Content-Length": "0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            token = resp.read().decode("utf-8")
        logger.info("Token Azure Speech gerado com sucesso.")
        return token
    except Exception as exc:
        logger.error("Erro ao gerar token Azure Speech: %s", exc)
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
