"""Tests for ROUND2 architecture additions.

Run:
    python scripts/test_round2.py
    python -m pytest scripts/test_round2.py -v  (if pytest available)
"""
# tested-by: CONSILIUM-AGGREGATOR-001
# tested-by: CONSILIUM-VALIDATE-REPORT-001
# tested-by: CONSILIUM-VOCABULARY-MAP-001
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


class TestAggregateRound2(unittest.TestCase):
    def _base_conservator(self, reversibility="complete", magnitude="trivial", meta=None, flag=False):
        # Mirror the real conservator.md output contract: every per-candidate
        # field (regression_risk, meta_recommendation, irreversibility_flag)
        # lives inside scores[i]. The voice emits NO top-level regression_risk
        # or irreversibility_flag — aggregate_sequential reads them from scores[].
        # (Earlier this fixture injected top-level copies that masked the nesting
        # bug — TODO bug-audit 2026-05-31, Cluster A.)
        return {
            "scores": [
                {
                    "id": "A",
                    "regression_risk": {
                        "reversibility": reversibility,
                        "magnitude": magnitude,
                        "net_concern": 0.05,
                    },
                    "meta_recommendation": meta,
                    "irreversibility_flag": flag,
                    "tokens_budget": {"generator": 300, "control": 300},
                }
            ],
        }

    def _base_generator(self, preferred: "str | None" = "A", abstain=False):
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

    def test_preferred_not_in_candidates_raises(self):
        # Guard (2026-06-28 Skeptic): a generator.preferred that names no real
        # candidate must fail loud, not silently become chosen — a non-existent
        # id collapses every confidence_per_option to the 0.5 base with no error.
        with self.assertRaises(ValueError):
            aggregator.aggregate_sequential(
                self._base_generator(preferred="ghost_candidate"),
                self._base_control(),
                self._base_conservator(),
            )

    def test_preferred_none_does_not_raise(self):
        # Boundary: preferred=None is the "no explicit winner" case (chosen=None),
        # not a hallucination — it stays permitted and must not trip the guard.
        result = aggregator.aggregate_sequential(
            self._base_generator(preferred=None),
            self._base_control(),
            self._base_conservator(),
        )
        self.assertEqual(result["result"], "AGGREGATE")
        self.assertIsNone(result["chosen"])

    def test_conservative_override_empty_candidates_raises(self):
        # Guard (audit 2026-07-02): an empty candidates list is an upstream
        # bundle bug — the default scheme used to exit 0 with a false "all
        # candidates vetoed by conservator" reason (nothing was vetoed) while
        # the sibling schemes raise ValueError. It must fail loud like them.
        with self.assertRaises(ValueError):
            aggregator.aggregate_conservative_override([])

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


