---
name: implement_pipeline
subagents: 3
cost_multiplier: 1.1
cost_note: "~1.1× tokens vs single-shot; 3–7× wall-clock (parallel stage)"
models: sonnet
description: Post-deliberation implementation pipeline — Coder → (Test Writer ∥ Reviewer). Default for regression-risk changes. The report is the spec.
---

# Implementation pipeline (Step 7, regression-risk default)

Post-deliberation pipeline that turns a Consilium report into working, tested, reviewed code. Three roles operate in two sequential stages; the report (`chosen_approach` + `success_criterion` + `verification`) is the spec — no separate brief needed.

## When to use

Routing is automatic via `recommend_implement_mode(report)` in `infer_pipeline.py`, keyed on **regression risk, not size**:

| magnitude | reversibility | mode |
|---|---|---|
| trivial / moderate | complete | single-shot |
| moderate | irreversible | **pipeline** |
| high | partial / irreversible | **pipeline** |
| critical | any | **pipeline** |

Greenfield (even large, fully reversible) stays single-shot. The routing decision is advisory — the user may override at the Step 7 prompt (`n`) or via `--dry-run`.

## Roles

| Role | Stage | Prompt | Path contract |
|---|---|---|---|
| **Coder** | 1 (sequential) | `prompts/implement/coder.md` | writes impl files |
| **Test Writer** | 2 (parallel) | `prompts/implement/test_writer.md` | writes `test_*` files only |
| **Reviewer** | 2 (parallel) | `prompts/voices/control.md` | read-only — no writes |

Reviewer reuses the Control voice on the *written* code (not the proposal). No separate reviewer prompt.

## Invariants

- **Disjoint-path ownership** — Coder writes impl; Test Writer writes `test_*`; Reviewer is read-only. Parallel stage is collision-free by construction.
- **Malformed-JSON hard-fail** — retry once, then abort. Never a silent-empty manifest.
- **Red→green gate** — a test that passes against a `raise NotImplementedError` stub is rejected. Tests must pin real behavior.

## Commands

```bash
# Plan only (dry-run)
python -X utf8 scripts/implement_pipeline.py --input .consilium/runs/<file>.json --dry-run

# Verify the red→green gate on an already-written impl
python -X utf8 scripts/implement_pipeline.py --verify-gate --test-cmd "pytest -x" --target <impl_file>

# Dispatch (orchestrator calls this after routing decision)
# Agent(subagent_type="consilium-implement-subagent", prompt=<inlined plan + spec>)
```

Dispatch vehicle: `agents/consilium-implement-subagent.md`. Returns a file manifest + Control verdict (not a `runs/<file>.json` deliberation report).

## Red→green gate

`--verify-gate` runs the suite twice:

1. **GREEN run** — real implementation. Must exit 0.
2. **RED run** — stub that replaces every function body with `raise NotImplementedError`. Must exit non-zero.

A test that passes the stub provides no regression protection and is rejected (`gate_passed: false`).

`_stub_bodies()` in `implement_pipeline.py` handles multi-line function headers. Known heuristic limits: `def`-like tokens inside string literals are treated as real headers; a multi-line header whose intermediate line ends with `:` closes the scan early. Both are acceptable for the gate's falsification purpose.

## Benchmark

Combined R1+R2 (n=6, hidden oracle; `experiments/pipeline-bench/RESULTS.md`):
**1 win / 5 ties / 0 losses** vs plain single-shot at ~1.1× tokens / 3–7× wall-clock.

The win: a refactor with a semantically-isolated secondary branch — Reviewer caught a second-code-path defect the single-shot shipped. On greenfield and algebraically-obvious tasks the base model nailed the edges (ties). Graduation criterion (≥2/3 wins) not met — promoted on user decision (2026-05-25).

Audit trail: `runs/2026-05-25_2140_pipeline-step7-default.json`.

## Skip conditions

- `chosen_approach` is `do_nothing` or `skipped` — `implement_pipeline.py` exits 1 with a clear message.
- Headless (`claude -p`): run `infer_pipeline.py --yes` (non-interactive).
- **Exception:** if the prompt declares deliverables (authoritative regex: `\*\*\s*(?:Required\s+output\s+files?|Deliverables?)\s*\*\*\s*:?`) and deliberation returns `do_nothing`, that is a hard error requiring a visible user signal — not a silent skip.
