"""
senate_todo.py — Append senate decisions to TODO.md as action items.

CLI:
    python scripts/senate_todo.py                       # latest bundle → TODO.md
    python scripts/senate_todo.py runs/senate/<f>.json  # specific bundle
    python scripts/senate_todo.py --todo path/to/TODO.md
    python scripts/senate_todo.py --dry-run             # print without writing
"""

import argparse
import json
import os
import sys
from glob import glob
from pathlib import Path

TODO_DEFAULT = Path(__file__).parent.parent / "TODO.md"

MONTHS = ["Ian", "Feb", "Mar", "Apr", "Mai", "Iun",
          "Iul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Mirrors senate_transcript._SKIP_WORDS: labels containing these substrings
# come from the test harness, not real audits, and must not pollute TODO.md.
# Without this filter, every `python scripts/test_senate_synth.py` run appends
# 10+ smoke/fixture entries that then have to be cleaned up by hand (see the
# precedent in PR #68 "fix(todo): cleanup after /consilium audit 2026-05-17").
_SKIP_LABEL_WORDS = ("smoke", "fixture", "collision")


def _is_test_label(label: str) -> bool:
    low = (label or "").lower()
    return any(w in low for w in _SKIP_LABEL_WORDS)


def find_latest_bundle():
    pattern = str(Path(__file__).parent.parent / "runs" / "senate" / "*.json")
    files = [f for f in glob(pattern)
             if not f.endswith("_fixture.json") and "transcripts" not in f]
    if not files:
        return None
    return max(files, key=os.path.getmtime)


def format_date(ts):
    try:
        date_part = ts.split("_")[0]
        y, mo, d = date_part.split("-")
        return f"{int(d)} {MONTHS[int(mo)-1]} {y}"
    except Exception:
        return ts


def build_todo_block(bundle):
    ts       = bundle.get("timestamp", "?")
    label    = bundle.get("label", "?")
    verdict  = bundle.get("verdict", "?")
    votes    = bundle.get("vote_counts", {})
    mod_reqs = bundle.get("modify_requests", [])
    absent   = bundle.get("senators_absent", [])
    proposal = bundle.get("proposal", "")

    date_str = format_date(ts)
    go_c   = votes.get("GO", 0)
    mod_c  = votes.get("MODIFY", 0)
    stop_c = votes.get("STOP", 0)
    votes_str = f"GO {go_c} · MODIFY {mod_c} · STOP {stop_c}"

    lines = []
    lines.append(f"### Hotărârea Senate — {label} · {date_str} · {verdict} ({votes_str})")
    lines.append("")

    # short proposal summary
    prop_short = proposal[:200] + ("…" if len(proposal) > 200 else "")
    lines.append(f"> **Propunere:** {prop_short}")
    if absent:
        lines.append(f"> **Absenți:** {', '.join(absent)}")
    lines.append("")

    if not mod_reqs:
        if verdict == "GO":
            lines.append("_Senatul a aprobat propunerea. Nicio modificare necesară._")
        else:
            lines.append("_Nicio cerere de modificare înregistrată._")
        lines.append("")
        return "\n".join(lines)

    for r in mod_reqs:
        senator = r.get("senator", "?").upper()
        request = r.get("request", "")
        lines.append(f"- [ ] **[{senator}]** {request}")

    lines.append("")
    return "\n".join(lines)


def session_anchor(bundle):
    """Unique string used to detect duplicate entries in TODO.md."""
    ts    = bundle.get("timestamp", "")
    label = bundle.get("label", "")
    return f"Hotărârea Senate — {label} · {format_date(ts)}"


SECTION_HEADER = "## 🏛 Hotărâri Senate\n"


def append_bundle_to_todo(bundle: dict, todo_path: "Path | None" = None) -> bool:
    """Append bundle decisions to TODO.md. Returns True if written, False if skipped
    (either duplicate anchor or test label matching _SKIP_LABEL_WORDS)."""
    if _is_test_label(bundle.get("label", "")):
        return False
    todo_path = Path(todo_path) if todo_path else TODO_DEFAULT
    anchor = session_anchor(bundle)

    existing = todo_path.read_text(encoding="utf-8") if todo_path.exists() else ""
    if anchor in existing:
        return False

    block = build_todo_block(bundle)

    if SECTION_HEADER in existing:
        idx = existing.index(SECTION_HEADER) + len(SECTION_HEADER)
        new_content = existing[:idx] + "\n" + block + existing[idx:]
    else:
        sep = "\n---\n\n" if not existing.endswith("\n---\n") else "\n\n"
        new_content = existing.rstrip("\n") + sep + SECTION_HEADER + "\n" + block

    todo_path.write_text(new_content, encoding="utf-8")
    return True


def main():
    ap = argparse.ArgumentParser(
        description="Append senate decisions to TODO.md.")
    ap.add_argument("bundle", nargs="?",
                    help="Path to senate bundle JSON (default: latest)")
    ap.add_argument("--todo", default=str(TODO_DEFAULT),
                    help="Path to TODO.md (default: TODO.md in repo root)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print the block without writing to file")
    args = ap.parse_args()

    bundle_path = args.bundle or find_latest_bundle()
    if not bundle_path or not os.path.exists(bundle_path):
        print(f"ERROR: bundle not found: {bundle_path}", file=sys.stderr)
        sys.exit(1)

    with open(bundle_path, encoding="utf-8") as f:
        bundle = json.load(f)

    if args.dry_run:
        print(build_todo_block(bundle))
        return

    written = append_bundle_to_todo(bundle, args.todo)
    anchor  = session_anchor(bundle)
    if written:
        print(f"written: {args.todo}  [{anchor}]", file=sys.stderr)
    elif _is_test_label(bundle.get("label", "")):
        print(f"INFO: test label ({bundle.get('label')!r}) — not appended to TODO.md.", file=sys.stderr)
    else:
        print(f"INFO: already in TODO.md ({anchor!r}), skipping.", file=sys.stderr)


if __name__ == "__main__":
    main()
