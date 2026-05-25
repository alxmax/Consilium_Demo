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

CALIBRATION NOTE (R2 audit 2026-05-17): ``agreement`` measures role-prompt
divergence within one run — how much Generator/Control/Conservator disagree
with each other. It is NOT inter-run stability. Running the same input twice
may produce different voice scores (predicted pstdev 0.12–0.18 for
risk_score). Conservator scores are anchored via categorical formula;
Generator/Control scores are self-assigned unanchored floats.

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
import pathlib
import statistics
import sys

from utils import force_utf8_streams, validate_keys

VOICES = ("generator", "control", "conservator")
# pstdev of [0, 0, 1] = sqrt(2/9) ≈ 0.4714
MAX_STDEV_3VALS = (2 / 9) ** 0.5
AGREEMENT_WEIGHT = 0.7
SEPARATION_WEIGHT = 0.3
CONFIDENCE_FLOOR = 0.05
CONFIDENCE_CEIL = 0.99

_MODES_DIR = pathlib.Path(__file__).parent.parent / "modes"

# Hardcoded fallback used when modes/*.md files are absent (e.g. older installs).
_FLOOR_FALLBACK: dict[str, float] = {
    "sequential": 0.70,
    "sequential_scale_down": 0.70,
    "dialectic": 0.75,
    "trias": 0.80,
}


