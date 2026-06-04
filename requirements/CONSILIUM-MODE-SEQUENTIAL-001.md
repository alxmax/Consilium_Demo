---
test_exempt: "prompt/mode document — acceptance validated by deliberation integration runs, not unit tests"
id: CONSILIUM-MODE-SEQUENTIAL-001
status: confirmed
layer: feature
owner: auto
depends_on: [CONSILIUM-VOICE-GENERATOR-001, CONSILIUM-VOICE-CONTROL-001, CONSILIUM-VOICE-CONSERVATOR-001, CONSILIUM-AGGREGATOR-001]
---

# sequential mode

> WHY: Run Conservator, Generator, and Control in a single shared context window — the cheapest deliberation path, used by default when no higher mode is warranted.

## WHAT — Contract (normative)
- The mode shall dispatch exactly three voices — Conservator, then Generator, then Control — in that fixed order within a single context window, with no external sub-agent dispatch (0 sub-agents, 1× baseline cost).
- Before each voice runs (Steps 3–4), the prior voice's prompt shall be stripped from context via `strip_context.py`; model in-context memory is not cleared — this is a known deliberate limitation documented in the mode spec.
- The aggregator shall apply an 8-component veto cascade (`aggregate_sequential()`) producing one of seven routing outcomes: BLOCK (irreversibility), BLOCK (glossary_fail), REWORK, SHORT-CIRCUIT (scale_down), ADAPT_EXTENDED (scale_up), ESCALATE, or AGGREGATE; the resulting report shall carry a `confidence` value derived from the veto outcome.
- When Conservator emits `magnitude: critical` AND `reversibility: irreversible`, a non-user-selectable auto-parallel cross-check shall be triggered; a silent parallel audit shall fire at a default cadence of 1-in-20 sequential runs (bumping to 1-in-5 when ≥2 of the last 5 audits diverged).
- The `confidence_floor: 0.70` in mode metadata is advisory — it represents the threshold below which Sequential mode confidence is flagged as "WEAK" in the `check_mode_floor` output. It is NOT a hard gate blocking report emission; a below-floor result still produces a complete report, with the floor surfaced in the confidence field's `outcome_hint`.

## WHAT — Notes & known limitations (informative)
- Role separation in Sequential is prompt-based, not architectural: `strip_context.py` removes the prior prompt but does not clear the model's in-context memory. True voice isolation requires Parallel sub-agents.
- The veto-budget for `meta_recommendation` (scale_up/scale_down) is 5 activations per month; on exhaustion the gate becomes a soft warning only.

## HOW — Acceptance (= tests)
AC-1
  Given a deliberation request with no explicit mode flag and no critical/irreversible trigger
  When  the mode runs
  Then  exactly three voices are invoked in the order Conservator → Generator → Control in a single context window, no sub-agents are dispatched, and the report carries a `confidence` value and a routing outcome from the veto cascade

AC-2
  Given a deliberation request where Conservator emits `meta_recommendation: scale_down`
  When  the mode runs
  Then  Generator and Control are skipped, the report contains `chosen_approach: "trivial-direct"`, `confidence: 0.85`, and `pipeline_executed: false`

AC-3
  Given a deliberation request where Control emits `glossary_fail: true`
  When  the aggregator runs
  Then  the routing outcome is BLOCK (glossary_fail) and the user is asked to reformulate with operational terms before any chosen approach is emitted

## WHERE — Current implementation
- modes/sequential.md
