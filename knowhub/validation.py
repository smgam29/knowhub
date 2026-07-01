"""Ontology contract validation for extracted KnowHub artifacts."""

from __future__ import annotations

from dataclasses import replace

from knowhub.schema import KnowledgeArtifact, KnowledgeGap, Relationship


VALID_KNOWLEDGE_TYPES = {
    "Comparative",
    "Contextual",
    "Diagnostic",
    "Procedural",
    "Conceptual",
    "Experiential",
    "Referential",
}

VALID_ENTITY_TYPES = {
    "Product",
    "Feature",
    "Decision",
    "Persona",
    "Prerequisite",
    "Outcome",
    "Concept",
    "Integration",
}

VALID_RELATIONSHIP_TYPES = {
    "REQUIRES",
    "ENABLES",
    "CONFLICTS_WITH",
    "TRADEOFF",
    "RECOMMENDED_WHEN",
    "IMPACTS",
    "PRODUCES",
    "SUPERSEDES",
    "PRECEDES",
    "PERFORMED_BY",
}

REQUIRED_RELATIONSHIP_PROPERTIES = {
    "TRADEOFF": {"gives", "costs"},
    "RECOMMENDED_WHEN": {"context"},
    "CONFLICTS_WITH": {"severity", "notes"},
}


def _relationship_context(relationship: Relationship) -> str:
    return (
        f"{relationship.source_id} "
        f"{relationship.relationship_type} "
        f"{relationship.target_id}"
    )


def _relationship_errors(
    relationship: Relationship,
    entity_ids: set[str],
) -> list[str]:
    errors = []

    if relationship.relationship_type not in VALID_RELATIONSHIP_TYPES:
        errors.append(f"unknown relationship type {relationship.relationship_type}")

    if relationship.source_id == "unknown":
        errors.append("missing source entity")
    elif relationship.source_id not in entity_ids:
        errors.append(f"source entity {relationship.source_id} was not defined")

    if relationship.target_id == "unknown":
        errors.append("missing target entity")
    elif relationship.target_id not in entity_ids:
        errors.append(f"target entity {relationship.target_id} was not defined")

    required_properties = REQUIRED_RELATIONSHIP_PROPERTIES.get(
        relationship.relationship_type,
        set(),
    )
    missing_properties = sorted(
        property_name
        for property_name in required_properties
        if not relationship.properties.get(property_name)
    )
    if missing_properties:
        errors.append(
            "missing required properties "
            + ", ".join(missing_properties)
        )

    return errors


def validate_artifact(artifact: KnowledgeArtifact) -> KnowledgeArtifact:
    """Drop contract-invalid relationships and record validation gaps."""
    gaps = list(artifact.knowledge_gaps)
    valid_relationships = []
    entity_ids = {entity.id for entity in artifact.entities}

    if artifact.knowledge_type and artifact.knowledge_type not in VALID_KNOWLEDGE_TYPES:
        gaps.append(
            KnowledgeGap(
                type="Invalid_Knowledge_Type",
                description=f"Unknown knowledge type: {artifact.knowledge_type}",
                context=artifact.source.path,
            )
        )

    for entity in artifact.entities:
        if entity.type not in VALID_ENTITY_TYPES:
            gaps.append(
                KnowledgeGap(
                    type="Invalid_Entity_Type",
                    description=f"Unknown entity type: {entity.type}",
                    context=entity.id,
                )
            )

    for relationship in artifact.relationships:
        errors = _relationship_errors(relationship, entity_ids)
        if not errors:
            valid_relationships.append(relationship)
            continue

        gaps.append(
            KnowledgeGap(
                type="Invalid_Relationship",
                description=(
                    f"Dropped {relationship.relationship_type} relationship: "
                    + "; ".join(errors)
                ),
                context=_relationship_context(relationship),
            )
        )

    return replace(
        artifact,
        relationships=valid_relationships,
        knowledge_gaps=gaps,
    )
