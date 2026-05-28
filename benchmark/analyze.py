#!/usr/bin/env python3
"""
Walk workspace/<mode>/<task>/ folders, pull metrics from claude_raw.json
(written by run_task.py --auto), and emit a single static report.html.

Usage:
  python analyze.py              # writes report.html in cwd
  python analyze.py --out foo.html
"""

import argparse
import html
import json
import os
import statistics
import sys
from datetime import datetime
from pathlib import Path

BASE      = Path(__file__).parent
WORKSPACE = BASE / "workspace"

sys.path.insert(0, str(BASE / "scripts"))
from _common import MODES, TASKS  # noqa: E402  — single source of truth

# Author's calibration of how much each task discriminates between modes.
# Kept out of the prompt files on purpose so models can't tune effort to it.
TASK_DIFFICULTY = {
    "code/01_circuit_breaker":       "Hard",
    "reasoning/01_transport_choice": "Easy",
    "reasoning/02_rule_of_three":    "Hard",
    "reasoning/03_schema_migration": "Hard",
    "reasoning/04_binary_search_bug": "Medium",
}

PROMPTS = BASE / "prompts"
SCORING = Path(
    os.environ.get("BENCHMARK_SCORING_DIR")
    or BASE.parent.parent / "Benchmark-scoring"
)  # external sibling repo, never reachable by the benchmarked subprocess


def fmt_ms(ms):
    if not ms:
        return "—"
    s = ms / 1000
    m, sec = divmod(s, 60)
    return f"{int(m)}m{sec:04.1f}s" if m else f"{sec:.1f}s"


def detect_broken(data, usage):
    """Detect hook interception / false-start runs.

    Calibrated against observed signals:
      - Hook ack (consilium SessionStart): turns=1, in=3, out=304
      - Real opus reasoning task:          turns=1, in=6, out=1233+

    The discriminator is OUTPUT size — a real task produces >500 tokens
    even on a one-shot reasoning answer. The signature is the conjunction
    of (low input ∧ low output ∧ single turn), not any one alone.
    """
    result_text = (data.get("result") or "").lstrip()
    in_tok = usage.get("input_tokens", 0) or 0
    out_tok = usage.get("output_tokens", 0) or 0
    turns = data.get("num_turns", 0) or 0
    if result_text.startswith("Understood. I'll proceed directly"):
        return True
    if turns <= 1 and in_tok < 10 and out_tok < 500:
        return True
    return False


def load_verify(d):
    """Read verify/report.json. Returns (state, score, max_score, raw).

    `raw` is the full verifier report so per-kind details can be rendered
    in the collapsible cell section (extracted answer, test counts, etc.)
    without re-parsing the file."""
    vp = d / "verify" / "report.json"
    if not vp.exists():
        return "UNVERIFIED", None, None, None
    try:
        v = json.loads(vp.read_text(encoding="utf-8"))
    except Exception:
        return "UNVERIFIED", None, None, None
    score = v.get("score")
    max_score = v.get("max_score")
    state = "OK" if v.get("ok") else "FAIL"
    return state, score, max_score, v


def load_audit(workspace_dir):
    """Read behavior_audit.json; return (verdict, summary) or ('-', '-')."""
    p = workspace_dir / "behavior_audit.json"
    if not p.exists():
        return "-", "-"
    try:
        a = json.loads(p.read_text(encoding="utf-8"))
        return a.get("verdict", "-"), a.get("summary", "-")
    except Exception:
        return "-", "-"


def load_pipeline(workspace_dir):
    """Read pipeline_audit.json; return report_detected (True/False/None).

    Written only for consilium_* runs (see run_task.detect_pipeline_execution).
    None = non-consilium mode or legacy run with no pipeline_audit.json → no badge.
    False = a consilium run that answered directly without a runs/ report path.
    True = response contained a runs/ path (proxy for pipeline execution).

    Field name: `report_detected` (renamed from `pipeline_executed` 2026-05-28 to
    disambiguate from runs/<file>.json `pipeline_executed` deliberation-quality gate).
    Fallback to old name for legacy files written before the rename.
    """
    p = workspace_dir / "pipeline_audit.json"
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data.get("report_detected", data.get("pipeline_executed"))
    except Exception:
        return None


def load_trias_parallelism(workspace_dir):
    """Return (serial_dispatch, ratio) from pipeline_audit.json or (None, None).

    serial_dispatch True  = Trias dispatched 3 personalities sequentially (api/wall < 1.5).
    serial_dispatch False = parallel evidence (ratio >= 1.5) OR scale_down (no dispatch).
    None = field absent (non-Trias mode, raw missing, or pre-2026-05-28 run).
    See benchmark/scripts/check_trias_parallelism.py for the contract.
    """
    p = workspace_dir / "pipeline_audit.json"
    if not p.exists():
        return None, None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data.get("trias_serial_dispatch"), data.get("trias_parallel_ratio")
    except Exception:
        return None, None


