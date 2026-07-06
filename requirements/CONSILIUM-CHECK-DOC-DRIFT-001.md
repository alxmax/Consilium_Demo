---
milestone: v1.1
id: CONSILIUM-CHECK-DOC-DRIFT-001
status: confirmed
layer: feature
owner: auto
test_exempt: "reads live source files and runs git — integration-only gate"
depends_on: []
risk: 1
---

# check_doc_drift

> Enforces parity between authoritative behavior (SKILL.md, confidence.py) and the docs/diagrams.

## Input
- `modes/trias.md`: read for `trias_parallel_dispatch` and `trias_parallelism_runtime_audit` invariants
- `modes/sequential.md`: read for `sequential_scale_down_skips_control` and `sequential_generator_first` invariants
- `docs/architecture/src/modes.jsx`: read for `trias_tally_caption_confidence`, `explainer_modes_voices_generator_first`, and the Trias spec-alignment worst-case check
- `docs/architecture/src/trias.jsx`: read for `TRIAS_OUTCOMES` confidence parity check
- `docs/architecture/src/extras.jsx`: read by the Trias spec-alignment check (CostScatter TRI entry + CostBars trias row)
- `SKILL.md`: read for the `skill_templates_have_pipeline_executed` invariant
- `scripts/build_report.py`: read for `build_report_emits_pipeline_executed` invariant
- `scripts/confidence.py`: AST-parsed for `VOTE_PATTERN_CONFIDENCE` dict values
- `scripts/validate_report.py`: read for legacy MODE alias removal milestone check
- `.github/workflows/ci.yml` and `.claude/skills/run-consilium/driver.py`: read for test-suite coverage check
- `scripts/test_*.py`: globbed to enumerate all test suites requiring coverage
- `.github/workflows/ci.yml` and `docs/architecture/src/extras.jsx`: parsed for the `ci_checks_completeness` check (every non-test CI step must have a matching `CI_CHECKS` card or an `ALLOWED_OUT_OF_SCOPE_CI_STEPS` entry)
- `scripts/personalities.py`: AST-parsed for the `PERSONALITIES` list (name SSOT) for the `trias_personality_name_parity` check
- `docs/architecture/src/trias.jsx`, `docs/architecture/src/modes.jsx`, `scripts/make_full_architecture.py`: regex-scanned for Trias personality names, compared against `personalities.py`
- `modes/implement_pipeline.md`: regex-parsed for `subagents`/`cost_multiplier` frontmatter (SSOT) for the `implement_pipeline_spec_alignment` check
- `docs/architecture/src/extras.jsx`: `GATE_ITEMS` array (ImplementSection) scanned for the matching sub-agent count / cost-multiplier strings

## Description
Enforces parity between the authoritative behavior defined in SKILL.md and `scripts/confidence.py` and the human-readable documentation in `modes/*.md` and `docs/architecture/src/*.jsx`, preventing the class of silent drift found in the design audit of 2026-05-28 where four discrepancies had accumulated undetected. It runs seven independent check families: text-based regex invariants (required/forbidden patterns in specific files), Trias confidence parity between `confidence.py`'s `VOTE_PATTERN_CONFIDENCE` dict and the `TRIAS_OUTCOMES` table in `trias.jsx` (parsed via AST and regex respectively), legacy MODE alias removal milestone enforcement (ensures dated removal comments accompany deprecated aliases in `validate_report.py`), test-suite coverage (every `scripts/test_*.py` must appear in both `ci.yml` and the run-consilium driver), CI_CHECKS completeness (every non-test `ci.yml` step must be represented in the architecture explainer's `CI_CHECKS` card list, matched by exact script basename — added 2026-07-06 after a Trias self-audit found the explainer's own "what CI runs" section had silently fallen behind `ci.yml` itself), Trias personality-name parity (`scripts/personalities.py`'s `PERSONALITIES` names must match the explainer's `trias.jsx`/`modes.jsx` and the `make_full_architecture.py` poster generator — added 2026-07-06 after the v3 lens rename, PR #482, was found to have never touched those three files), and implement-pipeline spec alignment (`modes/implement_pipeline.md`'s `subagents`/`cost_multiplier` frontmatter must be stated explicitly in the "Code integration pipeline" explainer section's `GATE_ITEMS` — added 2026-07-06 after that section was found to be the only mode/flag whose headline sub-agent count and cost multiplier weren't shown anywhere in its own text). The script is intended to run before any commit that touches `modes/`, `docs/architecture/src/`, `scripts/confidence.py`, `scripts/personalities.py`, `.github/workflows/ci.yml`, or `scripts/test_*.py`.

