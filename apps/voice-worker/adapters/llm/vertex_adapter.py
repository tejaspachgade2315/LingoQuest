import logging
from typing import Optional, AsyncGenerator
from core.interfaces import BaseLLMAdapter
from core.config import settings

logger = logging.getLogger("voice-worker.llm.vertex")


class VertexAIAdapter(BaseLLMAdapter):
    """
    LLM adapter using Google Cloud Vertex AI (Gemini 2.5 Flash / Gemini Pro).
    Uses GCP Application Default Credentials (ADC).
    """

    def __init__(self, project_id: Optional[str] = None, model_name: Optional[str] = None, location: Optional[str] = None):
        self.project_id = project_id or settings.GCP_PROJECT_ID
        self.model_name = model_name or settings.GEMINI_MODEL
        self.location = location or settings.GOOGLE_LOCATION
        self._model = None
        self._init_client()

    def _init_client(self):
        try:
            import vertexai
            from vertexai.generative_models import GenerativeModel
            if self.project_id:
                vertexai.init(project=self.project_id, location=self.location)
            self._model = GenerativeModel(self.model_name)
            logger.info(f"VertexAIAdapter initialized with model {self.model_name} in location {self.location}")
        except Exception as e:
            logger.warning(f"Failed to initialize Vertex AI client: {e}. Fallback mode active.")

    async def generate_response(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        if not self._model:
            return "Good job! Keep reading clearly and steadily."

        try:
            full_prompt = f"{system_instruction}\n\nUser: {prompt}" if system_instruction else prompt
            response = await self._model.generate_content_async(full_prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Vertex AI generate_content failed: {e}")
            return "You're doing fantastic! Keep on going."

    async def stream_response(
        self, prompt: str, system_instruction: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        if not self._model:
            yield "Great progress! Let's read the next sentence."
            return

        try:
            full_prompt = f"{system_instruction}\n\nUser: {prompt}" if system_instruction else prompt
            response = await self._model.generate_content_async(full_prompt, stream=True)
            async for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            logger.error(f"Vertex AI streaming failed: {e}")
            yield "Keep going, you are doing awesome!"
