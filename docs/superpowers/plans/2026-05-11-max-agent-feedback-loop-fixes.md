# max-agent Feedback Loop Fixes — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the feedback-loop drift in the max-agent skill — defensive `log_feedback.py` against non-canonical reports, strict `validate_report.py` checks that catch the drift at source, active-learning outcome capture at Step 6 with confidence-gated prompting, and retrospective PEND-closure signal at Step 0.

**Architecture:** Three coordinated changes to existing scripts plus workflow edits in `SKILL.md`. No new files. Component B (strict validator) lands first so future drift can't silently ship. Component A (defensive log_feedback) handles legacy reports already on disk. Component C (workflow + retrospective signal) is the user-facing behavior change.

**Tech Stack:** Python 3 stdlib only (`argparse`, `json`, `pathlib`, `datetime`, `re`). Testing via `scripts/run_evals.py` over `evals/scenarios.json` for deterministic scripts; CLI smoke tests for `log_feedback.py` and `priors.py` (no existing eval scenarios). Markdown for `SKILL.md` workflow doc.

**Spec:** `docs/superpowers/specs/2026-05-11-max-agent-feedback-loop-fixes-design.md`

---

## File Structure

**Modified files:**
- `scripts/validate_report.py` — adds `_validate_deliberation_log()` and `_validate_telemetry_required()`; wires both into `validate()`.
- `scripts/log_feedback.py` — defensive coercion on `aggregate_result`; new CLI flags `--outcome`, `--override-target`, `--user-note`; `build_line()` accepts new params.
- `scripts/priors.py` — adds `STALE_PEND_DAYS` constant, `find_stale_pendings()` helper; `build_priors()` emits new `stale_pendings` field.
- `SKILL.md` — Step 6 "Acțiuni finale" item 2 replaced with confidence-gated outcome flow; Step 0 priors paragraph appends retrospective close instruction.
- `evals/scenarios.json` — 3 existing scenarios updated to canonical shape; 4 new scenarios added for the strict validator.

**Not touched:** `build_report.py` (already produces canonical shape), `aggregator.py`, `confidence.py`, `feedback.py`, `personalities.py`. Component boundaries are tight by design.

---

## Task 1: Component B — Strict validator (`validate_report.py`)

**Why first:** locks the canonical report shape at the validation gate. Once shipped, any further drift in manual report assembly fails at Step 6 instead of corrupting downstream logging.

**Files:**
- Modify: `evals/scenarios.json` (update 3 existing entries, append 4 new)
- Modify: `scripts/validate_report.py:38-105` (add 2 helpers, extend `validate()`)
- Test: `python scripts/run_evals.py --filter validate_report`

### Subtask 1.1 — Update existing eval fixtures to canonical shape

- [ ] **Step 1: Update scenario `validate_report/full report with required fields passes` (index 8)**

The current minimal fixture lacks `deliberation_log` and `telemetry` — after the new validator lands it would start failing. Update it to the canonical shape so it remains a passing test of "valid non-skipped report".

Replace the `stdin_json` for that scenario in `evals/scenarios.json` with:

```json
{
  "success_criterion": "x is y",
  "verification": "run pytest",
  "chosen_approach": "approach_a",
  "deliberation_log": [
    {"step": "generator",   "candidates": []},
    {"step": "control",     "verdicts":   []},
    {"step": "conservator", "scores":     []},
    {"step": "aggregate",   "scheme": "majority", "result": {"chosen": "approach_a"}}
  ],
  "telemetry": {"mode": "sequential"}
}
```

- [ ] **Step 2: Update scenario `validate_report/telemetry with malformed token count fails` (index 12)**

The current fixture has telemetry but no `mode`. After the new validator, it would fail twice: once for malformed `tokens_in` (current intent) and once for missing `mode`. Keep the original intent — add `mode` and `deliberation_log` so only the `tokens_in` check trips.

Replace the `stdin_json` for that scenario with:

```json
{
  "success_criterion": "x",
  "verification": "y",
  "chosen_approach": "approach_a",
  "deliberation_log": [
    {"step": "generator",   "candidates": []},
    {"step": "control",     "verdicts":   []},
    {"step": "conservator", "scores":     []},
    {"step": "aggregate",   "scheme": "majority", "result": {"chosen": "approach_a"}}
  ],
  "telemetry": {
    "mode": "parallel",
    "voices": {"generator": {"tokens_in": -5}}
  }
}
```

