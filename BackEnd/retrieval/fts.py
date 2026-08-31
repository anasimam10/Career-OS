"""SQLite FTS5 full-text search (architecture_master §14).

External-content FTS5 virtual tables keep the index in sync with the
main tables through triggers, so ORM writes are searchable immediately.
Everything here is idempotent: ``ensure_fts()`` can run on every startup
(and every test setup) — it creates missing tables/triggers and then
REBUILDs each index from the current content tables.

If the SQLite build has no FTS5 support, the module degrades: searches
return no ids and callers fall back to SQL LIKE matching. No caller
ever needs to know which mode is active.
"""

from __future__ import annotations

import logging
import re

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

logger = logging.getLogger("ah_career.fts")

# content table -> (fts table, indexed columns). Columns map 1:1 onto the
# model tables; NULLs are coalesced in the triggers so the FTS 'delete'
# command always sees the values that were originally indexed.
FTS_SPECS: dict[str, tuple[str, list[str]]] = {
    "careers": ("careers_fts", ["name", "field", "category"]),
    "opportunities": ("opportunities_fts", ["title", "organization", "description"]),
    "universities": ("universities_fts", ["name"]),
    "programs": ("programs_fts", ["name"]),
    "alumni": ("alumni_fts", ["career_path", "field"]),
    "learning_resources": ("learning_resources_fts", ["title", "provider"]),
}

_fts_enabled: bool | None = None


def fts_available() -> bool:
    """True when the SQLite build supports FTS5 (probed lazily, cached)."""
    global _fts_enabled
    if _fts_enabled is None:
        try:
            import sqlite3

            conn = sqlite3.connect(":memory:")
            try:
                conn.execute("CREATE VIRTUAL TABLE fts_probe USING fts5(x)")
            finally:
                conn.close()
            _fts_enabled = True
        except Exception:
            _fts_enabled = False
            logger.warning("SQLite FTS5 is unavailable — LIKE fallback will be used.")
    return _fts_enabled


def _trigger_sql(content_table: str, fts_table: str, columns: list[str]) -> list[str]:
    """INSERT/UPDATE/DELETE triggers keeping the FTS table in sync."""
    cols = ", ".join(columns)
    old_cols = ", ".join(f"COALESCE(old.{c}, '')" for c in columns)
    new_cols = ", ".join(f"COALESCE(new.{c}, '')" for c in columns)
    prefix = f"trg_{content_table}"
    return [
        f"""
        CREATE TRIGGER IF NOT EXISTS {prefix}_ai AFTER INSERT ON {content_table}
        BEGIN
            INSERT INTO {fts_table}(rowid, {cols}) VALUES (new.id, {new_cols});
        END;
        """,
        f"""
        CREATE TRIGGER IF NOT EXISTS {prefix}_ad AFTER DELETE ON {content_table}
        BEGIN
            INSERT INTO {fts_table}({fts_table}, rowid, {cols})
            VALUES ('delete', old.id, {old_cols});
        END;
        """,
        f"""
        CREATE TRIGGER IF NOT EXISTS {prefix}_au AFTER UPDATE ON {content_table}
        BEGIN
            INSERT INTO {fts_table}({fts_table}, rowid, {cols})
            VALUES ('delete', old.id, {old_cols});
            INSERT INTO {fts_table}(rowid, {cols}) VALUES (new.id, {new_cols});
        END;
        """,
    ]


def ensure_fts(engine: Engine) -> None:
    """Create the FTS tables + triggers if missing, then rebuild every index.

    Safe to call repeatedly (startup, tests). When FTS5 is unavailable
    this is a no-op after the availability probe.
    """
    if not fts_available():
        return
    with engine.begin() as conn:
        for content_table, (fts_table, columns) in FTS_SPECS.items():
            cols = ", ".join(columns)
            conn.execute(
                text(
                    f"CREATE VIRTUAL TABLE IF NOT EXISTS {fts_table} USING fts5("
                    f"{cols}, content='{content_table}', content_rowid='id')"
                )
            )
            for statement in _trigger_sql(content_table, fts_table, columns):
                conn.execute(text(statement))
            # Repopulate from the content table (cheap at startup sizes) so
            # rows inserted before the triggers existed become searchable.
            conn.execute(text(f"INSERT INTO {fts_table}({fts_table}) VALUES('rebuild')"))


_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")


def _match_expression(query: str) -> str | None:
    """Turn raw user input into a safe FTS5 MATCH expression (implicit AND).

    Every token is quoted, so FTS5 operators, quotes, and hyphens in user
    input can never produce a syntax error.
    """
    tokens = _TOKEN_RE.findall(query or "")
    if not tokens:
        return None
    return " ".join(f'"{token}"' for token in tokens)


def fts_search_ids(db: Session, content_table: str, query: str, limit: int = 20) -> list[int]:
    """Row ids of content-table rows matching every word of ``query``.

    Returns [] when FTS is unavailable, the query has no usable tokens,
    or the table is unknown — callers fall back to LIKE matching.
    """
    spec = FTS_SPECS.get(content_table)
    if spec is None or not fts_available():
        return []
    fts_table = spec[0]
    match = _match_expression(query)
    if match is None:
        return []
    try:
        rows = db.execute(
            text(f"SELECT rowid FROM {fts_table} WHERE {fts_table} MATCH :m LIMIT :l"),
            {"m": match, "l": limit},
        ).fetchall()
    except Exception:
        logger.warning("FTS search failed on %s — falling back.", content_table, exc_info=True)
        return []
    return [row[0] for row in rows]
