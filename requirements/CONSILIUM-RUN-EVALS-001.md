---
milestone: v1.1
id: CONSILIUM-RUN-EVALS-001
status: confirmed
level: code
layer: feature
owner: alxmax
test_exempt: "subprocess-based eval harness — acceptance gated by run_evals.py itself in CI"
depends_on: []
risk: 1
satisfies: [ARCH-CONSILIUM-REPO-GATES-001]
---

# run_evals

> Subprocess-based regression harness over evals/scenarios.json; CI gate.

## Description

Every line in this section is binding.

- `run_evals.py` is the regression harness for all deterministic scripts in the Consilium pipeline.
- `run_evals.py` reads a `scenarios.json` corpus: `evals/scenarios.json` by default, or the path given by `--scenarios`.
- `--filter <substring>` optionally restricts execution to scenarios whose name matches the substring.
- For each scenario, `run_evals.py` spawns the scenario's named tool as a subprocess. The scenario's `stdin_json` field is serialised and piped to the subprocess; the scenario's `env` field is merged into the subprocess environment.
- `run_evals.py` verifies each subprocess's exit code against the scenario's declared expectation.
- `run_evals.py` verifies stdout against the scenario's declared expectation, as either a JSON subset-match or a plain-text substring match.
- `run_evals.py` verifies stderr against the scenario's declared substring expectations.
- A pre-flight linter (`lint_validate_report_fixtures`) runs before any scenario. The linter checks every `validate_report` fixture for the required `pipeline_executed` field, and ensures bypass-chosen fixtures set it to `false`.
- A corpus violation found by the pre-flight linter exits 2 before any scenario runs.
- PASS/FAIL lines print to stderr for each scenario.
- A summary line `<N> passed, <M> failed` prints to stderr.
- Exit code is 0 when all scenarios pass, 1 when any fail, and 2 on load or corpus errors.

## Verify intent

- None - all questions resolved.

## Cases

- **CASE-1** — Given the committed `evals/scenarios.json`, when `python scripts/run_evals.py` runs, then it exits 0 with every scenario reporting PASS.
- **CASE-2** — Given a scenario with `expect_exit=0` but no `pipeline_executed` in `stdin_json`, when the pre-flight linter runs, then it exits 2 with a descriptive corpus error before any scenario runs.
- **CASE-3** — Given a scenario with a bypass-chosen `chosen_approach` and `pipeline_executed=true`, when the pre-flight linter runs, then it exits 2.
- **CASE-4** — Given the `--filter` flag, when it is applied, then execution is restricted to matching scenario names; an empty match set exits 2 with `no scenarios matched`.
- **CASE-5** — Given a scenario that fails its `expect_stdout_subset` check, when it runs, then a human-readable mismatch message prints to stderr and the harness exits 1.

## Why test_exempt

`run_evals.py` is a subprocess orchestrator — it runs multiple Python scripts as child processes against fixture JSON and collects exit codes. Unit-testing it would require mocking every subprocess call, which tests the mock harness rather than the actual harness behavior. The harness is self-validating: running `python scripts/run_evals.py` in CI IS the acceptance test — all scenarios from `evals/scenarios.json` must pass, and the script itself exits non-zero if any fail.

## Context (non-binding)

**Notes** — The non-zero exit on any scenario failure is what makes the harness suitable as a CI gate.

**Current implementation** — `scripts/run_evals.py`