The existing `expect_exit: 1` and `expect_stderr_contains: ["tokens_in"]` stay unchanged.

- [ ] **Step 3: Update scenario `validate_report/well-formed telemetry passes` (index 13)**

Same reason as 1.1 — needs canonical `deliberation_log`.

Replace the `stdin_json` for that scenario with:

```json
{
  "success_criterion": "x",
  "verification": "y",
  "chosen_approach": "approach_a",
  "deliberation_log": [
    {"step": "generator",   "candidates": []},
    {"step": "control",     "verdicts":   []},
    {"step": "conservator", "scores":     []},
    {"step": "aggregate",   "scheme": "majority", "result": {"chosen": "approach_a"}}
  ],
  "telemetry": {
    "mode": "parallel",
    "passes": 1,
    "voices": {
      "generator":   {"tokens_in": 1200, "tokens_out": 400, "latency_ms": 3500},
      "control":     {"tokens_in":  800, "tokens_out": 200, "latency_ms": 2100},
      "conservator": {"tokens_in":  900, "tokens_out": 180, "latency_ms": 1800}
    }
  }
}
```

`expect_exit: 0` stays.

- [ ] **Step 4: Run evals to verify the 3 updated scenarios still pass under the current validator**

Run: `python scripts/run_evals.py --filter validate_report`
Expected: all `validate_report/*` scenarios pass (the new fields are extra; current validator ignores them). All 7 existing `validate_report` scenarios pass.

If any fails, the fixture change broke something — re-check that `expect_stdout_subset` / `expect_stderr_contains` were not accidentally changed.

### Subtask 1.2 — Add new eval scenarios for the strict validator

These scenarios target behavior the new validator will enforce. They are expected to **fail right now** (current validator returns exit 0 for them) — we add them first so the test→implement→pass loop drives Subtask 1.3.

- [ ] **Step 1: Append "missing deliberation_log fails" scenario**

Append to `evals/scenarios.json` (inside the top-level array):

```json
{
  "name": "validate_report/non-skipped missing deliberation_log fails",
  "tool": "scripts/validate_report.py",
  "stdin_json": {
    "success_criterion": "x",
    "verification": "y",
    "chosen_approach": "approach_a",
    "telemetry": {"mode": "sequential"}
  },
  "expect_exit": 1,
  "expect_stderr_contains": ["deliberation_log"]
}
```

- [ ] **Step 2: Append "aggregate.result as string fails" scenario**

Append:

```json
{
  "name": "validate_report/deliberation_log aggregate result as string fails",
  "tool": "scripts/validate_report.py",
  "stdin_json": {
    "success_criterion": "x",
    "verification": "y",
    "chosen_approach": "approach_a",
    "deliberation_log": [
      {"step": "generator",   "candidates": []},
      {"step": "control",     "verdicts":   []},
      {"step": "conservator", "scores":     []},
      {"step": "aggregate",   "scheme": "majority", "result": "narrative string instead of dict"}
    ],
    "telemetry": {"mode": "sequential"}
  },
  "expect_exit": 1,
  "expect_stderr_contains": ["result must be an object"]
}
```

- [ ] **Step 3: Append "non-skipped missing telemetry fails" scenario**

Append:

```json
{
  "name": "validate_report/non-skipped missing telemetry fails",
  "tool": "scripts/validate_report.py",
  "stdin_json": {
    "success_criterion": "x",
    "verification": "y",
    "chosen_approach": "approach_a",
    "deliberation_log": [
      {"step": "generator",   "candidates": []},
      {"step": "control",     "verdicts":   []},
      {"step": "conservator", "scores":     []},
      {"step": "aggregate",   "scheme": "majority", "result": {"chosen": "approach_a"}}
    ]
  },
  "expect_exit": 1,
  "expect_stderr_contains": ["telemetry block required"]
}
```

- [ ] **Step 4: Append "telemetry without mode fails" scenario**

Append:

```json
{
  "name": "validate_report/telemetry without mode fails",
  "tool": "scripts/validate_report.py",
  "stdin_json": {
    "success_criterion": "x",
    "verification": "y",
    "chosen_approach": "approach_a",
    "deliberation_log": [
      {"step": "generator",   "candidates": []},
      {"step": "control",     "verdicts":   []},
      {"step": "conservator", "scores":     []},
      {"step": "aggregate",   "scheme": "majority", "result": {"chosen": "approach_a"}}
    ],
    "telemetry": {"passes": 1}
  },
  "expect_exit": 1,
  "expect_stderr_contains": ["telemetry.mode required"]
}
```

