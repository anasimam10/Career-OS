"""
In-memory rate limiter for Coach Chat (Phase 8).

20 requests per student per hour.  Resets on server restart.
Production replacement: Redis with sliding window — swap requires no
changes to coach.py because both implementations expose ``is_allowed``.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
import threading


class InMemoryRateLimiter:
    """
    Simple in-memory rate limiter. Not persistent across restarts.
    For MVP/hackathon use only.
    Production replacement: Redis with sliding window.
    """

    def __init__(self, max_requests: int = 20, window_hours: int = 1):
        self.max_requests = max_requests
        self.window = timedelta(hours=window_hours)
        self._store: dict[int, list[datetime]] = defaultdict(list)
        self._lock = threading.Lock()

    def is_allowed(self, student_id: int) -> bool:
        now = datetime.utcnow()
        cutoff = now - self.window
        with self._lock:
            self._store[student_id] = [
                t for t in self._store[student_id] if t > cutoff
            ]
            if len(self._store[student_id]) >= self.max_requests:
                return False
            self._store[student_id].append(now)
            return True

    def clear(self, student_id: int) -> None:
        """Purge rate-limiting records for a deleted student."""
        with self._lock:
            self._store.pop(student_id, None)


# Singleton instance
rate_limiter = InMemoryRateLimiter(max_requests=20, window_hours=1)
