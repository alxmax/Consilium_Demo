"""Silent parallel audit counter — implements the "every N sequential runs"
cross-check claim from SKILL.md §"Parallel voices mode".

Stdlib-only. State lives in `.consilium/audit_state.json` (gitignored).

Mechanism (orchestrator-driven):
1. After each sequential deliberation completes Step 6 (report written), the
   orchestrator calls `--increment` to bump the sequential-run counter.
2. `--check` reports whether the current run is due for a silent parallel
   cross-check (every Nth sequential run, where N is the adaptive frequency).
3. If `should_audit: true`, the orchestrator dispatches the parallel voices
   flow (SKILL.md §"How (2 turns)") on the SAME input, compares the
   parallel `chosen` to the sequential `chosen`, and reports back via
   `--record-divergence <0|1>`.
4. Frequency adapts: 2+ divergences in last 5 audits → bump to N=5; 0
   divergences in last 5 audits at N=5 → restore to N=20.

Design decisions (settled by senate audit 2026-05-28 follow-up):
- Counter increments on EVERY sequential run, including scale_down short-
  circuits. Rationale: if sequential scale_downs while parallel runs the full
  pipeline, that IS divergence worth detecting.
- Prior-deliberation passthrough does NOT increment — it bypasses both
  pipelines so there is nothing to cross-check.
- Headless contexts (CLAUDE_HEADLESS=1) increment but `should_audit` returns
  `false` regardless — orchestrator-driven parallel dispatch is not available
  headlessly; the audit fires on the next interactive run instead.
- The 5-audit rolling window is fixed (not configurable) so the calibration
  remains stable for the follow-up audit Deming requested (3-6 months out).

Usage:
    python -X utf8 scripts/audit_counter.py --increment [--mode sequential]
    python -X utf8 scripts/audit_counter.py --check
    python -X utf8 scripts/audit_counter.py --record-divergence 0|1 \
        --sequential-chosen <id> --parallel-chosen <id>
    python -X utf8 scripts/audit_counter.py --status   # human-readable summary

State schema (.consilium/audit_state.json):
    {
      "sequential_count": <int>,        # total sequential runs counted
      "audit_count": <int>,             # total audits performed
      "frequency": 20|5,                # current adaptive frequency
      "recent_divergences": [bool]*5,   # last 5 audit outcomes (newest last)
      "last_audit_run": <int|null>,     # sequential_count at last audit fired
      "pending_audit_at": <int|null>,   # count already signaled by --check,
                                        # awaiting --record-divergence (idempotency)
      "audits": [                       # rolling log (last 20)
        {"at": <int>, "divergence": bool, "seq": "<id>", "par": "<id>",
         "timestamp": "ISO8601"}
      ]
    }
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from utils import DATA_DIR, atomic_write_text, force_utf8_streams, is_headless

# Cross-platform advisory file lock for the state read-modify-write. fcntl is
# POSIX-only and msvcrt is Windows-only — import exactly one.
if os.name == "nt":
    import msvcrt
else:
    import fcntl

STATE_PATH = DATA_DIR / "audit_state.json"
DEFAULT_FREQUENCY = 20
HOT_FREQUENCY = 5
ROLLING_WINDOW = 5
DIVERGENCE_TRIGGER = 2  # >= this many divergences in window → bump to HOT
AUDIT_LOG_LIMIT = 20    # keep last N audit records


@contextmanager
def _state_lock():
    """Serialize the state read-modify-write across processes (blocks until free).

    Locks a dedicated ``<state>.lock`` sentinel — never audit_state.json itself,
    whose atomic os.replace in save_state would invalidate a held handle. The OS
    releases the lock automatically when the holding process exits, so a crash
    mid-update cannot leave it stuck (unlike a mkdir-based lockdir).
    """
    lock_path = STATE_PATH.with_suffix(".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    f = open(lock_path, "a+")
    try:
        if os.name == "nt":
            # msvcrt.locking needs a real byte to lock; ensure the sentinel
            # is non-empty, then lock 1 byte at offset 0 (blocking).
            if os.fstat(f.fileno()).st_size == 0:
                f.write("\0")
                f.flush()
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
        else:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        yield
    finally:
        try:
            if os.name == "nt":
                f.seek(0)
                msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        finally:
            f.close()


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _empty_state() -> dict:
    return {
        "sequential_count": 0,
        "audit_count": 0,
        "frequency": DEFAULT_FREQUENCY,
        "recent_divergences": [],
        "last_audit_run": None,
        "pending_audit_at": None,
        "audits": [],
    }


def load_state() -> dict:
    if not STATE_PATH.exists():
        return _empty_state()
    try:
        raw = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"audit_counter: state file unreadable ({e}); resetting", file=sys.stderr)
        return _empty_state()
    # Tolerate missing keys (forward-compat).
    state = _empty_state()
    state.update({k: v for k, v in raw.items() if k in state})
    return state


def save_state(state: dict) -> None:
    # Route through the shared atomic writer (unique mkstemp temp + flush/fsync +
    # atomic replace). The old fixed `.json.tmp` had no fsync and let concurrent
    # writers clobber the same temp, after which load_state silently reset to empty.
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(STATE_PATH, json.dumps(state, indent=2))


def _adapt_frequency(state: dict) -> int:
    """Adjust frequency based on rolling divergence window. Returns new freq."""
    window = state["recent_divergences"][-ROLLING_WINDOW:]
    divergent = sum(1 for d in window if d)
    current = state["frequency"]
    if current == DEFAULT_FREQUENCY and divergent >= DIVERGENCE_TRIGGER:
        return HOT_FREQUENCY
    if current == HOT_FREQUENCY and len(window) >= ROLLING_WINDOW and divergent == 0:
        return DEFAULT_FREQUENCY
    return current


def cmd_increment(args) -> int:
    with _state_lock():
        state = load_state()
        state["sequential_count"] += 1
        save_state(state)
    print(json.dumps({"sequential_count": state["sequential_count"],
                      "mode_recorded": args.mode}))
    return 0


def _audit_decision(state: dict, headless: bool) -> dict:
    """Pure: decide whether the current run is due for a silent audit. No I/O.

    Cadence is anchored to ``last_audit_run`` (not the absolute count) so a
    frequency flip (HOT<->DEFAULT) restarts a full window — otherwise the first
    window after a HOT->DEFAULT flip could be as short as HOT_FREQUENCY runs
    (e.g. flip at count 55 would re-fire at the next absolute multiple of 20 = 60,
    only 5 runs later). Idempotent within a count: once ``--check`` has signalled
    an audit (pending_audit_at == count), a repeat check returns
    ``should_audit=False`` until ``--record-divergence`` clears the sentinel.
    """
    count = state["sequential_count"]
    base = state["last_audit_run"] or 0
    is_due = (
        count > 0
        and count != state["last_audit_run"]
        and (count - base) % state["frequency"] == 0
    )
    already_pending = state.get("pending_audit_at") == count
    return {
        "is_due": is_due,
        "already_pending": already_pending,
        "should_audit": is_due and not headless and not already_pending,
    }


def cmd_check(_args) -> int:
    with _state_lock():
        state = load_state()
        headless = is_headless()
        decision = _audit_decision(state, headless)
        if decision["should_audit"]:
            # Mark this count as signalled so a repeat --check before
            # --record-divergence does not double-fire the audit.
            state["pending_audit_at"] = state["sequential_count"]
            save_state(state)
    print(json.dumps({
        "should_audit": decision["should_audit"],
        "sequential_count": state["sequential_count"],
        "frequency": state["frequency"],
        "last_audit_run": state["last_audit_run"],
        "headless_skipped": decision["is_due"] and headless,
        "already_pending": decision["already_pending"],
        "recent_divergences": state["recent_divergences"][-ROLLING_WINDOW:],
    }))
    return 0


def cmd_record_divergence(args) -> int:
    if args.divergence not in (0, 1):
        print("--record-divergence value must be 0 or 1", file=sys.stderr)
        return 2
    div = bool(args.divergence)
    with _state_lock():
        state = load_state()
        state["audit_count"] += 1
        state["last_audit_run"] = state["sequential_count"]
        state["pending_audit_at"] = None  # audit resolved; clear the --check sentinel
        state["recent_divergences"].append(div)
        state["recent_divergences"] = state["recent_divergences"][-ROLLING_WINDOW:]
        state["audits"].append({
            "at": state["sequential_count"],
            "divergence": div,
            "seq": args.sequential_chosen or "",
            "par": args.parallel_chosen or "",
            "timestamp": _now_iso(),
        })
        state["audits"] = state["audits"][-AUDIT_LOG_LIMIT:]
        prev_freq = state["frequency"]
        state["frequency"] = _adapt_frequency(state)
        save_state(state)
    print(json.dumps({
        "divergence_recorded": div,
        "audit_count": state["audit_count"],
        "frequency_before": prev_freq,
        "frequency_after": state["frequency"],
        "frequency_changed": prev_freq != state["frequency"],
    }))
    return 0


def cmd_status(_args) -> int:
    state = load_state()
    window = state["recent_divergences"][-ROLLING_WINDOW:]
    div_count = sum(1 for d in window if d)
    print(f"sequential runs counted: {state['sequential_count']}")
    print(f"audits performed:        {state['audit_count']}")
    print(f"current frequency:       1/{state['frequency']}")
    print(f"rolling window ({ROLLING_WINDOW}):    {div_count}/{len(window)} divergent")
    print(f"last audit at run:       {state['last_audit_run']}")
    if state["audits"]:
        print("\nlast 5 audits:")
        for a in state["audits"][-5:]:
            mark = "DIVERGENT" if a["divergence"] else "match"
            print(f"  run {a['at']:>4}  {mark:<10}  seq={a['seq']!r} par={a['par']!r}  {a['timestamp']}")
    return 0


def main() -> int:
    force_utf8_streams()
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n", 1)[0])
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--increment", action="store_true",
                       help="bump sequential-run counter")
    group.add_argument("--check", action="store_true",
                       help="report whether current run is due for silent audit")
    group.add_argument("--record-divergence", type=int, metavar="0|1",
                       help="log audit outcome (0=match, 1=divergence)")
    group.add_argument("--status", action="store_true",
                       help="human-readable state summary")
    parser.add_argument("--mode", default="sequential",
                       help="mode that triggered the increment (informational)")
    parser.add_argument("--sequential-chosen", default="",
                       help="chosen id from sequential run (for divergence log)")
    parser.add_argument("--parallel-chosen", default="",
                       help="chosen id from silent parallel cross-check")
    parser.add_argument("--state-path", default=None,
                       help="override the state file path (default: .consilium/audit_state.json); "
                            "mainly for tests, so they don't touch the real state")
    args = parser.parse_args()

    if args.state_path:
        global STATE_PATH
        STATE_PATH = Path(args.state_path)

    if args.increment:
        return cmd_increment(args)
    if args.check:
        return cmd_check(args)
    if args.record_divergence is not None:
        # argparse stores --record-divergence as args.record_divergence
        args.divergence = args.record_divergence
        return cmd_record_divergence(args)
    if args.status:
        return cmd_status(args)
    return 2  # unreachable due to required=True


if __name__ == "__main__":
    sys.exit(main())
