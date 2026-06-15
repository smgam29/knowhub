import time
from collections import Counter
from extractor import extract_entities_and_relationships
from loader import write_to_neo4j, driver

def canonical_relationship(rel):
    # Create a hashable key for a relationship — source, type, target
    return (
        rel.get("source", ""),
        rel.get("type", "").lower().strip(),
        rel.get("target", "")
    )

def consensus_extract(file_path, runs=3, threshold=2):
    # Run extraction multiple times and return only relationships
    # that appear in at least `threshold` of `runs` runs

    all_relationships = []
    all_entities = []

    for i in range(runs):
        print(f"  Run {i + 1}/{runs}...")
        result = extract_entities_and_relationships(file_path)

        if result:
            all_entities.extend(result.get("entities", []))
            all_relationships.extend(result.get("relationships", []))

        if i < runs - 1:
            time.sleep(0.5)

    # Count how many runs each relationship appeared in
    rel_counts = Counter(canonical_relationship(r) for r in all_relationships)

    # Keep only relationships that met the threshold
    consensus_rels = [
        {"source": src, "type": typ, "target": tgt}
        for (src, typ, tgt), count in rel_counts.items()
        if count >= threshold
    ]

    # Deduplicate entities
    seen = set()
    consensus_entities = []
    for e in all_entities:
        key = (e.get("name", ""), e.get("type", ""))
        if key not in seen:
            seen.add(key)
            consensus_entities.append(e)

    # Show counts
    print(f"  Relationships: {len(all_relationships)} raw → {len(consensus_rels)} consensus")
    print(f"  Entities: {len(consensus_entities)} deduplicated")

    # Show confidence spread
    spread = Counter(rel_counts.values())
    print(f"  Confidence: 1-run={spread[1]}, 2-run={spread[2]}, 3-run={spread[3]}")

    # Show sample of what survived
    print(f"  Sample consensus relationships:")
    for rel in consensus_rels[:3]:
        print(f"    ✓ {rel['source']} --[{rel['type']}]--> {rel['target']}")

    # Show sample of what was dropped
    dropped = [(src, typ, tgt) for (src, typ, tgt), count in rel_counts.items() if count < threshold]
    print(f"  Dropped {len(dropped)} weak relationships:")
    for r in dropped[:3]:
        print(f"    ✗ {r[0]} --[{r[1]}]--> {r[2]}")

    return {"entities": consensus_entities, "relationships": consensus_rels}


if __name__ == "__main__":
    # Test on a single file first
    test_file = "../sn-docs/markdown/now-intelligence/now-assist-explorer.md"

    print(f"Running consensus extraction on: {test_file}")
    result = consensus_extract(test_file)

    print("\nWriting to Neo4j...")
    with driver.session() as session:
        write_to_neo4j(session, result["entities"], result["relationships"])
    print("Done.")