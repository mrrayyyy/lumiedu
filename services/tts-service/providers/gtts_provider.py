from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path

from config import settings

logger = logging.getLogger("tts.gtts")


class GTTSProvider:
    @staticmethod
    def is_available() -> bool:
        if not settings.gtts_enabled:
            return False
        try:
            import gtts  # noqa: F401
            return True
        except ImportError:
            return False

    @staticmethod
    def synthesize(text: str, language: str) -> str | None:
        if not text.strip():
            return None

        try:
            from gtts import gTTS

            cache_dir = Path(settings.audio_cache_dir)
            cache_dir.mkdir(parents=True, exist_ok=True)

            text_hash = hashlib.md5(f"{text}:{language}".encode()).hexdigest()[:16]
            filename = f"{text_hash}.mp3"
            filepath = cache_dir / filename

            if filepath.exists():
                return f"/audio/{filename}"

            GTTSProvider._cleanup_cache(cache_dir)

            tts = gTTS(text=text, lang=language, slow=settings.gtts_slow)
            tts.save(str(filepath))
            logger.info("synthesized %d chars -> %s", len(text), filename)
            return f"/audio/{filename}"
        except Exception as exc:
            logger.warning("gtts synthesis failed: %s", exc)
            return None

    @staticmethod
    def _cleanup_cache(cache_dir: Path) -> None:
        files = sorted(cache_dir.glob("*.mp3"), key=lambda f: f.stat().st_mtime)
        while len(files) > settings.max_cache_files:
            oldest = files.pop(0)
            try:
                oldest.unlink()
            except OSError:
                pass
