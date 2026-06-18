# pipeline.py
# Runs the consensus extraction pipeline across multiple files in a product directory

import os
import time
import sys
from crawler import get_markdown_files
from consensus import ConsensusExtractor
from extractors.claude import ClaudeExtractor
from extractors.mistral import MistralExtractor
from reconcilers.mistral import MistralReconciler
from loader import write_to_neo4j, driver

# Configure the pipeline
extractor = ConsensusExtractor(
    extractors=[ClaudeExtractor(), MistralExtractor()],
    reconciler=MistralReconciler(),
    runs_per_model=2
)

def run_pipeline(directory: str, limit: int = None):
    # Get all markdown files in the directory
    files = get_markdown_files(directory)

    if limit:
        files = files[:limit]

    total = len(files)

    print(f"Found {total} files in {directory}")
    print(f"Starting pipeline...\n")

    success = 0
    failed = 0

    for i, file_path in enumerate(files):
        print(f"[{i + 1}/{total}] {os.path.basename(file_path)}")

        try:
            result = extractor.extract(file_path)

            with driver.session() as session:
                write_to_neo4j(session, result["entities"], result["relationships"])

            success += 1

        except Exception as e:
            print(f"  X Failed: {e}")
            failed += 1

        time.sleep(0.5)

    print(f"\nPipeline complete -- {success} succeeded, {failed} failed")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: venv/bin/python ingest/pipeline.py <directory> [--limit N]")
        print("Example: venv/bin/python ingest/pipeline.py ../sn-docs/markdown/now-intelligence --limit 10")
        sys.exit(1)

    directory = sys.argv[1]

    if not os.path.exists(directory):
        print(f"Directory not found: {directory}")
        sys.exit(1)

    limit = None
    if "--limit" in sys.argv:
        limit_index = sys.argv.index("--limit") + 1
        limit = int(sys.argv[limit_index])

    run_pipeline(directory, limit=limit)
