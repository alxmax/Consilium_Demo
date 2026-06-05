"""Tests for utils.py pure utility functions.

Covers canonical_run_path (path normalization), is_headless (env detection),
issue_penalty (severity lookup), and validate_keys (required-field guard).

Run:
    python scripts/test_utils.py
    python -m pytest scripts/test_utils.py -v  (if pytest available)
"""
# tested-by: CONSILIUM-UTILS-001
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from utils import canonical_run_path, is_headless, issue_penalty, validate_keys


class TestCanonicalRunPath(unittest.TestCase):
    def test_plain_filename(self):
        self.assertEqual(canonical_run_path("run1.json"), "runs/run1.json")

    def test_full_consilium_path(self):
        self.assertEqual(canonical_run_path(".consilium/runs/run1.json"), "runs/run1.json")

    def test_absolute_path(self):
        result = canonical_run_path("/home/user/.consilium/runs/run1.json")
        self.assertEqual(result, "runs/run1.json")

    def test_windows_backslash_path(self):
        result = canonical_run_path("C:\\Users\\user\\.consilium\\runs\\run1.json")
        self.assertEqual(result, "runs/run1.json")

    def test_multiple_dots_in_name(self):
        result = canonical_run_path(".consilium/runs/run.2026.01.15.json")
        self.assertEqual(result, "runs/run.2026.01.15.json")


class TestIsHeadless(unittest.TestCase):
    def setUp(self):
        self._orig = os.environ.get("CLAUDE_HEADLESS")

    def tearDown(self):
        if self._orig is None:
            os.environ.pop("CLAUDE_HEADLESS", None)
        else:
            os.environ["CLAUDE_HEADLESS"] = self._orig

    def test_not_set_returns_false(self):
        os.environ.pop("CLAUDE_HEADLESS", None)
        self.assertFalse(is_headless())

    def test_set_to_1_returns_true(self):
        os.environ["CLAUDE_HEADLESS"] = "1"
        self.assertTrue(is_headless())

    def test_set_to_true_not_truthy(self):
        os.environ["CLAUDE_HEADLESS"] = "true"
        self.assertFalse(is_headless())

    def test_set_to_0_returns_false(self):
        os.environ["CLAUDE_HEADLESS"] = "0"
        self.assertFalse(is_headless())


class TestIssuePenalty(unittest.TestCase):
    def test_low_severity(self):
        self.assertEqual(issue_penalty({"severity": "low"}), 0.05)

    def test_medium_severity(self):
        self.assertEqual(issue_penalty({"severity": "medium"}), 0.15)

    def test_high_severity(self):
        self.assertEqual(issue_penalty({"severity": "high"}), 0.30)

    def test_missing_severity_defaults_to_medium(self):
        self.assertEqual(issue_penalty({}), 0.15)

    def test_unrecognized_severity_defaults_to_medium(self):
        self.assertEqual(issue_penalty({"severity": "unknown"}), 0.15)

    def test_non_dict_defaults_to_medium(self):
        self.assertEqual(issue_penalty("string"), 0.15)
        self.assertEqual(issue_penalty(None), 0.15)


class TestValidateKeys(unittest.TestCase):
    def test_all_keys_present_passes(self):
        validate_keys({"a": 1, "b": 2}, ["a", "b"], "ctx")

    def test_missing_key_raises(self):
        with self.assertRaises((ValueError, SystemExit)):
            validate_keys({"a": 1}, ["a", "b"], "ctx")

    def test_error_message_includes_key_and_context(self):
        try:
            validate_keys({}, ["missing_key"], "my_context")
            self.fail("expected exception")
        except (ValueError, SystemExit) as e:
            err = str(e)
            self.assertTrue("missing_key" in err or "my_context" in err)

    def test_non_dict_raises(self):
        with self.assertRaises((ValueError, SystemExit)):
            validate_keys("not a dict", ["x"], "ctx")  # type: ignore[arg-type]

    def test_empty_required_passes_any_dict(self):
        validate_keys({"a": 1}, [], "ctx")
        validate_keys({}, [], "ctx")

    def test_extra_keys_ignored(self):
        validate_keys({"a": 1, "b": 2, "c": 3}, ["a"], "ctx")


if __name__ == "__main__":
    unittest.main(verbosity=2)
