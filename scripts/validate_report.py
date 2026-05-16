"""Validate that a deliberation report satisfies Constitution Principle #4.

Reads a deliberation report (JSON) from stdin. Exits 0 iff:
- success_criterion is a non-empty string (str.strip() length > 0)
- verification is a non-empty string
- chosen_approach is EITHER a non-empty string OR null
- if skipped is true, skip_reason is a non-empty string
- if telemetry is present, its shape is well-formed (see _validate_telemetry)
- for non-skipped reports, deliberation_log is an array containing an aggregate
  step whose result is a dict (not a string narrative)
- for non-skipped reports, telemetry is a dict with a non-empty string mode field

The null chosen_approach case is legitimate: conservative_override with
veto_threshold can produce chosen: null when every candidate is vetoed
(see aggregator.py).

The skipped case (chosen_approach: "skipped", skipped: true) is legitimate
and emitted by the scope gate (see scripts/scope_gate.py). Principle #4
still applies — success_criterion + verification remain required even for
skipped reports — and skip_reason must justify the bypass.

The telemetry block is required for non-skipped reports (mode field
must be a non-empty string). For skipped reports it should be omitted.
When present it should carry per-voice token + latency counts so
scripts/usage.py can roll up cost statistics across runs/. Validator
checks shape (non-negative ints for counts, positive int for passes,
str for mode); fields beyond mode may be omitted individually because
the agent can't always measure them all (e.g. sequential mode can't
isolate per-voice tokens).

The deliberation_log + telemetry.mode requirements catch a class of bugs
where reports were manually assembled (bypassing build_report.py) and ended
up with shape drift — e.g., aggregate.result as a narrative string instead
of the canonical dict. Manual assembly is no longer accepted by this gate;
use build_report.py to produce the canonical shape.

On failure, prints each problem to stderr and exits 1. Malformed JSON exits 2.

CLI:
    cat runs/2026-05-11_1500_foo.json | python scripts/validate_report.py
    python scripts/validate_report.py < report.json
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys

from personalities import NAMES
from utils import force_utf8_streams


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
            if not problems:
                _warn_latency_spikes(voices)
    if "passes" in telemetry:
        p = telemetry["passes"]
        if not (isinstance(p, int) and not isinstance(p, bool) and p > 0):
            problems.append("telemetry.passes must be a positive int")
    if "mode" in telemetry and not isinstance(telemetry["mode"], str):
        problems.append("telemetry.mode must be a string")
    return problems


def _validate_deliberation_log(log: object, skipped: bool) -> list[str]:
    if skipped:
        return []
    if not isinstance(log, list):
        return ["deliberation_log must be an array"]
    aggregate_step = next(
        (s for s in log if isinstance(s, dict) and s.get("step") == "aggregate"),
        None,
    )
    if aggregate_step is None:
        return ["deliberation_log missing 'aggregate' step"]
    result = aggregate_step.get("result")
    if not isinstance(result, dict):
        return [
            f"deliberation_log[aggregate].result must be an object "
            f"(got {type(result).__name__}) — did you bypass build_report.py?"
        ]
    return []


def _warn_latency_spikes(voices: dict) -> None:
    latencies = {
        v: d["latency_ms"]
        for v, d in voices.items()
        if isinstance(d, dict) and isinstance(d.get("latency_ms"), int) and not isinstance(d.get("latency_ms"), bool)
    }
    if len(latencies) < 2:
        return
    vnames = list(latencies.keys())
    for i, vname in enumerate(vnames):
        peers = [latencies[n] for j, n in enumerate(vnames) if j != i]
        peer_median = statistics.median(peers)
        if peer_median > 0 and latencies[vname] > 2 * peer_median:
            print(
                f"[warning] latency_spike: {vname} {latencies[vname]}ms > 2× "
                f"peer median {peer_median:.0f}ms",
                file=sys.stderr,
            )


def _validate_telemetry_required(report: dict) -> list[str]:
    if report.get("skipped") is True:
        return []
    telemetry = report.get("telemetry")
    if not isinstance(telemetry, dict):
        return ["telemetry block required for non-skipped reports"]
    mode = telemetry.get("mode")
    if not isinstance(mode, str) or not mode.strip():
        return ["telemetry.mode required (non-empty string) for non-skipped reports"]
    if mode.strip() == "parallel":
        voices = telemetry.get("voices")
        if not isinstance(voices, dict) or len(voices) == 0:
            return [
                "telemetry.voices required (non-empty dict) for parallel mode; "
                "capture per-voice tokens/latency at dispatch for usage rollup "
                "(scripts/usage.py would skip this run)"
            ]
    return []


VOTE_PATTERN_REGEX = re.compile(r"^[0-3]-[0-3](-[0-1])?$")

_TRIAS_NULL_PATTERNS = {"1-1-1", "1-1-0", "1-0-0", "0-0-0"}
_TRIAS_EXPECTED_NAMES = frozenset(NAMES)


def _validate_trias(report: dict, errors: list) -> None:
    """Trias-specific validation. Only runs when report has team == 'trias'."""
    personalities = report.get("personalities")
    if not isinstance(personalities, list) or len(personalities) != 3:
        errors.append("trias: personalities must be a list of exactly 3 entries")
        return
    names_seen: set[str] = set()
    for i, p in enumerate(personalities):
        for f in ("name", "weights", "lens", "chose"):
            if f not in p:
                errors.append(f"trias: personalities[{i}] missing field {f!r}")
        if "name" in p:
            if p["name"] in names_seen:
                errors.append(f"trias: duplicate personality name {p['name']!r}")
            names_seen.add(p["name"])
    if names_seen and names_seen != _TRIAS_EXPECTED_NAMES:
        errors.append(
            f"trias: personality names must be exactly {sorted(_TRIAS_EXPECTED_NAMES)},"
            f" got {sorted(names_seen)}"
        )

    pattern = report.get("vote_pattern")
    if not pattern or not VOTE_PATTERN_REGEX.match(pattern):
        errors.append(f"trias: vote_pattern missing or malformed (got {pattern!r})")

    chosen = report.get("chosen_approach")
    conf = report.get("confidence")
    if pattern in _TRIAS_NULL_PATTERNS:
        if chosen is not None:
            errors.append(
                f"trias: vote_pattern {pattern!r} requires chosen_approach=null,"
                f" got {chosen!r}"
            )
        if conf is not None:
            errors.append(
                f"trias: vote_pattern {pattern!r} requires confidence=null,"
                f" got {conf!r}"
            )


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

    is_trias = report.get("team") == "trias"
    problems.extend(_validate_deliberation_log(
        report.get("deliberation_log"),
        report.get("skipped") is True or is_trias,
    ))
    # Telemetry required for all non-skipped reports, Trias included — it's
    # the most expensive mode (9 sub-agenți) so cost rollup matters most there.
    problems.extend(_validate_telemetry_required(report))

    if is_trias:
        _validate_trias(report, problems)

    return problems


def main(argv: list[str] | None = None) -> int:
    force_utf8_streams()
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
