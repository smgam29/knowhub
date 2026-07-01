"""High-level KnowHub compile pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from knowhub.confirmation import confirm_artifacts
from knowhub.extraction import KnowledgeExtractor
from knowhub.llms.base import LLMClient
from knowhub.parsers.base import DocumentParser
from knowhub.schema import KnowledgeArtifact
from knowhub.validation import validate_artifact


@dataclass
class CompileResult:
    artifact: KnowledgeArtifact
    candidates: list[KnowledgeArtifact]


def _validate_llm_count(
    llm_clients: list[LLMClient],
    allow_single_llm_for_testing: bool,
) -> None:
    if len(llm_clients) >= 2:
        return

    if allow_single_llm_for_testing and len(llm_clients) == 1:
        return

    raise ValueError(
        "KnowHub trusted compilation requires at least two tuned LLM clients "
        "for cross-confirmation. Single-LLM runs are only allowed for tests."
    )


def compile_file(
    file_path: str,
    parser: DocumentParser,
    llm_clients: list[LLMClient],
    min_support: int = 2,
    allow_single_llm_for_testing: bool = False,
    verbose: bool = False,
) -> KnowledgeArtifact:
    """Parse one file, extract with multiple LLMs, and confirm relationships."""
    return compile_file_with_candidates(
        file_path,
        parser=parser,
        llm_clients=llm_clients,
        min_support=min_support,
        allow_single_llm_for_testing=allow_single_llm_for_testing,
        verbose=verbose,
    ).artifact


def compile_file_with_candidates(
    file_path: str,
    parser: DocumentParser,
    llm_clients: list[LLMClient],
    min_support: int = 2,
    allow_single_llm_for_testing: bool = False,
    verbose: bool = False,
) -> CompileResult:
    """Parse one file and return confirmed plus per-model candidate artifacts."""
    _validate_llm_count(llm_clients, allow_single_llm_for_testing)
    parsed = parser.parse(file_path)
    candidates = []
    for client in llm_clients:
        if verbose:
            print(f"Extracting {parsed.source_path} with {client.name}...")
        extracted = KnowledgeExtractor(client).extract_text(
            parsed.source_path,
            parsed.text,
        )
        candidates.append(validate_artifact(extracted))

    artifact = confirm_artifacts(
        parsed.source_path,
        candidates,
        min_support=min_support,
    )
    return CompileResult(artifact=artifact, candidates=candidates)


def compile_directory(
    directory: str,
    parser: DocumentParser,
    llm_clients: list[LLMClient],
    suffixes: set[str] | None = None,
    min_support: int = 2,
    allow_single_llm_for_testing: bool = False,
    verbose: bool = False,
) -> list[KnowledgeArtifact]:
    """Compile all matching files in a directory tree."""
    _validate_llm_count(llm_clients, allow_single_llm_for_testing)
    allowed_suffixes = suffixes or {".md", ".txt", ".pdf", ".ppt", ".pptx"}
    root = Path(directory)

    artifacts = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in allowed_suffixes:
            continue

        artifacts.append(
            compile_file(
                str(path),
                parser=parser,
                llm_clients=llm_clients,
                min_support=min_support,
                allow_single_llm_for_testing=allow_single_llm_for_testing,
                verbose=verbose,
            )
        )

    return artifacts


def compile_directory_with_candidates(
    directory: str,
    parser: DocumentParser,
    llm_clients: list[LLMClient],
    suffixes: set[str] | None = None,
    min_support: int = 2,
    allow_single_llm_for_testing: bool = False,
    verbose: bool = False,
) -> list[CompileResult]:
    """Compile all matching files and preserve per-model candidates."""
    _validate_llm_count(llm_clients, allow_single_llm_for_testing)
    allowed_suffixes = suffixes or {".md", ".txt", ".pdf", ".ppt", ".pptx"}
    root = Path(directory)

    results = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in allowed_suffixes:
            continue

        results.append(
            compile_file_with_candidates(
                str(path),
                parser=parser,
                llm_clients=llm_clients,
                min_support=min_support,
                allow_single_llm_for_testing=allow_single_llm_for_testing,
                verbose=verbose,
            )
        )

    return results
