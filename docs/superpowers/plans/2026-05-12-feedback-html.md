# FEEDBACK.md → FEEDBACK.html Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Markdown feedback journal at `skills/consilium/FEEDBACK.md` with a dark-themed `FEEDBACK.html` table that supports row-level drill-down into the corresponding `runs/*.json` voice outputs, while keeping `priors.py` / `feedback.py` / `log_feedback.py` working against the new format.

**Architecture:** Add a new pure-render module `scripts/render_feedback_html.py` (entries list → HTML string). Modify `feedback.py` parser to read `<tr class="entry">` rows from HTML. Modify `log_feedback.py` to round-trip through render. Add a one-shot migration script. `runs/*.json` schema unchanged; drill-down content is statically embedded at render time. Spec: `docs/superpowers/specs/2026-05-12-feedback-html-design.md`.

**Tech Stack:** Python 3.x (stdlib only — `re`, `html`, `pathlib`, `json`, `argparse`, `datetime`). Pure string templating, no Jinja. Tests run via the existing `scripts/run_evals.py` + `evals/scenarios.json` harness plus a small dedicated `scripts/test_feedback_html.py` for non-CLI assertions.

---

## File Structure

| Path | State | Responsibility |
|---|---|---|
| `scripts/render_feedback_html.py` | new | Pure functions: `Entry` dataclass, `render(entries, runs_dir) -> str`, `render_drill(run_dict) -> str`. CLI emits HTML to stdout for testing. |
| `scripts/feedback.py` | modify | Swap `ENTRY_RE` and `parse_feedback()` to read `<tr class="entry">` rows from `FEEDBACK.html`. Keep field names (`date`, `context`, `chosen`, `outcome`, `note`) unchanged so `priors.py` is untouched. Update `FEEDBACK` constant to point at `.html`. |
| `scripts/log_feedback.py` | modify | Switch append path: load existing entries from HTML, append new one, re-render. Add `--run-path` flag. Default `--feedback` to `FEEDBACK.html`. |
| `scripts/migrate_feedback_md_to_html.py` | new | One-shot: parse old `FEEDBACK.md` lines, fuzzy-match each to a `runs/*.json`, render HTML. Backup MD to `.md.bak`. |
| `scripts/test_feedback_html.py` | new | Dedicated unit-test harness (assert-based, exit 0/1) for renderer + parser. Invoked from `run_evals.py` integration tests or standalone. |
| `evals/scenarios.json` | modify | Add 4 scenarios exercising the renderer CLI and parser roundtrip. |
| `SKILL.md` | modify | Text-only references: `FEEDBACK.md` → `FEEDBACK.html` in §"Feedback loop (artefacte)", Step 0 priors call, Step 6 log call, "Skill maintenance" audit. |
| `FEEDBACK.html` | generated | Output of migration script. Replaces `.md`. Gitignored. |
| `FEEDBACK.md.bak` | generated | Backup of legacy MD. Gitignored. |
| `.gitignore` | modify | Add `FEEDBACK.html` and `*.md.bak` (alongside existing `FEEDBACK.md` line). |

`priors.py` does **not** change — it imports `parse_feedback` from `feedback.py`, which we update.

---

## Task 1: Renderer module skeleton + drill-down rendering

**Files:**
- Create: `scripts/render_feedback_html.py`
- Create: `scripts/test_feedback_html.py`

- [ ] **Step 1.1: Create the test file with the first failing test**

Write to `scripts/test_feedback_html.py`:

```python
"""Standalone tests for render_feedback_html + feedback.py HTML parser.

Run: python scripts/test_feedback_html.py
Exit 0 = all pass; exit 1 = first failure with traceback.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import render_feedback_html as rfh  # noqa: E402


def test_render_empty_entries_produces_skeleton():
    html = rfh.render(entries=[], runs_dir=ROOT / "runs")
    assert "<!doctype html>" in html
    assert "consilium feedback" in html
    assert "<tbody>" in html and "</tbody>" in html
    assert "0 entries" in html


def _run_tests():
    funcs = [v for k, v in globals().items() if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in funcs:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {fn.__name__}: {e}")
        except Exception as e:
            failed += 1
            print(f"ERROR {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(funcs) - failed}/{len(funcs)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_run_tests())
```

