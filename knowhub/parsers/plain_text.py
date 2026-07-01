"""Plain text parser for lightweight tests and simple inputs."""

from __future__ import annotations

from pathlib import Path

from knowhub.parsers.base import ChunkEvidence, DocumentParser, ParsedChunk, ParsedDocument


class PlainTextParser(DocumentParser):
    def parse(self, file_path: str) -> ParsedDocument:
        path = Path(file_path)
        text = path.read_text(encoding="utf-8")
        return ParsedDocument(
            source_path=str(path),
            title=path.name,
            chunks=[
                ParsedChunk(
                    id="chunk_1",
                    text=text,
                    kind="paragraph",
                    order=1,
                    evidence=ChunkEvidence(
                        source="deterministic_rule",
                        detail="plain_text_file",
                    ),
                )
            ],
            metadata={"parser": "plain_text"},
        )
