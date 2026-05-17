"""One-shot migration: FEEDBACK.md -> FEEDBACK.html.

Parses the old Markdown pipe-table, fuzzy-matches each entry to a
runs/*.json file by (date, chosen_approach, token overlap on context),
and renders the new HTML. Backs up the old file as FEEDBACK.md.bak.

Run ONCE per skill instance:
    python scripts/migrate_feedback_md_to_html.py
    python scripts/migrate_feedback_md_to_html.py --md path/FEEDBACK.md --html path/FEEDBACK.html
    python scripts/migrate_feedback_md_to_html.py --force  # overwrite existing HTML
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent  # scripts/deprecated/ -> scripts/ -> repo root

LEGACY_ENTRY_RE = re.compile(
    r"^- (?P<date>\d{4}-\d{2}-\d{2})\s*\|\s*"
    r"(?P<context>[^|]+?)\s*\|\s*"
    r"(?P<chosen>[^|]+?)\s*\|\s*"
    r"(?P<outcome>OK|BAD|OVR|PEND)\s*\|\s*"
    r"(?P<note>.*)$"
)
TOKEN_RE = re.compile(r"[a-zA-Z0-9]{4,}")


def _load_render():
    spec = importlib.util.spec_from_file_location("consilium_render", ROOT / "scripts" / "render_feedback_html.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["consilium_render"] = mod
    spec.loader.exec_module(mod)
    return mod


def parse_legacy_md(path: Path) -> list[dict]:
    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        m = LEGACY_ENTRY_RE.match(line)
        if m:
            entries.append({k: v.strip() for k, v in m.groupdict().items()})
    return entries


def fuzzy_match_run(entry: dict, runs_dir: Path) -> str | None:
    """Return repo-relative path to best-matching run JSON, or None."""
    if not runs_dir.is_dir():
        return None
    candidates: list[tuple[float, Path]] = []
    ctx_tokens = set(t.lower() for t in TOKEN_RE.findall(entry["context"]))
    for f in runs_dir.glob(f"{entry['date']}_*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if data.get("chosen_approach") != entry["chosen"]:
            continue
        sc = (data.get("success_criterion") or "")
        sc_tokens = set(t.lower() for t in TOKEN_RE.findall(sc))
        overlap = len(ctx_tokens & sc_tokens)
        candidates.append((overlap, f))
    if not candidates:
        return None
    candidates.sort(key=lambda x: (-x[0], x[1].name))
    best_path = candidates[0][1]
    return f"runs/{best_path.name}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--md", default=str(ROOT / "FEEDBACK.md"))
    ap.add_argument("--html", default=str(ROOT / "FEEDBACK.html"))
    ap.add_argument("--runs-dir", default=str(ROOT / "runs"))
    ap.add_argument("--force", action="store_true", help="overwrite existing HTML")
    ap.add_argument("--no-backup", action="store_true", help="don't rename .md to .md.bak")
    args = ap.parse_args(argv)

    md_path = Path(args.md)
    html_path = Path(args.html)
    runs_dir = Path(args.runs_dir)

    if not md_path.exists():
        print(f"missing: {md_path}", file=sys.stderr)
        return 1
    if html_path.exists() and not args.force:
        print(f"refusing to overwrite existing {html_path}; pass --force", file=sys.stderr)
        return 1

    legacy = parse_legacy_md(md_path)
    render_mod = _load_render()

    entries = []
    match_log = []
    for row in legacy:
        run_path = fuzzy_match_run(row, runs_dir)
        match_log.append(f"{row['date']} | {row['chosen']} -> {run_path or 'STUB'}")
        entries.append(render_mod.Entry(
            date=row["date"],
            context=row["context"],
            chosen=row["chosen"],
            outcome=row["outcome"],
            note=row["note"],
            run_path=run_path,
        ))

    html_path.write_text(render_mod.render(entries, runs_dir), encoding="utf-8")
    print(f"wrote {html_path} ({len(entries)} entries)")
    for line in match_log:
        print(f"  {line}")

    if not args.no_backup:
        bak = md_path.with_suffix(".md.bak")
        md_path.rename(bak)
        print(f"backed up {md_path.name} -> {bak.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
