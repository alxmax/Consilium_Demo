"""Hidden oracle for T4 — authored before either arm runs. Neither arm sees this.

Discipline check: every assertion follows from the spec + explicitly-stated
non-negotiable constraints (existing guarantees must not regress, scale=1.0 default
must be identical to previous behavior).

The regression tests (all_zero_*) are not an alternative reading — the spec forbids
regressing them, and the scale parameter must apply uniformly including the all-zero path.
"""
from solution import normalize_weights


# --- existing guarantees (must not regress) ---
def test_empty():
    assert normalize_weights([]) == []


def test_all_zero_weights_scale_default():
    result = normalize_weights([0.0, 0.0, 0.0])
    assert len(result) == 3
    assert all(abs(r - 1 / 3) < 1e-9 for r in result)


def test_basic_proportional():
    result = normalize_weights([1.0, 1.0, 2.0])
    assert abs(result[0] - 0.25) < 1e-9
    assert abs(result[1] - 0.25) < 1e-9
    assert abs(result[2] - 0.50) < 1e-9


def test_single_nonzero():
    result = normalize_weights([5.0])
    assert abs(result[0] - 1.0) < 1e-9


# --- regression under the NEW parameter (the trap) ---
def test_all_zero_weights_with_scale():
    # All-zero weights => equal distribution, but scaled to `scale`, not 1.0.
    # normalize_weights([0,0,0], scale=3.0) must return [1.0, 1.0, 1.0] (sum = 3.0).
    result = normalize_weights([0.0, 0.0, 0.0], scale=3.0)
    assert len(result) == 3
    assert all(abs(r - 1.0) < 1e-9 for r in result), f"expected [1,1,1], got {result}"


def test_empty_with_scale():
    # Empty list must still return [] regardless of scale.
    assert normalize_weights([], scale=2.0) == []


# --- new scale behavior ---
def test_scale_basic():
    # [1,1,2] normalized → [0.25,0.25,0.5]; scaled by 2 → [0.5,0.5,1.0]
    result = normalize_weights([1.0, 1.0, 2.0], scale=2.0)
    assert abs(result[0] - 0.5) < 1e-9
    assert abs(result[1] - 0.5) < 1e-9
    assert abs(result[2] - 1.0) < 1e-9


def test_default_scale_unchanged():
    # scale=1.0 (explicit default) must behave identically to no-arg call.
    r1 = normalize_weights([1.0, 3.0])
    r2 = normalize_weights([1.0, 3.0], scale=1.0)
    assert r1 == r2
