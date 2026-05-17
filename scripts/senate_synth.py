"""Synthesize a Senate deliberation into a verdict bundle.

Orchestration note: this script is NOT a dispatcher. The 7 senators are
dispatched as sub-agents by the Claude orchestrator when
`/consilium senate <proposal>` is invoked (see SKILL.md "Senate mode").
This script consumes the senator JSON outputs and produces one bundle:

  - vote tally + verdict (GO / MODIFY / STOP / UNREACHABLE)
  - flat list of modify_requests
  - structured per-senator outputs (latest per senator)
  - warnings (only structural anomalies; absent senators surface via
    senators_absent rather than warning duplication)

Input format (multi-round, Laws 1-5 active):

      {
        "proposal": "<text>",
        "label":    "<short>",
        "rounds": [
          {"round": 1, "senators": {"wittgenstein": {..., "cross_questions": [
              {"to": "socrate", "question": "..."}
          ]}, ...}},
          {"round": 2, "senators": {"socrate": {<updated output, vote may change>}}},
          {"round": 3, "senators": {...}}          # max 3 rounds
        ],
        "blocaj_resolution": {                     # optional; orchestrator
            "pair": ["musk", "confucius"],         # supplies after 5-vote
            "winning_senator": "musk",             # tiebreaker dispatch
            "votes_from_others": {                 # 5 other senators choose
                "wittgenstein": "musk", ...        # which argument wins
            }
        },
        "absent": ["<senator_name>", ...]          # optional
      }

Verdict rule (same for both modes):
    UNREACHABLE  if voters_present < 5 (mathematically cannot reach quorum)
    GO           if GO   >= 5 of 7
    STOP         if STOP >= 5 of 7
    DEEPLY_SPLIT if quorum met, neither majority, AND both GO and STOP factions
                 reach POLARIZATION_THRESHOLD (currently 3 = QUORUM-2, "within
                 2 vote flips of majority"). Covers 4-3, 3-3-1, 3-4 patterns.
    MODIFY       otherwise (default — covers non-polarized non-quorum splits
                 like 4-0-3, 3-4 with abstentions where one side is below 3, etc.)

DEEPLY_SPLIT is advisory like UNREACHABLE: orchestrator MUST escalate to the
user with the vote matrix + per-senator modify_requests. No automatic action.

Multi-round semantics (Law 2: max 3 cross_questions per senator per round;
Law 3: blocaj_resolution.winning_senator's vote replaces loser's vote in the
tally; Law 4: synthesis runs once, at end, on latest votes per senator).

CLI:
    cat senate_input.json | python -X utf8 scripts/senate_synth.py

Output: writes runs/senate/<YYYY-MM-DD_HHMMSS>-<label>.json (collision-safe
via second-level granularity + numeric suffix if needed) and prints the
bundle to stdout.

Fixture (Socrate falsification request): see `scripts/senate_synth_fixture.json`
for a known-input -> known-verdict pair used in smoke tests.
"""

from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import re
import sys
from pathlib import Path

from utils import force_utf8_streams, load_json_stdin, validate_keys

SENATORS = (
    "wittgenstein",
    "aurelius",
    "confucius",
    "socrate",
    "musk",
    "dimon",
    "napoleon",
)
# code_audit mode (EXPERIMENTAL_DRAFT): tokens whose presence in senator output
# signals skill-audit framing leak on a user-code review. Allowed when the user
# code under audit IS a Consilium contribution (caller sets is_consilium_contribution).
SKILL_INTERNAL_ARTIFACTS = frozenset({
    "prompts/voices/", "prompts/senators/", "prompts/lenses/",
    "scripts/aggregator.py", "scripts/conservator", "scripts/generator",
    "scripts/senate_synth", "scripts/dialectic_merge", "scripts/personalities",
    "skill.md", "claude.md", "consilium internals", "consilium skill",
})
QUORUM = 5  # >= 5 of 7 needed for GO or STOP verdict
# A faction is "substantial" if it is within 2 vote flips of becoming majority.
# With QUORUM=5, that is 3 senators. Used by DEEPLY_SPLIT to detect a polarized
# split where both GO and STOP factions reach this threshold but neither hits
# majority. Derived from QUORUM rather than asserted so it scales if QUORUM
# changes (e.g., a future 9-senator senate with QUORUM=6 → threshold=4).
POLARIZATION_THRESHOLD = QUORUM - 2
VOTES = ("GO", "MODIFY", "STOP")
MAX_CROSS_QUESTIONS_PER_SENATOR_PER_ROUND = 3  # Law 2

