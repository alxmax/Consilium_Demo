---
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
- `modes/sequential.md`: read for `sequential_scale_down_skips_pipeline` invariant
- `docs/architecture/src/modes.jsx`: read for `parallel_auto_is_two_turn`, `trias_tally_caption_confidence`, and `parallel_auto_gen_dependency_edges` invariants
- `docs/architecture/src/trias.jsx`: read for `TRIAS_OUTCOMES` confidence parity check
- `docs/architecture/src/extras.jsx`: read for `costscatter_parallel_cost_parity` invariant
- `SKILL.md`: read for `silent_audit_implemented` and `skill_templates_have_pipeline_executed` invariants
- `scripts/build_report.py`: read for `build_report_emits_pipeline_executed` invariant
- `scripts/confidence.py`: AST-parsed for `VOTE_PATTERN_CONFIDENCE` dict values
- `scripts/validate_report.py`: read for legacy MODE alias removal milestone check
- `.github/workflows/ci.yml` and `.claude/skills/run-consilium/driver.py`: read for test-suite coverage check
- `scripts/test_*.py`: globbed to enumerate all test suites requiring coverage

## Description
Enforces parity between the authoritative behavior defined in SKILL.md and `scripts/confidence.py` and the human-readable documentation in `modes/*.md` and `docs/architecture/src/*.jsx`, preventing the class of silent drift found in the Senate audit of 2026-05-28 where four discrepancies had accumulated undetected. It runs four independent check families: text-based regex invariants (required/forbidden patterns in specific files), Trias confidence parity between `confidence.py`'s `VOTE_PATTERN_CONFIDENCE` dict and the `TRIAS_OUTCOMES` table in `trias.jsx` (parsed via AST and regex respectively), legacy MODE alias removal milestone enforcement (ensures dated removal comments accompany deprecated aliases in `validate_report.py`), and test-suite coverage (every `scripts/test_*.py` must appear in both `ci.yml` and the run-consilium driver). The script is intended to run before any commit that touches `modes/`, `docs/architecture/src/`, `scripts/confidence.py`, or `scripts/test_*.py`.

## Output
- stdout: `doc-drift OK: all invariants hold` when all checks pass
- stderr: numbered list of violated invariants with pattern, source, and rationale for each failure
- exit code 0 when all invariants pass; 1 when one or more are violated; 2 when a required input file is missing

## WHAT — Verify intent (open questions for the human)
- None — doc is unambiguous.

## Acceptance (= tests)
- When all invariant patterns hold and `confidence.py VOTE_PATTERN_CONFIDENCE` matches `trias.jsx TRIAS_OUTCOMES` for patterns 3-0, 2-1, and 2-0, the script exits 0 and prints the OK message.
- If `scripts/audit_counter.py` is removed from SKILL.md or a forbidden `pending` caveat phrase is re-introduced, the `silent_audit_implemented` invariant fails and the script exits 1.
- If `confidence.py VOTE_PATTERN_CONFIDENCE['2-1']` is changed to a value that differs from the `conf` field of the `2-1` row in `trias.jsx TRIAS_OUTCOMES`, the trias confidence parity check reports a failure.
- If a new `scripts/test_*.py` file is added without a corresponding entry in `ci.yml`, the `test_suite_coverage` check fails and exits 1.
- If a required file listed in an invariant's `file` key is missing from disk, the script exits 2 immediately.
