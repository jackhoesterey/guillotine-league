# -*- coding: utf-8 -*-
"""Sunday ~10:45am ET starter checklist. Fail loud. Do not auto-bench anyone."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from clients import injuries as inj  # noqa: E402
from clients import nflverse, sleeper  # noqa: E402
from clients.http import age_seconds, iso  # noqa: E402
from core.config import load_config  # noqa: E402
from core.ids import load_crosswalk  # noqa: E402
from core.matchup import game_for, team_implied  # noqa: E402
from core.notify import push  # noqa: E402
from core.roster import resolve_players  # noqa: E402
from paths import DATA, ROOT as REPO  # noqa: E402

STALE_WEEKLY = 36 * 3600  # weekly report older than 36h is UNVERIFIED on Sunday


def kickoff_for(games: list, team: str, week: int, season: int) -> dict:
    g = game_for(games, team, week, season)
    if not g:
        return {"kickoff": None, "status": "UNVERIFIED — no game row"}
    day = g.get("gameday") or ""
    tm = g.get("gametime") or ""
    implied = team_implied(g, team)
    return {
        "kickoff": f"{day} {tm}".strip() or None,
        "opponent": g.get("away_team") if g.get("home_team") == team else g.get("home_team"),
        "implied_total": implied.get("implied") if implied.get("status") == "ok" else None,
        "implied_status": implied.get("status"),
        "game_id": g.get("game_id"),
        "status": "ok" if (day or tm) else "UNVERIFIED — missing kickoff",
    }


def render_html(payload: dict) -> str:
    def esc(s):
        return (str(s) if s is not None else "").replace("&", "&amp;").replace("<", "&lt;")
    rows = []
    for s in payload.get("starters") or []:
        flag = s.get("designation") or "—"
        unver = s.get("status", "").startswith("UNVERIFIED")
        color = "#f85149" if unver or flag in ("Out", "Doubtful") else "#d29922" if flag == "Questionable" else "#3fb950"
        rows.append(
            f"<tr><td>{esc(s.get('slot'))}</td><td>{esc(s.get('name'))}</td>"
            f"<td>{esc(s.get('pos'))} {esc(s.get('team'))}</td>"
            f"<td style='color:{color};font-weight:600'>{esc(flag)}</td>"
            f"<td>{esc(s.get('kickoff'))}</td>"
            f"<td>{esc(s.get('status'))}</td></tr>"
        )
    table = "".join(rows) or "<tr><td colspan=6>UNVERIFIED — no starters</td></tr>"
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Gameday checklist</title>
<style>
:root{{--bg:#0f1115;--tx:#e8eaef;--tx2:#9aa2b1;--line:#2a2f3a}}
body{{margin:0;background:var(--bg);color:var(--tx);font:15px/1.5 -apple-system,sans-serif}}
.top{{padding:12px 18px;border-bottom:1px solid var(--line);display:flex;gap:12px}}
a{{color:var(--tx2);text-decoration:none}}
.wrap{{max-width:900px;margin:0 auto;padding:24px 18px 80px}}
.unv{{background:rgba(248,81,73,.12);border:1px solid rgba(248,81,73,.4);padding:10px 12px;border-radius:8px;color:#ffb4ae}}
table{{width:100%;border-collapse:collapse}} td,th{{text-align:left;padding:8px 6px;border-bottom:1px solid var(--line)}}
th{{font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:#6b7382}}
</style></head><body>
<div class="top"><b>Gameday checklist</b> <a href="/">draft room</a> <a href="/brief.html">brief</a></div>
<div class="wrap">
<p>Look with your eyes. This is a checklist, not a decision.</p>
<p class="unv">{esc(payload.get("banner"))}</p>
<p style="color:#6b7382;font-size:12px">built {esc(payload.get("built_at"))}</p>
<table><thead><tr><th>Slot</th><th>Player</th><th>Pos</th><th>Designation</th><th>Kickoff</th><th>Source</th></tr></thead>
<tbody>{table}</tbody></table>
<h3>Depth-chart moves</h3>
<pre style="white-space:pre-wrap;color:#9aa2b1">{esc(json.dumps(payload.get("depth_alerts") or [], indent=2))}</pre>
</div></body></html>"""


