---
milestone: v1.0
test_exempt: "prompt/mode document — acceptance validated by deliberation integration runs, not unit tests"
id: CONSILIUM-MODE-SEQUENTIAL-001
status: confirmed
layer: feature
owner: auto
depends_on: [CONSILIUM-VOICE-GENERATOR-001, CONSILIUM-VOICE-CONTROL-001, CONSILIUM-VOICE-CONSERVATOR-001, CONSILIUM-AGGREGATOR-001]
---

# sequential mode

> WHY: Run Generator, Conservator, and Control in a single shared context window — the cheapest deliberation path, used by default when no higher mode is warranted.

## WHAT — Contract (normative)
- The mode shall dispatch exactly three voices — Generator, then Conservator, then Control — in that fixed order within a single context window, with no external sub-agent dispatch (0 sub-agents, 1× baseline cost). Generator runs first, blind to risk framing (anti-anchoring), and self-scales its depth from the change's blast radius.
- The irreversibility consent gate shall run **pre-dispatch** (Step 1.6), before Generator, keyed on `scope_gate.consent_required` (a sensitive/irreversible path or an undeterminable change; fail-safe — uncertainty requires consent). Conservator's `irreversibility_flag` is the backstop for what a path/text pre-check cannot see.
- Before each voice runs (Steps 2–4), the prior voice's prompt shall be stripped from context via `strip_context.py`; model in-context memory is not cleared — this is a known deliberate limitation documented in the mode spec.
- The aggregator shall apply an 8-component veto cascade (`aggregate_sequential()`) producing one of seven routing outcomes: BLOCK (irreversibility), BLOCK (glossary_fail), REWORK, SHORT-CIRCUIT (scale_down — skips Control only, Generator already ran), ADAPT_EXTENDED (scale_up), ESCALATE, or AGGREGATE; the resulting report shall carry a `confidence` value derived from the veto outcome.
- When Conservator emits `magnitude: critical` AND `reversibility: irreversible`, a non-user-selectable auto-parallel cross-check shall be triggered; a silent parallel audit shall fire at a default cadence of 1-in-20 sequential runs (bumping to 1-in-5 when ≥2 of the last 5 audits diverged).
- The `confidence_floor: 0.70` in mode metadata is advisory — it represents the threshold below which Sequential mode confidence is flagged as "WEAK" in the `check_mode_floor` output. It is NOT a hard gate blocking report emission; a below-floor result still produces a complete report, with the floor surfaced in the confidence field's `outcome_hint`.

## WHAT — Verify intent (open questions for the human)
- None - all questions resolved.

## WHAT — Notes & known limitations (informative)
- Role separation in Sequential is prompt-based, not architectural: `strip_context.py` removes the prior prompt but does not clear the model's in-context memory. True voice isolation requires Parallel sub-agents.
- The veto-budget for `meta_recommendation` (scale_up/scale_down) is 5 activations per month; on exhaustion the gate becomes a soft warning only. This budget is **not implemented** — no script tracks activations or resets at month boundaries. It is aspirational policy documented in SKILL.md only.
- The `confidence_floor: 0.70` and the `log_feedback.py` `--outcome OK` confidence gate are the same numeric threshold applied at two distinct points: the floor is checked at Step 5b by `check_mode_floor()` (advisory, flags run as WEAK) while the log_feedback gate is enforced at Step 6 (hard gate on `--outcome OK`, requires `--force-override` to bypass). A below-floor Sequential run does not block report emission but does require `--force-override` to log it as OK.
- The auto-parallel cross-check (`magnitude: critical AND reversibility: irreversible`) and the 1-in-20 silent parallel audit are distinct mechanisms sharing the same 2-turn execution flow but with separate triggers: the cross-check fires per-run based on Conservator output (no counter), while the silent audit is driven by `scripts/audit_counter.py` and state in `.consilium/audit_state.json`.

## HOW — Acceptance (= tests)
AC-1
  Given a deliberation request with no explicit mode flag and no critical/irreversible trigger
  When  the mode runs
  Then  exactly three voices are invoked in the order Generator → Conservator → Control in a single context window, no sub-agents are dispatched, and the report carries a `confidence` value and a routing outcome from the veto cascade

AC-2
  Given a deliberation request where Conservator (running second) emits `meta_recommendation: scale_down`
  When  the mode runs
  Then  Control is skipped (Generator has already run), the report contains `chosen_approach: "trivial-direct"`, `confidence: 0.85`, and `pipeline_executed: false`

AC-3
  Given a deliberation request where Control emits `glossary_fail: true`
  When  the aggregator runs
  Then  the routing outcome is BLOCK (glossary_fail) and the user is asked to reformulate with operational terms before any chosen approach is emitted

AC-4
  Given a completed Sequential deliberation where `confidence < 0.6`
  When  the orchestrator checks confidence at Step 5b
  Then  it automatically re-runs the full pipeline with `--mode dialectic`; the Dialectic result (with `auto_escalated: true` in the report) is the final output; no further auto-escalation fires if Dialectic confidence is also < 0.6

AC-5
  Given a deliberation request whose diff touches a sensitive/irreversible path (scope_gate `consent_required: true`)
  When  the mode runs in an interactive (non-headless) context
  Then  the orchestrator requests explicit user consent BEFORE dispatching Generator; no voice output exists in context when consent is requested (the consent gate is pre-dispatch, not post-generation)

## WHERE — Current implementation
- modes/sequential.md

## Why test_exempt

This file is a mode specification document — it defines workflow rules, dispatch config (YAML frontmatter), and machine-readable invariants read by the orchestrator and sub-agents at runtime. It contains no executable Python logic. Structural parity between this document and the implemented behavior is enforced by `check_doc_drift.py` invariants; end-to-end conformance is validated through deliberation integration runs.
