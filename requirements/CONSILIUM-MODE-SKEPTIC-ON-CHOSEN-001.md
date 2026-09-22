---
milestone: v1.0
test_exempt: "prompt/mode document — acceptance validated by deliberation integration runs, not unit tests"
id: CONSILIUM-MODE-SKEPTIC-ON-CHOSEN-001
status: confirmed
level: code
layer: feature
owner: alxmax
depends_on: [CONSILIUM-VOICE-SKEPTIC-001]
satisfies: [ARCH-CONSILIUM-MODES-001]
---

# skeptic_on_chosen flag

> WHY: Compose a focused post-hoc Skeptic challenge on the chosen approach over any base mode — catching implicit constraints and high-concern discrepancies that the base deliberation may have missed.

## WHAT — Contract (normative)
- The flag dispatches exactly 1 Skeptic sub-agent (using `prompts/voices/skeptic.md`) after the base mode produces `chosen` and `confidence`; the flag is composable over any base mode (Sequential, Dialectic, Trias) and adds +1 sub-agent to whichever base was used.
- The flag auto-triggers when any of the following are true: `Conservator.net_concern > 0.7` on the chosen (`trigger_reason: "high_concern"`); `chosen_approach` matches a BAD outcome from FEEDBACK.html in the last 30 days (`trigger_reason: "similar_to_recent_bad"`); or `irreversibility_flag: true` (`trigger_reason: "irreversibility_gate"`). It may also be activated manually via `--skeptic-on-chosen`. Confidence alone never triggers it: on `[confirmed]` outcomes confidence does not predict success.
- The Skeptic sub-agent receives only `chosen` (id, summary, sketch, rationale), `success_criterion`, and `verification`; it does not receive other candidates, scores, or deliberation logs.
- An objection counts only when it passes the validation gate owned by [[CONSILIUM-VALIDATE-SKEPTIC-001]]; a rejected objection is dropped, and the original chosen ships unchanged.
- The Skeptic's verdict is advisory by default (`chosen` is not replaced); `chosen` is replaced only when `--skeptic-can-override` is active AND the Skeptic produces `addressable: requires_redesign`.
- The result is logged in `deliberation_log` with step `"skeptic_on_chosen"` and `skeptic_caught_constraint: true|false` set in the report.

## WHAT — Verify intent (open questions for the human)
- None — doc is unambiguous.

## WHAT — Notes & known limitations (informative)
- The legacy fixed modes `parallel_skeptic` and `dialectic_skeptic` were collapsed into this composable flag on 2026-05-17; the legacy names remain accepted via `validate_report.py`'s `_LEGACY_MODE_ALIASES` map for backward-compat with historical runs (there is no MODE enum; `telemetry.mode` is not enum-validated).
- Empirical origin (n=1, P3 problem): the equivalent `chosen_confirmation_pass` reached 4/7 catch-rate in real reruns; generalizability to other problems is unconfirmed until ≥3 distinct problems are tested.

## HOW — Acceptance (= tests)
AC-1
  Given a deliberation in Sequential mode where the base mode produces `confidence: 0.65`
  When  the flag auto-triggers
  Then  exactly 1 Skeptic sub-agent is dispatched with only `chosen`, `success_criterion`, and `verification` in its input; the report records `skeptic_caught_constraint: true|false` and `chosen` remains the Sequential result (advisory)

AC-2
  Given a deliberation where the Skeptic produces `can_object: true` with no `concrete_concerns` and no `quoted_scenario`
  When  the flag validates the Skeptic output
  Then  the objection is rejected as a schema fail, the original chosen is shipped unchanged, and the rejection is recorded in `deliberation_log`

AC-3
  Given a deliberation with `--skeptic-can-override` active and the Skeptic produces `addressable: requires_redesign`
  When  the flag applies override semantics
  Then  the orchestrator presents the report's alternatives to the user and asks whether to change the choice, rather than shipping the original chosen

## WHERE — Current implementation
- modes/skeptic_on_chosen.md

## Why test_exempt

This file is a mode specification document — it defines workflow rules, dispatch config (YAML frontmatter), and machine-readable invariants read by the orchestrator and sub-agents at runtime. It contains no executable Python logic. Structural parity between this document and the implemented behavior is enforced by `check_doc_drift.py` invariants; end-to-end conformance is validated through deliberation integration runs.
