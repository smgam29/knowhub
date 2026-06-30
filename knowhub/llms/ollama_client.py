"""Ollama LLM adapter for local BYO models."""

from __future__ import annotations

import requests

from knowhub.llms.base import LLMClient, LLMResponse


class OllamaClient(LLMClient):
    def __init__(
        self,
        model: str,
        url: str = "http://localhost:11434/api/generate",
        temperature: float = 0.1,
        prompt_hint: str = "Return compact valid JSON only. Do not use markdown fences.",
        timeout: int = 600,
        prompt_profile: str = "local_reasoning",
    ):
        self.model = model
        self.url = url
        self.temperature = temperature
        self.prompt_hint = prompt_hint
        self.timeout = timeout
        self._prompt_profile = prompt_profile

    @property
    def name(self) -> str:
        return self.model

    @property
    def prompt_profile(self) -> str:
        return self._prompt_profile

    def prepare_prompt(self, prompt: str) -> str:
        return f"{self.prompt_hint}\n\n{prompt}"

    def generate(self, prompt: str) -> LLMResponse:
        response = requests.post(
            self.url,
            json={
                "model": self.model,
                "temperature": self.temperature,
                "prompt": prompt,
                "stream": False,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        return LLMResponse(
            model=self.model,
            text=response.json().get("response", ""),
        )
