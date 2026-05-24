import pytest
from solution import merge_intervals


def test_empty():
    assert merge_intervals([]) == []


def test_single():
    assert merge_intervals([[3, 5]]) == [[3, 5]]


def test_no_overlap():
    assert merge_intervals([[1, 2], [4, 6]]) == [[1, 2], [4, 6]]


def test_touching_endpoints_merge():
    assert merge_intervals([[1, 2], [2, 3]]) == [[1, 3]]


def test_overlapping():
    assert merge_intervals([[1, 3], [2, 5]]) == [[1, 5]]


def test_nested():
    assert merge_intervals([[1, 10], [2, 3]]) == [[1, 10]]


def test_unsorted_input():
    assert merge_intervals([[4, 6], [1, 3]]) == [[1, 3], [4, 6]]


def test_unsorted_with_overlap():
    assert merge_intervals([[3, 5], [1, 4]]) == [[1, 5]]


def test_duplicates():
    assert merge_intervals([[1, 3], [1, 3]]) == [[1, 3]]


def test_negatives():
    assert merge_intervals([[-5, -2], [-3, 0]]) == [[-5, 0]]


def test_negatives_no_overlap():
    assert merge_intervals([[-5, -3], [-2, 0]]) == [[-5, -3], [-2, 0]]


def test_multiple_merges():
    assert merge_intervals([[1, 4], [2, 5], [6, 8], [7, 10]]) == [[1, 5], [6, 10]]


def test_all_merge_to_one():
    assert merge_intervals([[1, 5], [2, 6], [3, 7], [4, 8]]) == [[1, 8]]


def test_touching_three_in_a_row():
    assert merge_intervals([[1, 2], [2, 3], [3, 4]]) == [[1, 4]]


def test_returns_lists_not_tuples():
    result = merge_intervals([[1, 2]])
    assert isinstance(result[0], list)


def test_mixed_negatives_and_positives():
    assert merge_intervals([[-1, 1], [0, 2]]) == [[-1, 2]]
