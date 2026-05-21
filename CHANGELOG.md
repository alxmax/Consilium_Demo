# Changelog

## v1.01 — 2026-05-21

### Mode changes

**Trias** — internal execution model revised:
- Was: 9 sub-agents (3 personalities × 3 voices dispatched in parallel, each personality running its own parallel mode)
- Now: 3 sub-agents (one per personality). Within each sub-agent, the three voices run sequentially with context stripping between them (same isolation mechanism as Sequential — Blind). Democratic vote on the 3 chosen results is unchanged.
- Tie rule (1-1-1) made explicit: result is `PEND`, orchestrator must escalate or re-run.

**Parallel** — removed from user-selectable modes (RUND2):
- Was: OPT-IN mode, user could invoke explicitly
- Now: internal auto cross-check only. Auto-triggers when `magnitude=critical ∧ reversibility=irreversible`. Also runs as a silent audit every 20 runs. Not exposed in the `--mode` selector.

### Architecture poster (architecture.html)

- Hero section added (pitch, voice chips, stat badges, mini SVG flow)
- "Patterns" tab renamed to "Interactive Demo"
- "Benchmark" tab added: 3 tasks, 5 modes, `claude -p` methodology, results in progress
- Voice cards: accent moved from `border-top` to `border-left` strip
- `DEFAULT` badge added to `conservative_override` in Modes tab
- Trias info-flow SVG updated: sequential voice layout (strip labels, no parallel fan-out inside personalities)
- Flowmap SVG: SEQUENTIAL — NAIVE labelled as LEGACY; PARALLEL labelled as AUTO
- Footer added
- Benchmark task difficulty: Transport Choice → Medium, Rule of Three → Medium

---

## v1.00 — 2025-01-01

Initial public release.

- Architecture poster with Architecture / Flow / Modes / Patterns tabs
- Three voices: Generator / Control / Conservator
- Modes: Sequential — Blind (default), Parallel, Dialectic (two-pass), Dialectic (iterative, SPEC), Trias, Sequential — Naive (legacy)
- Voting schemes: conservative_override (default), weighted, majority, team_vote
- Canonical run example in `example_output.json`
