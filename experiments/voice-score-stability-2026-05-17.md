# Voice Score Stability Experiment — 2026-05-17

**Source:** Senate top-5 diagnostic audit (`runs/senate/2026-05-17_161608-top5-diagnostic-audit.json`), item #1 — `voice_scores_treated_as_calibrated_measurements` (Socrate, CRITICAL). R2 from Wittgenstein + Dimon refined the claim:

- Wittgenstein: calibration *asymmetry* — Conservator IS anchored via `conservator.md:62-75` formula; Generator + Control are NOT.
- Dimon: predicts inter-run `pstdev` 0.12-0.18 on `risk_score`; veto threshold 0.8 sits in high-variance region; non-deterministic veto on boundary cases.

## Falsification design

Per Dimon's R2 proposal: pick 5 historical diffs covering the risk spectrum (low ~0.05, medium ~0.5, boundary-low ~0.68, boundary-high ~0.84, high ~0.92), re-dispatch each twice with identical input, measure `pstdev` per voice. If `mean(pstdev) > 0.10` on `net_concern` → Socrate's claim empirically confirmed.

## Scope concessions (read before interpreting)

This run **measures only the Conservator voice**, not the full sequential pipeline. The original design was to re-dispatch the `consilium-subagent` 10 times; mid-execution the subagent reported missing Bash tool permissions on some calls and the dispatch was aborted. The pivot was: dispatch only the Conservator voice as a `general-purpose` Agent with the `conservator.md` prompt inline + the case context, request a strict JSON output, measure inter-run variance on `regression_risk.net_concern`.