- [ ] **Step 5: Run evals and confirm the 4 new scenarios fail**

Run: `python scripts/run_evals.py --filter validate_report`
Expected: the 7 existing `validate_report` scenarios pass; the 4 new scenarios FAIL (because the current `validate_report.py` doesn't have the new checks — it returns exit 0, which doesn't match `expect_exit: 1` or the `expect_stderr_contains` substrings).

The test runner will print which scenarios failed; if any of the 7 existing ones fail here, Subtask 1.1 has a regression — fix it before continuing.

### Subtask 1.3 — Implement the new validators

- [ ] **Step 1: Add `_validate_deliberation_log` helper**

Open `scripts/validate_report.py`. After `_validate_telemetry` (ending at line 77) and before `def validate(report)`, insert:

```python
def _validate_deliberation_log(log: object, skipped: bool) -> list[str]:
    if skipped:
        return []
    if not isinstance(log, list):
        return ["deliberation_log must be an array"]
    aggregate_step = next(
        (s for s in log if isinstance(s, dict) and s.get("step") == "aggregate"),
        None,
    )
    if aggregate_step is None:
        return ["deliberation_log missing 'aggregate' step"]
    result = aggregate_step.get("result")
    if not isinstance(result, dict):
        return [
            f"deliberation_log[aggregate].result must be an object "
            f"(got {type(result).__name__}) — did you bypass build_report.py?"
        ]
    return []


def _validate_telemetry_required(report: dict) -> list[str]:
    if report.get("skipped") is True:
        return []
    telemetry = report.get("telemetry")
    if not isinstance(telemetry, dict):
        return ["telemetry block required for non-skipped reports"]
    mode = telemetry.get("mode")
    if not isinstance(mode, str) or not mode.strip():
        return ["telemetry.mode required (non-empty string) for non-skipped reports"]
    return []
```

No comments beyond what's there. The diagnostic message ("did you bypass build_report.py?") is intentional.

- [ ] **Step 2: Wire the new validators into `validate()`**

In the same file, after the existing `if "telemetry" in report:` block in `validate()` (line ~103), append:

```python
    problems.extend(_validate_deliberation_log(
        report.get("deliberation_log"),
        report.get("skipped") is True,
    ))
    problems.extend(_validate_telemetry_required(report))
```

- [ ] **Step 3: Run evals and confirm all pass**

Run: `python scripts/run_evals.py --filter validate_report`
Expected: all 11 `validate_report` scenarios (7 existing + 4 new) pass with exit 0.

If any fail, read the runner's stderr — most likely cause is a stderr substring mismatch. Adjust either the substring in the scenario or the error message text to match (whichever is more readable).

- [ ] **Step 4: Run the full eval suite to confirm no collateral damage**

Run: `python scripts/run_evals.py`
Expected: all 30 scenarios pass (26 original + 4 new).

Pay attention to `build_report/output validates cleanly via validate_report contract` (index 20) — this scenario pipes `build_report.py` output into `validate_report.py` and expects it to validate. Since `build_report.py` already emits canonical shape (with `deliberation_log[aggregate].result` as the full aggregate dict, and `telemetry` only when present in the bundle), this should still pass — but the test fixture for #20 doesn't include `telemetry` in the bundle, so `build_report.py` won't emit it either, and the resulting report will lack `telemetry.mode`.

If #20 fails: open `evals/scenarios.json`, find scenario #20, and add `"telemetry": {"mode": "sequential"}` to its `stdin_json` (alongside `success_criterion`, `verification`, etc.) so `build_report.py` includes it in the emitted report.

- [ ] **Step 5: Commit**

```bash
git add scripts/validate_report.py evals/scenarios.json
git commit -m "feat(validate_report): require deliberation_log shape and telemetry.mode

Adds _validate_deliberation_log and _validate_telemetry_required.
Catches the report-shape drift that allowed 6/8 of today's runs
to ship with aggregate.result as a narrative string instead of
the canonical dict. Skipped reports continue to short-circuit
both new checks. Updates 3 existing eval fixtures to canonical
shape and adds 4 new fail scenarios."
```

---

## Task 2: Component A — Defensive log_feedback + outcome flag

**Files:**
- Modify: `scripts/log_feedback.py` (defensive line in `derive_note`, parameterize `build_line`, new CLI args)
- Test: manual CLI smoke tests against fixture report files (no existing eval scenarios for `log_feedback.py`; CLI is too I/O-heavy to fit the deterministic eval pattern cleanly)

