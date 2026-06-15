# consensus.py
# Orchestrates extractors and reconciler to produce consensus knowledge graph data

import time
from collections import Counter

class ConsensusExtractor:

    def __init__(self, extractors: list, reconciler, runs_per_model: int = 2, threshold: float = 0.5):
        self.extractors = extractors
        self.reconciler = reconciler
        self.runs_per_model = runs_per_model
        self.threshold = threshold

    def extract(self, file_path: str) -> dict:
        relationships_by_model = {}
        all_entities = []

        for extractor in self.extractors:
            model_name = extractor.__class__.__name__
            model_relationships = []

            print(f"\n  Running {model_name} ({self.runs_per_model} passes)...")

            for i in range(self.runs_per_model):
                print(f"    Pass {i + 1}/{self.runs_per_model}...")
                result = extractor.extract(file_path)

                if result:
                    all_entities.extend(result.get("entities", []))
                    model_relationships.extend(result.get("relationships", []))

                if i < self.runs_per_model - 1:
                    time.sleep(0.5)

            # Only keep relationships this model agreed with itself on
            rel_counts = Counter(
                (r.get("source", ""), r.get("type", "").lower().strip(), r.get("target", ""))
                for r in model_relationships
            )
            relationships_by_model[model_name] = [
                {"source": src, "type": typ, "target": tgt}
                for (src, typ, tgt), count in rel_counts.items()
                if count >= self.runs_per_model
            ]

            print(f"    {len(model_relationships)} raw → {len(relationships_by_model[model_name])} self-consistent")

        # Reconcile across models
        print(f"\n  Reconciling across {len(self.extractors)} models...")
        consensus_rels = self.reconciler.reconcile(relationships_by_model)
        print(f"  {sum(len(v) for v in relationships_by_model.values())} self-consistent → {len(consensus_rels)} cross-model consensus")

        # Deduplicate entities
        seen = set()
        consensus_entities = []
        for e in all_entities:
            key = (e.get("name", ""), e.get("type", ""))
            if key not in seen:
                seen.add(key)
                consensus_entities.append(e)

        print(f"  Entities: {len(consensus_entities)} deduplicated")

        return {"entities": consensus_entities, "relationships": consensus_rels}


if __name__ == "__main__":
    from extractors.claude import ClaudeExtractor
    from extractors.mistral import MistralExtractor
    from reconcilers.mistral import MistralReconciler
    from loader import write_to_neo4j, driver

    extractor = ConsensusExtractor(
        extractors=[ClaudeExtractor(), MistralExtractor()],
        reconciler=MistralReconciler(),
        runs_per_model=2
    )

    test_file = "../sn-docs/markdown/now-intelligence/now-assist-explorer.md"
    print(f"Running consensus extraction on: {test_file}")

    result = extractor.extract(test_file)

    print("\nWriting to Neo4j...")
    with driver.session() as session:
        write_to_neo4j(session, result["entities"], result["relationships"])
    print("Done.")