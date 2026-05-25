"""Tests for the normalize parameter added to compute_histogram.

These tests target only the new behavior; existing_tests.py covers the baseline.
All tests must be RED against a stub that raises NotImplementedError and
GREEN against the real implementation.
"""
import pytest
from solution import compute_histogram


# --- normalize=False is the default: must not change existing return type or values ---

def test_normalize_false_is_default_raw_counts():
    result = compute_histogram([0.0, 1.0, 2.0, 3.0], 4)
    assert result == [1, 1, 1, 1]


def test_normalize_false_explicit_raw_counts():
    result = compute_histogram([0.0, 1.0, 2.0, 3.0], 4, normalize=False)
    assert result == [1, 1, 1, 1]


# --- normalize=True: normal distribution path ---

def test_normalize_true_sums_to_one():
    data = [0.0, 1.0, 2.0, 3.0, 4.0]
    result = compute_histogram(data, 5, normalize=True)
    assert abs(sum(result) - 1.0) < 1e-9


def test_normalize_true_values_are_fractions():
    # 4 values, 2 bins: 2 in each -> [0.5, 0.5]
    result = compute_histogram([0.0, 1.0, 2.0, 3.0], 2, normalize=True)
    assert result == [0.5, 0.5]


def test_normalize_true_uneven_split():
    # [0,1,2,3,4,5] with 2 bins: values 0-2 in bin 0 (3 items), 3-5 in bin 1 (3 items)
    data = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
    result = compute_histogram(data, 3, normalize=True)
    assert abs(sum(result) - 1.0) < 1e-9
    for v in result:
        assert 0.0 <= v <= 1.0


def test_normalize_true_bins_1():
    # All data goes into the single bin -> fraction = 1.0
    result = compute_histogram([1.0, 2.0, 3.0], 1, normalize=True)
    assert result == [1.0]


# --- normalize=True: empty-data early-return path ---

def test_normalize_true_empty_returns_floats():
    result = compute_histogram([], 3, normalize=True)
    assert result == [0.0, 0.0, 0.0]


def test_normalize_true_empty_length_matches_bins():
    result = compute_histogram([], 5, normalize=True)
    assert len(result) == 5
    assert all(v == 0.0 for v in result)


# --- normalize=True: span==0 (all-equal data) early-return path ---

def test_normalize_true_all_equal_sums_to_one():
    result = compute_histogram([7.0, 7.0, 7.0, 7.0], 4, normalize=True)
    assert abs(sum(result) - 1.0) < 1e-9


def test_normalize_true_all_equal_bin0_is_one():
    # All data piles into bin 0 -> fraction 1.0 in bin 0, rest 0.0
    result = compute_histogram([5.0, 5.0, 5.0], 4, normalize=True)
    assert abs(result[0] - 1.0) < 1e-9
    assert result[1:] == [0.0, 0.0, 0.0]


def test_normalize_true_all_equal_single_item():
    result = compute_histogram([42.0], 3, normalize=True)
    assert abs(result[0] - 1.0) < 1e-9
    assert result[1:] == [0.0, 0.0]
