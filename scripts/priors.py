"""Load priors for a deliberation from FEEDBACK.md and runs/*.json.

Emits a small JSON block to stdout that the deliberation can paste as
soft priors at step 1. Reuses parse_feedback / parse_runs from feedback.py
so the parsing stays single-source.

Signals computed:
- recent: last N FEEDBACK entries (newest first; N defaults to 10)
- counts: outcome tally over the recent slice
- override_rate: OVR / (OK + BAD + OVR), PEND excluded
- bad_rate: BAD / (OK + BAD + OVR)
- conservator_veto_rate: from runs/*.json, fraction of runs whose aggregation
  vetoed at least one candidate (or chose None)
- top_note_keywords: top 5 alpha tokens (len >= 4, lowercased) from recent notes

The priors are advisory. Prompts in prompts/*.md remain authoritative.

CLI:
    python scripts/priors.py
    python scripts/priors.py --n 5
    python scripts/priors.py --no-runs
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_FB_PATH = ROOT / "scripts" / "feedback.py"
_spec = importlib.util.spec_from_file_location("max_agent_feedback", _FB_PATH)
assert _spec and _spec.loader
_feedback = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_feedback)

FEEDBACK = _feedback.FEEDBACK
RUNS = _feedback.RUNS
parse_feedback = _feedback.parse_feedback
parse_runs = _feedback.parse_runs

TOKEN_RE = re.compile(r"[^\W\d_]{4,}", re.UNICODE)
STOPWORDS = {
    "the", "and", "with", "from", "this", "that", "was", "were", "but",
    "for", "into", "than", "what", "when", "where", "after", "before",
    "still", "just", "not", "are", "shipped", "dropped", "real", "fine",
}


def _outcome_counts(entries: list[dict]) -> Counter:
    return Counter(e["outcome"] for e in entries)


def _rates(entries: list[dict]) -> dict:
    counts = _outcome_counts(entries)
    rated = counts.get("OK", 0) + counts.get("BAD", 0) + counts.get("OVR", 0)
    if not rated:
        return {"override_rate": None, "bad_rate": None, "rated_count": 0}
    return {
        "override_rate": counts.get("OVR", 0) / rated,
        "bad_rate": counts.get("BAD", 0) / rated,
        "rated_count": rated,
    }


def _result_mentions_veto(result: object) -> bool:
    if not isinstance(result, str):
        return False
    low = result.lower()
    if "veto" not in low:
        return False
    return "niciun veto" not in low and "no veto" not in low


def _run_had_veto(run: dict) -> bool:
    agg = run.get("aggregation")
    if isinstance(agg, dict):
        if agg.get("vetoed"):
            return True
        if "chosen" in agg and agg["chosen"] is None:
            return True
    for step in run.get("deliberation_log", []):
        if step.get("step") != "aggregate":
            continue
        if step.get("scheme") != "conservative_override":
            continue
        if _result_mentions_veto(step.get("result")):
            return True
        if "chosen" in step and step["chosen"] is None:
            return True
    return False


def _veto_rate(runs: list[dict]) -> dict:
    if not runs:
        return {"conservator_veto_rate": None, "runs_seen": 0}
    vetoed = sum(1 for r in runs if _run_had_veto(r))
    return {"conservator_veto_rate": vetoed / len(runs), "runs_seen": len(runs)}


def _top_keywords(entries: list[dict], k: int = 5) -> list[str]:
    tokens: Counter[str] = Counter()
    for e in entries:
        for tok in TOKEN_RE.findall(e.get("note", "").lower()):
            if tok in STOPWORDS:
                continue
            tokens[tok] += 1
    return [w for w, _ in tokens.most_common(k)]


def build_priors(n: int = 10, include_runs: bool = True) -> dict:
    entries = parse_feedback(FEEDBACK)
    recent = entries[:n]
    out: dict = {
        "source": {
            "feedback_path": str(FEEDBACK.relative_to(ROOT)),
            "feedback_total": len(entries),
            "feedback_window": len(recent),
        },
        "recent": recent,
        "counts": dict(_outcome_counts(recent)),
        **_rates(recent),
        "top_note_keywords": _top_keywords(recent),
    }
    if include_runs:
        runs = parse_runs(RUNS)
        out["source"]["runs_path"] = str(RUNS.relative_to(ROOT))
        out["source"]["runs_total"] = len(runs)
        out.update(_veto_rate(runs))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n", type=int, default=10, help="number of recent FEEDBACK entries to summarize")
    ap.add_argument("--no-runs", dest="runs", action="store_false", help="skip scanning runs/*.json")
    args = ap.parse_args(argv)

    priors = build_priors(n=args.n, include_runs=args.runs)
    json.dump(priors, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
