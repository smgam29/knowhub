# extractors/phi4.py
# Phi4 14B implementation of BaseExtractor via Ollama

import json
import requests
from extractors.base import BaseExtractor
from preprocessor import preprocess

class Phi4Extractor(BaseExtractor):

    def __init__(self):
        self.model = "phi4:14b"
        self.url = "http://localhost:11434/api/generate"

    def extract(self, file_path: str) -> dict:
        # Extract clean text via preprocessor
        content = preprocess(file_path)[:3000]

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

        try:
            raw = response.json()["response"].strip()
            start = raw.find("{")
            end = raw.rfind("}") + 1
            raw = raw[start:end]
            result = json.loads(raw)

            for entity in result.get("entities", []):
                entity["name"] = str(entity.get("name", "")).lower().strip()

            for rel in result.get("relationships", []):
                rel["source"] = str(rel.get("source", "")).lower().strip()
                rel["target"] = str(rel.get("target", "")).lower().strip()
                rel["type"] = str(rel.get("type", "")).upper().strip()

            return result

        except Exception as e:
            print(f"    Phi4 parse failed: {e} -- skipping")
            return {"entities": [], "relationships": []}
