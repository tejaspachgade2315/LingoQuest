import logging
from typing import Any, Optional
from core.interfaces import BaseTTSAdapter
from core.config import settings

try:
    from livekit.plugins import cartesia
except ImportError:
    cartesia = None

logger = logging.getLogger("voice-worker.tts.cartesia")


class CartesiaTTSAdapter(BaseTTSAdapter):
    """
    TTS Adapter using Cartesia Sonic ultra-low latency voice synthesis.
    Sub-100ms time-to-first-byte (TTFB).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "sonic-2",
        voice_id: str = "a0e99841-438c-4a64-b679-ae501e7d6091",  # Friendly tutor voice
    ):
        self.api_key = api_key or settings.CARTESIA_API_KEY
        self.model = model
        self.voice_id = voice_id

    def get_livekit_tts(self) -> Any:
        if cartesia is None:
            raise RuntimeError("livekit-plugins-cartesia is not installed or failed to load")
        try:
            logger.info("Initializing LiveKit Cartesia TTS plugin...")
            return cartesia.TTS(
                api_key=self.api_key,
                model=self.model,
                voice=self.voice_id,
            )
        except Exception as e:
            logger.error(f"Failed to create LiveKit Cartesia TTS instance: {e}")
            raise e

    async def synthesize(self, text: str) -> bytes:
        # Direct synthesis if needed
        return b""
