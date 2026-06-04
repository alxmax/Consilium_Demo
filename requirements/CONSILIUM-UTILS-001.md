---
id: CONSILIUM-UTILS-001
status: confirmed
layer: bus
owner: auto
depends_on: []
risk: 0
---

# utils

> Shared stdlib-only utilities: canonical paths, atomic writes, stdin JSON, headless detection.

## Input
- No CLI input for the module itself; individual functions accept:
  - `load_json_stdin`: reads from stdin
  - `atomic_write_text(path, content)`: file path + string content
  - `issue_penalty(severity)`: issue dict
  - `validate_keys(data, keys)`: data dict + required-keys list
- Environment variable `CLAUDE_HEADLESS` (read by `is_headless`)

## Description
Shared stdlib-only utilities that every other Consilium script imports instead of defining its own copies. It centralises the three canonical filesystem paths (`DATA_DIR`, `RUNS_DIR`, `FEEDBACK_PATH`) so their definitions exist in exactly one place. Beyond path constants, it provides: `force_utf8_streams` (Windows cp1252 safety), `is_headless` (headless-orchestrator detection for Step-0 through Step-7 flow-control), `load_json_stdin` (stdin read + parse with a clear error on empty or malformed input), `atomic_write_text` (crash-safe write via same-filesystem rename + fsync, critical for the FEEDBACK journal), `issue_penalty` (severity -> float score penalty lookup for Control issues), and `validate_keys` (dict schema assertion). The module exists to eliminate copy-paste divergence across scripts and to give each script a clean, importable API surface.

## Output
- No files written or stdout produced by the module itself; side effects are produced by its callers
- `atomic_write_text` writes atomically to the caller-supplied path using a sibling `.tmp` file; a read-only parent directory raises `OSError` (propagates to caller); the temp file is always deleted on any error, so no stale `.tmp` accumulates across crashes
- `load_json_stdin` exits with code 2 on empty stdin or JSON parse failure
- `validate_keys` raises `ValueError` on schema violation; callers map that to exit 1 or 2

## WHAT — Verify intent (open questions for the human)
- None - all questions resolved.

## Acceptance (= tests)
- `DATA_DIR`, `RUNS_DIR`, and `FEEDBACK_PATH` resolve to `.consilium/`, `.consilium/runs/`, and `.consilium/FEEDBACK.html` respectively, relative to the repo root; the repo root is derived from `Path(__file__).resolve().parent.parent` (two levels above `scripts/utils.py`), so paths are CWD-independent and never break silently when a script is invoked from outside the repo.
- `atomic_write_text` leaves the original file intact when a write is interrupted mid-way (no truncated or stale `.tmp` files persist on error).
- `is_headless` returns `True` only when `CLAUDE_HEADLESS` equals the string `'1'`; any other value including `'true'`, `'0'`, or empty returns `False`.
- `load_json_stdin` prints a usage hint to stderr and exits 2 on empty stdin; exits 2 with an error message on invalid JSON.
- `issue_penalty` returns `0.05` for severity `low`, `0.15` for `medium` or missing severity, and `0.30` for `high`.