class TestConservativeOverride(unittest.TestCase):
    """Behavioral coverage for the documented default aggregation scheme.

    CONSILIUM-AGGREGATOR-001 declares two acceptance criteria for
    conservative_override (all-vetoed retry, lower-risk-ranks-first) but only
    the sequential routing outcomes were actually tested. These lock the veto
    boundary (SKILL.md: risk>0.8 strict), the safer-wins tie-break (a bug that
    already shipped once — TODO.md:108), and the escalation path.
    """

    @staticmethod
    def _cand(cid, gen, ctrl, cons):
        return {"id": cid, "scores": {"generator": gen, "control": ctrl, "conservator": cons}}

    def test_veto_boundary_is_strict(self):
        # risk == 0.80 survives (not > 0.8); risk == 0.81 is vetoed.
        result = aggregator.aggregate_conservative_override([
            self._cand("at_080", 0.7, 0.7, 0.80),
            self._cand("over_081", 0.9, 0.9, 0.81),
        ])
        self.assertEqual(result["chosen"], "at_080")
        self.assertEqual([v["id"] for v in result["vetoed"]], ["over_081"])

    def test_all_vetoed_auto_relax_suggests_retry(self):
        # Acceptance #1: every candidate over threshold, auto_relax on ->
        # chosen null + non-empty retry_suggested with the lowest risk relaxed.
        result = aggregator.aggregate_conservative_override([
            self._cand("a", 0.8, 0.8, 0.84),
            self._cand("b", 0.8, 0.8, 0.82),
        ])
        self.assertIsNone(result["chosen"])
        self.assertIn("retry_suggested", result)
        self.assertEqual(result["retry_suggested"]["relaxed_threshold"], 0.82)
        self.assertEqual(result["retry_suggested"]["lowest_risk_candidate"]["id"], "b")
        self.assertNotIn("escalation_required", result)

    def test_lower_risk_ranks_first(self):
        # Acceptance #2: identical generator+control, different conservator ->
        # the lower-risk candidate ranks first.
        result = aggregator.aggregate_conservative_override([
            self._cand("risky", 0.7, 0.7, 0.55),
            self._cand("safe", 0.7, 0.7, 0.20),
        ])
        self.assertEqual(result["chosen"], "safe")

    def test_equal_score_tiebreak_prefers_safer(self):
        # Genuine weighted-score tie (both == 0.6): safer (lower conservator)
        # must win. Locks the TODO.md:108 "safer wins on tie" fix — the prior
        # bug broke the tie by insertion order instead.
        result = aggregator.aggregate_conservative_override([
            self._cand("hi_risk", 0.7, 0.7, 0.60),   # safety 0.4 -> (0.7+0.7+0.4)/3 = 0.6
            self._cand("lo_risk", 0.6, 0.6, 0.40),   # safety 0.6 -> (0.6+0.6+0.6)/3 = 0.6
        ])
        self.assertAlmostEqual(result["ranking"][0]["score"], result["ranking"][1]["score"])
        self.assertEqual(result["chosen"], "lo_risk")

    def test_all_vetoed_beyond_relaxed_cap_escalates(self):
        # Lowest risk exceeds RELAXED_VETO_CAP (0.85): relaxing would not help,
        # so escalate instead of suggesting a retry.
        result = aggregator.aggregate_conservative_override([
            self._cand("a", 0.8, 0.8, 0.92),
            self._cand("b", 0.8, 0.8, 0.90),
        ])
        self.assertIsNone(result["chosen"])
        self.assertTrue(result["escalation_required"])
        self.assertNotIn("retry_suggested", result)


class TestValidateReportRound2(unittest.TestCase):
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


class TestValidateTriasTrigger(unittest.TestCase):
    """GAP#1: _validate_trias must fire on telemetry.mode == 'trias', not only
    on team == 'trias'. Real trias runs key off mode and frequently omit team;
    gating on team alone silently skipped every trias check on those runs."""

    def _trias_shaped_report(self, mode, team=None):
        # Deliberately omits personalities + vote_pattern, so the trias checks
        # (if they run) MUST produce 'trias:'-prefixed problems.
        report = {
            "success_criterion": "x",
            "verification": "x",
            "chosen_approach": "x",
            "confidence": 0.8,
            "telemetry": {"mode": mode, "voices": {"pioneer_generator": {"tokens_in": 0}}},
            "pipeline_executed": True,
            "deliberation_log": [{"step": "aggregate", "result": {"chosen": "x"}}],
        }
        if team is not None:
            report["team"] = team
        return report

    def test_trias_mode_without_team_triggers_trias_checks(self):
        problems = validate_report.validate(self._trias_shaped_report(mode="trias"))
        self.assertTrue(
            any(p.startswith("trias:") for p in problems),
            f"trias-mode report (no team) must trigger trias checks; got {problems}",
        )

    def test_team_trias_still_triggers(self):
        problems = validate_report.validate(self._trias_shaped_report(mode="sequential", team="trias"))
        self.assertTrue(any(p.startswith("trias:") for p in problems))

    def test_sequential_mode_no_trias_checks(self):
        problems = validate_report.validate(self._trias_shaped_report(mode="sequential"))
        self.assertFalse(
            any(p.startswith("trias:") for p in problems),
            f"sequential report must NOT trigger trias checks; got {problems}",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
