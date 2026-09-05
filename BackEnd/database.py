"""
SQLAlchemy engine, session factory, and JSON column type.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy import Text, create_engine, event, inspect, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.types import TypeDecorator

from config import settings
from models.base import Base

logger = logging.getLogger("ah_career.database")

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
    """Create all tables, migrate missing columns, and build FTS indexes."""
    # Import all models so Base.metadata is populated
    import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _migrate_missing_columns()
    _deduplicate_milestones_migration()

    from retrieval.fts import ensure_fts  # local import: avoids import cycles

    ensure_fts(engine)


# ---------------------------------------------------------------------------
# Additive column migration (architecture_master §10 provenance columns)
# ---------------------------------------------------------------------------

# (column name, DDL) pairs added to EXISTING tables when the column is
# missing. New tables come from create_all; this only ever ADDS nullable
# or constant-defaulted columns, so it can never destroy data.
_COLUMN_MIGRATIONS: dict[str, list[tuple[str, str]]] = {
    "opportunities": [
        ("verification_status", "VARCHAR(32) DEFAULT 'CANDIDATE'"),
        ("status", "VARCHAR(32) DEFAULT 'ACTIVE'"),
        ("source_id", "INTEGER"),
        ("content_hash", "VARCHAR(64)"),
        ("dedup_key", "VARCHAR(255)"),
        ("retrieved_at", "DATETIME"),
        ("field", "VARCHAR(100)"),
        ("province", "VARCHAR(100)"),
        ("is_remote", "BOOLEAN DEFAULT FALSE"),
        ("organization_type", "VARCHAR(50)"),
        ("required_education_stage", "VARCHAR(50)"),
        ("required_degree_type", "VARCHAR(50)"),
        ("required_cgpa", "FLOAT"),
        ("stipend_pkr", "INTEGER"),
        ("eligibility_notes", "TEXT"),
    ],
    "sports_opportunities": [
        ("verification_status", "VARCHAR(32) DEFAULT 'CANDIDATE'"),
        ("source_id", "INTEGER"),
        ("content_hash", "VARCHAR(64)"),
        ("dedup_key", "VARCHAR(255)"),
        ("retrieved_at", "DATETIME"),
    ],
    "careers": [
        ("category", "VARCHAR(100)"),
        ("is_active", "BOOLEAN DEFAULT TRUE"),
    ],
    "learning_resources": [
        ("geographic_scope", "VARCHAR(64)"),
    ],
    "alumni": [
        ("university_id", "INTEGER"),
        ("career_id", "INTEGER"),
        ("source_id", "INTEGER"),
        ("source_url", "VARCHAR(500)"),
    ],
    "students": [
        ("city", "VARCHAR(100)"),
        ("province", "VARCHAR(100)"),
    ],
}

# Rows that existed BEFORE these columns were introduced are the curated
# seed/template records the running application already serves to students.
# Lifting them to VALIDATED (once, at migration time) preserves that
# behaviour; every later ingested record still starts as CANDIDATE (§11).
_BACKFILLS: dict[tuple[str, str], object] = {
    ("opportunities", "verification_status"): "VALIDATED",
    ("sports_opportunities", "verification_status"): "VALIDATED",
    ("careers", "is_active"): 1,
}


def _migrate_missing_columns() -> None:
    """Add missing columns to existing tables (idempotent, additive only)."""
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    added: list[str] = []
    with engine.begin() as conn:
        for table, columns in _COLUMN_MIGRATIONS.items():
            if table not in table_names:
                continue  # table not created yet — create_all will handle it
            existing = {col["name"] for col in inspector.get_columns(table)}
            for name, ddl in columns:
                if name in existing:
                    continue
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))
                backfill = _BACKFILLS.get((table, name))
                if backfill is not None:
                    conn.execute(
                        text(f"UPDATE {table} SET {name} = :value"), {"value": backfill}
                    )
                added.append(f"{table}.{name}")
    if added:
        logger.info("Migrated columns added: %s", ", ".join(added))


def _deduplicate_milestones_migration() -> None:
    """Remove legacy duplicate milestone records per roadmap, prioritizing completed records."""
    inspector = inspect(engine)
    if "milestones" not in inspector.get_table_names():
        return
    with engine.begin() as conn:
        result = conn.execute(
            text("""
                SELECT roadmap_id, title
                FROM milestones
                GROUP BY roadmap_id, title
                HAVING COUNT(*) > 1
            """)
        ).fetchall()
        for r_id, title in result:
            rows = conn.execute(
                text("""
                    SELECT id, status
                    FROM milestones
                    WHERE roadmap_id = :r_id AND title = :title
                    ORDER BY CASE WHEN status IN ('completed', 'done') THEN 0 ELSE 1 END, id ASC
                """),
                {"r_id": r_id, "title": title},
            ).fetchall()
            if len(rows) > 1:
                delete_ids = [r[0] for r in rows[1:]]
                conn.execute(
                    text(f"DELETE FROM milestones WHERE id IN ({','.join(str(i) for i in delete_ids)})")
                )
                logger.info("Deduplicated milestone '%s' on roadmap %s (kept %s, deleted %s)", title, r_id, rows[0][0], delete_ids)
