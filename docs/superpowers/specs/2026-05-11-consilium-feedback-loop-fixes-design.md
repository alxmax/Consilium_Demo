# Consilium feedback loop fixes — design

**Date:** 2026-05-11
**Scope:** HIGH-priority recommendations from the 8-run retrospective (15:00–21:00, 2026-05-11). Closes the feedback-loop drift identified across `runs/2026-05-11_*.json`.

## Problem statement

Across 8 deliberations today, the feedback loop is effectively broken:

- 6/8 runs have `deliberation_log[aggregate].result` as a **string** (manual-narrative summary) instead of the canonical dict that `build_report.py` emits. This crashed `log_feedback.py` twice (1730 and 2100 runs) and required manual workaround.
- 4 entries appended to `FEEDBACK.md` remain `PEND`. None were ever rated `OK`/`BAD`/`OVR` by the user — the manual close step described in SKILL.md never happens in practice.
- `validate_report.py` did not catch the malformed reports because it does not inspect `deliberation_log` shape or require `telemetry.mode` on non-skipped reports.

**Root cause:** the agent (me) bypassed the canonical `build_report.py` pipeline and hand-assembled reports. Nothing in the toolchain caught the drift. The passive instruction "user updates outcome manually later" produces no closure in practice.

## Goals

1. Crash-free auto-logging when reports drift from the canonical shape (defensive).
2. The validator catches the drift at the source so the next deliberation cannot ship a bad report (offensive).
3. Outcome closure happens at the moment of decision, not "later" — with friction proportional to confidence.

## Non-goals

- Adding the `dialectic_suggested` signal when confidence is low (separate proposal; additive, not corrective).
- Adding a `BAD` capture mechanism beyond what falls out of retrospective PEND closure.
- Rebuilding the 6 historical runs to match the new schema. They are written; new validation applies only to future reports.

## Architecture

```
Step 6 pipeline (after build_report.py)

bundle.json
    │
    ▼
build_report.py ──► report.json (canonical shape)
    │
    ▼
validate_report.py  ◄── (B) deliberation_log shape + telemetry.mode
    │
    ▼
log_feedback.py  ◄── (A) defensive on aggregate.result + (C) --outcome
    │
    ▼
agent reads report.confidence
    │
    ├── conf >= 0.7  ──► --outcome OK  (auto)
    │
    ├── conf <  0.7  ──► prompt user "Override? [alt_id|no|skip]"
    │                    └── --outcome {OK|OVR --override-target X|PEND}
    │
    └── conf is null ──► PEND default (all vetoed; no decision to rate)


Step 0 retrospective (priors.py)
    │
    ▼
parse FEEDBACK.md  ──► entries
    │
    ▼
find_stale_pendings(>7 days)  ──► up to 5 entries
    │
    ▼
agent prompts user: "Close these now? [OK/BAD/skip per entry]"
    │
    ▼
Edit tool on FEEDBACK.md (in-place line edit; not appends)
```

Three units, clear boundaries:
- **A** `scripts/log_feedback.py` — defensive on `aggregate.result`, parameterized outcome.
- **B** `scripts/validate_report.py` — adds 2 rules in `validate()`.
- **C** `SKILL.md` + `scripts/priors.py` — workflow change at Step 6, retrospective signal at Step 0.

No new files. No new scripts. CLI of all touched scripts remains backward-compatible.

## Component A — `log_feedback.py` defensive + outcome flag

### A.1 Defensive on `aggregate.result`

Line 77 currently:
```python
aggregate_result = aggregate_step.get("result") or {}
```
After the fix:
```python
raw_result = aggregate_step.get("result")
aggregate_result = raw_result if isinstance(raw_result, dict) else {}
```

Why: manual-assembled runs put a narrative string in `result` instead of the canonical aggregate dict. The downstream `.get("vetoed")` / `.get("retry_suggested")` calls would crash. Treating string as empty preserves the rest of the note derivation; the script keeps going.

Trade-off: notes on manual-assembled reports will show `n cand, 0 vetoed, ...` even when veto count > 0. Accepted — the source of truth is wrong (manual assembly); the note degrades gracefully rather than blocking the FEEDBACK.md append entirely.

