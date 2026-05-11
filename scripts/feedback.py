"""Summarize feedback from FEEDBACK.md and runs/*.json.

Reads the journal at FEEDBACK.md, parses entries, and prints a short stats
report so you can see whether each voice (Generator, Control, Conservator)
is actually pulling its weight in your real-world uses.

CLI:
    python scripts/feedback.py             # stats on everything
    python scripts/feedback.py --recent 10 # last 10 entries only
    python scripts/feedback.py --runs      # also scan runs/*.json
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FEEDBACK = ROOT / "FEEDBACK.md"
RUNS = ROOT / "runs"

OUTCOMES = ("OK", "BAD", "OVR", "PEND")

ENTRY_RE = re.compile(
    r"^- (?P<date>\d{4}-\d{2}-\d{2})\s*\|\s*"
    r"(?P<context>[^|]+?)\s*\|\s*"
    r"(?P<chosen>[^|]+?)\s*\|\s*"
    r"(?P<outcome>OK|BAD|OVR|PEND)\s*\|\s*"
    r"(?P<note>.*)$"
)


def parse_feedback(path: Path) -> list[dict]:
    entries = []
    if not path.exists():
        return entries
    for line in path.read_text(encoding="utf-8").splitlines():
        m = ENTRY_RE.match(line)
        if m:
            entries.append(m.groupdict())
    return entries


def parse_runs(path: Path) -> list[dict]:
    runs = []
    if not path.exists():
        return runs
    for f in sorted(path.glob("*.json")):
        try:
            runs.append(json.loads(f.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            continue
    return runs


def report(entries: list[dict], runs: list[dict] | None = None) -> str:
    out = []
    out.append(f"Total logged uses: {len(entries)}")
    if not entries:
        out.append("No entries yet. Use the skill on a real change, then append a line to FEEDBACK.md.")
        return "\n".join(out)

    outcomes = Counter(e["outcome"] for e in entries)
    out.append("Outcomes:")
    for k in OUTCOMES:
        out.append(f"  {k}: {outcomes.get(k, 0)}")

    rated = sum(outcomes.get(k, 0) for k in ("OK", "BAD", "OVR"))
    if rated:
        success = outcomes.get("OK", 0) / rated
        out.append(f"Success rate (excluding PEND): {success:.0%}")

    overrides = [e for e in entries if e["outcome"] == "OVR"]
    if overrides:
        out.append(f"Overrides ({len(overrides)}) — recommendation ignored:")
        for e in overrides[-5:]:
            out.append(f"  {e['date']} | {e['context']} | {e['note']}")

    if runs:
        out.append(f"\nDeliberation runs on disk: {len(runs)}")
        schemes = Counter(_run_scheme(r) for r in runs)
        for s, n in schemes.most_common():
            out.append(f"  scheme={s}: {n}")

    return "\n".join(out)


def _run_scheme(run: dict) -> str:
    """Read the aggregation scheme from a run, tolerating both the legacy
    top-level ``aggregation`` shape and the current ``deliberation_log``
    step shape (matches what priors.py:_run_had_veto walks)."""
    agg = run.get("aggregation")
    if isinstance(agg, dict) and agg.get("scheme"):
        return agg["scheme"]
    for step in run.get("deliberation_log") or []:
        if not isinstance(step, dict):
            continue
        if step.get("step") != "aggregate":
            continue
        if step.get("scheme"):
            return step["scheme"]
        result = step.get("result")
        if isinstance(result, dict) and result.get("scheme"):
            return result["scheme"]
    return "?"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--recent", type=int, default=0, help="only consider the N most recent entries")
    ap.add_argument("--runs", action="store_true", help="also scan runs/*.json")
    args = ap.parse_args(argv)

    entries = parse_feedback(FEEDBACK)
    if args.recent:
        entries = entries[: args.recent]

    runs = parse_runs(RUNS) if args.runs else None
    print(report(entries, runs))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
