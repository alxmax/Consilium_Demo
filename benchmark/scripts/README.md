# Benchmark scripts

Wrappers around `run_task.py` for running the benchmark.

`scripts/run.py` is a Python convenience runner with subcommands. By default
it runs in **append mode**: each cell auto-detects the highest existing
`rep_N` slot and writes the next runs starting from `rep_(max+1)`, preserving
prior data. Pass `--clean` to wipe a cell (default slot + all `rep_*` dirs)
before running. Run from anywhere — scripts always resolve paths relative to
the repo root.

## Convenience runners

| What it does                    | Command                                                  |
|---------------------------------|----------------------------------------------------------|
| All 7 modes × 3 tasks (21 runs) | `python scripts/run.py all`                              |
| One mode against all tasks      | `python scripts/run.py mode --mode <m>`                  |
| All modes against one task      | `python scripts/run.py task --task <t>`                  |
| One mode × one task             | `python scripts/run.py single --mode <m> --task <t>`     |
| Wipe workspace                  | `python scripts/run.py clean` (`--mode <m>` / `--task <t>` to scope) |
| Regenerate + open report        | `python scripts/run.py report`                           |

`_common.py` holds the canonical MODES + TASKS lists used by every Python
side of the harness (`run_task.py`, `analyze.py`, `audit_behavior.py`).
Adding a new mode means editing that one file.

## Flags

| Flag                  | Meaning                                                                |
|-----------------------|------------------------------------------------------------------------|
| `--reps N`            | Number of replicate runs to add per cell (default 1). Each lands in its own `rep_*` slot. |
| `--clean`             | Wipe each cell (default slot + all `rep_*` dirs) before running. Without it, runs **append** to existing data. |
| `--extra <a> <b> ...` | Forward extra args verbatim to `run_task.py`.                          |

Slot assignment:
- **Append (default, no `--clean`):** highest existing `rep_N` is detected; new runs go to `rep_(N+1)`, `rep_(N+2)`, …
- **Clean (`--clean`):** cell is wiped, runs go to `rep_1`, `rep_2`, …

Do NOT pass `--rep` via `--extra` — the wrapper manages slot indices. Use
`--extra` for: `--budget`, `--effort`, `--model`, `--no-verify`.

Common `--extra` knobs:

- `--budget 5` — raise the budget cap for a heavier batch.
- `--effort medium` — drop effort. Note: this biases bare modes more than
  deliberation modes (bare modes' quality drops faster as effort falls).
- `--model claude-haiku-4-5-20251001` — smoke test on Haiku.

## Examples

```powershell
# Full matrix, 1 rep per cell, append to whatever already exists.
python scripts/run.py all
python scripts/run.py report

# Full matrix, 3 fresh reps per cell (wipe first).
python scripts/run.py all --reps 3 --clean

# Add 3 more replicates on top of existing data for one task.
python scripts/run.py task --task reasoning/02_rule_of_three --reps 3

# Fresh 3-rep batch for transport_choice across all modes (e.g. after editing the prompt).
python scripts/run.py task --task reasoning/01_transport_choice --reps 3 --clean

# Re-run circuit breaker with extra budget on superpowers only, single run appended.
python scripts/run.py single --mode superpowers --task code/01_circuit_breaker --extra --budget 5

# Wipe one task across all modes (e.g. prompt changed).
python scripts/run.py clean --task reasoning/02_rule_of_three

# Wipe one mode across all tasks (e.g. template changed).
python scripts/run.py clean --mode consilium_dialectic

# Wipe one specific cell.
python scripts/run.py clean --mode opus_bare --task code/01_circuit_breaker

# Wipe the entire workspace.
python scripts/run.py clean
```

## Isolation guarantees

Three layers of isolation per run:

1. **Workspace scoping** — each run writes to
   `workspace/<mode>/<task>/[rep_N/]`. `--clean` deletes the entire cell
   (incl. all `rep_*` dirs) before starting; append mode never touches
   existing slots.
2. **Subprocess sandbox** — each run is its own `claude -p` subprocess with
   `cwd=workspace/<mode>/<task>/[rep_N/]`, so the model cannot read other
   modes' workspaces or the hidden `Benchmark-scoring/` tree.
3. **Prompt-cache buster** — `run_task.py` prepends a per-task,
   per-invocation timestamp token to every auto run, forcing Anthropic's
   prompt-cache prefix to miss between runs. Note: the Claude Code system
   prompt (~30K tokens) is cached structurally and is the same for every
   mode — a constant cost floor, not a bias source. The HTML report's
   `CR · CW` line surfaces cache_read / cache_write per cell so you can
   confirm cross-cell stability.
