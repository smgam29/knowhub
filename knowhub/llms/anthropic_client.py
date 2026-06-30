"""Anthropic LLM adapter for the KnowHub compiler path."""

from __future__ import annotations

import os

import anthropic
from dotenv import load_dotenv

from knowhub.llms.base import LLMClient, LLMResponse

load_dotenv()


class AnthropicClient(LLMClient):
    def __init__(
        self,
        model: str = "claude-haiku-4-5-20251001",
        api_key: str | None = None,
        max_tokens: int = 2000,
        prompt_profile: str = "frontier",
    ):
        self.model = model
        self.max_tokens = max_tokens
        self._prompt_profile = prompt_profile
        self.client = anthropic.Anthropic(
            api_key=api_key or os.getenv("ANTHROPIC_API_KEY")
        )

    @property
    def name(self) -> str:
        return self.model

    @property
    def prompt_profile(self) -> str:
        return self._prompt_profile

    def generate(self, prompt: str) -> LLMResponse:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return LLMResponse(model=self.model, text=response.content[0].text)
