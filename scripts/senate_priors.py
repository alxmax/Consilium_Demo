"""senate_priors.py — Law 6 helper: find prior senate runs with similar label.

Law 6 (Iterative Coherence): before Round 1, the orchestrator scans
runs/senate/ for runs with a similar label within the last 30 days.
Prior verdict + top 3 modify_requests are injected as prior_run_context
into all senators' Round 1 input.

CLI:
    python scripts/senate_priors.py --label "some-label"
    python scripts/senate_priors.py --label "some-label" --days 30 --top 3

Output (JSON to stdout):
    {
      "prior_run": null | {
        "path": "runs/senate/...",
        "label": "...",
        "verdict": "...",
        "modify_requests": [...],  # top --top items
        "run_date": "YYYY-MM-DD"
      },
      "match_method": "substring" | "none"
    }
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _parse_run_date(filename: str) -> dt.date | None:
    """Extract date from senate bundle filename: YYYY-MM-DD_HHMMSS-label.json"""
    try:
        date_str = filename[:10]
        return dt.date.fromisoformat(date_str)
    except (ValueError, IndexError):
        return None


def _substring_match(query: str, candidate: str) -> bool:
    """True if either string contains the other (case-insensitive)."""
    q = query.lower().strip()
    c = candidate.lower().strip()
    return q in c or c in q


def find_similar_runs(
    label: str,
    days: int = 30,
    top: int = 3,
) -> dict:
    """Find the most recent senate run with a label similar to `label`.

    Similarity: substring match (no embedding dependency; stdlib-only).
    Returns the most recent match within `days` days, or null if none found.

    The returned modify_requests are capped at `top` items.
    """
    senate_dir = _repo_root() / "runs" / "senate"
    if not senate_dir.is_dir():
        return {"prior_run": None, "match_method": "none"}

    cutoff = dt.date.today() - dt.timedelta(days=days)
    candidates = []

    for path in senate_dir.glob("*.json"):
        run_date = _parse_run_date(path.name)
        if run_date is None or run_date < cutoff:
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        candidate_label = data.get("label", "")
        if not _substring_match(label, candidate_label):
            continue
        candidates.append((run_date, path, data))

    if not candidates:
        return {"prior_run": None, "match_method": "none"}

    # Most recent match wins (sort descending by date, then by filename for stability)
    candidates.sort(key=lambda x: (x[0], x[1].name), reverse=True)
    run_date, path, data = candidates[0]

    modify_requests = data.get("modify_requests", [])
    if not isinstance(modify_requests, list):
        modify_requests = []

    return {
        "prior_run": {
            "path": str(path.relative_to(_repo_root())),
            "label": data.get("label", ""),
            "verdict": data.get("verdict", ""),
            "modify_requests": modify_requests[:top],
            "run_date": run_date.isoformat(),
        },
        "match_method": "substring",
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--label", required=True, help="Label to match against prior senate runs")
    ap.add_argument("--days", type=int, default=30, help="Look back this many days (default: 30)")
    ap.add_argument("--top", type=int, default=3, help="Max modify_requests to return (default: 3)")
    args = ap.parse_args(argv)

    result = find_similar_runs(label=args.label, days=args.days, top=args.top)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
