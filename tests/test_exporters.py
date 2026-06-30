import tempfile
import unittest
from pathlib import Path

from knowhub.exporters.cypher import render_cypher
from knowhub.exporters.json_exporter import export_json, render_json
from knowhub.exporters.okf import export_okf
from knowhub.schema import KnowledgeArtifact


class ExporterTests(unittest.TestCase):
    def test_artifact_exports_to_cypher_and_okf(self):
        artifact = KnowledgeArtifact.from_extraction(
            "examples/demo/source.md",
            {
                "knowledge_type": "Comparative",
                "reasoning": "An implementer would choose between two approaches.",
                "entities": [
                    {"name": "Input data optimization", "type": "Decision"},
                    {"name": "Prompt customization", "type": "Decision"},
                    {"name": "Maintenance overhead", "type": "Outcome"},
                ],
                "relationships": [
                    {
                        "source": "Prompt customization",
                        "type": "TRADEOFF",
                        "target": "Maintenance overhead",
                        "properties": {
                            "gives": "fast pilot results",
                            "costs": "ongoing maintenance",
                            "severity": "MEDIUM",
                        },
                        "confirmed_by": ["claude-haiku", "phi4"],
                    }
                ],
                "knowledge_gaps": [
                    {
                        "type": "Missing_Property",
                        "description": "The long-term owner is not stated.",
                        "context": "Prompt customization section",
                    }
                ],
            },
        )

        cypher = render_cypher([artifact])
        self.assertIn("MERGE (d:Document", cypher)
        self.assertIn("TRADEOFF", cypher)
        self.assertIn("confirmed_by", cypher)

        rendered_json = render_json([artifact])
        self.assertIn('"artifacts"', rendered_json)
        self.assertIn('"knowledge_type": "Comparative"', rendered_json)

        with tempfile.TemporaryDirectory() as tmp:
            export_okf([artifact], tmp)
            root = Path(tmp)

            self.assertTrue((root / "index.md").exists())
            self.assertTrue((root / "documents").exists())
            self.assertTrue((root / "entities").exists())
            self.assertTrue((root / "relationships").exists())
            self.assertTrue((root / "gaps").exists())

            export_json([artifact], root / "artifact.json")
            self.assertTrue((root / "artifact.json").exists())


if __name__ == "__main__":
    unittest.main()
