"""Tests for the scale parameter added to normalize_weights.

These tests are red against a raise-NotImplementedError stub and green against
the real implementation in solution.py.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from solution import normalize_weights


def test_scale_default_sums_to_one():
    result = normalize_weights([1.0, 1.0, 2.0])
    assert abs(sum(result) - 1.0) < 1e-9


def test_scale_explicit_one_identical_to_default():
    a = normalize_weights([1.0, 3.0])
    b = normalize_weights([1.0, 3.0], scale=1.0)
    assert a == b


def test_scale_two_sums_to_two():
    result = normalize_weights([1.0, 1.0, 2.0], scale=2.0)
    assert abs(sum(result) - 2.0) < 1e-9


def test_scale_two_proportions_preserved():
    result = normalize_weights([1.0, 1.0, 2.0], scale=2.0)
    assert abs(result[0] - 0.5) < 1e-9
    assert abs(result[1] - 0.5) < 1e-9
    assert abs(result[2] - 1.0) < 1e-9


def test_scale_zero_weights_all_equal_share():
    result = normalize_weights([0.0, 0.0, 0.0, 0.0], scale=4.0)
    assert len(result) == 4
    assert all(abs(r - 1.0) < 1e-9 for r in result)


def test_scale_zero_weights_default_unaffected():
    result = normalize_weights([0.0, 0.0], scale=1.0)
    assert all(abs(r - 0.5) < 1e-9 for r in result)


def test_scale_half():
    result = normalize_weights([1.0, 1.0], scale=0.5)
    assert abs(sum(result) - 0.5) < 1e-9
    assert all(abs(r - 0.25) < 1e-9 for r in result)


def test_scale_empty_returns_empty():
    assert normalize_weights([], scale=5.0) == []


def test_scale_single_nonzero():
    result = normalize_weights([7.0], scale=3.0)
    assert abs(result[0] - 3.0) < 1e-9
