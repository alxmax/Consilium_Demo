# T4 result — normalize_weights + scale (refactor / parameter extension)

Run: 2026-05-25. Both arms started from `start/solution.py` + `start/existing_tests.py`, same change
request; neither saw the oracle.

## Oracle outcome (hidden, 8 tests: 4 existing guarantees + 2 regression-under-new-param + 2 feature)

| Arm | Mechanism | Oracle pass | Tokens | Tool uses | Wall-clock |
|---|---|---|---|---|---|
| A — baseline | single-shot implement | **8/8** ✅ | ~17k | 2 | ~9 s |
| B — pipeline | coder→tests→review+gate | **8/8** ✅ | ~16k | 8 | ~50 s |

## Result: TIE

Both arms handled the all-zero branch correctly: `[scale/n]*n` instead of `[1/n]*n`.

## Why the trap did NOT activate

The algebraic connection between `scale` and the all-zero formula was obvious:
- The existing branch: `[1.0 / len(weights)] * n`  
- With `scale`: `[scale / len(weights)] * n`

The `1.0` is visually a placeholder; replacing it with `scale` is a direct algebraic substitution.
Compare to T3 (the successful trap): the all-equal branch returned `[0.0]*n` — a constant that has
no formula connection to `clip_floor`. A model must reason *semantically* (clip_floor applies after
normalization, including the degenerate case) to catch it. Here reasoning is *algebraic* (slot scale
into the formula), which is easier.

## Diagnostic value

Positive: confirms that single-shot Sonnet is correct on algebraically-obvious secondary paths.
Negative: this task pattern does not test the pipeline's specific value claim.
