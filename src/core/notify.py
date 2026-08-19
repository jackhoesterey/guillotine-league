# -*- coding: utf-8 -*-
"""Optional ntfy.sh push. Never required for the jobs to succeed."""
from __future__ import annotations

from urllib.error import URLError
from urllib.request import Request, urlopen


def push(topic: str, title: str, body: str) -> str:
    if not topic:
        return "skipped — no ntfy topic"
    url = f"https://ntfy.sh/{topic}"
    req = Request(url, data=body.encode("utf-8"), method="POST",
                  headers={"Title": title, "User-Agent": "guillotine-league-2026"})
    try:
        with urlopen(req, timeout=15) as resp:
            return f"ok {resp.status}"
    except URLError as e:
        return f"UNVERIFIED — ntfy failed: {e.reason}"
