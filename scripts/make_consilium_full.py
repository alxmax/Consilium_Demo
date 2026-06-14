#!/usr/bin/env python3
"""
make_consilium_full.py — Consilium complete architecture diagram.

Covers the 8-step pipeline, veto cascade, all 4 modes, and Skeptic sub-agent flow
in a single .excalidraw + .html file.

Run:  python scripts/make_consilium_full.py [out_dir]
Default out_dir: docs/
"""
import sys

BUILDER = r"C:\Users\ALEX\.claude\plugins\cache\requirement-manager\requirement-manager\1.32.0\skills\excalidraw-diagram\scripts"
sys.path.insert(0, BUILDER)
from excalidraw_builder import Scene

s = Scene(font="normal", sketch=False, seed=42)

# ── colour convention ───────────────────────────────────────────────────────
GEN  = "violet"  # Generator
CONS = "green"   # Conservator
CTRL = "blue"    # Control
SKEP = "red"     # Skeptic
AGG  = "teal"    # Aggregator / Confidence
REP  = "indigo"  # Report / Output

# ═══════════════════════════════════════════════════════════════════════════
# TITLE
# ═══════════════════════════════════════════════════════════════════════════
s.title("Consilium — Complete Architecture", 40, -108, size=40, color="black")
s.title(
    "Three AI voices deliberate a code change, then vote on the safest good option.",
    44, -58, size=17, color="grey",
)
s.label(
    "▪ violet = Generator   ▪ green = Conservator   ▪ blue = Control   "
    "▪ red = Skeptic   ▪ teal = Aggregation / Confidence   ▪ indigo = Report",
    40, -22, size=13, color="grey", align="left",
)

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 1 — PIPELINE
# ═══════════════════════════════════════════════════════════════════════════
s.title("PIPELINE  (Steps 0 – 7)", 40, 18, size=24, color="black")

PY   = 72     # top-y of pipeline boxes
BH   = 72     # box height
DY   = PY - 10  # diamonds sit slightly higher (taller)
DH   = 92     # diamond height
STEP = 200    # column step

def cx(n): return 40 + n * STEP  # x left-edge for column n

# ── pipeline boxes ──────────────────────────────────────────────────────────
b0  = s.box("Step 0\nBootstrap\npriors.py",             cx(0),  PY,  165, BH, fill="grey",   font_size=13)
b1  = s.box("Step 1\nGather & Goal\nsuccess_criterion", cx(1),  PY,  175, BH, fill="grey",   font_size=13)
b15 = s.diamond("Step 1.5\nScope Gate",                 cx(2),  DY,  175, DH, fill="orange", font_size=13)
b16 = s.diamond("Step 1.6\nConsent Gate",               cx(3),  DY,  175, DH, fill="yellow", font_size=13)
b2  = s.box("Step 2\nGenerator\ncandidates[ ]",         cx(4),  PY,  165, BH, fill=GEN,      font_size=13)
b3  = s.box("Step 3\nConservator\nrisk scores",         cx(5),  PY,  165, BH, fill=CONS,     font_size=13)
b4  = s.box("Step 4\nControl\nverdict[ ]",              cx(6),  PY,  165, BH, fill=CTRL,     font_size=13)
b5  = s.box("Step 5\nAggregator\nveto cascade",         cx(7),  PY,  165, BH, fill=AGG,      font_size=13)
b5b = s.box("Step 5b\nConfidence\n0.05 – 0.99",         cx(8),  PY,  165, BH, fill="pink",   font_size=13)
b6  = s.box("Step 6\nReport\n.consilium/runs/",          cx(9),  PY,  175, BH, fill=REP,      font_size=13)
b7  = s.box("Step 7\nImplement\n(if deliverables)",      cx(10), PY,  175, BH, fill="orange", font_size=13)

# ── main pipeline arrows ────────────────────────────────────────────────────
s.arrow(b0,  b1)
s.arrow(b1,  b15)
s.arrow(b15, b16, label="non-trivial")
s.arrow(b16, b2,  label="consent OK")
s.arrow(b2,  b3)
s.arrow(b3,  b4)
s.arrow(b4,  b5)
s.arrow(b5,  b5b)
s.arrow(b5b, b6)
s.arrow(b6,  b7, dashed=True, label="opt-in")

