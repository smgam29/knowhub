import tempfile
import unittest
from pathlib import Path

from knowhub.parsers.base import ChunkEvidence, ParsedChunk
from knowhub.parsers.plain_text import PlainTextParser


class ParserTests(unittest.TestCase):
    def test_chunk_rendering_includes_semantic_context(self):
        chunk = ParsedChunk(
            id="chunk_1",
            text="Do not customize this field.",
            kind="callout",
            role="warning",
            order=1,
            page_number=7,
            heading_path=["Now Assist", "Limitations"],
            evidence=ChunkEvidence(
                source="deterministic_rule",
                detail="text_prefix_warning",
            ),
        )

        rendered = chunk.render_for_extraction()

        self.assertIn("[CALLOUT role=warning]", rendered)
        self.assertIn("Heading: Now Assist > Limitations", rendered)
        self.assertIn("Page: 7", rendered)
        self.assertNotIn("deterministic_rule:text_prefix_warning", rendered)

        rendered_with_evidence = chunk.render_for_extraction(include_evidence=True)

        self.assertIn(
            "Parser evidence (not source content): "
            "deterministic_rule:text_prefix_warning",
            rendered_with_evidence,
        )

    def test_plain_text_parser_outputs_chunks(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "demo.txt"
            path.write_text("A simple implementation note.", encoding="utf-8")

            parsed = PlainTextParser().parse(str(path))

        self.assertEqual(len(parsed.chunks), 1)
        self.assertEqual(parsed.chunks[0].kind, "paragraph")
        self.assertEqual(parsed.chunks[0].evidence.source, "deterministic_rule")
        self.assertIn("[PARAGRAPH]", parsed.text)


if __name__ == "__main__":
    unittest.main()
