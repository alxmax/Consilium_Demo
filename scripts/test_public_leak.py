"""Tests for check_public_leak.py — the RED path of the public-leak guard.

A live CI run only exercises the pass path (the repo is clean), so a
PATTERNS/SKIP_SUFFIX regression would silently disable the guard. These
tests feed synthetic leaking text through the scan_text seam.
Fixture strings are built by concatenation so this (tracked) file does
not itself trip the guard.

Run:
    python scripts/test_public_leak.py
"""
# tested-by: CONSILIUM-CHECK-PUBLIC-LEAK-001
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from check_public_leak import SKIP_SUFFIX, scan_text

PRIVATE_REPO = "alxmax/" + "Consilium"
PUBLIC_REPO = "alxmax/" + "Consilium_Demo"
LOCAL_PATH = "Desktop" + chr(92) + "Doc" + chr(92) + "Consilium"


class TestScanText(unittest.TestCase):
    def test_private_repo_ref_detected(self):
        hits = scan_text("x.md", "see " + PRIVATE_REPO + " for source")
        self.assertEqual(len(hits), 1)
        self.assertIn("private dev repo", hits[0])

    def test_public_demo_repo_allowed(self):
        self.assertEqual(scan_text("x.md", "install from " + PUBLIC_REPO), [])

    def test_local_dev_path_detected(self):
        hits = scan_text("x.md", "C:" + chr(92) + "Users" + chr(92) + "A" + chr(92) + LOCAL_PATH)
        self.assertEqual(len(hits), 1)
        self.assertIn("local dev absolute path", hits[0])

    def test_line_number_reported(self):
        hits = scan_text("x.md", "clean line" + chr(10) + PRIVATE_REPO)
        self.assertIn("x.md:2:", hits[0])

    def test_clean_text_no_hits(self):
        self.assertEqual(scan_text("x.md", "nothing to see"), [])


class TestSkipSuffix(unittest.TestCase):
    def test_binary_suffixes_skipped_by_main(self):
        # main() skips these before scanning; pin the suffix set so an
        # accidental addition (e.g. .md) cannot silently blind the guard.
        self.assertIn(".png", SKIP_SUFFIX)
        for forbidden in (".md", ".py", ".html", ".json"):
            self.assertNotIn(forbidden, SKIP_SUFFIX)


if __name__ == "__main__":
    unittest.main(verbosity=2)