- [ ] **Step 1.2: Run test to verify it fails**

Run: `python C:/Users/ALEX/.claude/skills/consilium/scripts/test_feedback_html.py`
Expected: `ModuleNotFoundError: No module named 'render_feedback_html'`

- [ ] **Step 1.3: Create minimal renderer to pass the test**

Write to `scripts/render_feedback_html.py`:

```python
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


def render(entries: list[Entry], runs_dir: Path) -> str:
    rows_html = ""
    return (
        "<!doctype html>\n"
        "<meta charset=\"utf-8\">\n"
        "<title>consilium feedback</title>\n"
        f"<style>{CSS}</style>\n"
        "<h2>consilium feedback</h2>\n"
        f"<div class=\"sub\">{len(entries)} entries · skills/consilium/FEEDBACK.html · click pe rând pentru detalii voci</div>\n"
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
```

- [ ] **Step 1.4: Run test to verify it passes**

Run: `python C:/Users/ALEX/.claude/skills/consilium/scripts/test_feedback_html.py`
Expected: `PASS test_render_empty_entries_produces_skeleton` and `1/1 passed`. Exit 0.

- [ ] **Step 1.5: Commit**

```bash
cd C:/Users/ALEX/.claude/skills/consilium
git add scripts/render_feedback_html.py scripts/test_feedback_html.py
git commit -m "feat(feedback-html): renderer skeleton + first test"
```

---

## Task 2: Render entries with no drill-down (legacy stub)

**Files:**
- Modify: `scripts/render_feedback_html.py:render()`
- Modify: `scripts/test_feedback_html.py` (append tests)

- [ ] **Step 2.1: Append failing tests for entry rows**

Append to `scripts/test_feedback_html.py` *before* `_run_tests`:

```python
def test_render_single_legacy_entry_no_drill():
    e = rfh.Entry(
        date="2026-05-11",
        context="audit-reduction",
        chosen="nuke_orphans_and_stale_readme",
        outcome="PEND",
        note="5 cand, conf=0.63",
        run_path=None,
    )
    html_out = rfh.render([e], runs_dir=ROOT / "runs")
    assert "1 entries" in html_out
    assert "2026-05-11" in html_out
    assert "nuke_orphans_and_stale_readme" in html_out
    assert "PEND" in html_out
    assert 'class="outcome PEND"' in html_out
    assert "no detailed run data" in html_out
    assert 'class="entry"' in html_out
    assert 'class="drill"' in html_out


def test_render_escapes_html_in_user_text():
    e = rfh.Entry(
        date="2026-05-11",
        context="<script>alert(1)</script>",
        chosen="x",
        outcome="OK",
        note="& \"quoted\"",
        run_path=None,
    )
    html_out = rfh.render([e], runs_dir=ROOT / "runs")
    assert "<script>alert(1)</script>" not in html_out
    assert "&lt;script&gt;" in html_out
    assert "&amp;" in html_out
```

- [ ] **Step 2.2: Run tests to verify they fail**

Run: `python C:/Users/ALEX/.claude/skills/consilium/scripts/test_feedback_html.py`
Expected: `FAIL test_render_single_legacy_entry_no_drill` (`'1 entries' not in html_out`) and `FAIL test_render_escapes_html_in_user_text`.

- [ ] **Step 2.3: Implement entry row rendering with HTML escaping**

In `scripts/render_feedback_html.py`, replace the `render` function with:

```python
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
        "<title>consilium feedback</title>\n"
        f"<style>{CSS}</style>\n"
        "<h2>consilium feedback</h2>\n"
        f"<div class=\"sub\">{len(entries)} entries · skills/consilium/FEEDBACK.html · click pe rând pentru detalii voci</div>\n"
        "<table>\n"
        "<thead><tr><th></th><th>Data</th><th>Context</th><th>Chosen</th><th>Outcome</th><th>Note</th></tr></thead>\n"
        f"<tbody>\n{rows_html}</tbody>\n"
        "</table>\n"
        f"<script>{JS}</script>\n"
    )
```

