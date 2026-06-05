---
milestone: v1.0
id: CONSILIUM-MEMORY-001
status: confirmed
layer: feature
owner: auto
test_exempt: "file I/O and integration layer with trivial pure stubs"
depends_on: [CONSILIUM-FEEDBACK-001, CONSILIUM-UTILS-001]
risk: 1
---

# memory

> Unified read API over Consilium's three memory tiers (short / medium / long).

## Input
- CLI flag `--tier`: one of `short | medium | long | all` (default: `all`)
- CLI flag `--n`: maximum number of entries returned per tier (default: 10)
- CLI flag `--query`: optional substring filter applied to medium (`success_criterion` + `chosen_approach`) and long (`context` + `chosen` + `note`) tiers
- CLI flag `--feedback-file`: optional override path to FEEDBACK.html
- CLI flag `--runs-dir`: optional override path to the `runs/` directory
- `.consilium/runs/*.json`: episodic deliberation records read for the medium tier
- `.consilium/FEEDBACK.html`: aggregated feedback journal read for the long tier

## Description
Provides a unified read API over Consilium's three memory tiers - short (current session, stub only), medium (per-run episodic JSON files in `runs/`), and long (aggregate FEEDBACK.html parsed via `feedback.py`) - through a single CLI and importable surface. It exists so that an orchestrating agent can ask "what does Consilium remember about X" without knowing which tier holds the relevant data; the `--query` flag applies a substring filter uniformly across medium and long tiers. The short tier is represented by a descriptive stub because its content (the deliberation bundle being assembled) is only accessible inside the active agent context window. Confirmed-outcome rows (those carrying `[confirmed]` in their note, written by `mark_outcome.py`) are flagged in long-tier output so callers can apply higher trust weights to them.

## Output
- JSON object emitted to stdout: for a single tier, a dict with `tier`, `entries`, and `total` keys; for `--tier all`, a dict with `short`, `medium`, and `long` sub-objects
- exit code 0 always (no error paths beyond missing files, which return empty entry lists)

## WHAT — Verify intent
- None - all questions resolved.

## Contract (derived from code, 2026-06-04)
- The short tier stub is permanently fixed: `read_short()` is a hardcoded function returning `{"tier": "short", "note": "...", "entries": []}` with no file-based population path. There is no session-file mechanism and no design provision for one.
- Case-insensitivity is guaranteed for both tiers via `_matches(text, q) → q.lower() in text.lower()`. For the long tier the filter searches `context`, `chosen`, **and** `note` (the Description omitted `note`; the code includes it).
- `--n` applies independently per tier. `read_all` passes `n` to both `read_medium` and `read_long` separately, so `--tier all --n N` can return up to `2N` entries (short always returns 0 entries). There is no global cap.

## Acceptance (= tests)
- Running with `--tier medium` returns a JSON object whose `entries` array contains at most `--n` items, each with `run`, `date`, `success_criterion`, `chosen`, and `confidence` fields drawn from `runs/*.json` files.
- Running with `--tier long --query <term>` returns only rows whose `context`, `chosen`, or `note` contains the query term (case-insensitive), and each entry includes a `confirmed` boolean reflecting presence of `[confirmed]` in the note.
- Running with `--tier short` returns a stub dict with `entries: []` and a descriptive `note` explaining session-local scope.
- Running with `--tier all` returns a dict with exactly three keys (`short`, `medium`, `long`), each containing valid tier output.
- Passing `--feedback-file` and `--runs-dir` overrides the default `.consilium/` paths so the script can operate on arbitrary copies of the data.

## Why test_exempt

`memory.py` is a thin integration layer over two data sources already tested elsewhere: the medium tier reads `runs/*.json` files (format tested by `test_build_report.py`), and the long tier delegates to `feedback.py` (format tested by `test_feedback_html.py` and `test_priors.py`). The `read_short()` stub is hardcoded and trivially correct. A unit test for `memory.py` would create a fixture `.consilium/` tree and assert counts — adding test-infrastructure cost without catching bugs that the upstream tests would already surface.
