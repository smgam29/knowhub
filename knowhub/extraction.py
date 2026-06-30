"""LLM-backed extraction into the KnowHub internal schema."""

from __future__ import annotations

import json
from typing import Any

from knowhub.llms.base import LLMClient
from knowhub.prompts import build_extraction_prompt
from knowhub.schema import KnowledgeArtifact


def parse_json_response(text: str) -> dict[str, Any]:
    """Parse model output, tolerating common code-fence or preamble wrappers."""
    raw = text.strip()
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    if not raw.startswith("{"):
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start == -1 or end == 0:
            raise ValueError("No JSON object found in LLM response")
        raw = raw[start:end]

    return json.loads(raw)


class KnowledgeExtractor:
    """Run one LLM client and normalize its output into a KnowledgeArtifact."""

    def __init__(self, client: LLMClient):
        self.client = client

    def extract_text(self, source_path: str, text: str) -> KnowledgeArtifact:
        prompt = self.client.prepare_prompt(
            build_extraction_prompt(text, profile=self.client.prompt_profile)
        )
        response = self.client.generate(prompt)
        raw = parse_json_response(response.text)
        artifact = KnowledgeArtifact.from_extraction(source_path, raw)

        for relationship in artifact.relationships:
            if self.client.name not in relationship.confirmed_by:
                relationship.confirmed_by.append(self.client.name)

        return artifact
