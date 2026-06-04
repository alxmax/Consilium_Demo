"""Check that mode docs (modes/*.md, docs/architecture/src/*.jsx) match the
authoritative behavior in SKILL.md and scripts/confidence.py.

Stdlib-only. Exit 0 = OK, exit 1 = drift detected, exit 2 = malformed input.

Origin: Senate audit 2026-05-28 (runs/senate/2026-05-28_094832-doc-drift-ssot-mode-docs.json)
found 4 discrepancies between docs/architecture/ (CV-visible explainer) and the
authoritative behavior in modes/*.md + scripts/confidence.py + SKILL.md. Track 1
(fix/docs-arch-drift-sync, commit 2114f21) fixed the 4 drifts; this script is
Track 2 — enforces the invariants so the same drifts cannot recur silently.

Prior precedent: .consilium/runs/2026-05-25_160009-modes-dir-frontmatter-refactor.json
chose YAML frontmatter as the single source of truth for mode structured fields.
That outcome was marked OK but the 4 drifts found 3 days later proved frontmatter
alone is insufficient — the missing piece is enforcement (this script).

Each invariant has:
- `required`: a regex pattern that MUST appear in the file
- `forbidden` (optional): a regex pattern that MUST NOT appear in the file
- `source`: the authoritative source the invariant derives from

Usage:
    python -X utf8 scripts/check_doc_drift.py
"""
# implements: CONSILIUM-CHECK-DOC-DRIFT-001

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _read(rel_path: str) -> str:
    p = REPO_ROOT / rel_path
    if not p.exists():
        print(f"check_doc_drift: missing file {rel_path}", file=sys.stderr)
        sys.exit(2)
    return p.read_text(encoding="utf-8")


def _extract_confidence_values() -> dict[str, float | None]:
    """Parse VOTE_PATTERN_CONFIDENCE from scripts/confidence.py via AST."""
    src = _read("scripts/confidence.py")
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "VOTE_PATTERN_CONFIDENCE":
                    return ast.literal_eval(node.value)
    print("check_doc_drift: VOTE_PATTERN_CONFIDENCE not found in confidence.py", file=sys.stderr)
    sys.exit(2)


def _extract_trias_jsx_outcomes() -> dict[str, float | None]:
    """Parse TRIAS_OUTCOMES rows from docs/architecture/src/trias.jsx.

    Returns {pattern: conf} where pattern is normalized to ASCII hyphens
    (jsx uses en-dash). Patterns like '3-0', '2-1', '2-0', '1-1-1', '0-0-0'.
    """
    src = _read("docs/architecture/src/trias.jsx")
    # Each row looks like: { p: '2-1', label: '...', desc: '...', conf: 0.75, ...}
    # Use a tolerant regex that captures p and conf together.
    pattern = re.compile(
        r"\{\s*p:\s*['\"]([^'\"]+)['\"][^}]*?conf:\s*([0-9.]+|null)",
        re.DOTALL,
    )
    out: dict[str, float | None] = {}
    for p_raw, conf_raw in pattern.findall(src):
        p_ascii = p_raw.replace("–", "-").replace("—", "-")
        out[p_ascii] = None if conf_raw == "null" else float(conf_raw)
    return out


# ---------------------------------------------------------------------------
# Invariants (text-based)
# ---------------------------------------------------------------------------

