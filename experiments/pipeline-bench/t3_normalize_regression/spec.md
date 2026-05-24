# T3 — shared spec (both arms receive this + the starting code & existing tests, verbatim)

**Starting point (given to both arms):** `start/solution.py` (a working `normalize_scores`) and
`start/existing_tests.py` (3 passing tests fixing the contract: empty → `[]`; all-equal → all `0.0`
with **no division by zero**; basic min-max scaling).

**chosen_approach:** `add_clip_floor` — extend `normalize_scores` with a clip floor, without regressing
the existing contract.

**success_criterion:** Change `normalize_scores` to accept an optional parameter:

```python
def normalize_scores(scores: list[float], clip_floor: float = 0.0) -> list[float]:
    ...
```

After normalizing to `[0, 1]` as before, any normalized value **below `clip_floor`** is raised up to
`clip_floor`. `clip_floor=0.0` (default) leaves the existing behavior unchanged.

**Constraint (entailed by the starting code, not negotiable):** the existing guarantees must still hold —
empty input, all-equal input (no crash), and basic scaling. Do not regress them.

**verification:** a hidden `pytest` oracle suite (you do not see it) covering the existing guarantees
**and** the new `clip_floor` behavior.
