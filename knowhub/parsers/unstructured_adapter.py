"""Adapter around the original ingest/preprocessor.py parser."""

from __future__ import annotations

from pathlib import Path

from knowhub.parsers.base import ChunkEvidence, DocumentParser, ParsedChunk, ParsedDocument


KIND_BY_NATIVE_TYPE = {
    "Title": "heading",
    "NarrativeText": "paragraph",
    "ListItem": "list_item",
    "Table": "table",
}


def _infer_role(text: str) -> str:
    prefix = text.strip().lower()
    if prefix.startswith(("warning:", "caution:", "do not ", "never ")):
        return "warning"
    if prefix.startswith(("note:", "important:")):
        return "note"
    if prefix.startswith(("tip:", "best practice:")):
        return "tip"
    return "unknown"


class UnstructuredParser(DocumentParser):
    """Use the existing prototype preprocessor without moving or rewriting it."""

    def parse(self, file_path: str) -> ParsedDocument:
        from ingest.preprocessor import KEEP_TYPES
        from unstructured.partition.md import partition_md
        from unstructured.partition.pdf import partition_pdf
        from unstructured.partition.pptx import partition_pptx

        path = Path(file_path)
        ext = path.suffix.lower()

        if ext == ".md":
            elements = partition_md(filename=str(path))
        elif ext == ".pdf":
            elements = partition_pdf(filename=str(path))
        elif ext in (".pptx", ".ppt"):
            elements = partition_pptx(filename=str(path))
        else:
            raise ValueError(f"Unsupported file type: {ext}")

        chunks = []
        heading_path: list[str] = []

        for index, element in enumerate(elements, start=1):
            native_type = type(element).__name__
            if native_type not in KEEP_TYPES:
                continue

            text = str(element).strip()
            if not text:
                continue

            kind = KIND_BY_NATIVE_TYPE.get(native_type, "paragraph")
            if kind == "heading":
                heading_path = [text]

            chunks.append(
                ParsedChunk(
                    id=f"chunk_{len(chunks) + 1}",
                    text=text,
                    kind=kind,
                    role=_infer_role(text),
                    order=len(chunks) + 1,
                    heading_path=list(heading_path),
                    metadata={
                        "native_type": native_type,
                        "native_order": index,
                    },
                    evidence=ChunkEvidence(
                        source="parser_native",
                        detail=f"unstructured:{native_type}",
                    ),
                )
            )

        return ParsedDocument(
            source_path=str(path),
            title=path.name,
            chunks=chunks,
            metadata={"parser": "unstructured"},
        )
