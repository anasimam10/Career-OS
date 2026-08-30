"""
Career repository — career-specific queries.
"""

from __future__ import annotations

import json
from typing import Optional

from sqlalchemy.orm import Session

from models.career import Career
from repositories.base import BaseRepository


class CareerRepository(BaseRepository[Career]):
    def __init__(self, db: Session):
        super().__init__(Career, db)

    def get_by_slug(self, slug: str) -> Optional[Career]:
        return self._db.query(Career).filter(Career.slug == slug).first()

    def get_all_careers(self) -> list[Career]:
        return self._db.query(Career).order_by(Career.name).all()

    def get_by_field(self, field: str) -> list[Career]:
        return self._db.query(Career).filter(Career.field == field).all()

    def to_dict(self, career: Career) -> dict:
        """Convert a Career ORM instance to a plain dict.

        JSON-stored TEXT columns are deserialised here so that callers
        receive Python lists rather than raw JSON strings.
        """
        def _parse_json(raw: str | None) -> list:
            if raw is None:
                return []
            try:
                return json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                return []

        return {
            "slug": career.slug,
            "name": career.name,
            "field": career.field,
            "demand_level": career.demand_level,
            "competition_level": career.competition_level,
            "difficulty_level": career.difficulty_level,
            "required_skills": _parse_json(career.required_skills),
            "pk_opportunities": _parse_json(career.pk_opportunities),
            "top_pk_universities": _parse_json(career.top_pk_universities),
            "risks": _parse_json(career.risks),
            "last_updated": career.last_updated.isoformat() if career.last_updated else None,
        }
