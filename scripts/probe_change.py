"""Probe a code change for objective diff_size + churn signals.

Anchors Conservator's diff_size factor in git's actual numbers instead of
intuition. Returns JSON with files_changed, lines_added, lines_removed.

With --churn N, also reports per-file commit count over the last N days
(``git log --since=Ndays``) — input for Conservator's regression_risk
factor. A file churned 8 times in the last 14 days is fragile; one
untouched in 2 years is stable.

Deliberately ships WITHOUT modules_touched / shared_paths_hit — those are
undecidable without per-project config and would force the script to either
crash or guess. Conservator continues to judge scope_drift and regression
itself; only diff_size + recent churn get ground-truth anchors.

Modes (mutually exclusive):
  default       working tree vs HEAD  (staged + unstaged combined)
  --ref REF     diff REF..HEAD  (e.g., --ref HEAD~3, --ref main)
  --range A..B  diff A..B
  --files ...   diff against HEAD restricted to given paths

Additional flag:
  --churn N     also count commits per changed file in the last N days

On error (git missing, not a repo, bad ref), prints JSON {"error": "..."}
to stdout and exits 1. Never raises a traceback at the caller.

CLI:
    python scripts/probe_change.py
    python scripts/probe_change.py --ref main
    python scripts/probe_change.py --range origin/main..HEAD
    python scripts/probe_change.py --files src/foo.py src/bar.py
    python scripts/probe_change.py --ref main --churn 30
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys


def _run_numstat(args: list[str]) -> str:
    try:
        result = subprocess.run(
            ["git", "diff", "--numstat", "--no-renames", *args],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        raise RuntimeError("git executable not found on PATH")
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        raise RuntimeError(f"git diff failed: {stderr or 'no stderr'}")
    return result.stdout


def parse_numstat(text: str) -> tuple[dict, list[str]]:
    files = 0
    added = 0
    removed = 0
    paths: list[str] = []
    for line in text.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        a, r, path = parts
        files += 1
        paths.append(path)
        # Binary files show "-\t-\t<path>"; treat as 0 lines but counted file.
        if a != "-":
            try:
                added += int(a)
            except ValueError:
                pass
        if r != "-":
            try:
                removed += int(r)
            except ValueError:
                pass
    summary = {"files_changed": files, "lines_added": added, "lines_removed": removed}
    return summary, paths


def _commit_count(path: str, days: int) -> int:
    try:
        result = subprocess.run(
            ["git", "log", f"--since={days}.days", "--pretty=format:%H", "--", path],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError:
        return 0
    return sum(1 for line in result.stdout.splitlines() if line.strip())


def probe_churn(paths: list[str], days: int) -> dict:
    return {p: _commit_count(p, days) for p in paths}


def probe(
    ref: str | None,
    range_: str | None,
    files: list[str] | None,
    churn_days: int | None = None,
) -> dict:
    git_args: list[str]
    if range_:
        git_args = [range_]
    elif ref:
        git_args = [f"{ref}..HEAD"]
    else:
        git_args = ["HEAD"]
    if files:
        git_args += ["--", *files]
    text = _run_numstat(git_args)
    summary, paths = parse_numstat(text)
    if churn_days is not None and paths:
        summary["churn"] = {
            "window_days": churn_days,
            "commits_per_file": probe_churn(paths, churn_days),
        }
    return summary


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--ref", help="diff <ref>..HEAD")
    mode.add_argument("--range", dest="range_", help="diff <A>..<B>")
    ap.add_argument("--files", nargs="+", help="restrict to specific paths")
    ap.add_argument(
        "--churn",
        type=int,
        metavar="N",
        help="also count commits per changed file in the last N days",
    )
    args = ap.parse_args(argv)

    if args.churn is not None and args.churn <= 0:
        json.dump({"error": "--churn must be a positive integer"}, sys.stdout)
        sys.stdout.write("\n")
        return 1

    try:
        result = probe(args.ref, args.range_, args.files, args.churn)
    except RuntimeError as exc:
        json.dump({"error": str(exc)}, sys.stdout)
        sys.stdout.write("\n")
        return 1

    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
