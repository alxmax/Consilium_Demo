#!/usr/bin/env python3
"""Consilium — Complete Architecture poster (one .excalidraw + .html).

Five stacked sections: STRUCTURE, WORKFLOW, MODES, INTEGRATION, DATA SCHEMA.

Run from the repo root:
    python scripts/make_full_architecture.py
Outputs: docs/consilium_full.excalidraw  docs/consilium_full.html
"""
import os
import sys
import glob
import re


def _builder_path():
    cache = os.path.join(os.path.expanduser("~"), ".claude", "plugins",
                         "cache", "requirement-manager", "requirement-manager")
    hits = glob.glob(os.path.join(cache, "*", "skills",
                                  "excalidraw-diagram", "scripts"))
    if not hits:
        raise RuntimeError(
            "excalidraw-diagram skill not found — run: /plugin install requirement-manager"
        )
    def _ver(p):
        m = re.search(r"(\d+)\.(\d+)\.(\d+)", p)
        return tuple(int(x) for x in m.groups()) if m else (0, 0, 0)
    return max(hits, key=_ver)


sys.path.insert(0, _builder_path())
from excalidraw_builder import Scene

s = Scene(seed=42, roles={
    "voice":    "blue",     # Generator, Control, Conservator
    "skeptic":  "violet",   # Skeptic voice + Trias personality lenses
    "engine":   "teal",     # aggregator, confidence, priors, build_report, log_feedback, personalities
    "gate":     "orange",   # scope_gate, consent gate, validate_report
    "storage":  "green",    # .consilium/runs/*.json, FEEDBACK.html
    "impl":     "pink",     # Coder, Test Writer, Reviewer (implement pipeline)
    "mode":     "indigo",   # mode / variant labels
    "external": "grey",     # SKILL.md, /consilium invocation, CI, sub-agent vehicles
})

s.title("Consilium — Architecture", 80, -80, size=32)
s.label(
    "Multi-voice deliberation skill: Generator -> Conservator -> Control, "
    "aggregated to a canonical report. Read left -> right per section.",
    80, -38, size=13,
)

# ═══════════════════════ 1 · STRUCTURE ════════════════════════════════════
y = s.section("1 - STRUCTURE   the components")

# Row 1: Core voices + Skeptic
voices = s.row([
    ("generator.md", "voice"),
    ("control.md", "voice"),
    ("conservator.md", "voice"),
    ("skeptic.md", "skeptic"),
], 80, y + 44, w=155, h=55, gap=20, font_size=13)
s.enclose(voices, label="Core voices  (prompts/voices/)", pad=16)

# Row 2: Trias personality lenses
lenses = s.row([
    ("pioneer_lens.md", "skeptic"),
    ("architect_lens.md", "skeptic"),
    ("steward_lens.md", "skeptic"),
], 80, y + 162, w=178, h=55, gap=20, font_size=13)
s.enclose(lenses, label="Trias personality lenses", pad=16)

# Row 3: Engine scripts (two rows of 4)
scripts_a = s.row([
    ("scope_gate.py", "gate"),
    ("priors.py", "engine"),
    ("aggregator.py", "engine"),
    ("confidence.py", "engine"),
], 80, y + 272, w=168, h=52, gap=16, font_size=12)
scripts_b = s.row([
    ("build_report.py", "engine"),
    ("validate_report.py", "gate"),
    ("log_feedback.py", "engine"),
    ("personalities.py", "engine"),
], 80, y + 344, w=168, h=52, gap=16, font_size=12)
scripts_c = s.row([
    ("strip_context.py", "engine"),
    ("validate_skeptic.py", "gate"),
    ("audit_counter.py", "engine"),
], 80, y + 416, w=168, h=52, gap=16, font_size=12)
s.enclose(scripts_a + scripts_b + scripts_c, label="Engine scripts  (scripts/)", pad=16)

