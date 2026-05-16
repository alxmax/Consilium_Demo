"""
show_senate_transcript.py — HTML transcript of a Senate deliberation bundle.
WhatsApp group chat layout. One folder per session.

CLI:
    python scripts/show_senate_transcript.py                       # latest bundle
    python scripts/show_senate_transcript.py runs/senate/<f>.json  # specific bundle
    python scripts/show_senate_transcript.py --out-dir path/       # custom output dir
    python scripts/show_senate_transcript.py --stdout              # print to stdout
"""

import argparse
import html as _html
import json
import os
import sys
from glob import glob
from pathlib import Path

# ── metadata ──────────────────────────────────────────────────────────────────

# WhatsApp-style sender colors (distinct, readable on dark)
SENATORS = {
    "wittgenstein": {"color": "#53BDEB", "init": "W", "specialty": "Semantică Operațională"},
    "aurelius":     {"color": "#8694CA", "init": "A", "specialty": "Reversibilitate × Magnitudine"},
    "confucius":    {"color": "#CCA86F", "init": "C", "specialty": "Ierarhie & Precedente"},
    "socrate":      {"color": "#3FC198", "init": "S", "specialty": "Asumpții Ascunse"},
    "musk":         {"color": "#E84545", "init": "M", "specialty": "Delete the Part You Don't Need"},
    "dimon":        {"color": "#F09800", "init": "D", "specialty": "Stress Test & Contrapartidă"},
    "napoleon":     {"color": "#4FAD50", "init": "N", "specialty": "Cost & Teren"},
}

VOTE_COLOR = {
    "GO":     ("#00a884", "#fff"),
    "MODIFY": ("#f0c429", "#000"),
    "STOP":   ("#e84545", "#fff"),
}

SENATOR_ORDER = ["wittgenstein", "aurelius", "confucius", "socrate", "musk", "dimon", "napoleon"]

# WhatsApp-style time derived from timestamp
def _time_from_ts(ts):
    # ts like "2026-05-16_220025"
    try:
        parts = ts.split("_")
        t = parts[1] if len(parts) > 1 else "0000"
        return f"{t[:2]}:{t[2:4]}"
    except Exception:
        return "00:00"

def esc(s):
    return _html.escape(str(s))


# ── CSS ───────────────────────────────────────────────────────────────────────

