"""
Coach Chat router (Phase 8).

POST /api/v1/coach/chat — AI mentor conversation with rate limiting.

Error contract:
- blank message           -> 422 {"detail": "Message must not be empty."}
- rate limit exceeded     -> 429 {"detail": "Too many requests. ..."}
- student not found       -> 404 {"error": "..."}
- AI unavailable          -> 503 {"error": "..."}
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from database import get_db
from schemas.requests import CoachChatPayload
from schemas.shared import CoachResponse
from services import coach_service
from services.ai_service import AIUnavailableError, AIValidationError
from services.rate_limiter import rate_limiter
from services.journey_state import DEMO_STUDENT_ID

router = APIRouter(tags=["coach"])


@router.post("/coach/chat", response_model=None)
def coach_chat(
    payload: CoachChatPayload, db: Session = Depends(get_db)
) -> CoachResponse | JSONResponse:
    """Handle a coach chat message with rate limiting and AI validation."""
    # --- validate message ---
    if not payload.message or not payload.message.strip():
        return JSONResponse(
            status_code=422,
            content={"detail": "Message must not be empty."},
        )

    # --- rate limit ---
    if not rate_limiter.is_allowed(DEMO_STUDENT_ID):
        return JSONResponse(
            status_code=429,
            content={
                "detail": "Too many requests. Please wait before sending another message."
            },
        )

    # --- build history dicts ---
    history = [
        {"role": m.role, "content": m.content}
        for m in (payload.conversation_history or [])
    ]

    # --- call service ---
    try:
        result = coach_service.coach_chat(db, payload.message.strip(), history)
        return result
    except coach_service.StudentNotFoundError:
        return JSONResponse(
            status_code=404,
            content={"error": "Student profile not found — complete onboarding first."},
        )
    except AIUnavailableError:
        return JSONResponse(
            status_code=503,
            content={"error": "AI mentor is temporarily unavailable. Please try again."},
        )
    except AIValidationError:
        return JSONResponse(
            status_code=503,
            content={"error": "AI mentor could not produce a valid response. Please try again."},
        )
