"""Existing test suite — passes against the starting solution.py. Part of the codebase
both arms are given. The change must NOT regress these guarantees."""
from solution import normalize_weights


def test_empty():
    assert normalize_weights([]) == []


def test_all_zero_weights_equal_distribution():
    result = normalize_weights([0.0, 0.0, 0.0])
    assert len(result) == 3
    assert all(abs(r - 1 / 3) < 1e-9 for r in result)


def test_basic_proportional():
    result = normalize_weights([1.0, 1.0, 2.0])
    assert abs(result[0] - 0.25) < 1e-9
    assert abs(result[1] - 0.25) < 1e-9
    assert abs(result[2] - 0.50) < 1e-9


def test_single_nonzero():
    assert normalize_weights([5.0]) == [1.0]
