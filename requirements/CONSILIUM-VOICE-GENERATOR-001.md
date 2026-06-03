---
id: CONSILIUM-VOICE-GENERATOR-001
status: baseline
layer: feature
owner: auto
depends_on: []
---

# generator voice

> WHY: The Generator produces a structured set of candidate approaches for the deliberation, running second in the pipeline after Conservator has calibrated scope.

## WHAT — Contract (normative)

- The voice shall emit a JSON object containing a `candidates` array of 3–5 entries, each with the fields `id`, `summary`, `sketch`, `rationale`, and `downside_estimate`; it shall always include a candidate with `id: "do_nothing"`.
- The voice shall include a candidate named `adversarial_<short_id>` when the change touches shared/core code or a function with more than 3 external callers, or emit `adversarial_skipped` with a reason when that condition is not met.
- The voice shall emit `challenge_upward.triggered: true` (with a one-line reason) when Conservator has under-scaled the question — specifically when the input contains 3+ uneval'd risk terms or when `magnitude = trivial` but the fallback scenario implies more than 10% of capital or more than 1 month of recovery.
- The voice shall emit `fallback_scenario` (a concrete statement of what the user accepts if the preferred option fails) and `coverage_check` (a boolean confirming whether the proposed candidates collectively cover that fallback); if no fallback can be articulated after 2 attempts, it shall emit `abstain.triggered: true` with `reason: "goal_undefined"`.

## WHAT — Verify intent (open questions for the human)

- Observed: the prompt states the `unconventional_*` candidate can be skipped ONLY when `adversarial_*` varies on a non-scope axis — overlap on scope alone is not sufficient. This is a relatively subtle rule that could easily be misapplied, producing silent omission. Intended rule, or should it be simplified?
- Observed: the 0.5 generator-score handicap for `adversarial_*` and `do_nothing` is attributed to `build_report.py`, but the prompt lives in the voice file. This means the voice cannot self-verify whether the handicap will be applied. Is this cross-component dependency documented anywhere other than this prompt?

## WHAT — Notes & known limitations (informative)

- The voice self-limits output via `tokens_budget.generator` received from Conservator, but has no mechanical way to enforce it — over-generation is a real risk on `magnitude = critical` inputs where the model may ignore the budget signal.

## HOW — Acceptance (= tests)

AC-1
  Given a proposed change that touches shared/core code
  When  the Generator voice runs
  Then  the output `candidates` array contains exactly one entry whose `id` starts with `adversarial_`, OR `adversarial_skipped` is present with a non-empty reason string

AC-2
  Given a proposed change where no fallback can be articulated (internal contradiction or no data domain)
  When  the Generator voice runs
  Then  the output contains `abstain.triggered: true` and `abstain.reason` is one of `"goal_undefined"` or a description of the domain-data gap; the `candidates` array may still be present

AC-3
  Given a proposed change with `magnitude = trivial` from Conservator but whose stated fallback implies > 10% capital loss
  When  the Generator voice runs
  Then  the output contains `challenge_upward.triggered: true` with a non-null `reason` string

## WHERE — Current implementation

- prompts/voices/generator.md
