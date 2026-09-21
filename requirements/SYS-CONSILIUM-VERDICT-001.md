---
milestone: v1.1
id: SYS-CONSILIUM-VERDICT-001
status: confirmed
level: system
layer: need
depends_on: []
owner: alxmax
risk: 1
---

# A trustworthy verdict on a change before it is committed

> A developer about to commit a non-trivial code change gets a GO / MODIFY / STOP verdict they can trust, backed by a validated report, without reading the deliberation itself.

## Description

Every line in this section is binding.

- `/consilium` on a proposed change ends in exactly one verdict (GO, MODIFY or STOP), a chosen approach and a calibrated confidence score.
- Every non-skipped deliberation writes one report to `.consilium/runs/`, and that report passes `validate_report.py` before the verdict is shown.
- A change small enough for the scope gate (the check that lets trivial diffs skip deliberation) gets a bypass verdict instead of a full deliberation.
- Past outcomes logged to `FEEDBACK.html` feed the priors (historical rates that adjust later scores), so the verdict improves with use.

## Verify intent

- None - contract confirmed by the owner on 2026-09-21.

## Cases

- **CASE-1** — Given a non-trivial diff, when `/consilium` runs in any mode, then one report lands in `.consilium/runs/` and `validate_report.py` exits 0 on it.
- **CASE-2** — Given a report whose telemetry is malformed, when `validate_report.py` reads it, then it exits non-zero and the verdict is not presented as validated.
- **CASE-3** — Given a diff under the scope gate's size limits, when `/consilium` runs, then the report records a bypass and no voice is dispatched.
