# Observe → Think → Act → Learn (descriptive framing)

> Moved out of `SKILL.md` on 2026-06-10 to keep the runtime contract lean — every line
> of SKILL.md is read by the orchestrator at each invocation. This document is a
> reading aid for contributors; it creates **no behavioral contract**. Steps 0–7 in
> `SKILL.md` remain the authoritative workflow.

The mapping below names what is already present in the pipeline for contributors who
arrive expecting an Observe–Think–Act–Learn shape — without prescribing anything new.

| OTAL phase | Alias | Step(s) | Script(s) that implement the phase |
|---|---|---|---|
| **Observe** | **EXPLORE** | Step 0 + Step 1 | `priors.py` (reads `FEEDBACK.html` + `runs/*.json`); orchestrator gathers context from the codebase |
| **Think**   | — | Steps 2–5     | `aggregator.py`, `confidence.py`, `meta_critic.py` (retired); Generator → Conservator → Control voices |
| **Act**     | **COMMIT** | Step 6 + Step 7 | `validate_report.py`, `build_report.py` (write `.consilium/runs/<file>.json`); `infer_pipeline.py` (write code) |
| **Learn**   | — | Step 6 final action + retroactive | `log_feedback.py` (append to `FEEDBACK.html`); `mark_outcome.py` (retroactive `[confirmed]` weighting) |

```
         ┌────────────────────────────────────────────┐
    ┌───▶│  OBSERVE    (Step 0 + Step 1)              │
    │    │  priors.py · gather context                │
    │    └────────────────────┬───────────────────────┘
    │                         │
    │    ┌────────────────────▼───────────────────────┐
    │    │  THINK      (Steps 2 → 5)                  │
    │    │  Generator → Conservator → Control         │
    │    │  → aggregator.py · confidence.py           │
    │    │                                            │
    │    │  ↻ Step 5d: one orchestrator-driven        │
    │    │    sub-iteration if confidence < 0.7       │
    │    └────────────────────┬───────────────────────┘
    │                         │
    │    ┌────────────────────▼───────────────────────┐
    │    │  ACT        (Step 6 + Step 7)              │
    │    │  validate_report.py · build_report.py      │
    │    │  → .consilium/runs/<file>.json             │
    │    │  infer_pipeline.py → code written          │
    │    └────────────────────┬───────────────────────┘
    │                         │
    │    ┌────────────────────▼───────────────────────┐
    │    │  LEARN      (Step 6 final + retroactive)   │
    │    │  log_feedback.py → FEEDBACK.html           │
    │    │  mark_outcome.py — 2× weight when          │
    │    │  [confirmed] by production reality         │
    │    └────────────────────┬───────────────────────┘
    │                         │
    └─────────────────────────┘
         priors.py reads FEEDBACK.html at the next
         deliberation — this is the closing edge
```

A small in-run sub-iteration exists: at `confidence < 0.7`, Step 5d has the
orchestrator gather discriminating evidence and re-run the voices once (`↻` in the
diagram). This is the only formal iteration mechanism; there is no meta-controller.
(The old hint generator `retry_context.py` was retired to `scripts/deprecated/` on
2026-06-10 — its hints had zero corpus usage; the retry step itself stays.)

**Calibration note (Learn phase).** The Learn phase is presently *partial* in a
structural sense: `log_feedback.py` writes outcomes into `.consilium/FEEDBACK.html`
(HTML rows), but `.consilium/runs/<file>.json` does not carry a structured `outcome`
field. Consequently `priors.py` reads outcomes from the HTML journal, not from a typed
JSON field. The loop closes via the journal — naming the gap explicitly so future
readers don't assume an unwired feedback channel exists.

**What this framing is not.** This document does not introduce iteration triggers
beyond Step 5d's single retry, does not name a meta-controller, and does not authorize
voices or aggregator to cite "OTAL step X" as ground for new behavior. If a future
proposal seeks behavioral iteration triggers (e.g. firing a second pass on
`meta_critic.generator_divergence < 0.4`), that requires its own Senate audit with
empirical pilot data — `generator_divergence` had zero labeled triggering events in
`runs/`, so any threshold would be uncalibrated. A dynamic meta-controller is
explicitly out of scope: its TODO precondition (item #16) was dropped in triage, and
recursive routing contradicts Constitution Principle 2 (Simplicity first).

> **TODO #18 closure rationale** (2026-05-19 Senate audit,
> `runs/senate/2026-05-19_214850-todo-18-otal-formalization.json`, MODIFY 0-8-1): 8 of
> 9 senators converged on docs-only framing. Level 2 (iteration triggers) deferred
> until ≥3 PEND rows in `FEEDBACK.html` demonstrate the current `confidence<0.7` retry
> underperforms. Level 3 (meta-controller) closed pending #16's revival.
