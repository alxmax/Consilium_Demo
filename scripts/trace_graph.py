#!/usr/bin/env python3
"""Render a deliberation report as a Mermaid flowchart of the EXECUTED pipeline.

Reads a canonical report (`.consilium/runs/<file>.json`) and emits a mode-aware
Mermaid `flowchart` to stdout. This is a *view* of what a single run actually did
(short-circuit, passthrough, full pipeline, Trias fan) — not a runtime orchestrator.
Mermaid renders natively in GitHub markdown and at mermaid.live, so the output needs
no toolchain: paste it into a ```mermaid block.

The static, canonical pipeline diagram lives in docs/architecture/src/pipeline.jsx;
this script complements it with the per-run trace.

Stdlib-only. CLI:
    cat .consilium/runs/<file>.json | python scripts/trace_graph.py
    python scripts/trace_graph.py --input .consilium/runs/<file>.json
    python scripts/trace_graph.py --input <file>.json --fence   # wrap in ```mermaid

Exit 0 on success; 2 on malformed JSON / missing input.
"""
from __future__ import annotations

import argparse
import json
import sys

from utils import force_utf8_streams

# Canonical execution order (Conservator runs FIRST — see SKILL.md Stage 2).
# Maps a deliberation_log step / telemetry voice to (node_id, label).
VOICE_NODES = [
    ("conservator", "CON", "Conservator<br/>risk assessment"),
    ("generator", "GEN", "Generator<br/>candidates"),
    ("control", "CTRL", "Control<br/>verdicts"),
    ("skeptic", "SKP", "Skeptic<br/>challenge chosen"),
]


def _esc(text: object) -> str:
    """Make a string safe inside a Mermaid "..." node label."""
    return str(text).replace('"', "'").replace("\n", " ").strip()


def _present_steps(report: dict) -> set[str]:
    """Union of voices seen in deliberation_log steps and telemetry.voices."""
    steps = {
        str(s.get("step", "")).lower()
        for s in report.get("deliberation_log", []) or []
        if isinstance(s, dict)
    }
    voices = (report.get("telemetry") or {}).get("voices") or {}
    steps |= {str(v).lower() for v in voices}
    return steps