# Per-senator structural expectations: if a senator votes but omits its
# signature structured field, the audit is silent on that axis. We surface a
# warning rather than fail — orchestrator decides whether to retry or accept.
SENATOR_REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
    "wittgenstein": ("vague_terms_found",),
    "aurelius":     ("reversibility", "magnitude"),
    "confucius":    ("hierarchy_check",),
    "socrate":      ("hidden_assumptions",),
    "musk":         ("components_attacked",),
    "dimon":        ("stress_scenarios",),
    "napoleon":     ("cost_estimate",),
}


def normalize_vote(raw) -> str | None:
    """Map a senator's vote string to GO/MODIFY/STOP, or None if unrecognized.

    Returns None on missing/unrecognized — caller surfaces this as a warning
    AND counts it as MODIFY in the tally (most-conservative non-blocking).
    """
    if not isinstance(raw, str):
        return None
    upper = raw.strip().upper()
    return upper if upper in VOTES else None



def collect_final_outputs(rounds: list[dict]) -> dict[str, dict]:
    """For each senator that appeared in any round, return their LATEST output.

    Latest = highest round index in which they were present. Preserves canonical
    senator ordering for stable bundle serialization.
    """
    latest: dict[str, dict] = {}
    latest_round: dict[str, int] = {}
    for r in rounds:
        for name, output in r["senators"].items():
            if name not in latest_round or r["round"] >= latest_round[name]:
                latest[name] = output
                latest_round[name] = r["round"]
    return {n: latest[n] for n in SENATORS if n in latest}


def detect_position_changes(rounds: list[dict]) -> list[dict]:
    """Track per-senator vote changes between successive appearances.

    Only emits when normalize_vote(...) changes between rounds. The trigger
    string includes which senator(s) emitted a cross_question targeting this
    senator in the immediately preceding round (heuristic — orchestrator can
    enrich post-hoc by reading rounds[round_idx-1].senators[*].cross_questions).
    """
    history: dict[str, list[dict]] = {}
    for r in rounds:
        for name, output in r["senators"].items():
            history.setdefault(name, []).append({
                "round": r["round"],
                "vote": normalize_vote(output.get("vote")),
            })
    changes: list[dict] = []
    for name, hist in history.items():
        for i in range(1, len(hist)):
            prev, curr = hist[i - 1], hist[i]
            if prev["vote"] != curr["vote"]:
                changes.append({
                    "senator": name,
                    "from_round": prev["round"],
                    "to_round": curr["round"],
                    "from_vote": prev["vote"],
                    "to_vote": curr["vote"],
                    "trigger": _infer_trigger(rounds, name, prev["round"], curr["round"]),
                })
    return changes


def _infer_trigger(rounds: list[dict], target: str, from_round: int, to_round: int) -> str:
    """Best-effort: which senator's cross_question targeting `target` likely
    triggered the change. Scans rounds between from_round and to_round inclusive.
    """
    triggers: list[str] = []
    for r in rounds:
        if r["round"] < from_round or r["round"] >= to_round:
            continue
        for from_senator, output in r["senators"].items():
            cqs = output.get("cross_questions") or []
            if not isinstance(cqs, list):
                continue
            for cq in cqs:
                if isinstance(cq, dict) and cq.get("to") == target:
                    triggers.append(f"cross-Q from {from_senator} in round {r['round']}")
    return "; ".join(triggers) if triggers else "unspecified"


