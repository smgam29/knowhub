import json
import unittest

from knowhub.confirmation import confirm_artifacts
from knowhub.extraction import KnowledgeExtractor, parse_json_response
from knowhub.llms.static import StaticLLMClient


class HintingStaticLLMClient(StaticLLMClient):
    def __init__(self, name, response_text):
        super().__init__(name, response_text)
        self.last_prompt = ""

    def prepare_prompt(self, prompt: str) -> str:
        return f"MODEL HINT\n\n{prompt}"

    def generate(self, prompt: str):
        self.last_prompt = prompt
        return super().generate(prompt)


class ExtractionConfirmationTests(unittest.TestCase):
    def test_static_llm_extracts_artifact_and_tags_model(self):
        response = json.dumps(
            {
                "reasoning": "An implementer would compare two approaches.",
                "knowledge_type": "Comparative",
                "entities": [
                    {"id": "prompt_customization", "name": "Prompt customization", "type": "Decision"},
                    {"id": "maintenance_overhead", "name": "Maintenance overhead", "type": "Outcome"},
                ],
                "relationships": [
                    {
                        "source_id": "prompt_customization",
                        "relationship_type": "TRADEOFF",
                        "target_id": "maintenance_overhead",
                        "properties": {"gives": "speed", "costs": "maintenance"},
                    }
                ],
                "knowledge_gaps": [],
            }
        )

        extractor = KnowledgeExtractor(StaticLLMClient("test-model-a", response))
        artifact = extractor.extract_text("demo.md", "Prompt customization is faster but costs maintenance.")

        self.assertEqual(artifact.knowledge_type, "Comparative")
        self.assertEqual(artifact.relationships[0].confirmed_by, ["test-model-a"])

    def test_extractor_uses_model_specific_prompt_hook(self):
        response = json.dumps(
            {
                "entities": [],
                "relationships": [],
                "knowledge_gaps": [],
            }
        )

        client = HintingStaticLLMClient("hinted-model", response)
        KnowledgeExtractor(client).extract_text("demo.md", "Some text.")

        self.assertTrue(client.last_prompt.startswith("MODEL HINT"))

    def test_parse_json_response_accepts_code_fences(self):
        parsed = parse_json_response('```json\n{"entities": [], "relationships": []}\n```')
        self.assertEqual(parsed["entities"], [])

    def test_confirmation_keeps_cross_model_relationships(self):
        result_a = json.dumps(
            {
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
                        "properties": {"gives": "speed"},
                    }
                ],
                "knowledge_gaps": [],
            }
        )
        result_b = json.dumps(
            {
                "knowledge_type": "Comparative",
                "entities": [
                    {"name": "Prompt customization", "type": "Decision"},
                    {"name": "Maintenance overhead", "type": "Outcome"},
                ],
                "relationships": [
                    {
                        "source_id": "prompt_customization",
                        "relationship_type": "TRADEOFF",
                        "target_id": "maintenance_overhead",
                        "properties": {"costs": "maintenance"},
                    }
                ],
                "knowledge_gaps": [],
            }
        )

        artifact_a = KnowledgeExtractor(StaticLLMClient("model-a", result_a)).extract_text("demo.md", "text")
        artifact_b = KnowledgeExtractor(StaticLLMClient("model-b", result_b)).extract_text("demo.md", "text")

        confirmed = confirm_artifacts("demo.md", [artifact_a, artifact_b], min_support=2)

        self.assertEqual(len(confirmed.relationships), 1)
        relationship = confirmed.relationships[0]
        self.assertEqual(relationship.confirmed_by, ["model-a", "model-b"])
        self.assertEqual(relationship.properties["support_count"], 2)
        self.assertEqual(relationship.properties["gives"], "speed")
        self.assertEqual(relationship.properties["costs"], "maintenance")

    def test_confirmation_matches_compatible_entity_ids(self):
        result_a = json.dumps(
            {
                "knowledge_type": "Comparative",
                "entities": [
                    {"id": "prompt_customization_pilot", "name": "Prompt customization for pilot", "type": "Decision"},
                    {"id": "input_data_optimization", "name": "Input data optimization", "type": "Decision"},
                ],
                "relationships": [
                    {
                        "source_id": "prompt_customization_pilot",
                        "relationship_type": "TRADEOFF",
                        "target_id": "input_data_optimization",
                        "properties": {"gives": "speed"},
                    }
                ],
                "knowledge_gaps": [],
            }
        )
        result_b = json.dumps(
            {
                "knowledge_type": "Comparative",
                "entities": [
                    {"id": "prompt_customization", "name": "Prompt customization", "type": "Decision"},
                    {"id": "input_data_optimization", "name": "Input data optimization", "type": "Decision"},
                ],
                "relationships": [
                    {
                        "source_id": "prompt_customization",
                        "relationship_type": "TRADEOFF",
                        "target_id": "input_data_optimization",
                        "properties": {"costs": "maintenance"},
                    }
                ],
                "knowledge_gaps": [],
            }
        )

        artifact_a = KnowledgeExtractor(StaticLLMClient("model-a", result_a)).extract_text("demo.md", "text")
        artifact_b = KnowledgeExtractor(StaticLLMClient("model-b", result_b)).extract_text("demo.md", "text")

        confirmed = confirm_artifacts("demo.md", [artifact_a, artifact_b], min_support=2)

        self.assertEqual(len(confirmed.relationships), 1)
        self.assertEqual(confirmed.relationships[0].confirmed_by, ["model-a", "model-b"])


if __name__ == "__main__":
    unittest.main()
