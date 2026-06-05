---
id: CONSILIUM-FEEDBACK-001
status: confirmed
layer: bus
owner: auto
test_exempt: "file I/O wrapper with no isolated pure-function surface"
depends_on: [CONSILIUM-UTILS-001]
risk: 1
---

# feedback

> Canonical FEEDBACK.html parser + a human-readable stats report over logged outcomes.

## Input
- `.consilium/FEEDBACK.html`: the append-only HTML journal of logged deliberation outcomes (path from `utils.FEEDBACK_PATH`)
- `.consilium/runs/*.json`: deliberation run files, read only when `--runs` flag is passed
- CLI flags: `--recent N`, `--runs`

## Description
Provides the canonical HTML parser for FEEDBACK.html and a human-readable stats report over logged deliberation outcomes. The `parse_feedback` function is a shared utility imported by `priors.py`, `log_feedback.py`, `efficiency.py`, and deprecated scripts; it supports three HTML row layouts (attribute-based with `data-field`, and two legacy positional cell-count variants) for backward compatibility. Layout precedence is strict: attribute-based (`data-field`) is tried first; positional fallback only applies when no `data-field` attributes are found, matched by exact cell count (8 → 7 → 6 → skip). Rows with an unrecognized `outcome` field are dropped entirely — they are excluded from both the total count and all outcome stats. The success-rate denominator is `OK + BAD + OVR` only; both `PEND` and `PEND_HEADLESS` are excluded. When invoked as a CLI tool it prints total logged uses, per-outcome counts, overall success rate excluding pending entries, recent overrides, and optionally a breakdown of runs-on-disk by aggregation scheme. It exists to give the developer a fast, human-readable health check on the skill's real-world usefulness without opening the HTML journal manually.

## Output
- stdout: multi-line stats report (total uses, outcome breakdown, success rate, recent overrides, optional run scheme counts)
- exit code 0 always

## WHAT — Verify intent
- None - all questions resolved.

## Acceptance (= tests)
- `parse_feedback` returns an empty list without error when FEEDBACK.html does not exist.
- `parse_feedback` correctly parses all three row layouts (8-cell Trias, 7-cell previous, 6-cell legacy) and attribute-based `data-field` rows.
- Rows whose `outcome` field is not one of `OK`, `BAD`, `OVR`, `PEND`, `PEND_HEADLESS` are silently skipped.
- With `--recent N`, only the last N entries are included in the report stats.
- With `--runs`, the report includes a per-aggregation-scheme breakdown from `.consilium/runs/*.json`, tolerating both legacy `aggregation.scheme` and current `deliberation_log[step=aggregate].scheme` shapes.

## Why test_exempt

`feedback.py` is a thin read-only wrapper over `FEEDBACK.html` — its only logic is HTML row parsing and outcome counting. Both are exercised indirectly by `test_feedback_html.py` (which tests the HTML round-trip format) and by `test_priors.py` (which calls the same HTML-parsing path to derive priors signals). A dedicated `test_feedback.py` would duplicate fixture setup already done in those two files without adding independent signal.
