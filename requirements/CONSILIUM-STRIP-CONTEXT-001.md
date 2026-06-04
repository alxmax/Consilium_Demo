---
id: CONSILIUM-STRIP-CONTEXT-001
status: confirmed
layer: feature
owner: auto
depends_on: [CONSILIUM-UTILS-001]
risk: 1
---

# strip_context

> Projects each voice's output down to the minimum fields the next voice needs (anti-contamination).

## Input
- stdin (default) or `--input <file>`: JSON object for `--for control` or `--for conservator` modes; plain text for `--truncate-text` mode
- `--for control`: expects Generator output JSON with a `candidates` array
- `--for conservator`: expects combined JSON with `candidates` (Generator) and `verdicts` (Control) arrays
- `--truncate-text <MAX_TOKENS>`: maximum token budget (integer), approximated as 4 chars/token

## Description
Reduces cross-voice context contamination in the sequential deliberation pipeline by projecting each voice's output down to the minimum fields the next voice needs. In `--for control` mode it strips Generator candidates to only `id`, `summary`, and `sketch`, removing rationale fields that would rhetorically bias Control's technical validation. In `--for conservator` mode it intersects valid Control verdicts with Generator candidates, keeping only `id`/`summary`/`sketch` and discarding Control's issue descriptions that would bias Conservator's risk scoring. The `--truncate-text` mode is used by Trias orchestration to cap raw conversation context sent to each personality sub-agent to a configurable token budget, appending a truncation marker when the text is cut.

## Output
- JSON object to stdout (`--for control` or `--for conservator`): stripped candidate or verdict list
- Plain text to stdout (`--truncate-text`): possibly truncated text with optional marker appended
- exit code 0 on success; non-zero on argument or JSON parse errors

## Acceptance (= tests)
- Running `--for control` on a Generator output strips the `rationale` field from all candidates and keeps only `id`, `summary`, and `sketch`.
- Running `--for conservator` drops any candidate whose matching Control verdict has `valid=false`.
- Running `--for conservator` excludes Control's `issues` and `notes` fields from the output.
- Running `--truncate-text 15000` on text shorter than 60000 characters returns the text unchanged with no marker.
- Running `--truncate-text 15000` on text exceeding 60000 characters truncates at 60000 chars and appends the truncation marker.
