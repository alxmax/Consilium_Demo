---
id: CONSILIUM-RENDER-FEEDBACK-HTML-001
status: confirmed
layer: bus
owner: auto
depends_on: [CONSILIUM-UTILS-001]
risk: 1
---

# render_feedback_html

> Pure rendering engine: a list of Entry records -> one self-contained dark-themed FEEDBACK.html.

## Input
- List of `Entry` dataclass instances passed programmatically (primary import surface)
- Path to the `runs/` directory passed to `render()` so linked run JSON files can be loaded for drill-down panels
- CLI stdin: JSON object with an `entries` array (when invoked as a script)
- CLI flag `--runs-dir`: optional override for the `runs/` directory path
- `.consilium/runs/*.json` files: loaded per-entry for telemetry (`tokens_in`, `tokens_out`) and `deliberation_log` (generator candidates, control verdicts, conservator scores)

## Description
Pure rendering engine that converts a list of Entry records into a single self-contained dark-themed HTML file (inline CSS and JavaScript, no external assets). It exists as a separate bus-layer module so that both `log_feedback.py` and `mark_outcome.py` can rewrite FEEDBACK.html without duplicating HTML generation logic. For each entry it generates a collapsed table row with date, context, chosen approach, outcome badge, token count, note, and vote pattern, plus an expandable drill-down panel that loads Generator candidates, Control verdicts, and Conservator risk scores from the linked `runs/*.json` file. Token counts are shown as measured totals when telemetry is present, or as a `(calc)` estimate derived from the median tokens-per-candidate of peer runs when telemetry is absent; legacy entries with no run data show an em-dash. The vetoed badge in the Conservator panel is sourced from the aggregate step's `vetoed` list (not re-derived from a risk threshold) to avoid lying about candidates in the `[0.7, 0.8]` band.

## Output
- Complete `<!doctype html>` string returned by `render()` (primary output, written by callers)
- When invoked as CLI, the HTML string is written to stdout
- exit code 0 always

## WHAT — Verify intent (open questions for the human)
- The `(calc)` token estimate uses 'the median tokens-per-candidate of peer runs' — how are 'peer runs' defined (same mode, same date range, all runs)? An undefined peer set makes the estimate non-reproducible.
- The VETOED badge is sourced from the aggregate step's `vetoed` list — what if the run was produced by the `sequential` scheme, which does not produce a `vetoed` list in the same format? Is there a fallback, and is the Conservator drill-down panel suppressed or shown without vetoed badges?
- The HTML is described as 'self-contained' with no external asset references — is this verified by the acceptance test, or only stated? A test that checks for the absence of `<link>` and `<script src>` tags would confirm it.

## Acceptance (= tests)
- `render()` returns a string beginning with `<!doctype html>` that contains one `<tr class="entry">` row and one `<tr class="drill">` row for each Entry in the input list.
- For an Entry whose `run_path` points to an existing `runs/*.json` file with telemetry data, the rendered tokens cell shows the measured sum of `tokens_in + tokens_out` across all voices (formatted compactly as e.g. `14k`).
- For an Entry whose `run_path` points to a run file with a `vetoed` list in the aggregate step, the Conservator drill-down panel shows a VETOED badge only for candidates whose id appears in that list, not for any candidate exceeding a hard-coded risk threshold.
- For an Entry with no linked run file (`run_path` is None), the drill-down cell contains the legacy stub message and no Generator/Control/Conservator panels.
- The rendered HTML is self-contained: no `<link>`, `<script src>`, or `<img src>` tags reference external URLs.
