# T1 — shared spec (both arms receive this, verbatim)

**chosen_approach:** `merge_intervals_sorted` — sort by start, then sweep merging overlaps.

**success_criterion:** Implement, in `solution.py`:

```python
def merge_intervals(intervals: list[list[int]]) -> list[list[int]]:
    ...
```

that merges all overlapping intervals and returns them **sorted ascending by start**.

Rules (fixed — the oracle is bound by these):
- **Touching intervals merge.** Intervals sharing an endpoint, e.g. `[1, 2]` and `[2, 3]`, count as
  overlapping → merge to `[1, 3]`.
- Input may be **unsorted**, may contain **duplicates** and **nested** intervals (`[1,10]` ⊃ `[2,3]`).
- Each interval is `[start, end]` with `start <= end` (you need not handle reversed intervals).
- **Empty input → `[]`.**
- Return a list of `[start, end]` lists (not tuples).

**verification:** a hidden `pytest` oracle suite (you do not see it) covering the happy path plus the
edge cases implied by the rules above.
