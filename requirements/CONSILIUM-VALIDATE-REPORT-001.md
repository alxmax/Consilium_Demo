---
milestone: v1.0
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
- `chosen_approach` is present and either a non-empty string or JSON null; missing field is an error, explicit null is accepted (occurs on conservative-override veto AND Trias null-vote-patterns); no distinction is made between intentional and unintentional nulls
- if `skipped: true`, `skip_reason` is a non-empty string
- `deliberation_log` contains an aggregate step whose `result` is a dict (not a string narrative); for non-bypassed reports, `generator` and `control` steps must also be present; `conservator` step presence is NOT enforced (only validated under `--strict-round2`)
- `telemetry` is present for non-skipped reports and carries a non-empty `mode` string
- telemetry counts (`tokens_in`, `tokens_out`, `latency_ms`) must be non-negative ints (strict: `isinstance(v, int)` — float values such as `1500.0` are rejected); each count field is optional per voice

Reports manually assembled outside `build_report.py` are rejected — this gate
catches shape drift (e.g. aggregate.result as a narrative string).

## Output
- Exit 0 — report is valid
- Exit 1 — validation failed; each problem printed to stderr
- Exit 2 — malformed JSON input

## WHAT — Contract
- Shall validate report shape only (not deliberation substance): `success_criterion` and `verification` are non-empty strings; `chosen_approach` is present (explicit null accepted, missing field is an error); `telemetry` carries a non-empty `mode` for non-skipped reports.
- `deliberation_log` shall contain `generator`, `control`, and an aggregate step with `result` as a dict (not a string) for non-bypassed reports; `conservator` step presence is not enforced unless `--strict-round2` is set.
- Telemetry count fields (`tokens_in`, `tokens_out`, `latency_ms`) shall be non-negative `int`; float values such as `1500.0` shall be rejected.
- Shall exit 0 on valid, 1 on validation failure (each problem printed to stderr), 2 on malformed JSON.

## WHAT — Verify intent
- None - all questions resolved.

## Acceptance (= tests)
- Valid reports (from `.consilium/runs/*.json`) exit 0
- Missing `success_criterion` causes exit 1 with a message naming the field
- `skipped: true` without `skip_reason` causes exit 1
- Missing `telemetry.mode` on a non-skipped report causes exit 1
- Malformed JSON exits 2