def _css():
    return """
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: #111b21;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
      font-size: 14.5px;
      line-height: 1.45;
      color: #e9edef;
      min-height: 100vh;
    }

    /* ── phone shell ── */
    .shell {
      max-width: 480px;
      margin: 0 auto;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      background: #0b141a;
      box-shadow: 0 0 40px #00000088;
    }

    /* ── header ── */
    .wa-header {
      background: #1f2c34;
      padding: 10px 16px;
      display: flex;
      align-items: center;
      gap: 12px;
      position: sticky;
      top: 0;
      z-index: 100;
      border-bottom: 1px solid #2a3942;
    }
    .wa-header-avatar {
      width: 40px; height: 40px; border-radius: 50%;
      background: #00a884;
      display: flex; align-items: center; justify-content: center;
      font-size: 18px; font-weight: 700; color: #fff;
      flex-shrink: 0;
    }
    .wa-header-info { flex: 1; min-width: 0; }
    .wa-header-name { font-weight: 600; font-size: 16px; color: #e9edef; }
    .wa-header-sub { font-size: 12px; color: #8696a0; }
    .wa-header-verdict {
      padding: 3px 10px; border-radius: 12px;
      font-size: 12px; font-weight: 700;
    }

    /* ── chat background ── */
    .chat-bg {
      flex: 1;
      padding: 12px 8px 20px;
      background-color: #0b141a;
      background-image:
        radial-gradient(circle, #1f2c3411 1px, transparent 1px);
      background-size: 20px 20px;
    }

    /* ── date separator ── */
    .date-sep {
      text-align: center;
      margin: 10px 0 14px;
    }
    .date-sep span {
      background: #182229;
      color: #8696a0;
      font-size: 12px;
      padding: 5px 12px;
      border-radius: 8px;
    }

    /* ── system message ── */
    .sys-msg {
      text-align: center;
      margin: 8px 0;
    }
    .sys-msg span {
      background: #182229cc;
      color: #8696a0;
      font-size: 12px;
      padding: 5px 14px;
      border-radius: 8px;
      display: inline-block;
    }
    .sys-msg.verdict span {
      background: #1f2c34;
      color: #e9edef;
      font-size: 13px;
      padding: 8px 18px;
      border-radius: 10px;
    }

    /* ── message row ── */
    .msg-row {
      display: flex;
      align-items: flex-end;
      margin-bottom: 3px;
      gap: 6px;
    }
    .msg-row + .msg-row.same-sender { margin-top: 1px; }

    /* ── avatar ── */
    .msg-avatar {
      width: 28px; height: 28px; border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      font-size: 11px; font-weight: 800;
      flex-shrink: 0; color: #fff;
      align-self: flex-end;
      margin-bottom: 2px;
    }
    .msg-avatar.hidden { visibility: hidden; }

    /* ── bubble ── */
    .bubble {
      position: relative;
      background: #1f2c34;
      border-radius: 0 8px 8px 8px;
      padding: 6px 10px 20px;
      max-width: 340px;
      min-width: 120px;
      word-break: break-word;
    }
    .bubble.first::before {
      content: '';
      position: absolute;
      top: 0; left: -7px;
      width: 0; height: 0;
      border-top: 8px solid #1f2c34;
      border-left: 8px solid transparent;
    }
    .bubble.absent {
      background: #1a1f23;
      opacity: 0.5;
    }

    /* ── sender name ── */
    .bubble-name {
      font-size: 13px;
      font-weight: 600;
      margin-bottom: 3px;
    }

    /* ── vote badge inline ── */
    .vote-pill {
      display: inline-block;
      padding: 1px 8px;
      border-radius: 10px;
      font-size: 11px;
      font-weight: 700;
      margin-left: 6px;
      vertical-align: middle;
      letter-spacing: 0.3px;
    }

    /* ── message text ── */
    .bubble-text { font-size: 14px; color: #e9edef; }

    /* ── findings ── */
    .finding-block { margin-top: 5px; }
    .finding-lbl { font-size: 12px; color: #8696a0; margin-bottom: 2px; }
    .finding-item { font-size: 13px; color: #d1d7db; padding: 1px 0; }
    .finding-item.indent { padding-left: 10px; color: #adb5bd; font-size: 12px; }

    /* ── tags ── */
    .tag {
      display: inline-block; padding: 1px 6px; border-radius: 4px;
      font-size: 11px; font-weight: 600;
      margin-right: 3px; margin-bottom: 2px;
    }
    .tag-warn  { background: #2a1f00; color: #f0c429; border: 1px solid #f0c42944; }
    .tag-del   { background: #2d1010; color: #e84545; border: 1px solid #e8454544; }
    .tag-simp  { background: #2a2000; color: #f0c429; border: 1px solid #f0c42944; }
    .tag-lb    { background: #2d1010; color: #e84545; border: 1px solid #e8454544; }
    .tag-adv   { background: #1e2428; color: #8696a0; border: 1px solid #2a3942;   }

    /* ── metric rows ── */
    .metric { font-size: 13px; padding: 1px 0; }
    .metric-lbl { color: #8696a0; }

    /* ── highlight boxes ── */
    .hl-box {
      margin-top: 5px; padding: 6px 9px;
      border-radius: 6px; font-size: 13px;
    }
    .hl-green  { background: #0d2010; border-left: 3px solid #00a884; }
    .hl-yellow { background: #1a1500; border-left: 3px solid #f0c429; color: #f0c429; }
    .hl-blue   { background: #0a1520; border-left: 3px solid #53bdeb; }
    .hl-red    { background: #200d0d; border-left: 3px solid #e84545; color: #c4cdd6; }

    /* ── quoted reply (cross-question) ── */
    .cq-block {
      margin-top: 7px;
      border-radius: 6px;
      overflow: hidden;
    }
    .cq-to-label {
      font-size: 12px; font-weight: 700;
      padding: 4px 8px 2px;
      background: #182229;
    }
    .cq-body {
      font-size: 13px; color: #d1d7db;
      padding: 4px 8px 5px;
      background: #182229;
      border-left: 3px solid;
    }

    /* ── modify request ── */
    .modify-block {
      margin-top: 7px;
      background: #182229;
      border-left: 3px solid #e84545;
      border-radius: 0 6px 6px 0;
      padding: 5px 9px;
    }
    .modify-lbl {
      font-size: 11px; color: #e84545;
      font-weight: 700; text-transform: uppercase;
      letter-spacing: 0.6px; margin-bottom: 3px;
    }
    .modify-text { font-size: 13px; color: #c4cdd6; line-height: 1.45; }

    /* ── timestamp ── */
    .bubble-time {
      position: absolute;
      bottom: 5px; right: 8px;
      font-size: 11px; color: #8696a0;
      display: flex; align-items: center; gap: 3px;
    }
    .tick { color: #53bdeb; font-size: 12px; }

    /* ── verdict box ── */
    .verdict-box {
      margin: 14px 8px 6px;
      background: #1f2c34;
      border-radius: 10px;
      padding: 12px 16px;
      text-align: center;
    }
    .verdict-title { font-size: 13px; color: #8696a0; margin-bottom: 6px; }
    .verdict-pill {
      display: inline-block; padding: 5px 18px; border-radius: 16px;
      font-size: 16px; font-weight: 700; margin-bottom: 8px;
    }
    .verdict-counts { font-size: 14px; font-weight: 600; }
    .vc-go   { color: #00a884; }
    .vc-mod  { color: #f0c429; }
    .vc-stop { color: #e84545; }
    .vc-sep  { color: #8696a0; margin: 0 6px; }
    .verdict-meta { font-size: 12px; color: #8696a0; margin-top: 4px; }
"""


