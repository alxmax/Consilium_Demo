#!/usr/bin/env python3
"""Trias serial-dispatch escalation predicate (detect-log-don't-block, with a graduation gate).

Trias dispatches its 3 personalities SERIALLY at runtime (by construction — see
modes/trias.md "Vehicle decision", Senate 2026-05-29). That is accepted, not fixed:
any parallelism investment is gated on Trias first proving value (>=2 wins in
n>=20 oracle-validated tasks; current record 0 wins at n=6).

This script is the graduation mechanism: it counts accumulated SERIAL real-deliberation
Trias runs across the benchmark workspace and, once they pass a threshold, LOGS a
one-line recommendation to revisit the parallelism vehicle. It never blocks — it just
makes the accumulating gap visible so it doesn't sit silent forever.

Reads `trias_dispatch_pattern` from each `pipeline_audit.json` (written by
check_trias_parallelism.py). Stdlib-only. Exits 0 always (advisory).

CLI:
    python benchmark/scripts/check_trias_escalation.py            # threshold 20
    python benchmark/scripts/check_trias_escalation.py --threshold 10
    python benchmark/scripts/check_trias_escalation.py --json
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent / "workspace"
TRIAS_DIR = WORKSPACE / "consilium_trias"
DEFAULT_THRESHOLD = 20  # matches the n>=20 kill-criterion gate (modes/trias.md)


def tally_patterns() -> Counter:
    """Count trias_dispatch_pattern across every pipeline_audit.json under consilium_trias/."""
    counts: Counter = Counter()
    if not TRIAS_DIR.exists():
        return counts
    for audit in TRIAS_DIR.rglob("pipeline_audit.json"):
        try:
            data = json.loads(audit.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        pattern = data.get("trias_dispatch_pattern")
        if pattern:
            counts[pattern] += 1
    return counts


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--threshold", type=int, default=DEFAULT_THRESHOLD,
                    help=f"serial-run count that triggers the escalation note (default {DEFAULT_THRESHOLD})")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of human text")
    args = ap.parse_args(argv)

    counts = tally_patterns()
    serial = counts.get("serial", 0)
    parallel = counts.get("parallel", 0) + counts.get("mixed", 0)
    escalate = serial >= args.threshold and parallel == 0

    if args.json:
        print(json.dumps({
            "serial": serial, "parallel_or_mixed": parallel,
            "scale_down": counts.get("scale_down", 0),
            "threshold": args.threshold, "escalate": escalate,
        }))
    else:
        print(f"trias dispatch tally: serial={serial} parallel/mixed={parallel} "
              f"scale_down={counts.get('scale_down', 0)} (threshold {args.threshold})")
        if escalate:
            print(f"ESCALATION: {serial} serial Trias runs accumulated with 0 parallel — "
                  "revisit the parallelism vehicle (Senate 2026-05-29 gated this on "
                  ">=2 Trias wins in n>=20; confirm that bar is met before investing).")
        elif parallel:
            print("note: parallel/mixed dispatch observed — the serial-by-construction "
                  "assumption no longer holds; recount.")
        else:
            print("no escalation: below threshold; accept-serial + observe remains proportional.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
