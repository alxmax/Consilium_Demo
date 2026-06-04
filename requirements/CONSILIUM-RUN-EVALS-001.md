---
id: CONSILIUM-RUN-EVALS-001
status: confirmed
layer: feature
owner: auto
test_exempt: "subprocess-based eval harness — acceptance gated by run_evals.py itself in CI"
depends_on: []
risk: 1
---

# run_evals

> Subprocess-based regression harness over evals/scenarios.json; CI gate.

## Input
- `evals/scenarios.json` (default) or a custom path via `--scenarios`
- `--filter <substring>`: optional name filter applied to scenario list
- Each scenario's `stdin_json` field is serialised and piped to the target script
- Each scenario's `env` field is merged into the subprocess environment

## Description
Regression harness for all deterministic scripts in the Consilium pipeline. It reads a `scenarios.json` corpus, spawns each scenario's named tool as a subprocess, and verifies exit code, stdout (either as a JSON subset-match or a plain-text substring match), and stderr substrings against declared expectations. A pre-flight linter (`lint_validate_report_fixtures`) checks every `validate_report` fixture for the required `pipeline_executed` field and ensures bypass-chosen fixtures set it to `false`, catching fixture/validator drift at corpus level before any scenario runs. The script exits non-zero if any scenario fails, making it suitable as a CI gate.

## Output
- PASS/FAIL lines to stderr for each scenario
- Summary line `<N> passed, <M> failed` to stderr
- exit code 0 when all scenarios pass; 1 when any fail; 2 on load or corpus errors

## WHAT — Verify intent (open questions for the human)
- The description says stdout matching uses 'either a JSON subset-match or a plain-text substring match' — what determines which mode is used for a given scenario? Is it a field in `scenarios.json` (e.g., `expect_stdout_type`), and is the subset-match semantics defined (exact key equality, recursive inclusion, or type-only check)?
- The pre-flight linter checks for `pipeline_executed` in `validate_report` fixtures — does it also check that non-validate_report scenarios that produce a full report include `pipeline_executed`, or is the lint scoped only to `validate_report` fixtures?
- When `--filter` matches zero scenarios, the script exits 2 with 'no scenarios matched' — is this the same exit code as a corpus load error? Could the caller distinguish 'filter found nothing' from 'scenarios.json is malformed'?

## Acceptance (= tests)
- Running `python scripts/run_evals.py` against the committed `evals/scenarios.json` exits 0 with every scenario reporting PASS.
- Introducing a scenario with `expect_exit=0` but without `pipeline_executed` in `stdin_json` causes the script to exit 2 with a descriptive corpus error before running any scenario.
- A scenario with a bypass-chosen `chosen_approach` and `pipeline_executed=true` triggers the corpus pre-flight and exits 2.
- The `--filter` flag restricts execution to only matching scenario names, and an empty match set exits 2 with `no scenarios matched`.
- A scenario that fails its `expect_stdout_subset` check prints a human-readable mismatch message to stderr and exits 1.
