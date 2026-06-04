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
Provides the canonical HTML parser for FEEDBACK.html and a human-readable stats report over logged deliberation outcomes. The `parse_feedback` function is a shared utility imported by `priors.py`, `log_feedback.py`, `efficiency.py`, and deprecated scripts; it supports three HTML row layouts (attribute-based with `data-field`, and two legacy positional cell-count variants) for backward compatibility. When invoked as a CLI tool it prints total logged uses, per-outcome counts, overall success rate excluding pending entries, recent overrides, and optionally a breakdown of runs-on-disk by aggregation scheme. It exists to give the developer a fast, human-readable health check on the skill's real-world usefulness without opening the HTML journal manually.

## Output
- stdout: multi-line stats report (total uses, outcome breakdown, success rate, recent overrides, optional run scheme counts)
- exit code 0 always

## Acceptance (= tests)
- `parse_feedback` returns an empty list without error when FEEDBACK.html does not exist.
- `parse_feedback` correctly parses all three row layouts (8-cell Trias, 7-cell previous, 6-cell legacy) and attribute-based `data-field` rows.
- Rows whose `outcome` field is not one of `OK`, `BAD`, `OVR`, `PEND`, `PEND_HEADLESS` are silently skipped.
- With `--recent N`, only the last N entries are included in the report stats.
- With `--runs`, the report includes a per-aggregation-scheme breakdown from `.consilium/runs/*.json`, tolerating both legacy `aggregation.scheme` and current `deliberation_log[step=aggregate].scheme` shapes.
