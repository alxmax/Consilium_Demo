"""Search past deliberations for precedents using keyword overlap (TF-IDF light).

Stdlib-only. No external dependencies.

Returns precedent matches usable as context injection by any voice that requests
prior similar runs (pre-processing injection pattern).

CLI:
    python scripts/precedent_search.py --query "stop loss trading"
    python scripts/precedent_search.py --query "refactor auth" --limit 3
    python scripts/precedent_search.py --query "car wash decision" --category trivial
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

# === PHILOSOPHICAL VOICES ===


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _tokenize(text: str) -> list[str]:
    """Simple whitespace tokenization, lowercased."""
    return text.lower().split()


def _overlap_score(query_terms: set[str], doc_text: str) -> float:
    """Jaccard-style overlap: |query ∩ doc| / |query|.

    Returns 0.0 if query is empty. Score is in [0.0, 1.0].
    """
    if not query_terms:
        return 0.0
    doc_terms = set(_tokenize(doc_text))
    return len(query_terms & doc_terms) / len(query_terms)


def _load_runs() -> list[dict]:
    runs_dir = _repo_root() / "runs"
    result = []
    for path in sorted(runs_dir.glob("*.json")):
        if path.parent.name == "senate":
            continue  # skip senate runs
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            data["_filename"] = path.name
            result.append(data)
        except (json.JSONDecodeError, OSError):
            continue
    return result


def search(query: str, limit: int = 5, category: str | None = None) -> dict:
    """Search runs/ for past deliberations similar to `query`.

    Returns:
        {
          "query": str,
          "matches_found": int,
          "results": [
            {
              "run_id": str,
              "score": float,          # overlap score in [0.0, 1.0]
              "success_criterion": str,
              "chosen_approach": str | null,
              "outcome": str | null,   # "OK" | "BAD" | null
            },
            ...
          ]
        }
    """
    query_terms = set(_tokenize(query))
    runs = _load_runs()
    scored: list[tuple[float, dict]] = []

    for run in runs:
        if category and run.get("category") != category:
            continue
        sc = run.get("success_criterion", "")
        if not isinstance(sc, str):
            continue
        score = _overlap_score(query_terms, sc)
        if score > 0.0:
            scored.append((score, run))

    scored.sort(key=lambda t: t[0], reverse=True)
    top = scored[:limit]

    results = []
    for score, run in top:
        results.append({
            "run_id": run["_filename"],
            "score": round(score, 3),
            "success_criterion": run.get("success_criterion", ""),
            "chosen_approach": run.get("chosen_approach"),
            "outcome": run.get("outcome"),
        })

    return {
        "query": query,
        "matches_found": len(top),
        "results": results,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--query", required=True, help="search query (success criterion text)")
    ap.add_argument("--limit", type=int, default=5, help="max results (default: 5)")
    ap.add_argument("--category", default=None, help="filter by run category field")
    args = ap.parse_args(argv)

    result = search(args.query, args.limit, args.category)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# === END PHILOSOPHICAL VOICES ===
