"""Tests for confidence derivation from voice-score variance and vote patterns.

Covers both score-based mode (sequential/dialectic) and Trias mode (democratic
vote pattern). Includes agreement calculation, separation signal blending,
mode-floor exemption logic, and Steward-specific dissent/abstain penalties.

Run:
    python scripts/test_confidence.py
    python -m pytest scripts/test_confidence.py -v  (if pytest available)
"""
# tested-by: CONSILIUM-CONFIDENCE-001
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from confidence import (
    check_mode_floor,
    confidence_from_vote_pattern,
    derive,
    validate_input,
    CONFIDENCE_CEIL,
    CONFIDENCE_FLOOR,
    STEWARD_ABSTAIN_PENALTY,
    STEWARD_DISSENT_PENALTY,
    VOTE_PATTERN_CONFIDENCE,
)


class TestDeriveScoreBased(unittest.TestCase):
    def test_high_agreement_near_perfect_confidence(self):
        candidates = [
            {"id": "chosen", "scores": {"generator": 0.8, "control": 0.9, "conservator": 0.1}}
        ]
        result = derive(candidates, "chosen")
        self.assertIsNotNone(result["confidence"])
        self.assertGreater(result["confidence"], 0.90)
        self.assertLessEqual(result["confidence"], CONFIDENCE_CEIL)

    def test_no_separation_when_only_chosen(self):
        candidates = [
            {"id": "only_one", "scores": {"generator": 0.5, "control": 0.5, "conservator": 0.5}}
        ]
        result = derive(candidates, "only_one")
        self.assertEqual(result["separation"], 1.0)

    def test_separation_present_with_runner_up(self):
        candidates = [
            {"id": "chosen", "scores": {"generator": 0.9, "control": 0.9, "conservator": 0.1}},
            {"id": "runnerup", "scores": {"generator": 0.5, "control": 0.5, "conservator": 0.5}},
        ]
        result = derive(candidates, "chosen")
        self.assertGreater(result["separation"], 0.0)
        self.assertLess(result["separation"], 1.0)

    def test_chosen_not_in_candidates(self):
        candidates = [{"id": "A", "scores": {"generator": 0.5, "control": 0.5, "conservator": 0.5}}]
        result = derive(candidates, "nonexistent")
        self.assertIsNone(result["confidence"])
        self.assertIn("reason", result)

    def test_confidence_clamped_floor(self):
        candidates = [
            {"id": "c1", "scores": {"generator": 0.0, "control": 0.0, "conservator": 1.0}},
        ]
        result = derive(candidates, "c1")
        self.assertGreaterEqual(result["confidence"], CONFIDENCE_FLOOR)

    def test_confidence_clamped_ceil(self):
        candidates = [
            {"id": "perfect", "scores": {"generator": 0.5, "control": 0.5, "conservator": 0.5}},
        ]
        result = derive(candidates, "perfect")
        self.assertLessEqual(result["confidence"], CONFIDENCE_CEIL)
        self.assertLess(result["confidence"], 1.0)


class TestDeriveNullChosen(unittest.TestCase):
    def test_none_chosen_returns_null_confidence(self):
        candidates = [{"id": "A", "scores": {"generator": 0.5, "control": 0.5, "conservator": 0.5}}]
        result = derive(candidates, None)
        self.assertIsNone(result["confidence"])
        self.assertIn("reason", result)


class TestValidateInput(unittest.TestCase):
    def test_valid_input_passes(self):
        data = {
            "candidates": [{"id": "A", "scores": {"generator": 0.5, "control": 0.5, "conservator": 0.5}}],
            "chosen": "A",
        }
        try:
            validate_input(data)
        except SystemExit:
            self.fail("validate_input raised SystemExit for valid input")

    def test_missing_scores_key_exits_1(self):
        data = {
            "candidates": [{"id": "A"}],
            "chosen": "A",
        }
        with self.assertRaises(SystemExit) as ctx:
            validate_input(data)
        self.assertEqual(ctx.exception.code, 1)


class TestTriasVotePattern(unittest.TestCase):
    def test_three_zero_unanimous(self):
        result = confidence_from_vote_pattern("3-0")
        self.assertEqual(result["confidence"], VOTE_PATTERN_CONFIDENCE["3-0"])
        self.assertEqual(result["agreement"], 1.0)
        self.assertIsNone(result["separation"])
        self.assertEqual(result["source"], "vote_pattern")

    def test_two_one_dissent_without_steward(self):
        result = confidence_from_vote_pattern(
            "2-1",
            dissent=[{"personality": "pioneer", "chose": "other"}],
        )
        self.assertEqual(result["confidence"], VOTE_PATTERN_CONFIDENCE["2-1"])

    def test_two_one_dissent_with_steward(self):
        result = confidence_from_vote_pattern(
            "2-1",
            dissent=[{"personality": "steward", "chose": "other"}],
        )
        expected = round(VOTE_PATTERN_CONFIDENCE["2-1"] - STEWARD_DISSENT_PENALTY, 3)
        self.assertEqual(result["confidence"], expected)

    def test_two_zero_veto(self):
        result = confidence_from_vote_pattern("2-0")
        self.assertEqual(result["confidence"], VOTE_PATTERN_CONFIDENCE["2-0"])

    def test_two_zero_abstain_with_steward(self):
        result = confidence_from_vote_pattern(
            "2-0",
            abstained=[{"name": "steward", "reason": "ambiguous"}],
        )
        expected = round(VOTE_PATTERN_CONFIDENCE["2-0"] - STEWARD_ABSTAIN_PENALTY, 3)
        self.assertEqual(result["confidence"], expected)

    def test_unknown_pattern_raises(self):
        with self.assertRaises((ValueError, KeyError)):
            confidence_from_vote_pattern("9-9")


class TestCheckModeFloor(unittest.TestCase):
    def test_below_floor_flagged(self):
        result = check_mode_floor("trias", 0.70)
        self.assertTrue(result["below_floor"])

    def test_above_floor_ok(self):
        result = check_mode_floor("trias", 0.95)
        self.assertFalse(result["below_floor"])

    def test_none_confidence_always_ok(self):
        result = check_mode_floor("trias", None)
        self.assertFalse(result["below_floor"])

    def test_unknown_mode_no_floor(self):
        result = check_mode_floor("unknown_mode", 0.5)
        self.assertFalse(result["below_floor"])

    def test_trias_3_0_exempt_from_weak(self):
        result = check_mode_floor("trias", 0.70, vote_pattern="3-0")
        self.assertFalse(result["below_floor"])

    def test_trias_2_1_exempt_from_weak(self):
        result = check_mode_floor("trias", 0.70, vote_pattern="2-1")
        self.assertFalse(result["below_floor"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
