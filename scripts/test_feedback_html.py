"""Standalone tests for render_feedback_html + feedback.py HTML parser.

Run: python scripts/test_feedback_html.py
Exit 0 = all pass; exit 1 = one or more failures (all tests run; failures listed).
"""
# tested-by: CONSILIUM-RENDER-FEEDBACK-HTML-001
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import render_feedback_html as rfh  # noqa: E402


def test_render_empty_entries_produces_skeleton():
    html = rfh.render(entries=[], runs_dir=ROOT / "runs")
    assert "<!doctype html>" in html
    assert "Consilium feedback" in html
    assert "<tbody>" in html and "</tbody>" in html
    assert "0 entries" in html


def test_render_single_legacy_entry_no_drill():
    e = rfh.Entry(
        date="2026-05-11",
        context="audit-reduction",
        chosen="nuke_orphans_and_stale_readme",
        outcome="PEND",
        note="5 cand, conf=0.63",
        run_path=None,
    )
    html_out = rfh.render([e], runs_dir=ROOT / "runs")
    assert "1 entries" in html_out
    assert "2026-05-11" in html_out
    assert "nuke_orphans_and_stale_readme" in html_out
    assert "PEND" in html_out
    assert 'class="outcome PEND"' in html_out
    assert "no detailed run data" in html_out
    assert 'class="entry"' in html_out
    assert 'class="drill"' in html_out


def test_render_escapes_html_in_user_text():
    e = rfh.Entry(
        date="2026-05-11",
        context="<script>alert(1)</script>",
        chosen="x",
        outcome="OK",
        note="& \"quoted\"",
        run_path=None,
    )
    html_out = rfh.render([e], runs_dir=ROOT / "runs")
    assert "<script>alert(1)</script>" not in html_out
    assert "&lt;script&gt;" in html_out
    assert "&amp;" in html_out


def test_render_drill_from_real_run_file():
    # Use a synthetic run JSON in a temp directory so the test has no dependency
    # on any tracked file in runs/.
    synthetic_run = {
        "success_criterion": "Click pe sageata Rerun din topbar",
        "chosen_approach": "disable_when_unreachable",
        "confidence": 0.62,
        "deliberation_log": [
            {
                "step": "generator",
                "candidates": [
                    {"id": "do_nothing", "summary": "Accept current state.", "sketch": "Baseline."},
                    {"id": "disable_when_unreachable", "summary": "Probe disables Rerun.", "sketch": "~20 lines."},
                    {"id": "adversarial_url_protocol_handler", "summary": "Register protocol.", "sketch": "Stress test."},
                ],
            },
            {
                "step": "control",
                "verdicts": [
                    {"id": "do_nothing", "valid": True, "issues": [], "tests_to_write": []},
                    {
                        "id": "disable_when_unreachable",
                        "valid": True,
                        "issues": [],
                        "tests_to_write": [
                            {"name": "probe_success_enables", "assert": "200 -> opacity=1"},
                        ],
                    },
                    {
                        "id": "adversarial_url_protocol_handler",
                        "valid": False,
                        "issues": [{"category": "logic", "detail": "Registry irreversible."}],
                        "tests_to_write": [],
                    },
                ],
            },
            {
                "step": "conservator",
                "scores": [
                    {
                        "id": "disable_when_unreachable",
                        "risk_score": 0.14,
                        "factors": {"diff_size": 0.1, "scope_drift": 0.05, "regression_risk": 0.1, "reversibility": 0.2},
                    },
                ],
            },
            {
                "step": "aggregate",
                "result": {"vetoed": []},
            },
        ],
    }
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        runs_subdir = td_path / "runs"
        runs_subdir.mkdir()
        run_file = runs_subdir / "synthetic_run.json"
        run_file.write_text(json.dumps(synthetic_run), encoding="utf-8")

        e = rfh.Entry(
            date="2026-05-11",
            context="Click pe sageata Rerun din topbar",
            chosen="disable_when_unreachable",
            outcome="PEND",
            note="3 cand, 0 vetoed, conf=0.62",
            run_path="runs/synthetic_run.json",
        )
        html_out = rfh.render([e], runs_dir=runs_subdir)

    # Generator section
    assert "Generator" in html_out
    assert "do_nothing" in html_out
    assert "disable_when_unreachable" in html_out
    # CHOSEN badge on the picked candidate
    assert "CHOSEN" in html_out
    # Control section: valid/invalid badges
    assert ">valid<" in html_out
    assert ">invalid<" in html_out
    # Tests rendered
    assert "probe_success_enables" in html_out
    # Conservator section: factor breakdown
    assert "diff:" in html_out
    assert "scope:" in html_out
    assert "0.14" in html_out  # disable_when_unreachable risk_score
    assert "no detailed run data" not in html_out


