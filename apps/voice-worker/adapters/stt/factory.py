import logging
from typing import Optional
from core.interfaces import BaseSTTAdapter
from core.config import settings
from adapters.stt.deepgram_adapter import DeepgramSTTAdapter
from adapters.stt.whisper_adapter import WhisperSTTAdapter

logger = logging.getLogger("voice-worker.stt.factory")


class STTFactory:
    """Factory to instantiate the appropriate STT adapter based on configuration."""

    @staticmethod
    def get_adapter(provider: Optional[str] = None) -> BaseSTTAdapter:
        selected = (provider or settings.STT_PROVIDER).lower()

        if selected == "deepgram":
            logger.info("Instantiating DeepgramSTTAdapter...")
            return DeepgramSTTAdapter()
        elif selected in ("whisper", "whisper_local"):
            logger.info("Instantiating WhisperSTTAdapter...")
            return WhisperSTTAdapter()
        else:
            logger.warning(f"Unknown STT provider '{selected}', defaulting to DeepgramSTTAdapter.")
            return DeepgramSTTAdapter()
