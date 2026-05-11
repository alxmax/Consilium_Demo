"""Run regression scenarios against deterministic scripts.

Reads evals/scenarios.json, pipes each scenario through its named script
via subprocess, and checks exit code + stdout subset + stderr substrings
against expectations. Prints PASS/FAIL per scenario and exits non-zero
if any failed.

Subset-match semantics for expect_stdout_subset:
- dict: every key in expected must appear in actual with subset-matching value
- list: must equal exactly (order matters)
- scalar: equality

Use `{}` as expected to assert "stdout parses as JSON" without pinning fields.

For non-JSON stdout (e.g., a script that emits a plain line), use
`expect_stdout_contains` instead — list of substrings, all must appear.

CLI:
    python scripts/run_evals.py
    python scripts/run_evals.py --filter aggregator
    python scripts/run_evals.py --scenarios path/to/file.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def is_subset(expected, actual) -> bool:
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return False
        return all(k in actual and is_subset(v, actual[k]) for k, v in expected.items())
    if isinstance(expected, list):
        return expected == actual
    return expected == actual


def run_one(scenario: dict, repo_root: Path) -> list[str]:
    tool_path = repo_root / scenario["tool"]
    args = scenario.get("args", [])
    stdin_data = scenario.get("stdin_json")
    stdin_text = json.dumps(stdin_data) if stdin_data is not None else ""

    proc = subprocess.run(
        [sys.executable, str(tool_path), *args],
        input=stdin_text,
        capture_output=True,
        text=True,
        cwd=str(repo_root),
    )

    failures: list[str] = []
    expected_exit = scenario.get("expect_exit", 0)
    if proc.returncode != expected_exit:
        failures.append(f"exit: expected {expected_exit}, got {proc.returncode}")

    if "expect_stdout_subset" in scenario:
        try:
            actual = json.loads(proc.stdout) if proc.stdout.strip() else None
        except json.JSONDecodeError as exc:
            failures.append(f"stdout not JSON: {exc}; raw: {proc.stdout[:200]!r}")
        else:
            expected = scenario["expect_stdout_subset"]
            if not is_subset(expected, actual):
                failures.append(
                    f"stdout subset mismatch: expected {json.dumps(expected)}, "
                    f"got {proc.stdout[:300].strip()}"
                )

    for needle in scenario.get("expect_stderr_contains", []):
        if needle not in proc.stderr:
            failures.append(f"stderr missing substring {needle!r}; got: {proc.stderr[:200]!r}")

    for needle in scenario.get("expect_stdout_contains", []):
        if needle not in proc.stdout:
            failures.append(f"stdout missing substring {needle!r}; got: {proc.stdout[:200]!r}")

    return failures


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scenarios", default=None, help="path to scenarios.json (default: evals/scenarios.json)")
    ap.add_argument("--filter", default=None, help="substring filter on scenario name")
    args = ap.parse_args(argv)

    repo_root = Path(__file__).resolve().parent.parent
    scenarios_path = Path(args.scenarios) if args.scenarios else repo_root / "evals" / "scenarios.json"

    try:
        with open(scenarios_path, "r", encoding="utf-8") as f:
            scenarios = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"could not load {scenarios_path}: {exc}", file=sys.stderr)
        return 2

    if args.filter:
        scenarios = [s for s in scenarios if args.filter in s.get("name", "")]

    if not scenarios:
        print("no scenarios matched", file=sys.stderr)
        return 2

    passed = 0
    failed = 0
    for s in scenarios:
        name = s.get("name", "<unnamed>")
        failures = run_one(s, repo_root)
        if failures:
            failed += 1
            print(f"FAIL {name}", file=sys.stderr)
            for fail in failures:
                print(f"  {fail}", file=sys.stderr)
        else:
            passed += 1
            print(f"PASS {name}")

    print(f"\n{passed} passed, {failed} failed", file=sys.stderr)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
