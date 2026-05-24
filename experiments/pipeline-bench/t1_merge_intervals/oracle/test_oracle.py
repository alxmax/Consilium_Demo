"""Hidden oracle for T1 — authored before either arm runs. Neither arm sees this.

Per benchmarking discipline, the per-edge "is there an alternative reading where a
plausible arm output is correct and the oracle wrong?" check:
- touching-merge (test_touching): NOT ambiguous — the spec explicitly fixes it
  ("Touching intervals merge"). An impl using strict `<` fails legitimately.
- all other cases follow unambiguously from "merge overlapping, sort by start".
"""
from solution import merge_intervals


def test_empty():
    assert merge_intervals([]) == []


def test_single():
    assert merge_intervals([[1, 2]]) == [[1, 2]]


def test_two_overlapping():
    assert merge_intervals([[1, 3], [2, 4]]) == [[1, 4]]


def test_two_disjoint_sorted_output():
    assert merge_intervals([[5, 6], [1, 2]]) == [[1, 2], [5, 6]]


def test_unsorted_input():
    assert merge_intervals([[8, 10], [1, 3], [2, 6]]) == [[1, 6], [8, 10]]


def test_touching_merges():           # the implicit-constraint trap
    assert merge_intervals([[1, 2], [2, 3]]) == [[1, 3]]


def test_nested():
    assert merge_intervals([[1, 10], [2, 3]]) == [[1, 10]]


def test_chained():
    assert merge_intervals([[1, 3], [2, 4], [5, 7], [6, 8]]) == [[1, 4], [5, 8]]


def test_negatives():
    assert merge_intervals([[-5, -1], [-3, 0]]) == [[-5, 0]]


def test_duplicates():
    assert merge_intervals([[1, 2], [1, 2]]) == [[1, 2]]
