"""Generate a WhatsApp-style HTML transcript from a senate JSON bundle.

CLI:
    python scripts/senate_transcript.py runs/senate/<bundle>.json
    # → writes runs/senate/transcripts/<date>/<label>.html

Called automatically by senate_synth.py after every run.
"""
from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

SENATOR_META = {
    "wittgenstein": {"color": "#53BDEB", "initial": "W", "role": "Semantică Operațională"},
    "aurelius":     {"color": "#8694CA", "initial": "A", "role": "Reversibilitate × Magnitudine"},
    "confucius":    {"color": "#CCA86F", "initial": "C", "role": "Ierarhie &amp; Precedente"},
    "socrate":      {"color": "#3FC198", "initial": "S", "role": "Asumpții Ascunse"},
    "musk":         {"color": "#E84545", "initial": "M", "role": "Delete the Part You Don't Need"},
    "dimon":        {"color": "#F09800", "initial": "D", "role": "Stress Test &amp; Contrapartidă"},
    "napoleon":     {"color": "#2a3942", "initial": "N", "role": "Costuri &amp; Teren"},
    "deming":       {"color": "#6C8EBF", "initial": "De", "role": "Disciplină Statistică"},
    "tacitus":      {"color": "#7B5EA7", "initial": "T", "role": "Istoric Retrospectiv"},
}
VOTE_COLORS = {
    "GO":            ("#00a884", "#fff"),
    "STOP":          ("#e84545", "#fff"),
    "MODIFY":        ("#f0c429", "#000"),
    "DEEPLY_SPLIT":  ("#f07d00", "#fff"),
    "UNREACHABLE":   ("#6a737d", "#fff"),
}
# SENATOR_ORDER is used only for build_vote_summary ordering; build_html iterates bundle outputs dynamically.
SENATOR_ORDER = list(SENATOR_META.keys())

def e(s) -> str:
    return html.escape(str(s)) if s is not None else ""


def vote_pill(vote: str) -> str:
    bg, fg = VOTE_COLORS.get(str(vote).upper(), ("#8696a0", "#fff"))
    return f'<span class="vote-pill" style="background:{bg};color:{fg}">{e(vote)}</span>'


def finding_block(label: str, items: list[str]) -> str:
    if not items:
        return ""
    inner = "".join(f'<div class="finding-item">{it}</div>' for it in items)
    return f'<div class="finding-block"><div class="finding-lbl">{label}</div>{inner}</div>'


def hl_box(text: str, cls: str = "blue") -> str:
    return f'<div class="hl-box hl-{cls}">{e(text)}</div>' if text else ""


def metric(label: str, value, color: str = "") -> str:
    style = f' style="color:{color}"' if color else ""
    return f'<div class="metric"><span class="metric-lbl">{e(label)}: </span><b{style}>{e(value)}</b></div>'


def modify_block(req: str) -> str:
    if not req:
        return ""
    return f'<div class="modify-block"><div class="modify-lbl">Solicit:</div><div class="modify-text">{e(req)}</div></div>'


# ── per-senator renderers ──────────────────────────────────────────────────

def render_wittgenstein(out: dict) -> str:
    parts = []
    terms = out.get("vague_terms_found") or []
    if terms:
        tags = "".join(f'<span class="tag tag-warn">{e(t.get("term",""))}</span>' for t in terms)
        items = [f'<b>{e(t.get("term",""))}</b> — {e(t.get("why_vague",""))}' for t in terms]
        parts.append(f'<div class="finding-block"><div class="finding-lbl">Am găsit {len(terms)} termeni ambigui:</div>{tags}</div>')
        parts.append(finding_block("Explicații:", items))

    defs = out.get("operational_definitions_needed") or []
    if defs:
        items = [f'<b>{e(d.get("term",""))}</b> — {e(d.get("proposed_definition",""))}' for d in defs]
        parts.append(finding_block("Propun definițiile:", items))

    fc = out.get("false_consensus_risks") or []
    if fc:
        items = [f"• {e(r)}" for r in fc]
        parts.append(finding_block("⚠ Risc consens aparent:", items))

    return "".join(parts)


