# T5 result — weighted_average + default (refactor / trivial substitution)

Run: 2026-05-25. Both arms started from `start/solution.py` + `start/existing_tests.py`, same change
request; neither saw the oracle.

## Oracle outcome (hidden, 9 tests: 5 existing guarantees + 2 regression-under-new-param + 2 feature)

| Arm | Mechanism | Oracle pass | Tokens | Tool uses | Wall-clock |
|---|---|---|---|---|---|
| A — baseline | single-shot implement | **9/9** ✅ | ~17k | 2 | ~10 s |
| B — pipeline | coder→tests→review+gate | **9/9** ✅ | ~18k | 13 | ~78 s |

## Result: TIE

Both arms correctly changed `return 0.0` to `return default` in the all-zero-weight branch.

## Why the trap did NOT activate

The change is a trivial 1-line substitution: `return 0.0` → `return default`. There is only ONE
place in the function where the zero-weight early return exists, and the spec explicitly describes
changing it (`The total_w==0.0 early return must be changed to return default`). This is the
simplest possible pattern — no secondary path analysis required, no semantic reasoning, just
replace a literal with the new parameter.

This task does not belong in the "regression trap" regime at all. It is closer to a greenfield/
trivial change than to T3's structural pattern.

## Diagnostic value

Confirms: single-shot is correct on trivial 1-line substitutions. This task should not have been
in the refactor-regime bucket. The minimum qualifying task for "regression trap" is one where the
new parameter must be applied in multiple code paths, at least one of which is a non-obvious branch.