def cross_questions_summary(rounds: list[dict]) -> tuple[dict[str, int], list[str]]:
    """Sum cross_questions emitted per senator (across all rounds) and surface
    Law-2 violations (more than MAX per senator per round).
    """
    totals: dict[str, int] = {}
    violations: list[str] = []
    for r in rounds:
        per_round: dict[str, int] = {}
        for name, output in r["senators"].items():
            cqs = output.get("cross_questions") or []
            if not isinstance(cqs, list):
                continue
            n = len(cqs)
            per_round[name] = n
            totals[name] = totals.get(name, 0) + n
        for name, n in per_round.items():
            if n > MAX_CROSS_QUESTIONS_PER_SENATOR_PER_ROUND:
                violations.append(
                    f"law_2_violation: senator '{name}' emitted {n} cross_questions in round "
                    f"{r['round']} (max {MAX_CROSS_QUESTIONS_PER_SENATOR_PER_ROUND})"
                )
    return totals, violations


def detect_blocaj_pairs(final_outputs: dict[str, dict]) -> list[dict]:
    """Find every GO×STOP senator pair in final votes — candidates for Law-3
    tiebreaker. Pairs are surfaced when no `blocaj_resolution` was provided
    by orchestrator; presence of pairs without resolution becomes a warning.
    """
    go = sorted(n for n, o in final_outputs.items() if normalize_vote(o.get("vote")) == "GO")
    stop = sorted(n for n, o in final_outputs.items() if normalize_vote(o.get("vote")) == "STOP")
    return [{"go_senator": a, "stop_senator": b} for a in go for b in stop]


def apply_blocaj_resolution(
    final_outputs: dict[str, dict],
    blocaj_resolution,
) -> tuple[dict[str, dict], dict | None]:
    """Per Law 3: when 2 senators are in GO×STOP opposition after cross-questions,
    the other 5 vote between the two arguments. Winning side's vote replaces
    the losing senator's vote in the tally. Individual outputs are NOT mutated;
    we return a parallel dict with the adjusted vote so the original record is
    preserved for audit.
    """
    if not isinstance(blocaj_resolution, dict):
        return final_outputs, None
    pair = blocaj_resolution.get("pair")
    winner = blocaj_resolution.get("winning_senator")
    if not (isinstance(pair, list) and len(pair) == 2 and winner in pair):
        return final_outputs, None
    loser = pair[1] if pair[0] == winner else pair[0]
    if winner not in final_outputs or loser not in final_outputs:
        return final_outputs, None
    winning_vote = normalize_vote(final_outputs[winner].get("vote"))
    if winning_vote is None:
        return final_outputs, None
    adjusted = dict(final_outputs)
    adjusted[loser] = dict(final_outputs[loser])
    adjusted[loser]["vote"] = winning_vote
    adjusted[loser]["_blocaj_override"] = {
        "original_vote": normalize_vote(final_outputs[loser].get("vote")),
        "replaced_by": winner,
    }
    info = {
        "pair": pair,
        "winning_senator": winner,
        "winning_vote": winning_vote,
        "losing_senator": loser,
        "votes_from_others": blocaj_resolution.get("votes_from_others", {}),
    }
    return adjusted, info


def tally(senator_outputs: dict[str, dict]) -> dict[str, int]:
    counts = {v: 0 for v in VOTES}
    for output in senator_outputs.values():
        vote = normalize_vote(output.get("vote"))
        counts[vote if vote is not None else "MODIFY"] += 1
    return counts


def compute_verdict(counts: dict[str, int], voters_present: int) -> str:
    """Map (counts, voters_present) → verdict string.

    voters_present = number of senators with a recorded ballot in the latest
    round they appeared in. MODIFY votes count toward voters_present but go
    into counts["MODIFY"], not counts["GO"]/counts["STOP"]. Senators absent
    from all rounds do NOT contribute to voters_present.

    Order matters: GO/STOP majority checks run before DEEPLY_SPLIT, so a 5-2
    or 6-1 split is always reported as the majority verdict even though the
    minority side may reach POLARIZATION_THRESHOLD (here, 5-3 cannot occur
    with 7 senators, but 5-4 in a future 9-senator senate would still resolve
    to GO, not DEEPLY_SPLIT).
    """
    if voters_present < QUORUM:
        return "UNREACHABLE"
    if counts["GO"] >= QUORUM:
        return "GO"
    if counts["STOP"] >= QUORUM:
        return "STOP"
    if counts["GO"] >= POLARIZATION_THRESHOLD and counts["STOP"] >= POLARIZATION_THRESHOLD:
        return "DEEPLY_SPLIT"
    return "MODIFY"


