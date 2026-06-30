"""Minimal CLI for running the KnowHub compiler skeleton."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from knowhub.compiler import compile_directory, compile_file
from knowhub.exporters.cypher import render_cypher
from knowhub.exporters.json_exporter import export_json
from knowhub.exporters.okf import export_okf
from knowhub.llms.anthropic_client import AnthropicClient
from knowhub.llms.ollama_client import OllamaClient
from knowhub.llms.static import StaticLLMClient
from knowhub.parsers.plain_text import PlainTextParser
from knowhub.parsers.unstructured_adapter import UnstructuredParser


def _demo_response(properties):
    return json.dumps(
        {
            "reasoning": "An implementer would compare fast prompt customization with longer-term data optimization.",
            "knowledge_type": "Comparative",
            "entities": [
                {"name": "Prompt customization", "type": "Decision"},
                {"name": "Input data optimization", "type": "Decision"},
                {"name": "Maintenance overhead", "type": "Outcome"},
                {"name": "Summarization behavior", "type": "Feature"},
                {"name": "Out-of-box field label customization", "type": "Decision"},
            ],
            "relationships": [
                {
                    "source": "Prompt customization",
                    "type": "TRADEOFF",
                    "target": "Maintenance overhead",
                    "properties": properties,
                },
                {
                    "source": "Out-of-box field label customization",
                    "type": "CONFLICTS_WITH",
                    "target": "Summarization behavior",
                    "properties": {
                        "severity": "MEDIUM",
                        "notes": "The warning says field label customization should be validated against downstream summarization behavior.",
                    },
                },
            ],
            "knowledge_gaps": [],
        }
    )


def build_parser(name: str):
    if name == "plain-text":
        return PlainTextParser()
    if name == "unstructured":
        return UnstructuredParser()
    raise ValueError(f"Unsupported parser: {name}")


def build_llm_clients(names: list[str], ollama_timeout: int):
    clients = []
    for name in names:
        if name == "demo":
            clients.extend(
                [
                    StaticLLMClient(
                        "demo-model-a",
                        _demo_response(
                            {
                                "gives": "fast pilot results",
                                "costs": "ongoing maintenance overhead",
                                "severity": "MEDIUM",
                            }
                        ),
                    ),
                    StaticLLMClient(
                        "demo-model-b",
                        _demo_response(
                            {
                                "gives": "speed for a pilot",
                                "costs": "maintenance overhead",
                                "context": "pilot implementation",
                            }
                        ),
                    ),
                ]
            )
        elif name == "anthropic":
            clients.append(AnthropicClient())
        elif name.startswith("ollama:"):
            clients.append(
                OllamaClient(
                    model=name.split(":", 1)[1],
                    timeout=ollama_timeout,
                )
            )
        else:
            raise ValueError(f"Unsupported LLM client: {name}")
    return clients


def write_outputs(artifacts, output_dir: Path, exports: list[str]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    if "json" in exports:
        export_json(artifacts, output_dir / "artifact.json")

    if "cypher" in exports:
        (output_dir / "graph.cypher").write_text(
            render_cypher(artifacts),
            encoding="utf-8",
        )

    if "okf" in exports:
        export_okf(artifacts, output_dir / "okf")


def main() -> None:
    parser = argparse.ArgumentParser(description="Compile documents with KnowHub.")
    parser.add_argument("path", help="File or directory to compile.")
    parser.add_argument(
        "--parser",
        choices=["plain-text", "unstructured"],
        default="plain-text",
        help="Parser adapter to use.",
    )
    parser.add_argument(
        "--llm",
        action="append",
        default=None,
        help="LLM client to use. Options: demo, anthropic, ollama:<model>.",
    )
    parser.add_argument(
        "--export",
        action="append",
        choices=["json", "cypher", "okf"],
        default=["json"],
        help="Output format. Can be repeated.",
    )
    parser.add_argument(
        "--out",
        default="build/knowhub",
        help="Output directory.",
    )
    parser.add_argument(
        "--min-support",
        type=int,
        default=2,
        help="Minimum distinct model support required for a relationship.",
    )
    parser.add_argument(
        "--ollama-timeout",
        type=int,
        default=600,
        help="Read timeout in seconds for each Ollama model call.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print progress before each model call.",
    )
    args = parser.parse_args()

    input_path = Path(args.path)
    document_parser = build_parser(args.parser)
    llm_clients = build_llm_clients(args.llm or ["demo"], args.ollama_timeout)

    if input_path.is_dir():
        artifacts = compile_directory(
            str(input_path),
            parser=document_parser,
            llm_clients=llm_clients,
            min_support=args.min_support,
            verbose=args.verbose,
        )
    else:
        artifacts = [
            compile_file(
                str(input_path),
                parser=document_parser,
                llm_clients=llm_clients,
                min_support=args.min_support,
                verbose=args.verbose,
            )
        ]

    write_outputs(artifacts, Path(args.out), args.export)

    relationship_count = sum(len(artifact.relationships) for artifact in artifacts)
    print(
        f"Compiled {len(artifacts)} artifact(s), "
        f"{relationship_count} confirmed relationship(s)."
    )
    print(f"Wrote outputs to {args.out}")


if __name__ == "__main__":
    main()