# ── per-senator content builders ─────────────────────────────────────────────

def _build_wittgenstein(out):
    h = []
    terms = out.get("vague_terms_found", [])
    if terms:
        h.append('<div class="finding-block">')
        h.append(f'<div class="finding-lbl">Termeni vagi ({len(terms)}):</div>')
        for t in terms[:6]:
            h.append(f'<span class="tag tag-warn">{esc(t["term"])}</span>')
        h.append('</div>')
    defs = out.get("operational_definitions_needed", [])
    if defs:
        h.append('<div class="finding-block">')
        h.append(f'<div class="finding-lbl">Definiții propuse:</div>')
        for d in defs[:3]:
            h.append(f'<div class="finding-item"><b>{esc(d["term"])}</b> — {esc(d["proposed_definition"][:150])}</div>')
        h.append('</div>')
    risks = out.get("false_consensus_risks", [])
    if risks:
        h.append('<div class="finding-block">')
        h.append(f'<div class="finding-lbl">⚠ False consensus ({len(risks)}):</div>')
        for r in risks[:3]:
            h.append(f'<div class="finding-item">• {esc(str(r)[:170])}</div>')
        h.append('</div>')
    return "".join(h)


def _build_aurelius(out):
    rev = out.get("reversibility", "?")
    mag = out.get("magnitude", "?")
    quad = out.get("quadrant", "?")
    sc  = out.get("scaling_check", "")
    alt = out.get("smaller_alternative", "")

    rev_c = {"irreversible": "#e84545", "partial": "#f0c429", "reversible": "#00a884"}.get(rev, "#8696a0")
    mag_c = {"critical": "#e84545", "moderate": "#f0c429", "trivial": "#00a884"}.get(mag, "#8696a0")

    h = [
        f'<div class="metric"><span class="metric-lbl">Reversibility: </span>'
        f'<b style="color:{rev_c}">{esc(rev)}</b></div>',
        f'<div class="metric"><span class="metric-lbl">Magnitude: </span>'
        f'<b style="color:{mag_c}">{esc(mag)}</b></div>',
        f'<div class="metric"><span class="metric-lbl">Quadrant: </span>{esc(quad)}</div>',
    ]
    if sc:
        h.append(f'<div class="hl-box hl-blue" style="margin-top:5px">{esc(sc[:260])}</div>')
    if alt:
        h.append(f'<div class="hl-box hl-green">💡 {esc(alt[:210])}</div>')
    return "".join(h)


def _build_confucius(out):
    h = []
    hc = out.get("hierarchy_check", {})
    if hc:
        h.append(f'<div class="metric"><span class="metric-lbl">Authority: </span>{esc(hc.get("authority_layer","?"))}</div>')
        if hc.get("notes"):
            h.append(f'<div class="finding-item">{esc(hc["notes"][:210])}</div>')
    prec = out.get("precedent_search", [])
    if prec:
        h.append(f'<div class="finding-block"><div class="finding-lbl">Precedente ({len(prec)}):</div>')
        for p in prec[:4]:
            oc = p.get("outcome", "?")
            oc_c = {"OK": "#00a884", "BAD": "#e84545", "UNCLEAR": "#f0c429"}.get(oc, "#8696a0")
            h.append(f'<div class="finding-item"><b style="color:{oc_c}">[{esc(oc)}]</b> '
                     f'{esc(str(p.get("reference",""))[:85])}</div>')
            if p.get("relevance"):
                h.append(f'<div class="finding-item indent">{esc(p["relevance"][:170])}</div>')
        h.append('</div>')
    concerns = out.get("institutional_concerns", [])
    if concerns:
        h.append(f'<div class="finding-block"><div class="finding-lbl">⚠ Concerns:</div>')
        for c in concerns[:3]:
            h.append(f'<div class="finding-item">• {esc(str(c)[:170])}</div>')
        h.append('</div>')
    return "".join(h)


