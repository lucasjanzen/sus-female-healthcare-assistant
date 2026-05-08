import io
import json
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

    fmt = "webm" if "webm" in content_type else "ogg"
    seg = AudioSegment.from_file(io.BytesIO(audio_bytes), format=fmt)
    seg = seg.set_frame_rate(16000).set_channels(1).set_sample_width(2)
    buf = io.BytesIO()
    seg.export(buf, format="wav")
    return buf.getvalue()


def _identificar_speaker_paciente(trechos: list[dict]) -> str:
    """Heurística: paciente = speaker com maior tempo total de fala."""
    tempo_por_speaker: dict[str, float] = {}
    for t in trechos:
        sid = t.get("speaker_id", "")
        tempo_por_speaker[sid] = tempo_por_speaker.get(sid, 0) + t.get("duracao_ms", 0)
    return max(tempo_por_speaker, key=tempo_por_speaker.get) if tempo_por_speaker else ""


def transcrever_e_analisar_voz(
    audio_bytes: bytes,
    content_type: str = "audio/webm",
) -> dict:
    """Transcrição + sentimento vocal via Azure Conversation Transcription com diarização.

    Retorna dict com 'transcricao' (str) e 'sentimento_voz' (dict | None).
    sentimento_voz inclui 'dominante', 'scores', '_por_trecho_interno', '_speaker_paciente'.
    """
    if not settings.azure_speech_key or not settings.azure_speech_region:
        logger.info("Azure Speech nao configurado; transcricao indisponivel.")
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
        speech_config.output_format = speechsdk.OutputFormat.Detailed
        speech_config.set_property(
            speechsdk.PropertyId.SpeechServiceResponse_DiarizeIntermediateResults,
            "false",
        )

        audio_config = speechsdk.audio.AudioConfig(filename=tmp_path)
        transcriber = speechsdk.transcription.ConversationTranscriber(
            speech_config=speech_config,
            audio_config=audio_config,
        )

        trechos: list[dict] = []
        done = threading.Event()

        def on_transcribed(evt):
            if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                payload = json.loads(evt.result.json)
                nbest = payload.get("NBest", [{}])
                trechos.append({
                    "speaker_id": evt.result.speaker_id,
                    "texto": evt.result.text,
                    "duracao_ms": evt.result.duration / 10_000,
                    "sentiment": nbest[0].get("Sentiment"),
                })

        def on_session_stopped(evt):
            done.set()

        transcriber.transcribed.connect(on_transcribed)
        transcriber.session_stopped.connect(on_session_stopped)
        transcriber.canceled.connect(on_session_stopped)

        transcriber.start_transcribing_async()
        done.wait(timeout=600)
        transcriber.stop_transcribing_async()

        texto_completo = " ".join(t["texto"] for t in trechos)
        speaker_paciente = _identificar_speaker_paciente(trechos)

        trechos_paciente = [
            t for t in trechos
            if t["speaker_id"] == speaker_paciente and t["sentiment"] is not None
        ]

        if not trechos_paciente:
            logger.info("Nenhum trecho com sentimento detectado (regiao sem suporte ou paciente nao identificado).")
            return {"transcricao": texto_completo, "sentimento_voz": None}

        total_ms = sum(t["duracao_ms"] for t in trechos_paciente) or 1
        scores: dict[str, float] = {"positivo": 0.0, "negativo": 0.0, "neutro": 0.0}
        for t in trechos_paciente:
            peso = t["duracao_ms"] / total_ms
            scores["positivo"] += t["sentiment"]["Positive"] * peso
            scores["negativo"] += t["sentiment"]["Negative"] * peso
            scores["neutro"] += t["sentiment"]["Neutral"] * peso

        dominante = max(scores, key=scores.get).upper()

        return {
            "transcricao": texto_completo,
            "sentimento_voz": {
                "dominante": dominante,
                "scores": scores,
                "_por_trecho_interno": [
                    {"speaker_id": t["speaker_id"], **t["sentiment"]}
                    for t in trechos_paciente
                ],
                "_speaker_paciente": speaker_paciente,
            },
        }

    except Exception as exc:
        logger.error("Erro em transcrever_e_analisar_voz: %s", exc)
        return {"transcricao": "", "sentimento_voz": None}
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