# Row 4: Implement roles | persistent state | public interface
impl_y = y + 520
impl = s.row([
    ("coder.md", "impl"),
    ("test_writer.md", "impl"),
], 80, impl_y, w=162, h=55, gap=18, font_size=13)
s.enclose(impl, label="Implement roles", pad=16)

stor = s.row([
    (".consilium/runs/\n*.json", "storage"),
    ("FEEDBACK.html", "storage"),
], 500, impl_y, w=178, h=62, gap=18, font_size=12)
s.enclose(stor, label="Persistent state  (.consilium/)", pad=16)

entry = s.row([
    ("SKILL.md", "external"),
    ("/consilium", "external"),
], 990, impl_y, w=148, h=55, gap=20, font_size=13)
s.enclose(entry, label="Public interface", pad=16)

# ═══════════════════════ 2 · WORKFLOW ═════════════════════════════════════
y = s.section("2 - WORKFLOW   Sequential deliberation  (left -> right = run order)")

pipe = s.pipeline([
    {"text": "0·Bootstrap\n1·Gather", "kind": "terminator", "fill": "external",
     "w": 140, "h": 54},
    {"text": "1.5 scope gate\n+ 1.6 consent?", "kind": "decision", "fill": "gate",
     "label": "safe / small"},
    {"text": "2·Generator", "kind": "process", "fill": "voice",
     "label": "candidates"},
    {"text": "3·Conservator", "kind": "process", "fill": "voice",
     "label": "risk scores"},
    {"text": "4·Control", "kind": "process", "fill": "voice",
     "label": "verdicts"},
    {"text": "5·Aggregate\n+ confidence", "kind": "process", "fill": "engine",
     "label": "chosen"},
    {"text": "6·Report\n+ validate", "kind": "process", "fill": "gate",
     "label": "runs/*.json"},
    {"text": "7·Implement", "kind": "terminator", "fill": "impl", "w": 130, "h": 54},
], 80, y + 44, gap=165)

# Bypass: scope skip (trivial/small change → jump to report)
s.route_under(pipe[1], pipe[6], label="skip (trivial)", drop=80)
# Bypass: scale_down — Conservator signals trivial, skip Control
s.route_under(pipe[3], pipe[5], label="scale_down", drop=50)
# Retry: low confidence loops back to Generator (once)
s.route_under(pipe[5], pipe[2], label="conf<0.6: escalate\nto Dialectic", drop=155)

s.label(
    "Consent gate (Step 1.6) fires BEFORE Generator.  "
    "scale_down short-circuits Control.  Low confidence auto-escalates Sequential -> Dialectic at conf < 0.6.",
    80, y + 305, size=12,
)

# ═══════════════════════ 3 · MODES ════════════════════════════════════════
y = s.section("3 - MODES   user-selectable deliberation variants")

# Lane 1: Sequential (default)
seq = s.pipeline([
    ("Generator", "process", "voice"),
    ("Conservator", "process", "voice"),
    ("Control", "process", "voice"),
    ("Aggregate", "process", "engine"),
], 120, y + 60, gap=150)
s.lane(seq, "Sequential (default)  —  single context, 1x cost")

# Lane 2: Dialectic (Sequential + Skeptic on chosen)
dia_y = y + 260
dia = s.pipeline([
    ("Generator", "process", "voice"),
    ("Conservator", "process", "voice"),
    ("Control", "process", "voice"),
    ("Aggregate", "process", "engine"),
    ("Skeptic\n(chosen only)", "process", "skeptic"),
], 120, dia_y, gap=150)
s.lane(dia, "Dialectic  —  Sequential + post-hoc Skeptic sub-agent, ~1.33x cost")

# Lane 3: Trias (3 blind personalities + team vote + 1 post-vote Skeptic)
tri_y = dia_y + 260
dispatch_box = s.box("Orchestrator\ndispatch", 120, tri_y + 62, w=148, h=58,
                     fill="external", font_size=12)
