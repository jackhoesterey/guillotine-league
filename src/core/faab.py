# -*- coding: utf-8 -*-
"""Rival FAAB intelligence and bid ceilings. Never auto-submit a bid."""
from __future__ import annotations

from statistics import median
from typing import Iterable, Optional


# Playbook spend curve: remaining FAAB target at the *end* of each stretch.
SPEND_CURVE = [
    (1, 4, 850, "Survive — cheap patches only"),
    (5, 9, 650, "Navigate — spend on chaos/bye weeks, not between them"),
    (10, 13, 300, "Pivot — prices collapse; buy the roster that wins"),
    (14, 17, 0, "Empty the tank — leftover dollars are wasted"),
]


def remaining_for_roster(roster: dict, league_budget: int = 1000) -> int:
    used = (roster.get("settings") or {}).get("waiver_budget_used")
    if used is None:
        return league_budget
    try:
        used_i = int(used)
    except (TypeError, ValueError):
        return league_budget
    return league_budget - used_i


def remaining_map(rosters: Iterable[dict], league_budget: int = 1000,
                  surviving: Optional[set[int]] = None) -> dict[int, int]:
    out = {}
    for r in rosters:
        rid = r.get("roster_id")
        if rid is None:
            continue
        rid = int(rid)
        if surviving is not None and rid not in surviving:
            continue
        out[rid] = remaining_for_roster(r, league_budget)
    return out


def landscape(remaining: dict[int, int], my_roster_id: int,
              bids: Iterable[int] = (25, 44, 77, 121, 153, 201)) -> dict:
    rivals = [v for rid, v in remaining.items() if rid != my_roster_id]
    mine = remaining.get(my_roster_id)
    if not rivals:
        return {
            "my_remaining": mine,
            "rivals_alive": 0,
            "max_rival": None,
            "median_rival": None,
            "bids": [],
            "status": "UNVERIFIED — no rival budgets",
        }
    rows = []
    for x in bids:
        can = sum(1 for r in rivals if r > x)
        rows.append({
            "bid": x,
            "can_outbid_me": can,
            "rivals_alive": len(rivals),
            "blurb": f"Bid ${x} and {can} of {len(rivals)} surviving teams can outbid you.",
        })
    return {
        "my_remaining": mine,
        "rivals_alive": len(rivals),
        "max_rival": max(rivals),
        "median_rival": median(rivals),
        "broke": sorted(rid for rid, v in remaining.items() if rid != my_roster_id and v < 50),
        "bids": rows,
        "status": "ok",
    }


def curve_target(week: int) -> dict:
    for lo, hi, target, note in SPEND_CURVE:
        if lo <= week <= hi:
            return {"week": week, "remaining_target": target, "note": note}
    return {"week": week, "remaining_target": None, "note": "UNVERIFIED — week out of 1–17"}


def curve_verdict(week: int, my_remaining: Optional[int]) -> dict:
    t = curve_target(week)
    if my_remaining is None or t["remaining_target"] is None:
        t["verdict"] = "UNVERIFIED"
        return t
    target = t["remaining_target"]
    if my_remaining > target + 150 and week >= 10:
        t["verdict"] = "hoarding — the bar is rising and unspent FAAB dies with you"
    elif my_remaining < target - 200 and week <= 9:
        t["verdict"] = "overspending — you are burning capital in the weeks you were likely to survive anyway"
    else:
        t["verdict"] = "on curve"
    t["my_remaining"] = my_remaining
    t["delta_vs_target"] = my_remaining - target
    return t


def winning_bids_from_transactions(transactions: Iterable[dict]) -> list[dict]:
    """Pull waiver_bid amounts. Do not guess at trades beyond the documented waiver_budget array."""
    out = []
    for tx in transactions or []:
        if (tx.get("type") or "").lower() not in ("waiver", "free_agent", "waiver_wire"):
            # still record waiver_bid if present
            pass
        settings = tx.get("settings") or {}
        bid = settings.get("waiver_bid")
        adds = tx.get("adds") or {}
        if bid is None and not adds:
            # trades: waiver_budget array
            for move in tx.get("waiver_budget") or []:
                out.append({
                    "kind": "trade_faab",
                    "amount": move.get("amount"),
                    "sender": move.get("sender"),
                    "receiver": move.get("receiver"),
                    "transaction_id": tx.get("transaction_id"),
                    "status": tx.get("status"),
                    "week": tx.get("leg") or tx.get("week"),
                })
            continue
        if bid is None:
            continue
        player_ids = list(adds.keys()) if isinstance(adds, dict) else []
        out.append({
            "kind": "waiver",
            "amount": bid,
            "player_ids": player_ids,
            "roster_id": tx.get("roster_ids", [None])[0] if tx.get("roster_ids") else None,
            "transaction_id": tx.get("transaction_id"),
            "status": tx.get("status"),
            "week": tx.get("leg") or tx.get("week"),
        })
    return out


def price_curve(bids: list[dict]) -> dict:
    won = [b for b in bids if b.get("kind") == "waiver" and b.get("amount") is not None
           and (b.get("status") in (None, "complete"))]
    if not won:
        return {"n": 0, "median": None, "max": None, "status": "UNVERIFIED — no winning bids logged yet"}
    amounts = sorted(int(b["amount"]) for b in won)
    return {
        "n": len(amounts),
        "median": median(amounts),
        "max": max(amounts),
        "p90": amounts[int(0.9 * (len(amounts) - 1))],
        "status": "ok",
        "amounts": amounts,
    }
