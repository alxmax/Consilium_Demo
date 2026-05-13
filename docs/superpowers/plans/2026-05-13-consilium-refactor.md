# Consilium Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix 4 critical bugs + 5 issues, extract shared utilities into `scripts/utils.py`, add per-script input validation, update `docs/architecture.html`, and clean up stale worktrees.

**Architecture:** New `scripts/utils.py` centralizes `force_utf8_streams`, `load_json_stdin`, and `validate_keys` — all stdlib, imported by existing scripts which remain stand-alone executables. Each affected script gains a `validate_input()` guard at entry. Bug fixes are surgical, one script at a time.

**Tech Stack:** Python 3.11+ stdlib only, no new dependencies.

---

## File Map

| File | Action | What changes |
|---|---|---|
| `scripts/utils.py` | **CREATE** | `force_utf8_streams`, `load_json_stdin`, `validate_keys` |
| `scripts/priors.py` | modify | fix `entries[:n]` → `entries[-n:]` (B1) |
| `scripts/feedback.py` | modify | fix `entries[:args.recent]` → `entries[-args.recent:]` (B2) |
| `scripts/dialectic_merge.py` | modify | fix Pass-2 new candidates get `control=0.0` (B3); import from utils |
| `scripts/log_feedback.py` | modify | improve stdin error message (B4); import from utils |
| `scripts/aggregator.py` | modify | warn on `weighted` scheme (I1); validate `veto_threshold` (I2) |
| `scripts/confidence.py` | modify | `validate_input()` before logic (I3); import from utils |
| `scripts/build_report.py` | modify | exit immediately after bundle error (I4); import from utils |
| `scripts/render_feedback_html.py` | modify | catch `OSError` on run-file read (I5) |
| `scripts/strip_context.py` | modify | replace local `_force_utf8_streams` with import from utils |
| `scripts/validate_report.py` | modify | replace local `_force_utf8_streams` with import from utils |
| `docs/architecture.html` | modify | add `utils.py` card in Architecture tab; validation note in Flow tab |

---

## Task 1: Create `scripts/utils.py`

**Files:**
- Create: `scripts/utils.py`

- [ ] **Step 1: Write the file**

```python
"""Shared utilities for Consilium scripts.

All functions are stdlib-only. Scripts import from this module instead of
defining their own copies. Each script remains a stand-alone executable.
"""
from __future__ import annotations

import json
import sys
from typing import Any


def force_utf8_streams() -> None:
    """Reconfigure stdin/stdout/stderr to UTF-8.

    Windows default encoding is cp1252; piping UTF-8 JSON through it
    mangles non-ASCII characters (ț, ș, ă) before any script sees them.
    """
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(encoding="utf-8")


def load_json_stdin(script_name: str) -> Any:
    """Read and parse JSON from stdin.

    On empty stdin or parse error, prints a clear usage hint and exits 2.
    Callers treat the return value as already-validated JSON (dict or list).

    Usage hint format:
        "<script_name>: no input — pipe a report file, e.g.:
         cat runs/<file>.json | python scripts/<script_name>"
    """
    raw = sys.stdin.read()
    if not raw.strip():
        print(
            f"{script_name}: no input — pipe a report file, e.g.:\n"
            f"  cat runs/<file>.json | python scripts/{script_name}",
            file=sys.stderr,
        )
        sys.exit(2)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"{script_name}: invalid JSON — {exc}", file=sys.stderr)
        sys.exit(2)


def validate_keys(data: dict, required: list[str], context: str) -> None:
    """Assert that *data* contains all keys in *required*.

    On missing key, prints which key is missing with the *context* label
    and exits 1. Intended for use in per-script validate_input() guards.

    Example:
        validate_keys(bundle, ["success_criterion", "generator"], "bundle")
    """
    for key in required:
        if key not in data:
            print(
                f"{context}: missing required field '{key}'",
                file=sys.stderr,
            )
            sys.exit(1)
```

- [ ] **Step 2: Verify import works**

