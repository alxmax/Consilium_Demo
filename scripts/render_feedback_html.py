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
    vote_pattern: str = ""  # e.g. "2-1" for Trias mode; empty for non-Trias


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
td.tokens{font-family:Consolas,Menlo,monospace;font-size:12px;color:var(--fg-dim);text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
td.tokens.na{color:var(--border)}
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


def _row_html(idx: int, e: Entry, drill_inner: str, tokens_str: str) -> str:
    chev = "▸"
    tokens_cls = "tokens" if tokens_str != "—" else "tokens na"
    return (
        f'<tr class="entry" onclick="toggleDrill(this)">'
        f'<td class="chev">{chev}</td>'
        f'<td class="date">{_esc(e.date)}</td>'
        f'<td>{_esc(e.context)}</td>'
        f'<td class="chosen">{_esc(e.chosen)}</td>'
        f'<td class="outcome {_esc(e.outcome)}">{_esc(e.outcome)}</td>'
        f'<td class="{tokens_cls}">{tokens_str}</td>'
        f'<td class="note">{_esc(e.note)}</td>'
        f'<td>{_esc(e.vote_pattern)}</td>'
        f'</tr>\n'
        f'<tr class="drill"><td colspan="8">{drill_inner}</td></tr>\n'
    )


def _total_tokens(run: dict | None) -> str:
    """Sum tokens_in + tokens_out across all voices in run.telemetry.voices.

    Returns compact format: integer below 1000, X.Yk for 1000-9999,
    rounded Nk for >=10000. Returns '—' if telemetry is missing/empty.
    """
    if not run:
        return "—"
    voices = ((run.get("telemetry") or {}).get("voices") or {})
    if not voices:
        return "—"
    total = 0
    for v in voices.values():
        if not isinstance(v, dict):
            continue
        ti = v.get("tokens_in") or 0
        to = v.get("tokens_out") or 0
        if isinstance(ti, (int, float)):
            total += int(ti)
        if isinstance(to, (int, float)):
            total += int(to)
    if total <= 0:
        return "—"
    if total < 1000:
        return str(total)
    formatted = f"{total/1000:.1f}"
    if formatted.endswith(".0"):
        formatted = formatted[:-2]
    return f"{formatted}k"


def _risk_class(score: float) -> str:
    if score < 0.3:
        return "low"
    if score < 0.6:
        return "mid"
    return "high"


def _gen_panel(run: dict, chosen_id: str) -> str:
    log = run.get("deliberation_log") or []
    gen_step = next((s for s in log if isinstance(s, dict) and s.get("step") == "generator"), {})
    cands = gen_step.get("candidates") or []
    parts = [f'<div class="voice"><h4>Generator <span class="count">{len(cands)} candidates</span></h4>']
    for c in cands:
        cid = _esc(c.get("id", ""))
        chosen_badge = ' <span class="badge valid">CHOSEN</span>' if c.get("id") == chosen_id else ""
        summary = _esc(c.get("summary", ""))
        sketch = _esc(c.get("sketch", ""))
        parts.append(
            f'<div class="cand"><div><span class="cid">{cid}</span>{chosen_badge}</div>'
            f'<div class="csum">{summary}</div>'
            f'<div class="csketch">{sketch}</div></div>'
        )
    parts.append("</div>")
    return "".join(parts)


def _ctrl_panel(run: dict) -> str:
    log = run.get("deliberation_log") or []
    ctrl_step = next((s for s in log if isinstance(s, dict) and s.get("step") == "control"), {})
    verdicts = ctrl_step.get("verdicts") or []
    n_valid = sum(1 for v in verdicts if v.get("valid"))
    n_invalid = len(verdicts) - n_valid
    parts = [f'<div class="voice"><h4>Control <span class="count">{n_valid} valid, {n_invalid} invalid</span></h4>']
    for v in verdicts:
        cid = _esc(v.get("id", ""))
        badge_cls = "valid" if v.get("valid") else "invalid"
        badge_txt = "valid" if v.get("valid") else "invalid"
        parts.append(
            f'<div class="cand"><div><span class="cid">{cid}</span> '
            f'<span class="badge {badge_cls}">{badge_txt}</span></div>'
        )
        for issue in v.get("issues") or []:
            cat = _esc(issue.get("category", ""))
            detail = _esc(issue.get("detail", ""))
            parts.append(f'<div class="issue">{cat}: {detail}</div>')
        for t in v.get("tests_to_write") or []:
            name = _esc(t.get("name", ""))
            assertion = _esc(t.get("assert", ""))
            parts.append(f'<div class="test">{name}: {assertion}</div>')
        parts.append("</div>")
    parts.append("</div>")
    return "".join(parts)


def _cons_panel(run: dict) -> str:
    log = run.get("deliberation_log") or []
    cons_step = next((s for s in log if isinstance(s, dict) and s.get("step") == "conservator"), {})
    scores = cons_step.get("scores") or []
    n_vetoed = sum(1 for s in scores if (s.get("risk_score") or 0) >= 0.7)
    parts = [f'<div class="voice"><h4>Conservator <span class="count">{len(scores)} scored, {n_vetoed} vetoed</span></h4>']
    for s in scores:
        cid = _esc(s.get("id", ""))
        rs = s.get("risk_score") or 0.0
        rcls = _risk_class(rs)
        vetoed_badge = ' <span class="badge invalid">VETOED</span>' if rs >= 0.7 else ""
        f = s.get("factors") or {}
        parts.append(
            f'<div class="cand">'
            f'<span class="risk {rcls}">{rs:.2f}</span>'
            f'<div><span class="cid">{cid}</span>{vetoed_badge}</div>'
            f'<div class="factors">'
            f'<span><b>diff:</b> {(f.get("diff_size") or 0):.2f}</span>'
            f'<span><b>scope:</b> {(f.get("scope_drift") or 0):.2f}</span>'
            f'<span><b>regr:</b> {(f.get("regression_risk") or 0):.2f}</span>'
            f'<span><b>rev:</b> {(f.get("reversibility") or 0):.2f}</span>'
            f'</div></div>'
        )
    parts.append("</div>")
    return "".join(parts)


def render_drill(run: dict, chosen_id: str) -> str:
    return (
        '<div class="drill-grid">'
        + _gen_panel(run, chosen_id)
        + _ctrl_panel(run)
        + _cons_panel(run)
        + "</div>"
    )


def _legacy_stub() -> str:
    return '<div class="stub">no detailed run data — older entry pre-runs/</div>'


def render(entries: list[Entry], runs_dir: Path) -> str:
    rows = []
    for idx, e in enumerate(entries):
        run_dict = None
        if e.run_path:
            run_file = runs_dir.parent / e.run_path if not Path(e.run_path).is_absolute() else Path(e.run_path)
            # Accept both repo-relative ("runs/foo.json") and direct ("foo.json") forms.
            if not run_file.exists():
                run_file = runs_dir / Path(e.run_path).name
            if run_file.exists():
                try:
                    run_dict = json.loads(run_file.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    run_dict = None
        drill = render_drill(run_dict, e.chosen) if run_dict else _legacy_stub()
        tokens_str = _total_tokens(run_dict)
        rows.append(_row_html(idx, e, drill, tokens_str))
    rows_html = "".join(rows)
    return (
        "<!doctype html>\n"
        "<meta charset=\"utf-8\">\n"
        "<title>Consilium feedback</title>\n"
        f"<style>{CSS}</style>\n"
        "<h2>Consilium feedback</h2>\n"
        f"<div class=\"sub\">{len(entries)} entries · skills/consilium/FEEDBACK.html · click pe rând pentru detalii voci</div>\n"
        "<table>\n"
        "<thead><tr><th></th><th>Data</th><th>Context</th><th>Chosen</th><th>Outcome</th><th>Tokens</th><th>Note</th><th>Vote Pattern</th></tr></thead>\n"
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