One comment on the new line explaining *why* (the constraint: manual reports drift from canonical shape).

### A.2 Outcome flag

Current line 113 hardcodes `"PEND"`:
```python
return f"- {today} | {truncate(sc, CONTEXT_MAX)} | {chosen_s} | PEND | {derive_note(report)}"
```

New CLI:
```python
ap.add_argument("--outcome", choices=("OK", "BAD", "OVR", "PEND"), default="PEND")
ap.add_argument("--override-target", default=None,
                help="alt_id when outcome=OVR; ignored otherwise")
ap.add_argument("--user-note", default=None,
                help="optional user-supplied note, appended to auto-note")
```

`build_line` becomes:
```python
def build_line(report: dict, outcome: str, override_target: str | None, user_note: str | None) -> str:
    # ... existing validation ...
    auto_note = derive_note(report)
    extras = []
    if outcome == "OVR" and override_target:
        extras.append(f"override={_clean(override_target)}")
    if user_note and user_note.strip():
        extras.append(_clean(user_note))
    note = "; ".join([auto_note] + extras) if extras else auto_note
    return f"- {today} | {truncate(sc, CONTEXT_MAX)} | {chosen_s} | {outcome} | {note}"
```

Backward compat: no flags → default `PEND` outcome → identical output to today. Existing CLI users (smoke-test pipelines) are unaffected.

Validation:
- `--override-target` without `--outcome OVR` → silently ignored (no error; flag is just unused).
- `--outcome OVR` without `--override-target` → permitted (`extras` stays empty for that piece). User-note can still appear. Rationale: agent might OVR with free-text note when alt_id isn't a clean fit.

## Component B — `validate_report.py` strict checks

Two new validators added to `validate()`:

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

Wired into `validate(report)`:
```python
problems.extend(_validate_deliberation_log(
    report.get("deliberation_log"),
    report.get("skipped") is True,
))
problems.extend(_validate_telemetry_required(report))
```

The pre-existing `_validate_telemetry` (shape checks for `voices`, `passes`, `mode` type) is **kept** — it still runs when telemetry is present. The new check stacks: required + shape.

Skipped reports continue to short-circuit both new validators. Their `deliberation_log: []` and missing `telemetry` are legitimate by design.

Error messages are intentionally diagnostic — "did you bypass build_report.py?" gives the next reader (likely future-me) the cause, not just the symptom.

Backward compat: **breaks** all 6 historical manual-assembled runs that lack canonical shape. Intentional — they shouldn't have passed in the first place. Historical runs aren't re-validated, so no on-disk fallout. Future runs that go through `build_report.py` pass automatically (it always produces canonical shape).

## Component C — Outcome capture (SKILL.md + priors.py)

### C.1 SKILL.md Step 6 workflow

The current text in Step 6 ("Acțiuni finale" item 2):

> Outcome rămâne `PEND` — user-ul îl actualizează la `OK`/`BAD`/`OVR` ulterior, prin editare manuală a fișierului, când rezultatul e cunoscut.

Replaced with:

> **Decide outcome la finalul Step 6.** Citește `confidence` din raport:
>
> - **`confidence >= 0.7`** → rulează `cat runs/<file>.json | python scripts/log_feedback.py --outcome OK`. Nu întreba user-ul; pickul are agreement + separation suficient.
>
> - **`confidence < 0.7`** → întreabă user-ul: *"Confidence sub prag (<X>). Override pick `<chosen>`? Alternative din raport: `<alt_id list>`. Răspunde alt_id, 'no', sau 'skip'."* Pe baza răspunsului:
>   - `no` → `--outcome OK`
>   - `<alt_id>` → `--outcome OVR --override-target <alt_id>` (cu `--user-note` opțional)
>   - `skip` → fără flag (PEND default)
>
> - **`confidence` is null** (toți vetoiți) → `log_feedback.py` fără flag. Veto total = no decision = no outcome to rate.

Rationale (from brainstorm):
- Active learning sampling: don't ask on high-confidence; ask only where the signal would calibrate the aggregator.
- Implicit signal capture: a high-confidence decision the user doesn't push back on is OK by default — the absence of objection is the signal.
- Alt_id-based OVR: alternatives are already enumerated in the report; user picks one, the line is parseable downstream.

