"""AI provider abstraction. No feature code imports an SDK directly."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class AIResult:
    content: str
    model: str = ""
    provider: str = ""
    raw: dict = field(default_factory=dict)


class AIProvider(ABC):
    """Base class every provider implements."""

    name: str = "base"

    @abstractmethod
    async def complete(self, prompt: str, *, max_tokens: int = 512, temperature: float = 0.3) -> AIResult:
        """Return a text completion for the prompt."""
        raise NotImplementedError


class NullProvider(AIProvider):
    """Fallback that returns nothing — sentiment falls back to rule-based scoring."""

    name = "null"

    async def complete(self, prompt: str, *, max_tokens: int = 512, temperature: float = 0.3) -> AIResult:
        return AIResult(content="", provider="null")