def collect_modify_requests(senator_outputs: dict[str, dict]) -> list[dict]:
    requests = []
    for name, output in senator_outputs.items():
        req = output.get("modify_request")
        if isinstance(req, str) and req.strip():
            requests.append({"senator": name, "request": req.strip()})
    return requests


def collect_warnings(senator_outputs: dict[str, dict], voters_present: int) -> list[str]:
    """Surface only structural anomalies. Absent senators are recorded in
    `senators_absent`, so they do not generate redundant warnings here.
    """
    warnings = []
    for name in SENATORS:
        if name not in senator_outputs:
            continue
        output = senator_outputs[name]
        raw_vote = output.get("vote")
        if normalize_vote(raw_vote) is None:
            warnings.append(
                f"senator '{name}' emitted unrecognized vote {raw_vote!r} (counted as MODIFY)"
            )
        for field in SENATOR_REQUIRED_FIELDS.get(name, ()):
            value = output.get(field)
            if value is None or (isinstance(value, (list, dict)) and len(value) == 0):
                warnings.append(
                    f"senator '{name}' voted but omitted/empty '{field}' — that axis of audit is silent"
                )
    if voters_present < QUORUM:
        warnings.append(
            f"quorum_unreachable: only {voters_present} of {len(SENATORS)} senators voted "
            f"(need >= {QUORUM} to reach GO or STOP); verdict structurally biased toward MODIFY"
        )
    return warnings


def artifact_leak_count(senator_output: dict) -> int:
    """Count substring matches of skill-internal artifacts in senator output JSON.
    Threshold > 1 marks output off-target on code_audit mode."""
    text = json.dumps(senator_output, ensure_ascii=False).lower()
    return sum(1 for a in SKILL_INTERNAL_ARTIFACTS if a in text)


def extract_verdict_artifacts(senator_output: dict, files_touched: list) -> list:
    """Post-hoc orchestrator-extracted file refs; not LLM self-reported.
    Substring match; caller is responsible for path normalization upstream."""
    text = json.dumps(senator_output, ensure_ascii=False)
    return [f for f in files_touched if f in text]


def apply_code_audit_filter(
    senator_outputs: dict, files_touched: list, is_consilium_contribution: bool,
) -> tuple[dict, dict, list]:
    """Mark senators suspect on zero file refs or skill-vocabulary leak.
    Returns (filtered_outputs, verdict_artifacts_per_senator, suspect_names)."""
    filtered, artifacts, suspects = {}, {}, []
    for name, output in senator_outputs.items():
        refs = extract_verdict_artifacts(output, files_touched)
        leak = (not is_consilium_contribution) and artifact_leak_count(output) > 1
        artifacts[name] = refs
        if not refs or leak:
            suspects.append(name)
            continue  # excluded from quorum
        filtered[name] = output
    return filtered, artifacts, suspects


def slugify(label: str) -> str:
    s = re.sub(r"[^A-Za-z0-9_-]+", "-", label.strip())
    s = re.sub(r"-+", "-", s).strip("-")
    return s.lower() or "senate"


