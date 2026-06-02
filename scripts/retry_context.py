"""Identify what to read before retrying a low-confidence deliberation.

When ``confidence < 0.7`` the current SKILL.md flow asks the user to
override or skip. Often the right move is neither — what's missing is
*context*, not user judgment. This script proposes a single retry with
enriched input by:

1. Picking the **top-2 candidates** by utility (mean of generator,
   control, and 1 - conservator). These are the close-rivals — extra
   context disambiguates them, not the also-rans.
2. Extracting **concrete targets** from their sketches: file paths,
   symbol names, function calls. These point at what to read/grep
   before re-deliberation.
3. Emitting a small JSON plan: per-candidate suggested context-gathering
   commands (Read, Grep, churn). The agent runs the commands, attaches
   results to the bundle as ``retry_context``, and dispatches one more
   Generator/Control/Conservator pass with the enriched input.

The script does NOT itself run the deliberation. It is one-shot — the
agent calls it at most once per run (per SKILL.md). If after the retry
confidence is still under threshold, fall back to the existing user-ask
flow.

Output shape:

    {
      "retry_recommended": true,
      "reason": "confidence=0.61 below 0.70 threshold",
      "top_candidates": [
        {
          "id": "approach_a",
          "utility": 0.72,
          "targets": ["scripts/foo.py", "bar()", "baz.module"],
          "suggested_reads": ["scripts/foo.py"],
          "suggested_greps": ["bar\\(", "baz"]
        },
        ...
      ]
    }

When confidence is at/above threshold, or when the bundle has only one
candidate, ``retry_recommended`` is false and ``top_candidates`` is empty.

CLI:
    cat bundle.json | python scripts/retry_context.py
    cat bundle.json | python scripts/retry_context.py --threshold 0.7
"""
# implements: CONSILIUM-RETRY-CONTEXT-001

from __future__ import annotations

import argparse
import json
import re
import sys

from utils import force_utf8_streams, load_json_stdin


DEFAULT_THRESHOLD = 0.7
TOP_K = 2

FILE_RE = re.compile(r"[\w][\w./\-]*\.(?:py|md|js|ts|tsx|html|css|json|yml|yaml|sh|toml)\b")
SYMBOL_CALL_RE = re.compile(r"\b([a-zA-Z_][a-zA-Z0-9_]{2,})\s*\(")
DOTTED_RE = re.compile(r"\b([a-zA-Z_][\w]*\.[a-zA-Z_][\w]+(?:\.[a-zA-Z_][\w]+)*)\b")
BACKTICK_RE = re.compile(r"`([\w.]{2,40})`")


def _utility(scores: dict) -> float:
    return (
        float(scores.get("generator", 0.0))
        + float(scores.get("control", 0.0))
        + (1.0 - float(scores.get("conservator", 0.5)))
    ) / 3.0


def _scores_for(cid: str, control: list, conservator: list) -> dict:
    """Compose voice scores for a candidate from Control + Conservator outputs."""
    verdict = next((v for v in control if isinstance(v, dict) and v.get("id") == cid), {})
    risk = next((s for s in conservator if isinstance(s, dict) and s.get("id") == cid), {})
    issues = verdict.get("issues") or []
    control_score = 0.0 if not verdict.get("valid") else max(0.3, 1.0 - 0.15 * len(issues))
    # Conservator risk lives at regression_risk.net_concern (conservator.md);
    # the old top-level risk_score key is never populated, so retry top-2
    # selection was risk-blind (every candidate got 0.5). Mirror build_report.
    rr = risk.get("regression_risk")
    if isinstance(rr, dict) and isinstance(rr.get("net_concern"), (int, float)):
        risk_score = rr["net_concern"]
    else:
        risk_score = risk.get("risk_score", 0.5)
    return {
        "generator": 0.5 if cid == "do_nothing" or cid.startswith("adversarial_") else 1.0,
        "control": round(control_score, 3),
        "conservator": float(risk_score) if isinstance(risk_score, (int, float)) else 0.5,
    }


