# -*- coding: utf-8 -*-
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from jobs.draft_poll import apply_picks, my_slot  # noqa: E402


class DraftPollTests(unittest.TestCase):
    def test_marks_mine_vs_taken(self):
        xw = {"by_sleeper_id": {"9221": 1, "7564": 3}}
        picks = [
            {"player_id": "9221", "picked_by": "me", "pick_no": 1, "metadata": {"first_name": "Jahmyr", "last_name": "Gibbs"}},
            {"player_id": "7564", "picked_by": "you", "pick_no": 2, "metadata": {"first_name": "Ja'Marr", "last_name": "Chase"}},
            {"player_id": "99999", "picked_by": "you", "pick_no": 3, "metadata": {"first_name": "Nobody", "last_name": "Here"}},
        ]
        out = apply_picks(picks, xw, "me")
        self.assertEqual(out["st"]["1"], "mine")
        self.assertEqual(out["st"]["3"], "taken")
        self.assertEqual(out["unmapped"][0]["player_id"], "99999")

    def test_slot_from_draft_order(self):
        draft = {"draft_order": {"me": 7}, "settings": {"teams": 18}, "status": "drafting"}
        self.assertEqual(my_slot(draft, "me")["slot"], 7)
        self.assertEqual(my_slot(draft, "me")["teams"], 18)
