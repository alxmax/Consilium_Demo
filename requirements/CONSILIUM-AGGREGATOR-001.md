---
id: CONSILIUM-AGGREGATOR-001
status: confirmed
layer: feature
owner: auto
depends_on: [CONSILIUM-UTILS-001]
risk: 2
---

# aggregator

> Merges scored Generator/Control/Conservator outputs into a chosen candidate via one of five aggregation schemes.

## Input
- stdin or `--input` file: JSON object with `candidates` array and optional `weights`, `veto_threshold`, `personalities` keys (schema varies by scheme)
- CLI flag `--scheme`: one of `majority | conservative_override | risk_adjusted_utility | team_vote | sequential` (default: `conservative_override`)
- CLI flag `--input`: path to JSON file (default: stdin)

## Description
Implements five distinct aggregation schemes that merge the scored outputs of the Generator, Control, and Conservator voices into a single chosen candidate and ranking. The `majority` scheme picks the candidate with the highest mean voice score; `conservative_override` vetoes any candidate whose Conservator risk exceeds a configurable threshold and ranks survivors by a weighted utility that flips Conservator into a safety signal; `risk_adjusted_utility` applies a smooth sigmoid penalty instead of a hard veto so clustered candidates near the threshold are ranked gracefully. The `team_vote` scheme implements the democratic majority-vote logic used in Trias mode, deriving a vote pattern (3-0, 2-1, 2-0, etc.) from three personality sub-agents' chosen-IDs. The `sequential` scheme is the authoritative single-context aggregation path: it applies a priority-ordered veto cascade (glossary_fail -> irreversibility_flag -> escalate -> rework -> adapt_short/extend -> aggregate) over raw voice output dicts rather than numeric scores.

## Output
- stdout: JSON object with `scheme`, `chosen`, `ranking`, and scheme-specific fields (`vetoed`, `vote_pattern`, `dissent`, `retry_suggested`, `low_separation`, `veto_uncertain`, etc.)
- exit code 0 on success
- exit code non-zero on invalid input (raised `ValueError`)

## Acceptance (= tests)
- Given a candidates list where the Conservator score of every candidate exceeds `veto_threshold` and `auto_relax=True`, the output contains `chosen: null` and a non-empty `retry_suggested` block.
- Given two candidates with identical generator and control scores but different Conservator risk under `conservative_override`, the candidate with lower risk ranks first.
- Given `vote_pattern='2-1'` with three personalities and two of them choosing the same candidate, `team_vote` returns `chosen` equal to the majority candidate and a non-empty `dissent` list.
- Given sequential input where `control_out['glossary_fail']` is `True`, the output has `result: BLOCK` and `reason: glossary_fail`, regardless of other signals.
- Given three or more simultaneous triggers in sequential mode, the output has `result: ESCALATE` with a `triggers` list of length >= 3.
