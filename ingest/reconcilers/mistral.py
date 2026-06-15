# reconcilers/mistral.py
# Mistral implementation of BaseReconciler via Ollama

import json
import requests
from reconcilers.base import BaseReconciler

class MistralReconciler(BaseReconciler):

    def __init__(self):
        self.model = "mistral"
        self.url = "http://localhost:11434/api/generate"

    def reconcile(self, relationships_by_model: dict) -> list:
        # Format relationships for the prompt
        formatted = json.dumps(relationships_by_model, indent=2)

        # Ask Mistral to identify semantically equivalent relationships
        response = requests.post(self.url, json={
            "model": self.model,
            "prompt": f"""You are a knowledge graph reconciler. You will receive relationships extracted from the same document by multiple models.

Your job:
1. Identify relationships that are semantically equivalent across models (e.g. "llm" and "large language model" are the same)
2. Only return relationships that appear in AT LEAST TWO different models
3. Where relationships are equivalent, use the most descriptive version of the entity name
4. Return JSON only, no explanation, no code fences

Input:
{formatted}

Output format:
{{"relationships": [{{"source": "", "type": "", "target": ""}}]}}""",
            "stream": False
        })

# reconcilers/mistral.py
# Mistral implementation of BaseReconciler via Ollama

import json
import requests
from .base import BaseReconciler

class MistralReconciler(BaseReconciler):

    def __init__(self):
        self.model = "mistral"
        self.url = "http://localhost:11434/api/generate"

    def reconcile(self, relationships_by_model: dict) -> list:
        # Format relationships for the prompt
        formatted = json.dumps(relationships_by_model, indent=2)

        # Ask Mistral to identify semantically equivalent relationships
        response = requests.post(self.url, json={
            "model": self.model,
            "prompt": f"""You are a knowledge graph reconciler. You will receive relationships extracted from the same document by multiple models.

Your job:
1. Identify relationships that are semantically equivalent across models (e.g. "llm" and "large language model" are the same)
2. Only return relationships that appear in AT LEAST TWO different models
3. Where relationships are equivalent, use the most descriptive version of the entity name
4. Return JSON only, no explanation, no code fences

Input:
{formatted}

Output format:
{{"relationships": [{{"source": "", "type": "", "target": ""}}]}}""",
            "stream": False
        })

        # Parse response
        raw = response.json()["response"].strip()
        raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

        result = json.loads(raw)
        return result.get("relationships", [])