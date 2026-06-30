"""Core knowledge artifact schema for KnowHub.

This module is intentionally model-agnostic. Extractors can be Claude, Phi4,
OpenAI, Ollama, or a future fine-tuned model; they only need to produce data
that can be normalized into this schema.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Any


def make_id(value: str, fallback: str = "unknown") -> str:
    """Create a stable snake_case-ish identifier from human text."""
    text = str(value or fallback).strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text or fallback


@dataclass
class SourceDocument:
    path: str
    id: str | None = None
    title: str | None = None

    def __post_init__(self) -> None:
        if self.id is None:
            self.id = make_id(os.path.relpath(self.path))
        if self.title is None:
            self.title = os.path.basename(self.path)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "path": self.path,
            "title": self.title,
        }


@dataclass
class Entity:
    id: str
    name: str
    type: str = "Entity"
    properties: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> "Entity":
        name = str(raw.get("name") or raw.get("id") or "unknown").strip()
        entity_id = raw.get("id") or make_id(name)
        properties = dict(raw.get("properties") or {})

        if raw.get("decision_type"):
            properties["decision_type"] = raw["decision_type"]

        return cls(
            id=make_id(entity_id),
            name=name,
            type=str(raw.get("type") or "Entity").strip() or "Entity",
            properties=properties,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "properties": self.properties,
        }


@dataclass
class Relationship:
    source_id: str
    relationship_type: str
    target_id: str
    properties: dict[str, Any] = field(default_factory=dict)
    confirmed_by: list[str] = field(default_factory=list)

    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> "Relationship":
        source = raw.get("source_id") or raw.get("source") or ""
        target = raw.get("target_id") or raw.get("target") or ""
        rel_type = raw.get("relationship_type") or raw.get("type") or "RELATES_TO"

        return cls(
            source_id=make_id(source),
            relationship_type=str(rel_type).strip().upper() or "RELATES_TO",
            target_id=make_id(target),
            properties=dict(raw.get("properties") or {}),
            confirmed_by=list(raw.get("confirmed_by") or []),
        )

    def fingerprint(self) -> tuple[str, str, str]:
        return (self.source_id, self.relationship_type, self.target_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "relationship_type": self.relationship_type,
            "target_id": self.target_id,
            "properties": self.properties,
            "confirmed_by": self.confirmed_by,
        }


@dataclass
class KnowledgeGap:
    type: str
    description: str
    context: str = ""

    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> "KnowledgeGap":
        return cls(
            type=str(raw.get("type") or "Knowledge_Gap"),
            description=str(raw.get("description") or ""),
            context=str(raw.get("context") or ""),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "description": self.description,
            "context": self.context,
        }


@dataclass
class KnowledgeArtifact:
    source: SourceDocument
    entities: list[Entity] = field(default_factory=list)
    relationships: list[Relationship] = field(default_factory=list)
    knowledge_gaps: list[KnowledgeGap] = field(default_factory=list)
    knowledge_type: str = ""
    reasoning: str = ""

    @classmethod
    def from_extraction(
        cls,
        source_path: str,
        extraction_result: dict[str, Any],
    ) -> "KnowledgeArtifact":
        return cls(
            source=SourceDocument(path=source_path),
            entities=[
                Entity.from_raw(entity)
                for entity in extraction_result.get("entities", [])
            ],
            relationships=[
                Relationship.from_raw(relationship)
                for relationship in extraction_result.get("relationships", [])
            ],
            knowledge_gaps=[
                KnowledgeGap.from_raw(gap)
                for gap in extraction_result.get("knowledge_gaps", [])
            ],
            knowledge_type=str(extraction_result.get("knowledge_type") or ""),
            reasoning=str(extraction_result.get("reasoning") or ""),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source.to_dict(),
            "knowledge_type": self.knowledge_type,
            "reasoning": self.reasoning,
            "entities": [entity.to_dict() for entity in self.entities],
            "relationships": [
                relationship.to_dict()
                for relationship in self.relationships
            ],
            "knowledge_gaps": [gap.to_dict() for gap in self.knowledge_gaps],
        }
