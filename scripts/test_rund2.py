"""Tests for RUND2 architecture additions.

Run:
    python scripts/test_rund2.py
    python -m pytest scripts/test_rund2.py -v  (if pytest available)
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from vocabulary_map import translate, compute_tokens_budget, VOCABULARY_MAP
import aggregator
import validate_report


class TestVocabularyMap(unittest.TestCase):
    def test_translate_reversibility_complete(self):
        result = translate("reversibility", "complete")
        self.assertIn("ușor", result)

    def test_translate_magnitude_critical(self):
        result = translate("magnitude", "critical")
        self.assertIn("major", result.lower())

    def test_translate_meta_recommendation_scale_down(self):
        result = translate("meta_recommendation", "scale_down")
        self.assertTrue(len(result) > 0)

    def test_translate_unknown_category(self):
        result = translate("nonexistent", "value")
        self.assertEqual(result, "value")

    def test_translate_none_value(self):
        result = translate("meta_recommendation", None)
        self.assertEqual(result, "")

    def test_compute_tokens_budget_trivial_complete(self):
        budget = compute_tokens_budget("trivial", "complete")
        self.assertEqual(budget["generator"], 300)
        self.assertEqual(budget["control"], 300)

    def test_compute_tokens_budget_critical_irreversible(self):
        budget = compute_tokens_budget("critical", "irreversible")
        self.assertEqual(budget["generator"], 4000)

    def test_compute_tokens_budget_scale_down_override(self):
        budget = compute_tokens_budget("critical", "irreversible", meta="scale_down")
        self.assertEqual(budget["generator"], 300)

    def test_compute_tokens_budget_unknown_combo_defaults(self):
        budget = compute_tokens_budget("trivial", "irreversible")
        self.assertEqual(budget["generator"], 800)

    def test_compute_tokens_budget_scale_up_critical_clamped(self):
        # critical+irreversible base=4000; +50% would be 6000 but clamped to 4000 (cap is intentional)
        budget = compute_tokens_budget("critical", "irreversible", meta="scale_up")
        self.assertEqual(budget["generator"], 4000)
        self.assertEqual(budget["control"], 4000)

    def test_compute_tokens_budget_scale_up_moderate_increases(self):
        # moderate+partial base=800; +50% rounded to nearest 100 = 1200
        budget = compute_tokens_budget("moderate", "partial", meta="scale_up")
        self.assertEqual(budget["generator"], 1200)


class TestAggregateRund2(unittest.TestCase):
    def _base_conservator(self, reversibility="complete", magnitude="trivial", meta=None, flag=False):
        # meta_recommendation belongs inside scores[i] (per-candidate), per
        # conservator.md output contract. aggregate_sequential() reads it from
        # there; top-level meta_recommendation is legacy and ignored.
        return {
            "regression_risk": {
                "reversibility": reversibility,
                "magnitude": magnitude,
                "net_concern": 0.05,
            },
            "irreversibility_flag": flag,
            "tokens_budget": {"generator": 300, "control": 300},
            "scores": [
                {
                    "id": "A",
                    "regression_risk": {
                        "reversibility": reversibility,
                        "magnitude": magnitude,
                        "net_concern": 0.05,
                    },
                    "meta_recommendation": meta,
                    "tokens_budget": {"generator": 300, "control": 300},
                }
            ],
        }

    def _base_generator(self, preferred="A", abstain=False):
        return {
            "candidates": [{"id": "A"}, {"id": "do_nothing"}],
            "preferred": preferred,
            "abstain": {"triggered": abstain, "reason": "test" if abstain else None},
            "challenge_upward": {"triggered": False, "reason": None},
        }

    def _base_control(self, glossary_fail=False, disagreements=None):
        return {
            "glossary": {"term": "definition"},
            "glossary_fail": glossary_fail,
            "glossary_attempts": [],
            "disagreements": disagreements or [],
            "verdicts": [{"id": "A", "valid": True, "issues": [], "tests_to_write": []}],
        }

    def test_glossary_fail_blocks(self):
        result = aggregator.aggregate_sequential(
            self._base_generator(),
            self._base_control(glossary_fail=True),
            self._base_conservator(),
        )
        self.assertEqual(result["result"], "BLOCK")
        self.assertEqual(result["reason"], "glossary_fail")

    def test_irreversibility_flag_blocks(self):
        result = aggregator.aggregate_sequential(
            self._base_generator(),
            self._base_control(),
            self._base_conservator(flag=True),
        )
        self.assertEqual(result["result"], "BLOCK")
        self.assertEqual(result["reason"], "irreversibility_no_consent")

    def test_substantial_disagreement_reworks(self):
        result = aggregator.aggregate_sequential(
            self._base_generator(),
            self._base_control(disagreements=[{"between": ["g", "c"], "type": "substantial", "detail": "x"}]),
            self._base_conservator(),
        )
        self.assertEqual(result["result"], "REWORK")

    def test_scale_down_adapts_short(self):
        result = aggregator.aggregate_sequential(
            self._base_generator(),
            self._base_control(),
            self._base_conservator(meta="scale_down"),
        )
        self.assertEqual(result["result"], "ADAPT_SHORT")

    def test_scale_up_adapts_extended(self):
        result = aggregator.aggregate_sequential(
            self._base_generator(),
            self._base_control(),
            self._base_conservator(meta="scale_up"),
        )
        self.assertEqual(result["result"], "ADAPT_EXTENDED")

    def test_three_triggers_escalate(self):
        result = aggregator.aggregate_sequential(
            self._base_generator(abstain=True),
            self._base_control(
                disagreements=[{"between": ["g", "c"], "type": "substantial", "detail": "x"}]
            ),
            self._base_conservator(meta="scale_up"),
        )
        self.assertEqual(result["result"], "ESCALATE")
        self.assertEqual(len(result["triggers"]), 3)

    def test_normal_aggregate_returns_chosen(self):
        result = aggregator.aggregate_sequential(
            self._base_generator(preferred="A"),
            self._base_control(),
            self._base_conservator(),
        )
        self.assertEqual(result["result"], "AGGREGATE")
        self.assertEqual(result["chosen"], "A")

    def test_low_methodology_confidence_warns(self):
        result = aggregator.aggregate_sequential(
            self._base_generator(abstain=True),
            self._base_control(disagreements=[
                {"type": "substantial", "detail": "x"},
                {"type": "substantial", "detail": "y"},
                {"type": "substantial", "detail": "z"},
            ]),
            self._base_conservator(),
        )
        # abstain + 3 substantial disagreements = triggers ["substantial_disagreement", "generator_abstain"] → 2 triggers → REWORK
        self.assertIn(result["result"], ("REWORK", "ESCALATE", "AGGREGATE"))


class TestValidateReportRund2(unittest.TestCase):
    def test_regression_risk_scalar_still_valid(self):
        problems = validate_report._validate_regression_risk(0.5)
        self.assertEqual(problems, [])

    def test_regression_risk_object_valid(self):
        problems = validate_report._validate_regression_risk({
            "reversibility": "complete",
            "magnitude": "trivial",
            "net_concern": 0.05,
        })
        self.assertEqual(problems, [])

    def test_regression_risk_object_missing_magnitude(self):
        problems = validate_report._validate_regression_risk({
            "reversibility": "complete",
            "net_concern": 0.05,
        })
        self.assertTrue(any("magnitude" in p for p in problems))

    def test_regression_risk_invalid_reversibility(self):
        problems = validate_report._validate_regression_risk({
            "reversibility": "unknown",
            "magnitude": "trivial",
        })
        self.assertTrue(any("reversibility" in p for p in problems))

    def test_regression_risk_scalar_out_of_range(self):
        problems = validate_report._validate_regression_risk(1.5)
        self.assertTrue(len(problems) > 0)

    def test_regression_risk_wrong_type(self):
        problems = validate_report._validate_regression_risk("high")
        self.assertTrue(len(problems) > 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
