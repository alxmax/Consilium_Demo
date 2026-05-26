"""Aggregate voice scores into a final decision.

Four schemes exposed via CLI:
- majority: average of voices; pick highest mean. Ties broken by lowest stdev,
  then by insertion order (stable, deterministic).
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

from utils import force_utf8_streams

VOICES = ("generator", "control", "conservator")
DEFAULT_VETO = 0.8
RELAXED_VETO_CAP = 0.85
# Predicted inter-run pstdev for conservator risk_score is 0.12–0.18 (Dimon R2 2026-05-17).
VETO_UNCERTAINTY_BAND = 0.15
# Score delta below which the top-2 ranking is coin-flip territory (2026-05-26 experiment).
LOW_SEPARATION_THRESHOLD = 0.12
# Sigmoid risk penalty parameters: 50% at risk=0.5, ~0.79 at 0.7, ~0.93 at 0.85
SIGMOID_MIDPOINT = 0.5
SIGMOID_STEEPNESS = 10.0


def _voice_vec(scores: dict) -> list[float]:
    return [float(scores[v]) for v in VOICES]


def aggregate_majority(candidates: list[dict]) -> dict:
    """Pick candidate with highest mean voice score; tiebreak by lowest stdev,
    then by original insertion order (stable — avoids TypeError on dict comparisons
    when both mean and stdev are equal)."""
    rows = []
    for i, c in enumerate(candidates):
        vec = _voice_vec(c["scores"])
        mean = statistics.fmean(vec)
        stdev = statistics.pstdev(vec)
        rows.append((mean, stdev, i, c))
    # Sort: highest mean first; on tie, lowest stdev; on tie, earliest index.
    rows.sort(key=lambda t: (-t[0], t[1], t[2]))
    winner = rows[0][3]
    return {
        "scheme": "majority",
        "chosen": winner["id"],
        "ranking": [{"id": c["id"], "mean": m, "stdev": s} for m, s, _i, c in rows],
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
    if not (0.0 <= veto_threshold <= 1.0):
        raise ValueError(
            f"veto_threshold must be in [0.0, 1.0], got {veto_threshold!r}"
        )
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
            if lowest_risk > RELAXED_VETO_CAP:
                result["escalation_required"] = True
                result["escalation_reason"] = (
                    f"lowest candidate risk {lowest_risk:.2f} exceeds RELAXED_VETO_CAP "
                    f"{RELAXED_VETO_CAP}; relaxing threshold would not help"
                )
            else:
                relaxed_threshold = lowest_risk
                result["retry_suggested"] = {
                    "reason": "every candidate vetoed; consider relaxing or re-running Generator with a 'stay under risk X' constraint",
                    "relaxed_threshold": relaxed_threshold,
                    "lowest_risk_candidate": {"id": lowest["id"], "risk": lowest_risk},
                    "would_survive_relaxed": True,
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
    result = {
        "scheme": "conservative_override",
        "veto_threshold": veto_threshold,
        "chosen": winner["id"],
        "ranking": [{"id": c["id"], "score": s} for s, c in ranked],
        "vetoed": vetoed,
        "weights": dict(zip(VOICES, w)),
    }
    if len(ranked) >= 2 and ranked[0][0] - ranked[1][0] < LOW_SEPARATION_THRESHOLD:
        result["low_separation"] = True
    uncertain = [v["id"] for v in vetoed if abs(v["risk"] - veto_threshold) <= VETO_UNCERTAINTY_BAND]
    if uncertain:
        result["veto_uncertain"] = True
        result["veto_uncertain_ids"] = uncertain
    return result


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


def aggregate_team_vote(personalities: list[dict], candidates: list[dict]) -> dict:
    """Trias mode — democratic majority vote over 3 personalities' chosen-uri.

    Input personalities have shape: {"name": str, "chose": str | None}.
    Vote pattern is derived from the count of chosen-uri:
    - 3-0: all 3 personalities agree
    - 2-1: 2 agree, 1 prefers different candidate
    - 2-0: 2 agree, 1 abstain (chose=null)
    - 1-1-1: 3 different chosen-uri
    - 1-1-0: 2 different chosen-uri + 1 abstain
    - 1-0-0: 1 chosen + 2 abstain
    - 0-0-0: all abstain (total veto)
    """
    if len(personalities) != 3:
        raise ValueError(f"team_vote requires exactly 3 personalities, got {len(personalities)}")

    valid_ids = {c["id"] for c in candidates}
    valid_ids.add(None)

    tally: dict = {}
    abstained: list = []
    for p in personalities:
        chose = p.get("chose")
        if chose not in valid_ids:
            raise ValueError(f"personality {p.get('name')!r} chose unknown candidate {chose!r}")
        if chose is None:
            abstained.append({"name": p["name"], "reason": p.get("abstain_reason") or "all candidates vetoed"})
        else:
            tally[chose] = tally.get(chose, 0) + 1

    counts = sorted(tally.values(), reverse=True)
    abstain_count = len(abstained)
    pattern_parts = list(counts) + [0] * abstain_count
    # Always show second slot for 3-personality vote so 3-0/2-1/2-0 are readable.
    while len(pattern_parts) < 2:
        pattern_parts.append(0)
    vote_pattern = "-".join(str(x) for x in pattern_parts)

    chosen: str | None = None
    if counts:
        top = counts[0]
        # Majority = strictly more than half; with 3 voters, majority is >=2 votes.
        if top >= 2:
            tied = [cid for cid, n in tally.items() if n == top]
            if len(tied) > 1:
                raise ValueError(
                    f"team_vote tie: multiple candidates have top count {top}: {sorted(tied)}"
                )
            chosen = tied[0]

    dissent: list = []
    if chosen and len(tally) > 1:
        for p in personalities:
            cid = p.get("chose")
            if cid is not None and cid != chosen:
                dissent.append({"personality": p["name"], "chose": cid})

    result = {
        "scheme": "team_vote",
        "vote_pattern": vote_pattern,
        "chosen": chosen,
        "vote_tally": tally,
        "dissent": dissent,
        "abstained": abstained,
    }
    if vote_pattern == "0-0-0":
        result["retry_suggested"] = {
            "reason": "all 3 personalities vetoed every candidate",
            "hint": "relax conservator threshold or re-run Generator with risk constraints",
        }
    return result


# === SEQUENTIAL ===
def _sequential_methodology_notes(g: dict, c: dict) -> str:
    notes = []
    if g.get("abstain", {}).get("triggered"):
        notes.append(f"Generator abstain: {g['abstain'].get('reason', '?')}")
    if g.get("challenge_upward", {}).get("triggered"):
        notes.append("Generator challenged Conservator (challenge_upward)")
    if c.get("disagreements"):
        n = len(c["disagreements"])
        notes.append(f"{n} disagreement(s) detectate")
    return " | ".join(notes) if notes else "Deliberare completă fără anomalii"


def aggregate_sequential(
    generator_out: dict,
    control_out: dict,
    conservator_out: dict,
) -> dict:
    """Sequential priority-based aggregation with veto cascade.

    Input: voice output dicts (not candidate scores).

    Priority order:
    1. glossary_fail (Control) → BLOCK
    2. irreversibility_flag (Conservator) → BLOCK
    3. substantial disagreement (Control) → REWORK
    4. scale_down (Conservator meta) → ADAPT_SHORT
    5. scale_up (Conservator meta) → ADAPT_EXTENDED
    6. 3+ triggers simultaneously → ESCALATE
    7. default → AGGREGATE
    """
    triggers: list[str] = []

    # Priority 1: Glossary fail
    if control_out.get("glossary_fail"):
        return {
            "scheme": "sequential",
            "result": "BLOCK",
            "reason": "glossary_fail",
            "attempts": control_out.get("glossary_attempts", []),
            "action": "Reformulează întrebarea cu termeni operaționali verificabili",
        }

    # Priority 2: Irreversibility without consent
    if conservator_out.get("irreversibility_flag"):
        rr = conservator_out.get("regression_risk", {})
        return {
            "scheme": "sequential",
            "result": "BLOCK",
            "reason": "irreversibility_no_consent",
            "magnitude": rr.get("magnitude") if isinstance(rr, dict) else None,
            "action": "Confirmă explicit că această decizie este ireversibilă înainte de a continua",
        }

    # Collect triggers for escalation check
    disagreements = control_out.get("disagreements", [])
    substantial = [d for d in disagreements if isinstance(d, dict) and d.get("type") == "substantial"]
    if substantial:
        triggers.append("substantial_disagreement")

    # meta_recommendation lives inside conservator_out["scores"][i], not at top level
    _scores = conservator_out.get("scores") or []
    _metas = [s.get("meta_recommendation") for s in _scores if isinstance(s, dict) and s.get("meta_recommendation")]
    meta = "scale_up" if "scale_up" in _metas else ("scale_down" if "scale_down" in _metas else None)
    if meta == "scale_down":
        triggers.append("scale_down")
    elif meta == "scale_up":
        triggers.append("scale_up")

    if generator_out.get("abstain", {}).get("triggered"):
        triggers.append("generator_abstain")

    # Priority 5 (escalate before individual handling)
    if len(triggers) >= 3:
        return {
            "scheme": "sequential",
            "result": "ESCALATE",
            "triggers": triggers,
            "action": (
                "Multiple semnale critice detectate simultan. "
                "Aggregator nu poate decide singur. Alege ordinea de rezolvare:\n"
                + "\n".join(f"  - {t}" for t in triggers)
            ),
        }

    # Priority 3: Substantial disagreement
    if "substantial_disagreement" in triggers:
        return {
            "scheme": "sequential",
            "result": "REWORK",
            "reason": "substantial_disagreement",
            "disagreements": substantial,
            "action": "Vocile au divergențe substanțiale — clarifică înainte de agregare finală",
        }

    # Priority 4a: scale_down
    if "scale_down" in triggers:
        preferred = generator_out.get("preferred")
        return {
            "scheme": "sequential",
            "result": "ADAPT_SHORT",
            "meta_recommendation": "scale_down",
            "chosen": preferred,
            "action": "Deliberare comprimată — răspuns scurt (max 2 propoziții)",
        }

    # Priority 4b: scale_up
    if "scale_up" in triggers:
        return {
            "scheme": "sequential",
            "result": "ADAPT_EXTENDED",
            "meta_recommendation": "scale_up",
            "action": "Deliberare extinsă necesară — cere clarificare user înainte de a continua",
        }

    # Default: aggregate normally
    preferred = generator_out.get("preferred")
    options = generator_out.get("options", generator_out.get("candidates", []))
    rr = conservator_out.get("regression_risk", {})
    net_concern = (
        rr.get("net_concern", 0.15) if isinstance(rr, dict) else float(rr)
        if isinstance(rr, (int, float)) else 0.15
    )

    confidence_per_option: dict[str, float] = {}
    for opt in options:
        oid = opt.get("id", "")
        base = 1.0 if oid == preferred else 0.5
        confidence_per_option[oid] = round(base * (1.0 - net_concern), 3)

    methodology_confidence = 1.0
    if "generator_abstain" in triggers:
        methodology_confidence -= 0.3
    if not control_out.get("glossary"):
        methodology_confidence -= 0.1
    if control_out.get("disagreements"):
        methodology_confidence -= 0.05 * len(control_out["disagreements"])
    methodology_confidence = max(0.0, round(methodology_confidence, 2))

    result = {
        "scheme": "sequential",
        "result": "AGGREGATE",
        "chosen": preferred,
        "confidence_per_option": confidence_per_option,
        "confidence_methodology": methodology_confidence,
        "methodology_notes": _sequential_methodology_notes(generator_out, control_out),
    }
    if methodology_confidence < 0.5:
        result["warning"] = "Deliberare incompletă — consideră rezultatul ca preliminar"
    return result
# === END SEQUENTIAL ===


SCHEMES = {
    "majority": lambda data: aggregate_majority(data["candidates"]),
    "conservative_override": lambda data: aggregate_conservative_override(
        data["candidates"],
        data.get("weights"),
        data.get("veto_threshold", DEFAULT_VETO),
    ),
    "risk_adjusted_utility": lambda data: aggregate_risk_adjusted_utility(
        data["candidates"]
    ),
    "team_vote": lambda data: aggregate_team_vote(
        data["personalities"], data["candidates"]
    ),
    "sequential": lambda data: aggregate_sequential(
        data["generator"],
        data["control"],
        data["conservator"],
    ),
    "rund2": lambda data: aggregate_sequential(  # backward-compat alias
        data["generator"],
        data["control"],
        data["conservator"],
    ),
}


def main(argv: list[str] | None = None) -> int:
    force_utf8_streams()
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
