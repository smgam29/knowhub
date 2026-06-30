"""Provider-neutral document parser interface."""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from knowhub.schema import make_id


@dataclass
class ChunkEvidence:
    source: str
    detail: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "source": self.source,
            "detail": self.detail,
        }


@dataclass
class ParsedChunk:
    id: str
    text: str
    kind: str = "paragraph"
    role: str = "unknown"
    order: int = 0
    page_number: int | None = None
    heading_path: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    evidence: ChunkEvidence = field(
        default_factory=lambda: ChunkEvidence(source="parser_native")
    )

    def render_for_extraction(self) -> str:
        """Render semantic chunk context for an extraction prompt."""
        lines = [f"[{self.kind.upper()}"]
        if self.role != "unknown":
            lines[0] += f" role={self.role}"
        lines[0] += "]"

        if self.heading_path:
            lines.append(f"Heading: {' > '.join(self.heading_path)}")
        if self.page_number is not None:
            lines.append(f"Page: {self.page_number}")
        lines.append(f"Evidence: {self.evidence.source}:{self.evidence.detail}")
        lines.append("")
        lines.append(self.text)

        return "\n".join(lines).strip()


@dataclass
class ParsedDocument:
    source_path: str
    chunks: list[ParsedChunk] = field(default_factory=list)
    title: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.title is None:
            self.title = os.path.basename(self.source_path)

    @property
    def source_id(self) -> str:
        return make_id(os.path.relpath(self.source_path))

    @property
    def text(self) -> str:
        return "\n\n".join(chunk.render_for_extraction() for chunk in self.chunks)


class DocumentParser(ABC):
    """Minimal contract for parser adapters such as Unstructured or MinerU."""

    @abstractmethod
    def parse(self, file_path: str) -> ParsedDocument:
        pass