INVARIANTS = [
    {
        "id": "trias_parallel_dispatch",
        "file": "modes/trias.md",
        "required": r"[Dd]ispatch\s+all\s+3\s+personalities\s+in\s+parallel|in\s+parallel.*personalities|parallel\s+dispatch.*personalities",
        "forbidden": r"For\s+each\s+personality,\s+dispatch\s+\*\*1\s+`consilium-subagent`\*\*",
        "source": "Senate 2026-05-28 audit + benchmark task-08 timeout (sequential loop)",
        "rationale": "Trias must dispatch 3 sub-agents in parallel; sequential loop triples wall-clock and caused task-08 to time out at 15min in n=10 benchmark.",
    },
    {
        "id": "trias_parallelism_runtime_audit",
        "file": "modes/trias.md",
        "required": r"benchmark/scripts/check_trias_parallelism\.py|check_trias_parallelism\.py",
        "source": "Senate 2026-05-28 (trias-parallelism-enforcement.json) — Tacitus: 'pin enforcement at orchestrator/drift-checker, NOT voice prompts'",
        "rationale": "Spec prose alone has 0/6 clean-GO historical record for dispatch enforcement (per Tacitus retrospective on 6 prior runs). modes/trias.md MUST reference the runtime audit script that detects serial dispatch from JSONL transcripts. Removing the audit reference without removing the parallel mandate leaves a hidden, unmeasured drift — the exact gap this invariant prevents.",
    },
    {
        "id": "sequential_scale_down_skips_pipeline",
        "file": "modes/sequential.md",
        "required": r"scale_down.*SHORT-CIRCUIT.*Skip\s+Generator\s+AND\s+Control",
        "forbidden": r"scale_down.*ADAPT_SHORT.*max\s+2\s+candidates",
        "source": "SKILL.md Step 2 + benchmark 10/10 sequential runs (pipeline_executed=false)",
        "rationale": "Conservator scale_down skips Generator AND Control entirely per SKILL.md authoritative; old description 'ADAPT_SHORT max 2 candidates' implied Generator ran, which contradicts pipeline_audit.json output.",
    },
    {
        "id": "parallel_auto_is_two_turn",
        "file": "docs/architecture/src/modes.jsx",
        "required": r"parallel_auto[\s\S]*?(Two-turn|two-turn|Turn 1[\s\S]*?Turn 2)",
        "forbidden": r"parallel_auto[\s\S]*?true\s+3-way\s+(parallel\s+)?isolation",
        "source": "SKILL.md §'How (2 turns)' — Turn 1=Generator alone, Turn 2=Control+Conservator parallel with candidates",
        "rationale": "Control needs candidates to verdict and Conservator needs them to assess risk; true 3-way isolation breaks this data dependency. SKILL.md explicitly describes the 2-turn flow.",
    },
    {
        "id": "build_report_emits_pipeline_executed",
        "file": "scripts/build_report.py",
        "required": r'"pipeline_executed":\s*True',
        "source": "validate_report.py _validate_pipeline_executed() requires the field for non-skipped reports",
        "rationale": "Trias R1 vote (Pioneer 2026-05-28): consumers of runs/*.json cannot distinguish full-pipeline runs from scale_down short-circuits without this field. build_report.py is the canonical emitter for non-skipped reports — it MUST always set pipeline_executed: True. Hand-built bypass templates (trivial-direct, prior-deliberation) set False in SKILL.md.",
    },
    {
        "id": "skill_templates_have_pipeline_executed",
        "file": "SKILL.md",
        "required": r'"pipeline_executed":\s*false',
        "source": "SKILL.md Step 2 scale_down short-circuit + §'Prior-deliberation passthrough' templates",
        "rationale": "Bypass templates in SKILL.md (scale_down trivial-direct, prior-deliberation passthrough) construct reports by hand without build_report.py. They MUST include pipeline_executed: false so validate_report.py accepts them. If this disappears from SKILL.md, all headless scale_down runs will start failing validation silently.",
    },
    {
        "id": "trias_tally_caption_confidence",
        "file": "docs/architecture/src/modes.jsx",
        "required": r"2-1\s*→\s*0\.75",
        "forbidden": r"2-1\s*→\s*0\.70",
        "source": "scripts/confidence.py VOTE_PATTERN_CONFIDENCE (2-1=0.75, 2-0=0.70); explainer audit 2026-05-30",
        "rationale": "The Trias walkthrough tally caption in modes.jsx is prose, NOT the TRIAS_OUTCOMES table that check_trias_confidence_parity scans, so it drifted to '2-1 → 0.70' (the 2-0 value). It must state the 2-1 confidence as 0.75 to match confidence.py.",
    },
    {
        "id": "costscatter_parallel_cost_parity",
        "file": "docs/architecture/src/extras.jsx",
        "required": r"id:\s*'PAR'[\s\S]*?cost:\s*'3×\s*\(auto\)'",
        "forbidden": r"'1×\s*\(auto\)'",
        "source": "SKILL.md §Dispatch defaults (Parallel = 3 sub-agents = 3×) + extras.jsx CostBars parallel cost:3.0; explainer audit 2026-05-30",
        "rationale": "CostScatter MODES_PLOT plotted Parallel at 1× (auto), contradicting SKILL.md (3 sub-agents = 3×) AND the sibling CostBars panel in the same file. The PAR scatter point must read 3× (auto); no mode is 1× (auto).",
    },
    {
        "id": "parallel_auto_gen_dependency_edges",
        "file": "docs/architecture/src/modes.jsx",
        "required": r"parallel_auto[\s\S]*?gen_cons",
        "forbidden": r"orch_ctl",
        "source": "SKILL.md §'How (2 turns)' — Turn 2 = Generator's candidates → (Control ∥ Conservator); explainer audit 2026-05-30",
        "rationale": "The parallel_auto diagram must draw the Gen→(Conservator ∥ Control) data dependency (gen_cons / gen_ctl edges), not a flat orchestrator→all-three fan-out (orch_ctl). The 'done' step regressed to orch_cons/orch_gen/orch_ctl, implying the orchestrator dispatches Control directly without Generator's candidates.",
    },
]


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


