"""Tests for usage.py pure telemetry aggregation functions.

Covers _percentiles (statistical summaries), _new_voice_bucket (bucket init),
collect (cross-report aggregation), and _latency_warnings (spike detection).

Run:
    python scripts/test_usage.py
    python -m pytest scripts/test_usage.py -v  (if pytest available)
"""
# tested-by: CONSILIUM-USAGE-001
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from usage import _latency_warnings, _new_voice_bucket, _percentiles, collect


class TestPercentiles(unittest.TestCase):
    def test_empty_list(self):
        result = _percentiles([])
        self.assertEqual(result["count"], 0)

    def test_single_value(self):
        result = _percentiles([100])
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["sum"], 100)
        self.assertEqual(result["mean"], 100.0)

    def test_multiple_values(self):
        result = _percentiles([10, 20, 30, 40, 50])
        self.assertEqual(result["count"], 5)
        self.assertEqual(result["sum"], 150)
        self.assertEqual(result["mean"], 30.0)
        self.assertIn("p50", result)

    def test_p95_requires_at_least_2(self):
        self.assertNotIn("p95", _percentiles([100]))
        self.assertIn("p95", _percentiles([100, 200]))


class TestNewVoiceBucket(unittest.TestCase):
    def test_has_required_keys(self):
        bucket = _new_voice_bucket()
        self.assertIn("tokens_in", bucket)
        self.assertIn("tokens_out", bucket)
        self.assertIn("latency_ms", bucket)

    def test_values_are_empty_lists(self):
        bucket = _new_voice_bucket()
        for v in bucket.values():
            self.assertEqual(v, [])


class TestCollect(unittest.TestCase):
    def test_empty_reports(self):
        result = collect([])
        self.assertEqual(result["runs_total"], 0)
        self.assertEqual(result["with_telemetry"], 0)

    def test_report_without_telemetry_counted(self):
        result = collect([{"id": "run1"}])
        self.assertEqual(result["runs_total"], 1)
        self.assertEqual(result["with_telemetry"], 0)

    def test_skipped_reports_counted(self):
        reports = [{"skipped": True, "telemetry": {}}, {"skipped": False, "telemetry": {}}]
        result = collect(reports)
        self.assertEqual(result["skipped_runs"], 1)

    def test_mode_filter_excludes_non_matching(self):
        reports = [
            {"telemetry": {"mode": "sequential"}},
            {"telemetry": {"mode": "trias"}},
        ]
        result = collect(reports, mode_filter="trias")
        self.assertEqual(result["with_telemetry"], 1)
        self.assertIn("trias", result["modes"])
        self.assertNotIn("sequential", result["modes"])

    def test_per_voice_aggregation(self):
        reports = [
            {"telemetry": {"mode": "sequential", "voices": {
                "generator": {"tokens_in": 1000, "tokens_out": 200, "latency_ms": 1000},
            }}},
            {"telemetry": {"mode": "sequential", "voices": {
                "generator": {"tokens_in": 1500, "tokens_out": 300, "latency_ms": 1500},
            }}},
        ]
        result = collect(reports)
        gen = result["voices"]["generator"]
        self.assertEqual(gen["tokens_in"]["count"], 2)
        self.assertEqual(gen["tokens_in"]["sum"], 2500)

    def test_mode_tokens_summed(self):
        reports = [{"telemetry": {"mode": "sequential", "voices": {
            "generator": {"tokens_in": 1000, "tokens_out": 200},
            "control": {"tokens_in": 500, "tokens_out": 100},
        }}}]
        result = collect(reports)
        self.assertEqual(result["modes"]["sequential"]["tokens_in"], 1500)
        self.assertEqual(result["modes"]["sequential"]["tokens_out"], 300)


class TestLatencyWarnings(unittest.TestCase):
    def test_no_warnings_for_empty_reports(self):
        self.assertEqual(_latency_warnings([], []), [])

    def test_sequential_mode_not_checked(self):
        reports = [{"telemetry": {"mode": "sequential", "voices": {
            "generator": {"latency_ms": 1000},
            "control": {"latency_ms": 5000},
        }}}]
        files = [Path("run1.json")]
        self.assertEqual(_latency_warnings(files, reports), [])

    def test_spike_detected_in_parallel(self):
        reports = [{"telemetry": {"mode": "parallel", "voices": {
            "generator": {"latency_ms": 1000},
            "control": {"latency_ms": 4000},
        }}}]
        files = [Path("run1.json")]
        warnings = _latency_warnings(files, reports)
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0]["type"], "latency_spike")

    def test_single_voice_no_warning(self):
        reports = [{"telemetry": {"mode": "parallel", "voices": {
            "generator": {"latency_ms": 9000},
        }}}]
        files = [Path("run1.json")]
        self.assertEqual(_latency_warnings(files, reports), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
