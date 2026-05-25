"""Load priors for a deliberation from FEEDBACK.html and runs/*.json.

Emits a small JSON block to stdout that the deliberation can paste as
soft priors at step 1. Reuses parse_feedback / parse_runs from feedback.py
so the parsing stays single-source.

Signals computed:
- recent: last N FEEDBACK entries (newest first; N defaults to 10)
- counts: outcome tally over the recent slice
- override_rate: OVR / (OK + BAD + OVR), PEND excluded
- bad_rate: BAD / (OK + BAD + OVR)
- weighted_bad_rate: BAD weighted by ``[confirmed]`` marker in note
  (outcome confirmed by production = 2x weight vs subjective rating)
- conservator_veto_rate: from runs/*.json, fraction of runs whose aggregation
  vetoed at least one candidate (or chose None)
- top_note_keywords: top 5 alpha tokens (len >= 4, lowercased) from recent notes
- stale_pendings: up to STALE_PEND_CAP entries from the *full* FEEDBACK list
  (not just recent) whose outcome is PEND and whose date is older than
  STALE_PEND_DAYS — surfaces entries needing retrospective close at step 0
- missing_feedback_runs: runs/*.json files with NO matching FEEDBACK row
  (auto-logging was never called for them) — surfaces feedback gaps

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
import os
import re
import sys
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_FB_PATH = ROOT / "scripts" / "feedback.py"
_spec = importlib.util.spec_from_file_location("consilium_feedback", _FB_PATH)
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

# PEND entries older than this many days are surfaced at Step 0 so the user
# is prompted to close them retroactively. Was 7 — reduced to 2 because audits
# showed 40% of feedback rows reached PEND state and were forgotten before the
# week-long window expired. A two-day cutoff matches a typical "next session"
# cadence, which is when context for a deliberation is still recoverable.
STALE_PEND_DAYS = 2
STALE_PEND_CAP = 5
CONFIRMED_MARKER = "[confirmed]"
# Outcome rows whose note carries CONFIRMED_MARKER reflect production reality
# (the chosen approach was applied and observed), not the user's gut feeling
# right after deliberation. weighted_bad_rate gives them this much more weight
# than subjective rows in the same window.
CONFIRMED_WEIGHT = 2.0


def _outcome_counts(entries: list[dict]) -> Counter:
    return Counter(e["outcome"] for e in entries)


def _is_confirmed(entry: dict) -> bool:
    return CONFIRMED_MARKER in (entry.get("note") or "")


def _rates(entries: list[dict]) -> dict:
    counts = _outcome_counts(entries)
    rated = counts.get("OK", 0) + counts.get("BAD", 0) + counts.get("OVR", 0)
    if not rated:
        return {
            "override_rate": None,
            "bad_rate": None,
            "weighted_bad_rate": None,
            "rated_count": 0,
            "confirmed_count": 0,
        }
    confirmed = sum(1 for e in entries if _is_confirmed(e))
    # weighted_bad: confirmed BAD counts 2x toward numerator and denominator
    # so confirmed outcomes dominate over subjective ones when present.
    num = 0.0
    den = 0.0
    for e in entries:
        if e["outcome"] not in ("OK", "BAD", "OVR"):
            continue
        w = CONFIRMED_WEIGHT if _is_confirmed(e) else 1.0
        den += w
        if e["outcome"] == "BAD":
            num += w
    return {
        "override_rate": counts.get("OVR", 0) / rated,
        "bad_rate": counts.get("BAD", 0) / rated,
        "weighted_bad_rate": (num / den) if den else None,
        "rated_count": rated,
        "confirmed_count": confirmed,
    }


def find_missing_feedback_runs(runs_dir: Path, feedback_entries: list[dict], cap: int = 5) -> list[dict]:
    """Surface runs/*.json files with NO matching FEEDBACK row.

    Primary match: run_path appears in the .run_path_map.json sidecar written
    by log_feedback.py. Fallback (legacy runs not in sidecar): (date,
    chosen[:80]) appears in a feedback row. The fallback can produce false
    negatives when two runs on the same day share a chosen prefix, which is
    why the sidecar is preferred.
    """
    if not runs_dir.exists():
        return []
    import re

    # Load sidecar: maps fingerprint → "runs/<file>.json"
    sidecar_path = runs_dir / ".run_path_map.json"
    try:
        sidecar: dict[str, str] = json.loads(sidecar_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        sidecar = {}
    logged_run_paths: set[str] = set(sidecar.values())

    fb_keys: set[tuple[str, str]] = set()
    for e in feedback_entries:
        chosen = e.get("chosen") or ""
        fb_keys.add((e.get("date", ""), chosen[:80]))

    missing: list[dict] = []
    date_re = re.compile(r"^(\d{4}-\d{2}-\d{2})")
    for run_file in sorted(runs_dir.glob("*.json"), reverse=True):
        m = date_re.match(run_file.name)
        if not m:
            continue
        d = m.group(1)
        rel = f"runs/{run_file.name}"
        # Prefer sidecar match (exact, no collision risk)
        if rel in logged_run_paths:
            continue
        try:
            data = json.loads(run_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        chosen = data.get("chosen_approach")
        chosen_s = "null" if chosen is None else str(chosen)
        # Fallback: legacy rows without sidecar entry
        if (d, chosen_s[:80]) in fb_keys:
            continue
        missing.append({"run": run_file.name, "date": d, "chosen": chosen_s})
        if len(missing) >= cap:
            break
    return missing


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


def find_stale_pendings(entries: list[dict], days_old: int = STALE_PEND_DAYS) -> list[dict]:
    cutoff = (date.today() - timedelta(days=days_old)).isoformat()
    return [
        {"date": e["date"], "context": e["context"], "chosen": e["chosen"]}
        for e in entries
        if e.get("outcome") == "PEND" and e.get("date", "") and e["date"] < cutoff
    ][:STALE_PEND_CAP]


def build_priors(n: int = 10, include_runs: bool = True, headless: bool = False) -> dict:
    entries = parse_feedback(FEEDBACK)
    recent = entries[-n:]
    counts = dict(_outcome_counts(recent))
    pend_pressure = counts.get("PEND", 0) / len(recent) if recent else 0.0
    out: dict = {
        "source": {
            "feedback_path": str(FEEDBACK.relative_to(ROOT)),
            "feedback_total": len(entries),
            "feedback_window": len(recent),
        },
        "recent": recent,
        "counts": counts,
        **_rates(recent),
        "pend_pressure": round(pend_pressure, 2),
        "top_note_keywords": _top_keywords(recent),
        "stale_pendings": find_stale_pendings(entries),
    }
    if include_runs:
        runs = parse_runs(RUNS)
        out["source"]["runs_path"] = str(RUNS.relative_to(ROOT))
        out["source"]["runs_total"] = len(runs)
        out.update(_veto_rate(runs))
        out["missing_feedback_runs"] = find_missing_feedback_runs(RUNS, entries)
    if headless:
        out["stale_pendings"] = []
        out["missing_feedback_runs"] = []
        out["headless_mode"] = True
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n", type=int, default=10, help="number of recent FEEDBACK entries to summarize")
    ap.add_argument("--no-runs", dest="runs", action="store_false", help="skip scanning runs/*.json")
    ap.add_argument("--headless", action="store_true", help="suppress stale_pendings and missing_feedback_runs for non-interactive/CI runs")
    args = ap.parse_args(argv)

    _headless = args.headless or (not sys.stdin.isatty()) or (os.environ.get("CONSILIUM_HEADLESS") == "1")
    priors = build_priors(n=args.n, include_runs=args.runs, headless=_headless)
    json.dump(priors, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
