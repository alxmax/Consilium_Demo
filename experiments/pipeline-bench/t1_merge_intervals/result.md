# T1 result — merge_intervals

Run: 2026-05-24. Both arms: fresh Sonnet sub-agents, same spec (`spec.md`), neither saw the oracle.

## Oracle outcome (hidden, 10 deterministic tests)

| Arm | Mechanism | Oracle pass | Tokens | Tool uses | Wall-clock |
|---|---|---|---|---|---|
| A — baseline | single-shot implement | **10/10** | 17,261 | 1 | 7.8 s |
| B — pipeline | coder→tests→review+gate | **10/10** | 18,738 | 5 | 27.9 s |

Cost ratio B/A: **1.09× tokens, ~3.6× wall-clock, 5× tool-uses.**

## Reading (per decision rule)

Correctness **tie** (10 = 10) at **higher cost** → by the pre-registered rule this task favors **KILL**.
The two arms produced **byte-identical** algorithms — for a well-specified edge-heavy pure function the
pipeline added nothing but overhead.

## Honest caveat — T1 under-exercised the hypothesis

The pipeline's value claim is "test-writing surfaces edges the baseline *misses*." T1's trap (touching
intervals merge) was **explicit in the spec**, so the baseline handled it directly — there was no missed
edge for the pipeline to catch. This is a fair data point (the pipeline didn't help where it shouldn't),
but it does not yet test the regime where the pipeline *should* win.

**Design lesson for T2/T3:** the implicit constraint must be a *logical consequence* of the spec that a
hasty implementer drops (a hidden invariant under sequences; a regression of an existing guarantee) —
not a rule written verbatim in the spec. Otherwise the baseline trivially ties. T2 (stateful invariant)
and T3 (no-regression bugfix) are designed for exactly this; they carry the real signal.

## Verdict so far

1 of 3 tasks. Running tally: pipeline **0 wins / 1 tie** on correctness, behind on cost. Continue to
T2 + T3 before applying the graduate/kill rule (needs ≥2/3 correctness wins to graduate).
