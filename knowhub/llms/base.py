"""Provider-neutral LLM interface for KnowHub."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResponse:
    model: str
    text: str


class LLMClient(ABC):
    """Minimal contract every BYO LLM adapter must satisfy."""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    def prepare_prompt(self, prompt: str) -> str:
        """Allow model-specific prompt nudges without changing core prompts."""
        return prompt

    @property
    def prompt_profile(self) -> str:
        return "frontier"

    @abstractmethod
    def generate(self, prompt: str) -> LLMResponse:
        pass