def build_mermaid(report: dict) -> str:
    mode = str((report.get("telemetry") or {}).get("mode") or "sequential").lower()
    chosen = report.get("chosen_approach")
    lines = ["flowchart TD"]

    def node(nid: str, label: str) -> None:
        lines.append(f'  {nid}["{_esc(label)}"]')

    def edge(a: str, b: str, lbl: str | None = None) -> None:
        lines.append(f"  {a} -->|{_esc(lbl)}| {b}" if lbl else f"  {a} --> {b}")

    # 1. Skipped (scope gate) -------------------------------------------------
    if report.get("skipped") is True or chosen == "skipped":
        reason = report.get("skip_reason") or "scope gate: trivial change"
        node("SKIP", f"skipped<br/>{reason}")
        return "\n".join(lines)

    # 2. Prior-deliberation passthrough --------------------------------------
    if chosen == "prior-deliberation" or mode == "prior_deliberation_passthrough":
        matched = ""
        for s in report.get("deliberation_log", []) or []:
            if isinstance(s, dict) and s.get("matched"):
                matched = f"<br/>matched: {s.get('matched')}"
                break
        node("PRIOR", f"prior-deliberation passthrough{matched}")
        node("REP", "report")
        edge("PRIOR", "REP")
        return "\n".join(lines)

    # 3. Conservator scale_down short-circuit --------------------------------
    if mode == "sequential_scale_down" or chosen == "trivial-direct":
        node("CON", "Conservator<br/>meta: scale_down")
        node("REP", f"report<br/>{chosen or 'trivial-direct'}")
        edge("CON", "REP", "scale_down")
        return "\n".join(lines)

    # Shared tail: aggregate -> confidence -> report -------------------------
    # The aggregate result lives in deliberation_log[step=aggregate].result
    # (build_report), not at report["aggregate"]; confidence is a scalar float.
    agg: dict = {}
    for step in report.get("deliberation_log", []):
        if isinstance(step, dict) and step.get("step") == "aggregate":
            res = step.get("result")
            agg = res if isinstance(res, dict) else {}
            break
    vetoed = agg.get("vetoed") or []
    agg_label = f"aggregate<br/>chosen: {chosen or 'null'}"
    if vetoed:
        agg_label += f" · vetoed: {len(vetoed)}"
    conf_raw = report.get("confidence")
    conf_val = conf_raw if isinstance(conf_raw, (int, float)) and not isinstance(conf_raw, bool) else None

    # 4. Trias fan: 3 personalities dispatched IN PARALLEL, each a single
    # one-shot deliberation whose lens re-weights the 3 voice scores (since
    # 2026-05-21 one-shot dispatch — NOT 3 sequential voice sub-steps). Canonical
    # topology; per-run serial-vs-parallel drift is detected by
    # check_trias_parallelism.py, not derivable from the report alone. -----------
    if mode in ("trias", "trias_split"):
        node("ROOT", "Trias dispatch<br/>(3 personalities · parallel)")
        personas = (
            ("PIO", "Pioneer<br/>one-shot · lens up-weights Generator"),
            ("ARC", "Architect<br/>one-shot · lens balances voices"),
            ("STE", "Steward<br/>one-shot · lens up-weights Conservator"),
        )
        for pid, plabel in personas:
            node(pid, plabel)
            edge("ROOT", pid)
        node("VOTE", f"democratic vote<br/>chosen: {chosen or 'null'}")
        for pid, _ in personas:
            edge(pid, "VOTE")
        if conf_val is not None:
            node("CONF", f"confidence<br/>{conf_val}")
            edge("VOTE", "CONF")
            node("REP", "report")
            edge("CONF", "REP")
        else:
            node("REP", "report")
            edge("VOTE", "REP")
        return "\n".join(lines)

    # 5. Default: sequential / parallel / dialectic (+ optional skeptic) ------
    present = _present_steps(report)
    chain: list[str] = []
    for key, nid, label in VOICE_NODES:
        if key in present:
            node(nid, label)
            chain.append(nid)
    if not chain:  # nothing recognized — emit a minimal node so output is valid
        node("RUN", f"deliberation<br/>mode: {mode}")
        chain = ["RUN"]

    node("AGG", agg_label)
    tail = ["AGG"]
    if conf_val is not None:
        node("CONF", f"confidence<br/>{conf_val}")
        tail.append("CONF")
    node("REP", "report")
    tail.append("REP")

    # Skeptic (if present) is post-hoc/advisory on the chosen, after aggregate.
    seq = [n for n in chain if n != "SKP"] + tail
    for a, b in zip(seq, seq[1:]):
        edge(a, b)
    if "SKP" in chain:
        edge("AGG", "SKP")
        edge("SKP", "REP", "advisory")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", default=None, help="report JSON path (default: stdin)")
    ap.add_argument("--fence", action="store_true", help="wrap output in a ```mermaid fence")
    args = ap.parse_args(argv)

    # Labels contain non-ASCII (e.g. the → arrow) and the report read from stdin
    # carries UTF-8 (ț/ș/ă in success_criterion); reconfigure all three streams —
    # including stdin — so a bare `cat run.json | python scripts/trace_graph.py`
    # works on a cp1252 Windows console (the prior loop missed stdin).
    force_utf8_streams()

    try:
        raw = open(args.input, encoding="utf-8").read() if args.input else sys.stdin.read()
        report = json.loads(raw)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"trace_graph: cannot parse report: {exc}", file=sys.stderr)
        return 2
    if not isinstance(report, dict):
        print("trace_graph: report must be a JSON object", file=sys.stderr)
        return 2

    mermaid = build_mermaid(report)
    print(f"```mermaid\n{mermaid}\n```" if args.fence else mermaid)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
