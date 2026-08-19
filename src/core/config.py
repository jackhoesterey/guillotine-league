# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from paths import DATA, ROOT


@dataclass
class LeagueConfig:
    league_id: str = ""
    username: str = ""
    user_id: str = ""
    draft_id: str = ""
    faab_budget: int = 1000
    season: int = 2026
    ntfy_topic: str = ""
    my_roster_id: Optional[int] = None

    def require_league(self) -> None:
        if not self.league_id:
            raise SystemExit(
                "No league_id. Copy data/league.example.json to data/league.json "
                "and fill it in, or set SLEEPER_LEAGUE_ID."
            )


def load_config() -> LeagueConfig:
    cfg = LeagueConfig()
    for name in ("league.json", "league.example.json"):
        p = DATA / name
        if not p.exists() and name == "league.json":
            p = ROOT / name
        if p.exists():
            try:
                raw = json.loads(p.read_text())
            except json.JSONDecodeError:
                raw = {}
            for k in ("league_id", "username", "user_id", "draft_id", "ntfy_topic"):
                if raw.get(k):
                    setattr(cfg, k, str(raw[k]))
            if raw.get("faab_budget") is not None:
                cfg.faab_budget = int(raw["faab_budget"])
            if raw.get("season") is not None:
                cfg.season = int(raw["season"])
            if raw.get("my_roster_id") is not None:
                cfg.my_roster_id = int(raw["my_roster_id"])
            if name == "league.json":
                break
    cfg.league_id = os.environ.get("SLEEPER_LEAGUE_ID", cfg.league_id)
    cfg.username = os.environ.get("SLEEPER_USERNAME", cfg.username)
    cfg.user_id = os.environ.get("SLEEPER_USER_ID", cfg.user_id)
    cfg.draft_id = os.environ.get("SLEEPER_DRAFT_ID", cfg.draft_id)
    cfg.ntfy_topic = os.environ.get("NTFY_TOPIC", cfg.ntfy_topic)
    if os.environ.get("FAAB_BUDGET"):
        cfg.faab_budget = int(os.environ["FAAB_BUDGET"])
    return cfg
