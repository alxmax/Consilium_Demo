"""Hidden oracle for T2 — authored before either arm runs. Neither arm sees this.

Discipline check ("alternative reading where a plausible output is correct and the
oracle wrong?"):
- get_refreshes_recency / put_existing_refreshes: NOT ambiguous. "Least-recently-USED"
  entails that a successful get is a use. A FIFO/insertion-order impl fails these
  legitimately — it implements a different (wrong) contract, not an alternative reading.
- capacity_zero / update_no_grow: direct consequences of the stated contract.
"""
from solution import LRUCache


def test_basic_put_get():
    c = LRUCache(2)
    c.put(1, 10)
    assert c.get(1) == 10


def test_missing_returns_minus_one():
    c = LRUCache(2)
    assert c.get(99) == -1


def test_plain_eviction():
    c = LRUCache(2)
    c.put(1, 1); c.put(2, 2); c.put(3, 3)   # 1 is LRU -> evicted
    assert c.get(1) == -1
    assert c.get(2) == 2
    assert c.get(3) == 3


def test_get_refreshes_recency():            # LRU-vs-FIFO discriminator
    c = LRUCache(2)
    c.put(1, 1); c.put(2, 2)
    assert c.get(1) == 1                      # 1 now most-recently-used
    c.put(3, 3)                               # 2 is LRU -> evicted (NOT 1)
    assert c.get(2) == -1
    assert c.get(1) == 1
    assert c.get(3) == 3


def test_put_existing_refreshes_recency():
    c = LRUCache(2)
    c.put(1, 1); c.put(2, 2)
    c.put(1, 11)                              # update + refresh -> 2 is LRU
    c.put(3, 3)                               # evict 2
    assert c.get(2) == -1
    assert c.get(1) == 11


def test_update_does_not_grow_size():
    c = LRUCache(2)
    c.put(1, 1); c.put(1, 1); c.put(1, 1); c.put(2, 2)
    assert c.get(1) == 1 and c.get(2) == 2    # both still present


def test_capacity_zero_stores_nothing():
    c = LRUCache(0)
    c.put(1, 1)
    assert c.get(1) == -1


def test_longer_sequence():
    c = LRUCache(3)
    c.put(1, 1); c.put(2, 2); c.put(3, 3)
    assert c.get(2) == 2                       # order of use now: 1,3 older; 2 newest
    c.put(4, 4)                                # LRU is 1 -> evict 1
    assert c.get(1) == -1
    assert c.get(3) == 3 and c.get(4) == 4 and c.get(2) == 2
