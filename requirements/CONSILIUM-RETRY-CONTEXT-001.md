---
id: CONSILIUM-RETRY-CONTEXT-001
status: confirmed
layer: feature
owner: auto
depends_on: [CONSILIUM-UTILS-001]
risk: 1
---

# retry_context

> On low confidence, proposes a concrete Read/Grep context-gathering plan for one extra deliberation pass.

## Input
- stdin: JSON deliberation bundle containing `confidence` (scalar or dict with `confidence` key), `generator.candidates`, `control.verdicts`, and `conservator.scores`
- CLI flag `--threshold`: confidence threshold below which a retry is recommended (default: 0.7)

## Description
Operationalizes the SKILL.md low-confidence recovery path by analyzing a completed deliberation bundle and producing a concrete context-gathering plan rather than immediately escalating to the user. When confidence is below threshold, it identifies the top-2 candidates by a composite utility score (mean of generator pass, control validity, and inverted conservator risk) and extracts file paths, symbol names, dotted attribute paths, and backtick-quoted tokens from their summaries and sketches using targeted regex patterns. The output is a JSON plan with suggested Read targets and Grep patterns per candidate; the orchestrating agent runs those commands, attaches results as `retry_context` to the bundle, and dispatches one additional Generator/Control/Conservator pass with the enriched input. The script is deliberately one-shot and does not execute the deliberation itself, capping the retry loop at one attempt before falling back to the existing user-ask flow.

## Output
- JSON object to stdout with `retry_recommended` (bool), `reason` (string), and `top_candidates` array
- Each `top_candidates` entry contains `id`, utility score, `files`, `symbols`, `suggested_reads` (up to 4 file paths), and `suggested_greps` (up to 4 regex patterns)
- When `retry_recommended` is false (confidence at/above threshold, only one valid candidate, or null confidence), `top_candidates` is an empty array
- exit code 0 on success; exit code 2 if stdin is not a JSON object

## WHAT — Verify intent (open questions for the human)
- None — doc is unambiguous.

## Acceptance (= tests)
- Given a bundle with `confidence=0.61` and two or more valid candidates, the output has `retry_recommended=true`, a `reason` string containing `0.61`, and exactly 2 entries in `top_candidates`.
- Given a bundle with `confidence=0.85`, the output has `retry_recommended=false` and `top_candidates=[]`.
- Each `top_candidates` entry's `suggested_greps` list contains escaped regex patterns, with plain function names suffixed by `\(` and dotted attribute paths left unsuffixed.
- Given a bundle with only one Control-valid candidate, the output has `retry_recommended=false` with reason `too few valid candidates for retry to discriminate`.
- Given a bundle where `confidence` is a dict (`{"confidence": 0.55, ...}`), the script correctly unwraps the nested value and evaluates it against the threshold.
