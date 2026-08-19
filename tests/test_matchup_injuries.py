# -*- coding: utf-8 -*-
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from clients.injuries import assert_espn_summary_shape, parse_espn_summary_injuries  # noqa: E402
from core.matchup import implied_totals  # noqa: E402
from core.roster import bye_exposure, needs, stack_exposure  # noqa: E402


class RosterTests(unittest.TestCase):
    def test_needs_and_stacks(self):
        players = [
            {"pos": "QB", "team": "BUF", "bye": 7},
            {"pos": "RB", "team": "DET", "bye": 6},
            {"pos": "RB", "team": "DET", "bye": 6},
            {"pos": "WR", "team": "DET", "bye": 6},
            {"pos": "WR", "team": "CIN", "bye": 6},
            {"pos": "TE", "team": "ARI", "bye": 14},
        ]
        n = needs(players)
        self.assertEqual(n["need"]["QB"], 0)
        self.assertTrue(n["flex_open"])
        stacks = stack_exposure(players, threshold=3)
        det = [s for s in stacks if s["team"] == "DET"][0]
        self.assertTrue(det["flag"])
        byes = bye_exposure(players, threshold=4)
        wk6 = [b for b in byes if b["bye_week"] == 6][0]
        self.assertTrue(wk6["flag"])


class MatchupSignTests(unittest.TestCase):
    def test_phi_home_favorite_2025_w1(self):
        # DAL @ PHI, spread_line=8.5 (home favored), total=47.5
        t = implied_totals(8.5, 47.5)
        self.assertEqual(t["status"], "ok")
        self.assertAlmostEqual(t["implied_home"], 28.0)
        self.assertAlmostEqual(t["implied_away"], 19.5)

    def test_home_underdog_negative_spread(self):
        t = implied_totals(-2.5, 47.5)
        self.assertAlmostEqual(t["implied_home"], 22.5)
        self.assertAlmostEqual(t["implied_away"], 25.0)

    def test_missing_unverified(self):
        t = implied_totals(None, 47.5)
        self.assertTrue(t["status"].startswith("UNVERIFIED"))


class EspnShapeTests(unittest.TestCase):
    def test_pinned_summary_shape(self):
        payload = json.loads((ROOT / "tests/fixtures/espn_summary_injuries.json").read_text())
        assert_espn_summary_shape(payload)
        rows = parse_espn_summary_injuries(payload)
        self.assertTrue(rows)
        self.assertEqual(rows[0]["team"], "CIN")
        self.assertIn(rows[0]["report_status"], ("Questionable", "Out", "Doubtful"))
        self.assertTrue(rows[0]["name"])

    def test_shape_break_fails(self):
        with self.assertRaises(AssertionError):
            assert_espn_summary_shape({"foo": 1})