def _load_one_run(d):
    """Read one workspace directory; return metrics dict or None."""
    raw = d / "claude_raw.json"
    verify_state, verify_score, verify_max, verify_raw = load_verify(d)
    audit_verdict, audit_summary = load_audit(d)
    pipeline_executed = load_pipeline(d)
    trias_serial, trias_ratio = load_trias_parallelism(d)

    if not raw.exists():
        # No API data — surface only if verify data is present.
        if verify_state == "UNVERIFIED":
            return None
        return {
            "cost": None, "api_ms": None, "wall_ms": None,
            "turns": None, "input": None, "output": None,
            "cache_read": None, "cache_write": None,
            "model": "—", "halted": False, "subtype": "incomplete",
            "broken": False,
            "verify_state": verify_state, "verify_score": verify_score,
            "verify_max": verify_max, "verify_raw": verify_raw,
            "audit_verdict": audit_verdict, "audit_summary": audit_summary,
            "pipeline_executed": pipeline_executed,
            "trias_serial_dispatch": trias_serial,
            "trias_parallel_ratio": trias_ratio,
        }

    try:
        data = json.loads(raw.read_text(encoding="utf-8"))
    except Exception:
        return None
    u = data.get("usage", {}) or {}
    subtype = data.get("subtype", "")
    halted = bool(data.get("is_error")) or (subtype and subtype != "success")
    broken = detect_broken(data, u)
    # Top-level "model" is absent for non-bare modes; the real model surfaces
    # only under "modelUsage". Pick the highest-token entry there as a
    # tiebreak when multiple appear (mid-run model switches).
    model = data.get("model")
    if not model:
        usage_map = data.get("modelUsage") or {}
        if usage_map:
            model = max(
                usage_map.items(),
                key=lambda kv: (kv[1] or {}).get("inputTokens", 0)
                              + (kv[1] or {}).get("outputTokens", 0),
            )[0]
    return {
        "cost":          data.get("total_cost_usd", 0.0),
        "api_ms":        data.get("duration_api_ms", 0),
        "wall_ms":       data.get("duration_ms", 0),
        "turns":         data.get("num_turns", 0),
        "input":         u.get("input_tokens", 0),
        "output":        u.get("output_tokens", 0),
        "cache_read":    u.get("cache_read_input_tokens", 0),
        "cache_write":   u.get("cache_creation_input_tokens", 0),
        "model":         model or "—",
        "halted":        halted,
        "subtype":       subtype,
        "broken":        broken,
        "verify_state":  verify_state,
        "verify_score":  verify_score,
        "verify_max":    verify_max,
        "verify_raw":    verify_raw,
        "audit_verdict": audit_verdict,
        "audit_summary": audit_summary,
        "pipeline_executed": pipeline_executed,
        "trias_serial_dispatch": trias_serial,
        "trias_parallel_ratio": trias_ratio,
    }


