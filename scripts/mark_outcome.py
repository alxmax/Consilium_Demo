"""Retroactively mark a deliberation outcome based on what happened in reality.

Closes the loop opened by ``log_feedback.py``. The initial outcome that
gets logged at end of Step 6 is *subjective* — it reflects the user's
gut feeling immediately after the deliberation. Production reality may
flip it days later: a chosen approach that looked fine can cause a bug
in prod (=> BAD), or an override that felt risky can turn out to have
been the right call (=> OK).

This script updates an existing FEEDBACK.html row in place:

- Outcome cell is replaced (e.g. PEND -> BAD, OK -> BAD).
- Note is annotated with ``[confirmed]`` so ``priors.py`` can weight
  outcome-confirmed rows higher than subjective ones (signals quality).
- An optional ``--reason`` is appended to the note for future audits.

Row matching strategy (tried in order):

1. ``--run-path runs/<file>.json`` — looks up the entry via the sidecar
   ``runs/.run_path_map.json`` populated by ``log_feedback.py``.
2. ``--date YYYY-MM-DD --chosen <id>`` — direct match against the row.
3. If neither match: exits 1 with the list of candidate rows from the
   most recent N entries so the caller can pick the right one.

If --run-path matches multiple feedback rows (a run logged twice), all
matched rows are updated (rare but possible after a re-render).

CLI:
    python scripts/mark_outcome.py --run-path runs/2026-05-12_foo.json --outcome BAD --reason "broke prod migration"
    python scripts/mark_outcome.py --date 2026-05-12 --chosen approach_a --outcome OK
    python scripts/mark_outcome.py --run-path runs/2026-05-12_foo.json --outcome BAD --dry-run
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

from utils import atomic_write_text, force_utf8_streams


CONFIRMED_MARKER = "[confirmed]"
RUN_PATH_MAP = ".run_path_map.json"


def _fingerprint(date_str: str, chosen: str, context: str) -> str:
    raw = f"{date_str}|{chosen}|{context[:30]}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _load_modules():
    here = Path(__file__).resolve().parent
    fb_spec = importlib.util.spec_from_file_location("consilium_feedback", here / "feedback.py")
    assert fb_spec and fb_spec.loader
    fb_mod = importlib.util.module_from_spec(fb_spec)
    sys.modules["consilium_feedback"] = fb_mod
    fb_spec.loader.exec_module(fb_mod)

    render_spec = importlib.util.spec_from_file_location("consilium_render", here / "render_feedback_html.py")
    assert render_spec and render_spec.loader
    render_mod = importlib.util.module_from_spec(render_spec)
    sys.modules["consilium_render"] = render_mod
    render_spec.loader.exec_module(render_mod)
    return fb_mod, render_mod


def _load_run_map(runs_dir: Path) -> dict[str, str]:
    map_path = runs_dir / RUN_PATH_MAP
    if not map_path.exists():
        return {}
    try:
        return json.loads(map_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _annotate_note(note: str, reason: str | None) -> str:
    parts = [p.strip() for p in note.split(";") if p.strip()]
    if CONFIRMED_MARKER not in parts:
        parts.append(CONFIRMED_MARKER)
    if reason:
        clean = reason.replace("|", "/").replace("\n", " ").strip()
        if clean:
            parts.append(f"outcome_reason={clean}")
    return "; ".join(parts)


def main(argv: list[str] | None = None) -> int:
    force_utf8_streams()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--feedback", default=None, help="path to FEEDBACK.html (default: ./FEEDBACK.html)")
    ap.add_argument("--run-path", default=None, help="match the row whose sidecar maps to this run path")
    ap.add_argument("--date", default=None, help="match by date (with --chosen)")
    ap.add_argument("--chosen", default=None, help="match by chosen id (with --date)")
    ap.add_argument(
        "--outcome",
        choices=("OK", "BAD", "OVR", "PEND"),
        required=True,
        help="new outcome value (BAD usually — production confirmed regression)",
    )
    ap.add_argument("--reason", default=None, help="short string appended to note as outcome_reason=...")
    ap.add_argument("--dry-run", action="store_true", help="print matched rows; don't write")
    args = ap.parse_args(argv)

    if not args.run_path and not (args.date and args.chosen):
        print("mark_outcome: provide --run-path OR (--date AND --chosen)", file=sys.stderr)
        return 1

    fb_mod, render_mod = _load_modules()

    feedback_path = Path(args.feedback) if args.feedback else Path.cwd() / "FEEDBACK.html"
    if not feedback_path.exists():
        print(f"mark_outcome: feedback file missing: {feedback_path}", file=sys.stderr)
        return 1
    runs_dir = feedback_path.parent / "runs"

    existing = fb_mod.parse_feedback(feedback_path)
    run_map = _load_run_map(runs_dir)
    # Reverse map: fingerprint -> run_path for forward lookup
    fp_to_run = {fp: rp for fp, rp in run_map.items()}

    # Build entries with run_path attached
    entries = [
        render_mod.Entry(
            **row,
            run_path=fp_to_run.get(_fingerprint(row["date"], row["chosen"], row["context"])),
        )
        for row in existing
    ]

    # Identify candidates
    matched_idx: list[int] = []
    if args.run_path:
        # Normalize: caller may pass absolute or repo-relative path
        wanted = Path(args.run_path).as_posix()
        wanted_name = Path(args.run_path).name
        for i, e in enumerate(entries):
            if not e.run_path:
                continue
            if Path(e.run_path).as_posix() == wanted or Path(e.run_path).name == wanted_name:
                matched_idx.append(i)
    else:
        for i, e in enumerate(entries):
            if e.date == args.date and e.chosen == args.chosen:
                matched_idx.append(i)

    if not matched_idx:
        print(f"mark_outcome: no row matched", file=sys.stderr)
        print(f"  query: run_path={args.run_path!r} date={args.date!r} chosen={args.chosen!r}", file=sys.stderr)
        print(f"  last 5 rows for reference:", file=sys.stderr)
        for e in entries[-5:]:
            print(f"    {e.date} | {e.chosen} | {e.outcome} | run_path={e.run_path}", file=sys.stderr)
        return 1

    # Update outcome + annotate note
    for i in matched_idx:
        e = entries[i]
        old_outcome = e.outcome
        e.outcome = args.outcome
        e.note = _annotate_note(e.note, args.reason)
        print(f"matched [{i}]: {e.date} | {e.chosen} | {old_outcome} -> {args.outcome}")

    if args.dry_run:
        print("(dry-run; no write)")
        return 0

    atomic_write_text(feedback_path, render_mod.render(entries, runs_dir))
    print(f"updated {len(matched_idx)} row(s) in {feedback_path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
