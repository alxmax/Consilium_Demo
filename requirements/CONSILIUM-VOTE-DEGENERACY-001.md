---
id: CONSILIUM-VOTE-DEGENERACY-001
status: baseline
layer: feature
owner: auto
depends_on: [CONSILIUM-UTILS-001]
risk: 1
---

# vote_degeneracy

> Measures empirically whether the Trias 3-personality vote is statistically degenerate.

## Input
- `--runs-dir`: path to `.consilium/runs/` (default: `.consilium/runs`)
- `--degenerate-threshold`: float threshold for 3-0 unanimity rate (default: 0.85)
- `--min-n`: minimum Trias run count to render a verdict (default: 20)
- `--json`: emit JSON report to stdout instead of human-readable text
- Reads `*.json` files from the runs directory (text-based scan, not `json.loads`)

## Description
Empirically measures whether the Trias mode's three-personality democratic vote is statistically degenerate - i.e., whether the Pioneer/Architect/Steward lenses always agree because they are correlated samples from the same model. The script scans the run corpus for genuine Trias runs (identified by a `mode: trias`/`trias_split` marker), extracts each run's `vote_pattern` field via regex, and tallies the distribution using a `Counter`. It then computes the 3-0 unanimity rate and compares it against a configurable threshold: above 0.85 with at least 20 runs is judged `vote_degenerate` (the vote adds no signal), at or below is `vote_meaningful`, and below the minimum sample size is `insufficient` (Deming gate). The 2-0 veto pattern is tracked separately as `veto_rate` because it represents a personality veto event, not three lenses agreeing, so folding it into unanimity would overstate decorrelation.

## Output
- stdout: human-readable degeneracy report (n, distribution, unanimity/veto rates, verdict + note) or JSON when `--json` is passed
- exit code 0 on success, exit code 2 if the runs directory does not exist

## Acceptance (= tests)
- Runs with `mode: trias` or `trias_split` are admitted; runs with any other mode that merely contains a `vote_pattern` in their body are excluded.
- 3-0 patterns count as unanimity; 2-0 patterns count only as `veto_rate` and are not folded into `unanimity_rate`.
- With fewer than `--min-n` Trias runs, verdict is `insufficient` regardless of the observed 3-0 rate.
- When 3-0 rate exceeds `--degenerate-threshold` with `n >= --min-n`, verdict is `vote_degenerate`; otherwise `vote_meaningful`.
- `--json` flag produces valid JSON output with keys: `n`, `distribution`, `unanimity_rate`, `veto_rate`, `veto_count`, `degenerate_threshold`, `min_n`, `verdict`, `note`.
