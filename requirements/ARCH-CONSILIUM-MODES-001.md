---
milestone: v1.1
id: ARCH-CONSILIUM-MODES-001
status: confirmed
level: architecture
layer: aggregate
depends_on: [CONSILIUM-MODE-SEQUENTIAL-001, CONSILIUM-MODE-DIALECTIC-001, CONSILIUM-MODE-TRIAS-001, CONSILIUM-MODE-SKEPTIC-ON-CHOSEN-001, CONSILIUM-MODE-LENS-001, CONSILIUM-SUBAGENT-001, CONSILIUM-TRIAS-MODEL-SCHEMA-001, CONSILIUM-VOTE-DEGENERACY-001]
satisfies: [SYS-CONSILIUM-VERDICT-001]
owner: alxmax
risk: 1
---

# Deliberation modes

> How the voices are orchestrated: the cost/scrutiny ladder a caller picks from, and the sub-agent wrapper that isolates a run.

## Description

Every line in this section is binding.

- Sequential is the default mode and runs Generator, Conservator and Control in one context. [[CONSILIUM-MODE-SEQUENTIAL-001]]
- Dialectic is Sequential plus an unconditional Skeptic sub-agent on the chosen approach. [[CONSILIUM-MODE-DIALECTIC-001]]
- Trias runs the three personalities blind and in parallel, resolves by majority vote, then runs one post-vote Skeptic. [[CONSILIUM-MODE-TRIAS-001]] [[CONSILIUM-VOTE-DEGENERACY-001]]
- `skeptic_on_chosen` composes over any base mode and triggers on its own when confidence is below 0.70. [[CONSILIUM-MODE-SKEPTIC-ON-CHOSEN-001]]
- Sub-agents dispatched by any mode use the model the mode assigns (`sonnet` by default), never the orchestrator's inherited model. [[CONSILIUM-SUBAGENT-001]] [[CONSILIUM-TRIAS-MODEL-SCHEMA-001]]
- `--lens <name>` is an opt-in, off by default, that prepends one personality lens to Sequential or Dialectic. [[CONSILIUM-MODE-LENS-001]]

## Verify intent

- None - contract confirmed by the owner on 2026-09-21.

## Cases

- **CASE-1** — Given no mode flag, when `/consilium` runs, then the report's `telemetry.mode` is `sequential`.
- **CASE-2** — Given a Sequential run whose confidence is 0.65, when the run completes, then a Skeptic challenge is recorded on the chosen approach.
- **CASE-3** — Given a Trias run, when the vote is 2-1, then the confidence matches `VOTE_PATTERN_CONFIDENCE['2-1']`.