```bash
cd scripts && python -c "from utils import force_utf8_streams, load_json_stdin, validate_keys; print('OK')"
```
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add scripts/utils.py
git commit -m "feat(scripts): add utils.py with force_utf8_streams, load_json_stdin, validate_keys"
```

---

## Task 2: Fix B1 + B2 — Wrong slice direction (`priors.py`, `feedback.py`)

**Files:**
- Modify: `scripts/priors.py:134`
- Modify: `scripts/feedback.py:151`

- [ ] **Step 1: Verify the bug in `priors.py`**

```bash
python -c "
import sys; sys.path.insert(0, 'scripts')
from priors import build_priors
p = build_priors(n=3)
dates = [e['date'] for e in p['recent']]
print('dates:', dates)
# Bug: dates are ASCENDING (oldest first). Fix: should be DESCENDING (newest first).
"
```
Expected (buggy): oldest dates first.

- [ ] **Step 2: Fix `priors.py`**

In `scripts/priors.py`, find line ~134:
```python
    recent = entries[:n]
```
Replace with:
```python
    recent = entries[-n:]
```

- [ ] **Step 3: Fix `feedback.py`**

In `scripts/feedback.py`, find line ~151:
```python
        entries = entries[: args.recent]
```
Replace with:
```python
        entries = entries[-args.recent :]
```

- [ ] **Step 4: Verify fix**

```bash
python -c "
import sys; sys.path.insert(0, 'scripts')
from priors import build_priors
p = build_priors(n=3)
dates = [e['date'] for e in p['recent']]
print('dates:', dates)
# Fixed: dates should be DESCENDING (most recent first or equal).
"
```
Expected: dates are the most recent 3 entries (not the oldest 3).

- [ ] **Step 5: Commit**

```bash
git add scripts/priors.py scripts/feedback.py
git commit -m "fix(scripts): priors + feedback return newest N entries, not oldest"
```

---

## Task 3: Fix B3 — `dialectic_merge.py` new Pass-2 candidates get `control=0.0`

**Files:**
- Modify: `scripts/dialectic_merge.py:184-197`

**Root cause:** When Pass-2 Generator introduces a candidate not in Pass-1, the dissent-fallback
path does `p1_ctrl_by_id.get(cid, {})` → `{}` → score 0.0. Fix: if the candidate is new in
Pass-2 (not in Pass-1 generator candidates at all), always use Pass-2 voice data directly.

- [ ] **Step 1: Verify the bug**

```bash
python -c "
import json, sys
sys.path.insert(0, 'scripts')
from dialectic_merge import merge

payload = {
  'pass1': {
    'generator': {'candidates': [{'id': 'do_nothing', 'summary': 'baseline', 'sketch': '', 'rationale': ''}]},
    'control': {'verdicts': [{'id': 'do_nothing', 'valid': False, 'issues': [], 'tests_to_write': []}]},
    'conservator': {'scores': [{'id': 'do_nothing', 'risk_score': 0.0, 'factors': {}, 'rollback_recipe': []}]}
  },
  'pass2': {
    'generator': {'candidates': [
      {'id': 'do_nothing', 'summary': 'baseline', 'sketch': '', 'rationale': ''},
      {'id': 'new_candidate', 'summary': 'new in pass2', 'sketch': '', 'rationale': ''}
    ]},
    'control': {'verdicts': [
      {'id': 'do_nothing', 'valid': False, 'issues': [], 'tests_to_write': []},
      {'id': 'new_candidate', 'valid': True, 'issues': [], 'tests_to_write': []}
    ]},
    'conservator': {'scores': [
      {'id': 'do_nothing', 'risk_score': 0.0, 'factors': {}, 'rollback_recipe': []},
      {'id': 'new_candidate', 'risk_score': 0.25, 'factors': {}, 'rollback_recipe': []}
    ]}
  }
}
result = merge(payload)
for c in result['candidates']:
    print(c['id'], c['scores'])
# Bug: new_candidate should have control > 0 (valid=True) but shows control=0.0
"
```
Expected (buggy): `new_candidate {'generator': 1.0, 'control': 0.0, 'conservator': 0.25}`

- [ ] **Step 2: Apply the fix**

In `scripts/dialectic_merge.py`, find lines 183-197 (the `for cand in gen_candidates:` loop body):

```python
        # Use pass1 data for voices where this candidate had a dissent fallback
        gen_cand = p1_gen_by_id.get(cid, cand) if cid in dissent_fallbacks.get("generator", []) else cand
        verdict = p1_ctrl_by_id.get(cid, {}) if cid in dissent_fallbacks.get("control", []) else ctrl_verdicts.get(cid, {})
        risk_entry = p1_cons_by_id.get(cid, {}) if cid in dissent_fallbacks.get("conservator", []) else cons_scores.get(cid, {})
