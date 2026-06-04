---
test_exempt: "prompt/mode document — acceptance validated by deliberation integration runs, not unit tests"
id: CONSILIUM-LENS-PIONEER-001
status: confirmed
layer: feature
owner: auto
depends_on: [CONSILIUM-PERSONALITIES-001]
---

# pioneer lens

> WHY: biases all three voices toward boldness and upside — tolerating moderate risk and favoring novel, forward-moving solutions over safe, conservative ones.

## WHAT — Contract (normative)
- The lens shall cause the voice it overlays to weight creative potential and forward momentum more heavily than it would by default, preferring ambitious candidates over safe ones when the two are otherwise comparable.
- The lens shall preserve each voice's standard structural role (Generator produces candidates, Control verifies correctness, Conservator assesses risk); it shifts perception and priority without suppressing the role's core output.
- When applied to Conservator, the lens shall affect only magnitude calibration and meta_recommendation; it shall not directly alter the numerical  formula or its component scores (, , etc.).
- The Conservator carve-out is sufficient by design. Pioneer's influence is on narrative tone and meta_recommendation framing, not on the numerical risk gate. The  formula remains governed by Conservator's own logic, preserving Trias balance through democratic aggregation across all three voices.
- 'Magnitude calibration' means the `magnitude` label only (low/medium/high/critical); Pioneer shall not shift the `reversibility` component score or any other input to the `net_concern` formula.
- The Pioneer lens adds no additional pressure on `unconventional_*` candidate selection beyond what the Generator voice contract already requires.
- There is no defined minimum ambition gap for the lens to activate; when candidates differ in ambition, Pioneer always prefers the most ambitious one, even if the difference is marginal.

## WHAT — Verify intent (open questions for the human)
- None - all questions resolved.

## HOW — Acceptance (= tests)
AC-1
  Given  a set of candidates evaluated under Trias, one clearly novel and higher-risk, one safe and incremental
  When   the Pioneer lens is prepended to a core voice
  Then   the voice's chosen or most-favored candidate is the novel/ambitious option rather than the safe/incremental one

AC-2
  Given  the Pioneer lens applied to the Conservator voice
  When   the Conservator produces its risk assessment
  Then   the  numerical value reflects the standard formula unchanged, while the  or magnitude label may reflect a more tolerant stance toward the ambitious candidate

## WHERE — Current implementation
- prompts/voices/pioneer_lens.md
