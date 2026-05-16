"""Tests for philosophical voice variants (reduced scope).

Covers: Control+Aurelius, Conservator+Confucius, precedent_search.
Omitted (absorbed into RUND2): Control+Wittgenstein, Conservator+Aurelius.

Run:
    python scripts/test_philosophical_voices.py
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import validate_report
from precedent_search import search, _overlap_score, _tokenize


_AGGREGATE_LOG = [{"step": "aggregate", "result": {"chosen": "A"}}]


class TestBackwardCompat(unittest.TestCase):
    """Old runs must still pass validation."""

    def test_old_run_passes_default(self):
        report = {
            "success_criterion": "fix the bug",
            "verification": "tests pass",
            "chosen_approach": "inline_fix",
            "telemetry": {"mode": "sequential"},
            "deliberation_log": _AGGREGATE_LOG,
        }
        problems = validate_report.validate(report)
        self.assertEqual(problems, [])

    def test_old_run_no_philosophical_fields_passes(self):
        report = {
            "success_criterion": "fix the bug",
            "verification": "tests pass",
            "chosen_approach": "inline_fix",
            "telemetry": {"mode": "parallel", "voices": {"generator": {}, "control": {}, "conservator": {}}},
            "deliberation_log": _AGGREGATE_LOG,
        }
        problems = validate_report.validate(report)
        self.assertEqual(problems, [])


class TestAureliusControlValidator(unittest.TestCase):

    def test_valid_output_passes(self):
        output = {
            "in_control": ["choice A"],
            "out_of_control": [],
            "uncertain_control": ["negotiation"],
            "wasted_deliberation": None,
        }
        problems = validate_report._validate_philosophical_aurelius_control(output)
        self.assertEqual(problems, [])

    def test_missing_in_control_fails(self):
        output = {"out_of_control": []}
        problems = validate_report._validate_philosophical_aurelius_control(output)
        self.assertTrue(any("in_control" in p for p in problems))

    def test_missing_out_of_control_fails(self):
        output = {"in_control": []}
        problems = validate_report._validate_philosophical_aurelius_control(output)
        self.assertTrue(any("out_of_control" in p for p in problems))

    def test_uncertain_control_optional(self):
        output = {"in_control": [], "out_of_control": []}
        problems = validate_report._validate_philosophical_aurelius_control(output)
        self.assertEqual(problems, [])

    def test_wasted_deliberation_accepts_string(self):
        output = {"in_control": [], "out_of_control": [], "wasted_deliberation": "option C is out of control"}
        problems = validate_report._validate_philosophical_aurelius_control(output)
        self.assertEqual(problems, [])

    def test_wasted_deliberation_rejects_non_string(self):
        output = {"in_control": [], "out_of_control": [], "wasted_deliberation": 42}
        problems = validate_report._validate_philosophical_aurelius_control(output)
        self.assertTrue(any("wasted_deliberation" in p for p in problems))

    def test_wasted_deliberation_null_passes(self):
        output = {"in_control": ["x"], "out_of_control": [], "wasted_deliberation": None}
        problems = validate_report._validate_philosophical_aurelius_control(output)
        self.assertEqual(problems, [])


class TestConfuciusValidator(unittest.TestCase):

    def test_valid_fallback_output_passes(self):
        output = {
            "precedent_search": {"matches_found": 0, "fallback_to_abstract": True},
            "ancestor_guidance": None,
        }
        problems = validate_report._validate_philosophical_confucius(output)
        self.assertEqual(problems, [])

    def test_missing_precedent_search_fails(self):
        output = {"ancestor_guidance": None}
        problems = validate_report._validate_philosophical_confucius(output)
        self.assertTrue(any("precedent_search" in p for p in problems))

    def test_missing_matches_found_fails(self):
        output = {"precedent_search": {"fallback_to_abstract": True}}
        problems = validate_report._validate_philosophical_confucius(output)
        self.assertTrue(any("matches_found" in p for p in problems))

    def test_missing_fallback_to_abstract_fails(self):
        output = {"precedent_search": {"matches_found": 0}}
        problems = validate_report._validate_philosophical_confucius(output)
        self.assertTrue(any("fallback_to_abstract" in p for p in problems))

    def test_experimental_warning_on_low_matches(self):
        output = {
            "precedent_search": {"matches_found": 1, "fallback_to_abstract": False},
        }
        problems = validate_report._validate_philosophical_confucius(output)
        self.assertTrue(any("EXPERIMENTAL" in p or "limited" in p.lower() for p in problems))

    def test_sufficient_matches_no_warning(self):
        output = {
            "precedent_search": {"matches_found": 5, "fallback_to_abstract": False},
            "ancestor_guidance": "approach A worked in 4/5 cases",
        }
        problems = validate_report._validate_philosophical_confucius(output)
        self.assertEqual(problems, [])


class TestPrecedentSearch(unittest.TestCase):

    def test_overlap_score_empty_query(self):
        score = _overlap_score(set(), "any text here")
        self.assertEqual(score, 0.0)

    def test_overlap_score_full_match(self):
        score = _overlap_score({"stop", "loss"}, "stop loss strategy trading")
        self.assertEqual(score, 1.0)

    def test_overlap_score_partial_match(self):
        score = _overlap_score({"stop", "loss", "limit"}, "stop loss strategy")
        self.assertAlmostEqual(score, 2 / 3, places=5)

    def test_overlap_score_no_match(self):
        score = _overlap_score({"stop", "loss"}, "hello world")
        self.assertEqual(score, 0.0)

    def test_tokenize_lowercases(self):
        tokens = _tokenize("Stop Loss STRATEGY")
        self.assertIn("stop", tokens)
        self.assertIn("loss", tokens)
        self.assertIn("strategy", tokens)

    def test_search_returns_zero_results_on_no_match(self):
        result = search("xyzzy_not_in_any_run_ever_hopefully_12345")
        self.assertEqual(result["matches_found"], 0)
        self.assertEqual(result["results"], [])

    def test_search_returns_structure(self):
        result = search("test query")
        self.assertIn("query", result)
        self.assertIn("matches_found", result)
        self.assertIn("results", result)

    def test_search_limit_respected(self):
        result = search("the a is of", limit=2)
        self.assertLessEqual(len(result["results"]), 2)

    def test_search_results_have_required_fields(self):
        result = search("car wash decision", limit=5)
        for r in result["results"]:
            self.assertIn("run_id", r)
            self.assertIn("score", r)
            self.assertIn("success_criterion", r)
            self.assertIn("chosen_approach", r)
            self.assertIn("outcome", r)

    def test_search_scores_in_range(self):
        result = search("car wash", limit=5)
        for r in result["results"]:
            self.assertGreaterEqual(r["score"], 0.0)
            self.assertLessEqual(r["score"], 1.0)


class TestCrossVoice(unittest.TestCase):

    def test_all_philosophical_voice_outputs_pass_default_validation(self):
        report = {
            "success_criterion": "validate all voices",
            "verification": "test passes",
            "chosen_approach": "A",
            "telemetry": {"mode": "sequential"},
            "deliberation_log": _AGGREGATE_LOG,
            "voice_outputs": {
                "aurelius-control": {
                    "in_control": ["choice A"],
                    "out_of_control": [],
                },
                "confucius": {
                    "precedent_search": {"matches_found": 0, "fallback_to_abstract": True},
                    "ancestor_guidance": None,
                },
            },
        }
        problems = validate_report.validate(report)
        self.assertEqual(problems, [])

    def test_one_voice_active_does_not_require_other(self):
        report = {
            "success_criterion": "test",
            "verification": "test",
            "chosen_approach": "A",
            "telemetry": {"mode": "sequential"},
            "deliberation_log": _AGGREGATE_LOG,
            "voice_outputs": {
                "aurelius-control": {"in_control": [], "out_of_control": []},
            },
        }
        problems = validate_report.validate(report)
        self.assertEqual(problems, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
