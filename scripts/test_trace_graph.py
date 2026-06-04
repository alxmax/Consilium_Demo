"""Tests for trace_graph.py pure Mermaid-generation functions.

Covers _esc (string escaping) and build_mermaid (flowchart assembly
from a deliberation report dict).

Run:
    python scripts/test_trace_graph.py
    python -m pytest scripts/test_trace_graph.py -v  (if pytest available)
"""
# tested-by: CONSILIUM-TRACE-GRAPH-001
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from trace_graph import _esc, build_mermaid


class TestEsc(unittest.TestCase):
    def test_quotes_to_apostrophes(self):
        self.assertEqual(_esc('say "hello"'), "say 'hello'")

    def test_newlines_to_spaces(self):
        self.assertEqual(_esc("line1\nline2"), "line1 line2")

    def test_strips_whitespace(self):
        self.assertEqual(_esc("  text  "), "text")

    def test_non_string_coerced(self):
        self.assertEqual(_esc(123), "123")

    def test_empty_string(self):
        self.assertEqual(_esc(""), "")

    def test_combined(self):
        self.assertEqual(_esc('  "quote"\nand newline  '), "'quote' and newline")


class TestBuildMermaid(unittest.TestCase):
    def test_output_is_flowchart(self):
        report = {"telemetry": {"mode": "sequential"}, "deliberation_log": []}
        result = build_mermaid(report)
        self.assertIn("flowchart", result)

    def test_skipped_report(self):
        report = {
            "skipped": True,
            "skip_reason": "test skip",
            "telemetry": {"mode": "sequential"},
        }
        result = build_mermaid(report)
        self.assertIn("SKIP", result)

    def test_sequential_includes_voice_nodes(self):
        report = {
            "telemetry": {"mode": "sequential"},
            "deliberation_log": [
                {"step": "conservator", "result": {}},
                {"step": "generator", "result": {}},
                {"step": "control", "result": {}},
                {"step": "aggregate", "result": {}},
            ],
            "chosen_approach": "A",
        }
        result = build_mermaid(report)
        self.assertIn("GEN", result)
        self.assertIn("CON", result)

    def test_trias_includes_personality_nodes(self):
        report = {
            "telemetry": {"mode": "trias"},
            "deliberation_log": [],
            "chosen_approach": "A",
        }
        result = build_mermaid(report)
        self.assertIn("PIO", result)
        self.assertIn("ARC", result)
        self.assertIn("STE", result)

    def test_confidence_node_when_numeric(self):
        report = {
            "telemetry": {"mode": "sequential"},
            "deliberation_log": [{"step": "aggregate", "result": {}}],
            "chosen_approach": "A",
            "confidence": 0.85,
        }
        result = build_mermaid(report)
        self.assertIn("0.85", result)

    def test_confidence_omitted_when_none(self):
        report = {
            "telemetry": {"mode": "sequential"},
            "deliberation_log": [{"step": "aggregate", "result": {}}],
            "chosen_approach": "A",
            "confidence": None,
        }
        result = build_mermaid(report)
        self.assertNotIn("CONF", result)

    def test_empty_report_does_not_crash(self):
        result = build_mermaid({})
        self.assertIn("flowchart", result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
