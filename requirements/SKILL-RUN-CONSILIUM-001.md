---
milestone: v1.1
test_exempt: "integration harness — acceptance validated by run-consilium smoke + pipeline commands, not unit tests"
id: SKILL-RUN-CONSILIUM-001
status: confirmed
level: code
layer: feature
owner: alxmax
depends_on: [CONSILIUM-VALIDATE-REPORT-001, CONSILIUM-AGGREGATOR-001, CONSILIUM-CONFIDENCE-001]
risk: 1
satisfies: [ARCH-CONSILIUM-REPO-GATES-001]
---

# run-consilium driver

> Single entry point exercising Consilium's deterministic LLM-free surface (smoke / pipeline / shot).

## Description

Every line in this section is binding.

- `driver.py` is the single entry point exercising Consilium's entire deterministic, LLM-free surface, in one command; the script exists because Consilium has no single runnable app, and this driver replaces "run the app" for a skill-based deliberation system.
- In `smoke` mode, `driver.py` runs all the `scripts/test_*.py` unit suites, the `check_doc_drift.py` invariant gate, and the `docs/architecture` build `--check`.
- In `smoke` mode, `driver.py` also runs the full bundle → build_report → validate_report pipeline, reporting PASS/FAIL per step.
- `smoke` mode exits non-zero only when failures exceed a documented baseline.
- In `pipeline` mode, `driver.py` demos the aggregator → confidence → build_report → validate_report chain with inline synthetic input, printing each stage's JSON to stdout so the developer can see the data flowing through the pipeline; it exits 0.
- In `shot` mode, `driver.py` screenshots `docs/architecture.html` using headless Chrome or Edge, writing the PNG to `.consilium/shots/architecture.png` by default, or to the caller-supplied path.
- `shot` mode reads `docs/architecture.html` and checks for Chrome or Edge at known Windows paths.
- `smoke` and `pipeline` modes read `bundle_smoke_tests.json` from the repo root.
- `driver.py` injects `PYTHONUTF8=1` and `PYTHONIOENCODING=utf-8` into all child process environments.
- Stdout carries per-step PASS/FAIL lines with exit codes and failure tails, up to 12 lines.

## Verify intent

- None - all questions resolved.

## Cases

- **CASE-1** — Given the current repo state, when `python .claude/skills/run-consilium/driver.py smoke` runs, then it exits 0 with all suites PASS.
- **CASE-2** — Given the current repo state, when `python .claude/skills/run-consilium/driver.py pipeline` runs, then it prints valid JSON for each of the four pipeline stages and exits 0.
- **CASE-3** — Given Chrome or Edge is available, when `python .claude/skills/run-consilium/driver.py shot` runs, then it writes a non-empty PNG to `.consilium/shots/architecture.png`.
- **CASE-4** — Given a failing test suite, when `smoke` runs, then it prints the failure tail (up to 12 lines) and exits non-zero.
- **CASE-5** — Given non-ASCII output from a child process, when the driver runs, then the injected `PYTHONUTF8=1` prevents a codec error on Windows.

## Context (non-binding)

**Current implementation** — `.claude/skills/run-consilium/driver.py`.

## Why test_exempt

`driver.py` IS the test runner: its `smoke` command invokes every `scripts/test_*.py` unit suite, the `check_doc_drift.py` invariant gate, and the full build_report → validate_report pipeline. Writing a unit test for a script whose purpose is to run other tests would be circular — the driver's acceptance is the `smoke` run itself. Running `python .claude/skills/run-consilium/driver.py smoke` against the actual repo IS the authoritative acceptance check.
