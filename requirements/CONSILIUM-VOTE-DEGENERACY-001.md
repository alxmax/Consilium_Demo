---
id: CONSILIUM-VOTE-DEGENERACY-001
status: confirmed
layer: feature
owner: auto
depends_on: []
risk: 1
---

# Trias vote degeneracy measurement

> Empirically measures whether the Trias "democratic vote" carries signal by computing the 3-0 unanimity rate across Trias runs in the corpus — testing the hypothesis that 3 personality lenses on the same model are correlated and always agree (Senate audit 2026-05-26).

## WHAT — Contract

- Shall scan `.consilium/runs/*.json` for genuine Trias runs (mode field = `"trias"` or `"trias_split"` exactly) and tally vote-pattern distribution.
- Shall report `vote_degenerate: true` if 3-0 unanimity rate > threshold (default 0.85) and n ≥ min-n (default 20); `"insufficient"` when n < min-n; `false` otherwise.
- A 2-0 pattern (one personality all-vetoed) shall be counted as `veto_rate`, not folded into unanimity.
- Shall be read-only — no modification to runs, prompts, or pipeline.
- With `--json`, shall emit machine-readable output.
- `--runs-dir` overrides the default corpus directory; `--min-n` and `--degenerate-threshold` are configurable.
- The default threshold of 0.85 is calibration-provisional; it shall be revisited once n ≥ min-n genuine Trias runs exist. The `insufficient` verdict already defers judgment until that corpus exists.

## WHAT — Verify intent (open questions for the human)

- None — contract matches script docstring and Senate audit 2026-05-26 intent exactly.

## HOW — Acceptance (= tests)

- Given 20+ Trias runs all with 3-0, `vote_degenerate: true` is returned.
- Given 20+ Trias runs with 50% 3-0, `vote_degenerate: false`.
- Given fewer than min-n Trias runs, result is `"insufficient"`.
- Given `--json`, output parses as valid JSON with `vote_degenerate`, `three_zero_rate`, `n` fields.
- Non-Trias runs are excluded even if they reference `vote_pattern` in their body.

## WHERE — Current implementation

- scripts/vote_degeneracy.py
<!-- implements: CONSILIUM-VOTE-DEGENERACY-001 -->
