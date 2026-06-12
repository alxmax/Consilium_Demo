"""Tests for retry_context.py pure functions.

Covers _utility (score-to-utility conversion), _scores_for (per-candidate
voice score lookup), extract_targets (file/symbol extraction from candidate
text), _grep_patterns (regex generation), and plan_retry (retry decision logic).

Run:
    python scripts/test_retry_context.py
    python -m pytest scripts/test_retry_context.py -v  (if pytest available)
"""
# tested-by: CONSILIUM-RETRY-CONTEXT-001
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from retry_context import _utility, _scores_for, extract_targets, _grep_patterns, plan_retry


class TestUtility(unittest.TestCase):
    def test_all_zeros_gives_mid_utility(self):
        scores = {"generator": 0.0, "control": 0.0, "conservator": 0.0}
        result = _utility(scores)
        # conservator=0 → safety=1.0, so average > 0
        self.assertGreater(result, 0.0)

    def test_perfect_scores_not_maximum(self):
        # gen=1, ctrl=1, cons=1 → safety=0, so lower utility
        scores = {"generator": 1.0, "control": 1.0, "conservator": 1.0}
        result = _utility(scores)
        self.assertGreaterEqual(result, 0.0)
        self.assertLessEqual(result, 1.0)

    def test_low_risk_high_quality_high_utility(self):
        good = {"generator": 0.9, "control": 0.9, "conservator": 0.1}
        bad = {"generator": 0.9, "control": 0.9, "conservator": 0.9}
        self.assertGreater(_utility(good), _utility(bad))


class TestScoresFor(unittest.TestCase):
    def test_valid_candidate_control_score_1(self):
        control = [{"id": "A", "valid": True, "issues": []}]
        conservator = [{"id": "A", "regression_risk": {"net_concern": 0.3}}]
        scores = _scores_for("A", control, conservator)
        self.assertEqual(scores["control"], 1.0)
        self.assertAlmostEqual(scores["conservator"], 0.3)

    def test_invalid_candidate_control_score_0(self):
        control = [{"id": "A", "valid": False, "issues": []}]
        conservator = [{"id": "A"}]
        scores = _scores_for("A", control, conservator)
        self.assertEqual(scores["control"], 0.0)

    def test_missing_candidate_defaults(self):
        scores = _scores_for("missing", [], [])
        self.assertIn("generator", scores)
        self.assertIn("control", scores)
        self.assertIn("conservator", scores)

    def test_do_nothing_generator_penalty(self):
        control = [{"id": "do_nothing", "valid": True, "issues": []}]
        conservator = [{"id": "do_nothing"}]
        scores = _scores_for("do_nothing", control, conservator)
        self.assertEqual(scores["generator"], 0.5)

    def test_normal_candidate_generator_1(self):
        control = [{"id": "A", "valid": True, "issues": []}]
        conservator = [{"id": "A"}]
        scores = _scores_for("A", control, conservator)
        self.assertEqual(scores["generator"], 1.0)


class TestExtractTargets(unittest.TestCase):
    def test_extracts_file_paths(self):
        candidate = {"summary": "scripts/foo.py", "sketch": ""}
        result = extract_targets(candidate)
        self.assertIn("scripts/foo.py", result["files"])

    def test_extracts_function_calls(self):
        candidate = {"summary": "", "sketch": "bar() and baz()"}
        result = extract_targets(candidate)
        self.assertIn("bar", result["symbols"])
        self.assertIn("baz", result["symbols"])

    def test_extracts_backtick_quoted(self):
        candidate = {"summary": "use `myFunction` here", "sketch": ""}
        result = extract_targets(candidate)
        self.assertIn("myFunction", result["symbols"])

    def test_empty_candidate(self):
        candidate = {"summary": "", "sketch": ""}
        result = extract_targets(candidate)
        self.assertIn("files", result)
        self.assertIn("symbols", result)


class TestGrepPatterns(unittest.TestCase):
    def test_plain_function_pattern(self):
        result = _grep_patterns(["myFunc"])
        # Should include call pattern
        self.assertTrue(any("myFunc" in p for p in result))

    def test_deduplication(self):
        result = _grep_patterns(["foo", "foo"])
        self.assertLessEqual(result.count("foo("), 1)

    def test_capping(self):
        symbols = ["a", "b", "c", "d", "e", "f"]
        result = _grep_patterns(symbols, cap=3)
        self.assertLessEqual(len(result), 3)

    def test_empty_symbols(self):
        result = _grep_patterns([])
        self.assertEqual(result, [])


class TestPlanRetry(unittest.TestCase):
    def test_high_confidence_no_retry(self):
        result = plan_retry({"confidence": 0.9}, threshold=0.7)
        self.assertFalse(result["retry_recommended"])

    def test_null_confidence_no_retry(self):
        result = plan_retry({"confidence": None})
        self.assertFalse(result["retry_recommended"])

    def test_nested_confidence_dict(self):
        result = plan_retry({"confidence": {"confidence": 0.9}}, threshold=0.7)
        self.assertFalse(result["retry_recommended"])

    def test_low_confidence_no_candidates_no_retry(self):
        result = plan_retry({"confidence": 0.3}, threshold=0.7)
        self.assertFalse(result["retry_recommended"])

    def test_two_valid_candidates_retry_recommended(self):
        bundle = {
            "confidence": 0.5,
            "generator": {
                "candidates": [
                    {"id": "a", "summary": "scripts/foo.py", "sketch": "bar()"},
                    {"id": "b", "summary": "scripts/baz.py", "sketch": "qux()"},
                ]
            },
            "control": {
                "verdicts": [
                    {"id": "a", "valid": True, "issues": []},
                    {"id": "b", "valid": True, "issues": []},
                ]
            },
            "conservator": {
                "scores": [
                    {"id": "a", "regression_risk": {"net_concern": 0.3}},
                    {"id": "b", "regression_risk": {"net_concern": 0.4}},
                ]
            },
        }
        result = plan_retry(bundle, threshold=0.7)
        self.assertTrue(result["retry_recommended"])
        self.assertEqual(len(result["top_candidates"]), 2)

    def test_output_has_required_keys(self):
        result = plan_retry({"confidence": 0.5}, threshold=0.7)
        self.assertIn("retry_recommended", result)
        self.assertIn("reason", result)
        self.assertIn("top_candidates", result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
