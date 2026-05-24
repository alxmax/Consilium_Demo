"""Smoke test for recommend_implement_mode (Step 7 routing gate).

Run: python scripts/test_implement_mode.py   (exit 0 = all pass, 1 = a failure)

Gate contract: pipeline iff the change warrants a `review` step (regression-prone
quadrants); single_shot otherwise. Keyed on reversibility/magnitude, NOT size.
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from infer_pipeline import recommend_implement_mode  # noqa: E402


def _report(magnitude: str, reversibility: str, chosen: str = "approach_x") -> dict:
    return {
        "chosen_approach": chosen,
        "deliberation_log": [
            {"step": "conservator", "scores": [
                {"id": chosen, "regression_risk": {"magnitude": magnitude, "reversibility": reversibility}}
            ]}
        ],
    }


CASES = [
    # (magnitude, reversibility, expected_mode)
    ("trivial",  "complete",     "single_shot"),
    ("moderate", "complete",     "single_shot"),
    ("moderate", "partial",      "single_shot"),   # no review in table
    ("moderate", "irreversible", "pipeline"),
    ("high",     "complete",     "single_shot"),   # big but fully reversible -> no regression to catch
    ("high",     "partial",      "pipeline"),
    ("high",     "irreversible", "pipeline"),
    ("critical", "complete",     "pipeline"),
]


def main() -> int:
    passed = failed = 0
    for mag, rev, expected in CASES:
        got = recommend_implement_mode(_report(mag, rev))
        ok = got == expected
        passed += ok
        failed += not ok
        print(f"  {'PASS' if ok else 'FAIL'}  ({mag},{rev}) -> {got} (expected {expected})")

    # do_nothing / skipped -> single_shot (no implementation to route)
    for chosen in ("do_nothing", "skipped"):
        got = recommend_implement_mode({"chosen_approach": chosen})
        ok = got == "single_shot"
        passed += ok
        failed += not ok
        print(f"  {'PASS' if ok else 'FAIL'}  chosen={chosen} -> {got} (expected single_shot)")

    print(f"\n{passed}/{passed + failed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
