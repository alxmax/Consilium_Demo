# Consilium Refactor — Design Spec

**Date:** 2026-05-13  
**Branch:** `fix/script-bugs`  
**Scope:** Bugfix + deduplication + input validation + architecture doc update + worktree cleanup

---

## Goal

Fix 4 critical bugs and 5 issues discovered during audit, extract shared utilities into `scripts/utils.py`, add per-script input validation, update `docs/architecture.html` to reflect the new layer, and clean up stale git worktrees.

---

## 1. Bugfixes (Critical)

### B1 — `priors.py:~134` — Wrong slice direction
`entries[:n]` returns the **oldest** N entries. Fix: `entries[-n:]`.  
Affects: Step 0 priors — orchestrator reads stale feedback as "recent".

### B2 — `feedback.py:~151` — Same slice bug
`entries[:args.recent]` → `entries[-args.recent:]`. Same impact on `feedback.py --recent N`.

### B3 — `dialectic_merge.py:~185-195` — New Pass-2 candidates get `control=0.0`
When Pass-2 Generator introduces a candidate not present in Pass-1, the dissent-fallback
path does `p1_ctrl_by_id.get(cid, {})` → empty dict → `_voice_score_from_verdict({})` → 0.0.
Fix: when a candidate is new in Pass-2 (not in Pass-1 at all), use Pass-2 Control/Conservator
data directly instead of falling back to empty Pass-1 data.

### B4 — `log_feedback.py:~236` — Cryptic crash on empty stdin
`json.load(sys.stdin)` with no stdin produces "Expecting value: line 1 column 1 (char 0)".
Fix: replace with `load_json_stdin()` from utils, which emits a clear usage message.

---

## 2. Issues (Logic / Robustness)

### I1 — `aggregator.py` — `weighted` scheme inverts Conservator silently
The `weighted` scheme treats Conservator as utility (higher = better), but Conservator emits
risk (higher = worse). Fix: add a `warnings.warn()` when `--scheme weighted` is selected,
or flip conservator score internally with a comment. Prefer the warn approach to preserve
backward-compat.

### I2 — `aggregator.py` — `veto_threshold` not validated
`veto_threshold=2.0` makes veto inert with no warning. Fix: assert `0.0 <= veto_threshold <= 1.0`
at entry point, exit 1 with message on violation.

### I3 — `confidence.py` — No validation that candidate has `scores`
`_utility_vec()` crashes with `KeyError: 'scores'` if a candidate lacks the field.
Fix: `validate_input()` checks each candidate has `scores` with keys `generator`, `control`,
`conservator` before any computation.

### I4 — `build_report.py` — Error handling continues after error
Line ~210 prints error to stderr but continues, causing `AttributeError` on next `.get()`.
Fix: exit 1 immediately after printing the error.

### I5 — `render_feedback_html.py` — `OSError` not caught on run-file read
`Path(...).read_text()` can throw `OSError` if file is deleted between path lookup and read.
Fix: wrap in try/except OSError, fall back to stub render.

---

## 3. `scripts/utils.py` — New Shared Module

Exports three functions. All stdlib-only. Scripts remain stand-alone executables.

```python
def force_utf8_streams() -> None:
    """Reconfigure stdin/stdout/stderr to UTF-8 (Windows cp1252 fix)."""

def load_json_stdin(script_name: str) -> dict:
    """Read + parse JSON from stdin. On EOF or parse error, print usage hint and sys.exit(2).
    
    Usage hint format:
      "{script_name}: no input — pipe a report: cat runs/<file>.json | python scripts/{script_name}.py"
    """

def validate_keys(data: dict, required: list[str], context: str) -> None:
    """Assert data contains all required keys. On missing key, print which key is missing
    with context label and sys.exit(1)."""
```

**Import pattern** (replaces local `_force_utf8_streams` in each script):
```python
from utils import force_utf8_streams, load_json_stdin, validate_keys
```

Scripts that get the import: `confidence.py`, `priors.py`, `feedback.py`, `log_feedback.py`,
`build_report.py`, `dialectic_merge.py`, `aggregator.py`, `validate_report.py`,
`render_feedback_html.py`, `usage.py`.

---

## 4. Per-Script `validate_input()` Functions

Added to scripts that read structured JSON input. Runs before any business logic.

| Script | What it validates |
|---|---|
| `confidence.py` | Top-level has `candidates` (list) and `chosen` (str/null); each candidate has `scores.generator`, `scores.control`, `scores.conservator` |
| `build_report.py` | Bundle has `success_criterion`, `verification`, `generator.candidates`, `control.verdicts`, `conservator.scores` |
| `dialectic_merge.py` | Input has `pass1` with `generator`, `control`, `conservator` sub-keys |
| `log_feedback.py` | Report has `success_criterion` and `chosen_approach` (already done via exit 1, but improve message) |
| `priors.py` | No JSON stdin — validates `FEEDBACK.html` path exists before parsing |
| `feedback.py` | No JSON stdin — same path check |

---

## 5. `docs/architecture.html` Updates

**Tab: Architecture** — add a "Shared Utilities" card in the Scripts section:
- Card title: `utils.py`
- Content: table of 3 exported functions with one-line descriptions
- Visual: positioned below the scripts grid, labeled "imported by all scripts"

**Tab: Flow** — Step 0 and Step 6 already reference scripts by name. Add a small inline note:
*"Input validat la intrare prin `validate_input()` — mesaj clar la câmp lipsă."*

**Tab: Modes** — no changes.

---

## 6. Worktree Cleanup

```bash
git worktree prune
```
Then manually remove any directories under `.claude/worktrees/` that `prune` leaves behind
(orphaned directories without a registered worktree). Verify with `git worktree list`.

---

## 7. Eval Harness

After all script changes, run:
```bash
python scripts/run_evals.py
```
All 17+ scenarios must pass (exit 0) before commit. If any fail, fix before proceeding.

---

## Success Criteria

- `python scripts/run_evals.py` exits 0
- `priors.py` returns the 10 **most recent** entries (newest first), not oldest
- `feedback.py --recent 10` returns the 10 most recent entries
- `log_feedback.py` called without stdin prints a clear usage message (exit 2)
- `confidence.py` called with a candidate missing `scores` prints which field is missing (exit 1)
- `dialectic_merge.py` with a new Pass-2 candidate uses Pass-2 Control/Conservator data (not 0.0)
- `git worktree list` shows only active worktrees
- `docs/architecture.html` shows `utils.py` in the Architecture tab

---

## Out of Scope

- Centralizing schemas into a `schemas.py` (Approach C — deferred)
- Rewriting `_force_utf8_streams` across scripts not in the bug list (low value, done passively via import)
- Changes to `prompts/*.md` or `SKILL.md`
- New features
