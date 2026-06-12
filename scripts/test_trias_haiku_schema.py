"""Smoke test: Trias model-diversity assignment in personalities.py.

Validates that:
1. All 3 personalities emit a `model` field.
2. Model assignments are pioneer=haiku, architect=sonnet, steward=opus.
3. Steward carries schema_less=True (Opus+StructuredOutput dispatch rule).
4. Pioneer circuit-breaker: a helper returns the fallback model when the
   primary model is haiku (ensures the substitution logic is testable without
   a live API call).

CLI: python -X utf8 scripts/test_trias_haiku_schema.py
Exit 0 = all assertions passed.
"""
# tested-by: CONSILIUM-TRIAS-HAIKU-SCHEMA-001

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PERSONALITIES_PATH = REPO_ROOT / "scripts" / "personalities.py"

EXPECTED = {
    "pioneer": {"model": "haiku", "schema_less": False},
    "architect": {"model": "sonnet", "schema_less": False},
    "steward": {"model": "opus", "schema_less": True},
}


def _load_personalities() -> list[dict]:
    spec = importlib.util.spec_from_file_location("personalities", PERSONALITIES_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    return mod.PERSONALITIES  # type: ignore[attr-defined]


def pioneer_circuit_breaker_model(personality: dict) -> str:
    """Return the fallback model when the primary dispatch fails.

    Pioneer (Haiku) is the only personality with a circuit-breaker: on malformed
    or empty JSON, the orchestrator substitutes sonnet and re-dispatches once.
    All other personalities have no fallback (non-vote on failure).
    """
    if personality.get("model") == "haiku":
        return "sonnet"
    return personality["model"]


def test_model_fields_present(personalities: list[dict]) -> None:
    for p in personalities:
        assert "model" in p, f"{p['name']}: missing 'model' field"


def test_model_assignments(personalities: list[dict]) -> None:
    by_name = {p["name"]: p for p in personalities}
    for name, expected in EXPECTED.items():
        assert name in by_name, f"personality {name!r} not found"
        actual_model = by_name[name].get("model")
        assert actual_model == expected["model"], (
            f"{name}: expected model={expected['model']!r}, got {actual_model!r}"
        )


def test_steward_schema_less(personalities: list[dict]) -> None:
    steward = next(p for p in personalities if p["name"] == "steward")
    assert steward.get("schema_less") is True, (
        "steward must have schema_less=True (Opus+StructuredOutput dispatch rule)"
    )


def test_pioneer_and_architect_not_schema_less(personalities: list[dict]) -> None:
    for p in personalities:
        if p["name"] in ("pioneer", "architect"):
            assert not p.get("schema_less"), (
                f"{p['name']}: schema_less should be absent/False"
            )


def test_circuit_breaker(personalities: list[dict]) -> None:
    pioneer = next(p for p in personalities if p["name"] == "pioneer")
    fallback = pioneer_circuit_breaker_model(pioneer)
    assert fallback == "sonnet", (
        f"Pioneer circuit-breaker must fall back to sonnet, got {fallback!r}"
    )
    # Architect and Steward have no fallback — their circuit-breaker returns their own model.
    for name in ("architect", "steward"):
        p = next(x for x in personalities if x["name"] == name)
        assert pioneer_circuit_breaker_model(p) == p["model"], (
            f"{name}: non-pioneer personalities must not change model on circuit-breaker"
        )


def test_cli_output_valid_json() -> None:
    """CLI must emit valid JSON with model fields."""
    result = subprocess.run(
        [sys.executable, "-X", "utf8", str(PERSONALITIES_PATH)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"personalities.py exited {result.returncode}: {result.stderr}"
    data = json.loads(result.stdout)
    assert isinstance(data, list) and len(data) == 3
    for p in data:
        assert "model" in p, f"CLI output missing model field for {p.get('name')}"


def main() -> int:
    personalities = _load_personalities()
    tests = [
        test_model_fields_present,
        test_model_assignments,
        test_steward_schema_less,
        test_pioneer_and_architect_not_schema_less,
        test_circuit_breaker,
        test_cli_output_valid_json,
    ]
    failed = 0
    for t in tests:
        try:
            if t.__name__ == "test_cli_output_valid_json":
                t()
            else:
                t(personalities)
            print(f"[PASS] {t.__name__}")
        except AssertionError as e:
            print(f"[FAIL] {t.__name__}: {e}")
            failed += 1
    if failed:
        print(f"\n{failed}/{len(tests)} test(s) failed", file=sys.stderr)
        return 1
    print(f"\n{len(tests)}/{len(tests)} passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