def _build_socrate(out):
    h = []
    assumptions = out.get("hidden_assumptions", [])
    if assumptions:
        h.append(f'<div class="finding-block"><div class="finding-lbl">Asumpții ascunse ({len(assumptions)}):</div>')
        for a in assumptions[:5]:
            lb = a.get("load_bearing", False)
            badge = ('<span class="tag tag-lb">LOAD-BEARING</span>'
                     if lb else '<span class="tag tag-adv">advisory</span>')
            h.append(f'<div class="finding-item">{badge} {esc(a["assumption"][:170])}</div>')
            if lb and a.get("if_false_then"):
                h.append(f'<div class="finding-item indent">→ {esc(a["if_false_then"][:150])}</div>')
        h.append('</div>')
    qs = out.get("questions_to_user", [])
    if qs:
        h.append(f'<div class="finding-block"><div class="finding-lbl">❓ Întrebări:</div>')
        for q in qs[:3]:
            h.append(f'<div class="finding-item">• {esc(str(q)[:190])}</div>')
        h.append('</div>')
    mfc = out.get("missing_falsification_criteria", "")
    if mfc:
        h.append(f'<div class="hl-box hl-yellow">⚠ {esc(mfc[:220])}</div>')
    return "".join(h)


def _build_musk(out):
    h = []
    attacked = out.get("components_attacked", [])
    by_v = {"delete": [], "simplify": [], "keep": []}
    for c in attacked:
        by_v.setdefault(c.get("vote", "keep"), []).append(c)

    if by_v["delete"]:
        h.append(f'<div class="finding-block"><div class="finding-lbl">DELETE ({len(by_v["delete"])}):</div>')
        for c in by_v["delete"][:8]:
            h.append(f'<div class="finding-item"><span class="tag tag-del">✗</span>'
                     f' <b>{esc(c["component"][:55])}</b> — {esc(c["reason"][:110])}</div>')
        h.append('</div>')
    if by_v["simplify"]:
        h.append(f'<div class="finding-block"><div class="finding-lbl">SIMPLIFY ({len(by_v["simplify"])}):</div>')
        for c in by_v["simplify"][:4]:
            h.append(f'<div class="finding-item"><span class="tag tag-simp">~</span>'
                     f' <b>{esc(c["component"][:55])}</b> — {esc(c["reason"][:110])}</div>')
        h.append('</div>')
    if by_v["keep"]:
        names = [c["component"][:40] for c in by_v["keep"]]
        h.append(f'<div class="finding-block"><div class="finding-lbl">KEEP ({len(names)}):</div>'
                 f'<div class="finding-item" style="color:#8696a0">'
                 + " · ".join(esc(n) for n in names[:9])
                 + ("…" if len(names) > 9 else "")
                 + '</div></div>')
    abc = out.get("addback_check", {})
    if abc.get("if_deleted_all_keep_what"):
        h.append(f'<div class="hl-box hl-blue">10% add-back: {esc(abc["if_deleted_all_keep_what"][:210])}</div>')
    return "".join(h)


def _build_dimon(out):
    h = []
    scenarios = out.get("stress_scenarios", [])
    if scenarios:
        h.append(f'<div class="finding-block"><div class="finding-lbl">Stress scenarios ({len(scenarios)}):</div>')
        for s in scenarios[:5]:
            mode = s.get("failure_mode", "?")
            mc = {"silent": "#f0c429", "hard": "#e84545"}.get(mode, "#8696a0")
            h.append(f'<div class="finding-item"><b style="color:{mc}">[{esc(mode)}]</b>'
                     f' {esc(s.get("scenario","")[:160])}</div>')
        h.append('</div>')
    sfm = out.get("silent_failure_modes", [])
    if sfm:
        h.append(f'<div class="finding-block"><div class="finding-lbl">👻 Silent failures:</div>')
        for m in sfm[:3]:
            h.append(f'<div class="finding-item">• {esc(str(m)[:170])}</div>')
        h.append('</div>')
    vc = out.get("verifiability_check", {})
    if vc and vc.get("signal_for_success"):
        h.append(f'<div class="hl-box hl-green">✓ {esc(vc["signal_for_success"][:180])}</div>')
    return "".join(h)