```

Replace with:

```python
        # Candidates new in Pass-2 (not in Pass-1 at all) must never fall back to
        # empty Pass-1 data — that would produce a 0.0 control score for a valid
        # candidate. Always use Pass-2 voice data for genuinely new candidates.
        is_new_in_pass2 = cid not in p1_gen_by_id

        gen_cand = (
            cand if is_new_in_pass2
            else (p1_gen_by_id.get(cid, cand) if cid in dissent_fallbacks.get("generator", []) else cand)
        )
        verdict = (
            ctrl_verdicts.get(cid, {}) if is_new_in_pass2
            else (p1_ctrl_by_id.get(cid, {}) if cid in dissent_fallbacks.get("control", []) else ctrl_verdicts.get(cid, {}))
        )
        risk_entry = (
            cons_scores.get(cid, {}) if is_new_in_pass2
            else (p1_cons_by_id.get(cid, {}) if cid in dissent_fallbacks.get("conservator", []) else cons_scores.get(cid, {}))
        )
```

- [ ] **Step 3: Verify fix**

Re-run the same Python snippet from Step 1.
Expected (fixed): `new_candidate {'generator': 1.0, 'control': 0.85, 'conservator': 0.25}`
(`valid: true, no issues` → `1.0 - 0.15*0 = 1.0`; wait, actually `valid: true` with 0 issues = `max(0.3, 1.0 - 0.15*0)` = 1.0, but let me double-check: `_voice_score_from_verdict({'valid': True, 'issues': []})` = `max(0.3, 1.0 - 0) = 1.0`)

Expected (fixed): `new_candidate {'generator': 1.0, 'control': 1.0, 'conservator': 0.25}`

- [ ] **Step 4: Run evals**

```bash
python scripts/run_evals.py
```
Expected: all pass (exit 0).

- [ ] **Step 5: Commit**

```bash
git add scripts/dialectic_merge.py
git commit -m "fix(dialectic_merge): new Pass-2 candidates use Pass-2 voice data, not empty fallback"
```

---

## Task 4: Fix B4 — `log_feedback.py` cryptic stdin error

**Files:**
- Modify: `scripts/log_feedback.py`

- [ ] **Step 1: Verify the bug**

```bash
python scripts/log_feedback.py
```
Expected (buggy): `invalid JSON: Expecting value: line 1 column 1 (char 0)` — no hint on how to use the script.

- [ ] **Step 2: Replace stdin reading with `load_json_stdin` from utils**

In `scripts/log_feedback.py`, find the existing import block at the top and add:
```python
from utils import force_utf8_streams, load_json_stdin
```

Find the `_force_utf8_streams` function definition and **delete it entirely** (it's now in utils).

Find the `main` function's stdin reading (lines ~235-242):
```python
    try:
        report = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"invalid JSON: {exc}", file=sys.stderr)
        return 2
    if not isinstance(report, dict):
        print("report must be a JSON object", file=sys.stderr)
        return 2
```

Replace with:
```python
    report = load_json_stdin("log_feedback.py")
    if not isinstance(report, dict):
        print("log_feedback.py: report must be a JSON object", file=sys.stderr)
        return 2
```

Find the `_force_utf8_streams()` call in `main` and replace with `force_utf8_streams()`.

- [ ] **Step 3: Verify fix**

```bash
python scripts/log_feedback.py
```
Expected (fixed):
```
log_feedback.py: no input — pipe a report file, e.g.:
  cat runs/<file>.json | python scripts/log_feedback.py
