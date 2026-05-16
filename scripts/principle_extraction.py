"""Extract reusable principles from past deliberations — INACTIVE.

BLOCKED until ALL three conditions are met:
  1. runs/ has >= 10 entries in the target category
  2. outcome tracking active for >= 80% of those runs
  3. category has externally-verifiable outcomes (trading, code — NOT career/relationships)

To activate: flip _INACTIVE = False in this file after verifying conditions.

Supported categories (once active): trading, code, real_estate
Excluded categories (subjective outcomes): career, relationships, mental_health

CLI:
    python scripts/principle_extraction.py status
    python scripts/principle_extraction.py extract --category trading --query "stop loss"
    python scripts/principle_extraction.py extract --category code --query "refactor auth"
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

# === RUND2 ===
_INACTIVE = True  # flip to False only after verifying the 3 conditions above

SUPPORTED_CATEGORIES = frozenset({"trading", "code", "real_estate"})
EXCLUDED_CATEGORIES = frozenset({"career", "relationships", "mental_health"})
MIN_RUNS_THRESHOLD = 10
MIN_OUTCOME_COVERAGE = 0.80
# === END RUND2 ===


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _load_runs() -> list[dict]:
    runs_dir = _repo_root() / "runs"
    result = []
    for path in sorted(runs_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            data["_filename"] = path.name
            result.append(data)
        except (json.JSONDecodeError, OSError):
            continue
    return result


def _check_status() -> dict:
    runs = _load_runs()
    total = len(runs)
    with_outcome = sum(1 for r in runs if r.get("outcome") in ("OK", "BAD"))
    coverage = with_outcome / total if total > 0 else 0.0
    return {
        "inactive": _INACTIVE,
        "runs_total": total,
        "runs_with_outcome": with_outcome,
        "outcome_coverage": round(coverage, 3),
        "min_runs_threshold": MIN_RUNS_THRESHOLD,
        "min_outcome_coverage": MIN_OUTCOME_COVERAGE,
        "supported_categories": sorted(SUPPORTED_CATEGORIES),
        "excluded_categories": sorted(EXCLUDED_CATEGORIES),
        "ready_to_activate": (
            not _INACTIVE
            and total >= MIN_RUNS_THRESHOLD
            and coverage >= MIN_OUTCOME_COVERAGE
        ),
        "blocked_reason": (
            f"Set _INACTIVE=False and ensure: "
            f"runs >= {MIN_RUNS_THRESHOLD} (now {total}), "
            f"outcome coverage >= {MIN_OUTCOME_COVERAGE:.0%} (now {coverage:.0%})"
        ) if _INACTIVE else None,
    }


def _overlap_score(query_terms: set[str], doc_text: str) -> float:
    doc_terms = set(doc_text.lower().split())
    if not query_terms:
        return 0.0
    return len(query_terms & doc_terms) / len(query_terms)


def extract(category: str, query: str, limit: int = 5) -> dict:
    if _INACTIVE:
        return {"error": "principle_extraction is INACTIVE", "status": _check_status()}
    if category in EXCLUDED_CATEGORIES:
        return {"error": f"category {category!r} excluded (subjective outcomes)", "excluded": sorted(EXCLUDED_CATEGORIES)}
    if category not in SUPPORTED_CATEGORIES:
        return {"error": f"unsupported category {category!r}", "supported": sorted(SUPPORTED_CATEGORIES)}

    query_terms = set(query.lower().split())
    runs = _load_runs()
    scored = []
    for r in runs:
        sc = r.get("success_criterion", "")
        if not isinstance(sc, str):
            continue
        score = _overlap_score(query_terms, sc)
        if score > 0:
            scored.append((score, r))
    scored.sort(key=lambda t: t[0], reverse=True)
    top = scored[:limit]

    principles = []
    for score, run in top:
        if run.get("outcome") == "OK" and run.get("chosen_approach"):
            principles.append({
                "principle": f"In context similar to '{query}': '{run['chosen_approach']}' led to positive outcome",
                "based_on": [run["_filename"]],
                "similarity_score": round(score, 3),
                "confidence": round(min(score, 0.9), 2),
            })
    return {
        "query": query,
        "category": category,
        "matches_found": len(top),
        "principles": principles[:3],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd")

    sub.add_parser("status", help="check activation status and runs/ maturity")

    ext_p = sub.add_parser("extract", help="extract principles (requires active)")
    ext_p.add_argument("--category", required=True, choices=sorted(SUPPORTED_CATEGORIES))
    ext_p.add_argument("--query", required=True)
    ext_p.add_argument("--limit", type=int, default=5)

    args = ap.parse_args(argv)
    if args.cmd == "status" or args.cmd is None:
        print(json.dumps(_check_status(), indent=2, ensure_ascii=False))
    elif args.cmd == "extract":
        print(json.dumps(extract(args.category, args.query, args.limit), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
