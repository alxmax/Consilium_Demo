---
id: CONSILIUM-PERSONALITIES-001
status: baseline
layer: bus
owner: auto
depends_on: []
risk: 1
---

# personalities

> Canonical registry of the three fixed Trias personalities (Pioneer/Architect/Steward) and their voice weights.

## Input
- CLI flag `--name`: optional filter to emit a single personality by name (`pioneer | architect | steward`)
- Legacy positional argument N: rejected with exit code 2 and a migration message

## Description
Canonical registry of the three fixed Trias-mode personalities (Pioneer, Architect, Steward), each defined by a named set of voice-weighting coefficients and a path to a lens prompt file. It replaces the old random-sampling Ensemble approach with deterministic, named characters so that Trias deliberations are reproducible and auditable. Each personality biases the weighted aggregation of Generator, Control, and Conservator scores differently: Pioneer weights novelty (generator 0.49), Architect balances all three equally around Control (control 0.40), and Steward emphasizes risk-aversion (conservator 0.40). The script is also imported as a library by the Trias orchestration layer via `get_by_name()`, which returns a deep copy to prevent mutation of the module-level registry at runtime.

## Output
- JSON array of all three personality dicts emitted to stdout when called with no `--name` flag
- JSON object for a single personality emitted to stdout when `--name` is provided
- exit code 0 on success; exit code 2 when a legacy positional N argument is detected, with a human-readable migration message on stderr

## Acceptance (= tests)
- Running without arguments emits a JSON array of exactly 3 objects, each containing `name`, `weights` (with keys `generator`, `control`, `conservator` summing to 1.0), and `lens` (a path string).
- Running with `--name pioneer` emits a single JSON object matching the Pioneer entry; the returned dict is a deep copy and mutations do not affect subsequent calls.
- Running with a positional integer argument exits with code 2 and prints a migration message referencing the three valid personality names.
- `get_by_name('unknown')` raises `KeyError` with a message listing valid names.
- The weights for all three personalities each have `generator + control + conservator == 1.0` (within floating-point tolerance).
