"""Aggregate voice scores into a final decision.

Three schemes:
- majority: average of voices; pick highest mean. Ties broken by lowest variance.
- weighted: weighted average using personality weights.
- conservative_override: weighted average, BUT any candidate with conservator
  risk > veto_threshold is disqualified regardless of other voices.

Input format on stdin (JSON):
    {
      "candidates": [
        {
          "id": "approach_a",
          "scores": {"generator": 0.8, "control": 0.9, "conservator": 0.3}
        },
        ...
      ],
      "weights": {"generator": 0.33, "control": 0.34, "conservator": 0.33}
    }

CLI:
    cat input.json | python aggregator.py --scheme conservative_override
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from typing import Any

VOICES = ("generator", "control", "conservator")
DEFAULT_VETO = 0.7


def _voice_vec(scores: dict) -> list[float]:
    return [float(scores[v]) for v in VOICES]


def aggregate_majority(candidates: list[dict]) -> dict:
    """Pick candidate with highest mean voice score; tiebreak by lowest stdev."""
    ranked = []
    for c in candidates:
        vec = _voice_vec(c["scores"])
        mean = statistics.fmean(vec)
        stdev = statistics.pstdev(vec)
        ranked.append((mean, -stdev, c))
    ranked.sort(reverse=True)
    winner = ranked[0][2]
    return {
        "scheme": "majority",
        "chosen": winner["id"],
        "ranking": [{"id": c["id"], "mean": m, "stdev": -ns} for m, ns, c in ranked],
    }


def aggregate_weighted(candidates: list[dict], weights: dict) -> dict:
    """Weighted average across voices using supplied weights."""
    w = [float(weights[v]) for v in VOICES]
    s = sum(w)
    if s <= 0:
        raise ValueError("weights must sum to a positive value")
    w = [x / s for x in w]

    ranked = []
    for c in candidates:
        vec = _voice_vec(c["scores"])
        score = sum(a * b for a, b in zip(vec, w))
        ranked.append((score, c))
    ranked.sort(key=lambda t: t[0], reverse=True)
    winner = ranked[0][1]
    return {
        "scheme": "weighted",
        "weights": dict(zip(VOICES, w)),
        "chosen": winner["id"],
        "ranking": [{"id": c["id"], "score": s} for s, c in ranked],
    }


def aggregate_conservative_override(
    candidates: list[dict],
    weights: dict | None = None,
    veto_threshold: float = DEFAULT_VETO,
) -> dict:
    """Weighted-average ranking, but veto any candidate whose conservator
    voice scored above ``veto_threshold`` (interpreting conservator as a
    risk signal: higher = riskier).
    """
    weights = weights or {v: 1 / 3 for v in VOICES}

    survivors = []
    vetoed = []
    for c in candidates:
        risk = float(c["scores"]["conservator"])
        if risk > veto_threshold:
            vetoed.append({"id": c["id"], "risk": risk})
        else:
            survivors.append(c)

    if not survivors:
        return {
            "scheme": "conservative_override",
            "veto_threshold": veto_threshold,
            "chosen": None,
            "reason": "all candidates vetoed by conservator",
            "vetoed": vetoed,
        }

    base = aggregate_weighted(survivors, weights)
    return {
        "scheme": "conservative_override",
        "veto_threshold": veto_threshold,
        "chosen": base["chosen"],
        "ranking": base["ranking"],
        "vetoed": vetoed,
        "weights": base["weights"],
    }


SCHEMES = {
    "majority": lambda data: aggregate_majority(data["candidates"]),
    "weighted": lambda data: aggregate_weighted(data["candidates"], data["weights"]),
    "conservative_override": lambda data: aggregate_conservative_override(
        data["candidates"],
        data.get("weights"),
        data.get("veto_threshold", DEFAULT_VETO),
    ),
}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--scheme",
        choices=sorted(SCHEMES),
        default="conservative_override",
        help="aggregation scheme (default: conservative_override)",
    )
    ap.add_argument(
        "--input",
        type=argparse.FileType("r", encoding="utf-8"),
        default=sys.stdin,
        help="JSON input file (default: stdin)",
    )
    args = ap.parse_args(argv)

    data: dict[str, Any] = json.load(args.input)
    result = SCHEMES[args.scheme](data)
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
