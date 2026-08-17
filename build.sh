#!/usr/bin/env bash
# Rebuilds index.html and the FAAB tracker from source.
# Run this after editing src/board.py or src/stats25.py.
set -euo pipefail
cd "$(dirname "$0")"

echo "1/3  building the player board..."
python3 src/board.py

echo "2/3  merging 2025 stats and applying grade overrides..."
python3 src/merge.py

echo "3/3  rendering index.html and the tracker..."
python3 src/build_app.py
python3 src/build_xlsx.py

echo
echo "done."
echo "  index.html                       — open in a browser, or deploy on Vercel"
echo "  Guillotine-FAAB-Tracker-2026.xlsx — formulas recalculate when Excel opens it"
