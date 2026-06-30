"""Prompt builders for KnowHub extraction."""

from __future__ import annotations


IMPLEMENTATION_ONTOLOGY_PROMPT = """You are KnowHub, a knowledge extraction system.

Extract implementation knowledge from the text into JSON only.

Classify knowledge_type as one of:
Comparative, Contextual, Diagnostic, Procedural, Conceptual, Experiential, Referential.

Entity types:
Product, Feature, Decision, Persona, Prerequisite, Outcome, Concept, Integration.

Relationship types:
REQUIRES, ENABLES, CONFLICTS_WITH, TRADEOFF, RECOMMENDED_WHEN,
IMPACTS, PRODUCES, SUPERSEDES, PRECEDES, PERFORMED_BY.

Return this exact JSON shape:
{
  "reasoning": "what an implementer would do or decide after reading the text",
  "knowledge_type": "Comparative|Contextual|Diagnostic|Procedural|Conceptual|Experiential|Referential",
  "entities": [
    {
      "id": "snake_case_id",
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

Rules:
- Output valid JSON only.
- Extract TRADEOFF only when both gives and costs are present.
- Extract RECOMMENDED_WHEN only when the context is present.
- CONFLICTS_WITH must include severity and notes.
- Use knowledge_gaps when a relationship is implied but underspecified.
"""


def build_extraction_prompt(text: str) -> str:
    return f"{IMPLEMENTATION_ONTOLOGY_PROMPT}\n\nText:\n{text}"
