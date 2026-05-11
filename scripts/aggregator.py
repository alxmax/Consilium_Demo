"""Aggregate voice scores into a final decision.

Four schemes:
- majority: average of voices; pick highest mean. Ties broken by lowest variance.
- weighted: weighted average using personality weights. NOTE: treats every
  voice as utility (higher = better), which is wrong for conservator —
  kept for backward compatibility, prefer risk_adjusted_utility.
- conservative_override: vetoes any candidate with conservator risk >
  veto_threshold; survivors ranked by weighted average of (generator,
  control, 1-conservator) so safer candidates outrank riskier ones when
  other voices tie. (Earlier versions reused aggregate_weighted directly,
  which treated conservator as utility — fixed via audit C.)
- risk_adjusted_utility: flip conservator into safety, blend utility with
  a sigmoid risk penalty. No hard veto — risk degrades the score smoothly.

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
import math
import statistics
import sys
from typing import Any

VOICES = ("generator", "control", "conservator")
DEFAULT_VETO = 0.7
RELAXED_VETO_CAP = 0.85
# Sigmoid risk penalty parameters: 50% at risk=0.5, ~0.79 at 0.7, ~0.93 at 0.85
SIGMOID_MIDPOINT = 0.5
SIGMOID_STEEPNESS = 10.0


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
    auto_relax: bool = True,
) -> dict:
    """Weighted-average ranking, but veto any candidate whose conservator
    voice scored above ``veto_threshold`` (interpreting conservator as a
    risk signal: higher = riskier).

    If every candidate is vetoed and ``auto_relax`` is True, emit a
    ``retry_suggested`` block with a relaxed threshold and the
    lowest-risk candidate that would survive it. The caller decides
    whether to re-run Generator with the relaxation hint or to accept
    chosen=None. We do not pick automatically — that would defeat the
    veto's purpose.
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
        result: dict = {
            "scheme": "conservative_override",
            "veto_threshold": veto_threshold,
            "chosen": None,
            "reason": "all candidates vetoed by conservator",
            "vetoed": vetoed,
        }
        if auto_relax and candidates:
            lowest = min(candidates, key=lambda c: float(c["scores"]["conservator"]))
            lowest_risk = float(lowest["scores"]["conservator"])
            relaxed_threshold = min(RELAXED_VETO_CAP, lowest_risk)
            result["retry_suggested"] = {
                "reason": "every candidate vetoed; consider relaxing or re-running Generator with a 'stay under risk X' constraint",
                "relaxed_threshold": relaxed_threshold,
                "lowest_risk_candidate": {"id": lowest["id"], "risk": lowest_risk},
                "would_survive_relaxed": lowest_risk <= relaxed_threshold,
            }
        return result

    # Rank survivors by weighted average of (generator, control, safety)
    # where safety = 1 - conservator. Flipping conservator into safety
    # is the whole point of *conservative* override — without it, a
    # higher-risk survivor (risk=0.6) would outrank a lower-risk one
    # (risk=0.3) when other voices tie, defeating the scheme's name.
    # See aggregator audit C in branch claude/wonderful-dhawan-c83211.
    w = [float(weights[v]) for v in VOICES]
    s = sum(w)
    if s <= 0:
        raise ValueError("weights must sum to a positive value")
    w = [x / s for x in w]
    ranked: list[tuple[float, dict]] = []
    for c in survivors:
        gen = float(c["scores"]["generator"])
        ctrl = float(c["scores"]["control"])
        safety = 1.0 - float(c["scores"]["conservator"])
        score = w[0] * gen + w[1] * ctrl + w[2] * safety
        ranked.append((score, c))
    ranked.sort(key=lambda t: t[0], reverse=True)
    winner = ranked[0][1]
    return {
        "scheme": "conservative_override",
        "veto_threshold": veto_threshold,
        "chosen": winner["id"],
        "ranking": [{"id": c["id"], "score": s} for s, c in ranked],
        "vetoed": vetoed,
        "weights": dict(zip(VOICES, w)),
    }


def _sigmoid_penalty(risk: float) -> float:
    """Smooth [0,1] penalty curve. Centered at SIGMOID_MIDPOINT."""
    return 1.0 / (1.0 + math.exp(-SIGMOID_STEEPNESS * (risk - SIGMOID_MIDPOINT)))


def aggregate_risk_adjusted_utility(candidates: list[dict]) -> dict:
    """Pick the candidate with the highest risk-adjusted utility.

    utility(c)  = mean(generator, control, 1 - conservator)
                  # flip conservator: 1 = safe, 0 = risky
    penalty(c)  = sigmoid((conservator - 0.5) * STEEPNESS)
                  # smooth ramp; 0.5 risk = 0.5 penalty; 0.85 risk = ~0.97 penalty
    final(c)    = utility(c) * (1 - penalty(c))

    No hard veto — high-risk candidates can still win if their utility
    is dramatically higher than alternatives. In practice the sigmoid
    is steep enough that risk > 0.7 candidates lose unless they're
    nearly perfect on the other axes.

    Use this scheme when conservative_override's binary cutoff feels
    too coarse (e.g. you have many candidates clustered near the veto
    threshold and want a smooth tiebreaker instead of a cliff).
    """
    ranked = []
    for c in candidates:
        gen = float(c["scores"]["generator"])
        ctrl = float(c["scores"]["control"])
        cons = float(c["scores"]["conservator"])
        utility = (gen + ctrl + (1.0 - cons)) / 3.0
        penalty = _sigmoid_penalty(cons)
        final = utility * (1.0 - penalty)
        ranked.append((final, utility, penalty, c))
    ranked.sort(key=lambda t: t[0], reverse=True)

    winner = ranked[0][3]
    return {
        "scheme": "risk_adjusted_utility",
        "chosen": winner["id"],
        "ranking": [
            {
                "id": c["id"],
                "score": round(final, 4),
                "utility": round(util, 4),
                "risk_penalty": round(pen, 4),
            }
            for final, util, pen, c in ranked
        ],
    }


SCHEMES = {
    "majority": lambda data: aggregate_majority(data["candidates"]),
    "weighted": lambda data: aggregate_weighted(data["candidates"], data["weights"]),
    "conservative_override": lambda data: aggregate_conservative_override(
        data["candidates"],
        data.get("weights"),
        data.get("veto_threshold", DEFAULT_VETO),
    ),
    "risk_adjusted_utility": lambda data: aggregate_risk_adjusted_utility(
        data["candidates"]
    ),
}


def _force_utf8_streams() -> None:
    # Windows default stdin/stdout encoding is cp1252; piping UTF-8 JSON
    # through that mangles non-ASCII (ț, ș, ă) before any script sees it.
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    _force_utf8_streams()
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
