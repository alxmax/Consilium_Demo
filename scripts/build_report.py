"""Assemble the canonical deliberation report from intermediate voice outputs.

Reads a bundle (JSON) on stdin combining Generator/Control/Conservator
outputs plus aggregator + confidence results, and emits the report shape
that ``runs/README.md`` documents and ``validate_report.py`` enforces.

Eliminates the manual JSON assembly that used to live in the agent's head
between Step 5b and Step 6 — a step that was easy to get wrong (typo a
field, forget alternatives, mis-nest deliberation_log).

Input bundle shape on stdin:

    {
      "success_criterion": "REQUIRED",
      "verification":      "REQUIRED",
      "generator":   {"candidates": [...]},                  // from Step 2
      "control":     {"verdicts":   [...]},                  // from Step 3
      "conservator": {"scores":     [...]},                  // from Step 4
      "aggregate":   {"scheme":"...", "chosen":"...", ...},  // from Step 5 (aggregator.py)
      "confidence":  {"confidence":0.85, ...},               // from Step 5b (confidence.py)
      "telemetry":   {...},                                  // optional, Step 6
      "alternatives_limit": 3                                // optional, default 3
    }

Output: the canonical full report (or skipped report if ``skipped: true``
is set on the bundle root, in which case the bundle only needs
``success_criterion`` + ``verification`` + ``skip_reason`` + ``signals``).

Voice scores in the report are derived from the chosen candidate's
own scores in the conservator/control/generator inputs (or defaults).
The ``alternatives`` list is the runner-up candidates (capped at
``alternatives_limit``) with ``why_not`` derived from Control issues
or Conservator factors when present.

Exits 1 on missing required field. Exits 2 on malformed JSON.
Run ``validate_report.py`` after to confirm Principle #4 compliance.

CLI:
    cat bundle.json | python scripts/build_report.py | python scripts/validate_report.py
    python scripts/build_report.py --input bundle.json
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from utils import force_utf8_streams, validate_keys


def _err(msg: str) -> None:
    print(msg, file=sys.stderr)


def _candidate_by_id(items: list[dict], cid: str) -> dict | None:
    for item in items:
        if isinstance(item, dict) and item.get("id") == cid:
            return item
    return None


def _voice_scores_for(chosen: str | None, control: dict, conservator: dict) -> dict | None:
    if chosen is None:
        return None
    verdict = _candidate_by_id(control.get("verdicts") or [], chosen) or {}
    score = _candidate_by_id(conservator.get("scores") or [], chosen) or {}
    issues = verdict.get("issues") or []
    control_score = 0.0 if not verdict.get("valid") else max(0.3, 1.0 - 0.15 * len(issues))
    return {
        "generator": 0.5 if chosen == "do_nothing" or chosen.startswith("adversarial_") else 1.0,
        "control": round(control_score, 3),
        "conservator": float(score.get("risk_score", 0.5)),
    }


def _why_not(verdict: dict | None, score: dict | None) -> str:
    bits: list[str] = []
    if verdict and not verdict.get("valid"):
        details = ", ".join(i.get("category", "?") for i in (verdict.get("issues") or []) if isinstance(i, dict))
        bits.append(f"control: invalid ({details})" if details else "control: invalid")
    elif verdict and verdict.get("issues"):
        first = verdict["issues"][0] if verdict["issues"] else {}
        if isinstance(first, dict) and first.get("detail"):
            bits.append(f"control: {first['detail'][:80]}")
    if score and isinstance(score.get("risk_score"), (int, float)):
        risk = float(score["risk_score"])
        if risk >= 0.5:
            bits.append(f"risk={risk:.2f}")
    return "; ".join(bits) or "ranked below chosen"


def validate_input(bundle: dict) -> None:
    """Validate build_report bundle has required top-level fields.

    For skipped bundles, only success_criterion and verification are required.
    For normal bundles, generator/control/conservator are also required.
    """
    if bundle.get("skipped") is True:
        validate_keys(
            bundle,
            ["success_criterion", "verification"],
            context="build_report bundle",
        )
    else:
        validate_keys(
            bundle,
            ["success_criterion", "verification", "generator", "control", "conservator"],
            context="build_report bundle",
        )


def _alternatives(generator: dict, control: dict, conservator: dict, aggregate: dict, limit: int) -> list[dict]:
    chosen = aggregate.get("chosen")
    candidates = generator.get("candidates") or []
    verdicts = control.get("verdicts") or []
    scores = conservator.get("scores") or []
    out: list[dict] = []
    for cand in candidates:
        cid = cand.get("id")
        if not cid or cid == chosen:
            continue
        out.append({
            "id": cid,
            "summary": cand.get("summary", ""),
            "why_not": _why_not(_candidate_by_id(verdicts, cid), _candidate_by_id(scores, cid)),
        })
        if len(out) >= limit:
            break
    return out


def _build_skipped(bundle: dict) -> dict:
    for required in ("success_criterion", "verification", "skip_reason"):
        v = bundle.get(required)
        if not isinstance(v, str) or not v.strip():
            raise ValueError(f"skipped bundle missing required field: {required}")
    return {
        "success_criterion": bundle["success_criterion"],
        "verification": bundle["verification"],
        "chosen_approach": "skipped",
        "skipped": True,
        "skip_reason": bundle["skip_reason"],
        "signals": bundle.get("signals", {}),
        "voice_scores": None,
        "confidence": None,
        "alternatives": [],
        "deliberation_log": [],
    }


def build(bundle: dict) -> dict:
    if bundle.get("skipped") is True:
        return _build_skipped(bundle)

    for required in ("success_criterion", "verification"):
        v = bundle.get(required)
        if not isinstance(v, str) or not v.strip():
            raise ValueError(f"bundle missing required field: {required}")

    generator = bundle.get("generator") or {}
    control = bundle.get("control") or {}
    conservator = bundle.get("conservator") or {}
    aggregate = bundle.get("aggregate") or {}
    confidence_block = bundle.get("confidence") or {}

    if "chosen" not in aggregate:
        raise ValueError("bundle.aggregate missing 'chosen' field")
    chosen = aggregate["chosen"]
    if chosen is not None and not isinstance(chosen, str):
        raise ValueError("bundle.aggregate.chosen must be string or null")

    alt_limit = int(bundle.get("alternatives_limit", 3))

    report: dict[str, Any] = {
        "success_criterion": bundle["success_criterion"],
        "verification": bundle["verification"],
        "chosen_approach": chosen,
        "reasoning": bundle.get("reasoning") or _default_reasoning(aggregate, confidence_block),
        "alternatives": _alternatives(generator, control, conservator, aggregate, alt_limit),
        "voice_scores": _voice_scores_for(chosen, control, conservator),
        "confidence": confidence_block.get("confidence"),
        "deliberation_log": [
            {"step": "generator",   "candidates": generator.get("candidates") or []},
            {"step": "control",     "verdicts":   control.get("verdicts")   or []},
            {"step": "conservator", "scores":     conservator.get("scores") or []},
            {"step": "aggregate",   "scheme": aggregate.get("scheme", "?"), "result": aggregate},
        ],
    }
    if "telemetry" in bundle:
        report["telemetry"] = bundle["telemetry"]
    if "deliberation_quality" in bundle:
        # Advisory block from meta_critic.py — flags shallow deliberations
        # (generator paraphrasing, control speculation, conservator shrugging).
        report["deliberation_quality"] = bundle["deliberation_quality"]
    # Trias mode: pass through team/personalities/vote_pattern/dissent/abstained
    # fields when present in the bundle. These come from the orchestrator after
    # the team_vote aggregator scheme runs.
    if "team" in bundle:
        report["team"] = bundle["team"]
    if "personalities" in bundle:
        report["personalities"] = bundle["personalities"]
    if "vote_pattern" in bundle:
        report["vote_pattern"] = bundle["vote_pattern"]
    aggregate = bundle.get("aggregate", {})
    if isinstance(aggregate, dict):
        if "dissent" in aggregate:
            report["dissent"] = aggregate["dissent"]
        if "abstained" in aggregate:
            report["abstained"] = aggregate["abstained"]
    return report


def _default_reasoning(aggregate: dict, confidence_block: dict) -> str:
    chosen = aggregate.get("chosen")
    scheme = aggregate.get("scheme", "?")
    if chosen is None:
        return f"all candidates vetoed under {scheme}; see retry_suggested"
    conf = confidence_block.get("confidence")
    conf_s = f"{conf:.2f}" if isinstance(conf, (int, float)) else "?"
    return f"{scheme} picked {chosen} (confidence={conf_s})"


def main(argv: list[str] | None = None) -> int:
    force_utf8_streams()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--input",
        type=argparse.FileType("r", encoding="utf-8"),
        default=sys.stdin,
        help="JSON bundle file (default: stdin)",
    )
    args = ap.parse_args(argv)

    try:
        bundle = json.load(args.input)
    except json.JSONDecodeError as exc:
        _err(f"invalid JSON: {exc}")
        return 2
    if not isinstance(bundle, dict):
        _err("bundle must be a JSON object")
        return 2

    validate_input(bundle)

    try:
        report = build(bundle)
    except ValueError as exc:
        _err(str(exc))
        return 1

    json.dump(report, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
