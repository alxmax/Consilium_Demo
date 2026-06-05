---
name: sequential
subagents: 0
cost_multiplier: 1.0
confidence_floor: 0.70
models: sonnet
dispatch_count: 3
description: Default mode — Conservator, Generator, Control run in-context (no sub-agent dispatch).
---

# Sequential mode (default)

**Mechanics:** Conservator → Generator → Control run in the same context window. No external sub-agent dispatch. Cost: 1× (baseline).

`strip_context.py` applies ONLY in Sequential mode (Steps 3-4) — it strips the prior voice's prompt before the next voice runs. Parallel dispatches do not use it.

## Three-layer architecture

| Layer | Components | Role |
|---|---|---|
| **Deliberation** | Conservator → Generator → Control | Runs on every user question |
| **Aggregation** | aggregate_sequential() with 8-component veto cascade | Synthesizes voice outputs, decides what user sees |

## Dispatch order

Default order: **Conservator → Generator → Control**

1. Conservator sets `tokens_budget` and `irreversibility_flag`
2. Generator receives `magnitude`, `counterparty_risks`, `tokens_budget.generator` (NOT `meta_recommendation`)
3. Control receives full outputs from both Conservator and Generator

**Role separation, not Chinese wall.** Sequential runs the same LLM playing three roles in the same context window; `strip_context.py` strips the prior voice's prompt, but does not clear the model's in-context memory. This is a known, deliberate limitation — role prompts provide separation, not true isolation. True isolation requires Parallel sub-agents.

Auto-parallel cross-check: triggered only when Conservator outputs `magnitude: critical` AND `reversibility: irreversible`. Not user-selectable.

Silent audit: implemented in `scripts/audit_counter.py`; state in `.consilium/audit_state.json`. Default cadence 1 silent parallel audit per 20 sequential runs; bumps to 1/5 when ≥2 of the last 5 audits diverged (restores to 1/20 after 5 clean audits). Full workflow + counted-runs semantics in SKILL.md §"Silent parallel audit".

## Veto powers

The 8 design components (per spec): vocabulary_map, length_targets, priority_veto_order, tension_expose, metadata, user_profile, multi_confidence, escalation_rule. The `aggregate_sequential()` function produces 7 distinct routing outcomes derived from these components: `BLOCK` (glossary_fail), `BLOCK` (irreversibility), `REWORK`, `SHORT-CIRCUIT` (scale_down — skip Gen+Ctrl), `ADAPT_EXTENDED` (scale_up), `ESCALATE` (3+ triggers), `AGGREGATE` (default).

| Trigger | Source | Effect | Action |
|---|---|---|---|
| `irreversibility_flag: true` | Conservator | BLOCK (hard) | Ask user for explicit consent before Generator |
| `glossary_fail: true` | Control | BLOCK (soft) | Ask user to reformulate with operational terms |
| `disagreements: substantial` | Control | REWORK | Re-run Generator with clarification context |
| `meta_recommendation: scale_down` | Conservator | SHORT-CIRCUIT | Skip Generator AND Control entirely. Emit minimal report with `chosen_approach: "trivial-direct"`, `confidence: 0.85`, `pipeline_executed: false`. See SKILL.md Step 2 (authoritative). |
| `meta_recommendation: scale_up` | Conservator | ADAPT_EXTENDED | Warn user, add context before Generator |
| 3+ of above simultaneously | Aggregator | ESCALATE | Present trigger table to user, request decision |

Veto budget for `meta_recommendation`: 5 activations of `scale_up` or `scale_down` per month. On exhaustion → soft warning only, not blocking.

## Failure-mode recovery

- **Sub-agent crash / timeout:** retry that Agent call once; on a second failure, fall back to Sequential for that voice.
- **Malformed JSON from voice:** reject the voice's output, treat as missing (`{}` for verdicts/scores, or `{"candidates":[]}` for generator) and continue with the others. Log the error in `deliberation_log` with step `"<voice>_parse_error"`.
- **Missing mandatory fields (e.g. `candidates` empty):** raise a warning in the terminal, skip the aggregator and emit a skipped report with `skip_reason: "voice output incomplete after retry"`.
- **Strip_context**: necessary only in Sequential mode (Steps 3-4); in Parallel each voice runs in isolation and does not need `strip_context.py`.

## Low-confidence auto-escalation

When `confidence < 0.6` after Sequential completes, the orchestrator automatically re-runs with `--mode dialectic` — no user action required. The Dialectic result is the final output; the Sequential run is discarded. The report carries `auto_escalated: true` (passed in the bundle before `build_report.py`). One escalation level: if Dialectic also < 0.6, no further escalation fires. See SKILL.md §Step 5b for the full contract.

## When to use

- Default for all deliberations unless a higher mode is warranted
- Bugfix or <20-line diff — scope_gate will often skip automatically
- Low-stakes exploratory changes where isolation between voices is not needed
- Any deliberation where the user has not explicitly requested a higher mode

<!-- implements: CONSILIUM-MODE-SEQUENTIAL-001 -->

