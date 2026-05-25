"""Python wrapper for the benchmark runner. Canonical entry point.

Run from anywhere — every subcommand resolves paths against the repo root.

Examples:
    python scripts/run.py all
    python scripts/run.py mode --mode opus_bare
    python scripts/run.py task --task reasoning/02_rule_of_three --reps 3
    python scripts/run.py single --mode superpowers --task code/01_circuit_breaker
    python scripts/run.py clean --task reasoning/02_rule_of_three
    python scripts/run.py report

Subcommands run in APPEND mode by default: each cell auto-detects the
highest existing rep_N slot and writes the next N runs starting from
rep_(max+1). Pass `--clean` to wipe each cell (default + all rep_* slots)
before running, starting fresh from rep_1.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import webbrowser
from pathlib import Path

# Allow `python scripts/run.py` regardless of CWD.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import BENCHMARK_ROOT, MODES, TASKS, invoke_run  # noqa: E402


def _add_run_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--clean", action="store_true",
        help="Wipe workspace/<mode>/<task>/ (default slot + all rep_* dirs) "
             "for each cell before running, then start from rep_1. "
             "Default: append — write to rep_(max+1) without touching existing data.",
    )
    parser.add_argument(
        "--reps", type=int, default=1, metavar="N",
        help="Number of replicate runs to add per cell (default: 1). "
             "Each goes to a separate rep_N slot.",
    )
    parser.add_argument(
        "--extra", nargs=argparse.REMAINDER, default=[],
        help="Pass remaining args verbatim to run_task.py "
             "(e.g. --extra --budget 5 --effort medium). "
             "Do NOT include --rep here — slot is managed by --reps.",
    )


def _next_rep_start(mode: str, task: str) -> int:
    """Return the next free rep index for a cell (highest existing + 1)."""
    cell = BENCHMARK_ROOT / "workspace" / mode / task
    if not cell.exists():
        return 1
    max_existing = 0
    for sub in cell.iterdir():
        if sub.is_dir() and sub.name.startswith("rep_"):
            try:
                n = int(sub.name[4:])
                if n > max_existing:
                    max_existing = n
            except ValueError:
                pass
    return max_existing + 1


def _run_cell(mode: str, task: str, args: argparse.Namespace) -> int:
    """Run --reps replicates for one cell. Honors --clean (wipe + start at rep_1)
    or append (start at next free rep_*).
    """
    cell = BENCHMARK_ROOT / "workspace" / mode / task
    if args.clean and cell.exists():
        print(f"  Wiping {cell}", flush=True)
        shutil.rmtree(cell)
    start = 1 if args.clean else _next_rep_start(mode, task)
    rc = 0
    for offset in range(args.reps):
        rep_idx = start + offset
        extra = list(args.extra) + ["--rep", str(rep_idx)]
        # Cell-level wipe already happened above (if --clean); run_task.py
        # runs without --clean so it doesn't re-wipe its own rep_N subdir
        # mid-flight.
        rc |= invoke_run(mode, task, no_clean=True, extra_args=extra)
    return rc


def cmd_all(args: argparse.Namespace) -> int:
    total = len(MODES) * len(TASKS)
    i = 0
    rc = 0
    for mode in MODES:
        for task in TASKS:
            i += 1
            print(f"\n=== [{i}/{total}] {mode} :: {task} ===")
            rc |= _run_cell(mode, task, args)
    print("\nAll runs complete. View with: python scripts/run.py report")
    return rc


def cmd_mode(args: argparse.Namespace) -> int:
    rc = 0
    for i, task in enumerate(TASKS, 1):
        print(f"\n=== [{i}/{len(TASKS)}] {args.mode} :: {task} ===")
        rc |= _run_cell(args.mode, task, args)
    return rc


def cmd_task(args: argparse.Namespace) -> int:
    rc = 0
    for i, mode in enumerate(MODES, 1):
        print(f"\n=== [{i}/{len(MODES)}] {mode} :: {args.task} ===")
        rc |= _run_cell(mode, args.task, args)
    return rc


def cmd_single(args: argparse.Namespace) -> int:
    return _run_cell(args.mode, args.task, args)


def cmd_clean(args: argparse.Namespace) -> int:
    if args.task and not args.mode:
        # Wipe one task across all modes.
        wiped = 0
        for mode in MODES:
            t = BENCHMARK_ROOT / "workspace" / mode / args.task
            if t.exists():
                print(f"Wiping {t}")
                shutil.rmtree(t)
                wiped += 1
        if not wiped:
            print(f"Nothing to wipe for task {args.task}")
        else:
            print(f"Done. Wiped {wiped} cell(s) for task {args.task}.")
        return 0

    target = BENCHMARK_ROOT / "workspace"
    if args.mode:
        target = target / args.mode
    if args.task:
        target = target / args.task
    if target.exists():
        print(f"Wiping {target}")
        shutil.rmtree(target)
        print("Done.")
    else:
        print(f"Nothing to wipe (already absent): {target}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    rc = subprocess.run(
        [sys.executable, "analyze.py"], cwd=BENCHMARK_ROOT,
    ).returncode
    report = BENCHMARK_ROOT / "report.html"
    if rc == 0 and report.exists() and not args.no_open:
        webbrowser.open(report.as_uri())
    elif not report.exists():
        print(f"report.html not produced at {report}", file=sys.stderr)
    return rc


EXAMPLES = """\
examples:
  python scripts/run.py all                                          # append 1 rep per cell across the full matrix
  python scripts/run.py all --reps 3                                 # append 3 reps per cell
  python scripts/run.py all --reps 3 --clean                         # wipe everything then run a fresh 3-rep batch
  python scripts/run.py task --task reasoning/01_transport_choice --reps 3 --clean
  python scripts/run.py mode --mode opus_bare --reps 3
  python scripts/run.py single --mode superpowers --task code/01_circuit_breaker --reps 5
  python scripts/run.py clean --task reasoning/02_rule_of_three      # wipe one task across all modes
  python scripts/run.py clean --mode consilium_dialectic             # wipe one mode across all tasks
  python scripts/run.py clean --mode opus_bare --task code/01_circuit_breaker
  python scripts/run.py report
