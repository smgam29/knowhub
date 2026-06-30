import unittest

from knowhub.schema import Entity, KnowledgeArtifact, Relationship, SourceDocument
from knowhub.validation import validate_artifact


class ValidationTests(unittest.TestCase):
    def test_validation_drops_relationships_to_missing_entities(self):
        artifact = KnowledgeArtifact(
            source=SourceDocument(path="demo.txt"),
            entities=[
                Entity(
                    id="prompt_customization",
                    name="Prompt customization",
                    type="Decision",
                )
            ],
            relationships=[
                Relationship(
                    source_id="prompt_customization",
                    relationship_type="TRADEOFF",
                    target_id="maintenance_overhead",
                    properties={"gives": "speed", "costs": "maintenance"},
                    confirmed_by=["model-a"],
                )
            ],
        )

        validated = validate_artifact(artifact)

        self.assertEqual(validated.relationships, [])
        self.assertEqual(validated.knowledge_gaps[0].type, "Invalid_Relationship")
        self.assertIn(
            "target entity maintenance_overhead was not defined",
            validated.knowledge_gaps[0].description,
        )

    def test_validation_drops_relationships_missing_required_properties(self):
        artifact = KnowledgeArtifact(
            source=SourceDocument(path="demo.txt"),
            entities=[
                Entity(
                    id="prompt_customization",
                    name="Prompt customization",
                    type="Decision",
                ),
                Entity(
                    id="maintenance_overhead",
                    name="Maintenance overhead",
                    type="Outcome",
                ),
            ],
            relationships=[
                Relationship(
                    source_id="prompt_customization",
                    relationship_type="TRADEOFF",
                    target_id="maintenance_overhead",
                    properties={"gives": "speed"},
                    confirmed_by=["model-a"],
                )
            ],
        )

        validated = validate_artifact(artifact)

        self.assertEqual(validated.relationships, [])
        self.assertIn("costs", validated.knowledge_gaps[0].description)

    def test_validation_keeps_contract_valid_relationships(self):
        artifact = KnowledgeArtifact(
            source=SourceDocument(path="demo.txt"),
            entities=[
                Entity(
                    id="prompt_customization",
                    name="Prompt customization",
                    type="Decision",
                ),
                Entity(
                    id="maintenance_overhead",
                    name="Maintenance overhead",
                    type="Outcome",
                ),
            ],
            relationships=[
                Relationship(
                    source_id="prompt_customization",
                    relationship_type="TRADEOFF",
                    target_id="maintenance_overhead",
                    properties={"gives": "speed", "costs": "maintenance"},
                    confirmed_by=["model-a"],
                )
            ],
        )

        validated = validate_artifact(artifact)

        self.assertEqual(len(validated.relationships), 1)
        self.assertEqual(validated.knowledge_gaps, [])


if __name__ == "__main__":
    unittest.main()
