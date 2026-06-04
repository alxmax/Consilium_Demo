---
id: CONSILIUM-CONFIDENCE-001
status: confirmed
layer: feature
owner: auto
depends_on: [CONSILIUM-UTILS-001]
risk: 2
---

# confidence

> Derives a calibrated confidence score from inter-voice agreement + runner-up separation (or Trias vote pattern).

## Input
- stdin or `--input` file: JSON object with `candidates` (list of `{id, scores: {generator, control, conservator}}`) and `chosen` (string or null) for score-based mode
- For Trias mode: JSON object with `vote_pattern` (e.g. `3-0`, `2-1`) and optional `dissent` and `abstained` lists instead of candidates/chosen
- CLI flag `--input`: path to JSON input file (default: stdin)
- `modes/*.md` frontmatter: read at import time to populate per-mode confidence floors (`confidence_floor` key)

## Description
Derives a calibrated confidence score for a deliberation result using two complementary signals: inter-voice agreement on the chosen candidate (measured as 1 minus the population stdev of the three voices after flipping Conservator from risk to safety, normalized against the theoretical maximum stdev) and separation from the runner-up candidate (difference in mean utility). The two signals are blended as `0.7 * agreement + 0.3 * separation` and clamped to `[0.05, 0.99]`. For Trias mode it bypasses voice-score arithmetic entirely and derives confidence from the democratic vote pattern via a hardcoded lookup table (`VOTE_PATTERN_CONFIDENCE`), applying Steward-specific penalties when the conservative personality dissents (-0.10) or abstains (-0.15). The `check_mode_floor` helper lets callers determine whether the derived confidence falls below the mode-specific floor loaded from `modes/*.md` frontmatter, exempting structurally decisive Trias vote patterns (3-0, 2-1, 2-0) from the WEAK flag.

## Output
- stdout: JSON with `confidence` (float or null), `agreement` (float), `separation` (float or null), and optional `source` and `notes` fields
- When `chosen` is null or absent from candidates: JSON with `confidence: null` and `reason` string
- exit code 0 on success; exit code 1 on invalid input shape

## WHAT — Verify intent (open questions for the human)
- None — doc is unambiguous.

## Acceptance (= tests)
- Given a chosen candidate with `generator=0.8`, `control=0.9`, `conservator=0.1` (high utility, low risk, high agreement) and no runner-up, the output confidence is close to 0.99 (agreement near 1.0, separation defaults to 1.0).
- Given `chosen: null` in the input, the output is `{confidence: null, reason: "..."}` and the script exits 0.
- Given `vote_pattern='2-1'` with a dissent list containing the Steward personality, the output confidence equals `VOTE_PATTERN_CONFIDENCE['2-1']` minus the `STEWARD_DISSENT_PENALTY` (0.10), rounded to 3 decimal places.
- Given `vote_pattern='3-0'`, `check_mode_floor` with `mode='trias'` returns `below_floor=false` regardless of the numeric floor, because 3-0 is in the decisive exempt set.
- Given a candidates list where one candidate is missing the `scores` key, the script exits 1 and prints a descriptive error to stderr before producing any output.