def render_aurelius(out: dict) -> str:
    parts = []
    rev = out.get("reversibility")
    mag = out.get("magnitude")
    if rev:
        rev_color = {"complete": "#00a884", "partial": "#f0c429", "none": "#e84545"}.get(str(rev).lower(), "#8696a0")
        parts.append(metric("Reversibilitate", rev, rev_color))
    if mag:
        mag_color = {"low": "#00a884", "moderate": "#f0c429", "high": "#e84545", "critical": "#e84545"}.get(str(mag).lower(), "#8696a0")
        parts.append(metric("Magnitudine", mag, mag_color))
    if out.get("quadrant"):
        parts.append(metric("Cadran", out["quadrant"]))
    if out.get("scaling_check"):
        parts.append(hl_box(out["scaling_check"], "blue"))
    if out.get("smaller_alternative"):
        parts.append(hl_box("💡 " + out["smaller_alternative"], "green"))
    return "".join(parts)


def render_confucius(out: dict) -> str:
    parts = []
    hc = out.get("hierarchy_check") or {}
    if hc:
        ok = hc.get("respects_existing")
        color = "#00a884" if ok else "#e84545"
        parts.append(metric("Autoritate", hc.get("authority_layer", ""), color))
        if hc.get("notes"):
            parts.append(f'<div class="finding-item">{e(hc["notes"])}</div>')

    precs = out.get("precedent_search") or []
    if precs:
        items = []
        for p in precs:
            oc = p.get("outcome", "")
            oc_color = {"OK": "#00a884", "BAD": "#e84545"}.get(oc, "#f0c429")
            items.append(f'<b style="color:{oc_color}">[{e(oc)}]</b> {e(p.get("reference",""))}<div class="finding-item indent">{e(p.get("relevance",""))}</div>')
        parts.append(finding_block(f"Precedente ({len(precs)}):", items))

    ic = out.get("institutional_concerns") or []
    if ic:
        parts.append(finding_block("⚠ Îngrijorări instituționale:", [f"• {e(c)}" for c in ic]))

    return "".join(parts)


def render_socrate(out: dict) -> str:
    parts = []
    assumptions = out.get("hidden_assumptions") or []
    if assumptions:
        items = []
        for a in assumptions:
            lb = a.get("load_bearing")
            tag = '<span class="tag tag-lb">CRITIC</span>' if lb else '<span class="tag tag-adv">minor</span>'
            items.append(f'{tag} {e(a.get("assumption",""))}<div class="finding-item indent">→ {e(a.get("if_false_then",""))}</div>')
        parts.append(finding_block(f"Am identificat {len(assumptions)} asumpții nemarcate:", items))

    qs = out.get("questions_to_user") or []
    if qs:
        parts.append(finding_block("❓ Întrebări:", [f"• {e(q)}" for q in qs]))

    mfc = out.get("missing_falsification_criteria")
    if mfc:
        parts.append(hl_box("⚠ " + mfc, "yellow"))

    return "".join(parts)


def render_musk(out: dict) -> str:
    parts = []
    attacked = out.get("components_attacked") or []
    by_vote: dict[str, list] = {"delete": [], "simplify": [], "keep": []}
    for c in attacked:
        v = str(c.get("vote", "")).lower()
        by_vote.setdefault(v, []).append(c)

    if by_vote.get("delete"):
        tag_cls = "tag-del"
        items = [f'<span class="tag {tag_cls}">✗</span> <b>{e(c.get("component",""))}</b> — {e(c.get("reason",""))}' for c in by_vote["delete"]]
        parts.append(finding_block(f"Tăiem ({len(by_vote['delete'])}):", items))
    if by_vote.get("simplify"):
        items = [f'<span class="tag tag-simp">~</span> <b>{e(c.get("component",""))}</b> — {e(c.get("reason",""))}' for c in by_vote["simplify"]]
        parts.append(finding_block(f"Simplificăm ({len(by_vote['simplify'])}):", items))
    if by_vote.get("keep"):
        items = [f'<span style="color:#8696a0">{e(c.get("component",""))}</span>' for c in by_vote["keep"]]
        parts.append(finding_block(f"Păstrăm ({len(by_vote['keep'])}):", items))

    ab = out.get("addback_check") or {}
    if ab.get("if_deleted_all_keep_what"):
        parts.append(hl_box("10% add-back: " + ab["if_deleted_all_keep_what"], "blue"))

    return "".join(parts)


