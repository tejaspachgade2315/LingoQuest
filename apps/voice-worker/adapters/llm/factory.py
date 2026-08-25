import logging
from typing import Optional
from core.interfaces import BaseLLMAdapter
from core.config import settings
from adapters.llm.vertex_adapter import VertexAIAdapter
from adapters.llm.groq_adapter import GroqAdapter

logger = logging.getLogger("voice-worker.llm.factory")


class LLMFactory:
    """Factory to instantiate the appropriate LLM adapter based on environment configuration."""

    @staticmethod
    def get_adapter(provider: Optional[str] = None) -> BaseLLMAdapter:
        selected = (provider or settings.LLM_PROVIDER).lower()

        if selected == "vertex":
            logger.info("Instantiating VertexAIAdapter...")
            return VertexAIAdapter()
        elif selected == "groq":
            logger.info("Instantiating GroqAdapter...")
            return GroqAdapter()
        else:
            logger.warning(f"Unknown LLM provider '{selected}', defaulting to VertexAIAdapter.")
            return VertexAIAdapter()
