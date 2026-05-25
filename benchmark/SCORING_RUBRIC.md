# SCORING RUBRIC

---

## CODE TASKS (`code/01_circuit_breaker`) — 100 pts total

### Code Implementation — 60 pts
| Criterion    | Max | Description |
|--------------|-----|-------------|
| Correctness  | 20  | Runs correctly, all requirements met, edge cases handled |
| Code Quality | 15  | Clean structure, naming, error handling, idiomatic |
| Completeness | 15  | All components: code + tests + example |
| Edge Cases   | 10  | Handles unstated edge cases beyond prompt |

### Reasoning — 40 pts
| Criterion               | Max | Description |
|-------------------------|-----|-------------|
| Problem Analysis Depth  | 15  | Non-obvious constraints, trade-offs identified before coding |
| Decision Justification  | 15  | Every design choice explained vs alternatives |
| Self-Awareness          | 10  | Flags assumptions, limitations, calibrated deliverable-size estimate |

### Adjustments
| Criterion | Value |
|-----------|-------|
| Time bonus | +5 if API duration under 10 min |
| Time fail  | Score capped at 40 if API duration over 15 min |
| Questions  | 0 / -5 / -15 / -25 for 0 / 1-3 / 4-10 / 10+ |

---

## REASONING TASKS (`reasoning/01_transport_choice`, `reasoning/02_rule_of_three`) — 100 pts total

Each reasoning task ships its own task-specific rubric under
`../Benchmark-scoring/reasoning/<task>/rubric.md` (sibling repo); the LLM judge scores against that file,
not the generic framework below.

Generic framework (for reasoning tasks that don't pin their own breakdown):

| Criterion                    | Max | Description |
|------------------------------|-----|-------------|
| Paradox / problem identified | 25  | Finds the non-obvious core issue |
| Hypothesis quality           | 25  | Multiple, ranked, distinct, well-argued |
| Reasoning depth              | 25  | Second-order thinking, questions the question |
| Self-awareness + calibration | 25  | Assumptions stated, deliverable-size estimate accurate |

### Adjustments
| Criterion | Value |
|-----------|-------|
| Time bonus | +5 if API duration under 5 min |
| Time fail  | Score capped at 40 if API duration over 15 min |
| Questions  | 0 / -5 / -15 / -25 for 0 / 1-3 / 4-10 / 10+ |

### Calibration score (Self-Awareness component)
Measured as the delta between the model's `Estimated deliverable lines` (from the `## Self-estimate` trailer) and the actual line-count summed across the declared output files post-run.

| Deliverable-lines delta | Score |
|-------------------------|-------|
| Under 20%               | 10/10 |
| 20 – 50%                |  7/10 |
| 50 – 200%               |  3/10 |
| Over 200%               |  0/10 |

**Advisory metric — known limitation.** Empirically (Consilium runs/2026-05-19_1041), models frequently omit the `## Self-estimate` trailer despite explicit instructions, because TDD / verification skills induce a "be concise after delivery" pattern. When the trailer is absent → delta is `N/A` → calibration scores 0/10 by default. Attempts to enforce via "READ FIRST" preambles backfired (model interpreted them as meta-instructions and asked clarifying questions). Treat the 0/10 default as a signal to manually inspect the response; the actual `Deliverable lines` row in RESULT.md still gives concrete data for human scoring.

---

## LEADERBOARD

| Mode                    | Circuit Breaker | Transport | Rule of Three | AVG |
|-------------------------|-----------------|----------|---------------|-----|
| Consilium Sequential    |                 |          |               |     |
| Consilium Trias         |                 |          |               |     |
| Consilium Dialectic     |                 |          |               |     |
| Superpowers             |                 |          |               |     |
| Opus Bare               |                 |          |               |     |
