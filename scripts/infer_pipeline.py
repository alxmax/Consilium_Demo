"""Infer and confirm implementation pipeline steps from a Consilium deliberation report.

Reads a deliberation JSON (produced by build_report.py), infers which
implementation steps apply based on chosen_approach, magnitude, and reversibility,
then presents them for confirmation before execution.

Usage:
    cat runs/<file>.json | python scripts/infer_pipeline.py
    python scripts/infer_pipeline.py --input runs/<file>.json
    python scripts/infer_pipeline.py --input runs/<file>.json --dry-run
    python scripts/infer_pipeline.py --input runs/<file>.json --yes

Flags:
    --dry-run   Print inferred steps and exit without confirmation or execution.
    --yes       Skip confirmation prompt (CI/headless mode).
    --debug     Emit decision rationale to stderr (source, lookup key, fallback path).

Steps (in order when applicable):
    implement   Write code per chosen_approach (reminder — not automated).
    compile     Run the target module; verify exit code 0 (runtime check).
    review      Re-run Control voice on the actual written code.
    test        Run existing test suite (pytest/unittest autodiscovery).

Exit codes:
    0   Steps confirmed and printed to stdout, or dry-run complete.
    1   User declined, or step inference produced no steps.
    2   Input invalid (JSON parse error or missing required fields).
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys

from utils import RUNS_DIR, force_utf8_streams

# Lookup table: (magnitude, reversibility) -> ordered step list.
# Conservative tie-breaking: most restrictive key wins (see _infer_steps).
_STEP_TABLE: dict[tuple[str, str], list[str]] = {
    ("trivial",  "complete"):    ["implement"],
    ("trivial",  "partial"):     ["implement", "compile"],
    ("trivial",  "irreversible"):["implement", "compile", "test"],
    ("moderate", "complete"):    ["implement", "compile"],
    ("moderate", "partial"):     ["implement", "compile", "test"],
    ("moderate", "irreversible"):["implement", "compile", "review", "test"],
    ("high",     "complete"):    ["implement", "compile", "test"],
    ("high",     "partial"):     ["implement", "compile", "review", "test"],
    ("high",     "irreversible"):["implement", "compile", "review", "test"],
    ("critical", "complete"):    ["implement", "compile", "review", "test"],
    ("critical", "partial"):     ["implement", "compile", "review", "test"],
    ("critical", "irreversible"):["implement", "compile", "review", "test"],
}

# Fallback buckets when conservator fields are missing from the report.
# Maps net_concern range to (magnitude, reversibility).
_CONCERN_BUCKETS = [
    (0.0,  0.15, "trivial",  "complete"),
    (0.15, 0.35, "moderate", "partial"),
    (0.35, 0.65, "high",     "partial"),
    (0.65, 1.01, "critical", "irreversible"),
]


def _extract_conservator_fields(report: dict, chosen: str) -> tuple[str | None, str | None]:
    """Return (magnitude, reversibility) for chosen from deliberation_log."""
    for entry in report.get("deliberation_log", []):
        if entry.get("step") != "conservator":
            continue
        for score in entry.get("scores", []):
            if score.get("id") == chosen:
                rr = score.get("regression_risk", {})
                return rr.get("magnitude"), rr.get("reversibility")
    return None, None


def _fallback_from_concern(net_concern: float) -> tuple[str, str]:
    for lo, hi, mag, rev in _CONCERN_BUCKETS:
        if lo <= net_concern < hi:
            return mag, rev
    return "critical", "irreversible"


def infer_steps(report: dict) -> tuple[list[str], dict]:
    """Return (steps, rationale) from a deliberation report."""
    chosen = report.get("chosen_approach")

    if chosen in ("do_nothing", "skipped", None, ""):
        return [], {"reason": f"chosen_approach={chosen!r} — no steps to run"}

    magnitude, reversibility = _extract_conservator_fields(report, chosen)
    source = "deliberation_log"

    if not magnitude or not reversibility:
        net_concern = report.get("voice_scores", {}).get("conservator", 0.5)
        magnitude, reversibility = _fallback_from_concern(float(net_concern))
        source = f"voice_scores.conservator={net_concern} (fallback)"

    key = (magnitude, reversibility)
    steps = _STEP_TABLE.get(key)

    if steps is None:
        # Key not in table: default to safest full set.
        steps = ["implement", "compile", "review", "test"]
        source += " (key not in table — defaulting to full set)"

    rationale = {
        "chosen": chosen,
        "magnitude": magnitude,
        "reversibility": reversibility,
        "source": source,
        "lookup_key": f"({magnitude}, {reversibility})",
    }
    return list(steps), rationale


def recommend_implement_mode(report: dict) -> str:
    """Route the Step 7 `implement` action: ``"pipeline"`` vs ``"single_shot"``.

    Gate keyed on **regression risk, not size** (benchmark `experiments/pipeline-bench/`:
    the pipeline's only win was a 3-line edit to existing code — a size threshold would
    have mis-routed it). The signal reused here is the `review` step from ``infer_steps``:
    it appears exactly in the regression-prone quadrants (moderate×irreversible,
    high×{partial,irreversible}, critical×any). When `review` is warranted, the change is
    worth the pipeline (Coder → Test Writer ∥ Reviewer); otherwise plain single-shot.

    Advisory only — the orchestrator/user may override. Returns ``"single_shot"`` for
    ``do_nothing``/``skipped`` (no implementation to route).
    """
    steps, _ = infer_steps(report)
    return "pipeline" if "review" in steps else "single_shot"


def _log_rejection(report: dict, steps: list[str], rationale: dict) -> None:
    runs_dir = RUNS_DIR
    if not runs_dir.exists():
        return
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
    entry = {
        "event": "pipeline_rejected",
        "timestamp": timestamp,
        "steps_proposed": steps,
        "rationale": rationale,
        "success_criterion": report.get("success_criterion", ""),
        "chosen_approach": report.get("chosen_approach", ""),
    }
    path = runs_dir / f"{timestamp}_pipeline_rejected.json"
    path.write_text(json.dumps(entry, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    force_utf8_streams()

    parser = argparse.ArgumentParser(
        description="Infer and confirm pipeline steps from a Consilium deliberation report.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--input", help="Path to deliberation JSON (default: stdin)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print steps and exit without confirmation")
    parser.add_argument("--yes", action="store_true",
                        help="Skip confirmation prompt (CI/headless mode)")
    parser.add_argument("--debug", action="store_true",
                        help="Emit decision rationale to stderr")
    args = parser.parse_args()

    try:
        if args.input:
            with open(args.input, encoding="utf-8") as f:
                report = json.load(f)
        else:
            raw = sys.stdin.read()
            if not raw.strip():
                print("infer_pipeline: no input — pipe a deliberation JSON or use --input", file=sys.stderr)
                sys.exit(2)
            report = json.loads(raw)
    except (json.JSONDecodeError, FileNotFoundError, OSError) as exc:
        print(f"infer_pipeline: input error: {exc}", file=sys.stderr)
        sys.exit(2)

    steps, rationale = infer_steps(report)

    if args.debug:
        print(f"[debug] chosen={rationale.get('chosen')!r}", file=sys.stderr)
        print(f"[debug] source={rationale.get('source')!r}", file=sys.stderr)
        print(f"[debug] lookup_key={rationale.get('lookup_key')!r}", file=sys.stderr)
        print(f"[debug] steps={steps!r}", file=sys.stderr)

    if not steps:
        reason = rationale.get("reason", "unknown")
        print(f"infer_pipeline: no steps — {reason}")
        print(json.dumps({"steps": [], "rationale": rationale}, ensure_ascii=False))
        sys.exit(1)

    pipeline_str = " → ".join(steps)
    print(f"\nProposed pipeline: {pipeline_str}")
    print(f"  chosen : {rationale['chosen']}")
    print(f"  profile: {rationale['lookup_key']} (source: {rationale['source']})")

    if args.dry_run:
        print("(dry-run — no confirmation)")
        print(json.dumps({"steps": steps, "rationale": rationale}, ensure_ascii=False))
        sys.exit(0)

    if not args.yes:
        try:
            answer = input("\nProceed? [Y/n] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print(
                "\ninfer_pipeline: non-interactive environment detected — rerun with --yes to skip prompt",
                file=sys.stderr,
            )
            sys.exit(1)
        if answer not in ("", "y", "yes"):
            print("infer_pipeline: declined")
            _log_rejection(report, steps, rationale)
            sys.exit(1)

    print(json.dumps({"steps": steps, "rationale": rationale}, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