def test_render_drill_tolerates_string_issues():
    # Regression: 2026-06-10 — a run with control issues/tests_to_write as bare
    # strings (not dicts) crashed _ctrl_panel with AttributeError and blocked
    # every subsequent log_feedback append. Found when a BOM-corrupted run was
    # repaired and its drill-down rendered for the first time.
    synthetic_run = {
        "success_criterion": "x",
        "chosen_approach": "a",
        "confidence": 0.5,
        "deliberation_log": [
            {
                "step": "control",
                "verdicts": [
                    {
                        "id": "a",
                        "valid": False,
                        "issues": ["plain string issue"],
                        "tests_to_write": ["plain string test"],
                    },
                ],
            },
        ],
    }
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        runs_subdir = td_path / "runs"
        runs_subdir.mkdir()
        (runs_subdir / "string_issues.json").write_text(
            json.dumps(synthetic_run), encoding="utf-8"
        )
        e = rfh.Entry(
            date="2026-06-10",
            context="x",
            chosen="a",
            outcome="PEND",
            note="",
            run_path="runs/string_issues.json",
        )
        html_out = rfh.render([e], runs_dir=runs_subdir)
    assert "plain string issue" in html_out
    assert "plain string test" in html_out


def test_render_drill_missing_run_file_falls_back_to_stub():
    e = rfh.Entry(
        date="2026-05-11",
        context="x",
        chosen="y",
        outcome="PEND",
        note="",
        run_path="runs/does_not_exist.json",
    )
    html_out = rfh.render([e], runs_dir=ROOT / "runs")
    assert "no detailed run data" in html_out


def test_parse_feedback_roundtrip_html():
    # Build entries, render to HTML, parse back, expect same fields.
    sys.path.insert(0, str(ROOT / "scripts"))
    import feedback  # noqa: E402

    original = [
        rfh.Entry(date="2026-05-11", context="ctx one", chosen="approach_a",
                  outcome="OK", note="5 cand, conf=0.65"),
        rfh.Entry(date="2026-05-12", context="ctx <two> & special",
                  chosen="approach_b", outcome="OVR",
                  note="override=alt; conf=0.43"),
    ]
    html_out = rfh.render(original, runs_dir=ROOT / "runs")

    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html_out)
        tmp_path = Path(f.name)
    try:
        parsed = feedback.parse_feedback(tmp_path)
    finally:
        tmp_path.unlink()

    assert len(parsed) == 2, f"got {len(parsed)} entries, want 2"
    assert parsed[0]["date"] == "2026-05-11"
    assert parsed[0]["context"] == "ctx one"
    assert parsed[0]["chosen"] == "approach_a"
    assert parsed[0]["outcome"] == "OK"
    assert "5 cand" in parsed[0]["note"]
    assert parsed[1]["context"] == "ctx <two> & special"  # unescaped on parse
    assert parsed[1]["outcome"] == "OVR"


def test_parse_feedback_returns_empty_for_missing_file():
    sys.path.insert(0, str(ROOT / "scripts"))
    import feedback  # noqa: E402
    assert feedback.parse_feedback(Path("/nonexistent/FEEDBACK.html")) == []


def test_log_feedback_appends_html_entry():
    import subprocess
    sys.path.insert(0, str(ROOT / "scripts"))
    import feedback  # noqa: E402

    with tempfile.TemporaryDirectory() as td:
        feedback_path = Path(td) / "FEEDBACK.html"
        # Pre-populate with one entry via render.
        e0 = rfh.Entry(date="2026-05-01", context="pre", chosen="x",
                       outcome="OK", note="seed")
        feedback_path.write_text(rfh.render([e0], runs_dir=ROOT / "runs"), encoding="utf-8")

        report = {
            "success_criterion": "fix the test",
            "chosen_approach": "approach_a",
            "confidence": 0.81,
            "telemetry": {"mode": "parallel"},
            "deliberation_log": [{"step": "generator", "candidates": [{"id": "a"}, {"id": "b"}]}],
        }
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "log_feedback.py"),
             "--feedback", str(feedback_path),
             "--outcome", "OK"],
            input=json.dumps(report).encode("utf-8"),
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, f"stderr: {result.stderr.decode()}"

        parsed = feedback.parse_feedback(feedback_path)
        assert len(parsed) == 2, f"expected 2 entries (1 seed + 1 appended), got {len(parsed)}"
        assert parsed[1]["chosen"] == "approach_a"
        assert parsed[1]["outcome"] == "OK"


