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

## Acceptance (= tests)
- Running `python scripts/run_evals.py` against the committed `evals/scenarios.json` exits 0 with every scenario reporting PASS.
- Introducing a scenario with `expect_exit=0` but without `pipeline_executed` in `stdin_json` causes the script to exit 2 with a descriptive corpus error before running any scenario.
- A scenario with a bypass-chosen `chosen_approach` and `pipeline_executed=true` triggers the corpus pre-flight and exits 2.
- The `--filter` flag restricts execution to only matching scenario names, and an empty match set exits 2 with `no scenarios matched`.
- A scenario that fails its `expect_stdout_subset` check prints a human-readable mismatch message to stderr and exits 1.
