---
id: CONSILIUM-VOCABULARY-MAP-001
status: confirmed
layer: bus
owner: auto
depends_on: []
risk: 0
---

# vocabulary_map

> Single source of truth for field-value translations and the per-voice token budget table.

## Input
- CLI positional args: category (e.g. `reversibility`, `magnitude`, `verdict`) and optional value (e.g. `complete`, `critical`)
- `compute_tokens_budget` called programmatically with `magnitude`, `reversibility`, and optional `meta` strings

## Description
Single source of truth for all user-facing natural-language translations of structured deliberation field values, and for the per-voice token budget table. `VOCABULARY_MAP` maps categories (`reversibility`, `magnitude`, `meta_recommendation`, `verdict`) to their human-readable labels, which are used by the renderer and aggregator to produce consistent output strings. `compute_tokens_budget` derives a per-voice token allocation from the Conservator's Q1 (magnitude) and Q2 (reversibility) outputs, scaling down to 300 for trivial questions and applying `meta_recommendation` modifiers (`scale_down` -> 300, `scale_up` -> +50% capped at 4000). The module is bus-layer because it carries no pipeline logic - it is a pure lookup table consumed by feature scripts.

## Output
- stdout: translated human-readable string when invoked via CLI
- `compute_tokens_budget` returns a dict with `generator` and `control` keys
- exit code 0 always

## WHAT — Verify intent (open questions for the human)
- None — doc is unambiguous.

## Acceptance (= tests)
- `translate('reversibility', 'complete')` returns the Romanian string `usor de anulat`.
- `translate('verdict', 'GO')` returns `aprobat de majoritate`.
- `compute_tokens_budget('critical', 'irreversible')` returns `{'generator': 4000, 'control': 4000}`.
- `compute_tokens_budget` with `meta='scale_down'` always returns `{'generator': 300, 'control': 300}` regardless of magnitude/reversibility.
- `translate` for an unknown category or value returns `str(value)` without raising.
