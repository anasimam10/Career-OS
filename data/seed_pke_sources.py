"""
Seed the pke_sources table from data/seed/pke_sources.json.

Usage (from the repository root):

    python data/seed_pke_sources.py

Behaviour:
- Creates the pke_sources table if it does not exist.
- INSERT-ONLY: existing rows (matched by source_id) are skipped, never
  overwritten. This makes the script safe to re-run at any time.
- Prints a summary of inserted / skipped counts.
- Exits 0 on success, 1 on any error.

This script does NOT fetch, scrape, or ingest any external data.
It only populates the source registry with pre-defined metadata.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    backend = ROOT / "BackEnd"
    os.chdir(backend)
    sys.path.insert(0, str(backend))

    from database import SessionLocal, init_db  # noqa: E402
    from knowledge_engine.pke_source_registry import PKESource  # noqa: E402

    init_db()

    seed_file = ROOT / "data" / "seed" / "pke_sources.json"
    payload = json.loads(seed_file.read_text(encoding="utf-8"))

    db = SessionLocal()
    inserted = skipped = 0
    try:
        for record in payload["sources"]:
            existing = (
                db.query(PKESource)
                .filter(PKESource.source_id == record["source_id"])
                .first()
            )
            if existing is not None:
                skipped += 1
                continue

            last_checked = None
            if record.get("last_checked"):
                last_checked = date.fromisoformat(record["last_checked"])

            entry = PKESource(
                source_id=record["source_id"],
                name=record["name"],
                base_url=record["base_url"],
                authority_level=record["authority_level"],
                source_type=record["source_type"],
                domains=record["domains"],
                geographic_scope=record["geographic_scope"],
                access_review_status=record["access_review_status"],
                retrieval_method=record.get("retrieval_method"),
                has_official_api=bool(record.get("has_official_api", False)),
                is_reachable=record.get("is_reachable"),
                last_checked=last_checked,
                source_confidence=record.get("source_confidence"),
                notes=record.get("notes"),
                tos_review_url=record.get("tos_review_url"),
            )
            db.add(entry)
            inserted += 1

        db.commit()
    except Exception as exc:
        db.rollback()
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()

    print(
        f"PKE sources: {inserted} inserted, {skipped} skipped (already present)."
    )
    print("Done. No external data was fetched — this seeds registry metadata only.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
