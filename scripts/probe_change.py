"""Probe a code change for objective diff_size signals.

Anchors Conservator's diff_size factor in git's actual numbers instead of
intuition. Returns JSON with files_changed, lines_added, lines_removed.

Deliberately ships WITHOUT modules_touched / shared_paths_hit — those are
undecidable without per-project config and would force the script to either
crash or guess. Conservator continues to judge scope_drift and regression
itself; only diff_size gets a ground-truth anchor.

Modes (mutually exclusive):
  default       working tree vs HEAD  (staged + unstaged combined)
  --ref REF     diff REF..HEAD  (e.g., --ref HEAD~3, --ref main)
  --range A..B  diff A..B
  --files ...   diff against HEAD restricted to given paths

On error (git missing, not a repo, bad ref), prints JSON {"error": "..."}
to stdout and exits 1. Never raises a traceback at the caller.

CLI:
    python scripts/probe_change.py
    python scripts/probe_change.py --ref main
    python scripts/probe_change.py --range origin/main..HEAD
    python scripts/probe_change.py --files src/foo.py src/bar.py
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys


def _run_numstat(args: list[str]) -> str:
    try:
        result = subprocess.run(
            ["git", "diff", "--numstat", *args],
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


def parse_numstat(text: str) -> dict:
    files = 0
    added = 0
    removed = 0
    for line in text.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        a, r, _ = parts
        files += 1
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
    return {"files_changed": files, "lines_added": added, "lines_removed": removed}


def probe(ref: str | None, range_: str | None, files: list[str] | None) -> dict:
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
    return parse_numstat(text)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--ref", help="diff <ref>..HEAD")
    mode.add_argument("--range", dest="range_", help="diff <A>..<B>")
    ap.add_argument("--files", nargs="+", help="restrict to specific paths")
    args = ap.parse_args(argv)

    try:
        result = probe(args.ref, args.range_, args.files)
    except RuntimeError as exc:
        json.dump({"error": str(exc)}, sys.stdout)
        sys.stdout.write("\n")
        return 1

    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
