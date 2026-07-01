"""Test/demonstration LLM client that returns a fixed response."""

from __future__ import annotations

from knowhub.llms.base import LLMClient, LLMResponse


class StaticLLMClient(LLMClient):
    def __init__(self, name: str, response_text: str):
        self._name = name
        self._response_text = response_text

    @property
    def name(self) -> str:
        return self._name

    def generate(self, prompt: str) -> LLMResponse:
        return LLMResponse(model=self.name, text=self._response_text)
