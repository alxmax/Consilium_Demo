"""Find ``runs/*.json`` files that have no row in ``FEEDBACK.html`` and offer to backfill.

The auto-log step at end of SKILL.md Step 6 is the only thing that
creates a FEEDBACK row. If it gets skipped — orchestrator crashes,
session ends abruptly, user closes terminal before final pipe — the
run exists on disk but the journal has no record of it. ``priors.py``
already surfaces the gap as ``missing_feedback_runs``; this script
gives you the tool to act on it.

By default the script only **lists** the gap. With ``--backfill`` it
appends a default PEND row for each missing run (using the same
note-derivation as ``log_feedback.py``) so ``priors.py``'s
``stale_pendings`` will surface them at the next Step 0 and the user
can close them with the standard PEND->OK/BAD prompt.

Two safety choices baked in:

- Outcome defaults to PEND. We don't guess OK retroactively just because
  the run looks well-shaped — a missing-feedback run is by definition
  one the user never rated.
- Existing rows are never overwritten. A run is matched (and so skipped)
  if any row has the same date AND same chosen_approach prefix.

CLI:
    python scripts/audit_feedback.py                  # just list
    python scripts/audit_feedback.py --backfill       # append PEND rows
    python scripts/audit_feedback.py --backfill --dry-run
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

from utils import force_utf8_streams


def _load_modules():
    here = Path(__file__).resolve().parent
    priors_spec = importlib.util.spec_from_file_location("consilium_priors", here / "priors.py")
    assert priors_spec and priors_spec.loader
    priors_mod = importlib.util.module_from_spec(priors_spec)
    sys.modules["consilium_priors"] = priors_mod
    priors_spec.loader.exec_module(priors_mod)

    fb_spec = importlib.util.spec_from_file_location("consilium_feedback", here / "feedback.py")
    assert fb_spec and fb_spec.loader
    fb_mod = importlib.util.module_from_spec(fb_spec)
    sys.modules["consilium_feedback"] = fb_mod
    fb_spec.loader.exec_module(fb_mod)

    log_spec = importlib.util.spec_from_file_location("consilium_logfb", here / "log_feedback.py")
    assert log_spec and log_spec.loader
    log_mod = importlib.util.module_from_spec(log_spec)
    sys.modules["consilium_logfb"] = log_mod
    log_spec.loader.exec_module(log_mod)
    return priors_mod, fb_mod, log_mod


def main(argv: list[str] | None = None) -> int:
    force_utf8_streams()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs-dir", default=None, help="path to runs/ (default: ./runs)")
    ap.add_argument("--feedback", default=None, help="path to FEEDBACK.html (default: ./FEEDBACK.html)")
    ap.add_argument("--backfill", action="store_true", help="append PEND rows for each missing run")
    ap.add_argument("--dry-run", action="store_true", help="with --backfill: print plan but don't write")
    args = ap.parse_args(argv)

    priors_mod, fb_mod, log_mod = _load_modules()

    runs_dir = Path(args.runs_dir) if args.runs_dir else Path.cwd() / "runs"
    feedback_path = Path(args.feedback) if args.feedback else Path.cwd() / "FEEDBACK.html"

    entries = fb_mod.parse_feedback(feedback_path)
    missing = priors_mod.find_missing_feedback_runs(runs_dir, entries, cap=999)

    if not missing:
        print("no missing feedback rows — every run is logged.")
        return 0

    print(f"runs without feedback rows: {len(missing)}")
    for m in missing:
        print(f"  {m['run']}  date={m['date']}  chosen={m['chosen']}")

    if not args.backfill:
        print("\nrun with --backfill to append default PEND rows for these runs.")
        return 0

    appended = 0
    for m in missing:
        run_path = runs_dir / m["run"]
        try:
            report = json.loads(run_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            print(f"  skip {m['run']}: {exc}", file=sys.stderr)
            continue
        try:
            entry = log_mod.build_entry(report, outcome="PEND")
        except ValueError as exc:
            print(f"  skip {m['run']}: build_entry failed ({exc})", file=sys.stderr)
            continue
        # Force the entry's date to the run's date (which sits in the filename)
        # so the backfilled row reflects WHEN the deliberation actually happened,
        # not when the audit ran.
        if m.get("date"):
            entry["date"] = m["date"]
        rel = f"runs/{m['run']}"
        if args.dry_run:
            print(f"  [dry-run] would append: {entry['date']} | {entry['context']} | {entry['chosen']} | PEND | {entry['note']}")
        else:
            rc = log_mod.append_entry(feedback_path, entry, rel)
            if rc == 0:
                appended += 1
            else:
                print(f"  skip {m['run']}: duplicate fingerprint, already in FEEDBACK.html", file=sys.stderr)

    if args.dry_run:
        print(f"\ndry-run: {len(missing)} rows would be appended.")
    else:
        print(f"\nbackfilled {appended} PEND row(s) into {feedback_path.name}.")
        print("close them retroactively with: python scripts/mark_outcome.py --run-path runs/<file>.json --outcome OK|BAD")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
