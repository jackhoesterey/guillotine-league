# -*- coding: utf-8 -*-
"""
Player ID crosswalk: board name ↔ Sleeper player_id ↔ nflverse gsis_id.

Join Sleeper↔nflverse on gsis_id or espn_id (exact IDs). Fall back to
normalized (name, team, position) only for leftovers. Hand overrides in
data/id_overrides.json. Fail the build if <95% of board players map to Sleeper.
"""
from __future__ import annotations

import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Optional

from paths import DATA, ROOT, SRC

SKILL = {"QB", "RB", "WR", "TE"}
MIN_COVERAGE = 0.95
SUFFIXES = re.compile(r"\b(jr|sr|ii|iii|iv|v)\b", re.I)
PUNCT = re.compile(r"[^a-z0-9]+")
# Sleeper vs nflverse team abbreviations
TEAM_ALIAS = {"LAR": "LA", "LA": "LAR", "WSH": "WAS", "WAS": "WSH"}

# Bidirectional nicknames that show up on this board.
NICKNAMES = {
    "kenny": "kenneth",
    "kenneth": "kenny",
    "cam": "cameron",
    "cameron": "cam",
    "dj": "david",
    "aj": "alfred",
    "cj": "cj",
    "dk": "dk",
    "jk": "jk",
    "rj": "rj",
    "tj": "tj",
}

OVERRIDE_PATH = DATA / "id_overrides.json"
CROSSWALK_PATH = DATA / "crosswalk.json"
ROOT_CROSSWALK = ROOT / "crosswalk.json"