### Subtask 2.1 — Reproduce the crash on a manual-assembled report

- [ ] **Step 1: Build a fixture report file with `result` as a string**

Create `/tmp/legacy_report.json` (Windows: `$env:TEMP\legacy_report.json`) with this content. The deliberation_log mimics what manual assembly produces:

```json
{
  "success_criterion": "smoke test legacy shape",
  "verification": "appends a line to a temp FEEDBACK file",
  "chosen_approach": "approach_a",
  "confidence": 0.65,
  "telemetry": {"mode": "sequential"},
  "deliberation_log": [
    {"step": "generator",   "candidates": [{"id": "approach_a"}, {"id": "approach_b"}]},
    {"step": "control",     "verdicts":   []},
    {"step": "conservator", "scores":     []},
    {"step": "aggregate",   "scheme": "conservative_override", "result": "narrative override summary"}
  ]
}
```

- [ ] **Step 2: Run `log_feedback.py --dry-run` against it and capture the crash**

Run (PowerShell):
```powershell
Get-Content $env:TEMP\legacy_report.json -Raw | python scripts/log_feedback.py --dry-run
```
Or (bash):
```bash
cat /tmp/legacy_report.json | python scripts/log_feedback.py --dry-run
```

Expected: traceback ending in `AttributeError: 'str' object has no attribute 'get'` at line 81 (`(aggregate_result.get("retry_suggested") or {}).get("relaxed_threshold")`) or line 87 (`aggregate_result.get("vetoed")`) — depending on which `.get()` runs first for this chosen-non-null path, the crash is on line 87. Exit code non-zero.

This confirms the bug is reproducible. Keep the fixture file for the next step.

### Subtask 2.2 — Apply defensive fix

- [ ] **Step 1: Edit `derive_note` in `scripts/log_feedback.py`**

Find this block (lines 75-77):
```python
    log = report.get("deliberation_log") or []
    aggregate_step = next((s for s in log if isinstance(s, dict) and s.get("step") == "aggregate"), {})
    aggregate_result = aggregate_step.get("result") or {}
```

Replace with:
```python
    log = report.get("deliberation_log") or []
    aggregate_step = next((s for s in log if isinstance(s, dict) and s.get("step") == "aggregate"), {})
    raw_result = aggregate_step.get("result")
    # Manual-assembled runs may put a narrative string in `result` instead of
    # the canonical aggregate dict; coerce to {} so note derivation keeps going.
    aggregate_result = raw_result if isinstance(raw_result, dict) else {}
```

The one-line comment explains *why* (constraint not visible from the code itself: legacy shape drift).

- [ ] **Step 2: Re-run the smoke test from Subtask 2.1**

Run the same command. Expected output (stdout, no traceback):
```
- 2026-05-11 | smoke test legacy shape | approach_a | PEND | 2 cand, 0 vetoed, conf=0.65, mode=sequential
```

Exit code 0. The `0 vetoed` is the expected degradation — we don't know the real veto count from the string; treating result as empty is the documented trade-off.

### Subtask 2.3 — Add outcome flags

- [ ] **Step 1: Add CLI args**

In `scripts/log_feedback.py:main`, find the argparse block (lines 135-138):

```python
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--feedback", default=None, help="path to FEEDBACK.md (default: ./FEEDBACK.md)")
    ap.add_argument("--dry-run", action="store_true", help="print line to stdout, don't write file")
    args = ap.parse_args(argv)
```

Insert three new args before `args = ap.parse_args(argv)`:

```python
    ap.add_argument(
        "--outcome",
        choices=("OK", "BAD", "OVR", "PEND"),
        default="PEND",
        help="outcome to record (default: PEND; set OK/OVR after confidence-gated user prompt)",
    )
    ap.add_argument(
        "--override-target",
        default=None,
        help="alt_id when --outcome=OVR; ignored otherwise",
    )
    ap.add_argument(
        "--user-note",
        default=None,
        help="optional user-supplied note appended to auto-note",
    )
```

- [ ] **Step 2: Parameterize `build_line`**

Find `build_line(report)` (lines 97-113). Replace the entire function with:

