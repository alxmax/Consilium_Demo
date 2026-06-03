---
id: CONSILIUM-MODE-DIALECTIC-001
status: baseline
layer: feature
owner: auto
depends_on: [CONSILIUM-MODE-SEQUENTIAL-001, CONSILIUM-VOICE-SKEPTIC-001]
---

# dialectic mode

> WHY: Add a focused post-hoc challenge on the chosen approach for code changes — Sequential deliberation plus code-context injection, followed unconditionally by a Skeptic sub-agent regardless of confidence band.

## WHAT — Contract (normative)
- The mode shall inject code-specific context (`language`, `framework`, `build_command`, `files_touched[]`, `test_files[]`, `ci_gate`) into voice inputs (not into prompt files) before running the standard Sequential deliberation (Conservator → Generator → Control).
- After Sequential produces `chosen`, the mode shall unconditionally dispatch 1 Skeptic sub-agent (`skeptic_on_chosen`) on the result — not gated on confidence band and not skipped when Sequential short-circuits via `scale_down`; skipping the Skeptic on scale_down would collapse Dialectic into bare Sequential.
- The total cost shall be 1.33× Sequential (1× Sequential + 1 Skeptic sub-agent); telemetry shall record `mode: "dialectic"` and, when the Skeptic catches a constraint, `skeptic_caught_constraint: true` in the report.
- The Skeptic's verification claim shall be concrete (a named test, a build command, or a CI check); the Skeptic's verdict is advisory by default and can override `chosen` only when `--skeptic-can-override` is active and Skeptic produces `addressable: requires_redesign`.

## WHAT — Verify intent (open questions for the human)
- Observed: the spec states the Skeptic runs "not conditional on confidence band", yet `skeptic_on_chosen.md` describes auto-trigger conditions including `confidence ∈ [0.0, 0.7]`. In Dialectic, is the Skeptic always unconditional (ignoring the confidence band entirely), or does the same auto-trigger logic apply here too?

## WHAT — Notes & known limitations (informative)
- The old Dialectic (Pass1+Pass2 via `scripts/deprecated/dialectic_merge.py`) is retired; `prompts/voices/*_pass2.md` remain on disk for reference but are not dispatched.
- Historical runs with `mode: "dialectic"` from the old Pass1+Pass2 implementation are preserved and recognized by `validate_report.py` for backward-compat.

## HOW — Acceptance (= tests)
AC-1
  Given a deliberation request in dialectic mode with language/framework/files_touched provided
  When  the mode runs
  Then  Sequential completes (Conservator → Generator → Control) with code-context fields present in each voice input, followed by exactly 1 Skeptic sub-agent dispatch, and the report records `mode: "dialectic"`

AC-2
  Given a deliberation where Sequential's Step 2 short-circuits via `scale_down` (trivial-direct chosen)
  When  the mode runs
  Then  the Skeptic sub-agent is still dispatched on the trivial-direct chosen, and the report does not resemble a bare Sequential output

AC-3
  Given a Skeptic output with `can_object: true`, `concrete_concerns` ≥ 2, and `--skeptic-can-override` is NOT active
  When  the mode finalizes the report
  Then  `chosen` is unchanged from the Sequential result, `skeptic_caught_constraint: true` is set in the report, and the objection is visible to the user as advisory

## WHERE — Current implementation
- modes/dialectic.md
