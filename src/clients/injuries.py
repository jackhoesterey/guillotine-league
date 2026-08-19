# -*- coding: utf-8 -*-
"""
Injury sources behind one interface.

Tier 1 (weekly designations): nflverse injuries CSV is source of truth;
Sleeper /players/nfl is the backup. Depth-chart diffs are an early-warning
signal, not a designation.

Tier 2 (game-day inactives): ESPN scoreboard/summary/injuries were fetched
2026-08-19. Summary returns weekly-style designations under `injuries[]`
(status Questionable/Out, athlete.fullName, type.abbreviation). None of the
candidate endpoints returned a game-day inactive list. Do not invent one.
"""
from __future__ import annotations

from typing import Any, Optional

from clients.http import FetchResult, fetch
from clients import nflverse, sleeper

ESPN_SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
ESPN_SUMMARY = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event={event_id}"
ESPN_INJURIES = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/injuries"

# Shape pin — tests fail if ESPN drops these keys.
ESPN_SUMMARY_INJURY_SHAPE = {
    "injuries": list,  # [ {team: {abbreviation}, injuries: [ {status, athlete, type} ] } ]
}

REPORT_RANK = {"Out": 0, "Doubtful": 1, "Questionable": 2, "IR": 3, "PUP": 4}


def designation_rank(status: Optional[str]) -> int:
    if not status:
        return 99
    return REPORT_RANK.get(status, 50)


def from_nflverse_row(row: dict) -> dict:
    return {
        "gsis_id": row.get("gsis_id"),
        "name": row.get("full_name"),
        "team": row.get("team"),
        "position": row.get("position"),
        "week": row.get("week"),
        "report_status": row.get("report_status") or None,
        "practice_status": row.get("practice_status") or None,
        "report_primary_injury": row.get("report_primary_injury"),
        "source": "nflverse",
    }


def from_sleeper_player(p: dict) -> dict:
    return {
        "sleeper_id": str(p.get("player_id") or ""),
        "name": p.get("full_name"),
        "team": p.get("team"),
        "position": p.get("position"),
        "report_status": p.get("injury_status") or None,
        "practice_status": p.get("practice_participation") or None,
        "injury_start_date": p.get("injury_start_date"),
        "depth_chart_order": p.get("depth_chart_order"),
        "depth_chart_position": p.get("depth_chart_position"),
        "status": p.get("status"),
        "source": "sleeper",
    }


def parse_espn_summary_injuries(payload: dict) -> list[dict]:
    """Verified 2026-08-19 against summary?event=401873272. No inactives field."""
    out = []
    for team_block in payload.get("injuries") or []:
        team = (team_block.get("team") or {}).get("abbreviation")
        for inj in team_block.get("injuries") or []:
            athlete = inj.get("athlete") or {}
            typ = inj.get("type") or {}
            details = inj.get("details") or {}
            out.append({
                "espn_id": str(athlete.get("id") or ""),
                "name": athlete.get("fullName") or athlete.get("displayName"),
                "team": team,
                "report_status": inj.get("status") or (details.get("fantasyStatus") or {}).get("description"),
                "injury_type": details.get("type"),
                "type_abbr": typ.get("abbreviation"),
                "date": inj.get("date"),
                "source": "espn_summary",
            })
    return out


def assert_espn_summary_shape(payload: dict) -> None:
    if "injuries" not in payload or not isinstance(payload.get("injuries"), list):
        raise AssertionError("ESPN summary fixture missing injuries[] — endpoint shape changed")
    if payload["injuries"]:
        block = payload["injuries"][0]
        if "team" not in block or "injuries" not in block:
            raise AssertionError("ESPN summary injury team block missing team/injuries")
        if block["injuries"]:
            inj = block["injuries"][0]
            for k in ("status", "athlete", "type"):
                if k not in inj:
                    raise AssertionError(f"ESPN summary injury item missing {k}")


def fetch_espn_summary(event_id: str, force: bool = False) -> FetchResult:
    return fetch(ESPN_SUMMARY.format(event_id=event_id), f"espn_summary_{event_id}",
                 max_age=600, force=force, as_json=True)


def fetch_espn_scoreboard(force: bool = False) -> FetchResult:
    return fetch(ESPN_SCOREBOARD, "espn_scoreboard", max_age=300, force=force, as_json=True)


def fetch_espn_injuries(force: bool = False) -> FetchResult:
    # Large payload; daily is enough. Not used for inactives.
    return fetch(ESPN_INJURIES, "espn_injuries", max_age=86400, force=force, as_json=True)


def depth_chart_snapshot(sleeper_players: dict) -> dict[str, dict]:
    snap = {}
    for pid, p in (sleeper_players or {}).items():
        if not isinstance(p, dict) or p.get("position") not in {"QB", "RB", "WR", "TE"}:
            continue
        snap[str(p.get("player_id") or pid)] = {
            "name": p.get("full_name"),
            "team": p.get("team"),
            "position": p.get("position"),
            "depth_chart_order": p.get("depth_chart_order"),
            "depth_chart_position": p.get("depth_chart_position"),
        }
    return snap


def depth_chart_diff(prev: dict, curr: dict) -> list[dict]:
    alerts = []
    for pid, now in (curr or {}).items():
        was = (prev or {}).get(pid)
        if not was:
            continue
        if was.get("depth_chart_order") != now.get("depth_chart_order"):
            alerts.append({
                "sleeper_id": pid,
                "name": now.get("name"),
                "team": now.get("team"),
                "position": now.get("position"),
                "from": was.get("depth_chart_order"),
                "to": now.get("depth_chart_order"),
                "slot": now.get("depth_chart_position"),
            })
    return alerts


def merge_tier1(nflverse_rows: list[dict], sleeper_players: dict, crosswalk: dict) -> dict[str, dict]:
    """Key by sleeper_id when possible; else gsis_id. nflverse wins on report_status."""
    by_sleeper = {}
    gsis_to_sleeper = {}
    for rec in (crosswalk.get("by_rank") or {}).values():
        if rec.get("sleeper_id") and rec.get("gsis_id"):
            gsis_to_sleeper[rec["gsis_id"]] = rec["sleeper_id"]

    for pid, p in (sleeper_players or {}).items():
        if not isinstance(p, dict) or p.get("position") not in {"QB", "RB", "WR", "TE"}:
            continue
        rec = from_sleeper_player(p)
        by_sleeper[rec["sleeper_id"]] = rec

    for row in nflverse_rows or []:
        nv = from_nflverse_row(row)
        sid = gsis_to_sleeper.get(nv.get("gsis_id"))
        if not sid:
            continue
        cur = by_sleeper.setdefault(sid, {"sleeper_id": sid, "source": "nflverse"})
        # nflverse is source of truth for official report
        if nv.get("report_status"):
            cur["report_status"] = nv["report_status"]
        if nv.get("practice_status"):
            cur["practice_status"] = nv["practice_status"]
        cur["gsis_id"] = nv.get("gsis_id")
        cur["nflverse"] = True
        cur["name"] = cur.get("name") or nv.get("name")
        cur["source"] = "nflverse+sleeper" if cur.get("source") == "sleeper" else "nflverse"
    return by_sleeper
