# -*- coding: utf-8 -*-
"""Live draft poller. Writes data/draft_state.json every 2–3 seconds.

The draft room also polls Sleeper directly in the browser (CORS is *). This
job is the local/offline path and a stale-connection writer for the static site.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from clients import sleeper  # noqa: E402
from clients.http import iso  # noqa: E402
from core.config import load_config  # noqa: E402
from core.ids import load_crosswalk  # noqa: E402
from paths import DATA, ROOT as REPO  # noqa: E402


def apply_picks(picks: list, crosswalk: dict, my_user_id: str) -> dict:
    by_s = crosswalk.get("by_sleeper_id") or {}
    st = {}
    unmapped = []
    for pk in picks or []:
        sid = str(pk.get("player_id") or "")
        rank = by_s.get(sid)
        if rank is None:
            meta = pk.get("metadata") or {}
            unmapped.append({
                "player_id": sid,
                "name": f"{meta.get('first_name','')} {meta.get('last_name','')}".strip(),
                "pick_no": pk.get("pick_no"),
            })
            continue
        mine = bool(my_user_id) and str(pk.get("picked_by") or "") == str(my_user_id)
        st[str(rank)] = "mine" if mine else "taken"
    return {"st": st, "unmapped": unmapped, "n_picks": len(picks or [])}


def my_slot(draft: dict, user_id: str) -> dict:
    order = draft.get("draft_order") or {}
    # draft_order is {user_id: slot} per Sleeper docs
    slot = order.get(str(user_id))
    settings = draft.get("settings") or {}
    teams = settings.get("teams") or draft.get("settings", {}).get("teams")
    return {"slot": slot, "teams": teams, "status": draft.get("status")}


def write_state(payload: dict) -> None:
    DATA.mkdir(exist_ok=True)
    path = DATA / "draft_state.json"
    path.write_text(json.dumps(payload))
    (REPO / "draft_state.json").write_text(json.dumps(payload))


def once(draft_id: str, user_id: str, crosswalk: dict) -> dict:
    d = sleeper.draft(draft_id, force=True)
    p = sleeper.draft_picks(draft_id, force=True)
    payload = {
        "fetched_at": iso(),
        "draft_ok": d.ok,
        "picks_ok": p.ok,
        "draft_error": d.error,
        "picks_error": p.error,
        "draft_id": draft_id,
    }
    if not d.ok or not p.ok:
        payload["status"] = "UNVERIFIED — stale connection"
        payload["stale"] = True
        return payload
    applied = apply_picks(p.data or [], crosswalk, user_id)
    slot = my_slot(d.data or {}, user_id)
    payload.update(applied)
    payload.update(slot)
    payload["status"] = "ok"
    payload["stale"] = False
    payload["fetched_at"] = p.fetched_at
    return payload


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--interval", type=float, default=2.5)
    args = ap.parse_args()
    cfg = load_config()
    if not cfg.draft_id:
        raise SystemExit("No draft_id. Set SLEEPER_DRAFT_ID or data/league.json")
    xw = load_crosswalk()
    if not xw:
        raise SystemExit("No crosswalk. Run: python3 src/jobs/build_crosswalk.py")
    user_id = cfg.user_id
    if not user_id and cfg.username:
        u = sleeper.user(cfg.username)
        if u.ok:
            user_id = str((u.data or {}).get("user_id") or "")
    while True:
        payload = once(cfg.draft_id, user_id, xw)
        write_state(payload)
        n = payload.get("n_picks")
        flag = payload.get("status")
        print(f"{payload.get('fetched_at')}  picks={n}  {flag}")
        if args.once:
            break
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
