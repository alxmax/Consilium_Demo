"""Smoke tests for the Senate pipeline (stdlib-only, no test framework).

Following CLAUDE.md: "No tests dir. Smoke-test manual prin CLI." This script
exercises senate_synth.py and the 7 senator prompt files end-to-end and
reports pass/fail per case.

CLI:
    python -X utf8 scripts/test_senate_synth.py             # run all
    python -X utf8 scripts/test_senate_synth.py --verbose   # print bundle on each case
    python -X utf8 scripts/test_senate_synth.py --keep      # keep generated runs/senate/*.json

Exit: 0 if all pass, 1 if any fail. Intended as a quick gate before commits
touching senate_synth.py or any prompts/senators/*.md.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SYNTH = REPO / "scripts" / "senate_synth.py"
FIXTURE = REPO / "scripts" / "senate_synth_fixture.json"
SENATORS_DIR = REPO / "prompts" / "senators"
RUNS_DIR = REPO / "runs" / "senate"

SENATORS = (
    "wittgenstein", "aurelius", "confucius", "socrate",
    "musk", "dimon", "napoleon",
)
REQUIRED_PROMPT_SECTIONS = ("## Rol", "## Specialitate", "## Output format", "## Limite")


# ───────────────────────── helpers ─────────────────────────


def run_synth(payload: dict) -> tuple[int, dict | None, str]:
    """Pipe payload as stdin to senate_synth.py. Returns (exit_code, parsed_stdout_or_None, stderr)."""
    proc = subprocess.run(
        [sys.executable, "-X", "utf8", str(SYNTH)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=REPO,
    )
    parsed = None
    if proc.stdout.strip():
        try:
            parsed = json.loads(proc.stdout)
        except json.JSONDecodeError:
            pass
    return proc.returncode, parsed, proc.stderr


def base_senator_output(vote: str, modify_request: str = "") -> dict:
    """Minimal senator output that won't trigger structural warnings."""
    return {"vote": vote, "modify_request": modify_request}


def make_payload(
    proposal: str,
    senators: dict[str, dict],
    label: str = "smoke",
    absent: list[str] | None = None,
) -> dict:
    return {
        "proposal": proposal,
        "label": label,
        "rounds": [{"round": 1, "senators": senators}],
        "absent": absent or [],
    }


def all_voting(vote: str) -> dict[str, dict]:
    return {name: base_senator_output(vote) for name in SENATORS}


# ─────────────────────── test cases ────────────────────────


def test_prompts_are_consistent() -> tuple[bool, str]:
    """Each prompts/senators/<name>.md is valid markdown + has required sections."""
    missing = []
    for name in SENATORS:
        path = SENATORS_DIR / f"{name}.md"
        if not path.exists():
            return False, f"missing prompt file: {path.relative_to(REPO)}"
        text = path.read_text(encoding="utf-8")
        for section in REQUIRED_PROMPT_SECTIONS:
            if section not in text:
                missing.append(f"{name}.md missing section '{section}'")
        if '"vote"' not in text:
            missing.append(f"{name}.md output format missing 'vote' field declaration")
        if '"modify_request"' not in text:
            missing.append(f"{name}.md output format missing 'modify_request' field declaration")
    if missing:
        return False, "; ".join(missing)
    return True, f"all 7 prompts present, structured, declare vote + modify_request"


def test_fixture_smoke() -> tuple[bool, str]:
    """The shipped fixture produces the documented verdict + warning."""
    if not FIXTURE.exists():
        return False, f"missing fixture: {FIXTURE.relative_to(REPO)}"
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    # Strip metadata key from fixture
    payload.pop("_description", None)
    code, bundle, stderr = run_synth(payload)
    if code != 0 or bundle is None:
        return False, f"synth exit={code}, stderr={stderr.strip()[:200]}"
    if bundle["verdict"] != "MODIFY":
        return False, f"expected MODIFY, got {bundle['verdict']}"
    if bundle["vote_counts"] != {"GO": 3, "MODIFY": 3, "STOP": 1}:
        return False, f"unexpected vote_counts: {bundle['vote_counts']}"
    if not any("dimon" in w and "stress_scenarios" in w for w in bundle["warnings"]):
        return False, f"expected dimon stress_scenarios warning, got: {bundle['warnings']}"
    return True, f"fixture -> MODIFY (3/3/1) + dimon warning surfaced"