def extract_targets(candidate: dict) -> dict:
    """Pull file paths and symbol/function names out of a candidate's sketch + summary."""
    text = f"{candidate.get('summary', '')} {candidate.get('sketch', '')}"
    files = sorted(set(FILE_RE.findall(text)))
    symbols_calls = sorted(set(SYMBOL_CALL_RE.findall(text)))
    dotted = sorted(set(DOTTED_RE.findall(text)))
    quoted = sorted(set(BACKTICK_RE.findall(text)))
    # Combine candidate symbols, drop super-common stopwords
    stop = {"def", "the", "for", "and", "with", "this", "that", "from"}
    symbols = sorted({s for s in symbols_calls + dotted + quoted if s.lower() not in stop and len(s) >= 3})
    return {"files": files, "symbols": symbols}


def _grep_patterns(symbols: list[str], cap: int = 4) -> list[str]:
    out: list[str] = []
    for s in symbols[:cap]:
        # Escape regex metachars for grep
        escaped = re.escape(s)
        # Only suffix \( for plain function names (no dot); dotted attribute
        # paths (foo.bar) are not necessarily callable.
        if "(" not in s and "." not in s:
            out.append(escaped + r"\(")
        out.append(escaped)
    # De-dupe preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for p in out:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    return unique[:cap]


def plan_retry(bundle: dict, threshold: float = DEFAULT_THRESHOLD) -> dict:
    confidence = bundle.get("confidence")
    if isinstance(confidence, dict):
        confidence = confidence.get("confidence")
    confidence_val = confidence if isinstance(confidence, (int, float)) else None

    if confidence_val is None:
        reason = "confidence=null (all candidates vetoed)"
        retry = False
    elif confidence_val >= threshold:
        reason = f"confidence={confidence_val:.2f} at/above threshold {threshold}"
        retry = False
    else:
        reason = f"confidence={confidence_val:.2f} below {threshold} threshold"
        retry = True

    if not retry:
        return {"retry_recommended": False, "reason": reason, "top_candidates": []}

    candidates = (bundle.get("generator") or {}).get("candidates") or []
    control_verdicts = (bundle.get("control") or {}).get("verdicts") or []
    cons_scores = (bundle.get("conservator") or {}).get("scores") or []

    # Filter to candidates that Control marked valid (or trivially included)
    valid_ids = {v.get("id") for v in control_verdicts if isinstance(v, dict) and v.get("valid")}
    pool = [c for c in candidates if isinstance(c, dict) and c.get("id") in valid_ids] or list(candidates)

    if len(pool) < 2:
        return {
            "retry_recommended": False,
            "reason": "too few valid candidates for retry to discriminate",
            "top_candidates": [],
        }

    ranked = sorted(
        [(c, _utility(_scores_for(c.get("id", ""), control_verdicts, cons_scores))) for c in pool],
        key=lambda pair: pair[1],
        reverse=True,
    )[:TOP_K]

    top: list[dict] = []
    for cand, util in ranked:
        targets = extract_targets(cand)
        top.append({
            "id": cand.get("id"),
            "utility": round(util, 3),
            "files": targets["files"],
            "symbols": targets["symbols"],
            "suggested_reads": targets["files"][:4],
            "suggested_greps": _grep_patterns(targets["symbols"]),
        })

    return {"retry_recommended": True, "reason": reason, "top_candidates": top}


def main(argv: list[str] | None = None) -> int:
    force_utf8_streams()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD, help="confidence threshold (default 0.7)")
    args = ap.parse_args(argv)

    bundle = load_json_stdin("retry_context.py")
    if not isinstance(bundle, dict):
        print("retry_context: bundle must be a JSON object", file=sys.stderr)
        return 2

    result = plan_retry(bundle, threshold=args.threshold)
    json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
