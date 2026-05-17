"""Strip cross-voice context to reduce contamination in sequential mode.

In sequential mode, the same agent plays all three voices in one
context window. Generator's rationales leak into Control's verdict
write-up; Control's issue language leaks into Conservator's framing.
This script projects the previous voice's output down to the minimum
fields the next voice actually needs to do its job.

Two projections:

- ``--for control`` reads a Generator output and emits the candidate
  list with ONLY ``id``, ``summary``, ``sketch``. Drops ``rationale``
  (rhetoric that biases technical validation).

- ``--for conservator`` reads a Control output and emits valid
  verdicts with ONLY ``id`` plus the matching candidate's ``id``,
  ``summary``, ``sketch``. Drops ``issues`` and ``notes`` (rhetoric
  that biases risk scoring), and skips ``valid: false`` entries
  entirely — Conservator should never score those.

Input shape for ``--for conservator`` is the union of Generator and
Control outputs, passed as one JSON object::

    {
      "candidates": [...],   # from Generator
      "verdicts":   [...]    # from Control
    }

This is intentional: Conservator needs the original ``sketch`` text
(which Control doesn't carry forward) to score diff_size and scope_drift,
but should not see Control's issue descriptions.

CLI:
    cat generator_out.json | python scripts/strip_context.py --for control
    cat combined.json      | python scripts/strip_context.py --for conservator
"""

from __future__ import annotations

import argparse
import json
import sys

from utils import force_utf8_streams


CANDIDATE_KEEP = ("id", "summary", "sketch")


def strip_for_control(data: dict) -> dict:
    candidates = data.get("candidates") or []
    return {
        "candidates": [
            {k: c[k] for k in CANDIDATE_KEEP if k in c}
            for c in candidates
            if isinstance(c, dict)
        ]
    }


def strip_for_conservator(data: dict) -> dict:
    candidates = {c["id"]: c for c in (data.get("candidates") or []) if isinstance(c, dict)}
    verdicts = data.get("verdicts") or []
    out = []
    for v in verdicts:
        if not v.get("valid"):
            continue
        cid = v["id"]
        if cid not in candidates:
            continue
        c = candidates[cid]
        out.append({k: c[k] for k in CANDIDATE_KEEP if k in c})
    return {"candidates": out}


PROJECTIONS = {
    "control": strip_for_control,
    "conservator": strip_for_conservator,
}


def main(argv: list[str] | None = None) -> int:
    force_utf8_streams()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--for",
        dest="voice",
        choices=sorted(PROJECTIONS),
        required=True,
        help="which downstream voice should receive the stripped output",
    )
    ap.add_argument(
        "--input",
        type=argparse.FileType("r", encoding="utf-8"),
        default=sys.stdin,
        help="JSON input file (default: stdin)",
    )
    args = ap.parse_args(argv)

    data = json.load(args.input)
    result = PROJECTIONS[args.voice](data)
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
