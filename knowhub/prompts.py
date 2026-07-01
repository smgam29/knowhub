"""Prompt builders for KnowHub extraction.

The ontology contract is shared by every model. Profiles change the teaching
style around that contract so frontier models can stay concise while local
models get more scaffolding.
"""

from __future__ import annotations


ONTOLOGY_CONTRACT = """KnowHub ontology contract:

Task:
Extract implementation knowledge from the text into valid JSON only.

Knowledge types:
Comparative, Contextual, Diagnostic, Procedural, Conceptual, Experiential, Referential.

Entity types:
Product, Feature, Decision, Persona, Prerequisite, Outcome, Concept, Integration.

Relationship types:
REQUIRES, ENABLES, CONFLICTS_WITH, TRADEOFF, RECOMMENDED_WHEN,
IMPACTS, PRODUCES, SUPERSEDES, PRECEDES, PERFORMED_BY.

Output shape:
{
  "reasoning": "what an implementer would do or decide after reading the text",
  "knowledge_type": "Comparative|Contextual|Diagnostic|Procedural|Conceptual|Experiential|Referential",
  "entities": [
    {
      "id": "stable_snake_case_id",
      "name": "Human name",
      "type": "Decision",
      "properties": {}
    }
  ],
  "relationships": [
    {
      "source_id": "source_entity_id",
      "relationship_type": "TRADEOFF",
      "target_id": "target_entity_id",
      "properties": {}
    }
  ],
  "knowledge_gaps": [
    {
      "type": "Missing_Property",
      "description": "What is missing",
      "context": "Where it appeared"
    }
  ]
}

Hard rules:
- Output valid JSON only.
- Use only the listed knowledge, entity, and relationship types.
- TRADEOFF requires both gives and costs.
- RECOMMENDED_WHEN requires context.
- CONFLICTS_WITH requires severity and notes.
- Prefer knowledge_gaps over incomplete relationships.
- Use stable entity IDs. Do not add incidental context words like pilot, long_term, or warning unless needed to disambiguate two different entities.
"""


FRONTIER_PROFILE = """Profile: frontier
You are a strong instruction-following model. Apply the ontology contract directly.
Be concise. Do not over-extract. Prefer high-confidence relationships.
"""


LOCAL_REASONING_PROFILE = """Profile: local_reasoning
Follow the ontology contract carefully.

Extra guidance:
- First decide what an implementer would choose, avoid, configure, or verify.
- Comparative words such as faster, but, tradeoff, versus, or alternative usually mean Comparative, not Procedural.
- A Decision is an implementation choice. A Feature is a capability. Do not label a choice as a Feature.
- For TRADEOFF, the source is the Decision and the target is usually an Outcome, not the alternative option.
- Warning/caution/do not language is Diagnostic. Represent it as CONFLICTS_WITH or negative IMPACTS when properties are available.
- If a relationship is missing required properties, place it in knowledge_gaps instead of emitting a partial edge.
"""


LOCAL_SCHEMA_PROFILE = """Profile: local_schema
Follow the ontology contract exactly and prioritize schema validity.

Extra guidance:
- Return one JSON object and nothing else.
- Use exact enum values from the contract.
- Do not invent relationship types.
- Keep IDs short and stable: prompt_customization, input_data_optimization, maintenance_overhead.
- TRADEOFF must include properties.gives and properties.costs.
- RECOMMENDED_WHEN must include properties.context.
- CONFLICTS_WITH must include properties.severity and properties.notes.
"""


PROMPT_PROFILES = {
    "frontier": FRONTIER_PROFILE,
    "local_reasoning": LOCAL_REASONING_PROFILE,
    "local_schema": LOCAL_SCHEMA_PROFILE,
}


def build_extraction_prompt(text: str, profile: str = "frontier") -> str:
    profile_prompt = PROMPT_PROFILES.get(profile)
    if profile_prompt is None:
        raise ValueError(f"Unknown prompt profile: {profile}")

    return (
        f"{profile_prompt}\n\n"
        f"{ONTOLOGY_CONTRACT}\n\n"
        f"Text:\n{text}"
    )