def render_dimon(out: dict) -> str:
    parts = []
    scenarios = out.get("stress_scenarios") or []
    if scenarios:
        items = []
        for s in scenarios:
            fm = str(s.get("failure_mode", "")).lower()
            color = {"silent": "#f0c429", "graceful": "#8696a0", "hard": "#e84545"}.get(fm, "#8696a0")
            items.append(f'<b style="color:{color}">[{e(fm)}]</b> {e(s.get("scenario",""))}'
                         f'<div class="finding-item indent" style="color:#8696a0">{e(s.get("impact",""))}</div>')
        parts.append(finding_block(f"Scenarii adverse ({len(scenarios)}):", items))

    risks = out.get("counterparty_risks") or []
    if risks:
        items = [f'<b>{e(r.get("counterparty",""))}</b>: {e(r.get("risk",""))}' for r in risks]
        parts.append(finding_block("🔇 Eșecuri silențioase:", items))

    vc = out.get("verifiability_check") or {}
    if vc.get("signal_for_success"):
        parts.append(hl_box("✓ " + vc["signal_for_success"], "green"))

    return "".join(parts)


def render_napoleon(out: dict) -> str:
    parts = []
    ce = out.get("cost_estimate") or {}
    if ce:
        if ce.get("runtime_tokens_per_invocation") is not None:
            parts.append(metric("Tokens/invocație", ce["runtime_tokens_per_invocation"]))
        if ce.get("implementation_hours"):
            parts.append(metric("Ore implementare", ce["implementation_hours"]))
        if ce.get("complexity_score"):
            cs = str(ce["complexity_score"]).lower()
            cs_color = {"low": "#00a884", "medium": "#f0c429", "high": "#e84545"}.get(cs, "#8696a0")
            parts.append(metric("Complexitate", ce["complexity_score"], cs_color))

    bt = out.get("battle_threshold") or {}
    if bt.get("cost_vs_benefit"):
        cvb = str(bt["cost_vs_benefit"]).lower()
        cvb_color = {"favorable": "#00a884", "neutral": "#f0c429", "unfavorable": "#e84545"}.get(cvb, "#8696a0")
        parts.append(metric("Raport cost/beneficiu", bt["cost_vs_benefit"], cvb_color))
    if bt.get("rationale"):
        parts.append(hl_box(bt["rationale"], "blue"))

    dr = out.get("delay_recommendation") or {}
    if dr.get("should_delay") and dr.get("if_yes_when"):
        parts.append(hl_box("⏸ " + dr["if_yes_when"], "yellow"))

    tc = out.get("terrain_check") or {}
    if tc.get("context_signals"):
        items = [f"• {e(s)}" for s in tc["context_signals"]]
        parts.append(finding_block("Context signals:", items))

    return "".join(parts)


def render_deming(out: dict) -> str:
    parts = []
    sc = out.get("sample_size_check") or {}
    n = sc.get("n_evidence_points")
    below = sc.get("below_threshold")
    if n is not None:
        color = "#e84545" if below else "#00a884"
        parts.append(metric("N dovezi", n, color))
    cal = out.get("calibration_evidence") or []
    matches = sum(1 for c in cal if isinstance(c, dict) and c.get("match"))
    if cal:
        rate = round(matches / len(cal), 2)
        rate_color = "#00a884" if rate >= 0.7 else "#f0c429" if rate >= 0.5 else "#e84545"
        parts.append(metric(f"Match rate ({len(cal)} claims)", f"{rate:.0%}", rate_color))
    vc = out.get("variance_check") or {}
    if vc.get("dispersion"):
        disp_color = {"low": "#00a884", "moderate": "#f0c429", "high": "#e84545"}.get(vc["dispersion"], "#8696a0")
        parts.append(metric("Dispersie", vc["dispersion"], disp_color))
    return "".join(parts)


