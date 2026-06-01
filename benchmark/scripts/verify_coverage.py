#!/usr/bin/env python3
"""
Score tests_self.cpp for spec coverage on code/01_circuit_breaker.

Counts how many of the 9 behavioral requirements from the prompt appear as
tested scenarios. Each requirement maps to a detectable code pattern.

Usage:
    python scripts/verify_coverage.py workspace/<mode>/code/01_circuit_breaker/rep_1/tests_self.cpp
    python scripts/verify_coverage.py --all          # scan all modes
"""

import argparse
import re
import sys
from pathlib import Path

BASE = Path(__file__).parent.parent
WORKSPACE = BASE / "workspace"

sys.path.insert(0, str(BASE / "scripts"))
from _common import MODES

TASK = "code/01_circuit_breaker"

# 9 requirements from the prompt, each with detection patterns.
REQUIREMENTS = [
    {
        "id": "r1_consecutive_failure_trips",
        "desc": "N consecutive failures trip OPEN",
        "check": lambda t: bool(re.search(
            r'record_failure.*record_failure', t, re.DOTALL))
            and "OPEN" in t,
    },
    {
        "id": "r2_success_resets_streak",
        "desc": "success in CLOSED resets consecutive-failure streak",
        "check": lambda t: bool(re.search(
            r'record_failure.*record_success.*record_failure', t, re.DOTALL)),
    },
    {
        "id": "r3_open_ignores_records",
        "desc": "record_* in OPEN window is ignored",
        "check": lambda t: bool(re.search(
            r'(?:ignored|Inside.*open.*window|open.*window.*ignored|'
            r'record_(?:success|failure).*\n.*assert.*OPEN)',
            t, re.IGNORECASE | re.DOTALL)),
    },
    {
        "id": "r4_open_to_halfopen_lazy",
        "desc": "OPEN → HALF_OPEN transition is lazy (triggered on query)",
        "check": lambda t: bool(re.search(
            r'sleep_for|sleep\s*\(|this_thread.*sleep|steady_clock',
            t, re.IGNORECASE))
            and "HALF_OPEN" in t,
    },
    {
        "id": "r5_halfopen_success_closes",
        "desc": "N successes in HALF_OPEN re-close the breaker",
        "check": lambda t: bool(re.search(
            r'HALF_OPEN.*record_success|record_success.*CLOSED',
            t, re.DOTALL | re.IGNORECASE)),
    },
    {
        "id": "r6_halfopen_failure_reopens",
        "desc": "single failure in HALF_OPEN immediately re-opens with fresh timeout",
        "check": lambda t: bool(re.search(
            r'HALF_OPEN.*record_failure.*OPEN|'
            r'record_failure.*HALF_OPEN.*OPEN',
            t, re.DOTALL | re.IGNORECASE)),
    },
    {
        "id": "r7_is_open_false_in_halfopen",
        "desc": "is_open() returns false in HALF_OPEN",
        "check": lambda t: bool(re.search(
            r'HALF_OPEN.*is_open\s*\(\s*\).*false|'
            r'is_open.*false.*HALF_OPEN',
            t, re.DOTALL | re.IGNORECASE))
            or (
                "HALF_OPEN" in t
                and re.search(r'is_open\s*\(\s*\)', t)
                and re.search(r'false|!.*is_open', t)
            ),
    },
    {
        "id": "r8_threshold_one_edge",
        "desc": "failure_threshold=1 or success_threshold=1 edge case",
        "check": lambda t: bool(re.search(
            r'CircuitBreaker\s+\w+\s*\(\s*1\s*[,)]|'
            r'threshold.*one|threshold.*=.*1|threshold_one',
            t, re.IGNORECASE)),
    },
    {
        "id": "r9_full_timeout_after_reopen",
        "desc": "HALF_OPEN → OPEN → HALF_OPEN requires full timeout again",
        "check": lambda t: bool(re.search(
            r'HALF_OPEN.*OPEN.*HALF_OPEN|re.?open.*timeout|fresh.*timeout',
            t, re.DOTALL | re.IGNORECASE))
            or (
                t.count("HALF_OPEN") >= 2
                and re.search(r'sleep_for|this_thread.*sleep', t, re.IGNORECASE)
            ),
    },
]


def score_file(path: Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return {"error": str(e), "score": 0, "max": len(REQUIREMENTS), "hits": []}

    hits = []
    for req in REQUIREMENTS:
        try:
            passed = req["check"](text)
        except Exception:
            passed = False
        if passed:
            hits.append(req["id"])

    lines = len(text.splitlines())
    cb_instances = len(re.findall(r'CircuitBreaker\s+\w+\s*\(', text))
    assertions = len(re.findall(
        r'assert\s*\(|ASSERT|EXPECT|CHECK|==\s*(State::|true|false)',
        text, re.IGNORECASE))

    return {
        "score": len(hits),
        "max": len(REQUIREMENTS),
        "pct": round(100 * len(hits) / len(REQUIREMENTS)),
        "hits": hits,
        "missed": [r["id"] for r in REQUIREMENTS if r["id"] not in hits],
        "lines": lines,
        "cb_instances": cb_instances,
        "assertions": assertions,
    }


def scan_all():
    print(f"{'mode':30}  {'score':>5}  {'pct':>5}  {'lines':>5}  {'cb':>4}  {'assert':>6}")
    print("-" * 70)
    for mode in MODES:
        # Check both default slot and rep_1
        candidates = [
            WORKSPACE / mode / TASK / "tests_self.cpp",
            WORKSPACE / mode / TASK / "rep_1" / "tests_self.cpp",
        ]
        path = next((p for p in candidates if p.exists()), None)
        if path is None:
            print(f"{mode:30}  {'MISSING':>5}")
            continue
        r = score_file(path)
        if "error" in r:
            print(f"{mode:30}  ERROR: {r['error']}")
            continue
        missed_short = ", ".join(r["missed"]) if r["missed"] else "—"
        print(f"{mode:30}  {r['score']:>2}/{r['max']}  {r['pct']:>4}%"
              f"  {r['lines']:>5}  {r['cb_instances']:>4}  {r['assertions']:>6}"
              f"  missed: {missed_short}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file", nargs="?", help="Path to tests_self.cpp")
    ap.add_argument("--all", action="store_true", help="Scan all modes")
    args = ap.parse_args()

    if args.all:
        scan_all()
        return

    if not args.file:
        ap.print_help()
        sys.exit(1)

    path = Path(args.file)
    r = score_file(path)
    if "error" in r:
        print(f"Error: {r['error']}", file=sys.stderr)
        sys.exit(1)

    print(f"Coverage: {r['score']}/{r['max']} ({r['pct']}%)")
    print(f"Lines: {r['lines']}  CB instances: {r['cb_instances']}  Assertions: {r['assertions']}")
    if r["hits"]:
        print("Covered:")
        for h in r["hits"]:
            req = next(q for q in REQUIREMENTS if q["id"] == h)
            print(f"  ✓ {req['desc']}")
    if r["missed"]:
        print("Missed:")
        for m in r["missed"]:
            req = next(q for q in REQUIREMENTS if q["id"] == m)
            print(f"  ✗ {req['desc']}")


if __name__ == "__main__":
    main()
