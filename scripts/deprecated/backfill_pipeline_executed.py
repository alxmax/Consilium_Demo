"""One-shot migration: backfill `pipeline_executed` on historical .consilium/runs/.

Added when the field became required in validate_report.py (2026-05-28). The
.consilium/runs/ folder is gitignored, so this script runs locally and brings
each operator's run history up to the new schema.

Heuristic per report:
- chosen_approach in {trivial-direct, prior-deliberation} OR skipped: false
- generator.candidates AND control.verdicts both non-empty: true
- otherwise (ambiguous historical reports): false, with a logged warning

Idempotent: skips reports that already have `pipeline_executed`.

Usage:
    python -X utf8 scripts/deprecated/backfill_pipeline_executed.py [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RUNS_DIR = REPO_ROOT / ".consilium" / "runs"
BYPASS_CHOSEN = {"trivial-direct", "prior-deliberation"}


def classify(report: dict) -> tuple[bool, str]:
    """Return (pipeline_executed, reason_label)."""
    chosen = report.get("chosen_approach")
    if report.get("skipped") is True:
        return False, "skipped"
    if chosen in BYPASS_CHOSEN:
        return False, f"bypass:{chosen}"

    has_gen = False
    has_ctl = False
    for step in report.get("deliberation_log", []) or []:
        if not isinstance(step, dict):
            continue
        s = step.get("step")
        if s == "generator":
            cands = step.get("candidates")
            if isinstance(cands, list) and len(cands) > 0:
                has_gen = True
        elif s == "control":
            verds = step.get("verdicts")
            if isinstance(verds, list) and len(verds) > 0:
                has_ctl = True
    if has_gen and has_ctl:
        return True, "gen+ctl content"
    return False, "ambiguous historical (no gen/ctl content)"


def main() -> int:
    ap = argparse.ArgumentParser(description="Backfill pipeline_executed on .consilium/runs/")
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would change; do not write")
    args = ap.parse_args()

    if not RUNS_DIR.exists():
        print(f"no runs/ dir at {RUNS_DIR}; nothing to do", file=sys.stderr)
        return 0

    runs = sorted(RUNS_DIR.glob("*.json"))
    counts = {"already_has": 0, "true": 0, "false_skipped": 0,
              "false_bypass": 0, "false_ambiguous": 0, "malformed": 0}
    written = 0
    for path in runs:
        try:
            text = path.read_text(encoding="utf-8")
            report = json.loads(text)
        except (OSError, json.JSONDecodeError):
            counts["malformed"] += 1
            continue
        if not isinstance(report, dict):
            counts["malformed"] += 1
            continue
        if "pipeline_executed" in report:
            counts["already_has"] += 1
            continue
        value, reason = classify(report)
        if value:
            counts["true"] += 1
        else:
            if reason == "skipped":
                counts["false_skipped"] += 1
            elif reason.startswith("bypass"):
                counts["false_bypass"] += 1
            else:
                counts["false_ambiguous"] += 1
        if not args.dry_run:
            # Insert pipeline_executed before deliberation_log for readability.
            new_report = {}
            inserted = False
            for k, v in report.items():
                if not inserted and k in ("deliberation_log", "telemetry"):
                    new_report["pipeline_executed"] = value
                    inserted = True
                new_report[k] = v
            if not inserted:
                new_report["pipeline_executed"] = value
            tmp = path.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(new_report, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(path)
            written += 1

    print(f"runs scanned:        {len(runs)}")
    print(f"already had field:   {counts['already_has']}")
    print(f"set true (gen+ctl):  {counts['true']}")
    print(f"set false (skipped): {counts['false_skipped']}")
    print(f"set false (bypass):  {counts['false_bypass']}")
    print(f"set false (ambiguous historical): {counts['false_ambiguous']}")
    print(f"malformed (skipped): {counts['malformed']}")
    print(f"files written:       {written}{' (DRY RUN)' if args.dry_run else ''}")
    if counts["false_ambiguous"] > 0:
        print(f"\nNote: {counts['false_ambiguous']} historical reports were marked false "
              "because they have no Generator+Control content. These are likely pre-build_report.py "
              "hand-assembled reports. Review individually if you want to override.",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
