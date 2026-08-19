#!/usr/bin/env bash
# Rebuilds index.html, the FAAB tracker, and the Sleeper ID crosswalk from source.
# Run this after editing src/board.py or src/stats25.py.
set -euo pipefail
cd "$(dirname "$0")"

echo "1/4  building the player board..."
python3 src/board.py

echo "2/4  merging 2025 stats and applying grade overrides..."
python3 src/merge.py

echo "3/4  Sleeper / nflverse ID crosswalk (fails if coverage < 95%)..."
python3 src/jobs/build_crosswalk.py

echo "4/4  rendering index.html and the tracker..."
python3 src/build_app.py
python3 src/build_xlsx.py

echo
echo "done."
echo "  index.html                       — draft room (Vercel / any static host)"
echo "  crosswalk.json                   — board rank ↔ Sleeper player_id"
echo "  Guillotine-FAAB-Tracker-2026.xlsx — formulas recalculate when Excel opens it"
echo
echo "In-season (after data/league.json is filled):"
echo "  python3 src/jobs/draft_poll.py --once"
echo "  python3 src/jobs/weekly_sync.py"
echo "  python3 src/jobs/gameday_check.py"
