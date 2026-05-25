"""Tests for the add_default_param change.

These tests cover the new `default` parameter on weighted_average.
The existing test suite (existing_tests.py) covers baseline guarantees;
this file exercises only the new behavior introduced by this change.
"""
import pytest
from solution import weighted_average


def test_default_param_all_zero_weights():
    """Explicit default is returned when all weights are zero."""
    assert weighted_average([1.0, 2.0, 3.0], [0.0, 0.0, 0.0], default=-1.0) == -1.0


def test_default_param_empty_inputs():
    """Explicit default is returned for empty inputs (zero-weight edge case)."""
    assert weighted_average([], [], default=99.0) == 99.0


def test_default_param_negative():
    """default can be negative — returned as-is when total weight is zero."""
    assert weighted_average([5.0], [0.0], default=-42.5) == -42.5


def test_default_param_does_not_affect_normal_computation():
    """When weights are non-zero, default is irrelevant — normal result returned."""
    result = weighted_average([0.0, 10.0], [1.0, 3.0], default=999.0)
    assert abs(result - 7.5) < 1e-9


def test_default_param_zero_preserves_legacy_behavior_all_zero_weights():
    """default=0.0 (the actual default) replicates the original hardcoded 0.0 return."""
    assert weighted_average([1.0, 2.0], [0.0, 0.0]) == 0.0


def test_default_param_zero_preserves_legacy_behavior_empty():
    """default=0.0 (the actual default) replicates the original hardcoded 0.0 return for empty."""
    assert weighted_average([], []) == 0.0


def test_default_signature_accepts_keyword():
    """default can be passed as a keyword argument."""
    assert weighted_average([1.0], [0.0], default=3.14) == pytest.approx(3.14)


def test_default_signature_accepts_positional():
    """default can be passed as a positional argument (3rd position)."""
    assert weighted_average([1.0], [0.0], 7.0) == 7.0
