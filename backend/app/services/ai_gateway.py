"""Gateway module for communicating with LLM providers (Gemini, OpenAI, Anthropic)."""

from typing import Optional, Dict, Any
from app.core.config import settings
from app.core.logging import logger

try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False


class AIGateway:
    """Provides a unified interface for routing prompts to Gemini or configured fallback LLMs."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.client = None
        if self.api_key and HAS_GENAI:
            try:
                self.client = genai.Client(api_key=self.api_key)
                logger.info("AIGateway initialized with Google GenAI client.")
            except Exception as e:
                logger.warning(f"Could not initialize GenAI client: {e}")

    def generate_text(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        """Generate text using primary Gemini model or heuristic fallback."""
        if not self.client:
            logger.info("No Gemini API key configured. Operating in development fallback mode.")
            return (
                f"[AIGateway Dev Mode]: Received prompt ({len(prompt)} chars). "
                f"Please configure GEMINI_API_KEY in .env for live Gemini 1.5 responses."
            )
        try:
            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.3
            ) if system_instruction else None
            response = self.client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt,
                config=config
            )
            return response.text or ""
        except Exception as exc:
            logger.error(f"GenAI text generation error: {exc}")
            raise


ai_gateway = AIGateway()

