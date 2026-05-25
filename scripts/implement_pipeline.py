"""Plan + gate-verify the post-deliberation implementation pipeline.

Companion to ``infer_pipeline.py``. Where that script infers *which* steps apply,
this one turns a completed Consilium report into an implementation *dispatch plan*
(Coder -> Test Writer || Reviewer) and provides the red->green test gate verifier.

Like ``infer_pipeline.py``, this is a **planner**, not a dispatcher: the orchestrating
agent (``agents/consilium-implement-subagent.md``) performs the actual sub-agent
dispatch. This script only (a) extracts the spec + role->prompt mapping, and (b)
empirically verifies the red->green gate when asked.

> Status: default for regression-risk changes (promoted 2026-05-25). Routing via
> recommend_implement_mode() in infer_pipeline.py. See SKILL.md Step 7.

Usage:
    python scripts/implement_pipeline.py --input runs/<file>.json --dry-run
    python scripts/implement_pipeline.py --input runs/<file>.json          # prints plan JSON
    python scripts/implement_pipeline.py --verify-gate --test-cmd "pytest -x" --target solution.py

Flags:
    --dry-run      Print the dispatch plan and exit 0 (no side effects).
    --verify-gate  Run the red->green gate instead of planning (needs --test-cmd + --target).
    --test-cmd     Test command for the gate (e.g. "pytest -x").
    --target       Implementation file the gate stubs to produce the RED run.
    --stub-marker  Body injected to stub the target (default: "raise NotImplementedError").

Exit codes:
    0   Plan printed / dry-run complete / gate passed.
    1   chosen_approach is do_nothing/skipped (no pipeline), or gate failed.
    2   Input invalid (JSON parse error, missing fields, or bad gate args).
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import shlex
import subprocess
import sys

from utils import force_utf8_streams

_SKILL_ROOT = pathlib.Path(__file__).parent.parent

# Role -> prompt template. Reviewer reuses the existing Control voice (no reviewer.md).
_ROLE_PROMPTS = {
    "coder": "prompts/implement/coder.md",
    "test_writer": "prompts/implement/test_writer.md",
    "reviewer": "prompts/voices/control.md",
}


def build_plan(report: dict) -> dict:
    """Return the implementation dispatch plan from a deliberation report.

    Raises ValueError if chosen_approach is do_nothing/skipped (no pipeline).
    """
    chosen = report.get("chosen_approach")
    if chosen in ("do_nothing", "skipped", None, ""):
        raise ValueError(f"chosen_approach={chosen!r} — no implementation pipeline to run")

    spec = {
        "chosen_approach": chosen,
        "success_criterion": report.get("success_criterion", ""),
        "verification": report.get("verification", ""),
    }
    roles = [
        {"role": role, "prompt_path": path, "exists": (_SKILL_ROOT / path).is_file()}
        for role, path in _ROLE_PROMPTS.items()
    ]
    return {
        "spec": spec,
        "sequence": "coder -> (test_writer || reviewer)",
        "roles": roles,
        "rules": {
            "disjoint_paths": "coder writes impl; test_writer writes test_*; reviewer read-only",
            "malformed_json": "hard-fail; retry once then abort",
            "gate": "tests must be RED on stub, GREEN on real impl",
        },
    }


def _run(test_cmd: str) -> int:
    """Run a test command, return its exit code (non-zero = failing/RED)."""
    return subprocess.run(shlex.split(test_cmd), cwd=str(pathlib.Path.cwd())).returncode


def verify_red_green(
    test_cmd: str,
    target_file: str,
    stub_marker: str = "raise NotImplementedError",
) -> dict:
    """Run the suite against the real impl (expect GREEN) and a stubbed copy (expect RED).

    Never mutates the real target permanently: the original is restored from a backup.
    A green run on the stub means the tests do not pin behavior -> gate fails.
    """
    target = pathlib.Path(target_file)
    if not target.is_file():
        return {"error": f"target not found: {target_file}", "gate_passed": False}

    original = target.read_text(encoding="utf-8")

    # GREEN run: real implementation should pass (exit 0).
    green_code = _run(test_cmd)
    green_ok = green_code == 0

    # RED run: stub every def/async-def body, suite should now fail (exit != 0).
    stubbed = _stub_bodies(original, stub_marker)
    backup = target.with_suffix(target.suffix + ".redgreen.bak")
    red_ok = False
    try:
        backup.write_text(original, encoding="utf-8")
        target.write_text(stubbed, encoding="utf-8")
        red_code = _run(test_cmd)
        red_ok = red_code != 0
    finally:
        target.write_text(original, encoding="utf-8")
        if backup.exists():
            backup.unlink()

    return {
        "red_ok": red_ok,
        "green_ok": green_ok,
        "gate_passed": red_ok and green_ok,
    }


def _stub_bodies(source: str, stub_marker: str) -> str:
    """Replace each function body's first statement region with the stub marker.

    Heuristic + stdlib-only: after every line ending a `def ...:` / `async def ...:`
    header, insert the stub at the header's indent+4. This forces the suite RED
    without a full AST rewrite (sufficient for the gate's falsification purpose).

    Handles multi-line headers: once a `def`/`async def` opener is seen without
    a trailing `:`, lines are accumulated until one ends with `:`, then the stub
    is inserted at the opener's indent+4.

    Known heuristic limits (acceptable for the gate — it stubs normal impl files):
    a multi-line header whose *intermediate* line ends with `:` closes the scan
    early, and a `def`-like token inside a string literal is treated as a real
    header. Both are inherent to a line-scanner; use AST if these ever bite.
    """
    out: list[str] = []
    opener_re = re.compile(r"^(\s*)(async\s+def|def)\s+\w+")
    in_header = False
    header_indent: str = ""
    for line in source.splitlines():
        out.append(line)
        if in_header:
            # Keep accumulating until we see a line ending with ':'
            if line.rstrip().endswith(":"):
                in_header = False
                out.append(f"{header_indent}{stub_marker}")
        else:
            m = opener_re.match(line)
            if m:
                if line.rstrip().endswith(":"):
                    # Single-line header — insert stub immediately
                    indent = m.group(1) + "    "
                    out.append(f"{indent}{stub_marker}")
                else:
                    # Multi-line header — wait for the closing ':'
                    in_header = True
                    header_indent = m.group(1) + "    "
    return "\n".join(out) + ("\n" if source.endswith("\n") else "")


def main() -> None:
    force_utf8_streams()

    parser = argparse.ArgumentParser(
        description="Plan + gate-verify the post-deliberation implementation pipeline.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--input", help="Path to deliberation JSON (default: stdin)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print the dispatch plan and exit (no side effects)")
    parser.add_argument("--verify-gate", action="store_true",
                        help="Run the red->green gate instead of planning")
    parser.add_argument("--test-cmd", help="Test command for the gate (e.g. 'pytest -x')")
    parser.add_argument("--target", help="Implementation file the gate stubs for the RED run")
    parser.add_argument("--stub-marker", default="raise NotImplementedError",
                        help="Body injected to stub the target (default: raise NotImplementedError)")
    args = parser.parse_args()

    if args.verify_gate:
        if not args.test_cmd or not args.target:
            print("implement_pipeline: --verify-gate needs --test-cmd and --target", file=sys.stderr)
            sys.exit(2)
        result = verify_red_green(args.test_cmd, args.target, args.stub_marker)
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(0 if result.get("gate_passed") else 1)

    try:
        if args.input:
            with open(args.input, encoding="utf-8") as f:
                report = json.load(f)
        else:
            raw = sys.stdin.read()
            if not raw.strip():
                print("implement_pipeline: no input — pipe a deliberation JSON or use --input", file=sys.stderr)
                sys.exit(2)
            report = json.loads(raw)
    except (json.JSONDecodeError, FileNotFoundError, OSError) as exc:
        print(f"implement_pipeline: input error: {exc}", file=sys.stderr)
        sys.exit(2)

    try:
        plan = build_plan(report)
    except ValueError as exc:
        print(f"implement_pipeline: {exc}")
        sys.exit(1)

    print(f"\nImplementation pipeline: {plan['sequence']}")
    print(f"  chosen : {plan['spec']['chosen_approach']}")
    for role in plan["roles"]:
        flag = "" if role["exists"] else "  [MISSING]"
        print(f"  {role['role']:<12} <- {role['prompt_path']}{flag}")
    if args.dry_run:
        print("(dry-run — no dispatch)")
    print(json.dumps({"plan": plan}, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