def load_run(mode, task):
    """Return metrics for one cell, aggregating any replicate runs.

    Looks at:
      - WORKSPACE/<mode>/<task>/claude_raw.json    (the n=1 default slot)
      - WORKSPACE/<mode>/<task>/rep_<N>/claude_raw.json  (--rep N replicates)

    If multiple runs exist, returns the median run (by proxy_score, after
    quality gate). The returned dict carries a `replicates` field with the
    full per-run list so cell rendering can surface n + range.
    """
    base = WORKSPACE / mode / task
    runs = []
    main = _load_one_run(base)
    if main is not None:
        runs.append(main)
    if base.exists():
        for sub in sorted(base.iterdir()):
            if sub.is_dir() and sub.name.startswith("rep_"):
                r = _load_one_run(sub)
                if r is not None:
                    runs.append(r)
    if not runs:
        return None
    if len(runs) == 1:
        return runs[0]

    # Multiple replicates: pick the median by proxy_score (None scores
    # sort to the bottom). The returned dict is the median run's metrics
    # with a `replicates` attachment carrying the per-run breakdown so
    # the cell can render "n=K · range L-H".
    scored = [(proxy_score(r), r) for r in runs]
    scored.sort(key=lambda kv: (kv[0] is None, kv[0]))
    mid = scored[(len(scored) - 1) // 2][1]
    mid = dict(mid)  # avoid mutating the cached dict
    mid["replicates"] = [{"proxy": s, "cost": r["cost"], "api_ms": r["api_ms"]}
                         for s, r in scored]
    return mid


# Cost/speed caps anchor the /25 components. Calibrated at 50% of the
# per-task budget cap ($3 → $1.50) and 67% of the wall-clock cap (900s → 600s).
# This keeps all modes in the scoring range while preserving signal across the
# observed cost spread ($0.14–$1.15). The previous tighter caps ($0.50/120s)
# clipped all deliberation modes to 0 on both components — no signal.
# Scores are NOT comparable across harness versions if these caps are changed.
COST_CAP = 1.50
SPEED_CAP_SEC = 600


def proxy_breakdown(r):
    """Return scoring components for a run, or None.

    Formula: quality (0-50) + cost (0-25) + speed (0-25).
    cost/speed are only awarded when quality > 0 (correct answer required).
    cost/speed are omitted (0) when usage data is unavailable (incomplete runs).
    Cheat/broken/halted → all zero.
    """
    if r is None:
        return None
    if r.get("audit_verdict") == "cheat":
        return {"quality": 0.0, "cost": 0.0, "speed": 0.0}
    if r["broken"] or r["halted"]:
        return {"quality": 0.0, "cost": 0.0, "speed": 0.0}

    v_score = r.get("verify_score")
    v_max = r.get("verify_max")
    qual = (50.0 * v_score / v_max) if (v_score is not None and v_max) else 0.0

    if qual > 0 and r.get("cost") is not None and r.get("api_ms") is not None:
        cost = max(0.0, 25 * (1 - r["cost"] / COST_CAP))
        secs = (r["api_ms"] or 0) / 1000
        speed = max(0.0, 25 * (1 - secs / SPEED_CAP_SEC))
    else:
        cost = 0.0
        speed = 0.0
    return {"quality": qual, "cost": cost, "speed": speed}


def efficiency_score(r):
    """(60 / cost_usd) × (1 / turns) for runs that passed verification.

    Returns None for halted, broken, unverified, or missing-data runs.
    Raw value is unnormalized — callers normalize per-task to 0–100.
    """
    if r is None or r.get("broken") or r.get("halted"):
        return None
    if r.get("verify_state") != "OK":
        return None
    cost = r.get("cost")
    turns = r.get("turns")
    if not cost or not turns:
        return None
    return (60.0 / cost) * (1.0 / turns)


def proxy_score(r):
    """Aggregate proxy 0-100, or None when the proxy is meaningless.

    Returns None when a run completed cleanly but scored zero quality
    (cost+speed alone would produce a misleading rank for a wrong answer).
    """
    b = proxy_breakdown(r)
    if b is None:
        return None
    if not (r["broken"] or r["halted"]) and b["quality"] == 0:
        return None
    return round(sum(b.values()))


def verify_html(r):
    """Verify state line — short, rendered near the top of the cell."""
    state = r.get("verify_state", "UNVERIFIED")
    if state == "UNVERIFIED":
        return '<div class="verify verify-unk">verify: —</div>'
    score = r.get("verify_score")
    mx = r.get("verify_max")
    label = f"{score}/{mx}" if score is not None and mx is not None else state
    css = "verify-ok" if state == "OK" else "verify-fail"
    return f'<div class="verify {css}">verify: {state} ({label})</div>'


def judge_rationale_html(r):
    """Collapsible per-cell details, rendered for every verified run.

    Label and body adapt to verifier kind:
      llm_judge      → "judge rationale": sub-scores + judge summary
      closed_answer  → "verify details": extracted answer, expected, motivation
      pytest         → "verify details": passed/total + failure reason on FAIL
      cpp_self_tests → "verify details": passed/total + returncode on FAIL
    """
    raw = r.get("verify_raw") or {}
    kind = raw.get("kind")
    if not kind:
        return ""

    sub_line = ""
    summary_line = ""

    if kind == "llm_judge":
        label = "judge rationale"
        scores = raw.get("scores")
        if isinstance(scores, dict) and scores:
            sub_parts = " · ".join(f"{k} {v}" for k, v in scores.items())
            sub_line = f'<div class="judge-sub">{html.escape(sub_parts)}</div>'
        text = raw.get("summary") or raw.get("reason")
        if text:
            summary_line = f'<div class="judge-summary">{html.escape(text)}</div>'

    elif kind == "closed_answer":
        label = "verify details"
        extracted = raw.get("extracted")
        expected = raw.get("expected")
        bits = []
        if extracted or expected:
            bits.append(f"picked {extracted or '—'} · expected {expected or '—'}")
        if "value_extracted" in raw:
            v = raw.get("value_extracted")
            bucket = raw.get("value_bucket") or "—"
            bits.append(f"value {v} ({bucket})")
        if bits:
            sub_line = f'<div class="judge-sub">{html.escape(" · ".join(bits))}</div>'
        text = raw.get("motivation") or raw.get("reason")
        if text:
            summary_line = f'<div class="judge-summary">{html.escape(text)}</div>'

    elif kind in ("pytest", "cpp_self_tests"):
        label = "verify details"
        passed = raw.get("passed")
        total = raw.get("total")
        rc = raw.get("returncode")
        bits = []
        if passed is not None and total is not None:
            bits.append(f"{passed}/{total} tests passed")
        if rc is not None:
            bits.append(f"rc={rc}")
        if bits:
            sub_line = f'<div class="judge-sub">{html.escape(" · ".join(bits))}</div>'
        text = raw.get("reason")
        if text:
            summary_line = f'<div class="judge-summary">{html.escape(text)}</div>'

    else:
        label = "verify details"
        text = raw.get("summary") or raw.get("reason")
        if text:
            summary_line = f'<div class="judge-summary">{html.escape(text)}</div>'

    if not sub_line and not summary_line:
        return ""

    return (
        f'<details class="judge"><summary>{label}</summary>'
        f'{sub_line}{summary_line}'
        f'</details>'
    )


def breakdown_html(r):
    """Per-component score breakdown rendered as letter-prefixed values.
    Letters match the legend below the table."""
    b = proxy_breakdown(r)
    if b is None:
        return ""
    # "—" only when data is absent (incomplete run); "0.0" when cap is exceeded
    cost_str  = f'{b["cost"]:.1f}'  if r.get("cost")   is not None else "—"
    speed_str = f'{b["speed"]:.1f}' if r.get("api_ms") is not None else "—"
    return (
        '<div class="breakdown">'
        f'<span title="quality (max 50)">Q {b["quality"]:.1f}</span>'
        ' · '
        f'<span title="cost (max 25)">$ {cost_str}</span>'
        ' · '
        f'<span title="speed (max 25)">⏱ {speed_str}</span>'
        '</div>'
    )


def audit_html(r):
    """Render the behavior-audit badge for a cell.

    `cheat` (red) = the model successfully read an answer-key file.
    `searched` (amber) = the model probed for scoring but all lookups
    returned empty/denied. `computed` (green) = no scoring access detected.
    `-` (grey) = no audit data (legacy run).
    """
    verdict = r.get("audit_verdict", "-")
    summary = r.get("audit_summary", "-")
    css = {
        "computed": "audit-ok",
        "searched": "audit-warn",
        "cheat":    "audit-bad",
    }.get(verdict, "audit-unk")
    title = html.escape(summary)
    label = verdict if verdict != "-" else "audit: —"
    return f'<div class="audit {css}" title="{title}">behavior: {label}</div>'


def pipeline_html(r):
    """Render the pipeline-execution badge for a consilium_* cell.

    `deliberated` (green) = the run wrote a .consilium/runs/ report (the 8-step
    pipeline actually ran). `pipeline-skipped` (amber) = a consilium run that
    answered directly with no report — bare-Sonnet-equivalent, NOT a real
    deliberation (the 2026-05-26 audit gap). None = non-consilium mode or legacy
    run → no badge. Makes the bare-vs-Consilium distinction visible in the report.
    """
    status = r.get("pipeline_executed")
    if status is None:
        return ""
    if status:
        return ('<div class="pipe pipe-ok" title="wrote a .consilium/runs/ report — '
                'the deliberation pipeline ran">pipeline: deliberated</div>')
    return ('<div class="pipe pipe-warn" title="no runs/ report written — answered '
            'directly, bare-Sonnet-equivalent, not a real deliberation">'
            'pipeline: skipped</div>')


def trias_parallelism_html(r):
    """Render the Trias parallelism badge.

    serial_dispatch True → red badge with measured ratio (spec drift — personalities
    dispatched sequentially despite modes/trias.md Step 3 mandating parallel).
    serial_dispatch False on real deliberation → green badge (parallel evidence).
    None or scale_down → no badge.
    """
    serial = r.get("trias_serial_dispatch")
    ratio = r.get("trias_parallel_ratio")
    if serial is None or ratio is None:
        return ""
    if serial is True:
        return (f'<div class="pipe pipe-warn" title="api/wall ratio {ratio:.2f}x < 1.5 — '
                f'Trias dispatched personalities sequentially, not in parallel '
                f'(spec drift vs modes/trias.md Step 3)">'
                f'⚠ trias: serial dispatch ({ratio:.2f}x)</div>')
    # serial == False on real deliberation → parallel evidence (ratio >= 1.5).
    # Skip badge for scale_down (no dispatch to evaluate).
    if r.get("turns") and r["turns"] > 4:
        return (f'<div class="pipe pipe-ok" title="api/wall ratio {ratio:.2f}x ≥ 1.5 — '
                f'Trias personalities dispatched in parallel">'
                f'trias: parallel ({ratio:.2f}x)</div>')
    return ""


def _replicates_html(r):
    """Render 'n=K · p L-H · $σ X.XX' line when the cell aggregates >1 runs."""
    reps = r.get("replicates")
    if not reps or len(reps) < 2:
        return ""
    proxies = [p for p, *_ in [(x["proxy"],) for x in reps] if p is not None]
    if proxies:
        lo, hi = min(proxies), max(proxies)
        spread = f"p {lo}-{hi}" if lo != hi else f"p {lo}"
    else:
        spread = "p —"
    costs = [x["cost"] for x in reps if x.get("cost") is not None]
    cost_sigma = f" · $σ {statistics.stdev(costs):.3f}" if len(costs) >= 2 else ""
    return f'<div class="meta reps">n={len(reps)} · {spread}{cost_sigma}</div>'


def cell_html(r, rank=None):
    """Render a cell. `rank` ∈ {None, 'best', 'worst'} colors the background
    relative to other modes on the same task."""
    if r is None:
        return '<td class="missing">—</td>'
    cost = f"${r['cost']:.3f}" if r['cost'] is not None else "$—"

    # All abbreviations explained in the legend below the table.
    meta_time  = f'<div class="meta">t {fmt_ms(r["api_ms"])} · n {r["turns"] or "—"}</div>'
    meta_tok   = f'<div class="meta">i {r["input"] or "—"} · o {r["output"] or "—"}</div>'
    meta_cache = f'<div class="meta">CR {r.get("cache_read") or "—"} · CW {r.get("cache_write") or "—"}</div>'
    reps_line = _replicates_html(r)

    if r["broken"]:
        return (
            f'<td class="broken">'
            f'<div class="score score-bad">BROKEN</div>'
            f'<div class="halt">⚠ hook interception / false start</div>'
            f'<div class="cost">$ {cost[1:]}</div>'
            f'{meta_time}'
            f'{meta_tok}'
            f'{meta_cache}'
            f'</td>'
        )

    if r.get("audit_verdict") == "cheat":
        return (
            f'<td class="cheat">'
            f'<div class="score score-bad">VOID</div>'
            f'<div class="halt">!! CHEAT — score voided</div>'
            f'<div class="cost">$ {cost[1:]}</div>'
            f'{meta_time}'
            f'{meta_tok}'
            f'{meta_cache}'
            f'{verify_html(r)}'
            f'{audit_html(r)}'
            f'{judge_rationale_html(r)}'
            f'</td>'
        )

    base_klass = "halted" if r["halted"] else "ok"
    rank_klass = f" rank-{rank}" if rank else ""
    raw_score = proxy_score(r)
    if raw_score is None:
        score_html = (
            '<div class="score score-bad">—</div>'
            '<div class="halt">quality gate: verify did not pass</div>'
        )
    else:
        cls_score = "score-bad" if raw_score < 40 else "score-ok" if raw_score < 70 else "score-good"
        score_html = f'<div class="score {cls_score}">{raw_score}</div>'
    halt = f'<div class="halt">⚠ {html.escape(r["subtype"])}</div>' if r["halted"] else ""
    return (
        f'<td class="{base_klass}{rank_klass}">'
        f'{score_html}'
        f'{reps_line}'
        f'{breakdown_html(r)}'
        f'<div class="cost">$ {cost[1:]}</div>'
        f'{meta_time}'
        f'{meta_tok}'
        f'{meta_cache}'
        f'{verify_html(r)}'
        f'{audit_html(r)}'
        f'{pipeline_html(r)}'
        f'{trias_parallelism_html(r)}'
        f'{halt}'
        f'{judge_rationale_html(r)}'
        f'</td>'
    )


CSS = """
* { box-sizing: border-box; }
body { font: 13px/1.4 -apple-system, Segoe UI, Roboto, sans-serif;
       background: #0e1116; color: #e6edf3; margin: 0; padding: 24px; }
h1 { margin: 0 0 4px; font-size: 22px; }
.sub { color: #8b949e; margin-bottom: 8px; font-size: 12px; }
.caveat { background: #2d2611; border: 1px solid #6b5917; color: #e6d99a;
          padding: 10px 14px; border-radius: 6px; font-size: 12px;
          line-height: 1.5; margin-bottom: 18px; }
.caveat code { background: #1a1608; padding: 1px 5px; border-radius: 3px;
               color: #f7e89a; }
table { border-collapse: separate; border-spacing: 4px; width: 100%;
        table-layout: fixed; }
th { text-align: left; color: #8b949e; font-weight: 500; padding: 6px 10px;
     background: #161b22; border-radius: 4px; font-size: 11px;
     text-transform: uppercase; letter-spacing: 0.04em;
     overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.mode-model { color: #79c0ff; font-weight: 400; text-transform: lowercase;
              letter-spacing: 0; }
td { background: #161b22; padding: 10px; border-radius: 6px; vertical-align: top;
     min-width: 130px; overflow-wrap: anywhere; word-break: break-word; }
td.missing { color: #4a5160; text-align: center; font-size: 16px; }
td.halted { background: #2d1418; }
td.cheat  { background: #3a0d12; border: 1px solid #f85149; }
td.broken { background: #3a1622; border: 1px solid #f85149; }
td.rank-best  { background: #14331c; border: 1px solid #2ea043; }
td.rank-worst { background: #3a1a1f; border: 1px solid #b62324; }
.verify { font-size: 10px; margin-top: 4px; font-weight: 600; }
.verify-ok   { color: #3fb950; }
.verify-fail { color: #f85149; }
.verify-unk  { color: #6e7681; }
.breakdown { color: #8b949e; font-size: 10px; font-weight: 500;
             margin-top: -2px; margin-bottom: 4px;
             font-family: ui-monospace, "Cascadia Code", Consolas, monospace; }
.breakdown span { color: #c9d1d9; }
.reps { color: #d2a8ff; font-size: 10px; font-weight: 600;
        margin-top: -2px; margin-bottom: 2px; }
.judge { margin-top: 8px; padding-top: 6px;
         border-top: 1px dashed #30363d; }
.judge > summary { cursor: pointer; color: #8b949e; font-size: 10px;
                   font-weight: 500; outline: none; user-select: none; }
.judge > summary:hover { color: #c9d1d9; }
.judge[open] > summary { color: #c9d1d9; margin-bottom: 4px; }
.judge-sub { color: #79c0ff; font-size: 10px; font-weight: 600;
             margin-bottom: 4px; }
.judge-summary { color: #c9d1d9; font-size: 10px; line-height: 1.4;
                 font-weight: 400; white-space: normal;
                 overflow-wrap: anywhere; word-break: normal;
                 hyphens: auto; }
.audit       { font-size: 11px; margin-top: 4px; cursor: help; }
.audit-ok    { color: #3fb950; }
.audit-warn  { color: #d29922; }
.audit-bad   { color: #f85149; font-weight: 600; }
.audit-unk   { color: #6e7681; }
.pipe        { font-size: 11px; margin-top: 4px; cursor: help; }
.pipe-ok     { color: #3fb950; }
.pipe-warn   { color: #d29922; font-weight: 600; }
.task { font-weight: 600; color: #c9d1d9; background: #1c232b !important; }
.score { font-size: 22px; font-weight: 700; line-height: 1; margin-bottom: 4px; }
.score-good { color: #3fb950; }
.score-ok   { color: #d29922; }
.score-bad  { color: #f85149; }
.cost { color: #79c0ff; font-weight: 600; font-size: 13px; }
.meta { color: #8b949e; font-size: 11px; }
.halt { color: #f85149; font-size: 10px; margin-top: 4px; font-weight: 600; }
.legend { color: #8b949e; font-size: 11px; margin-top: 18px; line-height: 1.6; }
.legend code { background: #161b22; padding: 2px 5px; border-radius: 3px; color: #c9d1d9; }
.totals { margin-top: 20px; }
.totals td { font-weight: 600; }
.problems { margin-top: 36px; }
.problems h2 { font-size: 16px; color: #c9d1d9; margin: 0 0 12px;
               border-bottom: 1px solid #21262d; padding-bottom: 6px; }
.problems details { background: #161b22; border-radius: 6px; padding: 10px 14px;
                    margin-bottom: 8px; border: 1px solid #21262d; }
.problems details[open] { background: #1c232b; }
.problems summary { cursor: pointer; color: #79c0ff; font-weight: 600;
                    font-size: 13px; outline: none; }
.problems summary:hover { color: #a5d6ff; }
.problems .difficulty { display: inline-block; margin-left: 8px;
                        padding: 1px 7px; border-radius: 10px;
                        font-size: 10px; font-weight: 700;
                        text-transform: uppercase; letter-spacing: 0.05em;
                        vertical-align: middle; }
.problems .difficulty-easy   { background: #1a3a1f; color: #3fb950; }
.problems .difficulty-medium { background: #3a2f0e; color: #d29922; }
.problems .difficulty-hard   { background: #3a1622; color: #f85149; }
.problems .missing-prompt { color: #f85149; font-size: 11px; font-style: italic; }
.problems pre { white-space: pre-wrap; word-wrap: break-word;
                font: 12px/1.5 ui-monospace, "Cascadia Code", Consolas, monospace;
                color: #c9d1d9; margin: 10px 0 0; padding: 10px;
                background: #0e1116; border-radius: 4px;
                border-left: 2px solid #30363d; }
.problems details details { margin-top: 10px; background: #0e1116;
                            border-left: 2px solid #d29922;
                            border-radius: 0 4px 4px 0; padding: 8px 12px; }
.problems details details summary { color: #d29922; font-size: 12px;
                                    text-transform: uppercase;
                                    letter-spacing: 0.05em; }
.problems details details pre { border-left: none; background: transparent;
                                padding: 6px 0 0; }
"""


def build_html(rows):
    parts = ['<!doctype html><html><head><meta charset="utf-8">',
             '<title>Benchmark report</title><style>', CSS, '</style></head><body>']
    parts.append('<h1>Benchmark — modes × tasks</h1>')
    parts.append(f'<div class="sub">Generated {datetime.now():%Y-%m-%d %H:%M}. '
                 'Score is an automatic proxy: 50 quality + 25 cost + 25 speed (cost &amp; speed only awarded when quality &gt; 0).</div>')
    parts.append(
        '<div class="caveat">'
        '<strong>Exploratory ranking — n=1 per cell by default.</strong> '
        'Treat differences smaller than <code>~20pp</code> as noise; the order of close cells '
        'is not stable across reruns. To collect replicates on Hard tasks, '
        'add <code>--rep 2</code>, <code>--rep 3</code>, ... to your run; the cell '
        'will switch to the median and surface <code>n=K · p L-H</code>. '
        '<code>cost</code> and <code>speed</code> caps are '
        '<strong>arbitrary anchors</strong> set to the within-batch p95, '
        'so scores are NOT comparable across harness versions or across runs of different mode sets. '
        'Cells render <code>—</code> when the run completed but did not '
        'pass verification (no quality → proxy is meaningless).'
        '</div>')

    # Header — include the model family (opus/sonnet/haiku) used by each
    # mode, extracted from the first available run's claude_raw.json.
    def _model_family(mode):
        for t in TASKS:
            r = rows.get((mode, t))
            if r and r.get("model"):
                model_lc = r["model"].lower()
                for fam in ("opus", "sonnet", "haiku"):
                    if fam in model_lc:
                        return fam
                return r["model"]
        return None

    parts.append('<table><thead><tr><th>Task</th>')
    for m in MODES:
        fam = _model_family(m)
        suffix = f' <span class="mode-model">({html.escape(fam)})</span>' if fam else ''
        parts.append(f'<th>{html.escape(m)}{suffix}</th>')
    parts.append('</tr></thead><tbody>')

    # Per-task rows + collect totals
    n_tasks = len(TASKS)
    totals = {m: {"cost": 0.0,
                  "score": [], "broken": 0,
                  "exhausted": 0, "crashed": 0, "quality_gated": 0,
                  "runs": 0, "verified_ok": 0, "verify_fail": 0,
                  "cost_completed": 0.0}
              for m in MODES}
    for task in TASKS:
        # Rank cells by proxy score, ignoring BROKEN/cheat (already red-flagged).
        eligible = {}
        for m in MODES:
            r = rows.get((m, task))
            if r is None or r["broken"] or r.get("audit_verdict") == "cheat":
                continue
            # Pipeline-skipped consilium runs answered as bare Sonnet (no
            # deliberation). Crowning such a cell "best" would credit Consilium
            # for work it did not do — exclude from the per-task ranking. The
            # cell still renders (with its pipeline:skipped badge) and still
            # counts toward cost/run totals; it just cannot win/lose as a
            # deliberation result. (Senate 2026-05-26 rec#1.)
            if r.get("pipeline_executed") is False:
                continue
            sc = proxy_score(r)
            if sc is not None:
                eligible[m] = sc
        rank_by_mode = {}
        if len(eligible) >= 2:
            top = max(eligible.values())
            bot = min(eligible.values())
            if top != bot:
                for m, sc in eligible.items():
                    if sc == top:
                        rank_by_mode[m] = "best"
                    elif sc == bot:
                        rank_by_mode[m] = "worst"

        parts.append(f'<tr><td class="task">{html.escape(task)}</td>')
        for m in MODES:
            r = rows.get((m, task))
            parts.append(cell_html(r, rank_by_mode.get(m)))
            if r is not None:
                totals[m]["cost"] += r["cost"] or 0.0
                totals[m]["runs"] += 1
                if r["broken"]:
                    totals[m]["broken"] += 1
                elif r["halted"]:
                    # Bucket halts: budget/timeout caps tell us about
                    # mode overhead, not task competence — keep them
                    # visible but separate from crashes.
                    sub = r.get("subtype", "")
                    if sub in ("error_max_budget_usd", "error_max_duration",
                               "error_max_turns"):
                        totals[m]["exhausted"] += 1
                    else:
                        totals[m]["crashed"] += 1
                else:
                    if r.get("verify_state") == "OK":
                        totals[m]["verified_ok"] += 1
                        totals[m]["cost_completed"] += r["cost"] or 0.0
                    elif r.get("verify_state") == "FAIL":
                        totals[m]["verify_fail"] += 1
                    sc = proxy_score(r)
                    if sc is not None:
                        totals[m]["score"].append(sc)
                    else:
                        # Completed cleanly but quality-gated (verify
                        # failed or unverified); proxy is None.
                        totals[m]["quality_gated"] += 1
        parts.append('</tr>')

    # Totals row
    parts.append('<tr class="totals"><td class="task">TOTAL</td>')
    for m in MODES:
        t = totals[m]
        avg = round(sum(t["score"]) / len(t["score"])) if t["score"] else "—"
        cpc = (f'${t["cost_completed"] / t["verified_ok"]:.3f}'
               if t["verified_ok"] else "—")
        completed_cls = "score-good" if t["verified_ok"] >= 4 else \
                        "score-ok"   if t["verified_ok"] >= 2 else "score-bad"
        # Distinct buckets: exhausted (mode-overhead signal) vs crashed
        # (infra signal) vs verify_fail (model signal). Lumping them
        # under one 'halted' count hides which one is failing.
        flags = []
        if t["broken"]:        flags.append(f'{t["broken"]} broken')
        if t["exhausted"]:     flags.append(f'{t["exhausted"]} budget/timeout')
        if t["crashed"]:       flags.append(f'{t["crashed"]} crashed')
        if t["verify_fail"]:   flags.append(f'{t["verify_fail"]} verify-fail')
        if t["quality_gated"]: flags.append(f'{t["quality_gated"]} gated')
        flag_line = (f'<div class="meta">{" · ".join(flags)}</div>'
                     if flags else "")
        parts.append(
            f'<td>'
            f'<div class="score {completed_cls}">{t["verified_ok"]}/{n_tasks}</div>'
            f'<div class="meta">verified complete</div>'
            f'<div class="cost">${t["cost"]:.2f} total</div>'
            f'<div class="meta">{cpc} per verified</div>'
            f'<div class="meta">avg proxy {avg}</div>'
            f'{flag_line}'
            f'</td>'
        )
    parts.append('</tr>')

    parts.append('</tbody></table>')

    parts.append(
        '<div class="legend">'
        '<strong>Cell legend</strong> (top→bottom):<br>'
        '&nbsp;&nbsp;<code>score</code> — proxy 0–100 (integer), sum of the four components below. '
        'Rendered as <code>—</code> when the run completed cleanly but did not pass verification: '
        'without a quality signal, the cost+speed-only sum is misleading, so no proxy is emitted.<br>'
        '&nbsp;&nbsp;<code>n=K · p L-H · $σ X.XX</code> — replicate aggregation when '
        '<code>--rep N</code> was used: K runs found at this cell, proxy ranges from L to H, '
        '<code>$σ</code> = sample stdev of <code>total_cost_usd</code> across reps. '
        'The displayed <code>score</code> is the median. High <code>$σ</code> typically '
        'reflects agent stochasticity (different reasoning paths → different turn counts), '
        'not cache instability — confirm by inspecting <code>CR</code> spread.<br>'
        '&nbsp;&nbsp;<code>Q · $ · ⏱</code> — score breakdown:<br>'
        '&nbsp;&nbsp;&nbsp;&nbsp;<code>Q</code> = quality (max 50; scales linearly with verifier score)<br>'
        f'&nbsp;&nbsp;&nbsp;&nbsp;<code>$</code> = cost (max 25; linear $0 → 25, ${COST_CAP:.2f} → 0; '
        'only awarded when Q &gt; 0; calibrated on observed p95)<br>'
        f'&nbsp;&nbsp;&nbsp;&nbsp;<code>⏱</code> = speed (max 25; linear 0s → 25, {SPEED_CAP_SEC}s → 0; '
        'only awarded when Q &gt; 0; calibrated on observed p95)<br>'
        '&nbsp;&nbsp;<code>$ X.XXX</code> — actual USD billed by the API.<br>'
        '&nbsp;&nbsp;<code>t Xs · n Xt</code> — '
        '<code>t</code> = total API time (sum of model latency across the run); '
        '<code>n</code> = number of agent turns. One turn = one full cycle where the model '
        'emits a response (possibly with tool calls), waits for tool results, then decides what to do next. '
        '<code>n=1</code> means the model answered in one shot with no tools. Higher <code>n</code> '
        'indicates the model iterated — read files, ran commands, then incorporated the results.<br>'
        '&nbsp;&nbsp;<code>i X · o X</code> — <code>i</code> = non-cached input tokens this run, <code>o</code> = output tokens.<br>'
        '&nbsp;&nbsp;<code>CR X · CW X</code> — <code>CR</code> = cache-read tokens (served from Anthropic prompt cache, ~10% of input price), <code>CW</code> = cache-write tokens (added to cache this run). The Claude Code system prompt (~30K tokens) reads from cache on every <code>claude -p</code> invocation — a constant cost floor across modes, not a bias source. Cross-run CR variance signals real cache state change.<br>'
        '&nbsp;&nbsp;<code>verify: OK/FAIL (score/max)</code> — automatic verification result.<br>'
        '&nbsp;&nbsp;<code>behavior: computed/searched/cheat</code> — anti-cheat audit verdict.<br>'
        '&nbsp;&nbsp;<code>pipeline: deliberated/skipped</code> — consilium_* modes only. '
        '<code>deliberated</code> = the run wrote a <code>.consilium/runs/</code> report (the 8-step pipeline ran); '
        '<code>skipped</code> = the run answered directly with no report, i.e. bare-Sonnet-equivalent and NOT a real '
        'deliberation. A <code>skipped</code> cell means that mode/task pair did not exercise Consilium, '
        'so its score reflects the base model, not the deliberation process.<br>'
        '&nbsp;&nbsp;<code>▸ judge rationale</code> / <code>▸ verify details</code> — collapsible. '
        'For <code>llm_judge</code> tasks: per-criterion sub-scores + one-line summary from the judge. '
        'For other verifiers (pytest, cpp_self_tests, closed_answer): shown only on failure, '
        'contains the verifier\'s reason (e.g. <em>solution.py not found</em>).<br>'
        '<br><strong>Per-row highlight:</strong> '
        '<span style="background:#14331c;border:1px solid #2ea043;padding:1px 6px;border-radius:3px">best</span> '
        'and <span style="background:#3a1a1f;border:1px solid #b62324;padding:1px 6px;border-radius:3px">worst</span> '
        'mode by proxy score (BROKEN/cheat cells excluded from the ranking).<br>'
        '<strong>BROKEN</strong> = run intercepted by SessionStart hook or false-start '
        '(num_turns≤1 with input&lt;10 tokens, or output starts with hook ack).<br>'
        f'<strong>TOTAL row:</strong> <code>N/{n_tasks} verified complete</code> + average <code>$ per verified</code>.<br>'
        '<strong>Empty cell</strong> = no run recorded yet (no <code>claude_raw.json</code> in workspace).'
        '</div>'
    )

    # Efficiency table — (60/cost) × (1/turns), normalized per-task to 100.
    # Only verified-OK runs are included; modes without a passing run show "—".
    parts.append('<h2 style="font-size:16px;color:#c9d1d9;margin:28px 0 10px;'
                 'border-bottom:1px solid #21262d;padding-bottom:6px;">'
                 'Efficiency — (60/cost) × (1/turns), normalized per task (best=100, verified runs only)</h2>')
    parts.append('<table><thead><tr><th>Task</th>')
    for m in MODES:
        parts.append(f'<th>{html.escape(m)}</th>')
    parts.append('</tr></thead><tbody>')
    for task in TASKS:
        raw = {m: efficiency_score(rows.get((m, task))) for m in MODES}
        best = max((v for v in raw.values() if v is not None), default=None)
        parts.append(f'<tr><td class="task">{html.escape(task)}</td>')
        for m in MODES:
            v = raw[m]
            if v is None or best is None:
                parts.append('<td class="missing">—</td>')
            else:
                norm = round(100 * v / best)
                r = rows.get((m, task))
                cost_s = f"${r['cost']:.3f}" if r and r.get('cost') else ""
                turns_s = f"n{r['turns']}" if r and r.get('turns') else ""
                bar_w = max(2, norm)
                bar = (f'<div style="height:4px;width:{bar_w}%;'
                       f'background:#2ea043;border-radius:2px;margin-top:4px"></div>')
                cls = "score-good" if norm >= 70 else "score-ok" if norm >= 40 else "score-bad"
                parts.append(
                    f'<td>'
                    f'<span class="score {cls}" style="font-size:18px">{norm}</span>'
                    f'{bar}'
                    f'<div class="meta">{cost_s} · {turns_s}</div>'
                    f'</td>'
                )
        parts.append('</tr>')
    parts.append('</tbody></table>')

    # Problems summary — each task's prompt, collapsed by default.
    parts.append('<div class="problems">')
    parts.append('<h2>Problems</h2>')
    for task in TASKS:
        difficulty = TASK_DIFFICULTY.get(task)
        diff_badge = ""
        if difficulty:
            css = f"difficulty-{difficulty.lower()}"
            diff_badge = (
                f'<span class="difficulty {css}">{html.escape(difficulty)}</span>'
            )

        prompt_path = PROMPTS / f"{task}.md"
        summary = f"{html.escape(task)}{diff_badge}"

        if prompt_path.exists():
            try:
                body = prompt_path.read_text(encoding="utf-8")
            except Exception as e:
                body = f"(failed to read: {e})"
            parts.append(
                f'<details><summary>{summary}</summary>'
                f'<pre>{html.escape(body)}</pre>'
                f'</details>'
            )
        else:
            parts.append(
                f'<details><summary>{summary}</summary>'
                f'<div class="missing-prompt">prompt file not found: '
                f'prompts/{html.escape(task)}.md</div>'
                f'</details>'
            )
    parts.append('</div>')

    parts.append('</body></html>')
    return "\n".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="report.html",
                    help="Output HTML file (default: report.html)")
    args = ap.parse_args()

    rows = {}
    for m in MODES:
        for t in TASKS:
            r = load_run(m, t)
            if r is not None:
                rows[(m, t)] = r

    out = BASE / args.out
    out.write_text(build_html(rows), encoding="utf-8")
    print(f"  Found {len(rows)} run(s)")
    print(f"  Written: {out}")


if __name__ == "__main__":
    main()