## Output
- stdout: `doc-drift OK: all invariants hold` when all checks pass
- stderr: numbered list of violated invariants with pattern, source, and rationale for each failure
- exit code 0 when all invariants pass; 1 when one or more are violated; 2 when a required input file is missing

## WHAT — Verify intent
- None - all questions resolved.

## Contract (additional)
- Test-suite coverage uses plain substring match on the filename only (e.g., `test_round2.py`); a commented-out line that still contains the filename string passes the check — the script does not distinguish commented-out from active.
- Legacy MODE alias removal milestone date must be ISO `YYYY-MM-DD`; the date string must appear within 200 characters of the alias literal in `validate_report.py`; any comment syntax is accepted as long as the date string is present; future dates are accepted — the check only skips if the alias has already been removed from the file entirely.
- When multiple invariants are violated, all violations are collected across all seven check families before any output; the script prints every violation (numbered) to stderr then exits 1 — it never stops at the first failure.
- CI_CHECKS completeness matches on the invoked script's exact basename (e.g. `reqmap.py`), not the full run-line — two `ci.yml` steps that share one script (`reqmap.py gate --strict` / `reqmap.py map --check`) correctly resolve to the same single `CI_CHECKS` card. `scripts/test_*.py` steps are always skipped (covered generically by the "Unit suites" card). A step with no `scripts/*.py`/`docs/architecture/build.py` reference (e.g. an inline bash check) must have a named `ALLOWED_OUT_OF_SCOPE_CI_STEPS` entry or the check fails.
- Trias personality-name parity is case-insensitive (`personalities.py` uses lowercase, the explainer/poster use Title Case) and compares 3 independent structured sources against the SSOT separately — a drift in only one of `trias.jsx` / `modes.jsx` / `make_full_architecture.py` is reported for that source specifically, not merged into one opaque failure.
- Implement-pipeline spec alignment reuses `check_trias_spec_alignment`'s `_COST_FMT` explicit float→string map (never `f'{v}×'`) and reports the sub-agent-count and cost-multiplier omissions as two independent failures, not one merged message.

## Acceptance (= tests)
- When all invariant patterns hold and `confidence.py VOTE_PATTERN_CONFIDENCE` matches `trias.jsx TRIAS_OUTCOMES` for patterns 3-0, 2-1, and 2-0, the script exits 0 and prints the OK message.
- If the scale_down wording in `modes/sequential.md` regresses to "Skip Generator AND Control", the `sequential_scale_down_skips_control` invariant fails and the script exits 1.
- If `confidence.py VOTE_PATTERN_CONFIDENCE['2-1']` is changed to a value that differs from the `conf` field of the `2-1` row in `trias.jsx TRIAS_OUTCOMES`, the trias confidence parity check reports a failure.
- If a new `scripts/test_*.py` file is added without a corresponding entry in `ci.yml`, the `test_suite_coverage` check fails and exits 1.
- If a required file listed in an invariant's `file` key is missing from disk, the script exits 2 immediately.
- If a new named `ci.yml` step invokes a script with no matching `CI_CHECKS` card and no `ALLOWED_OUT_OF_SCOPE_CI_STEPS` entry, `check_ci_checks_completeness` reports a failure naming the step and the script (`scripts/test_check_doc_drift.py`).
- Two `ci.yml` steps invoking the same script under different flags (e.g. `reqmap.py`) do not double-fail or need two cards.
- If any of `trias.jsx`'s `LENSES`, `modes.jsx`'s `personalities` array, or `make_full_architecture.py`'s `personalities_row` regresses to a retired personality name (e.g. `Pioneer`), `check_trias_personality_name_parity` reports a failure naming the offending file (`scripts/test_check_doc_drift.py`).
- If extras.jsx's `GATE_ITEMS` (ImplementSection) loses its sub-agent-count or cost-multiplier string, `check_implement_pipeline_spec_alignment` reports the corresponding failure(s); a missing `subagents`/`cost_multiplier` field in `modes/implement_pipeline.md`'s own frontmatter exits 2.

## Why test_exempt

`check_doc_drift.py` reads live source files and runs `git` commands — its correctness depends on the actual repo tree having specific file states (mode docs, architecture JSX, `confidence.py` constants, CI config). Simulating that tree faithfully in a fixture would be more complex and brittle than the script itself for most of its check families. The CI step against the actual repo IS the acceptance test for those. The `ci_checks_completeness`, `trias_personality_name_parity`, and `implement_pipeline_spec_alignment` check families are exceptions — all are pure functions of file text, unit-tested directly in `scripts/test_check_doc_drift.py` (mirrors `CONSILIUM-CHECK-PUBLIC-LEAK-001`, which is also `test_exempt` overall yet has real unit-tested pure-function seams).

<!-- verified-by: scripts/test_check_doc_drift.py -->
