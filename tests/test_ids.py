# -*- coding: utf-8 -*-
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from core.ids import (  # noqa: E402
    MIN_COVERAGE, build_crosswalk, match_board_player, name_keys, normalize_name,
    index_sleeper, load_board_players,
)


class NormalizeTests(unittest.TestCase):
    def test_apostrophe(self):
        self.assertEqual(normalize_name("Ja'Marr Chase"), normalize_name("JaMarr Chase"))
        self.assertEqual(normalize_name("Tre' Harris"), normalize_name("Tre Harris"))
        self.assertEqual(normalize_name("De'Von Achane"), normalize_name("Devon Achane"))
        self.assertEqual(normalize_name("D'Andre Swift"), normalize_name("DAndre Swift"))
        self.assertEqual(normalize_name("Wan'Dale Robinson"), normalize_name("WanDale Robinson"))

    def test_suffixes(self):
        self.assertEqual(normalize_name("Michael Pittman Jr."), normalize_name("Michael Pittman"))
        self.assertEqual(normalize_name("Chris Godwin Jr."), normalize_name("Chris Godwin"))
        self.assertEqual(normalize_name("Deebo Samuel Sr."), normalize_name("Deebo Samuel"))
        self.assertEqual(normalize_name("Oronde Gadsden II"), normalize_name("Oronde Gadsden"))
        self.assertEqual(normalize_name("Patrick Mahomes II"), normalize_name("Patrick Mahomes"))
        self.assertEqual(normalize_name("Kyle Pitts Sr."), normalize_name("Kyle Pitts"))
        self.assertEqual(normalize_name("James Cook III"), normalize_name("James Cook"))
        self.assertEqual(normalize_name("Luther Burden III"), normalize_name("Luther Burden"))
        self.assertEqual(normalize_name("Brian Robinson"), "brianrobinson")

    def test_punctuation_and_case(self):
        self.assertEqual(normalize_name("A.J. Brown"), normalize_name("AJ Brown"))
        self.assertEqual(normalize_name("C.J. Stroud"), normalize_name("CJ Stroud"))
        self.assertEqual(normalize_name("J.K. Dobbins"), normalize_name("JK Dobbins"))
        self.assertEqual(normalize_name("T.J. Hockenson"), normalize_name("TJ Hockenson"))

    def test_kenny_kenneth_alias(self):
        self.assertIn(normalize_name("Kenneth Gainwell"), name_keys("Kenny Gainwell"))
        self.assertIn(normalize_name("Kenny Gainwell"), name_keys("Kenneth Gainwell"))


class FixtureMatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = ROOT / "tests" / "fixtures" / "sleeper_players_sample.json"
        cls.players = json.loads(path.read_text())

    def test_kenny_gainwell_from_kenneth_board_name(self):
        ix = index_sleeper(self.players)
        rec = match_board_player({"r": 88, "n": "Kenny Gainwell", "p": "RB", "t": "TB"}, ix, {})
        self.assertEqual(rec["sleeper_id"], "7567")
        rec2 = match_board_player({"r": 88, "n": "Kenneth Gainwell", "p": "RB", "t": "TB"}, ix, {})
        self.assertEqual(rec2["sleeper_id"], "7567")

    def test_suffix_board_names(self):
        ix = index_sleeper(self.players)
        cases = [
            ("Michael Pittman Jr.", "WR", "PIT", "6819"),
            ("Chris Godwin Jr.", "WR", "TB", "4037"),
            ("Deebo Samuel Sr.", "WR", "SF", "5872"),
            ("Oronde Gadsden II", "TE", "LAC", "12493"),
            ("Patrick Mahomes II", "QB", "KC", "4046"),
            ("Kyle Pitts Sr.", "TE", "ATL", "7553"),
            ("James Cook III", "RB", "BUF", "8138"),
            ("Tre' Harris", "WR", "LAC", "12509"),
            ("Ja'Marr Chase", "WR", "CIN", "7564"),
            ("A.J. Brown", "WR", "NE", "5859"),
            ("C.J. Stroud", "QB", "HOU", "9758"),
        ]
        for name, pos, team, sid in cases:
            rec = match_board_player({"r": 1, "n": name, "p": pos, "t": team}, ix, {})
            self.assertEqual(rec.get("sleeper_id"), sid, msg=name)

    def test_override_wins(self):
        ix = index_sleeper(self.players)
        rec = match_board_player(
            {"r": 1, "n": "Jahmyr Gibbs", "p": "RB", "t": "DET"},
            ix, {"Jahmyr Gibbs": {"sleeper_id": "7567"}},
        )
        self.assertEqual(rec["sleeper_id"], "7567")
        self.assertEqual(rec["method"], "override")


class CoverageTests(unittest.TestCase):
    def test_live_board_coverage(self):
        cache = ROOT / "cache" / "sleeper_players.json"
        if not cache.exists():
            self.skipTest("no cached Sleeper player master")
        players = json.loads(cache.read_text())
        board = load_board_players()
        self.assertGreaterEqual(len(board), 200)
        xw = build_crosswalk(players, [], board, {})
        if xw["unmatched"]:
            print("UNMATCHED:", xw["unmatched"])
        self.assertGreaterEqual(xw["coverage"], MIN_COVERAGE)
        self.assertEqual(xw["unmatched"], [])


if __name__ == "__main__":
    unittest.main()
