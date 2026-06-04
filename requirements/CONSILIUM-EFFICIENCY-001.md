---
id: CONSILIUM-EFFICIENCY-001
status: confirmed
layer: feature
owner: auto
test_exempt: "reads runs/ JSON and FEEDBACK.html at test time — integration-only"
depends_on: [CONSILIUM-FEEDBACK-001, CONSILIUM-UTILS-001]
risk: 1
---

# efficiency

> Computes a per-mode efficiency score (tokens per OK outcome) by joining telemetry with feedback.

## Input
- `.consilium/runs/*.json`: deliberation run files with `telemetry` blocks (overridable via `--runs`)
- `.consilium/FEEDBACK.html`: user-outcome journal (overridable via `--feedback`)
- `.consilium/runs/.run_path_map.json`: sidecar fingerprint-to-run-path index written by `log_feedback.py`
- CLI flags: `--by-mode`, `--compare MODE...`, `--since YYYY-MM-DD`, `--json`, `--self-test`, `--feedback`, `--runs`

## Description
Computes a per-mode efficiency score defined as `total_tokens / ok_count` (lower is better), joining run telemetry with user-logged outcomes from FEEDBACK.html via a fingerprint sidecar map. Only outcomes marked `OK` count toward the numerator; `BAD`, `OVR`, and `PEND` outcomes are tracked separately and modes with fewer than three telemetry runs are flagged as `insufficient_data`. Alongside the raw `tokens_per_ok` metric it also emits `tokens_per_dispatch` (normalized by number of voice calls) and average latency, then ranks modes by efficiency. The script deliberately does not compare quality across modes - a Trias OK represents deeper deliberation than a Sequential OK - and states this caveat explicitly in its output.

## Output
- stdout: JSON object with `modes` (per-mode stats), `ranking` (sorted by `tokens_per_ok`), and `caveat` string
- stderr: warning when the outcome map is empty or cannot be loaded
- exit code 0 on success, 1 if runs directory is not found

## WHAT — Verify intent (open questions for the human)
- The metric is `total_tokens / ok_count` (lower is better) — but a Trias OK represents deeper deliberation than a Sequential OK; is there any normalization or weighting applied per mode, or is the raw metric always emitted as-is with only a caveat string?
- `tokens_per_dispatch` is 'normalized by number of voice calls' — how is the voice-call count determined for skipped runs (which have 0 voice calls), and are skipped runs included or excluded from this sub-metric?
- The `--since YYYY-MM-DD` filter 'filters out runs whose timestamp or filename stem sorts before the given date' — if the timestamp inside the run JSON and the filename stem disagree (e.g., a renamed file), which source takes precedence?

## Acceptance (= tests)
- With three or more runs all marked `OK`, `tokens_per_ok` is a non-null integer equal to `total_tokens / ok_count`.
- Runs with outcomes `BAD`, `OVR`, or `PEND` increment `not_ok_count` and are excluded from `tokens_per_ok` numerator.
- Modes with fewer than `MIN_RUNS` (3) telemetry runs emit `note: insufficient_data` and null `tokens_per_ok`.
- `--self-test` runs against an inline fixture without reading the filesystem and exits 0 with `self-test PASS` on success.
- `--since YYYY-MM-DD` filters out runs whose timestamp or filename stem sorts before the given date.
