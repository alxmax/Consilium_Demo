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

SCOPE: this validator checks report *shape*, not deliberation *substance* —
it confirms the fields exist and are well-formed, not that the voices did
rigorous, non-vacuous work. Substance-level checking has no enforced gate
(meta_critic.py is advisory and, as of 2026-05-24, trimmed to a single
conservator_spread heuristic). This is a known, accepted gap — see TODO.md.

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


# === RUND2 ===
_REVERSIBILITY_VALUES = frozenset({"complete", "partial", "irreversible"})
_MAGNITUDE_VALUES = frozenset({"trivial", "moderate", "high", "critical"})


def _validate_regression_risk(value: object) -> list[str]:
    """Accept scalar float (old format) OR object with reversibility/magnitude/net_concern (RUND2)."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if not (0.0 <= float(value) <= 1.0):
            return [f"regression_risk scalar must be in [0.0, 1.0], got {value}"]
        return []
    if isinstance(value, dict):
        problems = []
        rev = value.get("reversibility")
        if rev not in _REVERSIBILITY_VALUES:
            problems.append(f"regression_risk.reversibility must be one of {sorted(_REVERSIBILITY_VALUES)}, got {rev!r}")
        mag = value.get("magnitude")
        if mag not in _MAGNITUDE_VALUES:
            problems.append(f"regression_risk.magnitude must be one of {sorted(_MAGNITUDE_VALUES)}, got {mag!r}")
        nc = value.get("net_concern")
        if nc is not None and not (isinstance(nc, (int, float)) and not isinstance(nc, bool) and 0.0 <= float(nc) <= 1.0):
            problems.append(f"regression_risk.net_concern must be float in [0.0, 1.0], got {nc!r}")
        return problems
    return [f"regression_risk must be a float or an object, got {type(value).__name__}"]


def _validate_rund2_fields(report: dict) -> list[str]:
    """Strict RUND2 field validation — only run with --strict-rund2 flag."""
    problems = []
    for score in report.get("voice_scores", {}).get("conservator", {}).get("scores", []):
        rr = score.get("regression_risk")
        if rr is None:
            problems.append(f"strict-rund2: candidate '{score.get('id')}' conservator missing regression_risk object")
            continue
        problems.extend(_validate_regression_risk(rr))
        if "tokens_budget" not in score:
            problems.append(f"strict-rund2: candidate '{score.get('id')}' conservator missing tokens_budget")
    return problems
# === END RUND2 ===


# === PHILOSOPHICAL VOICES ===
_PHILOSOPHICAL_VOICES = frozenset({
    "aurelius-control", "confucius"
})


def _validate_philosophical_aurelius_control(voice_output: dict) -> list[str]:
    problems = []
    for field in ("in_control", "out_of_control"):
        val = voice_output.get(field)
        if not isinstance(val, list):
            problems.append(f"strict-philosophical=aurelius-control: '{field}' must be a list")
    wasted = voice_output.get("wasted_deliberation")
    if wasted is not None and not isinstance(wasted, str):
        problems.append("strict-philosophical=aurelius-control: wasted_deliberation must be string or null")
    return problems


def _validate_philosophical_confucius(voice_output: dict) -> list[str]:
    # confucius-strict validation removed when precedent_search deprecated 2026-05-17
    del voice_output
    return []


_PHILOSOPHICAL_VALIDATORS = {
    "aurelius-control": _validate_philosophical_aurelius_control,
    "confucius": _validate_philosophical_confucius,
}
# === END PHILOSOPHICAL VOICES ===


# === SENATE STRICT VALIDATION (--strict-senate) ===
_SENATE_VALID_VERDICTS = frozenset({
    "GO", "MODIFY", "STOP", "DEEPLY_SPLIT", "UNREACHABLE", "OUT_OF_SCOPE",
})
_ADDRESSES_PRIOR_CONCERNS_VALUES = frozenset({"true", "false", "n_a"})


def _validate_senate_bundle(report: dict) -> list[str]:
    """Validate senate-specific fields (Laws 6-8). Used with --strict-senate flag.

    Expects senate bundle format (from senate_synth.py), not the standard
    deliberation report format validated by validate().
    """
    problems: list[str] = []
    verdict = report.get("verdict")
    if verdict not in _SENATE_VALID_VERDICTS:
        problems.append(f"senate: verdict must be one of {sorted(_SENATE_VALID_VERDICTS)}, got {verdict!r}")

    # Law 7: OUT_OF_SCOPE requires scope_veto_consensus
    if verdict == "OUT_OF_SCOPE":
        svc = report.get("scope_veto_consensus")
        if not isinstance(svc, dict):
            problems.append("senate law_7: OUT_OF_SCOPE verdict requires scope_veto_consensus dict")
        elif not isinstance(svc.get("senators"), list) or len(svc["senators"]) < 3:
            problems.append("senate law_7: scope_veto_consensus.senators must have >= 3 entries")

    # Law 6: each present senator must have addresses_prior_concerns if prior_run_context was injected
    # Soft check: if any senator output has addresses_prior_concerns, validate its value
    outputs = report.get("outputs", {})
    for name, output in outputs.items():
        if not isinstance(output, dict):
            continue
        apc = output.get("addresses_prior_concerns")
        if apc is not None:
            apc_str = str(apc).lower().strip()
            if apc_str not in _ADDRESSES_PRIOR_CONCERNS_VALUES:
                problems.append(
                    f"senate law_6: senator '{name}' addresses_prior_concerns must be "
                    f"true|false|n_a, got {apc!r}"
                )

    # Law 8: auto-promoted senators should have auto_promoted_from in their output
    auto_promoted = report.get("auto_promoted_senators", [])
    if isinstance(auto_promoted, list):
        for name in auto_promoted:
            output = outputs.get(name, {})
            if isinstance(output, dict) and "auto_promoted_from" not in output:
                problems.append(
                    f"senate law_8: senator '{name}' listed in auto_promoted_senators "
                    "but output missing auto_promoted_from field"
                )

    return problems
# === END SENATE STRICT VALIDATION ===


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
    # Alias resolution — collapsed 2026-05-17.  The live dispatcher no longer
    # emits these names; historical runs/*.json may still carry them.
    _LEGACY_MODE_ALIASES: dict[str, str] = {
        "parallel_skeptic": "skeptic_on_chosen",
        "dialectic_skeptic": "skeptic_on_chosen",
        "trias_split": "trias",  # deprecated 2026-05-21: trias 9→3 makes split redundant
    }
    mode = _LEGACY_MODE_ALIASES.get(mode.strip(), mode.strip())
    # All modes that dispatch multiple voices require per-voice telemetry so
    # usage.py can roll up cost across runs/. parallel_skeptic/dialectic_skeptic
    # are resolved via _LEGACY_MODE_ALIASES above before this check.
    _MULTI_VOICE_MODES = frozenset({
        "parallel", "trias", "dialectic", "trias_split",
        "skeptic_on_chosen", "parallel_skeptic", "dialectic_skeptic",
    })
    if mode in _MULTI_VOICE_MODES:
        voices = telemetry.get("voices")
        if not isinstance(voices, dict) or len(voices) == 0:
            return [
                f"telemetry.voices required (non-empty dict) for {mode!r} mode; "
                "capture per-voice tokens/latency at dispatch for usage rollup "
                "(scripts/usage.py would skip this run)"
            ]
    return []


# === SENATE LAWS ===
_FALSIFIABILITY_PATTERNS = (
    r"\bgrep\b",
    r"\btest\b",
    r"\bassert\b",
    r"[a-zA-Z_]+\.py:\d+",      # file:line
    r"<\d", r">\d", r"=\d", r"[≥≤]\d",  # numeric comparisons
    r"```",                     # explicit code block
    r"return\s+[A-Z]",          # exit-code check (e.g. return False, return None)
)


def has_falsifiability_anchor(modify_request: str) -> bool:
    """True if modify_request contains at least one verifiable predicate."""
    return any(
        re.search(p, modify_request, re.IGNORECASE)
        for p in _FALSIFIABILITY_PATTERNS
    )
# === END SENATE LAWS ===


VOTE_PATTERN_REGEX = re.compile(r"^[0-3]-[0-3](-[0-1])?$")

_TRIAS_NULL_PATTERNS = {"1-1-1", "1-1-0", "1-0-0", "0-0-0"}


def _validate_trias(report: dict, errors: list) -> None:
    """Trias-specific validation. Only runs when report has team == 'trias'."""
    personalities = report.get("personalities")
    if not isinstance(personalities, list) or len(personalities) != 3:
        errors.append("trias: personalities must be a list of exactly 3 entries")
        return
    names_seen: set[str] = set()
    for i, p in enumerate(personalities):
        if not isinstance(p, dict):
            errors.append(f"trias: personalities[{i}] must be a JSON object, got {type(p).__name__}")
            continue
        for f in ("name", "weights", "lens", "chose"):
            if f not in p:
                errors.append(f"trias: personalities[{i}] missing field {f!r}")
        if "name" in p:
            if p["name"] in names_seen:
                errors.append(f"trias: duplicate personality name {p['name']!r}")
            names_seen.add(p["name"])
    if names_seen and names_seen != frozenset(NAMES):
        errors.append(
            f"trias: personality names must be exactly {sorted(NAMES)},"
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
    # === RUND2 ===
    ap.add_argument(
        "--strict-rund2",
        action="store_true",
        default=False,
        help="require RUND2 fields (regression_risk object, tokens_budget) in conservator scores",
    )
    # === END RUND2 ===
    # === PHILOSOPHICAL VOICES ===
    ap.add_argument(
        "--strict-philosophical",
        choices=sorted(_PHILOSOPHICAL_VOICES),
        default=None,
        metavar="VOICE",
        help=f"require philosophical voice fields; one of: {', '.join(sorted(_PHILOSOPHICAL_VOICES))}",
    )
    # === END PHILOSOPHICAL VOICES ===
    # === SENATE LAWS ===
    ap.add_argument(
        "--strict-senate",
        action="store_true",
        default=False,
        help="validate senate bundle fields (Laws 6-8): verdict, scope_veto_consensus, addresses_prior_concerns, auto_promoted_senators",
    )
    # === END SENATE LAWS ===
    args = ap.parse_args(argv)

    try:
        report = json.load(args.input)
    except json.JSONDecodeError as exc:
        print(f"invalid JSON: {exc}", file=sys.stderr)
        return 2

    if not isinstance(report, dict):
        print("report must be a JSON object", file=sys.stderr)
        return 2

    # === SENATE LAWS ===
    if args.strict_senate:
        # Senate bundles have a different schema — skip standard deliberation validation.
        problems = _validate_senate_bundle(report)
    else:
        problems = validate(report)
        # === RUND2 ===
        if args.strict_rund2:
            problems.extend(_validate_rund2_fields(report))
        # === END RUND2 ===
        # === PHILOSOPHICAL VOICES ===
        if args.strict_philosophical:
            validator = _PHILOSOPHICAL_VALIDATORS.get(args.strict_philosophical)
            if validator:
                voice_output = report.get("voice_outputs", {}).get(args.strict_philosophical, report)
                problems.extend(validator(voice_output))
        # === END PHILOSOPHICAL VOICES ===
    # === END SENATE LAWS ===
    if problems:
        for p in problems:
            print(p, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