# ── exit / bypass paths ─────────────────────────────────────────────────────
# Scope Gate → auto-skip (trivial changes)
skip = s.box(
    "AUTO-SKIP\ntrivial change\n(< 15 lines, 1 file)",
    cx(2), PY + 140, 175, 72, fill="grey", font_size=12,
)
s.arrow(b15, skip, label="trivial", dashed=True, color="grey")

# Consent Gate → ask user before Generator dispatch
ask = s.box(
    "ASK USER\nbefore Generator\ndispatch",
    cx(3), PY + 140, 175, 72, fill="yellow", font_size=12,
)
s.arrow(b16, ask, label="sensitive", dashed=True, color="grey")

# scale_down bypass: Conservator → Aggregator, routing under Control
s.route_under(b3, b5, drop=52, label="scale_down → skip Control", dashed=True, color="grey")

# low-confidence auto-escalate note (right of Confidence box)
s.label(
    "confidence < 0.6\n→ auto-escalate to Dialectic",
    cx(8) + 82, PY + BH + 12, size=13, color="red", align="center",
)

# ── veto cascade notes box (below Aggregator) ───────────────────────────────
# Center it horizontally under the Aggregator
agg_cx = cx(7) + 82          # center x of Aggregator
cascade_w = 430
cascade = s.box(
    "Veto cascade (highest → lowest priority):\n"
    "P1  BLOCK     glossary_fail  or  irreversibility_flag\n"
    "P2  REWORK    substantial disagreement\n"
    "P3  ESCALATE  3 or more triggers fired\n"
    "P4  ADAPT     scale_down  or  scale_up\n"
    "    GO        default — aggregate vote",
    agg_cx - cascade_w // 2, PY + 136, cascade_w, 135,
    fill=None, font_size=12,
)
s.arrow(b5, cascade, color="grey", dashed=True)

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 2 — MODES
# ═══════════════════════════════════════════════════════════════════════════
MY = PY + 340    # section title y
FY = MY + 48     # top y of mode frames
FH = 418         # common frame height (all four frames same height)

s.title("MODES", 40, MY, size=24, color="black")
s.title(
    "Same three voices, arranged differently depending on the stakes.",
    44, MY + 34, size=15, color="grey",
)

# ─── Sequential (default) ──────────────────────────────────────────────────
SX, SW = 40, 420
s.frame(SX, FY, SW, FH)
s.title("Sequential  (default)", SX + 14, FY + 14, size=17)
s.label(
    "0 sub-agents · confidence floor 0.70\n"
    "Voices share context; strip_context.py reduces footprint",
    SX + SW // 2, FY + 78, size=12, color="grey", align="center",
)
sg = s.box("Generator",   SX + 60, FY + 128, 300, 60, fill=GEN,  font_size=14)
sc = s.box("Conservator", SX + 60, FY + 208, 300, 60, fill=CONS, font_size=14)
sk = s.box("Control",     SX + 60, FY + 288, 300, 60, fill=CTRL, font_size=14)
s.arrow(sg, sc)
s.arrow(sc, sk)
s.label(
    "Auto-escalates to Dialectic if confidence < 0.6",
    SX + SW // 2, FY + 375, size=12, color="red", align="center",
)

# ─── Dialectic ─────────────────────────────────────────────────────────────
DX, DW = SX + SW + 50, 500
s.frame(DX, FY, DW, FH)
s.title("Dialectic", DX + 14, FY + 14, size=17)
s.label(
    "+1 Skeptic sub-agent · confidence floor 0.75\n"
    "Code context injected: language, framework, test_files",
    DX + DW // 2, FY + 78, size=12, color="grey", align="center",
)
dag = s.box("Generator",   DX + 20, FY + 128, 220, 60, fill=GEN,  font_size=14)
dac = s.box("Conservator", DX + 20, FY + 208, 220, 60, fill=CONS, font_size=14)
dak = s.box("Control",     DX + 20, FY + 288, 220, 60, fill=CTRL, font_size=14)
s.arrow(dag, dac)
s.arrow(dac, dak)
dsk = s.box("Skeptic\n(sub-agent)", DX + 278, FY + 198, 178, 80, fill=SKEP, font_size=14)
s.label(
    "receives only:\nchosen + criterion",
    DX + 287, FY + 292, size=11, color="grey", align="left",
)
s.arrow(dak, dsk, label="chosen →", color="grey")
s.label(
    "Skeptic can hard-override with --skeptic-can-override",
    DX + DW // 2, FY + 375, size=12, color="grey", align="center",
)