Consequences of the pivot:
- We measure **only Conservator variance**, not Generator/Control. Wittgenstein's asymmetry claim (Gen/Ctrl are less anchored than Conservator) is **not tested** here.
- We measure **scoring stability**, not **chosen-flip stability**. Without Generator+Control voting, we can't say whether the score variance would flip the eventual `chosen_approach`.
- The veto-threshold-near-0.8 high-variance region (Dimon's main claim) is **not probed empirically** — none of our 5 cases produced `net_concern ≥ 0.5`. We hit ceiling 0.42 on BOUNDARY_HI.

## Cases

| Case | Source run | Risk level (historical cons score) | Candidates scored |
|---|---|---|---|
| LOW | `2026-05-12_1820_progress-voices-selfreview` | 0.05 | `do_nothing` vs `apply_3_edits` |
| MED | `2026-05-17_1500_todo-conservator-edits` | 0.50 | `do_nothing` vs `ship_conservator_edits` |
| BOUNDARY_LO (BLO) | `2026-05-17_1130_arch-html-refactor` | 0.68 | `do_nothing` vs `c4_consolidate_tabs` |
| BOUNDARY_HI (BHI) | `2026-05-15_2347_did-modes-think` | 0.84 | `do_nothing` vs `H_parallel_observations` |
| HIGH | `2026-05-11_1500_parallel-voices` | 0.92 | `do_nothing` vs `opt_in_section` |

For each case, two paired runs (A and B) with **identical input prompts** dispatched in parallel as `general-purpose` Agents using `claude-sonnet-4-6`.

## Results

### Per-pair: chosen-candidate `net_concern`

| Case | A.net_concern | B.net_concern | \|Δ\| | pstdev | reversibility flip | magnitude flip |
|---|---|---|---|---|---|---|
| LOW | 0.38 | 0.35 | 0.030 | 0.015 | — | — |
| MED | 0.18 | 0.38 | **0.200** | **0.100** | **FLIP** (complete → partial) | **FLIP** (trivial → moderate) |
| BLO | 0.38 | 0.40 | 0.020 | 0.010 | — | — |
| BHI | 0.42 | 0.42 | 0.000 | 0.000 | — | — |
| HIGH | 0.28 | 0.15 | **0.130** | **0.065** | — | **FLIP** (moderate → trivial) |

- Mean `pstdev` across 5 pairs: **0.038**
- Max `pstdev`: **0.100** (MED)

### Stability of the safe baseline (`do_nothing`)

Across all 10 runs, `do_nothing.net_concern`:

- Values: `[0.15, 0.15, 0.15, 0.12, 0.15, 0.15, 0.15, 0.15, 0.12, 0.15]`
- Mean: 0.144 · pstdev: **0.012** (very tight)

### Categorical flip rate (same input → different category)

| Field | Flips | Rate |
|---|---|---|
| reversibility | 1 / 5 pairs | 20% |
| magnitude | 2 / 5 pairs | **40%** |

### Meta-recommendation variance

| Case | A | B | Agreement |
|---|---|---|---|
| LOW | `scale_down` | `null` | DISAGREE |
| MED | `null` | `null` | agree |
| BLO | `null` | `scale_down` | DISAGREE |
| BHI | `scale_down` | `scale_down` | agree |
| HIGH | `null` | `null` | agree |

2/5 pairs disagree on whether `meta_recommendation` should fire.

## Findings

### F1 — Numerical stability of `net_concern` is BETTER than Dimon predicted

Mean `pstdev` = 0.038 across the 5 pairs, max = 0.10. Dimon's R2 prediction (0.12-0.18) is **refuted** for the cases sampled. Within a stable categorical assignment, Conservator's formula produces tight numerical output (Δ ≤ 0.03 in 3/5 pairs; identical to 2 decimal places in 1 pair).

**Interpretation:** the formula IS providing anchoring, exactly as Wittgenstein's R2 noted (`conservator.md:62-75` maps categorical labels to fixed sub-scores). When category assignments agree, the float output agrees.

### F2 — But categorical assignment is NOT stable (40% magnitude flip rate)

In 2 of 5 paired runs, the SAME input produced DIFFERENT magnitude categorizations. In MED, both magnitude AND reversibility flipped together, yielding the largest numerical delta (0.18 → 0.38). In HIGH, magnitude flipped from `moderate` → `trivial`, yielding Δ = 0.13.

**Interpretation:** the real noise is **upstream of the formula**, in the Q1-Q5 categorical assignment phase. The formula is deterministic given inputs, but the inputs themselves are model-generated categorical judgments that vary across identical prompts.

### F3 — `do_nothing` baseline is extremely stable (pstdev 0.012)

When the candidate is unambiguous (`do_nothing` = no change → trivial + complete by definition), agreement is near-perfect: 8/10 runs at exactly 0.15, 2/10 at 0.12. The remaining variance is at the noise floor of the model's output precision.

**Interpretation:** Conservator scoring is stable for clearly-categorized candidates. It's the ambiguously-categorized changes (moderate-vs-trivial boundary, complete-vs-partial boundary) where assignment flips occur.

### F4 — Veto threshold region (0.8) is UNTESTED

None of the 5 cases produced `net_concern ≥ 0.5`. Ceiling was 0.42 on BOUNDARY_HI. **Dimon's main claim** — that the veto threshold of 0.8 sits in the high-variance region and would fire non-deterministically on boundary cases — **remains untested** by this experiment. We need cases that ACTUALLY produce high `net_concern` for both pair members to probe the veto behavior.

### F5 — Meta-recommendation is noisier than `net_concern` itself

`meta_recommendation` disagrees in 2/5 pairs (40% rate), matching the categorical flip rate. This matters because `aggregate_rund2()` keys behavior off `meta_recommendation` (`scale_up`, `scale_down`, `null`) — same input could trigger different deliberation paths.

## Implications for action items

The original AC for #1 said "add inter-run stability check (run identical input twice; flag if stdev > 0.15) before authoritative veto." Based on this experiment, that AC needs refinement:

- **Drop the `pstdev > 0.15` check on `net_concern`.** Numerical variance is well below that for typical cases (max observed: 0.10). The check would never fire and would waste tokens.
- **Add a categorical-stability check instead.** Sample Conservator twice; if `reversibility` or `magnitude` categories disagree, surface the categorical disagreement to the orchestrator (don't auto-resolve). This catches the 40% flip rate at its source.
- **Probe the veto-threshold region separately.** Construct or find 2-3 cases with `net_concern` in [0.7, 0.9] and re-run this experiment. Until that data exists, Dimon's non-deterministic-veto claim is plausible but unconfirmed.
- **Generator + Control stability are still untested.** This experiment isolated Conservator. If Wittgenstein's asymmetry claim is right, Generator+Control should show MORE variance than Conservator (no formula anchor). Open question for future experiments.

## Suggested SKILL.md edits (separate PR)

Per refined AC from #1 R2 — document the calibration asymmetry without rebuilding the formula:

1. In Step 5 (Aggregate), add a brief note: "Voice scores are model estimates with explicit calibration only on the Conservator side (`conservator.md` formula). Generator and Control scores are uncalibrated; treat thresholds as advisory, not authoritative."
2. In the aggregator's `conservative_override` scheme description, add a sentence: "The 0.8 veto threshold has not been empirically validated in the 0.7-0.9 region — boundary cases may fire non-deterministically until a follow-up stability experiment closes that gap."

## Cost summary

- 10 sub-agent dispatches (Conservator only) × `sonnet`
- Token usage per dispatch: ~15K (visible to orchestrator); aggregate ~150K tokens (subagent + orchestrator overhead)
- Wall clock: ~3 minutes total (all 10 dispatched in parallel; first returned at ~13s, last at ~22s)
- Bug encountered (and worked around): consilium-subagent dispatch reported missing Bash permissions on 2 of 10 calls; aborted and pivoted to general-purpose agent with inline Conservator prompt.

## Raw data

Pairs by case, format `(net_concern, reversibility, magnitude, meta_recommendation)`:

```
LOW  A: (0.38, complete, moderate, scale_down)
LOW  B: (0.35, complete, moderate, null)
MED  A: (0.18, complete, trivial,  null)
MED  B: (0.38, partial,  moderate, null)
BLO  A: (0.38, partial,  moderate, null)
BLO  B: (0.40, partial,  moderate, scale_down)
BHI  A: (0.42, partial,  moderate, scale_down)
BHI  B: (0.42, partial,  moderate, scale_down)
HIGH A: (0.28, complete, moderate, null)
HIGH B: (0.15, complete, trivial,  null)
```
