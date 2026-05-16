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
        "senators": senators,
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


TESTS = [
    ("prompts_consistent",           test_prompts_are_consistent),
    ("fixture_smoke",                test_fixture_smoke),
    ("verdict_go_unanimous",         test_verdict_go_unanimous),
    ("verdict_go_quorum",            test_verdict_go_quorum),
    ("verdict_modify_default",       test_verdict_modify_default),
    ("verdict_unreachable",          test_verdict_unreachable),
    ("unrecognized_vote",            test_unrecognized_vote_warns_and_counts_modify),
    ("bundle_persisted",             test_bundle_persisted_and_valid_json),
    ("collision_safe_write",         test_collision_safe_write),
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
    for name, fn in TESTS:
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

    print(f"\n{len(TESTS) - failures}/{len(TESTS)} passed")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