personalities_row = s.row([
    ("Pioneer\n(Sequential)", "skeptic"),
    ("Architect\n(Sequential)", "skeptic"),
    ("Steward\n(Sequential)", "skeptic"),
], 466, tri_y + 56, w=162, h=68, gap=45, font_size=12)
pgroup = s.enclose(personalities_row, pad=14)
s.label("3 sub-agents  BLIND  (sonnet)", 754, tri_y + 48, size=11)
vote_box = s.box("Team Vote\n(majority)", 1100, tri_y + 62, w=148, h=58,
                 fill="engine", font_size=12)
skeptic_box = s.box("Skeptic\n(post-vote)", 1400, tri_y + 62, w=140, h=58,
                    fill="skeptic", font_size=12)
s.label("1  advisory  post-vote", 1475, tri_y + 48, size=11)
s.arrow(dispatch_box, pgroup, label="3x Sequential\nPARALLEL+BLIND")
s.arrow(pgroup, vote_box, label="chosen per lens")
s.arrow(vote_box, skeptic_box, label="winner")
s.lane([dispatch_box, pgroup, vote_box, skeptic_box],
       "Trias  —  3 blind personalities + team vote + 1 post-vote Skeptic, ~2.67x cost  "
       "(lazy routing: low/med -> Sequential, high -> Dialectic, critical -> Trias)")

# skeptic_on_chosen composable note
skep_y = tri_y + 248
s.box(
    "skeptic_on_chosen  — composable flag over any base mode (+1 Skeptic sub-agent).\n"
    "Auto-triggers when confidence in [0.0, 0.7]. Advisory by default; --skeptic-can-override allows override.",
    120, skep_y, w=960, h=68, fill="skeptic", font_size=12,
)

# ═══════════════════════ 4 · INTEGRATION ══════════════════════════════════
y = s.section("4 - INTEGRATION   invocation, sub-agents, CI, and persistent state")
yi = y + 36

user_b   = s.box("Developer / AI", 80,   yi, w=162, h=60, fill="external", font_size=13)
cc_b     = s.box("Claude Code",    479,  yi, w=148, h=60, fill="external", font_size=13)
skill_b  = s.box("SKILL.md\n(public contract)", 870, yi, w=170, h=62, fill="external", font_size=12)
runs_b   = s.box(".consilium/runs/\n*.json",   1310, yi, w=174, h=62, fill="storage", font_size=12)
fb_b     = s.box("FEEDBACK.html\n+ priors.py", 1748, yi, w=172, h=62, fill="storage", font_size=12)

s.arrow(user_b, cc_b, label="invokes")
s.arrow(cc_b, skill_b, label="loads skill")
s.arrow(skill_b, runs_b, label="writes report")
s.arrow(runs_b, fb_b, label="log_feedback.py")

yi2 = yi + 170
sub1 = s.box("consilium-subagent.md\n(Trias / Dialectic sub-agent)", 800, yi2,
             w=234, h=65, fill="external", font_size=11)
sub2 = s.box("consilium-implement-subagent.md\n(Coder -> Test Writer || Reviewer)", 1256, yi2,
             w=282, h=65, fill="impl", font_size=11)
ci_b = s.box("CI  (ci.yml)\ncheck_doc_drift.py\nrun_evals.py", 1748, yi2,
             w=172, h=76, fill="gate", font_size=11)

s.arrow(skill_b, sub1, label="dispatches (Trias/Dialectic)")
s.arrow(skill_b, sub2, label="Step 7 dispatch")
s.arrow(runs_b, ci_b, label="gated by")

# ═══════════════════════ 5 · DATA SCHEMA ══════════════════════════════════
y = s.section("5 - DATA SCHEMA   the run report  (.consilium/runs/YYYY-MM-DD_HHMM_<label>.json)")
ys = y + 24

