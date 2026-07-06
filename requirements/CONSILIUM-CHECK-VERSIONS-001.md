---
milestone: v1.4.0
id: CONSILIUM-CHECK-VERSIONS-001
status: confirmed
layer: feature
owner: auto
depends_on: []
risk: 1
---

# check_versions

> Fails CI if `plugin.json` and `marketplace.json` semver drift apart, or if `reqmap.py`'s MAP_ENGINE_VERSION is not a valid dated engine version.

## Input
- `.claude-plugin/plugin.json` `version` field (the canonical semver source)
- `.claude-plugin/marketplace.json` top-level `version` + each `plugins[].version`
- `scripts/reqmap.py` `MAP_ENGINE_VERSION` constant (a separate, non-semver axis)
- CLI flags: `--fix` (propagate the canonical version into marketplace.json)

## Description
The plugin's semver lives in two static manifests that no single process can derive
at load time — Claude Code reads `plugin.json` / `marketplace.json` as data, and
neither can import the other to stay in sync automatically. This script is the
single point that asserts they agree, so drift fails the build instead of shipping
silently. Mirrors `requirement-manager`'s `scripts/check_versions.py` (same
mechanism, adopted 2026-07-06 after `marketplace.json` was found to have no
`version` field at all while `plugin.json` had already drifted from an orphan
`v1.4.0` git tag). `MAP_ENGINE_VERSION` is checked independently — it is a
staleness-compare date stamp for the requirement-map engine, not a semver, and is
never compared against the plugin version.

## Output
- stdout: `OK  semver aligned at '<version>' across N location(s); engine MAP_ENGINE_VERSION = '<date>'` on success
- stderr-equivalent (stdout): `FAIL  version drift detected:` plus a per-location diff on mismatch
- exit 0 aligned, exit 1 drift detected, exit 2 a manifest/field is missing or unreadable

## WHAT — Contract (normative)
- `plugin.json`'s `version` field is the canonical source; every `version` occurrence in `marketplace.json` (top-level and each `plugins[]` entry) must equal it exactly (string equality, no semver-range logic).
- A non-dict entry in `marketplace.json`'s `plugins[]` array is reported as a readable diagnostic (exit 1), never an unhandled `AttributeError`.
- `MAP_ENGINE_VERSION` must match `YYYY-MM-DD` optionally followed by `.N` (N a positive integer, same-day revision suffix); the regex anchor is line-start so a docstring/comment mention preceding the real assignment cannot be matched instead.
- `--fix` rewrites only `marketplace.json` (never `plugin.json`, which stays the hand-edited canonical source) and is a no-op (exit 0, no write) when already aligned.

## WHAT — Verify intent
- None — resolved.

## Acceptance (= tests)
- Aligned manifests (plugin/marketplace/engine all valid) exit 0 (`scripts/test_check_versions.py`).
- A `marketplace.json` top-level or per-plugin-entry version mismatch exits 1.
- A missing `plugin.json` `version` field exits 2.
- A non-dict `plugins[]` entry exits 1 without raising.
- `MAP_ENGINE_VERSION` docstring mentions before the real assignment are ignored (anchored regex).
- Same-day revision suffixes (`.1`, `.2`, ...) are valid; `.0` and non-numeric suffixes are not.
- `--fix` propagates `plugin.json`'s version into both `marketplace.json` locations and a subsequent unflagged run then passes.

<!-- verified-by: scripts/test_check_versions.py -->
