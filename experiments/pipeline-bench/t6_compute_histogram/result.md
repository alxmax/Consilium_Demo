# T6 result — compute_histogram + normalize (refactor / early-return trap)

Run: 2026-05-25. Both arms started from `start/solution.py` + `start/existing_tests.py`, same change
request; neither saw the oracle.

## Oracle outcome (hidden, 8 tests: 4 existing guarantees + 2 regression-under-new-param + 2 feature)

| Arm | Mechanism | Oracle pass | Tokens | Tool uses | Wall-clock |
|---|---|---|---|---|---|
| A — baseline | single-shot implement | **8/8** ✅ | ~18k | 2 | ~13 s |
| B — pipeline | coder→tests→review+gate | **8/8** ✅ | ~17k | 10 | ~75 s |

## Result: TIE

Both arms correctly handled both early-return paths (empty and span==0) under `normalize=True`.

## Protocol note: arm A prompt compromised

The arm A prompt included an explicit `IMPORTANT CONSTRAINT` section that enumerated both
early-return paths verbatim — effectively telling arm A exactly where the trap was. This violates
the benchmark's fairness control (same spec, no hints beyond the shared task description).

**This task's result is not valid evidence** for or against the pipeline. The arm A prompt should
have mirrored spec.md verbatim (as T3 did), without enumeration of secondary paths.

## What this task WOULD test (if re-run correctly)

`compute_histogram` has two semantically-isolated early returns (empty path and span==0 path),
both of which return values that feel "complete" without `normalize` applied. This is a valid T3-
pattern trap. A correctly-run re-test (arm A sees only spec.md, no constraint hints) would be a
fair test of whether single-shot misses the early returns — which it plausibly would, given the
structural similarity to T3.

## Recommendation

Re-run T6 with a corrected arm A prompt (just the spec, no constraint enumeration) before using
this task's result as evidence.
