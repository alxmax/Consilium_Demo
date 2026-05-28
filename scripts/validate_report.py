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


def _validate_sequential_fields(report: dict) -> list[str]:
    """Strict sequential-mode field validation — only run with --strict-rund2 flag."""
    problems = []
    for score in report.get("voice_scores", {}).get("conservator", {}).get("scores", []):
        rr = score.get("regression_risk")
        if rr is None:
            problems.append(f"strict-sequential: candidate '{score.get('id')}' conservator missing regression_risk object")
            continue
        problems.extend(_validate_regression_risk(rr))
        if "tokens_budget" not in score:
            problems.append(f"strict-sequential: candidate '{score.get('id')}' conservator missing tokens_budget")
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


# Reports whose pipeline was bypassed by design — voice-step presence is not required
# because Generator/Control never ran. See SKILL.md Step 2 (scale_down) and
# §"Prior-deliberation passthrough".
_PIPELINE_BYPASS_CHOSEN = frozenset({"trivial-direct", "prior-deliberation"})


def _validate_deliberation_log(log: object, skipped: bool, chosen: object = None) -> list[str]:
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
    # Voice-step presence: a non-bypassed report must show that Generator and Control
    # actually ran. Hand-assembled reports that skip these steps would have passed before.
    if chosen not in _PIPELINE_BYPASS_CHOSEN:
        problems: list[str] = []
        steps_present = {s.get("step") for s in log if isinstance(s, dict)}
        for required_step in ("generator", "control"):
            if required_step not in steps_present:
                problems.append(
                    f"deliberation_log missing '{required_step}' step "
                    f"(required for chosen_approach={chosen!r}; exempt only for "
                    f"trivial-direct/prior-deliberation reports)"
                )
        if problems:
            return problems
    return []


