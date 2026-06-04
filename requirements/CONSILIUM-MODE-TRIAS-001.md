---
test_exempt: "prompt/mode document — acceptance validated by deliberation integration runs, not unit tests"
id: CONSILIUM-MODE-TRIAS-001
status: confirmed
layer: feature
owner: auto
depends_on: [CONSILIUM-MODE-SEQUENTIAL-001, CONSILIUM-LENS-PIONEER-001, CONSILIUM-LENS-ARCHITECT-001, CONSILIUM-LENS-STEWARD-001, CONSILIUM-PERSONALITIES-001]
---

# trias mode

> WHY: Apply three divergent personality lenses (Pioneer/Architect/Steward) each running a full Sequential deliberation, then resolve by democratic majority vote — providing genuine multi-perspective scrutiny for high-stakes, irreversible, or architecturally complex decisions.

## WHAT — Contract (normative)
- The mode shall classify magnitude via `scope_gate.py` on the original unstripped context before any context stripping; when lazy routing is enabled (default), it shall downgrade to Sequential (low/medium magnitude) or Dialectic (high magnitude) and emit a structured `trias_lazy_routed` notification — full Trias (3 sub-agents) runs only on `critical` magnitude or when the user explicitly requests it.
- When full Trias runs, the mode shall dispatch 3 personality sub-agents (Pioneer, Architect, Steward) each running a complete Sequential deliberation (Conservator → Generator → Control) internally with the personality lens prepended; each sub-agent receives context truncated to ≈15 000 tokens before dispatch.
- The mode shall aggregate the 3 `chosen_approach` values via `aggregator.py --scheme team_vote`; if all 3 are unanimous (`vote_pattern: 3-0`), the team_vote step shall be skipped and `vote_skipped: true` set; confidence shall be derived from the vote pattern (3-0 → 0.95, 2-1 → 0.75, 2-0 → 0.70).
- When the vote pattern is 1-1-1 or 0-0-0, the B2 deadlock cascade shall fire: Round 2 re-dispatches all 3 personalities with peer context; if still deadlocked, a Skeptic tiebreaker sub-agent is dispatched; if unresolved, the result is PEND. Maximum cost is 7 sub-agents (3 + 3 + 1).
- The 3 personality sub-agents shall be dispatched in parallel; the runtime audit tracks divergence between parallel and serial results.

## WHAT — Notes & known limitations (informative)
- Serial dispatch is an accepted implementation artifact that does not affect correctness; the silent parallel audit is the observability mechanism.
- `trias_split` is deprecated; `validate_report.py` maps legacy `trias_split` runs to `trias` via `_LEGACY_MODE_ALIASES` for telemetry backward-compat.
- Aggregated Trias is approximately −18% Conservator weight relative to single-context; avoid when strict conservatism is required.

## HOW — Acceptance (= tests)
AC-1
  Given a deliberation request in trias mode with `magnitude: critical` (blocklist hit)
  When  the mode runs
  Then  3 personality sub-agents are dispatched (Pioneer, Architect, Steward), each producing a `chosen_approach`, the vote is aggregated via `team_vote`, and the report contains `vote_pattern`, `confidence`, and `personalities[]` with each personality's `chose`

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
