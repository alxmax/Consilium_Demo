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
- The 'quality-progress path' is defined solely in the lens prompt (`architect_lens.md`), not in the Conservator voice contract; it refers to adjusting `regression_risk` upward when test coverage is weak relative to the change's scope.
- 'Ranking higher' is achieved by the voice shifting its qualitative judgment of which candidate is structurally sounder; no raw numerical score is changed by the lens — aggregator re-weighting (via personality weights in `personalities.py`) translates that judgment into the final ranking.
- When Architect is applied to Conservator, the lens can affect which candidate Conservator prefers (lower `regression_risk` on one candidate makes it preferred), but the mechanism is constrained to the quality-progress adjustment on `regression_risk` — not a direct `risk_score` inflation.

## WHAT — Verify intent (open questions for the human)
- None - all questions resolved.

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

## Why test_exempt

This file is a personality-lens overlay — plain text prepended to a core voice prompt at runtime by `personalities.py` for Trias mode. It contains no executable Python logic. The lens content cannot be unit-tested because its effect is the model's contextual shift in reasoning, which is non-deterministic. Conformance is validated through Trias deliberation integration runs.
