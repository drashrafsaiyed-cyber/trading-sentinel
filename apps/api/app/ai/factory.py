"""AI provider factory — switch providers via the AI_PROVIDER env var."""
import logging
from functools import lru_cache
from app.ai.base import AIProvider, NullProvider
from app.config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_ai_provider() -> AIProvider:
    """Return the configured AI provider. Falls back to NullProvider if unset."""
    provider = settings.ai_provider.lower()

    if provider == "nvidia":
        if not settings.nvidia_api_key:
            logger.info("NVIDIA_API_KEY not set — using rule-based sentiment only")
            return NullProvider()
        from app.ai.nvidia import NvidiaProvider
        return NvidiaProvider()

    logger.warning("Unknown AI_PROVIDER '%s' — using NullProvider", provider)
    return NullProvider()
