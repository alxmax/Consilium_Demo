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

from utils import force_utf8_streams, validate_keys

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

    Valid with no issues = 1.0; each issue subtracts 0.15 (down to 0.3).
    Invalid = 0.0. This is intentionally crude — Control's job is
    correctness, not nuanced ranking; nuance lives in Conservator.
    """
    if not verdict.get("valid"):
        return 0.0
    issues = verdict.get("issues") or []
    return max(0.3, 1.0 - 0.15 * len(issues))


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


def validate_input(payload: dict) -> None:
    """Validate dialectic_merge input has required pass1 structure."""
    validate_keys(payload, ["pass1"], context="dialectic_merge input")
    validate_keys(payload["pass1"], ["generator", "control", "conservator"],
                  context="dialectic_merge input.pass1")


def _diff_candidates(p1: list[dict], p2: list[dict]) -> list[dict]:
    """Per-id field diff between two candidate lists."""
    p1_by_id = _items_by_id(p1)
    p2_by_id = _items_by_id(p2)
    diffs: list[dict] = []
    for cid in sorted(set(p1_by_id) | set(p2_by_id)):
        if cid not in p1_by_id:
            diffs.append({"id": cid, "change": "added"})
            continue
        if cid not in p2_by_id:
            diffs.append({"id": cid, "change": "removed"})
            continue
        a, b = p1_by_id[cid], p2_by_id[cid]
        changed = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
        if changed:
            diffs.append({"id": cid, "change": "modified", "fields": changed})
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

        gen_cand = (
            cand if is_new_in_pass2
            else (p1_gen_by_id.get(cid, cand) if cid in dissent_fallbacks.get("generator", []) else cand)
        )
        verdict = (
            ctrl_verdicts.get(cid, {}) if is_new_in_pass2
            else (p1_ctrl_by_id.get(cid, {}) if cid in dissent_fallbacks.get("control", []) else ctrl_verdicts.get(cid, {}))
        )
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
                "conservator": float(risk_entry.get("risk_score", 0.5)),
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
            p1_verdict = p1_ctrl_by_id.get(cid, {})
            p1_risk = p1_cons_by_id.get(cid, {})
            merged_candidates.append({
                "id": cid,
                "summary": p1_cand.get("summary", ""),
                "scores": {
                    "generator": _generator_score(p1_cand),
                    "control": _voice_score_from_verdict(p1_verdict),
                    "conservator": float(p1_risk.get("risk_score", 0.5)),
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
    args = ap.parse_args(argv)

    try:
        payload: dict[str, Any] = json.load(args.input)
    except json.JSONDecodeError as exc:
        print(f"invalid JSON: {exc}", file=sys.stderr)
        return 2

    validate_input(payload)

    try:
        result = merge(payload)
    except ValueError as exc:
        print(f"merge failed: {exc}", file=sys.stderr)
        return 1

    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
