---
milestone: v1.0
test_exempt: "prompt/mode document — acceptance validated by deliberation integration runs, not unit tests"
id: CONSILIUM-MODE-TRIAS-001
status: confirmed
layer: feature
owner: auto
depends_on: [CONSILIUM-MODE-SEQUENTIAL-001, CONSILIUM-MODE-SKEPTIC-ON-CHOSEN-001, CONSILIUM-LENS-PIONEER-001, CONSILIUM-LENS-ARCHITECT-001, CONSILIUM-LENS-STEWARD-001, CONSILIUM-PERSONALITIES-001]
---

# trias mode

> WHY: Apply three divergent personality lenses (Pioneer/Architect/Steward) each running a full dialectic deliberation, then resolve by democratic majority vote — providing genuine multi-perspective scrutiny for high-stakes, irreversible, or architecturally complex decisions.

## WHAT — Contract (normative)
- The mode shall classify magnitude via `scope_gate.py` on the original unstripped context before any context stripping; when lazy routing is enabled (default), it shall downgrade to Sequential (low/medium magnitude) or Dialectic (high magnitude) and emit a structured `trias_lazy_routed` notification — full Trias (4 sub-agents nominal — 3 personalities + 1 post-vote Skeptic, ≈2.67× Sequential) runs only on `critical` magnitude or when the user explicitly requests it.
- When full Trias runs, the mode shall dispatch 3 personality sub-agents (Pioneer, Architect, Steward) **in parallel**, each running a complete Sequential deliberation (Generator → Conservator → Control) internally with the personality lens prepended; each sub-agent receives context truncated to ≈15 000 tokens before dispatch. There is **no pre-vote Skeptic** — the 2026-06-19 skeptic-lever redesign removed the 3 per-personality pre-vote Skeptics; the 3 returned `chosen_approach` values proceed directly to the vote.
- After a decisive vote yields a winning `chosen_approach`, the mode shall dispatch exactly **one** Skeptic sub-agent (`skeptic_on_chosen`, per `prompts/voices/skeptic.md`) to challenge that winner **post-vote**, supplying the runner-up personality's rationale as a counter-hypothesis the Skeptic must attack (the coverage compensation for no longer challenging the losing candidates directly). The Skeptic is **advisory by default** — the vote stands and any objection is recorded as a caveat. Under `--skeptic-can-override`, a *demolishing* objection (`can_object: true` AND (`severity == "blocking"` OR a falsifier that defeats the `success_criterion`)) shall trigger a re-vote over the remaining `chosen_approach` values excluding the demolished winner; the new winner is itself challenged by one further `skeptic_on_chosen` (PEND if also demolished — no loop). Telemetry shall record `skeptic_challenges_count` and `post_vote_skeptic_used`. This post-vote Skeptic does **not** fire on a winner already resolved by the B2 deadlock cascade (the cascade's tiebreaker Skeptic already challenged it). Default policy is unconditional (Variant A); the confidence-gated Variant C (`--trias-skeptic-gate`, fire only when `confidence ∈ [0.0, 0.7]`) is off by default.
- The mode shall aggregate the 3 `chosen_approach` values via `aggregator.py --scheme team_vote`; if all 3 are unanimous (`vote_pattern: 3-0`), the team_vote step shall be skipped and `vote_skipped: true` set; confidence shall be derived from the vote pattern (3-0 → 0.95, 2-1 → 0.75, 2-0 → 0.70).
- When the vote pattern is 1-1-1 or 0-0-0, the B2 deadlock cascade shall fire: Round 2 re-dispatches all 3 personalities with peer context; if still deadlocked, a Skeptic tiebreaker sub-agent is dispatched; if unresolved, the result is PEND. Maximum cost is 7 sub-agents (3 + 3 + 1). `0-0-0` means all 3 personalities returned `chose: null` (each personality's internal Sequential ran `conservative_override` and vetoed every candidate); it is distinct from 1-1-1 (three different non-null choices) and is achievable without abstention — it occurs when every candidate exceeds the conservator veto threshold inside each sub-agent.
- When lazy routing downgrades to Dialectic or Sequential, the `trias_lazy_routed: true` notification is emitted by the Trias orchestrator before the downgraded mode runs; the notification is not carried into the final persisted report produced by the downgraded mode's own pipeline. The persisted report reflects the actual mode that ran (`dialectic` or `sequential`), not `trias`.
- Context truncation for Trias sub-agents is a hard first-N-characters limit: `strip_context.py --truncate-text 15000` takes the first `15000 × 4 = 60 000` characters of the raw context and appends a `[... context truncated ...]` marker when the budget is exceeded. The 15 000 token figure is a hard ceiling (not a target), using the approximation 1 token ≈ 4 chars.
- The 3 personality sub-agents shall be dispatched in parallel; the runtime audit tracks divergence between parallel and serial results.

## WHAT — Verify intent (open questions for the human)
- None - all questions resolved.

## WHAT — Notes & known limitations (informative)
- Serial dispatch is an accepted implementation artifact that does not affect correctness; the silent parallel audit is the observability mechanism.
- `trias_split` is deprecated; `validate_report.py` maps legacy `trias_split` runs to `trias` via `_LEGACY_MODE_ALIASES` for telemetry backward-compat.
- Aggregated Trias is approximately −18% Conservator weight relative to single-context; avoid when strict conservatism is required.

## HOW — Acceptance (= tests)
AC-1
  Given a deliberation request in trias mode with `magnitude: critical` (blocklist hit)
  When  the mode runs
  Then  3 personality sub-agents are dispatched in parallel (Pioneer, Architect, Steward), each producing a `chosen_approach`; the 3 chosens are aggregated via `team_vote` with no pre-vote Skeptic; then exactly one post-vote Skeptic (`skeptic_on_chosen`) challenges the winning candidate; and the report contains `vote_pattern`, `confidence`, `personalities[]` with each personality's `chose`, plus `skeptic_challenges_count` and `post_vote_skeptic_used`

AC-2
  Given a deliberation request in trias mode with `magnitude: high` and lazy routing enabled
  When  the mode runs
  Then  the mode downgrades to Dialectic, emits a `trias_lazy_routed: true` notification with `routed_to: "dialectic"`, and no Trias sub-agents are dispatched

AC-3
  Given a full Trias run where all 3 personalities return different `chosen_approach` values (1-1-1 vote)
  When  the B2 cascade fires
  Then  Round 2 re-dispatches 3 sub-agents with peer context; if still 1-1-1, a Skeptic tiebreaker is dispatched; if unresolved, the report is marked PEND with `cascade_incomplete: true`

## WHERE — Current implementation
- modes/trias.md

## Why test_exempt

This file is a mode specification document — it defines workflow rules, dispatch config (YAML frontmatter), and machine-readable invariants read by the orchestrator and sub-agents at runtime. It contains no executable Python logic. Structural parity between this document and the implemented behavior is enforced by `check_doc_drift.py` invariants; end-to-end conformance is validated through deliberation integration runs.