# ─── Trias ─────────────────────────────────────────────────────────────────
TX, TW = DX + DW + 50, 1150
FH_TRIAS = 500
s.frame(TX, FY, TW, FH_TRIAS)
s.title("Trias", TX + 14, FY + 14, size=17)
s.label(
    "6 sub-agents nominal (3 Sequential + 3 Skeptics) · confidence floor 0.80 · democratic vote\n"
    "Lazy routing: low/medium effort → Sequential,  high → Dialectic,  critical → full Trias",
    TX + TW // 2, FY + 70, size=12, color="grey", align="center",
)

p_defs = [
    ("Pioneer\nlens",   "violet", TX +  30),
    ("Architect\nlens", "blue",   TX + 420),
    ("Steward\nlens",   "green",  TX + 810),
]
p_skep_boxes = []
for (p_name, p_fill, p_x) in p_defs:
    s.frame(p_x, FY + 108, 300, 178, dashed=True)
    s.label(p_name, p_x + 150, FY + 103, size=13, color="grey", align="center")
    p_seq = s.box(
        "G → Cons → Ctrl\n(Sequential)",
        p_x + 25, FY + 138, 250, 65, fill=p_fill, font_size=13,
    )
    p_skep = s.box("Skeptic", p_x + 75, FY + 318, 150, 55, fill=SKEP, font_size=14)
    s.arrow(p_seq, p_skep, label="chosen", color="grey")
    p_skep_boxes.append(p_skep)

vote = s.box("Vote\n(majority)", TX + 490, FY + 413, 160, 65, fill=AGG, font_size=14)
for pb in p_skep_boxes:
    s.arrow(pb, vote, color="grey")

s.label(
    "Pioneer weights Gen/Ctrl/Cons: 0.49/0.30/0.21   "
    "Architect: 0.30/0.40/0.30   Steward: 0.30/0.30/0.40",
    TX + TW // 2, FY + 476, size=11, color="grey", align="center",
)

# ─── skeptic_on_chosen (composable flag) ───────────────────────────────────
SOX, SOW = TX + TW + 50, 370
s.frame(SOX, FY, SOW, FH, dashed=True)
s.title("skeptic_on_chosen\n(flag, any mode)", SOX + 14, FY + 14, size=15)
s.label(
    "Auto-triggers when confidence ∈ [0.0, 0.7]\n+1 sub-agent over any base mode",
    SOX + SOW // 2, FY + 88, size=12, color="grey", align="center",
)
so_base = s.box(
    "Any base mode\n(Sequential /\nDialectic / Trias)",
    SOX + 60, FY + 148, 250, 82, fill="grey", font_size=13,
)
so_skep = s.box(
    "Skeptic\n(sub-agent)",
    SOX + 60, FY + 272, 250, 82, fill=SKEP, font_size=13,
)
s.arrow(so_base, so_skep, label="chosen →")
s.label(
    "Input: only chosen + success_criterion\n"
    "Advisory by default;\n"
    "--skeptic-can-override for hard override",
    SOX + SOW // 2, FY + 375, size=11, color="grey", align="center",
)

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 3 — INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════
_, _, _, _bot = s.bounds()
INTY  = _bot + 80
INFFY = INTY + 70
IH    = 65  # row box height

s.title("INTEGRATION", 40, INTY, size=24, color="black")
s.title(
    "Invocation chain, sub-agent dispatch, git automation, CI, "
    "plugin distribution, and the priors feedback loop.",
    44, INTY + 34, size=15, color="grey",
)

# ── Lane 1: Invocation chain + priors feedback loop ─────────────────────────
R1Y = INFFY + 40
s.label("Invocation chain & priors loop", 40, INFFY + 12, size=13, color="grey", align="left")

