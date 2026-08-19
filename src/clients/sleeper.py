# -*- coding: utf-8 -*-
"""Sleeper REST wrapper. No auth. Stay under 1000 calls/min. /players/nfl once a day."""
from __future__ import annotations

from typing import Any, Optional

from clients.http import FetchResult, fetch

BASE = "https://api.sleeper.app/v1"
PLAYERS_MAX_AGE = 86400  # Sleeper: fetch the 5MB player master at most once per day
DEFAULT_MAX_AGE = 300


def _get(path: str, key: str, max_age: Optional[float] = DEFAULT_MAX_AGE, force: bool = False) -> FetchResult:
    return fetch(f"{BASE}{path}", key, max_age=max_age, force=force, as_json=True)


def state_nfl(force: bool = False) -> FetchResult:
    return _get("/state/nfl", "sleeper_state_nfl", max_age=60, force=force)


def user(username_or_id: str, force: bool = False) -> FetchResult:
    return _get(f"/user/{username_or_id}", f"sleeper_user_{username_or_id}", force=force)


def user_leagues(user_id: str, season: int = 2026, force: bool = False) -> FetchResult:
    return _get(f"/user/{user_id}/leagues/nfl/{season}", f"sleeper_leagues_{user_id}_{season}", force=force)


def league(league_id: str, force: bool = False) -> FetchResult:
    return _get(f"/league/{league_id}", f"sleeper_league_{league_id}", force=force)


def rosters(league_id: str, force: bool = False) -> FetchResult:
    return _get(f"/league/{league_id}/rosters", f"sleeper_rosters_{league_id}", force=force)


def users(league_id: str, force: bool = False) -> FetchResult:
    return _get(f"/league/{league_id}/users", f"sleeper_users_{league_id}", force=force)


def matchups(league_id: str, week: int, force: bool = False) -> FetchResult:
    return _get(f"/league/{league_id}/matchups/{week}", f"sleeper_matchups_{league_id}_{week}", force=force)


def transactions(league_id: str, round_: int, force: bool = False) -> FetchResult:
    return _get(
        f"/league/{league_id}/transactions/{round_}",
        f"sleeper_tx_{league_id}_{round_}",
        force=force,
    )


def drafts(league_id: str, force: bool = False) -> FetchResult:
    return _get(f"/league/{league_id}/drafts", f"sleeper_drafts_{league_id}", force=force)


def draft(draft_id: str, force: bool = False) -> FetchResult:
    return _get(f"/draft/{draft_id}", f"sleeper_draft_{draft_id}", max_age=30, force=force)


def draft_picks(draft_id: str, force: bool = False) -> FetchResult:
    return _get(f"/draft/{draft_id}/picks", f"sleeper_picks_{draft_id}", max_age=2, force=force)


def players_nfl(force: bool = False) -> FetchResult:
    return _get("/players/nfl", "sleeper_players", max_age=PLAYERS_MAX_AGE, force=force)


def trending_add(lookback_hours: int = 24, limit: int = 25, force: bool = False) -> FetchResult:
    return _get(
        f"/players/nfl/trending/add?lookback_hours={lookback_hours}&limit={limit}",
        f"sleeper_trending_add_{lookback_hours}",
        max_age=600,
        force=force,
    )


def skill_players(players: dict[str, Any]) -> dict[str, Any]:
    out = {}
    for pid, p in (players or {}).items():
        if not p:
            continue
        if p.get("position") in {"QB", "RB", "WR", "TE"}:
            out[str(p.get("player_id") or pid)] = p
    return out
