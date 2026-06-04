---
id: CONSILIUM-LOG-FEEDBACK-001
status: confirmed
layer: feature
owner: auto
depends_on: [CONSILIUM-FEEDBACK-001, CONSILIUM-RENDER-FEEDBACK-HTML-001, CONSILIUM-UTILS-001]
risk: 1
---

# log_feedback

> Atomically appends (or upgrades) a FEEDBACK.html row from a deliberation report.

## Input
- Deliberation report JSON via stdin (required)
- `.consilium/FEEDBACK.html`: existing journal, created if absent (overridable via `--feedback`)
- `.consilium/runs/.run_path_map.json`: fingerprint-to-run-path sidecar (read and updated)
- CLI flags: `--outcome OK|BAD|OVR|PEND|PEND_HEADLESS`, `--override-target`, `--user-note`, `--run-path`, `--dry-run`, `--force-override`

## Description
Atomically appends a feedback entry to FEEDBACK.html from a deliberation report JSON, removing the manual friction of Step 6 outcome logging. It derives `date` (today), `context` (first 60 chars of `success_criterion`), `chosen` (from `chosen_approach`), an auto-generated `note` (candidate count, veto count, confidence, mode), and records the caller-supplied `outcome`. Before appending it checks for duplicates using a 16-character SHA-256 fingerprint keyed on `date|chosen|context|run_id`; if the existing row has the same `run_path` but a different outcome (e.g., PEND->OK), the row is upgraded in place rather than duplicated. The sidecar `.run_path_map.json` is updated on every real write so `efficiency.py` and `audit_feedback.py` can later join outcomes to telemetry by run path. The `--outcome OK` path enforces a 0.70 confidence threshold gate, requiring `--force-override` to bypass.

## Output
- stdout: `date | context | chosen | outcome | note` summary line (or `skipped (duplicate): ...` on exit 3)
- `.consilium/FEEDBACK.html`: updated atomically with the new or upgraded row
- `.consilium/runs/.run_path_map.json`: updated with the new fingerprint->run_path entry
- exit code 0 on success, 1 on validation error or confidence gate rejection, 2 on malformed JSON or missing required args, 3 on duplicate entry skipped

## WHAT — Verify intent

- None - all questions resolved.

## Contract addenda (from code audit 2026-06-04)
- When `run_id` is absent, the fingerprint falls back to a microsecond-precision timestamp (`datetime.now().strftime("%f")`) as the 4th field — not a 3-field key. This prevents same-day collisions but makes the fingerprint non-deterministic: two recomputed fingerprints for the same legacy row will differ, so old no-run_id rows can never be matched by fingerprint lookup (they fall back to `run_path=None`).
- The confidence gate reads `report.get("confidence")` — the top-level key only. If a report carries both a top-level `confidence` and a nested `confidence.confidence` dict, the top-level value is used and the nested form is silently ignored.
- The row-upgrade path (PEND → OK) uses a read-modify-write cycle protected only by `atomic_write_text` (rename-swap). There is no file lock or compare-and-swap: two concurrent callers would each read the same PEND state and the last writer would win. Concurrent upgrades are not prevented; they are tolerated as an acceptable race given that log_feedback is not designed for concurrent use.

## Acceptance (= tests)
- A report with a valid `success_criterion` and `chosen_approach` produces a new `<tr>` row in FEEDBACK.html with the correct date, truncated context, and derived note.
- Appending the same report twice with the same `--run-path` and same `--outcome` exits 3 and does not add a duplicate row.
- Appending the same report twice with the same `--run-path` but a different outcome (e.g., PEND then OK) upgrades the existing row in place and exits 0.
- `--outcome OK` with a report whose `confidence` is below 0.70 exits 1 with an error message, unless `--force-override` is passed.
- `--outcome OVR` without `--override-target` exits 2 with an error message to stderr.
