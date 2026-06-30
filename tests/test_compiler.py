import json
import tempfile
import unittest
from pathlib import Path

from knowhub.compiler import compile_file
from knowhub.llms.static import StaticLLMClient
from knowhub.parsers.plain_text import PlainTextParser


def _response(model_specific_property):
    return json.dumps(
        {
            "reasoning": "An implementer would choose between implementation approaches.",
            "knowledge_type": "Comparative",
            "entities": [
                {"name": "Prompt customization", "type": "Decision"},
                {"name": "Maintenance overhead", "type": "Outcome"},
            ],
            "relationships": [
                {
                    "source": "Prompt customization",
                    "type": "TRADEOFF",
                    "target": "Maintenance overhead",
                    "properties": model_specific_property,
                }
            ],
            "knowledge_gaps": [],
        }
    )


class CompilerTests(unittest.TestCase):
    def test_compile_file_requires_multiple_llms_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "demo.txt"
            path.write_text("A simple implementation note.", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "requires at least two"):
                compile_file(
                    str(path),
                    parser=PlainTextParser(),
                    llm_clients=[
                        StaticLLMClient("model-a", _response({"gives": "speed"})),
                    ],
                )

    def test_compile_file_allows_single_llm_for_testing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "demo.txt"
            path.write_text(
                "Prompt customization is faster but creates maintenance overhead.",
                encoding="utf-8",
            )

            artifact = compile_file(
                str(path),
                parser=PlainTextParser(),
                llm_clients=[
                    StaticLLMClient("model-a", _response({"gives": "speed"})),
                ],
                min_support=1,
                allow_single_llm_for_testing=True,
            )

        self.assertEqual(len(artifact.relationships), 1)

    def test_compile_file_parses_extracts_and_confirms(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "demo.txt"
            path.write_text(
                "Prompt customization is faster but creates maintenance overhead.",
                encoding="utf-8",
            )

            artifact = compile_file(
                str(path),
                parser=PlainTextParser(),
                llm_clients=[
                    StaticLLMClient("model-a", _response({"gives": "speed"})),
                    StaticLLMClient("model-b", _response({"costs": "maintenance"})),
                ],
                min_support=2,
            )

        self.assertEqual(artifact.knowledge_type, "Comparative")
        self.assertEqual(len(artifact.relationships), 1)
        self.assertEqual(
            artifact.relationships[0].confirmed_by,
            ["model-a", "model-b"],
        )


if __name__ == "__main__":
    unittest.main()
