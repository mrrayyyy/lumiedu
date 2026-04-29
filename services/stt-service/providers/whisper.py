from __future__ import annotations

import logging
import tempfile

from config import settings

logger = logging.getLogger("stt.whisper")

_model = None


def _load_model():
    global _model
    if _model is not None:
        return _model
    try:
        from faster_whisper import WhisperModel

        logger.info("loading model=%s device=%s", settings.model_size, settings.device)
        _model = WhisperModel(
            settings.model_size,
            device=settings.device,
            compute_type=settings.compute_type,
        )
        logger.info("model loaded")
        return _model
    except Exception as exc:
        logger.warning("load failed: %s", exc)
        return None


class WhisperProvider:
    @staticmethod
    def is_available() -> bool:
        return _load_model() is not None

    @staticmethod
    def transcribe(audio_bytes: bytes, language: str) -> str | None:
        model = _load_model()
        if model is None:
            return None

        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmp:
                tmp.write(audio_bytes)
                tmp.flush()

                vad_params = (
                    {"min_silence_duration_ms": settings.vad_min_silence_ms}
                    if settings.vad_enabled
                    else None
                )
                segments, _ = model.transcribe(
                    tmp.name,
                    language=language if language != "auto" else None,
                    beam_size=settings.beam_size,
                    vad_filter=settings.vad_enabled,
                    vad_parameters=vad_params,
                )
                texts = [seg.text.strip() for seg in segments if seg.text.strip()]
                return " ".join(texts) if texts else None
        except Exception as exc:
            logger.warning("transcribe failed: %s", exc)
            return None
