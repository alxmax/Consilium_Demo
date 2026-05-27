"""Canonical mode/task lists + Python-wrapper helpers for the benchmark.

SOURCE OF TRUTH for MODES + TASKS. `run_task.py`, `analyze.py`, and
`scripts/audit_behavior.py` import from here. Adding a new mode/task
means editing this file.

`invoke_run()` is the worker used by `scripts/run.py` to dispatch a
single (mode, task) to `run_task.py`.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BENCHMARK_ROOT = Path(__file__).resolve().parent.parent

MODES = [
    "consilium_sequential",
    "consilium_trias",
    "consilium_dialectic",
    "superpowers",
    "sonnet_bare",
]

TASKS = [
    "code/01_circuit_breaker",
    "reasoning/01_transport_choice",
    "reasoning/02_rule_of_three",
    "reasoning/03_schema_migration",
    "reasoning/04_binary_search_bug",
    "reasoning/05_warehouse_contradiction",
]


def invoke_run(mode: str, task: str, no_clean: bool = False,
               extra_args: list[str] | None = None) -> int:
    """Spawn `run_task.py` for one (mode, task). Returns the exit code.

    Always runs with cwd=BENCHMARK_ROOT so relative paths inside
    run_task.py resolve regardless of where the caller invokes from.
    """
    args = [sys.executable, "run_task.py", "--mode", mode, "--task", task]
    if not no_clean:
        args.append("--clean")
    if extra_args:
        args.extend(extra_args)
    print(f">>> {' '.join(args[1:])}", flush=True)
    return subprocess.run(args, cwd=BENCHMARK_ROOT).returncode
