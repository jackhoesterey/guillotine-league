# -*- coding: utf-8 -*-
"""Tuesday/Wednesday in-season job. Renders a one-page brief; degrades per-section."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from clients import sleeper  # noqa: E402
from clients.http import iso  # noqa: E402
from core.config import load_config  # noqa: E402
from core.faab import (  # noqa: E402
    curve_verdict, landscape, price_curve, remaining_map, winning_bids_from_transactions,
)
from core.ids import load_crosswalk  # noqa: E402
from core.notify import push  # noqa: E402
from core.survival import find_my_matchup, margin, matchup_points, scores_from_matchups  # noqa: E402
from paths import DATA, ROOT as REPO  # noqa: E402

BRIEF_JSON = DATA / "brief.json"
BRIEF_ROOT = REPO / "brief.json"


def section(name: str, fetch_result, body: dict) -> dict:
    base = {
        "name": name,
        "fetched_at": getattr(fetch_result, "fetched_at", None),
        "ok": bool(getattr(fetch_result, "ok", False)),
    }
    if not base["ok"]:
        base["status"] = fetch_result.fail_loud(name) if hasattr(fetch_result, "fail_loud") else "UNVERIFIED"
        base["data"] = None
        return base
    body = dict(body)
    body.setdefault("status", "ok")
    base["status"] = body["status"]
    base["data"] = body
    return base


def resolve_me(cfg, users_data, rosters_data) -> dict:
    user_id = cfg.user_id
    if not user_id and cfg.username:
        for u in users_data or []:
            if (u.get("display_name") or "").lower() == cfg.username.lower() or u.get("user_id") == cfg.username:
                user_id = u.get("user_id")
                break
        if not user_id:
            u = sleeper.user(cfg.username)
            if u.ok:
                user_id = str((u.data or {}).get("user_id") or "")
    roster_id = cfg.my_roster_id
    if roster_id is None and user_id:
        for r in rosters_data or []:
            if str(r.get("owner_id")) == str(user_id):
                roster_id = r.get("roster_id")
                break
    return {"user_id": user_id, "roster_id": roster_id}


def render_html(brief: dict) -> str:
    def esc(s):
        return (str(s) if s is not None else "").replace("&", "&amp;").replace("<", "&lt;")

    parts = ['<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">',
             '<meta name="viewport" content="width=device-width, initial-scale=1">',
             '<title>Weekly brief</title><link rel="stylesheet" href="/brief.css">',
             '<style>:root{--bg:#0f1115;--tx:#e8eaef;--tx2:#9aa2b1;--line:#2a2f3a;--accent:#f0883e;--bad:#f85149}',
             'body{margin:0;background:var(--bg);color:var(--tx);font:16px/1.5 -apple-system,sans-serif}',
             '.top{padding:12px 18px;border-bottom:1px solid var(--line);display:flex;gap:12px;align-items:center}',
             'a{color:var(--tx2);text-decoration:none} .wrap{max-width:760px;margin:0 auto;padding:28px 18px 80px}',
             'h1{font-size:22px} h2{font-size:15px;letter-spacing:.08em;text-transform:uppercase;color:#6b7382}',
             '.unv{color:var(--bad);font-weight:600} .card{background:#171a21;border:1px solid var(--line);border-radius:10px;padding:14px;margin:12px 0}',
             '</style></head><body>',
             '<div class="top"><b>Weekly brief</b> <a href="/">draft room</a> <a href="/gameday.html">gameday</a></div>',
             '<div class="wrap">']
    parts.append(f"<h1>Week {esc(brief.get('week'))} · {esc(brief.get('built_at'))}</h1>")
    for sec in brief.get("sections") or []:
        st = sec.get("status") or ""
        klass = "unv" if str(st).startswith("UNVERIFIED") else ""
        parts.append(f'<div class="card"><h2>{esc(sec.get("name"))}</h2>')
        parts.append(f'<p class="{klass}">{esc(st)}</p>')
        if sec.get("fetched_at"):
            parts.append(f'<p style="color:#6b7382;font-size:12px">fetched {esc(sec["fetched_at"])}</p>')
        data = sec.get("data")
        if data:
            parts.append("<pre style='white-space:pre-wrap;font-size:13px'>" + esc(json.dumps(data, indent=2)) + "</pre>")
        parts.append("</div>")
    parts.append("</div></body></html>")
    return "".join(parts)


def main() -> None:
    cfg = load_config()
    cfg.require_league()
    xw = load_crosswalk()

    st = sleeper.state_nfl()
    week = None
    if st.ok:
        week = (st.data or {}).get("display_week") or (st.data or {}).get("week")
    try:
        week_i = int(week)
    except (TypeError, ValueError):
        week_i = None

    ros = sleeper.rosters(cfg.league_id)
    usr = sleeper.users(cfg.league_id)
    mu = sleeper.matchups(cfg.league_id, week_i) if week_i else None
    tx = sleeper.transactions(cfg.league_id, week_i) if week_i else None
    trend = sleeper.trending_add()

    me = resolve_me(cfg, usr.data if usr.ok else [], ros.data if ros.ok else [])
    sections = [section("NFL state", st, {"week": week_i, "season": (st.data or {}).get("season"),
                                          "season_type": (st.data or {}).get("season_type")})]

    # Open question: how eliminated teams appear. Do not drop anyone until configured.
    surviving = None
    if ros.ok:
        rem = remaining_map(ros.data or [], cfg.faab_budget, surviving)
        land = landscape(rem, int(me["roster_id"] or 0)) if me.get("roster_id") is not None else {
            "status": "UNVERIFIED — could not resolve your roster_id"
        }
        verdict = curve_verdict(week_i or 0, rem.get(int(me["roster_id"])) if me.get("roster_id") is not None else None)
        sections.append(section("FAAB", ros, {
            "remaining": rem,
            "landscape": land,
            "curve": verdict,
            "note": "waiver_budget_used treated as dollars until confirmed against a known bid",
        }))
    else:
        sections.append(section("FAAB", ros, {}))

    if mu and mu.ok:
        chop = scores_from_matchups(mu.data or [], surviving)
        mine = find_my_matchup(mu.data or [], int(me["roster_id"] or 0)) if me.get("roster_id") is not None else None
        my_pts = matchup_points(mine) if mine else None
        sections.append(section("Chop line", mu, {
            **chop,
            "me": margin(my_pts, chop.get("chop_line")),
            "open_question": "Eliminated-roster scoring is unverified. Chop uses every matchup that has points.",
        }))
    else:
        sections.append(section("Chop line", mu or st, {"status": "UNVERIFIED — no matchups (need a week)"}))

    if tx and tx.ok:
        bids = winning_bids_from_transactions(tx.data or [])
        sections.append(section("Bids", tx, {"bids": bids, "curve": price_curve(bids)}))
    else:
        sections.append(section("Bids", tx or st, {}))

    if trend.ok:
        names = []
        by_s = (xw or {}).get("by_sleeper_id") or {}
        by_rank = (xw or {}).get("by_rank") or {}
        for row in (trend.data or [])[:25]:
            sid = str(row.get("player_id") or "")
            rank = by_s.get(sid)
            rec = by_rank.get(str(rank), {}) if rank is not None else {}
            names.append({"player_id": sid, "count": row.get("count"), "board": rec.get("board_name"), "rank": rank})
        sections.append(section("Trending adds (24h)", trend, {"players": names}))
    else:
        sections.append(section("Trending adds (24h)", trend, {}))

    brief = {
        "built_at": iso(),
        "week": week_i,
        "league_id": cfg.league_id,
        "me": me,
        "sections": sections,
    }
    DATA.mkdir(exist_ok=True)
    BRIEF_JSON.write_text(json.dumps(brief, indent=2))
    BRIEF_ROOT.write_text(json.dumps(brief, indent=2))
    (DATA / "brief.html").write_text(render_html(brief))
    print(f"wrote {BRIEF_JSON} (week {week_i})")
    push(cfg.ntfy_topic, f"Guillotine brief · week {week_i}", f"Built {brief['built_at']}. Open brief.html.")


if __name__ == "__main__":
    main()
