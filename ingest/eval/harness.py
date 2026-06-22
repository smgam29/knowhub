# eval/harness.py
import json
import os
import time
import requests
from datetime import datetime

MODELS = [
    {"name": "qwen3:8b", "type": "ollama"},
    {"name": "gpt-oss:20b", "type": "ollama"},
    {"name": "phi4:14b", "type": "ollama"},
]

EXCERPTS_DIR = os.path.join(os.path.dirname(__file__), "excerpts")
EXCERPTS = [
    {"id": "excerpt_1", "file": "excerpt_1_comparative.txt", "knowledge_type": "Comparative"},
    {"id": "excerpt_2", "file": "excerpt_2_diagnostic.txt", "knowledge_type": "Diagnostic"},
    {"id": "excerpt_3", "file": "excerpt_3_contextual.txt", "knowledge_type": "Contextual"},
]

RUNS = 3
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(OUTPUT_DIR, exist_ok=True)

PROMPT = (
    "You are a knowledge graph extraction specialist for ServiceNow implementation content.\n\n"
    "Classify the passage into one of: Conceptual, Procedural, Contextual, Experiential, Referential, Diagnostic, Comparative.\n\n"
    "Extract entities using only these types: Product, Feature, Decision, Persona, Prerequisite, Outcome, Concept, Integration.\n"
    "Every Decision entity must include a decision_type field: Configuration, Architecture, Process, Governance, or Role.\n"
    "Entity names must be lowercase and specific. Never use generic terms like system, data, or ai.\n\n"
    "Extract relationships using only: REQUIRES, ENABLES, CONFLICTS_WITH, TRADEOFF, RECOMMENDED_WHEN, IMPACTS, SUPERSEDES, PRECEDES, PERFORMED_BY, PRODUCES.\n\n"
    "TRADEOFF: only extract if you can populate both gives AND costs. If not, add to knowledge_gaps. Properties: gives, costs, severity (LOW/MEDIUM/HIGH), context.\n"
    "RECOMMENDED_WHEN: only extract if you can populate context. Properties: context, confidence (LOW/MEDIUM/HIGH).\n"
    "CONFLICTS_WITH properties: severity (LOW/MEDIUM/HIGH), notes.\n"
    "IMPACTS properties: direction (POSITIVE/NEGATIVE/NEUTRAL), severity (LOW/MEDIUM/HIGH).\n"
    "PRODUCES properties: likelihood (LOW/MEDIUM/HIGH), notes.\n\n"
    "Valid source to target combinations:\n"
    "REQUIRES: Product Feature Decision Prerequisite -> Product Feature Prerequisite Concept\n"
    "ENABLES: Product Feature Decision Prerequisite -> Product Feature Outcome Concept\n"
    "CONFLICTS_WITH: Decision Feature Concept -> Decision Feature Concept Outcome\n"
    "TRADEOFF: Decision -> Outcome\n"
    "RECOMMENDED_WHEN: Decision Feature -> Product Feature Concept\n"
    "IMPACTS: Decision Feature Product -> Outcome Feature Product Persona\n"
    "SUPERSEDES: Product Feature Decision -> Product Feature Decision\n"
    "PRECEDES: Decision Feature Prerequisite -> Decision Feature Prerequisite\n"
    "PERFORMED_BY: Feature Decision Product -> Persona\n"
    "PRODUCES: Decision Feature -> Outcome\n\n"
    "Do not extract relationships that violate these source to target rules.\n\n"
    "Return a single JSON object only. No explanation, no code fences, no preamble.\n"
    "Format: "
    '{"knowledge_type":"","entities":[{"name":"","type":""}],"relationships":[{"source":"","type":"","target":""}],"knowledge_gaps":[{"source":"","relationship_type":"","target":"","reason":""}]}'
    "\n\nText:\n"
)


def call_ollama(model_name, content):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model_name,
            "prompt": PROMPT + content,
            "temperature": 0.1,
            "stream": False
        }
    )
    raw = response.json()["response"].strip()
    start = raw.find("{")
    end = raw.rfind("}") + 1
    raw = raw[start:end]
    return json.loads(raw)


def run_eval():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary = []

    for excerpt in EXCERPTS:
        excerpt_path = os.path.join(EXCERPTS_DIR, excerpt["file"])
        with open(excerpt_path, "r") as f:
            content = f.read()

        print(f"\n{'='*60}")
        print(f"Excerpt: {excerpt['id']} ({excerpt['knowledge_type']})")
        print(f"{'='*60}")

        for model in MODELS:
            print(f"\n  Model: {model['name']}")
            model_results = []

            for run in range(RUNS):
                print(f"    Run {run + 1}/{RUNS}...")
                try:
                    result = call_ollama(model["name"], content)
                    model_results.append({"run": run + 1, "success": True, "output": result})
                    print(f"      knowledge_type: {result.get('knowledge_type', 'missing')}")
                    print(f"      entities: {len(result.get('entities', []))}")
                    print(f"      relationships: {len(result.get('relationships', []))}")
                    print(f"      knowledge_gaps: {len(result.get('knowledge_gaps', []))}")
                except Exception as e:
                    print(f"      Failed: {e}")
                    model_results.append({"run": run + 1, "success": False, "error": str(e)})

                if run < RUNS - 1:
                    time.sleep(0.5)

            output_file = os.path.join(
                OUTPUT_DIR,
                f"{timestamp}_{excerpt['id']}_{model['name'].replace(':', '_')}.json"
            )
            with open(output_file, "w") as f:
                json.dump({
                    "model": model["name"],
                    "excerpt": excerpt["id"],
                    "expected_knowledge_type": excerpt["knowledge_type"],
                    "runs": model_results
                }, f, indent=2)
            print(f"    Saved to {output_file}")
            summary.append({
                "model": model["name"],
                "excerpt": excerpt["id"],
                "output_file": output_file
            })

    summary_file = os.path.join(OUTPUT_DIR, f"{timestamp}_summary.json")
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nEval complete. Summary: {summary_file}")


if __name__ == "__main__":
    run_eval()