def main() -> None:
    cfg = load_config()
    cfg.require_league()
    xw = load_crosswalk()
    st = sleeper.state_nfl()
    week = (st.data or {}).get("week") if st.ok else None
    season = int((st.data or {}).get("season") or cfg.season)

    ros = sleeper.rosters(cfg.league_id)
    usr = sleeper.users(cfg.league_id)
    me_rid = cfg.my_roster_id
    user_id = cfg.user_id
    if not user_id and cfg.username:
        u = sleeper.user(cfg.username)
        if u.ok:
            user_id = str((u.data or {}).get("user_id") or "")
    my_roster = None
    if ros.ok:
        for r in ros.data or []:
            if me_rid is not None and int(r.get("roster_id") or 0) == int(me_rid):
                my_roster = r
                break
            if user_id and str(r.get("owner_id")) == str(user_id):
                my_roster = r
                break

    banner_bits = []
    if not st.ok:
        banner_bits.append(st.fail_loud("NFL state"))
    if not ros.ok:
        banner_bits.append(ros.fail_loud("rosters"))
    if my_roster is None:
        banner_bits.append("UNVERIFIED — could not resolve your roster")

    nv_inj = nflverse.injuries(season)
    if not nv_inj.ok:
        # 2026 file may not exist until the regular season; fail loud, do not silently use 2025.
        banner_bits.append(nv_inj.fail_loud("nflverse injuries"))
        nv_rows = []
    else:
        age = age_seconds(nv_inj.fetched_at) or 0
        if age > STALE_WEEKLY:
            banner_bits.append(f"UNVERIFIED — nflverse injuries stale (fetched {nv_inj.fetched_at})")
        nv_rows = nv_inj.data or []

    sp = sleeper.players_nfl()
    if not sp.ok:
        banner_bits.append(sp.fail_loud("Sleeper players"))
        sleeper_players = {}
    else:
        sleeper_players = sp.data or {}

    merged = inj.merge_tier1(nv_rows, sleeper_players, xw or {})

    prev_path = DATA / "depth_snapshot.json"
    prev = json.loads(prev_path.read_text()) if prev_path.exists() else {}
    curr = inj.depth_chart_snapshot(sleeper_players)
    alerts = inj.depth_chart_diff(prev.get("players") or {}, curr)
    DATA.mkdir(exist_ok=True)
    prev_path.write_text(json.dumps({"fetched_at": iso(), "players": curr}))

    games_r = nflverse.games()
    games = games_r.data if games_r.ok else []
    if not games_r.ok:
        banner_bits.append(games_r.fail_loud("nflverse games"))

    slots = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX"]
    starter_ids = list(my_roster.get("starters") or []) if my_roster else []
    resolved = resolve_players(starter_ids, xw or {})
    starters = []
    for i, p in enumerate(resolved):
        slot = slots[i] if i < len(slots) else f"BN{i}"
        sid = p.get("sleeper_id")
        des = merged.get(sid or "", {})
        report = des.get("report_status")
        ko = kickoff_for(games, p.get("team") or "", int(week or 0), season) if p.get("team") else {
            "kickoff": None, "status": "UNVERIFIED — no team"
        }
        status = "ok"
        if not report and not des:
            status = "UNVERIFIED — check manually"
            report = "UNVERIFIED"
        elif not nv_inj.ok and not report:
            status = "UNVERIFIED — check manually"
            report = "UNVERIFIED"
        starters.append({
            "slot": slot,
            "name": p.get("name"),
            "pos": p.get("pos"),
            "team": p.get("team"),
            "sleeper_id": sid,
            "designation": report or "—",
            "practice": des.get("practice_status"),
            "kickoff": ko.get("kickoff"),
            "opponent": ko.get("opponent"),
            "implied_total": ko.get("implied_total"),
            "source": des.get("source") or "none",
            "status": status if ko.get("status") == "ok" else ko.get("status") or status,
        })
    starters.sort(key=lambda s: (inj.designation_rank(s.get("designation")), s.get("slot") or ""))

    # ESPN inactives: endpoints exist but do not expose inactives. Keep the section loud.
    banner_bits.append("UNVERIFIED — game-day inactives: ESPN scoreboard/summary/injuries have no inactive list (checked 2026-08-19). Check Sleeper/NFL app 90 minutes before kickoff.")

    payload = {
        "built_at": iso(),
        "week": week,
        "banner": " · ".join(banner_bits) if banner_bits else "Sources loaded. Still look with your eyes.",
        "starters": starters,
        "depth_alerts": alerts,
        "inactives": {"status": "UNVERIFIED", "reason": "no ESPN inactive field"},
    }
    (DATA / "gameday.json").write_text(json.dumps(payload, indent=2))
    (REPO / "gameday.json").write_text(json.dumps(payload, indent=2))
    (DATA / "gameday.html").write_text(render_html(payload))
    print(payload["banner"])
    print(f"{len(starters)} starters")
    push(cfg.ntfy_topic, "Gameday checklist", payload["banner"][:180])


if __name__ == "__main__":
    main()
