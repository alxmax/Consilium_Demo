# Task 04 — Binary Search Bug

**Type:** Reasoning | **No code required**

---

The following Python function is supposed to return the index of `target` in a sorted list `arr`, or `-1` if not found:

```python
def binary_search(arr, target):
    lo, hi = 0, len(arr)
    while lo < hi:
        mid = (lo + hi) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1
```

With `arr = [1, 3]` and `target = 1`, the function returns `-1` (incorrect — expected `0`).

Where is the bug?

- A) Line 2: `hi` should be initialised to `len(arr) - 1`
- B) Line 3: the loop condition should be `while lo <= hi`
- C) The `else` branch: `hi = mid - 1` should be `hi = mid`
- D) Something else — there are multiple bugs; no single-line fix is sufficient

## Required answer format

**Pick exactly ONE option — A, B, C or D — and justify it.**

Your response must follow this exact structure:

1. **First line** (nothing else on it): `ANSWER: A` (or B, C, D — one letter only).
2. **Then the justification**, covering:
   - Why this option is the bug and why the single-line fix corrects it.
   - A step-by-step trace of the failing case (`arr=[1, 3]`, `target=1`) before and after your fix.
   - Why each of the other three options is wrong (one sentence each).

No hedging. No "it depends". No picking two. Commit to one letter.

**Also save the same response to a file `answer.md` in your assigned workspace folder.** The runner reads that file to extract the `ANSWER:` line and compare it to the expected answer. If `answer.md` is missing or its first non-empty line is not `ANSWER: <letter>`, the correctness check fails automatically.
