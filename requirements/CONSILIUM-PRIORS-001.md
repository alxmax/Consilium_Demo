---
id: CONSILIUM-PRIORS-001
status: confirmed
layer: feature
owner: auto
depends_on: [CONSILIUM-FEEDBACK-001, CONSILIUM-UTILS-001]
risk: 2  # REVIEW
---

# priors

> Describes observed behavior, verified against scripts/priors.py source.

## Input
- `.consilium/FEEDBACK.html` — usage journal (parsed via `feedback.py`)
- `.consilium/runs/*.json` — past deliberation reports
- CLI flags: `--n N` (recent slice size, default 10), `--no-runs`, `--feedback-file`, `--runs-dir`

## Description
Computes advisory soft-prior signals from past deliberation history and emits
them as a JSON block to stdout. The block is pasted into the deliberation at
step 0 so voices can calibrate toward patterns that have caused past problems.
Signals are advisory only — prompts in `prompts/*.md` remain authoritative.

Signals computed:
- `recent` — last N FEEDBACK entries (newest first)
- `counts` — outcome tally (OK / BAD / OVR / PEND) over the recent slice
- `override_rate`, `bad_rate`, `weighted_bad_rate` — risk indicators
- `conservator_veto_rate` — fraction of runs with at least one vetoed candidate
- `top_note_keywords` — top-5 alpha tokens (len ≥ 4) from recent notes
- `stale_pendings` — FEEDBACK rows still PEND older than `STALE_PEND_DAYS`
- `missing_feedback_runs` — runs/ files with no matching FEEDBACK row

## Output
JSON object to stdout with the signals above. Non-zero exit on parse error.

## WHAT — Verify intent (open questions for the human)
- None — doc is unambiguous.

## Acceptance (= tests)
- `python scripts/priors.py` runs without error given a valid FEEDBACK.html and runs/ dir
- `--no-runs` flag suppresses conservator_veto_rate and missing_feedback_runs
- stale_pendings surfaces entries older than STALE_PEND_DAYS with outcome PEND
- missing_feedback_runs lists runs/ files with no FEEDBACK match
