"""Existing test suite — passes against the starting solution.py. Part of the codebase
both arms are given. The change must NOT regress these guarantees."""
import pytest
from solution import weighted_average


def test_basic():
    assert abs(weighted_average([1.0, 2.0, 3.0], [1.0, 1.0, 1.0]) - 2.0) < 1e-9


def test_unequal_weights():
    # [0, 10] with weights [1, 3] -> (0*1 + 10*3) / 4 = 7.5
    assert abs(weighted_average([0.0, 10.0], [1.0, 3.0]) - 7.5) < 1e-9


def test_all_zero_weights_no_crash():
    assert weighted_average([1.0, 2.0, 3.0], [0.0, 0.0, 0.0]) == 0.0


def test_empty_no_crash():
    assert weighted_average([], []) == 0.0


def test_length_mismatch_raises():
    with pytest.raises(ValueError):
        weighted_average([1.0, 2.0], [1.0])
