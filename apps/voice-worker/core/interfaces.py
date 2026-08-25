from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, AsyncGenerator


class BaseLLMAdapter(ABC):
    """Abstract Base Class for Large Language Model adapters."""

    @abstractmethod
    async def generate_response(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        """Generate a text response to a prompt."""
        pass

    @abstractmethod
    async def stream_response(
        self, prompt: str, system_instruction: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Stream generated text chunks."""
        pass


class BaseSTTAdapter(ABC):
    """Abstract Base Class for Speech-to-Text adapters."""

    @abstractmethod
    def get_livekit_stt(self) -> Any:
        """Returns a LiveKit-compatible STT provider instance."""
        pass

    @abstractmethod
    async def transcribe_audio_chunk(self, audio_data: bytes) -> str:
        """Transcribe an isolated raw audio buffer."""
        pass


class BaseTTSAdapter(ABC):
    """Abstract Base Class for Text-to-Speech adapters."""

    @abstractmethod
    def get_livekit_tts(self) -> Any:
        """Returns a LiveKit-compatible TTS provider instance."""
        pass

    @abstractmethod
    async def synthesize(self, text: str) -> bytes:
        """Synthesize text into raw PCM/MP3 audio bytes."""
        pass


class BaseTelephonyAdapter(ABC):
    """Abstract Base Class for Telephony (SIP / PSTN / GSM) adapters."""

    @abstractmethod
    async def dial_outbound(self, to_number: str, room_name: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Dial a phone number and bridge it into a LiveKit room."""
        pass

    @abstractmethod
    async def terminate_call(self, call_sid: str) -> bool:
        """Hang up or disconnect an active phone call."""
        pass
