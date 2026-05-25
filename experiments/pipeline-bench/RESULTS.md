# Pipeline vs plain Step 7 — benchmark results (kill-criterion)

Protocol: `../pipeline-vs-step7-benchmark-spec.md`. Both arms = fresh Sonnet sub-agents,
shared Consilium spec per task, scored by a hidden deterministic oracle neither arm saw.

## Scoreboard — Round 1 (2026-05-24)

| Task | Regime | Arm A (single-shot) | Arm B (pipeline) | Correctness | Cost (tok / wall) |
|---|---|---|---|---|---|
| T1 merge_intervals | greenfield, edge-heavy | 10/10 | 10/10 | **tie** | 1.09× / 3.6× |
| T2 LRUCache | greenfield, hidden invariant | 8/8 | 8/8 | **tie** | 1.13× / 4.5× |
| T3 normalize+clip_floor | **refactor / regression trap** | 7/8 ❌ | 8/8 ✅ | **pipeline wins** | 1.14× / 6.6× |

R1 tally: pipeline **1 win / 2 ties / 0 losses**.

## Scoreboard — Round 2 (2026-05-25, refactor-only re-test)

All 3 R2 tasks are in the refactor/regression-trap regime (same pattern as T3).

| Task | Regime | Arm A (single-shot) | Arm B (pipeline) | Correctness | Notes |
|---|---|---|---|---|---|
| T4 normalize_weights+scale | refactor / algebraic extension | 8/8 ✅ | 8/8 ✅ | **tie** | Trap not activated — algebraically obvious |
| T5 weighted_average+default | refactor / trivial substitution | 9/9 ✅ | 9/9 ✅ | **tie** | Not a regression trap; 1-line change |
| T6 compute_histogram+normalize | refactor / early-return trap | 8/8 ✅ | 8/8 ✅ | **tie** | ⚠ arm A prompt compromised (see T6/result.md) |

R2 tally: pipeline **0 wins / 3 ties / 0 losses**.

## Combined verdict (R1 + R2, n=6)

| All tasks | Refactor-regime only |
|---|---|
| 1 win / 5 ties / 0 losses | 1 win / 3 ties / 0 losses (T3/T4/T5/T6) |

**Graduation criterion NOT met:** ≥2/3 wins required; observed 1/6 overall, 1/4 refactor-specific.

## Why R2 did not replicate R1's win

R2 revealed that the pipeline's value (Reviewer catching secondary code paths) is **task-regime
sensitive** — not all "refactor" tasks qualify:

- **T4 (algebraic-obvious):** The secondary path formula `[1/n]*n → [scale/n]*n` is a direct
  algebraic substitution. The model slots in `scale` without semantic reasoning. Not a trap.
- **T5 (trivial substitution):** A single `return 0.0 → return default` is a 1-line mechanical
  change. There is no secondary path analysis. Not a regression trap at all.
- **T6 (design flaw):** T6 has T3-pattern structure (two semantically-isolated early returns) but
  the arm A prompt explicitly enumerated the early-return constraints. This broke the fairness
  control. Result is not valid evidence.

**The precise qualifying condition for pipeline value** (from T3 data + R2 elimination):
> The secondary code path must return a value that is *semantically isolated* from the new
> parameter — i.e., the return value feels "complete" without the parameter applied to it, and
> the connection requires semantic reasoning rather than algebraic substitution.

In T3: `return [0.0]*n` in the all-equal branch feels semantically complete ("all-equal → 0.0
normalized"). clip_floor only applies via semantic reasoning (clip_floor post-processes normalized
values; this branch exits before normalization, but the guarantee should still hold).

## Updated recommendation

1. **KEEP the pipeline as EXPERIMENTAL_DRAFT, opt-in only.** Graduation is blocked — the win rate
   does not hold broadly in the refactor regime.
2. **The narrowed qualifying pattern is:** code changes to existing functions with:
   - Multiple code paths (at least one early return)
   - The early return value is semantically isolated from the new parameter
   - Connecting them requires semantic reasoning (not formula substitution)
3. **T6 should be re-run** with a corrected arm A prompt (spec.md verbatim, no constraint hints)
   to get clean evidence on the early-return-trap pattern.
4. **Kill the blanket "any refactor" claim** — algebraically-obvious changes and trivial
   substitutions do not benefit from the pipeline overhead (~1.1× tokens, ~4–6× wall-clock).

## Honesty caveats

- n=6 total (n=4 refactor-regime); same operator ran both arms; mitigated by deterministic oracle.
- Cost figures are token estimates, not billed dollars; wall-clock multiplier is large.
- T6 result is not valid evidence (arm A prompt compromised). Effective refactor-regime n=3 (T3/T4/T5).
- The "semantically isolated" condition is post-hoc reasoning from the data, not a pre-registered
  criterion. It should be treated as a hypothesis to test, not a proven characterization.
