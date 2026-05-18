"""Summarize feedback from FEEDBACK.md and runs/*.json.

Reads the journal at FEEDBACK.md, parses entries, and prints a short stats
report so you can see whether each voice (Generator, Control, Conservator)
is actually pulling its weight in your real-world uses.

CLI:
    python scripts/feedback.py             # stats on everything
    python scripts/feedback.py --recent 10 # last 10 entries only
    python scripts/feedback.py --runs      # also scan runs/*.json
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FEEDBACK = ROOT / "FEEDBACK.html"
RUNS = ROOT / "runs"

OUTCOMES = ("OK", "BAD", "OVR", "PEND", "PEND_HEADLESS")

ROW_RE = re.compile(
    r'<tr class="entry"[^>]*>(?P<body>.*?)</tr>',
    re.DOTALL,
)
CELL_RE = re.compile(r'<td(?P<attrs>[^>]*)>(?P<text>.*?)</td>', re.DOTALL)
FIELD_ATTR_RE = re.compile(r'data-field="([^"]+)"')
TAG_RE = re.compile(r'<[^>]+>')


def _strip_tags(s: str) -> str:
    s = TAG_RE.sub('', s)
    # html.unescape is in the stdlib; avoids extra deps.
    import html as _html
    return _html.unescape(s).strip()


def parse_feedback(path: Path) -> list[dict]:
    entries = []
    if not path.exists():
        return entries
    text = path.read_text(encoding="utf-8")
    for m in ROW_RE.finditer(text):
        cell_matches = list(CELL_RE.finditer(m.group("body")))

        # --- Attribute-based parsing (preferred, order-independent) ---
        # Rows written by render_feedback_html.py carry data-field="<name>"
        # on each <td>. Extract them into a dict keyed by field name.
        field_map: dict[str, str] = {}
        for cm in cell_matches:
            fa = FIELD_ATTR_RE.search(cm.group("attrs"))
            if fa:
                field_map[fa.group(1)] = _strip_tags(cm.group("text"))

        if field_map:
            # data-field rows: require the four mandatory fields.
            date = field_map.get("date", "")
            context = field_map.get("context", "")
            chosen = field_map.get("chosen", "")
            outcome = field_map.get("outcome", "")
            note = field_map.get("note", "")
            vote_pattern = field_map.get("vote_pattern", "")
        else:
            # --- Legacy positional fallback (rows without data-field attrs) ---
            # Trias layout (8 cells): [chev, date, context, chosen, outcome, tokens, note, vote_pattern]
            # Previous layout (7 cells): [chev, date, context, chosen, outcome, tokens, note]
            # Legacy layout (6 cells): [chev, date, context, chosen, outcome, note]
            # The tokens cell is regenerated at render time from run telemetry,
            # so we drop it here — the parser only returns the persistent fields.
            cells = [cm.group("text") for cm in cell_matches]
            if len(cells) == 8:
                date = _strip_tags(cells[1])
                context = _strip_tags(cells[2])
                chosen = _strip_tags(cells[3])
                outcome = _strip_tags(cells[4])
                note = _strip_tags(cells[6])
                vote_pattern = _strip_tags(cells[7])
            elif len(cells) == 7:
                date = _strip_tags(cells[1])
                context = _strip_tags(cells[2])
                chosen = _strip_tags(cells[3])
                outcome = _strip_tags(cells[4])
                note = _strip_tags(cells[6])
                vote_pattern = ""
            elif len(cells) == 6:
                date = _strip_tags(cells[1])
                context = _strip_tags(cells[2])
                chosen = _strip_tags(cells[3])
                outcome = _strip_tags(cells[4])
                note = _strip_tags(cells[5])
                vote_pattern = ""
            else:
                continue

        if outcome not in ("OK", "BAD", "OVR", "PEND", "PEND_HEADLESS"):
            continue
        entries.append({
            "date": date,
            "context": context,
            "chosen": chosen,
            "outcome": outcome,
            "note": note,
            "vote_pattern": vote_pattern,
        })
    return entries


def parse_runs(path: Path) -> list[dict]:
    runs = []
    if not path.exists():
        return runs
    for f in sorted(path.glob("*.json")):
        try:
            runs.append(json.loads(f.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            continue
    return runs


def report(entries: list[dict], runs: list[dict] | None = None) -> str:
    out = []
    out.append(f"Total logged uses: {len(entries)}")
    if not entries:
        out.append("No entries yet. Use the skill on a real change, then append a line to FEEDBACK.md.")
        return "\n".join(out)

    outcomes = Counter(e["outcome"] for e in entries)
    out.append("Outcomes:")
    for k in OUTCOMES:
        out.append(f"  {k}: {outcomes.get(k, 0)}")

    rated = sum(outcomes.get(k, 0) for k in ("OK", "BAD", "OVR"))
    if rated:
        success = outcomes.get("OK", 0) / rated
        out.append(f"Success rate (excluding PEND): {success:.0%}")

    overrides = [e for e in entries if e["outcome"] == "OVR"]
    if overrides:
        out.append(f"Overrides ({len(overrides)}) — recommendation ignored:")
        for e in overrides[-5:]:
            out.append(f"  {e['date']} | {e['context']} | {e['note']}")

    if runs:
        out.append(f"\nDeliberation runs on disk: {len(runs)}")
        schemes = Counter(_run_scheme(r) for r in runs)
        for s, n in schemes.most_common():
            out.append(f"  scheme={s}: {n}")

    return "\n".join(out)


def _run_scheme(run: dict) -> str:
    """Read the aggregation scheme from a run, tolerating both the legacy
    top-level ``aggregation`` shape and the current ``deliberation_log``
    step shape (matches what priors.py:_run_had_veto walks)."""
    agg = run.get("aggregation")
    if isinstance(agg, dict) and agg.get("scheme"):
        return agg["scheme"]
    for step in run.get("deliberation_log") or []:
        if not isinstance(step, dict):
            continue
        if step.get("step") != "aggregate":
            continue
        if step.get("scheme"):
            return step["scheme"]
        result = step.get("result")
        if isinstance(result, dict) and result.get("scheme"):
            return result["scheme"]
    return "?"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--recent", type=int, default=0, help="only consider the N most recent entries")
    ap.add_argument("--runs", action="store_true", help="also scan runs/*.json")
    args = ap.parse_args(argv)

    entries = parse_feedback(FEEDBACK)
    if args.recent:
        entries = entries[-args.recent :]

    runs = parse_runs(RUNS) if args.runs else None
    print(report(entries, runs))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
