---
id: CONSILIUM-MODE-SKEPTIC-ON-CHOSEN-001
status: baseline
layer: feature
owner: auto
depends_on: [CONSILIUM-VOICE-SKEPTIC-001]
---

# skeptic_on_chosen flag

> WHY: Compose a focused post-hoc Skeptic challenge on the chosen approach over any base mode — catching implicit constraints and high-concern discrepancies that the base deliberation may have missed.

## WHAT — Contract (normative)
- The flag shall dispatch exactly 1 Skeptic sub-agent (using `prompts/voices/skeptic.md`) after the base mode produces `chosen` and `confidence`; it is composable over any base mode (Sequential, Dialectic, Trias) and adds +1 sub-agent to whichever base was used.
- The flag shall auto-trigger when any of the following are true: `confidence ∈ [0.0, 0.7]`; `confidence > 0.7` AND `Conservator.net_concern > 0.7` (`trigger_reason: "high_conf_high_concern"`); `chosen_approach` matches a BAD outcome from FEEDBACK.html in the last 30 days (`trigger_reason: "similar_to_recent_bad"`); or `irreversibility_flag: true` (`trigger_reason: "irreversibility_gate"`). It may also be activated manually via `--skeptic-on-chosen`.
- The Skeptic sub-agent shall receive only `chosen` (id, summary, sketch, rationale), `success_criterion`, and `verification`; it shall NOT receive other candidates, scores, or deliberation logs. A valid objection requires `can_object: true` with either `concrete_concerns ≥ 2` or a non-null `quoted_scenario`; `can_object: true` without evidence shall be rejected and the original chosen shipped.
- The Skeptic's verdict shall be advisory by default (`chosen` is not replaced); `chosen` is replaced only when `--skeptic-can-override` is active AND the Skeptic produces `addressable: requires_redesign`. The result shall be logged in `deliberation_log` with step `"skeptic_on_chosen"` and `skeptic_caught_constraint: true|false` set in the report.

## WHAT — Verify intent (open questions for the human)
- None — doc is unambiguous.

## WHAT — Notes & known limitations (informative)
- The legacy fixed modes `parallel_skeptic` and `dialectic_skeptic` were collapsed into this composable flag on 2026-05-17; the legacy names remain in `validate_report.py` MODE enum for backward-compat with historical runs.
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