def _parse_frontmatter(text: str) -> dict[str, str]:
    """Parse flat YAML frontmatter between --- delimiters. Stdlib-only."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    end = next((i for i, l in enumerate(lines[1:], 1) if l.strip() == "---"), None)
    if end is None:
        return {}
    result: dict[str, str] = {}
    for line in lines[1:end]:
        if ":" in line:
            k, _, v = line.partition(":")
            result[k.strip()] = v.strip()
    return result


def _load_mode_floors() -> dict[str, float]:
    """Read confidence_floor from modes/*.md frontmatter. Falls back to hardcoded dict."""
    if not _MODES_DIR.is_dir():
        return dict(_FLOOR_FALLBACK)
    floors: dict[str, float] = {}
    for f in sorted(_MODES_DIR.glob("*.md")):
        try:
            fm = _parse_frontmatter(f.read_text(encoding="utf-8"))
        except OSError:
            continue
        name = fm.get("name", "").strip()
        raw = fm.get("confidence_floor", "").strip()
        if name and raw and raw != "N/A":
            try:
                floors[name] = float(raw)
            except ValueError:
                pass
    if not floors:
        return dict(_FLOOR_FALLBACK)
    # sequential_scale_down inherits sequential floor when not explicitly defined
    if "sequential" in floors and "sequential_scale_down" not in floors:
        floors["sequential_scale_down"] = floors["sequential"]
    return floors


# E1: mode-specific confidence floors. Loaded from modes/*.md frontmatter;
# falls back to hardcoded dict when modes/ is absent (e.g. older installs).
MODE_CONFIDENCE_FLOOR: dict[str, float] = _load_mode_floors()


def check_mode_floor(mode: str, confidence: float | None) -> dict:
    """Return {below_floor: bool, floor: float|None, outcome_hint: str}.

    Callers check this after confidence derivation and log WEAK in FEEDBACK.html
    when below_floor is True. outcome_hint is 'WEAK' or 'OK' (advisory only).
    """
    floor = MODE_CONFIDENCE_FLOOR.get(mode)
    if floor is None or confidence is None:
        return {"below_floor": False, "floor": floor, "outcome_hint": "OK"}
    below = confidence < floor
    return {
        "below_floor": below,
        "floor": floor,
        "outcome_hint": "WEAK" if below else "OK",
    }

VOTE_PATTERN_CONFIDENCE = {
    "3-0": 0.95,
    "2-1": 0.75,  # dissent: one personality chose a different candidate (recoverable)
    "2-0": 0.70,  # veto: one personality had all candidates vetoed (stronger risk signal)
    "1-1-1": None,
    "1-1-0": None,
    "1-0-0": None,
    "0-0-0": None,
}

# Steward is the conservative-leaning personality (weights K=0.40). When it
# dissents or abstains, that carries more risk-signal than the same outcome
# from Pioneer or Architect — drop confidence below the PEND threshold so
# the orchestrator prompts the user instead of auto-shipping.
STEWARD_DISSENT_PENALTY = 0.10
STEWARD_ABSTAIN_PENALTY = 0.15
STEWARD_NAME = "steward"


def _steward_involved(items: list[dict] | None, key: str) -> bool:
    if not items:
        return False
    return any(isinstance(it, dict) and it.get(key) == STEWARD_NAME for it in items)


def confidence_from_vote_pattern(
    pattern: str,
    dissent: list[dict] | None = None,
    abstained: list[dict] | None = None,
) -> dict:
    """Trias mode — derive confidence directly from democratic vote pattern.

    Returns the canonical confidence shape (confidence, agreement, separation)
    so downstream code doesn't need to branch on whether the input was Trias
    or score-based.

    When ``dissent`` (list of ``{personality, chose}``) or ``abstained``
    (list of ``{name, reason}``) is provided, applies a penalty when
    Steward — the conservative voice — is the dissenter/abstainer. Other
    personalities' dissent/abstain doesn't change confidence; the spec
    flags Steward involvement as semantically stronger.
    """
    if pattern not in VOTE_PATTERN_CONFIDENCE:
        raise ValueError(f"unknown vote pattern: {pattern!r}")
    conf = VOTE_PATTERN_CONFIDENCE[pattern]
    if pattern == "3-0":
        agreement = 1.0
    elif pattern in ("2-1", "2-0"):
        agreement = 2 / 3
    else:
        agreement = 0.0

    notes: list[str] = []
    if conf is not None:
        steward_dissenting = pattern == "2-1" and _steward_involved(dissent, "personality")
        steward_abstaining = pattern == "2-0" and _steward_involved(abstained, "name")
        if steward_dissenting:
            conf = round(conf - STEWARD_DISSENT_PENALTY, 3)
            notes.append(f"steward dissented (penalty {STEWARD_DISSENT_PENALTY})")
        if steward_abstaining:
            conf = round(conf - STEWARD_ABSTAIN_PENALTY, 3)
            notes.append(f"steward abstained (penalty {STEWARD_ABSTAIN_PENALTY})")

    result = {
        "confidence": conf,
        "agreement": agreement,
        "separation": None,
        "source": "vote_pattern",
    }
    if notes:
        result["notes"] = notes
    return result


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


def validate_input(data: dict) -> None:
    """Validate confidence.py input shape before any computation."""
    validate_keys(data, ["candidates", "chosen"], context="confidence input")
    if not isinstance(data["candidates"], list):
        print("confidence input: 'candidates' must be a list", file=sys.stderr)
        sys.exit(1)
    for i, cand in enumerate(data["candidates"]):
        if not isinstance(cand, dict):
            print(f"confidence input: candidates[{i}] must be an object", file=sys.stderr)
            sys.exit(1)
        if "scores" not in cand:
            print(
                f"confidence input: candidates[{i}] (id={cand.get('id', '?')!r}) "
                f"missing required field 'scores'. "
                f"For Trias mode, pass {{\"vote_pattern\": \"2-1\"}} instead of candidates with scores "
                f"(or pipe aggregator --scheme team_vote output directly to confidence.py).",
                file=sys.stderr,
            )
            sys.exit(1)
        validate_keys(
            cand["scores"],
            ["generator", "control", "conservator"],
            context=f"candidates[{i}].scores",
        )


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
    force_utf8_streams()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--input",
        type=argparse.FileType("r", encoding="utf-8"),
        default=sys.stdin,
        help="JSON input file (default: stdin)",
    )
    args = ap.parse_args(argv)

    data = json.load(args.input)

    # Trias mode: when vote_pattern is present, derive confidence from pattern
    # instead of from utility/variance over voice scores. Dissent/abstained
    # arrive on aggregator output piped from --scheme team_vote.
    if "vote_pattern" in data:
        result = confidence_from_vote_pattern(
            data["vote_pattern"],
            dissent=data.get("dissent"),
            abstained=data.get("abstained"),
        )
        json.dump(result, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    try:
        validate_input(data)
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    result = derive(data.get("candidates", []), data.get("chosen"))
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
