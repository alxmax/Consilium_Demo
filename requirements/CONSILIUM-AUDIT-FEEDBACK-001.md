---
id: CONSILIUM-AUDIT-FEEDBACK-001
status: deprecated
layer: feature
owner: auto
test_exempt: "dynamic module loading and atomic file I/O — no isolated pure-function surface"
depends_on: [CONSILIUM-UTILS-001, CONSILIUM-PRIORS-001, CONSILIUM-FEEDBACK-001, CONSILIUM-RENDER-FEEDBACK-HTML-001]
risk: 1
---

# audit_feedback

> Finds runs with no FEEDBACK.html row and optionally backfills PEND entries.

## Input
- `.consilium/runs/*.json`: deliberation run files scanned for missing coverage
- `.consilium/FEEDBACK.html`: existing journal read to determine which runs already have rows
- CLI flag `--runs-dir`: override path to runs directory
- CLI flag `--feedback`: override path to FEEDBACK.html
- CLI flag `--backfill`: when present, appends PEND rows for all missing runs
- CLI flag `--dry-run`: with `--backfill`, prints planned rows without writing
- CLI flag `--check`: corpus-completeness gate; exits 1 if any run lacks a FEEDBACK row (read-only)

## Description
Identifies deliberation run files in `.consilium/runs/` that have no corresponding row in FEEDBACK.html, surfacing gaps that occur when the auto-log step at the end of a session is skipped due to crashes or abrupt termination. In list mode (default) it reports the missing runs without writing anything; with `--backfill` it appends a PEND-outcome row for each missing run using the same entry-building logic as `log_feedback.py`, so the next Step 0 priors check will surface them as stale pendings to be rated. The `--check` flag acts as a CI corpus-completeness gate, returning exit code 1 if any run lacks a feedback row. All backfill writes are performed in a single atomic pass over the accumulated Entry list to avoid O(N^2) read-render-write cycles, and existing rows are never overwritten.

## Output
- stdout: list of missing run filenames with date and chosen fields
- with `--backfill`: atomically updated FEEDBACK.html with new PEND rows appended; updated fingerprint sidecar map
- with `--dry-run`: printed plan of rows that would be appended, no file writes
- with `--check`: exit code 1 if any missing rows found, exit code 0 if none
- exit code 0 on success; exit code 1 on `--check` failure

## WHAT — Verify intent (open questions for the human)
- The 'backfill' PEND row uses 'the same entry-building logic as `log_feedback.py`' — does that mean it also enforces the 0.70 confidence gate, or is that gate bypassed for backfill rows since no outcome is being claimed?
- When multiple missing runs are backfilled in one pass, are they appended in a defined order (e.g., by run timestamp, alphabetically by filename), or is the order undefined?
- What happens when `--check` is run and FEEDBACK.html does not exist at all — does it treat every run as missing and exit 1, or exit 0 because there are no rows to compare against?

## Acceptance (= tests)
- Given a runs/ directory containing a .json file with no matching row in FEEDBACK.html, the script without flags reports exactly that file and exits 0.
- Given the same setup with `--backfill`, the script appends exactly one PEND row to FEEDBACK.html with a `; backfilled` suffix on the note, and the run is no longer reported as missing on subsequent invocations.
- Given `--backfill --dry-run`, no file is written and the stdout plan lists each row that would be appended.
- Given `--check` with at least one missing run, the script exits with code 1 and prints a FAIL message to stderr.
- Given a run that already has a FEEDBACK.html row, `--backfill` does not append a duplicate row for that run.
