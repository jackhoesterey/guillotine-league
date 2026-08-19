# -*- coding: utf-8 -*-
"""nflverse schedules, player IDs, official injury report."""
from __future__ import annotations

import csv
import io
from typing import Optional

from clients.http import FetchResult, fetch

PLAYERS_CSV = "https://github.com/nflverse/nflverse-data/releases/download/players/players.csv"
GAMES_CSV = "https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv"
INJURIES_CSV = "https://github.com/nflverse/nflverse-data/releases/download/injuries/injuries_{season}.csv"

# Refresh player IDs daily; games hourly during the season; injuries a few times a day.
PLAYERS_MAX_AGE = 86400
GAMES_MAX_AGE = 3600
INJURIES_MAX_AGE = 6 * 3600


def _csv(url: str, key: str, max_age: float, force: bool = False) -> FetchResult:
    r = fetch(url, key, max_age=max_age, force=force, as_json=False, ext=".csv")
    if r.ok and r.text:
        r.data = list(csv.DictReader(io.StringIO(r.text)))
    return r


def players(force: bool = False) -> FetchResult:
    return _csv(PLAYERS_CSV, "nflverse_players", PLAYERS_MAX_AGE, force=force)


def games(force: bool = False) -> FetchResult:
    return _csv(GAMES_CSV, "nflverse_games", GAMES_MAX_AGE, force=force)


def injuries(season: int = 2026, force: bool = False) -> FetchResult:
    return _csv(INJURIES_CSV.format(season=season), f"nflverse_injuries_{season}", INJURIES_MAX_AGE, force=force)


def games_for_season(rows: list[dict], season: int = 2026) -> list[dict]:
    return [r for r in rows if str(r.get("season")) == str(season)]