def _build_napoleon(out):
    h = []
    ce = out.get("cost_estimate", {})
    if ce:
        cx = ce.get("complexity_score", "?")
        cx_c = {"high": "#e84545", "medium": "#f0c429", "low": "#00a884"}.get(cx, "#8696a0")
        h += [
            f'<div class="metric"><span class="metric-lbl">Tokens/invoc: </span>{esc(ce.get("runtime_tokens_per_invocation","?"))}</div>',
            f'<div class="metric"><span class="metric-lbl">Sub-agents: </span>{esc(str(ce.get("subagent_count","?")))}</div>',
            f'<div class="metric"><span class="metric-lbl">Complexity: </span><b style="color:{cx_c}">{esc(cx)}</b></div>',
            f'<div class="metric"><span class="metric-lbl">Impl hours: </span>{esc(str(ce.get("implementation_hours","?")))}</div>',
        ]
    tc = out.get("terrain_check", {})
    if tc:
        op = tc.get("operator_state", "?")
        op_c = {"fresh": "#00a884", "engaged": "#53bdeb", "stretched": "#f0c429", "fatigued": "#e84545"}.get(op, "#8696a0")
        h.append(f'<div class="metric" style="margin-top:4px"><span class="metric-lbl">Operator: </span>'
                 f'<b style="color:{op_c}">{esc(op)}</b></div>')
        for sig in tc.get("context_signals", [])[:3]:
            h.append(f'<div class="finding-item indent">• {esc(str(sig))}</div>')
    bt = out.get("battle_threshold", {})
    if bt:
        cvb = bt.get("cost_vs_benefit", "?")
        cvb_c = {"favorable": "#00a884", "neutral": "#f0c429", "unfavorable": "#e84545"}.get(cvb, "#8696a0")
        h.append(f'<div class="metric" style="margin-top:4px"><span class="metric-lbl">Cost vs benefit: </span>'
                 f'<b style="color:{cvb_c}">{esc(cvb)}</b></div>')
        if bt.get("rationale"):
            h.append(f'<div class="finding-item">{esc(bt["rationale"][:230])}</div>')
    dr = out.get("delay_recommendation", {})
    if dr and dr.get("should_delay"):
        h.append(f'<div class="hl-box hl-yellow">⏸ {esc(dr.get("if_yes_when","")[:200])}</div>')
    return "".join(h)


CONTENT_FN = {
    "wittgenstein": _build_wittgenstein,
    "aurelius":     _build_aurelius,
    "confucius":    _build_confucius,
    "socrate":      _build_socrate,
    "musk":         _build_musk,
    "dimon":        _build_dimon,
    "napoleon":     _build_napoleon,
}


# ── bubble builder ────────────────────────────────────────────────────────────

def _bubble(name, out, time_str, pos_chgs):
    meta   = SENATORS.get(name, {"color": "#8696a0", "init": "?", "specialty": ""})
    vote   = out.get("vote", "?")
    v_bg, v_text = VOTE_COLOR.get(vote, ("#8696a0", "#fff"))
    cqs    = out.get("cross_questions", [])
    mod_req = out.get("modify_request", "")

    fn = CONTENT_FN.get(name)
    body_html = fn(out) if fn else ""

    # position change note
    pcs = [p for p in pos_chgs if p.get("senator") == name]
    pc_html = ""
    if pcs:
        p = pcs[0]
        pc_html = (f'<div style="font-size:11px;color:#f0c429;margin-bottom:3px">'
                   f'↺ {esc(p["from_vote"])} → {esc(p["to_vote"])} '
                   f'(round {esc(str(p["from_round"]))}→{esc(str(p["to_round"]))})</div>')

    # cross-questions as reply cards
    cq_html = ""
    for q in cqs:
        to_meta = SENATORS.get(q["to"], {"color": "#8696a0"})
        cq_html += (
            f'<div class="cq-block">'
            f'<div class="cq-to-label" style="color:{to_meta["color"]}">↗ @{esc(q["to"])}</div>'
            f'<div class="cq-body" style="border-color:{to_meta["color"]}">{esc(q["question"])}</div>'
            f'</div>'
        )

    # modify request
    mq_html = ""
    if mod_req:
        mq_html = (
            f'<div class="modify-block">'
            f'<div class="modify-lbl">Modify request</div>'
            f'<div class="modify-text">{esc(mod_req)}</div>'
            f'</div>'
        )

    return (
        f'<div class="bubble first">'
        f'<div class="bubble-name" style="color:{meta["color"]}">'
        f'{esc(name.capitalize())} '
        f'<span style="font-size:11px;color:#8696a0;font-weight:400">{esc(meta["specialty"])}</span>'
        f'<span class="vote-pill" style="background:{v_bg};color:{v_text}">{esc(vote)}</span>'
        f'</div>'
        f'{pc_html}'
        f'<div class="bubble-text">{body_html}</div>'
        f'{cq_html}'
        f'{mq_html}'
        f'<div class="bubble-time">{esc(time_str)}'
        f' <span class="tick">✓✓</span></div>'
        f'</div>'
    )