def check_text_invariants() -> list[str]:
    failures: list[str] = []
    for inv in INVARIANTS:
        content = _read(inv["file"])
        req = inv["required"]
        if not re.search(req, content):
            failures.append(
                f"[{inv['id']}] {inv['file']}: required pattern not found\n"
                f"  pattern: {req}\n"
                f"  source:  {inv['source']}\n"
                f"  why:     {inv['rationale']}"
            )
        forbidden = inv.get("forbidden")
        if forbidden and re.search(forbidden, content):
            failures.append(
                f"[{inv['id']}] {inv['file']}: forbidden pattern present\n"
                f"  pattern: {forbidden}\n"
                f"  source:  {inv['source']}\n"
                f"  why:     {inv['rationale']}"
            )
    return failures


def check_trias_confidence_parity() -> list[str]:
    """Invariant 4: trias.jsx TRIAS_OUTCOMES must match confidence.py VOTE_PATTERN_CONFIDENCE."""
    failures: list[str] = []
    auth = _extract_confidence_values()
    jsx = _extract_trias_jsx_outcomes()
    # Check 2-1 and 2-0 specifically (the ones that drifted).
    for pattern in ("2-1", "2-0", "3-0"):
        if pattern not in auth:
            failures.append(
                f"[trias_confidence_parity] confidence.py missing pattern {pattern!r}"
            )
            continue
        if pattern not in jsx:
            failures.append(
                f"[trias_confidence_parity] trias.jsx TRIAS_OUTCOMES missing pattern {pattern!r}"
            )
            continue
        if auth[pattern] != jsx[pattern]:
            failures.append(
                f"[trias_confidence_parity] {pattern}: confidence.py={auth[pattern]} "
                f"vs trias.jsx={jsx[pattern]}\n"
                f"  source: scripts/confidence.py VOTE_PATTERN_CONFIDENCE (authoritative)\n"
                f"  fix:    update docs/architecture/src/trias.jsx TRIAS_OUTCOMES + run build.py"
            )
    return failures


# ---------------------------------------------------------------------------
# Legacy MODE enum removal milestone (Tacitus R1 pattern D)
# ---------------------------------------------------------------------------

REMOVAL_MILESTONES: dict[str, str] = {
    # alias -> dated removal milestone (ISO date). Removed after that date.
    "parallel_skeptic": "2026-08-17",   # collapsed 2026-05-17, +3mo
    "dialectic_skeptic": "2026-08-17",  # collapsed 2026-05-17, +3mo
    "trias_split": "2026-08-21",        # deprecated 2026-05-21, +3mo
}


def check_legacy_mode_milestone() -> list[str]:
    """Verify legacy MODE aliases in validate_report.py carry a dated removal note."""
    failures: list[str] = []
    src = _read("scripts/validate_report.py")
    for alias, milestone_date in REMOVAL_MILESTONES.items():
        if alias not in src:
            # Already removed — that's fine, milestone reached.
            continue
        # Require a comment containing the milestone date near the alias line.
        # Tolerant: the date must appear within 200 chars of the alias literal.
        idx = src.find(f'"{alias}"')
        if idx < 0:
            continue
        window = src[max(0, idx - 200): idx + 200]
        if milestone_date not in window:
            failures.append(
                f"[legacy_mode_milestone] {alias!r}: removal date {milestone_date} not declared\n"
                f"  fix: add comment '# remove after {milestone_date}' adjacent to the alias entry"
            )
    return failures


# ---------------------------------------------------------------------------
# Test-suite coverage (audit 2026-05-31)
# ---------------------------------------------------------------------------


def check_test_suite_coverage() -> list[str]:
    """Every scripts/test_*.py must be gated in BOTH ci.yml and the run-consilium driver.

    Prevents the test-drift class that let test_lens_bias.py sit RED on `main`
    unnoticed (audit 2026-05-31): a suite present on disk that no gate runs. Keeps
    the explicit named CI steps — this only fails the build if a suite is added
    without being wired into both gates.
    """
    failures: list[str] = []
    test_files = sorted(p.name for p in (REPO_ROOT / "scripts").glob("test_*.py"))
    if not test_files:
        return failures
    ci = _read(".github/workflows/ci.yml")
    driver = _read(".claude/skills/run-consilium/driver.py")
    for name in test_files:
        if name not in ci:
            failures.append(
                f"[test_suite_coverage] {name} is not gated in .github/workflows/ci.yml\n"
                f"  fix: add a step `run: python scripts/{name}` to the green-gate job"
            )
        if name not in driver:
            failures.append(
                f"[test_suite_coverage] {name} is not gated in run-consilium driver.py smoke()\n"
                f"  fix: add {name!r} to the test-suite loop in smoke()"
            )
    return failures


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    all_failures: list[str] = []
    all_failures.extend(check_text_invariants())
    all_failures.extend(check_trias_confidence_parity())
    all_failures.extend(check_legacy_mode_milestone())
    all_failures.extend(check_test_suite_coverage())

    if not all_failures:
        print("doc-drift OK: all invariants hold", flush=True)
        return 0

    print(f"doc-drift FAIL: {len(all_failures)} invariant(s) violated", file=sys.stderr)
    for i, f in enumerate(all_failures, 1):
        print(f"\n{i}. {f}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
