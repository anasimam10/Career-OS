"""Student-facing visibility filters (architecture_master §11/§22).

Single source of truth for the trust rules every student-facing
opportunity query must apply:

- only ``verification_status IN ('VALIDATED', 'VERIFIED')`` records
- only active records (``is_active = TRUE``)
- expired deadlines (``deadline < today``) never reach a student

Both the REST services and the MCP tools import these helpers so the
rule can never drift between surfaces (master §16: no duplicate logic).
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import or_
from sqlalchemy.orm import Query

from models.opportunity import Opportunity, SportsOpportunity

# Master §11: student-facing queries see VALIDATED/VERIFIED records only.
STUDENT_VISIBLE_STATUSES = ("VALIDATED", "VERIFIED")


def _not_expired(deadline_col):
    """A record with no deadline never expires; otherwise keep future ones."""
    return or_(deadline_col.is_(None), deadline_col >= date.today())


def apply_opportunity_visibility(query: Query) -> Query:
    """Chain onto an ``Opportunity`` query: active + verified + not expired."""
    return query.filter(
        Opportunity.is_active.is_(True),
        Opportunity.verification_status.in_(STUDENT_VISIBLE_STATUSES),
        _not_expired(Opportunity.deadline),
    )


def apply_sports_visibility(query: Query) -> Query:
    """Chain onto a ``SportsOpportunity`` query: active + verified + not expired."""
    return query.filter(
        SportsOpportunity.is_active.is_(True),
        SportsOpportunity.verification_status.in_(STUDENT_VISIBLE_STATUSES),
        _not_expired(SportsOpportunity.deadline),
    )


def is_opportunity_visible(record) -> bool:
    """Python-side visibility check for one already-loaded record."""
    if not record.is_active:
        return False
    if record.verification_status not in STUDENT_VISIBLE_STATUSES:
        return False
    if record.deadline is not None and record.deadline < date.today():
        return False
    return True


def is_sports_opportunity_visible(record) -> bool:
    """Python-side visibility check for one already-loaded sports record."""
    if not record.is_active:
        return False
    if record.verification_status not in STUDENT_VISIBLE_STATUSES:
        return False
    if record.deadline is not None and record.deadline < date.today():
        return False
    return True