def _require_bundle(code: int, bundle: dict | None, stderr: str) -> tuple[bool, str] | dict:
    """Guard: return (False, message) on synth failure, else return the bundle."""
    if code != 0 or bundle is None:
        return False, f"synth exit={code}, stderr={stderr.strip()[:200]}"
    return bundle


def test_verdict_go_unanimous() -> tuple[bool, str]:
    """7-of-7 GO yields verdict GO."""
    code, bundle, stderr = run_synth(make_payload(
        proposal="all-GO smoke test",
        senators=all_voting("GO"),
        label="smoke-go",
    ))
    guard = _require_bundle(code, bundle, stderr)
    if isinstance(guard, tuple):
        return guard
    bundle = guard
    if bundle["verdict"] != "GO":
        return False, f"expected GO, got {bundle['verdict']}"
    if bundle["vote_counts"]["GO"] != 7:
        return False, f"expected 7 GO, got {bundle['vote_counts']}"
    return True, "7/7 GO -> verdict GO"


def test_verdict_go_quorum() -> tuple[bool, str]:
    """5-of-7 GO + 2 MODIFY yields verdict GO."""
    senators = all_voting("GO")
    senators["musk"] = base_senator_output("MODIFY", "trim something")
    senators["dimon"] = base_senator_output("MODIFY", "add stress test")
    code, bundle, stderr = run_synth(make_payload(
        proposal="quorum smoke", senators=senators, label="smoke-quorum-go"))
    guard = _require_bundle(code, bundle, stderr)
    if isinstance(guard, tuple):
        return guard
    bundle = guard
    if bundle["verdict"] != "GO":
        return False, f"expected GO at 5/7, got {bundle['verdict']} (counts {bundle['vote_counts']})"
    return True, "5/7 GO + 2 MODIFY -> verdict GO"


def test_verdict_modify_default() -> tuple[bool, str]:
    """No-quorum split (e.g. 4 GO / 3 MODIFY) yields MODIFY."""
    senators = all_voting("GO")
    for name in ("musk", "dimon", "socrate"):
        senators[name] = base_senator_output("MODIFY", "x")
    code, bundle, stderr = run_synth(make_payload(
        proposal="no-quorum smoke", senators=senators, label="smoke-modify"))
    guard = _require_bundle(code, bundle, stderr)
    if isinstance(guard, tuple):
        return guard
    bundle = guard
    if bundle["verdict"] != "MODIFY":
        return False, f"expected MODIFY, got {bundle['verdict']} (counts {bundle['vote_counts']})"
    return True, "4 GO / 3 MODIFY -> verdict MODIFY"


def test_verdict_unreachable() -> tuple[bool, str]:
    """4 senators voting (3 absent) is below quorum -> UNREACHABLE."""
    present = ("wittgenstein", "aurelius", "confucius", "socrate")
    senators = {name: base_senator_output("GO") for name in present}
    code, bundle, stderr = run_synth(make_payload(
        proposal="unreachable smoke",
        senators=senators,
        absent=["musk", "dimon", "napoleon"],
        label="smoke-unreachable",
    ))
    guard = _require_bundle(code, bundle, stderr)
    if isinstance(guard, tuple):
        return guard
    bundle = guard
    if bundle["verdict"] != "UNREACHABLE":
        return False, f"expected UNREACHABLE, got {bundle['verdict']}"
    if not any("quorum_unreachable" in w for w in bundle["warnings"]):
        return False, f"expected quorum_unreachable warning, got: {bundle['warnings']}"
    if sorted(bundle["senators_absent"]) != ["dimon", "musk", "napoleon"]:
        return False, f"unexpected senators_absent: {bundle['senators_absent']}"
    return True, "4 present / 3 absent -> UNREACHABLE + quorum_unreachable warning"