def render_tacitus(out: dict) -> str:
    parts = []
    matches = out.get("retrospective_matches") or []
    confirmed = sum(1 for m in matches if isinstance(m, dict) and m.get("prediction_confirmed"))
    if matches:
        rate = round(confirmed / len(matches), 2)
        rate_color = "#00a884" if rate >= 0.7 else "#f0c429" if rate >= 0.5 else "#e84545"
        parts.append(metric(f"Acuratețe ({len(matches)} runs)", f"{rate:.0%}", rate_color))
    trend = out.get("accuracy_trend")
    if trend:
        parts.append(hl_box(str(trend), "blue"))
    pattern = out.get("pattern_observations")
    if pattern:
        items = [pattern] if isinstance(pattern, str) else [str(p) for p in pattern]
        parts.append(finding_block("Patternuri observate:", items))
    return "".join(parts)


RENDERERS: dict = {
    "wittgenstein": render_wittgenstein,
    "aurelius": render_aurelius,
    "confucius": render_confucius,
    "socrate": render_socrate,
    "musk": render_musk,
    "dimon": render_dimon,
    "napoleon": render_napoleon,
    "deming": render_deming,
    "tacitus": render_tacitus,
}


def render_senator_bubble(name: str, out: dict, ts_display: str) -> str:
    meta = SENATOR_META.get(name, {"color": "#8696a0", "initial": name[0].upper(), "role": ""})
    vote_raw = out.get("vote", "MODIFY")
    modify_req = out.get("modify_request", "")

    body = RENDERERS.get(name, lambda _: "")(out)

    return f"""<div class="msg-row">
  <div class="msg-avatar" style="background:{meta['color']}">{meta['initial']}</div>
  <div class="bubble first"><div class="bubble-name" style="color:{meta['color']}">{e(name.capitalize())} <span style="font-size:11px;color:#8696a0;font-weight:400">{meta['role']}</span>{vote_pill(vote_raw)}</div><div class="bubble-text">{body}</div>{modify_block(modify_req)}<div class="bubble-time">{e(ts_display)} <span class="tick">✓✓</span></div></div>
</div>"""


def render_absent_bubble(name: str, ts_display: str) -> str:
    return f"""<div class="msg-row">
  <div class="msg-avatar" style="background:#2a3942">{e(name[0].upper())}</div>
  <div class="bubble absent first">
    <div class="bubble-name" style="color:#8696a0">{e(name.capitalize())} — absent</div>
    <div class="bubble-time">{e(ts_display)}</div>
  </div>
</div>"""