Threshold `0.7` lives in SKILL.md as part of the workflow, not as a config in the script. The script is mechanical — it writes what the agent tells it to. Rationale: changing the threshold is a workflow decision, not a code change.

### C.2 `priors.py` retrospective signal

Add a helper and a new field in the output:

```python
from datetime import date, timedelta

STALE_PEND_DAYS = 7

def find_stale_pendings(entries: list[dict], days_old: int = STALE_PEND_DAYS) -> list[dict]:
    cutoff = (date.today() - timedelta(days=days_old)).isoformat()
    return [
        {"date": e["date"], "context": e["context"], "chosen": e["chosen"]}
        for e in entries
        if e.get("outcome") == "PEND" and e.get("date", "") < cutoff
    ][:5]  # cap at 5
```

Output gains:
```json
"stale_pendings": [
    {"date": "2026-05-03", "context": "...", "chosen": "..."},
    ...
]
```

SKILL.md Step 0 gains a note (after the existing priors.py paragraph):

> Dacă `stale_pendings` e non-empty în output-ul priors.py, întreabă user-ul *înainte* de a continua la Step 1: *"Ai N entries PEND mai vechi de 7 zile: [date | chosen] × N. Vrei să le închid acum (OK/BAD/skip per entry) sau să continuăm cu deliberarea nouă?"* Update-ul se face cu `Edit` tool pe `FEEDBACK.md` (înlocuiește `PEND` din linia respectivă cu `OK` / `BAD`), nu prin `log_feedback.py` (acela appendează, nu editează).

Cap at 5 to bound the prompt size — older PEND beyond that are effectively discarded as signal anyway.

### C.3 Edge cases

- **Confidence in [0.69, 0.71]:** strictly `< 0.7` triggers prompt. No fuzzy zone.
- **User replies invalid alt_id at conf<0.7 prompt:** agent treats the response as `--user-note` free text with `--outcome OVR` and no `--override-target`. The line still parses; the signal degrades from "user wanted X" to "user wanted something other than chosen, reason: …".
- **Confidence 0.99 but user wants to override anyway:** rare, not handled in flow. User can manually edit FEEDBACK.md after.
- **Multiple stale PEND with same context:** cap at 5 in priors output prevents noise; older entries decay silently.

## Implementation order

1. **B first** — make the validator strict. Pre-existing scenarios in `evals/scenarios.json` that test `validate_report.py` on non-skipped reports need updated fixtures (add canonical `deliberation_log[aggregate].result` dict and `telemetry.mode`). Run `python scripts/run_evals.py` to confirm green before moving on.
2. **A next** — defensive fix is independent; can be done in parallel with B but B's strict validator is the long-term prevention.
3. **C last** — SKILL.md edit + priors.py addition. Touches the workflow, so changes here should land after the tooling is reliable.

Each component is independently shippable. Bundling them in one commit is fine (they're coherent as a feedback-loop closure); splitting per-component is also fine.

## Testing

- `python scripts/run_evals.py` — must pass after each component. The 17+ scenarios cover validator + aggregator + confidence; B needs scenario updates, A and C don't touch the deterministic core.
- Manual smoke: assemble a bundle, pipe through `build_report.py | validate_report.py | log_feedback.py --outcome OK` and confirm the line in `FEEDBACK.md`. Repeat with `--outcome OVR --override-target some_alt --user-note "reason"`.
- For C.2: write a fake `FEEDBACK.md` with 6 PEND entries dated 8+ days ago, run `priors.py`, confirm `stale_pendings` returns 5 (capped) with correct shape.

## What this design intentionally does not do

- Does not auto-close PEND to OK after N days. Closure must be a user act, even if low-effort.
- Does not push outcome data to `runs/` (those files are immutable post-write).
- Does not change `build_report.py` or `aggregator.py`. The bug originated *around* them, not in them.
- Does not introduce a config file for the 0.7 threshold. Workflow constant in SKILL.md is sufficient; if the threshold needs to change, it's a 1-line edit.
