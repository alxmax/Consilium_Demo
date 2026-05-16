"""Synthesize a Senate deliberation into a verdict bundle.

Orchestration note: this script is NOT a dispatcher. The 7 senators are
dispatched as parallel sub-agents by the Claude orchestrator when
`/consilium senate <proposal>` is invoked (see SKILL.md "Senate mode").
This script consumes the 7 JSON outputs and produces one bundle:

  - vote tally + verdict (GO / MODIFY / STOP / UNREACHABLE)
  - flat list of modify_requests
  - structured per-senator outputs (kept verbatim for consumer-side views)
  - warnings (only structural anomalies; absent senators surface via
    senators_absent rather than warning duplication)

Input format on stdin (JSON):
    {
      "proposal": "<the proposal text being audited>",   # non-empty
      "label":    "<short filename label, e.g. 'self-validation'>",
      "senators": {"wittgenstein": {...}, ...},
      "absent":   ["<senator_name>", ...]                 # optional
    }

Verdict rule:
    UNREACHABLE if voters_present < 5 (matemathically cannot reach quorum)
    GO          if GO     >= 5 of 7
    STOP        if STOP   >= 5 of 7
    MODIFY      otherwise (default — also covers all non-quorum cases)

CLI:
    cat senate_input.json | python -X utf8 scripts/senate_synth.py

Output: writes runs/senate/<YYYY-MM-DD_HHMMSS>-<label>.json (collision-safe
via second-level granularity + numeric suffix if needed) and prints the
bundle to stdout.

Fixture (Socrate falsification request): see `scripts/senate_synth_fixture.json`
for a known-input -> known-verdict pair used in smoke tests.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

from utils import force_utf8_streams, load_json_stdin, validate_keys

SENATORS = (
    "wittgenstein",
    "aurelius",
    "confucius",
    "socrate",
    "musk",
    "dimon",
    "napoleon",
)
QUORUM = 5  # >= 5 of 7 needed for GO or STOP verdict
VOTES = ("GO", "MODIFY", "STOP")

# Per-senator structural expectations: if a senator votes but omits its
# signature structured field, the audit is silent on that axis. We surface a
# warning rather than fail — orchestrator decides whether to retry or accept.
SENATOR_REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
    "wittgenstein": ("vague_terms_found",),
    "aurelius":     ("reversibility", "magnitude"),
    "confucius":    ("hierarchy_check",),
    "socrate":      ("hidden_assumptions",),
    "musk":         ("components_attacked",),
    "dimon":        ("stress_scenarios",),
    "napoleon":     ("cost_estimate",),
}


def normalize_vote(raw) -> str | None:
    """Map a senator's vote string to GO/MODIFY/STOP, or None if unrecognized.

    Returns None on missing/unrecognized — caller surfaces this as a warning
    AND counts it as MODIFY in the tally (most-conservative non-blocking).
    """
    if not isinstance(raw, str):
        return None
    upper = raw.strip().upper()
    return upper if upper in VOTES else None


def tally(senator_outputs: dict[str, dict]) -> dict[str, int]:
    counts = {v: 0 for v in VOTES}
    for output in senator_outputs.values():
        vote = normalize_vote(output.get("vote"))
        counts[vote if vote is not None else "MODIFY"] += 1
    return counts


def compute_verdict(counts: dict[str, int], voters_present: int) -> str:
    if voters_present < QUORUM:
        return "UNREACHABLE"
    if counts["GO"] >= QUORUM:
        return "GO"
    if counts["STOP"] >= QUORUM:
        return "STOP"
    return "MODIFY"


def collect_modify_requests(senator_outputs: dict[str, dict]) -> list[dict]:
    requests = []
    for name, output in senator_outputs.items():
        req = output.get("modify_request")
        if isinstance(req, str) and req.strip():
            requests.append({"senator": name, "request": req.strip()})
    return requests


def collect_warnings(senator_outputs: dict[str, dict], voters_present: int) -> list[str]:
    """Surface only structural anomalies. Absent senators are recorded in
    `senators_absent`, so they do not generate redundant warnings here.
    """
    warnings = []
    for name in SENATORS:
        if name not in senator_outputs:
            continue
        output = senator_outputs[name]
        raw_vote = output.get("vote")
        if normalize_vote(raw_vote) is None:
            warnings.append(
                f"senator '{name}' emitted unrecognized vote {raw_vote!r} (counted as MODIFY)"
            )
        for field in SENATOR_REQUIRED_FIELDS.get(name, ()):
            value = output.get(field)
            if value is None or (isinstance(value, (list, dict)) and len(value) == 0):
                warnings.append(
                    f"senator '{name}' voted but omitted/empty '{field}' — that axis of audit is silent"
                )
    if voters_present < QUORUM:
        warnings.append(
            f"quorum_unreachable: only {voters_present} of {len(SENATORS)} senators voted "
            f"(need >= {QUORUM} to reach GO or STOP); verdict structurally biased toward MODIFY"
        )
    return warnings


def slugify(label: str) -> str:
    s = re.sub(r"[^A-Za-z0-9_-]+", "-", label.strip())
    s = re.sub(r"-+", "-", s).strip("-")
    return s.lower() or "senate"


def build_bundle(
    proposal: str,
    senator_outputs: dict[str, dict],
    absent: list[str],
    label: str,
    timestamp: str,
) -> dict:
    counts = tally(senator_outputs)
    voters_present = len(senator_outputs)
    senators_absent = sorted({n for n in SENATORS if n not in senator_outputs} | set(absent))
    return {
        "timestamp": timestamp,
        "label": label,
        "proposal": proposal,
        "senators_absent": senators_absent,
        "outputs": {n: senator_outputs[n] for n in SENATORS if n in senator_outputs},
        "vote_counts": counts,
        "verdict": compute_verdict(counts, voters_present),
        "modify_requests": collect_modify_requests(senator_outputs),
        "warnings": collect_warnings(senator_outputs, voters_present),
    }


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def write_bundle(bundle: dict) -> Path:
    """Write bundle to runs/senate/, avoiding silent overwrite.

    Filename: <timestamp>-<slug(label)>.json with second-level granularity.
    On collision (same timestamp + label), suffix `_v2`, `_v3`, ... is added.
    """
    out_dir = repo_root() / "runs" / "senate"
    out_dir.mkdir(parents=True, exist_ok=True)
    base = f"{bundle['timestamp']}-{slugify(bundle['label'])}"
    out_path = out_dir / f"{base}.json"
    n = 2
    while out_path.exists():
        out_path = out_dir / f"{base}_v{n}.json"
        n += 1
    out_path.write_text(json.dumps(bundle, indent=2, ensure_ascii=False), encoding="utf-8")
    return out_path


def parse_args() -> argparse.Namespace:
    return argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    ).parse_args()


def main() -> int:
    force_utf8_streams()
    parse_args()
    data = load_json_stdin("senate_synth.py")
    validate_keys(data, ["proposal", "senators"], "senate_synth input")

    proposal = str(data["proposal"]).strip()
    if not proposal:
        print("senate_synth: 'proposal' must be a non-empty string", file=sys.stderr)
        return 1

    senator_outputs = data["senators"]
    if not isinstance(senator_outputs, dict):
        print("senate_synth: 'senators' must be an object keyed by senator name", file=sys.stderr)
        return 1

    absent = data.get("absent", [])
    if not isinstance(absent, list):
        absent = []

    label = data.get("label") or "senate"
    timestamp = dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")

    bundle = build_bundle(proposal, senator_outputs, absent, label, timestamp)

    print(json.dumps(bundle, indent=2, ensure_ascii=False))
    out_path = write_bundle(bundle)
    print(f"\nwritten: {out_path.relative_to(repo_root())}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