def build_bundle(
    proposal: str,
    rounds: list[dict],
    blocaj_resolution,
    absent: list[str],
    label: str,
    timestamp: str,
    mode: str = "skill_audit",
    files_touched: list | None = None,
    is_consilium_contribution: bool = False,
) -> dict:
    senators_appearing = {n for r in rounds for n in r["senators"].keys()}
    senators_absent = sorted({n for n in SENATORS if n not in senators_appearing} | set(absent))

    final_outputs = collect_final_outputs(rounds)
    code_audit_artifacts, code_audit_suspects = None, []
    if mode == "code_audit" and files_touched:
        final_outputs, code_audit_artifacts, code_audit_suspects = apply_code_audit_filter(
            final_outputs, files_touched, is_consilium_contribution,
        )
        senators_absent = sorted(set(senators_absent) | set(code_audit_suspects))
    voters_present = len(final_outputs)

    raw_counts = tally(final_outputs)
    adjusted_outputs, blocaj_info = apply_blocaj_resolution(final_outputs, blocaj_resolution)
    final_counts = tally(adjusted_outputs) if blocaj_info else raw_counts

    cq_used, cq_violations = cross_questions_summary(rounds)
    position_changes = detect_position_changes(rounds)

    # Compute verdict before blocaj_pending: emit advisory signal when verdict
    # is MODIFY or DEEPLY_SPLIT (both indicate unresolved GO×STOP polarization
    # the orchestrator may want to put through a 5-vote tiebreaker). Suppressed
    # on clean GO/STOP outcomes.
    verdict = compute_verdict(final_counts, voters_present)
    blocaj_pending = []
    if blocaj_info is None and verdict in ("MODIFY", "DEEPLY_SPLIT"):
        blocaj_pending = detect_blocaj_pairs(final_outputs)

    warnings = collect_warnings(final_outputs, voters_present)
    warnings.extend(cq_violations)
    if blocaj_pending:
        warnings.append(
            f"blocaj_pending: {len(blocaj_pending)} GO×STOP pair(s) without resolution; "
            "orchestrator must dispatch 5-vote tiebreaker (Law 3)"
        )

    # When a blocaj resolution applied, `outputs` reflects the post-override
    # state (so tally(outputs) == vote_counts) with `_blocaj_override` marker
    # preserving the senator's original vote for audit.
    outputs_for_bundle = adjusted_outputs if blocaj_info else final_outputs
    bundle: dict = {
        "timestamp": timestamp,
        "label": label,
        "proposal": proposal,
        "mode": mode,
        "senators_absent": senators_absent,
        "outputs": outputs_for_bundle,
        "vote_counts": final_counts,
        "verdict": verdict,
        "modify_requests": collect_modify_requests(final_outputs),
        "warnings": warnings,
    }
    if mode == "code_audit":
        bundle["verdict_artifacts"] = code_audit_artifacts or {}
        bundle["semantic_suspects"] = code_audit_suspects
        if code_audit_suspects:
            warnings.append(
                f"code_audit: {len(code_audit_suspects)} senator(s) marked semantic_suspect "
                f"(zero file refs or skill-vocabulary leak): {', '.join(code_audit_suspects)}"
            )
    bundle["rounds"] = rounds
    bundle["position_changes"] = position_changes
    bundle["cross_questions_used"] = cq_used
    if blocaj_info:
        bundle["blocaj_resolution"] = blocaj_info
        bundle["vote_counts_pre_blocaj"] = raw_counts
    if blocaj_pending:
        bundle["blocaj_pending"] = blocaj_pending
    return bundle


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


REQUIRED_BUNDLE_KEYS = (
    "timestamp", "label", "proposal", "mode",
    "senators_absent", "outputs", "vote_counts", "verdict",
    "modify_requests", "warnings",
)


def validate_bundle(bundle: dict) -> None:
    """Fail-fast guard before write: ensure required top-level keys exist.

    Raises ValueError citing the missing key. Dimon R2 modify_request: synth.py
    must refuse to write incomplete bundles rather than emit JSON that downstream
    consumers (senate_history.py, transcripts) might render with inverted/missing
    verdicts.
    """
    for key in REQUIRED_BUNDLE_KEYS:
        if key not in bundle:
            raise ValueError(f"senate_synth: bundle missing required key {key!r}")
    if not isinstance(bundle["vote_counts"], dict):
        raise ValueError("senate_synth: 'vote_counts' must be a dict")
    if bundle["verdict"] not in ("GO", "MODIFY", "STOP", "DEEPLY_SPLIT", "UNREACHABLE"):
        raise ValueError(f"senate_synth: invalid verdict {bundle['verdict']!r}")


def write_bundle(bundle: dict) -> Path:
    """Write bundle to runs/senate/, avoiding silent overwrite.

    Filename: <timestamp>-<slug(label)>.json with second-level granularity.
    On collision (same timestamp + label), suffix `_v2`, `_v3`, ... is added.
    """
    validate_bundle(bundle)
    out_dir = repo_root() / "runs" / "senate"
    out_dir.mkdir(parents=True, exist_ok=True)
    base = f"{bundle['timestamp']}-{slugify(bundle['label'])}"
    out_path = out_dir / f"{base}.json"
    n = 2
    while out_path.exists():
        out_path = out_dir / f"{base}_v{n}.json"
        n += 1
    out_path.write_text(json.dumps(bundle, indent=2, ensure_ascii=False), encoding="utf-8")
    return out_path


