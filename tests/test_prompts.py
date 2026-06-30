import unittest

from knowhub.llms.ollama_client import OllamaClient
from knowhub.prompts import build_extraction_prompt


class PromptTests(unittest.TestCase):
    def test_frontier_prompt_is_concise_profile(self):
        prompt = build_extraction_prompt("Some text.", profile="frontier")

        self.assertIn("Profile: frontier", prompt)
        self.assertIn("KnowHub ontology contract", prompt)
        self.assertNotIn("Extra guidance", prompt)

    def test_local_prompt_includes_scaffolding(self):
        prompt = build_extraction_prompt("Some text.", profile="local_reasoning")

        self.assertIn("Profile: local_reasoning", prompt)
        self.assertIn("Extra guidance", prompt)
        self.assertIn("TRADEOFF", prompt)

    def test_ollama_defaults_to_local_reasoning_profile(self):
        client = OllamaClient(model="test-model")

        self.assertEqual(client.prompt_profile, "local_reasoning")


if __name__ == "__main__":
    unittest.main()
