import logging
from typing import Optional
from core.interfaces import BaseTTSAdapter
from core.config import settings
from adapters.tts.cartesia_adapter import CartesiaTTSAdapter
from adapters.tts.gcp_tts_adapter import GCPTTSAdapter

logger = logging.getLogger("voice-worker.tts.factory")


class TTSFactory:
    """Factory to instantiate the appropriate TTS adapter based on configuration."""

    @staticmethod
    def get_adapter(provider: Optional[str] = None) -> BaseTTSAdapter:
        selected = (provider or settings.TTS_PROVIDER).lower()

        if selected == "cartesia":
            logger.info("Instantiating CartesiaTTSAdapter...")
            return CartesiaTTSAdapter()
        elif selected in ("gcp_tts", "google"):
            logger.info("Instantiating GCPTTSAdapter...")
            return GCPTTSAdapter()
        else:
            logger.warning(f"Unknown TTS provider '{selected}', defaulting to CartesiaTTSAdapter.")
            return CartesiaTTSAdapter()
