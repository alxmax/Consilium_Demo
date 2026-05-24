# T2 — shared spec (both arms receive this, verbatim)

**chosen_approach:** `lru_cache_class` — a fixed-capacity LRU cache.

**success_criterion:** Implement, in `solution.py`:

```python
class LRUCache:
    def __init__(self, capacity: int): ...
    def get(self, key: int) -> int: ...      # value, or -1 if absent
    def put(self, key: int, value: int) -> None: ...
```

A **least-recently-used** cache of the given capacity:
- `get(key)` returns the stored value, or `-1` if the key is absent.
- `put(key, value)` inserts/updates. When inserting a new key would exceed `capacity`,
  evict the **least-recently-used** entry first.
- `capacity` is `>= 0`. A capacity of `0` stores nothing (`get` always returns `-1`).

That is the standard LRU contract — implement it faithfully.

**verification:** a hidden `pytest` oracle suite (you do not see it) exercising the LRU contract over
sequences of operations.
