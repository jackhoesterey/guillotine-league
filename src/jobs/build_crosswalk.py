# -*- coding: utf-8 -*-
"""Phase 0: build data/crosswalk.json. Fails if coverage < 95%."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from clients import nflverse, sleeper  # noqa: E402
from core.ids import assert_coverage, build_crosswalk, write_crosswalk  # noqa: E402
from clients.http import iso  # noqa: E402


def main() -> None:
    sp = sleeper.players_nfl()
    if not sp.ok:
        raise SystemExit(f"UNVERIFIED — could not load Sleeper players: {sp.error}")
    nv = nflverse.players()
    nv_rows = nv.data if nv.ok else []
    if not nv.ok:
        print(f"nflverse players UNVERIFIED ({nv.error}) — joining on gsis/espn will be incomplete")
    xw = build_crosswalk(sp.data or {}, nv_rows)
    xw["fetched_at"] = sp.fetched_at
    xw["sleeper_source"] = sp.url
    xw["nflverse_ok"] = nv.ok
    xw["built_at"] = iso()
    path = write_crosswalk(xw)
    print(f"matched {xw['matched']}/{xw['board_size']} ({xw['coverage']:.1%})")
    if xw["unmatched"]:
        print("unmatched:")
        for n in xw["unmatched"]:
            print(f"  - {n}")
    assert_coverage(xw)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