def format_date_ro(ts: str) -> str:
    months = ["Ian", "Feb", "Mar", "Apr", "Mai", "Iun", "Iul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    try:
        d = ts[:10].split("-")
        return f"{int(d[2])} {months[int(d[1])-1]} {d[0]}"
    except Exception:
        return ts[:10]


def build_vote_summary(outputs: dict, absent: set, vote_counts: dict) -> str:
    groups: dict[str, list[str]] = {"GO": [], "MODIFY": [], "STOP": [], "absent": []}
    for name in SENATOR_ORDER:
        if name in absent:
            groups["absent"].append(name)
        elif name in outputs:
            v = str(outputs[name].get("vote", "MODIFY")).upper()
            groups.setdefault(v, []).append(name)

    group_cfg = [
        ("GO",     "#00a884", "#0d1f17"),
        ("MODIFY", "#f0c429", "#1f1a00"),
        ("STOP",   "#e84545", "#1f0a0a"),
        ("absent", "#8696a0", "#1a2228"),
    ]
    rows = []
    for key, dot_color, _ in group_cfg:
        names = groups.get(key, [])
        if not names:
            continue
        chips = "".join(
            f'<span class="vs-chip">'
            f'<span class="vs-dot" style="background:{dot_color}"></span>'
            f'{e(n.capitalize())}</span>'
            for n in names
        )
        label_color = dot_color
        rows.append(
            f'<div class="vs-group">'
            f'<span class="vs-label" style="color:{label_color}">{e(key)}</span>'
            f'{chips}</div>'
        )

    total = sum(vote_counts.values())
    go = vote_counts.get("GO", 0)
    stop = vote_counts.get("STOP", 0)
    mod = vote_counts.get("MODIFY", 0)
    return (
        f'<div class="vote-summary">'
        f'<div class="vs-title">Tabel voturi · {go} GO · {mod} MODIFY · {stop} STOP · din {total} prezenți</div>'
        + "".join(rows)
        + "</div>"
    )


def build_html(bundle: dict) -> str:
    ts = bundle.get("timestamp", "")
    label = bundle.get("label", "senate")
    proposal = bundle.get("proposal", "")
    outputs = bundle.get("outputs") or {}
    absent = set(bundle.get("senators_absent") or [])
    vote_counts = bundle.get("vote_counts") or {}
    verdict = bundle.get("verdict", "MODIFY")
    ts_display = ts[11:15] if len(ts) >= 15 else ts  # HHMM from "YYYY-MM-DD_HHMMSS"

    verdict_bg, verdict_fg = VOTE_COLORS.get(str(verdict).upper(), ("#8696a0", "#fff"))
    date_ro = format_date_ro(ts)

    vc_go = vote_counts.get("GO", 0)
    vc_mod = vote_counts.get("MODIFY", 0)
    vc_stop = vote_counts.get("STOP", 0)

    vote_summary_html = build_vote_summary(outputs, absent, vote_counts)

    # Iterate dynamically: known senators first (stable order), then any extras from bundle.
    known_order = [n for n in SENATOR_ORDER if n in outputs or n in absent]
    extra = [n for n in outputs if n not in SENATOR_ORDER and n not in absent]
    absent_extra = [n for n in absent if n not in SENATOR_ORDER]
    render_order = known_order + extra + absent_extra

    bubbles = []
    for name in render_order:
        if name in absent:
            bubbles.append(render_absent_bubble(name, ts_display))
        elif name in outputs:
            bubbles.append(render_senator_bubble(name, outputs[name], ts_display))

    bubbles_html = "\n".join(bubbles)

    return f"""<!DOCTYPE html>
<html lang="ro">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Senate — {e(label)}</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: #111b21;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
      font-size: 14.5px;
      line-height: 1.45;
      color: #e9edef;
      min-height: 100vh;
    }}
    .shell {{
      max-width: min(1260px, 98vw);
      margin: 0 auto;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      background: #0b141a;
      box-shadow: 0 0 40px #00000088;
    }}
    .wa-header {{
      background: #1f2c34;
      padding: 10px 16px;
      display: flex;
      align-items: center;
      gap: 12px;
      position: sticky;
      top: 0;
      z-index: 100;
      border-bottom: 1px solid #2a3942;
    }}
    .wa-header-avatar {{
      width: 40px; height: 40px; border-radius: 50%;
      background: #00a884;
      display: flex; align-items: center; justify-content: center;
      font-size: 18px; font-weight: 700; color: #fff;
      flex-shrink: 0;
    }}
    .wa-header-info {{ flex: 1; min-width: 0; }}
    .wa-header-name {{ font-weight: 600; font-size: 16px; color: #e9edef; }}
    .wa-header-sub {{ font-size: 12px; color: #8696a0; }}
    .wa-header-verdict {{
      padding: 3px 10px; border-radius: 12px;
      font-size: 12px; font-weight: 700;
    }}
    .chat-bg {{
      flex: 1;
      padding: 16px 16px 28px;
      background-color: #0b141a;
      background-image:
        radial-gradient(circle at 100% 100%, #1a2942 0%, transparent 50%),
        radial-gradient(circle at 0% 0%, #1a2942 0%, transparent 40%);
    }}
    .date-sep {{
      text-align: center; margin: 8px 0 12px;
    }}
    .date-sep span {{
      background: #1f2c34; color: #8696a0;
      font-size: 12px; padding: 4px 10px; border-radius: 8px;
    }}
    .sys-msg {{
      text-align: center; margin: 4px 0 16px;
      color: #8696a0; font-size: 12px;
    }}
    .sys-msg span {{
      background: #1f2c34; padding: 4px 12px; border-radius: 8px;
    }}
    .msg-row {{
      display: flex; align-items: flex-start; gap: 10px;
      margin-bottom: 16px; padding: 0 4px;
    }}
    .msg-avatar {{
      width: 32px; height: 32px; border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      font-size: 13px; font-weight: 700; color: #fff;
      flex-shrink: 0; margin-top: 4px;
    }}
    .bubble {{
      background: #1f2c34;
      border-radius: 0 10px 10px 10px;
      padding: 8px 14px 10px;
      max-width: calc(100% - 54px);
      position: relative;
    }}
    .bubble.absent {{
      opacity: 0.5;
    }}
    .bubble-name {{
      font-size: 13px; font-weight: 600;
      display: flex; align-items: center; gap: 6px;
      flex-wrap: wrap; margin-bottom: 4px;
    }}
    .vote-pill {{
      display: inline-block; padding: 1px 8px; border-radius: 10px;
      font-size: 11px; font-weight: 700; margin-left: 4px;
    }}
    .bubble-text {{ font-size: 13.5px; color: #d1d7db; }}
    .bubble-time {{
      font-size: 11px; color: #8696a0;
      text-align: right; margin-top: 4px;
    }}
    .tick {{ color: #53bdeb; }}
    .finding-block {{ margin: 6px 0; }}
    .finding-lbl {{
      font-size: 11.5px; font-weight: 600; color: #8696a0;
      text-transform: uppercase; letter-spacing: 0.3px;
      margin-bottom: 3px;
    }}
    .finding-item {{
      font-size: 13px; margin: 3px 0; padding-left: 4px;
      border-left: 2px solid #2a3942;
    }}
    .finding-item.indent {{ padding-left: 16px; color: #8696a0; font-size: 12px; border-left: none; }}
    .metric {{ display: flex; gap: 6px; margin: 3px 0; font-size: 13px; }}
    .metric-lbl {{ color: #8696a0; }}
    .hl-box {{
      margin: 6px 0; padding: 6px 10px;
      border-radius: 6px; font-size: 12.5px;
    }}
    .hl-blue {{ background: #1a2940; border-left: 3px solid #53bdeb; }}
    .hl-green {{ background: #0d2117; border-left: 3px solid #00a884; }}
    .hl-yellow {{ background: #2a2000; border-left: 3px solid #f0c429; }}
    .tag {{
      display: inline-block; font-size: 11px; font-weight: 600;
      padding: 1px 5px; border-radius: 4px; margin: 1px 2px;
    }}
    .tag-warn {{ background: #2a2000; color: #f0c429; }}
    .tag-del {{ background: #2a0a0a; color: #e84545; }}
    .tag-simp {{ background: #1a2000; color: #a0c040; }}
    .tag-lb {{ background: #1a2940; color: #53bdeb; }}
    .tag-adv {{ background: #1f2c34; color: #8696a0; }}
    .modify-block {{
      margin-top: 10px; padding: 8px 10px;
      background: #111b21; border-radius: 6px;
      border-left: 3px solid #f0c429;
    }}
    .modify-lbl {{ font-size: 10.5px; color: #f0c429; font-weight: 600; margin-bottom: 2px; }}
    .modify-text {{ font-size: 12.5px; color: #d1d7db; }}
    .vote-summary {{
      margin: 4px 4px 20px;
      background: #1a2330; border-radius: 10px;
      padding: 12px 16px;
      border: 1px solid #2a3942;
    }}
    .vs-title {{
      font-size: 10.5px; font-weight: 600; color: #8696a0;
      text-transform: uppercase; letter-spacing: 0.5px;
      margin-bottom: 10px;
    }}
    .vs-group {{ display: flex; gap: 8px; flex-wrap: wrap; margin: 4px 0; align-items: center; }}
    .vs-label {{ font-size: 11px; font-weight: 700; min-width: 52px; }}
    .vs-chip {{
      display: inline-flex; align-items: center; gap: 5px;
      padding: 2px 8px; border-radius: 12px;
      font-size: 12px; font-weight: 500;
      background: #2a3942;
    }}
    .vs-dot {{ width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }}
    .verdict-box {{
      margin: 20px 8px 8px;
      background: #1f2c34; border-radius: 10px;
      padding: 14px 16px; text-align: center;
    }}
    .verdict-title {{ font-size: 11.5px; color: #8696a0; margin-bottom: 8px; }}
    .verdict-pill {{
      display: inline-block; padding: 4px 20px; border-radius: 14px;
      font-size: 16px; font-weight: 700; margin-bottom: 6px;
    }}
    .verdict-counts {{ font-size: 12px; color: #8696a0; margin-bottom: 4px; }}
    .vc-go {{ color: #00a884; }}
    .vc-mod {{ color: #f0c429; }}
    .vc-stop {{ color: #e84545; }}
    .vc-sep {{ margin: 0 6px; }}
    .verdict-meta {{ font-size: 11.5px; color: #8696a0; }}
    .proposal-text {{ font-size: 13px; color: #d1d7db; }}

    /* ── mode toggle button ── */
    .mode-btn {{
      background: #2a3942; border: none; cursor: pointer;
      color: #8696a0; font-size: 11.5px; font-weight: 600;
      padding: 4px 10px; border-radius: 8px;
      white-space: nowrap; flex-shrink: 0;
      transition: background 0.15s, color 0.15s;
    }}
    .mode-btn:hover {{ background: #3d4f5a; color: #e9edef; }}
    .mode-btn .lbl-adv {{ display: inline; }}
    .mode-btn .lbl-sim {{ display: none; }}

    /* ── simple mode ── */
    body.simple-mode .bubble-text {{ display: none; }}
    body.simple-mode .msg-row {{ margin-bottom: 8px; }}
    body.simple-mode .bubble {{ padding: 6px 12px 8px; }}
    body.simple-mode .modify-block {{ margin-top: 6px; }}
    body.simple-mode .vote-summary {{ margin-bottom: 12px; }}
    body.simple-mode .mode-btn .lbl-adv {{ display: none; }}
    body.simple-mode .mode-btn .lbl-sim {{ display: inline; }}
    body.simple-mode .bubble-name {{ margin-bottom: 0; }}
  </style>
</head>
<body>
<div class="shell">
  <div class="wa-header">
    <div class="wa-header-avatar">🏛</div>
    <div class="wa-header-info">
      <div class="wa-header-name">Senate — {e(label)}</div>
      <div class="wa-header-sub">7 senatori · {e(ts[:10])}</div>
    </div>
    <div class="wa-header-verdict" style="background:{verdict_bg};color:{verdict_fg}">{e(verdict)}</div>
    <button id="mode-toggle" class="mode-btn"><span class="lbl-adv">⊟ Sumar</span><span class="lbl-sim">⊞ Detaliat</span></button>
  </div>
  <div class="chat-bg">
    <div class="date-sep"><span>{e(date_ro)}</span></div>
    <div class="sys-msg"><span>🏛 Consilium deschide ședința</span></div>
    <div class="msg-row">
      <div class="msg-avatar" style="background:#00a884">🏛</div>
      <div class="bubble first">
        <div class="bubble-name" style="color:#00a884">Consilium <span style="font-size:11px;color:#8696a0;font-weight:400">— subiect de deliberat</span></div>
        <div class="bubble-text"><div style="font-size:12px;color:#8696a0;margin-bottom:4px">Supun atenției senatului:</div><span class="proposal-text">{e(proposal)}</span></div>
        <div class="bubble-time">{e(ts_display)} <span class="tick">✓✓</span></div>
      </div>
    </div>
{vote_summary_html}
{bubbles_html}
    <div class="verdict-box">
      <div class="verdict-title">Senatul a decis · {e(date_ro)}</div>
      <div class="verdict-pill" style="background:{verdict_bg};color:{verdict_fg}">{e(verdict)}</div>
      <div class="verdict-counts"><span class="vc-go">GO {vc_go}</span><span class="vc-sep">·</span><span class="vc-mod">MODIFY {vc_mod}</span><span class="vc-sep">·</span><span class="vc-stop">STOP {vc_stop}</span></div>
      {'<div class="verdict-meta">Absenți: ' + e(", ".join(sorted(absent))) + '</div>' if absent else ''}
    </div>
  </div>
</div>
</body>
<script>
  (function() {{
    var KEY = "consilium_transcript_mode";
    var btn = document.getElementById("mode-toggle");
    if (localStorage.getItem(KEY) === "simple") document.body.classList.add("simple-mode");
    btn.addEventListener("click", function() {{
      var simple = document.body.classList.toggle("simple-mode");
      localStorage.setItem(KEY, simple ? "simple" : "advanced");
    }});
  }})();
</script>
</html>"""


_SKIP_WORDS = ("smoke", "fixture", "collision")


def _is_smoke(label: str) -> bool:
    low = label.lower()
    return any(w in low for w in _SKIP_WORDS)


def generate(bundle_path: Path) -> Path | None:
    """Generate transcript for a senate bundle.

    Returns the output path, or None if the run should be skipped.
    Output: runs/senate/transcripts/<YYYY-MM-DD>/<label>.html
    On label collision uses timestamp suffix <label>_HHMMSS.html.
    """
    if bundle_path.stem.startswith("_"):
        return None
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    label = bundle.get("label", "senate")
    if _is_smoke(label):
        return None
    ts = bundle.get("timestamp", "unknown")
    date = ts[:10] if len(ts) >= 10 else "unknown"
    out_dir = bundle_path.parent / "transcripts" / date
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{label}.html"
    if out_file.exists():
        ts_suffix = ts[11:17] if len(ts) >= 17 else ts.replace(":", "").replace("-", "")[-6:]
        out_file = out_dir / f"{label}_{ts_suffix}.html"
    out_file.write_text(build_html(bundle), encoding="utf-8")
    return out_file


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("bundle", nargs="?", help="Path to senate JSON bundle (default: latest non-smoke in runs/senate/)")
    parser.add_argument("--backfill", action="store_true", help="Regenerate transcripts for all non-smoke bundles in runs/senate/")
    args = parser.parse_args()

    senate_dir = Path(__file__).resolve().parent.parent / "runs" / "senate"

    if args.backfill:
        bundles = sorted(p for p in senate_dir.glob("*.json") if p.is_file())
        generated, skipped = 0, 0
        for bp in bundles:
            out = generate(bp)
            if out:
                print(f"  generated: {out.relative_to(senate_dir.parent)}")
                generated += 1
            else:
                skipped += 1
        print(f"\n{generated} generated, {skipped} smoke/fixture skipped")
        return

    if args.bundle:
        bundle_path = Path(args.bundle)
    else:
        candidates = [p for p in senate_dir.glob("*.json") if p.is_file() and not _is_smoke(p.stem)]
        if not candidates:
            print("No non-smoke senate bundles found in runs/senate/", file=sys.stderr)
            sys.exit(1)
        bundle_path = max(candidates, key=lambda p: p.stat().st_mtime)

    out = generate(bundle_path)
    if out:
        print(f"transcript: {out}")
    else:
        print(f"skipped (smoke/fixture label): {bundle_path.name}")


if __name__ == "__main__":
    main()
