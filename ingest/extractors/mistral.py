# extractors/mistral.py
# Mistral implementation of BaseExtractor via Ollama

import json
from unittest import result
import requests
from extractors.base import BaseExtractor

class MistralExtractor(BaseExtractor):

    def __init__(self):
        self.model = "mistral"
        self.url = "http://localhost:11434/api/generate"

    def extract(self, file_path: str) -> dict:
        # Read and truncate file content
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()[:3000]

        # Call Ollama REST API
        response = requests.post(self.url, json={
            "model": self.model,
            "temperature": 0.1,
            "prompt": f"""Extract entities and relationships from this ServiceNow documentation as JSON only, no explanation, no code fences.
Format: {{"entities": [{{"name": "", "type": ""}}], "relationships": [{{"source": "", "type": "", "target": ""}}]}}
Entity types: Product, Feature, Concept, Integration, Persona
Relationship types: USES, REQUIRES, INTEGRATES_WITH, ENABLES, RELATES_TO

Text: {content}""",
            "stream": False
        })

        # Parse response
        try:
            raw = response.json()["response"].strip()
            start = raw.find("{")
            end = raw.rfind("}") + 1
            raw = raw[start:end]


        # Fix invalid escape sequences
            raw = raw.replace("\\", "\\\\")

            result = json.loads(raw)

        # Normalise entity names and relationship source/target
            for entity in result.get("entities", []):
                entity["name"] = entity["name"].lower().strip()

            for rel in result.get("relationships", []):
                rel["source"] = rel["source"].lower().strip()
                rel["target"] = rel["target"].lower().strip()
                rel["type"] = rel["type"].upper().strip()

            return result
        
        except Exception as e:
            print(f"    Mistral parse failed: {e} — skipping")
            return {"entities": [], "relationships": []}