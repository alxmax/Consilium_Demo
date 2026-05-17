"""Shared utilities for Consilium scripts.

All functions are stdlib-only. Scripts import from this module instead of
defining their own copies. Each script remains a stand-alone executable.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any


def force_utf8_streams() -> None:
    """Reconfigure stdin/stdout/stderr to UTF-8.

    Windows default encoding is cp1252; piping UTF-8 JSON through it
    mangles non-ASCII characters (ț, ș, ă) before any script sees them.
    """
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(encoding="utf-8")


def load_json_stdin(script_name: str) -> Any:
    """Read and parse JSON from stdin.

    On empty stdin or parse error, prints a clear usage hint and exits 2.
    Callers treat the return value as already-validated JSON (dict or list).

    Usage hint format:
        "<script_name>: no input — pipe a report file, e.g.:
         cat runs/<file>.json | python scripts/<script_name>"
    """
    raw = sys.stdin.read()
    if not raw.strip():
        print(
            f"{script_name}: no input — pipe a report file, e.g.:\n"
            f"  cat runs/<file>.json | python scripts/{script_name}",
            file=sys.stderr,
        )
        sys.exit(2)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"{script_name}: invalid JSON — {exc}", file=sys.stderr)
        sys.exit(2)


def atomic_write_text(path, content: str, encoding: str = "utf-8") -> None:
    """Write *content* to *path* atomically.

    Writes to a sibling temp file then ``os.replace``s it onto *path*.
    A crash anywhere in the write leaves the original intact rather than
    truncated — important for long-term journals (FEEDBACK.html) where a
    half-written render would erase historical data.

    ``os.replace`` is atomic on both POSIX and Windows when source and
    destination live on the same filesystem (always true here — same dir).
    """
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding=encoding)
    os.replace(tmp, path)


_ISSUE_PENALTIES = {"low": 0.05, "medium": 0.15, "high": 0.30}


def issue_penalty(issue: object) -> float:
    """Return the score penalty for a single Control issue based on severity.

    Severity levels: low=0.05, medium=0.15 (default), high=0.30.
    If the issue dict has no severity field, 0.15 is used (backward-compatible).
    """
    if isinstance(issue, dict):
        return _ISSUE_PENALTIES.get(issue.get("severity", "medium"), 0.15)
    return 0.15


def validate_keys(data: dict, required: list[str], context: str) -> None:
    """Assert that *data* contains all keys in *required*.

    On missing key, prints which key is missing with the *context* label
    and exits 1. Intended for use in per-script validate_input() guards.

    Example:
        validate_keys(bundle, ["success_criterion", "generator"], "bundle")
    """
    for key in required:
        if key not in data:
            print(
                f"{context}: missing required field '{key}'",
                file=sys.stderr,
            )
            sys.exit(1)
