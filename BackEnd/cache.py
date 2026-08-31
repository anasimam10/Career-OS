"""Simple in-memory TTL cache (architecture_master §15).

Python-dict caching for local development — no Redis required. The
interface (get/set/delete/clear) is designed so a Redis-backed cache can
be substituted later without changing any call site.

Cached (stable, seed-loaded data):
- career search results (5-minute TTL)
- university search results (5-minute TTL)

Never cached (master §15 "What NOT to cache"):
- opportunity deadlines / listings — always re-queried for freshness
- student profiles — always read fresh from DB for AI calls
- ingestion extraction results — never cached as truth

Call ``cache.clear()`` whenever curated data changes (admin update,
ingestion persist) — the admin router does this.
"""

from __future__ import annotations

import threading
import time
from typing import Any, Optional


class SimpleCache:
    """Thread-safe dict cache with per-entry TTL (time.monotonic based)."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[float, Any]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        """Return the cached value, or None when missing/expired."""
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            expires_at, value = entry
            if expires_at < time.monotonic():
                # Lazy expiry: drop the stale entry while we're here.
                self._store.pop(key, None)
                return None
            return value

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        """Store ``value`` under ``key`` for ``ttl_seconds`` seconds."""
        expires_at = time.monotonic() + max(0, ttl_seconds)
        with self._lock:
            self._store[key] = (expires_at, value)

    def delete(self, key: str) -> None:
        """Drop one key (no error when missing)."""
        with self._lock:
            self._store.pop(key, None)

    def clear(self) -> None:
        """Drop everything (tests, admin data updates)."""
        with self._lock:
            self._store.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._store)


# Shared application-level instance. Retrieval modules cache against it;
# tests clear it in the db_session fixture (conftest.py).
cache = SimpleCache()

# Master §15: frequently requested career/university searches are cached
# for 5 minutes.
DEFAULT_TTL_SECONDS = 300
