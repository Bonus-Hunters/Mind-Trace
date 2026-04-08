from dataclasses import dataclass
from typing import Optional, Literal

LLMProvider = Literal["ollama", "openai", "gemini"]

@dataclass
class LLMConfig:
    provider: LLMProvider
    model: str
    api_key: Optional[str] = None
    temperature: float = 0