```python
def build_line(
    report: dict,
    outcome: str = "PEND",
    override_target: str | None = None,
    user_note: str | None = None,
) -> str:
    sc = report.get("success_criterion")
    if not isinstance(sc, str) or not sc.strip():
        raise ValueError("report missing non-empty success_criterion")

    if "chosen_approach" not in report:
        raise ValueError("report missing chosen_approach")
    chosen = report["chosen_approach"]
    if chosen is None:
        chosen_s = "null"
    elif isinstance(chosen, str) and chosen.strip():
        chosen_s = _clean(chosen)
    else:
        raise ValueError("chosen_approach must be null or a non-empty string")

    auto_note = derive_note(report)
    extras: list[str] = []
    if outcome == "OVR" and override_target:
        extras.append(f"override={_clean(override_target)}")
    if user_note and user_note.strip():
        extras.append(_clean(user_note))
    note = "; ".join([auto_note] + extras) if extras else auto_note

    today = date.today().isoformat()
    return f"- {today} | {truncate(sc, CONTEXT_MAX)} | {chosen_s} | {outcome} | {note}"
```

- [ ] **Step 3: Pass new args into `build_line` call**

Find the call in `main` (line 150):
```python
        line = build_line(report)
```

Replace with:
```python
        line = build_line(
            report,
            outcome=args.outcome,
            override_target=args.override_target,
            user_note=args.user_note,
        )
```

- [ ] **Step 4: Smoke test all 4 outcome paths**

Reuse the fixture `/tmp/legacy_report.json` from Subtask 2.1 (or its Windows equivalent).

Run path 1 — default (PEND, backward compat):
```bash
cat /tmp/legacy_report.json | python scripts/log_feedback.py --dry-run
```
Expected: `- 2026-05-11 | smoke test legacy shape | approach_a | PEND | 2 cand, 0 vetoed, conf=0.65, mode=sequential`

Run path 2 — auto-OK:
```bash
cat /tmp/legacy_report.json | python scripts/log_feedback.py --dry-run --outcome OK
```
Expected: line ending `| approach_a | OK | 2 cand, ...` (only the outcome column changed).

Run path 3 — OVR with target:
```bash
cat /tmp/legacy_report.json | python scripts/log_feedback.py --dry-run --outcome OVR --override-target approach_b
```
Expected: `| approach_a | OVR | 2 cand, 0 vetoed, conf=0.65, mode=sequential; override=approach_b`

Run path 4 — OVR with target + user note:
```bash
cat /tmp/legacy_report.json | python scripts/log_feedback.py --dry-run --outcome OVR --override-target approach_b --user-note "preferred safer rollback"
```
Expected: `| approach_a | OVR | 2 cand, 0 vetoed, conf=0.65, mode=sequential; override=approach_b; preferred safer rollback`

All exit 0. Verify each output line matches expected exactly.

- [ ] **Step 5: Confirm no real FEEDBACK.md write happens during dry-run**

