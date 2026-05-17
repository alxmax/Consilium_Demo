"""Generate aggregate HTML dashboard of all Senate decisions from runs/senate/.

Walks runs/senate/*.json (skipping inputs `_*.json` and the transcripts/ subdir),
sorts by timestamp descending, and emits a self-contained HTML page with one
row per Senate run: timestamp, label, verdict, GO/MODIFY/STOP tally, top
modify_request summary, and a link to the per-run transcript when present.

Stdlib-only. No write coupling — runs on-demand, no pipeline hook.

CLI:
    python scripts/senate_history.py                       # writes senate-history.html
    python scripts/senate_history.py --stdout              # emits HTML to stdout
    python scripts/senate_history.py --output path/to.html # custom output path
    python scripts/senate_history.py --runs runs/senate    # custom runs dir
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import sys
from pathlib import Path


VERDICT_BADGE_CLASS = {
    "GO": "verdict-go",
    "MODIFY": "verdict-modify",
    "STOP": "verdict-stop",
    "DEEPLY_SPLIT": "verdict-split",
    "UNREACHABLE": "verdict-unreachable",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_bundles(senate_dir: Path) -> list[dict]:
    bundles: list[dict] = []
    for path in sorted(senate_dir.glob("*.json")):
        # Skip orchestrator input scratchpads — they aren't bundle outputs.
        if path.name.startswith("_"):
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"skip {path.name}: {exc}", file=sys.stderr)
            continue
        if not isinstance(data, dict):
            continue
        # Recognize bundle by required keys; tolerate legacy schemas missing newer
        # ones, but reject totally unrelated files dropped in the folder.
        if "verdict" not in data or "label" not in data:
            continue
        data["_source_path"] = path
        bundles.append(data)
    bundles.sort(key=lambda b: b.get("timestamp", ""), reverse=True)
    return bundles


def find_transcript(bundle: dict, senate_dir: Path) -> Path | None:
    """Best-effort transcript lookup matching senate_transcript naming."""
    ts = bundle.get("timestamp", "")
    if "_" not in ts:
        return None
    date_part = ts.split("_", 1)[0]
    base = bundle["_source_path"].stem  # e.g. 2026-05-17_173453-plugin-codecycle-history-bundle-r2
    candidate = senate_dir / "transcripts" / date_part / f"{base.split('-', 3)[-1]}.html"
    if candidate.exists():
        return candidate
    # Some transcripts include the time suffix when collision-avoided.
    return None


def humanize_timestamp(ts: str) -> str:
    """Convert YYYY-MM-DD_HHMMSS into a readable form, leaving raw if malformed."""
    try:
        parsed = dt.datetime.strptime(ts, "%Y-%m-%d_%H%M%S")
    except ValueError:
        try:
            parsed = dt.datetime.strptime(ts, "%Y-%m-%d_%H%M")
        except ValueError:
            return ts
    return parsed.strftime("%Y-%m-%d %H:%M:%S")


def top_modify_summary(bundle: dict, max_chars: int = 220) -> str:
    requests = bundle.get("modify_requests") or []
    if not requests:
        return ""
    first = requests[0]
    senator = first.get("senator", "?")
    text = (first.get("request") or "").strip()
    if len(text) > max_chars:
        text = text[: max_chars - 1].rstrip() + "…"
    rest = len(requests) - 1
    suffix = f" (+{rest} more)" if rest > 0 else ""
    return f"<strong>{html.escape(senator)}:</strong> {html.escape(text)}{html.escape(suffix)}"


def render_row(bundle: dict, senate_dir: Path) -> str:
    ts = humanize_timestamp(bundle.get("timestamp", ""))
    label = bundle.get("label", "")
    verdict = bundle.get("verdict", "?")
    badge = VERDICT_BADGE_CLASS.get(verdict, "verdict-unknown")
    counts = bundle.get("vote_counts") or {}
    counts_pre = bundle.get("vote_counts_pre_blocaj")

    def fmt_counts(c: dict) -> str:
        order = ("GO", "MODIFY", "STOP")
        parts = [f"{k} {c.get(k, 0)}" for k in order if k in c or c.get(k, 0)]
        # Include any non-standard verdict tallies (DEEPLY_SPLIT, UNREACHABLE)
        for k, v in c.items():
            if k not in order and v:
                parts.append(f"{html.escape(k)} {v}")
        return " · ".join(parts)

    counts_html = html.escape(fmt_counts(counts))
    if counts_pre:
        counts_html += (
            f"<br><span class='counts-pre'>pre-blocaj: "
            f"{html.escape(fmt_counts(counts_pre))}</span>"
        )

    transcript = find_transcript(bundle, senate_dir)
    if transcript is not None:
        try:
            href = transcript.relative_to(repo_root()).as_posix()
        except ValueError:
            href = transcript.as_posix()
        transcript_html = f'<a href="{html.escape(href)}">transcript</a>'
    else:
        transcript_html = "—"

    try:
        bundle_href = bundle["_source_path"].relative_to(repo_root()).as_posix()
    except ValueError:
        bundle_href = bundle["_source_path"].as_posix()

    summary = top_modify_summary(bundle)

    return (
        "<tr>"
        f"<td class='ts'>{html.escape(ts)}</td>"
        f"<td class='label'><a href='{html.escape(bundle_href)}'>{html.escape(label)}</a></td>"
        f"<td><span class='badge {badge}'>{html.escape(verdict)}</span></td>"
        f"<td class='counts'>{counts_html}</td>"
        f"<td class='summary'>{summary}</td>"
        f"<td class='transcript'>{transcript_html}</td>"
        "</tr>"
    )


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ro">
<head>
<meta charset="utf-8">
<title>Consilium · Senate History</title>
<style>
  :root {{ color-scheme: light dark; }}
  body {{
    font-family: -apple-system, "Segoe UI", Roboto, system-ui, sans-serif;
    margin: 2em auto; max-width: 1200px; padding: 0 1em;
    background: #fafafa; color: #1a1a1a;
  }}
  @media (prefers-color-scheme: dark) {{
    body {{ background: #0f1115; color: #e6e8eb; }}
    table {{ background: #161922; }}
    th {{ background: #1f2330; }}
    tr:hover {{ background: #1c2030; }}
    .counts-pre {{ color: #888; }}
  }}
  h1 {{ font-size: 1.6em; margin-bottom: 0.2em; }}
  .meta {{ color: #666; font-size: 0.9em; margin-bottom: 1.5em; }}
  table {{
    border-collapse: collapse; width: 100%;
    background: white; box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    font-size: 0.92em;
  }}
  th, td {{ padding: 0.6em 0.8em; text-align: left; vertical-align: top; border-bottom: 1px solid rgba(128,128,128,0.15); }}
  th {{ background: #f0f0f0; font-weight: 600; font-size: 0.85em; text-transform: uppercase; letter-spacing: 0.5px; }}
  tr:hover {{ background: rgba(0,0,0,0.02); }}
  td.ts {{ white-space: nowrap; font-variant-numeric: tabular-nums; color: #555; }}
  @media (prefers-color-scheme: dark) {{ td.ts {{ color: #aaa; }} }}
  td.label a {{ font-weight: 500; text-decoration: none; color: inherit; }}
  td.label a:hover {{ text-decoration: underline; }}
  td.counts {{ font-variant-numeric: tabular-nums; white-space: nowrap; }}
  .counts-pre {{ font-size: 0.85em; color: #999; }}
  td.summary {{ font-size: 0.88em; line-height: 1.4; }}
  td.transcript {{ white-space: nowrap; font-size: 0.85em; }}
  td.transcript a {{ color: #4a7eb8; text-decoration: none; }}
  td.transcript a:hover {{ text-decoration: underline; }}
  .badge {{ display: inline-block; padding: 0.15em 0.6em; border-radius: 3px;
    font-weight: 600; font-size: 0.8em; letter-spacing: 0.5px; }}
  .verdict-go {{ background: #2e7d32; color: white; }}
  .verdict-modify {{ background: #f57c00; color: white; }}
  .verdict-stop {{ background: #c62828; color: white; }}
  .verdict-split {{ background: #6a1b9a; color: white; }}
  .verdict-unreachable {{ background: #455a64; color: white; }}
  .verdict-unknown {{ background: #757575; color: white; }}
</style>
</head>
<body>
<h1>Senate History</h1>
<div class="meta">{count} decizii · generat {generated_at} · sursă <code>runs/senate/*.json</code></div>
<table>
<thead>
<tr><th>Data &amp; ora</th><th>Label</th><th>Verdict</th><th>Tally</th><th>Top modify_request</th><th>Transcript</th></tr>
</thead>
<tbody>
{rows}
</tbody>
</table>
</body>
</html>
"""


def render_html(bundles: list[dict], senate_dir: Path) -> str:
    rows = "\n".join(render_row(b, senate_dir) for b in bundles)
    return HTML_TEMPLATE.format(
        count=len(bundles),
        generated_at=dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        rows=rows,
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", default=None, help="senate runs dir (default: ./runs/senate)")
    ap.add_argument("--output", default="senate-history.html", help="output HTML file (default: senate-history.html)")
    ap.add_argument("--stdout", action="store_true", help="emit HTML to stdout instead of writing a file")
    args = ap.parse_args(argv)

    senate_dir = Path(args.runs) if args.runs else repo_root() / "runs" / "senate"
    if not senate_dir.is_dir():
        print(f"senate dir not found: {senate_dir}", file=sys.stderr)
        return 1

    bundles = load_bundles(senate_dir)
    if not bundles:
        print(f"no senate bundles found in {senate_dir}", file=sys.stderr)
        return 1

    html_text = render_html(bundles, senate_dir)

    if args.stdout:
        sys.stdout.write(html_text)
        return 0

    out_path = Path(args.output)
    out_path.write_text(html_text, encoding="utf-8")
    print(f"wrote {out_path} ({len(bundles)} decisions)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
