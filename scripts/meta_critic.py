"""Score the *quality* of a deliberation — not whether the chosen candidate is good.

``validate_report.py`` enforces JSON schema; this script enforces that the
three voices actually did distinct, concrete work. Without it, a deliberation
can pass every shape check while being intellectually empty: Generator emits
4 paraphrases of the same idea, Control speculates with no file references,
Conservator assigns 0.5 to everything.

Run between Step 5b (confidence) and Step 6 (build_report). Reads a bundle
from stdin and emits a ``deliberation_quality`` block to stdout that
``build_report.py`` can attach to the report.

Three metrics, each in [0,1] with 1 = healthy:

- **generator_divergence**: 1 - mean pairwise sketch similarity (Jaccard on
  word tokens, lowercased, len >= 4). Detects "4 variants of the same idea".
  Threshold: < 0.4 = degenerate, < 0.6 = weak.

- **control_concreteness**: fraction of issues whose detail mentions a file
  path, line number, symbol, or specific category beyond the generic
  catch-alls. Detects speculation-without-checking. Vacuous verdicts
  (valid=true, no issues, no tests) don't count against the score.
  Threshold: < 0.3 = speculative, < 0.5 = thin.

- **conservator_spread**: stdev of risk_scores across valid candidates,
  rescaled by the maximum possible stdev (~0.5 for 2-value bimodal). Detects
  the "0.5 shrug" pattern where every candidate gets identical risk.
  Threshold: < 0.1 = shrug, < 0.2 = weak.

Output shape:

    {
      "deliberation_quality": {
        "generator_divergence": 0.72,
        "control_concreteness": 0.55,
        "conservator_spread":   0.18,
        "flags": [
          "conservator_spread=0.18 weak — risk scores cluster near mean"
        ]
      }
    }

Flags only appear when a metric falls below its warning threshold. An
empty ``flags`` list means the deliberation looks healthy. The block is
advisory — it does NOT veto the chosen candidate. Use ``--strict`` to
exit 1 when any metric falls below the *degenerate* threshold so a CI
hook can fail noisily.

CLI:
    cat bundle.json | python scripts/meta_critic.py
    cat bundle.json | python scripts/meta_critic.py --strict
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys

from utils import force_utf8_streams, load_json_stdin


TOKEN_RE = re.compile(r"[a-z]{4,}")
STOPWORDS = {
    "with", "from", "this", "that", "were", "will", "would", "into",
    "than", "after", "before", "when", "where", "what", "have", "been",
    "code", "file", "files", "change", "changes", "logic", "case", "cases",
    "make", "makes", "uses", "used", "using", "current", "approach", "step",
    "steps", "side", "more", "less",
}
# Markers that suggest a Control issue is "concrete" (touches reality, not vibes)
CONCRETENESS_HINTS = re.compile(
    r"(?:^|[\s/\.])(?:line|lines|file|files|in [a-zA-Z_][\w]*\.|"
    r"`[^`]+`|[a-zA-Z_][\w]*\.(?:py|md|js|ts|html|css|json)|"
    r"[a-zA-Z_][\w]+\(|[a-zA-Z_][\w]+::|"
    r"[a-zA-Z_][\w]+\.[a-zA-Z_][\w]+|"
    r"\.py:\d+|\.js:\d+|line \d+)"
)
# Maximum stdev for risk_scores in [0,1]: bimodal {0, 1} -> pstdev = 0.5
MAX_RISK_STDEV = 0.5

DEGENERATE = {
    "generator_divergence": 0.40,
    "control_concreteness": 0.30,
    "conservator_spread":   0.10,
}
WARNING = {
    "generator_divergence": 0.60,
    "control_concreteness": 0.50,
    "conservator_spread":   0.20,
}


def _tokens(text: str) -> set[str]:
    if not text:
        return set()
    return {t for t in TOKEN_RE.findall(text.lower()) if t not in STOPWORDS}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    union = a | b
    if not union:
        return 1.0
    return len(a & b) / len(union)


def generator_divergence(candidates: list[dict]) -> float:
    """1 - mean pairwise Jaccard similarity of (summary + sketch) tokens.

    Excludes ``do_nothing`` and ``adversarial_*`` from the divergence
    measurement — they're spec-mandated stubs, not Generator's creative output,
    and would inflate divergence artificially.
    """
    real = [
        c for c in candidates
        if isinstance(c, dict)
        and c.get("id") not in (None, "")
        and c["id"] != "do_nothing"
        and not str(c.get("id", "")).startswith("adversarial_")
    ]
    if len(real) < 2:
        return 1.0
    bags = [_tokens(f"{c.get('summary', '')} {c.get('sketch', '')}") for c in real]
    sims: list[float] = []
    for i in range(len(bags)):
        for j in range(i + 1, len(bags)):
            sims.append(_jaccard(bags[i], bags[j]))
    if not sims:
        return 1.0
    return max(0.0, min(1.0, 1.0 - statistics.fmean(sims)))


def _issue_is_concrete(issue: dict) -> bool:
    detail = issue.get("detail", "") or ""
    if not isinstance(detail, str):
        return False
    return bool(CONCRETENESS_HINTS.search(detail))


def control_concreteness(verdicts: list[dict]) -> float:
    """Fraction of Control issues that mention a file/symbol/line OR provide
    >= 40 chars of detail. Verdicts with no issues are ignored (a valid
    candidate with no objections is a legitimate signal, not laziness).
    """
    issues: list[dict] = []
    for v in verdicts:
        if not isinstance(v, dict):
            continue
        for it in v.get("issues") or []:
            if isinstance(it, dict):
                issues.append(it)
    if not issues:
        # Nothing to evaluate; treat as healthy. Empty issues means Control
        # had nothing to flag, not that it was lazy.
        return 1.0
    concrete = sum(1 for it in issues if _issue_is_concrete(it))
    return concrete / len(issues)


def conservator_spread(scores: list[dict]) -> float:
    """Risk score stdev / max possible stdev, clamped to [0,1].

    Filters to valid candidates only (risk_score present + numeric). A single
    candidate returns 0.0 (no spread possible).
    """
    risks: list[float] = []
    for s in scores:
        if not isinstance(s, dict):
            continue
        r = s.get("risk_score")
        if isinstance(r, (int, float)):
            risks.append(float(r))
    if len(risks) < 2:
        return 0.0
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
    generator = (bundle.get("generator") or {}).get("candidates") or []
    control = (bundle.get("control") or {}).get("verdicts") or []
    conservator = (bundle.get("conservator") or {}).get("scores") or []

    gd = round(generator_divergence(generator), 3)
    cc = round(control_concreteness(control), 3)
    cs = round(conservator_spread(conservator), 3)

    # Optional metrics — emitted only when the relevant mode is active.
    prq_raw = pass2_revision_quality(bundle)
    pd_raw = personalities_divergence(bundle)
    speculation = control_speculation_flag(control)

    flags: list[str] = []
    if gd < WARNING["generator_divergence"]:
        sev = "degenerate" if gd < DEGENERATE["generator_divergence"] else "weak"
        flags.append(f"generator_divergence={gd} {sev} — candidates overlap heavily")
    if cc < WARNING["control_concreteness"]:
        sev = "degenerate" if cc < DEGENERATE["control_concreteness"] else "thin"
        flags.append(f"control_concreteness={cc} {sev} — issues lack file/symbol references")
    if cs < WARNING["conservator_spread"]:
        sev = "shrug" if cs < DEGENERATE["conservator_spread"] else "weak"
        flags.append(f"conservator_spread={cs} {sev} — risk scores cluster")
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
        "generator_divergence": gd,
        "control_concreteness": cc,
        "conservator_spread":   cs,
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
        if (
            q["generator_divergence"] < DEGENERATE["generator_divergence"]
            or q["control_concreteness"] < DEGENERATE["control_concreteness"]
            or q["conservator_spread"]   < DEGENERATE["conservator_spread"]
        ):
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
