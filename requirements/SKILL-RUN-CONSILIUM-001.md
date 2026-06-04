---
test_exempt: "integration harness — acceptance validated by run-consilium smoke + pipeline commands, not unit tests"
id: SKILL-RUN-CONSILIUM-001
status: confirmed
layer: feature
owner: auto
depends_on: [CONSILIUM-VALIDATE-REPORT-001, CONSILIUM-AGGREGATOR-001, CONSILIUM-CONFIDENCE-001]
risk: 1
---

# run-consilium driver

> Single entry point exercising Consilium's deterministic LLM-free surface (smoke / pipeline / shot).

## Input
- CLI positional arg: `smoke` (default), `pipeline`, or `shot [OUT.png]`
- `smoke` and `pipeline` read `bundle_smoke_tests.json` from the repo root
- `shot` reads `docs/architecture.html` and checks for Chrome/Edge at known Windows paths
- `PYTHONUTF8=1` and `PYTHONIOENCODING=utf-8` are injected into all child processes

## Description
The run-consilium skill driver exercises Consilium's entire deterministic, LLM-free surface in one command. In `smoke` mode it runs all the `scripts/test_*.py` unit suites, the `check_doc_drift.py` invariant gate, the `docs/architecture` build `--check`, and the full bundle->build_report->validate_report pipeline, reporting PASS/FAIL per step and exiting non-zero only when failures exceed a documented baseline. In `pipeline` mode it demos the aggregator -> confidence -> build_report -> validate_report chain with inline synthetic input, printing each stage's JSON so the developer can see the data flowing through the pipeline. In `shot` mode it screenshots `docs/architecture.html` using headless Chrome or Edge, writing the PNG to `.consilium/shots/architecture.png` by default. The driver exists because Consilium has no single runnable app - this script is the single entry point that replaces "run the app" for a skill-based deliberation system.

## Output
- stdout: per-step PASS/FAIL lines with exit codes and failure tails (up to 12 lines)
- exit code 0 iff all steps passed (`smoke`/`pipeline`) or screenshot written (`shot`)
- `shot` writes a PNG file to `.consilium/shots/architecture.png` or the caller-supplied path
- `pipeline` prints aggregator JSON, confidence JSON, and validate_report result to stdout

## Acceptance (= tests)
- `python .claude/skills/run-consilium/driver.py smoke` exits 0 against the current repo state with all suites PASS.
- `python .claude/skills/run-consilium/driver.py pipeline` prints valid JSON for each of the four pipeline stages and exits 0.
- `python .claude/skills/run-consilium/driver.py shot` writes a non-empty PNG to `.consilium/shots/architecture.png` when Chrome or Edge is available.
- A failing test suite causes `smoke` to print the failure tail (up to 12 lines) and exit non-zero.
- The driver injects `PYTHONUTF8=1` into all child process environments, ensuring non-ASCII output (e.g. arrows in trace_graph) does not cause codec errors on Windows.
