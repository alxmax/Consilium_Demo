# Eval harness

Regression suite for max-agent's deterministic scripts. Catches behavioral
drift when you edit `scripts/*.py` (e.g., did changing the sigmoid steepness
in `aggregator.py` accidentally make `risk_adjusted_utility` pick the risky
candidate?).

**Scope.** Eval covers only deterministic scripts: `aggregator.py`,
`confidence.py`, `validate_report.py`, `strip_context.py`, `dialectic_merge.py`.
LLM-driven voice prompts (`prompts/*.md`) are not testable here — that needs
a separate replay harness with golden voice outputs (deferred).

## Run

```bash
python scripts/run_evals.py                 # all scenarios
python scripts/run_evals.py --filter aggregator     # name substring
python scripts/run_evals.py --scenarios path.json   # alternate fixture file
```

Exit 0 if all pass, 1 if any fail. Each failure prints to stderr with the
scenario name and the specific mismatch (exit code, stdout subset, missing
stderr substring).

## Scenario schema

`scenarios.json` is a JSON array. Each entry:

```json
{
  "name": "human-readable name shown in pass/fail output",
  "tool": "scripts/aggregator.py",
  "args": ["--scheme", "majority"],
  "stdin_json": { ... } | null,
  "expect_exit": 0,
  "expect_stdout_subset": { ... },
  "expect_stderr_contains": ["substring1", "substring2"]
}
```

- `tool` — repo-relative path; runner invokes via `python <repo>/<tool>`
- `args` — optional CLI args appended after `tool`
- `stdin_json` — optional; serialized as JSON string and piped to stdin
- `expect_exit` — required process exit code (default 0)
- `expect_stdout_subset` — optional dict-subset match against parsed stdout JSON.
  Recursive: every key/value in expected must appear in actual; lists must
  match exactly. Use `{}` to assert "stdout is valid JSON" without pinning fields.
- `expect_stderr_contains` — optional list of substrings; all must appear in stderr
- `expect_stdout_contains` — optional list of substrings; all must appear in stdout (for scripts that emit plain text, not JSON)

## Adding cases

Two rules:

1. **Pin only what you care about.** Use `expect_stdout_subset: {"chosen": "x"}`
   instead of dumping the entire output — keeps fixtures stable across
   incidental field additions.
2. **Name the behavior, not the implementation.** `aggregator/conservative_override
   vetoes risky candidate` ages well; `aggregator scores 0.612 for safe` does not.

When adding a new deterministic script, add 2-4 scenarios covering its
contract. When changing existing behavior intentionally, update the
matching scenario in the same commit.
