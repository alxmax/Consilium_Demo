---
id: CONSILIUM-INFER-PIPELINE-001
status: confirmed
layer: feature
owner: auto
depends_on: [CONSILIUM-IMPLEMENT-PIPELINE-001, CONSILIUM-UTILS-001]
risk: 1
---

# Infer implementation pipeline steps

> Reads a deliberation report (from `build_report.py`) and determines which implementation steps apply — using a lookup table keyed on magnitude × reversibility — then presents them for confirmation before execution (SKILL.md Step 7).

## WHAT — Contract

- Shall read a deliberation JSON (from `--input` or stdin) and look up `(magnitude, reversibility)` in the step table to return an ordered list from `{implement, compile, review, test}`.
- With `--dry-run`, shall print inferred steps and exit 0 without confirmation or execution.
- With `--yes`, shall skip the confirmation prompt (CI/headless mode).
- Shall exit 1 when the user declines or the inference produces no steps.
- Shall exit 2 on invalid JSON or missing required fields.
- When `chosen_approach` is `do_nothing` or `skipped`, shall exit 1 with a clear message (no steps to infer).
- Shall also expose `recommend_implement_mode(report)` — returns `"pipeline"` for regression-risk quadrants (`moderate×irreversible`, `high×{partial,irreversible}`, `critical×any`), else `"single_shot"`.

## WHAT — Verify intent (open questions for the human)

- None — contract matches SKILL.md Step 7 routing table and script docstring.

## HOW — Acceptance (= tests)

- Given a report with `magnitude=moderate, reversibility=irreversible`, inferred steps are `[implement, compile, review, test]`.
- Given `chosen_approach=do_nothing`, exits 1.
- Given `--dry-run`, prints steps and exits 0 without writing any file.
- Given invalid JSON input, exits 2.
- `recommend_implement_mode` returns `"pipeline"` for `moderate×irreversible`; `"single_shot"` for `trivial×complete`.

## WHERE — Current implementation

- scripts/infer_pipeline.py
<!-- implements: CONSILIUM-INFER-PIPELINE-001 -->
