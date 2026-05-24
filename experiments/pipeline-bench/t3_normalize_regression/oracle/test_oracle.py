"""Hidden oracle for T3 — authored before either arm runs. Neither arm sees this.

Discipline check: every assertion follows from the spec + the explicitly-stated
non-negotiable constraint (existing guarantees must hold). The regression tests
(all_equal_*, empty_*) are not an alternative reading — the spec forbids regressing them.
"""
from solution import normalize_scores


# --- existing guarantees (must not regress) ---
def test_empty():
    assert normalize_scores([]) == []


def test_all_equal_no_crash():
    assert normalize_scores([5, 5, 5]) == [0.0, 0.0, 0.0]


def test_basic_scaling():
    assert normalize_scores([0, 5, 10]) == [0.0, 0.5, 1.0]


# --- regression under the NEW parameter (the trap) ---
def test_all_equal_with_floor_no_crash():
    # all-equal => normalized 0.0 each, then raised to the floor; must not divide by zero
    assert normalize_scores([5, 5, 5], clip_floor=0.2) == [0.2, 0.2, 0.2]


def test_empty_with_floor():
    assert normalize_scores([], clip_floor=0.5) == []


# --- new clip_floor behavior ---
def test_floor_raises_low_values():
    assert normalize_scores([0, 5, 10], clip_floor=0.3) == [0.3, 0.5, 1.0]


def test_default_floor_unchanged():
    assert normalize_scores([0, 5, 10]) == [0.0, 0.5, 1.0]


def test_floor_above_all_clamps_all():
    assert normalize_scores([0, 5, 10], clip_floor=1.0) == [1.0, 1.0, 1.0]