usr  = s.box("User\n/ Claude Code",             40,   R1Y, 160, IH, fill="grey",   font_size=13)
skll = s.box("/consilium\nSKILL.md",             250,  R1Y, 155, IH, fill="yellow", font_size=13)
pipe = s.box("8-step\npipeline",                 455,  R1Y, 145, IH, fill="grey",   font_size=13)
runs = s.box(".consilium/runs/\n*.json",          650,  R1Y, 185, IH, fill=REP,      font_size=13)
fbk  = s.box("FEEDBACK.html\n(log_feedback.py)", 885,  R1Y, 215, IH, fill=CONS,     font_size=13)
pri  = s.box("priors.py\n(Step 0)",              1150, R1Y, 155, IH, fill=AGG,      font_size=13)

s.arrow(usr,  skll)
s.arrow(skll, pipe)
s.arrow(pipe, runs, label="Step 6 persists")
s.arrow(runs, fbk,  label="log outcome")
s.arrow(fbk,  pri)
s.route_under(pri, skll, drop=55, label="feeds next run", dashed=True, color="grey")

# ── Lane 2: Sub-agent dispatch ───────────────────────────────────────────────
R2Y = R1Y + IH + 110
s.label("Sub-agent dispatch", 40, R2Y - 24, size=13, color="grey", align="left")

# left track: Trias / Dialectic → consilium-subagent
disp = s.box("Trias / Dialectic\ndispatch",         40,  R2Y, 200, IH, fill="grey", font_size=13)
csub = s.box("consilium-subagent\n(isolated Seq.)", 290, R2Y, 215, IH, fill=AGG,    font_size=13)
s.arrow(disp, csub)
s.label("isolated Sequential; returns canonical JSON report", 40, R2Y + IH + 8, size=12, color="grey", align="left")

# right track: Step 7 → consilium-implement-subagent
s7   = s.box("Step 7",                        555,  R2Y, 110, IH, fill="orange", font_size=13)
cimp = s.box("consilium-implement\n-subagent", 715,  R2Y, 225, IH, fill=AGG,     font_size=13)
ctr  = s.box("Coder ->\nTest || Review",      990,  R2Y, 170, IH, fill=CTRL,    font_size=13)
rgg  = s.box("red->green\ngate",              1210, R2Y, 145, IH, fill=CONS,    font_size=13)
s.arrow(s7,  cimp)
s.arrow(cimp, ctr)
s.arrow(ctr, rgg)
s.label("files + manifest written to disk", 555, R2Y + IH + 8, size=12, color="grey", align="left")

# ── Lane 3: Git automation + CI + Plugin distribution ───────────────────────
R3Y = R2Y + IH + 90
s.label("Automation & distribution", 40, R3Y - 24, size=13, color="grey", align="left")

# git / CI track
hook  = s.box("Stop hook\n(commit.ps1)",          40,  R3Y, 190, IH, fill="grey",   font_size=13)
ci    = s.box("GitHub CI\n(.github/workflows/)",  280, R3Y, 215, IH, fill="grey",   font_size=13)
gates = s.box("17 tests + run_evals\n+ drift gates", 545, R3Y, 225, IH, fill=CONS, font_size=13)
s.arrow(hook, ci)
s.arrow(ci, gates, label="all green gate")

# plugin distribution track
plug  = s.box(".claude-plugin\nplugin.json",         820,  R3Y, 200, IH, fill="yellow", font_size=13)
mkt   = s.box("marketplace\nalxmax/Consilium_Demo",  1070, R3Y, 220, IH, fill="yellow", font_size=13)
inst  = s.box("/plugin install\nconsilium",           1340, R3Y, 175, IH, fill="grey",   font_size=13)
s.arrow(plug, mkt)
s.arrow(mkt, inst, label="one-step")

s.label(
    "CLAUDE_HEADLESS=1 — suppress user prompts, skip consent gates, "
    "auto-backfill stale PENDs; used by CI and parent orchestrators.",
    40, R3Y + IH + 14, size=12, color="grey", align="left",
)

# ═══════════════════════════════════════════════════════════════════════════
# SAVE
# ═══════════════════════════════════════════════════════════════════════════
out_dir = sys.argv[1] if len(sys.argv) > 1 else "docs"
pj, ph = s.save("consilium_full", out_dir=out_dir)
print(f"elements: {len(s.elements)}")
print(f"wrote:    {pj}")
print(f"wrote:    {ph}")
