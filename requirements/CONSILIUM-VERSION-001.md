---
id: CONSILIUM-VERSION-001
status: deprecated
layer: bus
owner: auto
depends_on: []
risk: 0
---

# version

> Git-derived version provenance: display stamp, bare committed ref, and prompt-change drift count.

## Input
- No files read; all data comes from `git` subprocess calls against the repo root
- CLI flags: (none) prints display stamp; `--ref` prints bare committed HEAD sha; `--drift REF` prints diff `--stat` of `prompts/` + `modes/` since REF

## Description
Provides two distinct version provenance fields that the deliberation pipeline stamps onto every run record. `consilium_version()` returns a human-readable display string (`git describe --tags --always --dirty`, e.g. `v1.0.0-3-gabc123`) for display and provenance; `consilium_ref()` returns a bare committed HEAD sha usable as a `git diff` operand, or an empty string when the working tree is dirty or git is unavailable - because a dirty-tree sha cannot be reconstructed. `prompts_changed_since(ref)` counts how many `prompts/` and `modes/` files changed since a given ref, enabling Step-0 stale-prompt advisories without ever raising or shelling a malformed diff (it returns 0 silently when the ref is empty, `unknown`, or unresolvable). The module's design principle is that git is the version system: no bespoke per-prompt registry is needed because git already content-hashes, versions, and diffs everything.

## Output
- stdout: display stamp, bare ref, or diff `--stat` depending on CLI flag
- exit code 0 in all cases (fails open); returns `''` or `'unknown'` when git is unavailable rather than erroring

## WHAT — Verify intent (open questions for the human)
- `consilium_ref()` returns `''` when the working tree has uncommitted tracked changes — does 'uncommitted tracked changes' include staged-but-not-committed changes, or only unstaged modifications? The distinction matters for CI environments that stage files during build.
- `prompts_changed_since` returns 0 silently for unresolvable refs — but a caller that passes a stale ref (e.g., a deleted branch) would receive 0 and incorrectly conclude no prompts changed; is silent 0 the right behavior, or should there be an out-of-band signal indicating resolution failure?
- The `--drift REF` flag diffs only `prompts/` and `modes/` — but `scripts/aggregator.py` and `scripts/confidence.py` also affect deliberation behavior; is restricting drift detection to prompts and modes intentional, or an omission?

## Acceptance (= tests)
- `consilium_version()` returns a non-empty string and never raises, even when git is absent or the repo has no tags.
- `consilium_ref()` returns `''` (empty string) when the working tree has uncommitted tracked changes, and returns a 40-character hex sha when the tree is clean.
- `prompts_changed_since` returns 0 without raising for any of: empty string ref, `unknown`, or a ref that does not exist in the repo.
- `--drift REF` prints a human-readable diff `--stat` of `prompts/` and `modes/` for a valid ref, and prints a `does not resolve` message for an invalid ref.
- `ref_resolves` returns `False` for empty string and `unknown`, and `True` only for a reachable commit sha or tag.
