---
id: CONSILIUM-LENS-STEWARD-001
status: baseline
layer: feature
owner: auto
depends_on: [CONSILIUM-PERSONALITIES-001]
---

# steward lens

> WHY: biases all three voices toward minimal-scope, reversible changes — prioritizing blast-radius reduction and protection of working systems over novelty or ambition.

## WHAT — Contract (normative)
- The lens shall cause the voice it overlays to weight reversibility, minimal scope, and regression safety more heavily than it would by default, preferring smaller safe changes over larger ambitious ones when both are viable.
- The lens shall preserve each voice's standard structural role; it shifts candidate ordering and priority without suppressing the full candidate set or altering the role's core output format.
- When applied to Generator, the lens shall order candidates by smallest blast radius first but shall still produce the full required spread of candidates (3–5); it shall not suppress high-blast-radius candidates from the output.

## WHAT — Verify intent (open questions for the human)
- Observed: "prefer existing patterns over new ones unless the new one is clearly necessary" leaves "clearly necessary" undefined, which may produce inconsistent behavior across different voices and evaluators. Is there a threshold (e.g., existing pattern is insufficient vs. merely suboptimal) that clarifies when a new pattern qualifies?

## HOW — Acceptance (= tests)
AC-1
  Given  two candidates — one minimal-scope and easily reversible, one larger in blast radius and harder to roll back
  When   the Steward lens is prepended to a core voice
  Then   the voice ranks or selects the minimal-scope, reversible candidate as preferred

AC-2
  Given  the Steward lens applied to the Generator voice
  When   Generator produces its candidate list
  Then   the list contains the full required number of candidates (no suppression of ambitious options), with minimal-blast-radius candidates listed first

## WHERE — Current implementation
- prompts/voices/steward_lens.md
