"""Standalone tests for render_feedback_html + feedback.py HTML parser.

Run: python scripts/test_feedback_html.py
Exit 0 = all pass; exit 1 = first failure with traceback.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import render_feedback_html as rfh  # noqa: E402


def test_render_empty_entries_produces_skeleton():
    html = rfh.render(entries=[], runs_dir=ROOT / "runs")
    assert "<!doctype html>" in html
    assert "max-agent feedback" in html
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
