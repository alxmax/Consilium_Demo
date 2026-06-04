---
id: CONSILIUM-VALIDATE-REPORT-001
status: confirmed
layer: bus
owner: auto
depends_on: [CONSILIUM-PERSONALITIES-001, CONSILIUM-UTILS-001]
risk: 2  # REVIEW
---

# validate_report

> Describes observed behavior, verified against scripts/validate_report.py source.

## Input
- A deliberation report JSON on stdin (produced by `build_report.py`)

## Description
Constitution Principle #4 gate. Validates report *shape*, not deliberation
*substance* — confirms that required fields exist and are well-formed.

Checks enforced:
- `success_criterion` and `verification` are non-empty strings
- `chosen_approach` is a non-empty string OR null (conservative-override veto case)
- if `skipped: true`, `skip_reason` is a non-empty string
- `deliberation_log` contains an aggregate step whose `result` is a dict (not a string narrative)
- `telemetry` is present for non-skipped reports and carries a non-empty `mode` string
- telemetry counts (token/latency) are non-negative ints where present

Reports manually assembled outside `build_report.py` are rejected — this gate
catches shape drift (e.g. aggregate.result as a narrative string).

## Output
- Exit 0 — report is valid
- Exit 1 — validation failed; each problem printed to stderr
- Exit 2 — malformed JSON input

## WHAT — Verify intent (open questions for the human)
- The requirement says `chosen_approach` may be 'null (conservative-override veto case)' — but are there other valid null cases (e.g., a BLOCK outcome from the glossary_fail path), and does the validator distinguish between intentional nulls and missing fields?
- The check for `deliberation_log` requires 'an aggregate step whose `result` is a dict (not a string narrative)' — what other steps must be present in `deliberation_log` for a non-skipped report, and are missing steps (e.g., a report missing the `conservator` step) caught by the validator?
- Telemetry 'counts (token/latency) are non-negative ints where present' — does the validator reject float values (e.g., `1500.0` instead of `1500`), and is the 'where present' qualifier precisely defined (which telemetry sub-fields are required vs. optional)?

## Acceptance (= tests)
- Valid reports (from `.consilium/runs/*.json`) exit 0
- Missing `success_criterion` causes exit 1 with a message naming the field
- `skipped: true` without `skip_reason` causes exit 1
- Missing `telemetry.mode` on a non-skipped report causes exit 1
- Malformed JSON exits 2
