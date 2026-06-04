---
id: CONSILIUM-MEMORY-001
status: baseline
layer: feature
owner: auto
test_exempt: "file I/O and integration layer with trivial pure stubs"
depends_on: [CONSILIUM-FEEDBACK-001, CONSILIUM-UTILS-001]
risk: 1
---

# memory

> Unified read API over Consilium's three memory tiers (short / medium / long).

## Input
- CLI flag `--tier`: one of `short | medium | long | all` (default: `all`)
- CLI flag `--n`: maximum number of entries returned per tier (default: 10)
- CLI flag `--query`: optional substring filter applied to medium (`success_criterion` + `chosen_approach`) and long (`context` + `chosen` + `note`) tiers
- CLI flag `--feedback-file`: optional override path to FEEDBACK.html
- CLI flag `--runs-dir`: optional override path to the `runs/` directory
- `.consilium/runs/*.json`: episodic deliberation records read for the medium tier
- `.consilium/FEEDBACK.html`: aggregated feedback journal read for the long tier

## Description
Provides a unified read API over Consilium's three memory tiers - short (current session, stub only), medium (per-run episodic JSON files in `runs/`), and long (aggregate FEEDBACK.html parsed via `feedback.py`) - through a single CLI and importable surface. It exists so that an orchestrating agent can ask "what does Consilium remember about X" without knowing which tier holds the relevant data; the `--query` flag applies a substring filter uniformly across medium and long tiers. The short tier is represented by a descriptive stub because its content (the deliberation bundle being assembled) is only accessible inside the active agent context window. Confirmed-outcome rows (those carrying `[confirmed]` in their note, written by `mark_outcome.py`) are flagged in long-tier output so callers can apply higher trust weights to them.

## Output
- JSON object emitted to stdout: for a single tier, a dict with `tier`, `entries`, and `total` keys; for `--tier all`, a dict with `short`, `medium`, and `long` sub-objects
- exit code 0 always (no error paths beyond missing files, which return empty entry lists)

## Acceptance (= tests)
- Running with `--tier medium` returns a JSON object whose `entries` array contains at most `--n` items, each with `run`, `date`, `success_criterion`, `chosen`, and `confidence` fields drawn from `runs/*.json` files.
- Running with `--tier long --query <term>` returns only rows whose `context`, `chosen`, or `note` contains the query term (case-insensitive), and each entry includes a `confirmed` boolean reflecting presence of `[confirmed]` in the note.
- Running with `--tier short` returns a stub dict with `entries: []` and a descriptive `note` explaining session-local scope.
- Running with `--tier all` returns a dict with exactly three keys (`short`, `medium`, `long`), each containing valid tier output.
- Passing `--feedback-file` and `--runs-dir` overrides the default `.consilium/` paths so the script can operate on arbitrary copies of the data.
