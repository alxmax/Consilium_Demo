---
test_exempt: "prompt/mode document — acceptance validated by deliberation integration runs, not unit tests"
id: CONSILIUM-LENS-ARCHITECT-001
status: confirmed
layer: feature
owner: auto
depends_on: [CONSILIUM-PERSONALITIES-001]
---

# architect lens

> WHY: biases all three voices toward structural soundness, test coverage, and long-term maintainability over short-term speed or external novelty.

## WHAT — Contract (normative)
- The lens shall cause the voice it overlays to weight architectural cleanliness, type safety, clear abstractions, and test verifiability more heavily than it would by default, favoring candidates that strengthen invariants over those that loosen them.
- The lens shall preserve each voice's standard structural role; it shifts evaluation priorities without replacing the role's core output or inflating/deflating raw numerical scores directly.
- When applied to Conservator, the lens shall affect only the quality-progress adjustment on ; it shall not inflate  solely on the basis of absent tests.
- The lens operates as an absolute structural constraint within its voice layer; trade-off judgments between architectural integrity and pragmatic speed are delegated to the multi-voice aggregator (democratic vote across Personality trio), not internalized in Architect's reasoning. There is no internal threshold for accepting pragmatic shortcuts — that balance is handled at aggregation.

## WHAT — Verify intent (open questions for the human)
- None — doc is unambiguous.

## HOW — Acceptance (= tests)
AC-1
  Given  two candidates — one well-structured with full test coverage, one faster to ship but with weaker abstractions and no new tests
  When   the Architect lens is prepended to a core voice
  Then   the voice ranks the well-structured, well-tested candidate higher regardless of implementation speed

AC-2
  Given  the Architect lens applied to the Conservator voice and a candidate with no new tests
  When   the Conservator produces its risk assessment
  Then   the  component may be adjusted upward via the quality-progress path, but  is not inflated solely because tests are absent

## WHERE — Current implementation
- prompts/voices/architect_lens.md
