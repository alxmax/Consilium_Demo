---
id: CONSILIUM-LENS-PIONEER-001
status: baseline
layer: feature
owner: auto
depends_on: [CONSILIUM-PERSONALITIES-001]
---

# pioneer lens

> WHY: biases all three voices toward boldness and upside — tolerating moderate risk and favoring novel, forward-moving solutions over safe, conservative ones.

## WHAT — Contract (normative)
- The lens shall cause the voice it overlays to weight creative potential and forward momentum more heavily than it would by default, preferring ambitious candidates over safe ones when the two are otherwise comparable.
- The lens shall preserve each voice's standard structural role (Generator produces candidates, Control verifies correctness, Conservator assesses risk); it shifts perception and priority without suppressing the role's core output.
- When applied to Conservator, the lens shall affect only magnitude calibration and meta-recommendation; it shall not directly alter the numerical `net_concern` formula or its component scores (`risk_score`, `regression_risk`, etc.).

## WHAT — Verify intent (open questions for the human)
- Observed: the phrase "when in doubt between safe and ambitious, prefer ambitious" applies across all three voices uniformly, including Conservator, which is explicitly risk-focused. The Conservator carve-out partially limits this, but "prefer ambitious" may still affect Conservator's narrative and meta_recommendation in ways that undermine Trias balance. Intended, or should the carve-out be broadened?

## HOW — Acceptance (= tests)
AC-1
  Given  a set of candidates evaluated under Trias, one clearly novel and higher-risk, one safe and incremental
  When   the Pioneer lens is prepended to a core voice
  Then   the voice's chosen or most-favored candidate is the novel/ambitious option rather than the safe/incremental one

AC-2
  Given  the Pioneer lens applied to the Conservator voice
  When   the Conservator produces its risk assessment
  Then   the `net_concern` numerical value reflects the standard formula unchanged, while the `meta_recommendation` or magnitude label may reflect a more tolerant stance toward the ambitious candidate

## WHERE — Current implementation
- prompts/voices/pioneer_lens.md