chosen_enum = s.box(
    "chosen_approach\n\n"
    "<candidate_id>\n"
    "do_nothing\n"
    "skipped\n"
    "trivial-direct\n"
    "prior-deliberation\n"
    "user-spec",
    80, ys + 20, w=240, h=186, fill="mode", font_size=12,
)
report_record = s.box(
    "consilium run report\n\n"
    "success_criterion: str\n"
    "chosen_approach: id | null\n"
    "verification: str\n"
    "alternatives: [{id, summary, why_not}]\n"
    "voice_scores: {gen, ctrl, cons}\n"
    "confidence: float [0.05, 0.99]\n"
    "deliberation_log: [steps]\n"
    "telemetry: {mode, dispatch_count,\n"
    "  consilium_version, consilium_ref}",
    440, ys, w=370, h=240, fill="storage", font_size=12,
)
conf_ann = s.box(
    "confidence formula\n\n"
    "0.7 x agreement\n"
    "+ 0.3 x separation\n"
    "clamped [0.05, 0.99]\n\n"
    "floors: seq=0.70\n"
    "  dia=0.75  trias=0.80",
    920, ys + 20, w=210, h=186, fill="engine", font_size=12,
)
trias_fields = s.box(
    "Trias extras (mode=trias)\n\n"
    "vote_pattern:\n"
    "  3-0=0.95  2-1=0.75\n"
    "  2-0=0.70  1-1-1=null\n"
    "post_vote_skeptic_used: bool\n"
    "skeptic_challenges_count:\n"
    "  0 | 1 | 2",
    920, ys + 220, w=230, h=186, fill="mode", font_size=12,
)

s.arrow(chosen_enum, report_record, label="one value per run")
s.arrow(report_record, conf_ann, label="derived by\nconfidence.py")
s.arrow(conf_ann, trias_fields, label="vote-pattern\nconfidence", dashed=True)

# ═══════════════════════ Legend + Glossary ════════════════════════════════
_, _, max_x, max_y = s.bounds()
ly = max_y + 64

s.legend([
    ("deliberation voice", "blue"),
    ("Skeptic / Trias personality lens", "violet"),
    ("engine script", "teal"),
    ("gate / consent / decision", "orange"),
    ("persistent state / storage", "green"),
    ("implement pipeline role", "pink"),
    ("mode / variant label", "indigo"),
    ("external / entry point", "grey"),
], 80, ly, title="Legend — colour = role")

s.glossary([
    ("SKILL.md", "public contract — skill prompt loaded by Claude Code at invocation"),
    ("Sequential", "Generator -> Conservator -> Control in a single context"),
    ("Dialectic", "Sequential + one Skeptic sub-agent challenging the chosen answer"),
    ("Trias", "3 blind personalities (Pioneer/Architect/Steward) + team vote + 1 post-vote Skeptic"),
    ("skeptic_on_chosen", "composable flag: Skeptic sub-agent auto-triggers at confidence in [0.0,0.7]"),
    ("scale_down", "Conservator meta_recommendation -> skip Control (trivial / low-risk change)"),
    ("lazy routing", "Trias downgrades by magnitude: low/med->Sequential, high->Dialectic, critical->Trias"),
    ("priors.py", "loads FEEDBACK.html outcome history + memory context into Conservator at Step 0"),
    ("scope_gate.py", "auto-detects trivial changes (<=1 file / <=15 lines); fails open"),
    ("strip_context.py", "truncates conversation to ~15K tokens before sub-agent dispatch (Trias/Dialectic)"),
    ("validate_skeptic.py", "gate: enforces Skeptic output has concrete evidence before objection ships"),
    ("audit_counter.py", "silent parallel audit every ~20 Sequential runs; divergence logged to runs/*.json"),
    ("consilium_ref", "committed HEAD SHA embedded in every run — enables git-reproducible replay"),
], 760, ly, title="Glossary")

out_dir = os.path.join(os.path.dirname(__file__), "..", "docs")
pj, ph = s.save(
    "consilium_full",
    out_dir=out_dir,
    crossing_check="error",
    legend_check="error",
    overflow_check="error",
    text_overlap_check="error",
)
print(f"wrote {pj}")
print(f"wrote {ph}")
