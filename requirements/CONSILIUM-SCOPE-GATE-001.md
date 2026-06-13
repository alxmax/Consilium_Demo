---
milestone: v1.0
id: CONSILIUM-SCOPE-GATE-001
status: confirmed
layer: feature
owner: auto
depends_on: []
risk: 1
---

# scope_gate

> Decides whether a change is small enough to bypass full deliberation (fails open), and whether it needs explicit consent before any voice runs (fails safe).

## Input
- Git working tree diff via `probe_change.py` (default: HEAD, or `--ref <ref>..HEAD`, or `--range <A>..<B>`)
- `--files`: optional path restriction for the git diff
- `--config`: optional path to a `scope_gate.json` overriding `max_files`, `max_lines`, and `blocklist`
- stdin JSON when `--signals-stdin` is set: `{files_changed, lines_added, lines_removed, paths}`
- `CONSILIUM_FORCE_FULL` env variable: if `1`, always returns `should_skip=false`

## Description
Decides whether a change is small enough to bypass full deliberation. It collects diff signals either from git via `probe_change.py` or from pre-computed stdin JSON, checks file and line counts against configurable thresholds, and scans changed paths against a sensitive-path blocklist. Based on those signals it classifies the change's magnitude (`low/medium/high/critical`) and derives a `mode_ceiling` (the maximum appropriate deliberation mode), then outputs a JSON decision the orchestrator uses to short-circuit or proceed. The gate fails open: probe failures, missing git repos, or config load errors all produce `should_skip=false` so that uncertain situations always trigger deliberation rather than silently skipping it. The same probe also derives `consent_required` — a pre-dispatch irreversibility consent gate. Because the Generator voice now runs first, this gate lets the orchestrator request explicit user consent BEFORE any voice runs (so generation effort is never spent on a change the user might abort). It is true for sensitive/irreversible (blocklist) paths and, unlike `should_skip`, fails **safe**: an undeterminable change returns `consent_required=true` rather than silently bypassing consent.

## Output
- JSON object to stdout with keys: `should_skip`, `consent_required`, `magnitude`, `mode_ceiling`, `reason`, `signals`, `config_used`
- exit code 0 always (errors are reported inside the JSON, not via non-zero exit)

## WHAT — Contract
- Shall classify the change's magnitude (`low/medium/high/critical`) and derive a `mode_ceiling` from diff signals collected via `probe_change.py` (git) or pre-computed stdin JSON (`--signals-stdin`).
- Any path matching a blocklist entry shall force `should_skip=false`, `magnitude='critical'`, and `mode_ceiling='trias'` regardless of file or line counts.
- `CONSILIUM_FORCE_FULL=1` shall force `should_skip=false` and `magnitude='critical'` without reading the diff.
- Shall fail open on the cost gate: probe failures, missing git repos, and config load errors shall all produce `should_skip=false`; exit code shall always be 0.
- Shall emit `consent_required` — the pre-dispatch irreversibility consent gate the orchestrator uses to request explicit user consent before any voice runs. It shall be `true` on any blocklist (sensitive/irreversible path) hit and `false` on an ordinary non-sensitive change. Unlike `should_skip`, it shall fail **safe**: a probe or config failure shall return `consent_required=true` so an undeterminable change never silently bypasses consent.

## WHAT — Verify intent
- None - all questions resolved.

## Acceptance (= tests)
- A single-file, single-line change with no blocklist hits and default config returns `should_skip=true` and `magnitude='low'`.
- Any path matching a blocklist pattern returns `should_skip=false`, `magnitude='critical'`, and `mode_ceiling='trias'` regardless of file/line counts.
- Setting `CONSILIUM_FORCE_FULL=1` returns `should_skip=false` and `magnitude='critical'` without reading the diff.
- Using `--signals-stdin` with a pre-computed payload bypasses git and classifies magnitude purely from the payload values.
- A probe failure (e.g. not a git repo) returns `should_skip=false` with the error text in the `reason` field and exits 0.
- A blocklist (sensitive/irreversible) path returns `consent_required=true`; an ordinary non-sensitive change returns `consent_required=false`; a probe failure returns `consent_required=true` (fails safe, the opposite direction from `should_skip`). (`scripts/test_consent_gate.py`)
