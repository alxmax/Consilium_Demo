"""Derive report confidence from voice-score variance.

Replaces the magic number that used to live in the final report's
``confidence`` field. The intuition: when the three voices agree on a
candidate, confidence is high; when they disagree, confidence is low.

Two signals get folded in:

1. **Inter-voice agreement on the chosen candidate.** Generator and
   Control emit utility (1 = good), but Conservator emits risk
   (1 = bad), so we flip Conservator into safety = 1 - risk before
   measuring spread. Agreement is then
   ``1 - stdev([gen, ctrl, safety]) / max_stdev``, where
   ``max_stdev`` is the maximum possible stdev for 3 values in [0,1]
   (~0.471 for the bimodal case [0,0,1]). Without the flip, the
   metric would punish exactly the cases we want — Gen high, Ctrl
   high, Conservator low (= "everyone thinks this is a great, safe
   candidate") would register as high disagreement.
2. **Separation from runner-up.** ``utility(chosen) - max_utility(others)``,
   where ``utility(c) = mean(gen, ctrl, 1 - cons)``. If there is no
   runner-up, this term is 1.0.

Final confidence is a weighted blend: 0.7 * agreement + 0.3 * separation.
Clamped to [0.05, 0.99] — we never claim absolute certainty, nor zero.

Input format on stdin (JSON):
    {
      "candidates": [
        {
          "id": "chosen_one",
          "scores": {"generator": 0.8, "control": 0.9, "conservator": 0.3}
        },
        {
          "id": "runner_up",
          "scores": {"generator": 0.6, "control": 0.7, "conservator": 0.4}
        }
      ],
      "chosen": "chosen_one"
    }

Output: {"confidence": 0.84, "agreement": 0.91, "separation": 0.20}

If ``chosen`` is null or missing from candidates, returns
``{"confidence": null, "reason": "..."}`` — confidence is undefined
without a winner. Callers should fall back to their own heuristic.

CLI:
    cat aggregation.json | python scripts/confidence.py
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys

VOICES = ("generator", "control", "conservator")
# pstdev of [0, 0, 1] = sqrt(2/9) ≈ 0.4714
MAX_STDEV_3VALS = (2 / 9) ** 0.5
AGREEMENT_WEIGHT = 0.7
SEPARATION_WEIGHT = 0.3
CONFIDENCE_FLOOR = 0.05
CONFIDENCE_CEIL = 0.99


def _utility_vec(scores: dict) -> list[float]:
    """Project the three voices onto a common [0,1] = good axis."""
    return [
        float(scores["generator"]),
        float(scores["control"]),
        1.0 - float(scores["conservator"]),
    ]


def _utility(scores: dict) -> float:
    return statistics.fmean(_utility_vec(scores))


def _spread(scores: dict) -> float:
    return statistics.pstdev(_utility_vec(scores))


def derive(candidates: list[dict], chosen: str | None) -> dict:
    if chosen is None:
        return {"confidence": None, "reason": "no chosen candidate (e.g. all vetoed)"}

    by_id = {c["id"]: c for c in candidates}
    if chosen not in by_id:
        return {"confidence": None, "reason": f"chosen={chosen!r} not in candidates"}

    chosen_c = by_id[chosen]
    agreement = 1.0 - (_spread(chosen_c["scores"]) / MAX_STDEV_3VALS)
    agreement = max(0.0, min(1.0, agreement))

    others = [c for c in candidates if c["id"] != chosen]
    if others:
        chosen_u = _utility(chosen_c["scores"])
        runner_up_u = max(_utility(c["scores"]) for c in others)
        separation = max(0.0, chosen_u - runner_up_u)
    else:
        separation = 1.0

    raw = AGREEMENT_WEIGHT * agreement + SEPARATION_WEIGHT * separation
    confidence = max(CONFIDENCE_FLOOR, min(CONFIDENCE_CEIL, raw))

    return {
        "confidence": round(confidence, 3),
        "agreement": round(agreement, 3),
        "separation": round(separation, 3),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--input",
        type=argparse.FileType("r", encoding="utf-8"),
        default=sys.stdin,
        help="JSON input file (default: stdin)",
    )
    args = ap.parse_args(argv)

    data = json.load(args.input)
    result = derive(data.get("candidates", []), data.get("chosen"))
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
