---
id: CONSILIUM-SCOPE-GATE-001
status: confirmed
layer: feature
owner: auto
depends_on: []
risk: 1
---

# scope_gate

> Decides whether a change is small enough to bypass full deliberation; fails open.

## Input
- Git working tree diff via `probe_change.py` (default: HEAD, or `--ref <ref>..HEAD`, or `--range <A>..<B>`)
- `--files`: optional path restriction for the git diff
- `--config`: optional path to a `scope_gate.json` overriding `max_files`, `max_lines`, and `blocklist`
- stdin JSON when `--signals-stdin` is set: `{files_changed, lines_added, lines_removed, paths}`
- `CONSILIUM_FORCE_FULL` env variable: if `1`, always returns `should_skip=false`

## Description
Decides whether a change is small enough to bypass full deliberation. It collects diff signals either from git via `probe_change.py` or from pre-computed stdin JSON, checks file and line counts against configurable thresholds, and scans changed paths against a sensitive-path blocklist. Based on those signals it classifies the change's magnitude (`low/medium/high/critical`) and derives a `mode_ceiling` (the maximum appropriate deliberation mode), then outputs a JSON decision the orchestrator uses to short-circuit or proceed. The gate fails open: probe failures, missing git repos, or config load errors all produce `should_skip=false` so that uncertain situations always trigger deliberation rather than silently skipping it.

## Output
- JSON object to stdout with keys: `should_skip`, `magnitude`, `mode_ceiling`, `reason`, `signals`, `config_used`
- exit code 0 always (errors are reported inside the JSON, not via non-zero exit)

## WHAT — Verify intent (open questions for the human)
- The `mode_ceiling` output field maps magnitude to a maximum deliberation mode — is the full mapping table (low→?, medium→?, high→?, critical→trias) specified anywhere, or only the critical→trias case documented in the acceptance tests?
- When `--signals-stdin` is used, the `paths` field is accepted — but the blocklist check requires path matching; is the `paths` field compared against the blocklist the same way as git-diff paths, and what format are paths expected in (relative to repo root, absolute, etc.)?
- The gate 'fails open' on probe failures — but `CONSILIUM_FORCE_FULL=1` also returns `should_skip=false`; do both paths produce identical JSON shapes, or does the forced-full path produce a different reason field?

## Acceptance (= tests)
- A single-file, single-line change with no blocklist hits and default config returns `should_skip=true` and `magnitude='low'`.
- Any path matching a blocklist pattern returns `should_skip=false`, `magnitude='critical'`, and `mode_ceiling='trias'` regardless of file/line counts.
- Setting `CONSILIUM_FORCE_FULL=1` returns `should_skip=false` and `magnitude='critical'` without reading the diff.
- Using `--signals-stdin` with a pre-computed payload bypasses git and classifies magnitude purely from the payload values.
- A probe failure (e.g. not a git repo) returns `should_skip=false` with the error text in the `reason` field and exits 0.
