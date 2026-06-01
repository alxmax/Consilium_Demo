# Task 01 — Circuit Breaker (state machine) C++17

**Type:** Code | **Language:** C++17

---

Implement a circuit-breaker **state machine** in C++17. No callable wrapper,
no threading, no retry helper — just the state and the transitions.

This is a three-state breaker: `CLOSED → OPEN → HALF_OPEN → (CLOSED | OPEN)`.
Read the transition rules carefully; the half-open path has sharp edges.

Required interface (header-only, in `solution.hpp`):

```cpp
class CircuitBreaker {
public:
    enum class State { CLOSED, OPEN, HALF_OPEN };

    // failure_threshold:  consecutive failures in CLOSED that trip OPEN
    // recovery_timeout_sec: how long OPEN lasts before a trial is allowed
    // success_threshold:  consecutive successes in HALF_OPEN that re-close
    CircuitBreaker(int failure_threshold,
                   int recovery_timeout_sec,
                   int success_threshold);

    void record_success();   // see per-state behaviour below
    void record_failure();   // see per-state behaviour below
    bool is_open() const;    // true ONLY while the breaker is rejecting calls
    State state() const;     // CLOSED / OPEN / HALF_OPEN (evaluated on query)
};
```

Behaviour:

- Start in `CLOSED` with the failure counter at 0.

- **In `CLOSED`:**
  - `record_failure()` increments a *consecutive*-failure counter. When it
    reaches `failure_threshold`, the breaker transitions to `OPEN` and
    records the time of that transition.
  - `record_success()` resets the consecutive-failure counter to 0. It is a
    no-op with respect to state (you stay `CLOSED`).
  - Note the word *consecutive*: a success in `CLOSED` clears the streak, so
    `fail, fail, success, fail, fail` must NOT trip a breaker with
    `failure_threshold = 3`.

- **In `OPEN`:**
  - `is_open()` and `state()` report open until `recovery_timeout_sec` seconds
    have elapsed since the open transition. The transition out of `OPEN` is
    evaluated lazily, i.e. *on query* (`state()` / `is_open()`), not by any
    background timer.
  - Once the timeout has elapsed, the next query moves the breaker into
    `HALF_OPEN` (a trial state) and resets the consecutive-success counter
    to 0. The breaker does NOT jump straight back to `CLOSED`.
  - `record_success()` / `record_failure()` called while still inside the
    open window (before timeout) are ignored — they neither extend nor
    shorten the window, and they do not change the counters.

- **In `HALF_OPEN`:**
  - This is a trial state: probe calls are *allowed*, so `is_open()` returns
    `false` here even though `state()` returns `HALF_OPEN`. These two are
    deliberately not the same thing.
  - `record_success()` increments a *consecutive*-success counter. When it
    reaches `success_threshold`, the breaker returns to `CLOSED` (both
    counters reset to 0).
  - `record_failure()` immediately re-opens the breaker: state goes back to
    `OPEN`, the open-transition time is reset to *now* (so the full timeout
    starts over), and the consecutive-success counter is reset to 0. A single
    failure is enough — it does not wait for any threshold.

- Time can be tracked with `std::chrono::steady_clock`. You do NOT need to
  support thread-safety; single-threaded use is fine.

Edge cases worth getting right:
- `failure_threshold = 1` should trip on the very first failure.
- `success_threshold = 1` should re-close on the first half-open success.
- A breaker that has gone `CLOSED → OPEN → HALF_OPEN → OPEN` must require the
  *full* `recovery_timeout_sec` again from the re-open instant.
- `is_open()` must be `true` in `OPEN`, `false` in both `CLOSED` and
  `HALF_OPEN`.

---
**Required output files** (the runner looks for these by exact name in your workspace root):
- `solution.hpp` — header-only `CircuitBreaker` implementation.
- `tests_self.cpp` — your unit tests. The runner will compile with
  `g++ -std=c++17 -O2 -pthread tests_self.cpp -o tests_self.exe` and run it;
  exit code 0 = pass. Cover at least: trips after N consecutive failures,
  a success breaking the failure streak, the open→half-open→closed happy
  path, and a failure in half-open forcing a fresh full timeout.

---
**Toolchain available:**
- Compiler: `g++` (MSYS2 UCRT64, GCC 14.2.0) — already on PATH
- Standard: `-std=c++17`
- Tip for tests: `std::this_thread::sleep_for` is fine if your tests need
  to cross the timeout boundary; use a small `recovery_timeout_sec` like
  1 to keep test time short.
