"""Existing test suite — passes against the starting solution.py. Part of the codebase
both arms are given. The change must NOT regress these guarantees."""
from solution import normalize_scores


def test_empty():
    assert normalize_scores([]) == []


def test_all_equal_no_crash():
    assert normalize_scores([5, 5, 5]) == [0.0, 0.0, 0.0]


def test_basic_scaling():
    assert normalize_scores([0, 5, 10]) == [0.0, 0.5, 1.0]
