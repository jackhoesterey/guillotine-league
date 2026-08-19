# -*- coding: utf-8 -*-
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from core.survival import margin, scores_from_matchups  # noqa: E402


class SurvivalTests(unittest.TestCase):
    def test_chop_line_min(self):
        mu = [
            {"roster_id": 1, "points": 112.4},
            {"roster_id": 2, "points": 87.1},
            {"roster_id": 3, "points": 101.0},
        ]
        s = scores_from_matchups(mu)
        self.assertEqual(s["chop_line"], 87.1)
        self.assertEqual(s["status"], "ok")
        m = margin(112.4, s["chop_line"])
        self.assertAlmostEqual(m["margin"], 25.3, places=4)
        self.assertEqual(m["danger"], "safe")

    def test_surviving_filter_does_not_guess(self):
        mu = [
            {"roster_id": 1, "points": 90},
            {"roster_id": 2, "points": 0},
            {"roster_id": 3, "points": 88},
        ]
        # Without an explicit survivor set, a zero is a real score (open question).
        all_of = scores_from_matchups(mu, surviving=None)
        self.assertEqual(all_of["chop_line"], 0)
        # After we *know* roster 2 is dead, drop them.
        alive = scores_from_matchups(mu, surviving={1, 3})
        self.assertEqual(alive["chop_line"], 88)
        self.assertEqual(alive["assumption"], "survivors-only")

    def test_missing_points_unverified(self):
        s = scores_from_matchups([{"roster_id": 1}])
        self.assertEqual(s["chop_line"], None)
        self.assertTrue(s["status"].startswith("UNVERIFIED"))
        self.assertTrue(margin(None, 90)["status"].startswith("UNVERIFIED"))
