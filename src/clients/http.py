# -*- coding: utf-8 -*-
"""Disk cache for raw API responses. Always write before parse."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from paths import CACHE

UA = "guillotine-league-2026/1.0 (non-commercial; local tooling)"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: Optional[datetime] = None) -> str:
    return (dt or _now()).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class FetchResult:
    key: str
    url: str
    fetched_at: str
    path: Path
    ok: bool
    error: Optional[str] = None
    status: Optional[int] = None
    stale: bool = False
    data: Any = None
    text: Optional[str] = None

    def fail_loud(self, label: str) -> str:
        if not self.ok:
            return f"UNVERIFIED — {label}: {self.error or 'fetch failed'}"
        if self.stale:
            return f"UNVERIFIED — {label}: stale (fetched {self.fetched_at})"
        return ""


def _meta_path(key: str) -> Path:
    return CACHE / f"{key}.meta.json"


def _body_path(key: str, ext: str) -> Path:
    return CACHE / f"{key}{ext}"


def load_meta(key: str) -> Optional[dict]:
    p = _meta_path(key)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError:
        return None


def age_seconds(fetched_at: str) -> Optional[float]:
    try:
        raw = fetched_at.replace("Z", "+00:00")
        then = datetime.fromisoformat(raw)
        if then.tzinfo is None:
            then = then.replace(tzinfo=timezone.utc)
        return (_now() - then).total_seconds()
    except ValueError:
        return None


def fetch(
    url: str,
    key: str,
    *,
    max_age: Optional[float] = None,
    force: bool = False,
    timeout: int = 60,
    as_json: bool = True,
    min_interval: float = 0.0,
    ext: Optional[str] = None,
) -> FetchResult:
    """GET url, cache raw body + timestamp. Reuse cache if younger than max_age."""
    meta = load_meta(key)
    ext = ext if ext is not None else (".json" if as_json else ".txt")
    body_path = _body_path(key, ext)

    if not force and meta and body_path.exists() and max_age is not None:
        age = age_seconds(meta.get("fetched_at") or "")
        if age is not None and age <= max_age:
            text = body_path.read_text(encoding="utf-8")
            data = json.loads(text) if as_json else None
            return FetchResult(
                key=key, url=url, fetched_at=meta["fetched_at"], path=body_path,
                ok=True, status=meta.get("status"), data=data, text=text, stale=False,
            )

    if min_interval:
        time.sleep(min_interval)

    req = Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    try:
        with urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            status = getattr(resp, "status", 200)
    except HTTPError as e:
        err = f"HTTP {e.code} for {url}"
        return FetchResult(key=key, url=url, fetched_at=iso(), path=body_path, ok=False,
                           error=err, status=e.code)
    except URLError as e:
        return FetchResult(key=key, url=url, fetched_at=iso(), path=body_path, ok=False,
                           error=f"network error: {e.reason}")
    except TimeoutError:
        return FetchResult(key=key, url=url, fetched_at=iso(), path=body_path, ok=False,
                           error="timeout")

    text = raw.decode("utf-8", errors="replace")
    fetched_at = iso()
    body_path.write_text(text, encoding="utf-8")
    _meta_path(key).write_text(json.dumps({
        "url": url, "fetched_at": fetched_at, "status": status, "bytes": len(raw),
    }, indent=2), encoding="utf-8")

    data = None
    if as_json:
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            return FetchResult(key=key, url=url, fetched_at=fetched_at, path=body_path,
                               ok=False, error=f"invalid JSON: {e}", status=status, text=text)

    stale = False
    if max_age is not None:
        age = age_seconds(fetched_at)
        stale = age is not None and age > max_age

    return FetchResult(key=key, url=url, fetched_at=fetched_at, path=body_path, ok=True,
                       status=status, data=data, text=text, stale=stale)
