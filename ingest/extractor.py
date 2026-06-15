import os
import json
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()

# Normalise entity names to lower case and strip whitespace (assists with matching entities in Neo4j)

def normalise_entity_name(name):
    return name.lower().strip()

# Extracts entities and relationships from a markdown file using the Anthropic API

def extract_entities_and_relationships(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    if len(content) > 3000:
        content = content[:3000]

    prompt = f"""You are a knowledge graph builder. Analyze this ServiceNow documentation and extract entities and relationships.
    
Return ONLY a JSON object with this exact structure, no other text:
{{
    "entities": [
        {{"name": "entity name", "type": "Product|Feature|Concept|Integration|Persona"}}
    ],
    "relationships": [
        {{"source": "entity name", "target": "entity name", "type": "USES|REQUIRES|INTEGRATES_WITH|ENABLES|RELATES_TO"}}
    ]
}}

Documentation:
{content}"""    
    
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    response_text = message.content[0].text

    response_text = response_text.strip()
    if response_text.startswith("```json"):
        response_text = response_text[7:]
    if response_text.startswith("```"):
        response_text = response_text[3:]
    if response_text.endswith("```"):
        response_text = response_text[:-3]
    response_text = response_text.strip()

    try:
        result = json.loads(response_text)
    except json.JSONDecodeError:
        print(f"Warning: Could not parse JSON from response")
        result = {"entities": [], "relationships": []}

    for entity in result['entities']:
        entity['name'] = normalise_entity_name(entity['name'])

    for rel in result['relationships']:
        rel['source'] = normalise_entity_name(rel['source'])
        rel['target'] = normalise_entity_name(rel['target'])

    return result    

if __name__ == "__main__":
    test_file = os.path.expanduser("~/Documents/github/sn-docs/markdown/now-intelligence/now-assist-explorer.md")
    
    print(f"Extracting from: {test_file}")
    result = extract_entities_and_relationships(test_file)
    
    print(f"\nEntities found: {len(result['entities'])}")
    for entity in result['entities']:
        print(f"  - {entity['name']} ({entity['type']})")
    
    print(f"\nRelationships found: {len(result['relationships'])}")
    for rel in result['relationships']:
        print(f"  - {rel['source']} --[{rel['type']}]--> {rel['target']}")