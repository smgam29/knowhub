import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

def write_to_neo4j(session, entities, relationships):
    for entity in entities:
        session.run(
            "MERGE (n:Entity {name: $name, type: $type})",
            name=entity['name'],
            type=entity['type']
        )
    
    for rel in relationships:
        session.run(
            """
            MATCH (a:Entity {name: $source})
            MATCH (b:Entity {name: $target})
            MERGE (a)-[r:RELATIONSHIP {type: $type}]->(b)
            """,
            source=rel['source'],
            target=rel['target'],
            type=rel['type']
        )

if __name__ == "__main__":
    from extractor import extract_entities_and_relationships
    
    test_file = os.path.expanduser("~/Documents/github/sn-docs/markdown/now-intelligence/now-assist-explorer.md")
    
    result = extract_entities_and_relationships(test_file)
    
    with driver.session() as session:
        write_to_neo4j(session, result['entities'], result['relationships'])
    
    print(f"Written to Neo4j:")
    print(f"  - {len(result['entities'])} entities")
    print(f"  - {len(result['relationships'])} relationships")
    
    driver.close()