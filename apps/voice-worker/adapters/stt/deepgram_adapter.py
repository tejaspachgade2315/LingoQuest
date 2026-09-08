import logging
from typing import Any, Optional
from core.interfaces import BaseSTTAdapter
from core.config import settings

try:
    from livekit.plugins import deepgram
except ImportError:
    deepgram = None

logger = logging.getLogger("voice-worker.stt.deepgram")


class DeepgramSTTAdapter(BaseSTTAdapter):
    """
    STT Adapter using Deepgram Nova-2 streaming speech-to-text.
    Optimized for forced-alignment and word-level timestamp emission.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "nova-2"):
        self.api_key = api_key or settings.DEEPGRAM_API_KEY
        self.model = model

    def get_livekit_stt(self) -> Any:
        """Returns a LiveKit Agents deepgram STT plugin instance."""
        if deepgram is None:
            raise RuntimeError("livekit-plugins-deepgram is not installed or failed to load")
        try:
            logger.info(f"Initializing LiveKit Deepgram STT plugin with model {self.model}")
            
            story_keywords = [
                ("ridge", 5.0),
                ("falcon", 5.0),
                ("Pip", 5.0),
                ("rocky", 3.0),
                ("spread", 3.0),
                ("wings", 3.0),
                ("twilight", 4.0),
                ("canopy", 5.0),
                ("emerald", 4.0),
                ("obsidian", 5.0),
                ("turbulent", 4.0),
            ]

            return deepgram.STT(
                api_key=self.api_key,
                model=self.model,
                language="en-US",
                smart_format=False,  # Unformatted makes phoneme alignment cleaner
                interim_results=True,
                keywords=story_keywords,
            )
        except Exception as e:
            logger.error(f"Failed to create LiveKit Deepgram STT instance: {e}")
            raise e

    async def transcribe_audio_chunk(self, audio_data: bytes) -> str:
        # Standalone chunk transcription if needed outside pipeline
        return ""
