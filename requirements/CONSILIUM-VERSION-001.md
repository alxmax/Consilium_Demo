---
milestone: v1.2
id: CONSILIUM-VERSION-001
status: confirmed
layer: bus
owner: auto
depends_on: []
risk: 1
---

# version

> Repo version provenance: git-describe display stamp, resolvable committed-HEAD ref, and a guarded prompt-drift counter — the primitives every report producer stamps into telemetry.

## Input
- The git repository state of the Consilium checkout (`git describe`, `git status --porcelain`, `git rev-parse`), read via subprocess
- `prompts_changed_since(ref)` / `--drift <ref>`: a prior `consilium_ref` value to diff `prompts/` + `modes/` against
- CLI flags: `--version` (default), `--ref`, `--drift <ref>`

## Description
Single home for version provenance, separated from report assembly (`build_report`, which merely consumes these values). `consilium_version()` returns the human display stamp (`git describe --tags --always --dirty`) and FAILS OPEN to `"unknown"` when git is absent or errors. `consilium_ref()` returns the resolvable diff operand: the committed HEAD sha on a clean tree, and `""` — by contract, never a `<sha>-dirty` string — on a dirty or unknown tree, so a recorded ref is always `git checkout`-able. `prompts_changed_since(ref)` counts prompt/mode files changed since a prior ref and NEVER raises: it returns 0 on `""`/`"unknown"`/unreachable refs, so the Step-0 `prompt_drift` advisory can call it unconditionally. Origin of the split: review 2026-05-31_200016 (versioning-provenance-design); retagged out of CONSILIUM-BUILD-REPORT-001 on 2026-07-03 (review backlog-disposition audit, item b) because impact analysis on the report assembler was pulling in unrelated provenance code.

## Output
- `consilium_version()` → non-empty display string, `"unknown"` when git is unavailable
- `consilium_ref()` → committed HEAD sha (clean tree) or `""` (dirty/unknown tree)
- `ref_resolves(ref)` → bool; short-circuits `""`/`"unknown"` to False without a git call
- `prompts_changed_since(ref)` → int ≥ 0, never raises
- CLI prints the requested value to stdout; exit 0

## WHAT — Contract
- Shall return a `consilium_version` display stamp that fails open to `"unknown"` (never raises) when git is absent.
- Shall return `consilium_ref` as either the committed HEAD sha or `""` on a dirty/unknown tree — never a `-dirty`-suffixed or otherwise unresolvable string.
- `prompts_changed_since` shall never raise and shall return 0 for empty, `"unknown"`, or unreachable refs.
- `ref_resolves` shall return False for `""` and `"unknown"` without invoking git.

## WHAT — Verify intent
- None - the report-stamping obligation (every producer writes these two fields into telemetry) belongs to CONSILIUM-BUILD-REPORT-001 and the two hand-built SKILL.md templates; this requirement covers only the provenance primitives themselves.

## Acceptance (= tests)
- With `_git` stubbed to fail: `consilium_version() == "unknown"`, `consilium_ref() == ""`, `ref_resolves("abc") is False`, `prompts_changed_since("abc") == 0` (`scripts/test_version.py`).
- With a dirty-tree stub: `consilium_ref() == ""`; with a clean-tree stub: `consilium_ref()` equals the HEAD sha.
- `ref_resolves("")` and `ref_resolves("unknown")` are False without a git call.
- On a real repo, `consilium_version()` returns a non-empty string.

<!-- verified-by: scripts/test_version.py -->
