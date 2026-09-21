---
milestone: v1.0
test_exempt: "prompt/mode document — acceptance validated by deliberation integration runs, not unit tests"
id: CONSILIUM-VOICE-SKEPTIC-001
status: confirmed
level: code
layer: feature
owner: alxmax
depends_on: []
satisfies: [ARCH-CONSILIUM-VOICES-001]
---

# skeptic voice

> WHY: The Skeptic performs a focused post-selection challenge on the single chosen candidate, providing the last line of defense against a correct-looking but concretely-flawed winner before it ships.

## WHAT — Contract (normative)

- The voice emits either `can_object: true`, with a populated `objection` object, or `can_object: false`, with `objection: null` and a one-sentence `notes` explaining the absence of objection.
- The machine-checkable shape of the output is owned by [[CONSILIUM-VALIDATE-SKEPTIC-001]]: required fields, minimum evidence, allowed values. This requirement does not restate it.
- The voice never fabricates a concern that does not appear in `success_criterion` or stated context.
- The voice picks exactly one `failure_mode`, the one that names why the chosen candidate fails.
- The voice uses `addressable: unaddressable` only when no redesign can resolve the concern.
- Output that the validation gate rejects is discarded silently: the chosen candidate ships unchanged, no warning is emitted, and the base deliberation result stands as if the Skeptic had not run. This is a deliberate conservative fallback.
- `meta_scope_mismatch` is a self-assessed heuristic gate with no external oracle; all three conditions (correct answer, trivially-human-resolvable, cost exceeds decision value) are necessarily evaluated by the voice itself because they require contextual judgment that no deterministic external check can provide.

## WHAT — Verify intent (open questions for the human)
- None - all questions resolved. Silent discard is completely invisible: no log, no telemetry, no pipeline report entry (covered by Contract: "no warning is emitted"). `meta_scope_mismatch` uses `addressable: unaddressable` because the concern is not fixable by redesigning the candidate — the deliberation tool was wrong for the problem, not the answer; `unaddressable` refers to the tool-application level, not the human's ability to resolve the original question directly.

## WHAT — Notes & known limitations (informative)

- The validation gate is enforced by the orchestrator after the fact, not by the voice itself — a skeptic that emits invalid output does not know it was rejected.

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
  Then  the output has `failure_mode: "meta_scope_mismatch"`, `addressable: "unaddressable"`, and `concrete_concerns` contains at least 2 entries describing the cost/benefit inversion

## WHERE — Current implementation

- prompts/voices/skeptic.md

## Why test_exempt

This file is a prompt document — plain text read by the deliberation orchestrator or a sub-agent at runtime. It contains no executable Python logic; its "behavior" is the model's response to the text, which is non-deterministic and cannot be asserted in a repeatable unit test. Correctness is validated through deliberation integration runs stored in `.consilium/runs/` and manual review of real outputs, not by a stable `expected == actual` assertion.
