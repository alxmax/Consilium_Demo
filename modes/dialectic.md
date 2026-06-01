---
name: dialectic
subagents: 1
cost_multiplier: 1.33
confidence_floor: 0.75
models: sonnet
dispatch_count: 4
description: Sequential + 1 Skeptic sub-agent. Code-specialized context injection. Opt-in.
---

# Dialectic mode (opt-in)

**Mechanics:** Standard Sequential (Conservator→Generator→Control) with code-specific context injected into the voice inputs, followed by `skeptic_on_chosen`. Cost: 1.33× Sequential (1× Sequential + 1/3 for Skeptic sub-agent). No new prompt files — context is injected via the voice input fields.

**Old Dialectic (Pass1+Pass2) archived.** `scripts/deprecated/dialectic_merge.py` is the retired implementation. `prompts/voices/*_pass2.md` remain on disk for reference but are not dispatched.

## Code-context injection

Inject into each voice's input (not into the prompt file):
- `language` + `framework` + `build_command` (e.g. `pytest -x`, `cargo test`)
- `files_touched[]` — list of affected files with their roles
- `test_files[]` — existing test files the change must not break
- `ci_gate` — the check that must pass before merge

This injection activates code-specific reasoning in the existing voices without new prompt files.

## Skeptic stage

After Sequential produces `chosen`, always dispatch `skeptic_on_chosen` (not conditional on confidence band). The Skeptic receives the chosen + `success_criterion` + the code context. The verification claim must be concrete: a named test, a build command, or a CI check.

**Skeptic runs on scale_down too.** When Sequential's Step 2 short-circuits via Conservator `scale_down` (Gen+Ctrl skipped, `chosen_approach: "trivial-direct"`), the Skeptic stage STILL dispatches on the trivial-direct chosen. Cost-aware skipping of Gen+Ctrl is fine; skipping Skeptic would collapse Dialectic into bare Sequential and defeat the mode. See SKILL.md Step 2 "Dialectic mode exception (scale_down + Skeptic)" for the override. Motivating empirical case: 2026-05-28 benchmark validation (`experiments/dialectic-skeptic-on-scale-down-validation-2026-05-28.md`).

## When to use
- Code change where implementation strategy and verification strategy are both non-obvious
- You want a focused challenge on the chosen approach post-deliberation
- Medium-stakes refactor (2–5 files) where Sequential alone feels thin

## Workflow
1. Inject code-context into voice inputs (language, files, test suite, CI gate)
2. Run Sequential (Conservator→Generator→Control) — standard Steps 2–4. **If Sequential Step 2 short-circuits via scale_down**, the trivial-direct chosen becomes the input to Step 3 (do NOT exit the workflow as bare Sequential would).
3. Run `skeptic_on_chosen` unconditionally (not gated on confidence band, not gated on whether Gen+Ctrl ran). Input: `chosen` + `success_criterion` + code context.
4. Aggregate + confidence as normal (Steps 5–5b)
5. If Skeptic catches constraint: `skeptic_caught_constraint: true` in report; advisory by default, `--skeptic-can-override` for opt-in override

**telemetry.mode** for this mode: `"dialectic"`. Legacy runs with mode `"dialectic"` (old Pass1+Pass2) are preserved in `.consilium/runs/` with no schema change — `validate_report.py` keeps `"dialectic"` in `_MULTI_VOICE_MODES`.
