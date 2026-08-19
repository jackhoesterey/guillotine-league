# -*- coding: utf-8 -*-
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from core.faab import (  # noqa: E402
    curve_verdict, landscape, price_curve, remaining_map, winning_bids_from_transactions,
)


ROSTERS = [
    {"roster_id": 1, "settings": {"waiver_budget_used": 120}},
    {"roster_id": 2, "settings": {"waiver_budget_used": 900}},
    {"roster_id": 3, "settings": {"waiver_budget_used": 0}},
    {"roster_id": 4, "settings": {"waiver_budget_used": 40}},
]


class FaabTests(unittest.TestCase):
    def test_remaining(self):
        m = remaining_map(ROSTERS, 1000)
        self.assertEqual(m[1], 880)
        self.assertEqual(m[2], 100)
        self.assertEqual(m[3], 1000)

    def test_landscape_copy(self):
        m = remaining_map(ROSTERS, 1000)
        land = landscape(m, my_roster_id=1, bids=(77, 121, 201))
        self.assertEqual(land["rivals_alive"], 3)
        self.assertEqual(land["max_rival"], 1000)
        b77 = [b for b in land["bids"] if b["bid"] == 77][0]
        # rivals with remaining 100, 1000, 960 — all three can outbid 77
        self.assertEqual(b77["can_outbid_me"], 3)
        b201 = [b for b in land["bids"] if b["bid"] == 201][0]
        # only 1000 and 960
        self.assertEqual(b201["can_outbid_me"], 2)
        self.assertIn("3 of 3", b77["blurb"])

    def test_curve_hoarding_late(self):
        v = curve_verdict(12, 800)
        self.assertIn("hoarding", v["verdict"])

    def test_transactions(self):
        tx = [
            {"type": "waiver", "status": "complete", "settings": {"waiver_bid": 44},
             "adds": {"7567": 1}, "roster_ids": [1]},
            {"type": "trade", "waiver_budget": [{"sender": 1, "receiver": 2, "amount": 10}]},
        ]
        bids = winning_bids_from_transactions(tx)
        self.assertEqual(bids[0]["amount"], 44)
        self.assertEqual(bids[1]["kind"], "trade_faab")
        curve = price_curve(bids)
        self.assertEqual(curve["median"], 44)
        self.assertEqual(curve["n"], 1)
