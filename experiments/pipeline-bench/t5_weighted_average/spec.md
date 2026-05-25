# T5 — shared spec (both arms receive this + the starting code & existing tests, verbatim)

**Starting point (given to both arms):** `start/solution.py` (a working `weighted_average`) and
`start/existing_tests.py` (5 passing tests fixing the contract: basic weighted average; unequal
weights; all-zero weights → 0.0 with no crash; empty inputs → 0.0; length mismatch → ValueError).

**chosen_approach:** `add_default_param` — extend `weighted_average` with a `default` parameter,
without regressing the existing contract.

**success_criterion:** Change `weighted_average` to accept an optional parameter:

```python
def weighted_average(values: list[float], weights: list[float], default: float = 0.0) -> float:
    ...
```

When all weights are zero (including the empty-inputs case), return `default` instead of the
hardcoded `0.0`. `default=0.0` (the default) leaves the existing behavior unchanged.

**Constraint (entailed by the starting code, not negotiable):** the existing guarantees must still hold —
basic weighted average, all-zero weights (no crash, now returns `default`), empty inputs (returns
`default`), length mismatch → ValueError. Do not regress them.

**verification:** a hidden `pytest` oracle suite (you do not see it) covering the existing guarantees
**and** the new `default` behavior, including the all-zero-weights path with a non-default `default`.
