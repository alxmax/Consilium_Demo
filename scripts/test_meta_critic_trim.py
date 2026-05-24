"""Behavioral tests for the trimmed meta_critic.py.

Covers: conservator_spread metric, flags, absent removed metrics,
optional metrics (personalities_divergence, control_speculation).

Run:
    python scripts/test_meta_critic_trim.py
"""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from meta_critic import critique, conservator_spread

PASS = 0
FAIL = 0


def check(name: str, condition: bool) -> None:
    global PASS, FAIL
    if condition:
        print(f"  PASS  {name}")
        PASS += 1
    else:
        print(f"  FAIL  {name}")
        FAIL += 1


def _bundle_with_scores(scores: list[float]) -> dict:
    return {
        "conservator": {
            "scores": [{"id": f"c{i}", "risk_score": s} for i, s in enumerate(scores)]
        },
        "control": {"verdicts": []},
    }


def test_clustered_scores() -> None:
    """critique() on clustered scores → conservator_spread present + shrug flag; no removed keys."""
    bundle = _bundle_with_scores([0.5, 0.5, 0.5])
    result = critique(bundle)
    dq = result["deliberation_quality"]

    check("clustered: deliberation_quality has conservator_spread", "conservator_spread" in dq)
    check("clustered: conservator_spread == 0.0 (identical scores)", dq.get("conservator_spread") == 0.0)
    flags = dq.get("flags", [])
    flag_text = " ".join(flags)
    check("clustered: flags mention conservator_spread", any("conservator_spread" in f for f in flags))
    check("clustered: shrug severity mentioned", "shrug" in flag_text)
    check("clustered: no generator_divergence key", "generator_divergence" not in dq)
    check("clustered: no control_concreteness key", "control_concreteness" not in dq)


def test_well_spread_scores() -> None:
    """critique() on well-spread scores → conservator_spread present, no shrug flag."""
    bundle = _bundle_with_scores([0.1, 0.9])
    result = critique(bundle)
    dq = result["deliberation_quality"]

    check("spread: conservator_spread present", "conservator_spread" in dq)
    cs = dq.get("conservator_spread", 0.0)
    check("spread: conservator_spread > 0.2 (healthy)", cs > 0.2)
    flags = dq.get("flags", [])
    check("spread: no conservator_spread flag", not any("conservator_spread" in f for f in flags))


def test_single_candidate_spread() -> None:
    """conservator_spread([single]) == 0.0."""
    result = conservator_spread([{"id": "x", "risk_score": 0.7}])
    check("single candidate: spread == 0.0", result == 0.0)


def test_trias_personalities_divergence() -> None:
    """Optional metric personalities_divergence is present for trias team with all-same chosen."""
    bundle = {
        "team": "trias",
        "members": {
            "pioneer": {"chosen": "A"},
            "architect": {"chosen": "A"},
            "steward": {"chosen": "A"},
        },
        "conservator": {
            "scores": [{"id": "A", "risk_score": 0.4}, {"id": "B", "risk_score": 0.6}]
        },
        "control": {"verdicts": []},
    }
    result = critique(bundle)
    dq = result["deliberation_quality"]

    check("trias: personalities_divergence key present", "personalities_divergence" in dq)
    check("trias: personalities_divergence == 0.0", dq.get("personalities_divergence") == 0.0)
    flags = dq.get("flags", [])
    check("trias: personalities_divergence flag emitted", any("personalities_divergence" in f for f in flags))


def test_control_speculation() -> None:
    """control_speculation: verdict {valid:true, confidence_in_verdict:'low'} → metric >= 1."""
    bundle = {
        "conservator": {
            "scores": [{"id": "A", "risk_score": 0.3}, {"id": "B", "risk_score": 0.7}]
        },
        "control": {
            "verdicts": [
                {"id": "A", "valid": True, "confidence_in_verdict": "low"},
            ]
        },
    }
    result = critique(bundle)
    dq = result["deliberation_quality"]

    check("speculation: control_speculation key present", "control_speculation" in dq)
    check("speculation: control_speculation >= 1", dq.get("control_speculation", 0) >= 1)
    flags = dq.get("flags", [])
    check("speculation: control_speculation flag emitted", any("control_speculation" in f for f in flags))


def main() -> None:
    global PASS, FAIL
    print("=== test_meta_critic_trim ===")
    test_clustered_scores()
    test_well_spread_scores()
    test_single_candidate_spread()
    test_trias_personalities_divergence()
    test_control_speculation()
    print(f"\n{PASS} passed, {FAIL} failed")
    if FAIL:
        sys.exit(1)


if __name__ == "__main__":
    main()
