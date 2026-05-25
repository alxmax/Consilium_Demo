"""Existing test suite — passes against the starting solution.py. Part of the codebase
both arms are given. The change must NOT regress these guarantees."""
from solution import compute_histogram


def test_empty():
    assert compute_histogram([], 3) == [0, 0, 0]


def test_all_equal_no_crash():
    result = compute_histogram([5.0, 5.0, 5.0], 4)
    assert result == [3, 0, 0, 0]


def test_basic_distribution():
    # [0,1,2,3,4] with 5 bins -> one value per bin
    result = compute_histogram([0.0, 1.0, 2.0, 3.0, 4.0], 5)
    assert result == [1, 1, 1, 1, 1]


def test_bins_1():
    result = compute_histogram([1.0, 2.0, 3.0], 1)
    assert result == [3]
