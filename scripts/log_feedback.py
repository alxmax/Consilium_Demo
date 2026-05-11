"""Auto-append a one-line entry to FEEDBACK.md from a deliberation report.

Reads a deliberation report (JSON) from stdin, derives the standard
feedback line, and appends it to FEEDBACK.md (creating the file with a
header if missing). Removes the friction of asking the user for the line
at end of Step 6 — the agent calls this directly.

Line format (unchanged from the manual convention):
    - YYYY-MM-DD | <context> | <chosen> | PEND | <note>

The leading `- ` is the markdown bullet that ENTRY_RE in feedback.py
expects (and that priors.py inherits via parse_feedback). Skipping it
makes auto-written entries invisible to the priors loop — so don't.

Auto-fill rules:
- data    : today's date in ISO format
- context : success_criterion truncated to 60 chars (with `...`)
- chosen  : chosen_approach (or literal "null" / "skipped")
- outcome : always PEND. The user updates PEND -> OK / BAD / OVR later
            by editing FEEDBACK.md directly when the outcome is known.
- note    : derived from report shape, max 80 chars:
            * skipped report      -> "skipped: <skip_reason>"
            * all-vetoed (chosen=null) -> "all vetoed; relaxed=<X>"
            * normal              -> "<N> cand, <K> vetoed, conf=<X>, mode=<Y>"

Pipe ``|`` and newlines inside text fields are stripped/replaced so the
appended line stays parseable.

Exits 1 if the report lacks success_criterion or chosen_approach (run
validate_report.py first to catch shape issues earlier). Exits 2 on
malformed JSON. Otherwise exits 0 and prints the appended line to stdout.

CLI:
    cat runs/<file>.json | python scripts/log_feedback.py
    python scripts/log_feedback.py --feedback path/to/FEEDBACK.md < report.json
    python scripts/log_feedback.py --dry-run < report.json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path


CONTEXT_MAX = 60
NOTE_MAX = 80
HEADER_LINES = (
    "# FEEDBACK\n",
    "#\n",
    "# data | context | chosen | outcome | note\n",
    "# outcome: OK | BAD | OVR (override) | PEND (pending)\n",
    "\n",
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
    aggregate_result = aggregate_step.get("result") or {}

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


def build_line(report: dict) -> str:
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

    today = date.today().isoformat()
    return f"- {today} | {truncate(sc, CONTEXT_MAX)} | {chosen_s} | PEND | {derive_note(report)}"


def append_line(feedback_path: Path, line: str) -> None:
    is_new = not feedback_path.exists()
    with open(feedback_path, "a", encoding="utf-8", newline="\n") as f:
        if is_new:
            f.writelines(HEADER_LINES)
        f.write(line + "\n")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--feedback", default=None, help="path to FEEDBACK.md (default: ./FEEDBACK.md)")
    ap.add_argument("--dry-run", action="store_true", help="print line to stdout, don't write file")
    args = ap.parse_args(argv)

    try:
        report = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"invalid JSON: {exc}", file=sys.stderr)
        return 2
    if not isinstance(report, dict):
        print("report must be a JSON object", file=sys.stderr)
        return 2

    try:
        line = build_line(report)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if not args.dry_run:
        feedback_path = Path(args.feedback) if args.feedback else Path.cwd() / "FEEDBACK.md"
        append_line(feedback_path, line)

    print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
