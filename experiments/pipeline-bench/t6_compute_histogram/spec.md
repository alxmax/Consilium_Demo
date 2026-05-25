# T6 — shared spec (both arms receive this + the starting code & existing tests, verbatim)

**Starting point (given to both arms):** `start/solution.py` (a working `compute_histogram`) and
`start/existing_tests.py` (4 passing tests fixing the contract: empty → `[0]*bins`; all-equal data →
all counts in bin 0; basic distribution; bins=1 always returns `[len(data)]`).

**chosen_approach:** `add_normalize_param` — extend `compute_histogram` with a `normalize` parameter,
without regressing the existing contract.

**success_criterion:** Change `compute_histogram` to accept an optional parameter:

```python
def compute_histogram(data: list[float], bins: int, normalize: bool = False) -> list[int] | list[float]:
    ...
```

When `normalize=True`, return each count as a fraction of the total (count/len(data)), so the result
sums to 1.0. When `normalize=False` (default), return raw integer counts, identical to the existing
behavior.

**Constraint (entailed by the starting code, not negotiable):** the existing guarantees must still hold —
empty data (now returns `[0.0]*bins` when normalize=True), all-equal data (now returns `[1.0, 0.0, ...]`
when normalize=True), and basic count behavior. Do not regress them — in particular, the two
early-return paths (empty and span==0) must also apply normalization when `normalize=True`.

**verification:** a hidden `pytest` oracle suite (you do not see it) covering the existing guarantees
**and** the new `normalize` behavior, including both early-return paths (all-equal and empty) with
`normalize=True`.
