"""Hidden oracle for T6 — authored before either arm runs. Neither arm sees this.

Discipline check: every assertion follows from the spec + explicitly-stated
non-negotiable constraints (existing guarantees must not regress; normalize=False default
must be identical to previous behavior).

The regression tests (all_equal_*, empty_*) are not alternative readings — the spec forbids
regressing them, and the `normalize` parameter must apply uniformly including early-return paths.
"""
from solution import compute_histogram


# --- existing guarantees (must not regress) ---
def test_empty_no_normalize():
    assert compute_histogram([], 3) == [0, 0, 0]


def test_all_equal_no_crash():
    result = compute_histogram([5.0, 5.0, 5.0], 4)
    assert result == [3, 0, 0, 0]


def test_basic_distribution():
    result = compute_histogram([0.0, 1.0, 2.0, 3.0, 4.0], 5)
    assert result == [1, 1, 1, 1, 1]


def test_bins_1():
    result = compute_histogram([1.0, 2.0, 3.0], 1)
    assert result == [3]


# --- regression under the NEW parameter — the all-equal trap ---
def test_all_equal_with_normalize():
    # All-equal => span==0 => early return with counts[0]=n. With normalize=True,
    # must return fractions: [1.0, 0.0, 0.0, 0.0], not raw counts [3, 0, 0, 0].
    result = compute_histogram([5.0, 5.0, 5.0], 4, normalize=True)
    assert abs(result[0] - 1.0) < 1e-9, f"bin 0 expected 1.0, got {result[0]}"
    assert all(abs(r) < 1e-9 for r in result[1:]), f"bins 1+ expected 0.0, got {result[1:]}"


# --- regression under the NEW parameter — the empty trap ---
def test_empty_with_normalize():
    # Empty data => early return with [0]*bins. With normalize=True,
    # must return [0.0]*bins (fractions), not [0]*bins (ints).
    result = compute_histogram([], 3, normalize=True)
    assert len(result) == 3
    assert all(isinstance(r, float) for r in result), f"expected floats, got {result}"
    assert all(r == 0.0 for r in result)


# --- new normalize behavior ---
def test_normalize_basic():
    # [0,1,2,3,4] with 5 bins, 1 per bin -> each fraction = 0.2
    result = compute_histogram([0.0, 1.0, 2.0, 3.0, 4.0], 5, normalize=True)
    assert len(result) == 5
    assert all(abs(r - 0.2) < 1e-9 for r in result), f"expected all 0.2, got {result}"


def test_default_normalize_false_unchanged():
    r1 = compute_histogram([0.0, 1.0, 2.0], 3)
    r2 = compute_histogram([0.0, 1.0, 2.0], 3, normalize=False)
    assert r1 == r2
