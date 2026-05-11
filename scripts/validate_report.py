"""Validate that a deliberation report satisfies Constitution Principle #4.

Reads a deliberation report (JSON) from stdin. Exits 0 iff:
- success_criterion is a non-empty string (str.strip() length > 0)
- verification is a non-empty string
- chosen_approach is EITHER a non-empty string OR null
- if skipped is true, skip_reason is a non-empty string
- if telemetry is present, its shape is well-formed (see _validate_telemetry)

The null chosen_approach case is legitimate: conservative_override with
veto_threshold can produce chosen: null when every candidate is vetoed
(see aggregator.py).

The skipped case (chosen_approach: "skipped", skipped: true) is legitimate
and emitted by the scope gate (see scripts/scope_gate.py). Principle #4
still applies — success_criterion + verification remain required even for
skipped reports — and skip_reason must justify the bypass.

The telemetry block is optional. When present it should carry per-voice
token + latency counts so scripts/usage.py can roll up cost statistics
across runs/. Validator only checks shape (non-negative ints for counts,
positive int for passes, str for mode); fields may be omitted individually
because the agent can't always measure them all (e.g. sequential mode
can't isolate per-voice tokens).

On failure, prints each problem to stderr and exits 1. Malformed JSON exits 2.

CLI:
    cat runs/2026-05-11_1500_foo.json | python scripts/validate_report.py
    python scripts/validate_report.py < report.json
"""

from __future__ import annotations

import argparse
import json
import sys


REQUIRED_NON_EMPTY = ("success_criterion", "verification")
NULLABLE_NON_EMPTY = ("chosen_approach",)
TELEMETRY_INT_FIELDS = ("tokens_in", "tokens_out", "latency_ms")


def _is_non_empty_str(value: object) -> bool:
    return isinstance(value, str) and len(value.strip()) > 0


def _is_non_negative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _validate_telemetry(telemetry: object) -> list[str]:
    if not isinstance(telemetry, dict):
        return ["telemetry must be a JSON object"]
    problems: list[str] = []
    voices = telemetry.get("voices")
    if voices is not None:
        if not isinstance(voices, dict):
            problems.append("telemetry.voices must be a JSON object")
        else:
            for vname, vdata in voices.items():
                if not isinstance(vdata, dict):
                    problems.append(f"telemetry.voices.{vname} must be a JSON object")
                    continue
                for f in TELEMETRY_INT_FIELDS:
                    if f in vdata and not _is_non_negative_int(vdata[f]):
                        problems.append(
                            f"telemetry.voices.{vname}.{f} must be a non-negative int"
                        )
    if "passes" in telemetry:
        p = telemetry["passes"]
        if not (isinstance(p, int) and not isinstance(p, bool) and p > 0):
            problems.append("telemetry.passes must be a positive int")
    if "mode" in telemetry and not isinstance(telemetry["mode"], str):
        problems.append("telemetry.mode must be a string")
    return problems


def validate(report: dict) -> list[str]:
    problems: list[str] = []
    for field in REQUIRED_NON_EMPTY:
        if field not in report:
            problems.append(f"missing required field: {field}")
        elif not _is_non_empty_str(report[field]):
            problems.append(f"field {field} must be a non-empty string (got {type(report[field]).__name__})")

    for field in NULLABLE_NON_EMPTY:
        if field not in report:
            problems.append(f"missing required field: {field}")
            continue
        value = report[field]
        if value is None:
            continue
        if not _is_non_empty_str(value):
            problems.append(f"field {field} must be null or a non-empty string (got {type(value).__name__})")

    if report.get("skipped") is True:
        if not _is_non_empty_str(report.get("skip_reason")):
            problems.append("skipped=true requires non-empty skip_reason")

    if "telemetry" in report:
        problems.extend(_validate_telemetry(report["telemetry"]))

    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--input",
        type=argparse.FileType("r", encoding="utf-8"),
        default=sys.stdin,
        help="JSON input file (default: stdin)",
    )
    args = ap.parse_args(argv)

    try:
        report = json.load(args.input)
    except json.JSONDecodeError as exc:
        print(f"invalid JSON: {exc}", file=sys.stderr)
        return 2

    if not isinstance(report, dict):
        print("report must be a JSON object", file=sys.stderr)
        return 2

    problems = validate(report)
    if problems:
        for p in problems:
            print(p, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
