"""NVIDIA NIM provider (OpenAI-compatible endpoint). Free, no quota."""
import logging
from openai import AsyncOpenAI
from app.ai.base import AIProvider, AIResult
from app.config import settings

logger = logging.getLogger(__name__)

NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"


class NvidiaProvider(AIProvider):
    name = "nvidia"

    def __init__(self):
        self.model = settings.nvidia_model
        self._client = AsyncOpenAI(
            base_url=NVIDIA_BASE_URL,
            api_key=settings.nvidia_api_key or "missing",
            max_retries=0,
            timeout=30.0,
        )

    async def complete(self, prompt: str, *, max_tokens: int = 512, temperature: float = 0.3) -> AIResult:
        try:
            resp = await self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            content = resp.choices[0].message.content or ""
            return AIResult(content=content.strip(), model=self.model, provider=self.name)
        except Exception as e:  # noqa: BLE001 — degrade to rule-based
            logger.warning("NVIDIA completion failed: %s", e)
            return AIResult(content="", provider=self.name)
