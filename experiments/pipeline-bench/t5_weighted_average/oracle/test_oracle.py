"""Hidden oracle for T5 — authored before either arm runs. Neither arm sees this.

Discipline check: every assertion follows from the spec + explicitly-stated
non-negotiable constraints (existing guarantees must not regress, default=0.0 must
be identical to previous behavior).

The regression tests (all_zero_*) are not an alternative reading — the spec forbids
regressing them, and the `default` parameter must apply to the all-zero-weights branch.
"""
import pytest
from solution import weighted_average


# --- existing guarantees (must not regress) ---
def test_basic():
    assert abs(weighted_average([1.0, 2.0, 3.0], [1.0, 1.0, 1.0]) - 2.0) < 1e-9


def test_unequal_weights():
    assert abs(weighted_average([0.0, 10.0], [1.0, 3.0]) - 7.5) < 1e-9


def test_all_zero_weights_default_zero():
    assert weighted_average([1.0, 2.0, 3.0], [0.0, 0.0, 0.0]) == 0.0


def test_empty_default_zero():
    assert weighted_average([], []) == 0.0


def test_length_mismatch_raises():
    with pytest.raises(ValueError):
        weighted_average([1.0, 2.0], [1.0])


# --- regression under the NEW parameter (the trap) ---
def test_all_zero_weights_with_custom_default():
    # All weights are 0 => return `default`, not hardcoded 0.0.
    result = weighted_average([1.0, 2.0, 3.0], [0.0, 0.0, 0.0], default=-1.0)
    assert result == -1.0, f"expected -1.0 (custom default), got {result}"


def test_empty_with_custom_default():
    # Empty inputs still hit the all-zero-weight branch; default must apply.
    result = weighted_average([], [], default=99.0)
    assert result == 99.0, f"expected 99.0, got {result}"


# --- new default behavior ---
def test_explicit_default_zero_unchanged():
    # default=0.0 (explicit) must be identical to no-arg call.
    r1 = weighted_average([5.0], [0.0])
    r2 = weighted_average([5.0], [0.0], default=0.0)
    assert r1 == r2


def test_nonzero_weights_unaffected_by_default():
    # When weights are nonzero, `default` must never appear in the result.
    result = weighted_average([1.0, 3.0], [1.0, 1.0], default=999.0)
    assert abs(result - 2.0) < 1e-9, f"expected 2.0, got {result}"
