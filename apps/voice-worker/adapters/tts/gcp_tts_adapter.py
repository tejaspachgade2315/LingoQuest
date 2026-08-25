import logging
from typing import Any, Optional
from core.interfaces import BaseTTSAdapter
from core.config import settings

logger = logging.getLogger("voice-worker.tts.gcp")


class GCPTTSAdapter(BaseTTSAdapter):
    """
    TTS Adapter using Google Cloud Text-to-Speech (Journey or Neural2 voices).
    Native GCP integration using ADC.
    """

    def __init__(self, voice_name: str = "en-US-Journey-F", language_code: str = "en-US"):
        self.voice_name = voice_name
        self.language_code = language_code
        self._client = None
        self._init_client()

    def _init_client(self):
        try:
            from google.cloud import texttospeech
            self._client = texttospeech.TextToSpeechAsyncClient()
            logger.info(f"GCPTTSAdapter initialized with voice {self.voice_name}")
        except Exception as e:
            logger.warning(f"Could not initialize Google Cloud TTS client: {e}")

    def get_livekit_tts(self) -> Any:
        try:
            from livekit.plugins import google
            logger.info("Initializing LiveKit Google Cloud TTS plugin...")
            return google.TTS(
                voice_name=self.voice_name,
                language=self.language_code,
            )
        except Exception as e:
            logger.warning(f"Could not initialize LiveKit Google plugin: {e}")
            return None

    async def synthesize(self, text: str) -> bytes:
        if not self._client:
            return b""
        try:
            from google.cloud import texttospeech
            s_input = texttospeech.SynthesisInput(text=text)
            voice = texttospeech.VoiceSelectionParams(
                language_code=self.language_code,
                name=self.voice_name,
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )
            response = await self._client.synthesize_speech(
                input=s_input, voice=voice, audio_config=audio_config
            )
            return response.audio_content
        except Exception as e:
            logger.error(f"GCP TTS synthesize failed: {e}")
            return b""
