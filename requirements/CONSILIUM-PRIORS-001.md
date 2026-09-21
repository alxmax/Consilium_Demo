---
milestone: v1.0
id: CONSILIUM-PRIORS-001
status: confirmed
level: code
layer: feature
owner: alxmax
depends_on: [CONSILIUM-FEEDBACK-001, CONSILIUM-UTILS-001]
risk: 2  # REVIEW
satisfies: [ARCH-CONSILIUM-LEARNING-001]
---

# priors

> Describes observed behavior, verified against scripts/priors.py source.

## Description

Every line in this section is binding.

- `priors.py` computes advisory soft-prior signals from past deliberation history and emits them as a JSON object to stdout.
- The signal block is pasted into the deliberation at step 0 so voices can calibrate toward patterns that have caused past problems.
- Signals are advisory only; prompts in `prompts/*.md` remain authoritative.
- `priors.py` reads `.consilium/FEEDBACK.html` (the usage journal, parsed via `feedback.py`) and `.consilium/runs/*.json` (past deliberation reports).
- CLI flags control the read: `--n N` sets the recent-slice size (default 10); `--no-runs` skips the runs/ directory; `--feedback-file` overrides the FEEDBACK.html path; `--runs-dir` overrides the runs/ directory path.
- `recent` holds the last N FEEDBACK entries, newest first.
- `counts` tallies outcomes (OK / BAD / OVR / PEND) over the recent slice.
- `override_rate`, `bad_rate`, and `weighted_bad_rate` are risk indicators derived from the recent slice.
- `conservator_veto_rate` is the fraction of runs with at least one vetoed candidate. It counts only runs where `deliberation_log[step=aggregate].result.vetoed` is non-empty or `chosen` is `None`; Sequential BLOCK/REWORK outcomes are intentionally excluded — this is by design, not a bug to fix.
- `weighted_bad_rate` shares its denominator with `bad_rate` (OK+BAD+OVR). Rows whose note contains `[confirmed]` receive weight 2.0; unconfirmed rows receive weight 1.0. Production-verified outcomes dominate subjective ratings as a result.
- `top_note_keywords` lists the top-5 alpha tokens (length >= 4) from recent notes.
- `stale_pendings` lists FEEDBACK rows still PEND and older than `STALE_PEND_DAYS`. `STALE_PEND_DAYS = 2` is hardcoded, reduced from 7, and not CLI-configurable; entries older than 2 days surface at step 0 for retrospective close.
- `missing_feedback_runs` lists `runs/` files with no matching FEEDBACK row.
- Exit code is non-zero on a parse error.

## Verify intent

- None - all questions resolved.

## Cases

- **CASE-1** — Given a valid `FEEDBACK.html` and `runs/` directory, when `python scripts/priors.py` runs, then it completes without error.
- **CASE-2** — Given the `--no-runs` flag, when `priors.py` runs, then `conservator_veto_rate` and `missing_feedback_runs` are suppressed from the output.
- **CASE-3** — Given FEEDBACK entries with outcome PEND older than `STALE_PEND_DAYS`, when `priors.py` runs, then those entries appear in `stale_pendings`.
- **CASE-4** — Given `runs/` files with no matching FEEDBACK row, when `priors.py` runs, then those files appear in `missing_feedback_runs`.

## Context (non-binding)

**Notes** — Signals described here reflect observed behavior, verified against the `scripts/priors.py` source rather than a separate design spec.

**Current implementation** — `scripts/priors.py`
