import pytest
from solution import LRUCache


# --- Basic get/put ---

def test_get_absent_returns_minus_one():
    c = LRUCache(2)
    assert c.get(1) == -1


def test_put_then_get():
    c = LRUCache(2)
    c.put(1, 10)
    assert c.get(1) == 10


def test_put_update_existing_key():
    c = LRUCache(2)
    c.put(1, 10)
    c.put(1, 99)
    assert c.get(1) == 99


# --- Eviction: LRU entry is removed ---

def test_evict_lru_on_capacity_overflow():
    c = LRUCache(2)
    c.put(1, 1)
    c.put(2, 2)
    c.put(3, 3)   # evicts key 1 (LRU)
    assert c.get(1) == -1
    assert c.get(2) == 2
    assert c.get(3) == 3


def test_evict_correct_key_after_get_refreshes_recency():
    c = LRUCache(2)
    c.put(1, 1)
    c.put(2, 2)
    c.get(1)       # key 1 is now MRU; key 2 becomes LRU
    c.put(3, 3)    # evicts key 2
    assert c.get(2) == -1
    assert c.get(1) == 1
    assert c.get(3) == 3


def test_evict_correct_key_after_put_update_refreshes_recency():
    c = LRUCache(2)
    c.put(1, 1)
    c.put(2, 2)
    c.put(1, 100)  # update key 1 → key 1 becomes MRU; key 2 is LRU
    c.put(3, 3)    # evicts key 2
    assert c.get(2) == -1
    assert c.get(1) == 100
    assert c.get(3) == 3


def test_evict_oldest_insert_order_when_no_gets():
    c = LRUCache(3)
    c.put(1, 1)
    c.put(2, 2)
    c.put(3, 3)
    c.put(4, 4)   # evicts key 1
    assert c.get(1) == -1
    assert c.get(2) == 2
    assert c.get(3) == 3
    assert c.get(4) == 4


# --- Capacity 0 ---

def test_capacity_zero_get_always_minus_one():
    c = LRUCache(0)
    assert c.get(5) == -1


def test_capacity_zero_put_stores_nothing():
    c = LRUCache(0)
    c.put(1, 1)
    assert c.get(1) == -1


# --- Capacity 1 ---

def test_capacity_one_evicts_on_second_put():
    c = LRUCache(1)
    c.put(1, 1)
    c.put(2, 2)
    assert c.get(1) == -1
    assert c.get(2) == 2


def test_capacity_one_update_does_not_evict():
    c = LRUCache(1)
    c.put(1, 1)
    c.put(1, 99)
    assert c.get(1) == 99


# --- Sequence / stress ---

def test_sequence_from_leetcode_example():
    # LRUCache(2):
    # put(1,1), put(2,2), get(1)->1, put(3,3) evicts 2,
    # get(2)->-1, put(4,4) evicts 1, get(1)->-1, get(3)->3, get(4)->4
    c = LRUCache(2)
    c.put(1, 1)
    c.put(2, 2)
    assert c.get(1) == 1
    c.put(3, 3)
    assert c.get(2) == -1
    c.put(4, 4)
    assert c.get(1) == -1
    assert c.get(3) == 3
    assert c.get(4) == 4


def test_repeated_gets_do_not_corrupt_order():
    c = LRUCache(3)
    c.put(1, 1)
    c.put(2, 2)
    c.put(3, 3)
    c.get(1)
    c.get(1)
    c.get(1)   # key 1 still MRU; LRU should be key 2
    c.put(4, 4)  # evicts key 2
    assert c.get(2) == -1
    assert c.get(1) == 1
    assert c.get(3) == 3
    assert c.get(4) == 4


def test_interleaved_put_get_sequence():
    c = LRUCache(3)
    c.put(10, 10)
    c.put(20, 20)
    c.put(30, 30)
    assert c.get(10) == 10   # 10 → MRU; LRU=20
    c.put(40, 40)            # evicts 20
    assert c.get(20) == -1
    assert c.get(10) == 10
    assert c.get(30) == 30
    assert c.get(40) == 40
