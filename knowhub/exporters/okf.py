"""Open Knowledge Format exporter for KnowHub artifacts.

OKF is represented as Markdown files with YAML frontmatter. We keep this
exporter dependency-free so bundles can be generated in minimal environments.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from knowhub.schema import KnowledgeArtifact


def _yaml_scalar(value: Any) -> str:
    if value is None:
        return '""'
    if isinstance(value, bool):
        return "true" if value else "false"
    return json.dumps(str(value), ensure_ascii=False)


def _frontmatter(values: dict[str, Any]) -> str:
    lines = ["---"]
    for key, value in values.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {_yaml_scalar(item)}")
        else:
            lines.append(f"{key}: {_yaml_scalar(value)}")
    lines.append("---")
    return "\n".join(lines)


def _write_markdown(path: Path, frontmatter: dict[str, Any], body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"{_frontmatter(frontmatter)}\n\n{body.strip()}\n",
        encoding="utf-8",
    )


def export_okf(artifacts: list[KnowledgeArtifact], output_dir: str | Path) -> None:
    """Write an OKF-style Markdown bundle to output_dir."""
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)

    index_lines = ["# KnowHub Knowledge Bundle", ""]

    for artifact in artifacts:
        source = artifact.source
        index_lines.append(f"- [{source.title}](documents/{source.id}.md)")

        _write_markdown(
            root / "documents" / f"{source.id}.md",
            {
                "type": "document",
                "title": source.title,
                "source_path": source.path,
                "knowledge_type": artifact.knowledge_type,
            },
            f"# {source.title}\n\n{artifact.reasoning}",
        )

        for entity in artifact.entities:
            _write_markdown(
                root / "entities" / f"{entity.id}.md",
                {
                    "type": "entity",
                    "title": entity.name,
                    "entity_type": entity.type,
                    "source_document": source.id,
                },
                f"# {entity.name}\n\n```json\n{json.dumps(entity.properties, indent=2, ensure_ascii=False)}\n```",
            )

        for index, relationship in enumerate(artifact.relationships, start=1):
            relationship_id = (
                f"{relationship.source_id}__"
                f"{relationship.relationship_type.lower()}__"
                f"{relationship.target_id}__{index}"
            )
            _write_markdown(
                root / "relationships" / f"{relationship_id}.md",
                {
                    "type": "relationship",
                    "title": relationship.relationship_type,
                    "source_id": relationship.source_id,
                    "target_id": relationship.target_id,
                    "relationship_type": relationship.relationship_type,
                    "source_document": source.id,
                    "confirmed_by": relationship.confirmed_by,
                },
                f"# {relationship.relationship_type}\n\n```json\n{json.dumps(relationship.properties, indent=2, ensure_ascii=False)}\n```",
            )

        for index, gap in enumerate(artifact.knowledge_gaps, start=1):
            _write_markdown(
                root / "gaps" / f"{source.id}_gap_{index}.md",
                {
                    "type": "knowledge_gap",
                    "title": gap.type,
                    "source_document": source.id,
                },
                f"# {gap.type}\n\n{gap.description}\n\n{gap.context}",
            )

    _write_markdown(
        root / "index.md",
        {"type": "knowledge_bundle", "title": "KnowHub Knowledge Bundle"},
        "\n".join(index_lines),
    )
