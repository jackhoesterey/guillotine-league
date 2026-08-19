# -*- coding: utf-8 -*-
"""My roster, positional need, bye and NFL-team stack exposure."""
from __future__ import annotations

from collections import Counter
from typing import Iterable, Optional


STARTERS_NEEDED = {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "FLEX": 1}


def resolve_players(sleeper_ids: Iterable[str], crosswalk: dict, board_by_rank: Optional[dict] = None) -> list[dict]:
    by_s = crosswalk.get("by_sleeper_id") or {}
    by_rank = crosswalk.get("by_rank") or {}
    out = []
    for sid in sleeper_ids or []:
        sid = str(sid)
        rank = by_s.get(sid)
        rec = by_rank.get(str(rank), {}) if rank is not None else {}
        board = (board_by_rank or {}).get(rank) or (board_by_rank or {}).get(str(rank)) or {}
        out.append({
            "sleeper_id": sid,
            "rank": rank,
            "name": board.get("n") or rec.get("board_name") or rec.get("full_name"),
            "pos": board.get("p") or rec.get("position"),
            "team": board.get("t") or rec.get("team"),
            "bye": board.get("b"),
            "grade": board.get("g"),
        })
    return out


def needs(players: list[dict]) -> dict:
    cnt = Counter(p.get("pos") for p in players if p.get("pos") in STARTERS_NEEDED)
    need = {pos: max(0, n - cnt.get(pos, 0)) for pos, n in STARTERS_NEEDED.items() if pos != "FLEX"}
    flex_used = max(0, cnt.get("RB", 0) - 2) + max(0, cnt.get("WR", 0) - 2) + max(0, cnt.get("TE", 0) - 1)
    return {
        "counts": dict(cnt),
        "need": need,
        "flex_open": flex_used == 0 and cnt.get("RB", 0) >= 2 and cnt.get("WR", 0) >= 2 and cnt.get("TE", 0) >= 1,
    }


def bye_exposure(players: list[dict], threshold: int = 4) -> list[dict]:
    c = Counter(p.get("bye") for p in players if p.get("bye"))
    return [{"bye_week": wk, "n": n, "flag": n >= threshold} for wk, n in sorted(c.items())]


def stack_exposure(players: list[dict], threshold: int = 3) -> list[dict]:
    c = Counter(p.get("team") for p in players if p.get("team"))
    return [{"team": t, "n": n, "flag": n >= threshold} for t, n in sorted(c.items(), key=lambda x: -x[1])]
