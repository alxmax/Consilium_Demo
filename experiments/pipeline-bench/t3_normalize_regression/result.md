# T3 result — normalize_scores + clip_floor (regression trap)

Run: 2026-05-24. Both arms started from `start/solution.py` + `start/existing_tests.py`, same change
request; neither saw the oracle.

## Oracle outcome (hidden, 8 tests: 3 existing guarantees + 2 regression-under-new-param + 3 feature)

| Arm | Mechanism | Oracle pass | Tokens | Tool uses | Wall-clock |
|---|---|---|---|---|---|
| A — baseline | single-shot implement | **7/8** ❌ | 17,469 | 1 | 7.6 s |
| B — pipeline | coder→tests→review+gate | **8/8** ✅ | 19,870 | 7 | 49.8 s |

## The defect the pipeline caught (and the baseline shipped)

Both arms applied `clip_floor` correctly on the normal path (`max(clip_floor, (s-lo)/span)`). But the
**all-equal branch** (`span == 0`) is a separate code path:

- **Arm A:** `return [0.0 for _ in scores]` — silently ignores `clip_floor`.
  `normalize_scores([5,5,5], clip_floor=0.2)` → `[0.0,0.0,0.0]` (oracle expects `[0.2,0.2,0.2]`). **Fails.**
- **Arm B:** the Reviewer flagged that the all-equal path ignores the new parameter →
  `return [max(0.0, clip_floor) for _ in scores]`. **Passes.** (Arm B's own report explicitly named this catch.)

This is the pipeline's value mechanism working exactly as designed: a second code path that the
happy-path change missed, surfaced by writing/running tests + reviewing against the full contract.

## Reading

Pipeline **wins** correctness here (8 vs 7) at ~1.14× token / ~6.6× wall-clock cost. The win is real
and concentrated in the **regression/refactor regime** — a behavior change to existing code with a
second branch that the naive edit overlooks.
