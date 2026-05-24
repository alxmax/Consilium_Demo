"""Merge two-pass dialectic outputs into a single aggregator-ready payload.

In dialectic mode, the three voices each run twice:

- **Pass 1**: each voice produces its initial output in isolation
  (parallel sub-agents, same as parallel mode).
- **Pass 2**: each voice receives the other two voices' Pass-1 outputs
  and may revise its own — agree, refine, or push back. One round only.

Pass-2 outputs are authoritative for the final report. This script
projects the six raw outputs (3 voices × 2 passes) into the shape the
existing ``aggregator.py`` already understands, plus a ``revision_log``
that records what each voice changed between passes — auditable evidence
the dialectic actually moved the needle (or didn't).

If Pass-2 is missing for a voice (e.g. the sub-agent timed out, or you
chose to skip its revision because Pass-1 was already unanimous), this
script falls back to that voice's Pass-1 output and tags the entry with
``fallback_to_pass1: true``. Whole-pass-2 absence is also tolerated —
the script degrades cleanly to a single-pass payload with a warning
flag, rather than crashing.

If Pass-2 generator silently drops a Pass-1 candidate (omits it from
its output without re-emitting it — neither compliant nor non-compliant),
the candidate is recovered from Pass-1 data, tagged
``pass2_status: "dropped_silently"`` on the merged entry, and listed in
``revision_log.silently_dropped``. Without this recovery the candidate
would vanish from merged output entirely — a silent data loss.

Input format on stdin (JSON):
    {
      "pass1": {
        "generator": {"candidates": [...]},
        "control":   {"verdicts":   [...]},
        "conservator":{"scores":    [...]}
      },
      "pass2": {                          // optional whole-key
        "generator": {"candidates": [...]},   // optional per-voice
        "control":   {"verdicts":   [...]},
        "conservator":{"scores":    [...]}
      }
    }

Output: a dict the aggregator can consume directly, with merged
``candidates`` (each carrying both gen/ctrl/cons scores derived from
Pass-2 verdicts and scores) plus a ``revision_log`` summary.

CLI:
    cat dialectic.json | python scripts/dialectic_merge.py
    python scripts/dialectic_merge.py --input dialectic.json
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from utils import force_utf8_streams, issue_penalty

VOICES = ("generator", "control", "conservator")
VOICE_KEY = {
    "generator": "candidates",
    "control": "verdicts",
    "conservator": "scores",
}


def _items_by_id(items: list[dict]) -> dict[str, dict]:
    return {item["id"]: item for item in items if "id" in item}


def _final_voice_output(
    pass1: dict, pass2: dict | None, voice: str
) -> tuple[dict, bool]:
    """Return (authoritative_output, fell_back_to_pass1)."""
    key = VOICE_KEY[voice]
    p1 = pass1.get(voice, {})
    if pass2 is None or voice not in pass2:
        return p1, True
    p2 = pass2[voice]
    if not p2.get(key):
        return p1, True
    return p2, False


def _voice_score_from_verdict(verdict: dict) -> float:
    """Translate Control's binary verdict into a [0,1] utility score.

    Valid with no issues = 1.0; penalty per issue scaled by severity
    (low=0.05, medium=0.15, high=0.30); floor at 0.3.
    Invalid = 0.0.
    """
    if not verdict.get("valid"):
        return 0.0
    issues = verdict.get("issues") or []
    return max(0.3, 1.0 - sum(issue_penalty(i) for i in issues))


def _merge_pass2_control_verdict(p2_verdict: dict, p1_verdict: dict) -> dict:
    """Combine Pass-2 control metadata with Pass-1 verdict body.

    control_pass2.md schema is {id, revision|maintained} — Pass-2 carries
    only the dissent metadata, not valid/issues. Without inheriting Pass-1's
    valid/issues, every compliant Pass-2 verdict scores 0.0 in
    `_voice_score_from_verdict`, collapsing dialectic aggregation.

    Strict inheritance: Pass-1 is the base; Pass-2 wins only if it explicitly
    re-emits a field. revision/maintained metadata is preserved for audit.
    """
    merged = dict(p1_verdict)
    for k in ("valid", "issues", "tests_to_write", "notes"):
        if k in p2_verdict:
            merged[k] = p2_verdict[k]
    for k in ("revision", "maintained"):
        if k in p2_verdict:
            merged[k] = p2_verdict[k]
    return merged


def _safe_risk_score(risk_entry: dict, default: float = 0.5) -> float:
    """`float(risk_entry.get("risk_score", default))` blows up on explicit
    null risk_score; treat None the same as missing.
    """
    rs = risk_entry.get("risk_score")
    if rs is None:
        return default
    return float(rs)


def _generator_score(candidate: dict) -> float:
    """Generator's own confidence in a candidate.

    We don't ask Generator for a score; we infer 1.0 for normal
    candidates and 0.5 for ``do_nothing`` / ``adversarial_*`` —
    they're scaffolding, not real proposals. Aggregator + Control
    + Conservator do the actual ranking.
    """
    cid = candidate.get("id", "")
    if cid == "do_nothing" or cid.startswith("adversarial_"):
        return 0.5
    return 1.0


def _is_dissent_compliant(item: dict) -> bool:
    """Return True if a Pass-2 voice item has revision or maintained field (non-empty)."""
    revision = item.get("revision")
    maintained = item.get("maintained")
    return bool(revision) or bool(maintained)


def should_skip_pass2(pass1: dict) -> tuple[bool, list[str]]:
    """Return (skip, reasons) based on Pass-1 convergence criteria.

    All three must hold to skip Pass 2:
    1. All Control verdicts valid (no invalid candidates)
    2. Generator preferred matches Conservator lowest-risk candidate
    3. No substantial Control disagreements

    Call before dispatching Pass-2 sub-agents. If skip=True, call merge()
    with pass2 omitted — result will include dialectic_metadata.pass2_executed=False.
    """
    control = pass1.get("control", {})
    generator = pass1.get("generator", {})
    conservator = pass1.get("conservator", {})

    reasons: list[str] = []

    verdicts = control.get("verdicts", [])
    if not verdicts or not all(v.get("valid") for v in verdicts):
        reasons.append("not_all_valid")

    preferred = generator.get("preferred")
    scores: list[dict] = conservator.get("scores", [])
    if scores:
        lowest_risk: dict = min(scores, key=lambda s: _safe_risk_score(s))
        if preferred != lowest_risk.get("id"):
            reasons.append("preferred_differs_from_lowest_risk")
    else:
        reasons.append("no_conservator_scores")

    disagreements = control.get("disagreements", [])
    substantial = [d for d in disagreements if isinstance(d, dict) and d.get("type") == "substantial"]
    if substantial:
        reasons.append("substantial_disagreements")

    skip = len(reasons) == 0
    if skip:
        reasons = ["all_valid", "preferred_matches_lowest_risk", "no_substantial_disagreement"]
    return skip, reasons


def validate_input(payload: dict) -> None:
    """Validate dialectic_merge input has required pass1 structure."""
    if "pass1" not in payload:
        raise ValueError("dialectic_merge input: missing required field 'pass1'")
    for voice in ("generator", "control", "conservator"):
        if voice not in payload["pass1"]:
            raise ValueError(
                f"dialectic_merge input.pass1: missing required field '{voice}'"
            )
    if "pass2" in payload and not isinstance(payload["pass2"], dict):
        raise ValueError(
            f"dialectic_merge: pass2 must be a dict, got {type(payload['pass2']).__name__}"
        )


def _diff_candidates(p1: list[dict], p2: list[dict]) -> list[dict]:
    """Per-id field diff between two candidate lists.

    Emits enough payload for consumers to render a real before/after diff:
    - `added`   → `after`  carries the full new item
    - `removed` → `before` carries the full removed item
    - `modified`→ `fields` lists changed keys; `before`/`after` carry the
                  per-key values so reviewers see what actually changed
                  without re-deriving from raw bundles.
    """
    p1_by_id = _items_by_id(p1)
    p2_by_id = _items_by_id(p2)
    diffs: list[dict] = []
    for cid in sorted(set(p1_by_id) | set(p2_by_id)):
        if cid not in p1_by_id:
            diffs.append({"id": cid, "change": "added", "after": p2_by_id[cid]})
            continue
        if cid not in p2_by_id:
            diffs.append({"id": cid, "change": "removed", "before": p1_by_id[cid]})
            continue
        a, b = p1_by_id[cid], p2_by_id[cid]
        changed = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
        if changed:
            diffs.append({
                "id": cid,
                "change": "modified",
                "fields": changed,
                "before": {k: a.get(k) for k in changed},
                "after": {k: b.get(k) for k in changed},
            })
    return diffs


def merge(payload: dict) -> dict:
    pass1 = payload.get("pass1") or {}
    pass2 = payload.get("pass2")

    if not pass1:
        raise ValueError("pass1 is required")

    fallbacks: dict[str, bool] = {}
    final: dict[str, dict] = {}
    for voice in VOICES:
        out, fell_back = _final_voice_output(pass1, pass2, voice)
        final[voice] = out
        fallbacks[voice] = fell_back

    # Pass-1 lookups kept for per-candidate dissent fallback
    p1_gen_by_id = _items_by_id((pass1.get("generator") or {}).get("candidates", []))
    p1_ctrl_by_id = _items_by_id((pass1.get("control") or {}).get("verdicts", []))
    p1_cons_by_id = _items_by_id((pass1.get("conservator") or {}).get("scores", []))

    # Per-voice, per-candidate dissent fallback: pass2 item lacks both revision and maintained
    dissent_fallbacks: dict[str, list[str]] = {}
    if pass2 is not None:
        for voice in VOICES:
            if fallbacks[voice]:
                continue  # entire voice already fell back to pass1
            key = VOICE_KEY[voice]
            p2_items = (pass2.get(voice) or {}).get(key, [])
            bad_ids = [
                item["id"]
                for item in p2_items
                if item.get("id") and not _is_dissent_compliant(item)
            ]
            if bad_ids:
                dissent_fallbacks[voice] = bad_ids

    gen_candidates = final["generator"].get("candidates", [])
    ctrl_verdicts = _items_by_id(final["control"].get("verdicts", []))
    cons_scores = _items_by_id(final["conservator"].get("scores", []))

    merged_candidates: list[dict] = []
    for cand in gen_candidates:
        cid = cand.get("id")
        if not cid:
            continue

        # Candidates new in Pass-2 (not in Pass-1 at all) must never fall back to
        # empty Pass-1 data — that would produce a 0.0 control score for a valid
        # candidate. Always use Pass-2 voice data for genuinely new candidates.
        is_new_in_pass2 = cid not in p1_gen_by_id

        gen_cand: dict = (
            cand if is_new_in_pass2
            else (p1_gen_by_id.get(cid) or cand if cid in dissent_fallbacks.get("generator", []) else cand)
        )
        # Control: Pass-2 carries only revision/maintained metadata per
        # control_pass2.md — valid/issues stay in Pass-1. Merge so a compliant
        # Pass-2 verdict doesn't collapse to control_score=0.0.
        p1_verdict = p1_ctrl_by_id.get(cid, {})
        if is_new_in_pass2:
            verdict = ctrl_verdicts.get(cid, {})
        elif cid in dissent_fallbacks.get("control", []):
            verdict = p1_verdict
        else:
            verdict = _merge_pass2_control_verdict(ctrl_verdicts.get(cid, {}), p1_verdict)
        risk_entry = (
            cons_scores.get(cid, {}) if is_new_in_pass2
            else (p1_cons_by_id.get(cid, {}) if cid in dissent_fallbacks.get("conservator", []) else cons_scores.get(cid, {}))
        )

        merged_candidates.append({
            "id": cid,
            "summary": gen_cand.get("summary", ""),
            "scores": {
                "generator": _generator_score(gen_cand),
                "control": _voice_score_from_verdict(verdict),
                "conservator": _safe_risk_score(risk_entry),
            },
        })

    # Recover candidates the Pass-2 generator dropped silently. Only triggers when
    # Pass-2 generator was actually consulted — when the whole voice fell back to
    # Pass-1, every candidate is already in merged_candidates from the loop above.
    silently_dropped: list[str] = []
    if pass2 is not None and not fallbacks["generator"]:
        seen = {c["id"] for c in merged_candidates}
        for cid, p1_cand in p1_gen_by_id.items():
            if cid in seen:
                continue
            silently_dropped.append(cid)
            p1_verdict_recovered = p1_ctrl_by_id.get(cid, {})
            p1_risk = p1_cons_by_id.get(cid, {})
            merged_candidates.append({
                "id": cid,
                "summary": p1_cand.get("summary", ""),
                "scores": {
                    "generator": _generator_score(p1_cand),
                    "control": _voice_score_from_verdict(p1_verdict_recovered),
                    "conservator": _safe_risk_score(p1_risk),
                },
                "pass2_status": "dropped_silently",
            })

    revision_log = {
        "pass2_received": pass2 is not None,
        "fallback_to_pass1": fallbacks,
        "dissent_fallbacks": dissent_fallbacks,
        "silently_dropped": silently_dropped,
        "diffs": {},
    }
    if pass2 is not None:
        for voice in VOICES:
            if fallbacks[voice]:
                continue
            key = VOICE_KEY[voice]
            revision_log["diffs"][voice] = _diff_candidates(
                pass1.get(voice, {}).get(key, []),
                pass2.get(voice, {}).get(key, []),
            )

    # C2: count Pass-2 position changes (revision vs maintained) per voice
    if pass2 is not None:
        pass2_revisions: dict[str, int] = {}
        for voice in VOICES:
            if fallbacks.get(voice):
                continue
            key = VOICE_KEY[voice]
            items = (pass2.get(voice) or {}).get(key, [])
            revisions = sum(1 for item in items if isinstance(item, dict) and "revision" in item)
            pass2_revisions[voice] = revisions
        revision_log["pass2_revisions"] = pass2_revisions

    # Dialectic metadata for convergence reporting
    _, _criteria = should_skip_pass2(pass1)
    revision_log["dialectic_metadata"] = {
        "pass2_executed": pass2 is not None,
        "pass2_skip_reason": None if pass2 is not None else "pass1_converged",
        "convergence_criteria_met": _criteria,
    }

    return {
        "candidates": merged_candidates,
        "revision_log": revision_log,
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
    ap.add_argument(
        "--check-pass2",
        action="store_true",
        help="Check Pass-1 convergence and output {skip_pass2, reasons} without merging",
    )
    args = ap.parse_args(argv)

    try:
        payload: dict[str, Any] = json.load(args.input)
    except json.JSONDecodeError as exc:
        print(f"invalid JSON: {exc}", file=sys.stderr)
        return 2

    if args.check_pass2:
        try:
            validate_input(payload)
        except ValueError as exc:
            print(f"invalid input: {exc}", file=sys.stderr)
            return 2
        skip, reasons = should_skip_pass2(payload.get("pass1", {}))
        json.dump({"skip_pass2": skip, "reasons": reasons}, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    try:
        validate_input(payload)
    except ValueError as exc:
        print(f"invalid input: {exc}", file=sys.stderr)
        return 2

    try:
        result = merge(payload)
    except ValueError as exc:
        print(f"merge failed: {exc}", file=sys.stderr)
        return 1

    _emit_fallback_warnings(result.get("revision_log") or {})

    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


def _emit_fallback_warnings(revision_log: dict) -> None:
    """Surface silent Pass-2 fallbacks so the orchestrator notices a 2× cost
    deliberation degraded into Pass-1 for some voices/candidates.

    Three failure modes get a warning each:
      - whole-voice fallback (sub-agent skipped Pass-2 entirely)
      - per-candidate dissent fallback (Pass-2 item lacks revision/maintained)
      - silently dropped candidate (Pass-2 generator omitted a Pass-1 id)
    """
    fallbacks = revision_log.get("fallback_to_pass1") or {}
    fallen = [v for v, fell in fallbacks.items() if fell]
    if fallen:
        print(
            f"[warning] dialectic pass-2 fell back to pass-1 entirely for: "
            f"{', '.join(sorted(fallen))} — sub-agent skipped pass-2 or returned empty",
            file=sys.stderr,
        )

    dissent_fallbacks = revision_log.get("dissent_fallbacks") or {}
    for voice, ids in dissent_fallbacks.items():
        if ids:
            print(
                f"[warning] dialectic pass-2 dissent fallback for {voice}: "
                f"{', '.join(sorted(ids))} — items missing required "
                f"'revision' or 'maintained' field",
                file=sys.stderr,
            )

    dropped = revision_log.get("silently_dropped") or []
    if dropped:
        print(
            f"[warning] dialectic pass-2 generator silently dropped candidates: "
            f"{', '.join(sorted(dropped))} — recovered from pass-1 data",
            file=sys.stderr,
        )


if __name__ == "__main__":
    raise SystemExit(main())
