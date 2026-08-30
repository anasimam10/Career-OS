"""
Serialization helpers shared by the two MCP servers.

Every function here converts an ORM record to a plain JSON-serializable
dict using ONLY the record's own database values — no defaults that look
like facts, no invented fields (Phase 5 spec §4).
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

_BACKEND_DIR = Path(__file__).resolve().parents[1] / "BackEnd"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from models.opportunity import Opportunity, SportsOpportunity  # noqa: E402

# Safe, honest message for every "no matching records" case (spec §12).
NO_RESULTS_MESSAGE = "No matching opportunities found in our database right now."


def parse_json(raw: str | None, default: Any = None) -> Any:
    """Parse a JSON TEXT column; return the default when missing/malformed."""
    if raw is None or raw == "":
        return default
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return default


def opportunity_to_dict(o: Opportunity) -> dict:
    """Serialize an Opportunity exactly as stored (dates as ISO strings)."""
    return {
        "id": o.id,
        "type": o.type,
        "title": o.title,
        "organization": o.organization,
        "location": o.location,
        "deadline": o.deadline.isoformat() if o.deadline else None,
        "required_skills": parse_json(o.required_skills, []),
        "description": o.description,
        "source_url": o.source_url,
        "last_verified": o.last_verified.isoformat() if o.last_verified else None,
        "is_active": o.is_active,
    }


def sports_opportunity_to_dict(s: SportsOpportunity) -> dict:
    """Serialize a SportsOpportunity exactly as stored."""
    return {
        "id": s.id,
        "sport": s.sport,
        "type": s.type,
        "title": s.title,
        "organization": s.organization,
        "location": s.location,
        "deadline": s.deadline.isoformat() if s.deadline else None,
        "eligibility": parse_json(s.eligibility, {}),
        "description": s.description,
        "source_url": s.source_url,
        "last_verified": s.last_verified.isoformat() if s.last_verified else None,
        "is_active": s.is_active,
    }


def deadline_sort_key(record: Opportunity | SportsOpportunity):
    """Deterministic ordering: soonest deadline first, no-deadline last."""
    deadline: date | None = record.deadline
    return (deadline is None, deadline or date.min)


def city_matches(location: str | None, city: str) -> bool:
    """A record matches the queried city (case-insensitive) or is nationwide."""
    if not location:
        return False
    normalized = location.strip().lower()
    return normalized == "nationwide" or normalized == city.strip().lower()