"""


def main() -> int:
    p = argparse.ArgumentParser(
        prog="run.py",
        description="Benchmark runner wrapper.",
        epilog=EXAMPLES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    p_all = sub.add_parser("all", help="All modes x all tasks")
    _add_run_args(p_all)
    p_all.set_defaults(func=cmd_all)

    p_mode = sub.add_parser("mode", help="One mode x all tasks")
    p_mode.add_argument("--mode", required=True, choices=MODES)
    _add_run_args(p_mode)
    p_mode.set_defaults(func=cmd_mode)

    p_task = sub.add_parser("task", help="All modes x one task")
    p_task.add_argument("--task", required=True, choices=TASKS)
    _add_run_args(p_task)
    p_task.set_defaults(func=cmd_task)

    p_single = sub.add_parser("single", help="One mode x one task")
    p_single.add_argument("--mode", required=True, choices=MODES)
    p_single.add_argument("--task", required=True, choices=TASKS)
    _add_run_args(p_single)
    p_single.set_defaults(func=cmd_single)

    p_clean = sub.add_parser(
        "clean",
        help="Wipe workspace/ (or restrict to --mode, --task, or both)",
    )
    p_clean.add_argument("--mode", choices=MODES,
                         help="Restrict the wipe to one mode")
    p_clean.add_argument("--task", choices=TASKS,
                         help="Restrict the wipe to one task "
                              "(across all modes if --mode is not given)")
    p_clean.set_defaults(func=cmd_clean)

    p_report = sub.add_parser("report", help="Regenerate report.html and open it")
    p_report.add_argument("--no-open", action="store_true",
                          help="Generate report.html without opening a browser")
    p_report.set_defaults(func=cmd_report)

    args = p.parse_args()
    return args.func(args) or 0


if __name__ == "__main__":
    sys.exit(main())
