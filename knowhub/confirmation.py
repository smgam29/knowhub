"""Cross-model confirmation for KnowHub artifacts."""

from __future__ import annotations

from collections import Counter

from knowhub.schema import Entity, KnowledgeArtifact, Relationship, SourceDocument


def _compatible_id(left: str, right: str) -> bool:
    if left == right:
        return True
    return left in right or right in left


def _find_compatible_relationship(
    relationships_by_key: dict[tuple[str, str, str], Relationship],
    relationship: Relationship,
) -> tuple[str, str, str] | None:
    for key, existing in relationships_by_key.items():
        if existing.relationship_type != relationship.relationship_type:
            continue
        if not _compatible_id(existing.source_id, relationship.source_id):
            continue
        if not _compatible_id(existing.target_id, relationship.target_id):
            continue
        return key
    return None


def confirm_artifacts(
    source_path: str,
    candidates: list[KnowledgeArtifact],
    min_support: int = 2,
) -> KnowledgeArtifact:
    """Merge candidate artifacts and keep relationships with enough support.

    Support is counted by distinct model names in relationship.confirmed_by. This
    keeps confirmation model-agnostic: Claude, Phi4, OpenAI, and local models all
    contribute the same kind of evidence.
    """
    entities_by_id: dict[str, Entity] = {}
    relationships_by_key: dict[tuple[str, str, str], Relationship] = {}
    knowledge_gaps = []
    knowledge_types = Counter()

    for artifact in candidates:
        if artifact.knowledge_type:
            knowledge_types[artifact.knowledge_type] += 1

        for entity in artifact.entities:
            entities_by_id.setdefault(entity.id, entity)

        for relationship in artifact.relationships:
            key = relationship.fingerprint()
            if key not in relationships_by_key:
                compatible_key = _find_compatible_relationship(
                    relationships_by_key,
                    relationship,
                )
                if compatible_key is not None:
                    key = compatible_key

            existing = relationships_by_key.get(key)
            if existing is None:
                relationships_by_key[key] = Relationship(
                    source_id=relationship.source_id,
                    relationship_type=relationship.relationship_type,
                    target_id=relationship.target_id,
                    properties=dict(relationship.properties),
                    confirmed_by=sorted(set(relationship.confirmed_by)),
                )
                continue

            existing.confirmed_by = sorted(
                set(existing.confirmed_by) | set(relationship.confirmed_by)
            )
            existing.properties.update(relationship.properties)

        knowledge_gaps.extend(artifact.knowledge_gaps)

    confirmed_relationships = [
        relationship
        for relationship in relationships_by_key.values()
        if len(set(relationship.confirmed_by)) >= min_support
    ]

    for relationship in confirmed_relationships:
        relationship.properties["support_count"] = len(set(relationship.confirmed_by))

    knowledge_type = ""
    if knowledge_types:
        knowledge_type = knowledge_types.most_common(1)[0][0]

    return KnowledgeArtifact(
        source=SourceDocument(path=source_path),
        entities=list(entities_by_id.values()),
        relationships=confirmed_relationships,
        knowledge_gaps=knowledge_gaps,
        knowledge_type=knowledge_type,
        reasoning=(
            f"Confirmed {len(confirmed_relationships)} relationships "
            f"from {len(candidates)} candidate extraction(s)."
        ),
    )