def normalize_name(name: str) -> str:
    s = unicodedata.normalize("NFKD", name or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.casefold().replace("'", "").replace("’", "").replace(".", "")
    s = SUFFIXES.sub("", s)
    s = PUNCT.sub("", s)
    return s


def name_keys(name: str) -> list[str]:
    """Normalized keys including a nickname swap of the first token."""
    base = normalize_name(name)
    keys = [base]
    # first-token nickname: kennygainwell ↔ kennethgainwell
    raw = re.sub(r"[^a-z0-9\s]", "", (name or "").casefold())
    parts = raw.split()
    if parts:
        nick = NICKNAMES.get(parts[0])
        if nick:
            parts2 = [nick] + parts[1:]
            keys.append(normalize_name(" ".join(parts2)))
    # unique
    out, seen = [], set()
    for k in keys:
        if k and k not in seen:
            seen.add(k)
            out.append(k)
    return out


def load_overrides() -> dict:
    if not OVERRIDE_PATH.exists():
        return {}
    try:
        return json.loads(OVERRIDE_PATH.read_text())
    except json.JSONDecodeError:
        return {}


def load_board_players(path: Optional[Path] = None) -> list[dict]:
    """Board rows from generated JSON, or parse src/board.py if not built yet."""
    for p in (path, DATA / "board2.json", DATA / "board.json"):
        if p and Path(p).exists():
            blob = json.loads(Path(p).read_text())
            rows = blob.get("players") or blob
            if rows:
                return rows
    text = (SRC / "board.py").read_text()
    rows = []
    for line in text.splitlines():
        line = line.strip()
        m = re.match(r'^\((\d+),"([^"]+)","([A-Z]+)","([A-Z]+)"', line)
        if not m:
            continue
        rows.append({"r": int(m.group(1)), "n": m.group(2), "p": m.group(3), "t": m.group(4)})
    return rows


def _sleeper_record(p: dict) -> dict:
    pid = str(p.get("player_id") or "")
    return {
        "sleeper_id": pid,
        "full_name": p.get("full_name") or f"{p.get('first_name','')} {p.get('last_name','')}".strip(),
        "team": p.get("team"),
        "position": p.get("position"),
        "espn_id": str(p["espn_id"]) if p.get("espn_id") not in (None, "") else None,
        "gsis_id": p.get("gsis_id") or None,
        "sportradar_id": p.get("sportradar_id") or None,
        "status": p.get("status"),
        "search_rank": p.get("search_rank"),
    }


def index_sleeper(players: dict[str, Any]) -> dict:
    by_id = {}
    by_name = defaultdict(list)
    by_espn = {}
    by_gsis = {}
    for pid, p in (players or {}).items():
        if not isinstance(p, dict):
            continue
        if p.get("position") not in SKILL:
            continue
        rec = p
        sid = str(p.get("player_id") or pid)
        by_id[sid] = rec
        n = rec.get("full_name") or f"{rec.get('first_name','')} {rec.get('last_name','')}".strip()
        for key in name_keys(n):
            by_name[key].append(rec)
        if rec.get("search_full_name"):
            by_name[normalize_name(rec["search_full_name"])].append(rec)
        if rec.get("espn_id") not in (None, ""):
            by_espn[str(rec["espn_id"])] = rec
        if rec.get("gsis_id"):
            by_gsis[str(rec["gsis_id"])] = rec
    return {"by_id": by_id, "by_name": by_name, "by_espn": by_espn, "by_gsis": by_gsis}


def index_nflverse(rows: Iterable[dict]) -> dict:
    by_espn, by_gsis = {}, {}
    by_ntp = defaultdict(list)
    for row in rows:
        if row.get("espn_id"):
            by_espn[str(row["espn_id"])] = row
        if row.get("gsis_id"):
            by_gsis[str(row["gsis_id"])] = row
        n = row.get("display_name") or row.get("football_name") or ""
        team = row.get("latest_team") or row.get("team") or ""
        pos = row.get("position") or ""
        for key in name_keys(n):
            by_ntp[(key, team, pos)].append(row)
    return {"by_espn": by_espn, "by_gsis": by_gsis, "by_ntp": by_ntp}


def _pick_candidate(cands: list[dict], team: str, pos: str) -> tuple[Optional[dict], str]:
    if not cands:
        return None, ""
    # unique
    uniq = {str(c.get("player_id")): c for c in cands}
    cands = list(uniq.values())
    if len(cands) == 1:
        return cands[0], "name_unique"
    same_tp = [c for c in cands if (c.get("team") or "") == team and c.get("position") == pos]
    if len(same_tp) == 1:
        return same_tp[0], "name_team_pos"
    same_p = [c for c in cands if c.get("position") == pos]
    active = [c for c in same_p if c.get("active") or c.get("status") in
              ("Active", "Injured Reserve", "PUP", "Practice Squad", "Questionable")]
    if len(same_p) == 1:
        return same_p[0], "name_pos"
    if len(active) == 1:
        return active[0], "name_pos_active"
    pool = active or same_p or cands
    pool = sorted(pool, key=lambda c: c.get("search_rank") or 999999)
    return pool[0], "name_pos_searchrank"


def match_board_player(board: dict, sleeper_ix: dict, overrides: dict) -> dict:
    name = board["n"]
    pos = board.get("p") or board.get("position") or ""
    team = board.get("t") or board.get("team") or ""
    rank = board["r"]

    ov = overrides.get(name) or overrides.get(str(rank)) or {}
    if isinstance(ov, str):
        ov = {"sleeper_id": ov}
    if ov.get("sleeper_id"):
        p = sleeper_ix["by_id"].get(str(ov["sleeper_id"]))
        rec = _sleeper_record(p) if p else {"sleeper_id": str(ov["sleeper_id"])}
        rec.update({"rank": rank, "board_name": name, "method": "override"})
        return rec

    cands = []
    for key in name_keys(name):
        cands.extend(sleeper_ix["by_name"].get(key, []))
    p, method = _pick_candidate(cands, team, pos)
    if not p:
        return {"rank": rank, "board_name": name, "sleeper_id": None, "method": "unmatched"}
    rec = _sleeper_record(p)
    rec.update({"rank": rank, "board_name": name, "method": method})
    return rec


def attach_gsis(rec: dict, nfl_ix: dict) -> dict:
    gsis = rec.get("gsis_id")
    espn = rec.get("espn_id")
    nv = None
    how = None
    if gsis and gsis in nfl_ix["by_gsis"]:
        nv = nfl_ix["by_gsis"][gsis]
        how = "gsis_id"
    elif espn and espn in nfl_ix["by_espn"]:
        nv = nfl_ix["by_espn"][espn]
        how = "espn_id"
    if nv is None:
        team = rec.get("team") or ""
        pos = rec.get("position") or ""
        cands = []
        teams = {team, TEAM_ALIAS.get(team, ""), team}
        teams.discard("")
        for key in name_keys(rec.get("full_name") or rec.get("board_name") or ""):
            for tm in teams:
                cands.extend(nfl_ix.get("by_ntp", {}).get((key, tm, pos), []))
        uniq = {r.get("gsis_id"): r for r in cands if r.get("gsis_id")}
        if len(uniq) == 1:
            nv = next(iter(uniq.values()))
            how = "name_team_pos"
    rec["nflverse_join"] = how
    if nv:
        rec["gsis_id"] = rec.get("gsis_id") or nv.get("gsis_id")
        rec["espn_id"] = rec.get("espn_id") or (str(nv["espn_id"]) if nv.get("espn_id") else None)
    return rec


def build_crosswalk(sleeper_players: dict, nflverse_rows: Optional[list] = None,
                    board: Optional[list] = None, overrides: Optional[dict] = None) -> dict:
    board = board if board is not None else load_board_players()
    overrides = overrides if overrides is not None else load_overrides()
    six = index_sleeper(sleeper_players)
    nix = index_nflverse(nflverse_rows or [])
    by_rank, by_sleeper, unmatched = {}, {}, []
    for b in board:
        rec = match_board_player(b, six, overrides)
        rec = attach_gsis(rec, nix)
        by_rank[str(rec["rank"])] = rec
        if rec.get("sleeper_id"):
            by_sleeper[str(rec["sleeper_id"])] = rec["rank"]
        else:
            unmatched.append(rec["board_name"])
    n = len(board) or 1
    coverage = (n - len(unmatched)) / n
    return {
        "coverage": coverage,
        "board_size": len(board),
        "matched": len(board) - len(unmatched),
        "unmatched": unmatched,
        "min_coverage": MIN_COVERAGE,
        "by_rank": by_rank,
        "by_sleeper_id": by_sleeper,
    }


def assert_coverage(xw: dict) -> None:
    cov = xw.get("coverage") or 0
    if cov < MIN_COVERAGE:
        names = "\n".join(f"  - {n}" for n in xw.get("unmatched") or [])
        raise SystemExit(
            f"crosswalk coverage {cov:.1%} < {MIN_COVERAGE:.0%}. Unmatched:\n{names}"
        )


def write_crosswalk(xw: dict) -> Path:
    DATA.mkdir(exist_ok=True)
    payload = dict(xw)
    CROSSWALK_PATH.write_text(json.dumps(payload, indent=2))
    ROOT_CROSSWALK.write_text(json.dumps(payload, indent=2))
    return CROSSWALK_PATH


def load_crosswalk() -> dict:
    p = CROSSWALK_PATH if CROSSWALK_PATH.exists() else ROOT_CROSSWALK
    if not p.exists():
        return {}
    return json.loads(p.read_text())