```bash
git status
```
Expected: `FEEDBACK.md` should not show as modified (it's gitignored anyway, but verify the local file's mtime didn't change — `--dry-run` should be side-effect-free).

- [ ] **Step 6: Commit**

```bash
git add scripts/log_feedback.py
git commit -m "feat(log_feedback): defensive on aggregate.result + outcome flags

Coerces aggregate.result to {} when it's a string (legacy manual-
assembled reports). Adds --outcome (OK|BAD|OVR|PEND), --override-
target, --user-note flags. Default behavior unchanged — no flags
emits PEND, preserving backward compat. The new flags let the
agent capture OK auto when confidence >= 0.7 and OVR with target
when the user overrides a low-confidence pick at Step 6."
```

---

## Task 3: Component C.2 — Stale PEND signal in `priors.py`

**Files:**
- Modify: `scripts/priors.py` (add constant, helper, output field)
- Test: manual smoke test with a temp FEEDBACK.md fixture

### Subtask 3.1 — Add `find_stale_pendings`

- [ ] **Step 1: Add imports and constant**

Open `scripts/priors.py`. In the imports block (lines 25-32), the `from collections import Counter` already exists. Add `from datetime import date, timedelta` after `from pathlib import Path`:

```python
from collections import Counter
from datetime import date, timedelta
from pathlib import Path
```

After the `STOPWORDS = {...}` block (line 52), add:

```python
STALE_PEND_DAYS = 7
STALE_PEND_CAP = 5
```

- [ ] **Step 2: Add `find_stale_pendings` function**

After `_top_keywords(...)` (ends line 113) and before `build_priors(...)` (starts line 116), insert:

```python
def find_stale_pendings(entries: list[dict], days_old: int = STALE_PEND_DAYS) -> list[dict]:
    cutoff = (date.today() - timedelta(days=days_old)).isoformat()
    return [
        {"date": e["date"], "context": e["context"], "chosen": e["chosen"]}
        for e in entries
        if e.get("outcome") == "PEND" and e.get("date", "") < cutoff
    ][:STALE_PEND_CAP]
```

Note: `entries` is the full parsed FEEDBACK list (not the truncated `recent` slice). Stale PEND can be older than the recent-window — we want to surface them even if they're past entry 10.

- [ ] **Step 3: Wire into `build_priors`**

In `build_priors` (line 116), find the `entries = parse_feedback(FEEDBACK)` line. After it, the function builds `out` dict and `recent`. After `out["top_note_keywords"] = _top_keywords(recent)` (or wherever the dict construction ends — line 128), but BEFORE the `if include_runs:` block, add a line that adds `stale_pendings` to the output.

The cleanest spot is inside the initial `out` dict construction. Replace:

```python
    out: dict = {
        "source": {
            "feedback_path": str(FEEDBACK.relative_to(ROOT)),
            "feedback_total": len(entries),
            "feedback_window": len(recent),
        },
        "recent": recent,
        "counts": dict(_outcome_counts(recent)),
        **_rates(recent),
        "top_note_keywords": _top_keywords(recent),
    }
```

With:

```python
    out: dict = {
        "source": {
            "feedback_path": str(FEEDBACK.relative_to(ROOT)),
            "feedback_total": len(entries),
            "feedback_window": len(recent),
        },
        "recent": recent,
        "counts": dict(_outcome_counts(recent)),
        **_rates(recent),
        "top_note_keywords": _top_keywords(recent),
        "stale_pendings": find_stale_pendings(entries),
    }
```

### Subtask 3.2 — Smoke test

- [ ] **Step 1: Build a temp FEEDBACK.md with old PEND entries**

Create `/tmp/test_FEEDBACK.md` (or Windows equivalent):

```
# FEEDBACK
#
# data | context | chosen | outcome | note
# outcome: OK | BAD | OVR (override) | PEND (pending)

- 2026-04-01 | very old context A | approach_a | PEND | 3 cand, 0 vetoed
- 2026-04-15 | very old context B | approach_b | PEND | 4 cand, 1 vetoed
- 2026-04-20 | very old context C | approach_c | PEND | 5 cand, 0 vetoed
- 2026-04-25 | very old context D | approach_d | OK | 3 cand, 0 vetoed
- 2026-05-01 | semi-old context E | approach_e | PEND | 4 cand, 1 vetoed
- 2026-05-02 | semi-old context F | approach_f | PEND | 3 cand, 0 vetoed
- 2026-05-03 | semi-old context G | approach_g | PEND | 4 cand, 0 vetoed
- 2026-05-04 | semi-old context H | approach_h | PEND | 3 cand, 0 vetoed
- 2026-05-10 | recent context I | approach_i | PEND | 3 cand, 0 vetoed
- 2026-05-11 | today context J | approach_j | PEND | 3 cand, 0 vetoed
```

(Cutoff with `STALE_PEND_DAYS=7` and today=2026-05-11 is `2026-05-04`. Entries A, B, C are PEND and older — 3 candidates. D is OK so skipped. E, F, G are PEND and older than cutoff `2026-05-04` (strict `<`, so `2026-05-04` itself is NOT older). H is on the cutoff boundary and excluded. I, J are recent — excluded.)

Wait — recompute: cutoff is `(2026-05-11 - 7) == 2026-05-04`. Comparison `e["date"] < cutoff` means strictly less than `"2026-05-04"`. So `"2026-05-04"` is NOT stale (boundary excluded). Stale: A, B, C, E, F, G — that's 6 PEND entries. Cap is 5.

Expected `stale_pendings` output: 5 entries, the first 5 in parse order (which mirrors file order). Since `parse_feedback` reads top-to-bottom and returns in that order, the first 5 stale should be A, B, C, E, F (G is the 6th, dropped by the cap).

- [ ] **Step 2: Run priors.py against the temp fixture**

`priors.py` reads from `FEEDBACK = ROOT / "FEEDBACK.md"` (hardcoded). Temporarily swap by copying the temp file in place — but we don't want to clobber the real one. Use a backup-restore pattern (or copy the fixture to a temp file and use `FEEDBACK` env override).

Actually, `priors.py` doesn't take a `--feedback` CLI arg. Simplest: back up real FEEDBACK.md, copy fixture, run, restore.

```bash
cp FEEDBACK.md /tmp/FEEDBACK.md.bak
cp /tmp/test_FEEDBACK.md FEEDBACK.md
python scripts/priors.py --no-runs > /tmp/priors_out.json
cp /tmp/FEEDBACK.md.bak FEEDBACK.md
```

(Windows PowerShell equivalent: use `Copy-Item` and `$env:TEMP`.)

- [ ] **Step 3: Inspect the output**

```bash
python -c "import json; d=json.load(open('/tmp/priors_out.json')); print(json.dumps(d['stale_pendings'], indent=2))"
```

Expected: array of 5 dicts, ordered A → B → C → E → F. Each entry has `date`, `context`, `chosen` keys. No `outcome`, no `note` (those are filtered out in `find_stale_pendings`).

```json
[
  {"date": "2026-04-01", "context": "very old context A", "chosen": "approach_a"},
  {"date": "2026-04-15", "context": "very old context B", "chosen": "approach_b"},
  {"date": "2026-04-20", "context": "very old context C", "chosen": "approach_c"},
  {"date": "2026-05-01", "context": "semi-old context E", "chosen": "approach_e"},
  {"date": "2026-05-02", "context": "semi-old context F", "chosen": "approach_f"}
]
```

If output differs: check that today's date matches assumption (2026-05-11 per the system context). If the test is run on a different day, the cutoff shifts and the expected set changes — adjust either the test fixture's dates or compute the expected set dynamically.

- [ ] **Step 4: Verify the real FEEDBACK.md was restored**

```bash
head -5 FEEDBACK.md
```

Expected: the original FEEDBACK.md content, not the test fixture. If the restore failed, retrieve from `/tmp/FEEDBACK.md.bak`.

- [ ] **Step 5: Commit**

```bash
git add scripts/priors.py
git commit -m "feat(priors): emit stale_pendings for retrospective close

Adds find_stale_pendings + STALE_PEND_DAYS=7 constant. Surfaces
up to 5 PEND entries from FEEDBACK.md older than 7 days so the
agent at Step 0 can prompt the user to close them before
starting a new deliberation. Cap is intentional — older PEND
beyond 5 has decayed as signal anyway."
```

---

## Task 4: Component C.1 — SKILL.md workflow edits

**Files:**
- Modify: `SKILL.md` (Step 6 outcome paragraph, Step 0 priors paragraph)

### Subtask 4.1 — Step 6 outcome flow

- [ ] **Step 1: Replace the Step 6 outcome paragraph**

Open `SKILL.md`. Find the block starting at line 242 ("**Loghează automat în `FEEDBACK.md`.**"):

```markdown
2. **Loghează automat în `FEEDBACK.md`.** Rulează:
   ```bash
   cat runs/<file>.json | python scripts/log_feedback.py
   ```
   Script-ul derivă linia (`data | context | chosen | PEND | note`) din raport și o appendează (creează FEEDBACK.md cu header dacă lipsește). `note` e auto-extras: `"skipped: <reason>"`, `"all vetoed; relaxed=<X>"`, sau `"<N> cand, <K> vetoed, conf=<X>, mode=<Y>"`. Outcome rămâne `PEND` — user-ul îl actualizează la `OK`/`BAD`/`OVR` ulterior, prin editare manuală a fișierului, când rezultatul e cunoscut. Dacă vrei doar să previzualizezi linia fără să scrii, foloseste `--dry-run`.
```

Replace the entire item 2 with:

```markdown
2. **Loghează automat în `FEEDBACK.md` cu outcome confidence-gated.** La finalul Step 6, citește `confidence` din raport și alege calea:

   - **`confidence >= 0.7`** — pickul are agreement și separation suficient; auto-OK fără să întrebi user-ul:
     ```bash
     cat runs/<file>.json | python scripts/log_feedback.py --outcome OK
     ```

   - **`confidence < 0.7`** — întreabă user-ul: *"Confidence sub prag (`<X>`). Vrei să override-ezi `<chosen>`? Alternative din raport: `<alt_id list>`. Răspunde alt_id, 'no', sau 'skip'."* Apoi:
     - `no` → `python scripts/log_feedback.py --outcome OK`
     - `<alt_id>` → `python scripts/log_feedback.py --outcome OVR --override-target <alt_id>` (cu `--user-note "<motiv>"` opțional)
     - `skip` → `python scripts/log_feedback.py` (PEND, default — user-ul închide manual mai târziu)

   - **`confidence` is null** (toți candidates vetoiți) — `python scripts/log_feedback.py` fără flag. Veto total = no decision = no outcome to rate.

   Pragul `0.7` e o decizie de workflow în acest fișier, nu config în script. Schimbarea pragului = o editare aici. `--dry-run` previzualizează linia fără să scrie, în orice combinație de flag-uri.

   Script-ul derivă coloana note automat: `"skipped: <reason>"`, `"all vetoed; relaxed=<X>"`, sau `"<N> cand, <K> vetoed, conf=<X>, mode=<Y>"`. Când outcome e OVR, se append-ează `; override=<target>` și (opțional) nota user-ului.
```

- [ ] **Step 2: Verify the replacement reads cleanly**

Re-read the surrounding Step 6 section in `SKILL.md` (the "Acțiuni finale" header through end of item 2). Confirm the markdown renders correctly — three nested bullets under "**`confidence < 0.7`**", consistent indentation, no leftover text from the original paragraph.

### Subtask 4.2 — Step 0 priors retrospective note

- [ ] **Step 1: Append retrospective close note after the priors.py paragraph**

Open `SKILL.md`. Find the Step 0 paragraph that ends with "...prompts-urile rămâne autoritative." (around line 42, item 2 of the Bootstrap section).

After that line (end of priors.py instructions), append a new paragraph:

```markdown

Dacă `priors.py` raportează `stale_pendings` non-empty (PEND-uri mai vechi de 7 zile, max 5 entries), oprește **înainte** de Step 1 și întreabă user-ul: *"Ai N entries PEND vechi: [date | chosen] × N. Vrei să le închid acum (OK/BAD/skip per entry) sau să continuăm cu deliberarea nouă?"* Update-ul se face cu `Edit` tool pe `FEEDBACK.md` (înlocuiește literalul `PEND` din linia respectivă cu `OK` sau `BAD`), **nu** prin `log_feedback.py` — acela appendează o linie nouă, ducând la istoric dublu pentru aceeași deliberare. Dacă user-ul răspunde "skip", continuă la Step 1 fără modificări.
```

- [ ] **Step 2: Verify the addition fits the surrounding flow**

Re-read lines ~38-50 of `SKILL.md` (the Bootstrap section). Confirm the new paragraph flows after the priors.py instruction and before the Step 1 heading. No broken markdown, no orphan instructions.

- [ ] **Step 3: Commit**

```bash
git add SKILL.md
git commit -m "docs(SKILL): confidence-gated outcome flow + retrospective close

Step 6: log_feedback.py now driven by confidence threshold (0.7).
High-confidence runs auto-write OK; low-confidence prompts the
user for OVR/no/skip. Threshold lives in SKILL.md (workflow
constant), not in code. Step 0: surface stale_pendings from
priors.py and prompt the user to close them before starting
a new deliberation."
```

---

## Self-Review

After implementing all 4 tasks, run:

```bash
python scripts/run_evals.py
git log --oneline -10
git status
```

Expected:
- `run_evals.py` exits 0 — all 30 scenarios pass.
- 4 new commits visible (one per task) on top of the spec commit (`e1b945b`).
- Working tree clean.

Then validate end-to-end with one synthetic deliberation:

```bash
# Build a canonical bundle, pipe through the full pipeline.
echo '{
  "success_criterion": "end-to-end smoke after fixes",
  "verification": "validate then log",
  "generator":   {"candidates": [{"id": "a", "summary": "a"}, {"id": "b", "summary": "b"}]},
  "control":     {"verdicts":   [{"id": "a", "valid": true, "issues": []}, {"id": "b", "valid": true, "issues": []}]},
  "conservator": {"scores":     [{"id": "a", "risk_score": 0.2}, {"id": "b", "risk_score": 0.3}]},
  "aggregate":   {"scheme": "conservative_override", "chosen": "a"},
  "confidence":  {"confidence": 0.85},
  "telemetry":   {"mode": "sequential"}
}' | python scripts/build_report.py | python scripts/validate_report.py
```

Expected: exit 0, no stderr (validate accepts; build_report emits canonical shape; validate accepts canonical shape).

Then capture outcome auto:

```bash
echo '<same bundle as above>' | python scripts/build_report.py > /tmp/synth.json
cat /tmp/synth.json | python scripts/log_feedback.py --dry-run --outcome OK
```

Expected: a line ending `| a | OK | 2 cand, 0 vetoed, conf=0.85, mode=sequential`.