- [ ] **Step 2.4: Run tests to verify they pass**

Run: `python C:/Users/ALEX/.claude/skills/consilium/scripts/test_feedback_html.py`
Expected: `3/3 passed`.

- [ ] **Step 2.5: Commit**

```bash
cd C:/Users/ALEX/.claude/skills/consilium
git add scripts/render_feedback_html.py scripts/test_feedback_html.py
git commit -m "feat(feedback-html): legacy entry rows with HTML escaping"
```

---

## Task 3: Drill-down rendering from runs/*.json

**Files:**
- Modify: `scripts/render_feedback_html.py` (add `render_drill`)
- Modify: `scripts/test_feedback_html.py`
- Read fixture: `runs/2026-05-11_2030_live-rerun-resilience.json` (existing)

- [ ] **Step 3.1: Append failing test for drill-down**

Append to `scripts/test_feedback_html.py` before `_run_tests`:

```python
def test_render_drill_from_real_run_file():
    e = rfh.Entry(
        date="2026-05-11",
        context="Click pe sageata Rerun din topbar",
        chosen="disable_when_unreachable",
        outcome="PEND",
        note="5 cand, 1 vetoed, conf=0.62",
        run_path="runs/2026-05-11_2030_live-rerun-resilience.json",
    )
    html_out = rfh.render([e], runs_dir=ROOT / "runs")
    # Generator section
    assert "Generator" in html_out
    assert "do_nothing" in html_out
    assert "disable_when_unreachable" in html_out
    assert "adversarial_url_protocol_handler" in html_out
    # CHOSEN badge on the picked candidate
    assert "CHOSEN" in html_out
    # Control section: valid/invalid badges
    assert ">valid<" in html_out
    assert ">invalid<" in html_out
    # Tests rendered
    assert "probe_success_enables" in html_out
    # Conservator section: factor breakdown
    assert "diff:" in html_out
    assert "scope:" in html_out
    assert "0.14" in html_out  # disable_when_unreachable risk_score
    # VETOED badge on conservator side (Control marked adversarial invalid, conservator score >=0.7)
    # Note: in this run adversarial is Control-invalid so it gets no Conservator score; only score-side veto rendered
    assert "no detailed run data" not in html_out


def test_render_drill_missing_run_file_falls_back_to_stub():
    e = rfh.Entry(
        date="2026-05-11",
        context="x",
        chosen="y",
        outcome="PEND",
        note="",
        run_path="runs/does_not_exist.json",
    )
    html_out = rfh.render([e], runs_dir=ROOT / "runs")
    assert "no detailed run data" in html_out
```

- [ ] **Step 3.2: Run tests to verify they fail**

Run: `python C:/Users/ALEX/.claude/skills/consilium/scripts/test_feedback_html.py`
Expected: `FAIL test_render_drill_from_real_run_file` (`'Generator' not in html_out`) and previous tests still pass.

- [ ] **Step 3.3: Implement drill-down rendering**