def parse_args() -> argparse.Namespace:
    return argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    ).parse_args()


def main() -> int:
    force_utf8_streams()
    parse_args()
    data = load_json_stdin("senate_synth.py")
    validate_keys(data, ["proposal"], "senate_synth input")
    if "rounds" not in data:
        print("senate_synth: input must contain 'rounds' list; legacy 'senators' format no longer supported", file=sys.stderr)
        return 1

    proposal = str(data["proposal"]).strip()
    if not proposal:
        print("senate_synth: 'proposal' must be a non-empty string", file=sys.stderr)
        return 1

    rounds_raw = data["rounds"]
    if not isinstance(rounds_raw, list) or not rounds_raw:
        print("senate_synth: 'rounds' must be a non-empty list", file=sys.stderr)
        return 1
    rounds = []
    for i, r in enumerate(rounds_raw):
        if not isinstance(r, dict):
            continue
        senators = r.get("senators")
        if not isinstance(senators, dict):
            continue
        rounds.append({"round": r.get("round", i + 1), "senators": senators})
    if not rounds:
        print("senate_synth: 'rounds' contains no valid senator entries", file=sys.stderr)
        return 1

    absent = data.get("absent", [])
    if not isinstance(absent, list):
        absent = []

    label = data.get("label") or "senate"
    timestamp = dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    blocaj_resolution = data.get("blocaj_resolution")
    mode = data.get("mode", "skill_audit")
    if mode not in ("skill_audit", "code_audit"):
        print(f"senate_synth: unknown mode {mode!r}; expected skill_audit|code_audit", file=sys.stderr)
        return 1
    files_touched = data.get("files_touched") or []
    if not isinstance(files_touched, list):
        files_touched = []
    is_consilium_contribution = bool(data.get("is_consilium_contribution", False))

    bundle = build_bundle(
        proposal, rounds, blocaj_resolution,
        absent, label, timestamp,
        mode=mode, files_touched=files_touched,
        is_consilium_contribution=is_consilium_contribution,
    )

    # Optional telemetry passthrough: orchestrator may include per-senator
    # tokens/latency captured from Agent dispatch (e.g. <usage>total_tokens: N</usage>)
    # in the input JSON. Shape matches usage.py expectations:
    #   {"mode": "senate", "voices": {"<senator>": {"tokens_in": N, "tokens_out": N,
    #    "latency_ms": N, "source": "api_usage_field"|"estimate_chars_div_4"}}}
    telemetry = data.get("telemetry")
    if isinstance(telemetry, dict):
        bundle["telemetry"] = telemetry

    print(json.dumps(bundle, indent=2, ensure_ascii=False))
    out_path = write_bundle(bundle)
    print(f"\nwritten: {out_path.relative_to(repo_root())}", file=sys.stderr)

    # auto-append decisions to TODO.md
    try:
        _spec = importlib.util.spec_from_file_location(
            "senate_todo", Path(__file__).parent / "senate_todo.py"
        )
        if _spec is None or _spec.loader is None:
            raise ImportError("senate_todo.py not found")
        _mod = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_mod)  # type: ignore[union-attr]
        if _mod.append_bundle_to_todo(bundle):
            print("todo: hotărârea adăugată în TODO.md", file=sys.stderr)
        else:
            print("todo: sesiunea era deja în TODO.md, skip.", file=sys.stderr)
    except Exception as _e:
        print(f"todo: skip ({_e})", file=sys.stderr)

    _generate_transcript(out_path)
    return 0


def _generate_transcript(bundle_path: Path) -> None:
    try:
        import importlib.util as _ilu
        _spec = _ilu.spec_from_file_location("senate_transcript", Path(__file__).parent / "deprecated" / "senate_transcript.py")
        _mod = _ilu.module_from_spec(_spec)  # type: ignore[arg-type]
        _spec.loader.exec_module(_mod)  # type: ignore[union-attr]
        out_file = _mod.generate(bundle_path)
        if out_file:
            print(f"transcript: {out_file.relative_to(bundle_path.parent.parent)}", file=sys.stderr)
    except Exception as exc:
        print(f"transcript generation skipped: {exc}", file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main())