# ── HTML builder ──────────────────────────────────────────────────────────────

def build_html(bundle):
    ts       = bundle.get("timestamp", "?")
    label    = bundle.get("label", "?")
    proposal = bundle.get("proposal", "")
    verdict  = bundle.get("verdict", "?")
    votes    = bundle.get("vote_counts", {})
    absent   = bundle.get("senators_absent", [])
    outputs  = bundle.get("outputs", {})
    pos_chgs = bundle.get("position_changes", [])
    rounds   = bundle.get("rounds", [])
    warnings = bundle.get("warnings", [])
    cq_used  = bundle.get("cross_questions_used", {})

    time_str = _time_from_ts(ts)
    total_cq = sum(cq_used.values()) if cq_used else 0
    is_multiround = len(rounds) > 1
    members_present = len([n for n in SENATOR_ORDER if n not in absent])

    v_bg, v_text = VOTE_COLOR.get(verdict, ("#8696a0", "#fff"))

    # date from ts: "2026-05-16_220025" → "16 Mai 2026"
    MONTHS = ["Ian","Feb","Mar","Apr","Mai","Iun","Iul","Aug","Sep","Oct","Nov","Dec"]
    try:
        date_part = ts.split("_")[0]
        y, mo, d = date_part.split("-")
        date_display = f"{int(d)} {MONTHS[int(mo)-1]} {y}"
    except Exception:
        date_display = ts

    parts = []

    # ── head ──
    parts.append(
        "<!DOCTYPE html>\n<html lang=\"ro\">\n<head>\n"
        "  <meta charset=\"utf-8\">\n"
        "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        f"  <title>Senate — {esc(label)}</title>\n"
        "  <style>" + _css() + "  </style>\n"
        "</head>\n<body>\n<div class=\"shell\">\n"
    )

    # ── WA header ──
    parts.append(
        '<div class="wa-header">\n'
        '  <div class="wa-header-avatar">🏛</div>\n'
        '  <div class="wa-header-info">\n'
        f'    <div class="wa-header-name">Senate · {esc(label)}</div>\n'
        f'    <div class="wa-header-sub">{members_present} senatori'
        + (f', {len(absent)} absenți' if absent else '') + '</div>\n'
        '  </div>\n'
        f'  <div class="wa-header-verdict" style="background:{v_bg};color:{v_text}">{esc(verdict)}</div>\n'
        '</div>\n'
    )

    # ── chat area ──
    parts.append('<div class="chat-bg">\n')

    # date separator
    parts.append(
        f'<div class="date-sep"><span>{esc(date_display)}</span></div>\n'
    )

    # system: proposal
    parts.append(
        '<div class="sys-msg"><span>🏛 Sesiune senate deschisă</span></div>\n'
    )

    # proposal bubble (from "Consilium")
    parts.append(
        '<div class="msg-row">\n'
        '  <div class="msg-avatar" style="background:#00a884">🏛</div>\n'
        '  <div class="bubble first">\n'
        '    <div class="bubble-name" style="color:#00a884">Consilium'
        '      <span style="font-size:11px;color:#8696a0;font-weight:400"> @propunere</span>'
        '    </div>\n'
        f'    <div class="bubble-text">'
        f'      <div style="font-size:12px;color:#8696a0;margin-bottom:4px">Propunere spre audit:</div>'
        f'      {esc(proposal)}'
        f'    </div>\n'
        f'    <div class="bubble-time">{esc(time_str)} <span class="tick">✓✓</span></div>\n'
        '  </div>\n'
        '</div>\n'
    )

    # ── senator messages ──
    for name in SENATOR_ORDER:
        out  = outputs.get(name)
        meta = SENATORS.get(name, {"color": "#8696a0", "init": "?", "specialty": ""})

        if out is None:
            if name in absent:
                parts.append(
                    '<div class="msg-row">\n'
                    f'  <div class="msg-avatar" style="background:#2a3942">{esc(meta["init"])}</div>\n'
                    '  <div class="bubble absent first">\n'
                    f'    <div class="bubble-name" style="color:#8696a0">{esc(name.capitalize())} — absent</div>\n'
                    f'    <div class="bubble-time">{esc(time_str)}</div>\n'
                    '  </div>\n'
                    '</div>\n'
                )
            continue

        bubble_html = _bubble(name, out, time_str, pos_chgs)

        parts.append(
            '<div class="msg-row">\n'
            f'  <div class="msg-avatar" style="background:{meta["color"]}">{esc(meta["init"])}</div>\n'
            f'  {bubble_html}\n'
            '</div>\n'
        )

    # ── verdict ──
    go_c   = votes.get("GO", 0)
    mod_c  = votes.get("MODIFY", 0)
    stop_c = votes.get("STOP", 0)

    meta_lines = []
    if absent:
        meta_lines.append(f"Absenți: {', '.join(absent)}")
    if is_multiround:
        meta_lines.append(f"Runde: {len(rounds)} · Cross-questions: {total_cq} · Position changes: {len(pos_chgs)}")
    if warnings:
        for w in warnings:
            meta_lines.append(f"⚠ {w}")

    meta_html = "".join(f'<div class="verdict-meta">{esc(m)}</div>' for m in meta_lines)

    parts.append(
        f'<div class="verdict-box">\n'
        f'  <div class="verdict-title">Verdict final · {esc(date_display)}</div>\n'
        f'  <div class="verdict-pill" style="background:{v_bg};color:{v_text}">{esc(verdict)}</div>\n'
        f'  <div class="verdict-counts">'
        f'<span class="vc-go">GO {esc(str(go_c))}</span>'
        f'<span class="vc-sep">·</span>'
        f'<span class="vc-mod">MODIFY {esc(str(mod_c))}</span>'
        f'<span class="vc-sep">·</span>'
        f'<span class="vc-stop">STOP {esc(str(stop_c))}</span>'
        f'</div>\n'
        f'  {meta_html}\n'
        f'</div>\n'
    )

    parts.append('</div>\n</div>\n</body>\n</html>\n')
    return "".join(parts)