In `scripts/render_feedback_html.py`, **before** the `render` function, add these helpers (replace `_legacy_stub` while you're at it, and replace `render` body to use the new resolver):

```python
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
```

Then update the `render` function body to resolve `run_path`:

```python
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
                except json.JSONDecodeError:
                    run_dict = None
        drill = render_drill(run_dict, e.chosen) if run_dict else _legacy_stub()
        rows.append(_row_html(idx, e, drill))
    rows_html = "".join(rows)
    return (
        "<!doctype html>\n"
        "<meta charset=\"utf-8\">\n"
        "<title>consilium feedback</title>\n"
        f"<style>{CSS}</style>\n"
        "<h2>consilium feedback</h2>\n"
        f"<div class=\"sub\">{len(entries)} entries · skills/consilium/FEEDBACK.html · click pe rând pentru detalii voci</div>\n"
        "<table>\n"
        "<thead><tr><th></th><th>Data</th><th>Context</th><th>Chosen</th><th>Outcome</th><th>Note</th></tr></thead>\n"
        f"<tbody>\n{rows_html}</tbody>\n"
        "</table>\n"
        f"<script>{JS}</script>\n"
    )
```

- [ ] **Step 3.4: Run tests to verify they pass**

Run: `python C:/Users/ALEX/.claude/skills/consilium/scripts/test_feedback_html.py`
Expected: `5/5 passed`.

- [ ] **Step 3.5: Commit**

```bash
cd C:/Users/ALEX/.claude/skills/consilium
git add scripts/render_feedback_html.py scripts/test_feedback_html.py
git commit -m "feat(feedback-html): drill-down panels from runs/*.json"
```

---

## Task 4: HTML parser in feedback.py

**Files:**
- Modify: `scripts/feedback.py` (lines 22, 27-33, 36-44)
- Modify: `scripts/test_feedback_html.py`

- [ ] **Step 4.1: Append failing test for HTML parser**

Append to `scripts/test_feedback_html.py` before `_run_tests`:

```python
def test_parse_feedback_roundtrip_html():
    # Build entries, render to HTML, parse back, expect same fields.
    sys.path.insert(0, str(ROOT / "scripts"))
    import feedback  # noqa: E402

    original = [
        rfh.Entry(date="2026-05-11", context="ctx one", chosen="approach_a",
                  outcome="OK", note="5 cand, conf=0.65"),
        rfh.Entry(date="2026-05-12", context="ctx <two> & special",
                  chosen="approach_b", outcome="OVR",
                  note="override=alt; conf=0.43"),
    ]
    html_out = rfh.render(original, runs_dir=ROOT / "runs")

    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html_out)
        tmp_path = Path(f.name)
    try:
        parsed = feedback.parse_feedback(tmp_path)
    finally:
        tmp_path.unlink()

    assert len(parsed) == 2, f"got {len(parsed)} entries, want 2"
    assert parsed[0]["date"] == "2026-05-11"
    assert parsed[0]["context"] == "ctx one"
    assert parsed[0]["chosen"] == "approach_a"
    assert parsed[0]["outcome"] == "OK"
    assert "5 cand" in parsed[0]["note"]
    assert parsed[1]["context"] == "ctx <two> & special"  # unescaped on parse
    assert parsed[1]["outcome"] == "OVR"


def test_parse_feedback_returns_empty_for_missing_file():
    sys.path.insert(0, str(ROOT / "scripts"))
    import feedback  # noqa: E402
    assert feedback.parse_feedback(Path("/nonexistent/FEEDBACK.html")) == []
```

- [ ] **Step 4.2: Run tests to verify they fail**

Run: `python C:/Users/ALEX/.claude/skills/consilium/scripts/test_feedback_html.py`
Expected: `FAIL test_parse_feedback_roundtrip_html` (parser still expects MD; gets 0 entries).

- [ ] **Step 4.3: Swap parser in feedback.py to HTML**

In `scripts/feedback.py`, replace lines 22 (`FEEDBACK = ROOT / "FEEDBACK.md"`) with:

```python
FEEDBACK = ROOT / "FEEDBACK.html"
```

Replace lines 27-33 (the old `ENTRY_RE`) with:

```python
ROW_RE = re.compile(
    r'<tr class="entry"[^>]*>(?P<body>.*?)</tr>',
    re.DOTALL,
)
CELL_RE = re.compile(r'<td[^>]*>(?P<text>.*?)</td>', re.DOTALL)
TAG_RE = re.compile(r'<[^>]+>')
```

Replace lines 36-44 (the old `parse_feedback`) with:

```python
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
        cells = CELL_RE.findall(m.group("body"))
        if len(cells) < 6:
            continue
        # cells order: [chev, date, context, chosen, outcome, note]
        date = _strip_tags(cells[1])
        context = _strip_tags(cells[2])
        chosen = _strip_tags(cells[3])
        outcome = _strip_tags(cells[4])
        note = _strip_tags(cells[5])
        if outcome not in ("OK", "BAD", "OVR", "PEND"):
            continue
        entries.append({
            "date": date,
            "context": context,
            "chosen": chosen,
            "outcome": outcome,
            "note": note,
        })
    return entries
```

- [ ] **Step 4.4: Run tests to verify they pass**

Run: `python C:/Users/ALEX/.claude/skills/consilium/scripts/test_feedback_html.py`
Expected: `7/7 passed`.

- [ ] **Step 4.5: Verify priors.py still imports & works**

Run: `cd C:/Users/ALEX/.claude/skills/consilium && python scripts/priors.py --no-runs`
Expected: JSON output without exception (entries list may be empty if FEEDBACK.html doesn't yet exist — that's OK; the `_outcome_counts` returns empty Counter).

- [ ] **Step 4.6: Commit**

```bash
cd C:/Users/ALEX/.claude/skills/consilium
git add scripts/feedback.py scripts/test_feedback_html.py
git commit -m "feat(feedback-html): swap feedback.py parser to HTML rows"
```

---

## Task 5: log_feedback.py rewrites HTML in place

**Files:**
- Modify: `scripts/log_feedback.py`
- Modify: `scripts/test_feedback_html.py`

- [ ] **Step 5.1: Append failing test for append-then-roundtrip**

Append to `scripts/test_feedback_html.py` before `_run_tests`:

```python
def test_log_feedback_appends_html_entry():
    import subprocess
    sys.path.insert(0, str(ROOT / "scripts"))
    import feedback  # noqa: E402

    with tempfile.TemporaryDirectory() as td:
        feedback_path = Path(td) / "FEEDBACK.html"
        # Pre-populate with one entry via render.
        e0 = rfh.Entry(date="2026-05-01", context="pre", chosen="x",
                       outcome="OK", note="seed")
        feedback_path.write_text(rfh.render([e0], runs_dir=ROOT / "runs"), encoding="utf-8")

        report = {
            "success_criterion": "fix the test",
            "chosen_approach": "approach_a",
            "confidence": 0.81,
            "telemetry": {"mode": "parallel"},
            "deliberation_log": [{"step": "generator", "candidates": [{"id": "a"}, {"id": "b"}]}],
        }
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "log_feedback.py"),
             "--feedback", str(feedback_path),
             "--outcome", "OK"],
            input=json.dumps(report).encode("utf-8"),
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, f"stderr: {result.stderr.decode()}"

        parsed = feedback.parse_feedback(feedback_path)
        assert len(parsed) == 2, f"expected 2 entries (1 seed + 1 appended), got {len(parsed)}"
        assert parsed[1]["chosen"] == "approach_a"
        assert parsed[1]["outcome"] == "OK"


import json  # noqa: E402 (used by the test above)
```

- [ ] **Step 5.2: Run test to verify it fails**

Run: `python C:/Users/ALEX/.claude/skills/consilium/scripts/test_feedback_html.py`
Expected: `FAIL test_log_feedback_appends_html_entry` (log_feedback still appends MD line, breaking HTML).

- [ ] **Step 5.3: Rewrite log_feedback.py append logic**

In `scripts/log_feedback.py`, replace lines 57-63 (the `HEADER_LINES` constant) with:

```python
HEADER_LINES = ()  # legacy MD header no longer used
```

Replace the `append_line` function (lines 139-144) with a render-based round-trip:

```python
def append_entry(feedback_path: Path, entry: dict, run_path: str | None) -> None:
    """Round-trip the HTML: parse existing rows, append, re-render."""
    import importlib.util
    here = Path(__file__).resolve().parent
    feedback_spec = importlib.util.spec_from_file_location("consilium_feedback", here / "feedback.py")
    assert feedback_spec and feedback_spec.loader
    feedback_mod = importlib.util.module_from_spec(feedback_spec)
    feedback_spec.loader.exec_module(feedback_mod)

    render_spec = importlib.util.spec_from_file_location("consilium_render", here / "render_feedback_html.py")
    assert render_spec and render_spec.loader
    render_mod = importlib.util.module_from_spec(render_spec)
    render_spec.loader.exec_module(render_mod)

    existing = feedback_mod.parse_feedback(feedback_path)
    # parse_feedback returns dicts WITHOUT run_path (not persisted in HTML cells).
    # On rerender, drill-down for existing rows would degrade to legacy stub unless
    # we keep their original drill HTML. Simplest faithful approach: re-derive
    # run_path from a sidecar JSON map if present; otherwise stub. For Phase 1
    # we accept stub for legacy rows — the migrate script handles initial population.
    entries = [render_mod.Entry(**row, run_path=None) for row in existing]
    new_entry = render_mod.Entry(
        date=entry["date"],
        context=entry["context"],
        chosen=entry["chosen"],
        outcome=entry["outcome"],
        note=entry["note"],
        run_path=run_path,
    )
    entries.append(new_entry)
    runs_dir = feedback_path.parent / "runs"
    feedback_path.write_text(render_mod.render(entries, runs_dir), encoding="utf-8")
```

Then replace `build_line` (which returned a string) with a builder that returns a dict instead — and update `main`. Replace lines 107-137 (`build_line` function) with:

```python
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
    }
```

Update `main` (lines 156-204). Replace the `--feedback` default and the trailing block (everything from `args = ap.parse_args(argv)` onward):

```python
def main(argv: list[str] | None = None) -> int:
    _force_utf8_streams()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--feedback", default=None, help="path to FEEDBACK.html (default: ./FEEDBACK.html)")
    ap.add_argument("--dry-run", action="store_true", help="print summary, don't write file")
    ap.add_argument(
        "--outcome",
        choices=("OK", "BAD", "OVR", "PEND"),
        default="PEND",
        help="outcome to record (default: PEND; set OK/OVR after confidence-gated user prompt)",
    )
    ap.add_argument("--override-target", default=None, help="alt_id when --outcome=OVR")
    ap.add_argument("--user-note", default=None, help="optional user-supplied note appended to auto-note")
    ap.add_argument("--run-path", default=None, help="relative path to runs/*.json for drill-down (e.g. runs/2026-05-12_foo.json)")
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
        append_entry(feedback_path, entry, args.run_path)

    print(f"{entry['date']} | {entry['context']} | {entry['chosen']} | {entry['outcome']} | {entry['note']}")
    return 0
```

Delete the now-unused `build_line` reference (already replaced) and `append_line` (already replaced). Update the module docstring at lines 8-9 to read:

```python
Entry format:
    {date, context, chosen, outcome, note} appended as <tr> to FEEDBACK.html.
```

- [ ] **Step 5.4: Run test to verify it passes**

Run: `python C:/Users/ALEX/.claude/skills/consilium/scripts/test_feedback_html.py`
Expected: `8/8 passed`.

- [ ] **Step 5.5: Commit**

```bash
cd C:/Users/ALEX/.claude/skills/consilium
git add scripts/log_feedback.py scripts/test_feedback_html.py
git commit -m "feat(feedback-html): log_feedback round-trips HTML on append"
```

---

## Task 6: One-shot migration script

**Files:**
- Create: `scripts/migrate_feedback_md_to_html.py`

- [ ] **Step 6.1: Append failing test for migration**

Append to `scripts/test_feedback_html.py` before `_run_tests`:

```python
def test_migration_parses_legacy_md_and_emits_html():
    import subprocess
    with tempfile.TemporaryDirectory() as td:
        md_path = Path(td) / "FEEDBACK.md"
        html_path = Path(td) / "FEEDBACK.html"
        md_path.write_text(
            "# FEEDBACK\n#\n# data | context | chosen | outcome | note\n\n"
            "- 2026-05-11 | audit-reduction | nuke_orphans | PEND | 5 cand, conf=0.63\n"
            "- 2026-05-12 | rerun-resilience | disable_when_unreachable | OK | conf=0.62\n",
            encoding="utf-8",
        )
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "migrate_feedback_md_to_html.py"),
             "--md", str(md_path),
             "--html", str(html_path),
             "--runs-dir", str(ROOT / "runs")],
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, f"stderr: {result.stderr.decode()}"
        assert html_path.exists()
        body = html_path.read_text(encoding="utf-8")
        assert "nuke_orphans" in body
        assert "disable_when_unreachable" in body
        assert (md_path.parent / "FEEDBACK.md.bak").exists()
        assert not md_path.exists()
```

- [ ] **Step 6.2: Run test to verify it fails**

Run: `python C:/Users/ALEX/.claude/skills/consilium/scripts/test_feedback_html.py`
Expected: `FAIL test_migration_parses_legacy_md_and_emits_html` (script doesn't exist; FileNotFoundError).

- [ ] **Step 6.3: Implement migration script**

Write to `scripts/migrate_feedback_md_to_html.py`:

```python
"""One-shot migration: FEEDBACK.md → FEEDBACK.html.

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

ROOT = Path(__file__).resolve().parent.parent

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
```

- [ ] **Step 6.4: Run test to verify it passes**

Run: `python C:/Users/ALEX/.claude/skills/consilium/scripts/test_feedback_html.py`
Expected: `9/9 passed`.

- [ ] **Step 6.5: Commit**

```bash
cd C:/Users/ALEX/.claude/skills/consilium
git add scripts/migrate_feedback_md_to_html.py scripts/test_feedback_html.py
git commit -m "feat(feedback-html): one-shot migration script with fuzzy run match"
```

---

## Task 7: SKILL.md text updates + .gitignore

**Files:**
- Modify: `SKILL.md` (4 references)
- Modify: `.gitignore`

- [ ] **Step 7.1: Locate exact SKILL.md references**

Run: `cd C:/Users/ALEX/.claude/skills/consilium && grep -n "FEEDBACK.md" SKILL.md`
Expected output: 4-5 line numbers. Note them.

- [ ] **Step 7.2: Replace each reference**

For each reported line, replace `FEEDBACK.md` with `FEEDBACK.html` in `SKILL.md`. Use the Edit tool with unique surrounding context per occurrence. Specifically expect occurrences at:
- Step 0 (bootstrap describing priors reading from feedback)
- Step 6 final actions (log_feedback.py target file)
- "Feedback loop (artefacte)" section bullet
- "Skill maintenance" / audit periodic feedback section

Example edit pattern (apply to each line):

```
old_string: "FEEDBACK.md"
new_string: "FEEDBACK.html"
```

(Use `replace_all=true` only if grep confirmed no false-positive substrings; otherwise edit each occurrence with surrounding context.)

- [ ] **Step 7.3: Update .gitignore**

Run: `cd C:/Users/ALEX/.claude/skills/consilium && cat .gitignore`

If `.gitignore` contains `FEEDBACK.md`, leave it (legacy backup `.md.bak` matches no rule otherwise — add it). Append (using Edit with appropriate anchor):

```
FEEDBACK.html
*.md.bak
```

- [ ] **Step 7.4: Verify SKILL.md still reads cleanly**

Run: `cd C:/Users/ALEX/.claude/skills/consilium && grep -n "FEEDBACK" SKILL.md`
Expected: all matches now reference `FEEDBACK.html`, none mention `FEEDBACK.md`.

- [ ] **Step 7.5: Commit**

```bash
cd C:/Users/ALEX/.claude/skills/consilium
git add SKILL.md .gitignore
git commit -m "docs(feedback-html): update SKILL.md references and .gitignore"
```

---

## Task 8: Live migration + smoke test

**Files:**
- Modify: `skills/consilium/FEEDBACK.md` (consumed, renamed to `.md.bak`)
- Create: `skills/consilium/FEEDBACK.html`

- [ ] **Step 8.1: Run migration script**

Run: `cd C:/Users/ALEX/.claude/skills/consilium && python scripts/migrate_feedback_md_to_html.py`
Expected stdout:
```
wrote .../FEEDBACK.html (13 entries)
  2026-05-11 | xss_hardening_pass + 2 follow-ups -> STUB
  2026-05-11 | nuke_orphans_and_stale_readme -> runs/2026-05-11_1620_audit-reduction.json
  ...
backed up FEEDBACK.md -> FEEDBACK.md.bak
```

If `STUB` count is unexpectedly high (more than ~3 legacy entries), inspect the `runs/` filenames vs. chosen IDs — may need a manual fixup pass before promotion. Re-running requires `--force` since HTML exists.

- [ ] **Step 8.2: Open the HTML in a browser**

Run: `cd C:/Users/ALEX/.claude/skills/consilium && start FEEDBACK.html` (Windows) or open the file manually.
Expected: dark-themed table renders, 13 rows visible, outcomes colored; clicking row 4 (or whichever maps to `live-rerun-resilience.json`) expands the drill-down with 3 voice columns.

- [ ] **Step 8.3: Verify priors.py reads the new file**

Run: `cd C:/Users/ALEX/.claude/skills/consilium && python scripts/priors.py --no-runs`
Expected: JSON output with `recent`, `counts`, `override_rate`, `bad_rate`, `top_note_keywords` populated from the migrated entries (same numbers as before migration — sanity check by running `python scripts/feedback.py` and comparing outcome tallies).

- [ ] **Step 8.4: Smoke-test log_feedback append**

Run from PowerShell (one line):
```powershell
Get-Content "C:\Users\ALEX\.claude\skills\consilium\runs\2026-05-11_2030_live-rerun-resilience.json" | python "C:\Users\ALEX\.claude\skills\consilium\scripts\log_feedback.py" --feedback "C:\Users\ALEX\.claude\skills\consilium\FEEDBACK.html" --outcome PEND --run-path "runs/2026-05-11_2030_live-rerun-resilience.json" --dry-run
```
Expected: prints a line like `2026-05-12 | Click pe sageata Rerun... | disable_when_unreachable | PEND | 5 cand, ...` and exits 0. `--dry-run` means HTML is not modified.

- [ ] **Step 8.5: Final commit**

```bash
cd C:/Users/ALEX/.claude/skills/consilium
git add FEEDBACK.html  # if not gitignored; if gitignored, this is a no-op
git status
# Note: FEEDBACK.md should be gone (renamed); FEEDBACK.md.bak gitignored.
git commit -m "feat(feedback-html): migrate legacy FEEDBACK.md to FEEDBACK.html" --allow-empty
```

If `FEEDBACK.html` is gitignored (per Task 7.3), the commit is empty/symbolic — that's fine, the migration left only gitignored artifacts on disk.

---

## Self-review (completed inline, fixed where needed)

**Spec coverage**: each spec section maps to tasks: §Format → Task 1+2+3; §"render_feedback_html.py" → Task 1+2+3; §"log_feedback.py" → Task 5; §"migrate_feedback_md_to_html.py" → Task 6; §"priors.py" → Task 4 (parser swap propagates via feedback.py import); §"feedback.py" → Task 4; §"SKILL.md" → Task 7; §"Data Flow" → end-to-end smoke in Task 8. ✓

**Placeholder scan**: no "TODO", "TBD", "implement later", or "appropriate" left. ✓

**Type/name consistency**: `Entry` dataclass fields used uniformly (`date`, `context`, `chosen`, `outcome`, `note`, `run_path`) across renderer, log_feedback, migrate, and tests. `parse_feedback` returns dicts (matches existing priors.py expectation). `render_drill(run, chosen_id)` signature consistent. ✓

**Known fragility called out in plan body:** Task 5.3 notes that re-rendering on append loses drill-down for previously-logged rows (since HTML cells don't store `run_path`). The migration script populates the initial `run_path` correctly; for live appends from log_feedback we accept legacy stubs for older rows until a sidecar map is added in a future iteration. This is documented in the code comment and is consistent with §"Out of Scope" in the spec (no sidecar / no JSON-side persistence in Phase 1).

---

## Execution Handoff

Plan complete and saved to `C:\Users\ALEX\.claude\skills\consilium\docs\superpowers\plans\2026-05-12-feedback-html.md`. Two execution options:

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks, fast iteration.
2. **Inline Execution** — execute tasks in this session via `superpowers:executing-plans`, batch with checkpoints.

Which approach?
