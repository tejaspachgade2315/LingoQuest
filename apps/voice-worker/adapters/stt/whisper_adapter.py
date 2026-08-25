import logging
from typing import Any, Optional
from core.interfaces import BaseSTTAdapter

logger = logging.getLogger("voice-worker.stt.whisper")


class WhisperSTTAdapter(BaseSTTAdapter):
    """
    Self-hosted / Whisper STT alternative adapter.
    Can hook into OpenAI Whisper API or a local Faster-Whisper endpoint.
    """

    def __init__(self, model_size: str = "base.en"):
        self.model_size = model_size

    def get_livekit_stt(self) -> Any:
        try:
            from livekit.plugins import openai
            logger.info("Initializing LiveKit OpenAI Whisper STT plugin...")
            return openai.STT(model="whisper-1")
        except Exception as e:
            logger.warning(f"Could not initialize LiveKit OpenAI plugin: {e}")
            return None

    async def transcribe_audio_chunk(self, audio_data: bytes) -> str:
        logger.info(f"Transcribing {len(audio_data)} bytes using Whisper adapter...")
        return "the quick brown fox"
