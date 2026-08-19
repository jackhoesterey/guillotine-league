# -*- coding: utf-8 -*-
"""
Implied team totals from nflverse games.csv.

Verified 2025-01 DAL@PHI: spread_line=8.5, total_line=47.5, home=PHI.
Eagles were heavy home favorites; nflverse stores a *positive* spread_line when
the home team is favored (the opposite of a typical home spread of -8.5).

So the plan's formula (home = total/2 - spread/2) is backwards for this file.
Correct:

    implied_home = total_line/2 + spread_line/2
    implied_away = total_line/2 - spread_line/2

Use for tiebreaks between similar floor plays only. Never override a FLOOR/AVOID grade.
"""
from __future__ import annotations

from typing import Optional


def _f(v) -> Optional[float]:
    if v in (None, ""):
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def implied_totals(spread_line, total_line) -> dict:
    spread = _f(spread_line)
    total = _f(total_line)
    if spread is None or total is None:
        return {
            "implied_home": None,
            "implied_away": None,
            "status": "UNVERIFIED — missing spread_line or total_line",
        }
    return {
        "implied_home": total / 2 + spread / 2,
        "implied_away": total / 2 - spread / 2,
        "spread_line": spread,
        "total_line": total,
        "convention": "nflverse: positive spread_line = home favored",
        "status": "ok",
    }


def team_implied(game: dict, team: str) -> dict:
    home = game.get("home_team")
    away = game.get("away_team")
    base = implied_totals(game.get("spread_line"), game.get("total_line"))
    if base["status"] != "ok":
        return base
    if team == home:
        base["team"] = team
        base["implied"] = base["implied_home"]
        base["side"] = "home"
    elif team == away:
        base["team"] = team
        base["implied"] = base["implied_away"]
        base["side"] = "away"
    else:
        base["status"] = f"UNVERIFIED — {team} not in {away}@{home}"
        base["implied"] = None
    return base


def game_for(games: list[dict], team: str, week: int, season: int = 2026) -> Optional[dict]:
    for g in games:
        if str(g.get("season")) != str(season):
            continue
        try:
            if int(g.get("week") or 0) != int(week):
                continue
        except ValueError:
            continue
        if g.get("home_team") == team or g.get("away_team") == team:
            return g
    return None
