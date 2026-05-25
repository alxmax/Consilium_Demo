"""Auto-append an entry to FEEDBACK.html from a deliberation report.

Reads a deliberation report (JSON) from stdin, derives the standard
feedback entry, and appends it to FEEDBACK.html (creating the file if
missing). Removes the friction of asking the user for the entry at end
of Step 6 — the agent calls this directly.

Entry format:
    {date, context, chosen, outcome, note} appended as <tr> to FEEDBACK.html.

Auto-fill rules:
- data    : today's date in ISO format
- context : success_criterion truncated to 60 chars (with `...`)
- chosen  : chosen_approach (or literal "null" / "skipped")
- outcome : controlled by --outcome flag (default PEND). The Step 6
            workflow in SKILL.md drives this: confidence >= 0.7 -> OK,
            confidence < 0.7 + user picks alt -> OVR with --override-target,
            confidence < 0.7 + user says no -> OK, skip / null -> PEND.
- note    : auto-derived from report shape, max 80 chars:
            * skipped report      -> "skipped: <skip_reason>"
            * all-vetoed (chosen=null) -> "all vetoed; relaxed=<X>"
            * normal              -> "<N> cand, <K> vetoed, conf=<X>, mode=<Y>"
            When --outcome=OVR and --override-target is set, "; override=<id>"
            is appended. When --user-note is non-empty, it is appended too.

Pipe ``|`` and newlines inside text fields are stripped/replaced so the
appended entry stays parseable.

Exits 1 if the report lacks success_criterion or chosen_approach (run
validate_report.py first to catch shape issues earlier). Exits 2 on
malformed JSON. Otherwise exits 0 and prints the appended entry summary to stdout.

CLI:
    cat runs/<file>.json | python scripts/log_feedback.py
    cat runs/<file>.json | python scripts/log_feedback.py --outcome OK
    cat runs/<file>.json | python scripts/log_feedback.py --outcome OVR \\
        --override-target alt_b --user-note "preferred safer rollback"
    python scripts/log_feedback.py --feedback path/to/FEEDBACK.html < report.json
    python scripts/log_feedback.py --dry-run < report.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date, datetime
from pathlib import Path

from utils import atomic_write_text, force_utf8_streams, load_json_stdin


CONTEXT_MAX = 60
NOTE_MAX = 80
HEADER_LINES = ()  # legacy MD header no longer used
RUN_PATH_MAP = ".run_path_map.json"


def _fingerprint(date_str: str, chosen: str, context: str, run_id: str | None = None) -> str:
    """16-char hex fingerprint for a feedback entry (used as sidecar map key).

    ``run_id`` is the basename of the run JSON file (e.g. ``2026-05-17_foo.json``).
    When provided it makes the fingerprint unique per run, preventing collisions
    between same-day entries with the same chosen+context prefix.  When absent
    (e.g. when recomputing fingerprints for rows already in FEEDBACK.html that
    were written without a run_id), we fall back to a microsecond-precision
    timestamp component so that two distinct logging calls on the same day
    cannot silently collide on the old 30-char context truncation.
    """
    disambiguator = run_id if run_id else datetime.now().strftime("%f")
    raw = f"{date_str}|{chosen}|{context}|{disambiguator}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _load_map(runs_dir: Path) -> dict[str, str]:
    map_path = runs_dir / RUN_PATH_MAP
    if not map_path.exists():
        return {}
    try:
        return json.loads(map_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_map(runs_dir: Path, run_map: dict[str, str]) -> None:
    runs_dir.mkdir(parents=True, exist_ok=True)
    atomic_write_text(
        runs_dir / RUN_PATH_MAP,
        json.dumps(run_map, indent=2, ensure_ascii=False),
    )


def _clean(text: str) -> str:
    return text.replace("|", "/").replace("\n", " ").replace("\r", " ").strip()


def truncate(text: str, n: int) -> str:
    text = _clean(text or "")
    if len(text) <= n:
        return text
    # leave room for the ellipsis
    return text[: max(0, n - 1)].rstrip() + "…"


def derive_note(report: dict) -> str:
    if report.get("skipped") is True:
        return truncate(f"skipped: {report.get('skip_reason', '')}", NOTE_MAX)

    log = report.get("deliberation_log") or []
    aggregate_step = next((s for s in log if isinstance(s, dict) and s.get("step") == "aggregate"), {})
    raw_result = aggregate_step.get("result")
    # Manual-assembled runs may put a narrative string in `result` instead of
    # the canonical aggregate dict; coerce to {} so note derivation keeps going.
    aggregate_result = raw_result if isinstance(raw_result, dict) else {}

    chosen = report.get("chosen_approach")
    if chosen is None:
        relaxed = (aggregate_result.get("retry_suggested") or {}).get("relaxed_threshold")
        relaxed_s = f"{relaxed:.2f}" if isinstance(relaxed, (int, float)) else "?"
        return truncate(f"all vetoed; relaxed={relaxed_s}", NOTE_MAX)

    generator_step = next((s for s in log if isinstance(s, dict) and s.get("step") == "generator"), {})
    n_cand = len(generator_step.get("candidates") or [])
    n_vetoed = len(aggregate_result.get("vetoed") or [])
    conf = report.get("confidence")
    conf_s = f"{conf:.2f}" if isinstance(conf, (int, float)) else "?"
    mode = (report.get("telemetry") or {}).get("mode", "?")
    return truncate(
        f"{n_cand} cand, {n_vetoed} vetoed, conf={conf_s}, mode={mode}",
        NOTE_MAX,
    )


def build_entry(
    report: dict,
    outcome: str = "PEND",
    override_target: str | None = None,
    user_note: str | None = None,
) -> dict:
    sc = report.get("success_criterion")
    if not isinstance(sc, str) or not sc.strip():
        raise ValueError("report missing non-empty success_criterion")

    if "chosen_approach" not in report:
        raise ValueError("report missing chosen_approach")
    chosen = report["chosen_approach"]
    if chosen is None:
        chosen_s = "null"
    elif isinstance(chosen, str) and chosen.strip():
        chosen_s = _clean(chosen)
    else:
        raise ValueError("chosen_approach must be null or a non-empty string")

    if outcome == "OVR" and not override_target:
        raise ValueError("--outcome OVR requires --override-target <alt_id>")

    auto_note = derive_note(report)
    extras: list[str] = []
    if outcome == "OVR" and override_target:
        extras.append(f"override={_clean(override_target)}")
    if user_note and user_note.strip():
        extras.append(_clean(user_note))
    note = "; ".join([auto_note] + extras) if extras else auto_note

    return {
        "date": date.today().isoformat(),
        "context": truncate(sc, CONTEXT_MAX),
        "chosen": chosen_s,
        "outcome": outcome,
        "note": note,
        "vote_pattern": _clean(report.get("vote_pattern") or ""),
    }


def append_entry(feedback_path: Path, entry: dict, run_path: str | None) -> int:
    """Round-trip the HTML: parse existing rows, append, re-render.

    Returns:
        0  — new row written successfully.
        3  — duplicate fingerprint detected; row skipped (caller should exit 3
             so the caller can distinguish "duplicate" from "success").

    Callers can use the return value to track how many real appends happened —
    important for audit_feedback's --backfill summary.
    """
    import importlib.util
    here = Path(__file__).resolve().parent
    import sys as _sys

    feedback_spec = importlib.util.spec_from_file_location("consilium_feedback", here / "feedback.py")
    assert feedback_spec and feedback_spec.loader
    feedback_mod = importlib.util.module_from_spec(feedback_spec)
    _sys.modules["consilium_feedback"] = feedback_mod
    feedback_spec.loader.exec_module(feedback_mod)

    render_spec = importlib.util.spec_from_file_location("consilium_render", here / "render_feedback_html.py")
    assert render_spec and render_spec.loader
    render_mod = importlib.util.module_from_spec(render_spec)
    _sys.modules["consilium_render"] = render_mod
    render_spec.loader.exec_module(render_mod)

    existing = feedback_mod.parse_feedback(feedback_path)
    runs_dir = feedback_path.parent / "runs"
    run_map = _load_map(runs_dir)

    # Idempotent on re-run: if run_path is provided, check whether it is already
    # a value in the sidecar map — that is the most reliable duplicate signal
    # because the fingerprint key is stable only when the same run_id is used.
    # For entries logged without a run_path, fall back to a content hash over
    # the full context string (no truncation, no timestamp component).
    run_id = Path(run_path).name if run_path else None
    new_fp = _fingerprint(entry["date"], entry["chosen"], entry["context"], run_id=run_id)
    is_duplicate = False
    if run_path and run_path in run_map.values():
        is_duplicate = True
    elif not run_path:
        # Stable content-only hash: same date+chosen+full-context means same entry.
        stable_fp = hashlib.sha256(
            f"{entry['date']}|{entry['chosen']}|{entry['context']}".encode()
        ).hexdigest()[:16]
        stable_existing = {
            hashlib.sha256(
                f"{row['date']}|{row['chosen']}|{row['context']}".encode()
            ).hexdigest()[:16]
            for row in existing
        }
        if stable_fp in stable_existing:
            is_duplicate = True
    if is_duplicate:
        print(
            f"log_feedback: duplicate entry (fp {new_fp[:8]}) — already in FEEDBACK.html, skipping append.",
            file=sys.stderr,
        )
        # Still refresh the sidecar map for the new run_path even when the row
        # itself is a duplicate (a later mark_outcome may want to drill into the
        # newer run JSON for the same logical decision).
        if run_path:
            run_map[new_fp] = run_path
            _save_map(runs_dir, run_map)
        return 3

    # Restore run_path for existing rows from sidecar map so drill-down survives
    # re-renders. For each existing row, try to reconstruct its fingerprint using
    # the run_id extracted from each known run_path in the sidecar — when a match
    # is found the row's run_path is recovered.  Rows originally logged without a
    # run_id used an unstable timestamp and cannot be matched; they fall back to
    # run_path=None (same as legacy behaviour).
    def _row_run_path(row: dict) -> str | None:
        for fp, rp in run_map.items():
            run_id_candidate = Path(rp).name if rp else None
            fp_candidate = _fingerprint(row["date"], row["chosen"], row["context"], run_id=run_id_candidate)
            if fp_candidate == fp:
                return rp
        return None

    entries = [
        render_mod.Entry(
            **row,
            run_path=_row_run_path(row),
        )
        for row in existing
    ]
    new_entry = render_mod.Entry(
        date=entry["date"],
        context=entry["context"],
        chosen=entry["chosen"],
        outcome=entry["outcome"],
        note=entry["note"],
        run_path=run_path,
        vote_pattern=entry.get("vote_pattern", ""),
    )
    entries.append(new_entry)

    # Persist run_path for the new entry so future re-renders can recover it.
    if run_path:
        run_map[new_fp] = run_path
        _save_map(runs_dir, run_map)

    atomic_write_text(feedback_path, render_mod.render(entries, runs_dir))
    return 0


def main(argv: list[str] | None = None) -> int:
    force_utf8_streams()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--feedback", default=None, help="path to FEEDBACK.html (default: ./FEEDBACK.html)")
    ap.add_argument("--dry-run", action="store_true", help="print summary, don't write file")
    ap.add_argument(
        "--outcome",
        choices=("OK", "BAD", "OVR", "PEND", "PEND_HEADLESS"),
        default="PEND",
        help="outcome to record (default: PEND; set OK/OVR after confidence-gated user prompt; use PEND_HEADLESS in headless/CI context to avoid polluting pend_pressure)",
    )
    ap.add_argument("--override-target", default=None, help="alt_id when --outcome=OVR")
    ap.add_argument("--user-note", default=None, help="optional user-supplied note appended to auto-note")
    ap.add_argument("--run-path", default=None, help="relative path to runs/*.json for drill-down (e.g. runs/2026-05-12_foo.json)")
    ap.add_argument("--force-override", action="store_true",
        help="allow --outcome OK even when confidence < 0.70 (use when user has confirmed the pick despite low confidence)")
    args = ap.parse_args(argv)

    if args.outcome == "OVR" and not args.override_target:
        print("log_feedback: --outcome OVR requires --override-target <alt_id>", file=sys.stderr)
        sys.exit(2)

    report = load_json_stdin("log_feedback.py")
    if not isinstance(report, dict):
        print("log_feedback.py: report must be a JSON object", file=sys.stderr)
        return 2

    if args.outcome == "OK":
        conf = report.get("confidence")
        below = conf is None or (isinstance(conf, (int, float)) and conf < 0.7)
        if below and not args.force_override:
            conf_s = f"{conf:.2f}" if isinstance(conf, (int, float)) else str(conf)
            print(
                f"confidence {conf_s} is below threshold 0.70 — "
                "pass --force-override to log OK despite low confidence",
                file=sys.stderr,
            )
            return 1

    try:
        entry = build_entry(
            report,
            outcome=args.outcome,
            override_target=args.override_target,
            user_note=args.user_note,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if not args.dry_run:
        feedback_path = Path(args.feedback) if args.feedback else Path.cwd() / "FEEDBACK.html"
        rc = append_entry(feedback_path, entry, args.run_path)
        if rc != 0:
            # Exit 3 means duplicate detected — propagate so callers can distinguish
            # "duplicate skipped" from "success".
            print(f"{entry['date']} | {entry['context']} | {entry['chosen']} | {entry['outcome']} | {entry['note']}")
            return rc

    print(f"{entry['date']} | {entry['context']} | {entry['chosen']} | {entry['outcome']} | {entry['note']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
