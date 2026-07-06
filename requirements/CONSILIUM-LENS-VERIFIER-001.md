---
milestone: v1.1
test_exempt: "prompt/mode document — acceptance validated by deliberation integration runs, not unit tests"
id: CONSILIUM-LENS-VERIFIER-001
status: confirmed
layer: feature
owner: auto
depends_on: [CONSILIUM-PERSONALITIES-001]
---

# verifier lens

> WHY: control-heavy member of the Trias personality team — biases all three voices toward operational clarity: vague claims must be replaced with verifiable criteria, and candidates with checkable success signals are preferred over comparable ones whose success is a matter of opinion.

## WHAT — Contract (normative)
- The lens shall cause the voice it overlays to replace vague quality terms with testable criteria and to name, per candidate, the signal distinguishing working from silently-not-working.
- The lens shall preserve each voice's standard structural role; it shifts perception and priority without suppressing the role's core output.
- When applied to Control, demanding testability shall not stall the verdict: an unverifiable claim lowers confidence and becomes a named condition — it is not an automatic BLOCK, and no unbounded evidence may be demanded before ruling.
- When applied to Conservator, the lens shall affect only magnitude calibration and meta_recommendation; it shall not shift the `net_concern` numerical formula because a claim is merely well-phrased.
- The lens is the control-heavy Trias personality (weights generator 0.30 / control 0.40 / conservator 0.30) and is one of the three fixed personalities the Trias team dispatches.

## WHAT — Verify intent (open questions for the human)
- None - all questions resolved.

## HOW — Acceptance (= tests)
AC-1
  Given  two otherwise comparable candidates, one with a checkable success criterion and one whose benefit is stated in vague terms
  When   the Verifier lens is prepended to a core voice
  Then   the voice's chosen or most-favored candidate is the one with the checkable criterion

AC-2
  Given  the Verifier lens applied to the Control voice and a chosen candidate carrying an unverifiable claim
  When   Control produces its verdict
  Then   the verdict is still issued, with the unverifiable claim surfaced as a named condition or confidence reduction rather than an automatic BLOCK

## WHERE — Current implementation
- prompts/voices/verifier_lens.md

## Why test_exempt

This file is a personality-lens overlay — plain text prepended to a core voice prompt at runtime by `personalities.py` for Trias mode. It contains no executable Python logic; conformance is validated through Trias deliberation integration runs. Deterministic guards (frontmatter + bias-keyword signature) live in scripts/test_lens_bias.py.
