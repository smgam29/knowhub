"""JSON exporter for KnowHub's internal artifact format."""

from __future__ import annotations

import json
from pathlib import Path

from knowhub.schema import KnowledgeArtifact


def render_json(artifacts: list[KnowledgeArtifact]) -> str:
    return json.dumps(
        {
            "artifacts": [artifact.to_dict() for artifact in artifacts],
        },
        indent=2,
        ensure_ascii=False,
    )


def export_json(artifacts: list[KnowledgeArtifact], output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_json(artifacts) + "\n", encoding="utf-8")


def render_candidates_json(candidates: list[KnowledgeArtifact]) -> str:
    return json.dumps(
        {
            "candidates": [candidate.to_dict() for candidate in candidates],
        },
        indent=2,
        ensure_ascii=False,
    )


def export_candidates_json(
    candidates: list[KnowledgeArtifact],
    output_path: str | Path,
) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_candidates_json(candidates) + "\n", encoding="utf-8")
