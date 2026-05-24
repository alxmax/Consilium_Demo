# Pipeline vs plain Step 7 — benchmark results (kill-criterion)

Protocol: `../pipeline-vs-step7-benchmark-spec.md`. Run 2026-05-24. Both arms = fresh Sonnet sub-agents,
shared Consilium spec per task, scored by a hidden deterministic oracle neither arm saw.

## Scoreboard

| Task | Regime | Arm A (single-shot) | Arm B (pipeline) | Correctness | Cost (tok / wall) |
|---|---|---|---|---|---|
| T1 merge_intervals | greenfield, edge-heavy | 10/10 | 10/10 | **tie** | 1.09× / 3.6× |
| T2 LRUCache | greenfield, hidden invariant | 8/8 | 8/8 | **tie** | 1.13× / 4.5× |
| T3 normalize+clip_floor | **refactor / regression trap** | 7/8 ❌ | 8/8 ✅ | **pipeline wins** | 1.14× / 6.6× |

Correctness tally: pipeline **1 win / 2 ties / 0 losses**. Cost: ~1.1× tokens, ~3.6–6.6× wall-clock.

## Verdict (against the pre-registered rule)

The fixed rule was: **graduate iff correctness wins ≥2/3 AND cost ≤2×.** Wins = 1/3 → **the blanket
graduation bar is NOT met → the pipeline does not become default.** Per the rule, that is a kill for the
"pipeline as the default implement path" claim.

**But the data is not a blunt kill — it is a scoping signal.** The pipeline's win is real and entirely
in the **regression/refactor regime** (T3): the review+test step caught a second-code-path defect that
the single-shot shipped. In greenfield (T1, T2) the baseline Sonnet already nails edge-heavy and
hidden-invariant tasks, so the pipeline only added cost.

## Recommendation

1. **Do NOT wire the pipeline as the default `implement`.** For greenfield it pays ~1.1× tokens / 3–4×
   wall-clock for zero correctness gain (Constitution P2 — Simplicity first).
2. **KEEP it opt-in, scoped to its proven regime:** changes to *existing* code with regression risk
   (refactor / bugfix / behavior change with multiple code paths). That is where review+tests earn the cost.
3. **Re-test before any stronger claim.** n=3 (one win) is a pilot signal, not proof (Deming). Before
   promoting even the narrow use, add ≥3 more refactor-regime tasks and confirm the win rate holds.

## Honesty caveats

- n=3, same operator ran both arms; mitigated by deterministic hidden oracle + rule fixed before runs.
- Cost is token estimates, not billed dollars; wall-clock multiplier is large (3 sequential roles).
- T1/T2 arguably under-exercised the hypothesis (their traps were entailed by well-known contracts the
  base model already knows). T3 is the regime the pipeline was built for, and it delivered there.
