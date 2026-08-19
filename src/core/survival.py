# -*- coding: utf-8 -*-
"""Chop-line tracking, margin, danger. Do not guess how Sleeper represents eliminated teams."""
from __future__ import annotations

from typing import Iterable, Optional


def matchup_points(m: dict) -> Optional[float]:
    pts = m.get("points")
    if pts is None:
        return None
    try:
        return float(pts)
    except (TypeError, ValueError):
        return None


def scores_from_matchups(matchups: Iterable[dict],
                         surviving: Optional[set[int]] = None) -> dict:
    """
    surviving=None means 'we have not observed a chop yet — do not drop anyone'.
    After Week 1, pass the roster_ids still alive. Eliminated scoring (zero / null /
    absent) is an open question; never infer it.
    """
    rows = []
    skipped = []
    for m in matchups or []:
        rid = m.get("roster_id")
        if rid is None:
            continue
        rid = int(rid)
        if surviving is not None and rid not in surviving:
            skipped.append(rid)
            continue
        pts = matchup_points(m)
        if pts is None:
            skipped.append(rid)
            continue
        rows.append({"roster_id": rid, "points": pts})
    if not rows:
        return {
            "chop_line": None,
            "n": 0,
            "scores": [],
            "skipped": skipped,
            "status": "UNVERIFIED — no usable matchup points",
        }
    chop = min(r["points"] for r in rows)
    return {
        "chop_line": chop,
        "n": len(rows),
        "scores": sorted(rows, key=lambda r: r["points"]),
        "skipped": skipped,
        "status": "ok",
        "assumption": "survivors-only" if surviving is not None else "all-matchups-with-points",
    }


def margin(my_points: Optional[float], chop_line: Optional[float]) -> dict:
    if my_points is None or chop_line is None:
        return {"margin": None, "status": "UNVERIFIED — missing score or chop line"}
    m = my_points - chop_line
    if m <= 0:
        danger = "dead"
    elif m < 8:
        danger = "critical"
    elif m < 15:
        danger = "danger"
    elif m < 25:
        danger = "watch"
    else:
        danger = "safe"
    return {"margin": m, "my_points": my_points, "chop_line": chop_line, "danger": danger, "status": "ok"}


def find_my_matchup(matchups: Iterable[dict], roster_id: int) -> Optional[dict]:
    for m in matchups or []:
        if int(m.get("roster_id") or 0) == int(roster_id):
            return m
    return None
