"""
Dependencies for API routers.
Supports dynamic per-session student resolution with seamless fallback
to DEMO_STUDENT_ID for backward compatibility.
"""

from __future__ import annotations

from typing import Optional
from fastapi import Header

from services.journey_state import DEMO_STUDENT_ID


def get_current_student_id(
    x_student_id: Optional[str] = Header(default=None, alias="X-Student-Id")
) -> int:
    """
    Extract the active student id from the X-Student-Id request header.
    If the header is missing, 'new', or non-numeric, falls back to DEMO_STUDENT_ID.
    """
    if x_student_id:
        cleaned = x_student_id.strip()
        if cleaned.isdigit() and int(cleaned) > 0:
            return int(cleaned)
    return DEMO_STUDENT_ID
