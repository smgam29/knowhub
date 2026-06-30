# LLM Tuning Guide

KnowHub is BYO LLM, but not plug-and-pray.

The architecture is model-agnostic: any provider can be added behind the
`LLMClient` interface. Trustworthy extraction still depends on tuning each
model for KnowHub's task: implementation knowledge extraction, ontology
adherence, structured JSON output, and cross-model confirmation.

## Core Principle

Adding a model means adding two things:

1. A provider adapter that can call the model.
2. A tuning profile that captures how that model behaves on KnowHub extraction.

Untuned models should be treated as experimental until they pass the evaluation
harness on representative documents.

## Cross-Confirmation Is Required

Trusted KnowHub runs must use at least two tuned LLM profiles.

Single-model extraction is allowed for tests, development, and debugging, but it
is not a trustworthy production mode. The trust profile comes from comparing
independent model outputs and keeping relationships that survive confirmation.

The minimum trusted pattern is:

1. Run extraction with two or more tuned model profiles.
2. Measure self-consistency for each model when needed.
3. Cross-confirm relationships across model outputs.
4. Preserve model provenance in the output.
5. Export only confirmed or explicitly marked low-confidence knowledge.

If a user brings only one model, KnowHub can help evaluate that model, but it
should not present the result as cross-confirmed knowledge.

## What To Tune

### Prompt Hints

Keep the shared ontology prompt consistent across models, then add small
model-specific hints through `prepare_prompt()`.

Good hints are practical and specific:

- Return compact valid JSON only.
- Do not include markdown fences.
- Do not add explanation outside the JSON object.
- Use the exact relationship names from the ontology.
- Prefer knowledge gaps over incomplete relationships.

Avoid rewriting the whole ontology prompt per model. If every model has a
different ontology, cross-confirmation becomes less meaningful.

### Sampling Settings

Extraction should usually be low-temperature.

Recommended starting point:

- `temperature`: `0.0` to `0.3`
- retries: 1 to 3
- self-consistency passes: 2 or more for lower-confidence models

Higher temperature may help brainstorming, but KnowHub extraction needs
repeatable structure more than variety.

### Output Discipline

A useful KnowHub model must reliably produce parseable JSON.

Track these failure modes:

- empty responses
- markdown fenced JSON despite instructions
- prose before or after the JSON
- missing required top-level keys
- relationships without source or target IDs
- properties flattened into relationship text
- invalid relationship names

Some tolerance is fine. KnowHub can strip fences or recover a JSON object from
minor preamble text. A model that often emits malformed or incomplete JSON needs
more tuning before it should be trusted.

### Ontology Adherence

The model must follow the implementation ontology, not just extract generic
entities.

Evaluate whether it can:

- classify knowledge type correctly
- distinguish procedures from contextual or diagnostic guidance
- extract decisions, prerequisites, outcomes, and gaps
- populate required relationship properties
- avoid relationships that violate source-target constraints
- use `knowledge_gaps` when information is implied but underspecified

### Context Window And Chunking

Larger context windows are useful, but not a substitute for good chunking.

Prefer chunks that preserve semantic layout:

- heading path
- table/list/callout type
- warning/note/tip role
- page number when available
- parser evidence

The LLM should receive enough surrounding context to understand scope, but not
so much that it loses the specific implementation signal.

### JSON Repair Tolerance

Each model profile should record how much cleanup is usually needed.

Examples:

- no cleanup required
- strip markdown fences
- recover first JSON object from response
- retry on empty response
- reject because schema is incomplete

Heavy repair is a warning sign. The goal is not to make bad output look good;
the goal is to identify which models are reliable enough to participate in
confirmation.

## What LLMs Work Best

KnowHub extraction tends to work best with models that are strong at:

- instruction following
- structured JSON output
- schema discipline
- long-context reading
- careful classification
- relationship/property extraction
- consistency across repeated runs

It does not require the biggest model by default. A smaller model can be useful
if it reliably follows the ontology and gives different failure modes from the
primary model.

## Current Tuned Profiles

These are the profiles already explored in the prototype. Treat them as
project-specific findings, not universal model rankings.

| Model | Role | Status | Notes |
|---|---|---|---|
| Claude Haiku | Primary extractor | Tuned prototype | Good API-backed extractor. Used as one side of cross-model confirmation. |
| Phi-4 14B via Ollama | Secondary extractor | Tuned prototype | Best local extractor from the initial eval set. Stronger ontology adherence and property population than the other local candidates tested. |
| Mistral 7B via Ollama | Reconciler | Tuned prototype | Kept for reconciliation rather than primary extraction. |
| Qwen3 8B via Ollama | Candidate extractor | Experimental | Reliable calls in the eval harness, but needed more normalization and ontology tuning. |
| gpt-oss 20B via Ollama | Candidate extractor | Not recommended from initial eval | Produced empty or sparse responses too often in the initial eval. |
| Gemma 3 4B via Ollama | Superseded extractor | Retained for reference | Replaced by Phi-4 after evaluation. |

## Evaluation Checklist

Before trusting a new model profile:

1. Add the adapter or configure an existing provider adapter.
2. Add model-specific prompt hints and sampling settings.
3. Run the eval harness on comparative, diagnostic, and contextual excerpts.
4. Check parse success rate.
5. Check knowledge type accuracy.
6. Check ontology adherence.
7. Check property population.
8. Check gap detection.
9. Run at least two passes to measure self-consistency.
10. Compare against another tuned model for cross-confirmation.

## Passing Criteria

A model is ready for trusted KnowHub extraction when it can:

- return valid JSON consistently
- preserve the required schema
- classify knowledge type better than procedural fallback
- extract relationships with source, type, target, and required properties
- produce useful knowledge gaps
- repeat key relationships across runs
- agree with at least one other tuned model on important relationships

## Product Positioning

KnowHub should describe itself as:

> Model-agnostic, tuned-profile based, and cross-confirmed.

Not:

> Any LLM will work out of the box.

That difference matters. BYO LLM means users can bring their own models, but
they also own the tuning and evaluation needed to make those models trustworthy.
