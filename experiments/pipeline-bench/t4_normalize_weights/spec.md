# T4 — shared spec (both arms receive this + the starting code & existing tests, verbatim)

**Starting point (given to both arms):** `start/solution.py` (a working `normalize_weights`) and
`start/existing_tests.py` (4 passing tests fixing the contract: empty → `[]`; all-zero weights →
equal distribution with no division by zero; basic proportional scaling; single nonzero weight → `[1.0]`).

**chosen_approach:** `add_scale_param` — extend `normalize_weights` with a `scale` parameter, without
regressing the existing contract.

**success_criterion:** Change `normalize_weights` to accept an optional parameter:

```python
def normalize_weights(weights: list[float], scale: float = 1.0) -> list[float]:
    ...
```

After computing the normalized weights (summing to 1.0 as before), multiply each weight by `scale`
so that the result sums to `scale`. `scale=1.0` (default) leaves the existing behavior unchanged.

**Constraint (entailed by the starting code, not negotiable):** the existing guarantees must still hold —
empty input, all-zero weights (no crash, equal distribution now scaled by `scale`), and basic
proportional scaling. Do not regress them.

**verification:** a hidden `pytest` oracle suite (you do not see it) covering the existing guarantees
**and** the new `scale` behavior, including the all-zero-weights path with a non-default `scale`.