def test_log_feedback_dedup_skips_duplicate():
    """Appending the same entry twice must not create a duplicate row."""
    import subprocess
    sys.path.insert(0, str(ROOT / "scripts"))
    import feedback  # noqa: E402

    report = {
        "success_criterion": "dedup test",
        "chosen_approach": "approach_x",
        "confidence": 0.85,
        "telemetry": {"mode": "sequential"},
        "deliberation_log": [],
    }
    with tempfile.TemporaryDirectory() as td:
        feedback_path = Path(td) / "FEEDBACK.html"
        common_args = [
            sys.executable, str(ROOT / "scripts" / "log_feedback.py"),
            "--feedback", str(feedback_path),
            "--outcome", "OK",
            "--force-override",
        ]
        input_bytes = json.dumps(report).encode("utf-8")
        r1 = subprocess.run(common_args, input=input_bytes, capture_output=True, check=False)
        assert r1.returncode == 0, f"first append failed: {r1.stderr.decode()}"
        r2 = subprocess.run(common_args, input=input_bytes, capture_output=True, check=False)
        # Second call should exit 3 (duplicate) not 0.
        assert r2.returncode == 3, f"expected exit 3 (duplicate), got {r2.returncode}"
        parsed = feedback.parse_feedback(feedback_path)
        assert len(parsed) == 1, f"expected 1 row after dedup, got {len(parsed)}"


def test_log_feedback_upgrades_pend_in_place():
    """A second log with the same --run-path but a different outcome upgrades the
    existing row in place (close-the-loop), instead of skipping it as a duplicate."""
    import subprocess
    sys.path.insert(0, str(ROOT / "scripts"))
    import feedback  # noqa: E402

    report = {
        "success_criterion": "close-the-loop test",
        "chosen_approach": "approach_y",
        "confidence": 0.62,
        "telemetry": {"mode": "sequential"},
        "deliberation_log": [],
    }
    with tempfile.TemporaryDirectory() as td:
        feedback_path = Path(td) / "FEEDBACK.html"
        (Path(td) / "runs").mkdir()
        base = [
            sys.executable, str(ROOT / "scripts" / "log_feedback.py"),
            "--feedback", str(feedback_path),
            "--run-path", "runs/loop.json",
        ]
        inp = json.dumps(report).encode("utf-8")
        r1 = subprocess.run(base + ["--outcome", "PEND_HEADLESS"], input=inp, capture_output=True, check=False)
        assert r1.returncode == 0, f"first log failed: {r1.stderr.decode()}"
        # Same run, same outcome -> duplicate skip (exit 3).
        r2 = subprocess.run(base + ["--outcome", "PEND_HEADLESS"], input=inp, capture_output=True, check=False)
        assert r2.returncode == 3, f"expected exit 3 (duplicate), got {r2.returncode}"
        # Same run, NEW outcome -> upgrade in place (exit 0, no new row).
        r3 = subprocess.run(base + ["--outcome", "OK", "--force-override"], input=inp, capture_output=True, check=False)
        assert r3.returncode == 0, f"in-place upgrade failed: {r3.stderr.decode()}"
        parsed = feedback.parse_feedback(feedback_path)
        assert len(parsed) == 1, f"expected 1 row after in-place upgrade, got {len(parsed)}"
        assert parsed[0]["outcome"] == "OK", f"expected OK after upgrade, got {parsed[0]['outcome']}"


def test_mark_outcome_happy_path():
    """mark_outcome updates outcome and annotates note on a matched row."""
    import subprocess
    sys.path.insert(0, str(ROOT / "scripts"))
    import feedback  # noqa: E402

    with tempfile.TemporaryDirectory() as td:
        feedback_path = Path(td) / "FEEDBACK.html"
        e = rfh.Entry(date="2026-05-20", context="mark-test", chosen="approach_z",
                      outcome="PEND", note="5 cand, conf=0.75")
        feedback_path.write_text(rfh.render([e], runs_dir=Path(td) / "runs"), encoding="utf-8")

        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "mark_outcome.py"),
             "--feedback", str(feedback_path),
             "--date", "2026-05-20",
             "--chosen", "approach_z",
             "--outcome", "BAD",
             "--reason", "broke prod"],
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, f"stderr: {result.stderr.decode()}"
        parsed = feedback.parse_feedback(feedback_path)
        assert len(parsed) == 1
        assert parsed[0]["outcome"] == "BAD"
        assert "outcome_reason=broke prod" in parsed[0]["note"]
        assert "[confirmed]" in parsed[0]["note"]


def _run_tests():
    funcs = [v for k, v in globals().items() if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in funcs:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {fn.__name__}: {e}")
        except Exception as e:
            failed += 1
            print(f"ERROR {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(funcs) - failed}/{len(funcs)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_run_tests())
