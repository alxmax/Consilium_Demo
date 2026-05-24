"""Score the *quality* of a deliberation — not whether the chosen candidate is good.

``validate_report.py`` enforces JSON schema; this script enforces that
Conservator did distinct work. Without it, a deliberation can pass every
shape check while being intellectually empty: Conservator assigns 0.5 to
everything.

Run between Step 5b (confidence) and Step 6 (build_report). Reads a bundle
from stdin and emits a ``deliberation_quality`` block to stdout that
``build_report.py`` can attach to the report.

One core metric in [0,1] with 1 = healthy, plus optional mode-specific metrics:

- **conservator_spread**: stdev of risk_scores across valid candidates,
  rescaled by the maximum possible stdev (~0.5 for 2-value bimodal). Detects
  the "0.5 shrug" pattern where every candidate gets identical risk.
  Threshold: < 0.1 = shrug, < 0.2 = weak.

Output shape:

    {
      "deliberation_quality": {
        "conservator_spread": 0.18,
        "flags": [
          "conservator_spread=0.18 weak — risk scores cluster near mean"
        ]
      }
    }

Flags only appear when a metric falls below its warning threshold. An
empty ``flags`` list means the deliberation looks healthy. The block is
advisory — it does NOT veto the chosen candidate. Use ``--strict`` to
exit 1 when conservator_spread falls below the *degenerate* threshold so
a CI hook can fail noisily.

CLI:
    cat bundle.json | python scripts/meta_critic.py
    cat bundle.json | python scripts/meta_critic.py --strict
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys

from utils import force_utf8_streams, load_json_stdin


# Maximum stdev for risk_scores in [0,1]: bimodal {0, 1} -> pstdev = 0.5
MAX_RISK_STDEV = 0.5

DEGENERATE = {
    "conservator_spread": 0.10,
}
WARNING = {
    "conservator_spread": 0.20,
}


def conservator_spread(scores: list[dict]) -> float | None:
    """Risk score stdev / max possible stdev, clamped to [0,1].

    Filters to valid candidates only (risk_score present + numeric). A single
    candidate returns None (no spread possible).
    """
    risks: list[float] = []
    for s in scores:
        if not isinstance(s, dict):
            continue
        r = s.get("risk_score")
        if isinstance(r, (int, float)):
            risks.append(float(r))
    if len(risks) < 2:
        return None
    stdev = statistics.pstdev(risks)
    actual_range = max(risks) - min(risks)
    denom = max(actual_range, 0.5)
    return max(0.0, min(1.0, stdev / denom))


_PEER_EVIDENCE_BOILERPLATE = frozenset({
    "see above", "n/a", "none", "as noted", "no concern", "ok",
    "looks good", "no change", "no peer evidence", "tbd",
})


def pass2_revision_quality(bundle: dict) -> float | None:
    """Fraction of Pass-2 revisions that carry non-boilerplate peer_evidence
    ≥20 chars. Returns None if no Pass-2 revisions exist (the metric does
    not apply to single-pass modes).

    Triggers on `control` voice revisions in the dialectic merge step
    (where the schema documents `revision.peer_evidence`).
    """
    pass2 = bundle.get("pass2")
    if not isinstance(pass2, dict):
        return None
    verdicts = (pass2.get("control") or {}).get("verdicts") or []
    revisions = [
        v for v in verdicts
        if isinstance(v, dict) and isinstance(v.get("revision"), dict)
    ]
    if not revisions:
        return None
    good = 0
    for v in revisions:
        evidence = v["revision"].get("peer_evidence", "") or ""
        if not isinstance(evidence, str):
            continue
        normalized = evidence.strip().lower()
        if len(normalized) >= 20 and normalized not in _PEER_EVIDENCE_BOILERPLATE:
            good += 1
    return good / len(revisions)


def personalities_divergence(bundle: dict) -> float | None:
    """For Trias mode: fraction of personalities (Pioneer/Architect/Steward)
    that picked different `chosen` candidates. Returns None outside Trias.

    1.0 = full divergence (3 different chosen IDs).
    0.0 = full convergence (all 3 picked the same candidate) — advisory
    flag: lenses may not be biasing perception as intended.
    """
    team = bundle.get("team")
    if team != "trias":
        return None
    members = bundle.get("members") or bundle.get("personalities") or {}
    if not isinstance(members, dict) or not members:
        return None
    chosen_ids: list[str] = []
    for entry in members.values():
        if isinstance(entry, dict):
            cid = entry.get("chosen") or entry.get("chosen_approach")
            if isinstance(cid, str) and cid:
                chosen_ids.append(cid)
    if len(chosen_ids) < 2:
        return None
    return (len(set(chosen_ids)) - 1) / (len(chosen_ids) - 1)


def control_speculation_flag(verdicts: list[dict]) -> int:
    """Count verdicts that mark themselves `valid: true` while declaring
    `confidence_in_verdict: low` — Control admitting it speculated rather
    than verified. Returns 0 when the field is absent (legacy verdicts).
    """
    count = 0
    for v in verdicts:
        if not isinstance(v, dict):
            continue
        if v.get("valid") is True and v.get("confidence_in_verdict") == "low":
            count += 1
    return count


def critique(bundle: dict) -> dict:
    control = (bundle.get("control") or {}).get("verdicts") or []
    conservator = (bundle.get("conservator") or {}).get("scores") or []

    cs = conservator_spread(conservator)
    cs_rounded = round(cs, 3) if cs is not None else None

    # Optional metrics — emitted only when the relevant mode is active.
    prq_raw = pass2_revision_quality(bundle)
    pd_raw = personalities_divergence(bundle)
    speculation = control_speculation_flag(control)

    flags: list[str] = []
    if cs_rounded is not None and cs_rounded < WARNING["conservator_spread"]:
        sev = "shrug" if cs_rounded < DEGENERATE["conservator_spread"] else "weak"
        flags.append(f"conservator_spread={cs_rounded} {sev} — risk scores cluster")
    if prq_raw is not None and prq_raw < 0.5:
        flags.append(
            f"pass2_revision_quality={round(prq_raw, 3)} thin — "
            "peer_evidence boilerplate or under 20 chars"
        )
    if pd_raw is not None and pd_raw == 0.0:
        flags.append(
            "personalities_divergence=0.0 advisory — Trias lenses converged on "
            "the same chosen; verify lens injection is biasing perception"
        )
    if speculation > 0:
        flags.append(
            f"control_speculation={speculation} — verdicts marked valid:true with "
            "confidence_in_verdict:low (Control speculated rather than verified)"
        )

    quality: dict[str, object] = {
        "conservator_spread": cs_rounded,
        "flags": flags,
    }
    if prq_raw is not None:
        quality["pass2_revision_quality"] = round(prq_raw, 3)
    if pd_raw is not None:
        quality["personalities_divergence"] = round(pd_raw, 3)
    if speculation:
        quality["control_speculation"] = speculation
    return {"deliberation_quality": quality}


def main(argv: list[str] | None = None) -> int:
    force_utf8_streams()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--strict", action="store_true", help="exit 1 if any metric is degenerate")
    args = ap.parse_args(argv)

    bundle = load_json_stdin("meta_critic.py")
    if not isinstance(bundle, dict):
        print("meta_critic: bundle must be a JSON object", file=sys.stderr)
        return 2

    mode = (bundle.get("telemetry") or {}).get("mode", "")
    if mode == "trias":
        args.strict = True

    result = critique(bundle)
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")

    if args.strict:
        q = result["deliberation_quality"]
        if q["conservator_spread"] is not None and q["conservator_spread"] < DEGENERATE["conservator_spread"]:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
