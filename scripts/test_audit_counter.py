"""Tests for the silent-parallel-audit counter decision logic.

Covers the two deferred bug-audit fixes (TODO.md Cluster B):
  #6 cmd_check idempotency — a repeat --check before --record-divergence must
     not double-fire the audit.
  #7 HOT->DEFAULT window — a frequency flip must restart a FULL window, not
     fire again at the next absolute multiple a few runs later.

Pure-function tests only (no state-file I/O), so the real
`.consilium/audit_state.json` is never touched.

Run:
    python scripts/test_audit_counter.py
    python -m pytest scripts/test_audit_counter.py -v  (if pytest available)
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from audit_counter import (  # noqa: E402
    DEFAULT_FREQUENCY,
    HOT_FREQUENCY,
    ROLLING_WINDOW,
    _adapt_frequency,
    _audit_decision,
    _empty_state,
)


def _state(**over) -> dict:
    s = _empty_state()
    s.update(over)
    return s


class TestAuditDecision(unittest.TestCase):
    def test_first_audit_due_at_frequency(self):
        s = _state(sequential_count=DEFAULT_FREQUENCY)  # 20, last_audit_run=None
        d = _audit_decision(s, headless=False)
        self.assertTrue(d["is_due"])
        self.assertTrue(d["should_audit"])

    def test_not_due_between_intervals(self):
        s = _state(sequential_count=30, last_audit_run=20)
        self.assertFalse(_audit_decision(s, headless=False)["is_due"])
        s2 = _state(sequential_count=40, last_audit_run=20)
        self.assertTrue(_audit_decision(s2, headless=False)["is_due"])

    def test_idempotent_when_pending(self):
        # #6: --check already signalled this count → second check must not re-fire.
        s = _state(sequential_count=20, pending_audit_at=20)
        d = _audit_decision(s, headless=False)
        self.assertTrue(d["is_due"])
        self.assertTrue(d["already_pending"])
        self.assertFalse(d["should_audit"])

    def test_headless_never_audits(self):
        s = _state(sequential_count=20)
        d = _audit_decision(s, headless=True)
        self.assertTrue(d["is_due"])
        self.assertFalse(d["should_audit"])

    def test_same_count_as_last_audit_not_due(self):
        s = _state(sequential_count=20, last_audit_run=20)
        self.assertFalse(_audit_decision(s, headless=False)["is_due"])

    def test_hot_to_default_restarts_full_window(self):
        # #7: after a HOT->DEFAULT flip recorded at count 55, the next DEFAULT
        # audit must be a FULL 20 runs later (75), NOT at the next absolute
        # multiple of 20 (60), which would be only 5 runs after the flip.
        flipped = _state(sequential_count=55, last_audit_run=55, frequency=DEFAULT_FREQUENCY)
        # 60: the buggy absolute-modulo would fire here (60 % 20 == 0).
        s60 = dict(flipped, sequential_count=60)
        self.assertFalse(_audit_decision(s60, headless=False)["is_due"],
                         "count 60 is only 5 runs after the flip — must NOT be due")
        # 75: a full window after the flip.
        s75 = dict(flipped, sequential_count=75)
        self.assertTrue(_audit_decision(s75, headless=False)["is_due"],
                        "count 75 is a full 20 runs after the flip — must be due")


class TestAdaptFrequency(unittest.TestCase):
    def test_bump_to_hot_on_two_divergences(self):
        s = _state(frequency=DEFAULT_FREQUENCY, recent_divergences=[False, True, True])
        self.assertEqual(_adapt_frequency(s), HOT_FREQUENCY)

    def test_restore_to_default_on_clean_full_window(self):
        s = _state(frequency=HOT_FREQUENCY, recent_divergences=[False] * ROLLING_WINDOW)
        self.assertEqual(_adapt_frequency(s), DEFAULT_FREQUENCY)

    def test_stay_hot_on_partial_window(self):
        s = _state(frequency=HOT_FREQUENCY, recent_divergences=[False, False])
        self.assertEqual(_adapt_frequency(s), HOT_FREQUENCY)


class TestConcurrency(unittest.TestCase):
    def test_concurrent_increments_lose_nothing(self):
        """#5: N concurrent --increment on the same state file must all land.

        Stress test — deterministically passes with the file lock; without it the
        unguarded read-modify-write drops increments under this contention. Uses
        --state-path so the real .consilium/audit_state.json is never touched.
        """
        import json as _json
        import subprocess
        import tempfile

        script = str(Path(__file__).parent / "audit_counter.py")
        n = 30
        with tempfile.TemporaryDirectory() as td:
            state_path = str(Path(td) / "audit_state.json")
            procs = [
                subprocess.Popen(
                    [sys.executable, script, "--increment", "--state-path", state_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                for _ in range(n)
            ]
            for p in procs:
                p.wait()
            final = _json.load(open(state_path, encoding="utf-8"))
        self.assertEqual(
            final["sequential_count"], n,
            f"expected {n} increments, got {final['sequential_count']} (lost under concurrency)",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