# ── file helpers ──────────────────────────────────────────────────────────────

def find_latest_bundle():
    pattern = str(Path(__file__).parent.parent / "runs" / "senate" / "*.json")
    files = [f for f in glob(pattern)
             if not f.endswith("_fixture.json") and "transcripts" not in f]
    if not files:
        return None
    return max(files, key=os.path.getmtime)


def default_out_dir(bundle_path):
    p = Path(bundle_path)
    return p.parent / "transcripts" / p.stem


# ── entry point ───────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description="Generate WhatsApp-style HTML transcript of a Senate bundle.")
    ap.add_argument("bundle", nargs="?",
                    help="Path to runs/senate/<file>.json (default: latest)")
    ap.add_argument("--out-dir",
                    help="Output directory (default: runs/senate/transcripts/<stem>/)")
    ap.add_argument("--stdout", action="store_true",
                    help="Print HTML to stdout instead of saving")
    args = ap.parse_args()

    path = args.bundle or find_latest_bundle()
    if not path or not os.path.exists(path):
        print(f"ERROR: bundle not found: {path}", file=sys.stderr)
        sys.exit(1)

    with open(path, encoding="utf-8") as f:
        bundle = json.load(f)

    html_out = build_html(bundle)

    if args.stdout:
        sys.stdout.write(html_out)
        return

    out_dir  = Path(args.out_dir) if args.out_dir else default_out_dir(path)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "index.html"
    out_file.write_text(html_out, encoding="utf-8")
    print(f"written: {out_file}", file=sys.stderr)


if __name__ == "__main__":
    main()
