---
id: CONSILIUM-VOICE-SKEPTIC-001
status: baseline
layer: feature
owner: auto
depends_on: []
---

# skeptic voice

> WHY: The Skeptic performs a focused post-selection challenge on the single chosen candidate, providing the last line of defense against a correct-looking but concretely-flawed winner before it ships.

## WHAT — Contract (normative)

- The voice shall emit either `can_object: true` (with a populated `objection` object containing `concrete_concerns`, optional `quoted_scenario`, `failure_mode`, and `addressable`) or `can_object: false` (with `objection: null` and a one-sentence `notes` explaining the absence of objection); it shall never fabricate a concern that does not appear in `success_criterion` or stated context.
- When `can_object: true`, the voice shall supply at least 2 entries in `concrete_concerns` OR at least 1 non-null `quoted_scenario`; any output that meets neither threshold is rejected by the orchestrator's validation gate and discarded silently.
- The voice shall classify `failure_mode` as exactly one of `correctness`, `goal_fit`, `verification_inadequate`, or `meta_scope_mismatch`; if `failure_mode` is `goal_fit`, `concrete_concerns` must contain a direct quote or reference from `success_criterion`.
- The voice shall set `addressable` to `in_place`, `requires_redesign`, or `unaddressable`; `unaddressable` must be used only when no redesign can resolve the concern, defaulting to `in_place` for fixable issues.

## WHAT — Verify intent (open questions for the human)

- Observed: when the validation gate fails, the skeptic output is "discarded and the chosen ships unchallenged" — there is no retry, no fallback, and no signal to the user that the skeptic was rejected. Is silent discard the intended behavior, or should a warning be surfaced in the final report?
- Observed: `meta_scope_mismatch` requires all three conditions (correct answer, trivially-human-resolvable, cost exceeds decision value) to hold simultaneously, but the voice self-assesses all three. No external oracle checks "resolvable in < 10 seconds." Is this trust in the voice by design?

## WHAT — Notes & known limitations (informative)

- The validation gate is enforced by the orchestrator after the fact, not by the voice itself — a skeptic that emits invalid output does not know it was rejected, which makes it impossible for the voice prompt alone to guarantee compliant output without external enforcement.

## HOW — Acceptance (= tests)

AC-1
  Given the Skeptic receives a chosen candidate and can identify 2 specific, named concerns grounded in `success_criterion` or stated context
  When  the Skeptic voice runs
  Then  the output has `can_object: true`, `objection.concrete_concerns` contains at least 2 entries, and `objection.failure_mode` is one of the four enumerated labels

AC-2
  Given the Skeptic receives a chosen candidate with no concrete verifiable flaw
  When  the Skeptic voice runs
  Then  the output has `can_object: false`, `objection` is null, and `notes` contains a non-empty sentence explaining the absence of objection

AC-3
  Given the chosen candidate is technically correct but the problem is resolvable in under 10 seconds by a human without deliberation tooling
  When  the Skeptic voice runs
  Then  the output has `failure_mode: "meta_scope_mismatch"`, `addressable: "unaddressable"`, and `concrete_concerns` contains at least 2 entries describing the cost/benefit inversion of running the deliberation

## WHERE — Current implementation

- prompts/voices/skeptic.md
