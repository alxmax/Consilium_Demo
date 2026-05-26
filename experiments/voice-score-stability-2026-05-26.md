# Voice Score Stability Experiment — 2026-05-26

**Follows up:** `experiments/voice-score-stability-2026-05-17.md`
**Open gaps closed here:** #1-D (Generator + Control stability), partial #1-C (ambiguous input instability).
**F4 gap status:** still open — veto-threshold region [0.7, 0.9] not probed (see below).

## Design

Two paired runs per input, dispatched independently via `consilium-subagent` (sequential mode, sonnet).
Comparison via `python scripts/stability_check.py --compare` (extended in PR #223 to include categorical fields).

### Pair A — unambiguous input
Change the veto condition in `aggregator.py` from exclusive (`>`) to inclusive (`>=`) at 0.8.
1-char diff, 1 file, documented behavior change. Expected: low conservator score.

### Pair B — ambiguous input
Architectural decision: choose the subagent architecture for Consilium's Step 7 code-development pipeline
(single-shot Coder vs Refiner pass vs Parallel Coders vs spec-only vs do_nothing).
Multiple plausible options with close scores. Expected: higher variance.

## Results

### Pair A (unambiguous)

```
generator  : A=1.000  B=1.000  diff=0.000  pstdev=0.000
control    : A=1.000  B=0.950  diff=0.050  pstdev=0.025
conservator: A=0.150  B=0.180  diff=0.030  pstdev=0.015
mean pstdev: 0.013 → Bug #1 OK (≤ 0.10)

Categorical (chosen=make_inclusive in both runs):
  magnitude    : A=moderate  B=moderate  OK
  reversibility: A=complete  B=complete  OK

chosen_approach: A=make_inclusive (conf=0.713)  B=make_inclusive (conf=0.724)
```

### Pair B (ambiguous)

```
generator  : A=0.500  B=1.000  diff=0.500  pstdev=0.250  *** HIGH VARIANCE
control    : A=1.000  B=1.000  diff=0.000  pstdev=0.000
conservator: A=0.100  B=0.280  diff=0.180  pstdev=0.090
mean pstdev: 0.113 → Bug #1 CONFIRMED (> 0.10)

Categorical (chosen differs between runs):
  magnitude    : A=trivial  B=moderate  *** FLIP
  reversibility: A=complete  B=complete  OK

chosen_approach: A=do_nothing (conf=0.45)  B=single_shot_coder (conf=0.655)
```

### Raw scores per voice

| Pair | Voice | A | B | pstdev |
|---|---|---|---|---|
| A | generator | 1.000 | 1.000 | 0.000 |
| A | control | 1.000 | 0.950 | 0.025 |
| A | conservator | 0.150 | 0.180 | 0.015 |
| B | generator | 0.500 | 1.000 | **0.250** |
| B | control | 1.000 | 1.000 | 0.000 |
| B | conservator | 0.100 | 0.280 | 0.090 |

## Findings

### F1 — Wittgenstein's asymmetry confirmed on ambiguous inputs (#1-D closed)

Generator shows HIGH VARIANCE on ambiguous input (pstdev=0.250). Control is stable in both pairs (pstdev=0.000 for control).
On unambiguous input, all three voices are stable.

**Interpretation:** Wittgenstein's 2026-05-17 asymmetry claim was "Generator/Control are unanchored, Conservator is formula-anchored." This experiment confirms the Generator side: when the input has multiple valid framings, Generator assigns wildly different scores (0.5 vs 1.0) to the same candidates. Control is not formula-anchored but appears to apply a more deterministic verification logic — its stability is structural, not formula-based.

### F2 — Categorical flip on ambiguous input is caused by chosen-candidate divergence, not within-candidate scoring noise

In Pair B, the magnitude flip (trivial vs moderate) occurs because the two runs chose **different candidates** (do_nothing vs single_shot_coder), not because Conservator scored the same candidate differently. This is a deeper instability than the 2026-05-17 MED/HIGH cases, where categorical flips occurred on the same chosen candidate.

**Interpretation:** When confidence is low (0.45 / 0.655) and candidate scores are close, the aggregation is coin-flip territory. The categorical labels and downstream metrics are artifacts of which candidate won, not independent measurements.

### F3 — Low-confidence + low-separation = structurally unstable decision

Pair B: confidence 0.45 vs 0.655 (delta 0.205). Score separation in B1 was 0.09 (do_nothing=0.768 vs refiner_pass=0.667); in B2 was 0.116 (single_shot_coder=0.791 vs do_nothing=0.677). These are sub-skeptic-trigger range separations.

**Implication:** the `skeptic_on_chosen` auto-trigger band (confidence ∈ [0.5, 0.7]) is well-positioned. B1 at conf=0.45 is BELOW the trigger band — the current system would not trigger skeptic for conf < 0.5. This is a gap: the most unstable regime (conf < 0.5, separation < 0.12) is currently unguarded.

### F4 — Veto threshold region [0.7, 0.9] still unprobed

Neither pair produced conservator voice scores in [0.7, 0.9]:
- Pair A: conservator=0.15 / 0.18 (chosen=make_inclusive, low-risk change)
- Pair B: conservator=0.10 / 0.28 (chosen=do_nothing / single_shot_coder, both low-risk)

The `stability_check.py --pick 5` tool finds candidates by `|voice_scores.conservator - 0.8|`, but `voice_scores.conservator` is derived from the **chosen candidate's net_concern** — not the overall question risk. A question with a safe chosen approach will always have low conservator score regardless of how dangerous the rejected alternatives were. F4 requires constructing cases where the WINNING candidate itself has net_concern ∈ [0.7, 0.9].

## Implications for action items

### Immediately actionable (no new experiments needed)

1. **Extend `skeptic_on_chosen` trigger band to conf < 0.5** (currently only [0.5, 0.7]).
   The most unstable regime (Pair B B1 at conf=0.45) is currently unguarded. Low cost: 1-line change in `modes/skeptic_on_chosen.md` + SKILL.md.

2. **Add low-separation warning to aggregator output.**
   When `ranking[0].score - ranking[1].score < 0.12`, emit a `low_separation: true` flag. Orchestrators can use this to decide whether to double-sample or escalate to dialectic.

### Requires new experiment (F4 gap)

3. **Probe F4: construct 2-3 cases with chosen-candidate net_concern ∈ [0.7, 0.9].**
   Candidates: changes that are both high-magnitude AND complete-reversibility (so Conservator scores high but doesn't flag irreversible). Example: "Remove the `majority` scheme from aggregator.py entirely" (affects all future deliberations, git-revertible).

### Already implemented

- #1-B: `stability_check.py --compare` now reports categorical flip (PR #223, merged).
- SKILL.md Step 2: 40% flip-rate caveat added.

## Run files

| File | Role |
|---|---|
| `.consilium/runs/2026-05-26_stability_A1_veto-inclusive.json` | Pair A run 1 |
| `.consilium/runs/2026-05-26_stability_A2_veto-inclusive.json` | Pair A run 2 |
| `.consilium/runs/2026-05-26_stability_B1_coder-arch.json` | Pair B run 1 |
| `.consilium/runs/2026-05-26_stability_B2_coder-arch.json` | Pair B run 2 |

## Cost

- 4 `consilium-subagent` dispatches (sequential mode, sonnet)
- Approximate tokens: ~400K total (subagent overhead included)
- Wall clock: ~35 minutes (pairs dispatched in parallel within each round)
