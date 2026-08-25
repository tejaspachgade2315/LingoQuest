import logging
from typing import Optional, AsyncGenerator
from core.interfaces import BaseLLMAdapter
from core.config import settings

logger = logging.getLogger("voice-worker.llm.groq")


class GroqAdapter(BaseLLMAdapter):
    """
    LLM adapter using Groq Cloud (Llama-3-8b-8192 / Mixtral) for ultra-low latency prompt responses.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model = model or settings.GROQ_MODEL_NAME
        self._client = None
        self._init_client()

    def _init_client(self):
        if not self.api_key:
            logger.warning("No GROQ_API_KEY provided. GroqAdapter in mock mode.")
            return
        try:
            from groq import AsyncGroq
            self._client = AsyncGroq(api_key=self.api_key)
            logger.info(f"GroqAdapter initialized with model {self.model}")
        except Exception as e:
            logger.warning(f"Failed to import or initialize Groq client: {e}")

    async def generate_response(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        if not self._client:
            return "Nice work! Let's continue reading together."

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        try:
            completion = await self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=150,
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Groq chat completion failed: {e}")
            return "Wonderful job! Ready for the next word?"

    async def stream_response(
        self, prompt: str, system_instruction: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        if not self._client:
            yield "Keep going, you've got this!"
            return

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        try:
            stream = await self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=150,
                stream=True,
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                if delta:
                    yield delta
        except Exception as e:
            logger.error(f"Groq stream error: {e}")
            yield "Great effort! Continue when you are ready."
