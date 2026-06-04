---
test_exempt: "prompt/mode document — acceptance validated by deliberation integration runs, not unit tests"
id: CONSILIUM-LENS-ARCHITECT-001
status: baseline
layer: feature
owner: auto
depends_on: [CONSILIUM-PERSONALITIES-001]
---

# architect lens

> WHY: biases all three voices toward structural soundness, test coverage, and long-term maintainability over short-term speed or external novelty.

## WHAT — Contract (normative)
- The lens shall cause the voice it overlays to weight architectural cleanliness, type safety, clear abstractions, and test verifiability more heavily than it would by default, favoring candidates that strengthen invariants over those that loosen them.
- The lens shall preserve each voice's standard structural role; it shifts evaluation priorities without replacing the role's core output or inflating/deflating raw numerical scores directly.
- When applied to Conservator, the lens shall affect only the quality-progress adjustment on `regression_risk`; it shall not inflate `risk_score` solely on the basis of absent tests.

## WHAT — Verify intent (open questions for the human)
- Observed: "internal consistency > external speed" and "long-term maintainability > short-term win" are stated as absolute priorities, with no threshold for when a short-term win is large enough to justify a structural compromise. Is the intent that Architect always rejects pragmatic shortcuts, or only when the structural cost is non-trivial?

## HOW — Acceptance (= tests)
AC-1
  Given  two candidates — one well-structured with full test coverage, one faster to ship but with weaker abstractions and no new tests
  When   the Architect lens is prepended to a core voice
  Then   the voice ranks the well-structured, well-tested candidate higher regardless of implementation speed

AC-2
  Given  the Architect lens applied to the Conservator voice and a candidate with no new tests
  When   the Conservator produces its risk assessment
  Then   the `regression_risk` component may be adjusted upward via the quality-progress path, but `risk_score` is not inflated solely because tests are absent

## WHERE — Current implementation
- prompts/voices/architect_lens.md
