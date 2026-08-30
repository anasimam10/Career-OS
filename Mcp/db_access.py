"""
Shared database access for the two MCP servers.

The MCP servers live outside BackEnd/ but MUST use the project's single
database engine and models (Phase 5 spec §3): no second database file, no
second schema, no duplicated models. This module bootstraps the BackEnd
import path and exposes one session factory that tests can swap for the
in-memory test database.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable

# Bootstrap the BackEnd package on sys.path (same approach as data/seed_db.py)
_BACKEND_DIR = Path(__file__).resolve().parents[1] / "BackEnd"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from database import SessionLocal  # noqa: E402

# One tool call = one short session. Tests replace this factory with the
# in-memory test session factory so the tools read the test database.
_session_factory: Callable = SessionLocal


def get_session():
    """Open a new database session for one tool call (closed by the caller)."""
    return _session_factory()


def set_session_factory(factory: Callable) -> None:
    """Test hook: point the MCP servers at another session factory."""
    global _session_factory
    _session_factory = factory