def _validate_pipeline_executed(report: dict) -> list[str]:
    """pipeline_executed must be present for non-skipped reports.

    True ⇔ the 3-voice Generator→Control deliberation ran end-to-end (build_report
    sets this automatically). False ⇔ the pipeline was bypassed (scale_down
    short-circuit, prior-deliberation passthrough — see SKILL.md Step 2).
    """
    if report.get("skipped") is True:
        return []
    pe = report.get("pipeline_executed")
    if pe is None:
        return [
            "pipeline_executed required (bool) for non-skipped reports; "
            "build_report.py emits True by default — set False explicitly for "
            "trivial-direct / prior-deliberation passthrough templates"
        ]
    if not isinstance(pe, bool):
        return [f"pipeline_executed must be bool, got {type(pe).__name__}"]
    # Consistency: bypassed-chosen ⇒ pipeline_executed: false
    chosen = report.get("chosen_approach")
    if chosen in _PIPELINE_BYPASS_CHOSEN and pe is True:
        return [
            f"pipeline_executed: true inconsistent with chosen_approach={chosen!r} "
            f"(bypass templates must set pipeline_executed: false)"
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
    # Dated removal milestones (enforced by scripts/check_doc_drift.py):
    #   parallel_skeptic, dialectic_skeptic → remove after 2026-08-17 (3mo post-collapse)
    #   trias_split → remove after 2026-08-21 (3mo post-deprecation)
    _LEGACY_MODE_ALIASES: dict[str, str] = {
        "parallel_skeptic": "skeptic_on_chosen",   # remove after 2026-08-17
        "dialectic_skeptic": "skeptic_on_chosen",  # remove after 2026-08-17
        "trias_split": "trias",                    # remove after 2026-08-21
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


VOTE_PATTERN_REGEX = re.compile(r"^([0-3])-([0-3])(-([0-1]))?$")


def _vote_pattern_valid(pattern: str) -> bool:
    """Return True if pattern matches regex AND vote counts sum to exactly 3."""
    m = VOTE_PATTERN_REGEX.match(pattern)
    if not m:
        return False
    parts = [int(x) for x in pattern.split("-")]
    return sum(parts) == 3

_TRIAS_NULL_PATTERNS = {"1-1-1", "1-1-0", "1-0-0", "0-0-0"}


def _validate_trias(report: dict, errors: list) -> None:
    """Trias-specific validation. Only runs when report has team == 'trias'."""
    personalities = report.get("personalities")
    shape_ok = isinstance(personalities, list) and len(personalities) == 3
    if not shape_ok:
        errors.append("trias: personalities must be a list of exactly 3 entries")
    names_seen: set[str] = set()
    if shape_ok:
        for i, p in enumerate(personalities):  # type: ignore[union-attr]
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
            # Bug 10: weights must be a dict whose values sum to ~1.0
            weights = p.get("weights")
            if weights is not None:
                if not isinstance(weights, dict):
                    errors.append(f"trias: personalities[{i}].weights must be a JSON object")
                else:
                    try:
                        w_sum = sum(float(v) for v in weights.values())
                        if abs(w_sum - 1.0) > 0.01:
                            errors.append(
                                f"trias: personalities[{i}].weights values must sum to ~1.0, got {w_sum:.4f}"
                            )
                    except (TypeError, ValueError):
                        errors.append(f"trias: personalities[{i}].weights values must be numeric")
            # Bug 10: lens must be a string
            lens = p.get("lens")
            if lens is not None and not isinstance(lens, str):
                errors.append(f"trias: personalities[{i}].lens must be a string, got {type(lens).__name__}")
    if names_seen and names_seen != frozenset(NAMES):
        errors.append(
            f"trias: personality names must be exactly {sorted(NAMES)},"
            f" got {sorted(names_seen)}"
        )

    pattern = report.get("vote_pattern")
    if not pattern or not _vote_pattern_valid(pattern):
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
    is_passthrough = report.get("chosen_approach") == "prior-deliberation"
    problems.extend(_validate_deliberation_log(
        report.get("deliberation_log"),
        report.get("skipped") is True or is_trias or is_passthrough,
        report.get("chosen_approach"),
    ))
    # Telemetry required for all non-skipped reports, Trias included — it's
    # the most expensive mode (9 sub-agenți) so cost rollup matters most there.
    problems.extend(_validate_telemetry_required(report))
    # pipeline_executed required for non-skipped reports (Trias and Sequential alike).
    # Distinguishes the 3-voice path from scale_down / passthrough short-circuits.
    problems.extend(_validate_pipeline_executed(report))

    if is_trias:
        _validate_trias(report, problems)

    return problems


_SUBSTANCE_SKIP_CHOSEN = frozenset({"trivial-direct", "prior-deliberation", "skipped"})
# Conservator "shrug" floor — net_concern pstdev below this is taken as a sign the
# voice gave nearly-uniform scores across candidates (no real differentiation).
_SUBSTANCE_SHRUG_PSTDEV_FLOOR = 0.01


def _warn_substance(report: dict) -> list[str]:
    """Heuristic substance checks. Returns a list of warning strings.

    By default these are emitted to stderr as advisory (non-blocking).
    With ``--strict-substance``, they are promoted to errors (exit 1).
    Skipped/passthrough/trivial-direct reports are exempt (no voices ran).

    Checks:
    1. generator.candidates is non-empty
    2. control.verdicts is non-empty
    3. STRICT-only: every valid:true verdict has a non-empty tests_to_write list
       (Control's mandatory deliverable per its prompt — exempted only for do_nothing
       candidates per the contract)
    4. STRICT-only: conservator.scores net_concern values are not all near-identical
       (the "shrug" antipattern — Conservator gave the same score to every candidate,
       indicating no real risk assessment was done)
    """
    if report.get("skipped"):
        return []
    chosen = report.get("chosen_approach")
    if chosen in _SUBSTANCE_SKIP_CHOSEN:
        return []
    warnings: list[str] = []
    for step in report.get("deliberation_log") or []:
        if not isinstance(step, dict):
            continue
        s = step.get("step")
        if s == "generator":
            cands = step.get("candidates")
            if isinstance(cands, list) and len(cands) == 0:
                warnings.append("SUBSTANCE WARNING: generator.candidates is empty — voices may not have done substantive work")
        elif s == "control":
            verdicts = step.get("verdicts")
            if isinstance(verdicts, list) and len(verdicts) == 0:
                warnings.append("SUBSTANCE WARNING: control.verdicts is empty — voices may not have done substantive work")
    return warnings


def _strict_substance_problems(report: dict) -> list[str]:
    """Stricter substance checks — promoted to errors under --strict-substance.

    Includes everything from _warn_substance plus:
    - missing tests_to_write on valid:true verdicts (except do_nothing)
    - Conservator score uniformity ("shrug" antipattern)
    """
    problems = list(_warn_substance(report))
    if report.get("skipped"):
        return problems
    chosen = report.get("chosen_approach")
    if chosen in _SUBSTANCE_SKIP_CHOSEN:
        return problems

    for step in report.get("deliberation_log") or []:
        if not isinstance(step, dict):
            continue
        s = step.get("step")
        if s == "control":
            for v in step.get("verdicts") or []:
                if not isinstance(v, dict):
                    continue
                if v.get("valid") is True and v.get("id") != "do_nothing":
                    tw = v.get("tests_to_write")
                    if not isinstance(tw, list) or len(tw) == 0:
                        problems.append(
                            f"STRICT SUBSTANCE: control verdict {v.get('id')!r} valid:true "
                            f"but tests_to_write is empty or missing (Control contract requires "
                            f"1-4 acceptance tests for non-do_nothing valid candidates)"
                        )
        elif s == "conservator":
            scores = step.get("scores") or []
            net_concerns: list[float] = []
            for sc in scores:
                if not isinstance(sc, dict):
                    continue
                rr = sc.get("regression_risk")
                if isinstance(rr, dict):
                    nc = rr.get("net_concern")
                else:
                    nc = rr
                if isinstance(nc, (int, float)) and not isinstance(nc, bool):
                    net_concerns.append(float(nc))
            if len(net_concerns) >= 3:
                pstdev = statistics.pstdev(net_concerns)
                if pstdev < _SUBSTANCE_SHRUG_PSTDEV_FLOOR:
                    problems.append(
                        f"STRICT SUBSTANCE: conservator scores show 'shrug' antipattern "
                        f"(net_concern pstdev={pstdev:.4f} < {_SUBSTANCE_SHRUG_PSTDEV_FLOOR}; "
                        f"all candidates rated nearly-identically — Conservator did not "
                        f"differentiate risk between alternatives)"
                    )
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
    ap.add_argument(
        "--strict-substance",
        action="store_true",
        default=False,
        help="promote substance heuristics (empty candidates/verdicts, missing tests_to_write, "
             "Conservator score uniformity) from advisory warnings to blocking errors",
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
    # === RUND2 ===
    if args.strict_rund2:
        problems.extend(_validate_sequential_fields(report))
    # === END RUND2 ===
    # === PHILOSOPHICAL VOICES ===
    if args.strict_philosophical:
        validator = _PHILOSOPHICAL_VALIDATORS.get(args.strict_philosophical)
        if validator:
            voice_output = report.get("voice_outputs", {}).get(args.strict_philosophical, report)
            problems.extend(validator(voice_output))
    # === END PHILOSOPHICAL VOICES ===
    if args.strict_substance:
        problems.extend(_strict_substance_problems(report))
    if problems:
        for p in problems:
            print(p, file=sys.stderr)
        return 1
    if not args.strict_substance:
        # Advisory mode — warnings to stderr but don't block exit 0
        for w in _warn_substance(report):
            print(w, file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
