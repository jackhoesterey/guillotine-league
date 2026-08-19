# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
CACHE = ROOT / "cache"
DATA = ROOT / "data"
TESTS = ROOT / "tests"
FIXTURES = TESTS / "fixtures"

CACHE.mkdir(exist_ok=True)
DATA.mkdir(exist_ok=True)
