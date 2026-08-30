"""
SQLAlchemy engine, session factory, and JSON column type.
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import create_engine, Text, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.types import TypeDecorator

from config import settings
from models.base import Base

# ---------------------------------------------------------------------------
# Custom JSON type for SQLite (TEXT storage with automatic serialisation)
# ---------------------------------------------------------------------------


class JSONType(TypeDecorator):
    """Store Python dicts/lists as JSON text. Works with SQLite and PostgreSQL."""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> str | None:
        if value is not None:
            return json.dumps(value)
        return None

    def process_result_value(self, value: str | None, dialect: Any) -> Any:
        if value is not None:
            return json.loads(value)
        return None


# ---------------------------------------------------------------------------
# Engine & session
# ---------------------------------------------------------------------------

connect_args: dict[str, Any] = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,
)

# Enable WAL mode and foreign keys for SQLite
if settings.DATABASE_URL.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_conn: Any, _connection_record: Any) -> None:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def get_db() -> Session:  # type: ignore[misc]
    """FastAPI dependency — yields a DB session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables (call once at startup)."""
    # Import all models so Base.metadata is populated
    import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
