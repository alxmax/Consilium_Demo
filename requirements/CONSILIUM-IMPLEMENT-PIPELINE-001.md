---
milestone: v1.0
id: CONSILIUM-IMPLEMENT-PIPELINE-001
status: confirmed
layer: feature
owner: auto
depends_on: [CONSILIUM-UTILS-001]
risk: 1
---

# implement_pipeline

> Turns a deliberation report into an implementation dispatch plan; optionally verifies the red->green gate.

## Input
- Deliberation report JSON - via `--input <path>` or stdin
- CLI flags: `--dry-run`, `--verify-gate`, `--test-cmd`, `--target`, `--stub-marker`

## Description
Turns a completed Consilium deliberation report into a structured implementation dispatch plan (Coder -> Test Writer || Reviewer) and optionally verifies the red->green test gate. In planning mode it extracts `chosen_approach`, `success_criterion`, and `verification` from the report, maps the three roles to their prompt files, and emits a JSON plan for the orchestrating agent to consume; it is a planner, not a dispatcher - the `consilium-implement-subagent.md` agent performs actual sub-agent calls. In gate-verification mode it runs the real test suite (expect GREEN / exit 0) and then rewrites the target file with stub bodies (a heuristic line-scanner that inserts `raise NotImplementedError` after each `def`/`async def`) to confirm the suite fails RED, restoring the original in a `finally` block regardless of outcome. The script exits 1 for `do_nothing`/`skipped` chosen approaches and 2 for malformed input.

## Output
- stdout (plan mode): human-readable plan summary followed by `{"plan": ...}` JSON
- stdout (gate mode): `{"red_ok": bool, "green_ok": bool, "gate_passed": bool}` JSON
- exit code 0 on success/dry-run/gate passed, 1 on no-pipeline or gate failure, 2 on bad input

## WHAT — Verify intent
- None - all questions resolved.

## Contract
- The stub heuristic appends the stub marker as a new line after the `def`/`async def` header; it does not replace an existing `pass` or `...` body. Nested functions each receive their own stub insertion. This is intentional: the gate only needs the suite to go RED, not a clean AST rewrite.
- Exit code 1 is shared between `do_nothing`/`skipped` (no pipeline) and gate failure. The caller must read stdout to distinguish the two cases. This collapse is intentional and documented in the script's module docstring.
- The plan JSON schema (`spec`, `sequence`, `roles`, `rules`) is defined entirely by `build_plan()` in this script. The subagent handoff contract lives in `agents/consilium-implement-subagent.md` and is not part of this requirement.

## Acceptance (= tests)
- Given a report with a non-empty `chosen_approach`, `build_plan` returns a dict with `spec`, `sequence`, `roles`, and `rules` keys, and each role lists whether its prompt file exists.
- Given `chosen_approach` of `do_nothing` or `skipped`, the script prints a message and exits 1.
- In `--verify-gate` mode, `gate_passed` is `true` only when the real suite passes (exit 0) AND the stubbed suite fails (exit non-0).
- The `verify_red_green` function always restores the original target file content, even when the test command raises or the stubbed run crashes.
- Omitting `--test-cmd` or `--target` with `--verify-gate` causes exit 2 with an error message to stderr.
