import io
import logging
import os
import tempfile
import threading
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


def _converter_para_wav(audio_bytes: bytes, content_type: str) -> bytes:
    """Converte webm/ogg para WAV 16 kHz mono exigido pelo SDK de fala."""
    from pydub import AudioSegment

    tmp_in = None
    try:
        # Sem extensão reconhecida → pydub não passa -f ao ffmpeg → auto-detecção
        with tempfile.NamedTemporaryFile(suffix=".audio", delete=False) as f:
            f.write(audio_bytes)
            tmp_in = f.name
        seg = AudioSegment.from_file(tmp_in)
        logger.info("Audio original — duracao=%.1fs canais=%d frame_rate=%d", seg.duration_seconds, seg.channels, seg.frame_rate)
        seg = seg.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        buf = io.BytesIO()
        seg.export(buf, format="wav")
        wav_bytes = buf.getvalue()
        logger.info("WAV convertido — tamanho=%d bytes duracao=%.1fs", len(wav_bytes), seg.duration_seconds)
        return wav_bytes
    finally:
        if tmp_in and os.path.exists(tmp_in):
            os.remove(tmp_in)



def transcrever_e_analisar_voz(
    audio_bytes: bytes,
    content_type: str = "audio/webm",
) -> dict:
    """Transcrição via Azure SpeechRecognizer contínuo + sentimento via Language Analytics.

    Retorna dict com 'transcricao' (str) e 'sentimento_voz' (dict | None).
    """
    if not settings.azure_speech_key or not settings.azure_speech_region:
        logger.warning("Azure Speech nao configurado; transcricao indisponivel.")
        return {"transcricao": "", "sentimento_voz": None}

    tmp_path = None
    try:
        import azure.cognitiveservices.speech as speechsdk

        wav_bytes = _converter_para_wav(audio_bytes, content_type)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(wav_bytes)
            tmp_path = tmp.name

        speech_config = speechsdk.SpeechConfig(
            subscription=settings.azure_speech_key,
            region=settings.azure_speech_region,
        )
        speech_config.speech_recognition_language = "pt-BR"

        audio_config = speechsdk.audio.AudioConfig(filename=tmp_path)
        recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            audio_config=audio_config,
        )

        segmentos: list[str] = []
        done = threading.Event()

        def on_recognized(evt):
            if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech and evt.result.text:
                segmentos.append(evt.result.text)
                logger.warning("Segmento reconhecido: %r", evt.result.text[:80])

        def on_session_stopped(evt):
            done.set()

        def on_canceled(evt):
            details = evt.result.cancellation_details
            if details.reason != speechsdk.CancellationReason.EndOfStream:
                logger.warning("SpeechRecognizer cancelado — %s: %s", details.reason, details.error_details)
            done.set()

        recognizer.recognized.connect(on_recognized)
        recognizer.session_stopped.connect(on_session_stopped)
        recognizer.canceled.connect(on_canceled)

        recognizer.start_continuous_recognition_async().get()
        done.wait(timeout=120)
        recognizer.stop_continuous_recognition_async().get()

        texto_completo = " ".join(segmentos)
        logger.warning("Transcricao concluida — %d segmentos, texto=%r", len(segmentos), texto_completo[:120])

        if not texto_completo:
            return {"transcricao": "", "sentimento_voz": None}

        sentimento = analisar_sentimento_azure(texto_completo)
        if not sentimento:
            return {"transcricao": texto_completo, "sentimento_voz": None}

        scores = sentimento["scores"]
        dominante = max(scores, key=scores.get).upper()
        return {
            "transcricao": texto_completo,
            "sentimento_voz": {
                "dominante": dominante,
                "scores": scores,
            },
        }

    except Exception as exc:
        logger.error("Erro em transcrever_e_analisar_voz: %s", exc)
        return {"transcricao": "", "sentimento_voz": None}
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError as e:
                logger.warning("Nao foi possivel remover arquivo temp %s: %s", tmp_path, e)
