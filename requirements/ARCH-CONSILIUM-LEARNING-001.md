---
milestone: v1.1
id: ARCH-CONSILIUM-LEARNING-001
status: confirmed
level: architecture
layer: aggregate
depends_on: [CONSILIUM-FEEDBACK-001, CONSILIUM-LOG-FEEDBACK-001, CONSILIUM-MARK-OUTCOME-001, CONSILIUM-MEMORY-001, CONSILIUM-PRIORS-001, CONSILIUM-AUDIT-FEEDBACK-001, CONSILIUM-RENDER-FEEDBACK-HTML-001, CONSILIUM-CONFIDENCE-CALIBRATION-001]
satisfies: [SYS-CONSILIUM-VERDICT-001]
owner: alxmax
risk: 1
---

# Learning loop: feedback journal, outcomes and priors

> Real-usage outcomes are recorded and read back, so later deliberations are calibrated by earlier ones.

## Description

Every line in this section is binding.

- Each deliberation can be logged as one row of `.consilium/FEEDBACK.html`, written atomically, and its outcome corrected later in place. [[CONSILIUM-LOG-FEEDBACK-001]] [[CONSILIUM-MARK-OUTCOME-001]]
- `FEEDBACK.html` has one parser (`feedback.py`) and one renderer (`render_feedback_html.py`), and a parse of a rendered file round-trips. [[CONSILIUM-FEEDBACK-001]] [[CONSILIUM-RENDER-FEEDBACK-HTML-001]]
- `priors.py` computes historical rates from logged outcomes, and `memory.py` gives one read API over the short, medium and long memory tiers. [[CONSILIUM-PRIORS-001]] [[CONSILIUM-MEMORY-001]]
- Runs that were never logged are detectable, and can be backfilled as pending rows. [[CONSILIUM-AUDIT-FEEDBACK-001]]
- `confidence_calibration.py` reports from logged outcomes whether high confidence actually predicts success. [[CONSILIUM-CONFIDENCE-CALIBRATION-001]]

## Verify intent

- None - contract confirmed by the owner on 2026-09-21.

## Cases

- **CASE-1** — Given a report, when `log_feedback.py` appends it and `feedback.py` parses the file, then the parsed row carries the report's verdict.
- **CASE-2** — Given a run file with no FEEDBACK row, when `audit_feedback.py` runs, then the run is listed as an orphan.
- **CASE-3** — Given a logged row whose outcome is later known, when `mark_outcome.py` corrects it, then `feedback.py` parses the corrected outcome and the row count is unchanged.