def test_unrecognized_vote_warns_and_counts_modify() -> tuple[bool, str]:
    """A senator emitting an invalid vote string is counted MODIFY + warned."""
    senators = all_voting("GO")
    senators["aurelius"] = {"vote": "maybe", "modify_request": ""}
    code, bundle, stderr = run_synth(make_payload(
        proposal="bad-vote smoke", senators=senators, label="smoke-badvote"))
    guard = _require_bundle(code, bundle, stderr)
    if isinstance(guard, tuple):
        return guard
    bundle = guard
    if bundle["vote_counts"]["MODIFY"] != 1 or bundle["vote_counts"]["GO"] != 6:
        return False, f"expected 6 GO + 1 MODIFY, got {bundle['vote_counts']}"
    if not any("aurelius" in w and "unrecognized" in w for w in bundle["warnings"]):
        return False, f"expected unrecognized-vote warning for aurelius, got: {bundle['warnings']}"
    return True, "invalid vote -> counted MODIFY + structural warning surfaced"


def test_bundle_persisted_and_valid_json() -> tuple[bool, str]:
    """Last smoke run must have produced a parsable runs/senate/*.json file."""
    files = sorted(RUNS_DIR.glob("*-smoke-*.json"))
    if not files:
        return False, "no runs/senate/*-smoke-*.json file produced"
    last = files[-1]
    try:
        data = json.loads(last.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return False, f"bundle parse failed: {exc}"
    required = {"timestamp", "label", "proposal", "outputs", "verdict", "vote_counts", "modify_requests", "warnings", "senators_absent"}
    missing = required - set(data.keys())
    if missing:
        return False, f"bundle missing keys: {missing}"
    return True, f"bundle {last.name} parsable + has required keys"


# ───────── multi-round tests (Laws 2-4) ─────────


def make_multi_round_payload(
    proposal: str,
    rounds: list[dict],
    label: str = "smoke",
    absent: list[str] | None = None,
    blocaj_resolution: dict | None = None,
) -> dict:
    payload: dict = {
        "proposal": proposal,
        "label": label,
        "rounds": rounds,
        "absent": absent or [],
    }
    if blocaj_resolution is not None:
        payload["blocaj_resolution"] = blocaj_resolution
    return payload


def test_multi_round_position_change() -> tuple[bool, str]:
    """Senator changes vote between Round 1 and Round 2 — position_changes populated.

    Law 2 + Law 4: cross-question prompts senator to revise; final synthesis uses
    latest vote per senator (Round 2 overrides Round 1).
    """
    round1 = {
        "round": 1,
        "senators": {
            "wittgenstein": {"vote": "GO", "modify_request": "",
                             "cross_questions": [{"to": "musk", "question": "Why delete X?"}]},
            "aurelius":     base_senator_output("GO"),
            "confucius":    base_senator_output("GO"),
            "socrate":      base_senator_output("GO"),
            "musk":         base_senator_output("STOP", "delete X first"),
            "dimon":        base_senator_output("GO"),
            "napoleon":     base_senator_output("GO"),
        },
    }
    round2 = {
        "round": 2,
        "senators": {
            "musk": base_senator_output("GO", "ok keeping X with justification"),
        },
    }
    code, bundle, stderr = run_synth(make_multi_round_payload(
        proposal="multi-round position change", rounds=[round1, round2], label="smoke-multi-pos"))
    guard = _require_bundle(code, bundle, stderr)
    if isinstance(guard, tuple):
        return guard
    bundle = guard
    if "rounds" not in bundle:
        return False, "expected bundle.rounds to be present for multi-round input"
    if "position_changes" not in bundle or not bundle["position_changes"]:
        return False, f"expected position_changes populated, got: {bundle.get('position_changes')}"
    musk_change = next((c for c in bundle["position_changes"] if c["senator"] == "musk"), None)
    if not musk_change:
        return False, f"expected musk position change, got: {bundle['position_changes']}"
    if musk_change["from_vote"] != "STOP" or musk_change["to_vote"] != "GO":
        return False, f"expected musk STOP→GO, got {musk_change}"
    if "wittgenstein" not in musk_change.get("trigger", ""):
        return False, f"expected trigger to mention wittgenstein cross-Q, got: {musk_change['trigger']}"
    if bundle["verdict"] != "GO":
        return False, f"expected GO (7/7 after position change), got {bundle['verdict']}"
    return True, "Round 1 STOP → Round 2 GO tracked + trigger inferred + final tally uses latest"


def test_cross_questions_law2_violation() -> tuple[bool, str]:
    """Senator emits 4 cross_questions in a single round → law_2_violation warning."""
    round1 = {
        "round": 1,
        "senators": {
            "wittgenstein": {
                "vote": "GO", "modify_request": "",
                "cross_questions": [
                    {"to": "musk", "question": "q1"},
                    {"to": "musk", "question": "q2"},
                    {"to": "socrate", "question": "q3"},
                    {"to": "dimon", "question": "q4"},  # exceeds max 3
                ],
            },
            "aurelius":  base_senator_output("GO"),
            "confucius": base_senator_output("GO"),
            "socrate":   base_senator_output("GO"),
            "musk":      base_senator_output("GO"),
            "dimon":     base_senator_output("GO"),
            "napoleon":  base_senator_output("GO"),
        },
    }
    code, bundle, stderr = run_synth(make_multi_round_payload(
        proposal="law2 violation test", rounds=[round1], label="smoke-law2"))
    guard = _require_bundle(code, bundle, stderr)
    if isinstance(guard, tuple):
        return guard
    bundle = guard
    if not any("law_2_violation" in w and "wittgenstein" in w for w in bundle["warnings"]):
        return False, f"expected law_2_violation warning for wittgenstein, got: {bundle['warnings']}"
    if bundle.get("cross_questions_used", {}).get("wittgenstein") != 4:
        return False, f"expected cross_questions_used.wittgenstein=4, got: {bundle.get('cross_questions_used')}"
    return True, "4 cross_questions in 1 round → law_2_violation surfaced + count tracked"


def test_blocaj_pending() -> tuple[bool, str]:
    """2 senators in GO×STOP opposition + no resolution → blocaj_pending warning."""
    round1 = {
        "round": 1,
        "senators": {
            "wittgenstein": base_senator_output("MODIFY", "x"),
            "aurelius":     base_senator_output("MODIFY", "y"),
            "confucius":    base_senator_output("MODIFY", "z"),
            "socrate":      base_senator_output("MODIFY", "w"),
            "musk":         base_senator_output("GO"),
            "dimon":        base_senator_output("STOP", "block"),
            "napoleon":     base_senator_output("MODIFY", "v"),
        },
    }
    code, bundle, stderr = run_synth(make_multi_round_payload(
        proposal="blocaj pending", rounds=[round1], label="smoke-blocaj-pend"))
    guard = _require_bundle(code, bundle, stderr)
    if isinstance(guard, tuple):
        return guard
    bundle = guard
    if not bundle.get("blocaj_pending"):
        return False, f"expected blocaj_pending populated, got: {bundle.get('blocaj_pending')}"
    pair = bundle["blocaj_pending"][0]
    if pair["go_senator"] != "musk" or pair["stop_senator"] != "dimon":
        return False, f"expected musk/dimon pair, got: {pair}"
    if not any("blocaj_pending" in w for w in bundle["warnings"]):
        return False, f"expected blocaj_pending warning, got: {bundle['warnings']}"
    return True, "GO×STOP pair without resolution → blocaj_pending + warning surfaced"


def test_blocaj_resolution_applied() -> tuple[bool, str]:
    """blocaj_resolution provided → loser's vote replaced by winner's, verdict adjusted."""
    round1 = {
        "round": 1,
        "senators": {
            "wittgenstein": base_senator_output("GO"),
            "aurelius":     base_senator_output("GO"),
            "confucius":    base_senator_output("GO"),
            "socrate":      base_senator_output("GO"),
            "musk":         base_senator_output("GO"),
            "dimon":        base_senator_output("STOP", "argue stop"),
            "napoleon":     base_senator_output("GO"),
        },
    }
    blocaj_resolution = {
        "pair": ["musk", "dimon"],
        "winning_senator": "musk",
        "votes_from_others": {
            "wittgenstein": "musk", "aurelius": "musk", "confucius": "musk",
            "socrate": "musk", "napoleon": "dimon",
        },
    }
    code, bundle, stderr = run_synth(make_multi_round_payload(
        proposal="blocaj resolution", rounds=[round1], label="smoke-blocaj-res",
        blocaj_resolution=blocaj_resolution))
    guard = _require_bundle(code, bundle, stderr)
    if isinstance(guard, tuple):
        return guard
    bundle = guard
    if "blocaj_resolution" not in bundle:
        return False, "expected blocaj_resolution in bundle, missing"
    if bundle["blocaj_resolution"]["losing_senator"] != "dimon":
        return False, f"expected losing_senator=dimon, got: {bundle['blocaj_resolution']}"
    if bundle["vote_counts"]["GO"] != 7 or bundle["vote_counts"]["STOP"] != 0:
        return False, f"expected GO=7 STOP=0 post-blocaj, got: {bundle['vote_counts']}"
    if bundle.get("vote_counts_pre_blocaj", {}).get("STOP") != 1:
        return False, f"expected pre-blocaj STOP=1, got: {bundle.get('vote_counts_pre_blocaj')}"
    if bundle["verdict"] != "GO":
        return False, f"expected GO post-blocaj, got: {bundle['verdict']}"
    # dimon's output should be preserved with override marker
    dimon_out = bundle["outputs"]["dimon"]
    if dimon_out.get("vote") != "GO" or "_blocaj_override" not in dimon_out:
        return False, f"expected dimon vote replaced with GO + _blocaj_override marker, got: {dimon_out}"
    return True, "blocaj resolution replaces loser's vote, verdict computed post-tiebreaker"


def test_deeply_split_4_3() -> tuple[bool, str]:
    """4 GO + 3 STOP (polarized, both factions >= POLARIZATION_THRESHOLD=3) → DEEPLY_SPLIT."""
    senators = {
        "wittgenstein": base_senator_output("GO"),
        "aurelius":     base_senator_output("GO"),
        "confucius":    base_senator_output("GO"),
        "socrate":      base_senator_output("GO"),
        "musk":         base_senator_output("STOP", "block A"),
        "dimon":        base_senator_output("STOP", "block B"),
        "napoleon":     base_senator_output("STOP", "block C"),
    }
    code, bundle, stderr = run_synth(make_payload(
        proposal="4-3 polarized smoke", senators=senators, label="smoke-deeply-split-4-3"))
    guard = _require_bundle(code, bundle, stderr)
    if isinstance(guard, tuple):
        return guard
    bundle = guard
    if bundle["verdict"] != "DEEPLY_SPLIT":
        return False, f"expected DEEPLY_SPLIT, got {bundle['verdict']} (counts {bundle['vote_counts']})"
    if not bundle.get("blocaj_pending"):
        return False, f"expected blocaj_pending populated for DEEPLY_SPLIT, got: {bundle.get('blocaj_pending')}"
    return True, "4 GO / 3 STOP -> DEEPLY_SPLIT + blocaj_pending surfaced"


def test_deeply_split_3_3_1() -> tuple[bool, str]:
    """3 GO + 3 STOP + 1 MODIFY (polarized with abstention) → DEEPLY_SPLIT."""
    senators = {
        "wittgenstein": base_senator_output("GO"),
        "aurelius":     base_senator_output("GO"),
        "confucius":    base_senator_output("GO"),
        "socrate":      base_senator_output("STOP", "block X"),
        "musk":         base_senator_output("STOP", "block Y"),
        "dimon":        base_senator_output("STOP", "block Z"),
        "napoleon":     base_senator_output("MODIFY", "tweak Q"),
    }
    code, bundle, stderr = run_synth(make_payload(
        proposal="3-3-1 polarized smoke", senators=senators, label="smoke-deeply-split-3-3-1"))
    guard = _require_bundle(code, bundle, stderr)
    if isinstance(guard, tuple):
        return guard
    bundle = guard
    if bundle["verdict"] != "DEEPLY_SPLIT":
        return False, f"expected DEEPLY_SPLIT, got {bundle['verdict']} (counts {bundle['vote_counts']})"
    if bundle["vote_counts"] != {"GO": 3, "MODIFY": 1, "STOP": 3}:
        return False, f"expected GO=3 MODIFY=1 STOP=3, got: {bundle['vote_counts']}"
    return True, "3 GO / 3 STOP / 1 MODIFY -> DEEPLY_SPLIT (MODIFY abstention does not break polarization)"


def test_deeply_split_3_4() -> tuple[bool, str]:
    """3 GO + 4 STOP (polarized inverse) → DEEPLY_SPLIT (not STOP — 4 < QUORUM=5)."""
    senators = {
        "wittgenstein": base_senator_output("GO"),
        "aurelius":     base_senator_output("GO"),
        "confucius":    base_senator_output("GO"),
        "socrate":      base_senator_output("STOP", "block A"),
        "musk":         base_senator_output("STOP", "block B"),
        "dimon":        base_senator_output("STOP", "block C"),
        "napoleon":     base_senator_output("STOP", "block D"),
    }
    code, bundle, stderr = run_synth(make_payload(
        proposal="3-4 polarized smoke", senators=senators, label="smoke-deeply-split-3-4"))
    guard = _require_bundle(code, bundle, stderr)
    if isinstance(guard, tuple):
        return guard
    bundle = guard
    if bundle["verdict"] != "DEEPLY_SPLIT":
        return False, f"expected DEEPLY_SPLIT, got {bundle['verdict']} (counts {bundle['vote_counts']})"
    return True, "3 GO / 4 STOP -> DEEPLY_SPLIT (STOP=4 < QUORUM=5, no majority)"


def test_negative_5_2_not_deeply_split() -> tuple[bool, str]:
    """5 GO + 2 STOP → GO (majority check runs before DEEPLY_SPLIT; STOP=2 < threshold=3)."""
    senators = {
        "wittgenstein": base_senator_output("GO"),
        "aurelius":     base_senator_output("GO"),
        "confucius":    base_senator_output("GO"),
        "socrate":      base_senator_output("GO"),
        "musk":         base_senator_output("GO"),
        "dimon":        base_senator_output("STOP", "block"),
        "napoleon":     base_senator_output("STOP", "block"),
    }
    code, bundle, stderr = run_synth(make_payload(
        proposal="5-2 majority smoke", senators=senators, label="smoke-not-split-5-2"))
    guard = _require_bundle(code, bundle, stderr)
    if isinstance(guard, tuple):
        return guard
    bundle = guard
    if bundle["verdict"] != "GO":
        return False, f"expected GO (5/7 majority), got {bundle['verdict']} (counts {bundle['vote_counts']})"
    return True, "5 GO / 2 STOP -> GO (majority wins, STOP below polarization threshold)"


def test_deeply_split_resolved_via_blocaj() -> tuple[bool, str]:
    """4-3 polarized + valid blocaj_resolution → GO, NOT DEEPLY_SPLIT (blocaj runs first)."""
    round1 = {
        "round": 1,
        "senators": {
            "wittgenstein": base_senator_output("GO"),
            "aurelius":     base_senator_output("GO"),
            "confucius":    base_senator_output("GO"),
            "socrate":      base_senator_output("GO"),
            "musk":         base_senator_output("STOP", "block A"),
            "dimon":        base_senator_output("STOP", "block B"),
            "napoleon":     base_senator_output("STOP", "block C"),
        },
    }
    # Blocaj pair: socrate (GO) vs musk (STOP) — 5 others vote, socrate wins
    blocaj_resolution = {
        "pair": ["socrate", "musk"],
        "winning_senator": "socrate",
        "votes_from_others": {
            "wittgenstein": "socrate", "aurelius": "socrate", "confucius": "socrate",
            "dimon": "musk", "napoleon": "musk",
        },
    }
    code, bundle, stderr = run_synth(make_multi_round_payload(
        proposal="4-3 + blocaj resolution smoke", rounds=[round1],
        label="smoke-deeply-split-blocaj", blocaj_resolution=blocaj_resolution))
    guard = _require_bundle(code, bundle, stderr)
    if isinstance(guard, tuple):
        return guard
    bundle = guard
    # After blocaj: musk's STOP becomes GO → counts {GO:5, STOP:2}
    if bundle["verdict"] != "GO":
        return False, f"expected GO post-blocaj (5/2), got {bundle['verdict']} (counts {bundle['vote_counts']})"
    if bundle.get("vote_counts_pre_blocaj", {}).get("GO") != 4:
        return False, f"expected pre-blocaj GO=4, got: {bundle.get('vote_counts_pre_blocaj')}"
    return True, "4-3 + blocaj (musk→socrate) -> GO 5/2, DEEPLY_SPLIT bypassed"



def test_collision_safe_write() -> tuple[bool, str]:
    """Forcing same-timestamp collision: pre-write a stub at the path the next
    synth invocation will try to use, then verify synth produces a `_v2`
    suffixed file rather than overwriting the stub.
    """
    import datetime as _dt
    label = "smoke-collision"
    ts_now = _dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    stub_path = RUNS_DIR / f"{ts_now}-{label}.json"
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    stub_path.write_text('{"stub": true}', encoding="utf-8")
    code, _, stderr = run_synth(
        make_payload("collision smoke", all_voting("GO"), label=label)
    )
    if code != 0:
        return False, f"synth exit={code}, stderr={stderr.strip()[:200]}"
    # Stub must still be intact
    if json.loads(stub_path.read_text(encoding="utf-8")) != {"stub": True}:
        return False, "stub at expected timestamp path was overwritten"
    # A _vN suffixed file must exist for the synth run
    suffixed = sorted(RUNS_DIR.glob(f"*{label}*_v*.json"))
    if not suffixed:
        return False, f"expected _vN suffixed file for label={label}, found none"
    return True, f"collision-safe: stub preserved, synth wrote {suffixed[-1].name}"


# ─────────────────────── runner ────────────────────────


TEST_GROUPS = [
    ("Smoke", [
        ("prompts_consistent",          test_prompts_are_consistent),
        ("fixture_smoke",               test_fixture_smoke),
    ]),
    ("Verdicts", [
        ("verdict_go_unanimous",        test_verdict_go_unanimous),
        ("verdict_go_quorum",           test_verdict_go_quorum),
        ("verdict_modify_default",      test_verdict_modify_default),
        ("verdict_unreachable",         test_verdict_unreachable),
        ("unrecognized_vote",           test_unrecognized_vote_warns_and_counts_modify),
    ]),
    ("Laws 2-4 (multi-round)", [
        ("multi_round_position_change", test_multi_round_position_change),
        ("cross_questions_law2",        test_cross_questions_law2_violation),
        ("blocaj_pending",              test_blocaj_pending),
        ("blocaj_resolution_applied",   test_blocaj_resolution_applied),
    ]),
    ("DEEPLY_SPLIT (Phase 1)", [
        ("deeply_split_4_3",            test_deeply_split_4_3),
        ("deeply_split_3_3_1",          test_deeply_split_3_3_1),
        ("deeply_split_3_4",            test_deeply_split_3_4),
        ("negative_5_2_not_split",      test_negative_5_2_not_deeply_split),
        ("deeply_split_blocaj_bypass",  test_deeply_split_resolved_via_blocaj),
    ]),
    ("Compat & persistence", [
        ("bundle_persisted",            test_bundle_persisted_and_valid_json),
        ("collision_safe_write",        test_collision_safe_write),
    ]),
]


def cleanup_smoke_runs() -> int:
    """Remove transient *-smoke-*.json bundles produced by these tests."""
    n = 0
    for f in RUNS_DIR.glob("*-smoke-*.json"):
        try:
            f.unlink()
            n += 1
        except OSError:
            pass
    for f in RUNS_DIR.glob("*-fixture-smoke*.json"):
        try:
            f.unlink()
            n += 1
        except OSError:
            pass
    return n


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--verbose", action="store_true", help="Print detailed messages on failure.")
    parser.add_argument("--keep", action="store_true", help="Keep generated smoke run files in runs/senate/.")
    args = parser.parse_args()

    failures = 0
    total = 0
    for group_name, tests in TEST_GROUPS:
        print(f"\n── {group_name} {'─' * max(0, 38 - len(group_name))}")
        for name, fn in tests:
            total += 1
            try:
                ok, message = fn()
            except Exception as exc:
                ok, message = False, f"EXCEPTION: {type(exc).__name__}: {exc}"
            symbol = "PASS" if ok else "FAIL"
            print(f"  [{symbol}] {name}: {message}")
            if not ok:
                failures += 1

    if not args.keep:
        removed = cleanup_smoke_runs()
        if args.verbose:
            print(f"\ncleanup: removed {removed} smoke run file(s)")

    print(f"\n{total - failures}/{total} passed")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