```
Exit code: 2.

- [ ] **Step 4: Verify normal usage still works**

```bash
python -X utf8 scripts/log_feedback.py --dry-run < runs/$(ls runs/*.json | head -1 | xargs basename)
```
Expected: prints a feedback entry summary, does not write to file.

- [ ] **Step 5: Commit**

```bash
git add scripts/log_feedback.py
git commit -m "fix(log_feedback): clear usage hint on empty stdin via utils.load_json_stdin"
```

---

## Task 5: Fix I1 + I2 — `aggregator.py` weighted scheme warning + veto validation

**Files:**
- Modify: `scripts/aggregator.py`

- [ ] **Step 1: Add `warnings` import**

In `scripts/aggregator.py`, add `import warnings` to the imports block at the top.

- [ ] **Step 2: Add warning to `aggregate_weighted`**

Find `def aggregate_weighted` (~line 70). Add at the start of the function body:

```python
    import warnings
    warnings.warn(
        "aggregate_weighted treats Conservator as utility (higher=better), but Conservator "
        "emits risk (higher=worse). Scores will be inverted relative to other schemes. "
        "Use 'conservative_override' or 'risk_adjusted_utility' instead.",
        stacklevel=2,
    )
```

- [ ] **Step 3: Add veto_threshold validation to `aggregate_conservative_override`**

Find `def aggregate_conservative_override` (~line 93). After the `weights = weights or ...` line, add:

```python
    if not (0.0 <= veto_threshold <= 1.0):
        raise ValueError(
            f"veto_threshold must be in [0.0, 1.0], got {veto_threshold!r}"
        )
```

- [ ] **Step 4: Verify**

```bash
python -c "
import warnings, sys
sys.path.insert(0, 'scripts')
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter('always')
    from aggregator import aggregate_weighted
    aggregate_weighted([{'id':'a','scores':{'generator':1,'control':1,'conservator':0.2}}],
                       {'generator':1,'control':1,'conservator':1})
    print('warning caught:', w[0].message if w else 'NONE — bug not fixed')
"
```
Expected: `warning caught: aggregate_weighted treats Conservator as utility...`

```bash
python -c "
import sys; sys.path.insert(0, 'scripts')
from aggregator import aggregate_conservative_override
try:
    aggregate_conservative_override([], veto_threshold=2.0)
    print('BUG: no error raised')
except ValueError as e:
    print('OK:', e)
"
```
Expected: `OK: veto_threshold must be in [0.0, 1.0], got 2.0`

- [ ] **Step 5: Run evals**

```bash
python scripts/run_evals.py
```
Expected: exit 0.

- [ ] **Step 6: Commit**

```bash
git add scripts/aggregator.py
git commit -m "fix(aggregator): warn on weighted scheme; validate veto_threshold range"
```

---

## Task 6: Fix I3 — `confidence.py` validate_input + import from utils

**Files:**
- Modify: `scripts/confidence.py`

- [ ] **Step 1: Verify the bug**

```bash
python -c "
import json, subprocess
bad = json.dumps({'candidates': [{'id': 'x'}], 'chosen': 'x'})
r = subprocess.run(['python', 'scripts/confidence.py'], input=bad, capture_output=True, text=True)
print('exit:', r.returncode)
print('stderr:', r.stderr)
"
```
Expected (buggy): `KeyError: 'scores'` traceback, exit 1 (non-zero but uninformative).

- [ ] **Step 2: Add import from utils and validate_input**

In `scripts/confidence.py`, add import:
```python
from utils import force_utf8_streams, validate_keys
```

Delete the local `_force_utf8_streams` function definition.

Add a `validate_input` function before `derive`:
```python
def validate_input(data: dict) -> None:
    """Validate confidence.py input shape before any computation."""
    validate_keys(data, ["candidates", "chosen"], context="confidence input")
    if not isinstance(data["candidates"], list):
        print("confidence input: 'candidates' must be a list", file=sys.stderr)
        sys.exit(1)
    for i, cand in enumerate(data["candidates"]):
        if not isinstance(cand, dict):
            print(f"confidence input: candidates[{i}] must be an object", file=sys.stderr)
            sys.exit(1)
        if "scores" not in cand:
            print(
                f"confidence input: candidates[{i}] (id={cand.get('id', '?')!r}) "
                f"missing required field 'scores'",
                file=sys.stderr,
            )
            sys.exit(1)
        validate_keys(
            cand["scores"],
            ["generator", "control", "conservator"],
            context=f"candidates[{i}].scores",
        )
```

In the `main` function, call `validate_input(data)` right after `data = json.loads(...)` / reading stdin, before calling `derive`.

Replace `_force_utf8_streams()` call with `force_utf8_streams()`.

- [ ] **Step 3: Verify fix**

```bash
python -c "
import json, subprocess
bad = json.dumps({'candidates': [{'id': 'x'}], 'chosen': 'x'})
r = subprocess.run(['python', 'scripts/confidence.py'], input=bad, capture_output=True, text=True)
print('exit:', r.returncode)
print('stderr:', r.stderr.strip())
"
```
Expected (fixed):
```
exit: 1
stderr: confidence input: candidates[0] (id='x') missing required field 'scores'
```

- [ ] **Step 4: Verify normal usage**

```bash
echo '{"candidates":[{"id":"a","scores":{"generator":0.9,"control":0.8,"conservator":0.2}},{"id":"b","scores":{"generator":0.6,"control":0.7,"conservator":0.4}}],"chosen":"a"}' | python scripts/confidence.py
```
Expected: JSON with `confidence`, `agreement`, `separation` fields.

- [ ] **Step 5: Commit**

```bash
git add scripts/confidence.py
git commit -m "fix(confidence): validate_input catches missing scores field with clear message"
```

---

## Task 7: Fix I4 + I5 — `build_report.py` error handling + `render_feedback_html.py` OSError

**Files:**
- Modify: `scripts/build_report.py:209-211`
- Modify: `scripts/render_feedback_html.py:250-251`

- [ ] **Step 1: Fix `build_report.py` — exit immediately after bundle type error**

In `scripts/build_report.py`, find:
```python
    if not isinstance(bundle, dict):
        _err("bundle must be a JSON object")
        return 2
```

This is actually fine — it does return. But the `_err` function may continue. Let's verify:

```bash
grep -n "_err" scripts/build_report.py | head -5
```

If `_err` is just `print(..., file=sys.stderr)`, the existing code is correct and I4 was a false positive. Verify:
```bash
python -c "
import subprocess, json
r = subprocess.run(['python', 'scripts/build_report.py'], input='[1,2,3]', capture_output=True, text=True)
print('exit:', r.returncode, '| stderr:', r.stderr.strip())
"
```
Expected: exit 2, clear error message. If already working, mark as verified and skip.

- [ ] **Step 2: Fix `render_feedback_html.py` — catch OSError on run-file read**

In `scripts/render_feedback_html.py`, find lines ~250-251:
```python
            if run_file.exists():
                try:
                    run_dict = json.loads(run_file.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    run_dict = None
```

Replace with:
```python
            if run_file.exists():
                try:
                    run_dict = json.loads(run_file.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    run_dict = None
```

- [ ] **Step 3: Verify render_feedback_html.py still works**

```bash
python scripts/render_feedback_html.py --help
```
Expected: shows help without error.

- [ ] **Step 4: Commit**

```bash
git add scripts/build_report.py scripts/render_feedback_html.py
git commit -m "fix(scripts): catch OSError on run-file read in render_feedback_html"
```

---

## Task 8: Deduplication — replace local `_force_utf8_streams` with import from utils

**Files:**
- Modify: `scripts/aggregator.py`
- Modify: `scripts/build_report.py`
- Modify: `scripts/strip_context.py`
- Modify: `scripts/validate_report.py`
- Modify: `scripts/dialectic_merge.py` (not yet done in Task 3)

Note: `confidence.py` and `log_feedback.py` already done in Tasks 4 and 6.

For **each** of the 4 scripts above, do the same 3-step pattern:

- [ ] **Step 1: Add import to each script**

In each script's import block, add:
```python
from utils import force_utf8_streams
```

- [ ] **Step 2: Delete local `_force_utf8_streams` function**

Find and delete the function definition (typically 6 lines):
```python
def _force_utf8_streams() -> None:
    # Windows default stdin/stdout encoding is cp1252; piping UTF-8 JSON
    # through that mangles non-ASCII (ț, ș, ă) before any script sees it.
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(encoding="utf-8")
```

- [ ] **Step 3: Verify each script still runs**

```bash
python scripts/aggregator.py --help
python scripts/build_report.py --help
python scripts/strip_context.py --help
python scripts/validate_report.py --help
python scripts/dialectic_merge.py --help
```
Each: shows help without error.

- [ ] **Step 4: Run evals**

```bash
python scripts/run_evals.py
```
Expected: exit 0.

- [ ] **Step 5: Commit**

```bash
git add scripts/aggregator.py scripts/build_report.py scripts/strip_context.py scripts/validate_report.py scripts/dialectic_merge.py
git commit -m "refactor(scripts): replace local _force_utf8_streams with import from utils"
```

---

## Task 9: Add `validate_input()` to remaining scripts

**Files:**
- Modify: `scripts/dialectic_merge.py`
- Modify: `scripts/build_report.py`

### `dialectic_merge.py`

- [ ] **Step 1: Add validate_keys import**

Add `validate_keys` to the existing `from utils import force_utf8_streams` line:
```python
from utils import force_utf8_streams, validate_keys
```

- [ ] **Step 2: Add validate_input function**

Before the `merge` function, add:
```python
def validate_input(payload: dict) -> None:
    """Validate dialectic_merge input has required pass1 structure."""
    validate_keys(payload, ["pass1"], context="dialectic_merge input")
    validate_keys(payload["pass1"], ["generator", "control", "conservator"],
                  context="dialectic_merge input.pass1")
```

- [ ] **Step 3: Call validate_input in main**

In the `main` function, after reading and parsing stdin/file, call:
```python
    validate_input(payload)
```
before passing to `merge(payload)`.

### `build_report.py`

- [ ] **Step 4: Add validate_keys import**

Add `validate_keys` to the existing `from utils import force_utf8_streams` line:
```python
from utils import force_utf8_streams, validate_keys
```

- [ ] **Step 5: Add validate_input function**

Before the `build` function, add:
```python
def validate_input(bundle: dict) -> None:
    """Validate build_report bundle has required top-level fields."""
    validate_keys(
        bundle,
        ["success_criterion", "verification", "generator", "control", "conservator"],
        context="build_report bundle",
    )
```

- [ ] **Step 6: Call validate_input in main**

In the `main` function, after `bundle = json.load(args.input)` and the `isinstance` check, add:
```python
    validate_input(bundle)
```

- [ ] **Step 7: Verify both scripts give clear errors on missing fields**

```bash
echo '{"pass1": {"generator": {}}}' | python scripts/dialectic_merge.py
```
Expected: `dialectic_merge input.pass1: missing required field 'control'`

```bash
echo '{"success_criterion": "test"}' | python scripts/build_report.py
```
Expected: `build_report bundle: missing required field 'verification'`

- [ ] **Step 8: Run evals**

```bash
python scripts/run_evals.py
```
Expected: exit 0.

- [ ] **Step 9: Commit**

```bash
git add scripts/dialectic_merge.py scripts/build_report.py
git commit -m "feat(scripts): validate_input guards in dialectic_merge and build_report"
```

---

## Task 10: Update `docs/architecture.html`

**Files:**
- Modify: `docs/architecture.html`

- [ ] **Step 1: Find insertion point in Architecture tab**

```bash
grep -n "Scripts\|script\|utils" docs/architecture.html | head -20
```
Identify the scripts section in the Architecture tab (id="architecture").

- [ ] **Step 2: Add utils.py card to Architecture tab**

Find the scripts grid/section in the Architecture tab. After the last script card / before the closing `</section>`, add:

```html
<div style="margin-top:24px; padding:16px; background:var(--inset); border:1px solid var(--line); border-radius:6px;">
  <h3 style="margin:0 0 12px; font-size:13px; color:var(--muted); text-transform:uppercase; letter-spacing:.05em;">Shared Utilities — <code>scripts/utils.py</code></h3>
  <table style="width:100%; border-collapse:collapse; font-size:12.5px;">
    <thead><tr>
      <th style="text-align:left; padding:4px 8px; color:var(--muted); font-weight:500; border-bottom:1px solid var(--line);">Funcție</th>
      <th style="text-align:left; padding:4px 8px; color:var(--muted); font-weight:500; border-bottom:1px solid var(--line);">Rol</th>
    </tr></thead>
    <tbody>
      <tr><td style="padding:4px 8px;"><code>force_utf8_streams()</code></td><td style="padding:4px 8px; color:var(--muted);">Reconfigurează stdin/stdout/stderr la UTF-8 (fix Windows cp1252)</td></tr>
      <tr><td style="padding:4px 8px;"><code>load_json_stdin(script_name)</code></td><td style="padding:4px 8px; color:var(--muted);">Citește + parsează JSON din stdin; hint clar la stdin gol sau JSON invalid</td></tr>
      <tr><td style="padding:4px 8px;"><code>validate_keys(data, required, context)</code></td><td style="padding:4px 8px; color:var(--muted);">Verifică câmpuri obligatorii; exit 1 cu mesaj explicit la lipsă</td></tr>
    </tbody>
  </table>
  <p style="margin:10px 0 0; font-size:12px; color:var(--muted);">Importat de toate scriptele care citeau stdin sau aveau <code>_force_utf8_streams</code> local. Scriptele rămân executabile independent — <code>utils.py</code> e stdlib-only.</p>
</div>
```

- [ ] **Step 3: Add validation note to Flow tab Step 6**

In the Flow tab (id="flow"), find the Step 6 (Report) card. Locate the `<div>` that contains `build_report.py` reference. After that `<div>`, add:

```html
<div style="font-size:12px; color:var(--accent); margin-top:4px;">✓ Input validat prin <code>validate_input()</code> — exit 1 cu câmp lipsă specificat.</div>
```

- [ ] **Step 4: Open and verify**

Open `docs/architecture.html` in a browser (double-click or `start docs/architecture.html`).
Verify:
- Architecture tab shows the utils.py card at the bottom of the scripts section
- Flow tab Step 6 shows the validation note

- [ ] **Step 5: Commit**

```bash
git add docs/architecture.html
git commit -m "docs(architecture): add utils.py card in Architecture tab, validation note in Flow tab"
```

---

## Task 11: Worktree Cleanup

**Files:** none (git maintenance)

- [ ] **Step 1: List current worktrees**

```bash
git worktree list
```
Note which ones are active (main + fix/script-bugs) vs stale.

- [ ] **Step 2: Prune registered but gone worktrees**

```bash
git worktree prune
git worktree list
```
Verify only active worktrees remain in git's registry.

- [ ] **Step 3: Remove orphaned directories**

```bash
ls .claude/worktrees/
```
For each directory that no longer corresponds to an active worktree:
```bash
rm -rf ".claude/worktrees/<name>"
```

- [ ] **Step 4: Verify clean state**

```bash
git worktree list
ls .claude/worktrees/ 2>/dev/null || echo "directory gone or empty"
```
Expected: only `main` and `fix/script-bugs` (or whichever are active).

- [ ] **Step 5: Commit if .gitignore or other tracked files changed**

If `git status` shows changes:
```bash
git add -A
git commit -m "chore: prune stale git worktrees"
```
If nothing changed (worktrees were untracked), no commit needed.

---

## Task 12: Final Evals + Summary

- [ ] **Step 1: Run full eval suite**

```bash
python scripts/run_evals.py
```
Expected: exit 0, all scenarios pass.

- [ ] **Step 2: Smoke-test the key bug fixes**

```bash
# B1: priors returns recent entries
python -c "import sys; sys.path.insert(0,'scripts'); from priors import build_priors; p=build_priors(n=3); print('B1 OK — recent dates:', [e['date'] for e in p['recent']])"

# B4: log_feedback without stdin gives clear error
python scripts/log_feedback.py 2>&1 | head -2

# I3: confidence with missing scores gives clear error
echo '{"candidates":[{"id":"x"}],"chosen":"x"}' | python scripts/confidence.py 2>&1

# utils: import works from any working directory
python -c "import sys; sys.path.insert(0,'scripts'); from utils import force_utf8_streams, load_json_stdin, validate_keys; print('utils OK')"
```

- [ ] **Step 3: Verify no local `_force_utf8_streams` remain**

```bash
grep -rn "_force_utf8_streams" scripts/ --include="*.py"
```
Expected: no results (all replaced by import from utils).

- [ ] **Step 4: Final commit if anything uncommitted**

```bash
git status
```
If clean, done. If not:
```bash
git add -A
git commit -m "chore: final cleanup after refactor"
```
