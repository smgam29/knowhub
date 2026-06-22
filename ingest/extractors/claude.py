# extractors/claude.py
# Claude Haiku implementation of BaseExtractor

import json
import os
from unittest import result
import anthropic
from dotenv import load_dotenv
from extractors.base import BaseExtractor

load_dotenv()

class ClaudeExtractor(BaseExtractor):

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = "claude-haiku-4-5-20251001"

    def extract(self, file_path: str) -> dict:
       # Extract clean text via preprocessor
        from preprocessor import preprocess
        content = preprocess(file_path)[:3000]

        # Call Claude Haiku
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": f"""Extract entities and relationships from this ServiceNow documentation as JSON only.
Format: {{"entities": [{{"name": "", "type": ""}}], "relationships": [{{"source": "", "type": "", "target": ""}}]}}
Entity types: Product, Feature, Concept, Integration, Persona
Relationship types: USES, REQUIRES, INTEGRATES_WITH, ENABLES, RELATES_TO

Text: {content}"""
            }]
        )

        # Strip code fences and parse JSON
        raw = response.content[0].text
        raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

        result = json.loads(raw)

        # Normalise entity names and relationship source/target
        for entity in result.get("entities", []):
            entity["name"] = entity["name"].lower().strip()

        for rel in result.get("relationships", []):
            rel["source"] = rel["source"].lower().strip()
            rel["target"] = rel["target"].lower().strip()
            rel["type"] = rel["type"].upper().strip()

        return result