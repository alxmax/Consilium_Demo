"""Render entries + runs/*.json into a single dark-themed FEEDBACK.html.

Pure functions; no I/O except optional CLI shim. The HTML is self-contained
(inline <style> + <script>, no external assets). Drill-down content is
embedded statically per entry from the linked runs/*.json file.

CLI:
    python scripts/render_feedback_html.py < entries.json
    python scripts/render_feedback_html.py --feedback path/to/FEEDBACK.html < entries.json
"""
from __future__ import annotations

import argparse
import html
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Entry:
    date: str
    context: str
    chosen: str
    outcome: str  # OK | BAD | OVR | PEND
    note: str
    run_path: str | None = None  # relative path to runs/*.json (or None for legacy)


CSS = """
:root{--bg:#16161a;--bg-alt:#1c1c22;--bg-row:#1a1a20;--bg-row-alt:#1e1e25;--bg-drill:#121216;--fg:#d6d6d6;--fg-dim:#8a8a92;--fg-soft:#b4b4bc;--border:#2a2a32;--border-soft:#23232b;--accent:#7fb3ff;--mono:#9fc7ff;--ok:#5ec27a;--bad:#e36868;--ovr:#e0a85c;--pend:#787884;--valid:#5ec27a;--invalid:#e36868}
*{box-sizing:border-box}
body{font:13px/1.5 system-ui,-apple-system,Segoe UI,sans-serif;margin:1.5em;color:var(--fg);max-width:1400px;background:var(--bg)}
h2{margin:0 0 .25em;font-size:18px;font-weight:600;color:#fff}
.sub{color:var(--fg-dim);font-size:12px;margin-bottom:1.25em}
table{border-collapse:collapse;width:100%}
th,td{border-bottom:1px solid var(--border-soft);padding:7px 10px;text-align:left;vertical-align:top}
th{background:var(--bg-alt);font-weight:600;color:var(--fg-soft);white-space:nowrap;font-size:12px;text-transform:uppercase;letter-spacing:.04em}
tbody tr.entry{cursor:pointer;background:var(--bg-row);transition:background .12s}
tbody tr.entry:nth-child(4n+3){background:var(--bg-row-alt)}
tbody tr.entry:hover{background:#252530}
tbody tr.entry.open{background:#2b2b36}
td.outcome{font-weight:600;text-align:center;white-space:nowrap;font-size:12px;letter-spacing:.05em}
.OK{color:var(--ok)}.BAD{color:var(--bad)}.OVR{color:var(--ovr)}.PEND{color:var(--pend)}
td.date{white-space:nowrap;color:var(--fg-dim);font-variant-numeric:tabular-nums}
td.chosen{font-family:Consolas,Menlo,monospace;font-size:12px;color:var(--mono)}
td.note{color:var(--fg-soft);font-size:12px}
td.chev{width:18px;color:var(--fg-dim);text-align:center;font-family:monospace}
tr.entry.open td.chev{color:var(--accent)}
tr.drill{display:none;background:var(--bg-drill)}
tr.drill.open{display:table-row}
tr.drill td{border-bottom:1px solid var(--border);padding:14px 18px}
.drill-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:18px}
.voice{background:var(--bg-alt);border:1px solid var(--border-soft);border-radius:6px;padding:12px 14px}
.voice h4{margin:0 0 8px;font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:var(--accent);font-weight:600}
.voice h4 .count{color:var(--fg-dim);font-weight:400;margin-left:6px}
.cand{padding:8px 0;border-top:1px dashed var(--border-soft)}
.cand:first-of-type{border-top:none;padding-top:2px}
.cand .cid{font-family:Consolas,Menlo,monospace;font-size:11px;color:var(--mono);font-weight:600}
.cand .csum{color:var(--fg);font-size:12px;margin:2px 0}
.cand .csketch{color:var(--fg-dim);font-size:11px;font-style:italic;margin-top:2px}
.badge{display:inline-block;padding:1px 6px;border-radius:3px;font-size:10px;font-weight:600;letter-spacing:.03em;margin-left:6px;vertical-align:middle}
.badge.valid{background:rgba(94,194,122,.15);color:var(--valid)}
.badge.invalid{background:rgba(227,104,104,.15);color:var(--invalid)}
.issue{color:var(--bad);font-size:11px;margin-top:3px}
.issue::before{content:"\\2715 ";color:var(--bad)}
.test{color:var(--fg-dim);font-size:11px;margin-top:2px;font-family:Consolas,Menlo,monospace}
.test::before{content:"\\2713 ";color:var(--ok)}
.risk{font-family:Consolas,Menlo,monospace;font-size:13px;font-weight:600;float:right}
.risk.low{color:var(--ok)}.risk.mid{color:var(--ovr)}.risk.high{color:var(--bad)}
.factors{display:grid;grid-template-columns:repeat(2,1fr);gap:1px 10px;font-size:10px;color:var(--fg-dim);margin-top:3px;font-family:Consolas,Menlo,monospace}
.factors b{color:var(--fg-soft);font-weight:400}
.stub{color:var(--fg-dim);font-style:italic;font-size:12px;text-align:center;padding:8px}
"""

JS = """
function toggleDrill(row){
  var next = row.nextElementSibling;
  var chev = row.querySelector('.chev');
  if(next && next.classList.contains('drill')){
    var open = next.classList.toggle('open');
    row.classList.toggle('open', open);
    if(chev) chev.textContent = open ? '▾' : '▸';
  }
}
"""


def _esc(text: str) -> str:
    return html.escape(text or "", quote=True)


def _row_html(idx: int, e: Entry, drill_inner: str) -> str:
    chev = "▸"
    return (
        f'<tr class="entry" onclick="toggleDrill(this)">'
        f'<td class="chev">{chev}</td>'
        f'<td class="date">{_esc(e.date)}</td>'
        f'<td>{_esc(e.context)}</td>'
        f'<td class="chosen">{_esc(e.chosen)}</td>'
        f'<td class="outcome {_esc(e.outcome)}">{_esc(e.outcome)}</td>'
        f'<td class="note">{_esc(e.note)}</td>'
        f'</tr>\n'
        f'<tr class="drill"><td colspan="6">{drill_inner}</td></tr>\n'
    )


def _legacy_stub() -> str:
    return '<div class="stub">no detailed run data — older entry pre-runs/</div>'


def render(entries: list[Entry], runs_dir: Path) -> str:
    rows = []
    for idx, e in enumerate(entries):
        drill = _legacy_stub()  # drill-down filled in Task 3
        rows.append(_row_html(idx, e, drill))
    rows_html = "".join(rows)
    return (
        "<!doctype html>\n"
        "<meta charset=\"utf-8\">\n"
        "<title>max-agent feedback</title>\n"
        f"<style>{CSS}</style>\n"
        "<h2>max-agent feedback</h2>\n"
        f"<div class=\"sub\">{len(entries)} entries · skills/max-agent/FEEDBACK.html · click pe rând pentru detalii voci</div>\n"
        "<table>\n"
        "<thead><tr><th></th><th>Data</th><th>Context</th><th>Chosen</th><th>Outcome</th><th>Note</th></tr></thead>\n"
        f"<tbody>\n{rows_html}</tbody>\n"
        "</table>\n"
        f"<script>{JS}</script>\n"
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs-dir", default=None)
    args = ap.parse_args(argv)
    data = json.load(sys.stdin)
    entries = [Entry(**e) for e in data.get("entries", [])]
    runs_dir = Path(args.runs_dir) if args.runs_dir else Path.cwd() / "runs"
    sys.stdout.write(render(entries, runs_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
