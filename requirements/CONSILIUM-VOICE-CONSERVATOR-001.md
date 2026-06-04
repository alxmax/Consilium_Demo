---
test_exempt: "prompt/mode document — acceptance validated by deliberation integration runs, not unit tests"
id: CONSILIUM-VOICE-CONSERVATOR-001
status: confirmed
layer: feature
owner: auto
depends_on: []
---

# conservator voice

> WHY: The Conservator runs first in the pipeline, scoring risk and calibrating the token budget that Generator and Control will use — it is the scope gate for the entire deliberation.

## WHAT — Contract (normative)

- The voice shall emit a `scores` array where each entry carries `regression_risk` (with `reversibility`, `magnitude`, and `net_concern`), `counterparty_risks`, `bias_check`, `meta_recommendation`, and `tokens_budget` (with `generator` and `control` fields); the `id` field must be preserved verbatim from the input.
- The voice shall compute `net_concern` using the defined formula (`mean` of the four component scores, with `reversibility_score > 0.7` floored to `max(net_concern, reversibility_score)`) and document any unanchored score components in `notes`.
- The voice shall set `irreversibility_flag: true` for any candidate where `reversibility = irreversible` and explicit user consent is not documented in the input, signaling the aggregator to BLOCK before Generator runs.
- For any candidate with `net_concern >= 0.3`, the voice shall emit either a `rollback_recipe` (2–5 concrete human-executable steps) or, when rollback is structurally impossible, replace it with `mitigation_steps` and set `irreversible: true` at the candidate level.
- The mitigation cap (max two mitigations, total ≤ −0.20, second mitigation capped at −0.05 remaining budget) is discipline-based with no automated schema enforcement. Compliance is audited through `notes` documentation of applied mitigation values.
- When `meta_recommendation: "scale_down"` is set, the token budget is unconditionally overridden to 300 regardless of magnitude×reversibility. The Conservator's runtime judgment overrides pre-computed classifications; no floor exists for high/critical magnitude by design.

## WHAT — Verify intent (open questions for the human)
- None — doc is unambiguous.

## WHAT — Notes & known limitations (informative)

- The three irreversibility-related fields (`irreversibility_flag`, `irreversible`, `regression_risk.reversibility`) can coexist on the same candidate and carry different semantics; the prompt documents the distinction, but the overlap is a persistent source of confusion for readers and voice models alike.

## HOW — Acceptance (= tests)

AC-1
  Given a proposed change where `reversibility = irreversible` and no explicit user consent appears in the input
  When  the Conservator voice runs
  Then  the candidate's score entry has `irreversibility_flag: true`, and the aggregator-facing signal causes a BLOCK before Generator runs

AC-2
  Given a candidate scored with `net_concern >= 0.3` and a structurally possible rollback
  When  the Conservator voice runs
  Then  the candidate's score entry contains a `rollback_recipe` array with 2–5 non-abstract, human-executable steps; `irreversible` is absent or `false`

AC-3
  Given a candidate scored with `meta_recommendation: "scale_down"`
  When  the Conservator voice runs
  Then  `tokens_budget.generator` and `tokens_budget.control` are both 300, regardless of the magnitude×reversibility table value

## WHERE — Current implementation

- prompts/voices/conservator.md
