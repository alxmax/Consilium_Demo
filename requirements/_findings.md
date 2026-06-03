# Open findings

> 14 open verify-intent item(s) across 10 requirement(s), aggregated from each requirement's `## WHAT — Verify intent` section by `reqmap.py findings`.
>
> These are open questions raised while reconstructing intent from code - NOT confirmed bugs. Resolve each by fixing the code or promoting the behavior into a Contract line. Run the AI triage pass (see SKILL.md) and drop a `_findings_triage.json` beside this file for a verified, prioritized view.

---

## CONSILIUM-LENS-ARCHITECT-001 - architect lens  (1)

- Observed: "internal consistency > external speed" and "long-term maintainability > short-term win" are stated as absolute priorities, with no threshold for when a short-term win is large enough to justify a structural compromise. Is the intent that Architect always rejects pragmatic shortcuts, or only when the structural cost is non-trivial?

## CONSILIUM-LENS-PIONEER-001 - pioneer lens  (1)

- Observed: the phrase "when in doubt between safe and ambitious, prefer ambitious" applies across all three voices uniformly, including Conservator, which is explicitly risk-focused. The Conservator carve-out partially limits this, but "prefer ambitious" may still affect Conservator's narrative and meta_recommendation in ways that undermine Trias balance. Intended, or should the carve-out be broadened?

## CONSILIUM-LENS-STEWARD-001 - steward lens  (1)

- Observed: "prefer existing patterns over new ones unless the new one is clearly necessary" leaves "clearly necessary" undefined, which may produce inconsistent behavior across different voices and evaluators. Is there a threshold (e.g., existing pattern is insufficient vs. merely suboptimal) that clarifies when a new pattern qualifies?

## CONSILIUM-MODE-DIALECTIC-001 - dialectic mode  (1)

- Observed: the spec states the Skeptic runs "not conditional on confidence band", yet `skeptic_on_chosen.md` describes auto-trigger conditions including `confidence ∈ [0.0, 0.7]`. In Dialectic, is the Skeptic always unconditional (ignoring the confidence band entirely), or does the same auto-trigger logic apply here too?

## CONSILIUM-MODE-SEQUENTIAL-001 - sequential mode  (1)

- Observed: the `confidence_floor: 0.70` in the frontmatter is not explicitly described as a post-aggregation gate in the prose — it is listed alongside the other mode metadata. Intended as a hard floor enforced before emitting the report, or purely informational?

## CONSILIUM-MODE-TRIAS-001 - trias mode  (1)

- Observed: the spec states parallel dispatch of the 3 personalities is "mandatory", but a Senate audit (2026-05-28) concluded serial dispatch is accepted as "by-construction-not-intent, not a bug to fix now" — the runtime audit observes it rather than enforcing it. Is the "mandatory" language still normative, or should the requirement reflect the accepted-serial reality?

## CONSILIUM-VOICE-CONSERVATOR-001 - conservator voice  (2)

- Observed: the mitigation cap rule (max two mitigations, total ≤ −0.20, second mitigation capped at −0.05 remaining budget) is described as "no automated check — keep it disciplined manually." This means there is no observable output field that records whether the cap was respected. Should the voice be required to emit the mitigations it applied (and their amounts) in `notes` so reviewers can audit compliance?
- Observed: `meta_recommendation: "scale_down"` overrides the token budget to 300 regardless of magnitude×reversibility. This can produce a 300-token budget for a `high + irreversible` candidate if the Conservator judges it trivial. Is that override unconditional by design, or should a floor exist for high/critical magnitude?

## CONSILIUM-VOICE-CONTROL-001 - control voice  (2)

- Observed: the prompt instructs Control to read files when it cannot verify a signature, but Control runs inside a single-context pipeline where it may not have tool access. The fallback (`mark category: "types", detail: "unverifiable — file not accessible"`) silently degrades confidence. Intended behavior, or should there be a harder signal when file access fails systematically?
- Observed: `hidden_assumptions` is capped at 3 entries, but the selection criterion ("only include assumptions where if false the answer changes") is self-assessed by the model. No external check exists on whether excluded assumptions actually were non-load-bearing. Is this intentional trust in the voice?

## CONSILIUM-VOICE-GENERATOR-001 - generator voice  (2)

- Observed: the prompt states the `unconventional_*` candidate can be skipped ONLY when `adversarial_*` varies on a non-scope axis — overlap on scope alone is not sufficient. This is a relatively subtle rule that could easily be misapplied, producing silent omission. Intended rule, or should it be simplified?
- Observed: the 0.5 generator-score handicap for `adversarial_*` and `do_nothing` is attributed to `build_report.py`, but the prompt lives in the voice file. This means the voice cannot self-verify whether the handicap will be applied. Is this cross-component dependency documented anywhere other than this prompt?

## CONSILIUM-VOICE-SKEPTIC-001 - skeptic voice  (2)

- Observed: when the validation gate fails, the skeptic output is "discarded and the chosen ships unchallenged" — there is no retry, no fallback, and no signal to the user that the skeptic was rejected. Is silent discard the intended behavior, or should a warning be surfaced in the final report?
- Observed: `meta_scope_mismatch` requires all three conditions (correct answer, trivially-human-resolvable, cost exceeds decision value) to hold simultaneously, but the voice self-assesses all three. No external oracle checks "resolvable in < 10 seconds." Is this trust in the voice by design?

